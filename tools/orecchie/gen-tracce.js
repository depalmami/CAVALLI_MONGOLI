// TRACCE DI PROVA per le orecchie (3d/musica.js): un click a 128 BPM e un pezzo
// sintetico a 126 BPM — groove 16 battute → pausa 8 → salita 4 → DROP 16 — con la
// VERITÀ accanto (tempi delle casse e delle sezioni) in un .json.
// Uso:  node tools/orecchie/gen-tracce.js [cartella]   (default tools/orecchie/tracce)
const fs = require('fs');
const SR = +process.env.SR || 48000;
const DIR = process.argv[2] || require('path').join(__dirname, 'tracce');
fs.mkdirSync(DIR, { recursive: true });
let seme = 12345; const rnd = () => (seme = (seme * 1664525 + 1013904223) >>> 0) / 4294967296 * 2 - 1;
function scriviWav(nome, buf) {
  let picco = 0; for (const v of buf) picco = Math.max(picco, Math.abs(v));
  const g = 0.89 / picco, n = buf.length, dati = Buffer.alloc(44 + n * 4);
  dati.write('RIFF', 0); dati.writeUInt32LE(36 + n * 4, 4); dati.write('WAVE', 8); dati.write('fmt ', 12);
  dati.writeUInt32LE(16, 16); dati.writeUInt16LE(1, 20); dati.writeUInt16LE(2, 22); dati.writeUInt32LE(SR, 24);
  dati.writeUInt32LE(SR * 4, 28); dati.writeUInt16LE(4, 32); dati.writeUInt16LE(16, 34); dati.write('data', 36); dati.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) { const s = Math.round(Math.max(-1, Math.min(1, buf[i] * g)) * 32767); dati.writeInt16LE(s, 44 + i * 4); dati.writeInt16LE(s, 46 + i * 4); }
  fs.writeFileSync(nome, dati);
}
const add = (buf, t0, gen, dur, amp = 1) => { const a = Math.floor(t0 * SR); for (let i = 0; i < dur * SR && a + i < buf.length; i++) buf[a + i] += amp * gen(i / SR); };
const cassa = t => { const f = 50 + 100 * Math.exp(-t / 0.03); return Math.sin(2 * Math.PI * (50 * t + 100 * 0.03 * (1 - Math.exp(-t / 0.03)))) * Math.exp(-t / 0.13) + (t < 0.003 ? rnd() * 0.3 : 0); };
const rullante = t => (rnd() * 0.8 * Math.exp(-t / 0.10) + Math.sin(2 * Math.PI * 190 * t) * 0.5 * Math.exp(-t / 0.06));
let hp = 0; const charleston = t => { const r = rnd(); const v = r - hp; hp = r; return v * 0.5 * Math.exp(-t / 0.03); };
const basso = f => t => (Math.sin(2 * Math.PI * f * t) + 0.3 * Math.sin(4 * Math.PI * f * t)) * Math.exp(-t / 0.18);
const pad = (t, T) => [220, 277.2, 329.6, 440].reduce((s, f) => s + Math.sin(2 * Math.PI * f * T + Math.sin(T * 0.7)), 0) * 0.06;

// 1) click a 128 BPM, 40 s
{
  const bpm = 128, dur = 40, buf = new Float32Array(dur * SR), p = 60 / bpm;
  for (let t = 0.5; t < dur - 0.3; t += p) add(buf, t, cassa, 0.3);
  scriviWav(DIR + '/click128.wav', buf);
  const cs = []; for (let t = 0.5; t < dur - 0.3; t += p) cs.push(+t.toFixed(4));
  fs.writeFileSync(DIR + '/click128.json', JSON.stringify({ bpm, inizio: 0.5, sezioni: [], casse: cs }));
}
// 2) pezzo: groove 16 battute → pausa 8 → salita 4 → DROP 16, a 126 BPM
{
  const bpm = 126, p = 60 / bpm, B = 4 * p;
  const sez = [['groove', 16], ['pausa', 8], ['salita', 4], ['drop', 16]];
  const tot = sez.reduce((s, x) => s + x[1], 0) * B + 1;
  const buf = new Float32Array(Math.ceil(tot * SR));
  const note = [], casse = [];
  let t0 = 0.5;
  for (const [nome, battute] of sez) {
    note.push({ sezione: nome, t: +t0.toFixed(3) });
    for (let b = 0; b < battute; b++) {
      const tb = t0 + b * B;
      for (let k = 0; k < 4; k++) {
        const t = tb + k * p;
        if (nome === 'groove' || nome === 'drop') {
          add(buf, t, cassa, 0.3, nome === 'drop' ? 1.1 : 0.9); casse.push(+t.toFixed(4));
          if (k === 1 || k === 3) add(buf, t, rullante, 0.25, 0.5);
          add(buf, t + p / 2, basso(nome === 'drop' ? 49 : 55), 0.3, 0.5);
        }
        add(buf, t + p / 2, charleston, 0.06, nome === 'pausa' ? 0.25 : 0.35);
      }
      if (nome === 'pausa' || nome === 'salita') add(buf, tb, T => pad(0, tb + T), B, 1);
      if (nome === 'salita') {
        const div = b < 2 ? 2 : 4;                     // rullata che accelera
        for (let k = 0; k < 4 * div; k++) add(buf, tb + k * p / div, rullante, 0.2, 0.15 + 0.35 * (b * 4 * div + k) / (16 * div));
        add(buf, tb, T => { const r = rnd(); const v = r - hp; hp = r; return v * 0.25 * ((b * B + T) / (4 * B)); }, B, 1);   // riser di rumore
      }
    }
    t0 += battute * B;
  }
  scriviWav(DIR + '/pezzo126.wav', buf);
  fs.writeFileSync(DIR + '/pezzo126.json', JSON.stringify({ bpm, inizio: 0.5, sezioni: note, casse }));
  console.log('tracce in', DIR);
}
