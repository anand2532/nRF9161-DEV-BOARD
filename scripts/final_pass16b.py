#!/usr/bin/env python3
"""Pass 16b: P0.15 J18 wrap (outside F corridor), then delete corridor replacement."""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, fill_zones, run_drc  # noqa: E402
from final_pass14 import (  # noqa: E402
    class_counts,
    reload,
    snap_path,
    try_any,
    try_commit,
    write_gpio_csv,
    write_unconnected_csv,
)
from final_pass16 import (  # noqa: E402
    apply_net,
    leftover_f,
    route_dec0,
    route_enable,
    route_nreset_j8_r5,
    route_p008,
    route_sim_clk_c,
    route_sim_clk_u1,
    route_sim_io_c,
    route_vdd2_fb3,
    route_vin_f,
    route_vin_filt,
    write_release,
    check,
)

REP = "/workspace/kicad-projects/nRF9161-DEV-BOARD/reports"

# Never enters x=48–72, y=18–26. Ties west via to existing J18.3.
J18_WRAP = [
    (41.75, 23.10),
    (41.75, 22.50),
    (36.50, 22.50),
    (36.50, 27.20),
    (34.50, 27.20),
    (34.50, 30.80),
    (32.20, 30.80),
    (32.20, 40.50),
    (31.00, 40.50),
    (31.00, 43.50),
    (32.20, 43.50),
    (32.20, 59.20),
    (43.08, 59.20),
    (43.08, 62.00),
]


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return (
        pcbnew.ToMM(s.x),
        pcbnew.ToMM(s.y),
        pcbnew.ToMM(e.x),
        pcbnew.ToMM(e.y),
    )


def in_corridor(x1, y1, x2, y2, x0=47.5, x1b=72.5, y0=18.0, y1b=26.0):
    """True if the segment overlaps the F-class box."""
    xa, xb = min(x1, x2), max(x1, x2)
    ya, yb = min(y1, y2), max(y1, y2)
    if xb < x0 or xa > x1b or yb < y0 or ya > y1b:
        return False
    # skip the original via stub at x=41.75 (west of box)
    return True


def delete_corridor_p015(board):
    """Remove P0.15 B.Cu that still occupies x=47.5–72.5, y=18–26 (the VIN_FILT jog replacement)."""
    ripped = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if not in_corridor(x1, y1, x2, y2):
            continue
        print(f"  rip repl ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        ripped.append((x1, y1, x2, y2))
        board.Remove(tr)
    # West remnant y=20.60 x=41.75–47.50 still nicks nRESET; drop it (J18 wrap holds the via).
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if abs(y1 - 20.60) < 0.2 and abs(y2 - 20.60) < 0.2:
            xa, xb = min(x1, x2), max(x1, x2)
            if xb <= 48.0 and xa >= 41.0:
                print(f"  rip west remnant ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
                ripped.append((x1, y1, x2, y2))
                board.Remove(tr)
    return ripped


def extra_nreset(r):
    print("== nRESET extra jogs in opened y=20.60 gap ==", flush=True)
    B = pcbnew.B_Cu
    if try_any(
        r,
        "nRESET",
        B,
        0.18,
        [
            (
                [
                    (45.68, 19.80),
                    (45.68, 20.25),
                    (69.50, 20.25),
                    (69.50, 18.40),
                    (73.50, 18.40),
                    (73.50, 20.25),
                    (97.50, 20.25),
                    (97.50, 27.13),
                    (102.33, 27.13),
                ],
                "B y20.25 after remnant gone",
            ),
            (
                [
                    (45.68, 19.80),
                    (72.20, 19.80),
                    (72.20, 27.13),
                    (102.33, 27.13),
                ],
                "B y19.80 to east remnant",
            ),
            (
                [
                    (45.68, 16.87),
                    (45.68, 20.40),
                    (102.33, 20.40),
                    (102.33, 27.13),
                ],
                "B y20.40 from C39 V",
            ),
        ],
    ):
        return
    try_any(
        r,
        "nRESET",
        pcbnew.F_Cu,
        0.18,
        [
            (
                [
                    (53.65, 10.80),
                    (53.65, 20.40),
                    (102.33, 20.40),
                    (102.33, 27.13),
                ],
                "F y20.4 (P0.15 B gone)",
            ),
        ],
    )


def extra_vdd2(r):
    print("== VDD2 extra through true y=20.60 gap ==", flush=True)
    if try_any(
        r,
        "VDD2",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (68.79, 19.13),
                    (68.79, 20.40),
                    (59.70, 20.40),
                    (59.70, 32.00),
                ],
                "B y20.40 to C9 via",
            ),
            (
                [
                    (68.14, 16.87),
                    (68.14, 20.40),
                    (52.22, 20.40),
                    (52.22, 32.00),
                ],
                "B y20.40 to C8 via",
            ),
            (
                [
                    (68.79, 19.13),
                    (68.79, 20.40),
                    (36.50, 20.40),
                    (36.50, 27.20),
                    (52.22, 27.20),
                    (52.22, 32.00),
                ],
                "B west of COEX2 after gap",
            ),
        ],
    ):
        return


