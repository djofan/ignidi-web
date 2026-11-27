import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error

from content_queue import Queue
from review_workflow import Reviews
from send_review import send_preview
from buffer_drafts import (BufferAPI, BufferError, BufferUncertain, CREATE_DRAFT,
    ensure_tables, load_config, valid_channel, stage_draft, status, reconcile)
from buffer_media import approved_image_url, validate_url, upload_jpeg
from setup_buffer import save_config


class FakeBuffer:
    def __init__(self,config):
        self.config = config
        self.creates, self.posts = [], {}
        self.disconnected = False

    def channel(self,channel_id):
        service = next(key for key,value in self.config['channels'].items() if value == channel_id)
        return {'id':channel_id,'service':service,'name':'ignidi.labs',
                'organizationId':self.config['organization_id'],'isDisconnected':self.disconnected,'isLocked':False}

    def post(self,post_id):
        return self.posts[post_id]

    def create_draft(self,**kwargs):
        self.creates.append(kwargs)
        post_id = 'remote-'+str(len(self.creates))
        post = {'id':post_id,'channelId':kwargs['channel_id'],'text':kwargs['text'],
                'status':'draft','dueAt':None,
                'assets':[{'source':item['image']['url']} for item in kwargs['assets']]}
        self.posts[post_id] = post
        return post


class BufferDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.owner = '42'
        self.source = SimpleNamespace(user_id='42',chat_id='42',chat_type='dm')
        self.reviews = Reviews(self.queue,self.owner)
        self.config = {'mode':'draft_only','auto_stage':True,'api_key':'private-test-token',
            'organization_id':'org','channels':{'instagram':'ig-channel','threads':'threads-channel'},
            'cloudinary':{'cloud_name':'testcloud','api_key':'cloud-key','api_secret':'cloud-secret'}}
        self.api = FakeBuffer(self.config)
        self.image = Path(self.temp.name)/'source.jpg'
        self.image.write_bytes(b'\xff\xd8\xffapproved-original')
        self.ig = self.queue.add('instagram',{'account':'ignidi.labs','caption':'Caption asli.','alt_text':'Logo asli.'},self.image)
        self.threads = self.queue.add('threads',{'account':'ignidi.labs','text':'Threads asli.'})
        self.uploads = []

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def decide(self,action,draft_id=None,notes=''):
        draft_id = draft_id or self.ig
        raw = f'{draft_id} {self.queue.get(draft_id)["digest"]}' + (' '+notes if notes else '')
        return self.reviews.decide(action,raw,platform='telegram',source=self.source)

    def approve(self,draft_id=None):
        draft_id = draft_id or self.ig
        send_preview(self.queue,draft_id,{'token':'123:'+'x'*30,'chat_id':self.owner},transport=lambda *args:123)
        self.decide('setuju',draft_id)

    def media(self,queue,payload,config):
        self.uploads.append(payload['image_sha256'])
        return f'https://res.cloudinary.com/testcloud/image/upload/v1/ignidi-labs/{payload["image_sha256"]}.jpg'

    def stage(self,draft_id=None,**kwargs):
        return stage_draft(self.queue,draft_id or self.ig,self.owner,config=self.config,api=self.api,media=kwargs.get('media',self.media))

    def test_unapproved_draft_cannot_upload_or_reach_buffer(self):
        with self.assertRaises(BufferError): self.stage()
        self.assertEqual(self.uploads,[])
        self.assertEqual(self.api.creates,[])

    def test_instagram_handoff_uses_exact_caption_image_and_alt(self):
        self.approve()
        before = self.queue.get(self.ig)
        result = self.stage()
        request = self.api.creates[0]
        self.assertEqual(request['text'],'Caption asli.')
        self.assertEqual(request['channel_id'],'ig-channel')
        self.assertEqual(request['assets'][0]['image']['metadata']['altText'],'Logo asli.')
        self.assertIn(hashlib.sha256(self.image.read_bytes()).hexdigest(),request['assets'][0]['image']['url'])
        self.assertEqual(request['metadata'],{'instagram':{'type':'post','shouldShareToFeed':True}})
        self.assertFalse(result['published'])
        self.assertEqual(self.queue.get(self.ig),before)
        self.assertEqual(self.queue.db.execute('SELECT status FROM buffer_exports').fetchone()[0],'draft')

    def test_threads_handoff_has_no_image_or_instagram_metadata(self):
        self.approve(self.threads)
        self.stage(self.threads)
        self.assertEqual(self.uploads,[])
        request = self.api.creates[0]
        self.assertEqual(request['assets'],[])
        self.assertIsNone(request['metadata'])
        self.assertEqual(request['text'],'Threads asli.')
        self.assertEqual(request['channel_id'],'threads-channel')

    def test_one_platform_approval_does_not_approve_other(self):
        self.approve(self.threads)
        with self.assertRaises(BufferError): self.stage(self.ig)

    def test_duplicate_handoff_retrieves_same_remote_draft(self):
        self.approve()
        first = self.stage()
        second = self.stage()
        self.assertEqual(first['post_id'],second['post_id'])
        self.assertTrue(second['already_saved'])
        self.assertEqual(len(self.api.creates),1)
        self.assertEqual(len(self.uploads),1)

    def test_remote_manual_edits_or_scheduling_do_not_create_replacement(self):
        self.approve(self.threads)
        result = self.stage(self.threads)
        self.api.posts[result['post_id']]['status'] = 'scheduled'
        with self.assertRaises(BufferUncertain): self.stage(self.threads)
        self.assertEqual(len(self.api.creates),1)

    def test_timeout_is_not_retried(self):
        self.approve(self.threads)
        def lost(**kwargs):
            self.api.creates.append(kwargs)
            raise TimeoutError('must-not-leak-private-token')
        self.api.create_draft = lost
        with self.assertRaises(BufferUncertain) as error: self.stage(self.threads)
        self.assertNotIn('token',str(error.exception))
        with self.assertRaises(BufferUncertain): self.stage(self.threads)
        self.assertEqual(len(self.api.creates),1)
        self.assertEqual(self.queue.db.execute('SELECT status FROM buffer_exports').fetchone()[0],'uncertain')

    def test_definitive_rejection_can_be_retried_explicitly(self):
        self.approve(self.threads)
        original = self.api.create_draft
        self.api.create_draft = lambda **kwargs: (_ for _ in ()).throw(BufferError('definite'))
        with self.assertRaises(BufferError): self.stage(self.threads)
        self.api.create_draft = original
        self.stage(self.threads)
        self.assertEqual(len(self.api.creates),1)

    def test_disconnected_or_wrong_account_blocks_upload(self):
        self.approve()
        self.api.disconnected = True
        with self.assertRaises(BufferError): self.stage()
        self.assertEqual(self.uploads,[])
        self.assertEqual(self.api.creates,[])

    def test_changed_text_or_image_blocks_export(self):
        self.approve()
        media = self.queue.directory/'media'/f'{hashlib.sha256(self.image.read_bytes()).hexdigest()}.jpg'
        media.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.stage()
        self.assertEqual(self.api.creates,[])

    def test_fake_approved_status_without_telegram_event_rejected(self):
        self.queue.db.execute("UPDATE drafts SET status='review_approved',reviewer='telegram:42' WHERE id=?",(self.ig,))
        self.queue.db.commit()
        with self.assertRaises(BufferError): self.stage()

    def test_other_reviewer_is_not_accepted(self):
        self.approve()
        with self.assertRaises(BufferError): stage_draft(self.queue,self.ig,'99',config=self.config,api=self.api,media=self.media)

    def test_revision_revokes_old_handoff_and_child_needs_new_review(self):
        self.approve()
        result = self.stage()
        self.decide('revisi',notes='Ganti caption.')
        child = self.queue.add('instagram',{'account':'ignidi.labs','caption':'Caption revisi.'},self.image,revision_of=self.ig)
        with self.assertRaises(BufferError): self.stage()
        with self.assertRaises(BufferError): self.stage(child)
        report = status(self.queue,self.owner,self.ig,config=self.config,api=self.api)
        self.assertIn('DICABUT',report)
        self.assertEqual(self.api.posts[result['post_id']]['status'],'draft')
        self.approve(child)
        revised = self.stage(child)
        self.assertNotEqual(revised['post_id'],result['post_id'])

    def test_revoke_during_media_upload_blocks_buffer_request(self):
        self.approve()
        def revoked(queue,payload,config):
            self.decide('revisi',notes='Belum cocok.')
            return self.media(queue,payload,config)
        with self.assertRaises(BufferError): self.stage(media=revoked)
        self.assertEqual(self.api.creates,[])

    def test_unexpected_remote_scheduled_status_stops_and_blocks_retry(self):
        self.approve(self.threads)
        original = self.api.create_draft
        def unexpected(**kwargs):
            post = original(**kwargs)
            return {**post,'status':'scheduled','dueAt':'2026-12-01T00:00:00Z'}
        self.api.create_draft = unexpected
        with self.assertRaises(BufferUncertain): self.stage(self.threads)
        with self.assertRaises(BufferUncertain): self.stage(self.threads)
        self.assertEqual(len(self.api.creates),1)
        from buffer_drafts import verify_post
        incomplete = {'id':'remote','channelId':'threads-channel','text':'Threads asli.','status':'draft','assets':[]}
        with self.assertRaises(BufferUncertain): verify_post(incomplete,'threads-channel','Threads asli.',None)

    def test_reconciliation_is_read_only_and_requires_exact_post(self):
        self.approve(self.threads)
        original = self.api.create_draft
        def lost_after_create(**kwargs):
            original(**kwargs)
            raise TimeoutError()
        self.api.create_draft = lost_after_create
        with self.assertRaises(BufferUncertain): self.stage(self.threads)
        post_id = next(iter(self.api.posts))
        self.api.posts[post_id]['text'] = 'Wrong'
        with self.assertRaises(BufferUncertain): reconcile(self.queue,self.threads,post_id,self.owner,config=self.config,api=self.api)
        self.api.posts[post_id]['text'] = 'Threads asli.'
        result = reconcile(self.queue,self.threads,post_id,self.owner,config=self.config,api=self.api)
        self.assertFalse(result['published'])
        self.assertEqual(len(self.api.creates),1)
        self.assertEqual(self.queue.db.execute('SELECT status FROM buffer_exports').fetchone()[0],'draft')

    def test_channel_identity_service_org_and_connection_must_match(self):
        channel = self.api.channel('ig-channel')
        self.assertTrue(valid_channel(channel,'instagram','org'))
        for field,value in [('name','rama'),('service','threads'),('organizationId','other'),('isLocked',True),('isDisconnected',True)]:
            self.assertFalse(valid_channel({**channel,field:value},'instagram','org'))

    def test_config_requires_draft_mode_and_private_file(self):
        path = self.queue.directory/'buffer-config.json'
        self.assertIsNone(load_config(self.queue,required=False))
        save_config(path,self.config)
        self.assertEqual(load_config(self.queue),self.config)
        save_config(path,{**self.config,'mode':'publish'})
        with self.assertRaises(BufferError): load_config(self.queue)
        save_config(path,[])
        with self.assertRaises(BufferError): load_config(self.queue)
        save_config(path,self.config)
        if os.name != 'nt':
            os.chmod(path,0o644)
            with self.assertRaises(BufferError): load_config(self.queue)

    def test_cloudinary_caches_and_checks_exact_media(self):
        ensure_tables(self.queue)
        payload = self.queue.verify_content(self.queue.get(self.ig))
        uploads,checks = [],[]
        def upload(data,digest,config):
            uploads.append(data)
            return f'https://res.cloudinary.com/testcloud/image/upload/v1/ignidi-labs/{digest}.jpg'
        def verify(url,digest): checks.append((url,digest))
        first = approved_image_url(self.queue,payload,self.config,upload=upload,verify=verify)
        second = approved_image_url(self.queue,payload,self.config,upload=upload,verify=verify)
        self.assertEqual(first,second)
        self.assertEqual(uploads,[self.image.read_bytes()])
        self.assertEqual(len(checks),2)

    def test_cloudinary_rejects_wrong_hosts_expiring_and_transformed_urls(self):
        digest = 'a'*64
        valid = f'https://res.cloudinary.com/testcloud/image/upload/v1/ignidi-labs/{digest}.jpg'
        self.assertEqual(validate_url(valid,'testcloud',digest),valid)
        for url in (valid.replace('https:','http:'),valid+'?expires=tomorrow',valid.replace('res.cloudinary.com','localhost'),valid.replace('/testcloud/','/other/'),valid.replace(digest,'b'*64)):
            with self.assertRaises(BufferError): validate_url(url,'testcloud',digest)

    def test_failed_media_verification_never_reaches_buffer(self):
        self.approve()
        def changed(*args): raise BufferError('Gambar berbeda')
        with self.assertRaises(BufferError): self.stage(media=changed)
        self.assertEqual(self.api.creates,[])


