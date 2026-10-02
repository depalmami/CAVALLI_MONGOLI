// BANCO offline delle orecchie: lo STESSO worklet e la STESSA musica.js del gioco,
// fuori dal browser, su un WAV a tempo simulato (blocchi da 128 campioni, un frame
// ogni 16,7 ms). Misura contro la verità del generatore: casse giuste/false,
// orologio contro i battiti veri, sezioni. Gira in pochi secondi invece che a
// tempo reale, quindi si rilancia a ogni ritocco della rilevazione.
// Uso:  node tools/orecchie/banco.mjs tools/orecchie/tracce/pezzo126.wav
//       LINEA=1 …  stampa anche l'errore dell'orologio battito per battito
// Valori al 1 ott 2026: click → orologio +8,0 ± 0,4 ms, 0 casse false;
//                       pezzo → +5,6 ± 4,2 ms, drop a 53,85 s (vero 53,83).
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const radice = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const wavPath = process.argv[2], veritaPath = process.argv[3] || wavPath.replace(/\.wav$/, '.json');
const verita = JSON.parse(fs.readFileSync(veritaPath));
// WAV 16 bit stereo → mono
const buf = fs.readFileSync(wavPath), SR = buf.readUInt32LE(24), n = (buf.length - 44) / 4;
const x = new Float32Array(n);
for (let i = 0; i < n; i++) x[i] = (buf.readInt16LE(44 + i*4) + buf.readInt16LE(46 + i*4)) / 65536;
let T = 0;
globalThis.performance = { now: () => T };
globalThis.addEventListener = () => {};
globalThis.sampleRate = SR; globalThis.currentTime = 0;
const posta = [];
globalThis.AudioWorkletProcessor = class { constructor() { this.port = { postMessage: d => posta.push(d) }; } };
let Classe; globalThis.registerProcessor = (_, c) => { Classe = c; };
await import(radice + '/3d/orecchio.worklet.js');
const { creaMusica } = await import(radice + '/3d/musica.js');
const proc = new Classe(), m = creaMusica();
m._banco.attiva();
const eventi = [];
m.on('sezione', e => eventi.push({ t: T/1000, ...e }));
m.on('drop', () => eventi.push({ t: T/1000, DROP: true }));
const FRAME = 1000/60; let prossimoFrame = 0;
for (let i = 0; i + 128 <= n; i += 128) {
  globalThis.currentTime = i / SR;
  proc.process([[x.subarray(i, i + 128)]]);
  while (posta.length) m._banco.daWorklet(posta.shift());
  T = (i + 128) / SR * 1000;
  if (T >= prossimoFrame) {
    prossimoFrame += FRAME;
    let s = 0; const a = Math.max(0, i + 128 - 2048); for (let k = a; k < i + 128; k++) s += x[k]*x[k];
    m._banco.livello(20*Math.log10(Math.sqrt(s / (i + 128 - a)) + 1e-9));
    m.aggiorna();
  }
}
// ── metriche ──
const P = 60 / verita.bpm * 1000;
const colpi = m.diag.colpi.filter(c => c.voce === 'cassa').map(c => c.t);
const casseVere = verita.casse.map(t => t*1000);
const vicino = (t, lista) => { let b = 1e9; for (const y of lista) if (Math.abs(t - y) < Math.abs(b)) b = t - y; return b; };
const ok = colpi.filter(t => Math.abs(vicino(t, casseVere)) < 40);
const stat = a => { if (!a.length) return '—'; const mu = a.reduce((p, q) => p + q, 0)/a.length; return `media ${mu.toFixed(1)} dev ${Math.sqrt(a.reduce((p, q) => p + (q-mu)**2, 0)/a.length).toFixed(1)} n ${a.length}`; };
console.log(`CASSE: vere ${casseVere.length}, rilevate ${colpi.length}, giuste ${ok.length}, false ${colpi.length - ok.length}`);
console.log('  ritardo rilevamento (ms):', stat(ok.map(t => vicino(t, casseVere))));
// orologio contro i battiti veri, da quando il tempo è agganciato (oltre 10 s)
const battitiVeri = []; for (let t = verita.inizio*1000; t < n/SR*1000; t += P) battitiVeri.push(t);
const bt = m.diag.battiti.filter(b => b.t > 10000).map(b => b.t);
const errB = bt.map(t => vicino(t, battitiVeri));
console.log('OROLOGIO − battito vero (ms):', stat(errB), ' |err|>60:', errB.filter(e => Math.abs(e) > 60).length);
const st = m.diag.stime;
console.log('BPM: prima stima a', (st[0]?.t/1000)?.toFixed(1), 's =', st[0]?.bpm.toFixed(2), '· finale', m.bpm.toFixed(2), 'atteso', verita.bpm);
console.log('SEZIONI attese  :', verita.sezioni.map(s => `${s.sezione}@${s.t.toFixed(1)}`).join('  '));
console.log('SEZIONI rilevate:', eventi.map(e => e.DROP ? `💥@${e.t.toFixed(2)}` : `${e.sezione}@${e.t.toFixed(1)}`).join('  '));
if (process.env.LINEA) {
  // linea del tempo: errore dell'orologio per battito (ms), un carattere ogni battito
  const righe = [];
  for (const b of m.diag.battiti) { const e = vicino(b.t, battitiVeri); righe.push(`${(b.t/1000).toFixed(1)}:${e.toFixed(0)}`); }
  console.log(righe.join(' '));
}
