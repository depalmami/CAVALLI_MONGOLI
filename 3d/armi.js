// LE ARMI IN MANO AL PROTAGONISTA. Il cavallo di cartone ha un solo braccio visibile: quello destro, che tiene le redini
// vicino al muso. L'arma equipaggiata (curWeapon) si agguanta lì: un punto-mano figlio dell'osso che muove il braccio, così
// segue il galoppo, la piega della schiena e i colpi presi senza che nessuno la animi a parte.
//
// Cosa si vede: se esiste assets/models/armi/<chiave>.glb (chiave = whip, mace, saber, bow) si usa quello; finché manca c'è un
// segnaposto disegnato qui dentro, in modo che il gioco sia giocabile e il punto-mano si possa tarare. Il GLB va fatto con
// l'impugnatura nell'ORIGINE e la lunghezza lungo +Y (arco: corda verso -Z, cioè verso il cavaliere); la scala non conta,
// viene riportata a POSE[chiave].lungo. I pugni non hanno nulla in mano.
//
// UNITÀ. Il punto-mano e le armi sono nello spazio NATIVO del modello (1 unità = 1 m, il cavallo è alto 1,83): è lo spazio
// delle coordinate dei vertici, e la scala fino al mondo di gioco (×~765) la mette la catena delle ossa. Perciò una sciabola
// di 0,85 vale ~650 unità di gioco, metà cavallo.
//
// Il modulo non sa niente del resto del gioco: a ogni fotogramma `aggiorna(attore, chiave)` e basta. Il fendente lo legge
// dall'attore (swingC, swingDir: gli stessi numeri che piegano il corpo, vedi HorseActor.update).
//
// REGOLA DEL LIVELLO 0: niente qui batte a tempo.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export const ARMI = {
  cartella: 'assets/models/armi/',
  osso: 'Torso3',                    // l'osso che pesa quasi tutta la manica (150 vertici su 166); poi segue il collo
  mano: [-0.24, 1.30, 0.56],         // m nativi: x<0 = lato destro del cavallo, y su, z avanti (la testa è a z≈0,53)
};

// lungo: lunghezza in m nativi a cui si porta il GLB · alza: inclinazione a riposo verso avanti (rad) · fuori: inclinazione a
// riposo verso il lato destro (rad): la camera di corsa sta DIETRO il cavallo, un'arma dritta in alto si vedrebbe di taglio e
// nascosta dal collo, inclinata in fuori sporge accanto · giro: apertura del fendente verso il lato del bersaglio (rad) ·
// avanti: quanto si china in avanti sul colpo (rad) · vira (facoltativo): giro attorno alla propria lunghezza (rad), per mostrare alla
// camera il profilo di un'arma che di taglio sparirebbe: l'arco, tenuto dritto, da dietro è una stecca; con vira<0 i flettenti
// si aprono verso l'esterno (-X)
export const POSE = {
  whip:  { lungo: 1.00, alza: 0.55, fuori: 0.35, giro: 1.9, avanti: 0.25 },
  mace:  { lungo: 0.60, alza: 0.30, fuori: 0.30, giro: 1.7, avanti: 0.35 },
  saber: { lungo: 0.85, alza: 0.40, fuori: 0.35, giro: 1.8, avanti: 0.30 },
  bow:   { lungo: 0.95, alza: 0.00, fuori: 0.20, giro: 0.30, avanti: 0.10, vira: -0.7 },
};

// ── segnaposto: ogni arma ha l'impugnatura nell'origine e la lunghezza lungo +Y ──
const mat = (color, metalness, roughness) => new THREE.MeshStandardMaterial({ color, metalness, roughness });
const MAT = { legno: mat(0x6b4a2b, 0, 0.8), cuoio: mat(0x3b2a1c, 0, 0.9), ferro: mat(0xaeb6c2, 0.85, 0.35),
              ottone: mat(0xc9a24a, 0.7, 0.4), corda: mat(0xe8dcc0, 0, 0.9) };
const pezzo = (geo, m) => { const o = new THREE.Mesh(geo, m); o.castShadow = true; return o; };
const cilindro = (rBase, rTesta, h, m, y0) => { const o = pezzo(new THREE.CylinderGeometry(rTesta, rBase, h, 10), m); o.position.y = y0 + h/2; return o; };
const V = (x, y, z) => new THREE.Vector3(x, y, z);

