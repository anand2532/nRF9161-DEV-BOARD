#!/usr/bin/env python3
"""pass30bc — ONE attempt: P0.20 only.

U1.35 leaves on F.Cu into the existing through-via (36.20, 20.80).
J18.8 is a separate island and is a PTH, so the far island already has
In2.Cu. In1 east of the body is full (P0.19 at x=44.25, P0.16 at x=44.60).
The only corridor is In2 at x=44.25, same centerline as the P0.19 vertical.
That stack is not a crossing. A transverse hit of P0.16, P0.17, or P0.19 is.

No new via. No third In1 skirt. No second path.
"""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
spec = importlib.util.spec_from_file_location("p30bb", ROOT / "scripts" / "final_pass30bb.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
m = b.m

BOARD = m.BOARD
BACKUP = ROOT / ".mcp-backups/pass30bc/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
IN2 = m.IN2
F, B, IN1 = m.F, m.B, m.IN1
W = m.W
CF = m.CF
CP = m.CP
LAYERS = m.LAYERS

# In2.Cu from the existing through-via. x=44.25 stacks on the P0.19 In1
# vertical (intended slot). Eastbound y=63.20 is south of the J18 pads.
# West dodge is the same geometry as P0.19 around P0.06 (44.000, 39.900).
POLY = [
    (36.20, 20.80),
    (36.45, 20.80),
    (36.45, 26.50),
    (44.25, 26.50),
    (44.25, 39.10),
    (42.80, 39.90),
    (44.25, 40.70),
    (44.25, 63.20),
    (55.78, 63.20),
    (55.78, 62.00),
]
P19 = list(b.POLY)
LOCKED = [("P0.16", "In1.Cu", b.P16), ("P0.17", "In2.Cu", b.P17), ("P0.19", "In1.Cu", P19)]
EXPECTED_HEAD = "9ad4b94"
EXPECTED_BLOB = "9f2d8c0370c9ac60c5283fc3cbb2bc8b015d447a"


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


def whole_segment_crossing_test(poly):
    """Intersection plus samples. Layers are not an excuse.

    Same-centerline overlap with the P0.19 run is the In2 slot at x=44.25
    (and the matching dodge / y=26.50 / y=63.20 pieces), not a crossing.
    A transverse interior hit, or a sample that lands in the interior of
    P0.16 / P0.17 / a non-stacked P0.19 segment, is a crossing.
    """
    rows = []
    crossings = []
    stacks = []
    joins = []
    min_skirt = None
    min_p19 = None
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
            if sk["net"] in ("P0.16", "P0.17"):
                if seg_skirt is None or item[0] < seg_skirt[0]:
                    seg_skirt = item
                if min_skirt is None or item[0] < min_skirt[0]:
                    min_skirt = item
            else:
                if min_p19 is None or item[0] < min_p19[0]:
                    min_p19 = item
            stacked = sk["net"] == "P0.19" and coli
            if stacked:
                stacks.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "p019": [list(a), list(c)],
                    "note": "same-centerline In2 slot beside P0.19, not a crossing",
                })
            bad = (not stacked) and (proper or bool(interior_hits))
            if bad:
                seg_cross = sk["net"]
                crossings.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked_layer": sk["layer"],
                    "locked": [list(a), list(c)],
                    "proper_interior": proper,
                    "interior_sample_hits": interior_hits[:6],
                    "min_center_distance_mm": round(use, 6),
                })
            elif (not stacked) and (endpoint_hits or b.intersects((x1, y1), (x2, y2), a, c)):
                joins.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked": [list(a), list(c)],
                    "note": "endpoint touch only; centerline does not pass through the locked interior",
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
            "against P0.16, P0.17, and P0.19, layers not exempt. "
            "Collinear overlap with P0.19 is the x=44.25 In2 slot, not a crossing. "
            "Endpoint-only touches are not crossings. "
            "A sample in the interior of a locked segment is a crossing."
        ),
        "crossed": bool(crossings),
        "crossing_count": len(crossings),
        "crossings": crossings,
        "p019_same_centerline_stacks": stacks,
        "endpoint_joins_not_crossings": joins,
        "min_center_distance_to_p016_p017_mm": None if min_skirt is None else round(min_skirt[0], 4),
        "min_skirt_item": None if min_skirt is None else {"net": min_skirt[1], "segment": min_skirt[2]},
        "min_center_distance_to_p019_mm": None if min_p19 is None else round(min_p19[0], 4),
        "min_p019_item": None if min_p19 is None else {"net": min_p19[1], "segment": min_p19[2]},
        "segments": rows,
        "y61_63_not_used": (
            "y=61.63 is inside the J18.4/5/6 pad circles. Not this route. Eastbound is y=63.20."
        ),
    }


