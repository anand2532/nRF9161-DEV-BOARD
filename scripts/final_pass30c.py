#!/usr/bin/env python3
"""Pass30c: netlist-synced U3 closes + Class F surgical. Keep P0.15; shorting=0."""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
sys.path.insert(0, f"{ROOT}/scripts")

from complete_route import BOARD, hypot  # noqa: E402
from final_connect import fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    Final,
    class_counts,
    dump_vios,
    try_commit,
    waypoint_route,
)

SNAP = f"{ROOT}/.mcp-backups/pass30c-connect"
os.makedirs(SNAP, exist_ok=True)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
CLOSED, DEFERRED, NOTES = [], [], []
BASELINE_CLR = 0


def check(board, r, label, last_good, ceiling, clr_ceiling=BASELINE_CLR):
    if r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    clr = counts.get("clearance", 0)
    hole = counts.get("hole_clearance", 0)
    print(
        f"DRC [{label}] unconn={n} shorts={shorts} clr={clr} hole={hole}",
        flush=True,
    )
    bad = []
    if shorts > 0:
        bad.append("shorting_items")
    if hole > 0:
        bad.append("hole_clearance")
    if clr > clr_ceiling:
        bad.append("clearance")
    if counts.get("tracks_crossing", 0) > 0:
        bad.append("tracks_crossing")
    if bad or n > ceiling:
        reason = {k: counts.get(k, 0) for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}", flush=True)
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, f"{SNAP}/after-{label}.kicad_pcb")
    return pairs, n, counts, pairs


def reload():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def try_wp(r, name, layer, w, x1, y1, x2, y2, label, max_l=120):
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name)
    if pts is None:
        print(f"  FAIL waypoint {label}: no path", flush=True)
        return False
    if L > max_l:
        print(f"  skip long waypoint {label} L={L:.1f}", flush=True)
        return False
    return try_commit(r, pts, layer, w, name, f"waypoint {label} L={L:.1f}")


def route_via_path(r, f_pts, via_xy, b_pts, net, w_f, w_b, label, pwr=False):
    """F stub -> via -> B continuation."""
    if not try_commit(r, f_pts, F, w_f, net, f"{label} F"):
        return False
    vx, vy = via_xy
    if not r.via_ok(vx, vy, net, pwr=pwr):
        print(f"  FAIL {label} via_ok {via_xy}", flush=True)
        return False
    r.add_via(vx, vy, r.code_of(net), net, pwr=pwr)
    if not try_commit(r, b_pts, B, w_b, net, f"{label} B"):
        return False
    CLOSED.append(label)
    return True


def route_u3(board, r):
    """Priority: U3.ON=COEX0 then U3.VIN=VDD_GPIO using probed corridors."""
    # COEX0: F pad3 → (33,43) via → B to spine x=38.8
    # Prefer simplest F: (27.45,46.35)-(27.45,43)-(33,43)
    coex_ok = False
    for via, f_pts, b_pts in [
        (
            (33.0, 43.0),
            [(27.45, 46.35), (27.45, 43.0), (33.0, 43.0)],
            [(33.0, 43.0), (38.8, 43.0)],
        ),
        (
            (34.0, 43.0),
            [(27.45, 46.35), (27.45, 43.0), (34.0, 43.0)],
            [(34.0, 43.0), (38.8, 43.0)],
        ),
        (
            (33.5, 43.0),
            [(27.45, 46.35), (27.45, 43.0), (33.5, 43.0)],
            [(33.5, 43.0), (38.8, 43.0)],
        ),
        (
            (28.5, 40.0),
            [(27.45, 46.35), (28.5, 46.35), (28.5, 40.0)],
            [(28.5, 40.0), (28.5, 22.0), (31.11, 22.0)],
        ),
        (
            (28.0, 40.0),
            [(27.45, 46.35), (28.0, 46.35), (28.0, 40.0)],
            [(28.0, 40.0), (28.0, 22.0), (31.11, 22.0)],
        ),
    ]:
        # fresh attempt needs clean board state — caller gates DRC per step
        if route_via_path(r, f_pts, via, b_pts, "COEX0", 0.18, 0.18, f"COEX0 U3.ON via{via}"):
            coex_ok = True
            break
        # partial copper may remain on failure — caller will restore snapshot
        return False  # signal restore needed if partial
    if not coex_ok:
        DEFERRED.append("COEX0 U3.ON")

    # VDD_GPIO: F pad1 → (28.5,40) via → B north to (40.17,19.13)
    vin_ok = False
    for via, f_pts, b_pts in [
        (
            (28.5, 40.0),
            [(27.45, 47.65), (28.5, 47.65), (28.5, 40.0)],
            [(28.5, 40.0), (28.5, 19.13), (40.17, 19.13)],
        ),
        (
            (29.0, 40.0),
            [(27.45, 47.65), (29.0, 47.65), (29.0, 40.0)],
            [(29.0, 40.0), (29.0, 19.13), (40.17, 19.13)],
        ),
        (
            (28.5, 40.0),
            [(27.45, 47.65), (28.5, 47.65), (28.5, 40.0)],
            [(28.5, 40.0), (28.5, 14.8), (48.05, 14.8)],
        ),
    ]:
        if route_via_path(
            r, f_pts, via, b_pts, "VDD_GPIO", 0.25, 0.35, f"VDD_GPIO U3.VIN via{via}", pwr=True
        ):
            vin_ok = True
            break
        return False
    if not vin_ok:
        DEFERRED.append("VDD_GPIO U3.VIN")
    return True


