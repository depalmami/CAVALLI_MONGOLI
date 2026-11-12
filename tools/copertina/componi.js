// Le bozze della copertina: titoli (tools/copertina/bozze.html) sopra le scene scattate dal gioco (scatta.js).
// uso:  python3 tools/server-sviluppo.py 8902 &   poi   node tools/copertina/componi.js
const puppeteer = require('puppeteer-core');
const path = require('path'), fs = require('fs');
const OUT = path.join(__dirname, 'bozze'); fs.mkdirSync(OUT, { recursive: true });
const BOZZE = [                                   // [file, stile, scena]
  ['A-cabinato-tramonto', 'cabinato', 'tramonto-eroico'],
  ['A-cabinato-notte',    'cabinato', 'notte-eroico'],
  ['B-arco-alba',         'arco',     'alba-eroico'],
  ['C-bandiera-tramonto', 'bandiera', 'tramonto-fianco'],
];
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new' });
  const page = await browser.newPage(); await page.setViewport({ width: 1920, height: 1080 });
  for (const [nome, stile, scena] of BOZZE) {
    await page.goto(`http://127.0.0.1:8902/tools/copertina/bozze.html?stile=${stile}&scena=${scena}`);
    await page.waitForFunction(() => window.pronto, { timeout: 20000 });
    await page.screenshot({ path: path.join(OUT, nome + '.jpg'), type: 'jpeg', quality: 92 });
    console.log('fatto', nome);
  }
  await browser.close();
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
