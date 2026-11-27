"""Host only an approved JPEG on Cloudinary; verify exact bytes before Buffer handoff."""
import hashlib
import json
import re
import secrets
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

try:
    from .buffer_drafts import BufferError
    from .send_review import NoRedirect
except ImportError:
    from buffer_drafts import BufferError
    from send_review import NoRedirect


def validate_url(url,cloud_name,image_hash):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'res.cloudinary.com' or parts.port not in (None,443)
            or parts.username or parts.password or parts.query or parts.fragment
            or not parts.path.startswith(f'/{cloud_name}/image/upload/')
            or not parts.path.endswith(f'/ignidi-labs/{image_hash}.jpg')):
        raise BufferError('Cloudinary harus memberi URL HTTPS permanen untuk JPEG Ignidi yang tepat.')
    return url


def verify_remote(url,expected_hash):
    try:
        request = urllib.request.Request(url,headers={'Accept-Encoding':'identity'})
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=30) as response:
            data = response.read(8_000_001)
    except urllib.error.HTTPError as error:
        error.close()
        raise BufferError('Gambar Cloudinary belum dapat diakses publik; tidak ada draf Buffer yang dibuat.') from None
    except (OSError,ValueError):
        raise BufferError('Gambar Cloudinary belum dapat diakses publik; tidak ada draf Buffer yang dibuat.') from None
    if len(data) > 8_000_000 or hashlib.sha256(data).hexdigest() != expected_hash:
        raise BufferError('Byte gambar pada URL Cloudinary berbeda dari gambar yang direview. Handoff diblokir.')


def upload_jpeg(data,image_hash,config):
    cloud = config['cloud_name']
    if not re.fullmatch(r'[A-Za-z0-9_-]+',cloud):
        raise BufferError('Cloud name tidak valid.')
    fields = {'public_id':'ignidi-labs/'+image_hash,'overwrite':'false','timestamp':str(int(time.time()))}
    signature = hashlib.sha256(('&'.join(f'{key}={fields[key]}' for key in sorted(fields))+config['api_secret']).encode()).hexdigest()
    fields.update({'api_key':config['api_key'],'signature':signature})
    boundary = 'ignidi-'+secrets.token_hex(16)
    chunks = [f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode() for key,value in fields.items()]
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{image_hash}.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()+data+b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    request = urllib.request.Request(f'https://api.cloudinary.com/v1_1/{cloud}/image/upload',data=b''.join(chunks),method='POST',headers={'Content-Type':'multipart/form-data; boundary='+boundary})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=40) as response:
            result = json.loads(response.read(200_001))
    except urllib.error.HTTPError as error:
        error.close()
        raise BufferError('Cloudinary menolak upload. Periksa credential dan product environment; belum ada draf Buffer dibuat.') from None
    except (OSError,ValueError):
        raise BufferError('Upload Cloudinary belum berhasil dikonfirmasi. Tidak ada request pembuatan draf Buffer yang dikirim.') from None
    if result.get('public_id') != 'ignidi-labs/'+image_hash or result.get('resource_type') != 'image':
        raise BufferError('Respons Cloudinary tidak cocok dengan media Ignidi yang diminta.')
    return validate_url(result.get('secure_url',''),cloud,image_hash)


def approved_image_url(queue,payload,config,*,upload=None,verify=None):
    media = config.get('cloudinary',{})
    if not all(isinstance(media.get(key),str) and media[key].strip() for key in ('cloud_name','api_key','api_secret')):
        raise BufferError('Cloudinary belum dikonfigurasi. Jalankan setup_buffer.py di VPS.')
    image_hash = payload['image_sha256']
    data = (queue.directory/'media'/f'{image_hash}.jpg').read_bytes()
    if not data.startswith(b'\xff\xd8\xff') or len(data) > 8_000_000 or hashlib.sha256(data).hexdigest() != image_hash:
        raise BufferError('File JPEG lokal berbeda dari versi review atau terlalu besar.')
    existing = queue.db.execute('SELECT url FROM buffer_assets WHERE cloud_name=? AND image_sha256=?',(media['cloud_name'],image_hash)).fetchone()
    url = existing['url'] if existing else (upload or upload_jpeg)(data,image_hash,media)
    validate_url(url,media['cloud_name'],image_hash)
    (verify or verify_remote)(url,image_hash)
    with queue.db:
        queue.db.execute('INSERT INTO buffer_assets (cloud_name,image_sha256,url) VALUES (?,?,?) ON CONFLICT(cloud_name,image_sha256) DO UPDATE SET url=excluded.url',(media['cloud_name'],image_hash,url))
    return url
