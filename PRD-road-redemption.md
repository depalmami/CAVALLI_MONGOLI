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

## 10. Backlog / idee future (post-Fase 4)
- Coordinare la scelta di lato tra rivali (evitare che due puntino allo stesso `playerX±0.6`
  e si sovrappongano tra loro — vedi §9.1).
- Evitare sovrapposizione di etichette/barre-vita quando due rivali sono vicini in schermo
  (offset verticale se le proiezioni X sono troppo vicine).
- Grab/lotta (guidi il cavallo del rivale e lo schianti), boss di fine ciclo, cop/inseguitori.
- Armi: proiettili visibili per l'arco, effetti impatto (scintille/slow-mo sul takedown), combo counter.
- Multischermo del 2D (banda centrale + testo verticale laterale) e flash-immagine.
- Bilanciamento (danni, durabilità, ricompense), salvataggio XP/upgrade in localStorage.
