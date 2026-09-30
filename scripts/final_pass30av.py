#!/usr/bin/env python3
"""pass30av — ONE attempt: P0.14 only.

Place one 0.50/0.30 through via at x=42.25 between the P0.15 and P0.13
F.Cu tracks, tie U1.24 with one F.Cu stub, refill so B.Cu GND pulls back,
then route B.Cu toward J18.2 in at most 8 segments.

The live B.Cu free space (tracks, vias, pads, holes; GND pour ignored
because refill pulls it back) around that via does not reach J18.2 without
entering the SiP body or crossing foreign copper. No B.Cu segments are
added. The via+stub cannot drop a P0.14 open, so the gate fails and the
board is restored. No F.Cu pinch retry. No second path.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30av/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18
VIA_OD = 0.50
VIA_DRILL = 0.30
VIA_X = 42.25
VIA_Y = 25.50
STUB = ((42.25, 26.40), (42.25, 25.50))
CLEAR_FOREIGN = 0.15
CLEAR_POWER = 0.20
HOLE_MIN = 0.25
BODY = (28.0, 26.75, 44.0, 37.25)
POWER = {
    "VDD1",
    "VDD2",
    "VDD2_MID",
    "VDD_nRF",
    "VIN",
    "VIN_F",
    "VIN_FILT",
    "VIN_IN",
    "VDD_GPIO",
}


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def r3(v: float) -> float:
    return round(v, 3)


def gnd_zone(board, layer):
    for z in board.Zones():
        if z.GetNetname() == "GND" and z.GetFirstLayer() == layer and z.IsFilled():
            return z
    return None


def fill_distance(polys, x, y) -> float:
    pt = xy(x, y)
    if polys.Contains(pt):
        return 0.0
    if not polys.Collide(pcbnew.SHAPE_CIRCLE(pt, pcbnew.FromMM(4.0))):
        return 4.0
    lo, hi = 0.0, 4.0
    for _ in range(18):
        mid = (lo + hi) / 2
        if polys.Collide(pcbnew.SHAPE_CIRCLE(pt, pcbnew.FromMM(mid))):
            hi = mid
        else:
            lo = mid
    return lo


def nongnd_counts(data) -> Counter:
    c: Counter = Counter()
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        nets = {n for n in re.findall(r"\[([^\]]+)\]", desc) if n != "GND"}
        for n in nets:
            c[n] += 1
    return c


def gnd_items(data) -> int:
    n = 0
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        if "[GND]" in desc:
            n += 1
    return n


def run_drc(dest: Path) -> dict:
    tmp = Path("/tmp/nrf30av_drc.json")
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", str(tmp), str(BOARD)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, dest)
    data = json.loads(dest.read_text())
    vc = Counter(v["type"] for v in data.get("violations", []))
    stats = {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "hole_to_hole": vc.get("hole_to_hole", 0),
        "gnd_zone_islands": gnd_items(data),
        "p014_unconnected": nongnd_counts(data).get("P0.14", 0),
        "p030_unconnected": nongnd_counts(data).get("P0.30", 0),
        "p031_unconnected": nongnd_counts(data).get("P0.31", 0),
    }
    return {"stats": stats, "data": data}


def footprint_xy(board) -> dict:
    out = {}
    for f in board.GetFootprints():
        out[f.GetReference()] = (
            round(mm(f.GetPosition().x), 4),
            round(mm(f.GetPosition().y), 4),
            round(f.GetOrientationDegrees(), 3),
        )
    return out


def via_at(board, net, x, y, tol=0.02) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if abs(mm(t.GetPosition().x) - x) < tol and abs(mm(t.GetPosition().y) - y) < tol:
            return True
    return False


def protect(board) -> dict:
    return {
        "p030_via": via_at(board, "P0.30", 112.40, 46.40),
        "vdd_via": via_at(board, "VDD_GPIO", 76.4375, 39.050),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "p013_via": via_at(board, "P0.13", 42.75, 23.1),
        "p015_via": via_at(board, "P0.15", 41.75, 23.1),
    }


def collect_foreign(board, layer):
    shapes = []
    holes = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.14":
            continue
        if t.GetClass() == "PCB_VIA":
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(layer) // 2),
                    net in POWER,
                    f"via {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                )
            )
            holes.append(
                (
                    pcbnew.SHAPE_CIRCLE(t.GetPosition(), int(t.GetDrill()) // 2),
                    f"viahole {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                )
            )
        elif t.GetLayer() == layer:
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth()),
                    net in POWER,
                    (
                        f"{'F' if layer == F else 'B'} {net} "
                        f"({mm(t.GetStart().x):.2f},{mm(t.GetStart().y):.2f})-"
                        f"({mm(t.GetEnd().x):.2f},{mm(t.GetEnd().y):.2f})"
                    ),
                )
            )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(layer) or p.GetNetname() == "P0.14":
                continue
            shapes.append(
                (
                    p.GetNetname(),
                    p.GetEffectiveShape(layer),
                    p.GetNetname() in POWER,
                    f"pad {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                )
            )
            if p.GetDrillSize().x:
                holes.append(
                    (
                        pcbnew.SHAPE_CIRCLE(p.GetPosition(), int(p.GetDrillSize().x) // 2),
                        f"hole {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                    )
                )
    return shapes, holes


def consider(sh, shapes, holes):
    worst = None
    pwr = None
    bb = sh.BBox()
    pad = pcbnew.FromMM(3)
    for net, other, isp, desc in shapes:
        ob = other.BBox()
        if ob.GetRight() < bb.GetLeft() - pad or ob.GetLeft() > bb.GetRight() + pad:
            continue
        if ob.GetBottom() < bb.GetTop() - pad or ob.GetTop() > bb.GetBottom() + pad:
            continue
        c = mm(sh.GetClearance(other))
        rec = (c, net, desc)
        if worst is None or c < worst[0]:
            worst = rec
        if isp and (pwr is None or c < pwr[0]):
            pwr = rec
    hworst = None
    for circ, desc in holes:
        c = mm(sh.GetClearance(circ))
        if hworst is None or c < hworst[0]:
            hworst = (c, desc)
    return worst, pwr, hworst


def measure_new(board) -> dict:
    shapes_f, holes_f = collect_foreign(board, F)
    shapes_b, holes_b = collect_foreign(board, B)
    rows = []
    min_any = None
    min_pwr = None
    min_hole = None

    def eat(worst, pwr, hworst, row):
        nonlocal min_any, min_pwr, min_hole
        rows.append(row)
        if worst is not None and (min_any is None or worst[0] < min_any[0]):
            min_any = worst
        if pwr is not None and (min_pwr is None or pwr[0] < min_pwr[0]):
            min_pwr = pwr
        if hworst is not None and (min_hole is None or hworst[0] < min_hole[0]):
            min_hole = hworst

    stub = pcbnew.SHAPE_SEGMENT(xy(*STUB[0]), xy(*STUB[1]), pcbnew.FromMM(W))
    worst, pwr, hworst = consider(stub, shapes_f, holes_f)
    eat(
        worst,
        pwr,
        hworst,
        {
            "layer": "F.Cu",
            "stub": [list(STUB[0]), list(STUB[1])],
            "min_clearance_mm": None if worst is None else round(worst[0], 4),
            "min_item": None if worst is None else {"net": worst[1], "item": worst[2]},
            "min_power_mm": None if pwr is None else round(pwr[0], 4),
        },
    )
    via = pcbnew.SHAPE_CIRCLE(xy(VIA_X, VIA_Y), pcbnew.FromMM(VIA_OD / 2))
    for name, shapes, holes in (("F.Cu", shapes_f, holes_f), ("B.Cu", shapes_b, holes_b)):
        worst, pwr, hworst = consider(via, shapes, holes)
        eat(
            worst,
            pwr,
            hworst,
            {
                "layer": name,
                "via": [VIA_X, VIA_Y],
                "min_clearance_mm": None if worst is None else round(worst[0], 4),
                "min_item": None if worst is None else {"net": worst[1], "item": worst[2]},
                "min_power_mm": None if pwr is None else round(pwr[0], 4),
            },
        )
    # hole-to-hole of the new drill
    vdrill = pcbnew.SHAPE_CIRCLE(xy(VIA_X, VIA_Y), pcbnew.FromMM(VIA_DRILL / 2))
    h2h = None
    for circ, desc in holes_f:
        c = mm(vdrill.GetClearance(circ))
        if h2h is None or c < h2h[0]:
            h2h = (c, desc)
    # zone pullback after refill
    zone = {}
    for layer, name in ((F, "F.Cu"), (B, "B.Cu")):
        z = gnd_zone(board, layer)
        if z is None:
            zone[name] = {"present": False}
            continue
        polys = z.GetFilledPolysList(layer)
        d_center = fill_distance(polys, VIA_X, VIA_Y)
        edge = d_center - VIA_OD / 2
        zone[name] = {
            "present": True,
            "center_inside_fill": d_center == 0.0,
            "center_to_fill_mm": round(d_center, 4),
            "pad_edge_clearance_mm": round(edge, 4),
        }
        if d_center == 0.0 or edge < (min_any[0] if min_any else 99):
            rec = (edge, "GND", f"{name} GND zone fill")
            if min_any is None or edge < min_any[0]:
                min_any = rec
    return {
        "rows": rows,
        "min_clearance_mm": None if min_any is None else round(min_any[0], 4),
        "min_clearance_item": None if min_any is None else {"net": min_any[1], "item": min_any[2]},
        "min_power_vin_mm": None if min_pwr is None else round(min_pwr[0], 4),
        "min_power_vin_item": None if min_pwr is None else {"net": min_pwr[1], "item": min_pwr[2]},
        "min_hole_mm": None if min_hole is None else round(min_hole[0], 4),
        "min_hole_item": None if min_hole is None else min_hole[1],
        "min_hole_to_hole_mm": None if h2h is None else round(h2h[0], 4),
        "min_hole_to_hole_item": None if h2h is None else h2h[1],
        "zone": zone,
        "refill_cleared_via": all(
            (not zone[n]["present"]) or (not zone[n]["center_inside_fill"] and zone[n]["pad_edge_clearance_mm"] >= CLEAR_FOREIGN - 1e-6)
            for n in ("F.Cu", "B.Cu")
        ),
    }


def free_space(board) -> dict:
    """B.Cu track-center component from the via. GND pour is not an obstacle."""
    shapes, holes = collect_foreign(board, B)
    # bucket
    cell = 6.0
    buckets: dict = {}
    packed = []
    for net, sh, isp, desc in shapes:
        bb = sh.BBox()
        rec = (mm(bb.GetLeft()), mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom()), sh, net, isp, "cu")
        packed.append(rec)
    for sh, desc in holes:
        bb = sh.BBox()
        packed.append((mm(bb.GetLeft()), mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom()), sh, "", False, "hole"))
    for i, o in enumerate(packed):
        L, R, T, Bm = o[:4]
        for ix in range(int((L - 1.2) / cell) - 1, int((R + 1.2) / cell) + 2):
            for iy in range(int((T - 1.2) / cell) - 1, int((Bm + 1.2) / cell) + 2):
                buckets.setdefault((ix, iy), []).append(i)
    half = W / 2

    def ok(x, y):
        if x < 24.29 or y < 1.0 or y > 78.5 or x > 100:
            return False
        if BODY[0] - half <= x <= BODY[2] + half and BODY[1] - half <= y <= BODY[3] + half:
            return False
        circ = pcbnew.SHAPE_CIRCLE(xy(x, y), pcbnew.FromMM(half))
        ix, iy = int(x / cell), int(y / cell)
        for i in buckets.get((ix, iy), ()):
            L, R, T, Bm, sh, net, isp, kind = packed[i]
            if x < L - 1.2 or x > R + 1.2 or y < T - 1.2 or y > Bm + 1.2:
                continue
            c = mm(circ.GetClearance(sh))
            need = HOLE_MIN if kind == "hole" else (CLEAR_POWER if isp else CLEAR_FOREIGN)
            if c < need - 1e-9:
                return False
        return True

    step = 0.2
    sx, sy = round(round(VIA_X / step) * step, 2), round(round(VIA_Y / step) * step, 2)
    if not ok(sx, sy):
        return {"start_ok": False, "start": [sx, sy]}
    q = deque([(sx, sy)])
    seen = {(sx, sy)}
    minx = maxx = sx
    miny = maxy = sy
    reached_header = False
    while q:
        x, y = q.popleft()
        if y >= 60.5 and 39.0 <= x <= 42.5:
            reached_header = True
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            nx, ny = round(x + dx, 2), round(y + dy, 2)
            if (nx, ny) in seen or not ok(nx, ny):
                continue
            seen.add((nx, ny))
            minx, maxx = min(minx, nx), max(maxx, nx)
            miny, maxy = min(miny, ny), max(maxy, ny)
            q.append((nx, ny))
    return {
        "start_ok": True,
        "start": [sx, sy],
        "cells": len(seen),
        "bbox": {"xmin": minx, "xmax": maxx, "ymin": miny, "ymax": maxy},
        "reaches_j18": reached_header,
        "step_mm": step,
    }


def add_via_and_stub(board):
    net = board.FindNet("P0.14")
    if net is None:
        raise SystemExit("P0.14 missing")
    u1 = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    pad = next(p for p in u1.Pads() if p.GetNumber() == "24")
    if not pad.HitTest(xy(*STUB[0])):
        raise SystemExit(f"stub start {STUB[0]} is not on U1.24")
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(xy(*STUB[0]))
    tr.SetEnd(xy(*STUB[1]))
    tr.SetWidth(pcbnew.FromMM(W))
    tr.SetLayer(F)
    tr.SetNet(net)
    board.Add(tr)
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(xy(VIA_X, VIA_Y))
    v.SetWidth(F, pcbnew.FromMM(VIA_OD))
    v.SetWidth(B, pcbnew.FromMM(VIA_OD))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)


def write_outputs(decision, stamp, before, mid, after, measure, space, reason, board_sha):
    b = before["stats"]
    m = None if mid is None else mid["stats"]
    a = after["stats"]
    summary = {
        "pass": "pass30av",
        "timestamp": stamp,
        "kicad": "9.0.2",
        "decision": decision,
        "net": "P0.14",
        "backup": str(BACKUP.relative_to(ROOT)),
        "via": {
            "x": VIA_X,
            "y": VIA_Y,
            "pad_mm": VIA_OD,
            "drill_mm": VIA_DRILL,
            "placed_then_reverted": decision != "KEEP",
        },
        "fcu_stub": {
            "width_mm": W,
            "start": list(STUB[0]),
            "end": list(STUB[1]),
            "note": "Not part of the 8-segment B.Cu budget. Reverted with the via.",
        },
        "bcu_segments": [],
        "bcu_segment_count": 0,
        "bcu_limit": 8,
        "free_space": space,
        "refill_cleared_via": measure.get("refill_cleared_via"),
        "zone": measure.get("zone"),
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "min_foreign_item": measure.get("min_clearance_item"),
        "min_power_vin_clearance_mm": measure.get("min_power_vin_mm"),
        "min_power_item": measure.get("min_power_vin_item"),
        "min_hole_to_hole_mm": measure.get("min_hole_to_hole_mm"),
        "min_hole_to_hole_item": measure.get("min_hole_to_hole_item"),
        "p014_opens": {
            "before": b.get("p014_unconnected"),
            "mid": None if m is None else m.get("p014_unconnected"),
            "after": a.get("p014_unconnected"),
        },
        "unconnected": {
            "before": b.get("unconnected_items"),
            "mid": None if m is None else m.get("unconnected_items"),
            "after": a.get("unconnected_items"),
        },
        "gnd_islands": {
            "before": b.get("gnd_zone_islands"),
            "mid": None if m is None else m.get("gnd_zone_islands"),
            "after": a.get("gnd_zone_islands"),
            "note": "waived",
        },
        "drc_mid": m,
        "drc_after": a,
        "reason": reason,
        "board_sha256_final": board_sha,
        "locked_untouched": [
            "P0.15",
            "P0.30",
            "P0.31",
            "P0.22",
            "P0.04",
            "VDD_GPIO",
            "COEX0",
            "DEC0",
            "P0.10",
            "P0.12",
            "P0.19",
            "U1.88",
            "U1.89",
        ],
    }
    (REPORTS / "PASS30AV_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    bb = space.get("bbox") or {}
    zone_b = (measure.get("zone") or {}).get("B.Cu") or {}
    md = f"""# PASS30AV_SUMMARY — P0.14

