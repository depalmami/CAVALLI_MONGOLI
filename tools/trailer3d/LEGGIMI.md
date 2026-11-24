# tools/trailer3d — il trailer in Blender

Tutto si lancia con Blender **senza interfaccia** (`/opt/homebrew/bin/blender -b --python … -- argomenti`, versione 5.1.2): l'addon MCP di Blender non serve.

| File | A cosa serve |
|---|---|
| `animatic.py` | Libreria di base (importa i GLB cuocendo la posa, cielo, camera, oggetti di scena) + **un fotogramma per shot** dell'animatic: `-- <cartella> [S03 S11 … \| tutti]` |
| `monta-animatic.py` | Monta i fotogrammi sui tempi dello storyboard (ffmpeg + Pillow): `animatic-60s.mp4`, `animatic-30s-ritmo.mp4`, foglio contatti |
| `kit.py` | **Il kit di set**: il mondo del gioco per le macchine da presa (vedi sotto) |
| `animatic2.py` | **Animatic v2**: gli stessi shot di `animatic.py` girati nei set del kit (Cycles per S01–S05 e S18): `-- <cartella> [S17 … \| tutti]` |
| `foglio-kit.py` | Foglio con le 12 tappe e le loro etichette (Pillow) |
| `animatic-verticale.py` | **Animatic verticale** (storyboard v2: 30 s, 9:16, comico): un fotogramma per shot a 720×1280: `-- <cartella> [S14 … \| tutti]` |
| `monta-verticale.py` | Monta l'animatic verticale sui tempi v2 (ffmpeg + Pillow), con le gag scritte e zoom a scatto, fermo immagine, birra nel nero |
| `shot.py` | **Attrezzi comuni agli shot animati**: curve di tempo, camera a chiavi, sbuffi di polvere a chiavi, apparire/sparire, render, video, salvataggio del `.blend` |
| `shot-atto1.py` | **Atto 1 animato** (S03–S06, Cycles): `-- <cartella base> prova\|finale [S03 …]`, salva `trailer/blender/shot/S0x.blend` |
| `shot-atto2.py` | **Atto 2 animato** (S08–S13b, EEVEE): `-- <cartella base> prova\|finale [S08 … \| monta]`, monta `atto2.mp4` (con S14) |
| `avvolto.py` | **Il cavallo avvolto nel pluriball** sul rig vivo (il pony del gioco legato al rig del trailer) e le **bolle vere** che scoppiano a catena |
| `fumo.py` | **Fumo vero** dalla bocca del Boss: volume procedurale in EEVEE (getto con rumore 4D, si piega col calore), con una luce che illumina solo lui. `soffio(origine, direzione, f_on, f_off, n, …)` |
| `shot-atto3.py` | **Atto 3 animato** (S15, S16, S18, S19, S20: il viaggio, 3,5 s): `-- <cartella base> prova\|finale [S15 … S20 \| monta]`, monta `atto3.mp4`. Profilo con camera attaccata al cavallo, lama che gira la testa, aquila, pozza coi cerchi nello shader |
| `musica165.py` | **La musica del trailer, bozza a 165 BPM** (Re minore, tutta sintetizzata con numpy, col python di Blender: niente da scaricare): master, stem, guida MIDI per Ableton, cue sheet, e il video con l'audio |
| `grading.py` | **Grading del trailer** con ffmpeg: un look per gruppo di shot (alba, giorno, tramonto, ora blu, notte, birra), alone sulle luci, vignetta e grana leggere. `prova <cartella>` = foglio prima/dopo, `video` = `trailer-30s-graduato.mp4` |
| `cartone.py` | **Il predone di cartone** (24 nov): l'uomo con la testa di cavallo di cartone di `assets/models/predone-cartone-tavola.glb` (una tavola a 4 viste: se ne estrae una figura), con scheletro a 17 ossa, pesi dalla distanza d'osso e clip `Gallop` (corsa con IK dei piedi, senza pattinare), `Idle` (rigido) e `Attack_Headbutt` (affondo, con la quota del muso scelta per bisezione). `predone_cartone(colore, altezza, nome, z_colpo=…)` → (radice, rig, clip) come `predone_vivo`. Scheda di prova: `blender -b --python tools/trailer3d/cartone.py -- <cartella>` |
| `luna.py` | **Luna grande con dettagli** (mari e crateri nello shader), sempre dietro al cavallo lungo la retta camera→cavallo: usata in S27 perché il cavallo resti «inscritto» nel disco |
| `shot-atto4.py` | **Atto 4 animato + coda** (S21–S28, EEVEE): `-- <cartella base> prova\|finale [S21 … \| monta]`, monta `atto4.mp4` e `coda.mp4` |
| `shot-s14.py` | **S14 animato** (2 s, 1080×1920): scena a chiavi col rig vivo, salva `trailer/blender/shot/S14.blend`: `-- <cartella> prova\|finale` |
| `rig.py` | **Rig del trailer**: dal `.blend` del gioco (non toccato) a `trailer/blender/rig/protagonista-trailer.blend` col braccio e le clip nuove: `blender -b assets/models/protagonista-cartone.blend --python tools/trailer3d/rig.py -- trailer/blender/rig/protagonista-trailer.blend [foglio.jpg]` |
| `pose.py` | **Le pose negli shot**: `eroe()` (dal rig del trailer, con l'arma nella presa), `boss()` (passo, mascella, testa), `birra()` (spinta dei pattini) |

## kit.py in breve

```python
import sys; sys.path.insert(0, 'tools/trailer3d'); import kit
from animatic import nuovo, camera, scatta

nuovo()                                             # scena vuota (EEVEE)
m = kit.Mondo(tappa=3, curva=0.7, colline=1.0)      # tracciato + terreno + pista della tappa 3 (Piana del Tuul)
kit.luce(m, az=250)                                 # cielo, sole (o luna) e nebbia di quella tappa; az = dove sta il sole (da +X, antiorario)
kit.veste(m)                                        # alberi, erba vicina, nuvole, montagne e i pezzi che riconoscono la tappa
kit.eroe_su(m, s=0, lat=0, azione='Gallop')         # il protagonista sulla strada, orientato come la strada
kit.cam_su(m, 8, -5, 1.3, -3, 0, 1.35, 35)          # camera in coordinate di strada: (s, lat, quota) → (s, lat, quota), focale
scatta('/percorso/frame.jpg')
```

- **Coordinate di strada:** `s` = metri lungo la strada (verso crescente = verso di marcia), `lat` = metri a destra della mezzeria (come nel gioco, `lat +` = destra).
  `m.punto(s, lat)` dà un punto sul terreno, `m.tr.yaw(s)` l'orientamento di un modello che segue la strada. Strada dritta: si va verso -Y.
- **Pezzi** (metodi di `Mondo`): `vegetazione()`, `erba_vicino(s, lat, raggio, densita)`, `nuvole()`, `montagne()`, `acqua()`, `gregge()`, `rovine()`, `stupe()`, `luci_citta()`, `pozza()`; funzioni `ger()`, `masso()`, `muro()`.
- **Da riga di comando:** `-- <cartella> griglia` (le 12 tappe), `beauty` (alba, tramonto, notte a 2560×1072), `tempi` (misura EEVEE e Cycles e salva `kit-alba.blend`), `<0-11>` (una tappa).
- **La nebbia** è una dissolvenza per distanza nei materiali (il volume del mondo in EEVEE senza interfaccia dà nero): vale per i materiali del kit, non per quelli dei GLB.
## Render calmo (per non cuocere il MacBook)

Dal 23 nov gli shot animati (`shot.py`) girano di norma in **modo calmo**:
- **Cycles solo sulla GPU.** Prima accendevo anche la CPU accanto alla GPU: misurato su S04, la CPU stava a ~1110% e il fotogramma
  durava 17 s; solo GPU la CPU sta a ~35% e il fotogramma dura 13 s (più veloce: la CPU rubava solo calore).
- **Al massimo 4 fili di CPU** (`FILI`) per il resto del lavoro.
- **Una pausa dopo ogni fotogramma** lunga metà del fotogramma (`RIPOSO=0.5`, oppure `PAUSA=6` secondi fissi): la GPU lavora due
  terzi del tempo e riposa un terzo. Il render dura ~1,5 volte tanto.
- `CALMO=0` torna a pieno regime; `TRATTO=10-13` gira solo quei fotogrammi (prove), e stampa secondi e CPU di ogni fotogramma.
- **Campioni EEVEE:** 64 in `finale`, 16 in `prova`. Fino al 24 nov, per un errore, il modo calmo non li impostava e restavano 24:
  l'atto 4 e la coda (girati il 23 nov) sono a 24 campioni.
- **Il resto lo decide il Mac:** con «Prestazioni elevate» (Impostazioni → Batteria → Modalità energetica) il chip spinge al massimo;
  in «Automatica» o «Risparmio energetico» scalda molto meno. Durante i render conviene non tenerlo sulle ginocchia e non in carica al 100%.

## pose.py in breve

```python
import pose
r, info = pose.eroe(pos, yaw, corpo=('Gallop', 14), braccio=('Sciabola_Fendente', 11), sguardo=('Sguardo_D', 9), arma='saber')
info['punta']                                        # la punta dell'arma nel mondo: lì vanno scintille e lampi
pose.boss(pos, yaw, 1.35, fase=0.25, passo=1.2, mascella=30, testa=-20, alza=5)   # fase 0..1 = un ciclo del passo
pose.birra(pos, yaw, 2.0, fase=0.25, forza=1.7, piega=7)                          # fase 0..1 = una spinta per lato
```
- Le clip del protagonista: corpo `Gallop` `Walk` `Idle` `Salto`; braccio `Sciabola_Fendente` `Sciabola_Alta` `Frusta` `Afferra`; sguardo `Sguardo_D` `Sguardo_S`
  (fotogrammi chiave nello storyboard, sezione «Rig e pose»). Per l'animazione vera: la stessa NLA del `.blend` del trailer, oppure `pose.*` fotogramma per fotogramma.
- **Per gli shot animati:** `pose.eroe_vivo()` (rig vivo appeso a una radice da chiavare) + `pose.traccia(rig, azione, 'REPLACE'|'COMBINE')`
  (striscia NLA con `strip_time` e `influence` chiavabili: così una clip rallenta, si blocca o si somma a metà); `pose.birra_crea()` +
  `pose.birra_posa(..., chiave=f)` per chiavare la spinta dei pattini. Esempio completo: `shot-s14.py`.
- Il braccio NON esiste nel GLB del gioco: le pose d'attacco ci sono solo nel `.blend` del trailer. Se si rigenera il rig (`rig.py`), il `.blend` del trailer si riscrive.
- **Trappole:** `nuovo()` cancella tutto, quindi va chiamato PRIMA di `Mondo(...)`; i modelli guardano -Y (il coccodrillo +X); EEVEE con sole sotto i 10° ha luce piatta (per alba e tramonto usare Cycles).

## avvolto.py in breve (S13a, S13b)

```python
radice, rig, az = pose.eroe_vivo('eroe')            # con la radice ancora nell'origine…
pony = avvolto.avvolgi(rig, az)                      # …e PRIMA di mettere le clip nell'NLA
avvolto.mostra(pony, rig, 7)                         # dal 7 è avvolto (prima: il protagonista normale)
i, urto = avvolto.punto_riposo(pony, (-0.3, -0.15, 0.92), lato=(-1, 0, 0))   # un punto del fianco destro, nel riposo del rig
fronte = avvolto.bolle(pony, urto)                   # bolle vere attorno all'urto
fronte(f, 0.12)                                      # chiava il fronte: tutte le bolle entro 12 cm (± disordine) sono scoppiate
```
- Il pony è il mesh di `assets/models/pluriball/pony.blend` (generato dalla posa salvata del protagonista = `Gallop` al fotogramma 1),
  sovrapposto e pesato come in `tools/pluriball/pony_skin.py`, poi riportato nel riposo del rig (skinning inverso) e legato con un
  modificatore Armatura: segue tutte le clip. Le gambe sono quelle vere (una Maschera `solo_gambe` sul corpo, accesa da `mostra`).
- Le bolle sono Geometry Nodes dopo l'Armatura; la distanza dall'urto si misura sull'attributo `riposo` (la posizione nel riposo),
  così il fronte non trema col galoppo. Dietro il fronte anche il materiale del pony si sgonfia (più scuro e opaco).
- Anche il pony è figlio del rig: per trovare il corpo del protagonista fra i figli del rig, cercare quello con la Maschera `solo_gambe`.

## fumo.py in breve (fiato di S23, tosse di S26)
- `soffio()` crea una scatola di volume che segue la bocca a chiavi; il materiale calcola la densità da coordinate d'oggetto: cono che
  si allarga, curvatura verso l'alto, fronte che rallenta e coda che lo insegue, rumore 4D (distorsione 0,9) che scorre lungo il getto.
  Il tempo è un `Value` con un driver `frame/24`. La bocca per il Boss: `bocca_fumo(r, f_dir)` in `shot-atto4.py`.
- **Non usare Mantaflow per questo (provato il 24 nov, Blender 5.1 `-b`):** il bake ignora le animazioni dell'emettitore (posizione, scala,
  visibilità, `use_inflow`): la sorgente resta dove stava al fotogramma 1. Con `use_noise` acceso il volume resta vuoto se il rumore non è
  cotto, e `velocity_coord` si aggiunge solo al moto della sorgente. Il volume procedurale non ha niente da cuocere.