def collect(board, layer):
    vias, holes, pads, tracks = [], [], [], []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.20":
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
            if net == "P0.20" or not p.IsOnLayer(layer):
                continue
            x, y = m.mm(p.GetPosition().x), m.mm(p.GetPosition().y)
            pads.append((p, f"{fp.GetReference()}.{p.GetNumber()}", net, net in m.POWER, x, y))
            if p.GetDrillSize().x and f"{fp.GetReference()}.{p.GetNumber()}" != "J18.8":
                holes.append((x, y, m.mm(p.GetDrillSize().x) / 2, f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]"))
    return vias, holes, pads, tracks


def measure(board):
    vias, holes, pads, tracks = collect(board, IN2)
    rows, mf, mp, mh = [], None, None, None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = m.seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, IN2)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
        row["layer"] = "In2.Cu"
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
    j = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "J18":
            for p in fp.Pads():
                if p.GetNumber() == "8":
                    j = p
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2]), m.xy(*POLY[-1]), pcbnew.FromMM(W))
    hits_pad = bool(j and land.Collide(j.GetEffectiveShape(IN2)))
    pad_info = None
    if j is not None:
        sz = j.GetSize()
        pad_info = {
            "center": [round(m.mm(j.GetPosition().x), 3), round(m.mm(j.GetPosition().y), 3)],
            "size_mm": [round(m.mm(sz.x), 3), round(m.mm(sz.y), 3)],
            "drill_mm": round(m.mm(j.GetDrillSize().x), 3),
            "layers": [name for name, lid in LAYERS if j.IsOnLayer(lid)],
        }
    # straight In2 vertical in the slot, no dodge — record why the dodge is required
    nododge = m.seg_clearance(44.25, 26.50, 44.25, 63.20, vias, holes, pads, tracks, IN2)
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits_pad
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
        "lands_on_j18_8": hits_pad,
        "pad": pad_info,
        "no_dodge_vertical": {
            "ok": nododge["ok"],
            "foreign_mm": nododge.get("foreign"),
            "foreign_item": nododge.get("foreign_item"),
            "hole_mm": nododge.get("hole"),
            "hole_item": nododge.get("hole_item"),
            "why": "x=44.25 passes 0.25 mm from P0.06 via (44.000, 39.900). Edge clearance is negative. Dodge required. P0.19 dodge not ripped.",
        },
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= m.HOLE - 1e-9,
        "ok": ok,
        "layer": "In2.Cu",
        "new_via": False,
        "width_mm": W,
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
            if p.GetNetname() != "P0.20":
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
        if t.GetNetname() != "P0.20":
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
    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.35")
    j18 = next(i for i, it in enumerate(items) if it["name"] == "J18.8")
    same = find(u1) == find(j18)

    def names(root_idx):
        return [items[i]["name"] for i in range(len(items)) if find(i) == find(root_idx)]

    def layer_names(root_idx):
        lids = set()
        for i in range(len(items)):
            if find(i) == find(root_idx):
                lids.update(items[i]["layers"])
        return [name for name, lid in LAYERS if lid in lids]

    u = items[u1]["obj"]
    far = next(it for it in items if it["name"].startswith("F.Cu (55.780,62.000)"))
    gap = m.mm(u.GetEffectiveShape(F).GetClearance(shp_of(far, F)))
    opens = []
    if not same:
        for idx in (u1, j18):
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
    # also describe the DRC far track
    far_desc = {
        "name": far["name"],
        "center_xy": [round(far["x"], 3), round(far["y"], 3)],
        "layers": ["F.Cu"],
        "endpoints": [[55.78, 62.00], [55.78, 60.90]],
    }
    return {
        "same_island": same,
        "island_count": len({find(i) for i in range(len(items))}),
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "u1_35": [round(items[u1]["x"], 3), round(items[u1]["y"], 3)],
        "j18_8": [round(items[j18]["x"], 3), round(items[j18]["y"], 3)],
        "u1_island": names(u1),
        "u1_island_layers": layer_names(u1),
        "far_island": names(j18),
        "far_island_layers": layer_names(j18),
        "far_island_fcu_only": layer_names(j18) == ["F.Cu"],
        "far_track": far_desc,
        "opens_if_separate": opens,
    }


