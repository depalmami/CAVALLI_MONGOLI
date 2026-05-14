# 🐴 Animazione a 8 Frame - Cavalcata Dritta

## 📝 Riepilogo Modifiche

Il gioco ora supporta **8 frame** per l'animazione della cavalcata dritta (STRAIGHT), mentre le altre direzioni (LEFT, RIGHT) continuano ad usare 4 frame.

---

## ✅ Modifiche Applicate

### 1. File Rinominati

Gli 8 file originali `01.png` - `08.png` sono stati rinominati:

```
01.png → PLAYER_STRAIGHT_1.png
02.png → PLAYER_STRAIGHT_2.png
03.png → PLAYER_STRAIGHT_3.png
04.png → PLAYER_STRAIGHT_4.png
05.png → PLAYER_STRAIGHT_5.png
06.png → PLAYER_STRAIGHT_6.png
07.png → PLAYER_STRAIGHT_7.png
08.png → PLAYER_STRAIGHT_8.png
```

Posizione: `images/horses/PLAYER_STRAIGHT_*.png`

### 2. Codice Aggiornato

#### File: [horse-racing.html](horse-racing.html)

**Linee 147-166**: Funzione `loadHorseSprites()` modificata
```javascript
// STRAIGHT direction has 8 frames, others have 4
var frameCount = (direction === 'STRAIGHT') ? 8 : 4;
```

**Linee 496-505**: Funzione `renderHorsePlayer()` modificata
```javascript
// STRAIGHT direction has 8 frames, others have 4 frames
var maxFrames = (direction === 'STRAIGHT') ? 8 : 4;

// Cycle through frames (1, 2, 3, ..., maxFrames)
var frameIndex = Math.floor(gallopAnimationTime % maxFrames) + 1;
```

---

## 🎮 Come Funziona

### Sistema di Frame Dinamico

Il gioco ora determina automaticamente quanti frame usare in base alla direzione:

- **STRAIGHT** (dritto): **8 frame**
  - `PLAYER_STRAIGHT_1.png` → `PLAYER_STRAIGHT_8.png`
  - `PLAYER_UPHILL_STRAIGHT_1.png` → `PLAYER_UPHILL_STRAIGHT_8.png` (se disponibili)

- **LEFT** (sinistra): **4 frame**
  - `PLAYER_LEFT_1.png` → `PLAYER_LEFT_4.png`
  - `PLAYER_UPHILL_LEFT_1.png` → `PLAYER_UPHILL_LEFT_4.png` (se disponibili)

- **RIGHT** (destra): **4 frame**
  - `PLAYER_RIGHT_1.png` → `PLAYER_RIGHT_4.png`
  - `PLAYER_UPHILL_RIGHT_1.png` → `PLAYER_UPHILL_RIGHT_4.png` (se disponibili)

### Velocità Animazione

L'animazione si adatta alla velocità del cavallo:
- **Fermo/Lento**: 10 FPS (animazione lenta)
- **Velocità massima**: 30 FPS (animazione rapida)

Formula: `animationSpeed = 10 + (speedPercent * 20)`

---

## 📊 Totale Sprite

Con questa configurazione, il gioco può gestire:

| Direzione | Terreno | Frame | Totale |
|-----------|---------|-------|--------|
| STRAIGHT  | Normale | 8     | 8      |
| STRAIGHT  | Uphill  | 8     | 8      |
| LEFT      | Normale | 4     | 4      |
| LEFT      | Uphill  | 4     | 4      |
| RIGHT     | Normale | 4     | 4      |
| RIGHT     | Uphill  | 4     | 4      |
| **TOTALE**|         |       | **32** |

**Attualmente disponibili**: 8 sprite (STRAIGHT normale)

---

## 🎨 Come Aggiungere Altri Sprite

### Per le Direzioni LEFT e RIGHT (4 frame ciascuna)

Se vuoi animazioni anche per le altre direzioni, crea:

**Sinistra (LEFT)**:
- `PLAYER_LEFT_1.png` → `PLAYER_LEFT_4.png`

**Destra (RIGHT)**:
- `PLAYER_RIGHT_1.png` → `PLAYER_RIGHT_4.png`

### Per le Varianti Uphill (Salita)

Se vuoi sprite diversi per le salite, crea:

**Dritto in salita** (8 frame):
- `PLAYER_UPHILL_STRAIGHT_1.png` → `PLAYER_UPHILL_STRAIGHT_8.png`

**Sinistra in salita** (4 frame):
- `PLAYER_UPHILL_LEFT_1.png` → `PLAYER_UPHILL_LEFT_4.png`

**Destra in salita** (4 frame):
- `PLAYER_UPHILL_RIGHT_1.png` → `PLAYER_UPHILL_RIGHT_4.png`

### Per Usare 8 Frame Anche per LEFT e RIGHT

