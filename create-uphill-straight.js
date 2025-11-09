// Script per creare sprite UPHILL_STRAIGHT copiando gli sprite STRAIGHT
const fs = require('fs');
const path = require('path');

const horsesDir = path.join(__dirname, 'images', 'horses');

console.log('\n⛰️ Creando sprite UPHILL_STRAIGHT...\n');

let created = 0;
let errors = 0;

// Copia PLAYER_STRAIGHT_1-8.png a PLAYER_UPHILL_STRAIGHT_1-8.png
for (let i = 1; i <= 8; i++) {
  const sourceName = `PLAYER_STRAIGHT_${i}.png`;
  const targetName = `PLAYER_UPHILL_STRAIGHT_${i}.png`;
  const sourcePath = path.join(horsesDir, sourceName);
  const targetPath = path.join(horsesDir, targetName);

  if (fs.existsSync(sourcePath)) {
    try {
      if (!fs.existsSync(targetPath)) {
        fs.copyFileSync(sourcePath, targetPath);
        console.log(`✓ Creato: ${targetName}`);
        created++;
      } else {
        console.log(`⚠ Già esistente: ${targetName}`);
      }
    } catch (err) {
      console.error(`✗ Errore creando ${targetName}:`, err.message);
      errors++;
    }
  } else {
    console.error(`✗ File sorgente non trovato: ${sourceName}`);
    errors++;
  }
}

console.log('\n' + '═'.repeat(50));
console.log(`✓ Creati: ${created} file`);
if (errors > 0) {
  console.log(`✗ Errori: ${errors}`);
}
console.log('═'.repeat(50));

console.log('\n📝 Note:');
console.log('- Sprite UPHILL_STRAIGHT sono copie di STRAIGHT');
console.log('- Puoi sostituirli con sprite diversi in futuro');
console.log('- Il gioco ora dovrebbe caricare senza errori!\n');
