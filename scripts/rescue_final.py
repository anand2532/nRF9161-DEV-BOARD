#!/usr/bin/env python3
"""Rescue pass: re-engineer non-RF routing until unconnected→0.

LIVE board only. Never restore RF-only backup, never wipe B.Cu, never
complete_route.main() / rebuild_bcu / Freerouting.
Save only if shorts=0. Abort+restore backup on shorts/clearance/hole_clearance.
"""
from __future__ import annotations

import os
import shutil
import sys
from collections import defaultdict, deque

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot, in_box, RF_BOX  # noqa: E402
from final_connect import BOARD, SNAP_DIR, Final, fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402
from rescue_audit import graph_net  # noqa: E402

ROOT = "/home/anand/kicad-projects/nRF9161-DEV-BOARD"
START = os.path.join(SNAP_DIR, "after-pass30-start.kicad_pcb")
ABORT = {"shorting_items", "clearance", "hole_clearance", "tracks_crossing"}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18

# P0.15 west wrap geometry (B.Cu only). Keep U1 F stub, courtyard via, east/south.
WRAP_XS = (30.5, 43.20)
WRAP_YS = (22.35, 59.45)


def mm_xy(tr):
    s, e = tr.GetStart(), tr.GetEnd()
    return pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)


def near(a, b, tol=0.25):
    return abs(a - b) < tol


def snap(label):
    return os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")


def check(board, r, label, last_good, ceiling, fill=False, must_drop=False):
    if fill:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"DRC [{label}] unconn={n} shorts={counts.get('shorting_items',0)} "
        f"clr={counts.get('clearance',0)} hole={counts.get('hole_clearance',0)} "
        f"via_d={counts.get('via_diameter',0)}",
        flush=True,
    )
    bad = [k for k in ABORT if counts.get(k, 0) > 0]
    if bad or n > ceiling or (must_drop and n >= ceiling):
        reason = {k: counts[k] for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}", flush=True)
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    shutil.copy2(BOARD, snap(label))
    return pairs, n, counts, pairs


def pok(r, pts, layer, name, w=W):
    for a, b in zip(pts, pts[1:]):
        if hypot(a[0], a[1], b[0], b[1]) < 0.03:
            continue
        if not r.track_clear(a[0], a[1], b[0], b[1], layer, w, name):
            return why(r, [a, b], layer, w, name)
    return None


def try_pts(r, pts, layer, name, label, w=W):
    if pok(r, pts, layer, name, w) is not None:
        print(f"  FAIL {label}: {pok(r, pts, layer, name, w)}", flush=True)
        return False
    ok = r.commit(pts, layer, w, r.code_of(name), name)
    print(f"  {'OK' if ok else 'FAIL commit'} {label}", flush=True)
    return ok


def delete_tracks_vias(board, pred_tr, pred_via=None):
    ntr = nvia = 0
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            if pred_via and pred_via(tr):
                board.Remove(tr)
                nvia += 1
            continue
        if pred_tr(tr):
            board.Remove(tr)
            ntr += 1
    return ntr, nvia


def rip_p013_courtyard(board):
    """P0.13 courtyard via+F stub blocks P0.15 east F.Cu. Net is already OPEN."""

    def tr(t):
        if t.GetNetname() != "P0.13" or t.GetLayer() != F:
            return False
        x1, y1, x2, y2 = mm_xy(t)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        return 41.5 <= mx <= 44.5 and 22.5 <= my <= 28.0

    def via(v):
        if v.GetNetname() != "P0.13":
            return False
        p = v.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        return 41.5 <= x <= 44.5 and 22.5 <= y <= 28.0

    ntr, nvia = delete_tracks_vias(board, tr, via)
    print(f"  ripped P0.13 courtyard tracks={ntr} vias={nvia}", flush=True)
    return ntr + nvia


