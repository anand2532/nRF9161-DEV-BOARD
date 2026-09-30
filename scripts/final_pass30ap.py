#!/usr/bin/env python3
"""pass30ap — ONE attempt: close the last VDD_GPIO open.

Island A (F.Cu, includes the existing via at the U2.5 stub) to island B
(J18.9). Straight F.Cu is not used: it hits ENABLE, SIM_CLK, and P0.20.
This jog goes around them on F.Cu, 0.18 mm, eight segments, no new via.
Starts on the existing VDD_GPIO via (76.4375, 39.050). Does not rip any
trunk or locked copper.

KEEP only if VDD_GPIO opens go 1→0, no other non-GND net gains an open,
short/clearance/crossing/hole_clearance are 0, pre-measured POWER clearance
is ≥ 0.20 mm, and hole_to_hole does not rise. Extra GND islands are waived.
Otherwise full revert. No second path.
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
BACKUP = ROOT / ".mcp-backups/pass30ap/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs/PCB_LAYOUT_REVIEW.md"
F = pcbnew.F_Cu
B = pcbnew.B_Cu
W = 0.18
CLEAR_MIN = 0.20  # POWER / VIN copper, stricter than the 0.150 mm netclass
DRC_MIN = 0.15    # POWER-vs-Default netclass clearance

# Eight segments. Start is the existing VDD_GPIO via east of U2.5.
POLY = [
    (76.4375, 39.050),
    (76.4375, 41.550),
    (74.438, 43.050),
    (72.438, 43.050),
    (71.938, 42.050),
    (70.438, 41.550),
    (54.438, 61.050),
    (54.438, 63.550),
    (58.200, 62.700),
]

POWER_FOREIGN = {
    "VDD1",
    "VDD2",
    "VDD2_MID",
    "VDD_nRF",
    "VIN",
    "VIN_F",
    "VIN_FILT",
    "VIN_IN",
}

VDD_POLY = [
    (40.170, 19.126),
    (40.170, 20.200),
    (45.900, 20.200),
    (45.900, 25.400),
    (47.550, 25.400),
    (47.550, 31.500),
    (44.000, 31.500),
]
Y7050 = [
    (71.300, 8.000),
    (71.300, 7.050),
    (77.300, 7.050),
    (81.500, 13.500),
    (86.510, 26.000),
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


def via_at(board, net, x, y) -> bool:
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        if near(mm(t.GetPosition().x), x) and near(mm(t.GetPosition().y), y):
            return True
    return False


def p015_count(board) -> int:
    return sum(1 for t in board.GetTracks() if t.GetNetname() == "P0.15" and t.GetClass() != "PCB_VIA")


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
    tmp = Path("/tmp/nrf30ap_drc.json")
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
    }
    return {"stats": stats, "data": data}


def foreign_shapes(board):
    shapes = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if net == "VDD_GPIO":
            continue
        if t.GetClass() == "PCB_VIA":
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_CIRCLE(t.GetPosition(), t.GetWidth(F) // 2),
                    net in POWER_FOREIGN,
                    f"via {net} @({mm(t.GetPosition().x):.3f},{mm(t.GetPosition().y):.3f})",
                )
            )
        elif t.GetLayer() == F:
            shapes.append(
                (
                    net,
                    pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth()),
                    net in POWER_FOREIGN,
                    (
                        f"F.Cu {net} ({mm(t.GetStart().x):.3f},{mm(t.GetStart().y):.3f})"
                        f"-({mm(t.GetEnd().x):.3f},{mm(t.GetEnd().y):.3f})"
                    ),
                )
            )
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(F) or p.GetNetname() == "VDD_GPIO":
                continue
            shapes.append(
                (
                    p.GetNetname(),
                    p.GetEffectiveShape(F),
                    p.GetNetname() in POWER_FOREIGN,
                    f"pad {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}]",
                )
            )
    return shapes


def measure_poly(shapes) -> dict:
    """Copper-edge clearance of the 0.18 mm polyline before board.Add."""
    per = []
    min_any = None
    min_pwr = None
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        sh = pcbnew.SHAPE_SEGMENT(xy(x1, y1), xy(x2, y2), pcbnew.FromMM(W))
        worst = None
        pwr = None
        for net, other, isp, desc in shapes:
            c = mm(sh.GetClearance(other))
            rec = (c, net, desc)
            if worst is None or c < worst[0]:
                worst = rec
            if isp and (pwr is None or c < pwr[0]):
                pwr = rec
        row = {
            "start": [x1, y1],
            "end": [x2, y2],
            "min_clearance_mm": None if worst is None else round(worst[0], 4),
            "min_item": None if worst is None else {"net": worst[1], "item": worst[2]},
            "min_power_mm": None if pwr is None else round(pwr[0], 4),
            "min_power_item": None if pwr is None else {"net": pwr[1], "item": pwr[2]},
        }
        per.append(row)
        if worst is not None and (min_any is None or worst[0] < min_any[0]):
            min_any = worst
        if pwr is not None and (min_pwr is None or pwr[0] < min_pwr[0]):
            min_pwr = pwr
    return {
        "segments": per,
        "min_clearance_mm": None if min_any is None else round(min_any[0], 4),
        "min_clearance_item": None if min_any is None else {"net": min_any[1], "item": min_any[2]},
        "min_power_vin_mm": None if min_pwr is None else round(min_pwr[0], 4),
        "min_power_vin_item": None if min_pwr is None else {"net": min_pwr[1], "item": min_pwr[2]},
        "meets_power_0_20": min_pwr is None or min_pwr[0] >= CLEAR_MIN - 1e-6,
        "meets_drc_0_15": min_any is None or min_any[0] >= DRC_MIN - 1e-6,
    }


def blocker_snapshot(board) -> dict:
    """Remeasure the three straight-line blockers. Coordinates from pass30ao."""
    want = {
        "ENABLE": [
            ((72.860, 40.950), (72.860, 42.400)),
            ((72.860, 42.400), (74.200, 42.400)),
        ],
        "SIM_CLK": [
            ((71.680, 44.000), (70.900, 44.000)),
            ((71.680, 44.000), (71.680, 42.400)),
        ],
        "P0.20": [
            ((55.780, 60.900), (74.160, 60.900)),
        ],
    }
    found = {k: [] for k in want}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetLayer() != F:
            continue
        net = t.GetNetname()
        if net not in want:
            continue
        for (a, b) in want[net]:
            if track_is(t, a[0], a[1], b[0], b[1]):
                found[net].append(
                    {
                        "start": [round(mm(t.GetStart().x), 3), round(mm(t.GetStart().y), 3)],
                        "end": [round(mm(t.GetEnd().x), 3), round(mm(t.GetEnd().y), 3)],
                        "width_mm": round(mm(t.GetWidth()), 3),
                    }
                )
    pads = {}
    for fp in board.GetFootprints():
        if fp.GetReference() != "U2":
            continue
        for p in fp.Pads():
            if p.GetNumber() == "3":
                pads["U2.3"] = {
                    "net": p.GetNetname(),
                    "xy": [round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)],
                }
    return {"tracks_found": found, "pad_U2_3": pads.get("U2.3")}


def pad_gap(board) -> dict:
    u2 = j18 = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "U2":
            for p in fp.Pads():
                if p.GetNumber() == "5":
                    u2 = p
        if fp.GetReference() == "J18":
            for p in fp.Pads():
                if p.GetNumber() == "9":
                    j18 = p
    if u2 is None or j18 is None:
        return {"error": "pads missing"}
    gap = mm(u2.GetEffectiveShape(F).GetClearance(j18.GetEffectiveShape(F)))
    return {
        "u2_5": [round(mm(u2.GetPosition().x), 3), round(mm(u2.GetPosition().y), 3)],
        "j18_9": [round(mm(j18.GetPosition().x), 3), round(mm(j18.GetPosition().y), 3)],
        "pad_edge_gap_mm": round(gap, 3),
        "end_on_j18_9": j18.HitTest(xy(POLY[-1][0], POLY[-1][1])),
    }


def add_route(board):
    net = board.FindNet("VDD_GPIO")
    if net is None:
        raise SystemExit("VDD_GPIO missing")
    # snap the first point onto the existing via so the track is on that pad
    via = None
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == "VDD_GPIO":
            if near(mm(t.GetPosition().x), 76.4375, 0.01) and near(mm(t.GetPosition().y), 39.050, 0.01):
                via = t
                break
    if via is None:
        raise SystemExit("existing VDD_GPIO via at (76.4375, 39.050) not found")
    pts = list(POLY)
    pts[0] = (mm(via.GetPosition().x), mm(via.GetPosition().y))
    made = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(xy(x1, y1))
        tr.SetEnd(xy(x2, y2))
        tr.SetWidth(pcbnew.FromMM(W))
        tr.SetLayer(F)
        tr.SetNet(net)
        board.Add(tr)
        made.append(tr)
    return pts, made


def protect_ok(board) -> dict:
    return {
        "y7050": poly_ok(board, Y7050, "VDD_GPIO", F),
        "u1_12_poly": poly_ok(board, VDD_POLY, "VDD_GPIO", F),
        "dec0_bridge": any(
            t.GetNetname() == "DEC0" and t.GetLayer() == B and track_is(t, 46.950, 30.900, 48.100, 30.900)
            for t in board.GetTracks()
        ),
        "coex0_via": via_at(board, "COEX0", 37.0, 30.5),
        "coex0_runs": all(
            any(t.GetNetname() == "COEX0" and t.GetLayer() == B and track_is(t, a[0], a[1], b[0], b[1]) for t in board.GetTracks())
            for a, b in COEX0_B
        )
        and all(
            any(t.GetNetname() == "COEX0" and t.GetLayer() == F and track_is(t, a[0], a[1], b[0], b[1]) for t in board.GetTracks())
            for a, b in COEX0_F
        ),
        "p010": via_at(board, "P0.10", 47.0, 28.5),
        "p012": via_at(board, "P0.12", 47.0, 27.5),
        "p015": p015_count(board),
    }


def write_outputs(decision, info, before_stats, after_stats, gained, reason, keep, measure, mid_stats):
    ts = ist_now()
    b = before_stats
    a = after_stats
    segs = [
        {"layer": "F.Cu", "width_mm": W, "start": list(s), "end": list(e)}
        for s, e in zip(POLY, POLY[1:])
    ]
    payload = {
        "pass": "30ap",
        "timestamp": ts,
        "decision": decision,
        "net": "VDD_GPIO",
        "via_added": False,
        "start_via_existing": [76.4375, 39.050],
        "segments": segs if decision == "KEEP" else [],
        "segment_count": len(segs) if decision == "KEEP" else 0,
        "attempted_segments": segs,
        "min_power_clearance_mm": measure.get("min_power_vin_mm"),
        "min_foreign_clearance_mm": measure.get("min_clearance_mm"),
        "measure": measure,
        "jog_around": ["ENABLE", "SIM_CLK", "P0.20"],
        "blockers_remeasured": info.get("blockers"),
        "pad_gap": info.get("pad_gap"),
        "before": b,
        "mid": mid_stats,
        "after": a,
        "vdd_gpio_opens": {
            "before": b.get("vdd_gpio_unconnected"),
            "after": a.get("vdd_gpio_unconnected"),
        },
        "unconnected": {
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
        "protect": info.get("protect"),
    }
    (REPORTS / "PASS30AP_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")

    def fmt_segs():
        if decision != "KEEP":
            return "_none placed_"
        lines = [
            "| layer | start | end | width |",
            "| --- | --- | --- | --- |",
        ]
        for s in segs:
            lines.append(
                f"| F.Cu | ({s['start'][0]:.4f}, {s['start'][1]:.3f}) | "
                f"({s['end'][0]:.3f}, {s['end'][1]:.3f}) | 0.18 mm |"
            )
        return "\n".join(lines)

    md = f"""# PASS30AP_SUMMARY — last VDD_GPIO open

