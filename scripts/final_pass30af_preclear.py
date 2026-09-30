#!/usr/bin/env python3
"""Pass30af — safest non-protected preclear after pass30ae full revert.

Attempt 1 (keep if clean): SIM_RST_C only
  - delete two dangling duplicate B tracks (79.38,44.60)-(97.30,44.60)
  - jog live B trunk (81.80,44.60)-(97.30,44.60) to y=45.00
  - extend x=81.80 riser end 44.60 → 45.00
  Frees B.Cu y≈44.60, x≈81.8–97.3 for one future signal.
  Does NOT rip P0.22 keep, Stage A, P0.15 west, Class C, RF/U3.

Attempt 2 only if attempt 1 dirty: delete redundant SIM_CD F
  (100.27,52.04)-(96.55,52.04) covered by the longer y=52.04 track.
Stop after one clean keep or two dirty fails.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30af-preclear"
REPORTS = f"{ROOT}/reports"
PRE = f"{SNAP}/pre-edit.kicad_pcb"
B = pcbnew.B_Cu
F = pcbnew.F_Cu
BASELINE_UNCONNECTED = 64

FROZEN = {
    "J13": (64.0, 76.0),
    "J10": (116.0, 28.0),
    "J11": (116.0, 46.0),
    "J16": (108.0, 8.0),
    "J9": (116.0, 8.0),
    "J17": (108.0, 26.0),
    "J12": (6.0, 76.0),
    "U1": (36.0, 32.0),
    "J14": (104.0, 48.0),
    "J15": (104.0, 62.0),
}
CLASS_C_XY = {"C22": (17.5, 31.75), "C23": (24.8, 34.0), "C24": (15.0, 31.8)}
CLASS_C_GND_VIA = {"C22": (17.5, 32.23), "C23": (25.98, 34.0), "C24": (16.18, 31.8)}
P022_VIAS = [(112.5, 32.5), (114.7, 29.9), (112.5, 29.9), (109.2, 32.5)]
WATCH = [
    "SIM_RST_C", "SIM_CD", "SIM_CLK_C", "SIM_RST", "SIM_CLK", "SIM_IO", "SIM_1V8",
    "P0.22", "P0.04", "P0.06", "P0.01", "P0.15", "P0.19", "VDD2", "VDD_nRF",
]


def mm(v):
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def near(a, b, tol=0.08):
    return abs(a - b) < tol


def load(path=BOARD):
    return pcbnew.LoadBoard(path)


def save(board, path=BOARD):
    pcbnew.SaveBoard(path, board)


def fp_xy(board, ref):
    fp = board.FindFootprintByReference(ref)
    return (round(mm(fp.GetPosition().x), 3), round(mm(fp.GetPosition().y), 3))


def run_drc(out_path):
    tmp = "/tmp/nrf30af_drc.json"
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", tmp, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, out_path)
    data = json.load(open(out_path))
    vc = Counter(v["type"] for v in data.get("violations", []))
    stats = {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "track_dangling": vc.get("track_dangling", 0),
    }
    return data, stats


def nets_of(data):
    c = Counter()
    for u in data.get("unconnected_items", []):
        ns = set()
        for it in u.get("items", []):
            for m in re.findall(r"\[([^\]]+)\]", it.get("description", "")):
                if m not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                    ns.add(m)
        for n in ns:
            c[n] += 1
    return dict(c)


def clean(s):
    return s["shorting_items"] == 0 and s["clearance"] == 0 and s["tracks_crossing"] == 0


def colliding(data, limit=16):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in ("shorting_items", "clearance", "tracks_crossing", "hole_clearance"):
            out.append(
                {
                    "type": v["type"],
                    "description": v.get("description", "")[:200],
                    "items": [
                        {"description": it.get("description", "")[:140], "pos": it.get("pos")}
                        for it in v.get("items", [])[:3]
                    ],
                }
            )
        if len(out) >= limit:
            break
    return out


def zone_fill():
    path = f"{SNAP}/zone_fill_once.py"
    open(path, "w").write(
        "import pcbnew\n"
        f"b=pcbnew.LoadBoard({BOARD!r})\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        f"pcbnew.SaveBoard({BOARD!r}, b)\n"
        "print('zone-fill saved', flush=True)\n"
    )
    subprocess.check_call([sys.executable, path])


def p015_west(board):
    n = 0
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            continue
        if min(mm(t.GetStart().x), mm(t.GetEnd().x)) < 45:
            n += 1
    return n


def stage_a_ok(board):
    ok = {"VDD_nRF_via_north": False, "VDD2_vias": 0}
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if t.GetNetname() == "VDD_nRF" and abs(x - 69.3) < 0.2 and abs(y - 31.5) < 0.2:
            ok["VDD_nRF_via_north"] = True
        if t.GetNetname() == "VDD2" and abs(x - 58) < 0.2 and (
            abs(y - 29.55) < 0.2 or abs(y - 30.95) < 0.2
        ):
            ok["VDD2_vias"] += 1
    ok["VDD2_present"] = ok["VDD2_vias"] >= 2
    return ok


def p022_vias_ok(board):
    found = []
    for vx, vy in P022_VIAS:
        hit = False
        for t in board.GetTracks():
            if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != "P0.22":
                continue
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if abs(x - vx) < 0.15 and abs(y - vy) < 0.15:
                hit = True
                break
        found.append(hit)
    return all(found), found


def class_c_ok(board):
    reasons = []
    for ref, (ex, ey) in CLASS_C_XY.items():
        live = fp_xy(board, ref)
        if abs(live[0] - ex) > 0.05 or abs(live[1] - ey) > 0.05:
            reasons.append(f"{ref} moved {live}")
    for ref, (vx, vy) in CLASS_C_GND_VIA.items():
        hit = False
        for t in board.GetTracks():
            if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != "GND":
                continue
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if abs(x - vx) < 0.15 and abs(y - vy) < 0.15:
                hit = True
                break
        if not hit:
            reasons.append(f"missing GND via {ref}")
    return reasons


def protect_ok(board, west0):
    reasons = []
    stage = stage_a_ok(board)
    west = p015_west(board)
    if not stage["VDD_nRF_via_north"] or not stage["VDD2_present"]:
        reasons.append(f"stage_a={stage}")
    if west < west0:
        reasons.append(f"p015_west {west}<{west0}")
    p022_ok, p022_found = p022_vias_ok(board)
    if not p022_ok:
        reasons.append(f"p022_vias {p022_found}")
    reasons.extend(class_c_ok(board))
    for ref, exp in FROZEN.items():
        live = fp_xy(board, ref)
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            reasons.append(f"{ref} moved {live}")
    for ref, exp in (("L1", (22.0, 32.0)), ("L2", (20.0, 33.0)), ("U3", (26.5, 47.0))):
        live = fp_xy(board, ref)
        if abs(live[0] - exp[0]) > 0.05 or abs(live[1] - exp[1]) > 0.05:
            reasons.append(f"{ref} moved {live}")
    return {
        "ok": len(reasons) == 0,
        "reasons": reasons,
        "stage_a": stage,
        "p015_west": west,
        "p022_vias": p022_found,
    }


def seg_matches(t, net, layer, x1, y1, x2, y2, tol=0.08):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net or t.GetLayer() != layer:
        return False
    sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
    ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
    a = near(sx, x1, tol) and near(sy, y1, tol) and near(ex, x2, tol) and near(ey, y2, tol)
    b = near(sx, x2, tol) and near(sy, y2, tol) and near(ex, x1, tol) and near(ey, y1, tol)
    return a or b


def restore_pre():
    shutil.copy2(PRE, BOARD)


def attempt_sim_rst_c(board):
    """Delete dangling duplicates and jog the live trunk north 0.40 mm."""
    deleted = 0
    jogged = 0
    extended = 0
    for t in list(board.GetTracks()):
        if seg_matches(t, "SIM_RST_C", B, 79.38, 44.60, 97.30, 44.60):
            board.Delete(t)
            deleted += 1
    for t in list(board.GetTracks()):
        if seg_matches(t, "SIM_RST_C", B, 81.80, 44.60, 97.30, 44.60):
            sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
            ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
            t.SetStart(xy(sx, 45.00))
            t.SetEnd(xy(ex, 45.00))
            jogged += 1
        elif seg_matches(t, "SIM_RST_C", B, 81.80, 56.05, 81.80, 44.60):
            sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
            ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
            # move whichever end sits on y=44.60
            if near(sy, 44.60):
                t.SetStart(xy(sx, 45.00))
            if near(ey, 44.60):
                t.SetEnd(xy(ex, 45.00))
            extended += 1
    # Trim the duplicate via-risers so the old y=44.60 tail does not dangle
    # into the freed corridor. Both copies span (97.30,44.60)-(97.30,45.54).
    trimmed = 0
    for t in list(board.GetTracks()):
        if seg_matches(t, "SIM_RST_C", B, 97.30, 44.60, 97.30, 45.54):
            sx, sy = mm(t.GetStart().x), mm(t.GetStart().y)
            ex, ey = mm(t.GetEnd().x), mm(t.GetEnd().y)
            if near(sy, 44.60):
                t.SetStart(xy(sx, 45.00))
            if near(ey, 44.60):
                t.SetEnd(xy(ex, 45.00))
            trimmed += 1
    if deleted != 2 or jogged != 1 or extended != 1 or trimmed != 2:
        raise RuntimeError(
            f"SIM_RST_C geometry mismatch deleted={deleted} jogged={jogged} "
            f"extended={extended} trimmed={trimmed}"
        )
    return {"deleted_dangling": deleted, "jogged_trunk": jogged, "extended_riser": extended,
            "trimmed_via_risers": trimmed, "new_trunk_y": 45.00}


def attempt_sim_cd(board):
    deleted = 0
    for t in list(board.GetTracks()):
        if seg_matches(t, "SIM_CD", F, 100.27, 52.04, 96.55, 52.04):
            board.Delete(t)
            deleted += 1
    if deleted != 1:
        raise RuntimeError(f"SIM_CD duplicate count {deleted} != 1")
    # longer track must remain
    remain = 0
    for t in board.GetTracks():
        if seg_matches(t, "SIM_CD", F, 100.27, 52.04, 90.00, 52.04, tol=0.12):
            remain += 1
    if remain < 1:
        raise RuntimeError("SIM_CD long track missing after delete")
    return {"deleted_duplicate": deleted, "long_track_remains": remain}


def accept(stats, prot):
    if not clean(stats):
        return False, "dirty_drc"
    if stats["unconnected_items"] > BASELINE_UNCONNECTED:
        return False, f"unconnected_spike_{stats['unconnected_items']}"
    if not prot["ok"]:
        return False, "protect_fail:" + ",".join(prot["reasons"][:6])
    return True, "ok"


def main():
    os.makedirs(SNAP, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    assert os.path.isfile(PRE)

    summary = {
        "pass": "layout-pass30af-preclear",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "kicad": pcbnew.GetBuildVersion(),
        "python": sys.executable,
        "scope": "Safest SIM preclear only. No P0.22 rip. No header moves.",
        "backup": PRE,
        "phase": "INIT",
    }
    restore_pre()
    board = load()
    west0 = p015_west(board)
    summary["protect_before"] = protect_ok(board, west0)
    if not summary["protect_before"]["ok"]:
        summary["phase"] = "ABORT_PROTECT"
        json.dump(summary, open(f"{REPORTS}/PASS30AF_SUMMARY.json", "w"), indent=2)
        print("ABORT", summary["protect_before"])
        return

    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30AF_BEFORE.json")
    summary["before"] = before
    summary["before_nets_watch"] = {n: nets_of(before_data).get(n, 0) for n in WATCH}
    print("BEFORE", before, flush=True)

    attempts = []
    kept = None

    # Attempt 1
    restore_pre()
    board = load()
    info = {"label": "SIM_RST_C_dangling_rip_and_y45_jog", "net": "SIM_RST_C"}
    try:
        info["edit"] = attempt_sim_rst_c(board)
        save(board)
        zone_fill()
        data, stats = run_drc(f"{REPORTS}/DRC_PASS30AF_MID_SIM_RST_C.json")
        info["mid"] = stats
        info["mid_nets_watch"] = {n: nets_of(data).get(n, 0) for n in WATCH}
        info["collide"] = colliding(data)
        info["clean"] = clean(stats)
        info["protect"] = protect_ok(load(), west0)
        ok, reason = accept(stats, info["protect"])
        info["accept"] = ok
        info["reason"] = reason
    except Exception as e:
        info["accept"] = False
        info["reason"] = f"exception:{e}"
        info["clean"] = False
        restore_pre()
    attempts.append(info)
    print("MID1", info.get("mid"), info.get("reason"), flush=True)
    if info.get("accept"):
        kept = info
        shutil.copy2(BOARD, f"{SNAP}/after-sim-rst-c.kicad_pcb")
    else:
        restore_pre()
        info2 = {"label": "SIM_CD_redundant_F_segment", "net": "SIM_CD"}
        try:
            board = load()
            info2["edit"] = attempt_sim_cd(board)
            save(board)
            zone_fill()
            data, stats = run_drc(f"{REPORTS}/DRC_PASS30AF_MID_SIM_CD.json")
            info2["mid"] = stats
            info2["mid_nets_watch"] = {n: nets_of(data).get(n, 0) for n in WATCH}
            info2["collide"] = colliding(data)
            info2["clean"] = clean(stats)
            info2["protect"] = protect_ok(load(), west0)
            ok, reason = accept(stats, info2["protect"])
            info2["accept"] = ok
            info2["reason"] = reason
        except Exception as e:
            info2["accept"] = False
            info2["reason"] = f"exception:{e}"
            info2["clean"] = False
            restore_pre()
        attempts.append(info2)
        print("MID2", info2.get("mid"), info2.get("reason"), flush=True)
        if info2.get("accept"):
            kept = info2
            shutil.copy2(BOARD, f"{SNAP}/after-sim-cd.kicad_pcb")
        else:
            restore_pre()

    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30AF_AFTER.json")
    board = load()
    summary["attempts"] = []
    for a in attempts:
        row = {k: v for k, v in a.items() if k != "collide"}
        row["collide"] = a.get("collide", [])[:8]
        summary["attempts"].append(row)
    summary["after"] = after
    summary["after_nets_watch"] = {n: nets_of(after_data).get(n, 0) for n in WATCH}
    summary["unconnected_delta"] = after["unconnected_items"] - before["unconnected_items"]
    summary["protect_after"] = protect_ok(board, west0)
    summary["kept"] = None if not kept else {"net": kept["net"], "label": kept["label"], "edit": kept.get("edit")}
    summary["reverted"] = kept is None
    if kept:
        summary["phase"] = "COMPLETE_KEEP"
        summary["decision"] = "KEEP"
        summary["corridor"] = (
            "B.Cu y≈44.60 x≈81.8–97.3 freed for one 0.18 mm signal "
            "(SIM_RST_C trunk now y=45.00; dangling duplicates removed)"
            if kept["net"] == "SIM_RST_C"
            else "SIM_CD duplicate removed only; y=52.04 centerline still occupied by the long track. No new corridor."
        )
    else:
        summary["phase"] = "COMPLETE_REVERTED"
        summary["decision"] = "REVERT"
        summary["corridor"] = "none — both attempts reverted"
        summary["stop_reason"] = "two dirty/reject fails; board restored"

    json.dump(summary, open(f"{REPORTS}/PASS30AF_SUMMARY.json", "w"), indent=2)

    lines = [
        "# PASS30AF_SUMMARY — SIM preclear",
        "",
        f"**Timestamp:** {summary['timestamp_ist']}",
        f"**KiCad:** {summary['kicad']}",
        f"**Decision:** **{summary['decision']}**",
        f"**Net:** {summary['kept']['net'] if summary['kept'] else 'none'}",
        f"**Unconnected:** {before['unconnected_items']} → {after['unconnected_items']} (delta {summary['unconnected_delta']})",
        f"**Short/clearance/crossing after:** {after['shorting_items']}/{after['clearance']}/{after['tracks_crossing']}",
        f"**Corridor:** {summary['corridor']}",
        "",
        "## Attempts",
        "",
    ]
    for a in summary["attempts"]:
        lines.append(f"### {a['label']}")
        lines.append(f"- net: {a['net']}")
        lines.append(f"- edit: {a.get('edit')}")
        lines.append(f"- mid: {a.get('mid')}")
        lines.append(f"- accept: {a.get('accept')} reason: {a.get('reason')}")
        if a.get("collide"):
            lines.append(f"- collide: {json.dumps(a['collide'][:3])[:700]}")
        lines.append("")
    lines.append("P0.22 keep not ripped. No header moves. No Gerbers.")
    if summary.get("stop_reason"):
        lines.append("")
        lines.append(f"**Stop:** {summary['stop_reason']}")
    open(f"{REPORTS}/PASS30AF_SUMMARY.md", "w").write("\n".join(lines) + "\n")
    print("DONE", summary["decision"], summary.get("kept"), flush=True)
    print("AFTER", after, "delta", summary["unconnected_delta"], flush=True)


if __name__ == "__main__":
    main()
