# Trailer in Blender — storyboard v1 (bozza da discutere)

Niente titoli, niente cartelli, niente HUD: solo immagini. Dove un giorno andranno i titoli c'è uno spazio libero (S28).

## L'idea in una riga

**Un mito epico, serissimo, il cui eroe è un cavallo di cartone con le gambe di un uomo.** La steppa, l'alba, il branco
di cavalli veri che passa in controluce — e in cima al dosso, fermo, lui. Poi il viaggio da un'alba a una notte
(le 12 tappe del gioco, dal Kherlen a Karakorum), le armi, i predoni, il pluriball che scoppia, la birra sui pattini,
e alla fine il Boss: un coccodrillo-scalinata nero che cammina su 14 gambe umane.

Il trucco del tono: **la regia non ammicca mai.** Ottiche lunghe, controluce, slow-motion, polvere dorata, come in un
film storico; il cartone, le gambe nude e il bicchiere coi pattini sono già abbastanza buffi da soli. «Figo» è la
macchina da presa, «carino» sono i dettagli che nel gioco, dietro il cavallo e con la camera lontana, non si vedono.

## Formato e griglia (assunzioni mie, tutte cambiabili)

| | |
|---|---|
| Versione principale | **60 s**, 2,39:1 (2560×1072), 24 fps |
| Versione verticale | **30 s**, 9:16 (1080×1920) per storie IG — stessi shot, camera riposizionata, non un ritaglio |
| Griglia musicale | **120 BPM**: 1 battito = 0,5 s = 12 fotogrammi, 1 battuta = 2 s = 48 fotogrammi. Ogni taglio cade su un battito, ogni atto su una battuta |
| Musica / suoni | non ancora: lo storyboard dice solo dove cadono i colpi |

Le due versioni condividono lo stesso girato: ogni shot ha una durata nei 60 s e una (più corta, o «—» se salta) nei 30 s.

## I quattro atti e la luce

La luce è la spina dorsale: **un solo giorno che passa in 60 secondi**, dall'alba al buio. I valori sono quelli veri del gioco
(`LUCE_TAPPE` in `horse-racing-3d.html`), quindi la steppa di Blender ha lo stesso cielo del gioco.

| Atto | Tempo (60 s) | Tappa del gioco | Sole (elev. / colore) | Nebbia | Umore |
|---|---|---|---|---|---|
| 1 · Alba | 0:00–0:12 | Fiume Kherlen | 4° · `#ffb27a` | `#e9c3a6` | calma, solitudine, controluce |
| 2 · Cavalcata e lotta | 0:12–0:34 | Guado dell'Onon → Burkhan Khaldun | 14°–28° · `#ffd9ae` → `#fff1d6` | `#dfe0dc` → `#cfdde6` | energia, mattina limpida |
| 3 · Il viaggio | 0:34–0:44 | Tuul 58° → Dune 38° → Cascate 19° → Khar Balgas 3° → Erdene Zuu −2° → Karakorum −5° | `#ffffff` → … → `#9aa8ff` | fino a `#2e3858` | il sole scende a ogni taglio |
| 4 · Il Boss | 0:44–0:58 | Karakorum (notte) | luna, `#9aa8ff` | `#2e3858` | freddo, minaccia, poi scontro |
| Coda | 0:58–1:00 | — | — | — | respiro, spazio per i titoli |

## Tabella dei tempi

