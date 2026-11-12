// IL PLURIBALL — la barra scudo. Lungo la pista galleggiano dei rotoli di pluriball: ogni rotolo preso riempie la
// BARRA PLURIBALL di PLURIBALL.perRotolo punti (su PLURIBALL.max). Finché la barra non è vuota il protagonista è avvolto
// in una bolla di pluriball, e ogni colpo subito consuma prima la barra e solo poi la vita. La barra non si ricarica da
// sola e si perde se si muore; quando si svuota la bolla scoppia.
//
// Il modello del rotolo (assets/models/pluriball/rotolo.glb, da tools/pluriball/modello_rotolo.py) è un pezzo solo.
// Il protagonista AVVOLTO è il busto del pony generato (assets/models/pluriball/pony-skin.glb, da tools/pluriball/pony_skin.py:
// scatola di pluriball, gonna, testa, criniera, coda, braccia) più le GAMBE VERE del protagonista, che qui si estraggono dalla
// sua mesh (i triangoli pesati sulle ossa delle gambe): quelle del pony non coincidevano con lo scheletro e si sfaldavano.
// Il busto si lega allo scheletro del protagonista con le matrici di legatura del pony (è stato legato nella sua posa); le
// gambe con quelle del protagonista. Finché c'è barra prendono il posto della mesh normale e galoppano con le stesse clip. Con lo sprite (nessun modello) resta una bolla procedurale: un ellissoide di bolle
// semitrasparenti agganciato al gruppo.
//
// Il modulo non sa niente del resto del gioco: riceve la strada (posToWorld), a ogni fotogramma lo stato del giocatore,
// e il gioco gli passa ogni colpo subito (`assorbi`) e riceve gli eventi: preso, scoppia.
//
// REGOLA DEL LIVELLO 0: niente qui batte a tempo. Se un giorno il pluriball si lega alla musica, passa da un bersaglio
// della centralina (3d/centralina.js), mai da musica.* direttamente.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export const PLURIBALL = {
  nome: 'PLURIBALL',                            // ASCII: va nell'HUD a pixel
  url: 'assets/models/pluriball/rotolo.glb',
  pelle: 'assets/models/pluriball/pony-skin.glb',   // il protagonista avvolto
  max: 100,                                     // punti di barra
  perRotolo: 30,                                // punti per rotolo
  ogni: 300000,                                 // un rotolo ogni ~25 s a tutta (3-4 per tappa)
  ripresa: 20,                                  // secondi prima che un rotolo preso ricompaia
  lungo: 1500,                                  // unità di gioco: il lato lungo del rotolo
  avviso: 0.15,                                 // sotto questa quota di barra la bolla lampeggia
};

