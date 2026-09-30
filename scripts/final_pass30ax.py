#!/usr/bin/env python3
"""pass30ax — ONE attempt: P0.16 only.

The existing F.Cu stub (41.25, 26.75)–(40.70, 20.80) and via (40.70, 20.80)
already leave the SiP on the north side. The straight chord crosses the body
and the GND via at (42.0, 32.0). F.Cu and B.Cu free space around that via is
walled by the east fanout and the VDD2 / VDD_GPIO trunks, so it never meets
J18.4. One new via cannot bridge that gap.

In1.Cu is clear of those same-layer trunks (through-vias and PTH pads still
block). Six 0.18 mm In1 segments leave the existing via, pass east of the
VDD2 via (44.722, 25.900), and run down x=44.60 (east of the fab body) into
J18.4. No new via. No locked copper ripped.

KEEP only if P0.16 opens drop by at least 1, no other non-GND net gains an
open, short/clearance/crossing/hole are 0, foreign >= 0.15, POWER >= 0.20,
and hole_to_hole does not rise. Extra GND islands are waived. Otherwise full
revert. No second path. No P0.17.
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
BACKUP = ROOT / ".mcp-backups/pass30ax/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
IN1 = pcbnew.In1_Cu
W = 0.18
HW = W / 2
CF = 0.15
CP = 0.20
HOLE = 0.25
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
# East skirt on In1, off the fab body. Existing via is the start. J18.4 is the end.
POLY = [
    (40.70, 20.80),
    (45.55, 20.80),
    (45.55, 27.40),
    (44.60, 27.40),
    (44.60, 60.40),
    (45.62, 60.40),
    (45.62, 61.10),
]
STRAIGHT_A = (41.364, 27.150)
STRAIGHT_B = (45.537, 61.154)


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


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
        t
        for t in board.GetTracks()
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
    tmp = Path("/tmp/nrf30ax_drc.json")
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
        "p016_unconnected": nongnd_counts(data).get("P0.16", 0),
        "nongnd": dict(nongnd_counts(data)),
    }
    return {"stats": stats, "data": data}


def protect_ok(board) -> dict:
    vdd = [
        (40.170, 19.126),
        (40.170, 20.200),
        (45.900, 20.200),
        (45.900, 25.400),
        (47.550, 25.400),
        (47.550, 31.500),
        (44.000, 31.500),
    ]
    y7050 = [(71.300, 8.000), (71.300, 7.050), (77.300, 7.050), (81.500, 13.500), (86.510, 26.000)]
    ap = [
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
    p031 = [
        (102.60, 75.50),
        (103.05, 47.10),
        (106.70, 47.10),
        (106.70, 50.62),
        (114.90, 50.62),
        (114.90, 48.80),
        (115.55, 48.80),
    ]
    return {
        "stub": any(
            t.GetNetname() == "P0.16"
            and t.GetLayer() == F
            and track_is(t, 41.25, 26.75, 40.70, 20.80)
            for t in board.GetTracks()
        ),
        "stub_via": via_at(board, "P0.16", 40.70, 20.80),
        "u1_12": poly_ok(board, vdd, "VDD_GPIO", F),
        "y7050": poly_ok(board, y7050, "VDD_GPIO", F),
        "ap_run": poly_ok(board, ap, "VDD_GPIO", F),
        "ap_via": via_at(board, "VDD_GPIO", 76.4375, 39.050),
        "p030_via": via_at(board, "P0.30", 112.40, 46.40),
        "p031": poly_ok(board, p031, "P0.31", F),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "p013_via": via_at(board, "P0.13", 42.75, 23.1),
        "p015_via": via_at(board, "P0.15", 41.75, 23.1),
        "no_p014_via": not via_at(board, "P0.14", 42.25, 25.50),
        "dec0": any(
            t.GetNetname() == "DEC0"
            and t.GetLayer() == B
            and track_is(t, 46.950, 30.900, 48.100, 30.900)
            for t in board.GetTracks()
        ),
        "p015_tracks": sum(1 for t in board.GetTracks() if t.GetNetname() == "P0.15" and t.GetClass() != "PCB_VIA"),
        "p016_in1": sum(
            1
            for t in board.GetTracks()
            if t.GetNetname() == "P0.16" and t.GetClass() != "PCB_VIA" and t.GetLayer() == IN1
        ),
    }


def collect(board, layer, skip_net="P0.16"):
    vias = []
    holes = []
    pads = []
    tracks = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == skip_net:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            vias.append((x, y, mm(t.GetWidth(layer)) / 2, net, net in POWER))
            holes.append((x, y, mm(t.GetDrill()) / 2, f"via {net} @{x:.3f},{y:.3f}"))
        elif t.GetLayer() == layer:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            tracks.append((x1, y1, x2, y2, mm(t.GetWidth()) / 2, net, net in POWER))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == skip_net or not p.IsOnLayer(layer):
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            pads.append((p, f"{fp.GetReference()}.{p.GetNumber()}", net, net in POWER, x, y))
            if p.GetDrillSize().x:
                holes.append((x, y, mm(p.GetDrillSize().x) / 2, f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]"))
    return vias, holes, pads, tracks


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
    return False


def seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks):
    if body_hit(x1, y1, x2, y2):
        return {"ok": False, "why": "body_or_keepout"}
    worst = None
    pwr = None
    hh = None

    def eat(clr, net, desc, isp=False, hole=False):
        nonlocal worst, pwr, hh
        rec = (clr, net, desc)
        if hole:
            if hh is None or clr < hh[0]:
                hh = (clr, desc)
            return
        if worst is None or clr < worst[0]:
            worst = rec
        if isp and (pwr is None or clr < pwr[0]):
            pwr = rec

    for x, y, r, net, isp in vias:
        if x < min(x1, x2) - 3 or x > max(x1, x2) + 3 or y < min(y1, y2) - 3 or y > max(y1, y2) + 3:
            continue
        eat(dps(x, y, x1, y1, x2, y2) - r - HW, net, f"via@{x:.3f},{y:.3f}", isp)
    for x1t, y1t, x2t, y2t, ohw, net, isp in tracks:
        if max(x1t, x2t) < min(x1, x2) - 3 or min(x1t, x2t) > max(x1, x2) + 3:
            continue
        if max(y1t, y2t) < min(y1, y2) - 3 or min(y1t, y2t) > max(y1, y2) + 3:
            continue
        dist = min(
            dps(x1, y1, x1t, y1t, x2t, y2t),
            dps(x2, y2, x1t, y1t, x2t, y2t),
            dps(x1t, y1t, x1, y1, x2, y2),
            dps(x2t, y2t, x1, y1, x2, y2),
        )
        eat(dist - ohw - HW, net, f"trk ({x1t:.2f},{y1t:.2f})-({x2t:.2f},{y2t:.2f})", isp)
    for x, y, r, name in holes:
        if "J18.4" in name or "J13.1" in name:
            continue
        if x < min(x1, x2) - 3 or x > max(x1, x2) + 3 or y < min(y1, y2) - 3 or y > max(y1, y2) + 3:
            continue
        eat(dps(x, y, x1, y1, x2, y2) - r - HW, "HOLE", name, hole=True)
    sh = pcbnew.SHAPE_SEGMENT(xy(x1, y1), xy(x2, y2), pcbnew.FromMM(W))
    for p, name, net, isp, x, y in pads:
        if x < min(x1, x2) - 4 or x > max(x1, x2) + 4 or y < min(y1, y2) - 4 or y > max(y1, y2) + 4:
            continue
        eat(mm(sh.GetClearance(p.GetEffectiveShape(IN1))), net, f"pad {name}", isp)
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
    }


def measure_poly(board) -> dict:
    vias, holes, pads, tracks = collect(board, IN1)
    rows = []
    mf = mp = mh = None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
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
                if p.GetNumber() == "4":
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
        "lands_on_j18_4": hits_pad,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= HOLE - 1e-9,
        "ok": ok,
        "side": "east",
        "layer": "In1.Cu",
        "new_via": None,
    }


def straight_hits(board) -> dict:
    ax, ay = STRAIGHT_A
    bx, by = STRAIGHT_B
    sh = pcbnew.SHAPE_SEGMENT(xy(ax, ay), xy(bx, by), pcbnew.FromMM(W))
    hits = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.16":
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if not (30 < x < 60 and 20 < y < 70):
                continue
            clr = dps(x, y, ax, ay, bx, by) - mm(t.GetWidth(F)) / 2 - HW
            if clr < CF:
                hits.append({"clearance_mm": round(clr, 3), "net": net, "item": f"via@{x:.3f},{y:.3f}"})
        elif t.GetLayer() == F:
            other = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
            c = mm(sh.GetClearance(other))
            if c < CF:
                hits.append(
                    {
                        "clearance_mm": round(c, 3),
                        "net": net,
                        "item": (
                            f"F.Cu ({mm(t.GetStart().x):.2f},{mm(t.GetStart().y):.2f})"
                            f"-({mm(t.GetEnd().x):.2f},{mm(t.GetEnd().y):.2f})"
                        ),
                    }
                )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(F) or p.GetNetname() == "P0.16":
                continue
            c = mm(sh.GetClearance(p.GetEffectiveShape(F)))
            if c < CF:
                hits.append(
                    {
                        "clearance_mm": round(c, 3),
                        "net": p.GetNetname() or "<no-net>",
                        "item": f"pad {fp.GetReference()}.{p.GetNumber()}",
                    }
                )
    hits.sort(key=lambda h: h["clearance_mm"])
    worst = {}
    for h in hits:
        worst.setdefault(h["net"], h)
    return {
        "from": list(STRAIGHT_A),
        "to": list(STRAIGHT_B),
        "length_mm": round(math.hypot(bx - ax, by - ay), 3),
        "crosses_sip_body": True,
        "hit_count_under_0_15": len(hits),
        "nets_under_0_15": sorted(worst),
        "worst_by_net": worst,
    }


def pad_gap(board) -> dict:
    u = j = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "U1":
            for p in fp.Pads():
                if p.GetNumber() == "26":
                    u = p
        if fp.GetReference() == "J18":
            for p in fp.Pads():
                if p.GetNumber() == "4":
                    j = p
    gap = mm(u.GetEffectiveShape(F).GetClearance(j.GetEffectiveShape(F)))
    return {
        "u1_26": [round(mm(u.GetPosition().x), 3), round(mm(u.GetPosition().y), 3)],
        "j18_4": [round(mm(j.GetPosition().x), 3), round(mm(j.GetPosition().y), 3)],
        "pad_edge_mm": round(gap, 3),
        "other_island": "J18.4 + J13.1 on B.Cu (45.620,74.000)-(45.620,62.000) and (64.000,76.000)",
    }


def layer_reach(board, layer, tracks_too: bool):
    """Free-space bbox from the existing via. Zones ignored (refill pulls them back)."""
    HW_ = HW
    BUCKET = 2.0
    buck = defaultdict(list)
    hb = defaultdict(list)
    pb = defaultdict(list)

    def add(store, item, x0, y0, x1, y1):
        for ix in range(int(math.floor(min(x0, x1) / BUCKET)), int(math.floor(max(x0, x1) / BUCKET)) + 1):
            for iy in range(int(math.floor(min(y0, y1) / BUCKET)), int(math.floor(max(y0, y1) / BUCKET)) + 1):
                store[(ix, iy)].append(item)

    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.16":
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if not (15 <= x <= 80 and 8 <= y <= 80):
                continue
            r = mm(t.GetWidth(layer)) / 2
            req = CP if net in POWER else CF
            rad = r + HW_ + req
            add(buck, ("c", x, y, r, req), x - rad, y - rad, x + rad, y + rad)
            hr = mm(t.GetDrill()) / 2
            rad = hr + HW_ + HOLE
            add(hb, (x, y, hr), x - rad, y - rad, x + rad, y + rad)
        elif tracks_too and t.GetLayer() == layer:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            hw = mm(t.GetWidth()) / 2
            req = CP if net in POWER else CF
            rad = hw + HW_ + req
            add(buck, ("t", x1, y1, x2, y2, hw, req), min(x1, x2) - rad, min(y1, y2) - rad, max(x1, x2) + rad, max(y1, y2) + rad)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == "P0.16":
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            if not (15 <= x <= 80 and 8 <= y <= 80):
                continue
            if p.GetDrillSize().x:
                hr = mm(p.GetDrillSize().x) / 2
                rad = hr + HW_ + HOLE
                add(hb, (x, y, hr), x - rad, y - rad, x + rad, y + rad)
            if not p.IsOnLayer(layer):
                continue
            sx, sy = mm(p.GetSize().x), mm(p.GetSize().y)
            inf = HW_ + (CP if net in POWER else CF)
            hx, hy = sx / 2 + inf, sy / 2 + inf
            add(pb, (x, y, hx, hy, abs(sx - sy) < 1e-6), x - hx, y - hy, x + hx, y + hy)

    def ok(x, y):
        if x - HW_ <= 24.2:
            return False
        if BODY[0] - HW_ <= x <= BODY[2] + HW_ and BODY[1] - HW_ <= y <= BODY[3] + HW_:
            return False
        ix, iy = int(math.floor(x / BUCKET)), int(math.floor(y / BUCKET))
        for item in buck.get((ix, iy), ()):
            if item[0] == "c":
                _, cx, cy, r, req = item
                if (x - cx) ** 2 + (y - cy) ** 2 < (r + HW_ + req) ** 2:
                    return False
            else:
                _, x1, y1, x2, y2, hw, req = item
                if dps(x, y, x1, y1, x2, y2) < hw + HW_ + req:
                    return False
        for cx, cy, hr in hb.get((ix, iy), ()):
            if (x - cx) ** 2 + (y - cy) ** 2 < (hr + HW_ + HOLE) ** 2:
                return False
        for cx, cy, hx, hy, circ in pb.get((ix, iy), ()):
            dx, dy = abs(x - cx), abs(y - cy)
            if circ and dx * dx + dy * dy < hx * hx:
                return False
            if not circ and dx < hx and dy < hy:
                return False
        return True

    step = 0.25
    x0, x1, y0, y1 = 24.5, 72.0, 16.0, 63.0
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
            if leg[iy * nx + ix] and math.hypot(x0 + ix * step - 40.70, y0 + iy * step - 20.80) <= 0.32:
                seen.add((ix, iy))
                q.append((ix, iy))
    goal = False
    while q:
        ix, iy = q.popleft()
        if math.hypot(x0 + ix * step - 45.62, y0 + iy * step - 62.0) <= 0.85:
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
        "reaches_j18": goal,
    }


def add_route(board):
    net = board.FindNet("P0.16")
    if net is None:
        raise SystemExit("P0.16 missing")
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
    keys = set(before) | set(after)
    for k in keys:
        if k == "P0.16":
            continue
        if after.get(k, 0) > before.get(k, 0):
            out[k] = [before.get(k, 0), after.get(k, 0)]
    return out


def restore():
    shutil.copy2(BACKUP, BOARD)


def write_outputs(decision, info, before, after, reason, measure):
    ts = ist_now()
    b = before
    a = after
    segs = [
        {"layer": "In1.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30ax",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.16",
        "side": "east" if placed else "none",
        "layer": "In1.Cu" if placed else None,
        "new_via": None,
        "reason": reason,
        "pad_edge_mm": info["gap"]["pad_edge_mm"],
        "straight_line_not_used": info["straight"],
        "outer_layer_block": info["reach"],
        "segments": segs if placed else [],
        "segment_count": len(segs) if placed else 0,
        "attempted_segments": segs,
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "min_power_clearance_mm": measure.get("min_power_vin_mm"),
        "min_hole_clearance_mm": measure.get("min_hole_mm"),
        "min_foreign_item": measure.get("min_clearance_item"),
        "min_power_item": measure.get("min_power_vin_item"),
        "p016_opens_before": b.get("p016_unconnected"),
        "p016_opens_after": a.get("p016_unconnected"),
        "unconnected_before": b.get("unconnected_items"),
        "unconnected_after": a.get("unconnected_items"),
        "gnd_islands_before": b.get("gnd_zone_islands"),
        "gnd_islands_after": a.get("gnd_zone_islands"),
        "before": {k: v for k, v in b.items() if k != "nongnd"},
        "after": {k: v for k, v in a.items() if k != "nongnd"},
        "board_sha256": sha(BOARD),
        "backup_sha256": sha(BACKUP),
    }
    (REPORTS / "PASS30AX_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    fr = measure.get("min_clearance_mm")
    pw = measure.get("min_power_vin_mm")
    st = info["straight"]["worst_by_net"]
    gnd = st.get("GND", {})
    lines = [
        "# PASS30AX_SUMMARY — P0.16",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.16",
        f"**Side of package:** {'east skirt on In1.Cu' if placed else 'none — copper not left on the board'}",
        "**New via:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 8)",
        f"**Min foreign clearance:** {fr} mm vs {measure.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {pw} mm vs {measure.get('min_power_vin_item')}",
        f"**Min hole clearance (pre-add):** {measure.get('min_hole_mm')} mm vs {measure.get('min_hole_item')}",
        f"**P0.16 opens:** {b.get('p016_unconnected')} → {a.get('p016_unconnected')}",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)",
        "",
        "## Remeasured gap",
        "",
        f"Pad-edge **{info['gap']['pad_edge_mm']} mm** on F.Cu, U1.26 {info['gap']['u1_26']} to J18.4 {info['gap']['j18_4']}. "
        f"Other island is J18.4 already tied on B.Cu to J13.1. The U1 island is the existing stub "
        f"F.Cu (41.25, 26.75)–(40.70, 20.80) plus via (40.70, 20.80). Stub not ripped.",
        "",
        "## Straight line (not used)",
        "",
        f"0.18 mm F.Cu chord {list(STRAIGHT_A)} → {list(STRAIGHT_B)} ({info['straight']['length_mm']} mm). "
        f"Crosses the SiP body. Worst hit GND {gnd.get('clearance_mm')} mm ({gnd.get('item')}). "
        f"Foreign nets under 0.15 mm: {', '.join(info['straight']['nets_under_0_15']) or 'none'} "
        f"({info['straight']['hit_count_under_0_15']} items).",
        "",
        "## Why not F.Cu or B.Cu",
        "",
        "Free space (0.18 mm centerline, foreign ≥ 0.15, POWER ≥ 0.20, hole ≥ 0.25, off the fab body, "
        "x > 24.2, GND pour ignored) from the existing via:",
        "",
        f"- F.Cu: {info['reach']['F']}",
        f"- B.Cu: {info['reach']['B']}",
        "",
        "Neither component reaches J18.4. The start pocket ends near y≈27 and the J18 component starts "
        "south of the fanout (y≈41). One via is a point, so it cannot join two components that do not overlap. "
        "The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 was not used. No west skirt.",
        "",
        "## Route" if placed else "## Attempt",
        "",
    ]
    if placed:
        lines.append("In1.Cu 0.18 mm, east of the body (long run x=44.60 > 44). No new via. Corners:")
        lines.append("")
        for s in segs:
            lines.append(f"- ({s['start'][0]:.2f}, {s['start'][1]:.2f}) → ({s['end'][0]:.2f}, {s['end'][1]:.2f})")
        lines.append("")
        lines.append(
            "The north run is y=20.80, above the fab body. The drop at x=45.55 clears VDD2 via "
            "(44.722, 25.900). The south run at x=44.60 clears P0.06 via (45.150, 36.000) by 0.21 mm "
            "and stays east of the body (copper edge x=44.51). End cap overlaps J18.4."
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
        "| | unconnected | P0.16 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {b.get('unconnected_items')} | {b.get('p016_unconnected')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} |",
        f"| after | {a.get('unconnected_items')} | {a.get('p016_unconnected')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |",
        "",
    ]
    (REPORTS / "PASS30AX_SUMMARY.md").write_text("\n".join(lines) + "\n")
    return ts


def patch_review(ts, decision, before, after, measure):
    text = REVIEW.read_text()
    if "**Pass delta (pass30ax):**" in text:
        return
    fr = measure.get("min_clearance_mm")
    pw = measure.get("min_power_vin_mm")
    b, a = before, after
    banner = (
        f"**Review date:** {ts} (Asia/Calcutta) — pass30ax P0.16 {decision} "
        f"({'6-seg In1.Cu east skirt, no new via' if decision == 'KEEP' else 'no copper left'}, "
        f"foreign {fr} mm, POWER {pw} mm; unc {b.get('unconnected_items')}→{a.get('unconnected_items')}; "
        f"P0.16 opens {b.get('p016_unconnected')}→{a.get('p016_unconnected')}; "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} waived). "
    )
    pre, sep, post = text.partition("**Review date:**")
    if sep:
        old_body = post.split("\n", 1)[0]
        rest = post.split("\n", 1)[1]
        text = pre + banner + "Prior: " + old_body.strip() + "\n" + rest
    if decision == "KEEP":
        delta = (
            f"**Pass delta (pass30ax):** P0.16 U1.26↔J18.4, **KEEP**. Straight line not used "
            f"(crosses the SiP; GND via (42.0, 32.0) at about -0.349 mm). F.Cu and B.Cu from the "
            f"existing via (40.70, 20.80) are walled north of the body, so the skirt is six 0.18 mm "
            f"In1.Cu segments east of the fab body: (40.70, 20.80)→(45.55, 20.80)→(45.55, 27.40)→"
            f"(44.60, 27.40)→(44.60, 60.40)→(45.62, 60.40)→(45.62, 61.10). No new via. "
            f"Pre-add foreign {fr} mm (P0.06 via), POWER {pw} mm (VDD2 via). "
            f"P0.16 opens {b.get('p016_unconnected')}→{a.get('p016_unconnected')}. "
            f"Unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"short/clearance/crossing/hole "
            f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
            f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
            f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
            f"Stub, P0.15, P0.19, P0.30, P0.31, P0.22, P0.04, VDD_GPIO, COEX0, Class C, DEC0, "
            f"P0.10/P0.12, Stage-A VDD2, SIM walls not ripped. No header or U1 move. "
            f"No y=44.60 pocket. x>24.2. No P0.17. No Gerbers. Details: `reports/PASS30AX_SUMMARY.md`.\n\n"
        )
    else:
        delta = (
            f"**Pass delta (pass30ax):** P0.16, **{decision}**. Pad-edge still "
            f"{measure.get('min_clearance_mm') and 'see summary'}. "
            f"Straight line not used. No copper left on the board. "
            f"Unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"P0.16 opens {b.get('p016_unconnected')}→{a.get('p016_unconnected')}. "
            f"No P0.17. No Gerbers. Details: `reports/PASS30AX_SUMMARY.md`.\n\n"
        )
    needle = "**Pass delta (pass30aw):**"
    if needle in text:
        text = text.replace(needle, delta + needle, 1)
    status = (
        f"**2026-09-30 pass30ax:** P0.16 **{decision}**. "
        f"Unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"P0.16 opens {b.get('p016_unconnected')}→{a.get('p016_unconnected')}. "
        f"See `reports/PASS30AX_SUMMARY.md`.\n\n"
    )
    anchor = "**2026-09-30 12:27 IST — pass30aw no-copper census.**"
    if anchor in text and "pass30ax:" not in text.split(anchor)[0][-400:]:
        text = text.replace(anchor, status + anchor, 1)
    if "| **unconnected_items** | **60** | live `GetUnconnectedCount` 60" in text and decision == "KEEP":
        text = text.replace(
            "| **unconnected_items** | **60** | live `GetUnconnectedCount` 60 and `reports/DRC_PASS30AS_AFTER.json`.",
            f"| **unconnected_items** | **{a.get('unconnected_items')}** | `reports/DRC_PASS30AX_AFTER.json`. "
            f"pass30ax KEEP: P0.16 opens {b.get('p016_unconnected')}→{a.get('p016_unconnected')}. "
            f"Prior live count was 60 (`DRC_PASS30AS_AFTER.json`).",
            1,
        )
    REVIEW.write_text(text)


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not BACKUP.is_file():
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup does not match the live board; refusing to edit")

    board = pcbnew.LoadBoard(str(BOARD))
    info = {
        "gap": pad_gap(board),
        "straight": straight_hits(board),
        "protect_before": protect_ok(board),
        "fp": footprint_xy(board),
    }
    print("GAP", info["gap"], flush=True)
    print("STRAIGHT", info["straight"]["worst_by_net"].get("GND"), "nets", info["straight"]["nets_under_0_15"], flush=True)
    print("REACH F", flush=True)
    info["reach"] = {
        "F": layer_reach(board, F, True),
        "B": layer_reach(board, B, True),
    }
    print("REACH", info["reach"], flush=True)
    measure = measure_poly(board)
    print("MEASURE", {k: measure[k] for k in measure if k != "segments"}, flush=True)

    before = run_drc(REPORTS / "DRC_PASS30AX_BEFORE.json")
    print("BEFORE", {k: v for k, v in before["stats"].items() if k != "nongnd"}, flush=True)
    bst = before["stats"]

    def stop(decision, reason, after_stats=None):
        if sha(BOARD) != sha(BACKUP):
            restore()
        ast = after_stats
        if ast is None:
            shutil.copy2(REPORTS / "DRC_PASS30AX_BEFORE.json", REPORTS / "DRC_PASS30AX_MID.json")
            shutil.copy2(REPORTS / "DRC_PASS30AX_BEFORE.json", REPORTS / "DRC_PASS30AX_AFTER.json")
            ast = bst
        else:
            # caller already wrote AFTER; mirror MID if missing
            if not (REPORTS / "DRC_PASS30AX_MID.json").is_file():
                shutil.copy2(REPORTS / "DRC_PASS30AX_AFTER.json", REPORTS / "DRC_PASS30AX_MID.json")
        if sha(BOARD) != sha(BACKUP):
            restore()
        ts = write_outputs(decision, info, bst, ast, reason, measure)
        patch_review(ts, decision, bst, ast, measure)
        print(decision, reason, flush=True)

    pb = info["protect_before"]
    need = (
        "stub",
        "stub_via",
        "u1_12",
        "y7050",
        "ap_run",
        "ap_via",
        "p030_via",
        "p031",
        "coex0_via",
        "p010",
        "p012",
        "p013_via",
        "p015_via",
        "no_p014_via",
        "dec0",
    )
    if not all(pb[k] for k in need):
        stop("NO-ROUTE", f"Locked copper missing before edit: {pb}. No copper added.")
        return
    if pb["p016_in1"] != 0:
        stop("NO-ROUTE", "P0.16 already has In1 tracks. No copper added.")
        return
    if not measure["ok"]:
        stop(
            "NO-ROUTE",
            f"In1 east skirt failed pre-add clearance or did not land on J18.4 "
            f"(foreign {measure['min_clearance_mm']}, POWER {measure['min_power_vin_mm']}, "
            f"hole {measure['min_hole_mm']}, land {measure['lands_on_j18_4']}). No copper added.",
        )
        return
    if min(p[0] for p in POLY) <= 24.2:
        stop("NO-ROUTE", "Route enters x<=24.2. No copper added.")
        return

    add_route(board)
    pa = protect_ok(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != footprint_xy(board).get(ref))
    info["protect_after_add"] = pa
    if moved or pa["p015_tracks"] != pb["p015_tracks"] or not pa["stub"] or not pa["stub_via"]:
        restore()
        stop("REVERT", f"Protect guard failed moved={moved} protect={pa}. Full restore.")
        return
    if not poly_ok(board, POLY, "P0.16", IN1):
        restore()
        stop("REVERT", "New segments did not land as drawn. Full restore.")
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = run_drc(REPORTS / "DRC_PASS30AX_MID.json")
    print("MID", {k: v for k, v in mid["stats"].items() if k != "nongnd"}, flush=True)
    mst = mid["stats"]
    g = gained(bst["nongnd"], mst["nongnd"])
    drop = bst["p016_unconnected"] - mst["p016_unconnected"]
    gate_ok = (
        drop >= 1
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
        after = run_drc(REPORTS / "DRC_PASS30AX_AFTER.json")
        reason = (
            f"REVERT. P0.16 opens {bst['p016_unconnected']}→{mst['p016_unconnected']} "
            f"(need drop ≥ 1). Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. Full restore. No second path."
        )
        ts = write_outputs("REVERT", info, bst, after["stats"], reason, measure)
        patch_review(ts, "REVERT", bst, after["stats"], measure)
        print("REVERT", reason, flush=True)
        return

    shutil.copy2(REPORTS / "DRC_PASS30AX_MID.json", REPORTS / "DRC_PASS30AX_AFTER.json")
    reason = (
        f"KEEP. East In1 skirt, 6 new segments, no new via. "
        f"P0.16 opens {bst['p016_unconnected']}→{mst['p016_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {measure['min_clearance_mm']} mm, POWER {measure['min_power_vin_mm']} mm. "
        f"short/clearance/crossing/hole 0. hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none."
    )
    ts = write_outputs("KEEP", info, bst, mst, reason, measure)
    patch_review(ts, "KEEP", bst, mst, measure)
    print("KEEP", reason, flush=True)


if __name__ == "__main__":
    main()
