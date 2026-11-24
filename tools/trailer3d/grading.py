"""GRADING DEL TRAILER (24 nov): un look unico sopra rendering che vengono da luci molto diverse (alba in Cycles, giorno in EEVEE, notte).
Tutto con ffmpeg (eq, curves, colorbalance, vignette, noise), un gruppo di shot per volta, senza toccare i render.

  python3 tools/trailer3d/grading.py prova  <cartella>      un fotogramma per shot, prima/dopo, e il foglio di confronto
  python3 tools/trailer3d/grading.py video                  trailer-30s-muto.mp4 → trailer-30s-graduato.mp4 (con l'audio della bozza, se c'è)

Cosa si corregge, misurato sui fotogrammi non graduati (luminosità media, saturazione, percentili):
 · il GIORNO (S08–S16) è lattiginoso: il nero più scuro sta a 0,4–0,5 e la saturazione a 30–40 su 255 → curva con punto di nero forte e più saturazione;
 · la NOTTE (S20–S27) è buia (media 40/255, il 95° percentile a 90) e il blu è saturo (140–180): si schiarisce con la GAMMA (non col contrasto: schiaccia
   le notti), si toglie saturazione e le ombre vanno sul ciano;
 · l'ALBA (S03–S06) va già bene: solo un tocco di contrasto e il caldo sulle luci;
 · il NERO della coda resta nero (niente grana, niente curve che lo alzino).
Su tutto: una vignetta leggera (in ffmpeg l'angolo PIÙ GRANDE scurisce di PIÙ: 0,32 rad toglie il 17% negli angoli, 0,63 di default è già troppo) e un filo di grana (cuce i rendering di motori diversi)."""
import sys, os, subprocess
QUI = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.path.abspath(os.path.join(QUI, '..', '..', 'trailer', 'blender'))
FPS = 24

# (shot, primo fotogramma, ultimo escluso) sul video montato di 720 fotogrammi
SHOT = [('S03', 0, 48), ('S04', 48, 84), ('S05', 84, 108), ('S06', 108, 132), ('S08', 132, 168), ('S09a', 168, 180), ('S09b', 180, 192),
        ('S09c', 192, 204), ('S09d', 204, 216), ('S10', 216, 228), ('S11', 228, 264), ('S13a', 264, 276), ('S13b', 276, 300), ('S14', 300, 348),
        ('S15', 348, 360), ('S16', 360, 372), ('S18', 372, 384), ('S19', 384, 396), ('S20', 396, 432), ('S21', 432, 456), ('S22', 456, 504),
        ('S23', 504, 540), ('S24', 540, 564), ('S25', 564, 588), ('S26', 588, 612), ('S27', 612, 648), ('fermo', 648, 660), ('nero', 660, 696), ('S28', 696, 720)]
GRUPPO = {**{s: 'alba' for s in ('S03', 'S04', 'S05', 'S06')},
          **{s: 'giorno' for s in ('S08', 'S09a', 'S09b', 'S09c', 'S09d', 'S10', 'S11', 'S13a', 'S13b', 'S14')}, 'S15': 'profilo', 'S16': 'profilo',
          'S18': 'tramonto', 'S19': 'orablu',
          **{s: 'notte' for s in ('S20', 'S21', 'S22', 'S23', 'S24', 'S25', 'S26')}, 'S27': 'lunapiena', 'fermo': 'lunapiena', 'nero': 'nero', 'S28': 'birra'}

# eq: contrasto, luminosità, saturazione, gamma · curva: punti x/y della curva generale · bil: colorbalance (ombre rs gs bs, medi rm gm bm, luci rh gh bh)
LOOK = {
    'alba':     dict(eq='contrast=1.07:saturation=1.08', curva='0/0 0.25/0.21 0.6/0.62 0.9/0.93 1/1', bil='rs=-0.03:bs=0.04:rh=0.04:bh=-0.04', vig=0.32, grana=2, alone=0.30),
    'giorno':   dict(eq='contrast=1.04:saturation=1.38', curva='0/0 0.30/0.21 0.55/0.52 0.8/0.85 1/1', bil='rs=-0.03:bs=0.04:rh=0.04:bh=-0.04:rm=0.01', vig=0.32, grana=2, alone=0.0),
    'profilo':  dict(eq='contrast=1.03:saturation=1.38:gamma=1.12', curva='0/0 0.28/0.22 0.55/0.52 0.8/0.84 1/1', bil='rs=-0.02:bs=0.04:rh=0.04:bh=-0.04', vig=0.32, grana=2, alone=0.0),
    'tramonto': dict(eq='contrast=1.06:saturation=1.12:gamma=1.06', curva='0/0 0.3/0.25 0.6/0.6 0.9/0.93 1/1', bil='rs=-0.02:bs=0.04:rh=0.03:bh=-0.03', vig=0.32, grana=2, alone=0.35),
    'orablu':   dict(eq='gamma=1.3:saturation=1.25:contrast=1.06', curva='0/0 0.3/0.3 0.7/0.78 1/1', bil='rs=-0.02:bs=0.03:rh=0.03:bh=-0.02', vig=0.32, grana=2, alone=0.25),
    'notte':    dict(eq='gamma=1.55:saturation=0.92:contrast=1.1', curva='0/0 0.14/0.10 0.4/0.45 0.75/0.87 1/1', bil='rs=-0.04:gs=0.01:bs=0.03:rh=0.02', vig=0.36, grana=3, alone=0.40),
    # S27 e il fermo: la luna enorme riempie il quadro. Con la gamma della notte (1,55) diventava un disco bianco senza mari né crateri: qui poca gamma, le luci rientrate e un alone più piccolo
    'lunapiena': dict(eq='gamma=1.12:saturation=0.95:contrast=1.08', curva='0/0 0.14/0.11 0.4/0.43 0.75/0.78 0.92/0.88 1/0.95', bil='rs=-0.04:gs=0.01:bs=0.03:rh=0.02', vig=0.36, grana=3, alone=0.22),
    'birra':    dict(eq='contrast=1.05:saturation=1.3', curva='0/0 1/1', bil='', vig=0.32, grana=0, alone=0.0),
    'nero':     None,
}

