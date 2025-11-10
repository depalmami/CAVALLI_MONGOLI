#!/usr/bin/env python3
from PIL import Image
import os
import glob

# Target dimensions (same as Cavallone DX/SX)
TARGET_WIDTH = 384
TARGET_HEIGHT = 1126

horses_dir = os.path.join('images', 'horses')

# Find all PLAYER_STRAIGHT files
pattern = os.path.join(horses_dir, 'PLAYER_*STRAIGHT_*.png')
files = glob.glob(pattern)

print(f"Found {len(files)} STRAIGHT horse images to resize")
print(f"Target size: {TARGET_WIDTH}x{TARGET_HEIGHT}\n")

for filepath in files:
    filename = os.path.basename(filepath)

    # Create backup if it doesn't exist
    backup_path = filepath.replace('.png', '_original.png')
    if not os.path.exists(backup_path):
        img = Image.open(filepath)
        img.save(backup_path)
        print(f"Backed up: {filename} -> {os.path.basename(backup_path)}")

    # Resize image
    img = Image.open(filepath)
    original_size = img.size

    # Resize using high-quality Lanczos resampling
    img_resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # Save
    img_resized.save(filepath)
    print(f"Resized: {filename} from {original_size[0]}x{original_size[1]} to {TARGET_WIDTH}x{TARGET_HEIGHT}")

print("\n✅ All images resized successfully!")
print("Original images backed up with _original.png suffix")