**Timestamp:** {ts}
**KiCad:** 9.0.2
**Decision:** **{decision}**
**Net:** VDD_GPIO
**Via added:** no (starts on the existing via at (76.4375, 39.050))
**Segments:** {len(segs) if decision == 'KEEP' else 0} (limit 8)
**Min POWER/VIN clearance (pre-Add, copper edge):** {measure.get('min_power_vin_mm')} mm (need ≥ 0.20)
**Min foreign clearance (pre-Add):** {measure.get('min_clearance_mm')} mm vs {measure.get('min_clearance_item')}
**Unconnected:** {b.get('unconnected_items')} → {a.get('unconnected_items')}
**VDD_GPIO opens:** {b.get('vdd_gpio_unconnected')} → {a.get('vdd_gpio_unconnected')}
**GND zone islands:** {b.get('gnd_zone_islands')} → {a.get('gnd_zone_islands')} (waived)
**Short / clearance / crossing / hole_clearance:** {a.get('shorting_items')} / {a.get('clearance')} / {a.get('tracks_crossing')} / {a.get('hole_clearance')}
**hole_to_hole:** {b.get('hole_to_hole')} → {a.get('hole_to_hole')}

## Why this path

Straight F.Cu from pad U2.5 to pad J18.9 is not used. Remeasured blockers still sit on that line: ENABLE F.Cu (72.860, 40.950)–(72.860, 42.400) and (72.860, 42.400)–(74.200, 42.400) plus pad U2.3; SIM_CLK F.Cu (71.680, 44.000)–(70.900, 44.000) and (71.680, 44.000)–(71.680, 42.400); P0.20 F.Cu (55.780, 60.900)–(74.160, 60.900) then south at x=74.160. Pad-edge gap U2.5↔J18.9 is {info.get('pad_gap')}.

