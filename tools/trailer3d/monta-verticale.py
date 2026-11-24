# MONTAGGIO DELL'ANIMATIC VERTICALE (storyboard v2: 30 s, 9:16, comico). Mette i fotogrammi di animatic-verticale.py sui tempi di
# trailer/blender/STORYBOARD.md e scrive
#   animatic-verticale-30s.mp4   720×1280, 24 fps, muto
#   foglio-contatti.jpg          tutti i fotogrammi con sigla, tempo e gag
# Siccome è muto, le battute che nel trailer faranno la musica e il montaggio sono scritte in sovrimpressione (STOP, SILENZIO…)
# e i tre effetti di montaggio sono già simulati: lo zoom a scatto sui piedi (S04), il fermo immagine (S27) e la birra che
# attraversa il nero (S28). Gli altri fotogrammi hanno una spinta lenta, solo per dare vita.
# Richiede Pillow e ffmpeg.   uso: python monta-verticale.py <cartella fotogrammi> <cartella uscita> <cartella temporanea>
import sys, os, subprocess
from PIL import Image, ImageDraw, ImageFont

FPS = 24
W, H = 720, 1280
FONT = '/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf'
ATTI = {1: "L'EROE", 2: 'ARMI E LOTTA', 3: 'IL VIAGGIO', 4: 'IL BOSS', 5: 'CODA'}
COL = {1: (255, 190, 120), 2: (150, 210, 255), 3: (255, 150, 130), 4: (170, 140, 255), 5: (200, 200, 200)}

# (fotogramma o None = nero, sigla, titolo, atto, durata s, gag, effetto)
SEG = [
    ('S03', 'S03', 'Il cavallo sul dosso', 1, 2.0, 'musica solenne', None),
    ('S04', 'S04', 'I piedi', 1, 1.5, 'ZOOM A SCATTO · STOP MUSICA', 'scatto'),
    ('S05', 'S05', 'Sguardo in macchina', 1, 1.0, 'SILENZIO', 'lento'),
    ('S06', 'S06', 'La partenza', 1, 1.0, 'GAMBE A VUOTO · RIPARTE LA MUSICA', None),
    ('S08', 'S08', 'La cassa', 2, 1.5, 'PRESA AL VOLO', None),
    ('S09a', 'S09', 'Quattro armi', 2, 0.5, 'COLPO', None), ('S09b', 'S09', 'Quattro armi', 2, 0.5, 'COLPO', None),
    ('S09c', 'S09', 'Quattro armi', 2, 0.5, 'COLPO', None), ('S09d', 'S09', 'Quattro armi', 2, 0.5, 'COLPO', None),
    ('S10', 'S10', 'I predoni', 2, 0.5, '', None),
    ('S11', 'S11', 'Il duello', 2, 1.5, 'CADE RIGIDO · TONFO', None),
    ('S13a', 'S13', 'Il rotolo', 2, 0.5, '', None),
    ('S13b', 'S13', 'Il pluriball', 2, 1.0, 'BOLLE A CATENA', None),
    ('S14', 'S14', 'La Birra Grande', 2, 2.0, 'STOP · DOPPIA PRESA · SGUARDO IN MACCHINA', None),
    ('S15', 'S15', 'Piana del Tuul', 3, 0.5, '', None), ('S16', 'S16', 'Dune', 3, 0.5, 'IL LAMA LO SEGUE', None),
    ('S18', 'S18', 'Khar Balgas', 3, 0.5, '', None), ('S19', 'S19', 'Erdene Zuu', 3, 0.5, '', None),
    ('S20', 'S20', 'Karakorum, la terra trema', 3, 1.5, 'LA MUSICA SI SPEGNE', None),
    ('S21', 'S21', 'La schiena a gradini', 4, 1.0, 'TONFO', None),
    ('S22', 'S22', 'Sotto il ventre', 4, 2.0, 'TONFI A TEMPO · UNA GAMBA FUORI PASSO', None),
    ('S23', 'S23', 'La testa e la mascella', 4, 1.5, 'RUGGITO', None),
    ('S24', 'S24', 'Il cavallo e la sciabola', 4, 1.0, '', None),
    ('S25', 'S25', 'La carica', 4, 1.0, '', None),
    ('S26', 'S26', 'Il morso', 4, 1.0, 'TOSSE', None),
    ('S27', 'S27', 'Il salto', 4, 1.5, 'FERMO IMMAGINE · SGUARDO IN MACCHINA', 'fermo'),
    ('S27', 'S28', 'Coda', 5, 0.5, 'FERMO', 'fermo'),
    (None, 'S28', 'Coda (nero)', 5, 1.5, 'SPAZIO PER I TITOLI', None),
    ('S28', 'S28', 'Coda', 5, 1.0, 'LA BIRRA ATTRAVERSA IL NERO', 'attraversa'),
]

