import { ScrollReveal } from "@/components/scroll-reveal";

const stack = [
  {
    name: "Next.js",
    note: "Rendering cepat & SEO ramah mesin pencari.",
  },
  {
    name: "shadcn/ui",
    note: "Komponen konsisten, mudah dirawat jangka panjang.",
  },
  {
    name: "GSAP",
    note: "Animasi halus yang membantu, bukan mengganggu.",
  },
  {
    name: "Tailwind CSS",
    note: "Tampilan presisi di semua ukuran layar.",
  },
];

export function Stack() {
  return (
    <section className="border-t border-[var(--color-line)] bg-[var(--color-ink-soft)] py-24">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Fondasi Teknis
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Dibangun dengan modern tech stack.
          </h2>
        </ScrollReveal>

        <div className="mt-12 grid grid-cols-2 gap-8 sm:grid-cols-4">
          {stack.map((s, i) => (
            <ScrollReveal key={s.name} delay={i * 0.08}>
              <div className="border-l border-[var(--color-line)] pl-4">
                <p className="font-display text-lg text-[var(--color-paper)]">
                  {s.name}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-[var(--color-slate)]">
                  {s.note}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
