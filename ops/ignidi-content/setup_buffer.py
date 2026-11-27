"""Interactive VPS setup: read-only Buffer checks, private config, no social posts or media uploads."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import sys

from buffer_drafts import BufferAPI, BufferError, config_path, valid_channel, load_config
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


def prompt_cloudinary(existing=None):
    existing = existing or {}
    print('Cloudinary: salin nilai Cloud name dari Dashboard, bukan nama akun, key name, atau URL.')
    if existing:
        print('Jika memilih product environment lain, isi juga API key dan API secret dari environment yang sama.')
    cloud = input('Cloud name dari Dashboard (wajib diisi): ').strip()
    suffix = '; Enter untuk tetap memakai nilai tersimpan' if existing else ''
    cloud_key = getpass.getpass(f'API key Cloudinary (input tersembunyi{suffix}): ').strip()
    cloud_secret = getpass.getpass(f'API secret Cloudinary (input tersembunyi{suffix}): ').strip()
    media = {'cloud_name':cloud,
             'api_key':cloud_key or existing.get('api_key',''),
             'api_secret':cloud_secret or existing.get('api_secret','')}
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',cloud) or not media['api_key'] or not media['api_secret']:
        raise BufferError('Cloudinary belum lengkap. Masukkan cloud name saja, tanpa URL/email; konfigurasi belum diubah.')
    return media


def update_cloudinary(queue,media):
    if (not isinstance(media,dict) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',media.get('cloud_name',''))
            or not all(isinstance(media.get(key),str) and media[key].strip() for key in ('api_key','api_secret'))):
        raise BufferError('Konfigurasi Cloudinary tidak valid; konfigurasi lama dipertahankan.')
    config = load_config(queue)
    config['cloudinary'] = dict(media)
    save_config(config_path(queue),config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',default=os.environ.get('IGNIDI_CONTENT_STATE',str(Path.home()/'.local/state/ignidi-content')))
    parser.add_argument('--cloudinary-only',action='store_true',help='Perbarui hanya Cloudinary; tidak meminta key Buffer atau mengubah draf/persetujuan.')
    args = parser.parse_args()
    if os.name != 'nt' and getpass.getuser() != 'ignidi-hermes':
        raise BufferError('Jalankan sebagai ignidi-hermes, bukan root/ubuntu/Rama.')
    if not sys.stdin.isatty():
        raise BufferError('Jalankan secara interaktif di Termius agar secret tidak masuk argumen atau riwayat shell.')
    if args.cloudinary_only:
        queue = Queue(args.state)
        try:
            config = load_config(queue)
            media = prompt_cloudinary(config.get('cloudinary'))
            update_cloudinary(queue,media)
        finally:
            queue.db.close()
        print('Konfigurasi Cloudinary diperbarui privat (600). Tidak mengubah API key/channel Buffer, draf, atau persetujuan.')
        print('Tidak ada upload, request Buffer, jadwal, atau posting. Cloudinary diverifikasi saat handoff JPEG berikutnya.')
        print('Uji hanya Instagram melalui /bufferdraft ID yang failed. Tidak perlu restart gateway atau mengirim ulang Threads.')
        return
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
    media = prompt_cloudinary()
    config = {'mode':'draft_only','auto_stage':True,'api_key':api_key,
              'organization_id':organization['id'],'channels':selected,
              'cloudinary':media}
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
