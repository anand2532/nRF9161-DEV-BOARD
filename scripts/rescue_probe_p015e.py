#!/usr/bin/env python3
"""Probe F.Cu jog to a north via, then B.Cu y=14 to x=106 for P0.15."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def pok(r, pts, layer):
    for a, b in zip(pts, pts[1:]):
        if hypot(a[0], a[1], b[0], b[1]) < 0.03:
            continue
        if not r.track_clear(a[0], a[1], b[0], b[1], layer, W, NAME):
            return why(r, [a, b], layer, W, NAME)
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    viasites = [
        (41.75, 14.00),
        (41.75, 12.00),
        (41.75, 10.00),
        (37.00, 14.00),
        (36.00, 12.00),
        (46.50, 14.00),
        (50.00, 14.00),
        (52.00, 12.00),
        (60.00, 12.00),
        (55.00, 8.00),
        (43.50, 14.00),
        (39.50, 14.00),
        (34.00, 14.00),
        (32.00, 16.00),
        (26.50, 16.00),
        (26.50, 12.00),
        (26.90, 18.00),
    ]
    print("via sites:")
    for xy in viasites:
        print(f"  {xy} {r.via_why(xy[0], xy[1], NAME) or 'OK'}")

    fpaths = [
        [(41.75, 23.10), (41.75, 24.80), (37.00, 24.80), (37.00, 14.00), (41.75, 14.00)],
        [(41.75, 23.10), (41.75, 24.80), (36.00, 24.80), (36.00, 12.00), (41.75, 12.00)],
        [(41.75, 23.10), (41.75, 24.80), (37.00, 24.80), (37.00, 14.00)],
        [(41.75, 23.10), (41.75, 24.80), (46.50, 24.80), (46.50, 14.00)],
        [(41.75, 26.75), (44.80, 26.75), (44.80, 24.80), (46.50, 24.80), (46.50, 14.00)],
        [(41.75, 26.75), (41.75, 24.80), (50.00, 24.80), (50.00, 14.00)],
        [(41.75, 23.10), (41.75, 24.80), (32.00, 24.80), (32.00, 14.00), (41.75, 14.00)],
        [(41.75, 23.10), (41.75, 24.80), (26.90, 24.80), (26.90, 18.00)],
        [(41.75, 23.10), (39.50, 23.10), (39.50, 14.00)],
        [(41.75, 23.10), (41.75, 22.00), (50.00, 22.00), (50.00, 14.00)],
        [(41.75, 26.75), (47.50, 26.75), (47.50, 14.00)],
        [(41.75, 26.75), (45.80, 26.75), (45.80, 8.00), (55.00, 8.00)],
        [(41.75, 26.75), (45.80, 26.75), (45.80, 12.00), (60.00, 12.00)],
    ]
    print("\nF.Cu paths:")
    for pts in fpaths:
        err = pok(r, pts, F)
        print(("CLEAR" if err is None else "BLOCK"), pts[-1], err or "")

    print("\nB.Cu from candidate vias to 106,20.60:")
    for vx, vy in [(41.75, 14.00), (46.50, 14.00), (50.00, 14.00), (60.00, 12.00), (55.00, 8.00), (37.00, 14.00), (26.90, 18.00)]:
        for y in (vy, 14.00, 13.40, 12.00, 11.20, 10.00, 8.00, 7.20):
            pts = [(vx, vy), (vx, y), (106.00, y), (106.00, 20.60)]
            err = pok(r, pts, B)
            if err is None:
                print("CLEAR B", pts)
            elif y == vy:
                print("BLOCK B y=vy", (vx, vy), err)


if __name__ == "__main__":
    main()
