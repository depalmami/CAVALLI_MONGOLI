# MODALITÀ POPLAR — Doss Trento, venerdì 11 settembre

Set site-specific per la data al Poplar Festival. **Non è un livello**: è uno strato che si
appoggia sopra a tutti e sette, e si spegne con un interruttore se qualcosa non va.

## Accenderla

Nel banco di regia, riquadro rosso sotto i pulsanti dei livelli:

- **🌳 MODALITÀ POPLAR** — l'interruttore. Anche col **tasto 8** (1–7 restano i livelli).
- **🌙 Colori notte** — porta erba e asfalto verso la notte. Si può spegnere da solo, se si
  vuole lo sfondo notturno ma i livelli nei loro colori.
- **↻ Ricarica asset Poplar** — vedi sotto, non è opzionale.

## Uscita video

Bottone **"Dual Monitor classico (Full HD)"**. Il preset di render è già Full HD
(1920×1080) di default: non serve toccare altro. Niente layout a bande, niente testo
laterale — per questa data non ci sono i pannelli laterali.

## ⚠️ La cache: il problema che farà perdere tempo

**Se sostituisci un PNG in `images/poplar/` il browser continua a mostrare quello vecchio,
senza dare nessun errore.** Mi ha ingannato tre volte in una sera.

Dopo ogni sostituzione di asset premi **↻ Ricarica asset Poplar**: rilegge la cartella
scavalcando la cache. Se hai un dubbio, premilo comunque.

(Con `node server.js` il problema è attenuato — quel server manda già intestazioni no-cache
sulle immagini — ma il bottone resta la via sicura.)

## Cambiare la grafica

`images/poplar/` è la modalità. Ogni PNG con un nome noto entra in scena su **tutti** i
livelli; quelli che mancano lasciano passare l'asset del livello. Quindi si può aggiungere
o togliere roba fino all'ultimo senza toccare il codice.

Le misure **non sono libere**: il gioco disegna lo sprite dentro il rettangolo dell'atlas
(`common.js`, `SPRITES`). Un PNG con proporzioni diverse esce schiacciato.

| File | Misura | Cos'è ora |
|---|---|---|
| `BILLBOARD01/02/03/04/08` | varie | cartelloni Poplar (08 = **crediti foto, deve restare**) |
| `BILLBOARD05/06/07/09` | varie | i nostri, presi da `4-cantiere` |
| `PALM_TREE` | 215×540 | pioppo cipressino |
| `TREE1` / `TREE2` | 360×360 / 282×295 | latifoglie |
| `DEAD_TREE1` / `DEAD_TREE2` | 135×332 / 150×260 | lampioni (bracci speculari) |
| `sky.png` | 1280×480 | Trento di notte da Sardagna |
| `hills.png` | 1280×480 | trasparente: zittisce le colline del livello |
| `trees.png` | 1280×480 | filare all'orizzonte |

Rigenerare tutto: gli script in `tools/` (`gen-poplar-billboards.py` ha i testi in una
tabella in cima; `gen-poplar-backgrounds.py`, `-trees.py`, `-lampioni.py`). Servono i font
in `assets/fonts/poplar/`, che **non sono nel repo** — vanno riscaricati dal sito del
festival (vedi commento in cima allo script).

## Crediti — obbligo di licenza

Le foto sono Creative Commons **BY-SA** e il press kit del festival chiede il credito ai
fotografi. Il cartellone `BILLBOARD08` fa da schermata crediti dentro il gioco: **non
toglierlo senza rimpiazzarlo**. Elenco completo in `images/poplar/CREDITS.md`.

I font del festival sono commerciali (Dinamo, Grilli Type) e il loro uso qui va confermato
con `press@poplarfestival.it` o con Fat Fat (@fatfat.biz).

## Cosa manca ancora

Mausoleo di Cesare Battisti sullo slot `COLUMN`, veicoli a tema, flash di **foto** a tempo
(oggi il sistema lampeggia font, non immagini: va scritto), preset di frasi per la scritta
gigante, e i testi definitivi dei cartelloni.
