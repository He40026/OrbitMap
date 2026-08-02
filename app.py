"""Flask web application for orbit visualization."""

import math
import os
from flask import Flask, render_template, request, jsonify
import numpy as np
import urllib.request
from orbit_calc import (
    compute_orbit, compute_ground_track,
    split_at_discontinuity, R_EARTH, MU
)

app = Flask(__name__)

TLE_GROUPS = {
    'gps-ops', 'beidou', 'weather', 'starlink',
    'iridium', 'galileo', 'glo-ops', 'oneweb',
}


def ensure_placeholder_tile():
    """Create the offline map fallback tile if it is missing."""
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(static_dir, 'placeholder.png')
    from PIL import Image, ImageDraw
    size = 256
    if not os.path.exists(path):
        img = Image.new('RGB', (size, size), '#1a4a7a')
        draw = ImageDraw.Draw(img)
        for i in range(0, size, 32):
            draw.line([(i, 0), (i, size)], fill='#2a5a8a', width=1)
            draw.line([(0, i), (size, i)], fill='#2a5a8a', width=1)
        draw.text((8, 8), 'Offline Map', fill='#aaddff')
        draw.text((8, 26), 'OrbitMap placeholder', fill='#88bbdd')
        img.save(path, 'PNG')
    favicon = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon):
        icon = Image.new('RGB', (16, 16), '#1a4a7a')
        ImageDraw.Draw(icon).ellipse([2, 2, 13, 13], fill='#00ffcc')
        icon.save(favicon, 'ICO')


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


@app.route('/api/compute', methods=['POST'])
def api_compute():
    data = request.get_json()

    perigee = float(data.get('perigee', 300))
    apogee = float(data.get('apogee', 300))
    inclination = float(data.get('inclination', 51.6))
    raan = float(data.get('raan', 0))
    arg_perigee = float(data.get('arg_perigee', 0))
    num_orbits = int(data.get('num_orbits', 5))
    mean_anomaly = float(data.get('mean_anomaly', 0))

    if perigee > apogee:
        perigee, apogee = apogee, perigee

    if inclination < 0 or inclination > 180:
        return jsonify({'error': 'Inclination must be 0-180 degrees'}), 400

    rp = R_EARTH + perigee
    ra = R_EARTH + apogee
    a = (rp + ra) / 2
    e = (ra - rp) / (ra + rp)
    T_s = 2 * np.pi * np.sqrt(a ** 3 / MU)
    T_min = T_s / 60

    x_3d, y_3d, z_3d, r_3d, t_3d = compute_orbit(
        a, e, inclination, raan, arg_perigee,
        num_points=360, num_orbits=1, M0_deg=mean_anomaly,
    )

    x_gt, y_gt, z_gt, _, t_gt = compute_orbit(
        a, e, inclination, raan, arg_perigee,
        num_points=200, num_orbits=num_orbits, M0_deg=mean_anomaly,
    )
    lats_gt, lons_gt = compute_ground_track(x_gt, y_gt, z_gt, t_gt)

    segments = split_at_discontinuity(lats_gt, lons_gt)

    return jsonify({
        'orbital_elements': {
            'semi_major_axis': round(float(a), 2),
            'eccentricity': round(float(e), 6),
            'period_min': round(float(T_min), 1),
            'perigee_radius': round(float(rp), 2),
            'apogee_radius': round(float(ra), 2),
            'perigee_alt': round(float(perigee), 1),
            'apogee_alt': round(float(apogee), 1),
            'mean_anomaly': round(float(mean_anomaly), 2),
        },
        'orbit_3d': {
            'x': [float(v) for v in x_3d],
            'y': [float(v) for v in y_3d],
            'z': [float(v) for v in z_3d],
        },
        'orbit_anim': {
            'x': [float(v) for v in x_gt],
            'y': [float(v) for v in y_gt],
            'z': [float(v) for v in z_gt],
        },
        'ground_track': {
            'segments': segments,
            'start_lat': float(lats_gt[0]),
            'start_lon': float(lons_gt[0]),
        },
        'num_orbits': num_orbits,
    })


