"use client";

import { useState } from 'react';
import { Check, Play, RotateCcw, Workflow } from 'lucide-react';
import { automationCases } from '@/lib/automation-cases';

function AutomationCase({ item }: { item: typeof automationCases[number] }) {
  const [scenarioIndex, setScenarioIndex] = useState(0);
  const [step, setStep] = useState(0);
  const scenario = item.scenarios[scenarioIndex];
  const finished = step === item.steps.length;

  return (
    <article className="automation-case" aria-labelledby={`automation-title-${item.id}`}>
      <div className="automation-case-heading"><span className="mono">{item.category}</span><Workflow size={23} aria-hidden="true" /></div>
      <h3 id={`automation-title-${item.id}`}>{item.title}</h3>
      <p className="automation-problem">{item.problem}</p>
      <label htmlFor={`automation-scenario-${item.id}`}>Pilih kondisi contoh</label>
      <div className="automation-select"><select id={`automation-scenario-${item.id}`} value={scenarioIndex} onChange={event => { setScenarioIndex(Number(event.target.value)); setStep(0); }}>
        {item.scenarios.map((option, index) => <option value={index} key={option.label}>{option.label}</option>)}
      </select><span aria-hidden="true">⌄</span></div>
      <div className="automation-input"><span className="mono">DATA DUMMY</span><p>{scenario.input}</p></div>
      <ol className="automation-steps" aria-label="Tahapan simulasi">{item.steps.map((label, index) => (
        <li key={label} className={step > index ? 'is-done' : ''}><span aria-hidden="true">{step > index ? <Check size={14} /> : <span className="automation-step-dot" />}</span>{label}</li>
      ))}</ol>
      <div className="automation-result" role="status" aria-live="polite" aria-atomic="true">
        <span className="mono">{finished ? 'HASIL SIMULASI' : step ? 'PROSES SIMULASI' : 'SIAP DICOBA'}</span>
        <p>{step ? scenario.outputs[step - 1] : 'Jalankan demo untuk melihat bagaimana alur memproses kondisi yang dipilih.'}</p>
      </div>
      <div className="automation-case-actions"><button className="button small" onClick={() => setStep(finished ? 0 : step + 1)}>
        {finished ? <RotateCcw size={15} /> : <Play size={15} />}{finished ? 'Ulangi demo' : step ? 'Lanjutkan langkah' : 'Jalankan demo'}
      </button><span>{step} / {item.steps.length} langkah</span></div>
      <details className="automation-explainer"><summary>Manfaat & penerapan</summary><p>{item.outcome}</p><p>Integrasi formulir, database, email, atau WhatsApp dipilih sesuai kebutuhan dan akses yang disepakati. Demo ini hanya berjalan di browser, tanpa koneksi ke akun atau data produksi.</p></details>
      <p className="automation-disclaimer">SIMULASI · Tidak mengirim pesan, mengubah stok, atau memproses pembayaran.</p>
    </article>
  );
}

export function AutomationExamples() {
  return <>
    <div className="automation-intro"><p className="eyebrow">KASUS SEHARI-HARI, ALUR YANG BISA DICOBA.</p><h3>Kerja berulang?<br /><em>Coba lihat alurnya.</em></h3><p>Lima contoh berdasarkan kebutuhan operasional sehari-hari, dengan data dummy. Pilih kondisi berbeda untuk membandingkan hasilnya. Ini ilustrasi solusi, bukan klaim implementasi atau hasil klien.</p></div>
    {automationCases.map(item => <AutomationCase item={item} key={item.id} />)}
  </>;
}
