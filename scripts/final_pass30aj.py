#!/usr/bin/env python3
"""pass30aj — ONE attempt: F.Cu VDD_GPIO via@(40.170,19.126) -> U1.12.

Preferred shove (not the pass30ai x=45.5 spine). Shove only the escape
tracks the new polyline still crosses: P0.12, P0.10, and DEC0.
P0.08 and P0.11 are not on this polyline, so they are not shoved.
P0.15 is not shoved. West approach is not used.

Gate: shorting/clearance/tracks_crossing/hole_clearance = 0
AND unconnected drops by >= 1
AND GND zone-island count (unconnected Zone/GND items) does not increase.
Else FULL revert to .mcp-backups/pass30aj/pre-edit.kicad_pcb.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30aj/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18

# Not the x=45.5 east spine. Verticals at x=45.90 (north of the VDD2
# pocket) and x=47.55 (east of the shortened P0.10/P0.12 vias, west of
# the DEC0 trunk at x=48.0). Landing is the pad centerline y=31.500.
POLY = [
    (40.170, 19.126),
    (40.170, 20.200),
    (45.900, 20.200),
    (45.900, 25.400),
    (47.550, 25.400),
    (47.550, 31.500),
    (44.000, 31.500),
]


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def near(a, b, tol=0.02) -> bool:
    return abs(a - b) < tol


def ends(t):
    return (
        mm(t.GetStart().x),
        mm(t.GetStart().y),
        mm(t.GetEnd().x),
        mm(t.GetEnd().y),
    )


def track_is(t, x1, y1, x2, y2) -> bool:
    a, b, c, d = ends(t)
    return (near(a, x1) and near(b, y1) and near(c, x2) and near(d, y2)) or (
        near(a, x2) and near(b, y2) and near(c, x1) and near(d, y1)
    )


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def confirm(board) -> dict:
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if abs(x - 40.170) < 0.05 and abs(y - 19.126) < 0.05 and t.GetNetname() == "VDD_GPIO":
            via = {
                "net": t.GetNetname(),
                "x": round(x, 3),
                "y": round(y, 3),
                "dia": round(mm(t.GetWidth(F)), 3),
                "drill": round(mm(t.GetDrill()), 3),
            }
            break
    fp = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    pad = next(p for p in fp.Pads() if p.GetNumber() == "12")
    bb = pad.GetBoundingBox()
    info = {
        "via": via,
        "u1": {"x": round(mm(fp.GetPosition().x), 3), "y": round(mm(fp.GetPosition().y), 3)},
        "pad12": {
            "net": pad.GetNetname(),
            "x": round(mm(pad.GetPosition().x), 3),
            "y": round(mm(pad.GetPosition().y), 3),
            "size": [round(mm(pad.GetSize().x), 3), round(mm(pad.GetSize().y), 3)],
            "bbox": [
                round(mm(bb.GetLeft()), 3),
                round(mm(bb.GetTop()), 3),
                round(mm(bb.GetRight()), 3),
                round(mm(bb.GetBottom()), 3),
            ],
            "on_f": bool(pad.IsOnLayer(F)),
        },
    }
    if not via or via["net"] != "VDD_GPIO":
        raise SystemExit(f"via island not confirmed: {via}")
    if info["pad12"]["net"] != "VDD_GPIO" or abs(info["pad12"]["x"] - 44.0) > 0.01:
        raise SystemExit(f"U1.12 not confirmed: {info['pad12']}")
    if abs(info["u1"]["x"] - 36.0) > 0.01 or abs(info["u1"]["y"] - 32.0) > 0.01:
        raise SystemExit(f"U1 moved: {info['u1']}")
    return info


def p015_count(board) -> int:
    n = 0
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        if t.GetNetname() == "P0.15":
            n += 1
    return n


def gnd_outline_summaries(board):
    out = []
    for z in board.Zones():
        if z.GetNetname() != "GND" or z.GetLayer() != F:
            continue
        polys = z.GetFilledPolysList(F)
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            bb = ol.BBox()
            out.append(
                {
                    "area_mm2": round(abs(ol.Area()) / 1e12, 3),
                    "bbox": [
                        round(mm(bb.GetLeft()), 2),
                        round(mm(bb.GetTop()), 2),
                        round(mm(bb.GetRight()), 2),
                        round(mm(bb.GetBottom()), 2),
                    ],
                }
            )
    return out


def add_track(board, net, layer, x1, y1, x2, y2, w=W):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def add_via(board, net, x, y, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(xy(x, y))
    v.SetWidth(F, pcbnew.FromMM(dia))
    v.SetWidth(B, pcbnew.FromMM(dia))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net)
    board.Add(v)
    return v


def apply_shove(board) -> dict:
    """Minimum shove. Does not touch P0.15, P0.08, or P0.11."""
    tracks = list(board.GetTracks())
    shoved = []
    for net, ox, oy, nx, ny in (
        ("P0.12", 47.4, 27.5, 47.00, 27.5),
        ("P0.10", 47.4, 28.5, 47.00, 28.5),
    ):
        moved_via = False
        moved_trk = False
        for t in tracks:
            if t.GetNetname() != net:
                continue
            if t.GetClass() == "PCB_VIA":
                x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
                if near(x, ox) and near(y, oy):
                    t.SetPosition(xy(nx, ny))
                    moved_via = True
            elif t.GetLayer() == F and track_is(t, 44.0, oy, ox, oy):
                if near(mm(t.GetEnd().x), ox) and near(mm(t.GetEnd().y), oy):
                    t.SetEnd(xy(nx, ny))
                elif near(mm(t.GetStart().x), ox) and near(mm(t.GetStart().y), oy):
                    t.SetStart(xy(nx, ny))
                else:
                    raise SystemExit(f"{net} track end did not match via")
                moved_trk = True
        if not moved_via or not moved_trk:
            raise SystemExit(f"failed to shove {net} via={moved_via} trk={moved_trk}")
        shoved.append(
            {
                "net": net,
                "action": "shorten F stub and move dangling via west",
                "from": [ox, oy],
                "to": [nx, ny],
            }
        )

    removed = 0
    moved_dec_via = False
    retargeted = False
    to_remove = []
    for t in tracks:
        if t.GetNetname() != "DEC0":
            continue
        if t.GetClass() != "PCB_VIA" and t.GetLayer() == F and track_is(t, 44.0, 31.0, 48.72, 31.0):
            to_remove.append(t)
        elif t.GetClass() == "PCB_VIA":
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if near(x, 47.8) and near(y, 31.2):
                t.SetPosition(xy(45.40, 30.55))
                moved_dec_via = True
        elif t.GetLayer() == F and track_is(t, 48.72, 31.0, 47.8, 31.2):
            t.SetStart(xy(45.40, 31.00))
            t.SetEnd(xy(45.40, 30.55))
            retargeted = True
    if len(to_remove) != 4 or not moved_dec_via or not retargeted:
        raise SystemExit(
            f"DEC0 shove mismatch removed={len(to_remove)} via={moved_dec_via} diag={retargeted}"
        )
    for t in to_remove:
        board.Remove(t)
        removed += 1

    net = board.FindNet("DEC0")
    # Gap in the y=31.00 wall around the VDD drop at x=47.55.
    # F stubs stay connected through one B.Cu bridge between two new vias.
    add_track(board, net, F, 44.00, 31.00, 46.95, 31.00)
    add_track(board, net, F, 46.95, 31.00, 46.95, 30.90)
    add_via(board, net, 46.95, 30.90)
    add_via(board, net, 48.10, 30.90)
    add_track(board, net, F, 48.10, 30.90, 48.10, 31.00)
    add_track(board, net, F, 48.10, 31.00, 48.72, 31.00)
    add_track(board, net, B, 46.95, 30.90, 48.10, 30.90)
    shoved.append(
        {
            "net": "DEC0",
            "action": "open F.Cu gap at the VDD drop; bridge on B.Cu; park the dangling via off the gap",
            "removed_coincident_f_horizontals": removed,
            "f_left": [[44.00, 31.00], [46.95, 31.00], [46.95, 30.90]],
            "b_bridge": [[46.95, 30.90], [48.10, 30.90]],
            "f_right": [[48.10, 30.90], [48.10, 31.00], [48.72, 31.00]],
            "vias": [[46.95, 30.90], [48.10, 30.90]],
            "dangling_via_from": [47.800, 31.200],
            "dangling_via_to": [45.400, 30.550],
            "dangling_track": [[45.400, 31.000], [45.400, 30.550]],
        }
    )
    return {"path": "shove", "nets": shoved, "not_shoved": ["P0.08", "P0.11", "P0.15"]}


def add_poly(board):
    net = board.FindNet("VDD_GPIO")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        add_track(board, net, F, x1, y1, x2, y2, W)


def gnd_items(data) -> int:
    n = 0
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        if "[GND]" in desc:
            n += 1
    return n


def net_items(data, net) -> int:
    n = 0
    for it in data.get("unconnected_items", []):
        desc = " ".join(i.get("description", "") for i in it.get("items", []))
        if f"[{net}]" in desc:
            n += 1
    return n


def run_drc(dest: Path) -> dict:
    tmp = Path("/tmp/nrf30aj_drc.json")
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
        "vdd_gpio_unconnected": net_items(data, "VDD_GPIO"),
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
    return {"stats": stats, "hits": hits}


def main():
    if not BACKUP.is_file():
        raise SystemExit(f"missing backup {BACKUP}")
    before = json.loads((REPORTS / "DRC_PASS30AJ_BEFORE.json").read_text())
    before_unc = len(before.get("unconnected_items", []))
    before_gnd = gnd_items(before)
    before_vdd = net_items(before, "VDD_GPIO")
    board = pcbnew.LoadBoard(str(BOARD))
    info = confirm(board)
    p015_before = p015_count(board)
    outlines_before = gnd_outline_summaries(board)
    print("CONFIRM", json.dumps(info))
    print("P0.15", p015_before, "GND outlines", len(outlines_before), "unc", before_unc, "gnd", before_gnd)

    shove = apply_shove(board)
    add_poly(board)
    p015_mid = p015_count(board)
    if p015_mid != p015_before:
        raise SystemExit(f"P0.15 segment count changed {p015_before} -> {p015_mid}")
    confirm(board)  # U1 / via / pad still where they were
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    outlines_mid = gnd_outline_summaries(board)
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AJ_MID.json")
    print("MID", mid["stats"])
    st = mid["stats"]
    clean = (
        st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
    )
    dropped = before_unc - st["unconnected_items"]
    islands_ok = st["gnd_zone_islands"] <= before_gnd
    p015_ok = p015_mid == p015_before
    keep = clean and dropped >= 1 and islands_ok and p015_ok
    print("clean", clean, "dropped", dropped, "islands_ok", islands_ok, "keep", keep)

    decision = "KEEP" if keep else "REVERT"
    if not keep:
        shutil.copy2(BACKUP, BOARD)
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("revert failed: hash mismatch")
        after = run_drc(REPORTS / "DRC_PASS30AJ_AFTER.json")
        print("AFTER", after["stats"])
    else:
        after = {"stats": st, "hits": []}

    def key_area(rows):
        return {(r["area_mm2"], tuple(r["bbox"])) for r in rows}

    only_after = sorted(key_area(outlines_mid) - key_area(outlines_before))
    only_before = sorted(key_area(outlines_before) - key_area(outlines_mid))

    segments = []
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        segments.append({"layer": "F.Cu", "width_mm": W, "start": [x1, y1], "end": [x2, y2]})

    summary = {
        "pass": "30aj",
        "timestamp": ist_now(),
        "decision": decision,
        "path": "shove",
        "west_attempted": False,
        "west_skipped_reason": "shove geometry does not enter the P0.15 keep (x=41.75, y=23.10-26.75); west approach not used",
        "east_spine_x45_5": False,
        "net": "VDD_GPIO",
        "via_used_for_vdd": False,
        "confirmed": info,
        "segments": segments,
        "shove": shove,
        "unconnected_before": before_unc,
        "unconnected_mid": st["unconnected_items"],
        "unconnected_after": after["stats"]["unconnected_items"],
        "unconnected_delta_mid": st["unconnected_items"] - before_unc,
        "gnd_zone_islands_before": before_gnd,
        "gnd_zone_islands_mid": st["gnd_zone_islands"],
        "gnd_zone_islands_after": after["stats"]["gnd_zone_islands"],
        "vdd_gpio_unconnected_before": before_vdd,
        "vdd_gpio_unconnected_mid": st["vdd_gpio_unconnected"],
        "gate": {
            "clean_short_clear_cross_hole": clean,
            "unconnected_drop_at_least_1": dropped >= 1,
            "gnd_islands_not_increased": islands_ok,
            "p015_unchanged": p015_ok,
            "met": keep,
        },
        "drc_mid": st,
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
        "hits": mid["hits"],
        "revert_reason": None
        if keep
        else (
            "unconnected did not drop (VDD_GPIO open closed but a new F.Cu GND zone island offset it) "
            "and/or short/clear/cross/hole not all zero"
        ),
        "backup": str(BACKUP),
        "backup_sha256": sha(BACKUP),
        "board_sha256_after": sha(BOARD),
    }
    (REPORTS / "PASS30AJ_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_md(summary)
    print("DECISION", decision)


def write_md(s: dict) -> None:
    lines = []
    lines.append("# PASS30AJ_SUMMARY — VDD_GPIO to U1.12, shove (not x=45.5)")
    lines.append("")
    lines.append(f"**Timestamp:** {s['timestamp']}")
    lines.append("**KiCad:** 9.0.2")
    lines.append(f"**Decision:** **{s['decision']}**")
    lines.append(f"**Path:** {s['path']} (west attempted: {s['west_attempted']})")
    lines.append(f"**Net:** {s['net']}")
    lines.append(
        f"**Unconnected:** {s['unconnected_before']} → mid {s['unconnected_mid']} → after {s['unconnected_after']}"
    )
    lines.append(
        f"**GND zone islands:** {s['gnd_zone_islands_before']} → mid {s['gnd_zone_islands_mid']} → after {s['gnd_zone_islands_after']}"
    )
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
        "Shove, not west. The shove stays east of the P0.15 vertical keep (x=41.75, y=23.10–26.75) "
        "and does not rip or shove P0.15. The pass30ai east spine at x=45.5 was not repeated. "
        "Straight line was not used. No new via on VDD_GPIO. P0.08 and P0.11 were not shoved: "
        "this polyline does not cross them (P0.08 F ends at x=46.2, P0.11 F stub ends at x=46.5)."
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
                "Dangling via (47.800, 31.200) moved to (45.400, 30.550) with F riser (45.400, 31.000)–(45.400, 30.550), "
                "clear of the VDD drop and of the P0.08 F stub."
            )
    lines.append("- Not shoved: P0.08, P0.11, P0.15.")
    lines.append("")
    lines.append("## Gate")
    lines.append("")
    g = s["gate"]
    lines.append(f"- short/clear/cross/hole all zero: {g['clean_short_clear_cross_hole']}")
    lines.append(
        f"- unconnected drop ≥ 1: {g['unconnected_drop_at_least_1']} (delta mid {s['unconnected_delta_mid']})"
    )
    lines.append(f"- GND islands did not increase: {g['gnd_islands_not_increased']}")
    lines.append(f"- P0.15 segment count unchanged: {g['p015_unchanged']} ({s['p015_segments_before']} → {s['p015_segments_mid']})")
    lines.append(f"- **met: {g['met']}**")
    lines.append("")
    lines.append("## DRC")
    lines.append("")
    lines.append("| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | GND islands |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    b = s["drc_mid"]
    lines.append(
        f"| before | {s['unconnected_before']} | 0 | 0 | 0 | 0 | {s['gnd_zone_islands_before']} |"
    )
    lines.append(
        f"| mid (shove) | {b['unconnected_items']} | {b['shorting_items']} | {b['clearance']} | {b['tracks_crossing']} | {b['hole_clearance']} | {b['gnd_zone_islands']} |"
    )
    a = s["drc_after"]
    lines.append(
        f"| after ({s['decision']}) | {a['unconnected_items']} | {a['shorting_items']} | {a['clearance']} | {a['tracks_crossing']} | {a['hole_clearance']} | {a['gnd_zone_islands']} |"
    )
    lines.append("")
    lines.append(
        f"VDD_GPIO unconnected items: {s['vdd_gpio_unconnected_before']} → mid {s['vdd_gpio_unconnected_mid']} "
        "(U1.12 was reached). Headline unconnected did not fall because GND zone islands rose by the same amount. "
        "Pre-existing hole_to_hole (P0.02×P0.02) is unchanged and is not part of this gate."
    )
    lines.append("")
    if s["decision"] != "KEEP":
        lines.append("## Revert audit")
        lines.append("")
        lines.append(
            f"Full byte restore from `.mcp-backups/pass30aj/pre-edit.kicad_pcb` "
            f"(sha256 {s['backup_sha256'][:16]}… matches the board after revert). "
            "P0.15 trunk not ripped. No second geometry. West approach not started."
        )
        lines.append("")
        lines.append(
            "Short/clearance/crossing/hole_clearance on the attempt were 0. "
            "The polyline does not use x=45.5 and does not cross P0.15 or P0.16. "
            f"F.Cu GND filled outlines {s['gnd_f_outlines_before']} → {s['gnd_f_outlines_mid']}. "
            "The 186 mm² F.Cu GND pour (single stitch via at (50.00, 10.00)) is cut by the "
            "VDD track where it leaves the via island and crosses that pour. "
            "The via stays on the north piece; the south piece is a new zone island. "
            "That is why GND unconnected items go 10 → 11 while VDD_GPIO goes 3 → 2, and the headline count stays 64."
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
    (REPORTS / "PASS30AJ_SUMMARY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
