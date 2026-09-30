#!/usr/bin/env python3
"""pass30bj — ONE attempt: leftover P0.05 only.

The closed island already joins U1.2 and J12.6 on the locked In1 run.
This pass names the leftover pad and measures pad-edge clearance to that
island with the same GetClearance method as pass30bh (P0.07 leftover).
If the gap is over 36 mm it does not route, does not add a via, and does
not write copper. DRC is kicad-cli JSON via final_pass30ba.run_drc, the
same gate as pass30bh / pass30bi. J9.2 (P0.07) is not routed.
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
spec = importlib.util.spec_from_file_location("p30bi", ROOT / "scripts" / "final_pass30bi.py")
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)
m = bi.m

BOARD = m.BOARD
REPORTS = m.REPORTS
REVIEW = m.REVIEW
NET = "P0.05"
LIMIT = 36.0
EXPECTED_HEAD = "d9a2468"
EXPECTED_BLOB = "7bcfe5791b156e426a2a0affefe938be4d39f8e6"
EXPECTED_SHA1 = "c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40"
EXPECTED_UNC = 51
EXPECTED_OPENS = 1
W = m.W

# Locked In1 corners of the closed U1.2/J12.6 run. Not a route.
P005 = [
    (47.40, 36.50),
    (47.40, 38.40),
    (57.05, 38.40),
    (57.05, 74.70),
    (22.51, 74.70),
    (22.51, 79.40),
    (18.70, 79.40),
    (18.70, 76.00),
]

SHAPE_NAMES = {
    int(pcbnew.PAD_SHAPE_CIRCLE): "circle",
    int(pcbnew.PAD_SHAPE_RECT): "rect",
    int(pcbnew.PAD_SHAPE_OVAL): "oval",
    int(pcbnew.PAD_SHAPE_ROUNDRECT): "roundrect",
    int(pcbnew.PAD_SHAPE_TRAPEZOID): "trapezoid",
    int(pcbnew.PAD_SHAPE_CHAMFERED_RECT): "chamfered_rect",
}


def r6(v: float) -> float:
    return round(v, 6)


def sha1_file() -> str:
    return hashlib.sha1(BOARD.read_bytes()).hexdigest()


def collect(board):
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != NET:
                continue
            layers = [lid for _, lid in m.LAYERS if p.IsOnLayer(lid)]
            items.append({
                "kind": "pad",
                "name": f"{fp.GetReference()}.{p.GetNumber()}",
                "ref": fp.GetReference(),
                "num": p.GetNumber(),
                "x": m.mm(p.GetPosition().x),
                "y": m.mm(p.GetPosition().y),
                "sx": m.mm(p.GetSize().x),
                "sy": m.mm(p.GetSize().y),
                "drill": m.mm(p.GetDrillSizeX()),
                "shape": int(p.GetShape()),
                "shape_name": SHAPE_NAMES.get(int(p.GetShape()), str(int(p.GetShape()))),
                "layers": layers,
                "layer_names": [board.GetLayerName(lid) for lid in layers],
                "obj": p,
            })
    for t in board.GetTracks():
        if t.GetNetname() != NET:
            continue
        if t.GetClass() == "PCB_VIA":
            layers = [lid for _, lid in m.LAYERS if t.IsOnLayer(lid)]
            items.append({
                "kind": "via",
                "name": f"via@{m.mm(t.GetPosition().x):.3f},{m.mm(t.GetPosition().y):.3f}",
                "x": m.mm(t.GetPosition().x),
                "y": m.mm(t.GetPosition().y),
                "layers": layers,
                "layer_names": [board.GetLayerName(lid) for lid in layers],
                "obj": t,
                "w": m.mm(t.GetWidth(m.F)),
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
                "layer_names": [board.GetLayerName(t.GetLayer())],
                "obj": t,
                "a": (m.mm(t.GetStart().x), m.mm(t.GetStart().y)),
                "b": (m.mm(t.GetEnd().x), m.mm(t.GetEnd().y)),
                "w": m.mm(t.GetWidth()),
            })
    return items


def shp(it, lid):
    if it["kind"] == "pad":
        return it["obj"].GetEffectiveShape(lid)
    if it["kind"] == "via":
        return pcbnew.SHAPE_CIRCLE(
            m.xy(it["x"], it["y"]),
            pcbnew.FromMM(m.mm(it["obj"].GetWidth(lid)) / 2),
        )
    return pcbnew.SHAPE_SEGMENT(it["obj"].GetStart(), it["obj"].GetEnd(), it["obj"].GetWidth())


def touches(items, i, j) -> bool:
    for lid in set(items[i]["layers"]) & set(items[j]["layers"]):
        if m.mm(shp(items[i], lid).GetClearance(shp(items[j], lid))) <= 0.001:
            return True
    return False


def centerline_point(it, pad, lid):
    """Closest point on the copper center (segment, via, or circular pad)."""
    if it["kind"] == "trk":
        ax, ay = it["a"]
        bx, by = it["b"]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-18:
            return ax, ay
        t = max(0.0, min(1.0, ((pad["x"] - ax) * dx + (pad["y"] - ay) * dy) / L2))
        return ax + t * dx, ay + t * dy
    if it["kind"] == "via":
        return it["x"], it["y"]
    if it["kind"] == "pad":
        if it["shape_name"] != "circle" or abs(it["sx"] - it["sy"]) > 1e-6:
            raise SystemExit(f"nearest island pad {it['name']} is not a circle")
        return it["x"], it["y"]
    raise SystemExit(f"unknown kind {it['kind']}")


def copper_radius(it, lid) -> float:
    if it["kind"] == "trk":
        return it["w"] / 2
    if it["kind"] == "via":
        return m.mm(it["obj"].GetWidth(lid)) / 2
    if it["kind"] == "pad":
        return it["sx"] / 2
    raise SystemExit(f"unknown kind {it['kind']}")


def edge_pair(pad, it, lid):
    """Same chord construction as pass30bh: pad-edge to track-edge along the
    line from the pad center through the nearest centerline point."""
    if pad["shape_name"] != "circle" or abs(pad["sx"] - pad["sy"]) > 1e-6:
        raise SystemExit(f"leftover pad {pad['name']} is not a circular PTH")
    cx, cy = centerline_point(it, pad, lid)
    dx = pad["x"] - cx
    dy = pad["y"] - cy
    length_c = math.hypot(dx, dy)
    if length_c < 1e-9:
        raise SystemExit("pad center coincides with island copper center")
    ux, uy = dx / length_c, dy / length_c
    pr = pad["sx"] / 2
    tr = copper_radius(it, lid)
    p_pad = (pad["x"] - ux * pr, pad["y"] - uy * pr)
    p_trk = (cx + ux * tr, cy + uy * tr)
    chord = math.hypot(p_pad[0] - p_trk[0], p_pad[1] - p_trk[1])
    return {
        "corner": (cx, cy),
        "p_pad": p_pad,
        "p_trk": p_trk,
        "center_distance_mm": length_c,
        "chord": chord,
        "track_r": tr,
        "pad_r": pr,
    }


def measure_gap(board) -> dict:
    items = collect(board)
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
            if touches(items, i, j):
                union(i, j)

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.2")
    j12 = next(i for i, it in enumerate(items) if it["name"] == "J12.6")
    if find(u1) != find(j12):
        raise SystemExit("STOP: U1.2 and J12.6 are not one island")
    pads_off = [
        i for i, it in enumerate(items)
        if it["kind"] == "pad" and find(i) != find(u1)
    ]
    if len(pads_off) != 1:
        names = [items[i]["name"] for i in pads_off]
        raise SystemExit(f"STOP: expected one leftover P0.05 pad, found {names}")
    left = pads_off[0]
    best = None
    ties = []
    layer_of = {name: lid for name, lid in m.LAYERS}
    for name, lid in m.LAYERS:
        jsh = shp(items[left], lid)
        for i, it in enumerate(items):
            if find(i) != find(u1) or lid not in it["layers"]:
                continue
            c = m.mm(jsh.GetClearance(shp(it, lid)))
            rec = {
                "clearance_mm": c,
                "layer": name,
                "layer_id": lid,
                "item": it["name"],
                "kind": it["kind"],
                "index": i,
            }
            if best is None or c < best["clearance_mm"] - 1e-9:
                best = rec
                ties = [rec]
            elif abs(c - best["clearance_mm"]) <= 1e-9:
                ties.append(rec)
    pad = items[left]
    geos = []
    for rec in ties:
        it = items[rec["index"]]
        geo = edge_pair(pad, it, rec["layer_id"])
        if abs(geo["chord"] - rec["clearance_mm"]) > 0.002:
            raise SystemExit(
                f"nearest-point chord {geo['chord']} != GetClearance {rec['clearance_mm']} "
                f"for {rec['item']} on {rec['layer']}"
            )
        geos.append(geo)
    corners = { (round(g["corner"][0], 6), round(g["corner"][1], 6)) for g in geos }
    if len(corners) != 1:
        raise SystemExit(f"tied nearest items do not share one centerline point: {corners}")
    corner = geos[0]["corner"]
    # All ties share the clearance, so the pad-edge / track-edge points match.
    p_pad = geos[0]["p_pad"]
    p_trk = geos[0]["p_trk"]
    island_names = [items[i]["name"] for i in range(len(items)) if find(i) == find(u1)]
    return {
        "pad": pad,
        "gap_mm": best["clearance_mm"],
        "gap_layer": best["layer"],
        "near_item": best["item"],
        "ties": ties,
        "p_pad": p_pad,
        "p_track": p_trk,
        "corner": corner,
        "center_distance_mm": geos[0]["center_distance_mm"],
        "island_names": island_names,
        "same_closed_island": True,
        "n_items": len(items),
    }


def protect_ok(board) -> dict:
    ok = bi.protect_ok(board)
    ok["p005"] = m.poly_ok(board, P005, "P0.05", m.IN1)
    ok["p005_via"] = m.via_at(board, "P0.05", 47.40, 36.50)
    j92 = bi.j9_2_state(board)
    ok["j9_2"] = (
        j92.get("net") == "P0.07"
        and abs(j92.get("xy", [0, 0])[0] - 116.0) < 0.02
        and abs(j92.get("xy", [0, 0])[1] - 10.54) < 0.02
    )
    return ok, j92


def enrich(res):
    res["stats"]["p005_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
    return res


def write_outputs(head, blob, sha1, drc, gap, protect, j92):
    ts = m.ist_now()
    pad = gap["pad"]
    length = gap["gap_mm"]
    over = length > LIMIT
    decision = "NO-ROUTE"
    p_pad, p_trk = gap["p_pad"], gap["p_track"]
    corner = gap["corner"]
    end_blob = m.git_blob()
    end_sha = sha1_file()
    payload = {
        "pass": "30bj",
        "timestamp": ts,
        "kicad": "9.0.2",
        "decision": decision,
        "stopping_rule": "length",
        "routed": False,
        "copper_changed": False,
        "new_via": False,
        "segments": [],
        "segment_count": 0,
        "net": NET,
        "git_head": head,
        "pcb_blob_at_start": blob,
        "pcb_blob_at_end": end_blob,
        "sha1sum_at_start": sha1,
        "sha1sum_at_end": end_sha,
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "expected_sha1": EXPECTED_SHA1,
        "head_matches_expected": head.startswith(EXPECTED_HEAD),
        "blob_matches_expected": blob == EXPECTED_BLOB,
        "end_blob_matches_start": end_blob == blob,
        "precondition": {
            "unconnected": drc["unconnected_items"],
            "p005_opens": drc["p005_unconnected"],
            "required_unconnected": EXPECTED_UNC,
            "required_p005_opens": EXPECTED_OPENS,
            "ok": drc["unconnected_items"] == EXPECTED_UNC and drc["p005_unconnected"] == EXPECTED_OPENS,
        },
        "leftover_pad": {
            "refdes": f"{pad['ref']}.{pad['num']}",
            "center": [pad["x"], pad["y"]],
            "layers": pad["layer_names"],
            "shape": pad["shape_name"],
            "size_mm": [pad["sx"], pad["sy"]],
            "drill_mm": pad["drill"],
            "matches_prior_j9_3": (
                pad["ref"] == "J9" and pad["num"] == "3"
                and abs(pad["x"] - 116.0) < 0.02 and abs(pad["y"] - 13.08) < 0.02
            ),
        },
        "pad_edge_mm": r6(length),
        "pad_edge_exact_mm": length,
        "pad_edge_layer": gap["gap_layer"],
        "over_36_mm": over,
        "limit_mm": LIMIT,
        "nearest_copper": {
            "layer": gap["gap_layer"],
            "corner_xy": [r6(corner[0]), r6(corner[1])],
            "track_edge_xy": [r6(p_trk[0]), r6(p_trk[1])],
            "pad_edge_xy": [r6(p_pad[0]), r6(p_pad[1])],
            "center_distance_mm": r6(gap["center_distance_mm"]),
            "tied_items": [
                {
                    "clearance_mm": r6(t["clearance_mm"]),
                    "layer": t["layer"],
                    "item": t["item"],
                    "kind": t["kind"],
                }
                for t in gap["ties"]
            ],
            "note": (
                "Shared round cap of the locked In1 P0.05 run. "
                "Both adjoining segments return the same GetClearance."
            ),
        },
        "closed_island": gap["island_names"],
        "foreign_clearance_mm": None,
        "power_clearance_mm": None,
        "whole_segment_crossing_count": 0,
        "crossing_note": "No segments were laid. Crossing count is 0. No route was attempted.",
        "drc_before": {k: v for k, v in drc.items() if k != "nongnd"},
        "drc_after": {k: v for k, v in drc.items() if k != "nongnd"},
        "p005_opens_before": drc["p005_unconnected"],
        "p005_opens_after": drc["p005_unconnected"],
        "unconnected_before": drc["unconnected_items"],
        "unconnected_after": drc["unconnected_items"],
        "short": drc["shorting_items"],
        "clearance": drc["clearance"],
        "crossing": drc["tracks_crossing"],
        "hole": drc["hole_clearance"],
        "hole_to_hole": drc["hole_to_hole"],
        "gnd_islands": drc["gnd_zone_islands"],
        "locked_protect": protect,
        "locked_intact": all(protect.values()),
        "j9_2": j92,
        "j9_2_untouched": protect.get("j9_2") is True,
        "other_nets_touched": False,
        "backup": None,
        "gerbers": False,
        "commit": False,
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "PASS30BJ_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    tie_names = ", ".join(t["item"] for t in gap["ties"])
    lines = [
        "# PASS30BJ_SUMMARY — P0.05 leftover",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.05",
        f"**Git HEAD:** `{head}`",
        f"**PCB blob at start:** `{blob}`",
        f"**PCB blob at end:** `{end_blob}`",
        f"**sha1sum at start:** `{sha1}`",
        f"**sha1sum at end:** `{end_sha}`",
        "**Routed:** no",
        "**Copper changed:** no",
        "**New via:** no",
        "**New segments:** 0",
        f"**Stopping rule:** length (pad-edge {length:.6f} mm > {LIMIT:.0f} mm).",
        "",
        "## Preconditions",
        "",
        f"Live `kicad-cli` DRC (`run_drc`, same gate as pass30bh / pass30bi): unconnected **{drc['unconnected_items']}** "
        f"(required {EXPECTED_UNC}), P0.05 opens **{drc['p005_unconnected']}** (required {EXPECTED_OPENS}). "
        f"short/clearance/crossing/hole "
        f"{drc['shorting_items']}/{drc['clearance']}/{drc['tracks_crossing']}/{drc['hole_clearance']}. "
        f"hole_to_hole {drc['hole_to_hole']}. GND islands {drc['gnd_zone_islands']}. "
        "Counts matched, so the gap was measured. No copper was added. No backup (no edit).",
        "",
        "## Leftover pad",
        "",
        f"**{pad['ref']}.{pad['num']}** center ({pad['x']:.3f}, {pad['y']:.3f}), "
        f"{pad['shape_name']} PTH {pad['sx']:.3f} x {pad['sy']:.3f} mm, drill {pad['drill']:.3f} mm. "
        f"Copper on {', '.join(pad['layer_names'])}. "
        "This pad is its own island. U1.2 and J12.6 are already one island and were not ripped. "
        f"Prior report named J9.3 at (116.00, 13.08): "
        f"**{payload['leftover_pad']['matches_prior_j9_3']}**.",
        "",
        "## Pad-edge",
        "",
        f"Pad-edge to the nearest copper on the closed U1.2/J12.6 island: **{length:.6f} mm** "
        f"on {gap['gap_layer']}. "
        f"`GetClearance` from {pad['ref']}.{pad['num']} to the locked In1 run. "
        f"The minimum is shared by {tie_names} "
        f"because both end on the round cap at ({corner[0]:.2f}, {corner[1]:.2f}). "
        f"Track-edge point ({p_trk[0]:.6f}, {p_trk[1]:.6f}), "
        f"pad-edge point ({p_pad[0]:.6f}, {p_pad[1]:.6f}). "
        f"Center distance to that corner {gap['center_distance_mm']:.6f} mm. "
        f"**Over the {LIMIT:.0f} mm cap.** Same length rule as pass30bh (J9.2 was 58.617 mm and was not routed). "
        "No route attempted.",
        "",
        "## Why no route",
        "",
        f"Rule that stopped the pass: **length**. Pad-edge {length:.6f} mm is over 36 mm. "
        "No segments were laid, so there is no foreign clearance, no POWER clearance, and no new via. "
        "Whole-segment crossing count: 0 (no segments). "
        "The locked P0.05 In1 run was not ripped and nothing was stacked on its centerline. "
        "P0.07, P0.00, SIM_RST, SIM_CLK, and the four skirts were not ripped or stacked. "
        "J9.2 (P0.07) was not touched and stays open. "
        "Skirt slot, sealed pocket, and RF keepout were not entered. "
        "No second path. No other net. No Gerbers. No git commit.",
        "",
        "## Locked copper check (read only)",
        "",
        "```",
        json.dumps(protect, indent=2),
        "```",
        "",
        f"J9.2: `{json.dumps(j92)}`.",
        "",
        f"All locked checks true: **{all(protect.values())}**.",
        "",
        "## DRC (unchanged board)",
        "",
        "| | unconnected | P0.05 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {drc['unconnected_items']} | {drc['p005_unconnected']} | {drc['shorting_items']} | "
        f"{drc['clearance']} | {drc['tracks_crossing']} | {drc['hole_clearance']} | "
        f"{drc['hole_to_hole']} | {drc['gnd_zone_islands']} |",
        f"| after | {drc['unconnected_items']} | {drc['p005_unconnected']} | {drc['shorting_items']} | "
        f"{drc['clearance']} | {drc['tracks_crossing']} | {drc['hole_clearance']} | "
        f"{drc['hole_to_hole']} | {drc['gnd_zone_islands']} |",
        "",
        "No mid DRC: copper was not edited. AFTER is a copy of BEFORE. "
        f"End blob matches start blob: **{end_blob == blob}**.",
        "",
    ]
    (REPORTS / "PASS30BJ_SUMMARY.md").write_text("\n".join(lines) + "\n")
    paragraph = (
        f"\n## Pass30bj — P0.05 {pad['ref']}.{pad['num']} leftover, no route — {ts}\n\n"
        "**Decision:** **NO-ROUTE**. No copper. No via. No backup. "
        f"Stopping rule: length. Pad-edge **{length:.6f} mm** on {gap['gap_layer']} "
        f"(limit 36 mm, over the cap). Leftover pad {pad['ref']}.{pad['num']} "
        f"center ({pad['x']:.3f}, {pad['y']:.3f}), {pad['shape_name']} PTH "
        f"{pad['sx']:.3f} mm, drill {pad['drill']:.3f} mm, copper on "
        f"{', '.join(pad['layer_names'])}. Nearest closed-island copper is the locked In1 "
        f"round cap at ({corner[0]:.2f}, {corner[1]:.2f}), track-edge "
        f"({p_trk[0]:.3f}, {p_trk[1]:.3f}) to pad-edge ({p_pad[0]:.3f}, {p_pad[1]:.3f}). "
        "Closed U1.2/J12.6 run not ripped and not stacked. "
        "P0.07, P0.00, SIM_RST, SIM_CLK, and the four skirts not touched. "
        f"J9.2 still {j92.get('net')} at {j92.get('xy')}; not touched, stays open. "
        f"Unconnected {drc['unconnected_items']}→{drc['unconnected_items']}. "
        f"P0.05 opens {drc['p005_unconnected']}→{drc['p005_unconnected']}. "
        f"short/clearance/crossing/hole {drc['shorting_items']}/{drc['clearance']}/"
        f"{drc['tracks_crossing']}/{drc['hole_clearance']}. "
        f"hole_to_hole {drc['hole_to_hole']}. GND islands {drc['gnd_zone_islands']}. "
        "No other net. No Gerbers. No commit.\n"
    )
    REVIEW.write_text(REVIEW.read_text() + paragraph)
    return payload


def main():
    head = m.git_head()
    blob = m.git_blob()
    sha1 = sha1_file()
    print("HEAD", head, "BLOB", blob, "SHA1", sha1, flush=True)
    if not head.startswith(EXPECTED_HEAD) or blob != EXPECTED_BLOB or sha1 != EXPECTED_SHA1:
        raise SystemExit(f"STOP mismatch head={head} blob={blob} sha1={sha1}")

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BJ_BEFORE.json"))
    st = before["stats"]
    print("BEFORE", {k: v for k, v in st.items() if k != "nongnd"}, flush=True)
    if st["unconnected_items"] != EXPECTED_UNC or st["p005_unconnected"] != EXPECTED_OPENS:
        raise SystemExit(
            f"STOP mismatch unconnected={st['unconnected_items']} "
            f"P0.05 opens={st['p005_unconnected']}"
        )
    if m.git_blob() != blob:
        raise SystemExit("STOP: blob changed during DRC")

    board = pcbnew.LoadBoard(str(BOARD))
    gap = measure_gap(board)
    protect, j92 = protect_ok(board)
    print(
        "PAD", f"{gap['pad']['ref']}.{gap['pad']['num']}",
        gap["pad"]["x"], gap["pad"]["y"],
        "size", gap["pad"]["sx"], gap["pad"]["sy"],
        "drill", gap["pad"]["drill"],
        gap["pad"]["layer_names"],
        "EDGE", gap["gap_mm"], "over36", gap["gap_mm"] > LIMIT,
        "corner", gap["corner"],
        flush=True,
    )
    print("TIES", [(t["item"], t["layer"], t["clearance_mm"]) for t in gap["ties"]], flush=True)
    print("PROTECT", protect, flush=True)
    print("J9.2", j92, flush=True)
    if not (gap["gap_mm"] > LIMIT):
        raise SystemExit(
            f"STOP: pad-edge {gap['gap_mm']} mm is not over 36 mm. "
            "This script only records the length-cap NO-ROUTE. No copper was added."
        )
    if not all(protect.values()):
        raise SystemExit(f"STOP: locked copper missing before any decision: {protect}")

    shutil.copy2(REPORTS / "DRC_PASS30BJ_BEFORE.json", REPORTS / "DRC_PASS30BJ_AFTER.json")
    if m.git_blob() != blob:
        raise SystemExit("STOP: blob changed before the report write")
    payload = write_outputs(head, blob, sha1, st, gap, protect, j92)
    if m.git_blob() != EXPECTED_BLOB:
        raise SystemExit(f"STOP: end blob {m.git_blob()} != start")
    print("DECISION", payload["decision"], "edge", payload["pad_edge_exact_mm"], flush=True)


if __name__ == "__main__":
    main()
