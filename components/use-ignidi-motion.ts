"use client";

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

/** One scoped motion system. Forms and native scrolling retain their normal behavior. */
export function useIgnidiMotion(filter: string) {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!root.current) return;
    gsap.registerPlugin(ScrollTrigger);
    const scope = root.current;
    const media = gsap.matchMedia();
    let alive = true;
    let refreshFrame = 0;
    const refresh = () => {
      if (!alive) return;
      cancelAnimationFrame(refreshFrame);
      refreshFrame = requestAnimationFrame(() => ScrollTrigger.refresh());
    };
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const ctx = gsap.context(() => {
        const hero = gsap.timeline({ defaults: { ease: 'power3.out' } });
        hero.from('.header-inner', { y: -12, opacity: .65, duration: .55, clearProps: 'transform,opacity' })
          .from('.hero-labs .eyebrow', { y: 16, opacity: .35, duration: .6, clearProps: 'transform,opacity' }, .12)
          .from('.hero-word', { yPercent: 105, rotate: 2, duration: .95, stagger: .13, clearProps: 'transform' }, .18)
          .from('.hero-labs .lead, .hero-labs .actions, .hero-foot', { y: 22, opacity: .45, duration: .7, stagger: .1, clearProps: 'transform,opacity' }, .65)
          .from('.brand-art', { y: 30, scale: .96, opacity: .5, duration: 1.15, clearProps: 'transform,opacity' }, .28);
        gsap.to('.scroll-progress', {
          scaleX: 1, ease: 'none', scrollTrigger: { trigger: scope, start: 'top top', end: 'bottom bottom', scrub: .25, invalidateOnRefresh: true },
        });
        gsap.utils.toArray<HTMLElement>('.section-heading, .service, .capabilities, .social-deliverables article, .social-workflow-heading, .social-workflow li, .process-grid > div, .faq-section > h2, .faq-section details, .contact-section h2, .contact-bottom, .labs-footer', scope).forEach((element, index) => {
          // Already-passed content stays in place when opening an anchor directly.
          if (element.getBoundingClientRect().bottom <= 0) return;
          gsap.from(element, {
            y: 26, opacity: .7, duration: .75, delay: element.matches('.service, .social-deliverables article') ? (index % 3) * .045 : 0,
            ease: 'power3.out', clearProps: 'transform,opacity',
            scrollTrigger: { trigger: element, start: 'top 94%', once: true },
          });
        });
        gsap.from('.statement-bar svg', { rotate: -45, scale: .6, duration: 1, ease: 'back.out(1.6)', clearProps: 'transform', scrollTrigger: { trigger: '.statement-bar', start: 'top 95%', once: true } });
        gsap.from('.contact-section h2 em', { backgroundSize: '0% 2px', duration: 1.1, ease: 'power2.out', scrollTrigger: { trigger: '.contact-section', start: 'top 80%', once: true } });
      }, scope);
      return () => ctx.revert();
    });
    media.add('(prefers-reduced-motion: no-preference) and (min-width: 900px)', () => {
      const ctx = gsap.context(() => {
        gsap.fromTo('.brand-poster', { scale: 1.12, yPercent: -3 }, { yPercent: 5, ease: 'none', scrollTrigger: { trigger: '.hero-labs', start: 'top top', end: 'bottom top', scrub: 1 } });
        gsap.to('.hero-ember-one', { x: 24, y: -20, scale: 1.1, duration: 6, ease: 'sine.inOut', repeat: -1, yoyo: true });
        gsap.to('.hero-ember-two', { x: -18, y: 25, duration: 7.5, ease: 'sine.inOut', repeat: -1, yoyo: true });
        gsap.to('.hero-orbit', { rotation: 110, duration: 2, ease: 'none', scrollTrigger: { trigger: '.hero-labs', start: 'top top', end: 'bottom top', scrub: 1.2 } });
      }, scope);
      return () => ctx.revert();
    });
    media.add('(prefers-reduced-motion: no-preference) and (hover: hover) and (pointer: fine)', () => {
      const listeners: (() => void)[] = [];
      const ctx = gsap.context(() => {
        const art = scope.querySelector<HTMLElement>('.brand-motion-frame');
        if (art) {
          const x = gsap.quickTo(art, 'rotationY', { duration: .65, ease: 'power3.out' });
          const y = gsap.quickTo(art, 'rotationX', { duration: .65, ease: 'power3.out' });
          const holder = art.parentElement!;
          const move = (event: PointerEvent) => {
            const rect = holder.getBoundingClientRect();
            x((event.clientX - rect.left - rect.width / 2) / rect.width * 6);
            y(-(event.clientY - rect.top - rect.height / 2) / rect.height * 6);
          };
          const leave = () => { x(0); y(0); };
          holder.addEventListener('pointermove', move);
          holder.addEventListener('pointerleave', leave);
          listeners.push(() => { holder.removeEventListener('pointermove', move); holder.removeEventListener('pointerleave', leave); });
        }
        scope.querySelectorAll<HTMLElement>('.header-cta, .actions .button, .contact-links .button').forEach(element => {
          const x = gsap.quickTo(element, 'x', { duration: .35, ease: 'power3.out' });
          const y = gsap.quickTo(element, 'y', { duration: .35, ease: 'power3.out' });
          const move = (event: PointerEvent) => {
            const rect = element.getBoundingClientRect();
            x((event.clientX - rect.left - rect.width / 2) * .06);
            y((event.clientY - rect.top - rect.height / 2) * .08);
          };
          const leave = () => { x(0); y(0); };
          element.addEventListener('pointermove', move);
          element.addEventListener('pointerleave', leave);
          listeners.push(() => { element.removeEventListener('pointermove', move); element.removeEventListener('pointerleave', leave); });
        });
      }, scope);
      return () => { listeners.forEach(remove => remove()); ctx.revert(); };
    });
    const resize = new ResizeObserver(refresh);
    resize.observe(scope);
    document.fonts.ready.then(refresh);
    window.addEventListener('load', refresh, { once: true });
    scope.addEventListener('toggle', refresh, true);
    return () => {
      alive = false;
      resize.disconnect();
      window.removeEventListener('load', refresh);
      scope.removeEventListener('toggle', refresh, true);
      cancelAnimationFrame(refreshFrame);
      media.revert();
    };
  }, []);

  // Register new cards after portfolio filtering, without replaying the hero or losing form state.
  useEffect(() => {
    if (!root.current) return;
    const scope = root.current;
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const ctx = gsap.context(() => {
        gsap.utils.toArray<HTMLElement>('.project-grid > .project-card, .project-grid > .social-account, .project-grid > .automation-case, .automation-intro', scope).forEach((element, index) => {
          if (element.getBoundingClientRect().bottom <= 0) return;
          gsap.from(element, {
            y: 32, opacity: .75, duration: .7, delay: Math.min(index % 2 * .07, .07), ease: 'power3.out', clearProps: 'transform,opacity',
            scrollTrigger: { trigger: element, start: 'top 96%', once: true },
          });
        });
      }, scope);
      return () => ctx.revert();
    });
    const frame = requestAnimationFrame(() => ScrollTrigger.refresh());
    return () => { cancelAnimationFrame(frame); media.revert(); };
  }, [filter]);
  return root;
}
