#!/usr/bin/env python3
"""Pass 14: close F-class islands with jogs / short B.Cu hops; finish P0.06 headers.

Loads the LIVE board. Never restores RF-only backup, never wipes B.Cu,
never calls complete_route.main() or rebuild_bcu, never re-places the 11
extra U1 vias pass13 deleted. DRC after each net. Save only if shorts stay 0
and unconnected does not rise above the start count.
"""
from __future__ import annotations

import csv
import heapq
import json
import os
import shutil
import sys
from collections import Counter, defaultdict

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    DRC_JSON,
    SNAP_DIR,
    Final,
    fill_zones,
    run_drc,
)
from final_pass7 import why  # noqa: E402

ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}
REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"
ROOT = "/home/anand/kicad-projects/nRF9161-DEV-BOARD"

# Orthogonal search grid (includes west wrap, stub, east of P0.15, north of SIM_RST).
XS = [
    21.24, 25.10, 25.55, 26.20, 28.40, 32.20, 32.67, 34.00,
    42.75, 44.00, 45.15, 46.50, 47.40, 48.62, 48.80, 50.85,
    51.90, 52.22, 53.65, 55.35, 58.14, 59.70, 61.30, 63.20,
    64.80, 65.20, 67.21, 68.14, 70.90, 71.58, 72.86, 74.20,
    74.50, 75.50, 76.80, 80.40, 85.00, 90.38, 96.50, 99.19,
    102.40, 104.50, 105.40, 107.50, 110.90, 111.60, 112.40, 116.00,
]
YS = [
    6.40, 7.27, 8.00, 8.40, 10.80, 11.20, 12.40, 13.30, 14.40,
    16.30, 16.87, 18.00, 19.80, 21.13, 21.90, 22.40, 23.13,
    26.20, 28.00, 29.60, 32.00, 33.40, 34.20, 35.20, 36.00,
    37.13, 40.50, 40.80, 42.00, 42.40, 43.80, 45.50, 48.80,
    50.20, 54.40, 55.20, 56.40, 56.90, 57.80, 59.15, 65.20,
    66.40, 67.40, 73.40, 76.00, 77.70, 78.70, 79.00,
]


def snap_path(label):
    return os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")


def dump_vios():
    """Print first few DRC copper/hole hits so the next jog can miss them."""
    try:
        data = json.load(open(DRC_JSON))
    except OSError:
        return
    shown = 0
    for v in data.get("violations", []):
        if v.get("type") not in ABORT:
            continue
        items = v.get("items") or []
        desc = " | ".join((i.get("description") or "")[:90] for i in items[:2])
        print(f"    vio {v.get('type')}: {desc}", flush=True)
        shown += 1
        if shown >= 8:
            break


def waypoint_route(r, x1, y1, x2, y2, layer, w, name, xs=None, ys=None):
    xs = list(xs or XS)
    ys = list(ys or YS)
    nodes = {(round(x1, 3), round(y1, 3)), (round(x2, 3), round(y2, 3))}
    for x in xs:
        nodes.add((round(x, 3), round(y1, 3)))
        nodes.add((round(x, 3), round(y2, 3)))
        for y in ys:
            nodes.add((round(x, 3), round(y, 3)))
    for y in ys:
        nodes.add((round(x1, 3), round(y, 3)))
        nodes.add((round(x2, 3), round(y, 3)))
    nodes = list(nodes)
    idx = {p: i for i, p in enumerate(nodes)}
    start = idx[(round(x1, 3), round(y1, 3))]
    goal = idx[(round(x2, 3), round(y2, 3))]
    byx, byy = {}, {}
    for i, (x, y) in enumerate(nodes):
        byx.setdefault(x, []).append(i)
        byy.setdefault(y, []).append(i)
    for v in byx.values():
        v.sort(key=lambda i: nodes[i][1])
    for v in byy.values():
        v.sort(key=lambda i: nodes[i][0])

    def neighbors(i):
        x, y = nodes[i]
        out = []
        col = byx.get(x, [])
        k = col.index(i)
        if k > 0:
            out.append(col[k - 1])
        if k + 1 < len(col):
            out.append(col[k + 1])
        row = byy.get(y, [])
        k = row.index(i)
        if k > 0:
            out.append(row[k - 1])
        if k + 1 < len(row):
            out.append(row[k + 1])
        return out

    cache = {}

    def edge_ok(a, b):
        key = (a, b) if a < b else (b, a)
        if key in cache:
            return cache[key]
        xa, ya = nodes[a]
        xb, yb = nodes[b]
        ok = r.track_clear(xa, ya, xb, yb, layer, w, name)
        cache[key] = ok
        return ok

    h = lambda i: abs(nodes[i][0] - nodes[goal][0]) + abs(nodes[i][1] - nodes[goal][1])
    pq = [(h(start), 0.0, start)]
    came = {}
    cost = {start: 0.0}
    steps = 0
    found = False
    while pq and steps < 50000:
        _, gcost, cur = heapq.heappop(pq)
        steps += 1
        if cur == goal:
            found = True
            break
        if gcost != cost.get(cur):
            continue
        for nxt in neighbors(cur):
            if not edge_ok(cur, nxt):
                continue
            d = hypot(nodes[cur][0], nodes[cur][1], nodes[nxt][0], nodes[nxt][1])
            ng = gcost + d
            if ng < cost.get(nxt, 1e9):
                cost[nxt] = ng
                came[nxt] = cur
                heapq.heappush(pq, (ng + h(nxt), ng, nxt))
    if not found:
        return None, 1e9
    path = [goal]
    while path[-1] != start:
        path.append(came[path[-1]])
    path.reverse()
    return [nodes[i] for i in path], cost[goal]


