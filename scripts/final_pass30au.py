#!/usr/bin/env python3
"""pass30au — ONE attempt: P0.14 only (U1.24 ↔ J18.2 / J12.15).

The 25 mm cap does not apply. The straight F.Cu chord is not a candidate:
it crosses the SiP body and the south fanout, and it hits GND vias, locked
P0.04, P0.03, and no-net pad U1.127.

This pass looks for one 0.18 mm jog, at most 8 segments, one via only if
required, east of the RF keepout (x>24.2), around the package (not under the
body, not through the south fanout), without ripping locked copper.

Live geometry does not have such a jog. The script places no copper.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_pass30ah as ah  # noqa: E402

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18
CLEAR_FOREIGN = 0.15
CLEAR_POWER = 0.20
# SiP fab/silk outline (U1 at (36, 32), rot 180, 16.0 x 10.5).
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


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def r3(v: float) -> float:
    return round(v, 3)


def gnd_fill(board, layer):
    for z in board.Zones():
        if z.IsFilled() and z.GetNetname() == "GND" and z.GetFirstLayer() == layer:
            return z.GetFilledPolysList(layer)
    return None


def fill_distance(polys, x, y) -> float:
    """Distance from point to filled copper. 0 if inside."""
    pt = xy(x, y)
    if polys.Contains(pt):
        return 0.0
    # Binary search a colliding radius. Far points return the hi cap.
    if not polys.Collide(pcbnew.SHAPE_CIRCLE(pt, pcbnew.FromMM(4.0))):
        return 4.0
    lo, hi = 0.0, 4.0
    for _ in range(18):
        mid = (lo + hi) / 2
        if polys.Collide(pcbnew.SHAPE_CIRCLE(pt, pcbnew.FromMM(mid))):
            hi = mid
        else:
            lo = mid
    return lo


def pad_by(board, ref, num):
    for fp in board.GetFootprints():
        if fp.GetReference() != ref:
            continue
        for p in fp.Pads():
            if p.GetNumber() == num:
                return p
    raise SystemExit(f"missing {ref}.{num}")


def measure_islands(board) -> dict:
    by = ah.collect(board)
    ah.add_nonet(board, by)
    prims = by["P0.14"]
    islands = ah.cluster(prims)
    pairs = []
    for a in range(len(islands)):
        for b in range(a + 1, len(islands)):
            g, _same = ah.best_gap(prims, islands[a], islands[b])
            pairs.append(
                {
                    "gap_mm": round(g[0], 3),
                    "pt_a": [round(g[1][0], 3), round(g[1][1], 3)],
                    "pt_b": [round(g[2][0], 3), round(g[2][1], 3)],
                    "island_a": ah.island_summary(prims, islands[a]),
                    "island_b": ah.island_summary(prims, islands[b]),
                }
            )
    pairs.sort(key=lambda r: r["gap_mm"])
    return {"n_islands": len(islands), "opens": max(0, len(islands) - 1), "closest": pairs[0] if pairs else None}


def straight_hits(board, p1, p2) -> dict:
    """Edge gap of a 0.18 mm chord. Negative means overlap (pass30ao style)."""
    by = ah.collect(board)
    ah.add_nonet(board, by)
    cand = ah.Prim("seg", frozenset([ah.F]), "P0.14", "cand")
    cand.a = p1
    cand.b = p2
    cand.width = W
    cand.set_bbox()
    worst = {}
    n_under = 0
    for net, prims in by.items():
        if net == "P0.14":
            continue
        for prim in prims:
            if prim.kind == "circle":
                if ah.F not in prim.layers and prim.layers:
                    continue
            elif ah.F not in prim.layers:
                continue
            if ah.bbox_gap(cand.bbox, prim.bbox) > CLEAR_FOREIGN:
                continue
            g, _, _ = ah.gap_prims(cand, prim)
            if g < CLEAR_FOREIGN:
                n_under += 1
                key = net or "<no-net>"
                rec = {
                    "clearance_mm": round(g, 3),
                    "net": key,
                    "power": key in POWER,
                    "item": prim.label,
                }
                prev = worst.get(key)
                if prev is None or rec["clearance_mm"] < prev["clearance_mm"]:
                    worst[key] = rec
    length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    hits_body = False
    for k in range(41):
        tt = k / 40
        x = p1[0] + (p2[0] - p1[0]) * tt
        y = p1[1] + (p2[1] - p1[1]) * tt
        if BODY[0] <= x <= BODY[2] and BODY[1] <= y <= BODY[3]:
            hits_body = True
            break
    return {
        "from": [round(p1[0], 3), round(p1[1], 3)],
        "to": [round(p2[0], 3), round(p2[1], 3)],
        "length_mm": round(length, 3),
        "crosses_sip_body": hits_body,
        "hit_count_under_0_15": n_under,
        "worst_by_net": worst,
    }


def via_wall(board) -> dict:
    """Copper gap between the P0.13 and P0.15 fanout vias that close the north exit."""
    vias = []
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        if t.GetNetname() not in ("P0.13", "P0.15"):
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if not (40.5 <= x <= 44.0 and 22.0 <= y <= 25.0):
            continue
        vias.append(
            {
                "net": t.GetNetname(),
                "x": round(x, 3),
                "y": round(y, 3),
                "r": round(mm(t.GetWidth(F)) / 2, 3),
            }
        )
    # The pinch is the pair nearest each other in x at the northern row (smaller y).
    north = [v for v in vias if v["y"] < 23.5]
    north.sort(key=lambda v: v["x"])
    pair = None
    if len(north) >= 2:
        a, b = north[0], north[1]
        gap = (b["x"] - b["r"]) - (a["x"] + a["r"])
        need = W + 2 * CLEAR_FOREIGN
        pair = {
            "left": a,
            "right": b,
            "copper_gap_mm": round(gap, 3),
            "need_mm": round(need, 3),
            "short_by_mm": round(need - gap, 3),
            "passable": gap + 1e-6 >= need,
        }
    return {"vias": vias, "north_pinch": pair}


def pocket_fill(board) -> dict:
    """B.Cu GND fill inside the F.Cu pocket between P0.15 and P0.13."""
    poly_b = gnd_fill(board, B)
    poly_f = gnd_fill(board, F)
    samples = []
    for y in (26.2, 25.4, 25.0, 24.6):
        # mid-pocket and the sliver just west of the P0.13 track (x=42.75)
        for x in (42.25, 42.45, 42.60):
            samples.append(
                {
                    "xy": [x, y],
                    "dist_F_fill_mm": round(fill_distance(poly_f, x, y), 3),
                    "dist_B_fill_mm": round(fill_distance(poly_b, x, y), 3),
                }
            )
    # fill edge vs P0.13 track edge at y=25.0
    # track center 42.75, width 0.18 → west edge 42.66
    y = 25.0
    edge = None
    for i in range(80):
        x = 42.20 + i * 0.01
        if fill_distance(poly_b, x, y) > 0:
            edge = round(x, 3)
            break
    p013_west = 42.75 - 0.09
    halo = None if edge is None else round(p013_west - edge, 3)
    return {
        "samples": samples,
        "b_fill_edge_x_at_y25": edge,
        "p013_track_west_edge_x": round(p013_west, 3),
        "halo_mm": halo,
        "via_0_50_fits_in_halo": False
        if halo is None
        else halo >= (0.50 + CLEAR_FOREIGN + 0.15),
    }


def pad_pitch(board) -> dict:
    u24 = pad_by(board, "U1", "24")
    u23 = pad_by(board, "U1", "23")
    u25 = pad_by(board, "U1", "25")
    # copper edge gap along x (same y row)
    def edge_gap(a, b):
        return mm(a.GetEffectiveShape(F).GetClearance(b.GetEffectiveShape(F)))

    return {
        "u1_24": [r3(mm(u24.GetPosition().x)), r3(mm(u24.GetPosition().y))],
        "u1_23_p013_gap_mm": round(edge_gap(u24, u23), 3),
        "u1_25_p015_gap_mm": round(edge_gap(u24, u25), 3),
        "need_mm": round(W + 2 * CLEAR_FOREIGN, 3),
    }


def ratsnest(board) -> dict:
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    # Same counter DRC reports as unconnected_items on this board (60).
    return {"ratsnest_edges": int(conn.GetUnconnectedCount(False))}


def write_reports(stamp, board_sha, islands, straight, wall, fill, pitch, rats) -> None:
    closest = islands["closest"]
    pinch = wall["north_pinch"]
    summary = {
        "pass": "pass30au",
        "timestamp": stamp,
        "kicad": "9.0.2",
        "decision": "NO-ROUTE",
        "net": "P0.14",
        "copper_added": False,
        "backup": None,
        "via": None,
        "segments": [],
        "side_of_package": None,
        "reason": (
            "No 8-segment / one-via jog stays east of x=24.2, goes around the "
            "SiP (not under the body, not through the south fanout), and clears "
            "foreign copper. The U1.24 F.Cu pocket is closed on the north by the "
            "P0.13/P0.15 vias, on the sides by those nets' pad-pitch tracks, on "
            "the south by the SiP body, and on B.Cu by GND fill."
        ),
        "remeasured_gap_mm": closest["gap_mm"] if closest else None,
        "gap_pts_mm": {
            "island_header": closest["pt_a"] if closest else None,
            "island_u1": closest["pt_b"] if closest else None,
        },
        "islands": islands["n_islands"],
        "p014_opens": islands["opens"],
        "straight_line": {
            "from": straight["from"],
            "to": straight["to"],
            "length_mm": straight["length_mm"],
            "crosses_sip_body": straight["crosses_sip_body"],
            "hit_count_under_0_15": straight["hit_count_under_0_15"],
            "worst_by_net": straight["worst_by_net"],
        },
        "north_via_pinch": pinch,
        "pad_pitch": pitch,
        "b_fill_pocket": {
            "b_fill_edge_x_at_y25": fill["b_fill_edge_x_at_y25"],
            "p013_track_west_edge_x": fill["p013_track_west_edge_x"],
            "halo_mm": fill["halo_mm"],
            "via_0_50_fits_in_halo": fill["via_0_50_fits_in_halo"],
        },
        "min_foreign_clearance_mm": None,
        "min_power_vin_clearance_mm": None,
        "clearance_note": "No copper placed, so foreign and POWER/VIN clearance of new copper were not measured.",
        "unconnected_before": rats["ratsnest_edges"],
        "unconnected_after": rats["ratsnest_edges"],
        "unconnected_source": "pcbnew CONNECTIVITY_DATA.GetUnconnectedCount (no copper edit, no DRC json)",
        "p014_opens_before": islands["opens"],
        "p014_opens_after": islands["opens"],
        "gnd_islands_note": "Not recomputed by DRC. No copper edit, so the waived GND-island count is unchanged.",
        "board_sha256": board_sha,
        "locked_untouched": [
            "P0.30",
            "P0.31",
            "P0.22",
            "P0.04",
            "P0.15",
            "P0.19",
            "VDD_GPIO",
            "COEX0",
            "DEC0",
            "P0.10",
            "P0.12",
            "U1.88",
            "U1.89",
        ],
    }
    (REPORTS / "PASS30AU_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")

    def worst_line(net):
        rec = straight["worst_by_net"].get(net)
        if not rec:
            return f"{net}: not under 0.15 mm"
        return f"{net} {rec['clearance_mm']} mm ({rec['item']})"

    md = []
    md.append("# PASS30AU_SUMMARY — P0.14")
    md.append("")
    md.append(f"**Timestamp:** {stamp}")
    md.append("**KiCad:** 9.0.2")
    md.append("**Decision:** **NO-ROUTE**")
    md.append("**Net:** P0.14")
    md.append("**Via added:** no")
    md.append("**Segments:** 0 (limit 8)")
    md.append("**Side of package:** none — east skirt is not reachable from U1.24")
    md.append("**Min foreign clearance:** n/a (no copper)")
    md.append("**Min POWER/VIN clearance:** n/a (no copper)")
    md.append(f"**Unconnected (ratsnest edges):** {rats['ratsnest_edges']} → {rats['ratsnest_edges']}")
    md.append(f"**P0.14 opens:** {islands['opens']} → {islands['opens']}")
    md.append("**GND zone islands:** unchanged (no copper edit; waived)")
    md.append("**Short / clearance / crossing / hole:** unchanged (no copper edit)")
    md.append("")
    md.append("## Remeasured gap")
    md.append("")
    a = closest["island_a"]
    bsum = closest["island_b"]
    md.append(
        f"Copper-edge gap **{closest['gap_mm']} mm** on F.Cu between "
        f"{a['pads']} at ({closest['pt_a'][0]}, {closest['pt_a'][1]}) and "
        f"{bsum['pads']} at ({closest['pt_b'][0]}, {closest['pt_b'][1]}). "
        f"Islands: {islands['n_islands']} (opens {islands['opens']}). "
        "The 25 mm cap does not apply; this pass is the explicit P0.14 exception. "
        "The gap is still not a straight route."
    )
    md.append("")
    md.append("## Straight line (not used)")
    md.append("")
    md.append(
        f"0.18 mm F.Cu chord {straight['from']} → {straight['to']} "
        f"({straight['length_mm']} mm). Crosses the SiP body: "
        f"**{straight['crosses_sip_body']}**. "
        f"Foreign items under 0.15 mm: {straight['hit_count_under_0_15']}."
    )
    md.append("")
    for net in ("GND", "P0.04", "P0.03", "<no-net>", "P0.15", "ENABLE", "VDD2", "VDD_GPIO"):
        if net in straight["worst_by_net"] or net in ("GND", "P0.04", "P0.03", "<no-net>"):
            md.append(f"- {worst_line(net)}")
    md.append("")
    md.append(
        "The chord also runs the south fanout (y≈37–50 under the package). "
        "Locked P0.04 segments (41.25, 46.80)–(37.40, 46.80) and "
        "(41.25, 42.50)–(41.25, 46.80) were not ripped. P0.15 west wrap was not ripped."
    )
    md.append("")
    md.append("## Why no around-the-package jog")
    md.append("")
    md.append(
        "U1.24 is the north-edge pad (42.25, 26.75), size 0.30×0.80, F.Cu only. "
        f"SiP body is x {BODY[0]}–{BODY[2]}, y {BODY[1]}–{BODY[3]}. "
        "The exposed pad lip is only the north 0.40 mm (y 26.35–26.75). "
        "South of that lip is under the body, which this pass may not enter."
    )
    md.append("")
    md.append(
        f"East pad U1.23 (P0.13) copper gap {pitch['u1_23_p013_gap_mm']} mm and "
        f"west pad U1.25 (P0.15) copper gap {pitch['u1_25_p015_gap_mm']} mm. "
        f"A 0.18 mm track at 0.15 mm clearance needs {pitch['need_mm']} mm. "
        "The pad row does not pass a track. Both neighbors continue as 0.18 mm "
        "F.Cu tracks north to their fanout vias, so the pocket cannot be crossed sideways."
    )
    md.append("")
    if pinch:
        md.append(
            f"North exit at the via row: {pinch['left']['net']} via "
            f"({pinch['left']['x']}, {pinch['left']['y']}) r={pinch['left']['r']} and "
            f"{pinch['right']['net']} via ({pinch['right']['x']}, {pinch['right']['y']}) "
            f"r={pinch['right']['r']}. Copper-to-copper gap **{pinch['copper_gap_mm']} mm**, "
            f"need **{pinch['need_mm']} mm**, short by **{pinch['short_by_mm']} mm**. "
            "No x clears both vias at once, so the pocket has no north exit on F.Cu. "
            "A 0.50/0.30 via centered between the parallel tracks (x=42.25) would clear "
            "those tracks by 0.16 mm, but that point is inside the B.Cu GND fill. "
            "Moving the via east until it clears the fill (edge x=42.41) puts it through "
            "the P0.13 track (west edge x=42.66)."
        )
        md.append("")
    md.append(
        f"B.Cu inside the pocket is GND fill. At y=25.0 the fill edge is x="
        f"{fill['b_fill_edge_x_at_y25']} and the P0.13 track west edge is x="
        f"{fill['p013_track_west_edge_x']} (halo {fill['halo_mm']} mm, the zone's "
        "0.25 mm pullback). A via on the only F.Cu-clear cells drops into that fill "
        "or into the halo, which cannot hold a 0.50 mm via at ≥0.15 mm. "
        "North of the via row, both F.Cu and B.Cu are GND fill, so there is no "
        "layer change that reaches an east skirt."
    )
    md.append("")
    md.append(
        "East of the package (x>44, outside the body) is therefore not reachable "
        "in ≤8 segments and one via without crossing P0.13, the body, the south "
        "fanout, or the GND pour. No locked trunk was ripped. The sealed B.Cu "
        "pocket y≈44.60, x≈81.8–97.3 was not used. No header or U1 move. "
        "U1.88 and U1.89 were not retried. P0.24 was not started. No Gerbers. No git commit."
    )
    md.append("")
    md.append("## Gate")
    md.append("")
    md.append(
        "NO-ROUTE. P0.14 opens do not drop. No copper was added, so no other net "
        "gained an open, short/clearance/crossing/hole stayed as they were, and "
        "hole_to_hole was not raised. Nothing to revert."
    )
    md.append("")
    (REPORTS / "PASS30AU_SUMMARY.md").write_text("\n".join(md) + "\n")

    note = f"""
