# Ignidi Content Studio — draf, preview Telegram, dan review

Target: Instagram @ignidi.labs dengan gambar; Threads @ignidi.labs dengan teks; review pemilik lewat Telegram Hermes sebelum posting.

## Status yang benar-benar tersedia

- Template JPEG code-native 1080x1350 khas Ignidi, satu contoh draf dan gambar yang sudah dirender.
- Antrean SQLite dengan validasi target, batas teks konservatif, deduplikasi draf, hash teks dan gambar. Review editorial memakai status draft/review_approved/needs_revision/superseded/rejected, riwayat keputusan, dan hubungan versi.
- Prompt riset/penulisan Hermes dan daftar referensi yang disertai sumber.
- Plugin Hermes untuk /setuju, /revisi, /tolak, /statuskonten; 39 pengujian antrean, pengiriman tiruan, identitas, dan alur revisi.

Status yang dilaporkan pemilik: Hermes terpasang, bot Telegram membalas, serta preview gambar dan kedua draf sudah diterima. Plugin review tersedia di repo dan perlu dipasang melalui Termius; belum diverifikasi aktif di VPS. Scheduler aktif, hosting gambar publik, token Meta, dan publisher belum dipasang. Tidak ada publikasi Meta dari paket ini.

## Pemasangan pertama di VPS melalui Termius

Bagian arsip untuk pemasangan pertama saja. Hermes sudah terpasang pada VPS ini; jangan mengulang installer. Gunakan user khusus tanpa akses sudo dan tanpa akses ke folder Rama. Siapkan instalasi Hermes resmi lebih dulu jika memasang di mesin baru:

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

Perintah approve adalah primitif pengujian/local operator; BUKAN jalur yang boleh dijalankan agent atau plugin editorial. Plugin tidak membaca IGNIDI_REVIEW_KEY dan tidak membuat signature publikasi. Status review_approved tidak diterima Queue.approved(). Saat publisher produksi dibangun, hanya proses reviewer yang terautentikasi dan terisolasi boleh mengakses kunci tersebut. Akun pembuat draf tidak boleh membacanya atau menjalankan proses dengan identitas reviewer. Pemisahan OS/secret merupakan syarat, bukan sesuatu yang dijamin oleh SQLite/plugin dalam user Hermes yang sama.

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

## Pengiriman preview ke Telegram (tersedia; dijalankan di VPS)

`send_review.py` membaca hanya token bot, allowlist, serta tujuan DM dari environment atau file `.env` Hermes. Ia tidak membaca auth ChatGPT atau mengambil update Telegram, sehingga tidak menjadi poller kedua yang mengganggu gateway.

- Tujuan dibatasi ke DM numerik dalam allowlist. Jika hanya satu user diizinkan, ID itu dipakai sebagai fallback. Tidak menerima wildcard, grup, atau chat di luar allowlist.
- Dry run adalah default. `--send` mengirim melalui Bot API, bukan memublikasikan ke Instagram/Threads.
- Instagram: preview foto + caption lengkap/alt text + dokumen JPEG asli. Threads: pesan teks tanpa gambar. Setiap bagian memuat ID dan digest versi.
- Sender tidak mengubah status draf/persetujuan. Pesan baru menyertakan perintah review yang dapat disalin; pemrosesnya adalah plugin di bawah. Preview lama tetap dapat direview melalui perintah yang ditampilkan /statuskonten ID.
- Tabel `review_deliveries` menyimpan status per bagian dan message_id. Bagian `sent` dilewati. Kegagalan yang definitif bisa diperbaiki dan dicoba lagi; `sending`/`uncertain` berhenti dan perlu pemeriksaan chat. Jangan menghapus status ini atau mengulang buta setelah timeout.
- Seluruh batch divalidasi sebelum kirim, termasuk hash gambar. Token tidak dicetak dan redirect HTTP ditolak. Tidak ada retry otomatis terhadap request yang hasilnya belum pasti.
- Penerima harus sudah menekan Start pada bot. Untuk profil Hermes non-default, gunakan `--env-file /path/profil/.env`. File konfigurasi dibaca sebagai pasangan key-value sederhana, bukan dieksekusi sebagai shell. Format/secret backend lain perlu konfigurasi yang sesuai.

Dari user `ignidi-hermes`, setelah mengambil paket terbaru:

```bash
cd ~/ignidi-content-source/ops/ignidi-content
npm install --omit=dev
bash prepare_review.sh
python3 send_review.py --pending --limit 2 --send
```

