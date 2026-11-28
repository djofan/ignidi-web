"""Install/update only Ignidi's managed Hermes daily review job, using the official CLI."""
import argparse
from contextlib import contextmanager
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys

from buffer_drafts import load_config as load_buffer_config, BufferError
from content_queue import Queue
from daily_content import DailyContent
from send_review import load_config as load_telegram_config

NAME = 'ignidi-daily-review'
MARKER = '[IGNIDI_DAILY_REVIEW_V1]'
STUDIO = Path(__file__).resolve().parent


def read_jobs(hermes_home):
    path = Path(hermes_home)/'cron/jobs.json'
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    jobs = data.get('jobs') if isinstance(data, dict) else data
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise ValueError('Format jobs Hermes tidak dikenali. Tidak ada job yang diubah.')
    return jobs


def managed_job(jobs):
    matches = [job for job in jobs if str(job.get('name') or '').casefold() == NAME]
    if len(matches) > 1:
        raise ValueError('Ada lebih dari satu ignidi-daily-review. Periksa /cron list; jangan membuat duplikat.')
    if matches and (not isinstance(matches[0].get('prompt'), str)
                    or MARKER not in matches[0]['prompt'] or not matches[0].get('id')):
        raise ValueError('Nama job sudah digunakan tanpa penanda pemasang. Tidak ditimpa otomatis.')
    return matches[0] if matches else None


def job_prompt(state, hermes_home):
    # Prompt is passed as a single subprocess argument, never interpolated into a shell.
    settings = json.dumps({'studio':str(STUDIO), 'state':str(state),
                           'env_file':str(hermes_home/'.env')}, ensure_ascii=False)
    return (f'{MARKER}\nKonfigurasi path lokal: {settings}\n'
            'Kerjakan produksi harian dengan membaca daily-review-prompt.md di studio tersebut. '
            'Gunakan --state dan --env-file dari konfigurasi path pada setiap command daily_content.py '
            '(opsi global sebelum subcommand). Jangan mencetak isi file credential. '
            'Buat satu gambar+caption Instagram dan satu tulisan Threads, kirim untuk review Telegram. '
            'Mulai dengan plan, gunakan batch harian yang sudah ada bila tersedia. '
            'Jangan menyetujui konten sendiri atau mengakses Buffer/Meta dari tugas ini. '
            'Setelah /setuju pemilik, plugin hanya menyimpan ke Drafts Buffer. '
            'Tidak boleh ada penjadwalan atau posting otomatis. Ikuti seluruh langkah dan batas pada file prompt.')


def cli_args(binary, job, hour, minute, state, hermes_home, chat_id):
    expression = f'{minute} {hour} * * *'
    prompt = job_prompt(state, hermes_home)
    common = ['--name', NAME, '--timezone', 'Asia/Jakarta',
              '--workdir', str(STUDIO), '--deliver', 'telegram:'+str(chat_id)]
    if job:
        return [binary, 'cron', 'edit', str(job['id']), '--schedule', expression, '--prompt', prompt, *common]
    return [binary, 'cron', 'create', expression, prompt, *common]


