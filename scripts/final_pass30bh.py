#!/usr/bin/env python3
"""pass30bh — ONE attempt: leftover P0.07 only.

The closed island already joins U1.4 and J12.8 on the locked In2 run.
This pass names the leftover pad and measures pad-edge clearance to that
island with the same GetClearance method as the P0.17 leftover (pass30az).
If the gap is over 36 mm it does not route, does not add a via, and does
not write copper. DRC is kicad-cli JSON via final_pass30ba.run_drc, the
same gate as pass30bg. P0.05 is not routed.
"""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
spec = importlib.util.spec_from_file_location("p30bg", ROOT / "scripts" / "final_pass30bg.py")
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)
m = bg.m

BOARD = m.BOARD
REPORTS = m.REPORTS
REVIEW = m.REVIEW
NET = "P0.07"
LIMIT = 36.0
EXPECTED_HEAD = "bed9dc7"
EXPECTED_BLOB = "953e98bc52f2b39ffec50928389f4492eff69ce7"
EXPECTED_UNC = 52
EXPECTED_OPENS = 1
W = m.W

# Locked In2 corner of the closed U1.4/J12.8 run. Not a route.
CORNER = (63.10, 37.90)


def r6(v: float) -> float:
    return round(v, 6)


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

    u1 = next(i for i, it in enumerate(items) if it["name"] == "U1.4")
    j12 = next(i for i, it in enumerate(items) if it["name"] == "J12.8")
    if find(u1) != find(j12):
        raise SystemExit("STOP: U1.4 and J12.8 are not one island")
    pads_off = [
        i for i, it in enumerate(items)
        if it["kind"] == "pad" and find(i) != find(u1)
    ]
    if len(pads_off) != 1:
        raise SystemExit(f"STOP: expected one leftover P0.07 pad, found {len(pads_off)}")
    left = pads_off[0]
    best = None
    ties = []
    for name, lid in m.LAYERS:
        jsh = shp(items[left], lid)
        for i, it in enumerate(items):
            if find(i) != find(u1) or lid not in it["layers"]:
                continue
            c = m.mm(jsh.GetClearance(shp(it, lid)))
            rec = {"clearance_mm": c, "layer": name, "item": it["name"], "kind": it["kind"]}
            if best is None or c < best["clearance_mm"] - 1e-9:
                best = rec
                ties = [rec]
            elif abs(c - best["clearance_mm"]) <= 1e-9:
                ties.append(rec)
    pad = items[left]
    # Circular PTH: nearest copper is along the line from the pad center to
    # the locked In2 corner (63.10, 37.90), which is the shared round cap of
    # the two winning segments.
    dx = pad["x"] - CORNER[0]
    dy = pad["y"] - CORNER[1]
    length_c = math.hypot(dx, dy)
    ux, uy = dx / length_c, dy / length_c
    pr = pad["sx"] / 2
    tr = W / 2
    p_pad = (pad["x"] - ux * pr, pad["y"] - uy * pr)
    p_trk = (CORNER[0] + ux * tr, CORNER[1] + uy * tr)
    chord = math.hypot(p_pad[0] - p_trk[0], p_pad[1] - p_trk[1])
    if abs(chord - best["clearance_mm"]) > 0.002:
        raise SystemExit(
            f"nearest-point chord {chord} != GetClearance {best['clearance_mm']}"
        )
    island_names = [items[i]["name"] for i in range(len(items)) if find(i) == find(u1)]
    return {
        "pad": pad,
        "gap_mm": best["clearance_mm"],
        "gap_layer": best["layer"],
        "near_item": best["item"],
        "ties": ties,
        "p_pad": p_pad,
        "p_track": p_trk,
        "center_distance_mm": length_c,
        "island_names": island_names,
        "same_closed_island": True,
    }


