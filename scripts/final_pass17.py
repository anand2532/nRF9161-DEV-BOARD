#!/usr/bin/env python3
"""Pass 17: close F-nets through the freed y≈20.60 band.

LIVE board only. Do not restore backups, do not re-place extra U1 vias,
do not edit the plan, do not generate /fab unless unconnected=0 AND ratsnest=0.
Jog around ENABLE (48.33,23.13), VIN_FILT (52.55,23.03), COEX2, VIN_F.
Save only if shorts=0. Unconnected must not finish above 90.
"""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
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

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}


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
    got = check(r.board, r, f"pass17-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    pairs, n, counts, _ = got
    last = snap_path(f"pass17-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n


def record(r, name, pts, layer, w, lab):
    msg = why(r, pts, layer, w, name)
    BLOCKERS[name] = f"{lab}: {msg}"
    print(f"  BLOCK {lab}: {msg}", flush=True)


def try_list(r, name, layer, w, cands):
    for pts, lab in cands:
        if try_commit(r, pts, layer, w, name, lab):
            BLOCKERS.pop(name, None)
            return True
        record(r, name, pts, layer, w, lab)
    return False


def compress(pts):
    if not pts:
        return pts
    out = [pts[0]]
    for p in pts[1:]:
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if abs(a[0] - b[0]) < 0.02 and abs(b[0] - p[0]) < 0.02:
                out[-1] = p
                continue
            if abs(a[1] - b[1]) < 0.02 and abs(b[1] - p[1]) < 0.02:
                out[-1] = p
                continue
        out.append(p)
    return out


def try_wp_box(r, name, layer, w, x1, y1, x2, y2, x0, x3, y0, y3, step, max_l, lab):
    xs = []
    x = x0
    while x <= x3 + 1e-9:
        xs.append(round(x, 3))
        x += step
    ys = []
    y = y0
    while y <= y3 + 1e-9:
        ys.append(round(y, 3))
        y += step
    xs = sorted(set(xs + [round(x1, 3), round(x2, 3)]))
    ys = sorted(set(ys + [round(y1, 3), round(y2, 3)]))
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name, xs=xs, ys=ys)
    if pts is None:
        print(f"  FAIL waypoint {lab}", flush=True)
        return False
    pts = compress(pts)
    if L > max_l:
        print(f"  skip long waypoint {lab} L={L:.1f}", flush=True)
        BLOCKERS[name] = f"{lab} L={L:.1f} (over max {max_l})"
        return False
    if try_commit(r, pts, layer, w, name, f"waypoint {lab} L={L:.1f}"):
        BLOCKERS.pop(name, None)
        return True
    record(r, name, pts, layer, w, lab)
    return False


def try_via_routes(r, name, pwr, vias, routes):
    """Place vias then commit routes. All path_clear first."""
    for x, y in vias:
        w = r.via_why(x, y, name, pwr=pwr)
        if w is not None:
            print(f"  via ({x:.2f},{y:.2f}) {w}", flush=True)
            BLOCKERS[name] = f"via ({x:.2f},{y:.2f}) {w}"
            return False
    for pts, layer, w, lab in routes:
        if not r.path_clear(pts, layer, w, name):
            record(r, name, pts, layer, w, lab)
            return False
    for x, y in vias:
        r.add_via(x, y, r.code_of(name), name, pwr=pwr)
        print(f"  via {name} ({x:.2f},{y:.2f})", flush=True)
    for pts, layer, w, lab in routes:
        r.commit(pts, layer, w, r.code_of(name), name)
        print(f"  OK {lab}", flush=True)
    BLOCKERS.pop(name, None)
    return True


# --- routers ----------------------------------------------------------------

def route_dec0(r):
    print("== DEC0 C13 (48.72,31) → (48.65,20); east first, west jog around ENABLE ==", flush=True)
    # User-requested east jog x≈50.5–51.5 through y=20.60 (P0.15 gone).
    if try_list(
        r,
        "DEC0",
        F,
        0.18,
        [
            (
                [
                    (48.72, 31.00),
                    (51.20, 31.00),
                    (51.20, 20.60),
                    (48.65, 20.60),
                    (48.65, 20.00),
                ],
                "F east x51.2 y20.60",
            ),
            (
                [
                    (48.72, 31.00),
                    (50.80, 31.00),
                    (50.80, 24.80),
                    (51.40, 24.80),
                    (51.40, 20.60),
                    (48.65, 20.60),
                    (48.65, 20.00),
                ],
                "F east jog ENABLE/VIN_FILT",
            ),
        ],
    ):
        return
    # B from existing C13 via, east of ENABLE, through y=20.60, west to dest via.
    if try_list(
        r,
        "DEC0",
        B,
        0.18,
        [
            (
                [
                    (47.80, 31.20),
                    (49.80, 31.20),
                    (49.80, 33.20),
                    (58.20, 33.20),
                    (58.20, 42.80),
                    (64.80, 42.80),
                    (64.80, 20.60),
                    (48.65, 20.60),
                    (48.65, 21.13),
                ],
                "B VDD2-stair then y20.60 (crosses COEX2?)",
            ),
            (
                [
                    (47.80, 31.20),
                    (51.40, 31.20),
                    (51.40, 20.60),
                    (48.65, 20.60),
                    (48.65, 21.13),
                ],
                "B x51.4 y20.60",
            ),
        ],
    ):
        return
    # Proven F west jog around ENABLE (48.33,23.13), then east on y=21.50
    # through the freed band to dest. East alley did not fit.
    if try_commit(
        r,
        [
            (48.72, 31.00),
            (48.65, 31.00),
            (48.65, 28.75),
            (48.00, 28.75),
            (48.00, 23.75),
            (47.75, 23.75),
            (47.50, 23.50),
            (47.50, 22.50),
            (47.00, 22.50),
            (47.00, 21.50),
            (48.65, 21.50),
            (48.65, 20.00),
        ],
        F,
        0.18,
        "DEC0",
        "F west of ENABLE then y=21.50 to dest",
    ):
        BLOCKERS.pop("DEC0", None)
        return
    if try_via_routes(
        r,
        "DEC0",
        False,
        [(64.80, 42.80), (54.50, 20.60)],
        [
            (
                [
                    (47.80, 31.20),
                    (49.80, 31.20),
                    (49.80, 33.20),
                    (58.20, 33.20),
                    (58.20, 42.80),
                    (64.80, 42.80),
                ],
                B,
                0.18,
                "B C13 to via 64.8,42.8",
            ),
            (
                [
                    (54.50, 20.60),
                    (48.65, 20.60),
                    (48.65, 21.13),
                ],
                B,
                0.18,
                "B via 54.5 to dest",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "DEC0", F, 0.18, 48.72, 31.00, 48.65, 20.00,
        44.0, 56.0, 19.5, 33.0, 0.25, 25, "F dense C13-dest",
    )


def route_enable(r):
    print("== ENABLE C14–U1; y-jog C14.2; tie SW1; no 40 mm ==", flush=True)
    # C14–R1 y-jog ~0.7 mm around C14.2 GND (48.32, 22)
    try_list(
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
                    (47.68, 22.70),
                    (50.00, 22.70),
                    (50.00, 21.68),
                ],
                "F C14-R1 y+0.70",
            ),
        ],
    )
    if try_list(
        r,
        "ENABLE",
        B,
        0.18,
        [
            (
                [
                    (48.33, 23.13),
                    (47.20, 23.13),
                    (47.20, 20.60),
                    (42.75, 20.60),
                    (42.75, 41.10),
                ],
                "B west then y20.60 to U1 via",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 20.60),
                    (54.80, 20.60),
                    (54.80, 42.40),
                    (74.20, 42.40),
                ],
                "B y20.60 then to SW1 via (long?)",
            ),
            (
                [
                    (50.85, 23.15),
                    (51.40, 23.15),
                    (51.40, 20.60),
                    (76.80, 20.60),
                    (76.80, 28.00),
                ],
                "B y20.60 to existing ENABLE x76.8",
            ),
            (
                [
                    (48.33, 23.13),
                    (49.80, 33.20),
                    (43.40, 33.20),
                    (43.40, 45.13),
                ],
                "B south around VDD1 to U1 via",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "ENABLE",
        F,
        0.18,
        [
            (
                [
                    (47.68, 22.00),
                    (45.50, 22.00),
                    (45.50, 37.25),
                    (42.75, 37.25),
                ],
                "F west of C14 to U1.101",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 20.80),
                    (42.75, 20.80),
                    (42.75, 37.25),
                ],
                "F y20.80 to U1 column",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "ENABLE", B, 0.18, 48.33, 23.13, 42.75, 41.10,
        40.0, 56.0, 20.0, 46.0, 0.30, 35, "B dense C14-U1",
    )
    if r.ok:
        return
    try_wp_box(
        r, "ENABLE", F, 0.18, 47.68, 22.00, 42.75, 37.25,
        40.0, 56.0, 20.0, 46.0, 0.30, 35, "F dense C14-U1",
    )


