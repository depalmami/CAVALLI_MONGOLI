"""Colonna sonora del trailer d'azione — versione IBRIDA DURA (30 s, 120 BPM in mezzo tempo, Re minore).
Tutta sintetizzata, niente campioni. I tempi vengono da mappa.py, gli stessi del montaggio.

Suoni: cassa e rullante «ibridi» enormi, charleston, tom; bassi distorti GROWL (oscillatori ricchi → due filtri
formanti che si spostano fra le vocali u/o/a/e/i → saturazione, più il sub un'ottava sotto); REESE per i tappeti;
SUB DROP; BRAAM ibridi (ottoni saturi + growl + sub); riser, risucchi, ringhio, schiocco finale.
Il basso «pompa» sotto la cassa (sidechain). Prima di ogni drop: un silenzio secco.
uso: python musica.py uscita.wav
"""
import sys, os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mappa import BEAT, DUR, HIT, IMPATTI, CARTELLO3, RAFFICA4, RAFFICA8

SR = 48000
N = int(SR * DUR)
T = np.arange(N) / SR
rng = np.random.default_rng(23)
SEDICESIMO = BEAT / 4                 # 0,125 s
BATTUTA = BEAT * 4                    # 2 s


# ── attrezzi ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def lp(x, f, o=4): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, min(hi, SR / 2 - 100)], 'band', fs=SR, output='sos'), x)


def tv_filter(x, design, n_blk=256):
    """Filtro che cambia nel tempo, con lo stato portato da un blocco all'altro (niente click)."""
    x = np.atleast_2d(x)
    y = np.zeros_like(x)
    zi = None
    for i in range(0, x.shape[1], n_blk):
        sos = design(i)
        if zi is None:
            zi = np.zeros((x.shape[0], sos.shape[0], 2))
        for ch in range(x.shape[0]):
            y[ch, i:i + n_blk], zi[ch] = sosfilt(sos, x[ch, i:i + n_blk], zi=zi[ch])
    return y


def saw(f, t, phase=0.0):
    return 2 * ((f * t + phase) % 1.0) - 1


def saw_var(freq, phase=0.0):
    return 2 * ((np.cumsum(freq) / SR + phase) % 1.0) - 1


def env_ad(n, a, d, curve=4.0):
    t = np.arange(n) / SR
    return np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) * curve / d))


def st(x, pan=0.0, delay_ms=0.0):
    d = int(delay_ms * SR / 1000)
    l = x * np.sqrt(0.5 * (1 - pan))
    r = x * np.sqrt(0.5 * (1 + pan))
    if d:
        r = np.concatenate([np.zeros(d), r[:len(r) - d]])
    return np.vstack([l, r]) * 1.41


def place(buf, sig, at, g=1.0):
    if sig.ndim == 1:
        sig = st(sig)
    i = int(round(at * SR))
    j0 = max(0, -i)
    i = max(0, i)
    j = min(N, i + sig.shape[1] - j0)
    if i < N and j > i:
        buf[:, i:j] += sig[:, j0:j0 + (j - i)] * g


def reverb_ir(sec=2.4, seed=1, lpf=6500):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = np.vstack([r.standard_normal(n), r.standard_normal(n)]) * np.exp(-t * 6.9 / sec)
    ir = np.vstack([lp(ir[0], lpf), lp(ir[1], lpf)])
    ir[:, :int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    return ir / np.abs(ir).sum(axis=1, keepdims=True) * 38


IR_STANZA = reverb_ir(1.1, seed=2, lpf=8000)
IR_GRANDE = reverb_ir(4.0, seed=3, lpf=5000)


def verb(x2, ir):
    return np.vstack([fftconvolve(x2[0], ir[0])[:x2.shape[1]], fftconvolve(x2[1], ir[1])[:x2.shape[1]]])


def gate(a, b, fade=0.008):
    return np.clip((T - a) / fade, 0, 1) * np.clip((b - T) / fade, 0, 1)


# note
D1, D2 = 36.71, 73.42
def nota(semi, base=D2): return base * 2 ** (semi / 12)


# ── batteria ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def cassa(g=1.0, lunga=False):
    n = int((0.7 if lunga else 0.42) * SR)
    t = np.arange(n) / SR
    f = 44 + 130 * np.exp(-t * 38)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4.5 if lunga else 8))
    click = bp(rng.standard_normal(n), 2000, 9000) * np.exp(-t * 220) * 0.5
    return np.tanh((corpo * 1.6 + click) * 2.2) * 0.62 * g


