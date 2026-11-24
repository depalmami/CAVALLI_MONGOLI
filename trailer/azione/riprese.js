// LE RIPRESE del trailer d'azione (storia IG 1080×1920): ogni inquadratura è una scena del gioco vero, messa in scena
// e girata a tempo virtuale da set.js. Le pose di camera sono in unità di gioco attorno al cavallo (o alla testa del Boss):
// F avanti, R a destra, H in alto; tF/tR/tH = dove guarda. `a` → `b` = carrellata nella durata della ripresa.
// uso: NODE_PATH=<puppeteer>/node_modules node trailer/azione/riprese.js <cartella> [nomi,separati|tutte] [--foto]
//      --foto: tre scatti per ripresa (inizio, metà, fine) per tarare le pose senza girare tutto
const path = require('path');
const { apri, gira, avanza, sovrimpressioni } = require('./set.js');

const OUT = path.resolve(process.argv[2] || 'riprese');
const SCELTE = (process.argv[3] && process.argv[3] !== 'tutte') ? process.argv[3].split(',') : null;
const FOTO = process.argv.includes('--foto');

// tappe: alba 0, steppa 3, dune 5, tramonto 9, notte 11 (decidono luce e paesaggio)
const RIPRESE = [
  // misure (unità di gioco, attorno ai piedi del cavallo): il cavallo di cartone è F −770…720, R −265…350, H 0…1540,
  // la testa sta a F ~550, H ~1350. Una corsia: lat 1 = R 3000 (lat + = a destra). In verticale il campo orizzontale è
  // stretto: hfov = 2·atan(0,5625·tan(fov/2)) → fov 60 ≈ 36°. Boss (attorno all'origine di «Testa», il collo): muso a
  // F +3970, bocca H 1400…2200, cima della testa H 3200, larga ±670; il corpo va indietro fino a F −12400.
  // ── ATTO 1: la tensione ───────────────────────────────────────────────────────────────────────────────────
  { nome: 'a1_testa_notte', tappa: [11, 0.42], dt: 1 / 120, dur: 2.6, hud: 'nessuno',
    cam: { a: { F: 2300, R: -800, H: 1000, tF: 500, tR: 0, tH: 1100, fov: 42 }, b: { F: 1800, R: -620, H: 1020, tF: 500, tR: 0, tH: 1100, fov: 40 } } },
  { nome: 'a2_alba_galoppo', tappa: [0, 0.45], dt: 1 / 120, dur: 2.6, hud: 'nessuno',
    cam: { a: { F: 3000, R: 350, H: 120, tF: 0, tR: 0, tH: 1000, fov: 52 }, b: { F: 2200, R: 200, H: 220, tF: 0, tR: 0, tH: 1000, fov: 50 } } },
  { nome: 'a3_rivali_tramonto', tappa: [9, 0.45], dt: 1 / 60, dur: 3.0, hud: 'nessuno', corsia: 0,
    rivali: [{ i: 0, g: 1300, lat: 0.55 }, { i: 1, g: -500, lat: -0.55 }, { i: 2, g: 3300, lat: -0.15 }, { i: 3, g: 5200, lat: 0.4 }],
    cam: { a: { F: -3000, R: -600, H: 1500, tF: 2200, tR: 200, tH: 500, fov: 60 }, b: { F: -3600, R: -500, H: 3000, tF: 2600, tR: 200, tH: 0, fov: 60 } } },
  { nome: 'a4_sciabola_alzata', tappa: [9, 0.6], dt: 1 / 120, dur: 2.2, hud: 'nessuno', arma: 'saber',
    eventi: [[0.9, 'cm3d.playerAttack(-1)']],
    cam: { a: { F: 2400, R: 250, H: 160, tF: 0, tR: 0, tH: 1150, fov: 50 }, b: { F: 1700, R: 120, H: 260, tF: 0, tR: 0, tH: 1200, fov: 48 } } },

  // ── ATTO 2: l'azione ──────────────────────────────────────────────────────────────────────────────────────
  { nome: 'b1_frusta', tappa: [3, 0.4], dt: 1 / 60, dur: 2.4, hud: 'nessuno', arma: 'whip', corsia: -0.05,
    rivali: [{ i: 0, g: 0, lat: 0.55, vita: 400, fissa: true, molla: true }],
    eventi: [[0.5, 'cm3d.playerAttack(1)'], [1.3, 'cm3d.playerAttack(1)']],
    cam: { a: { F: -2300, R: -700, H: 2000, tF: 500, tR: 900, tH: 700, fov: 62 }, b: { F: -1900, R: -600, H: 1800, tF: 500, tR: 900, tH: 700, fov: 60 } } },
  { nome: 'b2_mazza', tappa: [3, 0.55], dt: 1 / 120, dur: 2.0, hud: 'nessuno', arma: 'mace', corsia: 0.05,
    rivali: [{ i: 0, g: 0, lat: -0.55, vita: 400, fissa: true, molla: true }],
    eventi: [[0.7, 'cm3d.playerAttack(-1)']],
    cam: { a: { F: 2700, R: 1300, H: 650, tF: 0, tR: -800, tH: 1000, fov: 60 }, b: { F: 2400, R: 1150, H: 700, tF: 0, tR: -800, tH: 1000, fov: 58 } } },
  { nome: 'b3_calcio', tappa: [5, 0.5], dt: 1 / 120, dur: 2.6, hud: 'nessuno', corsia: 0,
    rivali: [{ i: 0, g: 0, lat: 0.5, vita: 5, fissa: true }],
    eventi: [[0.6, 'cm3d.playerKick()']],
    cam: { a: { F: 2600, R: 1200, H: 2600, tF: 0, tR: 750, tH: 500, fov: 66 }, b: { F: 2400, R: 1500, H: 2400, tF: -200, tR: 1000, tH: 500, fov: 66 } } },
  { nome: 'b4_arco', tappa: [9, 0.3], dt: 1 / 60, dur: 2.4, hud: 'nessuno', arma: 'bow', corsia: -0.1,
    rivali: [{ i: 0, g: 4200, lat: 0.35, vita: 400, fissa: true, molla: true }],
    eventi: [[0.3, 'cm3d.playerAttack(1)'], [1.05, 'cm3d.playerAttack(1)'], [1.8, 'cm3d.playerAttack(1)']],
    cam: { a: { F: -1600, R: 350, H: 1500, tF: 4200, tR: 1050, tH: 500, fov: 48 }, b: { F: -1400, R: 350, H: 1450, tF: 4200, tR: 1050, tH: 600, fov: 40 } } },
  { nome: 'b5_sciabola_colpo', tappa: [9, 0.7], dt: 1 / 120, dur: 2.2, hud: 'nessuno', arma: 'saber', corsia: -0.05,
    rivali: [{ i: 0, g: 0, lat: 0.55, vita: 400, fissa: true, molla: true }],
    eventi: [[0.7, 'cm3d.playerAttack(1)']],
    cam: { a: { F: 3800, R: 2600, H: 700, tF: 0, tR: 850, tH: 950, fov: 60 }, b: { F: 3300, R: 2400, H: 750, tF: 0, tR: 850, tH: 950, fov: 56 } } },
  // la mischia: due rivali ai lati che attaccano, il cavallo frusta a destra e a sinistra e scalcia (niente HUD)
  { nome: 'b6_mischia', tappa: [5, 0.25], dt: 1 / 60, dur: 3.0, hud: 'nessuno', arma: 'whip', corsia: 0,
    rivali: [{ i: 0, g: 150, lat: 0.45, vita: 900, fissa: true, molla: true, attacca: true }, { i: 1, g: -150, lat: -0.45, vita: 900, fissa: true, molla: true, attacca: true }],
    eventi: [[0.35, 'cm3d.playerAttack(1)'], [0.85, 'cm3d.playerAttack(-1)'], [1.35, 'cm3d.playerAttack(1)'], [1.8, 'cm3d.playerKick()'], [2.3, 'cm3d.playerAttack(-1)'], [2.7, 'cm3d.playerAttack(1)']],
    cam: { a: { F: 4600, R: 250, H: 1150, tF: 0, tR: 0, tH: 800, fov: 60 }, b: { F: 3900, R: 150, H: 1050, tF: 0, tR: 0, tH: 820, fov: 60 } } },
  { nome: 'b7_notte_branco', tappa: [11, 0.6], dt: 1 / 60, dur: 3.0, hud: 'nessuno', corsia: 0,
    rivali: [{ i: 0, g: -1500, lat: -0.5 }, { i: 1, g: 900, lat: 0.55 }, { i: 2, g: -3500, lat: 0.2 }, { i: 3, g: 2200, lat: -0.35 }],
    cam: { a: { F: 4800, R: 900, H: 3200, tF: -1000, tR: 0, tH: 300, fov: 55 }, b: { F: 3600, R: 600, H: 2400, tF: -1000, tR: 0, tH: 300, fov: 55 } } },
  { nome: 'b8_frusta_retro', tappa: [11, 0.3], dt: 1 / 60, dur: 2.0, hud: 'nessuno', arma: 'whip', corsia: 0.05,
    rivali: [{ i: 0, g: 0, lat: -0.55, vita: 400, fissa: true, molla: true }],
    eventi: [[0.4, 'cm3d.playerAttack(-1)'], [1.1, 'cm3d.playerAttack(-1)']],
    cam: { a: { F: 2600, R: 200, H: 1100, tF: 0, tR: -800, tH: 1000, fov: 62 }, b: { F: 2300, R: 150, H: 1100, tF: 0, tR: -800, tH: 1000, fov: 60 } } },

  // ── ATTO 3: il Boss, a pezzi (niente spoiler: mai intero) ─────────────────────────────────────────────────
  { nome: 'c1_fauci', boss: true, tappa: [11, 0.4], dt: 1 / 120, dur: 2.4, hud: 'nessuno',
    bossPosa: { g: [-5200, -5200], lat: -0.4, bocca: 'Math.min(1, Math.max(0, (t - 0.3) / 1.6))' },
    cam: { a: { su: 'boss', F: 6600, R: 900, H: 1500, tF: 3300, tR: 0, tH: 1850, fov: 40 }, b: { su: 'boss', F: 5700, R: 700, H: 1550, tF: 3300, tR: 0, tH: 1850, fov: 38 } } },
  { nome: 'c2_gambe', boss: true, tappa: [11, 0.5], dt: 1 / 60, dur: 2.0, hud: 'nessuno',
    bossPosa: { g: [-5200, -5200], lat: -0.4, bocca: '0.15' },
    cam: { a: { su: 'boss', F: 300, R: 1800, H: 160, tF: -1000, tR: 0, tH: 500, fov: 52 }, b: { su: 'boss', F: -2600, R: 1800, H: 160, tF: -3900, tR: 0, tH: 500, fov: 52 } } },
  { nome: 'c3_incombe', boss: true, tappa: [9, 0.5], dt: 1 / 60, dur: 3.0, hud: 'nessuno',
    bossPosa: { g: [-6400, -4300], lat: -0.5, bocca: '0.35 + 0.35 * Math.sin(t * 7)' },
    cam: { a: { F: 3300, R: 200, H: 380, tF: -1500, tR: -100, tH: 1150, fov: 44 }, b: { F: 2800, R: 120, H: 420, tF: -1500, tR: -100, tH: 1150, fov: 42 } } },
  { nome: 'c4_morso', boss: true, tappa: [11, 0.55], dt: 1 / 60, dur: 2.0, hud: 'nessuno', scuoti: 60,
    bossPosa: { g: [-7000, -3000], lat: 0, bocca: 'Math.min(1, t / 1.2)', curva: 'accelera' },
    cam: { a: { F: 2600, R: -250, H: 650, tF: -2500, tR: 0, tH: 900, fov: 46 }, b: { F: 2600, R: -250, H: 650, tF: -2500, tR: 0, tH: 900, fov: 46 } } },
  { nome: 'c5_scatto_fauci', boss: true, tappa: [11, 0.65], dt: 1 / 120, dur: 1.2, hud: 'nessuno',
    bossPosa: { g: [-5200, -5200], lat: -0.4, bocca: 't < 0.45 ? 1 : Math.max(0, 1 - (t - 0.45) / 0.12)' },
    cam: { a: { su: 'boss', F: 5900, R: 350, H: 1700, tF: 3200, tR: 0, tH: 1800, fov: 40 }, b: { su: 'boss', F: 5300, R: 250, H: 1750, tF: 3200, tR: 0, tH: 1800, fov: 40 } } },
];

