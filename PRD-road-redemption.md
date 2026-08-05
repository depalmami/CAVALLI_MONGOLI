# PRD / Handoff — Cavalli Mongoli 3D → combat-racing stile **Road Redemption**

> Documento per riprendere il lavoro in una **nuova conversazione**. Contiene: visione,
> stato attuale del codice, cosa è FATTO, cosa MANCA (con i passi esatti di wiring),
> architettura, comandi, setup di test. Riferimento: **Road Redemption** (erede di
> Road Rash — corse di combattimento), **NON** Red Dead Redemption.

## 1. Visione
Trasformare il prototipo 3D `horse-racing-3d.html` (motore pseudo-3D OutRun portato a
Three.js) in un **combat-racing roguelike**: guerrieri mongoli a cavallo che si combattono
mentre corrono. Meccaniche di riferimento: attacco sx/dx, calcio per buttare fuori,
takedown → soldi/XP/nitro, boost, armi raccolte in pista, tipi evento (gara/razzia/
sopravvivenza/tempo), **una vita** (permadeath) con shop tra gli eventi (soldi = buff
del run, XP = upgrade permanenti).

## 2. File e contesto
- **Unico file di gioco**: `horse-racing-3d.html` (branch `3d-experiment`). Three.js 0.160
  via importmap CDN. ~1500+ righe, tutto inline.
- Gioco 2D originale (da cui è nata la parte "live show"): `horse-racing.html`.
- **Asset** (committati): `assets/models/horse-quaternius.glb` (cavallo CC0 animato),
  `assets/textures/Asphalt014` + `Grass004` (PBR CC0 ambientCG).
- Memory del progetto: `~/.claude/.../memory/esperimento-3d.md`,
  `road-redemption-direction.md`, `verifica-browser-headless.md`.

## 3. Stato del codice — sistemi GIÀ presenti (funzionanti)
Rendering/feel (fasi precedenti, tutte verificate):
- Cielo atmosferico `Sky`, ombre morbide PCFSoft che seguono il giocatore, tone mapping
  ACESFilmic, materiali PBR, **bloom** (EffectComposer→RenderPass→UnrealBloomPass→OutputPass),
  FOV dinamico con la velocità, golden-hour, alberi abete a 2 chiome, polvere sotto gli
  zoccoli, paletti rosso/bianco a bordo pista, fondale erboso world-locked (statico 1.5M).
- **Movimento fluido**: loop fixed-timestep (1/120) con interpolazione (`interpWrap`).
- **Cavallo** Quaternius con **locomozione realistica**: andature idle/walk/gallop miscelate
  per velocità (`HorseActor.update`), passi sincronizzati al suolo, inclinazione in curva,
  imbardata in sterzata, beccheggio. Loader pronto per modello utente in
  `assets/models/horse-custom.glb` (`MODEL_SOURCES[0]`, gestione scala via bbox delle OSSA).
- **SHOW LIVE** (portato dal 2D): overlay canvas 2D `live` — flash strobo + scritta gigante
  lampeggiante (8 palette halo/gradiente/contorno, rimbalzo sync-BPM, cambio colore), e
  versione **scritta 3D** (`text3d`, TextGeometry estruso + glow bloom). Guidati dal tap tempo
  del modulo `party` (`party.onBeat`, `party.periodNow`, `party.bpmNow`).
- **party**: tap tempo (T) → BPM; distorsione comica alberi + luce a tempo (P), slider intensità.

## 4. Road Redemption — piano a 4 fasi e STATO
- **Fase 1 — Combattimento**: ✅ FATTA e verificata (1 takedown nel test, danni reciproci).
- **Fase 2 — Nitro & boost**: ✅ FATTA (nitro da colpi/paletti; boost Shift 200→226 km/h; alone blu).
- **Fase 3 — Armi mongole**: ✅ FATTA (pickup casse luminose, equip, durabilità ×N; frusta/mazza/sciabola/arco).
- **Fase 4 — Eventi + roguelike**: ✅ FATTA — modulo agganciato al loop e verificata headless
  (2026-07-19): briefing→VIA→obiettivo HUD→vittoria→shop→evento 2→game over→nuova corsa con XP mantenuto.

### 4.1 Combattimento (Fase 1) — architettura implementata
Blocco `// COMBATTIMENTO stile Road Redemption` (subito dopo `keySlower`):
- Stato giocatore: `pHealth, nitro, money, score, kills, blocking, critical, boosting,
  pAtkCd, shake, dmgFlash, strengthMul, curWeapon, popups[]`. `MAX_HEALTH/MAX_NITRO` (let).
- Rivali: `RIVAL_DEFS` + `opponents[]` con `{actor,name,skill,pos,lat,targetLat,spd0,speed,
  health,hp0,state('race'|'wipe'),wipeT,atkCd,laneCd,flash}`.