def rullante(g=1.0, tono=1.0):
    """Rullante ibrido: corpo + rumore + battimani a tre colpi + schiocco."""
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    corpo = np.sin(2 * np.pi * np.cumsum(195 * tono + 60 * np.exp(-t * 40)) / SR) * np.exp(-t * 16)
    fruscio = bp(nz, 1800, 10000) * np.exp(-t * 13)
    mani = np.zeros(n)
    for k, d in enumerate((0.0, 0.009, 0.019)):
        i = int(d * SR)
        m = bp(rng.standard_normal(n - i), 900, 3200) * np.exp(-np.arange(n - i) / SR * (90 if k < 2 else 28))
        mani[i:] += m * (0.6 if k < 2 else 1.0)
    schiocco = bp(nz, 3000, 12000) * np.exp(-t * 300)
    y = corpo * 0.9 + fruscio * 0.7 + mani * 0.8 + schiocco * 0.5
    return np.tanh(y * 1.8) * 0.5 * g


def charleston(g=1.0, aperto=False):
    n = int((0.22 if aperto else 0.06) * SR)
    t = np.arange(n) / SR
    y = hp(rng.standard_normal(n), 7500, 4) * np.exp(-t * (18 if aperto else 70))
    return y * 0.16 * g


def tom(pitch=1.0, g=1.0):
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = (95 + 110 * np.exp(-t * 26)) * pitch
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    skin = bp(rng.standard_normal(n), 150, 2500) * np.exp(-t * 35)
    return np.tanh((body * 1.3 + skin * 0.5) * 1.6) * 0.45 * g


def boom(dur=3.0, f0=110, f1=30, crack=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    body = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4) * 2.4)
    nz = rng.standard_normal(n)
    click = bp(nz, 1500, 9000) * np.exp(-t * 55) * crack
    thump = lp(nz, 300) * np.exp(-t * 13) * 2.0
    crash = bp(nz, 3000, 14000) * np.exp(-t * 3.5) * 0.25 * crack
    return st(body + click * 0.6 + thump * 0.5 + crash, 0, 9) * 0.6


def sub_drop(dur=1.6, f0=95, f1=27):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 3.2)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 1.8) * np.exp(-t * 1.6) * 0.7


# ── bassi ────────────────────────────────────────────────────────────────────────────────────────────────────────────
VOC = {'u': (320, 800), 'o': (480, 950), 'a': (780, 1250), 'e': (520, 1850), 'i': (330, 2350)}