- **Di notte il fumo preso dalla sola luna è invisibile** (prima si usavano sfere emissive, che brillano): serve una luce che lo illumina
  (`luce_del_fumo`, light linking con `receiver_collection`: il resto della scena non cambia). Di controluce, 2–3 W/m².
- EEVEE: `volumetric_tile_size` 4 a 1080×1920 (con 2 le celle sono troppe), ombre del volume spente. ~5 s a fotogramma, CPU 15–20%.

## shot-atto3.py in breve (S15–S20)
- **Profilo con camera attaccata:** `profilo()` fa galoppare il cavallo in avanti a 0,17 m a fotogramma (il passo che non pattina) e la camera
  lo segue rigida a 6,5 m: sta fermo nel quadro e il mondo scorre. La clip `Gallop` parte da T0=2 in TUTTI gli shot (la gag è la ripetizione).
  Il passo (`Walk`, ciclo di 24 fotogrammi) non pattina a 0,034 m a fotogramma (misurato sulla punta del piede in appoggio).
- **Animali vivi:** `animale_vivo()` tiene lo scheletro (lama: ossa `Neck`, `Head`; aquila: clip `Flying` 1–30). La testa del lama gira con
  un'azione attiva in COMBINE sulle ossa, attorno alla verticale del mondo convertita nello spazio dell'osso.
