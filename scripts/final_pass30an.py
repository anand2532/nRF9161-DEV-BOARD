#!/usr/bin/env python3
"""pass30an — ONE attempt: replay the pass30am VDD_GPIO route with the
horizontal moved north from y=7.300 to y=7.050 (or y=6.800 if 7.050 is
still short of 0.20 mm to D3.1 / other POWER/VIN copper).

Geometry (0.18 mm, F.Cu, no via), corners otherwise unchanged:
  (71.300, 8.000) -> (71.300, y) -> (77.300, y)
  -> (81.500, 13.500) -> (86.510, 26.000)

Do not place copper if even y=6.800 cannot make 0.20 mm. Do not go
north of y=6.800.

KEEP if VDD_GPIO opens drop, no other non-GND net gains an open, and
short/clearance/crossing/hole_clearance are 0. Extra GND zone islands
are waived. hole_to_hole must not increase. Else FULL REVERT.
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
BACKUP = ROOT / ".mcp-backups/pass30an/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18
CLEAR_MIN = 0.20
Y_PREF = 7.050
Y_LIMIT = 6.800  # furthest north allowed

POWER_FOREIGN = {
    "VDD1",
    "VDD2",
    "VDD2_MID",
    "VDD_nRF",
    "VIN",
    "VIN_F",
    "VIN_FILT",
    "VIN_IN",
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


def poly_for(y):
    return [
        (71.300, 8.000),
        (71.300, y),
        (77.300, y),
        (81.500, 13.500),
        (86.510, 26.000),
    ]


def add_track(board, net, layer, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(W))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def p015_count(board) -> int:
    return sum(
        1
        for t in board.GetTracks()
        if t.GetNetname() == "P0.15" and t.GetClass() != "PCB_VIA"
    )


def vdd_poly_ok(board) -> bool:
    tracks = [
        t
        for t in board.GetTracks()
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == "VDD_GPIO" and t.GetLayer() == F
    ]
    for (x1, y1), (x2, y2) in zip(VDD_POLY, VDD_POLY[1:]):
        if not any(track_is(t, x1, y1, x2, y2) and abs(mm(t.GetWidth()) - W) < 0.001 for t in tracks):
            return False
    return True


def dec0_bridge_ok(board) -> bool:
    for t in board.GetTracks():
        if t.GetNetname() == "DEC0" and t.GetLayer() == B and track_is(t, 46.950, 30.900, 48.100, 30.900):
            return True
    return False


def coex0_ok(board) -> bool:
    tracks = [t for t in board.GetTracks() if t.GetNetname() == "COEX0" and t.GetClass() != "PCB_VIA"]
    vias = [t for t in board.GetTracks() if t.GetNetname() == "COEX0" and t.GetClass() == "PCB_VIA"]
    if not any(near(mm(v.GetPosition().x), 37.0) and near(mm(v.GetPosition().y), 30.5) for v in vias):
        return False
    for (x1, y1), (x2, y2) in COEX0_B:
        if not any(t.GetLayer() == B and track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    for (x1, y1), (x2, y2) in COEX0_F:
        if not any(t.GetLayer() == F and track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    return True


def via_at(board, net, x, y) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if near(mm(t.GetPosition().x), x) and near(mm(t.GetPosition().y), y):
            return True
    return False


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
    tmp = Path("/tmp/nrf30an_drc.json")
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
        "vdd_gpio_unconnected": nongnd_counts(data).get("VDD_GPIO", 0),
        "via_dangling": vc.get("via_dangling", 0),
        "track_dangling": vc.get("track_dangling", 0),
    }
    return {"stats": stats, "data": data}


def d3_pad(board):
    for f in board.GetFootprints():
        if f.GetReference() != "D3":
            continue
        for p in f.Pads():
            if p.GetNumber() == "1" and p.GetNetname() == "VIN":
                return p
    raise SystemExit("pad D3.1 [VIN] not found")


def power_shapes(board):
    shapes = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net not in POWER_FOREIGN:
            continue
        if t.GetClass() == "PCB_VIA":
            w = t.GetWidth(F)
            sh = pcbnew.SHAPE_CIRCLE(t.GetPosition(), w // 2)
            shapes.append(
                (
                    net,
                    f"via {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                    sh,
                )
            )
        elif t.GetLayer() == F:
            sh = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
            shapes.append(
                (
                    net,
                    (
                        f"F.Cu {net} ({mm(t.GetStart().x):.3f},{mm(t.GetStart().y):.3f})"
                        f"-({mm(t.GetEnd().x):.3f},{mm(t.GetEnd().y):.3f})"
                    ),
                    sh,
                )
            )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() not in POWER_FOREIGN or not p.IsOnLayer(F):
                continue
            shapes.append(
                (
                    p.GetNetname(),
                    f"pad {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                    p.GetEffectiveShape(F),
                )
            )
    return shapes


def measure_y(board, y, shapes, pad_shape) -> dict:
    """Copper-edge clearance of the proposed route to D3.1 and other POWER/VIN.

    Measured on the track solid (width 0.18 mm) before any copper is added.
    """
    poly = poly_for(y)
    seg_shapes = []
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        seg_shapes.append(
            (
                f"({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f})",
                pcbnew.SHAPE_SEGMENT(xy(x1, y1), xy(x2, y2), pcbnew.FromMM(W)),
            )
        )
    # nudged horizontal is the second segment
    horiz = seg_shapes[1][1]
    d31 = mm(pad_shape.GetClearance(horiz))
    # also the minimum of the whole route to D3.1 (vertical/diagonal could be closer)
    d31_route = d31
    d31_where = seg_shapes[1][0]
    for name, sh in seg_shapes:
        c = mm(pad_shape.GetClearance(sh))
        if c < d31_route:
            d31_route = c
            d31_where = name

    worst = None
    worst_horiz = None
    for name, sh in seg_shapes:
        for net, desc, other in shapes:
            c = mm(other.GetClearance(sh))
            rec = (c, name, net, desc)
            if worst is None or c < worst[0]:
                worst = rec
            if name == seg_shapes[1][0] and (worst_horiz is None or c < worst_horiz[0]):
                worst_horiz = rec
    return {
        "y": y,
        "d31_horizontal_mm": round(d31, 4),
        "d31_route_mm": round(d31_route, 4),
        "d31_route_segment": d31_where,
        "d31_pad_mm": [round(mm(d3_pos_x(board)), 4), round(mm(d3_pos_y(board)), 4)],
        "min_power_vin_route_mm": None if worst is None else round(worst[0], 4),
        "min_power_vin_route": None
        if worst is None
        else {"segment": worst[1], "net": worst[2], "item": worst[3]},
        "min_power_vin_horizontal_mm": None if worst_horiz is None else round(worst_horiz[0], 4),
        "min_power_vin_horizontal": None
        if worst_horiz is None
        else {"net": worst_horiz[2], "item": worst_horiz[3]},
        "meets_0_20": d31 >= CLEAR_MIN - 1e-6
        and d31_route >= CLEAR_MIN - 1e-6
        and (worst is None or worst[0] >= CLEAR_MIN - 1e-6),
    }


def d3_pos_x(board):
    return d3_pad(board).GetPosition().x


def d3_pos_y(board):
    return d3_pad(board).GetPosition().y


def apply_route(board, y):
    net = board.FindNet("VDD_GPIO")
    if net is None:
        raise SystemExit("VDD_GPIO net missing")
    poly = poly_for(y)
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        add_track(board, net, F, x1, y1, x2, y2)


def segment_rows(y):
    rows = []
    poly = poly_for(y) if y is not None else poly_for(Y_PREF)
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        rows.append({"layer": "F.Cu", "width_mm": W, "start": [x1, y1], "end": [x2, y2]})
    return rows


def protect_ok(board) -> bool:
    return (
        p015_count(board) == 42
        and vdd_poly_ok(board)
        and dec0_bridge_ok(board)
        and coex0_ok(board)
        and via_at(board, "P0.10", 47.0, 28.5)
        and via_at(board, "P0.12", 47.0, 27.5)
    )


def write_outputs(decision, info, before_stats, after_stats, gained, reason, keep, measure, mid_stats):
    ts = ist_now()
    y = measure.get("chosen_y")
    segs = segment_rows(y if y is not None else Y_PREF) if decision != "NO_ROUTE" else []
    if decision == "NO_ROUTE":
        segs = []
    b = before_stats
    a = after_stats
    payload = {
        "pass": "30an",
        "timestamp": ts,
        "decision": decision,
        "routed": decision != "NO_ROUTE",
        "net": "VDD_GPIO",
        "via_used": False,
        "y_used": y,
        "y_preferred": Y_PREF,
        "y_north_limit": Y_LIMIT,
        "clearance_requirement_mm": CLEAR_MIN,
        "measured_clearance_d31_mm": measure.get("d31_horizontal_mm"),
        "measure": measure,
        "gap_mm": 17.626,
        "replay_of": "pass30am",
        "change": "horizontal y=7.300 -> chosen y, vertical retied, other corners kept",
        "segments": segs,
        "segment_count": len(segs),
        "confirmed": info,
        "before": b,
        "mid": mid_stats,
        "after": a,
        "vdd_gpio_opens": {
            "before": b.get("vdd_gpio_unconnected"),
            "mid": None if not mid_stats else mid_stats.get("vdd_gpio_unconnected"),
            "after": a.get("vdd_gpio_unconnected"),
        },
        "headline_unconnected": {
            "before": b.get("unconnected_items"),
            "mid": None if not mid_stats else mid_stats.get("unconnected_items"),
            "after": a.get("unconnected_items"),
        },
        "gnd_islands": {
            "before": b.get("gnd_zone_islands"),
            "mid": None if not mid_stats else mid_stats.get("gnd_zone_islands"),
            "after": a.get("gnd_zone_islands"),
            "waived": True,
        },
        "nongnd_gained": gained,
        "hole_to_hole": {
            "before": b.get("hole_to_hole"),
            "mid": None if not mid_stats else mid_stats.get("hole_to_hole"),
            "after": a.get("hole_to_hole"),
        },
        "gate_met": keep,
        "reason": reason,
        "protect": {
            "vdd_gpio_u1_12_polyline": info.get("vdd_poly_after", info.get("vdd_poly")),
            "coex0_locked": info.get("coex0_after", info.get("coex0")),
            "dec0_bcu_bridge": info.get("dec0_after", info.get("dec0")),
            "p010_via_x47": info.get("p010_after", info.get("p010")),
            "p012_via_x47": info.get("p012_after", info.get("p012")),
            "p015_segments": {"before": info.get("p015"), "after": info.get("p015_after", info.get("p015"))},
            "u1_unmoved": True,
            "headers_unmoved": not info.get("moved"),
            "y_44_60_pocket": "not used",
            "min_x": 71.300,
            "gerbers": False,
            "git_commit": False,
        },
    }
    (REPORTS / "PASS30AN_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")

    def row(s):
        return (
            f"| {s['layer']} | ({s['start'][0]:.3f}, {s['start'][1]:.3f}) | "
            f"({s['end'][0]:.3f}, {s['end'][1]:.3f}) | {s['width_mm']:.2f} mm |"
        )

    d31 = measure.get("d31_horizontal_mm")
    lines = [
        "# PASS30AN_SUMMARY — VDD_GPIO east island, y nudge (GND islands waived)",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** VDD_GPIO",
        "**Via:** no",
        f"**y used:** {y if y is not None else 'none (no copper placed)'}",
        f"**Measured clearance to D3.1 [VIN] (75.213, 8.000), horizontal copper edge:** {d31} mm",
        f"**Requirement:** >= {CLEAR_MIN:.2f} mm to D3.1 and every other POWER/VIN copper",
        f"**Segments:** {len(segs)} (limit 6)",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**VDD_GPIO opens:** {b.get('vdd_gpio_unconnected')} → {a.get('vdd_gpio_unconnected')}",
        f"**GND zone islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (increase WAIVED)",
        "",
        "## Why this attempt",
        "",
        "Replay of the reverted pass30am VDD_GPIO route. That path failed because the",
        "y=7.300 horizontal was 0.135 mm from pad D3.1 [VIN] at (75.213, 8.000); POWER",
        "netclass wants 0.150 mm. This pass moves only that horizontal north, to clear",
        "0.20 mm, and reties the x=71.300 vertical. Other corners stay",
        "(71.300, 8.000), (81.500, 13.500), (86.510, 26.000). No via. No second path.",
        "The locked U1.12 polyline is not repeated. North limit is y=6.800.",
        "",
        "## Pre-commit clearance (pad geometry + 0.18 mm track)",
        "",
        "Measured with `SHAPE.GetClearance` on the solid 0.18 mm track against pad D3.1",
        "and every other F.Cu POWER/VIN track, via annular, and pad, before `board.Add`.",
        "",
        f"- Candidate y={Y_PREF:.3f}: D3.1 horizontal {measure.get('pref', {}).get('d31_horizontal_mm')} mm, "
        f"route min POWER/VIN {measure.get('pref', {}).get('min_power_vin_route_mm')} mm, "
        f"meets 0.20: {measure.get('pref', {}).get('meets_0_20')}",
        f"- Candidate y={Y_LIMIT:.3f}: "
        + (
            f"D3.1 horizontal {measure.get('limit', {}).get('d31_horizontal_mm')} mm, "
            f"route min POWER/VIN {measure.get('limit', {}).get('min_power_vin_route_mm')} mm, "
            f"meets 0.20: {measure.get('limit', {}).get('meets_0_20')}"
            if measure.get("limit")
            else "not measured (y=7.050 already met 0.20 mm)"
        ),
        f"- Chosen y: {y}",
        "",
        f"Reason: {reason}",
        "",
        "### Segments (0.18 mm)",
        "",
    ]
    if segs:
        lines += [
            "| layer | start | end | width |",
            "| --- | --- | --- | --- |",
        ]
        for s in segs:
            lines.append(row(s))
        lines.append("")
        lines.append("No via added.")
    else:
        lines.append("None. Board left untouched.")
    lines += [
        "",
        "## Gate (GND islands waived)",
        "",
    ]
    if mid_stats:
        lines += [
            f"- mid short/clear/cross/hole_clearance: "
            f"{mid_stats.get('shorting_items')}/{mid_stats.get('clearance')}/"
            f"{mid_stats.get('tracks_crossing')}/{mid_stats.get('hole_clearance')}",
            f"- mid VDD_GPIO opens: {b.get('vdd_gpio_unconnected')} → {mid_stats.get('vdd_gpio_unconnected')}",
            f"- no non-GND net gained an open: {not gained} {gained or ''}",
            f"- hole_to_hole: {b.get('hole_to_hole')} → {mid_stats.get('hole_to_hole')}",
            f"- GND islands on the attempt: {b.get('gnd_zone_islands')} → {mid_stats.get('gnd_zone_islands')} (WAIVED)",
        ]
    else:
        lines.append("- no copper committed, so the electrical gate was not run")
    lines += [
        f"- **met: {keep}**",
        "",
        "## DRC",
        "",
        "| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| before | {b.get('unconnected_items')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} | {b.get('vdd_gpio_unconnected')} |",
    ]
    if mid_stats:
        lines.append(
            f"| mid | {mid_stats.get('unconnected_items')} | {mid_stats.get('shorting_items')} | {mid_stats.get('clearance')} | {mid_stats.get('tracks_crossing')} | {mid_stats.get('hole_clearance')} | {mid_stats.get('hole_to_hole')} | {mid_stats.get('gnd_zone_islands')} | {mid_stats.get('vdd_gpio_unconnected')} |"
        )
    lines += [
        f"| after ({decision}) | {a.get('unconnected_items')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} | {a.get('vdd_gpio_unconnected')} |",
        "",
        "## Protect checklist",
        "",
        "- Locked VDD_GPIO F.Cu polyline to U1.12 still present (not the route repeated)",
        "- COEX0 via (37.000, 30.500) and the six locked segments still present",
        "- P0.10 via (47.000, 28.500) and P0.12 via (47.000, 27.500) not moved",
        "- DEC0 B.Cu bridge (46.950, 30.900)–(48.100, 30.900) not ripped",
        f"- P0.15 west wrap segment count {info.get('p015')} → {info.get('p015_after', info.get('p015'))}",
        "- Class C C22/C23/C24, P0.22, P0.19, Stage-A VDD2, SIM_IO_C/SIM_CLK_C walls not ripped",
        f"- Footprints moved: {info.get('moved') or 'none'}",
        "- y=44.60 B.Cu pocket not used",
        "- RF keepout: this route stays east of x=24.2 (min x=71.300)",
        "- No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30AN_SUMMARY.md").write_text("\n".join(lines))
    return ts


def patch_review(ts, decision, before_stats, after_stats, measure):
    text = REVIEW.read_text()
    b, a = before_stats, after_stats
    y = measure.get("chosen_y")
    d31 = measure.get("d31_horizontal_mm")
    ytxt = f"{y:.3f}" if isinstance(y, float) else "none"
    banner = (
        f"**Review date:** {ts} (Asia/Calcutta) — pass30an VDD_GPIO east "
        f"{decision} (y={ytxt}, D3.1 clearance {d31} mm; "
        f"unc {b.get('unconnected_items')}→{a.get('unconnected_items')}; "
        f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}; "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} waived). "
    )
    pre, sep, post = text.partition("**Review date:**")
    if not sep:
        raise SystemExit("review date line missing")
    rest = post.split("\n", 1)[1]
    # keep the previous review-date sentence as Prior, dropping its own '**Review date:**' prefix
    old_body = post.split("\n", 1)[0]
    # old_body begins with the timestamp; label it Prior
    text = pre + banner + "Prior: " + old_body.strip() + "\n" + rest

    delta = (
        f"**Pass delta (pass30an):** VDD_GPIO east island replay of pass30am, **{decision}**. "
        f"Same corners except the horizontal moved north off y=7.300. "
        f"Pre-commit measured clearance of the 0.18 mm horizontal to pad D3.1 [VIN] "
        f"(75.213, 8.000) is {d31} mm at y={ytxt} "
        f"(requirement 0.20 mm; y=6.800 not used"
        f"{'' if measure.get('limit') is None else ', limit was measured'}). "
        f"Segments: "
        + (
            f"(71.300, 8.000)→(71.300, {ytxt})→(77.300, {ytxt})→(81.500, 13.500)→(86.510, 26.000). "
            if decision != "NO_ROUTE"
            else "none placed. "
        )
        + f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. "
        f"Headline unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole_clearance "
        f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"Locked U1.12 polyline, COEX0, DEC0 bridge, P0.10/P0.12 x=47.0 not ripped. "
        f"No U1/header move. No y=44.60 pocket. x>24.2. No Gerbers. "
        f"Details: `reports/PASS30AN_SUMMARY.md`.\n\n"
    )
    needle = "**Pass delta (pass30am):**"
    if needle not in text:
        raise SystemExit("review doc anchor missing")
    if "**Pass delta (pass30an):**" not in text:
        text = text.replace(needle, delta + needle, 1)
    text = text.replace(
        "| **unconnected_items** | **63** | `reports/DRC_PASS30AM_AFTER.json` (live `kicad-cli` 9.0.2). pass30am REVERT: mid clearance 1 (D3.1 VIN, POWER 0.150 mm, actual 0.135 mm). VDD_GPIO opens stayed 2. GND islands 11. Prior pass30al COEX0 kept",
        f"| **unconnected_items** | **{a.get('unconnected_items')}** | `reports/DRC_PASS30AN_AFTER.json` (live `kicad-cli` 9.0.2). pass30an {decision}: VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). D3.1 clearance {d31} mm at y={ytxt}. Prior pass30am reverted",
    )
    text = text.replace(
        "| **shorting_items** | **0** | `reports/DRC_PASS30AM_AFTER.json` |",
        "| **shorting_items** | **0** | `reports/DRC_PASS30AN_AFTER.json` |",
    )
    REVIEW.write_text(text)


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if BACKUP.is_file():
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit(
                "pass30an backup exists and the live board does not match it; "
                "refusing to clobber the pre-edit or double-apply"
            )
    else:
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup hash mismatch before edit")

    print("BACKUP", sha(BACKUP)[:16], flush=True)
    before = run_drc(REPORTS / "DRC_PASS30AN_BEFORE.json")
    print("BEFORE", before["stats"], flush=True)
    if before["stats"]["unconnected_items"] != 63:
        raise SystemExit(f"expected headline 63, got {before['stats']['unconnected_items']}")

    board = pcbnew.LoadBoard(str(BOARD))
    if not protect_ok(board):
        raise SystemExit(
            f"protect confirm failed p015={p015_count(board)} vdd={vdd_poly_ok(board)} "
            f"dec0={dec0_bridge_ok(board)} coex0={coex0_ok(board)} "
            f"p010={via_at(board,'P0.10',47.0,28.5)} p012={via_at(board,'P0.12',47.0,27.5)}"
        )
    u1 = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    if not near(mm(u1.GetPosition().x), 36.0) or not near(mm(u1.GetPosition().y), 32.0):
        raise SystemExit("U1 moved before edit; refusing")
    if not via_at(board, "VDD_GPIO", 71.3, 8.0):
        raise SystemExit("start via (71.3, 8.0) missing")

    pad = d3_pad(board)
    pad_shape = pad.GetEffectiveShape(F)
    shapes = power_shapes(board)
    pref = measure_y(board, Y_PREF, shapes, pad_shape)
    print("MEASURE", Y_PREF, pref["d31_horizontal_mm"], "power", pref["min_power_vin_route_mm"], "ok", pref["meets_0_20"], flush=True)
    measure = {"pref": pref, "limit": None, "chosen_y": None, "d31_horizontal_mm": pref["d31_horizontal_mm"]}
    if pref["meets_0_20"]:
        measure["chosen_y"] = Y_PREF
        measure["d31_horizontal_mm"] = pref["d31_horizontal_mm"]
    else:
        limit = measure_y(board, Y_LIMIT, shapes, pad_shape)
        measure["limit"] = limit
        print("MEASURE", Y_LIMIT, limit["d31_horizontal_mm"], "power", limit["min_power_vin_route_mm"], "ok", limit["meets_0_20"], flush=True)
        if limit["meets_0_20"]:
            measure["chosen_y"] = Y_LIMIT
            measure["d31_horizontal_mm"] = limit["d31_horizontal_mm"]
        else:
            measure["d31_horizontal_mm"] = limit["d31_horizontal_mm"]

    fp_before = footprint_xy(board)
    info = {
        "u1": {"x": round(mm(u1.GetPosition().x), 3), "y": round(mm(u1.GetPosition().y), 3)},
        "p015": p015_count(board),
        "vdd_poly": vdd_poly_ok(board),
        "dec0": dec0_bridge_ok(board),
        "coex0": coex0_ok(board),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "moved": [],
    }

    y = measure["chosen_y"]
    if y is None:
        # no copper. after DRC is the untouched board.
        shutil.copy2(REPORTS / "DRC_PASS30AN_BEFORE.json", REPORTS / "DRC_PASS30AN_AFTER.json")
        # no separate mid; copy before so the artifact exists and matches the board
        shutil.copy2(REPORTS / "DRC_PASS30AN_BEFORE.json", REPORTS / "DRC_PASS30AN_MID.json")
        reason = (
            f"NO ROUTE. y={Y_PREF:.3f} D3.1 clearance {pref['d31_horizontal_mm']} mm "
            f"(POWER/VIN route min {pref['min_power_vin_route_mm']} mm); "
            f"y={Y_LIMIT:.3f} D3.1 clearance {measure['limit']['d31_horizontal_mm']} mm "
            f"(POWER/VIN route min {measure['limit']['min_power_vin_route_mm']} mm). "
            f"Neither meets {CLEAR_MIN:.2f} mm. Board untouched. One attempt, no copper left."
        )
        ts = write_outputs("NO_ROUTE", info, before["stats"], before["stats"], {}, reason, False, measure, None)
        patch_review(ts, "NO_ROUTE", before["stats"], before["stats"], measure)
        print("NO_ROUTE", reason, flush=True)
        return

    apply_route(board, y)
    info["p015_after"] = p015_count(board)
    info["vdd_poly_after"] = vdd_poly_ok(board)
    info["dec0_after"] = dec0_bridge_ok(board)
    info["coex0_after"] = coex0_ok(board)
    info["p010_after"] = via_at(board, "P0.10", 47.0, 28.5)
    info["p012_after"] = via_at(board, "P0.12", 47.0, 27.5)
    fp_after = footprint_xy(board)
    moved = sorted(ref for ref in fp_before if fp_before[ref] != fp_after.get(ref))
    info["moved"] = moved
    if (
        info["p015_after"] != 42
        or not info["vdd_poly_after"]
        or not info["dec0_after"]
        or not info["coex0_after"]
        or not info["p010_after"]
        or not info["p012_after"]
        or moved
    ):
        shutil.copy2(BACKUP, BOARD)
        after = run_drc(REPORTS / "DRC_PASS30AN_AFTER.json")
        shutil.copy2(REPORTS / "DRC_PASS30AN_BEFORE.json", REPORTS / "DRC_PASS30AN_MID.json")
        write_outputs(
            "REVERT",
            info,
            before["stats"],
            after["stats"],
            {},
            f"geometry guard failed {info}",
            False,
            measure,
            None,
        )
        patch_review(ist_now(), "REVERT", before["stats"], after["stats"], measure)
        print("REVERT guard", info, flush=True)
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AN_MID.json")
    print("MID", mid["stats"], flush=True)
    gained = {}
    bc = nongnd_counts(before["data"])
    ac = nongnd_counts(mid["data"])
    for n in set(ac) | set(bc):
        if ac[n] > bc[n]:
            gained[n] = {"before": bc[n], "after": ac[n]}
    st = mid["stats"]
    bst = before["stats"]
    electrical = (
        st["vdd_gpio_unconnected"] < bst["vdd_gpio_unconnected"]
        and not gained
        and st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
        and st["hole_to_hole"] <= bst["hole_to_hole"]
    )
    if electrical:
        shutil.copy2(REPORTS / "DRC_PASS30AN_MID.json", REPORTS / "DRC_PASS30AN_AFTER.json")
        reason = (
            f"KEEP. Horizontal at y={y:.3f} clears D3.1 by {measure['d31_horizontal_mm']} mm "
            f"(>= {CLEAR_MIN:.2f} mm) and other POWER/VIN copper by "
            f"{(pref if y == Y_PREF else measure['limit'])['min_power_vin_route_mm']} mm. "
            f"VDD_GPIO opens {bst['vdd_gpio_unconnected']}→{st['vdd_gpio_unconnected']}. "
            f"No new short, clearance, crossing, or hole hit. No via. "
            f"Locked COEX0 and the U1.12 polyline were not ripped."
        )
        ts = write_outputs("KEEP", info, bst, st, gained, reason, True, measure, st)
        patch_review(ts, "KEEP", bst, st, measure)
        print("KEEP", st, flush=True)
        return

    shutil.copy2(BACKUP, BOARD)
    after = run_drc(REPORTS / "DRC_PASS30AN_AFTER.json")
    reason = (
        f"REVERT. y={y:.3f}, D3.1 clearance {measure['d31_horizontal_mm']} mm. "
        f"VDD_GPIO {bst['vdd_gpio_unconnected']}→{st['vdd_gpio_unconnected']}, "
        f"gained={gained}, short/clear/cross/hole "
        f"{st['shorting_items']}/{st['clearance']}/{st['tracks_crossing']}/{st['hole_clearance']}, "
        f"hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}, "
        f"GND islands {bst['gnd_zone_islands']}→{st['gnd_zone_islands']} (waived, not the revert reason). "
        f"Full restore."
    )
    ts = write_outputs("REVERT", info, bst, after["stats"], gained, reason, False, measure, st)
    patch_review(ts, "REVERT", bst, after["stats"], measure)
    print("REVERT", reason, flush=True)


if __name__ == "__main__":
    main()
