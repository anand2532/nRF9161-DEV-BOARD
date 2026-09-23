#!/usr/bin/env python3
"""Probe P0.15 F.Cu north/east escape to a new via on existing B.Cu x=106."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def path_ok(r, pts, layer):
    for a, b in zip(pts, pts[1:]):
        if hypot(a[0], a[1], b[0], b[1]) < 0.03:
            continue
        if not r.track_clear(a[0], a[1], b[0], b[1], layer, W, NAME):
            return f"{a}->{b}: " + why(r, [a, b], layer, W, NAME)
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    print("F.Cu foreign near north of U1 (x=35-110 y=4-27):")
    n = 0
    for t in r.tracks:
        if t["ly"] != F or t["n"] == NAME:
            continue
        mx, my = (t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2
        if 35 <= mx <= 110 and 4 <= my <= 27:
            print(f"  {t['n']} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")
            n += 1
            if n >= 40:
                print("  ...")
                break
    print("via_ok samples:")
    for xy in [(106.00, 20.60), (106.00, 18.00), (105.20, 19.00), (104.50, 21.50), (100.00, 18.50), (60.00, 12.00), (50.00, 14.00), (48.00, 16.00), (41.75, 14.00), (41.75, 18.00), (55.00, 8.00), (70.00, 8.00), (90.00, 8.00), (106.00, 8.00)]:
        w = r.via_why(xy[0], xy[1], NAME, pwr=False)
        print(f"  via {xy} {w or 'OK'}")

    cands = []
    for y in (8.00, 9.20, 10.40, 11.60, 12.80, 14.00, 16.50, 18.00, 22.00, 24.20):
        cands.append((f"F y={y:.2f} from via", [(41.75, 23.10), (41.75, y), (106.00, y), (106.00, 20.60)]))
        cands.append((f"F y={y:.2f} from pad", [(41.75, 26.75), (41.75, y), (106.00, y), (106.00, 20.60)]))
    cands.append(("F east pad y=24.8", [(41.75, 26.75), (41.75, 24.80), (106.00, 24.80), (106.00, 20.60)]))
    cands.append(("F east 48,12", [(41.75, 23.10), (41.75, 12.00), (48.00, 12.00), (106.00, 12.00), (106.00, 20.60)]))
    cands.append(("F jog J8", [(41.75, 23.10), (41.75, 8.00), (48.50, 8.00), (48.50, 3.50), (106.00, 3.50), (106.00, 20.60)]))

    print("\n==== explicit F.Cu ====")
    for label, pts in cands:
        # F.Cu only for segments; last drop to 20.60 at x=106 may be F onto a via site
        err = path_ok(r, pts, F)
        if err is None:
            print("CLEAR", label)
        else:
            if "y=8.00" in label or "y=12.00" in label or "y=10.40" in label or "J8" in label or "24.8" in label:
                print("BLOCK", label, err)

    print("\n==== F waypoint via->106,8 ====")
    xs = [round(x, 2) for x in [41.75, 43, 45, 48, 50, 52, 55, 60, 70, 80, 90, 100, 106]]
    ys = [round(y, 2) for y in [3.5, 4.5, 5.5, 6.5, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 16.0, 18.0, 20.6, 23.1, 24.8, 26.75]]
    pts, L = waypoint_route(r, 41.75, 23.10, 106.00, 8.00, F, W, NAME, xs=xs, ys=ys)
    print("to 106,8", None if pts is None else f"L={L:.1f} {path_ok(r, pts, F)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")
    pts, L = waypoint_route(r, 41.75, 23.10, 106.00, 20.60, F, W, NAME, xs=xs, ys=ys)
    print("to 106,20.60 F", None if pts is None else f"L={L:.1f} {path_ok(r, pts, F)}")
    if pts:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")


if __name__ == "__main__":
    main()
