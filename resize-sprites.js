// Script per ridimensionare gli sprite dei cavalli
const { createCanvas, loadImage } = require('canvas');
const fs = require('fs');
const path = require('path');

// Dimensioni target basate sugli sprite originali
const TARGET_SIZES = {
  'PLAYER_STRAIGHT': { width: 80, height: 41 },
  'PLAYER_LEFT': { width: 80, height: 41 },
  'PLAYER_RIGHT': { width: 80, height: 41 },
  'PLAYER_UPHILL_STRAIGHT': { width: 80, height: 45 },
  'PLAYER_UPHILL_LEFT': { width: 80, height: 45 },
  'PLAYER_UPHILL_RIGHT': { width: 80, height: 45 }
};

const inputDir = path.join(__dirname, 'images', 'horses');
const outputDir = path.join(__dirname, 'images', 'horses_resized');

// Crea la cartella di output
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

async function resizeImage(inputPath, outputPath, targetWidth, targetHeight) {
  try {
    const image = await loadImage(inputPath);
    const canvas = createCanvas(targetWidth, targetHeight);
    const ctx = canvas.getContext('2d');

    // Disegna l'immagine ridimensionata
    ctx.drawImage(image, 0, 0, targetWidth, targetHeight);

    // Salva l'immagine
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(outputPath, buffer);

    return true;
  } catch (err) {
    console.error(`Error processing ${path.basename(inputPath)}:`, err.message);
    return false;
  }
}

async function resizeAll() {
  console.log('\n🔄 Ridimensionamento sprite...\n');

  for (const [key, size] of Object.entries(TARGET_SIZES)) {
    const inputPath = path.join(inputDir, `${key}.png`);
    const outputPath = path.join(outputDir, `${key}.png`);

    if (!fs.existsSync(inputPath)) {
      console.log(`⚠ ${key}.png non trovato`);
      continue;
    }

    const success = await resizeImage(inputPath, outputPath, size.width, size.height);
    if (success) {
      console.log(`✓ ${key}.png → ${size.width}×${size.height}px`);
    }
  }

  console.log('\n✓ Ridimensionamento completato!');
  console.log(`File salvati in: ${outputDir}\n`);
}

// Verifica se il modulo canvas è disponibile
try {
  require.resolve('canvas');
  resizeAll();
} catch (e) {
  console.log('\n⚠ Il modulo "canvas" non è installato.');
  console.log('Installalo con: npm install canvas\n');
  console.log('In alternativa, procedo con un approccio diverso...\n');

  // Metodo alternativo: copiamo gli sprite originali e li useremo così
  console.log('📝 Gli sprite sono stati scaricati ma devono essere ridimensionati manualmente.');
  console.log('Oppure posso creare una versione che li carichi direttamente come file separati.\n');
}
