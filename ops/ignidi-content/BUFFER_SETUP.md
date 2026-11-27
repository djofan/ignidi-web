# Buffer + Telegram Ignidi — DRAFT ONLY

Kode handoff tersedia di repo. Koneksi Buffer/Cloudinary di VPS belum terverifikasi. Tidak ada jadwal, cron publikasi, pemanggilan publishPostNow, atau pengubahan draf menjadi scheduled. User meminta belum posting; semua handoff memakai saveToDraft=true.

## 1. Hubungkan akun sosial pada Buffer

Masuk ke https://publish.buffer.com/settings/channels memakai akun Buffer sendiri. Tambahkan Instagram dan Threads @ignidi.labs. Pastikan akun yang aktif di jendela otorisasi memang Ignidi; jangan memilih channel lain.

Instagram perlu akun Business/Creator untuk publikasi otomatis di tahap berikutnya. Saat ini cukup menyambungkan channel; jangan membuat posting atau memasukkan konten ke Queue. Untuk Threads, akun yang aktif dalam sesi Meta menentukan akun yang tersambung. Setelah selesai, kedua channel harus terlihat di Buffer dan tidak terputus.

Sumber resmi:
- https://support.buffer.com/en-us/articles/using-instagram-with-buffer-YSjg2dXFV8
- https://support.buffer.com/en-us/articles/using-threads-with-buffer-HN9ZUFnVZv

## 2. API key Buffer dan Cloudinary

Pada https://publish.buffer.com/settings/api buat API key untuk integrasi milik sendiri. Jangan memasukkan key ke Telegram, chat Codex, Git, atau argumen shell. API key Buffer dapat mengakses organisasi/channel milik akun; ia bukan credential yang secara intrinsik terbatas ke draf. Pembatasan draft_only ada pada kode integrasi ini, dan target diverifikasi sebelum handoff.

Buat akun Cloudinary di https://cloudinary.com jika belum ada. Di Cloudinary Console, pilih product environment yang akan dipakai Ignidi, lalu buka Settings > API Keys untuk mencatat cloud name, API key dan API secret. Masukkan langsung ke prompt tersembunyi pada langkah berikutnya, bukan ke chat. Tidak perlu membuat unsigned upload preset atau mengubah seluruh media menjadi publik. Hanya JPEG versi yang sudah disetujui yang diunggah lewat signed upload, dengan public_id ignidi-labs/SHA256 dan overwrite=false.

Sumber resmi:
- https://developers.buffer.com/guides/authentication.html
- https://developers.buffer.com/guides/hosting-media.html
- https://cloudinary.com/documentation/upload_images
- https://cloudinary.com/documentation/authentication_signatures

## 3. Pasang pada VPS melalui Termius

Jalankan sebagai user ignidi-hermes yang sudah ada, bukan Rama/root. Jika masih berada pada prompt ubuntu, masuk lebih dulu dengan sudo -iu ignidi-hermes.

```bash
cd ~/ignidi-content-source
git pull --ff-only
cd ops/ignidi-content
bash install_review.sh
python3 setup_buffer.py
```

Installer memperbarui hanya plugin dan user service Hermes yang sama; limit RAM tidak berubah. Setup meminta API key Buffer, membaca organisasi/channel, memilih hanya Instagram/Threads @ignidi.labs yang tersambung, lalu meminta credential Cloudinary. Semua credential disimpan di ~/.local/state/ignidi-content/buffer-config.json (mode 600), mengikuti IGNIDI_CONTENT_STATE jika diubah. Tidak perlu menyalin credential ke .hermes/.env. File dibaca saat command berjalan, sehingga setelah setup tidak perlu restart tambahan.

Setup tidak membuat draf Buffer, mengunggah gambar, menjadwalkan, atau memosting. Pemeriksaan credential Cloudinary baru terjadi pada handoff JPEG pertama. Jangan menyimpulkan Cloudinary sudah bekerja hanya dari pesan config tersimpan.

## 4. Uji melalui Telegram

```text
/bufferstatus
/bufferdraft ID_DRAF_THREADS_YANG_SUDAH_DISETUJUI
/bufferstatus ID_DRAF_THREADS_YANG_SUDAH_DISETUJUI
/bufferdraft ID_DRAF_IG_YANG_SUDAH_DISETUJUI
/bufferstatus ID_DRAF_IG_YANG_SUDAH_DISETUJUI
```

Ganti ID dengan ID dari /statuskonten. Tidak perlu menyetujui ulang draf yang masih berstatus review_approved untuk digest yang sama. Handler hanya menerima DM pemilik; CLI, grup dan identitas kosong ditolak.

