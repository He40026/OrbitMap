"""Fetch current CELESTRAK constellation TLEs and save a local preset snapshot.

Run this while online to refresh static/data/constellation_presets.json.
The app uses this snapshot as an offline fallback when the live fetch fails.
"""

import datetime
import json
import math
import os
import urllib.request

GROUPS = ['gps-ops', 'beidou', 'weather', 'starlink',
          'iridium-next', 'galileo', 'glo-ops', 'oneweb']
MAX_PER_GROUP = 200
MU = 398600.4418
RE = 6378.137
HEADERS = {'User-Agent': 'OrbitMap-preset-builder/1.0 (educational)'}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, 'static', 'data', 'constellation_presets.json')


def fetch_text(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def parse_tle(name, line1, line2):
    """Parse a two-line TLE into the same fields the frontend uses."""
    inclination = float(line2[8:16])
    raan = float(line2[17:25])
    e = float('0.' + line2[26:33])
    arg_perigee = float(line2[34:42])
    mean_anomaly = float(line2[43:51])
    mean_motion = float(line2[52:63])

    epoch_str = line1[18:32]
    epoch_year = 2000 + int(epoch_str[:2])
    epoch_day = float(epoch_str[2:])
    epoch = (datetime.datetime(epoch_year, 1, 1, tzinfo=datetime.timezone.utc)
             + datetime.timedelta(days=epoch_day - 1))

    n_rad = mean_motion * 2 * math.pi / 86400
    a = (MU / (n_rad * n_rad)) ** (1 / 3)
    perigee = a * (1 - e) - RE
    apogee = a * (1 + e) - RE

    return {
        'name': name,
        'perigee': round(perigee, 3),
        'apogee': round(apogee, 3),
        'inclination': round(inclination, 6),
        'raan': round(raan, 6),
        'argPerigee': round(arg_perigee, 6),
        'meanAnomaly': round(mean_anomaly, 6),
        'meanMotion': round(mean_motion, 8),
        'epoch': epoch.isoformat(),
        'e': e,
        'a': round(a, 3),
    }


def parse_tle_file(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sats = []
    i = 0
    while i < len(lines):
        name = ''
        l1 = l2 = ''
        if lines[i].startswith('1 ') and i + 1 < len(lines) and lines[i + 1].startswith('2 '):
            l1, l2 = lines[i], lines[i + 1]
            i += 2
        elif (i + 2 < len(lines) and lines[i + 1].startswith('1 ')
              and lines[i + 2].startswith('2 ')):
            name, l1, l2 = lines[i], lines[i + 1], lines[i + 2]
            i += 3
        else:
            i += 1
            continue
        try:
            sat = parse_tle(name or f'SAT-{len(sats) + 1}', l1, l2)
            sats.append(sat)
        except (ValueError, IndexError):
            continue
    return sats


def sample_evenly(sats, max_n):
    if len(sats) <= max_n:
        return sats
    out = []
    for i in range(max_n):
        out.append(sats[int(i * len(sats) / max_n)])
    return out


def main():
    print('Fetching constellation TLE snapshots from CELESTRAK...')
    groups = {}
    for group in GROUPS:
        url = f'https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=TLE'
        text = fetch_text(url)
        sats = sample_evenly(parse_tle_file(text), MAX_PER_GROUP)
        groups[group] = {
            'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'satellites': sats,
        }
        print(f'  {group}: {len(sats)} satellites')

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    payload = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source': 'https://celestrak.org (TLE snapshot)',
        'groups': groups,
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f'Saved: {OUT_PATH}')


if __name__ == '__main__':
    main()
