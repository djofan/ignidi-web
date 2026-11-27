import hashlib
import tempfile
import unittest
from pathlib import Path
from content_queue import Queue

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.key = 'test-reviewer-secret-' * 3
        self.content = {'account': 'ignidi.labs', 'text': 'Contoh untuk review, belum dipublikasikan.'}
        self.id = self.queue.add('threads', self.content)
    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()
    def approve(self, draft_id=None):
        draft_id = draft_id or self.id
        self.queue.approve(draft_id, self.queue.get(draft_id)['digest'], 'reviewer-demo', self.key)
    def test_drafts_are_not_approved(self):
        with self.assertRaises(ValueError): self.queue.approved(self.id, self.key)
    def test_exact_content_approved(self):
        self.approve()
        self.assertEqual(self.queue.approved(self.id, self.key)['content'], self.content)
    def test_wrong_digest_is_rejected(self):
        with self.assertRaises(ValueError): self.queue.approve(self.id, '0' * 64, 'reviewer', self.key)
    def test_no_key_cannot_approve(self):
        with self.assertRaises(ValueError): self.queue.approve(self.id, self.queue.get(self.id)['digest'], 'reviewer', '')
    def test_changed_text_invalidates_approval(self):
        self.approve()
        self.queue.db.execute("UPDATE drafts SET payload=replace(payload,'review','revisi') WHERE id=?", (self.id,))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.queue.approved(self.id, self.key)
    def test_status_tampering_cannot_fake_signature(self):
        self.queue.db.execute("UPDATE drafts SET status='approved',signature='fake' WHERE id=?", (self.id,))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.queue.approved(self.id, self.key)
    def test_edited_content_creates_new_pending_draft(self):
        self.approve()
        other = self.queue.add('threads', {**self.content, 'text':'Revisi baru'})
        self.assertNotEqual(other, self.id)
        self.assertEqual(self.queue.get(other)['status'], 'draft')
    def test_duplicate_ingest_returns_existing_id(self):
        self.assertEqual(self.queue.add('threads', self.content), self.id)
    def test_rejection_revokes_approval(self):
        self.approve()
        self.queue.reject(self.id)
        with self.assertRaises(ValueError): self.queue.approved(self.id, self.key)
    def test_image_tampering_is_rejected(self):
        image = Path(self.temp.name) / 'example.jpg'
        image.write_bytes(b'\xff\xd8\xff' + b'example')
        draft = self.queue.add('instagram', {'account':'ignidi.labs','caption':'Contoh'}, image)
        self.approve(draft)
        media = next((Path(self.temp.name) / 'media').iterdir())
        media.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.queue.approved(draft, self.key)
    def test_threads_limit_and_account_guard(self):
        with self.assertRaises(ValueError): self.queue.add('threads', {**self.content,'text':'a'*501})
        with self.assertRaises(ValueError): self.queue.add('threads', {**self.content,'account':'other'})

if __name__ == '__main__': unittest.main()
