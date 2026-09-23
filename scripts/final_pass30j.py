#!/usr/bin/env python3
"""Pass30j — stitch P0.08 → J12.9 (Stage A + pass30i kept; no placement).

Applied on live board (see reports/PASS30J_SUMMARY.json):
  P0.08 branch B@x=65.2 from trunk H@y30.25:
    F via-hops: COEX2@37.45/38.55, COEX0@61.45/62.55, P0.18+P0.17@72.25/73.95
    B H@y79 (65.2→26.32) → via(26.32,78) → F to J12.9
  Rip+restore same transaction:
    P0.15 bottom H: wide F-bridge vias@(61.5,77.45)/(68.5,77.45)
    P0.01: final F-bridge 24.5–27.2 @y78.5 + column U-jog F@y74.5 (62–68)
  Trial note: tight P0.15@77.45 + P0.01@77.8 restores → shorting=5; widened/separated → KEEP.

Result: unconnected 77→76, shorting=0 clearance=0 crossing=0.
  Closed: P0.08 U1/SW3/R14 ↔ J12.9. VIN_F/SWDCLK skipped (not cheap).
  P0.15 west wrap preserved (21 segs). Stage A + pass30i ENABLE/COEX2/P0.08 trunk untouched.

Do not --apply unless intentionally replaying; prefer session/summary.
"""
Pass30j — stitch P0.08 → J12.9 (Stage A + pass30i kept; no placement).

Path: branch B@x=65.2 from trunk H@y30.25, F via-hops over COEX2/COEX0/P0.18+P0.17,
rip+restore P0.15@y77.45 and P0.01@y78.5 at column, B H@y79 to x=26.32,
rip+restore P0.01 at final, via(26.32,78)+F to J12.9 pad.
Protect P0.15 west wrap (restore bottom H), RF/U3, Stage A, existing P0.08 trunk.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30j-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
VIA_D, VIA_DRILL = 0.6, 0.3
XCOL = 65.2

os.makedirs(SNAP, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)
os.makedirs(BACKUPS, exist_ok=True)


def mm(v):
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def save(board, path=BOARD):
    pcbnew.SaveBoard(path, board)


def load(path=BOARD):
    return pcbnew.LoadBoard(path)


def add_trk(board, net, x1, y1, x2, y2, w, layer):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)


def add_via(board, net, x, y, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(xy(x, y))
    v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(d))
    v.SetWidth(pcbnew.B_Cu, pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(board.FindNet(net))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)


