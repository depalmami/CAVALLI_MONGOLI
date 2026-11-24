# MONTAGGIO DELL'ANIMATIC: mette i fotogrammi di animatic.py sui tempi di trailer/blender/STORYBOARD.md e scrive
#   animatic-60s.mp4        la versione principale (60 s, 24 fps)
#   animatic-30s-ritmo.mp4  il taglio breve, stessi fotogrammi (serve a provare il ritmo, non le inquadrature verticali)
#   foglio-contatti.jpg     tutti i fotogrammi con sigla e tempi
# Muto, con una spinta lenta sull'immagine (solo per dare vita) e una scritta in alto con sigla, titolo e tempo.
# Richiede Pillow (python3 -m venv v && v/bin/pip install pillow) e ffmpeg.
# uso: python monta-animatic.py <cartella fotogrammi> <cartella uscita> <cartella temporanea>
import sys, os, subprocess
from PIL import Image, ImageDraw, ImageFont

FPS = 24
W, H = 1280, 536
FONT = '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'
ATTI = {1: 'ALBA', 2: 'CAVALCATA E LOTTA', 3: 'IL VIAGGIO', 4: 'IL BOSS', 5: 'CODA'}
COL = {1: (255, 190, 120), 2: (150, 210, 255), 3: (255, 150, 130), 4: (170, 140, 255), 5: (200, 200, 200)}

# (sigla, titolo, atto, durata 60 s, durata 30 s, [(fotogramma, quota 60 s, quota 30 s), ...])
SHOT = [
    ('S01', 'Alba sul Kherlen', 1, 3.0, 1.0, None), ('S02', 'Il branco', 1, 2.0, 0, None), ('S03', 'Il cavallo sul dosso', 1, 3.0, 1.5, None),
    ('S04', 'I piedi', 1, 2.0, 0.5, None), ('S05', 'Muso e redini', 1, 2.0, 1.0, None),
    ('S06', 'La partenza', 2, 1.5, 1.0, None), ('S07', 'Galoppo sulla strada', 2, 2.0, 1.0, None), ('S08', 'La cassa', 2, 2.0, 1.0, None),
    ('S09', 'Quattro armi', 2, 4.0, 2.0, [('S09a', 1.0, .5), ('S09b', 1.0, .5), ('S09c', 1.0, .5), ('S09d', 1.0, .5)]),
    ('S10', 'I predoni', 2, 3.0, 1.0, None), ('S11', 'Il duello', 2, 3.0, 1.5, None), ('S12', 'Schivata e frusta', 2, 2.0, 0, None),
    ('S13', 'Il pluriball', 2, 3.0, 1.5, [('S13a', 1.0, .5), ('S13b', 2.0, 1.0)]), ('S14', 'La Birra Grande', 2, 1.5, 1.0, None),
    ('S15', 'Piana del Tuul', 3, 1.5, .5, None), ('S16', 'Dune di Elsen Tasarkhai', 3, 1.5, .5, None), ('S17', 'Cascate di Ulaan Tsutgalan', 3, 1.5, 0, None),
    ('S18', "Khar Balgas e l'aquila", 3, 1.5, 1.0, None), ('S19', 'Erdene Zuu', 3, 2.0, 1.5, None), ('S20', 'Karakorum, la terra trema', 3, 2.0, 1.5, None),
    ('S21', 'La schiena a gradini', 4, 2.0, 1.5, None), ('S22', 'Sotto il ventre', 4, 2.0, 1.5, None), ('S23', 'La testa e la mascella', 4, 2.0, 1.5, None),
    ('S24', 'Il cavallo e la sciabola', 4, 1.5, 1.0, None), ('S25', 'La carica', 4, 2.0, 1.5, None), ('S26', 'Il morso', 4, 2.0, 1.0, None),
    ('S27', 'Il salto', 4, 2.5, 1.0, None), ('S28', 'Coda', 5, 2.0, 2.0, 'nero'),
]

