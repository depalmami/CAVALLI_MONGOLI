// ORECCHIO — gira nel thread audio, non in quello del gioco.
//
// Perché un worklet e non l'AnalyserNode e basta: l'analyser si legge a ogni
// frame (16 ms) su una finestra di 43 ms, quindi un colpo di cassa arriva
// spalmato e in ritardo variabile. Qui invece ogni campione passa per tre filtri
// e l'energia si misura a pacchetti di 256 campioni (~5 ms): il colpo esce con il
// suo istante VERO, in tempo-contesto audio, e la pagina lo converte nel proprio.
//
// Tre voci, scelte per la batteria:
//   0 cassa       passa-basso  100 Hz, 4° ordine (due biquad in serie)
//   1 rullante    passa-banda 2500 Hz
//   2 charleston  passa-alto  8000 Hz
// La cassa deve anche DOMINARE: un colpo vale come cassa solo se nei bassi c'è più
// energia che nella banda del rullante. Senza questa regola, dopo una pausa lunga
// (soglia ormai bassissima) la rullata della salita passava per cassa e faceva
// scattare un drop finto — verificato sul pezzo di prova.
// Per ogni voce: energia in dB → "flusso" (quanto è salita rispetto ai pacchetti
// prima) → soglia che si adatta alla musica → picco locale → colpo.
// In più manda alla pagina, a gruppi, la curva del flusso: serve per stimare il
// tempo (BPM) e la fase del battito.

const HOP = 256;                  // campioni per pacchetto di analisi
const GRUPPO = 16;                // pacchetti per messaggio di curva (~85 ms)
const VOCI = [
  { tipo: 'lowpass',  f: 100,  q: 0.71, ordine: 2, minD: 6, refrattario: 0.14 },
  { tipo: 'bandpass', f: 2500, q: 0.9,  ordine: 1, minD: 5, refrattario: 0.11 },
  { tipo: 'highpass', f: 8000, q: 0.7,  ordine: 1, minD: 4, refrattario: 0.06 },
];
const DOMINIO_CASSA_DB = 0;       // bassi − medi al momento del colpo, in dB
const K_SOGLIA = 2.2;             // deviazioni standard sopra la media del flusso
const MEMORIA_S = 0.75;           // la soglia "ricorda" circa così tanto
const SOTTO_PICCO_DB = 38;        // sotto il massimo recente di tanto = rumore di fondo, niente colpi

function biquad(tipo, f0, q, fs) {
  const w0 = 2*Math.PI*f0/fs, c = Math.cos(w0), a = Math.sin(w0)/(2*q);
  let b0, b1, b2;
  if (tipo === 'lowpass')       { b0 = (1-c)/2; b1 = 1-c;     b2 = (1-c)/2; }
  else if (tipo === 'highpass') { b0 = (1+c)/2; b1 = -(1+c);  b2 = (1+c)/2; }
  else                          { b0 = a;       b1 = 0;       b2 = -a; }      // passa-banda, picco 0 dB
  const a0 = 1 + a;
  return { b0: b0/a0, b1: b1/a0, b2: b2/a0, a1: -2*c/a0, a2: (1-a)/a0, z1: 0, z2: 0 };
}

