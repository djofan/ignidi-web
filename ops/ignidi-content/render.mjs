import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const [input, output] = process.argv.slice(2);
if (!input || !output || !/\.jpe?g$/i.test(output)) throw new Error('Gunakan: node render.mjs draft.json output.jpg');
const draft = JSON.parse((await fs.readFile(input, 'utf8')).replace(/^\uFEFF/, ''));
const content = draft.instagram;
if (!content || typeof content.headline !== 'string' || !Array.isArray(content.points) || content.points.length > 3) throw new Error('Headline dan maksimal tiga poin diperlukan.');
if (content.headline.length > 80 || content.points.some(point => typeof point !== 'string' || point.length > 65)) throw new Error('Headline maksimal 80 karakter; setiap poin maksimal 65 karakter.');
const escape = text => text.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]));
function wrap(text, limit, maxLines) {
  const result = [''];
  for (const word of text.trim().split(/\s+/)) {
    if (word.length > limit) throw new Error('Kata terlalu panjang untuk layout. Revisi draf.');
    if ((result.at(-1) + ' ' + word).trim().length > limit) result.push(word);
    else result[result.length - 1] = (result.at(-1) + ' ' + word).trim();
  }
  if (result.length > maxLines) throw new Error('Teks melebihi layout. Revisi sebelum render.');
  return result;
}
const headline = wrap(content.headline, 19, 4);
const pointLines = content.points.map(point => wrap(point, 39, 2));
const pointsY = 320 + headline.length * 95;
const logoPath = process.env.IGNIDI_LOGO_PATH;
if (!logoPath) throw new Error('Set IGNIDI_LOGO_PATH ke file logo asli Ignidi sebelum render.');
const logo = await fs.readFile(logoPath);
const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1350" viewBox="0 0 1080 1350">
<defs><radialGradient id="glow"><stop stop-color="#ff672c" stop-opacity=".22"/><stop offset="1" stop-color="#101110" stop-opacity="0"/></radialGradient><pattern id="grid" width="70" height="70" patternUnits="userSpaceOnUse"><path d="M70 0H0V70" fill="none" stroke="#f4c89a" stroke-opacity=".045"/></pattern><clipPath id="brand"><rect x="76" y="73" width="70" height="70" rx="10"/></clipPath></defs>
<rect width="1080" height="1350" fill="#101110"/><rect width="1080" height="1350" fill="url(#grid)"/><ellipse cx="1040" cy="1080" rx="620" ry="650" fill="url(#glow)"/>
<g stroke="#ff672c" fill="none"><path d="M1080 210H935L870 275V385" opacity=".4"/><path d="M0 980H85L140 1035H250" opacity=".3"/><circle cx="870" cy="385" r="6" opacity=".5"/></g>
${logo ? `<image x="-91" y="-45" width="405" height="405" clip-path="url(#brand)" href="data:image/jpeg;base64,${logo.toString('base64')}"/>` : '<path d="M90 78L130 108L90 138" fill="none" stroke="#ff672c" stroke-width="8"/>'}
<g font-family="DejaVu Sans, Arial, sans-serif"><text x="165" y="122" font-size="38" font-weight="700" fill="#f3f3e9">ignidi labs<tspan fill="#ff672c">.</tspan></text>
<path d="M76 181H1004" stroke="#383b30"/>
<text x="76" y="255" fill="#ff854b" font-size="20" letter-spacing="2">${escape((draft.pillar || 'IGNIDI LABS').toUpperCase())}</text>
${headline.map((line, i) => `<text x="76" y="${365 + i * 95}" fill="${i === headline.length - 1 ? '#ff672c' : '#f3f3e9'}" font-size="78" font-weight="700" letter-spacing="-3">${escape(line)}</text>`).join('')}
${pointLines.map((lines, i) => `<circle cx="86" cy="${pointsY + 72 + i * 106}" r="4" fill="#ff672c"/>${lines.map((line, j) => `<text x="110" y="${pointsY + 82 + i * 106 + j * 34}" fill="#c5c8bb" font-size="28">${escape(line)}</text>`).join('')}`).join('')}
<rect x="76" y="1135" width="455" height="70" rx="5" fill="#ff672c"/><text x="104" y="1179" font-size="24" font-weight="700" fill="#101110">Ceritakan idemu ke Ignidi.</text>
<path d="M76 1250H1004" stroke="#383b30"/><text x="76" y="1297" fill="#b3b6a8" font-size="20">WEB / OTOMASI / SOSIAL MEDIA</text><text x="1004" y="1297" text-anchor="end" fill="#f3f3e9" font-size="22">@ignidi.labs</text></g></svg>`;
await fs.mkdir(path.dirname(output), {recursive:true});
await sharp(Buffer.from(svg)).jpeg({quality:92, mozjpeg:true}).toFile(output);
console.log(`Preview lokal: ${output}. Belum dipublikasikan.`);