def straight_chord(board) -> dict:
    ax, ay = 36.878, 27.147
    bx, by = 55.736, 60.821
    hit = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.06":
            continue
        x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
        if abs(x - 44.0) > 0.02 or abs(y - 39.9) > 0.02:
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
        "from": [ax, ay],
        "to": [bx, by],
        "width_mm": W,
        "layer": "F.Cu",
        "length_mm": round(math.hypot(bx - ax, by - ay), 6),
        "crosses_sip_body": m.crosses_body(ax, ay, bx, by),
        "p006": hit,
        "used": False,
        "note": "Chord crosses the fab body and hits P0.06. Not used.",
    }


def layer_die(board) -> dict:
    """Straight south from the existing via. Neighbor vias died at y=26.5; this x does not get that far."""
    out = {}
    for name, lid in LAYERS:
        vias, holes, pads, tracks = collect(board, lid)
        y = 20.80
        last = 20.80
        died = None
        while y < 32.0:
            y = round(y + 0.25, 2)
            row = m.seg_clearance(36.20, last, 36.20, y, vias, holes, pads, tracks, lid)
            if not row["ok"] or m.body_hit(36.20, last, 36.20, y):
                died = {
                    "last_clear_y": last,
                    "blocked_by_y": y,
                    "foreign_mm": row.get("foreign"),
                    "foreign_item": row.get("foreign_item"),
                    "why": row.get("why") or "clearance",
                    "body": m.body_hit(36.20, last, 36.20, y),
                }
                break
            last = y
        out[name] = died or {"reaches_y": last}
    return {
        "from": [36.20, 20.80],
        "straight_south": out,
        "note": (
            "F.Cu and B.Cu (and In1/In2 on this same x) die at the P0.21 via "
            "(35.750, 23.100), before y=26.5. The neighbor vias at x=39.25/40.25 "
            "were the ones that died at y=26.5. This via is through-hole to In2, "
            "so the route jogs to x=36.45 on In2 and does not punch a new via."
        ),
    }


def via_info(board) -> dict:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.20":
            continue
        if m.near(m.mm(t.GetPosition().x), 36.20) and m.near(m.mm(t.GetPosition().y), 20.80):
            return {
                "pos": [36.20, 20.80],
                "drill_mm": round(m.mm(t.GetDrillValue()), 3),
                "pad_mm": round(m.mm(t.GetWidth(F)), 3),
                "top": board.GetLayerName(t.TopLayer()),
                "bottom": board.GetLayerName(t.BottomLayer()),
                "through": board.GetLayerName(t.TopLayer()) == "F.Cu" and board.GetLayerName(t.BottomLayer()) == "B.Cu",
                "on": {name: bool(t.IsOnLayer(lid)) for name, lid in LAYERS},
            }
    return {}


def y6163_blocker(board):
    vias, holes, pads, tracks = collect(board, IN2)
    row = m.seg_clearance(44.25, 61.63, 55.78, 61.63, vias, holes, pads, tracks, IN2)
    return {
        "segment": [[44.25, 61.63], [55.78, 61.63]],
        "ok": row["ok"],
        "foreign_mm": row.get("foreign"),
        "foreign_item": row.get("foreign_item"),
        "why": "J18 pads are 1.700 mm circles on y=62.000. y=61.63 is inside the pad copper. Not placed.",
    }


def add_route(board):
    net = board.FindNet("P0.20")
    if net is None:
        raise SystemExit("P0.20 missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(m.xy(x1, y1))
        tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN2)
        tr.SetNet(net)
        board.Add(tr)


