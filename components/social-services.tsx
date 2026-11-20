import { Camera, Globe, Plus } from 'lucide-react';

export const socialAccounts = [
  { name: 'Contoh akun Facebook', handle: 'Profil Facebook', platform: 'Facebook', url: 'https://www.facebook.com/profile.php?id=61554436017146', tone: 'ember' },
  { name: 'Lazsip', handle: 'facebook.com/lazsip', platform: 'Facebook', url: 'https://www.facebook.com/lazsip', tone: 'olive' },
  { name: 'Insan Peduli', handle: '@insanpeduliofficial', platform: 'Instagram', url: 'https://www.instagram.com/insanpeduliofficial/', tone: 'olive' },
  { name: 'Lazsip', handle: '@lazsip_id', platform: 'Instagram', url: 'https://www.instagram.com/lazsip_id/', tone: 'ember' },
];

export function SocialAccountCards() {
  return socialAccounts.map(account => (
    <a className={`social-account social-account-${account.tone}`} key={account.url} href={account.url} target="_blank" rel="noopener noreferrer" aria-label={`Buka ${account.name} di ${account.platform}, tab baru`}>
      <div className="social-account-top"><span className="mono">CONTOH AKUN / {account.platform.toUpperCase()}</span>{account.platform === 'Instagram' ? <Camera size={24} /> : <Globe size={24} />}</div>
      <h3>{account.name}</h3>
      <p>{account.handle}</p>
      <div className="social-account-bottom"><span>Lihat akun di {account.platform}</span><Plus size={18} /></div>
    </a>
  ));
}

const deliverables = [
  ['Strategi & kalender konten', 'Kenali audiens, tentukan pilar cerita, lalu susun tema dan jadwal publikasi yang punya arah.'],
  ['Desain feed, carousel & story', 'Visual yang saling terhubung, mudah dikenali, dan konsisten dengan karakter brand kamu.'],
  ['Video pendek & Reels', 'Ide, naskah, dan editing video pendek sesuai materi serta lingkup produksi yang disepakati.'],
  ['Copywriting & caption', 'Pesan yang jelas, pembuka yang menarik, dan ajakan bertindak sesuai tujuan setiap konten.'],
  ['Publikasi & pengelolaan komunitas', 'Penjadwalan konten serta pemantauan komentar dan pesan sesuai jam layanan yang disepakati.'],
  ['Insight & evaluasi berkala', 'Tinjau jangkauan, interaksi, dan respons audiens untuk menentukan langkah konten berikutnya.'],
];
const process = [
  ['Kenali titik awal', 'Audit akun, pahami audiens dan identitas brand, lalu pelajari konteks kompetitor.'],
  ['Sepakati arah', 'Susun pilar, ide, dan kalender konten untuk kamu tinjau sebelum produksi.'],
  ['Produksi & review', 'Kerjakan visual, video, dan caption. Rapikan bersama lewat proses persetujuan.'],
  ['Publikasi & interaksi', 'Tayangkan konten yang disetujui dan pantau percakapan sesuai lingkup layanan.'],
  ['Baca hasil, perbaiki', 'Bahas insight dan rekomendasi untuk menyempurnakan rencana periode berikutnya.'],
];

export function SocialServices() {
  return (
    <section id="sosial-media" className="section social-services">
      <div className="shell">
        <div className="section-heading"><div><p className="eyebrow">SOCIAL MEDIA, WITH INTENTION.</p><h2>Hadir konsisten.<br /><em>Punya cerita.</em></h2></div><p>Dari merancang pesan sampai membaca respons audiens. Kita susun layanan sosial media sesuai kebutuhan dan ritme bisnismu.</p></div>
        <div className="social-deliverables">{deliverables.map(([title, text]) => <article key={title}><Plus size={20} /><h3>{title}</h3><p>{text}</p></article>)}</div>
        <div className="social-platforms"><span>Platform sesuai kebutuhan</span><span>Instagram</span><span>Facebook</span><span>TikTok</span><span>LinkedIn</span></div>
        <div className="social-workflow-heading"><p className="eyebrow">CARA KERJA SOSIAL MEDIA</p><h2>Dari arah yang jelas,<br /><em>ke cerita yang hidup.</em></h2><p>Setiap periode punya rencana, ruang persetujuan, dan bahan evaluasi.</p></div>
        <ol className="social-workflow">{process.map(([title, text]) => <li key={title}><span className="workflow-spark" aria-hidden="true">✳</span><h3>{title}</h3><p>{text}</p></li>)}</ol>
        <div className="social-services-cta"><p>Mulai dari akun yang kamu punya. Kita bahas apa yang perlu dirapikan.</p><a href="#kontak" className="button">Bahas sosial mediamu <Plus size={17} /></a></div>
      </div>
    </section>
  );
}
