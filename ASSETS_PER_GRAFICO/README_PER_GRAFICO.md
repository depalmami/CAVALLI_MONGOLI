# CAVALLI MONGOLI – THE GAME
## Guida agli Asset per il Grafico

> **Istruzioni generali:**
> Questa cartella contiene tutti gli asset grafici e audio del gioco.
> Il tuo compito è **sostituire i file placeholder** con le versioni definitive specifiche per ogni livello,
> mantenendo **esattamente lo stesso nome file** e le **stesse dimensioni in pixel**.
> Il gioco caricherà automaticamente i nuovi file senza modifiche al codice.

---

## Struttura delle cartelle

```
ASSETS_PER_GRAFICO/
├── 01_BACKGROUND/          → Sfondi a strati (sky, colline, alberi)
├── 02_CAVALLO_GIOCATORE/   → Sprite animati del cavallo del player
├── 03_AVVERSARI/           → Sprite dei cavalli avversari (8 frame animazione)
├── 04_ELEMENTI_PISTA/      → Cartelloni, vegetazione, ostacoli ai lati della pista
├── 05_UI/                  → Logo, titolo, icone interfaccia
├── 06_INTRO_ANIMAZIONE/    → 61 frame della sequenza di intro (loop)
├── 07_LIVELLI/             → Cartelle per gli asset specifici di ogni livello
└── 08_AUDIO/               → Tracce musicali
```

---

## 01_BACKGROUND — Sfondo della pista

Il background è composto da **3 layer sovrapposti** che scorrono a velocità diverse (parallax).
Dimensione obbligatoria per tutti: **1280 × 480 px**, PNG con trasparenza dove necessario.

### `layer_cielo/`
Il cielo. Scorre più lentamente. Può contenere nuvole, montagne lontane, sole, ecc.

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `sky.png` | 1280 × 480 px | Cielo generico (default) |
| `sky_1.png` … `sky_6.png` | 1280 × 480 px | Varianti cielo per livelli diversi |

### `layer_colline/`
Le colline/paesaggio in secondo piano.

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `hills.png` | 1280 × 480 px | Profilo colline (default) |

### `layer_alberi/`
La linea di alberi/vegetazione fiancheggiante la strada (orizzonte).

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `trees.png` | 1280 × 480 px | Linea alberi (default) |

> **Nota:** I 3 layer devono avere sfondo trasparente nelle zone vuote per sovrapporsi correttamente.
> Il file `background.svg` nella root di `01_BACKGROUND/` è la sorgente Illustrator/Inkscape di riferimento.

---

## 02_CAVALLO_GIOCATORE — Sprite del cavallo del giocatore

Il cavallo del giocatore è animato con **8 frame** per le posizioni di rettilineo e salita.
Le curve hanno 2 varianti (normale e in salita).

**Formato:** PNG con sfondo trasparente
**Canvas consigliato:** mantenere lo stesso canvas dei file originali

### `animazione_rettilineo/` — 8 frame
Sequenza ciclica dell'andatura in rettilineo. Frame numerati da 1 a 8.

| File | Dimensioni attuali | Note |
|------|-------------------|------|
| `PLAYER_STRAIGHT_1.png` … `PLAYER_STRAIGHT_8.png` | 384 × 1126 px | Il gioco scala automaticamente |

### `animazione_rettilineo_salita/` — 8 frame
Stessa andatura ma con postura del cavallo in salita (corpo più inclinato in avanti).

| File | Dimensioni attuali | Note |
|------|-------------------|------|
| `PLAYER_UPHILL_STRAIGHT_1.png` … `PLAYER_UPHILL_STRAIGHT_8.png` | 384 × 1126 px | Mantenere stesso canvas |

### `animazione_curva_destra/` — 2 varianti
Il cavallo che curva a destra (corpo inclinato, zampe adattate).

| File | Dimensioni | Note |
|------|-----------|------|
| `player_right.png` | 80 × 41 px | Sprite flat per curva destra |
| `player_uphill_right.png` | 80 × 45 px | Sprite flat per curva destra in salita |

### `animazione_curva_sinistra/` — 2 varianti

| File | Dimensioni | Note |
|------|-----------|------|
| `player_left.png` | 80 × 41 px | Sprite flat per curva sinistra |
| `player_uphill_left.png` | 80 × 45 px | Sprite flat per curva sinistra in salita |

---

## 03_AVVERSARI — Cavalli avversari

I cavalli avversari hanno **8 frame** di animazione, in versione destra (DX) e sinistra (SX).
Sono posizionati ai lati della pista come ostacoli/concorrenti.

**Formato:** PNG con sfondo trasparente
**Dimensioni attuali:** 384 × 1126 px (stessa base del cavallo giocatore)

### `cavalli_avversari_dx/` — versione destra (8 frame)

| File | Descrizione |
|------|-------------|
| `01_dx.png` … `08_dx.png` | Ciclo animazione cavallo che va verso destra |

### `cavalli_avversari_sx/` — versione sinistra (8 frame)

| File | Descrizione |
|------|-------------|
| `01_sx.png` … `08_sx.png` | Ciclo animazione cavallo che va verso sinistra (flip orizzontale del DX) |

---

## 04_ELEMENTI_PISTA — Elementi ai lati della pista

Tutti gli elementi ai bordi della pista. PNG con sfondo trasparente.
Il gioco li scala in base alla profondità prospettica, quindi la dimensione originale deve essere **grande** (mai sotto i 100 px di altezza).

### `billboard_cartelloni/` — 9 cartelloni pubblicitari

Cartelloni che appaiono ai lati della pista. Possono avere contenuti grafici specifici per ogni livello/canzone.

