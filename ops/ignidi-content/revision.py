"""Read revision requests and submit a new immutable draft. Never approves or posts."""
import argparse
import json
import os
from pathlib import Path
import sys
from content_queue import Queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=os.environ.get('IGNIDI_CONTENT_STATE', str(Path.home()/'.local/state/ignidi-content')))
    commands = parser.add_subparsers(dest='command', required=True)
    show = commands.add_parser('show')
    show.add_argument('id')
    add = commands.add_parser('add')
    add.add_argument('id')
    add.add_argument('bundle')
    add.add_argument('--image')
    args = parser.parse_args()
    queue = Queue(args.state)
    try:
        parent = queue.get(args.id)
        payload = queue.verify_content(parent)
        if parent['status'] != 'needs_revision':
            raise ValueError('ID ini tidak sedang menunggu revisi. Periksa status terbaru.')
        if args.command == 'show':
            request = queue.db.execute("SELECT notes,created_at,event_id FROM editorial_reviews WHERE draft_id=? AND action='revisi' ORDER BY event_id DESC LIMIT 1", (args.id,)).fetchone()
            if not request:
                raise ValueError('Catatan revisi belum tersimpan.')
            print(json.dumps({'parent_id':args.id, 'draft':payload, 'request':dict(request), 'published':False}, ensure_ascii=False, indent=2))
        else:
            bundle = json.loads(Path(args.bundle).read_text(encoding='utf-8-sig'))
            channel = payload['channel']
            new_id = queue.add(channel, bundle[channel], args.image, revision_of=args.id)
            print(json.dumps({'id':new_id, 'channel':channel, 'status':'draft', 'published':False}))
    finally:
        queue.db.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
