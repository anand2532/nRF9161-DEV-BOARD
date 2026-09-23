#!/usr/bin/env python3
"""P0.15 B.Cu: cross south of VDD_GPIO (y=15.5) then north at x=55. No save."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import mm_xy, near, pok  # noqa: E402
from rescue_probe_p015j import rip_p001_west  # noqa: E402

B = pcbnew.B_Cu
NAME = "P0.15"


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    print("rip P0.01", rip_p001_west(board))
    r.collect()
    paths = []
    for x in (46.50, 46.70, 46.90, 47.10):
        for y in (15.40, 15.50, 15.60, 15.70, 16.00, 16.20):
            paths.append(
                [
                    (41.75, 20.60),
                    (x, 20.60),
                    (x, y),
                    (55.00, y),
                    (55.00, 7.20),
                    (106.00, 7.20),
                    (106.00, 20.60),
                ]
            )
            paths.append(
                [
                    (41.75, 20.60),
                    (x, 20.60),
                    (x, y),
                    (56.50, y),
                    (56.50, 7.20),
                    (106.00, 7.20),
                    (106.00, 20.60),
                ]
            )
            paths.append(
                [
                    (41.75, 20.60),
                    (x, 20.60),
                    (x, y),
                    (54.20, y),
                    (54.20, 6.40),
                    (56.00, 6.40),
                    (56.00, 7.20),
                    (106.00, 7.20),
                    (106.00, 20.60),
                ]
            )
    nclear = 0
    for pts in paths:
        err = pok(r, pts, B, NAME)
        if err is None:
            print("CLEAR", pts)
            nclear += 1
            if nclear >= 5:
                break
        # keep quiet on blocks unless first few
    if nclear == 0:
        print("none clear, sample blocks:")
        for pts in paths[:12]:
            print(" BLOCK", pok(r, pts, B, NAME))

    # without P0.01 rip too
    board2 = pcbnew.LoadBoard(BOARD)
    r2 = Final(board2)
    r2.collect()
    pts = [
        (41.75, 20.60),
        (46.70, 20.60),
        (46.70, 15.55),
        (55.00, 15.55),
        (55.00, 7.20),
        (106.00, 7.20),
        (106.00, 20.60),
    ]
    print("without P0.01 rip:", pok(r2, pts, B, NAME) or "CLEAR")


if __name__ == "__main__":
    main()
