// MUSICA — le orecchie del gioco.
//
// Un orologio solo per tutto lo show. Le sorgenti lo correggono, nessuno lo
// sostituisce: così passare dal MIDI all'audio al tap non fa mai saltare un
// battito, e un cavo staccato a metà pezzo non ferma niente.
//
//   MIDI (clock di Ableton)  → tempo e fase esatti, e l'"uno" con Start/SPP
//   audio (ingresso o file)  → bande, energia, spettro, colpi; tempo e fase STIMATI
//   tap / libero             → l'orologio va da solo (120 BPM finché nessuno tappa)
//
// Il resto del gioco legge solo lo STATO (l'oggetto restituito) e si iscrive agli
// eventi con on(): non tocca mai l'audio, quindi si cambia sorgente senza toccare
// nemmeno un effetto. Il contratto è descritto nel PIANO-audioreattivo.md, §4.
//
// Tempi: tutto in millisecondi di performance.now(). I tempi dell'orologio sono
// tempi "del suono"; gli eventi però partono con l'ANTICIPO VISIVO (si calibra al
// soundcheck), perché schermo e ledwall arrivano dopo l'orecchio.

const VOCI = ['cassa', 'rullante', 'charleston'];
const RILASCIO = { cassa: 0.12, rullante: 0.10, charleston: 0.06, basso: 0.15 };   // s, decadimento degli impulsi
// note General MIDI della batteria (qualunque canale tranne quello dei comandi)
const NOTE_BATTERIA = { 35:'cassa', 36:'cassa', 37:'rullante', 38:'rullante', 39:'rullante', 40:'rullante',
                        42:'charleston', 44:'charleston', 46:'charleston' };
const CANALE_COMANDI = 16;            // riservato alla traccia cue "VISUAL" (Fase 5): mai batteria
const N_SPETTRO = 64, F_MIN = 45, F_MAX = 16000;
const BANDE = { sub: [25, 60], bassi: [60, 250], medi: [250, 2000], alti: [2000, 16000] };
const RING = 2048;                    // pacchetti di curva tenuti in memoria (~11 s)
const CONF_MINIMA = 2.2;              // sotto questa chiarezza la stima del tempo non comanda

const mod = (a, n) => ((a % n) + n) % n;
const lim = (v, a, b) => Math.max(a, Math.min(b, v));

