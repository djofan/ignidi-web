"""Offline content queue. No publishing endpoint exists in this preparation package."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class Queue:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.directory / "queue.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft', signature TEXT, reviewer TEXT)""")
        self.db.commit()

    def prepare_payload(self, channel, content, image=None):
        """Validate/copy media without inserting or deciding a draft."""
        if channel not in ("instagram", "threads") or content.get("account") != "ignidi.labs":
            raise ValueError("Akun tujuan harus ignidi.labs dan kanal harus instagram/threads.")
        body = content.get("caption" if channel == "instagram" else "text", "")
        # Conservative byte count also covers Threads' special emoji counting.
        if not isinstance(body, str) or not body.strip() or len(body.encode("utf-8")) > (2200 if channel == "instagram" else 500):
            raise ValueError("Teks kosong atau melebihi batas konservatif kanal.")
        payload = {"channel": channel, "content": content}
        if channel == "instagram":
            if not image:
                raise ValueError("Instagram harus disertai preview JPEG yang akan direview.")
            data = Path(image).read_bytes()
            if not data.startswith(b"\xff\xd8\xff"):
                raise ValueError("Preview Instagram harus JPEG.")
            media_hash = hashlib.sha256(data).hexdigest()
            media_dir = self.directory / "media"
            media_dir.mkdir(exist_ok=True, mode=0o700)
            media_file = media_dir / f"{media_hash}.jpg"
            if not media_file.exists():
                media_file.write_bytes(data)
            payload["image_sha256"] = media_hash
        return payload

    def add(self, channel, content, image=None, *, revision_of=None):
        payload = self.prepare_payload(channel, content, image)
        if revision_of:
            return self._add_revision(revision_of, payload)
        encoded = canonical(payload)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        existing = self.db.execute("SELECT id FROM drafts WHERE digest=?", (digest,)).fetchone()
        if existing:
            return existing["id"]
        draft_id = secrets.token_hex(8)
        self.db.execute("INSERT INTO drafts (id,payload,digest) VALUES (?,?,?)", (draft_id, encoded, digest))
        self.db.commit()
        return draft_id

    def _add_revision(self, parent_id, payload):
        # Serialize replacement against decisions and another concurrent revision.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            parent = self.get(parent_id)
            previous = self.verify_content(parent)
            if parent['status'] != 'needs_revision':
                raise ValueError('Draf induk belum meminta revisi atau sudah digantikan.')
            if previous['channel'] != payload['channel']:
                raise ValueError('Revisi harus pada kanal yang sama.')
            if 'editorial_plan' in previous:
                # Revisions keep the parent's manual posting reference even if the model omits it.
                payload['editorial_plan'] = previous['editorial_plan']
            comparable = {key: value for key, value in previous.items() if key != 'revision'}
            if canonical(comparable) == canonical(payload):
                raise ValueError('Revisi belum mengubah teks atau gambar; buat perubahan sesuai catatan.')
            payload['revision'] = {'parent_id': parent_id, 'number': previous.get('revision', {}).get('number', 1) + 1}
            encoded = canonical(payload)
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            draft_id = secrets.token_hex(8)
            self.db.execute('INSERT INTO drafts (id,payload,digest) VALUES (?,?,?)', (draft_id, encoded, digest))
            self.db.execute("UPDATE drafts SET status='superseded',signature=NULL WHERE id=?", (parent_id,))
        return draft_id

    def get(self, draft_id):
        row = self.db.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
        if not row:
            raise ValueError("Draf tidak ditemukan.")
        return dict(row)

    def verify_content(self, row):
        digest = hashlib.sha256(row["payload"].encode()).hexdigest()
        if not hmac.compare_digest(digest, row["digest"]):
            raise ValueError("Isi draf berubah; review ulang diperlukan.")
        payload = json.loads(row["payload"])
        if payload["channel"] == "instagram":
            media_hash = payload["image_sha256"]
            if len(media_hash) != 64 or any(c not in "0123456789abcdef" for c in media_hash):
                raise ValueError("Hash media tidak valid.")
            data = (self.directory / "media" / f"{media_hash}.jpg").read_bytes()
            if hashlib.sha256(data).hexdigest() != media_hash:
                raise ValueError("Gambar berubah; review ulang diperlukan.")
        return payload

    def approve(self, draft_id, expected_digest, reviewer, key):
        if not key or len(key) < 32 or not reviewer.strip():
            raise ValueError("Review memerlukan kunci privat reviewer minimal 32 karakter dan identitas reviewer.")
        with self.db:
            row = self.get(draft_id)
            if row["status"] != "draft":
                raise ValueError("Hanya draf pending yang bisa disetujui.")
            self.verify_content(row)
            if not hmac.compare_digest(row["digest"], expected_digest):
                raise ValueError("Versi yang disetujui tidak sama dengan versi draf.")
            message = canonical({"id": draft_id, "digest": row["digest"], "reviewer": reviewer})
            signature = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
            self.db.execute("UPDATE drafts SET status='approved',signature=?,reviewer=? WHERE id=?", (signature, reviewer, draft_id))

    def approved(self, draft_id, key):
        row = self.get(draft_id)
        if row["status"] != "approved" or not key or len(key) < 32:
            raise ValueError("Belum ada persetujuan reviewer yang valid.")
        message = canonical({"id": draft_id, "digest": row["digest"], "reviewer": row["reviewer"]})
        expected = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(row["signature"] or "", expected):
            raise ValueError("Tanda tangan persetujuan tidak valid.")
        return self.verify_content(row)

    def reject(self, draft_id):
        row = self.get(draft_id)
        if row["status"] not in ("draft", "approved"):
            raise ValueError("Status tidak dapat ditolak.")
        self.db.execute("UPDATE drafts SET status='rejected',signature=NULL WHERE id=?", (draft_id,))
        self.db.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=os.environ.get("IGNIDI_CONTENT_STATE", str(Path.home() / ".local/state/ignidi-content")))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("bundle")
    add.add_argument("--image", required=True)
    commands.add_parser("list")
    show = commands.add_parser("show")
    show.add_argument("id")
    approve = commands.add_parser("approve")
    approve.add_argument("id")
    approve.add_argument("--digest", required=True)
    approve.add_argument("--reviewer", required=True)
    reject = commands.add_parser("reject")
    reject.add_argument("id")
    args = parser.parse_args()
    queue = Queue(args.state)
    if args.command == "add":
        bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8-sig"))
        print(json.dumps({"instagram": queue.add("instagram", bundle["instagram"], args.image), "threads": queue.add("threads", bundle["threads"]), "status": "draft", "published": False}))
    elif args.command == "list":
        print(json.dumps([dict(row) for row in queue.db.execute("SELECT id,digest,status,reviewer FROM drafts ORDER BY rowid DESC")], indent=2))
    elif args.command == "show":
        row = queue.get(args.id)
        row["payload"] = queue.verify_content(row)
        row.pop("signature", None)
        print(json.dumps(row, ensure_ascii=False, indent=2))
    elif args.command == "approve":
        queue.approve(args.id, args.digest, args.reviewer, os.environ.get("IGNIDI_REVIEW_KEY"))
        print("Disetujui untuk versi tersebut; belum diterbitkan. Publisher belum dipasang.")
    else:
        queue.reject(args.id)
        print("Ditolak. Revisi harus masuk sebagai draf baru.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
