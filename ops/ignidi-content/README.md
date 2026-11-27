# Ignidi Content Studio — persiapan lokal, belum berjalan di VPS

Target: Instagram @ignidi.labs dengan gambar; Threads @ignidi.labs dengan teks; review pemilik lewat Telegram Hermes sebelum posting.

## Status yang benar-benar tersedia

- Template JPEG code-native 1080x1350 khas Ignidi, satu contoh draf dan gambar yang sudah dirender.
- Antrean SQLite dengan status draft/approved/rejected, validasi target, batas teks konservatif, deduplikasi draf, hash teks dan gambar, serta tanda tangan HMAC persetujuan.
- Prompt riset/penulisan Hermes dan daftar referensi yang disertai sumber.
- 11 pengujian antrean/persetujuan.

Belum tersedia: instalasi Hermes di VPS, koneksi Telegram, dispatcher yang mengautentikasi persetujuan Telegram, scheduler aktif, akun/provider LLM, hosting gambar publik, token Meta, dan publisher. Tidak ada posting atau pesan Telegram yang dikirim oleh paket ini. Ini belum otomasi end-to-end.

## Pemasangan pertama di VPS melalui Termius

Hermes belum terpasang. Gunakan user khusus tanpa akses sudo dan tanpa akses ke folder Rama. Jangan menjalankan installer sebagai root atau pada akun Rama. Siapkan instalasi Hermes resmi lebih dulu:

```bash
sudo adduser --disabled-password --gecos '' ignidi-hermes
sudo -iu ignidi-hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o "$HOME/hermes-install.sh"
bash "$HOME/hermes-install.sh"
source ~/.bashrc
hermes --version
```

Jika user sudah ada, jangan membuat ulang atau mengubahnya; cek instalasi yang ada. Jika installer meminta sudo atau mengubah runtime sistem, berhenti dan periksa, jangan menambahkan user ini ke grup sudo.

Ini hanya tahap installer; belum ada cron atau gateway aktif. Model diatur melalui `hermes model` sesuai provider milik pemilik. Token provider diisi langsung di VPS, bukan dikirim ke chat. Gateway perlu service resource-limited terpisah setelah lokasi binary diketahui (usulan MemoryHigh=2G, MemoryMax=3G, bukan mengalokasikan seluruh sisa RAM).

## Menguji paket ini

Jalankan dari folder paket, bukan dari root website:

```bash
npm install
export IGNIDI_LOGO_PATH=/path/to/original/ignidi-labs.jpeg
node render.mjs samples/lead.json samples/lead-preview.jpg
python3 -m unittest discover -s . -p test_queue.py
python3 content_queue.py --state /private/path/ignidi-content add samples/lead.json --image samples/lead-preview.jpg
python3 content_queue.py --state /private/path/ignidi-content list
```

State default berada di ~/.local/state/ignidi-content. Jangan memakai public/, .next/, atau webroot. Gambar preview dapat dibuka untuk review. Sampel tidak otomatis disetujui.

Perintah approve adalah primitif pengujian/local operator; BUKAN jalur yang boleh dijalankan agent. Saat dipasang, hanya proses reviewer yang terautentikasi dan terisolasi boleh mengakses IGNIDI_REVIEW_KEY. Akun pembuat draf tidak boleh membaca kunci tersebut atau menjalankan proses dengan identitas reviewer. Pemisahan OS/secret merupakan syarat, bukan sesuatu yang dijamin oleh SQLite saja.

Approval ditandatangani untuk satu ID dan digest tepat, mengikat kanal, akun, teks, dan hash gambar. File berubah atau draf direvisi memerlukan persetujuan baru. Fungsi approved() memvalidasi signature dan file; tidak melakukan publikasi. Kebutuhan produksi tambahan: transaksi atomik untuk claim publish, izin file antar-user, audit Telegram, expiration approval, idempotency, reconciliation API, serta backup.

## Telegram

Buat bot khusus lewat @BotFather, bukan menggunakan bot milik Rama. Jangan kirim token ke chat ini atau Git. Catat Telegram user ID pemilik untuk allowlist; jangan memakai allowlist wildcard. Pemasangan gateway dan dispatcher dilanjutkan setelah versi/lokasi Hermes serta provider dipastikan.

Dokumentasi resmi:
- https://hermes-agent.nousresearch.com/docs/getting-started/installation
- https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram
- https://hermes-agent.nousresearch.com/docs/user-guide/features/cron
- https://developers.facebook.com/documentation/instagram-platform/content-publishing
- https://developers.facebook.com/documentation/threads/posts

Referensi konten berada di references.json. Acuan gaya/topik bukan izin menyalin atau klaim bahwa feed terbaru telah dibaca.
