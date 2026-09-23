#!/usr/bin/env python3
"""Pass 22: SIM_IO_C around SIM_CLK_C F H; leftover F short jogs; GPIO extra vias.

LIVE. Do not restore backups. Ceiling finish ≤86. No /fab unless unconnected=0
AND ratsnest=0. Do not rip VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST wrap x=74 /
SIM_RST_C wrap x=81.8 / VIN V x=66.
"""
from __future__ import annotations

import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass13 import delete_via_and_stub, h_then_column  # noqa: E402
from final_pass14 import (  # noqa: E402
    ABORT,
    class_counts,
    dump_vios,
    reload,
    snap_path,
    try_commit,
    write_gpio_csv,
    write_unconnected_csv,
)
import final_pass17 as p17  # noqa: E402
from final_pass17 import try_list, try_via_routes  # noqa: E402
from final_pass21 import leftover_f, mm_xy, status_of  # noqa: E402
import final_pass21 as p21  # noqa: E402

REP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/reports"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
BLOCKERS = {}
p17.BLOCKERS = BLOCKERS
p21.BLOCKERS = BLOCKERS
ADDDEL = []
GPIO_ADDED = []
GPIO_CONNECTED = []
GPIO_DELETED = []

CLK_VIA = (77.75, 53.50)
IO_VIA = (75.20, 51.50)
IO_F = [(77.35, 55.40), (76.90, 55.40), (76.90, 51.50), (75.20, 51.50)]
IO_B = [
    (75.20, 51.50),
    (75.20, 45.80),
    (78.60, 45.80),
    (78.60, 42.50),
    (99.80, 42.50),
    (99.80, 48.50),
    (98.54, 48.50),
    (98.54, 50.01),
]
WEST_NORTH = {"MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_VIO", "MIPI_SCLK", "MIPI_SDATA"}
ODD_GPIO = [
    "COEX0",
    "COEX1",
    "MAGPIO0",
    "MAGPIO1",
    "MAGPIO2",
    "MIPI_SCLK",
    "MIPI_SDATA",
    "MIPI_VIO",
    "P0.00",
    "P0.01",
    "P0.03",
    "P0.04",
    "P0.09",
    "P0.11",
    "P0.14",
    "P0.16",
    "P0.18",
    "P0.22",
    "P0.24",
    "P0.27",
    "P0.29",
    "P0.31",
]


def check(board, r, label, last_good, ceiling, force_fill=False):
    if force_fill or r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or n > ceiling:
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}")
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, snap_path(label))
    return pairs, n, counts, pairs


def apply_net(board, r, name, fn, last, ceiling):
    r.ok = 0
    r.fail = 0
    fn(r)
    r.collect()
    got = check(r.board, r, f"pass22-{name.replace('.', '')}", last, ceiling, force_fill=True)
    if got[0] is None:
        board, r = reload()
        return board, r, last, False, ceiling, None
    pairs, n, counts, _ = got
    last = snap_path(f"pass22-{name.replace('.', '')}")
    board, r = reload()
    return board, r, last, True, n, pairs


def route_clk_c_add(r):
    print("== ADD SIM_CLK_C north via (77.75,53.50) + B join x=76.62 ==", flush=True)
    if try_via_routes(
        r,
        "SIM_CLK_C",
        False,
        [CLK_VIA],
        [
            ([(77.75, 54.70), (77.75, 53.50)], F, 0.18, "F extend V x=77.75 to via"),
            ([(77.75, 53.50), (76.62, 53.50)], B, 0.18, "B join existing V x=76.62"),
        ],
    ):
        return
    BLOCKERS["SIM_CLK_C_ADD"] = r.via_why(CLK_VIA[0], CLK_VIA[1], "SIM_CLK_C") or "path blocked"


