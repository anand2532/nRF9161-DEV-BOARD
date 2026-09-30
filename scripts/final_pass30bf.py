#!/usr/bin/env python3
"""pass30bf — ONE attempt: P0.00 only.

U1.95 is on the south edge. Existing through-via (39.75, 41.10) is already
on that island, so the route starts there and does not add a via. The far
F.Cu segment is tied to through-via (80.14, 19.125833), so the join is on
In1.Cu at that via (not a via punched into R10.1).

West of the body at x=25.20/25.00 (east of the RF keepout), north of the
SIM_RST y=17.60 run at y=15.20, then east and south onto the far via.
No skirt slot, no SIM_CLK/SIM_RST centerline, no sealed pocket.
Straight F.Cu chord is not used.
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
spec2 = importlib.util.spec_from_file_location("p30be", ROOT / "scripts" / "final_pass30be.py")
be = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(be)

BOARD = m.BOARD
BACKUP = ROOT / ".mcp-backups/pass30bf/pre-edit.kicad_pcb"
REPORTS = m.REPORTS
REVIEW = m.REVIEW
F, B, IN1, IN2 = m.F, m.B, m.IN1, m.IN2
W = m.W
CF = m.CF
CP = m.CP
LAYERS = m.LAYERS
NET = "P0.00"
be.NET = NET
EXPECTED_HEAD = "b60ffcb"
EXPECTED_BLOB = "625ef9d7ba5150f27306905b448cc93eee4f59d9"
EXPECTED_UNC = 54

# Exact far via center (nm), not the rounded 19.126 label.
FAR_VIA_NM = (80140000, 19125833)
FAR_VIA = (pcbnew.ToMM(FAR_VIA_NM[0]), pcbnew.ToMM(FAR_VIA_NM[1]))

POLY = [
    (39.75, 41.10, IN1, "In1.Cu"),
    (39.75, 37.40, IN1, "In1.Cu"),
    (25.20, 37.40, IN1, "In1.Cu"),
    (25.20, 23.50, IN1, "In1.Cu"),
    (25.00, 23.50, IN1, "In1.Cu"),
    (25.00, 15.20, IN1, "In1.Cu"),
    (68.70, 15.20, IN1, "In1.Cu"),
    (68.70, 16.40, IN1, "In1.Cu"),
    (80.14, 16.40, IN1, "In1.Cu"),
    (FAR_VIA[0], FAR_VIA[1], IN1, "In1.Cu"),
]

SIM_RST = [
    (32.71, 26.40), (32.75, 25.50), (26.20, 25.50), (26.20, 17.60),
    (55.30, 17.60), (55.30, 18.50), (68.00, 18.50), (68.00, 35.40),
    (78.00, 35.40), (78.00, 36.00),
]
be.LOCKED = list(be.LOCKED) + [("SIM_RST", "In1.Cu", SIM_RST)]


def poly_xy():
    return [(p[0], p[1]) for p in POLY]


def crossing_test(pts):
    skirt = be.whole_segment_crossing_test(pts)
    skirt["method"] = (
        "segment-vs-segment interior intersection plus 0.05 mm samples, "
        "against P0.16, P0.17, P0.19, P0.20, the SIM_CLK In1 run, and the "
        "SIM_RST run (F.Cu neck plus In1). Layers are not exempt. A "
        "same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds "
        "is a fail. Endpoint-only touches are not crossings."
    )
    return skirt


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

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.95")
    far_i = next(
        i for i, it in enumerate(items)
        if it["kind"] == "trk" and it["layers"] == [F] and "79.490,18.000" in it["name"]
    )
    start_via_i = next(
        i for i, it in enumerate(items)
        if it["kind"] == "via" and it.get("nm") == (39750000, 41100000)
    )

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
    gap = m.mm(u.GetEffectiveShape(F).GetClearance(shp_of(far, F)))
    through = []
    for i, it in enumerate(items):
        if it["kind"] == "via" and it.get("through") and find(i) == find(far_i):
            through.append({
                "name": it["name"],
                "xy": [round(it["x"], 6), round(it["y"], 6)],
                "width_mm": it["width"],
                "drill_mm": it["drill"],
                "nm": list(it["nm"]),
            })
    sv = items[start_via_i]
    return {
        "same_island": find(u1) == find(far_i),
        "pad_edge_mm": round(gap, 3),
        "pad_edge_exact_mm": gap,
        "u1_island": names(u1),
        "u1_island_layers": layer_names(u1),
        "far_island": names(far_i),
        "far_island_layers": layer_names(far_i),
        "far_through_vias": through,
        "far_track": far["name"],
        "bcu_only": layer_names(far_i) == ["B.Cu"],
        "fcu_only": layer_names(far_i) == ["F.Cu"],
        "start_via_on_u1": find(start_via_i) == find(u1),
        "start_via": {
            "xy": [sv["x"], sv["y"]],
            "width_mm": sv["width"],
            "radius_mm": sv["width"] / 2,
            "drill_mm": sv["drill"],
            "through": sv["through"],
            "nm": list(sv["nm"]),
        },
    }


def straight_chord(board) -> dict:
    ax, ay = 39.897, 36.872
    bx, by = 79.408, 19.163
    hit = None
    for t in board.GetTracks():
        if t.GetNetname() != "VDD1" or t.GetClass() == "PCB_VIA" or t.GetLayer() != F:
            continue
        a, b, c, d = m.ends(t)
        if abs(a - 50.68) > 0.02 or abs(c - 50.68) > 0.02:
            continue
        if min(b, d) > 31.05 or max(b, d) < 34.95:
            continue
        proper = be.interior_cross((ax, ay), (bx, by), (a, b), (c, d))
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
        "note": "Straight F.Cu chord crosses VDD1 (50.68, 35.00)-(50.68, 31.00). Not used.",
    }


def measure(board):
    rows = []
    mf = mp = mh = None
    for i in range(len(POLY) - 1):
        x1, y1 = POLY[i][0], POLY[i][1]
        x2, y2 = POLY[i + 1][0], POLY[i + 1][1]
        row = be.shape_clearance(board, IN1, x1, y1, x2, y2)
        row["start"] = [x1, y1]
        row["end"] = [x2, y2]
        row["layer"] = "In1.Cu"
        rows.append(row)
        if row.get("foreign_exact") is not None and (mf is None or row["foreign_exact"] < mf[0]):
            mf = (row["foreign_exact"], row["foreign_item"])
        if row.get("power_exact") is not None and (mp is None or row["power_exact"] < mp[0]):
            mp = (row["power_exact"], row["power_item"])
        if row.get("hole") is not None and (mh is None or row["hole"] < mh[0]):
            mh = (row["hole"], row["hole_item"])
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != NET:
            continue
        if t.GetPosition().x == FAR_VIA_NM[0] and t.GetPosition().y == FAR_VIA_NM[1]:
            via = t
    land = pcbnew.SHAPE_SEGMENT(m.xy(*POLY[-2][:2]), m.xy(*POLY[-1][:2]), pcbnew.FromMM(W))
    # Force the geometric end onto the stored via center.
    land = pcbnew.SHAPE_SEGMENT(
        m.xy(POLY[-2][0], POLY[-2][1]),
        pcbnew.VECTOR2I(FAR_VIA_NM[0], FAR_VIA_NM[1]),
        pcbnew.FromMM(W),
    )
    hits = False
    if via is not None:
        pad = pcbnew.SHAPE_CIRCLE(via.GetPosition(), via.GetWidth(IN1) // 2)
        hits = bool(land.Collide(pad))
    nseg = len(POLY) - 1
    ok = (
        all(r["ok"] for r in rows)
        and hits
        and nseg <= 10
        and min(p[0] for p in POLY) > 24.2
        and not any(r["body"] for r in rows)
        and (mf is None or mf[0] >= CF - 1e-9)
        and (mp is None or mp[0] >= CP - 1e-9)
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
        "new_via": None,
        "ok": ok,
        "meets_foreign_0_15": mf is None or mf[0] >= CF - 1e-9,
        "meets_power_0_20": mp is None or mp[0] >= CP - 1e-9,
        "width_mm": W,
    }


def add_route(board):
    net = board.FindNet(NET)
    if net is None:
        raise SystemExit("P0.00 missing")
    for i in range(len(POLY) - 1):
        x1, y1 = POLY[i][0], POLY[i][1]
        x2, y2 = POLY[i + 1][0], POLY[i + 1][1]
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(m.xy(x1, y1))
        if i == len(POLY) - 2:
            tr.SetEnd(pcbnew.VECTOR2I(FAR_VIA_NM[0], FAR_VIA_NM[1]))
        else:
            tr.SetEnd(m.xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(IN1)
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
        bad.append(f"P0.00 vias changed {before_counts['vias'].get(NET, 0)}->{after['vias'].get(NET, 0)}")
    expect = before_counts["tracks"].get(NET, 0) + (len(POLY) - 1)
    if after["tracks"].get(NET, 0) != expect:
        bad.append(f"P0.00 tracks {before_counts['tracks'].get(NET, 0)}->{after['tracks'].get(NET, 0)} expected {expect}")
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
    res["stats"]["p000_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
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
            "layer": "In1.Cu",
            "width_mm": W,
            "start": [round(POLY[i][0], 6), round(POLY[i][1], 6)],
            "end": [round(POLY[i + 1][0], 6), round(POLY[i + 1][1], 6)],
        })
    payload = {
        "pass": "30bf",
        "timestamp": ts,
        "decision": decision,
        "net": NET,
        "git_head": info.get("git_head"),
        "pcb_blob_at_start": info.get("pcb_blob"),
        "pcb_blob_at_end": m.git_blob(),
        "sha1sum_at_end": __import__("hashlib").sha1(BOARD.read_bytes()).hexdigest(),
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "head_matches_expected": info.get("git_head", "").startswith(EXPECTED_HEAD),
        "blob_matches_expected": info.get("pcb_blob") == EXPECTED_BLOB,
        "same_island": info["gap"]["same_island"],
        "start_via_on_u1_island": info["gap"]["start_via_on_u1"],
        "start_via": info["gap"]["start_via"],
        "far_island_layers": info["gap"]["far_island_layers"],
        "u1_island_layers": info["gap"]["u1_island_layers"],
        "u1_island": info["gap"]["u1_island"],
        "far_island": info["gap"]["far_island"],
        "far_bcu_only": info["gap"]["bcu_only"],
        "far_fcu_only": info["gap"]["fcu_only"],
        "far_through_vias": info["gap"]["far_through_vias"],
        "joined": "existing through-via (80.14, 19.125833) on In1.Cu" if placed else None,
        "pad_edge_mm": info["gap"]["pad_edge_exact_mm"],
        "pad_edge_census_mm": 43.298,
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
        "p000_opens_before": bstat.get("p000_unconnected"),
        "p000_opens_after": a.get("p000_unconnected"),
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
        "skirt_slot_used": False,
        "sealed_pocket_used": False,
        "other_net": False,
        "gerbers": False,
        "commit": False,
        "board_sha256": m.sha(BOARD),
        "backup": str(BACKUP) if BACKUP.is_file() else None,
        "reverted_to_pre_edit_blob": info.get("reverted_blob_match"),
    }
    (REPORTS / "PASS30BF_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BF_SUMMARY — P0.00",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.00",
        f"**Git HEAD:** `{info.get('git_head')}`",
        f"**PCB blob at start:** `{info.get('pcb_blob')}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**Expected tip/blob matched:** {payload['head_matches_expected']} / {payload['blob_matches_expected']}",
        f"**Ends already one island:** {info['gap']['same_island']}",
        f"**Start via (39.75, 41.10) on U1.95 island:** {info['gap']['start_via_on_u1']}",
        f"**Start via:** {info['gap']['start_via']}",
        f"**Far island layers:** {info['gap']['far_island_layers']}",
        f"**Far island F.Cu-only:** {info['gap']['fcu_only']}",
        f"**Far through-vias:** {info['gap']['far_through_vias']}",
        f"**U1 island layers:** {info['gap']['u1_island_layers']}",
        f"**Pad-edge (U1.95 to F.Cu x=79.49 segment):** {info['gap']['pad_edge_exact_mm']:.6f} mm (census 43.298)",
        "**New via:** no",
        f"**Joined:** existing through-via (80.14, 19.125833) on In1.Cu" if placed else "**Joined:** none (no copper left)",
        f"**New segments:** {len(segs) if placed else 0} (limit 10)",
        f"**Crossing test failed:** {skirt.get('crossed')}",
        f"**Whole-segment crossing count:** {skirt.get('crossing_count')}",
        f"**Min foreign clearance:** {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}",
        f"**Min POWER/VIN clearance:** {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}",
        f"**Min hole clearance:** {meas.get('min_hole_mm')} mm vs {meas.get('min_hole_item')}",
        f"**P0.00 opens:** {bstat.get('p000_unconnected')} → {a.get('p000_unconnected')}",
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
            "In1.Cu only, 9 segments, no new via. Starts at existing through-via "
            "(39.75, 41.10) and lands on existing through-via (80.14, 19.125833). Kept."
        )
        lines.append("")
        for s in segs:
            lines.append(f"- {tuple(s['start'])} → {tuple(s['end'])} {s['layer']} {s['width_mm']} mm")
    else:
        lines.append("No copper left on the board.")
    lines += [
        "",
        "West of the SiP on In1 at x=25.20 then x=25.00 (east of the RF keepout x=24.2), "
        "north at y=15.20 (north of SIM_RST y=17.60 and of SIM_CLK), east to x=80.14, "
        "south onto the existing far through-via. x=44.25 and x=44.60 not used. "
        "Sealed y=44.60 pocket not entered. SIM_RST and SIM_CLK centerlines not stacked. "
        "No header or U1 move. No other net.",
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
        "| | unconnected | P0.00 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        (
            f"| before | {bstat.get('unconnected_items')} | {bstat.get('p000_unconnected')} | "
            f"{bstat.get('shorting_items')} | {bstat.get('clearance')} | {bstat.get('tracks_crossing')} | "
            f"{bstat.get('hole_clearance')} | {bstat.get('hole_to_hole')} | {bstat.get('gnd_zone_islands')} |"
        ),
        (
            f"| after | {a.get('unconnected_items')} | {a.get('p000_unconnected')} | "
            f"{a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | "
            f"{a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} |"
        ),
        "",
        "No other non-GND net gained an open." if not info.get("gained") else f"Other non-GND gained: {info.get('gained')}",
        "P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. "
        "SIM_CLK and SIM_RST not ripped and not stacked. "
        "Skirt slot and sealed pocket not used. No other net. No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30BF_SUMMARY.md").write_text("\n".join(lines) + "\n")
    para = (
        f"\n## Pass30bf — P0.00 — {ts}\n\n"
        f"**Decision:** **{decision}**. Pad-edge {info['gap']['pad_edge_exact_mm']:.6f} mm (census 43.298). "
        f"Via (39.75, 41.10) on U1.95 island: {info['gap']['start_via_on_u1']} "
        f"(pad {info['gap']['start_via']['width_mm']} mm, drill {info['gap']['start_via']['drill_mm']} mm). "
        f"Far layers {info['gap']['far_island_layers']}; through-vias {info['gap']['far_through_vias']}. "
        f"Straight F.Cu chord hits VDD1 (50.68, 35)-(50.68, 31); not used. "
    )
    if placed:
        para += (
            f"Kept 9 In1.Cu segments, no new via, from via (39.75, 41.10) to via (80.14, 19.125833). "
            f"Foreign {meas.get('min_clearance_mm')} mm vs {meas.get('min_clearance_item')}. "
            f"POWER {meas.get('min_power_vin_mm')} mm vs {meas.get('min_power_vin_item')}. "
            f"Whole-segment crossings {skirt.get('crossing_count')}. "
            f"P0.00 opens {bstat.get('p000_unconnected')}→{a.get('p000_unconnected')}. "
            f"Unconnected {bstat.get('unconnected_items')}→{a.get('unconnected_items')}. "
            f"short/clearance/crossing/hole "
            f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
            f"hole_to_hole {a.get('hole_to_hole')}. "
            f"GND islands {bstat.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        )
    else:
        para += f"{reason} "
    para += (
        "SIM_RST, SIM_CLK, and the four skirts not ripped or stacked. "
        "Skirt slot and sealed pocket not used. No other net. No Gerbers. No commit.\n"
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
    print("VIA on U1", info["gap"]["start_via_on_u1"], info["gap"]["start_via"], flush=True)
    print("FAR", info["gap"]["far_island_layers"], info["gap"]["far_through_vias"], "fcu_only", info["gap"]["fcu_only"], flush=True)
    print("CHORD", info["chord"]["vdd1"], flush=True)
    print("PROTECT", info["protect_before"], flush=True)

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BF_BEFORE.json"))
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
        "land", meas["lands_on_far_via"], flush=True,
    )

    if bst["unconnected_items"] != EXPECTED_UNC:
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish(
            "NO-ROUTE",
            f"NO-ROUTE. Unconnected started at {bst['unconnected_items']}, not {EXPECTED_UNC}. No copper added.",
            bst,
        )
        return
    if not all(info["protect_before"].values()):
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish("NO-ROUTE", f"Locked copper missing before edit: {info['protect_before']}. No copper added.", bst)
        return
    if info["gap"]["same_island"]:
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish("NO-ROUTE", "NO-ROUTE. U1.95 and the far F.Cu segment are already one island. No copper added.", bst)
        return
    if not info["gap"]["start_via_on_u1"]:
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish("NO-ROUTE", "NO-ROUTE. Via (39.75, 41.10) is not on the U1.95 island. No copper added.", bst)
        return
    if info["gap"]["fcu_only"] or not info["gap"]["far_through_vias"]:
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. Far island has no through-via to land on, and this attempt is In1. "
            "A via was not punched into the F.Cu pad. No copper added.",
            bst,
        )
        return
    if skirt["crossed"] or not meas["ok"]:
        shutil.copy2(REPORTS / "DRC_PASS30BF_BEFORE.json", REPORTS / "DRC_PASS30BF_AFTER.json")
        finish(
            "NO-ROUTE",
            "NO-ROUTE. No legal path. "
            f"measure_ok={meas['ok']} foreign {meas['min_clearance_mm']} vs {meas['min_clearance_item']} "
            f"POWER {meas['min_power_vin_mm']} vs {meas['min_power_vin_item']} "
            f"hole {meas['min_hole_mm']} land {meas['lands_on_far_via']} crossings {skirt['crossing_count']}. "
            "Skirt slot, SIM_CLK/SIM_RST centerlines, and the sealed pocket were not used. No copper added.",
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
            after = enrich(m.run_drc(REPORTS / "DRC_PASS30BF_AFTER.json"))
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

    mid = enrich(m.run_drc(REPORTS / "DRC_PASS30BF_MID.json"))
    mst = mid["stats"]
    info["mid"] = mst
    print("MID", {k: v for k, v in mst.items() if k != "nongnd"}, flush=True)
    g = gained(bst["nongnd"], mst["nongnd"])
    info["gained"] = g
    pdrop = bst["p000_unconnected"] - mst["p000_unconnected"]
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
        after = enrich(m.run_drc(REPORTS / "DRC_PASS30BF_AFTER.json"))
        ast = after["stats"]
        info["reverted_blob_match"] = m.git_blob() == info["pcb_blob"]
        reason = (
            f"NO-ROUTE. Gate failed, full restore from `{BACKUP}`. "
            f"P0.00 opens {bst['p000_unconnected']}→{mst['p000_unconnected']} (need drop ≥ 1). "
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

    shutil.copy2(REPORTS / "DRC_PASS30BF_MID.json", REPORTS / "DRC_PASS30BF_AFTER.json")
    info["reverted_blob_match"] = False
    reason = (
        f"KEEP. In1 west/north bypass, {len(POLY) - 1} new segments, no new via, "
        f"from existing through-via (39.75, 41.10) onto existing through-via (80.14, 19.125833). "
        f"Straight F.Cu chord not used (VDD1). Skirt slot and sealed pocket not used. "
        f"Whole-segment crossings: {skirt_on_disk['crossing_count']}. "
        f"P0.00 opens {bst['p000_unconnected']}→{mst['p000_unconnected']}. "
        f"Unconnected {bst['unconnected_items']}→{mst['unconnected_items']}. "
        f"Foreign {meas['min_clearance_mm']} mm vs {meas['min_clearance_item']}. "
        f"POWER {meas['min_power_vin_mm']} mm vs {meas['min_power_vin_item']}. "
        f"short/clearance/crossing/hole "
        f"{mst['shorting_items']}/{mst['clearance']}/{mst['tracks_crossing']}/{mst['hole_clearance']}. "
        f"hole_to_hole {mst['hole_to_hole']}. "
        f"GND islands {bst['gnd_zone_islands']}→{mst['gnd_zone_islands']} (waived). "
        f"Other non-GND gained: none. Four skirts, SIM_CLK, and SIM_RST not ripped or stacked. No other net."
    )
    finish("KEEP", reason, mst)


if __name__ == "__main__":
    main()
