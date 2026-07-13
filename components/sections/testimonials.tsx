import { ScrollReveal } from "@/components/scroll-reveal";
import { Card, CardContent } from "@/components/ui/card";

const testimonials = [
  {
    quote:
      "Prosesnya jelas dari awal — kami tahu persis sedang di tahap mana. Website jadi lebih cepat dari perkiraan.",
    name: "Pemilik, Warung Rasa Nusantara",
  },
  {
    quote:
      "Tim Ignidi sabar menjelaskan istilah teknis dengan bahasa yang kami mengerti. Hasilnya pun sesuai kebutuhan klinik kami.",
    name: "Pengelola, Klinik Sehat Keluarga",
  },
  {
    quote:
      "Sistem donasi jadi jauh lebih rapi. Laporan yang dulu manual sekarang otomatis dan mudah dibagikan ke donatur.",
    name: "Bendahara, Yayasan Cahaya Ilmu",
  },
];

export function Testimonials() {
  return (
    <section className="border-t border-[var(--color-line)] bg-[var(--color-ink-soft)] py-28">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Kata Klien
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Dipercaya oleh usaha yang berkembang bersama kami.
          </h2>
        </ScrollReveal>

        <div className="mt-14 grid grid-cols-1 gap-5 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <ScrollReveal key={t.name} delay={i * 0.1}>
              <Card className="h-full">
                <CardContent className="flex h-full flex-col p-8">
                  <span className="font-display text-3xl text-[var(--color-ember)]">
                    &ldquo;
                  </span>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-[var(--color-paper)]">
                    {t.quote}
                  </p>
                  <p className="mt-6 font-mono text-xs uppercase tracking-[0.1em] text-[var(--color-slate)]">
                    {t.name}
                  </p>
                </CardContent>
              </Card>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