- `gapTo(oppPos)` = distanza segnata lungo pista (+ = davanti). `addPopup(who,off,text,color)`.
- `playerAttack(side)` (J=-1, L=+1): trova rivale affiancato sul lato, danno = arma×critico×forza;
  gestisce reach/ranged(arco)/durabilità/stun. `playerKick()` (K): spinge il rivale verso
  l'esterno; se esce di pista o hp≤0 → `wipe`. `hitOpponent`, `wipe` (ricompense + `onKill`).
- `updateAI(dt)`: **rubber-band forte** `target = speed - g*0.7 + skill…` (tiene il branco
  affiancato al giocatore = combattimento continuo — vedi §8 gotcha), cambio corsia, contrattacco
  (se `blocking` → `critical`, altrimenti danno + `dmgFlash`; a hp≤0 → `onPlayerDown`).
- Hook: `let onKill = ()=>{}` e `let onPlayerDown = ()=>{pHealth=MAX_HEALTH}` (riscritti dalla Fase 4).
- HUD combattimento: pannello DOM `#hud-combat` (barre `#bar-health`/`#bar-nitro`, `#stat-kills/score/money/weapon`,
  `#combat-obj`) + canvas `combatHud` (z-index 5) che **proietta** barre-vita nemici + popup +
  vignetta danno/boost. Camera shake nel loop.

### 4.2 Nitro/armi (Fasi 2-3)
- Nitro: +4 per colpo, +25 per takedown, trickle sfiorando i paletti (`|playerX|∈[1.03,1.32]`).
  Boost in `updatePhysics`: `boosting = keys['shift'] && nitro>0`, cap `MAX_SPEED*1.35`, drena nitro.
- `WEAPONS{fists,whip,mace,saber,bow}` + `equipWeapon(key)`. `pickups[]` + `updatePickups(dt)`
  (casse `BoxGeometry` emissive che ruotano/ondeggiano; raccolta se vicino). Chiamato nel loop.

### 4.3 Meta/roguelike (Fase 4) — **modulo GIÀ scritto**, blocco `// META / ROGUELIKE` prima del LOOP
Definiti: `game{state,eventIndex,dist,target,type,need,time,timeLeft,xp,up{strength,health,nitro},
killsThisEvent}`, `showScreen/hideScreen` (overlay `#screen`/`#screen-box`), `applyUpgrades`,
`eventFor(i)` (race/takedown/survival/time, difficoltà crescente), `respawnRivals(i)`,
`startEvent`, `objectiveText`, `checkGame` (win/lose + aggiorna `#combat-obj`), `winEvent`→
`renderShop` (shop: cura/nitro/sciabola con $, +forza/+salute/+nitro con XP; bottoni con
`disabled` sui saldi; `b-next`→prossimo evento), `loseEvent`→game over, `resetRun`, `showBriefing`.
Hook riscritti: `onKill = ()=>{game.killsThisEvent++}`, `onPlayerDown = ()=>loseEvent(...)`.
Overlay HTML `#screen` + CSS già aggiunti.

## 5. ✅ Wiring Fase 4 — COMPLETATO (2026-07-19)
Le 4 micro-modifiche sotto sono state applicate e verificate (test end-to-end §7, 10/10 PASS).
In più: `window.cm3d = { game }` esposto come handle di debug/test headless.
Nota di design confermata: il bottone "VIA! →" dello shop (`#b-next`) lancia **direttamente**
l'evento successivo (il briefing del prossimo evento è già mostrato dentro lo shop).

1. **Accumulo distanza/tempo** — in `updatePhysics`, subito dopo `position += speed * dt;`:
   ```js
   game.dist += speed * dt;
   if (game.type === 'time') game.timeLeft -= dt;
   ```
2. **Gating del loop** — nel `function frame(now)`, sostituire il blocco
   `acc += frameDt; while (acc >= FIXED_DT) { … }` con:
   ```js
   if (game.state === 'racing') {
     acc += frameDt;
     while (acc >= FIXED_DT) { prevPosition=position; prevPlayerX=playerX;
       for (const o of opponents) o.prevPos = o.pos ?? o.prevPos; updatePhysics(FIXED_DT); acc -= FIXED_DT; }
   } else { acc = 0; }
   ```
   e **dopo** lo stepping (una volta per frame) chiamare `checkGame();`
3. **Avvio** — definire `function begin(){ applyUpgrades(); pHealth = MAX_HEALTH; showBriefing(); }`
   e chiamarlo nella `Promise.all([...]).then(...)` di fine caricamento, dove c'è
   `$('loading').remove(); requestAnimationFrame(frame);` → aggiungere `begin();`.
