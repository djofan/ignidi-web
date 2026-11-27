"""Buffer handoff restricted to saveToDraft=true. No scheduling or publishing operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import urllib.error
import urllib.request

try:
    from .send_review import NoRedirect
except ImportError:
    from send_review import NoRedirect

CHANNEL_FIELDS = 'id organizationId name service externalLink isDisconnected isLocked'
POST_FIELDS = 'id channelId text status dueAt assets { ... on ImageAsset { source } }'
QUERIES = {
    'organizations': 'query IgnidiOrganizations { account { organizations { id name } } }',
    'channels': 'query IgnidiChannels($input: ChannelsInput!) { channels(input: $input) { '+CHANNEL_FIELDS+' } }',
    'channel': 'query IgnidiChannel($input: ChannelInput!) { channel(input: $input) { '+CHANNEL_FIELDS+' } }',
    'post': 'query IgnidiPost($input: PostInput!) { post(input: $input) { '+POST_FIELDS+' } }',
}
# Safety-critical literals are not parameters and cannot be overridden by content/config.
CREATE_DRAFT = '''mutation IgnidiDraft($text: String!, $channelId: ChannelId!,
    $assets: [AssetInput!]!, $metadata: PostInputMetaData) {
  createPost(input: {text: $text, channelId: $channelId, assets: $assets,
    metadata: $metadata, schedulingType: automatic, mode: addToQueue,
    saveToDraft: true, needsApproval: false, aiAssisted: true}) {
    __typename
    ... on PostActionSuccess { post { '''+POST_FIELDS+''' } }
    ... on MutationError { message }
  }
}'''


class BufferError(Exception):
    """Safe operator-facing error; no credentials or raw server messages."""


class BufferUncertain(BufferError):
    """A mutation may have reached Buffer. Never retry without reconciliation."""


class BufferAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.opener = urllib.request.build_opener(NoRedirect())

    def _request(self, query, variables=None, *, mutation=False):
        body = json.dumps({'query':query,'variables':variables or {}}).encode()
        request = urllib.request.Request('https://api.buffer.com', data=body, method='POST',
                    headers={'Authorization':'Bearer '+self.api_key, 'Content-Type':'application/json'})
        try:
            with self.opener.open(request,timeout=40) as response:
                data = json.loads(response.read(2_000_001))
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
            if code in (400,401,403,404,422,429):
                raise BufferError(f'Buffer menolak request (HTTP {code}). Periksa API key, izin, channel, atau limit.') from None
            raise (BufferUncertain if mutation else BufferError)('Respons Buffer belum pasti. Periksa Drafts Buffer; jangan ulang otomatis.') from None
        except (OSError,ValueError):
            raise (BufferUncertain if mutation else BufferError)('Koneksi/respons Buffer terputus. Periksa Drafts Buffer; jangan ulang otomatis.') from None
        if not isinstance(data,dict) or data.get('errors') or not isinstance(data.get('data'),dict):
            # GraphQL can return data and errors after a mutation side effect.
            raise (BufferUncertain if mutation else BufferError)('Buffer mengembalikan error GraphQL; periksa konfigurasi dan hasilnya di Buffer.')
        return data['data']

    def organizations(self):
        return self._request(QUERIES['organizations'])['account']['organizations']

    def channels(self, organization):
        return self._request(QUERIES['channels'],{'input':{'organizationId':organization}})['channels']

    def channel(self, channel_id):
        return self._request(QUERIES['channel'],{'input':{'id':channel_id}})['channel']

    def post(self, post_id):
        return self._request(QUERIES['post'],{'input':{'id':post_id}})['post']

    def create_draft(self, *, text, channel_id, assets, metadata):
        result = self._request(CREATE_DRAFT,{'text':text,'channelId':channel_id,'assets':assets,'metadata':metadata},mutation=True)['createPost']
        if result.get('__typename') != 'PostActionSuccess':
            if result.get('__typename') in ('InvalidInputError','UnauthorizedError','NotFoundError','LimitReachedError'):
                raise BufferError('Buffer menolak pembuatan draf. Periksa izin, media, atau format di dashboard; tidak dijadwalkan ulang.')
            raise BufferUncertain('Buffer mengembalikan hasil mutasi belum pasti. Periksa Drafts Buffer sebelum mencoba lagi.')
        post = result.get('post')
        if not isinstance(post,dict) or not post.get('id'):
            raise BufferUncertain('Buffer belum memberi ID draf. Periksa Drafts Buffer sebelum mencoba lagi.')
        return post


def config_path(queue):
    return queue.directory/'buffer-config.json'


def load_config(queue, *, required=True):
    path = config_path(queue)
    if not path.exists():
        if not required:
            return None
        raise BufferError('Buffer belum dikonfigurasi. Jalankan python3 setup_buffer.py di VPS; jangan kirim API key ke Telegram.')
    try:
        if os.name != 'nt' and path.stat().st_mode & 0o077:
            raise BufferError('Izin buffer-config.json harus 600 sebelum integrasi diaktifkan.')
        config = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(config,dict) or config.get('mode') != 'draft_only' or not isinstance(config.get('api_key'),str)
                or not config['api_key'].strip() or not config.get('organization_id')
                or any(char in config['api_key'] for char in '\r\n')
                or set(config['channels']) != {'instagram','threads'}
                or any(not value for value in config['channels'].values())
                or config['channels']['instagram'] == config['channels']['threads']):
            raise ValueError()
    except (ValueError,KeyError,TypeError):
        raise BufferError('Konfigurasi Buffer tidak valid atau bukan mode draft_only. Jalankan setup_buffer.py.') from None
    return config


def valid_channel(channel, service, organization):
    from urllib.parse import urlsplit
    url = urlsplit(channel.get('externalLink') or '')
    expected = {'instagram':{'instagram.com','www.instagram.com'},
                'threads':{'threads.com','www.threads.com','threads.net','www.threads.net'}}[service]
    identity = (channel.get('name','').lstrip('@').casefold() == 'ignidi.labs'
                or (url.hostname in expected and url.path.rstrip('/').lstrip('/@').casefold() == 'ignidi.labs'))
    return (channel.get('service') == service and channel.get('organizationId') == organization
            and identity and channel.get('isDisconnected') is False and channel.get('isLocked') is False)


def verify_channel(api, config, service):
    channel = api.channel(config['channels'][service])
    if channel.get('id') != config['channels'][service] or not valid_channel(channel, service, config['organization_id']):
        raise BufferError('Channel Buffer harus akun ignidi.labs yang tersambung, tidak terkunci, dan sesuai organisasi/kanal pilihan.')
    return channel


def ensure_tables(queue):
    queue.db.execute('''CREATE TABLE IF NOT EXISTS buffer_exports (
        draft_id TEXT NOT NULL, digest TEXT NOT NULL, organization_id TEXT NOT NULL,
        channel_id TEXT NOT NULL, status TEXT NOT NULL, post_id TEXT, media_url TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (draft_id,digest,organization_id,channel_id))''')
    queue.db.execute('''CREATE TABLE IF NOT EXISTS buffer_assets (
        cloud_name TEXT NOT NULL, image_sha256 TEXT NOT NULL, url TEXT NOT NULL,
        PRIMARY KEY (cloud_name,image_sha256))''')
    queue.db.commit()


def approved_payload(queue, draft_id, owner):
    if not re.fullmatch(r'[a-f0-9]{16}', draft_id):
        raise BufferError('Gunakan ID draf dari /statuskonten.')
    row = queue.get(draft_id)
    payload = queue.verify_content(row)
    if row['status'] != 'review_approved' or row['reviewer'] != 'telegram:'+str(owner):
        raise BufferError('Versi ini belum disetujui pemilik atau sudah dicabut/direvisi. Review di Telegram terlebih dahulu.')
    try:
        event = queue.db.execute('SELECT * FROM editorial_reviews WHERE draft_id=? ORDER BY event_id DESC LIMIT 1',(draft_id,)).fetchone()
    except sqlite3.OperationalError:
        event = None
    if not event or event['action'] != 'setuju' or event['digest'] != row['digest'] or event['user_id'] != str(owner) or event['chat_id'] != str(owner):
        raise BufferError('Tidak ditemukan keputusan Telegram pemilik untuk versi ini.')
    if payload['channel'] not in ('instagram','threads') or payload['content'].get('account') != 'ignidi.labs':
        raise BufferError('Target draf harus ignidi.labs.')
    return row, payload


def verify_post(post, channel_id, text, media_url):
    if (not {'id','channelId','text','status','dueAt','assets'}.issubset(post)
            or not isinstance(post.get('assets'),list)
            or post.get('channelId') != channel_id or post.get('text') != text
            or post.get('status') != 'draft' or post.get('dueAt') is not None):
        raise BufferUncertain('Hasil Buffer berbeda dari draf tanpa jadwal yang diminta. Periksa dashboard; proses dihentikan tanpa retry.')
    sources = [asset.get('source') for asset in post.get('assets',[])]
    if sources != ([media_url] if media_url else []):
        raise BufferUncertain('Media pada draf Buffer tidak cocok dengan versi review. Periksa dashboard sebelum melanjutkan.')


def stage_draft(queue, draft_id, owner, *, config=None, api=None, media=None):
    config = config or load_config(queue)
    if config.get('mode') != 'draft_only':
        raise BufferError('Integrasi hanya menerima mode draft_only.')
    row, payload = approved_payload(queue,draft_id,owner)
    api = api or BufferAPI(config['api_key'])
    channel_id = config['channels'][payload['channel']]
    identity = (draft_id,row['digest'],config['organization_id'],channel_id)
    ensure_tables(queue)
    with queue.db:
        queue.db.execute('BEGIN IMMEDIATE')
        approved_payload(queue,draft_id,owner)
        old = queue.db.execute('SELECT * FROM buffer_exports WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?',identity).fetchone()
        cached = dict(old) if old and old['status'] == 'draft' else None
        if old and not cached and old['status'] != 'failed':
            raise BufferUncertain('Handoff Buffer sedang berjalan atau hasilnya belum pasti. Periksa /bufferstatus ID; jangan kirim ulang buta.')
        if not cached:
            queue.db.execute("INSERT INTO buffer_exports (draft_id,digest,organization_id,channel_id,status) VALUES (?,?,?,?,'preparing') ON CONFLICT(draft_id,digest,organization_id,channel_id) DO UPDATE SET status='preparing',updated_at=CURRENT_TIMESTAMP",identity)
    if cached:
        verify_channel(api,config,payload['channel'])
        post = api.post(cached['post_id'])
        text = payload['content']['caption' if payload['channel'] == 'instagram' else 'text']
        verify_post(post,channel_id,text,cached['media_url'])
        return {'post_id':cached['post_id'],'already_saved':True,'published':False}
    mutation_started = False
    post_id = None
    try:
        verify_channel(api,config,payload['channel'])
        assets, metadata, media_url = [], None, None
        if payload['channel'] == 'instagram':
            if media is None:
                try:
                    from .buffer_media import approved_image_url
                except ImportError:
                    from buffer_media import approved_image_url
                media = approved_image_url
            media_url = media(queue,payload,config)
            assets = [{'image':{'url':media_url,'metadata':{'altText':str(payload['content'].get('alt_text',''))}}}]
            metadata = {'instagram':{'type':'post','shouldShareToFeed':True}}
        text = payload['content']['caption' if payload['channel'] == 'instagram' else 'text']
        approved_payload(queue,draft_id,owner)
        with queue.db:
            queue.db.execute("UPDATE buffer_exports SET status='sending',media_url=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?",(media_url,*identity))
        mutation_started = True
        post = api.create_draft(text=text,channel_id=channel_id,assets=assets,metadata=metadata)
        post_id = post.get('id')
        verify_post(post,channel_id,text,media_url)
        with queue.db:
            queue.db.execute("UPDATE buffer_exports SET status='draft',post_id=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?",(post_id,*identity))
        return {'post_id':post_id,'already_saved':False,'published':False}
    except Exception as error:
        uncertain = mutation_started and not (isinstance(error,BufferError) and not isinstance(error,BufferUncertain))
        with queue.db:
            queue.db.execute('UPDATE buffer_exports SET status=?,post_id=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?',('uncertain' if uncertain else 'failed',post_id,*identity))
        if isinstance(error,(BufferError,ValueError)):
            raise
        raise (BufferUncertain if uncertain else BufferError)('Handoff Buffer gagal. Periksa status dan konfigurasi di VPS; tidak diulang otomatis.') from None


def status(queue, owner, draft_id='', *, config=None, api=None):
    config = config or load_config(queue)
    api = api or BufferAPI(config['api_key'])
    if not draft_id:
        for service in ('instagram','threads'):
            verify_channel(api,config,service)
        return 'Buffer terhubung: Instagram dan Threads @ignidi.labs.\nMode: DRAFT ONLY — tanpa jadwal/publikasi.'
    if not re.fullmatch(r'[a-f0-9]{16}',draft_id):
        raise BufferError('Format: /bufferstatus ID atau /bufferstatus.')
    row = queue.get(draft_id)
    payload = queue.verify_content(row)
    ensure_tables(queue)
    exported = queue.db.execute('SELECT * FROM buffer_exports WHERE draft_id=? AND digest=? ORDER BY updated_at DESC LIMIT 1',(draft_id,row['digest'])).fetchone()
    if not exported:
        return f'{draft_id}: belum disalin ke Buffer.\n/bufferdraft {draft_id}'
    text = f'{draft_id}\nStatus handoff: {exported["status"]}'
    if exported['post_id']:
        post = api.post(exported['post_id'])
        text += f'\nID Buffer: {exported["post_id"]}\nStatus di Buffer: {post.get("status")}\nJadwal di Buffer: {post.get("dueAt") or "tidak ada"}'
    try:
        approved_payload(queue,draft_id,owner)
    except (BufferError,ValueError):
        text += '\nPERSETUJUAN SUDAH DICABUT / VERSI LAMA. Jangan jadwalkan draf Buffer ini.'
    return text + '\nIntegrasi ini hanya membuat draf; tidak menjadwalkan/memosting.'


def reconcile(queue,draft_id,post_id,owner,*,config=None,api=None):
    """Read-only remote check; manually bind a known Buffer draft after an uncertain mutation."""
    config = config or load_config(queue)
    api = api or BufferAPI(config['api_key'])
    row,payload = approved_payload(queue,draft_id,owner)
    ensure_tables(queue)
    identity = (draft_id,row['digest'],config['organization_id'],config['channels'][payload['channel']])
    export = queue.db.execute('SELECT * FROM buffer_exports WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?',identity).fetchone()
    if not export or export['status'] not in ('sending','uncertain','preparing'):
        raise BufferError('Tidak ada handoff belum pasti yang perlu direkonsiliasi.')
    post = api.post(post_id)
    text = payload['content']['caption' if payload['channel'] == 'instagram' else 'text']
    verify_post(post,identity[3],text,export['media_url'])
    with queue.db:
        approved_payload(queue,draft_id,owner)
        queue.db.execute("UPDATE buffer_exports SET status='draft',post_id=?,updated_at=CURRENT_TIMESTAMP WHERE draft_id=? AND digest=? AND organization_id=? AND channel_id=?",(post_id,*identity))
    return {'post_id':post_id,'published':False}


def main():
    from content_queue import Queue
    from send_review import load_config as telegram_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',default=os.environ.get('IGNIDI_CONTENT_STATE',str(Path.home()/'.local/state/ignidi-content')))
    commands = parser.add_subparsers(dest='command',required=True)
    check = commands.add_parser('check')
    check.add_argument('id',nargs='?',default='')
    stage = commands.add_parser('stage')
    stage.add_argument('id')
    stage.add_argument('--send-draft',action='store_true')
    recovery = commands.add_parser('reconcile')
    recovery.add_argument('id')
    recovery.add_argument('post_id')
    args = parser.parse_args()
    queue = Queue(args.state)
    try:
        owner = telegram_config(Path(os.environ.get('HERMES_HOME',str(Path.home()/'.hermes')))/'.env')['chat_id']
        if args.command == 'check':
            print(status(queue,owner,args.id))
        elif args.command == 'reconcile':
            print(json.dumps(reconcile(queue,args.id,args.post_id,owner)))
        elif args.send_draft:
            print(json.dumps(stage_draft(queue,args.id,owner)))
        else:
            row,payload = approved_payload(queue,args.id,owner)
            print(json.dumps({'id':row['id'],'channel':payload['channel'],'digest':row['digest'],'mode':'draft_only','would_stage':True,'network_calls':0,'published':False}))
    finally:
        queue.db.close()


if __name__ == '__main__':
    try:
        main()
    except (BufferError,ValueError) as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
    except (OSError,sqlite3.Error,KeyError,TypeError):
        print('Tidak dapat membaca antrean/config Buffer. Periksa setup di VPS; tidak ada retry otomatis.',file=sys.stderr)
        sys.exit(1)
