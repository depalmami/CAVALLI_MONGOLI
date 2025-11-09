// Script per rinominare i frame della cavalcata dritta da 01-08.png a PLAYER_STRAIGHT_1-8.png
const fs = require('fs');
const path = require('path');

const horsesDir = path.join(__dirname, 'images', 'horses');

console.log('\n🐴 Rinominando frame cavalcata dritta...\n');

let renamed = 0;
let errors = 0;

// Rinomina da 01.png...08.png a PLAYER_STRAIGHT_1.png...PLAYER_STRAIGHT_8.png
for (let i = 1; i <= 8; i++) {
  const oldName = `0${i}.png`;
  const newName = `PLAYER_STRAIGHT_${i}.png`;
  const oldPath = path.join(horsesDir, oldName);
  const newPath = path.join(horsesDir, newName);

  if (fs.existsSync(oldPath)) {
    try {
      fs.renameSync(oldPath, newPath);
      console.log(`✓ ${oldName} → ${newName}`);
      renamed++;
    } catch (err) {
      console.error(`✗ Errore rinominando ${oldName}:`, err.message);
      errors++;
    }
  } else {
    console.warn(`⚠ File non trovato: ${oldName}`);
  }
}

console.log('\n' + '═'.repeat(50));
console.log(`✓ Rinominati: ${renamed} file`);
if (errors > 0) {
  console.log(`✗ Errori: ${errors}`);
}
console.log('═'.repeat(50));

console.log('\n📝 Prossimi passi:');
console.log('1. Il codice ora caricherà automaticamente 8 frame per STRAIGHT');
console.log('2. Le direzioni LEFT e RIGHT useranno ancora 4 frame (fallback)');
console.log('3. Ricarica horse-racing.html nel browser per vedere l\'animazione!\n');