def counts_locked(before_counts, board):
    after = m.track_counts(board)
    bad = []
    for net, n in before_counts["tracks"].items():
        if net == "P0.20":
            continue
        if after["tracks"].get(net, 0) != n:
            bad.append(f"track {net} {n}->{after['tracks'].get(net, 0)}")
    for net, n in before_counts["vias"].items():
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get("P0.20", 0) != before_counts["vias"].get("P0.20", 0):
        bad.append("P0.20 via count changed")
    expect = before_counts["tracks"].get("P0.20", 0) + (len(POLY) - 1)
    if after["tracks"].get("P0.20", 0) != expect:
        bad.append(
            f"P0.20 tracks {before_counts['tracks'].get('P0.20', 0)}->"
            f"{after['tracks'].get('P0.20', 0)} expected {expect}"
        )
    # no In1 copper added for this net beyond what already existed
    in1 = [
        t for t in board.GetTracks()
        if t.GetNetname() == "P0.20" and t.GetClass() != "PCB_VIA" and t.GetLayer() == IN1
    ]
    if in1:
        bad.append(f"P0.20 In1 tracks present: {len(in1)}")
    return bad


def protect_ok(board) -> dict:
    return {
        "p016": m.poly_ok(board, b.P16, "P0.16", IN1),
        "p017": m.poly_ok(board, b.P17, "P0.17", IN2),
        "p019": m.poly_ok(board, P19, "P0.19", IN1),
        "p020_stub": any(
            t.GetNetname() == "P0.20" and t.GetLayer() == F and m.track_is(t, 36.75, 26.75, 36.20, 20.80)
            for t in board.GetTracks()
        ),
        "p020_via": m.via_at(board, "P0.20", 36.20, 20.80),
        "p016_via": m.via_at(board, "P0.16", 40.70, 20.80),
        "p017_via": m.via_at(board, "P0.17", 40.25, 23.10),
        "p019_via": m.via_at(board, "P0.19", 39.25, 23.10),
    }


def gained(before: dict, after: dict) -> dict:
    out = {}
    for k in set(before) | set(after):
        if k == "P0.20":
            continue
        if after.get(k, 0) > before.get(k, 0):
            out[k] = [before.get(k, 0), after.get(k, 0)]
    return out


def enrich(res):
    res["stats"]["p020_unconnected"] = res["stats"]["nongnd"].get("P0.20", 0)
    return res


def restore():
    shutil.copy2(BACKUP, BOARD)


