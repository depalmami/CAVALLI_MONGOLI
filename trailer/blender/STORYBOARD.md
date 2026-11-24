# Trailer in Blender — storyboard v2 (30 s verticale, comico)

Niente titoli, niente cartelli, niente HUD: solo immagini. Dove un giorno andranno i titoli c'è uno spazio libero (il nero di S28).
La v1 (60 s cinemascope, tono serio-epico, col 30 s ricavato) è in `STORYBOARD-v1-60s.md`: da lì si riprendono gli shot tagliati se un giorno si fa un 60 s.

## Decisioni (23 nov)

| Domanda | Scelta |
|---|---|
| Formato | **solo 30 s verticale**, 9:16 (1080×1920), 24 fps. Il 60 s cinemascope non si fa. |
| Tono | **apertamente comico**: tempi da gag, reazioni esagerate, montaggio che sottolinea le battute. |
| Predoni | **tinte del gioco smorzate**: arancio, azzurro, verde e rosa del gioco, meno saturi e impolverati. |
| Finale | **la birra sui pattini dopo il nero**; zero secondi di gameplay. |

## L'idea in una riga

**Un trailer d'azione epico che non riesce a restare serio, perché il suo eroe è un cavallo di cartone con dentro due uomini a piedi nudi.**
Si parte come un kolossal (alba, controluce, musica solenne) e ogni volta che il film prende quota una gag lo smonta: la musica si inceppa,
la camera piomba sui piedi nudi, il cavallo guarda in macchina. Poi si riparte più epici di prima. In 30 s: l'eroe, le armi, i predoni,
la birra, il viaggio da un'alba a una notte, il Boss su 14 gambe in jeans, il salto.

**Il meccanismo:** montato come un trailer serio, interrotto dalle gag. Ogni gag ha il suo battito di silenzio (0,5 s): è lì che si ride.

### Regole della comicità (valgono per tutti gli shot)
- **La musica si ferma sulle battute** (disco che gratta, oppure un battito di silenzio) e riparte sul taglio dopo. Nella tabella: «stop».
- **Zoom a scatto e fermo immagine** sottolineano il momento buffo invece di nasconderlo.
- **Il cavallo guarda in macchina** tre volte: dopo i piedi (S05), dopo la birra (S14), nel fermo immagine finale (S27). Il cartone non ha
  espressione, e proprio per questo funziona: la faccia impassibile la fa chi guarda.
- **Fisica da cartone animato** solo nei punti scelti: le gambe che girano a vuoto prima di partire (S06), il predone che cade rigido come un
  giocattolo (S11), una gamba del Boss fuori passo (S22), il Boss che tossisce la polvere (S26).
- **Il verticale lavora per noi:** le cose alte riempiono il quadro — il cavallo dalla testa ai piedi, la sciabola dritta, la schiena a gradini
  contro la luna, la testa del Boss sopra il cavallino.

## Formato e griglia

| | |
|---|---|
| Formato | **30 s**, 9:16, 1080×1920, 24 fps = 720 fotogrammi (storie e reel) |
| Griglia musicale | montaggio sui **0,5 s = 12 fotogrammi** (nato a 120 BPM); la musica è a **165 BPM** (vedi «Musica a 165 BPM»): 1 s = 2,75 battiti |
| Zona sicura | in alto e in basso ~250 px senza niente d'importante (lì vanno nome, didascalie e pulsanti di IG/TikTok) |
| Musica / suoni | non ancora: lo storyboard dice dove cadono i colpi e dove la musica si ferma |
| Ottiche | le focali sono indicative: in verticale Blender misura il sensore sul lato lungo, quindi a parità di mm il quadro è più stretto in larghezza |

## I quattro atti e la luce

Un solo giorno che passa in 30 secondi, coi valori veri di `LUCE_TAPPE` (`horse-racing-3d.html`), come nei set del kit.

| Atto | Tempo | Tappa del gioco | Sole | Umore |
|---|---|---|---|---|
| 1 · L'eroe | 0:00–0:05,5 | Fiume Kherlen, alba | 4° · `#ffb27a` | kolossal → prima gag |
| 2 · Armi e lotta | 0:05,5–0:14,5 | Guado dell'Onon → Burkhan Khaldun | 14°–28° | ritmo, colpi, la birra |
| 3 · Il viaggio | 0:14,5–0:18 | Tuul → Dune → Khar Balgas → Erdene Zuu → Karakorum | 58° → −5° | il sole cala a ogni taglio |
| 4 · Il Boss | 0:18–0:27 | Karakorum, notte | luna | orrore finto, poi lo scontro |
| Coda | 0:27–0:30 | — | — | nero, poi la birra |

## Tabella dei tempi

| Shot | Inizio | Durata (s) | Battiti | Titolo | Colpo / gag |
|---|---|---|---|---|---|
| S03 | 0:00 | 2 | 4 | Il cavallo sul dosso | musica solenne |
| S04 | 0:02 | 1,5 | 3 | I piedi | zoom a scatto · **stop** |
| S05 | 0:03,5 | 1 | 2 | Sguardo in macchina | silenzio |
| S06 | 0:04,5 | 1 | 2 | La partenza | gambe a vuoto, poi via · riparte la musica |
| S08 | 0:05,5 | 1,5 | 3 | La cassa | la presa al volo |
| S09 | 0:07 | 2 | 4 | Quattro armi (4 × 0,5) | un colpo per arma |
| S10 | 0:09 | 0,5 | 1 | I predoni | |
| S11 | 0:09,5 | 1,5 | 3 | Il duello | il predone cade rigido |
| S13a | 0:11 | 0,5 | 1 | Il rotolo | |
| S13b | 0:11,5 | 1 | 2 | Il pluriball | bolle a catena |
| S14 | 0:12,5 | 2 | 4 | La Birra Grande | **stop** · doppia presa · sguardo in macchina |
| S15 | 0:14,5 | 0,5 | 1 | Piana del Tuul | |
| S16 | 0:15 | 0,5 | 1 | Dune e lama | il lama lo segue con la testa |
| S18 | 0:15,5 | 0,5 | 1 | Khar Balgas | |
| S19 | 0:16 | 0,5 | 1 | Erdene Zuu | |
| S20 | 0:16,5 | 1,5 | 3 | Karakorum, la terra trema | la musica si spegne |
| S21 | 0:18 | 1 | 2 | La schiena a gradini | tonfo |
| S22 | 0:19 | 2 | 4 | Sotto il ventre | tonfi a tempo · una gamba fuori passo |
| S23 | 0:21 | 1,5 | 3 | La testa e la mascella | ruggito |
| S24 | 0:22,5 | 1 | 2 | Il cavallo e la sciabola | |
| S25 | 0:23,5 | 1 | 2 | La carica | |
| S26 | 0:24,5 | 1 | 2 | Il morso | tossisce polvere |
| S27 | 0:25,5 | 1,5 | 3 | Il salto | fermo immagine · sguardo in macchina |
| S28 | 0:27 | 3 | 6 | Coda | 0,5 fermo + 1,5 nero (titoli) + 1 birra |

