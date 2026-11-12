// LA BIRRA GRANDE — un bicchiere di birra sui pattini in linea che scappa lungo il tracciato. Se lo acchiappi:
// vai più veloce e incassi meno danno, per qualche secondo. È RARO: compare in una tappa su due, una volta sola.
//
// Il modello (assets/models/birra/birra.glb, generato da tools/boss/modello_birra.py) non ha scheletro: tre pezzi rigidi
// — Bicchiere, PattinoS, PattinoD — con l'origine all'anca, e qui si muovono a codice. Il passo è quello di chi
// pattina: i due pattini scivolano avanti e indietro in controfase (uno si solleva mentre torna avanti), il bicchiere
// dondola e si piega in avanti, e quando cambia corsia si inclina come in curva.
//
// Il modulo non sa niente del resto del gioco: riceve la strada (posToWorld) e, a ogni fotogramma, lo stato del
// giocatore. Il gioco gli chiede due numeri — `danno` e `piuVelocita` — e riceve tre eventi: avvista, preso, persa.
//
// REGOLA DEL LIVELLO 0: niente qui batte a tempo. Se un giorno la Birra si lega alla musica, passa da un bersaglio
// della centralina (3d/centralina.js), mai da musica.* direttamente.
//
// Assi del modello: +X davanti, +Y alto, +Z destra, in metri. Gioco: 1 m = 1000 unità.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export const BIRRA = {
  nome: 'BIRRA GRANDE',                         // ASCII: va nell'HUD a pixel
  url: 'assets/models/birra/birra.glb',
  probabilita: 0.5,                             // per tappa: «relativamente raro»
  durata: 14,                                   // secondi di effetto (riacchiappandola si riparte da qui)
  piuVelocita: 0.2,                             // limite di velocità +20%: 200 → 240 km/h, nitro compreso
  accelerazione: 0.35,                          // e si accelera di più
  danno: 0.55,                                  // moltiplicatore del danno subito: -45%
  velocita: 0.72,                               // quanto pattina, in parti della velocità massima (la rincorsa si vince)
  altezza: 850,                                 // unità di gioco: due terzi di un cavallo, come un oggettino da raccogliere (era 2200: troppo ingombrante)
};

const ALTO_MODELLO = 0.461;                     // m: altezza del modello nativo
const K = BIRRA.altezza / ALTO_MODELLO;         // metri del modello → unità di gioco
const DISTANZA_COMPARSA = 58000;                // compare così avanti al giocatore: si vede arrivare
const LONTANA = 150000;                         // oltre: se n'è andata
const limit = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