| File | Dimensioni | Note |
|------|-----------|------|
| `billboard01.png` | 300 × 170 px | Cartellone generico 1 |
| `billboard02.png` | 215 × 220 px | Cartellone generico 2 |
| `billboard03.png` | 230 × 220 px | Cartellone generico 3 |
| `billboard04.png` | 268 × 170 px | Cartellone generico 4 |
| `billboard05.png` | 298 × 190 px | Cartellone generico 5 |
| `billboard06.png` | 298 × 190 px | Cartellone generico 6 |
| `billboard07.png` | 298 × 190 px | Cartellone generico 7 |
| `billboard08.png` | 385 × 265 px | Cartellone grande 8 |
| `billboard09.png` | 328 × 282 px | Cartellone grande 9 |

> **Suggerimento:** I billboard sono il posto ideale per contenuti visivi specifici per ogni livello/canzone dei Cavalli Mongoli.

### `vegetazione/` — Alberi e piante

Elementi decorativi ai bordi pista. Mantenere le proporzioni.

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `tree1.png` | 360 × 360 px | Albero tipo 1 |
| `tree2.png` | 282 × 295 px | Albero tipo 2 |
| `dead_tree1.png` | 135 × 332 px | Albero secco tipo 1 |
| `dead_tree2.png` | 150 × 260 px | Albero secco tipo 2 |
| `palm_tree.png` | 215 × 540 px | Palma |
| `bush1.png` | 240 × 155 px | Cespuglio tipo 1 |
| `bush2.png` | 232 × 152 px | Cespuglio tipo 2 |
| `cactus.png` | 235 × 118 px | Cactus |
| `stump.png` | 195 × 140 px | Ceppo |

### `ostacoli/` — Ostacoli sulla pista

Elementi con cui il giocatore può scontrarsi.

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `boulder1.png` | 168 × 248 px | Masso tipo 1 |
| `boulder2.png` | 298 × 140 px | Masso tipo 2 |
| `boulder3.png` | 320 × 220 px | Masso tipo 3 |
| `column.png` | 200 × 315 px | Colonna |

---

## 05_UI — Interfaccia utente

### `logo_titolo/`

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `Cavalli mongoli.png` | 1289 × 202 px | Logo animato del titolo (con effetto flash) |
| `titolo_ref_1.jpeg` | — | Riferimento visivo logo (non usato in gioco) |
| `titolo_ref_2.jpeg` | — | Riferimento visivo logo alternativo |

### `icone/`

| File | Dimensioni | Descrizione |
|------|-----------|-------------|
| `mute.png` | — | Icona muto/volume |

---

## 06_INTRO_ANIMAZIONE — Sequenza di intro

61 frame PNG della sequenza animata mostrata all'avvio del gioco.
Vengono riprodotti in loop in sequenza: `loop iniziale0000.png` → `loop iniziale0060.png`

**Formato:** PNG (con eventuale trasparenza)
**Naming obbligatorio:** `loop iniziale0000.png` … `loop iniziale0060.png` (4 cifre, zero-padded)

---

## 07_LIVELLI — Asset specifici per livello

Ogni sottocartella corrisponde a una canzone/livello del gioco.
Qui vanno gli asset **sostitutivi** specifici per quel livello: sfondi tematici, billboard personalizzati, ecc.

```
07_LIVELLI/
├── 01-bulloncino/
├── 02-hanno-fallito/
├── 03-odore-del-buongiorno/
├── 04-cantiere/
├── 05-segreto-del-rap/
├── 06-come-tu-dici/
└── 07-diggiei/
```

**Per ogni livello**, popola la cartella con i file che vuoi sovrascrivere rispetto al default.
La struttura interna di ogni cartella livello deve **specchiare** quella delle cartelle globali:

```
07_LIVELLI/01-bulloncino/
├── background/
│   ├── sky.png           ← sfondo cielo specifico per questo livello
│   ├── hills.png         ← colline specifiche
│   └── trees.png         ← vegetazione orizzonte
├── billboard_cartelloni/
│   ├── billboard01.png   ← cartellone con contenuto della canzone
│   └── ...
└── (altri elementi opzionali)
```

> **Regola:** Se un file non è presente nella cartella del livello, il gioco usa il file default delle cartelle globali.

---

## 08_AUDIO — Musica

| File | Descrizione |
|------|-------------|
| `racer.mp3` | Traccia musicale principale (MP3) |
| `racer.ogg` | Stessa traccia in formato OGG (fallback browser) |

> **Nota:** Fornire sempre entrambi i formati. La traccia OGG è necessaria per Firefox.

---

## Regole generali

1. **Stesso nome file** — Non rinominare i file. Il codice li cerca per nome esatto.
2. **Stesso formato** — Usare PNG per le immagini (con trasparenza dove serve), JPG/JPEG solo dove già presente.
3. **Dimensioni** — Rispettare le dimensioni indicate. Per i background è **obbligatorio** (1280×480 px). Per gli sprite il gioco scala, ma partire da dimensioni simili all'originale.
4. **Sfondo trasparente** — Tutti gli sprite (cavalli, elementi pista, UI) devono avere sfondo **trasparente** (alpha channel), non bianco.
5. **Nessuna cartella `__MACOSX`** — Non includere metadata di sistema nella consegna.

---

## Flusso di lavoro consigliato

1. Apri il file corrente (placeholder) come riferimento per dimensioni e proporzioni
2. Crea il nuovo asset sulle stesse dimensioni
3. Salva con lo **stesso nome** nella stessa cartella
4. Testa nel gioco aprendo `horse-racing.html` nel browser

---

*Generato automaticamente — Cavalli Mongoli The Game, Febbraio 2026*
