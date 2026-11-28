from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import setup_daily as setup


class SetupDailyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)/'state'
        self.state.mkdir()
        self.hermes = Path(self.temp.name)/'hermes'
        (self.hermes/'cron').mkdir(parents=True)
        self.jobs = self.hermes/'cron/jobs.json'
        self.calls = []
        self.lock = patch.object(setup, 'install_lock', return_value=nullcontext())
        self.lock.start()

    def tearDown(self):
        self.lock.stop()
        self.temp.cleanup()

    def read(self):
        return setup.read_jobs(self.hermes)

    def save(self, jobs):
        self.jobs.write_text(json.dumps({'jobs':jobs}), encoding='utf-8')

    def run_cli(self, args, **kwargs):
        self.calls.append(args)
        if args[-1] == '--help':
            return subprocess.CompletedProcess(args, 0, '--timezone --workdir --deliver', '')
        jobs = self.read()
        action = args[2]
        if action == 'create':
            job = {'id':'managed001', 'enabled':True}
            jobs.append(job)
            expression, prompt = args[3:5]
        elif action == 'pause':
            for job in jobs:
                if job['id'] == args[3]:
                    job['enabled'] = False
            self.save(jobs)
            return subprocess.CompletedProcess(args, 0, '', '')
        else:
            job = next(job for job in jobs if job['id'] == args[3])
            expression = args[args.index('--schedule')+1]
            prompt = args[args.index('--prompt')+1]
        job.update(name=args[args.index('--name')+1], prompt=prompt,
                   schedule={'kind':'cron','value':expression}, timezone='Asia/Jakarta',
                   workdir=str(setup.STUDIO), deliver=['telegram:42'], next_run_at='2026-11-29T02:00:00+00:00')
        self.save(jobs)
        return subprocess.CompletedProcess(args, 0, 'saved', '')

    def install(self):
        return setup.install(9, 0, self.state, self.hermes, 'hermes', '42')

    def test_install_uses_official_cli_and_daily_jakarta_schedule(self):
        with patch.object(setup.subprocess,'run',side_effect=self.run_cli):
            saved = self.install()
        self.assertEqual(saved['timezone'], 'Asia/Jakarta')
        command = self.calls[-1]
        self.assertEqual(command[:4], ['hermes','cron','create','0 9 * * *'])
        self.assertIn('--deliver', command)
        self.assertEqual(command[-1], 'telegram:42')
        self.assertIn(setup.MARKER, saved['prompt'])
        self.assertIn('daily-review-prompt.md', saved['prompt'])

    def test_repeat_updates_same_job_and_preserves_unrelated_jobs(self):
        unrelated = {'id':'other001','name':'other-task','prompt':'leave me alone', 'enabled':True}
        self.save([unrelated])
        with patch.object(setup.subprocess,'run',side_effect=self.run_cli):
            first = self.install()
            second = self.install()
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(len(self.read()), 2)
        self.assertEqual(self.read()[0], unrelated)
        self.assertEqual(sum(command[2] == 'create' and command[-1] != '--help' for command in self.calls), 1)

    def test_paused_job_is_not_implicitly_resumed(self):
        with patch.object(setup.subprocess,'run',side_effect=self.run_cli):
            self.install()
            job = self.read()[0]
            job['enabled'] = False
            self.save([job])
            saved = self.install()
        self.assertFalse(saved['enabled'])
        self.assertFalse(any(command[2] == 'resume' for command in self.calls))

    def test_unknown_same_name_or_duplicate_refused_before_mutation(self):
        for jobs in ([{'id':'unknown','name':setup.NAME,'prompt':'unmanaged'}],
                     [{'id':str(i),'name':setup.NAME,'prompt':setup.MARKER} for i in range(2)]):
            self.save(jobs)
            with patch.object(setup.subprocess,'run') as call, self.assertRaises(ValueError):
                self.install()
            call.assert_not_called()
            self.assertEqual(self.read(), jobs)

    def test_unsupported_cli_refused_without_mutation(self):
        with patch.object(setup.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'--deliver','')) as call:
            with self.assertRaisesRegex(ValueError, 'belum mendukung'):
                self.install()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(self.read(), [])

    def test_cli_failure_does_not_retry_or_leak_cli_output(self):
        def failed(args, **kwargs):
            if args[-1] == '--help':
                return self.run_cli(args, **kwargs)
            return subprocess.CompletedProcess(args, 1, 'secret in stdout', 'secret in stderr')
        with patch.object(setup.subprocess,'run',side_effect=failed) as call:
            with self.assertRaises(ValueError) as caught:
                self.install()
        self.assertNotIn('secret', str(caught.exception))
        self.assertEqual(call.call_count, 2)

    def test_wrong_saved_schedule_paused_and_reported(self):
        def wrong(args, **kwargs):
            result = self.run_cli(args, **kwargs)
            if args[2] == 'create' and args[-1] != '--help':
                jobs = self.read()
                jobs[-1]['schedule']['value'] = '0 9 * * 1-5'
                self.save(jobs)
            return result
        with patch.object(setup.subprocess,'run',side_effect=wrong):
            with self.assertRaisesRegex(ValueError, 'belum terverifikasi'):
                self.install()
        self.assertFalse(self.read()[0]['enabled'])

    def test_corrupt_store_not_rewritten(self):
        self.jobs.write_text('{"jobs": "bad"}', encoding='utf-8')
        with patch.object(setup.subprocess,'run') as call, self.assertRaises(ValueError):
            self.install()
        call.assert_not_called()
        self.assertEqual(self.jobs.read_text(), '{"jobs": "bad"}')


if __name__ == '__main__':
    unittest.main()
