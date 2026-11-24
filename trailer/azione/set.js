// SET DI RIPRESA del trailer: il gioco vero in Chrome senza interfaccia, in verticale 1080×1920, con il TEMPO VIRTUALE.
// performance.now e requestAnimationFrame sono sostituiti prima che parta la pagina: finché si gira in «tempo reale»
// seguono l'orologio vero (caricamento, partenza), poi `passo(dt)` fa avanzare il gioco di dt secondi esatti e si
// fotografa. Niente scatti, niente frame persi, e il rallentatore è gratis (dt = 1/120 → 4× a 30 fps).
// Non tocca il gioco: tutto passa da window.cm3d e da un aggancio a scene.updateMatrixWorld (camere in posa).
// Serve: server statico sulla cartella del progetto (python3 tools/server-sviluppo.py 8903) e puppeteer-core
// installato a parte (NODE_PATH=<cartella>/node_modules).
const puppeteer = require('puppeteer-core');
const fs = require('fs'), path = require('path');

const W = 1080, H = 1920;
const PORTA = process.env.PORTA || 8903;
const pausa = ms => new Promise(r => setTimeout(r, ms));

// l'orologio virtuale: iniettato prima di ogni script della pagina
function orologio() {
  const rNow = performance.now.bind(performance), rRAF = window.requestAnimationFrame.bind(window);
  let passo = false, vt = 0, off = 0, cbs = [];
  const pend = new Set();        // richieste fatte in tempo reale e non ancora servite: all'ingresso nel passo passano in coda
  const reale = cb => { pend.add(cb); rRAF(() => { if (pend.delete(cb)) cb(performance.now()); }); };
  performance.now = () => passo ? vt : rNow() + off;
  window.requestAnimationFrame = cb => {
    if (!passo) { reale(cb); return 1; }
    cbs.push(cb); return cbs.length;
  };
  window.__clk = {
    entra() { if (!passo) { vt = rNow() + off; passo = true; cbs.push(...pend); pend.clear(); } },
    esci() { if (passo) { off = vt - rNow(); passo = false; const l = cbs; cbs = []; l.forEach(reale); } },
    passo(dt) {
      vt += dt * 1000;
      if (window.__regia) try { window.__regia(dt); } catch (e) { console.error('regia', e); }
      const l = cbs; cbs = []; l.forEach(cb => cb(vt));
    },
    get t() { return vt / 1000; },
  };
}

// le camere in posa e i pezzi di scena: dentro la pagina, una volta sola
function preparaScena() {
  const cam = cm3d.camera, P = cm3d.player;
  let scena = P.group; while (scena.parent) scena = scena.parent;
  window.__scena = scena;
  const V = (x = 0, y = 0, z = 0) => new P.basePos.constructor(x, y, z);
  const orig = scena.updateMatrixWorld.bind(scena);
  const tmpA = V(), tmpB = V();
  // posa = { F, R, H, tF, tR, tH, fov, roll, su: 'giocatore'|'boss'|oggetto3D }: in unità di gioco attorno all'ancora,
  // F avanti, R a destra, H in alto (lungo la direzione del cavallo). Con `a` e `b` la camera va da una posa all'altra
  // in `dur` secondi (carrellata), con `t` = tempo dall'inizio della ripresa.
  const mescola = (a, b, k) => { const o = {}; for (const c in a) o[c] = typeof a[c] === 'number' && typeof b[c] === 'number' ? a[c] + (b[c] - a[c]) * k : a[c]; return o; };
  const dolce = k => { k = Math.max(0, Math.min(1, k)); return k * k * (3 - 2 * k); };
  window.__cam = null;            // { a, b, dur, t0, curva } oppure null (camera del gioco)
  window.__fovGioco = null;       // per la camera del gioco: fov fisso al posto di quello di velocità
  scena.updateMatrixWorld = function (f) {
    if (window.__inScena) try { window.__inScena(__clk.t); } catch (e) { console.error('inScena', e); }
    const c = window.__cam;
    if (c) {
      const k = c.b ? (c.lineare ? Math.max(0, Math.min(1, (__clk.t - c.t0) / c.dur)) : dolce((__clk.t - c.t0) / c.dur)) : 0;
      const s = c.b ? mescola(c.a, c.b, k) : c.a;
      let p = P.basePos, h = P.heading;
      if (s.su === 'boss') { const t = scena.getObjectByName('Testa'); if (t) { p = t.getWorldPosition(tmpB); } }
      else if (s.su && s.su.isObject3D) p = s.su.getWorldPosition(tmpB);
      else if (typeof s.su === 'number') { const o = cm3d.opponents[s.su]; if (o && o.actor) p = o.actor.group.position; }
      const fx = Math.sin(h), fz = Math.cos(h), rx = -Math.cos(h), rz = Math.sin(h);
      const sx = s.scuoti ? (Math.random() - 0.5) * s.scuoti : 0, sy = s.scuoti ? (Math.random() - 0.5) * s.scuoti : 0;
      cam.position.set(p.x + fx * s.F + rx * s.R + sx, p.y + s.H + sy, p.z + fz * s.F + rz * s.R);
      cam.up.set(0, 1, 0);
      cam.lookAt(p.x + fx * s.tF + rx * s.tR, p.y + s.tH, p.z + fz * s.tF + rz * s.tR);
      if (s.roll) cam.rotateZ(s.roll);
      cam.fov = s.fov; cam.updateProjectionMatrix();
    } else if (window.__fovGioco) { cam.fov += window.__fovGioco; cam.updateProjectionMatrix(); }
    return orig(f);
  };
  // guida minima: tiene il cavallo su una corsia (senza, in curva scivola fuori e rallenta)
  const tasto = (k, giu) => dispatchEvent(new KeyboardEvent(giu ? 'keydown' : 'keyup', { key: k, bubbles: true }));
  const st = { sx: false, dx: false };
  window.__tasto = tasto;
  window.__guida = corsia => {
    const e = corsia - cm3d.playerX, sx = e < -0.04, dx = e > 0.04;
    if (sx !== st.sx) { tasto('ArrowLeft', sx); st.sx = sx; }
    if (dx !== st.dx) { tasto('ArrowRight', dx); st.dx = dx; }
  };
  // un rivale messo in scena accanto al giocatore: g = distanza lungo pista (+ davanti), lat = corsia
  window.__rivale = (i, g, lat, vita = 200) => {
    const o = cm3d.opponents[i]; if (!o) return null;
    const L = cm3d.TRACK_LENGTH, qui = (((-cm3d.gapTo(0)) % L) + L) % L;
    o.state = 'race'; o.actor.rimettiInPiedi(); o.actor.group.visible = true;
    o.pos = o.prevPos = (((qui + g) % L) + L) % L; o.lat = o.prevLat = o.targetLat = lat; o.spintaLat = 0;
    o.speed = cm3d.speed; o.health = o.hp0 = vita; o.atkCd = 99; o.wipeT = 0;
    return o;
  };
  window.__qui = () => { const L = cm3d.TRACK_LENGTH; return (((-cm3d.gapTo(0)) % L) + L) % L; };
}

