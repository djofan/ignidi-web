"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function Hero() {
  const sparkPathRef = useRef<SVGPathElement>(null);
  const glowRef = useRef<SVGCircleElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const path = sparkPathRef.current;
      const glow = glowRef.current;
      if (!path || !glow) return;

      const length = path.getTotalLength();
      gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
      gsap.set(glow, { opacity: 0 });

      const tl = gsap.timeline({ defaults: { ease: "power2.out" } });

      tl.to(".ignidi-eyebrow", { opacity: 1, y: 0, duration: 0.5 })
        .to(
          ".ignidi-headline-line",
          { opacity: 1, y: 0, duration: 0.7, stagger: 0.08 },
          "-=0.25"
        )
        .to(
          path,
          { strokeDashoffset: 0, duration: 1.1, ease: "power1.inOut" },
          "-=0.35"
        )
        .to(
          glow,
          {
            opacity: 1,
            duration: 0.15,
            onStart: () => {
              // move ember glow along the path end point
              const point = path.getPointAtLength(length);
              gsap.set(glow, { attr: { cx: point.x, cy: point.y } });
            },
          },
          "-=0.15"
        )
        .to(glow, { opacity: 0.55, duration: 1.4, repeat: -1, yoyo: true, ease: "sine.inOut" })
        .to(
          ".ignidi-sub",
          { opacity: 1, y: 0, duration: 0.6 },
          "-=1.3"
        )
        .to(
          ".ignidi-cta",
          { opacity: 1, y: 0, duration: 0.6, stagger: 0.1 },
          "-=0.4"
        )
        .to(
          ".ignidi-meta",
          { opacity: 1, duration: 0.6 },
          "-=0.3"
        );
    }, rootRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      id="top"
      ref={rootRef}
      className="bg-ignidi-grid relative flex min-h-[100svh] flex-col justify-center overflow-hidden pt-28 pb-20"
    >
      <div className="mx-auto w-full max-w-6xl px-6">
        <p className="ignidi-eyebrow mb-6 translate-y-3 font-mono text-xs uppercase tracking-[0.28em] text-[var(--color-ember)] opacity-0">
          Software House · Clean · Modern
        </p>

        <h1 className="font-display max-w-4xl text-[2.6rem] font-semibold leading-[1.05] tracking-tight text-[var(--color-paper)] sm:text-6xl md:text-7xl">
          <span className="ignidi-headline-line block translate-y-6 opacity-0">
            Website yang menyala,
          </span>
          <span className="ignidi-headline-line block translate-y-6 opacity-0">
            bisnis yang{" "}
            <span className="text-gradient-ember">bergerak.</span>
          </span>
        </h1>

        {/* Signature ignition line: a spark trail drawn on load */}
        <div className="relative mt-8 h-10 w-full max-w-2xl">
          <svg
            viewBox="0 0 640 60"
            fill="none"
            className="h-full w-full overflow-visible"
            preserveAspectRatio="none"
          >
            <path
              ref={sparkPathRef}
              d="M2 46 C 90 46, 120 10, 210 22 S 340 52, 420 18 S 560 8, 636 30"
              stroke="url(#emberGradient)"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <circle ref={glowRef} r="6" fill="var(--color-spark)" filter="url(#emberBlur)" />
            <defs>
              <linearGradient id="emberGradient" x1="0" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#C1121F" />
                <stop offset="55%" stopColor="#FF5A1F" />
                <stop offset="100%" stopColor="#FFC84A" />
              </linearGradient>
              <filter id="emberBlur" x="-200%" y="-200%" width="500%" height="500%">
                <feGaussianBlur stdDeviation="4" />
              </filter>
            </defs>
          </svg>
        </div>

        <p className="ignidi-sub mt-6 max-w-xl translate-y-4 text-base leading-relaxed text-[var(--color-slate)] opacity-0 sm:text-lg">
          Ignidi Web merancang dan membangun website untuk UMKM, lembaga,
          dan startup — dari landing page yang meyakinkan sampai sistem
          custom yang menopang operasional harian. Dibangun dengan framework modern dan tampilan yang clean.
        </p>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Button size="lg" className="ignidi-cta translate-y-4 opacity-0" asChild>
            <a href="#kontak">
              Mulai Proyek Anda <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
          <Button size="lg" variant="outline" className="ignidi-cta translate-y-4 opacity-0" asChild>
            <a href="#portofolio">Lihat Portofolio</a>
          </Button>
        </div>

        <div className="ignidi-meta mt-16 flex flex-wrap items-center gap-x-10 gap-y-3 border-t border-[var(--color-line)] pt-6 opacity-0">
          <span className="font-mono text-xs uppercase tracking-[0.14em] text-[var(--color-slate)]">
            Designed to be
          </span>
          <span className="font-display text-sm text-[var(--color-paper)]">Precise</span>
          <span className="font-display text-sm text-[var(--color-paper)]">Fast</span>
          <span className="font-display text-sm text-[var(--color-paper)]">Clean</span>
          <span className="font-display text-sm text-[var(--color-paper)]">Modern</span>
        </div>
      </div>
    </section>
  );
}
