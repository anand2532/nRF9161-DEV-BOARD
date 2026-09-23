#!/usr/bin/env python3
"""Extra U1 fanout + private B.Cu columns on the LIVE board.

May locally rip blocking B.Cu of P0.01 / P0.15 / COEX0 / COEX2 and immediately
re-route that same net. Never wipes all B.Cu. Never calls complete_route.main()
or rebuild_bcu.py.
"""
from __future__ import annotations

import math
import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot, mm, vec  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    FANOUT_NEED,
    SNAP_DIR,
    Final,
    fill_zones,
    run_drc,
)
from final_pass7 import commit_or_why, why  # noqa: E402

ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}
RIP_NETS = ("COEX2", "COEX0", "P0.01", "P0.15")


def snap_path(label):
    return os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")


def check(board, r, label, last_good, unconn_ceiling=None):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} ok={r.ok}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or (unconn_ceiling is not None and n > unconn_ceiling):
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{unconn_ceiling}"
        print(f"ABORT {reason}; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    shutil.copy2(BOARD, snap_path(label))
    return pairs, n, counts


def rip_bcu(r: Final, name, min_len=5.0, extra_pred=None):
    """Remove long B.Cu tracks of one net. Returns (count, specs)."""
    kill = []
    specs = []
    for tr in list(r.board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetLayer() != pcbnew.B_Cu or tr.GetNetname() != name:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
        L = hypot(x1, y1, x2, y2)
        pred = L >= min_len
        if extra_pred:
            pred = extra_pred(x1, y1, x2, y2, L)
        if pred:
            kill.append(tr)
            specs.append((name, x1, y1, x2, y2, L))
    for tr in kill:
        r.board.Remove(tr)
    if kill:
        r.collect()
    print(f"  ripped {name} B.Cu x{len(kill)}")
    for sp in specs:
        print(f"    ({sp[1]:.2f},{sp[2]:.2f})-({sp[3]:.2f},{sp[4]:.2f}) L={sp[5]:.1f}")
    return specs


def private_to_header(r: Final, name):
    hdr = r.primary_header(name)
    p = r.u1(name)
    via = None
    if p:
        via = r.nearest_via(name, p["x"], p["y"], 10.0)
    if via is None:
        vias = [v for v in r.vias if v["n"] == name]
        if vias and hdr:
            via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
        elif vias:
            via = vias[0]
    w = 0.40 if name.startswith("VDD") else 0.18
    if hdr and via:
        if r.route_b_corridor(via["x"], via["y"], hdr["x"], hdr["y"], name, w):
            print(f"  reroute {name} via({via['x']:.2f},{via['y']:.2f})->{hdr['ref']}.{hdr['num']}")
            return True
        # explicit private columns
        stub = 78.15
        cols_e = [64.80, 65.40, 66.20, 67.10, 70.90, 75.50]
        cols_w = [25.10, 25.55, 25.90]
        east = 107.50
        paths = []
        if hdr["y"] > 70 and hdr["x"] < 56:
            for col in cols_w:
                paths.append(
                    [
                        (via["x"], via["y"]),
                        (col, via["y"]),
                        (col, 66.20),
                        (col, stub),
                        (hdr["x"], stub),
                        (hdr["x"], hdr["y"]),
                    ]
                )
        for col in cols_e:
            paths.append(
                [
                    (via["x"], via["y"]),
                    (col, via["y"]),
                    (col, 57.20),
                    (east, 57.20),
                    (east, stub),
                    (hdr["x"], stub),
                    (hdr["x"], hdr["y"]),
                ]
            )
            paths.append(
                [
                    (via["x"], via["y"]),
                    (col, via["y"]),
                    (col, stub),
                    (hdr["x"], stub),
                    (hdr["x"], hdr["y"]),
                ]
            )
        paths.append(
            [
                (via["x"], via["y"]),
                (via["x"], 12.50),
                (east, 12.50),
                (east, stub),
                (hdr["x"], stub),
                (hdr["x"], hdr["y"]),
            ]
        )
        if name in {"P0.13", "P0.14", "P0.15", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "VDD_GPIO"}:
            j18 = r.pad("J18", net=name)
            if j18:
                paths.append([(via["x"], via["y"]), (via["x"], 58.40), (j18["x"], 58.40), (j18["x"], j18["y"])])
                paths.append(
                    [
                        (j18["x"], j18["y"]),
                        (j18["x"], stub),
                        (hdr["x"], stub),
                        (hdr["x"], hdr["y"]),
                    ]
                )
        for pts in paths:
            if r.commit(pts, pcbnew.B_Cu, w, r.code_of(name), name):
                print(f"  explicit {name} -> {hdr['ref']}.{hdr['num']}")
                return True
        print(f"  REROUTE FAIL {name}")
        return False
    print(f"  missing via/hdr {name} via={via} hdr={hdr}")
    return False


def phase_fanout(r: Final):
    print("== extra U1 fanout (outside ring) ==", flush=True)
    log = []
    added = []
    for name in FANOUT_NEED:
        got = r.extra_fanout_one(name, log)
        if got and got[3] != "existing":
            added.append((name, got[0], got[1], got[2], got[3]))
    return log, added


def phase_rip_reroute(r: Final, last_good, start_n):
    """Rip blocking B.Cu highways one net at a time; immediately re-route that net."""
    ripped = []
    board = r.board
    skipped = []

    def p015(x1, y1, x2, y2, L):
        # rip board-width H/V; keep J18 verticals near x=43
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        if abs(x1 - 43.08) < 0.3 and abs(x2 - 43.08) < 0.3 and min(y1, y2) < 65:
            return False
        if L >= 8:
            return True
        if abs(y1 - y2) < 0.2 and abs(my - 20.60) < 0.3:
            return True
        if abs(x1 - x2) < 0.2 and abs(mx - 106.00) < 0.3:
            return True
        if abs(y1 - y2) < 0.2 and abs(my - 77.45) < 0.3 and mx > 50:
            return True
        return False

    def coex2(x1, y1, x2, y2, L):
        my = (y1 + y2) / 2
        mx = (x1 + x2) / 2
        if abs(y1 - y2) < 0.25 and abs(my - 24.60) < 0.3 and L > 8:
            return True
        if abs(x1 - x2) < 0.25 and abs(mx - 105.10) < 0.3 and L > 8:
            return True
        if abs(x1 - x2) < 0.25 and abs(mx - 37.75) < 0.3 and L > 8:
            return True
        return L >= 16

    def coex0(x1, y1, x2, y2, L):
        my = (y1 + y2) / 2
        mx = (x1 + x2) / 2
        if L >= 10:
            return True
        if abs(y1 - y2) < 0.25 and abs(my - 44.40) < 0.3:
            return True
        if abs(x1 - x2) < 0.25 and abs(mx - 64.60) < 0.3:
            return True
        if abs(x1 - x2) < 0.25 and abs(mx - 38.80) < 0.3:
            return True
        return False

    def p001(x1, y1, x2, y2, L):
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        if abs(x1 - x2) < 0.25 and abs(mx - 27.65) < 0.3 and L > 8:
            return True
        if abs(y1 - y2) < 0.25 and abs(my - 15.20) < 0.3 and L > 8:
            return True
        if abs(y1 - y2) < 0.25 and abs(my - 77.45) < 0.3 and mx < 30:
            return True
        return L >= 20

    preds = {"P0.15": p015, "COEX2": coex2, "COEX0": coex0, "P0.01": p001}
    for name in RIP_NETS:
        pre = snap_path(f"pre-rip-{name.replace('.', '')}")
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        shutil.copy2(BOARD, pre)
        specs = rip_bcu(r, name, extra_pred=preds[name])
        if not specs:
            print(f"  no long B.Cu to rip on {name}")
            continue
        ripped.extend(specs)
        ok = private_to_header(r, name)
        if name == "P0.15":
            j18 = r.pad("J18", net=name)
            j12 = r.pad("J12", net=name)
            if j18 and j12:
                stub = 78.15
                r.commit(
                    [(j18["x"], j18["y"]), (j18["x"], stub), (j12["x"], stub), (j12["x"], j12["y"])],
                    pcbnew.B_Cu,
                    0.18,
                    r.code_of(name),
                    name,
                )
        if not ok:
            print(f"  WARN {name} private column failed after rip; continuing to DRC")
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        pairs, n, counts, _ = run_drc()
        print(
            f"  after-rip {name}: unconn={n} shorts={counts.get('shorting_items',0)} "
            f"clr={counts.get('clearance',0)}",
            flush=True,
        )
        if counts.get("shorting_items") or counts.get("clearance") or counts.get("hole_clearance") or n > start_n:
            print(f"  SKIP {name} rip (unconn/shorts); restoring {pre}")
            shutil.copy2(pre, BOARD)
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
            skipped.append(name)
            continue
        last_good = snap_path(f"rip-{name.replace('.', '')}")
        shutil.copy2(BOARD, last_good)
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        start_n = n
        # Retry fanout for nets that still lack an outside via.
        flog = []
        for fn in FANOUT_NEED:
            if r.u1(fn) and not r.nearest_via(fn, r.u1(fn)["x"], r.u1(fn)["y"], 8.0):
                r.extra_fanout_one(fn, flog)
        fill_zones(board)
        pcbnew.SaveBoard(BOARD, board)
        pairs2, n2, counts2, _ = run_drc()
        if counts2.get("shorting_items") or n2 > start_n:
            print(f"  fanout retry after {name} raised unconn; restoring {last_good}")
            shutil.copy2(last_good, BOARD)
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
        else:
            start_n = n2
            last_good = snap_path(f"rip-{name.replace('.', '')}-f")
            shutil.copy2(BOARD, last_good)
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
    if skipped:
        print("  skipped rips:", skipped)
    return r, ripped, start_n, last_good


def phase_gpio(r: Final):
    print("== private GPIO columns ==", flush=True)
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or p["name"] == "VDD_GPIO"
        }
    )
    ok = fail = 0
    for name in nets:
        if private_to_header(r, name):
            ok += 1
        else:
            fail += 1
        hdr = r.primary_header(name)
        if not hdr:
            continue
        stub = 78.15
        w = 0.40 if name == "VDD_GPIO" else 0.18
        for extra in r.extras(name, hdr):
            pts = [
                (hdr["x"], hdr["y"]),
                (hdr["x"], stub),
                (extra["x"], stub),
                (extra["x"], extra["y"]),
            ]
            if extra["x"] > 100:
                pts = [
                    (hdr["x"], hdr["y"]),
                    (hdr["x"], stub),
                    (107.50, stub),
                    (107.50, extra["y"]),
                    (extra["x"], extra["y"]),
                ]
            if r.commit(pts, pcbnew.B_Cu, w, r.code_of(name), name):
                print(f"  extra {name} {extra['ref']}.{extra['num']}")
    print(f"  gpio primary ok={ok} fail={fail}")


