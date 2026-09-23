#!/usr/bin/env python3
"""In-memory: rip P0.13 courtyard, search F.Cu escapes for P0.15. No save."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402
from rescue_final import rip_p013_courtyard, pok  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    rip_p013_courtyard(board)
    r.collect()
    start = (41.75, 23.10)
    goals = [
        (55.00, 8.00),
        (90.00, 8.00),
        (52.00, 12.00),
        (45.80, 41.50),
        (47.50, 42.50),
        (49.50, 45.00),
        (46.50, 39.80),
        (51.50, 38.00),
        (26.90, 18.00),
        (26.90, 12.00),
        (34.00, 14.00),
        (36.00, 12.00),
        (43.50, 14.00),
        (41.75, 14.00),
        (70.00, 45.00),
        (64.70, 45.00),
        (48.00, 48.00),
    ]
    print("via_why goals:")
    for g in goals:
        print(f"  {g} {r.via_why(g[0], g[1], NAME) or 'OK'}")

    xs = [round(x * 0.4, 2) for x in range(int(24 / 0.4), int(92 / 0.4))]
    ys = [round(y * 0.4, 2) for y in range(int(6 / 0.4), int(50 / 0.4))]
    for gx, gy in goals:
        pts, L = waypoint_route(r, start[0], start[1], gx, gy, F, W, NAME, xs=xs, ys=ys)
        if pts is None:
            print(f"WP FAIL {gx},{gy}")
            continue
        err = pok(r, pts, F, NAME)
        print(f"WP {'CLEAR' if err is None else 'BLOCK'} {gx},{gy} L={L:.1f} n={len(pts)} {err or ''}")
        if err is None:
            for p in pts:
                print(f"    {p[0]:.2f},{p[1]:.2f}")

    print("\nexplicit around U1 east/south:")
    expl = [
        [(41.75, 23.10), (41.75, 24.50), (45.80, 24.50), (45.80, 41.50)],
        [(41.75, 23.10), (41.75, 24.50), (45.50, 24.50), (45.50, 39.50), (47.50, 39.50), (47.50, 42.50)],
        [(41.75, 23.10), (41.75, 24.40), (45.90, 24.40), (45.90, 38.50), (51.50, 38.50)],
        [(41.75, 23.10), (41.75, 24.50), (26.90, 24.50), (26.90, 18.00)],
        [(41.75, 23.10), (41.75, 24.50), (32.00, 24.50), (32.00, 12.00), (36.00, 12.00)],
        [(41.75, 23.10), (43.20, 23.10), (43.20, 24.50), (45.80, 24.50), (45.80, 41.50)],
        [(41.75, 26.75), (41.75, 24.50), (45.80, 24.50), (45.80, 41.50)],
        [(41.75, 23.10), (41.75, 24.50), (45.80, 24.50), (45.80, 36.00), (64.70, 36.00), (64.70, 45.00)],
    ]
    for pts in expl:
        err = pok(r, pts, F, NAME)
        print(("CLEAR" if err is None else "BLOCK"), pts[-1], err or "")


if __name__ == "__main__":
    main()
