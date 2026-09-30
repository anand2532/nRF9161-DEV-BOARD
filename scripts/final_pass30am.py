#!/usr/bin/env python3
"""pass30am — ONE attempt: close the shortest non-GND island gap.

Live shortest non-GND gap is VDD_GPIO 17.626 mm:
  F.Cu (75.14, 32.00)–(75.14, 39.05)  <->  B.Cu (70.00, 8.00)–(70.00, 14.80)
Same-layer nearest is 18.444 mm on B.Cu. The straight B.Cu line hits VIN_F,
P0.08 and COEX2. Both islands already have F.Cu, so no via is required.

Route (4 segments, 0.18 mm, F.Cu only), all x>24.2, y<=26:
  (71.300, 8.000) -> (71.300, 7.300) -> (77.300, 7.300)
  -> (81.500, 13.500) -> (86.510, 26.000)
Starts on the existing VDD_GPIO via (71.300, 8.000) of the U1.12 island and
lands on the east-island junction (86.510, 26.000) at R14.2 / the y=26 run.
Does not touch the locked U1.12 polyline, COEX0, DEC0 bridge, or P0.10/P0.12.

KEEP if VDD_GPIO opens drop, no other non-GND net gains an open, and
short/clearance/crossing/hole_clearance are 0. Extra GND zone islands are
waived. hole_to_hole must not increase. Else FULL REVERT.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pcbnew

ROOT = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD")
BOARD = ROOT / "nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = ROOT / ".mcp-backups/pass30am/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18

POLY = [
    (71.300, 8.000),
    (71.300, 7.300),
    (77.300, 7.300),
    (81.500, 13.500),
    (86.510, 26.000),
]

VDD_POLY = [
    (40.170, 19.126),
    (40.170, 20.200),
    (45.900, 20.200),
    (45.900, 25.400),
    (47.550, 25.400),
    (47.550, 31.500),
    (44.000, 31.500),
]

COEX0_B = [
    ((31.110, 22.000), (32.250, 22.000)),
    ((32.250, 22.000), (32.250, 30.500)),
    ((32.250, 30.500), (37.000, 30.500)),
]
COEX0_F = [
    ((37.000, 30.500), (37.000, 35.900)),
    ((37.000, 35.900), (38.750, 35.900)),
    ((38.750, 35.900), (38.750, 37.250)),
]


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def near(a, b, tol=0.02) -> bool:
    return abs(a - b) < tol


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ends(t):
    return (mm(t.GetStart().x), mm(t.GetStart().y), mm(t.GetEnd().x), mm(t.GetEnd().y))


def track_is(t, x1, y1, x2, y2) -> bool:
    a, b, c, d = ends(t)
    return (near(a, x1) and near(b, y1) and near(c, x2) and near(d, y2)) or (
        near(a, x2) and near(b, y2) and near(c, x1) and near(d, y1)
    )


def add_track(board, net, layer, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(W))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def p015_count(board) -> int:
    return sum(
        1
        for t in board.GetTracks()
        if t.GetNetname() == "P0.15" and t.GetClass() != "PCB_VIA"
    )


def vdd_poly_ok(board) -> bool:
    tracks = [
        t
        for t in board.GetTracks()
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == "VDD_GPIO" and t.GetLayer() == F
    ]
    for (x1, y1), (x2, y2) in zip(VDD_POLY, VDD_POLY[1:]):
        if not any(track_is(t, x1, y1, x2, y2) and abs(mm(t.GetWidth()) - W) < 0.001 for t in tracks):
            return False
    return True


def dec0_bridge_ok(board) -> bool:
    for t in board.GetTracks():
        if t.GetNetname() == "DEC0" and t.GetLayer() == B and track_is(t, 46.950, 30.900, 48.100, 30.900):
            return True
    return False


def coex0_ok(board) -> bool:
    tracks = [t for t in board.GetTracks() if t.GetNetname() == "COEX0" and t.GetClass() != "PCB_VIA"]
    vias = [t for t in board.GetTracks() if t.GetNetname() == "COEX0" and t.GetClass() == "PCB_VIA"]
    if not any(near(mm(v.GetPosition().x), 37.0) and near(mm(v.GetPosition().y), 30.5) for v in vias):
        return False
    for (x1, y1), (x2, y2) in COEX0_B:
        if not any(t.GetLayer() == B and track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    for (x1, y1), (x2, y2) in COEX0_F:
        if not any(t.GetLayer() == F and track_is(t, x1, y1, x2, y2) for t in tracks):
            return False
    return True


def via_at(board, net, x, y) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if near(mm(t.GetPosition().x), x) and near(mm(t.GetPosition().y), y):
            return True
    return False


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
    tmp = Path("/tmp/nrf30am_drc.json")
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
        "vdd_gpio_unconnected": nongnd_counts(data).get("VDD_GPIO", 0),
        "via_dangling": vc.get("via_dangling", 0),
        "track_dangling": vc.get("track_dangling", 0),
    }
    return {"stats": stats, "data": data}


def apply_route(board):
    net = board.FindNet("VDD_GPIO")
    if net is None:
        raise SystemExit("VDD_GPIO net missing")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        add_track(board, net, F, x1, y1, x2, y2)


def segment_rows():
    rows = []
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        rows.append({"layer": "F.Cu", "width_mm": W, "start": [x1, y1], "end": [x2, y2]})
    return rows


def protect_ok(board) -> bool:
    return (
        p015_count(board) == 42
        and vdd_poly_ok(board)
        and dec0_bridge_ok(board)
        and coex0_ok(board)
        and via_at(board, "P0.10", 47.0, 28.5)
        and via_at(board, "P0.12", 47.0, 27.5)
    )


def write_outputs(decision, info, before_stats, after_stats, gained, reason, keep):
    ts = ist_now()
    segs = segment_rows()
    b = before_stats
    a = after_stats
    payload = {
        "pass": "30am",
        "timestamp": ts,
        "decision": decision,
        "routed": True,
        "net": "VDD_GPIO",
        "via_used": False,
        "gap_mm": 17.626,
        "same_layer_gap_mm": 18.444,
        "same_layer": "B.Cu",
        "island_a": {
            "closest_mm": [75.080, 31.808],
            "item": "F.Cu (75.14,32.00)-(75.14,39.05)",
            "layers": ["F.Cu"],
        },
        "island_b": {
            "closest_mm": [70.036, 14.920],
            "item": "B.Cu (70.00,8.00)-(70.00,14.80)",
            "layers": ["B.Cu"],
        },
        "why_not_straight": (
            "Closest copper is cross-layer (F.Cu vs B.Cu). Straight B.Cu between the "
            "same-layer points hits VIN_F, P0.08 and COEX2. COEX2's B.Cu vertical at "
            "x=72 walls the corridor north of y=24.60, and P0.08 B.Cu at y=30.25 spans "
            "x=46.20-78.50. The U1.12 landing was not repeated."
        ),
        "segments": segs,
        "segment_count": len(segs),
        "confirmed": info,
        "before": b,
        "after": a,
        "vdd_gpio_opens": {
            "before": b.get("vdd_gpio_unconnected"),
            "after": a.get("vdd_gpio_unconnected"),
        },
        "headline_unconnected": {
            "before": b.get("unconnected_items"),
            "after": a.get("unconnected_items"),
        },
        "gnd_islands": {
            "before": b.get("gnd_zone_islands"),
            "after": a.get("gnd_zone_islands"),
            "waived": True,
        },
        "nongnd_gained": gained,
        "hole_to_hole": {
            "before": b.get("hole_to_hole"),
            "after": a.get("hole_to_hole"),
        },
        "gate_met": keep,
        "reason": reason,
        "protect": {
            "vdd_gpio_u1_12_polyline": info.get("vdd_poly_after"),
            "coex0_locked": info.get("coex0_after"),
            "dec0_bcu_bridge": info.get("dec0_after"),
            "p010_via_x47": info.get("p010_after"),
            "p012_via_x47": info.get("p012_after"),
            "p015_segments": {"before": info.get("p015"), "after": info.get("p015_after")},
            "u1_unmoved": True,
            "headers_unmoved": not info.get("moved"),
            "y_44_60_pocket": "not used",
            "min_x": 71.300,
            "gerbers": False,
            "git_commit": False,
        },
    }
    (REPORTS / "PASS30AM_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")

    def row(s):
        return (
            f"| {s['layer']} | ({s['start'][0]:.3f}, {s['start'][1]:.3f}) | "
            f"({s['end'][0]:.3f}, {s['end'][1]:.3f}) | {s['width_mm']:.2f} mm |"
        )

    lines = [
        "# PASS30AM_SUMMARY — VDD_GPIO east island (GND islands waived)",
        "",
        f"**Timestamp:** {ts}",
        "**KiCad:** 9.0.2",
        f"**Decision:** **{decision}**",
        "**Net:** VDD_GPIO",
        "**Via:** no",
        f"**Segments:** {len(segs)} (limit 6)",
        "**Shortest non-GND gap:** 17.626 mm (≤ 20 mm)",
        f"**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}",
        f"**VDD_GPIO opens:** {b.get('vdd_gpio_unconnected')} → {a.get('vdd_gpio_unconnected')}",
        f"**GND zone islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (increase WAIVED)",
        "",
        "## Why this gap",
        "",
        "Remeasured live copper after pass30al. Headline unconnected 63, GND islands 11.",
        "Shortest remaining non-GND island gap is VDD_GPIO **17.626 mm**:",
        "",
        "- Island A (east, J9/J10/U2/R14): closest copper (75.080, 31.808) on F.Cu (75.14, 32.00)–(75.14, 39.05)",
        "- Island B (U1.12 / TP10 / U3): closest copper (70.036, 14.920) on B.Cu (70.00, 8.00)–(70.00, 14.80)",
        "- Same-layer nearest: 18.444 mm on B.Cu, (77.831, 31.637) ↔ (70.053, 14.913)",
        "",
        "The straight line is not used. Closest points are on different layers. The B.Cu",
        "straight line hits VIN_F, the P0.08 trunk at y=30.25 (x=46.20–78.50) and COEX2.",
        "COEX2's B.Cu vertical at x=72 closes the northbound corridor, so a same-layer B.Cu",
        "join needs a via to hop it. Both islands already have F.Cu, so the route stays on",
        "F.Cu and does not add a via. It does not repeat the locked U1.12 polyline",
        "(40.170, 19.126)→(44.000, 31.500) and does not rip COEX0.",
        "",
        "## Path",
        "",
        "South from the existing via (71.300, 8.000) on the U1.12 island, east under",
        "D3/LED_PWR at y=7.300 (clear of VIN pad D3.1 and the VIN_IN trunk at y=6), then",
        "northeast past the GND via at (80, 10) to the east-island F.Cu junction",
        "(86.510, 26.000), which is the R14.2 / (86.51, 26)–(87.81, 26) corner. Minimum",
        "x is 71.300 (>24.2). Maximum y is 26.000. The y=44.60 B.Cu pocket is not used.",
        "",
        f"Reason: {reason}",
        "",
        "### Segments (0.18 mm)",
        "",
        "| layer | start | end | width |",
        "| --- | --- | --- | --- |",
    ]
    for s in segs:
        lines.append(row(s))
    lines += [
        "",
        "No via added.",
        "",
        "## Gate (GND islands waived)",
        "",
        f"- short/clear/cross/hole_clearance all zero: "
        f"{a.get('shorting_items')==0 and a.get('clearance')==0 and a.get('tracks_crossing')==0 and a.get('hole_clearance')==0}",
        f"- VDD_GPIO opens drop: {b.get('vdd_gpio_unconnected')} → {a.get('vdd_gpio_unconnected')}",
        f"- no non-GND net gained an open: {not gained} {gained or ''}",
        f"- hole_to_hole did not increase: {b.get('hole_to_hole')} → {a.get('hole_to_hole')}",
        f"- GND islands: WAIVED ({b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')})",
        f"- **met: {keep}**",
        "",
        "## DRC",
        "",
        "| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| before | {b.get('unconnected_items')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} | {b.get('vdd_gpio_unconnected')} |",
        f"| after ({decision}) | {a.get('unconnected_items')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} | {a.get('vdd_gpio_unconnected')} |",
        "",
        "## Protect checklist",
        "",
        "- Locked VDD_GPIO F.Cu polyline to U1.12 still present (not the route repeated)",
        "- COEX0 via (37.000, 30.500) and the six locked segments still present",
        "- P0.10 via (47.000, 28.500) and P0.12 via (47.000, 27.500) not moved",
        "- DEC0 B.Cu bridge (46.950, 30.900)–(48.100, 30.900) not ripped",
        f"- P0.15 west wrap segment count {info.get('p015')} → {info.get('p015_after')}",
        "- Class C C22/C23/C24, P0.22, P0.19, Stage-A VDD2, SIM_IO_C/SIM_CLK_C walls not ripped",
        f"- Footprints moved: {info.get('moved') or 'none'}",
        "- y=44.60 B.Cu pocket not used",
        "- RF keepout: this route stays east of x=24.2 (min x=71.300)",
        "- No Gerbers. No git commit.",
        "",
    ]
    (REPORTS / "PASS30AM_SUMMARY.md").write_text("\n".join(lines))
    return ts


def patch_review(ts, decision, before_stats, after_stats):
    text = REVIEW.read_text()
    b, a = before_stats, after_stats
    banner = (
        f"**Review date:** {ts} (Asia/Calcutta) — pass30am VDD_GPIO east "
        f"{decision} (unc {b.get('unconnected_items')}→{a.get('unconnected_items')}; "
        f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}; "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} waived). "
    )
    pre, sep, post = text.partition("**Review date:**")
    if not sep:
        raise SystemExit("review date line missing")
    # drop the old review-date sentence through the end of that line
    rest = post.split("\n", 1)[1]
    text = pre + banner + "Prior: pass30al COEX0 KEEP (unc 64→63). " + rest.lstrip()
    # the previous line body started after the date; we replaced the whole line.
    # `rest` is everything after the first newline, which is correct.

    delta = (
        f"**Pass delta (pass30am):** VDD_GPIO east island, **{decision}**. Shortest remaining "
        f"non-GND gap 17.626 mm (F.Cu y=32 trunk ↔ B.Cu x=70 riser). Straight B.Cu hits "
        f"VIN_F / P0.08 / COEX2; COEX2 at x=72 walls a B.Cu hop. Four 0.18 mm F.Cu segments, "
        f"no via: (71.300, 8.000)→(71.300, 7.300)→(77.300, 7.300)→(81.500, 13.500)→"
        f"(86.510, 26.000), from the existing via (71.300, 8.000) onto the R14 junction. "
        f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. "
        f"Headline unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole_clearance "
        f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"Locked U1.12 polyline, COEX0, DEC0 bridge, P0.10/P0.12 x=47.0 not ripped. "
        f"No U1/header move. No y=44.60 pocket. x>24.2. No Gerbers. "
        f"Details: `reports/PASS30AM_SUMMARY.md`.\n\n"
    )
    needle = "**Pass delta (pass30al):**"
    if needle not in text:
        raise SystemExit("review doc anchor missing")
    if "**Pass delta (pass30am):**" not in text:
        text = text.replace(needle, delta + needle, 1)
    text = text.replace(
        "| **unconnected_items** | **63** | `reports/DRC_PASS30AL_AFTER.json` (live `kicad-cli` 9.0.2). COEX0 opens 1→0. GND islands 11→11. Prior pass30ak VDD_GPIO kept",
        f"| **unconnected_items** | **{a.get('unconnected_items')}** | `reports/DRC_PASS30AM_AFTER.json` (live `kicad-cli` 9.0.2). VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). Prior pass30al COEX0 kept",
    )
    text = text.replace(
        "| **shorting_items** | **0** | `reports/DRC_PASS30AL_AFTER.json` |",
        "| **shorting_items** | **0** | `reports/DRC_PASS30AM_AFTER.json` |",
    )
    REVIEW.write_text(text)


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if BACKUP.is_file():
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit(
                "pass30am backup exists and the live board does not match it; "
                "refusing to clobber the pre-edit or double-apply"
            )
    else:
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup hash mismatch before edit")

    print("BACKUP", sha(BACKUP)[:16])
    before = run_drc(REPORTS / "DRC_PASS30AM_BEFORE.json")
    print("BEFORE", before["stats"])
    if before["stats"]["unconnected_items"] != 63:
        raise SystemExit(f"expected headline 63, got {before['stats']['unconnected_items']}")

    board = pcbnew.LoadBoard(str(BOARD))
    if not protect_ok(board):
        raise SystemExit(
            f"protect confirm failed p015={p015_count(board)} vdd={vdd_poly_ok(board)} "
            f"dec0={dec0_bridge_ok(board)} coex0={coex0_ok(board)} "
            f"p010={via_at(board,'P0.10',47.0,28.5)} p012={via_at(board,'P0.12',47.0,27.5)}"
        )
    u1 = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    if not near(mm(u1.GetPosition().x), 36.0) or not near(mm(u1.GetPosition().y), 32.0):
        raise SystemExit("U1 moved before edit; refusing")
    if not via_at(board, "VDD_GPIO", 71.3, 8.0):
        raise SystemExit("start via (71.3, 8.0) missing")
    fp_before = footprint_xy(board)
    info = {
        "u1": {"x": round(mm(u1.GetPosition().x), 3), "y": round(mm(u1.GetPosition().y), 3)},
        "p015": p015_count(board),
        "vdd_poly": vdd_poly_ok(board),
        "dec0": dec0_bridge_ok(board),
        "coex0": coex0_ok(board),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
    }

    apply_route(board)
    info["p015_after"] = p015_count(board)
    info["vdd_poly_after"] = vdd_poly_ok(board)
    info["dec0_after"] = dec0_bridge_ok(board)
    info["coex0_after"] = coex0_ok(board)
    info["p010_after"] = via_at(board, "P0.10", 47.0, 28.5)
    info["p012_after"] = via_at(board, "P0.12", 47.0, 27.5)
    fp_after = footprint_xy(board)
    moved = sorted(ref for ref in fp_before if fp_before[ref] != fp_after.get(ref))
    info["moved"] = moved
    if (
        info["p015_after"] != 42
        or not info["vdd_poly_after"]
        or not info["dec0_after"]
        or not info["coex0_after"]
        or not info["p010_after"]
        or not info["p012_after"]
        or moved
    ):
        shutil.copy2(BACKUP, BOARD)
        after = run_drc(REPORTS / "DRC_PASS30AM_AFTER.json")
        write_outputs(
            "REVERT",
            info,
            before["stats"],
            after["stats"],
            {},
            f"geometry guard failed {info}",
            False,
        )
        patch_review(ist_now(), "REVERT", before["stats"], after["stats"])
        print("REVERT guard", info)
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AM_MID.json")
    print("MID", mid["stats"])
    gained = {}
    bc = nongnd_counts(before["data"])
    ac = nongnd_counts(mid["data"])
    for n in set(ac) | set(bc):
        if ac[n] > bc[n]:
            gained[n] = {"before": bc[n], "after": ac[n]}
    st = mid["stats"]
    bst = before["stats"]
    electrical = (
        st["vdd_gpio_unconnected"] < bst["vdd_gpio_unconnected"]
        and not gained
        and st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
        and st["hole_to_hole"] <= bst["hole_to_hole"]
    )
    if electrical:
        shutil.copy2(REPORTS / "DRC_PASS30AM_MID.json", REPORTS / "DRC_PASS30AM_AFTER.json")
        reason = (
            "VDD_GPIO open closed (U1.12 island to the east J9/U2 island) without a new "
            "short, clearance, crossing, or hole hit. No via. Straight B.Cu was not used. "
            "Locked COEX0 and the U1.12 polyline were not ripped."
        )
        ts = write_outputs("KEEP", info, bst, st, gained, reason, True)
        patch_review(ts, "KEEP", bst, st)
        print("KEEP", st)
        return

    shutil.copy2(BACKUP, BOARD)
    after = run_drc(REPORTS / "DRC_PASS30AM_AFTER.json")
    reason = (
        f"REVERT. VDD_GPIO {bst['vdd_gpio_unconnected']}→{st['vdd_gpio_unconnected']}, "
        f"gained={gained}, short/clear/cross/hole "
        f"{st['shorting_items']}/{st['clearance']}/{st['tracks_crossing']}/{st['hole_clearance']}, "
        f"hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}, "
        f"GND islands {bst['gnd_zone_islands']}→{st['gnd_zone_islands']} (waived, not the revert reason)."
    )
    # summary after-stats are the restored board; record the failed mid in the reason
    ts = write_outputs("REVERT", info, bst, after["stats"], gained, reason, False)
    patch_review(ts, "REVERT", bst, after["stats"])
    print("REVERT", reason)


if __name__ == "__main__":
    main()
