"""Download map tiles for offline use (zoom 0-3, ~85 tiles)."""
import os
import time
import urllib.request

TILE_DIR = os.path.join('static', 'tiles', 'osm')
ZOOM_LEVELS = range(0, 4)
HEADERS = {'User-Agent': 'OrbitVisualizer/1.0 (educational project)'}


def download_tile(z, x, y):
    url = f'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    dir_path = os.path.join(TILE_DIR, str(z), str(x))
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f'{y}.png')
    if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
        return 'skip'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as src:
            data = src.read()
        with open(file_path, 'wb') as f:
            f.write(data)
        return 'ok'
    except Exception as e:
        print(f'  [{z}/{x}/{y}] {e}')
        return 'fail'


def main():
    print('Downloading OSM tiles for offline use...')
    print(f'Zoom levels: {list(ZOOM_LEVELS)}')
    total = sum((2 ** z) ** 2 for z in ZOOM_LEVELS)
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
                time.sleep(0.1)
        print(f'  z={z}: {n*n} tiles processed ({ok} ok, {skip} exist, {fail} fail)')
    print(f'Done. {ok} new, {skip} skipped, {fail} failed (of {total} total)')


if __name__ == '__main__':
    main()
