import importlib.util
import shutil
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from content_queue import Queue
from review_workflow import Reviews
from send_review import send_reviews


class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(Path(self.temp.name)/'state')
        self.config = {'token':'123:' + 'x'*30, 'chat_id':'42'}
        self.source = SimpleNamespace(user_id='42', chat_id='42', chat_type='dm')
        self.reviews = Reviews(self.queue, '42')
        self.id = self.queue.add('threads', {'account':'ignidi.labs', 'text':'Teks awal.'})
        self.deliver(self.id)

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def deliver(self, draft_id):
        send_reviews(self.queue, [draft_id], self.config, send=True, transport=lambda *args: 123)

    def decide(self, action, draft_id=None, notes='', **kwargs):
        draft_id = draft_id or self.id
        raw = f'{draft_id} {self.queue.get(draft_id)["digest"]}' + (' ' + notes if notes else '')
        return self.reviews.decide(action, raw, platform=kwargs.get('platform','telegram'), source=kwargs.get('source',self.source))

    def test_exact_owner_approval_is_editorial_and_cannot_publish(self):
        self.decide('setuju')
        row = self.queue.get(self.id)
        self.assertEqual(row['status'], 'review_approved')
        self.assertIsNone(row['signature'])
        with self.assertRaises(ValueError): self.queue.approved(self.id, 'x'*64)

    def test_approval_does_not_approve_other_platform(self):
        image = Path(self.temp.name)/'preview.jpg'
        image.write_bytes(b'\xff\xd8\xffdemo')
        other = self.queue.add('instagram', {'account':'ignidi.labs','caption':'Caption.'}, image)
        self.decide('setuju')
        self.assertEqual(self.queue.get(other)['status'], 'draft')

    def test_wrong_actor_chat_group_cli_and_missing_source_rejected(self):
        for platform, source in (
            ('telegram', SimpleNamespace(user_id='99', chat_id='42', chat_type='dm')),
            ('telegram', SimpleNamespace(user_id='42', chat_id='99', chat_type='dm')),
            ('telegram', SimpleNamespace(user_id='42', chat_id='42', chat_type='group')),
            ('local', self.source), ('telegram',None), ('telegram',{'user_id':'42','chat_id':'42','chat_type':'dm'}),
        ):
            with self.subTest(platform=platform,source=source):
                with self.assertRaises(ValueError): self.decide('setuju', platform=platform, source=source)
        self.assertEqual(self.queue.get(self.id)['status'],'draft')

    def test_missing_version_wrong_version_and_casual_ok_not_approval(self):
        for raw in ('oke',self.id,self.id+' '+ '0'*64,self.id+' '+self.queue.get(self.id)['digest']+' anything'):
            with self.assertRaises(ValueError):
                self.reviews.decide('setuju', raw, platform='telegram',source=self.source)
        self.assertEqual(self.queue.get(self.id)['status'],'draft')

    def test_incomplete_preview_blocks_decision(self):
        image = Path(self.temp.name)/'preview.jpg'
        image.write_bytes(b'\xff\xd8\xffdemo')
        draft = self.queue.add('instagram', {'account':'ignidi.labs','caption':'Caption.'}, image)
        self.queue.db.execute("INSERT INTO review_deliveries (draft_id,digest,chat_id,part,status) VALUES (?,?,?,?,?)", (draft,self.queue.get(draft)['digest'],'42','instagram-preview','sent'))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.decide('setuju',draft)

    def test_duplicate_approval_is_idempotent(self):
        first, fresh = self.decide('setuju')
        second, repeated = self.decide('setuju')
        self.assertTrue(fresh)
        self.assertFalse(repeated)
        self.assertEqual(first['event_id'],second['event_id'])

    def test_revision_revokes_and_creates_pending_child(self):
        self.decide('setuju')
        self.decide('revisi',notes='Buat lebih singkat.')
        self.assertEqual(self.queue.get(self.id)['status'],'needs_revision')
        with self.assertRaises(ValueError): self.decide('setuju')
        new_id = self.queue.add('threads', {'account':'ignidi.labs','text':'Lebih singkat.'}, revision_of=self.id)
        self.assertNotEqual(new_id,self.id)
        self.assertEqual(self.queue.get(new_id)['status'],'draft')
        self.assertEqual(self.queue.get(self.id)['status'],'superseded')
        payload = self.queue.verify_content(self.queue.get(new_id))
        self.assertEqual(payload['revision'], {'parent_id':self.id,'number':2})
        with self.assertRaises(ValueError): self.decide('setuju',new_id)
        self.deliver(new_id)
        self.decide('setuju',new_id)
        with self.assertRaises(ValueError): self.decide('setuju',self.id)

    def test_unchanged_or_wrong_channel_revision_rejected(self):
        self.decide('revisi',notes='Ganti kalimat.')
        with self.assertRaises(ValueError): self.queue.add('threads',{'account':'ignidi.labs','text':'Teks awal.'},revision_of=self.id)
        image = Path(self.temp.name)/'preview.jpg'
        image.write_bytes(b'\xff\xd8\xffdemo')
        with self.assertRaises(ValueError): self.queue.add('instagram', {'account':'ignidi.labs','caption':'Caption'}, image, revision_of=self.id)
        self.assertEqual(self.queue.get(self.id)['status'],'needs_revision')

    def test_cannot_revise_unrequested_draft(self):
        with self.assertRaises(ValueError): self.queue.add('threads', {'account':'ignidi.labs','text':'Baru.'},revision_of=self.id)

    def test_reject_revokes_and_blocks_later_approval(self):
        self.decide('setuju')
        self.decide('tolak',notes='Tidak dipakai.')
        self.assertEqual(self.queue.get(self.id)['status'],'rejected')
        with self.assertRaises(ValueError): self.decide('setuju')

    def test_revision_notes_required_bounded_and_dispatch_claim_once(self):
        for notes in ('','x'*1201):
            with self.assertRaises(ValueError): self.decide('revisi',notes=notes)
        event, _ = self.decide('revisi',notes='Lebih konkret.')
        repeated, fresh = self.decide('revisi',notes='Lebih konkret.')
        self.assertFalse(fresh)
        self.assertEqual(event['event_id'],repeated['event_id'])
        self.assertTrue(self.reviews.claim_revision_dispatch(event['event_id']))
        self.assertFalse(self.reviews.claim_revision_dispatch(event['event_id']))
        self.reviews.finish_revision_dispatch(event['event_id'],True)
        self.assertEqual(self.reviews.latest_revision(self.id)['dispatch'],'queued')

    def test_content_tampering_blocks_approval(self):
        self.queue.db.execute("UPDATE drafts SET payload=replace(payload,'awal','diubah') WHERE id=?",(self.id,))
        self.queue.db.commit()
        with self.assertRaises(ValueError): self.decide('setuju')

    def test_status_does_not_decide_and_shows_exact_commands(self):
        text = self.reviews.status(self.id,platform='telegram',source=self.source)
        self.assertIn('/setuju '+self.id+' '+self.queue.get(self.id)['digest'],text)
        self.assertIn('nonaktif',text)
        self.assertEqual(self.queue.get(self.id)['status'],'draft')

    def test_second_revision_requires_another_review(self):
        self.decide('revisi',notes='Singkat.')
        child = self.queue.add('threads',{'account':'ignidi.labs','text':'Baru.'},revision_of=self.id)
        self.deliver(child)
        self.decide('revisi',child,notes='Tambahkan pertanyaan.')
        newest = self.queue.add('threads',{'account':'ignidi.labs','text':'Ada pertanyaan?'},revision_of=child)
        self.assertEqual(self.queue.verify_content(self.queue.get(newest))['revision']['number'],3)
        self.assertEqual(self.queue.get(newest)['status'],'draft')

    def test_concurrent_replacement_cannot_create_two_children(self):
        self.decide('revisi',notes='Ubah.')
        self.queue.add('threads',{'account':'ignidi.labs','text':'A.'},revision_of=self.id)
        with self.assertRaises(ValueError): self.queue.add('threads',{'account':'ignidi.labs','text':'B.'},revision_of=self.id)

    def test_installed_plugin_registers_identity_handlers_and_dispatches_once(self):
        studio = Path(__file__).parent
        target = Path(self.temp.name)/'plugin'
        target.mkdir()
        shutil.copyfile(studio/'hermes_plugin/entrypoint.py',target/'__init__.py')
        for name in ('content_queue.py','send_review.py','review_workflow.py'):
            shutil.copyfile(studio/name,target/name)
        (target/'studio-path.txt').write_text(str(studio))
        spec = importlib.util.spec_from_file_location('ignidi_test_plugin',target/'__init__.py',submodule_search_locations=[str(target)])
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        class Context:
            def __init__(self): self.handlers, self.injected = {}, []
            def register_command(self,name,handler,description): self.handlers[name]=handler
            def inject_message(self,text,session_key): self.injected.append((text,session_key)); return True
        ctx = Context()
        module.register(ctx)
        self.assertEqual(set(ctx.handlers),{'statuskonten','preview','setuju','revisi','tolak'})
        with patch.object(module,'load_config',return_value=self.config), patch.dict('os.environ',{'IGNIDI_CONTENT_STATE':str(self.queue.directory)}), patch.object(module,'send_preview',return_value={'draft':self.id}) as preview:
            ctx.handlers['preview'](self.id)
            preview.assert_not_called()
            reply = ctx.handlers['preview'](self.id,platform='telegram',source=self.source)
            preview.assert_called_once()
            self.assertIn('ditampilkan ulang',reply)
        raw = f'{self.id} {self.queue.get(self.id)["digest"]} Ringkas.'
        with patch.object(module,'load_config',return_value=self.config), patch.dict('os.environ',{'IGNIDI_CONTENT_STATE':str(self.queue.directory)}):
            refused = ctx.handlers['setuju'](raw.split(' Ringkas.')[0])
            self.assertIn('tidak diproses',refused)
            reply = ctx.handlers['revisi'](raw,platform='telegram',source=self.source,session_key='known-session')
            ctx.handlers['revisi'](raw,platform='telegram',source=self.source,session_key='known-session')
        self.assertIn('menerima tugas',reply)
        self.assertEqual(len(ctx.injected),1)
        self.assertEqual(ctx.injected[0][1],'known-session')
        self.assertIn('revision.py show '+self.id,ctx.injected[0][0])


if __name__ == '__main__': unittest.main()