def write_outputs(decision, info, before, after, reason, meas, skirt):
    ts = m.ist_now()
    bstat, a = before, after
    segs = [
        {"layer": "In2.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30bc",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.20",
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "pcb_blob_at_end": m.git_blob(),
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "head_matches_expected": info.get("git_head", "").startswith(EXPECTED_HEAD),
        "blob_matches_expected": info.get("pcb_blob") == EXPECTED_BLOB,
        "same_island": info["gap"]["same_island"],
        "far_island_layers": info["gap"]["far_island_layers"],
        "far_island_fcu_only": info["gap"]["far_island_fcu_only"],
        "u1_island_layers": info["gap"]["u1_island_layers"],
        "u1_island": info["gap"]["u1_island"],
        "far_island": info["gap"]["far_island"],
        "pad_edge_mm": info["gap"]["pad_edge_exact_mm"],
        "pad_edge_census_mm": 38.595,
        "straight_chord": info.get("chord"),
        "existing_via": info.get("via"),
        "layer_die_from_via": info.get("die"),
        "y_61_63_blocker": info.get("y6163"),
        "no_dodge": meas.get("no_dodge_vertical"),
        "whole_segment_crossing_test": skirt,
        "new_via": False,
        "third_in1_skirt": False,
        "via_punched_into_fcu_pad": False,
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
            for r in meas["segments"]
        ],
        "p020_opens_before": bstat.get("p020_unconnected"),
        "p020_opens_after": a.get("p020_unconnected"),
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
        "skirts_or_p019_crossed": skirt["crossed"],
        "skirts_ripped": False,
        "p019_ripped": False,
        "p017_not_retried": True,
        "p018_not_routed": True,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
    }
    (REPORTS / "PASS30BC_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BC_SUMMARY — P0.20",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.20",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**Expected tip/blob matched:** {payload['head_matches_expected']} / {payload['blob_matches_expected']}",
        f"**Ends already one island:** {info['gap']['same_island']}",
        f"**Far island layers:** {info['gap']['far_island_layers']}",
        f"**Far island F.Cu only:** {info['gap']['far_island_fcu_only']}",
        f"**U1 island layers:** {info['gap']['u1_island_layers']}",
        f"**Pad-edge (U1.35 to F.Cu 55.78 stub):** {info['gap']['pad_edge_exact_mm']:.6f} mm (census 38.595)",
        f"**Existing via:** {info.get('via')}",
        f"**New via:** no",
        f"**Third In1 skirt:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Crossing test failed:** {skirt['crossed']}",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**P0.20 opens:** {bstat.get('p020_unconnected')} → {a.get('p020_unconnected')}",
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
            f"F.Cu 0.18 mm ({info['chord']['from'][0]}, {info['chord']['from'][1]}) → "
            f"({info['chord']['to'][0]}, {info['chord']['to'][1]}), length {info['chord']['length_mm']} mm. "
            f"Crosses SiP body: {info['chord']['crosses_sip_body']}. "
            f"P0.06 via {info['chord']['p006']}. Not used."
        ),
        "",
        "## Layer exit from (36.20, 20.80)",
        "",
        info["die"]["note"],
        "",
        "## Whole-segment crossing test",
        "",
        skirt["method"],
        (
            f"Crossings: **{skirt['crossing_count']}**. "
            f"Min centerline to P0.16/P0.17: **{skirt['min_center_distance_to_p016_p017_mm']} mm** "
            f"vs {skirt['min_skirt_item']}. "
            f"Min centerline to P0.19: **{skirt['min_center_distance_to_p019_mm']} mm** "
            f"(0 means the same-centerline slot, not a transverse cross). "
            f"Stacks recorded: {len(skirt['p019_same_centerline_stacks'])}."
        ),
        "",
        "Per new segment, nearest of P0.16/P0.17:",
        "",
    ]
    for row in skirt["segments"]:
        near = row["nearest_skirt"]
        if near is None:
            lines.append(
                f"- ({row['start'][0]:.2f}, {row['start'][1]:.2f}) → ({row['end'][0]:.2f}, {row['end'][1]:.2f}) "
                f"crossed={row['crossed']}"
            )
        else:
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
        f"Probe (44.25, 61.63)–(55.78, 61.63) foreign {info['y6163']['foreign_mm']} mm vs {info['y6163']['foreign_item']}.",
        "",
        "## No-dodge check",
        "",
        str(meas.get("no_dodge_vertical")),
        "",
        "## Attempt",
        "",
    ]
    if placed:
        lines.append("In2.Cu 0.18 mm, no new via. Kept.")
    else:
        lines.append(reason)
        lines.append("")
        lines.append("Attempted corners (not left on the board):")
    lines.append("")
    for s in segs:
        lines.append(f"- ({s['start'][0]:.2f}, {s['start'][1]:.2f}) → ({s['end'][0]:.2f}, {s['end'][1]:.2f}) In2.Cu")
    lines += [
        "",
        "x=36.45 clears the P0.21 via (35.750, 23.100) that blocks a straight south exit. "
        "y=26.50 then x=44.25 is the In2 slot beside the P0.17 skirt (x=44.60) and on the P0.19 centerline. "
        "West dodge (44.25, 39.10)→(42.80, 39.90)→(44.25, 40.70) around P0.06 via (44.000, 39.900). "
        "Eastbound y=63.20, then north onto J18.8 (55.78, 62.00). No third In1 skirt. "
        "No via punched into the F.Cu stub. Skirts and the P0.19 run not ripped. x>24.2. No other net.",
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
        "| | unconnected | P0.20 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {bstat.get('unconnected_items')} | {bstat.get('p020_unconnected')} | {bstat.get('shorting_items')} | {bstat.get('clearance')} | {bstat.get('tracks_crossing')} | {bstat.get('hole_clearance')} | {bstat.get('hole_to_hole')} | {bstat.get('gnd_zone_islands')} |",
    ]
    if info.get("mid"):
        md = info["mid"]
        lines.append(
            f"| mid | {md.get('unconnected_items')} | {md.get('p020_unconnected')} | {md.get('shorting_items')} | {md.get('clearance')} | {md.get('tracks_crossing')} | {md.get('hole_clearance')} | {md.get('hole_to_hole')} | {md.get('gnd_zone_islands')} |"
        )
    lines += [
        f"| after | {a.get('unconnected_items')} | {a.get('p020_unconnected')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |",
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}.",
        "P0.16 / P0.17 skirts and the P0.19 run not ripped. No third In1 skirt. No new via. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BC_SUMMARY.md").write_text("\n".join(lines) + "\n")
    return ts