function sciabola() {
  const g = new THREE.Group();
  g.add(cilindro(0.020, 0.018, 0.16, MAT.cuoio, -0.08));
  const pomo = pezzo(new THREE.SphereGeometry(0.026, 10, 8), MAT.ottone); pomo.position.y = -0.085; g.add(pomo);
  const guardia = pezzo(new THREE.BoxGeometry(0.14, 0.018, 0.04), MAT.ottone); guardia.position.y = 0.085; g.add(guardia);
  const curva = new THREE.CatmullRomCurve3([V(0, 0.09, 0), V(0, 0.35, 0.01), V(0, 0.62, 0.06), V(0, 0.82, 0.15)]);
  const lama = pezzo(new THREE.TubeGeometry(curva, 24, 0.034, 4, false), MAT.ferro); lama.scale.x = 0.9;    // quasi tonda in sezione: da dietro (la camera di corsa) una lama sottile sparisce di taglio
  g.add(lama);
  return g;
}
function mazza() {
  const g = new THREE.Group();
  g.add(cilindro(0.022, 0.018, 0.50, MAT.legno, -0.06));
  const testa = pezzo(new THREE.SphereGeometry(0.075, 12, 10), MAT.ferro); testa.position.y = 0.52; g.add(testa);
  const su = V(0, 1, 0), d = new THREE.Vector3();
  const punte = [V(0, 1, 0), V(0, -1, 0)];
  for (let i = 0; i < 6; i++) { const a = i/6 * Math.PI*2; punte.push(V(Math.cos(a), 0.35, Math.sin(a)), V(Math.cos(a + Math.PI/6), -0.45, Math.sin(a + Math.PI/6))); }
  for (const p of punte) {
    d.copy(p).normalize();
    const cono = pezzo(new THREE.ConeGeometry(0.02, 0.07, 6), MAT.ferro);
    cono.quaternion.setFromUnitVectors(su, d);
    cono.position.copy(d).multiplyScalar(0.075 + 0.03); cono.position.y += 0.52;
    g.add(cono);
  }
  return g;
}
function frusta() {
  const g = new THREE.Group();
  g.add(cilindro(0.024, 0.02, 0.24, MAT.cuoio, -0.10));
  // la striscia sale dal manico e poi strascica all'indietro (-Z): il cavallo galoppa in avanti, la frusta resta dietro
  const curva = new THREE.CatmullRomCurve3([V(0, 0.14, 0), V(0, 0.30, -0.10), V(0, 0.36, -0.30), V(0, 0.28, -0.52), V(0, 0.10, -0.72), V(0, -0.06, -0.86)]);
  g.add(pezzo(new THREE.TubeGeometry(curva, 28, 0.011, 5, false), MAT.cuoio));
  return g;
}
function arco() {
  const g = new THREE.Group();
  // i flettenti sporgono verso +Z (il bersaglio), la corda sta dalla parte del cavaliere: z = -0.11, dritta fra le due punte
  const curva = new THREE.QuadraticBezierCurve3(V(0, -0.46, -0.11), V(0, 0, 0.11), V(0, 0.46, -0.11));
  g.add(pezzo(new THREE.TubeGeometry(curva, 24, 0.016, 6, false), MAT.legno));
  const corda = pezzo(new THREE.CylinderGeometry(0.004, 0.004, 0.92, 4), MAT.corda); corda.position.z = -0.11; g.add(corda);
  const impugnatura = cilindro(0.022, 0.022, 0.12, MAT.cuoio, -0.06); g.add(impugnatura);
  return g;
}
const SEGNAPOSTO = { whip: frusta, mace: mazza, saber: sciabola, bow: arco };

