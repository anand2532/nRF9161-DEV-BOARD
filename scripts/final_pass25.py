#!/usr/bin/env python3
"""Pass 25: combined 0.50/0.30 via + west wrap for open J12 nets.

LIVE. Do not restore backups. Ceiling finish ≤83. No /fab unless unconnected=0
AND ratsnest=0. Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 /
P0.01 east replacement. Rollback via+tracks if shorts or unconnected rose or
the J12 pair stayed open (no dangling vias).
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
from final_pass21 import leftover_f  # noqa: E402
import final_pass21 as p21  # noqa: E402
from final_pass22 import extra_via_sites  # noqa: E402
import final_pass24 as p24  # noqa: E402
from final_pass24 import try_sized  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
p24.BLOCKERS = BLOCKERS
CLOSED = []
NET_LOG = []


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
    placed = fn(r)
    r.collect()
    if not placed:
        print(f"  no copper for {name}", flush=True)
        return board, r, last, False, ceiling, None
    got = check(r.board, r, f"pass25-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass25-{name.replace('.', '')}")
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


def count_vias(board):
    return sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))


def dangling_new(board, before_xy):
    """Vias whose (x,y,net) was not in before_xy and have no F and no B track nearby."""
    from complete_route import mm

    old = set(before_xy)
    dang = []
    tracks = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    for tr in board.GetTracks():
        if not isinstance(tr, pcbnew.PCB_VIA):
            continue
        p = tr.GetPosition()
        x, y = round(mm(p.x), 3), round(mm(p.y), 3)
        name = tr.GetNetname()
        key = (name, x, y)
        if key in old:
            continue
        hit_f = hit_b = False
        for t in tracks:
            if t.GetNetname() != name:
                continue
            s, e = t.GetStart(), t.GetEnd()
            x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
            near = hypot(x1, y1, x, y) < 0.40 or hypot(x2, y2, x, y) < 0.40
            if not near:
                continue
            if t.GetLayer() == F:
                hit_f = True
            elif t.GetLayer() == B:
                hit_b = True
        if not hit_b:
            dang.append((name, x, y))
    return dang


def via_xy_set(board):
    from complete_route import mm

    out = []
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            p = tr.GetPosition()
            out.append((tr.GetNetname(), round(mm(p.x), 3), round(mm(p.y), 3)))
    return out


def wrap_jumps(y):
    """COEX0 + P0.15 F-jumps at y, matching P0.02/P0.06."""
    return (40.20, y), (37.40, y), (33.40, y), (30.90, y)


def route_p004(r):
    print("== P0.04 combined courtyard via + west wrap to J12.5 ==", flush=True)
    # Courtyard via (42.25,40.30): ring+2.10 south, not y=39.45, not pad-x through 41.10.
    # Jog B east of ENABLE ring via then west at y=42.80; F-hop P0.06 H at x=41.25;
    # F-jumps y=46.80; column x=27.70 (25.55/26.20 occupied); stub y=77.20 (not 78.50).
    if try_sized(
        r,
        "P0.04",
        [
            (42.25, 40.30, 0.50, 0.30),
            (41.25, 42.50, 0.50, 0.30),
            (37.40, 46.80, 0.50, 0.30),
            (33.40, 46.80, 0.50, 0.30),
            (30.90, 46.80, 0.50, 0.30),
        ],
        [
            ([(42.25, 37.25), (42.25, 40.30)], F, 0.18, "F pad to courtyard via"),
            (
                [
                    (42.25, 40.30),
                    (43.50, 40.30),
                    (43.50, 42.80),
                    (41.25, 42.80),
                    (41.25, 42.50),
                ],
                B,
                0.18,
                "B east of even-ring then west y=42.80",
            ),
            ([(41.25, 42.50), (41.25, 46.80), (37.40, 46.80)], F, 0.18, "F hop P0.06 H + COEX0"),
            ([(37.40, 46.80), (33.40, 46.80)], B, 0.18, "B mid"),
            ([(33.40, 46.80), (30.90, 46.80)], F, 0.18, "F hop P0.15"),
            (
                [
                    (30.90, 46.80),
                    (27.70, 46.80),
                    (27.70, 77.20),
                    (16.16, 77.20),
                    (16.16, 76.00),
                ],
                B,
                0.18,
                "B west column x=27.70 stub y=77.20 J12.5",
            ),
        ],
    ):
        return True
    BLOCKERS["P0.04"] = BLOCKERS.get("P0.04") or "combined via+wrap blocked"
    return False


def _p009_attempts(r):
    p = r.u1("P0.09")
    px, py = p["x"], p["y"]
    jx, jy = 28.86, 76.00
    sites = extra_via_sites(p, "P0.09") + [
        (47.20, 28.40),
        (47.50, 28.30),
        (47.80, 28.20),
        (48.20, 29.50),
        (45.20, 27.40),
        (42.80, 28.40),
        (47.05, 28.20),
        (46.60, 28.20),
        (47.40, 31.20),
        (48.62, 29.50),
    ]
    cols = (28.20, 27.90, 29.10, 24.90)
    wrap_ys = (47.50, 48.20, 52.00, 46.80)
    for vx, vy in sites:
        size, drill = 0.50, 0.30
        w = r.via_why(vx, vy, "P0.09", size=size, drill=drill)
        if w is not None:
            size, drill = 0.45, 0.25
            w = r.via_why(vx, vy, "P0.09", size=size, drill=drill)
            if w is not None:
                continue
        f_cands = [
            [(px, py), (px, vy), (vx, vy)],
            [(px, py), (vx, py), (vx, vy)],
            [(px, py), (px, 28.20), (vx, 28.20), (vx, vy)],
            [(px, py), (px, 28.40), (vx, 28.40), (vx, vy)],
            [(px, py), (45.40, py), (45.40, 28.20), (vx, 28.20), (vx, vy)],
        ]
        fpath = None
        for pts in f_cands:
            if r.path_clear(pts, F, 0.18, "P0.09"):
                fpath = pts
                break
        if not fpath:
            continue
        for wy in wrap_ys:
            a, b1, b2, b3 = wrap_jumps(wy)
            for col in cols:
                hops = [
                    (vx, vy, size, drill),
                    (a[0], a[1], 0.50, 0.30),
                    (b1[0], b1[1], 0.50, 0.30),
                    (b2[0], b2[1], 0.50, 0.30),
                    (b3[0], b3[1], 0.50, 0.30),
                ]
                routes = [
                    (fpath, F, 0.18, f"F pad to via ({vx:.2f},{vy:.2f})"),
                    ([(vx, vy), (a[0], vy), a], B, 0.18, "B to 40.20 wrap y"),
                    ([a, b1], F, 0.18, "F COEX"),
                    ([b1, b2], B, 0.18, "B mid"),
                    ([b2, b3], F, 0.18, "F P0.15"),
                    (
                        [b3, (col, wy), (col, 77.20), (jx, 77.20), (jx, jy)],
                        B,
                        0.18,
                        f"B col x={col} stub y=77.20 J12.10",
                    ),
                ]
                print(
                    f"  try P0.09 via ({vx:.2f},{vy:.2f}) wrap y={wy} col={col}",
                    flush=True,
                )
                if try_sized(r, "P0.09", hops, routes):
                    return True
    BLOCKERS["P0.09"] = BLOCKERS.get("P0.09") or "no via+F-stub+wrap"
    return False


def route_p009(r):
    print("== P0.09 combined extra via + west wrap to J12.10 ==", flush=True)
    return _p009_attempts(r)


def route_p005(r):
    print("== P0.05 H-then-west-wrap around P0.06 island ==", flush=True)
    # Existing via (47.40,36.50) boxed by P0.06. Go east of island, south, then wrap.
    for east_x, wy, col in (
        (50.80, 47.50, 28.20),
        (51.40, 47.50, 28.20),
        (50.80, 52.00, 28.20),
        (49.90, 47.50, 24.90),
    ):
        a, b1, b2, b3 = wrap_jumps(wy)
        hops = [
            (east_x, 37.40, 0.45, 0.25),
            (east_x, wy, 0.50, 0.30),
            (b1[0], b1[1], 0.50, 0.30),
            (b2[0], b2[1], 0.50, 0.30),
            (b3[0], b3[1], 0.50, 0.30),
        ]
        routes = [
            (
                [(47.40, 36.50), (47.40, 37.40), (east_x, 37.40)],
                B,
                0.18,
                f"B south-east around island x={east_x}",
            ),
            ([(east_x, 37.40), (east_x, wy)], B, 0.18, "B east of P0.06 island"),
            ([(east_x, wy), a], B, 0.18, "B west to COEX hop"),
            ([a, b1], F, 0.18, "F COEX"),
            ([b1, b2], B, 0.18, "B mid"),
            ([b2, b3], F, 0.18, "F P0.15"),
            (
                [b3, (col, wy), (col, 77.20), (18.70, 77.20), (18.70, 76.00)],
                B,
                0.18,
                f"B col x={col} J12.6",
            ),
        ]
        print(f"  try P0.05 east_x={east_x} y={wy} col={col}", flush=True)
        if try_sized(r, "P0.05", hops, routes):
            return True
    BLOCKERS["P0.05"] = BLOCKERS.get("P0.05") or "around-island wrap blocked"
    return False


def route_p007(r):
    print("== P0.07 H-then-west-wrap around P0.06 island ==", flush=True)
    for east_x, wy, col in (
        (50.80, 47.50, 28.20),
        (51.40, 48.20, 28.20),
        (50.80, 52.00, 24.90),
    ):
        a, b1, b2, b3 = wrap_jumps(wy)
        hops = [
            (east_x, 34.20, 0.45, 0.25),
            (east_x, wy, 0.50, 0.30),
            (b1[0], b1[1], 0.50, 0.30),
            (b2[0], b2[1], 0.50, 0.30),
            (b3[0], b3[1], 0.50, 0.30),
        ]
        routes = [
            (
                [(47.40, 35.50), (east_x, 35.50), (east_x, 34.20)],
                B,
                0.18,
                f"B east around C4 x={east_x}",
            ),
            ([(east_x, 34.20), (east_x, wy)], B, 0.18, "B east column"),
            ([(east_x, wy), a], B, 0.18, "B west to COEX hop"),
            ([a, b1], F, 0.18, "F COEX"),
            ([b1, b2], B, 0.18, "B mid"),
            ([b2, b3], F, 0.18, "F P0.15"),
            (
                [b3, (col, wy), (col, 77.20), (23.78, 77.20), (23.78, 76.00)],
                B,
                0.18,
                f"B col x={col} J12.8",
            ),
        ]
        print(f"  try P0.07 east_x={east_x} y={wy} col={col}", flush=True)
        if try_sized(r, "P0.07", hops, routes):
            return True
    BLOCKERS["P0.07"] = BLOCKERS.get("P0.07") or "around-island wrap blocked"
    return False


def route_p010(r):
    print("== P0.10 existing via west wrap (COEX2 F-jump if needed) ==", flush=True)
    for wy, col in ((47.50, 28.20), (52.00, 28.20), (47.50, 24.90)):
        a, b1, b2, b3 = wrap_jumps(wy)
        hops = [
            (51.40, 28.50, 0.45, 0.25),
            (51.40, 32.20, 0.50, 0.30),
            (51.40, 34.20, 0.50, 0.30),
            (51.40, wy, 0.50, 0.30),
            (b1[0], b1[1], 0.50, 0.30),
            (b2[0], b2[1], 0.50, 0.30),
            (b3[0], b3[1], 0.50, 0.30),
        ]
        routes = [
            ([(47.40, 28.50), (51.40, 28.50)], B, 0.18, "B east of P0.12"),
            ([(51.40, 28.50), (51.40, 32.20)], B, 0.18, "B south to COEX2"),
            ([(51.40, 32.20), (51.40, 34.20)], F, 0.18, "F hop COEX2 H y=33.20"),
            ([(51.40, 34.20), (51.40, wy), a], B, 0.18, "B south then west"),
            ([a, b1], F, 0.18, "F COEX0"),
            ([b1, b2], B, 0.18, "B mid"),
            ([b2, b3], F, 0.18, "F P0.15"),
            (
                [b3, (col, wy), (col, 77.20), (31.40, 77.20), (31.40, 76.00)],
                B,
                0.18,
                f"B col x={col} J12.11",
            ),
        ]
        print(f"  try P0.10 wrap y={wy} col={col}", flush=True)
        if try_sized(r, "P0.10", hops, routes):
            return True
    BLOCKERS["P0.10"] = BLOCKERS.get("P0.10") or "wrap blocked"
    return False


def route_p011(r):
    print("== P0.11 existing via, F-hop COEX2 H, west wrap ==", flush=True)
    for wy, col in ((47.50, 28.20), (52.00, 29.10), (48.20, 24.90)):
        a, b1, b2, b3 = wrap_jumps(wy)
        hops = [
            (51.80, 28.00, 0.45, 0.25),
            (51.80, 32.20, 0.50, 0.30),
            (51.80, 34.20, 0.50, 0.30),
            (51.80, wy, 0.50, 0.30),
            (b1[0], b1[1], 0.50, 0.30),
            (b2[0], b2[1], 0.50, 0.30),
            (b3[0], b3[1], 0.50, 0.30),
        ]
        routes = [
            ([(48.62, 28.00), (51.80, 28.00)], B, 0.18, "B east"),
            ([(51.80, 28.00), (51.80, 32.20)], B, 0.18, "B to COEX2"),
            ([(51.80, 32.20), (51.80, 34.20)], F, 0.18, "F hop COEX2 H y=33.20"),
            ([(51.80, 34.20), (51.80, wy), a], B, 0.18, "B south then west"),
            ([a, b1], F, 0.18, "F COEX0"),
            ([b1, b2], B, 0.18, "B mid"),
            ([b2, b3], F, 0.18, "F P0.15"),
            (
                [b3, (col, wy), (col, 77.20), (33.94, 77.20), (33.94, 76.00)],
                B,
                0.18,
                f"B col x={col} J12.12",
            ),
        ]
        print(f"  try P0.11 wrap y={wy} col={col}", flush=True)
        if try_sized(r, "P0.11", hops, routes):
            return True
    BLOCKERS["P0.11"] = BLOCKERS.get("P0.11") or "COEX2 hop/wrap blocked"
    return False


def route_p012(r):
    print("== P0.12 existing via west wrap ==", flush=True)
    for wy, col in ((47.50, 28.20), (52.00, 28.20)):
        a, b1, b2, b3 = wrap_jumps(wy)
        hops = [
            (51.40, 27.50, 0.45, 0.25),
            (51.40, 32.20, 0.50, 0.30),
            (51.40, 34.20, 0.50, 0.30),
            (51.40, wy, 0.50, 0.30),
            (b1[0], b1[1], 0.50, 0.30),
            (b2[0], b2[1], 0.50, 0.30),
            (b3[0], b3[1], 0.50, 0.30),
        ]
        routes = [
            ([(47.40, 27.50), (51.40, 27.50)], B, 0.18, "B east of P0.11"),
            ([(51.40, 27.50), (51.40, 32.20)], B, 0.18, "B south"),
            ([(51.40, 32.20), (51.40, 34.20)], F, 0.18, "F hop COEX2"),
            ([(51.40, 34.20), (51.40, wy), a], B, 0.18, "B south then west"),
            ([a, b1], F, 0.18, "F COEX0"),
            ([b1, b2], B, 0.18, "B mid"),
            ([b2, b3], F, 0.18, "F P0.15"),
            (
                [b3, (col, wy), (col, 77.20), (36.48, 77.20), (36.48, 76.00)],
                B,
                0.18,
                f"B col x={col} J12.13",
            ),
        ]
        print(f"  try P0.12 wrap y={wy} col={col}", flush=True)
        if try_sized(r, "P0.12", hops, routes):
            return True
    BLOCKERS["P0.12"] = BLOCKERS.get("P0.12") or "wrap blocked"
    return False


def route_j13_east(r, name, jx):
    """East private column x≥64.6 from an existing U1 via. Short stubs only."""
    print(f"== {name} J13 east column x>=64.6 ==", flush=True)
    u1v = [
        v
        for v in r.vias
        if v["n"] == name and 28.0 <= v["x"] <= 55.0 and 20.0 <= v["y"] <= 48.0
    ]
    if not u1v:
        BLOCKERS[name] = "no existing U1 via"
        return False
    v0 = min(u1v, key=lambda v: hypot(v["x"], v["y"], r.u1(name)["x"], r.u1(name)["y"]))
    for col in (64.80, 65.50, 66.30, 67.20):
        for wy in (70.70, 72.80, 73.40, 77.20):
            hops = [(col, v0["y"], 0.50, 0.30), (col, wy, 0.50, 0.30)]
            routes = [
                ([(v0["x"], v0["y"]), (col, v0["y"])], B, 0.18, f"B east to x={col}"),
                ([(col, v0["y"]), (col, wy)], B, 0.18, f"B east col to y={wy}"),
                ([(col, wy), (jx, wy), (jx, 76.00)], B, 0.18, f"stub J13 {name}"),
            ]
            # ADC may enter J18_BOX; skip extra hops. Keep path short.
            L = abs(col - v0["x"]) + abs(wy - v0["y"]) + abs(jx - col) + abs(76.00 - wy)
            if L > 90:
                continue
            print(f"  try {name} via ({v0['x']:.2f},{v0['y']:.2f}) col={col} y={wy} L={L:.1f}", flush=True)
            if try_sized(r, name, hops, routes):
                return True
    BLOCKERS[name] = BLOCKERS.get(name) or "east column blocked"
    return False


def write_release(n0, n1, shorts, counts, pairs, log, board, remaining_j12, dang, nvia0, nvia1):
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
        f.write(f"| Vias | {nvia} (start {nvia0}) |\n")
        f.write("| U1 | (36.0, 32.0) mm, rot 180° |\n")
        f.write("| SIM_DET U1 pad 45 net | `''` (must stay empty) |\n")
        f.write("| Backup | `.mcp-backups/final-fab-20260917-194911/` |\n")
        f.write("| Live snapshot after this pass | `after-pass25.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass25-start.kicad_pcb` |\n\n")
        f.write("## This pass (combined via + west wrap)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 83. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 east replacement not ripped. ")
        f.write(f"New vias this pass: {nvia1 - nvia0}. Dangling new vias: {len(dang)}.\n\n")
        f.write(f"**J12/J13 nets closed:** {', '.join(CLOSED) if CLOSED else 'none'}\n\n")
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


def run_one(board, r, name, fn, last, ceiling, last_pairs, header, note0):
    if not j12_open(last_pairs, name):
        NET_LOG.append((name, "skip", f"{header} not in DRC pairs"))
        return board, r, last, ceiling, last_pairs
    print(f"\n#### {name} {header}", flush=True)
    before = ceiling
    before_snap = last
    board, r, last, ok, ceiling, new_pairs = apply_net(board, r, name, fn, last, ceiling)
    if new_pairs is not None:
        last_pairs = new_pairs
    still = j12_open(last_pairs, name)
    if ok and still:
        print(f"  J12/J13 still open for {name}; rollback copper (no dangles)", flush=True)
        shutil.copy2(before_snap, BOARD)
        last = before_snap
        ceiling = before
        board, r = reload()
        last_pairs, nchk, _, _ = run_drc()
        ceiling = nchk
        ok = False
        BLOCKERS[name] = BLOCKERS.get(name) or "copper placed but pair still open"
    if ok and not still:
        CLOSED.append(f"{name} {header}")
        st = f"closed ({before}→{ceiling})"
    elif ok:
        st = f"not closed (unconn {before}→{ceiling})"
    else:
        st = "rolled back" if before_snap == last else "not closed (DRC revert or blocked)"
        if not ok:
            st = "rolled back"
    extra = BLOCKERS.get(name, "")
    note = note0 + (f". blocker: `{extra}`" if extra else "")
    NET_LOG.append((name, st, note))
    print(f"  {st}", flush=True)
    return board, r, last, ceiling, last_pairs


def main():
    start = snap_path("pass25-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 83:
        print(f"start {n0}>83 abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    nvia0 = count_vias(board)
    vias0 = via_xy_set(board)
    last_pairs = pairs

    jobs = [
        ("P0.04", route_p004, "J12.5", "combined 0.50 via (42.25,40.30)+west wrap x=27.70"),
        ("P0.09", route_p009, "J12.10", "combined extra via + west wrap"),
        ("P0.05", route_p005, "J12.6", "around P0.06 island then west wrap"),
        ("P0.07", route_p007, "J12.8", "around P0.06 island then west wrap"),
        ("P0.10", route_p010, "J12.11", "F-hop COEX2 then west wrap"),
        ("P0.11", route_p011, "J12.12", "F-hop COEX2 then west wrap"),
        ("P0.12", route_p012, "J12.13", "F-hop COEX2 then west wrap"),
    ]
    for name, fn, header, note0 in jobs:
        board, r, last, ceiling, last_pairs = run_one(
            board, r, name, fn, last, ceiling, last_pairs, header, note0
        )

    # J13 nets with an existing U1 via — east column, short stubs, no second U1 escape.
    j13 = [
        ("P0.21", 76.70),
        ("P0.22", 79.24),
        ("P0.23", 81.78),
        ("P0.25", 86.86),
        ("P0.26", 89.40),
        ("P0.28", 94.48),
        ("P0.30", 99.56),
        ("P0.31", 102.10),
    ]
    for name, jx in j13:
        def fn(rr, _n=name, _x=jx):
            return route_j13_east(rr, _n, _x)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            f"J13 east x>=64.6",
            "existing U1 via, east private column, short stub",
        )

    shutil.copy2(BOARD, snap_path("pass25"))
    board, r = reload()
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0) or 0
    if shorts or n1 > n0:
        print(f"FINISH abort shorts={shorts} unconn={n1}>{n0}; restore start")
        shutil.copy2(start, BOARD)
        return 3
    dang = dangling_new(board, vias0)
    nvia1 = count_vias(board)
    print(f"dangling new vias: {dang}", flush=True)
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    rem = remaining_j12_lines(pairs)
    write_release(n0, n1, shorts, counts, pairs, NET_LOG, board, rem, dang, nvia0, nvia1)
    print(
        f"END unconn={n1} shorts={shorts} closed={CLOSED} "
        f"vias {nvia0}->{nvia1} dang={len(dang)} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
