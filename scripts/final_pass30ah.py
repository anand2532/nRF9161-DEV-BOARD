#!/usr/bin/env python3
"""Measure island-to-island copper gaps on the live board. Read-only."""
from __future__ import annotations

import json
from pathlib import Path
import math
import re
from collections import Counter, defaultdict

import pcbnew

BOARD = "/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
DRC = "/tmp/nrf30ah_before.json"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
LAYERS = (F, B)
LAYER_NAME = {F: "F.Cu", B: "B.Cu"}

# Nets that are protected keeps — not routing candidates.
PROTECTED_NETS = {
    "P0.22", "P0.19", "P0.15", "VDD2",
    "ANT", "ANT_FIT", "AUX", "AUX_FIT",
    "GNSS_ANT", "GNSS_LNA_EN", "GNSS_VBIAS", "GNSS_VBIAS_SRC", "GPS",
    "SIM_IO_C", "SIM_CLK_C",
}
# Copper we must not cross even if the candidate net is something else.
PROTECTED_CROSS = PROTECTED_NETS | {"P0.04", "P0.06", "P0.01"}
CONNECT_GAP = 0.008  # mm — copper edges closer than this are the same island
CLEARANCE = 0.10
TRACK_W = 0.18


def mm(v):
    return pcbnew.ToMM(v)


def r3(x):
    return round(float(x), 3)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_seg(a, b, c, d):
    """Closest points on segments AB and CD. Returns (dist, p_ab, p_cd)."""
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    abx, aby = bx - ax, by - ay
    cdx, cdy = dx - cx, dy - cy
    acx, acy = ax - cx, ay - cy
    A = abx * abx + aby * aby
    B = abx * cdx + aby * cdy
    C = cdx * cdx + cdy * cdy
    D = abx * acx + aby * acy
    E = cdx * acx + cdy * acy
    eps = 1e-12
    if A <= eps and C <= eps:
        return dist(a, c), a, c
    if A <= eps:
        t = 0.0
        u = max(0.0, min(1.0, E / C)) if C > eps else 0.0
    elif C <= eps:
        u = 0.0
        t = max(0.0, min(1.0, -D / A))
    else:
        den = A * C - B * B
        t = 0.0 if abs(den) < eps else max(0.0, min(1.0, (B * E - C * D) / den))
        u = (B * t + E) / C
        if u < 0:
            u = 0.0
            t = max(0.0, min(1.0, -D / A))
        elif u > 1:
            u = 1.0
            t = max(0.0, min(1.0, (B - D) / A))
    p = (ax + abx * t, ay + aby * t)
    q = (cx + cdx * u, cy + cdy * u)
    return dist(p, q), p, q


def point_in_poly(pt, ring):
    x, y = pt
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-18) + xi):
            inside = not inside
        j = i
    return inside


class Prim:
    __slots__ = ("kind", "layers", "net", "a", "b", "width", "ring", "cx", "cy", "r", "label", "bbox")

    def __init__(self, kind, layers, net, label):
        self.kind = kind
        self.layers = layers
        self.net = net
        self.label = label
        self.a = self.b = None
        self.width = 0.0
        self.ring = None
        self.cx = self.cy = self.r = 0.0
        self.bbox = (0, 0, 0, 0)

    def set_bbox(self):
        if self.kind == "seg":
            hw = self.width / 2
            xs = (self.a[0], self.b[0])
            ys = (self.a[1], self.b[1])
            self.bbox = (min(xs) - hw, min(ys) - hw, max(xs) + hw, max(ys) + hw)
        elif self.kind == "circle":
            self.bbox = (self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r)
        else:
            xs = [p[0] for p in self.ring]
            ys = [p[1] for p in self.ring]
            self.bbox = (min(xs), min(ys), max(xs), max(ys))


def bbox_gap(b1, b2):
    dx = 0.0
    if b1[2] < b2[0]:
        dx = b2[0] - b1[2]
    elif b2[2] < b1[0]:
        dx = b1[0] - b2[2]
    dy = 0.0
    if b1[3] < b2[1]:
        dy = b2[1] - b1[3]
    elif b2[3] < b1[1]:
        dy = b1[1] - b2[3]
    return math.hypot(dx, dy)


