import { SiteHeader } from "@/components/site-header";
import { Hero } from "@/components/sections/hero";
import { Services } from "@/components/sections/services";
import { Process } from "@/components/sections/process";
import { Portfolio } from "@/components/sections/portfolio";
import { Stack } from "@/components/sections/stack";
import { Pricing } from "@/components/sections/pricing";
import { Testimonials } from "@/components/sections/testimonials";
import { Faq } from "@/components/sections/faq";
import { Cta } from "@/components/sections/cta";
import { SiteFooter } from "@/components/site-footer";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <Services />
        <Process />
        <Portfolio />
        <Stack />
        <Pricing />
        <Testimonials />
        <Faq />
        <Cta />
      </main>
      <SiteFooter />
    </>
  );
}
