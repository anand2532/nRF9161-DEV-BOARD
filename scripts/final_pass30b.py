#!/usr/bin/env python3
"""Pass30b: continue from placed U3/FB5 — close local bias, Class F, Class C, SIM."""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
sys.path.insert(0, f"{ROOT}/scripts")

from complete_route import BOARD, hypot, vec  # noqa: E402
from final_connect import fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import Final, class_counts, dump_vios, try_commit, waypoint_route  # noqa: E402

SNAP = f"{ROOT}/.mcp-backups/pass30-connect"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
CLOSED, DEFERRED = [], []
BASELINE_CLR = 0  # mid-pass already 0


def check(board, r, label, last_good, ceiling, clr_ceiling=BASELINE_CLR):
    if r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    clr = counts.get("clearance", 0)
    hole = counts.get("hole_clearance", 0)
    print(f"DRC [{label}] unconn={n} shorts={shorts} clr={clr} hole={hole}", flush=True)
    bad = []
    if shorts > 0:
        bad.append("shorting_items")
    if hole > 0:
        bad.append("hole_clearance")
    if clr > clr_ceiling:
        bad.append("clearance")
    if bad or n > ceiling:
        reason = {k: counts.get(k, 0) for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}", flush=True)
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, f"{SNAP}/after-{label}.kicad_pcb")
    return pairs, n, counts, pairs


def pads_of(board):
    u3 = board.FindFootprintByReference("U3")
    fb = board.FindFootprintByReference("FB5")
    pads = {}
    for p in u3.Pads():
        pads[p.GetNumber()] = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    for p in fb.Pads():
        pads[f"FB5.{p.GetNumber()}"] = (
            pcbnew.ToMM(p.GetPosition().x),
            pcbnew.ToMM(p.GetPosition().y),
        )
    return pads


def safe_wp(r, x1, y1, x2, y2, layer, w, name):
    path = waypoint_route(r, x1, y1, x2, y2, layer, w, name)
    if not path:
        return None
    if any(p is None or len(p) != 2 for p in path):
        return None
    return path


def route_bias(board, r, pads):
    x1, y1 = pads["6"]
    x2, y2 = pads["FB5.1"]
    # South wrap around GNSS_ANT x=16 spine and C23
    candidates = [
        [(x1, y1), (x1, 53.0), (x2, 53.0), (x2, y2)],
        [(x1, y1), (22.5, y1), (22.5, 53.0), (x2, 53.0), (x2, y2)],
        [(x1, y1), (x1, 54.5), (18.0, 54.5), (18.0, y2), (x2, y2)],
        [(x1, y1), (x1, 33.0), (x2, 33.0), (x2, y2)],
        [(x1, y1), (24.5, y1), (24.5, 33.5), (14.0, 33.5), (x2, y2)],
    ]
    ok = False
    for pts in candidates:
        if try_commit(r, pts, F, 0.25, "GNSS_VBIAS_SRC", f"bias {pts[1]}"):
            CLOSED.append("GNSS_VBIAS_SRC U3→FB5")
            ok = True
            break
    if not ok:
        DEFERRED.append("GNSS_VBIAS_SRC U3→FB5")

    # Finish COEX0 if dangling via exists from prior
    cx, cy = pads["3"]
    # find COEX0 vias near U3
    coex_vias = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "COEX0":
            x, y = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)
            if abs(x - 28) < 3 and abs(y - cy) < 3:
                coex_vias.append((x, y))
    for vx, vy in coex_vias or [(28.0, cy)]:
        for pts in [
            [(vx, vy), (vx, 18.0), (31.11, 18.0), (31.11, 22.0)],
            [(vx, vy), (31.11, vy), (31.11, 22.0)],
            [(cx, cy), (31.11, cy), (31.11, 22.0)],
            [(cx, cy), (cx, 18.5), (31.11, 18.5), (31.11, 22.0)],
        ]:
            layer = B if pts[0] == (vx, vy) and (vx, vy) in (coex_vias or [(28.0, cy)]) else F
            # first try B from via
            if try_commit(r, pts, B, 0.18, "COEX0", f"COEX0 B {pts}"):
                CLOSED.append("COEX0 U3.ON")
                ok = True
                break
            if try_commit(r, pts, F, 0.18, "COEX0", f"COEX0 F {pts}"):
                CLOSED.append("COEX0 U3.ON")
                ok = True
                break
        else:
            continue
        break
    else:
        if "COEX0 U3.ON" not in CLOSED:
            DEFERRED.append("COEX0 U3.ON finish")

    # VIN finish
    vx, vy = pads["1"]
    vin_vias = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "VDD_GPIO":
            x, y = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)
            if 26 < x < 32 and 45 < y < 50:
                vin_vias.append((x, y))
    ok = False
    for site in vin_vias or [(28.5, vy)]:
        for pts in [
            [site, (site[0], 19.13), (40.17, 19.13)],
            [site, (40.17, site[1]), (40.17, 19.13)],
            [(vx, vy), (40.17, 52.0), (40.17, 19.13)],
            [(vx, vy), (35.0, vy), (35.0, 19.13), (40.17, 19.13)],
        ]:
            for layer in (B, F):
                if try_commit(r, pts, layer, 0.35, "VDD_GPIO", f"VIN {layer} {pts[1]}"):
                    CLOSED.append("VDD_GPIO U3.VIN")
                    ok = True
                    break
            if ok:
                break
        if ok:
            break
    if not ok:
        DEFERRED.append("VDD_GPIO U3.VIN finish")

    # GND stub
    gx, gy = pads["2"]
    for pts in [[(gx, gy), (gx + 1.2, gy)], [(gx, gy), (gx, gy + 1.0)]]:
        if try_commit(r, pts, F, 0.25, "GND", f"GND {pts[-1]}"):
            CLOSED.append("U3 GND")
            break
    else:
        DEFERRED.append("U3 GND")


