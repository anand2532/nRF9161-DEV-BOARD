#!/usr/bin/env python3
"""pass30bd — ONE attempt: SIM_CLK only.

U1.46 leaves on F.Cu into the existing through-via (31.25, 23.10).
The far island is the SIM_CLK via (73.30, 36.00) on the B.Cu run.
x=44.25 and x=44.60 are full on both inner layers (P0.16/P0.19/P0.17/P0.20).
Those centerlines are not used. The route stays north of every locked
skirt segment, then drops south at x=57.20, east of the end caps.

No new via. No second path. No other net.
"""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
spec = importlib.util.spec_from_file_location("p30ba", ROOT / "scripts" / "final_pass30ba.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BOARD = m.BOARD
BACKUP = ROOT / ".mcp-backups/pass30bd/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
F, B, IN1, IN2 = m.F, m.B, m.IN1, m.IN2
W = m.W
CF = m.CF
CP = m.CP
LAYERS = m.LAYERS
NET = "SIM_CLK"

# In1.Cu north of every locked skirt, then south at x=57.20 onto the
# existing through-via (73.30, 36.00). Not the x=44.25 / x=44.60 slot.
POLY = [
    (31.25, 23.10),
    (33.60, 22.40),
    (33.60, 19.20),
    (39.40, 19.20),
    (39.40, 20.05),
    (56.00, 20.05),
    (56.00, 19.55),
    (57.20, 19.55),
    (57.20, 36.00),
    (73.30, 36.00),
]
P16 = [
    (40.70, 20.80), (45.55, 20.80), (45.55, 27.40), (44.60, 27.40),
    (44.60, 60.40), (45.62, 60.40), (45.62, 61.10),
]
P17 = [
    (40.25, 23.10), (40.25, 21.50), (45.55, 21.50), (45.55, 27.40),
    (44.60, 27.40), (44.60, 60.40), (48.16, 60.40), (48.16, 61.30),
]
P19 = [
    (39.25, 23.10), (39.25, 26.50), (44.25, 26.50), (44.25, 39.10),
    (42.80, 39.90), (44.25, 40.70), (44.25, 63.20), (53.24, 63.20), (53.24, 62.00),
]
P20 = [
    (36.20, 20.80), (36.45, 20.80), (36.45, 26.50), (44.25, 26.50),
    (44.25, 39.10), (42.80, 39.90), (44.25, 40.70), (44.25, 63.20),
    (55.78, 63.20), (55.78, 62.00),
]
LOCKED = [
    ("P0.16", "In1.Cu", P16),
    ("P0.17", "In2.Cu", P17),
    ("P0.19", "In1.Cu", P19),
    ("P0.20", "In2.Cu", P20),
]
EXPECTED_HEAD = "558e221"
EXPECTED_BLOB = "2d07228fba7bf2e61497e4e15cb3c4a9b90e1d57"
LAYER = IN1
LAYER_NAME = "In1.Cu"


def orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def interior_cross(a, bpt, c, d) -> bool:
    ax, ay = a
    bx, by = bpt
    cx, cy = c
    dx, dy = d
    o1 = orient(ax, ay, bx, by, cx, cy)
    o2 = orient(ax, ay, bx, by, dx, dy)
    o3 = orient(cx, cy, dx, dy, ax, ay)
    o4 = orient(cx, cy, dx, dy, bx, by)
    return o1 * o2 < 0 and o3 * o4 < 0


def collinear_overlap(a, bpt, c, d, tol=1e-3) -> bool:
    ax, ay = a
    bx, by = bpt
    cx, cy = c
    dx, dy = d
    L = math.hypot(bx - ax, by - ay)
    if L < 1e-9:
        return False

    def dist_line(px, py):
        return abs((bx - ax) * (ay - py) - (by - ay) * (ax - px)) / L

    if dist_line(cx, cy) > tol or dist_line(dx, dy) > tol:
        return False

    def proj(px, py):
        return ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L

    p0, p1 = sorted((proj(cx, cy), proj(dx, dy)))
    return min(L, p1) - max(0.0, p0) > tol


def closest_is_interior(px, py, a, bpt, tol=1e-3) -> bool:
    d_seg = m.dps(px, py, a[0], a[1], bpt[0], bpt[1])
    d_end = min(math.hypot(px - a[0], py - a[1]), math.hypot(px - bpt[0], py - bpt[1]))
    return d_seg + tol < d_end


def skirt_segments():
    out = []
    for net, layer, pts in LOCKED:
        for a, c in zip(pts, pts[1:]):
            out.append({"net": net, "layer": layer, "a": a, "b": c})
    return out


def forbidden_stack(x1, y1, x2, y2) -> bool:
    """Same centerline as a locked skirt run. Forbidden on every layer."""
    if abs(x1 - x2) < 1e-6 and abs(x1 - 44.25) < 1e-3:
        return True
    if abs(x1 - x2) < 1e-6 and abs(x1 - 44.60) < 1e-3:
        return True
    if abs(y1 - y2) < 1e-6 and abs(y1 - 63.20) < 1e-3 and min(x1, x2) < 56.0 and max(x1, x2) > 44.0:
        return True
    return False


def whole_segment_crossing_test(poly):
    """Intersection plus samples. A same-centerline stack on any of the four is a fail."""
    rows = []
    crossings = []
    stacks = []
    joins = []
    min_skirt = None
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        n = max(2, int(length / 0.05))
        seg_skirt = None
        seg_cross = None
        for sk in skirt_segments():
            a, c = sk["a"], sk["b"]
            dist = m.segseg(x1, y1, x2, y2, a[0], a[1], c[0], c[1])
            coli = collinear_overlap((x1, y1), (x2, y2), a, c)
            proper = interior_cross((x1, y1), (x2, y2), a, c)
            sample_min = dist
            interior_hits = []
            endpoint_hits = []
            for i in range(n + 1):
                t = i / n
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                d = m.dps(px, py, a[0], a[1], c[0], c[1])
                if d < sample_min:
                    sample_min = d
                if d <= 1e-4:
                    rec = {"at": [round(px, 4), round(py, 4)], "distance_mm": d}
                    if closest_is_interior(px, py, a, c):
                        interior_hits.append(rec)
                    else:
                        endpoint_hits.append(rec)
            use = min(dist, sample_min)
            item = (use, sk["net"], [list(a), list(c)])
            if seg_skirt is None or item[0] < seg_skirt[0]:
                seg_skirt = item
            if min_skirt is None or item[0] < min_skirt[0]:
                min_skirt = item
            if coli or forbidden_stack(x1, y1, x2, y2):
                stacks.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked": [list(a), list(c)],
                    "note": "same-centerline stack is forbidden on every layer",
                })
            bad = coli or forbidden_stack(x1, y1, x2, y2) or proper or bool(interior_hits)
            # forbidden_stack is a property of OUR segment, not of each skirt.
            # Only record it once per segment, below.
            if coli or proper or interior_hits:
                seg_cross = sk["net"]
                crossings.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked_layer": sk["layer"],
                    "locked": [list(a), list(c)],
                    "proper_interior": proper,
                    "collinear_stack": coli,
                    "interior_sample_hits": interior_hits[:6],
                    "min_center_distance_mm": round(use, 6),
                })
            elif endpoint_hits or (b_intersects := False):
                joins.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked": [list(a), list(c)],
                    "note": "endpoint touch only",
                })
        if forbidden_stack(x1, y1, x2, y2):
            seg_cross = seg_cross or "stacked-centerline"
            crossings.append({
                "segment": [[x1, y1], [x2, y2]],
                "locked_net": "stacked-centerline",
                "locked_layer": "In1.Cu/In2.Cu",
                "note": "x=44.25 or x=44.60 or y=63.20 eastbound stack",
            })
        near = None if seg_skirt is None else {
            "net": seg_skirt[1],
            "segment": seg_skirt[2],
            "center_distance_mm": round(seg_skirt[0], 4),
            "edge_clearance_mm": round(seg_skirt[0] - W, 4),
        }
        rows.append({
            "start": [x1, y1],
            "end": [x2, y2],
            "samples": n + 1,
            "crossed": seg_cross is not None,
            "nearest_skirt": near,
        })
    return {
        "method": (
            "segment-vs-segment interior intersection plus 0.05 mm samples, "
            "against P0.16, P0.17, P0.19, and P0.20, layers not exempt. "
            "A same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds "
            "is a fail even on another layer. Endpoint-only touches are not crossings. "
            "A sample in the interior of a locked segment is a crossing."
        ),
        "crossed": bool(crossings),
        "crossing_count": len(crossings),
        "crossings": crossings,
        "forbidden_stacks": stacks,
        "endpoint_joins_not_crossings": joins,
        "min_center_distance_to_locked_mm": None if min_skirt is None else round(min_skirt[0], 4),
        "min_locked_item": None if min_skirt is None else {"net": min_skirt[1], "segment": min_skirt[2]},
        "segments": rows,
        "y61_63_not_used": "y=61.63 is inside the J18 pad circles. Not this route. This route never goes south of y=36.00.",
    }


