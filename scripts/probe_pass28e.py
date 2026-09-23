#!/usr/bin/env python3
"""Find one CLEAR west-snake B path for P0.13/16/17."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

B = pcbnew.B_Cu


def chk(r, pts, name):
    ok = r.path_clear(pts, B, 0.18, name)
    if ok:
        print("CLEAR", name, pts)
    else:
        print("BLOCK", name, why(r, pts, B, 0.18, name))
    return ok


def main():
    board, r = reload()
    snakes = []
    for hy in (31.20, 31.50, 31.80, 44.20, 44.80, 27.00, 26.80):
        for col in (28.80, 29.20, 30.00, 27.70, 26.70):
            snakes.append((hy, col))
    jobs = [
        ("P0.13", 42.75, 23.10, 38.00),
        ("P0.13", 42.75, 23.95, 38.00),
        ("P0.16", 40.70, 20.80, 45.62),
        ("P0.17", 40.25, 23.95, 48.16),
        ("P0.17", 40.25, 23.10, 48.16),
    ]
    for name, vx, vy, bx in jobs:
        print(f"\n==== {name} ({vx},{vy}) ====")
        for hy, col in snakes:
            pts = [(vx, vy), (vx, hy), (col, hy), (col, 59.20), (bx, 59.20), (bx, 62.00)]
            if chk(r, pts, name):
                return
        # P0.15-parallel snake
        pts = [
            (vx, vy),
            (vx, 22.00),
            (36.80, 22.00),
            (36.80, 27.00),
            (34.80, 27.00),
            (34.80, 31.00),
            (31.50, 31.00),
            (31.50, 40.20),
            (30.20, 40.20),
            (30.20, 43.80),
            (31.50, 43.80),
            (31.50, 59.20),
            (bx, 59.20),
            (bx, 62.00),
        ]
        chk(r, pts, name)
        pts2 = [
            (vx, vy),
            (35.00, vy),
            (35.00, 31.50),
            (28.80, 31.50),
            (28.80, 59.20),
            (bx, 59.20),
            (bx, 62.00),
        ]
        chk(r, pts2, name)


if __name__ == "__main__":
    main()