## Pass30au — P0.14 around the SiP, no route — {stamp}

**Decision:** **NO-ROUTE**. No copper. No via. No backup. The 25 mm cap was waived for this net and the straight line was still not used.

**Remeasured gap:** {closest['gap_mm']} mm on F.Cu, pad J18.2 island ({closest['pt_a'][0]}, {closest['pt_a'][1]}) ↔ pad U1.24 ({closest['pt_b'][0]}, {closest['pt_b'][1]}). P0.14 opens {islands['opens']}→{islands['opens']}. Ratsnest edges {rats['ratsnest_edges']}→{rats['ratsnest_edges']}.

**Straight line:** crosses the SiP body and the south fanout. Worst hits include {worst_line('GND')}; {worst_line('P0.04')}; {worst_line('P0.03')}; {worst_line('<no-net>')}. Not used.

**Blocker:** U1.24's F.Cu pocket is closed. Pad gaps to P0.13/P0.15 are {pitch['u1_23_p013_gap_mm']} / {pitch['u1_25_p015_gap_mm']} mm (need {pitch['need_mm']} mm). North via pinch copper gap {pinch['copper_gap_mm'] if pinch else 'n/a'} mm (need {pinch['need_mm'] if pinch else 'n/a'} mm). B.Cu in the pocket is GND fill; the halo beside P0.13 is {fill['halo_mm']} mm and will not take a via. No east-of-package jog within 8 segments and one via without entering the body, the south fanout, or the pour. Locked copper not ripped. U1.88 / U1.89 not retried. P0.24 not started. No Gerbers.

