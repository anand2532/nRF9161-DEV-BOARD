#!/usr/bin/env python3
"""Pass 15: remaining F14 + tiny nRESET C39 pad on the LIVE board.

Loads the LIVE board. Never restores backups, never re-places the 11 extra
U1 vias, never calls complete_route.main() / rebuild_bcu / autoroute.
Zone refill after each hop. Save only if shorts stay 0 and unconnected
does not rise above the start count.
"""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    SNAP_DIR,
    fill_zones,
    run_drc,
)
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    class_counts,
    reload,
    snap_path,
    try_any,
    try_commit,
    waypoint_route,
    write_gpio_csv,
    write_unconnected_csv,
    XS as XS14,
    YS as YS14,
    check,
)

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"

# Denser local grids around F-island cages (P0.15, VIN, SIM_RST, ENABLE).
XS = sorted(
    set(XS14)
    | {
        31.25, 32.25, 32.40, 35.40, 36.50, 36.80, 37.50, 40.50, 40.80,
        41.20, 42.50, 45.48, 45.58, 45.68, 46.80, 47.20, 47.80, 48.33,
        48.65, 49.30, 50.85, 51.40, 51.50, 51.90, 52.22, 53.65, 55.35,
        60.50, 62.50, 63.00, 64.20, 66.50, 66.80, 67.00, 67.50, 68.14,
        68.79, 69.44, 69.50, 70.20, 70.80, 70.90, 71.58, 72.40, 72.50,
        72.88, 73.30, 73.50, 74.00, 75.10, 76.62, 77.35, 78.38, 79.67,
        80.50, 80.80, 97.50, 98.54, 99.19, 102.33, 107.50,
    }
)
YS = sorted(
    set(YS14)
    | {
        4.40, 4.80, 5.20, 6.50, 7.27, 8.20, 9.20, 10.80, 11.20, 12.60,
        13.30, 14.00, 15.70, 15.80, 16.00, 16.30, 16.50, 16.87, 17.20,
        18.00, 18.40, 19.13, 19.80, 20.20, 20.35, 21.13, 21.20, 21.50,
        21.90, 22.00, 23.10, 23.13, 24.90, 25.40, 25.80, 25.90, 26.00,
        27.13, 29.60, 30.00, 31.20, 31.50, 32.00, 33.50, 36.00, 37.25,
        38.80, 40.50, 41.10, 41.50, 42.40, 42.80, 43.20, 45.50, 46.67,
        48.71, 50.01, 54.70, 55.40, 56.05, 56.70, 57.20, 58.40,
    }
)


def try_wp(r, name, layer, w, x1, y1, x2, y2, label, max_l=40, xs=None, ys=None):
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name, xs=xs or XS, ys=ys or YS)
    if pts is None:
        print(f"  FAIL waypoint {label}: no path")
        return False
    if L > max_l:
        print(f"  skip long waypoint {label} L={L:.1f}")
        return False
    return try_commit(r, pts, layer, w, name, f"waypoint {label} L={L:.1f}")


