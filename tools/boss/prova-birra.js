// La Birra Grande: compare, pattina, si acchiappa (col pilota automatico), dà velocità e meno danno, poi finisce.
const puppeteer = require('puppeteer-core');
const OUT = __dirname + '/', pausa = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--window-size=1500,1100', '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1500, height: 1100 });
  const errori = [];
  page.on('console', m => { const t = m.text(); if ((m.type() === 'error' && !/404/.test(t)) || /Birra/.test(t)) errori.push(m.type() + ': ' + t.slice(0, 200)); });
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html?birra=1', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.game.state === 'briefing' && cm3d.birra.pronto, { timeout: 90000 });
  const gioco = await page.$('#gioco');
  const leggi = () => page.evaluate(() => { const d = cm3d.birra.dati; return { stato: d.stato, gap: Math.round(cm3d.gapTo(d.pos)), lat: +d.lat.toFixed(2), vB: Math.round(d.speed), effetto: +d.effetto.toFixed(1),
    quando: d.quando === Infinity ? 'mai' : Math.round(d.quando), dist: Math.round(cm3d.game.dist), px: +cm3d.playerX.toFixed(2), kmh: Math.round(cm3d.speed / 60), hp: Math.round(cm3d.pHealth), game: cm3d.game.state }; });
  console.log('avvio            ', JSON.stringify(await leggi()));
  await page.click('#b-go'); await page.keyboard.press('o');
  let preso = false, n = 0, fotoAvvista = false, fotoPreso = false, kmhMax = 0, fine = false;
  for (let i = 0; i < 90 && !fine; i++) {
    await pausa(500);
    const s = await leggi(); kmhMax = Math.max(kmhMax, s.kmh);
    if (i % 4 === 0 || s.stato === 'preso') console.log(((i * 0.5).toFixed(1) + 's').padStart(6), JSON.stringify(s));
    if (s.stato === 'pattina' && s.gap < 30000 && !fotoAvvista) { await gioco.screenshot({ path: OUT + 'birra-1-vista.png' }); fotoAvvista = true; }
    if (s.stato === 'pattina' && s.gap < 9000 && s.gap > 0) await gioco.screenshot({ path: OUT + 'birra-2-vicina.png' });
    if (s.effetto > 0 && !preso) { preso = true; await gioco.screenshot({ path: OUT + 'birra-3-preso.png' }); }
    if (preso && s.effetto > 0 && !fotoPreso && s.effetto < 12) { fotoPreso = true; await gioco.screenshot({ path: OUT + 'birra-4-effetto.png' }); }
    if (preso && s.effetto === 0) fine = true;
  }
  // il danno: assorbiScudo(100) con e senza effetto
  const danni = await page.evaluate(() => { const r = {}; cm3d.pScudo = 0; r.senza = cm3d.assorbiScudo(100); return r; });
  console.log('presa:', preso, '· velocità massima vista:', kmhMax, 'km/h · danno su 100 a effetto finito:', danni.senza);
  await page.evaluate(() => { cm3d.birra.dati; });
  console.log('--- errori (' + errori.length + ')'); errori.slice(0, 8).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
