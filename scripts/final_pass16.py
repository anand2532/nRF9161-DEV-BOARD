#!/usr/bin/env python3
"""Pass 16: add P0.15 replacement, then delete y=20.60 highway, then F-nets.

LIVE board only. Never restore backups, never re-place the 11 extra U1 vias,
never complete_route.main() / rebuild_bcu / autoroute. Add-then-delete on
P0.15 (and SIM_RST only if a replacement exists). Zone refill after every
copper change. Save only if shorts=0 and unconnected does not rise above 90.
"""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    ABORT,
    class_counts,
    dump_vios,
    reload,
    snap_path,
    try_any,
    try_commit,
    waypoint_route,
    write_gpio_csv,
    write_unconnected_csv,
)

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"

# Replacement: west via (41.75,23.10) to existing x=106 V, jogging VIN_FILT
# at y=19.80. Does not use the y=20.60 highway.
P015_REPL = [
    (41.75, 23.10),
    (41.75, 22.50),
    (46.50, 22.50),
    (46.50, 21.20),
    (47.80, 21.20),
    (47.80, 19.80),
    (51.50, 19.80),
    (51.50, 21.20),
    (54.80, 21.20),
    (54.80, 23.10),
    (106.00, 23.10),
    (106.00, 20.60),
]

# y=20.60 highway overlap with F-class corridor x≈48–72.
RIP_X0, RIP_X1 = 47.50, 72.50
RIP_Y = 20.60


def check(board, r, label, last_good, ceiling, force_fill=False):
    if force_fill or r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or n > ceiling:
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}")
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, snap_path(label))
    return pairs, n, counts, pairs


