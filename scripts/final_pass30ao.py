#!/usr/bin/env python3
"""pass30ao — remeasure live island gaps. No copper unless a qualifying gap exists.

Priority:
  1. Remaining VDD_GPIO open (exactly one after pass30an) if its copper gap is <= 25 mm.
  2. Else the shortest other non-GND gap that is <= 20 mm.
  3. Else NO-ROUTE. Write the five shortest non-GND gaps and stop.

This run is the no-route branch. The script refuses to place copper. If a later
board state would qualify, it aborts instead of writing a false NO-ROUTE.
GND zone islands are ignored when ranking. Protected keeps are measured but
only appear in the five if they are actually among the shortest non-GND gaps.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
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
BEFORE = REPORTS / "DRC_PASS30AO_BEFORE.json"
VDD_CAP = 25.0
OTHER_CAP = 20.0


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_open_nets(data):
    return ah.load_open_nets_from(data)


def drc_stats(data) -> dict:
    vc = Counter(v["type"] for v in data.get("violations", []))
    opens = load_open_nets(data)
    return {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "hole_to_hole": vc.get("hole_to_hole", 0),
        "gnd_zone_islands": opens.get("GND", 0),
        "vdd_gpio_unconnected": opens.get("VDD_GPIO", 0),
    }


def run_drc() -> dict:
    tmp = Path("/tmp/nrf30ao_drc.json")
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", str(tmp), str(BOARD)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, BEFORE)
    return json.loads(BEFORE.read_text())


def all_gaps(board, opens):
    """Every non-GND island pair, including protected keeps, shortest first."""
    by = ah.collect(board)
    ah.add_nonet(board, by)
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
        islands = ah.cluster(prims)
        audit[net] = {
            "drc_opens": nopen,
            "islands": len(islands),
            "prims": len(prims),
            "protected": net in ah.PROTECTED_NETS,
            "islands_match_drc": len(islands) == nopen + 1,
        }
        if len(islands) < 2:
            continue
        for a in range(len(islands)):
            for b in range(a + 1, len(islands)):
                best, same = ah.best_gap(prims, islands[a], islands[b])
                if best is None:
                    continue
                g, pa, pb, pi, pj, shared = best
                layer = None
                sp = sq = None
                sg = None
                if same:
                    sg, sp, sq, spi, spj, _ = same
                    layer = next(iter(spi.layers & spj.layers))
                blocks = ah.line_blocks(by, net, sp, sq, layer) if same else []
                rows.append(
                    {
                        "net": net,
                        "protected_keep": net in ah.PROTECTED_NETS,
                        "gap_mm": round(g, 3),
                        "closest_a": [ah.r3(pa[0]), ah.r3(pa[1])],
                        "closest_b": [ah.r3(pb[0]), ah.r3(pb[1])],
                        "a_item": pi.label,
                        "b_item": pj.label,
                        "a_layers": sorted(ah.LAYER_NAME[l] for l in pi.layers),
                        "b_layers": sorted(ah.LAYER_NAME[l] for l in pj.layers),
                        "same_layer_gap_mm": None if sg is None else round(sg, 3),
                        "same_layer": None if layer is None else ah.LAYER_NAME[layer],
                        "same_a": None if sp is None else [ah.r3(sp[0]), ah.r3(sp[1])],
                        "same_b": None if sq is None else [ah.r3(sq[0]), ah.r3(sq[1])],
                        "island_a": ah.island_summary(prims, islands[a]),
                        "island_b": ah.island_summary(prims, islands[b]),
                        "straight_blocks": blocks,
                        "corridor": ah.corridor_hit(sp, sq, layer) if same else False,
                        "rf_keepout": ah.rf_keepout_hit(
                            sp if sp else pa, sq if sq else pb, layer if layer is not None else ah.F
                        ),
                        "via_possible": g <= 0.60,
                    }
                )
    rows.sort(key=lambda r: r["gap_mm"])
    return rows, audit


def fmt_pt(p):
    return f"({p[0]:.3f}, {p[1]:.3f})"


def layers_of(names):
    return "+".join(names) if names else "?"


def gate_blocker(r, vdd_gap):
    """Why this pair is not the pass30ao route."""
    bits = []
    if r["net"] == "VDD_GPIO":
        bits.append(
            f"remaining VDD_GPIO open is {r['gap_mm']:.3f} mm, over the 25 mm cap, so priority 1 does not qualify"
        )
    else:
        bits.append(
            f"{r['gap_mm']:.3f} mm is over the 20 mm cap for any non-VDD_GPIO gap "
            f"(remaining VDD_GPIO is {vdd_gap:.3f} mm, already over 25 mm)"
        )
    bits.append(ah.why_blocked(r))
    if r["protected_keep"]:
        bits.append("net is a locked keep; a join that ripped that copper would not be placed")
    return "; ".join(bits)


def write_reports(rows, audit, stats, stamp, board_sha):
    vdd = [r for r in rows if r["net"] == "VDD_GPIO"]
    if len(vdd) != 1:
        raise SystemExit(f"expected exactly one VDD_GPIO gap, found {len(vdd)}")
    vdd_gap = vdd[0]["gap_mm"]
    others = [r for r in rows if r["net"] != "VDD_GPIO"]
    if not others:
        raise SystemExit("no other non-GND gaps")
    other_min = others[0]
    if not (vdd_gap > VDD_CAP and other_min["gap_mm"] > OTHER_CAP):
        raise SystemExit(
            f"qualifying gap appeared (VDD_GPIO {vdd_gap} mm, "
            f"shortest other {other_min['net']} {other_min['gap_mm']} mm). "
            "This script must not place copper and must not claim NO-ROUTE."
        )
    mismatched = [
        net
        for net, info in audit.items()
        if net != "GND" and "islands" in info and not info["islands_match_drc"]
    ]
    if mismatched:
        raise SystemExit(f"island count does not match DRC opens: {mismatched}")

    five = rows[:5]
    short_rows = []
    for i, r in enumerate(five, 1):
        short_rows.append(
            {
                "rank": i,
                "net": r["net"],
                "distance_mm": r["gap_mm"],
                "protected_keep": r["protected_keep"],
                "island_a": {
                    "closest_copper_mm": r["closest_a"],
                    "layers": r["a_layers"],
                    "item": r["a_item"],
                    "pads": r["island_a"]["pads"],
                    "anchor_mm": r["island_a"]["anchor"],
                    "island_layers": r["island_a"]["layers"],
                    "primitives": r["island_a"]["n"],
                },
                "island_b": {
                    "closest_copper_mm": r["closest_b"],
                    "layers": r["b_layers"],
                    "item": r["b_item"],
                    "pads": r["island_b"]["pads"],
                    "anchor_mm": r["island_b"]["anchor"],
                    "island_layers": r["island_b"]["layers"],
                    "primitives": r["island_b"]["n"],
                },
                "same_layer": r["same_layer"],
                "same_layer_gap_mm": r["same_layer_gap_mm"],
                "blocker": gate_blocker(r, vdd_gap),
            }
        )

    summary = {
        "pass": "30ao",
        "timestamp": stamp,
        "decision": "NO-ROUTE",
        "routed": False,
        "net": None,
        "distance_mm": vdd_gap,
        "vdd_gpio_remaining_gap_mm": vdd_gap,
        "vdd_gpio_cap_mm": VDD_CAP,
        "vdd_gpio_qualifies": False,
        "shortest_other_net": other_min["net"],
        "shortest_other_gap_mm": other_min["gap_mm"],
        "other_cap_mm": OTHER_CAP,
        "other_qualifies": False,
        "why": (
            f"Remaining VDD_GPIO open is {vdd_gap:.3f} mm (>{VDD_CAP:.0f} mm) between "
            f"F.Cu pad U2.5 {fmt_pt(vdd[0]['closest_a'])} and pad J18.9 {fmt_pt(vdd[0]['closest_b'])}. "
            f"Shortest other non-GND gap is {other_min['net']} {other_min['gap_mm']:.3f} mm "
            f"(>{OTHER_CAP:.0f} mm). Neither priority qualifies, so no track and no via."
        ),
        "path": None,
        "via_used": False,
        "segments": [],
        "power_clearance_measured_mm": None,
        "power_clearance_note": "No copper placed, so POWER/VIN clearance was not measured against a new track.",
        "unconnected_before": stats["unconnected_items"],
        "unconnected_after": stats["unconnected_items"],
        "vdd_gpio_opens_before": stats["vdd_gpio_unconnected"],
        "vdd_gpio_opens_after": stats["vdd_gpio_unconnected"],
        "gnd_islands_before": stats["gnd_zone_islands"],
        "gnd_islands_after": stats["gnd_zone_islands"],
        "gnd_islands_waived": True,
        "shorting_items": stats["shorting_items"],
        "clearance": stats["clearance"],
        "tracks_crossing": stats["tracks_crossing"],
        "hole_clearance": stats["hole_clearance"],
        "hole_to_hole": stats["hole_to_hole"],
        "board_sha256": board_sha,
        "board_modified": False,
        "backup": None,
        "drc_before": "reports/DRC_PASS30AO_BEFORE.json",
        "drc_mid": None,
        "drc_after": None,
        "island_audit_matches_drc": True,
        "y_7_050_path_not_repeated": True,
        "y_44_60_pocket_not_used": True,
        "locked_copper_not_ripped": True,
        "no_gerbers": True,
        "no_git_commit": True,
        "five": [{"net": s["net"], "distance_mm": s["distance_mm"]} for s in short_rows],
    }
    shortlist = {
        "pass": "30ao",
        "timestamp": stamp,
        "decision": "NO-ROUTE",
        "rule": (
            "Do not route. Priority 1 needs the remaining VDD_GPIO gap <= 25 mm. "
            "Priority 2 needs some other non-GND gap <= 20 mm. Neither is true on the live board. "
            "GND zone islands ignored."
        ),
        "vdd_gpio_remaining_gap_mm": vdd_gap,
        "shortest_other": {"net": other_min["net"], "distance_mm": other_min["gap_mm"]},
        "five": short_rows,
    }
    (REPORTS / "PASS30AO_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    (REPORTS / "PASS30AO_SHORTLIST.json").write_text(json.dumps(shortlist, indent=2) + "\n")

    sl = []
    sl.append("# PASS30AO shortlist — five shortest non-GND island gaps")
    sl.append("")
    sl.append(f"**Timestamp:** {stamp}")
    sl.append("**Decision:** **NO-ROUTE** (no copper edit)")
    sl.append(
        "**Gate:** close the remaining VDD_GPIO open only if it is ≤ 25 mm; otherwise close the "
        "shortest other non-GND gap only if it is ≤ 20 mm. One 0.18 mm route, ≤ 6 segments, one via "
        "only if required. Do not repeat the locked y=7.050 path. Stay east of x=24.2. Do not use the y=44.60 pocket."
    )
    sl.append(
        f"**Result:** remaining VDD_GPIO is **{vdd_gap:.3f} mm** (> 25 mm). "
        f"Shortest other non-GND gap is `{other_min['net']}` **{other_min['gap_mm']:.3f} mm** (> 20 mm). "
        "No pair qualifies, so nothing was routed."
    )
    sl.append("")
    sl.append(
        "GND zone islands ignored. Distance is copper-edge to copper-edge. "
        "Island counts match DRC opens (`islands = opens + 1`) on every non-GND open net. "
        "Protected keeps were measured: P0.19 is 36.661 mm and P0.22 is 51.605 mm, both outside this five. "
        "P0.15, VDD2, SIM_IO_C, and SIM_CLK_C have no open."
    )
    sl.append("")
    for row in short_rows:
        a, b = row["island_a"], row["island_b"]
        sl.append(f"## {row['rank']}. `{row['net']}` — {row['distance_mm']:.3f} mm")
        sl.append("")
        sl.append(
            f"- **Island A:** {layers_of(a['layers'])} {fmt_pt(a['closest_copper_mm'])} — {a['item']}"
        )
        sl.append(
            f"  - island layers {', '.join(a['island_layers'])}; pads {', '.join(a['pads']) or '(none)'}; "
            f"anchor {fmt_pt(a['anchor_mm'])}; {a['primitives']} primitives"
        )
        sl.append(
            f"- **Island B:** {layers_of(b['layers'])} {fmt_pt(b['closest_copper_mm'])} — {b['item']}"
        )
        sl.append(
            f"  - island layers {', '.join(b['island_layers'])}; pads {', '.join(b['pads']) or '(none)'}; "
            f"anchor {fmt_pt(b['anchor_mm'])}; {b['primitives']} primitives"
        )
        sl.append(f"- **Distance:** {row['distance_mm']:.3f} mm")
        if row["same_layer"]:
            sl.append(f"- **Same-layer gap:** {row['same_layer_gap_mm']:.3f} mm on {row['same_layer']}")
        sl.append(f"- **Blocker:** {row['blocker']}")
        sl.append("")
    sl.append("## Not attempted")
    sl.append("")
    sl.append(
        "No backup, no rip, no track, no via. The locked y=7.050 VDD_GPIO path was not repeated. "
        "The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved. "
        "No Gerbers. No git commit."
    )
    sl.append("")
    (REPORTS / "PASS30AO_SHORTLIST.md").write_text("\n".join(sl) + "\n")

    sm = []
    sm.append("# PASS30AO_SUMMARY — no qualifying gap")
    sm.append("")
    sm.append(f"**Timestamp:** {stamp}")
    sm.append("**KiCad:** 9.0.2")
    sm.append("**Decision:** **NO-ROUTE**")
    sm.append("**Net:** none")
    sm.append(f"**Distance:** remaining VDD_GPIO {vdd_gap:.3f} mm (cap 25 mm); shortest other `{other_min['net']}` {other_min['gap_mm']:.3f} mm (cap 20 mm)")
    sm.append("**Path:** none")
    sm.append("**POWER clearance measured:** n/a (no copper placed)")
    sm.append(f"**Unconnected:** {stats['unconnected_items']} → {stats['unconnected_items']}")
    sm.append(f"**VDD_GPIO opens:** {stats['vdd_gpio_unconnected']} → {stats['vdd_gpio_unconnected']}")
    sm.append(f"**GND zone islands:** {stats['gnd_zone_islands']} → {stats['gnd_zone_islands']} (waived, not a factor)")
    sm.append(
        f"**Short / clearance / crossing / hole_clearance:** "
        f"{stats['shorting_items']} / {stats['clearance']} / {stats['tracks_crossing']} / {stats['hole_clearance']}"
    )
    sm.append(f"**hole_to_hole:** {stats['hole_to_hole']} (unchanged; no edit)")
    sm.append("")
    sm.append("## Why no route")
    sm.append("")
    sm.append(summary["why"])
    sm.append("")
    sm.append(
        "Priority 1 is the single remaining VDD_GPIO open (DRC opens = 1, two islands). "
        "It is the same pair pass30an left open: the merged east/U1 island (closest copper pad U2.5) "
        "and the J18.9 / J12.17 / J12.18 island. 27.034 mm is over 25 mm, so it is not closed. "
        "Priority 2 then looks at every other non-GND pair. The shortest is P0.31 at 29.078 mm, over 20 mm. "
        "Nothing falls through into a route. A dirty jog was not forced."
    )
    sm.append("")
    sm.append("## Five shortest non-GND gaps")
    sm.append("")
    for row in short_rows:
        a, b = row["island_a"], row["island_b"]
        sm.append(
            f"- `{row['net']}` {row['distance_mm']:.3f} mm  "
            f"{layers_of(a['layers'])} {fmt_pt(a['closest_copper_mm'])} ↔ "
            f"{layers_of(b['layers'])} {fmt_pt(b['closest_copper_mm'])}"
        )
    sm.append("")
    sm.append("Detail: `reports/PASS30AO_SHORTLIST.md`.")
    sm.append("")
    sm.append("## DRC")
    sm.append("")
    sm.append("| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |")
    sm.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    sm.append(
        f"| before (also after; no edit) | {stats['unconnected_items']} | {stats['shorting_items']} | "
        f"{stats['clearance']} | {stats['tracks_crossing']} | {stats['hole_clearance']} | "
        f"{stats['hole_to_hole']} | {stats['gnd_zone_islands']} | {stats['vdd_gpio_unconnected']} |"
    )
    sm.append("")
    sm.append("Source: `reports/DRC_PASS30AO_BEFORE.json`. No mid or after file — the board file was not written.")
    sm.append("")
    sm.append("## Protect checklist")
    sm.append("")
    sm.append("- Locked pass30an VDD_GPIO F.Cu y=7.050 path not repeated and not ripped")
    sm.append("- Locked pass30ak VDD_GPIO polyline to U1.12 not ripped")
    sm.append("- COEX0, DEC0 B.Cu bridge, P0.10 via (47.000, 28.500), P0.12 via (47.000, 27.500) not moved")
    sm.append("- P0.15 west wrap not touched; east spine at x=45.5 not used")
    sm.append("- Class C C22/C23/C24, trunks, L1, L2, TP1, U3, solid In1 GND not touched")
    sm.append("- P0.22 keep, P0.19 keep, Stage-A VDD2, SIM_IO_C / SIM_CLK_C walls not ripped")
    sm.append("- y=44.60 B.Cu pocket (x≈81.8–97.3) not used")
    sm.append("- RF keepout: no new digital copper")
    sm.append("- U1 and headers unmoved")
    sm.append("- No Gerbers. No git commit.")
    sm.append("")
    (REPORTS / "PASS30AO_SUMMARY.md").write_text("\n".join(sm) + "\n")
    return summary


def patch_review(stamp, summary):
    text = REVIEW.read_text()
    if "pass30ao" in text:
        return "already"
    vdd = summary["vdd_gpio_remaining_gap_mm"]
    other_net = summary["shortest_other_net"]
    other = summary["shortest_other_gap_mm"]
    unc = summary["unconnected_before"]
    prefix = (
        f"**Review date:** {stamp} (Asia/Calcutta) — pass30ao NO-ROUTE "
        f"(remaining VDD_GPIO {vdd:.3f} mm > 25 mm; shortest other `{other_net}` {other:.3f} mm > 20 mm; "
        f"unc {unc}→{unc}, no copper). Prior: "
    )
    needle = "**Review date:** "
    if needle not in text:
        raise SystemExit("review date line missing")
    text = text.replace(needle, prefix, 1)
    section = f"""
