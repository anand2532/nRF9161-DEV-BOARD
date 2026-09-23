#!/usr/bin/env python3
"""Continue from after-pass9p (99 unconn). No isolated vias. Hop highways correctly."""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, SNAP_DIR, Final, fill_zones, run_drc  # noqa: E402
from final_pass7 import commit_or_why, why  # noqa: E402

LAST = os.path.join(SNAP_DIR, "after-pass9p.kicad_pcb")
ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}


def check(board, r, label, last_good):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} ok={r.ok}",
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


def try_via_then(r, fx, fy, vx, vy, name, pwr, f_pts, b_pts, w_f=None, w_b=None):
    """Add a via only if F path to it is clear; then try B. Remove via if both fail after add... 
    We add only after F path_clear."""
    w_f = r.local_w(name, w_f)
    if not r.via_ok(vx, vy, name, pwr=pwr):
        site = r.local_via(fx, fy, name, pwr=pwr)
        if not site:
            print(f"  no via site {name}")
            return False
        vx, vy = site
    if f_pts is None:
        f_pts = [(fx, fy), (vx, vy)]
    else:
        f_pts = list(f_pts) + [(vx, vy)]
    if not r.path_clear(f_pts, pcbnew.F_Cu, w_f, name):
        print(f"  F to via blocked {name}: {why(r, f_pts, pcbnew.F_Cu, w_f, name)}")
        return False
    r.add_via(vx, vy, r.code_of(name), name, pwr=pwr)
    r.commit(f_pts, pcbnew.F_Cu, w_f, r.code_of(name), name)
    print(f"  via+F {name} ({vx:.2f},{vy:.2f})")
    if b_pts:
        w_b = r.local_w(name, w_b)
        b_pts = [(vx, vy)] + list(b_pts)
        if r.commit(b_pts, pcbnew.B_Cu, w_b, r.code_of(name), name):
            print(f"  B {name}")
            return True
        print(f"  B fail {name}: {why(r, b_pts, pcbnew.B_Cu, w_b, name)}")
        return True  # via is still tied on F, not isolated
    return True


