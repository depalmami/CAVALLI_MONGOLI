// SMARMELLA — il passaggio di post-processing che fa colare l'immagine a tempo.
//
// Va DOPO l'OutputPass (immagine già in sRGB, tone mapping fatto) e lavora in due
// mezzi passaggi a tutto schermo:
//
//   A · STATO   l'immagine nuova deformata (barile, caleidoscopio, glitch,
//               aberrazione, zoom radiale) mescolata col FEEDBACK — il frame di
//               prima zoomato, ruotato, sporcato di rumore e virato di colore.
//               Questo stato si tiene da un frame all'altro: è lui che "cola".
//   B · FINITURA  viraggio, saturazione, bianco bruciato, posterizza, pixel,
//               scanline, grana, vignetta, lampo → schermo.
//
// La finitura sta FUORI dal feedback apposta: se la vignetta o il viraggio
// rientrassero nel giro, si sommerebbero frame dopo frame (nero o arcobaleno
// fisso in mezzo secondo).
//
// A SMARMELLA 0 il passaggio è SPENTO: la pipeline è identica a prima, pixel per
// pixel. Gli shader non includono colorspace_fragment: l'immagine è già sRGB e
// convertirla di nuovo la sbiancherebbe.

import * as THREE from 'three';
import { Pass, FullScreenQuad } from 'three/addons/postprocessing/Pass.js';

// i bersagli del post che la centralina può muovere, col loro intervallo sensato
export const BERSAGLI_POST = {
  colata:     [0, 0.92],   // quanto del frame prima resta (mescola): l'immagine "cola"
  scie:       [0, 0.97],   // scie delle alte luci (il più chiaro fra adesso e prima)
  zoomFb:     [0, 0.06],   // il feedback si allarga: le scie scappano verso i bordi
  ruotaFb:    [-0.06, 0.06],
  ondaFb:     [0, 0.02],   // il feedback ondeggia su un rumore lento
  hueFb:      [0, 0.12],   // le scie cambiano colore a ogni giro
  aberrazione:[0, 0.04],
  zoomRadiale:[0, 0.35],
  barile:     [-0.4, 0.8], // + = pugno verso lo spettatore
  caleido:    [0, 1],
  spicchi:    [2, 12],
  glitch:     [0, 1],
  bruciato:   [0, 1],      // bianco bruciato alla Boris
  hue:        [-1, 1],     // giri di colore (1 = un giro intero)
  saturazione:[0, 2.5],
  posterizza: [0, 1],
  pixel:      [0, 1],
  scanline:   [0, 1],
  grana:      [0, 1],
  vignetta:   [0, 1],
  tinta:      [0, 1],      // le luci prendono i colori della palette dello show (mappa a gradiente)
  flash:      [0, 1],
};

