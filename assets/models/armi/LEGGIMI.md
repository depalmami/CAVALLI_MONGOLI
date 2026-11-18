# Armi in mano al protagonista

Il gioco cerca qui un file per arma. Se c'è lo usa, altrimenti mostra un segnaposto disegnato dal codice (`3d/armi.js`).

| File          | Arma                                  |
|---------------|---------------------------------------|
| `whip.glb`    | Frusta                                |
| `mace.glb`    | Mazza                                 |
| `saber.glb`   | Sciabola                              |
| `bow.glb`     | Arco                                  |
| `freccia.glb` | Freccia in volo (non è in mano: la usa `frecce` in `horse-racing-3d.html` via `caricaFreccia`/`vestiFreccia` in `3d/armi.js`; lunghezza su +Y, punta in su, origine a metà asta; nel gioco è lunga 1100 unità e la sezione è ingrossata di 1,3×) |
| `cassa.glb`   | Cassa-arma che si raccoglie in pista (non è in mano: la usano i pickup di `horse-racing-3d.html` via `caricaCassa`/`vestiCassa` in `3d/armi.js`) |

I pugni non hanno nulla in mano.

## Come va fatto il modello

- **Origine nell'impugnatura** (il punto dove la mano chiude), **lunghezza lungo +Y** con la punta verso l'alto.
- Arco: lunghezza lungo Y, **corda verso -Z** (verso il cavaliere), la pancia dei flettenti verso +Z (il bersaglio).
- Qualunque scala: il gioco porta il lato più lungo a 1,00 m (frusta), 0,60 (mazza), 0,85 (sciabola), 0,95 (arco). Il cavallo è alto 1,83 m.
- **Deve leggersi da dietro**, perché la camera di corsa sta alle spalle del cavallo: una lama sottilissima vista di taglio sparisce. Meglio una sezione piena o un piatto largo almeno qualche cm.
- Materiali PBR standard (colore, metallo, rugosità), texture incluse nel GLB, circa 5-10k triangoli.

## Modelli che arrivano da un generatore (Meshy, Tripo...)

Escono con ~2 milioni di triangoli (65 MB l'uno), sdraiati a caso e con l'origine nel centro: non vanno messi qui così.
`tools/armi/prepara-arma.py` (Blender in background) li decima a 15-25k triangoli, riduce le texture a 1024, li raddrizza e mette
l'origine nell'impugnatura. Due passi: `--scegli` (una foto con le due estremità A rossa e B blu, per dire qual è l'impugnatura)
e poi la conversione vera con `--grip A|B --lungo ... --frac ...`; le opzioni sono spiegate nell'intestazione dello script.
Le impostazioni usate il 18 nov 2026 (da `Download/`):

| Arma    | Entrata       | Comando (dopo `--`)                                                                       |
|---------|---------------|-------------------------------------------------------------------------------------------|
| sciabola| `saber.glb`   | `--grip A --lungo 0.85 --frac 0.24 --eje 0.46 --tris 20000 --gira 180`                    |
| mazza   | `mace.glb`    | `--grip B --lungo 0.60 --frac 0.27 --eje 0.40 --tris 25000`                               |
| frusta  | `whip2.glb`   | `--grip B --asse impugnatura --lungo 1.0 --frac 0.14 --tris 15000 --gira 180`             |

| arco    | `bow.glb`     | `--grip A --lungo 0.95 --frac 0.5 --tris 15000 --gira 90`                                 |

| freccia | `freccia.glb` | `--grip A --lungo 1.0 --frac 0.5 --tris 12000` (A = la coda con le penne, B = la punta: si decide con `--scegli`)         |
| cassa   | `cassa.glb`   | `--cassa --lungo 1 --tris 12000` (nessun riorientamento: centrata, lato maggiore = 1; il gioco la porta a 520 unità e la tinge col colore dell'arma) |

`--gira 180` mette il filo della sciabola e il ricciolo della frusta verso l'esterno (lato destro, -X). Per l'arco `--gira 90` porta la
corda verso il cavaliere (-Z) e i flettenti verso il bersaglio (+Z); da dietro, dritto, sarebbe una stecca, perciò in `POSE.bow` c'è
`vira: -0.7` che lo gira di ~40° su se stesso e fa vedere la curva.

## Tarare

`node tools/armi/scatta-armi.js <cartella> saber dietro,mano,lato 0,1:1,1:-1` scatta l'arma in mano da più viste e a diversi punti del colpo
(`c:dir`, dir = 1 destra, -1 sinistra). Serve il server di sviluppo (`python3 tools/server-sviluppo.py 8902`).
Il punto-mano è `ARMI.mano` e le pose sono `POSE` in `3d/armi.js`.