def collect(board, layer):
    vias, holes, pads, tracks = [], [], [], []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == NET:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
            vias.append((x, y, m.mm(t.GetWidth(layer)) / 2, net, net in m.POWER))
            holes.append((x, y, m.mm(t.GetDrillValue()) / 2, f"via {net} @{x:.3f},{y:.3f}"))
        elif t.GetLayer() == layer:
            tracks.append((
                m.mm(t.GetStart().x), m.mm(t.GetStart().y),
                m.mm(t.GetEnd().x), m.mm(t.GetEnd().y),
                m.mm(t.GetWidth()) / 2, net, net in m.POWER,
            ))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == NET or not p.IsOnLayer(layer):
                continue
            x, y = m.mm(p.GetPosition().x), m.mm(p.GetPosition().y)
            pads.append((p, f"{fp.GetReference()}.{p.GetNumber()}", net, net in m.POWER, x, y))
            if p.GetDrillSize().x:
                holes.append((x, y, m.mm(p.GetDrillSize().x) / 2, f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]"))
    return vias, holes, pads, tracks


def measure(board):
    vias, holes, pads, tracks = collect(board, LAYER)
    rows, mf, mp, mh = [], None, None, None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = m.seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, LAYER)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
        row["layer"] = LAYER_NAME
        row["body"] = m.body_hit(x1, y1, x2, y2)
        if row["body"]:
            row["ok"] = False
            row["why"] = "body_or_keepout"
        rows.append(row)
        if row.get("foreign") is not None and (mf is None or row["foreign"] < mf[0]):
            mf = (row["foreign"], row["foreign_item"])
        if row.get("power") is not None and (mp is None or row["power"] < mp[0]):
            mp = (row["power"], row["power_item"])
        if row.get("hole") is not None and (mh is None or row["hole"] < mh[0]):
            mh = (row["hole"], row["hole_item"])
    # land on the far through-via
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != NET:
            continue
        if m.near(m.mm(t.GetPosition().x), 73.30) and m.near(m.mm(t.GetPosition().y), 36.00):
            via = t
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2]), m.xy(*POLY[-1]), pcbnew.FromMM(W))
    hits = False
    if via is not None:
        pad = pcbnew.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(LAYER) // 2)
        hits = bool(land.Collide(pad))
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits
        and nseg <= 10
        and min(p[0] for p in POLY) > 24.2
        and not any(r["body"] for r in rows)
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
        "lands_on_far_via": hits,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= m.HOLE - 1e-9,
        "ok": ok,
        "layer": LAYER_NAME,
        "new_via": False,
        "width_mm": W,
    }


