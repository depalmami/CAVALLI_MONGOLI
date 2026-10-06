// ALBERI — specie della Mongolia generate via codice (niente modelli da scaricare).
//
//   larice siberiano · l'albero delle foreste di Burkhan Khaldun e del Khangai:
//                      palchi di rami che ricadono, verde o dorato d'autunno
//   betulla          · corteccia bianca segnata di nero, chioma tonda e chiara
//   pino silvestre   · fusto alto che in cima diventa arancio, chioma a ombrello
//   cespuglio        · steppa e dune (il saxaul del Gobi, in piccolo)
//
// Ogni specie ha più varianti (semi diversi), così non ci sono cloni. Le chiome
// hanno normali che escono dal centro del ciuffo: si illuminano morbide come
// nuvole, non a faccette. I colori stanno nei vertici (scuro dentro e in basso,
// chiaro sulle punte); il colore per istanza li varia appena.
//
// La FORESTA si dispone per tappa (un bioma per tappa: rada nella steppa, fitta
// sulla montagna sacra, quasi assente nelle dune) e si divide in BLOCCHI lungo
// la pista: ogni blocco è una InstancedMesh con la sua sfera di ingombro, quindi
// si disegnano solo quelli in vista. Prima si disegnavano sempre tutti i 12 mila.

import * as THREE from 'three';

function rng(seme) { let s = (seme * 2654435761) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
const col = hex => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };   // sRGB → lineare
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];

// ── costruttore di triangoli con normali e colori per vertice ──
function costruttore() {
  const P = [], Nn = [], C = [];
  return {
    v(p, n, c) { P.push(p[0], p[1], p[2]); const l = Math.hypot(n[0], n[1], n[2]) || 1; Nn.push(n[0] / l, n[1] / l, n[2] / l); C.push(c[0], c[1], c[2]); },
    geometria() {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(Nn, 3));
      g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
      g.computeBoundingSphere();
      return g;
    },
  };
}

// fusto conico, leggermente piegato; colore per anello (per le macchie della betulla)
function fusto(b, { h, r0, r1, lati = 7, anelli = 5, piega = 0, colAnello }) {
  const pt = (k, j) => {
    const t = k / anelli, a = j / lati * Math.PI * 2, r = r0 + (r1 - r0) * t;
    const px = piega * t * t;
    return [Math.cos(a) * r + px, h * t, Math.sin(a) * r];
  };
  for (let k = 0; k < anelli; k++) {
    const c0 = colAnello(k / anelli), c1 = colAnello((k + 1) / anelli);
    for (let j = 0; j < lati; j++) {
      const a0 = j / lati * Math.PI * 2, a1 = (j + 1) / lati * Math.PI * 2;
      const n0 = [Math.cos(a0), 0.15, Math.sin(a0)], n1 = [Math.cos(a1), 0.15, Math.sin(a1)];
      const A = pt(k, j), B = pt(k, j + 1), Cc = pt(k + 1, j + 1), D = pt(k + 1, j);
      b.v(A, n0, c0); b.v(Cc, n1, c1); b.v(B, n1, c0);
      b.v(A, n0, c0); b.v(D, n0, c1); b.v(Cc, n1, c1);
    }
  }
}

// ciuffo: icosaedro deformato, normali dal centro (luce morbida), più scuro sotto
const ICO = (() => { const g = new THREE.IcosahedronGeometry(1, 1); return g.attributes.position.array; })();
function ciuffo(b, rand, { c, r, sy = 0.8, jit = 0.22, chiaro, scuro }) {
  const seme = rand() * 100;
  for (let i = 0; i < ICO.length; i += 3) {
    const x = ICO[i], y = ICO[i + 1], z = ICO[i + 2];
    // deformazione deterministica sul vertice dell'icosaedro (stessi vertici → niente crepe)
    const d = 1 + jit * Math.sin(x * 5.1 + seme) * Math.cos(y * 4.3 - seme * 0.7) * Math.sin(z * 3.7 + seme * 1.3);
    const p = [c[0] + x * r * d, c[1] + y * r * sy * d, c[2] + z * r * d];
    const n = [x, y * 0.8 + 0.25, z];
    const t = Math.max(0, Math.min(1, 0.5 + y * 0.55));
    b.v(p, n, mix(scuro, chiaro, t));
  }
}

