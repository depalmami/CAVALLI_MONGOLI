# PIANO — Cavalli Mongoli 3D: «Apri tutto, smarmella!»

> Piano di ammodernamento di `horse-racing-3d.html`, il punto più avanti del progetto.
> Obiettivo: un gioco che **smarmella completamente a ritmo di musica**, con un **HUD nuovo**
> che si veda anche in proiezione. Piano scritto il 1 ottobre 2026 su `master` @ `12b764e`.
> Il PRD del combattimento (`PRD-road-redemption.md`) resta valido: questo piano ci si
> appoggia sopra, non lo sostituisce.

---

## 1. In una riga

**La musica diventa l'orologio del gioco.** Un solo modulo ascolta (MIDI da Ableton, ingresso
audio, tap), produce uno stato `musica` (battito, fase, battuta, cassa, bassi, sezione…), e
tutto il resto — post-processing, mondo, cavalli, camera, HUD, combattimento — lo legge
attraverso una **centralina** con una manopola sola: **SMARMELLA**, da 0 (il gioco di oggi,
identico) a 1 (delirio totale).

---

## 2. Da dove partiamo

### Cosa c'è già e funziona
- Three.js 0.160 (WebGL2), pipeline `RenderPass → UnrealBloom → OutputPass`, ACES, ombre che
  seguono il giocatore, cielo `Sky`, terreno heightfield, 12 tappe fino a Karakorum
  (52101 segmenti, ~48 km), combattimento completo, pilota automatico, gamepad, proiezione sul
  secondo schermo, console di regia con persistenza.
- **Show a tempo** (`party` + `live` + `text3d`): tap tempo T, alberi che rimbalzano, luce e
  bloom che pulsano, flash strobo, scritta 2D/3D con 8 palette.
- Nel 2D: un **livello audio unico** (microfono/file → shake/zoom) e il **cielo Hydra**
  (`vendor/hydra-synth.js`). Il 3D di audio non ha nulla.
- Sulla macchina: **Ableton Live 12 Suite**, **BlackHole 16ch** già installato, Apple M5 Pro.

### Cosa manca o è debole
| Problema | Perché conta |
|---|---|
| Il battito esiste solo se qualcuno **tappa**. Nessuna analisi audio, nessun MIDI. | Senza orecchie non c'è audioreattività: c'è un metronomo manuale. |
| Ogni effetto è cablato a mano (`party.update` tocca alberi, sole, bloom). | Ogni nuovo effetto = nuovo codice. Serve una matrice, non altri `if`. |
| **L'HUD del giocatore è DOM** (`#hud-left`, `#hud-combat`, `#hud-help`) e la proiezione ricompone solo le **tele** (`proiezione.tele()`). | **Il pubblico non vede mai** velocità, vita, nitro, tappa. Solo le barre dei rivali, se attivate. |
| HUD con emoji e font di sistema. | Il 2D ha già un HUD da cabinato (Press Start 2P, `ffe23bc`); il 3D è rimasto indietro. |
| Three.js e il font della scritta 3D arrivano **da CDN**. | In location la rete non è garantita: il 2D ha già vendorato Hydra e il font per questo. |
| `trees.pulse` ricalcola **tutte** le matrici (~12 mila alberi × 3 mesh) sulla CPU a ogni frame. | Oggi pulsa solo sul tap; con l'audio pulserebbe sempre. Va spostato sulla GPU. |
| Un file unico da 3362 righe. | Ci stanno per entrare 4 sistemi grossi: vanno in moduli loro. |

---

## 3. Principi (le regole che decidono tutto il resto)

1. **La musica è l'orologio.** Tutto ciò che cambia "a scatti" (tagli di camera, cambi scena,
   banner, colpi del pilota) si **quantizza** su battito / battuta / frase da 4-8 battute.
2. **Nessun effetto legge l'audio direttamente.** Si legge `musica` (lo stato) o la centralina.
   Così si cambia sorgente (MIDI, audio, tap) senza toccare un solo effetto.
3. **SMARMELLA = 0 è il gioco di oggi, pixel per pixel.** È la garanzia di non-regressione e il
   pulsante di panico in concerto.
4. **Prima la proiezione.** Ciò che conta per il pubblico deve stare in una tela che
   `proiezione.tele()` ricompone. Niente più HUD in DOM.
5. **Zero rete in location.** Tutto vendorato in `vendor/`, come già nel 2D.
6. **Nuovi sistemi = nuovi moduli.** Niente refactor big-bang del nucleo: i moduli nuovi
   (`3d/*.js`) ricevono quello che serve con un `init({...})` esplicito.
7. **Leggibile anche nel delirio.** I numeri dell'HUD non si deformano mai; si muovono cornici,
   accenti, colori. Il giocatore deve poter giocare a SMARMELLA 0.6.
8. **Strobo con un tetto.** Limitatore anti-fotosensibilità acceso di default (≤ 3 lampi
   pieni al secondo), disattivabile solo di proposito.

---

## 4. Architettura

```
 SORGENTI                    ORECCHIE  (3d/musica.js)          CENTRALINA (3d/centralina.js)     BERSAGLI
 Ableton MIDI clock  ──┐     clock: bpm, fase, battuta, frase ──┐  scena attiva (preset)       ──┐  post   (3d/smarmella.js)
 Ableton note / cue  ──┤     colpi: cassa, rullante, charl.     │  matrice sorgente → bersaglio  │  mondo  (terreno, strada,
 Ingresso audio      ──┼──▶  bande: sub, bassi, medi, alti   ──┼─▶ × quantità × curva × rilascio ├─▶        alberi, paletti, cielo)
  (BlackHole / scheda) │     energia, brillanza, spettro[64]    │  macro SMARMELLA 0…1           │  cavalli (galoppo a tempo)
 File audio (prove)  ──┤     sezione: pausa / salita / DROP     │  auto-regia per sezioni        │  camera (regista)
 Tap tempo           ──┘     eventi: on('cassa'|'battito'|…)  ──┘  limitatore strobo           ──┘  HUD (3d/hud.js), gameplay
```

### Lo stato `musica` (il contratto fra le orecchie e il resto)
```js
musica = {
  fonte: 'midi' | 'audio' | 'tap' | 'interno',
  bpm: 128, fase: 0.37,            // 0..1 dentro il battito corrente
  battito: 213, battuta: 53, faseBattuta: 0.59, frase: 6,   // frase = 8 battute
  cassa: 0.0, rullante: 0.0, charleston: 0.0,   // impulsi 1 → 0 con rilascio
  sub: 0.4, bassi: 0.7, medi: 0.3, alti: 0.5,   // inviluppi normalizzati 0..1 (AGC sull'analisi)
  energia: 0.62, brillanza: 0.48,
  spettro: Float32Array(64),       // anche come DataTexture per gli shader
  sezione: 'pausa' | 'salita' | 'groove' | 'drop', drop: 0.0,  // impulso al drop
  prossimoBattito: 12345.6,        // ms performance.now(), PREVISTO → effetti in anticipo
};
musica.on('battito' | 'battuta' | 'frase' | 'cassa' | 'rullante' | 'drop' | 'sezione', fn);
```
Il vecchio `party` diventa un **adattatore**: `party.onBeat` → `musica.on('battito')`. Così
flash, scritta, alberi e luce di oggi seguono la musica vera dal primo giorno, senza riscriverli.

### Una voce della matrice
```js
{ da: 'cassa', a: 'post.aberrazione', quanto: 0.8, curva: 'esp', rilascio: 0.12, min: 0, max: 1 }
```
Valore finale di un bersaglio = `base(scena) + Σ voci × SMARMELLA`, smussato, con tetti.

---

## 5. Le orecchie — sorgenti, analisi, tempo

### Sorgenti, dalla più affidabile
| Sorgente | Come | Dà | Note |
|---|---|---|---|
| **MIDI da Ableton** | Web MIDI su *IAC Driver* (stesso Mac) o *Rete MIDI* di macOS (due Mac). In Ableton: Sync attivo sull'uscita IAC. | Clock 24 ppqn, Start/Stop, **posizione nel brano**, e le **note vere** di cassa/rullante (una traccia MIDI che ascolta la batteria e esce su IAC). | Precisione al millisecondo, zero falsi positivi. Il battere (l'"uno") è esatto. |
| **Traccia cue "VISUAL" in Ableton** | Una traccia MIDI con note = comandi (scena, drop, banner, palette). | La regia scritta **dentro l'arrangement**, già sincronizzata col pezzo. | È così che si fanno gli show "a timecode". |
| **Ingresso audio** | `getUserMedia` su BlackHole (loopback dal master di Ableton) o sulla scheda (mandata dal mixer). | Bande, energia, spettro, attacchi, BPM stimato. | Va **sempre** chiesto con `echoCancellation`, `noiseSuppression`, `autoGainControl` a `false`, altrimenti Chrome "ripulisce" la musica e l'analisi muore. |
| **File audio** | `<audio>` → MediaElementSource. | Tutto come l'ingresso. | Per provare senza band e per i test automatici. |
| **Tap** | T, come oggi, + "tap sull'uno" per rimettere in fase la battuta. | BPM e fase. | Sempre disponibile come rete di sicurezza. |
| **Interno** | Orologio a 120 BPM. | Il minimo vitale. | Se tutto il resto cade, lo show continua. |

