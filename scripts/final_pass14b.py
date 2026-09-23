#!/usr/bin/env python3
"""Pass 14b: remaining F islands after zone-fill hops, plus P0.06 headers.

Loads the LIVE board (post-pass14, unconn=92). Does not restore backups.
Does not re-place the 11 extra U1 vias. DRC after each net with zone refill.
"""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, SNAP_DIR, fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    apply_net,
    check,
    class_counts,
    reload,
    snap_path,
    try_any,
    try_commit,
    try_wp,
    write_gpio_csv,
    write_release,
    write_unconnected_csv,
)

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"


def route_nreset_c39_via(r):
    """C39 SMD pad is 0.3 mm from existing nRESET B.Cu. Drop a via + F stub."""
    print("== nRESET C39 pad to B.Cu stub (via + 0.3 mm F) ==", flush=True)
    vx, vy = 45.68, 16.30
    whyv = r.via_why(vx, vy, "nRESET", pwr=False)
    if whyv is not None:
        vx, vy = 45.20, 16.30
        whyv = r.via_why(vx, vy, "nRESET", pwr=False)
        print(f"  try ({vx:.2f},{vy:.2f}) {whyv}")
    if whyv is not None:
        print(f"  no via site: {whyv}")
        # F.Cu pad to existing J8 copper if a via already exists nearby
        try_wp(r, "nRESET", pcbnew.F_Cu, 0.18, 45.68, 16.00, 38.25, 21.80, "F C39-U1", max_l=20)
        return
    fpts = [(45.68, 16.00), (vx, vy)]
    bpts = [(vx, vy), (45.68, 16.30)]
    if not r.path_clear(fpts, pcbnew.F_Cu, 0.18, "nRESET"):
        print(f"  F stub: {why(r, fpts, pcbnew.F_Cu, 0.18, 'nRESET')}")
        return
    r.add_via(vx, vy, r.code_of("nRESET"), "nRESET", pwr=False)
    r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("nRESET"), "nRESET")
    if r.path_clear(bpts, pcbnew.B_Cu, 0.18, "nRESET"):
        r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("nRESET"), "nRESET")
    print(f"  OK nRESET via ({vx:.2f},{vy:.2f}) at C39")


def route_sim_clk_c35(r):
    """C35 F.Cu pad to SIM_CLK B.Cu at (70.90, 42.40)."""
    print("== SIM_CLK C35 to B.Cu (70.90,42.40) ==", flush=True)
    if try_any(
        r,
        "SIM_CLK",
        pcbnew.F_Cu,
        0.18,
        [
            ([(71.68, 44.00), (70.90, 44.00), (70.90, 42.40)], "F C35 to B track"),
            ([(71.68, 44.00), (71.68, 42.40), (70.90, 42.40)], "F C35 south then west"),
        ],
    ):
        return
    vx, vy = 71.68, 43.20
    if r.via_why(vx, vy, "SIM_CLK", pwr=False) is None:
        fpts = [(71.68, 44.00), (vx, vy)]
        bpts = [(vx, vy), (70.90, 42.40)]
        if r.path_clear(fpts, pcbnew.F_Cu, 0.18, "SIM_CLK") and r.path_clear(
            bpts, pcbnew.B_Cu, 0.18, "SIM_CLK"
        ):
            r.add_via(vx, vy, r.code_of("SIM_CLK"), "SIM_CLK", pwr=False)
            r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("SIM_CLK"), "SIM_CLK")
            r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("SIM_CLK"), "SIM_CLK")
            print("  OK SIM_CLK C35 via")
            return
    try_wp(r, "SIM_CLK", pcbnew.F_Cu, 0.18, 71.68, 44.00, 70.90, 42.40, "F C35-B", max_l=8)


def route_vdd2_fb3(r):
    print("== VDD2 FB3 around new VDD2_MID B.Cu y=16.87 ==", flush=True)
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.25,
        [
            (
                [
                    (68.14, 16.87),
                    (68.14, 15.40),
                    (61.30, 15.40),
                    (61.30, 42.00),
                ],
                "B y15.4 north of VDD2_MID to TP12",
            ),
            (
                [
                    (68.14, 16.87),
                    (69.80, 16.87),
                    (69.80, 18.50),
                    (61.30, 18.50),
                    (61.30, 42.00),
                ],
                "B east then y18.5 to TP12",
            ),
            (
                [
                    (68.14, 16.87),
                    (68.14, 15.40),
                    (52.22, 15.40),
                    (52.22, 32.00),
                ],
                "B y15.4 to C8 via",
            ),
        ],
    ):
        return
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 68.14, 16.87, 61.30, 42.00, "B FB3-TP12", max_l=40)
    try_wp(r, "VDD2", pcbnew.F_Cu, 0.25, 68.40, 18.00, 59.05, 36.00, "F FB3-C9", max_l=40)


