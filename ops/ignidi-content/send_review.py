"""Send queued drafts to the owner's Telegram DM. Never publishes to Meta or polls updates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

try:
    from .content_queue import Queue
except ImportError:
    from content_queue import Queue

CONFIG_KEYS = {'TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_USERS', 'TELEGRAM_HOME_CHANNEL', 'IGNIDI_REVIEW_CHAT_ID'}
STATUS_LABELS = {'draft':'MENUNGGU REVIEW', 'review_approved':'DISETUJUI PEMILIK',
                 'needs_revision':'PERLU REVISI', 'superseded':'DIGANTIKAN REVISI',
                 'rejected':'DITOLAK', 'approved':'PERSETUJUAN OPERATOR LAMA'}


def load_config(env_path):
    values = {}
    path = Path(env_path).expanduser()
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line.startswith('export '):
                line = line[7:]
            if '=' not in line or line.startswith('#'):
                continue
            key, raw = line.split('=', 1)
            key = key.strip()
            if key not in CONFIG_KEYS:
                continue
            parts = shlex.split(raw, comments=True, posix=True)
            if len(parts) == 1:
                values[key] = parts[0]
    values.update({key: os.environ[key] for key in CONFIG_KEYS if key in os.environ})
    token = values.get('TELEGRAM_BOT_TOKEN', '')
    if not re.fullmatch(r'\d+:[A-Za-z0-9_-]{20,}', token):
        raise ValueError('Belum ditemukan token bot yang valid. Periksa konfigurasi Telegram Hermes di VPS; jangan kirim token ke chat.')
    allowed = [value.strip() for value in values.get('TELEGRAM_ALLOWED_USERS', '').split(',') if value.strip()]
    if not allowed or any(not re.fullmatch(r'[1-9]\d*', value) for value in allowed):
        raise ValueError('Allowed user IDs harus berupa daftar ID numerik, tanpa wildcard atau akses terbuka.')
    chat = values.get('IGNIDI_REVIEW_CHAT_ID') or values.get('TELEGRAM_HOME_CHANNEL')
    if not chat and len(allowed) == 1:
        chat = allowed[0]
    if not chat or not re.fullmatch(r'[1-9]\d*', chat) or chat not in allowed:
        raise ValueError('Tujuan review harus DM pemilik yang ada di allowlist. Atur /sethome di DM bot, atau IGNIDI_REVIEW_CHAT_ID pada VPS.')
    return {'token': token, 'chat_id': chat}


class TelegramFailure(Exception):
    """Definitive rejection (safe to retry manually after fixing the error)."""


class DeliveryUncertain(Exception):
    """Request outcome unknown. Do not retry automatically."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Telegram:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect())

    def __call__(self, method, fields, file=None):
        if method not in {'sendMessage', 'sendPhoto', 'sendDocument'}:
            raise ValueError('Metode Telegram tidak diizinkan.')
        if file:
            boundary = 'ignidi-' + secrets.token_hex(16)
            chunks = []
            for key, value in fields.items():
                chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
            field, data, filename = file
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + data + b'\r\n')
            chunks.append(f'--{boundary}--\r\n'.encode())
            body = b''.join(chunks)
            content_type = f'multipart/form-data; boundary={boundary}'
        else:
            body = urllib.parse.urlencode(fields).encode()
            content_type = 'application/x-www-form-urlencoded'
        request = urllib.request.Request(f'https://api.telegram.org/bot{self.token}/{method}', data=body, headers={'Content-Type':content_type}, method='POST')
        try:
            with self.opener.open(request, timeout=45) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as error:
            # Never print exception strings or URLs: Telegram URLs contain bot tokens.
            if 400 <= error.code < 500 and error.code != 408:
                raise TelegramFailure(f'Telegram menolak pengiriman (HTTP {error.code}); cek koneksi bot dan chat tujuan.') from None
            raise DeliveryUncertain('Respons Telegram tidak pasti. Cek chat sebelum mencoba ulang.') from None
        except (OSError, ValueError):
            raise DeliveryUncertain('Pengiriman terputus atau respons tidak terbaca. Cek chat; tidak diulang otomatis.') from None
        if not result.get('ok'):
            raise TelegramFailure('Telegram menolak permintaan. Periksa konfigurasi bot di VPS.')
        message_id = result.get('result', {}).get('message_id')
        if not isinstance(message_id, int):
            raise DeliveryUncertain('Telegram belum memberikan ID pesan. Cek chat; tidak diulang otomatis.')
        return message_id


