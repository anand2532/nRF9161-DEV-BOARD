#!/usr/bin/env python3
"""P0.06 J9 four-via hop past P0.04 / VDD_GPIO walls."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def chk(r, pts, ly, name):
    ok = r.path_clear(pts, ly, 0.18, name)
    print(("  CLEAR " if ok else "  BLOCK " + why(r, pts, ly, 0.18, name) + " "), pts)
    return ok


def vwhy(r, x, y, name):
    for s, d in ((0.50, 0.30), (0.45, 0.25)):
        w = r.via_why(x, y, name, size=s, drill=d)
        print(f"  via ({x:.2f},{y:.2f}) {s:.2f}/{d:.2f}", w)
        if w is None:
            return True
    return False


def main():
    board, r = reload()
    x = 113.20
    vias = [
        (14.90, 77.80),
        (115.50, 55.50),
        (107.40, 47.20),
        (x, 36.00),
        (x, 20.20),
        (x, 18.90),
        (x, 17.50),
        (x, 14.50),
    ]
    print("==== vias ====")
    for a, b in vias:
        vwhy(r, a, b, "P0.06")
    # alts for tight pair
    for y in (18.95, 18.85, 18.80, 18.70, 17.60, 17.40, 17.30):
        vwhy(r, x, y, "P0.06")
    for xx in (112.80, 113.00, 113.50, 112.50, 114.00):
        print(f" -- x={xx}")
        for y in (20.20, 18.90, 17.50, 14.50):
            vwhy(r, xx, y, "P0.06")

    print("\n==== full route x=113.20 ====")
    routes = [
        ([(21.24, 74.00), (14.90, 74.00), (14.90, 77.80)], B),
        ([(14.90, 77.80), (14.90, 79.20), (115.50, 79.20), (115.50, 55.50)], F),
        ([(115.50, 55.50), (107.40, 55.50), (107.40, 47.20)], B),
        ([(107.40, 47.20), (113.20, 47.20), (113.20, 36.00)], F),
        ([(113.20, 36.00), (113.20, 20.20)], B),
        ([(113.20, 20.20), (113.20, 18.90)], F),
        ([(113.20, 18.90), (113.20, 17.50)], B),
        ([(113.20, 17.50), (113.20, 14.50)], F),
        ([(113.20, 14.50), (113.20, 8.40), (116.00, 8.40), (116.00, 8.00)], B),
    ]
    for pts, ly in routes:
        chk(r, pts, ly, "P0.06")

    print("\n==== F 20.20-18.90 / B 18.90-17.50 alts ====")
    for y1, y2 in [(20.20, 18.90), (20.20, 18.85), (20.30, 18.90), (20.40, 19.00)]:
        chk(r, [(x, 36.00), (x, y1)], B, "P0.06")
        chk(r, [(x, y1), (x, y2)], F, "P0.06")


if __name__ == "__main__":
    main()
