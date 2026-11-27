"""Exercise real renderer + revision CLI + sender, with no Telegram/Meta network calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from content_queue import Queue
from review_workflow import Reviews
from send_review import send_reviews


class RevisionRoundtripTests(unittest.TestCase):
    def test_instagram_revision_renders_and_returns_as_unapproved_review(self):
        studio = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            state = work/'state'
            env = {**os.environ, 'IGNIDI_CONTENT_STATE':str(state),
                   'IGNIDI_LOGO_PATH':str(studio.parents[1]/'public/ignidi-labs.jpeg')}

            def cli(*args):
                result = subprocess.run(args, cwd=studio, env=env, check=True,
                                        capture_output=True, text=True, encoding='utf-8', timeout=60)
                return result.stdout

            bundle = json.loads((studio/'samples/lead.json').read_text(encoding='utf-8-sig'))
            original_json, original_image = work/'original.json', work/'original.jpg'
            original_json.write_text(json.dumps(bundle),encoding='utf-8')
            cli('node',str(studio/'render.mjs'),str(original_json),str(original_image))
            queue = Queue(state)
            try:
                original_id = queue.add('instagram',bundle['instagram'],original_image)
                threads_id = queue.add('threads',bundle['threads'])
                untouched_digest = queue.get(threads_id)['digest']
                owner = '42'
                source = SimpleNamespace(user_id=owner,chat_id=owner,chat_type='dm')
                calls = []

                def telegram_stub(method, fields, file):
                    calls.append((method,fields,file))
                    return 100 + len(calls)

                config = {'chat_id':owner, 'token':'123:' + 'x'*30}
                send_reviews(queue,[original_id],config,send=True,transport=telegram_stub)
                reviews = Reviews(queue,owner)
                raw = f'{original_id} {queue.get(original_id)["digest"]} Ringkas headline dan caption; pertahankan logo dan warna Ignidi.'
                reviews.decide('revisi',raw,platform='telegram',source=source)
                request = json.loads(cli(sys.executable,str(studio/'revision.py'),'show',original_id))
                self.assertIn('Ringkas headline',request['request']['notes'])
                self.assertFalse(request['published'])

                # Deterministic sample edit stands in for model output; live Hermes is not mocked as tested.
                bundle['instagram'].update({
                    'headline':'Lead rapi. Tim siap.',
                    'caption':'Lead masuk? Catat kontak, tentukan penanggung jawab, dan siapkan pengingat. Bagian mana yang ingin kamu rapikan?',
                    'alt_text':'Poster Ignidi Labs gelap dan oranye dengan judul Lead rapi. Tim siap.',
                })
                revised_json, revised_image = work/'revised.json', work/'revised.jpg'
                revised_json.write_text(json.dumps(bundle),encoding='utf-8')
                cli('node',str(studio/'render.mjs'),str(revised_json),str(revised_image))
                result = json.loads(cli(sys.executable,str(studio/'revision.py'),'add',original_id,str(revised_json),'--image',str(revised_image)))
                child_id = result['id']
                self.assertNotEqual(original_id,child_id)
                self.assertFalse(result['published'])
                child = queue.get(child_id)
                payload = queue.verify_content(child)
                self.assertEqual(child['status'],'draft')
                self.assertIsNone(child['signature'])
                self.assertNotEqual(child['digest'],queue.get(original_id)['digest'])
                self.assertEqual(queue.get(original_id)['status'],'superseded')
                self.assertEqual(payload['revision'],{'number':2,'parent_id':original_id})
                self.assertNotEqual(original_image.read_bytes(),revised_image.read_bytes())

                send_reviews(queue,[child_id],config,send=True,transport=telegram_stub)
                self.assertEqual([call[0] for call in calls[3:]],['sendPhoto','sendMessage','sendDocument'])
                self.assertEqual(calls[3][2][1],revised_image.read_bytes())
                self.assertEqual(calls[5][2][1],revised_image.read_bytes())
                self.assertIn(child_id,calls[4][1]['text'])
                self.assertIn(child['digest'],calls[4][1]['text'])
                self.assertIn(bundle['instagram']['caption'],calls[4][1]['text'])
                self.assertIn('/revisi '+child_id,calls[4][1]['text'])
                self.assertEqual(payload['image_sha256'],hashlib.sha256(revised_image.read_bytes()).hexdigest())
                self.assertEqual(queue.get(child_id)['status'],'draft')
                with self.assertRaises(ValueError): queue.approved(child_id,'x'*64)
                self.assertEqual(queue.get(threads_id)['status'],'draft')
                self.assertEqual(queue.get(threads_id)['digest'],untouched_digest)
                send_reviews(queue,[child_id],config,send=True,transport=telegram_stub)
                self.assertEqual(len(calls),6)
            finally:
                queue.db.close()


if __name__ == '__main__': unittest.main()
