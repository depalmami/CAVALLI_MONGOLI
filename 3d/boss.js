// IL BOSS — il coccodrillo dell'etichetta, livello bonus dopo Karakorum.
//
// È un COSTUME, come il cavallo di cartone del giocatore: la testa-logo (la scalinata) portata in spalla e dietro una
// fila di spicchi, ognuno con le gambe di chi lo porta. Il modello (assets/models/boss/coccodrillo.glb, generato da
// tools/boss/modello_parata.py) non ha scheletro: sono pezzi rigidi con l'origine nel loro giunto, e qui li si muove
// a codice. Gli spicchi sono un TRENO SULLA STRADA: ogni giunto prende posto e quota dal tracciato, quindi il corpo
// lungo 12 m segue curve e salite da solo, senza uscire di carreggiata in curva.
//
// LA BOCCA si apre: la testa è divisa in Cranio e Mascella (tools/boss/taglia_bocca.py) e la mascella scende.
// Si apre mentre carica un morso — è l'avviso — e si richiude di scatto sul colpo.
//
// IL SORPASSO: ogni tanto il Boss allunga, ci passa davanti, FA DIETROFRONT e ci corre incontro all'indietro,
// faccia a faccia, mordendo di fronte. Il dietrofront è quello di un serpente: la testa fa una curva a U e il corpo
// la segue passando tutto dallo stesso punto (vedi `gamma`). Dopo due o tre morsi rifà la U e torna a correre dritto.
//
// Il modulo non sa niente del resto del gioco: riceve la strada (posToWorld), lo stato del giocatore a ogni passo e
// due funzioni da chiamare — `colpisci` quando un suo colpo va a segno, `evento` quando cambia fase o cade.
// Al combattimento che c'è già si presenta come un rivale: `boss.o` ha pos, lat, health, state e un actor.
//
// REGOLA DEL LIVELLO 0: qui niente batte a tempo. Se un giorno il Boss si lega alla musica, passa da un bersaglio
// della centralina (3d/centralina.js), mai da musica.* direttamente.
//
// Assi del modello: +X muso, +Y alto, +Z destra, in metri. Gioco: 1 m = 1000 unità.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export const BOSS = {
  nome: 'IL COCCODRILLO',                       // ASCII: va nell'HUD a pixel
  url: 'assets/models/boss/coccodrillo.glb',
  // TARATURA (10 nov 2026, misurata col giocatore di prova): con 1500 di vita uno che non sbaglia un colpo lo
  // abbatteva in 28 s. A pugni si fanno al massimo ~65 danni al secondo standogli sempre addosso; un umano la metà.
  // (11 nov 2026) Col sorpasso e il faccia a faccia si mena meno: a 2600 il pilota ci metteva 130 s e il 70% del tratto.
  vita: 2200,                                   // 110 pugni; la sciabola ne vale 6 l'una
  danni: { morso: 18, coda: 15, sbandata: 12, fauci: 20 },
  attesa: { 1: [3.0, 1.2], 2: [2.4, 1.0], 3: [1.7, 0.8] },   // secondi fra un attacco e l'altro: [minimo, casuale in più]
  scorta: { 1: 0, 2: 1, 3: 2 },                 // quanti predoni lo accompagnano, per fase
  sorpassoOgni: { 1: 2, 2: 2, 3: 1 },           // dopo quante mosse normali ci passa davanti e si gira
  morsiDiFronte: { 1: 2, 2: 2, 3: 3 },          // quanti morsi tira faccia a faccia prima di rigirarsi
  durataMorte: 2.8,
};

// LA TAGLIA. Il modello è fatto a misura d'uomo (12 m); in gioco è più grande di un terzo: un Boss, e sullo schermo
// del live deve riempire. Le zone degli attacchi sono scritte per la taglia 1 e si leggono in «misure del corpo»
// (la distanza divisa per SCALA): cambiando SCALA resta tutto in proporzione.
const SCALA = 1.35;
const K = 1000 * SCALA;         // metri del modello → unità di gioco
const DAVANTI0 = 2940;          // a taglia 1: dal collo alla punta del muso
const DAVANTI = DAVANTI0 * SCALA;
const DIETRO = 9200 * SCALA;    // dal collo alla punta della coda
const D_CORPO = 6600 * SCALA;   // dal collo alla fine degli spicchi: oltre c'è solo la coda, che non fa muro
const SEMI_LARG = 0.25 * SCALA; // mezza larghezza del corpo, in unità di playerX (strada larga 6 m)
const APERTURA = 0.5;           // radianti: quanto scende la mascella a bocca spalancata (~29°)
const STRISCIO = 8000;          // unità/s: quanto corre il corpo lungo la curva a U mentre si gira
const MUSO_DI_FRONTE = 2600;    // faccia a faccia: quanto sta davanti al giocatore la punta del muso
const DI_SBIECO = 0.75;         // faccia a faccia sta spostato di lato (2,2 m): dritto davanti lo copriva il cavallo di chi guida
// faccia a faccia SI IMPENNA: testa e primi spicchi salgono (unità di gioco, per giunto) e chi li porta va sui trampoli
const IMPENNATA = [600, 350, 150];
// dove vuole stare rispetto al giocatore (distanza collo − giocatore): alla testa per mordere, alla coda per frustare
// «fianco» è verso il fondo del corpo: così il Boss sta quasi tutto DAVANTI alla camera e si vede intero, invece di
// fare da muro accanto a chi guida (a 3000 il corpo copriva un terzo dello schermo)
// «sorpasso»: basta che il collo sia 8,5 m avanti; la curva a U parte lì, vicina, e si allontana mentre il corpo la percorre
const GDES = { testa: -900 * SCALA, coda: 7600 * SCALA, fianco: 5200 * SCALA, sorpasso: 9500 * SCALA, fronte: DAVANTI + MUSO_DI_FRONTE };
const limit = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const dolce = t => { t = limit(t, 0, 1); return t * t * (3 - 2 * t); };