// ── la FRECCIA in volo (assets/models/armi/freccia.glb): lunghezza lungo +Y con la punta in su, origine a metà asta (vedi
// tools/armi/prepara-arma.py). Il volo (`frecce` in horse-racing-3d.html) la vuole con la punta verso +Z, dove lo guarda `lookAt`:
// `vestiFreccia` la mette in un perno ruotato di 90°. `grosso` ingrossa solo la sezione (non la lunghezza): da dietro, a 40 metri
// di pista, un'asta vera sarebbe un filo. Se il file manca resta il cilindro con il cono di prima.
let frecciaPromessa = null;
export function caricaFreccia() {
  if (!frecciaPromessa) frecciaPromessa = new Promise(res => new GLTFLoader().load(ARMI.cartella + 'freccia.glb', gltf => {
    const sz = new THREE.Box3().setFromObject(gltf.scene).getSize(new THREE.Vector3()), w = new THREE.Group();
    gltf.scene.traverse(o => { if (o.isMesh) o.castShadow = true; });
    w.add(gltf.scene); w.scale.setScalar(1 / (sz.y || 1));
    console.log('Freccia caricata:', ARMI.cartella + 'freccia.glb', '· lunghezza', sz.y.toFixed(2), 'sezione', sz.x.toFixed(2), sz.z.toFixed(2));
    res(w);
  }, undefined, () => res(null)));
  return frecciaPromessa;
}
export function vestiFreccia(volo, modello, lunghezza, grosso = 1) {
  const m = modello.clone(true), perno = new THREE.Group();
  m.scale.multiply(new THREE.Vector3(lunghezza * grosso, lunghezza, lunghezza * grosso));
  perno.rotation.x = Math.PI / 2; perno.add(m); volo.add(perno);
  return perno;
}

// ── la CASSA-ARMA (assets/models/armi/cassa.glb): la scatola di cartone che si raccoglie in pista ──
// Il file è già centrato nel suo ingombro con il lato maggiore a 1 (vedi tools/armi/prepara-arma.py --cassa); qui si ricentra
// per sicurezza, la si porta alla misura di gioco (`lato`, unità di gioco) e la si tinge col colore dell'arma che contiene:
// un po' di emissivo sul cartone e un guscio additivo appena più grande, così da lontano si distingue la frusta dalla mazza.
// Finché il GLB non c'è (o manca) resta il cubo luminoso che il gioco disegnava prima: niente si rompe.
let cassaPromessa = null;
export function caricaCassa() {
  if (!cassaPromessa) cassaPromessa = new Promise(res => new GLTFLoader().load(ARMI.cartella + 'cassa.glb', gltf => {
    const box = new THREE.Box3().setFromObject(gltf.scene), sz = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
    const m = Math.max(sz.x, sz.y, sz.z) || 1, w = new THREE.Group();
    gltf.scene.position.sub(c); gltf.scene.traverse(o => { if (o.isMesh) o.castShadow = true; });
    w.add(gltf.scene); w.scale.setScalar(1 / m);
    console.log('Cassa-arma caricata:', ARMI.cartella + 'cassa.glb', '· ingombro', sz.x.toFixed(2), sz.y.toFixed(2), sz.z.toFixed(2));
    res({ modello: w, dim: sz.clone().multiplyScalar(1 / m) });
  }, undefined, () => res(null)));
  return cassaPromessa;
}
const tinte = new Map();                                                   // (materiale, colore) → copia tinta: una per arma, non una per cassa
function tinta(mat, colore) {
  const k = mat.uuid + ':' + colore;
  if (!tinte.has(k)) { const t = mat.clone(); if (t.emissive) { t.emissive.set(colore); t.emissiveIntensity = 0.18; } tinte.set(k, t); }
  return tinte.get(k);
}
const gusci = new Map();                                                   // colore → materiale del guscio
export function vestiCassa(gruppo, cassa, colore, lato) {
  while (gruppo.children.length) gruppo.remove(gruppo.children[0]);        // via il cubo luminoso di ripiego
  const m = cassa.modello.clone(true);
  m.traverse(o => { if (o.isMesh) o.material = tinta(o.material, colore); });
  m.scale.multiplyScalar(lato); gruppo.add(m);
  // l'aura: un riempimento appena visibile (le armi chiare, la sciabola, sbiancherebbero il cartone) e una gabbia di spigoli del
  // colore dell'arma, che da lontano si legge anche quando il colore è pallido
  if (!gusci.has(colore)) gusci.set(colore, {
    riempi: new THREE.MeshBasicMaterial({ color: colore, transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending, depthWrite: false }),
    bordo: new THREE.LineBasicMaterial({ color: colore, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false }) });
  const g = gusci.get(colore), aura = new THREE.Group();
  aura.add(new THREE.Mesh(GEO_UNO, g.riempi), new THREE.LineSegments(GEO_SPIGOLI, g.bordo));
  aura.scale.set(cassa.dim.x * lato * 1.1, cassa.dim.y * lato * 1.1, cassa.dim.z * lato * 1.1);
  gruppo.add(aura);
}
const GEO_UNO = new THREE.BoxGeometry(1, 1, 1), GEO_SPIGOLI = new THREE.EdgesGeometry(GEO_UNO);