def check(board, r, label, last_good, unconn_ceiling):
    """Refill zones when new copper was added (pours must clear the new tracks)."""
    if r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or n > unconn_ceiling:
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{unconn_ceiling}"
        print(f"ABORT {reason}; restoring {last_good}")
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, snap_path(label))
    return pairs, n, counts, pairs


def reload():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def try_commit(r, pts, layer, w, name, label):
    ok = r.commit(pts, layer, w, r.code_of(name), name)
    if ok:
        print(f"  OK {label}")
        return True
    print(f"  FAIL {label}: {why(r, pts, layer, w, name)}")
    return False


def try_any(r, name, layer, w, cands):
    for pts, label in cands:
        if try_commit(r, pts, layer, w, name, label):
            return True
    return False


def try_wp(r, name, layer, w, x1, y1, x2, y2, label, max_l=90):
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name)
    if pts is None:
        print(f"  FAIL waypoint {label}: no path")
        return False
    if L > max_l:
        print(f"  skip long waypoint {label} L={L:.1f}")
        return False
    return try_commit(r, pts, layer, w, name, f"waypoint {label} L={L:.1f}")


def apply_net(board, r, name, fn, last, ceiling):
    """Run fn(r); DRC; keep only if shorts=0 and unconn did not rise."""
    r.ok = 0
    r.fail = 0
    fn(r)
    r.collect()
    got = check(r.board, r, f"pass14-{name.replace('.', '')}", last, ceiling)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    pairs, n, counts, _ = got
    last = snap_path(f"pass14-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n


# --- per-net routers -------------------------------------------------------

def route_vdd2_mid(r):
    print("== VDD2_MID around VIN x=62 / VDD1 via (49.44,16.87) ==", flush=True)
    # F.Cu pad-level first (FB2.2 y=18 to FB3), jog around VIN.
    fb2, fb3 = r.pad("FB2", "2"), r.pad("FB3", "1")
    if fb2 and fb3:
        if try_any(
            r,
            "VDD2_MID",
            pcbnew.F_Cu,
            0.25,
            [
                (
                    [
                        (fb2["x"], fb2["y"]),
                        (fb2["x"], 17.20),
                        (fb3["x"], 17.20),
                        (fb3["x"], fb3["y"]),
                    ],
                    "F y17.20 south of VIN",
                ),
                (
                    [
                        (fb2["x"], fb2["y"]),
                        (fb2["x"], 19.20),
                        (fb3["x"], 19.20),
                        (fb3["x"], fb3["y"]),
                    ],
                    "F y19.20 north of VIN",
                ),
                (
                    [
                        (fb2["x"], fb2["y"]),
                        (fb2["x"], 16.40),
                        (fb3["x"], 16.40),
                        (fb3["x"], fb3["y"]),
                    ],
                    "F y16.40",
                ),
            ],
        ):
            return
    if try_any(
        r,
        "VDD2_MID",
        pcbnew.B_Cu,
        0.25,
        [
            ([(58.14, 16.87), (67.21, 16.87), (67.21, 16.30)], "B direct y16.87"),
            ([(58.14, 16.87), (58.14, 16.30), (67.21, 16.30)], "B via y"),
            ([(58.14, 16.87), (58.14, 17.80), (67.21, 17.80), (67.21, 16.30)], "B y17.80"),
        ],
    ):
        return
    try_wp(r, "VDD2_MID", pcbnew.F_Cu, 0.25, 58.79, 18.00, 67.21, 18.00, "F FB2-FB3", max_l=20)
    try_wp(r, "VDD2_MID", pcbnew.B_Cu, 0.25, 58.14, 16.87, 67.21, 16.30, "B vias", max_l=20)


def route_vdd2_c8_c9(r):
    print("== VDD2 C8 to C9 (VIN_FILT y=28.80 / VDD1 y=33) ==", flush=True)
    # F.Cu: C8 island (53.52,32) to C9 (53.68,36). Jog around VDD1 y=33.
    if try_any(
        r,
        "VDD2",
        pcbnew.F_Cu,
        0.25,
        [
            (
                [
                    (53.52, 32.00),
                    (50.80, 32.00),
                    (50.80, 36.00),
                    (53.68, 36.00),
                ],
                "F west of VDD1 y=33",
            ),
            (
                [
                    (53.52, 32.00),
                    (53.52, 28.10),
                    (59.70, 28.10),
                    (59.70, 37.13),
                    (59.05, 37.13),
                    (59.05, 36.00),
                ],
                "F south of VIN_FILT then C9 via",
            ),
            (
                [
                    (53.52, 32.00),
                    (53.52, 29.50),
                    (50.80, 29.50),
                    (50.80, 37.30),
                    (59.05, 37.30),
                ],
                "F y29.5 then west of VIN_FILT",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.25,
        [
            ([(52.22, 32.00), (59.70, 32.00), (59.70, 37.13)], "B H then N"),
            ([(52.22, 32.00), (52.22, 37.13), (59.70, 37.13)], "B N then H"),
            ([(52.22, 32.00), (52.22, 34.20), (59.70, 34.20), (59.70, 37.13)], "B y34.2"),
            ([(52.22, 32.00), (52.22, 30.50), (59.70, 30.50), (59.70, 37.13)], "B y30.5"),
        ],
    ):
        return
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 52.22, 32.00, 59.70, 37.13, "B C8-C9 vias", max_l=25)
    try_wp(r, "VDD2", pcbnew.F_Cu, 0.25, 53.52, 32.00, 53.68, 36.00, "F C8-C9", max_l=20)


def route_vdd2_c9_tp12(r):
    print("== VDD2 C9 to TP12 (ENABLE y=40.95) ==", flush=True)
    if try_any(
        r,
        "VDD2",
        pcbnew.F_Cu,
        0.25,
        [
            (
                [
                    (59.05, 37.30),
                    (59.05, 40.25),
                    (60.00, 40.25),
                    (60.00, 42.00),
                ],
                "F south of ENABLE",
            ),
            (
                [
                    (59.05, 37.30),
                    (59.05, 41.70),
                    (60.00, 41.70),
                    (60.00, 42.00),
                ],
                "F north of ENABLE",
            ),
            (
                [
                    (59.05, 37.30),
                    (51.20, 37.30),
                    (51.20, 42.00),
                    (60.00, 42.00),
                ],
                "F west of ENABLE H",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.25,
        [
            ([(59.70, 37.13), (61.30, 37.13), (61.30, 42.00)], "B east then N"),
            ([(59.70, 37.13), (61.30, 37.13), (61.30, 40.50), (61.30, 42.00)], "B via y40.5"),
            ([(59.70, 37.13), (59.70, 42.00), (61.30, 42.00)], "B N then E"),
        ],
    ):
        return
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 59.70, 37.13, 61.30, 42.00, "B C9-TP12", max_l=15)


def route_vdd2_fb3(r):
    print("== VDD2 FB3 island (around P0.15 y=20.60) ==", flush=True)
    try_any(
        r,
        "VDD2",
        pcbnew.F_Cu,
        0.25,
        [
            (
                [
                    (68.79, 19.13),
                    (69.80, 19.13),
                    (69.80, 21.40),
                    (61.30, 21.40),
                    (61.30, 32.00),
                    (59.05, 32.00),
                    (59.05, 36.00),
                ],
                "F north of P0.15 then west",
            ),
        ],
    )
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.25,
        [
            ([(68.14, 16.87), (61.30, 16.87), (61.30, 42.00)], "B west under P0.15 to TP12"),
            ([(68.14, 16.87), (68.14, 19.80), (61.30, 19.80), (61.30, 42.00)], "B y19.8 to TP12"),
            ([(68.14, 16.87), (52.22, 16.87), (52.22, 32.00)], "B west to C8 via"),
        ],
    ):
        return
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 68.14, 16.87, 61.30, 42.00, "B FB3-TP12", max_l=40)
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 68.14, 16.87, 52.22, 32.00, "B FB3-C8", max_l=40)