def apply_net(board, r, name, fn, last, ceiling):
    r.ok = 0
    r.fail = 0
    fn(r)
    r.collect()
    got = check(r.board, r, f"pass15-{name.replace('.', '')}", last, ceiling)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    pairs, n, counts, _ = got
    last = snap_path(f"pass15-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n


def stitch_via(r, name, sites, f_from, b_from, size=0.60, drill=0.30, w=0.18):
    """Place via + F/B stubs. Custom 0.45/0.25 allowed for C39."""
    for vx, vy in sites:
        whyv = r.via_why(vx, vy, name, pwr=False, size=size, drill=drill)
        if whyv is not None:
            print(f"  via_why ({vx:.2f},{vy:.2f}) {size:.2f}/{drill:.2f} {whyv}")
            continue
        fpts = list(f_from) + [(vx, vy)]
        bpts = [(vx, vy)] + list(b_from)
        f_ok = r.path_clear(fpts, pcbnew.F_Cu, w, name)
        b_ok = r.path_clear(bpts, pcbnew.B_Cu, w, name)
        if not f_ok:
            print(f"  F {why(r, fpts, pcbnew.F_Cu, w, name)}")
            continue
        r.add_via(vx, vy, r.code_of(name), name, pwr=False, size=size, drill=drill)
        r.commit(fpts, pcbnew.F_Cu, w, r.code_of(name), name)
        b_len = hypot(bpts[0][0], bpts[0][1], bpts[-1][0], bpts[-1][1]) if len(bpts) >= 2 else 0
        if b_ok and b_len >= 0.03:
            r.commit(bpts, pcbnew.B_Cu, w, r.code_of(name), name)
        elif not b_ok:
            print(f"  B skip {why(r, bpts, pcbnew.B_Cu, w, name)}")
        print(f"  OK via ({vx:.2f},{vy:.2f}) {size:.2f}/{drill:.2f}")
        return True
    return False


# --- per-net routers -------------------------------------------------------

def route_nreset_c39(r):
    print("== nRESET C39 0.45/0.25 via (east of VDD_nRF, west of C39.2) ==", flush=True)
    # Pad (45.68,16.00) to B stub (45.68,16.30). 0.60 via hits C39.2 / VDD_nRF.
    sites = [
        (45.68, 15.80),
        (45.58, 15.80),
        (45.68, 15.70),
        (45.48, 16.00),
        (45.78, 15.75),
        (45.58, 15.70),
    ]
    if stitch_via(
        r,
        "nRESET",
        sites,
        f_from=[(45.68, 16.00)],
        b_from=[(45.68, 16.30)],
        size=0.45,
        drill=0.25,
        w=0.18,
    ):
        return
    # Short F jog east then via (still west of C39.2 at x=46.32).
    for vx, vy in [(45.90, 15.55), (45.85, 15.60)]:
        if r.via_why(vx, vy, "nRESET", pwr=False, size=0.45, drill=0.25) is None:
            fpts = [(45.68, 16.00), (45.68, 15.55), (vx, vy)]
            bpts = [(vx, vy), (45.68, 16.30)]
            if r.path_clear(fpts, pcbnew.F_Cu, 0.18, "nRESET") and r.path_clear(
                bpts, pcbnew.B_Cu, 0.18, "nRESET"
            ):
                r.add_via(vx, vy, r.code_of("nRESET"), "nRESET", pwr=False, size=0.45, drill=0.25)
                r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("nRESET"), "nRESET")
                r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("nRESET"), "nRESET")
                print(f"  OK jog+via ({vx:.2f},{vy:.2f})")
                return
    print("  C39 pad not stitched")


def route_nreset_j8_r5(r):
    print("== nRESET J8–R5 (south of P0.22 / north of J1 / B alley) ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    if try_any(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [
                    (45.68, 19.80),
                    (66.80, 19.80),
                    (66.80, 18.40),
                    (73.50, 18.40),
                    (73.50, 20.35),
                    (97.50, 20.35),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B jog VDD2/VIN_F then y20.35",
            ),
            (
                [
                    (45.68, 19.80),
                    (67.00, 19.80),
                    (67.00, 20.35),
                    (70.20, 20.35),
                    (70.20, 18.20),
                    (73.50, 18.20),
                    (73.50, 20.35),
                    (97.50, 20.35),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B snake FB3 vias",
            ),
            (
                [
                    (45.68, 16.87),
                    (40.50, 16.87),
                    (40.50, 20.35),
                    (97.50, 20.35),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B west of nRESET V then alley",
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
                "F y4.4 north of J1 / VIN_IN",
            ),
            (
                [
                    (53.65, 10.80),
                    (58.80, 10.80),
                    (58.80, 8.80),
                    (64.80, 8.80),
                    (64.80, 4.40),
                    (80.80, 4.40),
                    (80.80, 27.13),
                    (102.33, 27.13),
                ],
                "F jog D1 then y4.4",
            ),
            (
                [
                    (52.22, 11.20),
                    (52.22, 14.40),
                    (64.20, 14.40),
                    (64.20, 21.20),
                    (75.50, 21.20),
                    (75.50, 23.80),
                    (102.33, 23.80),
                    (102.33, 27.13),
                ],
                "F east of VIN x=66 then south of VIN H 20.70",
            ),
        ],
    ):
        return
    if try_wp(r, "nRESET", B, 0.18, 45.68, 19.80, 102.33, 27.13, "B C39-R5", max_l=90):
        return
    try_wp(r, "nRESET", F, 0.18, 53.65, 7.27, 102.33, 27.13, "F J8-R5", max_l=90)


