#!/usr/bin/env python3
"""P0.13 via-to-maze stitch then zone refill so B.Cu GND clearance is legal."""
from __future__ import annotations

import os
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, SNAP_DIR, Final  # noqa: E402
from rescue_final import check, try_pts  # noqa: E402

B = pcbnew.B_Cu
LAST = os.path.join(SNAP_DIR, "after-pass30-p015-wrapdel.kicad_pcb")


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    if not try_pts(r, [(42.75, 23.95), (42.75, 26.75)], B, "P0.13", "P0.13 via-to-maze"):
        return
    r.collect()
    got = check(board, r, "pass31-P013-stitch", LAST, 80, fill=True, must_drop=True)
    if got[0] is None:
        print("aborted")
        return
    pairs, n, counts, _ = got
    print(f"kept unconn={n} shorts={counts.get('shorting_items')} clr={counts.get('clearance')}")
    print("nets", sorted({p['net'] for p in pairs}))


if __name__ == "__main__":
    main()
