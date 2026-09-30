#!/usr/bin/env python3
"""pass30bg — ONE attempt: P0.07 only.

Named through-via (47.40, 36.50) is P0.05, not the U1.4 island, so it is
not used. The existing P0.07 through-via is (47.40, 35.50), radius 0.30 mm,
already east of the fab body and east of the skirt slot. The route starts
there. J12.8 is a PTH pad (copper on F/B/In1/In2). No new via.

In2.Cu, 9 segments, south of the skirts (east of the y=63.20 eastbounds),
along the south edge at y=79.20 (south of the header row), then east into
J12.8. Straight F.Cu chord is not used (P0.02). Skirt slot, sealed pocket,
and the RF keepout box are not used. No stack on P0.00, SIM_RST, or SIM_CLK.
"""
from __future__ import annotations

import hashlib
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
spec2 = importlib.util.spec_from_file_location("p30be", ROOT / "scripts" / "final_pass30be.py")
be = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(be)

BOARD = m.BOARD
BACKUP = ROOT / ".mcp-backups/pass30bg/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
F, B, IN1, IN2 = m.F, m.B, m.IN1, m.IN2
W = m.W
CF = m.CF
CP = m.CP
LAYERS = m.LAYERS
NET = "P0.07"
be.NET = NET
EXPECTED_HEAD = "e851c3b"
EXPECTED_BLOB = "1689715203e755d4422b71fb29202c387b9c7889"
EXPECTED_UNC = 53

# Existing P0.07 through-via. The named (47.40, 36.50) via is P0.05.
START_VIA_NM = (47400000, 35500000)
NAMED_VIA_NM = (47400000, 36500000)
PAD_NM = (23780000, 76000000)

POLY = [
    (47.40, 35.50),
    (48.05, 35.50),
    (48.05, 37.90),
    (63.10, 37.90),
    (63.10, 70.00),
    (62.70, 70.00),
    (62.70, 79.20),
    (25.20, 79.20),
    (25.20, 76.00),
    (23.78, 76.00),
]

P000 = [
    (39.75, 41.10), (39.75, 37.40), (25.20, 37.40), (25.20, 23.50),
    (25.00, 23.50), (25.00, 15.20), (68.70, 15.20), (68.70, 16.40),
    (80.14, 16.40), (80.14, 19.125833),
]
SIM_RST = [
    (32.71, 26.40), (32.75, 25.50), (26.20, 25.50), (26.20, 17.60),
    (55.30, 17.60), (55.30, 18.50), (68.00, 18.50), (68.00, 35.40),
    (78.00, 35.40), (78.00, 36.00),
]
be.LOCKED = list(be.LOCKED) + [
    ("P0.00", "In1.Cu", P000),
    ("SIM_RST", "In1.Cu", SIM_RST),
]


def poly_xy():
    return [(p[0], p[1]) for p in POLY]


def crossing_test(pts):
    skirt = be.whole_segment_crossing_test(pts)
    skirt["method"] = (
        "segment-vs-segment interior intersection plus 0.05 mm samples, "
        "against P0.16, P0.17, P0.19, P0.20, the SIM_CLK In1 run, the "
        "SIM_RST run (F.Cu neck plus In1), and the P0.00 In1 run. Layers "
        "are not exempt. A same-centerline stack on x=44.25, x=44.60, or "
        "the y=63.20 eastbounds is a fail. Endpoint-only touches are not crossings."
    )
    return skirt


def route_box(x1, y1, x2, y2):
    """RF keepout is the box x<=24.2 and y in [20, 64], not every x<=24.2.
    Also the SiP body and the sealed B.Cu pocket."""
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(2, int(length / 0.02))
    for i in range(n + 1):
        t = i / n
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if x <= 24.2 + 1e-9 and 20.0 <= y <= 64.0:
            return "rf_keepout"
        if 28.0 <= x <= 44.0 and 26.75 <= y <= 37.25:
            return "sip_body"
        if 81.8 <= x <= 97.3 and abs(y - 44.60) <= (W / 2 + 0.15):
            return "sealed_pocket"
    return None