def route_nreset_c39_j8(r):
    print("== nRESET C39 to J8 via (F.Cu jog) ==", flush=True)
    if try_any(
        r,
        "nRESET",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (45.68, 16.00),
                    (45.68, 14.40),
                    (46.50, 14.40),
                    (46.50, 11.20),
                    (52.22, 11.20),
                    (52.22, 10.80),
                    (53.65, 10.80),
                    (53.65, 7.27),
                ],
                "C39 west/north of F1 to J8 via",
            ),
            (
                [
                    (45.68, 16.00),
                    (44.40, 16.00),
                    (44.40, 11.20),
                    (53.65, 11.20),
                    (53.65, 7.27),
                ],
                "west then y11.2",
            ),
            (
                [
                    (45.68, 16.00),
                    (45.68, 14.40),
                    (51.90, 14.40),
                    (51.90, 8.40),
                    (53.65, 8.40),
                    (53.65, 7.27),
                ],
                "east of C39 at y14.4",
            ),
        ],
    ):
        return
    try_wp(r, "nRESET", pcbnew.F_Cu, 0.18, 45.68, 16.00, 53.65, 7.27, "F C39-J8", max_l=25)
    try_wp(r, "nRESET", pcbnew.B_Cu, 0.18, 45.68, 16.00, 53.65, 7.27, "B C39-J8", max_l=25)


def route_nreset_u1_c39(r):
    print("== nRESET U1 via to C39 ==", flush=True)
    if try_any(
        r,
        "nRESET",
        pcbnew.F_Cu,
        0.18,
        [
            ([(38.25, 21.80), (37.20, 21.80), (37.20, 16.00), (45.68, 16.00)], "west of nRF via"),
            ([(38.25, 21.80), (38.25, 14.80), (44.80, 14.80), (44.80, 16.00), (45.68, 16.00)], "y14.8"),
            ([(38.25, 21.80), (40.50, 21.80), (40.50, 16.00), (45.68, 16.00)], "east of SWDIO"),
        ],
    ):
        return
    try_any(
        r,
        "nRESET",
        pcbnew.B_Cu,
        0.18,
        [
            ([(38.25, 21.80), (38.25, 16.00), (45.68, 16.00)], "B at y16"),
            ([(38.25, 21.80), (45.68, 21.80), (45.68, 16.00)], "B H then N"),
        ],
    )
    try_wp(r, "nRESET", pcbnew.F_Cu, 0.18, 38.25, 21.80, 45.68, 16.00, "F U1-C39", max_l=20)
    try_wp(r, "nRESET", pcbnew.B_Cu, 0.18, 38.25, 21.80, 45.68, 16.00, "B U1-C39", max_l=20)


