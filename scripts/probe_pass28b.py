#!/usr/bin/env python3
"""Probe COEX2 join at y=33.20 and post-rip ADC B hops (simulated by path_clear)."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass7 import why  # noqa: E402
from final_pass14 import reload, waypoint_route  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def chk(r, pts, ly, name, w=0.18):
    ok = r.path_clear(pts, ly, w, name)
    print(("  CLEAR " if ok else "  BLOCK " + why(r, pts, ly, w, name) + " "), pts)
    return ok


def main():
    board, r = reload()
    print("==== COEX2 join U1 V to wrap y=33.20 ====")
    for pts in [
        [(37.75, 33.20), (40.50, 33.20)],
        [(37.75, 34.00), (40.50, 34.00), (40.50, 33.20)],
        [(37.75, 41.10), (40.50, 41.10), (40.50, 33.20)],
        [(37.75, 33.20), (58.80, 33.20)],
        [(37.75, 36.00), (40.50, 36.00), (40.50, 33.20)],
        [(37.75, 32.00), (40.50, 32.00), (40.50, 33.20)],
        [(37.75, 35.00), (58.80, 35.00), (58.80, 33.20)],
    ]:
        chk(r, pts, B, "COEX2")

    print("\n==== ADC B from existing vias (remnants still present) ====")
    jobs = [
        ("P0.13", 42.75, 23.10, 38.00, 62.00),
        ("P0.13", 42.75, 23.95, 38.00, 62.00),
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.17", 40.25, 23.10, 48.16, 62.00),
        ("P0.17", 40.25, 23.95, 48.16, 62.00),
    ]
    xs = [32.2, 34.5, 36.5, 38.0, 40.25, 40.7, 41.75, 42.75, 43.08, 45.62, 48.16, 50.7]
    ys = [20.8, 23.1, 24.0, 25.5, 27.2, 30.8, 34.5, 40.5, 46.8, 50.0, 54.0, 58.8, 59.2, 62.0]
    for name, x1, y1, x2, y2 in jobs:
        path, cost = waypoint_route(r, x1, y1, x2, y2, B, 0.18, name, xs=xs, ys=ys)
        print(name, "NO" if path is None else f"L={cost:.1f} {path[:8]}...")


if __name__ == "__main__":
    main()