def growl(dur, f, v0='o', v1='a', forma='wub', lfo=8.0, drive=3.2, glide=0.0, sub=1.0):
    """Basso distorto che «parla»: oscillatori ricchi → due formanti che vanno da una vocale all'altra → saturazione.
    forma: wub (l'LFO va avanti e indietro a `lfo` Hz), yoi (si apre una volta), saw (riparte a ogni ciclo), fisso."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * 2 ** (glide * (t / dur) / 12)
    x = saw_var(fr) + 0.6 * saw_var(fr * 1.0071, 0.33) + 0.45 * np.sign(np.sin(2 * np.pi * np.cumsum(fr * 0.5) / SR))
    if forma == 'wub':
        l = 0.5 - 0.5 * np.cos(2 * np.pi * lfo * t)
    elif forma == 'yoi':
        l = np.clip(t / dur * 1.4, 0, 1) ** 0.55
    elif forma == 'saw':
        l = 1 - (lfo * t) % 1.0
    else:
        l = np.full(n, 0.6)
    A, B = VOC[v0], VOC[v1]
    c1 = A[0] + (B[0] - A[0]) * l
    c2 = A[1] + (B[1] - A[1]) * l
    f1 = tv_filter(x, lambda i: butter(2, [float(c1[min(i, n - 1)]) * 0.72, float(c1[min(i, n - 1)]) * 1.35], 'band', fs=SR, output='sos'), 96)[0]
    f2 = tv_filter(x, lambda i: butter(2, [float(c2[min(i, n - 1)]) * 0.8, float(c2[min(i, n - 1)]) * 1.25], 'band', fs=SR, output='sos'), 96)[0]
    y = f1 * 1.3 + f2 * 0.9 + lp(x, 160) * 0.5
    y = np.tanh(y * drive)
    y = lp(np.tanh(hp(y, 60) * 1.6), 7500)
    e = np.clip(t / 0.005, 0, 1) * np.clip((dur - t) / 0.01, 0, 1)
    s = np.sin(2 * np.pi * np.cumsum(fr * 0.5) / SR) * sub
    cima = hp(y, 1200)
    d = int(0.011 * SR)
    l_ = (y * 0.75 + s * 0.55) * e
    r_ = l_.copy()
    r_[d:] += cima[:-d] * e[d:] * 0.35            # un velo di larghezza solo in alto: il basso resta al centro
    l_ += cima * e * 0.35
    return np.vstack([l_, r_]) * 0.5


def reese(dur, f, apertura=(250, 650), g=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros((2, n))
    for k, det in enumerate((-0.0075, -0.0025, 0.0025, 0.0075)):
        s = saw(f * (1 + det), t, rng.random())
        x[k % 2] += s
        x[1 - k % 2] += s * 0.5
    cut = apertura[0] + (apertura[1] - apertura[0]) * (0.5 - 0.5 * np.cos(2 * np.pi * 0.25 * t))
    y = tv_filter(x, lambda i: butter(2, float(cut[min(i, n - 1)]), 'low', fs=SR, output='sos'))
    y = np.tanh(y * 1.6)
    s = np.sin(2 * np.pi * f * 0.5 * t)
    y += np.vstack([s, s]) * 0.6
    e = np.clip(t / 1.2, 0, 1) * np.clip((dur - t) / 0.15, 0, 1)
    return y * e * 0.16 * g


def braam(dur=2.4, root=D1, bright=1.0, minore=True):
    """Ottoni saturi col filtro che si apre e si richiude, più un growl e il sub: il BRAAM ibrido."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    terza = 1.189 if minore else 1.26
    x = np.zeros((2, n))
    for f, a in zip([root, root * 2, root * 3, root * 4, root * 2 * terza, root * 6], [1.0, 0.9, 0.65, 0.5, 0.45, 0.28]):
        for det in (-0.006, -0.002, 0.002, 0.006):
            s = saw(f * (1 + det), t, rng.random())
            ch = 0 if det < 0 else 1
            x[ch] += s * a
            x[1 - ch] += s * a * 0.6
    cut = 200 + 3200 * bright * np.exp(-t * 2.2) * np.clip(t / 0.05, 0, 1)
    y = tv_filter(x, lambda i: butter(2, float(cut[min(i, n - 1)]), 'low', fs=SR, output='sos'))
    y = np.tanh(y * 2.6) * env_ad(n, 0.02, dur * 0.6, 2.6)
    gr = growl(min(dur, 1.4), root * 2, 'u', 'a', 'yoi', drive=4.0)
    y[:, :gr.shape[1]] += gr * 1.1 * np.exp(-np.arange(gr.shape[1]) / SR * 1.2)
    sub = np.sin(2 * np.pi * root * t) * env_ad(n, 0.01, dur * 0.55, 3.0)
    return (y + np.vstack([sub, sub]) * 0.9) * 0.3


# ── effetti ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def riser(a, b, g=1.0):
    n = int((b - a) * SR)
    t = np.arange(n) / SR
    prog = t / t[-1]
    nz = rng.standard_normal(n)
    out = tv_filter(nz, lambda i: butter(2, [300 + 7000 * prog[min(i, n - 1)] ** 2.2 * 0.7,
                                             min((300 + 7000 * prog[min(i, n - 1)] ** 2.2) * 1.4, 20000)], 'band', fs=SR, output='sos'))[0]
    out *= prog ** 1.6
    sirena = np.tanh(2.5 * saw_var(D2 * 2 ** (prog * 2.5))) * prog ** 2
    sirena = lp(sirena, 3000) * 0.3
    return st((out * 0.55 + sirena) * 0.7 * g, 0, 11)