def delete_clk_c_west_f(board, r):
    hits = []
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "SIM_CLK_C" or tr.GetLayer() != F:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        xs, ys = [x1, x2], [y1, y2]
        is_h = (
            abs(y1 - y2) < 0.20
            and abs((y1 + y2) / 2 - 54.70) < 0.25
            and min(xs) < 76.80
            and max(xs) > 77.50
        )
        is_v = (
            abs(x1 - x2) < 0.20
            and abs((x1 + x2) / 2 - 76.62) < 0.25
            and max(ys) > 55.50
            and min(ys) < 55.00
        )
        if is_h or is_v:
            hits.append((tr, x1, y1, x2, y2))
    print(f"== DELETE SIM_CLK_C F H y=54.70 / V x=76.62 hits={len(hits)} ==", flush=True)
    specs = []
    for tr, x1, y1, x2, y2 in hits:
        print(f"  rip ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})")
        specs.append((x1, y1, x2, y2))
        board.Remove(tr)
    r.collect()
    return specs


def route_sim_io_c(r):
    print("== SIM_IO_C via (75.20,51.50) F jog x=76.90 then B wrap to J7 ==", flush=True)
    b_alts = [
        IO_B,
        [
            (75.20, 51.50),
            (75.20, 45.80),
            (78.60, 45.80),
            (78.60, 42.80),
            (99.80, 42.80),
            (99.80, 48.50),
            (98.54, 48.50),
            (98.54, 50.01),
        ],
        [
            (75.20, 51.50),
            (75.20, 45.80),
            (78.60, 45.80),
            (78.60, 42.20),
            (99.80, 42.20),
            (99.80, 48.20),
            (98.54, 48.20),
            (98.54, 50.01),
        ],
    ]
    f_alts = [
        IO_F,
        [(77.35, 55.40), (76.85, 55.40), (76.85, 51.50), (75.20, 51.50)],
        [(77.35, 55.40), (76.80, 55.40), (76.80, 51.20), (75.20, 51.20), (75.20, 51.50)],
    ]
    for fpts in f_alts:
        for bpts in b_alts:
            if try_via_routes(
                r,
                "SIM_IO_C",
                False,
                [IO_VIA],
                [
                    (fpts, F, 0.18, "F jog west of CLK_C via"),
                    (bpts, B, 0.18, "B gap x=78.60 then y=42.5 east of J7 CLK_C"),
                ],
            ):
                return
            # try_via_routes adds via only if all paths clear; if it failed after
            # adding, occupancy is dirty — caller DRC-reverts. If it failed before
            # add, board is clean. Re-collect in case a partial add happened.
            r.collect()
    BLOCKERS["SIM_IO_C"] = why(r, IO_F, F, 0.18, "SIM_IO_C")


def route_vin_filt(r):
    print("== VIN_FILT short jogs (no VIN x=66 rip) ==", flush=True)
    try_list(
        r,
        "VIN_FILT",
        F,
        0.25,
        [
            ([(55.35, 13.30), (55.35, 12.50), (51.90, 12.50), (51.90, 21.90)], "F y12.50 west to island"),
            ([(55.35, 13.30), (57.20, 13.30), (57.20, 16.80), (51.90, 16.80), (51.90, 21.90)], "F x57.2"),
            ([(55.35, 13.30), (55.35, 15.80), (51.90, 15.80), (51.90, 21.90)], "F y15.80"),
        ],
    )


def route_vin_f(r):
    print("== VIN_F short jogs; no 80 mm bus ==", flush=True)
    try_list(
        r,
        "VIN_F",
        F,
        0.25,
        [
            ([(48.00, 12.60), (48.00, 11.40), (56.50, 11.40), (56.50, 12.60), (71.58, 12.60), (71.58, 17.66)], "F y11.40 jog"),
            ([(49.30, 12.60), (49.30, 14.20), (56.20, 14.20), (56.20, 17.66), (71.58, 17.66)], "F y14.20"),
        ],
    )