// ── le specie ──
function larice(seme, oro = false) {
  const rand = rng(seme), b = costruttore();
  const H = 5200 + rand() * 1800;
  const corteccia = col('#4a3426'), cortecciaScura = col('#2c1f17');
  fusto(b, { h: H * 0.94, r0: 150, r1: 28, piega: (rand() - 0.5) * 160, colAnello: t => mix(cortecciaScura, corteccia, t) });
  // d'autunno il larice (unica conifera che perde gli aghi) diventa d'oro: colori nei vertici,
  // non una tinta sopra il verde — verde per giallo fa oliva, non oro
  const ago = col(oro ? '#e0a92e' : '#7fa648'), agoScuro = col(oro ? '#7a4f12' : '#2f4a1f'), punta = col(oro ? '#ffe08a' : '#b9d273');
  const palchi = 10 + (rand() * 4 | 0);
  for (let k = 0; k < palchi; k++) {
    const t = k / (palchi - 1);
    const y = H * (0.16 + 0.8 * t);
    const R = 1650 * Math.pow(1 - t, 0.85) * (0.85 + rand() * 0.3) + 170;
    const K = 9 + (rand() * 3 | 0);
    const alto = [0, y + 280 + 160 * (1 - t), 0], basso = [0, y - 200, 0];
    const anello = [];
    for (let j = 0; j < K; j++) {
      const a = (j + rand() * 0.6) / K * Math.PI * 2;
      const rr = R * (0.7 + rand() * 0.55);
      anello.push([Math.cos(a) * rr, y - rr * 0.22 + (rand() - 0.5) * 140, Math.sin(a) * rr]);
    }
    const cSu = mix(ago, punta, 0.25 + 0.5 * t), cFuori = mix(agoScuro, ago, 0.55 + 0.45 * t), cSotto = agoScuro;
    for (let j = 0; j < K; j++) {
      const A = anello[j], B = anello[(j + 1) % K];
      const nA = [A[0], R * 0.45, A[2]], nB = [B[0], R * 0.45, B[2]];
      b.v(alto, [0, 1, 0], cSu); b.v(B, nB, cFuori); b.v(A, nA, cFuori);           // sopra
      b.v(basso, [0, -1, 0], cSotto); b.v(A, [A[0], -R * 0.3, A[2]], cSotto); b.v(B, [B[0], -R * 0.3, B[2]], cSotto);   // sotto
    }
  }
  return b.geometria();
}

function betulla(seme) {
  const rand = rng(seme), b = costruttore();
  const H = 3800 + rand() * 1600;
  const bianco = col('#e9e4d6'), nero = col('#2b2a28');
  // anelli bianchi con qualche fascia scura: le "lenticelle" della betulla
  const macchie = Array.from({ length: 12 }, () => rand() < 0.35);
  fusto(b, { h: H * 0.78, r0: 115, r1: 45, lati: 6, anelli: 12, piega: (rand() - 0.5) * 380,
             colAnello: t => (t < 0.08 ? mix(nero, bianco, 0.4) : macchie[Math.min(11, t * 12 | 0)] ? mix(bianco, nero, 0.75) : bianco) });
  const foglia = col('#a8c84f'), fogliaScura = col('#476b25');
  const n = 6 + (rand() * 3 | 0);
  for (let i = 0; i < n; i++) {
    const a = rand() * Math.PI * 2, d = rand() * 650;
    const y = H * (0.6 + rand() * 0.33);
    ciuffo(b, rand, { c: [Math.cos(a) * d, y, Math.sin(a) * d], r: 520 + rand() * 380, sy: 0.85, chiaro: foglia, scuro: fogliaScura });
  }
  return b.geometria();
}

