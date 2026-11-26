"use client";

import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Pause, Play } from 'lucide-react';

const circuits = [
  'M0 170 H140 L210 240 H320 L390 310 H500',
  'M1440 100 H1280 L1200 180 V310 L1130 380 H1040',
  'M0 680 H110 L190 600 V460 L270 380 H340',
  'M1440 720 H1280 L1190 630 H1050 L980 560',
  'M80 900 V800 L170 710 H340 L410 640',
  'M1390 900 V830 L1300 740 V530 L1220 450',
];
const sparks = Array.from({ length: 20 }, (_, index) => ({
  left: `${(index * 37 + 7) % 100}%`, top: `${(index * 23 + 11) % 100}%`,
  size: index % 4 === 0 ? 3 : 2,
}));

export function LivingBackground() {
  const root = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const animation = useRef<gsap.core.Timeline | null>(null);
  useEffect(() => {
    pausedRef.current = paused;
    animation.current?.paused(paused || document.hidden);
  }, [paused]);
  useEffect(() => {
    const element = root.current;
    if (!element) return;
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const ctx = gsap.context(() => {
        const loop = gsap.timeline();
        animation.current = loop;
        loop.to('.background-glow-one', { xPercent: 13, yPercent: 10, scale: 1.1, duration: 12, yoyo: true, repeat: -1, ease: 'sine.inOut' }, 0)
          .to('.background-glow-two', { xPercent: -12, yPercent: -14, scale: .92, duration: 12, yoyo: true, repeat: -1, ease: 'sine.inOut' }, 0);
        const currents = gsap.utils.toArray<SVGPathElement>('.circuit-current', element);
        currents.forEach((path, index) => {
          const length = path.getTotalLength();
          gsap.set(path, { strokeDasharray: `28 ${length + 28}`, strokeDashoffset: 28 });
          loop.to(path, { strokeDashoffset: -length, duration: 5 + index % 3, ease: 'none', repeat: -1, repeatDelay: 2 + index * .3 }, index * .8);
        });
        gsap.utils.toArray<HTMLElement>('.background-spark', element).forEach((spark, index) => {
          loop.fromTo(spark, { y: 65, x: 0, opacity: 0 }, { y: -110, x: index % 2 ? 28 : -22, opacity: index % 3 === 0 ? .65 : .35, duration: 9 + index % 6, ease: 'sine.inOut', repeat: -1, yoyo: true }, index * .35);
        });
        const sync = () => {
          const stop = pausedRef.current || document.hidden;
          loop.paused(stop);
          element.dataset.still = String(stop);
        };
        sync();
        document.addEventListener('visibilitychange', sync);
        return () => document.removeEventListener('visibilitychange', sync);
      }, element);
      return () => { ctx.revert(); animation.current = null; delete element.dataset.still; };
    });
    return () => media.revert();
  }, []);
  return <>
    <div ref={root} className="living-background" aria-hidden="true">
      <div className="background-glow background-glow-one" />
      <div className="background-glow background-glow-two" />
      <div className="background-grid" />
      <svg className="background-circuits" viewBox="0 0 1440 900" preserveAspectRatio="none" fill="none">
        {circuits.map(path => <path key={path} d={path} className="circuit-track" />)}
        {circuits.map(path => <path key={path} d={path} className="circuit-current" />)}
        {[[210,240],[1200,180],[190,600],[1190,630],[340,710],[1300,740]].map(([cx,cy]) => <g key={`${cx}-${cy}`}><circle cx={cx} cy={cy} r="5" className="circuit-node-ring" /><circle cx={cx} cy={cy} r="1.5" className="circuit-node" /></g>)}
      </svg>
      {sparks.map((spark,index) => <span key={index} className="background-spark" style={{left:spark.left,top:spark.top,width:spark.size,height:spark.size}} />)}
      <div className="background-shade" />
    </div>
    <button className="background-motion-toggle" type="button" aria-label={paused ? 'Lanjutkan animasi latar' : 'Jeda animasi latar'} aria-pressed={paused} onClick={() => setPaused(value => !value)} title={paused ? 'Lanjutkan animasi latar' : 'Jeda animasi latar'}>{paused ? <Play size={13} /> : <Pause size={13} />}<span>Gerak latar</span></button>
  </>;
}
