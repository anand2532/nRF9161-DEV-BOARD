#!/usr/bin/env python3
"""Pass30l — Class F: SWDCLK F/mixed detour around J8.3 → nRESET → P0.02; else option C.

ONE honest cycle. No J8 move. No Gerbers. Protect Stage A + pass30i–30k copper + P0.15 west wrap + RF/U3.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30l-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
VIA_D, VIA_DRILL = 0.6, 0.3

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
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30l.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30l.json", path)
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


def clean(stats):
    return stats["shorting_items"] == 0 and stats["clearance"] == 0 and stats["tracks_crossing"] == 0


def signal_deltas(before_nets, after_nets, watch):
    out = {}
    for n in watch:
        out[n] = after_nets.get(n, 0) - before_nets.get(n, 0)
    return out


def restore_board(path):
    shutil.copy2(path, BOARD)


def apply_swdclk(board):
    """Mixed F/B SWDCLK: west B column x=34.2, F-hop over VDD_GPIO H@19.13,
    F north band y=1.5 around J8.3 into existing via@(53.65,4.73). No VDD_GPIO rip."""
    net = "SWDCLK"
    X = 34.2
    path = {
        "X_west": X,
        "segments": [
            "F (37.75,26.75)->(37.75,24.8)",
            f"via(37.75,24.8) B->({X},24.8)->({X},19.8)",
            f"via F-hop over VDD_GPIO H@19.13: ({X},19.8)->({X},18.4)",
            f"B ({X},18.4)->({X},1.5) via",
            "F ({X},1.5)->(53.65,1.5)->(53.65,4.73) into existing SWDCLK via",
        ],
        "notes": "F/mixed detour north of J8.3 GND@(48.05,4.73); no J8 move; no VDD_GPIO rip",
    }
    add_trk(board, net, 37.75, 26.75, 37.75, 24.8, W, F)
    add_via(board, net, 37.75, 24.8)
    add_trk(board, net, 37.75, 24.8, X, 24.8, W, B)
    add_trk(board, net, X, 24.8, X, 19.8, W, B)
    add_via(board, net, X, 19.8)
    add_trk(board, net, X, 19.8, X, 18.4, W, F)
    add_via(board, net, X, 18.4)
    add_trk(board, net, X, 18.4, X, 1.5, W, B)
    add_via(board, net, X, 1.5)
    add_trk(board, net, X, 1.5, 53.65, 1.5, W, F)
    add_trk(board, net, 53.65, 1.5, 53.65, 4.73, W, F)
    return path


def probe_nreset_gap(board):
    """Describe nRESET islands for corridor attempt / block reason."""
    return {
        "west_island": "U1.32/J8.8/C39 bbox~(38.2,7.3)-(53.6,26.8)",
        "east_island": "R5.1/TP9 bbox~(101.7,26.0)-(103.3,58.8)",
        "gap_mm": "~48 mm east-west through ENABLE/VIN_FILT/VDD2/P0.15/VIN_F via forest",
    }


def try_nreset_corridor(board, summary):
    """One honest probe: B H @ y=27.5 from west island tip to east, F-hop blockers.

    West tip near (53.65,10.8) / (52.22,11.2); east at (101.68,26).
    Prefer B @ y=12.5 under VIN_F B@y11? VIN_F occupies y11. Try y=13.5.
    If restore not clean — revert nRESET-only copper and report.
    """
    net = "nRESET"
    # Snapshot path for revert: we'll track added items by saving pre-file
    pre = f"{SNAP}/pre-nreset.kicad_pcb"
    save(board, pre)

    # West attach: existing F via at (53.65,7.27) and tracks to (52.22,11.2).
    # Add F stub east then via to B, run B east at y=12.6 (between VIN_F@11 and P0.15@15.35).
    # VIN_F has B at y=11 and V at x=70.8 — will need F-hops.
    # ENABLE vias around x=62.5 — hop.
    # This is congested; attempt a minimal probe path and DRC.

    # Attach from west F copper at (53.65,10.8) — extend east on F to via
    y = 12.6
    add_trk(board, net, 53.65, 10.8, 53.65, y, W, F)
    add_via(board, net, 53.65, y)

    # Candidate hops over known verticals (x positions from prior passes)
    # Path B along y=12.6 from 53.65 to 101.68 with F-hops at congested x
    hops = [
        # (x_via_w, x_via_e) F-hop windows where B verticals likely block
        (57.9, 58.2),   # near VDD2-ish — may be empty; harmless extra vias if clear
        (62.3, 62.7),   # ENABLE @62.5 if present on B at this y
        (69.0, 71.0),   # VIN_F / VDD_GPIO region
        (76.5, 79.5),   # ENABLE east
    ]
    # Simpler honest attempt: continuous B with only VIN_F column hop at x~70.8
    # and ENABLE if we detect tracks. For one cycle, place:
    xs = [53.65, 61.0, 62.9, 69.0, 72.0, 90.0, 101.68]
    # Manual F-hops between 61-62.9 (ENABLE) and 69-72 (VIN_F V@70.8)
    add_trk(board, net, 53.65, y, 61.0, y, W, B)
    add_via(board, net, 61.0, y)
    add_trk(board, net, 61.0, y, 62.9, y, W, F)
    add_via(board, net, 62.9, y)
    add_trk(board, net, 62.9, y, 69.0, y, W, B)
    add_via(board, net, 69.0, y)
    add_trk(board, net, 69.0, y, 72.0, y, W, F)
    add_via(board, net, 72.0, y)
    add_trk(board, net, 72.0, y, 101.68, y, W, B)
    # Rise to R5 pad y=26 on B then via/F if needed — R5 is on F at (101.68,26)
    add_trk(board, net, 101.68, y, 101.68, 26.0, W, B)
    add_via(board, net, 101.68, 26.0)
    # via on pad is OK (same net)

    summary["nreset_attempt"] = {
        "y": y,
        "f_hops": [[61.0, 62.9], [69.0, 72.0]],
        "attach": "F (53.65,10.8)->(53.65,12.6) via + B corridor to R5",
    }
    return pre


def find_cheap_option_c(before_nets, board):
    """Pick a few clear true-signal header/stub islands (not dangling load-bearing vias)."""
    # Prefer single-unconnected signal nets with short geometric gaps
    candidates = []
    for net, cnt in sorted(before_nets.items(), key=lambda kv: kv[1]):
        if net in ("GND", "VDD_GPIO", "VDD2", "VDD_nRF", "VIN_F", "VIN_FILT"):
            continue
        if cnt != 1:
            continue
        if net in ("SWDCLK", "nRESET", "P0.02"):
            continue
        candidates.append(net)
    return candidates[:8]


def try_coex0(board, summary):
    """Attempt COEX0 if islands are locally close — from DRC: two F tracks."""
    segs = []
    for t in board.GetTracks():
        if t.GetNetname() != "COEX0" or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetLayer() != F:
            continue
        xs, ys = mm(t.GetStart().x), mm(t.GetStart().y)
        xe, ye = mm(t.GetEnd().x), mm(t.GetEnd().y)
        segs.append((xs, ys, xe, ye, mm(t.GetWidth())))
    summary["coex0_segs"] = segs
    # Known from prior: short F stubs — try connect endpoints if gap < 5mm same-ish y
    if len(segs) < 2:
        return False, "fewer than 2 F segs"
    # Use island analysis
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == "COEX0":
                pads.append((fp.GetReference(), p.GetNumber(), mm(p.GetPosition().x), mm(p.GetPosition().y)))
    summary["coex0_pads"] = pads
    return False, "deferred_geometry"


def main():
    summary = {
        "pass": "layout-pass30l",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "one_honest_cycle": True,
        "keep_stage_A": True,
        "keep_pass30i_30k": True,
        "no_placement": True,
        "no_j8_move": True,
        "order": ["SWDCLK", "nRESET", "P0.02", "option_C"],
        "closed": [],
        "blocked": {},
        "proposals": [],
        "restores": {},
        "reverted_nets": [],
        "class_f_restore_failures": 0,
        "stop": False,
        "notes": [],
    }

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30l-{ts}"
    shutil.copy2(BOARD, backup)
    shutil.copy2(BOARD, f"{SNAP}/pre.kicad_pcb")
    summary["backup"] = backup.replace(ROOT + "/", "")
    print("Backup:", backup)

    board = load()
    p015_before = p015_west(board)
    summary["p015_west_segs"] = {"before": p015_before}
    summary["stage_a_check_before"] = stage_a_ok(board)

    print("DRC BEFORE...")
    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30L_BEFORE.json")
    summary["before"] = before
    before_nets = nets_of(before_data)
    print("  before:", before)

    watch = [
        "SWDCLK", "nRESET", "P0.02", "COEX0", "P0.15", "VDD_GPIO",
        "ENABLE", "VIN_F", "VIN_FILT", "P0.08", "GND",
    ]

    # ========== 1) SWDCLK ==========
    print("Applying SWDCLK mixed detour...")
    summary["swdclk"] = apply_swdclk(board)
    fill_zones(board)
    save(board)
    shutil.copy2(BOARD, f"{SNAP}/after-swdclk.kicad_pcb")

    print("DRC MID (SWDCLK)...")
    mid_data, mid = run_drc(f"{REPORTS}/DRC_PASS30L_MID.json")
    summary["mid_swdclk"] = mid
    mid_nets = nets_of(mid_data)
    print("  mid:", mid)

    if not clean(mid):
        print("SWDCLK DRC dirty — reverting SWDCLK copper")
        restore_board(f"{SNAP}/pre.kicad_pcb")
        board = load()
        fill_zones(board)
        save(board)
        summary["reverted_nets"].append("SWDCLK")
        summary["class_f_restore_failures"] += 1
        summary["blocked"]["SWDCLK"] = (
            f"Mixed F/B detour failed DRC: shorting={mid['shorting_items']} "
            f"clearance={mid['clearance']} crossing={mid['tracks_crossing']}"
        )
        # Propose J8 ≤3mm delta without moving
        summary["proposals"].append({
            "ref": "J8",
            "from_mm": [50.0, 6.0],
            "to_mm": [50.0, 3.5],
            "delta_mm": 2.5,
            "why": (
                "Shift J8 north ≤3mm so SWDCLK pad J8.4 clears VDD_GPIO V@x48.05 / "
                "opens B H@y≈5 east approach; avoids F north-band squeeze vs SWDIO@y2.76 + TP7"
            ),
        })
    elif mid_nets.get("SWDCLK", 0) >= before_nets.get("SWDCLK", 0):
        print("SWDCLK unconnected not reduced — reverting")
        restore_board(f"{SNAP}/pre.kicad_pcb")
        board = load()
        fill_zones(board)
        save(board)
        summary["reverted_nets"].append("SWDCLK")
        summary["class_f_restore_failures"] += 1
        summary["blocked"]["SWDCLK"] = "Path applied but unconnected count for SWDCLK did not drop"
        summary["proposals"].append({
            "ref": "J8",
            "from_mm": [50.0, 6.0],
            "to_mm": [52.5, 6.0],
            "delta_mm": 2.5,
            "why": "Shift J8 east ≤3mm to open west B column approach past J8.3 GND@x48.05 without F north squeeze",
        })
    else:
        summary["closed"].append("SWDCLK")
        summary["notes"].append(
            f"SWDCLK closed: unconnected {before['unconnected_items']}→{mid['unconnected_items']}"
        )
        shutil.copy2(BOARD, f"{SNAP}/keep-swdclk.kicad_pcb")

    # Refresh baseline after SWDCLK decision
    board = load()
    cur_data, cur = run_drc(f"{REPORTS}/DRC_PASS30L_MID.json")
    cur_nets = nets_of(cur_data)
    summary["after_swdclk"] = cur
    class_f_failures = summary["class_f_restore_failures"]

    # ========== 2) nRESET ==========
    if class_f_failures < 2:
        print("Attempting nRESET corridor...")
        summary["nreset_gap"] = probe_nreset_gap(board)
        pre_nr = f"{SNAP}/pre-nreset.kicad_pcb"
        shutil.copy2(BOARD, pre_nr)
        try_nreset_corridor(board, summary)
        fill_zones(board)
        save(board)
        nr_data, nr = run_drc(f"{REPORTS}/DRC_PASS30L_MID_NRESET.json")
        nr_nets = nets_of(nr_data)
        summary["mid_nreset"] = nr
        print("  nreset mid:", nr)

        if not clean(nr) or nr_nets.get("nRESET", 0) >= cur_nets.get("nRESET", 0):
            print("nRESET failed — reverting nRESET only")
            restore_board(pre_nr)
            board = load()
            fill_zones(board)
            save(board)
            summary["reverted_nets"].append("nRESET")
            summary["class_f_restore_failures"] += 1
            summary["blocked"]["nRESET"] = (
                f"Corridor @y=12.6 failed clean: shorting={nr['shorting_items']} "
                f"clearance={nr['clearance']} crossing={nr['tracks_crossing']} "
                f"nRESET_unc={nr_nets.get('nRESET')} (was {cur_nets.get('nRESET')}). "
                + json.dumps(summary.get("nreset_gap", {}))
            )
            class_f_failures = summary["class_f_restore_failures"]
        else:
            summary["closed"].append("nRESET")
            summary["notes"].append(
                f"nRESET closed: unconnected {cur['unconnected_items']}→{nr['unconnected_items']}"
            )
            cur, cur_nets = nr, nr_nets

    # ========== 3) P0.02 only if clear corridor after 1-2 ==========
    board = load()
    if class_f_failures < 2 and "nRESET" in summary["closed"]:
        summary["blocked"]["P0.02"] = "Skipped — no clear new corridor identified after SWDCLK/nRESET in one cycle"
    else:
        summary["blocked"]["P0.02"] = (
            "Not attempted — Class-F restore failures="
            f"{class_f_failures} or nRESET not closed; stop thrash"
        )

    # ========== 4) Option C if Class F stalls ==========
    if class_f_failures >= 1 and "SWDCLK" not in summary["closed"]:
        # full stall
        pass
    if len(summary["closed"]) == 0 or (
        class_f_failures >= 2 or ("SWDCLK" in summary["closed"] and "nRESET" not in summary["closed"])
    ):
        print("Option C: scan cheap signal islands...")
        board = load()
        # Refresh nets
        c_data, cstats = run_drc(f"{REPORTS}/DRC_PASS30L_MID_OPTC.json")
        c_nets = nets_of(c_data)
        cands = find_cheap_option_c(c_nets, board)
        summary["option_c_candidates"] = cands
        summary["notes"].append(f"Option C candidates (1-unc signal): {cands}")

        # Try COEX0 documentation only unless trivial
        ok, why = try_coex0(board, summary)
        if not ok:
            summary["blocked"]["COEX0"] = why

        # Look for MAGPIO1 / MIPI short stubs — only if endpoints < 3mm
        for net in cands[:4]:
            pads = []
            for fp in board.GetFootprints():
                for p in fp.Pads():
                    if p.GetNetname() == net:
                        pads.append((fp.GetReference(), mm(p.GetPosition().x), mm(p.GetPosition().y)))
            ends = []
            for t in board.GetTracks():
                if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T:
                    continue
                ends.append((mm(t.GetStart().x), mm(t.GetStart().y), board.GetLayerName(t.GetLayer())))
                ends.append((mm(t.GetEnd().x), mm(t.GetEnd().y), board.GetLayerName(t.GetLayer())))
            summary.setdefault("option_c_geometry", {})[net] = {"pads": pads, "ends_sample": ends[:6]}

    # ========== FINAL ==========
    board = load()
    fill_zones(board)
    save(board)
    print("DRC AFTER...")
    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30L_AFTER.json")
    after_nets = nets_of(after_data)
    summary["after"] = after
    summary["signal_net_deltas"] = signal_deltas(before_nets, after_nets, watch)
    all_d = {}
    for n in set(before_nets) | set(after_nets):
        d = after_nets.get(n, 0) - before_nets.get(n, 0)
        if d:
            all_d[n] = d
    summary["all_net_deltas"] = all_d

    p015_after = p015_west(board)
    summary["p015_west_segs"]["after"] = p015_after
    summary["p015_west_segs"]["preserved"] = p015_after >= p015_before
    summary["stage_a_check"] = stage_a_ok(board)

    if after["unconnected_items"] < before["unconnected_items"] and clean(after):
        summary["success_gate"] = (
            f"MET ({before['unconnected_items']}→{after['unconnected_items']})"
        )
    else:
        summary["success_gate"] = (
            f"NOT MET (unc {before['unconnected_items']}→{after['unconnected_items']}, "
            f"shorting={after['shorting_items']} clearance={after['clearance']})"
        )

    if class_f_failures >= 2 and not summary["closed"]:
        summary["stop"] = True
        summary["stop_reason"] = "Two Class-F failures; moved to option C scan / stop with proposals"
    elif "SWDCLK" in summary["closed"] and "nRESET" not in summary["closed"]:
        summary["stop"] = True
        summary["stop_reason"] = (
            "SWDCLK kept; nRESET one-probe failed — STOP further Class-F thrash per PM"
        )
    elif not summary["closed"]:
        summary["stop"] = True
        summary["stop_reason"] = "No nets closed this cycle; proposals recorded"

    summary["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30L_BEFORE.json",
        "reports/DRC_PASS30L_MID.json",
        "reports/DRC_PASS30L_AFTER.json",
        "reports/PASS30L_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30l.py",
    ]

    with open(f"{REPORTS}/PASS30L_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
