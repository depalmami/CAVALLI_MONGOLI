#!/usr/bin/env python3
"""
Costruisce sky.png e hills.png della MODALITÀ POPLAR dalla vista vera dal Doss Trento.

Convenzione copiata dai livelli esistenti (non inventata):
  sky.png    1280x480 RGBA, opaco su tutta l'area
  hills.png  1280x480 RGBA, trasparente sopra il crinale (prima riga opaca ~y=28)

Perché 1280 e non 640: Render.background (common.js:269) usa layer.w/2, cioè mostra
METÀ immagine per volta e poi riavvolge. Se il bordo destro non combacia col sinistro
si vede uno stacco netto ad ogni giro. Rimedio: 640 px di foto + gli stessi 640
specchiati, così la colonna 1279 è identica alla colonna 0 e la giunta sparisce.

Sorgente: foto CC BY-SA di Wikimedia Commons scattate DAL Doss (vedi CREDITI in fondo).
"""
import os, sys
from PIL import Image, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "images", "poplar")
SRC  = os.environ.get("POPLAR_FOTO", "/private/tmp/claude-501/-Users-mmm-Documents-Documenti---MacBook-Pro-di-Domenico---1-CAVALLI-MONGOLI/125f6011-de09-449b-b4f7-69aa22458787/scratchpad/doss")

W, H     = 1280, 480
META     = W // 2          # 640: la porzione realmente visibile
CRINALE  = 28              # prima riga opaca, come negli altri livelli

FOTO_COLLINE = os.environ.get("POPLAR_HILLS", "08_Trento_Blick_vom_Doss_Trento_auf_die_Altstadt_1.jpg")

def e_cielo(px, lum_min=118, sat_max=64):
    """Il cielo di queste foto è coperto: chiaro e poco saturo. Le montagne no."""
    r, g, b = px[:3]
    lum = (r*299 + g*587 + b*114) // 1000
    sat = max(r, g, b) - min(r, g, b)
    return lum >= lum_min and sat <= sat_max