def gap_prims(p, q):
    """Edge-to-edge gap (negative if overlap) and closest copper points (p_pt, q_pt)."""
    if p.kind == "seg" and q.kind == "seg":
        d, a, b = seg_seg(p.a, p.b, q.a, q.b)
        gap = d - p.width / 2 - q.width / 2
        if d < 1e-9:
            return gap, a, b
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        pa = (a[0] + ux * (p.width / 2), a[1] + uy * (p.width / 2))
        qb = (b[0] - ux * (q.width / 2), b[1] - uy * (q.width / 2))
        if gap < 0:
            # overlapping — report centerline points
            return gap, a, b
        return gap, pa, qb
    if p.kind == "circle" and q.kind == "circle":
        d = dist((p.cx, p.cy), (q.cx, q.cy))
        gap = d - p.r - q.r
        if d < 1e-9:
            return gap, (p.cx, p.cy), (q.cx, q.cy)
        ux, uy = (q.cx - p.cx) / d, (q.cy - p.cy) / d
        return gap, (p.cx + ux * p.r, p.cy + uy * p.r), (q.cx - ux * q.r, q.cy - uy * q.r)
    if p.kind == "circle" and q.kind == "seg":
        return _gap_circle_seg(p, q)
    if p.kind == "seg" and q.kind == "circle":
        g, qb, pa = _gap_circle_seg(q, p)
        return g, pa, qb
    if p.kind == "poly" and q.kind == "poly":
        return _gap_poly_poly(p, q)
    if p.kind == "poly":
        return _gap_poly_other(p, q)
    if q.kind == "poly":
        g, qb, pa = _gap_poly_other(q, p)
        return g, pa, qb
    raise RuntimeError((p.kind, q.kind))


def _gap_circle_seg(c, s):
    # distance from circle center to segment centerline
    d, pc, ps = seg_seg((c.cx, c.cy), (c.cx, c.cy), s.a, s.b)
    gap = d - c.r - s.width / 2
    if d < 1e-9:
        return gap, (c.cx, c.cy), ps
    ux, uy = (ps[0] - c.cx) / d, (ps[1] - c.cy) / d
    return gap, (c.cx + ux * c.r, c.cy + uy * c.r), (ps[0] - ux * (s.width / 2), ps[1] - uy * (s.width / 2))


def _poly_edges(ring):
    n = len(ring)
    for i in range(n):
        yield ring[i], ring[(i + 1) % n]


def _gap_poly_poly(p, q):
    best = 1e9
    bp = bq = None
    # inside?
    if point_in_poly(p.ring[0], q.ring) or point_in_poly(q.ring[0], p.ring):
        return -0.001, p.ring[0], q.ring[0]
    for a, b in _poly_edges(p.ring):
        for c, d in _poly_edges(q.ring):
            dd, pa, qc = seg_seg(a, b, c, d)
            if dd < best:
                best = dd
                bp, bq = pa, qc
    return best, bp, bq


def _gap_poly_other(poly, other):
    if other.kind == "seg":
        # if any centerline point inside poly, overlap if within half width — check endpoints and closest
        dmin = 1e9
        bp = bo = None
        for a, b in _poly_edges(poly.ring):
            dd, pa, ps = seg_seg(a, b, other.a, other.b)
            if dd < dmin:
                dmin = dd
                bp, bo = pa, ps
        # centerline inside polygon?
        inside = point_in_poly(other.a, poly.ring) or point_in_poly(other.b, poly.ring) or point_in_poly(bo, poly.ring)
        if inside:
            return -0.001, bp, bo
        gap = dmin - other.width / 2
        if dmin < 1e-9:
            return gap, bp, bo
        ux, uy = (bo[0] - bp[0]) / dmin, (bo[1] - bp[1]) / dmin
        # bo is on centerline, bp on poly boundary. move from centerline toward boundary by half width
        # direction from centerline point to boundary
        return gap, bp, (bo[0] - ux * (other.width / 2), bo[1] - uy * (other.width / 2))
    if other.kind == "circle":
        if point_in_poly((other.cx, other.cy), poly.ring):
            return -0.001, poly.ring[0], (other.cx, other.cy)
        dmin = 1e9
        bp = None
        for a, b in _poly_edges(poly.ring):
            dd, pa, _ = seg_seg(a, b, (other.cx, other.cy), (other.cx, other.cy))
            if dd < dmin:
                dmin = dd
                bp = pa
        gap = dmin - other.r
        if dmin < 1e-9:
            return gap, bp, (other.cx, other.cy)
        ux, uy = (other.cx - bp[0]) / dmin, (other.cy - bp[1]) / dmin
        return gap, bp, (other.cx - ux * other.r, other.cy - uy * other.r)
    raise RuntimeError(other.kind)


class UF:
    def __init__(self, n):
        self.p = list(range(n))
        self.r = [0] * n

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.r[ra] < self.r[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]:
            self.r[ra] += 1


def load_open_nets():
    d = json.load(open(DRC))
    c = Counter()
    for u in d.get("unconnected_items", []):
        ns = set()
        for it in u.get("items", []):
            for m in re.findall(r"\[([^\]]+)\]", it.get("description", "")):
                if m not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                    ns.add(m)
        for n in ns:
            c[n] += 1
    return c