Totale **30,0 s** (atti 5,5 / 9 / 3,5 / 9 / 3). Tutte le durate sono multipli di mezzo secondo.
**Tagliati** rispetto alla v1: S01 (alba sul fiume), S02 (il branco), S07 (galoppo laterale), S12 (schivata e frusta), S17 (cascate).
Se servisse altro spazio per le gag, si toglie prima S10, poi S13a.

---

## ATTO 1 · L'EROE (0:00–0:05,5)

Quattro secondi da kolossal, poi la prima gag. Chi guarda deve credere al film serio fino ai piedi.

### S03 · Il cavallo sul dosso — 2 s (0:00)
- **Verticale:** il cavallo in alto a metà quadro, controluce col sole a 4° dietro la testa; sotto, la strada che scende verso di noi.
- **Azione:** spinta lenta in avanti. Il vento muove criniera e coda; si capisce poco a poco che è di **cartone**. Musica solenne, cori.
- **Pose:** `Idle` (c'è). **Set:** Kherlen all'alba (c'è).

### S04 · I piedi — 1,5 s (0:02)
- **Verticale:** il formato è fatto per questo: **zoom a scatto in basso**, dalla pancia di cartone ai jeans ai **piedi nudi** nell'erba.
- **Azione:** le dita dei piedi si muovono. **Stop** della musica sul taglio (disco che gratta).
- **Pose:** `Idle`; le dita sono un blocco unico (si muove il piede, non le dita: va bene così).

### S05 · Sguardo in macchina — 1 s (0:03,5)
- **Verticale:** primo piano del muso di cartone, la manica blu sulle redini.
- **Azione:** **silenzio**. Il cavallo gira la testa lentissimo e **guarda in macchina**. Taglio secco.
- **Pose:** `Sguardo_D`/`Sguardo_S` sommato a `Idle` (c'è); la camera va messa dove arriva lo sguardo.

### S06 · La partenza — 1 s (0:04,5)
- **Verticale:** bassa, davanti, i piedi in basso e il cavallo intero.
- **Azione:** **gambe a vuoto** come nei cartoni: 0,5 s di galoppo velocissimo sul posto, zolle che volano; poi parte di colpo e lascia una
  **nuvola di polvere con la sua sagoma**. Riparte la musica, più forte di prima.
- **Pose:** `Gallop` accelerato ×3 sul posto (c'è). **Manca:** la nuvola a forma di cavallo (polvere emessa dalla mesh cotta).

## ATTO 2 · ARMI E LOTTA (0:05,5–0:14,5)

Ritmo da trailer d'azione: un colpo per battito, i tagli sui colpi.

### S08 · La cassa — 1,5 s (0:05,5)
- **Verticale:** sopra la spalla destra del cavallo; la mano in alto a destra, la sciabola che gira sopra.
- **Azione:** la cassa esplode in pannelli di cartone, la sciabola volteggia, **la manica la prende al volo**; il cavallo se la guarda, fiero.
- **Pose:** `Afferra` (c'è). **Manca:** la cassa divisa in pannelli che volano (nell'animatic sono scatole finte).

### S09 · Quattro armi — 2 s (0:07), quattro inserti da 0,5 s
Presentate come in una televendita epica, una per battito, sul fondo sfocato della steppa: in verticale ogni arma sta **dritta** e riempie il quadro.
- **a · Sciabola:** un lampo scorre sul filo. **b · Mazza:** gli spuntoni girano. **c · Frusta:** lo schiocco con la corona di polvere.
  **d · Arco:** la freccia parte e la camera la segue.
- **Modelli:** `saber`, `mace`, `whip`, `bow`, `freccia` (ci sono); per i macro meglio gli originali in `~/Downloads`; la corda dell'arco va rifatta.

### S10 · I predoni — 0,5 s (0:09)
- **Verticale:** tele, tre predoni escono dalla polvere uno dietro l'altro.
- **Predoni:** tinte del gioco **smorzate** (arancio, azzurro, verde: metà saturazione, più scure, polvere sulle zampe).

### S11 · Il duello — 1,5 s (0:09,5)
- **Verticale:** il cavallo in basso a destra, la sciabola che sale in diagonale, il predone in alto a sinistra.
- **Azione:** testata contro fendente, scintille, polvere ferma (0,5 s al rallentatore); poi il predone **cade rigido di lato come un
  giocattolo** (si ribalta tutto d'un pezzo, le zampe dritte). Colpo sul tonfo.
- **Pose:** `Sciabola_Fendente` (c'è), predone `Attack_Headbutt`; la caduta rigida è una rotazione del predone intero, non la clip `Death`.

### S13 · Il pluriball — 1,5 s (0:11)
- **a · 0,5 s:** il rotolo rotola sulla strada, il cavallo ci passa sopra: lampo, ed è **avvolto nel pluriball**.
- **b · 1 s:** macro: la mazza di un predone lo colpisce e le bolle **scoppiano a catena** (al 10%); il cavallo abbassa la testa a guardarsi, soddisfatto.
- **Manca:** le bolle vere sul busto (istanze che spariscono in ritardo con la distanza dall'urto).

### S14 · La Birra Grande — 2 s (0:12,5)
È **la battuta del trailer**: le si dà il tempo.
- **Verticale:** camera bassa a bordo strada; il bicchiere grande in primo piano, il cavallo dietro.
- **Azione:** il bicchiere sui pattini sfreccia in zigzag. **Stop** della musica. Il cavallo passa, **doppia presa** (si gira, torna avanti, si
  rigira di scatto), **sbanda** sui piedi nudi e **guarda in macchina**. Riparte la musica sul taglio.
- **Pose:** birra `pose.birra` e `Sguardo_D` (ci sono). **Manca:** la sbandata (piedi che scivolano: si può fare con `Gallop` rallentato e il corpo inclinato).

## ATTO 3 · IL VIAGGIO (0:14,5–0:18)

Montaggio a raffica: **stessa posa, stesso galoppo, mondo diverso a ogni battito**, il sole più basso a ogni taglio. La ripetizione è la gag.

### S15 · Piana del Tuul — 0,5 s · S16 · Dune — 0,5 s · S18 · Khar Balgas — 0,5 s · S19 · Erdene Zuu — 0,5 s
- **Verticale:** il cavallo sempre nello stesso punto del quadro, di profilo, con lo stesso fotogramma di `Gallop`: cambia solo il mondo intorno.
- **S16:** il **lama** sulla cresta lo segue girando la testa, impassibile.
- **S18:** l'aquila in alto nel quadro, il tramonto rosso.  **S19:** stupa e lanterne nell'ora blu.

### S20 · Karakorum, la terra trema — 1,5 s (0:16,5)
- **Verticale:** la pozza in primo piano in basso, il cavallo al passo sopra, le luci della città in alto.
- **Azione:** cerchi concentrici nella pozza, i sassi saltano; il cavallo si ferma, un orecchio si gira. La musica si spegne.

## ATTO 4 · IL BOSS (0:18–0:27)

Un finto film dell'orrore che si sgonfia nelle gag, poi lo scontro vero.

### S21 · La schiena a gradini — 1 s (0:18)
- **Verticale:** perfetto per la scalinata: la schiena nera a gradini sale nel quadro contro la luna piena. Tonfo.

### S22 · Sotto il ventre — 2 s (0:19)
- **Verticale:** camera a 30 cm da terra, tre o quattro gambe in jeans riempiono il quadro dall'alto in basso.
- **Azione:** le **14 gambe marciano all'unisono**, un tonfo per battito, la camera trema. Poi **una gamba è fuori passo**: si accorge,
  fa un saltello e rientra in passo. Orrore e comico insieme.
- **Pose:** il passo da parata c'è (`pose.boss`). **Manca:** la gamba fuori passo (uno sfasamento per gamba e il saltello).

### S23 · La testa e la mascella — 1,5 s (0:21)
- **Verticale:** la testa-logo gira verso di noi e riempie il quadro; la **mascella si spalanca** (denti, lingua), un filo di vapore, ruggito.
- **Pose:** mascella e testa (ci sono).

### S24 · Il cavallo e la sciabola — 1 s (0:22,5)
- **Verticale:** il contrasto di taglie: in alto la testa del Boss che sbava, in basso il cavallino di cartone che alza la sciabola; **la lama
  prende la luna**.
- **Pose:** `Sciabola_Alta` (c'è).

### S25 · La carica — 1 s (0:23,5)
- **Verticale:** tele compresso, i due uno contro l'altro sulla strada; polvere.
- **Pose:** `Gallop` + `Sciabola_Alta`, Boss in passo veloce (ci sono).

### S26 · Il morso — 1 s (0:24,5)
- **Azione:** la mascella si chiude **sulla polvere**: il cavallo non c'è più. Il Boss **tossisce** una nuvoletta di polvere.
- **Manca:** lo sbuffo dalla bocca (polvere che esce dalla mascella aperta).

### S27 · Il salto — 1,5 s (0:25,5)
- **Verticale:** dal basso: la schiena a gradini in basso, il cavallo in volo a metà quadro con la sciabola alta, la luna in alto.
- **Azione:** **fermo immagine** sull'ultimo battito, e nel fermo il cavallo ha la testa girata **in macchina**.
- **Pose:** `Salto` + `Sciabola_Alta` (ci sono) + `Sguardo` verso la camera.

### S28 · Coda — 3 s (0:27)
- 0,5 s ancora sul fermo immagine, poi **1,5 s di nero e silenzio**: lo spazio per i titoli (non inserirli ora).
- **1 s:** nel nero, il **bicchiere sui pattini** attraversa il quadro da un lato all'altro, illuminato solo di taglio. Ultimo colpo, fine.
- **Pose:** `pose.birra` (c'è).

### Tagliati (restano in `STORYBOARD-v1-60s.md`)
S01 alba sul Kherlen, S02 il branco di cavalli veri, S07 galoppo laterale sulla strada, S12 schivata e frusta, S17 cascate di Ulaan Tsutgalan.

---

## Cosa abbiamo già e cosa manca

| Cosa | Stato | Cosa manca |
|---|---|---|
| Protagonista (cavallo di cartone) | `protagonista-cartone.glb` con `Gallop`, `Idle`, `Walk`; il `.blend` ha il rig Rigify completo. **Dal 23 nov:** rig del trailer col braccio e le clip `Sciabola_Fendente`, `Sciabola_Alta`, `Frusta`, `Afferra`, `Sguardo_D/S`, `Salto` (vedi «Rig e pose») | calcio, partenza; pugno che si apre (la mano è un blocco unico) |
| Predoni | `horse-quaternius.glb`: `Gallop`, `Gallop_Jump`, `Attack_Kick`, `Attack_Headbutt`, `Death`, `Idle_HitReact_L/R`… | sono cavalli low-poly in tinta pastello: da lontano vanno bene, da vicino no |
| Boss | `coccodrillo.glb` (39 pezzi rigidi), `testa-bocca.blend`, `testa-60k.blend`; originale 183 MB in Git LFS. **Dal 23 nov:** passo da parata, mascella, testa e sobbalzo in `tools/trailer3d/pose.py` | sciabola per il macro |
| Armi | 5 GLB da 15–25k triangoli e texture 1024 px; originali da 65 MB in `~/Downloads` | per i macro usare gli originali; corda dell'arco |
| Cassa, rotolo, pony | `cassa.glb`, `rotolo.glb`, `pony-skin.glb` | pony-skin è solo il busto (le gambe vanno prese dal protagonista); bolle vere per il macro |
| Birra Grande | `birra.glb` (3 pezzi rigidi). **Dal 23 nov:** la spinta dei pattini in `pose.birra()` (la formula del gioco, esagerabile) | — |
| Animali | pecora, mucca, lama, cavallo (Idle, Walk, Run, Death), aquila (`Flying`, `Idle`) | — |
| **Il mondo** | **non esiste in Blender**: nel gioco è un terreno procedurale in three.js | **il kit di set** (sotto) |

### Il kit di set (la parte più grande del lavoro)
Si costruisce **una volta**: terreno spostato con erba, strada (`textures/Asphalt014`, `Grass004`), cielo Nishita, nebbia a volume, erba e cespugli istanziati
(sagome in `assets/alberi`), poi si rilancia con le luci di `LUCE_TAPPE` per ogni tappa. Gli shot sono quasi tutti stretti (tele, macro, controluce,
polvere), quindi non serve un mondo intero: serve che ogni inquadratura sembri costruita. In più: stupa (S19), pozza (S20), gola e acqua (S17).

### Render
EEVEE per quasi tutto (motion blur, profondità di campo); Cycles con Metal solo per i macro (S05, S09, S13, S23), come già in `tools/nuvole-blender.py`.
**I tempi per fotogramma sono da misurare** con un primo shot di prova prima di promettere una consegna.
Il montaggio e il grading si fanno come per `trailer/azione` (Python + ffmpeg, che c'è).

## Animatic (fatto il 23 nov)
Un fotogramma per shot coi modelli veri, in EEVEE a bassa qualità, montato muto sui tempi della v1 (60 s) (S09 ha 4 fotogrammi, S13 ne ha 2: 31 in tutto).
- `trailer/blender/animatic/animatic-60s.mp4` — la versione principale, 60,0 s, 24 fps.
- `trailer/blender/animatic/animatic-30s-ritmo.mp4` — il taglio breve con gli stessi fotogrammi: prova il **ritmo**, non le inquadrature verticali (quelle vanno rifatte in 9:16).
- `trailer/blender/animatic/foglio-contatti.jpg` e `fotogrammi/` — le 31 immagini, con sigla e tempi nel foglio.
- Si rifà con `tools/trailer3d/animatic.py` (un fotogramma ≈ 2 s; si può rifare un solo shot: `-- <cartella> S11`) e `tools/trailer3d/monta-animatic.py`.
- Ancora grezzi di proposito: nebbia e polvere sono finte, la gola delle cascate (S17) è un blocco di cubi, le stupa sono tornite al volo, il protagonista non ha le pose d'attacco (la sciabola è solo appoggiata alla mano).

## Kit di set (fatto il 23 nov)
Il mondo del gioco rifatto per le macchine da presa, in `tools/trailer3d/kit.py` (guida in `tools/trailer3d/LEGGIMI.md`). Stesse ricette del gioco:
pista di **terra** con due solchi e ghiaia sui bordi (non asfalto: come in `3d/mondo.js`), banchina erbosa, suolo per bioma (erba / steppa secca / sabbia / roccia),
rilievo e luce di **ogni tappa**, alberi e cespugli = le stesse foto di `assets/alberi`, fiume dove lo mette il gioco. In più, per la macchina da presa: ciuffi
d'erba veri attorno all'azione, nuvole, catena di montagne all'orizzonte, ger, rovine di terra cruda, stupa e lanterne, luci della città, pozza coi cerchi.
- `trailer/blender/kit/foglio-12-tappe.jpg` — le 12 tappe, stessa scena con luce e bioma diversi (anteprima 1280×536, 24 campioni).
- `trailer/blender/kit/beauty_00.jpg` (alba sul Kherlen), `beauty_09.jpg` (tramonto a Khar Balgas), `beauty_11.jpg` (notte a Karakorum) — 2560×1072, EEVEE 64 campioni.
- `trailer/blender/kit/kit-alba.blend` — la scena dell'alba, da aprire e girarci dentro (percorsi relativi verificati: si riapre e si renderizza).
- `trailer/blender/kit/alba-eevee.jpg` e `alba-cycles.jpg` — la stessa inquadratura nei due motori.

**Tempi misurati** (2560×1072, scena statica, questo Mac): **EEVEE 1,4 s a fotogramma** (64 campioni; 1440 fotogrammi ≈ 35 minuti), **Cycles 69 s a fotogramma** (64 campioni + denoise;
150 fotogrammi ≈ 3 ore). Con sole basso (alba, tramonto) EEVEE dà una luce piatta: niente luce radente, niente ombre lunghe, niente disco solare; Cycles sì, ed è molto meglio.
Quindi: **EEVEE per quasi tutto, Cycles per gli shot d'alba e tramonto e per i macro** (S01–S05, S18, S19). I tempi con animazione, mosso e profondità di campo vanno ancora misurati.

**Ancora grezzo o mancante:** gola e cascata rossa di S17 (ci sono solo massi rossi), acqua del fiume piatta (una striscia scura), nuvole con rumore e senza forma di cumulo,
stupa e ger essenziali, la notte è scura e senza luna in quadro (la luna si sposta per shot), le conifere sono carte (foto) e da vicino si vedono piatte.
Per alberi veri in 3D servirebbero i modelli Poly Haven (CC0) da cui il gioco ha tratto le foto: sono da scaricare e non l'ho fatto senza chiedere.

## Animatic v2 (fatto il 23 nov)
Gli stessi 31 fotogrammi e gli stessi tempi dell'animatic v1, ma girati nei set del kit: ogni shot nella sua tappa (atto 1 al Kherlen, atto 2 fra Onon e
Burkhan Khaldun, atto 3 nelle sue sei tappe, atto 4 di notte a Karakorum). Alba e tramonto (S01–S05, S18) in **Cycles**, il resto in EEVEE.
- `trailer/blender/animatic-v2/animatic-60s.mp4`, `animatic-30s-ritmo.mp4`, `foglio-contatti.jpg`, `fotogrammi/`.
- `trailer/blender/animatic-v2/prima-e-dopo.jpg` — S03, S11, S18, S21: a sinistra v1, a destra v2.
- Si rifà con `tools/trailer3d/animatic2.py` (tutti i 31 fotogrammi in meno di 2 minuti; un solo shot: `-- <cartella> S17`) e `monta-animatic.py`.
- Cambiati rispetto alla v1: S02 ora è girato lungo la strada (i cavalli di profilo, in controluce), S04 inquadra i piedi nell'erba vera, S17 ha una gola
  scavata nel terreno con pareti di roccia, il fiume rosso e la cascata, S20 ha la pozza sulla pista. Il kit ora sa scavare una gola (`Mondo(..., gola=...)`).
- Ancora deboli: S25 (Boss e cavallo troppo piccoli nel quadro), S26 (la polvere è una macchia), S27 (il cavallo in volo è piccolo), la notte in generale.

## Rig e pose (fatto il 23 nov)
Il protagonista nel gioco non ha ossa nel braccio (la manica pesa sulla colonna) e il Boss e la birra sono pezzi rigidi mossi a codice: per il trailer
servivano le pose che lo storyboard chiede. Il `.blend` del gioco **non è toccato**: tutto sta in una copia per il trailer, rifatta da script.
- `trailer/blender/rig/protagonista-trailer.blend` (da `tools/trailer3d/rig.py`): il rig Rigify del gioco **più il braccio destro** — `braccio.R`
  (spalla nascosta dentro la scatola → gomito sulla fessura del cartone), `avambraccio.R`, `mano.R` e `presa.R` (dove si impugna l'arma). I pesi di
  manica e mano sono ricalcolati solo sui vertici blu e color pelle; la mano è **staccata** dalla redine e dalle frange della criniera (la mesh di Meshy
  è un'unica superficie: senza il taglio, alzando la mano si tirava dietro strisce di cartone).
- **Clip nuove** (24 fps): `Sciabola_Fendente` (carica 7 · colpo 11 · seguito 15), `Sciabola_Alta` (alta dal 12), `Frusta` (schiocco 10),
  `Afferra` (presa 8) — solo braccio, si sommano a `Gallop`/`Walk`/`Idle`; `Sguardo_D`/`Sguardo_S` — collo e testa girano di ~55°, relativi;
  `Salto` — stacco 5 · in aria 9 · apice 14 · discesa 20 · atterraggio 26, con le gambe davanti raccolte e quelle dietro tese.
- `tools/trailer3d/pose.py`: `eroe()` (corpo + braccio + sguardo + arma nella presa, cotto in mesh statica), `boss()` (14 gambe **all'unisono, come
  una parata**: gamba d'appoggio tesa e piede fermo a terra, ginocchio piegato in volo, il corpo che scende a falcata aperta; mascella, testa che si
  gira o si alza), `birra()` (la spinta dei pattini di `3d/birra.js`, con l'ampiezza esagerabile).
- `trailer/blender/rig/foglio-pose.jpg` (10 pose da tre lati, Workbench) e `foglio-boss-birra.jpg` (quattro fasi del passo, otto della spinta).
- **Animatic v3** = l'animatic v2 con le pose: `trailer/blender/animatic-v3/` (`animatic-60s.mp4`, `animatic-30s-ritmo.mp4`, `foglio-contatti.jpg`,
  `prima-e-dopo.jpg`, `fotogrammi/`). Cambiati: S08 (la mano afferra la sciabola che gira, la cassa in pezzi, camera sulla spalla), S10 (gira appena
  la testa), S11 (fendente contro la testata, le scintille sulla punta), S12 (la frusta schiocca sul predone, ora a destra dove sta il braccio), S14
  (la birra in spinta, il cavallo si gira verso di noi), S21–S27 (il Boss marcia; S23 gira la testa a bocca aperta; S24 e S25 sciabola alta; S25 più
  stretto col 135 mm; S26 polvere più leggera; S27 il salto vero con la sciabola alta).
- **Limiti:** il pugno non si apre (S08 è una presa «a pugno chiuso»); dove c'era il pugno resta un pezzetto di redine; il gomito può uscire
  dalla fessura solo di poco (dentro la scatola non c'è il braccio); fra le pose le clip interpolano in Bezier e non sono ancora state viste in movimento.

## Animatic verticale (fatto il 23 nov)
Lo storyboard v2 in immagini: 30 s in 9:16, i 24 shot sui tempi della tabella in cima (27 fotogrammi: S09 ne ha 4, S13 2), nei set del kit e con
le pose del rig del trailer, inquadrati per il verticale.
- `trailer/blender/animatic-verticale/animatic-verticale-30s.mp4` — 720×1280, 24 fps, 30,0 s (720 fotogrammi), muto.
- `trailer/blender/animatic-verticale/foglio-contatti.jpg` e `fotogrammi/`.
- Si rifà con `tools/trailer3d/animatic-verticale.py` (tutti i fotogrammi in ~1 minuto e mezzo; un solo shot: `-- <cartella> S14`) e
  `tools/trailer3d/monta-verticale.py`.
- Siccome è muto, le battute della musica sono scritte in sovrimpressione (STOP, SILENZIO, TONFO…), e il montaggio simula già lo zoom a
  scatto sui piedi (S04), il fermo immagine (S27–S28) e la birra che attraversa il nero (S28).
- Le gag nei fotogrammi: la sagoma di polvere col cavallo già lontano (S06), il predone che cade rigido con le zampe dritte (S11), la doppia
  presa con lo sguardo in macchina davanti alla birra (S14), il lama che lo guarda dalla cresta (S16), la gamba fuori passo (S22), il Boss
  impennato che incombe sul cavallino (S24), la tosse di polvere (S26), il cavallo in volo davanti alla luna (S27).
- **Deboli:** i predoni smorzati, nella foschia del mattino, vengono quasi bianchi (S10); la gamba fuori passo in S22 non si distingue
  in un fotogramma fermo, si vedrà solo in movimento; la sbandata davanti alla birra è solo un'inclinazione del corpo; la notte resta scura.

## S14 animato (fatto il 23 nov) — il primo shot vero
La battuta del trailer, animata per davvero: 2 s, 48 fotogrammi, 1080×1920, EEVEE con mosso. Scena vera a chiavi, salvata da riaprire.
- `trailer/blender/shot/S14/S14-finale.mp4` (e i fotogrammi PNG), `trailer/blender/shot/S14.blend` (la scena: si apre e si ritocca in Blender).
- Si rifà con `tools/trailer3d/shot-s14.py -- <cartella> prova` (540×960, ~15 s, per giudicare i tempi) o `finale`.
- **La scaletta, al fotogramma:** 1–19 la birra a zigzag attraversa il quadro a 3 m dalla camera e per un attimo copre il cavallo che
  arriva; 10–17 il cavallo la segue con la testa; 17–19 torna avanti come niente fosse; **21–23 doppia presa**; 24–36 la sbandata (il
  galoppo rallenta e si blocca al 32 coi due piedi davanti puntati a terra, mentre il corpo scivola fino al 36: i piedi nudi pattinano,
  si piega indietro attorno ai piedi davanti, ruota verso la birra, polvere); 35–41 si gira e **guarda in macchina**; 41–48 fermo.
- **Come è fatto:** rig vivo (non cotto) con due strisce NLA, `Gallop` col tempo chiavato fotogramma per fotogramma (così rallenta e si
  blocca) e `Sguardo_D` sommato con l'influenza chiavata; la radice del cavallo a chiavi lungo la strada; la birra a chiavi (radice sullo
  zigzag, piegata dentro le curve, pattini e bicchiere con la spinta del gioco). Lo sguardo in macchina è **misurato**: nell'ultimo
  fotogramma si calcola dove punta il muso e si gira il corpo finché punta l'obiettivo.
- **Da rivedere quando lo guardi:** i tempi della doppia presa (2 fotogrammi: forse troppo secca), la quantità di polvere, se la birra
  deve restare in quadro un battito in più.

## Atto 1 animato (fatto il 23 nov) — S03, S04, S05, S06
I primi 5,5 s del trailer, animati e girati in **Cycles** all'alba (1080×1920, 48 campioni, mosso), ognuno con la sua scena da riaprire.
- `trailer/blender/shot/S03.blend` … `S06.blend`, i fotogrammi e i video in `trailer/blender/shot/S03/` … `S06/`, e l'atto montato in
  `trailer/blender/shot/atto1.mp4` (5,5 s, 132 fotogrammi).
- Si rifà con `tools/trailer3d/shot-atto1.py -- trailer/blender/shot prova|finale [S03 …]` (la prova dei quattro, 540×960, ~4 minuti).
- **S03** (48 f): carrellata lenta in avanti sul cavallo fermo in controluce (`Idle`), ombre lunghe verso di noi.
- **S04** (36 f): zoom a scatto vero — camera ferma a 18 cm da terra, l'ottica passa da 22 a 44 mm in 4 fotogrammi mentre la mira scende
  dalla pancia ai piedi, piccolo rimbalzo; le dita dei piedi davanti si muovono (rotazioni relative sul controllo delle dita, sfasate).
- **S05** (24 f): la testa gira lentissima (16 fotogrammi) fino a guardare in macchina; la camera è messa dove arriva lo sguardo e si avvicina.
- **S06** (24 f): galoppo a 2,5× sul posto con terra e polvere che volano dietro; al 13 parte di colpo verso la camera e le passa accanto
  (col mosso è uno strappo), e dove stava resta la **sagoma di polvere** (la posa del fotogramma 12 cotta in polvere) che si sfalda piano.

## Atto 2 animato (fatto il 24 nov) — S08–S13b
I 7 s fra il guado dell'Onon e il Burkhan Khaldun, in EEVEE (1080×1920, 64 campioni, mosso), modo calmo. Montati con S14 (che c'era
già) in `trailer/blender/shot/atto2.mp4` = 9 s, l'atto intero; ogni shot ha il suo `.blend` e la sua cartella in `trailer/blender/shot/`.
- Si rifà con `tools/trailer3d/shot-atto2.py -- trailer/blender/shot prova|finale [S08 …]`, e `… monta` per il solo montaggio.
- **S08** (36 f): la cassa del gioco scoppia nelle sue sei pareti (il mesh diviso per facce) più trucioli e polvere; la sciabola esce
  girando come una ruota, sale e ricade **esattamente nella presa** al 22 (`Afferra`); poi la alza (`Sciabola_Alta`) e gira la testa a
  guardarla. Camera sopra la spalla destra, che segue il cavallo.
- **S09a–d** (4 × 12 f, televendita su fondo sfocato): il lampo a stella che scorre sul filo della sciabola e scintilla sulla punta;
  la mazza che gira e si ferma di colpo («tac»); la frusta che schiocca con stella, onda d'urto e corona di polvere sul nodo; l'arco
  con la **corda rifatta** (quella del modello pendeva dritta: tolta) tirata fino allo scocco, poi la freccia parte e la camera le va dietro.
- **S10** (12 f): tele dall'alto, i tre predoni in fila escono dalla polvere (arancio, azzurro, verde smorzati, di fronte al sole).
- **S11** (36 f): il predone arriva di traverso, abbassa la testa (`Attack_Headbutt`) contro il fendente; **rallentatore** dal 10 al 20
  (scintille e polvere sospese), poi si irrigidisce (`Idle`) e **si ribalta tutto d'un pezzo** sul fianco, con le zampe dritte; la
  camera frena, scivola di lato e resta su di lui mentre il cavallo esce dal quadro.
- **S13a** (12 f): il rotolo rotola incontro al cavallo, lampo, ed è **avvolto nel pluriball** (il pony del gioco, sul rig vivo), con
  bolle che volano via.
- **S13b** (24 f): la mazza di un predone fuori quadro colpisce il fianco al 6; le **bolle vere scoppiano a catena** dall'urto
  (si gonfiano, scoppiano con uno sbuffo bianco, dietro resta la plastica sgonfia e più scura); il cavallo gira e abbassa la testa
  a guardarsi, con un cenno soddisfatto. Come è fatto: `tools/trailer3d/avvolto.py` (vedi `LEGGIMI.md`).
- **Da giudicare guardandolo:** se le bolle a catena si leggono a misura di telefono, il lampo di S13a (una palla bianca per due
  fotogrammi), quanto dura il rallentatore di S11, se in S10 il terzo predone sparisce troppo nella polvere.

## Atto 3 animato (fatto il 24 nov) — S15, S16, S18, S19, S20
I 3,5 s di montaggio a raffica, in EEVEE (1080×1920, 64 campioni, mosso; **S18 e S20 in Cycles**), modo calmo: ~10 minuti di render con la pozza di S20 in Cycles (era 4 minuti e 15 secondi tutto in EEVEE).
`trailer/blender/shot/atto3.mp4` = 3,5 s, 84 fotogrammi; ogni shot ha il suo `.blend` e la sua cartella in `trailer/blender/shot/`.
- Si rifà con `tools/trailer3d/shot-atto3.py -- trailer/blender/shot prova|finale [S15 …]`, e `… monta` per il solo montaggio.
- **Profilo (S15, S16, S18, S19, 12 f l'uno):** il cavallo galoppa in avanti a 0,17 m a fotogramma e la camera è attaccata a lui, di profilo da
  6,5 m: sta fermo nello stesso punto del quadro e col **fotogramma 2 di `Gallop` in tutti** (la ripetizione è la gag), il mondo scorre.
- **S15** Piana del Tuul (ger che passa). **S16** dune: il lama sulla cresta **gira la testa di ~60°** verso di lui mentre passa. **S18**
  Khar Balgas al tramonto, il disco del sole sull'orizzonte e l'aquila che attraversa il cielo in alto battendo le ali. **S19** Erdene
  Zuu nell'ora blu: stupa e lanterne che tremolano (esposizione alzata, il cavallo era un'ombra nera).
- **S20** (36 f, dal 24 nov in Cycles, con la luna nel quadro e riflessa, pozza a specchio e pista bagnata: vedi «Cielo e acqua»): Karakorum di notte. Quattro tonfi a 5, 13, 21 e 28, ognuno più forte: due cerchi per tonfo nascono al centro della pozza
  e si allargano, 18 sassi saltano, le luci della città sussultano, la camera trema. Il cavallo cammina verso di noi, rallenta, si ferma al 23
  (passo senza pattinare) e gira la testa. La musica si spegne qui: l'audio non c'è ancora.
- **Cambiato rispetto all'animatic:** S20 ha la camera più vicina (38 mm, il cavallo era troppo piccolo) e le luci della città sono DIETRO di
  lui, perché la camera guarda indietro lungo la pista (nell'animatic non si vedevano). Non c'è polvere dei piedi negli shot di giorno (vedi `LEGGIMI.md`).
- **Da giudicare guardandolo:** se la posa uguale a ogni taglio fa ridere o stanca in 3 s, se il lama si nota in mezzo secondo, se il
  cavallo di S20 che gira la testa (ora piccolo, ~35% dell'altezza del quadro) si legge senza il suono.

## Atto 4 e coda animati (fatto il 23 nov) — S21–S28
I 9 s del Boss e i 3 s della coda, in EEVEE (1080×1920, mosso; **24 campioni** e non 64, per un errore del modo calmo trovato il 24 nov), girati in **modo calmo** (vedi `tools/trailer3d/LEGGIMI.md`):
tutto in 6 minuti e mezzo, con la CPU intorno al 40%.
- `trailer/blender/shot/atto4.mp4` (9,0 s: S21–S27, col fermo di mezzo secondo sul salto) e `coda.mp4` (3,0 s: fermo, 1,5 s di nero
  per i titoli, la birra); ogni shot ha il suo `.blend` e la sua cartella in `trailer/blender/shot/`.
- Si rifà con `tools/trailer3d/shot-atto4.py -- trailer/blender/shot prova|finale [S21 …]`, e `… monta` per il solo montaggio.
- **S21** la schiena avanza contro la luna, la camera trema a ogni passo (un passo per battito). **S22** la camera scorre sotto il
  ventre appena più piano del Boss; la gamba destra del terzo spicchio è fuori passo di mezzo ciclo e al 24–32 fa un saltello e rientra.
  **S23** la testa si gira verso di noi, la mascella si spalanca, il fiato esce dalla bocca (dal 24 nov è un volume procedurale, `fumo.py`: prima erano dischi emissivi, troppo finti). **S24** il Boss si impenna a trampolo mentre il
  cavallino alza la sciabola; la punta della lama fa una scintilla (che splende senza illuminare). **S25** la carica al tele, la distanza
  si chiude a meno di due metri. **S26** affondo e morso a vuoto (al 4), poi la tosse (all'11, anche lei col fumo di `fumo.py`). **S27** il salto al rallentatore (la clip
  da 6 a 14 in 24 fotogrammi) con la camera che gira di 30°; all'ultimo fotogramma guarda in macchina (misurato). **Dal 24 nov la luna è enorme** (raggio 19°, il 80% della larghezza del quadro), con mari e crateri, e sta sempre dietro al cavallo, che resta inscritto nel disco (`tools/trailer3d/luna.py`); obiettivo 23 mm, luce di riempimento solo sul cavallo. **S28** la birra
  attraversa il nero con le sue luci addosso.
- **Da giudicare guardandolo:** la gamba fuori passo di S22 (si nota abbastanza?), la tosse di S26, quanto dura il fermo del salto.

## Montaggio dei 30 s (fatto il 24 nov) — `trailer/blender/trailer-30s-muto.mp4`
I cinque spezzoni già montati uniti in un video solo: `atto1.mp4` (5,5 s) + `atto2.mp4` (9 s, con S14) + `atto3.mp4` (3,5 s) + `atto4.mp4` (9 s,
col fermo di mezzo secondo sul salto) + `coda.mp4` (3 s: fermo, 1,5 s di nero per i titoli, la birra). **1080×1920, 24 fps, 720 fotogrammi =
30,000 s**, H.264 crf 14, 27 MB, **muto**. I tagli cadono sui tempi della tabella (verificato estraendo un fotogramma per shot). Si rifà con:
`ffmpeg -i shot/atto1.mp4 -i shot/atto2.mp4 -i shot/atto3.mp4 -i shot/atto4.mp4 -i shot/coda.mp4 -filter_complex "[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[o]" -map "[o]" -c:v libx264 -crf 14 -pix_fmt yuv420p -r 24 trailer-30s-muto.mp4`
(da `trailer/blender/`). Ogni spezzone si rifà col suo script (`shot-atto1…4.py … monta`), poi si riunisce. Ancora da fare: **musica** (a 120 BPM, un
battito = 12 fotogrammi; i punti dove si ferma sono S04, S14 e S20), **grading**, titoli nel nero della coda, e rigirare a 64 campioni gli shot
dell'atto 4 che sono a 24 (S21, S22, S24, S25, S27).

## Musica a 165 BPM, bozza (fatta il 24 nov) — `trailer/blender/musica/` e `trailer/blender/trailer-30s-musica.mp4`
La griglia musicale della tabella (120 BPM) è sostituita da **165 BPM** (scelta dell'utente): 1 s = 2,75 battiti, 4 s = 11 battiti esatti. Le tre frasi ripartono
su un taglio (**downbeat a 5,5 s, 14,5 s e 23,5 s**), così tutti i tagli cadono su una semicroma o a un fotogramma dal battito (vedi `CUE.md`; fuori griglia solo
i tonfi del Boss, ogni 0,5 s, di proposito). **È una bozza sintetizzata per sentire i tempi**, non la musica finale: i suoni veri si rifanno in Ableton con la guida MIDI.
- `trailer-30s-musica.mp4` (30,000 s, audio AAC 256k, -13,3 LUFS, picco -1,5 dBFS); `musica/trailer-30s-musica-bozza.wav`, `musica/stem/` (5 stem), `musica/guida-165bpm.mid`
  (tempo 165, click, una nota a ogni taglio, marcatori con gli shot), `musica/CUE.md` (la tabella dei tagli con lo scarto dalla griglia e cosa fa la musica).
- Cosa succede: cori in Re minore (S03) → **STOP** a 2,0 (disco che gratta) → silenzio fino a 4,5 → gambe a vuoto e la musica riparte a 5,0 → frase 1 a mezzo tempo (colpi su cassa che scoppia,
  sciabola, mazza, frusta, arco, bolle a catena) → **STOP** a 12,5 e quasi silenzio con i soli rumori della birra → frase 2 (cassa su ogni battito, uno stab per taglio, la nota scende ad ogni
  tappa) → S20 la musica rallenta e si spegne mentre la terra batte quattro tonfi → orrore (bordone e un tonfo ogni mezzo secondo), ruggito, colpo d'orchestra → frase 3 (la carica) →
  **SNAP** del morso a 24,625 e la tosse → il salto coi cori → STOP sul fermo → nero muto da 27,5 a 29,0 → la birra: pattini e un tintinnio.
- **Da decidere/giudicare:** tutto, a orecchio (non l'ho potuta ascoltare); in particolare se il groove a mezzo tempo regge a 165, se i colpi sui tagli si sentono sopra la
  batteria, se il ruggito e i cori suonano da trailer o da giocattolo.

## Grading (fatto il 24 nov) — `trailer/blender/trailer-30s-graduato.mp4`
Un look unico sopra rendering nati da luci molto diverse, con ffmpeg (`tools/trailer3d/grading.py`, spiegazione in `LEGGIMI.md`): **alba** calda con alone sul sole, **giorno** più
contrastato e saturo (il kit dava un velo lattiginoso), **tramonto** arancio, **ora blu** schiarita, **notte** schiarita con la gamma, meno satura e con le ombre sul ciano (luna con alone),
la **birra** sul nero, e il **nero della coda resta nero**. Su tutto vignetta leggera e un filo di grana. 1080×1920, 24 fps, 30,000 s, con l'audio della bozza a 165 BPM (-13,3 LUFS), 49 MB.
Il confronto prima/dopo di ogni shot si rifà con `python3 tools/trailer3d/grading.py prova <cartella>`. **Da giudicare a occhio:** se il giorno è troppo verde/saturo (l'erba), se la notte resta grigia
o va bene, se la grana si vede sul telefono.

## Cielo e acqua (fatto il 24 nov) — per la richiesta «più dettagli al paesaggio, al riflesso nell'acqua, ai cerchi»
- **Cielo con cumuli** (tappe 1–10, `animatic.strato_nuvole` + `kit.NUV`): sostituisce le carte di nuvole (foto del gioco, macchie grigie); bordi chiari verso il sole, pance scure, rosa al tramonto. Vedi `LEGGIMI.md`. Rigirati atto 2 (S08–S14) e atto 3 (S15–S19).
- **S20, la pozza vera:** Cycles; specchio (cavallo, stelle, luci, luna), cerchi come onde in rilievo (il riflesso ondeggia) con un alone sottile, pista bagnata con le strisce delle luci della città, **luna nel quadro a destra del cavallo e riflessa**. ~10 minuti l'atto 3 intero.
- **La luna ha mari e crateri in tutti gli shot notturni** (`luna.py`, come S27), quindi **S21, S22, S24, S25 sono stati rigirati a 64 campioni** (l'errore dei 24 campioni dell'atto 4 è chiuso: S23, S26 erano già a 64, S27 pure). L'atto 4 intero: ~9 minuti.
- **Non fatto, da decidere:** nebbiolina bassa sulla pozza, cerchietti dove ricadono i sassi, alberi veri 3D (servirebbe scaricare i modelli CC0 di Poly Haven: da chiedere), foschia a strati, primo piano con cespugli e fiori negli shot di profilo, cavalli nemici più dettagliati (S10/S11: 2.182 triangoli contro i 29.799 del protagonista; consiglio: generare un modello e trasferire i pesi dello scheletro Quaternius, come per il pony).
- **Da giudicare guardandolo:** se i cumuli di giorno bastano (sono ancora sobri) o li vuoi più grandi, se l'acqua di S20 non sia troppo «da spot», se la luna a destra del cavallo in S20 funziona.

## Nemici di cartone (fatto il 24 nov) — S10 e S11
Su richiesta («proviamo a usare lui come nemico») i predoni low poly a quattro zampe di S10 e S11 sono sostituiti da **un uomo con la testa di cavallo di cartone e la tunica a strisce**
(`assets/models/predone-cartone-tavola.glb`, scaricato dall'utente; è una tavola a quattro viste con quattro figure in posa a T nello stesso mesh, 9.428 triangoli e una texture 4096²: se ne usa
una, 2.346 triangoli). Sta nell'universo del protagonista (che è un uomo in costume da cavallo di cartone). Lo scheletro, i pesi e le clip sono in `tools/trailer3d/cartone.py` (vedi `LEGGIMI.md`).
- **S10:** tre corridori uguali in fila, tinta moltiplicata (arancio, azzurro, verde smorzati), alti 1,9 m (`ALT_NEMICO`), con la corsa agganciata alla velocità (senza pattinare).
- **S11:** corre di traverso, si china e dà la testata: l'affondo è scelto perché il **muso arrivi esattamente alla punta della lama** (1,10 m dal suolo); poi `Idle` lo irrigidisce e cade di lato come una tavola.
- **Interruttore:** `NEMICO=cavallo` rimette i predoni di prima (`shot-atto2.py`), `ALT_NEMICO=2.1` cambia l'altezza.
- **Deciso (24 nov, dall'utente): «Tienili»** — i nemici di cartone restano al posto dei cavalli in S10 e S11; il trailer di 30 s è rimontato e rigraduato con loro.
- **Ritocchi fatti (24 nov, dopo «Sì, ritocca»):** la tinta ora colora **solo il cartone** (maschera nello shader da R e R-G della texture: la pelle resta com'è), e in S11 una luce frontale sulla camera (`RIEMP_RIVALE`, 12) con light linking illumina solo il rivale, che era controluce e scuro. Con 30 il rivale diventa bianco, con 2,4 non cambia nulla.
- **Ancora così:** le strisce della tunica non ondeggiano da sole; il rivale blu resta grigio-azzurro (blu × cartone caldo).
- **Non fatto:** le strisce della tunica non ondeggiano da sole (seguono solo le ossa), la corsa è procedurale e senza peso nelle mani, un solo modello per tutti i nemici.

## Come lavoriamo (proposta)
1. ~~**Animatic**~~ — fatto, vedi sopra. 2. ~~**Kit di set**~~ — fatto, vedi sopra. 2b. ~~**Animatic v2**~~ — fatto, vedi sopra.
3. ~~**Rig e pose**~~ — fatto, vedi sopra (animatic v3, ancora sui tempi e nel formato della v1).
3b. ~~**Animatic verticale**~~ — fatto, vedi sopra.
3c. ~~**Primo shot animato (S14)**~~ — fatto, vedi sopra: è il modello per gli altri.
3d. ~~**Atto 1 animato (S03–S06)**~~ — fatto, vedi sopra.
3e. ~~**Atto 4 e coda (S21–S28)**~~ — fatto, vedi sopra.
3f. ~~**Atto 2 (S08–S13b)**~~ — fatto, vedi sopra.
3g. ~~**Atto 3 (S15–S20)**~~ — fatto, vedi sopra. **Tutti gli shot sono animati** e il montaggio dei 30 s c'è (3h, sotto): restano la musica, il grading e i titoli.
4. Shot per shot, uno script per shot (`tools/trailer3d/`), un `.blend` salvato per ognuno così lo si apre e lo si ritocca in Blender.
3h. ~~**Montaggio dei 30 s, muto**~~ — fatto, vedi sopra.
3i. ~~**Musica a 165 BPM, bozza sintetizzata**~~ — fatta, vedi sopra.
3j. ~~**Grading**~~ — fatto, vedi sopra.
5. Musica vera (Ableton), titoli.

## Domande aperte
Le cinque domande della v1 hanno avuto risposta il 23 nov (vedi «Decisioni» in cima). Restano da decidere più avanti: la musica (originale o di
repertorio) e i titoli nel nero di S28.
