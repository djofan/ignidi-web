import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from content_queue import Queue
from buffer_drafts import BufferError, load_config
from setup_buffer import prompt_cloudinary, save_config, update_cloudinary, main


class CloudinaryRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.queue = Queue(self.temp.name)
        self.config = {'mode':'draft_only','auto_stage':True,'api_key':'buffer-private-key',
            'organization_id':'organization','channels':{'instagram':'ig-channel','threads':'threads-channel'},
            'cloudinary':{'cloud_name':'wrong-name','api_key':'cloud-private-key','api_secret':'cloud-private-secret'}}
        save_config(self.queue.directory/'buffer-config.json',self.config)
        self.id = self.queue.add('threads',{'account':'ignidi.labs','text':'Draf tetap utuh.'})

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def test_only_cloudinary_changes_and_draft_stays_identical(self):
        before = self.queue.get(self.id)
        media = {**self.config['cloudinary'],'cloud_name':'correctcloud'}
        update_cloudinary(self.queue,media)
        updated = load_config(self.queue)
        self.assertEqual(updated['cloudinary'],media)
        self.assertEqual({key:value for key,value in updated.items() if key != 'cloudinary'},
                         {key:value for key,value in self.config.items() if key != 'cloudinary'})
        self.assertEqual(self.queue.get(self.id),before)

    def test_prompt_keeps_existing_pair_without_printing_it(self):
        output = io.StringIO()
        with patch('builtins.input',return_value='correctcloud'),patch('setup_buffer.getpass.getpass',side_effect=['','']),patch('sys.stdout',output):
            media = prompt_cloudinary(self.config['cloudinary'])
        self.assertEqual(media,{**self.config['cloudinary'],'cloud_name':'correctcloud'})
        self.assertNotIn('cloud-private-key',output.getvalue())
        self.assertNotIn('cloud-private-secret',output.getvalue())

    def test_url_email_and_empty_cloud_are_rejected_without_saving(self):
        path = self.queue.directory/'buffer-config.json'
        before = path.read_bytes()
        for cloud in ('https://res.cloudinary.com/name','someone@example.com',''):
            with self.subTest(cloud=cloud):
                with self.assertRaises(BufferError):
                    update_cloudinary(self.queue,{**self.config['cloudinary'],'cloud_name':cloud})
        self.assertEqual(path.read_bytes(),before)

    def test_rotation_replaces_only_cloudinary_pair(self):
        output = io.StringIO()
        with patch('builtins.input',return_value='correctcloud'),patch('setup_buffer.getpass.getpass',side_effect=['new-cloud-key','new-cloud-secret']),patch('sys.stdout',output):
            media = prompt_cloudinary(self.config['cloudinary'])
        update_cloudinary(self.queue,media)
        self.assertEqual(load_config(self.queue)['cloudinary'],{'cloud_name':'correctcloud','api_key':'new-cloud-key','api_secret':'new-cloud-secret'})
        self.assertEqual(load_config(self.queue)['api_key'],'buffer-private-key')

    def test_cloudinary_only_cli_never_calls_buffer_or_echoes_secret(self):
        output = io.StringIO()
        with patch('sys.argv',['setup_buffer.py','--state',self.temp.name,'--cloudinary-only']),patch('sys.stdin.isatty',return_value=True),patch('setup_buffer.getpass.getuser',return_value='ignidi-hermes'),patch('builtins.input',return_value='correctcloud'),patch('setup_buffer.getpass.getpass',side_effect=['','']),patch('setup_buffer.BufferAPI',side_effect=AssertionError('Buffer API must not be used')),patch('sys.stdout',output):
            main()
        self.assertEqual(load_config(self.queue)['cloudinary']['cloud_name'],'correctcloud')
        self.assertIn('Tidak ada upload',output.getvalue())
        for secret in ('buffer-private-key','cloud-private-key','cloud-private-secret'):
            self.assertNotIn(secret,output.getvalue())


if __name__ == '__main__': unittest.main()
