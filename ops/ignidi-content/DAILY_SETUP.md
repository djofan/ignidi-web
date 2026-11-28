# Konten harian Ignidi — 09.00 WIB, review sebelum Drafts Buffer

Pemilik memilih produksi setiap hari pukul 09.00 Asia/Jakarta, termasuk Sabtu/Minggu. Pada jam tersebut Hermes mulai bekerja; pengiriman preview menyusul setelah riset, penulisan dan render selesai. Waktu tiba bukan jaminan tepat menit 09.00. Ini jadwal pembuatan draf, bukan waktu posting.

Alur: satu JPEG Instagram 1080×1350 + caption dan satu tulisan Threads → DM Telegram pemilik → /setuju masing-masing ID/digest → Drafts Buffer tanpa jadwal. Revisi tetap menghasilkan versi/ID baru dan harus direview lagi. Tidak ada autoapprove, batas waktu persetujuan, atau publisher. Tidak menyetujui berarti tetap menunggu review.

## Aktifkan melalui Termius

Akses VPS di sesi ini hanya lewat Termius milik pemilik; pemasangan di VPS belum dapat diklaim selesai hanya karena file ada di GitHub. Jalankan sebagai user ignidi-hermes yang sudah digunakan untuk gateway. Tidak perlu mengulang setup API key atau mengubah akun Rama.

Jika prompt masih ubuntu, masuk dulu dengan `sudo -iu ignidi-hermes`. Lalu:

```bash
set -e
cd ~/ignidi-content-source
git pull --ff-only
cd ops/ignidi-content
python3 -m unittest discover -s . -p 'test_*.py'
python3 setup_daily.py --check
python3 setup_daily.py --time 09:00
hermes cron list
hermes cron status
```

`set -e` menghentikan blok jika pull, tes, pemeriksaan atau pemasangan gagal. Jangan melanjutkan pembuatan job manual jika ada error; periksa pesan terlebih dahulu. Dependency sharp dan logo sudah dipakai oleh preview sebelumnya. Jika renderer belum siap, pasang dependency paket dengan `npm install --omit=dev` pada folder studio.

Pemasang memeriksa DM owner, konfigurasi Buffer draft_only/auto_stage=true, logo, renderer, gateway milik user, dan dukungan CLI. Ia membuat satu job Hermes bernama **ignidi-daily-review**, memakai timezone per job Asia/Jakarta, direktori studio dan ringkasan hasil ke DM owner. Tidak mengubah timezone OS/global Hermes, tidak mengubah model/provider, tidak menambah systemd/OS crontab, tidak menjalankan LLM atau mengirim preview saat pemasangan. Job memakai provider/model Hermes yang sudah dikonfigurasi dan berjalan di gateway yang sudah dibatasi RAM-nya.

Pemasang memakai CLI resmi `hermes cron create/edit`; jobs.json hanya dibaca untuk deteksi/verifikasi, tidak ditulis mentah. Pemanggilan ulang mengedit job dengan penanda pemasang yang sama. Nama duplikat atau job yang bukan milik pemasang ditolak. Job paused tetap paused. Jika sesudah edit status enabled=false, baca alasan pause pada `hermes cron list`; jangan menganggap jadwal aktif atau mengaktifkan ulang tanpa memeriksa penyebabnya.

Jika versi Hermes belum mendukung `--timezone`, `--workdir`, atau `--deliver`, pemasang berhenti tanpa membuat job. Kirim keluaran `hermes --version` dan `hermes cron create --help` untuk menyesuaikan versi yang terpasang; jangan mengubah zona waktu global untuk mengakali perbedaan versi.

### Pemulihan pemasang awal yang salah membaca format jadwal

Versi awal pemasang pada commit bc75f96 membaca schedule.value, sedangkan format cron Hermes adalah schedule.kind=cron dan schedule.expr. Job yang benar dapat ditolak validasinya lalu di-pause oleh pemasang. Perbaikan membaca expr dan melaporkan nama kolom yang gagal tanpa mencetak prompt atau credential.

Untuk kasus ini, ambil pembaruan, jalankan `python3 setup_daily.py --time 09:00` untuk memverifikasi/memperbarui job dengan ID yang sama. Setelah berhasil dan output enabled=false, periksa `hermes cron list` untuk memastikan ini job ignidi-daily-review yang di-pause oleh pemasang tersebut, lalu `hermes cron resume ignidi-daily-review`. Periksa kembali list/status dan next_run_at; baru uji run. Jangan membuat job baru, menghapus jobs.json, atau mengubah antrean.

