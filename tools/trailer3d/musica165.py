"""MUSICA DEL TRAILER (30 s, 165 BPM, Re minore) — una BOZZA sintetizzata, per sentire i tempi: i suoni veri si rifanno in Ableton.
Tutta sintetizzata, niente campioni, solo numpy (si lancia col python di Blender: non serve scaricare nulla).

  /Applications/Blender.app/Contents/Resources/5.1/python/bin/python3.13 -I tools/trailer3d/musica165.py trailer/blender/musica

Esce: trailer-30s-musica-bozza.wav (master), stem/*.wav (batteria, basso, musica, effetti, riverbero), guida-165bpm.mid (tempo a 165,
un battito di click per battito, una nota a ogni taglio, marcatori con gli shot), CUE.md.

PERCHÉ 165 BPM TORNA COL MONTAGGIO (che era pensato a 120): un battito dura 0,3636 s, quindi 1 s = 2,75 battiti e 4 s = 11 battiti
esatti. Se ogni frase riparte su un taglio (il «downbeat» sta sul taglio), tutti i tagli successivi cadono su una semicroma o su un ottavo
(o a un fotogramma da un battito), tranne S10 (9,0 s). Le tre frasi ripartono su 5,5 s (S08), 14,5 s (S15) e 23,5 s (S25).
Gli effetti sui tagli sono messi al tempo ESATTO del taglio, non sulla griglia."""
import sys, os, math, wave, struct
import numpy as np

SR = 48000; DUR = 30.0; N = int(SR * DUR)
BPM = 165.0; BEAT = 60.0 / BPM; S16 = BEAT / 4
rng = np.random.default_rng(165)

# ── i tempi del montaggio (da STORYBOARD.md, 24 fps) ────────────────────────────────────────────────────────────────────
TAGLI = [('S03', 0.0), ('S04', 2.0), ('S05', 3.5), ('S06', 4.5), ('S08', 5.5), ('S09a', 7.0), ('S09b', 7.5), ('S09c', 8.0), ('S09d', 8.5),
         ('S10', 9.0), ('S11', 9.5), ('S13a', 11.0), ('S13b', 11.5), ('S14', 12.5), ('S15', 14.5), ('S16', 15.0), ('S18', 15.5), ('S19', 16.0),
         ('S20', 16.5), ('S21', 18.0), ('S22', 19.0), ('S23', 21.0), ('S24', 22.5), ('S25', 23.5), ('S26', 24.5), ('S27', 25.5),
         ('fermo', 26.5), ('nero', 27.5), ('S28', 29.0)]
A1, A2, A3 = 5.5, 14.5, 23.5                      # dove ripartono le tre frasi (il downbeat sta su un taglio)

# ── attrezzi ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def idx(t): return int(round(t * SR))
def tarr(n): return np.arange(n) / SR
def hz(m): return 440.0 * 2 ** ((m - 69) / 12.0)
def noise(n): return rng.standard_normal(n)

def fft_filter(x, H):
    n = len(x); m = 1 << (n - 1).bit_length(); f = np.fft.rfftfreq(m, 1 / SR)
    return np.fft.irfft(np.fft.rfft(x, m) * H(f), m)[:n]
def lp(x, fc, o=4): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * o)))
def hp(x, fc, o=2): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-6)) ** (2 * o)) * (f > 0))
def bp(x, lo, hi, o=2): return hp(lp(x, hi, o), lo, o)
def picco(x, fc, q): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (q * (f / fc - fc / np.maximum(f, 1e-6))) ** 2))

def stft(x, H, nfft=2048, hop=512):
    """Filtro che cambia nel tempo: H(t, f) → guadagno. Finestre di Hann a 75%: la somma vale 2."""
    win = np.hanning(nfft); f = np.fft.rfftfreq(nfft, 1 / SR); y = np.zeros(len(x) + 2 * nfft)
    xp = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    for s in range(0, len(xp) - nfft, hop):
        t = (s + nfft / 2 - nfft) / SR
        y[s:s + nfft] += np.fft.irfft(np.fft.rfft(xp[s:s + nfft] * win) * H(t, f), nfft)
    return y[nfft:nfft + len(x)] / 2.0

def e_ad(n, a, d, k=5.0):
    t = tarr(n); return np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) * k / d))
def e_sw(n, a, r):
    t = tarr(n); return np.minimum(1, t / max(a, 1e-6)) * np.minimum(1, (n / SR - t) / max(r, 1e-6))
def saw_f(freq): return 2 * ((np.cumsum(freq) / SR) % 1.0) - 1
def saw(f0, n, ph=0.0): return 2 * ((f0 * tarr(n) + ph) % 1.0) - 1
def sat(x, g=2.0): return np.tanh(g * x) / np.tanh(g)

class Bus:
    def __init__(s): s.d = np.zeros((2, N))
    def put(s, t0, x, g=1.0, pan=0.0):
        x = np.atleast_2d(x)
        if x.shape[0] == 1: x = np.vstack([x, x])
        a = idx(t0); b = min(N, a + x.shape[1])
        if a >= N or b <= 0: return
        lo = max(0, -a); l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
        s.d[0, a + lo:b] += x[0, lo:b - a] * g * l; s.d[1, a + lo:b] += x[1, lo:b - a] * g * r

B = {k: Bus() for k in ('batt', 'basso', 'musica', 'fx', 'verb')}
KICK_T = []                                         # i tempi delle casse: servono al sidechain
def a_(bus, t0, x, g=1.0, pan=0.0, verb=0.0):
    B[bus].put(t0, x, g, pan)
    if verb: B['verb'].put(t0, x, g * verb, pan)

# ── gli strumenti ─────────────────────────────────────────────────────────────────────────────────────────────────────
def kick(vel=1.0, lungo=1.0):
    n = idx(0.55 * lungo); t = tarr(n); f = 44 + 130 * np.exp(-t * 30)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5 / lungo)
    click = lp(noise(n), 5000) * np.exp(-t * 150) * 0.5
    return sat(corpo + click, 1.7) * vel

