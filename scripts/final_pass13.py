#!/usr/bin/env python3
"""Pass 13: recover GND +1, B.Cu from the 12 new vias (H then column), delete dangles.

Never adds vias at y=39.45. Never rips P0.01 / P0.15 / COEX2. Never south along
pad-x through y=41.10. Unconnected must finish <= 99.
"""
from __future__ import annotations

import os
import shutil
import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot, mm  # noqa: E402
from final_connect import (  # noqa: E402
    BOARD,
    SNAP_DIR,
    Final,
    fill_zones,
    run_drc,
)
from final_pass7 import commit_or_why, why  # noqa: E402

ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}
NEW_VIAS = [
    ("P0.01", 40.25, 39.45),
    ("P0.04", 42.25, 39.45),
    ("P0.06", 45.15, 36.00),
    ("P0.09", 45.15, 29.50),
    ("P0.11", 45.20, 28.00),
    ("P0.22", 35.25, 25.05),
    ("P0.24", 34.25, 25.05),
    ("P0.27", 34.25, 39.45),
    ("P0.29", 35.75, 39.45),
    ("P0.31", 36.75, 39.45),
    ("MAGPIO0", 26.85, 28.50),
    ("COEX1", 38.25, 39.45),
]
XS = [
    25.55,
    26.20,
    28.40,
    32.67,
    64.80,
    65.50,
    66.30,
    67.20,
    70.90,
    75.50,
    82.00,
    90.00,
    105.40,
    110.80,
    111.60,
    112.40,
]
YS = [
    8.20,
    9.60,
    10.80,
    12.40,
    14.00,
    16.20,
    17.80,
    18.40,
    19.00,
    21.60,
    22.40,
    33.40,
    34.20,
    40.70,
    42.20,
    44.80,
    46.40,
    48.80,
    50.20,
    54.80,
    56.40,
    58.80,
    65.20,
    66.60,
    67.40,
    73.40,
    77.60,
    78.50,
]
STUB = 78.15


def snap_path(label):
    return os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")


def gnd_count(pairs):
    return sum(1 for p in pairs if p["net"] == "GND")