def risucchio(dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = bp(rng.standard_normal(n), 400, 8000) * np.exp(-t * 5)
    return verb(np.vstack([nz, nz]), IR_GRANDE)[:, ::-1] * 0.7


def ringhio(dur=0.7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 44 + 7 * np.sin(2 * np.pi * 3 * t)
    tono = np.tanh(3.5 * saw_var(f)) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    y = lp(tono, 420) + bp(rng.standard_normal(n), 120, 1000) * 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * 17 * t))
    e = np.clip(t / 0.25, 0, 1) ** 2 * np.clip((t[-1] - t) / 0.05, 0, 1)
    return st(y * e * 0.6, 0, 6)


def schiocco():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    legno = bp(nz, 300, 3500) * np.exp(-t * 45) * 1.4
    denti = bp(nz, 3000, 11000) * np.exp(-t * 80) * 0.6
    sub = np.sin(2 * np.pi * np.cumsum(30 + 80 * np.exp(-t * 10)) / SR) * np.exp(-t * 2.2)
    return st(np.tanh((legno + denti + sub * 1.3) * 1.7) * 0.6, 0, 5)


def tic(g=1.0, f=2300):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 150) + bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t * 300) * 0.3) * 0.25 * g


# ── buse ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
tamburi = np.zeros((2, N))    # stanza corta
bassi = np.zeros((2, N))      # asciutti, col sidechain della cassa
grandi = np.zeros((2, N))     # braam, impatti, effetti: riverbero lungo
casse = []                    # istanti delle casse, per il sidechain

def K(at, g=1.0, lunga=False):
    place(tamburi, st(cassa(g, lunga)), at); casse.append(at)

def S(at, g=1.0, tono=1.0):
    place(tamburi, st(rullante(g, tono)), at)

def Hh(at, g=1.0, aperto=False):
    place(tamburi, st(charleston(g, aperto), rng.uniform(-0.3, 0.3)), at)

def G(at, passi, semi=0, **kw):
    place(bassi, growl(passi * SEDICESIMO, nota(semi), **kw), at)


A2, FINE2 = HIT['azione'], HIT['fine_azione']

# ATTO 1 ─ tappeto reese, cuore, orologio, due BRAAM, la salita col rullante ─────────────────────────────────────────
place(grandi, boom(2.5, 80, 28, 0.4), 0.0, 0.9)
place(bassi, reese(A2 - 0.1, D1 * 2, (180, 520), g=1.0), 0.0)
for k, at in enumerate(np.arange(0.5, 2.0, 1.0)):             # il cuore: due tonfi
    K(at, 0.35); K(at + 0.16, 0.25)
for at in np.arange(2.0, 6.0, BEAT):
    K(at, 0.35 + 0.25 * (at - 2) / 4); K(at + 0.16, 0.22 + 0.15 * (at - 2) / 4)
for k, at in enumerate(np.arange(0.5, 6.9, BEAT)):
    place(tamburi, st(tic(0.6 + 0.6 * at / 7, 2300 if k % 2 == 0 else 1950), 0.3 * (-1) ** k), at)
for k, at in enumerate(np.arange(4.5, 6.9, BEAT / 2)):
    place(tamburi, st(tic(0.5, 2900), -0.2), at + BEAT / 4)
place(grandi, braam(2.6, D1, 1.0), HIT['braam1'], 1.1)
place(grandi, boom(2.2, 110, 30, 0.9), HIT['braam1'])
place(grandi, st(sub_drop(1.5)), HIT['braam1'], 0.8)
place(grandi, braam(2.2, D1 * 2 ** (1 / 12), 1.1), HIT['braam2'], 1.1)       # Mib: mezzo tono più su
place(grandi, boom(2.0, 110, 30, 0.9), HIT['braam2'])
place(grandi, st(sub_drop(1.3)), HIT['braam2'], 0.8)
for c in (HIT['cartello1'], HIT['cartello2']):                  # i cartelli: colpo secco
    S(c, 0.9, 0.8); K(c, 0.8); place(grandi, boom(1.4, 90, 30, 0.6), c, 0.5)