def route_dec0(r):
    print("== DEC0 C13 to y≈20 (east of ENABLE via) ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    # New via west of C13.2 GND (49.68,29.60) / east of P0.10 (47.40,28.50).
    placed = stitch_via(
        r,
        "DEC0",
        [(47.80, 31.20), (47.20, 31.20), (46.80, 31.50), (46.50, 31.80)],
        f_from=[(48.72, 31.00)],
        b_from=[(47.80, 31.20)],
        size=0.60,
        drill=0.30,
        w=0.18,
    )
    if try_any(
        r,
        "DEC0",
        B,
        0.18,
        [
            (
                [
                    (47.80, 31.20),
                    (51.50, 31.20),
                    (51.50, 38.80),
                    (60.50, 38.80),
                    (60.50, 42.80),
                    (63.20, 42.80),
                    (63.20, 21.13),
                    (48.65, 21.13),
                ],
                "B north of C9 / east of TP12 V",
            ),
            (
                [
                    (47.80, 31.20),
                    (51.40, 31.20),
                    (51.40, 24.20),
                    (53.20, 24.20),
                    (53.20, 21.13),
                    (48.65, 21.13),
                ],
                "B x51.4 then east of ENABLE via",
            ),
            (
                [
                    (47.80, 31.20),
                    (40.50, 31.20),
                    (40.50, 21.13),
                    (48.65, 21.13),
                ],
                "B west of VDD2 H x=43.25",
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
                    (48.72, 33.40),
                    (52.80, 33.40),
                    (52.80, 20.00),
                    (48.65, 20.00),
                ],
                "F east of VDD1 V x=50.68",
            ),
            (
                [
                    (48.72, 29.60),
                    (50.20, 29.60),
                    (50.20, 20.00),
                    (48.65, 20.00),
                ],
                "F between C13.2 and VDD1",
            ),
        ],
    ):
        return
    sx, sy = (47.80, 31.20) if placed else (48.72, 31.00)
    if not try_wp(r, "DEC0", B, 0.18, sx, sy, 48.65, 21.13, "B C13-via", max_l=50):
        try_wp(r, "DEC0", F, 0.18, 48.72, 31.00, 48.65, 20.00, "F C13-TP18", max_l=40)


def route_enable_c14_u1(r):
    print("== ENABLE C14–U1 (y-jog around C14 GND / DEC0 via) ==", flush=True)
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
                    (46.20, 22.00),
                    (46.20, 27.20),
                    (42.75, 27.20),
                    (42.75, 37.25),
                ],
                "F west of C14 GND then U1",
            ),
            (
                [
                    (47.68, 22.00),
                    (50.85, 22.00),
                    (50.85, 25.80),
                    (72.86, 25.80),
                    (72.86, 40.95),
                ],
                "F via C14 via east to U2",
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
                    (40.80, 23.13),
                    (40.80, 25.20),
                    (40.80, 41.10),
                    (42.75, 41.10),
                ],
                "B west of P0.17 via to U1 via",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 25.80),
                    (73.30, 25.80),
                    (73.30, 42.40),
                    (74.20, 42.40),
                ],
                "B C14 via to U2 via north of COEX2",
            ),
            (
                [
                    (48.33, 23.13),
                    (48.33, 36.00),
                    (42.75, 36.00),
                    (42.75, 41.10),
                ],
                "B north past P0.08 via",
            ),
        ],
    ):
        return
    if not try_wp(r, "ENABLE", B, 0.18, 48.33, 23.13, 42.75, 41.10, "B C14-U1", max_l=50):
        try_wp(r, "ENABLE", F, 0.18, 47.68, 22.00, 42.75, 37.25, "F C14-U1", max_l=40)