def tc(t): return '%d:%02d,%d' % (int(t // 60), int(t % 60), round((t % 1) * 10))

def overlay(i, inizio, totale, percorso):
    f, sigla, titolo, atto, dur, gag, _ = SEG[i]
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, 40); f2 = ImageFont.truetype(FONT, 26); f3 = ImageFont.truetype(FONT, 30)
    testo = '%s  %s' % (sigla, titolo.upper()); lung = d.textlength(testo, font=f1)
    d.rectangle((0, 0, lung + 40, 56), fill=(0, 0, 0, 160)); d.rectangle((0, 0, 8, 56), fill=COL[atto] + (255,))
    d.text((20, 8), testo, font=f1, fill=(255, 255, 255, 255))
    t2 = 'ATTO %d · %s' % (atto, ATTI[atto]) if atto < 5 else ATTI[atto]
    d.rectangle((0, 56, d.textlength(t2, font=f2) + 32, 92), fill=(0, 0, 0, 130)); d.text((20, 60), t2, font=f2, fill=COL[atto] + (255,))
    if gag:
        forte = gag.isupper()
        lg = d.textlength(gag, font=f3)
        d.rectangle((0, 100, lg + 32, 142), fill=((200, 40, 40, 220) if forte else (0, 0, 0, 130)))
        d.text((16, 105), gag, font=f3, fill=(255, 255, 255, 255))
    tt = '%s / %s' % (tc(inizio), tc(totale))
    d.rectangle((0, H - 52, d.textlength(tt, font=f2) + 28, H - 12), fill=(0, 0, 0, 150)); d.text((14, H - 48), tt, font=f2, fill=(255, 255, 255, 255))
    x = 0.0; t = 0.0
    for j, s in enumerate(SEG):
        w = s[4] / totale * W; cur = j == i
        d.rectangle((x, H - (10 if cur else 6), x + w - 1, H), fill=COL[s[3]] + (255 if cur else 90,)); x += w
    im.save(percorso)

def ffmpeg(*args): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *args], check=True)

def costruisci(fotogrammi, uscita, tmp):
    totale = sum(s[4] for s in SEG)
    nero = os.path.join(tmp, 'nero.png'); Image.new('RGB', (W, H), (0, 0, 0)).save(nero)
    lista, t = [], 0.0
    for i, s in enumerate(SEG):
        f, _, _, _, dur, _, eff = s
        n = int(round(dur * FPS)); ov = os.path.join(tmp, 'ov_%02d.png' % i); mp = os.path.join(tmp, 'seg_%02d.mp4' % i)
        overlay(i, t, totale, ov)
        src = nero if f is None else os.path.join(fotogrammi, f + '.jpg')
        if eff == 'attraversa':        # la birra (su fondo nero) scorre da sinistra a destra
            filtro = ("color=black:s=%dx%d:r=%d[bg];[0:v]scale=%d:%d[b];[bg][b]overlay=x='-%d+%d*t/%.3f':y=0:shortest=1[v];"
                      "[v][1:v]overlay=0:0:shortest=1,format=yuv420p" % (W, H, FPS, W, H, W * 0.8, W * 1.6, dur))
            ffmpeg('-loop', '1', '-framerate', str(FPS), '-i', src, '-loop', '1', '-framerate', str(FPS), '-i', ov,
                   '-filter_complex', filtro, '-frames:v', str(n), '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', mp)
        else:
            if f is None or eff == 'fermo': z, y = '1', "ih/2-(ih/zoom/2)"
            elif eff == 'scatto': z, y = "if(lt(on,5),1+0.6*on/5,1.6+0.03*(on-5)/%d)" % n, "ih*0.66-(ih/zoom/2)"    # piomba sui piedi
            elif eff == 'lento': z, y = "1+0.12*on/%d" % n, "ih/2-(ih/zoom/2)"
            else: z, y = "1+0.05*on/%d" % n, "ih/2-(ih/zoom/2)"
            ffmpeg('-i', src, '-loop', '1', '-framerate', str(FPS), '-i', ov, '-filter_complex',
                   "[0:v]scale=%d:%d,zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='%s':d=%d:s=%dx%d:fps=%d[b];[b][1:v]overlay=0:0:shortest=1,format=yuv420p"
                   % (W * 2, H * 2, z, y, n, W, H, FPS), '-frames:v', str(n), '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', mp)
        lista.append(mp); t += dur
    elenco = os.path.join(tmp, 'lista.txt')
    open(elenco, 'w').write(''.join("file '%s'\n" % p for p in lista))
    ffmpeg('-f', 'concat', '-safe', '0', '-i', elenco, '-c', 'copy', '-movflags', '+faststart', uscita)
    print('FATTO', uscita, '%.1f s' % totale, len(SEG), 'segmenti')

def foglio(fotogrammi, uscita):
    visti, t, info = [], 0.0, {}
    for s in SEG:
        if s[0] and s[0] not in info: info[s[0]] = (s, t); visti.append(s[0])
        t += s[4]
    cw, ch, col = 240, 427, 9; righe = (len(visti) + col - 1) // col
    sh = Image.new('RGB', (cw * col, (ch + 58) * righe), (20, 20, 20)); d = ImageDraw.Draw(sh)
    f = ImageFont.truetype(FONT, 24); g = ImageFont.truetype(FONT, 15)
    for i, k in enumerate(visti):
        x, y = (i % col) * cw, (i // col) * (ch + 58)
        sh.paste(Image.open(os.path.join(fotogrammi, k + '.jpg')).resize((cw, ch)), (x, y + 58))
        (s, t0) = info[k]
        d.text((x + 6, y + 4), '%s  %s · %.1f s' % (k, tc(t0), s[4]), font=f, fill=COL[s[3]])
        d.text((x + 6, y + 32), (s[5] or s[2])[:44], font=g, fill=(230, 230, 230))
    sh.save(uscita, quality=90)
    print('FATTO', uscita)

if __name__ == '__main__':
    fotogrammi, uscita, tmp = [os.path.abspath(a) for a in sys.argv[1:4]]
    os.makedirs(uscita, exist_ok=True); os.makedirs(tmp, exist_ok=True)
    costruisci(fotogrammi, os.path.join(uscita, 'animatic-verticale-30s.mp4'), tmp)
    foglio(fotogrammi, os.path.join(uscita, 'foglio-contatti.jpg'))
