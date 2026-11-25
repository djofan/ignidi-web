import type { AutomationCase, AutomationValues } from './automation-cases';

export type RunStatus = 'success' | 'waiting' | 'skipped' | 'error';
export type RunLog = { name: string; status: RunStatus; detail: string };
export type AutomationRun = {
  status: RunStatus; summary: string; logs: RunLog[]; output: Record<string, unknown>;
};
const currency = (value: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(value);
const validEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
const normalizeEmail = (value: string) => value.trim().toLowerCase();
const lines = (value: string) => value.split(/\r?\n/).map(row => row.trim()).filter(Boolean);

/** Browser-only domain rules. No credentials, HTTP calls, timers, or external side effects. */
export function runAutomation(item: AutomationCase, values: AutomationValues, processedEvents: readonly string[] = []): AutomationRun {
  const v: AutomationValues = {};
  const errors: string[] = [];
  for (const field of item.fields) {
    const raw = values[field.key];
    v[field.key] = typeof raw === 'string' ? raw.trim() : '';
    if (v[field.key].length > 3000) errors.push(`${field.label}: maksimal 3.000 karakter.`);
    if (field.kind !== 'textarea' && field.key !== 'existing' && !v[field.key]) errors.push(`${field.label} wajib diisi.`);
    if (field.kind === 'number' && (!/^-?\d+$/.test(v[field.key]) || !Number.isSafeInteger(Number(v[field.key])) || Number(v[field.key]) < (field.min ?? 0) || Number(v[field.key]) > (field.max ?? 1_000_000_000))) {
      errors.push(`${field.label}: isi bilangan bulat antara ${field.min ?? 0} dan ${field.max ?? 1_000_000_000}.`);
    }
    if (field.kind === 'select' && !field.options?.some(option => option.value === v[field.key])) errors.push(`${field.label}: pilihan tidak valid.`);
  }
  const fail = (detail: string): AutomationRun => ({
    status: 'error', summary: detail,
    logs: [{ name: 'Pemicu contoh', status: 'success', detail: item.trigger }, { name: 'Validasi input', status: 'error', detail }, { name: 'Evaluasi aturan', status: 'skipped', detail: 'Tidak dijalankan karena input belum valid.' }, { name: 'Hasil', status: 'skipped', detail: 'Tidak ada tindakan disiapkan.' }],
    output: { action: 'blocked', reason: detail },
  });
  if (errors.length) return fail(errors.join(' '));
  const finish = (status: RunStatus, branch: string, summary: string, output: Record<string, unknown>): AutomationRun => ({
    status, summary, output,
    logs: [{ name: 'Pemicu contoh', status: 'success', detail: item.trigger }, { name: 'Validasi input', status: 'success', detail: 'Format dan batas nilai valid.' }, { name: 'Evaluasi aturan', status: 'success', detail: branch }, { name: 'Hasil', status, detail: summary }],
  });
  switch (item.id) {
    case 'lead': {
      const email = normalizeEmail(v.email);
      const existing = normalizeEmail(v.existing);
      if (!validEmail(email) || (existing && !validEmail(existing))) return fail('Gunakan format email yang valid untuk kontak masuk dan kontak CRM.');
      const duplicate = email === existing;
      return finish('success', duplicate ? 'Email setelah normalisasi cocok dengan CRM.' : 'Email belum ditemukan di CRM contoh.', `${duplicate ? 'Perbarui' : 'Buat'} lead ${v.name} (${email}); satu tugas tindak lanjut disiapkan untuk admin.`, { action: duplicate ? 'update' : 'create', name: v.name, email, newRecords: duplicate ? 0 : 1, task: 'follow_up_draft' });
    }
    case 'invoice': {
      const balance = Number(v.amount) - Number(v.paid);
      if (balance < 0) return fail('Pembayaran melebihi nilai tagihan. Periksa data sebelum membuat pengingat.');
      if (balance === 0) return finish('skipped', 'Saldo tagihan = 0.', 'Tagihan sudah lunas. Tidak ada draf pengingat dibuat.', { balance, action: 'skip_paid', draft: null });
      const days = Number(v.days);
      if (days > 1) return finish('skipped', `${days} hari lagi; aturan pengingat dimulai H-1.`, 'Belum waktunya mengingatkan. Tagihan tetap menunggu jadwal berikutnya.', { balance, days, action: 'skip_not_due', draft: null });
      const due = days < 0 ? `lewat jatuh tempo ${Math.abs(days)} hari` : days === 0 ? 'jatuh tempo hari ini' : 'jatuh tempo besok';
      const draft = `Halo, sisa tagihan ${currency(balance)} ${due}. Mohon diperiksa, terima kasih.`;
      return finish('waiting', `Saldo ${currency(balance)}; ${due}.`, 'Draf pengingat siap ditinjau admin, belum dikirim.', { balance, days, action: 'review_reminder', draft });
    }
    case 'stock': {
      const stock = Number(v.stock), minimum = Number(v.minimum), target = Number(v.target);
      if (target < minimum) return fail('Target stok tidak boleh lebih kecil dari batas minimum.');
      const low = stock < minimum;
      const quantity = low ? Math.max(0, target - stock) : 0;
      return finish(low ? 'waiting' : 'skipped', `${stock} ${low ? '<' : '≥'} ${minimum} (batas minimum).`, low ? `Rekomendasi restok ${v.product}: ${target} − ${stock} = ${quantity} unit. Menunggu review tim.` : 'Stok cukup. Tidak ada permintaan pembelian dibuat.', { product: v.product, stock, minimum, target, restock: quantity, action: low ? 'review_restock' : 'skip_sufficient' });
    }
    case 'report': {
      const rows = lines(v.rows);
      if (rows.length > 50) return fail('Maksimal 50 baris transaksi per simulasi.');
      const groups = { selesai: { count: 0, total: 0 }, batal: { count: 0, total: 0 }, menunggu: { count: 0, total: 0 } };
      for (const [index, row] of rows.entries()) {
        const parts = row.split('|').map(x => x.trim());
        if (parts.length !== 2 || !/^\d+$/.test(parts[0]) || !Number.isSafeInteger(Number(parts[0])) || Number(parts[0]) > 1_000_000_000 || !Object.hasOwn(groups, parts[1])) return fail(`Baris ${index + 1} tidak valid. Gunakan nominal bulat 0–1000000000 dan status selesai, batal, atau menunggu.`);
        const group = groups[parts[1] as keyof typeof groups];
        group.count += 1;
        group.total += Number(parts[0]);
      }
      return finish('success', `${rows.length} transaksi dikelompokkan berdasarkan status.`, `Penjualan selesai ${currency(groups.selesai.total)} dari ${groups.selesai.count} transaksi. Pembatalan dan pembayaran menunggu dipisahkan. Angka ini bukan laba.`, { sales: groups.selesai.total, transactions: rows.length, groups });
    }
    case 'learning': {
      const completed = Number(v.completed), total = Number(v.total);
      if (total < 1 || completed > total) return fail('Jumlah materi minimal 1 dan materi selesai tidak boleh melebihi jumlah materi.');
      const remaining = total - completed;
      const progress = Math.round(completed / total * 100);
      if (!remaining || v.consent === 'no') return finish('skipped', !remaining ? 'Semua materi sudah selesai.' : 'Izin pengingat tidak diberikan.', 'Tidak membuat draf pengingat untuk peserta ini.', { progress, remaining, action: !remaining ? 'skip_completed' : 'skip_no_consent', draft: null });
      return finish('waiting', `${progress}% selesai dan izin pengingat tersedia.`, 'Draf pengingat belajar siap ditinjau admin.', { progress, remaining, action: 'review_learning_reminder', draft: `Masih ada ${remaining} dari ${total} materi yang bisa kamu lanjutkan. Selamat belajar!` });
    }
    case 'ticket': {
      const team = { payment: 'Keuangan', access: 'Dukungan Teknis', general: 'Layanan Pelanggan' }[v.category];
      const responseHours = v.priority === 'urgent' ? 2 : 24;
      return finish('success', `Kategori ${v.category}; urgensi ${v.priority}. Router menggunakan aturan eksplisit, bukan AI.`, `Tiket “${v.subject}” diarahkan ke ${team}; target respons contoh ${responseHours} jam.`, { subject: v.subject, assignedTeam: team, responseHours, action: 'assignment_preview' });
    }
    case 'expense': {
      const amount = Number(v.amount), limit = Number(v.limit);
      if (amount < 1) return fail('Jumlah pengajuan harus lebih dari 0.');
      if (v.decision === 'rejected') return finish('skipped', 'Pengajuan ditolak pada keputusan contoh.', 'Alur berhenti. Tidak ada instruksi pembayaran dibuat.', { amount, action: 'rejected', paymentSent: false });
      const needsManager = amount > limit;
      if (needsManager && v.decision === 'pending') return finish('waiting', `${currency(amount)} melebihi otorisasi admin ${currency(limit)}.`, 'Tertahan di tahap approval manajer. Pilih keputusan disetujui atau ditolak untuk menguji cabang berikutnya.', { amount, action: 'await_manager', paymentSent: false });
      return finish('success', needsManager ? 'Keputusan manajer contoh: disetujui.' : 'Nominal berada dalam batas otorisasi admin.', 'Pengajuan masuk antrean administrasi. Demo tidak melakukan pembayaran.', { amount, approvedBy: needsManager ? 'manager_demo' : 'admin_policy_demo', action: 'administration_queue', paymentSent: false });
    }
    case 'order': {
      if (!/^[A-Za-z0-9_-]{1,80}$/.test(v.eventId) || !/^[A-Za-z0-9_-]{1,80}$/.test(v.orderId)) return fail('ID event dan pesanan: gunakan 1–80 huruf, angka, tanda hubung, atau garis bawah.');
      if (v.payment !== 'paid') return finish('skipped', 'Status pembayaran masih menunggu.', 'Pesanan tidak diteruskan dan ID event belum ditandai selesai.', { eventId: v.eventId, action: 'skip_unpaid' });
      if (processedEvents.includes(v.eventId)) return finish('skipped', `ID event ${v.eventId} sudah ada di memori demo.`, 'Event duplikat diabaikan. Tidak ada pemrosesan pesanan kedua.', { eventId: v.eventId, action: 'skip_duplicate' });
      return finish('success', 'Pembayaran lunas dan ID event belum diproses.', `Satu instruksi pemenuhan contoh dibuat untuk ${v.orderId}. ID event disimpan selama kartu demo ini terbuka.`, { eventId: v.eventId, orderId: v.orderId, action: 'fulfillment_preview', rememberEvent: v.eventId });
    }
    case 'contacts': {
      const rows = lines(v.emails);
      if (rows.length > 50) return fail('Maksimal 50 email per simulasi.');
      const unique = new Set<string>();
      const invalid: string[] = [];
      let duplicates = 0;
      for (const row of rows) {
        const email = normalizeEmail(row);
        if (!validEmail(email)) invalid.push(row);
        else if (unique.has(email)) duplicates++;
        else unique.add(email);
      }
      return finish('success', `${rows.length} baris dinormalisasi dan diperiksa format dasarnya.`, `${unique.size} kontak unik, ${duplicates} duplikat dibuang, ${invalid.length} baris tidak valid dipisahkan. Validasi format tidak membuktikan alamat bisa menerima email.`, { inputCount: rows.length, contacts: [...unique], duplicates, invalid, action: 'cleaned_preview' });
    }
    case 'monitor': {
      const responses = v.responses.split(',').map(x => x.trim().toLowerCase());
      if (responses.length > 10 || responses.some(x => x !== 'timeout' && (!/^\d{3}$/.test(x) || Number(x) < 200 || Number(x) > 599))) return fail('Isi maksimal 10 respons: kode HTTP 200–599 atau timeout, dipisahkan koma.');
      const retries = Number(v.retries);
      const attempts: { attempt: number; response: string; delayBeforeSeconds: number }[] = [];
      let totalDelay = 0;
      for (let index = 0; index <= retries; index++) {
        const response = responses[Math.min(index, responses.length - 1)];
        const delay = index === 0 ? 0 : 2 ** index;
        totalDelay += delay;
        attempts.push({ attempt: index + 1, response, delayBeforeSeconds: delay });
        if (response !== 'timeout' && Number(response) >= 200 && Number(response) < 300) return finish('success', `${attempts.length} percobaan contoh; total jeda terhitung ${totalDelay} detik.`, 'Endpoint contoh pulih. Tidak ada permintaan jaringan atau penantian sungguhan.', { attempts, totalDelay, action: 'healthy_preview' });
        const retryable = response === 'timeout' || response === '429' || Number(response) >= 500;
        if (!retryable) return finish('error', `HTTP ${response} tidak masuk aturan retry sementara demo.`, 'Hentikan retry dan siapkan eskalasi untuk pemeriksaan tim.', { attempts, totalDelay, action: 'escalate_nonretryable' });
      }
      return finish('error', `Batas ${retries} retry habis setelah ${attempts.length} percobaan.`, 'Gangguan belum pulih. Siapkan eskalasi; jangan mencoba tanpa batas.', { attempts, totalDelay, action: 'escalate_exhausted' });
    }
    default: return fail('Jenis otomasi tidak dikenali.');
  }
}
