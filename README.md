# Ignidi Labs

Studio digital dengan tiga layanan: Web Building, Otomasi, dan Manajemen Sosial Media.

## Menjalankan

- `npm install`
- `npm run dev`
- `npm run build` untuk validasi produksi

## Struktur

- `components/labs-home.tsx`: landing page, filter portofolio, simulasi otomasi dan contoh konten sosial media.
- `lib/projects.ts`: data empat proyek konsep.
- `app/showcase/[slug]/page.tsx`: halaman masing-masing showcase.
- `components/showcase-demo.tsx`: simulasi pemilihan menu, jadwal, produk, atau dukungan.
- `app/globals.css`: identitas gelap/oranye Ignidi dan tema showcase responsif.

Demo internal dilabeli dengan data contoh; kartu website dan akun sosial media menautkan situs eksternal. Simulasi tidak mengirim pesanan, janji konsultasi, pembayaran, donasi, atau data ke layanan luar. Kontak: https://www.instagram.com/ignidi.labs/

Folder komponen section lama dipertahankan sebagai arsip implementasi sebelumnya; landing aktif memakai LabsHome. Fokus roadmap 1–2 telah diterapkan. Integrasi otomasi eksternal, CMS, dan publikasi konten bukan bagian demo lokal ini.

Logo resmi: public/ignidi-labs.jpeg. Kontak WhatsApp: https://wa.me/6282113401340. Telepon: 0821-1340-1340.

## Showcase website aktif

Empat kartu website di landing page memakai `lib/website-showcases.ts` dan membuka tautan eksternal di tab baru:
- Solidaritas Insan Peduli: https://erp.lazsip.or.id/
- Insan Academy (LMS): https://erp.lazsip.or.id/academy
- Lazsip: https://erp.lazsip.or.id/lazsip
- Sarsip: https://erp.lazsip.or.id/sarsip

Visual kartu adalah ilustrasi, bukan screenshot situs. Empat demo lama tetap tersedia lewat URL `/showcase/...` untuk menjaga tautan lama, tetapi sudah diganti di landing page. Simulasi otomasi dan contoh sosial media tetap memakai data dummy.

## Kapabilitas dan sosial media

- `components/capabilities.tsx`: tab kapabilitas tiga layanan dengan navigasi keyboard.
- `components/social-services.tsx`: enam rincian layanan sosial media, lima tahap kerja, dan empat contoh tautan akun dari pengguna.
- Landing page mempertahankan website showcase serta demo otomasi dan konten sebelumnya. Filter sosial media memuat empat akun eksternal dan satu simulasi konten.
- Akun eksternal ditampilkan sebagai contoh tanpa klaim statistik atau hasil pengelolaan.

## Automation Lab: sepuluh kasus dengan input yang bisa diubah

- `lib/automation-cases.ts`: definisi field, preset, dan sumber pola setiap kasus.
- `lib/automation-engine.ts`: fungsi murni untuk validasi, percabangan, perhitungan, dan log hasil.
- `components/automation-examples.tsx`: form input, eksekusi, reset, log keputusan, hasil JSON yang bisa diunduh, serta tautan referensi.
- `tests/automation.test.mjs`: uji aturan dan kondisi batas. Jalankan `node --test tests/automation.test.mjs` dengan Node 22.18+ atau Node 24.

Kasus: deduplikasi lead, saldo tagihan, restok, rekap transaksi, progres belajar, routing tiket, approval pengeluaran, deduplikasi event pesanan, normalisasi kontak, serta retry endpoint dengan backoff. Jumlah filter mengikuti jumlah kasus.

Hasil dihitung dari input; tidak memakai keluaran preset statis. ID event pesanan disimpan hanya di memori kartu yang terbuka. Pergantian filter atau refresh menghapus memori; deduplikasi lintas sesi membutuhkan database dan kunci unik saat integrasi produksi.

Sumber pola yang ditinjau:

- [n8n](https://github.com/n8n-io/n8n): [Remove Duplicates](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/), [If](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/), [Summarize](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.summarize/).
- [Activepieces](https://github.com/activepieces/activepieces): [Building Flows](https://www.activepieces.com/docs/flows/building-flows), pemicu, tindakan, serta percabangan alur.
- [Windmill](https://github.com/windmill-labs/windmill): [approval](https://www.windmill.dev/docs/flows/flow_approval) dan [retry](https://www.windmill.dev/docs/flows/retries).

Kode mesin aturan ditulis untuk Ignidi, berdasarkan konsep dokumentasi. Tidak menyalin atau menjalankan engine ketiga repo, mengimpor template native, atau menyatakan afiliasi. Penyesuaian aturan kasus (batas nominal, SLA tiket, kriteria retry) adalah contoh kebijakan Ignidi, bukan default repo. Semua integrasi luar adalah rancangan penerapan, bukan koneksi aktif. Tidak ada API, akun, pesan, stok, pembayaran, atau data produksi yang diakses. Retry hanya menghitung jejak respons serta jeda contoh, tidak menjalankan jaringan atau menunggu sungguhan. Unduhan JSON berisi laporan simulasi, bukan workflow yang dapat langsung diimpor ke platform lain.
