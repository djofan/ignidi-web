"use client";

import { useRef, useState } from 'react';
import { Globe, Workflow, Camera, Plus, Check } from 'lucide-react';

const capabilities = [
  {
    name: 'Web Building', icon: Globe,
    description: 'Website dan aplikasi web yang mengikuti cara kerja bisnismu, dari halaman pertama sampai sistem yang dipakai tim setiap hari.',
    items: [
      ['Landing page', 'CAMPAIGN & LEADS'],
      ['Company profile', 'IDENTITAS BISNIS'],
      ['Katalog & toko online', 'PRODUK & PEMESANAN'],
      ['Dashboard bisnis', 'DATA & LAPORAN'],
      ['Sistem ERP custom', 'OPERASIONAL TIM'],
      ['Learning Management System', 'KELAS & EVALUASI'],
      ['Booking & reservasi', 'JADWAL & LAYANAN'],
    ],
  },
  {
    name: 'Otomasi', icon: Workflow,
    description: 'Rangkai pekerjaan berulang jadi alur yang lebih ringan. Pilih proses dan integrasi sesuai kebutuhan, lalu tentukan titik persetujuan tim.',
    items: [
      ['Pencatatan lead otomatis', 'FORM → DATABASE'],
      ['Notifikasi & pengingat', 'JADWAL & FOLLOW UP'],
      ['Sinkronisasi data', 'ANTAR TOOLS'],
      ['Rekap & laporan berkala', 'RINGKASAN OPERASIONAL'],
      ['Alur dokumen & persetujuan', 'REVIEW OLEH TIM'],
      ['Distribusi tugas', 'PIC & STATUS'],
      ['Integrasi workflow custom', 'SESUAI KEBUTUHAN'],
    ],
  },
  {
    name: 'Sosial Media', icon: Camera,
    description: 'Bangun kehadiran yang konsisten lewat strategi, visual, dan cerita yang nyambung. Lingkup produksi dan pengelolaan kita sepakati sebelum mulai.',
    items: [
      ['Audit & arah konten', 'AUDIENS & BRAND'],
      ['Content calendar', 'PILAR & JADWAL'],
      ['Desain feed & carousel', 'IDENTITAS VISUAL'],
      ['Video pendek', 'REELS & SHORT VIDEO'],
      ['Copywriting & caption', 'HOOK & PESAN'],
      ['Publikasi & interaksi', 'POSTING & KOMUNITAS'],
      ['Laporan & evaluasi', 'INSIGHT BERKALA'],
    ],
  },
];

export function Capabilities() {
  const [active, setActive] = useState(0);
  const tabs = useRef<Array<HTMLButtonElement | null>>([]);
  const current = capabilities[active];
  return (
    <div className="capabilities">
      <div className="capabilities-top mono"><span>KAPABILITAS IGNIDI LABS</span><span>{current.name}</span></div>
      <div className="capability-tabs" role="tablist" aria-label="Kapabilitas layanan">
        {capabilities.map((item, index) => (
          <button key={item.name} ref={element => { tabs.current[index] = element; }} type="button" role="tab" id={`capability-tab-${index}`} aria-selected={active === index} aria-controls={`capability-panel-${index}`} tabIndex={active === index ? 0 : -1} onClick={() => setActive(index)} onKeyDown={event => {
            let next = active;
            if (event.key === 'ArrowRight') next = (active + 1) % capabilities.length;
            else if (event.key === 'ArrowLeft') next = (active + capabilities.length - 1) % capabilities.length;
            else if (event.key === 'Home') next = 0;
            else if (event.key === 'End') next = capabilities.length - 1;
            else return;
            event.preventDefault();
            setActive(next);
            tabs.current[next]?.focus();
          }}><item.icon size={20} /><span>{item.name}</span></button>
        ))}
      </div>
      {capabilities.map((item, index) => (
        <div key={item.name} role="tabpanel" id={`capability-panel-${index}`} aria-labelledby={`capability-tab-${index}`} hidden={active !== index} tabIndex={0} className="capability-panel">
          <p>{item.description}</p>
          <ul>{item.items.map(([name, detail]) => <li key={name}><span className="capability-row-icon"><Check size={15} /></span><strong>{name}</strong><span className="mono">{detail}</span></li>)}</ul>
          <a href="#kontak" className="text-link">Diskusikan kebutuhan {item.name.toLowerCase()} <Plus size={14} /></a>
        </div>
      ))}
    </div>
  );
}