`prepare_review.sh` hanya menyiapkan contoh, menaruh gambar di state privat, dan dry run. Baris terakhir mengirim maksimal dua draf pending ke Telegram. Menjalankan ulang melewati bagian yang sudah terkonfirmasi terkirim.

Pengujian: `python3 -m unittest discover -s . -p 'test_*.py'` — 39 pengujian lolos dengan transport Telegram tiruan; tidak ada bot/token/jaringan sungguhan saat tes. Pengiriman dari VPS dikonfirmasi pemilik. Aktivasi plugin dan siklus revisi pada Hermes sungguhan tetap perlu diuji lewat Telegram setelah pemasangan.

## Alur persetujuan dan revisi editorial

Plugin menggunakan slash command resmi Hermes, tanpa getUpdates/poller kedua dan tanpa memodifikasi core Hermes. Identitas diambil dari SessionSource milik adapter Telegram. Source kosong, CLI, grup, user lain, atau chat di luar DM pemilik ditolak. Jika versi Hermes tidak menyediakan source pada handler, perintah gagal tertutup; jangan menggantinya dengan identitas dari teks/LLM. Rujukan API: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#register-slash-commands dan https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins#injecting-messages.

Dari akun ignidi-hermes melalui Termius:

```bash
cd ~/ignidi-content-source
git pull --ff-only
cd ops/ignidi-content
bash install_review.sh
```

Pemasang menjalankan tes, memvalidasi tujuan DM tanpa mencetak token, menyalin plugin ke ~/.hermes/plugins/ignidi-review, mengaktifkannya, mengizinkan injeksi tugas revisi ke chat yang sama, lalu me-restart hanya hermes-gateway.service milik user ini. Tidak mengubah limit RAM, service website, akun Rama, atau memasang scheduler. Plugin tidak memakai dependency Python tambahan. Bila ada prompt izin plugin, izin ini untuk tugas revisi via Hermes, bukan izin posting Meta.

Pada DM bot jalankan /statuskonten. Lalu /statuskonten ID menampilkan ID, hash SHA256 lengkap, status, nomor versi, serta perintah siap salin. Perintah harus dikirim sebagai pesan baru, bukan mengedit pesan lama:

- /setuju ID SHA256: catat persetujuan editorial tepat satu kanal dan versi, tanpa menerbitkan konten.
- /revisi ID SHA256 catatan: wajib catatan; mencabut persetujuan lama, menyimpan permintaan, dan mengantrekan satu tugas revisi ke Hermes. Pengulangan perintah yang sama tidak menggandakan tugas. Bila injeksi ditolak/terputus, catatan tetap ada dan bot memberikan pesan lanjutan manual; jangan mengira model sudah mengerjakannya.
- /tolak ID SHA256 [alasan]: cabut persetujuan dan tutup versi tersebut.
- /statuskonten [ID]: lihat status; tidak memberi persetujuan.

Keputusan hanya diterima setelah seluruh bagian preview versi tersebut tercatat terkirim ke DM pemilik (foto, caption dan dokumen asli untuk IG). ID/digest berbeda, konten atau gambar berubah, dan versi lama yang sudah digantikan ditolak. Diam, tenggat lewat, teks “oke”, instruksi referensi, hasil injeksi, dan ucapan model tidak dihitung sebagai persetujuan.

Catatan disimpan di tabel editorial_reviews: ID, digest, aksi, catatan, ID pengirim/chat, session_id, waktu UTC, dan status pengantrean revisi. Ini audit operasional pada user Hermes yang sama, bukan bukti yang tahan terhadap perubahan file oleh pemilik user tersebut. Tidak ada klaim bahwa tabel ini terisolasi dari tool shell agent.

Hermes membaca catatan menggunakan `python3 revision.py show ID_INDUK`, membuat bundle baru, merender ulang bila IG, lalu menjalankan:

```bash
python3 revision.py add ID_INDUK BUNDLE_BARU.json --image PREVIEW_BARU.jpg
# Untuk Threads, abaikan --image. Hanya kanal induk yang dimasukkan.
python3 send_review.py --draft ID_BARU --send
```

Penambahan revisi dan pencabutan versi induk berlangsung dalam satu transaksi. Revisi yang identik atau kanal berbeda ditolak; versi induk menjadi superseded, hasil baru berstatus draft dengan ID dan digest baru. Setiap hasil revisi wajib terkirim dan direview lagi. Publisher tetap tidak ada bahkan setelah /setuju; integrasi publikasi terpisah memerlukan otorisasi pemilik dan batas credential/OS yang sesuai sebelum dipasang.

Untuk menonaktifkan plugin: `hermes plugins disable ignidi-review`, lalu restart user service Hermes. Antrean dan audit tidak dihapus.