def route_u3_one_by_one(board, r, last, ceiling):
    """Commit COEX0 and VIN as separate DRC-gated steps."""
    global CLOSED

    # --- COEX0 ---
    for via, f_pts, b_pts in [
        ((33.0, 43.0), [(27.45, 46.35), (27.45, 43.0), (33.0, 43.0)], [(33.0, 43.0), (38.8, 43.0)]),
        ((34.0, 43.0), [(27.45, 46.35), (27.45, 43.0), (34.0, 43.0)], [(34.0, 43.0), (38.8, 43.0)]),
        ((33.5, 43.0), [(27.45, 46.35), (27.45, 43.0), (33.5, 43.0)], [(33.5, 43.0), (38.8, 43.0)]),
        ((35.0, 43.0), [(27.45, 46.35), (27.45, 43.0), (35.0, 43.0)], [(35.0, 43.0), (38.8, 43.0)]),
        ((28.5, 40.0), [(27.45, 46.35), (28.5, 46.35), (28.5, 40.0)], [(28.5, 40.0), (28.5, 22.0), (31.11, 22.0)]),
    ]:
        shutil.copy2(last, BOARD)
        board, r = reload()
        print(f"=== try COEX0 via {via} ===", flush=True)
        if not try_commit(r, f_pts, F, 0.18, "COEX0", f"COEX0 F {via}"):
            continue
        if not r.via_ok(*via, "COEX0"):
            print(f"  via_ok fail {via}", flush=True)
            continue
        r.add_via(*via, r.code_of("COEX0"), "COEX0")
        if not try_commit(r, b_pts, B, 0.18, "COEX0", f"COEX0 B {via}"):
            continue
        res = check(board, r, f"coex0-{via[0]}-{via[1]}", last, ceiling)
        if res[0] is not None:
            CLOSED.append(f"COEX0 U3.ON via{via}")
            pairs, n, counts, _ = res
            last = f"{SNAP}/after-coex0-{via[0]}-{via[1]}.kicad_pcb"
            ceiling = n
            board, r = reload()
            break
    else:
        DEFERRED.append("COEX0 U3.ON")
        shutil.copy2(last, BOARD)
        board, r = reload()
        pairs, n, counts, _ = run_drc()
        ceiling = n

    # --- VDD_GPIO ---
    for via, f_pts, b_pts in [
        ((28.5, 40.0), [(27.45, 47.65), (28.5, 47.65), (28.5, 40.0)], [(28.5, 40.0), (28.5, 19.13), (40.17, 19.13)]),
        ((29.0, 40.0), [(27.45, 47.65), (29.0, 47.65), (29.0, 40.0)], [(29.0, 40.0), (29.0, 19.13), (40.17, 19.13)]),
        ((28.5, 40.0), [(27.45, 47.65), (28.5, 47.65), (28.5, 40.0)], [(28.5, 40.0), (28.5, 14.8), (48.05, 14.8)]),
        ((29.0, 40.0), [(27.45, 47.65), (29.0, 47.65), (29.0, 40.0)], [(29.0, 40.0), (29.0, 14.8), (48.05, 14.8)]),
    ]:
        # save pre-attempt
        pre = f"{SNAP}/pre-vin-attempt.kicad_pcb"
        shutil.copy2(BOARD, pre)
        print(f"=== try VIN via {via} ===", flush=True)
        if not try_commit(r, f_pts, F, 0.25, "VDD_GPIO", f"VIN F {via}"):
            shutil.copy2(pre, BOARD)
            board, r = reload()
            continue
        if not r.via_ok(*via, "VDD_GPIO", pwr=True):
            print(f"  via_ok fail {via}", flush=True)
            shutil.copy2(pre, BOARD)
            board, r = reload()
            continue
        r.add_via(*via, r.code_of("VDD_GPIO"), "VDD_GPIO", pwr=True)
        if not try_commit(r, b_pts, B, 0.35, "VDD_GPIO", f"VIN B {via}"):
            shutil.copy2(pre, BOARD)
            board, r = reload()
            continue
        res = check(board, r, f"vin-{via[0]}-{via[1]}", last, ceiling)
        if res[0] is not None:
            CLOSED.append(f"VDD_GPIO U3.VIN via{via}")
            pairs, n, counts, _ = res
            last = f"{SNAP}/after-vin-{via[0]}-{via[1]}.kicad_pcb"
            ceiling = n
            board, r = reload()
            break
        board, r = reload()
    else:
        DEFERRED.append("VDD_GPIO U3.VIN")

    return board, r, last, ceiling


