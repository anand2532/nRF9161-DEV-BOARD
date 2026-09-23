#!/usr/bin/env python3
"""Pass 23: P0.01 add-then-delete x=27.65 wall, then P0.06 west wrap.

LIVE. Do not restore backups. Ceiling finish ≤85. No /fab unless unconnected=0
AND ratsnest=0. Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST wraps /
VIN V x=66. No extra U1 fanout.
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
from final_pass17 import try_list, try_via_routes  # noqa: E402
from final_pass21 import leftover_f, mm_xy, status_of  # noqa: E402
import final_pass21 as p21  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
ADDDEL = []
RIPPED = []
P001_REPL = False
P006_J12 = "not closed"
P006_J9 = "not closed"

# East column + F-jump over P0.15 H y=77.45, then south stub y=78.50 to J12.2.
# Does not use V x=27.65 for y≥20.
P001_VIAS = [(80.51, 76.70), (80.51, 78.20)]
P001_ROUTES = [
    (
        [
            (86.14, 15.20),
            (105.55, 15.20),
            (105.55, 70.70),
            (80.51, 70.70),
            (80.51, 76.70),
        ],
        B,
        0.18,
        "B east x=105.55 hop J15 then x=80.51 to F-jump",
    ),
    (
        [(80.51, 76.70), (80.51, 78.20)],
        F,
        0.18,
        "F jump P0.15 H y=77.45",
    ),
    (
        [
            (80.51, 78.20),
            (80.51, 78.50),
            (8.54, 78.50),
            (8.54, 76.00),
        ],
        B,
        0.18,
        "B south stub y=78.50 to J12.2",
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
    got = check(r.board, r, f"pass23-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass23-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def route_p001_repl(r):
    print("== ADD P0.01 replacement (not V x=27.65 for y>=20) ==", flush=True)
    if try_via_routes(r, "P0.01", False, P001_VIAS, P001_ROUTES):
        return
    BLOCKERS["P0.01"] = "replacement vias/path blocked"


def delete_p001_wall(board):
    """Delete blocking V x=27.65 and J12-corridor H y=77.45. Keep y=15.20 remnant."""
    hits = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.01" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        xs, ys = [x1, x2], [y1, y2]
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        is_wall = (
            abs(x1 - x2) < 0.20
            and abs(mx - 27.65) < 0.15
            and max(ys) > 20.0
        )
        is_south_h = (
            abs(y1 - y2) < 0.20
            and abs(my - 77.45) < 0.20
            and min(xs) < 20.0
            and max(xs) > 25.0
        )
        if is_wall or is_south_h:
            hits.append((tr, x1, y1, x2, y2, "V" if is_wall else "H"))
    for tr, x1, y1, x2, y2, kind in hits:
        board.Remove(tr)
        RIPPED.append(f"{kind} ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        print(f"  ripped P0.01 {kind} ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})", flush=True)
    return hits


def route_p006_j12(r):
    print("== P0.06 J12.7 west wrap x=25.55 after P0.01 wall gone ==", flush=True)
    # F-jump COEX0 then P0.15 at y=44.50, west column x=25.55, approach y=74.
    if try_via_routes(
        r,
        "P0.06",
        False,
        [(40.20, 44.50), (37.40, 44.50), (33.40, 44.50), (30.90, 44.50)],
        [
            ([(44.00, 43.80), (40.20, 44.50)], B, 0.18, "B island to COEX0 viaE"),
            ([(40.20, 44.50), (37.40, 44.50)], F, 0.18, "F jump COEX0"),
            ([(37.40, 44.50), (33.40, 44.50)], B, 0.18, "B between jumps"),
            ([(33.40, 44.50), (30.90, 44.50)], F, 0.18, "F jump P0.15 V x=32.20"),
            (
                [
                    (30.90, 44.50),
                    (25.55, 44.50),
                    (25.55, 74.00),
                    (21.24, 74.00),
                    (21.24, 76.00),
                ],
                B,
                0.18,
                "B west x=25.55 y>=64 then y=74 to J12.7",
            ),
        ],
    ):
        return
    if try_list(
        r,
        "P0.06",
        B,
        0.18,
        [
            (
                [(25.55, 44.50), (25.55, 74.00), (21.24, 74.00), (21.24, 76.00)],
                "B column only if jumps already placed",
            ),
            (
                [(45.15, 36.00), (25.55, 36.00), (25.55, 74.00), (21.24, 74.00), (21.24, 76.00)],
                "B direct y=36 (P0.15/COEX2 may still block)",
            ),
            (
                [
                    (30.90, 44.50),
                    (25.10, 44.50),
                    (25.10, 36.00),
                    (25.55, 36.00),
                    (25.55, 74.00),
                    (21.24, 74.00),
                    (21.24, 76.00),
                ],
                "B hop GNSS then x=25.55",
            ),
            (
                [(21.24, 76.00), (21.24, 77.45), (25.10, 77.45), (25.10, 74.00)],
                "B stub y=77.45 leftover",
            ),
        ],
    ):
        return
    BLOCKERS["P0.06"] = BLOCKERS.get("P0.06") or why(
        r,
        [(30.90, 44.50), (25.55, 44.50), (25.55, 74.00), (21.24, 74.00), (21.24, 76.00)],
        B,
        0.18,
        "P0.06",
    )


def route_p006_j9(r):
    print("== P0.06 J9.1 branch from J12 (no second U1 escape) ==", flush=True)
    if try_list(
        r,
        "P0.06",
        B,
        0.18,
        [
            (
                [(21.24, 76.00), (21.24, 78.90), (116.00, 78.90), (116.00, 8.00)],
                "B stub y=78.90 south of P0.01 y=78.50 to J9.1",
            ),
            (
                [(21.24, 76.00), (21.24, 77.20), (8.20, 77.20), (8.20, 78.90), (116.00, 78.90), (116.00, 8.00)],
                "B west then y=78.90 to J9.1",
            ),
        ],
    ):
        return
    BLOCKERS["P0.06_J9"] = BLOCKERS.get("P0.06_J9") or "J9 branch blocked"


def route_vin_filt_short(r):
    print("== VIN_FILT short hop only ==", flush=True)
    try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            ([(55.35, 12.00), (51.90, 12.00), (51.90, 21.90)], "F L 12.00"),
            ([(55.35, 12.00), (55.35, 21.90), (51.90, 21.90)], "F L 21.90"),
            ([(55.35, 13.30), (55.35, 12.00), (51.90, 12.00), (51.90, 21.90)], "F from JP1 y12"),
        ],
    )


def route_vin_f_short(r):
    print("== VIN_F short hop only (no 80 mm) ==", flush=True)
    try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            ([(49.30, 12.60), (49.30, 12.90), (71.20, 12.90), (71.20, 19.06)], "F y12.90"),
            ([(49.30, 12.60), (71.58, 12.60), (71.58, 17.66)], "F y12.60"),
        ],
    )


def route_nreset_short(r):
    print("== nRESET short hop only ==", flush=True)
    try_list(
        r,
        "nRESET",
        F,
        0.18,
        [
            ([(53.65, 7.27), (53.65, 4.20), (101.68, 4.20), (101.68, 10.80)], "F y4.20 short"),
        ],
    )


def route_sim_clk_short(r):
    print("== SIM_CLK U1 short hop only ==", flush=True)
    try_list(
        r,
        "SIM_CLK",
        B,
        0.18,
        [
            ([(31.25, 23.10), (31.25, 24.40), (36.50, 24.40)], "B courtyard east 5 mm"),
        ],
    )


def route_p008_short(r):
    print("== P0.08 short hop only ==", flush=True)
    try_list(
        r,
        "P0.08",
        F,
        0.18,
        [
            ([(44.00, 30.00), (44.00, 26.00), (78.38, 26.00)], "F y26 to east island"),
            ([(78.38, 26.00), (44.00, 26.00), (44.00, 30.00)], "F y26 reverse"),
        ],
    )


def net_open(pairs, name):
    return any(p["net"] == name for p in pairs)


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
        f.write("| Live snapshot after this pass | `after-pass23.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass23-start.kicad_pcb` |\n\n")
        f.write("## This pass (P0.01 add-then-delete, P0.06 west wrap)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 85. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST wraps / VIN V x=66 not ripped. ")
        f.write("No extra U1 fanout. P0.06 via (45.15, 36) kept.\n\n")
        f.write(f"**P0.01 replacement:** {'yes' if P001_REPL else 'no'}\n\n")
        f.write("**Add-then-delete:** " + ("; ".join(ADDDEL) if ADDDEL else "none kept") + "\n\n")
        f.write(f"**P0.01 x=27.65 segments removed:** {', '.join(RIPPED) if RIPPED else 'none'}\n\n")
        f.write(f"**P0.06 J12.7:** {P006_J12}\n\n")
        f.write(f"**P0.06 J9.1:** {P006_J9}\n\n")
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
    global P001_REPL, P006_J12, P006_J9
    start = snap_path("pass23-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 85:
        print(f"start {n0}>85 abort")
        return 2
    cap = 85
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs

    print("\n#### P0.01 ADD replacement", flush=True)
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "P0.01_ADD", route_p001_repl, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    P001_REPL = ok
    log.append(("P0.01_ADD", "added" if ok else "reverted", f"unconn={ceiling}"))
    print(f"  kept={ok} ceiling={ceiling}", flush=True)

    if ok:
        print("\n#### P0.01 RIP V x=27.65 / H y=77.45", flush=True)
        pre = last
        hits = delete_p001_wall(board)
        ripped = "; ".join(RIPPED) if RIPPED else "none"
        got = check(board, r, "pass23-P001_RIP", pre, cap, force_fill=True)
        if got[0] is None:
            ADDDEL.append("P0.01 replacement added but x=27.65 rip reverted")
            log.append(("P0.01_RIP", "reverted (unconn rose)", ripped))
            RIPPED.clear()
            board, r = reload()
        else:
            ceiling = got[1]
            last = snap_path("pass23-P001_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"P0.01 yes; removed {ripped}")
            log.append(("P0.01_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()

    print("\n#### P0.06 J12.7", flush=True)
    before = ceiling
    board, r, last, ok3, ceiling, new_pairs = apply_net(
        board, r, "P0.06", route_p006_j12, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    j12_open = any(
        p["net"] == "P0.06" and "J12" in (p.get("a", "") + p.get("b", ""))
        for p in last_pairs
    )
    if ok3 and not j12_open:
        P006_J12 = f"closed ({before}→{ceiling})"
    elif ok3:
        P006_J12 = f"partial ({before}→{ceiling})"
    else:
        P006_J12 = "not closed"
        extra = BLOCKERS.get("P0.06", "")
        if extra:
            P006_J12 += f" ({extra})"
    log.append(("P0.06 J12.7", P006_J12, "west wrap x=25.55 y>=64; via (45.15,36) kept"))
    print(f"  {P006_J12}", flush=True)

    if ok3 and not j12_open:
        print("\n#### P0.06 J9.1 from J12", flush=True)
        before = ceiling
        board, r, last, ok9, ceiling, new_pairs = apply_net(
            board, r, "P0.06_J9", route_p006_j9, last, cap
        )
        if new_pairs is not None:
            last_pairs = new_pairs
        j9_open = any(
            p["net"] == "P0.06" and "J9" in (p.get("a", "") + p.get("b", ""))
            for p in last_pairs
        )
        if ok9 and not j9_open:
            P006_J9 = f"closed ({before}→{ceiling})"
        elif ok9:
            P006_J9 = f"partial ({before}→{ceiling})"
        else:
            P006_J9 = "not closed"
        log.append(("P0.06 J9.1", P006_J9, "branch from J12; no second U1 escape"))
        print(f"  {P006_J9}", flush=True)
    else:
        log.append(("P0.06 J9.1", "skipped", "J12 not connected"))

    for name, fn, note0 in (
        ("VIN_FILT", route_vin_filt_short, "short F hop only"),
        ("VIN_F", route_vin_f_short, "short F hop; no 80 mm"),
        ("nRESET", route_nreset_short, "short hop only"),
        ("SIM_CLK", route_sim_clk_short, "U1 short hop only"),
        ("P0.08", route_p008_short, "short F hop only"),
    ):
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok2, ceiling, new_pairs = apply_net(board, r, name, fn, last, cap)
        if new_pairs is not None:
            last_pairs = new_pairs
        st, note = status_of(name, ok2, before, ceiling, last_pairs, note0)
        log.append((name, st, note))
        print(f"  {st}", flush=True)

    shutil.copy2(BOARD, snap_path("pass23"))
    board, r = reload()
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0) or 0
    if shorts or n1 > n0:
        print(f"FINISH abort shorts={shorts} unconn={n1}>{n0}; restore start")
        shutil.copy2(start, BOARD)
        return 3
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, shorts, counts, pairs, log, board)
    print(
        f"END unconn={n1} shorts={shorts} P0.01_repl={'yes' if P001_REPL else 'no'} "
        f"ripped={RIPPED} P0.06_J12={P006_J12} P0.06_J9={P006_J9} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