**Timestamp:** {stamp}
**KiCad:** 9.0.2
**Decision:** **{decision}**
**Net:** P0.14
**Via:** ({VIA_X:.2f}, {VIA_Y:.2f}), 0.50 mm pad, 0.30 mm drill. Placed, refilled, then removed on revert.
**Refill cleared the via:** {measure.get("refill_cleared_via")} (B.Cu pad-edge to GND fill {zone_b.get("pad_edge_clearance_mm")} mm, center inside fill {zone_b.get("center_inside_fill")})
**F.Cu stub:** ({STUB[0][0]:.2f}, {STUB[0][1]:.2f}) → ({STUB[1][0]:.2f}, {STUB[1][1]:.2f}), 0.18 mm, one segment, not in the B.Cu budget. Reverted with the via.
**B.Cu segments:** 0 (limit 8). No second via.
**Min foreign clearance (via + stub, after refill, including the pulled-back zone):** {measure.get("min_clearance_mm")} mm vs {measure.get("min_clearance_item")}
**Min POWER clearance:** {measure.get("min_power_vin_mm")} mm vs {measure.get("min_power_vin_item")}
**New via hole-to-hole:** {measure.get("min_hole_to_hole_mm")} mm vs {measure.get("min_hole_to_hole_item")}
**P0.14 opens:** {b.get("p014_unconnected")} → {a.get("p014_unconnected")} (mid {None if m is None else m.get("p014_unconnected")})
**Unconnected:** {b.get("unconnected_items")} → {a.get("unconnected_items")} (mid {None if m is None else m.get("unconnected_items")})
**GND islands:** {b.get("gnd_zone_islands")} → {a.get("gnd_zone_islands")} (waived; mid {None if m is None else m.get("gnd_zone_islands")})

