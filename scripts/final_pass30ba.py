#!/usr/bin/env python3
"""pass30ba — ONE attempt: P0.19 only.

U1.30 already leaves on F.Cu (39.25, 26.75)–(39.25, 23.10) into the
through-via (39.25, 23.10). J18.7 is a separate island (B.Cu run to J13.4).
F.Cu and B.Cu free space from that via die at y=26.5. The straight F.Cu
chord crosses the SiP and hits VDD1. Do not retry P0.17. Do not stack on
the locked In1 P0.16 or In2 P0.17 skirts at x=44.60.

One In1.Cu jog, 8 segments, no new via. Offset to x=44.25 (0.35 mm
center-to-center from the skirts). The P0.06 via (45.150, 36.000) still
closes the east strip; the west strip is open beside the body but the
P0.06 via (44.000, 39.900) forces a two-segment dodge. Lands on J18.7.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30ba/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
IN1 = pcbnew.In1_Cu
IN2 = pcbnew.In2_Cu
W = 0.18
HW = W / 2
CF = 0.15
CP = 0.20
HOLE = 0.25
BODY = (28.0, 26.75, 44.0, 37.25)
POWER = {
    "VDD1", "VDD2", "VDD2_MID", "VDD_nRF", "VIN", "VIN_F", "VIN_FILT", "VIN_IN", "VDD_GPIO",
}
# In1.Cu. Start is the existing through-via. End overlaps J18.7.
POLY = [
    (39.25, 23.10),
    (39.25, 26.50),
    (44.25, 26.50),
    (44.25, 39.10),
    (42.80, 39.90),
    (44.25, 40.70),
    (44.25, 60.00),
    (53.24, 60.00),
    (53.24, 61.40),
]
P16 = [
    (40.70, 20.80), (45.55, 20.80), (45.55, 27.40), (44.60, 27.40),
    (44.60, 60.40), (45.62, 60.40), (45.62, 61.10),
]
P17 = [
    (40.25, 23.10), (40.25, 21.50), (45.55, 21.50), (45.55, 27.40),
    (44.60, 27.40), (44.60, 60.40), (48.16, 60.40), (48.16, 61.30),
]
P19_LOCKED = [
    ("F.Cu", F, 39.25, 26.75, 39.25, 23.10),
    ("F.Cu", F, 64.00, 64.00, 66.40, 64.00),
    ("B.Cu", B, 53.24, 64.00, 64.00, 64.00),
    ("B.Cu", B, 66.40, 64.00, 71.62, 64.00),
    ("B.Cu", B, 53.24, 62.00, 53.24, 64.00),
    ("B.Cu", B, 71.62, 64.00, 71.62, 76.00),
]
STRAIGHT_A = (39.378, 27.147)
STRAIGHT_B = (52.993, 61.187)
VIA_X, VIA_Y = 39.25, 23.10
GOAL_X, GOAL_Y = 53.24, 62.0
LAYERS = (("F.Cu", F), ("In1.Cu", IN1), ("In2.Cu", IN2), ("B.Cu", B))


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_blob() -> str:
    return subprocess.check_output(
        ["git", "hash-object", "nRF9161-DEV-BOARD.kicad_pcb"], cwd=ROOT, text=True
    ).strip()


def near(a, b, tol=0.02) -> bool:
    return abs(a - b) < tol


def ends(t):
    return (mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y))


def track_is(t, x1, y1, x2, y2) -> bool:
    a, b, c, d = ends(t)
    return (near(a, x1) and near(b, y1) and near(c, x2) and near(d, y2)) or (
        near(a, x2) and near(b, y2) and near(c, x1) and near(d, y1)
    )


def via_at(board, net, x, y) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if near(mm(t.GetPosition().x), x) and near(mm(t.GetPosition().y), y):
            return True
    return False


def poly_ok(board, pts, net, layer) -> bool:
    tracks = [
        t for t in board.GetTracks()
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == net and t.GetLayer() == layer
    ]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if not any(track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    return True


def dps(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 < 1e-18:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def segseg(ax, ay, bx, by, cx, cy, dx, dy) -> float:
    return min(
        dps(ax, ay, cx, cy, dx, dy), dps(bx, by, cx, cy, dx, dy),
        dps(cx, cy, ax, ay, bx, by), dps(dx, dy, ax, ay, bx, by),
    )


def crosses_body(x1, y1, x2, y2) -> bool:
    xa, ya, xb, yb = BODY
    dx, dy = x2 - x1, y2 - y1
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


def body_hit(x1, y1, x2, y2) -> bool:
    xa, ya, xb, yb = BODY[0] - HW, BODY[1] - HW, BODY[2] + HW, BODY[3] + HW
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(2, int(length / 0.02))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if xa <= x <= xb and ya <= y <= yb:
            return True
        if x - HW <= 24.2:
            return True
        if 81.8 <= x <= 97.3 and abs(y - 44.60) <= (HW + 0.15):
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


def track_counts(board) -> dict:
    c, v = Counter(), Counter()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            v[t.GetNetname()] += 1
        else:
            c[t.GetNetname()] += 1
    return {"tracks": dict(c), "vias": dict(v)}


def nongnd_counts(data) -> Counter:
    c: Counter = Counter()
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        for n in {n for n in re.findall(r"\[([^\]]+)\]", desc) if n != "GND"}:
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
    tmp = Path("/tmp/nrf30ba_drc.json")
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", str(tmp), str(BOARD)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
        "p019_unconnected": nongnd_counts(data).get("P0.19", 0),
        "nongnd": dict(nongnd_counts(data)),
    }
    return {"stats": stats, "data": data}


def protect_ok(board) -> dict:
    return {
        "p019_stub": any(
            t.GetNetname() == "P0.19" and t.GetLayer() == F and track_is(t, 39.25, 26.75, 39.25, 23.10)
            for t in board.GetTracks()
        ),
        "p019_via": via_at(board, "P0.19", 39.25, 23.10),
        "p019_via_64": via_at(board, "P0.19", 64.00, 64.00),
        "p019_via_664": via_at(board, "P0.19", 66.40, 64.00),
        "p019_locked_tracks": all(
            any(
                t.GetNetname() == "P0.19" and t.GetLayer() == layer and track_is(t, x1, y1, x2, y2)
                for t in board.GetTracks()
            )
            for _name, layer, x1, y1, x2, y2 in P19_LOCKED
        ),
        "p016_in1": poly_ok(board, P16, "P0.16", IN1),
        "p017_in2": poly_ok(board, P17, "P0.17", IN2),
        "p016_via": via_at(board, "P0.16", 40.70, 20.80),
        "p017_via": via_at(board, "P0.17", 40.25, 23.10),
        "p015_via": via_at(board, "P0.15", 41.75, 23.10),
        "p030_via": via_at(board, "P0.30", 112.40, 46.40),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "dec0": any(
            t.GetNetname() == "DEC0" and t.GetLayer() == B and track_is(t, 46.950, 30.900, 48.100, 30.900)
            for t in board.GetTracks()
        ),
    }


def collect(board, layer):
    vias, holes, pads, tracks = [], [], [], []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.19":
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            vias.append((x, y, mm(t.GetWidth(layer)) / 2, net, net in POWER))
            holes.append((x, y, mm(t.GetDrillValue()) / 2, f"via {net} @{x:.3f},{y:.3f}"))
        elif t.GetLayer() == layer:
            tracks.append((
                mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y),
                mm(t.GetWidth()) / 2, net, net in POWER,
            ))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == "P0.19" or not p.IsOnLayer(layer):
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            pads.append((p, f"{fp.GetReference()}.{p.GetNumber()}", net, net in POWER, x, y))
            if p.GetDrillSize().x and f"{fp.GetReference()}.{p.GetNumber()}" != "J18.7":
                holes.append((x, y, mm(p.GetDrillSize().x) / 2, f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]"))
    return vias, holes, pads, tracks


def seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, layer):
    if body_hit(x1, y1, x2, y2):
        return {"ok": False, "why": "body_or_keepout", "foreign": None, "power": None, "hole": None}
    worst = pwr = hh = None

    def eat(clr, net, desc, isp=False, hole=False):
        nonlocal worst, pwr, hh
        if hole:
            if hh is None or clr < hh[0]:
                hh = (clr, desc)
            return
        if worst is None or clr < worst[0]:
            worst = (clr, net, desc)
        if isp and (pwr is None or clr < pwr[0]):
            pwr = (clr, net, desc)

    for x, y, r, net, isp in vias:
        if x < min(x1, x2) - 3 or x > max(x1, x2) + 3 or y < min(y1, y2) - 3 or y > max(y1, y2) + 3:
            continue
        eat(dps(x, y, x1, y1, x2, y2) - r - HW, net, f"via@{x:.3f},{y:.3f}", isp)
    for x1t, y1t, x2t, y2t, ohw, net, isp in tracks:
        if max(x1t, x2t) < min(x1, x2) - 3 or min(x1t, x2t) > max(x1, x2) + 3:
            continue
        if max(y1t, y2t) < min(y1, y2) - 3 or min(y1t, y2t) > max(y1, y2) + 3:
            continue
        dist = segseg(x1, y1, x2, y2, x1t, y1t, x2t, y2t)
        eat(dist - ohw - HW, net, f"trk ({x1t:.2f},{y1t:.2f})-({x2t:.2f},{y2t:.2f})", isp)
    for x, y, r, name in holes:
        if x < min(x1, x2) - 3 or x > max(x1, x2) + 3 or y < min(y1, y2) - 3 or y > max(y1, y2) + 3:
            continue
        eat(dps(x, y, x1, y1, x2, y2) - r - HW, "HOLE", name, hole=True)
    sh = pcbnew.SHAPE_SEGMENT(xy(x1, y1), xy(x2, y2), pcbnew.FromMM(W))
    for p, name, net, isp, x, y in pads:
        if x < min(x1, x2) - 4 or x > max(x1, x2) + 4 or y < min(y1, y2) - 4 or y > max(y1, y2) + 4:
            continue
        eat(mm(sh.GetClearance(p.GetEffectiveShape(layer))), net, f"pad {name}", isp)
    foreign_ok = worst is None or worst[0] >= CF - 1e-6
    power_ok = pwr is None or pwr[0] >= CP - 1e-6
    hole_ok = hh is None or hh[0] >= HOLE - 1e-6
    return {
        "ok": foreign_ok and power_ok and hole_ok,
        "foreign": None if worst is None else round(worst[0], 4),
        "foreign_item": None if worst is None else {"net": worst[1], "item": worst[2]},
        "power": None if pwr is None else round(pwr[0], 4),
        "power_item": None if pwr is None else {"net": pwr[1], "item": pwr[2]},
        "hole": None if hh is None else round(hh[0], 4),
        "hole_item": None if hh is None else hh[1],
        "why": None,
    }


def measure_poly(board) -> dict:
    vias, holes, pads, tracks = collect(board, IN1)
    rows, mf, mp, mh = [], None, None, None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, IN1)
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
    land = pcbnew.SHAPE_SEGMENT(xy(*POLY[-2]), xy(*POLY[-1]), pcbnew.FromMM(W))
    hits_pad = bool(j and land.Collide(j.GetEffectiveShape(IN1)))
    ok = all(r["ok"] for r in rows) and hits_pad and len(POLY) - 1 <= 8
    return {
        "segments": rows,
        "segment_count": len(POLY) - 1,
        "min_clearance_mm": None if mf is None else mf[0],
        "min_clearance_item": None if mf is None else mf[1],
        "min_power_vin_mm": None if mp is None else mp[0],
        "min_power_vin_item": None if mp is None else mp[1],
        "min_hole_mm": None if mh is None else mh[0],
        "min_hole_item": None if mh is None else mh[1],
        "lands_on_j18_7": hits_pad,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= HOLE - 1e-9,
        "ok": ok,
        "layer": "In1.Cu",
        "new_via": None,
    }


def pad_and_islands(board) -> dict:
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "P0.19":
                continue
            layers = [lid for _, lid in LAYERS if p.IsOnLayer(lid)]
            items.append({
                "kind": "pad", "name": f"{fp.GetReference()}.{p.GetNumber()}",
                "ref": fp.GetReference(), "num": p.GetNumber(),
                "x": mm(p.GetPosition().x), "y": mm(p.GetPosition().y),
                "layers": layers, "obj": p,
            })
    for t in board.GetTracks():
        if t.GetNetname() != "P0.19":
            continue
        if t.GetClass() == "PCB_VIA":
            layers = [lid for _, lid in LAYERS if t.IsOnLayer(lid)]
            items.append({
                "kind": "via",
                "name": f"via@{mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f}",
                "x": mm(t.GetPosition().x), "y": mm(t.GetPosition().y),
                "layers": layers, "obj": t,
            })
        else:
            items.append({
                "kind": "trk",
                "name": (
                    f"{board.GetLayerName(t.GetLayer())} "
                    f"({mm(t.GetStart().x):.3f},{mm(t.GetStart().y):.3f})-"
                    f"({mm(t.GetEnd().x):.3f},{mm(t.GetEnd().y):.3f})"
                ),
                "x": (mm(t.GetStart().x) + mm(t.GetEnd().x)) / 2,
                "y": (mm(t.GetStart().y) + mm(t.GetEnd().y)) / 2,
                "layers": [t.GetLayer()], "obj": t,
            })

    def shp(it, lid):
        if it["kind"] == "pad":
            return it["obj"].GetEffectiveShape(lid)
        if it["kind"] == "via":
            return pcbnew.SHAPE_CIRCLE(xy(it["x"], it["y"]), pcbnew.FromMM(mm(it["obj"].GetWidth(lid)) / 2))
        return pcbnew.SHAPE_SEGMENT(it["obj"].GetStart(), it["obj"].GetEnd(), it["obj"].GetWidth())

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
            if touches(i, j):
                union(i, j)
    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.30")
    j18 = next(i for i, it in enumerate(items) if it["name"] == "J18.7")
    same = find(u1) == find(j18)
    u = items[u1]["obj"]
    j = items[j18]["obj"]
    gap = mm(u.GetEffectiveShape(F).GetClearance(j.GetEffectiveShape(F)))
    # remaining opens: pads not on the U1 island, with pad-edge to nearest other-island copper
    opens = []
    if same:
        # still list any pad whose DRC partner would be the other side; none if joined
        pass
    else:
        other = [i for i in range(len(items)) if find(i) != find(u1)]
        # the open end on the U1 side is U1.30; report both endpoints' pad-edge
        for idx, label in ((u1, "U1.30"), (j18, "J18.7")):
            best = None
            others = [i for i in range(len(items)) if find(i) != find(idx)]
            for name, lid in LAYERS:
                if lid not in items[idx]["layers"]:
                    continue
                sh = shp(items[idx], lid)
                for i in others:
                    if lid not in items[i]["layers"]:
                        continue
                    c = mm(sh.GetClearance(shp(items[i], lid)))
                    if best is None or c < best[0]:
                        best = (c, name, items[i]["name"])
            it = items[idx]
            opens.append({
                "ref": it.get("ref", it["name"]),
                "pad": it.get("num", ""),
                "name": it["name"],
                "center_xy": [round(it["x"], 3), round(it["y"], 3)],
                "pad_edge_mm": None if best is None else round(best[0], 3),
                "nearest": None if best is None else {"layer": best[1], "item": best[2]},
            })
    return {
        "same_island": same,
        "islands": len({find(i) for i in range(len(items))}),
        "u1_30": [round(items[u1]["x"], 3), round(items[u1]["y"], 3)],
        "j18_7": [round(items[j18]["x"], 3), round(items[j18]["y"], 3)],
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "opens_if_separate": opens,
        "u1_island": [items[i]["name"] for i in range(len(items)) if find(i) == find(u1)],
        "j18_island": [items[i]["name"] for i in range(len(items)) if find(i) == find(j18)],
    }


def straight_hits(board) -> dict:
    ax, ay = STRAIGHT_A
    bx, by = STRAIGHT_B
    hits = []
    vdd1 = None
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.19":
            continue
        if t.GetClass() == "PCB_VIA":
            if not t.IsOnLayer(F):
                continue
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if not (30 < x < 70 and 20 < y < 70):
                continue
            clr = dps(x, y, ax, ay, bx, by) - mm(t.GetWidth(F)) / 2 - HW
            if clr < CF:
                hits.append({"clearance_mm": round(clr, 3), "net": net, "item": f"via@{x:.3f},{y:.3f}", "power": net in POWER})
        elif t.GetLayer() == F:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            hw = mm(t.GetWidth()) / 2
            clr = segseg(ax, ay, bx, by, x1, y1, x2, y2) - hw - HW
            rec = {
                "clearance_mm": round(clr, 3),
                "net": net,
                "item": f"F.Cu ({x1:.2f},{y1:.2f})-({x2:.2f},{y2:.2f}) w={mm(t.GetWidth()):.3f}",
                "power": net in POWER,
            }
            if (
                net == "VDD1"
                and abs(y1 - 38.0) < 0.02 and abs(y2 - 38.0) < 0.02
                and abs(min(x1, x2) - 43.25) < 0.05 and abs(max(x1, x2) - 50.52) < 0.05
            ):
                vdd1 = rec
            if clr < CF:
                hits.append(rec)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(F) or p.GetNetname() == "P0.19":
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            if not (30 < x < 70 and 20 < y < 70):
                continue
            sh = pcbnew.SHAPE_SEGMENT(xy(ax, ay), xy(bx, by), pcbnew.FromMM(W))
            c = mm(sh.GetClearance(p.GetEffectiveShape(F)))
            # geometric signed, so overlaps stay negative when the centerline crosses
            # GetClearance clamps at 0; keep it only when positive-ish
            if c < CF:
                hits.append({
                    "clearance_mm": round(c, 3),
                    "net": p.GetNetname() or "<no-net>",
                    "item": f"pad {fp.GetReference()}.{p.GetNumber()}",
                    "power": (p.GetNetname() or "") in POWER,
                    "note": "GetClearance (0 means overlap)",
                })
    hits.sort(key=lambda h: h["clearance_mm"])
    # dedupe identical items
    seen = set()
    uniq = []
    for h in hits:
        k = (h["net"], h["item"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(h)
    return {
        "from": list(STRAIGHT_A),
        "to": list(STRAIGHT_B),
        "length_mm": round(math.hypot(bx - ax, by - ay), 3),
        "crosses_sip_body": crosses_body(ax, ay, bx, by),
        "vdd1_track": vdd1,
        "foreign_under_0_15": [h for h in uniq if h["clearance_mm"] < CF],
        "power_under_0_20": [h for h in uniq if h.get("power") and h["clearance_mm"] < CP],
    }


def layer_reach(board, layer):
    BUCKET = 2.0
    buck, hb, pb = defaultdict(list), defaultdict(list), defaultdict(list)

    def add(store, item, x0, y0, x1, y1):
        for ix in range(int(math.floor(min(x0, x1) / BUCKET)), int(math.floor(max(x0, x1) / BUCKET)) + 1):
            for iy in range(int(math.floor(min(y0, y1) / BUCKET)), int(math.floor(max(y0, y1) / BUCKET)) + 1):
                store[(ix, iy)].append(item)

    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.19":
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if not (15 <= x <= 80 and 8 <= y <= 80):
                continue
            r = mm(t.GetWidth(layer)) / 2
            req = CP if net in POWER else CF
            rad = r + HW + req
            add(buck, ("c", x, y, r, req), x - rad, y - rad, x + rad, y + rad)
            hr = mm(t.GetDrillValue()) / 2
            rad = hr + HW + HOLE
            add(hb, (x, y, hr), x - rad, y - rad, x + rad, y + rad)
        elif t.GetLayer() == layer:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            hw = mm(t.GetWidth()) / 2
            req = CP if net in POWER else CF
            rad = hw + HW + req
            add(buck, ("t", x1, y1, x2, y2, hw, req), min(x1, x2) - rad, min(y1, y2) - rad, max(x1, x2) + rad, max(y1, y2) + rad)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == "P0.19":
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            if not (15 <= x <= 80 and 8 <= y <= 80):
                continue
            if p.GetDrillSize().x:
                hr = mm(p.GetDrillSize().x) / 2
                rad = hr + HW + HOLE
                add(hb, (x, y, hr), x - rad, y - rad, x + rad, y + rad)
            if not p.IsOnLayer(layer):
                continue
            sx, sy = mm(p.GetSize().x), mm(p.GetSize().y)
            inf = HW + (CP if net in POWER else CF)
            hx, hy = sx / 2 + inf, sy / 2 + inf
            add(pb, (x, y, hx, hy, abs(sx - sy) < 1e-6), x - hx, y - hy, x + hx, y + hy)

    def ok(x, y):
        if x - HW <= 24.2:
            return False
        if BODY[0] - HW <= x <= BODY[2] + HW and BODY[1] - HW <= y <= BODY[3] + HW:
            return False
        ix, iy = int(math.floor(x / BUCKET)), int(math.floor(y / BUCKET))
        for item in buck.get((ix, iy), ()):
            if item[0] == "c":
                _, cx, cy, r, req = item
                if (x - cx) ** 2 + (y - cy) ** 2 < (r + HW + req) ** 2:
                    return False
            else:
                _, x1, y1, x2, y2, hw, req = item
                if dps(x, y, x1, y1, x2, y2) < hw + HW + req:
                    return False
        for cx, cy, hr in hb.get((ix, iy), ()):
            if (x - cx) ** 2 + (y - cy) ** 2 < (hr + HW + HOLE) ** 2:
                return False
        for cx, cy, hx, hy, circ in pb.get((ix, iy), ()):
            dx, dy = abs(x - cx), abs(y - cy)
            if circ and dx * dx + dy * dy < hx * hx:
                return False
            if (not circ) and dx < hx and dy < hy:
                return False
        return True

    step = 0.25
    x0, x1, y0, y1 = 24.5, 72.0, 16.0, 70.0
    nx = int(round((x1 - x0) / step)) + 1
    ny = int(round((y1 - y0) / step)) + 1
    leg = bytearray(nx * ny)
    for iy in range(ny):
        y = y0 + iy * step
        row = iy * nx
        for ix in range(nx):
            if ok(x0 + ix * step, y):
                leg[row + ix] = 1
    q = deque()
    seen = set()
    for iy in range(ny):
        for ix in range(nx):
            if leg[iy * nx + ix] and math.hypot(x0 + ix * step - VIA_X, y0 + iy * step - VIA_Y) <= 0.40:
                seen.add((ix, iy))
                q.append((ix, iy))
    goal = False
    while q:
        ix, iy = q.popleft()
        if math.hypot(x0 + ix * step - GOAL_X, y0 + iy * step - GOAL_Y) <= 0.90:
            goal = True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jx, jy = ix + dx, iy + dy
            if 0 <= jx < nx and 0 <= jy < ny and (jx, jy) not in seen and leg[jy * nx + jx]:
                seen.add((jx, jy))
                q.append((jx, jy))
    if not seen:
        return {"cells": 0, "reaches_j18": False}
    xs = [x0 + ix * step for ix, iy in seen]
    ys = [y0 + iy * step for ix, iy in seen]
    return {
        "cells": len(seen),
        "bbox": [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2)],
        "ymax": round(max(ys), 2),
        "xmax": round(max(xs), 2),
        "reaches_j18": goal,
    }


def via_layers(board) -> dict:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.19":
            continue
        if near(mm(t.GetPosition().x), VIA_X) and near(mm(t.GetPosition().y), VIA_Y):
            return {
                "pos": [VIA_X, VIA_Y],
                "drill_mm": round(mm(t.GetDrillValue()), 3),
                "pad_mm": round(mm(t.GetWidth(F)), 3),
                "top": board.GetLayerName(t.TopLayer()),
                "bottom": board.GetLayerName(t.BottomLayer()),
                "on": {
                    "F.Cu": bool(t.IsOnLayer(F)),
                    "In1.Cu": bool(t.IsOnLayer(IN1)),
                    "In2.Cu": bool(t.IsOnLayer(IN2)),
                    "B.Cu": bool(t.IsOnLayer(B)),
                },
            }
    return {}


def p006_note(board) -> dict:
    """East strip beside x=44.60 vs the P0.06 via at (45.150, 36.000)."""
    out = {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        if abs(mm(t.GetPosition().x) - 45.150) < 0.02 and abs(mm(t.GetPosition().y) - 36.000) < 0.02:
            r = mm(t.GetWidth(IN1)) / 2
            # centerline x that keeps 0.15 to this via, east of the skirt (skirt needs x>=44.93)
            need = r + HW + CF
            out = {
                "net": t.GetNetname(),
                "at": [45.150, 36.000],
                "radius_mm": round(r, 3),
                "need_dx_mm": round(need, 3),
                "skirt_x": 44.60,
                "east_of_skirt_x": 44.93,
                "clearance_at_x_44_93_mm": round(abs(45.150 - 44.93) - r - HW, 3),
                "clearance_at_x_44_25_mm": round(abs(45.150 - 44.25) - r - HW, 3),
                "east_strip_closed": abs(45.150 - 44.93) - r - HW < CF,
                "west_x_44_25_clears_this_via": abs(45.150 - 44.25) - r - HW >= CF,
            }
    return out


def add_route(board):
    net = board.FindNet("P0.19")
    if net is None:
        raise SystemExit("P0.19 missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(xy(x1, y1))
        tr.SetEnd(xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN1)
        tr.SetNet(net)
        board.Add(tr)


def gained(before: dict, after: dict) -> dict:
    out = {}
    for k in set(before) | set(after):
        if k == "P0.19":
            continue
        if after.get(k, 0) > before.get(k, 0):
            out[k] = [before.get(k, 0), after.get(k, 0)]
    return out


def restore():
    shutil.copy2(BACKUP, BOARD)


def counts_locked(before_counts, board) -> list:
    after = track_counts(board)
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
        bad.append(f"P0.19 tracks {before_counts['tracks'].get('P0.19', 0)}->{after['tracks'].get('P0.19', 0)} expected {expect}")
    return bad


def write_outputs(decision, info, before, after, reason, measure):
    ts = ist_now()
    b, a = before, after
    segs = [
        {"layer": "In1.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30ba",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.19",
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "same_island_u1_30_j18_7": info["gap"]["same_island"],
        "pad_edge_mm": info["gap"]["pad_edge_mm"],
        "pad_edge_exact_mm": info["gap"]["pad_edge_exact_mm"],
        "u1_30": info["gap"]["u1_30"],
        "j18_7": info["gap"]["j18_7"],
        "straight_chord": info["straight"],
        "layers_checked": info["reach"],
        "layer_choice": info.get("layer_choice"),
        "p006_via": info.get("p006"),
        "via": info.get("via"),
        "new_via": False,
        "segments": segs if placed else [],
        "segment_count": len(segs) if placed else 0,
        "attempted_segments": segs,
        "dead_end": None if placed else reason,
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "min_foreign_item": measure.get("min_clearance_item"),
        "min_power_clearance_mm": measure.get("min_power_vin_mm"),
        "min_power_item": measure.get("min_power_vin_item"),
        "min_hole_clearance_mm": measure.get("min_hole_mm"),
        "min_hole_item": measure.get("min_hole_item"),
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
        "p017_not_retried": True,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "locked_copper_ripped": False,
        "board_sha256": sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
    }
    (REPORTS / "PASS30BA_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    st = info["straight"]
    vdd = st.get("vdd1_track") or {}
    lines = [
        "# PASS30BA_SUMMARY — P0.19",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.19",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**U1.30 and J18.7 same island:** {info['gap']['same_island']}",
        f"**New via:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 8)",
        f"**Min foreign clearance:** {measure.get('min_clearance_mm')} mm vs {measure.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {measure.get('min_power_vin_mm')} mm vs {measure.get('min_power_vin_item')}",
        f"**Min hole clearance:** {measure.get('min_hole_mm')} mm vs {measure.get('min_hole_item')}",
        f"**P0.19 opens:** {b.get('p019_unconnected')} → {a.get('p019_unconnected')}",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)",
        "",
        "## Endpoints",
        "",
        f"U1.30 center {info['gap']['u1_30']}, copper point {list(STRAIGHT_A)}. "
        f"Existing exit F.Cu (39.25, 26.75)–(39.25, 23.10) and through-via (39.25, 23.10) were not ripped. "
        f"J18.7 center {info['gap']['j18_7']} (census point {list(STRAIGHT_B)} is inside the 1.7 mm pad, not the center). "
        f"Same island: **{info['gap']['same_island']}**. Islands: {info['gap']['islands']}.",
        "",
        f"U1 island: {', '.join(info['gap']['u1_island'])}.",
        "",
        f"J18 island: {', '.join(info['gap']['j18_island'])}.",
        "",
        "## Pad-edge",
        "",
        f"Remeasured F.Cu effective-shape clearance U1.30↔J18.7: **{info['gap']['pad_edge_exact_mm']:.6f} mm** "
        f"(reported {info['gap']['pad_edge_mm']} mm). Census chord length between {list(STRAIGHT_A)} and "
        f"{list(STRAIGHT_B)} is {st['length_mm']} mm. U1.30 is F.Cu only, so there is no inner-layer pad-edge.",
        "",
        "## Straight chord (not used)",
        "",
        f"0.18 mm F.Cu chord {list(STRAIGHT_A)} → {list(STRAIGHT_B)}, length {st['length_mm']} mm. "
        f"Crosses the SiP fab body (x 28.0–44.0, y 26.75–37.25): **{st['crosses_sip_body']}**. "
        f"VDD1 F.Cu (50.52, 38.00)–(43.25, 38.00) w=0.40 signed edge clearance **{vdd.get('clearance_mm')} mm** "
        f"({vdd.get('item')}). The centerline crosses that track, so the clearance is −0.29 mm when the half-widths "
        f"are 0.09 and 0.20. Not used.",
        "",
        f"Foreign items under 0.15 mm on that chord: {len(st['foreign_under_0_15'])}. "
        f"POWER/VIN under 0.20 mm: {len(st['power_under_0_20'])}.",
        "",
        "## Layers checked",
        "",
        f"Existing via (39.25, 23.10) drill {info.get('via', {}).get('drill_mm')} mm, "
        f"pad {info.get('via', {}).get('pad_mm')} mm, {info.get('via', {}).get('top')} to {info.get('via', {}).get('bottom')}. "
        f"On layers: {info.get('via', {}).get('on')}. Through-via, so the route starts on a layer it already hits. No second via.",
        "",
        f"- F.Cu: {info['reach'].get('F')}",
        f"- B.Cu: {info['reach'].get('B')}",
        f"- In1.Cu: {info['reach'].get('In1')}",
        f"- In2.Cu: {info['reach'].get('In2')}",
        "",
        info.get("layer_choice", ""),
        "",
        f"P0.06 via check: {info.get('p006')}.",
        "",
        "## Route" if placed else "## Attempt",
        "",
    ]
    if placed:
        lines.append("In1.Cu 0.18 mm, no new via. Corners:")
        lines.append("")
        for s in segs:
            lines.append(f"- ({s['start'][0]:.2f}, {s['start'][1]:.2f}) → ({s['end'][0]:.2f}, {s['end'][1]:.2f})")
        lines.append("")
        lines.append(
            "x=44.25 is 0.35 mm center-to-center from the locked x=44.60 skirts (edge clearance 0.17 mm). "
            "Not stacked on them. The two diagonal segments dodge P0.06 via (44.000, 39.900) south of the fab body. "
            "End (53.24, 60.00)–(53.24, 61.40) overlaps J18.7. x>24.2. No sealed B.Cu pocket. "
            "P0.16 In1 skirt and P0.17 In2 skirt not ripped. P0.17 not retried. No other net."
        )
    else:
        lines.append(reason)
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
        f"| after | {a.get('unconnected_items')} | {a.get('p019_unconnected')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |",
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}.",
        "Locked copper not ripped. P0.17 not retried. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BA_SUMMARY.md").write_text("\n".join(lines) + "\n")
    return ts


def patch_review(ts, decision, before, after, measure, info):
    text = REVIEW.read_text()
    if "## Pass30ba —" in text:
        return
    b, a = before, after
    if decision == "KEEP":
        route = (
            "In1.Cu 0.18 mm, no new via: (39.25, 23.10)→(39.25, 26.50)→(44.25, 26.50)→"
            "(44.25, 39.10)→(42.80, 39.90)→(44.25, 40.70)→(44.25, 60.00)→(53.24, 60.00)→(53.24, 61.40)."
        )
    else:
        route = "No copper left on the board."
    note = (
        f"\n## Pass30ba — P0.19 — {ts}\n\n"
        f"**Decision:** **{decision}**. U1.30 and J18.7 were not the same island "
        f"(pad-edge {info['gap']['pad_edge_mm']} mm). {route} "
        f"Straight F.Cu chord (39.378, 27.147)→(52.993, 61.187) crosses the SiP and hits VDD1 at "
        f"{(info['straight'].get('vdd1_track') or {}).get('clearance_mm')} mm on "
        f"(50.52, 38.00)–(43.25, 38.00); not used. "
        f"F.Cu and B.Cu from via (39.25, 23.10) die at y=26.5. "
        f"Foreign {measure.get('min_clearance_mm')} mm vs {measure.get('min_clearance_item')}. "
        f"POWER {measure.get('min_power_vin_mm')} mm vs {measure.get('min_power_vin_item')}. "
        f"P0.19 opens {b.get('p019_unconnected')}→{a.get('p019_unconnected')}. "
        f"Unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole {a.get('shorting_items')}/{a.get('clearance')}/"
        f"{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"P0.16 and P0.17 skirts not ripped. P0.17 not retried. No other net. No Gerbers. No commit.\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    REVIEW.write_text(text + note)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    info = {"git_head": git_head(), "pcb_blob": git_blob(), "gained": {}}
    print("GIT", info["git_head"], info["pcb_blob"], flush=True)
    before = run_drc(REPORTS / "DRC_PASS30BA_BEFORE.json")
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = pad_and_islands(board)
    info["straight"] = straight_hits(board)
    info["via"] = via_layers(board)
    info["p006"] = p006_note(board)
    info["protect_before"] = protect_ok(board)
    info["fp"] = footprint_xy(board)
    info["counts"] = track_counts(board)
    print("GAP", info["gap"]["same_island"], info["gap"]["pad_edge_exact_mm"], info["gap"]["j18_7"], flush=True)
    print("VDD1", info["straight"].get("vdd1_track"), "body", info["straight"]["crosses_sip_body"], flush=True)
    print("VIA", info["via"], flush=True)
    info["reach"] = {
        "F": layer_reach(board, F),
        "B": layer_reach(board, B),
        "In1": layer_reach(board, IN1),
        "In2": layer_reach(board, IN2),
    }
    print("REACH", info["reach"], flush=True)
    info["layer_choice"] = (
        "F.Cu and B.Cu free space from the via both die at ymax 26.5, short of J18.7, same wall as the "
        "P0.16/P0.17 vias. A second via was not added. In1.Cu and In2.Cu both flood-fill to J18.7. "
        "Both inner layers already carry a locked skirt at x=44.60 (P0.16 on In1, P0.17 on In2). "
        "The P0.06 via (45.150, 36.000) r=0.25 still closes the strip immediately east of x=44.60 "
        f"(clearance at x=44.93 is {info['p006'].get('clearance_at_x_44_93_mm')} mm). "
        "The west offset x=44.25 clears that via "
        f"({info['p006'].get('clearance_at_x_44_25_mm')} mm) and sits 0.35 mm from the skirt. "
        "A second P0.06 via at (44.000, 39.900) blocks x=44.25 at y≈39.9, so the route dodges west of it "
        "south of the fab body, then returns. In1 was the one attempt: it is the GND plane (extra islands waived) "
        "and its P0.16 end cap stops at x=45.62, so y=60.00 passes north of that cap into J18.7. "
        "In2 was not used (VDD_nRF zone clearance 0.5 mm, and the P0.17 end cap runs to x=48.16). "
        "No sealed B.Cu pocket. x>24.2."
    )
    measure = measure_poly(board)
    print("MEASURE", {k: measure[k] for k in measure if k != "segments"}, flush=True)

    def finish(decision, reason, after_stats):
        ts = write_outputs(decision, info, bst, after_stats, reason, measure)
        patch_review(ts, decision, bst, after_stats, measure, info)
        print(decision, reason, flush=True)

    if bst["unconnected_items"] != 58:
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish("NO-ROUTE", f"Pre-edit unconnected is {bst['unconnected_items']}, not 58. No copper edited.", bst)
        return
    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish(
            "NO-ROUTE",
            f"U1.30 and J18.7 are already the same island. Remaining P0.19 opens: {info['gap']['opens_if_separate']}. No copper added.",
            bst,
        )
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if not info["via"].get("on", {}).get("In1.Cu"):
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish("NO-ROUTE", f"Existing via does not hit In1.Cu: {info['via']}. No copper added.", bst)
        return
    if not measure["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish(
            "NO-ROUTE",
            "No legal 8-segment path. The one In1 jog failed pre-add clearance or did not land on J18.7 "
            f"(foreign {measure['min_clearance_mm']} vs {measure['min_clearance_item']}, "
            f"POWER {measure['min_power_vin_mm']} vs {measure['min_power_vin_item']}, "
            f"hole {measure['min_hole_mm']} vs {measure['min_hole_item']}, "
            f"land {measure['lands_on_j18_7']}, segments {measure['segment_count']}). "
            "F.Cu/B.Cu die at y=26.5. East of x=44.60 is closed by P0.06 via (45.150, 36.000). "
            "No copper added. No second path. P0.17 not retried.",
            bst,
        )
        return
    if min(p[0] for p in POLY) <= 24.2:
        shutil.copy2(REPORTS / "DRC_PASS30BA_BEFORE.json", REPORTS / "DRC_PASS30BA_AFTER.json")
        finish("NO-ROUTE", "Route enters x<=24.2. No copper added.", bst)
        return

    shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup copy failed")

    add_route(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != footprint_xy(board).get(ref))
    ripped = counts_locked(info["counts"], board)
    pa = protect_ok(board)
    if moved or ripped or not all(pa.values()) or not poly_ok(board, POLY, "P0.19", IN1):
        restore()
        after = run_drc(REPORTS / "DRC_PASS30BA_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Protect guard failed before refill. moved={moved} ripped={ripped} protect={pa}. "
            f"Full restore. Post-revert unconnected {after['stats']['unconnected_items']}.",
            after["stats"],
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = run_drc(REPORTS / "DRC_PASS30BA_MID.json")
    mst = mid["stats"]
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    drop_nongnd = sum(bst["nongnd"].get(k, 0) - mst["nongnd"].get(k, 0) for k in set(bst["nongnd"]) | set(mst["nongnd"]))
    # count nets that dropped; the gate wants a non-GND open count to drop by >= 1 and P0.19 specifically
    pdrop = bst["p019_unconnected"] - mst["p019_unconnected"]
    gate_ok = (
        pdrop >= 1
        and not g
        and mst["shorting_items"] == 0
        and mst["clearance"] == 0
        and mst["tracks_crossing"] == 0
        and mst["hole_clearance"] == 0
        and mst["hole_to_hole"] == bst["hole_to_hole"]
        and measure["meets_foreign_0_15"]
        and measure["meets_power_0_20"]
    )
    if not gate_ok:
        restore()
        after = run_drc(REPORTS / "DRC_PASS30BA_AFTER.json")
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
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.19 opens {bst['p019_unconnected']}→{mst['p019_unconnected']} (need drop ≥ 1). "
            f"Non-GND open delta sum {drop_nongnd}. Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Post-revert DRC matches pre-edit: {match} "
            f"(unc {ast['unconnected_items']}, P0.19 {ast['p019_unconnected']}, "
            f"short/clearance/crossing/hole "
            f"{ast['shorting_items']}/{ast['clearance']}/{ast['tracks_crossing']}/{ast['hole_clearance']}, "
            f"hole_to_hole {ast['hole_to_hole']}, GND islands {ast['gnd_zone_islands']}). No second path."
        )
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30BA_MID.json", REPORTS / "DRC_PASS30BA_AFTER.json")
    reason = (
        f"KEEP. In1 east offset, {len(POLY) - 1} new segments, no new via. "
        f"P0.19 opens {bst['p019_unconnected']}→{mst['p019_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {measure['min_clearance_mm']} mm vs {measure['min_clearance_item']}. "
        f"POWER {measure['min_power_vin_mm']} mm vs {measure['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Locked skirts not ripped. P0.17 not retried."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
