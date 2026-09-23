#!/usr/bin/env python3
"""Pass 20: ENABLE dual-via jog around VDD2 V x=54.50, then remaining F-nets.

LIVE board only. Do not restore backups. No /fab unless unconnected=0 AND ratsnest=0.
Do not rip VDD2 / COEX2 replacement / P0.15 replacement.
Save only if shorts=0. Unconnected must not finish above 88.
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
    try_commit,
    write_gpio_csv,
    write_unconnected_csv,
)
import final_pass17 as p17  # noqa: E402
from final_pass17 import try_list, try_via_routes, try_wp_box  # noqa: E402

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS

# Dual-via ENABLE: B north of VDD2 stub y=21.20, F-jump the stub at x=56.50,
# B-jump VIN_FILT F H y=24.54, then B east of VDD2 V x=54.50 to F highway y=40.95.
ENABLE_VIAS = [(56.50, 20.30), (56.50, 23.80), (62.50, 40.95)]
ENABLE_ROUTES = [
    ([(50.85, 23.15), (50.85, 20.30), (56.50, 20.30)], B, 0.18, "B north of VDD2 stub y=20.30"),
    ([(56.50, 20.30), (56.50, 23.80)], F, 0.18, "F-jump VDD2 H y=21.20 at x=56.50"),
    (
        [(56.50, 23.80), (56.50, 25.20), (62.50, 25.20), (62.50, 40.95)],
        B,
        0.18,
        "B east of VDD2 V x=54.50 to F highway",
    ),
]


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
    got = check(r.board, r, f"pass20-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass20-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def leftover_f(pairs):
    want = {
        "nRESET",
        "ENABLE",
        "VIN_FILT",
        "VIN_F",
        "SIM_CLK",
        "SIM_CLK_C",
        "SIM_IO_C",
        "P0.08",
        "SIM_IO",
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


def net_open(pairs, name):
    return [p for p in (pairs or []) if p["net"] == name]


def status_of(name, ok, before, after, pairs, note):
    still = leftover_f(pairs) if pairs else []
    open_now = [ln for ln in still if ln.startswith(name + " ")]
    if not ok:
        extra = BLOCKERS.get(name, "")
        st = "not closed (DRC revert or blocked)"
        if extra:
            note = f"{note}. blocker: `{extra}`"
        return st, note
    if not open_now and after < before:
        return f"closed ({before}→{after})", note
    if not open_now:
        return f"closed (pair gone, unconn {before}→{after})", note
    if after < before:
        return f"partial ({before}→{after})", note + " | still: " + "; ".join(open_now)
    st = "not closed (no DRC-clean copper)"
    extra = BLOCKERS.get(name, "")
    if extra:
        note = f"{note}. blocker: `{extra}`"
    else:
        note = note + " | still: " + "; ".join(open_now)
    return st, note


def route_enable(r):
    print("== ENABLE C14–U1 dual-via around VDD2 V x=54.50; no y=24.90 ==", flush=True)
    # C14.1–R1.2 already B-tied at y=21.68. Optional F ±0.7 mm around C14.2 GND.
    try_list(
        r,
        "ENABLE",
        F,
        0.18,
        [
            (
                [(47.68, 22.00), (47.68, 21.30), (50.00, 21.30), (50.00, 21.68)],
                "F C14-R1 y-0.70",
            ),
            (
                [(47.68, 22.00), (47.68, 22.70), (50.00, 22.70), (50.00, 21.68)],
                "F C14-R1 y+0.70",
            ),
        ],
    )
    if try_via_routes(r, "ENABLE", False, ENABLE_VIAS, ENABLE_ROUTES):
        return
    # Alt x=56.80 (more margin from VDD2 V, still west of TP20 58.00).
    alt_vias = [(56.80, 20.30), (56.80, 23.80), (62.50, 40.95)]
    alt_routes = [
        ([(50.85, 23.15), (50.85, 20.30), (56.80, 20.30)], B, 0.18, "B y=20.30 to x=56.80"),
        ([(56.80, 20.30), (56.80, 23.80)], F, 0.18, "F-jump VDD2 at x=56.80"),
        (
            [(56.80, 23.80), (56.80, 25.20), (62.50, 25.20), (62.50, 40.95)],
            B,
            0.18,
            "B x=56.80 to highway",
        ),
    ]
    if try_via_routes(r, "ENABLE", False, alt_vias, alt_routes):
        return
    BLOCKERS["ENABLE"] = (
        "dual-via x=56.50/56.80 failed; do not use y=24.90 into VDD2 V (54.50,21.20)-(54.50,32.00)"
    )


def route_vin_filt(r):
    print("== VIN_FILT JP1 (55.35,13.30) → west island (51.90,21.90) or east FB4 ==", flush=True)
    if try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            (
                [(55.35, 13.30), (55.35, 13.80), (64.20, 13.80), (64.20, 16.94), (74.00, 16.94)],
                "F east of VIN x=62 to FB4 (74.00,16.94)",
            ),
            (
                [(55.35, 13.30), (63.20, 13.30), (63.20, 16.94), (74.00, 16.94)],
                "F y13.30 then x63.2 to FB4",
            ),
            (
                [(55.35, 13.30), (55.35, 11.20), (64.20, 11.20), (64.20, 16.94), (74.00, 16.94)],
                "F y11.20 north of VIN to FB4",
            ),
            (
                [(55.35, 13.30), (55.35, 13.80), (64.20, 13.80), (64.20, 20.80), (51.90, 20.80), (51.90, 21.90)],
                "F east of VIN then y20.80 to west island",
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
                [(55.35, 13.30), (55.35, 13.00), (64.20, 13.00), (64.20, 16.94), (74.00, 16.94)],
                "B east of VIN to FB4",
            ),
            (
                [(55.35, 13.30), (47.80, 13.30), (47.80, 20.80), (51.90, 20.80), (51.90, 21.90)],
                "B west of VIN then to west island",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_FILT", F, 0.25, 55.35, 13.30, 74.00, 16.94,
        54.0, 76.0, 10.0, 22.0, 0.30, 40, "F dense JP1-FB4",
    )


def route_vin_f(r):
    print("== VIN_F short hops (49.30,12.60) → (71.20,19.06); no long bus ==", flush=True)
    if try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            (
                [(49.30, 12.60), (49.30, 12.00), (64.50, 12.00), (64.50, 19.06), (71.20, 19.06)],
                "F y12.00 east of VIN x=62",
            ),
            (
                [(49.30, 12.60), (47.80, 12.60), (47.80, 11.20), (71.58, 11.20), (71.58, 17.66)],
                "F y11.20 to FB4 via",
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
                [(49.30, 12.60), (49.30, 11.20), (71.58, 11.20), (71.58, 17.66)],
                "B y11.20 to FB4 via",
            ),
            (
                [(49.30, 12.60), (47.80, 12.60), (47.80, 13.00), (71.20, 13.00), (71.20, 19.06)],
                "B y13.00 F1 to island",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_F", F, 0.25, 49.30, 12.60, 71.58, 17.66,
        47.0, 76.0, 10.5, 20.5, 0.30, 40, "F dense F1-FB4",
    )


def route_nreset(r):
    print("== nRESET J8/C39 island → R5 (101.68,26.00) ==", flush=True)
    if try_list(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [(45.68, 19.80), (45.68, 18.20), (99.20, 18.20), (99.20, 26.00), (101.68, 26.00)],
                "B y18.2 C39 to R5",
            ),
            (
                [(45.68, 19.80), (38.25, 19.80), (38.25, 18.20), (104.40, 18.20), (104.40, 27.13), (102.33, 27.13)],
                "B y18.2 west then to R5 via",
            ),
            (
                [(52.22, 10.80), (52.22, 9.40), (101.68, 9.40), (101.68, 26.00)],
                "B y9.40 J8 to R5",
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
                [(52.22, 10.80), (53.65, 10.80), (53.65, 5.20), (101.68, 5.20), (101.68, 26.00)],
                "F south of P0.22 to R5",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "nRESET", B, 0.18, 45.68, 19.80, 101.68, 26.00,
        38.0, 108.0, 8.0, 28.0, 0.40, 80, "B dense C39-R5",
    )


def route_sim_clk(r):
    print("== SIM_CLK courtyard via (31.25,23.10) east, not RF ==", flush=True)
    if try_list(
        r,
        "SIM_CLK",
        B,
        0.18,
        [
            (
                [(31.25, 23.10), (31.25, 19.20), (70.90, 19.20), (70.90, 42.40)],
                "B y19.20 east of courtyard via",
            ),
            (
                [(31.25, 23.10), (32.40, 23.10), (32.40, 19.20), (70.90, 19.20), (70.90, 42.40)],
                "B jog x32.4 y19.20",
            ),
            (
                [(31.25, 23.10), (32.40, 23.10), (32.40, 22.40), (70.90, 22.40), (70.90, 42.40)],
                "B y22.40 (south of ENABLE y=20.30 / north of COEX2 remnant)",
            ),
            (
                [(31.25, 23.10), (25.10, 23.10), (25.10, 42.40), (70.90, 42.40)],
                "B x=25.10 east of RF_BOX",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_CLK", B, 0.18, 31.25, 23.10, 70.90, 42.40,
        24.5, 74.0, 18.5, 46.0, 0.40, 55, "B dense U1-SIM",
    )


def route_sim_clk_c(r):
    print("== SIM_CLK_C (77.75,55.40) → J7 (98.54,45.54); no name merge ==", flush=True)
    if try_list(
        r,
        "SIM_CLK_C",
        F,
        0.18,
        [
            (
                [(77.75, 55.40), (77.75, 45.54), (98.54, 45.54)],
                "F west then y45.54 to J7.C3",
            ),
            (
                [(77.75, 55.40), (98.54, 55.40), (98.54, 45.54)],
                "F y55.40 then south to J7",
            ),
            (
                [(76.62, 56.05), (76.62, 46.67), (99.19, 46.67)],
                "F via-to-via y46.67",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "SIM_CLK_C",
        B,
        0.18,
        [
            (
                [(76.62, 56.05), (76.62, 46.67), (99.19, 46.67)],
                "B via-to-via",
            ),
            (
                [(77.75, 55.40), (77.75, 45.54), (98.54, 45.54)],
                "B west then y45.54",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_CLK_C", F, 0.18, 77.75, 55.40, 98.54, 45.54,
        74.0, 104.0, 42.0, 60.0, 0.35, 40, "F dense U4-J7",
    )


def route_sim_io_c(r):
    print("== SIM_IO_C U4.1 (77.35,55.40) → (98.54,48.71); no name merge ==", flush=True)
    if try_list(
        r,
        "SIM_IO_C",
        F,
        0.18,
        [
            (
                [(77.35, 55.40), (77.35, 48.71), (98.54, 48.71)],
                "F west then y48.71",
            ),
            (
                [(77.35, 55.40), (98.54, 55.40), (98.54, 50.01)],
                "F y55.40 then to existing via",
            ),
            (
                [(77.35, 55.40), (77.35, 50.01), (98.54, 50.01)],
                "F y50.01 to existing via",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "SIM_IO_C",
        B,
        0.18,
        [
            (
                [(77.35, 55.40), (77.35, 50.01), (98.54, 50.01)],
                "B y50.01 to existing via",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_IO_C", F, 0.18, 77.35, 55.40, 98.54, 48.71,
        74.0, 104.0, 44.0, 60.0, 0.35, 40, "F dense U4-J7 IO",
    )


def route_p008(r):
    print("== P0.08 east of VDD2 x=52.22 / around V x=54.50 to SW3 ==", flush=True)
    if try_list(
        r,
        "P0.08",
        B,
        0.18,
        [
            (
                [(46.20, 30.00), (46.20, 34.20), (79.67, 34.20), (79.67, 26.00)],
                "B y34.20 south of COEX2 H y=33.20",
            ),
            (
                [(46.20, 30.00), (53.00, 30.00), (53.00, 34.20), (79.67, 34.20), (79.67, 26.00)],
                "B east to x53 then y34.20",
            ),
            (
                [(46.20, 30.00), (46.20, 20.00), (79.67, 20.00), (79.67, 26.00)],
                "B y20.00 north of VDD2 stub / ENABLE",
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
                [(46.20, 30.00), (53.00, 30.00), (53.00, 24.00), (78.38, 24.00)],
                "F east of U1 then y24 to SW3",
            ),
            (
                [(44.00, 30.00), (44.00, 34.20), (78.38, 34.20), (78.38, 24.00)],
                "F y34.20 to SW3",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "P0.08", B, 0.18, 46.20, 30.00, 79.67, 26.00,
        45.0, 82.0, 19.0, 36.0, 0.35, 45, "B dense U1-SW3",
    )


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
        f.write("| Live snapshot after this pass | `after-pass20.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass19.kicad_pcb` |\n\n")
        f.write("## This pass (ENABLE dual-via around VDD2 V x=54.50, then F-nets)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was 88. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("VDD2 / COEX2 replacement / P0.15 replacement not ripped. ")
        f.write("No extra GPIO fanout. No DNP 50Ω stubs. G7 skipped. ")
        f.write("SIM_RST not ripped. ENABLE did not use y=24.90 into VDD2 V x=54.50.\n\n")
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
    start = snap_path("pass20-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    cls0 = class_counts(pairs)
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} {dict(cls0)}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        print("start already has shorts; abort")
        return 2
    if n0 > 88:
        print(f"start unconn {n0} > 88; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs

    steps = [
        ("ENABLE", route_enable,
         "C14 via (50.85,23.15) B y=20.30 F-jump VDD2 at x=56.50 then B to F highway (62.50,40.95)"),
        ("VIN_FILT", route_vin_filt,
         "JP1 (55.35,13.30) to west island (51.90,21.90) / FB4 (74.00,16.94); east of VIN x=62"),
        ("VIN_F", route_vin_f,
         "short hops (49.30,12.60) to (71.20,19.06) / FB4 via (71.58,17.66)"),
        ("nRESET", route_nreset,
         "J8 (52.22,10.80) / C39 (45.68,19.80) to R5 (101.68,26.00)"),
        ("SIM_CLK", route_sim_clk,
         "courtyard via (31.25,23.10) east to B (70.90,42.40); not RF keepout"),
        ("SIM_CLK_C", route_sim_clk_c,
         "(77.75,55.40) to J7 (98.54,45.54); names not merged; SIM_RST not ripped"),
        ("SIM_IO_C", route_sim_io_c,
         "U4.1 (77.35,55.40) to (98.54,48.71); names not merged"),
        ("P0.08", route_p008,
         "U1 via (46.20,30) east of VDD2 x=52.22 / around V x=54.50 to SW3 (79.67,26)"),
    ]
    for name, fn, note in steps:
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok, ceiling, new_pairs = apply_net(board, r, name, fn, last, ceiling)
        if new_pairs is not None:
            last_pairs = new_pairs
        st, note2 = status_of(name, ok, before, ceiling, last_pairs, note)
        log.append((name, st, note2))
        print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)
        if name in BLOCKERS:
            print(f"  last blocker: {BLOCKERS[name]}", flush=True)

    shorts = 0
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    if shorts:
        print(f"END shorts={shorts}; restoring last good {last}")
        shutil.copy2(last, BOARD)
        board, r = reload()
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        pairs, n1, counts, _ = run_drc()
        shorts = counts.get("shorting_items", 0)
    shutil.copy2(BOARD, snap_path("pass20"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, shorts, counts, pairs, log, board)
    print(
        f"\nEND unconn={n1} shorts={shorts} start={n0} fab={'yes' if n1==0 else 'no'}",
        flush=True,
    )
    print("BLOCKERS:", BLOCKERS, flush=True)
    print("classes", dict(class_counts(pairs)), flush=True)
    for line in leftover_f(pairs):
        print(" leftover", line, flush=True)
    return 0 if shorts == 0 and n1 <= 88 else 1


if __name__ == "__main__":
    sys.exit(main())
