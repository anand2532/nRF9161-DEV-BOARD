#!/usr/bin/env python3
"""P0.06 J9 path; courtyard F escapes; north-highway B for ADC."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload, waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def chk(r, pts, ly, name, w=0.18):
    ok = r.path_clear(pts, ly, w, name)
    lab = "F" if ly == F else "B"
    if ok:
        print(f"  {lab} CLEAR", pts)
        return True
    print(f"  {lab} {why(r, pts, ly, w, name)}")
    return False


def main():
    board, r = reload()

    print("==== P0.14 courtyard F east then via ====")
    px, py = 42.25, 26.75
    for vy in (25.40, 25.20, 25.00, 24.80, 24.60):
        for vx in (44.80, 45.15, 45.50, 46.00, 46.50, 47.00):
            w = r.via_why(vx, vy, "P0.14", size=0.50, drill=0.30)
            sz = (0.50, 0.30)
            if w:
                w = r.via_why(vx, vy, "P0.14", size=0.45, drill=0.25)
                sz = (0.45, 0.25)
            fpts = [(px, py), (px, vy), (vx, vy)]
            f2 = [(px, py), (vx, py), (vx, vy)]
            f3 = [(px, py), (px, 25.50), (vx, 25.50), (vx, vy)]
            fpath = None
            for pts in (fpts, f2, f3):
                if r.path_clear(pts, F, 0.18, "P0.14"):
                    fpath = pts
                    break
            if w is None and fpath:
                print(f"  HIT via ({vx},{vy}) {sz} F={fpath}")
            elif w is None:
                print(f"  via OK ({vx},{vy}) {sz} Fmiss {why(r, fpts, F, 0.18, 'P0.14')}")

    print("\n==== P0.18 courtyard F west/east then via ====")
    px, py = 39.75, 26.75
    for vy in (25.40, 25.20, 25.00, 24.80, 24.60):
        for vx in (36.20, 36.50, 37.00, 37.50, 38.00, 38.50, 41.50, 43.00, 44.50, 45.50):
            w = r.via_why(vx, vy, "P0.18", size=0.50, drill=0.30)
            sz = (0.50, 0.30)
            if w:
                w = r.via_why(vx, vy, "P0.18", size=0.45, drill=0.25)
                sz = (0.45, 0.25)
            fpts = [(px, py), (px, vy), (vx, vy)]
            f3 = [(px, py), (px, 25.50), (vx, 25.50), (vx, vy)]
            fpath = None
            for pts in (fpts, f3, [(px, py), (vx, py), (vx, vy)]):
                if r.path_clear(pts, F, 0.18, "P0.18"):
                    fpath = pts
                    break
            if w is None and fpath:
                print(f"  HIT via ({vx},{vy}) {sz} F={fpath}")
            elif w is None:
                print(f"  via OK ({vx},{vy}) {sz} Fmiss {why(r, fpts, F, 0.18, 'P0.18')}")

    print("\n==== ADC B north highway from existing vias ====")
    xs = [26.2, 26.7, 27.7, 28.5, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.75, 45.62, 48.16, 50.7, 55.78, 60, 70, 80, 90, 100, 108]
    ys = [16.0, 16.8, 17.5, 18.0, 18.5, 19.0, 19.5, 58.5, 59.2, 60.5, 61.2, 62.0]
    for name, x1, y1, x2, y2 in [
        ("P0.13", 42.75, 23.10, 38.00, 62.00),
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.17", 40.25, 23.10, 48.16, 62.00),
    ]:
        path, cost = waypoint_route(r, x1, y1, x2, y2, B, 0.18, name, xs=xs, ys=ys)
        print(name, "NO" if path is None else f"L={cost:.1f} {path}")

    print("\n==== P0.13 extend F north then new via + B ====")
    for vx, vy in [(42.75, 19.00), (44.50, 19.00), (40.00, 19.00), (38.00, 19.00), (42.75, 18.00), (45.50, 19.00), (47.00, 19.00)]:
        w = r.via_why(vx, vy, "P0.13", size=0.50, drill=0.30)
        print(f"  via ({vx},{vy})", w)
        if w is None:
            fpts = [(42.75, 23.10), (42.75, vy), (vx, vy)]
            print("   F", "OK" if r.path_clear(fpts, F, 0.18, "P0.13") else why(r, fpts, F, 0.18, "P0.13"))

    print("\n==== P0.06 J9 from J12 B island ====")
    for vx, vy in [
        (14.90, 77.80),
        (8.00, 77.80),
        (4.50, 77.80),
        (4.50, 77.20),
        (10.00, 77.80),
        (12.00, 77.80),
        (21.24, 78.00),
        (19.00, 77.80),
        (15.50, 77.80),
        (6.00, 77.80),
        (3.50, 77.50),
    ]:
        print(f"  via ({vx},{vy}) 0.50", r.via_why(vx, vy, "P0.06", size=0.50, drill=0.30))
        print(f"  via ({vx},{vy}) 0.45", r.via_why(vx, vy, "P0.06", size=0.45, drill=0.25))

    b_cands = [
        [(21.24, 74.00), (4.50, 74.00), (4.50, 77.80)],
        [(21.24, 74.00), (8.00, 74.00), (8.00, 77.80)],
        [(21.24, 74.00), (6.00, 74.00), (6.00, 77.80)],
        [(21.24, 74.00), (14.90, 74.00), (14.90, 77.80)],
        [(21.24, 76.00), (4.50, 76.00), (4.50, 77.80)],
    ]
    for pts in b_cands:
        chk(r, pts, B, "P0.06")

    f_cands = [
        [(4.50, 77.80), (4.50, 79.20), (114.80, 79.20)],
        [(8.00, 77.80), (8.00, 79.20), (114.80, 79.20)],
        [(4.50, 77.80), (4.50, 79.20), (114.80, 79.20), (114.80, 54.00)],
        [(6.00, 77.80), (6.00, 79.20), (115.20, 79.20)],
    ]
    for pts in f_cands:
        chk(r, pts, F, "P0.06")

    print("\n==== P0.06 SE drop like P0.04 offset ====")
    for xv in (107.70, 109.20, 110.00, 111.20, 112.40, 114.00, 115.00):
        for yv in (54.00, 52.80, 50.00, 48.00, 47.20):
            w = r.via_why(xv, yv, "P0.06", size=0.50, drill=0.30)
            if w is None:
                print(f"  SE via OK ({xv},{yv})")
    # J9.1 (116, 8)
    for xv in (113.20, 114.00, 114.40, 112.50, 111.00):
        for yv in (12.00, 10.00, 36.00, 38.00, 42.00):
            w = r.via_why(xv, yv, "P0.06", size=0.50, drill=0.30)
            if w is None:
                print(f"  NE via OK ({xv},{yv})")


if __name__ == "__main__":
    main()
