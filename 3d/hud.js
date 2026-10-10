// HUD — stile CABINATO (scelto il 3 ottobre 2026 fra le tre bozze della Fase 3).
//
// Il cruscotto da sala giochi dell'HUD 2D portato nel 3D: tutto in Press Start 2P,
// riquadri neri con bordo bianco spesso e ombra a scalino senza sfocatura, blocchi
// al posto delle barre. È UNA tela sola, e va in proiezione: i vecchi pannelli
// erano DOM e al secondo schermo non arrivavano mai.
//
// Il modulo non sa niente del gioco: disegna da uno STATO che il gioco gli passa
// a ogni frame (vedi statoHud() nella pagina). Così si prova anche fuori dal gioco.
//
// Tre modi: GIOCO (tutto), SHOW (tempo, sezione, smarmella, banner: per il
// concerto col pilota automatico), PULITO (niente).
//
// Costi: ogni scritta con contorno e ombra costa 10 fillText. Si disegna UNA volta
// in una tela a parte e poi si copia: nel 2D lo shadowBlur per frame del testo
// laterale era il collo di bottiglia, qui non si ripete l'errore.
// Il font vendorato è il sottoinsieme latino di base (4,7 KB): niente accenti né
// simboli, quindi ogni testo passa da ascii().

const FONT = '"Press Start 2P", monospace';
// TAVOLOZZA: i colori della bandiera mongola, un po' scuriti (9 ott 2026) — blu per i riquadri, rosso e il
// giallo del Soyombo per i dettagli. Tutto l'HUD e il menu dei bonus la usano; le schermate DOM la ripetono nel CSS.
const MN_BLU = '#082c6b', MN_BLU_SCURO = '#041737', MN_ROSSO = '#a51f27', MN_ORO = '#dcb200';
const GIALLO = '#e3b505', ROSSO = '#c0262e', CIANO = '#5b95ea', BIANCO = '#ffffff', SPENTO = '#1c2a52', GRIGIO = '#8fa0c8';
const FONDO = 'rgba(4,23,55,.9)';                 // il pieno dei riquadri: blu notte

// solo ASCII stampabile: accenti tolti, simboli sostituiti
export function ascii(s) {
  return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[·•]/g, '-').replace(/[×]/g, 'x').replace(/[→›»]/g, '>').replace(/[‹«]/g, '<')
    .replace(/[’‘]/g, "'").replace(/[^\x20-\x7e]/g, '').toUpperCase();
}

