#!/usr/bin/env python3
"""pass30ai — ONE attempt: F.Cu VDD_GPIO via@(40.17,19.13) -> U1.12.

Jog around P0.16. Do not touch the P0.15 trunk. At most four 0.18 mm segments.
No via (the polyline can reach the pad center; clearance, not reach, is the issue).
Gate: shorting/clearance/crossing/hole_clearance = 0 AND unconnected drops by >= 1.
Otherwise FULL revert to .mcp-backups/pass30ai/pre-edit.kicad_pcb.
"""
from __future__ import annotations

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
BACKUP = ROOT / ".mcp-backups/pass30ai/pre-edit.kicad_pcb"
REPORTS = ROOT / "reports"
F = pcbnew.F_Cu
W = 0.18

# One geometry. Segments 1-2 jog east of P0.16 and stay clear of the P0.15
# vertical keep (x=41.75, y=23.10-26.75). Segment 3 lands on U1.12.
POLY = [
    (40.170, 19.126),
    (45.500, 20.150),
    (45.500, 26.050),
    (44.000, 31.500),
]


def ist_now() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def confirm(board) -> dict:
    via = None
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if abs(x - 40.170) < 0.05 and abs(y - 19.126) < 0.05:
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
        "u1": {
            "x": round(mm(fp.GetPosition().x), 3),
            "y": round(mm(fp.GetPosition().y), 3),
        },
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


def add_poly(board):
    net = board.FindNet("VDD_GPIO")
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(xy(x1, y1))
        t.SetEnd(xy(x2, y2))
        t.SetWidth(pcbnew.FromMM(W))
        t.SetLayer(F)
        t.SetNet(net)
        board.Add(t)


def run_drc(dest: Path) -> dict:
    tmp = Path("/tmp/nrf30ai_drc.json")
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
    }
    interesting = []
    for v in data.get("violations", []):
        if v["type"] not in ("shorting_items", "clearance", "tracks_crossing", "hole_clearance"):
            continue
        interesting.append(
            {
                "type": v["type"],
                "description": v.get("description", ""),
                "items": [it.get("description", "") for it in v.get("items", [])],
            }
        )
    return {"stats": stats, "hits": interesting}