def extra_dec0(r):
    print("== DEC0 extra ==", flush=True)
    try_any(
        r,
        "DEC0",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (47.80, 31.20),
                    (47.80, 20.40),
                    (48.65, 20.40),
                    (48.65, 21.13),
                ],
                "B x47.8 y20.40",
            ),
            (
                [
                    (47.80, 31.20),
                    (51.20, 31.20),
                    (51.20, 20.40),
                    (48.65, 20.40),
                    (48.65, 21.13),
                ],
                "B x51.2 y20.40",
            ),
        ],
    )


def extra_enable(r):
    print("== ENABLE extra ==", flush=True)
    try_any(
        r,
        "ENABLE",
        pcbnew.B_Cu,
        0.18,
        [
            (
                [
                    (48.33, 23.13),
                    (48.33, 20.40),
                    (42.75, 20.40),
                    (42.75, 41.10),
                ],
                "B y20.40 to U1 via",
            ),
        ],
    )


def main():
    start = snap_path("pass16b-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(f"START unconn={n0} shorts={counts0.get('shorting_items',0)} {dict(class_counts(pairs))}", flush=True)
    if counts0.get("shorting_items") or n0 > 90:
        print("abort: shorts or unconn>90")
        return 2
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    p015_note = "J18 wrap not added"
    sim_note = "not ripped this subpass"

    print("\n#### P0.15_J18_WRAP", flush=True)
    r.ok = r.fail = 0
    ok = try_commit(r, J18_WRAP, pcbnew.B_Cu, 0.18, "P0.15", "J18 wrap west of corridor")
    got = check(board, r, "pass16b-j18wrap", last, ceiling, force_fill=True)
    if got[0] is None or not ok:
        log.append(("P0.15_J18", "not added", "wrap DRC-failed"))
        board, r = reload()
    else:
        ceiling = got[1]
        last = snap_path("pass16b-j18wrap")
        board, r = reload()
        p015_note = "J18 wrap added (41.75,23.10) west of COEX2 to J18.3 (43.08,62) at y=59.20"
        log.append(("P0.15_J18", f"added (unconn={ceiling})", p015_note))

        print("\n#### P0.15_DEL_CORRIDOR_REPL", flush=True)
        pre = snap_path("pass16b-pre-del-repl")
        shutil.copy2(BOARD, pre)
        ripped = delete_corridor_p015(board)
        r.collect()
        got = check(board, r, "pass16b-del-repl", pre, ceiling, force_fill=True)
        if got[0] is None:
            p015_note += "; corridor replacement rip REVERTED"
            log.append(("P0.15_DEL_REPL", "reverted", p015_note))
            board, r = reload()
        else:
            ceiling = got[1]
            last = snap_path("pass16b-del-repl")
            board, r = reload()
            txt = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in ripped)
            p015_note += f"; removed corridor replacement/west remnant: {txt}"
            log.append(("P0.15_DEL_REPL", f"ripped (unconn={ceiling})", txt))

    steps = [
        ("DEC0", extra_dec0, "retry through open y=20.60"),
        ("ENABLE_C14U1", extra_enable, "retry"),
        ("VDD2_FB3", extra_vdd2, "retry"),
        ("nRESET_J8R5", extra_nreset, "retry"),
        ("VIN_FILT", route_vin_filt, "short hops"),
        ("VIN_F", route_vin_f, "short hops"),
        ("SIM_CLK_U1", route_sim_clk_u1, "east of RF"),
        ("SIM_CLK_C", route_sim_clk_c, "names distinct"),
        ("SIM_IO_C", route_sim_io_c, "names distinct"),
        ("P0.08", route_p008, "east of VDD2"),
    ]
    for name, fn, note in steps:
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok, ceiling = apply_net(board, r, name, fn, last, ceiling)
        if not ok:
            status = "not closed (DRC revert)"
        elif ceiling < before:
            status = f"closed ({before}→{ceiling})"
        else:
            status = "not closed (no DRC-clean copper)"
        log.append((name, status, note))
        print(f"  kept={ok} ceiling={ceiling} {status}", flush=True)

    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shutil.copy2(BOARD, snap_path("pass16"))
    shutil.copy2("/tmp/nrf_final_drc.json", f"{REP}/DRC_AFTER_CONNECT.json")
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(
        n0, n1, counts.get("shorting_items", 0), counts, pairs, log, board, p015_note, sim_note
    )
    print(f"DONE start={n0} end={n1} shorts={counts.get('shorting_items',0)} {dict(class_counts(pairs))}")
    print("P0.15:", p015_note)
    for name, status, note in log:
        print(f"  {name}: {status}")
    for line in leftover_f(pairs):
        print(f"  leftover {line}")
    print(f"FAB={'yes' if n1==0 else 'no'}")
    return 0 if counts.get("shorting_items", 0) == 0 and n1 <= n0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
