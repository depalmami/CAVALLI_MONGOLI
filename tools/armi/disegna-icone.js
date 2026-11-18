// LE ICONE DELLE ARMI PER L'HUD (pixel art 32x32). Disegnate a codice, non a mano: ogni icona è fatta di poche primitive
// (curve spesse con un profilo di larghezza, linee, dischi) più un contorno automatico di 1 pixel, così si possono ritoccare
// forma e colori senza ridisegnare pixel per pixel. Escono in assets/hud/arma-<chiave>.png (RGBA, fondo trasparente), una per
// arma del gioco (fists, whip, mace, saber, bow), e in una tavola d'anteprima ingrandita sul blu dei riquadri dell'HUD.
//
// uso:  node tools/armi/disegna-icone.js [cartella-anteprima]
//
// Convenzione: le armi puntano in alto a destra (l'impugnatura in basso a sinistra), tranne i pugni e l'arco, che stanno dritti.
// Colori: l'acciaio azzurro della sciabola, il cuoio della frusta, il ferro della mazza (gli stessi di WEAPONS.color), l'oro
// del Soyombo per le guardie, il blu della bandiera per la manica dei pugni (come quella del protagonista).
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const N = 32;

const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const C = Object.fromEntries(Object.entries({
  nero: '#090b18',
  accL: '#f4f8ff', accM: '#b9c6ea', accD: '#6c7ba8',
  ferL: '#d5d9e2', ferM: '#8e96a3', ferD: '#555d6b',
  oroL: '#ffe36a', oroM: '#dcb200', oroD: '#946f00',
  cuL: '#d9993f', cuM: '#9a6330', cuD: '#5f3a1a',
  leL: '#c48a48', leM: '#8a5a2a', leD: '#52331a',
  peL: '#ffd7b0', peM: '#f0b585', peD: '#c98458',
  bluL: '#3a72dc', bluM: '#1c4db0', bluD: '#082c6b',
  rosso: '#c0262e', corda: '#efe3c4', cordaD: '#b9a67a', bianco: '#ffffff',
}).map(([k, v]) => [k, hex(v)]));

const nuova = () => Array.from({ length: N * N }, () => null);
const set = (g, x, y, c) => { x = Math.round(x); y = Math.round(y); if (x >= 0 && y >= 0 && x < N && y < N && c) g[y * N + x] = c; };
const get = (g, x, y) => (x >= 0 && y >= 0 && x < N && y < N) ? g[y * N + x] : null;
const rect = (g, x0, y0, x1, y1, c) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) set(g, x, y, c); };
const disco = (g, cx, cy, r, c) => { for (let y = Math.floor(cy - r); y <= Math.ceil(cy + r); y++) for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x++) if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.25) set(g, x, y, c); };
// linea con spessore w (pennello quadrato): w=1 un pixel, w=2 due...
function linea(g, x0, y0, x1, y1, w, c) {
  const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) * 2 || 1;
  for (let i = 0; i <= n; i++) { const x = x0 + (x1 - x0) * i / n, y = y0 + (y1 - y0) * i / n;
    for (let a = 0; a < w; a++) for (let b = 0; b < w; b++) set(g, Math.round(x) + a - Math.floor((w - 1) / 2), Math.round(y) + b - Math.floor((w - 1) / 2), typeof c === 'function' ? c(i / n) : c); }
}
const bez = (pts, t) => { let p = pts; while (p.length > 1) { const q = []; for (let i = 0; i < p.length - 1; i++) q.push([p[i][0] * (1 - t) + p[i + 1][0] * t, p[i][1] * (1 - t) + p[i + 1][1] * t]); p = q; } return p[0]; };
// un tratto lungo una curva di Bézier, con larghezza che cambia da w0 a w1; colore(u, t): u in [-1,1] attraverso la larghezza
// (-1 = lato sinistro andando avanti), t in [0,1] lungo la curva
function tratto(g, pts, w0, w1, colore, passi = 120) {
  for (let i = 0; i <= passi; i++) {
    const t = i / passi, c = bez(pts, t), a = bez(pts, Math.max(0, t - 0.01)), b = bez(pts, Math.min(1, t + 0.01));
    let dx = b[0] - a[0], dy = b[1] - a[1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
    const nx = -dy, ny = dx, h = (w0 + (w1 - w0) * t) / 2;
    for (let s = -h; s <= h + 1e-6; s += 0.4) set(g, c[0] + nx * s, c[1] + ny * s, colore(h ? s / h : 0, t));
  }
}
// contorno scuro di 1 pixel attorno a tutto ciò che è disegnato (spento quando si disegna per la versione a 16 px: lì si ricalcola dopo)
let SENZA_CONTORNO = false;
function contorno(g, c = C.nero) {
  if (SENZA_CONTORNO) return;
  const pieno = g.map(p => !!p);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (!pieno[y * N + x]) {
    const v = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => x + dx >= 0 && y + dy >= 0 && x + dx < N && y + dy < N && pieno[(y + dy) * N + x + dx]);
    if (v) g[y * N + x] = c;
  }
}

