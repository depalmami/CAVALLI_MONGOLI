// PAESAGGIO — quello che c'è attorno alla strada oltre agli alberi (vedi 3d/alberi.js).
//
//   fiumi        · acqua che riflette il cielo e si increspa coi bassi, nelle tappe dei fiumi
//                  (il letto lo scava il terreno: vedi fiumeAl() e il passo 5b nella pagina)
//   nuvole       · ciuffi in alto che seguono la camera, quante dipende dalla tappa
//   montagne     · due anelli di creste all'orizzonte, nel colore della foschia
//   pali         · pali di legno con la sciarpa blu (khadag) al posto dei paletti da circuito;
//                  le luci a tempo ora accendono la sciarpa
//   accampamenti · gher bianche con porta rossa e lanterna, che di notte si accendono
//   erba         · fili d'erba vicino al cavallo, a blocchi che lo seguono, mossi dal vento a raffiche
//
// Tutto a coordinate di pista (segmento, laterale), come il resto del mondo.

import * as THREE from 'three';

function rng(seme) { let s = (seme * 2654435761) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
const col = hex => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };

// costruttore di triangoli con normali, colori e un attributo scalare in più
function costruttore() {
  const P = [], N = [], C = [], X = [];
  return {
    v(p, n, c, x = 0) { P.push(...p); const l = Math.hypot(...n) || 1; N.push(n[0] / l, n[1] / l, n[2] / l); C.push(...c); X.push(x); },
    // aggiunge una geometria three.js (non indicizzata) con un colore e un valore x
    geo(g, c, x = 0, colFn) {
      g = g.index ? g.toNonIndexed() : g;
      const p = g.attributes.position.array, n = g.attributes.normal.array;
      for (let i = 0; i < p.length; i += 3) {
        P.push(p[i], p[i + 1], p[i + 2]); N.push(n[i], n[i + 1], n[i + 2]);
        C.push(...(colFn ? colFn(p[i], p[i + 1], p[i + 2]) : c)); X.push(x);
      }
    },
    geometria(nomeX = 'aX') {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
      g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
      g.setAttribute(nomeX, new THREE.Float32BufferAttribute(X, 1));
      g.computeBoundingSphere();
      return g;
    },
  };
}