def phase_power(r: Final):
    print("== power islands ==", flush=True)
    # VDD2 C8: south first so we do not scrape C8.2 GND at (54.48,32)
    commit_or_why(
        r,
        [(53.52, 32.00), (53.52, 31.15), (62.40, 31.15), (62.40, 34.20), (59.05, 34.20), (59.05, 36.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 C8 south-then-east",
    )
    # TP12 (60,42) west at y=42 (south of ENABLE y=40.95), then to C9 (53.68,38)
    commit_or_why(
        r,
        [(60.00, 42.00), (49.40, 42.00), (49.40, 38.00), (53.68, 38.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 TP12 west of ENABLE",
    )
    # leftover VDD2 B.Cu island (52.22,26.75) to FB3 F.Cu (68.14,18): via on FB3 side
    try_via_then(
        r,
        68.14,
        18.00,
        68.40,
        17.20,
        "VDD2",
        True,
        [(68.1375, 18.00), (68.40, 18.00)],
        [(68.40, 12.50), (52.22, 12.50), (52.22, 26.75)],
        0.25,
        0.25,
    )

    # VDD2_MID: vertical at x=58.79 would cross VIN y=15.4. West around VIN then south.
    commit_or_why(
        r,
        [
            (58.7875, 18.00),
            (58.7875, 17.30),
            (45.80, 17.30),
            (45.80, 8.20),
            (68.40, 8.20),
            (68.40, 18.00),
            (67.2125, 18.00),
        ],
        pcbnew.F_Cu,
        0.25,
        "VDD2_MID",
        "VDD2_MID west-south around VIN",
    )

    # DEC0: x=49.50 between C14 (47.68,22) and VDD1 (50.68)
    commit_or_why(
        r,
        [(48.72, 31.00), (49.50, 31.00), (49.50, 21.13), (48.65, 21.13)],
        pcbnew.F_Cu,
        0.18,
        "DEC0",
        "DEC0 x=49.50",
    )

    # VIN_FILT: hop P0.01 at x=107.5 (east of P0.01 H which ends x=86.14)
    vf = r.nearest_via("VIN_FILT", 55.35, 13.30, 3)
    if vf:
        try_via_then(
            r,
            51.90,
            21.90,
            53.20,
            22.50,
            "VIN_FILT",
            True,
            [(51.90, 21.90), (53.20, 21.90)],
            [(107.50, 22.50), (107.50, 12.50), (vf["x"], 12.50), (vf["x"], vf["y"])],
            0.25,
            0.25,
        )

    # VIN_F: east hop around P0.01 y=15.2
    try_via_then(
        r,
        71.575,
        19.06,
        71.20,
        18.60,
        "VIN_F",
        True,
        [(71.575, 19.06), (71.20, 19.06)],
        [(107.50, 18.60), (107.50, 12.50), (48.40, 12.50), (48.00, 12.60)],
        0.25,
        0.25,
    )


def phase_local(r: Final):
    print("== SIM/SWD/P0.11/ENABLE local ==", flush=True)
    # SIM_CLK C35 west then north of ENABLE y=40.95 (C35 is at y=44, south of ENABLE)
    commit_or_why(
        r,
        [(71.68, 44.00), (74.20, 44.00), (74.20, 56.60), (77.75, 56.60)],
        pcbnew.F_Cu,
        0.18,
        "SIM_CLK",
        "SIM_CLK C35-U4 east",
    )
    commit_or_why(
        r,
        [(72.00, 36.00), (72.00, 39.40), (69.20, 39.40), (69.20, 44.00), (71.68, 44.00)],
        pcbnew.F_Cu,
        0.18,
        "SIM_CLK",
        "SIM_CLK TP-C35 around ENABLE",
    )
    # SIM_CLK_C: south of U4 then east at y=53.5 (SIM_CD is y=52.04)
    commit_or_why(
        r,
        [(77.75, 55.40), (77.75, 53.50), (98.54, 53.50), (98.54, 45.54)],
        pcbnew.F_Cu,
        0.18,
        "SIM_CLK_C",
        "SIM_CLK_C y=53.5",
    )
    commit_or_why(
        r,
        [(77.35, 55.40), (74.80, 55.40), (74.80, 50.01), (98.54, 50.01)],
        pcbnew.F_Cu,
        0.18,
        "SIM_IO_C",
        "SIM_IO_C west then east",
    )

    # nRESET C39: north of pad (smaller y) to J8, avoid C39.2 GND at x=46.32
    commit_or_why(
        r,
        [(45.68, 16.00), (45.68, 14.50), (38.25, 14.50), (38.25, 23.10)],
        pcbnew.F_Cu,
        0.18,
        "nRESET",
        "nRESET C39-U1via y=14.5",
    )
    commit_or_why(
        r,
        [(45.68, 16.00), (45.68, 14.50), (51.95, 14.50), (51.95, 7.27)],
        pcbnew.F_Cu,
        0.18,
        "nRESET",
        "nRESET C39-J8 y=14.5",
    )

    # P0.11: south of pad row (y=27.15) between P0.12 y=27.5 and... pad 19 is y=28.
    # Via at 48.62,28. Go south to 26.9 (south of P0.12 track at 27.5).
    commit_or_why(
        r,
        [(44.00, 28.00), (45.10, 28.00), (45.10, 26.90), (48.62, 26.90), (48.62, 28.00)],
        pcbnew.F_Cu,
        0.18,
        "P0.11",
        "P0.11 south of P0.12 track",
    )

    # VDD_GPIO U1 pad 12 (44,31.5) to via (40.17,19.13): east then north around courtyard
    commit_or_why(
        r,
        [(44.00, 31.50), (46.60, 31.50), (46.60, 19.13), (40.17, 19.13)],
        pcbnew.F_Cu,
        0.40,
        "VDD_GPIO",
        "VDD_GPIO U1 east-north to via",
    )

    # ENABLE SW1 via at (90.38,26.20) to U1 via (42.75,45.60): east column 107.5
    sw1v = r.nearest_via("ENABLE", 90.38, 26.20, 4)
    ve = r.nearest_via("ENABLE", 42.75, 45.60, 4)
    if sw1v and ve:
        commit_or_why(
            r,
            [
                (sw1v["x"], sw1v["y"]),
                (107.50, sw1v["y"]),
                (107.50, 57.20),
                (70.90, 57.20),
                (70.90, ve["y"]),
                (ve["x"], ve["y"]),
            ],
            pcbnew.B_Cu,
            0.18,
            "ENABLE",
            "ENABLE SW1 via 107.5 (avoid J17 at 108)",
        )
    vb = r.nearest_via("ENABLE", 48.33, 23.13, 3)
    if ve and vb:
        # west of P0.01 x=27.65: x=25.10. Hop P0.01 H y=15.2 at x=25.10 (P0.01 H starts x=27.65)
        commit_or_why(
            r,
            [(ve["x"], ve["y"]), (25.10, ve["y"]), (25.10, vb["y"]), (vb["x"], vb["y"])],
            pcbnew.B_Cu,
            0.18,
            "ENABLE",
            "ENABLE U1-J via west of P0.01",
        )


def phase_gpio_adc_g(r: Final):
    print("== ADC J18 + header duplicates ==", flush=True)
    # ADC nets may use J18_BOX. Connect U1 via to J18, then J18 to J12/J13 along y=78.15.
    adc = {
        "P0.13": ("J18", "1"),
        "P0.14": ("J18", "2"),
        "P0.15": ("J18", "3"),
        "P0.16": ("J18", "4"),
        "P0.17": ("J18", "5"),
        "P0.18": ("J18", "6"),
        "P0.19": ("J18", "7"),
        "P0.20": ("J18", "8"),
        "VDD_GPIO": ("J18", "9"),
    }
    for name, (ref, num) in adc.items():
        via = r.nearest_via(name, 36, 32, 12)
        hdr = r.pad(ref, num, name)
        if via and hdr:
            ok = r.route_b_corridor(via["x"], via["y"], hdr["x"], hdr["y"], name, 0.40 if name == "VDD_GPIO" else 0.18)
            print(f"  ADC {name} via->J18 {ok}")
        primary = r.primary_header(name)
        if hdr and primary and primary is not hdr:
            stub = 78.15
            pts = [(hdr["x"], hdr["y"]), (hdr["x"], stub), (primary["x"], stub), (primary["x"], primary["y"])]
            if r.commit(pts, pcbnew.B_Cu, 0.18 if name != "VDD_GPIO" else 0.40, r.code_of(name), name):
                print(f"  ADC {name} J18->primary stub")
            else:
                print(f"  ADC stub fail {name}: {why(r, pts, pcbnew.B_Cu, 0.18, name)}")

    # G-class east headers: J13 y=76 to J10/J11 x=116 along y=78.15 then x=107.5
    g_pairs = [
        ("P0.21", (76.70, 76.00), (116.00, 28.00)),
        ("P0.22", (79.24, 76.00), (116.00, 30.54)),
        ("P0.23", (81.78, 76.00), (116.00, 33.08)),
        ("P0.24", (84.32, 76.00), (116.00, 35.62)),
        ("P0.30", (99.56, 76.00), (116.00, 46.00)),
        ("P0.31", (102.10, 76.00), (116.00, 48.54)),
        ("P0.17", (66.54, 76.00), (108.00, 26.00)),
        ("P0.18", (69.08, 76.00), (108.00, 28.54)),
        ("P0.19", (53.24, 62.00), (71.62, 76.00)),
    ]
    for name, a, b in g_pairs:
        stub = 78.15
        east = 107.50
        paths = [
            [a, (a[0], stub), (b[0], stub), b],
            [a, (a[0], stub), (east, stub), (east, b[1]), b],
            [a, (east, a[1]), (east, b[1]), b],
        ]
        ok = False
        for pts in paths:
            if r.commit(pts, pcbnew.B_Cu, 0.18, r.code_of(name), name):
                ok = True
                break
        print(f"  G {name} {ok}")


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_power(r)
    got = check(board, r, "pass10p", LAST)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass10p.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_local(r)
    got = check(board, r, "pass10s", last)
    if got[0] is None:
        return 3
    last = os.path.join(SNAP_DIR, "after-pass10s.kicad_pcb")

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_gpio_adc_g(r)
    got = check(board, r, "pass10g", last)
    if got[0] is None:
        return 3
    print("DONE unconn", got[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