export function creaBirra({ scene, posToWorld, gapTo, MAX_SPEED, TRACK_LENGTH, ROAD_WIDTH, evento, forzata = false }) {
  const gruppo = new THREE.Group(); gruppo.visible = false; scene.add(gruppo);
  const avvolgi = p => ((p % TRACK_LENGTH) + TRACK_LENGTH) % TRACK_LENGTH;

  // ── il modello ──────────────────────────────────────────────────────────
  let bicchiere = null, pattinoS = null, pattinoD = null, pronto = false;
  const base = {};
  new GLTFLoader().load(BIRRA.url, gltf => {
    const m = gltf.scene;
    bicchiere = m.getObjectByName('Bicchiere'); pattinoS = m.getObjectByName('PattinoS'); pattinoD = m.getObjectByName('PattinoD');
    if (!bicchiere || !pattinoS || !pattinoD) { console.warn('Birra: nel GLB mancano Bicchiere o PattinoS/D'); return; }
    m.scale.setScalar(K); gruppo.add(m);
    for (const [n, p] of [['b', bicchiere], ['s', pattinoS], ['d', pattinoD]]) base[n] = p.position.clone();
    m.traverse(o => { if (o.isMesh) o.castShadow = true; });
    pronto = true;
    console.log('Birra caricata:', BIRRA.url);
  }, undefined, () => console.warn('Birra: modello non trovato', BIRRA.url));

  // ── stato ───────────────────────────────────────────────────────────────
  const b = { stato: 'fuori', pos: 0, lat: 0, latV: 0, speed: 0, t: 0, fase: 0, tPreso: 0, tempo: 0 };
  let quando = Infinity;          // a che punto della tappa (game.dist) compare
  let effetto = 0;                // secondi di effetto rimasti
  let sfila = 0;                  // l'ultima posizione di chi l'ha presa, per il volo finale
  const volo = new THREE.Vector3();

  function nuovoEvento(dist) {
    esci();
    effetto = 0;
    quando = (forzata || Math.random() < BIRRA.probabilita) ? dist * (forzata ? 0.12 : 0.22 + Math.random() * 0.4) : Infinity;
  }
  function esci() { b.stato = 'fuori'; gruppo.visible = false; quando = Infinity; }
  function azzera() { esci(); effetto = 0; }
  function compari(G) {
    b.stato = 'pattina'; b.pos = avvolgi(G.position + DISTANZA_COMPARSA); b.lat = b.latOld = (Math.random() < 0.5 ? -1 : 1) * 0.35;
    b.speed = MAX_SPEED * BIRRA.velocita; b.t = Math.random() * 6; b.fase = 0; quando = Infinity;
    gruppo.visible = true; gruppo.scale.setScalar(1);
    evento('avvista');
  }

  // dove sta la corsia a cui punta, in corsie: dalla corsia centrale va a destra e a sinistra, e quando il giocatore
  // si avvicina scarta di lato per non farsi prendere (ma non abbastanza da essere imprendibile)
  function corsia(G, gap) {
    const vicino = limit((16000 - gap) / 16000, 0, 1);
    const scarto = Math.sign(b.lat - G.playerX || 1) * 0.3 * vicino;
    return limit(0.58 * Math.sin(b.t * 0.85) + scarto, -0.8, 0.8);
  }

  // un fotogramma. G = { racing, dist, resta, position, playerX, speed, giocatore (Vector3) }
  function aggiorna(dt, G) {
    if (!G.racing) return;                                       // nei menu e nei bonus il tempo non passa
    if (effetto > 0) effetto = Math.max(0, effetto - dt);
    b.tempo += dt;

    if (b.stato === 'fuori') {
      if (quando !== Infinity && G.dist >= quando && G.resta > DISTANZA_COMPARSA * 2 && pronto) compari(G);
      return;
    }
    if (!pronto) return;

    if (b.stato === 'pattina') {
      b.t += dt;
      const gap = gapTo(b.pos);
      // scatta ogni tanto quando il giocatore è vicino: la rincorsa dura, ma si vince col gas a fondo
      const scatto = gap < 16000 && gap > 0 ? Math.pow(Math.max(0, Math.sin(b.t * 2.2)), 3) : 0;
      b.speed += (MAX_SPEED * BIRRA.velocita * (1 + 0.38 * scatto) - b.speed) * Math.min(1, dt * 2.5);
      b.pos = avvolgi(b.pos + b.speed * dt);
      const l0 = b.lat; b.lat += (corsia(G, gap) - b.lat) * Math.min(1, dt * 2.2); b.latV = (b.lat - l0) / Math.max(dt, 1e-3);
      b.fase += dt * (2.2 + 4.2 * Math.min(1, b.speed / (MAX_SPEED * 0.5)));
      // acchiappata: la sua larghezza più la tua, e non conta da quale parte arrivi
      if (Math.abs(gap) < 2300 && Math.abs(b.lat - G.playerX) < 0.4) {
        b.stato = 'preso'; b.tPreso = 0; effetto = BIRRA.durata;
        evento('preso');
      } else if (gap > LONTANA || gap < -30000) { b.stato = 'fuori'; gruppo.visible = false; evento('persa'); return; }
    } else if (b.stato === 'preso') {
      b.tPreso += dt;
      if (b.tPreso >= 0.45) { b.stato = 'fuori'; gruppo.visible = false; return; }
    }
    disegna(dt, G);
  }

  // ── disegno ─────────────────────────────────────────────────────────────
  const A = new THREE.Vector3(), B = new THREE.Vector3();
  function disegna(dt, G) {
    posToWorld(b.pos, b.lat, A);
    posToWorld(b.pos + 900, b.lat + b.latV * 0.08, B);
    B.sub(A); const f = B.length() || 1; B.multiplyScalar(1 / f);
    gruppo.rotation.order = 'YZX';
    gruppo.rotation.set(0, Math.atan2(-B.z, B.x), Math.atan2(B.y, Math.hypot(B.x, B.z)));
    gruppo.position.copy(A);
    if (b.stato === 'preso') {                                    // se la beve: vola verso il giocatore, rimpicciolisce e gira
      const u = b.tPreso / 0.45, e = u * u * (3 - 2 * u);
      volo.copy(G.giocatore); volo.y += 1500;
      gruppo.position.lerp(volo, e);
      gruppo.scale.setScalar(Math.max(0.02, 1 - e)); gruppo.rotation.y += e * 9;
    }
    const ph = b.fase, s = Math.sin(ph), c = Math.cos(ph);
    // pattini: in controfase; quello che torna avanti si solleva, e punta appena la punta
    pattinoS.position.set(base.s.x + 0.075 * s, base.s.y + 0.03 * Math.max(0, c), base.s.z); pattinoS.rotation.z = 0.2 * s + 0.12 * Math.max(0, c);
    pattinoD.position.set(base.d.x - 0.075 * s, base.d.y + 0.03 * Math.max(0, -c), base.d.z); pattinoD.rotation.z = -0.2 * s + 0.12 * Math.max(0, -c);
    // bicchiere: dondola, si piega in avanti, e si inclina nella corsia in cui sta andando
    const lean = limit(b.latV * ROAD_WIDTH / Math.max(b.speed, 3000) * 1.4, -0.11, 0.11);   // poco: un bicchiere che si butta di lato sembra caduto
    bicchiere.position.set(base.b.x, base.b.y + 0.007 * Math.sin(2 * ph), base.b.z);
    bicchiere.rotation.set(0.05 * s + lean, 0.06 * c, -0.07 - 0.015 * Math.abs(c));
  }

  return {
    aggiorna, nuovoEvento, esci, azzera,
    get pronto() { return pronto; },
    get effetto() { return effetto; },
    get attiva() { return effetto > 0; },
    // limite di velocità in più (ripreso di colpo sarebbe uno strappo: negli ultimi 1,5 s scende piano)
    get piuVelocita() { return BIRRA.piuVelocita * limit(effetto / 1.5, 0, 1); },
    get accelMul() { return 1 + BIRRA.accelerazione * limit(effetto / 1.5, 0, 1); },
    get danno() { return effetto > 0 ? BIRRA.danno : 1; },
    get stato() { return b.stato; },
    get pos() { return b.pos; },
    get lat() { return b.lat; },
    // per il pilota automatico: la corsia della Birra se sta pattinando davanti e abbastanza vicina, altrimenti null
    corsiaPerPilota() { if (b.stato !== 'pattina') return null; const g = gapTo(b.pos); return g > 0 && g < 70000 ? b.lat : null; },
    // per i test
    get dati() { return { ...b, quando, effetto }; },
    prova() { quando = 0; },
  };
}