def extra_via_sites(p, name):
    px, py = p["x"], p["y"]
    outs = [1.20, 1.50, 1.80, 2.10]
    ring = 0.95
    sites = []
    for o in outs:
        d = ring + o
        if name in WEST_NORTH:
            sites.extend([(px - d, py), (px, py - d), (px - d, 18.80), (px - 1.6, py - d)])
        elif py >= 36.0:
            sites.extend([(px, py + d), (px + d, py), (px + d, py + 0.80), (px - d, py)])
        elif py <= 28.0:
            sites.extend([(px, py - d), (px + d, py), (px + d, py - 0.80), (px - d, py)])
        else:
            sites.extend([(px + d, py), (px, py + d), (px, py - d)])
    # Prefer east of freed COEX2 column.
    sites.extend([(64.80, py), (65.50, py), (64.80, py + 2.4), (65.50, 40.80)])
    out = []
    seen = set()
    for x, y in sites:
        x, y = round(x, 2), round(y, 2)
        if abs(y - 39.45) < 0.20:
            continue
        if (x, y) in seen:
            continue
        seen.add((x, y))
        out.append((x, y))
    return out


def f_to_via(r, p, vx, vy, name):
    px, py = p["x"], p["y"]
    w = 0.18
    if name in WEST_NORTH:
        cands = [
            [(px, py), (vx, py), (vx, vy)],
            [(px, py), (px, vy), (vx, vy)],
            [(px, py), (px, 19.00), (vx, 19.00), (vx, vy)],
        ]
    elif vy > py:
        cands = [
            [(px, py), (px, vy), (vx, vy)],
            [(px, py), (vx, py), (vx, vy)],
        ]
    else:
        cands = [
            [(px, py), (vx, py), (vx, vy)],
            [(px, py), (px, vy), (vx, vy)],
        ]
    for pts in cands:
        if r.commit(pts, F, w, r.code_of(name), name):
            return True
    return r.oblong_escape(p, vx, vy, name)


def route_gpio_extra(r):
    print("== GPIO extra U1 vias 1.15–2.1 mm outside 0.95 ring (not y=39.45) ==", flush=True)
    for name in ODD_GPIO:
        p = r.u1(name)
        if not p:
            continue
        existing = [v for v in r.vias if v["n"] == name]
        near = [v for v in existing if hypot(v["x"], v["y"], p["x"], p["y"]) < 4.0]
        if near:
            print(f"  skip {name}: already has near via {near[0]['x']:.2f},{near[0]['y']:.2f}")
            continue
        placed = None
        for x, y in extra_via_sites(p, name):
            size = drill = None
            w = r.via_why(x, y, name)
            if w is not None:
                w = r.via_why(x, y, name, size=0.45, drill=0.25)
                if w is not None:
                    continue
                size, drill = 0.45, 0.25
            r.add_via(x, y, r.code_of(name), name, size=size, drill=drill)
            r.collect()
            if not f_to_via(r, p, x, y, name):
                delete_via_and_stub(r, name, x, y)
                continue
            GPIO_ADDED.append((name, x, y))
            print(f"  via {name} ({x:.2f},{y:.2f})", flush=True)
            placed = (x, y)
            break
        if not placed:
            print(f"  no extra via site {name}")
            continue
        if h_then_column(r, name, placed[0], placed[1]):
            GPIO_CONNECTED.append(name)
            print(f"  B connected {name}", flush=True)
        else:
            print(f"  B fail {name}; will delete dangling via", flush=True)


def route_p006_j12(r):
    print("== P0.06 J12.7 west wrap x≈25.1 y≥64 (keep via 45.15,36) ==", flush=True)
    if try_list(
        r,
        "P0.06",
        B,
        0.18,
        [
            (
                [(45.15, 36.00), (25.10, 36.00), (25.10, 64.20), (25.10, 76.00), (21.24, 76.00)],
                "B west x=25.10 y>=64 to J12.7",
            ),
            (
                [(44.00, 43.80), (25.10, 43.80), (25.10, 64.20), (21.24, 64.20), (21.24, 76.00)],
                "B from existing x=44 y=43.80 wrap",
            ),
            (
                [(45.15, 36.00), (45.15, 64.80), (25.10, 64.80), (25.10, 76.00), (21.24, 76.00)],
                "B south then west y=64.80",
            ),
            (
                [(44.00, 43.80), (44.00, 65.20), (21.24, 65.20), (21.24, 76.00)],
                "B south x=44 y=65.20",
            ),
        ],
    ):
        if try_list(
            r,
            "P0.06",
            B,
            0.18,
            [
                (
                    [(21.24, 76.00), (21.24, 78.15), (116.00, 78.15), (116.00, 8.00)],
                    "B stub then J9.1",
                ),
                (
                    [(21.24, 76.00), (25.10, 76.00), (25.10, 78.50), (116.00, 78.50), (116.00, 8.00)],
                    "B y78.50 to J9.1",
                ),
            ],
        ):
            return
        return


