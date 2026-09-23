#!/usr/bin/env python3
"""Pass 3: B.Cu GPIO via route_to_via with parent-like B.Cu clearance; tiny P0.15 nudge."""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import BOARD, hypot, vec  # noqa: E402
from final_connect import BACKUP, DRC_JSON, Final, SNAP_DIR, fill_zones, run_drc  # noqa: E402
from final_pass2 import dnp_stubs, gpio_to_via, save_chk, wrap_fanout  # noqa: E402

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"


def load():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def nudge_p015_safe(r: Final):
    """Move P0.15 vertical 106.10 -> 106.00 (0.10 mm west). Stay east of COEX2 at 105.10."""
    changed = 0
    for tr in r.board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        if abs(x1 - 106.10) < 0.04 and abs(x2 - 106.10) < 0.04:
            tr.SetStart(vec(106.00, y1))
            tr.SetEnd(vec(106.00, y2))
            changed += 1
            continue
        nx1, nx2 = x1, x2
        if abs(x1 - 106.10) < 0.04 and abs(x2 - 106.10) > 0.5:
            nx1 = 106.00
        if abs(x2 - 106.10) < 0.04 and abs(x1 - 106.10) > 0.5:
            nx2 = 106.00
        if nx1 != x1 or nx2 != x2:
            tr.SetStart(vec(nx1, y1))
            tr.SetEnd(vec(nx2, y2))
            changed += 1
    print(f"  P0.15 safe nudge {changed}")
    r.collect()


def main():
    pairs, n0, base, _ = run_drc()
    print(f"start unconnected={n0} clear={base.get('clearance', 0)} shorts={base.get('shorting_items', 0)}")
    baseline = {
        "shorting_items": base.get("shorting_items", 0),
        "clearance": base.get("clearance", 0),
        "hole_clearance": base.get("hole_clearance", 0),
    }
    last_good = os.path.join(SNAP_DIR, "after-gpio2.kicad_pcb")
    if not os.path.isfile(last_good):
        last_good = BACKUP
    board, r = load()

    print("#### wrap fanout retry", flush=True)
    for name in (
        "P0.01",
        "P0.04",
        "P0.09",
        "P0.14",
        "P0.16",
        "P0.18",
        "P0.20",
        "P0.22",
        "P0.24",
        "P0.27",
        "P0.29",
        "P0.31",
        "MAGPIO0",
        "MIPI_SDATA",
        "COEX1",
    ):
        wrap_fanout(r, name)
    r.collect()
    got = save_chk(board, r, "fanout3", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-fanout3.kicad_pcb")
    board, r = load()

    print("#### gpio route_to_via (B.Cu 0.13)", flush=True)
    gpio_to_via(r)
    r.collect()
    got = save_chk(board, r, "gpio3", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-gpio3.kicad_pcb")
    board, r = load()

    print("#### P0.15 0.10mm", flush=True)
    nudge_p015_safe(r)
    got = save_chk(board, r, "p015s", baseline, last_good)
    if got[0] is None:
        print("P0.15 abort")
        board, r = load()
    else:
        pairs, n, counts = got
        last_good = os.path.join(SNAP_DIR, "after-p015s.kicad_pcb")
        baseline["clearance"] = min(baseline["clearance"], counts.get("clearance", 1))
        board, r = load()

    print("#### DNP", flush=True)
    dnp_stubs(r)
    got = save_chk(board, r, "dnp3", baseline, last_good)
    if got[0] is None:
        print("DNP abort")
        return 0
    pairs, n, counts = got
    print(f"PASS3 FINAL unconnected={n} shorts={counts.get('shorting_items', 0)} clear={counts.get('clearance', 0)}")
    shutil.copy2(DRC_JSON, f"{ROOT}/reports/DRC_AFTER_CONNECT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
