#!/usr/bin/env python3
"""pass30aq — ONE attempt: close P0.31 only.

Island A pad J13.16 and island B pad J11.2 are both single PTH pads.
The straight F.Cu line is not used: it hits locked P0.22, the GND via at
(110, 50), locked VDD_GPIO, and locked P0.04.

This jog stays on F.Cu, 0.18 mm, six segments, no via:
west of J14, north of J14.1, east of J14, north of the VDD_GPIO trunk at
y=51.08, south of the P0.04 corner at (113.8, 49.2), then into J11.2.
Does not rip P0.22, P0.04, VDD_GPIO, or any other locked copper.

KEEP only if P0.31 opens drop by at least 1, no other non-GND net gains an
open, short/clearance/crossing/hole_clearance are 0, pre-measured foreign
clearance is >= 0.15 mm, POWER/VIN clearance is >= 0.20 mm, and hole_to_hole
does not rise. Extra GND islands are waived. Otherwise full revert. No second
path. No P0.30.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30aq/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18
CLEAR_FOREIGN = 0.15
CLEAR_POWER = 0.20
HOLE_MIN = 0.25

# Six segments. Both ends land inside the PTH pads. No via.
POLY = [
    (102.60, 75.50),
    (103.05, 47.10),
    (106.70, 47.10),
    (106.70, 50.62),
    (114.90, 50.62),
    (114.90, 48.80),
    (115.55, 48.80),
]

POWER_FOREIGN = {
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

VDD_POLY = [
    (40.170, 19.126),
    (40.170, 20.200),
    (45.900, 20.200),
    (45.900, 25.400),
    (47.550, 25.400),
    (47.550, 31.500),
    (44.000, 31.500),
]
Y7050 = [
    (71.300, 8.000),
    (71.300, 7.050),
    (77.300, 7.050),
    (81.500, 13.500),
    (86.510, 26.000),
]
AP_POLY = [
    (76.4375, 39.050),
    (76.4375, 41.550),
    (74.438, 43.050),
    (72.438, 43.050),
    (71.938, 42.050),
    (70.438, 41.550),
    (54.438, 61.050),
    (54.438, 63.550),
    (58.200, 62.700),
]
COEX0_B = [
    ((31.110, 22.000), (32.250, 22.000)),
    ((32.250, 22.000), (32.250, 30.500)),
    ((32.250, 30.500), (37.000, 30.500)),
]
COEX0_F = [
    ((37.000, 30.500), (37.000, 35.900)),
    ((37.000, 35.900), (38.750, 35.900)),
    ((38.750, 35.900), (38.750, 37.250)),
]


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def near(a, b, tol=0.02) -> bool:
    return abs(a - b) < tol


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ends(t):
    return (mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y))


def track_is(t, x1, y1, x2, y2) -> bool:
    a, b, c, d = ends(t)
    return (near(a, x1) and near(b, y1) and near(c, x2) and near(d, y2)) or (
        near(a, x2) and near(b, y2) and near(c, x1) and near(d, y1)
    )


def poly_ok(board, pts, net, layer) -> bool:
    tracks = [
        t
        for t in board.GetTracks()
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == net and t.GetLayer() == layer
    ]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if not any(track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    return True


def via_at(board, net, x, y) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if near(mm(t.GetPosition().x), x) and near(mm(t.GetPosition().y), y):
            return True
    return False


def p015_count(board) -> int:
    return sum(1 for t in board.GetTracks() if t.GetNetname() == "P0.15" and t.GetClass() != "PCB_VIA")


def footprint_xy(board) -> dict:
    out = {}
    for f in board.GetFootprints():
        out[f.GetReference()] = (
            round(mm(f.GetPosition().x), 4),
            round(mm(f.GetPosition().y), 4),
            round(f.GetOrientationDegrees(), 3),
        )
    return out


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
    tmp = Path("/tmp/nrf30aq_drc.json")
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
        "p031_unconnected": nongnd_counts(data).get("P0.31", 0),
        "vdd_gpio_unconnected": nongnd_counts(data).get("VDD_GPIO", 0),
    }
    return {"stats": stats, "data": data}


def foreign_shapes(board):
    shapes = []
    holes = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.31":
            continue
        if t.GetClass() == "PCB_VIA":
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(F) // 2),
                    net in POWER_FOREIGN,
                    f"via {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                )
            )
            holes.append(
                (
                    pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetDrill() // 2),
                    f"viahole {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                    mm(t.GetPosition().x),
                    mm(t.GetPosition().y),
                )
            )
        elif t.GetLayer() == F:
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth()),
                    net in POWER_FOREIGN,
                    (
                        f"F.Cu {net} ({mm(t.GetStart().x):.3f},{mm(t.GetStart().y):.3f})"
                        f"-({mm(t.GetEnd().x):.3f},{mm(t.GetEnd().y):.3f})"
                    ),
                )
            )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(F) or p.GetNetname() == "P0.31":
                continue
            shapes.append(
                (
                    p.GetNetname(),
                    p.GetEffectiveShape(F),
                    p.GetNetname() in POWER_FOREIGN,
                    f"pad {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                )
            )
            if p.GetDrillSize().x:
                holes.append(
                    (
                        pcbnew.SHAPE_CIRCLE(p.GetPosition(), p.GetDrillSize().x // 2),
                        f"hole {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                        mm(p.GetPosition().x),
                        mm(p.GetPosition().y),
                    )
                )
    return shapes, holes


def measure_poly(shapes, holes) -> dict:
    per = []
    min_any = None
    min_pwr = None
    min_hole = None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        sh = pcbnew.SHAPE_SEGMENT(xy(x1, y1), xy(x2, y2), pcbnew.FromMM(W))
        worst = None
        pwr = None
        for net, other, isp, desc in shapes:
            c = mm(sh.GetClearance(other))
            rec = (c, net, desc)
            if worst is None or c < worst[0]:
                worst = rec
            if isp and (pwr is None or c < pwr[0]):
                pwr = rec
        hworst = None
        minx, maxx = min(x1, x2) - 3, max(x1, x2) + 3
        miny, maxy = min(y1, y2) - 3, max(y1, y2) + 3
        for circ, desc, hx, hy in holes:
            if hx < minx or hx > maxx or hy < miny or hy > maxy:
                continue
            c = mm(sh.GetClearance(circ))
            if hworst is None or c < hworst[0]:
                hworst = (c, desc)
        row = {
            "start": [x1, y1],
            "end": [x2, y2],
            "min_clearance_mm": None if worst is None else round(worst[0], 4),
            "min_item": None if worst is None else {"net": worst[1], "item": worst[2]},
            "min_power_mm": None if pwr is None else round(pwr[0], 4),
            "min_power_item": None if pwr is None else {"net": pwr[1], "item": pwr[2]},
            "min_hole_mm": None if hworst is None else round(hworst[0], 4),
            "min_hole_item": None if hworst is None else hworst[1],
        }
        per.append(row)
        if worst is not None and (min_any is None or worst[0] < min_any[0]):
            min_any = worst
        if pwr is not None and (min_pwr is None or pwr[0] < min_pwr[0]):
            min_pwr = pwr
        if hworst is not None and (min_hole is None or hworst[0] < min_hole[0]):
            min_hole = hworst
    return {
        "segments": per,
        "min_clearance_mm": None if min_any is None else round(min_any[0], 4),
        "min_clearance_item": None if min_any is None else {"net": min_any[1], "item": min_any[2]},
        "min_power_vin_mm": None if min_pwr is None else round(min_pwr[0], 4),
        "min_power_vin_item": None if min_pwr is None else {"net": min_pwr[1], "item": min_pwr[2]},
        "min_hole_mm": None if min_hole is None else round(min_hole[0], 4),
        "min_hole_item": None if min_hole is None else min_hole[1],
        "meets_power_0_20": min_pwr is None or min_pwr[0] >= CLEAR_POWER - 1e-6,
        "meets_foreign_0_15": min_any is None or min_any[0] >= CLEAR_FOREIGN - 1e-6,
        "meets_hole_0_25": min_hole is None or min_hole[0] >= HOLE_MIN - 1e-6,
    }


def straight_remeasure(shapes) -> dict:
    """Straight copper-edge chord from pass30ao, remeasured on the live board."""
    a = (102.501, 75.250)
    b = (115.599, 49.290)
    sh = pcbnew.SHAPE_SEGMENT(xy(*a), xy(*b), pcbnew.FromMM(W))
    hits = []
    for net, other, isp, desc in shapes:
        c = mm(sh.GetClearance(other))
        if c < CLEAR_FOREIGN:
            hits.append({"clearance_mm": round(c, 4), "net": net, "power": isp, "item": desc})
    hits.sort(key=lambda h: h["clearance_mm"])
    # keep the worst few per net
    worst = {}
    for h in hits:
        worst.setdefault(h["net"], h)
    return {
        "from": list(a),
        "to": list(b),
        "length_mm": round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5, 3),
        "worst_by_net": worst,
        "hit_count_under_0_15": len(hits),
    }


def blocker_snapshot(board) -> dict:
    want = {
        "P0.22": [
            ((104.50, 71.50), (106.50, 71.50)),
        ],
        "VDD_GPIO": [
            ((104.00, 67.08), (107.18, 67.08)),
            ((105.10, 51.08), (116.00, 51.08)),
        ],
        "P0.04": [
            ((114.80, 52.50), (108.45, 52.50)),
        ],
    }
    found = {k: [] for k in want}
    gnd_via = None
    p022_via = None
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if t.GetNetname() == "GND" and near(x, 110.0, 0.05) and near(y, 50.0, 0.05):
                gnd_via = {"xy": [round(x, 3), round(y, 3)], "od_mm": round(mm(t.GetWidth(F)), 3)}
            if t.GetNetname() == "P0.22" and near(x, 104.5, 0.05) and near(y, 71.5, 0.05):
                p022_via = {"xy": [round(x, 3), round(y, 3)], "od_mm": round(mm(t.GetWidth(F)), 3)}
            continue
        if t.GetLayer() != F:
            continue
        net = t.GetNetname()
        if net not in want:
            continue
        for (pa, pb) in want[net]:
            if track_is(t, pa[0], pa[1], pb[0], pb[1]):
                found[net].append(
                    {
                        "start": [round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)],
                        "end": [round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3)],
                        "width_mm": round(mm(t.GetWidth()), 3),
                    }
                )
    return {"tracks_found": found, "gnd_via_110_50": gnd_via, "p022_via_1045_715": p022_via}


def pad_gap(board) -> dict:
    j13 = j11 = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "J13":
            for p in fp.Pads():
                if p.GetNumber() == "16":
                    j13 = p
        if fp.GetReference() == "J11":
            for p in fp.Pads():
                if p.GetNumber() == "2":
                    j11 = p
    if j13 is None or j11 is None:
        return {"error": "pads missing"}
    gap = mm(j13.GetEffectiveShape(F).GetClearance(j11.GetEffectiveShape(F)))
    return {
        "j13_16": [round(mm(j13.GetPosition().x), 3), round(mm(j13.GetPosition().y), 3)],
        "j11_2": [round(mm(j11.GetPosition().x), 3), round(mm(j11.GetPosition().y), 3)],
        "pad_edge_gap_mm": round(gap, 3),
        "start_on_j13_16": j13.HitTest(xy(*POLY[0])),
        "end_on_j11_2": j11.HitTest(xy(*POLY[-1])),
    }


def add_route(board):
    net = board.FindNet("P0.31")
    if net is None:
        raise SystemExit("P0.31 missing")
    made = []
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(xy(x1, y1))
        tr.SetEnd(xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(F)
        tr.SetNet(net)
        board.Add(tr)
        made.append(tr)
    return made


def protect_ok(board) -> dict:
    return {
        "ap_run": poly_ok(board, AP_POLY, "VDD_GPIO", F),
        "ap_via": via_at(board, "VDD_GPIO", 76.4375, 39.050),
        "y7050": poly_ok(board, Y7050, "VDD_GPIO", F),
        "u1_12_poly": poly_ok(board, VDD_POLY, "VDD_GPIO", F),
        "dec0_bridge": any(
            t.GetNetname() == "DEC0" and t.GetLayer() == B and track_is(t, 46.950, 30.900, 48.100, 30.900)
            for t in board.GetTracks()
        ),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "coex0_runs": all(
            any(
                t.GetNetname() == "COEX0" and t.GetLayer() == B and track_is(t, a[0], a[1], b[0], b[1])
                for t in board.GetTracks()
            )
            for a, b in COEX0_B
        )
        and all(
            any(
                t.GetNetname() == "COEX0" and t.GetLayer() == F and track_is(t, a[0], a[1], b[0], b[1])
                for t in board.GetTracks()
            )
            for a, b in COEX0_F
        ),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "p015": p015_count(board),
        "p004_locked_track": any(
            t.GetNetname() == "P0.04" and t.GetLayer() == F and track_is(t, 114.80, 52.50, 108.45, 52.50)
            for t in board.GetTracks()
        ),
        "p022_locked_track": any(
            t.GetNetname() == "P0.22" and t.GetLayer() == F and track_is(t, 104.50, 71.50, 106.50, 71.50)
            for t in board.GetTracks()
        ),
    }


def write_outputs(decision, info, before_stats, after_stats, gained, reason, keep, measure, mid_stats):
    ts = ist_now()
    b = before_stats
    a = after_stats
    segs = [
        {"layer": "F.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30aq",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.31",
        "via_added": False,
        "segments": segs if placed else [],
        "segment_count": len(segs) if placed else 0,
        "attempted_segments": segs,
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "min_power_clearance_mm": measure.get("min_power_vin_mm"),
        "min_hole_clearance_mm": measure.get("min_hole_mm"),
        "measure": measure,
        "straight_line_not_used": info.get("straight"),
        "jog_around": ["P0.22", "P0.04", "VDD_GPIO", "GND via (110, 50)", "J14"],
        "blockers_remeasured": info.get("blockers"),
        "pad_gap": info.get("pad_gap"),
        "before": b,
        "mid": mid_stats,
        "after": a,
        "p031_opens": {
            "before": b.get("p031_unconnected"),
            "after": a.get("p031_unconnected"),
        },
        "unconnected": {
            "before": b.get("unconnected_items"),
            "after": a.get("unconnected_items"),
        },
        "gnd_islands": {
            "before": b.get("gnd_zone_islands"),
            "after": a.get("gnd_zone_islands"),
            "waived": True,
        },
        "nongnd_gained": gained,
        "hole_to_hole": {
            "before": b.get("hole_to_hole"),
            "after": a.get("hole_to_hole"),
        },
        "gate_met": keep,
        "reason": reason,
        "protect": info.get("protect"),
    }
    (REPORTS / "PASS30AQ_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")

    def fmt_segs():
        if not placed:
            return "_none placed_"
        lines = [
            "| layer | start | end | width |",
            "| --- | --- | --- | --- |",
        ]
        for s in segs:
            lines.append(
                f"| F.Cu | ({s['start'][0]:.2f}, {s['start'][1]:.2f}) | "
                f"({s['end'][0]:.2f}, {s['end'][1]:.2f}) | 0.18 mm |"
            )
        return "\n".join(lines)

    md = f"""# PASS30AQ_SUMMARY — P0.31

