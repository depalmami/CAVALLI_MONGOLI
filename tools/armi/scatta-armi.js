// Foto dell'arma in mano: pose fisse della camera attorno alla mano del protagonista. Non tocca il gioco.
// uso:  python3 tools/server-sviluppo.py 8902 &   poi   node tools/armi/scatta-armi.js <cartella> [armi] [viste] [colpi]
//       armi: whip,mace,saber,bow · viste: mano,lato,fronte,alto,dietro · colpi: c oppure c:dir (c = fase del colpo -0.35…1, dir = 1 destra, -1 sinistra)
const puppeteer = require('puppeteer-core');
const OUT = require('path').resolve(process.argv[2] || __dirname + '/scatti'); require('fs').mkdirSync(OUT, { recursive: true });
const  armi = (process.argv[3] || 'saber').split(','), viste = (process.argv[4] || 'mano').split(','), cs = (process.argv[5] || '0,1:1,1:-1').split(',').map(x => { const [c, d] = x.split(':'); return { c: +c, dir: d == null ? (+c >= 0 ? 1 : -1) : +d }; });
const pausa = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--window-size=1100,800','--use-angle=metal','--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1100, height: 800 });
  const err = [];
  page.on('console', m => { const t = m.text(); if ((m.type() === 'error' && !/404/.test(t)) || /Arma|Armi/.test(t)) err.push(m.type() + ': ' + t.slice(0, 200)); });
  page.on('pageerror', e => err.push('PAGEERROR: ' + String(e).slice(0, 300)));
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.player && cm3d.player.model, { timeout: 90000 });
  await page.addStyleTag({ content: `#gioco { position: fixed !important; left: 0; top: 0; width: 1100px !important; max-width: none !important; z-index: 99999; } #gioco > *:not(#scene) { visibility: hidden !important; } body { overflow: hidden; }` });
  await page.evaluate(() => {
    dispatchEvent(new Event('resize'));
    cm3d.setMode('model'); cm3d.setFreeRoam(true);
    const cam = cm3d.camera, P = cm3d.player; let scena = P.group; while (scena.parent) scena = scena.parent;
    const orig = scena.updateMatrixWorld.bind(scena); const v = new (cm3d.camera.position.constructor)();
    window.__posa = null; window.__c = null;
    scena.updateMatrixWorld = function (f) {
      const s = window.__posa;
      if (window.__c != null) { P.swingC = window.__c; P.swingDir = window.__dir; cm3d.armi.aggiorna(P, cm3d.curWeapon.key); }
      if (s) {
        cm3d.armi.radice.updateWorldMatrix(true, false); cm3d.armi.radice.getWorldPosition(v);
        const h = P.heading, fx = Math.sin(h), fz = Math.cos(h), rx = -Math.cos(h), rz = Math.sin(h);
        cam.position.set(v.x + fx*s.F + rx*s.R, v.y + s.H, v.z + fz*s.F + rz*s.R); cam.up.set(0,1,0);
        cam.lookAt(v.x + fx*s.tF + rx*s.tR, v.y + s.tH, v.z + fz*s.tF + rz*s.tR); cam.fov = s.fov; cam.updateProjectionMatrix();
      }
      return orig(f);
    };
  });
  const VISTE = { mano: { F: 250, R: 1500, H: 120, tF: 150, tR: 0, tH: 120, fov: 38 }, lato: { F: 0, R: 3200, H: 150, tF: 0, tR: 0, tH: -300, fov: 40 },
                  fronte: { F: 2600, R: 1500, H: 200, tF: 0, tR: 0, tH: -200, fov: 42 }, dietro: { F: -2800, R: 0, H: 600, tF: 300, tR: 0, tH: 100, fov: 38 }, alto: { F: 300, R: 700, H: 2400, tF: 0, tR: 0, tH: -300, fov: 40 } };
  for (const a of armi) {
    await page.evaluate(k => cm3d.equipWeapon(k), a); await pausa(400);
    for (const vn of viste) {
      await page.evaluate(s => { window.__posa = s; }, VISTE[vn]);
      for (const c of cs) {
        await page.evaluate(q => { window.__c = q.c; window.__dir = q.c === 0 ? 0 : q.dir; }, c);
        await pausa(250);
        await page.screenshot({ path: `${OUT}/${a}-${vn}-c${c.c}d${c.dir}.png` });
      }
    }
  }
  const info = await page.evaluate(() => ({ agganciata: cm3d.armi.agganciata, chiave: cm3d.armi.chiave, figli: cm3d.armi.arma.children.length }));
  console.log(JSON.stringify(info)); console.log('--- errori (' + err.length + ')'); err.slice(0, 8).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
