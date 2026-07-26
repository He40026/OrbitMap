"""Download Esri World Imagery tiles for offline use (zoom 0-5, 1365 tiles)."""

import os
import time
import urllib.request

TILE_DIR = os.path.join('static', 'tiles', 'esri')
ZOOM_LEVELS = range(0, 6)
HEADERS = {'User-Agent': 'OrbitVisualizer/1.0 (educational project)'}
DELAY = 0.4
TOTAL_TILES = sum((2 ** z) ** 2 for z in ZOOM_LEVELS)


def tile_path(z, x, y):
    return os.path.join(TILE_DIR, str(z), str(x), f'{y}.png')


def download_tile(z, x, y):
    url = f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    path = tile_path(z, x, y)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return 'skip'
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as src:
            data = src.read()
        content_type = src.headers.get('Content-Type', '')
        ext = '.jpg' if ('jpeg' in content_type or 'jpg' in content_type) else '.png'
        final_path = path if ext == '.png' else path.replace('.png', ext)
        with open(final_path, 'wb') as f:
            f.write(data)
        if ext != '.png':
            os.rename(final_path, path)
        return 'ok'
    except Exception as e:
        print(f'  [{z}/{x}/{y}] {e}')
        return 'fail'


def main():
    print('=' * 55)
    print('  Esri World Imagery Tile Downloader')
    print(f'  Zoom levels: 0-5  ({TOTAL_TILES} tiles total)')
    print('=' * 55)
    print()
    print('NOTE: Requires internet access (VPN if needed).')
    print('Only needs to run ONCE. After that, tiles are available offline.')
    print()

    reply = input('Start download? (y/n): ').strip().lower()
    if reply != 'y':
        print('Cancelled.')
        return

    ok = skip = fail = 0
    for z in ZOOM_LEVELS:
        n = 2 ** z
        for x in range(n):
            for y in range(n):
                result = download_tile(z, x, y)
                if result == 'ok':
                    ok += 1
                elif result == 'skip':
                    skip += 1
                else:
                    fail += 1
                time.sleep(DELAY)
        print(f'  z={z}: {n*n:>4} tiles  ({ok} new, {skip} exist, {fail} fail)')
    print()
    print(f'Done. {ok} new, {skip} skipped, {fail} failed (of {TOTAL_TILES} total)')
    print(f'Saved to: {os.path.abspath(TILE_DIR)}')


if __name__ == '__main__':
    main()
