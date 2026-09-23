#!/usr/bin/env python3
"""Explicit detours around known F.Cu walls on the LIVE board.

VIN_FILT x=51.90 blocks VDD1 C6–C3.
GNSS_ANT y≈51 blocks GNSS_VBIAS C30–C28.
VDD1 y=33 blocks VDD2 C8–C9.
Does not restore RF-only backup or wipe B.Cu.
"""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, SNAP_DIR, Final, fill_zones, run_drc  # noqa: E402

LAST_GOOD = os.path.join(SNAP_DIR, "after-pass6g.kicad_pcb")
ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}


def why(r: Final, pts, layer, w, name):
    from complete_route import dist_seg, dist_seg_aabb, seg_seg, in_box, RF_BOX, J18_BOX, ADC, RF_OK

    need = w / 2 + (0.13 if layer == pcbnew.B_Cu else 0.16)
    for a, b in zip(pts, pts[1:]):
        x1, y1, x2, y2 = a[0], a[1], b[0], b[1]
        if hypot(x1, y1, x2, y2) < 0.03:
            continue
        for p in r.pads:
            if p["npth"]:
                if dist_seg(p["x"], p["y"], x1, y1, x2, y2) < p["r"] + 0.22:
                    return f"npth {p['ref']} ({p['x']:.2f},{p['y']:.2f})"
                continue
            if p["name"] == name or not p["num"] and not p["pth"]:
                continue
            if not (layer == pcbnew.F_Cu or p["pth"]):
                continue
            d = dist_seg_aabb(p["x"], p["y"], p["sx"], p["sy"], x1, y1, x2, y2)
            if d < need:
                return f"pad {p['ref']}.{p['num']} {p['name']} d={d:.3f} need={need:.3f} @({p['x']:.2f},{p['y']:.2f})"
        for v in r.vias:
            if v["n"] == name:
                continue
            d = dist_seg(v["x"], v["y"], x1, y1, x2, y2)
            if d < v["r"] + need:
                return f"via {v['n']} d={d:.3f} @({v['x']:.2f},{v['y']:.2f})"
        for t in r.tracks:
            if t["ly"] != layer or t["n"] == name:
                continue
            d = seg_seg((x1, y1), (x2, y2), (t["x1"], t["y1"]), (t["x2"], t["y2"]))
            if d < need + t["w"] / 2:
                return f"trk {t['n']} d={d:.3f} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f}) w={t['w']:.2f}"
        if layer == pcbnew.B_Cu and name not in RF_OK:
            n = max(1, int(hypot(x1, y1, x2, y2) / 0.35))
            for k in range(n + 1):
                t = k / n
                x = x1 + t * (x2 - x1)
                y = y1 + t * (y2 - y1)
                if in_box(x, y, RF_BOX):
                    return f"RF_BOX ({x:.2f},{y:.2f})"
                if name not in ADC and in_box(x, y, J18_BOX):
                    return f"J18_BOX ({x:.2f},{y:.2f})"
    return "unknown"


def commit_or_why(r, pts, layer, w, name, label):
    ok = r.commit(pts, layer, w, r.code_of(name), name)
    if ok:
        print(f"  OK {label}")
        return True
    print(f"  FAIL {label}: {why(r, pts, layer, w, name)}")
    return False


