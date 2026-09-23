#!/usr/bin/env python3
"""Close remaining geometrically-clear detours on the LIVE board."""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, SNAP_DIR, Final, fill_zones, run_drc  # noqa: E402
from final_pass7 import commit_or_why, place_via  # noqa: E402

LAST = os.path.join(SNAP_DIR, "after-pass7e.kicad_pcb")
ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}


def check(board, r, label, last_good):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad:
        print(f"ABORT { {k: counts[k] for k in bad} }; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    snap = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, snap)
    return pairs, n, counts


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("== VDD1 B.Cu south of VDD2 y=26.75 ==", flush=True)
    v6 = r.nearest_via("VDD1", 49.20, 25.60, 2)
    v3 = r.nearest_via("VDD1", 53.70, 27.13, 2)
    if v6 and v3:
        for pts in (
            [(v6["x"], v6["y"]), (v6["x"], 24.20), (v3["x"], 24.20), (v3["x"], v3["y"])],
            [(v6["x"], v6["y"]), (v6["x"], 23.40), (55.20, 23.40), (55.20, v3["y"]), (v3["x"], v3["y"])],
            [(v6["x"], v6["y"]), (v6["x"], 28.80), (v3["x"], 28.80), (v3["x"], v3["y"])],
            [(v6["x"], v6["y"]), (47.80, v6["y"]), (47.80, 24.00), (55.40, 24.00), (55.40, v3["y"]), (v3["x"], v3["y"])],
        ):
            if commit_or_why(r, pts, pcbnew.B_Cu, 0.25, "VDD1", f"VDD1 B {pts[1]}"):
                break

    print("== VDD2 TP12 north of ENABLE y=40.95 ==", flush=True)
    for pts in (
        [(60.00, 42.00), (60.00, 43.80), (50.40, 43.80), (50.40, 38.00), (53.68, 38.00)],
        [(60.00, 42.00), (60.00, 44.40), (61.80, 44.40), (61.80, 43.80), (74.20, 43.80), (74.20, 37.13), (59.70, 37.13)],
        [(60.00, 42.00), (58.40, 42.00), (58.40, 38.00), (53.68, 38.00)],
    ):
        if commit_or_why(r, pts, pcbnew.F_Cu, 0.25, "VDD2", f"TP12 {pts[1]}"):
            break
    site = place_via(r, 61.80, 43.80, "VDD2", pwr=True)
    v2 = r.nearest_via("VDD2", 52.22, 32.00, 4) or r.nearest_via("VDD2", 59.70, 37.13, 4)
    if site and v2:
        commit_or_why(r, [(60.00, 42.00), (61.80, 42.00), site], pcbnew.F_Cu, 0.25, "VDD2", "TP12 F via")
        commit_or_why(
            r,
            [site, (site[0], 48.00), (v2["x"], 48.00), (v2["x"], v2["y"])],
            pcbnew.B_Cu,
            0.25,
            "VDD2",
            "TP12 B",
        )

    print("== ENABLE B.Cu east of P0.13 via ==", flush=True)
    ve = r.nearest_via("ENABLE", 42.75, 45.60, 2)
    vb = r.nearest_via("ENABLE", 48.33, 23.13, 10)
    if ve and vb:
        for pts in (
            [(ve["x"], ve["y"]), (50.80, ve["y"]), (50.80, vb["y"]), (vb["x"], vb["y"])],
            [(ve["x"], ve["y"]), (54.20, ve["y"]), (54.20, 20.80), (vb["x"], 20.80), (vb["x"], vb["y"])],
            [(ve["x"], ve["y"]), (40.80, ve["y"]), (40.80, 48.20), (50.80, 48.20), (50.80, vb["y"]), (vb["x"], vb["y"])],
        ):
            if commit_or_why(r, pts, pcbnew.B_Cu, 0.18, "ENABLE", f"ENABLE B {pts[1]}"):
                break
    sw1v = r.nearest_via("ENABLE", 90.38, 26.20, 2)
    if sw1v and ve:
        for pts in (
            [(sw1v["x"], sw1v["y"]), (sw1v["x"], 48.20), (ve["x"], 48.20), (ve["x"], ve["y"])],
            [(sw1v["x"], sw1v["y"]), (sw1v["x"], 12.40), (ve["x"], 12.40), (ve["x"], ve["y"])],
            [(sw1v["x"], sw1v["y"]), (94.00, sw1v["y"]), (94.00, 48.20), (50.80, 48.20), (ve["x"], ve["y"])],
        ):
            if commit_or_why(r, pts, pcbnew.B_Cu, 0.18, "ENABLE", f"SW1 B {pts[1]}"):
                break

    print("== P0.06 F.Cu south of VDD1 y=38 ==", flush=True)
    v06 = r.nearest_via("P0.06", 44.00, 39.90, 3)
    if v06:
        for pts in (
            [(44.00, 36.00), (45.20, 36.00), (45.20, 37.20), (46.80, 37.20), (46.80, v06["y"]), (v06["x"], v06["y"])],
            [(44.00, 36.00), (44.00, 37.20), (45.40, 37.20), (45.40, v06["y"]), (v06["x"], v06["y"])],
        ):
            if commit_or_why(r, pts, pcbnew.F_Cu, 0.18, "P0.06", f"P0.06 F {pts[1]}"):
                break
        # alternate via east of courtyard south of y=38 VDD1
        site = place_via(r, 48.80, 40.80, "P0.06")
        if site:
            commit_or_why(r, [(44.00, 36.00), (48.80, 36.00), site], pcbnew.F_Cu, 0.18, "P0.06", "P0.06 alt F")
            commit_or_why(r, [site, (site[0], v06["y"]), (v06["x"], v06["y"])], pcbnew.B_Cu, 0.13, "P0.06", "P0.06 alt B")

    pairs, n, counts = check(board, r, "pass8", LAST)
    if pairs is None:
        return 3
    print("DONE unconn", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
