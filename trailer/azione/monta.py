"""MONTAGGIO del trailer d'azione: dalle riprese (fotogrammi jpg di riprese.js) e dalla musica (musica.py) all'mp4
per le storie Instagram (1080x1920, 30 fps, H.264 + AAC). Tutto segue mappa.py.

Per ogni fotogramma d'uscita: quale taglio, quale istante della ripresa (curve di velocità: rallentatori sui colpi),
mosso cinematografico (otturatore a 180°: si fondono i fotogrammi girati dentro mezzo fotogramma d'uscita),
zoom e carrellate digitali, scossoni e lampi sui colpi, aberrazione cromatica, color grading (caldo per la steppa,
freddo per il Boss), vignettatura e grana. Poi cartelli, titolo e chiusa.
uso: python monta.py <cartella riprese> <musica.wav> <uscita.mp4> [--anteprima secondi,separati,da,virgole <cartella>]
"""
import sys, os, re, glob, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from mappa import TAGLI, CARTELLI, TITOLO, CHIUSA, FPS, DUR

RIPRESE, MUSICA, USCITA = sys.argv[1], sys.argv[2], sys.argv[3]
ANTEPRIMA = None
if '--anteprima' in sys.argv:
    i = sys.argv.index('--anteprima')
    ANTEPRIMA = ([float(x) for x in sys.argv[i + 1].split(',')], sys.argv[i + 2])
W, H = 1080, 1920
MOSSO = False                 # True: mosso a 180° fondendo i fotogrammi girati
PROGETTO = os.path.abspath(os.path.join(QUI, '..', '..'))
FONT_PIXEL = os.path.join(PROGETTO, 'vendor', 'font', 'PressStart2P.woff2')
FONT_CARTELLI = ('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf', 0)   # scelto dall'utente (18 nov 2026)
SPAZIO_CARTELLI = 0.16                                                              # spaziatura, in frazione del corpo

# passo di ripresa di ogni inquadratura, letto da riprese.js (1/60 o 1/120 s)
DT = {}
for nome, den in re.findall(r"nome: '(\w+)'.*?dt: 1 / (\d+)", open(os.path.join(QUI, 'riprese.js')).read()):
    DT[nome] = 1 / int(den)
FOTO = {n: sorted(glob.glob(os.path.join(RIPRESE, n, '*.jpg'))) for n in DT}


# ── lettura delle riprese ────────────────────────────────────────────────────────────────────────────────────────────
_cache = {}
def fotogramma(nome, i):
    lst = FOTO[nome]
    i = max(0, min(len(lst) - 1, i))
    k = (nome, i)
    if k not in _cache:
        if len(_cache) > 40:
            _cache.pop(next(iter(_cache)))
        _cache[k] = Image.open(lst[i]).convert('RGB')
    return _cache[k]


def curva(punti, t):
    """Tempo della ripresa all'istante t del montaggio, e velocità locale (pendenza)."""
    for (a, sa), (b, sb) in zip(punti, punti[1:]):
        if t <= b or (b, sb) == punti[-1]:
            v = (sb - sa) / (b - a)
            return sa + (t - a) * v, v
    return punti[-1][1], 1.0


def ripresa(nome, ts, vel):
    """Fotogramma della ripresa al tempo ts, col mosso di un otturatore a 180° (fusione dei fotogrammi girati)."""
    dt = DT[nome]
    i0 = ts / dt
    # con due soli campioni la fusione fa doppie immagini (scossoni, fermo-immagine): otturatore stretto, come nei film d'azione
    n = max(1, int(round(0.5 * vel * (1 / FPS) / dt))) if MOSSO else 1
    if n == 1:
        return fotogramma(nome, int(round(i0)))
    acc = np.zeros((H, W, 3), np.float32)
    for k in range(n):
        acc += np.asarray(fotogramma(nome, int(round(i0)) + k), np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))