def tc(t):
    return '%d:%02d,%d' % (int(t // 60), int(t % 60), round((t % 1) * 10))

def segmenti(versione):
    """Elenco di (sigla, titolo, atto, fotogramma, inizio, durata) per la versione '60' o '30'."""
    out, t = [], 0.0
    for sigla, titolo, atto, d60, d30, sub in SHOT:
        d = d60 if versione == '60' else d30
        if not d: continue
        if sub == 'nero':                                            # la coda: 1 s sull'ultimo fotogramma, poi nero
            out.append((sigla, titolo, atto, 'S27', t, d / 2)); out.append((sigla, titolo + ' (nero)', atto, None, t + d / 2, d / 2)); t += d; continue
        if sub:
            for f, q60, q30 in sub:
                dd = q60 if versione == '60' else q30
                out.append((sigla, titolo, atto, f, t, dd)); t += dd
        else:
            out.append((sigla, titolo, atto, sigla, t, d)); t += d
    return out, t

def overlay(seg, totale, versione, percorso):
    sigla, titolo, atto, _, inizio, dur = seg
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, 30); f2 = ImageFont.truetype(FONT, 22)
    testo = '%s   %s' % (sigla, titolo.upper()); lung = d.textlength(testo, font=f1)
    d.rectangle((0, 0, lung + 36, 44), fill=(0, 0, 0, 150)); d.rectangle((0, 0, 6, 44), fill=COL[atto] + (255,))
    d.text((18, 6), testo, font=f1, fill=(255, 255, 255, 255))
    t2 = 'ATTO %d · %s' % (atto, ATTI[atto]) if atto < 5 else ATTI[atto]
    d.rectangle((W - 12 - d.textlength(t2, font=f2) - 14, 0, W, 34), fill=(0, 0, 0, 150)); d.text((W - 12 - d.textlength(t2, font=f2), 5), t2, font=f2, fill=COL[atto] + (255,))
    tt = '%s / %s' % (tc(inizio), tc(totale))
    d.rectangle((0, H - 40, d.textlength(tt, font=f2) + 24, H - 8), fill=(0, 0, 0, 150)); d.text((12, H - 36), tt, font=f2, fill=(255, 255, 255, 255))
    # barra del tempo: un tratto per segmento, il corrente più alto e chiaro
    y0 = H - 6; x = 0.0
    for s in SEG_ALL[versione]:
        w = s[5] / totale * W; cur = (s[4] == inizio and s[3] == seg[3])
        d.rectangle((x, y0 - (4 if cur else 0), x + w - 1, H), fill=COL[s[2]] + (255 if cur else 90,)); x += w
    im.save(percorso)

def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *args], check=True)

def costruisci(versione, fotogrammi, uscita, tmp):
    seg, totale = segmenti(versione); SEG_ALL[versione] = seg
    nero = os.path.join(tmp, 'nero.png'); Image.new('RGB', (W, H), (0, 0, 0)).save(nero)
    lista = []
    for i, s in enumerate(seg):
        n = int(round(s[5] * FPS)); ov = os.path.join(tmp, 'ov_%s_%02d.png' % (versione, i)); mp = os.path.join(tmp, 'seg_%s_%02d.mp4' % (versione, i))
        overlay(s, totale, versione, ov)
        src = nero if s[3] is None else os.path.join(fotogrammi, s[3] + '.jpg')
        zoom = "1+0.05*on/%d" % n if s[3] else '1'
        ffmpeg('-i', src, '-loop', '1', '-framerate', str(FPS), '-i', ov, '-filter_complex',
               "[0:v]scale=%d:%d,zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d[b];[b][1:v]overlay=0:0:shortest=1,format=yuv420p" % (W*2, H*2, zoom, n, W, H, FPS),
               '-frames:v', str(n), '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', mp)
        lista.append(mp)
    elenco = os.path.join(tmp, 'lista_%s.txt' % versione)
    open(elenco, 'w').write(''.join("file '%s'\n" % p for p in lista))
    ffmpeg('-f', 'concat', '-safe', '0', '-i', elenco, '-c', 'copy', '-movflags', '+faststart', uscita)
    print('FATTO', uscita, '%.1f s' % totale, len(seg), 'segmenti')

def foglio(fotogrammi, uscita):
    segs, _ = segmenti('60'); visti = []
    for s in segs:
        if s[3] and s[3] not in visti: visti.append(s[3])
    info = {}
    for s in segs:
        if s[3] and s[3] not in info: info[s[3]] = s
    cw, ch, col = 640, 268, 4; righe = (len(visti) + col - 1) // col
    sh = Image.new('RGB', (cw * col, ch * righe), (20, 20, 20)); d = ImageDraw.Draw(sh); f = ImageFont.truetype(FONT, 24)
    for i, k in enumerate(visti):
        im = Image.open(os.path.join(fotogrammi, k + '.jpg')).resize((cw, ch)); x, y = (i % col) * cw, (i // col) * ch; sh.paste(im, (x, y))
        s = info[k]; testo = '%s  %s  ·  %s  ·  %.1f s' % (k, s[1].upper(), tc(s[4]), s[5])
        d.rectangle((x, y, x + d.textlength(testo, font=f) + 20, y + 32), fill=(0, 0, 0)); d.text((x + 10, y + 3), testo, font=f, fill=COL[s[2]])
    sh.save(uscita, quality=90)
    print('FATTO', uscita)

SEG_ALL = {}
if __name__ == '__main__':
    fotogrammi, uscita, tmp = [os.path.abspath(a) for a in sys.argv[1:4]]
    os.makedirs(uscita, exist_ok=True); os.makedirs(tmp, exist_ok=True)
    costruisci('60', fotogrammi, os.path.join(uscita, 'animatic-60s.mp4'), tmp)
    costruisci('30', fotogrammi, os.path.join(uscita, 'animatic-30s-ritmo.mp4'), tmp)
    foglio(fotogrammi, os.path.join(uscita, 'foglio-contatti.jpg'))