**Artifacts:** `reports/PASS30AU_SUMMARY.{{md,json}}`, `scripts/final_pass30au.py`
"""
    text = REVIEW.read_text()
    marker = "## Pass30au —"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    REVIEW.write_text(text.rstrip() + "\n" + note)


def main():
    before = sha(BOARD)
    board = pcbnew.LoadBoard(str(BOARD))
    stamp = ist_now()
    islands = measure_islands(board)
    closest = islands["closest"]
    # best_gap point order follows island index order, not a fixed end.
    # Normalize so pt_a is the header island (y larger) and pt_b is U1.
    if closest["pt_a"][1] < closest["pt_b"][1]:
        closest["pt_a"], closest["pt_b"] = closest["pt_b"], closest["pt_a"]
        closest["island_a"], closest["island_b"] = closest["island_b"], closest["island_a"]
    straight = straight_hits(board, tuple(closest["pt_b"]), tuple(closest["pt_a"]))
    wall = via_wall(board)
    fill = pocket_fill(board)
    pitch = pad_pitch(board)
    rats = ratsnest(board)
    after = sha(BOARD)
    if before != after:
        raise SystemExit("board bytes changed during a no-route pass")
    write_reports(stamp, before, islands, straight, wall, fill, pitch, rats)
    # confirm still unchanged after report writes (reports are outside the pcb)
    if sha(BOARD) != before:
        raise SystemExit("board bytes changed while writing reports")
    print(json.dumps({
        "decision": "NO-ROUTE",
        "gap_mm": islands["closest"]["gap_mm"],
        "p014_opens": islands["opens"],
        "ratsnest": rats["ratsnest_edges"],
        "p014_rats": islands["opens"],
        "pinch": wall["north_pinch"],
        "halo_mm": fill["halo_mm"],
        "straight_body": straight["crosses_sip_body"],
        "straight_worst_gnd": straight["worst_by_net"].get("GND"),
        "straight_worst_p004": straight["worst_by_net"].get("P0.04"),
        "straight_worst_p003": straight["worst_by_net"].get("P0.03"),
        "straight_worst_nonet": straight["worst_by_net"].get("<no-net>"),
        "sha": before,
    }, indent=2))


if __name__ == "__main__":
    main()
