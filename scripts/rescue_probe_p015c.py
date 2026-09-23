#!/usr/bin/env python3
"""Dense occupancy A* + explicit SE columns for P0.15."""
from __future__ import annotations

import heapq
import math
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import dist_seg, hypot, in_box, RF_BOX  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402

B = pcbnew.B_Cu
W = 0.18
NAME = "P0.15"
PITCH = 0.25


def path_ok(r, pts):
    for a, b in zip(pts, pts[1:]):
        if hypot(a[0], a[1], b[0], b[1]) < 0.03:
            continue
        if not r.track_clear(a[0], a[1], b[0], b[1], B, W, NAME):
            return f"{a}->{b}: " + why(r, [a, b], B, W, NAME)
    return None


def astar(r, x1, y1, x2, y2, x0, y0, x3, y3):
    blocked = set()
    rad_via = 0.30 + W / 2 + 0.16  # ~0.55
    for v in r.vias:
        if v["n"] == NAME:
            continue
        rr = v["r"] + W / 2 + 0.16
        i0, i1 = int((v["x"] - rr) / PITCH), int((v["x"] + rr) / PITCH)
        j0, j1 = int((v["y"] - rr) / PITCH), int((v["y"] + rr) / PITCH)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if hypot(i * PITCH, j * PITCH, v["x"], v["y"]) <= rr:
                    blocked.add((i, j))
    for p in r.pads:
        if p["name"] == NAME or not p["pth"]:
            continue
        rr = p["r"] + 0.22
        i0, i1 = int((p["x"] - rr) / PITCH), int((p["x"] + rr) / PITCH)
        j0, j1 = int((p["y"] - rr) / PITCH), int((p["y"] + rr) / PITCH)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if hypot(i * PITCH, j * PITCH, p["x"], p["y"]) <= rr:
                    blocked.add((i, j))
    for t in r.tracks:
        if t["ly"] != B or t["n"] == NAME:
            continue
        rr = t["w"] / 2 + W / 2 + 0.16
        dist = hypot(t["x1"], t["y1"], t["x2"], t["y2"])
        nseg = max(1, int(dist / (PITCH * 0.4)))
        for k in range(nseg + 1):
            tt = k / nseg
            x = t["x1"] + tt * (t["x2"] - t["x1"])
            y = t["y1"] + tt * (t["y2"] - t["y1"])
            i0, i1 = int((x - rr) / PITCH), int((x + rr) / PITCH)
            j0, j1 = int((y - rr) / PITCH), int((y + rr) / PITCH)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if hypot(i * PITCH, j * PITCH, x, y) <= rr:
                        blocked.add((i, j))
    # RF keepout
    i0, i1 = 0, int(24.2 / PITCH)
    j0, j1 = int(20.0 / PITCH), int(64.0 / PITCH)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            blocked.add((i, j))

    s = (int(round(x1 / PITCH)), int(round(y1 / PITCH)))
    g = (int(round(x2 / PITCH)), int(round(y2 / PITCH)))
    blocked.discard(s)
    blocked.discard(g)
    imin, imax = int(x0 / PITCH), int(x3 / PITCH)
    jmin, jmax = int(y0 / PITCH), int(y3 / PITCH)

    def h(a):
        return abs(a[0] - g[0]) + abs(a[1] - g[1])

    pq = [(h(s), 0, s)]
    came = {}
    cost = {s: 0}
    steps = 0
    found = None
    while pq and steps < 200000:
        _, gc, cur = heapq.heappop(pq)
        steps += 1
        if cur == g:
            found = cur
            break
        if gc != cost.get(cur):
            continue
        i, j = cur
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (i + di, j + dj)
            if nxt[0] < imin or nxt[0] > imax or nxt[1] < jmin or nxt[1] > jmax:
                continue
            if nxt in blocked:
                continue
            ng = gc + 1
            if ng < cost.get(nxt, 1e9):
                cost[nxt] = ng
                came[nxt] = cur
                heapq.heappush(pq, (ng + h(nxt), ng, nxt))
    print(f"  A* steps={steps} found={found is not None} blocked={len(blocked)}")
    if not found:
        return None
    cells = [g]
    while cells[-1] != s:
        cells.append(came[cells[-1]])
    cells.reverse()
    pts = [(x1, y1)]
    for i, j in cells:
        pts.append((i * PITCH, j * PITCH))
    pts.append((x2, y2))
    comp = [pts[0]]
    for p in pts[1:]:
        if len(comp) >= 2 and (
            (abs(comp[-1][0] - comp[-2][0]) < 0.06 and abs(p[0] - comp[-1][0]) < 0.06)
            or (abs(comp[-1][1] - comp[-2][1]) < 0.06 and abs(p[1] - comp[-1][1]) < 0.06)
        ):
            comp[-1] = p
            continue
        comp.append(p)
    return comp


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("==== explicit SE columns ====")
    for x in (46.50, 47.00, 47.40, 47.80, 48.20, 48.60, 49.60, 50.20, 51.20):
        for ygate in (23.6, 24.2, 24.8, 26.0, 39.8, 41.6, 45.0):
            pts = [
                (46.50, 21.20),
                (x, 21.20),
                (x, ygate),
                (x, 58.80),
                (43.08, 58.80),
                (43.08, 62.00),
            ]
            err = path_ok(r, pts)
            if err is None:
                print(f"CLEAR SE x={x:.2f} ygate={ygate:.1f}")
            # only print clears and a few blocks

    print("==== A* north band stub->x106 ====")
    pts = astar(r, 46.50, 21.20, 106.00, 20.60, 40.0, 15.5, 108.0, 24.5)
    if pts:
        err = path_ok(r, pts)
        print(" path n=", len(pts), "CLEAR" if err is None else err)
        for p in pts:
            print(f"   {p[0]:.2f},{p[1]:.2f}")
    else:
        print(" no A* north")

    print("==== A* SE via->J18 ====")
    pts = astar(r, 46.50, 21.20, 43.08, 59.20, 40.0, 20.0, 72.0, 62.0)
    if pts:
        err = path_ok(r, pts)
        print(" path n=", len(pts), "CLEAR" if err is None else err)
        for p in pts[:40]:
            print(f"   {p[0]:.2f},{p[1]:.2f}")
        if len(pts) > 40:
            print(f"   ... {len(pts)} pts")
    else:
        print(" no A* SE")

    print("==== A* via 41.75,23.10 -> 106,20.60 wider ====")
    pts = astar(r, 41.75, 23.10, 106.00, 20.60, 24.5, 6.0, 118.0, 50.0)
    if pts:
        err = path_ok(r, pts)
        print(" path n=", len(pts), "CLEAR" if err is None else err)
        for p in pts[:50]:
            print(f"   {p[0]:.2f},{p[1]:.2f}")
    else:
        print(" no A* wide")


if __name__ == "__main__":
    main()
