# Foglio dei 12 mondi: le tappe del gioco rifatte dal kit (kit.py griglia), una per riquadro, con nome, sole e bioma.
# uso: python foglio-kit.py <cartella con tappa_00.jpg … tappa_11.jpg> <uscita .jpg>     (serve Pillow)
import sys, os
from PIL import Image, ImageDraw, ImageFont
NOMI = ['Fiume Kherlen', "Guado dell'Onon", 'Burkhan Khaldun', 'Piana del Tuul', 'Colline di Khustai', 'Dune di Elsen Tasarkhai', "Valle dell'Orkhon",
        'Cascate di Ulaan Tsutgalan', 'Monti Khangai', 'Rovine di Khar Balgas', 'Erdene Zuu', 'Karakorum']
SOLE = ['alba · sole 4°', 'mattina · 14°', 'mattina limpida · 28°', 'mezzogiorno · 58°', 'primo pomeriggio · 44°', 'afa · 38°', 'pomeriggio · 28°', 'tardo pomeriggio · 19°',
        "ora d'oro · 10°", 'tramonto · 3°', 'ora blu · −2°', 'notte · luna']
cartella, uscita = sys.argv[1], sys.argv[2]
FONT = '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'
cw, ch, col = 800, 335, 3
sh = Image.new('RGB', (cw * col, ch * 4), (16, 16, 16)); d = ImageDraw.Draw(sh); f1 = ImageFont.truetype(FONT, 30); f2 = ImageFont.truetype(FONT, 22)
for k in range(12):
    im = Image.open(os.path.join(cartella, 'tappa_%02d.jpg' % k)).resize((cw, ch)); x, y = (k % col) * cw, (k // col) * ch; sh.paste(im, (x, y))
    t1 = '%02d  %s' % (k + 1, NOMI[k].upper()); w = d.textlength(t1, font=f1)
    d.rectangle((x, y, x + w + 26, y + 40), fill=(0, 0, 0)); d.text((x + 12, y + 5), t1, font=f1, fill=(255, 255, 255))
    d.rectangle((x, y + ch - 30, x + d.textlength(SOLE[k], font=f2) + 20, y + ch), fill=(0, 0, 0)); d.text((x + 10, y + ch - 27), SOLE[k], font=f2, fill=(255, 205, 140))
sh.save(uscita, quality=90); print('FATTO', uscita)