@app.route('/api/fetch-tle')
def api_fetch_tle():
    catnr = request.args.get('catnr', '').strip()
    group = request.args.get('group', '').strip()
    if group:
        if group not in TLE_GROUPS:
            return jsonify({'error': 'Unknown TLE group'}), 400
        url = f'https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=TLE'
    else:
        if not catnr.isdigit():
            return jsonify({'error': 'Invalid NORAD ID'}), 400
        url = f'https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=TLE'
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            body = resp.read().decode('utf-8')
        return body, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'Fetch failed: {e}'}), 502


@app.route('/api/compute-constellation', methods=['POST'])
def api_compute_constellation():
    """Batch-compute orbits for a set of satellites (constellation mode)."""
    data = request.get_json(silent=True) or {}
    sats = data.get('satellites')
    if not isinstance(sats, list) or not sats:
        return jsonify({'error': 'satellites list is required'}), 400
    if len(sats) > 500:
        return jsonify({'error': 'too many satellites (max 500)'}), 400
    try:
        num_orbits = max(1, min(int(data.get('num_orbits', 2)), 4))
        points_per_orbit = max(30, min(int(data.get('points_per_orbit', 90)), 300))
    except (TypeError, ValueError):
        return jsonify({'error': 'invalid num_orbits / points_per_orbit'}), 400

    results = []
    max_period = 0.0
    for s in sats:
        try:
            name = str(s.get('name', 'SAT'))[:64]
            perigee = float(s.get('perigee', 400))
            apogee = float(s.get('apogee', 400))
            inclination = float(s.get('inclination', 51.6))
            raan = float(s.get('raan', 0))
            arg_perigee = float(s.get('arg_perigee', 0))
            mean_anomaly = float(s.get('mean_anomaly', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'invalid satellite parameters'}), 400

        if perigee > apogee:
            perigee, apogee = apogee, perigee
        rp = R_EARTH + perigee
        ra = R_EARTH + apogee
        a = (rp + ra) / 2
        e = (ra - rp) / (ra + rp)
        period = 2 * math.pi * math.sqrt(a ** 3 / MU)
        max_period = max(max_period, period)

        # Full closed ring for the 3D orbit line (independent of mean anomaly)
        rx, ry, rz, _, _ = compute_orbit(
            a, e, inclination, raan, arg_perigee,
            num_points=180, num_orbits=1, M0_deg=0,
        )
        # Multi-orbit animation arrays starting from the propagated mean anomaly
        ax, ay, az, _, ta = compute_orbit(
            a, e, inclination, raan, arg_perigee,
            num_points=points_per_orbit, num_orbits=num_orbits, M0_deg=mean_anomaly,
        )
        t_rel = (ta - ta[0]).tolist()
        results.append({
            'name': name,
            'orbital_elements': {
                'semi_major_axis': round(float(a), 2),
                'eccentricity': round(float(e), 6),
                'period_min': round(float(period / 60), 2),
                'perigee_alt': round(float(perigee), 1),
                'apogee_alt': round(float(apogee), 1),
            },
            'orbit_ring': {
                'x': [round(float(v), 3) for v in rx],
                'y': [round(float(v), 3) for v in ry],
                'z': [round(float(v), 3) for v in rz],
            },
            'anim': {
                'x': [round(float(v), 3) for v in ax],
                'y': [round(float(v), 3) for v in ay],
                'z': [round(float(v), 3) for v in az],
                't': [round(float(v), 3) for v in t_rel],
            },
        })

    return jsonify({
        'satellites': results,
        'num_orbits': num_orbits,
        'sim_duration': round(max_period * num_orbits, 2),
    })


if __name__ == '__main__':
    import webbrowser, threading
    ensure_placeholder_tile()
    if os.environ.get('ORBITMAP_OPEN_BROWSER', '1') != '0':
        threading.Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
