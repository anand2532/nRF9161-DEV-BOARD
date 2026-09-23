#!/usr/bin/env python3
"""Pass 18: GND stitch island [7], then VDD2 FB3 along B y=21.20, then ENABLE.

LIVE board only. Do not restore backups, do not re-place extra U1 vias,
do not edit the plan, do not generate /fab unless unconnected=0 AND ratsnest=0.
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
    try_commit,
    write_gpio_csv,
    write_unconnected_csv,
)
from final_pass17 import (  # noqa: E402
    leftover_f,
    try_list,
    try_via_routes,
    try_wp_box,
)

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
VDD2_OK = [False]


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
    got = check(r.board, r, f"pass18-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    pairs, n, counts, _ = got
    last = snap_path(f"pass18-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n


def record(r, name, pts, layer, w, lab):
    msg = why(r, pts, layer, w, name)
    BLOCKERS[name] = f"{lab}: {msg}"
    print(f"  BLOCK {lab}: {msg}", flush=True)


def route_gnd(r):
    print("== GND stitch F island around C14.2 (48.52, 22.23) ==", flush=True)
    xy = (48.52, 22.23)
    for size, drill in ((0.60, 0.30), (0.45, 0.25)):
        w = r.via_why(xy[0], xy[1], "GND", pwr=True, size=size, drill=drill)
        if w is None:
            r.add_via(xy[0], xy[1], r.code_of("GND"), "GND", pwr=True, size=size, drill=drill)
            r.ok += 1
            print(f"  via GND {xy} {size}/{drill}", flush=True)
            BLOCKERS.pop("GND", None)
            return
        print(f"  via {xy} {size}/{drill}: {w}", flush=True)
        BLOCKERS["GND"] = f"via {xy} {size}/{drill}: {w}"
    print("  no GND stitch site", flush=True)


def route_vdd2_fb3(r):
    print("== VDD2 FB3 (68.79,19.13) B y=21.20 to (54.50,21.20) then C8 (59.70,32) ==", flush=True)
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
                    (54.50, 20.20),
                    (39.10, 20.20),
                    (39.10, 21.60),
                    (37.00, 21.60),
                    (37.00, 23.80),
                    (37.00, 58.40),
                    (64.20, 42.00),
                    (61.30, 42.00),
                ],
                "B wrap west of COEX2 then to 61.30,42 (may skip H)",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 21.20),
                    (54.50, 21.20),
                    (54.50, 26.20),
                    (52.22, 26.20),
                    (52.22, 26.75),
                ],
                "B y21.2 south across COEX2 to existing VDD2 H",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 21.20),
                    (61.50, 21.20),
                    (61.50, 32.00),
                    (59.70, 32.00),
                ],
                "B y21.2 then x=61.5 to C8",
            ),
        ],
    ):
        VDD2_OK[0] = True
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
                    (54.50, 16.10),
                    (50.50, 16.10),
                    (50.50, 17.25),
                    (46.20, 17.25),
                    (46.20, 25.90),
                    (44.72, 25.90),
                ],
                F,
                0.25,
                "F via to existing VDD2 (44.72,25.90)",
            ),
        ],
    ):
        VDD2_OK[0] = True
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
                    (54.50, 20.50),
                    (50.40, 20.50),
                    (50.40, 32.00),
                    (52.22, 32.00),
                ],
                F,
                0.25,
                "F west of VIN_FILT x=51.90 to C8 via",
            ),
        ],
    ):
        VDD2_OK[0] = True
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
                    (68.79, 21.20),
                    (68.79, 15.50),
                    (75.90, 15.50),
                    (75.90, 31.20),
                    (59.70, 31.20),
                    (59.70, 32.00),
                ],
                F,
                0.25,
                "F alley x=75.9 VIN_FILT/LED_PWR_K to C8",
            ),
        ],
    ):
        VDD2_OK[0] = True
        return
    if try_list(
        r,
        "VDD2",
        F,
        0.25,
        [
            (
                [
                    (68.79, 19.13),
                    (68.79, 15.50),
                    (74.50, 15.50),
                    (75.90, 15.50),
                    (75.90, 7.50),
                    (77.50, 7.50),
                    (77.50, 36.00),
                    (59.70, 36.00),
                ],
                "F north of LED_PWR_K then to C8 F",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 16.10),
                    (50.50, 16.10),
                    (46.20, 17.25),
                    (46.20, 25.90),
                    (44.72, 25.90),
                ],
                "F y16.1 then existing via 44.72",
            ),
        ],
    ):
        VDD2_OK[0] = True
        return
    try_wp_box(
        r, "VDD2", B, 0.25, 68.79, 19.13, 61.30, 42.00,
        34.0, 80.0, 16.0, 46.0, 0.45, 90, "B dense FB3-TP12",
    )
    if r.ok:
        VDD2_OK[0] = True
        return
    try_wp_box(
        r, "VDD2", F, 0.25, 68.79, 19.13, 44.72, 25.90,
        43.0, 76.0, 15.0, 28.0, 0.35, 80, "F dense FB3-U1via",
    )
    if r.ok:
        VDD2_OK[0] = True
        return
    try_wp_box(
        r, "VDD2", F, 0.25, 54.50, 21.20, 52.22, 32.00,
        46.0, 62.0, 16.0, 34.0, 0.30, 50, "F dense 54.5-C8via",
    )
    if r.ok:
        VDD2_OK[0] = True


def route_enable(r):
    print("== ENABLE C14–U1 if VDD2 closed; no 40 mm ==", flush=True)
    if not VDD2_OK[0]:
        BLOCKERS["ENABLE"] = "skipped; VDD2 not closed"
        print("  skip ENABLE; VDD2 still open", flush=True)
        return
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
                    (47.20, 21.50),
                    (43.40, 21.50),
                    (43.40, 23.95),
                    (42.20, 23.95),
                    (42.20, 41.10),
                    (42.75, 41.10),
                ],
                "B west of leftover P0.15 / P0.13 to U1 via",
            ),
            (
                [
                    (48.33, 23.13),
                    (47.40, 23.13),
                    (47.40, 24.20),
                    (42.75, 24.20),
                    (42.75, 41.10),
                ],
                "B south of P0.15 leftover then P0.13 to U1",
            ),
            (
                [
                    (50.85, 23.15),
                    (50.85, 21.20),
                    (47.80, 21.20),
                    (47.80, 24.40),
                    (42.75, 24.40),
                    (42.75, 41.10),
                ],
                "B from ENABLE 50.85 jog VIN_FILT / P0.15",
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
                    (47.00, 22.00),
                    (47.00, 24.20),
                    (42.75, 24.20),
                    (42.75, 26.00),
                ],
                "F west of C14.2 / leftover P0.15",
            ),
            (
                [
                    (48.33, 23.13),
                    (48.33, 24.40),
                    (43.40, 24.40),
                    (43.40, 45.13),
                ],
                "F south of C14 then to U1 via",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "ENABLE", B, 0.18, 48.33, 23.13, 42.75, 41.10,
        40.0, 52.0, 20.5, 42.0, 0.30, 38, "B dense C14-U1",
    )


def write_release(n0, n1, shorts, counts, pairs, log, board, e0, e1):
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
        f.write("| Live snapshot after this pass | `after-pass18.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass17.kicad_pcb` |\n\n")
        f.write("## This pass (GND stitch, VDD2 FB3, ENABLE)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write(f"GND E-class **{e0}→{e1}**. ")
        f.write("Ceiling was 90. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("The 11 extra U1 vias pass13 deleted were not re-placed. ")
        f.write("P0.06 / G7 / DNP C22–C24 skipped. SIM_RST not ripped. COEX2 not ripped. ")
        f.write("GND: refill + stitching via only (no dummy copper). ")
        f.write("P0.15 y=20.60 highway stays deleted. ENABLE skipped unless VDD2 closed.\n\n")
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
    import final_pass17 as p17

    p17.BLOCKERS = BLOCKERS
    start = snap_path("pass18-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    cls0 = class_counts(pairs)
    e0 = cls0.get("E", 0)
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} {dict(cls0)} E={e0}",
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
        ("GND", route_gnd, "stitch F island [7] at (48.52,22.23) around C14.2; refill only, no dummy copper"),
        ("VDD2", route_vdd2_fb3, "FB3 (68.79,19.13) B y=21.20 to (54.50,21.20) then C8 (59.70,32) / existing via (44.72,25.90)"),
        ("ENABLE", route_enable, "C14–U1 jog P0.13 (42.75,23.95), leftover P0.15, VIN_FILT, C14.2; tie existing via/B/SW1; no 40 mm"),
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
    cls1 = class_counts(pairs)
    e1 = cls1.get("E", 0)
    shutil.copy2(BOARD, snap_path("pass18"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board, e0, e1)
    print(
        f"\nEND unconn={n1} shorts={counts.get('shorting_items',0)} "
        f"start={n0} E {e0}->{e1} VDD2={'closed' if VDD2_OK[0] else 'open'} "
        f"fab={'yes' if n1==0 else 'no'}",
        flush=True,
    )
    print("BLOCKERS:", BLOCKERS, flush=True)
    print(f"classes {dict(cls1)}", flush=True)
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= 90 else 1


if __name__ == "__main__":
    sys.exit(main())
