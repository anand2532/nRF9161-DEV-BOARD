#!/usr/bin/env python3
"""From after-power: free north B.Cu, nudge P0.15, occupancy-aware GPIO columns."""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import ADC, BOARD, hypot, vec  # noqa: E402
from final_connect import DRC_JSON, Final, SNAP_DIR, run_drc  # noqa: E402
from final_pass2 import dnp_stubs, save_chk  # noqa: E402

ROOT = "/home/anand/kicad-projects/nRF9161-DEV-BOARD"


def load():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def reroute_p001_bus(r: Final):
    """Move P0.01 north bus y=15.2 -> y=8.4 so courtyard vias can be reached from the north."""
    kill = []
    for tr in r.board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.01" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        y1, y2 = pcbnew.ToMM(s.y), pcbnew.ToMM(e.y)
        x1, x2 = pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)
        if abs(y1 - 15.20) < 0.08 or abs(y2 - 15.20) < 0.08:
            kill.append(tr)
        elif abs(x1 - 86.14) < 0.08 and abs(x2 - 86.14) < 0.08 and min(y1, y2) < 16:
            kill.append(tr)
        elif abs(x1 - 27.65) < 0.08 and abs(x2 - 27.65) < 0.08:
            # keep the south vertical but we'll replace the whole west column
            kill.append(tr)
    for tr in kill:
        r.board.Remove(tr)
    r.collect()
    # Rebuild: via (86.14,19.13) - north 8.4 - west 27.65 - south to header stub
    pts = [
        (86.14, 19.13),
        (86.14, 8.40),
        (27.65, 8.40),
        (27.65, 77.45),
        (8.54, 77.45),
        (8.54, 76.00),
    ]
    if r.bcommit(pts, "P0.01", 0.18):
        print("  rebuilt P0.01 bus at y=8.4")
        return True
    print("  P0.01 rebuild failed")
    return False


def nudge_p015(r: Final):
    n = 0
    for tr in r.board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        if abs(x1 - 106.10) < 0.08 and abs(x2 - 106.10) < 0.08:
            tr.SetStart(vec(106.00, y1))
            tr.SetEnd(vec(106.00, y2))
            n += 1
            continue
        nx1, nx2 = x1, x2
        if abs(x1 - 106.10) < 0.08 and abs(x2 - 106.10) > 0.4:
            nx1 = 106.00
        if abs(x2 - 106.10) < 0.08 and abs(x1 - 106.10) > 0.4:
            nx2 = 106.00
        if nx1 != x1 or nx2 != x2:
            tr.SetStart(vec(nx1, y1))
            tr.SetEnd(vec(nx2, y2))
            n += 1
    print(f"  P0.15 nudge {n}")
    r.collect()


def gpio_east_wrap(r: Final):
    """One private path per net: south stub, east x≈112, then y-bus to courtyard gate."""
    nets = []
    for p in r.pads:
        n = p["name"]
        if n.startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or n == "VDD_GPIO":
            if n not in nets:
                nets.append(n)
    nets.sort()
    closed = 0
    used_x = {27.65, 106.00, 105.10, 64.60, 37.75, 110.60, 48.05}
    used_y = {8.40, 15.20, 20.60, 24.60, 77.45, 62.00, 58.80, 44.40}
    xi = 0
    yi = 0
    east_cols = [112.40, 113.00, 113.60, 111.80, 114.20, 111.20, 114.80, 110.00]
    ybuses = [45.80, 46.40, 47.00, 43.20, 42.40, 13.20, 12.40, 11.60, 10.80, 9.60, 40.80, 48.20]
    stubs = [78.30, 78.00, 78.60, 77.15]

    def take_x():
        nonlocal xi
        for _ in range(len(east_cols)):
            x = east_cols[xi % len(east_cols)]
            xi += 1
            if min(abs(x - u) for u in used_x) >= 0.50:
                used_x.add(x)
                return x
        return east_cols[xi % len(east_cols)]

    def take_y():
        nonlocal yi
        for _ in range(len(ybuses)):
            y = ybuses[yi % len(ybuses)]
            yi += 1
            if min(abs(y - u) for u in used_y) >= 0.50:
                used_y.add(y)
                return y
        return ybuses[yi % len(ybuses)]

    for i, name in enumerate(nets):
        hdr = r.primary_header(name)
        p = r.u1(name)
        via = None
        if p:
            via = r.nearest_via(name, p["x"], p["y"], 7.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias and hdr:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
            elif vias:
                via = vias[0]
        if not hdr or not via:
            print(f"  skip {name} hdr={bool(hdr)} via={bool(via)}")
            continue
        hx, hy = hdr["x"], hdr["y"]
        vx, vy = via["x"], via["y"]
        w = 0.25 if name.startswith("VDD") else 0.18
        xf = take_x()
        yb = take_y()
        stub = stubs[i % len(stubs)]
        if vy <= 24.8:
            gy = 13.20
        elif vy >= 39.5:
            gy = 45.80
        else:
            gy = yb
        paths = []
        if hy > 70:
            paths.append(
                [(hx, hy), (hx, stub), (xf, stub), (xf, yb), (vx, yb), (vx, gy if abs(gy - yb) > 0.3 else vy), (vx, vy)]
            )
            paths.append([(hx, hy), (hx, stub), (xf, stub), (xf, gy), (vx, gy), (vx, vy)])
        elif hx > 100:
            paths.append([(hx, hy), (xf, hy), (xf, yb), (vx, yb), (vx, vy)])
            paths.append([(hx, hy), (xf, hy), (xf, gy), (vx, gy), (vx, vy)])
        else:
            paths.append([(hx, hy), (hx, yb), (xf, yb), (vx, yb), (vx, vy)])
        ok = False
        for pts in paths:
            # compress duplicate points
            comp = [pts[0]]
            for q in pts[1:]:
                if hypot(comp[-1][0], comp[-1][1], q[0], q[1]) > 0.05:
                    comp.append(q)
            if r.bcommit(comp, name, w):
                ok = True
                break
        if ok:
            print(f"  B {name} -> {hdr['ref']}.{hdr['num']} col={xf:.1f} yb={yb:.1f}")
            closed += 1
            used_x.add(xf)
            used_y.add(yb)
        else:
            print(f"  FAIL {name} via=({vx:.1f},{vy:.1f}) hdr=({hx:.1f},{hy:.1f})")
    print(f"  closed {closed}/{len(nets)}")
    return closed


def main():
    pairs, n0, base, _ = run_drc()
    print(f"start unconnected={n0} clear={base.get('clearance', 0)} shorts={base.get('shorting_items', 0)}")
    baseline = {
        "shorting_items": 0,
        "clearance": max(base.get("clearance", 0), 1),
        "hole_clearance": 0,
    }
    last_good = os.path.join(SNAP_DIR, "after-power.kicad_pcb")
    board, r = load()

    print("#### free P0.01 bus + P0.15", flush=True)
    reroute_p001_bus(r)
    nudge_p015(r)
    r.collect()
    got = save_chk(board, r, "busfix", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-busfix.kicad_pcb")
    baseline["clearance"] = counts.get("clearance", 0)
    board, r = load()

    print("#### east-wrap GPIO", flush=True)
    gpio_east_wrap(r)
    r.collect()
    got = save_chk(board, r, "gpio5", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    print(f"PASS5 unconnected={n} shorts={counts.get('shorting_items', 0)} clear={counts.get('clearance', 0)}")
    shutil.copy2(DRC_JSON, f"{ROOT}/reports/DRC_AFTER_CONNECT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
