#!/usr/bin/env python3
"""Read-only probe: U1-to-existing-B islands and short F leftovers. No SaveBoard."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import reload  # noqa: E402
from final_pass22 import extra_via_sites  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
NETS = [
    "P0.13",
    "P0.14",
    "P0.16",
    "P0.17",
    "P0.18",
    "P0.19",
    "P0.20",
    "P0.11",
    "P0.06",
    "P0.02",
    "P0.08",
    "VIN_FILT",
    "VIN_F",
    "nRESET",
    "SIM_CLK",
    "COEX0",
]


def dump_net(r, name):
    p = r.u1(name)
    print(f"\n==== {name} U1={p} ====")
    vias = [v for v in r.vias if v["n"] == name]
    print(" vias:", [(round(v["x"], 2), round(v["y"], 2), round(v["r"] * 2, 2)) for v in vias])
    for t in r.tracks:
        if t["n"] != name:
            continue
        ly = "F" if t["ly"] == F else ("B" if t["ly"] == B else str(t["ly"]))
        print(
            f"  {ly} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f}) w={t['w']:.2f}"
        )
    pads = [q for q in r.pads if q["name"] == name and (q["pth"] or q["ref"] == "U1")]
    print(
        " pads:",
        [(q["ref"], q["num"], round(q["x"], 2), round(q["y"], 2)) for q in pads],
    )


def nearest_b(r, name, x, y):
    best = None
    bd = 1e9
    for t in r.tracks:
        if t["n"] != name or t["ly"] != B:
            continue
        for px, py in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            d = hypot(px, py, x, y)
            if d < bd:
                bd = d
                best = (px, py, d, t)
    for v in r.vias:
        if v["n"] != name:
            continue
        d = hypot(v["x"], v["y"], x, y)
        if d < bd:
            bd = d
            best = (v["x"], v["y"], d, "via")
    return best


def try_sites(r, name):
    p = r.u1(name)
    if not p:
        print(f"  no U1 for {name}")
        return
    nb = nearest_b(r, name, p["x"], p["y"])
    print(f"  nearest B/via to U1: {nb}")
    sites = extra_via_sites(p, name)
    extra = []
    px, py = p["x"], p["y"]
    for o in (1.15, 1.30, 1.50, 1.80, 2.10):
        extra += [
            (px, py - 0.95 - o),
            (px + 0.95 + o, py),
            (px - 0.95 - o, py),
            (px + 0.60, py - 0.95 - o),
            (px - 0.60, py - 0.95 - o),
            (px + 1.20, py - 0.95 - o),
            (px - 1.20, py - 0.95 - o),
        ]
    # south toward J18
    extra += [(px, 24.00), (px, 23.50), (px, 24.60), (px + 1.5, 24.00), (px - 1.5, 24.00)]
    extra += [(40.54, 24.00), (38.00, 24.00), (45.62, 24.00), (41.25, 24.00)]
    seen = set()
    ok_via = []
    for vx, vy in sites + extra:
        vx, vy = round(vx, 2), round(vy, 2)
        if (vx, vy) in seen:
            continue
        seen.add((vx, vy))
        w = r.via_why(vx, vy, name, size=0.50, drill=0.30)
        sz = (0.50, 0.30)
        if w is not None:
            w2 = r.via_why(vx, vy, name, size=0.45, drill=0.25)
            if w2 is not None:
                continue
            w = None
            sz = (0.45, 0.25)
        f_cands = [
            [(px, py), (px, vy), (vx, vy)],
            [(px, py), (vx, py), (vx, vy)],
        ]
        fpath = next((pts for pts in f_cands if r.path_clear(pts, F, 0.18, name)), None)
        if not fpath:
            continue
        ok_via.append((vx, vy, sz, fpath))
    print(f"  via+F clear sites ({len(ok_via)}): {ok_via[:12]}")
    targets = []
    if nb:
        targets.append((nb[0], nb[1]))
    # J18 pads
    for t in r.tracks:
        if t["n"] == name and t["ly"] == B:
            targets.append((t["x1"], t["y1"]))
            targets.append((t["x2"], t["y2"]))
    # unique nearby
    uniq = []
    for tx, ty in targets:
        tx, ty = round(tx, 2), round(ty, 2)
        if (tx, ty) in uniq:
            continue
        uniq.append((tx, ty))
    print(f"  B targets: {uniq[:20]}")
    hits = 0
    for vx, vy, sz, fpath in ok_via[:8]:
        for bx, by in uniq[:8]:
            b_cands = [
                [(vx, vy), (bx, vy), (bx, by)],
                [(vx, vy), (vx, by), (bx, by)],
                [(vx, vy), (vx, 24.50), (bx, 24.50), (bx, by)],
                [(vx, vy), (38.00, vy), (38.00, by), (bx, by)],
                [(vx, vy), (vx, 58.80), (bx, 58.80), (bx, by)],
                [(vx, vy), (vx, 50.00), (bx, 50.00), (bx, by)],
                [(vx, vy), (40.54, vy), (40.54, by), (bx, by)],
                [(vx, vy), (45.62, vy), (45.62, by), (bx, by)],
                [(vx, vy), (50.70, vy), (50.70, by), (bx, by)],
            ]
            for pts in b_cands:
                if r.path_clear(pts, B, 0.18, name):
                    print(f"  HIT via {vx, vy} {sz} B {pts} to {bx, by}")
                    hits += 1
                    break
            if hits >= 3:
                break
        if hits >= 3:
            break
    if not hits:
        # diagnose first via's first target
        if ok_via and uniq:
            vx, vy, sz, fpath = ok_via[0]
            bx, by = uniq[0]
            pts = [(vx, vy), (bx, vy), (bx, by)]
            print(f"  miss sample via {vx,vy} HV to {bx,by}: {why(r, pts, B, 0.18, name)}")
            pts2 = [(vx, vy), (vx, by), (bx, by)]
            print(f"  miss sample VH: {why(r, pts2, B, 0.18, name)}")


def try_f_hop(r, name, a, b):
    print(f"\n==== F hop {name} {a} -> {b} dist={hypot(a[0], a[1], b[0], b[1]):.3f} ====")
    cands = [
        [a, b],
        [a, (b[0], a[1]), b],
        [a, (a[0], b[1]), b],
        [a, (a[0], a[1] - 0.80), (b[0], a[1] - 0.80), b],
        [a, (a[0], a[1] + 0.80), (b[0], a[1] + 0.80), b],
        [a, (a[0], 27.20), (b[0], 27.20), b],
        [a, (a[0], 28.80), (b[0], 28.80), b],
    ]
    for pts in cands:
        if r.path_clear(pts, F, 0.18, name):
            print("  F CLEAR", pts)
            return
        print("  F block", pts, why(r, pts, F, 0.18, name))


def main():
    board, r = reload()
    for name in NETS:
        dump_net(r, name)
    for name in ("P0.13", "P0.14", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20"):
        try_sites(r, name)
    try_f_hop(r, "P0.11", (44.00, 28.00), (48.62, 28.00))
    try_f_hop(r, "COEX0", (38.75, 37.25), (29.81, 22.00))
    # P0.06 J12 copper
    dump_net(r, "P0.06")
    p6 = [t for t in r.tracks if t["n"] == "P0.06"]
    print("P0.06 track count", len(p6))


if __name__ == "__main__":
    main()
