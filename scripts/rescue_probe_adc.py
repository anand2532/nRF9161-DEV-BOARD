#!/usr/bin/env python3
"""Probe explicit west-courtyard B.Cu hops for ADC nets after P0.15 wrap delete."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok, existing_via  # noqa: E402

B = pcbnew.B_Cu


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    specs = [
        ("P0.13", 38.00, 62.00, 36.50),
        ("P0.14", 40.54, 62.00, 34.50),
        ("P0.16", 45.62, 62.00, 32.20),
        ("P0.17", 48.16, 62.00, 31.00),
        ("P0.18", 50.70, 62.00, 26.90),
        ("P0.19", 53.24, 62.00, 25.55),
    ]
    for name, dx, dy, col in specs:
        u1 = r.u1(name)
        v = existing_via(r, name, u1["x"], u1["y"], 10)
        src = (v["x"], v["y"]) if v else (u1["x"], u1["y"])
        print(f"{name} src={src} dest=({dx},{dy}) col={col} via={v is not None}")
        paths = [
            [src, (col, src[1]), (col, 58.80), (dx, 58.80), (dx, dy)],
            [src, (src[0], 23.10), (col, 23.10), (col, 58.80), (dx, 58.80), (dx, dy)],
            [src, (col, src[1]), (col, dy), (dx, dy)],
            [src, (src[0], 22.50), (col, 22.50), (col, 59.20), (dx, 59.20), (dx, dy)],
            [src, (26.90, src[1]), (26.90, 58.80), (dx, 58.80), (dx, dy)],
        ]
        anyc = False
        for i, pts in enumerate(paths):
            err = pok(r, pts, B, name)
            if err is None:
                print(f"  CLEAR i={i} {pts}")
                anyc = True
                break
            else:
                print(f"  BLOCK i={i} {err}")
        if not anyc:
            print("  none")


if __name__ == "__main__":
    main()
