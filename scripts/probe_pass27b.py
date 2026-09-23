#!/usr/bin/env python3
"""Probe B from existing U1 vias to J18 B islands; extra via sites for P0.14/18."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def dump_p015(r):
    print("==== P0.15 (ROUTED template) ====")
    for v in r.vias:
        if v["n"] == "P0.15":
            print(" via", round(v["x"], 2), round(v["y"], 2))
    for t in r.tracks:
        if t["n"] != "P0.15":
            continue
        ly = "F" if t["ly"] == F else ("B" if t["ly"] == B else "?")
        print(f"  {ly} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")


def b_paths(vx, vy, bx, by):
    xs = [vx, bx, 38.00, 40.54, 42.75, 43.08, 45.62, 48.16, 50.70, 36.00, 34.00, 32.00]
    ys = [vy, by, 24.00, 22.00, 20.80, 23.10, 23.95, 46.80, 50.00, 54.00, 58.80, 61.20, 62.00]
    cands = [
        [(vx, vy), (bx, vy), (bx, by)],
        [(vx, vy), (vx, by), (bx, by)],
        [(vx, vy), (vx, 58.80), (bx, 58.80), (bx, by)],
        [(vx, vy), (vx, 61.20), (bx, 61.20), (bx, by)],
        [(vx, vy), (32.00, vy), (32.00, by), (bx, by)],
        [(vx, vy), (34.00, vy), (34.00, 58.80), (bx, 58.80), (bx, by)],
        [(vx, vy), (36.00, vy), (36.00, 58.80), (bx, 58.80), (bx, by)],
        [(vx, vy), (vx, 50.00), (38.00, 50.00), (38.00, by), (bx, by)],
        [(vx, vy), (vx, 46.80), (30.90, 46.80), (30.90, 58.80), (bx, 58.80), (bx, by)],
        [(vx, vy), (vx, 20.80), (bx, 20.80), (bx, by)],
        [(vx, vy), (45.62, vy), (45.62, by)],
        [(vx, vy), (38.00, vy), (38.00, by), (bx, by)],
        [(vx, vy), (40.54, vy), (40.54, by)],
        [(vx, vy), (48.16, vy), (48.16, by)],
        [(vx, vy), (50.70, vy), (50.70, by)],
        [(vx, vy), (vx, 22.40), (32.50, 22.40), (32.50, 61.20), (bx, 61.20), (bx, by)],
        [(vx, vy), (vx, 21.50), (28.50, 21.50), (28.50, 61.20), (bx, 61.20), (bx, by)],
        [(vx, vy), (43.08, vy), (43.08, 61.20), (bx, 61.20), (bx, by)],
        [(vx, vy), (vx, 54.00), (55.00, 54.00), (55.00, by), (bx, by)],
        [(vx, vy), (55.00, vy), (55.00, by), (bx, by)],
        [(vx, vy), (vx, 22.00), (55.00, 22.00), (55.00, by), (bx, by)],
        [(vx, vy), (vx, 24.60), (55.78, 24.60), (55.78, by), (bx, by)],
    ]
    return cands


def try_b(r, name, vx, vy, bx, by):
    print(f"\n-- {name} B from via ({vx:.2f},{vy:.2f}) to island ({bx:.2f},{by:.2f}) --")
    hits = 0
    for pts in b_paths(vx, vy, bx, by):
        if r.path_clear(pts, B, 0.18, name):
            print("  HIT", pts)
            hits += 1
            if hits >= 4:
                return
    if not hits:
        pts = [(vx, vy), (bx, vy), (bx, by)]
        print("  miss HV:", why(r, pts, B, 0.18, name))
        pts = [(vx, vy), (vx, by), (bx, by)]
        print("  miss VH:", why(r, pts, B, 0.18, name))
        pts = [(vx, vy), (vx, 58.80), (bx, 58.80), (bx, by)]
        print("  miss y=58.80:", why(r, pts, B, 0.18, name))
        pts = [(vx, vy), (32.00, vy), (32.00, by), (bx, by)]
        print("  miss x=32:", why(r, pts, B, 0.18, name))
        pts = [(vx, vy), (55.00, vy), (55.00, by), (bx, by)]
        print("  miss x=55:", why(r, pts, B, 0.18, name))


def scan_vias(r, name, px, py):
    print(f"\n==== extra via scan {name} pad ({px:.2f},{py:.2f}) ====")
    ok = []
    xs = []
    for dx in [-3.0, -2.5, -2.1, -1.8, -1.5, -1.2, -0.6, 0, 0.6, 1.2, 1.5, 1.8, 2.1, 2.5, 3.0]:
        xs.append(round(px + dx, 2))
    ys = []
    for dy in [-3.5, -3.0, -2.5, -2.1, -1.8, -1.5, -1.2, 0, 1.2, 1.5, 1.8, 2.1]:
        ys.append(round(py + dy, 2))
    ys += [24.60, 24.30, 24.00, 23.70, 23.40, 23.10, 22.80, 22.40, 21.80, 20.80]
    seen = set()
    for vx in xs:
        for vy in ys:
            if (vx, vy) in seen:
                continue
            seen.add((vx, vy))
            d = hypot(vx, vy, px, py)
            if d < 1.10 or d > 6.5:
                continue
            w = r.via_why(vx, vy, name, size=0.50, drill=0.30)
            sz = (0.50, 0.30)
            if w is not None:
                w = r.via_why(vx, vy, name, size=0.45, drill=0.25)
                sz = (0.45, 0.25)
                if w is not None:
                    continue
            f_cands = [
                [(px, py), (px, vy), (vx, vy)],
                [(px, py), (vx, py), (vx, vy)],
                [(px, py), (px, py - 2.0), (vx, py - 2.0), (vx, vy)],
            ]
            fpath = next((pts for pts in f_cands if r.path_clear(pts, F, 0.18, name)), None)
            if not fpath:
                continue
            ok.append((vx, vy, sz, fpath, d))
    print(f"  {len(ok)} via+F sites")
    for item in ok[:20]:
        print("   ", item)
    return ok


def try_p011(r):
    print("\n==== P0.11 F jogs around P0.10 via (47.40,28.50) ====")
    a, b = (44.00, 28.00), (48.62, 28.00)
    cands = [
        [a, (44.00, 26.40), (48.62, 26.40), b],
        [a, (44.00, 26.20), (48.62, 26.20), b],
        [a, (44.00, 25.80), (48.62, 25.80), b],
        [a, (44.00, 25.40), (49.92, 25.40), (49.92, 28.00)],
        [a, (46.20, 28.00), (46.20, 26.20), (48.62, 26.20), b],
        [a, (44.00, 29.60), (48.62, 29.60), b],
        [a, (44.00, 30.40), (48.62, 30.40), b],
        [a, (45.15, 28.00), (45.15, 26.20), (48.62, 26.20), b],
        # B hop instead
    ]
    for pts in cands:
        if r.path_clear(pts, F, 0.18, "P0.11"):
            print("  F HIT", pts)
        else:
            print("  F miss", why(r, pts, F, 0.18, "P0.11"))
    # existing vias (48.62,28) (49.92,28) — B then F?
    for vx, vy in [(48.62, 28.00), (49.92, 28.00)]:
        for px, py in [(44.00, 24.00), (44.00, 23.10), (45.15, 24.00)]:
            w = r.via_why(px, py, "P0.11", size=0.50, drill=0.30)
            print(f"  via ({px},{py})", w)
            if w is None:
                fpath = [(44.00, 28.00), (44.00, py), (px, py)]
                print("   F", r.path_clear(fpath, F, 0.18, "P0.11"), why(r, fpath, F, 0.18, "P0.11"))
                bpath = [(px, py), (vx, py), (vx, vy)]
                print("   B", r.path_clear(bpath, B, 0.18, "P0.11"), why(r, bpath, B, 0.18, "P0.11"))


def try_p006_j9(r):
    print("\n==== P0.06 J9 from J12 wrap like P0.04 ====")
    # J12 copper at (21.24,76) B; wrap column x=25.55 y=44.50-74
    vias = [
        (21.24, 77.20, 0.50, 0.30),
        (108.45, 52.50, 0.50, 0.30),
        (108.45, 49.20, 0.50, 0.30),
        (113.80, 36.80, 0.50, 0.30),
    ]
    for x, y, s, d in vias:
        print(f"  via ({x},{y})", r.via_why(x, y, "P0.06", size=s, drill=d))
    routes = [
        ([(21.24, 76.00), (21.24, 77.20)], B),
        (
            [
                (21.24, 77.20),
                (21.24, 78.80),
                (114.80, 78.80),
                (114.80, 52.50),
                (108.45, 52.50),
            ],
            F,
        ),
        ([(108.45, 52.50), (108.45, 49.20)], B),
        ([(108.45, 49.20), (113.80, 49.20), (113.80, 36.80)], F),
        (
            [
                (113.80, 36.80),
                (113.80, 10.00),
                (106.70, 10.00),
                (106.70, 8.40),
                (116.00, 8.40),
                (116.00, 8.00),
            ],
            B,
        ),
    ]
    for pts, ly in routes:
        ok = r.path_clear(pts, ly, 0.18, "P0.06")
        print("  path", "F" if ly == F else "B", ok if ok else why(r, pts, ly, 0.18, "P0.06"), pts[:3], "...")


def main():
    board, r = reload()
    dump_p015(r)
    jobs = [
        ("P0.13", 42.75, 23.95, 38.00, 62.00),
        ("P0.13", 42.75, 23.10, 38.00, 62.00),
        ("P0.16", 40.70, 20.80, 45.62, 62.00),
        ("P0.17", 40.25, 23.95, 48.16, 62.00),
        ("P0.17", 40.25, 23.10, 48.16, 62.00),
        ("P0.19", 39.25, 23.10, 53.24, 62.00),
        ("P0.20", 36.20, 20.80, 55.78, 62.00),
    ]
    for name, vx, vy, bx, by in jobs:
        try_b(r, name, vx, vy, bx, by)
    scan_vias(r, "P0.14", 42.25, 26.75)
    scan_vias(r, "P0.18", 39.75, 26.75)
    try_p011(r)
    try_p006_j9(r)


if __name__ == "__main__":
    main()