// ── le cinque icone ─────────────────────────────────────────────────────────
function pugni() {
  const g = nuova();
  // manica blu (come il protagonista), polsino bianco
  rect(g, 8, 25, 24, 30, C.bluM); rect(g, 8, 25, 24, 26, C.bluL); rect(g, 8, 29, 24, 30, C.bluD); rect(g, 8, 24, 24, 24, C.bianco);
  // il pugno: palmo e quattro nocche
  rect(g, 8, 13, 24, 23, C.peM);
  for (let i = 0; i < 4; i++) { const x0 = 8 + i * 4.25 | 0; rect(g, x0 + 0, 8, x0 + 3, 14, C.peM); set(g, x0, 8, null); set(g, x0 + 3, 8, null); rect(g, x0 + 1, 8, x0 + 2, 9, C.peL); }
  for (const x of [12, 16, 20]) rect(g, x, 9, x, 14, C.peD);                 // le fessure fra le dita
  rect(g, 8, 13, 24, 13, C.peD);                                              // la piega delle dita
  // il pollice in diagonale sul palmo
  rect(g, 9, 17, 20, 21, C.peM); rect(g, 10, 17, 18, 17, C.peL); rect(g, 10, 16, 19, 16, C.peD);
  rect(g, 9, 21, 20, 21, C.peD); set(g, 9, 17, C.peD); set(g, 20, 17, C.peD); rect(g, 21, 18, 21, 20, C.peD);
  rect(g, 23, 14, 24, 23, C.peD);                                             // ombra a destra
  // i raggi del colpo
  linea(g, 27, 8, 30, 5, 1, C.oroL); linea(g, 28, 12, 31, 12, 1, C.oroL); linea(g, 4, 8, 1, 5, 1, C.oroL); linea(g, 4, 12, 1, 12, 1, C.oroL);
  contorno(g); return g;
}
function frusta() {
  const g = nuova();
  // la striscia intrecciata: due toni che si alternano, parte dal manico, sale e si arriccia sopra
  // (una S: sale dal manico, scende, risale e finisce in punta: legge come frusta, non come uncino)
  const lash = [[12, 20], [13, 4], [22, 30], [29, 5]];
  tratto(g, lash, 2.8, 1.4, (u, t) => (Math.floor(t * 40) % 2 ? C.cuL : C.cuM), 200);
  tratto(g, lash, 2.8, 1.4, (u, t) => (u > 0.55 ? C.cuD : null), 200);
  const punta = bez(lash, 1); disco(g, punta[0], punta[1], 1.2, C.cuD); set(g, punta[0] + 1, punta[1] - 2, C.cuM);   // il nodo e lo sfilacciato
  // il manico: cuoio avvolto, anello d'oro
  linea(g, 4, 28, 11, 21, 4, C.leM);
  linea(g, 3, 27, 10, 20, 1, C.leL); linea(g, 6, 29, 13, 22, 1, C.leD);
  for (const [x, y] of [[5, 26], [7, 24], [9, 22]]) { set(g, x, y + 1, C.leD); set(g, x + 1, y, C.leD); }
  linea(g, 10, 18, 14, 22, 2, C.oroM); set(g, 11, 18, C.oroL); set(g, 10, 19, C.oroL); set(g, 14, 22, C.oroD); set(g, 13, 23, C.oroD);
  disco(g, 3, 29, 1.2, C.oroM);                                               // il pomolo
  contorno(g); return g;
}
function mazza() {
  const g = nuova();
  // il manico di legno, in diagonale, con la fascetta di cuoio e il cinturino rosso in fondo
  linea(g, 4, 28, 17, 15, 4, C.leM);
  linea(g, 3, 27, 16, 14, 1, C.leL); linea(g, 6, 29, 19, 16, 1, C.leD);
  for (const [x, y] of [[8, 24], [11, 21], [14, 18]]) { linea(g, x, y + 1, x + 2, y - 1, 1, C.leD); }
  linea(g, 3, 29, 8, 24, 1, C.rosso); set(g, 2, 30, C.rosso); set(g, 3, 31, C.rosso); set(g, 4, 31, C.rosso);
  // la testa: sfera di ferro con otto punte
  const cx = 21, cy = 11;
  for (let k = 0; k < 8; k++) {
    const a = k * Math.PI / 4 + Math.PI / 8, ux = Math.cos(a), uy = Math.sin(a);
    linea(g, cx + ux * 6, cy + uy * 6, cx + ux * 10, cy + uy * 10, 2, C.ferM);
    set(g, cx + ux * 10.5, cy + uy * 10.5, C.ferL);
  }
  disco(g, cx, cy, 7, C.ferM);
  disco(g, cx + 1.5, cy + 1.5, 5.5, C.ferD); disco(g, cx - 0.5, cy - 0.5, 5.5, C.ferM);
  disco(g, cx - 2, cy - 2.5, 3, C.ferL); disco(g, cx - 3, cy - 3.5, 1.3, C.bianco);
  rect(g, 15, 15, 17, 17, C.leD);                                              // la ghiera dove il manico entra nella testa
  contorno(g); return g;
}
function sciabola() {
  const g = nuova();
  const lama = [[10, 21], [22, 15], [29, 3]];
  tratto(g, lama, 5, 1.2, (u, t) => (u < -0.35 ? C.accL : u > 0.45 ? C.accD : C.accM));
  // la scanalatura lungo il dorso
  for (let i = 0; i <= 40; i++) { const t = 0.08 + i / 40 * 0.62, p = bez(lama, t); set(g, p[0] - 0.6, p[1] - 0.6, C.accD); }
  // guardia d'oro (perpendicolare all'inizio della lama), impugnatura di cuoio, pomolo
  linea(g, 8, 17, 13, 27, 2, C.oroM); set(g, 8, 17, C.oroL); set(g, 9, 18, C.oroL); set(g, 13, 27, C.oroD); set(g, 12, 27, C.oroD);
  linea(g, 9, 23, 3, 26, 3, C.leM); linea(g, 9, 22, 3, 25, 1, C.leL); linea(g, 9, 24, 3, 27, 1, C.leD);
  set(g, 6, 24, C.leD); set(g, 7, 25, C.leD);
  disco(g, 2, 27, 1.8, C.oroM); set(g, 1, 26, C.oroL);
  contorno(g); return g;
}
function arco() {
  const g = nuova();
  // la freccia appena scoccata, dalla corda verso destra: asta, penne rosse, punta d'acciaio
  linea(g, 19, 16, 29, 16, 1, C.corda); linea(g, 19, 17, 29, 17, 1, C.cordaD);
  for (const x of [22, 25]) { linea(g, x + 1, 16, x - 1, 13, 1, C.rosso); linea(g, x + 1, 17, x - 1, 20, 1, C.rosso); }
  rect(g, 28, 14, 28, 19, C.accM); rect(g, 29, 15, 30, 18, C.accM); rect(g, 31, 16, 31, 17, C.accM);
  rect(g, 28, 14, 28, 15, C.accL); rect(g, 29, 15, 30, 15, C.accL); set(g, 31, 16, C.accL);
  // l'arco: legno che si piega a sinistra, con le punte rivolte in fuori
  const flettente = [[20, 2], [3, 12], [3, 21], [20, 30]];
  tratto(g, flettente, 4, 3, (u, t) => (u < -0.3 ? C.leL : u > 0.4 ? C.leD : C.leM));
  linea(g, 20, 2, 23, 1, 1, C.leM); linea(g, 20, 30, 23, 31, 1, C.leM);
  // impugnatura avvolta di cuoio al centro
  rect(g, 2, 13, 6, 19, C.cuM); rect(g, 2, 13, 3, 19, C.cuL); rect(g, 6, 13, 6, 19, C.cuD); for (const y of [14, 16, 18]) rect(g, 2, y, 6, y, C.cuD);
  // la corda, dritta fra le due punte
  linea(g, 20, 2, 20, 30, 1, C.corda);
  contorno(g); return g;
}

