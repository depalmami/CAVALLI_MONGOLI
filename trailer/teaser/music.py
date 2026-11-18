"""Colonna sonora del teaser (8 s): drone oscuro, BRAAM, sub-boom, riser, stutter, silenzio, impatto finale.
Mappa dei tempi (secondi di sequenza) condivisa con il montaggio."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
import sys

SR = 48000
DRONE_G = 0.05
DUR = 12.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR

HITS = dict(braam1=2.50, braam2=3.90, riser=(4.70, 7.40), stut=(7.40, 7.60, 7.80),
            gap=(8.00, 8.20), boom=8.20, vanish=266 / 30, final=10.00)


def lp(x, f, o=4):
    return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def tv_filter(x, design, n_blk=256):
    """Filtro tempo-variante con stato trasportato da un blocco all'altro (niente click)."""
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
    p = (f * t + phase) % 1.0
    return 2 * p - 1


def env_ad(n, a, d, curve=4.0):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) * curve / d))
    return e


def place(buf, sig, at):
    i = int(at * SR)
    j = min(N, i + sig.shape[-1])
    if i < N:
        buf[:, i:j] += sig[:, : j - i] if sig.ndim == 2 else sig[: j - i]


def stereo(x, width=0.0, delay_ms=0.0):
    d = int(delay_ms * SR / 1000)
    l = x.copy()
    r = np.concatenate([np.zeros(d), x[: len(x) - d]]) if d else x.copy()
    return np.vstack([l * (1 + width), r * (1 - width)])


def reverb_ir(sec=3.0, seed=1):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = np.vstack([r.standard_normal(n), r.standard_normal(n)]) * np.exp(-t * 6.9 / sec)
    ir = np.vstack([lp(ir[0], 6000), lp(ir[1], 6000)])
    ir[:, : int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    return ir / np.abs(ir).sum(axis=1, keepdims=True) * 40


IR = reverb_ir(3.2)


def verb(x2):
    return np.vstack([fftconvolve(x2[0], IR[0])[: x2.shape[1]], fftconvolve(x2[1], IR[1])[: x2.shape[1]]])


# --- 1. Drone: D1 + A1 + Eb2 (seconda minore, inquietante), respira con un LFO lento
def drone():
    t = t_all
    voices = [(36.71, 1.0), (55.0, 0.6), (77.78, 0.35), (73.42, 0.45)]
    out = np.zeros((2, N))
    for f, g in voices:
        for k, det in enumerate((-0.15, 0.0, 0.17)):
            s = saw(f * (1 + det / 100 * 3), t, phase=rng.random())
            pan = (k - 1) * 0.3
            out[0] += s * g * (1 - pan)
            out[1] += s * g * (1 + pan)
    cut = 180 + 120 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t))
    # filtro a tratti (cutoff variabile approssimato a blocchi)
    res = tv_filter(out, lambda i: butter(2, float(cut[i]), 'low', fs=SR, output='sos'))
    res = lp(res, 400)
    wind = bp(rng.standard_normal(N), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.21 * t + 1))
    res += np.vstack([wind, np.roll(wind, 900)]) * 0.12
    fade = np.clip(t / 1.2, 0, 1) ** 2
    # il drone si spegne nel buco di silenzio e rientra col boom
    g = np.ones(N)
    a, b = HITS['gap']
    g[int(a * SR) - 1200:int(b * SR)] = np.linspace(1, 0, int(b * SR) - int(a * SR) + 1200) ** 3
    g[int(a * SR):int(b * SR)] = 0
    return res * fade * g * DRONE_G