def route_vdd2_fb3(r):
    print("== VDD2 FB3 island to C8 B.Cu (P0.01 / P0.15 alley) ==", flush=True)
    B = pcbnew.B_Cu
    if try_any(
        r,
        "VDD2",
        B,
        0.18,
        [
            (
                [
                    (68.79, 19.13),
                    (66.50, 19.13),
                    (66.50, 20.35),
                    (40.80, 20.35),
                    (40.80, 25.90),
                    (44.72, 25.90),
                ],
                "B west of VIN_F then alley to U1 via",
            ),
            (
                [
                    (68.14, 16.87),
                    (70.80, 16.87),
                    (70.80, 20.35),
                    (40.80, 20.35),
                    (40.80, 25.90),
                    (44.72, 25.90),
                ],
                "B east of FB3 then alley",
            ),
            (
                [
                    (68.14, 16.87),
                    (68.14, 14.40),
                    (26.20, 14.40),
                    (26.20, 25.90),
                    (44.72, 25.90),
                ],
                "B west of P0.01 V x=27.65",
            ),
            (
                [
                    (68.14, 16.87),
                    (107.50, 16.87),
                    (107.50, 19.80),
                    (107.50, 32.00),
                    (63.20, 32.00),
                    (59.70, 32.00),
                ],
                "B east wrap x=107.5 (skip if ENABLE/P0.15)",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VDD2",
        pcbnew.F_Cu,
        0.25,
        [
            (
                [
                    (68.40, 18.00),
                    (70.80, 18.00),
                    (70.80, 21.40),
                    (61.30, 21.40),
                    (61.30, 32.00),
                    (53.52, 32.00),
                ],
                "F north of P0.15 then west to C8",
            ),
        ],
    ):
        return
    if not try_wp(r, "VDD2", B, 0.18, 68.14, 16.87, 52.22, 32.00, "B FB3-C8", max_l=55):
        try_wp(r, "VDD2", B, 0.18, 68.79, 19.13, 44.72, 25.90, "B FB3-U1via", max_l=45)


def route_vin_filt(r):
    print("== VIN_FILT JP1 via to island (VIN H y=15.40 / GPIO y=14.80) ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
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
            (
                [
                    (55.35, 13.30),
                    (64.80, 13.30),
                    (64.80, 14.70),
                    (75.10, 14.70),
                    (75.10, 16.94),
                ],
                "F north of VIN H then FB4 column",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 23.80),
                    (51.90, 23.80),
                    (51.90, 21.90),
                ],
                "F south across VIN (likely blocked)",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VIN_FILT",
        B,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (55.35, 16.80),
                    (71.50, 16.80),
                    (71.50, 21.90),
                    (51.90, 21.90),
                ],
                "B south of GPIO H then west",
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
    if not try_wp(r, "VIN_FILT", F, 0.18, 55.35, 13.30, 74.00, 16.94, "F JP1-FB4", max_l=40):
        try_wp(r, "VIN_FILT", B, 0.18, 55.35, 13.30, 51.90, 21.90, "B JP1-island", max_l=30)


def route_vin_f(r):
    print("== VIN_F short hops only (no ~80 mm B.Cu) ==", flush=True)
    B = pcbnew.B_Cu
    if try_any(
        r,
        "VIN_F",
        B,
        0.18,
        [
            (
                [
                    (49.30, 12.60),
                    (54.20, 12.60),
                    (54.20, 10.40),
                    (69.20, 10.40),
                    (69.20, 16.50),
                    (71.58, 16.50),
                    (71.58, 17.66),
                ],
                "B jog VDD_nRF / GPIO V",
            ),
            (
                [
                    (49.30, 12.60),
                    (49.30, 10.40),
                    (54.20, 10.40),
                    (54.20, 16.50),
                    (71.58, 16.50),
                    (71.58, 17.66),
                ],
                "B south of VDD_nRF via then y16.5",
            ),
            (
                [
                    (49.05, 13.33),
                    (47.50, 13.33),
                    (47.50, 16.50),
                    (71.58, 16.50),
                    (71.58, 17.66),
                ],
                "B west then y16.5",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VIN_F",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (49.30, 12.60),
                    (49.30, 11.20),
                    (71.20, 11.20),
                    (71.20, 19.06),
                ],
                "F y11.2 to FB4",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_F", B, 0.18, 49.30, 12.60, 71.58, 17.66, "B F1-FB4", max_l=28)


def route_sim_clk_u1(r):
    print("== SIM_CLK U1 courtyard via to B.Cu east of RF ==", flush=True)
    B = pcbnew.B_Cu
    # Courtyard via already at (31.25, 23.10). Do not enter RF keepout.
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
                    (35.40, 20.90),
                    (35.40, 25.80),
                    (73.30, 25.80),
                    (73.30, 36.00),
                ],
                "B jog COEX0/P0.25 then north of COEX2",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 25.80),
                    (36.80, 25.80),
                    (36.80, 35.00),
                    (73.30, 35.00),
                    (73.30, 36.00),
                ],
                "B south of courtyard row then east",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 21.20),
                    (26.20, 21.20),
                    (26.20, 36.00),
                    (73.30, 36.00),
                ],
                "B west private (still east of RF x=24.2)",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 40.80),
                    (70.90, 40.80),
                    (70.90, 42.40),
                ],
                "B even-ring y=40.8 to existing via",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK", B, 0.18, 31.25, 23.10, 73.30, 36.00, "B U1-TP3", max_l=70)