# ── colore ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def lut(contrasto=1.12, s=0.35, ombre=(0.0, 0.03, 0.06), luci=(0.05, 0.01, -0.05), gamma=1.0, nero=0.0):
    """Curve per canale: contrasto a S, ombre verso il ciano, luci verso l'arancio (il teal & orange da cinema)."""
    out = []
    x = np.arange(256) / 255.0
    for c in range(3):
        v = np.clip(0.5 + (x - 0.5) * contrasto, 0, 1)
        v = v * (1 - s) + (v * v * (3 - 2 * v)) * s
        v = v ** gamma
        v = v + ombre[c] * (1 - v) ** 3 + luci[c] * v ** 2
        v = np.clip((v - nero) / (1 - nero), 0, 1)
        out += list((np.clip(v, 0, 1) * 255).astype(np.uint8))
    return out


LUT_CALDO = lut()
LUT_FREDDO = lut(contrasto=1.08, s=0.25, ombre=(-0.01, 0.04, 0.10), luci=(-0.02, 0.0, 0.06), gamma=0.92)
LUT_TITOLO = lut(contrasto=1.1, s=0.3, ombre=(0.0, 0.02, 0.05), luci=(0.06, 0.0, -0.06), gamma=1.25)


_luci = {}
def luce_lut(l):
    if l not in _luci:
        x = np.arange(256) / 255.0
        _luci[l] = list((np.clip(x ** (1 / l), 0, 1) * 255).astype(np.uint8)) * 3
    return _luci[l]


