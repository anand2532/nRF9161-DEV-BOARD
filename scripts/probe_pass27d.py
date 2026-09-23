#!/usr/bin/env python3
"""Denser B waypoint; P0.14/18 F-to-via; P0.06 J9 parallel highway."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import reload, waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu

XS = [
    25.80, 26.20, 26.70, 27.20, 27.70, 28.20, 28.80, 29.40, 30.00, 30.40,
    31.50, 32.00, 33.00, 33.80, 34.80, 35.50, 36.50, 37.50, 38.00, 38.50,
    39.25, 40.25, 40.70, 41.25, 41.75, 42.25, 42.75, 43.08, 43.75, 44.10,
    44.50, 45.62, 46.50, 47.50, 48.16, 49.50, 50.70, 52.00, 53.24, 54.50,
    55.78, 57.00, 58.32, 60.00, 62.00,
]
YS = [
    17.60, 18.00, 18.50, 19.00, 19.40, 19.80, 20.20, 21.00, 21.60, 22.20,
    23.50, 24.60, 25.00, 26.00, 27.00, 28.50, 29.50, 31.50, 33.00, 35.00,
    38.00, 42.00, 44.50, 47.00, 49.00, 52.00, 55.00, 56.50, 57.50, 60.50,
    61.50, 62.00, 70.00, 72.80, 74.00,
]


def wp(r, name, x1, y1, x2, y2, layer=B, w=0.18):
    path, cost = waypoint_route(r, x1, y1, x2, y2, layer, w, name, xs=XS, ys=YS)
    if path is None:
        print(f"  NO {name} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})")
        return None
    print(f"  YES L={cost:.1f} n={len(path)} {path}")
    return path


def f_to(r, name, px, py, vx, vy):
    cands = [
        [(px, py), (px, vy), (vx, vy)],
        [(px, py), (vx, py), (vx, vy)],
        [(px, py), (px, 24.60), (vx, 24.60), (vx, vy)],
        [(px, py), (px, 25.00), (vx, 25.00), (vx, vy)],
        [(px, py), (px, 24.80), (vx, 24.80), (vx, vy)],
        [(px, py), (px, 22.20), (vx, 22.20), (vx, vy)],
        [(px, py), (px, 21.00), (vx, 21.00), (vx, vy)],
        [(px, py), (45.15, py), (45.15, vy), (vx, vy)],
        [(px, py), (44.00, py), (44.00, vy), (vx, vy)],
        [(px, py), (38.00, py), (38.00, vy), (vx, vy)],
        [(px, py), (36.50, py), (36.50, vy), (vx, vy)],
    ]
    for pts in cands:
        if r.path_clear(pts, F, 0.18, name):
            return pts
    return None


def scan(r, name, px, py, xs, ys):
    print(f"\n==== {name} via+F ====")
    out = []
    for vx in xs:
        for vy in ys:
            d = hypot(vx, vy, px, py)
            if d < 1.12 or d > 5.5:
                continue
            sz = (0.50, 0.30)
            w = r.via_why(vx, vy, name, size=0.50, drill=0.30)
            if w is not None:
                w = r.via_why(vx, vy, name, size=0.45, drill=0.25)
                sz = (0.45, 0.25)
                if w is not None:
                    continue
            fp = f_to(r, name, px, py, vx, vy)
            if not fp:
                continue
            print(f"  HIT via ({vx:.2f},{vy:.2f}) {sz} d={d:.2f} F={fp}")
            out.append((vx, vy, sz, fp))
    if not out:
        # show a few via_ok without F
        n = 0
        for vx in xs:
            for vy in ys:
                d = hypot(vx, vy, px, py)
                if d < 1.12 or d > 5.5:
                    continue
                w = r.via_why(vx, vy, name, size=0.50, drill=0.30)
                if w is None:
                    fp0 = [(px, py), (px, vy), (vx, vy)]
                    print(f"  via-only ({vx:.2f},{vy:.2f}) Fmiss {why(r, fp0, F, 0.18, name)}")
                    n += 1
                    if n >= 6:
                        return out
    return out


def p006(r):
    print("\n==== P0.06 J9 parallel to P0.04 ====")
    for yf in (79.20, 79.00, 78.95, 77.00, 76.40):
        pts = [(21.24, 77.20), (21.24, yf), (114.80, yf)]
        print(f"  F y={yf}", "OK" if r.path_clear(pts, F, 0.18, "P0.06") else why(r, pts, F, 0.18, "P0.06"))
    for xv, yv in [(21.24, 77.00), (21.24, 76.40), (25.55, 77.00), (25.55, 76.40), (22.50, 77.00)]:
        print(f"  via ({xv},{yv})", r.via_why(xv, yv, "P0.06", size=0.50, drill=0.30))
    # F from J12 area around P0.04 H y=77.20
    for yb in (76.40, 75.80, 73.40, 70.70):
        pts = [(21.24, 76.00), (21.24, yb), (110.00, yb)]
        print(f"  B y={yb}", "OK" if r.path_clear(pts, B, 0.18, "P0.06") else why(r, pts, B, 0.18, "P0.06"))


def main():
    board, r = reload()
    print("== waypoint existing vias ==")
    for job in [
        ("P0.13", 42.75, 23.10, 38.00, 62.00),
        ("P0.13", 42.75, 23.95, 38.00, 62.00),
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.17", 40.25, 23.10, 48.16, 62.00),
        ("P0.17", 40.25, 23.95, 48.16, 62.00),
        ("P0.19", 39.25, 23.10, 53.24, 62.00),
        ("P0.20", 36.20, 20.80, 55.78, 60.90),
    ]:
        print(f"-- {job[0]} --")
        wp(r, *job)

    scan(
        r,
        "P0.14",
        42.25,
        26.75,
        [x * 0.05 + 42.25 for x in range(-40, 60)],
        [24.80, 24.60, 24.40, 24.20, 23.80, 22.20, 21.60, 21.00, 19.80, 25.00, 25.20],
    )
    scan(
        r,
        "P0.18",
        39.75,
        26.75,
        [x * 0.05 + 39.75 for x in range(-80, 80)],
        [24.80, 24.60, 24.40, 24.20, 23.80, 22.20, 21.60, 21.00, 19.80, 25.00],
    )
    p006(r)

    # P0.11 via in gap then B
    print("\n==== P0.11 short to via island ====")
    scan(r, "P0.11", 44.00, 28.00, [45.15, 45.50, 46.00, 46.50, 44.80, 45.80], [26.20, 25.80, 25.40, 24.80, 29.40, 30.20, 27.20])


if __name__ == "__main__":
    main()