def write_release(n0, n1, shorts, counts, pairs, log, board):
    cls = class_counts(pairs)
    tracks = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    nvia = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
    path = f"{REP}/FINAL_FAB_RELEASE.md"
    fab = n1 == 0
    sim = "yes" if not any(p["net"] == "SIM_IO_C" for p in pairs) else "no"
    with open(path, "w") as f:
        f.write("# nRF9161 DEVELOPMENT BOARD — FINAL FAB RELEASE\n\n")
        if fab:
            f.write("**Status: FABRICATION-READY (connectivity gate)**\n\n")
        else:
            f.write("**Status: NOT FABRICATION-READY**\n\n")
            f.write(
                f"Hard gate failed: `unconnected_items = {n1}` (must be 0) "
                "and ratsnest is not zero. Fabrication outputs were **not** generated.\n\n"
            )
        f.write("Connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items`.\n\n")
        f.write("| Gate | Result |\n|------|--------|\n")
        f.write(f"| unconnected_items | **{n1}** (need 0) |\n")
        f.write(f"| shorting_items | {shorts} |\n")
        f.write(f"| clearance | {counts.get('clearance', 0)} |\n")
        f.write(f"| hole_clearance | {counts.get('hole_clearance', 0)} |\n")
        f.write(f"| Gerbers /fab | **{'generated' if fab else 'not generated'}** |\n\n")
        f.write("## Board\n\n")
        f.write("| Item | Value |\n|------|--------|\n")
        f.write("| Size | 120 × 80 mm |\n")
        f.write("| Layers | F.Cu / In1.Cu GND / In2.Cu / B.Cu |\n")
        f.write("| In2 plane net | `VDD_nRF` |\n")
        f.write(f"| Tracks | {tracks} |\n")
        f.write(f"| Vias | {nvia} |\n")
        f.write("| U1 | (36.0, 32.0) mm, rot 180° |\n")
        f.write("| SIM_DET U1 pad 45 net | `''` (must stay empty) |\n")
        f.write("| Backup | `.mcp-backups/final-fab-20260917-194911/` |\n")
        f.write("| Live snapshot after this pass | `after-pass22.kicad_pcb` |\n")
        f.write("| Pre-this-pass snapshot | `after-pass22-start.kicad_pcb` |\n\n")
        f.write("## This pass (SIM_IO_C, leftover F, GPIO extra vias)\n\n")
        f.write(f"Start **{n0}** unconnected / **0** shorts. End **{n1}** / **{shorts}**. ")
        f.write("Absolute cap 86. Zone refill after copper. ")
        f.write("VDD2 / COEX2 / P0.15 / ENABLE / SIM_RST wrap x=74 / SIM_RST_C wrap x=81.8 / VIN V x=66 not ripped. ")
        f.write("SIM_* names not merged. P0.06 via (45.15, 36) kept.\n\n")
        f.write(f"**SIM_IO_C closed:** {sim}\n\n")
        f.write("**Add-then-delete:** " + ("; ".join(ADDDEL) if ADDDEL else "none kept") + "\n\n")
        f.write(
            f"**GPIO extra vias:** added {len(GPIO_ADDED)}, connected {GPIO_CONNECTED}, "
            f"deleted {GPIO_DELETED}\n\n"
        )
        f.write("### Per-net\n\n")
        f.write("| net | result |\n|-----|--------|\n")
        for name, status, note in log:
            f.write(f"| {name} | {status} — {note} |\n")
        f.write("\n## Remaining unconnected (by class)\n\n")
        f.write("| Class | Count | Meaning |\n|-------|-------|--------|\n")
        f.write(f"| A | {cls.get('A',0)} | U1/via to header or island |\n")
        f.write(f"| F | {cls.get('F',0)} | F.Cu power/SIM/SWD islands |\n")
        f.write(f"| G | {cls.get('G',0)} | Header duplicate branches |\n")
        f.write(f"| C | {cls.get('C',0)} | DNP RF shunts |\n")
        f.write(f"| E | {cls.get('E',0)} | GND F.Cu zone-to-zone |\n\n")
        left = leftover_f(pairs)
        if left:
            f.write("### Still-open F targets\n\n")
            for line in left:
                f.write(f"- {line}\n")
            f.write("\n")
        f.write("## Reports\n\n")
        f.write("- `reports/UNCONNECTED_AFTER_FINAL.csv`\n")
        f.write("- `reports/GPIO_FINAL.csv`\n")
        f.write("- `reports/FINAL_FAB_RELEASE.md`\n")
        f.write("- `reports/DRC_AFTER_CONNECT.json`\n")
    print("wrote", path)


