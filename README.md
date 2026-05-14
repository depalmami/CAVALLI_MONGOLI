# Cavalli Mongoli — The Game

Gioco di corsa pseudo-3D costruito appositamente per i live dei **Cavalli Mongoli**.  
Gira nel browser, è controllabile da smartphone via WebRTC e reagisce in tempo reale all'audio.

---

## Cos'è

Un racing game in stile Outrun completamente riscritto e personalizzato a partire da un prototipo open source. La pista, i cavalli, il background e tutti gli asset grafici sono originali e legati all'estetica della band. Il gioco è pensato per essere proiettato durante i live: risponde al suono catturato dal microfono (o da un file audio) e si anima in sincronia con la musica.

## Features principali

**Audioreattività**
- Input da microfono (Web Audio API) o da file audio caricato
- Rilevamento BPM in tempo reale
- Effetti visivi sincronizzati al beat: flash, animazioni, variazioni di velocità

**Controllo da telefono via WebRTC**
- Il telefono funge da controller wireless (stessa rete WiFi)
- Connessione peer-to-peer tramite Socket.io come signaling server
- Nessuna app da installare: basta aprire `http://<ip-locale>/phone` nel browser del telefono

**Grafica custom**
- Sprite originali dei cavalli (animazioni rettilineo, curva destra/sinistra, salita)
- Background stratificato con parallax (cielo, colline, alberi)
- Intro animata con loop di frame custom
- Asset Editor integrato per modificare sprite e elementi di pista a caldo

**Livelli e pista**
- Pista con curve, salite e discese
- Billboard e oggetti di scena personalizzabili per livello
- Sistema di livelli configurabili (vegetazione, ostacoli, cartelloni)

## Come avviare

```bash
npm install
node server.js
```

Apri `http://localhost:3000` nel browser del PC.  
Per il controllo da telefono (stessa rete WiFi): `http://<ip-locale>:3000/phone`

## Stack tecnico

- HTML5 Canvas (rendering pseudo-3D)
- Web Audio API (audioreattività e BPM detection)
- WebRTC + Socket.io (controller wireless da telefono)
- Express.js (server statico + signaling)

## Origine

Basato sul prototipo open source [javascript-racer](https://github.com/jakesgordon/javascript-racer) di Jake Gordon (MIT License), estensivamente modificato per questo progetto.
