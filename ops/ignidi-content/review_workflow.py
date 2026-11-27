"""Deterministic Telegram feedback. Editorial decisions never mint publish signatures."""
import hmac
import json
import re

try:
    from .send_review import ensure_delivery_table, fully_delivered
except ImportError:
    from send_review import ensure_delivery_table, fully_delivered

LOCK = 'Belum diposting. Publikasi Instagram/Threads tetap nonaktif.'
LABELS = {'draft': 'MENUNGGU REVIEW', 'review_approved': 'DISETUJUI PEMILIK',
          'needs_revision': 'PERLU REVISI', 'superseded': 'DIGANTIKAN REVISI',
          'rejected': 'DITOLAK', 'approved': 'PERSETUJUAN OPERATOR LAMA'}


class Reviews:
    def __init__(self, queue, owner):
        if not re.fullmatch(r'[1-9]\d*', str(owner)):
            raise ValueError('Tujuan review harus ID DM pemilik.')
        self.queue, self.owner = queue, str(owner)
        ensure_delivery_table(queue)
        queue.db.execute('''CREATE TABLE IF NOT EXISTS editorial_reviews (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id TEXT NOT NULL, digest TEXT NOT NULL, action TEXT NOT NULL,
            notes TEXT NOT NULL, user_id TEXT NOT NULL, chat_id TEXT NOT NULL,
            session_id TEXT NOT NULL, dispatch TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
        queue.db.commit()

    def authorize(self, platform, source):
        # Only adapter-provided identity; never parse an identity from user text.
        platform = getattr(platform, 'value', platform)
        if (platform != 'telegram' or source is None
                or str(getattr(source, 'user_id', '')) != self.owner
                or str(getattr(source, 'chat_id', '')) != self.owner
                or getattr(source, 'chat_type', '') != 'dm'):
            raise ValueError('Perintah review hanya dari DM Telegram pemilik yang dikonfigurasi.')

    def latest_revision(self, draft_id):
        row = self.queue.db.execute("SELECT * FROM editorial_reviews WHERE draft_id=? AND action='revisi' ORDER BY event_id DESC LIMIT 1", (draft_id,)).fetchone()
        if not row:
            raise ValueError('Belum ada catatan revisi untuk ID ini.')
        return dict(row)

    def decide(self, action, raw, *, platform, source, session_id=''):
        self.authorize(platform, source)
        if action not in ('setuju', 'revisi', 'tolak'):
            raise ValueError('Perintah tidak dikenal.')
        pieces = raw.strip().split(maxsplit=2)
        if len(pieces) < 2 or not re.fullmatch(r'[a-f0-9]{16}', pieces[0]) or not re.fullmatch(r'[a-f0-9]{64}', pieces[1]):
            raise ValueError(f'Format: /{action} ID SHA256' + (' catatan revisi' if action == 'revisi' else ''))
        draft_id, digest = pieces[:2]
        notes = pieces[2].strip() if len(pieces) == 3 else ''
        if (action == 'revisi' and not notes) or len(notes) > 1200 or (action == 'setuju' and notes):
            raise ValueError('Setuju harus tepat ID dan SHA256. Revisi wajib catatan, maksimal 1200 karakter.')
        with self.queue.db:
            self.queue.db.execute('BEGIN IMMEDIATE')
            row = self.queue.get(draft_id)
            payload = self.queue.verify_content(row)
            if not hmac.compare_digest(digest, row['digest']):
                raise ValueError('Versi berbeda. Gunakan ID dan SHA256 dari preview yang direview.')
            required = {'instagram-preview', 'instagram-caption', 'instagram-original'} if payload['channel'] == 'instagram' else {'threads-text'}
            if not fully_delivered(self.queue, draft_id, digest, self.owner, required):
                raise ValueError('Preview versi ini belum lengkap terkirim ke DM pemilik. Selesaikan pengiriman sebelum review.')
            desired = {'setuju':'review_approved', 'revisi':'needs_revision', 'tolak':'rejected'}[action]
            last = self.queue.db.execute('SELECT * FROM editorial_reviews WHERE draft_id=? ORDER BY event_id DESC LIMIT 1', (draft_id,)).fetchone()
            if row['status'] == desired and last and last['action'] == action and last['notes'] == notes:
                return dict(last), False
            valid = ('draft',) if action == 'setuju' else ('draft', 'review_approved', 'approved')
            if row['status'] not in valid:
                raise ValueError('Versi ini sudah diputuskan atau digantikan. Periksa /statuskonten; review hasil revisi dengan ID baru.')
            self.queue.db.execute('UPDATE drafts SET status=?,signature=NULL,reviewer=? WHERE id=?', (desired, 'telegram:' + self.owner, draft_id))
            cursor = self.queue.db.execute('INSERT INTO editorial_reviews (draft_id,digest,action,notes,user_id,chat_id,session_id) VALUES (?,?,?,?,?,?,?)', (draft_id, digest, action, notes, self.owner, self.owner, session_id))
            event = dict(self.queue.db.execute('SELECT * FROM editorial_reviews WHERE event_id=?', (cursor.lastrowid,)).fetchone())
        return event, True

    def claim_revision_dispatch(self, event_id):
        with self.queue.db:
            cursor = self.queue.db.execute("UPDATE editorial_reviews SET dispatch='dispatching' WHERE event_id=? AND action='revisi' AND dispatch='pending'", (event_id,))
        return cursor.rowcount == 1

    def finish_revision_dispatch(self, event_id, accepted):
        with self.queue.db:
            self.queue.db.execute("UPDATE editorial_reviews SET dispatch=? WHERE event_id=? AND dispatch='dispatching'", ('queued' if accepted else 'manual', event_id))

    def status(self, raw, *, platform, source):
        self.authorize(platform, source)
        draft_id = raw.strip()
        if draft_id:
            row = self.queue.get(draft_id)
            payload = self.queue.verify_content(row)
            revision = payload.get('revision', {})
            message = (f'{payload["channel"].upper()} · @ignidi.labs\nID: {row["id"]}\n'
                       f'Status: {LABELS.get(row["status"], row["status"])}\nSHA256: {row["digest"]}'
                       f'\nVersi: {revision.get("number", 1)}\n\n/preview {row["id"]}')
            if revision:
                message += f'\nInduk: {revision["parent_id"]}'
            if row['status'] == 'draft':
                message += (f'\n\n/setuju {row["id"]} {row["digest"]}'
                            f'\n/revisi {row["id"]} {row["digest"]} catatanmu'
                            f'\n/tolak {row["id"]} {row["digest"]}')
            children = []
            for child in self.queue.db.execute('SELECT id,payload FROM drafts ORDER BY rowid DESC'):
                if json.loads(child['payload']).get('revision', {}).get('parent_id') == draft_id:
                    children.append(child['id'])
            if children:
                message += '\nID hasil revisi: ' + ', '.join(children)
            return message + '\n\n' + LOCK
        rows = list(self.queue.db.execute('SELECT * FROM drafts ORDER BY rowid DESC LIMIT 6'))
        lines = ['IGNIDI · REVIEW KONTEN']
        for row in rows:
            payload = self.queue.verify_content(row)
            lines.append(f'{payload["channel"].upper()} · {row["id"]}\n{LABELS.get(row["status"], row["status"])}\n/preview {row["id"]}\n/statuskonten {row["id"]}')
        return '\n\n'.join(lines + [LOCK])


def revision_prompt(studio, event):
    # Notes stay in SQLite: never interpolate review text into shell commands.
    return ('Kerjakan satu revisi konten Ignidi yang diminta pemilik. Ini bukan persetujuan publikasi. '
            'Jangan approve, jangan posting, jangan mengubah layanan atau credential. '
            f'Folder studio: {studio}. Baca hermes-content-prompt.md. '
            'Untuk render, IGNIDI_LOGO_PATH menunjuk public/ignidi-labs.jpeg di root repo ini, dua tingkat di atas studio. '
            f'Baca catatan dan draf asli melalui python3 revision.py show {event["draft_id"]}. '
            'Buat bundle JSON baru mengikuti samples/lead.json dan catatan pemilik. '
            'Untuk Instagram render gambar baru memakai render.mjs dan logo asli; untuk Threads cukup teks. '
            f'Masukkan dengan python3 revision.py add {event["draft_id"]} BUNDLE.json '
            '[--image PREVIEW.jpg untuk Instagram]. CLI memilih hanya kanal induk. '
            'Kirim ID baru menggunakan python3 send_review.py --draft ID_BARU --send. '
            'Hasil revisi harus direview dan disetujui lagi; jangan mengedit draf lama di database. '
            f'Event revisi: {event["event_id"]}. Publikasi tetap nonaktif.')