export function creaHud(cv) {
  const ctx = cv.getContext('2d');
  let modo = 'gioco';
  let fontPronto = false;
  const cache = new Map();
  // la tela non chiede i font da sola: senza questa richiesta i primi frame
  // uscirebbero in monospace, e la cache se li terrebbe per sempre
  if (document.fonts && document.fonts.load) {
    document.fonts.load('16px ' + FONT).then(() => { fontPronto = true; cache.clear(); }, () => { fontPronto = true; });
  } else fontPronto = true;

  // ── scritte pre-disegnate ───────────────────────────────────────────────
  function glifo(s, size, colore) {
    const k = size + '|' + colore + '|' + s;
    let g = cache.get(k);
    if (g) return g;
    if (cache.size > 600) cache.clear();
    const o = Math.max(1, Math.round(size / 8)), pad = o * 3;
    const m = document.createElement('canvas').getContext('2d');
    m.font = size + 'px ' + FONT;
    const w = Math.ceil(m.measureText(s).width);
    const c = document.createElement('canvas');
    c.width = Math.max(1, w + pad * 2); c.height = size + pad * 2;
    const x = c.getContext('2d');
    x.font = size + 'px ' + FONT; x.textBaseline = 'top'; x.textAlign = 'left';
    x.fillStyle = '#000';
    x.fillText(s, pad + o * 2, pad + o * 2);                                   // ombra a scalino
    for (const [dx, dy] of [[-o, 0], [o, 0], [0, -o], [0, o], [-o, -o], [o, o], [-o, o], [o, -o]]) x.fillText(s, pad + dx, pad + dy);
    x.fillStyle = colore; x.fillText(s, pad, pad);
    g = { c, w, pad };
    if (fontPronto) cache.set(k, g);
    return g;
  }
  const larg = (s, size) => glifo(s, size, BIANCO).w;
  function testo(s, x, y, size, colore, allinea = 'left') {
    if (!s) return 0;
    const g = glifo(s, size, colore);
    const dx = allinea === 'right' ? -g.w : allinea === 'center' ? -g.w / 2 : 0;
    ctx.drawImage(g.c, Math.round(x + dx - g.pad), Math.round(y - g.pad));
    return g.w;
  }
  function scatola(x, y, w, h, u) {
    x = Math.round(x); y = Math.round(y); w = Math.round(w); h = Math.round(h);
    const o = Math.max(2, Math.round(5 * u)), b = Math.max(2, Math.round(3 * u));
    ctx.fillStyle = '#000'; ctx.fillRect(x + o, y + o, w, h);
    ctx.fillStyle = FONDO; ctx.fillRect(x, y, w, h);
    // testata come nel menu dei bonus: una striscia rossa con il filo giallo sotto
    const t = Math.max(3, Math.round(7 * u)), f = Math.max(1, Math.round(2 * u));
    ctx.fillStyle = MN_ROSSO; ctx.fillRect(x, y, w, t);
    ctx.fillStyle = MN_ORO; ctx.fillRect(x, y + t, w, f);
    ctx.strokeStyle = BIANCO; ctx.lineWidth = b; ctx.strokeRect(x + b / 2, y + b / 2, w - b, h - b);
  }
  function blocchi(x, y, n, pieni, lato, gap, colore, vuoto = SPENTO) {
    for (let i = 0; i < n; i++) {
      ctx.fillStyle = i < pieni ? colore : vuoto;
      ctx.fillRect(Math.round(x + i * (lato + gap)), Math.round(y), lato, lato);
    }
    return n * (lato + gap) - gap;
  }
  // etichette dei rivali vicini: si impilano invece di sovrapporsi
  function separa(rivali, W, H, lx, ly) {
    const fatte = [];
    for (const r of [...rivali].sort((a, b) => b.y - a.y)) {
      const x = r.x * W; let y = r.y * H;
      while (fatte.some(f => Math.abs(f.x - x) < lx && Math.abs(f.y - y) < ly)) y -= ly;
      fatte.push({ r, x, y });
    }
    return fatte;
  }

  // ── eventi: banner, giudizio sul colpo, combo rotta ─────────────────────
  let banner = null, giudizio = null, rotta = 0;
  // NOTIFICHE (il takedown): frequenti, quindi non devono coprire la strada. Quattro modi di mostrarle, da scegliere:
  //   centro  · la fascia grande di prima (copre metà schermo)
  //   alto    · la stessa fascia ma sottile, appena sotto i riquadri in alto
  //   nastro  · una targhetta piccola al centro in alto, fra il pannello della tappa e il tachimetro
  //   lato    · un riquadro che entra da destra, sotto il tachimetro
  //   rivale  · niente fascia: la scritta salta fuori sopra il rivale abbattuto e sale svanendo
  let notifica = null, stileNotifica = 'rivale';      // scelto il 9 ott 2026
  function lanciaNotifica(t, sotto, pos) {
    if (stileNotifica === 'centro') return lanciaBanner(t, sotto, 1.9);
    notifica = { testo: ascii(t), sotto: ascii(sotto || ''), t0: ora(), durata: stileNotifica === 'rivale' ? 1.1 : 1.5, pos };
  }
  const ora = () => performance.now() / 1000;
  function lanciaBanner(t, sotto, durata = 1.9) { banner = { testo: ascii(t), sotto: ascii(sotto || ''), t0: ora(), durata }; }
  // il colpo è a tempo? scarto dal battito più vicino (la fase include già l'anticipo visivo)
  function colpo(musica) {
    const f = musica.fase, ms = Math.min(f, 1 - f) * musica.periodo * 1000;
    if (ms <= 70) giudizio = { testo: 'PERFETTO!', colore: GIALLO, t0: ora() };
    else if (ms <= 140) giudizio = { testo: 'BUONO', colore: BIANCO, t0: ora() };
    return ms;
  }

  // ── disegno ─────────────────────────────────────────────────────────────
  function disegna(S, W, H) {
    disegnaHud(S, W, H);
    if (S.scelta && fontPronto) disegnaScelta(S.scelta, S, W, H);   // il menu dei bonus si vede in ogni modo, anche PULITO
    else rettScelta = [];
  }

  // ── SCELTA DEL BONUS: a schermo, a 8 bit, nei colori della Mongolia ─────────
  // Sei caselle 3×2; quella scelta è rossa col bordo giallo e lampeggia a tempo. Le caselle non disponibili
  // (cura a vita piena, nitro pieno) sono spente. rettScelta tiene i rettangoli per il clic.
  let rettScelta = [];
  function disegnaScelta(C, S, W, H) {
    const u = H / 1080, px = n => Math.max(8, Math.round(n * u / 8) * 8);
    const T = { s: px(16), m: px(24), l: px(32), xl: px(48) };
    const lamp = S.musica.fase < 0.5, o = Math.max(2, Math.round(6 * u)), b = Math.max(2, Math.round(4 * u));
    ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, 0, W, H);
    const pw = Math.min(W * 0.86, 1500 * u), cols = 3, gap = Math.round(18 * u), pad = Math.round(28 * u);
    const cw = (pw - pad * 2 - gap * (cols - 1)) / cols, ch = Math.round(T.m + T.s * 2 + 58 * u);
    const testa = Math.round(T.xl + 40 * u), sotto = Math.round(T.s * 3 + 46 * u);
    const ph = testa + pad + 2 * ch + gap + sotto;
    const x0 = Math.round(W / 2 - pw / 2), y0 = Math.round(H / 2 - ph / 2);
    // pannello blu, bordo bianco, ombra a scalino
    ctx.fillStyle = '#000'; ctx.fillRect(x0 + o, y0 + o, pw, ph);
    ctx.fillStyle = MN_BLU; ctx.fillRect(x0, y0, pw, ph);
    ctx.fillStyle = MN_ROSSO; ctx.fillRect(x0, y0, pw, testa);                             // testata rossa
    ctx.fillStyle = MN_ORO; ctx.fillRect(x0, y0 + testa - b, pw, b);
    ctx.strokeStyle = BIANCO; ctx.lineWidth = b; ctx.strokeRect(x0 + b / 2, y0 + b / 2, pw - b, ph - b);
    testo(ascii(C.titolo), W / 2, y0 + (testa - T.xl) / 2, T.xl, lamp ? MN_ORO : BIANCO, 'center');
    rettScelta = [];
    C.opzioni.forEach((op, i) => {
      const cx = x0 + pad + (i % cols) * (cw + gap), cy = y0 + testa + pad + Math.floor(i / cols) * (ch + gap);
      const sel = i === C.indice, ok = op.ok;
      ctx.fillStyle = '#000'; ctx.fillRect(Math.round(cx + o), Math.round(cy + o), Math.round(cw), ch);
      ctx.fillStyle = !ok ? '#0d1530' : sel ? MN_ROSSO : MN_BLU_SCURO;
      ctx.fillRect(Math.round(cx), Math.round(cy), Math.round(cw), ch);
      ctx.strokeStyle = sel ? (lamp ? MN_ORO : BIANCO) : ok ? BIANCO : SPENTO; ctx.lineWidth = sel ? b * 1.6 : b;
      ctx.strokeRect(Math.round(cx) + b / 2, Math.round(cy) + b / 2, Math.round(cw) - b, ch - b);
      const ty = cy + Math.round(20 * u);
      testo(ascii(op.nome), cx + cw / 2, ty, T.m, ok ? (sel ? MN_ORO : BIANCO) : GRIGIO, 'center');
      testo(ascii(op.descr), cx + cw / 2, ty + T.m + Math.round(14 * u), T.s, ok ? (sel ? BIANCO : MN_ORO) : SPENTO, 'center');
      if (op.nota) testo(ascii(op.nota), cx + cw / 2, ty + T.m + T.s + Math.round(26 * u), T.s, ok ? GRIGIO : SPENTO, 'center');
      rettScelta.push({ x: cx / W, y: cy / H, w: cw / W, h: ch / H, i });
    });
    const ys = y0 + testa + pad + 2 * ch + gap + Math.round(24 * u);
    testo(ascii(C.sotto), W / 2, ys, T.s, MN_ORO, 'center');
    testo(ascii(C.aiuto), W / 2, ys + T.s + Math.round(18 * u), T.s, BIANCO, 'center');
  }
  // clic sulla tela (coordinate 0..1): quale casella
  function sceltaA(xn, yn) {
    const r = rettScelta.find(r => xn >= r.x && xn <= r.x + r.w && yn >= r.y && yn <= r.y + r.h);
    return r ? r.i : -1;
  }

  function disegnaHud(S, W, H) {
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.imageSmoothingEnabled = false;
    if (modo === 'pulito' || !fontPronto) return;
    if (modo === 'gioco' && !S.inGara) { if (banner) disegnaBanner(S, W, H, H / 1080); return; }

    const u = H / 1080, show = modo === 'show';
    const px = n => Math.max(8, Math.round(n * u / 8) * 8);      // il font a pixel solo a multipli di 8
    const T = { s: px(16), m: px(24), l: px(32), xl: px(64), xxl: px(96) };
    const M = Math.round(34 * u), pad = Math.max(8, Math.round(20 * u)), riga = T.s + Math.max(6, Math.round(14 * u));
    const mus = S.musica, lamp = mus.fase < 0.5;

    spettro(S, W, H, u, show);

    // ── rivali in vista e chi arriva da dietro ──
    // PRIMA dei riquadri: un'etichetta può passarci sotto, mai sopra
    if (!show) {
      const l = Math.max(4, Math.round(12 * u)), g = Math.max(1, Math.round(3 * u));
      for (const { r, x, y } of separa(S.rivali, W, H, larg('TEMUJIN', T.s) + 10 * u, T.s + l + 14 * u)) {
        const yy = y - l - 10 * u;
        if (r.ko && stileNotifica !== 'rivale') testo('KO', x, yy - T.s - 6 * u, T.s, GRIGIO, 'center');   // con lo stile «rivale» c'è già la scritta del takedown
        if (!r.ko) blocchi(x - (6 * l + 5 * g) / 2, yy, 6, Math.ceil(r.hp * 6), l, g, r.hp > 0.5 ? '#3fd66b' : r.hp > 0.25 ? GIALLO : ROSSO, '#000');
      }
      S.dietro.slice(0, 2).forEach((d, i) => {
        const sx = d.lato < 0, x = sx ? Math.round(14 * u) : W - Math.round(14 * u), y = H * 0.64 + i * (T.s + 30 * u), s = Math.max(6, Math.round(16 * u));   // sotto la combo, che sta a metà
        ctx.fillStyle = lamp ? GIALLO : BIANCO;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (sx ? s : -s), y - s); ctx.lineTo(x + (sx ? s : -s), y + s); ctx.closePath(); ctx.fill();
        testo(`${d.metri}M`, x + (sx ? 1 : -1) * (s + 10 * u), y - T.s / 2, T.s, BIANCO, sx ? 'left' : 'right');
      });
    }

    // ── viaggio e obiettivo (in alto a sinistra) ──
    {
      const r1 = `TAPPA ${String(S.tappa + 1).padStart(2, '0')}/${S.tappe}`, r2 = ascii(S.nomeTappa);
      const lato = Math.max(8, Math.round(22 * u)), gap = Math.max(2, Math.round(8 * u)), gr = Math.max(6, Math.round(14 * u));
      const km = S.km.toFixed(1) + 'KM', ob = show ? '' : ascii(S.obiettivo || ''), s2 = show ? T.s : T.m;
      const wQuad = S.tappe * (lato + gap) - gap + pad + larg(km, T.s);
      const w = Math.max(larg(r1, T.s), larg(r2, s2), show ? 0 : wQuad, larg(ob, T.s)) + pad * 2;
      // le righe dall'alto: [altezza, cosa disegnare]
      const righe = [[T.s, y => testo(r1, M + pad, y, T.s, GIALLO)], [s2, y => testo(r2, M + pad, y, s2, BIANCO)]];
      if (!show) righe.push([lato, y => {
        for (let i = 0; i < S.tappe; i++) {
          ctx.fillStyle = i < S.tappa ? GIALLO : i === S.tappa ? (lamp ? BIANCO : GIALLO) : SPENTO;
          ctx.fillRect(Math.round(M + pad + i * (lato + gap)), Math.round(y), lato, lato);
        }
        testo(km, M + w - pad, y + (lato - T.s) / 2, T.s, BIANCO, 'right');
      }]);
      if (ob) righe.push([T.s, y => testo(ob, M + pad, y, T.s, CIANO)]);
      const h = pad * 2 + righe.reduce((a, r) => a + r[0], 0) + gr * (righe.length - 1);
      scatola(M, M, w, h, u);
      let y = M + pad;
      for (const [alt, f] of righe) { f(y); y += alt + gr; }
    }

    if (!show) {
      tachimetro(S, W, H, u, T, M, lamp);       // la velocità sta in basso a destra, col nitro (vedi sotto)
      // ── vita, arma, bonus (in basso a sinistra). Il nitro è passato nel tachimetro, e sotto la vita resta una riga libera per lo scudo ──
      {
        const lato = Math.max(8, Math.round(26 * u)), gap = Math.max(2, Math.round(8 * u)), et = larg('VITA', T.s) + pad;
        const arma = ascii(S.arma.nome) + (isFinite(S.arma.usi) ? ' X' + S.arma.usi : '');
        // il contatore scende: BONUS FRA 5, 4, 3, 2, 1 — poi riparte da 7, poi da 10… — e accanto i takedown totali
        const fra = 'BONUS FRA ', n = String(S.mancano ?? 0), tot = `   KO TOT ${S.takedown}`;
        const wBott = larg(fra, T.s) + larg(n, T.m) + larg(tot, T.s);
        const w = Math.max(et + 9 * (lato + gap) - gap, larg(arma, T.s), wBott) + pad * 2;
        const rr = Math.max(lato, T.s) + Math.max(8, Math.round(14 * u));
        const h = pad * 2 + rr + riga + T.s + Math.round(4 * u);
        const x = M, y = H - M - h;
        scatola(x, y, w, h, u);
        const ty = (lato - T.s) / 2;
        testo('VITA', x + pad, y + pad + ty, T.s, GIALLO);
        blocchi(x + pad + et, y + pad, 9, Math.round(S.vita * 9), lato, gap, S.vita < 0.3 && lamp ? BIANCO : ROSSO);
        testo(arma, x + pad, y + pad + rr, T.s, BIANCO);
        {
          const yb = y + pad + rr + riga, ultimo = (S.mancano ?? 0) <= 1;
          let xb = x + pad + testo(fra, x + pad, yb, T.s, GRIGIO);
          xb += testo(n, xb, yb - (T.m - T.s), T.m, ultimo && lamp ? BIANCO : GIALLO);
          testo(tot, xb, yb, T.s, GRIGIO);
        }
      }
      // ── combo (a destra, a metà): rimbalza sulla cassa ──
      {
        const t = ora();
        const attiva = S.combo >= 2 && t - S.comboT < 2.5, rottaOra = t - rotta < 0.7;
        if (attiva || rottaOra) {
          const n = rottaOra ? 'X0' : 'X' + S.combo, sc = 1 + 0.14 * mus.cassa;
          const g = glifo(n, T.xl, rottaOra ? ROSSO : BIANCO), cx = W - M, cy = H * 0.5;
          testo('COMBO', cx, cy - T.xl / 2 - riga, T.s, GIALLO, 'right');
          ctx.drawImage(g.c, Math.round(cx - (g.w + g.pad) * sc), Math.round(cy - (T.xl / 2 + g.pad) * sc + T.xl * 0.1),
                        Math.round(g.c.width * sc), Math.round(g.c.height * sc));
        }
      }
    }

    // ── metronomo (in basso al centro): quattro quadrati, l'uno rosso ──
    {
      const lato = Math.max(8, Math.round((show ? 48 : 34) * u)), gap = Math.max(4, Math.round((show ? 22 : 16) * u));
      const tot = 4 * lato + 3 * gap, x0 = Math.round(W / 2 - tot / 2);
      const y0 = Math.round(H - M - lato - (show ? T.s + riga : Math.round(6 * u)));
      const o = Math.max(2, Math.round(4 * u)), b = Math.max(2, Math.round(3 * u));
      for (let i = 0; i < 4; i++) {
        const on = i === mus.inBattuta, x = x0 + i * (lato + gap);
        ctx.fillStyle = '#000'; ctx.fillRect(x + o, y0 + o, lato, lato);
        ctx.fillStyle = on ? (i === 0 ? ROSSO : GIALLO) : FONDO; ctx.fillRect(x, y0, lato, lato);
        ctx.strokeStyle = BIANCO; ctx.lineWidth = b; ctx.strokeRect(x + b / 2, y0 + b / 2, lato - b, lato - b);
      }
      if (show) testo(Math.round(mus.bpm) + ' BPM', W / 2, y0 + lato + riga - T.s + 6 * u, T.s, BIANCO, 'center');
      if (giudizio && !show) {
        const eta = ora() - giudizio.t0;
        if (eta > 0.7) giudizio = null;
        else testo(giudizio.testo, W / 2, y0 - T.m - 18 * u - eta * 30 * u, T.m, eta % 0.16 < 0.08 ? giudizio.colore : BIANCO, 'center');
      }
    }

    // ── SHOW: sezione e smarmellometro (in alto al centro) ──
    if (show) {
      const sez = ascii(mus.sezione), lato = Math.max(8, Math.round(24 * u)), gap = Math.max(2, Math.round(8 * u));
      const et = 'SMARMELLA ', n = Math.round(S.smarmella * 4) + 1;
      const w = Math.max(larg('SALITA', T.l), larg(et, T.s) + 5 * (lato + gap)) + pad * 2;
      const h = pad * 2 + T.l + riga + lato;
      const x = W / 2 - w / 2;
      scatola(x, M, w, h, u);
      testo(sez, W / 2, M + pad, T.l, mus.sezione === 'drop' ? (lamp ? ROSSO : GIALLO) : GIALLO, 'center');
      const yb = M + pad + T.l + riga - T.s;
      testo(et, x + pad, yb + (lato - T.s) / 2, T.s, BIANCO);
      blocchi(x + pad + larg(et, T.s), yb, 5, n, lato, gap, n >= 5 ? ROSSO : GIALLO);
    }

    if (banner) disegnaBanner(S, W, H, u, T, lamp);
    if (notifica && !show) disegnaNotifica(S, W, H, u, T, M, lamp);
  }

  function disegnaNotifica(S, W, H, u, T, M, lamp) {
    const n = notifica, eta = ora() - n.t0;
    if (eta > n.durata) { notifica = null; return; }
    const fuori = Math.max(0, (eta - (n.durata - 0.25)) / 0.25);          // ultimo quarto di secondo: svanisce
    const entra = Math.min(1, eta / 0.12), pad = Math.max(8, Math.round(18 * u)), b = Math.max(2, Math.round(3 * u));
    const colore = Math.floor(eta / ((S.musica.periodo || 0.5) / 2)) % 2 ? GIALLO : BIANCO;
    ctx.globalAlpha = 1 - fuori;
    if (stileNotifica === 'alto') {
      const alto = Math.round((T.l + T.s + 48 * u) * entra), y = Math.round(H * 0.19);
      const f = Math.max(2, Math.round(5 * u));
      ctx.fillStyle = MN_BLU_SCURO; ctx.fillRect(0, y, W, alto);
      ctx.fillStyle = MN_ROSSO; ctx.fillRect(0, y, W, f); ctx.fillRect(0, y + alto - f, W, f);
      if (entra >= 1) {
        testo(n.testo, W / 2, y + 16 * u, T.l, colore, 'center');
        if (n.sotto) testo(n.sotto, W / 2, y + 16 * u + T.l + 12 * u, T.s, CIANO, 'center');
      }
    } else if (stileNotifica === 'nastro' || stileNotifica === 'lato') {
      const w = Math.max(larg(n.testo, T.m), larg(n.sotto, T.s)) + pad * 2, h = pad * 2 + T.m + (n.sotto ? T.s + 12 * u : 0) + 8 * u;
      let x, y;
      if (stileNotifica === 'nastro') { x = W / 2 - w / 2; y = M - (1 - entra) * (h + M); }
      else { x = W - M - w + (1 - entra) * (w + M); y = H * 0.27; }
      scatola(x, y, w, h, u);
      testo(n.testo, x + w / 2, y + pad + 8 * u, T.m, colore, 'center');
      if (n.sotto) testo(n.sotto, x + w / 2, y + pad + 8 * u + T.m + 12 * u, T.s, CIANO, 'center');
    } else if (stileNotifica === 'rivale') {
      const p = S.notificaPos || n.pos || { x: 0.5, y: 0.4 };   // segue il rivale mentre cade, se il gioco lo passa
      const sc = 1 + 0.35 * Math.max(0, 1 - eta / 0.15);                     // salta fuori più grande e si assesta
      const x = p.x * W, y = p.y * H - eta * 90 * u - T.l;
      const g = glifo(n.testo, T.l, colore);
      ctx.drawImage(g.c, Math.round(x - (g.w / 2 + g.pad) * sc), Math.round(y - g.pad * sc), Math.round(g.c.width * sc), Math.round(g.c.height * sc));
      if (n.sotto) testo(n.sotto, x, y + T.l * sc + 10 * u, T.s, CIANO, 'center');
    }
    ctx.globalAlpha = 1;
  }

  // ── TACHIMETRO come quello di un'auto, a blocchi (8 bit), in basso a destra. Scala 0-300 km/h: 200 è la
  // velocità massima, oltre si va solo col nitro (zona rossa). Il NITRO è un arco di blocchi nel varco in basso
  // del quadrante (la scala occupa gli altri 240°): si svuota mentre lo usi, e quando è pieno lampeggia «NITRO PRONTO!».
  const KMH_FONDO = 300, KMH_MAX = 200;
  function tachimetro(S, W, H, u, T, M, lamp) {
    const q = Math.max(3, Math.round(7 * u));                    // il "pixel" del disegno
    const blocco = (x, y, c, k = 1) => { ctx.fillStyle = c; ctx.fillRect(Math.round(x / q) * q, Math.round(y / q) * q, q * k, q * k); };
    const t = Math.min(1, Math.max(0, S.kmh / KMH_FONDO)), tMax = KMH_MAX / KMH_FONDO;
    const mus = S.musica, bpm = Math.round(mus.bpm) + ' BPM';
    const ang = (v, a0, a1) => a0 + (a1 - a0) * v;              // radianti, 0 = destra, positivo = in alto
    const punto = (cx, cy, r, a) => [cx + r * Math.cos(a), cy - r * Math.sin(a)];
    const R = Math.round(175 * u), cx = W - M - R - q, cy = H - M - R - q, a0 = Math.PI * 7 / 6, a1 = -Math.PI / 6;
    // disco: ombra a scalino, anello bianco, anello rosso, fondo blu notte
    for (let y = -R - q; y <= R + q; y += q) for (let x = -R - q; x <= R + q; x += q)
      if (Math.hypot(x, y) <= R + q * 0.5) blocco(cx + x + q, cy + y + q, '#000');
    for (let y = -R; y <= R; y += q) for (let x = -R; x <= R; x += q) {
      const d = Math.hypot(x, y);
      if (d <= R + q * 0.5) blocco(cx + x, cy + y, d > R - q * 1.2 ? BIANCO : d > R - q * 2.6 ? MN_ROSSO : MN_BLU_SCURO);
    }
    // zona rossa del nitro e tacche
    for (let v = tMax; v <= 1.0001; v += 0.012) { const [x, y] = punto(cx, cy, R - q * 4, ang(v, a0, a1)); blocco(x, y, MN_ROSSO); }
    for (let kmh = 0; kmh <= KMH_FONDO; kmh += 10) {
      const v = kmh / KMH_FONDO, grande = kmh % 50 === 0, a = ang(v, a0, a1);
      const [x, y] = punto(cx, cy, R - q * (grande ? 5.2 : 4.6), a);
      blocco(x, y, kmh > KMH_MAX ? ROSSO : BIANCO, grande ? 2 : 1);
      if (grande) { const [nx, ny] = punto(cx, cy, R - q * 9.5, a); testo(String(kmh), nx, ny - T.s / 2, T.s, kmh > KMH_MAX ? ROSSO : GIALLO, 'center'); }
    }
    // NITRO: arco nel varco in basso, da sinistra a destra; il fondo del varco si vede sempre, i blocchi si svuotano da destra
    {
      const nN = 12, piena = S.nitro >= 1 - 1e-6, usa = S.boost, pieni = Math.floor(S.nitro * nN + 1e-6);
      for (let i = 0; i < nN; i++) {
        const v = (i + 0.5) / nN, a = (225 + 90 * v) * Math.PI / 180, [x, y] = punto(cx, cy, R - q * 4.4, a);   // 225° → 315°: il varco in basso
        const c = i < pieni ? ((usa || piena) && lamp ? BIANCO : CIANO) : SPENTO;
        blocco(x - q, y - q, c, 2);
      }
    }
    // lancetta
    {
      const a = ang(t, a0, a1), r = R - q * 6, c = S.boost && lamp ? CIANO : ROSSO;
      for (let k = 0; k <= r; k += q * 0.7) { const [x, y] = punto(cx, cy, k, a); blocco(x - q / 2, y - q / 2, k > r - q * 2 ? MN_ORO : c); }
      blocco(cx - q, cy - q, MN_ORO, 2);
    }
    testo(String(S.kmh), cx, cy + R * 0.12, T.l, S.boost && lamp ? CIANO : BIANCO, 'center');
    testo('KM/H', cx, cy + R * 0.12 + T.l + 8 * u, T.s, GIALLO, 'center');
    testo(S.boost ? 'BOOST!' : S.nitro >= 1 ? (lamp ? 'NITRO PRONTO' : '') : 'NITRO', cx, cy + R * 0.12 + T.l + T.s + 22 * u, T.s, S.boost || S.nitro >= 1 ? CIANO : GRIGIO, 'center');
    testo(bpm, cx, cy - R * 0.42, T.s, mus.cassa > 0.5 ? GIALLO : GRIGIO, 'center');
  }

  function spettro(S, W, H, u, show) {
    const sp = S.musica.spettro, n = 32, colW = W / n, blocco = Math.max(3, Math.round(8 * u)), sep = Math.max(1, Math.round(2 * u));
    const maxB = show ? 10 : 5;
    ctx.globalAlpha = show ? 0.85 : 0.55;
    for (let i = 0; i < n; i++) {
      // 64 bande → 32 colonne: il massimo delle due
      const v = Math.max(sp[i * 2] || 0, sp[i * 2 + 1] || 0), nb = Math.round(v * maxB);
      for (let k = 0; k < nb; k++) {
        ctx.fillStyle = k >= maxB - 2 ? ROSSO : k >= maxB - 4 ? GIALLO : CIANO;
        ctx.fillRect(Math.round(i * colW + sep), Math.round(H - (k + 1) * (blocco + sep)), Math.round(colW - 2 * sep), blocco);
      }
    }
    ctx.globalAlpha = 1;
  }

  function disegnaBanner(S, W, H, u, T, lamp) {
    const px = n => Math.max(8, Math.round(n * u / 8) * 8);
    T = T || { s: px(16), m: px(24), xxl: px(96) };
    const b = banner, eta = ora() - b.t0;
    if (eta > b.durata) { banner = null; return; }
    // la scritta deve stare nello schermo: se è lunga si scende di misura
    let size = T.xxl; while (size > 8 && larg(b.testo, size) > W * 0.9) size -= 8;
    const entra = Math.min(1, eta / 0.12), alto = Math.round((size + T.m + 90 * u) * entra), y = Math.round(H * 0.42 - alto / 2);
    const fascia = Math.max(3, Math.round(6 * u));
    ctx.fillStyle = MN_BLU_SCURO; ctx.fillRect(0, y, W, alto);
    ctx.fillStyle = MN_ROSSO; ctx.fillRect(0, y, W, fascia * 2); ctx.fillRect(0, y + alto - fascia * 2, W, fascia * 2);
    ctx.fillStyle = MN_ORO; ctx.fillRect(0, y + fascia * 2, W, fascia / 2); ctx.fillRect(0, y + alto - fascia * 2.5, W, fascia / 2);
    if (entra < 1) return;
    const mezzo = Math.floor(eta / ((S.musica.periodo || 0.5) / 2)) % 2;      // cambia colore ogni mezzo battito
    testo(b.testo, W / 2, y + 30 * u, size, mezzo ? GIALLO : BIANCO, 'center');
    if (b.sotto) testo(b.sotto, W / 2, y + 30 * u + size + 22 * u, T.m, CIANO, 'center');
  }

  return {
    disegna, colpo, ascii, sceltaA,
    banner: lanciaBanner,
    notifica: lanciaNotifica,
    setNotifica(st) { stileNotifica = st; },
    get stileNotifica() { return stileNotifica; },
    comboRotta() { rotta = ora(); },
    setModo(m) { modo = m; },
    get modo() { return modo; },
    get pronto() { return fontPronto; },
  };
}
