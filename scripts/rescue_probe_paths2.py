#!/usr/bin/env python3
"""Probe refined ADC first-jog paths, VIN_FILT B underpass, astar_b."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import existing_via, pok  # noqa: E402

B, F = pcbnew.B_Cu, pcbnew.F_Cu


def show(r, name, paths, layer, nshow=8):
    for i, pts in enumerate(paths):
        err = pok(r, pts, layer, name)
        if err is None:
            print(f"  CLEAR {name} i={i} {pts}")
            return pts
        if i < nshow:
            print(f"  BLOCK {name} i={i} {err}")
    print(f"  none {name}")
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("== VIN_FILT B underpass ==")
    show(
        r,
        "VIN_FILT",
        [
            [(51.90, 21.90), (51.90, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (55.35, 21.90), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 16.60), (55.35, 16.60), (55.35, 13.30)],
            [(53.70, 22.40), (53.70, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (47.00, 21.90), (47.00, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 24.80), (44.50, 24.80), (44.50, 12.20), (55.35, 12.20), (55.35, 13.30)],
        ],
        B,
    )

    print("== VIN_FILT F south-first ==")
    show(
        r,
        "VIN_FILT",
        [
            [(53.20, 21.90), (53.20, 20.40), (46.20, 20.40), (46.20, 13.30), (55.35, 13.30)],
            [(53.20, 21.90), (53.20, 20.20), (45.00, 20.20), (45.00, 12.40), (55.35, 12.40), (55.35, 13.30)],
            [(53.20, 21.90), (53.20, 23.50), (45.00, 23.50), (45.00, 12.40), (55.35, 12.40), (55.35, 13.30)],
        ],
        F,
    )

    specs = {
        "P0.16": ((40.70, 20.80), (45.62, 62.00)),
        "P0.17": ((40.25, 23.95), (48.16, 62.00)),
        "P0.19": ((39.25, 23.10), (53.24, 62.00)),
        "P0.20": ((36.20, 20.80), (55.78, 62.00)),
    }
    for name, ((sx, sy), (dx, dy)) in specs.items():
        print(f"== {name} first-jog east ==")
        paths = []
        for gx in (42.4, 43.5, 44.5, 46.0, 47.5, 49.0):
            for y in (16.60, 17.40, 18.20, 14.00, 12.50, 10.20, 8.40, 6.80):
                for x in (64.70, 86.00, 96.00, 107.20, 111.20):
                    paths.append([(sx, sy), (gx, sy), (gx, y), (x, y), (x, 60.50), (dx, 60.50), (dx, dy)])
        # west after south jog
        for yb in (24.90, 27.20):
            for col in (34.50, 29.50, 27.40):
                paths.append([(sx, sy), (sx, yb), (col, yb), (col, 58.80), (dx, 58.80), (dx, dy)])
        show(r, name, paths, B, nshow=4)

        print(f"  astar_b {name}...")
        r.ok = 0
        # dry: occupancy only by calling astar but that COMMITS. skip commit - monkeypatch later
        # just report we will try in commit script

    print("== P0.14 via+F then B ==")
    site = (43.35, 24.84)
    pad = (42.25, 26.75)
    print("  via_ok", r.via_ok(*site, "P0.14"), "F pad-via", pok(r, [pad, site], F, "P0.14"))
    print("  F L", pok(r, [pad, (site[0], pad[1]), site], F, "P0.14"))
    print("  F L2", pok(r, [pad, (pad[0], site[1]), site], F, "P0.14"))


if __name__ == "__main__":
    main()
