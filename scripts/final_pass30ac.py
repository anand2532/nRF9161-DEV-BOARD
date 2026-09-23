#!/usr/bin/env python3
"""Pass30ac — Package A_SE_duals EXECUTE (J16+J9+J17) atomic place + full reattach.

Preferred: J16(105.46,8) J9(113.46,8) J17(105.46,26) — west −2.54
Alt once if preferred dirty:
         J16(108.0,10.54) J9(116.0,10.54) J17(108.0,24.0)
If Alt also dirty → full revert to pass30z keep, STOP. No further landings.
J12 DO NOT MOVE. SE column (J13/J10/J11) FROZEN. No U1. No Gerbers. No B''.
Protect Stage A, P0.15 west, RF/U3, pass30r/u, pass30z Class C (C22/C23/C24).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30ac-package-a"
REPORTS = f"{ROOT}/reports"
PRE = f"{SNAP}/pre-edit.kicad_pcb"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18

# Package A preferred / alt (excl J12)
PREF = {"J16": (105.46, 8.0), "J9": (113.46, 8.0), "J17": (105.46, 26.0)}
ALT = {"J16": (108.0, 10.54), "J9": (116.0, 10.54), "J17": (108.0, 24.0)}
START = {"J16": (108.0, 8.0), "J9": (116.0, 8.0), "J17": (108.0, 26.0)}
FROZEN = {
    "J12": (6.0, 76.0),
    "J13": (64.0, 76.0),
    "J10": (116.0, 28.0),
    "J11": (116.0, 46.0),
    "U1": (36.0, 32.0),
}

# pass30x Package A full reattach net lists (J16/J9/J17 only)
REATTACH = {
    "J16": ["P0.10", "P0.11", "P0.12", "P0.09", "VDD_GPIO", "GND"],
    "J9": ["P0.06", "P0.07", "P0.05", "P0.04", "VDD_GPIO", "GND"],
    "J17": ["P0.17", "P0.18", "VDD_GPIO", "GND"],
}

WATCH = [
    "P0.04", "P0.05", "P0.06", "P0.07", "P0.09", "P0.10", "P0.11", "P0.12",
    "P0.15", "P0.17", "P0.18", "P0.19", "P0.22", "VDD_GPIO", "VDD_nRF", "VDD2",
    "GND", "COEX0", "COEX2", "ENABLE", "ANT_FIT", "AUX", "AUX_FIT",
]

CLASS_C_XY = {
    "C22": (17.5, 31.75),
    "C23": (24.8, 34.0),
    "C24": (15.0, 31.8),
}
CLASS_C_GND_VIA = {
    "C22": (17.5, 32.23),
    "C23": (25.98, 34.0),
    "C24": (16.18, 31.8),
}
BASELINE_UNCONNECTED = 64


def mm(v):
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def save(board, path=BOARD):
    pcbnew.SaveBoard(path, board)


def load(path=BOARD):
    return pcbnew.LoadBoard(path)


def add_trk(board, net, x1, y1, x2, y2, w, layer):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


def run_drc(out_path):
    tmp = "/tmp/nrf30ac_drc.json"
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", tmp, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, out_path)
    data = json.load(open(out_path))
    vc = Counter(v["type"] for v in data.get("violations", []))
    return data, {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "copper_edge_clearance": vc.get("copper_edge_clearance", 0),
        "silk_over_copper": vc.get("silk_over_copper", 0),
        "silk_overlap": vc.get("silk_overlap", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "via_dangling": vc.get("via_dangling", 0),
        "track_dangling": vc.get("track_dangling", 0),
    }


def nets_of(data):
    c = Counter()
    for u in data.get("unconnected_items", []):
        ns = set()
        for it in u.get("items", []):
            for m in re.findall(r"\[([^\]]+)\]", it.get("description", "")):
                if m not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                    ns.add(m)
        for n in ns:
            c[n] += 1
    return dict(c)


def clean(s):
    return s["shorting_items"] == 0 and s["clearance"] == 0 and s["tracks_crossing"] == 0


def colliding(data, limit=30):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in (
            "shorting_items",
            "clearance",
            "tracks_crossing",
            "copper_edge_clearance",
            "hole_clearance",
        ):
            out.append(
                {
                    "type": v["type"],
                    "description": v.get("description", "")[:220],
                    "items": [
                        {
                            "description": it.get("description", "")[:160],
                            "pos": it.get("pos"),
                        }
                        for it in v.get("items", [])[:3]
                    ],
                }
            )
        if len(out) >= limit:
            break
    return out


def zone_fill():
    open(f"{SNAP}/zone_fill_once.py", "w").write(
        "import pcbnew\n"
        f"b=pcbnew.LoadBoard({BOARD!r})\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        f"pcbnew.SaveBoard({BOARD!r}, b)\n"
        "print('zone-fill saved', flush=True)\n"
    )
    subprocess.check_call([sys.executable, f"{SNAP}/zone_fill_once.py"])


def p015_west(board):
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            continue
        if min(mm(t.GetStart().x), mm(t.GetEnd().x)) < 45:
            n += 1
    return n


def stage_a_ok(board):
    ok = {"VDD_nRF_via_north": False, "VDD2_vias": 0}
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if t.GetNetname() == "VDD_nRF" and abs(x - 69.3) < 0.2 and abs(y - 31.5) < 0.2:
            ok["VDD_nRF_via_north"] = True
        if t.GetNetname() == "VDD2" and abs(x - 58) < 0.2 and (
            abs(y - 29.55) < 0.2 or abs(y - 30.95) < 0.2
        ):
            ok["VDD2_vias"] += 1
    ok["VDD2_present"] = ok["VDD2_vias"] >= 2
    return ok


def fp_xy(board, ref):
    fp = board.FindFootprintByReference(ref)
    return (round(mm(fp.GetPosition().x), 3), round(mm(fp.GetPosition().y), 3))


def pad_centers(board, ref):
    fp = board.FindFootprintByReference(ref)
    out = {}
    for p in fp.Pads():
        n = p.GetNumber()
        if not n:
            continue
        out[n] = (
            mm(p.GetPosition().x),
            mm(p.GetPosition().y),
            p.GetNetname(),
        )
    return out


def near(a, b, tol=0.30):
    return abs(a - b) < tol


def class_c_protect(board):
    result = {"fps_ok": True, "gnd_vias": {}, "stub_tracks": {}, "ok": True, "reasons": []}
    for ref, (ex, ey) in CLASS_C_XY.items():
        live = fp_xy(board, ref)
        if abs(live[0] - ex) > 0.05 or abs(live[1] - ey) > 0.05:
            result["fps_ok"] = False
            result["ok"] = False
            result["reasons"].append(f"{ref} moved to {live}, expected {(ex, ey)}")
    for ref, (vx, vy) in CLASS_C_GND_VIA.items():
        found = False
        for t in list(board.GetTracks()):
            if t.Type() != pcbnew.PCB_VIA_T:
                continue
            if t.GetNetname() != "GND":
                continue
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if abs(x - vx) < 0.15 and abs(y - vy) < 0.15:
                found = True
                break
        result["gnd_vias"][ref] = found
        if not found:
            result["ok"] = False
            result["reasons"].append(f"missing GND via near {ref} @{(vx, vy)}")
    net_map = {"C22": "ANT_FIT", "C23": "AUX", "C24": "AUX_FIT"}
    for ref, net in net_map.items():
        pads = pad_centers(board, ref)
        px = py = None
        if "1" in pads:
            px, py = pads["1"][0], pads["1"][1]
        elif pads:
            px, py = next(iter(pads.values()))[0], next(iter(pads.values()))[1]
        ntrk = 0
        if px is not None:
            for t in list(board.GetTracks()):
                if isinstance(t, pcbnew.PCB_VIA):
                    continue
                if t.GetNetname() != net:
                    continue
                sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
                ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
                if (near(sx, px, 0.5) and near(sy, py, 0.5)) or (
                    near(ex, px, 0.5) and near(ey, py, 0.5)
                ):
                    ntrk += 1
        result["stub_tracks"][ref] = ntrk
        if ntrk < 1:
            result["ok"] = False
            result["reasons"].append(f"{ref} missing {net} stub near pad")
    return result


def protect_ok(board, west0):
    stage = stage_a_ok(board)
    west = p015_west(board)
    cc = class_c_protect(board)
    reasons = []
    if not stage["VDD_nRF_via_north"] or not stage["VDD2_present"]:
        reasons.append(f"stage_a={stage}")
    if west < west0:
        reasons.append(f"p015_west {west}<{west0}")
    for ref, exp in FROZEN.items():
        live = fp_xy(board, ref)
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            reasons.append(f"{ref} moved {live} (frozen at {exp})")
    if not cc["ok"]:
        reasons.extend(cc["reasons"])
    return {
        "stage_a": stage,
        "p015_west": west,
        "p015_west_before": west0,
        "class_c": cc,
        "frozen_xy": {ref: list(fp_xy(board, ref)) for ref in FROZEN},
        "ok": len(reasons) == 0,
        "reasons": reasons,
    }


def collect_pad_endpoint_hits(board, refs, tol=0.35):
    pads_by_ref = {ref: pad_centers(board, ref) for ref in refs}
    hits = []
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net = t.GetNetname()
        sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
        ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
        w = mm(t.GetWidth())
        layer = t.GetLayer()
        for ref, pads in pads_by_ref.items():
            for pnum, (px, py, pnet) in pads.items():
                if pnet != net:
                    continue
                if near(sx, px, tol) and near(sy, py, tol):
                    hits.append(
                        {
                            "track": t,
                            "end": "start",
                            "ref": ref,
                            "pad": pnum,
                            "net": net,
                            "layer": layer,
                            "w": w,
                            "pad_xy": (px, py),
                            "other": (ex, ey),
                        }
                    )
                if near(ex, px, tol) and near(ey, py, tol):
                    hits.append(
                        {
                            "track": t,
                            "end": "end",
                            "ref": ref,
                            "pad": pnum,
                            "net": net,
                            "layer": layer,
                            "w": w,
                            "pad_xy": (px, py),
                            "other": (sx, sy),
                        }
                    )
    return hits


def rip_pad_stubs(board, refs, tol=0.35):
    hits = collect_pad_endpoint_hits(board, refs, tol=tol)
    by_track = {}
    for h in hits:
        by_track.setdefault(id(h["track"]), {"track": h["track"], "hits": []})["hits"].append(h)
    records = []
    for pack in by_track.values():
        t = pack["track"]
        net = t.GetNetname()
        layer = t.GetLayer()
        w = mm(t.GetWidth())
        sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
        ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
        records.append(
            {
                "net": net,
                "layer": layer,
                "w": w,
                "seg": (sx, sy, ex, ey),
                "hits": [
                    {
                        "ref": h["ref"],
                        "pad": h["pad"],
                        "end": h["end"],
                        "pad_xy": h["pad_xy"],
                        "other": h["other"],
                    }
                    for h in pack["hits"]
                ],
            }
        )
        board.Delete(t)
    return records


def move_fps(board, targets):
    for ref, (x, y) in targets.items():
        if ref == "J12":
            raise RuntimeError("J12 must not be moved")
        fp = board.FindFootprintByReference(ref)
        fp.SetPosition(xy(x, y))


def reattach_after_rip(board, records, old_pads, new_pads):
    added = 0
    for rec in records:
        net, layer, w = rec["net"], rec["layer"], rec["w"]
        sx, sy, ex, ey = rec["seg"]
        start_hit = None
        end_hit = None
        for h in rec["hits"]:
            if h["end"] == "start":
                start_hit = h
            if h["end"] == "end":
                end_hit = h

        def new_pad_xy(h):
            ref, pad = h["ref"], h["pad"]
            return new_pads[ref][pad][0], new_pads[ref][pad][1]

        if start_hit and end_hit:
            x1, y1 = new_pad_xy(start_hit)
            x2, y2 = new_pad_xy(end_hit)
            if abs(x1 - x2) > 1e-9 and abs(y1 - y2) > 1e-9:
                add_trk(board, net, x1, y1, x2, y1, w, layer)
                add_trk(board, net, x2, y1, x2, y2, w, layer)
                added += 2
            else:
                add_trk(board, net, x1, y1, x2, y2, w, layer)
                added += 1
            continue

        if start_hit and not end_hit:
            nx, ny = new_pad_xy(start_hit)
            ox, oy = ex, ey
            if near(nx, ox) or near(ny, oy):
                add_trk(board, net, nx, ny, ox, oy, w, layer)
                added += 1
            else:
                add_trk(board, net, nx, ny, nx, oy, w, layer)
                add_trk(board, net, nx, oy, ox, oy, w, layer)
                added += 2
            continue

        if end_hit and not start_hit:
            nx, ny = new_pad_xy(end_hit)
            ox, oy = sx, sy
            if near(nx, ox) or near(ny, oy):
                add_trk(board, net, nx, ny, ox, oy, w, layer)
                added += 1
            else:
                add_trk(board, net, nx, ny, nx, oy, w, layer)
                add_trk(board, net, nx, oy, ox, oy, w, layer)
                added += 2
            continue

        add_trk(board, net, sx, sy, ex, ey, w, layer)
        added += 1
    return added


def also_shift_column_bus(board, old_x, new_x, y_lo, y_hi, nets, tol=0.35):
    """Shift vertical-column endpoints at old_x within y band (west package)."""
    if abs(old_x - new_x) < 0.01:
        return 0
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() not in nets:
            continue
        sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
        ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
        nsx, nsy, nex, ney = sx, sy, ex, ey
        ch = False
        if near(sx, old_x, tol) and y_lo <= sy <= y_hi:
            nsx = new_x
            ch = True
        if near(ex, old_x, tol) and y_lo <= ey <= y_hi:
            nex = new_x
            ch = True
        if ch:
            t.SetStart(xy(nsx, nsy))
            t.SetEnd(xy(nex, ney))
            n += 1
    return n


def also_shift_row_bus(board, old_y, new_y, x_lo, x_hi, nets, tol=0.35):
    """Shift horizontal-row endpoints at old_y within x band (alt south/north)."""
    if abs(old_y - new_y) < 0.01:
        return 0
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() not in nets:
            continue
        sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
        ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
        nsx, nsy, nex, ney = sx, sy, ex, ey
        ch = False
        if near(sy, old_y, tol) and x_lo <= sx <= x_hi:
            nsy = new_y
            ch = True
        if near(ey, old_y, tol) and x_lo <= ex <= x_hi:
            ney = new_y
            ch = True
        if ch:
            t.SetStart(xy(nsx, nsy))
            t.SetEnd(xy(nex, ney))
            n += 1
    return n


def apply_package(targets, label):
    """Atomic: rip pad stubs → move FPs → reattach → column/row bus fix → zone fill."""
    board = load()
    old_pads = {ref: pad_centers(board, ref) for ref in targets}

    records = rip_pad_stubs(board, list(targets.keys()), tol=0.35)
    save(board)
    board = load()
    move_fps(board, targets)
    save(board)
    board = load()
    new_pads = {ref: pad_centers(board, ref) for ref in targets}
    added = reattach_after_rip(board, records, old_pads, new_pads)

    # Combined nets for bus shifts
    all_nets = set()
    for nets in REATTACH.values():
        all_nets.update(nets)

    nbus = 0
    # J16/J17 share start x=108 — shift column if west move
    old_x_j16 = START["J16"][0]
    new_x_j16 = targets["J16"][0]
    nbus += also_shift_column_bus(
        board, old_x_j16, new_x_j16, 6.0, 36.0, all_nets, tol=0.40
    )
    # J9 column x=116
    old_x_j9 = START["J9"][0]
    new_x_j9 = targets["J9"][0]
    nbus += also_shift_column_bus(
        board, old_x_j9, new_x_j9, 6.0, 24.0, all_nets, tol=0.40
    )

    # Alt Y shifts: shift pad-row buses for each header
    nrow = 0
    for ref in targets:
        old_y = START[ref][1]
        new_y = targets[ref][1]
        dy = new_y - old_y
        if abs(dy) < 0.01:
            continue
        # Shift any leftover stub endpoints that still sit on old pad Y of this ref
        for pnum, (px, py, pnet) in old_pads[ref].items():
            if pnet not in all_nets:
                continue
            # pad y shifts by dy; shift tracks still at old pad y near old pad x
            old_pad_y = py
            new_pad_y = py + dy
            old_pad_x = px
            new_pad_x = new_pads[ref][pnum][0]
            for t in list(board.GetTracks()):
                if isinstance(t, pcbnew.PCB_VIA):
                    continue
                if t.GetNetname() != pnet:
                    continue
                sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
                ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
                nsx, nsy, nex, ney = sx, sy, ex, ey
                ch = False
                if near(sx, old_pad_x, 0.40) and near(sy, old_pad_y, 0.40):
                    nsx, nsy = new_pad_x, new_pad_y
                    ch = True
                if near(ex, old_pad_x, 0.40) and near(ey, old_pad_y, 0.40):
                    nex, ney = new_pad_x, new_pad_y
                    ch = True
                if ch:
                    t.SetStart(xy(nsx, nsy))
                    t.SetEnd(xy(nex, ney))
                    nrow += 1

        # Also shift horizontal tracks at this ref's VDD pad Y band near header X
        ox = START[ref][0]
        nx = targets[ref][0]
        # VDD pad y for J16/J9 pad5 = old_y+10.16; J17 pad3 = old_y+5.08
        # Use also_shift_row around old footprint origin and pad rows within ±12 mm
        for dy_off in [0.0, 2.54, 5.08, 7.62, 10.16, 12.70]:
            oy = old_y + dy_off
            ny = new_y + dy_off
            nrow += also_shift_row_bus(
                board, oy, ny, ox - 2.0, ox + 10.0, all_nets, tol=0.25
            )
            # if X also changed (shouldn't for alt), ignore — alt keeps X

    # Prefer: also preserve VDD_GPIO jog @x≈111 between J16.5 and J17.3 —
    # pad reattach already extends stubs to new pads; jog vertical stays at x111.

    save(board)
    zone_fill()
    return {
        "label": label,
        "targets": {k: list(v) for k, v in targets.items()},
        "ripped": len(records),
        "reattached_segs": added,
        "bus_shifted": nbus,
        "row_shifted": nrow,
        "final_xy": {ref: list(fp_xy(load(), ref)) for ref in targets},
        "new_pads_sample": {
            "J16.1": list(new_pads["J16"]["1"][:2]),
            "J16.5": list(new_pads["J16"]["5"][:2]),
            "J9.1": list(new_pads["J9"]["1"][:2]),
            "J9.5": list(new_pads["J9"]["5"][:2]),
            "J17.1": list(new_pads["J17"]["1"][:2]),
            "J17.3": list(new_pads["J17"]["3"][:2]),
        },
    }


def restore_pre():
    shutil.copy2(PRE, BOARD)


def accept_attempt(info, mid, west0, before_unc):
    if not info.get("clean"):
        return False, "dirty_drc"
    if mid["unconnected_items"] > BASELINE_UNCONNECTED:
        return False, f"unconnected_spike_{mid['unconnected_items']}"
    prot = info.get("protect") or {}
    if not prot.get("ok"):
        return False, "protect_fail:" + ",".join(prot.get("reasons", [])[:4])
    return True, "ok"


def main():
    os.makedirs(SNAP, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    assert os.path.isfile(PRE), "missing pre-edit backup"

    summary = {
        "pass": "layout-pass30ac",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "scope": "Package A_SE_duals EXECUTE — J16+J9+J17 atomic place + full reattach (excl J12)",
        "preferred": {k: list(v) for k, v in PREF.items()},
        "alt": {k: list(v) for k, v in ALT.items()},
        "j12_policy": "DO_NOT_MOVE",
        "no_gerbers": True,
        "packages_skipped": ["B", "B''", "C", "D", "J12"],
        "se_column_frozen": True,
        "no_u1_move": True,
        "baseline": "pass30z KEEP after pass30ab full revert; unconnected=64",
        "backup": PRE,
        "live_xy_before": {},
        "landing_kept": None,
        "phase": "INIT",
    }

    board = load()
    check_refs = ["J16", "J9", "J17", "J12", "J13", "J10", "J11", "U1", "C22", "C23", "C24"]
    for ref in check_refs:
        summary["live_xy_before"][ref] = list(fp_xy(board, ref))
    for ref, exp in START.items():
        live = tuple(summary["live_xy_before"][ref])
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            summary["phase"] = "ABORT_UNEXPECTED_START_XY"
            summary["error"] = f"{ref} live {live} != expected {exp}"
            json.dump(summary, open(f"{REPORTS}/PASS30AC_SUMMARY.json", "w"), indent=2)
            print("ABORT", summary["error"])
            return
    for ref, exp in FROZEN.items():
        live = tuple(summary["live_xy_before"][ref])
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            summary["phase"] = "ABORT_UNEXPECTED_FROZEN_XY"
            summary["error"] = f"{ref} live {live} != frozen expected {exp}"
            json.dump(summary, open(f"{REPORTS}/PASS30AC_SUMMARY.json", "w"), indent=2)
            print("ABORT", summary["error"])
            return

    west0 = p015_west(board)
    stage0 = stage_a_ok(board)
    cc0 = class_c_protect(board)
    summary["p015_west_before"] = west0
    summary["stage_a_before"] = stage0
    summary["class_c_before"] = cc0
    if not cc0["ok"]:
        summary["phase"] = "ABORT_CLASS_C_MISSING_AT_START"
        summary["error"] = cc0["reasons"]
        json.dump(summary, open(f"{REPORTS}/PASS30AC_SUMMARY.json", "w"), indent=2)
        print("ABORT Class C missing at start", cc0)
        return

    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30AC_BEFORE.json")
    summary["before"] = before
    summary["before_nets_watch"] = {n: nets_of(before_data).get(n, 0) for n in WATCH}
    print("BEFORE", before, flush=True)

    attempts = []
    kept = None

    # --- Attempt 1: preferred ---
    restore_pre()
    info = apply_package(PREF, "preferred_west_m2.54")
    mid_data, mid = run_drc(f"{REPORTS}/DRC_PASS30AC_MID_PREF.json")
    info["mid"] = mid
    info["mid_nets_watch"] = {n: nets_of(mid_data).get(n, 0) for n in WATCH}
    info["collide"] = colliding(mid_data)
    info["clean"] = clean(mid)
    info["protect"] = protect_ok(load(), west0)
    attempts.append(info)
    print("MID_PREF", mid, "clean", info["clean"], "protect", info["protect"]["ok"], flush=True)
    shutil.copy2(BOARD, f"{SNAP}/after-pref.kicad_pcb")

    ok, reason = accept_attempt(info, mid, west0, before["unconnected_items"])
    if ok:
        kept = "preferred"
        summary["landing_kept"] = "preferred"
    else:
        info["reject_reason"] = reason
        print("PREF rejected:", reason, "→ try ALT once", flush=True)
        restore_pre()
        info2 = apply_package(ALT, "alt_south_north_y_deltas")
        mid2_data, mid2 = run_drc(f"{REPORTS}/DRC_PASS30AC_MID_ALT.json")
        info2["mid"] = mid2
        info2["mid_nets_watch"] = {n: nets_of(mid2_data).get(n, 0) for n in WATCH}
        info2["collide"] = colliding(mid2_data)
        info2["clean"] = clean(mid2)
        info2["protect"] = protect_ok(load(), west0)
        attempts.append(info2)
        print("MID_ALT", mid2, "clean", info2["clean"], "protect", info2["protect"]["ok"], flush=True)
        shutil.copy2(BOARD, f"{SNAP}/after-alt.kicad_pcb")

        ok2, reason2 = accept_attempt(info2, mid2, west0, before["unconnected_items"])
        if ok2:
            kept = "alt"
            summary["landing_kept"] = "alt"
        else:
            info2["reject_reason"] = reason2
            restore_pre()
            summary["landing_kept"] = None
            summary["stop_reason"] = (
                f"preferred dirty/reject ({reason}); Alt also dirty/reject ({reason2}) "
                "— full revert to pass30z keep; STOP (no further landings)"
            )

    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30AC_AFTER.json")
    board = load()
    summary["attempts"] = []
    for a in attempts:
        row = {k: v for k, v in a.items() if k != "collide"}
        row["collide"] = a.get("collide", [])[:12]
        summary["attempts"].append(row)

    summary["after"] = after
    summary["after_nets_watch"] = {n: nets_of(after_data).get(n, 0) for n in WATCH}
    summary["final_xy"] = {ref: list(fp_xy(board, ref)) for ref in check_refs}
    summary["protect_after"] = protect_ok(board, west0)
    summary["kept"] = kept
    summary["reverted"] = kept is None
    summary["unconnected_delta"] = after["unconnected_items"] - before["unconnected_items"]

    if kept:
        summary["phase"] = "COMPLETE_KEEP"
        summary["decision"] = "KEEP"
        summary["success_gate"] = (
            f"OK clean DRC + unconnected {before['unconnected_items']}→{after['unconnected_items']} "
            f"≤{BASELINE_UNCONNECTED}; landing={summary['landing_kept']}"
        )
    else:
        summary["phase"] = "COMPLETE_REVERTED"
        summary["decision"] = "REVERT"
        summary["success_gate"] = (
            f"BLOCKED — reverted to pass30z keep; unconnected "
            f"{before['unconnected_items']}→{after['unconnected_items']}; "
            f"shorting/clearance/crossing="
            f"{after['shorting_items']}/{after['clearance']}/{after['tracks_crossing']}"
        )

    json.dump(summary, open(f"{REPORTS}/PASS30AC_SUMMARY.json", "w"), indent=2)

    lines = [
        "# PASS30AC_SUMMARY — Package A_SE_duals (excl J12)",
        "",
        f"**Timestamp:** {summary['timestamp_ist']}",
        f"**Decision:** **{summary['decision']}**",
        f"**Phase:** {summary['phase']}",
        f"**Landing kept:** {summary['landing_kept']}",
        f"**Final XY:** J16={summary['final_xy']['J16']} J9={summary['final_xy']['J9']} "
        f"J17={summary['final_xy']['J17']} J12={summary['final_xy']['J12']} "
        f"(frozen) J13={summary['final_xy']['J13']} J10={summary['final_xy']['J10']} "
        f"J11={summary['final_xy']['J11']} U1={summary['final_xy']['U1']}",
        f"**Class C XY:** C22={summary['final_xy']['C22']} C23={summary['final_xy']['C23']} "
        f"C24={summary['final_xy']['C24']}",
        "",
        "## DRC",
        "",
        "| | unconnected | shorting | clearance | crossing |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| Before | {before['unconnected_items']} | {before['shorting_items']} | {before['clearance']} | {before['tracks_crossing']} |",
        f"| After | {after['unconnected_items']} | {after['shorting_items']} | {after['clearance']} | {after['tracks_crossing']} |",
        "",
        f"**Delta unconnected:** {summary['unconnected_delta']}",
        f"**Gate:** {summary['success_gate']}",
        "",
        "## Attempts",
        "",
    ]
    for a in summary["attempts"]:
        lines.append(f"### {a['label']}")
        lines.append(f"- targets: {a['targets']}")
        lines.append(f"- mid: {a['mid']}")
        lines.append(f"- clean: {a.get('clean')} protect: {a.get('protect', {}).get('ok')}")
        lines.append(
            f"- ripped={a['ripped']} reattached={a['reattached_segs']} "
            f"bus={a['bus_shifted']} row={a.get('row_shifted', 0)}"
        )
        if a.get("reject_reason"):
            lines.append(f"- reject: {a['reject_reason']}")
        if a.get("collide"):
            lines.append(f"- collide head: {json.dumps(a['collide'][:4])[:800]}")
        lines.append("")

    lines.append("## Protect checklist (after)")
    lines.append("")
    lines.append("```")
    lines.append(json.dumps(summary["protect_after"], indent=2)[:2500])
    lines.append("```")
    lines.append("")
    lines.append("## Policy")
    lines.append("")
    lines.append("- J12: DO NOT MOVE (honored)")
    lines.append("- SE column J13/J10/J11: FROZEN (honored)")
    lines.append("- No B'' execute / No Gerbers / No U1 move")
    lines.append("- Class C C22/C23/C24 protected")
    lines.append("")
    if summary.get("stop_reason"):
        lines.append(f"**Stop:** {summary['stop_reason']}")
        lines.append("")

    open(f"{REPORTS}/PASS30AC_SUMMARY.md", "w").write("\n".join(lines) + "\n")
    print("DONE", summary["decision"], "landing", summary["landing_kept"], flush=True)
    print("AFTER", after, flush=True)


if __name__ == "__main__":
    main()
