#!/usr/bin/env python3
"""Find F.Cu path from P0.15 via to (55,8) / (52,12) / (50,14)."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def pok(r, pts, layer):
    for a, b in zip(pts, pts[1:]):
        if hypot(a[0], a[1], b[0], b[1]) < 0.03:
            continue
        if not r.track_clear(a[0], a[1], b[0], b[1], layer, W, NAME):
            return f"{a}->{b} " + why(r, [a, b], layer, W, NAME)
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    goals = [(55.00, 8.00), (52.00, 12.00), (50.00, 14.00), (60.00, 12.00), (90.00, 8.00)]
    fpaths = []
    for gx, gy in goals:
        fpaths.append([(41.75, 23.10), (41.75, 20.50), (gx, 20.50), (gx, gy)])
        fpaths.append([(41.75, 23.10), (41.75, 24.60), (gx, 24.60), (gx, gy)])
        fpaths.append([(41.75, 23.10), (43.50, 23.10), (43.50, gy), (gx, gy)])
        fpaths.append([(41.75, 23.10), (41.75, 21.00), (43.80, 21.00), (43.80, gy), (gx, gy)])
        fpaths.append([(41.75, 23.10), (41.75, 20.00), (46.00, 20.00), (46.00, gy), (gx, gy)])
        fpaths.append([(41.75, 23.10), (41.75, 19.20), (47.20, 19.20), (47.20, gy), (gx, gy)])
        fpaths.append([(41.75, 26.75), (41.75, 25.40), (45.50, 25.40), (45.50, gy), (gx, gy)])
        fpaths.append([(41.75, 26.75), (41.75, 25.40), (46.80, 25.40), (46.80, 16.00), (gx, 16.00), (gx, gy)])
    print("F.Cu to north vias:")
    for pts in fpaths:
        err = pok(r, pts, F)
        if err is None:
            print("CLEAR F", pts)
        # else skip noise

    print("\nwaypoint F 41.75,23.10 -> 55,8")
    xs = [round(x, 2) for x in [41.75, 42.4, 43.2, 43.8, 44.5, 45.5, 46.5, 47.2, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 55.0, 58.0, 60.0]]
    ys = [round(y, 2) for y in [7.2, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 16.0, 18.0, 19.2, 20.0, 20.5, 21.0, 21.5, 22.0, 23.1, 24.0, 24.6, 25.4, 26.75]]
    pts, L = waypoint_route(r, 41.75, 23.10, 55.00, 8.00, F, W, NAME, xs=xs, ys=ys)
    print(None if pts is None else f"L={L:.1f} {pok(r, pts, F)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")
    pts, L = waypoint_route(r, 41.75, 23.10, 52.00, 12.00, F, W, NAME, xs=xs, ys=ys)
    print("to 52,12", None if pts is None else f"L={L:.1f} {pok(r, pts, F)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")
    pts, L = waypoint_route(r, 41.75, 26.75, 55.00, 8.00, F, W, NAME, xs=xs, ys=ys)
    print("from pad to 55,8", None if pts is None else f"L={L:.1f} {pok(r, pts, F)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")

    print("\nB.Cu y=7.2 from other x:")
    for vx, vy in [(55, 8), (52, 12), (50, 14), (60, 12), (90, 8), (43.5, 14), (41.75, 14), (34, 14), (32, 16)]:
        pts = [(vx, vy), (vx, 7.20), (106.00, 7.20), (106.00, 20.60)]
        err = pok(r, pts, B)
        print(("CLEAR" if err is None else "BLOCK"), (vx, vy), err or "")


if __name__ == "__main__":
    main()
