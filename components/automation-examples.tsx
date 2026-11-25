"use client";

import { useState } from 'react';
import { Check, Play, RotateCcw, Workflow, Download, ExternalLink } from 'lucide-react';
import { automationCases, type AutomationCase, type AutomationValues } from '@/lib/automation-cases';
import { runAutomation, type AutomationRun } from '@/lib/automation-engine';

const statusNames = { success: 'Selesai', waiting: 'Menunggu review', skipped: 'Dilewati', error: 'Perlu diperiksa' };

function AutomationCard({ item }: { item: AutomationCase }) {
  const [preset, setPreset] = useState('0');
  const [values, setValues] = useState<AutomationValues>({ ...item.presets[0].values });
  const [result, setResult] = useState<AutomationRun | null>(null);
  const [processedEvents, setProcessedEvents] = useState<string[]>([]);
  const [runs, setRuns] = useState(0);
  function update(key: string, value: string) {
    setValues(previous => ({ ...previous, [key]: value }));
    setPreset('custom');
    setResult(null);
  }
  function execute() {
    const run = runAutomation(item, values, processedEvents);
    setResult(run);
    setRuns(count => count + 1);
    const event = run.output.rememberEvent;
    if (typeof event === 'string') setProcessedEvents(previous => [...new Set([...previous, event])]);
  }
  function download() {
    if (!result) return;
    const report = { kind: 'ignidi-browser-simulation', case: item.id, input: values, ...result, reference: item.source, note: 'Hasil lokal, bukan file workflow impor dan bukan bukti eksekusi layanan eksternal.' };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `ignidi-${item.id}-hasil-demo.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <article className="automation-case automation-lab-card" aria-labelledby={`automation-title-${item.id}`}>
      <div className="automation-case-heading"><span className="mono">{item.category}</span><Workflow size={23} aria-hidden="true" /></div>
      <h3 id={`automation-title-${item.id}`}>{item.title}</h3>
      <p className="automation-problem">{item.problem}</p>
      <div className="automation-pattern"><span className="mono">PEMICU · {item.trigger}</span><p>{item.pattern}</p></div>
      <label htmlFor={`automation-preset-${item.id}`}>Mulai dari kondisi contoh</label>
      <div className="automation-select"><select id={`automation-preset-${item.id}`} value={preset} onChange={event => {
        setPreset(event.target.value);
        setValues({ ...item.presets[Number(event.target.value)].values });
        setResult(null);
      }}>
        {preset === 'custom' && <option value="custom" disabled>Input kustom</option>}
        {item.presets.map((option, index) => <option value={index} key={option.label}>{option.label}</option>)}
      </select><span aria-hidden="true">⌄</span></div>
      <form className="automation-fields" onSubmit={event => { event.preventDefault(); execute(); }} noValidate>
        {item.fields.map(field => {
          const id = `automation-${item.id}-${field.key}`;
          const hintId = `${id}-hint`;
          return <div key={field.key} className="automation-field"><label htmlFor={id}>{field.label}</label>
            {field.kind === 'select' ? <div className="automation-select"><select id={id} value={values[field.key]} aria-describedby={field.hint ? hintId : undefined} onChange={event => update(field.key, event.target.value)}>{field.options?.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select><span aria-hidden="true">⌄</span></div>
              : field.kind === 'textarea' ? <textarea id={id} rows={4} maxLength={3000} value={values[field.key]} aria-describedby={field.hint ? hintId : undefined} onChange={event => update(field.key, event.target.value)} spellCheck={false} />
                : <input id={id} type={field.kind === 'number' ? 'number' : 'text'} min={field.min} max={field.max} step={field.kind === 'number' ? 1 : undefined} maxLength={field.kind === 'number' ? undefined : 3000} value={values[field.key]} aria-describedby={field.hint ? hintId : undefined} onChange={event => update(field.key, event.target.value)} autoComplete="off" />}
            {field.hint && <p id={hintId}>{field.hint}</p>}
          </div>;
        })}
        <div className="automation-case-actions"><button className="button small" type="submit"><Play size={15} />{result ? 'Jalankan lagi' : 'Jalankan alur'}</button><button type="button" className="automation-reset" onClick={() => { setValues({ ...item.presets[0].values }); setPreset('0'); setResult(null); setProcessedEvents([]); setRuns(0); }}><RotateCcw size={14} />Reset demo</button></div>
      </form>
      <div className={`automation-result automation-result-${result?.status ?? 'idle'}`} role="status" aria-live="polite" aria-atomic="true">
        <span className="mono">{result ? `${statusNames[result.status]} · EKSEKUSI LOKAL ${runs}` : 'SIAP MENERIMA INPUT CONTOH'}</span>
        <p>{result?.summary ?? 'Ubah input lalu jalankan. Hasil dihitung dari data dan aturan yang dipilih, tanpa menghubungi layanan luar.'}</p>
      </div>
      {result && <>
        <ol className="automation-run-log" aria-label={`Log alur ${item.title}`}>{result.logs.map(log => <li key={log.name} className={`log-${log.status}`}><span className="automation-log-icon" aria-hidden="true">{log.status === 'success' ? <Check size={14} /> : log.status === 'waiting' ? '…' : log.status === 'error' ? '!' : '–'}</span><div><strong>{log.name}<small>{statusNames[log.status]}</small></strong><p>{log.detail}</p></div></li>)}</ol>
        <details className="automation-explainer"><summary>Lihat data hasil</summary><pre>{JSON.stringify(result.output, null, 2)}</pre><button className="automation-reset" onClick={download}><Download size={14} />Unduh hasil JSON</button></details>
      </>}
      <details className="automation-explainer"><summary>Manfaat & sumber pola</summary><p>{item.outcome}</p><p>Pola diadaptasi dari kapabilitas {item.source.name}. Mesin aturan demo ini ditulis untuk Ignidi; tidak menjalankan engine repo tersebut.</p><div className="automation-source-links"><a href={item.source.repo} target="_blank" rel="noopener noreferrer">Repo {item.source.name}<ExternalLink size={12} /></a><a href={item.source.docs} target="_blank" rel="noopener noreferrer">Dokumentasi pola<ExternalLink size={12} /></a></div></details>
      {item.id === 'order' && <p className="automation-session-note">{processedEvents.length} ID event di memori kartu. Jalankan ID yang sama lagi untuk menguji duplikasi. Reset, ganti filter, atau muat ulang menghapus memori demo.</p>}
      <p className="automation-disclaimer">DEMO LOKAL · Gunakan data contoh. Tidak mengirim pesan, mengubah stok, melakukan pembayaran, atau mengakses API.</p>
    </article>
  );
}

export function AutomationExamples() {
  return <>
    <div className="automation-intro"><p className="eyebrow">AUTOMATION LAB / INPUT. RULES. RESULT.</p><h3>Sepuluh kasus.<br /><em>Logika yang bisa diuji.</em></h3><p>Ubah input, jalankan alur, lalu periksa cabang keputusan dan hasilnya. Deduplikasi, perhitungan, validasi, approval, serta retry dihitung di browser dengan data contoh. Untuk pemakaian bisnis, koneksi ke tools dan akun disiapkan sesuai kebutuhan.</p><div className="automation-references"><span>Pola rujukan</span>{[
      ['n8n', 'https://github.com/n8n-io/n8n'], ['Activepieces', 'https://github.com/activepieces/activepieces'], ['Windmill', 'https://github.com/windmill-labs/windmill'],
    ].map(([name, url]) => <a key={name} href={url} target="_blank" rel="noopener noreferrer">{name}<ExternalLink size={12} /></a>)}</div><p className="automation-origin-note">Implementasi demo oleh Ignidi, berdasarkan pola pada dokumentasi resmi. Bukan integrasi aktif, afiliasi, atau hasil klien. Sumber setiap pola tersedia di masing-masing kartu.</p></div>
    {automationCases.map(item => <AutomationCard item={item} key={item.id} />)}
  </>;
}
