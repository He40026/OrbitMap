"""Generate simple placeholder tiles for offline use (zoom 0-4, 341 tiles)."""
import os
from PIL import Image, ImageDraw

TILE_DIR = os.path.join('static', 'tiles', 'osm')
ZOOM_LEVELS = range(0, 5)
TILE_SIZE = 256


def generate_tile(z, x, y):
    img = Image.new('RGB', (TILE_SIZE, TILE_SIZE), '#1a4a7a')
    draw = ImageDraw.Draw(img)
    step = TILE_SIZE // max(1, 2 ** (z))
    for i in range(0, TILE_SIZE, max(step, 4)):
        draw.line([(i, 0), (i, TILE_SIZE)], fill='#4a8aaa', width=1)
        draw.line([(0, i), (TILE_SIZE, i)], fill='#4a8aaa', width=1)
    draw.text((6, 6), f'z{z} x{x} y{y}', fill='#aaddff')
    draw.text((6, 24), 'OSM (placeholder)', fill='#88bbdd')
    return img


def main():
    total = sum((2 ** z) ** 2 for z in ZOOM_LEVELS)
    for z in ZOOM_LEVELS:
        n = 2 ** z
        for x in range(n):
            for y in range(n):
                dir_path = os.path.join(TILE_DIR, str(z), str(x))
                file_path = os.path.join(dir_path, f'{y}.png')
                os.makedirs(dir_path, exist_ok=True)
                img = generate_tile(z, x, y)
                img.save(file_path, 'PNG')
        print(f'  z={z}: {n*n} tiles done')
    print(f'Done. Total: {total} tiles')


if __name__ == '__main__':
    main()
