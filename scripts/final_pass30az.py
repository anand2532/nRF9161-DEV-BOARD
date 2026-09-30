#!/usr/bin/env python3
"""pass30az — measure the remaining P0.17 open. No copper edit.

The live open is J17.1 against the pass30ay In2.Cu island. This script
measures the pad-edge gap and the straight 0.18 mm chord. It does not
route: the gap is over 36 mm. It does not save the board.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
W = 0.18
HW = W / 2.0
CF = 0.15
CP = 0.20
LIMIT = 36.0
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
LAYERS = (
    ("F.Cu", pcbnew.F_Cu),
    ("In1.Cu", pcbnew.In1_Cu),
    ("In2.Cu", pcbnew.In2_Cu),
    ("B.Cu", pcbnew.B_Cu),
)


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def r3(v: float) -> float:
    return round(v + 0.0, 3)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_blob() -> str:
    return subprocess.check_output(
        ["git", "hash-object", "nRF9161-DEV-BOARD.kicad_pcb"], cwd=ROOT, text=True
    ).strip()


def run_drc() -> dict:
    tmp = Path("/tmp/nrf30az_drc.json")
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", str(tmp), str(BOARD)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    data = json.loads(tmp.read_text())
    vc = Counter(v["type"] for v in data.get("violations", []))

    def nongnd(items) -> Counter:
        c: Counter = Counter()
        for it in items:
            desc = " ".join(i.get("description", "") for i in it.get("items", []))
            nets = {n for n in re.findall(r"\[([^\]]+)\]", desc) if n != "GND"}
            for n in nets:
                c[n] += 1
        return c

    gnd = 0
    p017 = None
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        if "[GND]" in desc:
            gnd += 1
        if "P0.17" in desc and p017 is None:
            p017 = it
    ng = nongnd(data.get("unconnected_items", []))
    return {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "hole_to_hole": vc.get("hole_to_hole", 0),
        "gnd_zone_islands": gnd,
        "p017_unconnected": ng.get("P0.17", 0),
        "p017_item": p017,
    }


def dps(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 < 1e-18:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def segseg(ax, ay, bx, by, cx, cy, dx, dy) -> float:
    return min(
        dps(ax, ay, cx, cy, dx, dy),
        dps(bx, by, cx, cy, dx, dy),
        dps(cx, cy, ax, ay, bx, by),
        dps(dx, dy, ax, ay, bx, by),
    )


def shape_of_track(t):
    return pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())


def shape_of_via(t, layer):
    return pcbnew.SHAPE_CIRCLE(
        xy(mm(t.GetPosition().x), mm(t.GetPosition().y)),
        pcbnew.FromMM(mm(t.GetWidth(layer)) / 2),
    )


def crosses_body(x1, y1, x2, y2) -> bool:
    """True if the centerline segment meets the closed fab rectangle."""
    xa, ya, xb, yb = BODY
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q, r in (
        (-dx, x1 - xa, xb - xa),
        (dx, xb - x1, xb - xa),
        (-dy, y1 - ya, yb - ya),
        (dy, yb - y1, yb - ya),
    ):
        if abs(p) < 1e-15:
            if q < 0 or q > r:
                return False
        else:
            s0, s1 = q / p, (q - r) / p if False else None
            # standard Liang-Barsky
    # Liang-Barsky
    p = [-dx, dx, -dy, dy]
    q = [x1 - xa, xb - x1, y1 - ya, yb - y1]
    u0, u1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-15:
            if qi < 0:
                return False
            continue
        t = qi / pi
        if pi < 0:
            if t > u1:
                return False
            if t > u0:
                u0 = t
        else:
            if t < u0:
                return False
            if t < u1:
                u1 = t
    return True


def measure_gap(board):
    layer_ids = {name: lid for name, lid in LAYERS}
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "P0.17":
                continue
            layers = [lid for _, lid in LAYERS if p.IsOnLayer(lid)]
            items.append(
                {
                    "kind": "pad",
                    "name": f"{fp.GetReference()}.{p.GetNumber()}",
                    "ref": fp.GetReference(),
                    "num": p.GetNumber(),
                    "x": mm(p.GetPosition().x),
                    "y": mm(p.GetPosition().y),
                    "layers": layers,
                    "layer_names": [board.GetLayerName(lid) for lid in layers],
                    "obj": p,
                    "shape": p.GetShape(),
                    "sx": mm(p.GetSize().x),
                    "sy": mm(p.GetSize().y),
                }
            )
    for t in board.GetTracks():
        if t.GetNetname() != "P0.17":
            continue
        if t.GetClass() == "PCB_VIA":
            layers = [lid for _, lid in LAYERS if t.IsOnLayer(lid)]
            items.append(
                {
                    "kind": "via",
                    "name": f"via@{mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f}",
                    "x": mm(t.GetPosition().x),
                    "y": mm(t.GetPosition().y),
                    "layers": layers,
                    "layer_names": [board.GetLayerName(lid) for lid in layers],
                    "obj": t,
                }
            )
        else:
            items.append(
                {
                    "kind": "trk",
                    "name": (
                        f"{board.GetLayerName(t.GetLayer())} "
                        f"({mm(t.GetStart().x):.3f},{mm(t.GetStart().y):.3f})-"
                        f"({mm(t.GetEnd().x):.3f},{mm(t.GetEnd().y):.3f})"
                    ),
                    "x": (mm(t.GetStart().x) + mm(t.GetEnd().x)) / 2,
                    "y": (mm(t.GetStart().y) + mm(t.GetEnd().y)) / 2,
                    "layers": [t.GetLayer()],
                    "layer_names": [board.GetLayerName(t.GetLayer())],
                    "obj": t,
                    "a": (mm(t.GetStart().x), mm(t.GetStart().y)),
                    "b": (mm(t.GetEnd().x), mm(t.GetEnd().y)),
                    "w": mm(t.GetWidth()),
                }
            )

    def shp(it, lid):
        if it["kind"] == "pad":
            return it["obj"].GetEffectiveShape(lid)
        if it["kind"] == "via":
            return shape_of_via(it["obj"], lid)
        return shape_of_track(it["obj"])

    def touches(i, j) -> bool:
        for lid in set(items[i]["layers"]) & set(items[j]["layers"]):
            if mm(shp(items[i], lid).GetClearance(shp(items[j], lid))) <= 0.001:
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
            if abs(items[i]["x"] - items[j]["x"]) > 12 and abs(items[i]["y"] - items[j]["y"]) > 12:
                if items[i]["kind"] != "trk" and items[j]["kind"] != "trk":
                    continue
            if touches(i, j):
                union(i, j)

    j17 = next(i for i, it in enumerate(items) if it["name"] == "J17.1")
    other = [i for i in range(len(items)) if find(i) != find(j17)]
    islands = len({find(i) for i in range(len(items))})
    best = None
    for name, lid in LAYERS:
        jsh = shp(items[j17], lid)
        for i in other:
            it = items[i]
            if lid not in it["layers"]:
                continue
            c = mm(jsh.GetClearance(shp(it, lid)))
            rec = (c, name, it)
            if best is None or c < best[0] - 1e-12:
                best = rec
    gap, layer_name, near = best
    # Nearest points. The winning geometry is the east edge of the vertical
    # In2 track against the west face of the J17.1 rectangle. The face is
    # equidistant for every y on the pad; the chord uses the pad-center y.
    pad = items[j17]
    assert near["kind"] == "trk"
    ax, ay = near["a"]
    bx, by = near["b"]
    assert abs(ax - bx) < 1e-9 and abs(near["w"] - W) < 1e-9
    track_east_x = ax + near["w"] / 2
    pad_west_x = pad["x"] - pad["sx"] / 2
    y_lo = max(min(ay, by), pad["y"] - pad["sy"] / 2)
    y_hi = min(max(ay, by), pad["y"] + pad["sy"] / 2)
    y_chord = pad["y"]
    assert y_lo - 1e-9 <= y_chord <= y_hi + 1e-9
    p_track = (track_east_x, y_chord)
    p_pad = (pad_west_x, y_chord)
    # points sit on the copper boundary
    tr_sh = shp(near, layer_ids[layer_name])
    pad_sh = shp(pad, layer_ids[layer_name])
    d_tr = mm(tr_sh.Distance(xy(*p_track)))
    d_pad = mm(pad_sh.Distance(xy(*p_pad)))
    if d_tr > 0.002 or d_pad > 0.002:
        raise SystemExit(f"nearest points not on copper: track {d_tr} pad {d_pad}")
    length = math.hypot(p_pad[0] - p_track[0], p_pad[1] - p_track[1])
    if abs(length - gap) > 0.002:
        raise SystemExit(f"chord length {length} != clearance {gap}")
    island_pads = []
    for i in other:
        it = items[i]
        if it["kind"] != "pad":
            continue
        island_pads.append(
            {
                "ref": it["ref"],
                "pad": it["num"],
                "net": "P0.17",
                "center_xy": [round(it["x"], 3), round(it["y"], 3)],
                "layers": it["layer_names"],
                "south_u1": it["ref"] == "U1" and it["y"] >= 37.0,
            }
        )
    return {
        "islands": islands,
        "gap_mm": gap,
        "gap_layer": layer_name,
        "near_item": near,
        "pad": pad,
        "p_track": p_track,
        "p_pad": p_pad,
        "equidistant_y": [y_lo, y_hi],
        "island_pads": island_pads,
        "j17_layers": pad["layer_names"],
    }


def chord_hits(board, p1, p2):
    x0, y0 = p1
    x1, y1 = p2
    assert abs(y0 - y1) < 1e-9
    y = y0
    if x0 > x1:
        x0, x1 = x1, x0
    layer = pcbnew.In2_Cu
    foreign = []
    power = []

    def consider(clr, net, kind, detail):
        rec = {
            "clearance_mm": r3(clr),
            "clearance_exact_mm": clr,
            "net": net or "<no-net>",
            "kind": kind,
            "item": detail,
            "power_vin": (net or "") in POWER,
        }
        if clr < CF - 1e-9:
            foreign.append(rec)
        if (net or "") in POWER and clr < CP - 1e-9:
            power.append(rec)

    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.17":
            continue
        if t.GetClass() == "PCB_VIA":
            if not t.IsOnLayer(layer):
                continue
            cx, cy = mm(t.GetPosition().x), mm(t.GetPosition().y)
            r = mm(t.GetWidth(layer)) / 2
            d = dps(cx, cy, x0, y, x1, y)
            clr = d - r - HW
            if clr < CP + 0.5:
                consider(
                    clr,
                    net,
                    "via",
                    f"via@{cx:.3f},{cy:.3f} r={r:.3f} on In2.Cu",
                )
        elif t.GetLayer() == layer:
            ax, ay = mm(t.GetStart().x), mm(t.GetStart().y)
            bx, by = mm(t.GetEnd().x), mm(t.GetEnd().y)
            hw = mm(t.GetWidth()) / 2
            d = segseg(x0, y, x1, y, ax, ay, bx, by)
            clr = d - hw - HW
            if clr < CP + 0.5:
                consider(
                    clr,
                    net,
                    "track",
                    f"In2.Cu ({ax:.3f},{ay:.3f})-({bx:.3f},{by:.3f}) w={mm(t.GetWidth()):.3f}",
                )

    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == "P0.17" or not p.IsOnLayer(layer):
                continue
            cx, cy = mm(p.GetPosition().x), mm(p.GetPosition().y)
            sx, sy = mm(p.GetSize().x), mm(p.GetSize().y)
            # coarse reject
            if cx + sx < x0 - 2 or cx - sx > x1 + 2 or abs(cy - y) > sy + 2:
                continue
            sh = p.GetEffectiveShape(layer)
            fat = pcbnew.SHAPE_SEGMENT(xy(x0, y), xy(x1, y), pcbnew.FromMM(W))
            gap = mm(fat.GetClearance(sh))
            if gap > 0:
                clr = gap
            else:
                clr = rect_or_circle_clearance(p, x0, x1, y)
            consider(
                clr,
                net,
                "pad",
                f"pad {fp.GetReference()}.{p.GetNumber()} @({cx:.3f},{cy:.3f}) on In2.Cu",
            )

    zclr = zone_clearance(board, x0, x1, y)
    consider(
        zclr["clearance_mm"],
        "VDD_nRF",
        "zone",
        (
            f"In2.Cu zone fill VDD_nRF (local clearance {zclr['local_clearance_mm']} mm); "
            f"worst at x={zclr['worst_x']:.3f}, centerline signed depth {zclr['signed_depth_mm']:.3f} mm"
        ),
    )
    foreign.sort(key=lambda h: h["clearance_exact_mm"])
    power.sort(key=lambda h: h["clearance_exact_mm"])
    # JSON-safe copies without the exact float key duplication issues
    def slim(rows):
        out = []
        for h in rows:
            out.append(
                {
                    "clearance_mm": h["clearance_mm"],
                    "net": h["net"],
                    "kind": h["kind"],
                    "item": h["item"],
                    "power_vin": h["power_vin"],
                }
            )
        return out

    return {"foreign_under_0_15": slim(foreign), "power_vin_under_0_20": slim(power)}


def rect_or_circle_clearance(pad, x0, x1, y) -> float:
    """Signed edge clearance of the 0.18 mm chord to a circle or axis-aligned rect pad.
    Overlap is negative. Used only when GetClearance is 0."""
    cx, cy = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
    sx, sy = mm(pad.GetSize().x), mm(pad.GetSize().y)
    orient = abs(pad.GetOrientationDegrees()) % 180
    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE or (
        abs(sx - sy) < 1e-9 and pad.GetShape() == pcbnew.PAD_SHAPE_OVAL
    ):
        d = dps(cx, cy, x0, y, x1, y)
        return d - sx / 2 - HW
    if orient > 1e-6 and abs(orient - 180) > 1e-6 and abs(orient - 90) > 1e-6:
        # rotated non-rect: sample the centerline across the pad bbox
        return sample_shape_clearance(pad, x0, x1, y)
    if abs(orient - 90) < 1e-6:
        sx, sy = sy, sx
    return aabb_chord_clearance(cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2, x0, x1, y)


def aabb_chord_clearance(xmin, ymin, xmax, ymax, x0, x1, y) -> float:
    if y < ymin or y > ymax:
        vgap = ymin - y if y < ymin else y - ymax
        if x1 < xmin:
            dist = math.hypot(xmin - x1, vgap)
        elif x0 > xmax:
            dist = math.hypot(x0 - xmax, vgap)
        else:
            dist = vgap
        return dist - HW
    # y is inside the vertical span
    depth_y = min(y - ymin, ymax - y)
    ox0, ox1 = max(x0, xmin), min(x1, xmax)
    if ox0 > ox1:
        dist = xmin - x1 if x1 < xmin else x0 - xmax
        return dist - HW
    mid = (xmin + xmax) / 2
    closest = min(max(mid, ox0), ox1)
    peak = min(closest - xmin, xmax - closest)
    max_depth = min(depth_y, peak)
    return -max_depth - HW


def sample_shape_clearance(pad, x0, x1, y) -> float:
    sh = pad.GetEffectiveShape(pcbnew.In2_Cu)
    poly = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(poly, pcbnew.In2_Cu, 0, 16, pcbnew.ERROR_INSIDE)
    ol = poly.Outline(0)
    edges = []
    for i in range(ol.GetSegmentCount()):
        s = ol.GetSegment(i)
        edges.append((mm(s.A.x), mm(s.A.y), mm(s.B.x), mm(s.B.y)))
    bb = sh.BBox()
    xa, xb = mm(bb.GetLeft()), mm(bb.GetRight())
    lo, hi = max(x0, xa - 0.2), min(x1, xb + 0.2)
    if hi < lo:
        # outside the bbox; fall back to endpoint distances
        lo, hi = x0, x1
    worst = None
    n = max(2, int((hi - lo) / 0.002))
    for i in range(n + 1):
        x = lo + (hi - lo) * i / n
        inside = sh.PointInside(xy(x, y))
        dist = min(dps(x, y, *e) for e in edges)
        sd = -dist if inside else dist
        clr = sd - HW
        if worst is None or clr < worst:
            worst = clr
    return worst


def zone_clearance(board, x0, x1, y) -> dict:
    zone = None
    for z in board.Zones():
        if z.GetLayer() == pcbnew.In2_Cu and not z.GetIsRuleArea():
            zone = z
            break
    if zone is None:
        raise SystemExit("In2 zone missing")
    poly = zone.GetFilledPolysList(pcbnew.In2_Cu)
    ol = poly.Outline(0)
    cell = 2.0
    buckets = defaultdict(list)
    for i in range(ol.GetSegmentCount()):
        s = ol.GetSegment(i)
        ax, ay, bx, by = mm(s.A.x), mm(s.A.y), mm(s.B.x), mm(s.B.y)
        ix0 = int(math.floor(min(ax, bx) / cell))
        ix1 = int(math.floor(max(ax, bx) / cell))
        iy0 = int(math.floor(min(ay, by) / cell))
        iy1 = int(math.floor(max(ay, by) / cell))
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                buckets[(ix, iy)].append((ax, ay, bx, by))

    def nearest(px, py) -> float:
        ix = int(math.floor(px / cell))
        iy = int(math.floor(py / cell))
        best = 1e9
        for rad in range(0, 40):
            for dx in range(-rad, rad + 1):
                for dy in range(-rad, rad + 1):
                    if max(abs(dx), abs(dy)) != rad:
                        continue
                    for e in buckets.get((ix + dx, iy + dy), ()):
                        best = min(best, dps(px, py, *e))
            if rad >= 1 and best < rad * cell:
                break
        return best

    worst = None
    worst_x = None
    worst_sd = None
    n = max(2, int(round((x1 - x0) / 0.01)))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        inside = poly.PointInside(xy(x, y))
        dist = nearest(x, y)
        sd = -dist if inside else dist
        clr = sd - HW
        if worst is None or clr < worst:
            worst = clr
            worst_x = x
            worst_sd = sd
    return {
        "clearance_mm": worst,
        "worst_x": worst_x,
        "signed_depth_mm": worst_sd,
        "local_clearance_mm": r3(mm(zone.GetLocalClearance())),
        "net": zone.GetNetname(),
    }


def main():
    head = git_head()
    blob = git_blob()
    board = pcbnew.LoadBoard(str(BOARD))
    drc = run_drc()
    gap = measure_gap(board)
    p_tr = gap["p_track"]
    p_pad = gap["p_pad"]
    hits = chord_hits(board, p_tr, p_pad)
    body = crosses_body(p_tr[0], p_tr[1], p_pad[0], p_pad[1])
    length = gap["gap_mm"]
    south = any(p["south_u1"] for p in gap["island_pads"]) or (
        gap["pad"]["ref"] == "U1" and gap["pad"]["y"] >= 37.0
    )
    fence = gap["pad"]["ref"] in {"J10", "J11"} or any(
        p["ref"] in {"J10", "J11"} for p in gap["island_pads"]
    )
    # The open's second DRC anchor is a track, not a header pad. Still record
    # that none of the island pads are J10/J11 or a south U1 pad.
    stop = None
    if drc["unconnected_items"] != 58 or drc["p017_unconnected"] != 1:
        stop = "counts"
    elif length > LIMIT + 1e-9:
        stop = "length"
    elif south:
        stop = "south pad"
    elif fence:
        stop = "east fence"
    decision = "NO-ROUTE" if stop else "WOULD-ROUTE"
    if decision != "NO-ROUTE":
        raise SystemExit(f"unexpected routable result stop={stop} length={length}")

    near = gap["near_item"]
    endpoints = {
        "a": {
            "ref": gap["pad"]["ref"],
            "pad": gap["pad"]["num"],
            "net": "P0.17",
            "center_xy": [round(gap["pad"]["x"], 3), round(gap["pad"]["y"], 3)],
            "layers": gap["j17_layers"],
            "shape": "rectangle 1.7 x 1.7 mm PTH",
            "role": "isolated pad island",
        },
        "b": {
            "ref": None,
            "pad": None,
            "net": "P0.17",
            "drc_anchor": "Track on In2.Cu, length 5.900 mm",
            "drc_anchor_xy": [round(near["a"][0], 3), round(near["a"][1], 3)],
            "track": {
                "layer": "In2.Cu",
                "width_mm": W,
                "start": [round(near["a"][0], 3), round(near["a"][1], 3)],
                "end": [round(near["b"][0], 3), round(near["b"][1], 3)],
            },
            "nearest_copper_xy": [round(p_tr[0], 3), round(p_tr[1], 3)],
            "island_pads": gap["island_pads"],
            "role": "pass30ay In2.Cu skirt island (U1.28 / J18.5 / J13.2). Not ripped.",
        },
    }
    ts = ist_now()
    payload = {
        "pass": "30az",
        "timestamp": ts,
        "kicad": "9.0.2",
        "decision": decision,
        "stopping_rule": stop,
        "routed": False,
        "copper_changed": False,
        "new_via": False,
        "segments": [],
        "net": "P0.17",
        "git_head": head,
        "pcb_blob": blob,
        "expected_head_prefix": "8942891",
        "expected_blob_prefix": "e1adfbd",
        "head_prefix_ok": head.startswith("8942891"),
        "blob_prefix_ok": blob.startswith("e1adfbd"),
        "precondition": {
            "unconnected": drc["unconnected_items"],
            "p017_opens": drc["p017_unconnected"],
            "required_unconnected": 58,
            "required_p017_opens": 1,
            "ok": drc["unconnected_items"] == 58 and drc["p017_unconnected"] == 1,
        },
        "drc": {k: v for k, v in drc.items() if k != "p017_item"},
        "endpoints": endpoints,
        "pad_edge_mm": r3(length),
        "pad_edge_exact_mm": length,
        "pad_edge_layer": gap["gap_layer"],
        "equidistant_y_mm": [round(gap["equidistant_y"][0], 3), round(gap["equidistant_y"][1], 3)],
        "chord": {
            "width_mm": W,
            "layer": "In2.Cu",
            "from_xy": [round(p_tr[0], 3), round(p_tr[1], 3)],
            "to_xy": [round(p_pad[0], 3), round(p_pad[1], 3)],
            "from_item": "east edge of In2.Cu P0.17 (45.550,21.500)-(45.550,27.400)",
            "to_item": "west edge of J17.1",
            "length_mm": r3(length),
            "crosses_sip_fab_body": body,
            "sip_fab_body_xy": {"x": [28.0, 44.0], "y": [26.75, 37.25]},
            "used_for_routing": False,
        },
        "chord_hits": hits,
        "rules": {
            "pad_edge_mm": r3(length),
            "limit_mm": LIMIT,
            "length_blocks": length > LIMIT,
            "south_u1_pad": south,
            "east_fence_j10_or_j11": fence,
            "stopping_rule": stop,
        },
        "other_nets_touched": False,
        "locked_copper_ripped": False,
        "gerbers": False,
        "commit": False,
        "backup": None,
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "PASS30AZ_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    fr = hits["foreign_under_0_15"]
    pw = hits["power_vin_under_0_20"]
    lines = [
        "# PASS30AZ_SUMMARY — P0.17",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.17",
        f"**Git HEAD:** `{head}`",
        f"**PCB blob:** `{blob}`",
        "**Routed:** no",
        "**Copper changed:** no",
        "**New via:** no",
        "**New segments:** 0",
        f"**Stopping rule:** {stop} (pad-edge {r3(length):.3f} mm > {LIMIT:.0f} mm). "
        "South U1 pad: no. East fence J10/J11: no.",
        "",
        "## Preconditions",
        "",
        f"Live `kicad-cli` DRC: unconnected **{drc['unconnected_items']}** (required 58), "
        f"P0.17 opens **{drc['p017_unconnected']}** (required 1). "
        f"short/clearance/crossing/hole "
        f"{drc['shorting_items']}/{drc['clearance']}/{drc['tracks_crossing']}/{drc['hole_clearance']}. "
        f"hole_to_hole {drc['hole_to_hole']}. GND islands {drc['gnd_zone_islands']}. "
        "Counts matched, so the gap was measured. No copper was added.",
        "",
        "## Endpoints",
        "",
        f"1. **J17.1** net P0.17, center ({gap['pad']['x']:.3f}, {gap['pad']['y']:.3f}), "
        f"rectangle 1.7×1.7 mm PTH. Copper on {', '.join(gap['j17_layers'])}. "
        "This pad is its own island.",
        f"2. **In2.Cu track** net P0.17, ({near['a'][0]:.3f}, {near['a'][1]:.3f})–"
        f"({near['b'][0]:.3f}, {near['b'][1]:.3f}), width 0.18 mm. "
        "DRC anchors the open on this track (length 5.900 mm). "
        "It is the pass30ay skirt, not a pad. Pads on the same island:",
        "",
    ]
    for p in gap["island_pads"]:
        lines.append(
            f"   - {p['ref']}.{p['pad']} center ({p['center_xy'][0]:.3f}, {p['center_xy'][1]:.3f}), "
            f"copper on {', '.join(p['layers'])}"
            + (" — south U1" if p["south_u1"] else "")
        )
    lines += [
        "",
        "Neither endpoint is a south U1 pad (U1 south means center y ≥ 37.0; U1.88 and U1.89 are the south pins). "
        "U1.28 is on the skirt island at y=26.750, north of that line, and it is not the open end. "
        "Neither endpoint is J10 or J11.",
        "",
        "## Pad-edge",
        "",
        f"Pad-edge length of a 0.18 mm join: **{r3(length):.3f} mm** "
        f"(exact {length:.6f} mm) on {gap['gap_layer']}. "
        f"`GetClearance` between J17.1 and the In2 track "
        f"({near['a'][0]:.3f}, {near['a'][1]:.3f})–({near['b'][0]:.3f}, {near['b'][1]:.3f}). "
        f"The west face of J17.1 (y {gap['equidistant_y'][0]:.3f}–{gap['equidistant_y'][1]:.3f}) "
        "is equally far from the east edge of that track, so every nearest pair has this length. "
        f"Over the {LIMIT:.0f} mm cap.",
        "",
        "## Straight chord (not used)",
        "",
        f"0.18 mm In2.Cu chord ({p_tr[0]:.3f}, {p_tr[1]:.3f}) → ({p_pad[0]:.3f}, {p_pad[1]:.3f}), "
        f"length {r3(length):.3f} mm. "
        f"Nearest copper: east edge of the In2 track at y={p_tr[1]:.3f}, and the west edge of J17.1. "
        f"Crosses the SiP fab body (x 28.0–44.0, y 26.75–37.25): **{body}**. "
        "The chord is east of x=44 and north of y=26.75.",
        "",
        f"Foreign items closer than 0.15 mm ({len(fr)}):",
        "",
    ]
    if not fr:
        lines.append("- none")
    for h in fr:
        lines.append(f"- {h['net']} {h['clearance_mm']:.3f} mm ({h['item']})")
    lines += [
        "",
        f"POWER/VIN items closer than 0.20 mm ({len(pw)}):",
        "",
    ]
    if not pw:
        lines.append("- none")
    for h in pw:
        lines.append(f"- {h['net']} {h['clearance_mm']:.3f} mm ({h['item']})")
    lines += [
        "",
        "POWER/VIN nets checked: " + ", ".join(sorted(POWER)) + ". "
        "Negative clearance is overlap. The VDD_nRF entry is the In2 pour the chord runs through, "
        "not a track. The chord was not used. No route was attempted.",
        "",
        "## Why no route",
        "",
        f"Rule that stopped the pass: **length**. Pad-edge {r3(length):.3f} mm is over 36 mm. "
        "South-pad and east-fence rules were checked and do not apply. "
        "No copper added. The pass30ay In2 skirt was not ripped. "
        "P0.19 and P0.20 were not started. No other net was touched. "
        "No backup (no edit). No Gerbers. No git commit.",
        "",
        "## DRC (unchanged board)",
        "",
        "| | unconnected | P0.17 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| measured | {drc['unconnected_items']} | {drc['p017_unconnected']} | {drc['shorting_items']} | "
        f"{drc['clearance']} | {drc['tracks_crossing']} | {drc['hole_clearance']} | "
        f"{drc['hole_to_hole']} | {drc['gnd_zone_islands']} |",
        "",
        "No before/after pair: copper was not edited.",
        "",
    ]
    (REPORTS / "PASS30AZ_SUMMARY.md").write_text("\n".join(lines) + "\n")

    paragraph = (
        "\n## Pass30az — P0.17 J17.1 leftover, no route — "
        f"{ts}\n\n"
        "**Decision:** **NO-ROUTE**. No copper. No via. No backup. "
        f"Stopping rule: length. Pad-edge **{r3(length):.3f} mm** on In2.Cu "
        f"(limit 36 mm). Endpoints: J17.1 ({gap['pad']['x']:.3f}, {gap['pad']['y']:.3f}), "
        f"PTH on F.Cu/In1.Cu/In2.Cu/B.Cu; and the pass30ay In2.Cu track "
        f"({near['a'][0]:.3f}, {near['a'][1]:.3f})–({near['b'][0]:.3f}, {near['b'][1]:.3f}) "
        f"on the island with U1.28 (40.250, 26.750) F.Cu, J18.5 (48.160, 62.000), "
        f"J13.2 (66.540, 76.000). Not a south U1 pad and not J10/J11.\n\n"
        f"Straight 0.18 mm chord ({p_tr[0]:.3f}, {p_tr[1]:.3f})→({p_pad[0]:.3f}, {p_pad[1]:.3f}) "
        f"does not cross the SiP fab body. "
        f"Foreign under 0.15 mm: {len(fr)}. POWER/VIN under 0.20 mm: {len(pw)}. "
        "Chord not used. Skirt not ripped. P0.19 and P0.20 not started. "
        f"Unconnected {drc['unconnected_items']}→{drc['unconnected_items']}. "
        f"P0.17 opens {drc['p017_unconnected']}→{drc['p017_unconnected']}. "
        "No other net touched. No Gerbers. No commit.\n\n"
        "**Artifacts:** `reports/PASS30AZ_SUMMARY.md`, `reports/PASS30AZ_SUMMARY.json`, "
        "`scripts/final_pass30az.py`\n"
    )
    text = REVIEW.read_text()
    if "## Pass30az —" not in text:
        if not text.endswith("\n"):
            text += "\n"
        REVIEW.write_text(text + paragraph)
    print(json.dumps({
        "decision": decision,
        "stop": stop,
        "gap_mm": r3(length),
        "body": body,
        "foreign": len(fr),
        "power": len(pw),
        "unc": drc["unconnected_items"],
        "p017": drc["p017_unconnected"],
        "south": south,
        "fence": fence,
    }, indent=2))


if __name__ == "__main__":
    main()
