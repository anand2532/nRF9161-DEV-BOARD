#!/usr/bin/env python3
"""Pass 14c: stitch vias + remaining short hops on the LIVE board."""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    apply_net,
    class_counts,
    reload,
    snap_path,
    try_any,
    try_wp,
    write_gpio_csv,
    write_release,
    write_unconnected_csv,
)
from final_connect import run_drc  # noqa: E402

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"


def route_sim_clk_via(r):
    print("== SIM_CLK via at B.Cu (70.90,42.40) to stitch C35 F.Cu ==", flush=True)
    for vx, vy in [(70.90, 42.40), (71.20, 42.70), (70.50, 42.70), (71.68, 42.80)]:
        w = r.via_why(vx, vy, "SIM_CLK", pwr=False)
        print(f"  via_why ({vx:.2f},{vy:.2f}) {w}")
        if w is not None:
            continue
        fpts = [(71.68, 44.00), (71.68, vy), (vx, vy)]
        if not r.path_clear(fpts, pcbnew.F_Cu, 0.18, "SIM_CLK"):
            print(f"  F {why(r, fpts, pcbnew.F_Cu, 0.18, 'SIM_CLK')}")
            continue
        r.add_via(vx, vy, r.code_of("SIM_CLK"), "SIM_CLK", pwr=False)
        r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("SIM_CLK"), "SIM_CLK")
        print(f"  OK via ({vx:.2f},{vy:.2f})")
        return


def route_nreset_c39(r):
    print("== nRESET via beside C39 ==", flush=True)
    sites = [
        (45.68, 15.40),
        (46.20, 16.00),
        (46.40, 16.30),
        (45.68, 16.80),
        (44.90, 15.40),
        (46.80, 15.40),
    ]
    for vx, vy in sites:
        w = r.via_why(vx, vy, "nRESET", pwr=False)
        print(f"  via_why ({vx:.2f},{vy:.2f}) {w}")
        if w is not None:
            continue
        fpts = [(45.68, 16.00), (vx, vy)]
        bpts = [(vx, vy), (45.68, 16.30)]
        if not r.path_clear(fpts, pcbnew.F_Cu, 0.18, "nRESET"):
            print(f"  F {why(r, fpts, pcbnew.F_Cu, 0.18, 'nRESET')}")
            continue
        if not r.path_clear(bpts, pcbnew.B_Cu, 0.18, "nRESET"):
            print(f"  B {why(r, bpts, pcbnew.B_Cu, 0.18, 'nRESET')}")
            # still add via + F if B already touches via location
            r.add_via(vx, vy, r.code_of("nRESET"), "nRESET", pwr=False)
            r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("nRESET"), "nRESET")
            print(f"  OK via+F only ({vx:.2f},{vy:.2f})")
            return
        r.add_via(vx, vy, r.code_of("nRESET"), "nRESET", pwr=False)
        r.commit(fpts, pcbnew.F_Cu, 0.18, r.code_of("nRESET"), "nRESET")
        r.commit(bpts, pcbnew.B_Cu, 0.18, r.code_of("nRESET"), "nRESET")
        print(f"  OK via ({vx:.2f},{vy:.2f})")
        return


def route_vdd2_fb3(r):
    print("== VDD2 FB3 B.Cu in the 15.20–16.87 alley ==", flush=True)
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.25,
        [
            (
                [
                    (68.14, 16.87),
                    (68.14, 16.04),
                    (61.30, 16.04),
                    (61.30, 42.00),
                ],
                "y16.04 between P0.01 and VDD2_MID",
            ),
            (
                [
                    (68.14, 16.87),
                    (68.14, 16.04),
                    (52.22, 16.04),
                    (52.22, 32.00),
                ],
                "y16.04 to C8 via",
            ),
            (
                [
                    (68.14, 16.87),
                    (70.40, 16.87),
                    (70.40, 16.04),
                    (61.30, 16.04),
                    (61.30, 37.13),
                    (59.70, 37.13),
                ],
                "east then y16.04 to C9 via",
            ),
        ],
    ):
        return
    try_wp(r, "VDD2", pcbnew.B_Cu, 0.25, 68.14, 16.87, 59.70, 37.13, "B FB3-C9", max_l=35)


def route_vin_filt(r):
    print("== VIN_FILT east of VDD_GPIO x=70 then back north of P0.15 ==", flush=True)
    if try_any(
        r,
        "VIN_FILT",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (55.35, 13.30),
                    (71.80, 13.30),
                    (71.80, 19.80),
                    (51.90, 19.80),
                    (51.90, 21.90),
                ],
                "east of VDD_GPIO then y19.8 to island",
            ),
            (
                [
                    (55.35, 13.30),
                    (72.50, 13.30),
                    (72.50, 18.40),
                    (51.90, 18.40),
                    (51.90, 21.90),
                ],
                "y18.4 back to island",
            ),
            (
                [
                    (55.35, 13.30),
                    (55.35, 19.80),
                    (51.90, 19.80),
                    (51.90, 21.90),
                ],
                "local south then island",
            ),
        ],
    ):
        return
    try_wp(r, "VIN_FILT", pcbnew.B_Cu, 0.18, 55.35, 13.30, 51.90, 21.90, "B", max_l=28)


def route_p006(r):
    print("== P0.06 y=59.15 east of SIM_RST vias / x=63.2 ==", flush=True)
    j12 = [
        (
            [
                (48.62, 43.80),
                (48.62, 59.15),
                (64.80, 59.15),
                (64.80, 58.40),
                (105.40, 58.40),
                (105.40, 65.20),
                (105.40, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y59.15 then x105.4 stub",
        ),
        (
            [
                (48.62, 43.80),
                (48.62, 59.15),
                (102.80, 59.15),
                (102.80, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "y59.15 x102.8 stub",
        ),
        (
            [
                (48.62, 43.80),
                (63.20, 43.80),
                (63.20, 58.40),
                (63.20, 65.20),
                (63.20, 78.70),
                (21.24, 78.70),
                (21.24, 76.00),
            ],
            "x63.2 between J18 and COEX0",
        ),
    ]
    if not try_any(r, "P0.06", pcbnew.B_Cu, 0.18, j12):
        print("  J12.7 not closed")


def main():
    start = snap_path("pass14c-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(f"START unconn={n0} shorts={counts0.get('shorting_items',0)} {dict(class_counts(pairs))}", flush=True)
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    steps = [
        ("SIM_CLK_via", route_sim_clk_via, "via stitch C35 F to B.Cu"),
        ("nRESET_C39", route_nreset_c39, "via beside C39 pad"),
        ("VDD2_FB3", route_vdd2_fb3, "y16.04 alley"),
        ("VIN_FILT", route_vin_filt, "east of VDD_GPIO"),
        ("P0.06", route_p006, "y59.15 / x63.2"),
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
    print(f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} classes={dict(class_counts(pairs))}")
    for name, status, note in log:
        print(f"  {name}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