The jog leaves the existing F.Cu via just east of U2.5, steps south and west around the ENABLE via at (74.200, 42.400) and the SIM_CLK stub at x≈70.9–71.7, then runs southwest to x=54.438 (west of J18.8 / the P0.20 trunk), drops south of that trunk, and enters J18.9 from the southwest. No trunk was ripped. No locked copper was ripped. No new via. y=44.60 B.Cu pocket not used. Min x = 54.438 (east of RF keepout x=24.2).

## Segments

{fmt_segs()}

## Gate

{reason}

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | {b.get('unconnected_items')} | {b.get('shorting_items')} | {b.get('clearance')} | {b.get('tracks_crossing')} | {b.get('hole_clearance')} | {b.get('hole_to_hole')} | {b.get('gnd_zone_islands')} | {b.get('vdd_gpio_unconnected')} |
| after | {a.get('unconnected_items')} | {a.get('shorting_items')} | {a.get('clearance')} | {a.get('tracks_crossing')} | {a.get('hole_clearance')} | {a.get('hole_to_hole')} | {a.get('gnd_zone_islands')} | {a.get('vdd_gpio_unconnected')} |

## Protect

{json.dumps(info.get('protect'), indent=2)}

No header or U1 move. No Gerbers. No git commit.
"""
    (REPORTS / "PASS30AP_SUMMARY.md").write_text(md)
    return ts


def patch_review(ts, decision, before_stats, after_stats, measure):
    text = REVIEW.read_text()
    b, a = before_stats, after_stats
    pwr = measure.get("min_power_vin_mm")
    banner = (
        f"**Review date:** {ts} (Asia/Calcutta) — pass30ap VDD_GPIO last open "
        f"{decision} (8-seg F.Cu jog around ENABLE/SIM_CLK/P0.20, no new via, "
        f"POWER clearance {pwr} mm; unc {b.get('unconnected_items')}→{a.get('unconnected_items')}; "
        f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}; "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} waived). "
    )
    pre, sep, post = text.partition("**Review date:**")
    if not sep:
        raise SystemExit("review date line missing")
    old_body = post.split("\n", 1)[0]
    rest = post.split("\n", 1)[1]
    text = pre + banner + "Prior: " + old_body.strip() + "\n" + rest
    delta = (
        f"**Pass delta (pass30ap):** last VDD_GPIO open, **{decision}**. "
        f"Straight line not used (ENABLE, SIM_CLK, P0.20). "
        f"Eight 0.18 mm F.Cu segments from the existing via (76.4375, 39.050) "
        f"around those trunks, west of P0.20 at x=54.438, into J18.9. No new via. "
        f"Pre-Add POWER/VIN clearance {pwr} mm (need 0.20). "
        f"VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. "
        f"Headline unconnected {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"short/clearance/crossing/hole_clearance "
        f"{a.get('shorting_items')}/{a.get('clearance')}/{a.get('tracks_crossing')}/{a.get('hole_clearance')}. "
        f"hole_to_hole {b.get('hole_to_hole')}→{a.get('hole_to_hole')}. "
        f"GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). "
        f"Locked y=7.050 run, U1.12 polyline, COEX0, DEC0 bridge, P0.10/P0.12 not ripped. "
        f"No U1/header move. No y=44.60 pocket. x>24.2. No Gerbers. "
        f"Details: `reports/PASS30AP_SUMMARY.md`.\n\n"
    )
    needle = "**Pass delta (pass30an):**"
    if needle not in text:
        raise SystemExit("review doc anchor missing")
    if "**Pass delta (pass30ap):**" not in text:
        text = text.replace(needle, delta + needle, 1)
    text = text.replace(
        "| **unconnected_items** | **63** | `reports/DRC_PASS30AN_AFTER.json` (live `kicad-cli` 9.0.2). pass30an KEEP: VDD_GPIO opens 2→1. GND islands 11→12 (waived). D3.1 clearance 0.385 mm at y=7.050. Prior pass30am reverted",
        f"| **unconnected_items** | **{a.get('unconnected_items')}** | `reports/DRC_PASS30AP_AFTER.json` (live `kicad-cli` 9.0.2). pass30ap {decision}: VDD_GPIO opens {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. GND islands {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived). POWER clearance {pwr} mm. Prior pass30ao NO-ROUTE",
    )
    # shorting line may already point at AN; point it at AP if we still see the AN form
    text = text.replace(
        "| **shorting_items** | **0** | `reports/DRC_PASS30AN_AFTER.json` |",
        "| **shorting_items** | **0** | `reports/DRC_PASS30AP_AFTER.json` |",
    )
    section = (
        f"\n## Pass30ap — last VDD_GPIO open, jog around ENABLE / SIM_CLK / P0.20 — {ts}\n\n"
        f"**Decision:** **{decision}**. No new via. Width 0.18 mm. Segments "
        f"{8 if decision == 'KEEP' else 0}.\n\n"
        f"Straight F.Cu U2.5→J18.9 not used. Jog: existing via (76.4375, 39.050) south/west "
        f"around ENABLE and SIM_CLK, then to x=54.438 west of the P0.20 trunk, south, into J18.9.\n\n"
        f"**POWER clearance:** {pwr} mm (≥ 0.20). "
        f"**VDD_GPIO opens:** {b.get('vdd_gpio_unconnected')}→{a.get('vdd_gpio_unconnected')}. "
        f"**Unconnected:** {b.get('unconnected_items')}→{a.get('unconnected_items')}. "
        f"**GND islands:** {b.get('gnd_zone_islands')}→{a.get('gnd_zone_islands')} (waived).\n\n"
        f"**Artifacts:** `reports/PASS30AP_SUMMARY.{{md,json}}`, "
        f"`reports/DRC_PASS30AP_{{BEFORE,MID,AFTER}}.json`, `scripts/final_pass30ap.py`\n"
    )
    if "## Pass30ap —" not in text:
        text = text.rstrip() + "\n" + section
    REVIEW.write_text(text)


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if BACKUP.is_file():
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("pass30ap backup exists and does not match the live board; refusing to clobber")
    else:
        shutil.copy2(BOARD, BACKUP)
    if sha(BOARD) != sha(BACKUP):
        raise SystemExit("backup hash mismatch")

    board = pcbnew.LoadBoard(str(BOARD))
    info = {
        "blockers": blocker_snapshot(board),
        "pad_gap": pad_gap(board),
        "protect_before": protect_ok(board),
        "fp": footprint_xy(board),
    }
    print("BLOCKERS", json.dumps(info["blockers"]), flush=True)
    print("PADGAP", info["pad_gap"], flush=True)
    print("PROTECT", info["protect_before"], flush=True)

    shapes = foreign_shapes(board)
    measure = measure_poly(shapes)
    print("MEASURE", json.dumps({k: measure[k] for k in measure if k != "segments"}), flush=True)

    before = run_drc(REPORTS / "DRC_PASS30AP_BEFORE.json")
    print("BEFORE", before["stats"], flush=True)
    bst = before["stats"]

    def abort_no_copper(decision, reason):
        shutil.copy2(REPORTS / "DRC_PASS30AP_BEFORE.json", REPORTS / "DRC_PASS30AP_AFTER.json")
        info["protect"] = info["protect_before"]
        ts = write_outputs(decision, info, bst, bst, {}, reason, False, measure, None)
        patch_review(ts, decision, bst, bst, measure)
        print(decision, reason, flush=True)

    if not measure["meets_power_0_20"] or not measure["meets_drc_0_15"]:
        abort_no_copper(
            "NO-ROUTE",
            f"Pre-Add clearance failed (foreign {measure['min_clearance_mm']} mm, "
            f"POWER {measure['min_power_vin_mm']} mm). No copper added.",
        )
        return
    if not info["pad_gap"].get("end_on_j18_9"):
        abort_no_copper("NO-ROUTE", "Endpoint is not on pad J18.9. No copper added.")
        return
    if any(not info["blockers"]["tracks_found"][n] for n in ("ENABLE", "SIM_CLK", "P0.20")):
        abort_no_copper(
            "NO-ROUTE",
            f"Blocker remeasure missed a trunk: {info['blockers']['tracks_found']}. No copper added.",
        )
        return
    pb = info["protect_before"]
    if not all(pb[k] for k in ("y7050", "u1_12_poly", "dec0_bridge", "coex0_via", "coex0_runs", "p010", "p012")) or pb["p015"] != 42:
        abort_no_copper("NO-ROUTE", f"Locked copper not in the expected state before edit: {pb}. No copper added.")
        return

    pts, _made = add_route(board)
    print("ADDED", pts, flush=True)
    pa = protect_ok(board)
    fp_after = footprint_xy(board)
    moved = sorted(ref for ref in info["fp"] if info["fp"][ref] != fp_after.get(ref))
    info["protect"] = {"before": pb, "after_add": pa, "moved": moved}
    if pa != pb or moved:
        shutil.copy2(BACKUP, BOARD)
        after = run_drc(REPORTS / "DRC_PASS30AP_AFTER.json")
        shutil.copy2(REPORTS / "DRC_PASS30AP_BEFORE.json", REPORTS / "DRC_PASS30AP_MID.json")
        write_outputs(
            "REVERT",
            info,
            bst,
            after["stats"],
            {},
            f"Protect guard failed after add {pa} moved={moved}. Full restore.",
            False,
            measure,
            None,
        )
        patch_review(ist_now(), "REVERT", bst, after["stats"], measure)
        print("REVERT guard", pa, moved, flush=True)
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AP_MID.json")
    print("MID", mid["stats"], flush=True)
    gained = {}
    bc = nongnd_counts(before["data"])
    ac = nongnd_counts(mid["data"])
    for n in set(ac) | set(bc):
        if ac[n] > bc[n]:
            gained[n] = {"before": bc[n], "after": ac[n]}
    st = mid["stats"]
    # VDD_GPIO itself must not be in gained (opens must fall, not rise)
    gained.pop("VDD_GPIO", None)
    electrical = (
        bst["vdd_gpio_unconnected"] == 1
        and st["vdd_gpio_unconnected"] == 0
        and not gained
        and st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
        and st["hole_to_hole"] <= bst["hole_to_hole"]
        and measure["min_power_vin_mm"] >= CLEAR_MIN - 1e-9
    )
    if electrical:
        shutil.copy2(REPORTS / "DRC_PASS30AP_MID.json", REPORTS / "DRC_PASS30AP_AFTER.json")
        reason = (
            f"KEEP. VDD_GPIO opens 1→0. No other non-GND net gained an open. "
            f"short/clearance/crossing/hole_clearance 0. hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}. "
            f"POWER clearance {measure['min_power_vin_mm']} mm. "
            f"GND islands {bst['gnd_zone_islands']}→{st['gnd_zone_islands']} (waived)."
        )
        ts = write_outputs("KEEP", info, bst, st, gained, reason, True, measure, st)
        patch_review(ts, "KEEP", bst, st, measure)
        print("KEEP", st, flush=True)
        return

    shutil.copy2(BACKUP, BOARD)
    after = run_drc(REPORTS / "DRC_PASS30AP_AFTER.json")
    reason = (
        f"REVERT. VDD_GPIO {bst['vdd_gpio_unconnected']}→{st['vdd_gpio_unconnected']}, "
        f"gained={gained}, short/clear/cross/hole "
        f"{st['shorting_items']}/{st['clearance']}/{st['tracks_crossing']}/{st['hole_clearance']}, "
        f"hole_to_hole {bst['hole_to_hole']}→{st['hole_to_hole']}. "
        f"POWER clearance {measure['min_power_vin_mm']} mm. Full restore. No second path."
    )
    ts = write_outputs("REVERT", info, bst, after["stats"], gained, reason, False, measure, st)
    patch_review(ts, "REVERT", bst, after["stats"], measure)
    print("REVERT", reason, flush=True)


if __name__ == "__main__":
    main()
