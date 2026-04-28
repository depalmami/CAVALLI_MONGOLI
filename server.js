const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const os = require('os');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static(path.join(__dirname, 'javascript-racer')));

app.get('/phone', (req, res) => {
  res.sendFile(path.join(__dirname, 'phone.html'));
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'javascript-racer', 'horse-racing.html'));
});

// Simple 2-peer signaling: 'phone' and 'pc' roles
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('join', (role) => {
    socket.data.role = role;
    socket.join('game-room');
    console.log(`[${role}] joined`);
    // Notify the other peer
    socket.to('game-room').emit('peer-joined', role);
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

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id, socket.data.role);
    socket.to('game-room').emit('peer-disconnected', socket.data.role);
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
  // Print local IPs so it's easy to connect phone
  const nets = os.networkInterfaces();
  console.log(`\nSignaling server running on port ${PORT}`);
  console.log('Open the game on this PC at:  http://localhost:' + PORT);
  console.log('Open on phone (same WiFi) at:');
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) {
        console.log(`  http://${net.address}:${PORT}/phone`);
      }
    }
  }
  console.log('');
});