def phase_power(r: Final):
    print("== remaining F-class power ==", flush=True)
    # VDD2 C8: y=29.0 south of TP11 (60,30) and VDD1 x=60 y=30-33, east of C8.2
    commit_or_why(
        r,
        [(53.52, 32.00), (53.52, 28.95), (61.20, 28.95), (61.20, 34.20), (59.05, 34.20), (59.05, 36.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 C8 y=28.95 east of C8 GND, south of TP11",
    )
    # TP12: ENABLE vertical at x=52 y=40.95-44. Go east first to x=63 then south.
    commit_or_why(
        r,
        [(60.00, 42.00), (63.40, 42.00), (63.40, 37.30), (59.05, 37.30)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 TP12 east of ENABLE V",
    )
    via_c8 = r.nearest_via("VDD2", 52.22, 32.00, 3)
    if via_c8:
        commit_or_why(
            r,
            [(53.52, 32.00), (52.22, 32.00)],
            pcbnew.F_Cu,
            0.25,
            "VDD2",
            "VDD2 C8 to via 52.22,32",
        )
    commit_or_why(
        r,
        [(58.7875, 18.00), (58.7875, 17.40), (44.80, 17.40), (44.80, 7.80), (68.80, 7.80), (68.80, 18.00), (67.2125, 18.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2_MID",
        "VDD2_MID around VIN/FB1",
    )
    # DEC0: C13.2 GND at 49.68,29.60 — go west of C13
    c13 = r.pad("C13", "1")
    vdec = r.nearest_via("DEC0", 48.65, 21.13, 4)
    if c13 and vdec:
        commit_or_why(
            r,
            [(c13["x"], c13["y"]), (47.90, c13["y"]), (47.90, 23.40), (vdec["x"], 23.40), (vdec["x"], vdec["y"])],
            pcbnew.F_Cu,
            0.18,
            "DEC0",
            "DEC0 west of C13 GND",
        )
    vf = r.nearest_via("VIN_FILT", 55.35, 13.30, 4)
    if vf:
        commit_or_why(
            r,
            [(51.90, 21.90), (54.20, 21.90), (54.20, 16.80), (vf["x"], 16.80), (vf["x"], vf["y"])],
            pcbnew.F_Cu,
            0.25,
            "VIN_FILT",
            "VIN_FILT jog around VIN y=15.4",
        )
    vinf = r.nearest_via("VIN_F", 49.30, 12.60, 5)
    if vinf:
        commit_or_why(
            r,
            [(71.575, 19.06), (71.575, 18.40), (vinf["x"], 18.40), (vinf["x"], vinf["y"])],
            pcbnew.F_Cu,
            0.25,
            "VIN_F",
            "VIN_F to via 49.30,12.60",
        )


def phase_dnp_gnd(board, r: Final):
    print("== DNP + GND ==", flush=True)
    # Only stub if same-net copper is within 3 mm without crossing RF trunks.
    for net, ref in (("ANT_FIT", "C22"), ("AUX", "C23"), ("AUX_FIT", "C24"), ("ANT", "C21"), ("GPS", "C31")):
        p = r.pad(ref, "1")
        if not p:
            continue
        others = [q for q in r.by_net.get(net, []) if q is not p and not q["npth"]]
        if not others:
            print(f"  {net} {ref}: no other copper")
            continue
        t = min(others, key=lambda q: hypot(p["x"], p["y"], q["x"], q["y"]))
        d = hypot(p["x"], p["y"], t["x"], t["y"])
        if d > 3.5:
            print(f"  {net} {ref}: nearest {t.get('ref','cu')} d={d:.2f} > 3.5 mm; leave (would cross 50ohm)")
            continue
        pts = [(p["x"], p["y"]), (t["x"], p["y"]), (t["x"], t["y"])]
        if r.commit(pts, pcbnew.F_Cu, 0.20, r.code_of(net), net):
            print(f"  {net} stub {ref}->{t.get('ref','?')} d={d:.2f}")
        else:
            print(f"  {net} stub blocked: {why(r, pts, pcbnew.F_Cu, 0.20, net)}")
    fill_zones(board)
    for cand in ((14.0, 10.0), (100.0, 10.0), (14.0, 70.0), (100.0, 70.0), (82.0, 36.0)):
        if r.via_why(cand[0], cand[1], "GND", pwr=True) is None:
            r.add_via(cand[0], cand[1], r.code_of("GND"), "GND", pwr=True)
            print("  GND via", cand)


def main():
    start_snap = snap_path("pass12-start")
    shutil.copy2(BOARD, start_snap)
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    pairs, n0, counts0, _ = run_drc()
    print(f"START unconn={n0} shorts={counts0.get('shorting_items',0)} clr={counts0.get('clearance',0)}")
    last = start_snap

    log, added = phase_fanout(r)
    board = r.board
    for item in added:
        name = item[0]
        private_to_header(r, name)
    for cand in ((14.0, 10.0), (100.0, 10.0), (14.0, 70.0), (100.0, 70.0), (82.0, 36.0), (50.0, 50.0), (90.0, 50.0)):
        if r.via_why(cand[0], cand[1], "GND", pwr=True) is None:
            r.add_via(cand[0], cand[1], r.code_of("GND"), "GND", pwr=True)
    got = check(board, r, "pass12f", last, unconn_ceiling=n0 + 2)
    if got[0] is None:
        return 3, log, added, []
    pairs, n, counts = got
    last = snap_path("pass12f")
    n0 = n

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    rr = phase_rip_reroute(r, last, n0)
    if rr[0] is None:
        return 3, log, added, rr[1]
    r, ripped, n0, last = rr

    board = r.board
    phase_gpio(r)
    got = check(board, r, "pass12g", last, unconn_ceiling=n0)
    if got[0] is None:
        return 3, log, added, ripped
    last = snap_path("pass12g")
    n0 = got[1]

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_power(r)
    got = check(board, r, "pass12p", last, unconn_ceiling=n0)
    if got[0] is None:
        return 3, log, added, ripped
    last = snap_path("pass12p")
    n0 = got[1]

    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    phase_dnp_gnd(board, r)
    got = check(board, r, "pass12d", last, unconn_ceiling=n0)
    if got[0] is None:
        return 3, log, added, ripped
    print("DONE unconn", got[1])
    # write fanout log
    with open(os.path.join(os.path.dirname(BOARD), "reports", "FANOUT_PASS12.txt"), "w") as f:
        f.write("name\tvia_xy_r\tstatus\n")
        for name, xy, st in log:
            f.write(f"{name}\t{xy}\t{st}\n")
    return 0, log, added, ripped


if __name__ == "__main__":
    code, log, added, ripped = main()
    print("ADDED", added)
    print("RIPPED", len(ripped) if ripped else 0)
    raise SystemExit(code)
