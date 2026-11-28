"""One IG + one Threads draft per Jakarta day; Telegram review only, no Buffer calls."""
import argparse
from datetime import datetime, timedelta, timezone, date
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys

from content_queue import Queue, canonical
from send_review import (load_config, send_reviews, review_parts, validate_parts,
                         TelegramFailure, DeliveryUncertain)

WIB = timezone(timedelta(hours=7), 'Asia/Jakarta')
PILLARS = ('Web Building', 'Otomasi bisnis', 'Manajemen Sosial Media')


def today():
    return datetime.now(WIB).date().isoformat()


def valid_day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Tanggal harus YYYY-MM-DD dalam zona Asia/Jakarta.')
    return value


class DailyContent:
    def __init__(self, queue):
        self.queue = queue
        queue.db.execute('''CREATE TABLE IF NOT EXISTS daily_batches (
            day TEXT PRIMARY KEY, topic TEXT NOT NULL, pillar TEXT NOT NULL,
            bundle_digest TEXT NOT NULL, instagram_id TEXT NOT NULL, threads_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        queue.db.commit()

    def status(self, day):
        valid_day(day)
        row = self.queue.db.execute('SELECT * FROM daily_batches WHERE day=?', (day,)).fetchone()
        if not row:
            return None
        batch = dict(row)
        batch.pop('bundle_digest')
        batch['drafts'] = {channel: {'id': row[channel+'_id'],
                                    'status': self.queue.get(row[channel+'_id'])['status']}
                           for channel in ('instagram', 'threads')}
        return batch

    def plan(self, day):
        valid_day(day)
        history = []
        for row in self.queue.db.execute('SELECT id,payload,digest,status FROM drafts ORDER BY rowid DESC LIMIT 60'):
            payload = self.queue.verify_content(dict(row))
            content = payload['content']
            history.append({'id':row['id'], 'channel':payload['channel'], 'status':row['status'],
                            'excerpt':content.get('headline', content.get('text', ''))[:200]})
        pillar = PILLARS[(date.fromisoformat(day)-date(2026, 1, 1)).days % len(PILLARS)]
        return {'day':day, 'timezone':'Asia/Jakarta', 'pillar':pillar,
                'existing':self.status(day), 'recent_content':history,
                'work_directory':str(self.queue.directory/'daily'/day),
                'mode':'telegram_review_then_buffer_draft_only', 'published':False}

    def submit(self, day, bundle, image):
        valid_day(day)
        if day != today():
            raise ValueError('Batch baru hanya untuk tanggal hari ini di Asia/Jakarta. Jalankan plan lagi.')
        if not isinstance(bundle, dict) or bundle.get('status') != 'draft':
            raise ValueError('Bundle harus berstatus draft.')
        topic, pillar = bundle.get('topic'), bundle.get('pillar')
        if not isinstance(topic, str) or not topic.strip() or len(topic) > 200 or pillar not in PILLARS:
            raise ValueError('Topik wajib diisi dan pilar harus salah satu dari tiga layanan Ignidi.')
        if any(not isinstance(bundle.get(channel), dict) for channel in ('instagram', 'threads')):
            raise ValueError('Bundle wajib berisi objek instagram dan threads.')
        ig = bundle['instagram']
        headline, points, alt = ig.get('headline'), ig.get('points'), ig.get('alt_text')
        if (not isinstance(headline, str) or not headline.strip() or len(headline) > 80
                or not isinstance(points, list) or not 1 <= len(points) <= 3
                or any(not isinstance(p, str) or not p.strip() or len(p) > 65 for p in points)
                or not isinstance(alt, str) or not alt.strip() or len(alt.encode()) > 800):
            raise ValueError('Instagram memerlukan headline, 1–3 poin, dan alt text yang valid.')
        # Validate BOTH channels and every Telegram part before any draft is inserted.
        payloads = {channel:self.queue.prepare_payload(channel, bundle.get(channel, {}),
                                                      image if channel == 'instagram' else None)
                    for channel in ('instagram', 'threads')}
        encoded = {channel:canonical(payload) for channel,payload in payloads.items()}
        digests = {channel:hashlib.sha256(value.encode()).hexdigest() for channel,value in encoded.items()}
        fingerprint = hashlib.sha256(canonical({'topic':topic,'pillar':pillar,'digests':digests}).encode()).hexdigest()
        ids = {channel:secrets.token_hex(8) for channel in payloads}
        for channel in payloads:
            row = {'id':ids[channel], 'payload':encoded[channel], 'digest':digests[channel], 'status':'draft'}
            validate_parts(review_parts(self.queue, row))
        with self.queue.db:
            self.queue.db.execute('BEGIN IMMEDIATE')
            old = self.queue.db.execute('SELECT * FROM daily_batches WHERE day=?', (day,)).fetchone()
            if old:
                if old['bundle_digest'] != fingerprint:
                    raise ValueError('Batch hari ini sudah ada. Gunakan ID yang sama; revisi melalui Telegram.')
            else:
                # Exact-copy old content is rejected instead of reusing an approved/old ID.
                if any(self.queue.db.execute('SELECT 1 FROM drafts WHERE digest=?', (digest,)).fetchone()
                       for digest in digests.values()):
                    raise ValueError('Konten identik sudah ada. Buat sudut bahasan baru sebelum submit.')
                for channel in payloads:
                    self.queue.db.execute('INSERT INTO drafts (id,payload,digest) VALUES (?,?,?)',
                                          (ids[channel], encoded[channel], digests[channel]))
                self.queue.db.execute('''INSERT INTO daily_batches
                    (day,topic,pillar,bundle_digest,instagram_id,threads_id) VALUES (?,?,?,?,?,?)''',
                    (day,topic,pillar,fingerprint,ids['instagram'],ids['threads']))
        return self.status(day)

    def send(self, day, config, *, send=False, transport=None):
        batch = self.status(day)
        if not batch:
            raise ValueError('Belum ada batch pada tanggal ini. Jangan mengirim semua draf pending.')
        # Already decided/revised channels are never reopened or re-sent by the daily job.
        ids = [draft['id'] for draft in batch['drafts'].values() if draft['status'] == 'draft']
        result = send_reviews(self.queue, ids, config, send=send, transport=transport)
        return {'day':day, 'drafts':batch['drafts'], 'delivery':result,
                'published':False, 'buffer_called':False, 'approvals_changed':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=os.environ.get('IGNIDI_CONTENT_STATE', str(Path.home()/'.local/state/ignidi-content')))
    parser.add_argument('--env-file', default=str(Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes')))/'.env'))
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'status', 'send'):
        command = sub.add_parser(name)
        command.add_argument('--day', default=today())
        if name == 'send':
            command.add_argument('--send', action='store_true', help='Kirim Telegram; default dry run.')
    submit = sub.add_parser('submit')
    submit.add_argument('--day', required=True)
    submit.add_argument('bundle')
    submit.add_argument('--image', required=True)
    args = parser.parse_args()
    queue = Queue(args.state)
    try:
        daily = DailyContent(queue)
        if args.command == 'submit':
            result = daily.submit(args.day, json.loads(Path(args.bundle).read_text(encoding='utf-8-sig')), args.image)
        elif args.command == 'send':
            result = daily.send(args.day, load_config(args.env_file), send=args.send)
        else:
            result = getattr(daily, args.command)(args.day)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        queue.db.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, TelegramFailure, DeliveryUncertain) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, sqlite3.Error, KeyError, TypeError):
        print('Batch harian gagal dibaca/disimpan. Periksa file, format, dan izin; jangan reset antrean.', file=sys.stderr)
        sys.exit(1)
