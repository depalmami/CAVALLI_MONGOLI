// Script per preparare gli sprite esistenti come frame 1 dell'animazione
const fs = require('fs');
const path = require('path');

const horsesDir = path.join(__dirname, 'images', 'horses');

// Mapping: sprite esistente → nuovo nome (frame 1)
const renameMap = {
  'PLAYER_STRAIGHT.png': 'PLAYER_STRAIGHT_1.png',
  'PLAYER_LEFT.png': 'PLAYER_LEFT_1.png',
  'PLAYER_RIGHT.png': 'PLAYER_RIGHT_1.png',
  'PLAYER_UPHILL_STRAIGHT.png': 'PLAYER_UPHILL_STRAIGHT_1.png',
  'PLAYER_UPHILL_LEFT.png': 'PLAYER_UPHILL_LEFT_1.png',
  'PLAYER_UPHILL_RIGHT.png': 'PLAYER_UPHILL_RIGHT_1.png'
};

console.log('\n🔄 Preparazione sprite per animazione...\n');

let copied = 0;
let errors = 0;

for (const [oldName, newName] of Object.entries(renameMap)) {
  const oldPath = path.join(horsesDir, oldName);
  const newPath = path.join(horsesDir, newName);

  if (fs.existsSync(oldPath)) {
    try {
      // Copia il file (non rinomina, così manteniamo anche l'originale)
      fs.copyFileSync(oldPath, newPath);
      console.log(`✓ ${oldName} → ${newName}`);
      copied++;

      // Crea anche i frame 2, 3, 4 come copie del frame 1 (placeholder)
      const baseName = newName.replace('_1.png', '');
      for (let frame = 2; frame <= 4; frame++) {
        const framePath = path.join(horsesDir, `${baseName}_${frame}.png`);
        fs.copyFileSync(oldPath, framePath);
        console.log(`  ↳ Creato placeholder: ${baseName}_${frame}.png`);
      }
    } catch (err) {
      console.error(`✗ Errore con ${oldName}:`, err.message);
      errors++;
    }
  } else {
    console.warn(`⚠ File non trovato: ${oldName}`);
  }
}

console.log('\n' + '═'.repeat(50));
console.log(`✓ Completato: ${copied} sprite copiati`);
if (errors > 0) {
  console.log(`✗ Errori: ${errors}`);
}
console.log('═'.repeat(50));

console.log('\n📝 Note:');
console.log('- Ogni sprite originale è stato copiato come frame 1');
console.log('- I frame 2, 3, 4 sono attualmente copie del frame 1 (placeholder)');
console.log('- Sostituisci i frame 2-4 con animazioni reali quando pronte');
console.log('- Gli sprite originali sono stati mantenuti come backup\n');
