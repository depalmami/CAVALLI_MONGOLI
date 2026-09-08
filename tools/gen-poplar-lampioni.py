#!/usr/bin/env python3
"""
Lampioni per la MODALITÀ POPLAR, negli slot DEAD_TREE1 e DEAD_TREE2.

Perché quegli slot: sono alti e stretti (135x332 e 150x260), stanno già a bordo
pista nel piazzamento del livello, e così COLUMN resta libero per il mausoleo.

Perché DUE varianti speculari: renderCustomSprite ancora lo sprite a sinistra o a
destra della strada ma NON lo specchia. Con un braccio solo, metà lampioni
punterebbero fuori strada. Uno per verso risolve.

Il bagliore è dipinto dentro il PNG (alone radiale + cono di luce a terra): il
gioco non ha illuminazione, quindi la luce va disegnata.
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "images", "poplar")
SS   = 4

PALO   = (26, 28, 34)
PALO_L = (44, 48, 58)
LUCE   = (255, 214, 138)

def lampione(W, H, verso=1):
    """verso=+1 braccio verso destra, -1 verso sinistra."""
    w, h = W*SS, H*SS
    im = Image.new("RGBA", (w, h), (0,0,0,0))

    # base del palo: sul lato opposto al braccio, così il braccio "sporge" sulla strada
    px = w*0.5 - verso*w*0.26
    testa_x = px + verso*w*0.34
    testa_y = h*0.10

    # ── alone: ellissi concentriche di alpha crescente, poi sfocate
    alone = Image.new("RGBA", (w, h), (0,0,0,0)); ad = ImageDraw.Draw(alone)
    for i in range(26, 0, -1):
        r = w*0.52 * (i/26)
        a = int(74 * (1 - i/26)**1.9)
        ad.ellipse([testa_x-r, testa_y-r*0.95, testa_x+r, testa_y+r*0.95], fill=LUCE+(a,))
    # cono di luce verso terra
    ad.polygon([(testa_x, testa_y), (testa_x - w*0.30, h), (testa_x + w*0.30, h)], fill=LUCE+(20,))
    alone = alone.filter(ImageFilter.GaussianBlur(w*0.045))
    # L'alone e il cono sforano la tela e il bordo li taglia di netto: si vedeva
    # un rettangolo chiaro attorno al lampione. Invece di calibrare i raggi (che
    # cambierebbero ad ogni misura), l'alpha viene sfumata verso i bordi: qualunque
    # geometria arrivi al bordo ci arriva ormai trasparente.
    m = max(2, int(min(w, h) * 0.16))
    maschera = Image.new("L", (w, h), 255); mp = maschera.load()
    for y in range(h):
        fy = min(1.0, min(y, h-1-y) / m)
        for x in range(w):
            fx = min(1.0, min(x, w-1-x) / m)
            f = min(fx, fy)
            if f < 1.0: mp[x, y] = int(255 * f*f*(3-2*f))   # smoothstep
    a = alone.getchannel("A").point(lambda v: v)
    alone.putalpha(Image.eval(Image.merge("L", (a,)), lambda v: v).point(lambda v: v))
    alone.putalpha(ImageChops.multiply(alone.getchannel("A"), maschera))
    im.alpha_composite(alone)

    d = ImageDraw.Draw(im)
    # ── palo, leggermente rastremato
    largh_giu, largh_su = w*0.085, w*0.045
    d.polygon([(px-largh_giu/2, h), (px+largh_giu/2, h),
               (px+largh_su/2, h*0.16), (px-largh_su/2, h*0.16)], fill=PALO)
    d.polygon([(px-largh_giu/2, h), (px-largh_giu/2+w*0.014, h),
               (px-largh_su/2+w*0.014, h*0.16), (px-largh_su/2, h*0.16)], fill=PALO_L)
    # piedino
    d.polygon([(px-w*0.075, h), (px+w*0.075, h), (px+w*0.05, h*0.93), (px-w*0.05, h*0.93)], fill=PALO)

    # ── braccio curvo: una spezzata che si alza e piega verso la strada
    punti = []
    for k in range(15):
        t = k/14
        bx = px + verso * (w*0.34) * (t**0.72)
        by = h*0.16 - (h*0.075) * (1 - (1-t)**2)
        punti.append((bx, by))
    d.line(punti, fill=PALO, width=int(w*0.038), joint="curve")

    # ── testa della lampada
    tw, th = w*0.20, h*0.028
    d.rounded_rectangle([testa_x-tw/2, testa_y-th/2, testa_x+tw/2, testa_y+th*1.5],
                        radius=int(th*0.8), fill=PALO)
    d.ellipse([testa_x-tw*0.38, testa_y+th*0.2, testa_x+tw*0.38, testa_y+th*1.5], fill=LUCE+(255,))

    return im.resize((W, H), Image.LANCZOS)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    lampione(135, 332, verso=+1).save(os.path.join(OUT, "DEAD_TREE1.png"))
    print("  DEAD_TREE1.png  135x332  lampione, braccio a destra")
    lampione(150, 260, verso=-1).save(os.path.join(OUT, "DEAD_TREE2.png"))
    print("  DEAD_TREE2.png  150x260  lampione, braccio a sinistra")
