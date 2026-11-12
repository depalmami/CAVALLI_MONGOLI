// Scene pulite per la copertina: il gioco vero, senza HUD, con gli attori e la camera messi in posa «da locandina».
// Non tocca il gioco. Si entra nel livello del Boss, si ferma la sua testa (boss.passo a vuoto) e a ogni fotogramma,
// agganciati a scene.updateMatrixWorld (la prima cosa del disegno), si piazzano camera, coccodrillo e birra.
// uso:  python3 tools/server-sviluppo.py 8902 &   poi   node tools/copertina/scatta.js [cartella] [larghezza] [tappe] [pose]
//       tappe e pose: nomi separati da virgola (vedi TAPPE_FOTO e POSE), oppure «tutte»
const puppeteer = require('puppeteer-core');
const fs = require('fs'), path = require('path');
const OUT = path.resolve(process.argv[2] || path.join(__dirname, 'scatti'));
const LARG = +(process.argv[3] || 1920), ALT = Math.round(LARG * 9 / 16);
const pausa = ms => new Promise(r => setTimeout(r, ms));
fs.mkdirSync(OUT, { recursive: true });

// dove si scatta: indice della tappa (decide luce e paesaggio) e a che punto della tappa (0…1)
const TAPPE_FOTO = { alba: [0, 0.45], steppa: [3, 0.4], dune: [5, 0.5], tramonto: [9, 0.45], notte: [11, 0.4] };

