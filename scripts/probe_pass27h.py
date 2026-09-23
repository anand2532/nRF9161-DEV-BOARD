#!/usr/bin/env python3
"""End-to-end P0.06 J9 candidate; a few ADC F/B last tries."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def chk(r, pts, ly, name):
    ok = r.path_clear(pts, ly, 0.18, name)
    if ok:
        print("  CLEAR", pts)
        return True
    print("  BLOCK", why(r, pts, ly, 0.18, name))
    return False


def vwhy(r, x, y, name, s=0.50, d=0.30):
    w = r.via_why(x, y, name, size=s, drill=d)
    print(f"  via ({x:.2f},{y:.2f}) {s:.2f}/{d:.2f}", w)
    return w is None


def main():
    board, r = reload()
    print("==== P0.06 J9 stacked hops ====")
    vias = [
        (14.90, 77.80),
        (115.50, 55.50),
        (107.70, 49.00),
        (113.20, 36.00),
        (106.15, 21.20),
        (113.20, 10.00),
    ]
    for x, y in vias:
        if not vwhy(r, x, y, "P0.06"):
            vwhy(r, x, y, "P0.06", 0.45, 0.25)

    routes = [
        ([(21.24, 74.00), (14.90, 74.00), (14.90, 77.80)], B, "B to SW via"),
        ([(14.90, 77.80), (14.90, 79.20), (115.50, 79.20), (115.50, 55.50)], F, "F y=79.20 east of P0.04"),
        ([(115.50, 55.50), (107.70, 55.50), (107.70, 49.00)], B, "B west then south"),
        ([(107.70, 49.00), (107.70, 47.20), (113.20, 47.20), (113.20, 36.00)], F, "F hop P0.04 H y=49.20"),
        ([(113.20, 36.00), (113.20, 21.20), (106.15, 21.20)], B, "B to west of P0.04 jog"),
        ([(106.15, 21.20), (106.15, 10.00), (113.20, 10.00)], B, "B hop y=19.43 and y=16.80"),
        ([(113.20, 10.00), (113.20, 8.40), (116.00, 8.40), (116.00, 8.00)], B, "stub J9.1"),
    ]
    for pts, ly, lab in routes:
        print(lab)
        chk(r, pts, ly, "P0.06")

    # alt SE via x
    print("\n alt F V x")
    for xv, yv in [(115.40, 55.80), (115.60, 55.20), (115.80, 56.00), (115.30, 56.50), (115.50, 56.00)]:
        vwhy(r, xv, yv, "P0.06")
        chk(r, [(14.90, 77.80), (14.90, 79.20), (xv, 79.20), (xv, yv)], F, "P0.06")

    print("\n alt hop west of 106.70")
    for xv in (106.00, 106.15, 106.30, 106.40):
        vwhy(r, xv, 21.20, "P0.06")
        chk(r, [(113.20, 36.00), (113.20, 21.20), (xv, 21.20), (xv, 10.00)], B, "P0.06")

    print("\n==== P0.13 F to (42.75,19) then B y=19 east of VDD_GPIO ====")
    vwhy(r, 42.75, 19.00, "P0.13")
    chk(r, [(42.75, 23.10), (42.75, 19.00)], F, "P0.13")
    for pts in [
        [(42.75, 19.00), (50.00, 19.00), (50.00, 59.20), (38.00, 59.20), (38.00, 62.00)],
        [(42.75, 19.00), (48.00, 19.00), (48.00, 21.20), (46.50, 21.20)],  # toward P0.15 east B?
        [(42.75, 19.00), (46.50, 19.00), (46.50, 21.20)],  # P0.15 B (46.50,22.50)-(46.50,21.20)
        [(42.75, 19.00), (41.75, 19.00), (41.75, 20.60)],  # P0.15 B V
    ]:
        chk(r, pts, B, "P0.13")

    print("\n==== P0.16 B from (40.70,20.80) join P0.15-style at 22.50? ====")
    chk(r, [(40.70, 20.80), (40.70, 22.50), (36.50, 22.50)], B, "P0.16")
    chk(r, [(40.70, 20.80), (36.50, 20.80), (36.50, 22.50)], B, "P0.16")
    chk(r, [(40.70, 20.80), (41.75, 20.80)], B, "P0.16")  # would short P0.15 - expect block


if __name__ == "__main__":
    main()
