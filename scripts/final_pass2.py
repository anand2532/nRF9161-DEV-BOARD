#!/usr/bin/env python3
"""Continue connectivity from the after-gpio live board.

Fixes layer-mismatch (F.Cu SMD vs B.Cu without via), wrap-around U1 fanout,
route_to_via GPIO (do not thread the 0.95 mm via ring), short DNP stubs,
P0.15 clearance nudge. Never restores the RF-only backup. Never wipes B.Cu.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import ADC, BOARD, RF_NETS, hypot, nm, vec  # noqa: E402
from final_connect import (  # noqa: E402
    BACKUP,
    DRC_JSON,
    Final,
    SNAP_DIR,
    fill_zones,
    run_drc,
)

ROOT = "/home/anand/kicad-projects/nRF9161-DEV-BOARD"


def fatal(counts, baseline):
    shorts = counts.get("shorting_items", 0)
    hole = counts.get("hole_clearance", 0)
    clr = counts.get("clearance", 0)
    if shorts > 0:
        return f"shorts={shorts}"
    if hole > baseline.get("hole_clearance", 0):
        return f"hole_clearance={hole}"
    if clr > max(baseline.get("clearance", 0), 1):
        return f"clearance={clr}"
    return None


def save_chk(board, r, label, baseline, last_good):
    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"  DRC [{label}] unconnected={n} shorts={counts.get('shorting_items', 0)} "
        f"clear={counts.get('clearance', 0)} hole={counts.get('hole_clearance', 0)} ok={r.ok}",
        flush=True,
    )
    why = fatal(counts, baseline)
    if why:
        print(f"ABORT {why}; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    snap = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, snap)
    return pairs, n, counts


def load():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def stitch_layer_gaps(r: Final, pairs):
    """SMD pad / F.Cu vs B.Cu at the same XY does not connect. Insert a via."""
    n = 0
    for p in pairs:
        name = p["net"]
        if not name or name in ("GND",) or name in RF_NETS:
            continue
        a_b = p["a_b"] and not p["a_pth"] and "B.Cu" in p["a"]
        b_b = p["b_b"] and not p["b_pth"] and "B.Cu" in p["b"]
        a_f = "F.Cu" in p["a"] or (p["a_pth"] is False and "Pad" in p["a"])
        b_f = "F.Cu" in p["b"] or (p["b_pth"] is False and "Pad" in p["b"])
        layer_mismatch = (a_b and b_f) or (b_b and a_f)
        d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
        if not layer_mismatch:
            continue
        # Via near the F.Cu side
        if a_f:
            fx, fy = p["ax"], p["ay"]
        else:
            fx, fy = p["bx"], p["by"]
        pwr = name.startswith(("VDD", "VIN")) or name in ("SIM_1V8", "SIM_VCC", "ENABLE")
        site = None
        if r.via_ok(fx, fy, name, pwr=pwr):
            site = (fx, fy)
        else:
            site = r.local_via(fx, fy, name, pwr=pwr)
        if not site:
            print(f"  no via stitch {name} @({fx:.2f},{fy:.2f}) d={d:.2f}")
            continue
        if r.route_f_any(fx, fy, site[0], site[1], name) or d < 0.4:
            r.add_via(site[0], site[1], r.code_of(name), name, pwr=pwr)
            # B.Cu already at the pair; tie via to B.Cu point
            bx, by = (p["bx"], p["by"]) if a_f else (p["ax"], p["ay"])
            r.bcommit([(site[0], site[1]), (bx, by)], name)
            print(f"  stitch via {name} ({site[0]:.2f},{site[1]:.2f})")
            n += 1
    print(f"  stitched {n} F/B vias")
    r.collect()
    return n


def wrap_fanout(r: Final, name):
    p = r.u1(name)
    if not p:
        return False
    if r.nearest_via(name, p["x"], p["y"], 6.5):
        if not r.connected_to_track(p, name):
            v = r.nearest_via(name, p["x"], p["y"], 6.5)
            return r.oblong_escape(p, v["x"], v["y"], name)
        return True
    px, py = p["x"], p["y"]
    sites = []
    if name in ("MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_VIO", "MIPI_SCLK", "MIPI_SDATA"):
        for x in (26.90, 27.40, 25.90, 28.20):
            for y in (18.80, 18.20, 17.40, 16.80):
                sites.append((x, y))
    elif py < 32:
        # north row: via outside ring, wrap east of courtyard then north
        for y in (20.80, 19.85, 18.90):
            sites.append((px, y))
            sites.append((px - 0.55, y))
            sites.append((px + 0.55, y))
        sites.append((48.55, py))
        sites.append((48.55, 20.80))
    elif py > 32:
        for y in (43.20, 44.20, 45.20):
            sites.append((px, y))
            sites.append((px - 0.55, y))
            sites.append((px + 0.55, y))
        sites.append((48.55, py))
        sites.append((48.55, 43.20))
    else:
        sites.append((48.55, py))
        sites.append((48.55, py + 1.15))
    site = None
    for sx, sy in sites:
        if r.via_ok(sx, sy, name):
            site = (sx, sy)
            break
    if not site:
        site = r.local_via(px, py, name)
    if not site:
        print(f"  NOVIA {name}")
        return False
    vx, vy = site
    cands = []
    if name.startswith(("MAGPIO", "MIPI")):
        gy = 19.00
        for gx in (26.90, 25.90, 27.40):
            cands.append([(px, py), (gx, py), (gx, gy), (vx, gy), (vx, vy)])
    elif py < 32:
        cands.append([(px, py), (px, 24.80), (48.60, 24.80), (48.60, vy), (vx, vy)])
        cands.append([(px, py), (46.80, py), (46.80, vy), (vx, vy)])
        cands.append([(px, py), (px, 24.80), (vx, 24.80), (vx, vy)])
    else:
        cands.append([(px, py), (px, 39.80), (48.60, 39.80), (48.60, vy), (vx, vy)])
        cands.append([(px, py), (46.80, py), (46.80, vy), (vx, vy)])
        cands.append([(px, py), (px, 39.80), (vx, 39.80), (vx, vy)])
    cands.append([(px, py), (vx, py), (vx, vy)])
    cands.append([(px, py), (px, vy), (vx, vy)])
    for pts in cands:
        if r.fcommit(pts, name, 0.18):
            r.add_via(vx, vy, p["code"], name)
            print(f"  via {name} ({vx:.2f},{vy:.2f})")
            return True
    if r.route_f_any(px, py, vx, vy, name, 0.18):
        r.add_via(vx, vy, p["code"], name)
        print(f"  via astar-off {name} ({vx:.2f},{vy:.2f})")
        return True
    print(f"  FANOUT fail {name} site=({vx:.2f},{vy:.2f})")
    return False


def gpio_to_via(r: Final):
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or p["name"] in ("VDD_GPIO",)
        }
    )
    closed = 0
    for name in nets:
        hdr = r.primary_header(name)
        p = r.u1(name)
        w = 0.18 if not name.startswith("VDD") else 0.25
        code = r.code_of(name)
        via = None
        if p:
            via = r.nearest_via(name, p["x"], p["y"], 7.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias and hdr:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
        if not hdr or not via:
            continue
        if r.route_to_via(hdr["x"], hdr["y"], via["x"], via["y"], name, w, code):
            print(f"  to-via {name} {hdr['ref']}.{hdr['num']}")
            closed += 1
        else:
            if r.route_b_any(hdr["x"], hdr["y"], via["x"], via["y"], name, w, astar=True):
                print(f"  b-any {name} {hdr['ref']}")
                closed += 1
            else:
                print(f"  FAIL {name}")
                continue
        for extra in r.extras(name, hdr):
            if extra["y"] > 70 and hdr["y"] > 70:
                stub = 77.55 if name not in ADC else 77.90
                pts = [
                    (hdr["x"], hdr["y"]),
                    (hdr["x"], stub),
                    (extra["x"], stub),
                    (extra["x"], extra["y"]),
                ]
                if r.bcommit(pts, name, w):
                    continue
            if extra["x"] > 100:
                xf = 111.2
                pts = [
                    (hdr["x"], hdr["y"]),
                    (hdr["x"], 74.20),
                    (xf, 74.20),
                    (xf, extra["y"]),
                    (extra["x"], extra["y"]),
                ]
                if r.bcommit(pts, name, w):
                    continue
            if extra["ref"] == "J18":
                pts = [
                    (hdr["x"], hdr["y"]),
                    (hdr["x"], 58.80),
                    (extra["x"], 58.80),
                    (extra["x"], extra["y"]),
                ]
                if r.bcommit(pts, name, w):
                    continue
            r.route_b_any(hdr["x"], hdr["y"], extra["x"], extra["y"], name, w, astar=True)
    print(f"  gpio primary closed {closed}")


def explicit_shorts(r: Final):
    """Remaining SMD-SMD F.Cu islands with 0.20–0.25 mm jogs."""
    def jf(net, a, b, w=0.22):
        if not a or not b:
            return
        if r.route_f_any(a["x"], a["y"], b["x"], b["y"], net, w):
            print(f"  F {net} {a['ref']}-{b['ref']}")
        else:
            print(f"  F fail {net} {a['ref']}-{b['ref']}")

    c6, c3 = r.pad("C6", "1"), r.pad("C3", "1")
    if c6 and c3:
        for pts in (
            [(c6["x"], c6["y"]), (c6["x"], 25.40), (c3["x"], 25.40), (c3["x"], c3["y"])],
            [(c6["x"], c6["y"]), (50.20, c6["y"]), (50.20, 25.40), (c3["x"], 25.40), (c3["x"], c3["y"])],
        ):
            if r.fcommit(pts, "VDD1", 0.22):
                print("  VDD1 C6-C3")
                break
        else:
            jf("VDD1", c6, c3, 0.22)

    fb2, fb3 = r.pad("FB2", "2"), r.pad("FB3", "1")
    if fb2 and fb3:
        for yj in (16.40, 15.80, 19.80, 20.40):
            pts = [(fb2["x"], fb2["y"]), (fb2["x"], yj), (fb3["x"], yj), (fb3["x"], fb3["y"])]
            if r.fcommit(pts, "VDD2_MID", 0.25):
                print("  VDD2_MID")
                break

    c13 = r.pad("C13", "1")
    v = r.nearest_via("DEC0", 48.65, 21.13, 5)
    if c13 and v:
        for xj in (51.60, 52.20, 46.20, 45.40):
            pts = [(c13["x"], c13["y"]), (xj, c13["y"]), (xj, v["y"]), (v["x"], v["y"])]
            if r.fcommit(pts, "DEC0", 0.22):
                print("  DEC0")
                break

    c14, r1 = r.pad("C14", "1"), r.pad("R1", "2")
    if c14 and r1:
        pts = [(c14["x"], c14["y"]), (c14["x"], 21.20), (r1["x"], 21.20), (r1["x"], r1["y"])]
        if r.fcommit(pts, "ENABLE", 0.20):
            print("  ENABLE C14-R1")
        else:
            jf("ENABLE", c14, r1, 0.20)
    sw1, u2e = r.pad("SW1", "1"), r.pad("U2", "3")
    if sw1 and u2e:
        v1 = r.nearest_via("ENABLE", sw1["x"], sw1["y"], 5)
        v2 = r.nearest_via("ENABLE", u2e["x"], u2e["y"], 10) or r.nearest_via("ENABLE", 42.75, 41.10, 6)
        if v1 and v2:
            if r.route_b_any(v1["x"], v1["y"], v2["x"], v2["y"], "ENABLE", 0.20, astar=True):
                print("  ENABLE SW1 B")
        elif sw1 and u2e:
            jf("ENABLE", u2e, sw1, 0.20)

    c39 = r.pad("C39", "1")
    vnr = r.nearest_via("nRESET", 38.25, 23.10, 5)
    if c39 and vnr:
        pts = [(c39["x"], c39["y"]), (c39["x"], 14.60), (vnr["x"], 14.60), (vnr["x"], vnr["y"])]
        if r.fcommit(pts, "nRESET", 0.18):
            print("  nRESET C39")
        else:
            jf("nRESET", c39, r.u1("nRESET"), 0.18)
    r5 = r.pad("R5", "1")
    vr5 = r.nearest_via("nRESET", 103.30, 36.00, 6)
    if r5:
        if vr5:
            jf("nRESET", r5, {"x": vr5["x"], "y": vr5["y"], "ref": "via"}, 0.18)
        if vnr and vr5:
            r.route_b_any(vnr["x"], vnr["y"], vr5["x"], vr5["y"], "nRESET", 0.18, astar=True)

    uclk, j8 = r.u1("SWDCLK"), r.pad("J8", "4")
    if uclk and j8:
        pts = [(uclk["x"], uclk["y"]), (uclk["x"], 23.10)]
        site = (uclk["x"], 21.95)
        if r.via_ok(site[0], site[1], "SWDCLK") and r.fcommit(
            [(uclk["x"], uclk["y"]), (uclk["x"], site[1])], "SWDCLK", 0.18
        ):
            r.add_via(site[0], site[1], r.code_of("SWDCLK"), "SWDCLK")
            r.route_f_any(site[0], site[1], j8["x"], j8["y"], "SWDCLK", 0.18)
            print("  SWDCLK via+F")
        else:
            jf("SWDCLK", uclk, j8, 0.18)

    c28, c30, l4, fb5 = r.pad("C28", "1"), r.pad("C30", "1"), r.pad("L4", "1"), r.pad("FB5", "2")
    if c28 and c30:
        pts = [(c28["x"], c28["y"]), (12.05, c28["y"]), (12.05, c30["y"]), (c30["x"], c30["y"])]
        if r.fcommit(pts, "GNSS_VBIAS", 0.20):
            print("  GNSS C28-C30 west")
        else:
            jf("GNSS_VBIAS", c28, c30, 0.20)
    if c30 and l4:
        pts = [(c30["x"], c30["y"]), (17.52, c30["y"]), (17.52, l4["y"]), (l4["x"], l4["y"])]
        if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
            jf("GNSS_VBIAS", c30, l4, 0.20)
    if l4 and fb5:
        pts = [(l4["x"], l4["y"]), (14.00, l4["y"]), (14.00, fb5["y"]), (fb5["x"], fb5["y"])]
        if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
            jf("GNSS_VBIAS", l4, fb5, 0.20)

    # SIM local F.Cu 0.18
    for net, ra, na, rb, nb in (
        ("SIM_CLK", "C35", "1", "U4", "7"),
        ("SIM_RST", "C36", "1", "U4", "6"),
        ("SIM_IO", "C37", "1", "U4", "8"),
        ("SIM_1V8", "C38", "1", "U4", "5"),
        ("SIM_1V8", "C33", "1", "C38", "1"),
        ("SIM_CLK_C", "U4", "2", "J7", None),
        ("SIM_RST_C", "U4", "3", "J7", None),
        ("SIM_IO_C", "U4", "1", "J7", None),
    ):
        a = r.pad(ra, na, net if ra == "J7" else None) if na else r.pad(ra, net=net)
        if rb == "J7":
            b = r.pad("J7", None, net)
        else:
            b = r.pad(rb, nb, net if rb == "U4" else None)
            if b is None:
                b = r.pad(rb, nb)
        if a and b:
            if not r.join_f(a, b, net):
                va = r.nearest_via(net, a["x"], a["y"], 8)
                vb = r.nearest_via(net, b["x"], b["y"], 8)
                if va and vb:
                    r.route_b_any(va["x"], va["y"], vb["x"], vb["y"], net, 0.18, astar=True)

    f1v = r.nearest_via("VIN_F", 49.30, 12.60, 3)
    fb4 = r.pad("FB4", "1")
    if f1v and fb4:
        v2 = r.nearest_via("VIN_F", fb4["x"], fb4["y"], 5)
        if v2:
            r.route_b_any(f1v["x"], f1v["y"], v2["x"], v2["y"], "VIN_F", 0.25, astar=True)
    jp1 = r.pad("JP1", "1")
    r2 = r.pad("R2", "1")
    if jp1 and r2:
        jf("VIN_FILT", jp1, r2, 0.25)

    u22, c8 = r.u1("VDD2"), r.pad("C8", "1")
    if u22 and c8:
        pts = [(u22["x"], u22["y"]), (46.80, u22["y"]), (46.80, c8["y"]), (c8["x"], c8["y"])]
        if not r.fcommit(pts, "VDD2", 0.25):
            jf("VDD2", u22, c8, 0.25)


def dnp_stubs(r: Final):
    for net, ref, xj in (
        ("ANT", "C21", 22.4),
        ("ANT_FIT", "C22", 21.6),
        ("AUX", "C23", 21.6),
        ("AUX_FIT", "C24", 21.6),
        ("GPS", "C31", 22.4),
    ):
        p = r.pad(ref, "1")
        if not p:
            continue
        # Only a short jog to the nearest SAME-NET track endpoint, not through trunks.
        ends = []
        for t in r.tracks:
            if t["n"] != net or t["ly"] != pcbnew.F_Cu:
                continue
            ends.append((t["x1"], t["y1"]))
            ends.append((t["x2"], t["y2"]))
        if not ends:
            continue
        t = min(ends, key=lambda q: hypot(p["x"], p["y"], q[0], q[1]))
        if hypot(p["x"], p["y"], t[0], t[1]) > 12:
            continue
        pts = [(p["x"], p["y"]), (xj, p["y"]), (xj, t[1]), t]
        if r.fcommit(pts, net, 0.20):
            print(f"  DNP {ref} {net}")
        else:
            pts = [(p["x"], p["y"]), (xj, p["y"]), (xj, t[1])]
            if hypot(xj, t[1], t[0], t[1]) < 3 and r.fcommit(pts + [t], net, 0.20):
                print(f"  DNP short {ref}")
            else:
                print(f"  DNP skip {ref} (would cross RF)")


def nudge_p015(r: Final):
    changed = 0
    for tr in r.board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        # Only the vertical at x≈106.10
        if abs(x1 - 106.10) < 0.08 and abs(x2 - 106.10) < 0.08:
            tr.SetStart(vec(105.40, y1))
            tr.SetEnd(vec(105.40, y2))
            changed += 1
            continue
        # T-junctions that ended on that vertical
        nx1, nx2 = x1, x2
        if abs(x1 - 106.10) < 0.08 and abs(x2 - 106.10) > 0.5:
            nx1 = 105.40
        if abs(x2 - 106.10) < 0.08 and abs(x1 - 106.10) > 0.5:
            nx2 = 105.40
        if nx1 != x1 or nx2 != x2:
            tr.SetStart(vec(nx1, y1))
            tr.SetEnd(vec(nx2, y2))
            changed += 1
    print(f"  P0.15 nudged {changed} segments")
    r.collect()


def main():
    pairs, n0, base, _ = run_drc()
    print(f"start unconnected={n0} clear={base.get('clearance', 0)} shorts={base.get('shorting_items', 0)}")
    baseline = {
        "shorting_items": base.get("shorting_items", 0),
        "clearance": base.get("clearance", 0),
        "hole_clearance": base.get("hole_clearance", 0),
    }
    last_good = os.path.join(SNAP_DIR, "after-gpio.kicad_pcb")
    if not os.path.isfile(last_good):
        last_good = BACKUP
    board, r = load()

    print("#### stitch F/B", flush=True)
    stitch_layer_gaps(r, pairs)
    r.collect()
    got = save_chk(board, r, "stitch", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-stitch.kicad_pcb")
    board, r = load()
    baseline["clearance"] = min(baseline["clearance"], counts.get("clearance", 1))

    print("#### explicit shorts", flush=True)
    explicit_shorts(r)
    r.collect()
    got = save_chk(board, r, "explicit", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-explicit.kicad_pcb")
    board, r = load()

    print("#### wrap fanout", flush=True)
    for name in (
        "P0.01",
        "P0.04",
        "P0.06",
        "P0.09",
        "P0.11",
        "P0.14",
        "P0.16",
        "P0.18",
        "P0.20",
        "P0.22",
        "P0.24",
        "P0.27",
        "P0.29",
        "P0.31",
        "MAGPIO0",
        "MIPI_SDATA",
        "COEX1",
    ):
        wrap_fanout(r, name)
    r.collect()
    got = save_chk(board, r, "fanout2", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-fanout2.kicad_pcb")
    board, r = load()

    print("#### gpio route_to_via", flush=True)
    gpio_to_via(r)
    r.collect()
    got = save_chk(board, r, "gpio2", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-gpio2.kicad_pcb")
    board, r = load()

    print("#### P0.15 nudge", flush=True)
    nudge_p015(r)
    r.collect()
    got = save_chk(board, r, "p015", baseline, last_good)
    if got[0] is None:
        return 1
    pairs, n, counts = got
    last_good = os.path.join(SNAP_DIR, "after-p015.kicad_pcb")
    board, r = load()
    baseline["clearance"] = min(baseline["clearance"], counts.get("clearance", 1))

    print("#### DNP stubs", flush=True)
    dnp_stubs(r)
    r.collect()
    got = save_chk(board, r, "dnp2", baseline, last_good)
    if got[0] is None:
        print("DNP aborted; live restored to last good")
        board, r = load()
    else:
        pairs, n, counts = got
        last_good = os.path.join(SNAP_DIR, "after-dnp2.kicad_pcb")
        board, r = load()

    print("#### GND stitch", flush=True)
    r.stitch_gnd()
    r.collect()
    got = save_chk(board, r, "gnd", baseline, last_good)
    if got[0] is None:
        print("GND stitch aborted")
        return 0
    pairs, n, counts = got
    print(f"PASS2 FINAL unconnected={n} shorts={counts.get('shorting_items', 0)} clear={counts.get('clearance', 0)}")
    shutil.copy2(DRC_JSON, f"{ROOT}/reports/DRC_AFTER_CONNECT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