def route_sim_clk_c(r):
    print("== SIM_CLK_C (keep name; jog around SIM_RST) ==", flush=True)
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
                "B north of SIM_CLK y=57.73 then west of SIM_RST",
            ),
            (
                [
                    (76.62, 56.05),
                    (76.62, 56.70),
                    (80.80, 56.70),
                    (80.80, 46.67),
                    (99.19, 46.67),
                ],
                "B east of SIM_RST_C via",
            ),
            (
                [
                    (76.62, 56.05),
                    (70.20, 56.05),
                    (70.20, 58.40),
                    (66.50, 58.40),
                    (66.50, 41.50),
                    (99.19, 41.50),
                    (99.19, 46.67),
                ],
                "B west under SIM_CLK then y41.5",
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
                "F south of U4 then east to J7",
            ),
            (
                [
                    (76.62, 56.05),
                    (76.62, 53.20),
                    (80.80, 53.20),
                    (80.80, 45.54),
                    (98.54, 45.54),
                ],
                "F east of SIM_RST V",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK_C", B, 0.18, 76.62, 56.05, 99.19, 46.67, "B U4-J7", max_l=50)


def route_sim_io_c(r):
    print("== SIM_IO_C (keep name; jog around SIM_RST) ==", flush=True)
    # U4.1 has no via yet. Try local via then B, or F.
    stitch_via(
        r,
        "SIM_IO_C",
        [(76.20, 55.40), (76.20, 54.70), (75.80, 55.00), (77.35, 54.20)],
        f_from=[(77.35, 55.40)],
        b_from=[(76.20, 55.40)],
        size=0.60,
        drill=0.30,
        w=0.18,
    )
    if try_any(
        r,
        "SIM_IO_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (76.20, 55.40),
                    (76.20, 58.40),
                    (66.50, 58.40),
                    (66.50, 41.50),
                    (98.54, 41.50),
                    (98.54, 50.01),
                ],
                "B north then west of SIM_RST",
            ),
            (
                [
                    (76.20, 55.40),
                    (80.80, 55.40),
                    (80.80, 50.01),
                    (98.54, 50.01),
                ],
                "B east of SIM_RST_C",
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
    print("== P0.08 U1 via to SW3 (east of VDD1/VDD2/ENABLE) ==", flush=True)
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
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
                    (54.80, 34.20),
                    (78.38, 34.20),
                    (78.38, 26.00),
                ],
                "F east of TP11 then y34.2",
            ),
            (
                [
                    (46.20, 30.00),
                    (54.80, 30.00),
                    (54.80, 27.80),
                    (78.38, 27.80),
                    (78.38, 26.00),
                ],
                "F y27.8 south of TP11",
            ),
            (
                [
                    (46.20, 30.00),
                    (46.20, 33.80),
                    (54.80, 33.80),
                    (54.80, 26.00),
                    (79.67, 26.00),
                ],
                "F north of DEC0 H y=31 then y26",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "P0.08",
        B,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (42.40, 30.00),
                    (42.40, 25.20),
                    (54.50, 25.20),
                    (54.50, 24.90),
                    (79.67, 24.90),
                    (79.67, 26.00),
                ],
                "B west of VDD2 H then y24.9",
            ),
            (
                [
                    (46.20, 30.00),
                    (42.40, 30.00),
                    (42.40, 38.80),
                    (63.20, 38.80),
                    (63.20, 26.00),
                    (79.67, 26.00),
                ],
                "B north of C9 then x63.2",
            ),
            (
                [
                    (46.20, 30.00),
                    (54.80, 30.00),
                    (54.80, 24.90),
                    (75.50, 24.90),
                    (75.50, 26.00),
                    (79.67, 26.00),
                ],
                "B east of VDD1 via y=27.13",
            ),
        ],
    ):
        return
    if not try_wp(r, "P0.08", F, 0.18, 46.20, 30.00, 79.67, 26.00, "F U1-SW3", max_l=55):
        try_wp(r, "P0.08", B, 0.18, 46.20, 30.00, 79.67, 26.00, "B U1-SW3", max_l=55)