def route_nreset_j8_r5(r):
    print("== nRESET J8 via east first (avoid P0.22 via x=53.65 y=6) ==", flush=True)
    if try_any(
        r,
        "nRESET",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (53.65, 7.27),
                    (56.50, 7.27),
                    (56.50, 5.40),
                    (112.40, 5.40),
                    (112.40, 58.80),
                    (101.68, 58.80),
                ],
                "east of P0.22 via then y5.4",
            ),
            (
                [
                    (53.65, 7.27),
                    (56.50, 7.27),
                    (56.50, 8.80),
                    (112.40, 8.80),
                    (112.40, 58.80),
                    (101.68, 58.80),
                ],
                "east then y8.8",
            ),
        ],
    ):
        return
    try_wp(r, "nRESET", pcbnew.B_Cu, 0.18, 53.65, 7.27, 101.68, 58.80, "B J8-R5", max_l=90)


def route_sim_clk_c(r):
    print("== SIM_CLK_C around new SIM_CLK B.Cu y=57.73 ==", flush=True)
    if try_any(
        r,
        "SIM_CLK_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (76.62, 56.05),
                    (80.40, 56.05),
                    (80.40, 54.40),
                    (85.00, 54.40),
                    (85.00, 45.54),
                    (98.54, 45.54),
                    (98.54, 46.67),
                ],
                "east of SIM_CLK then J7",
            ),
            (
                [
                    (76.62, 56.05),
                    (76.62, 53.20),
                    (80.40, 53.20),
                    (80.40, 46.67),
                    (99.19, 46.67),
                ],
                "north of U4 then east",
            ),
            (
                [
                    (76.62, 56.05),
                    (75.20, 56.05),
                    (75.20, 59.80),
                    (85.00, 59.80),
                    (85.00, 46.67),
                    (99.19, 46.67),
                ],
                "south of SIM_CLK y57.73 then east",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_CLK_C", pcbnew.B_Cu, 0.18, 76.62, 56.05, 99.19, 46.67, "B U4-J7", max_l=45)
    try_wp(r, "SIM_CLK_C", pcbnew.F_Cu, 0.18, 77.75, 55.40, 98.54, 45.54, "F U4-J7", max_l=45)


def route_sim_io_c(r):
    print("== SIM_IO_C around SIM_CLK / SIM_CLK_C ==", flush=True)
    if try_any(
        r,
        "SIM_IO_C",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (77.35, 55.40),
                    (81.20, 55.40),
                    (81.20, 50.01),
                    (98.54, 50.01),
                ],
                "east of U4 then J7",
            ),
            (
                [
                    (77.35, 55.40),
                    (77.35, 52.20),
                    (85.00, 52.20),
                    (85.00, 50.01),
                    (98.54, 50.01),
                ],
                "north then east y52.2",
            ),
        ],
    ):
        return
    try_wp(r, "SIM_IO_C", pcbnew.B_Cu, 0.18, 77.35, 55.40, 98.54, 50.01, "B U4-J7", max_l=45)


def route_vin_filt(r):
    print("== VIN_FILT B.Cu at y=13.3 (VIN H is F.Cu y=15.40) ==", flush=True)
    if try_any(
        r,
        "VIN_FILT",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (64.50, 13.30),
                    (64.50, 21.90),
                    (51.90, 21.90),
                ],
                "B y13.3 east of VIN then island",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 16.20),
                    (64.50, 16.20),
                    (64.50, 21.90),
                    (51.90, 21.90),
                ],
                "B y16.2 south of VIN H",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 12.20),
                    (47.40, 12.20),
                    (47.40, 21.90),
                    (51.90, 21.90),
                ],
                "B west of VIN x=48 then island",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_FILT", pcbnew.B_Cu, 0.18, 55.35, 13.30, 51.90, 21.90, "B JP1-island", max_l=30)
    try_wp(r, "VIN_FILT", pcbnew.F_Cu, 0.18, 55.35, 12.00, 51.90, 21.90, "F JP1-island", max_l=25)


