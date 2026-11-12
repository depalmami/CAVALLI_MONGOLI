// Il sorpasso: il Boss passa davanti, fa dietrofront, corre all'indietro e morde di fronte. Una foto ogni mezzo secondo.
// uso: node t-sorpasso.js [para|schiva|fermo]
const puppeteer = require('puppeteer-core');
const MODO = process.argv[2] || 'fermo';
const OUT = __dirname + '/', pausa = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--window-size=1500,1100', '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1500, height: 1100 });
  const errori = [];
  page.on('console', m => { if (m.type() === 'error' && !/404/.test(m.text())) errori.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html?boss=1', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.boss.pronto && cm3d.game.state === 'racing', { timeout: 90000 });
  const gioco = await page.$('#gioco');
  // guida semplice: gas, tiene una corsia; secondo il modo para o cambia corsia quando il Boss annuncia il morso di fronte
  await page.evaluate(modo => {
    const tasto = (k, giu) => dispatchEvent(new KeyboardEvent(giu ? 'keydown' : 'keyup', { key: k, bubbles: true }));
    const st = { sx: false, dx: false, i: false }; tasto('ArrowUp', true);
    let corsia = 0.5;
    setInterval(() => {
      if (cm3d.game.state !== 'racing') return;
      const b = cm3d.boss, px = cm3d.playerX, av = b.avviso;
      if (!b.diFronte && b.stato.piano.tipo !== 'giro') corsia = b.o.lat <= 0 ? 0.6 : -0.6;
      if (modo === 'schiva' && av && av.lato === 0 && av.quanto > 0.62) corsia = b.o.lat > 0 ? b.o.lat - 0.75 : b.o.lat + 0.75;
      const e = corsia - px, sx = e < -0.05, dx = e > 0.05;
      if (sx !== st.sx) { tasto('ArrowLeft', sx); st.sx = sx; }
      if (dx !== st.dx) { tasto('ArrowRight', dx); st.dx = dx; }
      const para = modo === 'para' && !!(av && av.parabile);
      if (para !== st.i) { tasto('i', para); st.i = para; }
    }, 40);
  }, MODO);
  await page.waitForFunction(() => cm3d.boss.o.state === 'race', { timeout: 30000 });
  await pausa(2500);
  await page.evaluate(() => cm3d.boss.prova('sorpasso'));
  const leggi = () => page.evaluate(() => { const b = cm3d.boss, s = b.stato; return { piano: s.piano.tipo, verso: s.verso, giro: s.giro, gap: Math.round(cm3d.gapTo(b.o.pos)), lat: +b.o.lat.toFixed(2),
    att: s.att && (s.att.tipo + '/' + s.att.stadio), morsi: s.morsi, bocca: s.apertura, px: +cm3d.playerX.toFixed(2), hp: Math.round(cm3d.pHealth), vBoss: Math.round(b.o.speed), stord: b.stordito }; });
  for (let i = 0; i < 44; i++) {
    const s = await leggi();
    if (i % 2 === 0) console.log(((i * 0.4).toFixed(1) + 's').padStart(6), JSON.stringify(s));
    await gioco.screenshot({ path: OUT + 'sorp-' + MODO + '-' + String(i).padStart(2, '0') + '.png' });
    await pausa(330);
  }
  console.log('--- errori (' + errori.length + ')'); errori.slice(0, 8).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
