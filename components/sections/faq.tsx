import { ScrollReveal } from "@/components/scroll-reveal";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    q: "Berapa lama waktu pengerjaan website?",
    a: "Landing page biasanya 1–2 minggu, company profile 2–4 minggu, dan sistem custom menyesuaikan kompleksitas — akan disepakati di awal proyek.",
  },
  {
    q: "Apakah saya bisa mengedit konten sendiri setelah website jadi?",
    a: "Bisa. Kami menyediakan panel pengelolaan konten sederhana atau panduan pengeditan, sehingga Anda tidak bergantung pada developer untuk perubahan kecil.",
  },
  {
    q: "Apakah harga sudah termasuk domain dan hosting?",
    a: "Biaya domain dan hosting terpisah dari paket pengembangan, namun kami membantu proses pembelian dan pengaturannya hingga website tayang.",
  },
  {
    q: "Bagaimana jika saya butuh perubahan setelah website diluncurkan?",
    a: "Tersedia paket perawatan bulanan untuk pembaruan konten, perbaikan, dan penyesuaian kecil. Perubahan besar dihitung sebagai proyek tambahan.",
  },
  {
    q: "Apakah Ignidi Web bisa membangun sistem di luar website biasa?",
    a: "Bisa. Selama kebutuhannya jelas — dashboard internal, sistem informasi, atau integrasi dengan layanan lain — kami petakan dulu kebutuhannya sebelum estimasi.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-3xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            FAQ
          </p>
          <h2 className="font-display mt-4 text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Pertanyaan yang sering ditanyakan.
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={0.1}>
          <Accordion type="single" collapsible className="mt-10">
            {faqs.map((f) => (
              <AccordionItem key={f.q} value={f.q}>
                <AccordionTrigger>{f.q}</AccordionTrigger>
                <AccordionContent>{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>
      </div>
    </section>
  );
}