// ── nella pagina: mette in scena una ripresa ─────────────────────────────────────────────────────────────────
function preparaRipresa(S) {
  const L = cm3d.TRACK_LENGTH;
  for (const o of cm3d.opponents) if (!o.boss) { o.state = 'fuori'; o.actor.rimettiInPiedi(); o.actor.group.visible = false; }
  cm3d.game.prossimoRivale = 1e15;                 // nessun rivale nuovo da solo: in scena ci sono solo quelli messi qui
  cm3d.game.target = 1e15; cm3d.game.dist = 0;     // la tappa non finisce mai durante le riprese
  cm3d.setPilota(!!S.pilota);
  const [k, u] = S.tappa;
  const a = cm3d.tappaInizio[k], b = k + 1 < cm3d.tappaInizio.length ? cm3d.tappaInizio[k + 1] : cm3d.FINE_VIAGGIO;
  cm3d.teleport(a + (b - a) * u, S.corsia || 0);
  cm3d.equipWeapon(S.arma || 'fists');
  __tasto('ArrowUp', !S.pilota);
  window.__fovGioco = S.fovGioco || null;
  window.__cam = null;
  window.__S = null;
  for (const p of cm3d.pickups) { p.active = false; p.respawnT = 1e9; p.mesh.visible = false; }   // niente casse: l'arma è quella scelta
  window.__pulisci = () => { cm3d.pluriball.azzera(); cm3d.kills = 0; cm3d.pHealth = Math.max(cm3d.pHealth, 80); if (cm3d.scelta) cm3d.confermaScelta(); };
  window.__regia = () => { if (!S.pilota) __guida(S.corsia || 0); __pulisci(); };
  if (S.boss) {
    const B = cm3d.boss; B.passo = () => {};       // il Boss non decide più niente: lo si mette in posa
    for (const o of cm3d.opponents) if (!o.boss && o.actor && o.actor.group) o.actor.group.visible = false;
  }
}

