"use client";
import {useState} from 'react';
import {projects} from '@/lib/projects';
export function ShowcaseDemo({project:p}:{project:typeof projects[number]}){
 const[selected,setSelected]=useState<string[]>([]);
 return <section id="koleksi" className="demo-catalog"><h2>{p.color==='clinic'?'Jadwal konsultasi':p.color==='foundation'?'Program dukungan':'Pilihan untuk kamu'}</h2><div className="catalog-grid">{p.items.map((item,i)=><article key={item}><div className={'catalog-art object-'+i} aria-hidden="true">{p.color==='clinic'?'✚':p.color==='foundation'?'☀':p.color==='craft'?'▧':'✳'}</div><h3>{item}</h3><p>{p.prices[i]}</p><button className="button small" aria-pressed={selected.includes(item)} onClick={()=>setSelected(selected.includes(item)?selected.filter(x=>x!==item):[...selected,item])}>{selected.includes(item)?'Batalkan pilihan':p.color==='clinic'?'Pilih jadwal':'Pilih'}</button></article>)}</div><div className="demo-selection" role="status"><strong>{selected.length?'Pilihan kamu: '+selected.join(', '):'Belum ada pilihan.'}</strong><p>Simulasi portofolio. Tidak ada pesanan, janji konsultasi, pembayaran, atau donasi yang dikirim.</p></div></section>;
}
