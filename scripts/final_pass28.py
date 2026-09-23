#!/usr/bin/env python3
"""Pass 28: COEX2 remnant add-then-delete, then U1-to-existing-B hops.

LIVE. Ceiling finish ≤80. No /fab unless unconnected=0 AND ratsnest=0.
Do not rip VDD2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 / P0.04 / P0.06.
Do not delete COEX2 east remnant x=72–105.10 unless needed.
Skip P0.05/07/09/10/11/12 west wrap. Skip VIN/nRESET/SIM_CLK long buses.
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
import final_pass27 as p27  # noqa: E402

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
p24.BLOCKERS = BLOCKERS
p25.BLOCKERS = BLOCKERS
p27.BLOCKERS = BLOCKERS
CLOSED = []
NET_LOG = []
DUP_BRANCHED = []
COEX2_REMOVED = []
JOIN = [(37.75, 33.20), (40.50, 33.20)]

ADC_XS = [
    32.20, 34.50, 36.50, 38.00, 39.25, 40.25, 40.54, 40.70, 41.25, 41.75,
    42.25, 42.75, 43.08, 44.50, 45.62, 47.00, 48.16, 50.70, 53.24, 55.78,
]
ADC_YS = [
    19.00, 20.80, 23.10, 23.95, 24.80, 25.20, 25.80, 27.20, 30.80, 34.50,
    40.50, 46.80, 50.00, 54.00, 58.80, 59.20, 61.20, 62.00, 72.80, 74.00,
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


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)


def near(a, b, tol=0.20):
    return abs(a - b) < tol


def overlaps(a0, a1, b0, b1, tol=0.20):
    lo, hi = min(a0, a1), max(a0, a1)
    blo, bhi = min(b0, b1), max(b0, b1)
    return hi >= blo - tol and lo <= bhi + tol


def delete_coex2_remnants(board, r):
    """Delete west H y=24.60 x=37.75–48 and wrap V x=40.50 y=24.60–33.20.
    Shorten U1 V x=37.75 so it stops at y=33.20. Keep east H x=72–105.10.
    """
    removed = []
    shorten = None
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "COEX2" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        w = pcbnew.ToMM(tr.GetWidth())
        # West remnant H y=24.60 overlapping 37.75–48, not the east run x>=72.
        if near((y1 + y2) / 2, 24.60) and abs(y1 - y2) < 0.30:
            if max(x1, x2) < 70.0 and overlaps(x1, x2, 37.75, 48.00):
                print(f"  DEL H ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})", flush=True)
                removed.append((x1, y1, x2, y2, w, "H"))
                board.Remove(tr)
                continue
        # Wrap start V x=40.50 y=24.60–33.20
        if near((x1 + x2) / 2, 40.50) and abs(x1 - x2) < 0.30:
            if overlaps(y1, y2, 24.60, 33.20) and min(y1, y2) < 30.0:
                print(f"  DEL V ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})", flush=True)
                removed.append((x1, y1, x2, y2, w, "V"))
                board.Remove(tr)
                continue
        # U1 column V x=37.75 that reaches y=24.60 — shorten to y=33.20
        if near((x1 + x2) / 2, 37.75) and abs(x1 - x2) < 0.30:
            if min(y1, y2) < 26.0 and max(y1, y2) > 38.0:
                print(
                    f"  SHORTEN V ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f}) -> y=33.20",
                    flush=True,
                )
                shorten = (x1, y1, x2, y2, w)
                board.Remove(tr)
                continue
    if shorten:
        r.add_track(37.75, 41.10, 37.75, 33.20, B, 0.18, r.code_of("COEX2"), "COEX2")
        print("  ADD shortened V (37.75,41.10)-(37.75,33.20)", flush=True)
    r.collect()
    return removed, shorten


def island_open(pairs, name):
    for p in pairs:
        if p["net"] != name:
            continue
        a, b = p.get("a", ""), p.get("b", "")
        blob = a + b
        if "of U1" in blob:
            return True
        if "Track [" in a and "Track [" in b:
            return True
    return False


def header_open(pairs, name, tag):
    for p in pairs:
        if p["net"] != name:
            continue
        if tag in (p.get("a", "") + p.get("b", "")):
            return True
    return False


def b_candidates(vx, vy, bx, by):
    return [
        [(vx, vy), (vx, by), (bx, by)],
        [(vx, vy), (bx, vy), (bx, by)],
        [(vx, vy), (vx, 24.80), (bx, 24.80), (bx, by)],
        [(vx, vy), (vx, 25.20), (bx, 25.20), (bx, by)],
        [(vx, vy), (vx, 25.80), (bx, 25.80), (bx, by)],
        [(vx, vy), (38.00, vy), (38.00, 24.80), (bx, 24.80), (bx, by)],
        [(vx, vy), (vx, 59.20), (bx, 59.20), (bx, by)],
        [(vx, vy), (43.08, vy), (43.08, 59.20), (bx, 59.20), (bx, by)],
        [(vx, vy), (40.54, vy), (40.54, by)],
        [(vx, vy), (45.62, vy), (45.62, by)],
        [(vx, vy), (48.16, vy), (48.16, by)],
        [(vx, vy), (50.70, vy), (50.70, by)],
        [
            (vx, vy),
            (vx, 22.50),
            (36.50, 22.50),
            (36.50, 27.20),
            (34.50, 27.20),
            (34.50, 30.80),
            (32.20, 30.80),
            (32.20, 59.20),
            (bx, 59.20),
            (bx, by),
        ],
    ]


def route_u1_to_existing_b(r, name):
    print(f"== {name} U1 to existing B island (post-COEX2 rip) ==", flush=True)
    p = r.u1(name)
    if not p:
        BLOCKERS[name] = "no U1 pad"
        return False
    island = p27.nearest_b_end(r, name, p["x"], p["y"])
    if not island:
        BLOCKERS[name] = "no B island"
        return False
    bx, by, dist = island
    print(f"  island ({bx:.2f},{by:.2f}) d={dist:.2f}", flush=True)
    ev = p27.existing_u1_via(r, name, p)
    attempts = []
    if ev:
        attempts.append((ev["x"], ev["y"], None, None, None))
        print(f"  existing via ({ev['x']:.2f},{ev['y']:.2f})", flush=True)
        for alt in r.vias:
            if alt["n"] != name or hypot(alt["x"], alt["y"], ev["x"], ev["y"]) < 0.15:
                continue
            if hypot(alt["x"], alt["y"], p["x"], p["y"]) < 8.0 and r.pad_reaches_via(p, alt, name):
                attempts.append((alt["x"], alt["y"], None, None, None))
    extra = extra_via_sites(p, name) + [
        (p["x"], 25.00),
        (p["x"], 24.80),
        (p["x"], 25.40),
        (p["x"] + 1.50, 25.00),
        (p["x"] - 1.50, 25.00),
        (p["x"], 19.00),
        (44.50, 19.00),
        (42.25, 25.00),
        (39.75, 25.00),
    ]
    for vx, vy in extra:
        vx, vy = round(vx, 2), round(vy, 2)
        size, drill = 0.50, 0.30
        w = r.via_why(vx, vy, name, size=size, drill=drill)
        if w is not None:
            size, drill = 0.45, 0.25
            w = r.via_why(vx, vy, name, size=size, drill=drill)
            if w is not None:
                continue
        fpath = p27.pad_f_to_via(r, p, vx, vy, name)
        if ev:
            ext = [(ev["x"], ev["y"]), (vx, vy)]
            if r.path_clear(ext, F, 0.18, name):
                fpath = fpath or ext
        if not fpath:
            continue
        attempts.append((vx, vy, size, drill, fpath))

    for vx, vy, size, drill, fpath in attempts:
        path, cost = waypoint_route(r, vx, vy, bx, by, B, 0.18, name, xs=ADC_XS, ys=ADC_YS)
        if path is None or cost > 90:
            path = next((pts for pts in b_candidates(vx, vy, bx, by) if r.path_clear(pts, B, 0.18, name)), None)
        if not path:
            continue
        hops, routes = [], []
        if size is not None:
            hops.append((vx, vy, size, drill))
            routes.append((fpath, F, 0.18, "F pad-via"))
        routes.append((path, B, 0.18, "B to island"))
        print(f"  try via ({vx:.2f},{vy:.2f}) B n={len(path)}", flush=True)
        if try_sized(r, name, hops, routes):
            return True
    sample = [(p["x"], 24.80), (bx, 24.80), (bx, by)]
    BLOCKERS[name] = BLOCKERS.get(name) or why(r, sample, B, 0.18, name)
    print(f"  blocker {BLOCKERS[name]}", flush=True)
    return False


def apply_net(board, r, name, fn, last, ceiling):
    r.ok = 0
    placed = fn(r)
    r.collect()
    if not placed:
        print(f"  no copper for {name}", flush=True)
        return board, r, last, False, ceiling, None
    got = check(r.board, r, f"pass28-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    last = snap_path(f"pass28-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, got[1], got[0]


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
    NET_LOG.append((name, st, note0 + (f". blocker: `{extra}`" if extra else "")))
    print(f"  {st}", flush=True)
    return board, r, last, ceiling, last_pairs


def route_j17_dup(r, name, j13x, j17y):
    """Branch J17 from live J13 B copper. No second U1 escape."""
    print(f"== {name} J17 duplicate from J13 ({j13x:.2f},76) ==", flush=True)
    # J13 already on B. Try B east/north then stub to J17 at (108, j17y).
    cands = [
        [(j13x, 76.00), (j13x, 74.00), (108.00, 74.00), (108.00, j17y)],
        [(j13x, 76.00), (j13x, 72.80), (108.00, 72.80), (108.00, j17y)],
        [(j13x, 76.00), (j13x, 77.20), (108.00, 77.20), (108.00, j17y)],
    ]
    for pts in cands:
        if try_sized(r, name, [], [(pts, B, 0.18, "B J13 to J17")]):
            return True
    BLOCKERS[name] = BLOCKERS.get(name) or why(r, cands[0], B, 0.18, name)
    return False


def write_release(n0, n1, shorts, counts, pairs, log, board, dang, nvia0, nvia1, rem_note):
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
        f.write("| Live snapshot after this pass | `after-pass28.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass28-start.kicad_pcb` |\n\n")
        f.write("## This pass (COEX2 remnant add-then-delete + U1-to-B)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 80. Zone refill after copper. ")
        f.write("VDD2 / P0.15 / ENABLE / SIM_RST / VIN x=66 / P0.01 / P0.04 / P0.06 not ripped. ")
        f.write(f"New vias this pass: {nvia1 - nvia0}. Dangling new vias: {len(dang)}.\n\n")
        f.write(f"**COEX2 remnants removed:** {rem_note}\n\n")
        f.write(f"**Nets closed:** {', '.join(CLOSED) if CLOSED else 'none'}\n\n")
        f.write(f"**Duplicates branched:** {', '.join(DUP_BRANCHED) if DUP_BRANCHED else 'none'}\n\n")
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
    start = snap_path("pass28-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 80:
        print(f"start {n0}>80 abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    nvia0 = p25.count_vias(board)
    vias0 = p25.via_xy_set(board)
    last_pairs = pairs
    rem_note = "none (not deleted)"

    print("\n#### COEX2_ADD join y=33.20", flush=True)
    r.ok = 0
    if not try_commit(r, JOIN, B, 0.18, "COEX2", "join U1 V x=37.75 to wrap at y=33.20"):
        NET_LOG.append(("COEX2_ADD", "not added", why(r, JOIN, B, 0.18, "COEX2")))
        print("  join blocked; stop (remnants kept)", flush=True)
        write_unconnected_csv(last_pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
        write_gpio_csv(board, last_pairs, f"{REP}/GPIO_FINAL.csv")
        write_release(n0, n0, 0, counts0, last_pairs, NET_LOG, board, [], nvia0, nvia0, rem_note)
        return 1
    got = check(r.board, r, "pass28-COEX2ADD", last, ceiling, force_fill=True)
    if got[0] is None:
        print("  join DRC failed; remnants kept", flush=True)
        NET_LOG.append(("COEX2_ADD", "reverted", "DRC abort"))
        write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
        write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
        write_release(n0, n0, 0, counts0, pairs, NET_LOG, board, [], nvia0, nvia0, rem_note)
        return 1
    last_pairs, ceiling, counts, _ = got[0], got[1], got[2], got[3]
    last = snap_path("pass28-COEX2ADD")
    board, r = reload()
    NET_LOG.append(("COEX2_ADD", f"added (unconn={ceiling})", "B (37.75,33.20)-(40.50,33.20)"))
    print(f"  join OK unconn={ceiling}", flush=True)

    print("\n#### COEX2_RIP remnants", flush=True)
    pre_rip = last
    removed, shorten = delete_coex2_remnants(board, r)
    r.ok = 1
    got = check(board, r, "pass28-COEX2RIP", pre_rip, ceiling, force_fill=True)
    if got[0] is None:
        print("  rip raised unconnected or DRC; remnants restored, stop", flush=True)
        NET_LOG.append(("COEX2_RIP", "reverted", "unconnected rose or DRC; remnants kept"))
        board, r = reload()
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        pairs, n1, counts, _ = run_drc()
        write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
        write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
        write_release(n0, n1, counts.get("shorting_items", 0) or 0, counts, pairs, NET_LOG, board, [], nvia0, p25.count_vias(board), rem_note)
        print(f"END unconn={n1} shorts={counts.get('shorting_items',0)} fab=no remnants kept", flush=True)
        return 1
    last_pairs, ceiling, counts = got[0], got[1], got[2]
    last = snap_path("pass28-COEX2RIP")
    board, r = reload()
    for spec in removed:
        COEX2_REMOVED.append(f"{spec[5]} ({spec[0]:.2f},{spec[1]:.2f})-({spec[2]:.2f},{spec[3]:.2f})")
    if shorten:
        COEX2_REMOVED.append("shortened V x=37.75 41.10–24.60 → 41.10–33.20")
    rem_note = ", ".join(COEX2_REMOVED) if COEX2_REMOVED else "none matched"
    NET_LOG.append(("COEX2_RIP", f"ripped (unconn={ceiling})", rem_note))
    print(f"  rip OK unconn={ceiling} removed={rem_note}", flush=True)

    for name in ("P0.13", "P0.14", "P0.16", "P0.17", "P0.18"):

        def fn(rr, _n=name):
            return route_u1_to_existing_b(rr, _n)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            island_open,
            "U1 to existing same-net B after COEX2 remnant rip",
            kind="U1-B",
        )

    # Live-primary duplicates: J17 copies if J13 B is live (P0.17 / P0.18).
    for name, j13x, j17y in (("P0.17", 66.54, 26.00), ("P0.18", 69.08, 28.54)):
        if not header_open(last_pairs, name, "J17"):
            NET_LOG.append((name, "skip", "J17 not in DRC"))
            continue
        # Only branch if U1-side is closed (primary live).
        if island_open(last_pairs, name):
            NET_LOG.append((name, "skip", "U1 island still open; not a live-primary dup"))
            continue

        def fn(rr, _n=name, _x=j13x, _y=j17y):
            return route_j17_dup(rr, _n, _x, _y)

        board, r, last, ceiling, last_pairs = run_one(
            board,
            r,
            name,
            fn,
            last,
            ceiling,
            last_pairs,
            lambda ps, n, t="J17": header_open(ps, n, t),
            "J17 branch from live J13 B",
            kind="J17",
        )
        if any(x.startswith(f"{name} J17") for x in CLOSED):
            DUP_BRANCHED.append(f"{name} J17 from J13")

    shutil.copy2(BOARD, snap_path("pass28"))
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
    write_release(n0, n1, shorts, counts, pairs, NET_LOG, board, dang, nvia0, nvia1, rem_note)
    print(
        f"END unconn={n1} shorts={shorts} closed={CLOSED} rem={COEX2_REMOVED} "
        f"vias {nvia0}->{nvia1} dang={len(dang)} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