def route_class_f(board, r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)

    def try_net(net, w, layers=(F, B)):
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            for layer in layers:
                # manual jogs
                jogs = [
                    [a, (a[0], b[1]), b],
                    [a, (b[0], a[1]), b],
                    [a, ((a[0] + b[0]) / 2, a[1]), ((a[0] + b[0]) / 2, b[1]), b],
                ]
                if net == "VIN_FILT":
                    jogs = [
                        [a, (54.0, a[1]), (54.0, b[1]), b],
                        [a, (55.35, 12.5), (50.5, 12.5), (50.5, b[1]), b],
                        [a, (57.5, a[1]), (57.5, b[1]), b],
                        [a, (55.35, 22.5), (51.9, 22.5), b],
                    ]
                if net == "VIN_F":
                    jogs = [
                        [a, (a[0], 10.5), (b[0], 10.5), b],
                        [a, (a[0], 19.06), b],
                        [a, (60.0, a[1]), (60.0, b[1]), b],
                    ]
                if net == "SWDCLK":
                    jogs = [
                        [a, (a[0], 10.0), (b[0], 10.0), b],
                        [a, (45.0, a[1]), (45.0, b[1]), b],
                        [a, (51.95, 15.0), (37.75, 15.0), b],
                    ]
                for pts in jogs:
                    if try_commit(r, pts, layer, w, net, f"{net} {layer} {pts[1]}"):
                        CLOSED.append(net)
                        return True
                path = safe_wp(r, a[0], a[1], b[0], b[1], layer, w, net)
                if path and try_commit(r, path, layer, w, net, f"{net} wp {layer}"):
                    CLOSED.append(net)
                    return True
            DEFERRED.append(net)
            return False
        return False

    try_net("VIN_FILT", 0.4, (F,))
    try_net("VIN_F", 0.4, (F,))
    try_net("SWDCLK", 0.18, (F, B))
    try_net("nRESET", 0.18, (F, B))
    try_net("P0.02", 0.18, (F, B))
    try_net("P0.08", 0.18, (F, B))


