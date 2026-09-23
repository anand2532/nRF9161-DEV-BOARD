#!/usr/bin/env python3
"""Targeted remaining F.Cu islands / F-B stitches / DNP stubs on the LIVE board.

Does not restore RF-only backup, wipe B.Cu, or call complete_route.main().
Aborts and restores last_good on shorts/clearance/hole_clearance.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot, nm, vec  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    SNAP_DIR,
    Final,
    fill_zones,
    parse_drc,
    run_drc,
)

LAST_GOOD = os.path.join(SNAP_DIR, "after-p015s.kicad_pcb")
ABORT_TYPES = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}


def dump_region(r: Final, x0, y0, x1, y1, label):
    print(f"\n-- {label} [{x0},{y0}]-[{x1},{y1}] --")
    for p in r.pads:
        if x0 <= p["x"] <= x1 and y0 <= p["y"] <= y1 and p["num"]:
            print(f"  PAD {p['ref']}.{p['num']:4s} {p['name']:12s} ({p['x']:.2f},{p['y']:.2f}) {p['sx']:.2f}x{p['sy']:.2f}")
    for v in r.vias:
        if x0 <= v["x"] <= x1 and y0 <= v["y"] <= y1:
            print(f"  VIA {v['n']:12s} ({v['x']:.2f},{v['y']:.2f})")
    for t in r.tracks:
        mx = (t["x1"] + t["x2"]) / 2
        my = (t["y1"] + t["y2"]) / 2
        if x0 <= mx <= x1 and y0 <= my <= y1:
            ly = "F" if t["ly"] == pcbnew.F_Cu else "B"
            print(
                f"  TR {ly} {t['n']:12s} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f}) w={t['w']:.3f}"
            )


def try_jogs(r: Final, x1, y1, x2, y2, name, layer, w, extras=()):
    code = r.code_of(name)
    paths = r.jogs(x1, y1, x2, y2, extra=extras)
    # denser small offsets for 0402 gaps
    for d in (-0.15, 0.15, -0.25, 0.25, -0.45, 0.45, -0.55, 0.55, -0.90, 0.90):
        paths.append([(x1, y1), (x1, y1 + d), (x2, y1 + d), (x2, y2)])
        paths.append([(x1, y1), (x1 + d, y1), (x1 + d, y2), (x2, y2)])
        paths.append([(x1, y1), (x2 + d, y1), (x2 + d, y2), (x2, y2)])
        paths.append([(x1, y1), (x1, y2 + d), (x2, y2 + d), (x2, y2)])
    for pts in paths:
        if r.commit(pts, layer, w, code, name):
            return True
    return False


def stitch_fb(r: Final, fx, fy, bx, by, name, pwr=False):
    """Place a via that both F and B copper can reach."""
    sites = [(bx, by), (fx, fy), ((fx + bx) / 2, (fy + by) / 2)]
    for dx in (0, 0.45, -0.45, 0.80, -0.80, 1.15, -1.15, 1.60, -1.60):
        for dy in (0, 0.45, -0.45, 0.80, -0.80, 1.15, -1.15):
            sites.append((bx + dx, by + dy))
            sites.append((fx + dx, fy + dy))
    site = None
    for sx, sy in sites:
        if r.via_ok(sx, sy, name, pwr=pwr):
            site = (sx, sy)
            break
    if not site:
        print(f"  stitch no-via {name}")
        return False
    r.add_via(site[0], site[1], r.code_of(name), name, pwr=pwr)
    okf = try_jogs(r, fx, fy, site[0], site[1], name, pcbnew.F_Cu, r.local_w(name))
    okb = try_jogs(r, bx, by, site[0], site[1], name, pcbnew.B_Cu, r.local_w(name, 0.13 if not pwr else 0.25))
    print(f"  stitch {name} via=({site[0]:.2f},{site[1]:.2f}) F={okf} B={okb}")
    return okf or okb


def nearest_copper(r: Final, name, x, y, layer=None):
    best = None
    bd = 1e9
    for t in r.tracks:
        if t["n"] != name:
            continue
        if layer is not None and t["ly"] != layer:
            continue
        for px, py in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            d = hypot(x, y, px, py)
            if d < bd:
                bd, best = d, (px, py, t["ly"])
    for v in r.vias:
        if v["n"] != name:
            continue
        d = hypot(x, y, v["x"], v["y"])
        if d < bd:
            bd, best = d, (v["x"], v["y"], None)
    return best, bd


def check_or_restore(board, r, label, last_good):
    fill_zones(board)
    pcbnew.Refresh() if hasattr(pcbnew, "Refresh") else None
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} "
        f"x={counts.get('tracks_crossing',0)} ok={r.ok} fail={r.fail}",
        flush=True,
    )
    bad = [k for k in ABORT_TYPES if counts.get(k, 0) > 0]
    if bad:
        print(f"ABORT { {k: counts[k] for k in bad} }; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    snap = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, snap)
    return pairs, n, counts


def phase_remaining_f(r: Final):
    print("== remaining F.Cu islands ==", flush=True)

    # VDD1 C3 (53.05,26) to existing copper ~ (50.68,27)
    c3 = r.pad("C3", "1")
    if c3:
        tgt, d = nearest_copper(r, "VDD1", c3["x"], c3["y"], pcbnew.F_Cu)
        print(f"  VDD1 C3->copper d={d:.3f} tgt={tgt}")
        if tgt and d > 0.2:
            w = 0.20
            ok = try_jogs(r, c3["x"], c3["y"], tgt[0], tgt[1], "VDD1", pcbnew.F_Cu, w)
            if not ok:
                ok = try_jogs(r, c3["x"], c3["y"], tgt[0], tgt[1], "VDD1", pcbnew.F_Cu, 0.15)
            print(f"  VDD1 {ok}")

    # VDD2 two short F.Cu gaps
    for ax, ay, bx, by in ((53.68, 36.00, 53.52, 32.00), (60.00, 42.00, 59.05, 37.30)):
        ok = try_jogs(r, ax, ay, bx, by, "VDD2", pcbnew.F_Cu, 0.25)
        if not ok:
            ok = try_jogs(r, ax, ay, bx, by, "VDD2", pcbnew.F_Cu, 0.18)
        print(f"  VDD2 ({ax},{ay})-({bx},{by}) {ok}")

    # VDD2_MID along y=18
    ok = try_jogs(r, 58.7875, 18.00, 67.2125, 18.00, "VDD2_MID", pcbnew.F_Cu, 0.25, extras=(-0.8, 0.8, -1.4, 1.4))
    if not ok:
        ok = try_jogs(r, 58.7875, 18.00, 67.2125, 18.00, "VDD2_MID", pcbnew.F_Cu, 0.18)
    print(f"  VDD2_MID {ok}")

    # DEC0 C13 track to via
    c13 = r.pad("C13", "1")
    via = r.nearest_via("DEC0", 48.65, 21.13, 5)
    if c13 and via:
        ok = try_jogs(r, c13["x"], c13["y"], via["x"], via["y"], "DEC0", pcbnew.F_Cu, 0.25)
        if not ok:
            ok = try_jogs(r, 48.72, 31.00, via["x"], via["y"], "DEC0", pcbnew.F_Cu, 0.18)
        print(f"  DEC0 {ok}")

    # VIN_FILT
    ok = try_jogs(r, 55.35, 12.00, 51.90, 21.90, "VIN_FILT", pcbnew.F_Cu, 0.25)
    if not ok:
        ok = try_jogs(r, 55.35, 12.00, 51.90, 21.90, "VIN_FILT", pcbnew.F_Cu, 0.18)
    print(f"  VIN_FILT {ok}")

    # VIN_F: F.Cu only if a via pair exists; skip GNSS
    a, da = nearest_copper(r, "VIN_F", 71.575, 19.06, pcbnew.F_Cu)
    b, db = nearest_copper(r, "VIN_F", 48.00, 12.60, pcbnew.F_Cu)
    print(f"  VIN_F ends {a} {da:.2f} / {b} {db:.2f}")
    if a and b:
        ok = try_jogs(r, a[0], a[1], b[0], b[1], "VIN_F", pcbnew.F_Cu, 0.25)
        if not ok:
            va = r.nearest_via("VIN_F", a[0], a[1], 8)
            vb = r.nearest_via("VIN_F", b[0], b[1], 8)
            if va and vb:
                ok = try_jogs(r, va["x"], va["y"], vb["x"], vb["y"], "VIN_F", pcbnew.B_Cu, 0.25)
        print(f"  VIN_F {ok}")

    # GNSS_VBIAS: C30 to west copper at x=13.52, stay off GNSS_ANT spine x≈16-18.5 y≈40-48
    c30 = r.pad("C30", "1")
    if c30:
        tgt, d = nearest_copper(r, "GNSS_VBIAS", c30["x"], c30["y"], pcbnew.F_Cu)
        print(f"  GNSS_VBIAS C30-> {tgt} d={d:.3f}")
        if tgt:
            # wrap SOUTH of C30 (y>=50.6) then west to x=13.52, never along y=46.8 or x=16-18.5 trunk
            w = 0.20
            paths = [
                [(c30["x"], c30["y"]), (c30["x"], 50.80), (12.80, 50.80), (tgt[0], tgt[1])],
                [(c30["x"], c30["y"]), (18.80, c30["y"]), (18.80, 51.20), (12.80, 51.20), (tgt[0], tgt[1])],
                [(c30["x"], c30["y"]), (c30["x"], 51.40), (13.52, 51.40), (tgt[0], tgt[1])],
                [(c30["x"], c30["y"]), (19.20, 50.00), (19.20, 51.60), (12.40, 51.60), (tgt[0], tgt[1])],
            ]
            ok = False
            for pts in paths:
                if r.commit(pts, pcbnew.F_Cu, w, r.code_of("GNSS_VBIAS"), "GNSS_VBIAS"):
                    ok = True
                    break
            if not ok:
                ok = try_jogs(r, c30["x"], c30["y"], tgt[0], tgt[1], "GNSS_VBIAS", pcbnew.F_Cu, 0.20)
            print(f"  GNSS_VBIAS {ok}")

    # SIM local 0402
    for name, ax, ay, bx, by, w in (
        ("SIM_CLK", 72.00, 36.00, 71.68, 44.00, 0.18),
        ("SIM_CLK", 71.68, 44.00, 77.75, 56.60, 0.18),
        ("SIM_1V8", 78.65, 56.60, 71.70, 48.60, 0.18),
        ("SIM_CLK_C", 77.75, 54.70, 98.54, 45.54, 0.18),
        ("SIM_IO_C", 77.35, 55.40, 98.54, 50.01, 0.18),
        ("nRESET", 38.25, 23.10, 45.68, 16.00, 0.18),
        ("nRESET", 45.68, 16.00, 51.95, 7.27, 0.18),
        ("P0.11", 44.00, 28.00, 48.62, 28.00, 0.18),
        ("ENABLE", 42.75, 44.00, 48.33, 23.13, 0.18),
    ):
        ok = try_jogs(r, ax, ay, bx, by, name, pcbnew.F_Cu, w)
        print(f"  {name} ({ax},{ay})-({bx},{by}) {ok}")

    # ENABLE SW1: use B.Cu if F fails
    sw1 = r.pad("SW1", "1")
    if sw1:
        tgt, d = nearest_copper(r, "ENABLE", sw1["x"], sw1["y"], pcbnew.F_Cu)
        print(f"  ENABLE SW1 d={d:.2f} {tgt}")
        if tgt and d > 0.4:
            ok = try_jogs(r, sw1["x"], sw1["y"], tgt[0], tgt[1], "ENABLE", pcbnew.F_Cu, 0.18)
            if not ok:
                va = r.search_via(sw1["x"], sw1["y"] + 1.6, "ENABLE", pwr=False)
                vb = r.nearest_via("ENABLE", tgt[0], tgt[1], 12)
                if va and vb:
                    ok = try_jogs(r, va[0], va[1], vb["x"], vb["y"], "ENABLE", pcbnew.B_Cu, 0.18)
            print(f"  ENABLE SW1 {ok}")


def phase_stitches(r: Final):
    print("== F/B stitches ==", flush=True)
    # SIM_RST U4 pad F vs nearby B.Cu
    stitch_fb(r, 78.25, 56.60, 79.375833, 57.25, "SIM_RST")
    # P0.06 F stub vs B.Cu south of courtyard
    stitch_fb(r, 44.00, 36.00, 44.00, 43.80, "P0.06")
    # P0.08 F via island vs F.Cu east — actually F via to F track, try F then B
    ok = try_jogs(r, 46.20, 30.00, 78.375, 26.00, "P0.08", pcbnew.F_Cu, 0.18)
    if not ok:
        va = r.nearest_via("P0.08", 46.20, 30.00, 2)
        site = r.search_via(78.375, 26.00, "P0.08")
        if va and site:
            ok = try_jogs(r, va["x"], va["y"], site[0], site[1], "P0.08", pcbnew.B_Cu, 0.13)
    print(f"  P0.08 {ok}")


def phase_dnp(r: Final):
    print("== DNP stubs ==", flush=True)
    for net, ref in (("ANT_FIT", "C22"), ("AUX", "C23"), ("AUX_FIT", "C24"), ("ANT", "C21"), ("GPS", "C31")):
        p = r.pad(ref, "1")
        if not p:
            continue
        tgt, d = nearest_copper(r, net, p["x"], p["y"], pcbnew.F_Cu)
        print(f"  {net} {ref} d={d:.3f} tgt={tgt}")
        if not tgt or d < 0.15:
            continue
        # short same-net stub; stay east of 50 ohm trunks (xj~21.6+)
        xj = max(p["x"], tgt[0], 21.55)
        paths = [
            [(p["x"], p["y"]), (xj, p["y"]), (xj, tgt[1]), (tgt[0], tgt[1])],
            [(p["x"], p["y"]), (p["x"] + 0.6, p["y"]), (p["x"] + 0.6, tgt[1]), (tgt[0], tgt[1])],
            [(p["x"], p["y"]), (22.20, p["y"]), (22.20, tgt[1]), (tgt[0], tgt[1])],
        ]
        ok = False
        for pts in paths:
            if r.commit(pts, pcbnew.F_Cu, 0.20, r.code_of(net), net):
                ok = True
                break
        if not ok:
            ok = try_jogs(r, p["x"], p["y"], tgt[0], tgt[1], net, pcbnew.F_Cu, 0.20)
        print(f"  {net} stub {ok}")


def phase_gnd(board, r: Final):
    print("== GND refill ==", flush=True)
    fill_zones(board)
    # extra GND stitch vias on F.Cu islands if DRC still reports zone-to-zone
    for cand in (
        (8.0, 8.0),
        (110.0, 8.0),
        (8.0, 72.0),
        (110.0, 72.0),
        (60.0, 8.0),
        (90.0, 70.0),
        (70.0, 50.0),
        (55.0, 55.0),
    ):
        if r.via_ok(cand[0], cand[1], "GND", pwr=True):
            r.add_via(cand[0], cand[1], r.code_of("GND"), "GND", pwr=True)
            print("  GND via", cand)


def main():
    if not os.path.isfile(LAST_GOOD):
        print("missing last_good", LAST_GOOD)
        return 2
    # ensure live matches last_good before we start
    live_sha = subprocess.check_output(["sha256sum", BOARD]).decode().split()[0]
    good_sha = subprocess.check_output(["sha256sum", LAST_GOOD]).decode().split()[0]
    print("live", live_sha[:16], "good", good_sha[:16], "match", live_sha == good_sha)
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    dump_region(r, 49.5, 24.5, 54.5, 28.5, "VDD1 C3")
    dump_region(r, 12.0, 47.5, 20.0, 52.0, "GNSS_VBIAS C30")
    dump_region(r, 52.5, 30.5, 61.0, 43.0, "VDD2")
    dump_region(r, 76.5, 54.5, 80.5, 58.5, "SIM_RST U4")
    dump_region(r, 17.5, 30.0, 23.0, 38.0, "ANT_FIT C22")

    phase_remaining_f(r)
    pairs, n, counts = check_or_restore(board, r, "pass6f", LAST_GOOD)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass6f.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_stitches(r)
    pairs, n, counts = check_or_restore(board, r, "pass6s", last)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass6s.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_dnp(r)
    pairs, n, counts = check_or_restore(board, r, "pass6d", last)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass6d.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_gnd(board, r)
    pairs, n, counts = check_or_restore(board, r, "pass6g", last)
    if pairs is None:
        return 3
    print("DONE unconn", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