## Uji satu kali setelah terpasang

Pemasang mencetak **job_id** dan baris tes siap salin. Jalankan baris itu, misalnya:

```bash
hermes cron run JOB_ID_DARI_HASIL_SETUP
```

Perintah bisa melaporkan masih berjalan di background; itu belum bukti Telegram terkirim. Periksa DM bot: foto IG, caption lengkap, JPEG asli, dan tulisan Threads dengan ID serta perintah review harus ada. Respons ringkasan cron hanya menyebut tanggal, ID dan hasil, tanpa menggandakan isi konten. Gunakan `/preview ID` untuk melihat ulang dan `/revisi ID SHA256 catatan` bila perlu. Saat tes, jangan /setuju jika hanya ingin menguji pratinjau. Menjalankan tes setelah jam 09.00 membuat batch hari ini; besok tetap membuat pasangan baru. Menjalankan ulang pada tanggal yang sama memakai pasangan yang sudah tercatat.

Untuk hasil/error dan rencana berikutnya:

```bash
hermes cron list
hermes cron status
python3 daily_content.py status
```

Keberhasilan end-to-end baru terverifikasi setelah job aktif dengan next_run_at yang benar, proses uji benar-benar selesai, dan penerimaan Telegram terlihat/dikonfirmasi pemilik. Pengujian lokal memakai transport tiruan; tidak membuktikan OAuth, riset web, atau jaringan VPS selalu tersedia.

## Pembatasan pasangan harian dan pengiriman

- `daily_content.py plan` memberi tanggal WIB, pilar bergilir, direktori privat dan riwayat 60 draf terakhir. Hermes menulis materi baru berdasarkan riwayat dan sumber primer. Berita/metrik tidak boleh dikarang jika riset gagal; edukasi umum tetap boleh dengan catatan sumber kosong yang jujur.
- `submit` memvalidasi kedua kanal serta bagian Telegram, lalu menyimpan dua draf dan batch dalam satu transaksi SQLite. Primary key tanggal mencegah pasangan kedua. Isi berubah pada tanggal yang sama harus lewat revisi, bukan menimpa batch; konten identik lama ditolak. Tidak menganggap persetujuan lama berlaku untuk hari baru.
- `send` hanya mengirim ID pada batch tersebut, bukan semua pending. Mode default dry run; --send memakai sender Telegram yang sudah ada. Bagian yang sudah sent dilewati. Hasil sending/uncertain terkunci untuk pemeriksaan; tidak ada retry otomatis atau penghapusan catatan. Kanal yang sudah disetujui/ditolak/direvisi tidak dibuka ulang oleh job.
- Gambar baru memakai renderer dan logo asli yang sudah direview: gelap/oranye, grid dan sirkuit. Belum ada variasi template AI baru; isi headline/poin berganti tiap hari, format visual tetap konsisten. Threads tanpa gambar dan bukan salinan caption IG.
- Batch/gambar/bundle disimpan pada state privat. Job harian tidak memanggil Buffer/Cloudinary. Hanya handler /setuju yang meneruskan versi tepat ke Drafts Buffer. Folder dan secret tetap di user Hermes yang sama, sehingga pembatasan ini bukan isolasi keamanan terhadap shell user tersebut.

## Mengubah atau menghentikan produksi

Ubah jam dengan `python3 setup_daily.py --time 19:00`; tetap WIB dan memperbarui job yang sama. Untuk menghentikan produksi tanpa menghapus antrean, pakai `hermes cron pause JOB_ID`. Setelah memeriksa alasan dan siap melanjutkan, `hermes cron resume JOB_ID`. Tidak perlu menghapus draf Buffer/Telegram atau me-restart gateway.

Rujukan resmi yang diperiksa saat implementasi:

- https://hermes-agent.nousresearch.com/docs/user-guide/features/cron — CLI, timezone per job, workdir, delivery dan gateway scheduler.
- https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/cron.py — create/edit, job ID dan status eksekusi.
- https://developers.buffer.com/examples/create-draft-post.html — saveToDraft menyimpan sebagai draf.