def sub_boom(f0=44.0, dur=1.6, vel=1.0):
    n = idx(dur); t = tarr(n); f = f0 * (1 + 0.5 * np.exp(-t * 14))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2 / dur * 1.6) * vel

def snare(vel=1.0):
    n = idx(0.45); t = tarr(n)
    r = bp(noise(n), 1400, 9500) * np.exp(-t * 20) + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.7
    clap = sum(np.roll(bp(noise(n), 900, 4500) * np.exp(-t * 90), idx(d)) * 0.5 for d in (0.0, 0.011, 0.022))
    return sat(r + clap, 1.3) * vel

def hat(vel=1.0, aperto=False):
    n = idx(0.22 if aperto else 0.06); t = tarr(n)
    return hp(noise(n), 7500) * np.exp(-t * (16 if aperto else 70)) * vel

def tom(f0, vel=1.0):
    n = idx(0.5); t = tarr(n); f = f0 * (1 + 0.6 * np.exp(-t * 20))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * vel

def basso(m, dur, vel=1.0):
    n = idx(dur); t = tarr(n); f = hz(m)
    x = 0.6 * saw(f, n) + 0.4 * saw(f * 1.006, n) + 0.5 * np.sign(np.sin(2 * np.pi * f * t))
    x = lp(x, 520 + 900 * np.exp(-t * 14), 3) if False else lp(x, 700, 3)
    x += 0.9 * np.sin(2 * np.pi * f * 0.5 * t)
    return sat(x, 1.8) * e_sw(n, 0.004, min(0.05, dur * 0.4)) * vel * 0.55

def ottoni(notes, dur, vel=1.0, tenue=False):
    n = idx(dur); x = np.zeros(n)
    for m in notes:
        for c in (-9, -3, 0, 3, 9):
            x += saw(hz(m) * 2 ** (c / 1200.0), n, rng.random())
    scuro = lp(x, 650, 3); chiaro = lp(x, 5200, 3)
    t = tarr(n); b = np.exp(-t * (3 if tenue else 14)) * 0.85 + (0.15 if not tenue else 0.35)
    y = sat((scuro + (chiaro - scuro) * b) * 0.12 / max(1, len(notes) ** 0.5), 2.2)
    return y * (e_sw(n, 0.03 if tenue else 0.006, 0.12 if tenue else 0.06)) * vel

def coro(notes, dur, a=0.6, r=0.4, vel=1.0, vocale=(800, 1150, 2900)):
    n = idx(dur); x = np.zeros(n)
    for m in notes:
        for c in (-14, -5, 5, 14):
            x += saw(hz(m) * 2 ** (c / 1200.0), n, rng.random())
    y = picco(x, vocale[0], 3.5) * 1.0 + picco(x, vocale[1], 4.0) * 0.7 + picco(x, vocale[2], 5.0) * 0.35
    y = lp(y, 5500, 3) * 0.06 / max(1, len(notes) ** 0.5)
    return y * e_sw(n, a, r) * vel

def riser(dur, lo=250, hi=9000, vel=1.0):
    n = idx(dur); x = noise(n); t = tarr(n)
    fc = lambda tt: lo * (hi / lo) ** np.clip(tt / dur, 0, 1)
    y = stft(x, lambda tt, f: 1 / np.sqrt(1 + (3.0 * (f / fc(tt) - fc(tt) / np.maximum(f, 1))) ** 2))
    y += 0.5 * np.sin(2 * np.pi * np.cumsum(lo * 0.5 * (hi / lo) ** (t / dur)) / SR) * 0.3
    return y * (t / dur) ** 2.2 * vel * 4.0

def inverso(dur, vel=1.0):
    n = idx(dur); t = tarr(n); return hp(noise(n), 3000) * (t / dur) ** 3 * vel

def impatto(taglia=1.0):
    n = idx(1.8 * taglia + 0.4); t = tarr(n); f = 120 * np.exp(-t * 5) + 32
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4 / taglia)
    urto = lp(noise(n), 2200) * np.exp(-t * 9) * 0.7
    return sat(boom * 1.1 + urto, 1.6) * 0.9

def nastro_che_si_ferma(x, dur):
    """La lettura va sempre più piano (disco che gratta / nastro che si ferma): x è lungo almeno quanto serve."""
    n = idx(dur); v = np.exp(-4.0 * np.arange(n) / n); pos = np.cumsum(v) * 1.0
    pos = np.clip(pos, 0, len(x) - 2)
    return np.interp(pos, np.arange(len(x)), x) * np.linspace(1, 0.0, n) ** 0.6

def graffio():
    n = idx(0.22); t = tarr(n)
    return bp(noise(n), 700, 6000) * np.exp(-t * 14) * (1 + 0.8 * np.sin(2 * np.pi * 70 * t)) * 0.9

def ruggito(dur=1.0, vel=1.0):
    n = idx(dur); t = tarr(n); f0 = 62 * (1 + 0.25 * np.sin(2 * np.pi * 7 * t)) * np.exp(-t * 0.25)
    x = saw_f(f0) * 0.8 + noise(n) * 0.35
    F1 = lambda tt: 350 + 450 * np.sin(np.pi * np.clip(tt / dur, 0, 1)); F2 = lambda tt: 900 + 900 * np.clip(tt / dur, 0, 1)
    def H(tt, f): return (1 / np.sqrt(1 + (4 * (f / F1(tt) - F1(tt) / np.maximum(f, 1))) ** 2) + 0.7 / np.sqrt(1 + (5 * (f / F2(tt) - F2(tt) / np.maximum(f, 1))) ** 2))
    y = stft(x, H)
    y = sat(y * 3.0, 2.5) * e_ad(n, 0.12, dur * 0.7, 3.0) * (1 - 0.0 * t)
    return y * vel