**Timestamp:** {ts}
**KiCad:** 9.0.2
**Decision:** **{decision}**
**Net:** P0.31
**Via added:** no
**Segments:** {len(segs) if placed else 0} (limit 8)
**Min foreign clearance (pre-Add, copper edge):** {measure.get('min_clearance_mm')} mm vs {measure.get('min_clearance_item')} (need ≥ 0.15)
**Min POWER/VIN clearance (pre-Add):** {measure.get('min_power_vin_mm')} mm vs {measure.get('min_power_vin_item')} (need ≥ 0.20)
**Min hole clearance (pre-Add):** {measure.get('min_hole_mm')} mm vs {measure.get('min_hole_item')} (DRC ≥ 0.25)
**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}
**P0.31 opens:** {b.get('p031_unconnected')} → {a.get('p031_unconnected')}
**GND zone islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)
**Short / clearance / crossing / hole_clearance:** {a.get('shorting_items')} / {a.get('clearance')} / {a.get('tracks_crossing')} / {a.get('hole_clearance')}
**hole_to_hole:** {b.get('hole_to_hole')} → {a.get('hole_to_hole')}

## Why this path

Straight F.Cu between pad J13.16 and pad J11.2 is not used. Remeasured blockers still sit on that chord (pad-edge gap {info.get('pad_gap')}): P0.22 via and F.Cu (104.50, 71.50)–(106.50, 71.50), GND via (110, 50), VDD_GPIO F.Cu (104.00, 67.08)–(107.18, 67.08) and (105.10, 51.08)–(116.00, 51.08), P0.04 F.Cu (114.80, 52.50)–(108.45, 52.50). Straight-line hits under 0.15 mm: {json.dumps(info.get('straight', {}).get('worst_by_net'), indent=2)}