def remaining_f_notes(pairs):
    """Blocker xy for still-open F targets."""
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
        f.write("| Live snapshot after this pass | `after-pass15.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass14.kicad_pcb` |\n\n")
        f.write("## This pass (remaining F14 + nRESET C39 pad)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was the start count. Zone refill ran after new copper. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("The 11 extra U1 vias pass13 deleted were not re-placed. ")
        f.write("P0.06 headers / G7 / DNP C22–C24 were skipped. ")
        f.write("SIM_*_C names were not merged. GND: refill only.\n\n")
        f.write("Overall from pass14 start: **98** → this pass end **")
        f.write(f"{n1}**.\n\n")
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
        left = remaining_f_notes(pairs)
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
    start = snap_path("pass15-start")
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
    if n0 > 91:
        print(f"start unconn {n0} > 91; abort (do not worsen from briefing)")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []

    steps = [
        ("nRESET_C39", route_nreset_c39, "0.45/0.25 via at C39 pad (45.68,16.00) to B stub (45.68,16.30)"),
        ("nRESET_J8R5", route_nreset_j8_r5, "J8 F (53.65,7.27) to R5 B/F (102.33,27.13); P0.22 via (53.65,6.00) J1 (82,6)/(82,8.54)"),
        ("DEC0", route_dec0, "C13 (48.72,29.60) to DEC0 via (48.65,21.13); ENABLE via (48.33,23.13) P0.10 (47.40,28.50)"),
        ("ENABLE_C14U1", route_enable_c14_u1, "C14 (47.68,22) to U1; DEC0 via (48.65,21.13) C14.2 (48.32,22)"),
        ("VDD2_FB3", route_vdd2_fb3, "FB3 (68.40,18) to C8 B (52.22,32); VDD2_MID (67.21,16.30) P0.01 y=15.20 P0.15 y=20.60"),
        ("VIN_FILT", route_vin_filt, "JP1 via (55.35,13.30) to island (51.90,21.90); VDD_GPIO y=14.80 / x=70"),
        ("VIN_F", route_vin_f, "short hops F1 via (49.30,12.60) to FB4; no ~80 mm B.Cu"),
        ("SIM_CLK_U1", route_sim_clk_u1, "U1 F via (31.25,23.10) to B (70.90,45.50)/(73.30,36); east of RF"),
        ("SIM_CLK_C", route_sim_clk_c, "U4 (76.62,56.05) to J7 (99.19,46.67); SIM_RST_C (79.38,56.05) SIM_RST x=78.25"),
        ("SIM_IO_C", route_sim_io_c, "U4 (77.35,55.40) to J7 (98.54,48.71); names kept distinct"),
        ("P0.08", route_p008, "U1 via (46.20,30) to SW3 (79.67,26); VDD1 (53.70,27.13) VDD2 x=52.22 ENABLE x=76.80"),
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

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass15"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board)
    print(
        f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} "
        f"classes={dict(class_counts(pairs))}"
    )
    for name, status, note in log:
        print(f"  {name}: {status}")
    for line in remaining_f_notes(pairs):
        print(f"  leftover {line}")
    fab = n1 == 0 and counts.get("shorting_items", 0) == 0
    print(f"FAB={'yes' if fab else 'no'}")
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= n0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