def sciabola_shing():
    n = idx(0.55); t = tarr(n)
    s = bp(noise(n), 4500, 12000) * np.exp(-t * 9) * (t < 0.3)
    ting = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3100, 1), (4700, 0.6), (7300, 0.4))) * np.exp(-t * 7)
    return (s * 0.6 + ting * 0.25) * np.minimum(1, t / 0.01)

def mazza_tac():
    n = idx(0.2); t = tarr(n)
    return (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 28) + lp(noise(n), 3000) * np.exp(-t * 90) * 0.6) * 1.0

def frusta_crack():
    n = idx(0.3); t = tarr(n)
    return hp(noise(n), 2500) * np.exp(-t * 220) * 1.4 + np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 120) * 0.3

def arco_twang():
    n = idx(0.55); t = tarr(n); f = 190 * (1 + 0.35 * np.exp(-t * 30))
    ph = np.cumsum(f) / SR * 2 * np.pi
    return sum(np.sin(ph * k) * (1.0 / k) for k in (1, 2, 3, 4, 5)) * np.exp(-t * 8) * 0.35

def whoosh(dur=0.35, lo=500, hi=6000, vel=1.0, giu=False):
    n = idx(dur); t = tarr(n); u = t / dur
    fc = (lambda tt: hi * (lo / hi) ** np.clip(tt / dur, 0, 1)) if giu else (lambda tt: lo * (hi / lo) ** np.clip(tt / dur, 0, 1))
    y = stft(noise(n), lambda tt, f: 1 / np.sqrt(1 + (2.2 * (f / fc(tt) - fc(tt) / np.maximum(f, 1))) ** 2))
    return y * np.sin(np.pi * u) ** 1.5 * vel * 3.0

def legno_pezzi(dur=0.5, n_pezzi=14, vel=1.0):
    out = np.zeros(idx(dur) + idx(0.2))
    for _ in range(n_pezzi):
        t0 = rng.random() * dur * 0.9; f = rng.uniform(350, 1800); m = idx(0.12); t = tarr(m)
        p = bp(noise(m), f * 0.6, f * 1.5) * np.exp(-t * rng.uniform(25, 60)) * rng.uniform(0.3, 1.0)
        out[idx(t0):idx(t0) + m] += p
    return out * vel * 2.0

def pop_bolla(vel=1.0):
    n = idx(0.05); t = tarr(n); f = rng.uniform(1400, 2600)
    return (bp(noise(n), 1500, 7000) * np.exp(-t * 130) * 0.8 + np.sin(2 * np.pi * f * t * (1 + 0.6 * np.exp(-t * 90))) * np.exp(-t * 80) * 0.5) * vel

