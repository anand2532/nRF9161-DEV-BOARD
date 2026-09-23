#!/usr/bin/env python3
"""West wrap at y=27.8 / 28.5 / 20.0 after P0.15 V x=36.50."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

B = pcbnew.B_Cu


def chk(r, pts, name):
    ok = r.path_clear(pts, B, 0.18, name)
    print(("  CLEAR " if ok else "  BLOCK " + why(r, pts, B, 0.18, name) + " "), pts[:5], "...")
    return ok


def main():
    board, r = reload()
    jobs = [
        ("P0.13", 42.75, 23.10, 38.00),
        ("P0.13", 42.75, 23.95, 38.00),
        ("P0.16", 40.70, 20.80, 45.62),
        ("P0.17", 40.25, 23.10, 48.16),
        ("P0.17", 40.25, 23.95, 48.16),
    ]
    cols = (28.80, 29.40, 30.00, 30.40, 31.50, 33.00)
    ys = (27.60, 27.80, 28.20, 28.80, 29.40, 20.00, 19.60, 21.00)
    for name, vx, vy, bx in jobs:
        print(f"\n==== {name} ({vx},{vy}) -> ({bx},62) ====")
        for hy in ys:
            for col in cols:
                pts = [
                    (vx, vy),
                    (vx, hy),
                    (col, hy),
                    (col, 59.20),
                    (bx, 59.20),
                    (bx, 62.00),
                ]
                if chk(r, pts, name):
                    print("  HIT", pts)
                    return


if __name__ == "__main__":
    main()
