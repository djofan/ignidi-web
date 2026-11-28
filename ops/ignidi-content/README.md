# Ignidi Content Studio — draf, preview Telegram, dan review

Target: Instagram @ignidi.labs dengan gambar; Threads @ignidi.labs dengan teks; review pemilik lewat Telegram Hermes sebelum posting.

## Status yang benar-benar tersedia

- Template JPEG code-native 1080x1350 khas Ignidi, satu contoh draf dan gambar yang sudah dirender.
- Antrean SQLite dengan validasi target, batas teks konservatif, deduplikasi draf, hash teks dan gambar. Review editorial memakai status draft/review_approved/needs_revision/superseded/rejected, riwayat keputusan, dan hubungan versi.
- Prompt riset/penulisan Hermes dan daftar referensi yang disertai sumber.
- Plugin Hermes untuk /preview, /setuju, /revisi, /tolak, /statuskonten, /bufferdraft, /bufferstatus; 127 pengujian antrean, pengiriman tiruan, identitas, revisi/preview, handoff Buffer, konfigurasi Cloudinary, batch harian dan pemasang jadwal.
- Integrasi Drafts Buffer dan hosting JPEG Cloudinary, setup interaktif tanpa menaruh secret di Git/chat. Panduan lengkap: [BUFFER_SETUP.md](BUFFER_SETUP.md).
- Produksi harian satu gambar+caption Instagram dan satu tulisan Threads, rotasi tiga layanan, batch per tanggal WIB dan pengiriman Telegram yang memakai ID tetap. Pemasang job Hermes diperbarui untuk produksi H-12 pukul 21.00 WIB, dengan acuan posting manual 09.00 besok. Panduan: [DAILY_SETUP.md](DAILY_SETUP.md). Perubahan jam ini perlu diterapkan lewat Termius pada job yang sama.

Status 28 November 2026: kedua draf sampel terlihat sesuai di Buffer tanpa jadwal; pemilik kemudian melaporkan keduanya diposting manual. Preview batch harian sudah diterima di Telegram. Pemilik mengirim status gateway aktif, heartbeat 24 detik dan satu job produksi 09.00 WIB, sehingga jadwal awal terverifikasi. Pilihan terbaru adalah H-12 jam: produksi 21.00 WIB untuk acuan posting MANUAL 09.00 besok. Kode, label tanggal review dan pemasang job yang sama sudah disiapkan; perubahan jam/prompt/plugin belum diklaim terpasang di VPS sampai pemilik menjalankan pembaruan dan mengirim status terbaru. Tidak ada publisher; persetujuan hanya meneruskan ke Drafts Buffer dengan saveToDraft=true.

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

Pengujian: `python3 -m unittest discover -s . -p 'test_*.py'` — 127 pengujian lolos dengan transport Telegram, Buffer dan Cloudinary tiruan; tidak ada credential atau jaringan sungguhan saat tes. Uji tambahan menjalankan renderer JPEG dan CLI revisi sungguhan. Pengujian Buffer mencakup flag draf yang konstan, teks melalui variables, persetujuan pemilik/digest, target organisasi/channel, draf tanpa jadwal, gambar exact-hash, deduplikasi, revokasi, hasil tak pasti, rekonsiliasi read-only, migrasi schema lama dan pencatatan error tanpa membocorkan credential. Perbaikan Cloudinary diuji mempertahankan key/channel Buffer dan draf, menolak URL/email sebagai cloud name, serta tidak melakukan request Buffer atau mencetak secret. Batch harian diuji menyimpan kedua kanal secara atomik, menolak pasangan kedua/duplikat lama, tidak mengubah keputusan, dan berhenti pada hasil Telegram tak pasti. Pemasang memakai CLI tiruan untuk memeriksa timezone, pembaruan job yang sama, job paused, dan penolakan konflik. Keluaran model diwakili contoh yang terkontrol; tes ini bukan bukti jadwal harian/OAuth/jaringan VPS sudah berjalan. Kedua handoff sampel kini terlihat berhasil di browser sebagai draf tanpa jadwal.

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

