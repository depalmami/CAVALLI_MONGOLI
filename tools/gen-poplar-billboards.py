#!/usr/bin/env python3
"""
Genera i cartelloni della MODALITÀ POPLAR in images/poplar/.

I testi stanno tutti nella tabella CARTELLONI qui sotto: si cambiano le parole e si
rilancia lo script, non serve toccare altro. Nel gioco basta poi premere "Ricarica
asset" nel banco di regia.

Le misure NON sono libere: il gioco disegna lo sprite sostitutivo dentro il rettangolo
dell'atlas (common.js, SPRITES.BILLBOARD0N), quindi un PNG con proporzioni diverse
esce schiacciato. SLOT tiene le misure vere.

Font: assets/fonts/poplar/ (scaricati dal sito del festival, non committati).
ATTENZIONE al font-logo Poplar-26-Def: ha 34 glifi. Ci sono A C E F I L O P R S T U V
e le cifre 1 2 4 5 6. NON ci sono B D G H J K M N Q W X Y Z né 0 3 7 8 9.
Se una parola contiene una lettera che manca, lo script lo dice e usa il Solar.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts", "poplar")
OUT   = os.path.join(ROOT, "images", "poplar")
SS    = 4                                    # supersampling: si disegna 4x e si riduce

LOGO  = os.path.join(FONTS, "Poplar-26-Def.ttf")          # solo per POPLAR/CAVALLI/FESTIVAL…
SOLAR = os.path.join(FONTS, "ABCSolarDisplay-Ultra.ttf")  # display grasso
GTB   = os.path.join(FONTS, "GT-Standard-Black.otf")      # testo di servizio

ROSSO, CREMA, NERO, BIANCO = (214,38,32), (238,232,220), (17,15,16), (255,255,255)

# misure reali degli slot, da common.js
SLOT = {"BILLBOARD01":(300,170), "BILLBOARD02":(215,220), "BILLBOARD03":(230,220),
        "BILLBOARD04":(268,170), "BILLBOARD05":(298,190), "BILLBOARD06":(298,190),
        "BILLBOARD07":(298,190), "BILLBOARD08":(385,265), "BILLBOARD09":(328,282)}

# ── Slot lasciati ai cartelloni DELLA BAND ────────────────────────────────────
# Sei livelli su sette montano i cartelloni di serie di javascript-racer (SEGA,
# LiquidPlanner, Code inComplete...): lasciare uno slot vuoto li farebbe tornare.
# L'unico set davvero nostro e' quello di 4-cantiere, quindi invece di generare
# questi slot li COPIAMO da li': cosi' le battute della band girano su tutti e
# sette i livelli, non solo sul cantiere.
# Per riprendersi uno slot basta toglierlo da qui e rimetterlo in CARTELLONI.
NOSTRI = {
  "BILLBOARD05": "4-cantiere",   # HOLEY MOLEY
  "BILLBOARD06": "4-cantiere",   # MIGHTY DUCTS
  "BILLBOARD07": "4-cantiere",   # BOB IL DISTRUTTORE
  "BILLBOARD09": "4-cantiere",   # POSA & PREGA
}

GLIFI_LOGO = set(" !12456ACEFILOPRSTUVacefiloprstuv")
def logo_puo(t): return all(c in GLIFI_LOGO for c in t)

# ── I TESTI — prima passata, da rivedere con la band ────────────────────────
# (font, testo, colore) per riga; "bg" = fondo del cartello
CARTELLONI = {
  "BILLBOARD01": dict(bg=ROSSO, righe=[(LOGO,"POPLAR",CREMA), (GTB,"11 SETTEMBRE",CREMA)]),
  "BILLBOARD02": dict(bg=ROSSO, righe=[(SOLAR,"STILL",CREMA), (SOLAR,"RAVING",CREMA), (SOLAR,"AL DOSS",CREMA)]),
  "BILLBOARD03": dict(bg=NERO,  righe=[(LOGO,"CAVALLI",ROSSO), (SOLAR,"MONGOLI",CREMA)]),
  "BILLBOARD04": dict(bg=CREMA, righe=[(GTB,"AREA PROTETTA",NERO), (GTB,"NATURA 2000",NERO), (GTB,"VIETATO AI CAVALLI",ROSSO)]),
  "BILLBOARD05": dict(bg=CREMA, righe=[(GTB,"NON DISTURBARE",NERO), (GTB,"LA FAUNA",NERO), (GTB,"PROTETTA",ROSSO)]),
  "BILLBOARD06": dict(bg=NERO,  righe=[(GTB,"PROSSIMA USCITA",CREMA), (SOLAR,"PIEDICASTELLO",ROSSO)]),
  "BILLBOARD07": dict(bg=ROSSO, righe=[(SOLAR,"SALITA",CREMA), (SOLAR,"AL DOSS",CREMA)]),
  "BILLBOARD08": dict(bg=NERO,  righe=[(GTB,"FOTO",CREMA), (GTB,"@poplar_festival",CREMA),
                                       (GTB,"Zairon · Jumk18 · CC BY-SA",CREMA)]),
  "BILLBOARD09": dict(bg=CREMA, righe=[(LOGO,"FESTIVAL",ROSSO), (GTB,"AL DOSS DAL 2017",NERO)]),
}

def misura(path, size, testo):
    f = ImageFont.truetype(path, size)
    b = f.getbbox(testo)
    return f, b[2]-b[0], b[3]-b[1], b

def adatta(path, testo, maxw, maxh):
    """la size più grande che sta dentro maxw x maxh"""
    lo, hi = 6, maxh*2
    best = ImageFont.truetype(path, 6)
    while lo <= hi:
        mid = (lo+hi)//2
        f, w, h, _ = misura(path, mid, testo)
        if w <= maxw and h <= maxh: best, lo = f, mid+1
        else: hi = mid-1
    return best

def disegna(nome, spec):
    W, H = SLOT[nome]
    w, h = W*SS, H*SS
    im = Image.new("RGB", (w, h), spec["bg"])
    d  = ImageDraw.Draw(im)

    pad     = int(w*0.06)
    righe   = spec["righe"]
    # la prima riga pesa il doppio delle altre: è il titolo
    pesi    = [2.0] + [1.0]*(len(righe)-1)
    tot     = sum(pesi)
    utile   = h - pad*2
    gap     = int(h*0.02)
    y       = pad

    for (path, testo, colore), peso in zip(righe, pesi):
        if path == LOGO and not logo_puo(testo):
            mancanti = "".join(sorted(set(c for c in testo if c not in GLIFI_LOGO)))
            print(f"    ! {nome}: '{testo}' non è scrivibile col font-logo (manca: {mancanti}) → uso Solar")
            path = SOLAR
        alt = int((utile - gap*(len(righe)-1)) * peso/tot)
        f   = adatta(path, testo, w-pad*2, alt)
        b   = f.getbbox(testo)
        d.text(((w-(b[2]+b[0]))//2, y - b[1] + (alt-(b[3]-b[1]))//2), testo, font=f, fill=colore)
        y  += alt + gap

    # bordino, così il cartello stacca dallo sfondo del livello
    d.rectangle([0,0,w-1,h-1], outline=CREMA if spec["bg"] != CREMA else NERO, width=SS*2)

    im = im.resize((W, H), Image.LANCZOS)
    p  = os.path.join(OUT, nome + ".png")
    im.save(p)
    return p

def copia_nostro(nome, cartella):
    """Porta dentro la modalità un cartellone gia' disegnato dalla band."""
    src = os.path.join(ROOT, "images", "levels", cartella, nome + ".png")
    if not os.path.exists(src):
        print(f"    ! manca {src} — slot saltato"); return None
    im = Image.open(src).convert("RGBA")
    if im.size != SLOT[nome]:
        im = im.resize(SLOT[nome], Image.LANCZOS)   # lo slot ha una misura fissa
    dst = os.path.join(OUT, nome + ".png")
    im.save(dst)
    return dst

if __name__ == "__main__":
    for f in (LOGO, SOLAR, GTB):
        if not os.path.exists(f):
            sys.exit(f"manca il font {f} — vedi assets/fonts/poplar/")
    os.makedirs(OUT, exist_ok=True)
    for nome in sorted(set(CARTELLONI) | set(NOSTRI)):
        if nome in NOSTRI:
            if copia_nostro(nome, NOSTRI[nome]):
                print(f"  {nome}.png  {SLOT[nome][0]}x{SLOT[nome][1]}  ← nostro, da {NOSTRI[nome]}")
        elif nome in CARTELLONI:
            disegna(nome, CARTELLONI[nome])
            print(f"  {nome}.png  {SLOT[nome][0]}x{SLOT[nome][1]}  Poplar")
    print(f"\n{len(CARTELLONI)-len(set(CARTELLONI)&set(NOSTRI))} Poplar + {len(NOSTRI)} nostri in images/poplar/")