// Pose, in unità di gioco rispetto al cavallo: F avanti, R a destra, H in alto; t* = dove guarda la camera.
// boss: { g, lat, bocca } = il collo a g dal cavallo (negativo = dietro), corsia, bocca 0…1.  birra: { av, lat }.
const POSE = {
  // il cavallo ci corre incontro fra la birra e il coccodrillo che gli spalanca le fauci alle spalle
  locandina: { F: 3100, R: 150, H: 430, tF: -1500, tR: 0, tH: 1150, fov: 42, boss: { g: -5200, lat: -0.55, bocca: 0.6 }, birra: { av: -1400, lat: 0.75 } },
  // da terra, verso il cielo: tanto cielo sopra per il titolo
  eroico:    { F: 2500, R: -300, H: 160, tF: -900, tR: 100, tH: 1550, fov: 56, boss: { g: -4700, lat: -0.55, bocca: 0.7 }, birra: { av: -1200, lat: 0.80 } },
  // dall'alto: tutta la parata lungo la strada
  parata:    { F: 5600, R: -1900, H: 2100, tF: -3500, tR: 300, tH: 600, fov: 44, boss: { g: -4800, lat: -0.40, bocca: 0.6 }, birra: { av: 2600, lat: 0.45 } },
  // dal bordo della strada: il coccodrillo di sbieco, col profilo del logo
  fianco:    { F: 1900, R: 2500, H: 520, tF: -2600, tR: -1300, tH: 1150, fov: 48, boss: { g: -3600, lat: -0.55, bocca: 0.6 }, birra: { av: -2600, lat: 0.30 } },
};
const scelti = (arg, tutti) => !arg || arg === 'tutte' ? Object.keys(tutti) : arg.split(',').filter(n => tutti[n]);
const tappe = scelti(process.argv[4], TAPPE_FOTO), pose = scelti(process.argv[5], POSE);

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new',
    args: [`--window-size=${LARG},${ALT + 200}`, '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: LARG, height: ALT + 200 });
  const errori = [];
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html?boss=1', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.birra.pronto && cm3d.boss.pronto && cm3d.game.state === 'racing', { timeout: 90000 });

  // l'anteprima a tutta finestra, solo la scena: via HUD, schermate, scritte
  await page.addStyleTag({ content: `
    #gioco { position: fixed !important; left: 0; top: 0; width: ${LARG}px !important; max-width: none !important; z-index: 99999; }
    #gioco > *:not(#scene) { visibility: hidden !important; }
    body { overflow: hidden; }` });
  await page.evaluate(() => {
    dispatchEvent(new Event('resize'));
    cm3d.setMode('model');                                   // il protagonista è il cavallo di cartone con le gambe
    dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true }));   // gas a fondo, niente pilota (pararebbe: l'anello azzurro)
    const cam = cm3d.camera, P = cm3d.player, B = cm3d.boss, L = cm3d.TRACK_LENGTH;
    B.passo = () => {};                                      // il Boss non decide più niente: lo si mette in posa
    let scena = P.group; while (scena.parent) scena = scena.parent;
    const orig = scena.updateMatrixWorld.bind(scena);        // la scena si aggiorna per prima: qui le pose valgono già per questo fotogramma
    // guida minima: tiene il cavallo in mezzo alla strada (senza, in curva scivola fuori e rallenta)
    const tasto = (k, giu) => dispatchEvent(new KeyboardEvent(giu ? 'keydown' : 'keyup', { key: k, bubbles: true }));
    const st = { sx: false, dx: false };
    setInterval(() => { const e = -cm3d.playerX, sx = e < -0.04, dx = e > 0.04;
      if (sx !== st.sx) { tasto('ArrowLeft', sx); st.sx = sx; } if (dx !== st.dx) { tasto('ArrowRight', dx); st.dx = dx; } }, 30);
    const bic = scena.getObjectByName('Bicchiere'), ps = scena.getObjectByName('PattinoS'), pd = scena.getObjectByName('PattinoD');
    let birra = bic; while (birra && birra.parent !== scena) birra = birra.parent;
    const mascella = scena.getObjectByName('Mascella');
    const V = P.basePos.clone(); let fase = 0;
    window.__posa = null;
    scena.updateMatrixWorld = function (f) {
      const s = window.__posa;
      if (s) {
        const qui = (((-cm3d.gapTo(0)) % L) + L) % L;        // dove sta il cavallo lungo la pista
        const p = P.basePos, h = P.heading, fx = Math.sin(h), fz = Math.cos(h), rx = -Math.cos(h), rz = Math.sin(h);
        cam.position.set(p.x + fx * s.F + rx * s.R, p.y + s.H, p.z + fz * s.F + rz * s.R);
        cam.up.set(0, 1, 0);
        cam.lookAt(p.x + fx * s.tF + rx * s.tR, p.y + s.tH, p.z + fz * s.tF + rz * s.tR);
        cam.fov = s.fov; cam.updateProjectionMatrix();
        for (const o of cm3d.opponents) if (!o.boss && o.actor && o.actor.group) o.actor.group.visible = false;   // niente scorta
        // il coccodrillo: collo a g dal cavallo, corre alla sua velocità, bocca in posa (vale dal fotogramma dopo)
        const o = B.o; o.state = 'race'; o.verso = 1; o.speed = cm3d.speed;
        o.pos = o.prevPos = (((qui + s.boss.g) % L) + L) % L; o.lat = o.prevLat = o.targetLat = s.boss.lat;
        if (mascella) mascella.rotation.z = -0.5 * s.boss.bocca;
        if (birra) {
          birra.visible = !!s.birra;
          if (s.birra) {                                     // il bicchiere pattina davanti al cavallo, nella sua corsia
            cm3d.posToWorld(qui + s.birra.av, s.birra.lat, V);
            birra.position.copy(V); birra.scale.setScalar(1);
            birra.rotation.order = 'YZX'; birra.rotation.set(0, Math.atan2(-fz, fx), 0);
            fase += 0.12; const sn = Math.sin(fase), c = Math.cos(fase);
            if (ps && pd) { ps.rotation.z = 0.2 * sn + 0.12 * Math.max(0, c); pd.rotation.z = -0.2 * sn + 0.12 * Math.max(0, -c); }
            bic.rotation.set(0.05 * sn, 0.06 * c, -0.09);
          }
        }
      }
      return orig(f);
    };
  });

  const scena = await page.$('#scene');
  let n = 0;
  for (const t of tappe) {
    const [k, u] = TAPPE_FOTO[t];
    await page.evaluate((k, u, posa) => {
      const a = cm3d.tappaInizio[k], b = k + 1 < cm3d.tappaInizio.length ? cm3d.tappaInizio[k + 1] : cm3d.FINE_VIAGGIO;
      cm3d.teleport(a + (b - a) * u, 0); window.__posa = posa;
    }, k, u, POSE[pose[0]]);
    await pausa(6500);                                       // riprende velocità, la polvere si alza, la luce si assesta
    for (const nome of pose) {
      await page.evaluate(p => { window.__posa = p; }, POSE[nome]);
      for (let i = 0; i < 2; i++) {
        await pausa(i ? 260 : 700);
        await scena.screenshot({ path: path.join(OUT, `${t}-${nome}-${i}.png`) }); n++;
      }
    }
    const st = await page.evaluate(() => ({ kmh: Math.round(cm3d.speed / 60), hp: Math.round(cm3d.pHealth), stato: cm3d.game.state, px: +cm3d.playerX.toFixed(2), modo: cm3d.renderMode }));
    console.log(t.padEnd(10), JSON.stringify(st));
  }
  console.log(n, 'scatti in', OUT, '· errori:', errori.length); errori.slice(0, 6).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
