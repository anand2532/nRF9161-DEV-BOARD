#!/usr/bin/env python3
"""Occupancy-aware private B.Cu columns. Avoid existing vertical/horizontal walls."""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import ADC, BOARD, hypot, vec  # noqa: E402
from final_connect import BACKUP, DRC_JSON, Final, SNAP_DIR, fill_zones, run_drc  # noqa: E402
from final_pass2 import dnp_stubs, save_chk, wrap_fanout  # noqa: E402

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"


def load():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def walls(r: Final):
    vx, hy = [], []
    for t in r.tracks:
        if t["ly"] != pcbnew.B_Cu:
            continue
        if hypot(t["x1"], t["y1"], t["x2"], t["y2"]) < 4:
            continue
        if abs(t["x1"] - t["x2"]) < 0.12:
            vx.append((t["x1"], t["n"], min(t["y1"], t["y2"]), max(t["y1"], t["y2"])))
        if abs(t["y1"] - t["y2"]) < 0.12:
            hy.append((t["y1"], t["n"], min(t["x1"], t["x2"]), max(t["x1"], t["x2"])))
    return vx, hy


def free_x(vx, name, cands, y1, y2):
    lo, hi = min(y1, y2), max(y1, y2)
    for x in cands:
        ok = True
        for wx, n, ya, yb in vx:
            if n == name:
                continue
            if abs(x - wx) < 0.50 and not (hi < ya - 0.3 or lo > yb + 0.3):
                ok = False
                break
        if ok:
            return x
    return None


def free_y(hy, name, cands, x1, x2):
    lo, hi = min(x1, x2), max(x1, x2)
    for y in cands:
        ok = True
        for wy, n, xa, xb in hy:
            if n == name:
                continue
            if abs(y - wy) < 0.50 and not (hi < xa - 0.3 or lo > xb + 0.3):
                ok = False
                break
        if ok:
            return y
    return None


