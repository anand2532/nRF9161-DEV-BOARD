#!/usr/bin/env python3
"""Pass 21b: VIN wrap+stitch+rip then VIN_FILT/VIN_F; SIM_RST_C add-then-delete; SIM_IO_C.

LIVE. Do not restore backups. Ceiling finish ≤87 (start 86). Allow VIN_ADD intermediate 87.
Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_CLK_C B wrap.
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
import final_pass21 as p21  # noqa: E402
from final_pass21 import (  # noqa: E402
    delete_vin_v66,
    leftover_f,
    mm_xy,
    status_of,
)
# Return H at y=11.90 so VIN_FILT y=13.80 / VIN_F y=13.10 can drop south of it.
VIN_WRAP = [
    (66.00, 10.00),
    (66.00, 11.50),
    (76.20, 11.50),
    (76.20, 11.90),
    (62.00, 11.90),
    (62.00, 15.40),
]

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
ADDDEL = []
GND_SITES = [
    (74.50, 13.20),
    (75.50, 12.50),
    (61.20, 13.20),
    (80.00, 13.00),
]
SIM_RST_C_WRAP = [
    (79.38, 56.05),
    (81.80, 56.05),
    (81.80, 44.60),
    (97.30, 44.60),
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
    got = check(r.board, r, f"pass21b-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass21b-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def route_vin_add(r):
    print("== ADD VIN wrap y=11.50/14.70 x=76.20 ==", flush=True)
    if try_commit(r, VIN_WRAP, F, 0.40, "VIN", "F wrap"):
        BLOCKERS.pop("VIN_ADD", None)
        return
    BLOCKERS["VIN_ADD"] = why(r, VIN_WRAP, F, 0.40, "VIN")


def route_gnd(r):
    print("== GND stitch north of VIN wrap (E island) ==", flush=True)
    for xy in GND_SITES:
        for size, drill in ((0.60, 0.30), (0.45, 0.25)):
            w = r.via_why(xy[0], xy[1], "GND", pwr=True, size=size, drill=drill)
            if w is None:
                r.add_via(xy[0], xy[1], r.code_of("GND"), "GND", pwr=True, size=size, drill=drill)
                r.ok += 1
                print(f"  via GND {xy} {size}/{drill}", flush=True)
                BLOCKERS.pop("GND", None)
                return
            print(f"  skip {xy} {size}/{drill}: {w}", flush=True)
    BLOCKERS["GND"] = "no stitch site"


def route_vin_filt(r):
    print("== VIN_FILT JP1 y=13.80 through freed x=66 to FB4 ==", flush=True)
    try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            ([(55.35, 13.30), (55.35, 13.80), (74.00, 13.80), (74.00, 16.94)], "F y13.80 to FB4"),
            ([(55.35, 13.30), (55.35, 13.50), (74.00, 13.50), (74.00, 16.94)], "F y13.50 to FB4"),
            ([(55.35, 13.30), (55.35, 12.90), (74.00, 12.90), (74.00, 16.94)], "F y12.90 to FB4"),
        ],
    )


def route_vin_f(r):
    print("== VIN_F y=12.60 through freed x=66 ==", flush=True)
    try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            ([(49.30, 13.10), (71.58, 13.10), (71.58, 17.66)], "F y13.10 to FB4 via"),
            ([(49.30, 12.80), (56.90, 12.80), (56.90, 13.10), (71.58, 13.10), (71.58, 17.66)], "F jog VDD_nRF 57.95,12"),
            ([(49.30, 12.60), (71.58, 12.60), (71.58, 17.66)], "F y12.60 to FB4 via"),
        ],
    )


def route_sim_rst_c_add(r):
    print("== ADD SIM_RST_C wrap x=81.8 (not V x=79.38) ==", flush=True)
    if try_commit(r, SIM_RST_C_WRAP, B, 0.18, "SIM_RST_C", "B wrap x=81.8"):
        BLOCKERS.pop("SIM_RST_C_ADD", None)
        return
    BLOCKERS["SIM_RST_C_ADD"] = why(r, SIM_RST_C_WRAP, B, 0.18, "SIM_RST_C")


def delete_sim_rst_c_v79(board, r):
    hits = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "SIM_RST_C" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(x1 - x2) > 0.30:
            continue
        if abs((x1 + x2) / 2 - 79.38) > 0.30:
            continue
        ya, yb = min(y1, y2), max(y1, y2)
        if yb - ya < 8.0:
            continue
        hits.append((tr, x1, y1, x2, y2))
    print(f"== DELETE SIM_RST_C B V x=79.38 hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2))
        board.Remove(tr)
    r.collect()
    return specs


def route_sim_io_c(r):
    print("== SIM_IO_C via (80.20,53.80) B y=52 to J7; names distinct ==", flush=True)
    if try_via_routes(
        r,
        "SIM_IO_C",
        False,
        [(80.20, 53.80)],
        [
            ([(77.35, 55.40), (77.35, 55.00), (80.20, 55.00), (80.20, 53.80)], F, 0.18, "F alley to via 80.20"),
            (
                [(80.20, 53.80), (80.20, 52.00), (98.54, 52.00), (98.54, 50.01)],
                B,
                0.18,
                "B y52 east of SIM_RST_C",
            ),
        ],
    ):
        return
    if try_via_routes(
        r,
        "SIM_IO_C",
        False,
        [(78.80, 53.80)],
        [
            ([(77.35, 55.40), (78.80, 53.80)], F, 0.18, "F direct to 78.80"),
            (
                [(78.80, 53.80), (80.20, 53.80), (80.20, 52.00), (98.54, 52.00), (98.54, 50.01)],
                B,
                0.18,
                "B from 78.80",
            ),
        ],
    ):
        return
    try_wp_box(
        r, "SIM_IO_C", B, 0.18, 80.20, 53.80, 98.54, 50.01,
        78.0, 104.0, 48.0, 56.0, 0.35, 40, "B dense via-J7",
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
        f.write("| Live snapshot after this pass | `after-pass21b.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass21.kicad_pcb` |\n\n")
        f.write("## This pass (VIN add-then-delete retry, SIM_RST_C, SIM_IO_C)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 87. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE not ripped. SIM_* names not merged. ")
        f.write("G7 / extra GPIO / DNP 50Ω skipped.\n\n")
        f.write("**Add-then-delete:** " + ("; ".join(ADDDEL) if ADDDEL else "none kept") + "\n\n")
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
    start = snap_path("pass21b-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 87:
        print(f"start {n0}>87 abort")
        return 2
    cap = 87
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs
    vin_seq_start = last

    print("\n#### VIN_ADD (allow 87)", flush=True)
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "VIN_ADD", route_vin_add, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    log.append(("VIN_ADD", "added" if ok else "reverted", f"unconn={ceiling}"))
    print(f"  kept={ok} ceiling={ceiling}", flush=True)

    if ok and ceiling > n0:
        print("skip GND stitch in VIN corridor until after hops", flush=True)


    if ok:
        print("\n#### VIN_RIP", flush=True)
        pre = last
        specs = delete_vin_v66(board, r)
        ripped = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in specs) or "none"
        got = check(board, r, "pass21b-VIN_RIP", pre, cap, force_fill=True)
        if got[0] is None:
            ADDDEL.append("VIN wrap added but V x=66 rip reverted")
            log.append(("VIN_RIP", "reverted", ripped))
            shutil.copy2(vin_seq_start, BOARD)
            board, r = reload()
            last = vin_seq_start
            ceiling = n0
        else:
            ceiling = got[1]
            last = snap_path("pass21b-VIN_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"VIN yes; removed F V x=66 {ripped}")
            log.append(("VIN_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()

            for name, fn, note in (
                ("VIN_FILT", route_vin_filt, "JP1 y=13.80 through freed x=66 to FB4"),
                ("VIN_F", route_vin_f, "y=12.60 to via (71.58,17.66); not merged with VIN_FILT"),
            ):
                print(f"\n#### {name}", flush=True)
                before = ceiling
                board, r, last, ok2, ceiling, new_pairs = apply_net(
                    board, r, name, fn, last, cap
                )
                if new_pairs is not None:
                    last_pairs = new_pairs
                st, note2 = status_of(name, ok2, before, ceiling, last_pairs, note)
                log.append((name, st, note2))
                print(f"  kept={ok2} ceiling={ceiling} {st}", flush=True)
            if ceiling > 87:
                print(f"VIN sequence finished above cap ({ceiling}>87); restoring {vin_seq_start}")
                shutil.copy2(vin_seq_start, BOARD)
                board, r = reload()
                last = vin_seq_start
                ceiling = n0
                ADDDEL[:] = [x for x in ADDDEL if not x.startswith("VIN")]
                ADDDEL.append("VIN sequence restored (finish would exceed 87)")
    else:
        log.append(("VIN_RIP", "skipped", "no wrap"))
        log.append(("VIN_FILT", "not closed", "VIN V x=66 remains"))
        log.append(("VIN_F", "not closed", "VIN V x=66 remains"))

    print("\n#### SIM_RST_C_ADD", flush=True)
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "SIM_RST_C_ADD", route_sim_rst_c_add, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    log.append(("SIM_RST_C_ADD", "added" if ok else "not added", f"unconn={ceiling}"))
    if ok:
        print("\n#### SIM_RST_C_RIP", flush=True)
        pre = last
        specs = delete_sim_rst_c_v79(board, r)
        ripped = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in specs) or "none"
        got = check(board, r, "pass21b-SIM_RST_C_RIP", pre, cap, force_fill=True)
        if got[0] is None:
            ADDDEL.append("SIM_RST_C wrap added but V x=79.38 rip reverted")
            log.append(("SIM_RST_C_RIP", "reverted", ripped))
            board, r = reload()
            last = pre
        else:
            ceiling = got[1]
            last = snap_path("pass21b-SIM_RST_C_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"SIM_RST_C yes; removed B V x=79.38 {ripped}")
            log.append(("SIM_RST_C_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()

    print("\n#### SIM_IO_C", flush=True)
    before = ceiling
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "SIM_IO_C", route_sim_io_c, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    st, note = status_of(
        "SIM_IO_C", ok, before, ceiling, last_pairs,
        "U4.1 to J7 via (80.20,53.80) B y=52; not merged with SIM_IO",
    )
    log.append(("SIM_IO_C", st, note))
    print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    if shorts or n1 > 87:
        print(f"END bad unconn={n1} shorts={shorts}; restoring {last}")
        shutil.copy2(last, BOARD)
        board, r = reload()
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        pairs, n1, counts, _ = run_drc()
        shorts = counts.get("shorting_items", 0)
    shutil.copy2(BOARD, snap_path("pass21b"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, shorts, counts, pairs, log, board)
    print(f"\nEND unconn={n1} shorts={shorts} start={n0} fab={'yes' if n1==0 else 'no'}", flush=True)
    print("ADDDEL:", ADDDEL, flush=True)
    print("BLOCKERS:", BLOCKERS, flush=True)
    print("classes", dict(class_counts(pairs)), flush=True)
    for line in leftover_f(pairs):
        print(" leftover", line, flush=True)
    return 0 if shorts == 0 and n1 <= 87 else 1


if __name__ == "__main__":
    sys.exit(main())
