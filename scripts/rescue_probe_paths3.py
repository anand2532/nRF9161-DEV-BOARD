#!/usr/bin/env python3
"""Leave via row on a different Y, then east/north. VIN_FILT west of ENABLE."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402

B = pcbnew.B_Cu


def show(r, name, paths, nshow=12):
    for i, pts in enumerate(paths):
        err = pok(r, pts, B, name)
        if err is None:
            print(f"  CLEAR {name} i={i} {pts}")
            return pts
        if i < nshow:
            print(f"  BLOCK {name} i={i} {err}")
    print(f"  none {name} tried={len(paths)}")
    return None


def adc_from(sx, sy, dx, dy):
    paths = []
    # north jog then east
    for ny in (20.15, 19.60, 18.80, 17.40, 16.60):
        if ny >= sy:
            continue
        for gx in (43.0, 44.5, 46.2, 47.8, 49.5):
            for x in (64.7, 86.0, 96.0, 107.2, 111.2):
                paths.append([(sx, sy), (sx, ny), (gx, ny), (gx, 16.60 if ny != 16.60 else ny), (x, 16.60 if ny != 16.60 else ny), (x, 60.50), (dx, 60.50), (dx, dy)])
    # south jog then east (avoid via-row)
    for sy2 in (21.50, 22.20, 24.80, 25.40, 27.20):
        if sy2 <= sy:
            continue
        for gx in (43.0, 44.5, 46.2, 47.8, 49.5, 52.0):
            for x in (64.7, 86.0, 107.2, 111.2):
                paths.append([(sx, sy), (sx, sy2), (gx, sy2), (gx, 16.60), (x, 16.60), (x, 60.50), (dx, 60.50), (dx, dy)])
                paths.append([(sx, sy), (sx, sy2), (gx, sy2), (x, sy2), (x, 60.50), (dx, 60.50), (dx, dy)])
    # south then west column
    for sy2 in (24.80, 27.20, 28.40):
        for col in (34.50, 33.00, 29.40, 27.40):
            paths.append([(sx, sy), (sx, sy2), (col, sy2), (col, 58.80), (dx, 58.80), (dx, dy)])
    return paths


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("== VIN_FILT west of ENABLE ==")
    show(
        r,
        "VIN_FILT",
        [
            [(51.90, 21.90), (49.20, 21.90), (49.20, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (49.20, 21.90), (49.20, 16.60), (55.35, 16.60), (55.35, 13.30)],
            [(51.90, 21.90), (48.00, 21.90), (48.00, 12.50), (55.35, 12.50), (55.35, 13.30)],
            [(51.90, 21.90), (50.20, 21.90), (50.20, 16.60), (58.50, 16.60), (58.50, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (49.20, 21.90), (49.20, 19.50), (58.50, 19.50), (58.50, 13.30), (55.35, 13.30)],
            [(53.70, 22.40), (49.20, 22.40), (49.20, 13.30), (55.35, 13.30)],
            [(52.55, 23.03), (49.20, 23.03), (49.20, 13.30), (55.35, 13.30)],
        ],
    )

    for name, sx, sy, dx, dy in [
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.17", 40.25, 23.95, 48.16, 62.00),
        ("P0.19", 39.25, 23.10, 53.24, 62.00),
        ("P0.20", 36.20, 20.80, 55.78, 62.00),
    ]:
        print(f"== {name} ==")
        show(r, name, adc_from(sx, sy, dx, dy), nshow=6)


if __name__ == "__main__":
    main()
