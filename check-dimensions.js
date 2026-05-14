// Script per verificare le dimensioni degli sprite
const fs = require('fs');
const path = require('path');

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);

function getPngDimensions(filepath) {
  const buffer = fs.readFileSync(filepath);

  // Verifica che sia un PNG
  if (!buffer.slice(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('Not a valid PNG file');
  }

  // Le dimensioni sono nei byte 16-23 (dopo signature + IHDR chunk)
  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);

  return { width, height };
}

const horsesDir = path.join(__dirname, 'images', 'horses');
const files = fs.readdirSync(horsesDir).filter(f => f.endsWith('.png'));

console.log('\n📐 Dimensioni Sprite Cavalli:\n');
console.log('═'.repeat(50));

files.forEach(file => {
  const filepath = path.join(horsesDir, file);
  try {
    const { width, height } = getPngDimensions(filepath);
    const size = (fs.statSync(filepath).size / 1024).toFixed(1);
    console.log(`${file.padEnd(30)} ${width}×${height}px (${size}KB)`);
  } catch (err) {
    console.log(`${file.padEnd(30)} ERROR: ${err.message}`);
  }
});

console.log('═'.repeat(50) + '\n');
