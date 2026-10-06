// ATMOSFERA — quello che sta fra la pista e il cielo.
//
//   montagne      · un anello di rilievo vero (creste, valli, neve) attorno alla camera, nel colore della
//                   foschia più lontano è; alte e innevate sul Khangai, basse e color sabbia nelle dune
//   luna          · disco con i mari e un alone, in cielo quando le stelle si accendono
//   lucciole      · puntini che lampeggiano attorno al cavallo la sera, a tempo di cassa
//   fuochi        · un fuoco davanti a ogni gher all'alba, al tramonto e di notte, che pulsa sui bassi;
//                   i due più vicini fanno luce vera (PointLight) sul cavallo e sul prato
//   nebbia bassa  · banchi di nebbia che stanno nelle valli, tanta sui fiumi e al mattino
//
// Tutto si aggiorna da `aggiorna()`, una volta per frame.

import * as THREE from 'three';

function rng(seme) { let s = (seme * 2654435761) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

// ── rumore per le montagne (in JS: la geometria si costruisce una volta) ──
const h2 = (x, z) => { const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453; return s - Math.floor(s); };
function n2(x, z) {
  const ix = Math.floor(x), iz = Math.floor(z), fx = x - ix, fz = z - iz, u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
  return (h2(ix, iz) * (1 - u) + h2(ix + 1, iz) * u) * (1 - v) + (h2(ix, iz + 1) * (1 - u) + h2(ix + 1, iz + 1) * u) * v;
}
function fbm(x, z, o = 5) { let a = 0.5, s = 0; for (let k = 0; k < o; k++) { s += a * n2(x, z); x = x * 2.03 + 11; z = z * 2.03 + 7; a *= 0.5; } return s; }
function cresta(x, z, o = 5) { let a = 0.5, s = 0; for (let k = 0; k < o; k++) { s += a * (1 - Math.abs(2 * n2(x, z) - 1)); x = x * 2.1 + 5; z = z * 2.1 + 17; a *= 0.5; } return s; }

// per tappa: [altezza (×), linea della neve (0…1 dell'altezza; >1 = niente neve), roccia]
const MONTI = [
  [0.45, 2.0, '#8b7a64'], [0.65, 1.5, '#7d7a66'], [1.55, 0.50, '#7f7b78'], [0.45, 2.0, '#9a8a68'],
  [0.80, 1.4, '#8d7c64'], [0.40, 2.0, '#bf9f6e'], [0.90, 0.95, '#80796a'], [1.35, 0.68, '#5d4e46'],
  [1.80, 0.46, '#716b68'], [0.65, 2.0, '#9d8664'], [0.85, 1.2, '#8a7e6c'], [1.0, 0.85, '#7a7468'],
];
// per tappa: quanta nebbia bassa (0…1)
const NEBBIA_BASSA = [0.9, 0.7, 0.35, 0.3, 0.2, 0.0, 0.7, 0.55, 0.35, 0.2, 0.45, 0.3];

export function creaAtmosfera({ scene, camera, U, groundAt, posToWorld, SEGMENT_LENGTH, gher }) {
  const tmp = new THREE.Vector3(), M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), V = new THREE.Vector3();
  const su = new THREE.Vector3(0, 1, 0);

  // ════════ MONTAGNE ════════
  const montagne = (() => {
    const NA = 540, NR = 22, R0 = 130000, R1 = 300000, BASE = 52000, pos = [], nor = [], col = [], hn = [], idx = [];
    const R = j => R0 + (R1 - R0) * (j / (NR - 1));
    // riga -1: lo zoccolo che scende sotto il terreno
    for (let j = -1; j < NR; j++) for (let i = 0; i <= NA; i++) {
      const a = i / NA * Math.PI * 2, r = R(Math.max(0, j)), x = Math.sin(a) * r, z = Math.cos(a) * r, rr = Math.max(0, j) / (NR - 1);
      const m = smooth(0.28, 0.72, fbm(x / 210000 + 9, z / 210000 + 3, 3));              // catene: dove si alzano e dove no
      let h = BASE * (0.10 + 0.90 * m) * (0.22 + 0.78 * Math.pow(cresta(x / 85000, z / 85000, 5), 1.35)) * (0.40 + 0.60 * rr);
      h += BASE * 0.05 * fbm(x / 9000, z / 9000, 3);                                      // dentellatura
      if (j < 0) h = -30000;
      pos.push(x, h, z); hn.push(Math.max(0, h) / BASE);
      const g = 0.62 + 0.55 * fbm(x / 5000, z / 5000, 3);
      col.push(g, g * 0.97, g * 0.94); nor.push(0, 1, 0);
    }
    const W = NA + 1;
    for (let j = 0; j < NR; j++) for (let i = 0; i < NA; i++) {
      const a = j * W + i, b = a + 1, c = a + W, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setAttribute('aH', new THREE.Float32BufferAttribute(hn, 1));
    g.setIndex(idx); g.computeVertexNormals();
    const u = { uNeve: { value: 2 }, uRoccia: { value: new THREE.Color('#8b7a64') }, uFoschia: { value: new THREE.Vector3(0.8, 0.8, 0.8) } };
    const mat = new THREE.MeshLambertMaterial({ vertexColors: true, fog: false, side: THREE.DoubleSide });
    mat.customProgramCacheKey = () => 'atmosfera-monti';
    mat.onBeforeCompile = sh => {
      Object.assign(sh.uniforms, u);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aH;\nvarying float vH, vR, vNy;')
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          vH = aH; vNy = normal.y; vR = (length(position.xz) - ${R0.toFixed(1)}) / ${(R1 - R0).toFixed(1)};`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vH, vR, vNy;\nuniform float uNeve;\nuniform vec3 uRoccia, uFoschia;')
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            // roccia: il colore della tappa × le macchie baked; neve in alto e dove il pendio è dolce
            vec3 roccia = uRoccia * diffuseColor.rgb * (1.15 - 0.45 * smoothstep(0.0, 0.6, vH));
            float neve = smoothstep(uNeve, uNeve + 0.14, vH + (diffuseColor.r - 0.8) * 0.35) * smoothstep(0.35, 0.8, vNy);
            diffuseColor.rgb = mix(roccia, vec3(0.93, 0.95, 1.0), neve);
          }`)
        .replace('#include <dithering_fragment>', `
          {
            // prospettiva aerea: più lontano e più in basso, più foschia
            float aria = clamp(0.16 + 0.55 * smoothstep(0.0, 1.0, vR) + 0.30 * (1.0 - smoothstep(0.0, 0.5, vH)), 0.0, 0.9);
            gl_FragColor.rgb = mix(gl_FragColor.rgb, uFoschia, aria);
          }
          #include <dithering_fragment>`);
    };
    const m = new THREE.Mesh(g, mat);
    m.frustumCulled = false; m.renderOrder = -1; scene.add(m);
    let y = 0, alt = 1;
    const roc = new THREE.Color(), tmpC = new THREE.Color();
    return { m, u, aggiorna(cam, nebbia, k, dt) {
      const T = MONTI[Math.min(MONTI.length - 1, k)], kk = Math.min(1, dt * 0.5);
      alt += (T[0] - alt) * kk; u.uNeve.value += (T[1] - u.uNeve.value) * kk;
      u.uRoccia.value.lerp(roc.set(T[2]), kk);
      y += (cam.y - 14000 - y) * Math.min(1, dt * 1.5);
      m.position.set(cam.x, y, cam.z); m.scale.y = alt;
      nebbia.getRGB(tmpC, THREE.SRGBColorSpace);
      u.uFoschia.value.set(tmpC.r, tmpC.g, tmpC.b);
    } };
  })();
  montagne.m.position.y = -14000;

  // ════════ LUNA ════════
  const luna = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const g = c.getContext('2d');
    const alone = g.createRadialGradient(128, 128, 30, 128, 128, 128);
    alone.addColorStop(0, 'rgba(190,210,255,0.55)'); alone.addColorStop(0.35, 'rgba(150,180,255,0.16)'); alone.addColorStop(1, 'rgba(120,150,255,0)');
    g.fillStyle = alone; g.fillRect(0, 0, 256, 256);
    g.save(); g.beginPath(); g.arc(128, 128, 40, 0, 6.2832); g.clip();
    g.fillStyle = '#f3f0e4'; g.fillRect(0, 0, 256, 256);
    const r = rng(3);                                                     // i "mari": macchie grigie e crateri
    for (let i = 0; i < 12; i++) { const x = 100 + r() * 56, y = 100 + r() * 56, R = 6 + r() * 14;
      const q = g.createRadialGradient(x, y, 0, x, y, R); q.addColorStop(0, 'rgba(120,125,135,0.5)'); q.addColorStop(1, 'rgba(120,125,135,0)');
      g.fillStyle = q; g.fillRect(0, 0, 256, 256); }
    g.restore();
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: tex, transparent: true, fog: false,
      depthWrite: false, opacity: 0, color: new THREE.Color(1.6, 1.6, 1.7), toneMapped: false }));
    m.scale.setScalar(70000); m.renderOrder = -0.5; m.visible = false; m.frustumCulled = false;
    scene.add(m);
    const dir = new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - 33), THREE.MathUtils.degToRad(205));
    return { m, dir, yaw: 0 };
  })();

  // ════════ LUCCIOLE ════════
  const lucciole = (() => {
    const N = 320, seme = new Float32Array(N * 4), r = rng(77);
    for (let i = 0; i < N; i++) seme.set([r(), r(), r(), 0.4 + r() * 1.2], i * 4);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(N * 3), 3));
    g.setAttribute('aSeme', new THREE.Float32BufferAttribute(seme, 4));
    const u = { uLuci: { value: 0 }, uCassa: { value: 0 } };
    const mat = new THREE.ShaderMaterial({
      uniforms: { ...U, ...u }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
      vertexShader: `
        attribute vec4 aSeme;
        uniform float uTempo, uLuci, uCassa;
        uniform vec3 uGiocatore;
        varying float vL;
        void main() {
          float t = uTempo;
          // posizione: una scatola attorno al cavallo, che i puntini percorrono lenti e si riavvolge
          vec3 p = fract(aSeme.xyz + vec3(sin(t * 0.07 * aSeme.w + aSeme.x * 30.0), t * 0.012 * aSeme.w, cos(t * 0.06 * aSeme.w + aSeme.z * 30.0)) * 0.5) * 2.0 - 1.0;
          vec3 w = uGiocatore + vec3(p.x * 9000.0, 250.0 + (p.y * 0.5 + 0.5) * 2100.0, p.z * 9000.0);
          w.xz += vec2(sin(t * 0.9 + aSeme.y * 40.0), cos(t * 0.8 + aSeme.x * 40.0)) * 140.0;
          float lamp = pow(sin(t * aSeme.w * 1.8 + aSeme.x * 60.0) * 0.5 + 0.5, 5.0);
          vL = uLuci * (0.12 + 0.88 * lamp + 0.6 * uCassa);
          vec4 mv = viewMatrix * vec4(w, 1.0);
          gl_PointSize = clamp(40000.0 * (1.0 + uCassa) / -mv.z, 1.5, 14.0);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        #include <common>
        varying float vL;
        void main() {
          float d = length(gl_PointCoord - 0.5) * 2.0;
          float a = smoothstep(1.0, 0.0, d); a *= a;
          gl_FragColor = vec4(vec3(0.62, 1.0, 0.3) * 2.2 * a * vL, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    const p = new THREE.Points(g, mat); p.frustumCulled = false; p.visible = false; p.renderOrder = 3;
    scene.add(p);
    return { p, u };
  })();

  // ════════ FUOCHI ════════
  const fuochi = (() => {
    const lista = [];
    for (const o of gher) {
      // davanti alla porta, verso la strada, appena fuori dalla gher
      const fx = o.x + Math.sin(o.yaw) * 3300 * o.s, fz = o.z + Math.cos(o.yaw) * 3300 * o.s;
      lista.push({ x: fx, y: groundAt(fx, fz), z: fz, ph: (fx * 0.013 + fz * 0.007) % 6.28 });
    }
    const n = lista.length;
    // fiamme: due rettangoli verticali (cilindrici) per fuoco, con la fiamma disegnata nello shader
    const quad = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0);
    const g = new THREE.InstancedBufferGeometry().copy(quad);
    g.setAttribute('aPh', new THREE.InstancedBufferAttribute(new Float32Array(Math.max(1, n * 2)).map((_, i) => lista[i >> 1].ph + (i & 1) * 2.3), 1));   // una fase per istanza: due fiamme per fuoco
    const u = { uFuoco: { value: 0 } };
    const mat = new THREE.ShaderMaterial({
      uniforms: { ...U, ...u }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, side: THREE.DoubleSide,
      vertexShader: `
        attribute float aPh;
        uniform float uTempo, uFuoco, uCassa;
        varying vec2 vUv; varying float vPh;
        void main() {
          vec3 ip = instanceMatrix[3].xyz;
          vec2 d = normalize(cameraPosition.xz - ip.xz);
          vec3 destra = vec3(d.y, 0.0, -d.x);
          float alto = 1800.0 * (1.0 + 0.55 * uCassa) * uFuoco, largo = 1050.0 * uFuoco * (1.0 + 0.2 * uCassa);
          vec3 p = ip + destra * position.x * largo + vec3(0.0, position.y * alto, 0.0);
          vUv = uv; vPh = aPh;
          gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
        }`,
      fragmentShader: `
        #include <common>
        varying vec2 vUv; varying float vPh;
        uniform float uTempo, uCassa;
        float hF(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float nF(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(hF(i), hF(i + vec2(1.0, 0.0)), f.x), mix(hF(i + vec2(0.0, 1.0)), hF(i + vec2(1.0, 1.0)), f.x), f.y); }
        void main() {
          float y = vUv.y, x = (vUv.x - 0.5) * 2.0;
          // la fiamma sale: rumore che scorre verso l'alto, più stretta e più scura in cima
          float t = uTempo * 2.4 + vPh * 9.0;
          float n = nF(vec2(x * 2.4 + vPh, y * 3.2 - t)) * 0.65 + nF(vec2(x * 5.1 - vPh, y * 6.0 - t * 1.7)) * 0.35;
          float larg = (1.0 - y) * (0.85 + 0.25 * sin(t * 1.3));
          float m = smoothstep(larg, larg - 0.45, abs(x) + (n - 0.5) * 0.9) * smoothstep(1.0, 0.15, y + (n - 0.5) * 0.55);
          vec3 c = mix(vec3(1.0, 0.18, 0.02), vec3(1.0, 0.72, 0.18), smoothstep(0.0, 0.55, m * (1.0 - y * 0.6)));
          c = mix(c, vec3(1.0, 0.95, 0.75), smoothstep(0.62, 0.95, m) * (1.0 - y));
          gl_FragColor = vec4(c * 2.6 * m * (1.0 + 0.7 * uCassa), 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    const mesh = new THREE.InstancedMesh(g, mat, Math.max(1, n * 2)); mesh.count = n * 2; mesh.frustumCulled = false; mesh.renderOrder = 4;
    lista.forEach((f, k) => {
      for (let q = 0; q < 2; q++) mesh.setMatrixAt(k * 2 + q, M.compose(V.set(f.x, f.y - 20, f.z), Q.identity(), S.set(1, 1, 1)));
    });
    scene.add(mesh);
    // un alone d'aria calda e un disco di luce sul prato (additivi, non toccano il resto)
    const lumeTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g2 = c.getContext('2d');
      const q = g2.createRadialGradient(64, 64, 0, 64, 64, 64); q.addColorStop(0, 'rgba(255,190,90,0.6)'); q.addColorStop(0.45, 'rgba(255,120,30,0.18)'); q.addColorStop(1, 'rgba(255,90,10,0)');
      g2.fillStyle = q; g2.fillRect(0, 0, 128, 128); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
    const lume = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ map: lumeTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, opacity: 0 }), Math.max(1, n));
    lume.count = n; lume.frustumCulled = false; lume.renderOrder = 2;
    lista.forEach((f, k) => lume.setMatrixAt(k, M.compose(V.set(f.x, f.y + 40, f.z), Q.identity(), S.set(4500, 1, 4500))));
    scene.add(lume);
    // le luci vere: due PointLight che si spostano sui fuochi più vicini (il numero di luci non cambia mai: niente ricompilazioni)
    const luci = [0, 1].map(() => { const l = new THREE.PointLight(0xff8a30, 0, 14000, 2); l.position.set(0, -99999, 0); scene.add(l); return l; });
    const scelti = [-1, -1];
    return { lista, mesh, lume, u, luci, scelti, n };
  })();

  // ════════ NEBBIA BASSA ════════
  const nebbiaBassa = (() => {
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    const r = rng(11);
    for (let i = 0; i < 40; i++) { const x = 64 + (r() - 0.5) * 70, y = 64 + (r() - 0.5) * 36, R = 14 + r() * 26;
      const q = g.createRadialGradient(x, y, 0, x, y, R); q.addColorStop(0, 'rgba(255,255,255,0.20)'); q.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = q; g.fillRect(0, 0, 128, 128); }
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    const N = 70, mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, fog: false, opacity: 0.5, side: THREE.DoubleSide });
    const quad = new THREE.PlaneGeometry(1, 1);
    const m = new THREE.InstancedMesh(quad, mat, N); m.frustumCulled = false; m.renderOrder = 1; m.count = 0;
    scene.add(m);
    const r2 = rng(5), banchi = Array.from({ length: N }, () => ({ x: (r2() * 2 - 1) * 90000, z: (r2() * 2 - 1) * 90000, w: 22000 + r2() * 30000, ya: -1e9, soglia: r2(), vento: 0.6 + r2() * 0.8 }));
    return { m, banchi, N, mat, q: new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)) };
  })();

  // ── a ogni frame ──
  const lun = new THREE.Vector3(), bas = new THREE.Color();
  function aggiorna({ cam, tappa, nebbia, giorno, stelleOpacita, musica, v, dt, giocatore, tempo }) {
    dt = Math.min(dt, 0.1);
    const buio = 1 - giorno, cassa = musica.cassa, balla = Math.min(1, (v['mondo.animali'] ?? 0));
    montagne.aggiorna(cam, nebbia, tappa, dt);

    // luna
    luna.m.visible = stelleOpacita > 0.02;
    if (luna.m.visible) {
      // la luna sta in cielo davanti a noi, un po' a destra, e segue le curve piano piano (se no sarebbe sempre alle spalle)
      camera.getWorldDirection(lun);
      const yaw = Math.atan2(lun.x, lun.z);
      let d = yaw + 0.5 - luna.yaw; d = Math.atan2(Math.sin(d), Math.cos(d));
      luna.yaw += d * Math.min(1, dt * 0.25);
      luna.dir.setFromSphericalCoords(1, THREE.MathUtils.degToRad(90 - 27), luna.yaw);
      luna.m.position.copy(cam).addScaledVector(luna.dir, 330000);
      luna.m.quaternion.copy(camera.quaternion);
      luna.m.material.opacity = stelleOpacita;
    }

    // lucciole: la sera, e un po' di più a tempo
    lucciole.p.visible = buio > 0.12;
    lucciole.u.uLuci.value = smooth(0.12, 0.6, buio);
    lucciole.u.uCassa.value = cassa * (0.3 + 0.7 * balla);

    // fuochi
    const accesi = smooth(0.22, 0.6, buio);
    fuochi.mesh.visible = fuochi.lume.visible = accesi > 0.01 && fuochi.n > 0;
    fuochi.u.uFuoco.value = accesi;
    fuochi.lume.material.opacity = accesi * (0.4 + 0.15 * Math.sin(tempo * 7.0) + 0.35 * cassa);
    U.uCassa.value = cassa;
    if (fuochi.mesh.visible) {
      // i due fuochi più vicini, entro 30.000 unità, fanno luce
      let a = -1, b = -1, da = 9e8, db = 9e8;
      for (let i = 0; i < fuochi.n; i++) {
        const f = fuochi.lista[i], dx = f.x - giocatore.x, dz = f.z - giocatore.z, d = dx * dx + dz * dz;
        if (d < da) { b = a; db = da; a = i; da = d; } else if (d < db) { b = i; db = d; }
      }
      [a, b].forEach((i, k) => {
        const l = fuochi.luci[k], f = i >= 0 ? fuochi.lista[i] : null, dist = f ? Math.sqrt(k ? db : da) : 1e9;
        if (!f || dist > 30000) { l.intensity = 0; return; }
        l.position.set(f.x, f.y + 700, f.z);
        l.intensity = accesi * 7e6 * (0.85 + 0.15 * Math.sin(tempo * 9 + f.ph * 3) + 0.6 * cassa) * smooth(30000, 9000, dist);
      });
    } else fuochi.luci.forEach(l => { l.intensity = 0; });

    // nebbia bassa: banchi che stanno nelle valli attorno alla camera
    const densita = NEBBIA_BASSA[Math.min(NEBBIA_BASSA.length - 1, tappa)];
    const nb = nebbiaBassa;
    nb.mat.opacity = 0.2 + 0.45 * densita;
    nb.mat.color.copy(nebbia).multiplyScalar(1.05 + 0.1 * (1 - buio));
    let n = 0;
    for (const b of nb.banchi) {
      b.z += dt * 220 * b.vento;                                                              // scorre piano col vento
      const dx = ((b.x - cam.x) % 180000 + 270000) % 180000 - 90000, dz = ((b.z - cam.z) % 180000 + 270000) % 180000 - 90000;
      const wx = cam.x + dx, wz = cam.z + dz;
      if (b.soglia > densita) continue;
      if (b.wx === undefined || Math.abs(wx - b.wx) > 5000 || Math.abs(wz - b.wz) > 5000) { b.ya = groundAt(wx, wz); b.wx = wx; b.wz = wz; }
      if (Math.hypot(dx, dz) < 12000) continue;                                               // non addosso al cavallo
      V.set(wx, b.ya + 450, wz); S.set(b.w, b.w * 0.7, 1);
      nb.m.setMatrixAt(n++, M.compose(V, nb.q, S));
    }
    nb.m.count = n; nb.m.instanceMatrix.needsUpdate = true;
  }

  return { aggiorna, montagne, luna, lucciole, fuochi, nebbiaBassa };
}