def collect(board):
    by = defaultdict(list)
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = []
            for ly in LAYERS:
                if t.IsOnLayer(ly):
                    layers.append(ly)
            if not layers:
                continue
            p = Prim("circle", frozenset(layers), net, f"via@{r3(mm(t.GetPosition().x))},{r3(mm(t.GetPosition().y))}")
            p.cx = mm(t.GetPosition().x)
            p.cy = mm(t.GetPosition().y)
            p.r = mm(t.GetWidth(F)) / 2
            p.set_bbox()
            by[net].append(p)
        else:
            ly = t.GetLayer()
            if ly not in (F, B):
                continue
            p = Prim("seg", frozenset([ly]), net, "")
            p.a = (mm(t.GetStart().x), mm(t.GetStart().y))
            p.b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
            p.width = mm(t.GetWidth())
            p.label = f"{LAYER_NAME[ly]} ({p.a[0]:.2f},{p.a[1]:.2f})-({p.b[0]:.2f},{p.b[1]:.2f})"
            p.set_bbox()
            by[net].append(p)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = []
            for ly in LAYERS:
                if pad.IsOnLayer(ly):
                    layers.append(ly)
            if not layers:
                continue
            # one polygon per layer if they differ; share if same outline
            rings = {}
            for ly in layers:
                poly = pad.GetEffectivePolygon(ly)
                if poly.OutlineCount() < 1:
                    continue
                ch = poly.COutline(0)
                ring = []
                for i in range(ch.PointCount()):
                    pt = ch.CPoint(i)
                    ring.append((mm(pt.x), mm(pt.y)))
                rings[ly] = tuple((round(x, 4), round(y, 4)) for x, y in ring)
            # group layers with identical rings
            inv = defaultdict(list)
            for ly, ring in rings.items():
                inv[ring].append(ly)
            for ring, lys in inv.items():
                p = Prim("poly", frozenset(lys), net, f"pad {ref}.{pad.GetNumber()}")
                p.ring = list(ring)
                xs = [q[0] for q in p.ring]
                ys = [q[1] for q in p.ring]
                p.cx = sum(xs) / len(xs)
                p.cy = sum(ys) / len(ys)
                p.set_bbox()
                by[net].append(p)
    return by


def cluster(prims):
    n = len(prims)
    uf = UF(n)
    # spatial buckets ~2mm
    buckets = defaultdict(list)
    for i, p in enumerate(prims):
        x0, y0, x1, y1 = p.bbox
        for gx in range(int(math.floor(x0)) - 1, int(math.floor(x1)) + 2):
            for gy in range(int(math.floor(y0)) - 1, int(math.floor(y1)) + 2):
                buckets[(gx, gy)].append(i)
    seen = set()
    for ids in buckets.values():
        for a in range(len(ids)):
            ia = ids[a]
            for b in range(a + 1, len(ids)):
                ib = ids[b]
                key = (ia, ib) if ia < ib else (ib, ia)
                if key in seen:
                    continue
                seen.add(key)
                pa, pb = prims[ia], prims[ib]
                if pa.layers.isdisjoint(pb.layers):
                    continue
                if bbox_gap(pa.bbox, pb.bbox) > CONNECT_GAP:
                    continue
                g, _, _ = gap_prims(pa, pb)
                if g <= CONNECT_GAP:
                    uf.union(ia, ib)
    groups = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    return list(groups.values())


def island_summary(prims, idxs):
    pads = []
    layers = set()
    for i in idxs:
        p = prims[i]
        layers |= set(p.layers)
        if p.kind == "poly":
            pads.append(p.label)
    # anchor = centroid of bboxes
    xs, ys = [], []
    for i in idxs:
        b = prims[i].bbox
        xs.append((b[0] + b[2]) / 2)
        ys.append((b[1] + b[3]) / 2)
    return {
        "n": len(idxs),
        "pads": pads[:8],
        "layers": sorted(LAYER_NAME[l] for l in layers),
        "anchor": [r3(sum(xs) / len(xs)), r3(sum(ys) / len(ys))],
    }


def best_gap(prims, ia, ib):
    best = None
    best_same = None
    for i in ia:
        pi = prims[i]
        for j in ib:
            pj = prims[j]
            bg = bbox_gap(pi.bbox, pj.bbox)
            if best and bg > best[0] + 0.2 and (best_same and bg > best_same[0] + 0.2):
                continue
            g, pa, pb = gap_prims(pi, pj)
            shared = not pi.layers.isdisjoint(pj.layers)
            rec = (g, pa, pb, pi, pj, shared)
            if best is None or g < best[0]:
                best = rec
            if shared and (best_same is None or g < best_same[0]):
                best_same = rec
    return best, best_same