def lane_checks(board) -> dict:
    """Remeasure the closed east strip and the in-body west centerline."""
    out = {}
    for name, lid in (("In1.Cu", IN1), ("In2.Cu", IN2), ("F.Cu", F), ("B.Cu", B)):
        vias, holes, pads, tracks = collect(board, lid)
        row = m.seg_clearance(44.93, 27.40, 44.93, 50.00, vias, holes, pads, tracks, lid)
        out[name] = {
            "x": 44.93,
            "span": [[44.93, 27.40], [44.93, 50.00]],
            "ok": row["ok"] and not m.body_hit(44.93, 27.40, 44.93, 50.00),
            "foreign_mm": row.get("foreign"),
            "foreign_item": row.get("foreign_item"),
            "power_mm": row.get("power"),
            "hole_mm": row.get("hole"),
            "hole_item": row.get("hole_item"),
            "body": m.body_hit(44.93, 27.40, 44.93, 50.00),
        }
    # the exact P0.06 edge at x=44.93
    p006 = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.06":
            continue
        x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
        if abs(x - 45.150) < 0.02 and abs(y - 36.0) < 0.02:
            r = m.mm(t.GetWidth(IN1)) / 2
            p006 = {
                "via_xy": [round(x, 3), round(y, 3)],
                "radius_mm": round(r, 3),
                "width_mm": round(m.mm(t.GetWidth(IN1)), 3),
                "centerline_x": 44.93,
                "edge_clearance_mm": round(abs(44.93 - x) - r - (W / 2), 4),
            }
    return {
        "x_44_93_by_layer": out,
        "p006_at_x_44_93": p006,
        "x_43_92_inside_body": m.body_hit(43.92, 30.0, 43.92, 50.0),
        "body_east_edge_mm": 44.0,
        "track_center_must_clear_body_x_mm": 44.0 + W / 2,
        "note": (
            "x=44.93 is 0.33 mm east of the x=44.60 skirts. "
            "P0.06 via (45.150, 36.000) pad radius 0.25 mm leaves edge clearance -0.12 mm. "
            "x=43.92 is the next 0.33 mm centerline west of x=44.25 and is inside the fab body "
            "(body ends at x=44.0; a 0.18 mm track needs center x>44.09). "
            "No legal centerline remains between the body and the two locked skirts on In1 or In2."
        ),
    }


def shp_of(it, lid):
    if it["kind"] == "pad":
        return it["obj"].GetEffectiveShape(lid)
    if it["kind"] == "via":
        return pcbnew.SHAPE_CIRCLE(m.xy(it["x"], it["y"]), pcbnew.FromMM(m.mm(it["obj"].GetWidth(lid)) / 2))
    return pcbnew.SHAPE_SEGMENT(it["obj"].GetStart(), it["obj"].GetEnd(), it["obj"].GetWidth())


