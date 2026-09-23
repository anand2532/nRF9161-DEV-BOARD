#!/usr/bin/env python3
"""Pass30y — Package B ONLY (J13+J10+J11) atomic place + full reattach.

Preferred: J13(64,78.5) J10(113.46,28) J11(113.46,46)
Alt once if preferred fails Edge.Cuts/silk/pad clearance toward y=80:
         J13(67,76) + same J10/J11
If alt also dirty → full revert to pass30u keep, stop.
No Package A/C/D. No U1 move. No Gerbers.
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
SNAP = f"{ROOT}/.mcp-backups/pass30y-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
PRE = f"{SNAP}/pre-edit.kicad_pcb"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18

# Package B preferred / alt
PREF = {"J13": (64.0, 78.5), "J10": (113.46, 28.0), "J11": (113.46, 46.0)}
ALT = {"J13": (67.0, 76.0), "J10": (113.46, 28.0), "J11": (113.46, 46.0)}
START = {"J13": (64.0, 76.0), "J10": (116.0, 28.0), "J11": (116.0, 46.0)}

REATTACH = {
    "J13": [
        "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "P0.21", "P0.22", "P0.23",
        "P0.24", "P0.25", "P0.26", "P0.27", "P0.28", "P0.29", "P0.30", "P0.31",
        "VDD_nRF", "VDD_GPIO", "GND",
    ],
    "J10": ["P0.21", "P0.22", "P0.23", "P0.24", "VDD_GPIO", "GND"],
    "J11": ["P0.30", "P0.31", "VDD_GPIO", "GND"],
}

WATCH = [
    "P0.08", "P0.15", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "P0.21",
    "P0.22", "P0.23", "P0.24", "P0.30", "P0.31", "VDD_GPIO", "VDD_nRF", "VDD2",
    "GND", "COEX0", "COEX2", "ENABLE",
]


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
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30y.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30y.json", out_path)
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


def edge_class_failure(data, stats):
    """Preferred (64,78.5) edge/silk/pad-to-y80 band failure → allow alt retry."""
    if stats.get("copper_edge_clearance", 0) > 0 or stats.get("hole_clearance", 0) > 0:
        return True
    for v in data.get("violations", []):
        typ = v.get("type", "")
        desc = (v.get("description") or "").lower()
        if typ in ("copper_edge_clearance", "edge_clearance", "silk_edge_clearance"):
            return True
        if "edge" in desc and ("cut" in desc or "board" in desc):
            return True
        # south-band copper fights near y=80 / J13 preferred landing
        if typ in ("shorting_items", "clearance", "tracks_crossing"):
            for it in v.get("items", []):
                pos = it.get("pos") or {}
                y = pos.get("y")
                x = pos.get("x")
                idesc = (it.get("description") or "")
                if y is not None and y >= 76.5:
                    if ("J13" in idesc) or (x is not None and 62 <= x <= 115):
                        return True
                if "Edge.Cuts" in idesc or "Edge.Cuts" in (v.get("description") or ""):
                    return True
                if "Silk" in idesc and y is not None and y >= 76:
                    return True
    return False


def collect_pad_endpoint_hits(board, refs, tol=0.35):
    """Return list of (track, which_end 'start'|'end', ref, padnum, net, layer, w, ox,oy, otherx,othery)."""
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
            allowed = set(REATTACH[ref])
            for pnum, (px, py, pnet) in pads.items():
                if pnet != net:
                    continue
                if net not in allowed and net != "GND":
                    # still move any copper physically on the pad to avoid orphans
                    pass
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


def translate_endpoints_for_pure_delta(board, refs, deltas, tol=0.40):
    """Move track endpoints that sit on old pads by per-ref (dx,dy). Best for pure dy/dx without diagonalizing when stub aligns with delta."""
    pads_by_ref = {ref: pad_centers(board, ref) for ref in refs}
    moved = 0
    touched_tracks = set()
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            # vias sitting on pads — rare for these headers
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            for ref, pads in pads_by_ref.items():
                dx, dy = deltas[ref]
                for pnum, (px, py, pnet) in pads.items():
                    if near(x, px, tol) and near(y, py, tol) and t.GetNetname() == pnet:
                        t.SetPosition(xy(px + dx, py + dy))
                        moved += 1
            continue
        sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
        ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
        nsx, nsy, nex, ney = sx, sy, ex, ey
        changed = False
        for ref, pads in pads_by_ref.items():
            dx, dy = deltas[ref]
            for pnum, (px, py, pnet) in pads.items():
                if t.GetNetname() != pnet:
                    continue
                if near(sx, px, tol) and near(sy, py, tol):
                    nsx, nsy = px + dx, py + dy
                    changed = True
                if near(ex, px, tol) and near(ey, py, tol):
                    nex, ney = px + dx, py + dy
                    changed = True
        if changed:
            t.SetStart(xy(nsx, nsy))
            t.SetEnd(xy(nex, ney))
            moved += 1
            touched_tracks.add(id(t))
    return moved


def rip_pad_stubs(board, refs, tol=0.35):
    """Remove tracks that touch any pad of refs; return records for reattach."""
    hits = collect_pad_endpoint_hits(board, refs, tol=tol)
    # de-dupe by track object — keep all hit ends
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
        fp = board.FindFootprintByReference(ref)
        fp.SetPosition(xy(x, y))


def reattach_after_rip(board, records, old_pads, new_pads):
    """Reattach ripped stubs to new pad positions with axis-aligned jogs."""
    added = 0
    for rec in records:
        net, layer, w = rec["net"], rec["layer"], rec["w"]
        sx, sy, ex, ey = rec["seg"]
        # Determine which ends were on pads
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
            # both ends on (possibly different) pads — connect new pads AA
            x1, y1 = new_pad_xy(start_hit)
            x2, y2 = new_pad_xy(end_hit)
            if abs(x1 - x2) > 1e-9 and abs(y1 - y2) > 1e-9:
                # L-jog via shared y of start new pad
                add_trk(board, net, x1, y1, x2, y1, w, layer)
                add_trk(board, net, x2, y1, x2, y2, w, layer)
                added += 2
            else:
                add_trk(board, net, x1, y1, x2, y2, w, layer)
                added += 1
            continue

        if start_hit and not end_hit:
            nx, ny = new_pad_xy(start_hit)
            ox, oy = ex, ey  # other end stays
            # AA path: pad -> (nx,oy) -> (ox,oy) if needed, or pad -> (ox,ny) -> (ox,oy)
            if near(nx, ox) or near(ny, oy):
                add_trk(board, net, nx, ny, ox, oy, w, layer)
                added += 1
            else:
                # Prefer vertical-first from header (J13 row / J10 col)
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

        # no hit classified — restore original segment
        add_trk(board, net, sx, sy, ex, ey, w, layer)
        added += 1
    return added


def also_shift_column_bus(board, old_x, new_x, y_lo, y_hi, nets, tol=0.35):
    """Shift track endpoints that sit on old header column x (bus stubs not exactly on pad centers)."""
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


def apply_package(targets, label):
    """Atomic: rip pad stubs → move FPs → reattach → column bus fix → zone fill.
    Returns dict with mid stats etc. Does not decide keep/revert.
    """
    board = load()
    old_pads = {ref: pad_centers(board, ref) for ref in targets}
    # verify start positions
    for ref, (sx, sy) in START.items():
        live = fp_xy(board, ref)
        if abs(live[0] - sx) > 0.05 or abs(live[1] - sy) > 0.05:
            # may already be mid-attempt only if we forgot restore — caller restores
            pass

    records = rip_pad_stubs(board, list(targets.keys()), tol=0.35)
    save(board)
    board = load()  # refresh after Delete — SWIG proxies go stale otherwise
    move_fps(board, targets)
    save(board)
    board = load()
    new_pads = {ref: pad_centers(board, ref) for ref in targets}
    added = reattach_after_rip(board, records, old_pads, new_pads)

    # J10/J11 column bus stubs (VDD_GPIO etc.) that end on x=116 in header y-band
    bus_nets = set(REATTACH["J10"]) | set(REATTACH["J11"])
    nbus = also_shift_column_bus(
        board, 116.0, targets["J10"][0], 27.0, 55.0, bus_nets, tol=0.40
    )
    # J13 row bus: any leftover endpoints on old y=76 along pad x span
    # (reattach should have handled pad hits; this catches near-misses)
    j13_nets = set(REATTACH["J13"])
    nrow = 0
    old_y = START["J13"][1]
    new_y = targets["J13"][1]
    old_x0 = START["J13"][0]
    new_x0 = targets["J13"][0]
    dx = new_x0 - old_x0
    dy = new_y - old_y
    if abs(dx) > 0.01 or abs(dy) > 0.01:
        for t in list(board.GetTracks()):
            if isinstance(t, pcbnew.PCB_VIA):
                continue
            if t.GetNetname() not in j13_nets:
                continue
            sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
            ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
            nsx, nsy, nex, ney = sx, sy, ex, ey
            ch = False
            # old pad-row orphans at y=76, x in old pad span
            for pnum, (px, py, pnet) in old_pads["J13"].items():
                if t.GetNetname() != pnet:
                    continue
                if near(sx, px, 0.35) and near(sy, py, 0.35):
                    nsx, nsy = px + dx, py + dy
                    ch = True
                if near(ex, px, 0.35) and near(ey, py, 0.35):
                    nex, ney = px + dx, py + dy
                    ch = True
            if ch:
                t.SetStart(xy(nsx, nsy))
                t.SetEnd(xy(nex, ney))
                nrow += 1

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
            "J13.1": list(new_pads["J13"]["1"][:2]),
            "J13.4": list(new_pads["J13"]["4"][:2]),
            "J13.7": list(new_pads["J13"]["7"][:2]),
            "J10.2": list(new_pads["J10"]["2"][:2]),
            "J11.2": list(new_pads["J11"]["2"][:2]),
        },
    }


def restore_pre():
    shutil.copy2(PRE, BOARD)


def main():
    os.makedirs(SNAP, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    assert os.path.isfile(PRE), "missing pre-edit backup"

    summary = {
        "pass": "layout-pass30y",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "scope": "Package B ONLY — J13+J10+J11 atomic place + full reattach",
        "preferred": {k: list(v) for k, v in PREF.items()},
        "alt": {k: list(v) for k, v in ALT.items()},
        "no_gerbers": True,
        "packages_skipped": ["A", "C", "D"],
        "no_u1_move": True,
        "backup": PRE,
        "live_xy_before": {},
        "j13_landing_kept": None,
        "phase": "INIT",
    }

    board = load()
    for ref in ["J13", "J10", "J11", "U1"]:
        summary["live_xy_before"][ref] = list(fp_xy(board, ref))
    # confirm start
    for ref, exp in START.items():
        live = tuple(summary["live_xy_before"][ref])
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            summary["phase"] = "ABORT_UNEXPECTED_START_XY"
            summary["error"] = f"{ref} live {live} != expected {exp}"
            json.dump(summary, open(f"{REPORTS}/PASS30Y_SUMMARY.json", "w"), indent=2)
            print("ABORT", summary["error"])
            return

    west0 = p015_west(board)
    stage0 = stage_a_ok(board)
    summary["p015_west_before"] = west0
    summary["stage_a_before"] = stage0

    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30Y_BEFORE.json")
    summary["before"] = before
    summary["before_nets_watch"] = {n: nets_of(before_data).get(n, 0) for n in WATCH}
    print("BEFORE", before)

    attempts = []

    # --- Attempt 1: preferred ---
    restore_pre()
    info = apply_package(PREF, "preferred_J13_64_78.5")
    mid_data, mid = run_drc(f"{REPORTS}/DRC_PASS30Y_MID_PREF.json")
    info["mid"] = mid
    info["mid_nets_watch"] = {n: nets_of(mid_data).get(n, 0) for n in WATCH}
    info["collide"] = colliding(mid_data)
    info["clean"] = clean(mid)
    info["edge_class"] = edge_class_failure(mid_data, mid)
    info["stage_a"] = stage_a_ok(load())
    info["p015_west"] = p015_west(load())
    attempts.append(info)
    print("MID_PREF", mid, "clean", info["clean"], "edge_class", info["edge_class"])
    shutil.copy2(BOARD, f"{SNAP}/after-pref.kicad_pcb")

    kept = None
    if info["clean"] and mid["unconnected_items"] <= 67:
        # soft allow temp spike? user said unconnected ≤67 success; temp spike OK during reattach but final must ≤67
        if (
            info["stage_a"]["VDD_nRF_via_north"]
            and info["stage_a"]["VDD2_present"]
            and info["p015_west"] >= west0
        ):
            kept = "preferred"
            summary["j13_landing_kept"] = "preferred (64, 78.5)"
        else:
            info["protect_fail"] = True
            restore_pre()
    elif info["clean"] and mid["unconnected_items"] > 67:
        # clean DRC but unconnected spiked — treat as fail, revert
        info["unconnected_spike"] = mid["unconnected_items"]
        restore_pre()
    else:
        # dirty
        if info["edge_class"]:
            print("PREF edge-class fail → try ALT once")
            restore_pre()
            info2 = apply_package(ALT, "alt_J13_67_76")
            mid2_data, mid2 = run_drc(f"{REPORTS}/DRC_PASS30Y_MID_ALT.json")
            info2["mid"] = mid2
            info2["mid_nets_watch"] = {n: nets_of(mid2_data).get(n, 0) for n in WATCH}
            info2["collide"] = colliding(mid2_data)
            info2["clean"] = clean(mid2)
            info2["stage_a"] = stage_a_ok(load())
            info2["p015_west"] = p015_west(load())
            attempts.append(info2)
            print("MID_ALT", mid2, "clean", info2["clean"])
            shutil.copy2(BOARD, f"{SNAP}/after-alt.kicad_pcb")
            if (
                info2["clean"]
                and mid2["unconnected_items"] <= 67
                and info2["stage_a"]["VDD_nRF_via_north"]
                and info2["stage_a"]["VDD2_present"]
                and info2["p015_west"] >= west0
            ):
                kept = "alt"
                summary["j13_landing_kept"] = "alt (67, 76)"
            else:
                restore_pre()
                summary["j13_landing_kept"] = None
                summary["stop_reason"] = "alt also dirty or protect/unconnected fail — full revert to pass30u keep"
        else:
            restore_pre()
            summary["j13_landing_kept"] = None
            summary["stop_reason"] = (
                "preferred dirty (non-edge-class shorting/clearance/crossing) — full package revert, no alt"
            )

    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30Y_AFTER.json")
    board = load()
    summary["attempts"] = []
    for a in attempts:
        row = {k: v for k, v in a.items() if k != "collide"}
        row["collide"] = a.get("collide", [])[:12]
        summary["attempts"].append(row)

    summary["after"] = after
    summary["after_nets_watch"] = {n: nets_of(after_data).get(n, 0) for n in WATCH}
    summary["final_xy"] = {ref: list(fp_xy(board, ref)) for ref in ["J13", "J10", "J11", "U1"]}
    summary["p015_west_after"] = p015_west(board)
    summary["stage_a_after"] = stage_a_ok(board)
    summary["kept"] = kept
    summary["reverted"] = kept is None

    if kept:
        summary["phase"] = "COMPLETE_PACKAGE_B_KEPT"
        summary["success_gate"] = (
            f"OK clean DRC + unconnected {before['unconnected_items']}→{after['unconnected_items']} "
            f"≤67; J13 landing={summary['j13_landing_kept']}"
        )
    else:
        summary["phase"] = "COMPLETE_REVERTED"
        summary["success_gate"] = (
            f"BLOCKED — reverted to pass30u keep; unconnected {before['unconnected_items']}→{after['unconnected_items']}; "
            f"shorting/clearance/crossing={after['shorting_items']}/{after['clearance']}/{after['tracks_crossing']}"
        )

    json.dump(summary, open(f"{REPORTS}/PASS30Y_SUMMARY.json", "w"), indent=2)
    # also markdown brief
    lines = [
        f"# PASS30Y_SUMMARY — Package B only",
        f"",
        f"**Timestamp:** {summary['timestamp_ist']}",
        f"**Phase:** {summary['phase']}",
        f"**J13 landing kept:** {summary['j13_landing_kept']}",
        f"**Final XY:** J13={summary['final_xy']['J13']} J10={summary['final_xy']['J10']} J11={summary['final_xy']['J11']} U1={summary['final_xy']['U1']}",
        f"",
        f"## DRC",
        f"",
        f"| | unconnected | shorting | clearance | crossing |",
        f"| --- | ---: | ---: | ---: | ---: |",
        f"| Before | {before['unconnected_items']} | {before['shorting_items']} | {before['clearance']} | {before['tracks_crossing']} |",
        f"| After | {after['unconnected_items']} | {after['shorting_items']} | {after['clearance']} | {after['tracks_crossing']} |",
        f"",
        f"**Gate:** {summary['success_gate']}",
        f"",
        f"## Attempts",
        f"",
    ]
    for a in summary["attempts"]:
        lines.append(f"### {a['label']}")
        lines.append(f"- targets: {a['targets']}")
        lines.append(f"- mid: {a['mid']}")
        lines.append(f"- clean: {a.get('clean')} edge_class: {a.get('edge_class')}")
        lines.append(f"- ripped={a['ripped']} reattached={a['reattached_segs']} bus={a['bus_shifted']}")
        if a.get("collide"):
            lines.append(f"- collide head: {json.dumps(a['collide'][:3])[:500]}")
        lines.append("")
    lines.append(f"**Stop reason:** {summary.get('stop_reason')}")
    lines.append(f"**Backup:** `{PRE}`")
    open(f"{REPORTS}/PASS30Y_SUMMARY.md", "w").write("\n".join(lines) + "\n")
    print("PHASE", summary["phase"])
    print("GATE", summary["success_gate"])
    print("FINAL_XY", summary["final_xy"])


if __name__ == "__main__":
    main()