function pino(seme) {
  const rand = rng(seme), b = costruttore();
  const H = 5600 + rand() * 2000;
  const sotto = col('#4b3324'), sopra = col('#c06a35');           // il pino silvestre in cima è arancio
  fusto(b, { h: H * 0.8, r0: 165, r1: 55, lati: 7, anelli: 6, piega: (rand() - 0.5) * 300, colAnello: t => mix(sotto, sopra, t * t) });
  const ago = col('#4f7a3a'), agoScuro = col('#1f3a22');
  const n = 5 + (rand() * 3 | 0);
  for (let i = 0; i < n; i++) {
    const a = rand() * Math.PI * 2, d = 250 + rand() * 750;
    const y = H * (0.66 + rand() * 0.3);
    ciuffo(b, rand, { c: [Math.cos(a) * d, y, Math.sin(a) * d], r: 620 + rand() * 420, sy: 0.5, jit: 0.3, chiaro: ago, scuro: agoScuro });
  }
  return b.geometria();
}

function cespuglio(seme) {
  const rand = rng(seme), b = costruttore();
  const foglia = col('#8a9a4a'), scura = col('#3d4a22');
  const n = 3 + (rand() * 3 | 0);
  for (let i = 0; i < n; i++) {
    const a = rand() * Math.PI * 2, d = rand() * 380;
    ciuffo(b, rand, { c: [Math.cos(a) * d, 220 + rand() * 180, Math.sin(a) * d], r: 260 + rand() * 220, sy: 0.7, chiaro: foglia, scuro: scura });
  }
  return b.geometria();
}

const lariceOro = seme => larice(seme, true);
export const SPECIE = { larice, lariceOro, betulla, pino, cespuglio };
// "abete" esiste solo come impostore (foto): la geometria procedurale è un pino, mai usata
SPECIE.abete = pino;
const VARIANTI = 3;

// ── un bioma per tappa: quanti alberi, quali, fin dove ──
// dens = densità media · gruppi = quanto si raccolgono a boschetti (0 uniforme, 1 a macchie)
// prof = fin dove arriva la foresta (in larghezze di strada dal centro) · autunno = larici dorati
const BIOMI = [
  { nome: 'Fiume Kherlen',             dens: 0.22, gruppi: 0.8, prof: 8,  mix: { betulla: 0.6, cespuglio: 0.4 } },
  { nome: "Guado dell'Onon",           dens: 0.45, gruppi: 0.6, prof: 10, mix: { betulla: 0.5, larice: 0.3, pino: 0.1, cespuglio: 0.1 } },
  { nome: 'Burkhan Khaldun',           dens: 0.9,  gruppi: 0.2, prof: 14, mix: { abete: 0.45, pino: 0.25, larice: 0.22, betulla: 0.08 } },
  { nome: 'Piana del Tuul',            dens: 0.07, gruppi: 0.9, prof: 7,  mix: { cespuglio: 0.7, betulla: 0.3 } },
  { nome: 'Colline di Khustai',        dens: 0.2,  gruppi: 0.8, prof: 9,  mix: { betulla: 0.5, cespuglio: 0.5 } },
  { nome: 'Dune di Elsen Tasarkhai',   dens: 0.06, gruppi: 0.5, prof: 8,  mix: { cespuglio: 1 } },
  { nome: "Valle dell'Orkhon",         dens: 0.4,  gruppi: 0.6, prof: 11, mix: { larice: 0.4, betulla: 0.45, cespuglio: 0.15 } },
  { nome: 'Cascate di Ulaan Tsutgalan', dens: 0.6, gruppi: 0.4, prof: 12, mix: { pino: 0.35, abete: 0.3, larice: 0.25, cespuglio: 0.1 } },
  { nome: 'Monti Khangai',             dens: 0.85, gruppi: 0.25, prof: 14, mix: { larice: 0.45, abete: 0.3, pino: 0.25 }, autunno: 0.75 },
  { nome: 'Rovine di Khar Balgas',     dens: 0.1,  gruppi: 0.8, prof: 8,  mix: { cespuglio: 0.6, betulla: 0.4 } },
  { nome: 'Erdene Zuu',                dens: 0.25, gruppi: 0.5, prof: 9,  mix: { betulla: 0.7, pino: 0.3 } },
  { nome: 'Karakorum',                 dens: 0.15, gruppi: 0.7, prof: 8,  mix: { betulla: 0.5, cespuglio: 0.5 } },
];