def islands(board) -> dict:
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != NET:
                continue
            layers = [lid for _, lid in LAYERS if p.IsOnLayer(lid)]
            items.append({
                "kind": "pad",
                "name": f"{fp.GetReference()}.{p.GetNumber()}",
                "ref": fp.GetReference(),
                "num": p.GetNumber(),
                "x": m.mm(p.GetPosition().x),
                "y": m.mm(p.GetPosition().y),
                "layers": layers,
                "obj": p,
            })
    for t in board.GetTracks():
        if t.GetNetname() != NET:
            continue
        if t.GetClass() == "PCB_VIA":
            layers = [lid for _, lid in LAYERS if t.IsOnLayer(lid)]
            items.append({
                "kind": "via",
                "name": f"via@{m.mm(t.GetPosition().x):.3f},{m.mm(t.GetPosition().y):.3f}",
                "x": m.mm(t.GetPosition().x),
                "y": m.mm(t.GetPosition().y),
                "layers": layers,
                "obj": t,
            })
        else:
            items.append({
                "kind": "trk",
                "name": (
                    f"{board.GetLayerName(t.GetLayer())} "
                    f"({m.mm(t.GetStart().x):.3f},{m.mm(t.GetStart().y):.3f})-"
                    f"({m.mm(t.GetEnd().x):.3f},{m.mm(t.GetEnd().y):.3f})"
                ),
                "x": (m.mm(t.GetStart().x) + m.mm(t.GetEnd().x)) / 2,
                "y": (m.mm(t.GetStart().y) + m.mm(t.GetEnd().y)) / 2,
                "layers": [t.GetLayer()],
                "obj": t,
            })

    def touches(i, j) -> bool:
        for lid in set(items[i]["layers"]) & set(items[j]["layers"]):
            if m.mm(shp_of(items[i], lid).GetClearance(shp_of(items[j], lid))) <= 0.001:
                return True
        return False

    parent = list(range(len(items)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, c):
        ra, rb = find(a), find(c)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if touches(i, j):
                union(i, j)

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.46")
    far_i = next(i for i, it in enumerate(items) if "B.Cu (70.900,45.500)-(68.140,45.500)" in it["name"] or "B.Cu (68.140,45.500)-(70.900,45.500)" in it["name"])
    same = find(u1) == find(far_i)

    def names(root_idx):
        return [items[i]["name"] for i in range(len(items)) if find(i) == find(root_idx)]

    def layer_names(root_idx):
        lids = set()
        for i in range(len(items)):
            if find(i) == find(root_idx):
                lids.update(items[i]["layers"])
        return [name for name, lid in LAYERS if lid in lids]

    # pad-edge: U1.46 (F.Cu only) has no shared layer with the B.Cu track.
    # Report the geometric gap between the pad shape and that track, which is
    # the census figure, plus every remaining open end if the islands differ.
    u = items[u1]["obj"]
    far = items[far_i]
    gap = m.mm(u.GetEffectiveShape(F).GetClearance(shp_of(far, B)))
    opens = []
    if not same:
        roots = []
        seen = set()
        for i in range(len(items)):
            r = find(i)
            if r in seen:
                continue
            seen.add(r)
            roots.append(i)
        # one representative per island: the item nearest another island
        for idx in roots:
            best = None
            others = [i for i in range(len(items)) if find(i) != find(idx)]
            for name, lid in LAYERS:
                if lid not in items[idx]["layers"]:
                    continue
                sh = shp_of(items[idx], lid)
                for i in others:
                    if lid not in items[i]["layers"]:
                        continue
                    c = m.mm(sh.GetClearance(shp_of(items[i], lid)))
                    if best is None or c < best[0]:
                        best = (c, name, items[i]["name"])
            it = items[idx]
            opens.append({
                "ref": it.get("ref", it["name"]),
                "pad": it.get("num", ""),
                "name": it["name"],
                "kind": it["kind"],
                "center_xy": [round(it["x"], 3), round(it["y"], 3)],
                "layers": [name for name, lid in LAYERS if lid in it["layers"]],
                "pad_edge_mm": None if best is None else round(best[0], 6),
                "nearest": None if best is None else {"layer": best[1], "item": best[2]},
            })
    return {
        "same_island": same,
        "island_count": len({find(i) for i in range(len(items))}),
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "u1_46": [round(items[u1]["x"], 3), round(items[u1]["y"], 3)],
        "far_track": far["name"],
        "u1_island": names(u1),
        "u1_island_layers": layer_names(u1),
        "far_island": names(far_i),
        "far_island_layers": layer_names(far_i),
        "opens_if_separate": opens,
    }


def straight_chord(board) -> dict:
    ax, ay = 31.397, 27.128
    bx, by = 68.060, 45.460
    hit = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "VDD2":
            continue
        x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
        if abs(x - 61.3) > 0.05 or abs(y - 42.0) > 0.05:
            continue
        r = m.mm(t.GetWidth(F)) / 2
        center = m.dps(x, y, ax, ay, bx, by)
        edge = center - r - (W / 2)
        hit = {
            "via_xy": [round(x, 3), round(y, 3)],
            "via_radius_mm": round(r, 3),
            "centerline_distance_mm": round(center, 4),
            "edge_clearance_mm": round(edge, 4),
        }
    return {
        "from_u1_46_copper": [ax, ay],
        "to_bcu_track_nearest": [bx, by],
        "width_mm": W,
        "layer": "F.Cu",
        "length_mm": round(math.hypot(bx - ax, by - ay), 6),
        "crosses_sip_body": m.crosses_body(ax, ay, bx, by),
        "vdd2": hit,
        "used": False,
        "note": "Chord crosses the fab body and hits VDD2 via (61.3, 42.0). Not used.",
    }


def layer_die(board) -> dict:
    """How far the existing via can go before foreign copper or the body stops it."""
    probes = {
        "south_x31.25": (31.25, 23.10, 31.25, 40.0),
        "north_x31.25": (31.25, 23.10, 31.25, 16.0),
        "east_y23.10": (31.25, 23.10, 46.0, 23.10),
        "west_y23.10": (31.25, 23.10, 24.5, 23.10),
    }
    out = {}
    for name, lid in LAYERS:
        vias, holes, pads, tracks = collect(board, lid)
        layer_out = {}
        for label, (x1, y1, x2, y2) in probes.items():
            # walk in 0.05 mm steps until blocked
            length = math.hypot(x2 - x1, y2 - y1)
            n = max(2, int(length / 0.05))
            last = (x1, y1)
            died = None
            for i in range(1, n + 1):
                t = i / n
                x = x1 + (x2 - x1) * t
                y = y1 + (y2 - y1) * t
                row = m.seg_clearance(x1, y1, x, y, vias, holes, pads, tracks, lid)
                body = m.body_hit(x1, y1, x, y)
                if (not row["ok"]) or body:
                    died = {
                        "last_clear": [round(last[0], 3), round(last[1], 3)],
                        "blocked_at": [round(x, 3), round(y, 3)],
                        "foreign_mm": row.get("foreign"),
                        "foreign_item": row.get("foreign_item"),
                        "power_mm": row.get("power"),
                        "power_item": row.get("power_item"),
                        "body": body,
                        "why": row.get("why") or ("body" if body else "clearance"),
                    }
                    break
                last = (x, y)
            layer_out[label] = died or {"reaches": [round(x2, 3), round(y2, 3)]}
        out[name] = layer_out
    return {
        "from": [31.25, 23.10],
        "probes": out,
        "note": (
            "The via sits at x=31.25, inside the fab body's x-range (28–44), so a "
            "straight south run enters the body at y=26.75. Straight north dies on "
            "the COEX0 via (31.110, 22.000). East along y=23.10 dies on the P0.25 "
            "via (33.250, 23.100) before the skirt. West dies on the SIM_IO via "
            "(30.250, 23.100). F.Cu and B.Cu therefore do not reach the far island "
            "in a straight shot. The kept route leaves northeast, then runs north of the skirts."
        ),
    }


def via_info(board) -> dict:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != NET:
            continue
        if m.near(m.mm(t.GetPosition().x), 31.25) and m.near(m.mm(t.GetPosition().y), 23.10):
            return {
                "pos": [31.25, 23.10],
                "drill_mm": round(m.mm(t.GetDrillValue()), 3),
                "pad_mm": round(m.mm(t.GetWidth(F)), 3),
                "top": board.GetLayerName(t.TopLayer()),
                "bottom": board.GetLayerName(t.BottomLayer()),
                "through": board.GetLayerName(t.TopLayer()) == "F.Cu" and board.GetLayerName(t.BottomLayer()) == "B.Cu",
                "on": {name: bool(t.IsOnLayer(lid)) for name, lid in LAYERS},
            }
    return {}


def add_route(board):
    net = board.FindNet(NET)
    if net is None:
        raise SystemExit("SIM_CLK missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(m.xy(x1, y1))
        tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(LAYER)
        tr.SetNet(net)
        board.Add(tr)


def counts_locked(before_counts, board):
    after = m.track_counts(board)
    bad = []
    for net, n in before_counts["tracks"].items():
        if net == NET:
            continue
        if after["tracks"].get(net, 0) != n:
            bad.append(f"track {net} {n}->{after['tracks'].get(net, 0)}")
    for net, n in before_counts["vias"].items():
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get(NET, 0) != before_counts["vias"].get(NET, 0):
        bad.append("SIM_CLK via count changed")
    expect = before_counts["tracks"].get(NET, 0) + (len(POLY) - 1)
    if after["tracks"].get(NET, 0) != expect:
        bad.append(
            f"SIM_CLK tracks {before_counts['tracks'].get(NET, 0)}->"
            f"{after['tracks'].get(NET, 0)} expected {expect}"
        )
    return bad


def protect_ok(board) -> dict:
    return {
        "p016": m.poly_ok(board, P16, "P0.16", IN1),
        "p017": m.poly_ok(board, P17, "P0.17", IN2),
        "p019": m.poly_ok(board, P19, "P0.19", IN1),
        "p020": m.poly_ok(board, P20, "P0.20", IN2),
        "sim_clk_stub": any(
            t.GetNetname() == NET and t.GetLayer() == F and m.track_is(t, 31.25, 26.75, 31.25, 23.10)
            for t in board.GetTracks()
        ),
        "sim_clk_via": m.via_at(board, NET, 31.25, 23.10),
        "far_via": m.via_at(board, NET, 73.30, 36.00),
    }


def gained(before: dict, after: dict) -> dict:
    out = {}
    for k in set(before) | set(after):
        if k == NET:
            continue
        if after.get(k, 0) > before.get(k, 0):
            out[k] = [before.get(k, 0), after.get(k, 0)]
    return out


def enrich(res):
    res["stats"]["sim_clk_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
    return res


def restore():
    shutil.copy2(BACKUP, BOARD)


def write_outputs(decision, info, before, after, reason, meas, skirt):
    ts = m.ist_now()
    bstat, a = before, after
    segs = [
        {"layer": LAYER_NAME, "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30bd",
        "timestamp": ts,
        "decision": decision,
        "net": NET,
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "pcb_blob_at_end": m.git_blob(),
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "head_matches_expected": info.get("git_head", "").startswith(EXPECTED_HEAD),
        "blob_matches_expected": info.get("pcb_blob") == EXPECTED_BLOB,
        "same_island": info["gap"]["same_island"],
        "far_island_layers": info["gap"]["far_island_layers"],
        "u1_island_layers": info["gap"]["u1_island_layers"],
        "u1_island": info["gap"]["u1_island"],
        "far_island": info["gap"]["far_island"],
        "pad_edge_mm": info["gap"]["pad_edge_exact_mm"],
        "pad_edge_census_mm": 40.990,
        "straight_chord": info.get("chord"),
        "existing_via": info.get("via"),
        "layer_die_from_via": info.get("die"),
        "lanes_checked": info.get("lanes"),
        "skirt_slot_only_way": False,
        "why_skirt_slot_not_only_way": (
            "The four locked skirts occupy x=44.25 and x=44.60 from about y=26.5 to y=63.2, "
            "and a same-centerline stack is forbidden on every layer. East of them, x=44.93 "
            "hits P0.06 (45.150, 36.000) at -0.12 mm. West of them, x=43.92 is inside the fab body. "
            "That slot is closed, but it is not the only way out: the through-via can leave north "
            "on In1.Cu, run at y=19.20/20.05/19.55 (all north of the skirt y=20.80 cap), and drop "
            "south at x=57.20, which is east of every locked segment. F.Cu and B.Cu copies of that "
            "polyline are blocked by VDD_GPIO, DEC0, P0.15, and VDD2 tracks. In2.Cu clears the same "
            "polyline; only In1.Cu was placed."
        ),
        "whole_segment_crossing_test": skirt,
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
                "start": r["start"], "end": r["end"], "ok": r["ok"], "body": r.get("body"),
                "foreign_mm": r.get("foreign"), "foreign_item": r.get("foreign_item"),
                "power_mm": r.get("power"), "power_item": r.get("power_item"),
                "hole_mm": r.get("hole"), "hole_item": r.get("hole_item"),
                "why": r.get("why"),
            }
            for r in meas.get("segments", [])
        ],
        "sim_clk_opens_before": bstat.get("sim_clk_unconnected"),
        "sim_clk_opens_after": a.get("sim_clk_unconnected"),
        "unconnected_before": bstat.get("unconnected_items"),
        "unconnected_after": a.get("unconnected_items"),
        "short_clearance_crossing_hole_before": [
            bstat.get("shorting_items"), bstat.get("clearance"), bstat.get("tracks_crossing"), bstat.get("hole_clearance")
        ],
        "short_clearance_crossing_hole_after": [
            a.get("shorting_items"), a.get("clearance"), a.get("tracks_crossing"), a.get("hole_clearance")
        ],
        "hole_to_hole_before": bstat.get("hole_to_hole"),
        "hole_to_hole_after": a.get("hole_to_hole"),
        "gnd_islands_before": bstat.get("gnd_zone_islands"),
        "gnd_islands_after": a.get("gnd_zone_islands"),
        "other_nongnd_gained": info.get("gained", {}),
        "reason": reason,
        "skirts_crossed_or_stacked": skirt.get("crossed"),
        "skirts_ripped": False,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
        "opens_if_separate": info["gap"].get("opens_if_separate"),
    }
    (REPORTS / "PASS30BD_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BD_SUMMARY — SIM_CLK",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** SIM_CLK",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**Expected tip/blob matched:** {payload['head_matches_expected']} / {payload['blob_matches_expected']}",
        f"**Ends already one island:** {info['gap']['same_island']}",
        f"**Far island layers:** {info['gap']['far_island_layers']}",
        f"**U1 island layers:** {info['gap']['u1_island_layers']}",
        f"**Pad-edge (U1.46 to B.Cu 45.50 track):** {info['gap']['pad_edge_exact_mm']:.6f} mm (census 40.990)",
        f"**Existing via:** {info.get('via')}",
        "**New via:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Crossing test failed:** {skirt.get('crossed')}",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**SIM_CLK opens:** {bstat.get('sim_clk_unconnected')} → {a.get('sim_clk_unconnected')}",
        f"**Unconnected:** {bstat.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**GND islands:** {bstat.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)",
        "",
        "## Islands",
        "",
        f"U1 island: {info['gap']['u1_island']}",
        f"Far island: {info['gap']['far_island']}",
        "",
        "## Straight chord",
        "",
        (
            f"F.Cu 0.18 mm {info['chord']['from_u1_46_copper']} → {info['chord']['to_bcu_track_nearest']}, "
            f"length {info['chord']['length_mm']} mm. Crosses SiP body: {info['chord']['crosses_sip_body']}. "
            f"VDD2 via {info['chord']['vdd2']}. Not used."
        ),
        "",
        "## Lanes checked",
        "",
        payload["why_skirt_slot_not_only_way"],
        "",
        f"x=44.93 remeasure: {info.get('lanes', {}).get('p006_at_x_44_93')}",
        f"x=43.92 inside body: {info.get('lanes', {}).get('x_43_92_inside_body')}",
        "",
        "Per-layer probe of x=44.93 from y=27.40 to y=50.00 (stops before the y=60.40 east caps so the via hit is visible):",
        "",
    ]
    for name, row in (info.get("lanes") or {}).get("x_44_93_by_layer", {}).items():
        lines.append(
            f"- {name}: ok={row['ok']} foreign={row['foreign_mm']} vs {row['foreign_item']} "
            f"hole={row['hole_mm']} vs {row['hole_item']}"
        )
    lines += [
        "",
        "## Free space from via (31.25, 23.10)",
        "",
        info.get("die", {}).get("note", ""),
        "",
        "## Whole-segment crossing test",
        "",
        skirt.get("method", ""),
        (
            f"Crossings: **{skirt.get('crossing_count')}**. "
            f"Min centerline to a locked skirt: **{skirt.get('min_center_distance_to_locked_mm')} mm** "
            f"vs {skirt.get('min_locked_item')}."
        ),
        "",
        "Per new segment, nearest locked skirt:",
        "",
    ]
    for row in skirt.get("segments", []):
        near = row.get("nearest_skirt") or {}
        lines.append(
            f"- {tuple(row['start'])} → {tuple(row['end'])} crossed={row['crossed']} "
            f"nearest {near.get('net')} {near.get('segment')} center {near.get('center_distance_mm')} mm "
            f"(edge {near.get('edge_clearance_mm')} mm), {row['samples']} samples"
        )
    lines += [
        "",
        "## Attempt",
        "",
    ]
    if placed:
        lines.append(f"{LAYER_NAME} 0.18 mm, no new via. Kept.")
        lines.append("")
        for s in segs:
            lines.append(f"- {tuple(s['start'])} → {tuple(s['end'])} {s['layer']}")
    else:
        lines.append("No copper left on the board.")
    lines += [
        "",
        "North bypass: leave the through-via northeast to clear P0.25, run north at x=33.60 "
        "(west of SWDCLK/P0.22), east at y=19.20 under VDD_GPIO (40.170, 19.126), south to y=20.05 "
        "(still 0.75 mm north of the P0.16/P0.20 y=20.80 cap), east to x=56.00, north to y=19.55 to "
        "clear ENABLE (56.500, 20.300), east to x=57.20, south to y=36.00, east onto SIM_CLK via "
        "(73.30, 36.00). x>24.2. No header or U1 move. Fanout vias not moved. Skirts not ripped "
        "and not stacked. No other net.",
        "",
        "## Clearance by segment",
        "",
    ]
    for r in meas.get("segments", []):
        lines.append(
            f"- {tuple(r['start'])}–{tuple(r['end'])} ok={r['ok']} foreign={r.get('foreign')} vs {r.get('foreign_item')} "
            f"power={r.get('power')} vs {r.get('power_item')} hole={r.get('hole')} vs {r.get('hole_item')} why={r.get('why')}"
        )
    lines += [
        "",
        "## Gate",
        "",
        reason,
        "",
        "## DRC",
        "",
        "| | unconnected | SIM_CLK | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        (
            f"| before | {bstat.get('unconnected_items')} | {bstat.get('sim_clk_unconnected')} | "
            f"{bstat.get('shorting_items')} | {bstat.get('clearance')} | {bstat.get('tracks_crossing')} | "
            f"{bstat.get('hole_clearance')} | {bstat.get('hole_to_hole')} | {bstat.get('gnd_zone_islands')} |"
        ),
        (
            f"| after | {a.get('unconnected_items')} | {a.get('sim_clk_unconnected')} | "
            f"{a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | "
            f"{a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |"
        ),
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}",
        "P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. No new via. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BD_SUMMARY.md").write_text("\n".join(lines) + "\n")
    para = (
        f"\n## Pass30bd — SIM_CLK — {ts}\n\n"
        f"**Decision:** **{decision}**. Ends already one island: {info['gap']['same_island']}. "
        f"Pad-edge {info['gap']['pad_edge_exact_mm']:.6f} mm (census 40.990). "
        f"Straight F.Cu chord crosses the body and hits VDD2 (61.3, 42.0) at "
        f"{info['chord']['vdd2']['edge_clearance_mm']} mm; not used. "
        f"x=44.93 remeasured at {info.get('lanes', {}).get('p006_at_x_44_93', {}).get('edge_clearance_mm')} mm "
        f"to P0.06; x=43.92 is inside the body. Skirt slot was not the only way and was not used. "
    )
    if placed:
        para += (
            f"Kept {LAYER_NAME} 0.18 mm, 9 segments, no new via, north of the four skirts then south at x=57.20 "
            f"onto via (73.30, 36.00). "
            f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
            f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
            f"SIM_CLK opens {bstat.get('sim_clk_unconnected')}→{a.get('sim_clk_unconnected')}. "
            f"Unconnected {bstat.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"short/clearance/crossing/hole "
            f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
            f"hole_to_hole {a.get('hole_to_hole')}. "
            f"GND islands {bstat.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
            f"Whole-segment crossings {skirt.get('crossing_count')}. "
        )
    else:
        para += f"{reason} "
    para += "Skirts not ripped or stacked. No other net. No Gerbers. No commit.\n"
    REVIEW.write_text(REVIEW.read_text() + para)


