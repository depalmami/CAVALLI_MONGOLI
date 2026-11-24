"""Copertina del gioco: via il sottotitolo della serata (PADOVA ATTACK / DISCHI SOTTERRANEI LA CAVALCATA, 13 nov 2026)
e al suo posto THE GAME, nello stesso stile a pixel (giallo, contorno scuro, ombra in basso a destra).
Il cielo si ricostruisce con l'inpainting di OpenCV (vedi sotto); le orecchie del cavallo restano quelle vere.
uso: python tools/copertina/the-game.py assets/titoli/copertina-padova-attack.jpg assets/titoli/copertina.jpg   (serve opencv-python-headless, numpy, pillow)
"""
import sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
FONT = os.path.join(os.path.dirname(__file__), '..', '..', 'vendor', 'font', 'PressStart2P.woff2')
img = np.array(Image.open(SRC).convert('RGB'))
h, w, _ = img.shape
assert (w, h) == (1024, 1024), (w, h)

# Le due righe del sottotitolo stanno su cielo azzurro. Prima riga (PADOVA ATTACK): si tolgono solo i pixel delle
# lettere (giallo + contorno scuro, allargati), così fra una lettera e l'altra resta il cielo vero; seconda riga (piccola
# e fitta): via tutto il rettangolo. Il cielo lo ricostruisce l'inpainting di OpenCV.
# Trappola: le punte delle orecchie del cavallo spuntano subito sotto la seconda riga (x 383-440, da y 433): l'inpainting
# ne tirava su il colore. Durante il calcolo le orecchie si coprono col colore del cielo, poi si rimettono quelle vere.
yy, xx = np.mgrid[0:h, 0:w]
r, g, b = [img[..., i].astype(int) for i in range(3)]
cielo = (b > r + 40) & (b > g + 15)
giallo = (r > 140) & (g > 120) & (b < 150) & (r - b > 60)
scuro = (r + g + b) < 330
mask = np.zeros((h, w), np.uint8)
riga1 = (xx >= 338) & (xx < 735) & (yy >= 348) & (yy < 400)
mask[riga1 & (giallo | scuro)] = 255
mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
mask[(xx >= 262) & (xx < 790) & (yy >= 403) & (yy < 442)] = 255   # fino a 442: sotto restavano puntini dell'ombra
mask[:348, :] = 0                                   # la banda rossa non si tocca
orecchie = (xx >= 372) & (xx < 448) & (yy >= 434) & (yy < 480) & ~cielo
lavoro = img.copy()
intorno = (xx >= 340) & (xx < 480) & (yy >= 438) & (yy < 452) & cielo
lavoro[orecchie] = img[intorno].mean(axis=0).astype(np.uint8)
mask[orecchie] = 0
pulita = cv2.inpaint(cv2.cvtColor(lavoro, cv2.COLOR_RGB2BGR), mask, 7, cv2.INPAINT_TELEA)
pulita = cv2.cvtColor(pulita, cv2.COLOR_BGR2RGB)
ver = orecchie & ((yy >= 437) | ~scuro)               # le orecchie vere (sopra y 437 lo scuro è l'ombra delle lettere)
pulita[ver] = img[ver]
pulita = Image.fromarray(pulita)

# THE GAME, centrato sotto la banda (il centro di PADOVA ATTACK era x 535)
d = ImageDraw.Draw(pulita)
font = ImageFont.truetype(FONT, 50)
testo, spazio = 'THE GAME', 6
larg = [d.textlength(c, font=font) for c in testo]
tot = sum(larg) + spazio * (len(testo) - 1)
cx, base = 535, 412
def scrivi(dx, dy, fill, stroke, stroke_fill):
    x = cx - tot / 2 + dx
    for c, wc in zip(testo, larg):
        d.text((x, base + dy), c, font=font, fill=fill, anchor='ls', stroke_width=stroke, stroke_fill=stroke_fill)
        x += wc + spazio
scrivi(5, 5, (38, 22, 10), 5, (38, 22, 10))           # ombra
scrivi(0, 0, (236, 212, 58), 4, (46, 30, 16))         # lettere col contorno
# un filo più chiaro in cima alle lettere, come nell'originale
strato = Image.new('L', pulita.size, 0)
ds = ImageDraw.Draw(strato)
x = cx - tot / 2
for c, wc in zip(testo, larg):
    ds.text((x, base), c, font=font, fill=255, anchor='ls'); x += wc + spazio
alto = np.array(strato) > 0
alto[base - 28:, :] = False
arr = np.array(pulita)
arr[alto] = (np.clip(arr[alto].astype(int) + [18, 18, 30], 0, 255)).astype(np.uint8)
Image.fromarray(arr).save(OUT, quality=93)
print('ok', OUT)
