// CENTRALINA — dalla musica ai parametri, con una manopola sola: SMARMELLA 0…1.
//
// Ogni LIVELLO è un preset: valori di BASE per alcuni bersagli + VOCI che
// collegano una sorgente musicale a un bersaglio ("la cassa spinge il barile").
// La manopola scorre fra i cinque livelli e mescola i due vicini, quindi si
// passa da «Diretta» ad «APRI TUTTO» senza scatti.
//
// I bersagli si leggono da `v` (un oggetto piatto) a ogni frame. Nessun effetto
// sa da dove arriva il suo valore: domani le voci si modificano dalla console
// (Fase 5) senza toccare né la musica né gli shader.

import { BERSAGLI_POST } from './smarmella.js';

// bersagli: [min, max]. Fuori dal post: moltiplicatori della luce e FOV in gradi.
export const BERSAGLI = {
  ...Object.fromEntries(Object.entries(BERSAGLI_POST).map(([k, r]) => ['post.' + k, r])),
  'luce.bloom':       [0.2, 8],
  'luce.esposizione': [0.4, 2.2],
  'luce.sole':        [0.1, 3],
  'camera.fov':       [-4, 16],
  // il mondo (Fase 4)
  'mondo.linee':      [0, 1],      // linee del battito sull'asfalto
  'mondo.eqBordi':    [0, 1],      // equalizzatore sui cigli
  'mondo.foresta':    [0, 2],      // gli alberi crescono con la loro banda
  'mondo.led':        [0, 4],      // luci che corrono sui paletti
  'mondo.ledFlash':   [0, 4],      // lampo dei paletti
  'mondo.terreno':    [0, 3500],   // onde del terreno lontano (unità mondo)
  'mondo.laser':      [0, 1],
  'mondo.notte':      [0, 1],      // 0 tardo pomeriggio · 1 notte
  'mondo.polvere':    [0, 1],      // sbuffi sotto gli zoccoli sulla cassa
  'cavalli.tempo':    [0, 1],      // galoppo agganciato al battito
  'camera.scossa':    [0, 1],
  'camera.rollio':    [-0.6, 0.6],
};
// a riposo = il gioco di prima, esattamente
const RIPOSO = { 'post.saturazione': 1, 'post.spicchi': 6, 'luce.bloom': 1, 'luce.esposizione': 1, 'luce.sole': 1 };

