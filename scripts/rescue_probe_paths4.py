#!/usr/bin/env python3
"""Few targeted P0.16 west/south paths + dry astar_b + VIN_FILT south-around ENABLE."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402

B = pcbnew.B_Cu


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    sx, sy, dx, dy = 40.70, 20.80, 45.62, 62.00
    paths = [
        [(sx, sy), (sx, 21.55), (31.70, 21.55), (31.70, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.55), (31.70, 21.55), (31.70, 40.20), (30.00, 40.20), (30.00, 43.80), (31.70, 43.80), (31.70, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.70), (29.40, 21.70), (29.40, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.70), (28.20, 21.70), (28.20, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 22.40), (31.70, 22.40), (31.70, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 24.90), (31.70, 24.90), (31.70, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.55), (34.80, 21.55), (34.80, 43.20), (31.70, 43.20), (31.70, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.55), (34.80, 21.55), (34.80, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.55), (35.50, 21.55), (35.50, 40.00), (34.80, 40.00), (34.80, 58.80), (dx, 58.80), (dx, dy)],
        # east after south, stay south of nRESET 19.80 and east of P0.15 stub
        [(sx, sy), (sx, 21.55), (44.80, 21.55), (44.80, 24.90), (49.50, 24.90), (49.50, 58.80), (dx, 58.80), (dx, dy)],
        [(sx, sy), (sx, 21.55), (44.80, 21.55), (44.80, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (47.50, 21.55), (47.50, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 24.90), (47.50, 24.90), (47.50, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 24.90), (52.00, 24.90), (52.00, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 28.20), (52.00, 28.20), (52.00, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (44.80, 21.55), (44.80, 18.40), (58.00, 18.40), (58.00, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (44.80, 21.55), (44.80, 17.20), (107.20, 17.20), (107.20, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (44.80, 21.55), (44.80, 18.60), (107.20, 18.60), (107.20, 60.50), (dx, 60.50), (dx, dy)],
        # detour around nRESET: go east past 45.68 then north
        [(sx, sy), (sx, 21.55), (48.00, 21.55), (48.00, 16.60), (107.20, 16.60), (107.20, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (48.00, 21.55), (48.00, 14.20), (86.00, 14.20), (86.00, 60.50), (dx, 60.50), (dx, dy)],
        [(sx, sy), (sx, 21.55), (48.00, 21.55), (48.00, 12.00), (107.20, 12.00), (107.20, 60.50), (dx, 60.50), (dx, dy)],
    ]
    print("== P0.16 targeted ==")
    for i, pts in enumerate(paths):
        err = pok(r, pts, B, "P0.16")
        print(f"  {'CLEAR' if err is None else 'BLOCK'} i={i} {err if err else pts}")

    print("== VIN_FILT south then west ==")
    for i, pts in enumerate(
        [
            [(51.90, 21.90), (51.90, 24.80), (49.00, 24.80), (49.00, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 25.50), (47.50, 25.50), (47.50, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 26.50), (46.50, 26.50), (46.50, 12.40), (55.35, 12.40), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 24.80), (58.80, 24.80), (58.80, 13.30), (55.35, 13.30)],
            [(51.90, 21.90), (51.90, 18.80), (49.00, 18.80), (49.00, 13.30), (55.35, 13.30)],
            [(52.55, 23.03), (52.55, 25.80), (47.50, 25.80), (47.50, 13.30), (55.35, 13.30)],
        ]
    ):
        err = pok(r, pts, B, "VIN_FILT")
        print(f"  {'CLEAR' if err is None else 'BLOCK'} i={i} {err if err else pts}")

    print("== astar_b P0.16 (occupancy, no commit if we intercept) ==")
    # call internal search by copying logic via route_b but that commits.
    # Instead: run astar and if commit would happen, print True/False.
    r.ok = 0
    ntracks = len(r.tracks)
    ok = r.astar_b(sx, sy, dx, dy, "P0.16", 0.18, r.code_of("P0.16"))
    print(f"  astar_b result={ok} newtracks={len(r.tracks)-ntracks}")


if __name__ == "__main__":
    main()
