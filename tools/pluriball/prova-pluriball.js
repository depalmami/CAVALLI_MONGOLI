// La barra PLURIBALL: un rotolo messo sulla strada davanti al giocatore, il pilota automatico lo prende, la barra sale di
// 30 e la bolla avvolge il protagonista; i colpi consumano prima la barra, la bolla scoppia a barra vuota.
// uso: NODE_PATH=<cartella con puppeteer-core>/node_modules node tools/pluriball/prova-pluriball.js <cartella foto>   (server su 127.0.0.1:8902)
const puppeteer = require('puppeteer-core');
const OUT = (process.argv[2] || __dirname) + '/', pausa = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--window-size=1500,1100', '--use-angle=metal', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage(); await page.setViewport({ width: 1500, height: 1100 });
  const errori = [];
  page.on('console', m => { const t = m.text(); if ((m.type() === 'error' && !/404/.test(t)) || /Pluriball/.test(t)) errori.push(m.type() + ': ' + t.slice(0, 200)); });
  page.on('pageerror', e => errori.push('PAGEERROR: ' + String(e).slice(0, 300)));
  await page.goto('http://127.0.0.1:8902/horse-racing-3d.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.cm3d && cm3d.game.state === 'briefing' && cm3d.pluriball.pronto, { timeout: 90000 });
  const gioco = await page.$('#gioco');
  await page.evaluate(() => cm3d.setMode('model'));
  const leggi = () => page.evaluate(() => ({ scudo: +cm3d.pluriball.scudo.toFixed(1), bolla: cm3d.pluriball.guscio.visible, op: +cm3d.pluriball.guscio.material.opacity.toFixed(2),
    vita: Math.round(cm3d.pHealth), game: cm3d.game.state, rotoli: cm3d.pluriball.rotoli.filter(r => r.gr.visible).length }));
  await page.click('#b-go'); await page.keyboard.press('o');
  await pausa(2500);
  console.log('prima del rotolo', JSON.stringify(await leggi()));
  // metto il rotolo 22000 unità davanti, sulla corsia del giocatore: il pilota lo prende
  const piazza = () => page.evaluate(() => { const r = cm3d.pluriball.rotoli[0]; r.active = true; r.preso = -1; r.pos = (cm3d.gapTo(0) * -1 + 22000 + cm3d.TRACK_LENGTH) % cm3d.TRACK_LENGTH; r.lat = cm3d.playerX; return r.pos; });
  await piazza();
  let foto = 0;
  for (let i = 0; i < 30; i++) {
    await pausa(250); const s = await leggi();
    if (s.scudo > 0) { if (!foto) { await pausa(600); await gioco.screenshot({ path: OUT + 'pl-barra.png' }); foto = 1; } break; }
  }
  const dopo = await leggi(); console.log('dopo il rotolo ', JSON.stringify(dopo));
  const r1 = await page.evaluate(() => { const p = cm3d.assorbiScudo(20); return { passa: p, scudo: +cm3d.pluriball.scudo.toFixed(1) }; });
  await pausa(300); await gioco.screenshot({ path: OUT + 'pl-colpo.png' });
  const r2 = await page.evaluate(() => { const p = cm3d.assorbiScudo(30); return { passa: p, scudo: +cm3d.pluriball.scudo.toFixed(1) }; });
  await pausa(150); await gioco.screenshot({ path: OUT + 'pl-scoppio.png' });
  await pausa(600);
  const r3 = await page.evaluate(() => { const p = cm3d.assorbiScudo(10); return { passa: p, bolla: cm3d.pluriball.guscio.visible }; });
  console.log('colpo 20 ->', JSON.stringify(r1), '· colpo 30 ->', JSON.stringify(r2), '· colpo 10 a barra vuota ->', JSON.stringify(r3));
  console.log('--- errori (' + errori.length + ')'); errori.slice(0, 8).forEach(e => console.log(e));
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