def delete_p015_west_wrap(board):
    def tr(t):
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            return False
        x1, y1, x2, y2 = mm_xy(t)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # Keep north stubs x=41.75 y<=23.15, east stub y=22.5 x>=41.7, south of J18.
        if near((x1 + x2) / 2, 41.75, 0.20) and max(y1, y2) <= 23.20:
            return False
        if near((y1 + y2) / 2, 22.50, 0.20) and min(x1, x2) >= 41.65:
            return False
        if min(y1, y2) >= 61.8:
            return False
        if 30.8 <= mx <= 43.25 and 22.35 <= my <= 59.55:
            return True
        # wrap arrival onto J18 from y=59.2
        if near((x1 + x2) / 2, 43.08, 0.20) and min(y1, y2) >= 58.8 and max(y1, y2) <= 62.3:
            return True
        return False

    ntr, _ = delete_tracks_vias(board, tr)
    print(f"  deleted P0.15 west-wrap tracks={ntr}", flush=True)
    return ntr


def delete_p015_unused_north_stubs(board):
    """Drop unused east courtyard stub at y=22.50 / x=46.50.

    Keep (41.75,23.10)-(41.75,20.60): feed into the new east-north hop.
    """

    def tr(t):
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            return False
        x1, y1, x2, y2 = mm_xy(t)
        if near((y1 + y2) / 2, 22.50, 0.2) and min(x1, x2) >= 41.6 and max(x1, x2) <= 47.0:
            return True
        if near((x1 + x2) / 2, 46.50, 0.2) and min(y1, y2) >= 21.0 and max(y1, y2) <= 22.7:
            return True
        return False

    ntr, _ = delete_tracks_vias(board, tr)
    print(f"  deleted P0.15 unused east stubs={ntr}", flush=True)


def p015_f_candidates():
    gx, gy = 55.00, 8.00
    out = []
    out.append([(41.75, 23.10), (41.75, 24.90), (48.40, 24.90), (48.40, 20.40), (gx, 20.40), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 24.90), (47.20, 24.90), (47.20, 28.80), (51.80, 28.80), (51.80, gy), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 24.90), (47.20, 24.90), (47.20, 21.00), (gx, 21.00), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 24.70), (gx, 24.70), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 20.40), (43.80, 20.40), (43.80, gy), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 20.20), (46.20, 20.20), (46.20, gy), (gx, gy)])
    out.append([(41.75, 26.75), (41.75, 25.20), (46.80, 25.20), (46.80, gy), (gx, gy)])
    out.append([(41.75, 23.10), (41.75, 24.90), (90.00, 24.90), (90.00, 8.00)])
    out.append([(41.75, 23.10), (41.75, 24.90), (52.00, 24.90), (52.00, 12.00)])
    for y in (24.70, 25.10, 28.40, 29.20, 20.20, 19.40, 16.50, 12.00, 9.00):
        out.append([(41.75, 23.10), (41.75, y if y >= 23.10 else 24.90), (55.00, y if y >= 23.10 else 24.90), (55.00, y), (55.00, 8.00)])
    return out


def rip_p001_west_dangle(board):
    """P0.01 B.Cu y=15.20 x=27.65–86.14 is dangling and walls the north corridor.
    Keep the east spine x>=86.14 that still feeds J12.
    """
    n = 0
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.01" or tr.GetLayer() != B:
            continue
        x1, y1, x2, y2 = mm_xy(tr)
        if near((y1 + y2) / 2, 15.20, 0.25) and abs(y1 - y2) < 0.4 and min(x1, x2) < 80:
            print(f"  DEL dangling P0.01 ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f})", flush=True)
            board.Remove(tr)
            n += 1
    return n


def route_p015(board, r):
    print("== P0.15 new topology: B.Cu y=15.35 via x=72 / y=7.2 to x=106 ==", flush=True)
    n = rip_p001_west_dangle(board)
    print(f"  ripped P0.01 west dangle segs={n}", flush=True)
    r.collect()
    bpaths = [
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.35),
            (72.00, 15.35),
            (72.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.45),
            (74.00, 15.45),
            (74.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
        [
            (41.75, 20.60),
            (46.70, 20.60),
            (46.70, 15.45),
            (76.00, 15.45),
            (76.00, 7.20),
            (106.00, 7.20),
            (106.00, 20.60),
        ],
    ]
    for i, pts in enumerate(bpaths):
        if try_pts(r, pts, B, "P0.15", f"B east-north i={i}"):
            return True
    print("  P0.15 B.Cu east-north failed", flush=True)
    return False