def route_vin_f(r):
    print("== VIN_F around nRESET y=11.20 / VDD_GPIO y=14.80 ==", flush=True)
    if try_any(
        r,
        "VIN_F",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (49.30, 12.60),
                    (49.30, 13.80),
                    (64.50, 13.80),
                    (64.50, 17.66),
                    (71.58, 17.66),
                ],
                "F y13.8 south of nRESET y11.2",
            ),
            (
                [
                    (49.30, 12.60),
                    (47.40, 12.60),
                    (47.40, 17.66),
                    (71.58, 17.66),
                ],
                "F west of F1 then y17.66",
            ),
        ],
    ):
        return
    if try_any(
        r,
        "VIN_F",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (49.30, 12.60),
                    (49.30, 13.80),
                    (64.50, 13.80),
                    (64.50, 17.66),
                    (71.58, 17.66),
                ],
                "B y13.8",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_F", pcbnew.F_Cu, 0.18, 49.30, 12.60, 71.58, 17.66, "F F1-FB4", max_l=40)


def route_dec0(r):
    print("== DEC0 C13 around ENABLE via (48.33,23.13) / C13 GND ==", flush=True)
    for vx, vy in [(47.00, 29.60), (50.00, 29.60), (47.00, 31.20), (50.40, 31.00)]:
        whyv = r.via_why(vx, vy, "DEC0", pwr=False)
        if whyv is not None:
            print(f"  via ({vx:.2f},{vy:.2f}) {whyv}")
            continue
        fpts = [(48.72, 29.60), (vx, vy)] if abs(vy - 29.60) < 0.05 else [(48.72, 31.00), (48.72, vy), (vx, vy)]
        bpts = [(vx, vy), (vx, 21.13), (48.65, 21.13)]
        if r.path_clear(fpts, pcbnew.F_Cu, 0.18, "DEC0") and r.path_clear(
            bpts, pcbnew.B_Cu, 0.18, "DEC0"
        ):
            r.add_via(vx, vy, r.code_of("DEC0"), "DEC0", pwr=False)
            r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("DEC0"), "DEC0")
            r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("DEC0"), "DEC0")
            print(f"  OK DEC0 via ({vx:.2f},{vy:.2f})")
            return
        print(f"  paths blocked at ({vx:.2f},{vy:.2f})")
    try_wp(r, "DEC0", pcbnew.F_Cu, 0.18, 48.72, 31.00, 48.65, 21.13, "F C13-via", max_l=18)


def route_enable_c14(r):
    print("== ENABLE C14 F (47.68,22) to U1 (42.75,44) ==", flush=True)
    if try_any(
        r,
        "ENABLE",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (47.68, 22.00),
                    (46.20, 22.00),
                    (46.20, 44.00),
                    (42.75, 44.00),
                ],
                "F west of C14 to U1",
            ),
            (
                [
                    (47.68, 22.00),
                    (47.68, 19.80),
                    (42.75, 19.80),
                    (42.75, 44.00),
                ],
                "F north then U1 column",
            ),
        ],
    ):
        return
    try_wp(r, "ENABLE", pcbnew.F_Cu, 0.18, 47.68, 22.00, 42.75, 44.00, "F C14-U1", max_l=35)
    try_wp(r, "ENABLE", pcbnew.B_Cu, 0.18, 48.33, 23.13, 42.75, 41.10, "B C14-U1", max_l=35)


def route_p008(r):
    print("== P0.08 around new VDD2 B.Cu ==", flush=True)
    if try_any(
        r,
        "P0.08",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (46.20, 30.00),
                    (50.00, 30.00),
                    (50.00, 34.20),
                    (79.68, 34.20),
                    (79.68, 26.00),
                ],
                "B y34.2 east of VDD1 via to SW3",
            ),
            (
                [
                    (46.20, 30.00),
                    (46.20, 35.20),
                    (79.68, 35.20),
                    (79.68, 26.00),
                ],
                "B y35.2",
            ),
            (
                [
                    (46.20, 30.00),
                    (51.90, 30.00),
                    (51.90, 23.50),
                    (79.68, 23.50),
                    (79.68, 26.00),
                ],
                "B y23.5",
            ),
        ],
    ):
        return
    try_wp(r, "P0.08", pcbnew.B_Cu, 0.18, 46.20, 30.00, 79.68, 26.00, "B U1-SW3", max_l=55)


