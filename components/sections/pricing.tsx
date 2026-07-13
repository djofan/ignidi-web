import { ScrollReveal } from "@/components/scroll-reveal";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Check } from "lucide-react";

const plans = [
  {
    name: "Starter",
    price: "Rp 2.500.000",
    note: "Cocok untuk UMKM & profil usaha",
    features: [
      "1–3 halaman (landing page)",
      "Desain khusus, bukan template",
      "Optimasi kecepatan & SEO dasar",
      "Domain & hosting dibantu setup",
    ],
    highlighted: false,
  },
  {
    name: "Bisnis",
    price: "Rp 6.500.000",
    note: "Untuk company profile & toko online",
    features: [
      "5–8 halaman + animasi GSAP",
      "Integrasi form, peta, atau katalog",
      "Panel konten yang mudah diedit sendiri",
      "3 bulan pendampingan pasca-luncur",
    ],
    highlighted: true,
  },
  {
    name: "Custom",
    price: "Hubungi Kami",
    note: "Sistem informasi & web app",
    features: [
      "Kebutuhan & alur kerja disesuaikan",
      "Integrasi database & sistem internal",
      "Skalabilitas untuk pertumbuhan tim",
      "Kontrak perawatan berkelanjutan",
    ],
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="harga" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Harga
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Paket transparan, tanpa biaya tersembunyi.
          </h2>
          <p className="mt-4 max-w-lg text-sm text-[var(--color-slate)]">
            Perkiraan investasi awal. Penawaran akhir menyesuaikan cakupan
            setelah sesi diskusi gratis.
          </p>
        </ScrollReveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {plans.map((plan, i) => (
            <ScrollReveal key={plan.name} delay={i * 0.1}>
              <Card
                className={`h-full ${
                  plan.highlighted
                    ? "border-[var(--color-ember)] bg-[var(--color-ink-soft)] shadow-[0_0_40px_-12px_rgba(255,90,31,0.35)]"
                    : ""
                }`}
              >
                <CardContent className="flex h-full flex-col p-8">
                  <p className="font-mono text-xs uppercase tracking-[0.14em] text-[var(--color-ember)]">
                    {plan.name}
                  </p>
                  <p className="font-display mt-3 text-2xl text-[var(--color-paper)]">
                    {plan.price}
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-slate)]">
                    {plan.note}
                  </p>

                  <ul className="mt-6 flex-1 space-y-3">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5 text-sm text-[var(--color-slate)]">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-ember)]" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    variant={plan.highlighted ? "default" : "outline"}
                    className="mt-8"
                    asChild
                  >
                    <a href="#kontak">Pilih {plan.name}</a>
                  </Button>
                </CardContent>
              </Card>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