// la versione piccola (16x16) per l'HUD quando è piccolo (la matrice 2304x768): un 32x32 dimezzato a campione sporcherebbe i
// pixel, quindi si riduce a blocchi 2x2 (opaco se almeno 2 pixel su 4, colore più frequente, a parità il più chiaro) e il
// contorno si rifà da capo a 16 px
const lum = c => c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11;
function riduci(g) {
  const h = N / 2, r = Array.from({ length: h * h }, () => null);
  for (let by = 0; by < h; by++) for (let bx = 0; bx < h; bx++) {
    const px = [get(g, bx * 2, by * 2), get(g, bx * 2 + 1, by * 2), get(g, bx * 2, by * 2 + 1), get(g, bx * 2 + 1, by * 2 + 1)].filter(Boolean);
    if (px.length < 2) continue;
    const conta = new Map(); for (const p of px) { const k = p.join(','); conta.set(k, { p, n: (conta.get(k)?.n || 0) + 1 }); }
    r[by * h + bx] = [...conta.values()].sort((a, b) => b.n - a.n || lum(b.p) - lum(a.p))[0].p;
  }
  return r;
}

const ICONE = { fists: pugni, whip: frusta, mace: mazza, saber: sciabola, bow: arco };

// ── PNG (senza dipendenze) ──────────────────────────────────────────────────
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc = b => { let c = 0xffffffff; for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function chunk(tipo, dati) { const l = Buffer.alloc(4); l.writeUInt32BE(dati.length); const td = Buffer.concat([Buffer.from(tipo), dati]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); }
function png(w, h, rgba) {
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4); }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}
const aRgba = (g, n = N) => { const b = Buffer.alloc(n * n * 4); g.forEach((p, i) => { if (p) { b[i * 4] = p[0]; b[i * 4 + 1] = p[1]; b[i * 4 + 2] = p[2]; b[i * 4 + 3] = 255; } }); return b; };