place(grandi, riser(*HIT['riser1'], g=1.1), HIT['riser1'][0])
for k, at in enumerate(np.arange(6.0, 6.9, BEAT / 2)):          # la rullata che stringe: crome, poi semicrome
    S(at, 0.35 + 0.3 * k / 4, 1.0 + 0.05 * k)
for k, at in enumerate(np.arange(6.5, 6.9, SEDICESIMO / 2)):
    S(at, 0.45 + 0.1 * k, 1.2 + 0.04 * k)

# ATTO 2 ─ il drop: mezzo tempo, growl, cassa che spinge ────────────────────────────────────────────────────────────
# battuta (16 sedicesimi): cassa 0, 3, 10 · rullante 8 · charleston sui levare · growl a domanda e risposta
PAT_A = [(0, 3, 0, dict(v0='o', v1='a', forma='wub', lfo=8)), (4, 2, 0, dict(v0='u', v1='i', forma='yoi')),
         (6, 2, 3, dict(v0='a', v1='o', forma='yoi')), (10, 4, 0, dict(v0='o', v1='e', forma='wub', lfo=16)),
         (14, 2, 12, dict(v0='a', v1='i', forma='yoi'))]
PAT_B = [(0, 2, 0, dict(v0='o', v1='a', forma='wub', lfo=8)), (2, 1, 0, dict(v0='u', v1='a', forma='yoi')),
         (3, 1, 0, dict(v0='u', v1='a', forma='yoi')), (4, 4, -2, dict(v0='o', v1='a', forma='saw', lfo=6)),
         (10, 2, 0, dict(v0='e', v1='o', forma='wub', lfo=16)), (12, 2, 3, dict(v0='u', v1='i', forma='yoi')),
         (14, 2, 0, dict(v0='o', v1='i', forma='yoi', glide=12))]


def battuta_drop(t0, pat, fino=None, fill=False, piena=False):
    fine = t0 + BATTUTA if fino is None else fino
    for s in (0, 3, 10):
        if t0 + s * SEDICESIMO < fine - 0.01:
            K(t0 + s * SEDICESIMO, 1.0 if s == 0 else 0.8)
    if t0 + 8 * SEDICESIMO < fine - 0.01:
        S(t0 + 8 * SEDICESIMO, 1.0)
    for s in range(2, 16, 4 if not piena else 2):
        if t0 + s * SEDICESIMO < fine - 0.01:
            Hh(t0 + s * SEDICESIMO, 0.9 if s % 4 == 2 else 0.5, aperto=(s % 8 == 6))
    for s, l, semi, kw in pat:
        a = t0 + s * SEDICESIMO
        if a < fine - 0.02:
            passi = min(l, (fine - a) / SEDICESIMO)
            G(a, passi, semi, **kw)
    if fill:
        for k, s in enumerate((12, 13, 14, 15)):
            if t0 + s * SEDICESIMO < fine - 0.01:
                place(tamburi, st(tom(1.3 - 0.12 * k, 0.9), 0.4 * (-1) ** k), t0 + s * SEDICESIMO)


battuta_drop(7.0, PAT_A)
battuta_drop(9.0, PAT_A, fino=CARTELLO3[0], fill=False)
battuta_drop(11.5, PAT_B, piena=True)
battuta_drop(13.5, PAT_A, piena=True, fill=True)
battuta_drop(15.5, PAT_B, fino=RAFFICA4[0], piena=True)
place(grandi, braam(2.4, D1, 1.2), A2, 1.2)
place(grandi, st(sub_drop(1.8, 110, 26)), A2, 1.0)
place(grandi, braam(2.0, D1 * 2 ** (-4 / 12) * 2 / 2, 1.1), 11.5, 1.0)       # Sib
place(grandi, st(sub_drop(1.4)), 11.5, 0.8)
for at in IMPATTI:
    place(grandi, boom(1.6, 120, 30, 1.0), at, 0.8 if at != A2 else 1.1)