## Why no B.Cu route

The via sits between the parallel F.Cu tracks (P0.15 at x=41.75, P0.13 at x=42.75). A 0.50 mm pad at x=42.25 clears each track by 0.16 mm. y=25.50 keeps the pad north of the SiP body (pad south edge y=25.75, body starts y=26.75) and south of the P0.13/P0.15 vias at y=23.1 / 23.95.

B.Cu GND there is zone fill. Refill was run so the pour could pull back. That does not open a path to J18.2. A 0.2 mm flood of B.Cu track centers that clear foreign copper by 0.15 mm, POWER by 0.20 mm, and holes by 0.25 mm, stay at copper x>24.2, and stay outside the SiP body, has bbox x {bb.get("xmin")}–{bb.get("xmax")}, y {bb.get("ymin")}–{bb.get("ymax")} ({space.get("cells")} cells). It does not reach J18.2. The south side is the body plus the VDD2 trunk at y=26.75; the west side stops at the VDD_GPIO / COEX0 wall near x=29; the east side stops at x=46.2. Leaving that component crosses foreign copper or the body. No 8-segment polyline exists, and no longer polyline exists either. Zero B.Cu segments were added. The sealed pocket y≈44.60, x≈81.8–97.3 was not used. Locked trunks were not ripped. P0.13 and P0.15 vias were not moved. The F.Cu pinch between those vias was not retried. U1.88 and U1.89 were not retried. P0.24 was not started.

