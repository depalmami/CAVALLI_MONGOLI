const express = require('express');
const https = require('https');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const os = require('os');
const fs = require('fs');

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

// Log every HTTP request with IP and User-Agent
app.use((req, res, next) => {
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const ua = req.headers['user-agent'] || '-';
  const isIpad = /iPad|iPhone/.test(ua);
  console.log(`[${isIpad ? 'iPAD' : 'REQ '}] ${ip} ${req.method} ${req.url}  (${ua.slice(0, 60)})`);
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
  res.json({ ips, port: PORT, proto });
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
