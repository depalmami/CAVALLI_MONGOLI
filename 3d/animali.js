// ANIMALI — greggi, mandrie, yak, cammelli e aquile che a un certo punto della serata ballano.
//
//   piazzaBranchi()  piazza i branchi lungo la pista (subito: serve prima degli alberi, che
//                    devono girargli attorno) — nessun modello è ancora caricato
//   creaFauna()      carica i modelli (Quaternius, CC0, assets/animali/) e li fa comparire
//                    solo vicino al giocatore, da un pool: ~1.100 animali in mappa, ~80 vivi
//
// Il ballo non è un'animazione che parte e va avanti: la clip del SALTO è agganciata alla fase del
// battito (action.time = fase × durata), quindi cade sul tempo a qualunque BPM, anche se il tempo
// cambia a metà pezzo. `a` (da 0 a 1, dalla centralina) dice quanto balla: a 0 pascolano, a 1
// saltano tutti sul battito, sfasati di poco fra loro (l'onda attraversa il branco), si voltano
// verso la strada e al drop fanno un giro su se stessi.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

function rng(seme) { let s = (seme * 2654435761) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
const M_UNITA = 800;                         // 1 m = 800 unità di gioco

// ── le specie ──
// alto = altezza totale in metri (testa alta), pool = quanti ne vivono insieme al massimo,
// colori = sostituzioni per nome di materiale: una riga per variante (scelta a caso per ogni animale)
const SPECIE = {
  pecora:   { url: 'assets/animali/pecora.glb',  alto: 0.95, pool: 34,
              colori: [{ White: 0xe9e6dc }, { White: 0xd6cdb8 }, { White: 0xbfb49c }, { White: 0x4a4036, Black: 0x241e18 }] },
  mucca:    { url: 'assets/animali/mucca.glb',   alto: 1.55, pool: 14,
              colori: [{}, { White: 0xc9a37a }, { White: 0x6b4a33, Pink: 0x9c6a5a }] },
  yak:      { url: 'assets/animali/mucca.glb',   alto: 1.7, pool: 16,
              colori: [{ White: 0x2e2118, Black: 0x15110e, Pink: 0x2a1f1a }, { White: 0x3b2c20, Black: 0x1a1410, Pink: 0x30241d }, { White: 0x1d1713, Black: 0x0f0c0a, Pink: 0x201914 }] },
  cavallo:  { url: 'assets/animali/cavallo.glb', alto: 1.75, pool: 22,
              colori: [{ 'Material.003': 0x744d3d }, { 'Material.003': 0x4a2f22 }, { 'Material.003': 0xc2ac86 }, { 'Material.003': 0x2b2420 }, { 'Material.003': 0x8f6a47 }, { 'Material.003': 0xd8d2c4 }] },
  cammello: { url: 'assets/animali/lama.glb',    alto: 2.3, pool: 10,
              colori: [{ Brown: 0xa57f4e, White: 0xd5bd8c, Grey: 0x7c6845 }, { Brown: 0x8b6a40, White: 0xc2aa7a, Grey: 0x6b5a3a }] },
};
const AQUILA = { url: 'assets/animali/aquila.glb', apertura: 3.8, n: 3,
                 colori: { Wings: 0x5a4330, Beak: 0xd9a53a, Head: 0xf1ece0, Claws: 0x3a3329 } };

// ── dove: branchi per tappa [specie, quanti, min animali, max animali] ──
const BRANCHI = [
  [['pecora', 9, 6, 16], ['cavallo', 5, 3, 7]],                         // 1 Kherlen
  [['pecora', 6, 6, 14], ['mucca', 5, 3, 6], ['cavallo', 4, 3, 6]],     // 2 Onon
  [['yak', 6, 3, 7]],                                                   // 3 Burkhan Khaldun
  [['pecora', 12, 8, 20], ['cavallo', 8, 4, 9], ['mucca', 3, 3, 6]],    // 4 Tuul
  [['cavallo', 12, 5, 11], ['pecora', 4, 6, 12]],                       // 5 Khustai: cavalli selvatici
  [['cammello', 8, 2, 5]],                                              // 6 dune
  [['pecora', 7, 6, 14], ['mucca', 4, 3, 6], ['cavallo', 5, 3, 7]],     // 7 Orkhon
  [['yak', 5, 3, 7], ['pecora', 3, 5, 10]],                             // 8 cascate
  [['yak', 8, 4, 9], ['pecora', 3, 5, 10]],                             // 9 Khangai
  [['cammello', 5, 2, 5], ['pecora', 5, 6, 12]],                        // 10 rovine
  [['pecora', 5, 6, 12], ['cavallo', 4, 3, 6]],                         // 11 Erdene Zuu
  [['pecora', 5, 6, 12], ['mucca', 3, 3, 5]],                           // 12 Karakorum
];

export function piazzaBranchi({ N, SEGMENT_LENGTH, ROAD_WIDTH, tappaInizio, posToWorld, groundAt, roadDist, libero, occupa }) {
  const r = rng(31337), P = new THREE.Vector3(), animali = [], branchi = [];
  const pendenza = (x, z) => Math.hypot(groundAt(x + 300, z) - groundAt(x - 300, z), groundAt(x, z + 300) - groundAt(x, z - 300)) / 600;
  BRANCHI.forEach((lista, k) => {
    const i0 = Math.floor(tappaInizio[k] / SEGMENT_LENGTH) + 220, i1 = Math.floor(tappaInizio[k + 1] / SEGMENT_LENGTH) - 220;
    if (k === BRANCHI.length - 1) return;      // l'ultimo "inizio" è la fine del viaggio: niente oltre
    for (const [specie, quanti, nmin, nmax] of lista) {
      for (let q = 0, messi = 0; q < quanti * 12 && messi < quanti; q++) {
        const seg = Math.floor(i0 + r() * (i1 - i0)), lato = r() < 0.5 ? -1 : 1, lat = lato * (3.3 + Math.pow(r(), 1.3) * 3.4);
        const n = nmin + Math.floor(r() * (nmax - nmin + 1)), raggio = 500 + n * 90;       // unità mondo
        if (!libero(seg, lat)) continue;
        posToWorld(seg * SEGMENT_LENGTH, lat, P);
        if (roadDist(P.x, P.z) < 3600 || pendenza(P.x, P.z) > 0.45) continue;
        const idB = branchi.length, sfasa = r(), yaw = r() * 6.283, mem = [];
        for (let t = 0; t < n * 6 && mem.length < n; t++) {
          const a = r() * 6.283, d = Math.sqrt(r()) * raggio;
          const sg = seg + Math.cos(a) * d / SEGMENT_LENGTH, lt = lat + Math.sin(a) * d / ROAD_WIDTH;
          posToWorld(sg * SEGMENT_LENGTH, lt, P);
          if (!libero(sg, lt) || roadDist(P.x, P.z) < 3000 || pendenza(P.x, P.z) > 0.55) continue;
          if (mem.some(m => Math.hypot(m.x - P.x, m.z - P.z) < 420)) continue;
          mem.push({ x: P.x, z: P.z, y: groundAt(P.x, P.z), d, seg: sg });
        }
        if (mem.length < 2) continue;
        mem.forEach(m => animali.push({ specie, branco: idB, x: m.x, y: m.y, z: m.z, seg: m.seg, yaw: yaw + (r() - 0.5) * 1.6,
                                         s: 0.88 + r() * 0.26, variante: Math.floor(r() * 99), ph: r(), ritardo: m.d / raggio * 0.3 + sfasa * 0.5 }));
        branchi.push({ specie, seg, lat, n: mem.length, raggio });
        occupa(seg, lat, 1.0 + raggio / ROAD_WIDTH, Math.ceil(raggio / SEGMENT_LENGTH) + 6);     // alberi ed erba girano attorno
        messi++;
      }
    }
  });
  animali.sort((a, b) => a.seg - b.seg);
  return { animali, branchi };
}

export function creaFauna({ scene, SEGMENT_LENGTH, posizione, groundAt, camera }) {
  const { animali, branchi } = posizione;
  const segs = animali.map(a => a.seg);
  const specie = {}, libere = {}, attivi = new Map(), loader = new GLTFLoader();
  let pronto = false, aquile = [], scatto = 0, dance = 0, tAq = 0;
  const P = new THREE.Vector3(), tmp = new THREE.Vector3();

  // un modello caricato → misure, materiali per variante e un pool di cloni
  function prepara(nome, cfg, gltf, alto, orizzontale = false) {
    gltf.scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(gltf.scene, true), size = box.getSize(new THREE.Vector3());
    const scala = alto * M_UNITA / (orizzontale ? Math.max(size.x, size.z) : size.y);     // le aquile si misurano sull'apertura alare
    const base = new Map();
    gltf.scene.traverse(o => { if (o.isMesh) [].concat(o.material).forEach(m => base.set(m.name, m)); });
    const varianti = (Array.isArray(cfg.colori) ? cfg.colori : [cfg.colori]).map(sost => {
      const mm = {};
      for (const [n, m] of base) {
        const c = m.clone(); c.roughness = 0.88; c.metalness = 0; c.envMapIntensity = 0.35;
        if (sost[n] !== undefined) c.color.set(sost[n]);
        mm[n] = c;
      }
      return mm;
    });
    const clips = Object.fromEntries(gltf.animations.map(a => [a.name, a]));
    return { nome, gltf, scala, piede: -box.min.y * scala, varianti, clips, pool: cfg.pool || 4 };
  }
  function nuovo(sp) {
    const grp = new THREE.Group(), modello = SkeletonUtils.clone(sp.gltf.scene);
    modello.scale.setScalar(sp.scala); modello.position.y = sp.piede;
    grp.add(modello); grp.visible = false;
    const mixer = new THREE.AnimationMixer(modello), az = {};
    for (const n in sp.clips) { az[n] = mixer.clipAction(sp.clips[n]); az[n].enabled = true; }
    if (az.Idle) { az.Idle.play(); }
    if (az.Jump) { az.Jump.setLoop(THREE.LoopOnce, 1); az.Jump.clampWhenFinished = true; az.Jump.play(); az.Jump.paused = true; az.Jump.weight = 0; }
    const meshes = []; modello.traverse(o => { if (o.isMesh) { o.frustumCulled = false; o.castShadow = true; meshes.push(o); } });
    scene.add(grp);
    return { grp, modello, mixer, az, meshes, sp, indice: -1, spin: 0 };
  }
  function vesti(o, v) {
    const mm = o.sp.varianti[v % o.sp.varianti.length];
    for (const m of o.meshes) m.material = Array.isArray(m.material) ? m.material.map(x => mm[x.name] || x) : (mm[m.material.name] || m.material);
  }

  // ── caricamento (in background: il gioco parte comunque) ──
  const nomi = [...new Set([...Object.values(SPECIE).map(s => s.url), AQUILA.url])];
  Promise.all(nomi.map(u => loader.loadAsync(u).then(g => [u, g]))).then(coppie => {
    const g = Object.fromEntries(coppie);
    for (const [nome, cfg] of Object.entries(SPECIE)) {
      specie[nome] = prepara(nome, cfg, g[cfg.url], cfg.alto);
      libere[nome] = Array.from({ length: cfg.pool }, () => nuovo(specie[nome]));
    }
    // aquile: un modello solo, colori per nome di materiale
    const sp = prepara('aquila', { colori: [AQUILA.colori], pool: AQUILA.n }, g[AQUILA.url], AQUILA.apertura, true);
    aquile = Array.from({ length: AQUILA.n }, (_, k) => { const o = nuovo(sp); vesti(o, 0); o.grp.visible = true; o.k = k; return o; });
    pronto = true;
  }).catch(e => console.warn('animali non caricati:', e));

  // ── a ogni frame ──
  const lb = (v) => { let a = 0, b = segs.length; while (a < b) { const m = (a + b) >> 1; if (segs[m] < v) a = m + 1; else b = m; } return a; };
  const ang = (a, b) => { let d = (b - a) % 6.283185; if (d > Math.PI) d -= 6.283185; if (d < -Math.PI) d += 6.283185; return d; };

  function aggiorna({ posSeg, giocatore, heading, a, dt, musica }) {
    if (!pronto) return;
    dt = Math.min(dt, 0.1);
    dance += (Math.min(1, Math.max(0, (a - 0.12) / 0.4)) - dance) * Math.min(1, dt * 3);       // il ballo parte e finisce dolce
    scatto = Math.max(0, scatto - dt * 0.7);
    // quanti salti per battito: oltre i 150 BPM uno ogni due battiti (le gambe non ce la fanno)
    const mezzo = musica.bpm > 150 ? 0.5 : 1, tempo = (musica.battito + musica.fase) * mezzo;

    // chi deve esserci: davanti fino a ~34.000 unità, dietro poche decine di segmenti
    const lo = lb(posSeg - 30), hi = lb(posSeg + 170);
    for (const [i, o] of attivi) if (i < lo || i >= hi) { o.grp.visible = false; o.indice = -1; libere[o.sp.nome].push(o); attivi.delete(i); }
    for (let i = lo; i < hi; i++) {
      if (attivi.has(i)) continue;
      const d = animali[i], pool = libere[d.specie]; if (!pool || !pool.length) continue;
      const o = pool.pop(); o.indice = i; o.spin = 0;
      vesti(o, d.variante);
      if (o.az.Idle) o.az.Idle.time = d.ph * o.az.Idle.getClip().duration;
      o.grp.visible = true; attivi.set(i, o);
    }

    for (const [i, o] of attivi) {
      const d = animali[i];
      // si voltano verso la strada quando ballano; al drop girano su se stessi
      const verso = Math.atan2(giocatore.x - d.x, giocatore.z - d.z);
      d.yaw += ang(d.yaw, verso) * Math.min(1, dt * 2.2) * dance * 0.9 + o.spin * dt;
      o.spin = scatto > 0.01 ? 7 * scatto * dance : 0;
      // salto agganciato alla fase del battito (con l'onda che attraversa il branco)
      const p = (((tempo - d.ritardo * dance) % 1) + 1) % 1;
      const jump = o.az.Jump, idle = o.az.Idle;
      if (jump) {
        const dur = jump.getClip().duration;
        jump.paused = true; jump.time = Math.min(dur * 0.999, ((p + 0.38) % 1) * dur);
        jump.weight = dance;                       // .weight, non setEffectiveWeight: il mixer lo ricalcola da .weight a ogni giro
      }
      if (idle) idle.weight = 1 - 0.9 * dance;
      o.mixer.update(dt);
      // il battito della cassa: leggera spinta in su e schiacciamento
      const cassa = musica.cassa * dance;
      // la clip stacca le zampe solo di ~25 cm: sopra ci metto un rimbalzo in più nella fase in cui sono in aria
      const frazione = (p + 0.38) % 1, rimbalzo = frazione > 0.25 && frazione < 0.58 ? Math.sin((frazione - 0.25) / 0.33 * Math.PI) : 0;
      o.grp.position.set(d.x, d.y + dance * rimbalzo * 330 * d.s, d.z);
      o.grp.rotation.y = d.yaw;
      o.grp.scale.set(d.s * (1 + 0.05 * cassa), d.s * (1 - 0.07 * cassa), d.s * (1 + 0.05 * cassa));
    }

    // aquile: girano in alto davanti al giocatore; il battito d'ali segue il tempo quando si balla
    tAq += dt;
    aquile.forEach(o => {
      const k = o.k, T = tAq * (0.16 + k * 0.03) + k * 2.1, R = 8000 + k * 2500;
      const cx = giocatore.x + Math.sin(heading) * 21000, cz = giocatore.z + Math.cos(heading) * 21000;
      const x = cx + Math.cos(T) * R, z = cz + Math.sin(T) * R, y = giocatore.y + 9500 + k * 2500 + Math.sin(tAq * 0.4 + k) * 700;
      o.grp.position.set(x, y, z);
      o.grp.rotation.y = Math.atan2(-Math.sin(T) * R, Math.cos(T) * R);     // tangente dell'orbita
      o.grp.rotation.z = -0.45;                                              // inclinata in curva
      o.grp.scale.setScalar(1);
      const volo = o.az.Flying || o.az.Idle;
      if (volo) {
        if (!o.avviato) { volo.play(); o.avviato = true; }
        if (dance > 0.15) { volo.paused = true; volo.time = (((tempo * 1) % 1 + 1) % 1) * volo.getClip().duration; }
        else volo.paused = false;
        o.mixer.update(dance > 0.15 ? 0 : dt);
      }
    });
  }

  return { aggiorna, scatta() { scatto = 1; }, get attivi() { return attivi.size; }, get pronto() { return pronto; },
           animali, branchi, get vivi() { return [...attivi.values()]; }, get aquile() { return aquile; }, get danza() { return dance; } };
}
