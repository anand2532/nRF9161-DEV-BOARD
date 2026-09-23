#!/usr/bin/env python3
"""Continue connectivity from the live 100-unconnected board.

Occupancy-aware F.Cu islands + B.Cu corridors that hop P0.01/P0.15/COEX highways.
Never restores RF-only backup, never wipes B.Cu.
"""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    FANOUT_NEED,
    SNAP_DIR,
    WEST_NORTH,
    Final,
    fill_zones,
    run_drc,
)
from final_pass7 import commit_or_why, place_via, why  # noqa: E402

LAST = os.path.join(SNAP_DIR, "after-silk.kicad_pcb")
if not os.path.isfile(LAST):
    LAST = os.path.join(SNAP_DIR, "after-pass8.kicad_pcb")
ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}


def check(board, r, label, last_good):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} "
        f"ok={r.ok}",
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


def phase_power(r: Final):
    print("== power F/B corridors ==", flush=True)
    # VDD1: C6 via (49.2,25.6) to C3 via (53.70,27.13). Stay BETWEEN
    # COEX2 y=24.60 and VDD2 B.Cu y=26.75 — do not vertical-cross either.
    v6 = r.nearest_via("VDD1", 49.20, 25.60, 2)
    v3 = r.nearest_via("VDD1", 53.70, 27.13, 2)
    if v6 and v3:
        commit_or_why(
            r,
            [(v6["x"], v6["y"]), (v3["x"], v6["y"]), (v3["x"], v3["y"])],
            pcbnew.B_Cu,
            0.25,
            "VDD1",
            "VDD1 B between COEX2 and VDD2",
        )

    # VDD2 C8 (53.52,32) to C9 stub y=36: VDD1 H y=33 x<=60. Go EAST of x=60,
    # stay south of C7 GND (60.95,36).
    commit_or_why(
        r,
        [(53.52, 32.00), (62.30, 32.00), (62.30, 34.20), (59.05, 34.20), (59.05, 36.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 C8 east of VDD1 y=33",
    )
    # TP12 via (61.80,45.10) to VDD2 via (59.70,37.13): COEX0 H y=44.4 ends x=64.6
    vtp = r.nearest_via("VDD2", 61.80, 45.10, 3)
    v2 = r.nearest_via("VDD2", 59.70, 37.13, 3) or r.nearest_via("VDD2", 52.22, 32.00, 4)
    if vtp and v2:
        commit_or_why(
            r,
            [(vtp["x"], vtp["y"]), (66.50, vtp["y"]), (66.50, v2["y"]), (v2["x"], v2["y"])],
            pcbnew.B_Cu,
            0.25,
            "VDD2",
            "VDD2 TP12 B east of COEX0",
        )

    # VDD2_MID y=18 blocked by VIN x=62 and x=66. Wrap south of VIN y=10.
    commit_or_why(
        r,
        [(58.7875, 18.00), (58.7875, 8.40), (67.2125, 8.40), (67.2125, 18.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2_MID",
        "VDD2_MID south of VIN",
    )
    va = r.nearest_via("VDD2_MID", 58.79, 18.00, 6)
    vb = r.nearest_via("VDD2_MID", 67.21, 18.00, 6)
    if not va:
        va_pt = place_via(r, 57.40, 17.20, "VDD2_MID", pwr=True)
        if va_pt:
            commit_or_why(r, [(58.7875, 18.00), va_pt], pcbnew.F_Cu, 0.25, "VDD2_MID", "VDD2_MID west via F")
            va = {"x": va_pt[0], "y": va_pt[1]}
    if not vb:
        vb_pt = place_via(r, 68.40, 17.20, "VDD2_MID", pwr=True)
        if vb_pt:
            commit_or_why(r, [(67.2125, 18.00), vb_pt], pcbnew.F_Cu, 0.25, "VDD2_MID", "VDD2_MID east via F")
            vb = {"x": vb_pt[0], "y": vb_pt[1]}
    if va and vb:
        commit_or_why(
            r,
            [(va["x"], va["y"]), (va["x"], 12.50), (vb["x"], 12.50), (vb["x"], vb["y"])],
            pcbnew.B_Cu,
            0.25,
            "VDD2_MID",
            "VDD2_MID B y=12.5",
        )

    # DEC0: x=47.5 between P0.08 via 46.20 and VDD1 x=50.68
    commit_or_why(
        r,
        [(48.72, 31.00), (47.55, 31.00), (47.55, 21.13), (48.65, 21.13)],
        pcbnew.F_Cu,
        0.18,
        "DEC0",
        "DEC0 x=47.55",
    )

    # VIN_FILT: existing via (55.35,13.30) south of VIN y=15.4; track (51.90,21.90) north.
    # B.Cu west of P0.15 (x=41.75) at x=40.2.
    vf = r.nearest_via("VIN_FILT", 55.35, 13.30, 3)
    site = place_via(r, 52.40, 22.40, "VIN_FILT", pwr=True)
    if vf and site:
        commit_or_why(r, [(51.90, 21.90), site], pcbnew.F_Cu, 0.25, "VIN_FILT", "VIN_FILT north via F")
        commit_or_why(
            r,
            [(vf["x"], vf["y"]), (vf["x"], 12.50), (40.20, 12.50), (40.20, site[1]), site],
            pcbnew.B_Cu,
            0.25,
            "VIN_FILT",
            "VIN_FILT B west of P0.15",
        )

    # VIN_F: (71.58,19.06) to (48.00,12.60) — B.Cu y=12.5
    a = place_via(r, 71.20, 19.80, "VIN_F", pwr=True)
    b = place_via(r, 48.40, 12.20, "VIN_F", pwr=True)
    if a:
        commit_or_why(r, [(71.575, 19.06), a], pcbnew.F_Cu, 0.25, "VIN_F", "VIN_F east via F")
    if b:
        commit_or_why(r, [(48.00, 12.60), b], pcbnew.F_Cu, 0.25, "VIN_F", "VIN_F west via F")
    if a and b:
        commit_or_why(r, [a, (a[0], 12.50), (b[0], 12.50), b], pcbnew.B_Cu, 0.25, "VIN_F", "VIN_F B y=12.5")


def phase_sim_swd(r: Final):
    print("== SIM / nRESET / ENABLE / P0.08 / P0.11 ==", flush=True)
    # SIM_CLK C35 (71.68,44) to U4 (77.75,56.6): via near C35, B.Cu x=76.0 (west of SIM_RST 78.25)
    c35 = r.pad("C35", "1")
    u4c = r.pad("U4", "7")
    vclk = r.nearest_via("SIM_CLK", 78.40, 57.73, 4)
    site = place_via(r, 71.00, 42.80, "SIM_CLK")
    if c35 and site:
        commit_or_why(r, [(c35["x"], c35["y"]), (site[0], c35["y"]), site], pcbnew.F_Cu, 0.18, "SIM_CLK", "SIM_CLK C35 via")
    if site and vclk:
        commit_or_why(
            r,
            [site, (76.00, site[1]), (76.00, vclk["y"]), (vclk["x"], vclk["y"])],
            pcbnew.B_Cu,
            0.18,
            "SIM_CLK",
            "SIM_CLK B x=76",
        )
    # TP island (72,36) to C35
    if c35:
        commit_or_why(
            r,
            [(72.00, 36.00), (69.40, 36.00), (69.40, 44.00), (c35["x"], c35["y"])],
            pcbnew.F_Cu,
            0.18,
            "SIM_CLK",
            "SIM_CLK TP-C35 west of GND via",
        )

    # SIM_CLK_C / SIM_IO_C U4 to J7: B.Cu north of SIM_CD y=52, east column
    for net, u4xy, j7xy in (
        ("SIM_CLK_C", (77.75, 55.40), (98.54, 45.54)),
        ("SIM_IO_C", (77.35, 55.40), (98.54, 50.01)),
    ):
        vu = r.nearest_via(net, u4xy[0], u4xy[1], 6)
        vj = r.nearest_via(net, j7xy[0], j7xy[1], 6)
        if not vu:
            vu_pt = place_via(r, u4xy[0] - 1.4, u4xy[1] - 1.6, net)
            if vu_pt:
                commit_or_why(r, [u4xy, vu_pt], pcbnew.F_Cu, 0.18, net, f"{net} U4 via")
                vu = {"x": vu_pt[0], "y": vu_pt[1]}
        if vu and vj:
            ok = r.route_b_corridor(vu["x"], vu["y"], vj["x"], vj["y"], net, 0.18)
            print(f"  {net} corridor {ok}")
            if not ok:
                commit_or_why(
                    r,
                    [(vu["x"], vu["y"]), (vu["x"], 57.20), (vj["x"], 57.20), (vj["x"], vj["y"])],
                    pcbnew.B_Cu,
                    0.18,
                    net,
                    f"{net} B y=57.2",
                )

    # nRESET C39 (45.68,16) to U1 via (38.25,23.1) and J8 (51.95,7.27)
    commit_or_why(
        r,
        [(38.25, 23.10), (38.25, 14.80), (45.68, 14.80), (45.68, 16.00)],
        pcbnew.F_Cu,
        0.18,
        "nRESET",
        "nRESET via-C39 y=14.8",
    )
    commit_or_why(
        r,
        [(45.68, 16.00), (47.20, 16.00), (47.20, 7.27), (51.95, 7.27)],
        pcbnew.F_Cu,
        0.18,
        "nRESET",
        "nRESET C39-J8 east of C39 GND",
    )
    vnr = r.nearest_via("nRESET", 38.25, 23.10, 3)
    vr5 = r.nearest_via("nRESET", 102.40, 36.00, 5)
    if vnr and vr5:
        ok = r.route_b_corridor(vnr["x"], vnr["y"], vr5["x"], vr5["y"], "nRESET", 0.18)
        print(f"  nRESET U1-R5 corridor {ok}")

    # ENABLE U1 pad (42.75,37.25) already has vias at 41.10/45.60. B.Cu to (48.33,23.13)
    # in the y=28-43 band then hop COEX2 at x=70.9 (outside COEX2? COEX2 H is 37.75-105.10 — 70.9 is INSIDE)
    # Hop COEX2 y=24.6 at x=107.5 or x=25.1.
    ve = r.nearest_via("ENABLE", 42.75, 45.60, 3) or r.nearest_via("ENABLE", 42.75, 41.10, 3)
    vb = r.nearest_via("ENABLE", 48.33, 23.13, 3)
    if ve and vb:
        commit_or_why(
            r,
            [(ve["x"], ve["y"]), (25.10, ve["y"]), (25.10, 12.50), (vb["x"], 12.50), (vb["x"], vb["y"])],
            pcbnew.B_Cu,
            0.18,
            "ENABLE",
            "ENABLE B west wrap y=12.5",
        )
    sw1v = r.nearest_via("ENABLE", 90.38, 26.20, 3)
    if sw1v and ve:
        ok = r.route_b_corridor(sw1v["x"], sw1v["y"], ve["x"], ve["y"], "ENABLE", 0.18)
        print(f"  ENABLE SW1 corridor {ok}")
        if not ok:
            commit_or_why(
                r,
                [(sw1v["x"], sw1v["y"]), (107.50, sw1v["y"]), (107.50, 57.20), (70.90, 57.20), (70.90, ve["y"]), (ve["x"], ve["y"])],
                pcbnew.B_Cu,
                0.18,
                "ENABLE",
                "ENABLE SW1 east hop",
            )

    # P0.08 F via (46.20,30) to F track (78.375,24): B.Cu y=28-43 then east
    v08 = r.nearest_via("P0.08", 46.20, 30.00, 2)
    if v08:
        site = place_via(r, 78.40, 24.80, "P0.08")
        if site:
            commit_or_why(r, [(78.375, 24.00), site], pcbnew.F_Cu, 0.18, "P0.08", "P0.08 east via F")
            ok = r.route_b_corridor(v08["x"], v08["y"], site[0], site[1], "P0.08", 0.18)
            print(f"  P0.08 corridor {ok}")

    # P0.11 F.Cu (44,28) to via (48.62,28): P0.12 at y=27.5. Try y=28.55 north of pad row.
    commit_or_why(
        r,
        [(44.00, 28.00), (44.00, 28.70), (48.62, 28.70), (48.62, 28.00)],
        pcbnew.F_Cu,
        0.18,
        "P0.11",
        "P0.11 north of P0.12",
    )


def phase_fanout(r: Final):
    print("== extra U1 vias outside ring ==", flush=True)
    for name in FANOUT_NEED:
        p = r.u1(name)
        if not p:
            continue
        existing = r.nearest_via(name, p["x"], p["y"], limit=8.0)
        if existing and hypot(existing["x"], existing["y"], p["x"], p["y"]) < 8:
            if not r.connected_to_track(p, name):
                r.oblong_escape(p, existing["x"], existing["y"], name)
            continue
        ok = r.fanout_one(name)
        print(f"  fanout {name} {ok}")


def phase_gpio(r: Final):
    print("== private GPIO corridors ==", flush=True)
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or p["name"] == "VDD_GPIO"
        }
    )
    for name in nets:
        hdr = r.primary_header(name)
        p = r.u1(name)
        w = 0.40 if name == "VDD_GPIO" else 0.18
        via = None
        if p:
            via = r.nearest_via(name, p["x"], p["y"], 8.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias and hdr:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
            elif vias:
                via = vias[0]
        if hdr and via:
            if r.route_b_corridor(via["x"], via["y"], hdr["x"], hdr["y"], name, w):
                print(f"  B {name} -> {hdr['ref']}.{hdr['num']}")
            else:
                print(f"  corridor fail {name}")
        elif hdr and p:
            if r.route_b_corridor(p["x"], p["y"], hdr["x"], hdr["y"], name, w):
                print(f"  B-no-via {name}")
            else:
                print(f"  no-via fail {name}")
        if hdr:
            for extra in r.extras(name, hdr):
                if r.route_b_corridor(hdr["x"], hdr["y"], extra["x"], extra["y"], name, w):
                    print(f"  extra {name} {extra['ref']}.{extra['num']}")


def phase_dnp_gnd(board, r: Final):
    print("== DNP local + GND refill ==", flush=True)
    # ANT_FIT C22: only a same-net stub that stays north of GNSS_ANT y=35 and west of GPS x=22.32
    # If L1 is south of GNSS_ANT, a legal short stub cannot reach it — skip if commit fails.
    commit_or_why(
        r,
        [(19.52, 36.00), (19.52, 36.55)],
        pcbnew.F_Cu,
        0.20,
        "ANT_FIT",
        "ANT_FIT local stub (no 50ohm cross)",
    )
    fill_zones(board)
    for cand in ((12.0, 12.0), (96.0, 12.0), (12.0, 68.0), (96.0, 68.0), (80.0, 40.0), (64.0, 12.0)):
        if r.via_ok(cand[0], cand[1], "GND", pwr=True):
            r.add_via(cand[0], cand[1], r.code_of("GND"), "GND", pwr=True)
            print("  GND via", cand)


def main():
    if not os.path.isfile(LAST):
        print("missing last good", LAST)
        return 2
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    phase_power(r)
    got = check(board, r, "pass9p", LAST)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass9p.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_sim_swd(r)
    got = check(board, r, "pass9s", last)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass9s.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_fanout(r)
    got = check(board, r, "pass9f", last)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass9f.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_gpio(r)
    got = check(board, r, "pass9g", last)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass9g.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_dnp_gnd(board, r)
    got = check(board, r, "pass9d", last)
    if got[0] is None:
        return 3
    print("DONE unconn", got[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