# cartello 3: tutto tace di colpo, resta il tappeto e l'orologio, poi il risucchio verso il rientro
place(bassi, reese(CARTELLO3[1] - CARTELLO3[0], D1 * 2, (150, 380), g=1.3), CARTELLO3[0])
for k, at in enumerate(np.arange(CARTELLO3[0] + 0.125, CARTELLO3[1] - 0.05, BEAT / 2)):
    place(tamburi, st(tic(0.9, 2300 if k % 2 == 0 else 1950)), at)
sw = risucchio(0.6); place(grandi, sw * 0.8, CARTELLO3[1] - sw.shape[1] / SR)
# raffica: semiminime (cassa + rullante + growl secco), poi crome che salgono, poi rullata a semicrome
for i in range(4):
    a = RAFFICA4[0] + i * BEAT
    K(a, 1.0); S(a, 0.9); G(a, 3, [0, 3, 5, 7][i], v0='o', v1=['a', 'i', 'e', 'a'][i], forma='yoi', drive=4)
for i in range(8):
    a = RAFFICA8[0] + i * BEAT / 2
    K(a, 0.9); S(a + BEAT / 4, 0.6 + 0.04 * i, 1.0 + 0.04 * i); G(a, 2, i, v0='u', v1='a', forma='yoi', drive=4)
for i in range(6):
    a = 18.0 + i * SEDICESIMO
    S(a, 0.6 + 0.07 * i, 1.15 + 0.05 * i); K(a, 0.5)
G(18.0, 6, 0, v0='o', v1='i', forma='wub', lfo=24, glide=12, drive=4.5)
place(grandi, riser(16.0, FINE2, g=1.3), 16.0)

# BUCO ─ silenzio secco, il ringhio, il risucchio ──────────────────────────────────────────────────────────────────
# ATTO 3 ─ il Boss: ancora più lento e più basso ──────────────────────────────────────────────────────────────────
PAT_BOSS = [(0, 6, -12, dict(v0='u', v1='a', forma='wub', lfo=4)), (8, 4, -11, dict(v0='o', v1='e', forma='wub', lfo=3)),
            (12, 2, -12, dict(v0='u', v1='i', forma='yoi')), (14, 2, 0, dict(v0='a', v1='o', forma='yoi', glide=-12))]
for t0 in (19.5, 21.5):
    fine = min(t0 + BATTUTA, HIT['riser2'][0])
    K(t0, 1.0, lunga=True); K(t0 + 6 * SEDICESIMO, 0.7)
    S(t0 + 8 * SEDICESIMO, 1.0, 0.85)
    if t0 + 14 * SEDICESIMO < fine:
        K(t0 + 14 * SEDICESIMO, 0.8)
    for s, l, semi, kw in PAT_BOSS:
        a = t0 + s * SEDICESIMO
        if a < fine - 0.02:
            G(a, min(l, (fine - a) / SEDICESIMO), semi, drive=4.0, **kw)