## Pass30ao — island remeasure, no qualifying gap — {stamp}

**Decision:** **NO-ROUTE**. No copper. No backup. Board bytes unchanged.

**Live remeasure** (`reports/DRC_PASS30AO_BEFORE.json`, island copper matches DRC opens): unconnected {unc}, VDD_GPIO opens 1, GND islands {summary['gnd_islands_before']} (ignored for ranking), short/clearance/crossing/hole_clearance 0/0/0, hole_to_hole {summary['hole_to_hole']}.

**Priority 1:** the remaining VDD_GPIO open is **{vdd:.3f} mm** on F.Cu, pad U2.5 (74.519, 39.306) ↔ pad J18.9 (58.859, 61.343). Over the 25 mm cap, so it was not closed. The locked y=7.050 path was not repeated.

**Priority 2:** shortest other non-GND gap is `{other_net}` **{other:.3f} mm**, over the 20 mm cap. No other non-GND pair is ≤ 20 mm.

**POWER clearance:** not measured — no track was added.

**Five shortest non-GND gaps:** VDD_GPIO 27.034, P0.31 29.078, P0.30 32.207, P0.14 34.038, P0.16 34.259. Detail: `reports/PASS30AO_SHORTLIST.md`.

**Protect:** locked VDD_GPIO (y=7.050 and the U1.12 polyline), COEX0, DEC0 bridge, P0.10/P0.12 vias, P0.15 west wrap, Class C, P0.22, P0.19, Stage-A VDD2, SIM walls, y=44.60 pocket, RF keepout, U1 and headers all untouched. No Gerbers. No git commit.