def stub_class_c(board, r):
    mapping = [
        ("C21", "ANT"),
        ("C22", "ANT_FIT"),
        ("C23", "AUX"),
        ("C24", "AUX_FIT"),
        ("C31", "GPS"),
        ("C32", "GNSS_ANT"),
    ]
    for ref, expect in mapping:
        fp = board.FindFootprintByReference(ref)
        if not fp:
            DEFERRED.append(f"ClassC {ref} missing")
            continue
        rf_pad = gnd_pad = None
        for p in fp.Pads():
            if p.GetNetname() == "GND":
                gnd_pad = p
            elif p.GetNetname() and p.GetNetname() != "GND":
                rf_pad = p
        if rf_pad is None:
            DEFERRED.append(f"ClassC {ref} no RF pad")
            continue
        netname = rf_pad.GetNetname()
        x, y = pcbnew.ToMM(rf_pad.GetPosition().x), pcbnew.ToMM(rf_pad.GetPosition().y)
        best = None
        best_d = 1e9
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != netname:
                continue
            if t.GetLayer() != F:
                continue
            for px, py in [
                (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)),
                (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)),
            ]:
                d = hypot(x, y, px, py)
                if 0.2 < d < best_d:
                    best_d = d
                    best = (px, py)
        if best is None:
            DEFERRED.append(f"ClassC {ref}/{netname} no trunk")
            continue
        dist = best_d
        if dist <= 2.0:
            pts = [(x, y), best]
        else:
            dx, dy = best[0] - x, best[1] - y
            pts = [(x, y), (x + dx * 2.0 / dist, y + dy * 2.0 / dist)]
        if try_commit(r, pts, F, 0.2, netname, f"ClassC {ref}"):
            CLOSED.append(f"ClassC {ref}")
        else:
            DEFERRED.append(f"ClassC {ref}")


def route_sim(board, r, pairs):
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)
    for net in ["SIM_CLK", "SIM_RST", "SIM_IO", "SIM_1V8"]:
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            ok = False
            for layer in (B, F):
                path = safe_wp(r, a[0], a[1], b[0], b[1], layer, 0.18, net)
                if path and try_commit(r, path, layer, 0.18, net, f"{net} {layer}"):
                    CLOSED.append(net)
                    ok = True
                    break
                for pts in [
                    [a, (a[0], b[1]), b],
                    [a, (b[0], a[1]), b],
                    [a, (50.0, a[1]), (50.0, b[1]), b],
                    [a, (64.7, a[1]), (64.7, b[1]), b],
                ]:
                    if try_commit(r, pts, layer, 0.18, net, f"{net} jog"):
                        CLOSED.append(net)
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                DEFERRED.append(net)


def main():
    # ensure we start from good snapshot if live got corrupted
    if board_has_u3 := True:
        pass
    board = pcbnew.LoadBoard(BOARD)
    if board.FindFootprintByReference("U3") is None:
        shutil.copy2(f"{SNAP}/after-u3-fb5.kicad_pcb", BOARD)
        board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    pairs, n0, counts0, _ = run_drc()
    print(f"START30b unconn={n0} clr={counts0.get('clearance',0)} dang={counts0.get('via_dangling',0)}", flush=True)
    last = f"{SNAP}/after-u3-fb5.kicad_pcb"
    shutil.copy2(BOARD, last)
    ceiling = n0

    pads = pads_of(board)
    print("pads", pads, flush=True)
    print("=== bias ===", flush=True)
    route_bias(board, r, pads)
    res = check(board, r, "bias", last, ceiling)
    if res[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-bias.kicad_pcb"
        ceiling = n0
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    print("=== class F ===", flush=True)
    route_class_f(board, r, pairs)
    res = check(board, r, "class-f", last, ceiling)
    if res[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-class-f.kicad_pcb"
        ceiling = n0
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    print("=== class C ===", flush=True)
    stub_class_c(board, r)
    res = check(board, r, "class-c", last, ceiling)
    if res[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res
        last = f"{SNAP}/after-class-c.kicad_pcb"
        ceiling = n0
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    print("=== SIM ===", flush=True)
    route_sim(board, r, pairs)
    res = check(board, r, "sim", last, ceiling)
    if res[0] is None:
        pairs, n0, counts0, _ = run_drc()
    else:
        pairs, n0, counts0, _ = res

    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    summary = {"closed": CLOSED, "deferred": DEFERRED, "unconn": n0, "counts": dict(counts0)}
    open(f"{ROOT}/reports/PASS30_SUMMARY.json", "w").write(json.dumps(summary, indent=2))
    print("SUMMARY", json.dumps(summary, indent=2), flush=True)
    print("classes", class_counts(pairs), flush=True)


if __name__ == "__main__":
    main()
