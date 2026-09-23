#!/usr/bin/env python3
"""Probe ADC B hops on the LIVE board after COEX2 remnant rip. No SaveBoard."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload, waypoint_route  # noqa: E402
from final_pass22 import extra_via_sites  # noqa: E402
import final_pass27 as p27  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu

XS = [
    28.80, 30.40, 31.00, 32.20, 33.00, 33.80, 34.50, 36.50, 37.00, 38.00,
    39.25, 40.25, 40.54, 40.70, 41.25, 41.75, 42.25, 42.75, 43.08, 44.50,
    45.62, 48.16, 50.70,
]
YS = [
    20.80, 22.00, 22.50, 23.10, 23.95, 24.80, 25.20, 25.80, 27.20, 28.50,
    30.80, 33.20, 36.00, 40.50, 43.50, 46.80, 50.00, 54.00, 58.80, 59.20,
    61.20, 62.00,
]


def chk(r, pts, name):
    ok = r.path_clear(pts, B, 0.18, name)
    print(("  CLEAR " if ok else "  BLOCK " + why(r, pts, B, 0.18, name) + " "), pts)
    return ok


def main():
    board, r = reload()
    print("==== confirm remnants gone ====")
    for t in r.tracks:
        if t["n"] != "COEX2" or t["ly"] != B:
            continue
        print(f"  B ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")

    print("\n==== P0.13 from via 23.10 / 23.95 ====")
    for vx, vy in [(42.75, 23.10), (42.75, 23.95)]:
        print(f" -- from ({vx},{vy})")
        for col in (28.80, 30.40, 33.00, 33.80, 34.80, 36.00, 37.00):
            pts = [(vx, vy), (vx, 24.80), (col, 24.80), (col, 59.20), (38.00, 59.20), (38.00, 62.00)]
            chk(r, pts, "P0.13")
        chk(r, [(vx, vy), (vx, 24.80), (38.00, 24.80), (38.00, 62.00)], "P0.13")
        chk(r, [(vx, vy), (vx, 25.80), (38.00, 25.80), (38.00, 62.00)], "P0.13")
        path, cost = waypoint_route(r, vx, vy, 38.00, 62.00, B, 0.18, "P0.13", xs=XS, ys=YS)
        print("  WP", "NO" if path is None else f"L={cost:.1f} {path}")

    print("\n==== P0.16 from (40.70,20.80) ====")
    for col in (40.70, 41.25, 39.00, 38.00, 45.62, 33.00, 30.40):
        pts = [(40.70, 20.80), (40.70, 24.80), (col, 24.80), (col, 59.20), (45.62, 59.20), (45.62, 62.00)]
        chk(r, pts, "P0.16")
    path, cost = waypoint_route(r, 40.70, 20.80, 45.62, 62.00, B, 0.18, "P0.16", xs=XS, ys=YS)
    print("  WP", "NO" if path is None else f"L={cost:.1f} {path}")

    print("\n==== P0.17 from 23.10 / 23.95 ====")
    for vx, vy in [(40.25, 23.10), (40.25, 23.95)]:
        path, cost = waypoint_route(r, vx, vy, 48.16, 62.00, B, 0.18, "P0.17", xs=XS, ys=YS)
        print(f"  WP ({vx},{vy})", "NO" if path is None else f"L={cost:.1f} {path}")
        chk(r, [(vx, vy), (vx, 24.80), (48.16, 24.80), (48.16, 62.00)], "P0.17")
        chk(r, [(vx, vy), (33.00, vy), (33.00, 24.80), (33.00, 59.20), (48.16, 59.20), (48.16, 62.00)], "P0.17")

    print("\n==== P0.14 extra via + B ====")
    p = r.u1("P0.14")
    hits = 0
    for vx, vy in extra_via_sites(p, "P0.14") + [
        (42.25, 25.00),
        (42.25, 24.80),
        (43.50, 25.00),
        (44.00, 24.80),
        (42.25, 20.80),
        (43.80, 24.80),
    ]:
        vx, vy = round(vx, 2), round(vy, 2)
        w = r.via_why(vx, vy, "P0.14", size=0.50, drill=0.30)
        if w:
            continue
        fpath = p27.pad_f_to_via(r, p, vx, vy, "P0.14")
        if not fpath:
            continue
        path, cost = waypoint_route(r, vx, vy, 40.54, 62.00, B, 0.18, "P0.14", xs=XS, ys=YS)
        if path is not None:
            print(f"  HIT via ({vx},{vy}) F={fpath} B L={cost:.1f} {path[:6]}")
            hits += 1
            if hits >= 3:
                break
        else:
            pts = [(vx, vy), (vx, 24.80), (40.54, 24.80), (40.54, 62.00)]
            if r.path_clear(pts, B, 0.18, "P0.14"):
                print(f"  HIT via ({vx},{vy}) F={fpath} B {pts}")
                hits += 1
    print("  P0.14 hits", hits)

    print("\n==== P0.18 extra via + B ====")
    p = r.u1("P0.18")
    hits = 0
    for vx, vy in extra_via_sites(p, "P0.18") + [
        (39.75, 25.00),
        (39.75, 24.80),
        (38.50, 24.80),
        (37.50, 24.80),
        (39.75, 20.80),
    ]:
        vx, vy = round(vx, 2), round(vy, 2)
        w = r.via_why(vx, vy, "P0.18", size=0.50, drill=0.30)
        if w:
            continue
        fpath = p27.pad_f_to_via(r, p, vx, vy, "P0.18")
        if not fpath:
            continue
        path, cost = waypoint_route(r, vx, vy, 50.70, 62.00, B, 0.18, "P0.18", xs=XS, ys=YS)
        if path is not None:
            print(f"  HIT via ({vx},{vy}) F={fpath} B L={cost:.1f}")
            hits += 1
            if hits >= 3:
                break
    print("  P0.18 hits", hits)


if __name__ == "__main__":
    main()
