# Konten harian Ignidi — produksi 21.00 WIB, acuan posting manual 09.00 besok

Pemilik memilih persiapan H-12 jam: mulai produksi setiap hari pukul 21.00 Asia/Jakarta, termasuk Sabtu/Minggu, untuk acuan posting manual pukul 09.00 keesokan harinya. Preview menyusul setelah riset, penulisan dan render selesai, sehingga kedatangan tepat menit 21.00 tidak dijamin. Contoh: produksi 28 November pukul 21.00 → konten bertanggal 29 November dengan acuan posting manual 09.00. Pemilik bebas menunda/menolak atau mengganti waktu posting; sistem tidak memublikasikan saat jam acuan tiba.

Alur: satu JPEG Instagram 1080×1350 + caption dan satu tulisan Threads → DM Telegram pemilik → /setuju masing-masing ID/digest → Drafts Buffer tanpa jadwal. Revisi tetap menghasilkan versi/ID baru dan harus direview lagi. Tidak ada autoapprove, batas waktu persetujuan, atau publisher. Tidak menyetujui berarti tetap menunggu review.

## Aktifkan melalui Termius

Akses VPS di sesi ini hanya lewat Termius milik pemilik; pemasangan di VPS belum dapat diklaim selesai hanya karena file ada di GitHub. Jalankan sebagai user ignidi-hermes yang sudah digunakan untuk gateway. Tidak perlu mengulang setup API key atau mengubah akun Rama.

Jika prompt masih ubuntu, masuk dulu dengan `sudo -iu ignidi-hermes`. Lalu:

```bash
set -e
cd ~/ignidi-content-source
git pull --ff-only
cd ops/ignidi-content
bash install_review.sh
python3 setup_daily.py --check
python3 setup_daily.py --time 21:00 --lead-hours 12
hermes cron list
hermes cron status
```

`set -e` menghentikan blok jika pull, tes, pemeriksaan atau pemasangan gagal. install_review.sh menjalankan tes, menyalin sender/plugin agar /preview juga menampilkan tanggal tujuan, lalu me-restart hanya gateway user ignidi-hermes. Antrean, persetujuan dan job tidak dihapus. setup_daily memperbarui ID job yang sama ke pukul 21.00 dan menambahkan konfigurasi acuan 12 jam ke prompt. Jangan membuat job kedua. Dependency sharp dan logo sudah dipakai oleh preview sebelumnya; jika renderer belum siap, jalankan npm install --omit=dev pada folder studio.

Pemasang memeriksa DM owner, konfigurasi Buffer draft_only/auto_stage=true, logo, renderer, gateway milik user, dan dukungan CLI. Ia membuat/memperbarui satu job Hermes bernama **ignidi-daily-review**, memakai timezone per job Asia/Jakarta, direktori studio dan ringkasan hasil ke DM owner. Output editorial_plan harus berisi days_ahead=1, intended_time=09:00, lead_hours=12; Schedule harus 0 21 * * *. Tidak mengubah timezone OS/global Hermes, model/provider, atau systemd/OS crontab. Setup_daily tidak menjalankan LLM, mengirim preview, atau me-restart layanan. Job memakai model/provider Hermes yang sudah dikonfigurasi dan gateway yang sudah dibatasi RAM-nya. Untuk instalasi yang sudah diverifikasi sebelumnya, hanya perubahan jam/prompt ini yang perlu diverifikasi lagi.

Pemasang memakai CLI resmi `hermes cron create/edit`; jobs.json hanya dibaca untuk deteksi/verifikasi, tidak ditulis mentah. Pemanggilan ulang mengedit job dengan penanda pemasang yang sama. Nama duplikat atau job yang bukan milik pemasang ditolak. Job paused tetap paused. Jika sesudah edit status enabled=false, baca alasan pause pada `hermes cron list`; jangan menganggap jadwal aktif atau mengaktifkan ulang tanpa memeriksa penyebabnya.

Jika versi Hermes belum mendukung `--timezone`, `--workdir`, atau `--deliver`, pemasang berhenti tanpa membuat job. Kirim keluaran `hermes --version` dan `hermes cron create --help` untuk menyesuaikan versi yang terpasang; jangan mengubah zona waktu global untuk mengakali perbedaan versi.

### Pemulihan pemasang awal yang salah membaca format jadwal

Versi awal pemasang pada commit bc75f96 membaca schedule.value, sedangkan format cron Hermes adalah schedule.kind=cron dan schedule.expr. Job yang benar dapat ditolak validasinya lalu di-pause oleh pemasang. Perbaikan membaca expr dan melaporkan nama kolom yang gagal tanpa mencetak prompt atau credential.

Untuk kasus ini, ambil pembaruan, jalankan `python3 setup_daily.py --time 21:00 --lead-hours 12` sesuai pilihan terbaru untuk memverifikasi/memperbarui job dengan ID yang sama. Setelah berhasil dan output enabled=false, periksa `hermes cron list` untuk memastikan ini job ignidi-daily-review yang di-pause oleh pemasang tersebut, lalu `hermes cron resume ignidi-daily-review`. Periksa kembali list/status dan next_run_at; baru uji run. Jangan membuat job baru, menghapus jobs.json, atau mengubah antrean.

