import { ScrollReveal } from "@/components/scroll-reveal";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight } from "lucide-react";

const projects = [
  {
    name: "Warung Rasa Nusantara",
    type: "Landing Page + Pemesanan",
    tag: "F&B",
    result: "Reservasi online naik, tanpa perlu telepon manual.",
  },
  {
    name: "Klinik Sehat Keluarga",
    type: "Company Profile + Jadwal Dokter",
    tag: "Kesehatan",
    result: "Jadwal praktik selalu terbarui, pasien tak lagi salah info.",
  },
  {
    name: "Rumah Tenun Kriya",
    type: "Toko Online",
    tag: "UMKM Kriya",
    result: "Katalog dan pembayaran jadi satu alur yang rapi.",
  },
  {
    name: "Yayasan Cahaya Ilmu",
    type: "Sistem Informasi Donasi",
    tag: "Lembaga Sosial",
    result: "Laporan donasi otomatis, transparan bagi donatur.",
  },
];

export function Portfolio() {
  return (
    <section id="portofolio" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Portofolio
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Beberapa proyek yang pernah kami nyalakan.
          </h2>
          <p className="mt-4 max-w-lg text-sm text-[var(--color-slate)]">
            Contoh kasus di bawah menggambarkan jenis proyek yang kami
            kerjakan untuk UMKM dan lembaga.
          </p>
        </ScrollReveal>

        <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-line)] sm:grid-cols-2">
          {projects.map((p, i) => (
            <ScrollReveal key={p.name} delay={(i % 2) * 0.1} className="bg-[var(--color-ink)]">
              <div className="group h-full cursor-default p-8 transition-colors hover:bg-[var(--color-ink-soft)]">
                <div className="flex items-start justify-between gap-4">
                  <Badge variant="outline">{p.tag}</Badge>
                  <ArrowUpRight className="h-4 w-4 text-[var(--color-slate)] transition-all duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[var(--color-ember)]" />
                </div>
                <h3 className="font-display mt-6 text-xl text-[var(--color-paper)]">
                  {p.name}
                </h3>
                <p className="mt-1 font-mono text-xs uppercase tracking-[0.1em] text-[var(--color-slate)]">
                  {p.type}
                </p>
                <p className="mt-4 text-sm leading-relaxed text-[var(--color-slate)]">
                  {p.result}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