async function apri({ boss = false, hud = 'nessuno', log = false } = {}) {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new',
    args: [`--window-size=${W},${H}`, '--use-angle=metal', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  const errori = [];
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  page.on('console', m => { if (m.type() === 'error') errori.push(m.text().slice(0, 200)); if (log) console.log('  [pagina]', m.text().slice(0, 200)); });
  await page.evaluateOnNewDocument(orologio);
  await page.goto(`http://127.0.0.1:${PORTA}/horse-racing-3d.html${boss ? '?boss=1' : ''}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(b => window.cm3d && cm3d.player && cm3d.armi && (b ? cm3d.boss.pronto && cm3d.game.state === 'racing' : cm3d.pannello || cm3d.game.state === 'racing'),
    { timeout: 120000, polling: 250 }, boss);
  // solo la scena e le due tele dell'HUD, accese o spente a comando (sovrimpressioni)
  await page.addStyleTag({ content: `
    #gioco { position: fixed !important; left: 0 !important; top: 0 !important; width: ${W}px !important; height: ${H}px !important;
             max-width: none !important; z-index: 99999; border-radius: 0 !important; }
    #gioco > *:not(#scene):not(#combat-overlay):not(#hud-overlay) { visibility: hidden !important; }
    body { overflow: hidden !important; margin: 0; }` });
  await page.evaluate((W, H) => {
    const sel = document.getElementById('proj-res');
    const o = document.createElement('option'); o.value = `${W}x${H}`; o.textContent = 'trailer'; sel.appendChild(o);
    sel.value = o.value; sel.dispatchEvent(new Event('change'));
    cm3d.setMode('model');
  }, W, H);
  if (!boss) await page.evaluate(() => { cm3d.scegliPannello(); cm3d.scegliPannello(); });   // titoli: NUOVO VIAGGIO, poi VIA!
  await page.waitForFunction(() => cm3d.game.state === 'racing', { timeout: 30000 });
  await page.evaluate(preparaScena);
  await sovrimpressioni(page, hud);
  return { browser, page, errori };
}

// quali tele dell'HUD si vedono: 'nessuno' | 'combattimento' (barre dei rivali, scritte dei colpi) | 'tutto'
async function sovrimpressioni(page, hud) {
  await page.evaluate(hud => {
    const v = (id, on) => { const e = document.getElementById(id); if (e) e.style.visibility = on ? 'visible' : 'hidden'; };
    v('combat-overlay', hud !== 'nessuno'); v('hud-overlay', hud === 'tutto');
  }, hud);
}

// gira `sec` secondi di gioco a passi di dt e salva i fotogrammi in `cartella` (jpg); `ogni` = scatta un passo su N
async function gira(page, cartella, sec, { dt = 1 / 60, ogni = 1, prima = null, qualita = 93 } = {}) {
  fs.mkdirSync(cartella, { recursive: true });
  for (const f of fs.readdirSync(cartella)) if (f.endsWith('.jpg')) fs.unlinkSync(path.join(cartella, f));
  await page.evaluate(() => __clk.entra());
  const n = Math.round(sec / dt);
  let k = 0;
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(dt => __clk.passo(dt), dt);
    if (prima) await prima(i);
    if (i % ogni === 0) await page.screenshot({ path: path.join(cartella, String(k++).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: qualita });
  }
  return { fotogrammi: k, secondi: ((Date.now() - t0) / 1000).toFixed(1) };
}

// avanza senza fotografare (per portare la scena al punto giusto)
async function avanza(page, sec, dt = 1 / 60) {
  await page.evaluate((sec, dt) => { __clk.entra(); const n = Math.round(sec / dt); for (let i = 0; i < n; i++) __clk.passo(dt); }, sec, dt);
}

module.exports = { apri, gira, avanza, sovrimpressioni, pausa, W, H };