def seg_clearance(board, x1, y1, x2, y2):
    row = be.shape_clearance(board, IN2, x1, y1, x2, y2)
    box = route_box(x1, y1, x2, y2)
    foreign_ok = row["foreign"] is None or row["foreign_exact"] >= CF - 1e-9
    power_ok = row["power"] is None or row["power_exact"] >= CP - 1e-9
    hole_ok = row["hole"] is None or row["hole"] >= m.HOLE - 1e-9
    row["body"] = box is not None
    row["why"] = box
    row["ok"] = foreign_ok and power_ok and hole_ok and box is None
    row["start"] = [x1, y1]
    row["end"] = [x2, y2]
    row["layer"] = "In2.Cu"
    return row


def shp_of(it, lid):
    if it["kind"] == "pad":
        return it["obj"].GetEffectiveShape(lid)
    if it["kind"] == "via":
        return pcbnew.SHAPE_CIRCLE(
            m.xy(it["x"], it["y"]),
            pcbnew.FromMM(m.mm(it["obj"].GetWidth(lid)) / 2),
        )
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
                "x": m.mm(p.GetPosition().x),
                "y": m.mm(p.GetPosition().y),
                "layers": layers,
                "obj": p,
                "nm": (p.GetPosition().x, p.GetPosition().y),
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
                "drill": m.mm(t.GetDrillValue()),
                "width": m.mm(t.GetWidth(F)),
                "through": (
                    board.GetLayerName(t.TopLayer()) == "F.Cu"
                    and board.GetLayerName(t.BottomLayer()) == "B.Cu"
                ),
                "nm": (t.GetPosition().x, t.GetPosition().y),
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

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.4")
    far_i = next(i for i, it in enumerate(items) if it["name"] == "J12.8")
    start_i = next(i for i, it in enumerate(items) if it.get("nm") == START_VIA_NM)
    named = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        if (t.GetPosition().x, t.GetPosition().y) == NAMED_VIA_NM:
            named = {
                "net": t.GetNetname(),
                "xy": [m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)],
                "width_mm": m.mm(t.GetWidth(F)),
                "radius_mm": m.mm(t.GetWidth(F)) / 2,
                "drill_mm": m.mm(t.GetDrillValue()),
                "through": (
                    board.GetLayerName(t.TopLayer()) == "F.Cu"
                    and board.GetLayerName(t.BottomLayer()) == "B.Cu"
                ),
                "nm": [t.GetPosition().x, t.GetPosition().y],
                "on_u1_island": False,
            }

    def names(root_idx):
        return [items[i]["name"] for i in range(len(items)) if find(i) == find(root_idx)]

    def layer_names(root_idx):
        lids = set()
        for i in range(len(items)):
            if find(i) == find(root_idx):
                lids.update(items[i]["layers"])
        return [name for name, lid in LAYERS if lid in lids]

    u = items[u1]["obj"]
    far = items[far_i]["obj"]
    gap = m.mm(u.GetEffectiveShape(F).GetClearance(far.GetEffectiveShape(F)))
    sv = items[start_i]
    far_layers = []
    for name, lid in LAYERS:
        if far.IsOnLayer(lid):
            far_layers.append(name)
    return {
        "same_island": find(u1) == find(far_i),
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "u1_island": names(u1),
        "u1_island_layers": layer_names(u1),
        "far_island": names(far_i),
        "far_island_layers": layer_names(far_i),
        "far_pad_layers_all_copper": far_layers,
        "far_pad_xy": [items[far_i]["x"], items[far_i]["y"]],
        "far_pad_nm": list(items[far_i]["nm"]),
        "far_fcu_only": far_layers == ["F.Cu"],
        "j12_has_in2": far.IsOnLayer(IN2),
        "start_via_on_u1": find(start_i) == find(u1),
        "start_via": {
            "xy": [sv["x"], sv["y"]],
            "width_mm": sv["width"],
            "radius_mm": sv["width"] / 2,
            "drill_mm": sv["drill"],
            "through": sv["through"],
            "nm": list(sv["nm"]),
            "net": NET,
        },
        "named_via": named,
        "named_via_on_u1": False,
    }