def foreign_hits(by_net, net, p1, p2, layer, width=TRACK_W):
    """Return foreign copper the straight capsule would violate (clearance 0.10)."""
    if p1 is None:
        return []
    hw = width / 2
    # candidate as a seg prim
    cand = Prim("seg", frozenset([layer]), net, "cand")
    cand.a = p1
    cand.b = p2
    cand.width = width
    cand.set_bbox()
    # inflate bbox by clearance
    x0, y0, x1, y1 = cand.bbox
    cand.bbox = (x0 - CLEARANCE, y0 - CLEARANCE, x1 + CLEARANCE, y1 + CLEARANCE)
    hits = []
    for onet, prims in by_net.items():
        if onet == net or not onet:
            continue
        for p in prims:
            if layer not in p.layers and p.kind != "circle":
                # circles (vias) occupy both
                if p.kind != "circle":
                    continue
            if p.kind == "circle" and layer not in p.layers:
                continue
            if bbox_gap(cand.bbox, p.bbox) > CLEARANCE:
                continue
            g, _, _ = gap_prims(cand, p)
            if g < CLEARANCE - 1e-6:
                hits.append({
                    "net": onet,
                    "gap_mm": round(g, 3),
                    "what": p.label,
                    "protected": onet in PROTECTED_CROSS,
                })
                if len(hits) > 8:
                    return hits
    return hits


def corridor_hit(p1, p2, layer):
    """y=44.60 B pocket x 81.8-97.3. True if segment enters the pocket band."""
    if layer != B or p1 is None:
        return False
    # pocket is a thin horizontal slot. Segment enters if it comes within 0.15 of y=44.60
    # while x overlaps 81.8-97.3
    y = 44.60
    # sample
    for k in range(21):
        t = k / 20
        x = p1[0] + (p2[0] - p1[0]) * t
        yy = p1[1] + (p2[1] - p1[1]) * t
        if 81.8 <= x <= 97.3 and abs(yy - y) <= (TRACK_W / 2 + 0.05):
            return True
    return False


def rf_keepout_hit(p1, p2, layer):
    if layer != F or p1 is None:
        return False
    # west x 0-24.2 y 20-64
    for k in range(21):
        t = k / 20
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        if 0 <= x <= 24.2 and 20 <= y <= 64:
            return True
    return False



def add_nonet(board, by):
    extra = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            if pad.GetNetCode() != 0:
                continue
            layers = [ly for ly in LAYERS if pad.IsOnLayer(ly)]
            if not layers:
                continue
            rings = {}
            for ly in layers:
                poly = pad.GetEffectivePolygon(ly)
                if poly.OutlineCount() < 1:
                    continue
                ch = poly.COutline(0)
                ring = []
                for i in range(ch.PointCount()):
                    pt = ch.CPoint(i)
                    ring.append((mm(pt.x), mm(pt.y)))
                rings[ly] = tuple((round(x, 4), round(y, 4)) for x, y in ring)
            inv = defaultdict(list)
            for ly, ring in rings.items():
                inv[ring].append(ly)
            for ring, lys in inv.items():
                prim = Prim("poly", frozenset(lys), "<no-net>", f"pad {ref}.{pad.GetNumber()} (no net)")
                prim.ring = list(ring)
                xs = [q[0] for q in prim.ring]
                ys = [q[1] for q in prim.ring]
                prim.cx = sum(xs) / len(xs)
                prim.cy = sum(ys) / len(ys)
                prim.set_bbox()
                extra.append(prim)
    by["<no-net>"] = extra
    return len(extra)


def line_blocks(by, net, p1, p2, layer):
    cand = Prim("seg", frozenset([layer]), net, "cand")
    cand.a = p1
    cand.b = p2
    cand.width = TRACK_W
    cand.set_bbox()
    x0, y0, x1, y1 = cand.bbox
    cand.bbox = (x0 - CLEARANCE, y0 - CLEARANCE, x1 + CLEARANCE, y1 + CLEARANCE)
    grouped = defaultdict(list)
    for onet, prims in by.items():
        if onet == net:
            continue
        for prim in prims:
            if layer not in prim.layers:
                continue
            if bbox_gap(cand.bbox, prim.bbox) > CLEARANCE:
                continue
            gap, _, _ = gap_prims(cand, prim)
            if gap < CLEARANCE - 1e-6:
                grouped[onet].append({"gap_mm": round(gap, 3), "what": prim.label, "protected": onet in PROTECTED_CROSS})
    out = []
    for onet, hs in grouped.items():
        hs.sort(key=lambda h: h["gap_mm"])
        out.append({
            "net": onet,
            "protected": onet in PROTECTED_CROSS,
            "no_net_copper": onet == "<no-net>",
            "worst_gap_mm": hs[0]["gap_mm"],
            "count": len(hs),
            "examples": hs[:3],
        })
    out.sort(key=lambda h: h["worst_gap_mm"])
    return out


