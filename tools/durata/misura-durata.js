// Quanto dura il viaggio: tempo di caricamento, lunghezza del tracciato, distanza minima fra tratti non vicini (il
// tracciato non deve avvicinarsi a se stesso) e, per le tappe chieste, il tempo VERO che ci mette il pilota automatico
// confrontato col tempo «a tutta» (distanza / velocità massima).
// uso: NODE_PATH=<cartella con puppeteer-core>/node_modules node tools/durata/misura-durata.js [tappe, es. 0,5] [boss]
//      (server su 127.0.0.1:8902). Le tappe si contano da 0; «boss» corre anche il livello bonus.
const puppeteer = require('puppeteer-core');
const tappe = (process.argv[2] || '').split(',').filter(Boolean).map(Number);
const conBoss = process.argv.includes('boss');
const pausa = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new',
    protocolTimeout: 0, args: ['--window-size=1280,800', '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1280, height: 800 });
  const errori = [];
  page.on('console', m => { if (m.type() === 'error' && !/404/.test(m.text())) errori.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  const t0 = Date.now();
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.game.state === 'briefing', { timeout: 300000 });
  const carica = (Date.now() - t0) / 1000;
  const info = await page.evaluate(() => {
    const V = cm3d.MAX_SPEED, P = cm3d.pts, passo = 5, CELLA = 40000, griglia = new Map();
    // distanza minima fra punti della pista lontani almeno 2000 segmenti lungo il percorso
    let min = Infinity;
    for (let i = 0; i < P.length; i += passo) {
      const p = P[i], cx = Math.floor(p.x / CELLA), cz = Math.floor(p.z / CELLA);
      for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (const j of griglia.get((cx + a) + ',' + (cz + b)) || []) {
        if (i - j < 2000) continue; const q = P[j]; min = Math.min(min, Math.hypot(p.x - q.x, p.z - q.z));
      }
      const k = cx + ',' + cz; if (!griglia.has(k)) griglia.set(k, []); griglia.get(k).push(i);
    }
    const tappe = cm3d.TAPPE.map((t, i) => { const e = cm3d.eventFor(i); return [i + 1, t.nome, e.type, Math.round(e.dist / V), Math.round(e.time)]; });
    let zMax = 0; for (const p of P) zMax = Math.max(zMax, Math.abs(p.z));
    return { N: cm3d.N, km: +(cm3d.FINE_VIAGGIO * 200 / 3.6 / 12000 / 1000).toFixed(1), aTutta: Math.round(cm3d.FINE_VIAGGIO / V), minDistanza: min === Infinity ? '>40000' : Math.round(min), zMax: Math.round(zMax),
             tappe, boss: Math.round((cm3d.BOSS_TRATTO.fine - cm3d.BOSS_TRATTO.inizio) / V), vitaBoss: cm3d.BOSS.vita };
  });
  console.log('caricamento', carica.toFixed(1), 's');
  console.log(JSON.stringify(info));
  await page.click('#b-go').catch(() => {});
  await pausa(500);
  const corri = async (avvia, nome, tutta) => {
    await page.evaluate(avvia);
    await page.evaluate(() => { cm3d.setPilota(true); window.__fps = 0; window.__t0 = performance.now(); if (!window.__conta) { window.__conta = 1; const f = () => { window.__fps++; requestAnimationFrame(f); }; f(); } });
    let s;
    for (;;) {
      await pausa(2000);
      s = await page.evaluate(() => ({ stato: cm3d.game.state, sec: (performance.now() - __t0) / 1000, fps: __fps / ((performance.now() - __t0) / 1000),
        pct: Math.round(100 * cm3d.game.dist / cm3d.game.target), kills: cm3d.game.killsThisEvent, vitaBoss: cm3d.boss.vita }));
      if (s.stato !== 'racing' && s.stato !== 'bonus') break;   // 'bonus' è la pausa per la scelta: il pilota sceglie da solo
    }
    console.log(nome, '-> esito', s.stato, '· vero', s.sec.toFixed(0), 's · a tutta', tutta, 's · rapporto', (s.sec / tutta).toFixed(2),
      '· fps', s.fps.toFixed(0), '· abbattuti', s.kills, conBoss ? '· vita boss ' + (s.vitaBoss * 100).toFixed(0) + '%' : '');
  };
  for (const i of tappe) await corri(new Function(`cm3d.game.eventIndex = ${i}; cm3d.startEvent();`), 'tappa ' + (i + 1), info.tappe[i][3]);
  if (conBoss) await corri(() => cm3d.startBoss(), 'boss', info.boss);
  console.log('--- errori (' + errori.length + ')'); errori.slice(0, 8).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
