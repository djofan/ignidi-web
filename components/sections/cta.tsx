import { ScrollReveal } from "@/components/scroll-reveal";
import { Button } from "@/components/ui/button";
import { ArrowRight, Mail, MessageCircle } from "lucide-react";

export function Cta() {
  return (
    <section id="kontak" className="border-t border-[var(--color-line)] py-28">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <ScrollReveal>
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)]">
            Mulai Sekarang
          </p>
          <h2 className="font-display mx-auto mt-4 max-w-2xl text-3xl font-semibold leading-tight text-[var(--color-paper)] sm:text-5xl">
            Siap menyalakan website Anda?
          </h2>
          <p className="mx-auto mt-5 max-w-md text-sm leading-relaxed text-[var(--color-slate)] sm:text-base">
            Ceritakan kebutuhan Anda, kami balas dengan estimasi biaya dan
            linimasa dalam 1x24 jam kerja.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
            <Button size="lg" asChild>
              <a href="mailto:halo@ignidiweb.id">
                <Mail className="h-4 w-4" /> jofantoalfaj@gmail.com
              </a>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <a href="https://wa.me/6282113401340" target="_blank" rel="noopener noreferrer">
                <MessageCircle className="h-4 w-4" /> Chat WhatsApp
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