def review_parts(queue, row, *, preview=False):
    payload = queue.verify_content(row)
    channel = payload['channel']
    content = payload['content']
    if channel not in ('instagram', 'threads') or content.get('account') != 'ignidi.labs':
        raise ValueError('Target draft tidak cocok dengan akun Ignidi.')
    prefix = 'PREVIEW ULANG' if preview else 'REVIEW'
    label = STATUS_LABELS.get(row['status'], row['status'])
    title = f'{prefix} {channel.upper()} · @ignidi.labs\nID: {row["id"]}\nVersi SHA-256: {row["digest"]}\nStatus: {label}\nBELUM DIPUBLIKASIKAN'
    plan = payload.get('editorial_plan')
    if plan is not None:
        from datetime import date
        try:
            prepared, content_day, intended = plan['prepared_day'], plan['content_day'], plan['intended_time']
            if (date.fromisoformat(prepared).isoformat() != prepared
                    or date.fromisoformat(content_day).isoformat() != content_day
                    or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', intended)
                    or plan['timezone'] != 'Asia/Jakarta' or plan['publication'] != 'manual'):
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise ValueError('Penanda rencana konten tidak valid; pengiriman dihentikan.') from None
        title += (f'\nDisiapkan: {prepared}\nUntuk konten: {content_day} · {intended} WIB'
                  '\nAcuan posting MANUAL, bukan jadwal otomatis.')
    footer = ''
    if row['status'] == 'draft':
        footer += f'\n\nSETUJUI VERSI INI:\n/setuju {row["id"]} {row["digest"]}'
    if row['status'] in ('draft', 'review_approved', 'approved'):
        footer += (f'\n\nMINTA REVISI:\n/revisi {row["id"]} {row["digest"]} tulis catatanmu'
                   f'\n\nTOLAK:\n/tolak {row["id"]} {row["digest"]}')
    if row['status'] == 'superseded':
        footer += '\n\nVERSI LAMA: sudah digantikan; lihat ID hasil revisi melalui status di bawah.'
    footer += (f'\n\n/statuskonten {row["id"]}\n/preview {row["id"]}'
               '\n\nPerintah memerlukan plugin ignidi-review aktif. Persetujuan per kanal dan versi. Posting belum diaktifkan.')
    if channel == 'threads':
        body = content.get('text', '')
        if not isinstance(body, str) or not body.strip() or len(body.encode()) > 500:
            raise ValueError('Tulisan Threads tidak valid.')
        return [('threads-text', 'sendMessage', {'text': title + '\n\nTULISAN THREADS:\n' + body + footer}, None)]
    caption = content.get('caption', '')
    if not isinstance(caption, str) or not caption.strip() or len(caption.encode()) > 2200:
        raise ValueError('Caption Instagram tidak valid.')
    data = (queue.directory / 'media' / f'{payload["image_sha256"]}.jpg').read_bytes()
    if hashlib.sha256(data).hexdigest() != payload['image_sha256']:
        raise ValueError('Gambar berubah, review dibatalkan.')
    if len(data) > 8_000_000:
        raise ValueError('Preview terlalu besar; render JPEG di bawah 8 MB.')
    return [
        ('instagram-preview', 'sendPhoto', {'caption': title + '\n\nPreview gambar; file asli dikirim terpisah.'}, ('photo', data, 'ignidi-preview.jpg')),
        ('instagram-caption', 'sendMessage', {'text': title + '\n\nCAPTION INSTAGRAM:\n' + caption + '\n\nALT TEXT:\n' + str(content.get('alt_text', '')) + footer}, None),
        ('instagram-original', 'sendDocument', {'caption': f'File gambar asli untuk review.\nID: {row["id"]}\nSHA-256 gambar: {payload["image_sha256"]}'}, ('document', data, f'ignidi-{row["id"]}.jpg')),
    ]


def ensure_delivery_table(queue):
    queue.db.execute('''CREATE TABLE IF NOT EXISTS review_deliveries (
        draft_id TEXT, digest TEXT, chat_id TEXT, part TEXT, status TEXT NOT NULL,
        message_id INTEGER, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (draft_id,digest,chat_id,part))''')
    queue.db.execute('''CREATE TABLE IF NOT EXISTS preview_deliveries (
        request_id TEXT NOT NULL, draft_id TEXT NOT NULL, digest TEXT NOT NULL,
        chat_id TEXT NOT NULL, part TEXT NOT NULL, status TEXT NOT NULL,
        message_id INTEGER, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (request_id,part))''')
    queue.db.commit()


