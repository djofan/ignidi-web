"use client";
import Image from 'next/image';
import {BrandLogo} from '@/components/brand-logo';
import {LivingBackground} from '@/components/living-background';
import {useState} from 'react';
import {useIgnidiMotion} from '@/components/use-ignidi-motion';
import {Flame,Globe,Workflow,Camera as Instagram,MessageCircle,Phone,Plus,Menu,X} from 'lucide-react';
import {websiteShowcases} from '@/lib/website-showcases';
import {Capabilities} from '@/components/capabilities';
import {AutomationExamples} from '@/components/automation-examples';
import {automationCases} from '@/lib/automation-cases';
import {SocialServices, SocialAccountCards} from '@/components/social-services';
const ig='https://www.instagram.com/ignidi.labs/';
const whatsapp='https://wa.me/6282113401340';
const phone='tel:+6282113401340';
const services=[{icon:Globe,name:'Web Building',word:'Bangun.',text:'Rumah digital yang memperkenalkan bisnismu dengan tepat. Rapi, responsif, dan mudah dijelajahi.',tags:['Landing page','Company profile','Katalog produk']},{icon:Workflow,name:'Otomasi',word:'Hubungkan.',text:'Bereskan pekerjaan berulang. Sambungkan formulir, pencatatan, dan notifikasi dalam satu alur kerja.',tags:['Alur operasional','Integrasi tools','Rekap otomatis']},{icon:Instagram,name:'Manajemen Sosial Media',word:'Hidupkan.',text:'Bikin brand kamu hadir dengan konsisten. Dari arah konten sampai visual dan kalender publikasi.',tags:['Strategi konten','Desain feed','Content planning']}];
export function LabsHome(){
 const[menu,setMenu]=useState(false),[filter,setFilter]=useState('Semua'),[post,setPost]=useState(0);
 const motionRoot=useIgnidiMotion(filter);
 const posts=['Kenalan dengan rasa yang bikin pulang.','Di balik sepiring nasi, ada cerita.','Makan siang kamu, sudah direncanakan?'];
 return <div ref={motionRoot} className="labs-site"><LivingBackground /><div className="scroll-progress" aria-hidden="true"/><a className="skip-link" href="#utama">Lompat ke konten</a><header className="labs-header"><div className="shell header-inner"><a className="brand" href="#"><BrandLogo/><span>ignidi<small>labs</small><i>.</i></span></a><nav className={menu?'nav is-open':'nav'} aria-label="Navigasi utama">{[['Layanan','layanan'],['Portofolio','portofolio'],['Cara kerja','proses']].map(([t,id])=><a href={'#'+id} key={id} onClick={()=>setMenu(false)}>{t}</a>)}</nav><a className="button small header-cta" href="#kontak">Mulai obrolan <Plus size={16}/></a><button className="menu-toggle" aria-label={menu?'Tutup menu':'Buka menu'} aria-expanded={menu} onClick={()=>setMenu(!menu)}>{menu?<X/>:<Menu/>}</button></div></header>
 <main id="utama"><section className="hero-labs"><div className="hero-atmosphere" aria-hidden="true"><span className="hero-ember hero-ember-one"/><span className="hero-ember hero-ember-two"/><span className="hero-orbit"/></div><div className="shell hero-grid"><div><p className="eyebrow">INDEPENDENT DIGITAL STUDIO · BEKASI, ID</p><h1 aria-label="Nyalakan ide. Gerakkan bisnismu."><span className="hero-line" aria-hidden="true"><span className="hero-word">Nyalakan ide.</span></span><span className="hero-line" aria-hidden="true"><span className="hero-word">Gerakkan</span></span><span className="hero-line" aria-hidden="true"><em className="hero-word">bisnismu.</em></span></h1><p className="lead">Website yang bekerja. Proses yang lebih ringan. Konten yang punya cerita. Kami merangkainya jadi langkah berikutnya untuk bisnis kamu.</p><div className="actions"><a className="button" href="#kontak">Ceritakan idemu <Plus size={18}/></a><a className="text-link" href="#portofolio">Jelajahi portofolio</a></div><div className="hero-foot"><span>Berangkat dari ide.<br/><strong>Dibangun untuk bertumbuh.</strong></span><span className="mono">WEB / AUTO / SOCIAL</span></div></div><div className="lab-art brand-art"><div className="brand-motion-frame"><Image className="brand-poster" src="/ignidi-labs.jpeg" alt="Logo resmi Ignidi Labs dengan simbol putih dan latar kode berwarna oranye" width={1600} height={1600} sizes="(max-width: 760px) 100vw, 50vw" preload /></div></div></div></section>
 <div className="statement-bar"><div className="shell"><span className="mono">SMALL STUDIO. BIG SPARK.</span><p>Bangun kehadirannya. Ringankan kerjanya. Hidupkan ceritanya.</p><Flame size={22}/></div></div>
 <section id="layanan" className="section shell"><div className="section-heading"><div><p className="eyebrow">APA YANG KAMI KERJAKAN</p><h2>Tiga cara.<br/><em>Satu arah: maju.</em></h2></div><p>Mulai dari satu layanan, atau rangkai ketiganya jadi ekosistem digital yang nyambung dengan kebutuhan bisnismu.</p></div><div className="service-grid">{services.map(s=><article className="service" key={s.name}><s.icon size={28} strokeWidth={1.5}/><p className="mono service-name">{s.name}</p><h3>{s.word}</h3><p>{s.text}</p><ul>{s.tags.map(t=><li key={t}><Plus size={14}/>{t}</li>)}</ul><a className="text-link" href="#kontak">Bahas kebutuhanmu</a></article>)}</div><Capabilities /></section>
 <section id="portofolio" className="section portfolio-section"><div className="shell"><div className="section-heading"><div><p className="eyebrow">WEBSITES & EXPERIMENTS</p><h2>Ide jadi sesuatu<br/>yang <em>bisa kamu coba.</em></h2></div><p>Jelajahi empat website melalui tautannya masing-masing. Lihat juga empat contoh akun sosial media, serta simulasi otomasi dan konten di halaman ini.</p></div><div className="filters" aria-label="Filter portofolio">{['Semua','Website','Otomasi','Sosial Media'].map(f=><button key={f} className={filter===f?'active':''} aria-pressed={filter===f} onClick={()=>setFilter(f)}>{f}<span>{String(f==='Semua'?websiteShowcases.length+automationCases.length+5:f==='Website'?websiteShowcases.length:f==='Sosial Media'?5:automationCases.length).padStart(2,'0')}</span></button>)}</div><div className="project-grid">
 {(filter==='Semua'||filter==='Website')&&websiteShowcases.map((p,i)=>(
   <a className="project-card" href={p.url} target="_blank" rel="noopener noreferrer" key={p.url} aria-label={`Buka ${p.name} di tab baru`}>
     <div className={'project-visual '+p.color}>
       <div className="mini-browser">
         <div className="browser-bar"><span>● ● ●</span><span>{p.displayUrl}</span></div>
         <div className="mini-content">
           <div className="mini-brand">{p.name}<span>WEBSITE</span></div>
           <p className="mini-label">{p.category}</p>
           <h3>{p.title}</h3>
           <span className="mini-pill">Buka website</span>
           <div className={'project-object object-'+i} aria-hidden="true">{p.symbol}</div>
         </div>
       </div>
       <span className="demo-tag">TAUTAN WEBSITE · TAB BARU</span>
     </div>
     <div className="project-caption"><div><p className="mono">WEB BUILDING · {p.category}</p><h3>{p.name}</h3></div><Plus size={22}/></div>
     <p className="showcase-description">{p.description}</p>
     <p className="showcase-url">{p.displayUrl}</p>
   </a>
 ))}
 {(filter==='Semua'||filter==='Otomasi')&&<AutomationExamples />}
 {(filter==='Semua'||filter==='Sosial Media')&&<SocialAccountCards />}
 {(filter==='Semua'||filter==='Sosial Media')&&<article className="project-card"><div className="social-preview"><div className="social-post"><span className="mono">RASA NUSANTARA / CONTENT STUDY</span><h3>{posts[post]}</h3><span className="social-spark">✳</span><span className="social-bottom">rasa yang dekat. cerita yang hangat.</span></div><div className="post-controls">{['Awareness','Storytelling','Promosi'].map((t,i)=><button key={t} aria-pressed={post===i} className={post===i?'active':''} onClick={()=>setPost(i)}>{t}</button>)}</div></div><div className="project-caption"><div><p className="mono">SOSIAL MEDIA · SAMPLE CONTENT</p><h3>Satu brand, banyak cerita.</h3></div><Instagram size={22}/></div><details className="content-plan"><summary>Lihat contoh kalender konten</summary><p>Senin · Perkenalan brand<br/>Rabu · Cerita resep keluarga<br/>Jumat · Promosi menu makan siang</p><p>Konsep feed dan perencanaan, belum dipublikasikan.</p></details></article>}
 </div></div></section>
 <SocialServices />
 <section id="proses" className="section shell"><div className="section-heading"><div><p className="eyebrow">DARI OBROLAN KE EKSEKUSI</p><h2>Proses jelas.<br/><em>Jalan bareng.</em></h2></div><p>Kamu paling tahu bisnismu. Kami bantu menerjemahkannya ke solusi digital yang masuk akal.</p></div><div className="process-grid">{[['Kenalan dulu','Ceritakan bisnis, tantangan, dan tujuan yang ingin kamu capai.'],['Rancang arahnya','Sepakati lingkup, konsep, jadwal, dan estimasi sebelum mulai.'],['Bangun & rapikan','Kami kerjakan, kamu beri masukan. Kita tes sebelum digunakan.'],['Siap dinyalakan','Serah terima dan panduan untuk langkah berikutnya.']].map(([t,d])=><div key={t}><Plus className="process-mark" size={22}/><h3>{t}</h3><p>{d}</p></div>)}</div></section>
 <section className="section shell faq-section"><p className="eyebrow">SEBELUM MULAI</p><h2>Masih penasaran?</h2>{[['Bisa mulai dari satu layanan saja?','Bisa. Mulai dari website, otomasi, atau sosial media sesuai prioritas bisnismu.'],['Berapa biaya dan lama pengerjaannya?','Tergantung lingkup dan kebutuhan. Ceritakan idemu lewat WhatsApp atau Instagram, lalu kita susun estimasi dan jadwal yang sesuai.'],['Bagaimana cara mencoba showcase?','Kartu website dan contoh akun sosial media membuka tautan masing-masing di tab baru. Visual kartu adalah ilustrasi, bukan screenshot atau statistik akun. Demo otomasi dan contoh konten menggunakan data dummy, tanpa mengirim data atau memublikasikan konten.']].map(([q,a])=><details key={q}><summary>{q}<Plus size={18}/></summary><p>{a}</p></details>)}</section>
 <section id="kontak" className="contact-section"><div className="shell"><p className="eyebrow">NEXT CHAPTER, TOGETHER.</p><h2>Idemu punya potensi.<br/>Yuk, <em>nyalakan.</em></h2><div className="contact-bottom"><p>Belum punya brief yang rapi? Tidak apa-apa.<br/>Mulai dari cerita singkat tentang bisnismu.</p><div className="contact-links"><a className="button" href={whatsapp} target="_blank" rel="noopener noreferrer"><MessageCircle size={20}/>Chat WhatsApp</a><a className="contact-phone" href={phone}><Phone size={17}/>0821-1340-1340</a><a className="text-link" href={ig} target="_blank" rel="noopener noreferrer">Instagram @ignidi.labs</a></div></div></div></section></main><footer className="shell labs-footer"><a className="brand" href="#"><BrandLogo/><span>ignidi<small>labs</small><i>.</i></span></a><p>© {new Date().getFullYear()} Ignidi Labs · Bekasi, Indonesia</p><div className="footer-contacts"><a href={phone}>0821-1340-1340</a><a href={ig} target="_blank" rel="noopener noreferrer">@ignidi.labs</a></div></footer></div>;
}