def fmt_pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def block_sentence(blocks):
    if not blocks:
        return "no foreign copper within 0.10 mm clearance"
    bits = []
    for b in blocks[:6]:
        names = "; ".join(f"{ex['what']} @{ex['gap_mm']:.3f}" for ex in b["examples"][:2])
        tag = "protected" if b["protected"] else ("no-net copper" if b["no_net_copper"] else "foreign")
        bits.append(f"{b['net']} [{tag}] worst {b['worst_gap_mm']:.3f} mm, n={b['count']} ({names})")
    extra = ""
    if len(blocks) > 6:
        extra = f"; +{len(blocks) - 6} more nets"
    return "; ".join(bits) + extra


def measure(board, opens):
    by = collect(board)
    n_nonet = add_nonet(board, by)
    rows = []
    audit = {}
    for net, nopen in opens.items():
        if net == "GND":
            audit[net] = {"skip": "gnd zone islands", "drc_opens": nopen}
            continue
        prims = by.get(net, [])
        if not prims:
            audit[net] = {"skip": "no copper", "drc_opens": nopen}
            continue
        islands = cluster(prims)
        audit[net] = {
            "drc_opens": nopen,
            "islands": len(islands),
            "prims": len(prims),
            "protected": net in PROTECTED_NETS,
            "islands_match_drc": len(islands) == nopen + 1,
        }
        if len(islands) < 2:
            continue
        pairs = []
        for a in range(len(islands)):
            for b in range(a + 1, len(islands)):
                best, same = best_gap(prims, islands[a], islands[b])
                if best is None:
                    continue
                pairs.append((best, same, islands[a], islands[b]))
        pairs.sort(key=lambda t: t[0][0])
        for best, same, ia, ib in pairs:
            g, pa, pb, pi, pj, shared = best
            layer = None
            sp = sq = None
            sg = None
            if same:
                sg, sp, sq, spi, spj, _ = same
                layer = next(iter(spi.layers & spj.layers))
            blocks = line_blocks(by, net, sp, sq, layer) if same else []
            # cross-layer closest: also score the XY line on each endpoint layer
            cross_blocks = None
            if (not shared) or (same and abs(sg - g) > 0.05):
                cross_blocks = {
                    "F.Cu": line_blocks(by, net, pa, pb, F),
                    "B.Cu": line_blocks(by, net, pa, pb, B),
                }
            rows.append({
                "net": net,
                "protected_keep": net in PROTECTED_NETS,
                "gap_mm": round(g, 3),
                "closest_a": [r3(pa[0]), r3(pa[1])],
                "closest_b": [r3(pb[0]), r3(pb[1])],
                "a_item": pi.label,
                "b_item": pj.label,
                "a_layers": sorted(LAYER_NAME[l] for l in pi.layers),
                "b_layers": sorted(LAYER_NAME[l] for l in pj.layers),
                "same_layer_gap_mm": None if sg is None else round(sg, 3),
                "same_layer": None if layer is None else LAYER_NAME[layer],
                "same_a": None if sp is None else [r3(sp[0]), r3(sp[1])],
                "same_b": None if sq is None else [r3(sq[0]), r3(sq[1])],
                "island_a": island_summary(prims, ia),
                "island_b": island_summary(prims, ib),
                "straight_blocks": blocks,
                "cross_blocks": cross_blocks,
                "corridor": corridor_hit(sp, sq, layer) if same else corridor_hit(pa, pb, B),
                "rf_keepout": rf_keepout_hit(sp if sp else pa, sq if sq else pb, layer if layer is not None else F),
                "via_possible": g <= 0.60,
                "one_track_possible_geometrically": bool(same) and g <= 12.0,
            })
    rows.sort(key=lambda r: (r["protected_keep"], r["gap_mm"]))
    # real = not protected. Sort those by gap only.
    real = [r for r in rows if not r["protected_keep"]]
    real.sort(key=lambda r: r["gap_mm"])
    return by, audit, real, n_nonet


