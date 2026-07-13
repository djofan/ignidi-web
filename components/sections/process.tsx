import { ScrollReveal } from "@/components/scroll-reveal";

const steps = [
  {
    n: "01",
    title: "Diskusi & Riset",
    desc: "Kami gali tujuan bisnis, target pengunjung, dan referensi Anda, lalu susun ruang lingkup dan linimasa yang jelas.",
  },
  {
    n: "02",
    title: "Desain UI/UX",
    desc: "Wireframe dan desain visual disusun berdasarkan isi dan karakter bisnis Anda — bukan template yang dipaksakan.",
  },
  {
    n: "03",
    title: "Pengembangan",
    desc: "Dibangun dengan Framework Modern & powerrful component, animasi smooth yang berada di titik yang tepat, lalu diuji di berbagai perangkat.",
  },
  {
    n: "04",
    title: "Peluncuran & Perawatan",
    desc: "Website naik ke domain Anda, tim kami mendampingi masa transisi, dan tersedia paket perawatan bulanan bila dibutuhkan.",
  },
];

export function Process() {
  return (
    <section id="proses" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Proses
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Empat tahap, satu arah yang jelas.
          </h2>
        </ScrollReveal>

        <div className="mt-16 grid grid-cols-1 gap-0 md:grid-cols-4">
          {steps.map((step, i) => (
            <ScrollReveal key={step.n} delay={i * 0.1}>
              <div
                className={`relative h-full border-t border-[var(--color-line)] px-1 py-8 md:border-t-0 md:border-l md:px-7 ${
                  i === 0 ? "md:border-l-0 md:pl-0" : ""
                }`}
              >
                <span className="font-display text-sm text-[var(--color-ember)]">
                  {step.n}
                </span>
                <h3 className="font-display mt-4 text-lg text-[var(--color-paper)]">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-[var(--color-slate)]">
                  {step.desc}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