def main():
    info = {
        "git_head": m.git_head(),
        "pcb_blob": m.git_blob(),
    }
    print("HEAD", info["git_head"], "BLOB", info["pcb_blob"], flush=True)
    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = islands(board)
    info["chord"] = straight_chord(board)
    info["via"] = via_info(board)
    info["lanes"] = lane_checks(board)
    info["die"] = layer_die(board)
    info["fp"] = m.footprint_xy(board)
    info["counts"] = m.track_counts(board)
    info["protect_before"] = protect_ok(board)
    print("ISLAND", info["gap"]["same_island"], "pad-edge", info["gap"]["pad_edge_exact_mm"], flush=True)
    print("CHORD", info["chord"]["vdd2"], "body", info["chord"]["crosses_sip_body"], flush=True)
    print("P006", info["lanes"]["p006_at_x_44_93"], flush=True)

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BD_BEFORE.json"))
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    def finish(decision, reason, after_stats):
        info["gained"] = info.get("gained", {})
        skirt = info.get("skirt") or {"crossed": False, "crossing_count": 0, "segments": [], "method": ""}
        meas = info.get("meas") or {"segments": []}
        write_outputs(decision, info, bst, after_stats, reason, meas, skirt)
        print("DECISION", decision, flush=True)
        print(reason, flush=True)

    if bst["unconnected_items"] != 56:
        shutil.copy2(REPORTS / "DRC_PASS30BD_BEFORE.json", REPORTS / "DRC_PASS30BD_AFTER.json")
        info["skirt"] = {"crossed": False, "crossing_count": 0, "segments": [], "method": "not run"}
        info["meas"] = {"segments": []}
        finish(
            "NO-ROUTE",
            f"NO-ROUTE. Unconnected started at {bst['unconnected_items']}, not 56. No copper added.",
            bst,
        )
        return

    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BD_BEFORE.json", REPORTS / "DRC_PASS30BD_AFTER.json")
        info["skirt"] = {"crossed": False, "crossing_count": 0, "segments": [], "method": "not run"}
        info["meas"] = {"segments": []}
        finish(
            "NO-ROUTE",
            "NO-ROUTE. U1.46 and the B.Cu (70.90, 45.50)–(68.14, 45.50) track are already one island. No copper added.",
            bst,
        )
        return

    meas = measure(board)
    skirt = whole_segment_crossing_test(POLY)
    info["meas"] = meas
    info["skirt"] = skirt
    print("MEAS ok", meas["ok"], "foreign", meas["min_clearance_mm"], "power", meas["min_power_vin_mm"], "cross", skirt["crossed"], flush=True)

    if not info["via"].get("through"):
        shutil.copy2(REPORTS / "DRC_PASS30BD_BEFORE.json", REPORTS / "DRC_PASS30BD_AFTER.json")
        finish("NO-ROUTE", f"Existing via is not a through-via: {info['via']}. No copper added.", bst)
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BD_BEFORE.json", REPORTS / "DRC_PASS30BD_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if skirt["crossed"] or not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BD_BEFORE.json", REPORTS / "DRC_PASS30BD_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. No legal path inside the budget that avoids the locked skirts. "
            f"measure_ok={meas['ok']} foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']} "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']} "
            f"hole {meas['min_hole_mm']} crossings {skirt['crossing_count']}. "
            "The x=44.25/x=44.60 slot was not used. No copper added.",
            bst,
        )
        return

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BOARD, BACKUP)
    if m.sha(BOARD) != m.sha(BACKUP):
        raise SystemExit("backup copy failed")

    add_route(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != m.footprint_xy(board).get(ref))
    ripped = counts_locked(info["counts"], board)
    pa = protect_ok(board)
    skirt_after = whole_segment_crossing_test(POLY)
    if moved or ripped or not all(pa.values()) or not m.poly_ok(board, POLY, NET, LAYER) or skirt_after["crossed"]:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BD_AFTER.json"))
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        finish(
            "NO-ROUTE",
            f"Protect or crossing guard failed after add, before save. moved={moved} ripped={ripped} "
            f"protect={pa} crossed={skirt_after['crossed']}. Full restore. "
            f"Post-revert unconnected {after['stats']['unconnected_items']}. "
            f"Blob matches pre-edit: {info['reverted_blob_match']}.",
            after["stats"],
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = enrich(m.run_drc(REPORTS / "DRC_PASS30BD_MID.json"))
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["sim_clk_unconnected"] - mst["sim_clk_unconnected"]
    board2 = pcbnew.LoadBoard(str(BOARD))
    skirts_intact = protect_ok(board2)
    skirt_on_disk = whole_segment_crossing_test(POLY)
    info["skirt"] = skirt_on_disk
    gate_ok = (
        pdrop >= 1
        and not g
        and mst["shorting_items"] == 0
        and mst["clearance"] == 0
        and mst["tracks_crossing"] == 0
        and mst["hole_clearance"] == 0
        and mst["hole_to_hole"] == bst["hole_to_hole"]
        and meas["meets_foreign_0_15"]
        and meas["meets_power_0_20"]
        and not skirt_on_disk["crossed"]
        and all(skirts_intact.values())
        and m.poly_ok(board2, POLY, NET, LAYER)
        and mst["unconnected_items"] <= bst["unconnected_items"] - 1
    )
    if not gate_ok:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BD_AFTER.json"))
        ast = after["stats"]
        match = (
            ast["unconnected_items"] == bst["unconnected_items"]
            and ast["sim_clk_unconnected"] == bst["sim_clk_unconnected"]
            and ast["shorting_items"] == bst["shorting_items"]
            and ast["clearance"] == bst["clearance"]
            and ast["tracks_crossing"] == bst["tracks_crossing"]
            and ast["hole_clearance"] == bst["hole_clearance"]
            and ast["hole_to_hole"] == bst["hole_to_hole"]
        )
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        # post-revert board is the pre-edit board; report pre-edit clearances still
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"SIM_CLK opens {bst['sim_clk_unconnected']}→{mst['sim_clk_unconnected']} (need drop ≥ 1). "
            f"Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
            f"Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
            f"Locked intact: {all(skirts_intact.values())}. "
            f"Post-revert DRC matches pre-edit: {match} "
            f"(unc {ast['unconnected_items']}, SIM_CLK {ast['sim_clk_unconnected']}, "
            f"short/clearance/crossing/hole "
            f"{ast['shorting_items']}/{ast['clearance']}/{ast['tracks_crossing']}/{ast['hole_clearance']}, "
            f"hole_to_hole {ast['hole_to_hole']}, GND islands {ast['gnd_zone_islands']}). "
            f"Blob matches pre-edit: {info['reverted_blob_match']}. No second path."
        )
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30BD_MID.json", REPORTS / "DRC_PASS30BD_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. In1.Cu north bypass, {len(POLY) - 1} new segments, no new via. "
        f"Skirt slot (x=44.25 / x=44.60) was not the only way and was not used. "
        f"Whole-segment crossing test: 0 crossings "
        f"(min center to a locked skirt {skirt_on_disk['min_center_distance_to_locked_mm']} mm). "
        f"SIM_CLK opens {bst['sim_clk_unconnected']}→{mst['sim_clk_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Four skirts not ripped or stacked. No other net."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