def straight_chord(board) -> dict:
    ax, ay = 43.622, 35.647
    bx, by = 24.181, 75.250
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != "P0.02":
            continue
        x, y = m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)
        if abs(x - 40.75) > 0.02 or abs(y - 41.1) > 0.02:
            continue
        dist = m.dps(x, y, ax, ay, bx, by)
        edge = dist - m.mm(t.GetWidth(F)) / 2 - (W / 2)
        via = {
            "xy": [x, y],
            "width_mm": m.mm(t.GetWidth(F)),
            "center_distance_mm": dist,
            "edge_clearance_mm": edge,
        }
        break
    return {
        "from_existing_copper": [ax, ay],
        "to_pad_edge_point": [bx, by],
        "width_mm": W,
        "layer": "F.Cu",
        "length_mm": round(math.hypot(bx - ax, by - ay), 6),
        "crosses_sip_body": m.crosses_body(ax, ay, bx, by),
        "p002": via,
        "used": False,
        "note": "Straight F.Cu chord hits P0.02 via (40.75, 41.10). Not used.",
    }


def measure(board):
    rows = []
    mf = mp = mh = None
    for i in range(len(POLY) - 1):
        x1, y1 = POLY[i]
        x2, y2 = POLY[i + 1]
        row = seg_clearance(board, x1, y1, x2, y2)
        rows.append(row)
        if row.get("foreign_exact") is not None and (mf is None or row["foreign_exact"] < mf[0]):
            mf = (row["foreign_exact"], row["foreign_item"])
        if row.get("power_exact") is not None and (mp is None or row["power_exact"] < mp[0]):
            mp = (row["power_exact"], row["power_item"])
        if row.get("hole") is not None and (mh is None or row["hole"] < mh[0]):
            mh = (row["hole"], row["hole_item"])
    pad = None
    for fp in board.GetFootprints():
        if fp.GetReference() != "J12":
            continue
        for p in fp.Pads():
            if p.GetNumber() == "8":
                pad = p
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2]), m.xy(*POLY[-1]), pcbnew.FromMM(W))
    hits = bool(pad is not None and land.Collide(pad.GetEffectiveShape(IN2)))
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits
        and nseg <= 10
        and (mf is None or mf[0] >= CF - 1e-9)
        and (mp is None or mp[0] >= CP - 1e-9)
        and (mh is None or mh[0] >= m.HOLE - 1e-9)
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
        "lands_on_j12_8": hits,
        "new_via": None,
        "ok": ok,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "width_mm": W,
    }


def add_route(board):
    net = board.FindNet(NET)
    if net is None:
        raise SystemExit("P0.07 missing")
    for i in range(len(POLY) - 1):
        x1, y1 = POLY[i]
        x2, y2 = POLY[i + 1]
        tr = pcbnew.PCB_TRACK(board)
        if i == 0:
            tr.SetStart(pcbnew.VECTOR2I(START_VIA_NM[0], START_VIA_NM[1]))
        else:
            tr.SetStart(m.xy(x1, y1))
        if i == len(POLY) - 2:
            tr.SetEnd(pcbnew.VECTOR2I(PAD_NM[0], PAD_NM[1]))
        else:
            tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN2)
        tr.SetNet(net)
        board.Add(tr)


