#!/usr/bin/env python3
"""Read-only: KiCad connectivity for P0.15 west wrap vs east bus."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def mm(p):
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def is_west_wrap_track(tr):
    """West courtyard snake only — not via column east drop, not east T, not J18 south."""
    if isinstance(tr, pcbnew.PCB_VIA):
        return False
    if tr.GetNetname() != "P0.15" or tr.GetLayer() != B:
        return False
    x1, y1 = mm(tr.GetStart())
    x2, y2 = mm(tr.GetEnd())
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    # Keep via-column V x=41.75 y=20.60–23.10 (east drop stub)
    if abs(mx - 41.75) < 0.20 and max(y1, y2) <= 23.20 and min(y1, y2) >= 20.40:
        return False
    # Keep east T y=22.50 x=41.75–46.50 and stub x=46.50
    if abs(my - 22.50) < 0.20 and min(x1, x2) >= 41.60:
        return False
    if abs(mx - 46.50) < 0.20 and min(y1, y2) >= 21.00 and max(y1, y2) <= 22.70:
        return False
    # West snake: courtyard west of via, y~22.5–59.2, plus J18 entry H y=59.20
    if mx < 41.60 and 20.0 <= my <= 60.0:
        return True
    if abs(my - 59.20) < 0.25 and max(x1, x2) <= 44.0:
        return True
    if abs(mx - 43.08) < 0.20 and min(y1, y2) >= 58.9 and max(y1, y2) <= 62.2:
        return True  # last V into J18 pad from wrap
    return False


def cluster_items(items, conn):
    """BFS through GetConnectedItems."""
    seen = set()
    clusters = []
    for it in items:
        iid = id(it)
        if iid in seen:
            continue
        q = [it]
        seen.add(iid)
        cl = []
        while q:
            cur = q.pop()
            cl.append(cur)
            for nxt in conn.GetConnectedItems(cur):
                if nxt not in items:
                    continue
                nid = id(nxt)
                if nid in seen:
                    continue
                seen.add(nid)
                q.append(nxt)
        clusters.append(cl)
    return clusters


def describe(it):
    if isinstance(it, pcbnew.PCB_VIA):
        x, y = mm(it.GetPosition())
        return f"via({x:.2f},{y:.2f})"
    if isinstance(it, pcbnew.PAD):
        x, y = mm(it.GetPosition())
        return f"pad {it.GetParent().GetReference()}.{it.GetNumber()} ({x:.2f},{y:.2f})"
    if isinstance(it, pcbnew.PCB_TRACK):
        x1, y1 = mm(it.GetStart())
        x2, y2 = mm(it.GetEnd())
        ly = "F" if it.GetLayer() == F else ("B" if it.GetLayer() == B else str(it.GetLayer()))
        return f"{ly} ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})"
    return str(it)


def main():
    board, r = reload()
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    items = []
    for tr in board.GetTracks():
        if tr.GetNetname() == "P0.15":
            items.append(tr)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "P0.15":
                items.append(pad)

    print("==== west-wrap tracks that would be deleted ====")
    wrap = []
    for tr in board.GetTracks():
        if is_west_wrap_track(tr):
            wrap.append(tr)
            print(" ", describe(tr))
    print(f"count={len(wrap)}")

    wrap_ids = {id(t) for t in wrap}
    remaining = [it for it in items if id(it) not in wrap_ids]
    print("\n==== clusters if west wrap removed ====")
    clusters = cluster_items(remaining, conn)
    for i, cl in enumerate(clusters):
        pads = [describe(x) for x in cl if isinstance(x, pcbnew.PAD)]
        vias = [describe(x) for x in cl if isinstance(x, pcbnew.PCB_VIA)]
        ntrk = sum(1 for x in cl if isinstance(x, pcbnew.PCB_TRACK) and not isinstance(x, pcbnew.PCB_VIA))
        print(f"  cluster {i}: pads={pads} vias={vias} tracks={ntrk} n={len(cl)}")

    # current clusters (should be 1)
    print("\n==== current clusters (wrap kept) ====")
    for i, cl in enumerate(cluster_items(items, conn)):
        pads = [describe(x) for x in cl if isinstance(x, pcbnew.PAD)]
        print(f"  cluster {i}: pads={pads} n={len(cl)}")

    # Does 41.75,20.60 touch any track toward x=106?
    print("\n==== tracks touching (41.75,20.60) or (106.00,20.60) ====")
    for tr in board.GetTracks():
        if tr.GetNetname() != "P0.15" or isinstance(tr, pcbnew.PCB_VIA):
            continue
        x1, y1 = mm(tr.GetStart())
        x2, y2 = mm(tr.GetEnd())
        for px, py in ((41.75, 20.60), (106.00, 20.60), (46.50, 21.20)):
            if hypot(x1, y1, px, py) < 0.30 or hypot(x2, y2, px, py) < 0.30:
                print(f"  near ({px:.2f},{py:.2f}): {describe(tr)}")
                break


if __name__ == "__main__":
    main()
