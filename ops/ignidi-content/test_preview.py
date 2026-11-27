import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from content_queue import Queue
from review_workflow import Reviews
from send_review import send_preview, send_reviews, DeliveryUncertain, TelegramFailure


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.config = {'token':'123:' + 'x'*30,'chat_id':'42'}
        self.owner = SimpleNamespace(user_id='42',chat_id='42',chat_type='dm')
        self.reviews = Reviews(self.queue,'42')
        self.image = Path(self.temp.name)/'source.jpg'
        self.image.write_bytes(b'\xff\xd8\xfforiginal-for-review')
        self.ig = self.queue.add('instagram',{'account':'ignidi.labs','caption':'Caption lengkap.','alt_text':'Logo oranye.'},self.image)
        self.threads = self.queue.add('threads',{'account':'ignidi.labs','text':'Isi Threads.'})
        self.calls = []

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def transport(self,method,fields,file):
        self.calls.append((method,fields,file))
        return 100 + len(self.calls)

    def preview(self,draft_id=None,transport=None,config=None):
        return send_preview(self.queue,draft_id or self.ig,config or self.config,transport=transport or self.transport)

    def decide(self,action,draft_id=None,notes=''):
        draft_id = draft_id or self.ig
        raw = f'{draft_id} {self.queue.get(draft_id)["digest"]}' + (' '+notes if notes else '')
        return self.reviews.decide(action,raw,platform='telegram',source=self.owner)

    def test_instagram_reappears_even_after_original_delivery(self):
        send_reviews(self.queue,[self.ig],self.config,send=True,transport=self.transport)
        original_delivery = [dict(row) for row in self.queue.db.execute('SELECT * FROM review_deliveries')]
        original_draft = self.queue.get(self.ig)
        result = self.preview()
        self.assertEqual([call[0] for call in self.calls[3:]],['sendPhoto','sendMessage','sendDocument'])
        self.assertEqual(self.calls[3][2][1],self.image.read_bytes())
        self.assertEqual(self.calls[5][2][1],self.image.read_bytes())
        message = self.calls[4][1]['text']
        for text in ('Caption lengkap.','Logo oranye.',self.ig,original_draft['digest'],'MENUNGGU REVIEW'):
            self.assertIn(text,message)
        self.assertFalse(result['published_to_meta'])
        self.assertFalse(result['approvals_changed'])
        self.assertEqual(self.queue.get(self.ig),original_draft)
        self.assertEqual([dict(row) for row in self.queue.db.execute('SELECT * FROM review_deliveries')],original_delivery)

    def test_explicit_repeat_is_a_fresh_request(self):
        first = self.preview()
        second = self.preview()
        self.assertNotEqual(first['request_id'],second['request_id'])
        self.assertEqual(len(self.calls),6)
        self.assertEqual(self.queue.db.execute("SELECT COUNT(*) FROM preview_deliveries WHERE status='sent'").fetchone()[0],6)

    def test_threads_preview_only_sends_exact_text(self):
        self.preview(self.threads)
        self.assertEqual(len(self.calls),1)
        method,fields,file = self.calls[0]
        self.assertEqual(method,'sendMessage')
        self.assertIn('TULISAN THREADS:\nIsi Threads.',fields['text'])
        self.assertEqual(fields['chat_id'],'42')
        self.assertIsNone(file)

    def test_complete_preview_enables_review_but_does_not_approve(self):
        self.preview()
        self.assertEqual(self.queue.get(self.ig)['status'],'draft')
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM editorial_reviews').fetchone()[0],0)
        self.decide('setuju')
        self.assertEqual(self.queue.get(self.ig)['status'],'review_approved')
        with self.assertRaises(ValueError): self.queue.approved(self.ig,'x'*64)

    def test_approved_preview_preserves_decision_and_has_correct_label(self):
        self.preview()
        self.decide('setuju')
        before = self.queue.get(self.ig)
        reviews_before = [dict(row) for row in self.queue.db.execute('SELECT * FROM editorial_reviews')]
        self.calls.clear()
        self.preview()
        self.assertIn('DISETUJUI PEMILIK',self.calls[1][1]['text'])
        self.assertNotIn('/setuju ',self.calls[1][1]['text'])
        self.assertEqual(self.queue.get(self.ig),before)
        self.assertEqual([dict(row) for row in self.queue.db.execute('SELECT * FROM editorial_reviews')],reviews_before)

    def test_old_version_preview_is_labelled_and_never_resurrected(self):
        self.preview()
        self.decide('revisi',notes='Ganti caption.')
        child = self.queue.add('instagram',{'account':'ignidi.labs','caption':'Caption baru.'},self.image,revision_of=self.ig)
        self.calls.clear()
        self.preview()
        text = self.calls[1][1]['text']
        self.assertIn('VERSI LAMA',text)
        self.assertIn('DIGANTIKAN REVISI',text)
        self.assertIn('Caption lengkap.',text)
        self.assertNotIn('/setuju ',text)
        self.assertNotIn('/revisi ',text)
        self.assertEqual(self.queue.get(self.ig)['status'],'superseded')
        self.assertEqual(self.queue.get(child)['status'],'draft')
        self.assertIn(child,self.reviews.status(self.ig,platform='telegram',source=self.owner))

    def test_rejected_and_needs_revision_drafts_remain_closed(self):
        for action, expected in [('tolak','DITOLAK'),('revisi','PERLU REVISI')]:
            draft = self.queue.add('threads',{'account':'ignidi.labs','text':action})
            self.preview(draft)
            self.decide(action,draft,notes='Catatan.' if action == 'revisi' else '')
            before = self.queue.get(draft)
            self.calls.clear()
            self.preview(draft)
            self.assertIn(expected,self.calls[0][1]['text'])
            self.assertNotIn('/setuju ',self.calls[0][1]['text'])
            self.assertEqual(self.queue.get(draft),before)

    def test_bad_id_extra_args_and_missing_id_send_nothing(self):
        for raw in ('',self.ig+' extra','../../etc/passwd','0'*16):
            with self.assertRaises(ValueError): send_preview(self.queue,raw,self.config,transport=self.transport)
        self.assertEqual(self.calls,[])

    def test_tampered_text_or_image_send_nothing(self):
        self.queue.db.execute("UPDATE drafts SET payload=replace(payload,'Isi','Palsu') WHERE id=?",(self.threads,))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.preview(self.threads)
        media = self.queue.directory/'media'/f'{hashlib.sha256(self.image.read_bytes()).hexdigest()}.jpg'
        media.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.preview()
        self.assertEqual(self.calls,[])

    def test_oversize_message_rejected_before_any_photo(self):
        draft = self.queue.add('instagram',{'account':'ignidi.labs','caption':'Valid','alt_text':'x'*4096},self.image)
        with self.assertRaises(ValueError): self.preview(draft)
        self.assertEqual(self.calls,[])

    def test_timeout_stops_without_retry_or_leaking_error(self):
        attempted = []
        def timeout(method,fields,file):
            attempted.append(method)
            raise TimeoutError('secret-token-in-url')
        with self.assertRaises(DeliveryUncertain) as error: self.preview(transport=timeout)
        self.assertNotIn('secret',str(error.exception))
        self.assertEqual(attempted,['sendPhoto'])
        self.assertEqual([row[0] for row in self.queue.db.execute('SELECT status FROM preview_deliveries ORDER BY rowid')],['uncertain','pending','pending'])
        self.assertEqual(self.queue.get(self.ig)['status'],'draft')
        with self.assertRaises(ValueError): self.decide('setuju')

    def test_partial_failure_is_audited_and_does_not_change_original_delivery(self):
        def partial(method,fields,file):
            if method == 'sendMessage': raise TelegramFailure('rejected')
            return self.transport(method,fields,file)
        with self.assertRaises(TelegramFailure): self.preview(transport=partial)
        self.assertEqual(self.queue.db.execute('SELECT COUNT(*) FROM review_deliveries').fetchone()[0],0)
        self.assertEqual([row[0] for row in self.queue.db.execute('SELECT status FROM preview_deliveries ORDER BY rowid')],['sent','failed','pending'])
        with self.assertRaises(ValueError): self.decide('setuju')

    def test_delivery_evidence_must_be_one_complete_request_to_owner(self):
        digest = self.queue.get(self.ig)['digest']
        for request,chat,parts in [('one','42',['instagram-preview']),('two','42',['instagram-caption','instagram-original']),('other','99',['instagram-preview','instagram-caption','instagram-original'])]:
            self.queue.db.executemany('INSERT INTO preview_deliveries (request_id,draft_id,digest,chat_id,part,status) VALUES (?,?,?,?,?,?)',[(request,self.ig,digest,chat,part,'sent') for part in parts])
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.decide('setuju')
        self.preview()
        self.decide('setuju')


if __name__ == '__main__': unittest.main()