export function creaArmi() {
  const radice = new THREE.Object3D(); radice.matrixAutoUpdate = false;   // il punto-mano: nello spazio del modello, figlio dell'osso
  const arma = new THREE.Group();                                         // il perno che ruota nel fendente
  radice.add(arma);
  let attore = null, aggancio = false, chiave = null, avvisato = false;
  const cache = new Map();                                                // chiave → Promise<Object3D|null> (il GLB normalizzato)
  const segnaposto = {};                                                  // chiave → il segnaposto già costruito
  const loader = new GLTFLoader();
  const qz = new THREE.Quaternion(), qx = new THREE.Quaternion(), qy = new THREE.Quaternion(), ASSE_Z = V(0, 0, 1), ASSE_X = V(1, 0, 0), ASSE_Y = V(0, 1, 0);

  function carica(k) {
    if (!cache.has(k)) cache.set(k, new Promise(res => loader.load(ARMI.cartella + k + '.glb', gltf => {
      const box = new THREE.Box3().setFromObject(gltf.scene), sz = box.getSize(new THREE.Vector3());
      const m = Math.max(sz.x, sz.y, sz.z) || 1, w = new THREE.Group();
      gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; } });
      w.add(gltf.scene); w.scale.setScalar(POSE[k].lungo / m);
      console.log('Arma in mano caricata:', ARMI.cartella + k + '.glb', '· lato lungo', m.toFixed(2), '→', POSE[k].lungo, 'm');
      res(w);
    }, undefined, () => res(null))));                                      // niente file: resta il segnaposto
    return cache.get(k);
  }
  function mostra(k) {
    chiave = k;
    while (arma.children.length) arma.remove(arma.children[0]);
    if (!POSE[k]) return;                                                  // pugni: niente in mano
    arma.add(segnaposto[k] || (segnaposto[k] = SEGNAPOSTO[k]()));          // costruiti una volta sola: niente geometrie nuove a ogni cambio arma
    carica(k).then(w => { if (w && chiave === k) { while (arma.children.length) arma.remove(arma.children[0]); arma.add(w); } });
  }
  // lega il punto-mano all'osso: nello spazio dell'osso l'orientamento è quello del modello a riposo (boneInverse · bindMatrix),
  // quindi gli assi dell'arma sono quelli nativi (x lato, y su, z avanti) qualunque sia come è ruotato lo scheletro
  function aggancia(a) {
    let sk = null; a.model.traverse(o => { if (o.isSkinnedMesh && !sk) sk = o; });
    const i = sk ? sk.skeleton.bones.findIndex(b => b.name === ARMI.osso) : -1;
    if (i < 0) { if (!avvisato) console.warn('Armi in mano: osso', ARMI.osso, 'non trovato'); avvisato = true; return; }
    radice.matrix.copy(sk.skeleton.boneInverses[i]).multiply(sk.bindMatrix).multiply(new THREE.Matrix4().makeTranslation(...ARMI.mano));
    radice.matrixWorldNeedsUpdate = true;
    sk.skeleton.bones[i].add(radice);
    aggancio = true; attore = a;
  }
  // un fotogramma: quale arma, e dov'è nel fendente
  function aggiorna(a, k) {
    if (!a || !a.model) return;
    if (!aggancio || attore !== a) aggancia(a);
    if (!aggancio) return;
    if (k !== chiave) mostra(k);
    const p = POSE[k];
    arma.visible = !!p;
    if (!p) return;
    const c = a.swingC || 0, dir = a.swingDir || 0;
    // alza a riposo + si china sul colpo; il fendente apre l'arma verso il lato (dir>0 = destra = −x nello spazio del modello)
    qx.setFromAxisAngle(ASSE_X, p.alza + p.avanti * Math.max(0, c) * (dir === 0 ? 1.6 : 1));
    qz.setFromAxisAngle(ASSE_Z, p.fuori + p.giro * c * dir);
    qy.setFromAxisAngle(ASSE_Y, p.vira || 0);                     // prima di tutto: gira l'arma su se stessa
    arma.quaternion.copy(qz).multiply(qx).multiply(qy);
  }
  return { aggiorna, radice, arma, ARMI, POSE, get chiave() { return chiave; }, get agganciata() { return aggancio; } };
}