def closest_island_pair(islands):
    best = None
    for i, a in enumerate(islands):
        for b in islands[i + 1 :]:
            for pa in a:
                for pb in b:
                    d = hypot(pa[0], pa[1], pb[0], pb[1])
                    if best is None or d < best[0]:
                        best = (d, pa, pb, a, b)
    return best


def existing_via(r, name, x, y, limit=10.0):
    vias = [v for v in r.vias if v["n"] == name]
    if not vias:
        return None
    v = min(vias, key=lambda q: hypot(q["x"], q["y"], x, y))
    if hypot(v["x"], v["y"], x, y) > limit:
        return None
    return v


def search_via_ring(r, name, x, y):
    """Legal via near a U1 pad; not the 0.95 mm ring as a requirement."""
    pwr = name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC"))
    deltas = []
    for dy in (-3.65, -3.2, -2.8, -2.4, -1.8, 1.8, 2.4, 2.8, 3.65, 3.85):
        deltas.append((0.0, dy))
    for dx in (-2.2, -1.6, -1.1, 1.1, 1.6, 2.2, 3.4, 4.0):
        deltas.append((dx, 0.0))
        deltas.append((dx, -2.8))
        deltas.append((dx, 2.8))
    for d in (0.4, 0.8, 1.2, 1.8, 2.4, 3.2):
        for ang in range(0, 360, 30):
            rad = ang * 3.14159265 / 180.0
            deltas.append((d * __import__("math").cos(rad), d * __import__("math").sin(rad)))
    seen = set()
    for dx, dy in deltas:
        vx, vy = round(x + dx, 2), round(y + dy, 2)
        key = (vx, vy)
        if key in seen:
            continue
        seen.add(key)
        if r.via_why(vx, vy, name, pwr=pwr) is None:
            return vx, vy
    site = r.search_via(x, y, name, pwr=pwr)
    return site


def b_private(r, name, x1, y1, x2, y2):
    """Few private B.Cu channels, then one waypoint. West courtyard after wrap delete."""
    w = r.local_w(name)
    cols = [25.55, 26.90, 32.20, 34.50, 36.50, 46.70, 64.70, 74.00, 106.00, 111.20]
    rows = [7.20, 15.35, 23.10, 41.10, 58.80, 74.00, 77.45, 78.15]
    paths = [
        [(x1, y1), (x2, y1), (x2, y2)],
        [(x1, y1), (x1, y2), (x2, y2)],
    ]
    for c in cols:
        paths.append([(x1, y1), (c, y1), (c, y2), (x2, y2)])
    for row in rows:
        paths.append([(x1, y1), (x1, row), (x2, row), (x2, y2)])
        paths.append([(x1, y1), (x1, row), (32.20, row), (32.20, y2), (x2, y2)])
        paths.append([(x1, y1), (x1, row), (106.00, row), (106.00, y2), (x2, y2)])
    for pts in paths:
        if pok(r, pts, B, name, w) is None:
            if r.commit(pts, B, w, r.code_of(name), name):
                print(f"  OK {name} B-private", flush=True)
                return True
    xs = sorted(set([round(x1, 2), round(x2, 2)] + cols))
    ys = sorted(set([round(y1, 2), round(y2, 2)] + rows))
    pts, L = waypoint_route(r, x1, y1, x2, y2, B, w, name, xs=xs, ys=ys)
    if pts and L < 160 and pok(r, pts, B, name, w) is None:
        if r.commit(pts, B, w, r.code_of(name), name):
            print(f"  OK {name} Bwp L={L:.1f}", flush=True)
            return True
    print(f"  FAIL {name} B from ({x1:.2f},{y1:.2f}) to ({x2:.2f},{y2:.2f})", flush=True)
    return False


