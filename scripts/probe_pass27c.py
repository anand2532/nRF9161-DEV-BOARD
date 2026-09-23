#!/usr/bin/env python3
"""Waypoint B from existing vias; via_why dump for P0.14/P0.18."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_pass14 import reload, waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu

ADC_XS = [
    25.55, 26.20, 27.70, 28.50, 29.50, 30.90, 31.00, 32.20, 32.50, 33.40,
    34.00, 34.50, 35.50, 36.20, 36.50, 37.00, 38.00, 39.02, 39.25, 40.25,
    40.54, 40.70, 41.25, 41.56, 41.75, 42.25, 42.75, 43.08, 43.50, 44.10,
    45.15, 45.62, 46.50, 48.16, 50.70, 53.24, 55.78, 58.32,
]
ADC_YS = [
    19.20, 19.80, 20.60, 20.80, 21.20, 21.50, 21.80, 22.00, 22.40, 22.50,
    23.10, 23.95, 24.00, 24.60, 27.20, 30.80, 32.00, 36.00, 40.50, 41.10,
    43.50, 46.80, 50.00, 54.00, 58.80, 59.20, 59.80, 61.20, 62.00, 72.80,
    73.40, 74.00,
]


def wp(r, name, x1, y1, x2, y2):
    path, cost = waypoint_route(r, x1, y1, x2, y2, B, 0.18, name, xs=ADC_XS, ys=ADC_YS)
    if path is None:
        print(f"  {name} NO PATH ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})")
        return
    print(f"  {name} PATH L={cost:.2f} n={len(path)} {path[:8]} ... {path[-4:]}")


def via_grid(r, name, px, py):
    print(f"\n==== via_why {name} ====")
    hits = 0
    for dx in [-2.5, -2.1, -1.8, -1.5, -1.2, -0.6, 0, 0.6, 1.2, 1.5, 1.8, 2.1, 2.5]:
        for vy in [24.60, 24.30, 24.00, 23.70, 23.40, 23.10, 22.80, 22.40, 21.80, 20.80, 19.80]:
            vx = round(px + dx, 2)
            d = hypot(vx, vy, px, py)
            if d < 1.10 or d > 4.5:
                continue
            w50 = r.via_why(vx, vy, name, size=0.50, drill=0.30)
            w45 = r.via_why(vx, vy, name, size=0.45, drill=0.25)
            if w50 is None or w45 is None:
                sz = (0.50, 0.30) if w50 is None else (0.45, 0.25)
                f_cands = [
                    [(px, py), (px, vy), (vx, vy)],
                    [(px, py), (vx, py), (vx, vy)],
                    [(px, py), (px, 24.00), (vx, 24.00), (vx, vy)],
                ]
                fpath = next((pts for pts in f_cands if r.path_clear(pts, F, 0.18, name)), None)
                print(f"  VIA OK ({vx},{vy}) {sz} d={d:.2f} F={fpath}")
                hits += 1
            elif hits == 0 and abs(dx) < 0.01 and vy in (24.00, 23.10, 22.40):
                print(f"  via fail ({vx},{vy}) 0.50:{w50} 0.45:{w45}")
    print(f"  total via-ok printed above")


def main():
    board, r = reload()
    jobs = [
        ("P0.13", 42.75, 23.10, 38.00, 62.00),
        ("P0.13", 42.75, 23.95, 38.00, 62.00),
        ("P0.13", 42.75, 23.10, 38.00, 78.15),
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.16", 40.70, 20.80, 45.62, 74.00),
        ("P0.17", 40.25, 23.10, 48.16, 62.00),
        ("P0.17", 40.25, 23.95, 48.16, 73.40),
        ("P0.19", 39.25, 23.10, 53.24, 62.00),
        ("P0.20", 36.20, 20.80, 55.78, 62.00),
        ("P0.20", 36.20, 20.80, 55.78, 60.90),
        ("P0.15", 41.75, 23.10, 43.08, 62.00),  # should find existing-ish
    ]
    for name, x1, y1, x2, y2 in jobs:
        print(f"\n-- {name} ({x1},{y1})->({x2},{y2}) --")
        wp(r, name, x1, y1, x2, y2)
    via_grid(r, "P0.14", 42.25, 26.75)
    via_grid(r, "P0.18", 39.75, 26.75)

    # P0.11 F waypoint
    print("\n-- P0.11 F (44,28)->(48.62,28) --")
    path, cost = waypoint_route(r, 44.00, 28.00, 48.62, 28.00, F, 0.18, "P0.11")
    print("P0.11 F", None if path is None else (cost, path[:12]))

    # VIN_FILT 8.9mm — skip if >5 but probe F waypoint
    print("\n-- VIN_FILT F (55.35,13.30)->(53.20,21.90) --")
    path, cost = waypoint_route(r, 55.35, 13.30, 53.20, 21.90, F, 0.25, "VIN_FILT")
    print("VIN_FILT F", None if path is None else (cost, path[:12]))


if __name__ == "__main__":
    main()
