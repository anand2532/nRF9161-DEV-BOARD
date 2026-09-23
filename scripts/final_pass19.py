#!/usr/bin/env python3
"""Pass 19: VDD2 stub, COEX2 add-then-delete y=24.60 x=48–72, VDD2 complete, ENABLE.

LIVE board only. Do not restore backups. No /fab unless unconnected=0 AND ratsnest=0.
Save only if shorts=0. Unconnected must not finish above 89.
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
from final_pass17 import leftover_f  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}

VDD2_STUB = [(68.79, 19.13), (68.79, 21.20), (54.50, 21.20)]
VDD2_VIA = (54.50, 21.20)
VDD2_C8 = [(54.50, 21.20), (54.50, 32.00), (59.70, 32.00)]
COEX2_REPL = [
    (40.50, 24.60),
    (40.50, 33.20),
    (58.80, 33.20),
    (58.80, 43.20),
    (64.60, 43.20),
    (64.60, 38.00),
    (72.00, 38.00),
    (72.00, 24.60),
]
ENABLE_HW = [(50.85, 23.15), (50.85, 24.90), (62.50, 24.90), (62.50, 40.95)]
ENABLE_VIA = (62.50, 40.95)
RIP_X0, RIP_X1, RIP_Y = 48.00, 72.00, 24.60


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


def apply_fn(board, r, name, fn, last, ceiling):
    r.ok = 0
    r.fail = 0
    fn(r)
    r.collect()
    got = check(r.board, r, f"pass19-{name}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling
    last = snap_path(f"pass19-{name}")
    board, r = reload()
    return board, r, last, True, got[1]


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)


def list_coex2_mid_h(board):
    hits = []
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "COEX2" or tr.GetLayer() != B:
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


def route_vdd2_stub(r):
    print("== VDD2 stub B y=21.20 to via (54.50, 21.20) ==", flush=True)
    if not try_commit(r, VDD2_STUB, B, 0.25, "VDD2", "B FB3 y=21.20 to 54.50"):
        BLOCKERS["VDD2_STUB"] = why(r, VDD2_STUB, B, 0.25, "VDD2")
        return
    w = r.via_why(VDD2_VIA[0], VDD2_VIA[1], "VDD2", pwr=True)
    if w is not None:
        print(f"  via {VDD2_VIA} blocked: {w}; leaving track only", flush=True)
        BLOCKERS["VDD2_STUB"] = f"via {VDD2_VIA}: {w}"
        return
    r.add_via(VDD2_VIA[0], VDD2_VIA[1], r.code_of("VDD2"), "VDD2", pwr=True)
    r.ok += 1
    print(f"  via VDD2 {VDD2_VIA} 0.80/0.40", flush=True)
    BLOCKERS.pop("VDD2_STUB", None)


def route_coex2_add(r):
    print("== ADD COEX2 replacement (not y=24.60 in x=48–72) ==", flush=True)
    if try_commit(r, COEX2_REPL, B, 0.18, "COEX2", "private col x=64.6 / y=33.2–38 wrap"):
        BLOCKERS.pop("COEX2_ADD", None)
        return
    BLOCKERS["COEX2_ADD"] = why(r, COEX2_REPL, B, 0.18, "COEX2")


def delete_coex2_mid_h(board, r):
    hits = list_coex2_mid_h(board)
    print(f"== DELETE COEX2 y=24.60 x={RIP_X0}–{RIP_X1} hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2, tr.GetWidth()))
        board.Remove(tr)
    code = r.code_of("COEX2")
    west = [(37.75, RIP_Y), (RIP_X0, RIP_Y)]
    east = [(RIP_X1, RIP_Y), (105.10, RIP_Y)]
    for pts, lab in ((west, "west remnant"), (east, "east remnant")):
        if r.path_clear(pts, B, 0.18, "COEX2"):
            r.commit(pts, B, 0.18, code, "COEX2")
            print(f"  keep {lab} {pts}")
        else:
            print(f"  skip {lab}: {why(r, pts, B, 0.18, 'COEX2')}")
            # remnant may overlap replacement T-junction; add anyway if same-net
            r.add_track(pts[0][0], pts[0][1], pts[1][0], pts[1][1], B, 0.18, code, "COEX2")
            print(f"  force {lab}")
    r.collect()
    return specs


def restore_coex2_h(r, specs):
    code = r.code_of("COEX2")
    for x1, y1, x2, y2, width in specs:
        w = pcbnew.ToMM(width) if width > 100 else width
        r.add_track(x1, y1, x2, y2, B, w, code, "COEX2")
        print(f"  restored ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")


def route_vdd2_c8(r):
    print("== VDD2 complete through freed y=24.60 to C8 (59.70, 32) ==", flush=True)
    if try_commit(r, VDD2_C8, B, 0.25, "VDD2", "B x=54.50 to C8 H y=32"):
        BLOCKERS.pop("VDD2", None)
        return
    BLOCKERS["VDD2"] = why(r, VDD2_C8, B, 0.25, "VDD2")
    alts = [
        ([(54.50, 21.20), (54.50, 26.75), (56.50, 26.75), (56.50, 32.00), (59.70, 32.00)],
         "jog east of VDD1 via 53.70,27.13"),
        ([(54.50, 21.20), (56.20, 21.20), (56.20, 32.00), (59.70, 32.00)],
         "east of TP19 then south"),
        ([(54.50, 21.20), (54.50, 25.90), (44.72, 25.90)],
         "west to south island via 44.72"),
    ]
    for pts, lab in alts:
        if try_commit(r, pts, B, 0.25, "VDD2", lab):
            BLOCKERS.pop("VDD2", None)
            return
        BLOCKERS["VDD2"] = f"{lab}: {why(r, pts, B, 0.25, 'VDD2')}"


def route_enable(r):
    print("== ENABLE C14 island to existing F highway y=40.95 / U1 ==", flush=True)
    w = r.via_why(ENABLE_VIA[0], ENABLE_VIA[1], "ENABLE", pwr=False)
    if w is not None:
        print(f"  via {ENABLE_VIA} {w}", flush=True)
        BLOCKERS["ENABLE"] = f"via {ENABLE_VIA}: {w}"
    else:
        if r.path_clear(ENABLE_HW, B, 0.18, "ENABLE"):
            r.add_via(ENABLE_VIA[0], ENABLE_VIA[1], r.code_of("ENABLE"), "ENABLE", pwr=False)
            r.commit(ENABLE_HW, B, 0.18, r.code_of("ENABLE"), "ENABLE")
            print(f"  OK B gap y=24.90 x=62.50 + via {ENABLE_VIA} to F highway", flush=True)
            BLOCKERS.pop("ENABLE", None)
            return
        BLOCKERS["ENABLE"] = why(r, ENABLE_HW, B, 0.18, "ENABLE")
        print(f"  FAIL highway: {BLOCKERS['ENABLE']}", flush=True)
    alts = [
        ([(48.33, 23.13), (48.33, 24.90), (62.50, 24.90), (62.50, 40.95)], B, 0.18, (62.50, 40.95),
         "from 48.33 via gap to highway"),
        ([(50.85, 23.15), (50.85, 25.00), (63.00, 25.00), (63.00, 40.95)], B, 0.18, (63.00, 40.95),
         "y=25 x=63 to highway"),
        ([(50.85, 23.15), (50.85, 24.95), (62.00, 24.95), (62.00, 40.95)], B, 0.18, (62.00, 40.95),
         "x=62 to highway"),
        ([(48.33, 23.13), (48.33, 25.50), (42.75, 25.50), (42.75, 41.10)], B, 0.18, None,
         "B west through gap to U1 via"),
        ([(47.68, 22.00), (46.80, 22.00), (46.80, 24.40), (42.90, 24.40)], F, 0.18, None,
         "F west of C14.2 / leftover P0.15"),
    ]
    for pts, ly, wth, via, lab in alts:
        if via is not None:
            vw = r.via_why(via[0], via[1], "ENABLE", pwr=False)
            if vw is not None:
                print(f"  skip {lab}: via {via} {vw}", flush=True)
                continue
            if not r.path_clear(pts, ly, wth, "ENABLE"):
                print(f"  FAIL {lab}: {why(r, pts, ly, wth, 'ENABLE')}", flush=True)
                BLOCKERS["ENABLE"] = f"{lab}: {why(r, pts, ly, wth, 'ENABLE')}"
                continue
            r.add_via(via[0], via[1], r.code_of("ENABLE"), "ENABLE", pwr=False)
            r.commit(pts, ly, wth, r.code_of("ENABLE"), "ENABLE")
            print(f"  OK {lab}", flush=True)
            BLOCKERS.pop("ENABLE", None)
            return
        if try_commit(r, pts, ly, wth, "ENABLE", lab):
            BLOCKERS.pop("ENABLE", None)
            return
        BLOCKERS["ENABLE"] = f"{lab}: {why(r, pts, ly, wth, 'ENABLE')}"


def write_release(n0, n1, shorts, counts, pairs, log, board, coex2_note):
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
        f.write("| Live snapshot after this pass | `after-pass19.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass18.kicad_pcb` |\n\n")
        f.write("## This pass (VDD2 stub, COEX2 add-then-delete, VDD2, ENABLE)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Ceiling was 89. Zone refill ran after every copper change. ")
        f.write("`complete_route.py` main() and `rebuild_bcu.py` were not run. ")
        f.write("Locked RF was not rewritten. In2 remains `VDD_nRF`. ")
        f.write("P0.01 / P0.15 replacement / SIM_RST not ripped. No extra GPIO fanout. ")
        f.write("No DNP 50Ω stubs. GND stitch from pass18 kept.\n\n")
        f.write(f"**COEX2:** {coex2_note}\n\n")
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
    start = snap_path("pass19-start")
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
    if n0 > 89:
        print(f"start unconn {n0} > 89; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    coex2_note = "not replaced"
    ripped_txt = "none"

    print("\n#### VDD2_STUB", flush=True)
    before = ceiling
    board, r, last, ok, ceiling = apply_fn(board, r, "VDD2STUB", route_vdd2_stub, last, ceiling)
    status = (
        f"committed (unconn={ceiling})"
        if ok
        else "not committed (DRC revert)"
    )
    log.append(("VDD2_STUB", status, "B (68.79,19.13) y=21.20 to via (54.50,21.20)"))
    print(f"  kept={ok} ceiling={ceiling} {status}", flush=True)

    print("\n#### COEX2_ADD", flush=True)
    board, r, last, ok, ceiling = apply_fn(board, r, "COEX2ADD", route_coex2_add, last, ceiling)
    if not ok:
        coex2_note = "replacement DRC-failed; original y=24.60 H kept"
        log.append(("COEX2_ADD", "not added", coex2_note))
    else:
        log.append(("COEX2_ADD", f"added (unconn={ceiling})", "wrap x=40.5 / y=33.2 / x=64.6 / y=38 / x=72"))
        print("\n#### COEX2_RIP", flush=True)
        pre_rip = last
        specs = delete_coex2_mid_h(board, r)
        ripped_txt = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for _, a, b, c, d in
                               [(None, *s[:4]) for s in specs]) or "none"
        got = check(board, r, "pass19-COEX2RIP", pre_rip, ceiling, force_fill=True)
        if got[0] is None:
            coex2_note = (
                f"replacement added but rip reverted (unconnected rose). "
                f"Would have removed {ripped_txt}"
            )
            log.append(("COEX2_RIP", "reverted", coex2_note))
            board, r = reload()
            last = pre_rip
        else:
            ceiling = got[1]
            last = snap_path("pass19-COEX2RIP")
            coex2_note = (
                "replacement yes; removed y=24.60 mid-H "
                f"{ripped_txt}; remnants x=37.75–48 and x=72–105.10 kept"
            )
            log.append(("COEX2_RIP", f"ripped (unconn={ceiling})", coex2_note))
            board, r = reload()

            print("\n#### VDD2", flush=True)
            before = ceiling
            board, r, last, ok, ceiling = apply_fn(board, r, "VDD2", route_vdd2_c8, last, ceiling)
            if not ok:
                st = "not closed (DRC revert or blocked)"
            elif ceiling < before:
                st = f"closed ({before}→{ceiling})"
            else:
                st = "not closed (no DRC-clean copper)"
            log.append(("VDD2", st, "FB3 via (54.50,21.20) through freed y=24.60 to C8 (59.70,32)"))
            print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)
            if "VDD2" in BLOCKERS:
                print(f"  last blocker: {BLOCKERS['VDD2']}", flush=True)

    print("\n#### ENABLE", flush=True)
    before = ceiling
    board, r, last, ok, ceiling = apply_fn(board, r, "ENABLE", route_enable, last, ceiling)
    if not ok:
        st = "not closed (DRC revert or blocked)"
    elif ceiling < before:
        st = f"closed ({before}→{ceiling})"
    else:
        st = "not closed (no DRC-clean copper)"
    log.append(
        ("ENABLE", st,
         "C14 island (50.85,23.15) through gap y=24.90 to via (62.50,40.95) on existing F highway")
    )
    print(f"  kept={ok} ceiling={ceiling} {st}", flush=True)
    if "ENABLE" in BLOCKERS:
        print(f"  last blocker: {BLOCKERS['ENABLE']}", flush=True)

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass19"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board, coex2_note)
    print(
        f"\nEND unconn={n1} shorts={counts.get('shorting_items',0)} "
        f"start={n0} fab={'yes' if n1==0 else 'no'}",
        flush=True,
    )
    print("COEX2:", coex2_note, flush=True)
    print("BLOCKERS:", BLOCKERS, flush=True)
    print("classes", dict(class_counts(pairs)), flush=True)
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= 89 else 1


if __name__ == "__main__":
    sys.exit(main())
