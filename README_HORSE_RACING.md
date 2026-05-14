# 🏇 Horse Racing Game - Mongolian Horses Edition

Versione modificata del javascript-racer che trasforma il gioco di corse automobilistiche in un gioco di corse di cavalli mongoli.

---

## 🚀 Quick Start

### 1. Avvia il gioco
Apri `horse-racing.html` in un browser moderno, oppure usa un server HTTP locale:

```bash
npx http-server .
```

Poi vai su: `http://localhost:8080/horse-racing.html`

### 2. Controlli
- **Frecce ↑↓** o **W/S**: Accelera / Frena
- **Frecce ←→** o **A/D**: Sterza sinistra / destra

---

## ✨ Caratteristiche

### ✅ Implementato
- [x] Sistema di caricamento sprite cavalli separati
- [x] Animazione galoppo a 4 frame
- [x] Velocità animazione proporzionale alla velocità del cavallo
- [x] Aspect ratio corretto degli sprite
- [x] HUD modificato (km/h invece di mph)
- [x] 24 sprite pronti (attualmente placeholder)
- [x] Sistema fallback intelligente

### 🎨 Grafica
- **Cavallo giocatore**: 6 direzioni × 4 frame = 24 sprite
- **Dimensioni**: Scalate automaticamente mantenendo proporzioni
- **Animazione**: 10-30 FPS basata su velocità cavallo

### ⚙️ Fisica
- **Velocità massima**: ~200 km/h (uguale all'originale)
- **Accelerazione**: Ottimizzata per cavalli
- **Decelerazione fuori pista**: Simula il rallentamento su terreno non adatto

---

## 📁 Struttura File

```
javascript-racer/
├── horse-racing.html           ← FILE PRINCIPALE DEL GIOCO
├── HORSE_SPRITES_GUIDE.md      ← Guida completa sprite
├── README_HORSE_RACING.md      ← Questo file
├── images/
│   └── horses/                 ← Sprite dei cavalli (24 file)
│       ├── PLAYER_STRAIGHT_1.png
│       ├── PLAYER_STRAIGHT_2.png
│       ├── PLAYER_STRAIGHT_3.png
│       ├── PLAYER_STRAIGHT_4.png
│       ├── PLAYER_LEFT_1.png
│       ├── ... (altri 19 sprite)
├── download-sprites.js         ← Script per scaricare sprite
├── setup-animation-sprites.js  ← Script per preparare animazione
└── check-dimensions.js         ← Utility per verificare dimensioni
```

---

## 🎨 Sprite Cavalli

### Sprite Attuali
Gli sprite attuali sono **placeholder** - tutti i 4 frame per ogni direzione usano la stessa immagine.

### Come Sostituire con Sprite Reali

1. **Crea i tuoi sprite** seguendo la guida in `HORSE_SPRITES_GUIDE.md`
2. **Nomina i file** correttamente:
   - `PLAYER_STRAIGHT_1.png` ... `PLAYER_STRAIGHT_4.png`
   - `PLAYER_LEFT_1.png` ... `PLAYER_LEFT_4.png`
   - `PLAYER_RIGHT_1.png` ... `PLAYER_RIGHT_4.png`
   - `PLAYER_UPHILL_STRAIGHT_1.png` ... `PLAYER_UPHILL_STRAIGHT_4.png`
   - `PLAYER_UPHILL_LEFT_1.png` ... `PLAYER_UPHILL_LEFT_4.png`
   - `PLAYER_UPHILL_RIGHT_1.png` ... `PLAYER_UPHILL_RIGHT_4.png`

3. **Sostituisci** i file in `images/horses/`
4. **Ricarica** il gioco - l'animazione apparirà automaticamente!

---

## ⚙️ Personalizzazione

### Dimensione Cavallo
Modifica la linea **528** in `horse-racing.html`:

```javascript
var horseSizeMultiplier = 0.5; // Cambia questo valore!
```

- `0.3` = Molto piccolo
- `0.5` = Attuale (metà dimensione auto)
- `0.8` = Grande
- `1.0` = Dimensione auto originale

### Velocità Animazione
Modifica la linea **500** in `horse-racing.html`:

```javascript
var animationSpeed = 10 + (speedPercent * 20); // Range: 10-30
```

- Primo numero (10): FPS minimo quando il cavallo è fermo
- Secondo numero (20): Aumento FPS in base alla velocità

### Velocità Massima
Modifica la variabile `maxSpeed` per cambiare la velocità di gioco.

---

## 🛠️ Script Utility

### `download-sprites.js`
Scarica gli sprite dai CDN:
```bash
node download-sprites.js
```

### `setup-animation-sprites.js`
Prepara gli sprite esistenti per l'animazione a 4 frame:
```bash
node setup-animation-sprites.js
```

### `check-dimensions.js`
Verifica le dimensioni degli sprite:
```bash
node check-dimensions.js
```

---

## 🐛 Troubleshooting

### Il cavallo non appare
- Verifica che gli sprite siano in `images/horses/`
- Apri la console del browser (F12) per vedere errori
- Il gioco userà sprite delle auto come fallback

### L'animazione non è fluida
- Aumenta `animationSpeed` per animazione più veloce
- Verifica che tutti i 4 frame per direzione esistano

### Il cavallo è troppo grande/piccolo
- Regola `horseSizeMultiplier` in `horse-racing.html`

### Gli sprite appaiono "schiacciati"
- Il codice mantiene automaticamente l'aspect ratio
- Verifica che gli sprite abbiano proporzioni corrette (~1.5-2.0 altezza/larghezza)

---

## 📊 Specifiche Tecniche

### Sprite
- **Formato**: PNG con trasparenza
- **Dimensioni originali**: 400-1300px (vengono scalati automaticamente)
- **Aspect ratio**: Mantenuto automaticamente dal codice
- **Totale sprite**: 24 (6 direzioni × 4 frame)

### Performance
- **FPS target**: 60
- **Frame animazione**: 10-30 (variabile)
- **Risoluzione canvas**: 480×360 fino a 1280×960

### Browser Supportati
- Chrome 19+
- Firefox 12+
- Edge
- Safari (con possibili limitazioni di performance)

---

## 🔮 Sviluppi Futuri

### Possibili Miglioramenti
- [ ] Sprite cavalli avversari (sostituire le auto)
- [ ] Sfondo ippodromo (sostituire autostrada)
- [ ] Sistema stamina per il cavallo
- [ ] Effetti sonori zoccoli
- [ ] Particelle polvere
- [ ] Diversi tipi di cavalli (velocità/resistenza)
- [ ] Ostacoli specifici per ippodromo
- [ ] Multiplayer

---

## 📄 Licenza

Basato su [javascript-racer](https://github.com/jakesgordon/javascript-racer) di Jake Gordon (MIT License)

Modifiche per Horse Racing Edition: MIT License

**Nota**: Gli sprite dei cavalli devono essere creati/forniti separatamente. Gli sprite placeholder attuali sono solo per test.

---

## 🙏 Credits

- **Gioco originale**: [Jake Gordon](https://jakesgordon.com/)
- **Adattamento cavalli**: Creato con Claude Code
- **Sprite cavalli**: [Da fornire/creare]

---

## 📞 Supporto

Per problemi o domande:
1. Consulta `HORSE_SPRITES_GUIDE.md` per dettagli sprite
2. Verifica la console del browser per errori
3. Assicurati che tutti i file siano nelle cartelle corrette

Buon galoppo! 🏇💨
