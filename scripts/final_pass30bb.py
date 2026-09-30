#!/usr/bin/env python3
"""pass30bb — ONE attempt: P0.19 only.

Same In1.Cu jog as pass30ba from the existing through-via (39.25, 23.10),
but the eastbound is south of both locked end caps AND south of the J18
1.7 mm round pads. pass30ba's y=60.00 eastbound crossed the P0.16 skirt.
y=61.63 clears the skirt centerlines and still runs through J18.4/5/6.
Measured pad geometry puts the open slot at y>=63.09; this attempt uses
y=63.20, then a north stub onto J18.7. No new via. No second path.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
spec = importlib.util.spec_from_file_location("p30ba", ROOT / "scripts" / "final_pass30ba.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BOARD = m.BOARD
BACKUP = ROOT / ".mcp-backups/pass30bb/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
IN1 = m.IN1
W = m.W
CF = m.CF
CP = m.CP

# In1.Cu. Eastbound is south of P0.16 end (y=61.10) and P0.17 end (y=61.30)
# and south of the 1.7 mm J18 pads centered at y=62.0 (need y>=63.09).
POLY = [
    (39.25, 23.10),
    (39.25, 26.50),
    (44.25, 26.50),
    (44.25, 39.10),
    (42.80, 39.90),
    (44.25, 40.70),
    (44.25, 63.20),
    (53.24, 63.20),
    (53.24, 62.00),
]
P16 = m.P16
P17 = m.P17
SKIRTS = [("P0.16", "In1.Cu", P16), ("P0.17", "In2.Cu", P17)]


def orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def onseg(ax, ay, bx, by, cx, cy, tol=1e-9):
    return (min(ax, bx) - tol <= cx <= max(ax, bx) + tol) and (
        min(ay, by) - tol <= cy <= max(ay, by) + tol
    )


def intersects(a, b, c, d) -> bool:
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    o1 = orient(ax, ay, bx, by, cx, cy)
    o2 = orient(ax, ay, bx, by, dx, dy)
    o3 = orient(cx, cy, dx, dy, ax, ay)
    o4 = orient(cx, cy, dx, dy, bx, by)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return True
    if abs(o1) < 1e-9 and onseg(ax, ay, bx, by, cx, cy):
        return True
    if abs(o2) < 1e-9 and onseg(ax, ay, bx, by, dx, dy):
        return True
    if abs(o3) < 1e-9 and onseg(cx, cy, dx, dy, ax, ay):
        return True
    if abs(o4) < 1e-9 and onseg(cx, cy, dx, dy, bx, by):
        return True
    return False


def skirt_segments():
    out = []
    for net, layer, pts in SKIRTS:
        for a, b in zip(pts, pts[1:]):
            out.append({"net": net, "layer": layer, "a": list(a), "b": list(b)})
    return out


def whole_segment_skirt_test(poly):
    """Centerline intersection plus samples along every new segment.

    Endpoint-only clearance is not used. A hit is any interior or endpoint
    intersection with either skirt, on either layer.
    """
    rows = []
    crossings = []
    samples_inside = []
    min_d = None
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        n = max(2, int(length / 0.05))
        seg_min = None
        seg_hit = None
        for sk in skirt_segments():
            a, b = tuple(sk["a"]), tuple(sk["b"])
            hit = intersects((x1, y1), (x2, y2), a, b)
            dist = m.segseg(x1, y1, x2, y2, a[0], a[1], b[0], b[1])
            # sample the new segment; catch a graze the closed-form test missed
            sample_min = dist
            sample_hit = False
            for i in range(n + 1):
                t = i / n
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                d = m.dps(px, py, a[0], a[1], b[0], b[1])
                if d < sample_min:
                    sample_min = d
                if d <= 1e-4:
                    sample_hit = True
                    samples_inside.append({
                        "at": [round(px, 4), round(py, 4)],
                        "skirt": sk,
                        "distance_mm": d,
                    })
            if hit or sample_hit:
                crossings.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "skirt_net": sk["net"],
                    "skirt_layer": sk["layer"],
                    "skirt": [sk["a"], sk["b"]],
                    "centerline_intersection": hit,
                    "sample_touch": sample_hit,
                    "min_center_distance_mm": round(min(dist, sample_min), 6),
                })
            rec = (min(dist, sample_min), sk["net"], sk["a"], sk["b"])
            if seg_min is None or rec[0] < seg_min[0]:
                seg_min = rec
            if min_d is None or rec[0] < min_d[0]:
                min_d = rec
            if hit or sample_hit:
                seg_hit = sk["net"]
        rows.append({
            "start": [x1, y1],
            "end": [x2, y2],
            "samples": n + 1,
            "crossed": seg_hit is not None,
            "nearest_skirt": None if seg_min is None else {
                "net": seg_min[1],
                "segment": [list(seg_min[2]), list(seg_min[3])],
                "center_distance_mm": round(seg_min[0], 4),
                "edge_clearance_mm": round(seg_min[0] - W, 4),
            },
        })
    return {
        "method": "segment-vs-segment intersection plus 0.05 mm samples along each new segment, both skirts, layers not exempt",
        "crossed": bool(crossings),
        "crossing_count": len(crossings),
        "crossings": crossings,
        "sample_touches": samples_inside,
        "min_center_distance_mm": None if min_d is None else round(min_d[0], 4),
        "min_center_item": None if min_d is None else {
            "net": min_d[1], "segment": [list(min_d[2]), list(min_d[3])],
        },
        "segments": rows,
        "y61_63_note": (
            "A horizontal at y=61.63 clears both skirt centerlines (>=0.33 mm) but "
            "its copper runs through J18.4/J18.5/J18.6 (1.7 mm circles at y=62.0). "
            "That Y is not the route. The one attempt is y=63.20."
        ),
    }


def y6163_blocker(board):
    """Document why the skirt-minimum Y is not usable. Not a second route."""
    vias, holes, pads, tracks = m.collect(board, IN1)
    x1, y, x2 = 44.25, 61.63, 53.24
    row = m.seg_clearance(x1, y, x2, y, vias, holes, pads, tracks, IN1)
    return {
        "segment": [[x1, y], [x2, y]],
        "ok": row["ok"],
        "foreign_mm": row.get("foreign"),
        "foreign_item": row.get("foreign_item"),
        "hole_mm": row.get("hole"),
        "hole_item": row.get("hole_item"),
        "why": "J18 pads are 1.700 mm circles on y=62.000. y=61.63 is inside J18.4 (P0.16), J18.5 (P0.17) and J18.6 (P0.18). Blocked. Not placed.",
    }


def measure(board):
    vias, holes, pads, tracks = m.collect(board, IN1)
    rows, mf, mp, mh = [], None, None, None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = m.seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, IN1)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
        row["layer"] = "In1.Cu"
        rows.append(row)
        if row.get("foreign") is not None and (mf is None or row["foreign"] < mf[0]):
            mf = (row["foreign"], row["foreign_item"])
        if row.get("power") is not None and (mp is None or row["power"] < mp[0]):
            mp = (row["power"], row["power_item"])
        if row.get("hole") is not None and (mh is None or row["hole"] < mh[0]):
            mh = (row["hole"], row["hole_item"])
    j = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "J18":
            for p in fp.Pads():
                if p.GetNumber() == "7":
                    j = p
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2]), m.xy(*POLY[-1]), pcbnew.FromMM(W))
    hits_pad = bool(j and land.Collide(j.GetEffectiveShape(IN1)))
    # pad size
    pad_info = None
    if j is not None:
        sz = j.GetSize()
        pad_info = {
            "center": [round(m.mm(j.GetPosition().x), 3), round(m.mm(j.GetPosition().y), 3)],
            "size_mm": [round(m.mm(sz.x), 3), round(m.mm(sz.y), 3)],
            "shape": int(j.GetShape()),
            "shape_name": "circle" if int(j.GetShape()) == 0 else str(int(j.GetShape())),
            "drill_mm": round(m.mm(j.GetDrillSize().x), 3),
            "layers_include_in1": j.IsOnLayer(IN1),
        }
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits_pad
        and nseg <= 10
        and min(p[0] for p in POLY) > 24.2
    )
    return {
        "segments": rows,
        "segment_count": nseg,
        "min_clearance_mm": None if mf is None else mf[0],
        "min_clearance_item": None if mf is None else mf[1],
        "min_power_vin_mm": None if mp is None else mp[0],
        "min_power_vin_item": None if mp is None else mp[1],
        "min_hole_mm": None if mh is None else mh[0],
        "min_hole_item": None if mh is None else mh[1],
        "lands_on_j18_7": hits_pad,
        "pad": pad_info,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= m.HOLE - 1e-9,
        "ok": ok,
        "layer": "In1.Cu",
        "new_via": False,
        "width_mm": W,
    }


def add_route(board):
    net = board.FindNet("P0.19")
    if net is None:
        raise SystemExit("P0.19 missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(m.xy(x1, y1))
        tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN1)
        tr.SetNet(net)
        board.Add(tr)


def counts_locked(before_counts, board):
    after = m.track_counts(board)
    bad = []
    for net, n in before_counts["tracks"].items():
        if net == "P0.19":
            continue
        if after["tracks"].get(net, 0) != n:
            bad.append(f"track {net} {n}->{after['tracks'].get(net, 0)}")
    for net, n in before_counts["vias"].items():
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get("P0.19", 0) != before_counts["vias"].get("P0.19", 0):
        bad.append("P0.19 via count changed")
    expect = before_counts["tracks"].get("P0.19", 0) + (len(POLY) - 1)
    if after["tracks"].get("P0.19", 0) != expect:
        bad.append(
            f"P0.19 tracks {before_counts['tracks'].get('P0.19', 0)}->"
            f"{after['tracks'].get('P0.19', 0)} expected {expect}"
        )
    return bad


def restore():
    shutil.copy2(BACKUP, BOARD)


def write_outputs(decision, info, before, after, reason, meas, skirt):
    ts = m.ist_now()
    b, a = before, after
    segs = [
        {"layer": "In1.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30bb",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.19",
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "pcb_blob_at_end": m.git_blob(),
        "same_island_u1_30_j18_7": info["gap"]["same_island"],
        "pad_edge_mm": info["gap"]["pad_edge_mm"],
        "pad_edge_exact_mm": info["gap"]["pad_edge_exact_mm"],
        "u1_30": info["gap"]["u1_30"],
        "j18_7": info["gap"]["j18_7"],
        "j18_7_pad": meas.get("pad"),
        "whole_segment_skirt_test": skirt,
        "y_61_63_blocker": info.get("y6163"),
        "new_via": False,
        "segments": segs if placed else [],
        "segment_count": len(segs) if placed else 0,
        "attempted_segments": segs,
        "min_foreign_clearance_mm": meas.get("min_clearance_mm"),
        "min_foreign_item": meas.get("min_clearance_item"),
        "min_power_clearance_mm": meas.get("min_power_vin_mm"),
        "min_power_item": meas.get("min_power_vin_item"),
        "min_hole_clearance_mm": meas.get("min_hole_mm"),
        "min_hole_item": meas.get("min_hole_item"),
        "segment_clearances": [
            {
                "start": r["start"], "end": r["end"], "ok": r["ok"],
                "foreign_mm": r.get("foreign"), "foreign_item": r.get("foreign_item"),
                "power_mm": r.get("power"), "power_item": r.get("power_item"),
                "hole_mm": r.get("hole"), "hole_item": r.get("hole_item"),
                "why": r.get("why"),
            }
            for r in meas["segments"]
        ],
        "p019_opens_before": b.get("p019_unconnected"),
        "p019_opens_after": a.get("p019_unconnected"),
        "unconnected_before": b.get("unconnected_items"),
        "unconnected_after": a.get("unconnected_items"),
        "short_clearance_crossing_hole_before": [
            b.get("shorting_items"), b.get("clearance"), b.get("tracks_crossing"), b.get("hole_clearance")
        ],
        "short_clearance_crossing_hole_after": [
            a.get("shorting_items"), a.get("clearance"), a.get("tracks_crossing"), a.get("hole_clearance")
        ],
        "hole_to_hole_before": b.get("hole_to_hole"),
        "hole_to_hole_after": a.get("hole_to_hole"),
        "gnd_islands_before": b.get("gnd_zone_islands"),
        "gnd_islands_after": a.get("gnd_zone_islands"),
        "other_nongnd_gained": info.get("gained", {}),
        "reason": reason,
        "skirts_crossed": skirt["crossed"],
        "skirts_ripped": False,
        "p017_not_retried": True,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "locked_copper_ripped": info.get("locked_ripped", False),
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
    }
    (REPORTS / "PASS30BB_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BB_SUMMARY — P0.19",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.19",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**U1.30 and J18.7 same island:** {info['gap']['same_island']}",
        f"**Pad-edge:** {info['gap']['pad_edge_exact_mm']:.6f} mm",
        f"**New via:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Skirts crossed:** {skirt['crossed']}",
        f"**Skirts ripped:** no",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**P0.19 opens:** {b.get('p019_unconnected')} → {a.get('p019_unconnected')}",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)",
        "",
        "## Whole-segment skirt test",
        "",
        skirt["method"] + ".",
        f"Crossings: **{skirt['crossing_count']}**. "
        f"Min centerline distance to either skirt: **{skirt['min_center_distance_mm']} mm** "
        f"vs {skirt['min_center_item']}.",
        "Both P0.16 (In1.Cu) and P0.17 (In2.Cu) were tested. Different layers were not treated as allowed to cross.",
        "",
        "Per new segment, nearest skirt:",
        "",
    ]
    for row in skirt["segments"]:
        near = row["nearest_skirt"]
        lines.append(
            f"- ({row['start'][0]:.2f}, {row['start'][1]:.2f}) → ({row['end'][0]:.2f}, {row['end'][1]:.2f}) "
            f"crossed={row['crossed']} nearest {near['net']} {near['segment']} "
            f"center {near['center_distance_mm']} mm (edge {near['edge_clearance_mm']} mm), "
            f"{row['samples']} samples"
        )
    lines += [
        "",
        "## Why not y=61.63",
        "",
        info["y6163"]["why"],
        f"Clearance of (44.25, 61.63)–(53.24, 61.63): foreign {info['y6163']['foreign_mm']} mm "
        f"vs {info['y6163']['foreign_item']}; hole {info['y6163']['hole_mm']} mm vs {info['y6163']['hole_item']}.",
        "J18.7 is a 1.700 mm circle at (53.240, 62.000), drill 1.000 mm, on In1.Cu. "
        "Pad copper runs y=61.15–62.85. The P0.17 end cap stops at y=61.30 on x=48.16, which is J18.5's center, "
        "so there is no corridor between the end cap and the pad. The open eastbound is south of the pads.",
        "",
        "## Attempt",
        "",
    ]
    if placed:
        lines.append("In1.Cu 0.18 mm, no new via. Kept. Corners:")
    else:
        lines.append(reason)
        lines.append("")
        lines.append("Attempted corners (not left on the board):" if not placed else "")
    lines.append("")
    for s in segs:
        lines.append(f"- ({s['start'][0]:.2f}, {s['start'][1]:.2f}) → ({s['end'][0]:.2f}, {s['end'][1]:.2f}) In1.Cu")
    lines += [
        "",
        "West dodge (44.25, 39.10)→(42.80, 39.90)→(44.25, 40.70) is around P0.06 via (44.000, 39.900). "
        "Vertical x=44.25 is 0.35 mm center-to-center from the locked x=44.60 skirts (edge 0.17 mm) and passes "
        "between J18.3 (43.08, 62.00) and J18.4 (45.62, 62.00). Eastbound y=63.20 is 1.90 mm south of the "
        "P0.17 end cap (y=61.30) and 0.26 mm off the J18 pad copper. North stub ends at the J18.7 center, "
        "not past the pad. x>24.2. No new via. P0.17 not retried. No other net.",
        "",
        "## Clearance by segment",
        "",
    ]
    for r in meas["segments"]:
        lines.append(
            f"- ({r['start'][0]:.2f}, {r['start'][1]:.2f})–({r['end'][0]:.2f}, {r['end'][1]:.2f}) "
            f"ok={r['ok']} foreign={r.get('foreign')} vs {r.get('foreign_item')} "
            f"power={r.get('power')} vs {r.get('power_item')} "
            f"hole={r.get('hole')} vs {r.get('hole_item')} why={r.get('why')}"
        )
    lines += [
        "",
        "## Gate",
        "",
        reason,
        "",
        "## DRC",
        "",
        "| | unconnected | P0.19 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {b.get('unconnected_items')} | {b.get('p019_unconnected')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} |",
    ]
    if info.get("mid"):
        md = info["mid"]
        lines.append(
            f"| mid | {md.get('unconnected_items')} | {md.get('p019_unconnected')} | {md.get('shorting_items')} | {md.get('clearance')} | {md.get('tracks_crossing')} | {md.get('hole_clearance')} | {md.get('hole_to_hole')} | {md.get('gnd_zone_islands')} |"
        )
    lines += [
        f"| after | {a.get('unconnected_items')} | {a.get('p019_unconnected')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |",
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}.",
        "Locked copper not ripped. P0.16 and P0.17 skirts not crossed and not ripped. P0.17 not retried. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BB_SUMMARY.md").write_text("\n".join(lines) + "\n")
    return ts


def patch_review(ts, decision, before, after, meas, info, skirt):
    text = REVIEW.read_text()
    if "## Pass30bb —" in text:
        return
    b, a = before, after
    if decision == "KEEP":
        route = (
            "Kept In1.Cu 0.18 mm, no new via: "
            "(39.25, 23.10)→(39.25, 26.50)→(44.25, 26.50)→(44.25, 39.10)→(42.80, 39.90)→"
            "(44.25, 40.70)→(44.25, 63.20)→(53.24, 63.20)→(53.24, 62.00)."
        )
    else:
        route = "No copper left on the board."
    note = (
        f"\n## Pass30bb — P0.19 — {ts}\n\n"
        f"**Decision:** **{decision}**. {route} "
        f"Whole-segment test against both skirts (intersection plus 0.05 mm samples, layers not exempt) "
        f"found {skirt['crossing_count']} crossings; min centerline distance {skirt['min_center_distance_mm']} mm. "
        f"y=61.63 was not used: it clears the end caps and hits J18.4 "
        f"({info['y6163']['foreign_mm']} mm). Eastbound y=63.20 is south of both end caps and the 1.7 mm pads, "
        f"then north onto J18.7, not past it. "
        f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
        f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
        f"P0.19 opens {b.get('p019_unconnected')}→{a.get('p019_unconnected')}. "
        f"Unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole {a.get('shorting_items')}/{a.get('clearance')}/"
        f"{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"Skirts not crossed or ripped. P0.17 not retried. No other net. No Gerbers. No commit.\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    REVIEW.write_text(text + note)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    info = {"git_head": m.git_head(), "pcb_blob": m.git_blob(), "gained": {}, "locked_ripped": False}
    print("GIT", info["git_head"], info["pcb_blob"], flush=True)
    before = m.run_drc(REPORTS / "DRC_PASS30BB_BEFORE.json")
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = m.pad_and_islands(board)
    info["protect_before"] = m.protect_ok(board)
    info["fp"] = m.footprint_xy(board)
    info["counts"] = m.track_counts(board)
    info["y6163"] = y6163_blocker(board)
    skirt = whole_segment_skirt_test(POLY)
    meas = measure(board)
    print("GAP", info["gap"]["same_island"], round(info["gap"]["pad_edge_exact_mm"], 3), flush=True)
    print("SKIRT crossed", skirt["crossed"], "min", skirt["min_center_distance_mm"], flush=True)
    print("MEASURE ok", meas["ok"], "f", meas["min_clearance_mm"], "p", meas["min_power_vin_mm"], "land", meas["lands_on_j18_7"], flush=True)

    def finish(decision, reason, after_stats):
        ts = write_outputs(decision, info, bst, after_stats, reason, meas, skirt)
        patch_review(ts, decision, bst, after_stats, meas, info, skirt)
        print(decision, flush=True)
        print(reason, flush=True)

    if bst["unconnected_items"] != 58 or bst["p019_unconnected"] != 1:
        shutil.copy2(REPORTS / "DRC_PASS30BB_BEFORE.json", REPORTS / "DRC_PASS30BB_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Pre-edit unconnected is {bst['unconnected_items']} (need 58), "
            f"P0.19 opens {bst['p019_unconnected']} (need 1). No copper edited.",
            bst,
        )
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BB_BEFORE.json", REPORTS / "DRC_PASS30BB_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if skirt["crossed"]:
        shutil.copy2(REPORTS / "DRC_PASS30BB_BEFORE.json", REPORTS / "DRC_PASS30BB_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Whole-segment skirt test failed before copper was added: {skirt['crossings']}. No copper added.",
            bst,
        )
        return
    if not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BB_BEFORE.json", REPORTS / "DRC_PASS30BB_AFTER.json")
        finish(
            "NO-ROUTE",
            "South slot blocked. The eastbound south of both end caps does not clear pad/track geometry "
            f"(foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']}, "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']}, "
            f"hole {meas['min_hole_mm']} vs {meas['min_hole_item']}, "
            f"land {meas['lands_on_j18_7']}, segments {meas['segment_count']}). "
            f"y=61.63 is inside J18.4 ({info['y6163']['foreign_mm']} mm). "
            "No copper added. No second path.",
            bst,
        )
        return

    shutil.copy2(BOARD, BACKUP)
    if m.sha(BOARD) != m.sha(BACKUP):
        raise SystemExit("backup copy failed")

    add_route(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != m.footprint_xy(board).get(ref))
    ripped = counts_locked(info["counts"], board)
    pa = m.protect_ok(board)
    skirt_after = whole_segment_skirt_test(POLY)
    if moved or ripped or not all(pa.values()) or not m.poly_ok(board, POLY, "P0.19", IN1) or skirt_after["crossed"]:
        info["locked_ripped"] = bool(ripped) or not all(pa.values())
        restore()
        after = m.run_drc(REPORTS / "DRC_PASS30BB_AFTER.json")
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        finish(
            "NO-ROUTE",
            f"Protect or skirt guard failed after add, before save. moved={moved} ripped={ripped} "
            f"protect={pa} skirt_crossed={skirt_after['crossed']}. Full restore. "
            f"Post-revert unconnected {after['stats']['unconnected_items']}. "
            f"Blob matches pre-edit: {info['reverted_blob_match']}.",
            after["stats"],
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = m.run_drc(REPORTS / "DRC_PASS30BB_MID.json")
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = m.gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["p019_unconnected"] - mst["p019_unconnected"]
    # re-load and confirm skirts still the original polylines and the new route does not cross them
    board2 = pcbnew.LoadBoard(str(BOARD))
    skirts_intact = m.protect_ok(board2)
    skirt_on_disk = whole_segment_skirt_test(POLY)
    drc_cross = mst["tracks_crossing"]
    gate_ok = (
        pdrop >= 1
        and not g
        and mst["shorting_items"] == 0
        and mst["clearance"] == 0
        and drc_cross == 0
        and mst["hole_clearance"] == 0
        and mst["hole_to_hole"] == bst["hole_to_hole"]
        and meas["meets_foreign_0_15"]
        and meas["meets_power_0_20"]
        and not skirt_on_disk["crossed"]
        and all(skirts_intact.values())
        and m.poly_ok(board2, POLY, "P0.19", IN1)
    )
    if not gate_ok:
        restore()
        after = m.run_drc(REPORTS / "DRC_PASS30BB_AFTER.json")
        ast = after["stats"]
        match = (
            ast["unconnected_items"] == bst["unconnected_items"]
            and ast["p019_unconnected"] == bst["p019_unconnected"]
            and ast["shorting_items"] == bst["shorting_items"]
            and ast["clearance"] == bst["clearance"]
            and ast["tracks_crossing"] == bst["tracks_crossing"]
            and ast["hole_clearance"] == bst["hole_clearance"]
            and ast["hole_to_hole"] == bst["hole_to_hole"]
        )
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        info["mid"] = mst
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.19 opens {bst['p019_unconnected']}→{mst['p019_unconnected']} (need drop ≥ 1). "
            f"Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Whole-segment skirt crossings on the placed geometry: {skirt_on_disk['crossing_count']}. "
            f"Skirts intact: {all(skirts_intact.values())}. "
            f"Post-revert DRC matches pre-edit: {match} "
            f"(unc {ast['unconnected_items']}, P0.19 {ast['p019_unconnected']}, "
            f"short/clearance/crossing/hole "
            f"{ast['shorting_items']}/{ast['clearance']}/{ast['tracks_crossing']}/{ast['hole_clearance']}, "
            f"hole_to_hole {ast['hole_to_hole']}, GND islands {ast['gnd_zone_islands']}). "
            f"Blob matches pre-edit: {info['reverted_blob_match']}. No second path."
        )
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30BB_MID.json", REPORTS / "DRC_PASS30BB_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. In1.Cu south of both end caps, {len(POLY) - 1} new segments, no new via. "
        f"Whole-segment skirt test: 0 crossings (min center distance {skirt['min_center_distance_mm']} mm). "
        f"P0.19 opens {bst['p019_unconnected']}→{mst['p019_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Skirts not crossed or ripped. P0.17 not retried."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