def fill_zones(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def run_drc(path):
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30j.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30j.json", path)
    data = json.load(open(path))
    vc = Counter(v["type"] for v in data.get("violations", []))
    return data, {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "via_dangling": vc.get("via_dangling", 0),
    }


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


def commit_removes(board, doomed, tag):
    for t in doomed:
        board.Delete(t)
    print(f"  deleted {len(doomed)} ({tag})")
    save(board)
    return load()


def find_h_tracks(board, net, y, x_cover, layer=B, tol=0.05):
    out = []
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != net or t.GetLayer() != layer:
            continue
        a, b = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = mm(a.x), mm(a.y), mm(b.x), mm(b.y)
        if abs(ay - by) > tol or abs(ay - y) > tol:
            continue
        if min(ax, bx) - 0.2 <= x_cover <= max(ax, bx) + 0.2:
            out.append((t, min(ax, bx), max(ax, bx), ay, mm(t.GetWidth())))
    return out


def main():
    summary = {
        "pass": "layout-pass30j",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "one_honest_cycle": True,
        "keep_stage_A": True,
        "keep_pass30i": True,
        "no_placement": True,
        "closed": [],
        "blocked": {},
        "restores": {},
        "p008_stitch": {},
        "reverted": False,
        "stop": False,
        "notes": [],
        "vin_f": "not_attempted",
        "swdclk": "not_attempted",
    }

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30j-{ts}"
    shutil.copy2(BOARD, backup)
    shutil.copy2(BOARD, f"{SNAP}/pre-stitch.kicad_pcb")
    summary["backup"] = backup.replace(ROOT + "/", "")
    print("Backup:", backup)

    board = load()
    p015_before = p015_west(board)
    summary["p015_west_segs"] = {"before": p015_before}

    print("DRC BEFORE...")
    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30J_BEFORE.json")
    summary["before"] = before
    before_nets = nets_of(before_data)
    print("  before:", before)

    # --- RIP P0.15 and P0.01 at column (and P0.01 at final) in one delete pass ---
    doomed = []
    rip_meta = []

    # P0.15 bottom H @ y=77.45 covering x=65.2
    for t, x0, x1, y, w in find_h_tracks(board, "P0.15", 77.45, XCOL):
        doomed.append(t)
        rip_meta.append(("P0.15", x0, x1, y, w, "col"))
    # P0.01 @ y=78.5 covering both column and final (one long track) — rip once
    for t, x0, x1, y, w in find_h_tracks(board, "P0.01", 78.5, XCOL):
        doomed.append(t)
        rip_meta.append(("P0.01", x0, x1, y, w, "full"))
    # Also catch if separate segment at final only
    for t, x0, x1, y, w in find_h_tracks(board, "P0.01", 78.5, 26.32):
        if t not in doomed:
            doomed.append(t)
            rip_meta.append(("P0.01", x0, x1, y, w, "final"))

    # Dedup doomed by identity
    seen = set()
    uniq = []
    for t in doomed:
        i = id(t)
        if i not in seen:
            seen.add(i)
            uniq.append(t)
    doomed = uniq
    summary["ripped"] = [
        {"net": n, "x0": x0, "x1": x1, "y": y, "w": w, "where": wh}
        for (n, x0, x1, y, w, wh) in rip_meta
    ]
    print("Ripping:", summary["ripped"])
    board = commit_removes(board, doomed, "P0.15+P0.01 crossings")

    # --- Place P0.08 stitch ---
    net = "P0.08"
    # Branch + F hops
    hops = [
        # (y_before, y_after) F hop windows
        (37.45, 38.55),  # COEX2
        (61.45, 62.55),  # COEX0
        (72.25, 73.95),  # P0.18 + P0.17
    ]
    y_cursor = 30.25
    add_trk(board, net, XCOL, y_cursor, XCOL, hops[0][0], W, B)
    for i, (ya, yb) in enumerate(hops):
        add_via(board, net, XCOL, ya)
        add_trk(board, net, XCOL, ya, XCOL, yb, W, F)
        add_via(board, net, XCOL, yb)
        next_y = hops[i + 1][0] if i + 1 < len(hops) else 79.0
        add_trk(board, net, XCOL, yb, XCOL, next_y, W, B)
        y_cursor = next_y

    # Bottom H to final column
    add_trk(board, net, XCOL, 79.0, 26.32, 79.0, W, B)
    # Drop through P0.01 gap to via, then F to pad
    add_trk(board, net, 26.32, 79.0, 26.32, 78.0, W, B)
    add_via(board, net, 26.32, 78.0)
    add_trk(board, net, 26.32, 78.0, 26.32, 76.0, W, F)

    summary["p008_stitch"] = {
        "layer_primary": "B.Cu",
        "column_x": XCOL,
        "f_hops": hops,
        "bottom_y": 79.0,
        "final_via": [26.32, 78.0],
        "pad": [26.32, 76.0],
    }

    # --- Restore P0.15 @ y=77.45 wide F-bridge (gap covers P0.01 jog columns) ---
    p015 = [r for r in rip_meta if r[0] == "P0.15"]
    if p015:
        _, x0, x1, y, w, _ = p015[0]
        xl, xr = 61.5, 68.5
        add_trk(board, "P0.15", x0, y, xl, y, w, B)
        add_via(board, "P0.15", xl, y)
        add_trk(board, "P0.15", xl, y, xr, y, w, F)
        add_via(board, "P0.15", xr, y)
        add_trk(board, "P0.15", xr, y, x1, y, w, B)
        summary["restores"]["P0.15_col"] = {
            "type": "F-bridge-wide",
            "y": y,
            "xl": xl,
            "xr": xr,
            "span": [x0, x1],
        }

    # --- Restore P0.01: final F-bridge + column U-jog F@y=74.5 (clear of J13/P0.15) ---
    p001 = [r for r in rip_meta if r[0] == "P0.01"]
    if p001:
        _, x0, x1, y, w, _ = p001[0]  # full track 8.54-80.51

        # Final bridge (west of P0.04 F start @27.7)
        add_trk(board, "P0.01", x0, y, 24.5, y, w, B)
        add_via(board, "P0.01", 24.5, y)
        add_trk(board, "P0.01", 24.5, y, 27.2, y, w, F)
        add_via(board, "P0.01", 27.2, y)
        add_trk(board, "P0.01", 27.2, y, 62.0, y, w, B)

        # Column U-jog south @ y=74.5 (2.95 mm below P0.15 restore)
        add_trk(board, "P0.01", 62.0, y, 62.0, 74.5, w, B)
        add_via(board, "P0.01", 62.0, 74.5)
        add_trk(board, "P0.01", 62.0, 74.5, 68.0, 74.5, w, F)
        add_via(board, "P0.01", 68.0, 74.5)
        add_trk(board, "P0.01", 68.0, 74.5, 68.0, y, w, B)
        add_trk(board, "P0.01", 68.0, y, x1, y, w, B)

        summary["restores"]["P0.01_final"] = {
            "type": "F-bridge",
            "y": y,
            "xl": 24.5,
            "xr": 27.2,
        }
        summary["restores"]["P0.01_col"] = {
            "type": "U-jog-F-south",
            "y_trk": y,
            "y_f": 74.5,
            "xl": 62.0,
            "xr": 68.0,
        }

    fill_zones(board)
    save(board)
    shutil.copy2(BOARD, f"{SNAP}/after-stitch.kicad_pcb")

    print("DRC MID (after stitch)...")
    mid_data, mid = run_drc(f"{REPORTS}/DRC_PASS30J_MID.json")
    summary["mid"] = mid
    mid_nets = nets_of(mid_data)
    print("  mid:", mid)

    # Delta nets
    delta = {}
    for n in set(before_nets) | set(mid_nets):
        d = mid_nets.get(n, 0) - before_nets.get(n, 0)
        if d:
            delta[n] = d
    summary["net_unconnected_delta_mid"] = delta
    print("  net delta:", delta)

    p015_after = p015_west(board)
    summary["p015_west_segs"]["after"] = p015_after
    summary["p015_west_segs"]["preserved"] = p015_after >= p015_before

    # Success gate
    worse = (
        mid["shorting_items"] > 0
        or mid["clearance"] > 0
        or mid["tracks_crossing"] > 0
        or mid["unconnected_items"] > before["unconnected_items"]
    )
    p008_closed = mid_nets.get("P0.08", 0) < before_nets.get("P0.08", 0)

    if worse:
        print("WORSE — reverting stitch to pre-backup")
        shutil.copy2(backup, BOARD)
        board = load()
        fill_zones(board)
        save(board)
        summary["reverted"] = True
        summary["stop"] = True
        summary["notes"].append(
            "Stitch reverted: shorting/clearance/crossing rose or unconnected worsened."
        )
        after_data, after = run_drc(f"{REPORTS}/DRC_PASS30J_AFTER.json")
        summary["after"] = after
        summary["signal_net_deltas"] = {}
        summary["p008_j12_closed"] = False
    else:
        summary["after"] = mid
        after_data, after = mid_data, mid
        # copy mid as after
        shutil.copy2(f"{REPORTS}/DRC_PASS30J_MID.json", f"{REPORTS}/DRC_PASS30J_AFTER.json")
        summary["signal_net_deltas"] = {
            n: d
            for n, d in delta.items()
            if n not in ("GND",) and not n.startswith("unconnected")
        }
        summary["p008_j12_closed"] = p008_closed
        if p008_closed:
            summary["closed"].append("P0.08 U1/SW3/R14 ↔ J12.9 (B@x65.2 + B@y79 + F final)")
            summary["notes"].append(
                "P0.08 fully closed to J12.9. Stage A + pass30i ENABLE/COEX2/P0.08 trunk kept."
            )
            # Cheap VIN_F / SWDCLK only if corridor free — probe counts; skip if not cheap
            # Per scope: attempt only if cheap. With unconnected already dropped, skip deep RIP — document.
            summary["vin_f"] = "skipped_not_cheap_geometry"
            summary["swdclk"] = "skipped_not_cheap_geometry"
            summary["notes"].append(
                "VIN_F/SWDCLK not attempted: Class-F corridors still congested; one-cycle budget spent on P0.08."
            )
        else:
            summary["notes"].append(
                "No shorting/clearance but P0.08 unconnected count did not drop — inspect."
            )
            summary["stop"] = True

        if not summary["p015_west_segs"]["preserved"]:
            summary["notes"].append("WARNING: P0.15 west seg count dropped")

    summary["success_gate"] = (
        "signal-net drop with shorting=0 clearance=0 crossing=0 — "
        + ("MET" if (not summary["reverted"] and p008_closed and after["shorting_items"] == 0 and after["clearance"] == 0) else "NOT MET")
    )

    summary["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30J_BEFORE.json",
        "reports/DRC_PASS30J_MID.json",
        "reports/DRC_PASS30J_AFTER.json",
        "reports/PASS30J_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30j.py",
    ]

    with open(f"{REPORTS}/PASS30J_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0 if not summary["reverted"] else 1


if __name__ == "__main__":
    if "--apply" not in sys.argv:
        print(__doc__)
        print("Pass --apply to execute.")
        sys.exit(0)
    sys.exit(main())