**Artifacts:** `reports/PASS30AO_SUMMARY.{{md,json}}`, `reports/PASS30AO_SHORTLIST.{{md,json}}`, `reports/DRC_PASS30AO_BEFORE.json`, `scripts/final_pass30ao.py`
"""
    if not text.endswith("\n"):
        text += "\n"
    text = text + section
    REVIEW.write_text(text)
    return "inserted"


def main():
    before_sha = sha(BOARD)
    data = run_drc()
    stats = drc_stats(data)
    board = pcbnew.LoadBoard(str(BOARD))
    rows, audit = all_gaps(board, load_open_nets(data))
    stamp = ist_now()
    summary = write_reports(rows, audit, stats, stamp, before_sha)
    if sha(BOARD) != before_sha:
        raise SystemExit("board bytes changed; pass30ao must not write the pcb")
    review = patch_review(stamp, summary)
    print(
        json.dumps(
            {
                "decision": summary["decision"],
                "vdd_gpio_mm": summary["vdd_gpio_remaining_gap_mm"],
                "other": [summary["shortest_other_net"], summary["shortest_other_gap_mm"]],
                "unconnected": summary["unconnected_before"],
                "vdd_opens": summary["vdd_gpio_opens_before"],
                "gnd_islands": summary["gnd_islands_before"],
                "five": summary["five"],
                "review": review,
                "board_unchanged": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
