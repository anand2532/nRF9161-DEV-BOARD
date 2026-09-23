#!/usr/bin/env python3
"""Pass 29 BOUNDING: test P0.15 west-wrap redundancy. Do not add copper.

If U1 P0.15 still reaches J18/J12 without the west courtyard snake, delete
only that wrap. If load-bearing, do not rip, do not add a third path, stop.
"""
from __future__ import annotations

import shutil
import sys
from collections import defaultdict, deque

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, fill_zones, run_drc  # noqa: E402
from final_pass14 import (  # noqa: E402
    class_counts,
    reload,
    snap_path,
    write_gpio_csv,
    write_unconnected_csv,
)
from final_pass21 import leftover_f  # noqa: E402
import final_pass25 as p25  # noqa: E402

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu


def node(x, y, prec=2):
    return (round(x, prec), round(y, prec))


def p015_graph(r):
    g = defaultdict(set)
    segs = []
    for t in r.tracks:
        if t["n"] != "P0.15":
            continue
        ly = "F" if t["ly"] == F else ("B" if t["ly"] == B else str(t["ly"]))
        segs.append((ly, t["x1"], t["y1"], t["x2"], t["y2"]))
        a, b = node(t["x1"], t["y1"]), node(t["x2"], t["y2"])
        g[a].add(b)
        g[b].add(a)
    keys = list(g.keys())
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if hypot(a[0], a[1], b[0], b[1]) < 0.25:
                g[a].add(b)
                g[b].add(a)
    return g, segs


def bfs(g, start, blocked=None):
    blocked = blocked or set()
    q = deque([start])
    seen = {start}
    while q:
        cur = q.popleft()
        for nxt in g[cur]:
            if nxt in seen or nxt in blocked:
                continue
            seen.add(nxt)
            q.append(nxt)
    return seen


def west_box_nodes(segs):
    west = set()
    for ly, x1, y1, x2, y2 in segs:
        if ly != "B":
            continue
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if 31.0 <= mx <= 48.0 and 20.0 <= my <= 45.0:
            west.add(node(x1, y1))
            west.add(node(x2, y2))
    return west


def wrap_is_load_bearing(r):
    """True if U1 pad would lose J18/J12 without west courtyard snake.

    Keep via column x=41.75 y<=23.10 and east T y=22.50 x>=41.75 / x=46.50 stub.
    """
    g, segs = p015_graph(r)
    p = r.u1("P0.15")
    u1 = node(p["x"], p["y"])
    j18 = node(43.08, 62.00)
    j12 = node(44.10, 76.00)
    via = node(41.75, 23.10)
    full = bfs(g, u1)
    print(
        f"  full: U1->J18={j18 in full} J12={j12 in full} via={via in full}",
        flush=True,
    )
    block = set()
    for n in west_box_nodes(segs):
        if abs(n[0] - 41.75) < 0.15 and n[1] <= 23.15:
            continue
        if abs(n[1] - 22.50) < 0.15 and n[0] >= 41.70:
            continue
        if abs(n[1] - 21.20) < 0.15 and n[0] >= 46.0:
            continue
        block.add(n)
    # Also block remaining west snake south of y=45 (x=32.20 V and y=59.20 H)
    for ly, x1, y1, x2, y2 in segs:
        if ly != "B":
            continue
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if mx < 41.60 and 20.0 <= my <= 60.0:
            block.add(node(x1, y1))
            block.add(node(x2, y2))
        if abs(my - 59.20) < 0.25 and max(x1, x2) <= 44.0:
            block.add(node(x1, y1))
            block.add(node(x2, y2))
    # Never block via column / U1
    block.discard(via)
    block.discard(u1)
    block.discard(node(41.75, 20.60))
    block.discard(node(41.75, 22.50))
    cut = bfs(g, u1, blocked=block)
    print(
        f"  without west snake: U1->J18={j18 in cut} J12={j12 in cut} "
        f"blocked={sorted(block)}",
        flush=True,
    )
    east_h = any(
        ly == "B"
        and abs((y1 + y2) / 2.0 - 20.60) < 0.20
        and min(x1, x2) <= 42.0
        and max(x1, x2) >= 100.0
        for ly, x1, y1, x2, y2 in segs
    )
    print(f"  H y=20.60 from via to x=106 present={east_h}", flush=True)
    return not (j18 in cut or j12 in cut)


