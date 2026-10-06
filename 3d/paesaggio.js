// PAESAGGIO — quello che c'è attorno alla strada oltre agli alberi (vedi 3d/alberi.js).
//
//   fiumi        · acqua che riflette il cielo e si increspa coi bassi, nelle tappe dei fiumi
//                  (il letto lo scava il terreno: vedi fiumeAl() e il passo 5b nella pagina)
//   nuvole       · nuvole volumetriche fotografate in Cycles, che seguono la camera; quante dipende dalla tappa
//   montagne     · due anelli di creste all'orizzonte, nel colore della foschia
//   pali         · pali di legno con la sciarpa blu (khadag) al posto dei paletti da circuito;
//                  le luci a tempo ora accendono la sciarpa
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
    const pos = [];
    let prima = null;
    for (let s = 0; s < N - 2; s += 2) {
      const f = fiumeAl(s);
      if (!f || f.mezza < 60) { prima = null; continue; }
      const a = punti[s], rx = -Math.cos(a.heading), rz = Math.sin(a.heading);
      const cx = a.x + rx * f.lat * ROAD_WIDTH, cz = a.z + rz * f.lat * ROAD_WIDTH;
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
      piano:    new THREE.BoxGeometry(5200, 90, SEGMENT_LENGTH + 4),    // lastre: 45 sopra la pista
      soletta:  new THREE.BoxGeometry(5600, 520, SEGMENT_LENGTH + 4),   // lo spessore sotto
      parapetto:new THREE.BoxGeometry(300, 560, SEGMENT_LENGTH + 4),
      copertina:new THREE.BoxGeometry(400, 90, SEGMENT_LENGTH + 4),
      spalla:   new THREE.BoxGeometry(6000, 2600, 900),
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
  // il palo è un tronco lavorato a mano: più grosso alla base, appena curvo, schiarito dal sole in
  // cima e scuro e umido a terra; la sciarpa è legata con una corda di canapa e ha le frange.
  // aSciarpa: −1 = legno/corda (lo shader gli disegna le venature), 0…1 = sciarpa dal nodo alla punta
  const pali = (() => {
    const b = costruttore();
    const legno = col('#7a5636'), umido = col('#3b2a1a'), sole = col('#a98c68'), canapa = col('#d9c9a0');
    const palo = new THREE.CylinderGeometry(36, 56, 1000, 8, 10); palo.translate(0, 500, 0);
    b.geo(palo, null, -1, (x, y, z) => {
      const t = Math.min(1, Math.max(0, y / 1000));
      const c = t < 0.22 ? umido.map((u, i) => u + (legno[i] - u) * (t / 0.22)) : legno.map((l, i) => l + (sole[i] - l) * Math.pow((t - 0.22) / 0.78, 1.6));
      return c;
    });
    // il fusto non è dritto: una curva dolce (applicata ai vertici già inseriti)
    // la cima: taglio obliquo schiarito, come un palo segato
    const cima = new THREE.ConeGeometry(62, 80, 8); cima.translate(0, 1040, 0);
    b.geo(cima, sole.map(c => c * 0.85), -1);
    // corda di canapa: tre giri attorno al palo dove si lega la sciarpa
    for (let k = 0; k < 3; k++) {
      const giro = new THREE.TorusGeometry(48 + (850 - 500) * 0.0, 11, 5, 10); giro.rotateX(Math.PI / 2); giro.translate(0, 820 + k * 24, 0);
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
    const g = b.geometria('aSciarpa');
    const slots = [];
    for (let i = 6; i < N - 4; i += 4) if (!sulPonte.has(i)) for (const lato of [-1, 1]) slots.push({ i, lato });   // sui ponti c'è il parapetto
    g.setAttribute('aIdx', new THREE.InstancedBufferAttribute(new Float32Array(slots.map(p => p.i / 4)), 1));
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'paesaggio-pali';
    mat.onBeforeCompile = sh => {
      uni(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
          attribute float aIdx, aSciarpa;
          uniform float uLed, uLedFlash, uCorsa, uTempo, uVento;
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
            transformed.z += (sin(uTempo * 6.0 + aIdx * 1.7 - s * 9.0) * 0.6 + sin(uTempo * 3.1 + aIdx - s * 5.0) * 0.4) * s * 70.0 * (0.4 + uVento);
            transformed.y += sin(uTempo * 4.3 + aIdx * 2.3 - s * 7.0) * s * 45.0;
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
    const m = new THREE.InstancedMesh(g, mat, slots.length);
    const look = {}, tilt = new THREE.Quaternion(), eu = new THREE.Euler();
    slots.forEach((p, k) => {
      posToWorld(p.i * SEGMENT_LENGTH, p.lato * 1.18, P, look);
      Q.setFromAxisAngle(su, look.heading + Math.PI / 2);          // la sciarpa ricade all'indietro
      const h = ((p.i * 7919) % 100) / 100, h2 = ((p.i * 104729) % 100) / 100;
      Q.multiply(tilt.setFromEuler(eu.set((h - 0.5) * 0.07, 0, (h2 - 0.5) * 0.07)));   // ogni palo un po' storto
      m.setMatrixAt(k, M.compose(V.set(P.x, P.y - 20, P.z), Q, S.setScalar(0.86 + h2 * 0.28)));
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
    return { m, n: gher.length };
  })();

  // libero(seg, lat): niente alberi né erba nel fiume o dentro un accampamento
  function libero(seg, lat) {
    const f = fiumeAl(Math.round(seg));
    if (f && Math.abs(lat - f.lat) * ROAD_WIDTH < f.mezza + 1400) return false;
    for (const c of vicini) if (Math.abs(c.seg - seg) < 60 && Math.abs(c.lat - lat) < c.raggio) return false;
    return true;
  }

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
    libero, fiumi, accampamenti, pali, nuvole,
    // la pagina passa la luce della tappa: sole (lato acceso) e cielo (lato in ombra)
    tingi(sole, cielo, foschia) { uNuvole.uSole.value.copy(sole); uNuvole.uOmbra.value.copy(cielo); uNuvole.uFoschia.value.copy(foschia); },
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