def route_vdd2_fb3(r):
    print("== VDD2 FB3 (68.79,19.13) → C8 B (59.70,32) through y=20.60 ==", flush=True)
    if try_list(
        r,
        "VDD2",
        B,
        0.25,
        [
            (
                [
                    (68.79, 19.13),
                    (68.79, 21.20),
                    (54.50, 21.20),
                    (54.50, 26.20),
                    (52.22, 26.20),
                    (52.22, 26.75),
                ],
                "B y21.2 under VIN_FILT to VDD2 H",
            ),
            (
                [
                    (68.79, 19.13),
                    (70.50, 19.13),
                    (70.50, 21.20),
                    (61.80, 21.20),
                    (61.80, 32.00),
                    (59.70, 32.00),
                ],
                "B east of VIN_F then west of VDD_nRF",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 21.20),
                    (61.50, 21.20),
                    (61.50, 26.20),
                    (61.50, 32.00),
                    (59.70, 32.00),
                ],
                "B y21.2 x61.5 (east of VDD_nRF 59.30,27.46)",
            ),
        ],
    ):
        return
    if try_via_routes(
        r,
        "VDD2",
        True,
        [(54.50, 21.20)],
        [
            (
                [(68.79, 19.13), (68.79, 21.20), (54.50, 21.20)],
                B,
                0.25,
                "B FB3 to via 54.5,21.2",
            ),
            (
                [
                    (54.50, 21.20),
                    (54.50, 23.20),
                    (76.20, 23.20),
                    (76.20, 33.50),
                    (59.70, 33.50),
                    (59.70, 36.00),
                ],
                F,
                0.25,
                "F east of VIN_FILT wall to C8",
            ),
        ],
    ):
        return
    if try_via_routes(
        r,
        "VDD2",
        True,
        [(54.50, 21.20)],
        [
            (
                [(68.79, 19.13), (68.79, 21.20), (54.50, 21.20)],
                B,
                0.25,
                "B FB3 to via 54.5",
            ),
            (
                [
                    (54.50, 21.20),
                    (50.40, 21.20),
                    (50.40, 32.00),
                    (52.22, 32.00),
                ],
                F,
                0.25,
                "F west of VIN_FILT x=51.90 to C8 via",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VDD2", B, 0.25, 68.79, 19.13, 59.70, 32.00,
        50.0, 78.0, 16.0, 38.0, 0.35, 45, "B dense FB3-C8",
    )
    if r.ok:
        return
    try_wp_box(
        r, "VDD2", F, 0.25, 68.79, 19.13, 59.70, 36.00,
        50.0, 78.0, 16.0, 38.0, 0.35, 45, "F dense FB3-C8",
    )


def route_vin_filt(r):
    print("== VIN_FILT (55.35,13.30) → island (51.90,21.90) through y=20.60 ==", flush=True)
    if try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            (
                [
                    (55.35, 13.30),
                    (55.35, 13.80),
                    (64.20, 13.80),
                    (64.20, 20.60),
                    (51.90, 20.60),
                    (51.90, 21.90),
                ],
                "F east of VIN x=62 then y20.60",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 13.80),
                    (64.20, 13.80),
                    (64.20, 18.40),
                    (73.50, 18.40),
                    (73.50, 16.94),
                    (74.00, 16.94),
                ],
                "F to FB4.2 jogging VDD2_MID / VIN x=66",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 11.20),
                    (59.80, 11.20),
                    (59.80, 8.20),
                    (73.80, 8.20),
                    (73.80, 16.94),
                    (74.00, 16.94),
                ],
                "F north of VIN V x=66 / D1",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "VIN_FILT",
        B,
        0.25,
        [
            (
                [
                    (55.35, 13.30),
                    (55.35, 12.40),
                    (47.80, 12.40),
                    (47.80, 20.60),
                    (51.90, 20.60),
                    (51.90, 21.90),
                ],
                "B west of VDD_GPIO then y20.60",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 7.20),
                    (61.20, 7.20),
                    (61.20, 7.20),
                    (71.50, 7.20),
                    (71.50, 16.94),
                    (74.00, 16.94),
                ],
                "B north of VDD_GPIO V x=70",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 20.60),
                    (51.90, 20.60),
                    (51.90, 21.90),
                ],
                "B direct y20.60 (VDD_GPIO?)",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_FILT", F, 0.25, 55.35, 13.30, 51.90, 21.90,
        47.0, 76.0, 7.0, 24.0, 0.30, 40, "F dense JP1-island",
    )
    if r.ok:
        return
    try_wp_box(
        r, "VIN_FILT", B, 0.25, 55.35, 13.30, 74.00, 16.94,
        47.0, 76.0, 6.5, 22.0, 0.30, 40, "B dense JP1-FB4",
    )


