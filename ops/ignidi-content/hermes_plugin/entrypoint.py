"""Hermes native commands: no second Telegram poller, LLM tool, signing key or publisher."""
import os
from pathlib import Path
import sqlite3

from .content_queue import Queue
from .send_review import load_config, send_preview, TelegramFailure, DeliveryUncertain
from .review_workflow import Reviews, LOCK, revision_prompt
from .buffer_drafts import BufferError, load_config as buffer_config, stage_draft, status as buffer_status


def register(ctx):
    def run(command, raw, *, platform='', source=None, session_id='', session_key=''):
        queue = None
        try:
            home = Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes')))
            config = load_config(home/'.env')
            queue = Queue(os.environ.get('IGNIDI_CONTENT_STATE', str(Path.home()/'.local/state/ignidi-content')))
            reviews = Reviews(queue, config['chat_id'])
            if command == 'statuskonten':
                return reviews.status(raw, platform=platform, source=source)
            if command == 'preview':
                reviews.authorize(platform, source)
                result = send_preview(queue, raw.strip(), config)
                return f'Preview {result["draft"]} ditampilkan ulang. Status review tidak berubah.\n\n{LOCK}'
            if command in ('bufferstatus','bufferdraft'):
                reviews.authorize(platform, source)
                if command == 'bufferstatus':
                    return buffer_status(queue,config['chat_id'],raw.strip()) + '\n\n' + LOCK
                result = stage_draft(queue,raw.strip(),config['chat_id'])
                return f'Draft Buffer tersimpan.\nID lokal: {raw.strip()}\nID Buffer: {result["post_id"]}\nTanpa jadwal tayang.\n\n{LOCK}'
            event, fresh = reviews.decide(command, raw, platform=platform, source=source, session_id=session_id)
            if command == 'revisi':
                accepted = False
                # Repeated command never dispatches the model twice.
                if fresh and session_key and reviews.claim_revision_dispatch(event['event_id']):
                    try:
                        studio = (Path(__file__).parent/'studio-path.txt').read_text().strip()
                        accepted = bool(ctx.inject_message(revision_prompt(studio, event), session_key=session_key))
                    except Exception:
                        accepted = False
                    reviews.finish_revision_dispatch(event['event_id'], accepted)
                detail = ('Hermes menerima tugas revisi; tunggu preview dengan ID baru.' if accepted
                          else 'Catatan tersimpan. Jika belum dikerjakan, kirim pesan biasa: kerjakan revisi ID ' + event['draft_id'] + ' sesuai revision.py show, lalu kirim preview ID baru.')
                return f'PERLU REVISI · {event["draft_id"]}\nPersetujuan lama dicabut.\n{detail}\nJika ada draf versi lama di Buffer, jangan jadwalkan; hasil revisi perlu persetujuan baru.\n\n{LOCK}'
            label = 'DISETUJUI PEMILIK' if command == 'setuju' else 'DITOLAK'
            handoff = ''
            if command == 'setuju':
                try:
                    configured = buffer_config(queue,required=False)
                    if configured and configured.get('auto_stage') is True:
                        result = stage_draft(queue,event['draft_id'],config['chat_id'],config=configured)
                        handoff = f'\nDraft Buffer: {result["post_id"]} (tanpa jadwal).'
                    else:
                        handoff = '\nBuffer belum diaktifkan; persetujuan tersimpan lokal.'
                except (BufferError,ValueError,OSError,sqlite3.Error):
                    handoff = f'\nPersetujuan tersimpan; handoff Buffer belum dikonfirmasi.\n/bufferstatus {event["draft_id"]}'
            else:
                handoff = '\nJika versi ini sudah disalin ke Buffer, draf lama tetap di sana. Jangan jadwalkan; periksa /bufferstatus ID.'
            return f'{label} · {event["draft_id"]}\nVersi: {event["digest"]}\nKeputusan hanya untuk kanal dan versi ini.{handoff}\n\n{LOCK}'
        except BufferError as error:
            return 'Buffer: ' + str(error) + '\n\n' + LOCK
        except (TelegramFailure, DeliveryUncertain) as error:
            return 'Preview belum lengkap: ' + str(error) + '\n\n' + LOCK
        except ValueError as error:
            return 'Review tidak diproses: ' + str(error) + '\n\n' + LOCK
        except (OSError, sqlite3.Error, KeyError, TypeError):
            return 'Review tidak selesai. Periksa konfigurasi/antrean pada VPS; jangan anggap respons ini sebagai persetujuan.\n\n' + LOCK
        finally:
            if queue:
                queue.db.close()

    # Explicit kwargs are required for transport identity in supported Hermes versions.
    def handler(command):
        def handle(raw_args, *, platform='', source=None, session_id='', session_key=''):
            return run(command, raw_args, platform=platform, source=source, session_id=session_id, session_key=session_key)
        return handle

    for command, description in (
        ('statuskonten', 'Lihat status review konten Ignidi'),
        ('preview', 'Tampilkan ulang gambar dan isi satu draf Ignidi'),
        ('bufferstatus', 'Periksa koneksi dan status draf Buffer Ignidi'),
        ('bufferdraft', 'Salin versi disetujui ke Drafts Buffer tanpa jadwal'),
        ('setuju', 'Setujui satu ID dan versi draf Ignidi'),
        ('revisi', 'Minta revisi satu ID dan versi draf Ignidi'),
        ('tolak', 'Tolak satu ID dan versi draf Ignidi'),
    ):
        ctx.register_command(command, handler=handler(command), description=description)
