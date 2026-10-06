// MONDO — la pista, il terreno, gli alberi e i paletti ballano a tempo (Fase 4).
//
// Niente geometria nuova dove non serve: si aggancia il codice agli SHADER dei
// materiali che ci sono già (onBeforeCompile), con uniform condivise che si
// aggiornano una volta per frame. Tutto parte da 0: a SMARMELLA 0 ogni effetto
// somma zero e il mondo è quello di prima.
//
//   strada    · LINEE DEL BATTITO: bande di luce a distanza velocità × tempo al
//               battito → il cavallo ci passa sopra esattamente sul battito
//             · EQUALIZZATORE sui cigli: barre dello spettro dipinte sull'asfalto
//   terreno   · onde che partono dal cavallo a ogni battito, SOLO lontano dalla
//               strada (attributo aDist = distanza dal corridoio di QUALUNQUE ramo)
//   alberi    · ognuno ascolta una banda dello spettro e cresce con lei (GPU:
//               prima il party ricalcolava ~36 mila matrici a frame sulla CPU)
//   paletti   · luci che corrono a sedicesimi, colore della palette, lampo sulla cassa
//   laser     · fasci dall'orizzonte che spazzano sui charleston (seguono il giocatore)

import * as THREE from 'three';

export function creaMondo() {
  // ── spettro come texture 64×1 per gli shader ──
  const datiSpettro = new Uint8Array(64);
  const texSpettro = new THREE.DataTexture(datiSpettro, 64, 1, THREE.RedFormat, THREE.UnsignedByteType);
  texSpettro.magFilter = THREE.LinearFilter; texSpettro.minFilter = THREE.LinearFilter;
  texSpettro.needsUpdate = true;

  // uniform condivise: stesso oggetto in tutti i materiali, si aggiornano una volta
  const U = {
    uSpettro:   { value: texSpettro },
    uBattiti:   { value: 0 },                       // battito + fase (cresce sempre)
    // strada
    uLinee:     { value: 0 }, uEqBordi: { value: 0 },
    uStradaD:   { value: 0 },                       // dove sta il cavallo, in coordinate UV della strada × uvTile
    uPrimo:     { value: 0 }, uPasso: { value: 1 }, // distanza della prossima linea, distanza fra due linee
    uColLinee:  { value: new THREE.Color(1, 0.85, 0.3) },
    uColEq:     { value: new THREE.Color(0.25, 0.8, 1) },
    // terreno
    uTerrAmp:   { value: 0 }, uGiocatore: { value: new THREE.Vector3() },
    // alberi
    uPulseXZ:   { value: 1 }, uPulseY: { value: 1 }, uForesta: { value: 0 },
    uTempo:     { value: 0 }, uVento: { value: 1 }, uRim: { value: 0.22 },
    // paletti
    uLed:       { value: 0 }, uLedFlash: { value: 0 }, uCorsa: { value: 0 },
    uColLed:    { value: new THREE.Color(1, 0.84, 0.25) },
  };
  const conUniform = sh => { for (const k in U) sh.uniforms[k] = U[k]; };

  // ── STRADA: linee del battito + equalizzatore sui cigli ──
  function patchStrada(mat, { uvTile, preD, semiLarg }) {
    mat.customProgramCacheKey = () => 'mondo-strada';
    mat.onBeforeCompile = sh => {
      conUniform(sh);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vStrada;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvStrada = uv;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec2 vStrada;
          uniform sampler2D uSpettro;
          uniform float uLinee, uEqBordi, uStradaD, uPrimo, uPasso;
          uniform vec3 uColLinee, uColEq;
          ${RUMORE_GLSL}`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            // PISTA DI TERRA E GHIAIA: due solchi di ruote più scuri e lisci, in mezzo una
            // striscia dove a tratti cresce l'erba, sassi chiari sparsi, chiazze di terra
            vec2 sp = vStrada * ${uvTile.toFixed(1)};                  // x laterale, y lungo pista (unità mondo)
            float L = sp.x / ${semiLarg.toFixed(1)};                   // −1…1 da ciglio a ciglio
            float chiazze = fbmT(sp * 0.0009);
            vec3 terra = mix(vec3(0.36, 0.28, 0.20), vec3(0.55, 0.45, 0.33), chiazze);
            float solco = 0.0;
            for (int k = -1; k <= 1; k += 2) {
              float c = float(k) * (0.38 + 0.05 * sin(sp.y * 0.0007));  // i solchi serpeggiano appena
              solco = max(solco, 1.0 - smoothstep(0.06, 0.16, abs(L - c)));
            }
            terra *= 1.0 - 0.28 * solco;
            float mezzo = (1.0 - smoothstep(0.08, 0.2, abs(L))) * smoothstep(0.45, 0.7, fbmT(sp * 0.00025 + 3.0));
            terra = mix(terra, vec3(0.30, 0.36, 0.17) * (0.8 + 0.4 * rumoreT(sp * 0.02)), mezzo * 0.85);
            float sasso = smoothstep(0.82, 0.9, rumoreT(sp * 0.045)) * (1.0 - solco);
            terra = mix(terra, vec3(0.68, 0.64, 0.58), sasso * 0.7);
            terra *= mix(1.0, 0.75, smoothstep(0.85, 1.0, abs(L)));   // bordi più scuri, verso il cordolo
            diffuseColor.rgb *= terra * 1.6;                              // × tinta del bioma (vertex color)
          }`)
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          {
            float D = vStrada.y * ${uvTile.toFixed(1)};             // lungo pista (unità mondo, coi PRE davanti)
            float L = vStrada.x * ${uvTile.toFixed(1)};             // laterale
            float avanti = D - uStradaD;
            if (uLinee > 0.001) {
              float S = max(uPasso, 1.0);
              float n = floor((avanti - uPrimo) / S + 0.5);
              float dl = abs(avanti - uPrimo - n * S);
              float linea = (n >= 0.0 && n < 8.0) ? (1.0 - smoothstep(70.0, 200.0, dl)) * (1.0 - n / 8.0) : 0.0;   // larga: si vede di taglio
              totalEmissiveRadiance += uColLinee * linea * uLinee * 3.0;
            }
            if (uEqBordi > 0.001) {
              float Dt = D - ${preD.toFixed(1)};
              float bordo = ${semiLarg.toFixed(1)} - abs(L);       // dal ciglio verso l'interno
              float idx = mod(floor(Dt / 500.0), 64.0);
              float v = texture2D(uSpettro, vec2((idx + 0.5) / 64.0, 0.5)).r;
              float barra = step(0.0, bordo) * step(bordo, 30.0 + v * 340.0) * step(140.0, mod(Dt, 500.0));
              totalEmissiveRadiance += uColEq * barra * uEqBordi * (0.3 + 1.4 * v);
            }
          }`);
    };
    mat.needsUpdate = true;
  }

  // ── TERRENO: onde dal cavallo (solo lontano dalla strada) + SUOLO PER BIOMA ──
  // aSuolo = pesi di erba verde, steppa secca, sabbia, roccia (dal bioma della tappa
  // e dalla pendenza). L'erba è la texture che c'era; secca, sabbia e roccia sono
  // disegnate qui, senza texture nuove: paglia dall'erba, increspature del vento
  // sulla sabbia, roccia venata.
  const RUMORE_GLSL = `
    float hashT(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float rumoreT(vec2 p) {
      vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(hashT(i), hashT(i + vec2(1,0)), f.x), mix(hashT(i + vec2(0,1)), hashT(i + vec2(1,1)), f.x), f.y);
    }
    float fbmT(vec2 p) { float v = 0.0, a = 0.5; for (int k = 0; k < 4; k++) { v += a * rumoreT(p); p *= 2.07; a *= 0.5; } return v; }`;
  // ── BANCHINA: la striscia di terra fra la pista e l'erba ──
  // ghiaia fine, qualche sasso, il ciglio della pista pressato e scuro, e verso l'esterno la terra
  // si fa umida e screziata d'erba secca (i ciuffi fotografati vengono a poggiarsi qui)
  function patchBanchina(mat, { uvTile, interno, largo }) {
    mat.customProgramCacheKey = () => 'mondo-banchina';
    mat.onBeforeCompile = sh => {
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vBanc;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBanc = uv;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>\nvarying vec2 vBanc;\n${RUMORE_GLSL}`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            vec2 sp = vBanc * ${uvTile.toFixed(1)};
            float t = clamp((abs(sp.x) - ${interno.toFixed(1)}) / ${largo.toFixed(1)}, 0.0, 1.0);   // 0 ciglio → 1 fuori
            float g = fbmT(sp * 0.0024);
            vec3 terra = mix(vec3(0.34, 0.25, 0.17), vec3(0.72, 0.58, 0.42), smoothstep(0.25, 0.75, g));   // chiazze di terra chiara e scura
            terra *= 0.7 + 0.6 * fbmT(sp * 0.011);                              // grumi
            terra *= 0.85 + 0.3 * rumoreT(sp * 0.07);                           // ghiaia fine
            // sassolini (~5 cm) con l'ombra sotto, e qualche sasso più grosso (~15 cm) molto raro
            float s1 = smoothstep(0.80, 0.85, rumoreT(sp * 0.022 + 7.0));
            float s2 = smoothstep(0.90, 0.93, rumoreT(sp * 0.008 + 3.0));
            vec3 pietra = vec3(0.60, 0.56, 0.50) * (0.7 + 0.6 * rumoreT(sp * 0.12));
            terra = mix(terra, terra * 0.6, smoothstep(0.76, 0.80, rumoreT(sp * 0.022 + 7.0)) * (1.0 - s1));
            terra = mix(terra, pietra, max(s1 * 0.75, s2 * 0.9));
            // verso l'esterno: terra umida e scura, screziata d'erba secca
            float erbaN = fbmT(sp * 0.004 + 11.0);
            float erba = smoothstep(0.30, 0.95, t + (erbaN - 0.5) * 0.9);
            terra = mix(terra, terra * vec3(0.82, 0.88, 0.62), erba * 0.55);
            terra *= 1.0 - 0.3 * (1.0 - smoothstep(0.0, 0.1, t));            // ciglio pressato
            diffuseColor.rgb *= terra * 1.7;                                   // × tinta del bioma
          }`);
    };
    mat.needsUpdate = true;
  }

  function patchTerreno(mat) {
    mat.customProgramCacheKey = () => 'mondo-terreno';
    mat.onBeforeCompile = sh => {
      conUniform(sh);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec4 vSuolo;
          varying vec3 vPosT;
          ${RUMORE_GLSL}`)
        .replace('#include <color_fragment>', `#include <color_fragment>
          {
            vec4 w = vSuolo / max(1e-3, vSuolo.x + vSuolo.y + vSuolo.z + vSuolo.w);
            vec3 erba = diffuseColor.rgb;                                   // texture d'erba × tinta per quota
            float l = dot(erba, vec3(0.299, 0.587, 0.114));
            vec3 secca = l * vec3(1.30, 1.06, 0.55) * (0.85 + 0.3 * rumoreT(vPosT.xz * 0.0011));   // paglia
            // sabbia: increspature del vento (onde storte dal rumore) + grana fine
            float rip = sin(dot(vPosT.xz, vec2(0.0042, 0.0027)) * 6.2831 + fbmT(vPosT.xz * 0.0006) * 7.0);
            vec3 sabbia = mix(vec3(0.50, 0.31, 0.15), vec3(0.74, 0.52, 0.30), 0.5 + 0.5 * rip)
                          * (0.9 + 0.2 * rumoreT(vPosT.xz * 0.05)) * (0.85 + 0.3 * fbmT(vPosT.xz * 0.00008));
            // roccia: macchie larghe + venature
            float n = fbmT(vPosT.xz * 0.0012 + vPosT.y * 0.0004);
            float vena = smoothstep(0.45, 0.5, abs(fbmT(vPosT.xz * 0.004) - 0.5) + 0.42);
            vec3 roccia = mix(vec3(0.20, 0.18, 0.17), vec3(0.42, 0.38, 0.34), n) * (1.0 - 0.35 * vena);
            diffuseColor.rgb = erba * w.x + secca * w.y + sabbia * w.z + roccia * w.w;
          }`);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', `#include <common>
          attribute float aDist;                 // 0 sulla scarpata (che l'attributo non ce l'ha): mai mossa
          attribute vec4 aSuolo;
          varying vec4 vSuolo;
          varying vec3 vPosT;
          uniform float uTerrAmp, uBattiti;
          uniform vec3 uGiocatore;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          vSuolo = aSuolo; vPosT = position;
          if (uTerrAmp > 0.5) {
            // oltre la banchina E oltre gli alberi (piantati fino a ~6000 dal corridoio)
            float m = smoothstep(8000.0, 23000.0, aDist);   // l'albero più lontano dal corridoio sta a 7135
            if (m > 0.0) {
              float d = distance(position.xz, uGiocatore.xz);
              float onda = 0.5 + 0.5 * cos(6.2831853 * (d / 24000.0 - uBattiti));   // un anello per battito
              transformed.y += uTerrAmp * m * (onda - 0.3) * exp(-d / 110000.0);
            }
          }`);
    };
    mat.needsUpdate = true;
  }

  // ── ALBERI: ognuno ascolta una banda; il party ora è un uniform, non 36 mila matrici ──
  const PATCH_ALBERO = `#include <begin_vertex>
    {
      float v = texture2D(uSpettro, vec2((aBanda * 63.0 + 0.5) / 64.0, 0.5)).r;
      float sy = uPulseY * (1.0 + uForesta * v * 1.6);
      float sx = uPulseXZ * (1.0 + uForesta * v * 0.45);
      transformed = vec3(transformed.x * sx, (transformed.y + aOff) * sy - aOff, transformed.z * sx);
      // vento: più in alto più si piega, ognuno col suo passo
      float hh = max(0.0, transformed.y) / 4000.0, w = uVento * hh * hh;
      transformed.x += sin(uTempo * 1.6 + aBanda * 37.0) * w * 90.0;
      transformed.z += cos(uTempo * 1.1 + aBanda * 23.0) * w * 60.0;
      #ifdef USE_INSTANCING
      // gli alberi lontani cavalcano le onde del terreno: stessa formula di patchTerreno
      if (uTerrAmp > 0.5) {
        float m = smoothstep(8000.0, 23000.0, aDistT);
        if (m > 0.0) {
          vec3 ip = instanceMatrix[3].xyz;
          float d = distance(ip.xz, uGiocatore.xz);
          float onda = 0.5 + 0.5 * cos(6.2831853 * (d / 24000.0 - uBattiti));
          transformed.y += uTerrAmp * m * (onda - 0.3) * exp(-d / 110000.0) / max(length(instanceMatrix[1].xyz), 0.01);
        }
      }
      #endif
    }`;
  const DICH_ALBERO = `#include <common>
    attribute float aBanda;      // per istanza: quale banda dello spettro ascolta (e il passo del vento)
    attribute float aOff;        // per geometria: centro del pezzo rispetto alla base (0 se l'origine è già al piede)
    attribute float aDistT;      // per istanza: distanza dal corridoio stradale (0 = non segue il terreno)
    uniform sampler2D uSpettro;
    uniform float uPulseXZ, uPulseY, uForesta, uTempo, uVento, uTerrAmp, uBattiti;
    uniform vec3 uGiocatore;`;
  function patchAlbero(mat, chiave) {
    mat.customProgramCacheKey = () => 'mondo-albero-' + chiave;
    mat.onBeforeCompile = sh => {
      conUniform(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', DICH_ALBERO).replace('#include <begin_vertex>', PATCH_ALBERO);
      // luce di bordo morbida sulle chiome (solo nel materiale vero, non nell'ombra)
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform float uRim;')
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          { float rim = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 3.0);
            totalEmissiveRadiance += diffuseColor.rgb * rim * uRim; }`);
    };
    mat.needsUpdate = true;
    return mat;
  }
  // l'ombra deve crescere con l'albero: stesso spostamento nel materiale di profondità
  function profonditaAlbero() {
    return patchAlbero(new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking }), 'ombra');
  }

  // ── PALETTI: luci che corrono a sedicesimi + lampo sulla cassa ──
  function patchPaletti(mat) {
    mat.customProgramCacheKey = () => 'mondo-paletti';
    mat.onBeforeCompile = sh => {
      conUniform(sh);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', `#include <common>
          attribute float aIdx;                  // posizione del paletto lungo la pista
          uniform float uLed, uLedFlash, uCorsa;
          varying float vLed;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          {
            float k = mod(aIdx + uCorsa, 8.0);   // uno su otto acceso, la fila corre verso il cavallo
            vLed = uLed * (0.12 + (1.0 - smoothstep(0.0, 1.6, k))) + uLedFlash;
          }`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vLed;\nuniform vec3 uColLed;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += uColLed * vLed;');
    };
    mat.needsUpdate = true;
  }

  // ── LASER: fasci dall'orizzonte, davanti al giocatore ──
  // fusione NORMALE con colore > 1, non additiva: sul cielo chiaro un additivo non si vede
  const laser = (() => {
    const N = 6, gruppo = new THREE.Group(), fasci = [];
    gruppo.visible = false;
    const geo = new THREE.CylinderGeometry(70, 220, 1, 8, 1, true);
    geo.translate(0, 0.5, 0);                         // il perno alla base
    for (let i = 0; i < N; i++) {
      const mat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0,
        depthWrite: false, fog: false, side: THREE.DoubleSide });
      const m = new THREE.Mesh(geo, mat);
      m.scale.set(1, 160000, 1); m.frustumCulled = false;
      gruppo.add(m); fasci.push({ m, mat, ph: i * 1.7, lato: i % 2 ? 1 : -1 });
    }
    return { gruppo, fasci };
  })();

  const col = new THREE.Color();
  // ogni frame: valori della centralina, musica, palette, dove sta il cavallo
  function aggiorna({ v, musica, pal, stradaD, velocita, giocatore, heading, scala }) {
    for (let i = 0; i < 64; i++) datiSpettro[i] = Math.min(255, (musica.spettro[i] || 0) * 255) | 0;
    texSpettro.needsUpdate = true;
    const b = musica.battito + musica.fase;
    U.uBattiti.value = b;
    // linee: la prossima arriva al cavallo esattamente sul prossimo battito
    U.uStradaD.value = stradaD;
    U.uPrimo.value = velocita * (1 - musica.fase) * musica.periodo;
    U.uPasso.value = Math.max(1, velocita * musica.periodo);
    U.uLinee.value = velocita > 1500 ? v['mondo.linee'] : 0;     // da fermi le linee si ammasserebbero sul cavallo
    U.uEqBordi.value = v['mondo.eqBordi'];
    U.uTerrAmp.value = v['mondo.terreno'];
    U.uGiocatore.value.copy(giocatore);
    U.uForesta.value = v['mondo.foresta'];
    U.uTempo.value = performance.now() / 1000;
    U.uVento.value = 1 + 2.5 * musica.bassi * v['mondo.foresta'];   // il vento rinforza coi bassi quando la foresta balla
    U.uLed.value = v['mondo.led'];
    U.uLedFlash.value = v['mondo.ledFlash'];
    U.uCorsa.value = Math.floor(b * 4);                           // a sedicesimi, a scatti
    if (pal) {
      U.uColLinee.value.set(pal.grad[0]).multiplyScalar(1.2);
      U.uColEq.value.set(pal.halo);
      U.uColLed.value.set(pal.halo);
    }
    // laser
    const lz = v['mondo.laser'];
    laser.gruppo.visible = lz > 0.01;
    if (laser.gruppo.visible) {
      const fx = Math.sin(heading), fz = Math.cos(heading), rx = -Math.cos(heading), rz = Math.sin(heading);
      const t = performance.now() / 1000;
      laser.fasci.forEach((f, i) => {
        const lat = (i - 2.5) * 16000;
        f.m.position.set(giocatore.x + fx * 75000 + rx * lat, giocatore.y - 2000, giocatore.z + fz * 75000 + rz * lat);
        // spazzano piano, e scattano sui charleston
        const a = Math.sin(t * 0.7 + f.ph) * 0.55 + musica.charleston * 0.35 * f.lato;
        f.m.rotation.set(Math.sin(t * 0.5 + f.ph * 1.3) * 0.35 - 0.25, heading, a * f.lato);
        f.mat.opacity = Math.min(1, lz * (0.35 + 0.65 * Math.max(musica.cassa, musica.charleston)));
        col.set(pal ? (i % 2 ? pal.halo : pal.grad[1]) : '#ffd23f').multiplyScalar(3 * lz * (scala ?? 1));
        f.mat.color.copy(col);
      });
    }
  }

  return { U, texSpettro, patchStrada, patchBanchina, patchTerreno, patchAlbero, profonditaAlbero, patchPaletti, laser: laser.gruppo, aggiorna };
}
