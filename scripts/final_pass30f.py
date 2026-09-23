#!/usr/bin/env python3
"""Pass30f: ONE atomic VIN_FILT co-route with full restores.

Kept geometry (see reports/PASS30F_SUMMARY.json):
  Rip: VDD_GPIO H@14.8, P0.15 N@15.35, ENABLE H@20.3, VDD2_MID H@16.87
  VIN_FILT B: (55.35,13.3)->(51.9,13.3)->(51.9,21.9) w=0.30
  VDD_GPIO: (70,14.8)->(70,9)->(48.05,9)->(48.05,14.8)
  ENABLE F: (50.85,23.15)->(50.85,20.3)->(56.5,20.3)
  VDD2_MID: (58.14,16.87)->(58.14,17.8)->(67.21,17.8)->(67.21,16.87)
  P0.15: vias@(51,16.5)/(60,16.5) + F@y19.5 + B stubs

KiCad 9.0.2: collect-all Remove once, Save, reload before Adds (no mid-session GetTracks after Remove).
P0.08 probed separately; not kept. Stopped at unconnected=78 per PM one-cycle rule.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30f-connect"
F, B = pcbnew.F_Cu, pcbnew.B_Cu


def add_trk(board, net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)


def add_via(board, net, x, y, dia=0.60, drill=0.30):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(dia))
    v.SetWidth(pcbnew.B_Cu, pcbnew.FromMM(dia))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(board.FindNet(net))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)


def rip_walls(board):
    doomed = []
    for t in list(board.Tracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net, ly = t.GetNetname(), t.GetLayer()
        x1 = pcbnew.ToMM(t.GetStart().x)
        y1 = pcbnew.ToMM(t.GetStart().y)
        x2 = pcbnew.ToMM(t.GetEnd().x)
        y2 = pcbnew.ToMM(t.GetEnd().y)
        if net == "VDD_GPIO" and ly == B and abs(y1 - 14.8) < 0.05 and abs(y2 - 14.8) < 0.05 and min(x1, x2) < 50 and max(x1, x2) > 60:
            doomed.append(t)
        elif net == "P0.15" and ly == B and abs(y1 - 15.35) < 0.05 and abs(y2 - 15.35) < 0.05 and min(x1, x2) < 50 and max(x1, x2) > 60:
            doomed.append(t)
        elif net == "ENABLE" and ly == B and abs(y1 - 20.3) < 0.05 and abs(y2 - 20.3) < 0.05 and min(x1, x2) < 52 and max(x1, x2) > 55:
            doomed.append(t)
        elif net == "VDD2_MID" and ly == B and abs(y1 - 16.87) < 0.05 and abs(y2 - 16.87) < 0.05 and min(x1, x2) < 60 and max(x1, x2) > 65:
            doomed.append(t)
    for t in doomed:
        board.Remove(t)
    return len(doomed)


def commit_paths(board):
    paths = [
        ("VIN_FILT", B, 0.30, [(55.35, 13.3), (51.9, 13.3), (51.9, 21.9)]),
        ("VDD_GPIO", B, 0.25, [(70.0, 14.8), (70.0, 9.0), (48.05, 9.0), (48.05, 14.8)]),
        ("ENABLE", F, 0.18, [(50.85, 23.15), (50.85, 20.30), (56.50, 20.30)]),
        ("VDD2_MID", B, 0.25, [(58.14, 16.87), (58.14, 17.80), (67.21, 17.80), (67.21, 16.87)]),
    ]
    for net, ly, w, pts in paths:
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            add_trk(board, net, a[0], a[1], b[0], b[1], w, ly)
    add_via(board, "P0.15", 51.0, 16.5)
    add_via(board, "P0.15", 60.0, 16.5)
    for pts, ly in [
        ([(46.70, 15.35), (51.0, 15.35), (51.0, 16.5)], B),
        ([(60.0, 16.5), (60.0, 15.35), (72.00, 15.35)], B),
        ([(51.0, 16.5), (51.0, 19.5), (60.0, 19.5), (60.0, 16.5)], F),
    ]:
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            add_trk(board, "P0.15", a[0], a[1], b[0], b[1], 0.18, ly)


def main():
    os.makedirs(SNAP, exist_ok=True)
    print("Pass30f replay helper — prefer reports/PASS30F_SUMMARY.json for outcomes.")
    print(f"Board {BOARD}")
    board = pcbnew.LoadBoard(BOARD)
    n = rip_walls(board)
    pcbnew.SaveBoard(f"{SNAP}/after-rip4.kicad_pcb", board)
    print("ripped", n)
    board = pcbnew.LoadBoard(f"{SNAP}/after-rip4.kicad_pcb")
    commit_paths(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    shutil.copy2(BOARD, f"{SNAP}/after-vinfilt-restores.kicad_pcb")
    print("saved; run kicad-cli pcb drc for AFTER JSON")


if __name__ == "__main__":
    # Do not auto-run destructive replay unless explicitly invoked with --apply
    if "--apply" in sys.argv:
        main()
    else:
        print(__doc__)
        print("Invoke with --apply to replay onto live board (usually already applied).")