4. **Tasto R** — opzionale: cambiare `if (k === 'r') {…}` in `if (k === 'r') startEvent();`
   (riavvia l'evento corrente pulito).

Poi **testare** (vedi §7): il gioco deve partire su schermata briefing, "VIA!" avvia l'evento,
obiettivo aggiornato in `#combat-obj`, vittoria→shop, morte→game over→nuova corsa (XP mantenuto).

## 6. Comandi
`↑↓/WS` gas/freno · `←→/AD` sterza · `J` attacca sx · `L` attacca dx · `K` calcio · `I` parata ·
`Shift` boost · `C` camera · `B` sprite/modello · `T` tap tempo · `P` alberi · `F` flash ·
`G` scritta · `H` scritta 3D · `R` riparti/riavvia evento.

## 7. Testing (headless, niente estensione Chrome)
- Server: `cd <progetto> && python3 -m http.server 8901 --bind 127.0.0.1` (bind IPv4 obbligatorio su macOS).
- Script puppeteer-core + Chrome di sistema in `…/scratchpad/cm3d-test/` (Chrome path
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`). Pattern: `page.goto`,
  `waitForFunction(!loading)`, `page.keyboard`, leggere HUD via `page.$eval('#stat-…')`,
  screenshot, controllare `pageerror`/console. NB: **un 404 atteso** = sonda `horse-custom.glb`
  (innocuo, filtrarlo). Il node_modules dello scratchpad a volte va reinstallato (`npm i puppeteer-core`).

## 8. Gotcha / lezioni
- **Rubber-band AI**: deve essere FORTE (`target = playerSpeed - gap*0.7`) o i rivali non stanno
  al passo di un giocatore a velocità piena e il combattimento non avviene mai (bug già risolto).
- **Box3 su SkinnedMesh** misura la bind-pose ignorando la scala armatura → scalare dalle OSSA.
- **Bloom**: soglia alta / strength bassa, altrimenti full-white. La luce del party ha tetti.
- Overlay canvas: `pointer-events:none`; `.panel` a z-index 20 così l'HUD resta sopra gli overlay.
- Convenzione coordinate: forward `(sin h,0,cos h)`, destra `(-cos h,0,sin h)`, `curve>0`=destra.

## 9. Stato git
- Tutte le 4 fasi (combat/nitro/armi/roguelike) + SHOW LIVE + scritta 3D sono committate in blocco
  su `3d-experiment` (commit successivo a `1b749e6`). Prossimi lavori: vedi backlog §10.

## 9.1 Bug reali trovati dal primo playtest utente e corretti (2026-07-19, commit `29b69fa`)
Il "funziona" della Fase 4 era solo strutturale (transizioni di schermata); testando la
partita vera sono emersi 3 bug concreti, diagnosticati con `window.cm3d` (handle di debug
esposto a fine file, ora con `opponents/gapTo/playerAttack/camera/...`) via Puppeteer:
- **Gara troppo corta**: `eventFor().dist` era un placeholder (45000) mai ricalibrato sul
  vero `TRACK_LENGTH` (~1.341.000 unità) → l'evento 0 durava ~7s reali (3.36% del giro).
  Fix: `dist = 380000 + i*70000` (evento 0 ora ~30-35s reali).
- **Rivali ammassati sul giocatore**: in `updateAI`, il rivale che si affianca per colpire
  puntava a `targetLat = playerX` — la STESSA posizione laterale del giocatore, non una
  accanto. Risultato: i cavalli si sovrapponevano al modello del giocatore invece di
  affiancarlo, rendendo illeggibili nomi/barre-vita/colpi. Fix: `targetLat = playerX +
  (o.lat>=playerX?1:-1)*0.6` (resta dentro `LAT_RANGE=0.95` per l'hit-check, ma visivamente
  di lato). Residuo minore: due rivali possono ancora scegliere lo stesso lato e sovrapporsi
  un po' tra loro (non col giocatore) — non ancora risolto, vedi backlog.
- **Nessun feedback visivo 3D sul colpo**: solo popup testuale nel groviglio. Aggiunto
  `HorseActor.flashHit()` — impulso emissivo rosso sul modello GLB (o tinta sul billboard
  sprite) agganciato a `hitOpponent`/`playerKick`/contrattacco AI sul giocatore.
Verificato con screenshot headless prima/dopo (scratchpad di sessione) + regressione
Fase 4 (10/10) ancora verde.

## 9.2 Animazioni di combattimento (2026-07-19, commit `e32afc4`)
Su richiesta dell'utente, aggiunto MOVIMENTO reale ai colpi (non solo il flash statico
di §9.1) — il cavallo non ha un cavaliere separato, quindi si lavora sul corpo intero:
- `HorseActor.lunge(dir)`: chi attacca scatta verso il lato colpito (o in avanti per il
  calcio, `dir=0`) e torna, curva `sin(t*π)` su `punch` che decade da 1 a 0.
- `HorseActor.knockback(dir)`: chi viene colpito è respinto lateralmente e torna,
  stessa curva su `knock`. Convenzione segno: `dir` punta SEMPRE da chi colpisce verso
  chi subisce, continuato verso l'esterno (vedi i 3 call-site in `hitOpponent`/
  `playerKick`/contrattacco AI per l'esempio di calcolo `Math.sign(target.lat - attacker.lat)`).
- Nuovo modulo `hitSpark` (accanto a `dust`, stesso pattern a pool di sprite ma a burst
  invece che continuo): scintille colorate nel punto d'impatto — colore dell'arma sui
  fendenti, polveroso sul calcio, rosso sul colpo subito dal giocatore.
Verificato: screenshot headless mostra il rivale colpito chiaramente separato dal
gruppo (non più solo tinto rosso fermo), regressione Fase 4 ancora 10/10.

## 9.3 Il proprio affondo era invisibile: bug di camera-tracking (2026-07-19, commit `4e6054b`)
L'utente ha segnalato "non vedo ancora movimento d'attacco" DOPO §9.2. Causa reale (non
ampiezza insufficiente): la camera `'chase'` (default) in `updateCamera()` legge
`player.group.position` sia per la propria posizione sia per `camera.lookAt(...)` — la
STESSA proprietà su cui `HorseActor.update()` applica l'offset di `punch`/`knock`. La
camera insegue e ri-punta istantaneamente sul giocatore ogni frame, quindi il PROPRIO
affondo veniva quasi del tutto cancellato visivamente (misurato via proiezione a schermo:
~12px su 1280 di spostamento). Il rinculo di un RIVALE restava visibile perché la camera
non lo insegue — ecco perché §9.2 sembrava funzionare negli screenshot (che mostravano
rivali colpiti) ma non "si sentiva" giocando in prima persona.
Fix: `HorseActor.basePos` — copia della posizione "pulita" impostata in `place()` PRIMA
che `update()` aggiunga il wobble di combattimento. `updateCamera()` ora legge
`player.basePos` invece di `player.group.position`. Inoltre: ampiezza affondo/rinculo
più che raddoppiata (260/160 e 380, prima 110/70 e 190) e `player.lunge()` spostato
PRIMA del controllo del bersaglio in `playerAttack`/`playerKick` — prima un colpo a
vuoto (bersaglio fuori range/non allineato) non produceva ALCUN feedback, il che è
comune dati i range di aggancio stretti (`ATK_RANGE`/`LAT_RANGE`).
Verificato con proiezione a schermo via Puppeteer (prima/durante/dopo un attacco) +
screenshot. Regressione Fase 4 ancora 10/10.

## 9.4 Percorso e illuminazione: il terreno diventa un vero heightfield (2026-08-05)
Segnalazione utente: «nel percorso ci sono sezioni in cui i layer strada-erba si
sovrappongono, a volte sembra di essere sotto il piano della terra». Misurando il
tracciato (6705 segmenti) sono emersi **quattro difetti geometrici distinti**, non uno:

| # | Difetto | Misura |
|---|---------|--------|
| 1 | Prato `flatOuter` con bordo esterno inchiodato a `y=0` | la pista sale a **+32871** → muro d'erba a **70°** che tappa il cielo |
| 2 | Fondale piatto infinito a `y=-40` | **73 segmenti** hanno quota < -40 → si correva *letteralmente* sotto terra |
| 3 | Nastro erboso largo 26480 dal centro, raggio di curva minimo **13158** | oltre il raggio il nastro si **ripiega su se stesso**: normali rovesciate, autointersezioni = i "layer sovrapposti" |
| 4 | Il tracciato **passa sopra se stesso** (segmenti 3272/4832: 131 unità in pianta, **4201** di dislivello) | il prato del ramo alto faceva da **soffitto** sopra il ramo basso |

E un quinto, di illuminazione, indipendente e più grave di quanto sembrasse:
la cupola `Sky` è una `BoxGeometry` unitaria scalata ×450000 e **centrata sull'origine**
(±225000), ma la pista arriva a `z=662717`: **per l'80% del tracciato (5354 punti su 6705)
la camera usciva dalla cupola e il cielo diventava nero.** Solo il primo quinto della gara
— dove erano stati presi tutti gli screenshot di sviluppo — è mai stato illuminato bene.

**Soluzione — il terreno non è più un nastro, è una superficie che interpola la strada:**
1. si *timbrano* nella griglia (`CELL=2000`) le quote del corridoio stradale, a `VERGE_DROP=300`
   sotto il piano viabile: la strada sta su un **rilevato**. Dove il tracciato si sovrappone
   vince la quota **più bassa** → il ramo alto diventa un viadotto, non un soffitto (risolve #4);
2. le celle libere si risolvono per **rilassamento (Laplace) su piramide multigrid cascadica**
   (~80 iterazioni sul livello grosso + 26 per livello scendendo): superficie liscia che
   raccorda le quote senza artefatti da "cono di distanza";
3. ondulazione collinare lontano dalla strada, dosata sulla **distanza chamfer** dal corridoio;
4. **clamp finale**: sotto ogni punto strada il terreno è garantito ≤ quota strada − 300.
   È l'invariante che rende *impossibile* il bug "sono sotto il piano della terra".

Sezione trasversale ora formalmente corretta (semilarghezze): asfalto 2000 → cordolo 2480 →
**banchina erbosa in piano fino a 4800** → scarpata fino a 8000. La banchina arriva a 4800
perché `playerX` è limitato a ±2.2 = **4400**: tutto ciò che il giocatore può calpestare deve
stare a quota strada, altrimenti il cavallo (che prende la quota dalla linea d'asse)
galleggerebbe sulla scarpata. 8000 è ben sotto il raggio minimo 13158 → niente ripiegamenti (#3).
La scarpata scende fino a **sotto** la quota minima del terreno attraversato (`BANK_BURY=900`):
il lembo esterno resta sepolto, quindi non può mai aprirsi una fessura fra scarpata e terreno.
Il timbro prosegue oltre il traguardo (come la coda pre-partenza): senza, il franco crollava
da 300 a 55 proprio sul traguardo.

Illuminazione: `sky.position.copy(camera.position)` a ogni frame (il cielo è per definizione
all'infinito); `HemisphereLight` con colore-da-terra verde-cachi `0x6e7a45` invece del bruno
`0x6a5436` (il rimbalzo deve essere di ciò che c'è davvero sotto: prato, non fango); terreno
e scarpate `castShadow` (a 17° di elevazione il rilevato ombreggia davvero la banchina).
Alberi spostati oltre il piede della scarpata e piantati su `groundAt()`, non più sulla quota
della strada.

**Verifiche** (`invariant.js`, `playtest.js`, `perf.js` headless):
- 87178 campioni su tutta la fascia calpestabile → **0 violazioni**, franco minimo 299.7/300;
- playtest di 20 s con sterzate reali → **affondamento massimo nel terreno 0.0**, 0 errori console;
- 120 fps a inizio/salita/culmine/fondo pista, caricamento 1.1 s, 510k triangoli statici.

## 9.5 Tracciato lungo il doppio + modalità libera per il debug (2026-08-05)

**Tracciato: da 6705 a 16035 segmenti** (1.34M → 3.21M unità; giro alla velocità massima
da 112s a 267s). La prima metà resta il livello 1 originale di javascript-racer, invariata;
la seconda è nuova e usa tre sezioni aggiunte: `addSwitchbacks` (tornanti alternati a quota
costante), `addValley` (si scende in conca e si risale), `addPlateau` (salita e lungo tratto
in quota).

Due correzioni necessarie perché l'allungamento non rompesse nulla:
- **`addDownhillToEnd` ora si dimensiona sulla quota da smaltire.** Con lunghezza fissa a 200
  segmenti si arrivava al traguardo da +37000 e la discesa finale diventava una rampa al
  **48%**. Poiché `easeInOut` concentra la pendenza al centro (dove vale ~π/2 volte la media),
  il numero di segmenti si ricava da lì per tenere il picco sotto il 20%. Risultato: pendenza
  massima di tutto il tracciato di nuovo **37.7%**, cioè il punto peggiore già presente nel
  livello originale (segmento 2941) — la pista non è diventata più ripida di com'era.
- **Le casse-arma seguono la lunghezza della pista** invece di essere fisse a 12. La spaziatura
  resta quella tarata sul tracciato corto (~103k unità): altrimenti, dato che gli eventi
  misurano *distanza percorsa* e non giri, ogni evento avrebbe offerto metà delle armi.

**VINCOLO ora documentato nel codice:** mai superare `ROAD.CURVE.MEDIUM`. Con `CURVE_K=0.0038`
una MEDIUM ha raggio 13158; una HARD scenderebbe a 8772, cioè dentro la fascia occupata da
scarpate (8000) e alberi (fino a 11200) → tutto ciò che segue il frame della pista si
ripiegherebbe sull'interno delle curve, riaprendo il bug dei "layer sovrapposti" di §9.4.

**Modalità libera (tasto `N`, o il pulsante 🔧 nell'HUD).** Spegne tutta la parte Road
Redemption — rivali, combattimento, casse-arma, obiettivi d'evento, danni e morte — e lascia
solo la guida, per ispezionare pista/terreno/luci senza interruzioni. Non è una pausa: si
entra subito in pista saltando briefing/shop/game-over. In modalità libera `R` riporta solo
il cavallo al via senza riaccendere l'evento; spegnendola si torna a un briefing pulito con
i rivali di nuovo visibili. Guardie in `updateAI`, `updatePickups`, `checkGame`,
`combatHud.draw`, nel ciclo di rendering dei rivali e sui tasti d'attacco.

**Verifiche** (headless): invariante del terreno su **213421** campioni → **0 violazioni**,
franco minimo 299.9/300 · guida reale con sterzate → affondamento massimo 0.0 · modalità
libera 11/11 asserzioni (rivali spariti, vita mai scesa, obiettivo superato senza che accada
nulla, ritorno al gioco normale intero) · **120 fps** in 6 punti sparsi sui 16035 segmenti,
caricamento 1.26s, 1.2M triangoli statici.

## 9.6 Tre difetti, una causa sola: CURVE_K era troppo grande (2026-08-05)

Segnalazione utente dopo §9.5, con screenshot: «ci sono ancora punti in cui il tracciato
entra nelle colline d'erba e punti in cui addirittura si sovrappone a se stesso. Inoltre
sono presenti alberi in carreggiata».

Sembravano tre problemi indipendenti. Misurando, ne è emerso **uno solo**: il tracciato
si sovrapponeva a se stesso in **20 punti**, con rami che passavano a **22–109 unità** di
distanza in pianta e fino a **11135** di dislivello. Il 51.5% del tracciato aveva un altro
ramo entro 26000 unità. Da lì discendevano tutti e tre i sintomi:

| Sintomo segnalato | Causa reale |
|---|---|
| muri d'erba a bordo strada | il *rilevato* del ramo che passava sopra, a quota diversa |
| «la pista entra nella collina» | lo stesso rilevato, visto da dentro l'abitacolo |
| alberi in carreggiata | piazzati a lato del **proprio** ramo, cadevano sulla strada dell'**altro** |

**Perché si avvitava.** `CURVE_K` converte il valore `curve` dei segmenti in una rotazione
vera. A 0.0038 una curva MEDIUM lunga 600 segmenti ruota di **366°**: più di un giro
completo. Nel motore pseudo-3D originale `curve` era solo un effetto ottico e questo non
si vedeva; integrato in geometria reale, il tracciato diventa un gomitolo.

**Correzione: `CURVE_K` 0.0038 → 0.0020.** Scelto misurando, non a occhio: è il valore più
alto che azzera i conflitti, ed è una soglia netta, non un passaggio al pelo.

| CURVE_K | raggio min | zone di conflitto | distanza min fra rami |
|---|---|---|---|
| 0.0038 (prima) | 13157 | 20 | 20 |
| 0.0024 | 20833 | 13 | 38 |
| 0.0022 | 22727 | 4 | 75 |
| **0.0020** | **25000** | **0** | **35867** |
| 0.0018 | 27777 | 0 | 36632 (griglia terreno +50%) |

`CURVE_K` è puramente geometrico: la fisica (centrifuga, rollio) usa `curve` grezzo, quindi
**la guida non cambia**. L'escursione di direzione resta 359°, quindi le curve restano varie.

Due interventi di rinforzo, perché il layout da solo non è una garanzia:
- **Tetto laterale del terreno.** Entro 20000 dalla strada il terreno non può salire più
  ripido del 30% rispetto alla quota stradale. Il campo chamfer ora propaga anche la *quota
  della strada più vicina* (solo la più vicina: nessuna interferenza fra rami). Senza,
  l'ondulazione da sola piazzava ancora una collina al 51% a ridosso del ciglio.
- **Alberi filtrati sulla distanza reale dalla strada** (`roadDist`, il campo chamfer),
  non sull'offset laterale del proprio segmento: un albero a lato del ramo A non può più
  finire sulla carreggiata del ramo B. ~30 alberi su ~3600 vengono scartati.

Con il raggio minimo salito a 25000, le curve **HARD** sono tornate utilizzabili (raggio
16667, sopra gli 11200 degli alberi): applicate ai tornanti, che con le MEDIUM non erano
più tornanti. Verificato che restano puliti (distanza min fra rami 32965).

**Verifiche** (`tredifetti.js`, headless, misure esatte sul gioco che gira):
- alberi: **0** in carreggiata, **0** sulla banchina, il più vicino a 8502 (piede scarpata 8000);
- muri: **0** punti su 10946 con pendenza laterale >50%; massima ora **30%**, cioè esattamente
  il tetto imposto;
- sovrapposizione: **0** tratti entro 26000 da un altro; distanza minima **32965**;
- invariante del terreno ancora 0 violazioni su 213421 campioni; guida reale affondamento 0.0;
  modalità libera 11/11; **120 fps** in 6 punti, caricamento 1.35s, 1.4M triangoli.

## 9.7 «Sembra un'auto che derapa»: assetto in curva del cavallo (2026-08-05)

Segnalazione utente: sterzando, il cavallo sembra un'auto in derapata, col posteriore
disallineato dal muso. Domanda posta: è colpa del modello low-poly?

**No.** L'orientamento del corpo rispetto alla traiettoria non dipende dai poligoni: un
cavallo fotorealistico avrebbe derapato uguale. E il modello Quaternius ha **50 ossa**, con
spina segmentata (`Torso/Torso2/Torso3`), collo (`Neck1..3`), `Head` e `Tail1..7`:
semplicemente non le stavamo usando.

**Diagnosi misurata** (`assetto.js`: angolo della traiettoria vs imbardata del modello):

| fase | traiettoria | imbardata | deriva | rollio |
|---|---|---|---|---|
| sterzo +0.1s | 18.4° | 10.6° | 7.9° | **0.0°** |
| sterzo +0.5s | 13.4° | 13.9° | -0.5° | **-1.9°** |

La deriva era piccola. Il problema vero è la colonna rollio: **il cavallo imbardava di 18°
restando perfettamente in piedi**, perché `bank` dipendeva solo dalla curvatura della
*strada* e non dalla sterzata del giocatore. Ruotare attorno all'asse verticale senza
inclinarsi è esattamente la firma visiva di un'auto che scivola: un animale (o una moto)
che gira si inclina sempre.

**Correzioni:**
1. **Rollio dalla sterzata** (`BANK_STEER_K = 0.75`), sommato a quello della strada;
   `BANK_MAX` alzato 0.32 → 0.40 (~23°) perché ora i contributi si sommano. Da 0.0° a **-13.5°**.
2. **Deriva azzerata**: `STEER_K` 0.9 → 1.0 (il corpo punta esattamente lungo la velocità) e
   imbardata smorzata ~3× più svelta delle altre grandezze — con la costante lenta il muso
   restava indietro all'ingresso e avanti all'uscita, cioè proprio la derapata. Da 7.9° a **0.7°**.
3. **Il corpo si arcua** (`shapeTurn`): collo/testa verso l'interno, schiena arcuata, coda
   all'esterno. La rotazione è espressa attorno al su del mondo **riportato nello spazio del
   genitore dell'osso**, così non serve sapere come sono orientate le ossa nel rig.
4. **Anche i rivali**: prima non imbardavano affatto, quindi cambiando corsia traslavano di
   lato restando puntati dritti (andatura a granchio).

**Due cose imparate misurando, che a occhio non si vedevano:**
- I primi guadagni di flessione (0.05–0.10) spostavano la testa di **62 unità** su un cavallo
  alto 1300: invisibili, perché il galoppo da solo la muove di centinaia. Serve un confronto
  A/B allo **stesso fotogramma d'animazione** (`piega.js`) per isolare l'effetto. Alzati a
  0.08–0.17 → 105 unità, ~43° di testa a piena curva.
- La coda non va imbardata: misurata, **pende** (componente verticale -0.87 su `Tail1→Tail7`),
  e ruotarla attorno alla verticale la fa girare su se stessa senza spostarla. Va mossa a
  **pendolo attorno all'asse di marcia** → da +25 (verso l'interno, trascinata dal torace) a
  **-159** (verso l'esterno). Nota: la coda orizzontale che si vede è la posa naturale del
  galoppo, verificata con uno scatto in rettilineo.
- `ROAD_TURN_K` tenuto a 0.09: con 0.22 una curva HARD da sola saturava la piega e il cavallo
  teneva la testa girata di 43° per tutta la curva.

**Correzione dell'ampiezza (stessa giornata, dopo playtest utente).** Segnalato che «il collo
si gira in maniera quasi horror», col promemoria di valutare il MODELLO 3D e non lo sprite —
alcuni screenshot precedenti erano in modalità sprite, dove `shapeTurn` non gira nemmeno.
Misurando il quaternione mondiale dell'osso a parità di fotogramma: la rotazione era
**imbardata pulita** (asse verticale 1.00 → nessuna torsione o deformazione del rig), ma
l'ampiezza era **43° di testa a piena curva** e 21.5° allo sterzo normale. Un cavallo al
galoppo non gira la testa di 43°: guadagni ridotti a un terzo e spostati verso la TESTA
invece che sulla base del collo (che è ciò che rendeva innaturale la posa) → ora **14° a
piena curva, 7° allo sterzo normale**. Aggiunta la manopola unica `BODY_BEND` per ritarare
l'ampiezza senza toccare i singoli guadagni.

**IL BUG VERO, trovato al terzo giro (segnalato «il movimento è al contrario»).** Il corpo
imbardava dalla parte OPPOSTA al moto: misurato in spazio schermo, sterzando a destra il
cavallo si muoveva a +38px ma puntava il muso a **-86px**. Un angolo di deriva doppio e
invertito — *era questo* il «sembra un'auto che derapa» originale, e c'era da prima che
toccassimo l'assetto. Anche il rollio era invertito (si inclinava in FUORI dalla curva).

Causa: in `posToWorld` un offset laterale **positivo** va verso destra schermo, ma la
rotazione attorno a Y che punta a destra è **minore**, non maggiore (una traiettoria a `+s`
verso destra corrisponde all'angolo `h − s`). `model.rotation.y` usava `heading + steerYaw`.
Corretti quattro segni: imbardata del modello, rollio (giocatore e rivali), asse di marcia
del pendolo della coda.

**Perché non era emerso prima.** I miei controlli confrontavano `steerYaw` con un angolo di
traiettoria calcolato *nella stessa convenzione*: un errore di segno comune si cancellava e
la "deriva" risultava 0.7°. Non avevo mai verificato come la scena viene **renderizzata**.
La verifica giusta è proiettare in **spazio schermo** con la camera vera del gioco.

**E un secondo tranello, opposto**: correggendo, avevo invertito anche la piega del corpo,
che era già giusta. Il test in spazio schermo sembrava confermarlo, ma era confuso dal moto
rigido — la coda sta DIETRO il centro, quindi quando il corpo imbarda a destra la coda va a
sinistra da sola. Per la piega serve l'A/B a fotogramma d'animazione fisso (`piega.js`), che
è l'unico a isolarla. Segni finali: imbardata `heading − steerYaw`, piega `−turn * gain`
(opposti fra loro, e non è un errore: ruotano cose diverse attorno ad assi diversi).

**Lezione di metodo:** «si sposta di N unità» non basta a giudicare una posa — serviva
l'angolo dell'osso, e serviva guardare la modalità giusta. Un effetto può essere
matematicamente corretto (imbardata pura, verso giusto, nessun artefatto) e comunque
sbagliato perché è semplicemente troppo.

**Verifiche**: deriva ≤0.9° in tutte le fasi (ingresso/regime/uscita), rollio -13.5° a regime,
testa 14°/7° con asse verticale 1.00, coda -159 verso l'esterno; regressioni invariate
(affondamento 0.0, modalità libera 11/11, 120 fps).

## 9.8 Console + proiezione sul secondo schermo (2026-08-05)

Primo pezzo del porting dello **spettacolo live** dal 2D al 3D: console sullo schermo
dell'operatore, e sul secondo schermo **solo il gioco**.

**Come è fatto.** Il gioco a schermo è tre tele sovrapposte — scena WebGL (`#scene`), HUD
combattimento (`#combat-overlay`, z5), overlay dello show (`#live-overlay`, z6) — mentre i
pannelli di controllo sono DOM. Quindi "proiettare solo il gioco" = ricomporre le tre tele
in ordine di z-index in una seconda finestra: **i pannelli restano fuori per costruzione**,
senza doverli nascondere e senza rischio di dimenticarne uno. Verificato che nella finestra
di proiezione `document.body.innerText` è vuoto.

**Due modalità**: *adatta* (il gioco riempie lo schermo mantenendo l'aspetto) e **matrice
2304×768**, il layout dei live: bande `384 | 192 | 1152(gioco) | 192 | 384`, con testo
verticale scorrevole sulle quattro bande laterali (palette condivisa con la scritta dello
show, glifi pre-renderizzati in cache — nel 2D lo `shadowBlur` per-frame era *il* collo di
bottiglia).

**`vista`: risoluzione logica condivisa.** Punto non ovvio: la banda centrale è 1152×768
(3:2). Se il gioco fosse renderizzato nell'aspetto della finestra dell'operatore, in
proiezione arriverebbe incorniciato di nero. Con la risoluzione di render fissa il render è
NATIVO per il pannello, e nella finestra dell'operatore le tele vengono solo centrate e
scalate — **tutte e tre insieme**, altrimenti le scritte si scollerebbero dal 3D. Per questo
`live` e `combatHud` non usano più `innerWidth/innerHeight` ma `vista.W/H`.

Schermi rilevati con `getScreenDetails()` (serve contesto sicuro: `127.0.0.1` va bene),
`requestFullscreen({screen})` per mandare la proiezione a pieno schermo su quello scelto.
Interruttore per includere o no l'HUD di gioco (di norma escluso).

**Verifiche** (`proiezione.js`, `matrice.js`): la seconda finestra si apre e riceve immagine
(82% di pixel accesi); in modalità matrice il gioco sta nella banda centrale (centro 1363 vs
bordi 0); le bande si accendono col testo (0 → 324); nessun testo DOM in proiezione. Scenario
live vero 2304×768 con render 1152×768: scena e overlay alla stessa risoluzione, **banda
centrale piena al 100% dell'altezza**, nessuna fascia nera. Regressioni invariate, 120 fps.

### Cosa resta del 2D da portare
`gamepad` (Xbox) · `audio reactivity` · `pause menu` · `localStorage persistence` ·
`level system` (livelli tematici + sprite per livello) · `pilota automatico` ·
`custom background` · `asset editor` · `intro/title screens` · `WebRTC webcam` (Livello 7).

## 10. Backlog / idee future (post-Fase 4)
- Coordinare la scelta di lato tra rivali (evitare che due puntino allo stesso `playerX±0.6`
  e si sovrappongano tra loro — vedi §9.1).
- Evitare sovrapposizione di etichette/barre-vita quando due rivali sono vicini in schermo
  (offset verticale se le proiezioni X sono troppo vicine).
- Grab/lotta (guidi il cavallo del rivale e lo schianti), boss di fine ciclo, cop/inseguitori.
- Armi: proiettili visibili per l'arco, effetti impatto (scintille/slow-mo sul takedown), combo counter.
- Multischermo del 2D (banda centrale + testo verticale laterale) e flash-immagine.
- Bilanciamento (danni, durabilità, ricompense), salvataggio XP/upgrade in localStorage.
