#!/usr/bin/env python3
"""P0.15 B.Cu east of VDD2_MID x=67.21 then north. With P0.01 west rip."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402
from rescue_probe_p015j import rip_p001_west  # noqa: E402

B = pcbnew.B_Cu
NAME = "P0.15"


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    print("rip", rip_p001_west(board))
    r.collect()
    nclear = 0
    for yb in (15.35, 15.45, 15.55, 15.70):
        for xn in (68.20, 68.60, 69.00, 69.50, 70.20, 72.00, 74.00, 76.00, 80.00):
            for ynorth in (7.20, 6.40, 8.00):
                pts = [
                    (41.75, 20.60),
                    (46.70, 20.60),
                    (46.70, yb),
                    (xn, yb),
                    (xn, ynorth),
                    (106.00, ynorth),
                    (106.00, 20.60),
                ]
                err = pok(r, pts, B, NAME)
                if err is None:
                    print("CLEAR", pts)
                    nclear += 1
                    if nclear >= 6:
                        return
                elif nclear == 0 and xn == 68.60 and yb == 15.45 and ynorth == 7.20:
                    print("sample", err)
    print("nclear", nclear)
    # two-step north if vertical blocked
    extra = [
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.45),
            (68.60, 15.45),
            (68.60, 18.20),
            (76.00, 18.20),
            (76.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.45),
            (68.80, 15.45),
            (68.80, 9.20),
            (90.00, 9.20),
            (90.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.45),
            (68.80, 15.45),
            (68.80, 12.00),
            (80.00, 12.00),
            (80.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
    ]
    for i, pts in enumerate(extra):
        err = pok(r, pts, B, NAME)
        print(("CLEAR" if err is None else "BLOCK extra"), i, err or pts)


if __name__ == "__main__":
    main()
