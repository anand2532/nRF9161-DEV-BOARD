#!/usr/bin/env python3
"""Layer-aware island dump for remaining ADC nets + gap geometry."""
from __future__ import annotations

import sys
from collections import defaultdict

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
TOL = 0.25


def islands(r, name):
    nodes = []

    def add(x, y, ly, kind, extra=""):
        nodes.append({"x": x, "y": y, "ly": ly, "k": kind, "e": extra})

    for t in r.tracks:
        if t["n"] != name:
            continue
        add(t["x1"], t["y1"], t["ly"], "trk", f"{t['x1']:.2f},{t['y1']:.2f}->{t['x2']:.2f},{t['y2']:.2f}")
        add(t["x2"], t["y2"], t["ly"], "trk", "")
    for v in r.vias:
        if v["n"] != name:
            continue
        add(v["x"], v["y"], F, "via", "")
        add(v["x"], v["y"], B, "via", "")
    for p in r.pads:
        if p["name"] != name:
            continue
        lys = [F, B] if p.get("pth") else [F]
        for ly in lys:
            add(p["x"], p["y"], ly, "pad", p.get("ref", ""))

    parent = list(range(len(nodes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b

    for i, a in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            if a["ly"] != b["ly"]:
                continue
            if abs(a["x"] - b["x"]) <= TOL and abs(a["y"] - b["y"]) <= TOL:
                union(i, j)
    groups = defaultdict(list)
    for i, n in enumerate(nodes):
        groups[find(i)].append(n)
    return groups


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    for name in ["P0.13", "P0.14", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "P0.15"]:
        g = islands(r, name)
        print(f"\n=== {name} islands={len(g)} ===")
        for k, nodes in g.items():
            pads = sorted({n["e"] for n in nodes if n["k"] == "pad" and n["e"]})
            vias = [(n["x"], n["y"]) for n in nodes if n["k"] == "via"]
            trks = [n for n in nodes if n["k"] == "trk"]
            xs = [n["x"] for n in nodes]
            ys = [n["y"] for n in nodes]
            lys = sorted({n["ly"] for n in nodes})
            print(
                f"  pads={pads} vias={len(vias)} trkpts={len(trks)} "
                f"bbox=({min(xs):.2f},{min(ys):.2f})-({max(xs):.2f},{max(ys):.2f}) layers={lys}"
            )
            if vias:
                uniq = sorted({(round(v[0], 2), round(v[1], 2)) for v in vias})
                print(f"    viaXY={uniq[:8]}")


if __name__ == "__main__":
    main()
