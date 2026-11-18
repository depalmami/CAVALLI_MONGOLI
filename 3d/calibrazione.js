// CALIBRAZIONE DEL PROIETTORE/LEDWALL — una correzione di SATURAZIONE sull'immagine finale, per adattarla al
// device di uscita della serata (un ledwall economico spesso stampa i colori più slavati di un proiettore vero,
// o viceversa). NON è un effetto dello show: a differenza del post di 3d/smarmella.js, che a SMARMELLA 0 si spegne
// del tutto, questa correzione resta attiva SEMPRE, SMARMELLA 0 compreso — è una proprietà della sala, non della
// musica. Va per questo DOPO tutta la pipeline (anche dopo smarmella), sull'immagine che finisce davvero in
// proiezione.
//
// Stessa formula di 3d/smarmella.js (mix fra il grigio-luma e il colore, clampato a 0): a 1 è un passthrough.
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

const SHADER = {
  uniforms: { tDiffuse: { value: null }, uSaturazione: { value: 1 } },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse;
    uniform float uSaturazione;
    varying vec2 vUv;
    void main() {
      vec4 t = texture2D(tDiffuse, vUv);
      float l = dot(t.rgb, vec3(0.2126, 0.7152, 0.0722));
      gl_FragColor = vec4(max(mix(vec3(l), t.rgb, uSaturazione), 0.0), t.a);
    }
  `,
};

export function creaCalibrazione() {
  const pass = new ShaderPass(SHADER);
  pass.enabled = false;        // a 1.0 (neutro) il passaggio si salta del tutto: costa zero quando non serve
  return {
    pass,
    setSaturazione(v) {
      pass.uniforms.uSaturazione.value = v;
      pass.enabled = Math.abs(v - 1) > 1e-3;
    },
  };
}
