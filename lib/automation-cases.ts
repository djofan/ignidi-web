export type AutomationValues = Record<string, string>;
export type AutomationField = {
  key: string; label: string; kind: 'text' | 'number' | 'select' | 'textarea';
  options?: { value: string; label: string }[]; min?: number; max?: number; hint?: string;
};
export type AutomationCase = {
  id: string; category: string; title: string; problem: string; outcome: string;
  trigger: string; pattern: string; source: { name: string; repo: string; docs: string };
  fields: AutomationField[]; presets: { label: string; values: AutomationValues }[];
};
const n8n = (node: string) => ({ name: 'n8n', repo: 'https://github.com/n8n-io/n8n', docs: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.${node}/` });
const pieces = { name: 'Activepieces', repo: 'https://github.com/activepieces/activepieces', docs: 'https://www.activepieces.com/docs/flows/building-flows' };
const windmill = (page: string) => ({ name: 'Windmill', repo: 'https://github.com/windmill-labs/windmill', docs: `https://www.windmill.dev/docs/flows/${page}` });
const number = (key: string, label: string, max = 1_000_000_000): AutomationField => ({ key, label, kind: 'number', min: 0, max });
const text = (key: string, label: string): AutomationField => ({ key, label, kind: 'text' });
const choice = (key: string, label: string, items: [string, string][]): AutomationField => ({ key, label, kind: 'select', options: items.map(([value, label]) => ({ value, label })) });

export const automationCases: AutomationCase[] = [
  {
    id: 'lead', category: 'SALES & ADMIN', title: 'Lead masuk, follow-up tertata.',
    problem: 'Kontak yang mengisi formulir berulang bisa tercatat ganda dan ditindaklanjuti dua kali.',
    outcome: 'Normalisasi email dan pencocokan kontak menentukan apakah lead dibuat atau diperbarui.',
    trigger: 'Formulir masuk', pattern: 'Normalize → compare → create / update', source: n8n('removeduplicates'),
    fields: [text('name', 'Nama calon pelanggan'), text('email', 'Email masuk'), text('existing', 'Email di CRM contoh (opsional)')],
    presets: [
      { label: 'Kontak baru', values: { name: 'Rani', email: 'rani@example.com', existing: 'budi@example.com' } },
      { label: 'Kontak sama, format berbeda', values: { name: 'Rani', email: ' RANI@example.com ', existing: 'rani@example.com' } },
    ],
  },
  {
    id: 'invoice', category: 'KEUANGAN OPERASIONAL', title: 'Pengingat tagihan yang tepat.',
    problem: 'Pengingat harus mempertimbangkan sisa pembayaran dan waktu jatuh tempo.',
    outcome: 'Hitung saldo dan siapkan draf hanya jika saldo masih ada dan jatuh tempo maksimal H-1.',
    trigger: 'Pengecekan harian', pattern: 'Balance → due-date condition → draft', source: n8n('if'),
    fields: [number('amount', 'Nilai tagihan (Rp)'), number('paid', 'Sudah dibayar (Rp)'), { ...number('days', 'Hari menuju jatuh tempo', 365), min: -365, hint: 'Angka negatif berarti sudah lewat jatuh tempo.' }],
    presets: [
      { label: 'Belum lunas, H-1', values: { amount: '750000', paid: '250000', days: '1' } },
      { label: 'Sudah lunas', values: { amount: '750000', paid: '750000', days: '1' } },
      { label: 'Belum waktunya', values: { amount: '750000', paid: '0', days: '7' } },
    ],
  },
  {
    id: 'stock', category: 'TOKO & GUDANG', title: 'Stok menipis, restok terukur.',
    problem: 'Angka stok perlu dibandingkan dengan batas minimum dan target persediaan.',
    outcome: 'Rekomendasi jumlah restok dihitung dari selisih target dan stok saat ini.',
    trigger: 'Perubahan stok', pattern: 'Threshold → calculate → review', source: n8n('if'),
    fields: [text('product', 'Nama produk'), number('stock', 'Stok sekarang', 100000), number('minimum', 'Batas minimum', 100000), number('target', 'Target stok', 100000)],
    presets: [
      { label: 'Perlu restok', values: { product: 'Kopi 250 g', stock: '4', minimum: '10', target: '20' } },
      { label: 'Stok cukup', values: { product: 'Kopi 250 g', stock: '15', minimum: '10', target: '20' } },
    ],
  },
  {
    id: 'report', category: 'REKAP BISNIS', title: 'Rekap penjualan tanpa tercampur.',
    problem: 'Transaksi batal atau belum dibayar tidak boleh ikut dihitung sebagai penjualan selesai.',
    outcome: 'Kelompokkan status dan hitung jumlah serta nominal per kelompok dari baris yang dimasukkan.',
    trigger: 'Penutupan harian', pattern: 'Parse → group by status → sum', source: n8n('summarize'),
    fields: [{ key: 'rows', label: 'Transaksi contoh', kind: 'textarea', hint: 'Satu baris: nominal|status. Status: selesai, batal, menunggu. Kosongkan untuk hari tanpa transaksi. Maksimal 50 baris.' }],
    presets: [
      { label: 'Transaksi campuran', values: { rows: '125000|selesai\n80000|selesai\n50000|batal\n90000|menunggu' } },
      { label: 'Tanpa transaksi', values: { rows: '' } },
      { label: 'Data perlu diperiksa', values: { rows: '125000|selesai\nabc|selesai' } },
    ],
  },
  {
    id: 'learning', category: 'LEMBAGA & PENDIDIKAN', title: 'Pengingat belajar sesuai progres.',
    problem: 'Peserta yang telah selesai atau belum menyetujui pengingat tidak perlu dihubungi.',
    outcome: 'Hitung progres dan sisa materi, lalu periksa izin komunikasi sebelum menyiapkan draf.',
    trigger: 'Jadwal evaluasi kelas', pattern: 'Progress → consent filter → draft', source: pieces,
    fields: [number('completed', 'Materi selesai', 1000), number('total', 'Jumlah materi', 1000), choice('consent', 'Izin pengingat', [['yes', 'Diizinkan'], ['no', 'Tidak diizinkan']])],
    presets: [
      { label: 'Belum selesai', values: { completed: '3', total: '5', consent: 'yes' } },
      { label: 'Sudah selesai', values: { completed: '5', total: '5', consent: 'yes' } },
      { label: 'Tanpa izin pengingat', values: { completed: '2', total: '5', consent: 'no' } },
    ],
  },
  {
    id: 'ticket', category: 'CUSTOMER SUPPORT', title: 'Tiket sampai ke tim yang tepat.',
    problem: 'Keluhan pembayaran dan masalah akses membutuhkan penanggung jawab berbeda.',
    outcome: 'Router berbasis aturan memilih tim serta target respons sesuai kategori dan urgensi.',
    trigger: 'Tiket bantuan masuk', pattern: 'Trigger → rule-based router → assign', source: pieces,
    fields: [text('subject', 'Judul tiket'), choice('category', 'Kategori', [['payment', 'Pembayaran'], ['access', 'Akses akun'], ['general', 'Pertanyaan umum']]), choice('priority', 'Urgensi', [['normal', 'Normal'], ['urgent', 'Mendesak']])],
    presets: [
      { label: 'Pembayaran mendesak', values: { subject: 'Transfer belum tercatat', category: 'payment', priority: 'urgent' } },
      { label: 'Kendala akses', values: { subject: 'Tidak bisa masuk kelas', category: 'access', priority: 'normal' } },
    ],
  },
  {
    id: 'expense', category: 'PERSETUJUAN INTERNAL', title: 'Pengeluaran melewati review.',
    problem: 'Pengajuan di atas batas otorisasi memerlukan keputusan manajer sebelum dilanjutkan.',
    outcome: 'Pengajuan di atas batas ditahan sampai ada persetujuan; keputusan ditolak menghentikan alur.',
    trigger: 'Pengajuan biaya', pattern: 'Amount condition → suspend → approval', source: windmill('flow_approval'),
    fields: [number('amount', 'Jumlah pengajuan (Rp)'), number('limit', 'Batas otorisasi admin (Rp)'), choice('decision', 'Keputusan manajer (simulasi)', [['pending', 'Belum diputuskan'], ['approved', 'Disetujui'], ['rejected', 'Ditolak']])],
    presets: [
      { label: 'Menunggu manajer', values: { amount: '2500000', limit: '1000000', decision: 'pending' } },
      { label: 'Manajer menyetujui', values: { amount: '2500000', limit: '1000000', decision: 'approved' } },
      { label: 'Pengajuan ditolak', values: { amount: '2500000', limit: '1000000', decision: 'rejected' } },
    ],
  },
  {
    id: 'order', category: 'TOKO ONLINE', title: 'Event berulang, pesanan tetap satu.',
    problem: 'Notifikasi pembayaran bisa diterima berulang dan memicu pemrosesan pesanan ganda.',
    outcome: 'Gunakan ID event sebagai kunci deduplikasi. Coba jalankan lagi ID yang sama setelah berhasil.',
    trigger: 'Event pesanan contoh', pattern: 'Validate → event deduplication → fulfill', source: n8n('removeduplicates'),
    fields: [text('eventId', 'ID event contoh'), text('orderId', 'ID pesanan'), choice('payment', 'Status pembayaran', [['paid', 'Lunas'], ['pending', 'Menunggu pembayaran']])],
    presets: [
      { label: 'Pembayaran lunas', values: { eventId: 'evt-demo-001', orderId: 'ORD-DEMO-024', payment: 'paid' } },
      { label: 'Belum dibayar', values: { eventId: 'evt-demo-002', orderId: 'ORD-DEMO-025', payment: 'pending' } },
    ],
  },
  {
    id: 'contacts', category: 'DATA & CRM', title: 'Daftar kontak bersih sebelum dipakai.',
    problem: 'Kontak dari banyak formulir sering memiliki spasi, huruf besar, atau email tidak valid.',
    outcome: 'Normalisasi, validasi format dasar email, dan singkirkan duplikat di dalam daftar.',
    trigger: 'Daftar kontak diimpor', pattern: 'Normalize → validate → deduplicate', source: n8n('removeduplicates'),
    fields: [{ key: 'emails', label: 'Daftar email contoh', kind: 'textarea', hint: 'Satu email per baris, maksimal 50 baris. Gunakan data contoh.' }],
    presets: [
      { label: 'Duplikat & format salah', values: { emails: 'RANI@example.com\nrani@example.com\n budi@example.com \nbukan-email' } },
      { label: 'Kontak unik', values: { emails: 'rani@example.com\nbudi@example.com' } },
    ],
  },
  {
    id: 'monitor', category: 'OPERASIONAL DIGITAL', title: 'Gangguan sementara, retry terukur.',
    problem: 'Kegagalan sementara perlu dicoba ulang, sedangkan penolakan akses harus langsung diperiksa.',
    outcome: 'Evaluasi respons contoh dengan batas retry dan jeda eksponensial; tidak membuat permintaan jaringan.',
    trigger: 'Pengecekan endpoint terjadwal', pattern: 'Response → retry / backoff → escalate', source: windmill('retries'),
    fields: [text('responses', 'Urutan respons contoh'), { ...number('retries', 'Maksimal retry', 4), hint: 'Respons: kode HTTP 200–599 atau timeout, pisahkan koma. Respons terakhir diulang jika contoh habis. Jeda hanya dihitung, tidak ditunggu.' }],
    presets: [
      { label: 'Pulih setelah retry', values: { responses: '503,timeout,200', retries: '3' } },
      { label: 'Gagal terus', values: { responses: '503', retries: '2' } },
      { label: 'Akses ditolak', values: { responses: '403', retries: '3' } },
    ],
  },
];
