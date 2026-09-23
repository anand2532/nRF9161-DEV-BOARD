#!/usr/bin/env python3
"""Pass 30 connect: place U3 TPS22919, FB5→0402, surgical Class F, safe extras.

HARD: backup already taken; no Gerbers; keep shorting=0; do not raise clearance
above baseline; do not rip P0.15 west wrap; RF keepout x0-24.2 y20-64.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
sys.path.insert(0, f"{ROOT}/scripts")

from complete_route import (  # noqa: E402
    BOARD,
    hypot,
    nm,
    vec,
)
from final_pass14 import Final  # noqa: E402
from final_connect import fill_zones, run_drc  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import (  # noqa: E402
    ABORT,
    class_counts,
    dump_vios,
    snap_path,
    try_commit,
    waypoint_route,
)

SNAP_DIR = f"{ROOT}/.mcp-backups/pass30-connect"
os.makedirs(SNAP_DIR, exist_ok=True)

# Override final_pass14 snap dir
import final_pass14 as p14  # noqa: E402

p14.SNAP_DIR = SNAP_DIR

F, B = pcbnew.F_Cu, pcbnew.B_Cu
FP_SOT = "/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty"
FP_IND = "/usr/share/kicad/footprints/Inductor_SMD.pretty"

BASELINE_CLR = 6  # pre-existing via/zone clearance from prior via upsizing
CLOSED = []
DEFERRED = []
PLACED = []


def ensure_net(board, name: str):
    ni = board.FindNet(name)
    if ni is not None and ni.GetNetCode() > 0:
        return ni
    item = pcbnew.NETINFO_ITEM(board, name)
    board.Add(item)
    return board.FindNet(name)


def set_pad_net(pad, netitem):
    pad.SetNet(netitem)

def netcode(board, name: str) -> int:
    ni = board.FindNet(name)
    if ni is None or ni.GetNetCode() <= 0:
        ni = ensure_net(board, name)
    return ni.GetNetCode()




def check(board, r, label, last_good, ceiling, clr_ceiling=BASELINE_CLR):
    if r.ok:
        fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    shorts = counts.get("shorting_items", 0)
    clr = counts.get("clearance", 0)
    hole = counts.get("hole_clearance", 0)
    print(
        f"DRC [{label}] unconn={n} shorts={shorts} clr={clr} hole={hole}",
        flush=True,
    )
    bad = []
    if shorts > 0:
        bad.append("shorting_items")
    if hole > 0:
        bad.append("hole_clearance")
    if clr > clr_ceiling:
        bad.append("clearance")
    if counts.get("tracks_crossing", 0) > 0:
        bad.append("tracks_crossing")
    if bad or n > ceiling:
        reason = {k: counts.get(k, 0) for k in bad} if bad else f"unconn {n}>{ceiling}"
        print(f"ABORT {reason}; restoring {last_good}", flush=True)
        dump_vios()
        shutil.copy2(last_good, BOARD)
        return None, n, counts, pairs
    dest = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, dest)
    return pairs, n, counts, pairs


def remove_tracks_touching_pad(board, r, netname, x, y, rad=0.6):
    """Delete short stubs of net that touch a pad center (for footprint swap)."""
    doomed = []
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() != netname:
            continue
        x1, y1 = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        x2, y2 = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
        if hypot(x1, y1, x, y) <= rad or hypot(x2, y2, x, y) <= rad:
            # only remove short local stubs
            if hypot(x1, y1, x2, y2) <= 3.0:
                doomed.append(t)
    for t in doomed:
        board.Remove(t)
    # refresh router cache lightly
    r.collect()


def place_u3_and_fb5(board, r):
    """Place U3 SC-70-6 and retarget FB5 to 0402 with correct nets."""
    global PLACED
    net_vdd = ensure_net(board, "VDD_GPIO")
    net_src = ensure_net(board, "GNSS_VBIAS_SRC")
    net_bias = ensure_net(board, "GNSS_VBIAS")
    net_coex = ensure_net(board, "COEX0")
    net_gnd = ensure_net(board, "GND")

    # --- FB5: exchange to 0402, keep center (14,46), orient 270 so pad1 south ---
    old = board.FindFootprintByReference("FB5")
    if old is None:
        raise RuntimeError("FB5 missing")
    old_pos = old.GetPosition()
    # remove short VDD_GPIO stub into old pad1 if any
    remove_tracks_touching_pad(
        board, r, "VDD_GPIO", pcbnew.ToMM(old_pos.x), pcbnew.ToMM(old_pos.y) + 0.8, rad=1.0
    )
    remove_tracks_touching_pad(
        board, r, "VDD_GPIO", 14.0, 46.7875, rad=0.8
    )
    # Keep GNSS_VBIAS north stubs; may need nudge after pad move

    new_fb = pcbnew.FootprintLoad(FP_IND, "L_0402_1005Metric")
    if new_fb is None:
        raise RuntimeError("cannot load L_0402_1005Metric")
    new_fb.SetReference("FB5")
    new_fb.SetValue(old.GetValue() or "BLM15HG102SN1")
    new_fb.SetPosition(old_pos)
    new_fb.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    new_fb.SetLayer(pcbnew.F_Cu)
    board.Remove(old)
    board.Add(new_fb)
    # pad nets: pad1 = GNSS_VBIAS_SRC, pad2 = GNSS_VBIAS
    for p in new_fb.Pads():
        if p.GetNumber() == "1":
            set_pad_net(p, net_src)
        elif p.GetNumber() == "2":
            set_pad_net(p, net_bias)
    PLACED.append("FB5→L_0402_1005Metric @ (14,46) orient90")

    # --- U3 place west of FB5 ---
    u3 = pcbnew.FootprintLoad(FP_SOT, "SOT-363_SC-70-6")
    if u3 is None:
        raise RuntimeError("cannot load SOT-363_SC-70-6")
    u3.SetReference("U3")
    u3.SetValue("TPS22919DCKR")
    # Outside RF keepout (x>24.2); VOUT (pad6) faces west toward FB5
    u3.SetPosition(vec(26.5, 47.0))
    u3.SetOrientation(pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
    u3.SetLayer(pcbnew.F_Cu)
    board.Add(u3)
    pin_nets = {
        "1": net_vdd,  # VIN
        "2": net_gnd,  # GND
        "3": net_coex,  # ON
        "4": None,  # NC
        "5": None,  # QOD leave unconnected
        "6": net_src,  # VOUT
    }
    for p in u3.Pads():
        n = pin_nets.get(p.GetNumber())
        if n is not None:
            set_pad_net(p, n)
        else:
            # leave no-net / unique
            pass
    PLACED.append("U3 TPS22919DCKR SOT-363 @ (26.5,47) orient180")

    r.collect()
    # Record pad positions
    pads = {}
    for p in u3.Pads():
        pads[p.GetNumber()] = (
            pcbnew.ToMM(p.GetPosition().x),
            pcbnew.ToMM(p.GetPosition().y),
        )
    for p in new_fb.Pads():
        pads[f"FB5.{p.GetNumber()}"] = (
            pcbnew.ToMM(p.GetPosition().x),
            pcbnew.ToMM(p.GetPosition().y),
        )
    print("U3/FB5 pads:", pads, flush=True)
    return u3, new_fb, pads


def route_u3_local(board, r, pads):
    """Route U3 VOUT→FB5, GND stitch, COEX0/VIN with RF-safe exits."""
    w = 0.25

    # VOUT pad6 → FB5.1 along y≈46.5–47 (north of GNSS_VBIAS y=45.21)
    x1, y1 = pads["6"]
    x2, y2 = pads["FB5.1"]
    ok = False
    for pts in [
        [(x1, y1), (x1, 46.6), (x2, 46.6), (x2, y2)],
        [(x1, y1), (20.0, y1), (20.0, y2), (x2, y2)],
        [(x1, y1), (x2, y1), (x2, y2)],
        [(x1, y1), (x2, y2)],
    ]:
        if try_commit(r, pts, F, w, "GNSS_VBIAS_SRC", f"U3.VOUT→FB5 {pts[1]}"):
            CLOSED.append("GNSS_VBIAS_SRC U3→FB5")
            ok = True
            break
    if not ok:
        DEFERRED.append("GNSS_VBIAS_SRC U3→FB5 local")

    # FB5.2 → existing GNSS_VBIAS spine at (14.0, 45.2125)
    fx, fy = pads["FB5.2"]
    ok = False
    for pts in [
        [(fx, fy), (14.0, 45.2125)],
        [(fx, fy), (fx, 45.2125), (12.05, 45.2125)],
    ]:
        if try_commit(r, pts, F, 0.18, "GNSS_VBIAS", f"FB5.2→bias {pts[-1]}"):
            CLOSED.append("GNSS_VBIAS FB5.2 stub")
            ok = True
            break
    if not ok:
        DEFERRED.append("GNSS_VBIAS FB5.2 reconnect")

    # GND pad2: short stub south into pour / toward via (17,41) staying outside dense RF
    gx, gy = pads["2"]
    ok = False
    for pts in [
        [(gx, gy), (gx, 48.5)],
        [(gx, gy), (28.0, gy), (28.0, 50.0)],
    ]:
        if try_commit(r, pts, F, 0.25, "GND", f"U3.GND {pts[-1]}"):
            CLOSED.append("U3 GND stub")
            ok = True
            break
    if not ok:
        DEFERRED.append("U3 GND")

    # COEX0 pad3 → via cluster (31.11,22) — stay x>=25.1 (outside RF box)
    cx, cy = pads["3"]
    ok = False
    for pts in [
        [(cx, cy), (31.11, cy), (31.11, 22.0)],
        [(cx, cy), (cx, 22.0), (31.11, 22.0)],
        [(cx, cy), (29.81, cy), (29.81, 22.0)],
    ]:
        if try_commit(r, pts, F, 0.18, "COEX0", f"U3.ON F {pts[1]}"):
            CLOSED.append("COEX0 U3.ON")
            ok = True
            break
    if not ok:
        # via + B
        vx, vy = 28.0, cy
        if try_commit(r, [(cx, cy), (vx, vy)], F, 0.18, "COEX0", "U3.ON to via"):
            if r.via_ok(vx, vy, "COEX0"):
                r.add_via(vx, vy, r.code_of("COEX0"), "COEX0")
                if try_commit(
                    r,
                    [(vx, vy), (vx, 18.0), (31.11, 18.0), (31.11, 22.0)],
                    B,
                    0.18,
                    "COEX0",
                    "COEX0 B north",
                ):
                    CLOSED.append("COEX0 U3.ON via B")
                    ok = True
    if not ok:
        DEFERRED.append("COEX0 U3.ON")

    # VIN pad1 → VDD_GPIO via (40.17,19.13)
    vx, vy = pads["1"]
    ok = False
    for pts in [
        [(vx, vy), (vx, 19.13), (40.17, 19.13)],
        [(vx, vy), (40.17, vy), (40.17, 19.13)],
        [(vx, vy), (30.0, vy), (30.0, 19.13), (40.17, 19.13)],
    ]:
        if try_commit(r, pts, F, 0.35, "VDD_GPIO", f"U3.VIN F {pts[1]}"):
            CLOSED.append("VDD_GPIO U3.VIN")
            ok = True
            break
    if not ok:
        site = (28.5, vy)
        if try_commit(r, [(vx, vy), site], F, 0.35, "VDD_GPIO", "U3.VIN to via"):
            if r.via_ok(*site, "VDD_GPIO"):
                r.add_via(*site, r.code_of("VDD_GPIO"), "VDD_GPIO", pwr=True)
                if try_commit(
                    r,
                    [site, (site[0], 19.13), (40.17, 19.13)],
                    B,
                    0.35,
                    "VDD_GPIO",
                    "VDD_GPIO B",
                ):
                    CLOSED.append("VDD_GPIO U3.VIN via B")
                    ok = True
    if not ok:
        DEFERRED.append("VDD_GPIO U3.VIN")


def route_class_f(board, r, pairs):
    """Surgical VIN_FILT, VIN_F, SWDCLK, nRESET, P0.02."""
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)

    def endpoints(net):
        return by.get(net, [])

    # VIN_FILT: via (55.35,13.3) <-> track (51.9,21.9)
    for p in endpoints("VIN_FILT"):
        a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
        w = 0.4
        ok = False
        for pts in [
            [a, (a[0], b[1]), b],
            [a, (b[0], a[1]), b],
            [a, (53.5, a[1]), (53.5, b[1]), b],
            [a, (55.35, 21.9), b],
        ]:
            if try_commit(r, pts, F, w, "VIN_FILT", f"VIN_FILT {pts}"):
                CLOSED.append("VIN_FILT")
                ok = True
                break
        if not ok:
            path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, "VIN_FILT")
            if path and try_commit(r, path, F, w, "VIN_FILT", "VIN_FILT wp"):
                CLOSED.append("VIN_FILT")
            else:
                DEFERRED.append("VIN_FILT")

    for p in endpoints("VIN_F"):
        a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
        w = 0.4
        ok = False
        for pts in [
            [a, (a[0], b[1]), b],
            [a, (b[0], a[1]), b],
            [a, (48.0, 19.06), (71.2, 19.06)],
            [a, (60.0, a[1]), (60.0, b[1]), b],
        ]:
            if try_commit(r, pts, F, w, "VIN_F", f"VIN_F {pts[1]}"):
                CLOSED.append("VIN_F")
                ok = True
                break
        if not ok:
            path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, "VIN_F")
            if path and try_commit(r, path, F, w, "VIN_F", "VIN_F wp"):
                CLOSED.append("VIN_F")
            else:
                DEFERRED.append("VIN_F")

    for p in endpoints("SWDCLK"):
        a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
        w = 0.18
        # prefer B under courtyard: via near U1 pad33 (37.75,26.75) and J8 (51.95,4.73)
        ok = False
        # F direct jogs
        for pts in [
            [a, (a[0], 10.0), (b[0], 10.0), b],
            [a, (45.0, a[1]), (45.0, b[1]), b],
        ]:
            if try_commit(r, pts, F, w, "SWDCLK", f"SWDCLK F {pts[1]}"):
                CLOSED.append("SWDCLK")
                ok = True
                break
        if not ok:
            # via at (37.75, 24.5) and (51.95, 8.0)
            v1, v2 = (37.75, 24.8), (51.95, 8.0)
            if try_commit(r, [b, v1], F, w, "SWDCLK", "SWDCLK U1→via") and r.via_ok(
                *v1, "SWDCLK"
            ):
                r.add_via(*v1, r.code_of("SWDCLK"), "SWDCLK")
                if try_commit(r, [a, v2], F, w, "SWDCLK", "SWDCLK J8→via") and r.via_ok(
                    *v2, "SWDCLK"
                ):
                    r.add_via(*v2, r.code_of("SWDCLK"), "SWDCLK")
                    if try_commit(
                        r, [v1, (v1[0], v2[1]), v2], B, w, "SWDCLK", "SWDCLK B"
                    ):
                        CLOSED.append("SWDCLK")
                        ok = True
        if not ok:
            path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, "SWDCLK")
            if path and try_commit(r, path, F, w, "SWDCLK", "SWDCLK wp"):
                CLOSED.append("SWDCLK")
            else:
                DEFERRED.append("SWDCLK")

    for p in endpoints("nRESET"):
        a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
        w = 0.18
        # (101.68,26) <-> (52.22,10.8) — use B with existing vias
        ok = False
        path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, "nRESET")
        if path and try_commit(r, path, F, w, "nRESET", "nRESET F wp"):
            CLOSED.append("nRESET")
            ok = True
        if not ok:
            path = waypoint_route(r, a[0], a[1], b[0], b[1], B, w, "nRESET")
            if path and try_commit(r, path, B, w, "nRESET", "nRESET B wp"):
                CLOSED.append("nRESET")
                ok = True
        if not ok:
            DEFERRED.append("nRESET")

    # P0.02 via already sized; try close open
    for p in endpoints("P0.02"):
        a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
        w = 0.18
        path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, "P0.02")
        if path and try_commit(r, path, F, w, "P0.02", "P0.02 F"):
            CLOSED.append("P0.02")
        else:
            path = waypoint_route(r, a[0], a[1], b[0], b[1], B, w, "P0.02")
            if path and try_commit(r, path, B, w, "P0.02", "P0.02 B"):
                CLOSED.append("P0.02")
            else:
                DEFERRED.append("P0.02")


def stub_terminate_class_c(board, r, pairs):
    """≤2 mm same-net stub from DNP cap RF-side pad toward trunk; GND pad via pour."""
    targets = {
        "ANT_FIT": "C22",
        "AUX": "C23",
        "AUX_FIT": "C24",
        "ANT": "C21",
        "GPS": "C31",
        "GNSS_ANT": "C32",
    }
    # Also handle by unconnected pairs for ANT_FIT/AUX/AUX_FIT
    for net in ["ANT_FIT", "AUX", "AUX_FIT", "ANT", "GPS", "GNSS_ANT"]:
        ref = targets.get(net)
        fp = board.FindFootprintByReference(ref) if ref else None
        if not fp:
            continue
        # find RF-side pad (non-GND)
        rf_pad = None
        gnd_pad = None
        for p in fp.Pads():
            if p.GetNetname() == "GND":
                gnd_pad = p
            elif p.GetNetname() == net or p.GetNetname() in (
                "ANT_FIT",
                "AUX",
                "AUX_FIT",
                "ANT",
                "GPS",
                "GNSS_ANT",
            ):
                rf_pad = p
        if rf_pad is None:
            # pick non-gnd
            for p in fp.Pads():
                if p.GetNetname() != "GND":
                    rf_pad = p
                    break
        if rf_pad is None:
            DEFERRED.append(f"ClassC {ref} no RF pad")
            continue
        netname = rf_pad.GetNetname()
        if not netname:
            DEFERRED.append(f"ClassC {ref} empty net")
            continue
        x, y = pcbnew.ToMM(rf_pad.GetPosition().x), pcbnew.ToMM(rf_pad.GetPosition().y)
        # Find nearest same-net track endpoint within 8 mm
        best = None
        best_d = 1e9
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                continue
            if t.GetNetname() != netname:
                continue
            if t.GetLayer() != F:
                continue
            for px, py in [
                (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)),
                (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)),
            ]:
                d = hypot(x, y, px, py)
                if 0.15 < d < best_d:
                    best_d = d
                    best = (px, py)
        if best is None:
            DEFERRED.append(f"ClassC {ref}/{netname} no nearby trunk")
            continue
        # stub ≤2 mm toward trunk
        dx, dy = best[0] - x, best[1] - y
        dist = hypot(0, 0, dx, dy)
        if dist < 0.15:
            CLOSED.append(f"ClassC {ref} already close")
            continue
        scale = min(2.0, dist) / dist
        tx, ty = x + dx * scale, y + dy * scale
        # if full distance ≤2mm, connect fully
        if dist <= 2.0:
            pts = [(x, y), best]
        else:
            pts = [(x, y), (tx, ty)]
        if try_commit(r, pts, F, 0.2, netname, f"ClassC stub {ref}"):
            CLOSED.append(f"ClassC {ref} {netname} stub")
        else:
            DEFERRED.append(f"ClassC {ref} stub blocked")
        # GND pad: short stub into pour (0.3 mm)
        if gnd_pad is not None:
            gx, gy = pcbnew.ToMM(gnd_pad.GetPosition().x), pcbnew.ToMM(
                gnd_pad.GetPosition().y
            )
            # tiny stub - zone should cover; skip if risky
            _ = (gx, gy)


def try_sim_and_more(board, r, pairs):
    """SIM private exits + a few easy GPIO if safe."""
    by = defaultdict(list)
    for p in pairs:
        by[p["net"]].append(p)
    for net in ["SIM_CLK", "SIM_RST", "SIM_IO", "SIM_1V8"]:
        for p in by.get(net, []):
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            w = 0.18
            # Prefer B.Cu, stay out of RF box
            path = waypoint_route(r, a[0], a[1], b[0], b[1], B, w, net)
            if path and try_commit(r, path, B, w, net, f"{net} B"):
                CLOSED.append(net)
            else:
                path = waypoint_route(r, a[0], a[1], b[0], b[1], F, w, net)
                if path and try_commit(r, path, F, w, net, f"{net} F"):
                    CLOSED.append(net)
                else:
                    DEFERRED.append(net)


def main():
    global CLOSED, DEFERRED, PLACED
    shutil.copy2(BOARD, os.path.join(SNAP_DIR, "start.kicad_pcb"))
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    pairs0, n0, counts0, _ = run_drc()
    print(
        f"BASELINE unconn={n0} shorts={counts0.get('shorting_items',0)} "
        f"clr={counts0.get('clearance',0)} dangling={counts0.get('via_dangling',0)}",
        flush=True,
    )
    ceiling = n0 + 8  # U3 may add opens until routed
    last = os.path.join(SNAP_DIR, "start.kicad_pcb")

    # A) Place U3 + FB5
    print("=== A place U3/FB5 ===", flush=True)
    u3, fb5, pads = place_u3_and_fb5(board, r)
    pcbnew.SaveBoard(BOARD, board)
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    # refresh pads after reload
    u3 = board.FindFootprintByReference("U3")
    fb5 = board.FindFootprintByReference("FB5")
    pads = {}
    for p in u3.Pads():
        pads[p.GetNumber()] = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
    for p in fb5.Pads():
        pads[f"FB5.{p.GetNumber()}"] = (
            pcbnew.ToMM(p.GetPosition().x),
            pcbnew.ToMM(p.GetPosition().y),
        )

    route_u3_local(board, r, pads)
    res = check(board, r, "u3-fb5", last, ceiling)
    if res[0] is None:
        print("U3/FB5 step reverted — aborting further copper", flush=True)
        return
    pairs, n, counts, _ = res
    last = os.path.join(SNAP_DIR, "after-u3-fb5.kicad_pcb")
    ceiling = n  # only allow decrease or equal after this
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()

    print("=== C Class F surgical ===", flush=True)
    route_class_f(board, r, pairs)
    res = check(board, r, "class-f", last, ceiling)
    if res[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n, counts, _ = run_drc()
    else:
        pairs, n, counts, _ = res
        last = os.path.join(SNAP_DIR, "after-class-f.kicad_pcb")
        ceiling = n
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    print("=== I Class C stubs ===", flush=True)
    stub_terminate_class_c(board, r, pairs)
    res = check(board, r, "class-c", last, ceiling)
    if res[0] is None:
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()
        pairs, n, counts, _ = run_drc()
    else:
        pairs, n, counts, _ = res
        last = os.path.join(SNAP_DIR, "after-class-c.kicad_pcb")
        ceiling = n
        board = pcbnew.LoadBoard(BOARD)
        r = Final(board)
        r.collect()

    print("=== D SIM ===", flush=True)
    try_sim_and_more(board, r, pairs)
    res = check(board, r, "sim", last, ceiling)
    if res[0] is None:
        pairs, n, counts, _ = run_drc()
    else:
        pairs, n, counts, _ = res

    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)

    # summary json
    summary = {
        "placed": PLACED,
        "closed": CLOSED,
        "deferred": DEFERRED,
        "unconn_after_steps": n,
        "counts": dict(counts),
    }
    open(f"{ROOT}/reports/PASS30_SUMMARY.json", "w").write(json.dumps(summary, indent=2))
    print("SUMMARY", json.dumps(summary, indent=2), flush=True)
    print("class counts", class_counts(pairs), flush=True)


if __name__ == "__main__":
    main()