Harapan hasil: bot memberi ID Buffer, status remote draft dan tidak ada dueAt. Buka tab Drafts masing-masing channel di Buffer untuk memeriksa teks dan gambar. Jangan tekan Add to Queue, Schedule, atau Publish. Kode meminta saveToDraft=true secara literal; mode addToQueue tetap muncul dalam request karena schema Buffer mensyaratkan mode, tetapi flag saveToDraft=true menyimpan ke Drafts dan mencegah penjadwalan. Bila respons tidak draft/tanpa dueAt atau konten/media berbeda, integrasi berhenti dengan status uncertain.

Sumber jaminan draf dari Buffer: https://developers.buffer.com/examples/create-draft-post.html.

## 5. Perilaku review setelah setup

- /preview ID dan /statuskonten tetap seperti sebelumnya.
- /setuju ID SHA256 menyimpan keputusan editorial lebih dulu. Setelah config ada dan auto_stage=true, hanya versi tersebut disalin ke Drafts Buffer. Jika handoff gagal, keputusan tetap tersimpan dan bot memberi /bufferstatus ID.
- /bufferdraft ID menangani persetujuan yang sudah ada sebelum integrasi. Hanya satu versi yang disalin, bukan kedua platform sekaligus.
- /bufferstatus memeriksa kedua channel. /bufferstatus ID membaca status handoff dan status Buffer terkini bila ID remote diketahui; tidak membuat atau menjadwalkan posting.
- /revisi atau /tolak mencabut izin lokal untuk handoff berikutnya. Draf yang sudah tersalin ke Buffer tetap berada di sana sebagai draf lama; tidak dihapus/diubah otomatis. Statusnya diberi peringatan jangan dijadwalkan. Hasil revisi mendapat ID/digest baru dan perlu review baru sebelum handoff.
- Pengulangan versi yang terkonfirmasi tersimpan tidak membuat salinan baru; draf remote dibaca ulang dan harus tetap identik serta tidak terjadwal.
- JPEG diunduh dari Cloudinary sebelum dipakai dan SHA256-nya wajib sama dengan JPEG review. Caption/Threads dikirim persis dari antrean; tidak ditambahi penanda, hashtag, atau teks otomatis. Alt text ikut dikirim. Tidak ada modifikasi logo.

## Kegagalan dan rekonsiliasi

buffer_exports menyimpan ID/digest, organisasi, channel, status, URL media dan ID Buffer. buffer_assets mencatat URL Cloudinary per cloud name dan hash. Kegagalan sebelum mutasi atau penolakan definitif dapat dicoba lagi secara eksplisit setelah diperbaiki. sending/uncertain/preparing setelah crash tidak dikirim ulang otomatis.

Jika Buffer mungkin sudah menerima request tetapi hasilnya tidak diketahui, periksa Drafts Buffer. Ambil ID post yang benar, lalu operator dapat menjalankan:

```bash
python3 buffer_drafts.py reconcile ID_LOKAL ID_BUFFER
```

Perintah hanya membaca remote dan menautkan bukti lokal jika channel, teks, URL media, status draft dan ketiadaan jadwal semuanya cocok dengan versi disetujui. Jika tidak ada remote draft yang dapat diidentifikasi, hentikan dan lakukan pemeriksaan; jangan menghapus status uncertain agar bisa mencoba ulang secara buta.

CLI stage default hanya dry run tanpa request jaringan; --send-draft diperlukan untuk handoff nyata. Tidak ada flag untuk publish atau schedule:

```bash
python3 buffer_drafts.py stage ID
python3 buffer_drafts.py stage ID --send-draft
python3 buffer_drafts.py check ID
```

## Batas yang tetap berlaku

Config, SQLite dan plugin masih berada pada user Hermes yang sama. Ini integrasi draf dengan pemeriksaan identitas/versi, bukan isolasi credential terhadap proses shell user tersebut. Primitif HMAC Queue.approved() dan kunci reviewer produksi tidak digunakan atau dibuat oleh integrasi ini. Publikasi otomatis kelak membutuhkan otorisasi pemilik serta batas credential/OS yang sesuai, dan bukan bagian tahap ini.

Tidak mengubah proses, user, RAM, atau direktori Rama. Tidak menjalankan layanan baru atau memasang dependency Python tambahan. Gambar Cloudinary menjadi publik untuk dibaca Buffer hanya ketika handoff IG yang disetujui diminta; folder state dan credential tetap privat. Tidak menghapus gambar Cloudinary secara otomatis karena URL harus tetap stabil bila nanti dipakai.