function avviaRipresa(S, prova) {
  const L = cm3d.TRACK_LENGTH, T0 = __clk.t;
  const fatti = new Set();
  cm3d.equipWeapon(S.arma || 'fists');
  for (const r of S.rivali || []) __rivale(r.i, r.g, r.lat, r.vita || 200);
  const rival = (S.rivali || []).map(r => ({ r, o: cm3d.opponents[r.i] }));
  const scena = window.__scena, mascella = scena.getObjectByName('Mascella');
  const bocca = S.bossPosa ? new Function('t', 'return ' + S.bossPosa.bocca) : null;
  window.__S = { ...S, T0 };
  window.__regia = dt => {
    const t = __clk.t - T0;
    if (!S.pilota) __guida(S.corsia || 0);
    __pulisci();
    for (const { r, o } of rival) {
      if (!o || o.state !== 'race') continue;
      o.laneCd = 99; if (!r.attacca) o.atkCd = 99;
      if (r.fissa) {                                // resta accanto: stessa velocità, distanza fissa (la molla lo riporta in corsia)
        o.pos = (((__qui() + r.g) % L) + L) % L; o.speed = cm3d.speed;
        if (r.molla) { o.targetLat = r.lat; o.lat += (r.lat - o.lat) * 0.2; }
      }
    }
    if (!prova) (S.eventi || []).forEach(([te, code], k) => { if (t >= te && !fatti.has(k)) { fatti.add(k); new Function(code)(); } });
  };
  // il Boss in posa: collo a g dal cavallo, corsia, bocca; si aggancia al disegno (scene.updateMatrixWorld)
  window.__inScena = S.bossPosa ? (tAss => {
    const t = tAss - T0, P = S.bossPosa, o = cm3d.boss.o;
    let k = Math.max(0, Math.min(1, t / S.dur));
    k = P.curva === 'accelera' ? k * k * k : k * k * (3 - 2 * k);
    const g = P.g[0] + (P.g[1] - P.g[0]) * k;
    o.state = 'race'; o.verso = 1; o.speed = cm3d.speed;
    o.pos = o.prevPos = (((__qui() + g) % L) + L) % L; o.lat = o.prevLat = o.targetLat = P.lat;
    if (mascella) mascella.rotation.z = -0.5 * Math.max(0, Math.min(1, bocca(t)));
    for (const r of cm3d.opponents) if (!r.boss && r.actor && r.actor.group) r.actor.group.visible = false;   // niente scorta
  }) : null;
  window.__cam = S.cam ? { ...S.cam, a: { ...S.cam.a, scuoti: S.scuoti || 0 }, b: S.cam.b && { ...S.cam.b, scuoti: S.scuoti || 0 }, dur: S.dur, t0: T0 } : null;
}

