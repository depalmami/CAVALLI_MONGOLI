// PANNELLO MUSICA — la parte di console che mostra cosa sentono le orecchie e
// ne sceglie le sorgenti. Non va mai in proiezione: è roba da regia.
//
// Si ricorda da solo sorgente, ingresso, guadagno e anticipo (chiave separata
// dalle preferenze generali: l'ingresso audio si può riaprire solo DOPO aver
// elencato i dispositivi, quindi non può passare dal giro "riapplica i valori").

const CHIAVE = 'cm3d.musica.v1';
const COLORE_SEZIONE = { pausa: '#7aa2ff', salita: '#ffd166', groove: '#38a169', drop: '#ff4d6d' };
const COLORE_VOCE = { cassa: '#ff6b35', rullante: '#ffd166', charleston: '#7ee8fa' };

export function collegaPannelloMusica(musica) {
  const $ = id => document.getElementById(id);
  const cv = $('mu-meter'), ctx = cv.getContext('2d');
  const pref = (() => { try { return JSON.parse(localStorage.getItem(CHIAVE) || '{}') || {}; } catch { return {}; } })();
  const salva = () => { try { localStorage.setItem(CHIAVE, JSON.stringify(pref)); } catch {} };
  const scrivi = (t, forte) => { const e = $('mu-stato'); e.textContent = t; e.classList.toggle('forte', !!forte); };

  // ── sorgente del tempo ──
  $('mu-fonte').value = pref.fonte || 'auto';
  musica.setScelta($('mu-fonte').value);
  $('mu-fonte').onchange = e => { musica.setScelta(e.target.value); pref.fonte = e.target.value; salva(); };

  // ── guadagno dell'analisi e anticipo visivo ──
  const trim = $('mu-trim'), anticipo = $('mu-anticipo');
  trim.value = pref.trim ?? 0; anticipo.value = pref.anticipo ?? 0;
  const suTrim = () => { musica.setTrimDb(+trim.value); $('mu-trim-val').textContent = (+trim.value > 0 ? '+' : '') + trim.value + ' dB'; pref.trim = +trim.value; salva(); };
  const suAnticipo = () => { musica.setAnticipo(+anticipo.value); $('mu-anticipo-val').textContent = anticipo.value + ' ms'; pref.anticipo = +anticipo.value; salva(); };
  trim.oninput = suTrim; anticipo.oninput = suAnticipo; suTrim(); suAnticipo();

  // ── ingresso audio ──
  const sel = $('mu-ingresso');
  async function riempiIngressi(scelto) {
    const lista = await musica.elencaIngressi().catch(() => []);
    sel.innerHTML = '<option value="">— ingresso predefinito —</option>' +
      lista.map(d => `<option value="${d.id}">${d.nome.replace(/</g, '&lt;')}</option>`).join('');
    if (scelto && lista.some(d => d.id === scelto)) sel.value = scelto;
    return lista;
  }
  async function ascolta(id) {
    scrivi('apro l’ingresso…');
    try {
      const nome = await musica.ascoltaIngresso(id || undefined);
      const st = musica.stato();
      pref.sorgente = 'ingresso'; pref.ingresso = st.audio.id; salva();
      await riempiIngressi(st.audio.id);
      scrivi('🎙 ascolto: ' + nome);
    } catch (e) {
      scrivi('ingresso non disponibile: ' + (e.name === 'NotAllowedError' ? 'permesso negato dal browser' : e.message), true);
    }
  }
  $('mu-attiva').onclick = () => ascolta(sel.value);
  sel.onchange = () => ascolta(sel.value);
  $('mu-ferma').onclick = () => { musica.ferma(); pref.sorgente = ''; salva(); scrivi('audio spento'); };

  // ── file audio (prove senza band) ──
  const player = $('mu-player');
  $('mu-file').onclick = () => $('mu-file-in').click();
  $('mu-file-in').onchange = async e => {
    const f = e.target.files[0]; if (!f) return;
    try {
      await musica.ascoltaFile(f, player);
      player.style.display = 'block';
      pref.sorgente = ''; salva();             // un file locale non si può riaprire da solo
      scrivi('📁 file: ' + f.name);
    } catch (err) { scrivi('file non leggibile: ' + err.message, true); }
  };
  const monitor = $('mu-monitor');
  monitor.checked = pref.monitor ?? true;
  musica.setMonitor(monitor.checked);
  monitor.onchange = () => { musica.setMonitor(monitor.checked); pref.monitor = monitor.checked; salva(); };

  // ── MIDI ──
  async function midi() {
    try {
      const porte = await musica.attivaMidi();
      pref.midi = true; salva();
      $('mu-midi').classList.add('active');
      scrivi('🎹 MIDI: ' + (porte.length ? porte.join(', ') : 'nessuna porta (accendi il bus IAC in Configurazione MIDI Audio)'));
    } catch (e) { scrivi('MIDI non disponibile: ' + e.message, true); }
  }
  $('mu-midi').onclick = midi;

  // ── tempo a mano ──
  $('mu-tap').onclick = () => musica.tap();
  $('mu-uno').onclick = () => musica.uno();
  $('mu-x2').onclick  = () => musica.raddoppia();
  $('mu-d2').onclick  = () => musica.dimezza();

  // ── ripristino all'avvio: solo ciò che non chiede permessi nuovi ──
  (async () => {
    if (pref.midi) midi();
    if (pref.sorgente === 'ingresso') {
      let concesso = false;
      try { concesso = (await navigator.permissions.query({ name: 'microphone' })).state === 'granted'; } catch {}
      if (concesso) { await riempiIngressi(pref.ingresso); ascolta(sel.value); }
      else scrivi('premi «Ascolta ingresso» per riaprire l’ingresso dell’ultima volta');
    }
  })();

  // ── METER ───────────────────────────────────────────────────────────────
  let W = 0, H = 0, lampDrop = 0;
  musica.on('drop', () => { lampDrop = 1; });
  function misura() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const w = Math.round(cv.clientWidth * dpr), h = Math.round(cv.clientHeight * dpr);
    if (w !== W || h !== H) { W = cv.width = w; H = cv.height = h; }
    return dpr;
  }
  let ultimoTesto = 0;
  function disegna(dt) {
    if (!cv.clientWidth) return;
    const k = misura(), m = musica;
    ctx.fillStyle = '#0b0e14'; ctx.fillRect(0, 0, W, H);

    // spettro
    const x0 = 150*k, y0 = 14*k, sw = W - x0 - 150*k, sh = H - 34*k, n = m.spettro.length, bw = sw / n;
    for (let i = 0; i < n; i++) {
      const v = m.spettro[i], h = Math.max(1*k, v * sh);
      ctx.fillStyle = `hsl(${200 - i/n*200}, 85%, ${35 + v*30}%)`;
      ctx.fillRect(x0 + i*bw + 0.5*k, y0 + sh - h, Math.max(1, bw - 1*k), h);
    }
    // anello di fase + battuta
    const cx = 72*k, cy = H/2 - 6*k, r = 44*k;
    ctx.lineWidth = 6*k; ctx.strokeStyle = '#1f2633';
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2); ctx.stroke();
    ctx.strokeStyle = m.fonte === 'midi' ? '#b18cff' : m.fonte === 'audio' ? '#38a169' : '#c98a3a';
    ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI/2, -Math.PI/2 + m.fase*Math.PI*2); ctx.stroke();
    for (let i = 0; i < 4; i++) {
      const a = -Math.PI/2 + i*Math.PI/2, on = i === m.inBattuta;
      ctx.fillStyle = on ? (i === 0 ? '#ff4d6d' : '#ffffff') : '#3a4456';
      ctx.beginPath(); ctx.arc(cx + Math.cos(a)*(r + 12*k), cy + Math.sin(a)*(r + 12*k), (on ? 5 : 3.5)*k, 0, Math.PI*2); ctx.fill();
    }
    ctx.fillStyle = '#e8edf6'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `800 ${24*k}px -apple-system, sans-serif`; ctx.fillText(m.bpm.toFixed(1), cx, cy - 4*k);
    ctx.font = `600 ${10*k}px -apple-system, sans-serif`; ctx.fillStyle = '#9aa7bd';
    ctx.fillText(m.fonte.toUpperCase(), cx, cy + 16*k);
    ctx.fillText(`${m.battuta + 1}.${m.inBattuta + 1}`, cx, H - 10*k);

    // bande, energia, brillanza
    const etich = [['SUB', m.sub], ['BAS', m.bassi], ['MED', m.medi], ['ALT', m.alti], ['ENE', m.energia], ['BRI', m.brillanza]];
    const bx = W - 140*k, bbw = 18*k;
    etich.forEach(([nome, v], i) => {
      const x = bx + i*22*k;
      ctx.fillStyle = '#1f2633'; ctx.fillRect(x, y0, bbw, sh);
      ctx.fillStyle = i < 4 ? '#38a1d9' : '#c98a3a'; ctx.fillRect(x, y0 + sh*(1 - v), bbw, sh*v);
      ctx.fillStyle = '#9aa7bd'; ctx.font = `600 ${8*k}px -apple-system, sans-serif`; ctx.fillText(nome, x + bbw/2, H - 10*k);
    });
    // lampade dei colpi e sezione
    ['cassa', 'rullante', 'charleston'].forEach((v, i) => {
      const x = x0 + 14*k + i*90*k, y = H - 10*k, a = m[v];
      ctx.fillStyle = a > 0.05 ? COLORE_VOCE[v] : '#2a3140'; ctx.globalAlpha = 0.35 + 0.65*a;
      ctx.beginPath(); ctx.arc(x, y, 5*k, 0, Math.PI*2); ctx.fill(); ctx.globalAlpha = 1;
      ctx.fillStyle = '#9aa7bd'; ctx.textAlign = 'left'; ctx.fillText(v.toUpperCase(), x + 9*k, y);
    });
    lampDrop = Math.max(0, lampDrop - (dt || 0.016)*0.8);
    ctx.textAlign = 'right'; ctx.font = `800 ${13*k}px -apple-system, sans-serif`;
    ctx.fillStyle = COLORE_SEZIONE[m.sezione] || '#fff';
    ctx.fillText((lampDrop > 0 ? '💥 ' : '') + m.sezione.toUpperCase(), x0 + sw, H - 10*k);
    if (lampDrop > 0) { ctx.fillStyle = `rgba(255,77,109,${lampDrop*0.25})`; ctx.fillRect(0, 0, W, H); }
    ctx.textAlign = 'left';

    // riga di stato testuale, 4 volte al secondo
    const ora = performance.now();
    if (ora - ultimoTesto > 250) {
      ultimoTesto = ora;
      const st = musica.stato(), a = st.audio, mi = st.midi;
      const parti = [];
      parti.push(a.attivo ? `🎙 ${a.tipo === 'file' ? 'file' : 'ingresso'} ${m.livelloDb > -100 ? m.livelloDb.toFixed(0) + ' dB' : '—'}` +
                 (a.bpm ? ` · stima ${(a.bpm * st.ottava).toFixed(1)} (chiarezza ${a.conf.toFixed(1)})` : ' · sto ascoltando…')
                 : '🎙 audio spento');
      if (a.contesto === 'suspended') parti.push('⚠️ clicca nella pagina per far partire l’audio');
      parti.push(mi.attivo ? `🎹 ${mi.clock ? 'clock ' + mi.bpm.toFixed(1) : 'nessun clock'}` : '🎹 MIDI spento');
      parti.push(st.unoNoto ? `uno: ${st.unoNoto}` : 'uno: da segnare (U)');
      $('mu-lettura').textContent = parti.join('  ·  ');
    }
  }
  return { disegna };
}
