#!/usr/bin/env python3
"""Close short F.Cu islands with jogs around 0402 GND pads. No B.Cu, no RF rewrite."""
from __future__ import annotations

import json
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import BOARD, RF_NETS, Router, hypot, net_width  # noqa: E402

DRC = "/tmp/nrf_fcu.json"


def pairs():
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", DRC, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    data = json.load(open(DRC))
    out = []
    for u in data.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        def net(d):
            return d.split("[")[1].split("]")[0] if "[" in d else ""
        n = net(a["description"]) or net(b["description"])
        if n in ("", "GND"):
            continue
        pth = "PTH" in a["description"] or "PTH" in b["description"]
        via = "Via" in a["description"] or "Via" in b["description"]
        out.append(
            {
                "n": n,
                "x1": a["pos"]["x"],
                "y1": a["pos"]["y"],
                "x2": b["pos"]["x"],
                "y2": b["pos"]["y"],
                "pth": pth,
                "via": via,
                "rf": n in RF_NETS,
            }
        )
    out.sort(key=lambda p: hypot(p["x1"], p["y1"], p["x2"], p["y2"]))
    shorts = sum(1 for v in data.get("violations", []) if v.get("type") == "shorting_items")
    return out, len(data.get("unconnected_items", [])), shorts


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Router(board)
    r.collect()
    ps, n0, sh0 = pairs()
    print("start", n0, "shorts", sh0, "pairs", len(ps), flush=True)
    closed = 0
    for p in ps:
        d = hypot(p["x1"], p["y1"], p["x2"], p["y2"])
        if d > 22 or (p["pth"] and d > 8):
            continue
        name = p["n"]
        net = board.FindNet(name)
        if not net:
            continue
        code = net.GetNetCode()
        w = 0.20 if p["rf"] else net_width(name)
        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        jogs = [
            [(x1, y1), (x2, y1), (x2, y2)],
            [(x1, y1), (x1, y2), (x2, y2)],
        ]
        for dy in (-0.70, 0.70, -1.10, 1.10, -1.60, 1.60, -2.20, 2.20):
            jogs.append([(x1, y1), (x1, y1 + dy), (x2, y1 + dy), (x2, y2)])
            jogs.append([(x1, y1), (x1 + dy, y1), (x1 + dy, y2), (x2, y2)])
        ok = False
        for pts in jogs:
            if r.commit(pts, pcbnew.F_Cu, w, code, name):
                ok = True
                break
        if not ok and d < 12:
            ok = r.route_f(x1, y1, x2, y2, name, w, code)
        if ok:
            closed += 1
            print("closed", name, f"{d:.1f}mm", flush=True)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    _, n1, sh1 = pairs()
    print(f"closed={closed} unconnected {n0}->{n1} shorts={sh1}", flush=True)
    return 0 if sh1 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