// [sorgente, bersaglio, quanto]
export const LIVELLI = [
  { nome: 'Diretta', base: {}, voci: [] },
  { nome: 'Groove',
    base: { 'post.vignetta': 0.15, 'post.saturazione': 1.08, 'cavalli.tempo': 1, 'mondo.linee': 0.5, 'mondo.led': 0.3 },
    voci: [['cassa', 'post.barile', 0.06], ['cassa', 'post.aberrazione', 0.004], ['cassa', 'camera.fov', 2.5],
           ['energia', 'luce.bloom', 0.5], ['cassa', 'mondo.ledFlash', 0.4]] },
  { nome: 'Festa',
    base: { 'post.vignetta': 0.25, 'post.saturazione': 1.2, 'post.colata': 0.12, 'post.zoomFb': 0.004, 'post.grana': 0.04,
            'cavalli.tempo': 1, 'mondo.linee': 0.8, 'mondo.eqBordi': 0.6, 'mondo.foresta': 0.6, 'mondo.led': 0.6,
            'mondo.polvere': 0.5, 'mondo.notte': 0.1 },
    voci: [['cassa', 'post.barile', 0.12], ['cassa', 'post.aberrazione', 0.01], ['rullante', 'post.glitch', 0.15],
           ['bassi', 'post.zoomRadiale', 0.05], ['charleston', 'post.grana', 0.12], ['cassa', 'camera.fov', 4],
           ['energia', 'luce.bloom', 1.0], ['drop', 'post.bruciato', 0.7], ['giro', 'post.hue', 0.08],
           ['cassa', 'mondo.ledFlash', 1.0], ['bassi', 'mondo.terreno', 700], ['rullante', 'camera.scossa', 0.3],
           ['pausaLiscia', 'mondo.notte', 0.35]] },
  { nome: 'Rave',
    base: { 'post.vignetta': 0.3, 'post.saturazione': 1.45, 'post.colata': 0.3, 'post.scie': 0.55, 'post.zoomFb': 0.012,
            'post.ruotaFb': 0.004, 'post.ondaFb': 0.003, 'post.hueFb': 0.012, 'post.scanline': 0.12, 'post.tinta': 0.15,
            'cavalli.tempo': 1, 'mondo.linee': 1, 'mondo.eqBordi': 1, 'mondo.foresta': 1, 'mondo.led': 1,
            'mondo.polvere': 1, 'mondo.terreno': 300, 'mondo.laser': 0.6, 'mondo.notte': 0.35 },
    voci: [['cassa', 'post.barile', 0.2], ['cassa', 'post.aberrazione', 0.018], ['rullante', 'post.glitch', 0.4],
           ['bassi', 'post.zoomRadiale', 0.12], ['energia', 'post.colata', 0.25], ['alti', 'post.hueFb', 0.03],
           ['rullante', 'post.bruciato', 0.3], ['dopoDrop', 'post.caleido', 1.0], ['charleston', 'post.grana', 0.2],
           ['cassa', 'camera.fov', 6], ['energia', 'luce.bloom', 1.5], ['giro', 'post.hue', 0.25], ['basso', 'post.ruotaFb', 0.01],
           ['cassa', 'mondo.ledFlash', 1.5], ['bassi', 'mondo.terreno', 1500], ['rullante', 'camera.scossa', 0.6],
           ['pausaLiscia', 'mondo.notte', 0.4], ['drop', 'camera.rollio', 0.25]] },
  { nome: 'APRI TUTTO',
    base: { 'post.vignetta': 0.35, 'post.saturazione': 1.6, 'post.colata': 0.45, 'post.scie': 0.75, 'post.zoomFb': 0.022,
            'post.ruotaFb': 0.01, 'post.ondaFb': 0.007, 'post.hueFb': 0.03, 'post.spicchi': 6,
            'post.scanline': 0.22, 'post.posterizza': 0.12, 'post.tinta': 0.4,
            'cavalli.tempo': 1, 'mondo.linee': 1, 'mondo.eqBordi': 1, 'mondo.foresta': 1.6, 'mondo.led': 1.5,
            'mondo.polvere': 1, 'mondo.terreno': 600, 'mondo.laser': 1, 'mondo.notte': 0.6 },
    voci: [['cassa', 'post.barile', 0.32], ['cassa', 'post.aberrazione', 0.03], ['rullante', 'post.glitch', 0.7],
           ['bassi', 'post.zoomRadiale', 0.22], ['rullante', 'post.bruciato', 0.5], ['dopoDrop', 'post.caleido', 1.0],
           ['frase1', 'post.caleido', 1.0], ['scoppio', 'post.flash', 0.85], ['drop', 'post.tinta', 0.5],
           ['energia', 'post.colata', 0.3], ['sub', 'post.ondaFb', 0.008],
           ['alti', 'post.hueFb', 0.05], ['cassa', 'camera.fov', 9], ['energia', 'luce.bloom', 1.5], ['giro', 'post.hue', 1.0],
           ['charleston', 'post.grana', 0.3], ['basso', 'post.ruotaFb', 0.025], ['onda', 'post.spicchi', 4],
           ['cassa', 'mondo.ledFlash', 2.5], ['bassi', 'mondo.terreno', 2500], ['rullante', 'camera.scossa', 1],
           ['pausaLiscia', 'mondo.notte', 0.3], ['scoppio', 'mondo.notte', -0.6], ['drop', 'camera.rollio', 0.4]] },
];

// bersagli che fanno un LAMPO a tutto schermo: passano dal limitatore
const LAMPI = ['post.flash', 'post.bruciato'];
const SOGLIA_LAMPO = 0.35, TETTO_SOPPRESSO = 0.1, MAX_LAMPI_AL_SECONDO = 3;
const STESSO_LAMPO_MS = 60;           // strobo + luce + bruciato sullo stesso battito = UN lampo, non tre

