#!/usr/bin/env python3
"""Pass 27: U1-to-existing-B islands + P0.06 J9 duplicate from J12 copper.

LIVE. Ceiling finish ≤81. No /fab unless unconnected=0 AND ratsnest=0.
Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 /
P0.04 wrap+J9. Do not retry J13 east x=66/72/80 or P0.05/07/09/10/11/12 west wrap.
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
    waypoint_route,
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
DUP_BRANCHED = []

ADC_XS = [
    25.80, 26.20, 26.70, 27.70, 28.80, 30.00, 31.00, 32.20, 33.00, 34.50,
    36.50, 38.00, 40.25, 40.70, 41.75, 42.75, 43.08, 44.50, 45.62, 47.00,
    48.16, 50.70, 53.24, 55.78, 60.00, 70.00, 90.00, 108.00,
]
ADC_YS = [
    16.50, 17.50, 19.00, 20.80, 22.50, 23.10, 24.00, 27.20, 30.80, 34.50,
    40.50, 43.50, 46.80, 50.00, 54.00, 58.80, 59.20, 61.20, 62.00, 72.80, 74.00,
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
    placed = fn(r)
    r.collect()
    if not placed:
        print(f"  no copper for {name}", flush=True)
        return board, r, last, False, ceiling, None
    got = check(r.board, r, f"pass27-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass27-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def pair_open(pairs, name, pred):
    for p in pairs:
        if p["net"] != name:
            continue
        if pred(p):
            return True
    return False


def u1_open(pairs, name):
    """True if any DRC pair for this net still names a U1 pad or U1-side track."""
    def pred(p):
        blob = p.get("a", "") + p.get("b", "")
        return "of U1" in blob or (blob.count("Track [") >= 1 and "Pad " in blob)

    return pair_open(pairs, name, pred)


def header_open(pairs, name, tag):
    def pred(p):
        return tag in (p.get("a", "") + p.get("b", ""))

    return pair_open(pairs, name, pred)


def nearest_b_end(r, name, x, y):
    best = None
    bd = 1e9
    for t in r.tracks:
        if t["n"] != name or t["ly"] != B:
            continue
        for px, py in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            d = hypot(px, py, x, y)
            if d < bd:
                bd = d
                best = (px, py, d)
    return best


def pad_f_to_via(r, p, vx, vy, name):
    px, py = p["x"], p["y"]
    cands = [
        [(px, py), (px, vy), (vx, vy)],
        [(px, py), (vx, py), (vx, vy)],
        [(px, py), (px, 24.60), (vx, 24.60), (vx, vy)],
        [(px, py), (px, 25.00), (vx, 25.00), (vx, vy)],
    ]
    return next((pts for pts in cands if r.path_clear(pts, F, 0.18, name)), None)


def existing_u1_via(r, name, p):
    best = None
    bd = 8.0
    for v in r.vias:
        if v["n"] != name:
            continue
        d = hypot(v["x"], v["y"], p["x"], p["y"])
        if d < bd and r.pad_reaches_via(p, v, name):
            bd = d
            best = v
    return best


def route_u1_to_existing_b(r, name):
    """Combined extra via (if needed) + B to existing same-net island."""
    print(f"== {name} U1 to existing B island ==", flush=True)
    p = r.u1(name)
    if not p:
        BLOCKERS[name] = "no U1 pad"
        return False
    island = nearest_b_end(r, name, p["x"], p["y"])
    if not island:
        BLOCKERS[name] = "no B island"
        return False
    bx, by, dist = island
    print(f"  island ({bx:.2f},{by:.2f}) d={dist:.2f}", flush=True)

    ev = existing_u1_via(r, name, p)
    attempts = []
    if ev:
        attempts.append((ev["x"], ev["y"], None, None, None))
        print(f"  existing via ({ev['x']:.2f},{ev['y']:.2f})", flush=True)

    for vx, vy in extra_via_sites(p, name) + [
        (p["x"], 19.00),
        (p["x"], 24.00),
        (p["x"] + 1.50, 24.60),
        (p["x"] - 1.50, 24.60),
        (44.50, 19.00),
        (47.00, 19.00),
    ]:
        vx, vy = round(vx, 2), round(vy, 2)
        size, drill = 0.50, 0.30
        w = r.via_why(vx, vy, name, size=size, drill=drill)
        if w is not None:
            size, drill = 0.45, 0.25
            w = r.via_why(vx, vy, name, size=size, drill=drill)
            if w is not None:
                continue
        fpath = pad_f_to_via(r, p, vx, vy, name)
        if ev and hypot(vx, vy, ev["x"], ev["y"]) < 0.20:
            fpath = [(ev["x"], ev["y"]), (vx, vy)] if r.path_clear([(ev["x"], ev["y"]), (vx, vy)], F, 0.18, name) else fpath
        if not fpath:
            continue
        attempts.append((vx, vy, size, drill, fpath))

    for vx, vy, size, drill, fpath in attempts:
        path, cost = waypoint_route(r, vx, vy, bx, by, B, 0.18, name, xs=ADC_XS, ys=ADC_YS)
        if path is None or cost > 120:
            b_cands = [
                [(vx, vy), (bx, vy), (bx, by)],
                [(vx, vy), (vx, by), (bx, by)],
                [(vx, vy), (vx, 22.50), (36.50, 22.50), (36.50, 27.20), (34.50, 27.20), (34.50, 30.80), (32.20, 30.80), (32.20, 59.20), (bx, 59.20), (bx, by)],
                [(vx, vy), (27.70, vy), (27.70, 59.20), (bx, 59.20), (bx, by)],
            ]
            path = next((pts for pts in b_cands if r.path_clear(pts, B, 0.18, name)), None)
            if not path:
                continue
        hops = []
        routes = []
        if size is not None:
            hops.append((vx, vy, size, drill))
            routes.append((fpath, F, 0.18, "F pad-via"))
        routes.append((path, B, 0.18, f"B to island L={hypot(vx, vy, bx, by):.1f}"))
        print(f"  try via ({vx:.2f},{vy:.2f}) B n={len(path)}", flush=True)
        if try_sized(r, name, hops, routes):
            return True
    sample = [(p["x"], p["y"] - 2.15), (bx, p["y"] - 2.15), (bx, by)]
    BLOCKERS[name] = BLOCKERS.get(name) or why(r, sample, B, 0.18, name)
    print(f"  blocker {BLOCKERS[name]}", flush=True)
    return False


def route_p006_j9(r):
    print("== P0.06 J9.1 branch from J12 wrap copper (no second U1 escape) ==", flush=True)
    if try_sized(
        r,
        "P0.06",
        [
            (14.90, 77.80, 0.50, 0.30),
            (115.50, 55.50, 0.50, 0.30),
            (107.40, 47.20, 0.50, 0.30),
            (113.20, 36.00, 0.50, 0.30),
        ],
        [
            ([(21.24, 74.00), (14.90, 74.00), (14.90, 77.80)], B, 0.18, "B from J12 island west of P0.04 stub"),
            (
                [(14.90, 77.80), (14.90, 79.20), (115.50, 79.20), (115.50, 55.50)],
                F,
                0.18,
                "F y=79.20 east of P0.04 y=78.80 then drop",
            ),
            ([(115.50, 55.50), (107.40, 55.50), (107.40, 47.20)], B, 0.18, "B west of VDD_GPIO F y=51.08"),
            (
                [(107.40, 47.20), (113.20, 47.20), (113.20, 36.00)],
                F,
                0.18,
                "F hop P0.04 H y=49.20",
            ),
            (
                [
                    (113.20, 36.00),
                    (113.20, 22.00),
                    (106.35, 22.00),
                    (106.35, 14.50),
                    (114.50, 14.50),
                    (114.50, 8.40),
                    (116.00, 8.40),
                    (116.00, 8.00),
                ],
                B,
                0.18,
                "B jog x=106.35 between P0.15 and P0.04 to J9.1",
            ),
        ],
    ):
        return True
    BLOCKERS["P0.06"] = BLOCKERS.get("P0.06") or "J9 branch blocked"
    return False


def route_p011_f(r):
    print("== P0.11 4.62 mm F hop to existing via island ==", flush=True)
    p = r.u1("P0.11")
    if not p:
        BLOCKERS["P0.11"] = "no U1 pad"
        return False
    cands = [
        [(44.00, 28.00), (48.62, 28.00)],
        [(44.00, 28.00), (44.00, 26.40), (48.62, 26.40), (48.62, 28.00)],
        [(44.00, 28.00), (45.15, 28.00), (45.15, 26.20), (48.62, 26.20), (48.62, 28.00)],
        [(44.00, 28.00), (44.00, 29.60), (48.62, 29.60), (48.62, 28.00)],
    ]
    for pts in cands:
        if try_sized(r, "P0.11", [], [(pts, F, 0.18, "F hop to via island")]):
            return True
    BLOCKERS["P0.11"] = BLOCKERS.get("P0.11") or why(r, cands[0], F, 0.18, "P0.11")
    return False


def short_f_hop(r, name, a, b, limit=5.0):
    d = hypot(a[0], a[1], b[0], b[1])
    print(f"== {name} F leftover {d:.2f} mm ==", flush=True)
    if d > limit:
        BLOCKERS[name] = f"{d:.2f} mm > {limit} mm, skip long bus"
        print(f"  skip {BLOCKERS[name]}", flush=True)
        return False
    cands = [
        [a, b],
        [a, (b[0], a[1]), b],
        [a, (a[0], b[1]), b],
    ]
    for pts in cands:
        if try_sized(r, name, [], [(pts, F, 0.18, f"F {d:.2f} mm hop")]):
            return True
    BLOCKERS[name] = BLOCKERS.get(name) or why(r, cands[0], F, 0.18, name)
    return False


def run_one(board, r, name, fn, last, ceiling, last_pairs, still_fn, note0, kind="hop"):
    if not still_fn(last_pairs, name):
        NET_LOG.append((name, "skip", "pair not in DRC"))
        return board, r, last, ceiling, last_pairs
    print(f"\n#### {name} {kind}", flush=True)
    before = ceiling
    before_snap = last
    board, r, last, ok, ceiling, new_pairs = apply_net(board, r, name, fn, last, ceiling)
    if new_pairs is not None:
        last_pairs = new_pairs
    still = still_fn(last_pairs, name)
    if ok and still:
        print(f"  pair still open for {name}; rollback copper", flush=True)
        shutil.copy2(before_snap, BOARD)
        last = before_snap
        board, r = reload()
        last_pairs, nchk, _, _ = run_drc()
        ceiling = nchk
        ok = False
        BLOCKERS[name] = BLOCKERS.get(name) or "copper placed but pair still open"
    if ok and not still:
        CLOSED.append(f"{name} {kind}")
        st = f"closed ({before}→{ceiling})"
    else:
        st = "rolled back"
    extra = BLOCKERS.get(name, "")
    note = note0 + (f". blocker: `{extra}`" if extra else "")
    NET_LOG.append((name, st, note))
    print(f"  {st}", flush=True)
    return board, r, last, ceiling, last_pairs


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
        f.write("| Live snapshot after this pass | `after-pass27.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass27-start.kicad_pcb` |\n\n")
        f.write("## This pass (U1-to-existing-B + P0.06 J9 duplicate)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 81. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 / P0.04 wrap+J9 not ripped. ")
        f.write(f"New vias this pass: {nvia1 - nvia0}. Dangling new vias: {len(dang)}.\n\n")
        f.write(f"**Nets closed:** {', '.join(CLOSED) if CLOSED else 'none'}\n\n")
        f.write(f"**Duplicates branched:** {', '.join(DUP_BRANCHED) if DUP_BRANCHED else 'none'}\n\n")
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            f.write(f"| {name} | {status} — {note} |\n")
        f.write("\n## Remaining U1-to-island / J12/J13\n\n")
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


def remaining_lines(pairs):
    out = []
    for p in sorted(pairs, key=lambda x: (x["net"], x.get("a", ""))):
        blob = p.get("a", "") + p.get("b", "")
        interesting = (
            "of U1" in blob
            or "J12" in blob
            or "J13" in blob
            or "J9" in blob
            or "Track [" in blob
        )
        if not interesting:
            continue
        d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
        why_s = BLOCKERS.get(p["net"], "")
        extra = f" — {why_s}" if why_s else ""
        out.append(
            f"{p['net']} {p['cls']} {d:.3f} mm "
            f"({p['ax']:.2f},{p['ay']:.2f})–({p['bx']:.2f},{p['by']:.2f}){extra}"
        )
    return out[:40]


def main():
    start = snap_path("pass27-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 81:
        print(f"start {n0}>81 abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    nvia0 = p25.count_vias(board)
    vias0 = p25.via_xy_set(board)
    last_pairs = pairs

    for name in ("P0.13", "P0.14", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20"):

        def fn(rr, _n=name):
            return route_u1_to_existing_b(rr, _n)

        def still(ps, n, _n=name):
            return u1_open(ps, _n)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            still,
            "U1 pad to existing same-net B",
            kind="U1-B",
        )

    def still_j9(ps, n):
        return header_open(ps, n, "J9")

    board, r, last, ceiling, last_pairs = run_one(
        board,
        r,
        "P0.06",
        route_p006_j9,
        last,
        ceiling,
        last_pairs,
        still_j9,
        "branch from J12 wrap; F y=79.20; B jog x=106.35 to J9.1",
        kind="J9",
    )
    if any(x.startswith("P0.06") for x in CLOSED):
        DUP_BRANCHED.append("P0.06 J9 from J12")

    def still_p011(ps, n):
        return u1_to_copper_open(ps, n) or header_open(ps, n, "Track [P0.11] on F.Cu")

    board, r, last, ceiling, last_pairs = run_one(
        board,
        r,
        "P0.11",
        route_p011_f,
        last,
        ceiling,
        last_pairs,
        lambda ps, n: any(
            p["net"] == "P0.11" and hypot(p["ax"], p["ay"], p["bx"], p["by"]) < 6.0 for p in ps
        ),
        "4.62 mm F hop to via (48.62,28.00)",
        kind="F-hop",
    )

    f_jobs = [
        ("P0.08", (78.375, 26.00), (46.20, 30.00)),
        ("VIN_FILT", (55.35, 13.30), (53.20, 21.90)),
        ("VIN_F", (48.00, 12.60), (71.20, 19.06)),
        ("nRESET", (101.68, 26.00), (52.22, 10.80)),
        ("SIM_CLK", (31.25, 26.75), (70.90, 45.50)),
    ]
    for name, a, b in f_jobs:

        def fn(rr, _n=name, _a=a, _b=b):
            return short_f_hop(rr, _n, _a, _b, limit=5.0)

        def still(ps, n, _n=name):
            return any(p["net"] == _n and p.get("cls") == "F" for p in ps)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            still,
            "F leftover only if ≤5 mm",
            kind="F",
        )

    shutil.copy2(BOARD, snap_path("pass27"))
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
    rem = remaining_lines(pairs)
    write_release(n0, n1, shorts, counts, pairs, NET_LOG, board, rem, dang, nvia0, nvia1)
    print(
        f"END unconn={n1} shorts={shorts} closed={CLOSED} dups={DUP_BRANCHED} "
        f"vias {nvia0}->{nvia1} dang={len(dang)} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
