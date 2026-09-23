#!/usr/bin/env python3
"""Pass 21: VIN add-then-delete V x=66, VIN_FILT/VIN_F hops, SIM local, nRESET, P0.08.

LIVE board only. Do not restore backups. No /fab unless unconnected=0 AND ratsnest=0.
Do not rip VDD2 / COEX2 replacement / P0.15 replacement / ENABLE.
Save only if shorts=0. Unconnected must not finish above 87.
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
import final_pass17 as p17  # noqa: E402
from final_pass17 import try_list, try_via_routes, try_wp_box  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
ADDDEL = []

VIN_WRAP = [
    (66.00, 10.00),
    (66.00, 11.50),
    (76.20, 11.50),
    (76.20, 14.70),
    (62.00, 14.70),
    (62.00, 15.40),
]
SIM_RST_WRAP = [
    (78.25, 56.60),
    (74.00, 56.60),
    (74.00, 43.80),
    (71.68, 43.80),
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
    got = check(r.board, r, f"pass21-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass21-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def leftover_f(pairs):
    want = {
        "nRESET",
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


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)


def delete_vin_v66(board, r):
    """Delete only VIN F vertical at x=66 connecting y=10 to y=20.70."""
    hits = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "VIN" or tr.GetLayer() != F:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(x1 - x2) > 0.30:
            continue
        if abs((x1 + x2) / 2 - 66.00) > 0.30:
            continue
        ya, yb = min(y1, y2), max(y1, y2)
        if yb < 9.50 or ya > 21.20:
            continue
        if yb - ya < 5.0:
            continue
        hits.append((tr, x1, y1, x2, y2))
    print(f"== DELETE VIN F V x=66 hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2))
        board.Remove(tr)
    r.collect()
    return specs


def delete_sim_rst_v78(board, r):
    """Delete only SIM_RST B vertical at x=78.25 y≈43.80–56.60."""
    hits = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "SIM_RST" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(x1 - x2) > 0.30:
            continue
        if abs((x1 + x2) / 2 - 78.25) > 0.30:
            continue
        ya, yb = min(y1, y2), max(y1, y2)
        if yb < 43.0 or ya > 57.2:
            continue
        if yb - ya < 8.0:
            continue
        hits.append((tr, x1, y1, x2, y2))
    print(f"== DELETE SIM_RST B V x=78.25 hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2))
        board.Remove(tr)
    r.collect()
    return specs


def route_vin_add(r):
    print("== ADD VIN replacement (not V x=66 y=10–20.70) ==", flush=True)
    if try_commit(r, VIN_WRAP, F, 0.40, "VIN", "F wrap y=11.50/14.70 x=76.20 to x=62"):
        BLOCKERS.pop("VIN_ADD", None)
        return
    alts = [
        [(66.00, 10.00), (66.00, 11.50), (76.20, 11.50), (76.20, 14.50), (62.00, 14.50), (62.00, 15.40)],
        [(66.00, 10.00), (66.00, 11.50), (76.20, 11.50), (76.20, 13.20), (62.00, 13.20), (62.00, 15.40)],
        [(66.00, 10.00), (66.00, 11.50), (75.00, 11.50), (75.00, 14.50), (62.00, 14.50), (62.00, 15.40)],
    ]
    for pts in alts:
        if try_commit(r, pts, F, 0.40, "VIN", f"F wrap alt {pts[2]}"):
            BLOCKERS.pop("VIN_ADD", None)
            return
    BLOCKERS["VIN_ADD"] = why(r, VIN_WRAP, F, 0.40, "VIN")


def route_vin_filt(r):
    print("== VIN_FILT JP1 (55.35,13.30) → FB4 (74.00,16.94) through freed x=66 ==", flush=True)
    if try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            (
                [(55.35, 13.30), (55.35, 13.80), (74.00, 13.80), (74.00, 16.94)],
                "F y13.80 through freed VIN V x=66 to FB4",
            ),
            (
                [(55.35, 13.30), (55.35, 13.50), (74.00, 13.50), (74.00, 16.94)],
                "F y13.50 to FB4",
            ),
            (
                [(55.35, 13.30), (55.35, 12.80), (74.00, 12.80), (74.00, 16.94)],
                "F y12.80 to FB4",
            ),
            (
                [(55.35, 13.30), (66.00, 13.30), (66.00, 21.90), (51.90, 21.90)],
                "F freed x=66 south to west island",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_FILT", F, 0.25, 55.35, 13.30, 74.00, 16.94,
        54.0, 77.0, 11.0, 22.0, 0.30, 40, "F dense JP1-FB4",
    )


def route_vin_f(r):
    print("== VIN_F short hop (49.30,12.60) → (71.58,17.66); no 80 mm bus ==", flush=True)
    if try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            (
                [(49.30, 12.60), (71.58, 12.60), (71.58, 17.66)],
                "F y12.60 through freed x=66 to FB4 via",
            ),
            (
                [(49.30, 12.60), (71.20, 12.60), (71.20, 19.06)],
                "F y12.60 to island via 71.20",
            ),
            (
                [(48.00, 12.60), (48.00, 12.90), (71.58, 12.90), (71.58, 17.66)],
                "F y12.90 from F1.2",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "VIN_F", F, 0.25, 49.30, 12.60, 71.58, 17.66,
        47.0, 74.0, 11.0, 20.0, 0.30, 40, "F dense F1-FB4",
    )


def route_sim_rst_add(r):
    print("== ADD SIM_RST replacement V x=74 (not x=78.25) ==", flush=True)
    if try_commit(r, SIM_RST_WRAP, B, 0.18, "SIM_RST", "B wrap x=74 y=56.60–43.80"):
        BLOCKERS.pop("SIM_RST_ADD", None)
        return
    BLOCKERS["SIM_RST_ADD"] = why(r, SIM_RST_WRAP, B, 0.18, "SIM_RST")


def route_sim_clk_c(r):
    print("== SIM_CLK_C (76.62,56.05) → J7 (99.19,46.67); names distinct ==", flush=True)
    if try_list(
        r,
        "SIM_CLK_C",
        B,
        0.18,
        [
            (
                [(76.62, 56.05), (76.62, 51.00), (99.19, 51.00), (99.19, 46.67)],
                "B y51 through freed x=78.25",
            ),
            (
                [(76.62, 56.05), (76.62, 52.50), (99.19, 52.50), (99.19, 46.67)],
                "B y52.50",
            ),
            (
                [(76.62, 56.05), (82.50, 56.05), (82.50, 46.67), (99.19, 46.67)],
                "B y56.05 then x=82.5",
            ),
            (
                [(76.62, 56.05), (76.62, 47.50), (99.19, 47.50), (99.19, 46.67)],
                "B y47.50",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "SIM_CLK_C",
        F,
        0.18,
        [
            (
                [(77.75, 54.70), (76.00, 54.70), (76.00, 50.80), (98.54, 50.80), (98.54, 45.54)],
                "F west then y50.80",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_CLK_C", B, 0.18, 76.62, 56.05, 99.19, 46.67,
        73.0, 104.0, 43.0, 58.0, 0.35, 45, "B dense U4-J7",
    )


def route_sim_io_c(r):
    print("== SIM_IO_C U4.1 (77.35,55.40) → (98.54,50.01); names distinct ==", flush=True)
    print("via 75.80,55.40", r.via_why(75.80, 55.40, "SIM_IO_C"))
    if try_via_routes(
        r,
        "SIM_IO_C",
        False,
        [(75.80, 55.40)],
        [
            ([(77.35, 55.40), (75.80, 55.40)], F, 0.18, "F U4.1 to via west of U4.2"),
            (
                [(75.80, 55.40), (75.80, 51.20), (98.54, 51.20), (98.54, 50.01)],
                B,
                0.18,
                "B y51.20 to J7 via",
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
                [(77.35, 55.40), (77.35, 51.20), (98.54, 51.20), (98.54, 50.01)],
                "B y51.20 from U4.1 (needs via)",
            ),
            (
                [(77.35, 55.40), (82.20, 55.40), (82.20, 50.01), (98.54, 50.01)],
                "B x=82.2 to existing via",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_IO_C", B, 0.18, 77.35, 55.40, 98.54, 50.01,
        73.0, 104.0, 44.0, 58.0, 0.35, 45, "B dense U4-J7 IO",
    )


def route_nreset(r):
    print("== nRESET J8/C39 → R5; jog ENABLE via 56.50,20.30 / VDD2 69.44,18 ==", flush=True)
    if try_list(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [
                    (45.68, 19.80),
                    (45.68, 18.90),
                    (55.40, 18.90),
                    (55.40, 17.50),
                    (70.80, 17.50),
                    (70.80, 19.40),
                    (97.00, 19.40),
                    (97.00, 26.00),
                    (101.68, 26.00),
                ],
                "B jog ENABLE via then VDD2 via 69.44",
            ),
            (
                [
                    (45.68, 19.80),
                    (58.80, 19.80),
                    (58.80, 22.80),
                    (68.20, 22.80),
                    (68.20, 23.40),
                    (97.00, 23.40),
                    (97.00, 26.00),
                    (101.68, 26.00),
                ],
                "B y22.80–23.40 east of ENABLE x=56.50 / VDD2 stub",
            ),
            (
                [
                    (38.25, 21.80),
                    (38.25, 22.80),
                    (53.80, 22.80),
                    (53.80, 23.50),
                    (97.00, 23.50),
                    (97.00, 26.00),
                    (101.68, 26.00),
                ],
                "B from U1 nRESET via y=22.80",
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
                [(53.65, 7.27), (53.65, 4.20), (101.68, 4.20), (101.68, 26.00)],
                "F y4.20 south of P0.22 / J8",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "nRESET", B, 0.18, 45.68, 19.80, 101.68, 26.00,
        37.0, 108.0, 16.5, 28.0, 0.40, 80, "B dense C39-R5",
    )


def route_sim_clk(r):
    print("== SIM_CLK courtyard via (31.25,23.10) east private column ==", flush=True)
    if try_list(
        r,
        "SIM_CLK",
        B,
        0.18,
        [
            (
                [
                    (31.25, 23.10),
                    (31.25, 24.40),
                    (32.40, 24.40),
                    (32.40, 25.60),
                    (36.90, 25.60),
                    (36.90, 22.00),
                    (39.80, 22.00),
                    (39.80, 21.20),
                    (70.90, 21.20),
                    (70.90, 42.40),
                ],
                "B jog P0.25 33.25 then P0.15 x=36.5",
            ),
            (
                [
                    (31.25, 23.10),
                    (32.40, 23.10),
                    (32.40, 21.80),
                    (36.90, 21.80),
                    (36.90, 21.20),
                    (70.90, 21.20),
                    (70.90, 42.40),
                ],
                "B y21.80 jog P0.25",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_CLK", B, 0.18, 31.25, 23.10, 70.90, 42.40,
        24.5, 74.0, 18.5, 46.0, 0.40, 55, "B dense U1-SIM",
    )


def route_p008(r):
    print("== P0.08 via east of VDD2; F-jump ENABLE B x=62.50; jog COEX2 y=33.20 ==", flush=True)
    if try_via_routes(
        r,
        "P0.08",
        False,
        [(50.50, 30.90), (61.00, 34.20), (64.20, 34.20)],
        [
            (
                [(46.20, 30.00), (46.20, 30.90), (50.50, 30.90)],
                F,
                0.18,
                "F jog north of C13.1 / south of DEC0",
            ),
            (
                [(50.50, 30.90), (50.50, 34.20), (61.00, 34.20)],
                B,
                0.18,
                "B south of COEX2 H y=33.20 to x=61",
            ),
            (
                [(61.00, 34.20), (64.20, 34.20)],
                F,
                0.18,
                "F-jump ENABLE B V x=62.50",
            ),
            (
                [(64.20, 34.20), (75.50, 34.20), (75.50, 26.00), (79.67, 26.00)],
                B,
                0.18,
                "B east of ENABLE V to SW3",
            ),
        ],
    ):
        return
    if try_via_routes(
        r,
        "P0.08",
        False,
        [(56.80, 30.00), (64.20, 30.00)],
        [
            (
                [(46.20, 30.00), (46.20, 30.90), (56.80, 30.90), (56.80, 30.00)],
                F,
                0.18,
                "F to via 56.80,30 east of VDD2 V",
            ),
            (
                [(56.80, 30.00), (61.80, 30.00), (61.80, 30.90), (64.20, 30.90), (64.20, 30.00)],
                F,
                0.18,
                "F-jump ENABLE V at y=30.90",
            ),
            (
                [(64.20, 30.00), (75.50, 30.00), (75.50, 26.00), (79.67, 26.00)],
                B,
                0.18,
                "B y=30 east of ENABLE to SW3",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "P0.08", B, 0.18, 46.20, 30.00, 79.67, 26.00,
        38.0, 82.0, 23.0, 36.0, 0.35, 50, "B dense U1-SW3",
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
        f.write("| Live snapshot after this pass | `after-pass21.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass20.kicad_pcb` |\n\n")
        f.write("## This pass (VIN add-then-delete, VIN_FILT/VIN_F, SIM, nRESET, P0.08)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was 87. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("VDD2 / COEX2 replacement / P0.15 replacement / ENABLE not ripped. ")
        f.write("No extra GPIO fanout. No DNP 50Ω stubs. G7 skipped. ")
        f.write("SIM_* names not merged.\n\n")
        if ADDDEL:
            f.write("**Add-then-delete:** " + "; ".join(ADDDEL) + "\n\n")
        else:
            f.write("**Add-then-delete:** none kept\n\n")
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
    start = snap_path("pass21-start")
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
    if n0 > 87:
        print(f"start unconn {n0} > 87; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs

    print("\n#### VIN_ADD", flush=True)
    before = ceiling
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "VIN_ADD", route_vin_add, last, ceiling
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    st, note = status_of(
        "VIN", ok, before, ceiling, last_pairs,
        "replacement wrap y=11.50/14.70 x=76.20 joining VIN at (62,15.40)",
    )
    log.append(("VIN_ADD", st if ok else "not added", note))
    print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)

    if ok:
        print("\n#### VIN_RIP", flush=True)
        pre_rip = last
        specs = delete_vin_v66(board, r)
        ripped = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in specs) or "none"
        got = check(board, r, "pass21-VIN_RIP", pre_rip, ceiling, force_fill=True)
        if got[0] is None:
            ADDDEL.append("VIN wrap added but V x=66 rip reverted")
            log.append(("VIN_RIP", "reverted", ripped))
            board, r = reload()
            last = pre_rip
        else:
            ceiling = got[1]
            last = snap_path("pass21-VIN_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"VIN yes; removed F V x=66 {ripped}")
            log.append(("VIN_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()

            print("\n#### VIN_FILT", flush=True)
            before = ceiling
            board, r, last, ok, ceiling, new_pairs = apply_net(
                board, r, "VIN_FILT", route_vin_filt, last, ceiling
            )
            if new_pairs is not None:
                last_pairs = new_pairs
            st, note = status_of(
                "VIN_FILT", ok, before, ceiling, last_pairs,
                "JP1 (55.35,13.30) y=13.80 through freed x=66 to FB4 (74.00,16.94)",
            )
            log.append(("VIN_FILT", st, note))
            print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)

            print("\n#### VIN_F", flush=True)
            before = ceiling
            board, r, last, ok, ceiling, new_pairs = apply_net(
                board, r, "VIN_F", route_vin_f, last, ceiling
            )
            if new_pairs is not None:
                last_pairs = new_pairs
            st, note = status_of(
                "VIN_F", ok, before, ceiling, last_pairs,
                "short hop (49.30,12.60) y=12.60 to via (71.58,17.66); not merged with VIN_FILT",
            )
            log.append(("VIN_F", st, note))
            print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)
    else:
        log.append(("VIN_RIP", "skipped", "no replacement"))
        log.append(("VIN_FILT", "not closed", "VIN V x=66 still present"))
        log.append(("VIN_F", "not closed", "VIN V x=66 still present"))

    print("\n#### SIM_RST_ADD", flush=True)
    before = ceiling
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "SIM_RST_ADD", route_sim_rst_add, last, ceiling
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    st, note = status_of(
        "SIM_RST", ok, before, ceiling, last_pairs,
        "B wrap x=74 instead of V x=78.25",
    )
    log.append(("SIM_RST_ADD", st if ok else "not added", note))
    print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)

    if ok:
        print("\n#### SIM_RST_RIP", flush=True)
        pre_rip = last
        specs = delete_sim_rst_v78(board, r)
        ripped = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in specs) or "none"
        got = check(board, r, "pass21-SIM_RST_RIP", pre_rip, ceiling, force_fill=True)
        if got[0] is None:
            ADDDEL.append("SIM_RST wrap added but V x=78.25 rip reverted")
            log.append(("SIM_RST_RIP", "reverted", ripped))
            board, r = reload()
            last = pre_rip
        else:
            ceiling = got[1]
            last = snap_path("pass21-SIM_RST_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"SIM_RST yes; removed B V x=78.25 {ripped}")
            log.append(("SIM_RST_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()
    else:
        log.append(("SIM_RST_RIP", "skipped", "no replacement"))

    steps = [
        ("SIM_CLK_C", route_sim_clk_c,
         "U4.2 island (76.62,56.05) to J7 (99.19,46.67); not merged with SIM_CLK"),
        ("SIM_IO_C", route_sim_io_c,
         "U4.1 (77.35,55.40) to (98.54,50.01); not merged with SIM_IO"),
        ("nRESET", route_nreset,
         "J8/C39 to R5 jogging ENABLE via (56.50,20.30), VDD2 (69.44,18), VDD1 (49.44,16.87)"),
        ("SIM_CLK", route_sim_clk,
         "courtyard via (31.25,23.10) east to B (70.90,42.40); not RF"),
        ("P0.08", route_p008,
         "via east of VDD2; F-jump ENABLE x=62.50; jog COEX2 H y=33.20 to SW3"),
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
    shutil.copy2(BOARD, snap_path("pass21"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, shorts, counts, pairs, log, board)
    print(
        f"\nEND unconn={n1} shorts={shorts} start={n0} fab={'yes' if n1==0 else 'no'}",
        flush=True,
    )
    print("ADDDEL:", ADDDEL, flush=True)
    print("BLOCKERS:", BLOCKERS, flush=True)
    print("classes", dict(class_counts(pairs)), flush=True)
    for line in leftover_f(pairs):
        print(" leftover", line, flush=True)
    return 0 if shorts == 0 and n1 <= 87 else 1


if __name__ == "__main__":
    sys.exit(main())