const out = path.resolve(__dirname, '../../assets/hud'); fs.mkdirSync(out, { recursive: true });
const icone = {};
const piccole = {};
for (const [k, f] of Object.entries(ICONE)) {
  icone[k] = f(); fs.writeFileSync(path.join(out, 'arma-' + k + '.png'), png(N, N, aRgba(icone[k])));
  SENZA_CONTORNO = true; const nuda = f(); SENZA_CONTORNO = false;
  const p16 = riduci(nuda);
  { const h = N / 2, pieno = p16.map(p => !!p);                                 // il contorno a 16 px
    for (let y = 0; y < h; y++) for (let x = 0; x < h; x++) if (!pieno[y * h + x] && [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => x + dx >= 0 && y + dy >= 0 && x + dx < h && y + dy < h && pieno[(y + dy) * h + x + dx])) p16[y * h + x] = C.nero; }
  piccole[k] = p16; fs.writeFileSync(path.join(out, 'arma-' + k + '-16.png'), png(N / 2, N / 2, aRgba(p16, N / 2)));
}
console.log('scritte', Object.keys(icone).map(k => 'arma-' + k + '[-16].png').join(', '), 'in', out);

// anteprima: le cinque icone a 10x sul blu notte dei riquadri, e a 1x come nel gioco
const prev = process.argv[2];
if (prev) {
  fs.mkdirSync(prev, { recursive: true });
  const Z = 10, gap = 24, W = Object.keys(icone).length * (N * Z + gap) + gap, H = N * Z + gap * 2 + N + gap + 130;
  const b = Buffer.alloc(W * H * 4); for (let i = 0; i < W * H; i++) { b[i * 4] = 4; b[i * 4 + 1] = 23; b[i * 4 + 2] = 55; b[i * 4 + 3] = 255; }
  Object.values(icone).forEach((g, n) => {
    const ox = gap + n * (N * Z + gap), oy = gap;
    g.forEach((p, i) => { if (!p) return; const x = i % N, y = i / N | 0;
      for (let a = 0; a < Z; a++) for (let c = 0; c < Z; c++) { const o = ((oy + y * Z + a) * W + ox + x * Z + c) * 4; b[o] = p[0]; b[o + 1] = p[1]; b[o + 2] = p[2]; }
      const o1 = ((oy + N * Z + gap + y) * W + ox + x) * 4; b[o1] = p[0]; b[o1 + 1] = p[1]; b[o1 + 2] = p[2]; });
    (Object.values(piccole)[n]).forEach((p, i) => { if (!p) return; const x = i % (N / 2), y = i / (N / 2) | 0;
      for (let a = 0; a < 6; a++) for (let c = 0; c < 6; c++) { const o = ((oy + N * Z + gap + 40 + y * 6 + a) * W + ox + 60 + x * 6 + c) * 4; b[o] = p[0]; b[o + 1] = p[1]; b[o + 2] = p[2]; } });
  });
  fs.writeFileSync(path.join(prev, 'icone-anteprima.png'), png(W, H, b));
  console.log('anteprima in', path.join(prev, 'icone-anteprima.png'));
}