## Gate

{reason}

## DRC

| | unconnected | P0.14 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | {b.get("unconnected_items")} | {b.get("p014_unconnected")} | {b.get("shorting_items")} | {b.get("clearance")} | {b.get("tracks_crossing")} | {b.get("hole_clearance")} | {b.get("hole_to_hole")} | {b.get("gnd_zone_islands")} |
| mid (via+stub, before revert) | {None if m is None else m.get("unconnected_items")} | {None if m is None else m.get("p014_unconnected")} | {None if m is None else m.get("shorting_items")} | {None if m is None else m.get("clearance")} | {None if m is None else m.get("tracks_crossing")} | {None if m is None else m.get("hole_clearance")} | {None if m is None else m.get("hole_to_hole")} | {None if m is None else m.get("gnd_zone_islands")} |
| after restore | {a.get("unconnected_items")} | {a.get("p014_unconnected")} | {a.get("shorting_items")} | {a.get("clearance")} | {a.get("tracks_crossing")} | {a.get("hole_clearance")} | {a.get("hole_to_hole")} | {a.get("gnd_zone_islands")} |
"""
    (REPORTS / "PASS30AV_SUMMARY.md").write_text(md)
    note = f"""
## Pass30av — P0.14 via in the pocket, revert — {stamp}

**Decision:** **{decision}**. One via at ({VIA_X:.2f}, {VIA_Y:.2f}), 0.50/0.30, plus one F.Cu stub ({STUB[0][0]:.2f}, {STUB[0][1]:.2f})–({STUB[1][0]:.2f}, {STUB[1][1]:.2f}). Refill cleared the via: {measure.get("refill_cleared_via")} (B.Cu pad-edge {zone_b.get("pad_edge_clearance_mm")} mm). B.Cu segments 0. The free B.Cu component from the via is x {bb.get("xmin")}–{bb.get("xmax")}, y {bb.get("ymin")}–{bb.get("ymax")} and does not reach J18.2, so no 8-segment route was added.

