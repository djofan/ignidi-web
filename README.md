# Ignidi Web

Landing page jasa pembuatan website, dibangun dengan **Next.js 16 (App Router)**,
komponen bergaya **shadcn/ui** (dibuat manual: Button, Card, Badge, Accordion),
dan animasi **GSAP** (ignition spark line di hero + scroll reveal di tiap section).

## Menjalankan di lokal

```bash
npm install
npm run dev
```

Buka http://localhost:3000

## Build produksi

```bash
npm run build
npm run start
```

## Struktur penting

- `app/page.tsx` — merangkai semua section
- `components/sections/` — Hero, Services, Process, Portfolio, Stack, Pricing, Testimonials, FAQ, CTA
- `components/ui/` — komponen dasar bergaya shadcn (button, card, badge, accordion)
- `components/scroll-reveal.tsx` — wrapper GSAP ScrollTrigger untuk animasi muncul saat discroll
- `app/globals.css` — token desain (warna ember/ignition, font Space Grotesk + Inter + JetBrains Mono)

## Kustomisasi cepat

- **Warna**: ubah variabel `--color-ember`, `--color-ink`, dll di `app/globals.css`
- **Konten**: teks layanan, harga, testimoni, dan FAQ ada langsung di masing-masing file section (array `const`)
- **Kontak**: ubah email & nomor WhatsApp di `components/sections/cta.tsx`
- **Logo**: teks "IGNIDI WEB" di `components/site-header.tsx`, memakai ikon Flame dari lucide-react

## Catatan

Font di-self-host lewat paket `@fontsource/*` (bukan Google Fonts CDN) supaya build tidak
bergantung pada koneksi eksternal. shadcn/ui registry resmi tidak sempat diakses langsung
saat pembuatan — komponen dibuat manual mengikuti pola resminya, jadi tetap kompatibel bila
suatu saat ingin `npx shadcn add ...`.
