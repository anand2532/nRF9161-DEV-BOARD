#!/usr/bin/env python3
"""After deleting dangling P0.01 west y=15.2, probe P0.15 B.Cu north hop. No save."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402
from rescue_final import mm_xy, near, pok  # noqa: E402

B = pcbnew.B_Cu
NAME = "P0.15"


def rip_p001_west(board):
    n = 0
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.01" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if near((y1 + y2) / 2, 15.20, 0.25) and abs(y1 - y2) < 0.4 and min(x1, x2) < 80:
            print(f"  DEL P0.01 ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
            board.Remove(tr)
            n += 1
    return n


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    print("ripped P0.01 west", rip_p001_west(board))
    r.collect()

    bpaths = [
        [(41.75, 20.60), (46.20, 20.60), (46.20, 8.00), (55.00, 8.00), (55.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.20, 20.60), (46.20, 7.20), (52.80, 7.20), (52.80, 6.40), (54.50, 6.40), (54.50, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (45.90, 20.60), (45.90, 8.00), (55.00, 8.00), (55.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.20, 20.60), (46.20, 12.00), (54.20, 12.00), (54.20, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.20, 20.60), (46.20, 16.50), (54.00, 16.50), (54.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 23.10), (41.75, 20.60), (46.20, 20.60), (46.20, 8.00), (55.00, 8.00), (55.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.80, 20.60), (46.80, 23.45), (55.20, 23.45), (55.20, 17.50), (67.20, 17.50), (67.20, 8.00), (90.00, 8.00), (90.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
        [(41.75, 20.60), (46.20, 20.60), (46.20, 8.00), (90.00, 8.00), (90.00, 7.20), (106.00, 7.20), (106.00, 20.60)],
    ]
    for pts in bpaths:
        print(("CLEAR" if pok(r, pts, B, NAME) is None else "BLOCK"), pok(r, pts, B, NAME) or pts[-1])

    xs = [round(x, 2) for x in [41.75, 45.9, 46.2, 46.8, 48, 50, 52.8, 53.65, 54.2, 54.5, 55, 60, 67.2, 70, 80, 90, 100, 106]]
    ys = [round(y, 2) for y in [6.4, 7.2, 8.0, 10.0, 12.0, 14.0, 16.5, 17.5, 19.2, 20.6, 23.1, 23.45]]
    pts, L = waypoint_route(r, 41.75, 20.60, 106.00, 20.60, B, 0.18, NAME, xs=xs, ys=ys)
    print("waypoint", None if pts is None else f"L={L:.1f} {pok(r, pts, B, NAME)}")
    if pts and pok(r, pts, B, NAME) is None:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")
    pts, L = waypoint_route(r, 41.75, 20.60, 55.00, 8.00, B, 0.18, NAME, xs=xs, ys=ys)
    print("wp to 55,8", None if pts is None else f"L={L:.1f} {pok(r, pts, B, NAME)}")
    if pts and pok(r, pts, B, NAME) is None:
        for p in pts:
            print(f"  {p[0]:.2f},{p[1]:.2f}")


if __name__ == "__main__":
    main()