// rumore 1D lungo la pista: dove nascono i boschetti
function boschi(i) {
  const x = i / 140;
  return 0.5 + 0.3 * Math.sin(x * 1.3 + Math.sin(x * 0.37) * 2.1) + 0.2 * Math.sin(x * 3.7 + 1.7);
}

// ── IMPOSTORI: abeti e pini fotorealistici ──
// Poly Haven li dà a milioni di poligoni (aghi veri): ridotti diventano scheletri. Allora
// li ho FOTOGRAFATI in Blender da 8 lati (assets/alberi/CREDITI.md) e qui ogni albero è
// un rettangolo che si gira verso la camera e mostra la foto del lato giusto.
// ortho = altezza (m) inquadrata dalla foto, base = metri fra il fondo della foto e il piede.
const M_UNITA = 800;                       // 1 m = 800 unità di gioco (il cavallo, 1300, è 1,6 m)
export const IMPOSTORI = {
  abete: [{ url: 'assets/alberi/abete_a.webp', ortho: 19.68, base: 0.379 }, { url: 'assets/alberi/abete_b.webp', ortho: 16.8, base: 1.371 },
          { url: 'assets/alberi/abete_c.webp', ortho: 17.49, base: 1.484 }],
  pino:  [{ url: 'assets/alberi/pino_a.webp', ortho: 23.06, base: 1.342 }, { url: 'assets/alberi/pino_b.webp', ortho: 21.07, base: 3.094 },
          { url: 'assets/alberi/pino_c.webp', ortho: 21.79, base: 2.121 }],
  // larici: le foto degli abeti ricolorate (tools/larici-da-abete.py) — verde tenero e oro d'autunno
  larice:    [{ url: 'assets/alberi/larice_a.webp', ortho: 19.68, base: 0.379 }, { url: 'assets/alberi/larice_b.webp', ortho: 16.8, base: 1.371 },
              { url: 'assets/alberi/larice_c.webp', ortho: 17.49, base: 1.484 }],
  lariceOro: [{ url: 'assets/alberi/larice_oro_a.webp', ortho: 19.68, base: 0.379 }, { url: 'assets/alberi/larice_oro_b.webp', ortho: 16.8, base: 1.371 },
              { url: 'assets/alberi/larice_oro_c.webp', ortho: 17.49, base: 1.484 }],
};
const SCHIARISCI = { pino: 2.0, abete: 1.35, larice: 1.25, lariceOro: 1.2 };
const VISTE = 8, ASPETTO = 384 / 1024;
function materialeImpostore(tex, mondo, luce, schiarisci) {
  const m = new THREE.ShaderMaterial({
    uniforms: { ...mondo.U, uTex: { value: tex }, uLuceAlberi: luce, uSchiarisci: { value: schiarisci },
                ...THREE.UniformsLib.fog },
    fog: true, alphaToCoverage: true, side: THREE.DoubleSide,
    vertexShader: `
      #include <common>
      #include <fog_pars_vertex>
      attribute float aYaw, aAlt, aBase, aBanda;
      uniform sampler2D uSpettro;
      uniform float uPulseXZ, uPulseY, uForesta, uTempo, uVento;
      varying vec2 vUv;
      void main() {
        vec3 ip = instanceMatrix[3].xyz;
        vec2 d = normalize(cameraPosition.xz - ip.xz);
        // quale foto: l'angolo da cui la camera guarda l'albero, tolta la sua rotazione
        float fi = atan(d.x, d.y) - aYaw;
        float k = mod(floor(fi / 6.2831853 * ${VISTE}.0 + 0.5), ${VISTE}.0);
        vUv = vec2((k + uv.x) / ${VISTE}.0, uv.y);
        float v = texture2D(uSpettro, vec2((aBanda * 63.0 + 0.5) / 64.0, 0.5)).r;
        float alt = aAlt * uPulseY * (1.0 + uForesta * v * 1.2), larg = aAlt * ${ASPETTO} * uPulseXZ;
        vec3 destra = vec3(d.y, 0.0, -d.x);
        vec3 p = ip + destra * position.x * larg;
        p.y = ip.y - aBase * (alt / aAlt) + position.y * alt;      // il piede della foto va a terra
        p += destra * sin(uTempo * 1.3 + aBanda * 40.0) * uv.y * uv.y * 140.0 * uVento;   // vento in cima
        vec4 mvPosition = viewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        #include <fog_vertex>
      }`,
    fragmentShader: `
      #include <common>
      #include <fog_pars_fragment>
      uniform sampler2D uTex;
      uniform vec3 uLuceAlberi;
      uniform float uSchiarisci;
      varying vec2 vUv;
      void main() {
        vec4 c = texture2D(uTex, vUv);
        if (c.a < 0.35) discard;
        gl_FragColor = vec4(c.rgb * uLuceAlberi * uSchiarisci, c.a);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        #include <fog_fragment>
      }`,
  });
  return m;
}

