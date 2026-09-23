#!/usr/bin/env python3
"""Probe explicit B.Cu ADC hops and F.Cu VIN_FILT jogs on the live board."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import existing_via, pok  # noqa: E402

B, F = pcbnew.B_Cu, pcbnew.F_Cu


def try_paths(r, name, paths, layer):
    for i, pts in enumerate(paths):
        err = pok(r, pts, layer, name)
        if err is None:
            print(f"  CLEAR {name} i={i} {pts[:3]}...")
            return pts
        if i < 6:
            print(f"  BLOCK {name} i={i} {err}")
    return None


def adc_paths(sx, sy, dx, dy, extra_cols, extra_rows):
    out = []
    # east-north then south then west to pin (private north of P0.15 y=15.35)
    for y in extra_rows:
        for x in extra_cols:
            out.append([(sx, sy), (sx, y), (x, y), (x, 60.50), (dx, 60.50), (dx, dy)])
            out.append([(sx, sy), (sx, y), (x, y), (x, dy), (dx, dy)])
    # east of U1 then south
    for x in (47.2, 48.4, 49.6, 51.0, 54.0, 57.0):
        out.append([(sx, sy), (x, sy), (x, 60.50), (dx, 60.50), (dx, dy)])
        out.append([(sx, sy), (x, sy), (x, dy), (dx, dy)])
    # south-first then west columns (avoid via row)
    for yb in (24.80, 27.20, 28.40):
        for col in (34.50, 33.00, 29.50, 27.40):
            out.append([(sx, sy), (sx, yb), (col, yb), (col, 58.80), (dx, 58.80), (dx, dy)])
    return out


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    specs = [
        ("P0.14", 40.54, 62.00),
        ("P0.16", 45.62, 62.00),
        ("P0.17", 48.16, 62.00),
        ("P0.18", 50.70, 62.00),
        ("P0.19", 53.24, 62.00),
        ("P0.20", 55.78, 62.00),
    ]
    cols = [64.70, 74.00, 86.00, 96.00, 107.20, 111.20]
    rows = [6.60, 8.40, 10.40, 14.20, 16.60, 18.40]
    for name, dx, dy in specs:
        u1 = r.u1(name)
        v = existing_via(r, name, u1["x"], u1["y"], 12)
        if v:
            sx, sy = v["x"], v["y"]
            print(f"{name} via ({sx:.2f},{sy:.2f}) -> ({dx},{dy})")
        else:
            sx, sy = u1["x"], u1["y"]
            print(f"{name} NO VIA pad ({sx:.2f},{sy:.2f})")
            site = r.local_via(sx, sy, name)
            print(f"  local_via -> {site}")
            continue
        try_paths(r, name, adc_paths(sx, sy, dx, dy, cols, rows), B)

    print("\n== VIN_FILT F jogs ==")
    vf = [
        [(53.20, 21.90), (47.40, 21.90), (47.40, 13.30), (55.35, 13.30)],
        [(53.20, 21.90), (46.20, 21.90), (46.20, 12.40), (55.35, 12.40), (55.35, 13.30)],
        [(53.20, 21.90), (64.00, 21.90), (64.00, 13.30), (55.35, 13.30)],
        [(53.20, 21.90), (66.00, 21.90), (66.00, 11.50), (55.35, 11.50), (55.35, 13.30)],
        [(53.20, 21.90), (53.20, 24.50), (47.00, 24.50), (47.00, 12.20), (55.35, 12.20), (55.35, 13.30)],
        [(51.90, 21.90), (51.90, 24.80), (45.50, 24.80), (45.50, 12.20), (55.35, 12.20), (55.35, 13.30)],
    ]
    try_paths(r, "VIN_FILT", vf, F)

    print("\n== VIN_F F jogs ==")
    vinf = [
        [(71.20, 19.06), (71.20, 14.00), (49.30, 14.00), (49.30, 12.60)],
        [(71.20, 19.06), (74.50, 19.06), (74.50, 12.00), (49.30, 12.00), (49.30, 12.60)],
        [(71.20, 19.06), (68.00, 19.06), (68.00, 21.50), (48.00, 21.50), (48.00, 12.60), (49.30, 12.60)],
        [(71.20, 19.06), (71.20, 8.00), (49.30, 8.00), (49.30, 12.60)],
        [(71.20, 19.80), (80.00, 19.80), (80.00, 12.00), (49.30, 12.00), (49.30, 12.60)],
    ]
    try_paths(r, "VIN_F", vinf, F)

    print("\n== nRESET B from courtyard via to R5 cluster ==")
    nr = [
        [(45.68, 15.80), (45.68, 14.20), (102.00, 14.20), (102.00, 27.13)],
        [(45.68, 15.80), (107.20, 15.80), (107.20, 27.13), (102.33, 27.13)],
        [(38.25, 23.10), (38.25, 14.20), (102.00, 14.20), (102.00, 27.13)],
        [(45.68, 15.80), (45.68, 8.40), (102.00, 8.40), (102.00, 27.13)],
        [(45.68, 15.80), (64.70, 15.80), (64.70, 36.00), (102.00, 36.00)],
    ]
    try_paths(r, "nRESET", nr, B)


if __name__ == "__main__":
    main()