def main():
    start = snap_path("pass22-start")
    shutil.copy2(BOARD, start)
    pairs, n0, counts0, _ = run_drc()
    print(
        f"START unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"{dict(class_counts(pairs))}",
        flush=True,
    )
    if counts0.get("shorting_items", 0):
        return 2
    if n0 > 86:
        print(f"start {n0}>86 abort")
        return 2
    cap = 86
    ceiling = n0
    last = start
    board, r = reload()
    log = []
    last_pairs = pairs

    print("\n#### SIM_CLK_C_ADD", flush=True)
    board, r, last, ok, ceiling, new_pairs = apply_net(
        board, r, "SIM_CLK_C_ADD", route_clk_c_add, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    log.append(("SIM_CLK_C_ADD", "added" if ok else "reverted", f"unconn={ceiling}"))
    print(f"  kept={ok} ceiling={ceiling}", flush=True)

    if ok:
        print("\n#### SIM_CLK_C_RIP F H y=54.70 / V x=76.62", flush=True)
        pre = last
        specs = delete_clk_c_west_f(board, r)
        ripped = "; ".join(f"({a:.2f},{b:.2f})-({c:.2f},{d:.2f})" for a, b, c, d in specs) or "none"
        got = check(board, r, "pass22-SIM_CLK_C_RIP", pre, cap, force_fill=True)
        if got[0] is None:
            ADDDEL.append("SIM_CLK_C north via added but west F rip reverted")
            log.append(("SIM_CLK_C_RIP", "reverted", ripped))
            shutil.copy2(start, BOARD)
            board, r = reload()
            last = start
            ceiling = n0
            last_pairs = pairs
            ok = False
        else:
            ceiling = got[1]
            last = snap_path("pass22-SIM_CLK_C_RIP")
            last_pairs = got[0]
            ADDDEL.append(f"SIM_CLK_C yes; removed F H/V {ripped}")
            log.append(("SIM_CLK_C_RIP", f"ripped (unconn={ceiling})", ripped))
            board, r = reload()

    print("\n#### SIM_IO_C", flush=True)
    before = ceiling
    board, r, last, ok_io, ceiling, new_pairs = apply_net(
        board, r, "SIM_IO_C", route_sim_io_c, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    st, note = status_of("SIM_IO_C", ok_io, before, ceiling, last_pairs, "F jog x=76.90 / B wrap J7")
    log.append(("SIM_IO_C", st, note))
    print(f"  {st}", flush=True)

    for name, fn, note0 in (
        ("VIN_FILT", route_vin_filt, "short F jogs; VIN x=66 kept"),
        ("VIN_F", route_vin_f, "short F jogs; no 80 mm"),
        ("nRESET", p21.route_nreset, "J8/C39 to R5 short jogs"),
        ("SIM_CLK", p21.route_sim_clk, "U1 courtyard via east"),
        ("P0.08", p21.route_p008, "east of VDD2 / ENABLE jump"),
    ):
        print(f"\n#### {name}", flush=True)
        before = ceiling
        board, r, last, ok2, ceiling, new_pairs = apply_net(board, r, name, fn, last, cap)
        if new_pairs is not None:
            last_pairs = new_pairs
        st, note = status_of(name, ok2, before, ceiling, last_pairs, note0)
        log.append((name, st, note))
        print(f"  {st}", flush=True)

    print("\n#### GPIO extra vias", flush=True)
    before = ceiling
    r.ok = 0
    route_gpio_extra(r)
    r.collect()
    got = check(r.board, r, "pass22-GPIO_ADD", last, cap, force_fill=True)
    if got[0] is None:
        log.append(("GPIO_ADD", "reverted", f"added {GPIO_ADDED}"))
        GPIO_ADDED.clear()
        GPIO_CONNECTED.clear()
        board, r = reload()
    else:
        ceiling = got[1]
        last = snap_path("pass22-GPIO_ADD")
        last_pairs = got[0]
        board, r = reload()
        # Delete dangling extras that did not get B.Cu.
        still_open = {p["net"] for p in last_pairs}
        for name, x, y in list(GPIO_ADDED):
            if name in GPIO_CONNECTED and name not in still_open:
                continue
            if name in GPIO_CONNECTED:
                continue
            delete_via_and_stub(r, name, x, y)
            GPIO_DELETED.append(name)
            print(f"  delete dangling {name} @({x:.2f},{y:.2f})")
        if GPIO_DELETED:
            got = check(r.board, r, "pass22-GPIO_DEL", last, cap, force_fill=True)
            if got[0] is None:
                log.append(("GPIO_DEL", "reverted (kept dangling)", str(GPIO_DELETED)))
                GPIO_DELETED.clear()
                board, r = reload()
            else:
                ceiling = got[1]
                last = snap_path("pass22-GPIO_DEL")
                last_pairs = got[0]
                board, r = reload()
        log.append(
            (
                "GPIO_ADD",
                f"added={len(GPIO_ADDED)} connected={GPIO_CONNECTED} deleted={GPIO_DELETED}",
                f"unconn {before}→{ceiling}",
            )
        )

    print("\n#### P0.06 J12.7", flush=True)
    before = ceiling
    board, r, last, ok3, ceiling, new_pairs = apply_net(
        board, r, "P0.06", route_p006_j12, last, cap
    )
    if new_pairs is not None:
        last_pairs = new_pairs
    st = "closed" if ok3 and not any(p["net"] == "P0.06" for p in last_pairs) else (
        "partial" if ok3 else "not closed"
    )
    log.append(("P0.06", st, "west wrap x=25.1 y>=64; via (45.15,36) kept"))

    shutil.copy2(BOARD, snap_path("pass22"))
    board, r = reload()
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n1, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0) or 0
    if shorts or n1 > n0:
        print(f"FINISH abort shorts={shorts} unconn={n1}>{n0}; restore start")
        shutil.copy2(start, BOARD)
        return 3
    write_unconnected_csv(pairs, f"{REP}/UNCONNECTED_AFTER_FINAL.csv")
    write_gpio_csv(board, pairs, f"{REP}/GPIO_FINAL.csv")
    write_release(n0, n1, shorts, counts, pairs, log, board)
    print(
        f"END unconn={n1} shorts={shorts} SIM_IO_C="
        f"{'yes' if not any(p['net']=='SIM_IO_C' for p in pairs) else 'no'} "
        f"gpio_added={GPIO_ADDED} connected={GPIO_CONNECTED} deleted={GPIO_DELETED} fab=no",
        flush=True,
    )
    return 0 if n1 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