- **Cerchi nella pozza nello shader** (`materiale_pozza`): con tori scalati la riga si ingrossava insieme al raggio; con l'anello calcolato
  sulle coordinate d'oggetto (e un driver sul fotogramma) resta sottile.
- **Provato e scartato: polvere dei piedi come volume** (`fumo.py`) negli shot di giorno: con l'esposizione bassa del sole il volume
  viene scuro (marrone) e la scatola lascia un bordo dritto. Gli shot di profilo non hanno polvere; se servisse, ci vorrebbe una lampada
  solo-volume forte (10+ W/m²) e una scatola più grande della nuvola.
- **Luci della città in S20:** la camera guarda indietro lungo la pista, quindi le luci stanno DIETRO il cavallo (s = −190), non davanti
  come nel gioco; di fianco si perdono, perciò sono sfere grandi (0,6–1,3 m) a un orizzonte basso.

## musica165.py in breve
- Si lancia così (python di Blender, che ha numpy; il python di sistema no, e scipy non c'è da nessuna parte):
  `/Applications/Blender.app/Contents/Resources/5.1/python/bin/python3.13 -I tools/trailer3d/musica165.py trailer/blender/musica`
  Fa in pochi secondi: `trailer-30s-musica-bozza.wav`, `stem/` (batteria, basso, musica, effetti, riverbero), `guida-165bpm.mid`, `CUE.md`, e se
  c'è `trailer/blender/trailer-30s-muto.mp4` anche `trailer/blender/trailer-30s-musica.mp4`. Il volume è un guadagno statico fino a -12 LUFS (picco ≤ -1,5 dBTP: viene -13,3).
- **Perché 165 BPM torna con un montaggio pensato a 120:** 1 s = 2,75 battiti e 4 s = 11 battiti esatti, quindi se ogni frase ricomincia su un taglio
  (downbeat a 5,5 s, 14,5 s e 23,5 s) tutti gli altri tagli cadono su una semicroma o a un fotogramma da un battito (tabella in `CUE.md`).
  Le cadute dei suoni sui tagli sono al tempo ESATTO, non sulla griglia. I tonfi di S21–S22 (uno ogni 0,5 s) sono volutamente fuori dal groove: lì c'è solo orrore, niente ritmo.
- **Filtri senza scipy:** `fft_filter` (risposta di Butterworth applicata in frequenza, a fase zero) per i filtri fissi, `stft` (finestre di Hann al 75%)
  per quelli che si muovono (riser, ruggito, whoosh). Il riverbero è una convoluzione con una risposta sintetica.
- **Gli STOP (S04, S14, fermo di S27) e lo spegnimento di S20** si fanno SULLA somma già mixata (`POST`, dopo sidechain e abbassamenti): il suono
  rallenta fino a fermarsi (lettura a velocità decrescente) e i bus tonali tacciono. Sotto ogni colpo sul taglio la musica si abbassa un attimo (`HIT_T`).
- Non l'ho ascoltata: l'ho controllata con livelli (RMS a 250 ms, silenzi di S05/S14/nero), spettrogramma e picchi sui punti di sincronia.

## grading.py in breve
- **Misurato prima di correggere** (un fotogramma per shot): il giorno era lattiginoso (nero più scuro a 0,4–0,5, saturazione 30–40 su 255), la notte buia (media 40/255, blu saturo 140–180), l'alba già bella. Quindi: giorno con punto di nero forte e più saturazione (×1,38), notte schiarita con la GAMMA (1,55) e meno satura (0,92) con ombre sul ciano, alba solo con un tocco di contrasto e il caldo sulle luci. S15 e S16 (cavallo in controluce, scuro) hanno un giorno più morbido (`profilo`).
- **Trappola della vignetta di ffmpeg:** l'angolo PIÙ GRANDE scurisce di PIÙ (il default PI/5 = 0,63 rad porta gli angoli a ~1/8 della luce del centro: troppo). Qui 0,32–0,36 (−17% negli angoli).
- **Il nero della coda resta nero** (segmento senza curve, né grana: Y = 16 in range limitato). La grana è temporale e incomprimibile: con grana 3–4 e crf 14 il file veniva 273 MB; con grana 2–3 e crf 17 sono 49 MB.
- L'alone è `split` + curva che tiene solo le luci forti + `gblur` (sigma 28 a 1080 px) + `blend screen`: fa brillare sole e luna. Il grading lavora sul `trailer-30s-muto.mp4` e prende l'audio da `trailer-30s-musica.mp4`: se si rifà la musica, rifare prima quello.

## luna.py in breve (S27, 24 nov)
- Richiesta dell'utente: nel salto davanti alla luna (S27 e il fermo) la luna deve essere grande, con qualche dettaglio, e il cavallo «inscritto» nel disco dietro di lui.
  `luna_grande(cam, centro, n, raggio=19, su=1, forza=0.62)`: sfera emissiva a 700 m, raggio angolare 19° (il quadro verticale a 23 mm è largo ~47°, il disco ne copre l'80%),
  chiavata ogni fotogramma sulla retta camera → centro del cavallo (la mesh valutata) e con una Track To sulla camera (mostra sempre la stessa faccia mentre la camera gira di 30°).
  Mari = rumore a macchie, crateri = Voronoi a tre scale (buco scuro + bordo chiaro), bordo del disco più scuro. Obiettivo 23 mm (era 26) perché il cavallo abbia aria intorno.
- **Trappole:** (1) la luce di riempimento frontale (sole attaccato alla camera, i raggi vanno verso l'alto) NON illuminava il cavallo: il Boss sotto proiettava l'ombra su di lui → `use_shadow = False`.
  (2) Lasciata libera illumina anche il Boss e appiattisce la notte → light linking solo sul cavallo. (3) La luna emissiva a forza 3,4 era un disco bianco: 0,62 mostra i mari. (4) Il grading della notte (gamma 1,55) la
  bruciava di nuovo: S27 e il fermo hanno un gruppo a parte, `lunapiena` (gamma 1,12, luci rientrate, alone più piccolo). Parametri di prova da ambiente: `LUNA_R`, `LUNA_SU`, `LUNA_F`, `LUNA_RI`, `LUNA_L`.

## Cielo con cumuli e acqua vera (24 nov)
- **Cumuli nel mondo** (`animatic.strato_nuvole`, attivati per tappa da `kit.NUV`): un rumore frattale proiettato su un piano alto, con l'ombra finta cercata VERSO IL SOLE
  (dove tra il punto e il sole c'è più nuvola, il punto è in ombra: bordi chiari, pance scure) e sfumato verso l'orizzonte. Ora sono solo un nodo del mondo, quindi valgono in EEVEE e in Cycles.
  **Trappola:** i colori assoluti non andavano (la radianza del cielo Nishita cambia di ordini di grandezza da una tappa all'altra: le nuvole venivano più SCURE del cielo). Il colore
  si misura sul cielo: luminosità del cielo in quella direzione × (1,05 in ombra … 2,2 al sole), tinta di ombra o di sole. All'alba (tappa 0) restano le vecchie carte di nuvole.
- **Pozza di S20 in Cycles** (`shot-atto3.py`, `materiale_pozza`): speculare (IOR 1,33, rugosità 0,03) che riflette cielo, luna, luci e cavallo; ogni anello è anche un pacchetto d'onde
  in rilievo (nodo Bump: la normale cambia, il riflesso ondeggia) più un alone sottile. `strada_bagnata`: un nastro sopra la pista, trasparente dove è asciutto e speculare dove è bagnato
  (rumore a macchie), per le strisce verticali delle luci della città. La luna è nel quadro, a destra del cavallo e riflessa nell'acqua (`luna_rel=163`, `luna_el=17`).
  Tempi: ~1,8 s a fotogramma in prova (540×960, 12 campioni, GPU); in finale molto di più (vedi STORYBOARD).
- **La luna ha sempre i dettagli** (mari e crateri di `luna.py`, forza 1,5) anche nei disco piccolo degli altri shot notturni: `animatic.notte` usa `materiale_luna`.
- Non fatti (consigliati, da chiedere): nebbiolina bassa sulla pozza (si può fare col volume procedurale di `fumo.py`), cerchietti dove ricadono i sassi.