export function creaCentralina(musica) {
  const chiavi = Object.keys(BERSAGLI);
  const v = {}, post = {};
  for (const k of chiavi) v[k] = RIPOSO[k] ?? 0;

  // sorgenti: i campi di `musica` più qualche derivata comoda
  function sorgente(nome) {
    switch (nome) {
      case 'giro': return (((musica.battuta % 8) + 8) % 8 + musica.faseBattuta) / 8;   // 0→1 su una frase da 8 battute
      case 'onda': return 0.5 - 0.5 * Math.cos(musica.fase * Math.PI * 2);           // dolce, picco a metà battito
      case 'dopoDrop': {                                     // 2 battute piene dopo il drop, poi sfuma in altre 2
        const b = musica.battito + musica.fase - dropB;
        return b < 0 || b > 16 ? 0 : b < 8 ? 1 : 1 - (b - 8) / 8;
      }
      case 'pausaLiscia': return pausaLiscia;              // pausa o salita, sfumata in ~2 s: il cielo non scatta
      case 'scoppio': return musica.drop ** 4;              // il lampo del drop: secco (~0,15 s), non mezzo secondo di bianco
      case 'frase1': return (((musica.battuta % 8) + 8) % 8) === 0 ? 1 - musica.faseBattuta : 0;   // la prima battuta di ogni frase
      default: { const x = musica[nome]; return typeof x === 'number' ? x : 0; }
    }
  }
  // valore di un bersaglio dentro UN livello
  const tmp = [{}, {}];
  function valuta(liv, out) {
    for (const k of chiavi) out[k] = liv.base[k] ?? RIPOSO[k] ?? 0;
    for (const [da, a, quanto] of liv.voci) out[a] += sorgente(da) * quanto;
  }

  // ── MANOPOLA, auto-regia ──
  let macro = 0, liscia = 0, auto = false, limita = true;
  let sezB0 = 0, dropB = -1e9, pausaLiscia = 0;
  musica.on('drop', () => { dropB = musica.battito; });
  musica.on('sezione', e => {
    sezB0 = musica.battito;
    if (auto && e.sezione === 'drop') liscia = macro = 1;     // il drop non sale piano: arriva
  });
  function bersaglioAuto() {
    const b = musica.battito - sezB0;
    switch (musica.sezione) {
      case 'pausa':  return 0.25;
      case 'salita': return 0.5 + 0.25 * Math.min(1, b / 16);
      case 'drop':   return b < 32 ? 1 : 0.75;               // 8 battute di APRI TUTTO, poi Rave
      default:       return 0.5;
    }
  }

  // ── LIMITATORE dei lampi (≤ 3 al secondo): strobo della scritta + flash/bruciato del post ──
  const lampi = [];
  const statoLampo = Object.fromEntries(LAMPI.map(k => [k, { sopra: false, soppresso: false }]));
  function chiediLampo(ora) {
    while (lampi.length && lampi[0] < ora - 1000) lampi.shift();
    if (lampi.length && ora - lampi[lampi.length - 1] < STESSO_LAMPO_MS) return true;   // è lo stesso lampo
    if (limita && lampi.length >= MAX_LAMPI_AL_SECONDO) return false;
    lampi.push(ora); return true;
  }
  function limitaLampi(ora) {
    for (const k of LAMPI) {
      const s = statoLampo[k], x = v[k];
      if (x >= SOGLIA_LAMPO && !s.sopra) { s.sopra = true; s.soppresso = !chiediLampo(ora); }
      else if (x < SOGLIA_LAMPO) { s.sopra = false; s.soppresso = false; }
      if (s.soppresso) v[k] = Math.min(x, TETTO_SOPPRESSO);
    }
  }

  function aggiorna(dt, ora) {
    const inPausa = musica.sezione === 'pausa' || musica.sezione === 'salita' ? 1 : 0;
    pausaLiscia += (inPausa - pausaLiscia) * (1 - Math.exp(-dt / 0.8));
    if (auto) macro = bersaglioAuto();
    liscia += (macro - liscia) * (1 - Math.exp(-dt / 0.25));
    if (Math.abs(macro - liscia) < 1e-4) liscia = macro;
    const pos = Math.max(0, Math.min(1, liscia)) * (LIVELLI.length - 1);
    const i = Math.min(LIVELLI.length - 2, Math.floor(pos)), f = pos - i;
    valuta(LIVELLI[i], tmp[0]); valuta(LIVELLI[i + 1], tmp[1]);
    for (const k of chiavi) {
      const [lo, hi] = BERSAGLI[k];
      v[k] = Math.max(lo, Math.min(hi, tmp[0][k] + (tmp[1][k] - tmp[0][k]) * f));
    }
    limitaLampi(ora);
    for (const k of chiavi) if (k.startsWith('post.')) post[k.slice(5)] = v[k];
  }

  return {
    v, post, LIVELLI, aggiorna, chiediLampo,
    get attiva() { return liscia > 0.001; },
    get macro() { return macro; }, get liscia() { return liscia; }, get auto() { return auto; },
    setMacro(x) { macro = Math.max(0, Math.min(1, x)); },
    livello(n) { macro = n / (LIVELLI.length - 1); },
    nomeLivello() { return LIVELLI[Math.round(liscia * (LIVELLI.length - 1))].nome; },
    setAuto(b) { auto = b; },
    setLimita(b) { limita = b; },
  };
}
