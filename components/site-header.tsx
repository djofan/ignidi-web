"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Menu, X, Flame } from "lucide-react";

const links = [
  { href: "#layanan", label: "Layanan" },
  { href: "#proses", label: "Proses" },
  { href: "#portofolio", label: "Portofolio" },
  { href: "#harga", label: "Harga" },
  { href: "#faq", label: "FAQ" },
];

export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 z-50 w-full transition-all duration-300 ${
        scrolled
          ? "border-b border-[var(--color-line)] bg-[var(--color-ink)]/90 backdrop-blur-md"
          : "border-b border-transparent bg-transparent"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <a href="#top" className="flex items-center gap-2">
          <Flame className="h-5 w-5 text-[var(--color-ember)]" strokeWidth={2.4} />
          <span className="font-display text-lg font-semibold tracking-tight text-[var(--color-paper)]">
            IGNIDI<span className="text-[var(--color-ember)]">.</span>
            <span className="font-mono text-xs font-normal tracking-[0.2em] text-[var(--color-slate)]">
              {" "}
              WEB
            </span>
          </span>
        </a>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs uppercase tracking-[0.14em] text-[var(--color-slate)] transition-colors hover:text-[var(--color-ember)]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden md:block">
          <Button size="sm" asChild>
            <a href="#kontak">Mulai Proyek</a>
          </Button>
        </div>

        <button
          className="text-[var(--color-paper)] md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Tutup menu" : "Buka menu"}
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-[var(--color-line)] bg-[var(--color-ink)] px-6 py-6 md:hidden">
          <nav className="flex flex-col gap-5">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="font-mono text-sm uppercase tracking-[0.14em] text-[var(--color-slate)]"
              >
                {link.label}
              </a>
            ))}
            <Button size="sm" asChild>
              <a href="#kontak" onClick={() => setOpen(false)}>
                Mulai Proyek
              </a>
            </Button>
          </nav>
        </div>
      )}
    </header>
  );
}
