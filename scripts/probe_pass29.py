#!/usr/bin/env python3
"""Read-only: classify P0.15 west wrap vs east/J18 copper and graph connectivity."""
from __future__ import annotations

import sys
from collections import defaultdict, deque

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def node(x, y, prec=2):
    return (round(x, prec), round(y, prec))


def main():
    board, r = reload()
    p = r.u1("P0.15")
    print("U1", p)
    print("vias", [(round(v["x"], 2), round(v["y"], 2)) for v in r.vias if v["n"] == "P0.15"])
    pads = [(q["ref"], q["num"], round(q["x"], 2), round(q["y"], 2)) for q in r.pads if q["name"] == "P0.15"]
    print("pads", pads)
    print("\n==== all P0.15 copper ====")
    segs = []
    for t in r.tracks:
        if t["n"] != "P0.15":
            continue
        ly = "F" if t["ly"] == F else ("B" if t["ly"] == B else str(t["ly"]))
        print(f"  {ly} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")
        segs.append((ly, t["x1"], t["y1"], t["x2"], t["y2"]))

    # Graph on B+F+vias+pads
    g = defaultdict(set)
    pts = {}

    def add_edge(a, b, kind):
        g[a].add(b)
        g[b].add(a)
        pts[a] = a
        pts[b] = b

    for ly, x1, y1, x2, y2 in segs:
        add_edge(node(x1, y1), node(x2, y2), ly)
    for v in r.vias:
        if v["n"] == "P0.15":
            add_edge(node(v["x"], v["y"]), node(v["x"], v["y"]), "via")
    # connect nearby ends (T-junctions) within 0.25 mm
    keys = list(g.keys())
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if hypot(a[0], a[1], b[0], b[1]) < 0.25:
                add_edge(a, b, "snap")

    def bfs(start, blocked=None):
        blocked = blocked or set()
        q = deque([start])
        seen = {start}
        while q:
            cur = q.popleft()
            for nxt in g[cur]:
                if nxt in seen or nxt in blocked:
                    continue
                # skip edges that use blocked nodes as the only path: we block nodes
                seen.add(nxt)
                q.append(nxt)
        return seen

    u1 = node(p["x"], p["y"])
    j18 = node(43.08, 62.00)
    j12 = node(44.10, 76.00)
    via = node(41.75, 23.10)

    # Identify west-wrap nodes: B tracks in x=31-48 (but not east x>50) and y=20-45
    # excluding the via itself and the east stub from via y=23.10-20.60 at x=41.75
    print("\n==== west-region B segments (x=31–48, y=20–45) ====")
    west_nodes = set()
    for ly, x1, y1, x2, y2 in segs:
        if ly != "B":
            continue
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if 31.0 <= mx <= 48.0 and 20.0 <= my <= 45.0:
            print(f"  WEST-BOX B ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
            west_nodes.add(node(x1, y1))
            west_nodes.add(node(x2, y2))

    print("\nU1 in graph", u1 in g, "J18", j18 in g, "J12", j12 in g, "via", via in g)
    full = bfs(u1)
    print("U1 reaches J18", j18 in full, "J12", j12 in full, "via", via in full, "n=", len(full))

    # Block west wrap nodes except via and except x=41.75 y<=23.10 (east drop)
    keep = set()
    keep.add(via)
    keep.add(node(41.75, 20.60))
    keep.add(node(41.75, 22.50))  # might be T for east H y=22.50
    # Don't keep 22.50 if it's only west... we'll test two scenarios

    block_west = set()
    for n in west_nodes:
        # keep via column x=41.75 y<=23.10 (U1 escape + east drop)
        if abs(n[0] - 41.75) < 0.15 and n[1] <= 23.15:
            continue
        # keep east-going from 22.50 x>=41.75
        if abs(n[1] - 22.50) < 0.15 and n[0] >= 41.70:
            continue
        if abs(n[1] - 21.20) < 0.15 and n[0] >= 46.0:
            continue
        block_west.add(n)

    print("block west nodes", sorted(block_west))
    cut = bfs(u1, blocked=block_west)
    print("AFTER blocking west (keep via+east T): U1->J18", j18 in cut, "J12", j12 in cut, "n=", len(cut))

    # stricter: also block 22.50 east T, keep only 23.10-20.60 V
    block2 = set(west_nodes)
    for n in list(block2):
        if abs(n[0] - 41.75) < 0.15 and n[1] <= 23.15:
            block2.discard(n)
    print("block2 (only keep x=41.75 y<=23.10)", sorted(block2))
    cut2 = bfs(u1, blocked=block2)
    print("AFTER block2: U1->J18", j18 in cut2, "J12", j12 in cut2, "via", via in cut2)


if __name__ == "__main__":
    main()