def route_vin_f(r):
    print("== VIN_F short hops to existing vias; no ~80 mm bus ==", flush=True)
    if try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            (
                [
                    (49.30, 12.60),
                    (49.30, 12.00),
                    (64.50, 12.00),
                    (64.50, 19.06),
                    (71.20, 19.06),
                    (71.20, 19.80),
                ],
                "F north of VIN H y=15.40 east of x=62",
            ),
            (
                [
                    (49.30, 12.60),
                    (49.30, 13.80),
                    (64.50, 13.80),
                    (64.50, 17.66),
                    (71.58, 17.66),
                ],
                "F y13.8 to FB4 via",
            ),
            (
                [
                    (49.30, 12.60),
                    (49.30, 20.60),
                    (71.20, 20.60),
                    (71.20, 19.80),
                ],
                "F y20.60 F1 to VIN_F island",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "VIN_F",
        B,
        0.25,
        [
            (
                [
                    (49.30, 12.60),
                    (49.30, 20.60),
                    (71.20, 20.60),
                    (71.20, 19.80),
                ],
                "B y20.60 F1 to VIN_F island",
            ),
            (
                [
                    (49.30, 12.60),
                    (47.80, 12.60),
                    (47.80, 20.60),
                    (71.20, 20.60),
                    (71.20, 19.06),
                ],
                "B west of VDD_GPIO then y20.60",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_F", F, 0.25, 49.30, 12.60, 71.58, 17.66,
        47.0, 76.0, 11.0, 22.0, 0.30, 40, "F dense F1-FB4",
    )
    if r.ok:
        return
    try_wp_box(
        r, "VIN_F", B, 0.25, 49.30, 12.60, 71.20, 19.80,
        47.0, 76.0, 11.0, 22.0, 0.30, 40, "B dense F1-island",
    )


def route_nreset(r):
    print("== nRESET J8 (52.22,10.80) toward R5; south of P0.22; west of COEX2 V ==", flush=True)
    if try_list(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [
                    (52.22, 10.80),
                    (52.22, 20.60),
                    (99.20, 20.60),
                    (99.20, 26.00),
                    (101.68, 26.00),
                ],
                "B y20.60 to R5 (GND 100,20?)",
            ),
            (
                [
                    (45.68, 19.80),
                    (45.68, 18.20),
                    (99.20, 18.20),
                    (99.20, 26.00),
                    (101.68, 26.00),
                ],
                "B y18.2 from C39 island to R5",
            ),
            (
                [
                    (45.68, 19.80),
                    (99.20, 19.80),
                    (99.20, 21.50),
                    (103.80, 21.50),
                    (103.80, 27.13),
                    (102.33, 27.13),
                ],
                "B y19.8 jog GND 100,20 then R5 via",
            ),
            (
                [
                    (38.25, 21.80),
                    (38.25, 20.60),
                    (104.40, 20.60),
                    (104.40, 27.13),
                    (102.33, 27.13),
                ],
                "B U1 via y20.60 west of COEX2 V 105.10",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "nRESET",
        F,
        0.18,
        [
            (
                [
                    (52.22, 10.80),
                    (53.65, 10.80),
                    (53.65, 5.20),
                    (101.68, 5.20),
                    (101.68, 26.00),
                ],
                "F south of P0.22 (53.65,6) to R5",
            ),
            (
                [
                    (52.22, 10.80),
                    (52.22, 20.60),
                    (101.68, 20.60),
                    (101.68, 26.00),
                ],
                "F y20.60 to R5",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "nRESET", B, 0.18, 45.68, 19.80, 101.68, 26.00,
        38.0, 108.0, 15.0, 28.0, 0.40, 70, "B dense C39-R5",
    )


def route_sim_clk_u1(r):
    print("== SIM_CLK U1 courtyard via (31.25,23.10) east to B (70.90,45.50) ==", flush=True)
    if try_list(
        r,
        "SIM_CLK",
        B,
        0.18,
        [
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 20.60),
                    (70.90, 20.60),
                    (70.90, 42.40),
                ],
                "B jog P0.20 then y20.60 to existing",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 21.50),
                    (70.50, 21.50),
                    (70.50, 42.40),
                    (70.90, 42.40),
                ],
                "B y21.5 south of P0.20 / north of VIN_F 71.20,19.80",
            ),
            (
                [
                    (31.25, 23.10),
                    (25.50, 23.10),
                    (25.50, 45.50),
                    (70.90, 45.50),
                ],
                "B west corridor (RF keepout?)",
            ),
            (
                [
                    (31.25, 23.10),
                    (31.25, 20.60),
                    (70.90, 20.60),
                    (70.90, 45.50),
                ],
                "B y20.60 direct",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "SIM_CLK",
        F,
        0.18,
        [
            (
                [
                    (31.25, 23.10),
                    (31.25, 20.60),
                    (70.90, 20.60),
                    (70.90, 36.00),
                    (73.30, 36.00),
                ],
                "F y20.60 to TP3 via",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_CLK", B, 0.18, 31.25, 23.10, 70.90, 42.40,
        24.5, 74.0, 19.5, 46.0, 0.40, 55, "B dense U1-SIM",
    )


def route_p008(r):
    print("== P0.08 if DEC0/ENABLE opened space east of VDD2 x=52.22 ==", flush=True)
    if try_list(
        r,
        "P0.08",
        B,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (53.00, 30.00),
                    (53.00, 20.60),
                    (79.67, 20.60),
                    (79.67, 26.00),
                ],
                "B east of VDD2 then y20.60 to SW3",
            ),
            (
                [
                    (46.20, 30.00),
                    (46.20, 33.40),
                    (79.67, 33.40),
                    (79.67, 26.00),
                ],
                "B y33.4 to SW3",
            ),
        ],
    ):
        return
    if try_list(
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
                "F east of C13 / VDD2",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "P0.08", B, 0.18, 46.20, 30.00, 79.67, 26.00,
        45.0, 82.0, 20.0, 36.0, 0.35, 45, "B dense U1-SW3",
    )


