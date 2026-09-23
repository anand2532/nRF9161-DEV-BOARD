#!/usr/bin/env python3
"""Probe the y≈19.7 P0.15 east channel past nRESET / ENABLE."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402

B = pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def path_ok(r, pts):
    for a, b in zip(pts, pts[1:]):
        if not r.track_clear(a[0], a[1], b[0], b[1], B, W, NAME):
            return f"{a}->{b}: " + why(r, [a, b], B, W, NAME)
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    print("vias near y=19-22 x=40-110:")
    for v in r.vias:
        if 18.5 <= v["y"] <= 22.5 and 40 <= v["x"] <= 110:
            print(f"  {v['n']} ({v['x']:.2f},{v['y']:.2f}) r={v['r']:.2f}")
    print("B tracks crossing y=19.5-20.0 x=46-106:")
    for t in r.tracks:
        if t["ly"] != B:
            continue
        ymid = (t["y1"] + t["y2"]) / 2
        if 18.8 <= ymid <= 20.5 or (min(t["y1"], t["y2"]) <= 19.7 <= max(t["y1"], t["y2"])):
            if max(t["x1"], t["x2"]) >= 46 and min(t["x1"], t["x2"]) <= 106:
                print(f"  {t['n']} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")

    for y in (19.40, 19.50, 19.55, 19.60, 19.65, 19.70, 19.75, 19.80, 19.85, 19.90, 20.00, 18.40, 18.00, 17.50):
        pts = [(46.50, 21.20), (46.50, y), (106.00, y), (106.00, 20.60)]
        err = path_ok(r, pts)
        print(f"{'CLEAR' if err is None else 'BLOCK'} stub y={y:.2f}: {err or ''}")

    for y in (19.50, 19.70, 19.90):
        pts = [(41.75, 20.60), (46.50, 20.60), (46.50, y), (106.00, y), (106.00, 20.60)]
        err = path_ok(r, pts)
        print(f"{'CLEAR' if err is None else 'BLOCK'} from20.60 y={y:.2f}: {err or ''}")

    # waypoint with y=19.7 in the grid, start at stub
    xs = [round(x * 0.5, 2) for x in range(int(41.5 * 2), int(107 * 2))]
    ys = [round(y, 2) for y in [15.2, 16.0, 17.0, 18.0, 18.5, 19.0, 19.2, 19.4, 19.55, 19.7, 19.85, 20.0, 20.3, 20.6, 21.2, 21.7, 22.5, 23.1]]
    pts, L = waypoint_route(r, 46.50, 21.20, 106.00, 20.60, B, W, NAME, xs=xs, ys=ys)
    print("waypoint stub", None if pts is None else f"L={L:.1f} n={len(pts)} {path_ok(r, pts)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")


if __name__ == "__main__":
    main()
