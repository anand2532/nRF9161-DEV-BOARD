#!/usr/bin/env python3
"""Proper layer-aware islands + gap list for P0.13 and nearby ADC."""
from __future__ import annotations

import sys
from collections import defaultdict

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def net_graph(r, name):
    """Union-find: pads, vias (both layers), tracks (union endpoints)."""
    nodes = []  # (x, y, ly, kind, extra)

    def add(x, y, ly, kind, extra=""):
        nodes.append((round(x, 3), round(y, 3), ly, kind, extra))
        return len(nodes) - 1

    parent = []

    def ensure():
        while len(parent) < len(nodes):
            parent.append(len(parent))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b

    def snap_union(x, y, ly, idx):
        for i, n in enumerate(nodes):
            if n[2] != ly:
                continue
            if hypot(n[0], n[1], x, y) <= 0.20:
                union(i, idx)

    for t in r.tracks:
        if t["n"] != name:
            continue
        i1 = add(t["x1"], t["y1"], t["ly"], "trk", "")
        i2 = add(t["x2"], t["y2"], t["ly"], "trk", "")
        ensure()
        union(i1, i2)
        snap_union(t["x1"], t["y1"], t["ly"], i1)
        snap_union(t["x2"], t["y2"], t["ly"], i2)

    for v in r.vias:
        if v["n"] != name:
            continue
        iF = add(v["x"], v["y"], F, "via", "")
        iB = add(v["x"], v["y"], B, "via", "")
        ensure()
        union(iF, iB)  # via stitches layers
        snap_union(v["x"], v["y"], F, iF)
        snap_union(v["x"], v["y"], B, iB)

    for p in r.pads:
        if p["name"] != name:
            continue
        lys = [F, B] if p.get("pth") else [F]
        ids = []
        for ly in lys:
            idx = add(p["x"], p["y"], ly, "pad", p["ref"])
            ids.append(idx)
        ensure()
        if p.get("pth") and len(ids) == 2:
            union(ids[0], ids[1])
        for idx, ly in zip(ids, lys):
            snap_union(p["x"], p["y"], ly, idx)

    ensure()
    groups = defaultdict(list)
    for i, n in enumerate(nodes):
        groups[find(i)].append(n)
    return groups


def summarize(groups):
    out = []
    for g in groups.values():
        pads = sorted({n[4] for n in g if n[3] == "pad" and n[4]})
        vias = sorted({(n[0], n[1]) for n in g if n[3] == "via"})
        xs = [n[0] for n in g]
        ys = [n[1] for n in g]
        lys = sorted({n[2] for n in g})
        out.append(
            {
                "pads": pads,
                "vias": vias,
                "n": len(g),
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
                "lys": lys,
                "pts": [(n[0], n[1], n[2]) for n in g],
            }
        )
    out.sort(key=lambda z: -z["n"])
    return out


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    for name in ["P0.13", "P0.14", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "P0.15", "COEX0", "VIN_FILT", "VIN_F"]:
        g = summarize(net_graph(r, name))
        print(f"\n=== {name} islands={len(g)} ===")
        for i, z in enumerate(g[:8]):
            print(
                f"  [{i}] n={z['n']} pads={z['pads']} vias={z['vias'][:4]} "
                f"bbox=({z['bbox'][0]:.2f},{z['bbox'][1]:.2f})-({z['bbox'][2]:.2f},{z['bbox'][3]:.2f}) ly={z['lys']}"
            )
        if len(g) >= 2:
            # closest points between island 0 (largest) and others
            a = g[0]["pts"]
            for j, z in enumerate(g[1:6], 1):
                best = None
                for p in a:
                    for q in z["pts"]:
                        if p[2] != q[2]:
                            continue
                        d = hypot(p[0], p[1], q[0], q[1])
                        if best is None or d < best[0]:
                            best = (d, p, q)
                if best:
                    d, p, q = best
                    same = p[2]
                    layer = "F" if same == F else "B"
                    err = pok(r, [(p[0], p[1]), (q[0], q[1])], same, name)
                    print(f"    vs[{j}] closest {d:.3f}mm {layer} {p[:2]}->{q[:2]} straight={err}")


if __name__ == "__main__":
    main()