def vignettatura(forza=0.75):
    small = np.zeros((H // 8, W // 8), np.float32)
    yy, xx = np.mgrid[0:H // 8, 0:W // 8]
    dx = (xx - W / 16) / (W / 16)
    dy = (yy - H / 16) / (H / 16)
    r = np.sqrt(dx * dx * 0.9 + dy * dy * 0.75)
    k = np.clip((r - 0.55) / 0.7, 0, 1) ** 1.7
    small = 255 * (1 - forza * k)
    img = Image.fromarray(small.astype(np.uint8), 'L').resize((W, H), Image.BICUBIC)
    return Image.merge('RGB', [img] * 3)


VIGNETTA = vignettatura(0.6)
rng = np.random.default_rng(3)
GRANA = [Image.fromarray(np.clip(128 + rng.normal(0, 4.5, (H // 2, W // 2)), 0, 255).astype(np.uint8), 'L')
         .resize((W, H), Image.NEAREST).convert('RGB') for _ in range(6)]


def grana(img, f):
    return ImageChops.add(img, GRANA[f % len(GRANA)], 1.0, -128)


def aberrazione(img, d):
    d = int(round(d))
    if d == 0:
        return img
    r, g, b = img.split()
    r = ImageChops.offset(r, d, 0)
    b = ImageChops.offset(b, -d, int(d * 0.3))
    return Image.merge('RGB', (r, g, b))


def lampo(img, a, colore=(255, 255, 255)):
    if a <= 0.003:
        return img
    return Image.blend(img, Image.new('RGB', (W, H), colore), min(1.0, a))


def inquadra(img, z, ox=0.0, oy=0.0):
    """Zoom digitale centrato (con spostamento per gli scossoni) e ritorno a 1080x1920."""
    if z <= 1.0005 and abs(ox) < 0.5 and abs(oy) < 0.5:
        return img
    z = max(z, 1.0 + 2.2 * max(abs(ox) / W, abs(oy) / H))
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2 + ox
    y0 = (H - ch) / 2 + oy
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


# ── testi ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def testo_spaziato(d, xy_centro, testo, font, spazio, fill, stroke=0, stroke_fill=None):
    larg = [d.textlength(c, font=font) for c in testo]
    tot = sum(larg) + spazio * (len(testo) - 1)
    x = xy_centro[0] - tot / 2
    for c, w in zip(testo, larg):
        d.text((x, xy_centro[1]), c, font=font, fill=fill, anchor='ls', stroke_width=stroke, stroke_fill=stroke_fill)
        x += w + spazio
    return tot


def cartello(righe):
    """Cartello da trailer: maiuscole spaziate, bianco caldo con alone."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    strato = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(strato)
    corpo = 150
    while True:
        font = ImageFont.truetype(FONT_CARTELLI[0], corpo, index=FONT_CARTELLI[1])
        larga = max(sum(d.textlength(c, font=font) for c in r) + corpo * SPAZIO_CARTELLI * (len(r) - 1) for r in righe)
        if larga <= 900: break
        corpo -= 4
    passo = corpo * 1.12
    y0 = H / 2 - (len(righe) - 1) * passo / 2 + corpo * 0.36
    for i, r in enumerate(righe):
        testo_spaziato(d, (W / 2, y0 + i * passo), r, font, corpo * SPAZIO_CARTELLI, (246, 238, 225, 255))
    alone = strato.split()[3].filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, int(v * 0.9)))
    glow = Image.new('RGBA', (W, H), (255, 150, 60, 0)); glow.putalpha(alone)
    img.alpha_composite(glow)
    img.alpha_composite(strato)
    # filo sottile sopra e sotto, come nei trailer
    d2 = ImageDraw.Draw(img)
    # i filetti: misurati sul testo vero (sopra la prima riga, sotto l'ultima), con un po' d'aria
    yt = d2.textbbox((W / 2, y0), righe[0], font=font, anchor='ms')[1] - corpo * 0.28
    yb = d2.textbbox((W / 2, y0 + (len(righe) - 1) * passo), righe[-1], font=font, anchor='ms')[3] + corpo * 0.22
    for y in (yt, yb):
        d2.rectangle((W / 2 - 70, y, W / 2 + 70, y + 2), fill=(200, 150, 90, 200))
    return img


def titolo():
    """Il titolo come sulla copertina: banda rossa con bordo d'oro, lettere a pixel gialle col contorno scuro."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H // 2 - 40
    bw, bh = 1000, 190
    x0, y0, x1, y1 = (W - bw) // 2, cy - bh // 2, (W + bw) // 2, cy + bh // 2
    # ombra della banda
    om = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(om).rectangle((x0, y0 + 14, x1, y1 + 14), fill=(0, 0, 0, 170))
    img.alpha_composite(om.filter(ImageFilter.GaussianBlur(14)))
    # banda: rosso con sfumatura verticale
    banda = np.zeros((bh, bw, 4), np.uint8)
    for y in range(bh):
        k = y / bh
        banda[y, :] = (int(176 - 50 * k), int(28 - 10 * k), int(24 - 8 * k), 255)
    img.alpha_composite(Image.fromarray(banda, 'RGBA'), (x0, y0))
    oro, scuro = (226, 172, 72, 255), (60, 20, 10, 255)
    for k, c in ((0, scuro), (4, oro), (11, scuro), (14, oro)):
        d.rectangle((x0 + k, y0 + k, x1 - k, y1 - k), outline=c, width=3 if c == oro else 2)
    # angoli a greca (pixel)
    for sx, sy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        fx = 1 if sx == x0 else -1
        fy = 1 if sy == y0 else -1
        for dx_, dy_ in ((24, 24), (24, 36), (36, 24), (48, 24), (24, 48)):
            px, py = sx + fx * dx_, sy + fy * dy_
            d.rectangle((min(px, px + fx * 9), min(py, py + fy * 9), max(px, px + fx * 9), max(py, py + fy * 9)), fill=oro)
    f1 = ImageFont.truetype(FONT_PIXEL, 58)
    f2 = ImageFont.truetype(FONT_PIXEL, 74)
    giallo = (255, 214, 64, 255)
    testo_spaziato(d, (W / 2 + 4, cy + 29 + 6), 'CAVALLI MONGOLI', f1, 2, (40, 10, 5, 255), 6, (40, 10, 5, 255))
    testo_spaziato(d, (W / 2, cy + 29), 'CAVALLI MONGOLI', f1, 2, giallo, 5, (52, 16, 8, 255))
    testo_spaziato(d, (W / 2 + 6, y1 + 134 + 7), 'THE GAME', f2, 8, (20, 6, 2, 230), 7, (20, 6, 2, 230))
    testo_spaziato(d, (W / 2, y1 + 134), 'THE GAME', f2, 8, giallo, 6, (52, 16, 8, 255))
    return img


def chiusa():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    strato = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(strato)
    font = ImageFont.truetype(FONT_CARTELLI[0], 96, index=FONT_CARTELLI[1])
    testo_spaziato(d, (W / 2, H / 2 + 34), 'PROSSIMAMENTE', font, 96 * SPAZIO_CARTELLI, (246, 238, 225, 255))
    alone = strato.split()[3].filter(ImageFilter.GaussianBlur(20))
    glow = Image.new('RGBA', (W, H), (255, 140, 50, 0)); glow.putalpha(alone)
    img.alpha_composite(glow); img.alpha_composite(strato)
    return img


IMG_CARTELLI = [cartello(c['righe']) for c in CARTELLI]
IMG_TITOLO = titolo()
IMG_CHIUSA = chiusa()


def sovrapponi(base, rgba, scala=1.0, alfa=1.0, dy=0):
    if alfa <= 0.003:
        return base
    s = rgba
    if abs(scala - 1) > 1e-3:
        sw, sh = int(W * scala), int(H * scala)
        s = rgba.resize((sw, sh), Image.BICUBIC).crop(((sw - W) // 2, (sh - H) // 2 - dy, (sw - W) // 2 + W, (sh - H) // 2 + H - dy))
    if alfa < 0.999:
        a = s.split()[3].point(lambda v: int(v * alfa))
        s = s.copy(); s.putalpha(a)
    out = base.convert('RGBA')
    out.alpha_composite(s)
    return out.convert('RGB')


# polvere luminosa sotto il titolo
POLV = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), v=rng.uniform(25, 90), r=rng.uniform(1.5, 4.5), f=rng.uniform(0, 6.28)) for _ in range(140)]


def polvere(img, t):
    strato = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(strato)
    for p in POLV:
        y = (p['y'] - p['v'] * t * 3) % H
        x = p['x'] + 18 * math.sin(t * 1.3 + p['f'])
        a = int(110 + 100 * math.sin(t * 5 + p['f']))
        d.ellipse((x - p['r'], y - p['r'], x + p['r'], y + p['r']), fill=(255, 190, 110, max(0, a)))
    strato = strato.filter(ImageFilter.GaussianBlur(1.6))
    out = img.convert('RGBA'); out.alpha_composite(strato)
    return out.convert('RGB')


NERO = Image.new('RGB', (W, H), (0, 0, 0))


# ── un fotogramma del montaggio ──────────────────────────────────────────────────────────────────────────────────────
def fotogramma_montaggio(f):
    t = (f + 0.5) / FPS                   # il centro del fotogramma
    rs = np.random.default_rng(1000 + f)
    taglio = next((c for c in TAGLI if c['t'][0] <= t < c['t'][1]), None)
    img = NERO
    if taglio:
        c = taglio
        ts, vel = curva(c['s'], t)
        img = ripresa(c['r'], ts, abs(vel))
        k = (t - c['t'][0]) / (c['t'][1] - c['t'][0])
        z0, z1 = c.get('zoom', (1.0, 1.0))
        z = z0 + (z1 - z0) * (k * k * (3 - 2 * k))
        ox = oy = 0.0
        flash = ab = 0.0
        p = c.get('punch')
        if p is not None and t >= p:
            e = math.exp(-(t - p) * 13)
            z *= 1 + 0.07 * e
            amp = 22 * e
            ox += rs.uniform(-amp, amp); oy += rs.uniform(-amp, amp)
            flash = 0.55 * math.exp(-(t - p) * 22)
            ab = 12 * math.exp(-(t - p) * 14)
        if 'scuoti' in c:
            a0, a1 = c['scuoti']
            amp = a0 + (a1 - a0) * k
            ox += rs.uniform(-amp, amp); oy += rs.uniform(-amp, amp)
        img = inquadra(img, z, ox, oy)
        if c.get('luce'):                 # schiarisce i medi e le ombre (curva gamma), senza bruciare fuochi e lampi
            img = img.point(luce_lut(c['luce']))
        if c.get('sotto_titolo'):
            img = img.filter(ImageFilter.GaussianBlur(7))
            img = ImageEnhance.Color(img).enhance(0.6)
            img = ImageEnhance.Brightness(img).enhance(0.42)
            img = img.point(LUT_TITOLO)
        elif c.get('freddo'):
            img = ImageEnhance.Color(img).enhance(0.75).point(LUT_FREDDO)
        else:
            img = ImageEnhance.Color(img).enhance(0.9).point(LUT_CALDO)
        if c.get('scuro'):
            img = ImageEnhance.Brightness(img).enhance(1 - c['scuro'])
        img = aberrazione(img, ab)
        img = lampo(img, flash)
        if c.get('entra_dal_nero'):
            a = min(1.0, (t - c['t'][0]) / c['entra_dal_nero'])
            img = Image.blend(NERO, img, a ** 1.5)
    # cartelli
    for cc, im in zip(CARTELLI, IMG_CARTELLI):
        a, b = cc['t']
        if a <= t < b:
            k = (t - a) / (b - a)
            alfa = min(1.0, (t - a) / 0.16, (b - t) / 0.1)
            img = sovrapponi(NERO, im, 1.06 - 0.06 * k, alfa)
            if t - a < 0.1:
                img = aberrazione(img, 8 * (1 - (t - a) / 0.1))
    # titolo: entra di colpo sul BOOM e poi si avvicina piano
    a, b = TITOLO
    if a <= t < b:
        d = t - a
        sc = 1.22 - 0.22 * (1 - (1 - min(1, d / 0.16)) ** 3) + 0.045 * (d / (b - a))
        img = polvere(img, t)
        alfa = min(1.0, d / 0.06, (b - t) / 0.12)
        img = sovrapponi(img, IMG_TITOLO, sc, alfa)
        img = aberrazione(img, 14 * math.exp(-d * 10))
        img = lampo(img, 0.85 * math.exp(-d * 9), (255, 236, 200))
    a, b = CHIUSA
    if a <= t < b:
        alfa = min(1.0, (t - a) / 0.35, (b - t) / 0.25)
        img = sovrapponi(img, IMG_CHIUSA, 1.02 - 0.02 * (t - a) / (b - a), alfa)
    img = ImageChops.multiply(img, VIGNETTA)
    img = grana(img, f)
    return img


if ANTEPRIMA:
    istanti, cartella = ANTEPRIMA
    os.makedirs(cartella, exist_ok=True)
    for s in istanti:
        f = int(s * FPS)
        fotogramma_montaggio(f).save(os.path.join(cartella, f'm{s:05.2f}.jpg'), quality=85)
    print('anteprime in', cartella)
    sys.exit(0)

n = int(DUR * FPS)
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', MUSICA, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-maxrate', '16M', '-bufsize', '32M', '-pix_fmt', 'yuv420p',
       '-profile:v', 'high', '-level', '4.1', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', str(DUR),
       '-movflags', '+faststart', USCITA]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for f in range(n):
    proc.stdin.write(fotogramma_montaggio(f).tobytes())
    if f % 90 == 0:
        print(f'{f / FPS:5.1f} s', flush=True)
proc.stdin.close()
proc.wait()
print('fatto:', USCITA, 'codice', proc.returncode)
