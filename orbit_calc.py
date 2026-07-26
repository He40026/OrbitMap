"""Orbit computation module - extracted from orbit_viz.py"""

import numpy as np

MU = 398600.4418
R_EARTH = 6378.137
OMEGA_E = 7.2921159e-5


def solve_kepler(M, e, tol=1e-12):
    if e < 1e-12:
        return M.copy()
    E = M.copy()
    for _ in range(200):
        dE = (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
        E -= dE
        if np.max(np.abs(dE)) < tol:
            break
    return E


def compute_orbit(a, e, i_deg, raan_deg, w_deg, num_points=360, num_orbits=1, M0_deg=0):
    M0_rad = np.radians(M0_deg)
    M = np.linspace(M0_rad, M0_rad + 2 * np.pi * num_orbits, num_points * num_orbits)
    E = solve_kepler(M, e)
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2),
    )
    r = a * (1 - e * np.cos(E))

    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)
    z_orb = np.zeros_like(nu)

    i_rad, raan_rad, w_rad = np.radians([i_deg, raan_deg, w_deg])
    cw, sw = np.cos(w_rad), np.sin(w_rad)
    ci, si = np.cos(i_rad), np.sin(i_rad)
    co, so = np.cos(raan_rad), np.sin(raan_rad)

    positions = np.vstack([x_orb, y_orb, z_orb])
    Rz_w = np.array([[cw, -sw, 0], [sw, cw, 0], [0, 0, 1]])
    Rx_i = np.array([[1, 0, 0], [0, ci, -si], [0, si, ci]])
    Rz_O = np.array([[co, -so, 0], [so, co, 0], [0, 0, 1]])

    R = Rz_O @ Rx_i @ Rz_w
    eci = R @ positions

    n = np.sqrt(MU / a ** 3)
    t = M / n

    return eci[0], eci[1], eci[2], r, t


def compute_ground_track(x_eci, y_eci, z_eci, t):
    theta = OMEGA_E * t
    x_ecef = x_eci * np.cos(theta) + y_eci * np.sin(theta)
    y_ecef = -x_eci * np.sin(theta) + y_eci * np.cos(theta)
    z_ecef = z_eci

    r_xy = np.sqrt(x_ecef ** 2 + y_ecef ** 2)
    lat = np.degrees(np.arctan2(z_ecef, r_xy))
    lon = np.degrees(np.arctan2(y_ecef, x_ecef))

    return lat, lon


def split_at_discontinuity(lats, lons, threshold=180.0):
    segments = []
    start = 0
    for i in range(1, len(lons)):
        if abs(lons[i] - lons[i - 1]) > threshold:
            segments.append((lats[start:i].tolist(), lons[start:i].tolist()))
            start = i
    segments.append((lats[start:].tolist(), lons[start:].tolist()))
    return segments