def route_nreset_j8_r5(r):
    print("== nRESET J8 via to R5 B.Cu column ==", flush=True)
    if try_any(
        r,
        "nRESET",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (53.65, 7.27),
                    (53.65, 6.40),
                    (110.90, 6.40),
                    (110.90, 36.00),
                    (103.30, 36.00),
                ],
                "north y6.4 then east 110.9",
            ),
            (
                [
                    (53.65, 7.27),
                    (53.65, 5.40),
                    (112.40, 5.40),
                    (112.40, 36.00),
                    (102.00, 36.00),
                ],
                "y5.4 east 112.4",
            ),
        ],
    ):
        return
    try_wp(r, "nRESET", pcbnew.B_Cu, 0.18, 53.65, 7.27, 102.00, 36.00, "B J8-R5", max_l=80)


def route_sim_clk(r):
    print("== SIM_CLK TP3 / C35 / U4 ==", flush=True)
    try_any(
        r,
        "SIM_CLK",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (72.00, 36.00),
                    (71.20, 36.00),
                    (71.20, 44.00),
                    (71.68, 44.00),
                ],
                "F TP3-C35 x71.2",
            ),
            (
                [
                    (72.00, 36.00),
                    (73.50, 36.00),
                    (73.50, 44.00),
                    (71.68, 44.00),
                ],
                "F TP3-C35 east of ENABLE",
            ),
        ],
    )
    try_any(
        r,
        "SIM_CLK",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (71.68, 44.00),
                    (71.68, 50.80),
                    (77.75, 50.80),
                    (77.75, 56.60),
                ],
                "F C35-U4 y50.8",
            ),
            (
                [
                    (71.68, 44.00),
                    (74.50, 44.00),
                    (74.50, 56.60),
                    (77.75, 56.60),
                ],
                "F C35-U4 x74.5",
            ),
        ],
    )
    if try_any(
        r,
        "SIM_CLK",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (73.30, 36.00),
                    (73.30, 42.40),
                    (70.90, 42.40),
                    (70.90, 45.50),
                    (68.14, 45.50),
                    (68.14, 54.40),
                    (71.58, 54.40),
                    (71.58, 57.73),
                    (75.50, 57.73),
                    (75.50, 59.15),
                    (78.40, 59.15),
                    (78.40, 57.73),
                ],
                "B west of U2 then south of U4",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK", pcbnew.F_Cu, 0.18, 72.00, 36.00, 71.68, 44.00, "F TP3-C35", max_l=20)
    try_wp(r, "SIM_CLK", pcbnew.F_Cu, 0.18, 71.68, 44.00, 77.75, 56.60, "F C35-U4", max_l=25)
    try_wp(r, "SIM_CLK", pcbnew.B_Cu, 0.18, 73.30, 36.00, 78.40, 57.73, "B TP3-U4", max_l=45)