def private_gpio(r: Final):
    vx, hy = walls(r)
    print(f"  B.Cu walls vert={len(vx)} horz={len(hy)}")
    east = [64.70 + i * 0.50 for i in range(24)]
    west = [25.10, 25.55, 26.00, 24.70]
    stubs = [78.10, 77.85, 78.35, 77.20]
    south = [65.40, 66.00, 66.60, 67.20, 64.80, 68.00]
    mid = [45.20, 44.60, 43.80, 42.80, 41.60, 14.80, 13.60, 12.40, 10.80, 9.20, 8.40]
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or p["name"] == "VDD_GPIO"
        }
    )
    closed = 0
    for i, name in enumerate(nets):
        hdr = r.primary_header(name)
        p = r.u1(name)
        if not hdr:
            continue
        via = None
        if p:
            via = r.nearest_via(name, p["x"], p["y"], 7.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
        if not via:
            print(f"  no via {name}")
            continue
        hx, hyy = hdr["x"], hdr["y"]
        vx_, vy_ = via["x"], via["y"]
        w = 0.18 if not name.startswith("VDD") else 0.25
        stub = stubs[i % len(stubs)]
        # gate outside courtyard ring
        if vy_ >= 39.5:
            gy = 45.6
        elif vy_ <= 24.8:
            gy = 14.8
        elif vx_ >= 45.0:
            gy = vy_
        else:
            gy = 45.6
        gx = vx_ if vy_ >= 39.5 or vy_ <= 24.8 else 49.4
        if vx_ >= 45.0 and 24.8 < vy_ < 39.5:
            gx, gy = 49.4, vy_

        paths = []
        if hyy > 70:
            col = free_x(vx, name, east if hx >= 56 else west + east, stub, gy)
            yb = free_y(hy, name, south, hx if col is None else col, gx)
            ys = free_y(hy, name, stubs, 6, 112)
            if ys:
                stub = ys
            if col is None:
                col = 65.2 if hx >= 56 else 25.1
            if yb is None:
                yb = 65.6
            # Always stub south of header row first (avoid y=76 pad wall)
            paths.append([(hx, hyy), (hx, stub), (col, stub), (col, yb), (gx, yb), (gx, gy), (vx_, vy_)])
            paths.append([(hx, hyy), (hx, stub), (col, stub), (col, gy), (gx, gy), (vx_, vy_)])
            if name in ADC:
                paths.append([(hx, hyy), (hx, stub), (hx, 58.8), (vx_, 58.8), (vx_, vy_)])
        elif hx > 100:
            xf = free_x(vx, name, [110.8, 111.4, 112.0, 112.6, 105.6, 106.6, 102.4], hyy, gy)
            yn = free_y(hy, name, mid, xf or 111, gx)
            if xf is None:
                xf = 111.2
            if yn is None:
                yn = 14.8
            paths.append([(hx, hyy), (xf, hyy), (xf, yn), (gx, yn), (gx, gy), (vx_, vy_)])
        else:
            col = free_x(vx, name, east, hyy, gy)
            yn = free_y(hy, name, mid, col or 65, gx)
            paths.append([(hx, hyy), (col or 65.2, hyy), (col or 65.2, yn or gy), (gx, yn or gy), (vx_, vy_)])

        ok = False
        for pts in paths:
            if r.bcommit(pts, name, w):
                ok = True
                break
        if not ok:
            # piecewise: stub, then rest
            if r.bcommit([(hx, hyy), (hx, stub)], name, w):
                for pts in paths:
                    rest = pts[1:]
                    if r.bcommit(rest, name, w):
                        ok = True
                        break
        if ok:
            print(f"  B {name} {hdr['ref']}.{hdr['num']} via=({vx_:.1f},{vy_:.1f})")
            closed += 1
            vx, hy = walls(r)  # refresh occupancy
        else:
            if r.route_b_any(hx, hyy, vx_, vy_, name, w, astar=True):
                print(f"  B* {name}")
                closed += 1
                vx, hy = walls(r)
            else:
                print(f"  FAIL {name}")

        # extras from primary header
        if ok or True:
            for extra in r.extras(name, hdr):
                eok = False
                if extra["y"] > 70:
                    ys = free_y(hy, name, [78.10, 78.35, 77.85], hx, extra["x"]) or 78.10
                    pts = [(hx, hyy), (hx, ys), (extra["x"], ys), (extra["x"], extra["y"])]
                    eok = r.bcommit(pts, name, w)
                if not eok and extra["x"] > 100:
                    xf = free_x(vx, name, [111.2, 111.8, 112.4], hyy, extra["y"]) or 111.4
                    pts = [(hx, hyy), (hx, 74.2), (xf, 74.2), (xf, extra["y"]), (extra["x"], extra["y"])]
                    eok = r.bcommit(pts, name, w)
                if not eok and extra["ref"] == "J18" and name in ADC:
                    pts = [(hx, hyy), (hx, 58.8), (extra["x"], 58.8), (extra["x"], extra["y"])]
                    eok = r.bcommit(pts, name, w)
                if not eok:
                    r.route_b_any(hx, hyy, extra["x"], extra["y"], name, w, astar=True)
    print(f"  private closed {closed}/{len(nets)}")


def main():
    pairs, n0, base, _ = run_drc()
    print(f"start unconnected={n0} clear={base.get('clearance', 0)} shorts={base.get('shorting_items', 0)}")
    baseline = {
        "shorting_items": base.get("shorting_items", 0),
        "clearance": base.get("clearance", 0),
        "hole_clearance": base.get("hole_clearance", 0),
    }
    last_good = os.path.join(SNAP_DIR, "after-p015s.kicad_pcb")
    if not os.path.isfile(last_good):
        last_good = os.path.join(SNAP_DIR, "after-gpio2.kicad_pcb")
    board, r = load()

    print("#### occupancy GPIO", flush=True)
    private_gpio(r)
    r.collect()
    got = save_chk(board, r, "gpio4", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-gpio4.kicad_pcb")
    board, r = load()

    print("#### DNP retry", flush=True)
    dnp_stubs(r)
    got = save_chk(board, r, "dnp4", baseline, last_good)
    if got[0] is None:
        print("DNP aborted")
        return 0
    pairs, n, counts = got
    print(f"PASS4 FINAL unconnected={n} shorts={counts.get('shorting_items', 0)} clear={counts.get('clearance', 0)}")
    shutil.copy2(DRC_JSON, f"{ROOT}/reports/DRC_AFTER_CONNECT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