const LUNGO_MODELLO = 0.98;                     // m: il lato lungo del modello nativo (asse Z nel GLB)
const K = PLURIBALL.lungo / LUNGO_MODELLO;
const VISTA = 90000;                            // oltre questa distanza i rotoli non si aggiornano
const limit = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// la texture delle bolle: cerchi sfalsati con riflesso, bianco-azzurro, per il guscio
function texBolle() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256; const g = c.getContext('2d');
  g.fillStyle = 'rgba(190,230,245,0.35)'; g.fillRect(0, 0, 256, 256);
  for (let r = 0; r < 8; r++) for (let q = 0; q < 8; q++) {
    const x = q * 32 + (r % 2 ? 16 : 0) + 16, y = r * 32 + 16, R = 14.5;
    g.fillStyle = 'rgba(150,210,235,0.55)'; g.beginPath(); g.arc(x, y, R, 0, 6.2832); g.fill();
    const l = g.createRadialGradient(x - 5, y - 5, 1, x, y, R);
    l.addColorStop(0, 'rgba(255,255,255,0.95)'); l.addColorStop(0.4, 'rgba(235,248,255,0.4)'); l.addColorStop(1, 'rgba(120,190,225,0)');
    g.fillStyle = l; g.beginPath(); g.arc(x, y, R, 0, 6.2832); g.fill();
    g.strokeStyle = 'rgba(40,120,170,0.9)'; g.lineWidth = 2; g.beginPath(); g.arc(x, y, R, 0, 6.2832); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4;
  return t;
}
function texAlone() {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const l = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  l.addColorStop(0, 'rgba(210,245,255,0.9)'); l.addColorStop(0.35, 'rgba(120,205,240,0.35)'); l.addColorStop(1, 'rgba(80,180,230,0)');
  g.fillStyle = l; g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

export function creaPluriball({ scene, posToWorld, gapTo, TRACK_LENGTH, HORSE_HEIGHT, evento }) {
  // ── i rotoli da raccogliere ─────────────────────────────────────────────
  let pronto = false;
  const matAlone = new THREE.SpriteMaterial({ map: texAlone(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0.6 });
  const rotoli = [], n = Math.max(4, Math.round(TRACK_LENGTH / PLURIBALL.ogni));
  for (let i = 0; i < n; i++) {
    const gr = new THREE.Group(), rullo = new THREE.Group(), alone = new THREE.Sprite(matAlone);
    alone.scale.setScalar(PLURIBALL.lungo * 2.0); gr.add(rullo, alone); gr.visible = false; scene.add(gr);
    rotoli.push({ gr, rullo, alone, pos: ((i + 0.5) * (TRACK_LENGTH / n) + 40000) % TRACK_LENGTH, lat: Math.random() * 1.2 - 0.6,
                  active: true, respawnT: 0, preso: -1, t: Math.random() * 6 });
  }
  new GLTFLoader().load(PLURIBALL.url, gltf => {
    const m = gltf.scene; m.scale.setScalar(K);
    m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.material.emissive = new THREE.Color(0x2f6f8f); o.material.emissiveIntensity = 0.35; } });
    for (const r of rotoli) r.rullo.add(m.clone());
    pronto = true;
    console.log('Pluriball caricato:', PLURIBALL.url, '·', n, 'rotoli');
  }, undefined, () => console.warn('Pluriball: modello non trovato', PLURIBALL.url));

  // ── il protagonista avvolto: la mesh del pony, legata allo scheletro del protagonista ──
  let ponySk = null;
  new GLTFLoader().load(PLURIBALL.pelle, gltf => {
    gltf.scene.traverse(o => { if (o.isSkinnedMesh && !ponySk) ponySk = o; });
    if (ponySk) console.log('Pluriball (protagonista avvolto) caricato:', PLURIBALL.pelle);
  }, undefined, () => console.warn('Pluriball: protagonista avvolto non trovato', PLURIBALL.pelle));
  const veste = new WeakMap();       // modello del protagonista → { sk: la sua mesh, pm: il busto avvolto, gm: le sue gambe } (o null)
  function vestito(m) {
    if (veste.has(m)) return veste.get(m);
    let sk = null; m.traverse(o => { if (o.isSkinnedMesh && !o.userData.pluriball && !sk) sk = o; });
    let r = null;
    if (sk && ponySk) {
      const perNome = new Map(); sk.skeleton.bones.forEach(b => perNome.set(b.name, b));
      const ossa = ponySk.skeleton.bones.map(b => perNome.get(b.name));
      if (ossa.every(Boolean)) {
        const pm = ponySk.clone(); pm.userData.pluriball = true;
        pm.material = ponySk.material.clone(); pm.material.side = THREE.DoubleSide;
        pm.position.copy(sk.position); pm.quaternion.copy(sk.quaternion); pm.scale.copy(sk.scale);
        pm.bind(new THREE.Skeleton(ossa, ponySk.skeleton.boneInverses.map(x => x.clone())), sk.bindMatrix);
        pm.frustumCulled = false; pm.castShadow = true; pm.visible = false;
        // le gambe vere: gli stessi vertici della mesh del protagonista, solo i triangoli che dipendono dalle ossa delle gambe
        const g = sk.geometry, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, ix = g.index;
        const ossaGamba = new Set(sk.skeleton.bones.map((b, i) => /^(Front|Rear)/.test(b.name) ? i : -1).filter(i => i >= 0));
        const diGamba = new Uint8Array(si.count);
        for (let i = 0; i < si.count; i++) {
          let gw = 0; for (let c = 0; c < 4; c++) if (ossaGamba.has(si.getComponent(i, c))) gw += sw.getComponent(i, c);
          diGamba[i] = gw > 0.5 ? 1 : 0;
        }
        const tri = [];
        for (let t = 0; t < ix.count; t += 3) { const a = ix.getX(t), b = ix.getX(t + 1), c = ix.getX(t + 2); if (diGamba[a] && diGamba[b] && diGamba[c]) tri.push(a, b, c); }
        const gg = new THREE.BufferGeometry();
        for (const k in g.attributes) gg.setAttribute(k, g.attributes[k]);
        gg.setIndex(tri);
        const gm = new THREE.SkinnedMesh(gg, sk.material); gm.userData.pluriball = true;
        gm.position.copy(sk.position); gm.quaternion.copy(sk.quaternion); gm.scale.copy(sk.scale);
        gm.bind(sk.skeleton, sk.bindMatrix); gm.frustumCulled = false; gm.castShadow = true; gm.visible = false;
        sk.parent.add(pm, gm); r = { sk, pm, gm };
      } else console.warn('Pluriball: le ossa del pony non corrispondono a quelle del protagonista');
    }
    veste.set(m, r); return r;
  }
  let ultimo = null;                 // l'ultimo vestito mostrato, per rimettere a posto la mesh normale
  function ripristina() { if (ultimo) { ultimo.sk.visible = true; ultimo.pm.visible = ultimo.gm.visible = false; ultimo = null; } }
  // sceglie quale mesh del protagonista si vede; restituisce true se c'è un modello avvolto (e allora la bolla procedurale sta spenta)
  function vesti(player, avvolto) {
    const m = player.model && player.model.visible ? player.model : null, v = m ? vestito(m) : null;
    if (ultimo && ultimo !== v) ripristina();
    if (!v) return false;
    v.sk.visible = !avvolto; v.pm.visible = v.gm.visible = avvolto; ultimo = v;
    return true;
  }

  // ── la bolla che avvolge il protagonista (se non c'è un modello avvolto: sprite) ──
  const matGuscio = new THREE.MeshStandardMaterial({ map: texBolle(), color: 0xffffff, roughness: 0.12, metalness: 0, transparent: true, opacity: 0.5,
                                                     side: THREE.DoubleSide, depthWrite: false, emissive: 0x2a7da6, emissiveIntensity: 0.5 });
  matGuscio.map.repeat.set(10, 5);
  const guscio = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 26), matGuscio);
  guscio.visible = false; guscio.renderOrder = 5; guscio.frustumCulled = false;
  const misure = new WeakMap();      // modello → {c, semi}: le dimensioni del guscio, nello spazio locale del modello

  // le ossa del modello, nel suo spazio locale: dicono dov'è il corpo e quanto è grande
  function misura(m) {
    let r = misure.get(m); if (r) return r;
    let skinned = null; m.traverse(o => { if (o.isSkinnedMesh && !skinned) skinned = o; });
    m.updateWorldMatrix(true, true);
    const inv = new THREE.Matrix4().copy(m.matrixWorld).invert(), box = new THREE.Box3(), v = new THREE.Vector3();
    if (skinned && skinned.skeleton.bones.length) for (const b of skinned.skeleton.bones) { b.getWorldPosition(v).applyMatrix4(inv); box.expandByPoint(v); }
    const s = m.scale.x || 1;
    if (box.isEmpty()) box.set(new THREE.Vector3(-0.4 * HORSE_HEIGHT / s, 0, -0.9 * HORSE_HEIGHT / s), new THREE.Vector3(0.4 * HORSE_HEIGHT / s, HORSE_HEIGHT / s, 0.9 * HORSE_HEIGHT / s));
    const c = box.getCenter(new THREE.Vector3()), d = box.getSize(new THREE.Vector3());
    // le ossa stanno dentro la pelle: il guscio deve starle attorno con un po' d'aria
    r = { c, semi: new THREE.Vector3(Math.max(d.x * 0.62, d.y * 0.30), d.y * 0.54, Math.max(d.z * 0.6, d.y * 0.5)) };
    misure.set(m, r); return r;
  }
  function aggancia(player) {
    const m = player.model && player.model.visible ? player.model : null;
    const padre = m || player.group;
    if (guscio.parent !== padre) padre.add(guscio);
    if (m) { const r = misura(m); guscio.position.copy(r.c); guscio.userData.semi = r.semi; }
    else { guscio.position.set(0, HORSE_HEIGHT * 0.55, 0); guscio.userData.semi = new THREE.Vector3(HORSE_HEIGHT * 0.7, HORSE_HEIGHT * 0.72, HORSE_HEIGHT * 0.85); }
  }

  // ── stato ───────────────────────────────────────────────────────────────
  let scudo = 0;                      // punti di barra
  let da = 0;                         // da quanto tempo la bolla è su (per gonfiarla)
  let urto = 0;                       // impulso quando la bolla incassa un colpo
  let scoppio = 0;                    // > 0: la bolla sta scoppiando (secondi che restano)
  let lampoOra = false;               // la barra è quasi vuota e questo è il momento «spento» del lampeggio

  function azzera() { scudo = 0; scoppio = 0; da = 0; guscio.visible = false; ripristina(); }

  // un colpo subito: restituisce il danno che ARRIVA alla vita (la barra prende il primo)
  function assorbi(danno) {
    if (scudo <= 0) return danno;
    const preso = Math.min(scudo, danno);
    scudo -= preso; urto = 1;
    if (scudo <= 0) { scudo = 0; scoppio = 0.3; evento('scoppia'); }
    return danno - preso;
  }

  const A = new THREE.Vector3(), volo = new THREE.Vector3();
  // un fotogramma. G = { racing (false in modalità libera), playerX, giocatore (Vector3), player (l'attore) }
  function aggiorna(dt, G) {
    for (const r of rotoli) {
      if (!G.racing) { r.gr.visible = false; continue; }
      if (!r.active) { r.respawnT -= dt; if (r.respawnT <= 0) { r.active = true; r.preso = -1; } else { r.gr.visible = false; continue; } }
      const gap = gapTo(r.pos), lontano = Math.abs(gap) > VISTA;
      r.gr.visible = !lontano && pronto;
      if (lontano || !pronto) continue;
      r.t += dt;
      posToWorld(r.pos, r.lat, A);
      A.y += 800 + Math.sin(r.t * 2.2) * 130;                               // galleggia
      r.gr.position.copy(A);
      r.gr.rotation.y += dt * 1.1;                                          // gira come un'insegna...
      r.rullo.rotation.z += dt * 2.2;                                       // ...e su se stesso, come un rullo (l'asse del rotolo è Z)
      r.alone.scale.setScalar(PLURIBALL.lungo * 2.0 * (1 + 0.06 * Math.sin(r.t * 5)));
      if (r.preso >= 0) {                                                   // preso: vola verso il giocatore e rimpicciolisce
        r.preso += dt; const u = Math.min(1, r.preso / 0.4), e = u * u * (3 - 2 * u);
        volo.copy(G.giocatore); volo.y += HORSE_HEIGHT * 0.6; r.gr.position.lerp(volo, e); r.gr.scale.setScalar(Math.max(0.02, 1 - e));
        if (u >= 1) { r.active = false; r.respawnT = PLURIBALL.ripresa; r.gr.visible = false; r.gr.scale.setScalar(1); }
      } else if (scudo < PLURIBALL.max && Math.abs(gap) < 1900 && Math.abs(r.lat - G.playerX) < 0.55) {
        const prima = scudo; scudo = Math.min(PLURIBALL.max, scudo + PLURIBALL.perRotolo); r.preso = 0;
        if (prima <= 0) da = 0;                                             // bolla nuova: si gonfia
        scoppio = 0;
        evento('preso', scudo - prima);
      }
    }
    if (G.player && G.racing) {
      if (scudo > 0 || scoppio > 0) aggancia(G.player);
      disegnaGuscio(dt);
      if (vesti(G.player, scudo > 0 && scoppio <= 0 && !lampoOra)) guscio.visible = false;   // col modello avvolto la bolla procedurale non serve
    } else if (!G.racing) { guscio.visible = false; ripristina(); }
  }

  // la bolla: si gonfia (con un rimbalzo), respira, trema quando incassa, sbiadisce con la barra, lampeggia in fondo e scoppia
  function disegnaGuscio(dt) {
    urto = Math.max(0, urto - dt * 4);
    const semi = guscio.userData.semi || new THREE.Vector3(1, 1, 1);
    if (scoppio > 0) {                                                      // scoppio: si allarga di colpo e svanisce
      scoppio -= dt; const u = 1 - Math.max(0, scoppio) / 0.3;
      guscio.scale.copy(semi).multiplyScalar(1 + 0.5 * u); matGuscio.opacity = 0.5 * (1 - u); guscio.visible = true;
      if (scoppio <= 0) guscio.visible = false;
      return;
    }
    if (scudo <= 0) { guscio.visible = false; lampoOra = false; return; }
    da += dt;
    const g = limit(da / 0.4, 0, 1), gonfia = 1 - Math.pow(1 - g, 3) * Math.cos(g * 9);           // sale oltre 1 e si assesta
    guscio.scale.copy(semi).multiplyScalar(Math.max(0.05, gonfia) * (1 + 0.025 * Math.sin(da * 3.1) + 0.09 * urto));
    guscio.rotation.y = da * 0.25; guscio.visible = true;                   // il guscio ruota piano: le bolle scintillano
    const q = scudo / PLURIBALL.max, lampo = q < PLURIBALL.avviso && Math.sin(da * 16) > 0;
    lampoOra = lampo;
    matGuscio.opacity = (lampo ? 0.15 : 0.28 + 0.24 * q) + 0.2 * urto;       // più barra = più bolla
  }

  return {
    aggiorna, azzera, assorbi,
    get pronto() { return pronto; },
    get scudo() { return scudo; },
    // per il pilota automatico: la corsia del rotolo più vicino davanti, se la barra non è piena
    corsiaPerPilota() {
      if (scudo >= PLURIBALL.max) return null;
      let best = null, bg = 45000;
      for (const r of rotoli) { if (!r.active || r.preso >= 0) continue; const g = gapTo(r.pos); if (g > 0 && g < bg) { bg = g; best = r.lat; } }
      return best;
    },
    // per i test
    get rotoli() { return rotoli; },
    get guscio() { return guscio; },
    get vestito() { return ultimo && ultimo.pm.visible; },
    dai(punti = PLURIBALL.perRotolo) { if (scudo <= 0) da = 0; scudo = limit(scudo + punti, 0, PLURIBALL.max); scoppio = 0; },
    // mette un rotolo a `davanti` unità dal giocatore, in corsia `lat`
    prova(position, davanti = 20000, lat = 0) { const r = rotoli.find(x => x.active && x.preso < 0); if (r) { r.pos = ((position + davanti) % TRACK_LENGTH + TRACK_LENGTH) % TRACK_LENGTH; r.lat = lat; } return r; },
  };
}
