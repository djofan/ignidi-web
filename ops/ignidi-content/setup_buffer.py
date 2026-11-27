"""Interactive VPS setup: read-only Buffer checks, private config, no social posts or media uploads."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import sys

from buffer_drafts import BufferAPI, BufferError, config_path, valid_channel
from content_queue import Queue


def choose(items,label):
    if not items:
        raise BufferError(f'{label} belum ditemukan. Sambungkan akun sosial di Buffer terlebih dahulu.')
    if len(items) == 1:
        return items[0]
    for index,item in enumerate(items,1):
        print(f'{index}. {item.get("name") or item["id"]} ({item["id"]})')
    answer = input(f'Pilih {label} [1-{len(items)}]: ').strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(items):
        raise BufferError('Pilihan tidak valid; konfigurasi tidak diubah.')
    return items[int(answer)-1]


def save_config(path,config):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temporary = path.with_name('.buffer-config-'+secrets.token_hex(8))
    try:
        descriptor = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'w',encoding='utf-8') as file:
            json.dump(config,file,ensure_ascii=False,indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,path)
        os.chmod(path,0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',default=os.environ.get('IGNIDI_CONTENT_STATE',str(Path.home()/'.local/state/ignidi-content')))
    args = parser.parse_args()
    if os.name != 'nt' and getpass.getuser() != 'ignidi-hermes':
        raise BufferError('Jalankan sebagai ignidi-hermes, bukan root/ubuntu/Rama.')
    if not sys.stdin.isatty():
        raise BufferError('Jalankan secara interaktif di Termius agar secret tidak masuk argumen atau riwayat shell.')
    print('Setup Buffer DRAFT ONLY. Tidak membuat posting, jadwal, atau upload gambar saat setup.')
    api_key = getpass.getpass('API key Buffer (input tersembunyi): ').strip()
    if not api_key:
        raise BufferError('API key belum diisi.')
    api = BufferAPI(api_key)
    organization = choose(api.organizations(),'organisasi Buffer')
    channels = api.channels(organization['id'])
    selected = {}
    for service in ('instagram','threads'):
        matches = [item for item in channels if valid_channel(item,service,organization['id'])]
        channel = choose(matches,service+' @ignidi.labs')
        selected[service] = channel['id']
        print(f'{service}: @ignidi.labs terverifikasi (channel {channel["id"]}).')
    print('Cloudinary: buka Product Environment > API Keys; jangan tempel secret ke Telegram/chat.')
    cloud = input('Cloud name Cloudinary: ').strip()
    cloud_key = getpass.getpass('API key Cloudinary (input tersembunyi): ').strip()
    cloud_secret = getpass.getpass('API secret Cloudinary (input tersembunyi): ').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',cloud) or not cloud_key or not cloud_secret:
        raise BufferError('Konfigurasi Cloudinary belum lengkap; tidak disimpan.')
    config = {'mode':'draft_only','auto_stage':True,'api_key':api_key,
              'organization_id':organization['id'],'channels':selected,
              'cloudinary':{'cloud_name':cloud,'api_key':cloud_key,'api_secret':cloud_secret}}
    queue = Queue(args.state)
    try:
        save_config(config_path(queue),config)
    finally:
        queue.db.close()
    print('Konfigurasi tersimpan privat (600). Cek /bufferstatus di Telegram.')
    print('Cloudinary akan diverifikasi saat handoff JPEG pertama; belum ada upload atau createPost pada setup ini.')
    print('/setuju baru akan menyalin versi itu ke Drafts Buffer. Untuk persetujuan lama: /bufferdraft ID.')
    print('Tidak ada jadwal tayang atau fitur publish yang diaktifkan.')


if __name__ == '__main__':
    try:
        main()
    except (BufferError,ValueError) as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
    except (OSError,KeyError,TypeError):
        print('Setup belum selesai. Periksa koneksi dan respons akun Buffer; jangan membagikan secret.',file=sys.stderr)
        sys.exit(1)
