#!/usr/bin/env python3
"""pass30ay — ONE attempt: P0.17 only.

Existing north exit: F.Cu stub (40.25, 26.75)–(40.25, 23.10) and through-via
(40.25, 23.10), drill 0.30 / pad 0.60, already on F.Cu, In1.Cu, In2.Cu, B.Cu.
The via at (40.25, 23.95) stays. No new via. No fanout via moved.

F.Cu and B.Cu free space from that via die at y=26.5 (same wall as P0.16).
The straight 0.18 mm F.Cu chord is not used: it crosses the SiP and hits
GND via (42.0, 35.0).

In1.Cu reaches in the flood fill, but the locked pass30ax skirt owns the
east corridor (x=44.60 and the x=45.55 north jog). Same-layer clearance to
that 0.18 mm copper is 0.33 mm center-to-center, and the P0.06 via
(45.150, 36.000) closes the gap beside it. The one path is therefore In2.Cu,
which has no tracks in this corridor. Seven 0.18 mm segments leave the
existing via, pass east of the body, and land on J18.5. In2 is a VDD_nRF
plane (zone clearance 0.5 mm); refill must keep foreign >= 0.15, POWER >= 0.20,
and must not give any other non-GND net a new open. Else full revert.
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
BACKUP = ROOT / ".mcp-backups/pass30ay/pre-edit.kicad_pcb"
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
# In2.Cu east skirt. Start is the existing through-via. End overlaps J18.5.
POLY = [
    (40.25, 23.10),
    (40.25, 21.50),
    (45.55, 21.50),
    (45.55, 27.40),
    (44.60, 27.40),
    (44.60, 60.40),
    (48.16, 60.40),
    (48.16, 61.30),
]
P16 = [
    (40.70, 20.80),
    (45.55, 20.80),
    (45.55, 27.40),
    (44.60, 27.40),
    (44.60, 60.40),
    (45.62, 60.40),
    (45.62, 61.10),
]
STRAIGHT_A = (40.378, 27.147)
STRAIGHT_B = (47.913, 61.187)
VIA_X, VIA_Y = 40.25, 23.10
GOAL_X, GOAL_Y = 48.16, 62.0


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


def track_counts(board) -> dict:
    c = Counter()
    v = Counter()
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
    tmp = Path("/tmp/nrf30ay_drc.json")
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
        "p017_unconnected": nongnd_counts(data).get("P0.17", 0),
        "nongnd": dict(nongnd_counts(data)),
    }
    return {"stats": stats, "data": data}


def protect_ok(board) -> dict:
    return {
        "stub": any(
            t.GetNetname() == "P0.17"
            and t.GetLayer() == F
            and track_is(t, 40.25, 26.75, 40.25, 23.10)
            for t in board.GetTracks()
        ),
        "stub_south": any(
            t.GetNetname() == "P0.17"
            and t.GetLayer() == F
            and track_is(t, 40.25, 26.75, 40.25, 23.95)
            for t in board.GetTracks()
        ),
        "via_2310": via_at(board, "P0.17", 40.25, 23.10),
        "via_2395": via_at(board, "P0.17", 40.25, 23.95),
        "p016_in1": poly_ok(board, P16, "P0.16", IN1),
        "p016_via": via_at(board, "P0.16", 40.70, 20.80),
        "p015_via": via_at(board, "P0.15", 41.75, 23.10),
        "p019_via": via_at(board, "P0.19", 39.25, 23.10),
        "p030_via": via_at(board, "P0.30", 112.40, 46.40),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "dec0": any(
            t.GetNetname() == "DEC0"
            and t.GetLayer() == B
            and track_is(t, 46.950, 30.900, 48.100, 30.900)
            for t in board.GetTracks()
        ),
    }


def collect(board, layer, skip_net="P0.17"):
    vias, holes, pads, tracks = [], [], [], []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == skip_net:
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            vias.append((x, y, mm(t.GetWidth(layer)) / 2, net, net in POWER))
            holes.append((x, y, mm(t.GetDrillValue()) / 2, f"via {net} @{x:.3f},{y:.3f}"))
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
                holes.append(
                    (x, y, mm(p.GetDrillSize().x) / 2, f"hole {fp.GetReference()}.{p.GetNumber()} [{net}]")
                )
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
        # sealed B.Cu pocket is not on this route; keep the test anyway
        if 81.8 <= x <= 97.3 and abs(y - 44.60) <= (HW + 0.15):
            return True
    return False


def seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, layer):
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
        if "J18.5" in name:
            continue
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
    vias, holes, pads, tracks = collect(board, IN2)
    rows = []
    mf = mp = mh = None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        row = seg_clearance(x1, y1, x2, y2, vias, holes, pads, tracks, IN2)
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
                if p.GetNumber() == "5":
                    j = p
    land = pcbnew.SHAPE_SEGMENT(xy(*POLY[-2]), xy(*POLY[-1]), pcbnew.FromMM(W))
    hits_pad = bool(j and land.Collide(j.GetEffectiveShape(IN2)))
    ok = all(r["ok"] for r in rows) and hits_pad and len(POLY) - 1 <= 8
    return {
        "segments": rows,
        "segment_count": len(POLY) - 1,
        "in2_foreign_tracks": len(tracks),
        "min_clearance_mm": None if mf is None else mf[0],
        "min_clearance_item": None if mf is None else mf[1],
        "min_power_vin_mm": None if mp is None else mp[0],
        "min_power_vin_item": None if mp is None else mp[1],
        "min_hole_mm": None if mh is None else mh[0],
        "min_hole_item": None if mh is None else mh[1],
        "lands_on_j18_5": hits_pad,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "meets_hole_0_25": mh is None or mh[0] >= HOLE - 1e-9,
        "ok": ok,
        "layer": "In2.Cu",
        "new_via": None,
    }


def straight_hits(board) -> dict:
    ax, ay = STRAIGHT_A
    bx, by = STRAIGHT_B
    sh = pcbnew.SHAPE_SEGMENT(xy(ax, ay), xy(bx, by), pcbnew.FromMM(W))
    hits = []
    gnd_via = None
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "P0.17":
            continue
        if t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if not (30 < x < 60 and 20 < y < 70):
                continue
            clr = dps(x, y, ax, ay, bx, by) - mm(t.GetWidth(F)) / 2 - HW
            if abs(x - 42.0) < 0.02 and abs(y - 35.0) < 0.02:
                gnd_via = {
                    "clearance_mm": round(clr, 3),
                    "net": net,
                    "item": f"via@{x:.3f},{y:.3f}",
                    "via_radius_mm": round(mm(t.GetWidth(F)) / 2, 3),
                }
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
            if not p.IsOnLayer(F) or p.GetNetname() == "P0.17":
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
        "gnd_via_42_35": gnd_via,
        "hit_count_under_0_15": len(hits),
        "nets_under_0_15": sorted(worst),
        "worst_by_net": worst,
    }


def pad_gap(board) -> dict:
    u = j = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "U1":
            for p in fp.Pads():
                if p.GetNumber() == "28":
                    u = p
        if fp.GetReference() == "J18":
            for p in fp.Pads():
                if p.GetNumber() == "5":
                    j = p
    gap = mm(u.GetEffectiveShape(F).GetClearance(j.GetEffectiveShape(F)))
    return {
        "u1_28": [round(mm(u.GetPosition().x), 3), round(mm(u.GetPosition().y), 3)],
        "j18_5": [round(mm(j.GetPosition().x), 3), round(mm(j.GetPosition().y), 3)],
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": round(gap, 6),
        "stated_chord_mm": round(math.hypot(STRAIGHT_B[0] - STRAIGHT_A[0], STRAIGHT_B[1] - STRAIGHT_A[1]), 3),
        "other_island": "J18.5 already on F.Cu and B.Cu (B.Cu run (48.16, 62.0)–(48.16, 73.4)–(66.54, 73.4)–(66.54, 76.0))",
    }


def layer_reach(board, layer, tracks_too: bool):
    """Free-space bbox from the existing via. Zones ignored (refill pulls them back)."""
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
        if net == "P0.17":
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
        elif tracks_too and t.GetLayer() == layer:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            hw = mm(t.GetWidth()) / 2
            req = CP if net in POWER else CF
            rad = hw + HW + req
            add(
                buck,
                ("t", x1, y1, x2, y2, hw, req),
                min(x1, x2) - rad,
                min(y1, y2) - rad,
                max(x1, x2) + rad,
                max(y1, y2) + rad,
            )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net == "P0.17":
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
            if not circ and dx < hx and dy < hy:
                return False
        return True

    step = 0.25
    x0, x1, y0, y1 = 24.5, 72.0, 16.0, 64.0
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
            if leg[iy * nx + ix] and math.hypot(x0 + ix * step - VIA_X, y0 + iy * step - VIA_Y) <= 0.35:
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
        "reaches_j18": goal,
    }


def via_layers(board) -> dict:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.17":
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


def add_route(board):
    net = board.FindNet("P0.17")
    if net is None:
        raise SystemExit("P0.17 missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(xy(x1, y1))
        tr.SetEnd(xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN2)
        tr.SetNet(net)
        board.Add(tr)


def gained(before: dict, after: dict) -> dict:
    out = {}
    keys = set(before) | set(after)
    for k in keys:
        if k == "P0.17":
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
        {"layer": "In2.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    placed = decision == "KEEP"
    payload = {
        "pass": "30ay",
        "timestamp": ts,
        "decision": decision,
        "net": "P0.17",
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "side": "east" if placed else "none",
        "layer": "In2.Cu" if placed else None,
        "new_via": None,
        "reason": reason,
        "pad_edge_mm": info["gap"]["pad_edge_mm"],
        "pad_edge_exact_mm": info["gap"]["pad_edge_exact_mm"],
        "straight_line_not_used": info["straight"],
        "layers_checked": info["reach"],
        "via": info.get("via"),
        "segments": segs if placed else [],
        "segment_count": len(segs) if placed else 0,
        "attempted_segments": segs,
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "min_power_clearance_mm": measure.get("min_power_vin_mm"),
        "min_hole_clearance_mm": measure.get("min_hole_mm"),
        "min_foreign_item": measure.get("min_clearance_item"),
        "min_power_item": measure.get("min_power_vin_item"),
        "min_hole_item": measure.get("min_hole_item"),
        "p017_opens_before": b.get("p017_unconnected"),
        "p017_opens_after": a.get("p017_unconnected"),
        "unconnected_before": b.get("unconnected_items"),
        "unconnected_after": a.get("unconnected_items"),
        "gnd_islands_before": b.get("gnd_zone_islands"),
        "gnd_islands_after": a.get("gnd_zone_islands"),
        "other_nongnd_gained": info.get("gained", {}),
        "before": {k: v for k, v in b.items() if k != "nongnd"},
        "after": {k: v for k, v in a.items() if k != "nongnd"},
        "board_sha256": sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "backup_sha256": sha(BACKUP) if BACKUP.is_file() else None,
        "locked_copper_ripped": False,
        "gerbers": False,
        "commit": False,
    }
    (REPORTS / "PASS30AY_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    fr = measure.get("min_clearance_mm")
    pw = measure.get("min_power_vin_mm")
    gnd = (info["straight"].get("gnd_via_42_35") or {})
    lines = [
        "# PASS30AY_SUMMARY — P0.17",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.17",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**Side of package:** {'east skirt on In2.Cu' if placed else 'none — copper not left on the board'}",
        "**New via:** no",
        f"**New segments:** {len(segs) if placed else 0} (limit 8)",
        f"**Min foreign clearance:** {fr} mm vs {measure.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {pw} mm vs {measure.get('min_power_vin_item')}",
        f"**Min hole clearance (pre-add):** {measure.get('min_hole_mm')} mm vs {measure.get('min_hole_item')}",
        f"**P0.17 opens:** {b.get('p017_unconnected')} → {a.get('p017_unconnected')}",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)",
        f"**Backup:** `{BACKUP}`",
        "",
        "## Remeasured gap",
        "",
        f"Pad-edge **{info['gap']['pad_edge_exact_mm']} mm** (reported {info['gap']['pad_edge_mm']} mm) "
        f"on F.Cu effective shapes, U1.28 {info['gap']['u1_28']} to J18.5 {info['gap']['j18_5']}. "
        f"The stated copper points {(list(STRAIGHT_A))} → {(list(STRAIGHT_B))} are {info['gap']['stated_chord_mm']} mm apart "
        f"(J18.5 center is (48.16, 62.0); (47.913, 61.187) is on the pad edge). "
        f"Other island is J18.5, already on F.Cu and B.Cu. "
        f"U1 island is the existing stub F.Cu (40.25, 26.75)–(40.25, 23.10) plus through-via (40.25, 23.10). "
        f"The second via (40.25, 23.95) was not ripped. Stub not ripped.",
        "",
        "## Straight line (not used)",
        "",
        f"0.18 mm F.Cu chord {list(STRAIGHT_A)} → {list(STRAIGHT_B)} ({info['straight']['length_mm']} mm). "
        f"Crosses the SiP body. GND via (42.0, 35.0) clearance **{gnd.get('clearance_mm')} mm** "
        f"({gnd.get('item')}, pad radius {gnd.get('via_radius_mm')} mm). "
        f"Foreign nets under 0.15 mm: {', '.join(info['straight']['nets_under_0_15']) or 'none'} "
        f"({info['straight']['hit_count_under_0_15']} items). Not used.",
        "",
        "## Layers checked",
        "",
        f"Existing via (40.25, 23.10) drill {info.get('via', {}).get('drill_mm')} mm, "
        f"pad {info.get('via', {}).get('pad_mm')} mm, {info.get('via', {}).get('top')} to {info.get('via', {}).get('bottom')}. "
        f"On layers: {info.get('via', {}).get('on')}. It is a through via, so the new copper starts on a layer it already hits. "
        f"No second via.",
        "",
        "Free space (0.18 mm centerline, foreign ≥ 0.15, POWER ≥ 0.20, hole ≥ 0.25, off the fab body, "
        "x > 24.2, zones ignored because refill pulls them back) from that via:",
        "",
        f"- F.Cu: {info['reach'].get('F')}",
        f"- B.Cu: {info['reach'].get('B')}",
        f"- In1.Cu: {info['reach'].get('In1')}",
        f"- In2.Cu: {info['reach'].get('In2')}",
        "",
        "F.Cu and B.Cu both die at ymax 26.5, short of the header, same as the P0.16 via. "
        "One extra via cannot join a pocket that ends near y≈27 to J18.5. "
        "In1.Cu flood-fill does reach J18.5, but the locked pass30ax skirt "
        "(40.70, 20.80)→(45.55, 20.80)→(45.55, 27.40)→(44.60, 27.40)→(44.60, 60.40)→(45.62, 60.40)→(45.62, 61.10) "
        "owns that east corridor. Same-layer 0.18 mm centerlines need ≥ 0.33 mm. "
        "The P0.06 via (45.150, 36.000) closes the strip beside x=44.60, so this attempt does not run on In1. "
        "In2.Cu has no tracks in the corridor and the through-via already hits it. "
        "In2 is the VDD_nRF plane (zone local clearance 0.5 mm). "
        "The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 was not used. x > 24.2. No west skirt.",
        "",
        "## Route" if placed else "## Attempt",
        "",
    ]
    if placed:
        lines.append("In2.Cu 0.18 mm, east of the body (long run x=44.60). No new via. Corners:")
        lines.append("")
        for s in segs:
            lines.append(f"- ({s['start'][0]:.2f}, {s['start'][1]:.2f}) → ({s['end'][0]:.2f}, {s['end'][1]:.2f})")
        lines.append("")
        lines.append(
            "North of the fab body at y=21.50, drop at x=45.55 (clears VDD2 via (44.722, 25.900)), "
            "then x=44.60 from y=27.40 to y=60.40 (clears P0.06 via (45.150, 36.000) by 0.21 mm; "
            "copper edge x=44.51, fab body ends at x=44.0). End cap (48.16, 60.40)–(48.16, 61.30) overlaps J18.5. "
            "P0.16's matching XY on In1.Cu is a different layer, so the 0.33 mm same-layer rule does not apply. "
            "That In1 copper was not ripped."
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
        "| | unconnected | P0.17 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {b.get('unconnected_items')} | {b.get('p017_unconnected')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} |",
        f"| after | {a.get('unconnected_items')} | {a.get('p017_unconnected')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |",
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}.",
        "Locked copper not ripped. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30AY_SUMMARY.md").write_text("\n".join(lines) + "\n")
    return ts


def patch_review(ts, decision, before, after, measure):
    text = REVIEW.read_text()
    if "## Pass30ay —" in text:
        return
    b, a = before, after
    fr = measure.get("min_clearance_mm")
    pw = measure.get("min_power_vin_mm")
    if decision == "KEEP":
        route = (
            "In2.Cu 0.18 mm, no new via: (40.25, 23.10)→(40.25, 21.50)→(45.55, 21.50)→"
            "(45.55, 27.40)→(44.60, 27.40)→(44.60, 60.40)→(48.16, 60.40)→(48.16, 61.30)."
        )
    else:
        route = "No copper left on the board."
    note = (
        f"\n## Pass30ay — P0.17 north-exit jog — {ts}\n\n"
        f"**Decision:** **{decision}**. {route}\n\n"
        f"Pad-edge U1.28↔J18.5 **{measure.get('min_clearance_mm') and ''}**"
        f"see summary. Foreign {fr} mm ({measure.get('min_clearance_item')}). "
        f"POWER {pw} mm ({measure.get('min_power_vin_item')}). "
        f"Straight F.Cu chord not used (GND via (42.0, 35.0)). "
        f"F.Cu/B.Cu free space dies at y=26.5.\n\n"
        f"**P0.17 opens:** {b.get('p017_unconnected')} → {a.get('p017_unconnected')}. "
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}. "
        f"**short/clearance/crossing/hole:** {a.get('shorting_items')}/{a.get('clearance')}/"
        f"{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"**hole_to_hole:** {b.get('hole_to_hole')} → {a.get('hole_to_hole')}. "
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived).\n\n"
        f"**Artifacts:** `reports/PASS30AY_SUMMARY.{{md,json}}`, "
        f"`reports/DRC_PASS30AY_{{BEFORE,MID,AFTER}}.json`, `scripts/final_pass30ay.py`\n"
    )
    # The pad-edge phrase above is awkward if I leave the empty conditional. Rewrite cleanly.
    gap = None
    note = (
        f"\n## Pass30ay — P0.17 north-exit jog — {ts}\n\n"
        f"**Decision:** **{decision}**. {route}\n\n"
        f"Remeasured pad-edge U1.28↔J18.5 is in `reports/PASS30AY_SUMMARY.md`. "
        f"Foreign {fr} mm vs {measure.get('min_clearance_item')}. "
        f"POWER {pw} mm vs {measure.get('min_power_vin_item')}. "
        f"Straight 0.18 mm F.Cu chord (40.378, 27.147)→(47.913, 61.187) not used "
        f"(crosses the SiP; GND via (42.0, 35.0)). "
        f"F.Cu and B.Cu free space from via (40.25, 23.10) die at y=26.5. "
        f"Existing through-via kept. No second via. Locked P0.16 In1 skirt not ripped. "
        f"x>24.2. No header or U1 move. No Gerbers. No commit.\n\n"
        f"**P0.17 opens:** {b.get('p017_unconnected')} → {a.get('p017_unconnected')}. "
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}. "
        f"**short/clearance/crossing/hole:** {a.get('shorting_items')}/{a.get('clearance')}/"
        f"{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"**hole_to_hole:** {b.get('hole_to_hole')} → {a.get('hole_to_hole')}. "
        f"**GND islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived).\n\n"
        f"**Artifacts:** `reports/PASS30AY_SUMMARY.md`, `reports/PASS30AY_SUMMARY.json`, "
        f"`reports/DRC_PASS30AY_BEFORE.json`, `reports/DRC_PASS30AY_MID.json`, "
        f"`reports/DRC_PASS30AY_AFTER.json`, `scripts/final_pass30ay.py`\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    REVIEW.write_text(text + note)


def counts_locked(before_counts, board) -> list:
    after = track_counts(board)
    bad = []
    for net, n in before_counts["tracks"].items():
        if net == "P0.17":
            continue
        if after["tracks"].get(net, 0) != n:
            bad.append(f"track {net} {n}->{after['tracks'].get(net, 0)}")
    for net, n in before_counts["vias"].items():
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get("P0.17", 0) != before_counts["vias"].get("P0.17", 0):
        bad.append("P0.17 via count changed")
    return bad


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    info = {
        "git_head": git_head(),
        "pcb_blob": git_blob(),
    }
    print("GIT", info["git_head"], info["pcb_blob"], flush=True)

    before = run_drc(REPORTS / "DRC_PASS30AY_BEFORE.json")
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = pad_gap(board)
    info["straight"] = straight_hits(board)
    info["via"] = via_layers(board)
    info["protect_before"] = protect_ok(board)
    info["fp"] = footprint_xy(board)
    info["counts"] = track_counts(board)
    info["gained"] = {}
    print("GAP", info["gap"], flush=True)
    print("STRAIGHT_GND", info["straight"].get("gnd_via_42_35"), flush=True)
    print("VIA", info["via"], flush=True)
    info["reach"] = {
        "F": layer_reach(board, F, True),
        "B": layer_reach(board, B, True),
        "In1": layer_reach(board, IN1, True),
        "In2": layer_reach(board, IN2, True),
    }
    print("REACH", info["reach"], flush=True)
    measure = measure_poly(board)
    print("MEASURE", {k: measure[k] for k in measure if k != "segments"}, flush=True)

    def finish(decision, reason, after_stats):
        ts = write_outputs(decision, info, bst, after_stats, reason, measure)
        patch_review(ts, decision, bst, after_stats, measure)
        print(decision, reason, flush=True)

    if bst["unconnected_items"] != 59:
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_MID.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_AFTER.json")
        finish(
            "NO-ROUTE",
            f"Pre-edit unconnected is {bst['unconnected_items']}, not 59. No copper edited.",
            bst,
        )
        return

    pb = info["protect_before"]
    if not all(pb.values()):
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_MID.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {pb}. No copper added.", bst)
        return

    if not info["via"].get("on", {}).get("In2.Cu"):
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_MID.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_AFTER.json")
        finish("NO-ROUTE", f"Existing via does not hit In2.Cu: {info['via']}. No copper added.", bst)
        return

    if not measure["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_MID.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_AFTER.json")
        finish(
            "NO-ROUTE",
            f"In2 east skirt failed pre-add clearance or did not land on J18.5 "
            f"(foreign {measure['min_clearance_mm']}, POWER {measure['min_power_vin_mm']}, "
            f"hole {measure['min_hole_mm']}, land {measure['lands_on_j18_5']}). No copper added.",
            bst,
        )
        return

    if min(p[0] for p in POLY) <= 24.2:
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_MID.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_BEFORE.json", REPORTS / "DRC_PASS30AY_AFTER.json")
        finish("NO-ROUTE", "Route enters x<=24.2. No copper added.", bst)
        return

    shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup copy failed")

    add_route(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != footprint_xy(board).get(ref))
    ripped = counts_locked(info["counts"], board)
    pa = protect_ok(board)
    if moved or ripped or not all(pa.values()) or not poly_ok(board, POLY, "P0.17", IN2):
        restore()
        after = run_drc(REPORTS / "DRC_PASS30AY_AFTER.json")
        shutil.copy2(REPORTS / "DRC_PASS30AY_AFTER.json", REPORTS / "DRC_PASS30AY_MID.json")
        finish(
            "NO-ROUTE",
            f"Protect guard failed before refill. moved={moved} ripped={ripped} protect={pa}. "
            f"Full restore. Post-revert unconnected {after['stats']['unconnected_items']}.",
            after["stats"],
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(BOARD))
    mid = run_drc(REPORTS / "DRC_PASS30AY_MID.json")
    mst = mid["stats"]
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    drop = bst["p017_unconnected"] - mst["p017_unconnected"]
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
        after = run_drc(REPORTS / "DRC_PASS30AY_AFTER.json")
        ast = after["stats"]
        match = (
            ast["unconnected_items"] == bst["unconnected_items"]
            and ast["p017_unconnected"] == bst["p017_unconnected"]
            and ast["shorting_items"] == bst["shorting_items"]
            and ast["clearance"] == bst["clearance"]
            and ast["tracks_crossing"] == bst["tracks_crossing"]
            and ast["hole_clearance"] == bst["hole_clearance"]
            and ast["hole_to_hole"] == bst["hole_to_hole"]
        )
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.17 opens {bst['p017_unconnected']}→{mst['p017_unconnected']} (need drop ≥ 1). "
            f"Other non-GND gained: {g or 'none'}. "
            f"Mid short/clearance/crossing/hole "
            f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
            f"hole_to_hole {bst['hole_to_hole']}→{mst['hole_to_hole']}. "
            f"Post-revert DRC matches pre-edit: {match} "
            f"(unc {ast['unconnected_items']}, P0.17 {ast['p017_unconnected']}, "
            f"short/clearance/crossing/hole "
            f"{ast['shorting_items']}/{ast['clearance']}/{ast['tracks_crossing']}/{ast['hole_clearance']}, "
            f"hole_to_hole {ast['hole_to_hole']}). No second path."
        )
        # after counts are the restored board; also keep mid numbers in the reason
        finish("NO-ROUTE", reason, ast)
        return

    shutil.copy2(REPORTS / "DRC_PASS30AY_MID.json", REPORTS / "DRC_PASS30AY_AFTER.json")
    reason = (
        f"KEEP. East In2 skirt, {len(POLY) - 1} new segments, no new via. "
        f"P0.17 opens {bst['p017_unconnected']}→{mst['p017_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {measure['min_clearance_mm']} mm vs {measure['min_clearance_item']}. "
        f"POWER {measure['min_power_vin_mm']} mm vs {measure['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Locked copper not ripped."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