@contextmanager
def install_lock(state):
    # This installer is VPS/Linux only. Lock prevents two installers creating duplicate jobs.
    import fcntl
    with (state/'daily-install.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Pemasang harian lain sedang berjalan; tunggu hasilnya.') from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def install(hour, minute, state, hermes_home, binary, chat_id):
    with install_lock(state):
        job = managed_job(read_jobs(hermes_home))
        action = 'edit' if job else 'create'
        help_result = subprocess.run([binary, 'cron', action, '--help'], capture_output=True, text=True, timeout=30)
        if help_result.returncode or any(flag not in help_result.stdout for flag in ('--timezone','--workdir','--deliver')):
            raise ValueError('CLI Hermes ini belum mendukung opsi jadwal yang diperlukan. Periksa hermes --version dan cron --help; jadwal belum diubah.')
        result = subprocess.run(cli_args(binary, job, hour, minute, state, hermes_home, chat_id),
                                capture_output=True, text=True, timeout=60)
        # Never echo arbitrary CLI stderr/stdout, which can include unrelated environment values.
        if result.returncode:
            raise ValueError('CLI Hermes gagal menyimpan job. Periksa hermes cron list/status; jangan membuat jadwal kedua secara manual.')
        saved = managed_job(read_jobs(hermes_home))
        expected = job_prompt(state, hermes_home)
        schedule = saved.get('schedule') if saved else None
        schedule = schedule.get('value') if isinstance(schedule, dict) else schedule
        delivery = saved.get('deliver') if saved else None
        delivery = [delivery] if isinstance(delivery, str) else delivery
        if (not saved or saved.get('prompt') != expected or saved.get('timezone') != 'Asia/Jakarta'
                or schedule != f'{minute} {hour} * * *' or saved.get('workdir') != str(STUDIO)
                or delivery != ['telegram:'+str(chat_id)]
                or (saved.get('enabled', True) and not saved.get('next_run_at'))):
            if saved:
                subprocess.run([binary,'cron','pause',str(saved['id'])], capture_output=True, timeout=30)
            raise ValueError('Penyimpanan job belum terverifikasi. Periksa hermes cron list; jangan ulang pembuatan secara buta.')
        return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--time', default='09:00', help='HH:MM WIB; default 09:00 setiap hari.')
    parser.add_argument('--check', action='store_true', help='Periksa prasyarat tanpa membuat/mengubah jadwal.')
    args = parser.parse_args()
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', args.time):
        raise ValueError('Waktu harus HH:MM, misalnya 09:00 WIB.')
    if sys.platform != 'linux' or getpass.getuser() != 'ignidi-hermes':
        raise ValueError('Jalankan hanya sebagai user ignidi-hermes di VPS melalui Termius.')
    os.umask(0o077)
    state = Path(os.environ.get('IGNIDI_CONTENT_STATE', str(Path.home()/'.local/state/ignidi-content'))).expanduser().resolve()
    hermes_home = Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes'))).expanduser().resolve()
    binary = shutil.which('hermes')
    if not binary or not shutil.which('node'):
        raise ValueError('hermes dan node harus tersedia pada PATH user ignidi-hermes.')
    if not (STUDIO.parent.parent/'public/ignidi-labs.jpeg').is_file():
        raise ValueError('Logo asli tidak ditemukan pada checkout.')
    # All checks are local; no content is sent and no Buffer request is made during setup.
    telegram = load_telegram_config(hermes_home/'.env')
    queue = Queue(state)
    try:
        buffer = load_buffer_config(queue)
        DailyContent(queue)
    finally:
        queue.db.close()
    if not buffer or buffer.get('mode') != 'draft_only' or buffer.get('auto_stage') is not True:
        raise ValueError('Integrasi Buffer harus draft_only dan auto_stage=true sebelum memasang jadwal.')
    node_check = subprocess.run(['node','--input-type=module','-e',"await import('sharp');"],
                                cwd=STUDIO, capture_output=True, timeout=30)
    if node_check.returncode:
        raise ValueError('Renderer belum siap. Jalankan npm install --omit=dev di folder studio.')
    env = {**os.environ, 'XDG_RUNTIME_DIR':f'/run/user/{os.getuid()}'}
    env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path='+env['XDG_RUNTIME_DIR']+'/bus'
    service = subprocess.run(['systemctl','--user','is-active','--quiet','hermes-gateway.service'], env=env,
                             capture_output=True, timeout=15)
    if service.returncode:
        raise ValueError('Gateway Hermes user ini belum aktif. Periksa user service; pemasang tidak me-restart layanan.')
    if args.check:
        existing = managed_job(read_jobs(hermes_home))
        print(json.dumps({'ready':True, 'job_id':existing.get('id') if existing else None,
                          'schedule_changed':False, 'published':False}))
        return
    hour, minute = map(int, args.time.split(':'))
    saved = install(hour, minute, state, hermes_home, binary, telegram['chat_id'])
    print(json.dumps({'job_id':saved['id'], 'name':NAME, 'time_wib':args.time,
                      'timezone':saved['timezone'], 'enabled':saved.get('enabled', True),
                      'next_run_at':saved.get('next_run_at'), 'mode':'review_then_buffer_drafts',
                      'published':False}, ensure_ascii=False, indent=2))
    print('Job disimpan. Jalankan hermes cron list dan status untuk memeriksa waktu berikutnya.')
    print('Tes sekarang: hermes cron run '+saved['id'])
    print('Pengulangan pemasang memperbarui job yang sama; job paused tidak diaktifkan ulang otomatis.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, BufferError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, sqlite3.Error):
        print('Pemasangan belum terverifikasi. Periksa path/izin dan hermes cron list/status; jangan reset job atau antrean.', file=sys.stderr)
        sys.exit(1)