def f_jogs(r, name, x1, y1, x2, y2):
    w = r.local_w(name)
    cands = [
        [(x1, y1), (x2, y2)],
        [(x1, y1), (x2, y1), (x2, y2)],
        [(x1, y1), (x1, y2), (x2, y2)],
    ]
    for d in (-0.6, 0.6, -1.2, 1.2, -2.0, 2.0, -3.2, 3.2):
        cands.append([(x1, y1), (x1, y1 + d), (x2, y1 + d), (x2, y2)])
        cands.append([(x1, y1), (x1 + d, y1), (x1 + d, y2), (x2, y2)])
    for pts in cands:
        if pok(r, pts, F, name, w) is None and r.commit(pts, F, w, r.code_of(name), name):
            print(f"  OK {name} F-jog", flush=True)
            return True
    return False


def join_points(r, name, p1, p2):
    """Join two points with correct layer: SMD stays F.Cu; PTH/via may use B.Cu."""
    x1, y1 = p1
    x2, y2 = p2
    u1 = r.u1(name)
    dest_pth = None
    for p in r.pads:
        if p["name"] != name:
            continue
        if p["pth"] and hypot(p["x"], p["y"], x2, y2) < 0.6:
            dest_pth = p
            break
        if p["pth"] and hypot(p["x"], p["y"], x1, y1) < 0.6:
            dest_pth = p
            x1, y1, x2, y2 = x2, y2, x1, y1
            u1 = r.u1(name)
            break

    # Same-layer F.Cu first when both ends look like F (short gaps).
    if hypot(x1, y1, x2, y2) < 8.0:
        if f_jogs(r, name, x1, y1, x2, y2):
            return True

    # Via at U1 island, then B.Cu to destination.
    vx = vy = None
    v = existing_via(r, name, x1, y1, limit=8.0)
    if v:
        vx, vy = v["x"], v["y"]
        print(f"  {name} using via ({vx:.2f},{vy:.2f})", flush=True)
        if u1 and hypot(u1["x"], u1["y"], vx, vy) > 0.2:
            f_jogs(r, name, u1["x"], u1["y"], vx, vy)
    else:
        site = search_via_ring(r, name, x1, y1)
        if site:
            vx, vy = site
            if f_jogs(r, name, x1, y1, vx, vy) or pok(r, [(x1, y1), (vx, vy)], F, name) is None:
                if pok(r, [(x1, y1), (vx, vy)], F, name) is None:
                    r.commit([(x1, y1), (vx, vy)], F, r.local_w(name), r.code_of(name), name)
                r.add_via(vx, vy, r.code_of(name), name, pwr=name.startswith(("VDD", "VIN")))
                r.collect()
                print(f"  {name} new via ({vx:.2f},{vy:.2f})", flush=True)
            else:
                vx = vy = None
    if vx is None:
        # last-ditch same-layer B if both PTH
        return b_private(r, name, x1, y1, x2, y2)

    r.collect()
    return b_private(r, name, vx, vy, x2, y2)


def route_net_islands(r, name, pair=None):
    u1 = r.u1(name)
    if pair and u1:
        ax, ay, bx, by = pair["ax"], pair["ay"], pair["bx"], pair["by"]
        d1 = hypot(ax, ay, u1["x"], u1["y"])
        d2 = hypot(bx, by, u1["x"], u1["y"])
        dest = (bx, by) if d1 <= d2 else (ax, ay)
        print(f"  {name} U1 ({u1['x']:.2f},{u1['y']:.2f}) -> DRC ({dest[0]:.2f},{dest[1]:.2f})", flush=True)
        return join_points(r, name, (u1["x"], u1["y"]), dest)
    dests = []
    for p in r.pads:
        if p["name"] != name or p["ref"] == "U1":
            continue
        dests.append((p["x"], p["y"], "pad", p["pth"]))
    if u1 and dests:
        pth = [d for d in dests if d[3]]
        pool = pth or dests
        d = min(pool, key=lambda q: hypot(q[0], q[1], u1["x"], u1["y"]))
        print(f"  {name} U1 ({u1['x']:.2f},{u1['y']:.2f}) -> {d[2]} ({d[0]:.2f},{d[1]:.2f})", flush=True)
        return join_points(r, name, (u1["x"], u1["y"]), (d[0], d[1]))
    islands = graph_net(r, name)
    if len(islands) < 2:
        return False
    islands.sort(key=len, reverse=True)
    pair2 = closest_island_pair(islands[:4])
    if not pair2:
        return False
    dist, p1, p2, _, _ = pair2
    print(f"  {name} islands={len(islands)} closest {dist:.2f}mm {p1}->{p2}", flush=True)
    return join_points(r, name, p1, p2)


