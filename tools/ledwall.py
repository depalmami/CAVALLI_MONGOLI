#!/usr/bin/env python3
"""
Ritocchi per il LEDWALL, da usare sugli asset della modalità Poplar.

Perché servono: i pannelli LED sono al loro peggio nei grigi bassi — pochi livelli
utili, banding e virate di colore — e la sera il pannello viene tenuto a luminosità
ridotta, il che riduce ancora i toni disponibili in basso. Misurato sugli asset
nostri: metà di sky.png stava sotto luminanza 8 su 255, cioè nella fascia peggiore.

Due correzioni, entrambe conservative:
  - alza_pavimento(): rimappa i valori in modo che il nero non tocchi mai lo zero.
    Il buio resta buio all'occhio (il pannello è luminoso, 14/255 legge come nero)
    ma il dettaglio entra in una zona che il LED riesce davvero a distinguere.
  - dithera(): rumore di ±1-2 livelli SOLO nelle zone scure. Le sfumature morbide
    su fondo quasi nero sono ciò che banda di più; il rumore rompe le fasce.

ATTENZIONE — non applicarle "per sicurezza". Il ledwall il NERO VERO lo fa benissimo
(pixel spento) ed è il suo punto di forza: alzare il pavimento su tutta l'immagine
trasforma il cielo notturno in un grigio lattiginoso e butta via proprio quel
vantaggio. Vanno usate SOLO se sul pannello vero si vede il difetto opposto, cioè
banding e virate nelle zone scure. Si guarda, si decide, si applica.

Su un proiettore non servirebbero affatto: là il problema è rovesciato, i neri si
alzano da soli per la luce ambientale.
"""
import random
from PIL import Image

def alza_pavimento(im, minimo=14):
    """0 → minimo, 255 resta 255. Lineare: non tocca i rapporti fra i toni."""
    tabella = [round(minimo + v * (255 - minimo) / 255) for v in range(256)]
    alpha = im.getchannel("A") if im.mode == "RGBA" else None
    rgb = im.convert("RGB").point(tabella * 3)
    if alpha is None:
        return rgb
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out

def dithera(im, ampiezza=2, soglia=72, seme=5, anche_alpha=False):
    """Rumore ±ampiezza dove è scuro (luminanza < soglia). Sopra soglia non tocca
    niente, così le luci della città restano pulite."""
    rnd = random.Random(seme)
    ha_alpha = im.mode == "RGBA"
    im = im.convert("RGBA") if ha_alpha else im.convert("RGB")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            r, g, b = p[0], p[1], p[2]
            lum = (r*299 + g*587 + b*114) // 1000
            if lum >= soglia:
                continue
            n = rnd.randint(-ampiezza, ampiezza)
            nr = min(255, max(0, r + n)); ng = min(255, max(0, g + n)); nb = min(255, max(0, b + n))
            if ha_alpha:
                a = p[3]
                if anche_alpha and 0 < a < 255:
                    a = min(255, max(0, a + rnd.randint(-ampiezza, ampiezza)))
                px[x, y] = (nr, ng, nb, a)
            else:
                px[x, y] = (nr, ng, nb)
    return im

def per_ledwall(im, minimo=14, ampiezza=2, anche_alpha=False):
    return dithera(alza_pavimento(im, minimo), ampiezza=ampiezza, anche_alpha=anche_alpha)
