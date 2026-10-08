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
const GIALLO = '#ffd23f', ROSSO = '#ff3b30', CIANO = '#3fd0ff', BIANCO = '#ffffff', SPENTO = '#2a2f45', GRIGIO = '#9aa3c0';

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
    ctx.fillStyle = 'rgba(8,10,24,.86)'; ctx.fillRect(x, y, w, h);
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
        if (r.ko) testo('KO', x, yy - T.s - 6 * u, T.s, GRIGIO, 'center');   // i rivali non hanno nome
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
      // ── velocità (in alto a destra) ──
      {
        const kmh = String(S.kmh), bpm = Math.round(mus.bpm) + ' BPM';
        const w = Math.max(larg('000', T.xl), larg(bpm, T.s)) + pad * 2, h = pad * 2 + T.s + riga - T.s + T.xl + riga;
        const x = W - M - w;
        scatola(x, M, w, h, u);
        testo(S.boost ? (lamp ? 'BOOST!' : '') : 'KM/H', x + pad, M + pad, T.s, S.boost ? CIANO : GIALLO);
        testo(kmh, x + w - pad, M + pad + riga, T.xl, BIANCO, 'right');
        testo(bpm, x + w - pad, M + pad + riga + T.xl + riga - T.s, T.s, mus.cassa > 0.5 ? GIALLO : GRIGIO, 'right');
      }
      // ── vita, nitro, arma, bottino (in basso a sinistra) ──
      {
        const lato = Math.max(8, Math.round(26 * u)), gap = Math.max(2, Math.round(8 * u)), et = larg('NITRO', T.s) + pad;
        const arma = ascii(S.arma.nome) + (isFinite(S.arma.usi) ? ' X' + S.arma.usi : '');
        const bottino = `KO ${S.takedown}  BONUS ${S.bonus ?? 0} (${S.versoBonus ?? 0}/${S.perBonus ?? 5})  ${String(S.punti).padStart(6, '0')}`;
        const w = Math.max(et + 9 * (lato + gap) - gap, larg(arma, T.s), larg(bottino, T.s)) + pad * 2;
        const rr = Math.max(lato, T.s) + Math.max(8, Math.round(14 * u));
        const h = pad * 2 + rr * 2 + riga + T.s;
        const x = M, y = H - M - h;
        scatola(x, y, w, h, u);
        const ty = (lato - T.s) / 2;
        testo('VITA', x + pad, y + pad + ty, T.s, GIALLO);
        blocchi(x + pad + et, y + pad, 9, Math.round(S.vita * 9), lato, gap, S.vita < 0.3 && lamp ? BIANCO : ROSSO);
        testo('NITRO', x + pad, y + pad + rr + ty, T.s, GIALLO);
        blocchi(x + pad + et, y + pad + rr, 9, Math.floor(S.nitro * 9 + 1e-6), lato, gap, (S.boost || S.nitro >= 1) && lamp ? BIANCO : CIANO);
        testo(S.nitro >= 1 && !S.boost ? (lamp ? 'NITRO PRONTO!' : '') : arma, x + pad, y + pad + rr * 2, T.s, S.nitro >= 1 ? CIANO : BIANCO);
        testo(bottino, x + pad, y + pad + rr * 2 + riga, T.s, GRIGIO);
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
        ctx.fillStyle = on ? (i === 0 ? ROSSO : GIALLO) : 'rgba(8,10,24,.86)'; ctx.fillRect(x, y0, lato, lato);
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
    ctx.fillStyle = '#000'; ctx.fillRect(0, y, W, alto);
    ctx.fillStyle = GIALLO; ctx.fillRect(0, y, W, fascia); ctx.fillRect(0, y + alto - fascia, W, fascia);
    if (entra < 1) return;
    const mezzo = Math.floor(eta / ((S.musica.periodo || 0.5) / 2)) % 2;      // cambia colore ogni mezzo battito
    testo(b.testo, W / 2, y + 30 * u, size, mezzo ? GIALLO : BIANCO, 'center');
    if (b.sotto) testo(b.sotto, W / 2, y + 30 * u + size + 22 * u, T.m, CIANO, 'center');
  }

  return {
    disegna, colpo, ascii,
    banner: lanciaBanner,
    comboRotta() { rotta = ora(); },
    setModo(m) { modo = m; },
    get modo() { return modo; },
    get pronto() { return fontPronto; },
  };
}