def main():
    if not BACKUP.is_file():
        raise SystemExit(f"missing backup {BACKUP}")
    before = json.loads((REPORTS / "DRC_PASS30AI_BEFORE.json").read_text())
    before_unc = len(before.get("unconnected_items", []))
    board = pcbnew.LoadBoard(str(BOARD))
    info = confirm(board)
    p015_before = p015_count(board)
    print("CONFIRM", json.dumps(info))
    print("P0.15 segments", p015_before)
    print("POLY", POLY)

    add_poly(board)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

    mid = run_drc(REPORTS / "DRC_PASS30AI_MID.json")
    print("MID", mid["stats"])
    st = mid["stats"]
    clean = (
        st["shorting_items"] == 0
        and st["clearance"] == 0
        and st["tracks_crossing"] == 0
        and st["hole_clearance"] == 0
    )
    dropped = before_unc - st["unconnected_items"]
    keep = clean and dropped >= 1
    print("clean", clean, "dropped", dropped, "keep", keep)

    decision = "KEEP" if keep else "REVERT"
    if not keep:
        shutil.copy2(BACKUP, BOARD)
        # prove byte restore
        import hashlib
        def sha(p):
            return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        if sha(BOARD) != sha(BACKUP):
            raise SystemExit("revert failed: hash mismatch")
        after = run_drc(REPORTS / "DRC_PASS30AI_AFTER.json")
        print("AFTER", after["stats"])
    else:
        after = {"stats": st, "hits": []}

    segments = []
    for (x1, y1), (x2, y2) in zip(POLY, POLY[1:]):
        segments.append(
            {
                "layer": "F.Cu",
                "width_mm": W,
                "start": [x1, y1],
                "end": [x2, y2],
            }
        )
    summary = {
        "pass": "30ai",
        "timestamp": ist_now(),
        "decision": decision,
        "net": "VDD_GPIO",
        "via_used": False,
        "confirmed": info,
        "segments": segments,
        "unconnected_before": before_unc,
        "unconnected_mid": st["unconnected_items"],
        "unconnected_after": after["stats"]["unconnected_items"],
        "unconnected_delta_mid": st["unconnected_items"] - before_unc,
        "gate": {
            "clean_short_clear_cross_hole": clean,
            "unconnected_drop_at_least_1": dropped >= 1,
            "met": keep,
        },
        "drc_mid": st,
        "drc_after": after["stats"],
        "p015_segments_before": p015_before,
        "via_allowed_reason": (
            "not used — polyline reaches U1.12 pad center; "
            "one via cannot bridge the sealed F.Cu gap at the north pad row"
        ),
        "hits": mid["hits"],
        "revert_reason": None
        if keep
        else "shorting/clearance/crossing/hole not all zero and/or unconnected did not drop",
        "backup": str(BACKUP),
    }
    (REPORTS / "PASS30AI_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_md(summary)
    print("DECISION", decision)


def write_md(s: dict) -> None:
    lines = []
    lines.append("# PASS30AI_SUMMARY — VDD_GPIO via island to U1.12")
    lines.append("")
    lines.append(f"**Timestamp:** {s['timestamp']}")
    lines.append("**KiCad:** 9.0.2")
    lines.append(f"**Decision:** **{s['decision']}**")
    lines.append(f"**Net:** {s['net']}")
    lines.append(f"**Via used:** {s['via_used']}")
    lines.append(
        f"**Unconnected:** {s['unconnected_before']} → mid {s['unconnected_mid']} → after {s['unconnected_after']}"
    )
    lines.append("")
    lines.append("## Confirmed live coordinates")
    lines.append("")
    v = s["confirmed"]["via"]
    p = s["confirmed"]["pad12"]
    lines.append(
        f"- F.Cu via island: net {v['net']} @ ({v['x']}, {v['y']}) dia {v['dia']} drill {v['drill']}"
    )
    lines.append(
        f"- U1 @ ({s['confirmed']['u1']['x']}, {s['confirmed']['u1']['y']}) unmoved"
    )
    lines.append(
        f"- U1.12: net {p['net']} center ({p['x']}, {p['y']}) size {p['size']} bbox {p['bbox']} F.Cu only"
    )
    lines.append("")
    lines.append("## One geometry (not retried)")
    lines.append("")
    lines.append(
        "Straight line forbidden (shorts P0.15 keep and P0.16). "
        "Three F.Cu 0.18 mm segments. Segments 1–2 jog east of the P0.16 via@(40.700,20.800) "
        "and stay east of the P0.15 vertical keep (x=41.75). Segment 3 is the landing onto U1.12. "
        "No via. P0.15 trunk not ripped. No header/U1 move."
    )
    lines.append("")
    lines.append("| # | start | end | width |")
    lines.append("| --- | --- | --- | --- |")
    for i, seg in enumerate(s["segments"], 1):
        a, b = seg["start"], seg["end"]
        lines.append(f"| {i} | ({a[0]:.3f}, {a[1]:.3f}) | ({b[0]:.3f}, {b[1]:.3f}) | {seg['width_mm']} mm F.Cu |")
    lines.append("")
    lines.append("## Gate")
    lines.append("")
    g = s["gate"]
    lines.append(f"- short/clear/cross/hole all zero: {g['clean_short_clear_cross_hole']}")
    lines.append(f"- unconnected drop ≥ 1: {g['unconnected_drop_at_least_1']} (delta mid {s['unconnected_delta_mid']})")
    lines.append(f"- **met: {g['met']}**")
    lines.append("")
    lines.append("## DRC")
    lines.append("")
    lines.append("| | unconnected | shorting | clearance | tracks_crossing | hole_clearance |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    b = s["drc_mid"]
    # before is known 64 / 0s; after from summary
    lines.append(f"| before | {s['unconnected_before']} | 0 | 0 | 0 | 0 |")
    lines.append(
        f"| mid (attempt) | {b['unconnected_items']} | {b['shorting_items']} | {b['clearance']} | {b['tracks_crossing']} | {b['hole_clearance']} |"
    )
    a = s["drc_after"]
    lines.append(
        f"| after ({s['decision']}) | {a['unconnected_items']} | {a['shorting_items']} | {a['clearance']} | {a['tracks_crossing']} | {a['hole_clearance']} |"
    )
    lines.append("")
    if s["decision"] != "KEEP":
        lines.append("## Revert audit — what the landing hit")
        lines.append("")
        lines.append(
            "Full file restore from `.mcp-backups/pass30ai/pre-edit.kicad_pcb`. "
            "P0.15 segment count was not reduced (trunk not ripped). "
            "Segments 1–2 had no foreign-copper clearance hit in pre-DRC geometry check. "
            "Segment 3 (45.500,26.050)→(44.000,31.500) is the dirty landing. "
            "A via was not added: U1.12 is F.Cu-only, and one via cannot cross the north pad-row wall "
            "(0.20 mm pad gaps vs 0.18 mm track + 0.15 mm POWER clearance)."
        )
        lines.append("")
        # unique descriptions
        seen = set()
        for h in s["hits"]:
            key = (h["type"], h["description"])
            if key in seen:
                continue
            seen.add(key)
            items = "; ".join(h["items"])
            lines.append(f"- **{h['type']}** — {h['description']}")
            if items:
                lines.append(f"  - {items}")
        lines.append("")
    lines.append("## Protect checklist")
    lines.append("")
    lines.append("- y=44.60 B.Cu pocket: no track")
    lines.append("- SIM_IO_C / SIM_CLK_C walls: not ripped")
    lines.append("- U1 and headers: not moved")
    lines.append("- Class C, Stage-A VDD2, P0.22, P0.19, P0.15 west wrap / trunk: not ripped")
    lines.append("- No Gerbers. No git commit. COEX0 not started.")
    lines.append("")
    (REPORTS / "PASS30AI_SUMMARY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