- /preview ID: tampilkan ulang gambar/caption/alt text/JPEG asli untuk Instagram, atau teks untuk Threads. Tidak perlu SHA256. Setiap permintaan eksplisit membuat kiriman baru meskipun preview sebelumnya sudah terkirim. Status draf, keputusan, signature, serta catatan pengiriman awal tidak diubah. Status saat permintaan ditampilkan pada pesan; versi superseded diberi penanda VERSI LAMA dan tidak diberi perintah persetujuan. Pemilik tetap bisa melihat versi ditolak atau disetujui tanpa membukanya kembali untuk review.
- /setuju ID SHA256: catat persetujuan editorial tepat satu kanal dan versi, tanpa menerbitkan konten.
- /revisi ID SHA256 catatan: wajib catatan; mencabut persetujuan lama, menyimpan permintaan, dan mengantrekan satu tugas revisi ke Hermes. Pengulangan perintah yang sama tidak menggandakan tugas. Bila injeksi ditolak/terputus, catatan tetap ada dan bot memberikan pesan lanjutan manual; jangan mengira model sudah mengerjakannya.
- /tolak ID SHA256 [alasan]: cabut persetujuan dan tutup versi tersebut.
- /statuskonten [ID]: lihat status; tidak memberi persetujuan.
- /bufferdraft ID: salin versi yang sudah disetujui pemilik ke Drafts Buffer, tidak dijadwalkan/diposting.
- /bufferstatus [ID]: periksa koneksi kedua channel atau status handoff/remote draft. Lihat BUFFER_SETUP.md untuk pemasangan dan batasnya.

Keputusan hanya diterima setelah seluruh bagian preview versi tersebut tercatat terkirim ke DM pemilik (foto, caption dan dokumen asli untuk IG). Bukti dapat berasal dari pengiriman awal, atau satu permintaan /preview yang lengkap. Bagian parsial dari beberapa permintaan tidak digabungkan menjadi bukti lengkap. ID/digest berbeda, konten atau gambar berubah, dan versi lama yang sudah digantikan ditolak. Diam, tenggat lewat, teks “oke”, instruksi referensi, hasil injeksi, dan ucapan model tidak dihitung sebagai persetujuan.

Pengiriman ulang /preview dicatat terpisah pada preview_deliveries dengan request_id, ID/digest draf, chat_id, bagian, message_id, status, dan waktu UTC. Foto/teks diverifikasi serta seluruh batas pesan diperiksa sebelum request pertama. Jika request gagal/timeout, hentikan pengiriman sisa bagian dan tampilkan pesan kegagalan; tidak ada pengulangan otomatis. Periksa chat sebelum meminta /preview lagi karena hasil timeout mungkin sudah diterima. Pengiriman awal tetap mempunyai perlindungan deduplikasi sendiri. /preview hanya mengirim ke DM pemilik, tidak menginjeksi tugas LLM dan tidak mempunyai jalur publikasi Meta.

Catatan disimpan di tabel editorial_reviews: ID, digest, aksi, catatan, ID pengirim/chat, session_id, waktu UTC, dan status pengantrean revisi. Ini audit operasional pada user Hermes yang sama, bukan bukti yang tahan terhadap perubahan file oleh pemilik user tersebut. Tidak ada klaim bahwa tabel ini terisolasi dari tool shell agent.

Hermes membaca catatan menggunakan `python3 revision.py show ID_INDUK`, membuat bundle baru, merender ulang bila IG, lalu menjalankan:

```bash
python3 revision.py add ID_INDUK BUNDLE_BARU.json --image PREVIEW_BARU.jpg
# Untuk Threads, abaikan --image. Hanya kanal induk yang dimasukkan.
python3 send_review.py --draft ID_BARU --send
```

Penambahan revisi dan pencabutan versi induk berlangsung dalam satu transaksi. Revisi yang identik atau kanal berbeda ditolak; versi induk menjadi superseded, hasil baru berstatus draft dengan ID dan digest baru. Setiap hasil revisi wajib terkirim dan direview lagi. Publisher tetap tidak ada bahkan setelah /setuju; integrasi publikasi terpisah memerlukan otorisasi pemilik dan batas credential/OS yang sesuai sebelum dipasang.

Untuk menonaktifkan plugin: `hermes plugins disable ignidi-review`, lalu restart user service Hermes. Antrean dan audit tidak dihapus.
