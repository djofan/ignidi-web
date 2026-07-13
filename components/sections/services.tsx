import { ScrollReveal } from "@/components/scroll-reveal";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import {
  LayoutTemplate,
  Building2,
  ShoppingCart,
  Wrench,
  Rocket,
  Gauge,
} from "lucide-react";

const services = [
  {
    icon: LayoutTemplate,
    title: "Landing Page",
    desc: "Satu halaman yang fokus mengonversi: penawaran jelas, CTA kuat, dan copy yang bicara ke calon pelanggan Anda.",
  },
  {
    icon: Building2,
    title: "Company Profile",
    desc: "Wajah digital resmi bisnis atau lembaga Anda — profil, layanan, tim, dan kontak dalam satu tempat yang rapi.",
  },
  {
    icon: ShoppingCart,
    title: "Toko Online",
    desc: "Katalog produk, keranjang, dan pembayaran yang terintegrasi, dibangun agar mudah Anda kelola sendiri.",
  },
  {
    icon: Rocket,
    title: "Sistem & Web App Custom",
    desc: "Dashboard, sistem informasi, atau aplikasi internal yang disesuaikan dengan alur kerja bisnis Anda.",
  },
  {
    icon: Gauge,
    title: "Optimasi & SEO Teknis",
    desc: "Kecepatan muat, struktur data, dan praktik SEO teknis supaya website Anda mudah ditemukan.",
  },
  {
    icon: Wrench,
    title: "Perawatan & Support",
    desc: "Pembaruan konten, pemantauan server, dan perbaikan rutin — website tetap menyala tanpa Anda pusingkan.",
  },
];

export function Services() {
  return (
    <section id="layanan" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-6xl px-6">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Layanan
          </p>
          <h2 className="font-display mt-4 max-w-xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-4xl">
            Satu tim, mulai dari ide sampai website berjalan.
          </h2>
        </ScrollReveal>

        <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((s, i) => (
            <ScrollReveal key={s.title} delay={(i % 3) * 0.08}>
              <Card className="group h-full transition-colors hover:border-[var(--color-ember)]/50">
                <CardContent className="p-7">
                  <s.icon className="h-6 w-6 text-[var(--color-ember)] transition-transform duration-300 group-hover:-translate-y-0.5" strokeWidth={1.8} />
                  <CardTitle className="mt-5 text-[var(--color-paper)]">
                    {s.title}
                  </CardTitle>
                  <CardDescription className="mt-2.5">
                    {s.desc}
                  </CardDescription>
                </CardContent>
              </Card>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
