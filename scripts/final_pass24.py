#!/usr/bin/env python3
"""Pass 24: west-wrap J12/J13 from existing U1 vias; P0.06 J9 from J12.

LIVE. Do not restore backups. Ceiling finish ≤84. No /fab unless unconnected=0
AND ratsnest=0. Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 /
P0.01 east replacement. No extra U1 vias that will only be deleted.
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
    write_gpio_csv,
    write_unconnected_csv,
)
import final_pass17 as p17  # noqa: E402
from final_pass17 import try_list  # noqa: E402
from final_pass21 import leftover_f, status_of  # noqa: E402
import final_pass21 as p21  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
CLOSED = []
P006_J9 = "not closed"


def try_sized(r, name, vias, routes):
    """vias: (x, y, size, drill). Check all, then place."""
    for x, y, s, d in vias:
        w = r.via_why(x, y, name, size=s, drill=d)
        if w is not None:
            print(f"  via ({x:.2f},{y:.2f}) {w}", flush=True)
            BLOCKERS[name] = f"via ({x:.2f},{y:.2f}) {w}"
            return False
    for pts, layer, w, lab in routes:
        if not r.path_clear(pts, layer, w, name):
            msg = why(r, pts, layer, w, name)
            print(f"  BLOCK {lab}: {msg}", flush=True)
            BLOCKERS[name] = f"{lab}: {msg}"
            return False
    for x, y, s, d in vias:
        r.add_via(x, y, r.code_of(name), name, size=s, drill=d)
        print(f"  via {name} ({x:.2f},{y:.2f}) {s:.2f}/{d:.2f}", flush=True)
    for pts, layer, w, lab in routes:
        r.commit(pts, layer, w, r.code_of(name), name)
        print(f"  OK {lab}", flush=True)
    BLOCKERS.pop(name, None)
    return True


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
    got = check(r.board, r, f"pass24-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass24-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def j12_open(pairs, name):
    for p in pairs:
        if p["net"] != name:
            continue
        blob = p.get("a", "") + p.get("b", "")
        if "J12" in blob or "J13" in blob:
            return True
    return False


def route_p006_j9(r):
    print("== P0.06 J9.1 branch from J12 copper (no second U1 escape) ==", flush=True)
    # F south of P0.01 stub y=78.50 then east; drop and jog VDD_GPIO.
    if try_sized(
        r,
        "P0.06",
        [
            (21.24, 77.20, 0.60, 0.30),
            (115.20, 77.95, 0.60, 0.30),
        ],
        [
            ([(21.24, 76.00), (21.24, 77.20)], B, 0.18, "B stub to F via"),
            (
                [
                    (21.24, 77.20),
                    (79.00, 77.20),
                    (79.00, 78.80),
                    (115.20, 78.80),
                    (115.20, 77.95),
                ],
                F,
                0.18,
                "F south of P0.01 y=78.50 to SE",
            ),
        ],
    ):
        # try continue on B — may still fail; copper to SE is still a branch
        try_list(
            r,
            "P0.06",
            B,
            0.18,
            [
                (
                    [
                        (115.20, 77.95),
                        (115.20, 54.20),
                        (113.40, 54.20),
                        (113.40, 8.00),
                        (116.00, 8.00),
                    ],
                    "B jog J11/VDD_GPIO to J9.1",
                ),
                (
                    [
                        (115.20, 77.95),
                        (108.80, 77.95),
                        (108.80, 8.00),
                        (116.00, 8.00),
                    ],
                    "B x=108.8 to J9.1",
                ),
            ],
        )
        return
    if try_list(
        r,
        "P0.06",
        B,
        0.18,
        [
            (
                [(21.24, 76.00), (21.24, 77.20), (24.80, 77.20), (24.80, 73.40)],
                "B stub y=77.20 then y=73.40",
            ),
        ],
    ):
        return
    BLOCKERS["P0.06_J9"] = BLOCKERS.get("P0.06") or "J9 branch blocked"


def route_p002(r):
    print("== P0.02 via (40.75,41.10) west wrap x=26.2 y>=64 to J12.3 ==", flush=True)
    if try_sized(
        r,
        "P0.02",
        [
            (40.75, 43.50, 0.45, 0.25),
            (39.50, 45.80, 0.60, 0.30),
            (37.40, 45.80, 0.60, 0.30),
            (33.40, 45.80, 0.60, 0.30),
            (30.90, 45.80, 0.60, 0.30),
            (26.20, 73.40, 0.60, 0.30),
            (24.80, 73.40, 0.60, 0.30),
        ],
        [
            ([(40.75, 41.10), (40.75, 43.50)], F, 0.18, "F south from courtyard via"),
            (
                [(40.75, 43.50), (39.50, 43.50), (39.50, 45.80)],
                B,
                0.18,
                "B west of P0.06 H then south",
            ),
            ([(39.50, 45.80), (37.40, 45.80)], F, 0.18, "F jump COEX0"),
            ([(37.40, 45.80), (33.40, 45.80)], B, 0.18, "B between jumps"),
            ([(33.40, 45.80), (30.90, 45.80)], F, 0.18, "F jump P0.15"),
            (
                [(30.90, 45.80), (26.20, 45.80), (26.20, 73.40)],
                B,
                0.18,
                "B column x=26.2 y>=64",
            ),
            ([(26.20, 73.40), (24.80, 73.40)], F, 0.18, "F hop P0.06 V x=25.55"),
            (
                [(24.80, 73.40), (11.08, 73.40), (11.08, 76.00)],
                B,
                0.18,
                "B y=73.40 stub to J12.3",
            ),
        ],
    ):
        return
    BLOCKERS["P0.02"] = BLOCKERS.get("P0.02") or "west wrap blocked"


def route_p005(r):
    print("== P0.05 via (47.40,36.50) west wrap (skip if boxed by P0.06) ==", flush=True)
    if try_sized(
        r,
        "P0.05",
        [
            (51.20, 36.50, 0.45, 0.25),
            (51.20, 45.80, 0.60, 0.30),
            (40.20, 45.80, 0.60, 0.30),
            (37.40, 46.80, 0.60, 0.30),
            (33.40, 46.80, 0.60, 0.30),
            (30.90, 46.80, 0.60, 0.30),
            (26.20, 73.40, 0.60, 0.30),
        ],
        [
            ([(47.40, 36.50), (47.40, 34.80), (51.20, 34.80), (51.20, 36.50)], F, 0.18, "F jog around P0.06 via"),
            ([(51.20, 36.50), (51.20, 45.80)], B, 0.18, "B east column"),
            ([(51.20, 45.80), (40.20, 45.80)], B, 0.18, "B west y=45.80"),
            ([(40.20, 45.80), (37.40, 46.80)], F, 0.18, "F COEX"),
            ([(37.40, 46.80), (33.40, 46.80)], B, 0.18, "B mid"),
            ([(33.40, 46.80), (30.90, 46.80)], F, 0.18, "F P0.15"),
            (
                [(30.90, 46.80), (26.20, 46.80), (26.20, 73.40)],
                B,
                0.18,
                "B x=26.2",
            ),
            ([(26.20, 73.40), (26.20, 77.20), (18.70, 77.20), (18.70, 76.00)], B, 0.18, "stub y=77.2 J12.6"),
        ],
    ):
        return
    BLOCKERS["P0.05"] = BLOCKERS.get("P0.05") or "boxed by P0.06 / VDD1"


def route_p007(r):
    print("== P0.07 via (47.40,35.50) west wrap ==", flush=True)
    if try_sized(
        r,
        "P0.07",
        [
            (51.20, 34.80, 0.45, 0.25),
            (51.20, 47.00, 0.60, 0.30),
            (37.40, 47.00, 0.60, 0.30),
            (33.40, 46.00, 0.60, 0.30),
            (30.90, 46.00, 0.60, 0.30),
        ],
        [
            ([(47.40, 35.50), (47.40, 34.80), (51.20, 34.80)], F, 0.18, "F north-east C4"),
            ([(51.20, 34.80), (51.20, 47.00), (40.20, 47.00)], B, 0.18, "B east then west"),
            ([(40.20, 47.00), (37.40, 47.00)], F, 0.18, "F COEX"),
            ([(37.40, 47.00), (33.40, 46.00)], B, 0.18, "B mid"),
            ([(33.40, 46.00), (30.90, 46.00)], F, 0.18, "F P0.15"),
            (
                [(30.90, 46.00), (26.20, 46.00), (26.20, 73.40), (23.78, 73.40), (23.78, 76.00)],
                B,
                0.18,
                "B wrap to J12.8",
            ),
        ],
    ):
        return
    BLOCKERS["P0.07"] = BLOCKERS.get("P0.07") or "C4 / P0.06 cage"


def route_p010(r):
    print("== P0.10 via (47.40,28.50) — skip if no legal wrap ==", flush=True)
    if try_list(
        r,
        "P0.10",
        B,
        0.18,
        [
            ([(47.40, 28.50), (47.40, 27.20), (26.20, 27.20), (26.20, 73.40), (31.40, 73.40), (31.40, 76.00)], "B y27.2 wrap"),
        ],
    ):
        return
    BLOCKERS["P0.10"] = BLOCKERS.get("P0.10") or "GND via / P0.15 wall"


def route_p011(r):
    print("== P0.11 via (48.62,28.00) — skip if no legal wrap ==", flush=True)
    if try_list(
        r,
        "P0.11",
        B,
        0.18,
        [
            ([(48.62, 28.00), (51.20, 28.00), (51.20, 46.80), (26.20, 46.80), (26.20, 73.40), (33.94, 73.40), (33.94, 76.00)], "B east then wrap"),
        ],
    ):
        return
    BLOCKERS["P0.11"] = BLOCKERS.get("P0.11") or "no B island path"


def route_p012(r):
    print("== P0.12 via (47.40,27.50) — skip if no legal wrap ==", flush=True)
    if try_list(
        r,
        "P0.12",
        B,
        0.18,
        [
            ([(47.40, 27.50), (51.20, 27.50), (51.20, 46.80)], "B east of P0.15"),
        ],
    ):
        return
    BLOCKERS["P0.12"] = BLOCKERS.get("P0.12") or "P0.15 V wall"


def write_release(n0, n1, shorts, counts, pairs, log, board, remaining_j12):
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
        f.write("| Live snapshot after this pass | `after-pass24.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass24-start.kicad_pcb` |\n\n")
        f.write("## This pass (west wrap J12/J13, P0.06 J9)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 84. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 east replacement not ripped. ")
        f.write("No extra dangling U1 vias.\n\n")
        f.write(f"**J12/J13 nets closed:** {', '.join(CLOSED) if CLOSED else 'none'}\n\n")
        f.write(f"**P0.06 J9.1:** {P006_J9}\n\n")
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            f.write(f"| {name} | {status} — {note} |\n")
        f.write("\n## Remaining J12 still open\n\n")
        if remaining_j12:
            for line in remaining_j12:
                f.write(f"- {line}\n")
            f.write("\n")
        else:
            f.write("None in DRC pairs.\n\n")
        f.write("## Remaining unconnected (by class)\n\n")
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


def remaining_j12_lines(pairs):
    out = []
    for p in sorted(pairs, key=lambda x: x["net"]):
        blob = p.get("a", "") + p.get("b", "")
        if "J12" not in blob and "J13" not in blob:
            continue
        d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
        why_s = BLOCKERS.get(p["net"], "")
        extra = f" — {why_s}" if why_s else ""
        out.append(
            f"{p['net']} {p['cls']} {d:.3f} mm "
            f"({p['ax']:.2f},{p['ay']:.2f})–({p['bx']:.2f},{p['by']:.2f}){extra}"
        )
    return out


def main():
    global P006_J9
    start = snap_path("pass24-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 84:
        print(f"start {n0}>84 abort")
        return 2
    cap = 84
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs

    print("\n#### P0.06 J9.1", flush=True)
    before = ceiling
    j9_was = any("J9" in (p.get("a", "") + p.get("b", "")) and p["net"] == "P0.06" for p in last_pairs)
    board, r, last, ok9, ceiling, new_pairs = apply_net(
        board, r, "P0.06_J9", route_p006_j9, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    j9_now = any("J9" in (p.get("a", "") + p.get("b", "")) and p["net"] == "P0.06" for p in last_pairs)
    if ok9 and j9_was and not j9_now:
        P006_J9 = f"yes ({before}→{ceiling})"
    else:
        P006_J9 = "no"
        extra = BLOCKERS.get("P0.06") or BLOCKERS.get("P0.06_J9") or ""
        if extra:
            P006_J9 += f" ({extra})"
    log.append(("P0.06 J9.1", P006_J9, "branch from J12; no second U1 escape"))
    print(f"  {P006_J9}", flush=True)

    for name, fn, note0, header in (
        ("P0.02", route_p002, "west wrap x=26.2 from via (40.75,41.10)", "J12.3"),
        ("P0.05", route_p005, "via (47.40,36.50) wrap", "J12.6"),
        ("P0.07", route_p007, "via (47.40,35.50) wrap", "J12.8"),
        ("P0.10", route_p010, "via (47.40,28.50) wrap", "J12.11"),
        ("P0.11", route_p011, "via (48.62,28.00) wrap", "J12.12"),
        ("P0.12", route_p012, "via (47.40,27.50) wrap", "J12.13"),
    ):
        if not j12_open(last_pairs, name):
            log.append((name, "skip", f"{header} not in DRC pairs"))
            continue
        print(f"\n#### {name} {header}", flush=True)
        before = ceiling
        board, r, last, ok, ceiling, new_pairs = apply_net(board, r, name, fn, last, cap)
        if new_pairs is not None:
            last_pairs = new_pairs
        still = j12_open(last_pairs, name)
        if ok and not still:
            CLOSED.append(f"{name} {header}")
            st = f"closed ({before}→{ceiling})"
        elif ok:
            st = f"not closed (unconn {before}→{ceiling})"
        else:
            st = "not closed (DRC revert or blocked)"
        extra = BLOCKERS.get(name, "")
        note = note0 + (f". blocker: `{extra}`" if extra else "")
        log.append((name, st, note))
        print(f"  {st}", flush=True)

    shutil.copy2(BOARD, snap_path("pass24"))
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
    rem = remaining_j12_lines(pairs)
    write_release(n0, n1, shorts, counts, pairs, log, board, rem)
    print(
        f"END unconn={n1} shorts={shorts} closed={CLOSED} "
        f"P0.06_J9={P006_J9} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