export function creaBoss({ scene, posToWorld, gapTo, interpWrap, MAX_SPEED, TRACK_LENGTH, ROAD_WIDTH, colpisci, evento }) {
  const gruppo = new THREE.Group(); gruppo.visible = false; scene.add(gruppo);
  // il punto del corpo più vicino al giocatore: lì compaiono scintille, scritte del danno e frecce
  const punto = new THREE.Group(); scene.add(punto);
  const avvolgi = p => ((p % TRACK_LENGTH) + TRACK_LENGTH) % TRACK_LENGTH;

  // ── come lo vede il combattimento: un rivale ────────────────────────────
  let lampo = 0, scossa = null;
  const o = {
    boss: true, pos: 0, prevPos: 0, lat: 0, prevLat: 0, targetLat: 0, speed: 0, verso: 1,   // verso +1 = guarda avanti, -1 = ci guarda
    health: BOSS.vita, hp0: BOSS.vita, state: 'fuori', atkCd: 0, flash: 0,
    actor: { group: punto, flashHit() { lampo = 1; }, colpito(dir, forza = 1) { scossa = { t: 0, dir: dir || 1, forza }; },
             attacca() {}, cadi() {}, rialzati() {}, rimettiInPiedi() {} },
  };

  // ── il modello: pezzi in fila dal collo alla coda ───────────────────────
  let testa = null, mascella = null;
  const pezzi = [];             // { nodo, d } spicchi e coda, d = distanza dal collo
  const gambe = [];             // { coscia, stinco, fase }
  const materiali = new Set();
  let pronto = false;
  new GLTFLoader().load(BOSS.url, gltf => {
    const radici = gltf.scene.children.slice();
    const trova = re => radici.filter(n => re.test(n.name)).sort((a, b) => a.name.localeCompare(b.name));
    testa = radici.find(n => n.name === 'Testa');
    for (const n of [...trova(/^Spicchio\d/), ...trova(/^Coda\d/)]) pezzi.push({ nodo: n, d: -n.position.x * K });
    if (!testa || !pezzi.length) { console.warn('Boss: nel GLB mancano Testa o Spicchio*'); return; }
    mascella = testa.getObjectByName('Mascella') || null;       // se manca (modello vecchio) la bocca resta chiusa
    [testa, ...pezzi.map(p => p.nodo)].forEach(n => {
      gruppo.add(n); n.scale.setScalar(K); n.rotation.order = 'YZX';   // imbardata, poi beccheggio, poi rollio
      n.traverse(m => {
        if (m.isMesh) { m.castShadow = true; (Array.isArray(m.material) ? m.material : [m.material]).forEach(x => materiali.add(x)); }
        if (/^Coscia_/.test(m.name)) {
          const stinco = m.children.find(c => /^Stinco_/.test(c.name));
          // passo alternato: sinistra e destra in opposizione, e ogni portatore sfalsato dal vicino
          const sp = m.name.match(/_S(\d)_/);                    // di chi sono: -1 la testa, altrimenti il numero dello spicchio
          gambe.push({ coscia: m, stinco, fase: gambe.length * 1.9 + (/_S$/.test(m.name) ? 0 : Math.PI), di: sp ? +sp[1] : -1 });
        }
      });
    });
    pronto = true;
    console.log('Boss caricato:', BOSS.url, '·', pezzi.length, 'pezzi ·', gambe.length, 'gambe ·', mascella ? 'bocca apribile' : 'bocca fissa');
  }, undefined, () => console.warn('Boss: modello non trovato', BOSS.url));

  // ── stato dello scontro ─────────────────────────────────────────────────
  let fase = 1, att = null, piano = { tipo: 'fianco', t: 0 }, ruggito = 0, stordito = 0;
  let morte = 0, finito = false, tEntra = 0, latCd = 0, spinta = 0, corsa = 0;
  let giro = null;              // il dietrofront in corso: { S, sigma, lat0, lat1, R, v0, fine } (+ prevS, prevSigma)
  let mosse = 0, morsi = 0, apertura = 0, tempo = 0, mira = 0, scena = 0, alza = 0;
  const visto = { playerX: 0, g: 0 };   // l'ultimo stato del giocatore, per puntargli la testa quando si disegna

  const nuovoPiano = (tipo, t) => { piano = { tipo, t }; };

  // LA CURVA A U. Il corpo è un serpente steso su un percorso: corsia d'arrivo (lat0), mezzo cerchio, corsia di
  // ritorno (lat1) in senso opposto. `s` è la strada fatta lungo il percorso, 0 = inizio della curva; S è il punto
  // della pista dove sta la curva (e corre con il Boss). Dà posizione lungo pista e lato di un punto del corpo.
  const G0 = { pos: 0, lat: 0 };
  function gamma(q, S, s, out = G0) {
    const L = Math.PI * q.R;
    if (s <= 0)      { out.pos = S + q.v0 * s; out.lat = q.lat0; }
    else if (s < L)  { const th = s / q.R; out.pos = S + q.v0 * q.R * Math.sin(th); out.lat = q.lat0 + (q.lat1 - q.lat0) * (1 - Math.cos(th)) / 2; }
    else             { out.pos = S - q.v0 * (s - L); out.lat = q.lat1; }
    return out;
  }
  function iniziaGiro(playerX, versoGiocatore) {
    // la U si allarga verso il giocatore quando gli si gira incontro, e via da lui quando torna a correre dritto
    let da = Math.sign(playerX - o.lat) || (o.lat > 0 ? -1 : 1);
    if (!versoGiocatore) da = -da;
    let lat1 = limit(o.lat + da * limit(Math.abs(playerX - o.lat) + 0.3, 0.7, 1.3), -0.75, 0.75);   // una U larga: deve vedersi
    if (Math.abs(lat1 - o.lat) < 0.4) lat1 = limit(o.lat - da * 0.6, -0.75, 0.75);       // contro il bordo: gira dall'altra parte
    const R = Math.abs(lat1 - o.lat) * ROAD_WIDTH / 2;
    giro = { S: avvolgi(o.pos + o.verso * DAVANTI), sigma: -DAVANTI, lat0: o.lat, lat1, R, v0: o.verso, fine: Math.PI * R + DIETRO + 300 };
    giro.prevS = giro.S; giro.prevSigma = giro.sigma;
    att = null; nuovoPiano('giro', 9);
  }
  function fineGiro() {
    const q = giro; gamma(q, q.S, q.sigma);
    o.pos = avvolgi(G0.pos); o.lat = o.targetLat = q.lat1; o.verso = -q.v0; giro = null;
    if (o.verso < 0) { morsi = 0; o.atkCd = 0.9; nuovoPiano('fronte', 10); }
    else { mosse = 0; o.atkCd = 1.5; latCd = 4; nuovoPiano('fianco', 2); }
  }
  const avanza = dt => {
    if (giro) { giro.S = avvolgi(giro.S + o.speed * dt); gamma(giro, giro.S, giro.sigma); o.pos = avvolgi(G0.pos); o.lat = G0.lat; }
    else o.pos = avvolgi(o.pos + o.speed * dt);
  };

  function entra(position) {
    o.pos = o.prevPos = avvolgi(position + 16000);
    o.lat = o.prevLat = -1.9; o.targetLat = -0.45;             // arriva da fuori strada, dal lato del fiume
    o.speed = MAX_SPEED * 0.3; o.health = o.hp0 = BOSS.vita; o.atkCd = 0; o.flash = 0; o.state = 'entra'; o.verso = 1;
    fase = 1; att = null; ruggito = 0; stordito = 0; morte = 0; finito = false; tEntra = 0; latCd = 4; spinta = 0;
    giro = null; mosse = BOSS.sorpassoOgni[1] - 1; morsi = 0; apertura = 0;     // il primo sorpasso arriva presto: è la sua mossa
    lampo = 0; scossa = null; nuovoPiano('fianco', 2.5);
    for (const g of gambe) { g.coscia.visible = true; }
    gruppo.visible = true;
  }
  function esci() { o.state = 'fuori'; att = null; giro = null; spinta = 0; gruppo.visible = false; }

  // il colpo del giocatore: restituisce il danno entrato davvero (0 mentre ruggisce: è il cambio di fase)
  function ferisci(dmg) {
    if (o.state !== 'race' || ruggito > 0) return 0;
    if (stordito > 0) dmg *= 1.5;                              // dopo una parata è scoperto
    o.health = Math.max(0, o.health - dmg);
    if (o.health <= 0) { muori(); return dmg; }
    const f = o.health > o.hp0 * 2 / 3 ? 1 : o.health > o.hp0 / 3 ? 2 : 3;
    if (f > fase) { fase = f; ruggito = 1.6; att = null; o.atkCd = 2.2; evento('fase', f); }
    return dmg;
  }
  function muori() {
    if (o.state === 'morto') return;
    o.state = 'morto'; o.health = 0; att = null; morte = 0; finito = false; spinta = 0;
    evento('abbattuto');
  }

  // dove sta il giocatore LUNGO IL CORPO: distanza dal collo verso la coda (negativa = verso il muso).
  // g = collo − giocatore lungo pista. Vale nei due versi; durante il dietrofront non ha senso (corpo piegato).
  const lungoCorpo = g => o.verso * g;

  // il giocatore può colpirlo? dl = lat del Boss − playerX, side = lato del colpo (0 = qualunque)
  function aTiro(g, dl, side, latR, ranged) {
    if (ranged) {                                              // arco: basta che un pezzo sia davanti e a gittata
      return g + (o.verso > 0 ? DAVANTI : DIETRO) > 0 && g - (o.verso > 0 ? DIETRO : DAVANTI) < 18000;
    }
    if (giro) return false;                                    // mentre si gira è un groviglio: solo le frecce
    const d = lungoCorpo(g);
    if (d < -DAVANTI - 700 || d > DIETRO + 700) return false;  // è lungo: vale tutto il corpo, non un punto
    if (Math.abs(dl) > latR + SEMI_LARG) return false;
    if (side < 0 && dl > 0.15) return false;
    if (side > 0 && dl < -0.15) return false;
    return true;
  }

  function risolvi(G, gVero) {
    const dl = G.playerX - o.lat, ad = Math.abs(dl), lato = Math.sign(dl) || 1;
    const g = gVero / SCALA;                                    // in misure del corpo
    if (att.tipo === 'morso') {
      if (g < 100 && g > -3500 && ad < SEMI_LARG + 1.25 && (lato === att.dir || ad < SEMI_LARG)) {
        const parato = colpisci({ danno: BOSS.danni.morso, dir: att.dir, spinta: 0.35, parabile: true, nome: 'MORSO!' });
        if (parato) { stordito = 1.6; scossa = { t: 0, dir: -att.dir, forza: 1.5 }; lampo = 0.6; }
      }
    } else if (att.tipo === 'fauci') {
      // di fronte: la punta del muso deve essere arrivata al giocatore, nella sua corsia
      const muso = gVero - DAVANTI;
      if (muso < 1700 && muso > -2600 && ad < SEMI_LARG + 0.33) {
        const parato = colpisci({ danno: BOSS.danni.fauci, dir: lato, spinta: 0.3, parabile: true, nome: 'MORSO!' });
        if (parato) { stordito = 1.8; scossa = { t: 0, dir: -lato, forza: 1.5 }; lampo = 0.6; }
      }
    } else if (g > 4900 && g < 10200 && ad < 1.3 && (lato === att.dir || ad < 0.3)) {
      colpisci({ danno: BOSS.danni.coda, dir: att.dir, spinta: 0.6, parabile: false, nome: 'CODATA!' });
    }
  }

  // ATTACCHI — tutti annunciati (stadio 'carica'), tutti evitabili:
  //   morso     giocatore accanto alla testa        → si para (I) e lo si stordisce, o ci si allontana
  //   coda      giocatore accanto alla coda         → allargarsi (la frustata arriva a 1,3), o passare dall'altro lato
  //   sbandata  giocatore accanto al corpo, fase 2+ → stringersi al bordo strada (non ci arriva), frenare o scattare via
  //   fauci     faccia a faccia, dopo il sorpasso   → cambiare corsia quando smette di seguirti, o parare
  function attacchi(dt, G, gVero) {
    const dl = G.playerX - o.lat, ad = Math.abs(dl), lato = Math.sign(dl) || 1;
    const g = gVero / SCALA;                                    // in misure del corpo
    if (!att) {
      if (o.atkCd > 0 || ruggito > 0 || stordito > 0) return;
      let tipo = null;
      if (o.verso < 0) { if (gVero > DAVANTI + 1500 && gVero < DAVANTI + 8000) tipo = 'fauci'; }
      else if (piano.tipo === 'sorpasso') tipo = null;
      else if (g < -200 && g > -3300 && ad < SEMI_LARG + 1.15) tipo = 'morso';
      else if (g > 5200 && g < 9900 && ad < 1.2) tipo = 'coda';
      else if (fase >= 2 && g > -600 && g < 4400 && ad > SEMI_LARG + 0.15 && ad < 1.35 && Math.random() < dt * 0.9) tipo = 'sbandata';
      if (tipo) att = { tipo, dir: tipo === 'fauci' ? 0 : lato, t: 0, stadio: 'carica', fatto: false,
                        dur: tipo === 'fauci' ? (fase >= 3 ? 0.75 : 1.0) : (fase >= 3 ? 0.5 : 0.75) };
      return;
    }
    att.t += dt;
    if (att.stadio === 'carica') {
      if (att.t >= att.dur) { att.stadio = 'colpo'; att.t = 0; if (att.tipo === 'morso' || att.tipo === 'coda') risolvi(G, gVero); }
    } else if (att.stadio === 'colpo') {
      if (att.tipo === 'sbandata') {
        // si butta di lato ma non oltre ±0,42: chi sta sul bordo strada (da 0,98) è salvo senza finire nell'erba
        const nl = o.lat + att.dir * 2.6 * dt;
        if (Math.abs(nl) <= 0.42 || Math.abs(nl) < Math.abs(o.lat)) o.lat = nl;
        if (!att.fatto && g > -DAVANTI0 && g < 4600 && Math.abs(G.playerX - o.lat) < SEMI_LARG + 0.32) {
          att.fatto = true;
          colpisci({ danno: BOSS.danni.sbandata, dir: att.dir, spinta: 0.7, parabile: false, nome: 'TRAVOLTO!' });
        }
        if (att.t >= 0.3) { att.stadio = 'recupero'; att.t = 0; o.targetLat = o.lat; }
      } else if (att.tipo === 'fauci') {
        if (att.t >= 0.24) { risolvi(G, gVero); att.stadio = 'recupero'; att.t = 0; morsi++; }   // l'affondo dura 0,24 s, poi le fauci si chiudono
      } else if (att.t >= 0.16) { att.stadio = 'recupero'; att.t = 0; }
    } else if (att.t >= (att.tipo === 'fauci' ? 0.8 : fase >= 3 ? 0.45 : 0.7)) {
      const eraFauci = att.tipo === 'fauci';
      att = null;
      if (eraFauci) o.atkCd = fase >= 3 ? 0.6 + Math.random() * 0.5 : 1.1 + Math.random() * 0.8;
      else {
        o.atkCd = Math.max(o.atkCd, BOSS.attesa[fase][0] + Math.random() * BOSS.attesa[fase][1]);
        if (piano.tipo === 'testa' || piano.tipo === 'coda') { mosse++; nuovoPiano('fianco', fase >= 3 ? 1.2 : 2.4); }
      }
    }
  }

  // che cosa fare adesso: le mosse normali, e ogni tanto il sorpasso con dietrofront
  function scegliPiano(G, g) {
    const t = piano.tipo;
    if (t === 'fianco') {
      if (mosse >= BOSS.sorpassoOgni[fase]) nuovoPiano('sorpasso', 6);
      else nuovoPiano(Math.random() < 0.55 ? 'testa' : 'coda', 4.5);
    }
    else if (t === 'testa' || t === 'coda') { mosse++; nuovoPiano('fianco', fase >= 3 ? 1.2 : 2.4); }   // non è riuscito ad attaccare: conta lo stesso
    else if (t === 'sorpasso') { if (g > 6500 * SCALA) iniziaGiro(G.playerX, true); else { mosse = 0; nuovoPiano('fianco', 2); } }   // non ce l'ha fatta a passare
    else if (t === 'fronte') iniziaGiro(G.playerX, false);
  }

  // UN PASSO DI FISICA (stesso passo fisso del gioco). G = { playerX, speed }
  function passo(dt, G) {
    o.prevPos = o.pos; o.prevLat = o.lat; spinta = 0; tempo += dt;
    if (giro) { giro.prevS = giro.S; giro.prevSigma = giro.sigma; }
    if (o.state === 'fuori') return;
    const g = gapTo(o.pos);
    visto.playerX = G.playerX; visto.g = g;
    if (o.atkCd > 0) o.atkCd -= dt;
    if (o.state === 'morto') {
      // crolla restando accanto a chi l'ha abbattuto, poi si ferma: frenando di colpo spariva dietro la camera
      // e il crollo non lo vedeva nessuno
      morte += dt; o.speed = G.speed * Math.max(0, 1 - morte / (BOSS.durataMorte * 0.85)); avanza(dt);
      if (morte >= BOSS.durataMorte && !finito) { finito = true; evento('fine'); }
      return;
    }
    if (o.state === 'entra') {
      tEntra += dt;
      o.lat += (o.targetLat - o.lat) * Math.min(1, dt * 0.8); avanza(dt);
      if (g < 9000 || tEntra > 7) { o.state = 'race'; o.atkCd = 2.2; nuovoPiano('fianco', 2.5); }
      return;
    }
    if (ruggito > 0) ruggito -= dt;
    if (stordito > 0) stordito -= dt;

    // IL DIETROFRONT: il corpo scorre lungo la U; il punto della curva resta alla giusta distanza dal giocatore
    if (giro) {
      const q = giro, gS = gapTo(q.S);
      // dove deve stare la curva perché a giro finito il Boss sia al suo posto: di fronte, muso a MUSO_DI_FRONTE;
      // tornando dritto, la curva resta dov'era il muso
      const sDes = q.v0 > 0 ? MUSO_DI_FRONTE + DAVANTI + DIETRO + 300 : MUSO_DI_FRONTE;
      const target = limit(G.speed - (gS - sDes) * 0.9, MAX_SPEED * 0.35, MAX_SPEED * 1.6);
      o.speed += (target - o.speed) * Math.min(1, dt * 2.2);
      q.sigma += STRISCIO * dt;
      avanza(dt);
      if (q.sigma >= q.fine) fineGiro();
      return;
    }

    piano.t -= dt;
    if (piano.tipo === 'sorpasso' && g > 8500 * SCALA && !att) iniziaGiro(G.playerX, true);           // il collo è passato davanti: si gira
    else if (piano.tipo === 'fronte' && morsi >= BOSS.morsiDiFronte[fase] && !att) iniziaGiro(G.playerX, false);
    else if (piano.t <= 0 && !att) scegliPiano(G, g);
    if (giro) return;

    // lungo pista: lo stesso elastico dei rivali, ma attorno al posto che gli serve per la prossima mossa.
    // Se il giocatore resta molto indietro non scappa all'infinito: lo aspetta.
    let gDes = GDES[piano.tipo], molla = 0.9;
    if (att && att.tipo === 'fauci') {
      if (att.stadio === 'carica') gDes = DAVANTI + 2600;                                  // si avvicina a bocca aperta…
      else if (att.stadio === 'colpo') { gDes = DAVANTI + 900; molla = 7; }                // …e affonda
    }
    const err = g - gDes;
    // nell'affondo pianta i piedi (può perfino arretrare): con il minimo normale non arrivava a mordere
    const target = limit(G.speed - err * molla, molla > 1 ? -MAX_SPEED * 0.3 : err > 12000 ? 0 : MAX_SPEED * 0.35, MAX_SPEED * 1.6);
    o.speed += (target - o.speed) * Math.min(1, dt * (molla > 1 ? 14 : 2.2));

    // di lato: tiene una corsia e ogni tanto la cambia; per mordere si accosta. Lento apposta: si deve poter schivare.
    if (!(att && att.tipo === 'sbandata' && att.stadio !== 'carica')) {
      const dl = G.playerX - o.lat, lato = Math.sign(dl) || 1;
      latCd -= dt;
      let passoLat = 0.45;
      if (o.verso < 0) {
        // faccia a faccia sta DI SBIECO, una corsia più in là, con la testa girata verso di noi. Caricando il morso
        // ci segue; a due terzi della carica FISSA LA MIRA (da lì si può schivare) e sul colpo taglia nella nostra corsia
        const fauci = att && att.tipo === 'fauci';
        if (fauci && att.stadio === 'carica' && att.t > att.dur * 0.62) { if (att.mira == null) att.mira = limit(G.playerX, -0.85, 0.85); passoLat = 0; }
        else if (fauci && att.stadio === 'colpo') { o.targetLat = att.mira ?? G.playerX; passoLat = 3.4; }
        else {
          const dalLato = Math.sign(o.lat - G.playerX) || 1;
          let t = G.playerX + dalLato * DI_SBIECO;
          if (Math.abs(t) > 0.78) t = G.playerX - dalLato * DI_SBIECO;       // contro il bordo passa dall'altra parte
          o.targetLat = limit(t, -0.78, 0.78); passoLat = 0.6;
        }
      }
      else if (piano.tipo === 'testa') o.targetLat = limit(G.playerX - lato * (SEMI_LARG + 0.5), -0.7, 0.7);
      else if (piano.tipo === 'sorpasso') o.targetLat = (o.lat >= G.playerX ? 1 : -1) * 0.55;   // passa dal suo lato, senza tagliarci la strada
      else if (latCd <= 0) { latCd = 5 + Math.random() * 4; o.targetLat = (Math.random() < 0.5 ? -1 : 1) * (0.25 + Math.random() * 0.3); }
      o.lat += limit((o.targetLat - o.lat) * (passoLat > 1 ? 14 : 1.5), -passoLat, passoLat) * dt;   // nell'affondo taglia secco
    }
    avanza(dt);
    attacchi(dt, G, g);
    // il corpo fa muro: chi ci entra dentro viene scostato (la coda no, è sottile e sta in alto)
    const dl = G.playerX - o.lat, d = lungoCorpo(g);
    if (d > -DAVANTI && d < D_CORPO && Math.abs(dl) < SEMI_LARG + 0.2) spinta = (Math.sign(dl) || 1) * 1.8;
  }

  // ── DISEGNO: a ogni fotogramma, con lo stato interpolato ────────────────
  const J = Array.from({ length: 12 }, () => new THREE.Vector3());
  const F = new THREE.Vector3(), A = new THREE.Vector3(), B = new THREE.Vector3(), la = {}, GP = { pos: 0, lat: 0 };
  // la curva di un colpo: si carica dalla parte opposta, scatta, torna. Da -0,4 a +1.
  function curvaAtt() {
    if (!att) return 0;
    if (att.stadio === 'carica') return -0.4 * Math.sin(Math.min(1, att.t / att.dur) * Math.PI / 2);
    if (att.stadio === 'colpo') return -0.4 + 1.4 * Math.min(1, att.t / 0.12);
    return 1 - dolce(att.t / 0.6);
  }
  // quanto deve essere aperta la bocca adesso, 0…1
  function boccaVoluta(rugge) {
    if (o.state === 'morto') return 0.55;
    if (rugge > 0) return Math.max(0.3, rugge);
    if (att && (att.tipo === 'morso' || att.tipo === 'fauci')) {
      if (att.stadio === 'carica') return att.tipo === 'fauci' ? dolce(att.t / att.dur * 1.4) : 0.3 + 0.7 * att.t / att.dur;   // si apre: è l'avviso
      if (att.stadio === 'colpo') return att.tipo === 'fauci' && att.t < 0.17 ? 1 : 0;                                          // …e si chiude di scatto
      return 0;
    }
    return o.verso < 0 ? 0.2 + 0.07 * Math.sin(tempo * 3.1) : 0.04;        // di fronte la tiene socchiusa, minaccioso
  }
  function orienta(nodo, f, rollio) {
    nodo.rotation.set(rollio, Math.atan2(-f.z, f.x), Math.atan2(f.y, Math.hypot(f.x, f.z)));
  }
  function disegna(dt, alpha) {
    if (o.state === 'fuori' || !pronto) { gruppo.visible = false; return; }
    gruppo.visible = true;
    const pos = interpWrap(o.prevPos, o.pos, alpha), lat = o.prevLat + (o.lat - o.prevLat) * alpha;
    const q = giro, qS = q ? interpWrap(q.prevS, q.S, alpha) : 0, qSig = q ? q.prevSigma + (q.sigma - q.prevSigma) * alpha : 0;
    // un punto del corpo a distanza d dal collo (verso la coda; negativa = verso il muso): dritto, oppure lungo la U
    const corpo = d => { if (q) return gamma(q, qS, qSig - d, GP); GP.pos = pos - o.verso * d; GP.lat = lat; return GP; };
    const vel = Math.min(1, o.speed / (MAX_SPEED * 0.5));
    corsa += dt * Math.PI * 2 * Math.min(3.2, o.speed / (2600 * SCALA)) * (q ? 1 : o.verso);    // di fronte le gambe corrono all'indietro
    if (lampo > 0) lampo = Math.max(0, lampo - dt * 4);
    if (scossa) { scossa.t += dt; if (scossa.t > 0.5) scossa = null; }
    const c = curvaAtt(), dir = att ? att.dir : 0, tipo = att && att.tipo;
    const urto = scossa ? scossa.dir * 0.06 * scossa.forza * 1.5 * Math.exp(-scossa.t * 6.5) * Math.sin(scossa.t * 24) : 0;
    const rugge = ruggito > 0 ? Math.sin(Math.PI * limit(1 - ruggito / 1.6, 0, 1)) : 0;
    const n = pezzi.length, onda = (0.04 + 0.1 * rugge) * vel;
    const giu = k => o.state === 'morto' ? dolce((morte - k * 0.1) / 0.45) : 0;      // il costume crolla, un pezzo dopo l'altro
    apertura += (boccaVoluta(rugge) - apertura) * Math.min(1, dt * 18);
    // «scena»: 0…1 quando fa la sua mossa (dietrofront e faccia a faccia): la camera del gioco si allarga per farcelo stare
    const inScena = o.state === 'race' && (q || o.verso < 0);
    scena += ((inScena ? 1 : 0) - scena) * Math.min(1, dt * 2.5);
    alza += ((o.state === 'race' && o.verso < 0 && !q ? 1 : 0) - alza) * Math.min(1, dt * 4);
    const su = k => (IMPENNATA[k] || 0) * alza;

    // i giunti: collo, poi l'inizio di ogni pezzo, poi la punta della coda
    for (let k = 0; k <= n; k++) {
      const p = corpo(k < n ? pezzi[k].d : DIETRO);
      let l = p.lat + urto + onda * Math.sin(corsa * 0.5 - k * 0.9) * (0.3 + 0.7 * k / n);
      if (tipo === 'coda' && k >= 3) l += dir * c * 1.15 * Math.pow((k - 2) / (n - 2), 1.3);   // la frustata cresce verso la punta
      posToWorld(p.pos, l, J[k]);
      J[k].y += 45 * vel * Math.sin(corsa + k * 1.3) - 950 * SCALA * giu(k) + su(k);
    }
    const rollCorpo = tipo === 'sbandata' ? dir * (c < 0 ? c * 0.45 : c * 0.3) : 0;
    for (let k = 0; k < n; k++) {
      const p = pezzi[k].nodo, m = giu(k);
      p.position.copy(J[k]);
      F.subVectors(J[k], J[k + 1]);
      orienta(p, F, rollCorpo + m * (k % 2 ? 0.5 : -0.4));
    }
    // la testa: punta dove va il corpo (anche nella U); nel morso di lato si gira di scatto verso il giocatore,
    // nel ruggito si alza, e a bocca aperta alza un po' il muso
    {
      let p = corpo(0); posToWorld(p.pos, p.lat + urto, A, la);
      p = corpo(-1500); posToWorld(p.pos, p.lat + urto, B);
      // faccia a faccia la testa ci punta: si gira verso la nostra corsia (di più di quanto servirebbe, perché si legga)
      const vuole = o.verso < 0 && !q ? limit(Math.atan2((visto.playerX - lat) * ROAD_WIDTH, Math.max(1500, visto.g - DAVANTI * 0.5)) * 1.7, -0.6, 0.6) : 0;
      mira += (vuole - mira) * Math.min(1, dt * 8);
      const h = la.heading, morso = tipo === 'morso' ? c : 0, a = morso * dir * 0.7 + mira, m = giu(0);
      F.subVectors(B, A); const lung = F.length() || 1; F.multiplyScalar(1 / lung);
      // gira verso il lato `dir` della pista: destra pista = (-cos h, 0, sin h)
      const ca = Math.cos(a), sa = Math.sin(a), fy = F.y;
      F.set(F.x * ca - Math.cos(h) * sa, fy + 0.5 * rugge + 0.25 * Math.max(0, -morso) + 0.1 * apertura - 0.3 * m - 0.14 * alza, F.z * ca + Math.sin(h) * sa);   // impennato guarda in giù, verso di noi
      const allungo = Math.max(0, morso) * dir * 450;
      testa.position.set(A.x - Math.cos(h) * allungo, A.y + 45 * vel * Math.sin(corsa) - 900 * SCALA * m + su(0), A.z + Math.sin(h) * allungo);
      orienta(testa, F, rollCorpo + (rugge ? 0.12 * Math.sin(corsa * 3) * rugge : 0) + m * 0.45);
      if (mascella) mascella.rotation.z = -apertura * APERTURA;   // attorno all'asse laterale: negativo = la punta scende
    }
    // le gambe corrono (ferme se è fermo); a terra spariscono sotto il costume
    for (const g of gambe) {
      const s = Math.sin(corsa + g.fase);
      g.coscia.rotation.z = 0.62 * s * vel;
      if (g.stinco) g.stinco.rotation.z = -(0.12 + 1.0 * Math.max(0, Math.sin(corsa + g.fase - 1.1))) * vel;
      g.coscia.visible = o.state !== 'morto' || morte < 0.5;
      // impennato: le gambe si allungano quanto è salito il pezzo che portano (anca a 1,2 m), i piedi restano a terra
      g.coscia.scale.y = 1 + (g.di < 0 ? su(0) : (su(g.di) + su(g.di + 1)) / 2) / (1.2 * K);
    }
    // lampo rosso quando incassa: leggero, perché sotto una raffica di pugni resta quasi sempre acceso e a piena
    // forza il Boss diventava tutto rosa. In fase 3 resta un rosso fisso (non pulsa: niente batte a tempo qui).
    const rosso = Math.max(lampo * lampo * 0.3, fase >= 3 && o.state !== 'morto' ? 0.07 : 0);
    for (const m of materiali) { m.emissive.setRGB(rosso, 0, 0); m.emissiveIntensity = 1; }
    // il punto più vicino al giocatore lungo il corpo
    { const p = corpo(q ? 0 : limit(lungoCorpo(gapTo(o.pos)), -DAVANTI, DIETRO)); posToWorld(p.pos, p.lat, punto.position); punto.position.y += 300; }
  }

  // per il pilota automatico: cosa conviene fare adesso. null = niente da segnalare
  // Il morso di fronte arriva a fine affondo, non a fine carica: l'avviso (e la parata) valgono fino a lì.
  const annunciato = () => o.state === 'race' && att && (att.stadio === 'carica' || (att.tipo === 'fauci' && att.stadio === 'colpo'));
  function consiglio(playerX) {
    if (!annunciato()) return null;
    if (att.tipo === 'morso' || att.tipo === 'fauci') return { parata: true };
    if (att.tipo === 'coda') return { x: limit(o.lat + att.dir * 1.4, -0.9, 0.9) };        // si allarga
    return { x: att.dir * 0.9, freno: true };                                              // sbandata: al bordo, e molla
  }

  return {
    o, passo, disegna, entra, esci, ferisci, muori, aTiro, consiglio,
    get attivo() { return o.state !== 'fuori'; },
    get attaccabile() { return o.state === 'race'; },
    get vivo() { return o.state === 'entra' || o.state === 'race'; },
    get vita() { return o.health / o.hp0; },
    get fase() { return fase; },
    get scorta() { return o.state === 'race' ? BOSS.scorta[fase] : 0; },
    get spinta() { return spinta; },               // playerX al secondo: il corpo che scosta il giocatore
    get stordito() { return stordito > 0; },
    get ruggisce() { return ruggito > 0; },
    get diFronte() { return o.verso < 0 && !giro; },
    get scena() { return scena; },                 // 0…1: sta facendo la sua mossa; la camera si allarga
    get pronto() { return pronto; },
    // l'attacco annunciato, per l'HUD: { testo, lato da cui arriva (-1 sinistra, +1 destra, 0 di fronte), parabile, quanto 0..1 }
    get avviso() {
      if (!annunciato()) return null;
      return { testo: { morso: 'MORSO', coda: 'CODA', sbandata: 'CARICA', fauci: 'MORSO' }[att.tipo], lato: -att.dir,   // att.dir è dove sta il giocatore: il colpo arriva dall'altra parte
               parabile: att.tipo === 'morso' || att.tipo === 'fauci', quanto: att.stadio === 'carica' ? att.t / att.dur : 1 };
    },
    // per i test: stato interno, attacco o mossa a comando
    get stato() { return { fase, att: att && { ...att }, piano: { ...piano }, ruggito, stordito, morte, verso: o.verso, giro: giro && +(giro.sigma / giro.fine).toFixed(2),
                           mosse, morsi, apertura: +apertura.toFixed(2), pezzi: pezzi.length, gambe: gambe.length, bocca: !!mascella }; },
    prova(tipo, dir = 1) {
      if (o.state !== 'race') return;
      if (tipo === 'sorpasso') { att = null; nuovoPiano('sorpasso', 6); }
      else att = { tipo, dir: tipo === 'fauci' ? 0 : dir, t: 0, stadio: 'carica', dur: tipo === 'fauci' ? 1.0 : 0.75, fatto: false };
    },
    DAVANTI, DIETRO, SEMI_LARG,
  };
}
