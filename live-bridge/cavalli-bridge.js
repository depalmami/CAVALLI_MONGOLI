// Node for Max: converte gli eventi dei due device in JSON su UDP.
const max = require('max-api');
const dgram = require('dgram');
const fs = require('fs');
const path = require('path');
const udp = dgram.createSocket('udp4');
const configPath = path.join(__dirname, 'bridge-config.json');
let config = { host: '127.0.0.1', port: 41234 };
try { config = { ...config, ...JSON.parse(fs.readFileSync(configPath, 'utf8')) }; }
catch (e) { max.post('Cavalli Bridge: bridge-config.json non trovato, uso localhost:41234'); }
if (!Number.isInteger(config.port) || config.port < 1 || config.port > 65535) config.port = 41234;
const send = data => {
  const b = Buffer.from(JSON.stringify({ v: 1, ...data }));
  udp.send(b, config.port, config.host, e => { if (e) max.post('Cavalli Bridge UDP: ' + e.message); });
};
max.post(`Cavalli Bridge -> ${config.host}:${config.port}`);
max.addHandler('clock', (bpm, beat, playing) => {
  bpm = Number(bpm); beat = Number(beat);
  if (Number.isFinite(bpm) && Number.isFinite(beat)) send({ type: 'clock', bpm, beat, playing: !!Number(playing) });
});
max.addHandler('audio', level => {
  level = Number(level);
  if (Number.isFinite(level)) send({ type: 'audio', level: Math.max(0, Math.min(4, level)) });
});
let status = 0, pending = [];
max.addHandler('midi', byte => {
  byte = Number(byte);
  if (!Number.isInteger(byte) || byte < 0 || byte > 255) return;
  if (byte >= 0xF8) return; // Clock MIDI grezzo: il tempo arriva dal trasporto Live.
  if (byte & 0x80) { status = byte; pending = []; return; }
  if (!status || status >= 0xF0) return;
  pending.push(byte);
  const count = (status & 0xF0) === 0xC0 || (status & 0xF0) === 0xD0 ? 1 : 2;
  if (pending.length >= count) {
    send({ type: 'midi', bytes: [status, ...pending.slice(0, count)] });
    pending = [];
  }
});