export function creaPaesaggio({ scene, U, posToWorld, groundAt, roadDist, tappaDi, tappaInizio, N, SEGMENT_LENGTH, ROAD_WIDTH,
                                pesiSuolo, fiumeAl, punti }) {
  U.uLuci = U.uLuci || { value: 0 };          // luci della notte (lanterne, porte delle gher)
  const uni = sh => { for (const k in U) sh.uniforms[k] = U[k]; };
  const P = new THREE.Vector3(), M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), V = new THREE.Vector3();
  const su = new THREE.Vector3(0, 1, 0);

  // ════════ FIUMI: l'acqua sul letto già scavato nel terreno ════════
  const fiumi = (() => {
    const pos = [];
    let prima = null;
    for (let s = 0; s < N - 2; s += 2) {
      const f = fiumeAl(s);
      if (!f || f.mezza < 60) { prima = null; continue; }
      const a = punti[s], rx = -Math.cos(a.heading), rz = Math.sin(a.heading);
      const cx = a.x + rx * f.lato * f.lat * ROAD_WIDTH, cz = a.z + rz * f.lato * f.lat * ROAD_WIDTH;
      const L = [cx - rx * f.mezza, f.y, cz - rz * f.mezza], R = [cx + rx * f.mezza, f.y, cz + rz * f.mezza];
      if (prima) pos.push(...prima.L, ...prima.R, ...R, ...prima.L, ...R, ...L);
      prima = { L, R };
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: '#24495a', roughness: 0.05, metalness: 0.1, side: THREE.DoubleSide,
                                                 transparent: true, opacity: 0.93, envMapIntensity: 1.1 });
    mat.userData.iblDosato = true;            // l'acqua il cielo lo deve riflettere tutto
    mat.customProgramCacheKey = () => 'paesaggio-acqua';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vPosA;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPosA = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vPosA;\nuniform float uTempo, uVento;')
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          {
            // increspature: somme di onde che scorrono; i bassi (dentro uVento) le gonfiano
            vec2 q = vPosA.xz; float t = uTempo, k = 0.07 + 0.12 * max(0.0, uVento - 1.0);
            vec2 g = vec2(cos(q.x * 0.004 + t * 1.3) + 0.6 * cos((q.x + q.y) * 0.009 - t * 1.9),
                          sin(q.y * 0.005 + t * 1.1) + 0.6 * sin((q.x - q.y) * 0.011 + t * 2.3)) * k;
            normal = normalize((viewMatrix * vec4(normalize(vec3(g.x, 1.0, g.y)), 0.0)).xyz);
          }`);
    };
    const m = new THREE.Mesh(g, mat);
    m.receiveShadow = true;
    scene.add(m);
    return m;
  })();

  // ════════ NUVOLE: ciuffi in alto, attorno alla camera ════════
  const COPERTURA = [0.45, 0.55, 0.85, 0.2, 0.4, 0.05, 0.5, 0.65, 0.55, 0.45, 0.3, 0.2];   // per tappa
  const nuvole = (() => {
    const VAR = 3, PER = 22, geos = [];
    for (let v = 0; v < VAR; v++) {
      const r = rng(31 + v * 7), b = costruttore();
      const n = 6 + (r() * 5 | 0);
      for (let i = 0; i < n; i++) {
        const g = new THREE.IcosahedronGeometry(1, 1);
        const rr = 4500 + r() * 5000;
        g.scale(rr, rr * 0.5, rr); g.translate((r() - 0.5) * 18000, r() * 1800, (r() - 0.5) * 9000);
        b.geo(g, null, 0, (x, y) => { const t = Math.min(1, Math.max(0, (y + 600) / 2400)); return [0.80 + 0.20 * t, 0.82 + 0.18 * t, 0.86 + 0.14 * t]; });
      }
      geos.push(b.geometria());
    }
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true, fog: false, emissive: '#6a7080' });
    const r = rng(99), istanze = [], meshes = geos.map(g => {
      const m = new THREE.InstancedMesh(g, mat, PER); m.frustumCulled = false; scene.add(m); return m;
    });
    for (let v = 0; v < VAR; v++) for (let i = 0; i < PER; i++)
      istanze.push({ m: meshes[v], i, x: r() * 600000, z: r() * 600000, y: 38000 + r() * 22000, s: 0.7 + r() * 1.1, yaw: r() * 6.28, soglia: r() });
    let vento = 0;
    return { aggiorna(cam, dt, copertura) {
      vento += dt * 900;
      for (const it of istanze) {
        const vis = it.soglia < copertura;
        const wrap = (a, c) => ((a - c) % 600000 + 900000) % 600000 - 300000;
        V.set(cam.x + wrap(it.x + vento, cam.x), cam.y + it.y, cam.z + wrap(it.z + vento * 0.35, cam.z));
        Q.setFromAxisAngle(su, it.yaw); S.setScalar(vis ? it.s : 0);
        it.m.setMatrixAt(it.i, M.compose(V, Q, S));
      }
      for (const m of meshes) m.instanceMatrix.needsUpdate = true;
    } };
  })();

  // ════════ MONTAGNE: due anelli di creste nel colore della foschia ════════
  const montagne = (() => {
    const anelli = [];
    for (const [R, alt, seme, mix] of [[300000, 34000, 5, 0.25], [230000, 22000, 11, 0.45]]) {
      const r = rng(seme), n = 360, pos = [];
      const quota = a => {                         // creste: somma di "denti" a scale diverse
        let h = 0;
        for (const [f, w] of [[3, 0.5], [7, 0.3], [17, 0.15], [41, 0.07]]) h += w * Math.abs(Math.sin(a * f + seme * 1.7 + Math.sin(a * f * 0.37) * 1.3));
        return alt * (0.25 + h);
      };
      for (let i = 0; i < n; i++) {
        const a0 = i / n * Math.PI * 2, a1 = (i + 1) / n * Math.PI * 2;
        const p0 = [Math.sin(a0) * R, 0, Math.cos(a0) * R], p1 = [Math.sin(a1) * R, 0, Math.cos(a1) * R];
        const t0 = [p0[0], quota(a0), p0[2]], t1 = [p1[0], quota(a1), p1[2]];
        const b0 = [p0[0], -30000, p0[2]], b1 = [p1[0], -30000, p1[2]];
        pos.push(...b0, ...t1, ...t0, ...b0, ...b1, ...t1);
      }
      r();
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0x556070, fog: false, side: THREE.DoubleSide }));
      m.frustumCulled = false; m.renderOrder = -1; scene.add(m);
      anelli.push({ m, mix });
    }
    const scuro = new THREE.Color('#3b4660');
    return { aggiorna(cam, nebbia) {
      for (const a of anelli) { a.m.position.set(cam.x, cam.y - 14000, cam.z); a.m.material.color.copy(nebbia).lerp(scuro, a.mix); }
    } };
  })();

  // ════════ PALI con la sciarpa blu (khadag) ════════
  const pali = (() => {
    const b = costruttore();
    const palo = new THREE.CylinderGeometry(38, 52, 980, 6); palo.translate(0, 490, 0);
    b.geo(palo, col('#6b4a2e'), 0);
    const cima = new THREE.ConeGeometry(60, 90, 6); cima.translate(0, 1025, 0);
    b.geo(cima, col('#4a3220'), 0);
    // sciarpa: una striscia che parte dal palo e ricade al vento; aX = 0 al nodo → 1 in punta
    const blu = col('#3d8bff'), bluScuro = col('#1f5fcf'), K = 7;
    for (let k = 0; k < K; k++) {
      const q = [k / K, (k + 1) / K].map(t => ({ t, x: 45 + t * 240, y: 840 - t * t * 160, w: 70 - t * 25 }));
      const [a, c] = q;
      const A1 = [a.x, a.y, 0], A2 = [a.x, a.y - a.w, 8], C1 = [c.x, c.y, 0], C2 = [c.x, c.y - c.w, 8];
      const n = [0, 0, 1], ca = a.t > 0.5 ? bluScuro : blu;
      b.v(A1, n, ca, a.t); b.v(A2, n, ca, a.t); b.v(C1, n, ca, c.t);
      b.v(C1, n, ca, c.t); b.v(A2, n, ca, a.t); b.v(C2, n, ca, c.t);
    }
    const g = b.geometria('aSciarpa');
    const slots = [];
    for (let i = 6; i < N - 4; i += 4) for (const lato of [-1, 1]) slots.push({ i, lato });
    g.setAttribute('aIdx', new THREE.InstancedBufferAttribute(new Float32Array(slots.map(p => p.i / 4)), 1));
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'paesaggio-pali';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
          attribute float aIdx, aSciarpa;
          uniform float uLed, uLedFlash, uCorsa, uTempo, uVento;
          varying float vLed;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          {
            // la sciarpa sventola: più verso la punta, più si muove
            float s = aSciarpa;
            transformed.z += sin(uTempo * 6.0 + aIdx * 1.7 + s * 4.0) * s * 55.0 * uVento;
            transformed.y += sin(uTempo * 4.3 + aIdx * 2.3 + s * 3.0) * s * 35.0;
            float k = mod(aIdx + uCorsa, 8.0);   // uno su otto acceso, la fila corre verso il cavallo
            vLed = step(0.001, s) * (uLed * (0.12 + (1.0 - smoothstep(0.0, 1.6, k))) + uLedFlash);
          }`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vLed;\nuniform vec3 uColLed;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += uColLed * vLed;');
    };
    const m = new THREE.InstancedMesh(g, mat, slots.length);
    const look = {};
    slots.forEach((p, k) => {
      posToWorld(p.i * SEGMENT_LENGTH, p.lato * 1.18, P, look);
      Q.setFromAxisAngle(su, look.heading + Math.PI / 2);          // la sciarpa ricade all'indietro
      m.setMatrixAt(k, M.compose(V.set(P.x, P.y - 20, P.z), Q, S.setScalar(0.9 + ((p.i * 7919) % 100) / 500)));
    });
    m.castShadow = m.receiveShadow = true;
    scene.add(m);
    return m;
  })();

  // ════════ ACCAMPAMENTI: gher con porta rossa e lanterna ════════
  const vicini = [];          // accampamenti in coordinate di pista, per tenere lontani alberi ed erba
  const accampamenti = (() => {
    const b = costruttore();
    const feltro = col('#ece4d2'), fascia = col('#b9aa8c'), tetto = col('#f3eee2'), legno = col('#6b4a2b');
    const parete = new THREE.CylinderGeometry(2400, 2400, 1500, 20, 1, true); parete.translate(0, 750, 0);
    b.geo(parete, null, 0, (x, y) => y < 260 ? fascia : feltro);
    const t = new THREE.CylinderGeometry(380, 2480, 850, 20, 1, true); t.translate(0, 1925, 0);
    b.geo(t, tetto, 0);
    const corona = new THREE.CylinderGeometry(380, 380, 140, 12); corona.translate(0, 2420, 0);
    b.geo(corona, legno, 0.45);                                    // il foro del fumo di notte si illumina appena
    const porta = new THREE.BoxGeometry(950, 1250, 120); porta.translate(0, 625, 2390);
    b.geo(porta, col('#c0392b'), 0.35);
    const lanterna = new THREE.BoxGeometry(260, 340, 260); lanterna.translate(720, 1180, 2520);
    b.geo(lanterna, col('#ffd27a'), 1.0);
    const g = b.geometria('aLuce');
    // dove: tappe di steppa e le città (passo in segmenti fra un accampamento e l'altro)
    const PASSO = { 0: 900, 1: 1500, 3: 650, 4: 900, 6: 1200, 9: 900, 10: 420, 11: 200 };
    const r = rng(2026), gher = [];
    for (const [kk, passo] of Object.entries(PASSO)) {
      const k = +kk, i0 = Math.floor(tappaInizio[k] / SEGMENT_LENGTH) + 150, i1 = Math.floor(tappaInizio[k + 1] / SEGMENT_LENGTH) - 150;
      for (let i = i0; i < i1; i += passo * (0.6 + r() * 0.8)) {
        const seg = Math.floor(i), lato = r() < 0.5 ? -1 : 1, lat = lato * (5.6 + r() * 2.5);
        const f = fiumeAl(seg);
        if (f && f.lato === lato) continue;                        // non sul lato del fiume
        const n = k >= 10 ? 4 + (r() * 5 | 0) : 2 + (r() * 3 | 0);
        let messe = 0;
        for (let q = 0; q < n * 3 && messe < n; q++) {
          const sDelta = (r() - 0.5) * 50, lDelta = (r() - 0.5) * 3.2 * Math.abs(lato);
          posToWorld((seg + sDelta) * SEGMENT_LENGTH, lat + lDelta * lato, P);
          if (roadDist(P.x, P.z) < 4500) continue;
          if (gher.some(o => Math.hypot(o.x - P.x, o.z - P.z) < 6200)) continue;
          // la porta guarda la strada
          const look = {}; const C = posToWorld((seg + sDelta) * SEGMENT_LENGTH, 0, new THREE.Vector3(), look);
          gher.push({ x: P.x, y: groundAt(P.x, P.z) - 60, z: P.z, yaw: Math.atan2(C.x - P.x, C.z - P.z), s: 0.85 + r() * 0.3 });
          messe++;
        }
        if (messe) vicini.push({ seg, lat, raggio: 4.2 });
      }
    }
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 });
    mat.customProgramCacheKey = () => 'paesaggio-gher';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aLuce;\nvarying float vLuce;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLuce = aLuce;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vLuce;\nuniform float uLuci;')
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          totalEmissiveRadiance += vec3(1.0, 0.72, 0.4) * vLuce * (0.15 + 9.0 * uLuci);`);
    };
    const m = new THREE.InstancedMesh(g, mat, Math.max(1, gher.length));
    m.count = gher.length;
    gher.forEach((o, k) => m.setMatrixAt(k, M.compose(V.set(o.x, o.y, o.z), Q.setFromAxisAngle(su, o.yaw), S.setScalar(o.s))));
    m.computeBoundingSphere();
    m.castShadow = m.receiveShadow = true;
    scene.add(m);
    return { m, n: gher.length };
  })();

  // libero(seg, lat): niente alberi né erba nel fiume o dentro un accampamento
  function libero(seg, lat) {
    const f = fiumeAl(Math.round(seg));
    if (f && Math.sign(lat) === f.lato && Math.abs(Math.abs(lat) - f.lat) * ROAD_WIDTH < f.mezza + 1400) return false;
    for (const c of vicini) if (Math.abs(c.seg - seg) < 60 && Math.abs(c.lat - lat) < c.raggio) return false;
    return true;
  }

  // ════════ ERBA: fili a blocchi di pista attorno al cavallo ════════
  const erba = (() => {
    const BLOCCO = 40, POOL = 7, MAX = 7000;
    // un filo: tre tratti che si assottigliano, alto 1 e largo 1 (la misura la dà l'istanza)
    const pos = [], colori = [], base = col('#2f3d17'), punta = col('#ffffff');
    const seg = [[0, 1], [0.38, 0.8], [0.72, 0.5], [1, 0]];
    for (let k = 0; k < 3; k++) {
      const [ya, wa] = seg[k], [yb, wb] = seg[k + 1];
      const A1 = [-wa / 2, ya, 0], A2 = [wa / 2, ya, 0], B1 = [-wb / 2, yb, 0], B2 = [wb / 2, yb, 0];
      const ca = base.map((c, i) => c + (punta[i] - c) * ya), cb = base.map((c, i) => c + (punta[i] - c) * yb);
      pos.push(...A1, ...A2, ...B2, ...A1, ...B2, ...B1); colori.push(...ca, ...ca, ...cb, ...ca, ...cb, ...cb);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(colori, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(new Float32Array(pos.length).map((_, i) => i % 3 === 1 ? 1 : 0), 3));
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'paesaggio-erba';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uTempo, uVento;\nuniform vec3 uGiocatore;')
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          #ifdef USE_INSTANCING
          {
            vec3 ip = instanceMatrix[3].xyz;
            // raffiche che attraversano il prato; i bassi (in uVento) le rinforzano
            float raffica = sin(dot(ip.xz, vec2(0.0007, 0.0005)) - uTempo * 1.8) * 0.5 + 0.5;
            float h = transformed.y * transformed.y;
            transformed.z += (0.35 + raffica * 1.3) * uVento * h * 160.0;   // z non è scalato: unità mondo
            transformed.x += sin(uTempo * 2.7 + ip.x * 0.01) * h * 0.4;      // x è scalato dalla larghezza
            // lontano dal cavallo l'erba si abbassa fino a sparire: niente bordo netto
            transformed *= 1.0 - smoothstep(20000.0, 30000.0, distance(ip.xz, uGiocatore.xz));
          }
          #endif`);
    };
    const verde = new THREE.Color('#6f9a36'), paglia = new THREE.Color('#b59a52'), c = new THREE.Color(), ps = [0, 0, 0, 0];
    const pool = Array.from({ length: POOL }, () => {
      const m = new THREE.InstancedMesh(g, mat, MAX); m.count = 0; m.blocco = -1; m.receiveShadow = true;
      scene.add(m); return m;
    });
    function genera(m, b) {
      const r = rng(b * 7 + 3); let n = 0;
      for (let s = b * BLOCCO; s < (b + 1) * BLOCCO && s < N - 2; s += 0.25) {
        pesiSuolo(Math.floor(s), ps);
        const dens = ps[0] + ps[1] * 0.85 + ps[3] * 0.2;           // sulla sabbia niente erba
        const verdeQ = ps[0] / Math.max(0.01, ps[0] + ps[1]);
        for (let q = 0; q < 8 && n < MAX; q++) {
          if (r() > dens) continue;
          const lato = r() < 0.5 ? -1 : 1, lat = lato * (1.32 + Math.pow(r(), 1.4) * 6.5);
          if (!libero(s, lat)) continue;
          posToWorld((s + r() * 0.25) * SEGMENT_LENGTH, lat, P);
          const a = Math.abs(lat);
          // sulla banchina a quota strada, sulla scarpata a scendere, poi il terreno
          const y = a <= 2.4 ? P.y : Math.max(groundAt(P.x, P.z), P.y - 300 - (a - 2.4) / 1.6 * 1200);
          const alt = 260 + r() * 420;
          M.compose(V.set(P.x, y - 10, P.z), Q.setFromAxisAngle(su, r() * 6.28), S.set(55 + r() * 35, alt, 1));
          m.setMatrixAt(n, M);
          c.copy(paglia).lerp(verde, verdeQ).multiplyScalar(0.75 + r() * 0.5);
          m.setColorAt(n, c);
          n++;
        }
      }
      m.count = n; m.blocco = b;
      m.computeBoundingSphere();               // fuori vista il blocco non si disegna
      m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true;
    }
    return { aggiorna(pos) {
      const b0 = Math.floor(pos / SEGMENT_LENGTH / BLOCCO);
      const servono = [];
      for (let b = b0 - 1; b <= b0 + 4; b++) if (b >= 0) servono.push(b);
      const mancano = servono.filter(b => !pool.some(m => m.blocco === b));
      if (!mancano.length) return;
      const libera = pool.find(m => !servono.includes(m.blocco));
      if (libera) genera(libera, mancano[0]);                       // uno per frame: niente scatti
    } };
  })();

  let tPrec = performance.now();
  return {
    libero, fiumi, accampamenti, pali,
    aggiorna({ camera, posRender, giorno, nebbia }) {
      const t = performance.now(), dt = Math.min(0.1, (t - tPrec) / 1000); tPrec = t;
      const k = Math.min(COPERTURA.length - 1, tappaDi(posRender));
      nuvole.aggiorna(camera.position, dt, COPERTURA[k]);
      montagne.aggiorna(camera.position, nebbia);
      erba.aggiorna(posRender);
      U.uLuci.value = 1 - giorno;
    },
  };
}