class BufferTransportTests(unittest.TestCase):
    def make(self,data):
        api = BufferAPI('never-log-this-key')
        calls = []
        class Opener:
            def open(self,request,timeout):
                calls.append(request)
                return io.BytesIO(json.dumps(data).encode())
        api.opener = Opener()
        return api,calls

    def test_mutation_is_constant_draft_only_and_text_uses_variables(self):
        post = {'id':'post','status':'draft','dueAt':None,'assets':[]}
        api,calls = self.make({'data':{'createPost':{'__typename':'PostActionSuccess','post':post}}})
        malicious = 'text" }) { publishPostNow(input:{id:"x"}) }'
        api.create_draft(text=malicious,channel_id='threads',assets=[],metadata=None)
        body = json.loads(calls[0].data)
        self.assertEqual(body['query'],CREATE_DRAFT)
        self.assertIn('saveToDraft: true',body['query'])
        self.assertNotIn('publishPostNow',body['query'])
        self.assertNotIn('dueAt:',body['query'])
        self.assertEqual(body['variables']['text'],malicious)
        self.assertNotIn('mode',body['variables'])
        self.assertNotIn('saveToDraft',body['variables'])
        self.assertEqual(calls[0].full_url,'https://api.buffer.com')

    def test_graphql_partial_errors_are_uncertain(self):
        api,_ = self.make({'data':{'createPost':{'post':{'id':'post'}}},'errors':[{'message':'secret'}]})
        with self.assertRaises(BufferUncertain) as error: api.create_draft(text='x',channel_id='y',assets=[],metadata=None)
        self.assertNotIn('secret',str(error.exception))

    def test_unknown_union_error_is_uncertain_but_invalid_input_is_definite(self):
        for kind,error_class in [('UnexpectedError',BufferUncertain),('InvalidInputError',BufferError)]:
            api,_ = self.make({'data':{'createPost':{'__typename':kind,'message':'sensitive'}}})
            with self.assertRaises(error_class) as error: api.create_draft(text='x',channel_id='y',assets=[],metadata=None)
            self.assertNotIn('sensitive',str(error.exception))
            if kind == 'InvalidInputError': self.assertNotIsInstance(error.exception,BufferUncertain)

    def test_http_error_never_leaks_token(self):
        api = BufferAPI('private-key')
        class Opener:
            def open(self,*args,**kwargs):
                raise urllib.error.HTTPError('https://api.buffer.com?private-key',401,'private-key',{},None)
        api.opener = Opener()
        with self.assertRaises(BufferError) as error: api.organizations()
        self.assertNotIn('private-key',str(error.exception))

    def test_cloudinary_upload_is_hash_named_signed_and_never_overwrites(self):
        digest = 'a'*64
        reply = {'public_id':'ignidi-labs/'+digest,'resource_type':'image',
                 'secure_url':f'https://res.cloudinary.com/testcloud/image/upload/v1/ignidi-labs/{digest}.jpg'}
        requests = []
        class Opener:
            def open(self,request,timeout):
                requests.append(request)
                return io.BytesIO(json.dumps(reply).encode())
        with patch('buffer_media.urllib.request.build_opener',return_value=Opener()):
            url = upload_jpeg(b'\xff\xd8\xfforiginal',digest,{'cloud_name':'testcloud','api_key':'key','api_secret':'secret'})
        self.assertIn(digest,url)
        self.assertIn(b'name="overwrite"\r\n\r\nfalse',requests[0].data)
        self.assertIn(b'name="public_id"\r\n\r\nignidi-labs/'+digest.encode(),requests[0].data)
        self.assertNotIn(b'\r\nsecret\r\n',requests[0].data)
        self.assertTrue(requests[0].full_url.startswith('https://api.cloudinary.com/v1_1/testcloud/image/upload'))


if __name__ == '__main__': unittest.main()