class Orecchio extends AudioWorkletProcessor {
  constructor() {
    super();
    // per ogni voce una catena di biquad uguali (la cassa ne ha due: 4° ordine)
    this.filtri = VOCI.map(v => Array.from({ length: v.ordine }, () => biquad(v.tipo, v.f, v.q, sampleRate)));
    this.lv = new Float64Array(3);            // livelli (dB) del pacchetto appena chiuso
    this.lPrec = new Float64Array(3).fill(-120);   // …e di quello prima: è lì che si decide il colpo
    this.acc = new Float64Array(3);
    this.n = 0;
    this.hopS = HOP / sampleRate;
    this.alfa = 1 - Math.exp(-this.hopS / MEMORIA_S);
    this.voci = VOCI.map(v => ({
      l: [-120, -120, -120],      // ultime tre energie in dB
      d1: 0, d2: 0,               // flusso dei due pacchetti precedenti (per il picco locale)
      media: 0, media2: 0,        // statistiche del flusso per la soglia adattiva
      picco: -120,                // massimo recente in dB (scende piano)
      ultimo: -1,                 // istante dell'ultimo colpo (s, tempo-contesto)
      refr: v.refrattario, minD: v.minD,
    }));
    this.curvaC = new Float32Array(GRUPPO);   // flusso della cassa
    this.curvaO = new Float32Array(GRUPPO);   // flusso complessivo (per il tempo)
    this.g = 0;
    this.port.postMessage({ tipo: 'pronto', hopS: this.hopS, sampleRate });
  }

  fineHop(t) {
    const d = [0, 0, 0], lv = this.lv, lp = this.lPrec;
    for (let k = 0; k < 3; k++) lv[k] = 10 * Math.log10(this.acc[k] / HOP + 1e-12);
    for (let k = 0; k < 3; k++) {
      const v = this.voci[k];
      const l = lv[k];
      // flusso: salita rispetto alla media dei tre pacchetti prima, solo se positiva
      const prima = (v.l[0] + v.l[1] + v.l[2]) / 3;
      d[k] = Math.max(0, l - prima);
      v.l[2] = v.l[1]; v.l[1] = v.l[0]; v.l[0] = l;
      v.picco = Math.max(l, v.picco - 4 * this.hopS);         // scende di 4 dB al secondo

      // picco locale sul pacchetto PRECEDENTE (costa 5 ms di ritardo, evita i doppi colpi)
      const soglia = Math.max(v.minD, v.media + K_SOGLIA * Math.sqrt(Math.max(0, v.media2 - v.media*v.media)));
      const tPrec = t - this.hopS;
      const domina = k !== 0 || lp[0] > lp[1] + DOMINIO_CASSA_DB;
      if (v.d1 > soglia && v.d1 >= v.d2 && v.d1 > d[k] && domina &&
          lp[k] > v.picco - SOTTO_PICCO_DB && tPrec - v.ultimo > v.refr) {
        v.ultimo = tPrec;
        this.port.postMessage({ tipo: 'colpo', v: k, t: tPrec, f: Math.min(1, Math.max(0.15, v.d1 / 24)) });
      }
      v.d2 = v.d1; v.d1 = d[k];
      v.media  += (d[k] - v.media) * this.alfa;
      v.media2 += (d[k]*d[k] - v.media2) * this.alfa;
    }
    lp[0] = lv[0]; lp[1] = lv[1]; lp[2] = lv[2];
    this.curvaC[this.g] = d[0];
    this.curvaO[this.g] = d[0] + 0.6*d[1] + 0.25*d[2];
    if (++this.g === GRUPPO) {
      this.port.postMessage({ tipo: 'curva', t, c: this.curvaC.slice(), o: this.curvaO.slice() });
      this.g = 0;
    }
  }

  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    const f = this.filtri, acc = this.acc;
    for (let i = 0; i < ch.length; i++) {
      const x = ch[i];
      for (let k = 0; k < 3; k++) {
        let y = x;
        for (const q of f[k]) {
          const u = y;
          y = q.b0*u + q.z1;
          q.z1 = q.b1*u - q.a1*y + q.z2;
          q.z2 = q.b2*u - q.a2*y;
        }
        acc[k] += y*y;
      }
      if (++this.n === HOP) {
        // currentTime = inizio di questo blocco; il pacchetto finisce al campione i
        this.fineHop(currentTime + (i + 1) / sampleRate);
        this.n = 0; acc[0] = acc[1] = acc[2] = 0;
      }
    }
    return true;
  }
}

registerProcessor('orecchio', Orecchio);
