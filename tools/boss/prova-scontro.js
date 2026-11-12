// PROVA DELLO SCONTRO COL BOSS in un browser senza interfaccia.
// Serve: un server statico sulla cartella del progetto (python3 -m http.server 8902 --bind 127.0.0.1) e puppeteer-core
// (npm i puppeteer-core in una cartella a parte, poi NODE_PATH=<quella cartella>/node_modules node tools/boss/prova-scontro.js pilota 200).
// Modi: pilota (guida il pilota automatico) · bravo (para e schiva; non sceglie i bonus, quindi si ferma al menu) · fermo (non schiva).
// Scontro "vero": un giocatore-prova tiene una corsia, mena quando il Boss è a tiro, para il morso e (se MODO=bravo)
// schiva coda e carica. Si registra come va e si fotografa il gioco ogni pochi secondi.
// uso: node t-boss2.js [bravo|fermo|pilota] [secondi]
const puppeteer = require('puppeteer-core');
const MODO = process.argv[2] || 'bravo', SEC = +(process.argv[3] || 60);
const OUT = __dirname + '/', pausa = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--window-size=1500,1100', '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1500, height: 1100, deviceScaleFactor: 1 });
  const errori = [];
  page.on('console', m => { if (m.type() === 'error') errori.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  page.on('requestfailed', r => errori.push('rete: ' + r.url().slice(-60)));
  page.on('response', r => { if (r.status() === 404) errori.push('404: ' + r.url().slice(-70)); });
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html?boss=1', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.boss && cm3d.boss.pronto && cm3d.game.state === 'racing', { timeout: 90000 });
  const gioco = await page.$('#gioco');

  await page.evaluate(modo => {
    const tasto = (k, giu) => dispatchEvent(new KeyboardEvent(giu ? 'keydown' : 'keyup', { key: k, bubbles: true }));
    const st = { sx: false, dx: false, i: false, presi: 0, hp0: cm3d.pHealth, log: [] };
    window.__prova = st;
    if (modo === 'pilota') { tasto('o', true); tasto('o', false); return; }
    tasto('ArrowUp', true);
    let corsia = 0.55, tAtk = 0;
    setInterval(() => {
      if (cm3d.game.state !== 'racing') return;
      const b = cm3d.boss, o = b.o, px = cm3d.playerX, g = cm3d.gapTo(o.pos), av = b.avviso;
      // la corsia: accanto al Boss, dal lato libero più largo
      let voglio = o.lat <= 0 ? Math.min(0.85, o.lat + 0.85) : Math.max(-0.85, o.lat - 0.85);
      if (modo === 'bravo' && av && !av.parabile) {
        if (av.testo === 'CODA') voglio = o.lat + (px >= o.lat ? 1.45 : -1.45);                     // mi allargo: la frustata arriva a 1,3
        else voglio = px >= o.lat ? 0.99 : -0.99;                                                    // carica: mi stringo al bordo
      }
      corsia = voglio;
      const e = corsia - px, sx = e < -0.05, dx = e > 0.05;
      if (sx !== st.sx) { tasto('ArrowLeft', sx); st.sx = sx; }
      if (dx !== st.dx) { tasto('ArrowRight', dx); st.dx = dx; }
      // para il morso e, come farebbe chiunque, i predoni che ha addosso
      const addosso = cm3d.opponents.some(r => r.state === 'race' && Math.abs(cm3d.gapTo(r.pos)) < cm3d.ATK_RANGE * 1.1 && Math.abs(r.lat - px) < cm3d.LAT_RANGE * 1.1);
      const para = !!(av && av.parabile) || (modo !== 'fermo' && addosso);
      if (para !== st.i) { tasto('i', para); st.i = para; }
      tAtk -= 0.05;
      if (tAtk <= 0 && b.attaccabile && b.aTiro(g, o.lat - px, 0, cm3d.LAT_RANGE, false)) {
        const k = o.lat < px ? 'j' : 'l'; tasto(k, true); tasto(k, false); tAtk = 0.3;
      }
    }, 50);
  }, MODO);

  const leggi = () => page.evaluate(() => { const b = cm3d.boss; return {
    stato: b.o.state, gap: Math.round(cm3d.gapTo(b.o.pos)), lat: +b.o.lat.toFixed(2), vita: Math.round(b.o.health), fase: b.fase,
    att: b.stato.att && (b.stato.att.tipo + '/' + b.stato.att.stadio), piano: b.stato.piano.tipo,
    px: +cm3d.playerX.toFixed(2), kmh: Math.round(cm3d.speed / 60), hp: Math.round(cm3d.pHealth), scudo: Math.round(cm3d.pScudo),
    game: cm3d.game.state, kills: cm3d.kills, pct: Math.round(100 * cm3d.game.dist / cm3d.game.target), rivali: cm3d.opponents.filter(o => o.state !== 'fuori').length }; });
  const t0 = Date.now();
  let n = 0, ultimo = null;
  while ((Date.now() - t0) / 1000 < SEC) {
    await pausa(2500);
    const s = await leggi(); ultimo = s;
    const t = ((Date.now() - t0) / 1000).toFixed(0).padStart(3);
    console.log(t + 's', JSON.stringify(s));
    if (n % 2 === 0) await gioco.screenshot({ path: OUT + MODO + '-' + String(n / 2).padStart(2, '0') + '.png' });
    n++;
    if (s.game !== 'racing' && s.game !== 'bonus') { await pausa(800); await gioco.screenshot({ path: OUT + MODO + '-fine.png' }); break; }
  }
  console.log('ESITO', MODO, ultimo.game, 'vita boss', ultimo.vita, 'hp', ultimo.hp, 'tratto', ultimo.pct + '%');
  console.log('--- errori (' + errori.length + ')'); [...new Set(errori)].slice(0, 10).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