## Uji satu kali setelah terpasang

Pemasang mencetak **job_id** dan baris tes siap salin. Jalankan baris itu, misalnya:

```bash
hermes cron run JOB_ID_DARI_HASIL_SETUP
```

Perintah bisa melaporkan masih berjalan di background; itu belum bukti Telegram terkirim. Periksa DM bot: foto IG, caption lengkap, JPEG asli, dan tulisan Threads dengan ID serta perintah review harus ada. Pesan baru menyebut "Disiapkan" dan "Untuk konten: YYYY-MM-DD · 09:00 WIB", serta acuan posting MANUAL. Caption publik tidak ditambah tanggal/jam ini. Gunakan /preview ID untuk melihat ulang, dan /revisi ID SHA256 catatan bila perlu; revisi mempertahankan acuan tanggal dan tetap memerlukan persetujuan baru. Tes manual sebelum pukul 21.00 berarti preview dikirim lebih awal satu kali. Job pukul 21.00 memakai pasangan yang sama dan melewati kiriman yang sudah terkonfirmasi, bukan membuat batch kedua. Draf hari ini yang sudah diposting tidak dipakai sebagai konten besok. Tes ini opsional; jika ingin menunggu jam produksi, jangan menjalankan cron run.

Untuk hasil/error dan rencana berikutnya:

```bash
hermes cron list
hermes cron status
python3 daily_content.py --days-ahead 1 --intended-time 09:00 status
```

Keberhasilan end-to-end baru terverifikasi setelah job aktif dengan next_run_at yang benar, proses uji benar-benar selesai, dan penerimaan Telegram terlihat/dikonfirmasi pemilik. Pengujian lokal memakai transport tiruan; tidak membuktikan OAuth, riset web, atau jaringan VPS selalu tersedia.

## Pembatasan pasangan harian dan pengiriman

- `daily_content.py --days-ahead 1 --intended-time 09:00 plan` memberi tanggal tujuan besok (day), tanggal produksi (prepared_day), pilar bergilir, direktori privat dan riwayat 60 draf terakhir. Tanpa opsi tersebut, CLI tetap mendukung mode lama hari ini untuk inspeksi/tes; job baru selalu mengirim kedua opsi. Hermes menulis materi baru berdasarkan riwayat dan sumber primer. Berita/metrik tidak boleh dikarang jika riset gagal; edukasi umum tetap boleh dengan catatan sumber kosong yang jujur.
- `submit` memvalidasi kedua kanal serta bagian Telegram, lalu menyimpan dua draf dan batch dalam satu transaksi SQLite. Primary key tanggal tujuan mencegah pasangan kedua. Data lama tetap utuh dengan day yang dulu berlaku; tidak ditulis ulang atau disetujui ulang. Perubahan tanggal/label tidak bisa menyamarkan caption/tulisan identik lama. Label rencana masuk digest versi, diwariskan ke revisi, dan hanya ditampilkan pada pesan review—bukan dueAt atau caption Buffer.
- `send` hanya mengirim ID pada batch tersebut, bukan semua pending. Mode default dry run; --send memakai sender Telegram yang sudah ada. Bagian yang sudah sent dilewati. Hasil sending/uncertain terkunci untuk pemeriksaan; tidak ada retry otomatis atau penghapusan catatan. Kanal yang sudah disetujui/ditolak/direvisi tidak dibuka ulang oleh job.
- Gambar baru memakai renderer dan logo asli yang sudah direview: gelap/oranye, grid dan sirkuit. Belum ada variasi template AI baru; isi headline/poin berganti tiap hari, format visual tetap konsisten. Threads tanpa gambar dan bukan salinan caption IG.
- Batch/gambar/bundle disimpan pada state privat. Job harian tidak memanggil Buffer/Cloudinary. Hanya handler /setuju yang meneruskan versi tepat ke Drafts Buffer. Folder dan secret tetap di user Hermes yang sama, sehingga pembatasan ini bukan isolasi keamanan terhadap shell user tersebut.

## Mengubah atau menghentikan produksi

Pilihan saat ini: `python3 setup_daily.py --time 21:00 --lead-hours 12`. Acuan posting manual dihitung 12 jam setelah waktu produksi; mengubah --time akan menggeser acuan itu juga. Untuk menghentikan produksi tanpa menghapus antrean, pakai hermes cron pause JOB_ID. Setelah memeriksa alasan dan siap melanjutkan, hermes cron resume JOB_ID. Tidak perlu menghapus draf Buffer/Telegram. Setup jam saja tidak memerlukan restart; pembaruan sender/plugin pertama kali memakai install_review.sh seperti di atas.

Rujukan resmi yang diperiksa saat implementasi:

- https://hermes-agent.nousresearch.com/docs/user-guide/features/cron — CLI, timezone per job, workdir, delivery dan gateway scheduler.
- https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/cron.py — create/edit, job ID dan status eksekusi.
- https://developers.buffer.com/examples/create-draft-post.html — saveToDraft menyimpan sebagai draf.