def route_p006(r):
    print("== P0.06 south of SIM_RST y=57.8 then stub; J9 from stub ==", flush=True)
    j12 = [
        (
            [
                (48.62, 43.80),
                (48.62, 57.80),
                (104.50, 57.80),
                (104.50, 65.20),
                (104.50, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y57.8 east 104.5 then stub (around J15?)",
        ),
        (
            [
                (48.62, 43.80),
                (48.62, 57.80),
                (101.20, 57.80),
                (101.20, 73.40),
                (101.20, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y57.8 x101.2 stub",
        ),
        (
            [
                (48.62, 43.80),
                (48.62, 57.80),
                (99.50, 57.80),
                (99.50, 73.40),
                (110.90, 73.40),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "x99.5 then stub east of P0.15 at y78.7",
        ),
        (
            [
                (44.00, 43.80),
                (44.00, 57.80),
                (32.67, 57.80),
                (32.67, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "west at y57.8 (south of COEX0 V) to 32.67 stub",
        ),
        (
            [
                (48.62, 43.80),
                (70.90, 43.80),
                (70.90, 57.80),
                (101.20, 57.80),
                (101.20, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "east 70.9 (west of SIM_RST x78) then south",
        ),
        (
            [
                (48.62, 36.00),
                (51.50, 36.00),
                (51.50, 34.89),
                (110.90, 34.89),
                (110.90, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "between J17 pads y=34.89",
        ),
    ]
    if not try_any(r, "P0.06", pcbnew.B_Cu, 0.18, j12):
        if not try_wp(r, "P0.06", pcbnew.B_Cu, 0.18, 48.62, 43.80, 21.24, 76.00, "B island-J12", max_l=220):
            print("  J12.7 not closed")
            return
    j9 = [
        (
            [
                (21.24, 76.00),
                (21.24, 78.70),
                (110.90, 78.70),
                (110.90, 8.00),
                (116.00, 8.00),
            ],
            "stub 110.9 to J9",
        ),
        (
            [
                (21.24, 78.70),
                (112.40, 78.70),
                (112.40, 8.00),
                (116.00, 8.00),
            ],
            "stub 112.4 to J9",
        ),
    ]
    if not try_any(r, "P0.06", pcbnew.B_Cu, 0.18, j9):
        if not try_wp(r, "P0.06", pcbnew.B_Cu, 0.18, 21.24, 76.00, 116.00, 8.00, "B J12-J9", max_l=220):
            print("  J9.1 not closed")


def main():
    start = snap_path("pass14b-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} {dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        print("start already has shorts; abort")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    steps = [
        ("nRESET_C39via", route_nreset_c39_via, "C39 pad 0.3 mm from B.Cu stub"),
        ("SIM_CLK_C35", route_sim_clk_c35, "C35 to B.Cu (70.90,42.40)"),
        ("VDD2_FB3", route_vdd2_fb3, "FB3 around VDD2_MID y=16.87"),
        ("nRESET_J8R5", route_nreset_j8_r5, "J8 east of P0.22 via"),
        ("SIM_CLK_C", route_sim_clk_c, "U4-J7 around SIM_CLK y=57.73"),
        ("SIM_IO_C", route_sim_io_c, "U4-J7"),
        ("VIN_FILT", route_vin_filt, "B y13.3 around VIN H"),
        ("VIN_F", route_vin_f, "around nRESET y=11.2"),
        ("DEC0", route_dec0, "C13 around ENABLE via"),
        ("ENABLE_C14", route_enable_c14, "C14 to U1"),
        ("P0.08", route_p008, "U1-SW3 around VDD2 B.Cu"),
        ("P0.06", route_p006, "J12.7 y57.8 / stub; J9 from stub"),
    ]
    for name, fn, note in steps:
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok, ceiling = apply_net(board, r, name, fn, last, ceiling)
        if not ok:
            status = "not closed (DRC revert or blocked)"
        elif ceiling < before:
            status = f"closed ({before}→{ceiling})"
        else:
            status = "not closed (no DRC-clean copper)"
        log.append((name, status, note))
        print(f"  kept={ok} ceiling={ceiling} {status}", flush=True)

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass14"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board)
    # Honest pass14 combined note is in FINAL_FAB_RELEASE from write_release
    # (it will say start=n0 of THIS subpass). Patch header to keep 98→end.
    print(
        f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} "
        f"classes={dict(class_counts(pairs))}"
    )
    for name, status, note in log:
        print(f"  {name}: {status} ({note[:80]})")
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= n0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
