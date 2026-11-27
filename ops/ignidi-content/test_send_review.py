import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from content_queue import Queue
from send_review import load_config, send_reviews, pending_ids, TelegramFailure, DeliveryUncertain

class ReviewDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.config = {'token': '123:' + 'x'*30, 'chat_id':'42'}
        self.id = self.queue.add('threads', {'account':'ignidi.labs', 'text':'Teks draf asli untuk review.'})
        self.calls = []
    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()
    def transport(self, method, fields, file):
        self.calls.append((method,fields,file))
        return len(self.calls) + 100
    def send(self, ids=None, send=True, transport=None):
        return send_reviews(self.queue, ids or [self.id], self.config, send=send, transport=transport or self.transport)
    def test_dry_run_does_not_send_or_approve(self):
        self.assertEqual(self.send(send=False)[0]['status'], 'would_send')
        self.assertEqual(self.calls, [])
        self.assertEqual(self.queue.get(self.id)['status'], 'draft')
    def test_threads_exact_text_without_photo_or_approval(self):
        self.send()
        self.assertEqual(self.calls[0][0], 'sendMessage')
        self.assertIn('Teks draf asli untuk review.', self.calls[0][1]['text'])
        self.assertIn(self.queue.get(self.id)['digest'], self.calls[0][1]['text'])
        self.assertIsNone(self.calls[0][2])
        self.assertEqual(self.calls[0][1]['chat_id'], '42')
        self.assertEqual(self.queue.get(self.id)['status'], 'draft')
    def test_pending_moves_past_already_sent_drafts(self):
        self.send()
        second = self.queue.add('threads', {'account':'ignidi.labs','text':'Draf baru'})
        self.assertEqual(pending_ids(self.queue, '42', 2), [second])
    def test_repeat_send_skips_confirmed_messages(self):
        self.send()
        self.assertEqual(self.send()[0]['status'], 'already_sent')
        self.assertEqual(len(self.calls), 1)
    def test_photo_caption_original_are_separate_review_parts(self):
        image = Path(self.temp.name)/'image.jpg'
        data = b'\xff\xd8\xff' + b'demo'
        image.write_bytes(data)
        draft = self.queue.add('instagram', {'account':'ignidi.labs','caption':'Caption lengkap','alt_text':'Gambar contoh'}, image)
        self.send([draft])
        self.assertEqual([call[0] for call in self.calls], ['sendPhoto','sendMessage','sendDocument'])
        self.assertEqual(self.calls[2][2][1], data)
        self.assertIn('Caption lengkap', self.calls[1][1]['text'])
        self.assertEqual(self.queue.get(draft)['status'], 'draft')
    def test_unknown_result_is_not_retried(self):
        def lost(*args): raise TimeoutError('url-with-secret-must-not-leak')
        with self.assertRaises(DeliveryUncertain) as result: self.send(transport=lost)
        self.assertNotIn('secret',str(result.exception))
        with self.assertRaises(DeliveryUncertain): self.send()
        self.assertEqual(self.calls, [])
    def test_definitive_failure_can_retry(self):
        def denied(*args): raise TelegramFailure('denied')
        with self.assertRaises(TelegramFailure): self.send(transport=denied)
        self.assertEqual(self.send()[0]['status'],'sent')
    def test_partial_delivery_resumes_without_repeating_photo(self):
        image = Path(self.temp.name)/'image.jpg'
        image.write_bytes(b'\xff\xd8\xffdemo')
        draft = self.queue.add('instagram', {'account':'ignidi.labs','caption':'Caption'}, image)
        def partial(method, fields, file):
            if method == 'sendMessage': raise TelegramFailure('denied')
            return self.transport(method,fields,file)
        with self.assertRaises(TelegramFailure): self.send([draft],transport=partial)
        self.send([draft])
        self.assertEqual([call[0] for call in self.calls], ['sendPhoto','sendMessage','sendDocument'])
    def test_rejected_or_tampered_draft_is_not_sent(self):
        self.queue.reject(self.id)
        with self.assertRaises(ValueError): self.send()
        self.assertEqual(self.calls, [])
    def test_whole_batch_is_verified_before_any_send(self):
        second = self.queue.add('threads', {'account':'ignidi.labs','text':'Draf kedua'})
        self.queue.db.execute("UPDATE drafts SET payload='{}' WHERE id=?", (second,))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.send([self.id,second])
        self.assertEqual(self.calls, [])
    def test_config_reads_only_needed_keys_without_executing_shell(self):
        file = Path(self.temp.name)/'.env'
        file.write_text('TELEGRAM_BOT_TOKEN="123:'+ 'x'*30 +'"\nTELEGRAM_ALLOWED_USERS=42\nOTHER_SECRET=ignored\n',encoding='utf8')
        with patch.dict(os.environ,{},clear=True):
            config = load_config(file)
        self.assertEqual(config['chat_id'],'42')
        self.assertNotIn('OTHER_SECRET',config)
    def test_config_blocks_public_access_and_nonowner_chat(self):
        file = Path(self.temp.name)/'.env'
        for allowed, chat in [('*','42'),('42','-100123'),('42','99'),('','42')]:
            file.write_text(f'TELEGRAM_BOT_TOKEN=123:{"x"*30}\nTELEGRAM_ALLOWED_USERS={allowed}\nIGNIDI_REVIEW_CHAT_ID={chat}\n',encoding='utf8')
            with patch.dict(os.environ,{},clear=True):
                with self.assertRaises(ValueError): load_config(file)

if __name__ == '__main__': unittest.main()