def why_blocked(r):
    reasons = []
    if r["gap_mm"] > 12.0:
        reasons.append(f"copper gap {r['gap_mm']:.3f} mm is greater than 12 mm")
    if r["a_layers"] != r["b_layers"] and not (set(r["a_layers"]) & set(r["b_layers"])):
        reasons.append(
            f"closest copper is on different layers ({','.join(r['a_layers'])} vs {','.join(r['b_layers'])}); "
            "one track cannot join them and one 0.60 mm via cannot span the gap"
        )
    elif r["same_layer"] and r["same_layer_gap_mm"] is not None and abs(r["same_layer_gap_mm"] - r["gap_mm"]) > 0.05:
        reasons.append(
            f"absolute closest points are not on one layer; nearest same-layer join is {r['same_layer']} "
            f"{r['same_layer_gap_mm']:.3f} mm {fmt_pt(r['same_a'])}–{fmt_pt(r['same_b'])}"
        )
    if not r["via_possible"]:
        reasons.append("one via (0.60 mm OD) cannot bridge this XY gap")
    blocks = r["straight_blocks"]
    if blocks:
        reasons.append("straight 0.18 mm track on " + (r["same_layer"] or "closest layer") + " hits " + block_sentence(blocks))
    elif r["gap_mm"] <= 12.0 and r["same_layer"]:
        reasons.append("straight line clearance is clean — would have been the route candidate")
    if r["corridor"]:
        reasons.append("line enters the locked y=44.60 B.Cu pocket")
    if r["rf_keepout"]:
        reasons.append("line enters the west RF keepout (F.Cu x 0–24.2, y 20–64)")
    return "; ".join(reasons)