def validate_parts(parts):
    for _, method, fields, _ in parts:
        text = fields.get('text', fields.get('caption', ''))
        if len(text.encode('utf-16-le')) // 2 > (4096 if method == 'sendMessage' else 1024):
            raise ValueError('Pesan review melebihi batas Telegram; pendekkan draf atau alt text.')


def send_preview(queue, draft_id, config, *, transport=None):
    """One explicit re-display request. Separate audit; never resets original deliveries or decisions."""
    if not re.fullmatch(r'[a-f0-9]{16}', draft_id):
        raise ValueError('Format: /preview ID. Salin ID dari /statuskonten.')
    row = queue.get(draft_id)
    parts = review_parts(queue, row, preview=True)
    validate_parts(parts)
    ensure_delivery_table(queue)
    request_id = secrets.token_hex(16)
    with queue.db:
        queue.db.executemany('INSERT INTO preview_deliveries (request_id,draft_id,digest,chat_id,part,status) VALUES (?,?,?,?,?,?)',
                             [(request_id, draft_id, row['digest'], config['chat_id'], part, 'pending') for part, _, _, _ in parts])
    delivery = transport or Telegram(config['token'])
    results = []
    for part, method, fields, file in parts:
        with queue.db:
            queue.db.execute("UPDATE preview_deliveries SET status='sending',updated_at=CURRENT_TIMESTAMP WHERE request_id=? AND part=?", (request_id,part))
        params = {'chat_id':config['chat_id'], **fields}
        if method == 'sendMessage':
            params['link_preview_options'] = json.dumps({'is_disabled':True})
        try:
            message_id = delivery(method, params, file)
        except Exception as error:
            with queue.db:
                queue.db.execute('UPDATE preview_deliveries SET status=?,updated_at=CURRENT_TIMESTAMP WHERE request_id=? AND part=?', ('failed' if isinstance(error, TelegramFailure) else 'uncertain', request_id, part))
            if isinstance(error, (TelegramFailure, DeliveryUncertain)):
                raise
            raise DeliveryUncertain('Hasil pengiriman preview belum pasti. Periksa chat; tidak diulang otomatis.') from None
        with queue.db:
            queue.db.execute("UPDATE preview_deliveries SET status='sent',message_id=?,updated_at=CURRENT_TIMESTAMP WHERE request_id=? AND part=?", (message_id,request_id,part))
        results.append({'part':part, 'message_id':message_id})
    return {'request_id':request_id, 'draft':draft_id, 'status':row['status'], 'delivery':results,
            'published_to_meta':False, 'approvals_changed':False}


def fully_delivered(queue, draft_id, digest, chat_id, required):
    sent = {row['part'] for row in queue.db.execute("SELECT part FROM review_deliveries WHERE draft_id=? AND digest=? AND chat_id=? AND status='sent'", (draft_id,digest,chat_id))}
    if required.issubset(sent):
        return True
    # One complete explicit preview also counts as review evidence. Never combine partial requests.
    requests = {}
    for row in queue.db.execute("SELECT request_id,part FROM preview_deliveries WHERE draft_id=? AND digest=? AND chat_id=? AND status='sent'", (draft_id,digest,chat_id)):
        requests.setdefault(row['request_id'], set()).add(row['part'])
    return any(required.issubset(parts) for parts in requests.values())


def pending_ids(queue, chat_id, limit):
    ensure_delivery_table(queue)
    selected = []
    for row in queue.db.execute("SELECT id,digest,payload FROM drafts WHERE status='draft' ORDER BY rowid"):
        channel = json.loads(row['payload'])['channel']
        required = {'instagram-preview','instagram-caption','instagram-original'} if channel == 'instagram' else {'threads-text'}
        delivered = {part['part'] for part in queue.db.execute("SELECT part FROM review_deliveries WHERE draft_id=? AND digest=? AND chat_id=? AND status='sent'", (row['id'],row['digest'],chat_id))}
        if not required.issubset(delivered):
            selected.append(row['id'])
        if len(selected) == limit:
            break
    return selected