| Shot | Inizio 60 s | Dur. 60 s | Inizio 30 s | Dur. 30 s | Titolo |
|---|---|---|---|---|---|
| S01 | 0:00 | 3 | 0:00 | 1 | Alba sul Kherlen |
| S02 | 0:03 | 2 | — | — | Il branco |
| S03 | 0:05 | 3 | 0:01 | 1,5 | Il cavallo sul dosso |
| S04 | 0:08 | 2 | 0:02,5 | 0,5 | I piedi |
| S05 | 0:10 | 2 | 0:03 | 1 | Muso e redini |
| S06 | 0:12 | 1,5 | 0:04 | 1 | La partenza |
| S07 | 0:13,5 | 2 | 0:05 | 1 | Galoppo sulla strada |
| S08 | 0:15,5 | 2 | 0:06 | 1 | La cassa |
| S09 | 0:17,5 | 4 | 0:07 | 2 | Quattro armi |
| S10 | 0:21,5 | 3 | 0:09 | 1 | I predoni |
| S11 | 0:24,5 | 3 | 0:10 | 1,5 | Il duello |
| S12 | 0:27,5 | 2 | — | — | Schivata e frusta |
| S13 | 0:29,5 | 3 | 0:11,5 | 1,5 | Il pluriball |
| S14 | 0:32,5 | 1,5 | 0:13 | 1 | La Birra Grande |
| S15 | 0:34 | 1,5 | 0:14 | 0,5 | Piana del Tuul |
| S16 | 0:35,5 | 1,5 | 0:14,5 | 0,5 | Dune di Elsen Tasarkhai |
| S17 | 0:37 | 1,5 | — | — | Cascate di Ulaan Tsutgalan |
| S18 | 0:38,5 | 1,5 | 0:15 | 1 | Khar Balgas e l'aquila |
| S19 | 0:40 | 2 | 0:16 | 1,5 | Erdene Zuu |
| S20 | 0:42 | 2 | 0:17,5 | 1,5 | Karakorum, la terra trema |
| S21 | 0:44 | 2 | 0:19 | 1,5 | La schiena a gradini |
| S22 | 0:46 | 2 | 0:20,5 | 1,5 | Sotto il ventre |
| S23 | 0:48 | 2 | 0:22 | 1,5 | La testa e la mascella |
| S24 | 0:50 | 1,5 | 0:23,5 | 1 | Il cavallo e la sciabola |
| S25 | 0:51,5 | 2 | 0:24,5 | 1,5 | La carica |
| S26 | 0:53,5 | 2 | 0:26 | 1 | Il morso |
| S27 | 0:55,5 | 2,5 | 0:27 | 1 | Il salto |
| S28 | 0:58 | 2 | 0:28 | 2 | Coda |

Totali: 60,0 s e 30,0 s (atti: 12 / 22 / 10 / 14 / 2 e 4 / 10 / 5 / 9 / 2). Tutte le durate sono multipli di mezzo secondo.
Per tagliare ancora, si toglie prima S17 (la più cara da costruire), poi S12 e S02.

---

## ATTO 1 · ALBA (0:00–0:12)

Nessun colpo di musica: vento, un drone, zoccoli lontani. Chi guarda deve credere a un film serio per quattro secondi.

### S01 · Alba sul Kherlen — 3 s (30 s: 1)
- **Camera:** gru alta, 24 mm, discesa lentissima verso il fiume. Sole a 4° dietro l'acqua, controluce.
- **Azione:** il fiume serpeggia nella nebbia bassa; sulla riva, minuscole, due pecore e una mucca ferme.
- **Modelli:** kit terreno (vedi sotto) + `animali/pecora.glb`, `animali/mucca.glb` (clip Idle).
- **Blender:** cielo Nishita con i valori di Kherlen, nebbia come volume basso, riflesso del sole sul fiume.

### S02 · Il branco — 2 s (30 s: —)
- **Camera:** tele 200 mm, panning parallelo alla corsa, bassa profondità di campo, polvere dorata in controluce.
- **Azione:** 8–10 cavalli veri al galoppo che attraversano il quadro. Il pan finisce su uno spazio vuoto.
- **Modelli:** `horse-quaternius.glb`, clip `Gallop` (14 fotogrammi, ciclo veloce) con fase diversa per ogni cavallo; tinte naturali, non le pastello dei predoni.
- **Blender:** istanze con offset di animazione; polvere = particelle o volume a piccole sfere.

### S03 · Il cavallo sul dosso — 3 s (30 s: 1,5)
- **Camera:** spinta lenta da dietro la spalla, 50 mm, all'altezza degli occhi. Resta controluce: prima si vede solo una sagoma, poi i bordi illuminati rivelano il **cartone**.
- **Azione:** il branco si allontana in fondo. Lui resta fermo in cima al dosso, il vento muove la criniera di spago e la coda. È l'unico che non è partito: questo è il «gancio» emotivo.
- **Modelli:** `protagonista-cartone.glb` clip `Idle` (72 fotogrammi); in Blender meglio il rig Rigify di `protagonista-cartone.blend`.
- **Blender:** vento sulla criniera e sulla coda con rumore sulle ossa; luce di bordo (rim) dal sole.

### S04 · I piedi — 2 s (30 s: 0,5)
- **Camera:** macro a 10 cm da terra, 35 mm, inclinazione dal basso verso l'alto: erba bagnata di rugiada → piedi nudi → jeans → cartone.
- **Azione:** un piede si sposta e cerca l'appoggio. **Si scopre che dentro c'è un uomo.** È il primo sorriso del trailer.
- **Modelli:** protagonista, clip `Idle`.
- **Blender:** erba istanziata (geometry nodes) con rugiada; contatto piede-terreno.

