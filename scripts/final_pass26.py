#!/usr/bin/env python3
"""Pass 26: P0.04 J9 branch from J12 copper; untried J12/J13 combined via+route.

LIVE. Ceiling finish ≤82. No /fab unless unconnected=0 AND ratsnest=0.
Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 east /
P0.04 wrap. Do not retry P0.05/07/09/10/11/12 or last J13-east x>=64.6 style.
"""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, fill_zones, run_drc  # noqa: E402
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
from final_pass21 import leftover_f  # noqa: E402
import final_pass21 as p21  # noqa: E402
from final_pass22 import extra_via_sites  # noqa: E402
import final_pass24 as p24  # noqa: E402
from final_pass24 import try_sized  # noqa: E402
import final_pass25 as p25  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
p24.BLOCKERS = BLOCKERS
p25.BLOCKERS = BLOCKERS
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
    got = check(r.board, r, f"pass26-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass26-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def header_open(pairs, name, tag):
    for p in pairs:
        if p["net"] != name:
            continue
        blob = p.get("a", "") + p.get("b", "")
        if tag in blob:
            return True
    return False


def route_p004_j9(r):
    print("== P0.04 J9.4 branch from J12 wrap copper (no second U1 escape) ==", flush=True)
    if try_sized(
        r,
        "P0.04",
        [
            (27.70, 77.20, 0.50, 0.30),
            (108.45, 52.50, 0.50, 0.30),
            (108.45, 49.20, 0.50, 0.30),
            (113.80, 36.80, 0.50, 0.30),
        ],
        [
            (
                [
                    (27.70, 77.20),
                    (27.70, 78.80),
                    (114.80, 78.80),
                    (114.80, 52.50),
                    (108.45, 52.50),
                ],
                F,
                0.18,
                "F y=78.80 past P0.01 stub then jog west of VDD_GPIO F y=51.08",
            ),
            ([(108.45, 52.50), (108.45, 49.20)], B, 0.18, "B J13.18-19 gap through y=51.08"),
            (
                [(108.45, 49.20), (113.80, 49.20), (113.80, 36.80)],
                F,
                0.18,
                "F east hop VDD_GPIO B V then through y=38",
            ),
            (
                [
                    (113.80, 36.80),
                    (113.80, 19.43),
                    (106.70, 19.43),
                    (106.70, 16.80),
                    (116.00, 16.80),
                    (116.00, 15.62),
                ],
                B,
                0.18,
                "B hop y=31.08 and y=18.16 to J9.4",
            ),
        ],
    ):
        return True
    BLOCKERS["P0.04"] = BLOCKERS.get("P0.04") or "J9 branch blocked"
    return False


def route_to_existing_b(r, name, bx, by, header):
    """Combined extra via + B to existing header copper."""
    print(f"== {name} combined via to existing B ({bx:.2f},{by:.2f}) {header} ==", flush=True)
    p = r.u1(name)
    if not p:
        BLOCKERS[name] = "no U1 pad"
        return False
    for vx, vy in extra_via_sites(p, name) + [
        (p["x"] + 1.20, p["y"] - 2.15),
        (p["x"] - 1.20, p["y"] - 2.15),
        (p["x"], p["y"] - 2.15),
        (p["x"] + 1.80, p["y"] - 1.50),
        (bx, p["y"] - 2.15),
    ]:
        size, drill = 0.50, 0.30
        w = r.via_why(vx, vy, name, size=size, drill=drill)
        if w is not None:
            size, drill = 0.45, 0.25
            w = r.via_why(vx, vy, name, size=size, drill=drill)
            if w is not None:
                continue
        f_cands = [
            [(p["x"], p["y"]), (p["x"], vy), (vx, vy)],
            [(p["x"], p["y"]), (vx, p["y"]), (vx, vy)],
        ]
        fpath = next((pts for pts in f_cands if r.path_clear(pts, F, 0.18, name)), None)
        if not fpath:
            continue
        b_cands = [
            [(vx, vy), (bx, vy), (bx, by)],
            [(vx, vy), (vx, by), (bx, by)],
            [(vx, vy), (vx, 24.50), (bx, 24.50), (bx, by)],
            [(vx, vy), (38.00, vy), (38.00, by), (bx, by)],
        ]
        bpath = next((pts for pts in b_cands if r.path_clear(pts, B, 0.18, name)), None)
        if not bpath:
            continue
        print(f"  try {name} via ({vx:.2f},{vy:.2f})", flush=True)
        if try_sized(
            r,
            name,
            [(vx, vy, size, drill)],
            [(fpath, F, 0.18, "F pad-via"), (bpath, B, 0.18, "B to existing header")],
        ):
            return True
    BLOCKERS[name] = BLOCKERS.get(name) or "no via+B to existing header"
    return False


def route_j13_east_col(r, name, jx, cols=(66.00, 72.00, 80.00)):
    print(f"== {name} combined via + east column {cols} to J13 ({jx:.2f},76) ==", flush=True)
    p = r.u1(name)
    if not p:
        BLOCKERS[name] = "no U1 pad"
        return False
    existing = [
        v
        for v in r.vias
        if v["n"] == name and hypot(v["x"], v["y"], p["x"], p["y"]) < 5.0
    ]
    via_cands = [(v["x"], v["y"], None, None) for v in existing]
    for xy in extra_via_sites(p, name):
        via_cands.append((xy[0], xy[1], 0.50, 0.30))
    for vx, vy, size, drill in via_cands:
        new_via = size is not None
        if new_via:
            w = r.via_why(vx, vy, name, size=size, drill=drill)
            if w is not None:
                w = r.via_why(vx, vy, name, size=0.45, drill=0.25)
                if w is not None:
                    continue
                size, drill = 0.45, 0.25
            f_cands = [
                [(p["x"], p["y"]), (p["x"], vy), (vx, vy)],
                [(p["x"], p["y"]), (vx, p["y"]), (vx, vy)],
            ]
            fpath = next((pts for pts in f_cands if r.path_clear(pts, F, 0.18, name)), None)
            if not fpath:
                continue
        else:
            fpath = None
        for col in cols:
            for wy in (70.70, 72.80, 77.20):
                hops = []
                routes = []
                if new_via:
                    hops.append((vx, vy, size, drill))
                    routes.append((fpath, F, 0.18, "F pad-via"))
                hops += [(col, vy, 0.50, 0.30), (col, wy, 0.50, 0.30)]
                routes += [
                    ([(vx, vy), (col, vy)], B, 0.18, f"B east to x={col}"),
                    ([(col, vy), (col, wy)], B, 0.18, f"B col to y={wy}"),
                    ([(col, wy), (jx, wy), (jx, 76.00)], B, 0.18, "stub J13"),
                ]
                print(f"  try {name} via ({vx:.2f},{vy:.2f}) col={col} y={wy}", flush=True)
                if try_sized(r, name, hops, routes):
                    return True
    BLOCKERS[name] = BLOCKERS.get(name) or "east col 66/72/80 blocked"
    return False


def write_release(n0, n1, shorts, counts, pairs, log, board, remaining, dang, nvia0, nvia1):
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
        f.write("| Live snapshot after this pass | `after-pass26.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass26-start.kicad_pcb` |\n\n")
        f.write("## This pass (P0.04 J9 + untried J12/J13)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 82. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 / P0.04 wrap not ripped. ")
        f.write(f"New vias this pass: {nvia1 - nvia0}. Dangling new vias: {len(dang)}.\n\n")
        f.write(f"**Nets closed:** {', '.join(CLOSED) if CLOSED else 'none'}\n\n")
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            f.write(f"| {name} | {status} — {note} |\n")
        f.write("\n## Remaining J12/J13 still open\n\n")
        if remaining:
            for line in remaining:
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


def run_one(board, r, name, fn, last, ceiling, last_pairs, tag, note0):
    if not header_open(last_pairs, name, tag):
        NET_LOG.append((name, "skip", f"{tag} not in DRC pairs"))
        return board, r, last, ceiling, last_pairs
    print(f"\n#### {name} {tag}", flush=True)
    before = ceiling
    before_snap = last
    board, r, last, ok, ceiling, new_pairs = apply_net(board, r, name, fn, last, ceiling)
    if new_pairs is not None:
        last_pairs = new_pairs
    still = header_open(last_pairs, name, tag)
    if ok and still:
        print(f"  {tag} still open for {name}; rollback copper", flush=True)
        shutil.copy2(before_snap, BOARD)
        last = before_snap
        board, r = reload()
        last_pairs, nchk, _, _ = run_drc()
        ceiling = nchk
        ok = False
        BLOCKERS[name] = BLOCKERS.get(name) or "copper placed but pair still open"
    if ok and not still:
        CLOSED.append(f"{name} {tag}")
        st = f"closed ({before}→{ceiling})"
    else:
        st = "rolled back"
    extra = BLOCKERS.get(name, "")
    note = note0 + (f". blocker: `{extra}`" if extra else "")
    NET_LOG.append((name, st, note))
    print(f"  {st}", flush=True)
    return board, r, last, ceiling, last_pairs


def main():
    start = snap_path("pass26-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 82:
        print(f"start {n0}>82 abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    nvia0 = p25.count_vias(board)
    vias0 = p25.via_xy_set(board)
    last_pairs = pairs

    board, r, last, ceiling, last_pairs = run_one(
        board,
        r,
        "P0.04",
        route_p004_j9,
        last,
        ceiling,
        last_pairs,
        "J9",
        "branch from J12 wrap at (27.70,77.20); F y=78.80 then east hops",
    )

    for name, bx, by, tag in (
        ("P0.14", 40.54, 62.00, "J18"),
        ("P0.16", 45.62, 62.00, "J18"),
        ("P0.18", 50.70, 62.00, "J18"),
    ):

        def fn(rr, _n=name, _x=bx, _y=by, _t=tag):
            return route_to_existing_b(rr, _n, _x, _y, _t)

        board, r, last, ceiling, last_pairs = run_one(
            board, r, name, fn, last, ceiling, last_pairs, tag, "combined via to existing J18 B"
        )

    j13 = [
        ("P0.24", 84.32),
        ("P0.27", 91.94),
        ("P0.29", 97.02),
        ("P0.31", 102.10),
        ("P0.19", 71.62),
        ("P0.20", 74.16),
    ]
    for name, jx in j13:

        def fn(rr, _n=name, _x=jx):
            return route_j13_east_col(rr, _n, _x)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            "J13",
            "combined via + east column x=66/72/80",
        )

    shutil.copy2(BOARD, snap_path("pass26"))
    board, r = reload()
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0) or 0
    if shorts or n1 > n0:
        print(f"FINISH abort shorts={shorts} unconn={n1}>{n0}; restore start")
        shutil.copy2(start, BOARD)
        return 3
    dang = p25.dangling_new(board, vias0)
    nvia1 = p25.count_vias(board)
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