(async () => {
  const lista = RIPRESE.filter(r => !SCELTE || SCELTE.includes(r.nome));
  let set = null, modo = null;
  for (const S of lista) {
    const vuole = S.boss ? 'boss' : 'corsa';
    if (modo !== vuole) {                            // corsa e Boss: due pagine diverse (?boss=1)
      if (set) await set.browser.close();
      set = await apri({ boss: !!S.boss }); modo = vuole;
    }
    const { page } = set;
    await sovrimpressioni(page, S.hud || 'nessuno');
    await page.evaluate(preparaRipresa, S);
    await page.evaluate(avviaRipresa, S, true);       // in posa già durante il riscaldamento, ma senza colpi
    await avanza(page, S.riscaldo || 6.5);           // riprende velocità, la polvere si alza, la luce si assesta
    await page.evaluate(avviaRipresa, S, false);
    const cartella = path.join(OUT, S.nome);
    const n = Math.round(S.dur / S.dt);
    if (FOTO) {
      const fs = require('fs'); fs.mkdirSync(OUT, { recursive: true });
      const scatti = [0, Math.floor(n / 2), n - 1];
      for (let i = 0; i < n; i++) {
        await page.evaluate(dt => __clk.passo(dt), S.dt);
        const j = scatti.indexOf(i);
        if (j >= 0) await page.screenshot({ path: path.join(OUT, `${S.nome}-${j}.jpg`), type: 'jpeg', quality: 80 });
      }
      console.log('foto', S.nome);
    } else {
      const r = await gira(page, cartella, S.dur, { dt: S.dt });
      console.log(S.nome.padEnd(22), r.fotogrammi, 'fotogrammi in', r.secondi, 's');
    }
    const st = await page.evaluate(() => ({ kmh: Math.round(cm3d.speed / 60), px: +cm3d.playerX.toFixed(2), arma: cm3d.curWeapon.key, kills: cm3d.kills,
      riv: cm3d.opponents.filter(o => !o.boss && o.state !== 'fuori').map(o => o.state + ':' + Math.round(o.health) + '@' + o.lat.toFixed(2)).join(' ') }));
    console.log('   ', JSON.stringify(st));
  }
  if (set) { console.log('errori pagina:', set.errori.filter(e => !/404/.test(e)).slice(0, 5)); await set.browser.close(); }
})().catch(e => { console.error('FALLITO', e); process.exit(1); });