def route_sim_clk_c(r):
    print("== SIM_CLK_C U4 via to J7 via (B.Cu) ==", flush=True)
    if try_any(
        r,
        "SIM_CLK_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (76.62, 56.05),
                    (76.62, 56.90),
                    (75.50, 56.90),
                    (75.50, 59.15),
                    (80.40, 59.15),
                    (80.40, 54.40),
                    (85.00, 54.40),
                    (85.00, 46.67),
                    (99.19, 46.67),
                ],
                "south of U4 then east",
            ),
            (
                [
                    (76.62, 56.05),
                    (80.40, 56.05),
                    (80.40, 46.67),
                    (99.19, 46.67),
                ],
                "east of U4 then J7",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK_C", pcbnew.B_Cu, 0.18, 76.62, 56.05, 99.19, 46.67, "B U4-J7", max_l=45)
    try_wp(r, "SIM_CLK_C", pcbnew.F_Cu, 0.18, 77.75, 55.40, 98.54, 45.54, "F U4-J7", max_l=45)


def route_sim_io_c(r):
    print("== SIM_IO_C U4 to J7 via ==", flush=True)
    if try_any(
        r,
        "SIM_IO_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (77.35, 55.40),
                    (77.35, 59.15),
                    (80.40, 59.15),
                    (80.40, 54.40),
                    (85.00, 54.40),
                    (85.00, 50.01),
                    (98.54, 50.01),
                ],
                "south of U4 then east",
            ),
            (
                [
                    (77.35, 55.40),
                    (80.40, 55.40),
                    (80.40, 50.01),
                    (98.54, 50.01),
                ],
                "east of U4 then J7",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_IO_C", pcbnew.B_Cu, 0.18, 77.35, 55.40, 98.54, 50.01, "B U4-J7", max_l=45)
    try_wp(r, "SIM_IO_C", pcbnew.F_Cu, 0.18, 77.35, 55.40, 98.54, 48.71, "F U4-J7", max_l=45)


def route_enable_sw1(r):
    print("== ENABLE U2 to SW1 (via south of U2, short B.Cu) ==", flush=True)
    w = 0.18
    sites = [(74.20, 42.40), (72.86, 42.40), (73.50, 42.40), (74.80, 41.70)]
    for vx, vy in sites:
        whyv = r.via_why(vx, vy, "ENABLE", pwr=False)
        if whyv is not None:
            print(f"  via ({vx:.2f},{vy:.2f}) blocked {whyv}")
            continue
        fpts = [(72.86, 40.95), (72.86, vy), (vx, vy)] if abs(vx - 72.86) > 0.05 else [(72.86, 40.95), (vx, vy)]
        bpts = [
            (vx, vy),
            (75.50, vy),
            (75.50, 36.00),
            (76.80, 36.00),
            (76.80, 28.00),
            (90.38, 28.00),
            (90.38, 26.20),
        ]
        if not r.path_clear(fpts, pcbnew.F_Cu, w, "ENABLE"):
            print(f"  F to via ({vx:.2f},{vy:.2f}): {why(r, fpts, pcbnew.F_Cu, w, 'ENABLE')}")
            continue
        if not r.path_clear(bpts, pcbnew.B_Cu, w, "ENABLE"):
            print(f"  B to SW1 ({vx:.2f},{vy:.2f}): {why(r, bpts, pcbnew.B_Cu, w, 'ENABLE')}")
            continue
        r.add_via(vx, vy, r.code_of("ENABLE"), "ENABLE", pwr=False)
        r.commit(fpts, pcbnew.F_Cu, w, r.code_of("ENABLE"), "ENABLE")
        r.commit(bpts, pcbnew.B_Cu, w, r.code_of("ENABLE"), "ENABLE")
        print(f"  OK ENABLE U2 via ({vx:.2f},{vy:.2f}) to SW1")
        return
    v = r.nearest_via("ENABLE", 72.86, 40.95, limit=6)
    if v:
        try_wp(r, "ENABLE", pcbnew.B_Cu, w, v["x"], v["y"], 90.38, 26.20, "B existing via-SW1", max_l=40)
    try_wp(r, "ENABLE", pcbnew.F_Cu, w, 72.86, 40.95, 90.38, 26.20, "F U2-SW1", max_l=40)


def route_enable_c14_u1(r):
    print("== ENABLE C14/R1 island to U1/TP17 ==", flush=True)
    # Local F.Cu C14-R1 if B.Cu stitch is not enough for DRC.
    c14, r1 = r.pad("C14", "1"), r.pad("R1", "2")
    if c14 and r1:
        try_any(
            r,
            "ENABLE",
            pcbnew.F_Cu,
            0.18,
            [
                (
                    [
                        (c14["x"], c14["y"]),
                        (c14["x"], c14["y"] - 0.70),
                        (r1["x"], c14["y"] - 0.70),
                        (r1["x"], r1["y"]),
                    ],
                    "C14-R1 y-0.7",
                ),
                (
                    [
                        (c14["x"], c14["y"]),
                        (c14["x"] + 0.90, c14["y"]),
                        (c14["x"] + 0.90, r1["y"]),
                        (r1["x"], r1["y"]),
                    ],
                    "C14-R1 x+0.9",
                ),
            ],
        )
    vx, vy = 52.00, 45.50
    if r.via_why(vx, vy, "ENABLE", pwr=False) is None:
        fpts = [(52.00, 44.00), (vx, vy)]
        bpts = [
            (50.85, 23.15),
            (50.85, 24.05),
            (104.50, 24.05),
            (107.80, 24.05),
            (107.80, 45.50),
            (vx, vy),
        ]
        if r.path_clear(fpts, pcbnew.F_Cu, 0.18, "ENABLE") and r.path_clear(
            bpts, pcbnew.B_Cu, 0.18, "ENABLE"
        ):
            r.add_via(vx, vy, r.code_of("ENABLE"), "ENABLE", pwr=False)
            r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("ENABLE"), "ENABLE")
            r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("ENABLE"), "ENABLE")
            print("  OK ENABLE C14via east-of-COEX2 to TP17via")
            return
        print("  TP17 via wrap not clear; trying local B jogs (no board-width run)")
    if try_any(
        r,
        "ENABLE",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (48.33, 23.13),
                    (47.20, 23.13),
                    (47.20, 41.10),
                    (42.75, 41.10),
                ],
                "B west of C14 via to U1 ring",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 33.40),
                    (43.40, 33.40),
                    (43.40, 45.13),
                ],
                "B R1via y33.4 to U1via",
            ),
            (
                [
                    (48.33, 23.13),
                    (48.33, 34.20),
                    (42.75, 34.20),
                    (42.75, 41.10),
                ],
                "B C14via y34.2 to U1",
            ),
        ],
    ):
        return
    try_wp(r, "ENABLE", pcbnew.B_Cu, 0.18, 48.33, 23.13, 42.75, 41.10, "B C14-U1", max_l=35)
    try_wp(r, "ENABLE", pcbnew.F_Cu, 0.18, 48.33, 23.13, 42.75, 44.00, "F C14-U1", max_l=35)