def check(board, r, label, last_good):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} "
        f"x={counts.get('tracks_crossing',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad:
        print(f"ABORT { {k: counts[k] for k in bad} }; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    snap = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, snap)
    return pairs, n, counts


def place_via(r, x, y, name, pwr=False):
    if r.via_ok(x, y, name, pwr=pwr):
        r.add_via(x, y, r.code_of(name), name, pwr=pwr)
        print(f"  via {name} ({x:.2f},{y:.2f})")
        return x, y
    site = r.local_via(x, y, name, pwr=pwr)
    if site:
        r.add_via(site[0], site[1], r.code_of(name), name, pwr=pwr)
        print(f"  via {name} ({site[0]:.2f},{site[1]:.2f}) from ({x:.2f},{y:.2f})")
        return site
    print(f"  no via {name} near ({x:.2f},{y:.2f})")
    return None


def phase_power(r: Final):
    print("== VDD1 via under VIN_FILT ==", flush=True)
    # C6 island ~ (50.68,27) / (50.00,26.30). C3 via already at (53.70,27.13).
    c6 = r.pad("C6", "1")
    v_c3 = r.nearest_via("VDD1", 53.70, 27.13, 2)
    site = None
    for cand in (
        (49.35, 26.40),
        (49.20, 25.60),
        (49.50, 25.20),
        (48.80, 26.80),
        (50.00, 24.80),
        (48.60, 24.80),
        (49.10, 28.80),
        (48.50, 27.40),
    ):
        if r.via_ok(cand[0], cand[1], "VDD1", pwr=True):
            site = cand
            break
    if not site:
        site = r.local_via(50.00, 26.30, "VDD1", pwr=True)
    if site and c6:
        r.add_via(site[0], site[1], r.code_of("VDD1"), "VDD1", pwr=True)
        print(f"  VDD1 via {site}")
        f_ok = False
        for pts in (
            [(c6["x"], c6["y"]), (c6["x"], site[1]), site],
            [(c6["x"], c6["y"]), (50.00, 26.30), (50.00, site[1]), site],
            [(50.00, 26.30), (site[0], 26.30), site],
            [(50.00, 27.00), site],
        ):
            if r.commit(pts, pcbnew.F_Cu, 0.25, r.code_of("VDD1"), "VDD1"):
                f_ok = True
                print("  VDD1 F to via")
                break
        if not f_ok:
            print("  VDD1 F to via FAIL", why(r, [(c6["x"], c6["y"]), site], pcbnew.F_Cu, 0.25, "VDD1"))
        if v_c3:
            commit_or_why(
                r,
                [site, (site[0], v_c3["y"]), (v_c3["x"], v_c3["y"])],
                pcbnew.B_Cu,
                0.25,
                "VDD1",
                "VDD1 B.Cu under VIN_FILT",
            )
            commit_or_why(r, [site, (v_c3["x"], v_c3["y"])], pcbnew.B_Cu, 0.25, "VDD1", "VDD1 B direct")

    print("== VDD2 around VDD1 y=33 wall ==", flush=True)
    # C8 (53.52,32) already tied to (52.22,32). C9 stub (53.68,36).
    for pts, w, lab in (
        ([(53.52, 32.00), (49.20, 32.00), (49.20, 36.00), (53.68, 36.00)], 0.25, "VDD2 west of VDD1"),
        ([(53.52, 32.00), (49.60, 32.00), (49.60, 35.50), (53.68, 35.50), (53.68, 36.00)], 0.18, "VDD2 west thin"),
        ([(53.52, 32.00), (52.22, 32.00), (52.22, 34.20), (49.20, 34.20), (49.20, 36.00), (53.68, 36.00)], 0.25, "VDD2 via-west"),
        ([(60.00, 42.00), (61.50, 42.00), (61.50, 37.13), (59.70, 37.13)], 0.25, "VDD2 TP12 east of GND via"),
        ([(60.00, 42.00), (61.80, 42.00), (61.80, 36.00), (59.05, 36.00)], 0.25, "VDD2 TP12 to C7"),
        ([(58.7875, 18.00), (58.7875, 16.40), (67.2125, 16.40), (67.2125, 18.00)], 0.25, "VDD2_MID south"),
        ([(58.7875, 18.00), (58.7875, 19.60), (67.2125, 19.60), (67.2125, 18.00)], 0.25, "VDD2_MID north"),
        ([(48.72, 31.00), (51.80, 31.00), (51.80, 21.13), (48.65, 21.13)], 0.25, "DEC0 east"),
        ([(48.72, 31.00), (46.40, 31.00), (46.40, 21.13), (48.65, 21.13)], 0.18, "DEC0 west"),
        ([(55.35, 12.00), (57.20, 12.00), (57.20, 21.90), (51.90, 21.90)], 0.25, "VIN_FILT east"),
        ([(55.35, 12.00), (55.35, 10.40), (51.90, 10.40), (51.90, 21.90)], 0.25, "VIN_FILT south"),
        ([(48.00, 12.60), (48.00, 10.20), (71.58, 10.20), (71.58, 19.06)], 0.25, "VIN_F south"),
        ([(48.00, 12.60), (46.20, 12.60), (46.20, 19.06), (71.58, 19.06)], 0.25, "VIN_F west-north"),
    ):
        name = lab.split()[0]
        commit_or_why(r, pts, pcbnew.F_Cu, w, name, lab)


def phase_gnss(r: Final):
    print("== GNSS_VBIAS wrap south-east of GNSS_ANT / U.FL ==", flush=True)
    c30 = r.pad("C30", "1")
    c28 = r.pad("C28", "1")
    if not (c30 and c28):
        return
    # GNSS_ANT trunk ~ (16,51)-(8,50.95). U.FL (5.2,49.6)-(12.4,54.7).
    # Stay x>=13.3 and y>=52.4 or x>=20.
    paths = [
        [(c30["x"], c30["y"]), (21.20, c30["y"]), (21.20, 55.40), (13.35, 55.40), (13.35, 50.00)],
        [(c30["x"], c30["y"]), (21.60, 49.52), (21.60, 55.80), (13.52, 55.80), (13.52, 50.00)],
        [(c30["x"], c30["y"]), (20.40, 49.20), (20.40, 47.20), (13.52, 47.20), (13.52, 50.00)],
        [(c30["x"], c30["y"]), (18.00, 48.40), (12.05, 48.40), (12.05, 50.00)],
        [(c30["x"], c30["y"]), (19.80, 49.52), (19.80, 52.80), (13.80, 52.80), (13.80, 50.00)],
    ]
    for pts in paths:
        if commit_or_why(r, pts, pcbnew.F_Cu, 0.20, "GNSS_VBIAS", f"VBIAS {pts[1]}"):
            return
    # B.Cu inside RF is allowed for GNSS_VBIAS (RF_OK)
    v = r.nearest_via("GNSS_VBIAS", 13.35, 50.00, 3)
    site = place_via(r, 20.80, 49.52, "GNSS_VBIAS", pwr=False)
    if site and v:
        commit_or_why(r, [(c30["x"], c30["y"]), site], pcbnew.F_Cu, 0.20, "GNSS_VBIAS", "VBIAS F to via")
        commit_or_why(
            r,
            [site, (site[0], 55.40), (v["x"], 55.40), (v["x"], v["y"])],
            pcbnew.B_Cu,
            0.20,
            "GNSS_VBIAS",
            "VBIAS B wrap",
        )


def phase_sim_swd(r: Final):
    print("== SIM / nRESET / ENABLE / P0.06 F ==", flush=True)
    for pts, name, w, lab in (
        ([(71.68, 44.00), (70.20, 44.00), (70.20, 36.00), (72.00, 36.00)], "SIM_CLK", 0.18, "SIM_CLK C35-TP"),
        ([(71.68, 44.00), (71.68, 46.80), (77.75, 46.80), (77.75, 56.60)], "SIM_CLK", 0.18, "SIM_CLK C35-U4"),
        ([(77.75, 54.70), (77.75, 52.20), (98.54, 52.20), (98.54, 45.54)], "SIM_CLK_C", 0.18, "SIM_CLK_C south"),
        ([(77.75, 54.70), (86.00, 54.70), (86.00, 45.54), (98.54, 45.54)], "SIM_CLK_C", 0.18, "SIM_CLK_C mid"),
        ([(77.35, 55.40), (77.35, 51.80), (98.54, 51.80), (98.54, 50.01)], "SIM_IO_C", 0.18, "SIM_IO_C south"),
        ([(38.25, 23.10), (38.25, 16.00), (45.68, 16.00)], "nRESET", 0.18, "nRESET U1via-C39"),
        ([(45.68, 16.00), (45.68, 14.60), (51.95, 14.60), (51.95, 7.27)], "nRESET", 0.18, "nRESET C39-J8"),
        ([(45.68, 16.00), (51.95, 16.00), (51.95, 7.27)], "nRESET", 0.18, "nRESET C39-J8 L"),
        ([(44.00, 28.00), (44.00, 26.80), (48.62, 26.80), (48.62, 28.00)], "P0.11", 0.18, "P0.11 south"),
        ([(44.00, 28.00), (46.20, 28.00), (46.20, 26.40), (48.62, 26.40), (48.62, 28.00)], "P0.11", 0.18, "P0.11 east-south"),
        # P0.06: pad 3 (44,36) east then south to via (44,39.90) — pad 2 P0.05 is at (44,36.5)
        ([(44.00, 36.00), (46.40, 36.00), (46.40, 39.90), (44.00, 39.90)], "P0.06", 0.18, "P0.06 east-south via"),
        ([(44.00, 36.00), (47.20, 36.00), (47.20, 40.40), (44.00, 40.40), (44.00, 39.90)], "P0.06", 0.18, "P0.06 farther east"),
    ):
        commit_or_why(r, pts, pcbnew.F_Cu, w, name, lab)

    # ENABLE F (42.75,44) to B (48.33,23.13) — stitch via
    site = place_via(r, 42.75, 45.60, "ENABLE")
    if site:
        commit_or_why(r, [(42.75, 44.00), site], pcbnew.F_Cu, 0.18, "ENABLE", "ENABLE F to via")
        vb = r.nearest_via("ENABLE", 48.33, 23.13, 8)
        if vb:
            commit_or_why(r, [site, (site[0], vb["y"]), (vb["x"], vb["y"])], pcbnew.B_Cu, 0.18, "ENABLE", "ENABLE B")
    sw1 = r.pad("SW1", "1")
    if sw1:
        site = place_via(r, sw1["x"], sw1["y"] + 2.2, "ENABLE")
        vb = r.nearest_via("ENABLE", 52.00, 40.95, 15)
        if site and vb:
            commit_or_why(r, [(sw1["x"], sw1["y"]), site], pcbnew.F_Cu, 0.18, "ENABLE", "SW1 F via")
            commit_or_why(r, [site, (vb["x"], site[1]), (vb["x"], vb["y"])], pcbnew.B_Cu, 0.18, "ENABLE", "SW1 B")


def phase_dnp(r: Final):
    print("== DNP east of 50ohm ==", flush=True)
    # ANT_FIT C22 (19.52,36) to L1.2 (21.52,32); GNSS_ANT wall y=35 x<=21.68
    commit_or_why(
        r,
        [(19.52, 36.00), (19.52, 37.60), (23.70, 37.60), (23.70, 32.00), (21.52, 32.00)],
        pcbnew.F_Cu,
        0.20,
        "ANT_FIT",
        "ANT_FIT east wrap",
    )
    commit_or_why(
        r,
        [(19.52, 48.00), (23.70, 48.00), (23.70, 33.00), (20.48, 33.00)],
        pcbnew.F_Cu,
        0.20,
        "AUX",
        "AUX east wrap",
    )
    commit_or_why(
        r,
        [(19.52, 56.00), (23.70, 56.00), (23.70, 33.00), (19.52, 33.00)],
        pcbnew.F_Cu,
        0.20,
        "AUX_FIT",
        "AUX_FIT east wrap",
    )


def phase_gpio_edges(r: Final):
    """Header duplicate branches on free board edges; ADC may use J18_BOX."""
    print("== header-edge branches ==", flush=True)
    pairs = [
        ("P0.19", 53.24, 62.00, 71.62, 76.00, 0.18),
        ("P0.22", 79.24, 76.00, 116.00, 30.54, 0.18),
        ("P0.21", 76.70, 76.00, 116.00, 28.00, 0.18),
        ("P0.23", 81.78, 76.00, 116.00, 33.08, 0.18),
        ("P0.24", 84.32, 76.00, 116.00, 35.62, 0.18),
        ("P0.30", 99.56, 76.00, 116.00, 46.00, 0.18),
        ("P0.31", 102.10, 76.00, 116.00, 48.54, 0.18),
        ("P0.17", 66.54, 76.00, 108.00, 26.00, 0.18),
        ("P0.18", 69.08, 76.00, 108.00, 28.54, 0.18),
        ("VDD_GPIO", 104.00, 67.08, 107.18, 76.00, 0.40),
        ("VDD_GPIO", 104.00, 67.08, 116.00, 51.08, 0.40),
        ("VDD_GPIO", 116.00, 51.08, 116.00, 38.16, 0.40),
        ("VDD_GPIO", 108.00, 31.08, 116.00, 18.16, 0.40),
    ]
    for name, x1, y1, x2, y2, w in pairs:
        ok = r.route_b_any(x1, y1, x2, y2, name, w, astar=True)
        print(f"  {name} ({x1:.1f},{y1:.1f})->({x2:.1f},{y2:.1f}) {ok}")


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_power(r)
    pairs, n, counts = check(board, r, "pass7p", LAST_GOOD)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass7p.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_gnss(r)
    pairs, n, counts = check(board, r, "pass7g", last)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass7g.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_sim_swd(r)
    pairs, n, counts = check(board, r, "pass7s", last)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass7s.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_dnp(r)
    pairs, n, counts = check(board, r, "pass7d", last)
    if pairs is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass7d.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_gpio_edges(r)
    pairs, n, counts = check(board, r, "pass7e", last)
    if pairs is None:
        return 3
    print("DONE unconn", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
