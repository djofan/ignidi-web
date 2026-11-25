export const automationCases = [
  {
    id: 'lead', category: 'SALES & ADMIN', title: 'Lead masuk, follow-up tertata.',
    problem: 'Permintaan dari formulir mudah terlewat atau tercatat dua kali saat admin sedang sibuk.',
    outcome: 'Tim mendapat daftar tindak lanjut yang jelas tanpa mencatat ulang lead yang sama.',
    steps: ['Terima formulir', 'Periksa kontak', 'Siapkan tindak lanjut'],
    scenarios: [
      { label: 'Kontak baru', input: 'Rani · Toko Kriya · Permintaan website katalog', outputs: ['Form demo Rani diterima.', 'Kontak belum ada. Satu lead baru ditambahkan ke daftar simulasi.', 'Tugas untuk admin: hubungi Rani dan bahas kebutuhan katalog.'] },
      { label: 'Kontak sudah tercatat', input: 'Rani · Kontak dengan permintaan aktif', outputs: ['Form demo Rani diterima.', 'Kontak sudah ada. Catatan diperbarui tanpa menambah lead duplikat.', 'Tugas yang sudah ada diperbarui dengan permintaan terbaru.'] },
    ],
  },
  {
    id: 'invoice', category: 'KEUANGAN OPERASIONAL', title: 'Tagihan diingatkan pada waktunya.',
    problem: 'Admin harus mengecek satu per satu tagihan yang mendekati jatuh tempo.',
    outcome: 'Pengingat hanya disiapkan untuk tagihan yang belum lunas; tim tetap meninjau sebelum mengirim.',
    steps: ['Baca tagihan', 'Periksa pembayaran', 'Siapkan pengingat'],
    scenarios: [
      { label: 'Belum lunas', input: 'INV-DEMO-024 · Rp750.000 · Jatuh tempo besok', outputs: ['Tagihan demo Rp750.000 ditemukan.', 'Status belum lunas dan jatuh tempo H-1. Masuk daftar pengingat.', 'Draf: Halo, pengingat tagihan INV-DEMO-024 Rp750.000 jatuh tempo besok. Menunggu persetujuan admin, belum dikirim.'] },
      { label: 'Sudah lunas', input: 'INV-DEMO-024 · Rp750.000 · Sudah lunas', outputs: ['Tagihan demo Rp750.000 ditemukan.', 'Pembayaran sudah tercatat. Tagihan dikeluarkan dari daftar pengingat.', 'Tidak ada draf pengingat dibuat. Pelanggan tidak ditagih ulang.'] },
    ],
  },
  {
    id: 'stock', category: 'TOKO & GUDANG', title: 'Stok menipis, tim lebih sigap.',
    problem: 'Produk baru diketahui habis saat pesanan pelanggan masuk.',
    outcome: 'Tim bisa meninjau kebutuhan restok lebih awal, tanpa pembelian otomatis.',
    steps: ['Baca stok', 'Bandingkan batas', 'Buat rekomendasi'],
    scenarios: [
      { label: 'Di bawah batas', input: 'Kopi 250 g · Stok 4 · Batas minimum 10 · Target 20', outputs: ['Stok demo: 4 kemasan kopi.', '4 lebih kecil dari batas minimum 10. Peringatan stok rendah dibuat.', 'Rekomendasi restok: 20 − 4 = 16 kemasan. Menunggu pemeriksaan tim, belum membuat pesanan.'] },
      { label: 'Stok cukup', input: 'Kopi 250 g · Stok 15 · Batas minimum 10 · Target 20', outputs: ['Stok demo: 15 kemasan kopi.', '15 masih di atas batas minimum 10.', 'Tidak ada rekomendasi restok atau notifikasi stok rendah.'] },
    ],
  },
  {
    id: 'report', category: 'REKAP BISNIS', title: 'Tutup hari, rekap lebih rapi.',
    problem: 'Pesanan dibatalkan ikut terhitung sebagai penjualan ketika rekap dikerjakan terburu-buru.',
    outcome: 'Ringkasan memisahkan transaksi selesai dan dibatalkan sehingga mudah diperiksa tim.',
    steps: ['Kumpulkan transaksi', 'Pisahkan status', 'Susun ringkasan'],
    scenarios: [
      { label: 'Ada transaksi', input: 'Selesai: Rp125.000 + Rp80.000 · Dibatalkan: Rp50.000', outputs: ['Tiga transaksi demo dibaca dari tabel contoh.', 'Dua transaksi selesai dihitung. Satu transaksi dibatalkan dikecualikan.', 'Rekap demo: penjualan selesai Rp205.000 dari 2 transaksi; pembatalan Rp50.000 dari 1 transaksi. Bukan perhitungan laba.'] },
      { label: 'Belum ada transaksi', input: 'Tidak ada transaksi untuk hari contoh', outputs: ['Tabel demo hari ini kosong.', 'Tidak ada transaksi yang perlu dijumlahkan.', 'Rekap demo: 0 transaksi dan Rp0 penjualan. Tidak menggunakan angka hari sebelumnya.'] },
    ],
  },
  {
    id: 'learning', category: 'LEMBAGA & PENDIDIKAN', title: 'Pengingat belajar yang relevan.',
    problem: 'Pengelola kelas harus memeriksa progres peserta sebelum menyiapkan pengingat.',
    outcome: 'Peserta yang sudah selesai tidak masuk antrean pengingat; admin bisa meninjau draf untuk yang belum.',
    steps: ['Baca progres', 'Cek kelengkapan', 'Siapkan tindak lanjut'],
    scenarios: [
      { label: 'Materi belum lengkap', input: 'Peserta Demo A · 3 dari 5 materi selesai', outputs: ['Progres peserta contoh dibaca: 3 dari 5 materi.', 'Masih ada 2 materi belum selesai. Peserta masuk daftar tindak lanjut.', 'Draf: Masih ada 2 materi yang bisa kamu lanjutkan. Menunggu tinjauan admin, belum dikirim.'] },
      { label: 'Semua materi selesai', input: 'Peserta Demo A · 5 dari 5 materi selesai', outputs: ['Progres peserta contoh dibaca: 5 dari 5 materi.', 'Semua materi sudah selesai. Peserta dikeluarkan dari daftar pengingat.', 'Tidak ada pengingat dibuat. Status progres selesai dicatat pada rekap demo.'] },
    ],
  },
];
