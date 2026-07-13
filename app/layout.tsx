import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ignidi Web — Jasa Pembuatan Website Profesional",
  description:
    "Ignidi Web menyalakan kehadiran digital bisnis Anda: landing page, company profile, sistem custom, dan e-commerce yang dibangun dengan Next.js — cepat, modern, dan siap berkembang.",
  keywords: [
    "jasa pembuatan website",
    "jasa website Indonesia",
    "landing page",
    "website UMKM",
    "Next.js developer",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="antialiased">{children}</body>
    </html>
  );
}