Se hai 8 frame anche per LEFT e RIGHT, modifica [horse-racing.html:159](horse-racing.html#L159):

```javascript
// Cambia da:
var frameCount = (direction === 'STRAIGHT') ? 8 : 4;

// A:
var frameCount = 8; // Tutte le direzioni usano 8 frame
```

E modifica anche la [linea 502](horse-racing.html#L502):

```javascript
// Cambia da:
var maxFrames = (direction === 'STRAIGHT') ? 8 : 4;

// A:
var maxFrames = 8; // Tutte le direzioni usano 8 frame
```

---

## 🛠️ Script Utility

### `rename-straight-frames.js`

Script Node.js per rinominare automaticamente i frame:

```bash
node rename-straight-frames.js
```

Rinomina i file da `01.png`-`08.png` a `PLAYER_STRAIGHT_1.png`-`PLAYER_STRAIGHT_8.png`.

---

## 🎯 Test dell'Animazione

### Come Verificare

1. **Apri il gioco**: `horse-racing.html` nel browser
2. **Controlla la console** (F12):
   - Dovrebbe mostrare: "Horse sprites loaded!"
   - Non dovrebbero esserci errori di caricamento sprite

3. **Osserva il cavallo**:
   - Quando vai **dritto** (nessun tasto freccia laterale), dovresti vedere l'animazione a 8 frame
   - L'animazione dovrebbe essere **fluida e ciclica**
   - La velocità dell'animazione dovrebbe **aumentare** con la velocità del cavallo

4. **Test con frecce laterali**:
   - Se premi **LEFT** o **RIGHT**, il gioco userà sprite diversi (se disponibili) o farà fallback

---

## 🔧 Personalizzazione

### Velocità Animazione

Modifica [horse-racing.html:498](horse-racing.html#L498):

```javascript
var animationSpeed = 10 + (speedPercent * 20);
//                   ^^     ^^^^^^^^^^^^^^^^^^
//                   |      └─ Incremento basato su velocità
//                   └─ FPS minimo quando fermo
```

**Esempi**:
- Animazione più lenta: `var animationSpeed = 5 + (speedPercent * 10);`
- Animazione più veloce: `var animationSpeed = 15 + (speedPercent * 30);`
- Velocità costante: `var animationSpeed = 20;` (sempre 20 FPS)

### Dimensione Cavallo

Modifica [horse-racing.html:525](horse-racing.html#L525):

```javascript
var horseSizeMultiplier = 0.5; // Attualmente metà dimensione auto
```

- `0.3` = Molto piccolo
- `0.5` = Metà dimensione (attuale)
- `0.8` = Grande
- `1.0` = Dimensione auto originale

---

## 📈 Benefici dell'Animazione a 8 Frame

1. **Maggiore Fluidità**: L'animazione appare più naturale e realistica
2. **Dettagli Migliori**: Più frame permettono di mostrare più dettagli del galoppo
3. **Ciclo Completo**: 8 frame permettono di rappresentare un ciclo completo di galoppo
4. **Scalabilità**: Il sistema supporta facilmente configurazioni diverse (4, 6, 8, o più frame)

---

## 🐛 Troubleshooting

### I frame non si animano

1. **Verifica che i file siano rinominati correttamente**:
   ```bash
   cd images/horses
   ls PLAYER_STRAIGHT_*.png
   ```
   Dovresti vedere 8 file: `PLAYER_STRAIGHT_1.png` fino a `PLAYER_STRAIGHT_8.png`

2. **Controlla la console del browser** (F12):
   - Cerca messaggi di errore riguardo il caricamento sprite
   - Verifica che tutti i file siano caricati correttamente

3. **Verifica il codice**:
   - Controlla che [linea 502](horse-racing.html#L502) contenga:
     ```javascript
     var maxFrames = (direction === 'STRAIGHT') ? 8 : 4;
     ```

### L'animazione è troppo veloce/lenta

Modifica la velocità dell'animazione come descritto nella sezione "Personalizzazione" sopra.

### Il cavallo appare distorto

Verifica che tutte le immagini abbiano lo **stesso aspect ratio** (rapporto larghezza/altezza). Altrimenti l'animazione apparirà "saltellante".

---

## 📚 Documentazione Correlata

- [README_HORSE_RACING.md](README_HORSE_RACING.md) - Guida principale del gioco
- [HORSE_SPRITES_GUIDE.md](HORSE_SPRITES_GUIDE.md) - Guida completa agli sprite
- [FULLSCREEN_GUIDE.md](FULLSCREEN_GUIDE.md) - Guida modalità fullscreen
- [FIXES_APPLIED.md](FIXES_APPLIED.md) - Correzioni applicate (audio, fullscreen)

---

## ✨ Stato Attuale

- ✅ Sistema di animazione a 8 frame implementato
- ✅ File sprite rinominati correttamente
- ✅ Codice aggiornato per gestire frame dinamici
- ✅ Animazione adattiva alla velocità
- ✅ Sistema di fallback funzionante
- ✅ Compatibile con fullscreen
- ⏳ Sprite per LEFT e RIGHT da aggiungere (opzionale)
- ⏳ Sprite UPHILL da aggiungere (opzionale)

---

Buon galoppo con l'animazione migliorata! 🏇💨