export function creaMusica() {
  const ora = () => performance.now();

  // ── eventi ──────────────────────────────────────────────────────────────
  const ascoltatori = new Map();
  function on(nome, fn) {
    if (!ascoltatori.has(nome)) ascoltatori.set(nome, []);
    ascoltatori.get(nome).push(fn);
    return () => off(nome, fn);
  }
  function off(nome, fn) {
    const a = ascoltatori.get(nome); if (!a) return;
    const i = a.indexOf(fn); if (i >= 0) a.splice(i, 1);
  }
  function emetti(nome, dati) {
    const a = ascoltatori.get(nome); if (!a) return;
    for (const fn of a) { try { fn(dati); } catch (e) { console.error(`musica.on('${nome}')`, e); } }
  }

  // ── STATO pubblico ──────────────────────────────────────────────────────
  const m = {
    fonte: 'libero',                  // chi comanda l'orologio adesso: 'midi' | 'audio' | 'libero'
    bpm: 120, periodo: 0.5, fase: 0,
    battito: 0, inBattuta: 0, battuta: 0, faseBattuta: 0, frase: 0,
    cassa: 0, rullante: 0, charleston: 0,
    basso: 0,                         // colpo grave FUORI griglia (il basso in levare): non è una cassa
    sub: 0, bassi: 0, medi: 0, alti: 0, energia: 0, brillanza: 0,
    spettro: new Float32Array(N_SPETTRO),
    sezione: 'groove', drop: 0,
    prossimoBattito: 0,               // ms: quando VEDERE il prossimo battito (anticipo già tolto)
    livelloDb: -120, segnale: false,
    anticipoMs: 0,
  };

  // ── OROLOGIO ────────────────────────────────────────────────────────────
  // indice del battito al tempo t = ancoraB + (t − ancoraT) / periodo
  const orologio = {
    periodo: 500, ancoraT: ora(), ancoraB: 0, unoOffset: 0,
    indice(t) { return this.ancoraB + (t - this.ancoraT) / this.periodo; },
    tempoDi(b) { return this.ancoraT + (b - this.ancoraB) * this.periodo; },
    // cambia velocità SENZA saltare: la fase al tempo t resta quella che era
    nuovoPeriodo(p, t) { this.ancoraB = this.indice(t); this.ancoraT = t; this.periodo = p; },
  };
  let ultimoEmesso = -1;
  let unoNoto = '';                   // '' | 'tap' | 'midi' | 'drop': da dove sappiamo dov'è l'"uno"
  let scelta = 'auto';                // 'auto' | 'midi' | 'audio' | 'libero'
  let manoT = -1e9;                   // ultimo intervento a mano (tap/uno): l'audio non lo scavalca subito
  let ottava = 1;                     // ×2 / ÷2 sulla stima audio (errori d'ottava)

  // ── TAP ─────────────────────────────────────────────────────────────────
  let taps = [];
  function tap() {
    const t = ora();
    if (taps.length && t - taps[taps.length - 1] > 2000) taps = [];   // pausa lunga = nuova battuta
    taps.push(t); if (taps.length > 6) taps.shift();
    if (taps.length >= 2 && m.fonte !== 'midi') {
      const bpm = lim(60000 / ((taps[taps.length - 1] - taps[0]) / (taps.length - 1)), 40, 240);
      orologio.nuovoPeriodo(60000 / bpm, t);
      // con l'audio acceso il tap serve anche a correggere l'ottava della stima
      if (audioStima.bpm && taps.length >= 4) ottava = lim(2 ** Math.round(Math.log2(bpm / audioStima.bpm)), 0.25, 4);
    }
    if (m.fonte !== 'midi') { orologio.ancoraB = Math.round(orologio.indice(t)); orologio.ancoraT = t; }
    manoT = t;
  }
  // "questo è l'uno": rimette in fase il battito E la battuta
  function uno() {
    const t = ora(), r = Math.round(orologio.indice(t));
    if (m.fonte !== 'midi') { orologio.ancoraB = r; orologio.ancoraT = t; }
    orologio.unoOffset = mod(r, 4); unoNoto = 'tap'; manoT = t;
  }
  function cambiaOttava(f) {
    if (m.fonte === 'midi') return;
    if (m.fonte === 'audio') ottava = lim(ottava * f, 0.25, 4);
    else orologio.nuovoPeriodo(orologio.periodo / f, ora());
  }

  // ── AUDIO: grafo ────────────────────────────────────────────────────────
  let ctx = null, trim = null, analyser = null, worklet = null, monitor = null;
  let sorgente = null, stream = null, elemento = null, elementoSrc = null, urlOggetto = null;
  let deltaCtx = 0, deltaPronto = false;               // perf ms − tempo-contesto ms
  let hopS = 256 / 48000, hopHz = 48000 / 256;
  const audio = { attivo: false, tipo: '', nome: '', id: '', errore: '' };

  async function contesto() {
    if (!ctx) {
      ctx = new AudioContext({ latencyHint: 'interactive' });
      trim = ctx.createGain();
      analyser = ctx.createAnalyser(); analyser.fftSize = 2048; analyser.smoothingTimeConstant = 0;
      // pozzo muto verso le casse: tiene "tirati" analyser e worklet senza farli suonare
      const pozzo = ctx.createGain(); pozzo.gain.value = 0; pozzo.connect(ctx.destination);
      monitor = ctx.createGain(); monitor.gain.value = 0; monitor.connect(ctx.destination);
      trim.connect(analyser); analyser.connect(pozzo);
      await ctx.audioWorklet.addModule(new URL('./orecchio.worklet.js', import.meta.url));
      worklet = new AudioWorkletNode(ctx, 'orecchio', { numberOfInputs: 1, numberOfOutputs: 1,
        outputChannelCount: [1], channelCount: 1, channelCountMode: 'explicit', channelInterpretation: 'speakers' });
      worklet.port.onmessage = e => daWorklet(e.data);
      trim.connect(worklet); worklet.connect(pozzo);
      preparaBande();
      if (m._trimDb != null) trim.gain.value = 10 ** (m._trimDb / 20);
      monitor.gain.value = m._monitor ? 1 : 0;
      // senza un gesto il contesto nasce sospeso: riparte al primo clic o tasto
      const sveglia = () => { if (ctx.state === 'suspended') ctx.resume().catch(() => {}); };
      addEventListener('pointerdown', sveglia); addEventListener('keydown', sveglia);
    }
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});   // niente await: senza gesto resterebbe appeso
    return ctx;
  }

  function staccaSorgente() {
    if (sorgente) { try { sorgente.disconnect(); } catch {} }
    if (stream) { stream.getTracks().forEach(tr => tr.stop()); stream = null; }
    if (elemento && sorgente === elementoSrc) elemento.pause();
    sorgente = null;
    Object.assign(audio, { attivo: false, tipo: '', nome: '', id: '' });
  }

  async function ascoltaIngresso(deviceId) {
    try {
      await contesto();
      staccaSorgente();
      // senza questi tre "false" Chrome tratta la musica come una telefonata:
      // toglie l'eco, schiaccia il rumore e livella il volume — e l'analisi muore
      const vincoli = { echoCancellation: false, noiseSuppression: false, autoGainControl: false,
                        channelCount: { ideal: 2 } };
      if (deviceId) vincoli.deviceId = { exact: deviceId };
      stream = await navigator.mediaDevices.getUserMedia({ audio: vincoli, video: false });
      sorgente = ctx.createMediaStreamSource(stream);
      sorgente.connect(trim);                          // MAI verso le casse: sarebbe larsen
      const tr = stream.getAudioTracks()[0];
      Object.assign(audio, { attivo: true, tipo: 'ingresso', nome: tr ? tr.label : 'ingresso',
                             id: (tr && tr.getSettings().deviceId) || deviceId || '', errore: '' });
      azzeraAnalisi();
      return audio.nome;
    } catch (e) { audio.errore = e.message || String(e); throw e; }
  }

  async function ascoltaFile(fileOUrl, el) {
    try {
      await contesto();
      staccaSorgente();
      if (el && el !== elemento) { elemento = el; elementoSrc = null; }
      if (!elemento) elemento = new Audio();
      if (!elementoSrc) elementoSrc = ctx.createMediaElementSource(elemento);   // una volta sola per elemento
      if (urlOggetto) { URL.revokeObjectURL(urlOggetto); urlOggetto = null; }
      if (typeof fileOUrl === 'string') elemento.src = fileOUrl;
      else { urlOggetto = URL.createObjectURL(fileOUrl); elemento.src = urlOggetto; }
      elemento.loop = true;
      elementoSrc.connect(trim); elementoSrc.connect(monitor);
      sorgente = elementoSrc;
      Object.assign(audio, { attivo: true, tipo: 'file', nome: typeof fileOUrl === 'string' ? fileOUrl.split('/').pop() : fileOUrl.name, id: '', errore: '' });
      azzeraAnalisi();
      await elemento.play().catch(() => {});           // senza gesto partirà al primo clic
      return audio.nome;
    } catch (e) { audio.errore = e.message || String(e); throw e; }
  }

  async function elencaIngressi() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return [];
    const tutti = await navigator.mediaDevices.enumerateDevices();
    return tutti.filter(d => d.kind === 'audioinput').map(d => ({ id: d.deviceId, nome: d.label || 'ingresso senza nome' }));
  }

  // ── AUDIO: dal worklet (colpi e curva del flusso) ───────────────────────
  const ringC = new Float32Array(RING), ringO = new Float32Array(RING);
  let ringN = 0, ringT = 0;
  const coda = [];                    // colpi arrivati, smaltiti nel frame (ordine deterministico)
  const ctxAPerf = s => s * 1000 + deltaCtx;
  function daWorklet(d) {
    if (d.tipo === 'pronto') { hopS = d.hopS; hopHz = 1 / d.hopS; return; }
    if (d.tipo === 'curva') {
      for (let i = 0; i < d.c.length; i++) { ringC[ringN % RING] = d.c[i]; ringO[ringN % RING] = d.o[i]; ringN++; }
      ringT = ctxAPerf(d.t);
      return;
    }
    if (d.tipo === 'colpo') coda.push({ voce: VOCI[d.v], t: ctxAPerf(d.t), f: d.f, da: 'audio' });
  }
  function aggiornaDelta() {
    if (!ctx || ctx.state !== 'running') return;
    let d;
    if (audio.tipo === 'file' && ctx.getOutputTimestamp) {
      // file in cuffia: conta quando il campione ESCE, cioè quando lo si sente
      const ts = ctx.getOutputTimestamp();
      d = ts.performanceTime > 0 ? ts.performanceTime - ts.contextTime * 1000 : ora() - ctx.currentTime * 1000;
    } else d = ora() - ctx.currentTime * 1000;        // ingresso: il suono è GIÀ avvenuto
    deltaCtx = deltaPronto ? deltaCtx + (d - deltaCtx) * 0.05 : d;
    deltaPronto = true;
  }

  // ── AUDIO: spettro e bande, a ogni frame ────────────────────────────────
  let fft = null, onda = null, binHz = 23.4;
  const spettroBin = [];              // per ognuna delle 64 bande: [primo, ultimo] bin
  const binBande = {};
  const spettroMax = new Float32Array(N_SPETTRO).fill(-70);
  const bandeMax = { sub: -70, bassi: -70, medi: -70, alti: -70 };
  let energiaMax = -60;
  function preparaBande() {
    fft = new Float32Array(analyser.frequencyBinCount);
    onda = new Float32Array(analyser.fftSize);
    binHz = ctx.sampleRate / analyser.fftSize;
    const nb = analyser.frequencyBinCount;
    spettroBin.length = 0;
    for (let i = 0; i < N_SPETTRO; i++) {
      const f0 = F_MIN * (F_MAX / F_MIN) ** (i / N_SPETTRO), f1 = F_MIN * (F_MAX / F_MIN) ** ((i + 1) / N_SPETTRO);
      const a = lim(Math.round(f0 / binHz), 1, nb - 1);
      spettroBin.push([a, lim(Math.max(a, Math.round(f1 / binHz) - 1), 1, nb - 1)]);
    }
    for (const k in BANDE) binBande[k] = [lim(Math.round(BANDE[k][0] / binHz), 1, nb - 1), lim(Math.round(BANDE[k][1] / binHz), 1, nb - 1)];
  }
  let bancoDb = -120;
  function azzeraAnalisi() {
    // una sorgente nuova riparte da zero anche con la storia delle sezioni: i battiti
    // "senza cassa" di prima che l'audio arrivasse facevano scattare una pausa finta
    storia.length = 0; accDb = accDbN = 0; inSezione = 0; dallaPausa = 0; pausaMuta = false;
    if (m.sezione !== 'groove') cambiaSezione('groove');
    ringN = 0; coda.length = 0; audioStima.bpm = 0; audioStima.agganciato = false; audioStima.conf = 0; audioStima.pendente = 0; audioStima.conta = 0;
    spettroMax.fill(-70); for (const k in bandeMax) bandeMax[k] = -70; energiaMax = -60;
  }
  const potenza = db => db > -200 ? 10 ** (db / 10) : 0;
  const segui = (v, bersaglio, dt, su, giu) => v + (bersaglio - v) * (1 - Math.exp(-dt / (bersaglio > v ? su : giu)));
  let silenzioT = 0;
  function analizza(dt) {
    analyser.getFloatFrequencyData(fft);
    analyser.getFloatTimeDomainData(onda);
    let s = 0; for (let i = 0; i < onda.length; i++) s += onda[i] * onda[i];
    m.livelloDb = 20 * Math.log10(Math.sqrt(s / onda.length) + 1e-9);
    m.segnale = m.livelloDb > -62;
    silenzioT = m.segnale ? 0 : silenzioT + dt;

    // spettro a 64 bande logaritmiche, ognuna normalizzata sul proprio massimo recente
    for (let i = 0; i < N_SPETTRO; i++) {
      const [a, b] = spettroBin[i];
      let p = 0; for (let k = a; k <= b; k++) p += potenza(fft[k]);
      const db = 10 * Math.log10(p / (b - a + 1) + 1e-20);
      spettroMax[i] = Math.max(db, spettroMax[i] - 3 * dt, -70);
      const v = db < -85 ? 0 : lim((db - (spettroMax[i] - 36)) / 36, 0, 1);
      m.spettro[i] = segui(m.spettro[i], v, dt, 0.01, 0.12);
    }
    // quattro bande + baricentro (brillanza)
    let pTot = 0, pf = 0;
    for (let k = 1; k < fft.length; k++) { const p = potenza(fft[k]); pTot += p; pf += p * k * binHz; }
    for (const k in BANDE) {
      const [a, b] = binBande[k];
      let p = 0; for (let j = a; j <= b; j++) p += potenza(fft[j]);
      const db = 10 * Math.log10(p + 1e-20);
      bandeMax[k] = Math.max(db, bandeMax[k] - 3 * dt, -75);
      const v = db < -90 ? 0 : lim((db - (bandeMax[k] - 30)) / 30, 0, 1);
      m[k] = segui(m[k], v, dt, 0.012, 0.18);
    }
    energiaMax = Math.max(m.livelloDb, energiaMax - 2 * dt, -60);
    m.energia = segui(m.energia, m.segnale ? lim((m.livelloDb - (energiaMax - 24)) / 24, 0, 1) : 0, dt, 0.06, 0.5);
    const centro = pTot > 0 ? pf / pTot : 300;
    m.brillanza = segui(m.brillanza, m.segnale ? lim(Math.log2(centro / 300) / Math.log2(6000 / 300), 0, 1) : 0, dt, 0.3, 0.3);
  }
  function spegniAnalisi(dt) {
    m.livelloDb = -120; m.segnale = false;
    for (const k of ['sub', 'bassi', 'medi', 'alti', 'energia', 'brillanza']) m[k] = segui(m[k], 0, dt, 0.1, 0.3);
    for (let i = 0; i < N_SPETTRO; i++) m.spettro[i] *= Math.exp(-dt / 0.2);
  }

  // ── AUDIO: stima del TEMPO (autocorrelazione del flusso) ────────────────
  const audioStima = { bpm: 0, conf: 0, pendente: 0, conta: 0, ultima: 0, ultimaFase: 0, errori: 0 };
  const AC_N = 700, ac = new Float32Array(AC_N), xs = new Float32Array(RING);
  function stimaTempo() {
    const N = Math.min(ringN, Math.floor(hopHz * 8), RING);
    if (N < hopHz * 4) return;
    let media = 0;
    for (let i = 0; i < N; i++) { xs[i] = ringO[(ringN - N + i) % RING]; media += xs[i]; }
    media /= N;
    for (let i = 0; i < N; i++) xs[i] -= media;
    const Lmax = Math.min(AC_N - 2, N - 2, Math.ceil(4 * 60 * hopHz / 70) + 2);
    for (let L = 0; L <= Lmax + 1; L++) {
      let s = 0; for (let i = 0; i + L < N; i++) s += xs[i] * xs[i + L];
      ac[L] = s / (N - L);
    }
    if (ac[0] <= 1e-9) return;
    const acI = L => { if (L >= Lmax) return 0; const i = Math.floor(L), f = L - i; return (ac[i] * (1 - f) + ac[i + 1] * f) / ac[0]; };
    // pettine: il periodo vero ha picchi anche a 2, 3, 4 volte; il "prior" preferisce 110–150
    const griglia = [];
    let migliore = -Infinity, iMig = 0, somma = 0, somma2 = 0;
    for (let bpm = 70; bpm <= 180; bpm += 0.5) {
      const L = 60 * hopHz / bpm;
      const pettine = acI(L) + 0.5 * acI(2 * L) + 0.33 * acI(3 * L) + 0.25 * acI(4 * L);
      const s = Math.max(0, pettine) * Math.exp(-0.5 * (Math.log2(bpm / 125) / 0.6) ** 2);
      griglia.push(s); somma += s; somma2 += s * s;
      if (s > migliore) { migliore = s; iMig = griglia.length - 1; }
    }
    const n = griglia.length, mediaS = somma / n, dev = Math.sqrt(Math.max(1e-12, somma2 / n - mediaS * mediaS));
    const conf = (migliore - mediaS) / dev;
    // raffinamento parabolico fra i punti della griglia
    let bpm = 70 + iMig * 0.5;
    if (iMig > 0 && iMig < n - 1) {
      const a = griglia[iMig - 1], b = griglia[iMig], c = griglia[iMig + 1], den = a - 2 * b + c;
      if (den < 0) bpm += 0.5 * lim(0.5 * (a - c) / den, -0.5, 0.5);
    }
    audioStima.conf += (conf - audioStima.conf) * 0.4;
    if (conf < CONF_MINIMA) return;
    // isteresi: piccoli scarti si inseguono dolcemente, un tempo nuovo deve confermarsi 3 volte
    if (!audioStima.bpm) audioStima.bpm = bpm;
    else if (Math.abs(bpm / audioStima.bpm - 1) < 0.03) audioStima.bpm += (bpm - audioStima.bpm) * 0.3;
    else {
      if (audioStima.pendente && Math.abs(bpm / audioStima.pendente - 1) < 0.02) audioStima.conta++;
      else { audioStima.pendente = bpm; audioStima.conta = 1; }
      if (audioStima.conta >= 3) { audioStima.bpm = bpm; audioStima.conta = 0; }
    }
  }

  // ── AUDIO: stima della FASE (dove cadono i battiti nella curva della cassa) ─
  const curvaFase = pos => {         // pos = pacchetti PRIMA dell'ultimo, interpolato e un po' sfumato
    const leggi = p => {
      const i = Math.floor(p); if (i < 0 || i >= Math.min(ringN, RING) - 1) return 0;
      const f = p - i, a = (ringN - 1 - i) % RING, b = (ringN - 2 - i + RING) % RING;
      return (ringC[a] + 0.3 * ringO[a]) * (1 - f) + (ringC[b] + 0.3 * ringO[b]) * f;
    };
    return 0.25 * leggi(pos - 1) + 0.5 * leggi(pos) + 0.25 * leggi(pos + 1);
  };
  function stimaFase() {
    const P = orologio.periodo / 1000 * hopHz;
    const W = Math.min(ringN, Math.floor(hopHz * 4), RING);
    if (W < P * 3) return null;
    const K = Math.floor((W - P) / P);
    let migliore = -1, phiMig = 0;
    for (let phi = 0; phi < P; phi += 0.5) {
      let s = 0, w = 1;
      for (let k = 0; k <= K; k++) { s += w * curvaFase(phi + k * P); w *= 0.85; }
      if (s > migliore) { migliore = s; phiMig = phi; }
    }
    return migliore > 0 ? ringT - phiMig * hopS * 1000 : null;   // istante dell'ultimo battito stimato
  }

  // ── MIDI ────────────────────────────────────────────────────────────────
  const midi = { attivo: false, porte: [], errore: '', ticks: 0, base: 0, tT: [], tI: [], ultimoTick: -1e9,
                 inAttesaStart: false, posizionato: false, corre: false, bpm: 0 };
  const batteriaMidiT = { cassa: -1e9, rullante: -1e9, charleston: -1e9 };
  let accessoMidi = null;
  async function attivaMidi() {
    try {
      if (!navigator.requestMIDIAccess) throw new Error('Web MIDI non disponibile in questo browser');
      accessoMidi = await navigator.requestMIDIAccess({ sysex: false });
      const collega = () => {
        midi.porte = [];
        for (const inp of accessoMidi.inputs.values()) { inp.onmidimessage = daMidi; midi.porte.push(inp.name); }
      };
      collega(); accessoMidi.onstatechange = collega;
      midi.attivo = true; midi.errore = '';
      return midi.porte;
    } catch (e) { midi.errore = e.message || String(e); throw e; }
  }
  function daMidi(e) {
    const d = e.data, t = e.timeStamp || ora(), st = d[0];
    if (st === 0xF8) return tickMidi(t);
    if (st === 0xFA) { midi.inAttesaStart = true; midi.corre = true; return; }   // Start: il prossimo tick è l'"uno"
    if (st === 0xFB) { midi.corre = true; return; }
    if (st === 0xFC) { midi.corre = false; return; }
    if (st === 0xF2) {                                  // Song Position Pointer, in sedicesimi
      midi.ticks = (d[1] | (d[2] << 7)) * 6;
      midi.base = Math.max(ultimoEmesso + 1 - Math.ceil(midi.ticks / 24), Math.round(orologio.indice(t) - midi.ticks / 24));
      orologio.unoOffset = mod(midi.base, 4); unoNoto = 'midi';
      midi.posizionato = true; midi.tT.length = midi.tI.length = 0;
      return;
    }
    const tipo = st & 0xF0, canale = (st & 0x0F) + 1;
    if (tipo === 0x90 && d[2] > 0) {
      const voce = canale !== CANALE_COMANDI && NOTE_BATTERIA[d[1]];
      if (voce) { batteriaMidiT[voce] = t; coda.push({ voce, t, f: d[2] / 127, da: 'midi' }); }
      emetti('nota', { nota: d[1], vel: d[2], canale, t });
    } else if (tipo === 0xB0) emetti('cc', { cc: d[1], valore: d[2], canale, t });
  }
  function tickMidi(t) {
    const buco = t - midi.ultimoTick > 1000;
    if (midi.inAttesaStart) {
      // dopo uno Start il primo tick è l'"uno" del brano
      midi.ticks = 0;
      midi.base = Math.max(ultimoEmesso + 1, Math.round(orologio.indice(t)));
      orologio.unoOffset = mod(midi.base, 4); unoNoto = 'midi';
      midi.inAttesaStart = false;
    } else if (buco && !midi.posizionato) {
      // clock ripreso dopo un buco, senza Start né posizione: la fase dentro il
      // battito non la sa nessuno — si riparte da qui e si corregge con U
      midi.ticks = 0;
      midi.base = Math.max(ultimoEmesso + 1, Math.round(orologio.indice(t)));
    }
    if (buco || midi.posizionato) { midi.tT.length = midi.tI.length = 0; }
    midi.posizionato = false;
    const i = midi.ticks++;
    midi.tT.push(t); midi.tI.push(i);
    if (midi.tT.length > 48) { midi.tT.shift(); midi.tI.shift(); }
    midi.ultimoTick = t;
    const n = midi.tT.length;
    if (n < 6) return;
    // retta dei minimi quadrati sugli ultimi tick: il jitter del singolo tick sparisce
    const t0 = midi.tT[0], i0 = midi.tI[0];
    let sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (let k = 0; k < n; k++) { const x = midi.tI[k] - i0, y = midi.tT[k] - t0; sx += x; sy += y; sxx += x * x; sxy += x * y; }
    const b = (n * sxy - sx * sy) / (n * sxx - sx * sx), a = (sy - b * sx) / n;
    if (!(b > 0)) return;
    midi.bpm = 60000 / (24 * b);
    if (i % 24 === 0 && m.fonte === 'midi') {
      orologio.periodo = 24 * b;
      orologio.ancoraT = t0 + a + b * (i - i0);
      orologio.ancoraB = midi.base + i / 24;
    }
  }

  // ── COLPI (dall'audio o dal MIDI) ───────────────────────────────────────
  const colpiRecenti = [];
  const diag = { colpi: [], battiti: [], stime: [] };          // per i test headless
  const tieni = (arr, x, n = 2000) => { arr.push(x); if (arr.length > n) arr.shift(); };
  function applicaColpo(c, t) {
    if (c.da === 'audio' && t - batteriaMidiT[c.voce] < 4000) return;   // se il MIDI suona la batteria, comanda lui
    // a tempo agganciato, un colpo grave lontano dalla griglia è il basso in levare,
    // non la cassa: nel pezzo di prova erano METÀ delle "casse" rilevate
    if (c.voce === 'cassa' && c.da === 'audio' && m.fonte !== 'libero') {
      const b = orologio.indice(c.t);
      if (Math.abs(b - Math.round(b)) > 0.25) c = { ...c, voce: 'basso' };
    }
    m[c.voce] = Math.max(m[c.voce], c.f);
    colpiRecenti.push(c);
    tieni(diag.colpi, c);
    if (c.voce === 'cassa') forseDrop(c, t);
    emetti(c.voce, c);
  }

  // ── SEZIONI: pausa / salita / groove / drop ─────────────────────────────
  const storia = [];                  // per battito: { cassa, db }
  let accDb = 0, accDbN = 0, inSezione = 0, dallaPausa = 0, pausaMuta = false;
  function cambiaSezione(s) {
    if (s === m.sezione) return;
    const prima = m.sezione;
    m.sezione = s; inSezione = 0;
    if (s === 'pausa' && prima !== 'salita') dallaPausa = 0;
    emetti('sezione', { sezione: s, prima });
    if (s === 'drop') { m.drop = 1; emetti('drop', { battito: m.battito }); }
  }
  // le sezioni hanno senso solo se l'orologio segue DAVVERO la musica: col tempo
  // libero le casse non cadono sui battiti e ogni battuta sembrerebbe una pausa
  const sorgenteCasse = t => m.fonte !== 'libero' &&
    ((audio.attivo && silenzioT < 8) || t - batteriaMidiT.cassa < 8000);
  // il DROP non si aspetta: scatta sulla PRIMA cassa dopo una pausa lunga, se cade
  // sull'"uno" (o su un battito qualunque, finché l'uno non lo sappiamo).
  function forseDrop(c, t) {
    if ((m.sezione !== 'pausa' && m.sezione !== 'salita') || dallaPausa < 10 || pausaMuta || !sorgenteCasse(t)) return;
    const b = orologio.indice(c.t), r = Math.round(b);
    if (Math.abs(b - r) > 0.3) return;
    if (unoNoto && mod(r - orologio.unoOffset, 4) !== 0) return;
    if (!unoNoto) { orologio.unoOffset = mod(r, 4); unoNoto = 'drop'; }   // i drop cadono sull'uno: lo impariamo
    cambiaSezione('drop');
  }
  function chiudiBattito(n, t) {
    // il battito n−1 è finito da un pezzo: le sue casse (anche quelle rilevate in ritardo) sono arrivate
    const tb = orologio.tempoDi(n - 1), P = orologio.periodo;
    while (colpiRecenti.length && colpiRecenti[0].t < t - 4000) colpiRecenti.shift();
    const cassa = colpiRecenti.some(c => c.voce === 'cassa' && Math.abs(c.t - tb) < 0.3 * P);
    storia.push({ cassa, db: accDbN ? accDb / accDbN : -120 }); accDb = accDbN = 0;
    if (storia.length > 64) storia.shift();
    if (!sorgenteCasse(t)) { cambiaSezione('groove'); return; }
    inSezione++; dallaPausa++;
    const casse = k => storia.slice(-k).filter(s => s.cassa).length;
    const mediaDb = (da, a) => { const s = storia.slice(Math.max(0, storia.length - a), storia.length - da); return s.length ? s.reduce((x, y) => x + y.db, 0) / s.length : -120; };
    const delta = mediaDb(0, 4) - mediaDb(4, 8);
    switch (m.sezione) {
      case 'groove': case 'drop':
        // una battuta intera senza cassa = pausa (prima erano 8 battiti: arrivava 3 s dopo)
        // (non appena entrati: dopo un drop la storia ha ancora i battiti muti di prima)
        if (inSezione >= 4 && storia.length >= 4 && casse(4) === 0) { cambiaSezione('pausa'); pausaMuta = mediaDb(0, 4) < -55; }
        else if (m.sezione === 'drop' && inSezione >= 64) cambiaSezione('groove');
        break;
      case 'pausa':
        pausaMuta = pausaMuta && mediaDb(0, 4) < -55;
        if (casse(4) >= 3) cambiaSezione('groove');          // tornata senza drop (o dopo il silenzio fra due pezzi)
        else if (inSezione >= 4 && delta > 1.5) cambiaSezione('salita');
        break;
      case 'salita':
        if (casse(4) >= 3) cambiaSezione(dallaPausa >= 10 ? 'drop' : 'groove');
        else if (delta < -3) cambiaSezione('pausa');
        break;
    }
  }

  // ── CICLO: da chiamare a ogni frame ─────────────────────────────────────
  let tPrec = ora();
  function emettiBattito(k, t) {
    chiudiBattito(k, t);
    const inBattuta = mod(k - orologio.unoOffset, 4);
    tieni(diag.battiti, { b: k, t: orologio.tempoDi(k), inBattuta });
    emetti('battito', { battito: k, inBattuta });
    if (inBattuta === 0) {
      const battuta = Math.floor((k - orologio.unoOffset) / 4);
      emetti('battuta', { battuta });
      if (mod(battuta, 8) === 0) emetti('frase', { frase: Math.floor(battuta / 8) });
    }
  }
  function aggiorna() {
    const t = ora(), dt = Math.min(0.1, Math.max(0, (t - tPrec) / 1000));
    tPrec = t;
    aggiornaDelta();
    if (audio.tipo === 'banco') {                     // banco di prova offline: il livello lo dà il test
      m.livelloDb = bancoDb; m.segnale = bancoDb > -62; silenzioT = m.segnale ? 0 : silenzioT + dt;
      accDb += m.livelloDb; accDbN++;
    } else if (audio.attivo && analyser && ctx.state === 'running') {
      analizza(dt);
      accDb += m.livelloDb; accDbN++;
    } else spegniAnalisi(dt);

    while (coda.length) applicaColpo(coda.shift(), t);
    for (const v in RILASCIO) m[v] *= Math.exp(-dt / RILASCIO[v]);
    m.drop *= Math.exp(-dt / 0.6);

    // chi comanda l'orologio
    const midiVivo = t - midi.ultimoTick < 400 && midi.tT.length >= 6;
    const audioVivo = audio.attivo && silenzioT < 2 && audioStima.bpm > 0 && audioStima.conf >= CONF_MINIMA * 0.8;
    const vuole = scelta === 'auto' ? (midiVivo ? 'midi' : audioVivo ? 'audio' : 'libero') : scelta;
    m.fonte = (vuole === 'midi' && !midiVivo) || (vuole === 'audio' && !audioVivo) ? 'libero' : vuole;

    if (audio.attivo && t - audioStima.ultima > 500) {
      audioStima.ultima = t; stimaTempo();
      if (audioStima.bpm) tieni(diag.stime, { t, bpm: audioStima.bpm, conf: audioStima.conf }, 600);
    }
    if (m.fonte === 'audio') {
      const p = 60000 / lim(audioStima.bpm * ottava, 40, 240);
      if (Math.abs(p / orologio.periodo - 1) > 0.0005) orologio.nuovoPeriodo(orologio.periodo + (p - orologio.periodo) * 0.5, t);
      // senza casse (pausa, salita) la curva ha solo charleston e rullate, spesso in
      // levare: la fase NON si corregge e l'orologio tira dritto come un volano.
      // Le casse devono esserci ADESSO: con una finestra di 4 s le ultime casse prima
      // della pausa tenevano aperta la correzione proprio mentre arrivavano i levare.
      const casseOra = colpiRecenti.reduce((n, c) => n + (c.voce === 'cassa' && t - c.t < 2000), 0);
      if (t - audioStima.ultimaFase > 250 && t - manoT > 3000 && (casseOra >= 3 || !audioStima.agganciato)) {
        audioStima.ultimaFase = t;
        const tb = stimaFase();
        if (tb != null) {
          const b = orologio.indice(tb), err = (b - Math.round(b)) * orologio.periodo;   // ms: + = l'orologio è in anticipo
          audioStima.errori = Math.abs(err) > 0.3 * orologio.periodo ? audioStima.errori + 1 : 0;
          orologio.ancoraT += err * (audioStima.errori >= 8 ? 1 : 0.25);   // riaggancio brusco solo dopo 2 s coerenti
          if (Math.abs(err) < 0.1 * orologio.periodo) audioStima.agganciato = true;
        }
      }
    }

    // l'orologio → eventi (con l'anticipo visivo); mai raffiche di battiti arretrati
    const bA = orologio.indice(t + m.anticipoMs), n = Math.floor(bA);
    if (n > ultimoEmesso) {
      for (let k = Math.max(ultimoEmesso + 1, n - 1); k <= n; k++) emettiBattito(k, t);
      ultimoEmesso = n;
    }
    m.fase = bA - n;
    m.battito = n;
    m.inBattuta = mod(n - orologio.unoOffset, 4);
    m.faseBattuta = (m.inBattuta + m.fase) / 4;
    m.battuta = Math.floor((n - orologio.unoOffset) / 4);
    m.frase = Math.floor(m.battuta / 8);
    m.periodo = orologio.periodo / 1000;
    m.bpm = 60 / m.periodo;
    m.prossimoBattito = orologio.tempoDi(n + 1) - m.anticipoMs;
  }

  function stato() {
    return {
      fonte: m.fonte, scelta, ottava, unoNoto,
      audio: { ...audio, contesto: ctx ? ctx.state : 'spento', bpm: audioStima.bpm, conf: audioStima.conf },
      midi: { attivo: midi.attivo, porte: midi.porte.slice(), errore: midi.errore, bpm: midi.bpm,
              clock: ora() - midi.ultimoTick < 400, corre: midi.corre },
    };
  }

  return Object.assign(m, {
    on, off, aggiorna, tap, uno, raddoppia: () => cambiaOttava(2), dimezza: () => cambiaOttava(0.5),
    ascoltaIngresso, ascoltaFile, ferma: staccaSorgente, elencaIngressi, attivaMidi, stato, diag,
    setScelta(s) { scelta = s; },
    setTrimDb(db) { if (trim) trim.gain.value = 10 ** (db / 20); m._trimDb = db; },
    setAnticipo(ms) { m.anticipoMs = ms; },
    setMonitor(b) { m._monitor = b; if (monitor) monitor.gain.value = b ? 1 : 0; },
    forzaSezione: cambiaSezione,
    get contesto() { return ctx; },
    _daMidi: daMidi,                  // per i test: messaggi MIDI finti
    // banco di prova offline (Node): il worklet gira fuori dal browser e i suoi
    // messaggi entrano da qui, col livello calcolato dal test
    _banco: { daWorklet, attiva() { Object.assign(audio, { attivo: true, tipo: 'banco', nome: 'banco' }); azzeraAnalisi(); },
              livello(db) { bancoDb = db; } },
  });
}