def check(board, label, last_good, unconn_ceiling=None):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} gnd={gnd_count(pairs)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or (unconn_ceiling is not None and n > unconn_ceiling):
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{unconn_ceiling}"
        print(f"ABORT {reason}; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, snap_path(label))
    return pairs, n, counts, pairs


def forbidden_south(vx, vy, pts):
    """True if a segment runs south along pad-x through y=41.10."""
    if vy < 38.5 or vy > 40.2:
        return False
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - vx) < 0.35 and abs(b[0] - vx) < 0.35:
            lo, hi = min(a[1], b[1]), max(a[1], b[1])
            if lo < 41.10 < hi:
                return True
    return False


def try_commit(r, name, pts, w):
    if forbidden_south(pts[0][0], pts[0][1], pts):
        return False
    return r.commit(pts, pcbnew.B_Cu, w, r.code_of(name), name)


def h_then_column(r: Final, name, vx, vy):
    hdr = r.primary_header(name)
    if not hdr:
        print(f"  no header {name}")
        return False
    hx, hy = hdr["x"], hdr["y"]
    wlist = (0.20, 0.18)

    # P0.06: 1.15 mm onto existing B.Cu at x=44.
    if name == "P0.06":
        for w in wlist:
            if try_commit(r, name, [(vx, vy), (44.00, vy)], w):
                print(f"  OK {name} short H to existing B.Cu w={w}")
                return True

    # MAGPIO0: north of RF then east (not west alley through GNSS).
    if name == "MAGPIO0":
        for w in wlist:
            for gx in (26.20, 26.00, 25.70):
                for gy in (18.40, 17.80, 16.40, 15.20, 19.00):
                    for xf in (105.40, 110.80, 111.60, 112.40):
                        pts = [(vx, vy), (gx, vy), (gx, gy), (xf, gy), (xf, hy), (hx, hy)]
                        if try_commit(r, name, pts, w):
                            print(f"  OK {name} north-east w={w} gx={gx} gy={gy} xf={xf}")
                            return True
                        pts = [(vx, vy), (gx, vy), (gx, gy), (xf, gy), (xf, STUB), (hx, STUB), (hx, hy)]
                        if try_commit(r, name, pts, w):
                            print(f"  OK {name} north-east-stub w={w}")
                            return True

    xs = list(XS)
    if name == "MAGPIO0":
        xs = [x for x in xs if x >= 105.0 or x <= 26.3]
    for w in wlist:
        for xl in xs:
            if not r.track_clear(vx, vy, xl, vy, pcbnew.B_Cu, w, name):
                continue
            # H reached private column at via y.
            for yl in YS:
                if name == "MAGPIO0" and not (yl <= 19.2 or yl >= 65.0):
                    continue
                if not r.track_clear(xl, vy, xl, yl, pcbnew.B_Cu, w, name):
                    continue
                cands = [
                    [(vx, vy), (xl, vy), (xl, yl), (hx, yl), (hx, hy)],
                    [(vx, vy), (xl, vy), (xl, yl), (xl, STUB), (hx, STUB), (hx, hy)],
                    [(vx, vy), (xl, vy), (xl, STUB), (hx, STUB), (hx, hy)],
                ]
                if yl <= 19.2:
                    for xf in (105.40, 110.80, 111.60, 112.40):
                        cands.append([(vx, vy), (xl, vy), (xl, yl), (xf, yl), (xf, hy), (hx, hy)])
                        cands.append(
                            [(vx, vy), (xl, vy), (xl, yl), (xf, yl), (xf, STUB), (hx, STUB), (hx, hy)]
                        )
                for pts in cands:
                    if try_commit(r, name, pts, w):
                        print(f"  OK {name} H-col xl={xl} yl={yl} w={w}")
                        return True
        # Native y blocked by sibling vias: jog NORTH on B.Cu (not through y=41.10), then H.
        for yj in (vy - 0.50, vy - 0.90, vy - 1.30, vy - 1.80, vy - 2.40, vy - 3.20):
            if yj < 33.0:
                continue
            if not r.track_clear(vx, vy, vx, yj, pcbnew.B_Cu, w, name):
                continue
            for xl in xs:
                if not r.track_clear(vx, yj, xl, yj, pcbnew.B_Cu, w, name):
                    continue
                for yl in YS:
                    if not r.track_clear(xl, yj, xl, yl, pcbnew.B_Cu, w, name):
                        continue
                    pts = [(vx, vy), (vx, yj), (xl, yj), (xl, yl), (hx, yl), (hx, hy)]
                    if try_commit(r, name, pts, w):
                        print(f"  OK {name} N-jog yj={yj} xl={xl} yl={yl} w={w}")
                        return True
                    pts = [(vx, vy), (vx, yj), (xl, yj), (xl, STUB), (hx, STUB), (hx, hy)]
                    if try_commit(r, name, pts, w):
                        print(f"  OK {name} N-jog-stub yj={yj} xl={xl} w={w}")
                        return True
    print(f"  FAIL {name} no B.Cu path")
    return False


def delete_via_and_stub(r: Final, name, x, y):
    """Remove the 0.50/0.30 via and the F.Cu pad-to-via stub added in pass12."""
    killed_v = killed_t = 0
    pad = r.u1(name)
    for tr in list(r.board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            p = tr.GetPosition()
            if tr.GetNetname() == name and hypot(mm(p.x), mm(p.y), x, y) < 0.20:
                r.board.Remove(tr)
                killed_v += 1
            continue
        if tr.GetLayer() != pcbnew.F_Cu or tr.GetNetname() != name:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
        hits_via = hypot(x1, y1, x, y) < 0.35 or hypot(x2, y2, x, y) < 0.35
        hits_pad = False
        if pad:
            hits_pad = hypot(x1, y1, pad["x"], pad["y"]) < 0.40 or hypot(x2, y2, pad["x"], pad["y"]) < 0.40
        L = hypot(x1, y1, x2, y2)
        # Keep pre-existing long stubs (P0.06/P0.11 2.2 mm east) unless they only exist to the new via.
        if hits_via and hits_pad and L < 3.0:
            r.board.Remove(tr)
            killed_t += 1
        elif hits_via and L < 0.8:
            r.board.Remove(tr)
            killed_t += 1
    r.collect()
    print(f"  DEL {name} via@({x:.2f},{y:.2f}) vias={killed_v} Ftrks={killed_t}")
    return killed_v


def phase_gnd(r: Final):
    print("== GND stitch ==", flush=True)
    cands = [
        (32.0, 42.0),
        (33.5, 40.2),
        (41.0, 40.2),
        (43.6, 38.0),
        (46.8, 29.0),
        (35.0, 24.2),
        (50.0, 50.0),
        (90.0, 50.0),
        (14.0, 10.0),
        (100.0, 10.0),
        (14.0, 70.0),
        (100.0, 70.0),
        (82.0, 36.0),
        (47.5, 32.5),
        (31.5, 26.5),
    ]
    n = 0
    for x, y in cands:
        if r.via_why(x, y, "GND", pwr=True) is None:
            r.add_via(x, y, r.code_of("GND"), "GND", pwr=True)
            print(f"  GND via ({x:.2f},{y:.2f})")
            n += 1
    print(f"  added {n} GND vias")
    return n


def phase_power(r: Final):
    print("== remaining F-class power ==", flush=True)
    commit_or_why(
        r,
        [(53.52, 32.00), (53.52, 28.95), (61.20, 28.95), (61.20, 34.20), (59.05, 34.20), (59.05, 36.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 C8 y=28.95",
    )
    commit_or_why(
        r,
        [(60.00, 42.00), (63.40, 42.00), (63.40, 37.30), (59.05, 37.30)],
        pcbnew.F_Cu,
        0.25,
        "VDD2",
        "VDD2 TP12",
    )
    commit_or_why(
        r,
        [(58.7875, 18.00), (58.7875, 16.80), (44.80, 16.80), (44.80, 7.80), (68.80, 7.80), (68.80, 18.00)],
        pcbnew.F_Cu,
        0.25,
        "VDD2_MID",
        "VDD2_MID",
    )
    c13 = r.pad("C13", "1")
    vdec = r.nearest_via("DEC0", 48.65, 21.13, 4)
    if c13 and vdec:
        commit_or_why(
            r,
            [(c13["x"], c13["y"]), (47.90, c13["y"]), (47.90, 23.40), (vdec["x"], 23.40), (vdec["x"], vdec["y"])],
            pcbnew.F_Cu,
            0.18,
            "DEC0",
            "DEC0",
        )
    vf = r.nearest_via("VIN_FILT", 55.35, 13.30, 4)
    if vf:
        commit_or_why(
            r,
            [(51.90, 21.90), (54.20, 21.90), (54.20, 16.80), (vf["x"], 16.80), (vf["x"], vf["y"])],
            pcbnew.F_Cu,
            0.25,
            "VIN_FILT",
            "VIN_FILT",
        )
    vinf = r.nearest_via("VIN_F", 49.30, 12.60, 5)
    if vinf:
        commit_or_why(
            r,
            [(71.575, 19.06), (71.575, 17.20), (vinf["x"], 17.20), (vinf["x"], vinf["y"])],
            pcbnew.F_Cu,
            0.25,
            "VIN_F",
            "VIN_F",
        )


def main():
    start = snap_path("pass13-start")
    shutil.copy2(BOARD, start)
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    pairs, n0, counts0, _ = run_drc()
    g0 = gnd_count(pairs)
    print(f"START unconn={n0} shorts={counts0.get('shorting_items',0)} gnd={g0}", flush=True)
    last = start
    connected, deleted = [], []

    phase_gnd(r)
    got = check(board, "pass13gnd", last, unconn_ceiling=n0)
    if got[0] is None:
        return 3, connected, deleted, g0, g0
    pairs, n, counts, _ = got
    g1 = gnd_count(pairs)
    print(f"  GND {g0} -> {g1}", flush=True)
    last = snap_path("pass13gnd")
    n0 = n
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("== B.Cu from 12 new vias (H then column) ==", flush=True)
    for name, x, y in NEW_VIAS:
        if h_then_column(r, name, x, y):
            connected.append(name)
            fill_zones(r.board)
            pcbnew.SaveBoard(BOARD, r.board)
            pairs, n, counts, _ = run_drc()
            if counts.get("shorting_items") or counts.get("clearance") or n > n0:
                print(f"  revert {name} (unconn {n} shorts {counts.get('shorting_items')})")
                shutil.copy2(last, BOARD)
                board = pcbnew.LoadBoard(BOARD)
                r = Final(board)
                r.collect()
                connected.pop()
            else:
                n0 = n
                last = snap_path(f"pass13-{name.replace('.', '')}")
                shutil.copy2(BOARD, last)
                board = pcbnew.LoadBoard(BOARD)
                r = Final(board)
                r.collect()

    print("== delete unrouted dangling vias ==", flush=True)
    still = []
    for name, x, y in NEW_VIAS:
        if name in connected:
            still.append((name, x, y))
            continue
        delete_via_and_stub(r, name, x, y)
        deleted.append(name)
    got = check(r.board, "pass13del", last, unconn_ceiling=99)
    if got[0] is None:
        # deletion raised unconn (unlikely); keep vias, but ceiling is 99
        print("  delete check failed; board restored to last good with connected vias")
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        deleted = []
    else:
        pairs, n0, counts, _ = got
        last = snap_path("pass13del")
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    phase_power(r)
    got = check(r.board, "pass13p", last, unconn_ceiling=99)
    if got[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n0, counts, _ = run_drc()
    else:
        pairs, n0, counts, _ = got

    g2 = gnd_count(pairs)
    print(f"DONE unconn={n0} shorts={counts.get('shorting_items',0)} gnd={g2}")
    print("CONNECTED", connected)
    print("DELETED", deleted)
    return 0, connected, deleted, g0, g2


if __name__ == "__main__":
    code, connected, deleted, g0, g2 = main()
    raise SystemExit(code)