Catena di ripiego automatica: **MIDI → audio → tap → interno**, con l'indicatore in console.

### Analisi audio
- **Spettro per gli occhi** — `AnalyserNode` (fft 2048, smoothing 0) letto a ogni frame:
  64 bande logaritmiche → `musica.spettro` + una `DataTexture` 64×1 per gli shader.
- **Attacchi per il tempo** — `AudioWorklet` (`3d/orecchio-worklet.js`) su filtri dedicati
  (cassa < 120 Hz, rullante 1–4 kHz, charleston > 7 kHz): energia per blocco da 128 campioni
  (~2,7 ms), soglia adattiva (mediana dell'ultimo secondo × k), refrattario 100 ms. Gli eventi
  portano il **timestamp audio**, convertito in tempo di pagina con `getOutputTimestamp()`.
- **AGC sull'analisi, non sull'ingresso**: ogni banda si normalizza sul proprio massimo mobile
  (8 s, rilascio lento) → funziona uguale a volume da prove e a volume da concerto.
- **BPM dall'audio**: autocorrelazione dell'inviluppo degli attacchi su 6–8 s, intervallo
  70–180 con preferenza per 110–150; bottoni **×2 / ÷2** per gli errori d'ottava; la fase si
  aggancia con un PLL sugli attacchi di cassa. Il battere dall'audio è ambiguo → "tap sull'uno".
- **Sezioni** (`pausa / salita / groove / drop`): energia su 2 battute contro 16; cassa assente
  da ≥ 4 battute = pausa; brillanza ed energia in crescita = salita; ritorno della cassa con
  salto d'energia dopo una pausa = **DROP**. Con la traccia cue di Ableton la sezione è esplicita.

### Latenza (si calibra, non si indovina)
L'audio analizzato arriva tardi di 20–60 ms; il ledwall aggiunge 1–3 frame; il suono in sala
viaggia a 343 m/s. Gli effetti agganciati alla griglia usano `prossimoBattito` (sono **previsti**,
quindi possono partire in anticipo) più uno **slider "anticipo visivo" in ms**. Procedura al
soundcheck: click in cassa, si muove lo slider finché lampo e click coincidono, si salva.

---

## 6. Cosa smarmella — il catalogo

Ordinato per resa / costo. Ogni voce è un **bersaglio** della centralina, quindi si accende,
si dosa e si combina dalla regia.

### 6.1 Post-processing — il grosso dell'effetto, quasi gratis
Pipeline nuova: `RenderPass → Bloom (forza/soglia modulate) → OutputPass (esposizione modulata)
→ **SMARMELLA** (un unico shader "uber", in LDR) con **feedback** (ping-pong del frame
precedente)`. Un solo passaggio a tutto schermo: su M5 Pro a 1080p costa pochissimo.

| Effetto | Agganciato di solito a | Note |
|---|---|---|
| **Feedback / scie** — il frame precedente rimescolato, zoomato, ruotato, sporcato di rumore, con hue che slitta | energia, sezione | **È lui lo "smarmellamento"**: l'immagine che cola e si fonde. |
| **Sovraesposizione** — bianco bruciato alla Boris | rullante, drop | In HDR prima del tone mapping: brucia come una luce vera. |
| Aberrazione cromatica / RGB split | cassa | |
| Zoom radiale / linee di velocità | bassi, boost | |
| Pugno a barile (fisheye) | cassa | Pochi gradi: dà il "colpo" senza nausea. |
| Caleidoscopio / specchio | drop, frase | Livelli alti soltanto. |
| Glitch a blocchi, slice orizzontali | rullante, fill | |
| Viraggio colore per scena (le 8 palette dello show come LUT) | battuta, scena | |
| Posterizza / pixel / scanline CRT | scena "Arcade" | Sul ledwall 768×512 rende benissimo. |
| Grana | charleston | |

**Livelli di SMARMELLA** (preset della macro, tutto dosabile):
`0 Diretta` (oggi) · `1 Groove` (luce e FOV a tempo, galoppo a tempo) · `2 Festa` (mondo che
balla, HUD che pulsa) · `3 Rave` (scie, aberrazioni, laser) · `4 APRI TUTTO` (feedback pieno,
caleidoscopio, bianco bruciato sul drop).

Attenzione tecnica: lo shader finale scrive già in sRGB (dopo `OutputPass`): non deve
includere `colorspace_fragment`, o la conversione si applica due volte.

### 6.2 Il mondo balla (shader di vertice, `onBeforeCompile` sui materiali esistenti)
- **Linee del battito sull'asfalto**: bande luminose disegnate dallo shader della strada a
  distanza `velocità × tempo al battito k` davanti al cavallo → **ci passa sopra esattamente
  sul battito**, come in Audiosurf/Thumper. La strada ha già la coordinata lungo-pista nelle UV
  (`D = i*SEG`), quindi basta un uniform. Costo: zero geometria.
- **Equalizzatore sulle righe di bordo**: lo spettro (DataTexture) dipinto sulle linee laterali.
- **Il terreno respira**: onde che partono dal cavallo a ogni cassa, ampiezza dai bassi.
  Maschera sulla **distanza dal corridoio stradale globale** (attributo per vertice calcolato
  una volta da `roadDist`): **spostamento zero** nella fascia calpestabile (±4800) e mai sopra
  `quota strada − VERGE_DROP`. Vedi §11.
- **Foresta equalizzatore**: ogni albero prende una banda dello spettro (attributo d'istanza) e
  scala nello shader. Sostituisce `trees.pulse` su CPU (~36 mila matrici a frame).
- **Paletti a LED**: i ~26 mila paletti rosso/bianco diventano luci che "corrono" lungo la pista
  a sedicesimi, colore della palette; emissive → il bloom li accende.
- **Portali delle tappe**: bandiere di preghiera che si accendono sul battere; arrivo di tappa
  = esplosione di luce sull'"uno" della battuta successiva.
- **Laser**: piani additivi dall'orizzonte che spazzano sui charleston (seguono la camera,
  come il cielo — §11).
- **Cielo e nebbia per sezione**: in pausa il sole scende (crepuscolo), sul drop torna su a
  scatto; colore e densità della nebbia sull'energia. Scena "notte": stelle + **cielo Hydra**
  portato dal 2D come texture della cupola, con i valori di `musica` passati a Hydra.
- **Polvere a tempo**: sbuffi sotto gli zoccoli sulle casse, coriandoli/petali sul drop.

### 6.3 I cavalli
- **Galoppo a tempo** — il dettaglio che fa sembrare tutto coreografato. Numeri: a velocità
  piena il passo naturale è 12000 / 5200 = **2,3 falcate al secondo ≈ 138 BPM**. Agganciare una
  falcata a un battito costa quindi pochissimo pattinamento in tutta la fascia 110–160 BPM
  (fuori fascia: una falcata ogni due battiti, o due per battito). Il `timeScale` del galoppo
  si corregge di poco perché lo zoccolo anteriore tocchi terra sul battito.
- Squash & stretch del cavaliere sulla cassa; criniera/coda più ampie in salita.
- **Pilota automatico a tempo**: nello show attacca **sui battiti** → ogni colpo cade sulla
  cassa. Takedown preferibilmente sul drop.

### 6.4 La camera — un regista automatico
- **Tagli quantizzati**: cambio camera (chase / onboard / tv / orbit) ogni 4 o 8 battute,
  mai a metà battuta.
- Cassa = pugno di FOV (+2–4°); rullante = micro-scossa; salita = dolly zoom progressivo
  (effetto vertigo) + scossa crescente; **drop** = rollio a frusta + 0,4 s di slow-motion e poi
  scatto di velocità; pausa = orbita lenta cinematografica.
- Si applica **dopo** `updateCamera` e non insegue il modello animato (lezione §9.3 del PRD).

### 6.5 Testo
La scritta dello show diventa **tipografia cinetica**: una parola per battito, slam 3D sull'uno,
frasi preimpostate per pezzo (era già nella lista "da fare" del Poplar).

---

## 7. L'HUD nuovo

### Requisiti
- **Una tela sola** `hud-overlay` in `teleVista` e **sempre** in `proiezione.tele()`.
  I tre pannelli DOM spariscono; l'aiuto tasti va nella console, non sul gioco.
- Disegnata alla risoluzione logica `vista`: deve funzionare a **1920×1080**, **1152×768** e
  **768×512** (sul ledwall il font a pixel va a multipli interi: 8/16/24/32 px).
- Glifi ed elementi **pre-renderizzati in cache**, niente `shadowBlur` per frame (era il collo
  di bottiglia del testo laterale nel 2D). Budget: < 1 ms a frame.
- **Tre modalità**: `GIOCO` (tutto), `SHOW` (solo il musicale e lo spettacolare: battuta,
  sezione, combo, banner, tappa) e `PULITO` (niente). Durante il live col pilota, `SHOW`.
- Reagisce alla musica con misura: cornici, accenti e colori si muovono, **i numeri no**.

### I pezzi
1. **Tachimetro ad arco** a segmenti, km/h in font a pixel, BPM piccolo sotto; i segmenti
   pulsano sulla cassa.
2. **Vita e nitro come VU-meter** a LED; nitro pieno = la barra respira a tempo ("pronto").
3. **Metronomo di battuta**: 4 tacche + anello di fase; giudizio sui colpi a tempo
   (PERFETTO / BUONO / FUORI — §8).
4. **Combo ×N** con moltiplicatore: cresce, trema, si rompe in glitch quando la perdi.
5. **Striscia del viaggio**: 12 tappe come tacche fino a Karakorum, il cavallo che avanza,
   nome della tappa in carattere condensato.
6. **Rivali**: etichette ridisegnate + **frecce a bordo schermo** per chi arriva da dietro.
7. **Banner** a tutta larghezza: TAPPA · TAKEDOWN · DROP · KO, tipografia cinetica a fette.
8. **Spettro** sottile sul bordo basso: decorazione e dichiarazione ("qui comanda la musica").
9. In `SHOW`: etichetta di sezione (PAUSA / SALITA / DROP) e **smarmellometro**.

### Tre direzioni di stile (prima i mockup, poi il codice)
| | Carattere | Pro | Contro |
|---|---|---|---|
| **A · Cabinato** | Press Start 2P, ombra a scalino, colori pieni — come l'HUD del 2D | Coerente col 2D, perfetto sul ledwall | Il meno sorprendente |
| **B · Khan Rave** | Wipeout/Designers Republic × ornamento mongolo: condensato pesante, linee tecniche sottili, angoli con motivi tradizionali (nodo *ulzii*, meandro), palette dello show | Il più "fico", identitario, nessuno ce l'ha | Più lavoro di disegno |
| **C · Steppa synthwave** | Cromature, neon, griglie, tramonto | Effetto immediato | Cliché |

**Consiglio: B con i numeri in font a pixel** (ibrido A+B): identità forte, nitidezza sul
ledwall, continuità col 2D. Il condensato va scelto fra font **OFL** vendorabili (Anton, Big
Shoulders Display, Oswald…), **non** i font commerciali del Poplar.

---

## 8. Gameplay a ritmo

L'audioreattività non deve restare solo da guardare: chi gioca deve **sentirla nelle mani**.
- **Colpo a tempo**: attacco entro ±70 ms dal battito = PERFETTO (danno ×2, nitro bonus);
  entro ±140 ms = BUONO; fuori = colpo normale. **Mai penalizzante**: chi non sente il tempo
  gioca come oggi.
- **Combo** di azioni a tempo → moltiplicatore di punti.
- **Nitro del drop**: se hai il nitro pieno quando arriva il drop, il boost raddoppia →
  "aspetta il drop".
- **Rivali che seguono il pezzo**: in pausa si tengono a distanza, in salita stringono,
  sul drop attaccano tutti insieme.
- **Casse-arma sulla griglia**: piazzate a `velocità × tempo al battito k`, le prendi sul battito.
- **Modalità canzone** (ambiziosa, con MIDI): una tappa dura un pezzo; il pilota modula la
  velocità per **arrivare al portale sull'ultimo colpo del brano**.

---

## 9. La regia

- **Console riorganizzata** in sezioni: *Audio* (sorgente, meter per banda, BPM, anello di
  fase, anticipo visivo), *SMARMELLA* (fader grande, livelli, auto-regia), *Scene* (griglia di
  pad), *Matrice* (le voci, modificabili), *HUD* (modalità e stile), *Proiezione* e *Show*
  (quelle di oggi).
- **Scene** = preset (base + voci della matrice + palette + stile di regia + modalità HUD),
  con dissolvenza **quantizzata alla battuta**. Tasti 1–9 e pad MIDI.
- **MIDI learn** su qualunque controllo (clic destro → muovi una manopola). Va bene qualunque
  controller, anche Push in modalità utente.
- **Auto-regia**: senza nessuno alla console, la sezione rilevata guida SMARMELLA
  (pausa → 1, salita → rampa 2→3, drop → 4 per 8–16 battute, poi rientro).
- **Setlist**: un preset per pezzo; Ableton manda un Program Change all'inizio di ogni brano.
- Persistenza: il modulo `preferenze` esteso + **esporta/importa JSON** (backup sulla chiavetta).

---

## 10. Roadmap

Ogni fase si chiude con un commit funzionante e un criterio verificabile. Taglia indicativa
in sessioni di lavoro (S ≈ 1, M ≈ 2–3, L ≈ 4+).

| Fase | Cosa | Fatto quando | Taglia |
|---|---|---|---|
| **0 · Fondamenta** | Branch `audioreattivo` da `master`. Three 0.160 + addons + font helvetiker **in `vendor/`**, importmap locale. Cartella `3d/` per i moduli nuovi. Contatore fps/ms in console. `cm3d.musica` per i test. | Con il **Wi-Fi spento** la pagina parte identica a oggi. | S |
| **1 · Le orecchie** | `musica.js` + worklet: sorgenti (file, ingresso, MIDI, tap, interno), bande, attacchi, BPM, fase, sezioni, anticipo visivo, meter in console. `party` diventa adattatore. | Click a 128 BPM: errore mediano < 15 ms, nessun falso. Un vostro pezzo: la cassa "si vede" giusta. MIDI da Ableton: 5 minuti senza deriva. Alberi/flash/scritta di oggi seguono la musica. | M |
| **2 · Smarmella v1** | `smarmella.js`: shader uber + feedback, fader, 5 livelli, limitatore strobo, prima matrice (in codice). | SMARMELLA 0 = screenshot identico a `master`. 4 = delirio. ≥ 60 fps a 1080p con margine (> 200 fps senza vsync). Limitatore misurato ≤ 3 lampi/s. | M |
| **3 · HUD** | Mockup delle 3 direzioni su screenshot veri alle 3 risoluzioni → scelta → `hud.js` (tela unica, modalità, cache), via i pannelli DOM. | L'HUD **si vede in proiezione** ed è leggibile a 768×512. < 1 ms/frame. | M |
| **4 · Il mondo balla** | Galoppo a tempo, linee del battito, equalizzatore sulle righe, foresta su GPU, paletti LED, terreno che respira, laser, cielo/nebbia per sezione, polvere, regista automatico. | Fascia calpestabile **misurata** ferma su tutto il tracciato (punti campione inizio/salita/culmine/fondo). Screenshot in 4 punti. fps invariati. | L |
| **5 · La centralina** | UI della matrice, scene quantizzate, MIDI learn, traccia cue di Ableton, setlist, auto-regia, export/import. | Uno show intero guidato da Ableton senza toccare la console. | M |
| **6 · Gameplay a ritmo** | Colpo a tempo, combo, rivali per sezione, casse sulla griglia, nitro del drop, pilota a tempo, (modalità canzone). | **Playtest vero** dell'utente con musica (lezione del PRD: le transizioni non bastano). | M |
| **7 · Pronti per il palco** | Scala di qualità automatica se gli fps calano, catena di ripiego delle sorgenti, **PANICO** (SMARMELLA 0 + strobo off in un tasto), registratore di clip dalla proiezione (per i social), checklist da soundcheck. | Prova generale di 45 minuti senza intoppi, staccando apposta MIDI e audio a metà. | S |
| **8 · Oltre** (opzionale) | WebGPU + TSL e particelle a milioni; dispositivo Max for Live con inviluppi **per traccia** via WebSocket (`node.script`); Ableton Link fra più macchine; Hydra sulle superfici del mondo. | — | L |

**Ordine consigliato**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. I mockup dell'HUD (inizio Fase 3)
si possono fare in parallelo alla Fase 1, perché non dipendono dal codice. Se c'è una data
vicina, il minimo da palco è **0 + 1 + 2 + PANICO**: già da solo cambia lo show.

---

## 11. Rischi e trappole già note

Dalle lezioni pagate su questo progetto (memoria + PRD), da rispettare in ogni fase:
- **Terreno**: mai spostare la fascia calpestabile (±4800) né salire sopra
  `quota strada − 300`; la maschera usa la distanza dal corridoio **globale**, perché un vertice
  lontano dal ramo A può essere vicino al ramo B.
- **Elementi "all'infinito"** (laser, stelle, cupola Hydra) seguono la camera come il cielo,
  o per l'80% del tracciato spariscono.
- **Segni**: rollio della camera sul drop e qualsiasi effetto laterale si verificano proiettando
  in spazio schermo, non confrontando due grandezze calcolate nella stessa convenzione.
- **Salti di `lat`/`playerX` letti come velocità**: un "salto sulla cassa" si fa sulla
  grafica (offset del modello), mai sulla posizione fisica.
- **Effetti additivi sul cielo chiaro non si vedono**: fusione normale con anima > 1.
- **Proiezione**: ogni tela nuova va aggiunta a `tele()`; la tela WebGL si copia subito dopo il render.
- **Analisi di una band dal vivo**: chitarre e voce sporcano la cassa → la via robusta è il MIDI
  da Ableton; l'audio serve per bande, energia e colore.
- **Permessi** (microfono, MIDI): su `127.0.0.1` si concedono una volta e restano; vanno
  provati sulla macchina del live **prima** del soundcheck.
- **Strobo**: limitatore di default + avviso in sala.
- **Aggiornare Three.js** è un passo a parte (dalla r163 `TextGeometry` usa `depth` e non
  `height`): ora si vendora la 0.160 così com'è.

---

## 12. Come si verifica (headless, come sempre)

- Chrome con `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream
  --use-file-for-fake-audio-capture=<file.wav>`: `getUserMedia` riceve il WAV → si prova la
  **vera** catena d'ingresso, non una scorciatoia.
- Tracce di prova generate (Python/Node): click a 128 BPM, cassa sola, un pezzo sintetico con
  pausa → salita → drop annotati; più un pezzo vero dei Cavalli Mongoli.
- **Metriche**: errore sul battito (ms), falsi positivi al minuto, secondi per agganciare il BPM,
  sezioni rilevate contro quelle annotate.
- MIDI: la logica del clock si prova iniettando messaggi finti; la prova vera con Ableton e IAC
  è manuale.
- Immagini: **screenshot in punti sparsi del tracciato** (non solo la partenza), confronto
  pixel a SMARMELLA 0 contro `master`, fps senza vsync coi flag già noti.
- E soprattutto: **guardarlo con la musica**, per secondi veri. Uno stato che cambia non
  dimostra che sia bello.

---

## 13. Decisioni aperte (servono dall'utente)

1. **Dal vivo suonate con Ableton** (clip/arrangement) o è tutto suonato? Decide se il cuore è
   il MIDI (preciso) o l'analisi audio.
2. **Il gioco gira sullo stesso Mac di Ableton?** Sì → IAC + BlackHole, zero cavi. No → Rete
   MIDI di macOS + mandata audio dal mixer alla scheda.
3. **Chi guida durante il live**: pilota automatico + regia, o qualcuno gioca davvero? Sposta
   il peso fra Fase 4-5 (spettacolo) e Fase 6 (gameplay).
4. **Stile dell'HUD**: A, B o C — dopo i mockup.
5. **Prossima data**: decide cosa deve essere pronto per quella sera.

---

## 14. Diario

### 1 ottobre 2026 — Fase 0 e Fase 1 fatte (branch `audioreattivo`)
**Fase 0.** Three.js 0.160 vendorato in `vendor/three/` (solo i 16 addon usati + le loro
dipendenze, 1,5 MB) e il font della scritta 3D: con la rete esterna **bloccata** la pagina
parte con zero richieste fuori da 127.0.0.1. Da `file://` ora compare subito l'istruzione per
il server (prima, con i moduli locali, sarebbe rimasta su «Caricamento…»). Contatore
fps · ms/frame in testata. I tasti non vanno più al gioco mentre si scrive nei campi di testo.

**Fase 1.** `3d/musica.js` (orologio unico + sorgenti + analisi), `3d/orecchio.worklet.js`
(colpi nel thread audio), `3d/pannello-musica.js` (card «Musica» in console). `party` è
diventato l'adattatore: flash, scritta e alberi seguono già la musica vera; il rimbalzo della
scritta usa la **fase vera** del battito. Tasto **U** = «è l'uno». In più del piano: evento
`basso` (colpo grave fuori griglia), e il drop **insegna l'uno** se nessuno l'ha segnato.

Misure (banco `tools/orecchie/`, confermate nel browser vero):
| | click 128 | pezzo 126 (groove → pausa → salita → drop) |
|---|---|---|
| BPM agganciato in | 4,1 s | 4,1 s |
| orologio − battito vero | +8,0 ± 0,4 ms | +5,6 ± 4,2 ms, nessuno oltre 60 ms |
| casse giuste / false | 64 / 0 | 119 / 6 |
| drop | — | 53,85 s (vero 53,83) |
| pausa / salita | — | +1,9 s / +2,4 s di ritardo |
| MIDI clock simulato (jitter ±1,5 ms) | 127,99–128,05 BPM, «uno» dallo Start | |

Lezioni pagate (sono anche nei commenti del codice):
- **Il basso in levare passa per cassa** se si guarda solo l'energia sotto 100 Hz: a tempo
  agganciato, un colpo grave a più di ¼ di battito dalla griglia è `basso`.
- **La rullata della salita passava per cassa** dopo una pausa lunga (soglia ormai bassa) e
  faceva scattare un drop finto: la cassa ora deve **dominare** sui medi, filtro di 4° ordine.
- **Nella pausa la fase scivola sul levare** (restano solo i charleston): la fase si corregge
  solo se ci sono casse **negli ultimi 2 s**; altrimenti l'orologio tira dritto come un volano
  (23 s di pausa: 9 ms di deriva).
- **Il microfono finto di Chrome headless** (`--use-file-for-fake-audio-capture`) su questo
  Mac restituisce **zeri**, anche su una pagina vuota: per i test dell'ingresso si sostituisce
  `getUserMedia` con lo stream di un `<audio>` (`captureStream`). Il banco Node resta il test
  principale: stesso codice, tempo simulato, pochi secondi.

**Da provare a mano** (non si può da headless): bus IAC con Ableton (Sync attivo) e
BlackHole come ingresso vero; calibrare l'anticipo visivo con un click in sala.

### 2 ottobre 2026 — Fase 2 fatta: SMARMELLA
`3d/smarmella.js` (passaggio di post) e `3d/centralina.js` (manopola, livelli, auto-regia,
limitatore); card «🌀 Smarmella» in console, tasti **0–4**.
- **Due mezzi passaggi** dopo l'OutputPass: STATO (barile, caleidoscopio, glitch, aberrazione,
  zoom radiale + FEEDBACK del frame prima) e FINITURA (bruciato, viraggio, saturazione,
  **tinta** con la palette dello show, posterizza, pixel, scanline, grana, vignetta, lampo).
  La finitura sta fuori dal giro di feedback, se no vignetta e viraggio si sommano all'infinito.