def route_dnp_stubs(r):
    """Optional DNP 50Ω shunts: short stub to existing same-net copper. No trunk rewrite."""
    print("== DNP stubs ==", flush=True)
    for name, ref in (("ANT_FIT", "C22"), ("AUX", "C23"), ("AUX_FIT", "C24")):
        pad = r.pad(ref, "1")
        if not pad:
            continue
        islands = graph_net(r, name)
        if len(islands) < 2:
            continue
        pair = closest_island_pair(islands)
        if not pair:
            continue
        d, p1, p2, _, _ = pair
        print(f"  {name} stub {d:.3f}mm {p1}->{p2}", flush=True)
        # Allow RF_BOX for these RF nets (same-net stub only).
        join_points(r, name, p1, p2)


def stitch_gnd(board, r):
    print("== GND refill ==", flush=True)
    fill_zones(board)
    r.collect()


def fix_tiny_vias(board):
    """via_diameter / drill_out_of_range on P0.02 and nRESET."""
    n = 0
    for tr in board.GetTracks():
        if not isinstance(tr, pcbnew.PCB_VIA):
            continue
        name = tr.GetNetname()
        if name not in ("P0.02", "nRESET"):
            continue
        size = pcbnew.ToMM(tr.GetWidth())
        drill = pcbnew.ToMM(tr.GetDrill())
        if size + 1e-6 < 0.60 or drill + 1e-6 < 0.30:
            print(f"  resize via {name} {size:.3f}/{drill:.3f} -> 0.60/0.30", flush=True)
            tr.SetDrill(pcbnew.FromMM(0.30))
            try:
                tr.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(0.60))
                tr.SetWidth(pcbnew.B_Cu, pcbnew.FromMM(0.60))
            except TypeError:
                pass
            try:
                tr.SetFrontWidth(pcbnew.FromMM(0.60))
            except Exception:
                pass
            n += 1
    return n


PRIO_NETS = [
    "P0.13",
    "P0.14",
    "P0.16",
    "P0.17",
    "P0.18",
    "VIN_FILT",
    "VIN_F",
    "nRESET",
    "SWDCLK",
    "SIM_CLK",
    "SIM_IO",
    "SIM_RST",
    "SIM_1V8",
    "VDD_GPIO",
    "P0.08",
    "P0.19",
    "P0.20",
    "P0.00",
    "P0.01",
    "P0.02",
    "P0.03",
    "P0.05",
    "P0.07",
    "P0.09",
    "P0.10",
    "P0.11",
    "P0.12",
    "P0.21",
    "P0.22",
    "P0.23",
    "P0.24",
    "P0.25",
    "P0.26",
    "P0.27",
    "P0.28",
    "P0.29",
    "P0.30",
    "P0.31",
    "MAGPIO0",
    "MAGPIO1",
    "MAGPIO2",
    "MIPI_VIO",
    "MIPI_SCLK",
    "MIPI_SDATA",
    "COEX0",
    "COEX1",
]


def open_nets(pairs):
    s = []
    seen = set()
    for p in pairs:
        n = p["net"]
        if n in seen or n == "GND":
            continue
        seen.add(n)
        s.append(n)
    return s


