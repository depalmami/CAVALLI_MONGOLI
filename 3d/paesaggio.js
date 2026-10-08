// PAESAGGIO — quello che c'è attorno alla strada oltre agli alberi (vedi 3d/alberi.js).
//
//   fiumi        · acqua che riflette il cielo e si increspa coi bassi, nelle tappe dei fiumi
//                  (il letto lo scava il terreno: vedi fiumeAl() e il passo 5b nella pagina)
//   nuvole       · nuvole volumetriche fotografate in Cycles, che seguono la camera; quante dipende dalla tappa
//   pali         · pali di legno con la sciarpa blu (khadag) al posto dei paletti da circuito;
//                  le luci a tempo ora accendono la sciarpa
//   ovoo e massi · cumuli di pietre sacri con bandiere di preghiera; massi sparsi, fitti nelle tappe rocciose
//   accampamenti · gher bianche con porta rossa e lanterna, che di notte si accendono
//   erba         · ciuffi d'erba e fiori fotografati vicino al cavallo, a blocchi che lo seguono,
//                  mossi dal vento a raffiche
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
    // un nastro lungo il fiume: ogni vertice sa dove sta fra le rive (aAcross 0…1), in che direzione
    // corre l'acqua (aFlow, dal tracciato del centro) e quanto è turbolento (aTurb: i torrenti di montagna)
    const pos = [], acr = [], flo = [], tur = [];
    let corsa = [];
    const chiudi = () => {
      for (let i = 0; i + 1 < corsa.length; i++) {
        const a = corsa[i], c = corsa[i + 1];
        const v = (q, lato) => {
          pos.push(...(lato ? q.R : q.L)); acr.push(lato); flo.push(q.fx, q.fz); tur.push(q.tur);
        };
        v(a, 0); v(a, 1); v(c, 1); v(a, 0); v(c, 1); v(c, 0);
      }
      corsa = [];
    };
    for (let s = 0; s < N - 2; s += 2) {
      const f = fiumeAl(s);
      if (!f || f.mezza < 60) { chiudi(); continue; }
      const a = punti[s], rx = -Math.cos(a.heading), rz = Math.sin(a.heading);
      const cx = a.x + rx * f.lat * ROAD_WIDTH, cz = a.z + rz * f.lat * ROAD_WIDTH;
      const m = f.mezza * 1.3;               // il letto scavato arriva al pelo dell'acqua ~20-30% oltre la "mezza": il nastro arriva lì, senza sospendersi sulla riva
      const L = [cx - rx * m, f.y, cz - rz * m], R = [cx + rx * m, f.y, cz + rz * m];
      const k = tappaDi(s * SEGMENT_LENGTH);
      corsa.push({ L, R, cx, cz, fx: 0, fz: 1, tur: (k === 2 || k === 8) ? 1 : 0.15 });
    }
    chiudi();
    // direzione di scorrimento = tangente del centro (la strada va verso +s: l'acqua corre nello stesso verso)
    // ricalcolata dopo, perché chiudi() ha già spezzato le corse: rifaccio il passaggio sui vertici
    {
      const n = pos.length / 3;
      for (let i = 0; i < n; i += 6) {
        // vertici del quad: 0=L(a),1=R(a),2=R(c),3=L(a),4=R(c),5=L(c) → centro a e centro c
        const ca = [(pos[i * 3] + pos[(i + 1) * 3]) / 2, (pos[i * 3 + 2] + pos[(i + 1) * 3 + 2]) / 2];
        const cc = [(pos[(i + 4) * 3] + pos[(i + 5) * 3]) / 2, (pos[(i + 4) * 3 + 2] + pos[(i + 5) * 3 + 2]) / 2];
        const dx = cc[0] - ca[0], dz = cc[1] - ca[1], l = Math.hypot(dx, dz) || 1;
        for (let q = 0; q < 6; q++) { flo[(i + q) * 2] = dx / l; flo[(i + q) * 2 + 1] = dz / l; }
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('aAcross', new THREE.Float32BufferAttribute(acr, 1));
    g.setAttribute('aFlow', new THREE.Float32BufferAttribute(flo, 2));
    g.setAttribute('aTurb', new THREE.Float32BufferAttribute(tur, 1));
    g.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: '#24495a', roughness: 0.04, metalness: 0.0, side: THREE.DoubleSide,
                                                 transparent: true, depthWrite: false, envMapIntensity: 0.6 });
    mat.userData.iblDosato = true;            // l'acqua il cielo lo deve riflettere tutto
    mat.customProgramCacheKey = () => 'paesaggio-acqua2';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nattribute float aAcross, aTurb;\nattribute vec2 aFlow;\nvarying vec3 vPosA;\nvarying float vAcc, vTurb;\nvarying vec2 vFlow;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPosA = (modelMatrix * vec4(transformed, 1.0)).xyz; vAcc = aAcross; vTurb = aTurb; vFlow = aFlow;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vPosA; varying float vAcc, vTurb; varying vec2 vFlow;
          uniform float uTempo, uVento;
          float hW(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
          float nW(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
            return mix(mix(hW(i), hW(i + vec2(1.0, 0.0)), f.x), mix(hW(i + vec2(0.0, 1.0)), hW(i + vec2(1.0, 1.0)), f.x), f.y); }
          float fW(vec2 p) { float v = 0.0, a = 0.5; for (int k = 0; k < 3; k++) { v += a * nW(p); p *= 2.03; a *= 0.5; } return v; }
          float gFoam, gProf;
          vec2 qW() { vec2 f = normalize(vFlow); return vec2(dot(vPosA.xz, f), dot(vPosA.xz, vec2(-f.y, f.x))); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            vec2 q = qW(); float t = uTempo;
            float e = min(vAcc, 1.0 - vAcc);                              // 0 alla riva → 0.5 al centro
            gProf = smoothstep(0.0, 0.42, e);                             // 0 acqua bassa → 1 profonda
            // schiuma: orlo di riva (frastagliato), e nei torrenti anche sulle rapide
            float orlo = 1.0 - smoothstep(0.015, 0.09, e + (nW(q * vec2(0.006, 0.02) + vec2(-t * 0.8, 0.0)) - 0.5) * 0.14);
            float rapide = vTurb * smoothstep(0.62, 0.82, fW(q * vec2(0.004, 0.013) + vec2(-t * 1.8, 0.0)));
            gFoam = clamp(orlo * (0.25 + 0.55 * vTurb) + rapide * 0.8, 0.0, 1.0);
            // colore: il fondo sabbioso si vede dove è basso, poi verde-azzurro, poi scuro
            vec3 fondo = vec3(0.26, 0.27, 0.19), medio = vec3(0.045, 0.20, 0.23), prof = vec3(0.01, 0.065, 0.10);
            vec3 acqua = mix(mix(fondo, medio, smoothstep(0.0, 0.5, gProf)), prof, smoothstep(0.5, 1.0, gProf));
            diffuseColor.rgb = mix(acqua, vec3(0.90, 0.95, 0.97), gFoam);
            diffuseColor.a = mix(mix(0.42, 0.93, smoothstep(0.0, 0.6, gProf)), 1.0, gFoam) * smoothstep(0.0, 0.06, e);
          }`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(0.03, 0.85, gFoam);')
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          {
            // increspature che scorrono lungo il fiume, più veloci al centro; i bassi (uVento) le gonfiano
            vec2 q = qW(); float t = uTempo;
            float v = 1.0 + 0.6 * (1.0 - abs(2.0 * vAcc - 1.0));
            float k = 0.30 + 0.30 * vTurb + 0.14 * max(0.0, uVento - 1.0);
            vec2 p1 = q * vec2(0.0045, 0.013) + vec2(-t * 1.3 * v, 0.0);
            vec2 p2 = q * vec2(0.012, 0.03) + vec2(-t * 2.4 * v, t * 0.15);
            float d = 0.35;
            float h0 = nW(p1) * 0.7 + nW(p2) * 0.3;
            float hA = nW(p1 + vec2(d, 0.0)) * 0.7 + nW(p2 + vec2(d, 0.0)) * 0.3;
            float hB = nW(p1 + vec2(0.0, d)) * 0.7 + nW(p2 + vec2(0.0, d)) * 0.3;
            float sa = (hA - h0) / d * k * (1.0 - 0.6 * gFoam), sc = (hB - h0) / d * k * (1.0 - 0.6 * gFoam);
            vec2 f = normalize(vFlow), pp = vec2(-f.y, f.x);
            vec3 nw = normalize(vec3(-(f.x * sa + pp.x * sc), 1.0, -(f.y * sa + pp.y * sc)));
            normal = normalize((viewMatrix * vec4(nw, 0.0)).xyz);
          }`);
    };
    const m = new THREE.Mesh(g, mat);
    m.receiveShadow = true; m.renderOrder = 1;
    scene.add(m);
    return m;
  })();

  // ════════ PONTI DI PIETRA: dove l'acqua passa davvero sotto la strada ════════
  // Piano di lastre un filo più alto della pista, parapetti a blocchi con la copertina chiara,
  // spalle che scendono fino all'acqua. La pietra è disegnata nello shader (blocchi sfalsati e
  // malta, dalla posizione nel mondo: niente UV da preparare).
  const sulPonte = new Set();
  const ponti = (() => {
    for (let sg = 0; sg < N - 2; sg++) { const f = fiumeAl(sg); if (f && Math.abs(f.lat) < f.mezza / ROAD_WIDTH + 1.4) sulPonte.add(sg); }
    const segs = [...sulPonte].sort((a, b) => a - b);
    const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.92 });
    mat.customProgramCacheKey = () => 'paesaggio-pietra';
    mat.onBeforeCompile = sh => {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vPosP; varying vec3 vNorP;')
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          #ifdef USE_INSTANCING
          vPosP = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).xyz;
          vNorP = normalize(mat3(modelMatrix * instanceMatrix) * objectNormal);
          #endif`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vPosP; varying vec3 vNorP;
          float hashP(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            // piani orizzontali: lastre dal piano xz; pareti: blocchi da (x+z, y)
            vec2 q = abs(vNorP.y) > 0.5 ? vPosP.xz : vec2(vPosP.x + vPosP.z, vPosP.y);
            float alt = abs(vNorP.y) > 0.5 ? 520.0 : 230.0, lun = 480.0;
            float riga = floor(q.y / alt), x = q.x + mod(riga, 2.0) * lun * 0.5;
            vec2 cella = vec2(floor(x / lun), riga), f = vec2(fract(x / lun), fract(q.y / alt));
            float malta = max(1.0 - smoothstep(0.0, 0.05, min(f.x, 1.0 - f.x)), 1.0 - smoothstep(0.0, 0.09, min(f.y, 1.0 - f.y)));
            float h = hashP(cella);
            vec3 pietra = mix(vec3(0.50, 0.47, 0.42), vec3(0.74, 0.70, 0.62), h) * (0.88 + 0.24 * hashP(cella + 7.0));
            diffuseColor.rgb = mix(pietra, vec3(0.28, 0.26, 0.23), malta * 0.85);
          }`);
    };
    const pezzi = {
      piano:    new THREE.BoxGeometry(ROAD_WIDTH * 2.6, 90, SEGMENT_LENGTH + 4),    // lastre: 45 sopra la pista (copre carreggiata e ghiaia)
      soletta:  new THREE.BoxGeometry(ROAD_WIDTH * 2.8, 520, SEGMENT_LENGTH + 4),   // lo spessore sotto
      parapetto:new THREE.BoxGeometry(300, 560, SEGMENT_LENGTH + 4),
      copertina:new THREE.BoxGeometry(400, 90, SEGMENT_LENGTH + 4),
      spalla:   new THREE.BoxGeometry(ROAD_WIDTH * 3, 2600, 900),
    };
    const mesh = {};
    for (const k in pezzi) { mesh[k] = new THREE.InstancedMesh(pezzi[k], mat, Math.max(2, segs.length * 2 + 4)); mesh[k].count = 0; }
    const metti = (k, x, y, z, q) => { const m = mesh[k]; m.setMatrixAt(m.count++, M.compose(V.set(x, y, z), q, S.set(1, 1, 1))); };
    const look = {};
    segs.forEach(sg => {
      posToWorld((sg + 0.5) * SEGMENT_LENGTH, 0, P, look);
      const q = new THREE.Quaternion().setFromAxisAngle(su, look.heading);
      metti('piano', P.x, P.y + 1, P.z, q);
      metti('soletta', P.x, P.y - 300, P.z, q);
      for (const lato of [-1, 1]) {
        posToWorld((sg + 0.5) * SEGMENT_LENGTH, lato * 1.4, P);
        metti('parapetto', P.x, P.y + 280, P.z, q);
        metti('copertina', P.x, P.y + 600, P.z, q);
      }
      // spalle alle due teste di ogni ponte, giù fino all'acqua
      for (const testa of [sg - 1, sg + 1]) if (!sulPonte.has(testa)) {
        posToWorld((sg + 0.5 + (testa - sg) * 0.5) * SEGMENT_LENGTH, 0, P);
        metti('spalla', P.x, P.y - 1350, P.z, q);
      }
    });
    for (const k in mesh) { const m = mesh[k]; m.computeBoundingSphere(); m.castShadow = m.receiveShadow = true; scene.add(m); }
    return { n: segs.length };
  })();

  // ════════ NUVOLE: ciuffi in alto, attorno alla camera ════════
  const COPERTURA = [0.45, 0.55, 0.85, 0.2, 0.4, 0.05, 0.5, 0.65, 0.55, 0.45, 0.3, 0.2];   // per tappa
  // nuvole vere: 6 nuvole volumetriche renderizzate in Cycles (tools/nuvole-blender.py) in
  // un atlante 3×2; ognuna è un rettangolo che guarda la camera, tinto dalla luce della tappa
  // e sfumato nel colore della foschia verso l'orizzonte
  const uNuvole = { uTex: { value: null }, uSole: { value: new THREE.Vector3(1, 1, 1) },
                    uOmbra: { value: new THREE.Vector3(0.6, 0.65, 0.75) }, uFoschia: { value: new THREE.Color() } };
  const nuvole = (() => {
    const TANTE = 66, tex = new THREE.TextureLoader().load('assets/alberi/nuvole.webp');
    tex.colorSpace = THREE.SRGBColorSpace; uNuvole.uTex.value = tex;
    const g = new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(1, 1));
    const r = rng(99), istanze = [];
    for (let i = 0; i < TANTE; i++)
      istanze.push({ x: r() * 600000, z: r() * 600000, y: 38000 + r() * 22000, s: 0.7 + r() * 1.1, soglia: r(),
                     foto: (r() * 6) | 0, specchio: r() < 0.5 ? -1 : 1 });
    g.setAttribute('aFoto', new THREE.InstancedBufferAttribute(new Float32Array(istanze.map(it => it.foto + (it.specchio < 0 ? 8 : 0))), 1));
    const mat = new THREE.ShaderMaterial({
      uniforms: uNuvole, transparent: true, depthWrite: false, fog: false,
      vertexShader: `
        attribute float aFoto;
        varying vec2 vUv; varying float vLontano;
        void main() {
          vec3 c = instanceMatrix[3].xyz;
          float s = length(instanceMatrix[0].xyz);
          float specchio = aFoto >= 8.0 ? -1.0 : 1.0, f = mod(aFoto, 8.0);
          vec2 u = vec2(specchio > 0.0 ? uv.x : 1.0 - uv.x, uv.y);
          vUv = vec2((mod(f, 3.0) + u.x) / 3.0, (1.0 - floor(f / 3.0)) * 0.5 + u.y * 0.5);
          vec4 mv = viewMatrix * vec4(c, 1.0);
          mv.xy += position.xy * vec2(1.6, 1.0) * s;               // il fotogramma è 640×400
          vLontano = smoothstep(120000.0, 290000.0, length(c.xz - cameraPosition.xz));
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        uniform sampler2D uTex; uniform vec3 uSole, uOmbra, uFoschia;
        varying vec2 vUv; varying float vLontano;
        void main() {
          vec4 t = texture2D(uTex, vUv);
          if (t.a < 0.01) discard;
          // la foto è bianca dove batte il sole e grigia in ombra: la riaccendo coi colori del cielo
          float l = dot(t.rgb, vec3(0.3, 0.55, 0.15));
          vec3 c = mix(uOmbra, uSole, smoothstep(0.25, 0.95, l)) * (0.55 + 0.6 * l);
          c = mix(c, uFoschia, vLontano * 0.85);
          gl_FragColor = vec4(c, t.a * (1.0 - vLontano * 0.6));
          #include <colorspace_fragment>
        }`,
    });
    const m = new THREE.InstancedMesh(g, mat, TANTE); m.frustumCulled = false; m.renderOrder = -1; scene.add(m);
    let vento = 0;
    return { mesh: m, aggiorna(cam, dt, copertura) {
      vento += dt * 900;
      const wrap = (a, c) => ((a - c) % 600000 + 900000) % 600000 - 300000;
      istanze.forEach((it, i) => {
        V.set(cam.x + wrap(it.x + vento, cam.x), cam.y + it.y, cam.z + wrap(it.z + vento * 0.35, cam.z));
        S.setScalar(it.soglia < copertura ? it.s * 55000 : 0);
        m.setMatrixAt(i, M.compose(V, Q.identity(), S));
      });
      m.instanceMatrix.needsUpdate = true;
    } };
  })();

  // ════════ PALI con la sciarpa blu (khadag) ════════
  // il palo è un tronco lavorato a mano: più grosso alla base, appena curvo, schiarito dal sole in
  // cima e scuro e umido a terra; la sciarpa è legata con una corda di canapa e ha le frange.
  // aSciarpa: −1 = legno/corda (lo shader gli disegna le venature), 0…1 = sciarpa dal nodo alla punta
  const pali = (() => {
    const b = costruttore();
    const legno = col('#7a5636'), umido = col('#3b2a1a'), sole = col('#a98c68'), canapa = col('#d9c9a0');
    const palo = new THREE.CylinderGeometry(36, 56, 1000, 8, 4); palo.translate(0, 500, 0);
    b.geo(palo, null, -1, (x, y, z) => {
      const t = Math.min(1, Math.max(0, y / 1000));
      const c = t < 0.22 ? umido.map((u, i) => u + (legno[i] - u) * (t / 0.22)) : legno.map((l, i) => l + (sole[i] - l) * Math.pow((t - 0.22) / 0.78, 1.6));
      return c;
    });
    // il fusto non è dritto: una curva dolce (applicata ai vertici già inseriti)
    // la cima: taglio obliquo schiarito, come un palo segato
    const cima = new THREE.ConeGeometry(62, 80, 8, 1, true); cima.translate(0, 1040, 0);
    b.geo(cima, sole.map(c => c * 0.85), -1);
    // corda di canapa: tre giri attorno al palo dove si lega la sciarpa
    for (let k = 0; k < 3; k++) {                                  // anelli bassi di 8 facce: con 26 mila pali ogni vertice conta
      const giro = new THREE.CylinderGeometry(46, 46, 16, 8, 1, true); giro.translate(0, 820 + k * 26, 0);
      b.geo(giro, canapa, -1);
    }
    // sciarpa di seta: lunga, ondulata, con un taglio a coda di rondine in punta e tre frange
    const blu = col('#3d8bff'), bluScuro = col('#1f5fcf'), bluChiaro = col('#7db3ff'), K = 12, LUNGA = 360;
    for (let k = 0; k < K; k++) {
      const q = [k / K, (k + 1) / K].map(t => ({ t, x: 50 + t * LUNGA, y: 830 - t * t * 220, w: 92 - t * 38 }));
      const [a, c] = q;
      const coda = c.t > 0.93;                                  // gli ultimi tratti si dividono in due punte
      const A1 = [a.x, a.y, 0], A2 = [a.x, a.y - a.w, 10], C1 = [c.x, c.y, 0], C2 = [c.x, c.y - c.w * (coda ? 1.5 : 1), 10];
      const n = [0, 0, 1], ca = a.t > 0.55 ? bluScuro : blu;
      b.v(A1, n, ca, a.t); b.v(A2, n, ca, a.t); b.v(C1, n, bluChiaro.map((x, i) => x * 0.5 + ca[i] * 0.5), c.t);
      b.v(C1, n, ca, c.t); b.v(A2, n, ca, a.t); b.v(C2, n, ca, c.t);
    }
    for (let f = 0; f < 3; f++) {                                // frange: fili sottili alla punta
      const x0 = 50 + LUNGA, y0 = 830 - 220 - 40 + f * 22;
      const F1 = [x0, y0, 0], F2 = [x0 + 6, y0, 0], F3 = [x0 + 3 + f * 10, y0 - 70, 8];
      b.v(F1, [0, 0, 1], bluChiaro, 1); b.v(F2, [0, 0, 1], bluChiaro, 1); b.v(F3, [0, 0, 1], bluChiaro, 1);
    }
    const base = b.geometria('aSciarpa');
    const slots = [];
    for (let i = 6; i < N - 4; i += 4) if (!sulPonte.has(i)) for (const lato of [-1, 1]) slots.push({ i, lato });   // sui ponti c'è il parapetto
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'paesaggio-pali';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
          attribute float aIdx, aSciarpa;
          uniform float uLed, uLedFlash, uCorsa, uTempo, uVento, uCassa;
          varying float vLed, vS, vIdx;
          varying vec3 vPL;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          {
            vPL = position; vS = aSciarpa; vIdx = aIdx;
            // il palo è appena curvo: la cima si sposta di lato
            float h = clamp(position.y / 1000.0, 0.0, 1.2);
            transformed.x += sin(aIdx * 1.3) * h * h * 26.0;
            // la sciarpa sventola: più verso la punta, più si muove, con un'onda che la percorre
            float s = max(aSciarpa, 0.0);
            transformed.z += (sin(uTempo * 6.0 + aIdx * 1.7 - s * 9.0) * 0.6 + sin(uTempo * 3.1 + aIdx - s * 5.0) * 0.4) * s * 70.0 * (0.4 + uVento) * (1.0 + 1.5 * uCassa);
            transformed.y += sin(uTempo * 4.3 + aIdx * 2.3 - s * 7.0) * s * 45.0 * (1.0 + 1.5 * uCassa);
            float k = mod(aIdx + uCorsa, 8.0);   // uno su otto acceso, la fila corre verso il cavallo
            vLed = step(0.001, s) * step(-0.5, aSciarpa) * (uLed * (0.12 + (1.0 - smoothstep(0.0, 1.6, k))) + uLedFlash);
          }`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying float vLed, vS, vIdx;
          varying vec3 vPL;
          uniform vec3 uColLed;
          uniform float uTempo;
          float hP(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
          float nP(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
            return mix(mix(hP(i), hP(i + vec2(1, 0)), f.x), mix(hP(i + vec2(0, 1)), hP(i + vec2(1, 1)), f.x), f.y); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          if (vS < -0.5) {
            // legno: venature lungo il palo (rumore stirato in verticale), spaccature e nodi
            float ang = vPL.x * 0.045 + vPL.z * 0.037;
            float ven = nP(vec2(ang * 3.0, vPL.y * 0.004 + vIdx)) * 0.6 + nP(vec2(ang * 9.0, vPL.y * 0.012)) * 0.4;
            float crepa = smoothstep(0.78, 0.9, nP(vec2(ang * 5.0 + 3.0, vPL.y * 0.0022 + vIdx * 2.0)));
            float nodo = smoothstep(0.88, 0.95, nP(vec2(ang * 1.5 + vIdx, vPL.y * 0.01)));
            diffuseColor.rgb *= (0.72 + 0.5 * ven) * (1.0 - 0.45 * crepa) * (1.0 - 0.35 * nodo);
          } else {
            // seta: pieghe che corrono lungo la sciarpa, più chiare sulle creste
            float piega = sin(vS * 17.0 - uTempo * 4.0 + vIdx * 2.0) * 0.5 + 0.5;
            diffuseColor.rgb *= 0.72 + 0.5 * piega;
          }`)
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += uColLed * vLed;');
    };
    // a blocchi lungo la pista: quelli fuori dall'inquadratura non si disegnano (26 mila pali tutti insieme pesavano 100 fps)
    const gruppo = new THREE.Group(), BLOCCO = 300, look = {}, tilt = new THREE.Quaternion(), eu = new THREE.Euler();
    const perBlocco = new Map();
    for (const sl of slots) { const k = Math.floor(sl.i / BLOCCO); if (!perBlocco.has(k)) perBlocco.set(k, []); perBlocco.get(k).push(sl); }
    for (const lista of perBlocco.values()) {
      const g = new THREE.BufferGeometry();
      for (const a of ['position', 'normal', 'color', 'aSciarpa']) g.setAttribute(a, base.attributes[a]);
      g.boundingSphere = base.boundingSphere;
      g.setAttribute('aIdx', new THREE.InstancedBufferAttribute(new Float32Array(lista.map(p => p.i / 4)), 1));
      const m = new THREE.InstancedMesh(g, mat, lista.length);
      lista.forEach((p, k) => {
        posToWorld(p.i * SEGMENT_LENGTH, p.lato * 1.18, P, look);
        Q.setFromAxisAngle(su, look.heading + Math.PI / 2);          // la sciarpa ricade all'indietro
        const h = ((p.i * 7919) % 100) / 100, h2 = ((p.i * 104729) % 100) / 100;
        Q.multiply(tilt.setFromEuler(eu.set((h - 0.5) * 0.07, 0, (h2 - 0.5) * 0.07)));   // ogni palo un po' storto
        m.setMatrixAt(k, M.compose(V.set(P.x, P.y - 20, P.z), Q, S.setScalar(0.86 + h2 * 0.28)));
      });
      m.computeBoundingSphere();
      m.castShadow = m.receiveShadow = true;
      gruppo.add(m);
    }
    scene.add(gruppo);
    return gruppo;
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
        if (f && (f.lato === lato || Math.abs(f.lat) < 7)) continue;   // non sul lato del fiume, né dove attraversa
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
    return { m, n: gher.length, lista: gher };
  })();

  // libero(seg, lat): niente alberi né erba nel fiume o dentro un accampamento
  function libero(seg, lat) {
    const f = fiumeAl(Math.round(seg));
    if (f && Math.abs(lat - f.lat) * ROAD_WIDTH < f.mezza + 1400) return false;
    for (const c of vicini) if (Math.abs(c.seg - seg) < (c.ds ?? 60) && Math.abs(c.lat - lat) < c.raggio) return false;
    return true;
  }

  // ════════ PIETRE: ovoo (i cumuli sacri) e massi sparsi ════════
  // Un ovoo è un cumulo di pietre con in cima un fascio di bastoni, sciarpe blu e fili di bandiere di
  // preghiera nei cinque colori (blu, bianco, rosso, verde, giallo); si trova sui passi e sulle alture.
  // Qui le pietre sono blocchi sbozzati dal rumore, con licheni e venature nello shader.
  function roccia(seme, dettaglio = 1) {
    const g = new THREE.IcosahedronGeometry(1, dettaglio), p = g.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i).normalize();
      const d = 1 + 0.22 * Math.sin(v.x * 3.1 + seme) * Math.sin(v.y * 2.7 + seme * 1.3) * Math.sin(v.z * 3.3 + seme * 0.7)
                  + 0.12 * Math.sin(v.x * 7.3 + seme * 2.1 + v.z * 5.0) + 0.08 * Math.sin(v.y * 9.1 + seme);
      p.setXYZ(i, v.x * d, v.y * d * 0.72, v.z * d);                    // un po' schiacciate: le pietre poggiano
    }
    g.computeVertexNormals();                                           // non indicizzata: facce piatte, da pietra sbozzata
    return g;
  }
  function pietraShader(mat, chiave, vento) {
    mat.customProgramCacheKey = () => chiave;
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
          varying vec3 vPosS;
          ${vento ? 'attribute float aX;\nuniform float uTempo, uVento, uCassa;' : ''}`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          ${vento ? `{
            // bandiere e sciarpe: aX = quanto sono libere di muoversi (0 = ferme, pietre e bastoni)
            float f = aX;
            float frusta = 1.0 + 1.8 * uCassa;                 // la cassa le frusta
            transformed.x += sin(uTempo * (6.0 + 5.0 * uCassa) + position.y * 0.012 + position.x * 0.005) * f * 70.0 * (0.4 + uVento) * frusta;
            transformed.z += sin(uTempo * (5.2 + 5.0 * uCassa) + position.x * 0.007 + position.y * 0.01) * f * 110.0 * (0.4 + uVento) * frusta;
            transformed.y += sin(uTempo * 8.0 + position.x * 0.01) * f * 25.0 * frusta;
          }` : ''}
          #ifdef USE_INSTANCING
          vPosS = (modelMatrix * instanceMatrix * vec4(position, 1.0)).xyz;
          #else
          vPosS = (modelMatrix * vec4(position, 1.0)).xyz;
          #endif`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vPosS;
          float hS(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
          float nS(vec3 p) { vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
            return mix(mix(mix(hS(i), hS(i + vec3(1,0,0)), f.x), mix(hS(i + vec3(0,1,0)), hS(i + vec3(1,1,0)), f.x), f.y),
                       mix(mix(hS(i + vec3(0,0,1)), hS(i + vec3(1,0,1)), f.x), mix(hS(i + vec3(0,1,1)), hS(i + vec3(1,1,1)), f.x), f.y), f.z); }`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            // solo dove il colore del vertice è grigio (pietra): le bandiere e le sciarpe restano pulite
            float grigio = 1.0 - clamp((max(diffuseColor.r, max(diffuseColor.g, diffuseColor.b)) - min(diffuseColor.r, min(diffuseColor.g, diffuseColor.b))) * 4.0, 0.0, 1.0);
            float n = nS(vPosS * 0.0035) * 0.6 + nS(vPosS * 0.014) * 0.3 + nS(vPosS * 0.06) * 0.1;
            float vena = smoothstep(0.43, 0.5, abs(nS(vPosS * vec3(0.002, 0.009, 0.002)) - 0.5) + 0.43);
            float lichene = smoothstep(0.62, 0.78, nS(vPosS * 0.0022 + 5.0));
            vec3 pietra = diffuseColor.rgb * (0.55 + 0.9 * n) * (1.0 - 0.3 * vena);
            pietra = mix(pietra, vec3(0.62, 0.60, 0.28) * (0.6 + 0.5 * n), lichene * 0.55);
            diffuseColor.rgb = mix(diffuseColor.rgb, pietra, grigio);
          }`);
    };
    mat.needsUpdate = true;
  }
  const ovoo = (() => {
    const rr = rng(808), b = costruttore();
    const grigi = ['#8a8780', '#77746d', '#9b978d', '#6a6862', '#a39e90'].map(col);
    const rocce = [roccia(1.7, 2), roccia(4.1, 2)];
    // il cumulo: pietre sempre più piccole verso l'alto
    const NP = 78, tutte = [];
    for (let k = 0; k < NP; k++) {
      const t = k / NP, a = rr() * 6.283, R = Math.pow(1 - t, 0.7) * 1550 * (0.45 + 0.55 * rr());
      const sz = (440 - 230 * t) * (0.7 + 0.6 * rr());
      tutte.push({ x: Math.cos(a) * R, z: Math.sin(a) * R, y: t * 1500 + sz * 0.3, sz, g: rocce[k % 2], c: grigi[(rr() * grigi.length) | 0], ry: rr() * 6.28 });
    }
    for (const r of tutte) {
      const g = r.g.clone(); g.scale(r.sz * (0.9 + 0.4 * rr()), r.sz, r.sz * (0.9 + 0.4 * rr())); g.rotateY(r.ry); g.translate(r.x, r.y, r.z);
      const v = 0.85 + 0.3 * rr();
      b.geo(g, null, 0, () => [r.c[0] * v, r.c[1] * v, r.c[2] * v]);
    }
    // bastoni: un fascio che si apre alla base
    const legno = col('#6b5133'), TOP = [0, 4700, 0];
    const bastoni = 7;
    for (let k = 0; k < bastoni; k++) {
      const a = k / bastoni * 6.283 + rr() * 0.4, sx = Math.cos(a) * 520, sz = Math.sin(a) * 520, sy = 1250;
      const dx = TOP[0] - sx + (rr() - 0.5) * 160, dy = TOP[1] - sy + rr() * 500, dz = TOP[2] - sz + (rr() - 0.5) * 160;
      const len = Math.hypot(dx, dy, dz), g = new THREE.CylinderGeometry(28, 48, len, 5); g.translate(0, len / 2, 0);
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(dx, dy, dz).normalize());
      g.applyQuaternion(q); g.translate(sx, sy, sz);
      b.geo(g, legno.map(c => c * (0.8 + 0.4 * rr())), 0);
    }
    // sciarpe blu legate in cima e a metà fascio
    const blu = col('#3d8bff'), bluScuro = col('#1f5fcf');
    for (let k = 0; k < 4; k++) {
      const a = k * 1.6 + 0.4, base = [Math.cos(a) * 90, 3900 - k * 380, Math.sin(a) * 90], K = 9, LUNGA = 650;
      for (let i = 0; i < K; i++) {
        const t0 = i / K, t1 = (i + 1) / K, w0 = 130 - t0 * 50, w1 = 130 - t1 * 50;
        const A1 = [base[0] + Math.cos(a) * 60, base[1] - t0 * LUNGA - 0, base[2] + Math.sin(a) * 60];
        const o = (t, w, up) => { const y = base[1] - t * LUNGA; return [base[0] + Math.cos(a) * (60 + t * 70) - Math.sin(a) * (up ? w / 2 : -w / 2), y, base[2] + Math.sin(a) * (60 + t * 70) + Math.cos(a) * (up ? w / 2 : -w / 2)]; };
        const n = [Math.cos(a), 0, Math.sin(a)], c = t0 > 0.5 ? bluScuro : blu;
        b.v(o(t0, w0, true), n, c, t0 + 0.02); b.v(o(t0, w0, false), n, c, t0 + 0.02); b.v(o(t1, w1, true), n, c, t1);
        b.v(o(t1, w1, true), n, c, t1); b.v(o(t0, w0, false), n, c, t0 + 0.02); b.v(o(t1, w1, false), n, c, t1);
      }
    }
    // fili di bandiere di preghiera: dalla cima del fascio a terra, in quattro direzioni
    const COL5 = ['#2a6fd6', '#f2f2ee', '#d0312d', '#2e9e4f', '#f2c230'].map(col);
    for (let k = 0; k < 4; k++) {
      const a = k * 1.571 + 0.5 + rr() * 0.3, fine = [Math.cos(a) * 3600, 520, Math.sin(a) * 3600], NB = 13;
      for (let i = 0; i < NB; i++) {
        const t0 = 0.06 + i / NB * 0.9, t1 = t0 + 0.9 / NB * 0.92;
        const pt = t => [TOP[0] + (fine[0] - TOP[0]) * t, TOP[1] + (fine[1] - TOP[1]) * t - Math.sin(t * Math.PI) * 360, TOP[2] + (fine[2] - TOP[2]) * t];
        const P0 = pt(t0), P1 = pt(t1), c = COL5[(i + k) % 5], alto = 330;
        const n = [-Math.sin(a), 0, Math.cos(a)];
        b.v(P0, n, c, 0.05); b.v(P1, n, c, 0.05); b.v([P0[0], P0[1] - alto, P0[2]], n, c, 1);
        b.v(P1, n, c, 0.05); b.v([P1[0], P1[1] - alto, P1[2]], n, c, 1); b.v([P0[0], P0[1] - alto, P0[2]], n, c, 1);
      }
    }
    const g = b.geometria('aX');
    // dove: qualche ovoo per tappa, a pochi metri dalla strada, mai nei fiumi
    const PER_TAPPA = [1, 2, 2, 1, 2, 1, 2, 2, 3, 2, 1, 1];
    const r = rng(4242), lista = [], scarti = { ponte: 0, libero: 0, fiume: 0, strada: 0 };
    for (let k = 0; k < PER_TAPPA.length; k++) {
      const i0 = Math.floor(tappaInizio[k] / SEGMENT_LENGTH) + 300, i1 = Math.floor(tappaInizio[k + 1] / SEGMENT_LENGTH) - 300;
      for (let q = 0, messi = 0; q < 60 && messi < PER_TAPPA[k]; q++) {
        const seg = Math.floor(i0 + r() * (i1 - i0)), lato = r() < 0.5 ? -1 : 1, lat = lato * (3.4 + r() * 1.6);
        if (sulPonte.has(seg)) { scarti.ponte++; continue; }
        if (!libero(seg, lat)) { scarti.libero++; continue; }
        const f = fiumeAl(seg); if (f && Math.abs(f.lat - lat) < 2.5) { scarti.fiume++; continue; }
        posToWorld(seg * SEGMENT_LENGTH, lat, P);
        if (roadDist(P.x, P.z) < 3600) { scarti.strada++; continue; }
        lista.push({ x: P.x, y: groundAt(P.x, P.z) - 40, z: P.z, yaw: r() * 6.28, s: 0.9 + r() * 0.5 });
        vicini.push({ seg, lat, raggio: 1.7, ds: 22 }); messi++;
      }
    }
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, side: THREE.DoubleSide });
    pietraShader(mat, 'paesaggio-ovoo', true);
    const m = new THREE.InstancedMesh(g, mat, Math.max(1, lista.length)); m.count = lista.length;
    lista.forEach((o, k) => m.setMatrixAt(k, M.compose(V.set(o.x, o.y, o.z), Q.setFromAxisAngle(su, o.yaw), S.setScalar(o.s))));
    m.computeBoundingSphere(); m.castShadow = m.receiveShadow = true;
    scene.add(m);
    return { m, n: lista.length, scarti };
  })();

  // massi sparsi lungo la pista, più fitti dove la tappa è rocciosa
  const massi = (() => {
    const DENS = [0.05, 0.08, 0.30, 0.10, 0.28, 0.02, 0.10, 0.45, 0.35, 0.18, 0.12, 0.06];   // per tappa
    const rr = rng(777), BLOCCO = 300, perBlocco = new Map(), ps = [0, 0, 0, 0];
    for (let seg = 20; seg < N - 6; seg += 5) {
      const k = Math.min(DENS.length - 1, tappaDi(seg * SEGMENT_LENGTH));
      pesiSuolo(seg, ps);
      const d = DENS[k] + 0.5 * ps[3];
      if (rr() > d) continue;
      const lato = rr() < 0.5 ? -1 : 1, lat = lato * (2.9 + Math.pow(rr(), 1.5) * 9);
      if (sulPonte.has(seg) || !libero(seg, lat)) continue;
      posToWorld((seg + rr() * 5) * SEGMENT_LENGTH, lat, P);
      if (roadDist(P.x, P.z) < 3600) continue;
      const grande = rr() < 0.08 + 0.2 * ps[3], sz = grande ? 900 + rr() * 1500 : 220 + rr() * 650;
      const kk = Math.floor(seg / BLOCCO); if (!perBlocco.has(kk)) perBlocco.set(kk, []);
      perBlocco.get(kk).push({ x: P.x, y: groundAt(P.x, P.z), z: P.z, sz, yaw: rr() * 6.28, forma: rr() < 0.5 ? 0 : 1, v: 0.8 + rr() * 0.4, sx: 0.8 + rr() * 0.5 });
    }
    const forme = [roccia(2.3), roccia(5.9)];
    const mat = new THREE.MeshStandardMaterial({ color: 0x8a867c, roughness: 0.95 });
    pietraShader(mat, 'paesaggio-massi', false);
    const gruppo = new THREE.Group(); let tot = 0;
    for (const lista of perBlocco.values()) for (const f of [0, 1]) {
      const l = lista.filter(o => o.forma === f); if (!l.length) continue;
      const m = new THREE.InstancedMesh(forme[f], mat, l.length);
      l.forEach((o, k) => m.setMatrixAt(k, M.compose(V.set(o.x, o.y - o.sz * 0.15, o.z), Q.setFromAxisAngle(su, o.yaw), S.set(o.sz * o.sx, o.sz, o.sz))));
      m.setColorAt(0, new THREE.Color(1, 1, 1)); l.forEach((o, k) => m.setColorAt(k, new THREE.Color(o.v, o.v, o.v * 0.97)));
      m.computeBoundingSphere(); m.castShadow = m.receiveShadow = true; gruppo.add(m); tot += l.length;
    }
    scene.add(gruppo);
    return { gruppo, n: tot };
  })();

  // ════════ ERBA: ciuffi fotografati a blocchi di pista attorno al cavallo ════════
  // 16 ciuffi (erbe, ortica, tarassaco, celidonia) da Poly Haven, fotografati di fianco con
  // tools/fotografa-piante.py in assets/alberi/prato.webp (4×4); ogni ciuffo è una croce di
  // due rettangoli. CELLE: [altezza inquadrata (m), metri fra il fondo della foto e il piede]
  const CELLE = [[0.34, 0.096], [0.295, 0.063], [0.29, 0.074], [0.23, 0.006], [0.209, 0.016], [0.335, 0.006],
                 [0.297, 0.006], [0.246, 0.005], [0.272, 0.02], [0.376, 0.058], [0.451, 0.024], [0.225, 0.004],
                 [0.268, 0.052], [0.227, 0.056], [0.287, 0.05], [0.267, 0.046]];
  // (3-7 hanno pennacchi che in foto vengono quasi neri: niente)
  const ERBA_VERDE = [0, 1, 2, 0, 1, 2, 9, 10], ERBA_SECCA = [8, 9, 10], FIORI = [12, 13, 14, 15, 11];
  const erba = (() => {
    const BLOCCO = 40, POOL = 7, MAX = 2400, K = 800 * 2.2;      // i ciuffi veri sono piccoli: ×2,2
    const croce = [new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0), new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0).rotateY(Math.PI / 2)];
    const g = new THREE.BufferGeometry();
    {
      const pos = [], uv = [], nor = [], idx = [];
      croce.forEach((q, n) => {
        pos.push(...q.attributes.position.array); uv.push(...q.attributes.uv.array);
        for (let i = 0; i < 4; i++) nor.push(0, 1, 0);                 // luce come un prato, non come un muro
        idx.push(...Array.from(q.index.array, i => i + n * 4));
      });
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
      g.setIndex(idx);
    }
    const tex = new THREE.TextureLoader().load('assets/alberi/prato.webp');
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    const mat = new THREE.MeshStandardMaterial({ map: tex, alphaTest: 0.4, alphaToCoverage: true, roughness: 0.95, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'paesaggio-erba';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uTempo, uVento;\nuniform vec3 uGiocatore;\nattribute float aCella;')
        .replace('#include <uv_vertex>', `#include <uv_vertex>
          vMapUv = (vec2(mod(aCella, 4.0), 3.0 - floor(aCella / 4.0)) + uv) / 4.0;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          #ifdef USE_INSTANCING
          {
            vec3 ip = instanceMatrix[3].xyz;
            float sx = length(instanceMatrix[0].xyz);
            // raffiche che attraversano il prato; i bassi (in uVento) le rinforzano
            float raffica = sin(dot(ip.xz, vec2(0.0007, 0.0005)) - uTempo * 1.8) * 0.5 + 0.5;
            float h = max(0.0, transformed.y) * max(0.0, transformed.y);
            transformed.z += (0.35 + raffica * 1.3) * uVento * h * 160.0 / sx;   // in unità mondo
            transformed.x += sin(uTempo * 2.7 + ip.x * 0.01) * h * 60.0 / sx;
            // lontano dal cavallo l'erba si abbassa fino a sparire: niente bordo netto
            transformed *= 1.0 - smoothstep(20000.0, 30000.0, distance(ip.xz, uGiocatore.xz));
          }
          #endif`);
    };
    const verde = new THREE.Color(1.35, 1.45, 1.1), paglia = new THREE.Color(1.75, 1.45, 0.85), c = new THREE.Color(), ps = [0, 0, 0, 0];
    const pool = Array.from({ length: POOL }, () => {
      const gg = new THREE.InstancedBufferGeometry().copy(g);
      gg.setAttribute('aCella', new THREE.InstancedBufferAttribute(new Float32Array(MAX), 1));
      const m = new THREE.InstancedMesh(gg, mat, MAX); m.count = 0; m.blocco = -1; m.receiveShadow = true;
      scene.add(m); return m;
    });
    const scegli = (r, l) => l[(r() * l.length) | 0];
    function genera(m, b) {
      const r = rng(b * 7 + 3), celle = m.geometry.attributes.aCella; let n = 0;
      for (let s = b * BLOCCO; s < (b + 1) * BLOCCO && s < N - 2; s += 0.25) {
        pesiSuolo(Math.floor(s), ps);
        const dens = ps[0] + ps[1] * 0.85 + ps[3] * 0.2;           // sulla sabbia niente erba
        const verdeQ = ps[0] / Math.max(0.01, ps[0] + ps[1]);
        for (let q = 0; q < 7 && n < MAX; q++) {
          if (r() > dens) continue;
          const lato = r() < 0.5 ? -1 : 1, lat = lato * (1.32 + Math.pow(r(), 1.4) * 6.5);
          if (!libero(s, lat)) continue;
          posToWorld((s + r() * 0.25) * SEGMENT_LENGTH, lat, P);
          const a = Math.abs(lat);
          // sulla banchina a quota strada, sulla scarpata a scendere, poi il terreno
          const y = a <= 2.4 ? P.y : Math.max(groundAt(P.x, P.z), P.y - 300 - (a - 2.4) / 1.6 * 1200);
          // fiori dove il prato è verde, erba secca dove è steppa
          const cella = r() < 0.07 * verdeQ ? scegli(r, FIORI) : r() < verdeQ ? scegli(r, ERBA_VERDE) : scegli(r, ERBA_SECCA);
          const [orto, base] = CELLE[cella], lato2 = orto * K * (0.8 + r() * 0.6);
          M.compose(V.set(P.x, y - base / orto * lato2 - 10, P.z), Q.setFromAxisAngle(su, r() * 6.28), S.set(lato2, lato2, lato2));
          m.setMatrixAt(n, M); celle.array[n] = cella;
          c.copy(paglia).lerp(verde, verdeQ).multiplyScalar(0.8 + r() * 0.4);
          m.setColorAt(n, c);
          n++;
        }
      }
      m.count = n; m.blocco = b; celle.needsUpdate = true;
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
    libero, occupa: (seg, lat, raggio, ds) => vicini.push({ seg, lat, raggio, ds }), fiumi, accampamenti, pali, nuvole, ovoo, massi,
    // la pagina passa la luce della tappa: sole (lato acceso) e cielo (lato in ombra)
    tingi(sole, cielo, foschia) { uNuvole.uSole.value.copy(sole); uNuvole.uOmbra.value.copy(cielo); uNuvole.uFoschia.value.copy(foschia); },
    aggiorna({ camera, posRender, giorno, nebbia }) {
      const t = performance.now(), dt = Math.min(0.1, (t - tPrec) / 1000); tPrec = t;
      const k = Math.min(COPERTURA.length - 1, tappaDi(posRender));
      nuvole.aggiorna(camera.position, dt, COPERTURA[k]);
      erba.aggiorna(posRender);
      U.uLuci.value = 1 - giorno;
    },
  };
}