def leftover_f(pairs):
    want = {
        "nRESET",
        "DEC0",
        "ENABLE",
        "VDD2",
        "VIN_FILT",
        "VIN_F",
        "SIM_CLK",
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
    fab = n1 == 0
    with open(path, "w") as f:
        f.write("# nRF9161 DEVELOPMENT BOARD — FINAL FAB RELEASE\n\n")
        if fab:
            f.write("**Status: FABRICATION-READY (connectivity gate)**\n\n")
        else:
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
        f.write(f"| Gerbers /fab | **{'generated' if fab else 'not generated'}** |\n\n")
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
        f.write("| Live snapshot after this pass | `after-pass17.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass16.kicad_pcb` |\n\n")
        f.write("## This pass (y=20.60 jogs around ENABLE / VIN_FILT / COEX2 / VIN_F)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was 90. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("The 11 extra U1 vias pass13 deleted were not re-placed. ")
        f.write("P0.06 / G7 / DNP C22–C24 skipped. SIM_RST not ripped (no CLEAR parallel). ")
        f.write("GND: refill only. P0.15 y=20.60 highway stays deleted.\n\n")
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            extra = BLOCKERS.get(name, "")
            if extra and "not closed" in status:
                f.write(f"| {name} | {status} — {note}. blocker: `{extra}` |\n")
            else:
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
    start = snap_path("pass17-start")
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

    steps = [
        ("DEC0", route_dec0, "C13 (48.72,31) to (48.65,20); east x=50.5–51.5 else west of ENABLE (48.33,23.13) then y=21.50"),
        ("ENABLE", route_enable, "C14–R1 y-jog C14.2 (48.32,22); then U1 (42.75,44) / SW1; no 40 mm"),
        ("VDD2", route_vdd2_fb3, "FB3 (68.79,19.13) to C8 (59.70,32) y=20.60 between VIN_F and COEX2"),
        ("VIN_FILT", route_vin_filt, "(55.35,13.30) to (51.90,21.90) short through y=20.60"),
        ("VIN_F", route_vin_f, "short hops to (49.30,12.60)/(71.20,19.06); no ~80 mm"),
        ("nRESET", route_nreset, "J8 (52.22,10.80) to R5; south of P0.22; west of COEX2 V"),
        ("SIM_CLK", route_sim_clk_u1, "U1 via (31.25,23.10) to B (70.90,45.50); not RF keepout"),
        ("P0.08", route_p008, "U1 (46.20,30) to SW3 if DEC0/ENABLE opened x>52.22"),
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
        if name in BLOCKERS:
            print(f"  last blocker: {BLOCKERS[name]}", flush=True)

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass17"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board)
    print(
        f"\nEND unconn={n1} shorts={counts.get('shorting_items',0)} "
        f"start={n0} fab={'yes' if n1==0 else 'no'}",
        flush=True,
    )
    print("BLOCKERS:", BLOCKERS, flush=True)
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= 90 else 1


if __name__ == "__main__":
    sys.exit(main())
