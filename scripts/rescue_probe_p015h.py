#!/usr/bin/env python3
"""Ray-scan F.Cu and B.Cu from P0.15 via/pad after P0.13 courtyard rip. No save."""
from __future__ import annotations

import math
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import rip_p013_courtyard, pok  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
NAME = "P0.15"


def rays(r, x0, y0, layer, dist=8.0):
    hits = []
    for deg in range(0, 360, 10):
        rad = math.radians(deg)
        x1 = x0 + dist * math.cos(rad)
        y1 = y0 + dist * math.sin(rad)
        err = pok(r, [(x0, y0), (x1, y1)], layer, NAME)
        hits.append((deg, err is None, err))
    return hits


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    rip_p013_courtyard(board)
    r.collect()
    for label, xy, layer in (
        ("via F", (41.75, 23.10), F),
        ("via B", (41.75, 23.10), B),
        ("pad F", (41.75, 26.75), F),
        ("stub 46.5,21.2 B", (46.50, 21.20), B),
        ("stub 41.75,20.6 B", (41.75, 20.60), B),
    ):
        print(f"\n==== {label} {xy} ====")
        for deg, ok, err in rays(r, xy[0], xy[1], layer, 6.0):
            if ok:
                print(f"  CLEAR {deg:3d}")
            elif deg % 30 == 0:
                print(f"  BLOCK {deg:3d} {err}")

    # short steps
    print("\n==== short F steps from via ====")
    for dx, dy in [
        (0, 0.6), (0, 1.2), (0, -0.6), (0, -1.2),
        (0.6, 0), (1.2, 0), (-0.6, 0), (-1.2, 0),
        (0.6, 0.6), (0.8, 1.4), (1.4, 1.8), (2.0, 1.6),
        (-0.8, 1.4), (-1.5, 1.5), (0.5, -1.5), (1.5, -0.8),
        (3.0, 1.8), (4.0, 1.4), (3.5, -2.0),
    ]:
        pts = [(41.75, 23.10), (41.75 + dx, 23.10 + dy)]
        err = pok(r, pts, F, NAME)
        print(("CLEAR" if err is None else "BLOCK"), f"d=({dx},{dy})", err or "")


if __name__ == "__main__":
    main()