def route_dec0(r):
    print("== DEC0 C13 to via (around ENABLE via / C13 GND) ==", flush=True)
    vx, vy = 47.40, 29.60
    fpts = [(48.72, 29.60), (vx, vy)]
    bpts = [
        (vx, vy),
        (vx, 32.80),
        (44.80, 32.80),
        (44.80, 21.13),
        (48.65, 21.13),
    ]
    if r.via_why(vx, vy, "DEC0", pwr=False) is None and r.path_clear(
        fpts, pcbnew.F_Cu, 0.18, "DEC0"
    ):
        if r.path_clear(bpts, pcbnew.B_Cu, 0.18, "DEC0"):
            r.add_via(vx, vy, r.code_of("DEC0"), "DEC0", pwr=False)
            r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("DEC0"), "DEC0")
            r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("DEC0"), "DEC0")
            print("  OK DEC0 via+B hop")
            return
        print(f"  DEC0 B blocked: {why(r, bpts, pcbnew.B_Cu, 0.18, 'DEC0')}")
    try_any(
        r,
        "DEC0",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (48.72, 31.00),
                    (47.20, 31.00),
                    (47.20, 24.80),
                    (47.20, 21.13),
                    (48.65, 21.13),
                ],
                "west of ENABLE via from y31",
            ),
            (
                [
                    (48.72, 31.00),
                    (50.00, 31.00),
                    (50.00, 24.80),
                    (50.00, 21.13),
                    (48.65, 21.13),
                ],
                "east alley y31",
            ),
            (
                [
                    (48.72, 29.60),
                    (50.20, 29.60),
                    (50.20, 21.13),
                    (48.65, 21.13),
                ],
                "F east of ENABLE via at C13 y",
            ),
            (
                [
                    (48.72, 29.60),
                    (46.80, 29.60),
                    (46.80, 21.13),
                    (48.65, 21.13),
                ],
                "F west of ENABLE via at C13 y",
            ),
        ],
    )
    try_wp(r, "DEC0", pcbnew.F_Cu, 0.18, 48.72, 31.00, 48.65, 21.13, "F C13-via", max_l=20)
    try_wp(r, "DEC0", pcbnew.B_Cu, 0.18, 48.72, 29.60, 48.65, 21.13, "B C13-via", max_l=20)


def route_vin_filt(r):
    print("== VIN_FILT JP1 via to island (around VIN H y=15.40) ==", flush=True)
    try_any(
        r,
        "VIN_FILT",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (56.80, 13.30),
                    (56.80, 6.20),
                    (64.50, 6.20),
                    (64.50, 5.40),
                    (72.20, 5.40),
                    (72.20, 22.40),
                    (51.90, 22.40),
                    (51.90, 21.90),
                ],
                "north of VDD_GPIO then east",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 11.00),
                    (46.20, 11.00),
                    (46.20, 22.40),
                    (51.90, 22.40),
                    (51.90, 21.90),
                ],
                "west of VIN_F via",
            ),
        ],
    )
    try_any(
        r,
        "VIN_FILT",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (64.00, 13.30),
                    (64.00, 23.50),
                    (53.70, 23.50),
                    (53.70, 22.40),
                ],
                "F east of VIN H",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 14.80),
                    (47.20, 14.80),
                    (47.20, 21.90),
                    (51.90, 21.90),
                ],
                "F west of VIN H then island",
            ),
            (
                [
                    (55.35, 13.30),
                    (48.80, 13.30),
                    (48.80, 21.90),
                    (51.90, 21.90),
                ],
                "F west at y13.3 around VIN H",
            ),
        ],
    )
    try_wp(r, "VIN_FILT", pcbnew.F_Cu, 0.25, 55.35, 13.30, 51.90, 21.90, "F JP1-island", max_l=25)
    try_wp(r, "VIN_FILT", pcbnew.B_Cu, 0.18, 55.35, 13.30, 51.90, 21.90, "B JP1-island", max_l=30)


def route_vin_f(r):
    print("== VIN_F F1 via to FB4 via (short hop only; no board-width bus) ==", flush=True)
    cands = [
        (
            [
                (49.30, 12.60),
                (50.80, 12.60),
                (50.80, 11.00),
                (64.50, 11.00),
                (64.50, 17.66),
                (71.58, 17.66),
            ],
            pcbnew.F_Cu,
            "F y11 x64.5",
        ),
        (
            [
                (49.30, 12.60),
                (50.80, 12.60),
                (50.80, 11.00),
                (64.50, 11.00),
                (64.50, 17.66),
                (71.58, 17.66),
            ],
            pcbnew.B_Cu,
            "B y11 x64.5",
        ),
        (
            [
                (49.30, 12.60),
                (49.30, 11.00),
                (76.80, 11.00),
                (76.80, 17.66),
                (71.58, 17.66),
            ],
            pcbnew.F_Cu,
            "F y11 x76.8",
        ),
    ]
    for pts, ly, lab in cands:
        L = sum(hypot(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:]))
        if L > 45:
            print(f"  skip long {lab} L={L:.1f}")
            continue
        try_commit(r, pts, ly, 0.18, "VIN_F", lab)
    try_wp(r, "VIN_F", pcbnew.F_Cu, 0.18, 49.30, 12.60, 71.58, 17.66, "F F1-FB4", max_l=40)
    try_wp(r, "VIN_F", pcbnew.B_Cu, 0.18, 49.30, 12.60, 71.58, 17.66, "B F1-FB4", max_l=40)


def route_p008(r):
    print("== P0.08 U1 via to SW3 via (F-class island) ==", flush=True)
    if try_any(
        r,
        "P0.08",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (50.85, 30.00),
                    (50.85, 34.20),
                    (53.65, 34.20),
                    (53.65, 26.00),
                    (79.68, 26.00),
                ],
                "jog around TP11 then y26",
            ),
            (
                [
                    (46.20, 30.00),
                    (46.20, 26.00),
                    (79.68, 26.00),
                ],
                "B y26 direct",
            ),
            (
                [
                    (46.20, 30.00),
                    (51.90, 30.00),
                    (51.90, 24.80),
                    (79.68, 24.80),
                    (79.68, 26.00),
                ],
                "B y24.8 south of VDD1 via",
            ),
        ],
    ):
        return
    try_wp(r, "P0.08", pcbnew.B_Cu, 0.18, 46.20, 30.00, 79.68, 26.00, "B U1-SW3", max_l=50)
    try_wp(r, "P0.08", pcbnew.F_Cu, 0.18, 44.00, 30.00, 78.38, 24.00, "F U1-SW3", max_l=50)