def ritaglia_cielo(im, morbidezza=3, tenuta=9):
    """Alpha 0 sopra il crinale.

    Non basta fermarsi al primo pixel non-cielo: sopra la citta' c'e' foschia
    chiara che passa per cielo, e sotto ci sono tetti chiari che pure passano per
    cielo — il risultato era un pettine di denti verticali dentro il paesaggio.
    Due difese: (1) serve una TENUTA di pixel consecutivi non-cielo per dichiarare
    finito il cielo, (2) il profilo passa per una MEDIANA, che toglie le colonne
    isolate invece di spalmarle come farebbe una media."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    profilo = []
    for x in range(w):
        y = 0
        while y < h:
            if not e_cielo(px[x, y]):
                if all(not e_cielo(px[x, k]) for k in range(y, min(h, y+tenuta))):
                    break
            y += 1
        profilo.append(y)
    liscio = []
    for x in range(w):
        a = max(0, x-morbidezza); b = min(w, x+morbidezza+1)
        finestra = sorted(profilo[a:b])
        liscio.append(finestra[len(finestra)//2])
    for x in range(w):
        for y in range(min(liscio[x], h)):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
    return im, liscio

def grada_crepuscolo(im, forza=0.34):
    """Porta la foto diurna verso il crepuscolo SENZA spegnerla.

    Prima versione: un velo di colore piatto fuso al 47%. Spostava la tinta ma
    mangiava contrasto e saturazione, e la citta' diventava una macchia marrone.
    Qui invece:
      1. contrasto e NITIDEZZA per primi — il layer verra' stirato da 480 a 1080
         px di altezza, quindi parte gia' morbido e va compensato;
      2. la tinta e' un DUOTONO (ombre blu / luci calde) costruito sulla luminanza
         della foto: porta il colore ma il disegno resta, perche' la mappa di
         tinta segue il contenuto invece di coprirlo;
      3. il duotono pesa di piu' in alto, dove c'e' foschia vera, e quasi niente
         in basso, dove ci sono i dettagli che si devono leggere.
    """
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    im = ImageEnhance.Contrast(rgba.convert("RGB")).enhance(1.30)
    im = ImageEnhance.Brightness(im).enhance(1.06)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=3))
    im = ImageEnhance.Color(im).enhance(1.10)

    w, h = im.size
    lum   = im.convert("L")
    ombra = Image.new("RGB", (w, h), ( 32,  38,  74))
    luce  = Image.new("RGB", (w, h), (255, 208, 158))
    duo   = Image.composite(luce, ombra, lum)

    peso = Image.new("L", (w, h))
    pp = peso.load()
    for y in range(h):
        t = y / max(1, h-1)
        v = int(255 * forza * (1 - 0.45*t))     # in alto pieno, in basso attenuato ma presente
        for x in range(w): pp[x, y] = v
    fuso = Image.composite(duo, im, peso)

    out = fuso.convert("RGBA")
    out.putalpha(alpha)
    return out

def giunta_invisibile(im, sovr=190):
    """Rende l'immagine ripetibile in orizzontale SENZA specchiarla.

    Lo specchio funziona ma si vede: crea una farfalla simmetrica in mezzo al
    paesaggio, e se sull'asse capita una vetta la simmetria salta all'occhio.
    Qui invece si prende una striscia larga W+sovr e si dissolve la coda sulla
    testa: così l'ultima colonna e la prima diventano contigue nella foto
    originale e il riavvolgimento non si nota."""
    assert im.width == W + sovr, f"attesa larghezza {W+sovr}, trovata {im.width}"
    im = im.convert("RGBA")
    testa = im.crop((0, 0, W, im.height))
    coda  = im.crop((W, 0, W + sovr, im.height))
    maschera = Image.new("L", (sovr, im.height))
    mp = maschera.load()
    for x in range(sovr):
        a = int(255 * (1 - x/(sovr-1)))       # 255 sul bordo sinistro, 0 dopo la sovrapposizione
        for y in range(im.height): mp[x, y] = a
    testa.paste(coda, (0, 0), maschera)
    return testa

def fai_colline():
    p = os.path.join(SRC, FOTO_COLLINE)
    if not os.path.exists(p): sys.exit(f"manca la foto sorgente: {p}")
    im = Image.open(p).convert("RGB")
    w, h = im.size
    # banda centrale: sopra il crinale un po' di cielo, sotto la valle
    alto  = int(h*float(os.environ.get("POPLAR_TOP",  "0.30")))
    basso = int(h*float(os.environ.get("POPLAR_BOT", "0.90")))   # NB: ritagliare piu stretto (0.62) PEGGIORA — la montagna si rimpicciolisce e la striscia di citta sparisce: il layer viene scalato, non mostrato dall alto
    SOVR = 190
    im = im.crop((0, alto, w, basso)).resize((W + SOVR, H - CRINALE), Image.LANCZOS)
    im = giunta_invisibile(im, SOVR)
    im, profilo = ritaglia_cielo(im)
    im = grada_crepuscolo(im)
    intera = Image.new("RGBA", (W, H), (0,0,0,0))
    intera.paste(im, (0, CRINALE), im)
    intera.save(os.path.join(OUT, "hills.png"))
    return min(profilo)+CRINALE, max(profilo)+CRINALE

def fai_cielo():
    """Crepuscolo pieno: il concerto è di sera, una foto diurna grigia stonerebbe."""
    mezza = Image.new("RGB", (META, H))
    px = mezza.load()
    for y in range(H):
        t = y / (H-1)
        if t < 0.55:
            k = t/0.55
            r = int( 18 + (86-18)*k**1.5); g = int( 20 + (44-20)*k**1.5); b = int( 48 + (92-48)*k**1.5)
        else:
            k = (t-0.55)/0.45
            r = int( 86 + (236-86)*k**0.8); g = int( 44 + (128-44)*k**0.9); b = int( 92 + ( 78-92)*k)
        for x in range(META): px[x, y] = (r, g, b)
    # il cielo e' un gradiente solo verticale: si ripete da se', basta allargarlo
    cielo = mezza.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")
    cielo.save(os.path.join(OUT, "sky.png"))

def fai_cielo_foto(nome, alto=0.14, basso=0.88):
    """Variante NOTTE: la foto fa da fondale unico e opaco.

    Di notte il rilevatore del crinale non funziona — cerca un cielo "chiaro e
    poco saturo" e di notte e' il contrario: il cielo e' scuro e la citta' e'
    la cosa luminosa. Invece di inseguire una segmentazione fragile si usa la
    foto intera come sky.png, che e' opaco e sta sotto a tutto. Serve pero' un
    hills.png TRASPARENTE, se no le colline del livello sotto restano visibili.
    """
    SOVR = 190
    p = os.path.join(SRC, nome)
    if not os.path.exists(p): sys.exit(f"manca la foto sorgente: {p}")
    im = Image.open(p).convert("RGB")
    w, h = im.size
    im = im.crop((0, int(h*alto), w, int(h*basso))).resize((W + SOVR, H), Image.LANCZOS)
    im = giunta_invisibile(im, SOVR).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.16)
    im = ImageEnhance.Color(im).enhance(1.22)          # le luci della citta' devono accendersi
    im = ImageEnhance.Brightness(im).enhance(1.10)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=3))
    im.convert("RGBA").save(os.path.join(OUT, "sky.png"))

def hills_trasparente():
    Image.new("RGBA", (W, H), (0,0,0,0)).save(os.path.join(OUT, "hills.png"))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    variante = os.environ.get("POPLAR_VARIANTE", "notte")   # default: Trento di notte. POPLAR_VARIANTE=doss per la versione diurna
    if variante == "notte":
        fai_cielo_foto(os.environ.get("POPLAR_NOTTE", "00_Trento-panorama_from_Sardagna_by_night.jpg"))
        hills_trasparente()
        print("  sky.png    1280x480  Trento di notte da Sardagna (fondale unico)")
        print("  hills.png  1280x480  trasparente (zittisce le colline del livello)")
    else:
        fai_cielo();  print("  sky.png    1280x480  crepuscolo")
        lo, hi = fai_colline()
        print(f"  hills.png  1280x480  crinale fra y={lo} e y={hi}")
