"""Cartelli del teaser, 1080x1920 trasparenti: testo largo e spaziato, con alone."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, os

W, H = 1080, 1920
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
COPPER = "/System/Library/Fonts/Supplemental/Copperplate.ttc"


def tracked(draw, text, font, tracking):
    widths = [draw.textlength(c, font=font) for c in text]
    return sum(widths) + tracking * (len(text) - 1), widths


def line(img, text, font, y, fill, tracking=0, glow=(255, 40, 40), glow_r=18, glow_a=200):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total, widths = tracked(d, text, font, tracking)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=font, fill=fill, anchor="ls")
        x += w + tracking
    if glow:
        g = layer.split()[3].filter(ImageFilter.GaussianBlur(glow_r))
        g = g.point(lambda v: min(255, int(v * glow_a / 100)))
        halo = Image.new("RGBA", img.size, glow + (0,))
        halo.putalpha(g)
        img.alpha_composite(halo)
    img.alpha_composite(layer)


# 1) apertura: "C’ERA UNA VOLTA UN GIOCO" su una sfumatura scura (dentro la zona sicura delle storie)
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
grad = Image.new("L", (1, H), 0)
for y in range(H):
    k = min(1.0, max(0.0, (y - 1150) / 420))
    grad.putpixel((0, y), int(205 * k ** 1.4))
band = Image.new("RGBA", (W, H), (8, 0, 4, 0))
band.putalpha(grad.resize((W, H)))
img.alpha_composite(band)
f = ImageFont.truetype(COPPER, 64, index=0)
line(img, "C’ERA UNA VOLTA", f, 1470, (245, 240, 235, 255), tracking=12, glow=(0, 0, 0), glow_r=22, glow_a=420)
line(img, "UN GIOCO", f, 1562, (245, 240, 235, 255), tracking=12, glow=(0, 0, 0), glow_r=22, glow_a=420)
img.save(f"{OUT}/t1_cera.png")

# 2) titolo: "CAVALLI MONGOLI"
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
big = ImageFont.truetype(DIDOT, 150, index=2 if True else 0)
line(img, "CAVALLI", big, 930, (255, 255, 255, 255), tracking=14, glow=(255, 30, 50), glow_r=28, glow_a=160)
line(img, "MONGOLI", big, 1090, (255, 255, 255, 255), tracking=14, glow=(255, 30, 50), glow_r=28, glow_a=160)
img.save(f"{OUT}/t2_titolo.png")

# 3) sottotitolo: "RINASCE"
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
f = ImageFont.truetype(COPPER, 76, index=0)
line(img, "RINASCE", f, 1260, (255, 45, 60, 255), tracking=34, glow=(255, 0, 30), glow_r=16, glow_a=180)
img.save(f"{OUT}/t3_rinasce.png")
print("ok")

# 4) vignettatura: nero radiale ai bordi (sopra il girato, sotto i titoli)
import math
small = Image.new("L", (W // 4, H // 4), 0)
for y in range(H // 4):
    for x in range(W // 4):
        dx = (x - W / 8) / (W / 8)
        dy = (y - H / 8) / (H / 8)
        r = math.sqrt(dx * dx * 1.0 + dy * dy * 0.85)
        k = min(1.0, max(0.0, (r - 0.45) / 0.75))
        small.putpixel((x, y), int(215 * k ** 1.6))
vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vig.putalpha(small.resize((W, H), Image.BICUBIC))
vig.save(f"{OUT}/vignettatura.png")
print("vignettatura ok")
