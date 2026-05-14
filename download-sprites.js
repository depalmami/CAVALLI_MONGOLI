// Script Node.js per scaricare gli sprite dei cavalli
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const sprites = {
  "PLAYER_STRAIGHT": "https://cdn-game-mcp.gambo.ai/5bef70bb-eb45-4a7b-b926-72017ff68d2e/images/PLAYER_STRAIGHT.png",
  "PLAYER_LEFT": "https://cdn-game-mcp.gambo.ai/6fa6820f-3178-4113-bf02-050d9cec4039/images/PLAYER_LEFT.png",
  "PLAYER_RIGHT": "https://cdn-game-mcp.gambo.ai/7abe3f0a-64ea-4f8e-9940-04c112231369/images/PLAYER_RIGHT.png",
  "PLAYER_UPHILL_STRAIGHT": "https://cdn-game-mcp.gambo.ai/30ce3bea-2f4e-4f75-83e3-b7c7ce9e0925/images/PLAYER_UPHILL_STRAIGHT.png",
  "PLAYER_UPHILL_LEFT": "https://cdn-game-mcp.gambo.ai/4ca75d41-594a-47a4-80fe-0c010463322a/images/PLAYER_UPHILL_LEFT.png",
  "PLAYER_UPHILL_RIGHT": "https://cdn-game-mcp.gambo.ai/195a49bc-4179-4228-92c6-22089d919c8e/images/PLAYER_UPHILL_RIGHT.png"
};

const outputDir = path.join(__dirname, 'images', 'horses');

// Crea la cartella se non esiste
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;

    protocol.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download ${url}: ${response.statusCode}`));
        return;
      }

      const fileStream = fs.createWriteStream(filepath);
      response.pipe(fileStream);

      fileStream.on('finish', () => {
        fileStream.close();
        console.log(`✓ Downloaded: ${path.basename(filepath)}`);
        resolve();
      });

      fileStream.on('error', (err) => {
        fs.unlink(filepath, () => {});
        reject(err);
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
}

async function downloadAll() {
  console.log('Downloading horse sprites...\n');

  for (const [key, url] of Object.entries(sprites)) {
    const filepath = path.join(outputDir, `${key}.png`);
    try {
      await downloadImage(url, filepath);
    } catch (err) {
      console.error(`✗ Error downloading ${key}:`, err.message);
    }
  }

  console.log('\n✓ All downloads completed!');
  console.log(`Files saved to: ${outputDir}`);
}

downloadAll();
