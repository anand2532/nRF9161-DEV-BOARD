#!/usr/bin/env python3
"""Phases 1–3: classify remaining unconnected items and probe new corridors.

Does not modify copper. Writes reports/RESCUE_BEFORE.csv.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict, deque

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot, in_box, RF_BOX, U1_BOX, J18_BOX  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    Final,
    classify_pair,
    parse_drc,
)

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
REP = f"{ROOT}/reports"
DRC = "/tmp/nrf_rescue_drc_full.json"
F, B = pcbnew.F_Cu, pcbnew.B_Cu

INTENTIONAL_NC = {
    # SIM_DET U1 pad 45 is Nordic-PS floating; mechanical detect is SIM_CD.
}
DNP_RF = {"ANT_FIT", "AUX", "AUX_FIT"}
PRIORITY = [
    "U1 power",
    "U1 control",
    "SIM",
    "SWD",
    "GNSS bias",
    "MAGPIO/MIPI/COEX",
    "GPIO",
    "header duplicates",
    "DNP",
    "GND",
]


def prio(net, cls, a, b):
    blob = a + " " + b
    if net.startswith(("VDD", "VIN", "DEC")):
        return "U1 power"
    if net in ("nRESET", "ENABLE", "nRESET_SW"):
        return "U1 control"
    if net.startswith("SIM"):
        return "SIM"
    if net in ("SWDCLK", "SWDIO"):
        return "SWD"
    if "GNSS" in net:
        return "GNSS bias"
    if net.startswith(("MAGPIO", "MIPI", "COEX")):
        return "MAGPIO/MIPI/COEX"
    if cls == "G":
        return "header duplicates"
    if cls == "C" or net in DNP_RF:
        return "DNP"
    if net == "GND" or cls == "E":
        return "GND"
    if net.startswith("P0.") or "GPIO" in net:
        return "GPIO"
    if " of U1" in blob:
        return "U1 control"
    return "GPIO"


def problem_of(net, cls, a, b, ax, ay, bx, by):
    if cls == "E":
        return "GND F.Cu zone island (plane, not a missing GPIO hop)"
    if cls == "C":
        return "DNP 50Ω shunt stub not tied to existing same-net trunk"
    if cls == "G":
        return "duplicate expansion-header branch (same net on two headers)"
    if cls == "F":
        return "F.Cu power/control island gap"
    if " of U1" in a or " of U1" in b:
        return "U1 pad island not joined to header/existing copper"
    return "routing gap between copper islands"


def proposed(net, cls, a, b):
    if cls == "E":
        return "refill/stitch GND; no dummy copper"
    if cls == "C":
        return "optional stub to existing same-net copper; do not rewrite 50Ω trunks"
    if cls == "G":
        return "B.Cu/F.Cu private header-to-header hop or accept after GPIO spine exists"
    if net == "P0.15":
        return "NEW east hop via y~20.6 to x=106; then DELETE west wrap"
    if net in ("P0.13", "P0.14", "P0.16", "P0.17", "P0.18"):
        return "private B.Cu channel after P0.15 west wrap is removed"
    if net.startswith("VIN"):
        return "complete J1→protection→fuse→ferrite F.Cu path"
    if net == "nRESET":
        return "short U1→R5→C39→button/debug→J8; join F/B islands"
    if net.startswith("SIM"):
        return "U1→U4→connector; keep *_C distinct"
    return "legal escape + private layer hop; not the 0.95 mm ring"


def graph_net(r, name):
    g = defaultdict(set)

    def node(x, y):
        return (round(x, 2), round(y, 2))

    def add(a, b):
        g[a].add(b)
        g[b].add(a)

    for t in r.tracks:
        if t["n"] != name:
            continue
        add(node(t["x1"], t["y1"]), node(t["x2"], t["y2"]))
    for v in r.vias:
        if v["n"] == name:
            n = node(v["x"], v["y"])
            g.setdefault(n, set())
    for p in r.pads:
        if p["name"] != name:
            continue
        n = node(p["x"], p["y"])
        g.setdefault(n, set())
    keys = list(g.keys())
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if hypot(a[0], a[1], b[0], b[1]) < 0.28:
                add(a, b)
    seen = set()
    islands = []
    for n in g:
        if n in seen:
            continue
        q = deque([n])
        seen.add(n)
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nxt in g[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        islands.append(comp)
    return islands


def probe_hline(r, y, x0, x1, layer, w, name, step=0.40):
    """Return first blocker along a horizontal, or None if clear."""
    from final_pass7 import why

    x = x0
    dx = step if x1 >= x0 else -step
    while (dx > 0 and x < x1) or (dx < 0 and x > x1):
        xn = x + dx
        if (dx > 0 and xn > x1) or (dx < 0 and xn < x1):
            xn = x1
        pts = [(x, y), (xn, y)]
        if not r.track_clear(x, y, xn, y, layer, w, name):
            return why(r, pts, layer, w, name), (x, xn)
        x = xn
    return None, None


def main():
    os.makedirs(REP, exist_ok=True)
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    pairs, n, counts, data = parse_drc(DRC)
    print(f"unconnected={n} shorts={counts.get('shorting_items',0)} "
          f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)}")
    print("violation counts:", dict(sorted(counts.items(), key=lambda kv: -kv[1]))[:12]
          if False else dict(sorted(counts.items(), key=lambda kv: -kv[1])))

    rows = []
    by_cls = Counter()
    for p in pairs:
        net, cls = p["net"], p["cls"]
        a, b = p["a"], p["b"]
        kind = "genuine"
        if cls == "E":
            kind = "plane"
        elif cls == "C":
            kind = "DNP"
        elif cls == "G":
            kind = "duplicate header"
        elif net in INTENTIONAL_NC:
            kind = "intentional NC"
        elif cls == "F":
            kind = "routing gap"
        else:
            kind = "genuine"
        by_cls[cls] += 1
        copper = []
        if p["a_f"] or p["b_f"]:
            copper.append("F.Cu")
        if p["a_b"] or p["b_b"]:
            copper.append("B.Cu")
        layer = "+".join(copper) if copper else "?"
        rows.append(
            {
                "Net": net,
                "Source": a,
                "Destination": b,
                "Current layer": layer,
                "Current copper": f"({p['ax']:.3f},{p['ay']:.3f})-({p['bx']:.3f},{p['by']:.3f})",
                "Problem": problem_of(net, cls, a, b, p["ax"], p["ay"], p["bx"], p["by"]),
                "Proposed solution": proposed(net, cls, a, b),
                "Status": f"{kind}|class {cls}|prio {prio(net, cls, a, b)}|OPEN",
            }
        )

    outp = f"{REP}/RESCUE_BEFORE.csv"
    with open(outp, "w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Net",
                "Source",
                "Destination",
                "Current layer",
                "Current copper",
                "Problem",
                "Proposed solution",
                "Status",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {outp} rows={len(rows)} class={dict(by_cls)}")

    # Island graphs for open nets
    nets = sorted(set(p["net"] for p in pairs))
    print("\n==== island graphs ====")
    for name in nets:
        if name == "GND":
            continue
        islands = graph_net(r, name)
        print(f"  {name}: {len(islands)} islands sizes={[len(i) for i in islands[:8]]}")

    # P0.15 wrap vs east
    print("\n==== P0.15 occupancy / east hop probe ====")
    p015 = [t for t in r.tracks if t["n"] == "P0.15"]
    print(f"  tracks={len(p015)} vias={[ (round(v['x'],2), round(v['y'],2)) for v in r.vias if v['n']=='P0.15']}")
    for y in (20.60, 21.20, 19.80, 18.40, 17.20, 16.00, 14.80, 13.20, 12.00, 10.80, 9.40, 8.40, 7.40, 22.50, 23.10):
        blocker, span = probe_hline(r, y, 41.75, 106.00, B, 0.18, "P0.15")
        if blocker:
            print(f"  y={y:.2f} BLOCKED {span} {blocker}")
        else:
            print(f"  y={y:.2f} CLEAR 41.75→106")

    # West courtyard occupancy after hypothetical wrap delete
    print("\n==== B.Cu foreign occupancy west courtyard x=24.6–41.5 y=22–60 ====")
    occ = Counter()
    for t in r.tracks:
        if t["ly"] != B:
            continue
        mx, my = (t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2
        if 24.6 <= mx <= 41.5 and 22.0 <= my <= 60.0:
            occ[t["n"]] += 1
    print(" ", dict(occ.most_common(20)))

    # Headers
    print("\n==== headers ====")
    for ref in ("J1", "J8", "J9", "J10", "J11", "J12", "J13", "J14", "J15", "J16", "J17", "J18"):
        fp = board.FindFootprintByReference(ref)
        if not fp:
            print(f"  {ref} MISSING")
            continue
        pos = fp.GetPosition()
        print(f"  {ref} ({pcbnew.ToMM(pos.x):.2f},{pcbnew.ToMM(pos.y):.2f}) rot={fp.GetOrientationDegrees()} {fp.GetFPID().GetLibItemName()}")

    u1 = board.FindFootprintByReference("U1")
    pos = u1.GetPosition()
    print(f"\nU1 ({pcbnew.ToMM(pos.x):.2f},{pcbnew.ToMM(pos.y):.2f}) rot={u1.GetOrientationDegrees()}")
    p45 = None
    for pad in u1.Pads():
        if pad.GetNumber() == "45":
            p45 = pad
            break
    print(f"U1 pad45 SIM_DET net='{p45.GetNetname() if p45 else '?'}'")

    # In2 plane
    for z in board.Zones():
        print(f"  zone net={z.GetNetname()} layer={z.GetLayerName()} pri={z.GetAssignedPriority()}")


if __name__ == "__main__":
    main()