def send_reviews(queue, draft_ids, config, send=False, transport=None):
    ensure_delivery_table(queue)
    prepared = []
    # Verify the whole batch, including images, before sending anything.
    for draft_id in draft_ids:
        row = queue.get(draft_id)
        if row['status'] != 'draft':
            raise ValueError('Hanya draf pending yang dikirim untuk review. Pilih ID draf yang belum diputuskan.')
        parts = review_parts(queue, row)
        validate_parts(parts)
        prepared.append((row, parts))
    results = []
    for row, parts in prepared:
        for part, method, fields, file in parts:
            identity = (row['id'], row['digest'], config['chat_id'], part)
            old = queue.db.execute('SELECT status FROM review_deliveries WHERE draft_id=? AND digest=? AND chat_id=? AND part=?', identity).fetchone()
            if old and old['status'] == 'sent':
                results.append({'draft': row['id'], 'part':part, 'status':'already_sent'})
                continue
            if old and old['status'] in ('sending', 'uncertain'):
                raise DeliveryUncertain(f'Bagian {part} draf {row["id"]} belum pasti terkirim. Cek chat; pengulangan diblokir untuk mencegah duplikasi.')
            if not send:
                results.append({'draft':row['id'], 'part':part, 'status':'would_send'})
                continue
            with queue.db:
                queue.db.execute('BEGIN IMMEDIATE')
                old = queue.db.execute('SELECT status FROM review_deliveries WHERE draft_id=? AND digest=? AND chat_id=? AND part=?', identity).fetchone()
                if old and old['status'] != 'failed':
                    raise DeliveryUncertain('Pengiriman lain sedang aktif atau sudah selesai. Jalankan pengecekan ulang, jangan kirim paralel.')
                queue.db.execute('INSERT INTO review_deliveries (draft_id,digest,chat_id,part,status) VALUES (?,?,?,?,?) ON CONFLICT(draft_id,digest,chat_id,part) DO UPDATE SET status=excluded.status,updated_at=CURRENT_TIMESTAMP', (*identity,'sending'))
            try:
                params = {'chat_id':config['chat_id'], **fields}
                if method == 'sendMessage':
                    params['link_preview_options'] = json.dumps({'is_disabled':True})
                message_id = (transport or Telegram(config['token']))(method, params, file)
            except Exception as error:
                state = 'failed' if isinstance(error, TelegramFailure) else 'uncertain'
                with queue.db:
                    queue.db.execute('UPDATE review_deliveries SET status=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND chat_id=? AND part=?', (state,*identity))
                if isinstance(error, (TelegramFailure, DeliveryUncertain)):
                    raise
                raise DeliveryUncertain('Hasil pengiriman tidak pasti. Cek chat; tidak diulang otomatis.') from None
            with queue.db:
                queue.db.execute('UPDATE review_deliveries SET status=?,message_id=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND chat_id=? AND part=?', ('sent',message_id,*identity))
            results.append({'draft':row['id'], 'part':part, 'status':'sent', 'message_id':message_id})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=os.environ.get('IGNIDI_CONTENT_STATE', str(Path.home()/'.local/state/ignidi-content')))
    parser.add_argument('--env-file', default=str(Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes')))/'.env'))
    parser.add_argument('--draft', action='append', default=[])
    parser.add_argument('--pending', action='store_true')
    parser.add_argument('--limit', type=int, default=2)
    parser.add_argument('--send', action='store_true', help='Kirim ke Telegram. Tanpa flag ini hanya dry run.')
    args = parser.parse_args()
    if bool(args.draft) == args.pending or not 1 <= args.limit <= 10:
        parser.error('Pilih --draft ID (bisa berulang) atau --pending; limit 1–10.')
    config = load_config(args.env_file)
    queue = Queue(args.state)
    try:
        ids = args.draft or pending_ids(queue, config['chat_id'], args.limit)
        if len(ids) > 10:
            raise ValueError('Maksimal 10 draf per pengiriman.')
        result = send_reviews(queue, ids, config, send=args.send)
        print(json.dumps({'delivery':result, 'published_to_meta':False, 'approvals_changed':False}, indent=2))
    finally:
        queue.db.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, TelegramFailure, DeliveryUncertain) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, sqlite3.Error):
        print('Tidak dapat membaca konfigurasi atau antrean. Periksa path dan izin file di VPS.', file=sys.stderr)
        sys.exit(1)
