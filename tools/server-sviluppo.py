#!/usr/bin/env python3
"""Server statico per provare il gioco mentre lo si modifica.

È `python3 -m http.server` con una differenza: dice al browser di NON tenere copie in cache
(Cache-Control: no-store). Col server normale Safari e Chrome tengono i moduli JavaScript in cache
e, dopo una modifica, possono caricare la pagina nuova insieme a un modulo vecchio: il 9 ottobre 2026
la pagina fermava il gioco per la scelta del bonus, ma il vecchio 3d/hud.js non sapeva disegnare il
menu e il gioco restava bloccato.

Uso, dalla cartella del progetto:
    python3 tools/server-sviluppo.py              # http://127.0.0.1:8901/horse-racing-3d.html
    python3 tools/server-sviluppo.py 8901 0.0.0.0 # visibile dalla rete di casa (telefono)
"""
import http.server, os, sys

class SenzaCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8901
indirizzo = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
print(f'Cavalli Mongoli: http://{indirizzo}:{porta}/horse-racing-3d.html  (senza cache, Ctrl+C per fermare)')
http.server.ThreadingHTTPServer((indirizzo, porta), SenzaCache).serve_forever()
