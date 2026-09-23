#!/usr/bin/env python3
"""Probe y=24.9 west channel and south columns for ADC."""
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
    print("B.Cu foreign in west courtyard x=24.6-41.5 y=22-60:")
    from collections import Counter
    occ = Counter()
    for t in r.tracks:
        if t["ly"] != B:
            continue
        mx, my = (t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2
        if 24.6 <= mx <= 41.5 and 22 <= my <= 60:
            occ[t["n"]] += 1
            print(f"  {t['n']} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")
    print("counts", dict(occ))

    specs = [
        ("P0.13", 38.00, 62.00),
        ("P0.14", 40.54, 62.00),
        ("P0.16", 45.62, 62.00),
        ("P0.17", 48.16, 62.00),
        ("P0.18", 50.70, 62.00),
    ]
    for name, dx, dy in specs:
        u1 = r.u1(name)
        v = existing_via(r, name, u1["x"], u1["y"], 10)
        src = (v["x"], v["y"]) if v else (u1["x"], u1["y"])
        print(f"\n{name} src={src}")
        for yb in (24.60, 24.90, 25.20, 21.50, 22.00, 27.50, 28.20, 39.80, 41.50):
            for col in (36.50, 35.00, 34.50, 33.00, 32.20, 29.00, 26.90):
                pts = [src, (src[0], yb), (col, yb), (col, 58.80), (dx, 58.80), (dx, dy)]
                err = pok(r, pts, B, name)
                if err is None:
                    print(f"  CLEAR y={yb} col={col} {pts}")
                    break
            else:
                continue
            break
        else:
            print("  none of yb/col grid")


if __name__ == "__main__":
    main()