def patch_review(ts, decision, before, after, meas, info, skirt):
    text = REVIEW.read_text()
    if "## Pass30bc —" in text:
        return
    bstat, a = before, after
    if decision == "KEEP":
        route = (
            "Kept In2.Cu 0.18 mm, no new via: "
            "(36.20, 20.80)→(36.45, 20.80)→(36.45, 26.50)→(44.25, 26.50)→(44.25, 39.10)→"
            "(42.80, 39.90)→(44.25, 40.70)→(44.25, 63.20)→(55.78, 63.20)→(55.78, 62.00)."
        )
    else:
        route = "No copper left on the board."
    note = (
        f"\n## Pass30bc — P0.20 — {ts}\n\n"
        f"**Decision:** **{decision}**. {route} "
        f"Ends were already one island: {info['gap']['same_island']}. "
        f"Far island layers: {info['gap']['far_island_layers']}. "
        f"Pad-edge {info['gap']['pad_edge_exact_mm']:.6f} mm. "
        f"Straight chord hit P0.06 at {info['chord']['p006']['edge_clearance_mm']} mm and crosses the body; not used. "
        f"Whole-segment test crossings {skirt['crossing_count']}; "
        f"min center to P0.16/P0.17 {skirt['min_center_distance_to_p016_p017_mm']} mm. "
        f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
        f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
        f"P0.20 opens {bstat.get('p020_unconnected')}→{a.get('p020_unconnected')}. "
        f"Unconnected {bstat.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole {a.get('shorting_items')}/{a.get('clearance')}/"
        f"{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {bstat.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {bstat.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"No third In1 skirt. No via punched into an F.Cu-only pad. "
        f"Skirts and P0.19 not ripped. No other net. No Gerbers. No commit.\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    REVIEW.write_text(text + note)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    info = {
        "git_head": m.git_head(),
        "pcb_blob": m.git_blob(),
        "gained": {},
        "locked_ripped": False,
    }
    print("GIT", info["git_head"], info["pcb_blob"], flush=True)
    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BC_BEFORE.json"))
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = islands(board)
    info["via"] = via_info(board)
    info["chord"] = straight_chord(board)
    info["die"] = layer_die(board)
    info["y6163"] = y6163_blocker(board)
    info["fp"] = m.footprint_xy(board)
    info["counts"] = m.track_counts(board)
    info["protect_before"] = protect_ok(board)
    # known-bad self test: pass30ba's y=60.00 eastbound must be a crossing
    bad = whole_segment_crossing_test([(44.25, 39.10), (44.25, 60.00), (53.24, 60.00)])
    if not bad["crossed"]:
        raise SystemExit("crossing self-test failed to flag y=60.00 vs the skirts")
    skirt = whole_segment_crossing_test(POLY)
    meas = measure(board)
    print("GAP", info["gap"]["same_island"], "layers", info["gap"]["far_island_layers"],
          "pad", round(info["gap"]["pad_edge_exact_mm"], 6), flush=True)
    print("CHORD", info["chord"]["p006"], "body", info["chord"]["crosses_sip_body"], flush=True)
    print("VIA", info["via"], flush=True)
    print("SKIRT crossed", skirt["crossed"], "min16/17", skirt["min_center_distance_to_p016_p017_mm"],
          "stacks", len(skirt["p019_same_centerline_stacks"]), flush=True)
    print("MEASURE ok", meas["ok"], "f", meas["min_clearance_mm"], "p", meas["min_power_vin_mm"],
          "h", meas["min_hole_mm"], "land", meas["lands_on_j18_8"], flush=True)

    def finish(decision, reason, after_stats):
        ts = write_outputs(decision, info, bst, after_stats, reason, meas, skirt)
        patch_review(ts, decision, bst, after_stats, meas, info, skirt)
        print(decision, flush=True)
        print(reason, flush=True)

    if bst["unconnected_items"] != 57:
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Pre-edit unconnected is {bst['unconnected_items']} (need 57). No copper edited.",
            bst,
        )
        return
    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish(
            "NO-ROUTE",
            "U1.35 and J18.8 are already the same island. No copper added. Opens: "
            + json.dumps(info["gap"]["opens_if_separate"]),
            bst,
        )
        return
    if info["gap"]["far_island_fcu_only"]:
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish(
            "NO-ROUTE",
            "Far island is F.Cu only. No via punched into that pad or track. No copper added.",
            bst,
        )
        return
    if not info["via"].get("through"):
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish("NO-ROUTE", f"Existing via is not a through-via: {info['via']}. No copper added.", bst)
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if skirt["crossed"]:
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Whole-segment crossing test failed before copper was added: {skirt['crossings']}. No copper added.",
            bst,
        )
        return
    if not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BC_BEFORE.json", REPORTS / "DRC_PASS30BC_AFTER.json")
        finish(
            "NO-ROUTE",
            "In2 x=44.25 slot blocked. "
            f"foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']}, "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']}, "
            f"hole {meas['min_hole_mm']} vs {meas['min_hole_item']}, "
            f"land {meas['lands_on_j18_8']}, segments {meas['segment_count']}. "
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
    pa = protect_ok(board)
    skirt_after = whole_segment_crossing_test(POLY)
    if moved or ripped or not all(pa.values()) or not m.poly_ok(board, POLY, "P0.20", IN2) or skirt_after["crossed"]:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BC_AFTER.json"))
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
    mid = enrich(m.run_drc(REPORTS / "DRC_PASS30BC_MID.json"))
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["p020_unconnected"] - mst["p020_unconnected"]
    board2 = pcbnew.LoadBoard(str(BOARD))
    skirts_intact = protect_ok(board2)
    skirt_on_disk = whole_segment_crossing_test(POLY)
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
        and m.poly_ok(board2, POLY, "P0.20", IN2)
        and mst["unconnected_items"] <= bst["unconnected_items"] - 1
    )
    if not gate_ok:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BC_AFTER.json"))
        ast = after["stats"]
        match = (
            ast["unconnected_items"] == bst["unconnected_items"]
            and ast["p020_unconnected"] == bst["p020_unconnected"]
            and ast["shorting_items"] == bst["shorting_items"]
            and ast["clearance"] == bst["clearance"]
            and ast["tracks_crossing"] == bst["tracks_crossing"]
            and ast["hole_clearance"] == bst["hole_clearance"]
            and ast["hole_to_hole"] == bst["hole_to_hole"]
        )
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.20 opens {bst['p020_unconnected']}→{mst['p020_unconnected']} (need drop ≥ 1). "
            f"Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
            f"Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
            f"Locked intact: {all(skirts_intact.values())}. "
            f"Post-revert DRC matches pre-edit: {match} "
            f"(unc {ast['unconnected_items']}, P0.20 {ast['p020_unconnected']}, "
            f"short/clearance/crossing/hole "
            f"{ast['shorting_items']}/{ast['clearance']}/{ast['tracks_crossing']}/{ast['hole_clearance']}, "
            f"hole_to_hole {ast['hole_to_hole']}, GND islands {ast['gnd_zone_islands']}). "
            f"Blob matches pre-edit: {info['reverted_blob_match']}. No second path."
        )
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30BC_MID.json", REPORTS / "DRC_PASS30BC_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. In2.Cu x=44.25 slot, {len(POLY) - 1} new segments, no new via. "
        f"Whole-segment crossing test: 0 crossings "
        f"(min center to P0.16/P0.17 {skirt['min_center_distance_to_p016_p017_mm']} mm; "
        f"P0.19 same-centerline stacks {len(skirt['p019_same_centerline_stacks'])}, not crossings). "
        f"P0.20 opens {bst['p020_unconnected']}→{mst['p020_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. No third In1 skirt. Skirts and P0.19 not ripped."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