def route_p006(r):
    print("== P0.06 headers: north of SIM_RST then east 110.9 / west wrap y>=64 ==", flush=True)
    # SIM_RST wall at x≈78 y=36–56.6. Escape north of y=36 then east of P0.15.
    j12 = [
        (
            [
                (48.62, 36.00),
                (48.62, 34.20),
                (110.90, 34.20),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "north of SIM_RST y34.2 east 110.9 stub",
        ),
        (
            [
                (48.62, 36.00),
                (48.62, 33.40),
                (111.60, 33.40),
                (111.60, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y33.4 east 111.6 stub",
        ),
        (
            [
                (48.62, 36.00),
                (48.62, 32.00),
                (112.40, 32.00),
                (112.40, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y32 east 112.4 stub",
        ),
        (
            [
                (48.62, 36.00),
                (48.62, 28.00),
                (110.90, 28.00),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y28 east 110.9 stub",
        ),
        (
            [
                (48.62, 36.00),
                (48.62, 22.40),
                (110.90, 22.40),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "between P0.15 H and COEX2 H then east",
        ),
        (
            [
                (48.62, 36.00),
                (48.62, 34.20),
                (110.90, 34.20),
                (110.90, 66.40),
                (25.10, 66.40),
                (25.10, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "east of COEX0 H then west wrap x=25.1 y=66.4",
        ),
        (
            [
                (48.80, 40.80),
                (48.80, 34.20),
                (110.90, 34.20),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "from y40.8 island north then east",
        ),
    ]
    if not try_any(r, "P0.06", pcbnew.B_Cu, 0.18, j12):
        if not try_wp(r, "P0.06", pcbnew.B_Cu, 0.18, 48.62, 36.00, 21.24, 76.00, "B island-J12", max_l=220):
            if not try_wp(r, "P0.06", pcbnew.B_Cu, 0.18, 45.15, 36.00, 21.24, 76.00, "B via-J12", max_l=220):
                print("  J12.7 not closed")
                return
    # J9.1 duplicate: branch from J12 copper / stub, not a second U1 escape.
    j9 = [
        (
            [
                (21.24, 76.00),
                (21.24, 78.70),
                (110.90, 78.70),
                (110.90, 8.00),
                (116.00, 8.00),
            ],
            "J12 stub column 110.9 to J9",
        ),
        (
            [
                (21.24, 78.70),
                (112.40, 78.70),
                (112.40, 8.00),
                (116.00, 8.00),
            ],
            "stub x112.4 to J9",
        ),
        (
            [
                (110.90, 34.20),
                (110.90, 8.00),
                (116.00, 8.00),
            ],
            "existing east column north to J9",
        ),
    ]
    if not try_any(r, "P0.06", pcbnew.B_Cu, 0.18, j9):
        if not try_wp(r, "P0.06", pcbnew.B_Cu, 0.18, 21.24, 76.00, 116.00, 8.00, "B J12-J9", max_l=220):
            print("  J9.1 not closed (J12 may still be open)")


def class_counts(pairs):
    c = Counter(p["cls"] for p in pairs)
    return c


def write_unconnected_csv(pairs, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["net", "class", "dist_mm", "ax", "ay", "a", "bx", "by", "b"])
        for p in sorted(pairs, key=lambda x: (x["cls"], x["net"], hypot(x["ax"], x["ay"], x["bx"], x["by"]))):
            d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
            w.writerow(
                [
                    p["net"],
                    p["cls"],
                    f"{d:.3f}",
                    f"{p['ax']:.4f}",
                    f"{p['ay']:.4f}",
                    p["a"],
                    f"{p['bx']:.4f}",
                    f"{p['by']:.4f}",
                    p["b"],
                ]
            )


def write_gpio_csv(board, pairs, path):
    by_net = defaultdict(list)
    for p in pairs:
        by_net[p["net"]].append(p)
    u1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
    u1_pads = {}
    for pad in u1.Pads():
        u1_pads[pad.GetNumber()] = (
            pad.GetNetname(),
            pcbnew.ToMM(pad.GetPosition().x),
            pcbnew.ToMM(pad.GetPosition().y),
        )
    vias = defaultdict(list)
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            vias[tr.GetNetname()].append(
                (pcbnew.ToMM(tr.GetPosition().x), pcbnew.ToMM(tr.GetPosition().y))
            )
    pth = defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                pth[pad.GetNetname()].append(
                    f"{fp.GetReference()}.{pad.GetNumber()}"
                    f"({pcbnew.ToMM(pad.GetPosition().x):.2f},{pcbnew.ToMM(pad.GetPosition().y):.2f})"
                )
    gpio_nets = sorted(
        n
        for n in {p[0] for p in u1_pads.values()}
        if n.startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or n in ("VDD_GPIO",)
    )
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["net", "u1_pads", "via_count", "nearest_via_mm", "headers", "unconnected_items", "status"]
        )
        for n in gpio_nets:
            pads = [f"{num}({xy[1]:.2f},{xy[2]:.2f})" for num, xy in u1_pads.items() if xy[0] == n]
            vs = vias.get(n, [])
            hdr = ";".join(pth.get(n, []))
            n_un = len(by_net.get(n, []))
            if pads:
                px, py = next(xy[1:] for xy in u1_pads.values() if xy[0] == n)
                nv = min(((v[0] - px) ** 2 + (v[1] - py) ** 2) ** 0.5 for v in vs) if vs else ""
            else:
                nv = ""
            w.writerow(
                [
                    n,
                    ";".join(pads),
                    len(vs),
                    f"{nv:.3f}" if nv != "" else "",
                    hdr,
                    n_un,
                    "OPEN" if n_un else "ROUTED",
                ]
            )


def write_release(n0, n1, shorts, counts, pairs, log, board):
    cls = class_counts(pairs)
    tracks = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    nvia = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
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
        f.write(f"| Vias | {nvia} |\n")
        f.write("| U1 | (36.0, 32.0) mm, rot 180° |\n")
        f.write("| SIM_DET U1 pad 45 net | `''` (must stay empty) |\n")
        f.write("| Backup | `.mcp-backups/final-fab-20260917-194911/` |\n")
        f.write("| Live snapshot after this pass | `after-pass14.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass13.kicad_pcb` |\n\n")
        f.write(f"## This pass (F-class islands + P0.06 headers)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was the start count. `complete_route.py` main() and `rebuild_bcu.py` ")
        f.write("were not run. Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("The 11 extra U1 vias pass13 deleted were not re-placed. ")
        f.write("P0.01 / P0.15 / COEX2 B.Cu were not ripped.\n\n")
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            f.write(f"| {name} | {status} — {note} |\n")
        f.write("\n## Remaining unconnected (by class)\n\n")
        f.write("| Class | Count | Meaning |\n|-------|-------|--------|\n")
        f.write(f"| A | {cls.get('A',0)} | U1/via to header or island |\n")
        f.write(f"| F | {cls.get('F',0)} | F.Cu power/SIM/SWD islands |\n")
        f.write(f"| G | {cls.get('G',0)} | Header duplicate branches |\n")
        f.write(f"| C | {cls.get('C',0)} | DNP RF shunts |\n")
        f.write(f"| E | {cls.get('E',0)} | GND F.Cu zone-to-zone |\n\n")
        f.write("## Reports\n\n")
        f.write("- `reports/UNCONNECTED_AFTER_FINAL.csv`\n")
        f.write("- `reports/GPIO_FINAL.csv`\n")
        f.write("- `reports/FINAL_FAB_RELEASE.md`\n")
        f.write("- `reports/DRC_AFTER_CONNECT.json`\n")
    print("wrote", path)


def main():
    start = snap_path("pass14-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} {dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        print("start already has shorts; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []

    steps = [
        ("VDD2_MID", route_vdd2_mid, "B.Cu FB2 via (58.14,16.87) to FB3 via (67.21,16.30); VIN x=62 is F.Cu"),
        ("VDD2_C8C9", route_vdd2_c8_c9, "B.Cu C8 via (52.22,32) to C9 via (59.70,37.13); jog not through VIN_FILT y=28.80 or VDD1 y=33"),
        ("VDD2_TP12", route_vdd2_c9_tp12, "B.Cu C9 via to TP12 via (61.30,42); around ENABLE y=40.95"),
        ("VDD2_FB3", route_vdd2_fb3, "FB3 (68.14,16.87) to C8/C9/TP12; P0.15 y=20.60 / VIN x=66"),
        ("nRESET_C39J8", route_nreset_c39_j8, "F.Cu C39 to J8 via (53.65,7.27)"),
        ("nRESET_U1C39", route_nreset_u1_c39, "U1 via (38.25,23.10) to C39"),
        ("nRESET_J8R5", route_nreset_j8_r5, "J8 via to R5 B.Cu column"),
        ("SIM_CLK", route_sim_clk, "TP3 via to U4 via"),
        ("SIM_CLK_C", route_sim_clk_c, "U4 via to J7 via"),
        ("SIM_IO_C", route_sim_io_c, "U4 to J7 via"),
        ("ENABLE_SW1", route_enable_sw1, "U2 pad to existing SW1 via; no 40 mm new run"),
        ("ENABLE_C14U1", route_enable_c14_u1, "C14/R1 island to U1/TP17"),
        ("DEC0", route_dec0, "C13 to DEC0 via (48.65,21.13); ENABLE via (48.33,23.13)"),
        ("VIN_FILT", route_vin_filt, "JP1 via (55.35,13.30) to island (51.90,21.90); VIN H y=15.40"),
        ("VIN_F", route_vin_f, "F1 via (49.30,12.60) to FB4 via; skip board-width B.Cu"),
        ("P0.08", route_p008, "U1 via (46.20,30) to SW3 via (79.68,26)"),
        ("P0.06", route_p006, "J12.7 west wrap / stub; J9.1 branch from J12"),
    ]

    for name, fn, note in steps:
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok, ceiling = apply_net(board, r, name, fn, last, ceiling)
        if not ok:
            status = "not closed (DRC revert or blocked)"
        elif ceiling < before:
            status = f"closed ({before}→{ceiling})"
        else:
            status = "not closed (no DRC-clean copper)"
        log.append((name, status, note))
        print(f"  kept={ok} ceiling={ceiling} {status}", flush=True)

    # Final snapshot
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass14"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board)
    print(
        f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} "
        f"classes={dict(class_counts(pairs))}"
    )
    for name, status, note in log:
        print(f"  {name}: {status} ({note[:80]})")
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= n0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