def main():
    if not os.path.exists(START):
        shutil.copy2(BOARD, START)
    last = START
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    pairs, n0, counts, _ = run_drc()
    print(f"START unconn={n0} shorts={counts.get('shorting_items',0)}", flush=True)
    ceiling = n0
    u1 = board.FindFootprintByReference("U1")
    print(f"U1 ({pcbnew.ToMM(u1.GetPosition().x):.2f},{pcbnew.ToMM(u1.GetPosition().y):.2f}) rot={u1.GetOrientationDegrees()}", flush=True)

    # --- P0.15 ---
    already = any(
        t["n"] == "P0.15" and t["ly"] == B
        and abs((t["y1"] + t["y2"]) / 2 - 15.35) < 0.15
        and max(t["x1"], t["x2"]) > 70
        for t in r.tracks
    )
    if already:
        print("P0.15 east-north hop already present; skip add", flush=True)
        if os.path.exists(snap("pass30-p015-add")):
            last = snap("pass30-p015-add")
    else:
        if not route_p015(board, r):
            print("P0.15 B.Cu new topology failed; restoring start", flush=True)
            shutil.copy2(START, BOARD)
            return
        r.collect()
        got = check(board, r, "pass30-p015-add", last, ceiling)
        if got[0] is None:
            return
        pairs, n, counts, _ = got
        last = snap("pass30-p015-add")
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
    ceiling = n0
    print("deleting P0.15 west wrap", flush=True)
    delete_p015_west_wrap(board)
    delete_p015_unused_north_stubs(board)
    r.collect()
    got = check(board, r, "pass30-p015-wrapdel", last, ceiling, fill=True)
    if got[0] is None:
        return
    pairs, n, counts, _ = got
    last = snap("pass30-p015-wrapdel")
    ceiling = n
    print(f"P0.15 wrap removed, unconn={n}", flush=True)

    # --- island join loop ---
    stall = 0
    round_i = 0
    while n > 0 and stall < 6 and round_i < 20:
        round_i += 1
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n, counts, _ = run_drc()
        names = [x for x in PRIO_NETS if any(p["net"] == x for p in pairs)]
        names += [x for x in open_nets(pairs) if x not in names]
        names = [x for x in names if x not in ("ANT_FIT", "AUX", "AUX_FIT", "GND")]
        progressed = False
        for name in names:
            if name == "GND":
                continue
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
            print(f"-- join {name} --", flush=True)
            r.ok = 0
            net_pairs = [p for p in pairs if p["net"] == name]
            u1p = [p for p in net_pairs if " of U1" in p.get("a", "") or " of U1" in p.get("b", "")]
            pair = (u1p or net_pairs or [None])[0]
            if not route_net_islands(r, name, pair):
                continue
            r.collect()
            got = check(board, r, f"pass30-{name.replace('.', '')}-r{round_i}", last, ceiling, must_drop=True)
            if got[0] is None:
                board = pcbnew.LoadBoard(BOARD)
                r = Final(board)
                r.collect()
                continue
            pairs, n, counts, _ = got
            last = snap(f"pass30-{name.replace('.', '')}-r{round_i}")
            if n < ceiling:
                ceiling = n
                progressed = True
                print(f"  closed toward {name}, unconn={n}", flush=True)
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
        if not progressed:
            stall += 1
            print(f"stall {stall} unconn={n}", flush=True)
        else:
            stall = 0

        # Tiny via resize is safe (errors, not connectivity). DNP later.
        if n <= 20:
            board = pcbnew.LoadBoard(BOARD)
            r = Final(board)
            r.collect()
            r.ok = 0
            route_dnp_stubs(r)
            stitch_gnd(board, r)
            r.collect()
            got = check(board, r, f"pass30-dnp-gnd-r{round_i}", last, ceiling, fill=True)
            if got[0] is not None:
                pairs, n, counts, _ = got
                last = snap(f"pass30-dnp-gnd-r{round_i}")
                ceiling = min(ceiling, n)

    print(f"END unconn={n} last={last}", flush=True)


if __name__ == "__main__":
    main()
