"""Flask web application for orbit visualization."""

from flask import Flask, render_template, request, jsonify
import numpy as np
import urllib.request
from orbit_calc import (
    compute_orbit, compute_ground_track,
    split_at_discontinuity, R_EARTH, MU
)

app = Flask(__name__)


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


@app.route('/')
def index():
    return render_template('index.html')


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
    if not catnr.isdigit():
        return jsonify({'error': 'Invalid NORAD ID'}), 400
    url = f'https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=TLE'
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            body = resp.read().decode('utf-8')
        return body, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'Fetch failed: {e}'}), 502


if __name__ == '__main__':
    import webbrowser, threading
    threading.Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