def apply_net(board, r, name, fn, last, ceiling):
    r.ok = 0
    r.fail = 0
    fn(r)
    r.collect()
    got = check(r.board, r, f"pass16-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    pairs, n, counts, _ = got
    last = snap_path(f"pass16-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n


def try_wp(r, name, layer, w, x1, y1, x2, y2, label, max_l=50):
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name)
    if pts is None:
        print(f"  FAIL waypoint {label}: no path")
        return False
    if L > max_l:
        print(f"  skip long waypoint {label} L={L:.1f}")
        return False
    return try_commit(r, pts, layer, w, name, f"waypoint {label} L={L:.1f}")


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return (
        pcbnew.ToMM(s.x),
        pcbnew.ToMM(s.y),
        pcbnew.ToMM(e.x),
        pcbnew.ToMM(e.y),
    )


def add_p015_replacement(r):
    print("== ADD P0.15 replacement (not y=20.60) via to x=106 ==", flush=True)
    if try_commit(r, P015_REPL, pcbnew.B_Cu, 0.18, "P0.15", "repl via-VIN_FILT-x106"):
        return True
    # Fallback: join x=106 at y=23.10 only (already on existing V).
    pts = P015_REPL[:-1]
    return try_commit(r, pts, pcbnew.B_Cu, 0.18, "P0.15", "repl to (106,23.10)")


def list_p015_highway(board):
    """B.Cu P0.15 segments on y=20.60 that overlap x=[RIP_X0, RIP_X1]."""
    hits = []
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(y1 - y2) > 0.25:
            continue
        if abs((y1 + y2) / 2 - RIP_Y) > 0.30:
            continue
        xa, xb = min(x1, x2), max(x1, x2)
        if xb < RIP_X0 or xa > RIP_X1:
            continue
        hits.append((tr, x1, y1, x2, y2))
    return hits


def delete_p015_corridor(board, r):
    """Remove y=20.60 copper across the F corridor. Keep west/east remnants."""
    hits = list_p015_highway(board)
    print(f"== DELETE P0.15 y=20.60 corridor hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2, tr.GetWidth()))
        board.Remove(tr)
    # Restore west/east remnants so x=106 and the west stub stay on the highway y.
    code = r.code_of("P0.15")
    west = [(41.75, RIP_Y), (RIP_X0, RIP_Y)]
    east = [(RIP_X1, RIP_Y), (106.00, RIP_Y)]
    for pts, lab in ((west, "west remnant"), (east, "east remnant")):
        if r.path_clear(pts, pcbnew.B_Cu, 0.18, "P0.15"):
            r.commit(pts, pcbnew.B_Cu, 0.18, code, "P0.15")
            print(f"  keep {lab} {pts}")
        else:
            print(f"  skip {lab}: {why(r, pts, pcbnew.B_Cu, 0.18, 'P0.15')}")
    r.collect()
    return specs


def restore_p015_segments(r, specs):
    code = r.code_of("P0.15")
    for x1, y1, x2, y2, width in specs:
        w = pcbnew.ToMM(width) if width > 100 else width
        r.add_track(x1, y1, x2, y2, pcbnew.B_Cu, w, code, "P0.15")
        print(f"  restored ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")


# --- F-net routers (after y=20.60 gap) ------------------------------------

def route_dec0(r):
    print("== DEC0 through P0.15 gap / around COEX2 ==", flush=True)
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    if try_any(
        r,
        "DEC0",
        B,
        0.18,
        [
            (
                [
                    (47.80, 31.20),
                    (47.80, 20.25),
                    (48.65, 20.25),
                    (48.65, 21.13),
                ],
                "B x47.8 through y20.25 gap",
            ),
            (
                [
                    (47.80, 31.20),
                    (51.40, 31.20),
                    (51.40, 20.25),
                    (48.65, 20.25),
                    (48.65, 21.13),
                ],
                "B x51.4 through gap",
            ),
            (
                [
                    (47.80, 31.20),
                    (36.50, 31.20),
                    (36.50, 27.20),
                    (36.50, 22.50),
                    (48.65, 22.50),
                    (48.65, 21.13),
                ],
                "B west of COEX2 V then gap",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "DEC0",
        F,
        0.18,
        [
            (
                [
                    (48.72, 31.00),
                    (48.72, 20.00),
                    (48.65, 20.00),
                ],
                "F direct C13-TP18",
            ),
            (
                [
                    (48.72, 31.00),
                    (52.80, 31.00),
                    (52.80, 20.00),
                    (48.65, 20.00),
                ],
                "F east of VDD1 V",
            ),
        ],
    ):
        return
    try_wp(r, "DEC0", B, 0.18, 47.80, 31.20, 48.65, 21.13, "B C13-via", max_l=40)


def route_enable(r):
    print("== ENABLE C14–U1 through gap / y-jog C14 GND ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    if try_any(
        r,
        "ENABLE",
        F,
        0.18,
        [
            (
                [
                    (47.68, 22.00),
                    (47.68, 21.30),
                    (50.00, 21.30),
                    (50.00, 21.68),
                ],
                "F C14-R1 y-0.70",
            ),
            (
                [
                    (47.68, 22.00),
                    (46.40, 22.00),
                    (46.40, 20.25),
                    (42.75, 20.25),
                    (42.75, 37.25),
                ],
                "F west then y20.25 to U1",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "ENABLE",
        B,
        0.18,
        [
            (
                [
                    (48.33, 23.13),
                    (48.33, 20.25),
                    (42.75, 20.25),
                    (42.75, 41.10),
                ],
                "B north through gap to U1 via",
            ),
            (
                [
                    (48.33, 23.13),
                    (36.50, 23.13),
                    (36.50, 27.20),
                    (36.50, 41.10),
                    (42.75, 41.10),
                ],
                "B west of COEX2 V to U1 via",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 20.25),
                    (74.20, 20.25),
                    (74.20, 42.40),
                ],
                "B C14 via east at y20.25 to U2 via",
            ),
        ],
    ):
        return
    try_wp(r, "ENABLE", B, 0.18, 48.33, 23.13, 42.75, 41.10, "B C14-U1", max_l=45)


def route_vdd2_fb3(r):
    print("== VDD2 FB3 through P0.15 gap to C8 ==", flush=True)
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    if try_any(
        r,
        "VDD2",
        B,
        0.18,
        [
            (
                [
                    (68.79, 19.13),
                    (68.79, 20.25),
                    (59.70, 20.25),
                    (59.70, 32.00),
                ],
                "B y20.25 then C9 via x=59.70",
            ),
            (
                [
                    (68.14, 16.87),
                    (68.14, 20.25),
                    (52.22, 20.25),
                    (52.22, 32.00),
                ],
                "B y20.25 to C8 via",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 20.25),
                    (36.50, 20.25),
                    (36.50, 27.20),
                    (52.22, 27.20),
                    (52.22, 32.00),
                ],
                "B west of COEX2 then C8",
            ),
            (
                [
                    (68.14, 16.87),
                    (40.80, 16.87),
                    (40.80, 20.25),
                    (44.72, 20.25),
                    (44.72, 25.90),
                ],
                "B west then gap to U1 VDD2 via",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VDD2",
        F,
        0.25,
        [
            (
                [
                    (68.40, 18.00),
                    (61.30, 18.00),
                    (61.30, 32.00),
                    (59.05, 32.00),
                ],
                "F west at y18 to TP12/C8",
            ),
        ],
    ):
        return
    try_wp(r, "VDD2", B, 0.18, 68.14, 16.87, 52.22, 32.00, "B FB3-C8", max_l=55)


def route_nreset_j8_r5(r):
    print("== nRESET J8–R5 through y=20.25 gap ==", flush=True)
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    if try_any(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [
                    (45.68, 19.80),
                    (47.20, 19.80),
                    (47.20, 20.25),
                    (69.50, 20.25),
                    (69.50, 18.40),
                    (73.50, 18.40),
                    (73.50, 20.25),
                    (97.50, 20.25),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B y20.25 jog VIN_F/VDD2",
            ),
            (
                [
                    (45.68, 19.80),
                    (47.20, 19.80),
                    (47.20, 20.30),
                    (97.50, 20.30),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B y20.30 direct-ish",
            ),
            (
                [
                    (45.68, 16.87),
                    (45.68, 20.25),
                    (102.33, 20.25),
                    (102.33, 27.13),
                ],
                "B from C39 V then y20.25",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "nRESET",
        F,
        0.18,
        [
            (
                [
                    (53.65, 7.27),
                    (58.50, 7.27),
                    (58.50, 4.40),
                    (80.80, 4.40),
                    (80.80, 23.80),
                    (102.33, 23.80),
                    (102.33, 27.13),
                ],
                "F y4.4 north of J1",
            ),
        ],
    ):
        return
    try_wp(r, "nRESET", B, 0.18, 45.68, 19.80, 102.33, 27.13, "B C39-R5", max_l=80)


def route_vin_filt(r):
    print("== VIN_FILT short hops ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    if try_any(
        r,
        "VIN_FILT",
        B,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (55.35, 20.25),
                    (51.90, 20.25),
                    (51.90, 21.90),
                ],
                "B south through P0.15 gap",
            ),
            (
                [
                    (55.35, 13.30),
                    (47.50, 13.30),
                    (47.50, 21.90),
                    (51.90, 21.90),
                ],
                "B west of VIN_F vias",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VIN_FILT",
        F,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (55.35, 9.20),
                    (58.80, 9.20),
                    (58.80, 8.20),
                    (67.50, 8.20),
                    (67.50, 16.50),
                    (74.00, 16.50),
                    (74.00, 16.94),
                ],
                "F north of D1 to FB4.2",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_FILT", B, 0.18, 55.35, 13.30, 51.90, 21.90, "B JP1-island", max_l=25)


def route_vin_f(r):
    print("== VIN_F short hops only ==", flush=True)
    if try_any(
        r,
        "VIN_F",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (49.30, 12.60),
                    (54.20, 12.60),
                    (54.20, 20.25),
                    (71.58, 20.25),
                    (71.58, 19.06),
                ],
                "B through P0.15 gap to FB4",
            ),
            (
                [
                    (49.30, 12.60),
                    (49.30, 20.25),
                    (71.20, 20.25),
                    (71.20, 19.80),
                ],
                "B y20.25 to VIN_F via",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_F", pcbnew.B_Cu, 0.18, 49.30, 12.60, 71.58, 17.66, "B F1-FB4", max_l=28)


def route_sim_clk_u1(r):
    print("== SIM_CLK U1 courtyard via east of RF ==", flush=True)
    B = pcbnew.B_Cu
    if try_any(
        r,
        "SIM_CLK",
        B,
        0.18,
        [
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 20.90),
                    (36.50, 20.90),
                    (36.50, 20.25),
                    (70.90, 20.25),
                    (70.90, 42.40),
                ],
                "B y20.25 then south to existing via",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 20.25),
                    (73.30, 20.25),
                    (73.30, 36.00),
                ],
                "B y20.25 to TP3 via",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK", B, 0.18, 31.25, 23.10, 73.30, 36.00, "B U1-TP3", max_l=70)


def route_sim_clk_c(r):
    print("== SIM_CLK_C (names distinct; around SIM_RST) ==", flush=True)
    B = pcbnew.B_Cu
    if try_any(
        r,
        "SIM_CLK_C",
        B,
        0.18,
        [
            (
                [
                    (76.62, 56.05),
                    (76.62, 58.40),
                    (66.50, 58.40),
                    (66.50, 41.50),
                    (99.19, 41.50),
                    (99.19, 46.67),
                ],
                "B north of SIM_CLK then west of SIM_RST",
            ),
            (
                [
                    (76.62, 56.05),
                    (80.80, 56.05),
                    (80.80, 46.67),
                    (99.19, 46.67),
                ],
                "B east of SIM_RST V",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "SIM_CLK_C",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (77.75, 55.40),
                    (77.75, 53.20),
                    (99.19, 53.20),
                    (99.19, 46.67),
                ],
                "F y53.2 to J7",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK_C", B, 0.18, 76.62, 56.05, 99.19, 46.67, "B U4-J7", max_l=50)


def route_sim_io_c(r):
    print("== SIM_IO_C (names distinct) ==", flush=True)
    if try_any(
        r,
        "SIM_IO_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (77.35, 55.40),
                    (76.20, 55.40),
                    (76.20, 58.40),
                    (66.50, 58.40),
                    (66.50, 41.50),
                    (98.54, 41.50),
                    (98.54, 50.01),
                ],
                "B north then west of SIM_RST",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "SIM_IO_C",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (77.35, 55.40),
                    (77.35, 53.20),
                    (98.54, 53.20),
                    (98.54, 50.01),
                ],
                "F y53.2 to J7 via",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_IO_C", pcbnew.B_Cu, 0.18, 77.35, 55.40, 98.54, 50.01, "B U4-J7", max_l=50)


def route_p008(r):
    print("== P0.08 after ENABLE/DEC0 space ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    if try_any(
        r,
        "P0.08",
        B,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (46.20, 20.25),
                    (79.67, 20.25),
                    (79.67, 26.00),
                ],
                "B north through gap then SW3",
            ),
            (
                [
                    (46.20, 30.00),
                    (54.80, 30.00),
                    (54.80, 20.25),
                    (79.67, 20.25),
                    (79.67, 26.00),
                ],
                "B east of VDD2 x=52.22 then gap",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "P0.08",
        F,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (54.80, 30.00),
                    (54.80, 26.00),
                    (79.67, 26.00),
                ],
                "F east of C13 then y26",
            ),
        ],
    ):
        return
    try_wp(r, "P0.08", B, 0.18, 46.20, 30.00, 79.67, 26.00, "B U1-SW3", max_l=55)


