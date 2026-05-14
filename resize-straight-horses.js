const fs = require('fs');
const path = require('path');

// Try to use sharp, fallback to canvas if not available
let resizeImage;

try {
  const sharp = require('sharp');
  console.log('Using sharp for image resizing');

  resizeImage = async (inputPath, outputPath, width, height) => {
    await sharp(inputPath)
      .resize(width, height, {
        fit: 'fill',
        kernel: 'lanczos3'
      })
      .png()
      .toFile(outputPath);
  };
} catch (err) {
  console.log('Sharp not available, using canvas');
  const { createCanvas, loadImage } = require('canvas');

  resizeImage = async (inputPath, outputPath, width, height) => {
    const image = await loadImage(inputPath);
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext('2d');

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(image, 0, 0, width, height);

    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(outputPath, buffer);
  };
}

const horsesDir = path.join(__dirname, 'images', 'horses');
const targetWidth = 384;
const targetHeight = 1126;

async function resizeAllStraightHorses() {
  // Process all PLAYER_STRAIGHT_*.png files
  const files = fs.readdirSync(horsesDir);
  const straightFiles = files.filter(f => f.match(/^PLAYER_(UPHILL_)?STRAIGHT_\d+\.png$/));

  console.log(`Found ${straightFiles.length} STRAIGHT horse images to resize`);
  console.log(`Target size: ${targetWidth}x${targetHeight}`);

  for (const file of straightFiles) {
    const inputPath = path.join(horsesDir, file);
    const outputPath = inputPath; // Overwrite original
    const backupPath = inputPath.replace('.png', '_original.png');

    // Backup original
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(inputPath, backupPath);
      console.log(`Backed up: ${file} -> ${path.basename(backupPath)}`);
    }

    // Resize
    await resizeImage(inputPath, outputPath, targetWidth, targetHeight);
    console.log(`Resized: ${file} to ${targetWidth}x${targetHeight}`);
  }

  console.log('\n✅ All images resized successfully!');
  console.log('Original images backed up with _original.png suffix');
}

resizeAllStraightHorses().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
