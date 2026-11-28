import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from content_queue import Queue
from daily_content import DailyContent, WIB, PILLARS
from send_review import DeliveryUncertain


class DailyContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.daily = DailyContent(self.queue)
        self.day = '2026-11-28'
        self.clock = patch('daily_content.today', return_value=self.day)
        self.clock.start()
        self.bundle = json.loads((Path(__file__).parent/'samples/lead.json').read_text(encoding='utf-8'))
        self.image = Path(self.temp.name)/'preview.jpg'
        self.image.write_bytes(b'\xff\xd8\xff' + b'unit-test-image')
        self.config = {'token':'123:'+'x'*30, 'chat_id':'42'}
        self.calls = []

    def tearDown(self):
        self.clock.stop()
        self.queue.db.close()
        self.temp.cleanup()

    def submit(self, bundle=None):
        return self.daily.submit(self.day, bundle or self.bundle, self.image)

    def transport(self, method, fields, file):
        self.calls.append((method, fields, file))
        return 100+len(self.calls)

    def test_one_pair_atomic_and_same_day_idempotent(self):
        first = self.submit()
        again = self.submit()
        self.assertEqual(first, again)
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 2)
        self.assertNotEqual(first['instagram_id'], first['threads_id'])
        self.assertEqual({d['status'] for d in first['drafts'].values()}, {'draft'})

    def test_changed_second_batch_same_day_blocked(self):
        self.submit()
        self.bundle['instagram']['caption'] += '\nCaption lain.'
        with self.assertRaisesRegex(ValueError, 'sudah ada'):
            self.submit()
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 2)

    def test_other_connection_cannot_duplicate_daily_pair(self):
        first = self.submit()
        other = Queue(self.temp.name)
        try:
            self.assertEqual(DailyContent(other).submit(self.day, self.bundle, self.image), first)
        finally:
            other.db.close()

    def test_failed_second_insert_rolls_back_entire_batch(self):
        self.queue.db.execute("""CREATE TRIGGER fail_threads BEFORE INSERT ON drafts
            WHEN NEW.payload LIKE '%\"channel\":\"threads\"%' BEGIN
            SELECT RAISE(ABORT, 'test failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.submit()
        self.assertIsNone(self.daily.status(self.day))
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 0)

    def test_invalid_threads_never_inserts_instagram(self):
        self.bundle['threads']['text'] = 'x'*501
        with self.assertRaises(ValueError):
            self.submit()
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 0)

    def test_exact_old_content_not_reused_as_new_daily_batch(self):
        self.queue.add('threads', self.bundle['threads'])
        with self.assertRaisesRegex(ValueError, 'identik'):
            self.submit()
        self.assertIsNone(self.daily.status(self.day))

    def test_old_or_future_day_cannot_create_batch(self):
        for day in ('2026-11-27', '2026-11-29'):
            with self.assertRaises(ValueError):
                self.daily.submit(day, self.bundle, self.image)

    def test_target_alt_text_and_status_validation(self):
        for edit in ('target','alt','status'):
            bundle = copy.deepcopy(self.bundle)
            if edit == 'target':
                bundle['instagram']['account'] = 'another.account'
            elif edit == 'alt':
                bundle['instagram']['alt_text'] = ''
            else:
                bundle['status'] = 'approved'
            with self.assertRaises(ValueError):
                self.submit(bundle)

    def test_daily_dry_run_sends_nothing_and_changes_no_decisions(self):
        batch = self.submit()
        result = self.daily.send(self.day, self.config, transport=self.transport)
        self.assertEqual(self.calls, [])
        self.assertEqual(len(result['delivery']), 4)
        self.assertFalse(result['buffer_called'])
        self.assertFalse(result['approvals_changed'])
        self.assertEqual(batch, self.daily.status(self.day))

    def test_full_pair_sent_to_owner_without_duplicates_or_buffer(self):
        batch = self.submit()
        result = self.daily.send(self.day, self.config, send=True, transport=self.transport)
        self.daily.send(self.day, self.config, send=True, transport=self.transport)
        self.assertEqual([call[0] for call in self.calls], ['sendPhoto','sendMessage','sendDocument','sendMessage'])
        self.assertEqual({call[1]['chat_id'] for call in self.calls}, {'42'})
        self.assertIn(self.bundle['instagram']['caption'], self.calls[1][1]['text'])
        self.assertIn(self.bundle['threads']['text'], self.calls[3][1]['text'])
        self.assertEqual(self.calls[2][2][1], self.image.read_bytes())
        self.assertFalse(result['published'])
        self.assertEqual(batch, self.daily.status(self.day))
        self.assertFalse(self.queue.db.execute("SELECT 1 FROM sqlite_master WHERE name='buffer_exports'").fetchone())

    def test_uncertain_stops_repeat_without_creating_second_pair(self):
        batch = self.submit()
        def uncertain(*args):
            self.calls.append(args)
            raise DeliveryUncertain('Unknown Telegram result')
        with self.assertRaises(DeliveryUncertain):
            self.daily.send(self.day, self.config, send=True, transport=uncertain)
        with self.assertRaises(DeliveryUncertain):
            self.daily.send(self.day, self.config, send=True, transport=self.transport)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(batch, self.submit())

    def test_already_decided_channel_not_reopened_or_resent(self):
        batch = self.submit()
        self.queue.db.execute("UPDATE drafts SET status='review_approved' WHERE id=?", (batch['instagram_id'],))
        self.queue.db.commit()
        self.daily.send(self.day, self.config, send=True, transport=self.transport)
        self.assertEqual([call[0] for call in self.calls], ['sendMessage'])
        self.assertEqual(self.queue.get(batch['instagram_id'])['status'], 'review_approved')

    def test_missing_batch_does_not_send_other_pending_drafts(self):
        self.queue.add('threads', self.bundle['threads'])
        with self.assertRaises(ValueError):
            self.daily.send(self.day, self.config, send=True, transport=self.transport)
        self.assertEqual(self.calls, [])

    def test_plan_rotates_three_pillars_and_surfaces_history(self):
        self.submit()
        plans = [self.daily.plan(day) for day in ('2026-11-28','2026-11-29','2026-11-30')]
        self.assertEqual({plan['pillar'] for plan in plans}, set(PILLARS))
        self.assertIsNotNone(plans[0]['existing'])
        self.assertEqual(len(plans[0]['recent_content']), 2)
        self.assertEqual(datetime(2026,11,27,18,0,tzinfo=timezone.utc).astimezone(WIB).date().isoformat(), self.day)

    def test_plan_rejects_corrupted_queue_digest(self):
        batch = self.submit()
        self.queue.db.execute("UPDATE drafts SET digest='corrupted' WHERE id=?", (batch['threads_id'],))
        self.queue.db.commit()
        with self.assertRaisesRegex(ValueError, 'berubah'):
            self.daily.plan(self.day)

    def tomorrow_mode(self):
        return DailyContent(self.queue, days_ahead=1, intended_time='09:00')

    def test_prepare_next_day_without_reusing_todays_already_posted_pair(self):
        old = self.submit()
        revised = copy.deepcopy(self.bundle)
        revised['instagram']['caption'] = 'Konten baru untuk besok, tetap perlu review.'
        revised['threads']['text'] = 'Tulisan baru untuk besok. Bagian mana yang ingin kamu rapikan?'
        daily = self.tomorrow_mode()
        self.assertEqual(daily.expected_day(), '2026-11-29')
        new = daily.submit('2026-11-29', revised, self.image)
        self.assertNotEqual(old['instagram_id'], new['instagram_id'])
        self.assertNotEqual(old['threads_id'], new['threads_id'])
        self.assertEqual(old, self.daily.status(self.day))
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 4)

    def test_h12_preview_labels_target_date_without_changing_public_text(self):
        daily = self.tomorrow_mode()
        batch = daily.submit('2026-11-29', self.bundle, self.image)
        daily.send('2026-11-29', self.config, send=True, transport=self.transport)
        for index in (0, 1, 3):
            fields = self.calls[index][1]
            text = fields.get('text', fields.get('caption'))
            self.assertIn('Disiapkan: 2026-11-28', text)
            self.assertIn('Untuk konten: 2026-11-29 · 09:00 WIB', text)
            self.assertIn('posting MANUAL', text)
        payload = self.queue.verify_content(self.queue.get(batch['instagram_id']))
        self.assertEqual(payload['content']['caption'], self.bundle['instagram']['caption'])
        self.assertEqual(payload['editorial_plan']['publication'], 'manual')
        self.assertFalse(self.queue.db.execute("SELECT 1 FROM sqlite_master WHERE name='buffer_exports'").fetchone())

    def test_next_day_repeat_uses_same_ids_and_sends_no_duplicate_messages(self):
        daily = self.tomorrow_mode()
        first = daily.submit('2026-11-29', self.bundle, self.image)
        self.assertEqual(daily.submit('2026-11-29', self.bundle, self.image), first)
        daily.send('2026-11-29', self.config, send=True, transport=self.transport)
        daily.send('2026-11-29', self.config, send=True, transport=self.transport)
        self.assertEqual(len(self.calls), 4)

    def test_changed_planning_date_cannot_disguise_duplicate_content(self):
        self.submit()
        with self.assertRaisesRegex(ValueError, 'identik'):
            self.tomorrow_mode().submit('2026-11-29', self.bundle, self.image)
        self.assertIsNone(self.daily.status('2026-11-29'))

    def test_tomorrow_mode_blocks_today_and_day_after_tomorrow(self):
        for day in ('2026-11-28', '2026-11-30'):
            with self.assertRaises(ValueError):
                self.tomorrow_mode().submit(day, self.bundle, self.image)

    def test_h12_date_rollover_month_and_year(self):
        for prepared, intended in [('2026-11-30','2026-12-01'), ('2026-12-31','2027-01-01')]:
            with patch('daily_content.today',return_value=prepared):
                self.assertEqual(self.tomorrow_mode().expected_day(), intended)

    def test_revision_keeps_manual_posting_reference(self):
        batch = self.tomorrow_mode().submit('2026-11-29', self.bundle, self.image)
        parent = batch['threads_id']
        self.queue.db.execute("UPDATE drafts SET status='needs_revision' WHERE id=?", (parent,))
        self.queue.db.commit()
        child = self.queue.add('threads', {'account':'ignidi.labs','text':'Versi revisi yang lebih singkat.'}, revision_of=parent)
        original = self.queue.verify_content(self.queue.get(parent))
        changed = self.queue.verify_content(self.queue.get(child))
        self.assertEqual(changed['editorial_plan'], original['editorial_plan'])
        self.assertEqual(self.queue.get(child)['status'], 'draft')
        from send_review import review_parts
        self.assertIn('Untuk konten: 2026-11-29 · 09:00 WIB', review_parts(self.queue, self.queue.get(child), preview=True)[0][2]['text'])

    def test_unchanged_revision_not_accepted_just_because_plan_is_omitted(self):
        batch = self.tomorrow_mode().submit('2026-11-29', self.bundle, self.image)
        parent = batch['threads_id']
        self.queue.db.execute("UPDATE drafts SET status='needs_revision' WHERE id=?", (parent,))
        self.queue.db.commit()
        with self.assertRaisesRegex(ValueError, 'belum mengubah'):
            self.queue.add('threads', self.bundle['threads'], revision_of=parent)


if __name__ == '__main__':
    unittest.main()