def sim_c_still_open(pairs):
    return any(p["net"] in ("SIM_CLK_C", "SIM_IO_C") for p in pairs)


def add_sim_rst_replacement(r):
    """Parallel SIM_RST east of x=78.25, then we may rip the vertical."""
    print("== ADD SIM_RST replacement east of x=78.25 ==", flush=True)
    return try_any(
        r,
        "SIM_RST",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (78.00, 36.00),
                    (80.80, 36.00),
                    (80.80, 56.60),
                    (78.25, 56.60),
                ],
                "B x80.8 parallel",
            ),
            (
                [
                    (78.00, 43.80),
                    (81.20, 43.80),
                    (81.20, 56.60),
                    (79.38, 56.60),
                    (79.38, 57.25),
                ],
                "B x81.2 to existing via",
            ),
            (
                [
                    (71.68, 43.80),
                    (71.68, 41.50),
                    (80.80, 41.50),
                    (80.80, 56.60),
                    (78.25, 56.60),
                ],
                "B south of H then x80.8",
            ),
        ],
    )


def delete_sim_rst_vertical(board, r):
    hits = []
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "SIM_RST" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(x1 - x2) > 0.25:
            continue
        if abs((x1 + x2) / 2 - 78.25) > 0.20:
            continue
        ya, yb = min(y1, y2), max(y1, y2)
        if yb < 43.5 or ya > 57.0:
            continue
        hits.append((tr, x1, y1, x2, y2, tr.GetWidth()))
        print(f"  rip SIM_RST ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        board.Remove(tr)
    r.collect()
    return hits


def leftover_f(pairs):
    want = {
        "nRESET",
        "DEC0",
        "ENABLE",
        "VDD2",
        "VIN_FILT",
        "VIN_F",
        "SIM_CLK",
        "SIM_CLK_C",
        "SIM_IO_C",
        "P0.08",
        "SWDCLK",
    }
    out = []
    for p in pairs:
        if p["net"] not in want:
            continue
        d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
        out.append(
            f"{p['net']} OPEN {d:.3f} mm ({p['ax']:.2f},{p['ay']:.2f})–({p['bx']:.2f},{p['by']:.2f})"
        )
    return out


def write_release(n0, n1, shorts, counts, pairs, log, board, p015_note, sim_note):
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
        f.write("| Live snapshot after this pass | `after-pass16.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass15.kicad_pcb` |\n\n")
        f.write("## This pass (P0.15 add-then-delete, then F-nets)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was the start count. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("The 11 extra U1 vias pass13 deleted were not re-placed. ")
        f.write("P0.06 / G7 / DNP C22–C24 skipped. SIM_*_C names not merged. GND: refill only.\n\n")
        f.write(f"**P0.15:** {p015_note}\n\n")
        f.write(f"**SIM_RST:** {sim_note}\n\n")
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
        left = leftover_f(pairs)
        if left:
            f.write("### Still-open F targets\n\n")
            for line in left:
                f.write(f"- {line}\n")
            f.write("\n")
        f.write("## Reports\n\n")
        f.write("- `reports/UNCONNECTED_AFTER_FINAL.csv`\n")
        f.write("- `reports/GPIO_FINAL.csv`\n")
        f.write("- `reports/FINAL_FAB_RELEASE.md`\n")
        f.write("- `reports/DRC_AFTER_CONNECT.json`\n")
    print("wrote", path)


def main():
    start = snap_path("pass16-start")
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
    if n0 > 90:
        print(f"start unconn {n0} > 90; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    p015_note = "replacement not added"
    sim_note = "not ripped"

    # 1. ADD replacement
    print("\n#### P0.15_ADD", flush=True)
    r.ok = r.fail = 0
    added = add_p015_replacement(r)
    r.collect()
    got = check(board, r, "pass16-p015-add", last, ceiling, force_fill=True)
    if got[0] is None or not added:
        p015_note = "replacement DRC-failed or blocked; y=20.60 NOT ripped"
        board, r = reload()
        log.append(("P0.15_ADD", "not added", p015_note))
    else:
        ceiling = got[1]
        last = snap_path("pass16-p015-add")
        board, r = reload()
        p015_note = (
            "added B.Cu via (41.75,23.10) jog y=19.80 around VIN_FILT "
            "to existing x=106 V at (106,23.10)/(106,20.60)"
        )
        log.append(("P0.15_ADD", f"added (unconn={ceiling})", p015_note))

        # 2. DELETE y=20.60 corridor
        print("\n#### P0.15_RIP", flush=True)
        pre_rip = snap_path("pass16-pre-p015-rip")
        shutil.copy2(BOARD, pre_rip)
        r.ok = r.fail = 0
        specs = delete_p015_corridor(board, r)
        ripped_txt = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d, _ in specs)
        got = check(board, r, "pass16-p015-rip", pre_rip, ceiling, force_fill=True)
        if got[0] is None:
            p015_note += f". RIP REVERTED (unconn rose). Would have removed {ripped_txt}"
            log.append(("P0.15_RIP", "reverted", p015_note))
            board, r = reload()
        else:
            ceiling = got[1]
            last = snap_path("pass16-p015-rip")
            board, r = reload()
            p015_note += f". Removed y=20.60 corridor: {ripped_txt}. West remnant to x={RIP_X0}, east remnant from x={RIP_X1}."
            log.append(("P0.15_RIP", f"ripped (unconn={ceiling})", ripped_txt or "none"))

    # 3. F-nets
    steps = [
        ("DEC0", route_dec0, "C13 (48.72,31) to (48.65,20) through y=20.25 gap"),
        ("ENABLE_C14U1", route_enable, "C14 (48.33,23.13) to U1 (42.75,44); 0.7 mm C14 GND jog"),
        ("VDD2_FB3", route_vdd2_fb3, "FB3 (68.40,18) to C8 (52.22,32)/(59.70,32) through gap"),
        ("nRESET_J8R5", route_nreset_j8_r5, "J8 (52.22,10.80) to R5 via y=20.25; P0.22 (53.65,6) J1"),
        ("VIN_FILT", route_vin_filt, "JP1 (55.35,13.30) to island (51.90,21.90); short hops"),
        ("VIN_F", route_vin_f, "F1 (49.30,12.60) to FB4; no ~80 mm B.Cu"),
        ("SIM_CLK_U1", route_sim_clk_u1, "courtyard via (31.25,23.10) east of RF to (70.90,45.50)"),
        ("SIM_CLK_C", route_sim_clk_c, "U4 to J7; names distinct"),
        ("SIM_IO_C", route_sim_io_c, "U4 to J7; names distinct"),
        ("P0.08", route_p008, "U1 via (46.20,30) to SW3; east of VDD2 x=52.22"),
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

    # 4. SIM_RST add-then-delete only if *_C still open and replacement exists
    pairs_now, _, _, _ = run_drc()
    if sim_c_still_open(pairs_now):
        print("\n#### SIM_RST_ADD", flush=True)
        r.ok = r.fail = 0
        if add_sim_rst_replacement(r):
            got = check(board, r, "pass16-simrst-add", last, ceiling, force_fill=True)
            if got[0] is None:
                sim_note = "replacement DRC-failed; vertical not ripped"
                board, r = reload()
            else:
                ceiling = got[1]
                last = snap_path("pass16-simrst-add")
                board, r = reload()
                pre = snap_path("pass16-pre-simrst-rip")
                shutil.copy2(BOARD, pre)
                r.ok = r.fail = 0
                hits = delete_sim_rst_vertical(board, r)
                got = check(board, r, "pass16-simrst-rip", pre, ceiling, force_fill=True)
                if got[0] is None:
                    sim_note = "replacement added but vertical rip reverted (unconn rose)"
                    board, r = reload()
                else:
                    ceiling = got[1]
                    last = snap_path("pass16-simrst-rip")
                    board, r = reload()
                    sim_note = f"replacement added; ripped {len(hits)} x=78.25 segments"
                    # retry SIM_C after rip
                    for name, fn, note in [
                        ("SIM_CLK_C_after", route_sim_clk_c, "retry after SIM_RST rip"),
                        ("SIM_IO_C_after", route_sim_io_c, "retry after SIM_RST rip"),
                    ]:
                        print(f"\n#### {name}", flush=True)
                        before = ceiling
                        board, r, last, ok, ceiling = apply_net(board, r, name, fn, last, ceiling)
                        status = (
                            f"closed ({before}→{ceiling})"
                            if ok and ceiling < before
                            else "not closed"
                        )
                        log.append((name, status, note))
        else:
            sim_note = "no CLEAR replacement; x=78.25 not ripped"
        log.append(("SIM_RST", sim_note, "add-then-delete only if *_C blocked"))
    else:
        sim_note = "SIM_*_C already closed; SIM_RST not touched"
        log.append(("SIM_RST", sim_note, "skipped"))

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass16"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(
        n0,
        n1,
        counts.get("shorting_items", 0),
        counts,
        pairs,
        log,
        board,
        p015_note,
        sim_note,
    )
    print(
        f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} "
        f"classes={dict(class_counts(pairs))}"
    )
    print("P0.15:", p015_note)
    print("SIM_RST:", sim_note)
    for name, status, note in log:
        print(f"  {name}: {status}")
    for line in leftover_f(pairs):
        print(f"  leftover {line}")
    fab = n1 == 0 and counts.get("shorting_items", 0) == 0
    print(f"FAB={'yes' if fab else 'no'}")
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= n0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