def protect_ok(board) -> dict:
    return {
        "p016": m.poly_ok(board, be.P16, "P0.16", IN1),
        "p017": m.poly_ok(board, be.P17, "P0.17", IN2),
        "p019": m.poly_ok(board, be.P19, "P0.19", IN1),
        "p020": m.poly_ok(board, be.P20, "P0.20", IN2),
        "sim_clk": m.poly_ok(board, be.SIM, "SIM_CLK", IN1),
        "sim_rst_in1": m.poly_ok(board, SIM_RST[1:], "SIM_RST", IN1),
        "sim_rst_neck": m.poly_ok(board, SIM_RST[:2], "SIM_RST", F),
        "sim_rst_via": m.via_at(board, "SIM_RST", 32.75, 25.50),
        "p000": m.poly_ok(board, P000, "P0.00", IN1),
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
        if after["vias"].get(net, 0) != n:
            bad.append(f"via {net} {n}->{after['vias'].get(net, 0)}")
    if after["vias"].get(NET, 0) != before_counts["vias"].get(NET, 0):
        bad.append(f"P0.07 vias changed {before_counts['vias'].get(NET, 0)}->{after['vias'].get(NET, 0)}")
    expect = before_counts["tracks"].get(NET, 0) + (len(POLY) - 1)
    if after["tracks"].get(NET, 0) != expect:
        bad.append(f"P0.07 tracks {before_counts['tracks'].get(NET, 0)}->{after['tracks'].get(NET, 0)} expected {expect}")
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
    res["stats"]["p007_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
    return res


def restore():
    shutil.copy2(BACKUP, BOARD)


def write_outputs(decision, info, before, after, reason, meas, skirt):
    ts = m.ist_now()
    bstat, a = before, after
    placed = decision == "KEEP"
    segs = []
    for i in range(len(POLY) - 1):
        segs.append({
            "layer": "In2.Cu",
            "width_mm": W,
            "start": [round(POLY[i][0], 6), round(POLY[i][1], 6)],
            "end": [round(POLY[i + 1][0], 6), round(POLY[i + 1][1], 6)],
        })
    payload = {
        "pass": "30bg",
        "timestamp": ts,
        "decision": decision,
        "net": NET,
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "pcb_blob_at_end": m.git_blob(),
        "sha1sum_at_end": hashlib.sha1(BOARD.read_bytes()).hexdigest(),
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "head_matches_expected": info.get("git_head", "").startswith(EXPECTED_HEAD),
        "blob_matches_expected": info.get("pcb_blob") == EXPECTED_BLOB,
        "same_island": info["gap"]["same_island"],
        "named_via_on_u1_island": info["gap"]["named_via_on_u1"],
        "named_via": info["gap"]["named_via"],
        "start_via_on_u1_island": info["gap"]["start_via_on_u1"],
        "start_via": info["gap"]["start_via"],
        "far_island_layers": info["gap"]["far_island_layers"],
        "far_pad_layers": info["gap"]["far_pad_layers_all_copper"],
        "far_pad_xy": info["gap"]["far_pad_xy"],
        "u1_island_layers": info["gap"]["u1_island_layers"],
        "u1_island": info["gap"]["u1_island"],
        "far_island": info["gap"]["far_island"],
        "far_fcu_only": info["gap"]["far_fcu_only"],
        "joined": "J12.8 pad center on In2.Cu (PTH, copper already on In2)" if placed else None,
        "pad_edge_mm": info["gap"]["pad_edge_exact_mm"],
        "pad_edge_census_mm": 44.118,
        "straight_chord": info.get("chord"),
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
                "start": r["start"], "end": r["end"], "layer": r.get("layer"),
                "ok": r["ok"], "body": r.get("body"),
                "foreign_mm": r.get("foreign"), "foreign_item": r.get("foreign_item"),
                "power_mm": r.get("power"), "power_item": r.get("power_item"),
                "hole_mm": r.get("hole"), "hole_item": r.get("hole_item"),
                "why": r.get("why"),
            }
            for r in meas.get("segments", [])
        ],
        "p007_opens_before": bstat.get("p007_unconnected"),
        "p007_opens_after": a.get("p007_unconnected"),
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
        "sim_clk_ripped_or_stacked": False,
        "sim_rst_ripped_or_stacked": False,
        "p000_ripped_or_stacked": False,
        "skirt_slot_used": False,
        "sealed_pocket_used": False,
        "rf_keepout_used": False,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
    }
    (REPORTS / "PASS30BG_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BG_SUMMARY — P0.07",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.07",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**Expected tip/blob matched:** {payload['head_matches_expected']} / {payload['blob_matches_expected']}",
        f"**Ends already one island:** {info['gap']['same_island']}",
        f"**Named via (47.40, 36.50) on U1.4 island:** {info['gap']['named_via_on_u1']}",
        f"**Named via:** {info['gap']['named_via']}",
        f"**Start via (47.40, 35.50) on U1.4 island:** {info['gap']['start_via_on_u1']}",
        f"**Start via:** {info['gap']['start_via']}",
        f"**J12.8 center:** {info['gap']['far_pad_xy']}",
        f"**J12.8 layers:** {info['gap']['far_pad_layers_all_copper']}",
        f"**Far island F.Cu-only:** {info['gap']['far_fcu_only']}",
        f"**U1 island layers:** {info['gap']['u1_island_layers']}",
        f"**Pad-edge (U1.4 to J12.8):** {info['gap']['pad_edge_exact_mm']:.6f} mm (census 44.118)",
        "**New via:** no",
        (
            "**Joined:** J12.8 pad center on In2.Cu (PTH copper already on In2)"
            if placed else "**Joined:** none (no copper left)"
        ),
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Crossing test failed:** {skirt.get('crossed')}",
        f"**Whole-segment crossing count:** {skirt.get('crossing_count')}",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**P0.07 opens:** {bstat.get('p007_unconnected')} → {a.get('p007_unconnected')}",
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
            f"F.Cu 0.18 mm {info['chord']['from_existing_copper']} → {info['chord']['to_pad_edge_point']}, "
            f"length {info['chord']['length_mm']} mm. Crosses SiP body: {info['chord']['crosses_sip_body']}. "
            f"P0.02 {info['chord']['p002']}. Not used."
        ),
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
        lines.append(
            "In2.Cu only, 9 segments, no new via. Named via (47.40, 36.50) is P0.05 and was not used. "
            "Starts at existing P0.07 through-via (47.40, 35.50) and lands on J12.8 (PTH, In2 copper). Kept."
        )
        lines.append("")
        for s in segs:
            lines.append(f"- {tuple(s['start'])} → {tuple(s['end'])} {s['layer']} {s['width_mm']} mm")
    else:
        lines.append("No copper left on the board.")
    lines += [
        "",
        "East of the SiP at x=48.05 (clear of the P0.06 via at 48.62, 36.00), east to x=63.10 "
        "(east of the P0.20 y=63.20 end at x=55.78 and of the skirt verticals), south to y=70, "
        "jog to x=62.70 to clear J13.1, south to y=79.20 (south of the header row and of the RF keepout), "
        "west to x=25.20, north into the gap east of J12.8, then west onto the pad center. "
        "x=44.25 and x=44.60 not used. Sealed y=44.60 pocket not entered. "
        "RF keepout box x<=24.2 and y in [20, 64] not entered. "
        "P0.00, SIM_RST, and SIM_CLK centerlines not stacked. No header or U1 move. No other net.",
        "",
        "## Clearance by segment",
        "",
    ]
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
        "| | unconnected | P0.07 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        (
            f"| before | {bstat.get('unconnected_items')} | {bstat.get('p007_unconnected')} | "
            f"{bstat.get('shorting_items')} | {bstat.get('clearance')} | {bstat.get('tracks_crossing')} | "
            f"{bstat.get('hole_clearance')} | {bstat.get('hole_to_hole')} | {bstat.get('gnd_zone_islands')} |"
        ),
        (
            f"| after | {a.get('unconnected_items')} | {a.get('p007_unconnected')} | "
            f"{a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | "
            f"{a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |"
        ),
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}",
        "P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. "
        "SIM_CLK, SIM_RST, and P0.00 not ripped and not stacked. "
        "Skirt slot, sealed pocket, and RF keepout not used. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BG_SUMMARY.md").write_text("\n".join(lines) + "\n")
    para = (
        f"\n## Pass30bg — P0.07 — {ts}\n\n"
        f"**Decision:** **{decision}**. Pad-edge {info['gap']['pad_edge_exact_mm']:.6f} mm (census 44.118). "
        f"Named via (47.40, 36.50) on U1.4 island: {info['gap']['named_via_on_u1']} "
        f"(net {None if not info['gap']['named_via'] else info['gap']['named_via'].get('net')}; not used). "
        f"P0.07 via (47.40, 35.50) on U1.4 island: {info['gap']['start_via_on_u1']} "
        f"(pad {info['gap']['start_via']['width_mm']} mm, drill {info['gap']['start_via']['drill_mm']} mm). "
        f"J12.8 center {info['gap']['far_pad_xy']}; layers {info['gap']['far_pad_layers_all_copper']}. "
        f"Straight F.Cu chord hits P0.02 via (40.75, 41.10) at "
        f"{None if not info['chord']['p002'] else round(info['chord']['p002']['edge_clearance_mm'], 3)} mm; not used. "
    )
    if placed:
        para += (
            f"Kept 9 In2.Cu segments, no new via, from via (47.40, 35.50) onto J12.8. "
            f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
            f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
            f"Whole-segment crossings {skirt.get('crossing_count')}. "
            f"P0.07 opens {bstat.get('p007_unconnected')}→{a.get('p007_unconnected')}. "
            f"Unconnected {bstat.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"short/clearance/crossing/hole "
            f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
            f"hole_to_hole {a.get('hole_to_hole')}. "
            f"GND islands {bstat.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        )
    else:
        para += f"{reason} "
    para += (
        "P0.00, SIM_RST, SIM_CLK, and the four skirts not ripped or stacked. "
        "Skirt slot, sealed pocket, and RF keepout not used. No other net. No Gerbers. No commit.\n"
    )
    REVIEW.write_text(REVIEW.read_text() + para)


def main():
    info = {"git_head": m.git_head(), "pcb_blob": m.git_blob()}
    print("HEAD", info["git_head"], "BLOB", info["pcb_blob"], flush=True)
    if not info["git_head"].startswith(EXPECTED_HEAD) or info["pcb_blob"] != EXPECTED_BLOB:
        raise SystemExit(f"STOP mismatch head={info['git_head']} blob={info['pcb_blob']}")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BOARD, BACKUP)
    if m.git_blob() != EXPECTED_BLOB:
        raise SystemExit("blob changed while copying backup")

    board = pcbnew.LoadBoard(str(BOARD))
    info["gap"] = islands(board)
    info["chord"] = straight_chord(board)
    info["fp"] = m.footprint_xy(board)
    info["counts"] = m.track_counts(board)
    info["protect_before"] = protect_ok(board)
    print("ISLAND", info["gap"]["same_island"], "pad-edge", info["gap"]["pad_edge_exact_mm"], flush=True)
    print("NAMED", info["gap"]["named_via"], "on U1", info["gap"]["named_via_on_u1"], flush=True)
    print("START", info["gap"]["start_via_on_u1"], info["gap"]["start_via"], flush=True)
    print("J12", info["gap"]["far_pad_xy"], info["gap"]["far_pad_layers_all_copper"], "fcu_only", info["gap"]["far_fcu_only"], flush=True)
    print("CHORD", info["chord"]["p002"], flush=True)
    print("PROTECT", info["protect_before"], flush=True)

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BG_BEFORE.json"))
    bst = before["stats"]
    print("BEFORE", {k: v for k, v in bst.items() if k != "nongnd"}, flush=True)

    def finish(decision, reason, after_stats):
        info["gained"] = info.get("gained", {})
        skirt = info.get("skirt") or {"crossed": False, "crossing_count": 0, "segments": [], "method": ""}
        meas = info.get("meas") or {"segments": []}
        write_outputs(decision, info, bst, after_stats, reason, meas, skirt)
        print("DECISION", decision, flush=True)
        print(reason, flush=True)

    meas = measure(board)
    skirt = crossing_test(poly_xy())
    info["meas"] = meas
    info["skirt"] = skirt
    print(
        "MEAS ok", meas["ok"], "foreign", meas["min_clearance_mm"], meas["min_clearance_item"],
        "power", meas["min_power_vin_mm"], meas["min_power_vin_item"],
        "cross", skirt["crossed"], skirt["crossing_count"],
        "land", meas["lands_on_j12_8"], flush=True,
    )

    if bst["unconnected_items"] != EXPECTED_UNC:
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish(
            "NO-ROUTE",
            f"NO-ROUTE. Unconnected started at {bst['unconnected_items']}, not {EXPECTED_UNC}. No copper added.",
            bst,
        )
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish("NO-ROUTE", "NO-ROUTE. U1.4 and J12.8 are already one island. No copper added.", bst)
        return
    if not info["gap"]["start_via_on_u1"]:
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. Existing P0.07 via (47.40, 35.50) is not on the U1.4 island. "
            "Named via (47.40, 36.50) is not on that island either. No copper added.",
            bst,
        )
        return
    if info["gap"]["far_fcu_only"] or not info["gap"]["j12_has_in2"]:
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. J12.8 has no In2 copper to land on. A via was not punched into an F.Cu-only pad. No copper added.",
            bst,
        )
        return
    if skirt["crossed"] or not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BG_BEFORE.json", REPORTS / "DRC_PASS30BG_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. No legal path. "
            f"measure_ok={meas['ok']} foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']} "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']} "
            f"hole {meas['min_hole_mm']} land {meas['lands_on_j12_8']} crossings {skirt['crossing_count']}. "
            "Skirt slot, sealed pocket, RF keepout, and locked centerlines were not used. No copper added.",
            bst,
        )
        return

    try:
        add_route(board)
        moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != m.footprint_xy(board).get(ref))
        ripped = counts_locked(info["counts"], board)
        pa = protect_ok(board)
        skirt_after = crossing_test(poly_xy())
        if moved or ripped or not all(pa.values()) or skirt_after["crossed"]:
            restore()
            after = enrich(m.run_drc(REPORTS / "DRC_PASS30BG_AFTER.json"))
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
    except Exception:
        if BACKUP.is_file():
            restore()
        raise

    mid = enrich(m.run_drc(REPORTS / "DRC_PASS30BG_MID.json"))
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["p007_unconnected"] - mst["p007_unconnected"]
    board2 = pcbnew.LoadBoard(str(BOARD))
    skirts_intact = protect_ok(board2)
    skirt_on_disk = crossing_test(poly_xy())
    info["skirt"] = skirt_on_disk
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
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BG_AFTER.json"))
        ast = after["stats"]
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.07 opens {bst['p007_unconnected']}→{mst['p007_unconnected']} (need drop ≥ 1). "
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

    shutil.copy2(REPORTS / "DRC_PASS30BG_MID.json", REPORTS / "DRC_PASS30BG_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. In2 south bypass, {len(POLY) - 1} new segments, no new via, "
        f"from existing P0.07 through-via (47.40, 35.50) onto J12.8. "
        f"Named via (47.40, 36.50) is P0.05 and was not used. "
        f"Straight F.Cu chord not used (P0.02). Skirt slot, sealed pocket, and RF keepout not used. "
        f"Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
        f"P0.07 opens {bst['p007_unconnected']}→{mst['p007_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Four skirts, SIM_CLK, SIM_RST, and P0.00 not ripped or stacked. No other net."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