export function creaForesta({ scene, N, SEGMENT_LENGTH, ROAD_WIDTH, posToWorld, roadDist, groundAt, tappaDi, distanzaMinima, mondo, blocco = 1000, libero = () => true }) {
  const rand = rng(12345);                    // seme fisso: la foresta è sempre la stessa
  const geo = {};
  for (const s in SPECIE) geo[s] = Array.from({ length: VARIANTI }, (_, v) => SPECIE[s](101 + v * 977 + s.length * 31));
  const luceAlberi = { value: new THREE.Vector3(1, 1, 1) };   // la tinge la pagina con la luce della tappa

  // ── disposizione ──
  const P = new THREE.Vector3(), istanze = [];
  let scartati = 0;
  for (let i = 8; i < N - 4; i += 3) {
    const bi = BIOMI[Math.min(BIOMI.length - 1, tappaDi(i * SEGMENT_LENGTH))];
    const macchia = boschi(i);
    const dens = Math.min(1, bi.dens * (1 - bi.gruppi + bi.gruppi * 2.2 * Math.max(0, macchia - 0.35)));
    for (const lato of [-1, 1]) {
      // file di alberi verso l'esterno: tante quante ne regge la densità
      const file = Math.max(1, Math.round(dens * (bi.prof - 4)));
      for (let f = 0; f < file; f++) {
        if (rand() > dens) continue;
        const lat = lato * (4.3 + f * ((bi.prof - 4.3) / Math.max(1, file)) + rand() * 1.1);
        if (Math.abs(lat) > bi.prof) continue;
        if (!libero(i, lat)) continue;                 // niente alberi nei fiumi e negli accampamenti
        posToWorld((i + (rand() - 0.5) * 2.5) * SEGMENT_LENGTH, lat, P);
        const dist = roadDist(P.x, P.z);
        if (dist < distanzaMinima) { scartati++; continue; }
        // specie dal mix del bioma
        let r = rand(), specie = 'cespuglio';
        for (const [s, w] of Object.entries(bi.mix)) { if ((r -= w) <= 0) { specie = s; break; } }
        if (specie === 'larice' && bi.autunno && rand() < bi.autunno) specie = 'lariceOro';
        istanze.push({ i, specie, variante: (rand() * VARIANTI) | 0, x: P.x, y: groundAt(P.x, P.z), z: P.z,
                       s: specie === 'cespuglio' ? 0.7 + rand() * 0.8 : 0.75 + rand() * 0.55, yaw: rand() * Math.PI * 2,
                       luce: 0.82 + rand() * 0.3, banda: rand(), dist });
      }
    }
  }

  // ── materiale unico per tutte le specie (colori nei vertici) + ombra che segue vento e musica ──
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, metalness: 0 });
  mondo.patchAlbero(mat, 'foresta');
  const ombra = mondo.profonditaAlbero();

  // ── blocchi lungo la pista: una InstancedMesh per (blocco, specie, variante) ──
  // impostori: un'InstancedMesh per foto (abete/pino × 3), rettangoli che guardano la camera
  const caricatore = new THREE.TextureLoader(), quad = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0);
  const iM = new THREE.Matrix4(), iQ = new THREE.Quaternion(), iS = new THREE.Vector3(1, 1, 1), iV = new THREE.Vector3();
  const impostori = [];
  for (const [specie, varianti] of Object.entries(IMPOSTORI)) varianti.forEach((v, vi) => {
    const lista = istanze.filter(x => x.specie === specie && x.variante === vi);
    if (!lista.length) return;
    const tex = caricatore.load(v.url);
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    const g = new THREE.InstancedBufferGeometry().copy(quad);
    const alt = lista.map(x => v.ortho * M_UNITA * x.s * 0.62);           // un po' più piccoli del vero: il mondo è stilizzato
    g.setAttribute('aYaw', new THREE.InstancedBufferAttribute(new Float32Array(lista.map(x => x.yaw)), 1));
    g.setAttribute('aAlt', new THREE.InstancedBufferAttribute(new Float32Array(alt), 1));
    g.setAttribute('aBase', new THREE.InstancedBufferAttribute(new Float32Array(lista.map((x, n) => v.base / v.ortho * alt[n])), 1));
    g.setAttribute('aBanda', new THREE.InstancedBufferAttribute(new Float32Array(lista.map(x => x.banda)), 1));
    const m = new THREE.InstancedMesh(g, materialeImpostore(tex, mondo, luceAlberi, SCHIARISCI[specie]), lista.length);
    lista.forEach((it, n) => m.setMatrixAt(n, iM.compose(iV.set(it.x, it.y, it.z), iQ, iS)));
    m.frustumCulled = false;
    scene.add(m); impostori.push(m);
  });
  const gruppi = new Map();
  for (const it of istanze) {
    if (IMPOSTORI[it.specie]) continue;      // gli impostori sono già sistemati
    const k = `${Math.floor(it.i / blocco)}|${it.specie}|${it.variante}`;
    if (!gruppi.has(k)) gruppi.set(k, []);
    gruppi.get(k).push(it);
  }
  const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), V = new THREE.Vector3(), su = new THREE.Vector3(0, 1, 0);
  const tinta = new THREE.Color(), meshes = [];
  for (const [k, lista] of gruppi) {
    const [, specie, variante] = k.split('|');
    const base = geo[specie][+variante];
    // geometria per blocco che CONDIVIDE i buffer della specie, con i suoi attributi per istanza
    const g = new THREE.BufferGeometry();
    for (const a of ['position', 'normal', 'color']) g.setAttribute(a, base.attributes[a]);
    g.boundingSphere = base.boundingSphere;
    g.setAttribute('aBanda', new THREE.InstancedBufferAttribute(new Float32Array(lista.map(x => x.banda)), 1));
    g.setAttribute('aDistT', new THREE.InstancedBufferAttribute(new Float32Array(lista.map(x => x.dist)), 1));
    const m = new THREE.InstancedMesh(g, mat, lista.length);
    lista.forEach((it, n) => {
      Q.setFromAxisAngle(su, it.yaw); S.set(it.s, it.s, it.s); V.set(it.x, it.y - 30, it.z);
      m.setMatrixAt(n, M.compose(V, Q, S));
      tinta.setRGB(it.luce, it.luce, it.luce * 0.95);
      m.setColorAt(n, tinta);
    });
    m.computeBoundingSphere();               // sfera dell'intero blocco: fuori vista, non si disegna
    m.castShadow = specie !== 'cespuglio'; m.receiveShadow = true;
    m.customDepthMaterial = ombra;
    scene.add(m); meshes.push(m);
  }
  const conteggio = Object.fromEntries(Object.keys(SPECIE).map(s => [s, istanze.filter(x => x.specie === s).length]));
  console.info(`foresta: ${istanze.length} alberi in ${meshes.length} blocchi`, conteggio, `· scartati vicino alla strada: ${scartati}`);

  return {
    // il rimbalzo del party ora è un uniform (nello shader), come l'equalizzatore
    pulse(sxz, sy) { mondo.U.uPulseXZ.value = sxz; mondo.U.uPulseY.value = sy; },
    data: istanze, meshes, impostori, conteggio, BIOMI,
    // colore della luce sugli alberi fotografati (la foto ha una luce neutra; qui si tinge)
    tingi(r, g, b) { luceAlberi.value.set(r, g, b); },
  };
}