def route_class_f(board, r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)

    def attempt(net, w, layers, extra_jogs=None):
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            jogs = [
                [a, b],
                [a, (a[0], b[1]), b],
                [a, (b[0], a[1]), b],
                [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b],
                [a, (a[0], (a[1] + b[1]) / 2), (b[0], (a[1] + b[1]) / 2), b],
            ]
            if extra_jogs:
                jogs = extra_jogs(a, b) + jogs
            for layer in layers:
                for pts in jogs:
                    if try_commit(r, pts, layer, w, net, f"{net} {layer} {pts[1] if len(pts)>1 else pts}"):
                        CLOSED.append(net)
                        return True
                if try_wp(r, net, layer, w, a[0], a[1], b[0], b[1], f"{net}-{layer}"):
                    CLOSED.append(net)
                    return True
            DEFERRED.append(net)
            return False
        DEFERRED.append(f"{net} (no pair)")
        return False

    def vin_filt_jogs(a, b):
        return [
            [a, (55.35, 21.9), b],
            [a, (54.0, a[1]), (54.0, b[1]), b],
            [a, (57.5, a[1]), (57.5, b[1]), b],
            [a, (55.35, 10.5), (51.9, 10.5), (51.9, b[1]), b],
            [a, (55.35, 12.5), (50.5, 12.5), (50.5, b[1]), b],
            [a, (58.5, a[1]), (58.5, 21.9), b],
            [a, (53.0, a[1]), (53.0, 18.0), (51.9, 18.0), b],
        ]

    def vin_f_jogs(a, b):
        return [
            [a, (a[0], 19.06), b],
            [a, (a[0], 10.5), (b[0], 10.5), b],
            [a, (60.0, a[1]), (60.0, b[1]), b],
            [a, (48.0, 19.06), (71.2, 19.06)],
            [a, (49.3, 12.6), (49.3, 19.06), (71.2, 19.06)],
            [a, (a[0], 14.8), (b[0], 14.8), b],
            [a, (65.0, a[1]), (65.0, b[1]), b],
        ]

    def swdclk_jogs(a, b):
        return [
            [a, (a[0], 10.0), (b[0], 10.0), b],
            [a, (45.0, a[1]), (45.0, b[1]), b],
            [a, (51.95, 15.0), (37.75, 15.0), b],
            [a, (53.65, 4.73), (53.65, 8.0), (37.75, 8.0), b],
            [a, (51.95, 8.0), (37.75, 8.0), b],
            [a, (62.0, 4.73), (62.0, 26.75), b],
        ]

    def nreset_jogs(a, b):
        return [
            [a, (101.68, 10.8), b],
            [a, (52.22, 58.8), b],
            [a, (101.68, 26.0), (52.22, 26.0), b],
            [a, (90.0, a[1]), (90.0, b[1]), b],
            [a, (a[0], 40.0), (b[0], 40.0), b],
            [a, (70.0, a[1]), (70.0, b[1]), b],
        ]

    def p002_jogs(a, b):
        return [
            [a, (a[0], b[1]), b],
            [a, (b[0], a[1]), b],
            [a, (40.75, 19.13), b],
            [a, (91.49, 37.25), b],
            [a, (50.0, a[1]), (50.0, b[1]), b],
            [a, (60.0, a[1]), (60.0, b[1]), b],
            [a, (70.0, a[1]), (70.0, b[1]), b],
            [a, (40.75, 45.8), (30.9, 45.8)],  # toward existing P0.02 via cluster
        ]

    def p008_jogs(a, b):
        return [
            [a, (a[0], b[1]), b],
            [a, (b[0], a[1]), b],
            [a, (78.375, 30.0), (44.0, 30.0)],
            [a, (46.2, 30.0), (46.2, 26.0), (78.375, 26.0)],
            [a, (60.0, a[1]), (60.0, b[1]), b],
            [a, (70.0, a[1]), (70.0, b[1]), b],
        ]

    attempt("VIN_FILT", 0.4, (F,), vin_filt_jogs)
    attempt("VIN_F", 0.4, (F, B), vin_f_jogs)
    attempt("SWDCLK", 0.18, (F, B), swdclk_jogs)
    attempt("nRESET", 0.18, (F, B), nreset_jogs)
    attempt("P0.02", 0.18, (F, B), p002_jogs)
    attempt("P0.08", 0.18, (F, B), p008_jogs)