const VERT = /* glsl */`
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

const COMUNE = /* glsl */`
  varying vec2 vUv;
  uniform vec2 uRis;
  uniform float uTempo;
  float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
  float rumore(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f*f*(3.0 - 2.0*f);
    return mix(mix(hash(i), hash(i + vec2(1,0)), f.x), mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
  }
  vec2 specchio(vec2 u) { return 1.0 - abs(1.0 - mod(u, 2.0)); }       // fuori bordo: riflette, niente nero
  vec3 ruotaHue(vec3 c, float a) {                                      // rotazione attorno al grigio
    const vec3 k = vec3(0.57735);
    float ca = cos(a), sa = sin(a);
    return c*ca + cross(k, c)*sa + k*dot(k, c)*(1.0 - ca);
  }`;

const FRAG_STATO = /* glsl */`
  ${COMUNE}
  uniform sampler2D tDiffuse, tPrec;
  uniform float uColata, uScie, uZoomFb, uRuotaFb, uOndaFb, uHueFb;
  uniform float uAberrazione, uZoomRadiale, uBarile, uCaleido, uSpicchi, uGlitch;
  void main() {
    float asp = uRis.x / uRis.y;
    vec2 c = vUv - 0.5; c.x *= asp;
    // caleidoscopio: piega l'angolo in spicchi specchiati, che ruotano piano
    if (uCaleido > 0.001) {
      float r = length(c), a = atan(c.y, c.x);
      float seg = 6.2831853 / max(2.0, floor(uSpicchi));
      float af = abs(mod(a + uTempo*0.15, seg) - seg*0.5);
      c = mix(c, vec2(cos(af), sin(af)) * r, smoothstep(0.0, 1.0, uCaleido));
    }
    // barile: il centro viene incontro (pugno della cassa)
    float r2 = dot(c, c);
    c *= (1.0 - uBarile*0.35) / max(0.2, 1.0 - uBarile*r2*0.9);
    // glitch: fasce orizzontali spostate, che cambiano 15 volte al secondo
    if (uGlitch > 0.001) {
      float seme = floor(uTempo * 15.0);
      float fasce = mix(8.0, 48.0, hash(vec2(seme, 1.7)));
      float f = floor(vUv.y * fasce);
      if (hash(vec2(f, seme)) < uGlitch * 0.55) c.x += (hash(vec2(f, seme + 3.1)) - 0.5) * 0.3 * uGlitch;
    }
    c.x /= asp;
    vec2 uv = c + 0.5;
    // aberrazione cromatica radiale + zoom radiale (scia verso il centro)
    vec3 col;
    if (uZoomRadiale < 0.002) {
      col = vec3(texture2D(tDiffuse, specchio(0.5 + (uv - 0.5)*(1.0 + uAberrazione))).r,
                 texture2D(tDiffuse, specchio(uv)).g,
                 texture2D(tDiffuse, specchio(0.5 + (uv - 0.5)*(1.0 - uAberrazione))).b);
    } else {
      col = vec3(0.0); float tot = 0.0;
      for (int i = 0; i < 8; i++) {
        float t = float(i) / 7.0, w = 1.0 - t*0.6;
        vec2 u = 0.5 + (uv - 0.5) * (1.0 - uZoomRadiale*t);
        col += w * vec3(texture2D(tDiffuse, specchio(0.5 + (u - 0.5)*(1.0 + uAberrazione))).r,
                        texture2D(tDiffuse, specchio(u)).g,
                        texture2D(tDiffuse, specchio(0.5 + (u - 0.5)*(1.0 - uAberrazione))).b);
        tot += w;
      }
      col /= tot;
    }
    // FEEDBACK: il frame di prima, trasformato, rientra
    if (uColata > 0.001 || uScie > 0.001) {
      vec2 f = vUv - 0.5; f.x *= asp;
      float ca = cos(uRuotaFb), sa = sin(uRuotaFb);
      f = mat2(ca, sa, -sa, ca) * f * (1.0 - uZoomFb);
      f.x /= asp;
      vec2 n = vec2(rumore(vUv*3.0 + uTempo*0.35), rumore(vUv*3.0 - uTempo*0.3 + 7.3)) - 0.5;
      vec3 prec = texture2D(tPrec, specchio(0.5 + f + n*uOndaFb)).rgb;
      prec = clamp(ruotaHue(prec, uHueFb * 6.2831853), 0.0, 1.0);
      col = mix(col, prec, uColata);
      // scia = il più chiaro fra adesso e prima, ma per LUMINANZA: col massimo canale per
      // canale le copie virate di colore si sommavano in un grigio-bianco senza forma
      vec3 scia = prec * uScie;
      const vec3 Y = vec3(0.299, 0.587, 0.114);
      col = mix(col, scia, step(dot(col, Y), dot(scia, Y)));
    }
    gl_FragColor = vec4(col, 1.0);
  }`;

const FRAG_FINITURA = /* glsl */`
  ${COMUNE}
  uniform sampler2D tStato;
  uniform float uBruciato, uHue, uSaturazione, uPosterizza, uPixel, uScanline, uGrana, uVignetta, uTinta, uFlash;
  uniform vec3 uT0, uT1, uT2;      // palette dello show: chiaro, medio, scuro
  void main() {
    vec2 uv = vUv;
    if (uPixel > 0.001) { vec2 cella = mix(1.0, 16.0, uPixel) / uRis; uv = (floor(uv / cella) + 0.5) * cella; }
    vec3 c = texture2D(tStato, uv).rgb;
    // bianco bruciato: le luci si aprono e si schiacciano verso il bianco
    if (uBruciato > 0.001) {
      c = 1.0 - pow(max(1.0 - c, 0.0), vec3(1.0 + uBruciato*5.0));
      c = mix(c, vec3(dot(c, vec3(0.299, 0.587, 0.114))), uBruciato*0.35);
    }
    if (abs(uHue) > 0.0005) c = clamp(ruotaHue(c, uHue * 6.2831853), 0.0, 1.0);
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    c = max(mix(vec3(l), c, uSaturazione), 0.0);
    if (uTinta > 0.001) {
      float y = dot(c, vec3(0.299, 0.587, 0.114));
      vec3 g = y < 0.5 ? mix(uT2, uT1, y*2.0) : mix(uT1, uT0, y*2.0 - 1.0);
      c = mix(c, g, uTinta);
    }
    if (uPosterizza > 0.001) { float liv = mix(48.0, 3.0, uPosterizza); c = floor(c*liv + 0.5) / liv; }
    if (uScanline > 0.001) c *= 1.0 - uScanline*0.45*(0.5 + 0.5*sin(gl_FragCoord.y*3.14159));
    if (uGrana > 0.001) c += (hash(gl_FragCoord.xy + fract(uTempo)*97.0) - 0.5) * uGrana * 0.3;
    if (uVignetta > 0.001) c *= 1.0 - uVignetta * smoothstep(0.25, 0.95, length((vUv - 0.5) * vec2(uRis.x/uRis.y, 1.0)) * 1.1);
    c = mix(c, vec3(1.0), uFlash);
    gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
  }`;

const nomeUniform = k => 'u' + k[0].toUpperCase() + k.slice(1);

export class PassoSmarmella extends Pass {
  constructor() {
    super();
    const comuni = { uRis: { value: new THREE.Vector2(1, 1) }, uTempo: { value: 0 } };
    const uniformi = (chiavi, extra) => {
      const u = { ...extra, uRis: comuni.uRis, uTempo: comuni.uTempo };
      for (const k of chiavi) u[nomeUniform(k)] = { value: 0 };
      return u;
    };
    const A = ['colata','scie','zoomFb','ruotaFb','ondaFb','hueFb','aberrazione','zoomRadiale','barile','caleido','spicchi','glitch'];
    const B = ['bruciato','hue','saturazione','posterizza','pixel','scanline','grana','vignetta','tinta','flash'];
    this.matStato = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG_STATO, depthTest: false, depthWrite: false,
      uniforms: uniformi(A, { tDiffuse: { value: null }, tPrec: { value: null } }) });
    this.matFinitura = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG_FINITURA, depthTest: false, depthWrite: false,
      uniforms: uniformi(B, { tStato: { value: null }, uT0: { value: new THREE.Color(1, 0.96, 0.65) },
                              uT1: { value: new THREE.Color(1, 0.62, 0.11) }, uT2: { value: new THREE.Color(0.9, 0.22, 0.27) } }) });
    this.matFinitura.uniforms.uSaturazione.value = 1;
    this.matStato.uniforms.uSpicchi.value = 6;
    this.quadStato = new FullScreenQuad(this.matStato);
    this.quadFinitura = new FullScreenQuad(this.matFinitura);
    // stato a mezza precisione: con 8 bit le scie che decadono lasciano un fantasma che non sparisce mai
    const opz = { type: THREE.HalfFloatType, depthBuffer: false };
    this.stato = [new THREE.WebGLRenderTarget(1, 1, opz), new THREE.WebGLRenderTarget(1, 1, opz)];
    this.cur = 0;
    this.daPulire = true;
    this.comuni = comuni;
    this.enabled = false;
  }

  // valori: { colata, scie, …, flash } — chiavi di BERSAGLI_POST
  imposta(valori, tempo) {
    for (const k in valori) {
      const u = this.matStato.uniforms[nomeUniform(k)] || this.matFinitura.uniforms[nomeUniform(k)];
      if (u) u.value = valori[k];
    }
    this.comuni.uTempo.value = tempo;
  }

  // palette dello show { grad: [chiaro, medio, scuro] } (stringhe CSS)
  tinte(pal) {
    if (!pal || pal === this._pal) return;
    this._pal = pal;
    const u = this.matFinitura.uniforms;
    u.uT0.value.set(pal.grad[0]); u.uT1.value.set(pal.grad[1]); u.uT2.value.set(pal.grad[2]);
  }

  accendi(b) {
    if (b && !this.enabled) this.daPulire = true;   // niente fantasmi di minuti fa al riaccendersi
    this.enabled = b;
  }

  setSize(w, h) {
    for (const rt of this.stato) rt.setSize(w, h);
    this.comuni.uRis.value.set(w, h);
    this.daPulire = true;
  }

  render(renderer, writeBuffer, readBuffer) {
    const prec = this.stato[this.cur], nuovo = this.stato[1 - this.cur];
    if (this.daPulire) {
      // il primo giro parte dall'immagine attuale, non dal nero
      for (const rt of this.stato) { renderer.setRenderTarget(rt); renderer.clear(); }
      this.daPulire = false;
    }
    this.matStato.uniforms.tDiffuse.value = readBuffer.texture;
    this.matStato.uniforms.tPrec.value = prec.texture;
    renderer.setRenderTarget(nuovo);
    this.quadStato.render(renderer);
    this.matFinitura.uniforms.tStato.value = nuovo.texture;
    renderer.setRenderTarget(this.renderToScreen ? null : writeBuffer);
    this.quadFinitura.render(renderer);
    this.cur = 1 - this.cur;
  }

  dispose() {
    for (const rt of this.stato) rt.dispose();
    this.matStato.dispose(); this.matFinitura.dispose();
    this.quadStato.dispose(); this.quadFinitura.dispose();
  }
}