def named_p005(board) -> dict:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        if abs(m.mm(t.GetPosition().x) - 47.40) > 0.001:
            continue
        if abs(m.mm(t.GetPosition().y) - 36.50) > 0.001:
            continue
        return {
            "net": t.GetNetname(),
            "xy": [m.mm(t.GetPosition().x), m.mm(t.GetPosition().y)],
            "width_mm": m.mm(t.GetWidth(m.F)),
            "drill_mm": m.mm(t.GetDrillValue()),
        }
    return {}


def enrich(res):
    res["stats"]["p007_unconnected"] = res["stats"]["nongnd"].get(NET, 0)
    return res


def write_outputs(head, blob, sha1, drc, gap, protect, via):
    ts = m.ist_now()
    pad = gap["pad"]
    length = gap["gap_mm"]
    over = length > LIMIT
    decision = "NO-ROUTE"
    p_pad, p_trk = gap["p_pad"], gap["p_track"]
    payload = {
        "pass": "30bh",
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
        "pcb_blob_at_end": m.git_blob(),
        "sha1sum_at_start": sha1,
        "sha1sum_at_end": __import__("hashlib").sha1(BOARD.read_bytes()).hexdigest(),
        "expected_head_prefix": EXPECTED_HEAD,
        "expected_blob": EXPECTED_BLOB,
        "head_matches_expected": head.startswith(EXPECTED_HEAD),
        "blob_matches_expected": blob == EXPECTED_BLOB,
        "end_blob_matches_start": m.git_blob() == blob,
        "precondition": {
            "unconnected": drc["unconnected_items"],
            "p007_opens": drc["p007_unconnected"],
            "required_unconnected": EXPECTED_UNC,
            "required_p007_opens": EXPECTED_OPENS,
            "ok": drc["unconnected_items"] == EXPECTED_UNC and drc["p007_unconnected"] == EXPECTED_OPENS,
        },
        "leftover_pad": {
            "refdes": f"{pad['ref']}.{pad['num']}",
            "center": [pad["x"], pad["y"]],
            "layers": pad["layer_names"],
            "shape": "circle",
            "size_mm": [pad["sx"], pad["sy"]],
            "drill_mm": pad["drill"],
        },
        "pad_edge_mm": r6(length),
        "pad_edge_exact_mm": length,
        "pad_edge_layer": gap["gap_layer"],
        "over_36_mm": over,
        "limit_mm": LIMIT,
        "nearest_copper": {
            "layer": gap["gap_layer"],
            "corner_xy": list(CORNER),
            "track_edge_xy": [r6(p_trk[0]), r6(p_trk[1])],
            "pad_edge_xy": [r6(p_pad[0]), r6(p_pad[1])],
            "tied_items": gap["ties"],
            "note": (
                "Shared round cap of the locked In2 run at (63.10, 37.90). "
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
        "p007_opens_before": drc["p007_unconnected"],
        "p007_opens_after": drc["p007_unconnected"],
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
        "p005_via": via,
        "p005_untouched": via.get("net") == "P0.05",
        "other_nets_touched": False,
        "backup": None,
        "gerbers": False,
        "commit": False,
    }
    # ties contain raw floats; make JSON stable
    payload["nearest_copper"]["tied_items"] = [
        {
            "clearance_mm": r6(t["clearance_mm"]),
            "layer": t["layer"],
            "item": t["item"],
            "kind": t["kind"],
        }
        for t in gap["ties"]
    ]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "PASS30BH_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        "# PASS30BH_SUMMARY — P0.07 leftover",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** P0.07",
        f"**Git HEAD:** `{head}`",
        f"**PCB blob at start:** `{blob}`",
        f"**PCB blob at end:** `{payload['pcb_blob_at_end']}`",
        f"**sha1sum at start:** `{sha1}`",
        f"**sha1sum at end:** `{payload['sha1sum_at_end']}`",
        "**Routed:** no",
        "**Copper changed:** no",
        "**New via:** no",
        "**New segments:** 0",
        f"**Stopping rule:** length (pad-edge {length:.6f} mm > {LIMIT:.0f} mm).",
        "",
        "## Preconditions",
        "",
        f"Live `kicad-cli` DRC (`run_drc`, same gate as pass30bg): unconnected **{drc['unconnected_items']}** "
        f"(required {EXPECTED_UNC}), P0.07 opens **{drc['p007_unconnected']}** (required {EXPECTED_OPENS}). "
        f"short/clearance/crossing/hole "
        f"{drc['shorting_items']}/{drc['clearance']}/{drc['tracks_crossing']}/{drc['hole_clearance']}. "
        f"hole_to_hole {drc['hole_to_hole']}. GND islands {drc['gnd_zone_islands']}. "
        "Counts matched, so the gap was measured. No copper was added. No backup (no edit).",
        "",
        "## Leftover pad",
        "",
        f"**{pad['ref']}.{pad['num']}** center ({pad['x']:.3f}, {pad['y']:.3f}), "
        f"circular PTH {pad['sx']:.3f} mm, drill {pad['drill']:.3f} mm. "
        f"Copper on {', '.join(pad['layer_names'])}. "
        "This pad is its own island. U1.4 and J12.8 are already one island and were not ripped.",
        "",
        "## Pad-edge",
        "",
        f"Pad-edge to the nearest copper on the closed U1.4/J12.8 island: **{length:.6f} mm** "
        f"on {gap['gap_layer']}. "
        f"`GetClearance` from {pad['ref']}.{pad['num']} to the locked In2 run. "
        f"The minimum is shared by {', '.join(t['item'] for t in gap['ties'])} "
        f"because both end on the round cap at ({CORNER[0]:.2f}, {CORNER[1]:.2f}). "
        f"Track-edge point ({p_trk[0]:.6f}, {p_trk[1]:.6f}), "
        f"pad-edge point ({p_pad[0]:.6f}, {p_pad[1]:.6f}). "
        f"Center distance to that corner {gap['center_distance_mm']:.6f} mm. "
        f"**Over the {LIMIT:.0f} mm cap.** Same length rule as the P0.17 leftover. No route attempted.",
        "",
        "## Why no route",
        "",
        f"Rule that stopped the pass: **length**. Pad-edge {length:.6f} mm is over 36 mm. "
        "No segments were laid, so there is no foreign clearance, no POWER clearance, and no new via. "
        "Whole-segment crossing count: 0 (no segments). "
        "The locked P0.07 In2 run was not ripped and nothing was stacked on its centerline. "
        "P0.00, SIM_RST, SIM_CLK, and the four skirts were not ripped or stacked. "
        f"P0.05 via at (47.40, 36.50) is still net {via.get('net')} and was not routed. "
        "Skirt slot, sealed pocket, and RF keepout were not entered. "
        "No second path. No other net. No Gerbers. No git commit.",
        "",
        "## Locked copper check (read only)",
        "",
        "```",
        json.dumps(protect, indent=2),
        "```",
        "",
        f"All locked checks true: **{all(protect.values())}**.",
        "",
        "## DRC (unchanged board)",
        "",
        "| | unconnected | P0.07 | short | clearance | crossing | hole | hole_to_hole | GND islands |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| before | {drc['unconnected_items']} | {drc['p007_unconnected']} | {drc['shorting_items']} | "
        f"{drc['clearance']} | {drc['tracks_crossing']} | {drc['hole_clearance']} | "
        f"{drc['hole_to_hole']} | {drc['gnd_zone_islands']} |",
        f"| after | {drc['unconnected_items']} | {drc['p007_unconnected']} | {drc['shorting_items']} | "
        f"{drc['clearance']} | {drc['tracks_crossing']} | {drc['hole_clearance']} | "
        f"{drc['hole_to_hole']} | {drc['gnd_zone_islands']} |",
        "",
        "No mid DRC: copper was not edited. AFTER is a copy of BEFORE. "
        f"End blob matches start blob: **{payload['end_blob_matches_start']}**.",
        "",
    ]
    (REPORTS / "PASS30BH_SUMMARY.md").write_text("\n".join(lines) + "\n")
    paragraph = (
        f"\n## Pass30bh — P0.07 {pad['ref']}.{pad['num']} leftover, no route — {ts}\n\n"
        "**Decision:** **NO-ROUTE**. No copper. No via. No backup. "
        f"Stopping rule: length. Pad-edge **{length:.6f} mm** on {gap['gap_layer']} "
        f"(limit 36 mm, over the cap). Leftover pad {pad['ref']}.{pad['num']} "
        f"center ({pad['x']:.3f}, {pad['y']:.3f}), circular PTH, copper on "
        f"{', '.join(pad['layer_names'])}. Nearest closed-island copper is the locked In2 "
        f"round cap at ({CORNER[0]:.2f}, {CORNER[1]:.2f}), track-edge "
        f"({p_trk[0]:.3f}, {p_trk[1]:.3f}) to pad-edge ({p_pad[0]:.3f}, {p_pad[1]:.3f}). "
        "Closed U1.4/J12.8 run not ripped and not stacked. "
        "P0.00, SIM_RST, SIM_CLK, and the four skirts not touched. "
        f"P0.05 via (47.40, 36.50) still {via.get('net')}; not routed. "
        f"Unconnected {drc['unconnected_items']}→{drc['unconnected_items']}. "
        f"P0.07 opens {drc['p007_unconnected']}→{drc['p007_unconnected']}. "
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
    sha1 = __import__("hashlib").sha1(BOARD.read_bytes()).hexdigest()
    print("HEAD", head, "BLOB", blob, "SHA1", sha1, flush=True)
    if not head.startswith(EXPECTED_HEAD) or blob != EXPECTED_BLOB:
        raise SystemExit(f"STOP mismatch head={head} blob={blob} sha1={sha1}")

    before = enrich(m.run_drc(REPORTS / "DRC_PASS30BH_BEFORE.json"))
    st = before["stats"]
    print("BEFORE", {k: v for k, v in st.items() if k != "nongnd"}, flush=True)
    if st["unconnected_items"] != EXPECTED_UNC or st["p007_unconnected"] != EXPECTED_OPENS:
        raise SystemExit(
            f"STOP mismatch unconnected={st['unconnected_items']} "
            f"P0.07 opens={st['p007_unconnected']}"
        )

    board = pcbnew.LoadBoard(str(BOARD))
    gap = measure_gap(board)
    protect = bg.protect_ok(board)
    via = named_p005(board)
    print(
        "PAD", f"{gap['pad']['ref']}.{gap['pad']['num']}",
        gap["pad"]["x"], gap["pad"]["y"], gap["pad"]["layer_names"],
        "EDGE", gap["gap_mm"], "over36", gap["gap_mm"] > LIMIT,
        flush=True,
    )
    print("PROTECT", protect, flush=True)
    print("P005", via, flush=True)
    if not (gap["gap_mm"] > LIMIT):
        raise SystemExit(
            f"STOP: pad-edge {gap['gap_mm']} mm is not over 36 mm. "
            "This script only records the length-cap NO-ROUTE. No copper was added."
        )
    if not all(protect.values()):
        raise SystemExit(f"STOP: locked copper missing before any decision: {protect}")
    if via.get("net") != "P0.05":
        raise SystemExit(f"STOP: via (47.40, 36.50) is {via}, not P0.05")

    shutil.copy2(REPORTS / "DRC_PASS30BH_BEFORE.json", REPORTS / "DRC_PASS30BH_AFTER.json")
    if m.git_blob() != blob:
        raise SystemExit("STOP: blob changed before the report write")
    payload = write_outputs(head, blob, sha1, st, gap, protect, via)
    if m.git_blob() != EXPECTED_BLOB:
        raise SystemExit(f"STOP: end blob {m.git_blob()} != start")
    print("DECISION", payload["decision"], "edge", payload["pad_edge_exact_mm"], flush=True)


if __name__ == "__main__":
    main()