def catena(g, i=0):
    """La catena di filtri di un gruppo, da attaccare a un'uscita già pronta; i = indice per i nomi delle etichette (l'alone usa split)."""
    L = LOOK[g]
    if L is None: return 'null'
    f = ['eq=' + L['eq'], "curves=master='%s'" % L['curva']]
    if L['bil']: f.append('colorbalance=' + L['bil'])
    s = ','.join(f)
    if L['alone']:                                          # alone: le luci forti (sole, luna) sfumate e sommate in «screen»
        s += ",split=2[a%d][b%d];[b%d]curves=master='0/0 0.62/0 1/1',gblur=sigma=28[g%d];[a%d][g%d]blend=all_mode=screen:all_opacity=%.2f" % (i, i, i, i, i, i, L['alone'])
    post = []
    if L['vig']: post.append('vignette=angle=%.2f' % L['vig'])
    if L['grana']: post.append('noise=alls=%d:allf=t' % L['grana'])
    return s + (',' + ','.join(post) if post else '')

def ff(*a): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *a], check=True)

def prova(cartella):
    from PIL import Image, ImageDraw
    os.makedirs(cartella, exist_ok=True); muto = os.path.join(BLENDER, 'trailer-30s-muto.mp4'); coppie = []
    for n, a, b in SHOT:
        if n == 'nero': continue
        f = (a + b) // 2; pr = os.path.join(cartella, 'prima-%s.png' % n); dp = os.path.join(cartella, 'dopo-%s.png' % n)
        ff('-i', muto, '-vf', 'select=eq(n\\,%d),scale=540:960' % f, '-vframes', '1', pr)
        ff('-i', muto, '-filter_complex', '[0:v]select=eq(n\\,%d),%s,scale=540:960[o]' % (f, catena(GRUPPO[n], 0)), '-map', '[o]', '-vframes', '1', dp)
        coppie.append((n, pr, dp))
    cols = 14; w, h = 216, 384; rows = (len(coppie) + cols - 1) // cols
    W = Image.new('RGB', (w * cols, h * 2 * rows))
    for i, (n, pr, dp) in enumerate(coppie):
        for k, p in enumerate((pr, dp)):
            im = Image.open(p).convert('RGB').resize((w, h)); d = ImageDraw.Draw(im); d.rectangle((0, 0, 70, 14), fill=(0, 0, 0)); d.text((3, 1), '%s %s' % (n, 'prima' if k == 0 else 'dopo'), fill=(255, 255, 255))
            W.paste(im, (w * (i % cols), h * (2 * (i // cols) + k)))
    W.save(os.path.join(cartella, 'foglio-prima-dopo.jpg'), quality=90); print('FOGLIO', os.path.join(cartella, 'foglio-prima-dopo.jpg'))

def video():
    muto = os.path.join(BLENDER, 'trailer-30s-muto.mp4'); musica = os.path.join(BLENDER, 'trailer-30s-musica.mp4'); out = os.path.join(BLENDER, 'trailer-30s-graduato.mp4')
    parti = []; labs = ''
    for i, (n, a, b) in enumerate(SHOT):
        parti.append('[0:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS,%s[v%d]' % (a, b, catena(GRUPPO[n], i), i)); labs += '[v%d]' % i
    filt = ';'.join(parti) + ';' + labs + 'concat=n=%d:v=1:a=0[o]' % len(SHOT)
    args = ['-i', muto]
    if os.path.exists(musica): args += ['-i', musica, '-map', '[o]', '-map', '1:a', '-c:a', 'copy']
    else: args += ['-map', '[o]']
    ff(*args, '-filter_complex', filt, '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-threads', '4', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-shortest', '-movflags', '+faststart', out)
    print('VIDEO', out)

if __name__ == '__main__':
    if sys.argv[1] == 'prova': prova(os.path.abspath(sys.argv[2]))
    else: video()