def route_sim_safe(board, r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)
    for net in ["SIM_CLK", "SIM_RST", "SIM_IO", "SIM_1V8"]:
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            ok = False
            for layer in (B, F):
                if try_wp(r, net, layer, 0.18, a[0], a[1], b[0], b[1], f"{net}-{layer}", max_l=100):
                    CLOSED.append(net)
                    ok = True
                    break
                for pts in [
                    [a, (a[0], b[1]), b],
                    [a, (b[0], a[1]), b],
                    [a, (50.0, a[1]), (50.0, b[1]), b],
                    [a, (64.7, a[1]), (64.7, b[1]), b],
                    [a, (70.0, a[1]), (70.0, b[1]), b],
                ]:
                    if try_commit(r, pts, layer, 0.18, net, f"{net} jog"):
                        CLOSED.append(net)
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                DEFERRED.append(net)


def main():
    NOTES.append("Netlist sync applied from reports/netlist_after_u3.xml (U3 NC/QOD unconnected nets)")
    NOTES.append("U3 signal nets already matched schematic: VIN=VDD_GPIO ON=COEX0 VOUT=GNSS_VBIAS_SRC GND")

    board, r = reload()
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START30c unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)}",
        flush=True,
    )
    last = f"{SNAP}/start.kicad_pcb"
    shutil.copy2(BOARD, last)
    ceiling = n0

    print("=== U3 priority ===", flush=True)
    board, r, last, ceiling = route_u3_one_by_one(board, r, last, ceiling)
    pairs, n0, counts0, _ = run_drc()

    print("=== Class F ===", flush=True)
    pre = f"{SNAP}/pre-class-f.kicad_pcb"
    shutil.copy2(BOARD, pre)
    route_class_f(board, r, pairs)
    res = check(board, r, "class-f", last, ceiling)
    if res[0] is None:
        board, r = reload()
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-class-f.kicad_pcb"
        ceiling = n0
        board, r = reload()

    print("=== SIM safe ===", flush=True)
    pre = f"{SNAP}/pre-sim.kicad_pcb"
    shutil.copy2(BOARD, pre)
    route_sim_safe(board, r, pairs)
    res = check(board, r, "sim", last, ceiling)
    if res[0] is None:
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        n0 = res[1]
        counts0 = res[2]

    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)

    # final DRC copy for reports
    shutil.copy2(
        os.environ.get("DRC_JSON", "/tmp/drc_final.json")
        if False
        else BOARD,
        BOARD,
    )

    summary = {
        "pass": "layout-pass30c",
        "closed": CLOSED,
        "deferred": DEFERRED,
        "notes": NOTES,
        "unconn": n0,
        "counts": dict(counts0),
        "classes": class_counts(pairs),
    }
    open(f"{ROOT}/reports/PASS30C_SUMMARY.json", "w").write(json.dumps(summary, indent=2))
    print("SUMMARY", json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
