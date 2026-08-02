"""Generate simple placeholder tiles for offline use.

Creates the full OSM placeholder grid (zoom 0-4, 341 tiles) plus the single
fallback tile used by Leaflet's errorTileUrl when real tiles are missing.
"""
import os
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_DIR = os.path.join(BASE_DIR, 'static', 'tiles', 'osm')
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


def generate_placeholder():
    """Generate the single offline fallback tile (static/placeholder.png)."""
    img = Image.new('RGB', (TILE_SIZE, TILE_SIZE), '#1a4a7a')
    draw = ImageDraw.Draw(img)
    for i in range(0, TILE_SIZE, 32):
        draw.line([(i, 0), (i, TILE_SIZE)], fill='#2a5a8a', width=1)
        draw.line([(0, i), (TILE_SIZE, i)], fill='#2a5a8a', width=1)
    draw.text((8, 8), 'Offline Map', fill='#aaddff')
    draw.text((8, 26), 'OrbitMap placeholder', fill='#88bbdd')
    path = os.path.join(BASE_DIR, 'static', 'placeholder.png')
    img.save(path, 'PNG')
    return path


def generate_favicon():
    """Generate a tiny favicon (static/favicon.ico)."""
    img = Image.new('RGB', (16, 16), '#1a4a7a')
    ImageDraw.Draw(img).ellipse([2, 2, 13, 13], fill='#00ffcc')
    path = os.path.join(BASE_DIR, 'static', 'favicon.ico')
    img.save(path, 'ICO')
    return path


def main():
    placeholder = generate_placeholder()
    print(f'Fallback tile: {placeholder}')
    favicon = generate_favicon()
    print(f'Favicon: {favicon}')
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