The jog leaves J13.16 on the north side of the header, runs west of J14 at x=103.05 down to y=47.10 (north of J14.1), steps east to x=106.70 (east of J14, west of the P0.06 via), drops to y=50.62 (north of the locked VDD_GPIO trunk at y=51.08, south of the P0.04 corner at (113.8, 49.2), clear of the GND via at (110, 50)), runs east to x=114.90, then south and into J11.2. No trunk was ripped. No locked copper was ripped. No via. y=44.60 B.Cu pocket not used. Min x = 102.60 (east of RF keepout x=24.2).

## Segments

{fmt_segs()}

## Gate

{reason}

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | P0.31 opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | {b.get('unconnected_items')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} | {b.get('p031_unconnected')} |
| after | {a.get('unconnected_items')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} | {a.get('p031_unconnected')} |

## Protect

{json.dumps(info.get('protect'), indent=2)}

No header or U1 move. No Gerbers. No git commit. P0.30 not started.
"""
    (REPORTS / "PASS30AQ_SUMMARY.md").write_text(md)
    return ts


def patch_review(ts, decision, before_stats, after_stats, measure):
    text = REVIEW.read_text()
    b, a = before_stats, after_stats
    fr = measure.get("min_clearance_mm")
    pwr = measure.get("min_power_vin_mm")
    banner = (
        f"**Review date:** {ts} (Asia/Calcutta) — pass30aq P0.31 "
        f"{decision} (6-seg F.Cu jog around P0.22/P0.04/VDD_GPIO/J14, no via, "
        f"foreign {fr} mm, POWER {pwr} mm; unc {b.get('unconnected_items')}→{a.get('unconnected_items')}; "
        f"P0.31 opens {b.get('p031_unconnected')}→{a.get('p031_unconnected')}; "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} waived). "
    )
    pre, sep, post = text.partition("**Review date:**")
    if not sep:
        raise SystemExit("review date line missing")
    old_body = post.split("\n", 1)[0]
    rest = post.split("\n", 1)[1]
    text = pre + banner + "Prior: " + old_body.strip() + "\n" + rest
    delta = (
        f"**Pass delta (pass30aq):** P0.31 J13.16↔J11.2, **{decision}**. "
        f"Straight line not used (P0.22, GND via (110, 50), VDD_GPIO, P0.04). "
        f"Six 0.18 mm F.Cu segments, no via: west of J14, north of J14.1, "
        f"y=50.62 north of the VDD_GPIO trunk and south of the P0.04 corner, into J11.2. "
        f"Pre-Add foreign clearance {fr} mm (need 0.15), POWER/VIN {pwr} mm (need 0.20). "
        f"P0.31 opens {b.get('p031_unconnected')}→{a.get('p031_unconnected')}. "
        f"Headline unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole_clearance "
        f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"Locked VDD_GPIO (pass30ap run, y=7.050, U1.12), P0.22, P0.04, COEX0, DEC0, P0.10/P0.12 not ripped. "
        f"No U1/header move. No y=44.60 pocket. x>24.2. No P0.30. No Gerbers. "
        f"Details: `reports/PASS30AQ_SUMMARY.md`.\n\n"
    )
    needle = "**Pass delta (pass30ap):**"
    if needle not in text:
        raise SystemExit("review doc anchor missing")
    if "**Pass delta (pass30aq):**" not in text:
        text = text.replace(needle, delta + needle, 1)
    text = text.replace(
        "| **unconnected_items** | **62** | `reports/DRC_PASS30AP_AFTER.json` (live `kicad-cli` 9.0.2). pass30ap KEEP: VDD_GPIO opens 1→0. GND islands 12→12 (waived). POWER clearance 2.2373 mm. Prior pass30ao NO-ROUTE",
        f"| **unconnected_items** | **{a.get('unconnected_items')}** | `reports/DRC_PASS30AQ_AFTER.json` (live `kicad-cli` 9.0.2). pass30aq {decision}: P0.31 opens {b.get('p031_unconnected')}→{a.get('p031_unconnected')}. GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). foreign {fr} mm, POWER {pwr} mm. Prior pass30ap KEEP",
    )
    text = text.replace(
        "| **shorting_items** | **0** | `reports/DRC_PASS30AP_AFTER.json` |",
        "| **shorting_items** | **0** | `reports/DRC_PASS30AQ_AFTER.json` |",
    )
    section = (
        f"\n## Pass30aq — P0.31 jog around P0.22 / P0.04 / VDD_GPIO — {ts}\n\n"
        f"**Decision:** **{decision}**. No via. Width 0.18 mm. Segments "
        f"{6 if decision == 'KEEP' else 0}.\n\n"
        f"Straight F.Cu J13.16→J11.2 not used. Jog: (102.60, 75.50) on J13.16, "
        f"x=103.05 west of J14 to y=47.10, east to x=106.70, y=50.62 north of VDD_GPIO "
        f"and south of the P0.04 corner, east to x=114.90, into J11.2 at (115.55, 48.80).\n\n"
        f"**Foreign clearance:** {fr} mm (≥ 0.15). **POWER clearance:** {pwr} mm (≥ 0.20). "
        f"**P0.31 opens:** {b.get('p031_unconnected')}→{a.get('p031_unconnected')}. "
        f"**Unconnected:** {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"**GND islands:** {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived).\n\n"
        f"**Artifacts:** `reports/PASS30AQ_SUMMARY.{{md,json}}`, "
        f"`reports/DRC_PASS30AQ_{{BEFORE,MID,AFTER}}.json`, `scripts/final_pass30aq.py`\n"
    )
    if "## Pass30aq —" not in text:
        text = text.rstrip() + "\n" + section
    REVIEW.write_text(text)


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if BACKUP.is_file():
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("pass30aq backup exists and does not match the live board; refusing to clobber")
    else:
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup hash mismatch")

    board = pcbnew.LoadBoard(str(BOARD))
    shapes, holes = foreign_shapes(board)
    measure = measure_poly(shapes, holes)
    info = {
        "blockers": blocker_snapshot(board),
        "pad_gap": pad_gap(board),
        "straight": straight_remeasure(shapes),
        "protect_before": protect_ok(board),
        "fp": footprint_xy(board),
    }
    print("BLOCKERS", json.dumps(info["blockers"]), flush=True)
    print("PADGAP", info["pad_gap"], flush=True)
    print("STRAIGHT_WORST", json.dumps(info["straight"]["worst_by_net"]), flush=True)
    print("MEASURE", json.dumps({k: measure[k] for k in measure if k != "segments"}), flush=True)
    print("PROTECT", info["protect_before"], flush=True)

    before = run_drc(REPORTS / "DRC_PASS30AQ_BEFORE.json")
    print("BEFORE", before["stats"], flush=True)
    bst = before["stats"]

    def abort_no_copper(decision, reason):
        shutil.copy2(REPORTS / "DRC_PASS30AQ_BEFORE.json", REPORTS / "DRC_PASS30AQ_AFTER.json")
        shutil.copy2(REPORTS / "DRC_PASS30AQ_BEFORE.json", REPORTS / "DRC_PASS30AQ_MID.json")
        info["protect"] = info["protect_before"]
        # board file was never written
        if sha(BOARD) != sha(BACKUP):
            shutil.copy2(BACKUP, BOARD)
        ts = write_outputs(decision, info, bst, bst, {}, reason, False, measure, None)
        patch_review(ts, decision, bst, bst, measure)
        print(decision, reason, flush=True)

    blockers = info["blockers"]
    missing = [n for n, rows in blockers["tracks_found"].items() if not rows]
    if missing or blockers["gnd_via_110_50"] is None or blockers["p022_via_1045_715"] is None:
        abort_no_copper(
            "NO-ROUTE",
            f"Blocker remeasure missed a trunk: missing={missing} gnd_via={blockers['gnd_via_110_50']} "
            f"p022_via={blockers['p022_via_1045_715']}. No copper added.",
        )
        return
    if not info["pad_gap"].get("start_on_j13_16") or not info["pad_gap"].get("end_on_j11_2"):
        abort_no_copper("NO-ROUTE", "Endpoint is not on J13.16 / J11.2. No copper added.")
        return
    if not (
        measure["meets_foreign_0_15"] and measure["meets_power_0_20"] and measure["meets_hole_0_25"]
    ):
        abort_no_copper(
            "NO-ROUTE",
            f"Pre-Add clearance failed (foreign {measure['min_clearance_mm']} mm, "
            f"POWER {measure['min_power_vin_mm']} mm, hole {measure['min_hole_mm']} mm). No copper added.",
        )
        return
    pb = info["protect_before"]
    flags = (
        "ap_run",
        "ap_via",
        "y7050",
        "u1_12_poly",
        "dec0_bridge",
        "coex0_via",
        "coex0_runs",
        "p010",
        "p012",
        "p004_locked_track",
        "p022_locked_track",
    )
    if not all(pb[k] for k in flags):
        abort_no_copper("NO-ROUTE", f"Locked copper not in the expected state before edit: {pb}. No copper added.")
        return
    if bst.get("p031_unconnected", 0) < 1:
        abort_no_copper(
            "NO-ROUTE",
            f"P0.31 opens already {bst.get('p031_unconnected')}; nothing to close. No copper added.",
        )
        return

    add_route(board)
    pa = protect_ok(board)
    fp_after = footprint_xy(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != fp_after.get(ref))
    info["protect"] = {"before": pb, "after_add": pa, "moved": moved}
    if pa != pb or moved:
        shutil.copy2(BACKUP, BOARD)
        after = run_drc(REPORTS / "DRC_PASS30AQ_AFTER.json")
        shutil.copy2(REPORTS / "DRC_PASS30AQ_BEFORE.json", REPORTS / "DRC_PASS30AQ_MID.json")
        write_outputs(
            "REVERT",
            info,
            bst,
            after["stats"],
            {},
            f"Protect guard failed after add {pa} moved={moved}. Full restore.",
            False,
            measure,
            None,
        )
        patch_review(ist_now(), "REVERT", bst, after["stats"], measure)
        print("REVERT guard", pa, moved, flush=True)
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AQ_MID.json")
    print("MID", mid["stats"], flush=True)
    gained = {}
    bc = nongnd_counts(before["data"])
    ac = nongnd_counts(mid["data"])
    for n in set(ac) | set(bc):
        if ac[n] > bc[n]:
            gained[n] = {"before": bc[n], "after": ac[n]}
    st = mid["stats"]
    gained.pop("P0.31", None)
    drop = bst["p031_unconnected"] - st["p031_unconnected"]
    electrical = (
        drop >= 1
        and st["p031_unconnected"] == bst["p031_unconnected"] - drop
        and (bst["p031_unconnected"] != 1 or st["p031_unconnected"] == 0)
        and not gained
        and st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
        and st["hole_to_hole"] <= bst["hole_to_hole"]
        and measure["min_clearance_mm"] >= CLEAR_FOREIGN - 1e-9
        and measure["min_power_vin_mm"] >= CLEAR_POWER - 1e-9
    )
    if electrical:
        shutil.copy2(REPORTS / "DRC_PASS30AQ_MID.json", REPORTS / "DRC_PASS30AQ_AFTER.json")
        reason = (
            f"KEEP. P0.31 opens {bst['p031_unconnected']}→{st['p031_unconnected']}. "
            f"No other non-GND net gained an open. "
            f"short/clearance/crossing/hole_clearance 0. hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}. "
            f"Foreign clearance {measure['min_clearance_mm']} mm. POWER clearance {measure['min_power_vin_mm']} mm. "
            f"GND islands {bst['gnd_zone_islands']}→{st['gnd_zone_islands']} (waived)."
        )
        ts = write_outputs("KEEP", info, bst, st, gained, reason, True, measure, st)
        patch_review(ts, "KEEP", bst, st, measure)
        print("KEEP", st, flush=True)
        return

    shutil.copy2(BACKUP, BOARD)
    after = run_drc(REPORTS / "DRC_PASS30AQ_AFTER.json")
    reason = (
        f"REVERT. P0.31 {bst['p031_unconnected']}→{st['p031_unconnected']}, "
        f"gained={gained}, short/clear/cross/hole "
        f"{st['shorting_items']}/{st['clearance']}/{st['tracks_crossing']}/{st['hole_clearance']}, "
        f"hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}. "
        f"Foreign {measure['min_clearance_mm']} mm, POWER {measure['min_power_vin_mm']} mm. "
        f"Full restore. No second path."
    )
    ts = write_outputs("REVERT", info, bst, after["stats"], gained, reason, False, measure, st)
    patch_review(ts, "REVERT", bst, after["stats"], measure)
    print("REVERT", reason, flush=True)


if __name__ == "__main__":
    main()