def boing(dur=0.3, vel=1.0, giu=False):
    n = idx(dur); t = tarr(n); u = t / dur
    f = (700 - 450 * u + 120 * np.sin(2 * np.pi * 14 * t)) if giu else (260 + 520 * np.sin(np.pi * u) + 90 * np.sin(2 * np.pi * 16 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.5 * vel * 0.5

def squittio(vel=1.0):
    n = idx(0.07); t = tarr(n); return bp(noise(n), 1800, 6500) * np.exp(-t * 55) * (1 + np.sin(2 * np.pi * 900 * t)) * 0.5 * vel

def tosse():
    n = idx(0.3); t = tarr(n)
    return (lp(noise(n), 1500, 3) * (np.exp(-t * 14) * (t > 0.0)) * 1.4 + np.sin(2 * np.pi * 120 * (1 - 0.3 * t) * t) * np.exp(-t * 20) * 0.5)

def schiocco_morso():
    n = idx(0.25); t = tarr(n)
    return sat(np.sin(2 * np.pi * 70 * t) * np.exp(-t * 15) * 1.2 + hp(noise(n), 800) * np.exp(-t * 90) * 1.0 + bp(noise(n), 150, 600) * np.exp(-t * 40), 1.5)

def tintinnio(vel=1.0):
    n = idx(1.4); t = tarr(n)
    return sum(np.sin(2 * np.pi * f * t) * a * np.exp(-t * d) for f, a, d in ((2370, 1, 5), (3610, 0.7, 6), (5420, 0.4, 9), (7600, 0.2, 12))) * 0.28 * vel

def riverbero(x, durata=1.8, coda=1.0):
    """Riverbero a convoluzione con una risposta sintetica (rumore che si spegne, sempre più scuro)."""
    n = idx(durata); t = tarr(n); out = np.zeros_like(x)
    for ch in range(2):
        ir = noise(n) * np.exp(-t * 6.9 / durata); ir = lp(ir, 5500, 2) * 1.0
        ir[:idx(0.012)] *= np.linspace(0, 1, idx(0.012))
        m = 1 << (x.shape[1] + n - 1).bit_length()
        out[ch] = np.fft.irfft(np.fft.rfft(x[ch], m) * np.fft.rfft(ir, m), m)[:x.shape[1]]
    return out * 0.08 * coda


# ══ L'ARRANGIAMENTO ══════════════════════════════════════════════════════════════════════════════════════════════════
DM, BB, CM = (38, [62, 65, 69]), (34, [58, 62, 65]), (36, [60, 64, 67])      # (radice, accordo): Re minore, Si bemolle, Do

def groove(A, t_end, barre, tipo, vel=1.0):
    """Una frase a 16 semicrome per battuta, a partire dal downbeat A: tipo 'mezzo' (mezzo tempo, epico), 'pieno' (cassa su ogni battito),
    'carica' (come 'pieno' con tom e il motivo degli ottoni)."""
    k = 0
    while True:
        t = A + k * S16
        if t >= t_end: break
        b = (k // 16) % len(barre); st = k % 16; rad, acc = barre[b]
        cassa = {'mezzo': (0, 6, 10), 'pieno': (0, 4, 8, 12), 'carica': (0, 4, 8, 11, 12)}[tipo]
        rull = {'mezzo': (8,), 'pieno': (4, 12), 'carica': (4, 12)}[tipo]
        if st in cassa: a_('batt', t, kick(1.0 * vel), 0.9); KICK_T.append(t)
        if st in rull: a_('batt', t, snare(0.9 * vel), 0.7, 0.0, 0.25)
        a_('batt', t, hat((1.0 if st % 4 == 0 else 0.55 if st % 2 == 0 else 0.3) * vel, aperto=False), 0.35, 0.3 if st % 2 else -0.3)
        if st in (14,) or (tipo != 'mezzo' and st in (2, 6, 10, 14)): a_('batt', t, hat(0.7 * vel, aperto=True), 0.3, 0.4)
        if tipo == 'carica' and st in (13, 14, 15) and b % 2 == 1: a_('batt', t, tom(150 - 25 * (st - 13), 0.8), 0.6, -0.3 + 0.3 * (st - 13), 0.2)
        if st in ((0, 2, 3, 6, 8, 10, 11, 14) if tipo == 'mezzo' else (0, 2, 4, 6, 8, 10, 12, 14)):
            a_('basso', t, basso(rad + (12 if st in (3, 11) else 0), S16 * 1.7), 0.8 * vel)
        if st == 0:
            a_('basso', t, sub_boom(hz(rad - 12), BEAT * 4, 1.0), 0.55 * vel)
            a_('musica', t, coro(acc + [rad + 12], BEAT * 4.3, 0.25, 0.4), 0.6 * vel, 0.0, 0.3)
        if st in ((0, 3, 6) if tipo == 'mezzo' else (0, 6, 10)):
            a_('musica', t, ottoni(acc + [rad + 24], S16 * 2.2), 0.55 * vel, 0.0, 0.18)
        k += 1

HIT_T = []                                          # i colpi sui tagli: sotto ognuno la musica si abbassa un attimo, così il colpo si sente
def colpo(t, taglia=1.0, g=0.8, verb=0.3):
    a_('fx', t, impatto(taglia), g, 0.0, verb); HIT_T.append((t, min(1.0, 0.45 + 0.25 * taglia)))

def stab(t, notes, dur=0.3, g=0.7, tenue=False):
    a_('musica', t, ottoni(notes, dur, 1.0, tenue), g, 0.0, 0.25)

def fermata(ts, dur=0.5, buses=('batt', 'basso', 'musica'), g=0.9):
    """STOP: da ts in poi i bus tonali tacciono e al loro posto c'è il loro stesso suono che rallenta fino a fermarsi (disco che gratta)."""
    a = idx(ts); L = idx(dur * 3)
    mix = sum(B[k].d for k in buses)[:, a:a + L]
    if mix.shape[1] < L: mix = np.pad(mix, ((0, 0), (0, L - mix.shape[1])))
    nuovo = np.vstack([nastro_che_si_ferma(mix[c], dur) for c in range(2)])
    for k in buses:
        B[k].d[:, a:a + idx(0.02)] *= np.linspace(1, 0, idx(0.02)); B[k].d[:, a + idx(0.02):] = 0
    a_('fx', ts, nuovo, g, 0.0, 0.1); a_('fx', ts + 0.01, graffio(), 0.5)

def rallenta(ts, te, buses=('batt', 'basso', 'musica'), g=0.9):
    """S20: la musica si spegne, sempre più lenta e cupa, tra ts e te (nastro che finisce)."""
    a = idx(ts); L = idx(te - ts) + idx(0.5)
    mix = sum(B[k].d for k in buses)[:, a:a + L]
    if mix.shape[1] < L: mix = np.pad(mix, ((0, 0), (0, L - mix.shape[1])))
    n = idx(te - ts); v = np.exp(-2.6 * np.arange(n) / n) * 0.95 + 0.04; pos = np.clip(np.cumsum(v), 0, mix.shape[1] - 2)
    nuovo = np.vstack([np.interp(pos, np.arange(mix.shape[1]), mix[c]) for c in range(2)]) * (np.linspace(1, 0, n) ** 0.7)
    nuovo = np.vstack([lp(nuovo[c], 8000 * np.exp(-3.2 * np.arange(n) / n)[0] + 400, 2) for c in range(2)]) if False else nuovo
    for k in buses: B[k].d[:, a:] = 0
    a_('fx', ts, nuovo, g, 0.0, 0.15)

POST = []
def curva_gain(punti):
    t = tarr(N); return np.interp(t, [p[0] for p in punti], [p[1] for p in punti])

# ── A · S03: il kolossal, cori e un boato lontano; si taglia sullo STOP di S04 ────────────────────────────────────────
a_('fx', 0.0, sub_boom(41.2, 1.6, 0.9), 0.55, 0.0, 0.5)
a_('musica', 0.0, coro([50, 57, 62, 65, 69], 1.55, 0.95, 0.12, 1.0), 0.95, 0.0, 0.5)
a_('musica', 1.40, coro([46, 53, 58, 62, 65], 1.6, 0.18, 0.5, 1.0), 1.0, 0.0, 0.5)
a_('musica', 0.0, coro([38, 45], 2.6, 1.3, 0.3, 1.0, vocale=(500, 900, 2400)), 0.9, 0.0, 0.4)
POST.append(lambda: fermata(2.0, 0.40, ('musica',), 0.9))
a_('fx', 2.04, whoosh(0.18, 700, 8000, 0.9), 0.7, 0.0, 0.2)                              # lo zoom a scatto
for i, tt in enumerate(np.arange(2.38, 3.3, 0.165)): a_('fx', tt, squittio(0.5), 0.10, (-0.6, 0.6)[i % 2], 0.15)   # le dita dei piedi

# ── C · S06: gambe a vuoto, poi parte e riparte la musica (più forte di prima) ────────────────────────────────────────
n_g = idx(0.5); t_g = tarr(n_g)
a_('fx', 4.5, bp(saw_f(160 + 700 * (t_g / 0.5) ** 1.6) * (1 + np.sin(2 * np.pi * 26 * t_g)) * 0.5, 300, 4000) * np.minimum(1, t_g / 0.05) * 0.5, 0.5, 0.0, 0.1)
a_('fx', 4.5, riser(0.5, 300, 6000, 0.6), 0.5)
colpo(5.0, 1.0, 0.9, 0.4); stab(5.0, [38, 50, 57, 62, 66], 0.45, 0.8)
a_('fx', 5.04, whoosh(0.28, 300, 4500, 0.9, giu=True), 0.7, 0.0, 0.2)                    # passa accanto alla camera
for i in range(5): a_('batt', A1 - (5 - i) * S16, snare(0.3 + 0.17 * i), 0.6, 0.0, 0.2)          # rullata verso il downbeat

# ── D · S08–S13b: ritmo da trailer d'azione, un colpo per battito, i tagli sui colpi ──────────────────────────────────
groove(A1, 12.78, [DM, DM, BB, CM, DM], 'mezzo')
colpo(A1, 1.2, 1.0, 0.4); a_('fx', A1, inverso(0.5, 0.8), 0.6)
a_('fx', 5.74, legno_pezzi(0.55, 16, 1.0), 0.7, 0.0, 0.3); colpo(5.75, 0.6, 0.7, 0.3)                  # la cassa scoppia
a_('fx', 6.375, tintinnio(0.4), 0.7); a_('fx', 6.375, mazza_tac(), 0.6)                               # la sciabola in mano
a_('fx', 6.9, riser(0.1, 800, 6000, 0.5), 0.3)
a_('fx', 7.02, sciabola_shing(), 1.6, 0.0, 0.3); colpo(7.0, 0.5, 0.55); stab(7.0, [74, 62, 50], 0.25, 0.9)   # S09a sciabola
a_('fx', 7.33, tintinnio(0.55), 0.7)
colpo(7.5, 0.5, 0.5); a_('fx', 7.5, whoosh(0.33, 200, 1800, 0.9), 0.6); a_('fx', 7.83, mazza_tac(), 1.7, 0.0, 0.3); colpo(7.83, 0.6, 0.7)   # S09b
colpo(8.0, 0.5, 0.5); a_('fx', 8.2, frusta_crack(), 1.8, 0.0, 0.3); colpo(8.21, 0.7, 0.7)                  # S09c frusta
colpo(8.5, 0.5, 0.5); a_('fx', 8.625, arco_twang(), 1.6, 0.0, 0.2); a_('fx', 8.64, whoosh(0.36, 600, 5000, 0.9), 0.7)   # S09d arco
for i in range(8): a_('batt', 9.0 + i * 0.0625, tom(110 + 6 * i, 0.5 + 0.07 * i), 0.8, -0.4 + 0.1 * i, 0.2)           # S10 gli zoccoli
a_('fx', 9.0, riser(0.5, 200, 7000, 0.9), 0.8); colpo(9.5, 0.9, 0.9, 0.4)
a_('fx', 10.1, sciabola_shing(), 1.0, 0.0, 0.5); colpo(10.1, 0.7, 0.7); a_('fx', 10.12, mazza_tac(), 0.8)            # S11 lo scontro
a_('fx', 10.58, mazza_tac(), 1.2, 0.0, 0.3); colpo(10.58, 1.0, 1.0, 0.4)                                # cade rigido
a_('fx', 11.25, lp(noise(idx(0.3)), 1800, 2) * np.exp(-tarr(idx(0.3)) * 9) * 1.5, 0.8, 0.0, 0.4); colpo(11.25, 0.5, 0.6)   # S13a lampo
a_('fx', 11.0, riser(0.5, 300, 5000, 0.5), 0.45)
colpo(11.75, 0.6, 0.7); a_('fx', 11.75, mazza_tac(), 0.9)                                                # S13b la mazza
for u in np.sort(rng.random(24)) ** 0.9: a_('fx', 11.76 + 0.62 * u, pop_bolla(0.9), 0.55, float(rng.uniform(-0.7, 0.7)), 0.25)
POST.append(lambda: fermata(12.5, 0.30))                                                                                      # S14 · STOP

# ── E · S14: la Birra Grande, quasi in silenzio ───────────────────────────────────────────────────────────────────────
for i, tt in enumerate(np.arange(12.56, 13.32, 0.072)): a_('fx', tt, squittio(0.8), 0.22, 0.8 - 1.6 * ((i // 3) % 2), 0.1)
for i, tt in enumerate((12.62, 12.88, 13.12)): a_('fx', tt, whoosh(0.22, 500, 2800, 0.9), 0.5, 0.8 if i % 2 == 0 else -0.8, 0.1)
a_('fx', 13.38, boing(0.14, 1.0), 0.8); a_('fx', 13.50, boing(0.12, 1.0), 0.8)                         # la doppia presa
a_('fx', 13.56, boing(0.5, 1.0, giu=True), 0.7)                                                          # la sbandata
for tt in (13.6, 13.74, 13.9): a_('fx', tt, graffio() * 0.5, 0.35, 0.0, 0.1)
a_('fx', 14.1, inverso(0.4, 0.7), 0.7)

# ── F · S15–S20: il viaggio a raffica, ogni taglio un colpo, il sole cala; S20 la musica si spegne ───────────────────────
groove(A2, 17.0, [DM, DM], 'pieno', 1.0)
for tt, nn, tg in ((14.5, [69, 57, 45], 1.2), (15.0, [67, 55, 43], 0.8), (15.5, [65, 53, 41], 0.8), (16.0, [64, 52, 40], 0.8), (16.5, [62, 50, 38, 26], 1.2)):
    stab(tt, nn, 0.32, 0.9); colpo(tt, tg, 0.8 if tt in (14.5, 16.5) else 0.55, 0.3); a_('fx', tt - 0.02, whoosh(0.18, 600, 7000, 0.7), 0.5)
POST.append(lambda: rallenta(16.5, 17.95))
for tt, v in ((16.667, 0.35), (17.0, 0.55), (17.333, 0.8), (17.625, 1.0)):                               # i quattro tonfi della terra
    a_('fx', tt, sub_boom(38, 1.0, v), 0.85, 0.0, 0.3); a_('fx', tt, lp(noise(idx(0.5)), 600) * np.exp(-tarr(idx(0.5)) * 8) * v, 0.5, 0.0, 0.2)

# ── G · S21–S24: finto film dell'orrore ───────────────────────────────────────────────────────────────────────────────
nd = idx(5.4); td = tarr(nd)
dr = lp(saw(hz(26), nd) + 0.8 * saw(hz(32), nd, 0.3) + 0.5 * saw(hz(33), nd, 0.6), 420, 3) * (1 + 0.25 * np.sin(2 * np.pi * 4.7 * td))
a_('musica', 17.9, dr * np.minimum(1, td / 3.0) ** 2 * 0.22 * e_sw(nd, 3.0, 0.3), 0.8, 0.0, 0.4)
a_('musica', 19.0, coro([74, 75], 2.3, 1.8, 0.3, 1.0, vocale=(1500, 2300, 3500)), 0.3, 0.0, 0.6)
for tt in np.arange(18.0, 20.6, 0.5):
    v = 0.7 + 0.07 * int((tt - 18.0) / 0.5)
    a_('fx', tt, sub_boom(40, 1.2, v), 0.8, 0.0, 0.3); a_('batt', tt, kick(0.8, 1.2), 0.7); KICK_T.append(tt)
    a_('fx', tt + 0.02, lp(noise(idx(0.6)), 500) * np.exp(-tarr(idx(0.6)) * 6) * 0.7, 0.5, 0.0, 0.3)
a_('fx', 20.15, sub_boom(60, 0.5, 0.6), 0.6); a_('fx', 20.2, boing(0.2, 0.8), 0.45)                       # la gamba fuori passo rientra
a_('fx', 20.6, riser(0.7, 120, 2500, 0.9), 0.5)
a_('fx', 21.3, ruggito(1.1, 1.0), 0.95, 0.0, 0.35); a_('fx', 21.3, sub_boom(36, 1.6, 1.0), 0.8)              # S23 ruggito
a_('fx', 21.55, hp(noise(idx(0.7)), 5000) * np.sin(np.pi * tarr(idx(0.7)) / 0.7) ** 2, 0.18, 0.0, 0.3)      # il vapore
colpo(21.0, 0.6, 0.6)
stab(22.5, [38, 50, 62, 66, 69], 1.0, 0.95, tenue=True); colpo(22.5, 1.4, 1.0, 0.5)                   # S24 si impenna
a_('fx', 22.9, tintinnio(0.6), 0.8); a_('fx', 22.85, whoosh(0.2, 1000, 9000, 0.7), 0.4)
a_('fx', 22.55, riser(0.95, 150, 9000, 1.0), 0.85); a_('fx', 22.7, inverso(0.8, 0.6), 0.5)

# ── H · S25–S27: la carica, il morso a vuoto, il salto ────────────────────────────────────────────────────────────────
groove(A3, 24.625, [DM, DM], 'carica', 1.0)
colpo(A3, 1.4, 1.0, 0.4)
for tt, nn in ((A3 + 0.0, [62, 69, 74]), (A3 + 0.72, [65, 72, 77]), (A3 + 1.0, [69, 76, 81])): stab(tt, nn, 0.4, 0.85, tenue=True)
for B_ in ('batt', 'basso', 'musica'):
    B[B_].d[:, idx(24.625):] = 0
a_('fx', 24.625, schiocco_morso(), 1.0, 0.0, 0.2); colpo(24.625, 0.6, 0.9, 0.3)                          # SNAP
a_('fx', 24.92, tosse(), 1.7, 0.0, 0.2)                                                                  # la tosse
a_('fx', 25.15, boing(0.45, 0.7, giu=True), 0.35)                                                        # il «ouch» del Boss
a_('fx', 25.2, inverso(0.3, 0.9), 0.7); colpo(25.5, 1.1, 0.9, 0.5)                                       # S27 il salto
a_('musica', 25.5, coro([50, 57, 62, 65, 69, 74], 2.0, 0.35, 0.9, 1.0), 1.1, 0.0, 0.8)
a_('musica', 25.5, coro([38, 45], 2.0, 0.3, 0.9, 1.0, vocale=(500, 900, 2400)), 0.9, 0.0, 0.6)
a_('fx', 25.55, whoosh(0.95, 200, 3000, 0.7, giu=True), 0.4, 0.0, 0.3)
POST.append(lambda: fermata(26.5, 0.45, ('musica', 'fx'), 0.7))                                                                # il fermo immagine

# ── J · coda: nero e silenzio, poi la birra ───────────────────────────────────────────────────────────────────────────
for i, tt in enumerate(np.arange(29.02, 29.82, 0.065)): a_('fx', tt, squittio(0.7), 0.4, -0.9 + 1.8 * (tt - 29.0) / 0.8, 0.12)
a_('fx', 29.30, whoosh(0.5, 300, 2600, 0.9), 0.55, 0.0, 0.1)
a_('fx', 29.62, tintinnio(0.6), 2.8, 0.0, 0.1)

# ══ MIX E MASTER ═════════════════════════════════════════════════════════════════════════════════════════════════════════
side = np.ones(N)
for kt in KICK_T:
    a = idx(kt); b = min(N, a + idx(0.35))
    if a < N: side[a:b] = np.minimum(side[a:b], 1 - 0.55 * np.exp(-np.arange(b - a) / SR / 0.11))
for k in ('basso', 'musica'): B[k].d *= side
duck = curva_gain([(0, 1), (10.09, 1), (10.14, 0.18), (10.56, 0.18), (10.6, 1), (11.45, 1), (11.55, 0.55), (12.5, 0.55)])   # S11 rallentatore, S13b piano
for k in ('batt', 'basso', 'musica'): B[k].d *= duck
hd = np.ones(N)
for th, dp in HIT_T:
    i0 = idx(th); i1 = min(N, i0 + idx(0.3))
    if i0 < N: hd[i0:i1] = np.minimum(hd[i0:i1], 1 - dp * np.exp(-np.arange(i1 - i0) / SR / 0.09))
for k in ('batt', 'basso', 'musica'): B[k].d *= hd
for f in POST: f()                                  # gli STOP e lo spegnimento di S20 lavorano sul suono già abbassato
B['verb'].d = riverbero(B['verb'].d, 2.0, 1.0)
chiusura = curva_gain([(0, 1), (27.15, 1), (27.45, 0.0), (28.9, 0.0), (29.0, 1.0), (29.88, 1.0), (30, 0.0)])
stems = {k: B[k].d * chiusura for k in B}
stems['fx'] = B['fx'].d * chiusura
master = (stems['batt'] * 0.75 + stems['basso'] * 0.75 + stems['musica'] * 0.65 + stems['fx'] * 1.0 + stems['verb'] * 1.0)
master = np.tanh(master * 0.5 * 1.2) / 1.2                  # sommati i bus, un taglio morbido dei picchi; il volume vero si mette dopo (loudnorm)
for k in stems: stems[k] = stems[k] * 0.5

def scrivi(path, x, g=1.0):
    y = np.clip(x * g, -1, 1); pcm = (y.T * 32767).astype('<i2')
    with wave.open(path, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ══ LA GUIDA MIDI (per Ableton) ══════════════════════════════════════════════════════════════════════════════════════
def vlq(v):
    out = [v & 0x7F]; v >>= 7
    while v: out.append((v & 0x7F) | 0x80); v >>= 7
    return bytes(reversed(out))
def traccia_midi(eventi):
    eventi.sort(key=lambda e: (e[0], e[1])); out = b''; ultimo = 0
    for tick, _, dati in eventi: out += vlq(tick - ultimo) + dati; ultimo = tick
    out += vlq(0) + b'\xFF\x2F\x00'; return b'MTrk' + struct.pack('>I', len(out)) + out
def scrivi_midi(path, testo):
    PPQ = 960; tk = lambda t: int(round(t * BPM / 60.0 * PPQ))
    t0 = [(0, 0, b'\xFF\x51\x03' + struct.pack('>I', int(60e6 / BPM))[1:]), (0, 0, b'\xFF\x58\x04\x04\x02\x18\x08')]
    for nome, tt, nota in testo: t0.append((tk(tt), 1, b'\xFF\x06' + vlq(len(nota.encode())) + nota.encode()))
    click = []; b = 0
    while b * BEAT < DUR:
        tick = tk(b * BEAT); n = 36 if b % 4 == 0 else 37
        click += [(tick, 1, bytes([0x99, n, 100 if b % 4 == 0 else 70])), (tick + 120, 0, bytes([0x89, n, 0]))]; b += 1
    cuts = []
    for nome, tt in TAGLI:
        tick = tk(tt); cuts += [(tick, 1, bytes([0x90, 60, 110])), (tick + 240, 0, bytes([0x80, 60, 0]))]
    trk = lambda nome, ev: [(0, 0, b'\xFF\x03' + vlq(len(nome)) + nome.encode())] + ev
    dati = struct.pack('>HHH', 1, 3, PPQ)
    with open(path, 'wb') as f:
        f.write(b'MThd' + struct.pack('>I', 6) + dati)
        f.write(traccia_midi(trk('Tempo e cue', t0))); f.write(traccia_midi(trk('Click 165', click))); f.write(traccia_midi(trk('Tagli', cuts)))

CUE = [
    ('S03', 0.0, 'cori in Re minore, boato lontano; cresce'), ('S04', 2.0, 'STOP (nastro che si ferma, disco che gratta); zoom a scatto; dita dei piedi'),
    ('S05', 3.5, 'SILENZIO'), ('S06', 4.5, 'gambe a vuoto (ronzio che sale); 5,0 la musica riparte più forte, whoosh'),
    ('S08', 5.5, 'DOWNBEAT 1 (frase 1, mezzo tempo): cassa che scoppia 5,75; presa della sciabola 6,375'),
    ('S09a', 7.0, 'sciabola: shing + stab; scintilla 7,33'), ('S09b', 7.5, 'mazza: giro, TAC a 7,83'), ('S09c', 8.0, 'frusta: SCHIOCCO a 8,21'),
    ('S09d', 8.5, 'arco: twang a 8,625, freccia'), ('S10', 9.0, 'zoccoli (tom) + riser'), ('S11', 9.5, 'scontro a 10,1; rallentatore (musica giù); cade rigido a 10,58'),
    ('S13a', 11.0, 'rotolo; lampo 11,25'), ('S13b', 11.5, 'mazza a 11,75; bolle che scoppiano a catena fino a ~12,4 (musica bassa)'),
    ('S14', 12.5, 'STOP; birra sui pattini (squittii), doppia presa 13,4–13,5, sbandata 13,5–14; riser dalle 14,1'),
    ('S15', 14.5, 'DOWNBEAT 2 (frase 2, cassa su ogni battito): stab La'), ('S16', 15.0, 'stab Sol'), ('S18', 15.5, 'stab Fa'), ('S19', 16.0, 'stab Mi'),
    ('S20', 16.5, 'stab Re grave, poi la musica si spegne (nastro che rallenta); tonfi della terra a 16,67 · 17,0 · 17,33 · 17,63'),
    ('S21', 18.0, 'orrore finto: bordone, un tonfo ogni mezzo secondo (18,0 … 20,5)'), ('S22', 19.0, 'tonfi; gamba fuori passo 20,0–20,3'),
    ('S23', 21.0, 'riser; ruggito 21,3–22,4; vapore'), ('S24', 22.5, 'colpo d\'orchestra, riser; scintilla della lama 22,9'),
    ('S25', 23.5, 'DOWNBEAT 3 (frase 3, la carica): ottoni'), ('S26', 24.5, 'SNAP 24,625 (tutto si ferma), tosse 24,92'),
    ('S27', 25.5, 'salto al rallentatore: cori, reverse, boato di sub'), ('fermo', 26.5, 'fermo immagine: STOP (nastro che si ferma), la coda di riverbero si spegne entro 27,45'),
    ('nero', 27.5, 'silenzio assoluto fino a 29,0 (i titoli)'),
    ('S28', 29.0, 'la birra sui pattini attraversa il nero; tintinnio a 29,62')]

if __name__ == '__main__':
    out = os.path.abspath(sys.argv[1]); os.makedirs(os.path.join(out, 'stem'), exist_ok=True)
    pk = float(np.max(np.abs(master)))
    scrivi(os.path.join(out, 'grezzo-master.wav'), master, 1.0)
    for k, v in stems.items(): scrivi(os.path.join(out, 'stem', 'stem-%s.wav' % k), v, 1.0)
    scrivi_midi(os.path.join(out, 'guida-165bpm.mid'), [(n, t, '%s %.2f s: %s' % (n, t, c)) for (n, t), (_, _, c) in zip(TAGLI, CUE)])
    # il volume vero: guadagno STATICO fino a -12 LUFS integrati (mantiene la dinamica), picco vero non oltre -1,5 dBTP
    import subprocess, re
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', os.path.join(out, 'grezzo-master.wav'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    lufs = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
    gdb = min(-12.0 - lufs, -1.5 - tp)
    for src, dst in [(os.path.join(out, 'grezzo-master.wav'), os.path.join(out, 'trailer-30s-musica-bozza.wav'))] + [(os.path.join(out, 'stem', 'stem-%s.wav' % k), os.path.join(out, 'stem', 'stem-%s.wav' % k)) for k in stems]:
        tmp = dst + '.tmp.wav'; subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af', 'volume=%.2fdB' % gdb, '-c:a', 'pcm_s16le', tmp], check=True); os.replace(tmp, dst)
    os.remove(os.path.join(out, 'grezzo-master.wav'))
    # il cue sheet: ogni taglio, dove cade sulla griglia a 165 BPM (rispetto al downbeat della sua frase) e cosa fa la musica
    righe = ['# Cue sheet della musica a 165 BPM', '',
             '1 s = 2,75 battiti, 4 s = 11 battiti esatti; battito = %.4f s = %.2f fotogrammi, semicroma = %.2f fotogrammi.' % (BEAT, BEAT * 24, S16 * 24),
             'Le frasi ripartono su un taglio: **downbeat 1 = 5,5 s (S08), downbeat 2 = 14,5 s (S15), downbeat 3 = 23,5 s (S25)**. «Scarto» = quanto il taglio',
             'cade lontano dalla semicroma più vicina della sua frase, in fotogrammi (0 = esattamente sulla griglia, ±1 = un fotogramma, che a video non si nota).', '',
             '| Shot | Taglio (s) | Fotogramma | Battiti dal downbeat | Scarto (fotogrammi) | La musica |', '|---|---|---|---|---|---|']
    for (nome, tt), (_, _, c) in zip(TAGLI, CUE):
        anc = A3 if tt >= A3 else A2 if tt >= A2 else A1 if tt >= A1 else 0.0
        bt = (tt - anc) / BEAT; sc = (bt * 4 - round(bt * 4)) * S16 * 24
        righe.append('| %s | %.2f | %d | %.3f | %+.1f | %s |' % (nome, tt, round(tt * 24), bt, sc, c))
    righe += ['', '## In Ableton', '- Imposta il tempo a **165** e importa `guida-165bpm.mid` all\'inizio del brano: la traccia «Tempo e cue» ha i marcatori (nome shot e istante), «Click 165» un colpo a ogni battito (più forte sul primo di ogni battuta) e «Tagli» una nota a ogni taglio.',
              '- Il video parte dal secondo 0 = battuta 1: nessun offset. Le frasi 2 e 3 non cadono su una battuta intera (14,5 s = battito 39,875; 23,5 s = battito 64,625): se vuoi le battute allineate, sposta il downbeat della frase sul taglio e lascia che la griglia scorra (è ciò che fa la bozza).',
              '- `trailer-30s-musica-bozza.wav` è la bozza sintetizzata (tutto da numpy, `tools/trailer3d/musica165.py`): serve per sentire i tempi, i suoni veri si rifanno. `stem/` ha batteria, basso, musica, effetti e riverbero separati, sommati danno il master.',
              '- Loudness della bozza: -12 LUFS al massimo, guadagno statico (la dinamica resta); non è mixata come un master.']
    open(os.path.join(out, 'CUE.md'), 'w').write('\n'.join(righe) + '\n')
    print('SCRITTO', out, 'grezzo %.1f LUFS, picco vero %.1f dBFS → guadagno %.2f dB' % (lufs, tp, gdb))
    muto = os.path.join(os.path.dirname(out), 'trailer-30s-muto.mp4')
    if os.path.exists(muto):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', muto, '-i', os.path.join(out, 'trailer-30s-musica-bozza.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', os.path.join(os.path.dirname(out), 'trailer-30s-musica.mp4')], check=True)
        print('VIDEO', os.path.join(os.path.dirname(out), 'trailer-30s-musica.mp4'))
