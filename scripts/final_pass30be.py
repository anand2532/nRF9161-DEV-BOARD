#!/usr/bin/env python3
"""pass30be — ONE attempt: SIM_RST only.

U1.43 is F.Cu-only. The P0.25 flank at x=32.71 clears the via by exactly
0.150 mm, but a north run through that x crosses the locked SIM_CLK In1
diagonal. A 0.60 mm via does not fit between COEX0 B.Cu x=32.25 and the
P0.25 F.Cu stub x=33.25. One 0.50/0.30 through-via at (32.75, 25.50)
(foreign 0.160 mm) leaves on In1 west of the skirts, north of the SIM_CLK
run, and lands on the existing through-via (78.00, 36.00).

No second path. No other net.
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
BACKUP = ROOT / ".mcp-backups/pass30be/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
F, B, IN1, IN2 = m.F, m.B, m.IN1, m.IN2
W = m.W
CF = m.CF
CP = m.CP
LAYERS = m.LAYERS
NET = "SIM_RST"
EXPECTED_HEAD = "2201658"
EXPECTED_BLOB = "036e870670d173055c85ca41c994405c95fbb4e8"
VIA_D = 0.50
VIA_DRILL = 0.30
VIA_XY = (32.75, 25.50)

# F.Cu neck onto the new via, then In1 west of the body, north of SIM_CLK,
# east of the skirt caps, south clear of VDD2, onto through-via (78, 36).
POLY = [
    (32.71, 26.40, F, "F.Cu"),
    (32.75, 25.50, F, "F.Cu"),
    (26.20, 25.50, IN1, "In1.Cu"),
    (26.20, 17.60, IN1, "In1.Cu"),
    (55.30, 17.60, IN1, "In1.Cu"),
    (55.30, 18.50, IN1, "In1.Cu"),
    (68.00, 18.50, IN1, "In1.Cu"),
    (68.00, 35.40, IN1, "In1.Cu"),
    (78.00, 35.40, IN1, "In1.Cu"),
    (78.00, 36.00, IN1, "In1.Cu"),
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
SIM = [
    (31.25, 23.10), (33.60, 22.40), (33.60, 19.20), (39.40, 19.20),
    (39.40, 20.05), (56.00, 20.05), (56.00, 19.55), (57.20, 19.55),
    (57.20, 36.00), (73.30, 36.00),
]
LOCKED = [
    ("P0.16", "In1.Cu", P16),
    ("P0.17", "In2.Cu", P17),
    ("P0.19", "In1.Cu", P19),
    ("P0.20", "In2.Cu", P20),
    ("SIM_CLK", "In1.Cu", SIM),
]


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
    if abs(x1 - x2) < 1e-6 and abs(x1 - 44.25) < 1e-3:
        return True
    if abs(x1 - x2) < 1e-6 and abs(x1 - 44.60) < 1e-3:
        return True
    if abs(y1 - y2) < 1e-6 and abs(y1 - 63.20) < 1e-3 and min(x1, x2) < 56.0 and max(x1, x2) > 44.0:
        return True
    return False


def whole_segment_crossing_test(poly_xy):
    rows = []
    crossings = []
    min_skirt = None
    for (x1, y1), (x2, y2) in zip(poly_xy, poly_xy[1:]):
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
            for i in range(n + 1):
                t = i / n
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                d = m.dps(px, py, a[0], a[1], c[0], c[1])
                if d < sample_min:
                    sample_min = d
                if d <= 1e-4 and closest_is_interior(px, py, a, c):
                    interior_hits.append({"at": [round(px, 4), round(py, 4)]})
            use = min(dist, sample_min)
            item = (use, sk["net"], [list(a), list(c)])
            if seg_skirt is None or item[0] < seg_skirt[0]:
                seg_skirt = item
            if min_skirt is None or item[0] < min_skirt[0]:
                min_skirt = item
            if coli or proper or interior_hits:
                seg_cross = sk["net"]
                crossings.append({
                    "segment": [[x1, y1], [x2, y2]],
                    "locked_net": sk["net"],
                    "locked_layer": sk["layer"],
                    "locked": [list(a), list(c)],
                    "proper_interior": proper,
                    "collinear_stack": coli,
                    "interior_sample_hits": interior_hits[:4],
                    "min_center_distance_mm": round(use, 6),
                })
        if forbidden_stack(x1, y1, x2, y2):
            seg_cross = seg_cross or "stacked-centerline"
            crossings.append({
                "segment": [[x1, y1], [x2, y2]],
                "locked_net": "stacked-centerline",
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
            "against P0.16, P0.17, P0.19, P0.20, and the SIM_CLK In1 run. "
            "Layers are not exempt. A same-centerline stack on x=44.25, x=44.60, "
            "or the y=63.20 eastbounds is a fail. Endpoint-only touches are not crossings."
        ),
        "crossed": bool(crossings),
        "crossing_count": len(crossings),
        "crossings": crossings,
        "min_center_distance_to_locked_mm": None if min_skirt is None else round(min_skirt[0], 4),
        "min_locked_item": None if min_skirt is None else {"net": min_skirt[1], "segment": min_skirt[2]},
        "segments": rows,
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


def shape_clearance(board, layer, x1, y1, x2, y2):
    """True copper clearance (shape), not endpoint-only segseg."""
    sh = pcbnew.SHAPE_SEGMENT(m.xy(x1, y1), m.xy(x2, y2), pcbnew.FromMM(W))
    worst = pwr = hh = None
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == NET:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
            if x < min(x1, x2) - 4 or x > max(x1, x2) + 4 or y < min(y1, y2) - 4 or y > max(y1, y2) + 4:
                continue
            r = m.mm(t.GetWidth(layer)) / 2
            clr = m.dps(x, y, x1, y1, x2, y2) - r - (W / 2)
            desc = f"via@{x:.3f},{y:.3f}"
            isp = net in m.POWER
            if worst is None or clr < worst[0]:
                worst = (clr, net, desc)
            if isp and (pwr is None or clr < pwr[0]):
                pwr = (clr, net, desc)
            hclr = m.dps(x, y, x1, y1, x2, y2) - m.mm(t.GetDrillValue()) / 2 - (W / 2)
            hdesc = f"via {net} @{x:.3f},{y:.3f}"
            if hh is None or hclr < hh[0]:
                hh = (hclr, hdesc)
        elif t.GetLayer() == layer:
            a, b, c, d = m.ends(t)
            if max(a, c) < min(x1, x2) - 3 or min(a, c) > max(x1, x2) + 3:
                continue
            if max(b, d) < min(y1, y2) - 3 or min(b, d) > max(y1, y2) + 3:
                continue
            other = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
            clr = m.mm(sh.GetClearance(other))
            desc = f"trk ({a:.2f},{b:.2f})-({c:.2f},{d:.2f})"
            isp = net in m.POWER
            if worst is None or clr < worst[0]:
                worst = (clr, net, desc)
            if isp and (pwr is None or clr < pwr[0]):
                pwr = (clr, net, desc)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == NET or not p.IsOnLayer(layer):
                continue
            x, y = m.mm(p.GetPosition().x), m.mm(p.GetPosition().y)
            if x < min(x1, x2) - 5 or x > max(x1, x2) + 5 or y < min(y1, y2) - 5 or y > max(y1, y2) + 5:
                continue
            clr = m.mm(sh.GetClearance(p.GetEffectiveShape(layer)))
            desc = f"pad {fp.GetReference()}.{p.GetNumber()}"
            isp = net in m.POWER
            if worst is None or clr < worst[0]:
                worst = (clr, net, desc)
            if isp and (pwr is None or clr < pwr[0]):
                pwr = (clr, net, desc)
            if p.GetDrillSize().x:
                hclr = m.dps(x, y, x1, y1, x2, y2) - m.mm(p.GetDrillSize().x) / 2 - (W / 2)
                hdesc = f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]"
                if hh is None or hclr < hh[0]:
                    hh = (hclr, hdesc)
    body = m.body_hit(x1, y1, x2, y2)
    foreign_ok = worst is None or worst[0] >= CF - 1e-9
    power_ok = pwr is None or pwr[0] >= CP - 1e-9
    hole_ok = hh is None or hh[0] >= m.HOLE - 1e-9
    return {
        "ok": foreign_ok and power_ok and hole_ok and not body,
        "foreign": None if worst is None else round(worst[0], 4),
        "foreign_exact": None if worst is None else worst[0],
        "foreign_item": None if worst is None else {"net": worst[1], "item": worst[2]},
        "power": None if pwr is None else round(pwr[0], 4),
        "power_exact": None if pwr is None else pwr[0],
        "power_item": None if pwr is None else {"net": pwr[1], "item": pwr[2]},
        "hole": None if hh is None else round(hh[0], 4),
        "hole_item": None if hh is None else hh[1],
        "body": body,
        "why": "body_or_keepout" if body else None,
    }


def p025_flank(board):
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.25":
            continue
        x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
        if abs(x - 33.25) < 0.02 and abs(y - 23.10) < 0.02:
            via = t
            break
    out = {"via": None, "candidates": []}
    if via is None:
        return out
    r = m.mm(via.GetWidth(F)) / 2
    out["via"] = {
        "xy": [m.mm(via.GetPosition().x), m.mm(via.GetPosition().y)],
        "width_mm": m.mm(via.GetWidth(F)),
        "radius_mm": r,
        "drill_mm": m.mm(via.GetDrillValue()),
        "pos_nm": [via.GetPosition().x, via.GetPosition().y],
    }
    for x in (32.71, 32.70, 32.69):
        seg = pcbnew.SHAPE_SEGMENT(m.xy(x, 26.40), m.xy(x, 21.50), pcbnew.FromMM(W))
        pad = pcbnew.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(F) // 2)
        copper = m.mm(seg.GetClearance(pad))
        center = abs(m.mm(via.GetPosition().x) - x)
        hole = center - m.mm(via.GetDrillValue()) / 2 - (W / 2)
        out["candidates"].append({
            "x": x,
            "stored_x_nm": int(pcbnew.FromMM(x)),
            "copper_clearance_mm": copper,
            "hole_clearance_mm": hole,
            "center_distance_mm": center,
            "under_0_15": copper < 0.15 - 1e-12,
            "meets_gate": copper >= 0.15 - 1e-12,
        })
    return out


def straight_chord(board) -> dict:
    ax, ay = 32.897, 27.128
    bx, by = 71.597, 43.764
    hit = None
    for t in board.GetTracks():
        if t.GetNetname() != "VDD1" or t.GetClass() == "PCB_VIA" or t.GetLayer() != F:
            continue
        a, b, c, d = m.ends(t)
        if abs(a - 50.68) > 0.02 or abs(c - 50.68) > 0.02:
            continue
        if min(b, d) > 31.05 or max(b, d) < 34.95:
            continue
        proper = interior_cross((ax, ay), (bx, by), (a, b), (c, d))
        edge = -(W / 2 + m.mm(t.GetWidth()) / 2) if proper else None
        hit = {
            "track": [a, b, c, d],
            "width_mm": m.mm(t.GetWidth()),
            "proper_cross": proper,
            "edge_clearance_mm": edge,
        }
        break
    return {
        "from_existing_copper": [ax, ay],
        "to_join_point": [bx, by],
        "width_mm": W,
        "layer": "F.Cu",
        "length_mm": round(math.hypot(bx - ax, by - ay), 6),
        "crosses_sip_body": m.crosses_body(ax, ay, bx, by),
        "vdd1": hit,
        "used": False,
        "note": "Straight F.Cu chord crosses VDD1 (50.68, 35.00)-(50.68, 31.00) at -0.29 mm. Not used.",
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
                "kind": "pad", "name": f"{fp.GetReference()}.{p.GetNumber()}",
                "x": m.mm(p.GetPosition().x), "y": m.mm(p.GetPosition().y),
                "layers": layers, "obj": p,
            })
    for t in board.GetTracks():
        if t.GetNetname() != NET:
            continue
        if t.GetClass() == "PCB_VIA":
            layers = [lid for _, lid in LAYERS if t.IsOnLayer(lid)]
            items.append({
                "kind": "via",
                "name": f"via@{m.mm(t.GetPosition().x):.3f},{m.mm(t.GetPosition().y):.3f}",
                "x": m.mm(t.GetPosition().x), "y": m.mm(t.GetPosition().y),
                "layers": layers, "obj": t,
                "through": (
                    board.GetLayerName(t.TopLayer()) == "F.Cu"
                    and board.GetLayerName(t.BottomLayer()) == "B.Cu"
                ),
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
                "layers": [t.GetLayer()], "obj": t,
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

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.43")
    far_i = next(
        i for i, it in enumerate(items)
        if "B.Cu (71.680,43.800)-(71.680,48.000)" in it["name"]
        or "B.Cu (71.680,48.000)-(71.680,43.800)" in it["name"]
    )
    same = find(u1) == find(far_i)

    def names(root_idx):
        return [items[i]["name"] for i in range(len(items)) if find(i) == find(root_idx)]

    def layer_names(root_idx):
        lids = set()
        for i in range(len(items)):
            if find(i) == find(root_idx):
                lids.update(items[i]["layers"])
        return [name for name, lid in LAYERS if lid in lids]

    u = items[u1]["obj"]
    far = items[far_i]
    gap = m.mm(u.GetEffectiveShape(F).GetClearance(shp_of(far, B)))
    through = [
        {"name": it["name"], "xy": [round(it["x"], 3), round(it["y"], 3)]}
        for it in items
        if it["kind"] == "via" and it.get("through") and find(items.index(it)) == find(far_i)
    ]
    # items.index is wrong if duplicates; use enumeration
    through = []
    for i, it in enumerate(items):
        if it["kind"] == "via" and it.get("through") and find(i) == find(far_i):
            through.append({"name": it["name"], "xy": [round(it["x"], 3), round(it["y"], 3)]})
    return {
        "same_island": same,
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "u1_island": names(u1),
        "u1_island_layers": layer_names(u1),
        "far_island": names(far_i),
        "far_island_layers": layer_names(far_i),
        "far_through_vias": through,
        "far_track": far["name"],
        "bcu_only": layer_names(far_i) == ["B.Cu"],
    }


def measure(board):
    rows = []
    mf = mp = mh = None
    xy = [(p[0], p[1]) for p in POLY]
    layers = [(p[2], p[3]) for p in POLY]
    for (x1, y1), (x2, y2), (lid, lname) in zip(xy, xy[1:], layers[1:]):
        # layer of the segment is the end point's layer; first segment is F
        pass
    segs = []
    for i in range(len(POLY) - 1):
        x1, y1, lid, lname = POLY[i]
        x2, y2, lid2, lname2 = POLY[i + 1]
        # segment lives on the layer shared; neck is F, rest In1. Use the layer of the later point
        # except the first segment which is entirely F (both points tagged F then the second point is the via).
        use_lid, use_name = (lid, lname) if i == 0 else (lid2, lname2)
        if i == 0:
            use_lid, use_name = F, "F.Cu"
        else:
            use_lid, use_name = IN1, "In1.Cu"
        row = shape_clearance(board, use_lid, x1, y1, x2, y2)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
        row["layer"] = use_name
        rows.append(row)
        if row.get("foreign_exact") is not None and (mf is None or row["foreign_exact"] < mf[0]):
            mf = (row["foreign_exact"], row["foreign_item"])
        if row.get("power_exact") is not None and (mp is None or row["power_exact"] < mp[0]):
            mp = (row["power_exact"], row["power_item"])
        if row.get("hole") is not None and (mh is None or row["hole"] < mh[0]):
            mh = (row["hole"], row["hole_item"])
    # land on far through-via
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != NET:
            continue
        if m.near(m.mm(t.GetPosition().x), 78.00) and m.near(m.mm(t.GetPosition().y), 36.00):
            via = t
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2][:2]), m.xy(*POLY[-1][:2]), pcbnew.FromMM(W))
    hits = False
    if via is not None:
        pad = pcbnew.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(IN1) // 2)
        hits = bool(land.Collide(pad))
    # new via copper vs foreign, using a circle not a track
    vx, vy = VIA_XY
    vworst = vpwr = vhh = None
    circ = {lid: pcbnew.SHAPE_CIRCLE(m.xy(vx, vy), pcbnew.FromMM(VIA_D / 2)) for _, lid in LAYERS}
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == NET:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
            r = max(m.mm(t.GetWidth(lid)) / 2 for _, lid in LAYERS)
            clr = math.hypot(x - vx, y - vy) - r - VIA_D / 2
            if vworst is None or clr < vworst[0]:
                vworst = (clr, net, f"via@{x:.3f},{y:.3f}")
            if net in m.POWER and (vpwr is None or clr < vpwr[0]):
                vpwr = (clr, net, f"via@{x:.3f},{y:.3f}")
            hclr = math.hypot(x - vx, y - vy) - m.mm(t.GetDrillValue()) / 2 - VIA_DRILL / 2
            if vhh is None or hclr < vhh[0]:
                vhh = (hclr, f"via {net} @{x:.3f},{y:.3f}")
        else:
            a, b, c, d = m.ends(t)
            if max(a, c) < vx - 4 or min(a, c) > vx + 4 or max(b, d) < vy - 4 or min(b, d) > vy + 4:
                continue
            clr = m.dps(vx, vy, a, b, c, d) - m.mm(t.GetWidth()) / 2 - VIA_D / 2
            if vworst is None or clr < vworst[0]:
                vworst = (clr, net, f"{board.GetLayerName(t.GetLayer())} trk ({a:.2f},{b:.2f})-({c:.2f},{d:.2f})")
            if net in m.POWER and (vpwr is None or clr < vpwr[0]):
                vpwr = (clr, net, f"{board.GetLayerName(t.GetLayer())} trk")
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == NET:
                continue
            x, y = m.mm(p.GetPosition().x), m.mm(p.GetPosition().y)
            if abs(x - vx) > 6 or abs(y - vy) > 6:
                continue
            for lname, lid in LAYERS:
                if not p.IsOnLayer(lid):
                    continue
                clr = m.mm(circ[lid].GetClearance(p.GetEffectiveShape(lid)))
                if vworst is None or clr < vworst[0]:
                    vworst = (clr, net, f"pad {fp.GetReference()}.{p.GetNumber()}")
                if net in m.POWER and (vpwr is None or clr < vpwr[0]):
                    vpwr = (clr, net, f"pad {fp.GetReference()}.{p.GetNumber()}")
    via_ok = (
        (vworst is None or vworst[0] >= CF - 1e-9)
        and (vpwr is None or vpwr[0] >= CP - 1e-9)
        and (vhh is None or vhh[0] >= 0.25 - 1e-9)
        and not (28.0 <= vx <= 44.0 and 26.75 <= vy <= 37.25)
    )
    if vworst is not None and (mf is None or vworst[0] < mf[0]):
        mf = (vworst[0], {"net": vworst[1], "item": vworst[2]})
    if vpwr is not None and (mp is None or vpwr[0] < mp[0]):
        mp = (vpwr[0], {"net": vpwr[1], "item": vpwr[2]})
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits
        and via_ok
        and nseg <= 10
        and min(p[0] for p in POLY) > 24.2
        and not any(r["body"] for r in rows)
    )
    return {
        "segments": rows,
        "segment_count": nseg,
        "min_clearance_mm": None if mf is None else round(mf[0], 4),
        "min_clearance_exact": None if mf is None else mf[0],
        "min_clearance_item": None if mf is None else mf[1],
        "min_power_vin_mm": None if mp is None else round(mp[0], 4),
        "min_power_exact": None if mp is None else mp[0],
        "min_power_vin_item": None if mp is None else mp[1],
        "min_hole_mm": None if mh is None else mh[0],
        "min_hole_item": None if mh is None else mh[1],
        "lands_on_far_via": hits,
        "new_via": {
            "xy": list(VIA_XY),
            "diameter_mm": VIA_D,
            "drill_mm": VIA_DRILL,
            "ok": via_ok,
            "foreign_mm": None if vworst is None else round(vworst[0], 4),
            "foreign_item": None if vworst is None else {"net": vworst[1], "item": vworst[2]},
            "power_mm": None if vpwr is None else round(vpwr[0], 4),
            "hole_mm": None if vhh is None else round(vhh[0], 4),
            "hole_item": None if vhh is None else vhh[1],
        },
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= m.HOLE - 1e-9,
        "ok": ok,
        "width_mm": W,
    }


def add_route(board):
    net = board.FindNet(NET)
    if net is None:
        raise SystemExit("SIM_RST missing")
    for i in range(len(POLY) - 1):
        x1, y1 = POLY[i][0], POLY[i][1]
        x2, y2 = POLY[i + 1][0], POLY[i + 1][1]
        lid = F if i == 0 else IN1
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(m.xy(x1, y1))
        tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(lid)
        tr.SetNet(net)
        board.Add(tr)
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(m.xy(*VIA_XY))
    via.SetWidth(pcbnew.FromMM(VIA_D))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetLayerPair(F, B)
    via.SetNet(net)
    board.Add(via)


def protect_ok(board) -> dict:
    return {
        "p016": m.poly_ok(board, P16, "P0.16", IN1),
        "p017": m.poly_ok(board, P17, "P0.17", IN2),
        "p019": m.poly_ok(board, P19, "P0.19", IN1),
        "p020": m.poly_ok(board, P20, "P0.20", IN2),
        "sim_clk": m.poly_ok(board, SIM, "SIM_CLK", IN1),
    }


def counts_locked(before_counts, board):
    after = m.track_counts(board)
    bad = []
    for net, n in before_counts["tracks"].items():
        if net == NET:
            continue
        if after["tracks"].get(net, 0) != n:
            bad.append(f"track {net} {n}->{after['tracks'].get(net, 0)}")
    for net, n in before_counts["vias"].items():
        if net == NET:
            continue
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get(NET, 0) != before_counts["vias"].get(NET, 0) + 1:
        bad.append(
            f"SIM_RST vias {before_counts['vias'].get(NET, 0)}->{after['vias'].get(NET, 0)}"
        )
    expect = before_counts["tracks"].get(NET, 0) + (len(POLY) - 1)
    if after["tracks"].get(NET, 0) != expect:
        bad.append(
            f"SIM_RST tracks {before_counts['tracks'].get(NET, 0)}->"
            f"{after['tracks'].get(NET, 0)} expected {expect}"
        )
    return bad


def gained(before: dict, after: dict) -> dict:
    out = {}
    for k in set(before) | set(after):
        if k == NET:
            continue
        if after.get(k, 0) > before.get(k, 0):
            out[k] = [before.get(k, 0), after.get(k, 0)]
    return out


def enrich(res):
    res["stats"]["sim_rst_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
    return res


def restore():
    shutil.copy2(BACKUP, BOARD)


def poly_xy():
    return [(p[0], p[1]) for p in POLY]


def write_outputs(decision, info, before, after, reason, meas, skirt):
    ts = m.ist_now()
    bstat, a = before, after
    placed = decision == "KEEP"
    segs = []
    for i in range(len(POLY) - 1):
        lname = "F.Cu" if i == 0 else "In1.Cu"
        segs.append({
            "layer": lname,
            "width_mm": W,
            "start": [POLY[i][0], POLY[i][1]],
            "end": [POLY[i + 1][0], POLY[i + 1][1]],
        })
    flank = info.get("flank") or {}
    cand = None
    for c in flank.get("candidates") or []:
        if abs(c["x"] - 32.71) < 1e-9:
            cand = c
    payload = {
        "pass": "30be",
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
        "far_bcu_only": info["gap"]["bcu_only"],
        "far_through_vias": info["gap"]["far_through_vias"],
        "pad_edge_mm": info["gap"]["pad_edge_exact_mm"],
        "pad_edge_census_mm": 42.124,
        "straight_chord": info.get("chord"),
        "p025_flank": flank,
        "p025_x": 32.71,
        "p025_clearance_mm": None if cand is None else cand["copper_clearance_mm"],
        "p025_x_decision": (
            "rejected as a through-run: copper clearance is exactly 0.150000 mm "
            "(not under 0.15) but continuing north crosses SIM_CLK In1 "
            "(31.25, 23.10)-(33.60, 22.40) at about (32.71, 22.665). "
            "The kept neck stops at the via (32.75, 25.50) and does not pass the P0.25 via."
        ),
        "whole_segment_crossing_test": skirt,
        "new_via": placed,
        "new_via_spec": meas.get("new_via"),
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
                "start": r["start"], "end": r["end"], "layer": r.get("layer"),
                "ok": r["ok"], "body": r.get("body"),
                "foreign_mm": r.get("foreign"), "foreign_item": r.get("foreign_item"),
                "power_mm": r.get("power"), "power_item": r.get("power_item"),
                "hole_mm": r.get("hole"), "hole_item": r.get("hole_item"),
                "why": r.get("why"),
            }
            for r in meas.get("segments", [])
        ],
        "sim_rst_opens_before": bstat.get("sim_rst_unconnected"),
        "sim_rst_opens_after": a.get("sim_rst_unconnected"),
        "unconnected_before": bstat.get("unconnected_items"),
        "unconnected_after": a.get("unconnected_items"),
        "short_clearance_crossing_hole_before": [
            bstat.get("shorting_items"), bstat.get("clearance"),
            bstat.get("tracks_crossing"), bstat.get("hole_clearance"),
        ],
        "short_clearance_crossing_hole_after": [
            a.get("shorting_items"), a.get("clearance"),
            a.get("tracks_crossing"), a.get("hole_clearance"),
        ],
        "hole_to_hole_before": bstat.get("hole_to_hole"),
        "hole_to_hole_after": a.get("hole_to_hole"),
        "gnd_islands_before": bstat.get("gnd_zone_islands"),
        "gnd_islands_after": a.get("gnd_zone_islands"),
        "other_nongnd_gained": info.get("gained", {}),
        "reason": reason,
        "skirts_crossed_or_stacked": skirt.get("crossed"),
        "skirts_ripped": False,
        "sim_clk_ripped_or_stacked": bool(skirt.get("crossed")),
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
    }
    (REPORTS / "PASS30BE_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BE_SUMMARY — SIM_RST",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** SIM_RST",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**Expected tip/blob matched:** {payload['head_matches_expected']} / {payload['blob_matches_expected']}",
        f"**Ends already one island:** {info['gap']['same_island']}",
        f"**Far island layers:** {info['gap']['far_island_layers']}",
        f"**Far island B.Cu-only:** {info['gap']['bcu_only']}",
        f"**Far through-vias:** {info['gap']['far_through_vias']}",
        f"**U1 island layers:** {info['gap']['u1_island_layers']}",
        f"**Pad-edge (U1.43 to B.Cu x=71.68 track):** {info['gap']['pad_edge_exact_mm']:.6f} mm (census 42.124)",
        f"**P0.25 flank x=32.71 copper clearance:** {None if cand is None else round(cand['copper_clearance_mm'], 6)} mm "
        f"(stored x nm {None if cand is None else cand['stored_x_nm']}; under 0.15: {None if cand is None else cand['under_0_15']})",
        "**P0.25 x decision:** rejected as a through-run. Clearance is exactly 0.150 mm, not under the gate, "
        "but the north continuation crosses SIM_CLK In1 at (32.71, 22.665). Kept route does not pass that via.",
        f"**New via:** {'yes (32.75, 25.50) 0.50/0.30 through' if placed else 'no'}",
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Crossing test failed:** {skirt.get('crossed')}",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**SIM_RST opens:** {bstat.get('sim_rst_unconnected')} → {a.get('sim_rst_unconnected')}",
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
            f"F.Cu 0.18 mm {info['chord']['from_existing_copper']} → {info['chord']['to_join_point']}, "
            f"length {info['chord']['length_mm']} mm. Crosses SiP body: {info['chord']['crosses_sip_body']}. "
            f"VDD1 {info['chord']['vdd1']}. Not used."
        ),
        "",
        "## P0.25 flank",
        "",
        f"Via: {flank.get('via')}",
        "",
    ]
    for c in flank.get("candidates") or []:
        lines.append(
            f"- x={c['x']:.2f} stored_nm={c['stored_x_nm']} copper={c['copper_clearance_mm']:.6f} mm "
            f"hole={c['hole_clearance_mm']:.6f} mm under_0.15={c['under_0_15']}"
        )
    lines += [
        "",
        "## Whole-segment crossing test",
        "",
        skirt.get("method", ""),
        (
            f"Crossings: **{skirt.get('crossing_count')}**. "
            f"Min centerline to a locked run: **{skirt.get('min_center_distance_to_locked_mm')} mm** "
            f"vs {skirt.get('min_locked_item')}."
        ),
        "",
    ]
    for row in skirt.get("segments", []):
        near = row.get("nearest_skirt") or {}
        lines.append(
            f"- {tuple(row['start'])} → {tuple(row['end'])} crossed={row['crossed']} "
            f"nearest {near.get('net')} {near.get('segment')} center {near.get('center_distance_mm')} mm "
            f"(edge {near.get('edge_clearance_mm')} mm), {row['samples']} samples"
        )
    lines += ["", "## Attempt", ""]
    if placed:
        lines.append("F.Cu neck plus In1.Cu, one 0.50/0.30 through-via. Kept.")
        lines.append("")
        lines.append(f"- via (32.75, 25.50) drill 0.30 diameter 0.50 through")
        for s in segs:
            lines.append(f"- {tuple(s['start'])} → {tuple(s['end'])} {s['layer']} {s['width_mm']} mm")
    else:
        lines.append("No copper left on the board.")
    lines += [
        "",
        "West of the SiP on In1 at x=26.20 (east of the RF keepout x=24.2), north at y=17.60 "
        "(north of the skirt cap y=20.80 and of the SIM_CLK run), east to x=68.00, south to y=35.40 "
        "(0.60 mm centerline off the SIM_CLK y=36.00 run), east onto through-via (78.00, 36.00). "
        "x=44.25 and x=44.60 not used. Sealed y=44.60 pocket not entered. No header or U1 move. "
        "Skirts not ripped and not stacked. SIM_CLK run not ripped and not stacked. No other net.",
        "",
        "## Clearance by segment",
        "",
    ]
    nv = meas.get("new_via") or {}
    if nv:
        lines.append(
            f"- via (32.75, 25.50) 0.50 mm ok={nv.get('ok')} foreign={nv.get('foreign_mm')} vs {nv.get('foreign_item')} "
            f"power={nv.get('power_mm')} hole={nv.get('hole_mm')} vs {nv.get('hole_item')}"
        )
    for r in meas.get("segments", []):
        lines.append(
            f"- {r.get('layer')} {tuple(r['start'])}–{tuple(r['end'])} ok={r['ok']} "
            f"foreign={r.get('foreign')} vs {r.get('foreign_item')} "
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
        "| | unconnected | SIM_RST | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        (
            f"| before | {bstat.get('unconnected_items')} | {bstat.get('sim_rst_unconnected')} | "
            f"{bstat.get('shorting_items')} | {bstat.get('clearance')} | {bstat.get('tracks_crossing')} | "
            f"{bstat.get('hole_clearance')} | {bstat.get('hole_to_hole')} | {bstat.get('gnd_zone_islands')} |"
        ),
        (
            f"| after | {a.get('unconnected_items')} | {a.get('sim_rst_unconnected')} | "
            f"{a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | "
            f"{a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |"
        ),
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}",
        "P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. SIM_CLK In1 run not ripped and not stacked. "
        "No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BE_SUMMARY.md").write_text("\n".join(lines) + "\n")
    para = (
        f"\n## Pass30be — SIM_RST — {ts}\n\n"
        f"**Decision:** **{decision}**. Pad-edge {info['gap']['pad_edge_exact_mm']:.6f} mm (census 42.124). "
        f"P0.25 flank at x=32.71 remeasured {None if cand is None else round(cand['copper_clearance_mm'], 6)} mm "
        f"(exact 0.150, not under 0.15); that x was not used as a through-run because it crosses SIM_CLK In1 "
        f"at (32.71, 22.665). Straight F.Cu chord hits VDD1 (50.68, 35)-(50.68, 31) at -0.29 mm; not used. "
    )
    if placed:
        para += (
            f"Kept 9 segments (1 F.Cu + 8 In1.Cu) and one 0.50/0.30 through-via at (32.75, 25.50), "
            f"landing on existing through-via (78.00, 36.00). "
            f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
            f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
            f"SIM_RST opens {bstat.get('sim_rst_unconnected')}→{a.get('sim_rst_unconnected')}. "
            f"Unconnected {bstat.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"short/clearance/crossing/hole "
            f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
            f"hole_to_hole {a.get('hole_to_hole')}. "
            f"GND islands {bstat.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        )
    else:
        para += f"{reason} "
    para += (
        "Four skirts and the SIM_CLK run not ripped or stacked. No other net. No Gerbers. No commit.\n"
    )
    REVIEW.write_text(REVIEW.read_text() + para)


def main():
    info = {"git_head": m.git_head(), "pcb_blob": m.git_blob()}
    print("HEAD", info["git_head"], "BLOB", info["pcb_blob"], flush=True)
    if not info["git_head"].startswith(EXPECTED_HEAD) or info["pcb_blob"] != EXPECTED_BLOB:
        raise SystemExit(
            f"STOP mismatch head={info['git_head']} blob={info['pcb_blob']}"
        )
    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = islands(board)
    info["chord"] = straight_chord(board)
    info["flank"] = p025_flank(board)
    info["fp"] = m.footprint_xy(board)
    info["counts"] = m.track_counts(board)
    info["protect_before"] = protect_ok(board)
    print("ISLAND", info["gap"]["same_island"], "pad-edge", info["gap"]["pad_edge_exact_mm"], flush=True)
    print("FLANK", info["flank"]["candidates"], flush=True)
    print("CHORD", info["chord"]["vdd1"], flush=True)
    print("FAR vias", info["gap"]["far_through_vias"], "bcu_only", info["gap"]["bcu_only"], flush=True)

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BE_BEFORE.json"))
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    def finish(decision, reason, after_stats):
        info["gained"] = info.get("gained", {})
        skirt = info.get("skirt") or {"crossed": False, "crossing_count": 0, "segments": [], "method": ""}
        meas = info.get("meas") or {"segments": []}
        write_outputs(decision, info, bst, after_stats, reason, meas, skirt)
        print("DECISION", decision, flush=True)
        print(reason, flush=True)

    if bst["unconnected_items"] != 55:
        shutil.copy2(REPORTS / "DRC_PASS30BE_BEFORE.json", REPORTS / "DRC_PASS30BE_AFTER.json")
        info["skirt"] = {"crossed": False, "crossing_count": 0, "segments": [], "method": "not run"}
        info["meas"] = {"segments": []}
        finish(
            "NO-ROUTE",
            f"NO-ROUTE. Unconnected started at {bst['unconnected_items']}, not 55. No copper added.",
            bst,
        )
        return

    meas = measure(board)
    skirt = whole_segment_crossing_test(poly_xy())
    info["meas"] = meas
    info["skirt"] = skirt
    print(
        "MEAS ok", meas["ok"], "foreign", meas["min_clearance_mm"],
        "power", meas["min_power_vin_mm"], "cross", skirt["crossed"],
        "via", meas["new_via"], flush=True,
    )

    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BE_BEFORE.json", REPORTS / "DRC_PASS30BE_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BE_BEFORE.json", REPORTS / "DRC_PASS30BE_AFTER.json")
        finish("NO-ROUTE", "NO-ROUTE. U1.43 and the far B.Cu segment are already one island. No copper added.", bst)
        return
    if skirt["crossed"] or not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BE_BEFORE.json", REPORTS / "DRC_PASS30BE_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. No legal path. "
            f"measure_ok={meas['ok']} foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']} "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']} "
            f"hole {meas['min_hole_mm']} via {meas['new_via']} crossings {skirt['crossing_count']}. "
            "Skirt slot, SIM_CLK centerline, and the sealed pocket were not used. No copper added.",
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
    skirt_after = whole_segment_crossing_test(poly_xy())
    if moved or ripped or not all(pa.values()) or skirt_after["crossed"]:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BE_AFTER.json"))
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        finish(
            "NO-ROUTE",
            f"Protect or crossing guard failed after add, before save. moved={moved} ripped={ripped} "
            f"protect={pa} crossed={skirt_after['crossed']}. Full restore. "
            f"Blob matches pre-edit: {info['reverted_blob_match']}.",
            after["stats"],
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = enrich(m.run_drc(REPORTS / "DRC_PASS30BE_MID.json"))
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["sim_rst_unconnected"] - mst["sim_rst_unconnected"]
    board2 = pcbnew.LoadBoard(str(BOARD))
    skirts_intact = protect_ok(board2)
    skirt_on_disk = whole_segment_crossing_test(poly_xy())
    info["skirt"] = skirt_on_disk
    # Class-E: do not fail solely because GND unconnected items rise.
    nongnd_before = sum(v for k, v in bst["nongnd"].items())
    nongnd_after = sum(v for k, v in mst["nongnd"].items())
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
        and nongnd_after <= nongnd_before - 1
    )
    if not gate_ok:
        restore()
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BE_AFTER.json"))
        ast = after["stats"]
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"SIM_RST opens {bst['sim_rst_unconnected']}→{mst['sim_rst_unconnected']} (need drop ≥ 1). "
            f"Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
            f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']}. "
            f"Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
            f"Locked intact: {all(skirts_intact.values())}. "
            f"Post-revert unconnected {ast['unconnected_items']}. "
            f"Blob matches pre-edit: {info['reverted_blob_match']}. No second path."
        )
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30BE_MID.json", REPORTS / "DRC_PASS30BE_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. F.Cu neck plus In1 west/north bypass, {len(POLY) - 1} new segments, "
        f"one 0.50/0.30 through-via at (32.75, 25.50), landing on existing through-via (78.00, 36.00). "
        f"x=32.71 through-run was not used (P0.25 clearance exactly 0.150 mm, but it crosses SIM_CLK). "
        f"Skirt slot and sealed pocket not used. Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
        f"SIM_RST opens {bst['sim_rst_unconnected']}→{mst['sim_rst_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Four skirts and the SIM_CLK run not ripped or stacked. No other net."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