def write_release(n0, n1, shorts, counts, pairs, board, load_bearing):
    cls = class_counts(pairs)
    tracks = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    nvia = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
    leftover = leftover_f(pairs)
    path = f"{REP}/FINAL_FAB_RELEASE.md"
    with open(path, "w") as f:
        f.write("# nRF9161 DEVELOPMENT BOARD — FINAL FAB RELEASE\n\n")
        f.write("**Status: NOT FABRICATION-READY**\n\n")
        f.write(
            f"Hard gate failed: `unconnected_items = {n1}` (must be 0) "
            "and ratsnest is not zero. Fabrication outputs were **not** generated.\n\n"
        )
        f.write("Connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items`.\n\n")
        f.write("| Gate | Result |\n|------|--------|\n")
        f.write(f"| unconnected_items | **{n1}** (need 0) |\n")
        f.write(f"| shorting_items | {shorts} |\n")
        f.write(f"| clearance | {counts.get('clearance', 0)} |\n")
        f.write(f"| hole_clearance | {counts.get('hole_clearance', 0)} |\n")
        f.write("| Gerbers /fab | **not generated** |\n\n")
        f.write("## Board\n\n")
        f.write("| Item | Value |\n|------|--------|\n")
        f.write("| Size | 120 × 80 mm |\n")
        f.write("| Layers | F.Cu / In1.Cu GND / In2.Cu / B.Cu |\n")
        f.write("| In2 plane net | `VDD_nRF` |\n")
        f.write(f"| Tracks | {tracks} |\n")
        f.write(f"| Vias | {nvia} (start 250) |\n")
        f.write("| U1 | (36.0, 32.0) mm, rot 180° |\n")
        f.write("| SIM_DET U1 pad 45 net | `''` (must stay empty) |\n")
        f.write("| Backup | `.mcp-backups/final-fab-20260917-194911/` |\n")
        f.write("| Live snapshot after this pass | `after-pass29.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass28.kicad_pcb` |\n\n")
        f.write("## This pass (P0.15 west-wrap bounding test)\n\n")
        f.write(
            f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. "
            "Absolute cap 80. No copper added. No wrap ripped. "
            "P0.13–P0.18 U1-to-B hops **not retried** (step 1 did not delete). "
            "New vias this pass: 0. Dangling new vias: 0.\n\n"
        )
        if load_bearing:
            f.write(
                "**P0.15 west wrap is load-bearing — not removed.** "
                "U1 pad 25 (41.75, 26.75) reaches J18.3 / J12.16 only through the "
                "courtyard snake from via (41.75, 23.10) west/south "
                "(x≈31.00–36.50, y≈22.50–59.20) into J18 at (43.08, 59.20). "
                "East copper V x=106 y=20.60–77.45 is fed from J18/J12 south stubs "
                "(y=77.45 H), not from an independent via-to-x=106 hop. "
                "Stubs (41.75, 23.10)–(41.75, 20.60) and "
                "(41.75, 22.50)–(46.50, 22.50)–(46.50, 21.20) do **not** reach x=106. "
                "Deleting the wrap would disconnect the U1 pad. "
                "A third P0.15 path was **not** added.\n\n"
            )
        else:
            f.write("**P0.15 west wrap was redundant and removed.**\n\n")
        f.write("**Nets closed this pass:** none\n\n")
        f.write(
            "**Closed this live session (earlier passes):** P0.04 J9 (82→81), "
            "P0.06 J9 (81→80). COEX2 west remnants removed at unconnected=80 "
            "(net stayed ROUTED). This bounding pass closed zero nets.\n\n"
        )
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        f.write(
            "| P0.15 west wrap | **kept** — load-bearing U1-to-J18/J12; "
            "east x=106 is downstream of J18 south stubs |\n"
        )
        f.write(
            "| P0.13–P0.18 U1-to-B | **not attempted** — wrap still occupies "
            "x≈31–41.75 y≈22.5–45; ENABLE via (42.75, 41.10) remains |\n"
        )
        f.write("\n## Remaining unconnected (by class)\n\n")
        f.write("| Class | Count | Meaning |\n|-------|-------|--------|\n")
        f.write(f"| A | {cls.get('A',0)} | U1/via to header or island |\n")
        f.write(f"| F | {cls.get('F',0)} | F.Cu power/SIM/SWD islands |\n")
        f.write(f"| G | {cls.get('G',0)} | Header duplicate branches |\n")
        f.write(f"| C | {cls.get('C',0)} | DNP RF shunts (50 Ω) |\n")
        f.write(f"| E | {cls.get('E',0)} | GND F.Cu zone-to-zone |\n\n")
        f.write("## Named walls (unchanged)\n\n")
        f.write(
            "- **P0.15 west wrap** — via (41.75, 23.10), B courtyard snake "
            "x≈31.00–36.50 y≈22.50–59.20 into J18 (43.08, 59.20). "
            "Blocks P0.13–P0.18 U1-to-existing-B hops.\n"
        )
        f.write(
            "- **ENABLE via (42.75, 41.10)** — occupies the south courtyard "
            "column that ADC hops need after the wrap.\n"
        )
        f.write(
            "- **VIN** — VIN_FILT / VIN_F F-class islands; no 80 mm VIN bus this pass.\n"
        )
        f.write(
            "- **DNP 50 Ω** — class C RF shunt stubs; not closed (F-nets still open).\n"
        )
        f.write("- **GND E** — F.Cu zone-to-zone GND islands.\n\n")
        f.write("### Still-open F targets\n\n")
        for ln in leftover:
            f.write(f"- {ln}\n")
        f.write("\n## Reports\n\n")
        f.write("- `reports/UNCONNECTED_AFTER_FINAL.csv`\n")
        f.write("- `reports/GPIO_FINAL.csv`\n")
        f.write("- `reports/FINAL_FAB_RELEASE.md`\n")
        f.write("- `reports/DRC_AFTER_CONNECT.json`\n")