**Clearance of the new copper (mid, after refill):** foreign {measure.get("min_clearance_mm")} mm, POWER {measure.get("min_power_vin_mm")} mm, hole-to-hole {measure.get("min_hole_to_hole_mm")} mm.

**P0.14 opens:** {b.get("p014_unconnected")} → {a.get("p014_unconnected")} (mid {None if m is None else m.get("p014_unconnected")}). **Unconnected:** {b.get("unconnected_items")} → {a.get("unconnected_items")} (mid {None if m is None else m.get("unconnected_items")}). GND islands waived. Full restore to `.mcp-backups/pass30av/pre-edit.kicad_pcb`. No F.Cu pinch retry. P0.13/P0.15 vias not moved. U1.88 / U1.89 not retried. P0.24 not started. No Gerbers. No git commit.

**Artifacts:** `reports/PASS30AV_SUMMARY.{{md,json}}`, `reports/DRC_PASS30AV_BEFORE.json`, `reports/DRC_PASS30AV_MID.json`, `reports/DRC_PASS30AV_AFTER.json`, `scripts/final_pass30av.py`
"""
    text = REVIEW.read_text()
    marker = "## Pass30av —"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    REVIEW.write_text(text.rstrip() + "\n" + note)


def main():
    if not BACKUP.exists():
        raise SystemExit("backup missing")
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("live board does not match pass30av backup; refusing to edit")
    stamp = ist_now()
    before = run_drc(REPORTS / "DRC_PASS30AV_BEFORE.json")
    print("BEFORE", before["stats"], flush=True)
    if sha(BOARD) != sha(BACKUP):
        shutil.copy2(BACKUP, BOARD)
        raise SystemExit("DRC modified the board; restored backup and stopped")

    board = pcbnew.LoadBoard(str(BOARD))
    fp_before = footprint_xy(board)
    prot_before = protect(board)
    space = free_space(board)
    print("SPACE", json.dumps(space), flush=True)
    add_via_and_stub(board)
    if footprint_xy(board) != fp_before or protect(board) != prot_before:
        shutil.copy2(BACKUP, BOARD)
        raise SystemExit("protect or footprint changed; restored")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)
    # reload so fill geometry is what DRC will see
    board = pcbnew.LoadBoard(str(BOARD))
    measure = measure_new(board)
    print("MEASURE", json.dumps({k: measure[k] for k in measure if k != "rows"}), flush=True)
    mid = run_drc(REPORTS / "DRC_PASS30AV_MID.json")
    print("MID", mid["stats"], flush=True)

    b = before["stats"]
    m = mid["stats"]
    gained = {}
    bc = nongnd_counts(before["data"])
    mc = nongnd_counts(mid["data"])
    for n in set(bc) | set(mc):
        if mc[n] > bc[n]:
            gained[n] = {"before": bc[n], "after": mc[n]}
    gained.pop("P0.14", None)
    drop = b["p014_unconnected"] - m["p014_unconnected"]
    zone_ok = measure["refill_cleared_via"]
    foreign_ok = measure["min_clearance_mm"] is not None and measure["min_clearance_mm"] >= CLEAR_FOREIGN - 1e-9
    power_ok = measure["min_power_vin_mm"] is None or measure["min_power_vin_mm"] >= CLEAR_POWER - 1e-9
    electrical = (
        drop >= 1
        and not gained
        and m["shorting_items"] == 0
        and m["clearance"] == 0
        and m["tracks_crossing"] == 0
        and m["hole_clearance"] == 0
        and m["hole_to_hole"] <= b["hole_to_hole"]
        and zone_ok
        and foreign_ok
        and power_ok
        and space.get("reaches_j18")
    )
    # The B.Cu route was not added, so a keep is not possible even if the
    # via itself is clean. electrical stays false because drop is 0 and
    # reaches_j18 is false. Restore unconditionally unless every clause holds.
    if electrical:
        shutil.copy2(REPORTS / "DRC_PASS30AV_MID.json", REPORTS / "DRC_PASS30AV_AFTER.json")
        reason = "KEEP. Unexpected: opens dropped with no B.Cu route."
        write_outputs("KEEP", stamp, before, mid, mid, measure, space, reason, sha(BOARD))
        print("KEEP", flush=True)
        return

    shutil.copy2(BACKUP, BOARD)
    after = run_drc(REPORTS / "DRC_PASS30AV_AFTER.json")
    print("AFTER", after["stats"], flush=True)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("restore did not match backup bytes")
    reason = (
        f"REVERT. P0.14 opens {b['p014_unconnected']}→{m['p014_unconnected']} (need a drop of at least 1). "
        f"B.Cu segments added: 0. Free-space component reaches J18: {space.get('reaches_j18')}. "
        f"Refill cleared via: {zone_ok}. "
        f"Foreign {measure['min_clearance_mm']} mm, POWER {measure['min_power_vin_mm']} mm. "
        f"Mid short/clearance/crossing/hole "
        f"{m['shorting_items']}/{m['clearance']}/{m['tracks_crossing']}/{m['hole_clearance']}, "
        f"hole_to_hole {b['hole_to_hole']}→{m['hole_to_hole']}. "
        f"Other nets gained: {gained or 'none'}. "
        f"Full restore. No second path. No F.Cu pinch retry."
    )
    write_outputs("REVERT", stamp, before, mid, after, measure, space, reason, sha(BOARD))
    print(reason, flush=True)


if __name__ == "__main__":
    main()
