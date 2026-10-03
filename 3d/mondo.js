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
          uniform vec3 uColLinee, uColEq;`)
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

  // ── TERRENO: onde dal cavallo, solo lontano dalla strada ──
  function patchTerreno(mat) {
    mat.customProgramCacheKey = () => 'mondo-terreno';
    mat.onBeforeCompile = sh => {
      conUniform(sh);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', `#include <common>
          attribute float aDist;                 // 0 sulla scarpata (che l'attributo non ce l'ha): mai mossa
          uniform float uTerrAmp, uBattiti;
          uniform vec3 uGiocatore;`)
        .replace('#include <begin_vertex>', `#include <begin_vertex>
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

  return { U, texSpettro, patchStrada, patchTerreno, patchAlbero, profonditaAlbero, patchPaletti, laser: laser.gruppo, aggiorna };
}