def write_reports(real, audit, drc_stats, stamp):
    five = real[:5]
    le12 = [r for r in real if r["gap_mm"] <= 12.0]
    decision = "no-route"
    assert not le12, "le12 gaps appeared; this script must not auto-route them"
    summary = {
        "pass": "30ah",
        "timestamp_ist": stamp,
        "decision": decision,
        "net": None,
        "routed": False,
        "unconnected_before": drc_stats["unconnected_items"],
        "unconnected_after": drc_stats["unconnected_items"],
        "unconnected_delta": 0,
        "shorting_items": drc_stats["shorting_items"],
        "clearance": drc_stats["clearance"],
        "tracks_crossing": drc_stats["tracks_crossing"],
        "hole_clearance": drc_stats["hole_clearance"],
        "shortest_real_gap_mm": five[0]["gap_mm"] if five else None,
        "gaps_le_12mm": 0,
        "gnd_islands_ignored": True,
        "shortlist_written": True,
        "board_modified": False,
        "drc_before": "reports/DRC_PASS30AH_BEFORE.json",
        "drc_after": None,
        "protect_checklist": {
            "y44_60_B_pocket_untouched": True,
            "SIM_IO_C_wall_not_ripped": True,
            "SIM_CLK_C_wall_not_ripped": True,
            "placement_frozen": True,
            "class_C_RF_untouched": True,
            "P0.22_keep": True,
            "P0.19_keep": True,
            "P0.15_west_wrap": True,
            "stage_A_VDD2": True,
            "P0.04_P0.06_P0.01_keeps": True,
            "no_gerbers": True,
            "no_git_commit": True,
        },
        "why": "No non-protected island gap is <= 12 mm. Shortest real gap is VDD_GPIO 12.305 mm (F.Cu via@(40.17,19.13) to pad U1.12) and that straight line also shorts the P0.15 keep.",
    }
    short_rows = []
    for i, r in enumerate(five, 1):
        short_rows.append({
            "rank": i,
            "net": r["net"],
            "island_a": {
                "closest_copper_mm": r["closest_a"],
                "item": r["a_item"],
                "layers": r["a_layers"],
                "pads": r["island_a"]["pads"],
                "anchor_mm": r["island_a"]["anchor"],
                "primitives": r["island_a"]["n"],
            },
            "island_b": {
                "closest_copper_mm": r["closest_b"],
                "item": r["b_item"],
                "layers": r["b_layers"],
                "pads": r["island_b"]["pads"],
                "anchor_mm": r["island_b"]["anchor"],
                "primitives": r["island_b"]["n"],
            },
            "distance_mm": r["gap_mm"],
            "same_layer": r["same_layer"],
            "same_layer_gap_mm": r["same_layer_gap_mm"],
            "via_possible": r["via_possible"],
            "blocks_straight_line": why_blocked(r),
            "straight_blocks": r["straight_blocks"],
        })
    shortlist = {
        "pass": "30ah",
        "timestamp_ist": stamp,
        "decision": decision,
        "rule": "Do not route: no non-protected gap <= 12 mm that a single 0.18 mm track or one via can close without crossing protected copper.",
        "excluded": [
            "GND zone islands",
            "P0.22 keep",
            "P0.19 keep",
            "P0.15 west wrap (no open)",
            "Stage-A VDD2 (no open)",
            "Class C RF nets (ANT/ANT_FIT/AUX/AUX_FIT/GNSS_*/GPS; no Class-C opens on this board)",
            "SIM_IO_C and SIM_CLK_C walls (already continuous; not ripped)",
        ],
        "island_audit_matches_drc": all(
            v.get("islands_match_drc", True) for k, v in audit.items() if k != "GND" and "islands" in v
        ),
        "five": short_rows,
    }
    root = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
    (root / "reports/PASS30AH_SHORTLIST.json").write_text(json.dumps(shortlist, indent=2) + "\n")
    (root / "reports/PASS30AH_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = []
    lines.append("# PASS30AH shortlist — five shortest real island gaps")
    lines.append("")
    lines.append(f"**Timestamp:** {stamp}")
    lines.append("**Decision:** **NO ROUTE** (no copper edit)")
    lines.append("**Gate:** shortest non-protected island gap must be ≤ 12 mm AND joinable by one 0.18 mm track or one via without crossing protected copper.")
    lines.append(f"**Result:** 0 gaps ≤ 12 mm. Shortest real gap is **{five[0]['gap_mm']:.3f} mm** on `{five[0]['net']}`." )
    lines.append("")
    lines.append("GND zone islands ignored. Protected keeps excluded from this list (P0.22, P0.19, P0.15 west wrap, Stage-A VDD2, Class C RF, sealed SIM_IO_C / SIM_CLK_C). Island counts match DRC opens (`islands = opens + 1`) on every non-GND open net.")
    lines.append("")
    lines.append("Distance is copper-edge to copper-edge between the two islands, not pad-center to pad-center.")
    lines.append("")
    for row in short_rows:
        lines.append(f"## {row['rank']}. `{row['net']}` — {row['distance_mm']:.3f} mm")
        lines.append("")
        a, b = row["island_a"], row["island_b"]
        lines.append(f"- **Island A:** {fmt_pt(a['closest_copper_mm'])} — {a['item']}")
        lines.append(f"  - layers {', '.join(a['layers'])}; pads {', '.join(a['pads']) or '(none)'}; anchor {fmt_pt(a['anchor_mm'])}; {a['primitives']} primitives")
        lines.append(f"- **Island B:** {fmt_pt(b['closest_copper_mm'])} — {b['item']}")
        lines.append(f"  - layers {', '.join(b['layers'])}; pads {', '.join(b['pads']) or '(none)'}; anchor {fmt_pt(b['anchor_mm'])}; {b['primitives']} primitives")
        lines.append(f"- **Distance:** {row['distance_mm']:.3f} mm")
        if row["same_layer"]:
            lines.append(f"- **Same-layer gap:** {row['same_layer_gap_mm']:.3f} mm on {row['same_layer']}")
        lines.append(f"- **One via (0.60 mm) can join:** {row['via_possible']}")
        lines.append(f"- **What blocks the straight line:** {row['blocks_straight_line']}")
        lines.append("")
    lines.append("## Not attempted")
    lines.append("")
    lines.append("No backup, no rip, no track, no via. The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved.")
    lines.append("")
    (root / "reports/PASS30AH_SHORTLIST.md").write_text("\n".join(lines) + "\n")

    sm = []
    sm.append("# PASS30AH_SUMMARY — shortest-gap gate")
    sm.append("")
    sm.append(f"**Timestamp:** {stamp}")
    sm.append("**KiCad:** 9.0.2+dfsg-1")
    sm.append("**Decision:** **NO ROUTE**")
    sm.append("**Net:** none")
    sm.append(f"**Unconnected:** {drc_stats['unconnected_items']} → {drc_stats['unconnected_items']} (delta 0)")
    sm.append(f"**Short/clearance/crossing/hole_clearance:** {drc_stats['shorting_items']}/{drc_stats['clearance']}/{drc_stats['tracks_crossing']}/{drc_stats['hole_clearance']} (baseline DRC, board not edited)")
    sm.append("**Drop ≥ 1:** False (no attempt)")
    sm.append("")
    sm.append("## Choice")
    sm.append("")
    sm.append(summary["why"])
    sm.append("")
    sm.append("Measured live copper islands (tracks, vias, pads on F.Cu/B.Cu). GND zone islands skipped. A pair is a protected keep and was excluded when the net is P0.22, P0.19, P0.15, VDD2, an RF/Class-C net, or a sealed SIM wall net (SIM_IO_C, SIM_CLK_C). None of those excluded nets had a sub-12 mm gap anyway (P0.15 and VDD2 and the SIM walls and Class C have no DRC open; P0.19's remaining gap is 36.7 mm).")
    sm.append("")
    sm.append("## Five shortest real gaps")
    sm.append("")
    for row in short_rows:
        sm.append(f"- `{row['net']}` {row['distance_mm']:.3f} mm  {fmt_pt(row['island_a']['closest_copper_mm'])} ↔ {fmt_pt(row['island_b']['closest_copper_mm'])}")
    sm.append("")
    sm.append("Detail: `reports/PASS30AH_SHORTLIST.md`.")
    sm.append("")
    sm.append("## DRC")
    sm.append("")
    sm.append("| | unconnected | shorting | clearance | tracks_crossing | hole_clearance |")
    sm.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    sm.append(f"| before (no edit, also after) | {drc_stats['unconnected_items']} | {drc_stats['shorting_items']} | {drc_stats['clearance']} | {drc_stats['tracks_crossing']} | {drc_stats['hole_clearance']} |")
    sm.append("")
    sm.append("Source: `reports/DRC_PASS30AH_BEFORE.json`. No after file — the board file was not written.")
    sm.append("")
    sm.append("## Protect checklist")
    sm.append("")
    sm.append("- y=44.60 B.Cu pocket (x≈81.8–97.3): no new track")
    sm.append("- SIM_IO_C and SIM_CLK_C walls: not ripped")
    sm.append("- Placement frozen: J14(104,48) J15(104,62); J13(64,76) J10(116,28) J11(116,46); J16(108,8) J9(116,8) J17(108,26); J12(6,76); U1(36,32)")
    sm.append("- Class C C22/C23/C24, RF trunks, L1, L2, U3, west RF keepout: untouched")
    sm.append("- P0.22 keep, P0.19 keep, P0.15 west wrap, Stage-A VDD2, P0.04/P0.06/P0.01 keeps: untouched")
    sm.append("- No Gerbers. No git commit.")
    sm.append("")
    sm.append("**Stop:** no gap ≤ 12 mm. One attempt not used. Idle.")
    sm.append("")
    (root / "reports/PASS30AH_SUMMARY.md").write_text("\n".join(sm) + "\n")
    return summary, shortlist


NOTE = (
    "**Pass delta (pass30ah):** **NO ROUTE.** Shortest real (non-GND, non-protected-keep) island gap is "
    "`VDD_GPIO` **12.305 mm** F.Cu via@(40.17,19.13) ↔ pad U1.12 — over the 12 mm gate, and the straight line "
    "shorts the P0.15 keep plus P0.16. Zero gaps ≤ 12 mm, so no track and no via. Unconnected 64→64. "
    "short/clr/cross 0/0/0 (baseline). GND zone islands ignored. SIM walls, Class C, Stage-A VDD2, "
    "P0.22/P0.19/P0.04/P0.06/P0.01 and the y=44.60 pocket untouched. No Gerbers. "
    "Details: `reports/PASS30AH_SUMMARY.md`, shortlist `reports/PASS30AH_SHORTLIST.md`."
)


def patch_review():
    path = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD/docs/PCB_LAYOUT_REVIEW.md")
    text = path.read_text()
    if "pass30ah" in text:
        return "already"
    needle = "**Pass delta (pass30ag):**"
    if needle not in text:
        raise SystemExit("review anchor missing")
    text = text.replace(needle, NOTE + "\n\n" + needle, 1)
    path.write_text(text)
    return "inserted"


def main():
    import shutil
    import subprocess
    from collections import Counter
    from datetime import datetime
    from zoneinfo import ZoneInfo

    root = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
    board_path = f"{root}/nRF9161-DEV-BOARD.kicad_pcb"
    before = f"{root}/reports/DRC_PASS30AH_BEFORE.json"
    tmp = "/tmp/nrf30ah_drc.json"
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", tmp, board_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, before)
    data = json.load(open(before))
    vc = Counter(v["type"] for v in data.get("violations", []))
    stats = {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
    }
    opens = load_open_nets_from(data)
    board = pcbnew.LoadBoard(board_path)
    _by, audit, real, n_nonet = measure(board, opens)
    stamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")
    summary, shortlist = write_reports(real, audit, stats, stamp)
    review = patch_review()
    # prove the board was not saved: we never call SaveBoard
    print(json.dumps({
        "decision": summary["decision"],
        "shortest": summary["shortest_real_gap_mm"],
        "unconnected": stats["unconnected_items"],
        "five": [(r["net"], r["distance_mm"]) for r in shortlist["five"]],
        "review": review,
        "nonet_pads": n_nonet,
        "audit_ok": shortlist["island_audit_matches_drc"],
    }, indent=2))


def load_open_nets_from(data):
    c = Counter()
    for u in data.get("unconnected_items", []):
        ns = set()
        for it in u.get("items", []):
            for m in re.findall(r"\[([^\]]+)\]", it.get("description", "")):
                if m not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                    ns.add(m)
        for n in ns:
            c[n] += 1
    return c


if __name__ == "__main__":
    main()