# --- 2. BRAAM: ottoni sintetici saturi, filtro che si apre
def braam(dur=2.4, root=36.71, bright=1.0, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    notes = [root, root * 2, root * 3, root * 4, root * 2 * 1.189, root * 6]  # D, D, A, D, F(minore), A
    amps = [1.0, 0.9, 0.6, 0.5, 0.45, 0.25]
    x = np.zeros((2, n))
    for f, a in zip(notes, amps):
        for det in (-0.004, -0.0015, 0.0015, 0.004):
            s = saw(f * (1 + det), t, rng.random())
            ch = 0 if det < 0 else 1
            x[ch] += s * a
            x[1 - ch] += s * a * 0.6
    e = env_ad(n, 0.025, dur * 0.55, curve=3.0)
    cut = 250 + 2600 * bright * np.exp(-t * 2.2) * np.clip(t / 0.06, 0, 1)
    y = tv_filter(x, lambda i: butter(2, float(cut[i]), 'low', fs=SR, output='sos'))
    y = np.tanh(y * 1.8) * e
    sub = np.sin(2 * np.pi * root * t) * env_ad(n, 0.01, dur * 0.5, 3.0)
    y += np.vstack([sub, sub]) * 0.9
    return y * gain * 0.35


# --- 3. Sub boom / impatto cinematografico
def boom(dur=3.0, f0=110, f1=32, gain=1.0, crack=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 1.5)
    body = np.tanh(body * 2.2)
    nz = rng.standard_normal(n)
    click = bp(nz, 1500, 9000) * np.exp(-t * 60) * crack
    thump = lp(nz, 300) * np.exp(-t * 14) * 2.0
    y = body + click * 0.6 + thump * 0.5
    return stereo(y, 0, 7) * gain * 0.6


# --- 4. Colpo stutter (taiko + metallo)
def hit(pitch=1.0, gain=1.0):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = (55 + 70 * np.exp(-t * 25)) * pitch
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    nz = rng.standard_normal(n)
    skin = bp(nz, 120, 900) * np.exp(-t * 30)
    metal = sum(np.sin(2 * np.pi * fr * pitch * t) for fr in (523, 787, 1131, 1607)) * np.exp(-t * 9) * 0.08
    y = np.tanh((body * 1.4 + skin * 0.5 + metal) * 1.5)
    return stereo(y, 0, 3) * gain * 0.55


# --- 5. Riser: rumore in sweep + tono che sale + ticchettio che accelera
def riser(a, b):
    n = int((b - a) * SR)
    t = np.arange(n) / SR
    T = t[-1]
    prog = t / T
    nz = rng.standard_normal(n)
    def des(i):
        c = 300 + 6000 * prog[i] ** 2.2
        return butter(2, [c * 0.7, min(c * 1.4, 20000)], 'band', fs=SR, output='sos')
    out = tv_filter(nz, des)[0]
    out *= prog ** 1.6
    f = 73.42 * 2 ** (prog * 2.0)
    tone = np.tanh(2 * saw(1, np.cumsum(f) / SR)) * prog ** 2 * 0.25
    tone = lp(tone, 2500)
    # ticchettio da orologio che accelera
    ticks = np.zeros(n)
    tt, step = 0.0, 0.32
    while tt < T:
        i = int(tt * SR)
        k = np.arange(min(1500, n - i)) / SR
        ticks[i:i + len(k)] += np.sin(2 * np.pi * 2400 * k) * np.exp(-k * 120) * (0.4 + 0.6 * tt / T)
        tt += step
        step = max(0.06, step * 0.86)
    y = out * 0.5 + tone + ticks * 0.35
    return stereo(y, 0, 11) * 0.7


# --- 6. Risucchio inverso verso il boom
def reverse_swell(dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = bp(rng.standard_normal(n), 400, 7000) * np.exp(-t * 5)
    x = verb(np.vstack([nz, nz]))[:, ::-1]
    return x * 0.6


# --- 7. "Strappo" nel fotogramma in cui la cartella sparisce: rumore che crolla di frequenza + sub che cade
def tear(dur=0.7, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    def des(i):
        c = 200 + 9000 * np.exp(-t[i] * 9)
        return butter(2, [c * 0.6, min(c * 1.6, 20000)], 'band', fs=SR, output='sos')
    swp = tv_filter(nz, des)[0] * np.exp(-t * 5)
    f = 30 + 90 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5)
    y = np.tanh(swp * 1.2 + sub * 1.2)
    return stereo(y, 0, 13) * gain * 0.6


G = dict(drone=1.0, heart=0.22, braam1=0.8, braam2=0.9, riser=1.6, stut=1.45, boom=1.5, final=1.35, wet=0.3)
mix = np.zeros((2, N))
mix += drone()
for at in (0.05, 0.72, 1.38, 1.98):
    place(mix, boom(1.0, 70, 38, G['heart'], 0.0), at)
place(mix, braam(2.2, 36.71, 0.8, G['braam1']), HITS['braam1'])
place(mix, boom(2.0, 100, 34, G['braam1'] * 0.9, 0.8), HITS['braam1'])
place(mix, braam(1.6, 36.71 * 1.0595, 1.0, G['braam2']), HITS['braam2'])  # mezzo tono sopra: tensione
place(mix, boom(1.6, 100, 36, G['braam2'] * 0.8, 0.8), HITS['braam2'])
ra, rb = HITS['riser']
place(mix, riser(ra, rb) * G['riser'], ra)
for i, at in enumerate(HITS['stut']):
    place(mix, hit(1.0 + 0.12 * i, G['stut'] * (0.8 + 0.2 * i)), at)

a, b = HITS['gap']
mix[:, int(a * SR):int(b * SR)] = 0.0
big = np.zeros((2, N))
place(big, braam(2.6, 36.71, 1.2, G['boom']), HITS['boom'])
place(big, boom(3.0, 140, 30, G['boom'], 1.4), HITS['boom'])
place(big, tear(0.7, 1.1), HITS['vanish'])        # la cartella sparisce (fotogramma 266)
place(big, braam(2.0, 36.71, 1.4, G['final']), HITS['final'])
place(big, boom(2.0, 120, 28, G['final'], 1.0), HITS['final'])

full = mix + big
wet = verb(full)
out = full + wet * G['wet']
out[:, int(a * SR):int(b * SR)] = 0.0          # silenzio vero nel buco
sw = reverse_swell(0.7) * 0.5
place(out, sw, b - sw.shape[1] / SR)           # ...tranne il risucchio verso il boom
out = np.vstack([hp(out[0], 25), hp(out[1], 25)])
pk = np.abs(out).max()
out = out / pk * 1.15
out = np.tanh(out) / np.tanh(1.15)               # saturazione morbida: picchi domati, impatto conservato
k = int(0.6 * SR)
out[:, -k:] *= np.linspace(1, 0, k) ** 1.5
out *= 0.89 / np.abs(out).max()
wavfile.write(sys.argv[1], SR, (out.T * 32767).astype(np.int16))
print('ok', out.shape)
