# 🖥️ Modalità Schermo Intero - Guida

## 🎮 Come Attivare il Fullscreen

### Metodo 1: Pulsante
Clicca sul pulsante **"🖥️ Fullscreen Mode"** sopra il gioco

### Metodo 2: Tastiera
Premi il tasto **F** durante il gioco

---

## ⌨️ Come Uscire dal Fullscreen

### Metodo 1: Pulsante
Clicca sul pulsante **"🗙 Exit Fullscreen"** (il pulsante cambia testo quando sei in fullscreen)

### Metodo 2: Tastiera - ESC
Premi il tasto **ESC**

### Metodo 3: Tastiera - F
Premi di nuovo il tasto **F**

---

## ✨ Caratteristiche

### Adattamento Automatico
- Il canvas si adatta automaticamente alla risoluzione dello schermo
- L'HUD (velocità, tempo) viene ingrandito per migliore visibilità
- Sfondo nero per eliminare distrazioni

### Cross-Browser
Supporta tutti i principali browser:
- ✅ Chrome / Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

### Risoluzione
- **Modalità normale**: 1024×768px (canvas) / 640×480px (display)
- **Modalità fullscreen**: Risoluzione della finestra browser a schermo intero
  - Es. 1920×1080, 2560×1440, 3840×2160, ecc.

---

## 🎯 Vantaggi del Fullscreen

1. **Immersione Totale** - Nessuna distrazione da browser/desktop
2. **Campo Visivo Maggiore** - Vedi più strada davanti a te
3. **Migliore Performance** - GPU può ottimizzare per schermo intero
4. **Esperienza Console** - Come un gioco per console/arcade

---

## ⚙️ Configurazione Tecnica

### Come Funziona

1. **Attivazione**:
   - Mette in fullscreen il div `#racer`
   - Ridimensiona il canvas alla risoluzione della finestra browser (`window.innerWidth/Height`)
   - Imposta sia la risoluzione interna che il CSS del canvas
   - Applica CSS specifico per fullscreen

2. **Disattivazione**:
   - Esce dal fullscreen
   - Ripristina dimensioni originali (canvas: 1024×768, display: 640×480)
   - Ripristina CSS normale

### Compatibilità Browser

```javascript
// Il codice gestisce automaticamente i prefissi vendor:
requestFullscreen          // Standard
webkitRequestFullscreen    // Chrome/Safari
mozRequestFullScreen       // Firefox
msRequestFullscreen        // Edge Legacy
```

---

## 🐛 Risoluzione Problemi

### Il pulsante non funziona
- Verifica che JavaScript sia abilitato
- Alcuni browser bloccano fullscreen da iframe
- Apri il file direttamente (non in iframe)

### Il gioco appare distorto
- Il canvas si adatta automaticamente
- Se l'aspect ratio è molto diverso (es. 21:9), il gioco potrebbe apparire stirato
- Questo è normale per mantenere tutto visibile

### ESC non funziona
- ESC è gestito direttamente dal browser
- Dovrebbe sempre funzionare, è uno standard di sicurezza

### Performance peggiore in fullscreen
- Risoluzioni molto alte (4K+) richiedono più potenza GPU
- Riduci la risoluzione nelle impostazioni del gioco se necessario
- Abbassa "Draw Distance" o "Fog Density" per migliorare FPS

---

## 📱 Fullscreen su Mobile

**Nota**: Il fullscreen funziona anche su dispositivi mobili, ma:
- Potrebbe richiedere orientamento landscape (orizzontale)
- Su iOS potrebbe non essere supportato in Safari
- Performance potrebbe essere limitata

---

## 🎨 Personalizzazione

### Modificare il Pulsante

Modifica [common.css](common.css:62-77) per cambiare stile:

```css
#fullscreen-btn {
  background: linear-gradient(to bottom, #4CAF50, #45a049);
  color: white;
  /* ... altri stili ... */
}
```

### Cambiare Tasto Scorciatoia

Modifica [horse-racing.html](horse-racing.html:911-916):

```javascript
if (ev.keyCode === 70 && !ev.ctrlKey && !ev.altKey) { // F key
  // Cambia 70 con altro keyCode
  // Es: 71 = G, 72 = H, ecc.
}
```

### Sfondo Fullscreen

Modifica [common.css](common.css:39):

```css
#racer:fullscreen {
  background-color: black; /* Cambia colore qui */
}
```

---

## 💡 Suggerimenti

### Miglior Esperienza
1. Usa fullscreen su monitor grande (24"+ consigliato)
2. Abbassa le luci della stanza per migliore immersione
3. Usa cuffie/altoparlanti per audio coinvolgente
4. Aumenta "Draw Distance" in fullscreen per sfruttare più spazio

### Performance
- Risoluzione 1080p = Buona performance su hardware medio
- Risoluzione 1440p = Richiede GPU discreta
- Risoluzione 4K = Richiede GPU potente

---

## 🔧 Codice Implementazione

### File Modificati

1. **[horse-racing.html](horse-racing.html)**
   - Linea 66: Pulsante fullscreen
   - Linea 742: Disabilitazione audio (Game.playMusic override)
   - Linee 823-920: Logica fullscreen JavaScript

2. **[common.css](common.css)**
   - Linee 29-78: Stili fullscreen

### Eventi Gestiti

- `click` su pulsante fullscreen
- `keydown` con tasto F
- `fullscreenchange` (tutte le varianti browser)
- Resize automatico del canvas

---

## 📊 Statistiche

**Codice aggiunto**:
- JavaScript: ~90 righe
- CSS: ~45 righe
- HTML: 1 pulsante

**Compatibilità**: 95%+ dei browser moderni

---

## 🆘 Supporto

Se hai problemi con il fullscreen:

1. Controlla la console del browser (F12)
2. Verifica che il browser supporti Fullscreen API
3. Testa su browser diverso
4. Prova su schermo/risoluzione diversa

Goditi il gioco a schermo intero! 🏇🖥️
