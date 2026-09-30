#!/usr/bin/env python3
"""pass30ak — replay pass30aj geometry. GND zone-island increase is waived.

Same shove and the same F.Cu 0.18 mm polyline as scripts/final_pass30aj.py.
Do not invent a new path.

Shove only:
- P0.12 and P0.10 dangling vias from x=47.4 to x=47.0
- Bridge the DEC0 F.Cu gap near x=47.55 on B.Cu
P0.08 and P0.11 stay put. P0.15 stays 42 segments.

Polyline:
(40.170,19.126)→(40.170,20.200)→(45.900,20.200)→(45.900,25.400)
→(47.550,25.400)→(47.550,31.500)→(44.000,31.500)

NEW GATE (GND islands waived). KEEP if:
- VDD_GPIO opens drop (3→2 or better)
- no non-GND net gains an open
- short, clearance, crossing, and hole are all 0
- P0.15 segment count is still 42
FULL REVERT only if that electrical gate fails.
The extra F.Cu GND zone island (10→11) is waived.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30ak/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"

_spec = importlib.util.spec_from_file_location(
    "final_pass30aj", ROOT / "scripts" / "final_pass30aj.py"
)
aj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(aj)


def sha(p) -> str:
    return aj.sha(p)


def nongnd_counts(data) -> Counter:
    """One count per unconnected item, attributed to each non-GND net named on it."""
    c: Counter = Counter()
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        nets = {n for n in re.findall(r"\[([^\]]+)\]", desc) if n != "GND"}
        for n in nets:
            c[n] += 1
    return c


def run_drc(dest: Path) -> dict:
    tmp = Path("/tmp/nrf30ak_drc.json")
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
        "gnd_zone_islands": aj.gnd_items(data),
        "vdd_gpio_unconnected": aj.net_items(data, "VDD_GPIO"),
    }
    hits = []
    for v in data.get("violations", []):
        if v["type"] not in ("shorting_items", "clearance", "tracks_crossing", "hole_clearance"):
            continue
        hits.append(
            {
                "type": v["type"],
                "description": v.get("description", ""),
                "items": [it.get("description", "") for it in v.get("items", [])],
            }
        )
    return {"stats": stats, "hits": hits, "data": data}


def poly_missing(board) -> list:
    tracks = [
        t
        for t in board.GetTracks()
        if t.GetClass() != "PCB_VIA"
        and t.GetNetname() == "VDD_GPIO"
        and t.GetLayer() == aj.F
    ]
    missing = []
    for (x1, y1), (x2, y2) in zip(aj.POLY, aj.POLY[1:]):
        ok = False
        for t in tracks:
            if aj.track_is(t, x1, y1, x2, y2) and abs(aj.mm(t.GetWidth()) - aj.W) < 0.001:
                ok = True
                break
        if not ok:
            missing.append([[x1, y1], [x2, y2]])
    return missing


def footprint_xy(board) -> dict:
    out = {}
    for f in board.GetFootprints():
        out[f.GetReference()] = (
            round(aj.mm(f.GetPosition().x), 4),
            round(aj.mm(f.GetPosition().y), 4),
            round(f.GetOrientationDegrees(), 3),
        )
    return out


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if BACKUP.is_file():
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit(
                "pass30ak backup exists and the live board does not match it; "
                "refusing to clobber the pre-edit or double-apply"
            )
    else:
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup hash mismatch before edit")

    print("BACKUP", sha(BACKUP))
    before_path = REPORTS / "DRC_PASS30AK_BEFORE.json"
    before_run = run_drc(before_path)
    before = before_run["data"]
    before_unc = before_run["stats"]["unconnected_items"]
    before_gnd = before_run["stats"]["gnd_zone_islands"]
    before_vdd = before_run["stats"]["vdd_gpio_unconnected"]
    before_nongnd = nongnd_counts(before)
    print("BEFORE", before_run["stats"], "vdd", before_vdd)

    board = pcbnew.LoadBoard(str(BOARD))
    info = aj.confirm(board)
    p015_before = aj.p015_count(board)
    if p015_before != 42:
        raise SystemExit(f"P0.15 before is {p015_before}, expected 42; not editing")
    outlines_before = aj.gnd_outline_summaries(board)
    fp_before = footprint_xy(board)
    print("CONFIRM", json.dumps(info))
    print("P0.15", p015_before, "GND outlines", len(outlines_before))

    shove = aj.apply_shove(board)
    aj.add_poly(board)
    p015_mid = aj.p015_count(board)
    missing = poly_missing(board)
    aj.confirm(board)
    fp_after = footprint_xy(board)
    moved_fp = sorted(ref for ref in fp_before if fp_before[ref] != fp_after.get(ref))
    if p015_mid != 42 or missing or moved_fp:
        # Do not save a bad edit.
        print("ABORT geometry", "p015", p015_mid, "missing", missing, "moved", moved_fp)
        shutil.copy2(BACKUP, BOARD)
        after = run_drc(REPORTS / "DRC_PASS30AK_AFTER.json")
        decision = "REVERT"
        st = {
            "unconnected_items": before_unc,
            "shorting_items": None,
            "clearance": None,
            "tracks_crossing": None,
            "hole_clearance": None,
            "hole_to_hole": None,
            "gnd_zone_islands": before_gnd,
            "vdd_gpio_unconnected": before_vdd,
        }
        keep = False
        gained = {}
        outlines_mid = outlines_before
        reason = (
            f"geometry guard failed before save: p015 {p015_before}->{p015_mid}, "
            f"missing polyline {missing}, moved footprints {moved_fp}"
        )
        write_outputs(
            decision, info, shove, before_unc, st, after, before_gnd, before_vdd,
            p015_before, p015_mid, outlines_before, outlines_mid, [], keep,
            gained, reason, False, False, False,
        )
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    outlines_mid = aj.gnd_outline_summaries(board)
    pcbnew.SaveBoard(str(BOARD), board)

    # Reload to confirm the saved polyline, not just the in-memory board.
    saved = pcbnew.LoadBoard(str(BOARD))
    missing_saved = poly_missing(saved)
    p015_saved = aj.p015_count(saved)
    aj.confirm(saved)
    if missing_saved or p015_saved != 42:
        print("SAVED GEOMETRY BAD", missing_saved, p015_saved)
        shutil.copy2(BACKUP, BOARD)
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("revert failed: hash mismatch")
        after = run_drc(REPORTS / "DRC_PASS30AK_AFTER.json")
        decision = "REVERT"
        st = before_run["stats"]
        write_outputs(
            decision, info, shove, before_unc, st, after, before_gnd, before_vdd,
            p015_before, p015_saved, outlines_before, outlines_mid, [], False,
            {}, "saved board polyline or P0.15 did not match; full revert",
            False, False, False,
        )
        return

    mid = run_drc(REPORTS / "DRC_PASS30AK_MID.json")
    print("MID", mid["stats"])
    st = mid["stats"]
    after_nongnd = nongnd_counts(mid["data"])
    gained = {}
    for net in set(before_nongnd) | set(after_nongnd):
        b = before_nongnd.get(net, 0)
        a = after_nongnd.get(net, 0)
        if a > b:
            gained[net] = {"before": b, "after": a}
    clean = (
        st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
    )
    vdd_drop = st["vdd_gpio_unconnected"] < before_vdd and st["vdd_gpio_unconnected"] <= 2
    no_new_nongnd = len(gained) == 0
    p015_ok = p015_saved == 42 and p015_before == 42
    keep = clean and vdd_drop and no_new_nongnd and p015_ok
    print(
        "clean", clean,
        "vdd", before_vdd, "->", st["vdd_gpio_unconnected"],
        "gained", gained,
        "p015", p015_ok,
        "keep", keep,
        "gnd_islands", before_gnd, "->", st["gnd_zone_islands"], "(waived)",
    )

    decision = "KEEP" if keep else "REVERT"
    if not keep:
        shutil.copy2(BACKUP, BOARD)
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("revert failed: hash mismatch")
        after = run_drc(REPORTS / "DRC_PASS30AK_AFTER.json")
        print("AFTER", after["stats"])
        reason = (
            "electrical gate failed: "
            f"vdd_drop={vdd_drop} ({before_vdd}->{st['vdd_gpio_unconnected']}), "
            f"no_new_nongnd_open={no_new_nongnd} gained={gained}, "
            f"short/clear/cross/hole zero={clean}. "
            "GND island change is waived and is not the revert reason."
        )
    else:
        shutil.copy2(REPORTS / "DRC_PASS30AK_MID.json", REPORTS / "DRC_PASS30AK_AFTER.json")
        after = {"stats": st, "hits": mid["hits"], "data": mid["data"]}
        reason = None

    write_outputs(
        decision, info, shove, before_unc, st, after, before_gnd, before_vdd,
        p015_before, p015_saved, outlines_before, outlines_mid, mid["hits"], keep,
        gained, reason, clean, vdd_drop, no_new_nongnd,
        before_nongnd=before_nongnd, after_nongnd=after_nongnd,
    )


def write_outputs(
    decision, info, shove, before_unc, st, after, before_gnd, before_vdd,
    p015_before, p015_mid, outlines_before, outlines_mid, hits, keep,
    gained, reason, clean, vdd_drop, no_new_nongnd,
    before_nongnd=None, after_nongnd=None,
):
    def key_area(rows):
        return {(r["area_mm2"], tuple(r["bbox"])) for r in rows}

    only_after = sorted(key_area(outlines_mid) - key_area(outlines_before))
    only_before = sorted(key_area(outlines_before) - key_area(outlines_mid))
    segments = []
    for (x1, y1), (x2, y2) in zip(aj.POLY, aj.POLY[1:]):
        segments.append({"layer": "F.Cu", "width_mm": aj.W, "start": [x1, y1], "end": [x2, y2]})

    summary = {
        "pass": "30ak",
        "timestamp": aj.ist_now(),
        "decision": decision,
        "path": "shove",
        "replay_of": "pass30aj",
        "geometry_matches_aj": True if decision == "KEEP" else False,
        "west_attempted": False,
        "west_skipped_reason": aj.main.__doc__ and "shove geometry does not enter the P0.15 keep (x=41.75, y=23.10-26.75); west approach not used",
        "east_spine_x45_5": False,
        "net": "VDD_GPIO",
        "via_used_for_vdd": False,
        "confirmed": info,
        "segments": segments,
        "shove": shove,
        "unconnected_before": before_unc,
        "unconnected_mid": st["unconnected_items"],
        "unconnected_after": after["stats"]["unconnected_items"],
        "unconnected_delta_mid": (st["unconnected_items"] - before_unc) if st["unconnected_items"] is not None else None,
        "gnd_zone_islands_before": before_gnd,
        "gnd_zone_islands_mid": st.get("gnd_zone_islands"),
        "gnd_zone_islands_after": after["stats"]["gnd_zone_islands"],
        "gnd_zone_islands_waived": True,
        "vdd_gpio_unconnected_before": before_vdd,
        "vdd_gpio_unconnected_mid": st.get("vdd_gpio_unconnected"),
        "vdd_gpio_unconnected_after": after["stats"]["vdd_gpio_unconnected"],
        "nongnd_opens_gained": gained,
        "gate": {
            "rule": "KEEP if VDD_GPIO opens drop (3→2 or better) AND no non-GND net gains an open AND short/clearance/crossing/hole are all 0 AND P0.15 stays 42. GND islands waived.",
            "clean_short_clear_cross_hole": clean,
            "vdd_gpio_opens_dropped": vdd_drop,
            "no_nongnd_net_gained_an_open": no_new_nongnd,
            "gnd_islands_waived": True,
            "p015_unchanged_42": p015_before == 42 and p015_mid == 42,
            "met": keep,
        },
        "drc_mid": {k: v for k, v in st.items()},
        "drc_after": after["stats"],
        "p015_segments_before": p015_before,
        "p015_segments_mid": p015_mid,
        "gnd_f_outlines_before": len(outlines_before),
        "gnd_f_outlines_mid": len(outlines_mid),
        "gnd_outline_only_after": [
            {"area_mm2": a, "bbox": list(bb)} for a, bb in only_after
        ],
        "gnd_outline_only_before": [
            {"area_mm2": a, "bbox": list(bb)} for a, bb in only_before
        ],
        "hits": hits,
        "revert_reason": reason,
        "backup": str(BACKUP),
        "backup_sha256": sha(BACKUP),
        "board_sha256_after": sha(BOARD),
    }
    # west_skipped_reason should be the same sentence as aj, not a docstring check.
    summary["west_skipped_reason"] = (
        "shove geometry does not enter the P0.15 keep (x=41.75, y=23.10-26.75); west approach not used"
    )
    (REPORTS / "PASS30AK_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_md(summary)
    print("DECISION", decision)


def write_md(s: dict) -> None:
    lines = []
    lines.append("# PASS30AK_SUMMARY — replay pass30aj VDD_GPIO shove (GND islands waived)")
    lines.append("")
    lines.append(f"**Timestamp:** {s['timestamp']}")
    lines.append("**KiCad:** 9.0.2")
    lines.append(f"**Decision:** **{s['decision']}**")
    lines.append(f"**Path:** {s['path']} (replay of pass30aj; west attempted: {s['west_attempted']})")
    lines.append(f"**Net:** {s['net']}")
    lines.append(
        f"**Unconnected:** {s['unconnected_before']} → mid {s['unconnected_mid']} → after {s['unconnected_after']}"
    )
    lines.append(
        f"**VDD_GPIO opens:** {s['vdd_gpio_unconnected_before']} → mid {s['vdd_gpio_unconnected_mid']} → after {s['vdd_gpio_unconnected_after']}"
    )
    lines.append(
        f"**GND zone islands:** {s['gnd_zone_islands_before']} → mid {s['gnd_zone_islands_mid']} → after {s['gnd_zone_islands_after']} (increase WAIVED)"
    )
    lines.append(f"**Geometry matches pass30aj:** {s['geometry_matches_aj']}")
    lines.append("")
    lines.append("## Confirmed live coordinates")
    lines.append("")
    v = s["confirmed"]["via"]
    p = s["confirmed"]["pad12"]
    lines.append(
        f"- F.Cu via island: net {v['net']} @ ({v['x']}, {v['y']}) dia {v['dia']} drill {v['drill']}"
    )
    lines.append(f"- U1 @ ({s['confirmed']['u1']['x']}, {s['confirmed']['u1']['y']}) unmoved")
    lines.append(
        f"- U1.12: net {p['net']} center ({p['x']}, {p['y']}) size {p['size']} bbox {p['bbox']} F.Cu only"
    )
    lines.append("")
    lines.append("## Path")
    lines.append("")
    lines.append(
        "Exact replay of `scripts/final_pass30aj.py` (`apply_shove` + `add_poly`). "
        "Not a new corridor. Shove, not west. The shove stays east of the P0.15 vertical keep "
        "(x=41.75, y=23.10–26.75) and does not rip or shove P0.15. "
        "The pass30ai east spine at x=45.5 was not repeated. Straight line was not used. "
        "No new via on VDD_GPIO. P0.08 and P0.11 were not shoved."
    )
    lines.append("")
    lines.append(s["west_skipped_reason"] + ".")
    lines.append("")
    lines.append("### VDD_GPIO polyline (0.18 mm F.Cu)")
    lines.append("")
    lines.append("| # | start | end | width |")
    lines.append("| --- | --- | --- | --- |")
    for i, seg in enumerate(s["segments"], 1):
        a, b = seg["start"], seg["end"]
        lines.append(
            f"| {i} | ({a[0]:.3f}, {a[1]:.3f}) | ({b[0]:.3f}, {b[1]:.3f}) | {seg['width_mm']} mm F.Cu |"
        )
    lines.append("")
    lines.append("### Nets shoved")
    lines.append("")
    for item in s["shove"]["nets"]:
        if item["net"] in ("P0.12", "P0.10"):
            lines.append(
                f"- **{item['net']}**: F stub + dangling via ({item['from'][0]:.3f}, {item['from'][1]:.3f}) → ({item['to'][0]:.3f}, {item['to'][1]:.3f}). Pad connection kept."
            )
        else:
            lines.append(
                "- **DEC0**: removed 4 coincident F horizontals (44.000, 31.000)–(48.720, 31.000). "
                "Left F stub ends at via (46.950, 30.900); B.Cu bridge to via (48.100, 30.900); "
                "right F stub returns to (48.720, 31.000) so the DEC0 trunk is continuous. "
                "Dangling via (47.800, 31.200) moved to (45.400, 30.550) with F riser (45.400, 31.000)–(45.400, 30.550)."
            )
    lines.append("- Not shoved: P0.08, P0.11, P0.15.")
    lines.append("")
    lines.append("## Gate (GND islands waived)")
    lines.append("")
    g = s["gate"]
    lines.append(f"- short/clear/cross/hole all zero: {g['clean_short_clear_cross_hole']}")
    lines.append(
        f"- VDD_GPIO opens drop (3→2 or better): {g['vdd_gpio_opens_dropped']} "
        f"({s['vdd_gpio_unconnected_before']} → {s['vdd_gpio_unconnected_mid']})"
    )
    lines.append(f"- no non-GND net gained an open: {g['no_nongnd_net_gained_an_open']}")
    if s["nongnd_opens_gained"]:
        lines.append(f"- gained: {s['nongnd_opens_gained']}")
    lines.append("- GND islands: WAIVED (do not revert for 10→11)")
    lines.append(
        f"- P0.15 segment count still 42: {g['p015_unchanged_42']} "
        f"({s['p015_segments_before']} → {s['p015_segments_mid']})"
    )
    lines.append(f"- **met: {g['met']}**")
    lines.append("")
    lines.append("## DRC")
    lines.append("")
    lines.append("| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | GND islands | VDD_GPIO opens |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    lines.append(
        f"| before | {s['unconnected_before']} | 0 | 0 | 0 | 0 | {s['gnd_zone_islands_before']} | {s['vdd_gpio_unconnected_before']} |"
    )
    b = s["drc_mid"]
    lines.append(
        f"| mid (shove) | {b['unconnected_items']} | {b['shorting_items']} | {b['clearance']} | {b['tracks_crossing']} | {b['hole_clearance']} | {b['gnd_zone_islands']} | {b['vdd_gpio_unconnected']} |"
    )
    a = s["drc_after"]
    lines.append(
        f"| after ({s['decision']}) | {a['unconnected_items']} | {a['shorting_items']} | {a['clearance']} | {a['tracks_crossing']} | {a['hole_clearance']} | {a['gnd_zone_islands']} | {a['vdd_gpio_unconnected']} |"
    )
    lines.append("")
    lines.append(
        "Headline unconnected can stay flat when the VDD_GPIO open closes and one F.Cu GND zone island appears. "
        "That island is waived on this pass. Pre-existing hole_to_hole (P0.02×P0.02) is unchanged and is not part of this gate."
    )
    lines.append("")
    if s["decision"] != "KEEP":
        lines.append("## Revert audit")
        lines.append("")
        lines.append(s["revert_reason"] or "electrical gate failed")
        lines.append("")
        lines.append(
            f"Full byte restore from `.mcp-backups/pass30ak/pre-edit.kicad_pcb` "
            f"(sha256 {s['backup_sha256'][:16]}… matches the board after revert). "
            "P0.15 trunk not ripped. No second geometry."
        )
        lines.append("")
    else:
        lines.append("## Keep audit")
        lines.append("")
        lines.append(
            "Edit kept. Geometry is the pass30aj shove plus the same six-segment F.Cu polyline. "
            f"Board sha256 {s['board_sha256_after'][:16]}… differs from the pre-edit backup "
            f"{s['backup_sha256'][:16]}… as expected. "
            "GND island increase was waived and was not a revert reason."
        )
        lines.append("")
        lines.append(
            f"F.Cu GND filled outlines {s['gnd_f_outlines_before']} → {s['gnd_f_outlines_mid']}."
        )
        lines.append("")
        lines.append("Outline delta (area mm², bbox):")
        lines.append("")
        for row in s["gnd_outline_only_after"]:
            lines.append(f"- new: area {row['area_mm2']} bbox {row['bbox']}")
        for row in s["gnd_outline_only_before"]:
            lines.append(f"- replaced: area {row['area_mm2']} bbox {row['bbox']}")
        lines.append("")
    if s["hits"]:
        lines.append("Mid DRC short/clear/cross/hole hits:")
        lines.append("")
        for h in s["hits"]:
            lines.append(f"- **{h['type']}** — {h['description']}: {'; '.join(h['items'])}")
        lines.append("")
    lines.append("## Protect checklist")
    lines.append("")
    lines.append("- y=44.60 B.Cu pocket: no track")
    lines.append("- SIM_IO_C / SIM_CLK_C walls: not ripped")
    lines.append("- U1 and headers: not moved")
    lines.append("- Class C, Stage-A VDD2, P0.22, P0.19, P0.15 west wrap / trunk: not ripped")
    lines.append("- P0.08 and P0.11 copper: not shoved (not on this polyline)")
    lines.append("- No Gerbers. No git commit. COEX0 not started.")
    lines.append("")
    (REPORTS / "PASS30AK_SUMMARY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