- **Cinque livelli** (Diretta · Groove · Festa · Rave · APRI TUTTO) mescolati dalla manopola.
  Sorgenti in più: `giro` (0→1 su 8 battute), `onda`, `dopoDrop` (2 battute piene + 2 di
  sfumatura), `frase1` (prima battuta di ogni frase), `scoppio` (lampo secco del drop).
- **Auto-regia**: pausa → 25 %, salita → rampa 50→75 %, drop → 100 % di colpo per 8 battute,
  poi 75 %. Sul pezzo di prova segue la struttura senza nessuno alla console.
- **Luce = di serie × party × centralina**: prima il party sovrascriveva sole/bloom/esposizione.
- **Limitatore** (acceso di default): ≤ 3 lampi al secondo contando insieme strobo, colpo di
  luce del party, flash e bruciato; lampi entro 60 ms = uno solo. Un lampo negato scende al 10 %.
- La scritta 3D non diventa più una barra bianca: il suo bagliore cala quando il bloom è aperto.

Misure: SMARMELLA 0 = nessun valore diverso dal gioco di prima e passaggio spento (test
`centralina`); 1080p senza vsync **317 fps a 0, 269 fps ad APRI TUTTO** (~0,5 ms/frame);
limitatore: con rullante a 7,5 colpi/s e strobo a 3/s, massimo 3 lampi in ogni secondo.