def main():
    start = snap_path("pass28")
    shutil.copy2(BOARD, snap_path("pass29-start"))
    board, r = reload()
    pairs, n0, counts0, _ = run_drc()
    shorts0 = counts0.get("shorting_items", 0) or 0
    print(
        f"START unconn={n0} shorts={shorts0} {dict(class_counts(pairs))}",
        flush=True,
    )
    if shorts0:
        print("shorts != 0; not saving; stop")
        return 2
    if n0 > 80:
        print(f"start {n0}>80 abort")
        return 2

    print("\n#### P0.15 west-wrap redundancy", flush=True)
    load_bearing = wrap_is_load_bearing(r)
    print(f"  load_bearing={load_bearing}", flush=True)

    if not load_bearing:
        print("UNEXPECTED: wrap classified redundant; this script does not delete.")
        print("Stop without copper change (parent sequence would delete then DRC).")
        return 3

    # Load-bearing: do not rip, do not add a third path, do not retry hops.
    nvia = p25.count_vias(board)
    tracks = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    shutil.copy2(BOARD, snap_path("pass29"))
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n0, shorts0, counts0, pairs, board, True)
    print(
        f"END wrap=LOAD-BEARING kept unconn={n0}->{n0} shorts={shorts0} "
        f"hops=none fab=no tracks={tracks} vias={nvia}",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
