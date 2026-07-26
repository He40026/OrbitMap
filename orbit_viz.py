#!/usr/bin/env python3
"""
航天器轨道3D可视化工具
Orbit 3D Visualization Tool

输入近地点、远地点、倾角、升交点赤经、近地点幅角等轨道参数，
生成3D轨道模型和地面投影轨迹的交互式HTML文件。

Usage:
  python orbit_viz.py -p 200 -a 35786 -i 30 -r 45 -w 0
  python orbit_viz.py --interactive
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import argparse
import os
import sys

# ── Physical Constants ──────────────────────────────────────────────
MU = 398600.4418       # Earth gravitational parameter (km³/s²)
R_EARTH = 6378.137     # Earth equatorial radius (km)
OMEGA_E = 7.2921159e-5  # Earth rotation rate (rad/s)


# ── Keplerian Orbit Computation ─────────────────────────────────────
def solve_kepler(M, e, tol=1e-12):
    """Solve Kepler's equation M = E - e*sin(E) via Newton's method."""
    if e < 1e-12:
        return M.copy()
    E = M.copy()
    for _ in range(200):
        dE = (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
        E -= dE
        if np.max(np.abs(dE)) < tol:
            break
    return E


def compute_orbit(a, e, i_deg, raan_deg, w_deg, num_points=360, num_orbits=1):
    """
    Compute orbit position and time arrays in ECI frame.

    Returns
    -------
    x, y, z : ECI coordinates (km)
    r       : radius from Earth centre (km)
    t       : time from perigee passage (s)
    """
    M = np.linspace(0, 2 * np.pi * num_orbits, num_points * num_orbits)
    E = solve_kepler(M, e)
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2),
    )
    r = a * (1 - e * np.cos(E))

    # Position in orbital plane (perigee on +x)
    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)
    z_orb = np.zeros_like(nu)

    # 3-1-3 Euler rotation: orbital plane -> ECI
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


# ── Ground Track ─────────────────────────────────────────────────────
def compute_ground_track(x_eci, y_eci, z_eci, t):
    """
    Convert ECI positions to geodetic lat/lon accounting for Earth rotation.

    Returns (lat_deg, lon_deg).
    """
    theta = OMEGA_E * t
    x_ecef = x_eci * np.cos(theta) + y_eci * np.sin(theta)
    y_ecef = -x_eci * np.sin(theta) + y_eci * np.cos(theta)
    z_ecef = z_eci

    r_xy = np.sqrt(x_ecef ** 2 + y_ecef ** 2)
    lat = np.degrees(np.arctan2(z_ecef, r_xy))
    lon = np.degrees(np.arctan2(y_ecef, x_ecef))

    return lat, lon


def split_at_discontinuity(lats, lons, threshold=180.0):
    """Split lat/lon arrays at longitude wrap-around to avoid plot artifacts."""
    segments = []
    start = 0
    for i in range(1, len(lons)):
        if abs(lons[i] - lons[i - 1]) > threshold:
            segments.append((lats[start:i], lons[start:i]))
            start = i
    segments.append((lats[start:], lons[start:]))
    return segments


# ── 3D Earth Sphere ─────────────────────────────────────────────────
def earth_sphere_mesh(n=80):
    phi = np.linspace(0, np.pi, n)
    theta = np.linspace(0, 2 * np.pi, 2 * n)
    phi, theta = np.meshgrid(phi, theta)
    x = R_EARTH * np.sin(phi) * np.cos(theta)
    y = R_EARTH * np.sin(phi) * np.sin(theta)
    z = R_EARTH * np.cos(phi)
    return x, y, z


# ── Reference Elements ──────────────────────────────────────────────
def equator_ring(n=300):
    th = np.linspace(0, 2 * np.pi, n)
    return R_EARTH * np.cos(th), R_EARTH * np.sin(th), np.zeros(n)


def axis_line(length, n=2):
    v = np.linspace(0, length, n)
    return v, v * 0, v * 0


# ── Plotting ────────────────────────────────────────────────────────
def build_figure(x_3d, y_3d, z_3d, lats_gt, lons_gt,
                 a, e, perigee_alt, apogee_alt, incl, raan, argp,
                 period_min, output_path):
    """Build and save a single HTML figure with 3D orbit + ground-track map."""

    axes_lim = a * 1.15  # slightly bigger than apogee

    # ── 3D Scene ────────────────────────────────────────────────────
    ex, ey, ez = earth_sphere_mesh()
    earth = go.Surface(
        x=ex, y=ey, z=ez,
        colorscale=[[0.0, '#1B4F72'], [0.4, '#2E86C1'], [0.75, '#AED6F1'], [1.0, '#EAF2F8']],
        showscale=False,
        name='Earth',
        lighting=dict(ambient=0.6, diffuse=0.4, specular=0.05, roughness=0.9),
    )

    orbit_line = go.Scatter3d(
        x=x_3d, y=y_3d, z=z_3d,
        mode='lines',
        line=dict(color='#E74C3C', width=4),
        name='Orbit',
    )

    perigee_pt = go.Scatter3d(
        x=[x_3d[0]], y=[y_3d[0]], z=[z_3d[0]],
        mode='markers+text',
        marker=dict(color='#27AE60', size=6, symbol='circle'),
        text=['Perigee'],
        textposition='top center',
        textfont=dict(size=11, color='#27AE60'),
        name='Perigee',
        showlegend=True,
    )

    mid = len(x_3d) // 2
    apogee_pt = go.Scatter3d(
        x=[x_3d[mid]], y=[y_3d[mid]], z=[z_3d[mid]],
        mode='markers+text',
        marker=dict(color='#E67E22', size=6, symbol='circle'),
        text=['Apogee'],
        textposition='top center',
        textfont=dict(size=11, color='#E67E22'),
        name='Apogee',
        showlegend=True,
    )

    eqx, eqy, eqz = equator_ring()
    equator = go.Scatter3d(
        x=eqx, y=eqy, z=eqz,
        mode='lines',
        line=dict(color='white', width=1, dash='dot'),
        name='Equator',
        showlegend=False,
    )

    def coord_axes():
        L = axes_lim
        return [
            go.Scatter3d(x=[-L, L], y=[0, 0], z=[0, 0], mode='lines',
                         line=dict(color='red', width=1), showlegend=False),
            go.Scatter3d(x=[0, 0], y=[-L, L], z=[0, 0], mode='lines',
                         line=dict(color='green', width=1), showlegend=False),
            go.Scatter3d(x=[0, 0], y=[0, 0], z=[-L, L], mode='lines',
                         line=dict(color='blue', width=1), showlegend=False),
        ]

    # ── Ground Track (scattergeo) ───────────────────────────────────
    segments = split_at_discontinuity(lats_gt, lons_gt)
    gt_traces = []
    first_seg = True
    for seg_lat, seg_lon in segments:
        gt_traces.append(go.Scattergeo(
            lon=seg_lon, lat=seg_lat,
            mode='lines',
            line=dict(color='#E74C3C', width=2),
            name='Ground Track' if first_seg else None,
            showlegend=first_seg,
            legendgroup='gt',
        ))
        first_seg = False

    start_pt = go.Scattergeo(
        lon=[lons_gt[0]], lat=[lats_gt[0]],
        mode='markers',
        marker=dict(color='#27AE60', size=6),
        name='Start',
        showlegend=True,
    )

    # ── Subplot layout ──────────────────────────────────────────────
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.55, 0.45],
        specs=[[{'type': 'scene'}, {'type': 'geo'}]],
        subplot_titles=(
            '3D Orbit (ECI Frame)',
            'Ground Track (ECEF)',
        ),
        horizontal_spacing=0.02,
    )

    # Add 3D traces
    for trace in [earth, orbit_line, perigee_pt, apogee_pt, equator] + coord_axes():
        fig.add_trace(trace, row=1, col=1)

    # Add geo traces
    for trace in gt_traces + [start_pt]:
        fig.add_trace(trace, row=1, col=2)

    # ── Layout ──────────────────────────────────────────────────────
    info = (
        f"a={a:.0f} km | e={e:.4f} | "
        f"h<sub>p</sub>={perigee_alt:.0f} km | h<sub>a</sub>={apogee_alt:.0f} km<br>"
        f"i={incl:.1f}° | Ω={raan:.1f}° | ω={argp:.1f}° | T={period_min:.1f} min"
    )

    fig.update_layout(
        title=dict(
            text=f"<b>Orbit Visualization</b><br><sup>{info}</sup>",
            x=0.5,
            xanchor='center',
        ),
        scene=dict(
            xaxis=dict(title='X (km)', range=[-axes_lim, axes_lim], showbackground=False),
            yaxis=dict(title='Y (km)', range=[-axes_lim, axes_lim], showbackground=False),
            zaxis=dict(title='Z (km)', range=[-axes_lim, axes_lim], showbackground=False),
            aspectmode='data',
            camera=dict(eye=dict(x=1.3, y=1.3, z=1.0)),
        ),
        geo=dict(
            projection_type='equirectangular',
            showland=True,
            landcolor='#EAECEE',
            coastlinecolor='#85929E',
            showocean=True,
            oceancolor='#D6EAF8',
            showcountries=True,
            countrycolor='#BDC3C7',
            showframe=False,
            lonaxis=dict(showgrid=True, gridcolor='#D5D8DC', gridwidth=0.5),
            lataxis=dict(showgrid=True, gridcolor='#D5D8DC', gridwidth=0.5),
        ),
        width=1500,
        height=720,
        margin=dict(l=0, r=0, t=100, b=0),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='#CCC',
            borderwidth=1,
        ),
    )

    fig.write_html(output_path, include_plotlyjs='cdn')
    return fig


# ── Main ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Orbit 3D Visualization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orbit_viz.py -p 300 -a 300 -i 51.6 -r 0 -w 0     ISS-like LEO
  python orbit_viz.py -p 35786 -a 35786 -i 0 -r 0 -w 0    Geostationary
  python orbit_viz.py -p 500 -a 39800 -i 63.4 -r 45 -w 270  Molniya-like
  python orbit_viz.py --interactive                        Interactive input
        """,
    )
    parser.add_argument('-p', '--perigee', type=float,
                        help='Perigee altitude above Earth surface (km)')
    parser.add_argument('-a', '--apogee', type=float,
                        help='Apogee altitude above Earth surface (km)')
    parser.add_argument('-i', '--inclination', type=float,
                        help='Orbital inclination (degrees, 0–180)')
    parser.add_argument('-r', '--raan', type=float,
                        help='Right Ascension of Ascending Node (degrees, 0–360)')
    parser.add_argument('-w', '--arg_perigee', type=float, default=0.0,
                        help='Argument of perigee (degrees, default: 0)')
    parser.add_argument('--num-orbits', type=int, default=5,
                        help='Number of orbits for ground track (default: 5)')
    parser.add_argument('-o', '--output', type=str, default='orbit_visualization.html',
                        help='Output HTML file path')
    parser.add_argument('--no-browser', action='store_true',
                        help='Do not open in browser automatically')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive input mode')

    args = parser.parse_args()

    # ── Interactive mode ────────────────────────────────────────────
    if args.interactive or (args.perigee is None and args.apogee is None and
                            args.inclination is None and args.raan is None):
        print("=" * 55)
        print("  Orbit 3D Visualization Tool")
        print("=" * 55)
        print("Enter orbital parameters (press Enter for defaults):\n")

        def ask(prompt, default=None, vtype=float):
            d = f" [{default}]" if default is not None else ""
            while True:
                raw = input(f"  {prompt}{d}: ").strip()
                if raw == "" and default is not None:
                    return default
                try:
                    return vtype(raw)
                except ValueError:
                    print(f"    Please enter a valid {vtype.__name__}.")

        args.perigee = ask("Perigee altitude (km)", 300, float)
        args.apogee = ask("Apogee altitude (km)", 300, float)
        args.inclination = ask("Inclination (deg, 0–180)", 51.6, float)
        args.raan = ask("RAAN (deg, 0–360)", 0.0, float)
        args.arg_perigee = ask("Argument of perigee (deg)", 0.0, float)
        args.num_orbits = ask("Ground-track orbits to show", 5, int)

        if args.perigee is None or args.apogee is None or args.inclination is None or args.raan is None:
            print("Error: perigee, apogee, inclination, and raan are required.")
            sys.exit(1)

    # ── Validation ──────────────────────────────────────────────────
    if args.perigee > args.apogee:
        print("Warning: perigee > apogee, swapping values.")
        args.perigee, args.apogee = args.apogee, args.perigee

    if args.perigee < 80:
        print(f"Warning: perigee altitude {args.perigee:.0f} km is very low. "
              "Significant atmospheric drag expected.")

    if args.inclination < 0 or args.inclination > 180:
        print("Error: inclination must be 0–180 degrees.")
        sys.exit(1)

    # ── Compute orbital elements ────────────────────────────────────
    rp = R_EARTH + args.perigee
    ra = R_EARTH + args.apogee
    a = (rp + ra) / 2
    e = (ra - rp) / (ra + rp)
    T_s = 2 * np.pi * np.sqrt(a ** 3 / MU)
    T_min = T_s / 60

    print("\n" + "-" * 40)
    print("  Computed Orbital Elements")
    print("-" * 40)
    print(f"  Semi-major axis (a)    : {a:12.2f} km")
    print(f"  Eccentricity (e)       : {e:12.6f}")
    print(f"  Orbital period (T)     : {T_min:9.1f} min  ({T_min / 60:.2f} hr)")
    print(f"  Perigee radius         : {rp:12.2f} km")
    print(f"  Apogee radius          : {ra:12.2f} km")
    print("-" * 40)

    # ── Compute 3D orbit (1 orbit) ──────────────────────────────────
    print("\nComputing orbit positions ... ", end='', flush=True)
    x_3d, y_3d, z_3d, _, _ = compute_orbit(
        a, e, args.inclination, args.raan, args.arg_perigee,
        num_points=720, num_orbits=1,
    )

    # ── Compute ground track (multiple orbits) ──────────────────────
    x_gt, y_gt, z_gt, _, t_gt = compute_orbit(
        a, e, args.inclination, args.raan, args.arg_perigee,
        num_points=240, num_orbits=args.num_orbits,
    )
    lats_gt, lons_gt = compute_ground_track(x_gt, y_gt, z_gt, t_gt)
    print("done.")

    # ── Build & save figure ─────────────────────────────────────────
    print(f"Generating visualization ... ", end='', flush=True)
    build_figure(
        x_3d, y_3d, z_3d, lats_gt, lons_gt,
        a, e, args.perigee, args.apogee,
        args.inclination, args.raan, args.arg_perigee,
        T_min, args.output,
    )
    abs_path = os.path.abspath(args.output)
    print(f"done.\nSaved to: {abs_path}")

    # ── Open ────────────────────────────────────────────────────────
    if not args.no_browser:
        webbrowser.open('file://' + abs_path)
        print("Opened in browser.")


if __name__ == '__main__':
    main()
