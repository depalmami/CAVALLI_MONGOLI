#!/usr/bin/env python3
"""
Alberi della MODALITÀ POPLAR: pioppi al posto delle palme.

Il pioppo cipressino (l'albero che dà il nome al festival) è alto e strettissimo, e
lo slot PALM_TREE è 215x540 — le stesse proporzioni. Sostituzione perfetta.
TREE1/TREE2 diventano latifoglie tonde, come la vegetazione del Doss.

Disegnati a codice invece che con una foto: così l'alpha è pulita, si rigenerano a
qualsiasi misura e non c'è niente da ritagliare. Il seme è fisso: due esecuzioni
danno lo stesso risultato.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "images", "poplar")
SS   = 3

MISURE = {"PALM_TREE": (215, 540), "TREE1": (360, 360), "TREE2": (282, 295)}

# Palette NOTTURNA: gli sprite sono PNG, quindi la tinta notte applicata ai colori
# del livello non li tocca — se restano verdi da mezzogiorno stonano contro le luci
# di Trento. Verdi bassi e spostati verso il blu, con un filo di luce calda in cima
# come se li prendesse il lampione.
NOTTE  = os.environ.get("POPLAR_ALBERI", "notte") == "notte"
if NOTTE:
    VERDI  = [(14,22,18), (18,29,23), (24,38,29), (31,48,35), (46,62,42)]
    TRONCO = [(20,18,17), (30,27,24)]
else:
    VERDI  = [(38,58,32), (46,72,38), (56,86,44), (68,100,52), (82,114,60)]
    TRONCO = [(52,42,34), (68,56,44)]

def chioma(d, cx, base_y, altezza, largh_max, profilo, rnd, n=400, grana=0.20):
    """Tante macchie lungo una spina verticale: la sagoma viene irregolare come
    quella vera, e l'alpha resta netta perché si disegna su un layer dedicato.

    `largh_max` è la SEMI-larghezza della chioma; `grana` è quanto è grossa la
    singola macchia RISPETTO alla chioma. Tenerle legate era l'errore: con macchie
    larghe quanto la chioma il disegno si trasformava in un quadrato pieno."""
    for i in range(n):
        t = rnd.random()                      # 0 = cima, 1 = base della chioma
        y = base_y - altezza * (1 - t)
        semi = largh_max * profilo(t)         # semi-larghezza a questa quota
        if semi < 1: continue
        r = largh_max * grana * (0.45 + 0.75*rnd.random())
        x = cx + (rnd.random()*2 - 1) * semi
        c = VERDI[min(len(VERDI)-1, int((1-t)*len(VERDI)*0.9 + rnd.random()*1.2))]
        d.ellipse([x-r, y-r*0.8, x+r, y+r*0.8], fill=c+(255,))

def tronco(d, cx, y0, y1, largh, rnd):
    for k in range(6):
        w = largh * (1 - k/8)
        c = TRONCO[k % 2]
        d.polygon([(cx-w/2, y1), (cx+w/2, y1), (cx+w/3, y0), (cx-w/3, y0)], fill=c+(255,))

def pioppo(W, H, seme=7):
    rnd = random.Random(seme)
    w, h = W*SS, H*SS
    im = Image.new("RGBA", (w, h), (0,0,0,0)); d = ImageDraw.Draw(im)
    cx = w*0.5
    # il cipressino: appuntito in cima, pancia sotto la metà, stretto sempre
    prof = lambda t: (t**0.55) * (1 - 0.45*max(0, t-0.75)/0.25)
    tronco(d, cx, h*0.86, h, w*0.10, rnd)
    chioma(d, cx, h*0.90, h*0.90, w*0.33, prof, rnd, n=900, grana=0.20)
    return im.resize((W, H), Image.LANCZOS)

def latifoglia(W, H, seme=3):
    rnd = random.Random(seme)
    w, h = W*SS, H*SS
    im = Image.new("RGBA", (w, h), (0,0,0,0)); d = ImageDraw.Draw(im)
    cx = w*0.5
    # tonda: massimo a metà chioma, chiusa sopra e sotto
    prof = lambda t: math.sin(min(1, t*1.05) * math.pi) ** 0.7
    tronco(d, cx, h*0.70, h, w*0.13, rnd)
    chioma(d, cx, h*0.78, h*0.74, w*0.38, prof, rnd, n=1100, grana=0.17)
    return im.resize((W, H), Image.LANCZOS)

def filare_orizzonte():
    """trees.png: la linea d'alberi lontana. Sostituisce il filare di palme.
    Trasparente sopra y=162 come negli altri livelli. Si ripete da sé perché gli
    alberi che escono a destra vengono ridisegnati a sinistra."""
    W, H, CIMA = 1280, 480, 162
    im = Image.new("RGBA", (W, H), (0,0,0,0))
    rnd = random.Random(11)
    sagome = [pioppo(90, 250, seme=s) for s in (2,5,9,13)] + [latifoglia(150, 150, seme=s) for s in (4,8)]
    x = -60
    while x < W + 60:
        s = sagome[rnd.randrange(len(sagome))]
        scala = 0.7 + rnd.random()*0.55
        t = s.resize((max(8,int(s.width*scala)), max(8,int(s.height*scala))), Image.LANCZOS)
        # lontani = più scuri e più freddi, si fondono con la collina
        px = t.load()
        for yy in range(t.height):
            for xx in range(t.width):
                r,g,b,a = px[xx,yy]
                if a: px[xx,yy] = (int(r*0.72), int(g*0.75), int(b*0.92), a)
        y = CIMA + int(rnd.random()*40)
        for dx in (0, -W, W):                      # ricopia oltre i bordi: ripetibile
            if -t.width < x+dx < W:
                im.alpha_composite(t, (int(x+dx), y))
        x += int(38 + rnd.random()*54)
    # zoccolo scuro sotto il filare, così non "galleggia"
    base = Image.new("RGBA", (W, H-(CIMA+150)), (26,34,26,255))
    im.alpha_composite(base, (0, CIMA+150))
    return im

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pioppo(*MISURE["PALM_TREE"]).save(os.path.join(OUT, "PALM_TREE.png"))
    print(f"  PALM_TREE.png  {MISURE['PALM_TREE'][0]}x{MISURE['PALM_TREE'][1]}  pioppo cipressino")
    latifoglia(*MISURE["TREE1"], seme=3).save(os.path.join(OUT, "TREE1.png"))
    print(f"  TREE1.png      360x360  latifoglia")
    latifoglia(*MISURE["TREE2"], seme=6).save(os.path.join(OUT, "TREE2.png"))
    print(f"  TREE2.png      282x295  latifoglia")
    filare_orizzonte().save(os.path.join(OUT, "trees.png"))
    print(f"  trees.png      1280x480  filare all'orizzonte")
