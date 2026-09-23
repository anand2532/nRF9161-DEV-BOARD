#!/usr/bin/env python3
"""P0.15 B.Cu: go east past VDD_GPIO x=70 at y≈15.7, then north. No save."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402

B = pcbnew.B_Cu
NAME = "P0.15"


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    nclear = 0
    for xg in (46.50, 46.70, 46.90):
        for yb in (15.55, 15.70, 15.90, 16.10, 16.40):
            for xn in (70.80, 71.50, 71.80, 72.40, 73.20, 74.00, 75.50):
                pts = [
                    (41.75, 20.60),
                    (xg, 20.60),
                    (xg, yb),
                    (xn, yb),
                    (xn, 7.20),
                    (106.00, 7.20),
                    (106.00, 20.60),
                ]
                err = pok(r, pts, B, NAME)
                if err is None:
                    print("CLEAR", pts)
                    nclear += 1
                    if nclear >= 8:
                        return
                elif nclear == 0 and xn == 71.80 and yb == 15.70 and xg == 46.70:
                    print("sample", err)
    print("nclear", nclear)
    # extra jogs around VIN_F cluster
    for pts in [
        [(41.75, 20.60), (46.70, 20.60), (46.70, 15.70), (69.20, 15.70), (69.20, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.70, 20.60), (46.70, 16.20), (69.20, 16.20), (69.20, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.70, 20.60), (46.70, 15.70), (80.00, 15.70), (80.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.70, 20.60), (46.70, 16.20), (85.00, 16.20), (85.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.70, 20.60), (46.70, 17.20), (80.00, 17.20), (80.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.70, 20.60), (46.70, 15.70), (71.80, 15.70), (71.80, 9.00), (90.00, 9.00), (90.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
    ]:
        err = pok(r, pts, B, NAME)
        print(("CLEAR" if err is None else "BLOCK"), err or pts)


if __name__ == "__main__":
    main()
