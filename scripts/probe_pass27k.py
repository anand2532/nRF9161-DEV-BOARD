#!/usr/bin/env python3
"""P0.06 J9 B jog x=106.35 west of P0.04 x=106.70."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def chk(r, pts, ly, name):
    ok = r.path_clear(pts, ly, 0.18, name)
    print(("  CLEAR " if ok else "  BLOCK " + why(r, pts, ly, 0.18, name) + " "), pts)
    return ok


def main():
    board, r = reload()
    print("==== B jog x candidates ====")
    for x in [106.20, 106.25, 106.30, 106.35, 106.40, 106.45, 106.50, 106.55]:
        pts = [(113.20, 36.00), (113.20, 22.00), (x, 22.00), (x, 14.50), (114.50, 14.50)]
        chk(r, pts, B, "P0.06")
        pts = [(113.20, 36.00), (113.20, 22.50), (x, 22.50), (x, 14.50), (113.20, 14.50)]
        chk(r, pts, B, "P0.06")

    print("\n==== pieces ====")
    for x in (106.30, 106.35, 106.40):
        print(f" -- x={x}")
        chk(r, [(113.20, 36.00), (113.20, 22.00)], B, "P0.06")
        chk(r, [(113.20, 22.00), (x, 22.00)], B, "P0.06")
        chk(r, [(x, 22.00), (x, 14.50)], B, "P0.06")
        chk(r, [(x, 14.50), (114.50, 14.50)], B, "P0.06")
        chk(r, [(x, 22.00), (x, 8.40)], B, "P0.06")
        chk(r, [(x, 14.50), (113.20, 14.50), (113.20, 8.40), (116.00, 8.40), (116.00, 8.00)], B, "P0.06")
        chk(r, [(x, 14.50), (114.50, 14.50), (114.50, 8.40), (116.00, 8.40), (116.00, 8.00)], B, "P0.06")

    print("\n==== full candidate ====")
    routes = [
        ([(21.24, 74.00), (14.90, 74.00), (14.90, 77.80)], B),
        ([(14.90, 77.80), (14.90, 79.20), (115.50, 79.20), (115.50, 55.50)], F),
        ([(115.50, 55.50), (107.40, 55.50), (107.40, 47.20)], B),
        ([(107.40, 47.20), (113.20, 47.20), (113.20, 36.00)], F),
    ]
    for pts, ly in routes:
        chk(r, pts, ly, "P0.06")
    for x in (106.30, 106.35, 106.40):
        print(f" join x={x}")
        chk(
            r,
            [
                (113.20, 36.00),
                (113.20, 22.00),
                (x, 22.00),
                (x, 14.50),
                (114.50, 14.50),
                (114.50, 8.40),
                (116.00, 8.40),
                (116.00, 8.00),
            ],
            B,
            "P0.06",
        )


if __name__ == "__main__":
    main()