### S05 · Muso e redini — 2 s (30 s: 1)
- **Camera:** primissimo piano, 85 mm a f/1.8. Fuoco sul muso di cartone (si vedono le toppe di nastro adesivo), poi rack focus sulla manica blu che **stringe le redini**.
- **Azione:** un orecchio si muove. La mano si chiude su un battito: **lì si taglia.**
- **Modelli:** protagonista (braccio destro: l'unico braccio visibile).
- **Blender:** profondità di campo vera, pochi riflessi; la texture del cartone è già buona per il macro.

## ATTO 2 · CAVALCATA E LOTTA (0:12–0:34)

Entra la musica: ostinato e percussioni. Un colpo per ogni evento che si vede (stile `mappa.py` del trailer d'azione).

### S06 · La partenza — 1,5 s (30 s: 1)
- **Camera:** a terra davanti ai piedi, 24 mm. Rallentatore al 20% che fa rampa al 100% sul terzo battito.
- **Azione:** i piedi nudi affondano e sparano via erba e polvere; il cavallo parte e supera la camera (whoosh).
- **Modelli:** protagonista, `Gallop` (40 fotogrammi) con rampa di velocità.
- **Blender:** zolle e fili d'erba come particelle/istanze; motion blur forte.

### S07 · Galoppo sulla strada — 2 s (30 s: 1)
- **Camera:** carrellata laterale parallela, 35 mm a 1,2 m da terra. Rampa di velocità 1× → 0,5× → 1×.
- **Azione:** il cavallo di cartone sulla strada (la stessa strada del gioco) in mezzo alla steppa, ombra lunghissima, zoccoli che alzano polvere.
- **Modelli:** protagonista `Gallop`; kit terreno con la strada (`textures/Asphalt014`).
- **Luce:** Guado dell'Onon, sole 14°.

### S08 · La cassa — 2 s (30 s: 1)
- **Camera:** prima la cassa in primo piano sulla strada (1 m, angolari di metallo, corde, alone luminoso come in gioco); poi, a collisione, la camera sta sulla spalla del cavallo.
- **Azione:** il cavallo la prende. Esplode in pezzi di cartone; dentro, la sciabola in rotazione; la manica blu l'afferra.
- **Modelli:** `armi/cassa.glb`, `armi/saber.glb`, protagonista.
- **Blender:** la cassa va divisa in pannelli (6 facce + corda) e fatta esplodere con rigid body.

### S09 · Quattro armi — 4 s (30 s: 2) — quattro inserti da 1 s (0,5 s nei 30 s)
Un'arma per battito, sul nero o sullo sfondo sfocato della steppa. Macro con luce radente: il metallo e il cuoio devono sembrare veri.
- **a · Sciabola:** macro sul filo, un lampo scorre lungo la lama; taglio d'aria.
- **b · Mazza:** spuntoni in rotazione al rallentatore, il gancio che oscilla.
- **c · Frusta:** lo schiocco con onda d'urto e corona di polvere.
- **d · Arco:** la corda si tende, rilascio, **camera sulla freccia** per l'ultima parte del secondo.
- **Modelli:** `armi/saber.glb`, `mace.glb`, `whip.glb`, `bow.glb`, `freccia.glb`.
- **Blender:** per i macro conviene usare gli originali ad alta risoluzione (ancora in `~/Downloads`); quelli del gioco sono a 1024 px. La corda dell'arco va rifatta (Tripo la rovina: nel gioco è procedurale).

### S10 · I predoni — 3 s (30 s: 1)
- **Camera:** elicottero laterale, 28 mm. Da dietro una collinetta emergono tre cavalli che affiancano il nostro nella polvere; poi mezzo primo piano.
- **Azione:** i rivali (un'arma di firma ciascuno: mazza, sciabola, frusta); il nostro gira appena la testa.
- **Modelli:** `horse-quaternius.glb` con le tinte del gioco (arancio, azzurro, verde, rosa), clip `Gallop`.
- **Attenzione:** da vicino i predoni sembrano cavalli-giocattolo; restano a media distanza e nella polvere, oppure si decide di scurirli (domanda aperta).

### S11 · Il duello — 3 s (30 s: 1,5)
- **Camera:** bullet-time. Orbita di 180° attorno al punto d'impatto a tempo ×0,05, poi rientro a velocità piena nell'ultimo battito.
- **Azione:** testata del rivale (`Attack_Headbutt`), la sciabola lo incontra: lampo, scintille, polvere ferma in aria, fili d'erba sospesi; il rivale cade (`Death`).
- **Modelli:** protagonista (colpo di sciabola in posa), `horse-quaternius.glb`.
- **Blender:** il protagonista **non ha clip d'attacco**: il braccio destro va posato a mano sul rig Rigify. Camera su curva circolare e tempo rimappato su un canale di animazione.

### S12 · Schivata e frusta — 2 s (30 s: —)
- **Camera:** whip-pan da un rivale all'altro, 35 mm.
- **Azione:** un calcio del rivale (`Attack_Kick`) sfiora il cartone; il nostro si scansa; lo schiocco della frusta lo spazza via.
- **Modelli:** `horse-quaternius.glb` (`Attack_Kick`, `Idle_HitReact_Left/Right`), protagonista.

### S13 · Il pluriball — 3 s (30 s: 1,5)
- **1,0 s:** il rotolo gira sulla strada; il cavallo lo raccoglie e **si avvolge di pluriball** (stacco con lampo, dal cartone alla versione avvolta).
- **2,0 s:** macro 100 mm: la mazza di un predone colpisce; le bolle scoppiano **a catena**, un'onda che parte dal punto d'urto, a velocità 10%. Il cartone sotto non si tocca.
- **Modelli:** `pluriball/rotolo.glb`, `pluriball/pony-skin.glb` (solo il busto: le gambe sono quelle del protagonista), `armi/mace.glb`.
- **Blender:** nel macro servono bolle vere: un livello di geometria istanziata sul busto, con la scala che va a zero in ritardo secondo la distanza dall'impatto.

### S14 · La Birra Grande — 1,5 s (30 s: 1)
- **Camera:** bassa, fissa, 35 mm, a bordo strada. Whip-pan.
- **Azione:** un bicchiere di birra sui pattini in linea sfreccia in zigzag da destra a sinistra; il cavallo di cartone passa, **gira la testa** (doppia presa) e via.
- **Musica:** un battito di silenzio sul bicchiere — è la battuta del trailer.
- **Modelli:** `birra/birra.glb` (tre pezzi rigidi: Bicchiere, PattinoS, PattinoD; il passo si fa a mano con i keyframe).

## ATTO 3 · IL VIAGGIO (0:34–0:44)

Un taglio ogni 1,5 s, il sole più basso a ogni taglio: si **sente** il giorno che passa. Stessa strada, stesso cavallo, un solo set rilanciato con luci diverse.

### S15 · Piana del Tuul — 1,5 s (30 s: 0,5)
- **Camera:** carrellata laterale, 35 mm. Mezzogiorno, sole a 58°, luce dura, ombra sotto i piedi, erba a perdita d'occhio, cielo blu profondo.

### S16 · Dune di Elsen Tasarkhai — 1,5 s (30 s: 0,5)
- **Camera:** 50 mm da dietro le dune. Sole 38°, aria torbida (turbidità 14), sabbia che soffia, distorsione da calore.
- **Cameo:** un **lama** (`animali/lama.glb`, Idle) sulla cresta guarda passare il cavallo senza battere ciglio.

### S17 · Cascate di Ulaan Tsutgalan — 1,5 s (30 s: —)
- **Camera:** aerea che segue il cavallo sul bordo della gola. Sole 19°.
- **Azione:** il fiume rosso che precipita; spruzzo nell'aria.
- **Nota:** è lo shot più costoso (acqua + gola). **Se serve, si taglia questo per primo.**

### S18 · Khar Balgas e l'aquila — 1,5 s (30 s: 1)
- **Camera:** parte dall'aquila (`animali/aquila.glb`, `Flying`) in primo piano, la segue e scende in gru sulle mura in rovina dove passa il cavallo. Tramonto, sole a 3°, rosso.

### S19 · Erdene Zuu — 2 s (30 s: 1,5)
- **Camera:** carrellata lenta laterale. Ora blu, sole −2°, nebbia `#7f84a8`. Le **108 stupa** in fila con le lanterne accese; il cavallo passa in mezzo, il cartone preso dalla luce calda mentre il resto del mondo è blu.
- **Nota:** le stupa non esistono ancora: si modellano a codice (profilo a rivoluzione, bianche).

### S20 · Karakorum, la terra trema — 2 s (30 s: 1,5)
- **Camera:** 35 mm bassa. Notte, stelle, luna, le luci della capitale lontane; il cavallo avanza al passo (`Walk`, 96 fotogrammi).
- **Azione:** **in una pozza si formano cerchi concentrici.** I sassi saltano, le luci tremano, la polvere sale: qualcosa di grosso cammina. Taglio sul battito del primo passo.
- **Blender:** cerchi con uno shader/displacement animato; stelle e luna nel cielo.

## ATTO 4 · IL BOSS (0:44–0:58)

Qui il montaggio cambia: tagli più lunghi, camera quasi ferma, il peso lo danno le **battute dei passi** a tempo con la musica.

### S21 · La schiena a gradini — 2 s (30 s: 1,5)
- **Camera:** fissa, bassa, 50 mm. Contro la luna piena, oltre la cresta, **sale la schiena del coccodrillo**: blocchi neri a scalinata con gli spigoli bianchi (il logo). Il corpo scorre da sinistra a destra, lungo 16 m, lentissimo.
- **Modelli:** `boss/coccodrillo.glb` (39 pezzi rigidi: `Coda0–2`, `Coscia_S0–S4_D/S`, `Coscia_T0…`, ecc.).
- **Blender:** nessuno scheletro: va animato a keyframe pezzo per pezzo (il gioco lo fa a codice, `3d/boss.js`).

### S22 · Sotto il ventre — 2 s (30 s: 1,5)
- **Camera:** a 30 cm da terra, 20 mm, carrellata lunga dentro le **14 gambe umane in jeans** che marciano all'unisono. Un tonfo a ogni battito, la camera trema appena.
- **Effetto:** orrore e comico insieme: è il momento più «nostro» del trailer.

### S23 · La testa e la mascella — 2 s (30 s: 1,5)
- **Camera:** 85 mm sul testone-logo che gira verso di noi. La **mascella si apre**: taglio rosso scuro, denti, lingua, un filo di vapore; la luna dietro.
- **Modelli:** `boss/testa-bocca.blend` (cranio + mascella, già divisi) e `testa-60k.blend` per il macro.

### S24 · Il cavallo e la sciabola — 1,5 s (30 s: 1)
- **Camera:** contro-campo, il cavallo di cartone piccolo al centro del quadro, vento nella criniera; l'ombra del Boss lo ricopre.
- **Azione:** la manica blu stringe le redini, la sciabola si alza e **la lama prende la luna**.

### S25 · La carica — 2 s (30 s: 1,5)
- **Camera:** tele 135 mm, compresso. I due si lanciano uno contro l'altro sulla strada, la distanza si chiude e la polvere sale.

### S26 · Il morso — 2 s (30 s: 1)
- **Camera:** whip-pan. La mascella scatta **sulla polvere**: il cavallo non c'è già più.

### S27 · Il salto — 2,5 s (30 s: 1)
- **Camera:** orbita lenta di 90° attorno al cavallo in volo, bullet-time, luna alle spalle.
- **Azione:** il cavallo di cartone sopra la schiena a gradini, sciabola alta, polvere sospesa. **Fermo immagine** sull'ultimo battito.
- **Blender:** il protagonista non ha clip di salto: la posa a mezz'aria si fa a mano sul rig.

### S28 · Coda — 2 s (30 s: 2)
- 1 s sull'immagine ferma del salto, poi nero e silenzio. **Spazio libero per i titoli** (non inserirne ora).
- Idea facoltativa «dopo i titoli»: 0,5 s in cui il bicchiere sui pattini attraversa il quadro nero. Da decidere.

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
Un fotogramma per shot coi modelli veri, in EEVEE a bassa qualità, montato muto sui tempi di sopra (S09 ha 4 fotogrammi, S13 ne ha 2: 31 in tutto).
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

## Come lavoriamo (proposta)
1. ~~**Animatic**~~ — fatto, vedi sopra. 2. ~~**Kit di set**~~ — fatto, vedi sopra. 2b. ~~**Animatic v2**~~ — fatto, vedi sopra.
3. ~~**Rig e pose**~~ — fatto, vedi sopra (animatic v3).
4. Shot per shot, uno script per shot (`tools/trailer3d/`), un `.blend` salvato per ognuno così lo si apre e lo si ritocca in Blender.
5. Montaggio, musica, grading.

## Domande aperte
1. **Formato:** 60 s in cinemascope + 30 s verticale va bene, o ne vuoi uno solo?
2. **Tono:** serio-epico che non ammicca (come sopra) o più apertamente comico?
3. **Predoni:** restano giocattolo-pastello (a media distanza) o li scuriamo con colori da guerra?
4. **Il finale facoltativo** del bicchiere sui pattini dopo il nero: sì o no?
5. **Gameplay vero:** zero secondi (come hai detto) oppure uno stacco finale di 1–2 s col gioco, per non promettere più del gioco?
