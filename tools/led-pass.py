#!/usr/bin/env python3
"""
Ritocco degli asset Poplar per il LEDWALL — da lanciare SUL POSTO, se serve.

Uso, dalla cartella del progetto:

    python3 tools/led-pass.py            # applica il ritocco (pavimento 14)
    python3 tools/led-pass.py 20         # più aggressivo, se banda ancora
    python3 tools/led-pass.py --annulla  # torna agli asset originali

Dopo OGNI lancio, nel gioco premi "↻ Ricarica asset Poplar", se no vedi ancora i
file vecchi (il browser li tiene in cache e non lo dice).

QUANDO SERVE — guardando il pannello vero, non lo schermo del portatile:
  - se le zone scure fanno FASCE o virano di colore → serve, lancialo;
  - se il cielo notturno è già nero pulito → NON serve, non lanciarlo: alzerebbe
    il nero e lo farebbe diventare grigio slavato.

Gli originali vengono salvati in images/poplar/_originali/ al primo lancio, quindi
--annulla funziona sempre.
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ledwall import per_ledwall
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "images", "poplar")
BAK  = os.path.join(OUT, "_originali")

# i cartelloni no: sono già ad alto contrasto e non hanno sfumature scure
BERSAGLI = ["sky.png", "trees.png", "PALM_TREE.png", "TREE1.png", "TREE2.png",
            "DEAD_TREE1.png", "DEAD_TREE2.png"]

def salva_originali():
    os.makedirs(BAK, exist_ok=True)
    for f in BERSAGLI:
        s, d = os.path.join(OUT, f), os.path.join(BAK, f)
        if os.path.exists(s) and not os.path.exists(d):
            shutil.copy2(s, d)

def annulla():
    if not os.path.isdir(BAK):
        sys.exit("non c'è niente da annullare: images/poplar/_originali/ non esiste")
    n = 0
    for f in BERSAGLI:
        s = os.path.join(BAK, f)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(OUT, f)); n += 1
    print(f"ripristinati {n} file. Ora premi ↻ Ricarica asset Poplar nel gioco.")

def applica(minimo):
    salva_originali()
    for f in BERSAGLI:
        s = os.path.join(BAK, f)                 # sempre dall'originale: non si accumula
        if not os.path.exists(s): continue
        im = Image.open(s)
        per_ledwall(im, minimo=minimo, ampiezza=2,
                    anche_alpha=f.startswith("DEAD_TREE")).save(os.path.join(OUT, f))
        print(f"  {f}")
    print(f"\nritocco applicato (pavimento {minimo}). Ora premi ↻ Ricarica asset Poplar.")
    print("Se il nero è diventato grigio slavato: python3 tools/led-pass.py --annulla")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] in ("--annulla", "--ripristina"): annulla()
    else: applica(int(a[0]) if a and a[0].isdigit() else 14)
