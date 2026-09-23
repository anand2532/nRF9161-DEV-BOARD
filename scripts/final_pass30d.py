#!/usr/bin/env python3
"""Pass30d: aggressive Class F closes via surgical B.Cu corridor jogs.

Order: VIN_FILT -> VIN_F -> SWDCLK -> nRESET -> P0.02 -> P0.08; COEX0 if easy.
Preserve P0.15 west wrap (only jog north trunk y=15.35). shorting=0, clearance=0.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
sys.path.insert(0, f"{ROOT}/scripts")

from complete_route import BOARD  # noqa: E402
from final_connect import DRC_JSON, fill_zones, run_drc  # noqa: E402
from final_pass14 import (  # noqa: E402
    Final,
    class_counts,
    dump_vios,
    try_commit,
    waypoint_route,
)

SNAP = f"{ROOT}/.mcp-backups/pass30d-connect"
os.makedirs(SNAP, exist_ok=True)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
CLOSED, DEFERRED, NOTES, BLOCKED = [], [], [], []


def p015_west_count(board):
    n = 0
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            continue
        x1 = pcbnew.ToMM(t.GetStart().x)
        x2 = pcbnew.ToMM(t.GetEnd().x)
        if min(x1, x2) < 45 or max(x1, x2) < 45:
            n += 1
    return n


def check(board, r, label, last_good, ceiling, clr_ceiling=0):
    if getattr(r, "ok", 0):
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    clr = counts.get("clearance", 0)
    hole = counts.get("hole_clearance", 0)
    print(
        f"DRC [{label}] unconn={n} shorts={shorts} clr={clr} hole={hole}",
        flush=True,
    )
    bad = []
    if shorts > 0:
        bad.append("shorting_items")
    if hole > 0:
        bad.append("hole_clearance")
    if clr > clr_ceiling:
        bad.append("clearance")
    if counts.get("tracks_crossing", 0) > 0:
        bad.append("tracks_crossing")
    west = p015_west_count(board)
    if west < 17:
        bad.append(f"p015_west={west}")
    if bad or n > ceiling:
        reason = (
            {k: counts.get(k, 0) for k in bad if isinstance(k, str) and k in counts}
            if bad
            else f"unconn {n}>{ceiling}"
        )
        if any(isinstance(b, str) and b.startswith("p015") for b in bad):
            reason = bad
        print(f"ABORT {reason}; restoring {last_good}", flush=True)
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, f"{SNAP}/after-{label}.kicad_pcb")
    return pairs, n, counts, pairs


def reload():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def add_trk(board, net, x1, y1, x2, y2, w, layer=B):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)


def apply_corridor_jogs(board):
    """Batch rip+replace blockers for VIN_FILT B corridor. No P0.15 west wrap."""
    info = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        info.append(
            {
                "net": t.GetNetname(),
                "ly": t.GetLayer(),
                "obj": t,
                "x1": pcbnew.ToMM(t.GetStart().x),
                "y1": pcbnew.ToMM(t.GetStart().y),
                "x2": pcbnew.ToMM(t.GetEnd().x),
                "y2": pcbnew.ToMM(t.GetEnd().y),
                "w": pcbnew.ToMM(t.GetWidth()),
            }
        )

    def find(pred, key):
        for i in info:
            if pred(i):
                print(
                    f"  jog-rip {key}: {i['net']} "
                    f"({i['x1']:.2f},{i['y1']:.2f})-({i['x2']:.2f},{i['y2']:.2f}) w={i['w']}",
                    flush=True,
                )
                return i
        print(f"  MISS jog {key}", flush=True)
        return None

    rules = [
        (
            "V70",
            lambda i: i["net"] == "VDD_GPIO"
            and i["ly"] == B
            and abs(i["x1"] - 70) < 0.05
            and abs(i["x2"] - 70) < 0.05
            and min(i["y1"], i["y2"]) < 9
            and max(i["y1"], i["y2"]) > 14,
        ),
        (
            "H148",
            lambda i: i["net"] == "VDD_GPIO"
            and i["ly"] == B
            and abs(i["y1"] - 14.8) < 0.05
            and abs(i["y2"] - 14.8) < 0.05
            and min(i["x1"], i["x2"]) < 50
            and max(i["x1"], i["x2"]) > 60,
        ),
        (
            "P015N",
            lambda i: i["net"] == "P0.15"
            and i["ly"] == B
            and abs(i["y1"] - 15.35) < 0.05
            and abs(i["y2"] - 15.35) < 0.05
            and min(i["x1"], i["x2"]) < 50
            and max(i["x1"], i["x2"]) > 60,
        ),
        (
            "EN",
            lambda i: i["net"] == "ENABLE"
            and i["ly"] == B
            and abs(i["y1"] - 20.3) < 0.05
            and abs(i["y2"] - 20.3) < 0.05
            and min(i["x1"], i["x2"]) < 52
            and max(i["x1"], i["x2"]) > 55,
        ),
        (
            "VDD2H",
            lambda i: i["net"] == "VDD2"
            and i["ly"] == B
            and abs(i["y1"] - 21.2) < 0.05
            and abs(i["y2"] - 21.2) < 0.05
            and min(i["x1"], i["x2"]) < 55
            and max(i["x1"], i["x2"]) > 60,
        ),
        (
            "VDD2V",
            lambda i: i["net"] == "VDD2"
            and i["ly"] == B
            and abs(i["x1"] - 54.5) < 0.05
            and abs(i["x2"] - 54.5) < 0.05
            and min(i["y1"], i["y2"]) < 22
            and max(i["y1"], i["y2"]) > 30,
        ),
    ]
    doomed, ws = [], {}
    for key, pred in rules:
        i = find(pred, key)
        if i:
            doomed.append(i["obj"])
            ws[key] = i["w"]
    for t in doomed:
        board.Remove(t)

    w = ws.get("H148", 0.25)
    for seg in [
        (70, 8, 72.5, 8),
        (72.5, 8, 72.5, 14.8),
        (72.5, 14.8, 56.5, 14.8),
        (56.5, 14.8, 56.5, 12.2),
        (56.5, 12.2, 54.2, 12.2),
        (54.2, 12.2, 54.2, 14.8),
        (54.2, 14.8, 48.05, 14.8),
    ]:
        add_trk(board, "VDD_GPIO", *seg, w)

    w = ws.get("P015N", 0.18)
    for seg in [
        (46.70, 15.35, 51.50, 15.35),
        (51.50, 15.35, 51.50, 25.50),
        (51.50, 25.50, 56.50, 25.50),
        (56.50, 25.50, 56.50, 15.35),
        (56.50, 15.35, 72.00, 15.35),
    ]:
        add_trk(board, "P0.15", *seg, w)

    w = ws.get("EN", 0.18)
    for seg in [
        (50.85, 20.30, 50.00, 20.30),
        (50.00, 20.30, 50.00, 24.50),
        (50.00, 24.50, 56.50, 24.50),
        (56.50, 24.50, 56.50, 20.30),
    ]:
        add_trk(board, "ENABLE", *seg, w)

    w = ws.get("VDD2H", 0.25)
    for seg in [
        (68.79, 21.20, 56.10, 21.20),
        (54.70, 21.20, 54.50, 21.20),
        (54.50, 21.20, 50.80, 21.20),
        (50.80, 21.20, 50.80, 32.00),
    ]:
        add_trk(board, "VDD2", *seg, w)

    NOTES.append(
        "Corridor jogs: VDD_GPIO V70/H148, P0.15 north trunk (not west wrap), "
        "ENABLE H, VDD2 H+V(54.5)->west vertical @50.8"
    )
    return ws


def route_vin_filt(r):
    pts = [(55.35, 13.3), (55.35, 22.5), (51.9, 22.5), (51.9, 21.9)]
    for w in (0.30, 0.25):
        if try_commit(r, pts, B, w, "VIN_FILT", f"VIN_FILT B slot w={w}"):
            CLOSED.append("VIN_FILT")
            return True
    DEFERRED.append("VIN_FILT")
    BLOCKED.append("VIN_FILT: commit failed after corridor jogs")
    return False


def try_wp(r, name, layer, w, x1, y1, x2, y2, label, max_l=120):
    pts, L = waypoint_route(r, x1, y1, x2, y2, layer, w, name)
    if pts is None:
        print(f"  FAIL waypoint {label}: no path", flush=True)
        return False
    if L > max_l:
        print(f"  skip long waypoint {label} L={L:.1f}", flush=True)
        return False
    return try_commit(r, pts, layer, w, name, f"waypoint {label} L={L:.1f}")


def route_one_net(r, net, w, layers, jog_lists):
    """jog_lists: callable(a,b)->list of polylines, or list of absolute polylines."""
    # Prefer absolute candidates if provided as list of lists of tuples with >2 pts starting near vias
    if callable(jog_lists):
        # need pair from DRC - handled by caller
        return False
    for layer in layers:
        for pts in jog_lists:
            if try_commit(r, pts, layer, w, net, f"{net} {layer} {pts[1] if len(pts)>1 else pts}"):
                CLOSED.append(net)
                return True
        # waypoint between ends
        if len(jog_lists) > 0:
            a, b = jog_lists[0][0], jog_lists[0][-1]
            if try_wp(r, net, layer, w, a[0], a[1], b[0], b[1], f"{net}-{layer}"):
                CLOSED.append(net)
                return True
    DEFERRED.append(net)
    BLOCKED.append(f"{net}: no clear candidate")
    return False


def route_class_f_rest(r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)

    def attempt(net, w, layers, extra):
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            jogs = extra(a, b) + [
                [a, b],
                [a, (a[0], b[1]), b],
                [a, (b[0], a[1]), b],
                [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b],
            ]
            for layer in layers:
                for pts in jogs:
                    if try_commit(
                        r, pts, layer, w, net, f"{net} {layer} {pts[1] if len(pts)>1 else pts}"
                    ):
                        CLOSED.append(net)
                        return True
                if try_wp(r, net, layer, w, a[0], a[1], b[0], b[1], f"{net}-{layer}"):
                    CLOSED.append(net)
                    return True
            DEFERRED.append(net)
            BLOCKED.append(f"{net}: blocked a={a} b={b}")
            return False
        DEFERRED.append(f"{net} (no pair)")
        return False

    # Absolute known vias for P0.02
    if try_commit(
        r,
        [(40.75, 43.5), (40.75, 19.13), (92.14, 19.13)],
        B,
        0.18,
        "P0.02",
        "P0.02 B west via to east via",
    ):
        CLOSED.append("P0.02")
    elif try_commit(
        r,
        [(40.75, 43.5), (92.14, 43.5), (92.14, 19.13)],
        B,
        0.18,
        "P0.02",
        "P0.02 B high then south",
    ):
        CLOSED.append("P0.02")
    else:
        attempt(
            "P0.02",
            0.18,
            (B, F),
            lambda a, b: [
                [a, (a[0], b[1]), b],
                [a, (60.0, a[1]), (60.0, b[1]), b],
                [a, (a[0], 50.0), (b[0], 50.0), b],
            ],
        )

    attempt(
        "VIN_F",
        0.30,
        (B, F),
        lambda a, b: [
            [a, (a[0], 22.5), (b[0], 22.5), b],
            [a, (a[0], 10.5), (b[0], 10.5), b],
            [a, (a[0], 19.06), b],
            [a, (60.0, a[1]), (60.0, b[1]), b],
            [a, (48.0, 12.6), (48.0, 22.5), (71.575, 22.5), (71.575, 19.06)],
        ],
    )
    attempt(
        "SWDCLK",
        0.18,
        (B, F),
        lambda a, b: [
            [a, (a[0], 3.0), (b[0], 3.0), b],
            [a, (66.0, a[1]), (66.0, b[1]), b],
            [(53.65, 4.73), (53.65, 3.2), (37.75, 3.2), (37.75, 26.75)],
            [(63.3, 6.0), (66.0, 6.0), (66.0, 26.75), (37.75, 26.75)],
        ],
    )
    attempt(
        "nRESET",
        0.18,
        (B, F),
        lambda a, b: [
            [(101.68, 26.0), (45.68, 26.0), (45.68, 15.8)],
            [(101.68, 58.8), (90.0, 58.8), (90.0, 10.8), (52.22, 10.8)],
            [a, (70.0, a[1]), (70.0, b[1]), b],
            [a, (a[0], 40.0), (b[0], 40.0), b],
        ],
    )
    # P0.08: prefer first pair (stub to via)
    attempt(
        "P0.08",
        0.18,
        (B, F),
        lambda a, b: [
            [(78.375, 24.0), (78.375, 30.0), (46.2, 30.0)],
            [(78.375, 26.0), (46.2, 26.0), (46.2, 30.0)],
            [(44.0, 30.0), (44.0, 70.0), (26.32, 70.0), (26.32, 76.0)],
            [a, (a[0], b[1]), b],
            [a, (b[0], a[1]), b],
        ],
    )


def route_coex0(r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)
    if not by.get("COEX0"):
        DEFERRED.append("COEX0 (no pair)")
        return False
    for pts in [
        [(31.11, 22.0), (33.0, 22.0), (33.0, 43.0)],
        [(31.11, 22.0), (38.8, 22.0), (38.8, 43.0)],
        [(31.11, 22.0), (35.0, 22.0), (35.0, 43.0), (33.0, 43.0)],
        [(31.11, 22.0), (31.11, 43.0), (33.0, 43.0)],
        [(29.81, 22.0), (33.0, 22.0), (33.0, 43.0)],
    ]:
        if try_commit(r, pts, B, 0.18, "COEX0", f"COEX0 {pts[1]}"):
            CLOSED.append("COEX0 north-south")
            return True
    DEFERRED.append("COEX0 north island")
    BLOCKED.append("COEX0: north via@22 still walled from south spine")
    return False


def main():
    board, r = reload()
    west0 = p015_west_count(board)
    NOTES.append(f"P0.15 west-ish B segs before={west0}")

    pairs, n0, counts0, _ = run_drc()
    print(
        f"START30d unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} west={west0}",
        flush=True,
    )
    last = f"{SNAP}/start.kicad_pcb"
    shutil.copy2(BOARD, last)
    ceiling = n0
    before = {
        "unconnected_items": n0,
        "shorting_items": counts0.get("shorting_items", 0),
        "clearance": counts0.get("clearance", 0),
    }

    print("=== Corridor jogs + VIN_FILT ===", flush=True)
    apply_corridor_jogs(board)
    pcbnew.SaveBoard(BOARD, board)
    board, r = reload()
    route_vin_filt(r)
    res = check(board, r, "vin-filt", last, ceiling)
    if res[0] is None:
        board, r = reload()
        pairs, n0, counts0, _ = run_drc()
        NOTES.append("VIN_FILT+jogs aborted by DRC; board restored")
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-vin-filt.kicad_pcb"
        ceiling = n0
        board, r = reload()

    print("=== Class F rest ===", flush=True)
    pre = f"{SNAP}/pre-class-f-rest.kicad_pcb"
    shutil.copy2(BOARD, pre)
    route_class_f_rest(r, pairs)
    res = check(board, r, "class-f-rest", last, ceiling)
    if res[0] is None:
        board, r = reload()
        pairs, n0, counts0, _ = run_drc()
        # strip Class F rest closed claims that were rolled back
        for name in ("VIN_F", "SWDCLK", "nRESET", "P0.02", "P0.08"):
            while name in CLOSED:
                CLOSED.remove(name)
                DEFERRED.append(f"{name} (rolled back)")
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-class-f-rest.kicad_pcb"
        ceiling = n0
        board, r = reload()

    print("=== COEX0 easy ===", flush=True)
    pre = f"{SNAP}/pre-coex0.kicad_pcb"
    shutil.copy2(BOARD, pre)
    route_coex0(r, pairs)
    res = check(board, r, "coex0", last, ceiling)
    if res[0] is None:
        while "COEX0 north-south" in CLOSED:
            CLOSED.remove("COEX0 north-south")
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        n0 = res[1]
        counts0 = res[2]

    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n0, counts0, _ = run_drc()
    shutil.copy2(DRC_JSON, f"{ROOT}/reports/DRC_PASS30D_AFTER.json")

    after = {
        "unconnected_items": n0,
        "shorting_items": counts0.get("shorting_items", 0),
        "clearance": counts0.get("clearance", 0),
    }
    west1 = p015_west_count(pcbnew.LoadBoard(BOARD))
    summary = {
        "pass": "layout-pass30d",
        "before": before,
        "after": after,
        "closed": CLOSED,
        "deferred": DEFERRED,
        "blocked": BLOCKED,
        "notes": NOTES,
        "p0_15_west_segs": {"before": west0, "after": west1},
        "p0_15_wrap": "preserved (north trunk jogged only)",
        "gerbers": False,
        "backup": ".mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30d-20260923-100505",
        "drc": [
            "reports/DRC_PASS30D_BEFORE.json",
            "reports/DRC_PASS30D_AFTER.json",
        ],
        "classes": class_counts(pairs),
        "counts": dict(counts0),
    }
    open(f"{ROOT}/reports/PASS30D_SUMMARY.json", "w").write(json.dumps(summary, indent=2))
    print("SUMMARY", json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
