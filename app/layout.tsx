import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
 title:'Ignidi Labs — Website, Otomasi & Sosial Media',
 description:'Studio digital di Bekasi untuk Web Building, otomasi proses bisnis, dan manajemen sosial media. Jelajahi proyek konsep dan demo Ignidi Labs.',
 keywords:['Ignidi Labs','jasa pembuatan website','otomasi bisnis','manajemen sosial media','studio digital Bekasi'],
 openGraph:{title:'Ignidi Labs — Nyalakan ide. Gerakkan bisnismu.',description:'Website, otomasi, dan sosial media dalam satu studio digital.',locale:'id_ID',type:'website'},
};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="id"><body>{children}</body></html>;}