place(grandi, braam(3.0, D1, 1.5), HIT['boss'], 1.35)
place(grandi, boom(3.0, 150, 26, 1.3), HIT['boss'], 1.25)
place(grandi, st(sub_drop(2.2, 120, 24)), HIT['boss'], 1.1)
place(grandi, braam(2.0, D1 * 2 ** (1 / 12), 1.2), HIT['boss2'], 1.0)          # Mib
place(grandi, braam(2.6, D1 * 2 ** (-4 / 12) * 2 / 2, 1.3), HIT['boss3'], 1.1)  # Sib
place(grandi, boom(1.8, 120, 30, 1.0), HIT['boss3'], 0.9)
# salita verso i tre colpi: growl a semicrome che accelera, rullata
a0, a1 = HIT['riser2']
for k, at in enumerate(np.arange(a0, a1 - 0.01, SEDICESIMO)):
    G(at, 0.8, k // 2, v0='u', v1='a', forma='yoi', drive=4)
    S(at, 0.4 + 0.5 * (at - a0) / (a1 - a0), 1.0 + 0.3 * (at - a0) / (a1 - a0))
place(grandi, riser(a0, a1, g=1.5), a0)
for i, at in enumerate(HIT['stutter']):
    K(at, 1.0, lunga=True); S(at, 1.0, 0.9 - 0.05 * i)
    place(grandi, boom(1.2, 130, 30, 1.2), at, 1.0 + 0.1 * i)
    G(at, 2.2, [0, 1, 3][i], v0='a', v1='u', forma='yoi', drive=4.5)

# TITOLO ─ il colpo più grande, poi un tappeto che trattiene il fiato ───────────────────────────────────────────────
TI = HIT['titolo']
K(TI, 1.2, lunga=True); S(TI, 1.0, 0.8)
place(grandi, braam(4.2, D1, 1.6), TI, 1.5)
place(grandi, boom(4.0, 160, 24, 1.5), TI, 1.5)
place(grandi, st(sub_drop(3.0, 130, 22)), TI, 1.3)
place(bassi, growl(1.6, D2, 'u', 'a', 'yoi', drive=4.5), TI, 1.1)
place(bassi, reese(HIT['scatto'] - TI - 1.0, D1 * 2, (140, 420), g=1.2), TI + 1.0)
for k, at in enumerate(np.arange(TI + 1.0, HIT['scatto'] - 0.2, 1.0)):     # il cuore torna, piano
    K(at, 0.35); K(at + 0.16, 0.22)
SC = HIT['scatto']
K(SC, 1.2, lunga=True); S(SC, 1.0, 0.75)
place(grandi, schiocco(), SC, 1.3)
place(grandi, boom(2.6, 100, 24, 1.1), SC, 1.2)
place(grandi, st(sub_drop(1.8, 100, 24)), SC, 1.0)
place(bassi, growl(0.6, D2, 'a', 'u', 'yoi', drive=4.5), SC, 1.0)
place(bassi, reese(DUR - SC, D1 * 2, (120, 300), g=0.9), SC)

# ── mix ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# sidechain: il basso si abbassa sotto ogni cassa e risale in ~120 ms
sc = np.ones(N)
for at in casse:
    i = int(at * SR)
    k = np.arange(min(int(0.3 * SR), N - i))
    sc[i:i + len(k)] = np.minimum(sc[i:i + len(k)], 1 - 0.65 * np.exp(-k / SR / 0.09))
bassi *= sc
mix = tamburi + verb(tamburi, IR_STANZA) * 0.18 + bassi * 0.95 + grandi * 0.85 + verb(grandi, IR_GRANDE) * 0.32

# silenzi secchi: prima del drop, prima del Boss, prima del titolo
for a, b in ((A2 - 0.10, A2), HIT['buco'], HIT['pre_titolo']):
    mix *= 1 - gate(a, b, 0.004)
# il cartello 3 lascia passare solo tappeto, orologio e risucchio (già messi): taglia le code dei tamburi
m3 = gate(CARTELLO3[0], CARTELLO3[1] - 0.6, 0.004)
mix -= (verb(tamburi, IR_STANZA) * 0.18) * m3 * 0.9
# nel buco: solo ringhio e risucchio
extra = np.zeros((2, N))
place(extra, ringhio(HIT['ringhio'][1] - HIT['ringhio'][0]), HIT['ringhio'][0], 1.2)
sw = risucchio(0.55); place(extra, sw * 0.9, HIT['boss'] - sw.shape[1] / SR)
sw = risucchio(0.3); place(extra, sw * 0.7, HIT['titolo'] - sw.shape[1] / SR)
mix += extra

# master: via il sotto-sonico, una spinta sui medi per i telefoni, limitatore morbido
out = np.vstack([hp(mix[0], 34), hp(mix[1], 34)])
presenza = np.vstack([bp(out[0], 900, 4000), bp(out[1], 900, 4000)])
out = out + presenza * 0.18
GUIDA = 3.2
out = out / np.abs(out).max() * GUIDA
out = np.tanh(out) / np.tanh(GUIDA)
k = int(0.5 * SR)
out[:, -k:] *= np.linspace(1, 0, k) ** 1.5
out *= 0.84 / np.abs(out).max()          # −1,5 dB: dopo l'AAC il picco vero resta sotto −1 dB
wavfile.write(sys.argv[1], SR, (out.T * 32767).astype(np.int16))
print('ok', out.shape, 'rms dBFS %.1f' % (20 * np.log10(np.sqrt((out ** 2).mean()))))