Lezioni:
- **Il "più chiaro" canale per canale sbianca tutto**: fra copie virate di colore il massimo
  per canale tende al grigio-bianco. Le scie scelgono per LUMINANZA.
- **Un caleidoscopio a metà è solo sporco**: va pieno (dopo il drop, inizio frase) o niente.
- **Il lampo del drop agganciato all'impulso `drop` (0,6 s) era mezzo secondo di bianco**:
  serve un impulso secco (`drop⁴`).

### 3 ottobre 2026 — Fase 3 fatta: HUD Cabinato
Bozze delle tre direzioni pubblicate come pagina (https://claude.ai/artifact/PbsMzmPtQB9CFjmGuW1Hzu);
scelta dell'utente: **A · Cabinato**. Implementato in `3d/hud.js`.
- **Una tela sola, anche in proiezione**: via i tre pannelli DOM (velocità/tappa, vita/nitro/
  statistiche, aiuto tasti), che al secondo schermo non arrivavano mai. L'aiuto tasti è in Regia.
- Selettore **HUD: Gioco / Show / Pulito** (tasto **V**) al posto della spunta «Includi l'HUD»:
  vale per anteprima e proiezione insieme; i popup dei colpi seguono il modo Gioco.
- Pezzi: viaggio (12 tappe, km, obiettivo dell'evento), velocità + BPM, vita/nitro a blocchi,
  arma e bottino, **combo** (colpi entro 2,5 s; si rompe se ti colpiscono), rivali con vita a
  blocchi e frecce per chi arriva da dietro, **metronomo** (l'uno rosso) col **giudizio sui
  colpi** (PERFETTO ≤ 70 ms, BUONO ≤ 140 ms, il bonus arriva in Fase 6), spettro a blocchi,
  banner su tappa · takedown · drop · vittoria · KO. In Show: sezione + smarmellometro.
- Nuova risoluzione di render **768×512 (ledwall, pixel 1:1)**, come nel 2D.
- Costo: **0,03–0,05 ms per frame** a 1080p (ogni scritta con contorno e ombra si disegna una
  volta e poi si copia). Font a pixel solo a multipli di 8: a 768×512 cade a 8 px, la sua misura nativa.

Lezioni:
- **Il font vendorato è solo latino di base** (4,7 KB): niente accenti, «·», «×», emoji. Ogni
  testo passa da `ascii()`, compresi l'obiettivo dell'evento e i nomi delle tappe.
- **La cache delle scritte va svuotata quando arriva il font**: una scritta pre-disegnata prima
  resterebbe in monospace per sempre, senza errori.
- **Catturare la tela WebGL fuori dal frame dà bianco** (niente `preserveDrawingBuffer`): per
  i test la composizione si fa dentro il render, come fa la proiezione vera.

### 3 ottobre 2026 — Fase 4 fatta: il mondo balla
`3d/mondo.js`: codice agganciato agli shader dei materiali che c'erano già (onBeforeCompile),
uniform condivise, nessuna geometria nuova tranne i laser. Bersagli nuovi nella centralina
(`mondo.*`, `cavalli.tempo`, `camera.regista/scossa/rollio`), tutti a 0 a SMARMELLA 0.
- **Galoppo a tempo** (da Groove in su): sprite → il fotogramma lo decide il battito (scarto
  misurato: 0 fotogrammi su 25 campioni); modello 3D → aggancio di fase sulla falcata (5–15 ms;
  i fermo-immagine dei takedown lo sganciano per ~0,3 s). Falcate per battito = potenza di 2
  più vicina al passo naturale.
- **Linee del battito** sull'asfalto a distanza velocità × tempo al battito: arrivano al cavallo
  sul battito. **Equalizzatore** sui cigli: una barra ogni 500 unità, una banda per barra.
- **Foresta equalizzatore su GPU**: ogni albero ascolta una banda; il rimbalzo del party è un
  uniform. Le ~36 mila matrici a frame sulla CPU non ci sono più (e l'ombra cresce con l'albero).
- **Paletti a LED**: uno su otto acceso, la fila corre verso il cavallo a sedicesimi; lampo sulla cassa.
- **Terreno che respira**: un anello per battito che parte dal cavallo, solo oltre 8000 unità
  dal corridoio stradale (l'albero più lontano sta a ~7150; la scarpata non ha l'attributo e resta ferma).
- **Laser** (Rave, APRI TUTTO): fusione normale con colore > 1, non additiva.
- **Notte** (0…1): il sole scende fino a −4°, nebbia blu, luce ambiente giù; nelle pause più
  buio, sul drop di APRI TUTTO un lampo di giorno.
- **Polvere** sulla cassa, **scossa** sul rullante, **rollio** sul drop (alterno), **fermo-immagine**
  di 0,2 s sul drop dal 70 % in su.
- **Regista**: da Rave in su taglia la camera a fine frase (8 battute; 4 ad APRI TUTTO); spento
  torna alla camera scelta con C.

Misure: 1080p senza vsync 303 fps a 0, 273 ad APRI TUTTO (prima 317/269: invariato); riposo a 0
verificato su tutti i bersagli nuovi.

Rimandato: bandiere dei portali sul battere, normali del terreno che si muove (oggi l'onda si
vede dalla sagoma, non dall'ombreggiatura), verifica a occhio della notte piena.

### 3 ottobre 2026 — Grafica: alberi nuovi
L'utente rimanda **controller MIDI e integrazione con Ableton Live alla fine del progetto** e
chiede di concentrarsi sugli elementi grafici. Primo pezzo: gli alberi (`3d/alberi.js`).
- **Specie della Mongolia generate via codice**, 3 varianti ciascuna: larice siberiano a palchi
  (anche **dorato** d'autunno, coi colori nei vertici), betulla bianca segnata di nero, pino
  silvestre col fusto arancio in cima, cespuglio. Chiome con normali dal centro del ciuffo
  (luce morbida), colori nei vertici (scuro dentro e in basso), luce di bordo, **vento**.
- **Un bioma per tappa**: steppa rada a boschetti (Kherlen, Tuul, Khustai, Khar Balgas,
  Karakorum), foresta fitta e profonda fino a 14 larghezze di strada (Burkhan Khaldun, Khangai
  con i larici d'oro), misto lungo i fiumi (Onon, Orkhon), cespugli radi nelle dune.
- **41.812 alberi a blocchi** (1000 segmenti × specie × variante, 389 InstancedMesh con la
  propria sfera d'ingombro): si disegnano solo quelli in vista. Gli alberi oltre 8000 dal
  corridoio cavalcano le onde del terreno (stessa formula nello shader).
- Equalizzatore e rimbalzo del party restano agganciati; l'ombra segue vento e musica.

Misure: 1080p senza vsync 285 fps a 0, 251 ad APRI TUTTO (prima 303/273 con 12 mila alberi a 3
primitive); CPU per frame 2,1 ms.

Lezione: **tingere per istanza un verde col giallo dà oliva, non oro** — le varianti di colore
vere stanno nei vertici della geometria; il colore per istanza serve solo a variare la luce.

Visto e da fare: **le dune di Elsen Tasarkhai sono colline verdi** — serve il terreno per bioma.

### 5 ottobre 2026 — Proiezione a schermo intero, una camera sola
- **Clic per lo schermo intero** nella finestra di proiezione, portato dal 2D (velo «clicca»,
  «resta in finestra», misura viva, F). Il bottone «Pieno» dalla console poteva essere rifiutato
  perché il gesto è dell'altra finestra.
- **Una camera sola**, quella che segue il cavallo (richiesta dell'utente): via onboard, tv,
  orbita, il tasto C, il bottone in Resa e il **regista automatico** della Fase 4 (bersaglio
  `camera.regista` tolto dalla centralina). Restano pugno di FOV, scossa e rollio sul drop.
  Le camere tolte si recuperano da git (`9d00bfe`).

### 5 ottobre 2026 — Grafica: terreno per bioma, luce del cielo
L'utente chiede di «riprendere la migrazione verso WebGL per grafica mozzafiato». Il gioco è già
WebGL; WebGPU sarebbe un rifacimento del motore di resa, sconsigliato a un mese dalla data.
Si prosegue il piano grafico in WebGL.
- **Suolo per bioma**: ogni cella del terreno sa qual è il segmento di strada più vicino (il
  timbro porta l'indice, la distanza chamfer lo propaga) → tappa → pesi di erba verde, steppa
  secca, sabbia, roccia (`SUOLO_TAPPE`, raccordati per 600 segmenti sui confini). Roccia anche
  dove la pendenza supera ~35 %. Lo shader disegna paglia, sabbia con le increspature del vento
  e roccia venata senza texture nuove. Anche la scarpata ha l'attributo (senza, vale (0,0,0,1):
  tutta roccia).
- **Dune vere** a Elsen Tasarkhai: creste affilate (1 − |sen|) al posto delle colline, solo
  lontano dalla strada; il taglio finale tiene l'invariante «mai sopra la sede stradale».
- **Luce del cielo (IBL)**: il cielo atmosferico fotografato in una mappa d'ambiente (PMREM),
  rifatta quando il sole si muove (al più 2 volte/s). Dosata per materiale: a 1 slavava tutto,
  l'asfalto sembrava bagnato e il prato sotto il cielo azzurro si desaturava.
- **Luce per tappa** (`LUCE_TAPPE`): alba sul Kherlen → mattina → mezzogiorno sul Tuul → afa sulle
  dune → ora d'oro sul Khangai → tramonto a Khar Balgas → ora blu a Erdene Zuu → notte a Karakorum.
  Sole (elevazione, azimut, colore), foschia, Rayleigh, nebbia ed esposizione per tappa, raccordati
  per 600 segmenti; la notte della musica si somma. Sotto l'orizzonte il sole si spegne, resta una
  luna azzurra nell'emisferica e compaiono 2800 **stelle** che seguono la camera.
- **Paesaggio** (`3d/paesaggio.js`): **fiumi** nelle tappe di Kherlen, Onon, Tuul e Orkhon (letto
  scavato nel terreno al passo 5b, acqua che riflette il cielo e si increspa coi bassi); **nuvole**
  a ciuffi, quante dipende dalla tappa (quasi nessuna sulle dune); **montagne** all'orizzonte in due
  anelli nel colore della foschia; **pali di legno con la sciarpa blu** al posto dei paletti da
  circuito (le luci a tempo accendono la sciarpa); **gher** con porta rossa e lanterna negli
  accampamenti di steppa e nelle città, accese di notte; **erba** a blocchi attorno al cavallo, mossa
  da raffiche. Alberi ed erba stanno fuori da fiumi e accampamenti (`paesaggio.libero`).
  Notti più leggibili: luna azzurra nell'emisferica, esposizione più alta.
- **Rilievo per tappa** (`RILIEVO_TAPPE`: ampiezza, creste, pendenza massima vicino alla strada):
  steppa dolce, colline a Khustai e sull'Orkhon, montagne a creste su Burkhan Khaldun, Ulaan
  Tsutgalan e Khangai; i rilievi partono più vicino alla strada (raccordo 11000 invece di 16000).
- **Fiumi che attraversano**: il fiume cambia lato passando sotto la strada (8 attraversamenti
  sul viaggio, anche torrenti di montagna). Lì il terreno è scavato sotto la sede (il taglio finale
  è un minimo, quindi lo scavo vale), la scarpata si interrompe e c'è un ponte: impalcato di pietra
  e parapetto di legno su due correnti.
- **Pista sterrata** al posto dell'asfalto: terra e ghiaia disegnate nello shader della strada
  (solchi delle ruote, striscia d'erba a tratti in mezzo, sassi, chiazze), tinta per bioma dal
  vertex color; dell'asfalto restano solo rilievo e ruvidezza. Via linee di corsia e cordoli rossi/bianchi.
- **Ponti di pietra** solo dove l'acqua passa davvero sotto: lastre 45 sopra la pista, parapetti
  a blocchi con copertina, spalle fino all'acqua; pietra procedurale dalla posizione nel mondo.
  Niente pali con sciarpa sui ponti.
- **Alberi fotorealistici (impostori)**: abete e pino di Poly Haven (CC0). Ridotti in Blender a
  13–21 mila poligoni diventavano scheletri (gli aghi sono geometria vera); allora li ho fotografati
  in Blender a piena qualità da 8 lati (`tools/fotografa-alberi.py`, `assets/alberi/`, 4,7 MB in
  WebP) e nel gioco sono rettangoli che guardano la camera e mostrano la foto del lato giusto,
  tinti dalla luce della tappa, col vento e l'equalizzatore. Abeti e pini nelle foreste di
  montagna e lungo Onon/Orkhon; larici e betulle restano procedurali (nessun asset gratuito).

### 6 ottobre 2026 — Grafica: tutta la vegetazione e le nuvole fotografiche
- **Larici** verdi e d'oro: le foto degli abeti ricolorate (`tools/larici-da-abete.py`).
- **Latifoglie** al posto delle betulle procedurali: Island Tree 01–03 (Poly Haven, CC0), 8 vedute
  512×512, ingrandite ×2–2,6 (i modelli sono alberelli da 2,6–5 m). **Cespugli**: Fern 02, 512×256.
  Ora tutte le specie della foresta sono impostori; i modelli procedurali non si costruiscono più.
- **Erba**: al posto dei fili, ciuffi fotografati di fianco (Grass Medium 01/02, ortica, tarassaco,
  celidonia) in un atlante 4×4 (`assets/alberi/prato.webp`), ciascuno una croce di due rettangoli,
  fiori solo dove il prato è verde. I ciuffi coi pennacchi (celle 3–7) in foto vengono quasi neri:
  esclusi. Strumento unico `tools/fotografa-piante.py` (modi `impostore` e `ciuffi`).
  Trappola zsh: `$C:celandine…` è un modificatore di variabile → scrivere `${C}:…`.
- **Nuvole**: 6 nuvole volumetriche Cycles (`tools/nuvole-blender.py`, atlante 3×2) come rettangoli
  verso la camera, lato al sole col colore del sole (smorzato verso il bianco), ombra col cielo,
  sfumate nella foschia oltre 120 km di gioco; larghe ~90–160 mila unità.
- Misure 1080p senza limite: 211 fps a SMARMELLA 0, 184 a livello 4. Nessun errore sulle 12 tappe.

### 6 ottobre 2026 — Rifiniture del mondo di gioco
- **Pali**: tronco a 8 facce con curva e inclinazione diverse per palo, scuro e umido in basso,
  schiarito dal sole in cima; venature, spaccature e nodi disegnati nello shader (`aSciarpa = −1` marca
  legno e corda); tre giri di corda di canapa; sciarpa di seta lunga, con onda che la percorre, pieghe
  che scorrono e frange. Le luci a tempo accendono ancora la sciarpa.
- **Banchina** (`patchBanchina` in `3d/mondo.js`): niente più righe alterne (`isDark`); terra a chiazze,
  grumi, ghiaia, sassolini con ombra, ciglio pressato, esterno screziato d'erba secca. Trappola: le
  frequenze del rumore sono in unità di gioco (1 m = 800): sotto 0,01 non si vede nulla a distanza di camera.
- **Polvere** riscritta: nuvole irregolari (4 texture a batuffoli), un'emissione per zoccolo, colore =
  terra della tappa × luce del momento (di notte scura, all'alba calda), svanisce vicino alla camera
  (altrimenti è una macchia sull'obiettivo). Quella vecchia era color crema fisso e di notte era la
  "macchia di luce" sotto il cavallo. `cm3d.dust` per il debug. Resta il bersaglio `mondo.polvere` sulla cassa.

### 6 ottobre 2026 — Acqua e pali a blocchi
- **Acqua** (`fiumi` in `3d/paesaggio.js`): il nastro ora porta per vertice la posizione fra le rive,
  la direzione di corrente (tangente del centro) e la turbolenza. Shader: fondo sabbioso trasparente
  vicino a riva → verde-azzurro → scuro al centro; increspature che scorrono lungo il fiume (più veloci
  al centro, gonfiate dai bassi); schiuma sulla riva e, nei torrenti di montagna (tappe 3 e 9), sulle
  rapide; rugosità alta dove c'è schiuma; riflesso del cielo ridotto (1,25 → 0,6: a vista radente
  riflette tutto il cielo chiaro e diventa bianca). Il nastro è largo 1,3× la "mezza": prima il bordo
  stava 20–25 cm sopra la riva e l'acqua sembrava un canale sospeso (misurato: letto 450 sotto il pelo
  al centro, la riva lo raggiunge ~1,2× la mezza). Niente riflessi veri (planari): costerebbero un secondo rendering.
- **Pali**: con 26.000 istanze da 1500 vertici facevano scendere a 69 fps. Ora 420 vertici e a blocchi di
  300 segmenti con la propria sfera di visibilità: 241 fps (prima 211), il culling per blocchi li ha
  resi più veloci di prima. Lezione: ogni InstancedMesh lungo tutta la pista va a blocchi.

### 6 ottobre 2026 — Ovoo e massi
- **Ovoo** (`ovoo` in `3d/paesaggio.js`): 20 cumuli in 12 tappe (1–3 a tappa), a 3,4–5 larghezze di
  strada da un lato, mai in fiumi, ponti o accampamenti (`vicini` con `ds` più stretto). Una sola geometria
  unita (78 pietre sbozzate dal rumore, 7 bastoni a fascio, 4 sciarpe blu, 4 fili da 13 bandiere nei
  cinque colori) istanziata con scala e rotazione a caso. Bandiere e sciarpe si muovono nello shader
  (`aX` = libertà di movimento), le pietre hanno licheni e venature solo dove il colore del vertice è grigio.
- **Massi** (`massi`): ~1300 pietre lungo la pista, a blocchi di 300 segmenti, più fitte nelle tappe
  rocciose (DENS per tappa + peso roccia del suolo), con lo stesso shader di pietra.
- Trappole di collaudo: `roadDist` misura dal BORDO del corridoio (soglia 5200 scartava tutto); i test
  con camera libera finiscono dentro le colline, meglio la camera di gioco con `setPilota(false)` (cavallo
  fermo) e il cavallo ~55 segmenti prima, dal lato dell'oggetto; il lettore di immagini mette in cache per
  nome: copiare su un nome nuovo.

### 6 ottobre 2026 — Animali che ballano (`3d/animali.js`)
- Modelli: Quaternius CC0 (pecora, mucca, cavallo, lama, aquila), 300–800 poligoni, 24–28 ossa, clip
  Idle/Walk/Run/Jump; Poly Haven non ha animali veri. `assets/animali/*.glb` (1,4 MB), esportati da
  Blender con `tools/esporta-animali.py`. Yak = mucca scura, "cammello" = lama (manca un cammello vero).
- Posizione: `piazzaBranchi()` mette ~1000 animali in 134 branchi (6–20 per branco, per tappa: pecore
  nella steppa, yak in montagna, cavalli a Khustai, lama nelle dune), PRIMA degli alberi, che girano
  attorno (`paesaggio.occupa`). `creaFauna()` carica i modelli e tiene un pool di cloni skinnati: vivi
  solo i ~40 vicini al giocatore (da 30 segmenti dietro a 170 davanti). 44 animali ballanti: 193 fps.
- Ballo: la clip del salto non gira da sola, è AGGANCIATA alla fase del battito (`jump.time = fase × durata`),
  quindi cade sul tempo a qualunque BPM, anche se cambia; oltre 150 BPM un salto ogni due battiti. Sopra la
  clip (che stacca le zampe di soli ~25 cm) c'è un rimbalzo in più di ~40 cm. Sfasamento di poco fra
  animali del branco (l'onda attraversa il gregge), si voltano verso il giocatore, spinta/schiacciamento
  sulla cassa, e al drop un giro su se stessi. Le aquile (3) girano in cielo e battono le ali a tempo.
- Centralina: nuovo bersaglio `mondo.animali` (0 pascolano → 1 ballano): Groove 0,25, Festa 0,6,
  Rave 0,9, Apri tutto 1. A livello 0 non ballano mai: pascolano (clip Idle).
- Trappola: `action.setEffectiveWeight()` NON basta con `AnimationMixer`: il mixer ricalcola il peso da
  `action.weight` a ogni update. Usare `.weight`.

### 6 ottobre 2026 — Atmosfera: montagne, luna, lucciole, fuochi, nebbia bassa (`3d/atmosfera.js`)
- **Montagne** (sostituiscono i due anelli piatti): un anello di rilievo vero attorno alla camera, 540×22 punti
  fra 130 e 300 mila unità, creste dal rumore (catene dove `fbm` è alto, dentellatura fine), neve in cima
  e dove il pendio è dolce, roccia del colore della tappa, prospettiva aerea nello shader (più lontano e più in
  basso = più foschia). Per tappa (`MONTI`): altezza, linea della neve, roccia — alte e innevate a Burkhan
  Khaldun e sul Khangai, basse color sabbia nelle dune; i valori si raccordano piano fra tappe. Nei boschi
  gli alberi le coprono: si vedono nei tratti aperti e di sera, quando illuminano di blu.
- **Luna**: disco con i mari e un alone, davanti alla camera (un po' a destra) e segue le curve piano
  (altrimenti sarebbe sempre alle spalle): compare con le stelle.
- **Lucciole**: 320 punti additivi attorno al cavallo (scatola 9000×2100×9000) che lampeggiano, con un
  rilancio sulla cassa. Un solo draw call, posizioni calcolate nel vertex shader.
- **Fuochi**: uno davanti a ogni gher (85), due fiamme per fuoco, rumore che sale, alto e largo con la cassa;
  si accendono all'alba, al tramonto e di notte; alone d'aria calda sul prato; i DUE più vicini fanno luce vera
  (PointLight, due sempre presenti con intensità 0: il numero di luci non cambia mai, niente ricompilazioni).
- **Nebbia bassa**: 70 banchi piatti che scorrono col vento, ancorati al terreno, tanti sui fiumi
  (`NEBBIA_BASSA` per tappa), nessuno nelle dune.
- **Bandiere a ritmo**: nuovo uniform `uCassa` (musica.cassa): le bandiere degli ovoo e le sciarpe dei pali
  frustano di più sulla cassa.
- Trappola: gli attributi per istanza devono avere ESATTAMENTE tante voci quante le istanze: con 85 fasi per
  170 istanze `drawElementsInstanced` fallisce e la mesh sparisce senza un errore in console (solo un
  warning WebGL). Controllare `m.count` contro la lunghezza di ogni InstancedBufferAttribute.
- Misure: 229 fps a SMARMELLA 0, 192 a livello 4 (di notte accanto ai fuochi: 213 con i due lumi accesi).

### 7 ottobre 2026 — Livello 0 faceva ancora festa (bug mio)
- Segnalato dall'utente: tornando a SMARMELLA 0 il mondo continuava a battere. Misurato con una cassa finta
  (`Object.defineProperty(musica, 'cassa', { get, set: () => {} })` — il setter che ignora le scritture è
  necessario, un getter solo manda in errore il motore musicale): a livello 0 `U.uCassa` (bandiere degli ovoo,
  sciarpe dei pali, fiamme) pulsava 0→1, l'alone dei fuochi 0,25→0,67 e le lucciole fino a 0,3.
- Causa: quegli effetti leggevano `musica.cassa` direttamente invece di passare dalla centralina. Ora in
  `atmosfera.aggiorna` `cassa = musica.cassa × festa`, con `festa = min(1, mondo.animali × 1.6)`: 0 a Diretta,
  ~0,4 a Groove, 1 da Rave. Restano solo i guizzi naturali (la fiamma sfarfalla da sola, le lucciole lampeggiano da sole).
- REGOLA: ogni nuovo effetto a tempo deve passare da un bersaglio della centralina; a livello 0 il gioco è uguale a prima.

### 7 ottobre 2026 — Il velo di nebbia sulla strada
- Segnalato: una fascia lattiginosa sulla strada, con le basi dei pali sfumate e un bordo netto, "solo in certi
  punti". Era la nebbia bassa: piani orizzontali larghi 22–52 mila unità a ~0,5 m da terra; se il cavallo ci
  passa sotto/sopra il piano taglia la strada. Ora ogni banco svanisce del tutto entro 26.000 unità dalla
  camera (smoothstep 26–48 mila nello shader): resta solo lontano, come foschia di valle.
- Le strisce colorate orizzontali (rosa/verde/azzurro) dentro la fascia nell'immagine NON le ho riprodotte a
  livello 0: potrebbero essere il glitch/aberrazione del post a livelli alti. Da chiedere: tappa, livello, ora.

### 7 ottobre 2026 — Pallini colorati (forse solo Safari)
- L'utente vede un velo di puntini multicolore sopra la strada a SMARMELLA 0, che sparisce quando ci si entra;
  gioca in Safari, i miei test sono in Chrome e non lo riproducono. Sospetti, corretti per prudenza:
  `smoothstep` con i bordi invertiti (indefinito per le specifiche GLSL: Chrome/ANGLE lo tollera, Metal no) nelle
  lucciole e nelle fiamme; `pow` di un numero che può essere un soffio sotto zero (NaN) nelle lucciole; banchi di
  nebbia bassa sopra il corridoio della strada (ora mai).
- Nuovo interruttore nell'indirizzo: `?spegni=nebbia,lucciole,fuochi,montagne,luna,nuvole,acqua,erba,polvere,
  animali,ovoo,massi,pali,alberi` toglie quei pezzi dalla scena, per isolare un difetto di resa a occhio.

### 8 ottobre 2026 — Pista 1,5× più larga
- `ROAD_WIDTH` 2000 → 3000. Quasi tutto è in unità di larghezza strada e segue da solo (banchine, pali a 1,18,
  erba, fiumi, alberi da 4,3, ovoo, animali, portali, limite ±2,2 del giocatore). Sistemati a mano: i pezzi dei ponti
  (erano misure fisse, ora 2,6/2,8/3 × ROAD_WIDTH) e il piede della scarpata, che ora è VERGE_OUT + 3200 = 10400:
  con 4 × ROAD_WIDTH sarebbe arrivato a 12000, troppo vicino al raggio di curva minimo (13158).

### 8 ottobre 2026 — Takedown, bonus e rivali rifatti
- Problemi segnalati: nella razzia la tappa si vinceva al 2°-3° takedown; 40-80 $ a takedown compravano tutto il
  negozio a ogni tappa; 4 rivali con nome, sempre gli stessi, legati al giocatore e risorti dopo 3,5 s.
- **Rivali**: senza nome; pool di 4 attori, stato 'fuori' finché non compaiono. `spawnRivali()` ne fa comparire uno
  ogni ~60.000 unità di strada (±20%, ~4-5 s a tutta), 65% davanti e 35% dietro; abbattuti escono di scena (non si
  rialzano più). Vita `vitaRivale()` = 50 → 220 lungo il viaggio (da 3 a 11 pugni). Misurato: ~10 rivali a tappa.
- **Tappe**: finiscono sempre al traguardo; la razzia chiede `3 + i/2` takedown ENTRO il traguardo.
- **Bonus**: niente soldi. Ogni `TAKEDOWN_PER_BONUS` (5) takedown un gettone; a fine tappa ogni gettone vale UNA cosa
  fra cura, nitro pieno, sciabola, mazza, frusta, arco. Gli upgrade permanenti restano a XP. HUD: `KO n  BONUS g (k/5)`.

### 8 ottobre 2026 — Bonus progressivi, schermo intero per il debug
- Ogni bonus costa più takedown del precedente: 5, 7, 10, 15, poi gli aumenti seguono la somma dei due precedenti
  (23, 36, 57…). Takedown totali: 5, 12, 22, 37, 60, 96. `COSTI_BONUS` + `costoBonus(n)`; HUD `BONUS g (k/costo)`.
- «Pieno» senza proiezione (o doppio clic sull'anteprima) mette a schermo intero l'anteprima della console: lì
  tastiera, pad e schermate di fine tappa funzionano (nella finestra di proiezione no, i tasti non arrivano). Esc esce.

### 9 ottobre 2026 — Bonus scelto subito, contatore alla rovescia, menu a 8 bit
- Alla soglia di takedown il gioco si FERMA (stato 'bonus': la fisica non avanza) e compare il menu dei sei bonus
  (cura, nitro, sciabola, mazza, frusta, arco), disegnato sulla tela dell'HUD — quindi va anche in proiezione.
  Comandi: frecce + Invio, pad (croce + A), clic sulla casella; col pilota automatico sceglie da solo dopo 2 s
  (`sceltaPilota`: cura sotto metà vita, sciabola se a mani nude, altrimenti nitro). Caselle non disponibili spente.
  Spariti i gettoni e la spesa a fine tappa: lì restano solo gli upgrade permanenti a XP.
- Contatore nell'HUD alla rovescia: `BONUS FRA 5…1`, poi 7…1, 10…1 (numero grande in giallo, lampeggia all'ultimo),
  accanto `KO TOT n`.
- Menu e schermate di tappa (briefing, fine tappa, sconfitta, arrivo) rifatti nello stile dell'HUD: Press Start 2P,
  riquadri pieni con bordo bianco e ombra a scalino, colori della bandiera mongola (blu #0b3a8c, rosso #c4272f,
  giallo Soyombo #f9cf02). Niente emoji (il font a pixel non le ha).

### 9 ottobre 2026 — Gioco bloccato al bonus: moduli vecchi in cache
- Al 5° takedown il gioco si fermava senza menu. L'HUD dell'immagine scriveva `$undefined`: il browser aveva la
  pagina nuova (che ferma il gioco per la scelta) e un `3d/hud.js` di due versioni prima, preso dalla cache, che il
  menu non lo disegna. `python3 -m http.server` non vieta la cache e i moduli ES restano in memoria.
- `tools/server-sviluppo.py`: lo stesso server statico con `Cache-Control: no-store` (porta e indirizzo come argomenti).
  Va usato al posto di `http.server` mentre si sviluppa.
- Rete di sicurezza in `apriScelta()`: se l'HUD caricato non ha `sceltaA`, sceglie come il pilota, NON ferma il
  gioco e lancia il banner «RICARICA LA PAGINA».

### 9 ottobre 2026 — HUD nei colori della Mongolia, scritta del takedown sul rivale
- Tavolozza unica in `3d/hud.js` (blu notte #041737 per i riquadri, rosso #a51f27, giallo Soyombo #dcb200,
  vita rossa, nitro blu #5b95ea), scurita di un tono; i riquadri hanno la testata rossa col filo giallo come il
  menu dei bonus; le schermate DOM ripetono gli stessi colori nel CSS.
- La scritta del takedown copriva cavallo e strada (fascia grande al 42% dell'altezza). Proposte quattro varianti
  (`?takedown=centro|alto|nastro|lato|rivale`): l'utente ha scelto **rivale** — «TAKEDOWN» salta fuori sopra il
  rivale abbattuto, lo segue mentre cade (`notificaPos` da statoHud) e sale svanendo in ~1,1 s; dentro c'è
  «+150 - BONUS FRA n» (niente più popup +150 né etichetta KO lì sopra). I banner rari (tappa, drop, KO) restano grandi.

### 10 ottobre 2026 — Tachimetro a lancetta con il nitro
- Scelto il tachimetro a lancetta (opzione 1 delle tre). Il riquadro della velocità in alto a destra e gli altri
  stili (segmenti, rally, box) sono stati tolti dal codice. Il NITRO è un arco di 12 blocchi nel varco in basso del
  quadrante (da 225° a 315°: la scala dei km/h occupa gli altri 240°); lampeggia quando è pieno, e col boost
  la lancetta e le cifre diventano azzurre; sotto le cifre la scritta dice NITRO / NITRO PRONTO / BOOST!.
- Il riquadro in basso a sinistra ora ha: VITA, arma, BONUS FRA n · KO TOT. Lo SCUDO non esiste ancora come
  meccanica (c'è solo la parata, tasto I / LB): la riga sotto la vita è lasciata libera per quando si decide cosa fa.

### 10 ottobre 2026 — Scudo (rotolo di pluriball) e barra vita che si allunga
- **Scudo**: un rotolo di pluriball raccolto in pista dà `SCUDO_PER_ROTOLO` = 30 punti di scudo, tetto `SCUDO_MAX` = 100.
  I colpi dei rivali consumano PRIMA lo scudo (`assorbiScudo`), poi la vita; non si ricarica da solo, si perde se si
  muore. Se lo scudo assorbe tutto il colpo il popup dice «SCUDO!» e il lampo di danno è debole. Costanti da regolare.
- **Il rotolo** (`rotoli`, `updateRotoli`): 35 lungo il viaggio (uno ogni 300.000 unità, ~3 per tappa), cilindro di
  bolle azzurre con anima di cartone e due teste, coricato di traverso, che gira come un'insegna e su se stesso come un
  rullo; si vede entro 90.000 unità e torna dopo 20 s; se lo scudo è già al massimo non si raccoglie. Il pluriball
  doveva essere scuro e a doppia faccia: chiaro e trasparente sul cielo si vedeva solo il bordo.
- **HUD**: sotto la vita c'è la riga SCUDO (blocchi azzurro chiaro); un blocco = 100/9 ≈ 11 punti. La barra VITA ora è
  lunga quanto la vita massima (190 con tre «vita max» = 17 blocchi); oltre ~640 px di barra i blocchi si stringono.
- Trappola di collaudo: `cm3d.setFreeRoam(false)` richiama `resetRun()` e rimette il gioco in briefing (niente HUD, cavallo fermo).
