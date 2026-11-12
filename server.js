const express = require('express');
const https = require('https');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const os = require('os');
const fs = require('fs');
const dgram = require('dgram');

const app = express();

// HTTPS with self-signed cert (required for getUserMedia on iOS Safari)
let server;
try {
  const sslOptions = {
    key:  fs.readFileSync(path.join(__dirname, 'ssl/key.pem')),
    cert: fs.readFileSync(path.join(__dirname, 'ssl/cert.pem')),
  };
  server = https.createServer(sslOptions, app);
} catch (e) {
  console.warn('SSL certs not found, falling back to HTTP (camera will not work on iOS):', e.message);
  server = http.createServer(app);
}
const io = new Server(server);
// I device Max inviano piccoli datagrammi JSON sulla LAN. Non esponiamo
// comandi di controllo: il ponte inoltra solo telemetria musicale validata.
const MUSIC_PORT = Number(process.env.MUSIC_PORT) || 41234;
const musicUdp = dgram.createSocket('udp4');
let musicSender = null;
musicUdp.on('message', (buffer, remote) => {
  if (buffer.length > 2048) return;
  let data;
  try { data = JSON.parse(buffer.toString('utf8')); } catch { return; }
  if (!data || data.v !== 1 || !['clock', 'midi', 'audio'].includes(data.type)) return;
  if (data.type === 'clock' &&
      (!Number.isFinite(data.bpm) || data.bpm < 20 || data.bpm > 300 ||
       !Number.isFinite(data.beat) || data.beat < 0)) return;
  if (data.type === 'midi' &&
      (!Array.isArray(data.bytes) || data.bytes.length > 3 ||
       data.bytes.some(b => !Number.isInteger(b) || b < 0 || b > 255))) return;
  if (data.type === 'audio' && (!Number.isFinite(data.level) || data.level < 0 || data.level > 4)) return;
  musicSender = remote.address;
  io.emit('music-lan', data);
});
musicUdp.on('error', e => console.warn('[music UDP]', e.message));
musicUdp.bind(MUSIC_PORT, '0.0.0.0', () => console.log(`Music UDP: ${MUSIC_PORT}`));

// Log every HTTP request with IP, status code and User-Agent.
// Mostrare lo status code aiuta a identificare al volo eventuali 404/500
// nascosti tra centinaia di richieste (es. durante il preload di tutti i livelli).
app.use((req, res, next) => {
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const ua = req.headers['user-agent'] || '-';
  const isIpad = /iPad|iPhone/.test(ua);
  const start = Date.now();
  res.on('finish', () => {
    const code = res.statusCode;
    const tag = code >= 500 ? 'ERR ' : code >= 400 ? 'WARN' : (isIpad ? 'iPAD' : 'REQ ');
    const ms = Date.now() - start;
    console.log(`[${tag}] ${code} ${ip} ${req.method} ${req.url}  (${ms}ms)  (${ua.slice(0, 50)})`);
  });
  next();
});

// No-cache su HTML così iOS Safari ricarica davvero il codice nuovo ad ogni reload
const noCache = (req, res, next) => {
  res.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
  res.set('Pragma', 'no-cache');
  res.set('Expires', '0');
  next();
};

app.use(express.static(__dirname, {
  index: false,
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    } else if (/\.(png|jpe?g|gif|svg|webp)$/i.test(filePath)) {
      // Anti-cache aggressivo su immagini: il dev sostituisce asset frequentemente
      // e iOS Safari / Chrome cachano vecchie versioni indefinitamente.
      // ETag basato su mtime/size resta abilitato → reload veloci se nulla cambia.
      res.set('Cache-Control', 'no-cache, must-revalidate');
    }
  }
}));

app.get('/phone', noCache, (req, res) => {
  res.sendFile(path.join(__dirname, 'phone.html'));
});

// URL alternativi: bypass cache di iOS Safari quando il vecchio /phone è già cached
app.get(['/cam', '/ipad', '/phone2', '/phone-v3'], noCache, (req, res) => {
  res.sendFile(path.join(__dirname, 'phone.html'));
});

app.get('/', noCache, (req, res) => {
  res.sendFile(path.join(__dirname, 'horse-racing.html'));
});

// LAN info per il pannello del gioco
app.get('/_lan_info', (req, res) => {
  const nets = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) ips.push(net.address);
    }
  }
  res.json({ ips, port: PORT, proto, musicPort: MUSIC_PORT, musicSender });
});

// 2-peer signaling con single-occupant per ruolo
const peers = { pc: null, phone: null };

io.on('connection', (socket) => {
  const ip = socket.handshake.address;
  const ua = socket.handshake.headers['user-agent'] || '-';
  console.log(`[WS  ] Client connected: ${socket.id}  ip=${ip}  ua=${ua.slice(0, 60)}`);

  socket.on('join', (role) => {
    if (role !== 'pc' && role !== 'phone') {
      console.warn('[join] unknown role:', role);
      return;
    }
    const existing = peers[role];
    if (existing && existing.id !== socket.id && existing.connected) {
      console.log(`[${role}] kicking previous peer ${existing.id}`);
      existing.emit('kicked', 'replaced by new ' + role);
      existing.disconnect(true);
    }
    socket.data.role = role;
    peers[role] = socket;
    socket.join('game-room');
    console.log(`[${role}] joined  (pc=${!!peers.pc} phone=${!!peers.phone})`);
    socket.to('game-room').emit('peer-joined', role);
    // Conferma retroattivamente al peer chi c'è già nella stanza
    const otherRole = role === 'pc' ? 'phone' : 'pc';
    if (peers[otherRole]) socket.emit('peer-joined', otherRole);
  });

  socket.on('offer', (offer) => {
    socket.to('game-room').emit('offer', offer);
  });

  socket.on('answer', (answer) => {
    socket.to('game-room').emit('answer', answer);
  });

  socket.on('ice-candidate', (candidate) => {
    socket.to('game-room').emit('ice-candidate', candidate);
  });

  // PC chiede al phone di rimandare un fresh offer (utile se il PC entra dopo o ricarica)
  socket.on('request-offer', () => {
    console.log('[request-offer] from', socket.data.role);
    socket.to('game-room').emit('request-offer');
  });

  socket.on('disconnect', () => {
    const role = socket.data.role;
    console.log('Client disconnected:', socket.id, role || '(no role)');
    if (role && peers[role] === socket) peers[role] = null;
    socket.to('game-room').emit('peer-disconnected', role);
  });
});

const PORT = process.env.PORT || 3000;
const isHttps = server instanceof https.Server;
const proto = isHttps ? 'https' : 'http';

server.listen(PORT, '0.0.0.0', () => {
  const nets = os.networkInterfaces();
  console.log(`\nSignaling server running on port ${PORT} (${proto.toUpperCase()})`);
  console.log(`Open the game on this Mac at:  ${proto}://localhost:${PORT}`);
  console.log('Open on iPad/phone (same WiFi) at:');
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) {
        console.log(`  ${proto}://${net.address}:${PORT}/`);
        console.log(`  ${proto}://${net.address}:${PORT}/phone  (modalità telefono)`);
      }
    }
  }
  if (isHttps) {
    console.log('\n⚠  Certificato self-signed: al primo accesso accetta il rischio nel browser.');
  }
  console.log('');
});
