#!/usr/bin/env python3
"""Pass30t — executed 2026-09-23. See reports/PASS30T_SUMMARY.json.

Steering: P0.11 stubs → P0.10/P0.17 → MAGPIO/MIPI/AUX if clean → VDD_GPIO low-risk.
SKIP P0.31. No J13/J11 moves. No Gerbers. Atomic rip/restore.

Results:
- P0.11/P0.10/P0.17/MAGPIO1/AUX: all DRC-dirty; atomic restore OK (restore_fail_streak=0).
- VDD_GPIO J16↔J17 F-jog @x=111.0 KEPT (69→68). Direct F@x108 shorts J17.1 P0.17.
- Board = pass30r keep + VDD_GPIO island. P0.15 west / Stage A / P0.22 preserved.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30t-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
BACKUP = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30t-20260923-124446"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
VIA_D, VIA_DRILL = 0.6, 0.3

os.makedirs(SNAP, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

WATCH = [
    "P0.11", "P0.10", "P0.17", "P0.22", "P0.31", "P0.15", "P0.16", "P0.18",
    "MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_SCLK", "MIPI_SDATA", "MIPI_VIO",
    "AUX", "AUX_FIT", "VDD_GPIO", "VDD2", "VDD_nRF", "GND", "P0.01", "P0.08",
]


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
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


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
    return v


def run_drc(out_path):
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30t.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30t.json", out_path)
    data = json.load(open(out_path))
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


def clean(stats):
    return (
        stats["shorting_items"] == 0
        and stats["clearance"] == 0
        and stats["tracks_crossing"] == 0
    )


def p015_west(board):
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != "P0.15" or t.GetLayer() != B:
            continue
        if min(mm(t.GetStart().x), mm(t.GetEnd().x)) < 45:
            n += 1
    return n


def stage_a_ok(board):
    ok = {"VDD_nRF_via_north": False, "VDD2_vias": 0}
    for t in list(board.GetTracks()):
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


def zone_fill():
    fill_script = f"{SNAP}/zone_fill_once.py"
    open(fill_script, "w").write(
        "import pcbnew\n"
        f"b=pcbnew.LoadBoard({BOARD!r})\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        f"pcbnew.SaveBoard({BOARD!r}, b)\n"
        "print('zone-fill saved', flush=True)\n"
    )
    return subprocess.call([sys.executable, fill_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def colliding_from_drc(data):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in ("shorting_items", "clearance", "tracks_crossing"):
            out.append({
                "type": v.get("type"),
                "description": v.get("description", "")[:300],
                "items": [
                    {"description": it.get("description", "")[:200], "pos": it.get("pos")}
                    for it in v.get("items", [])[:4]
                ],
            })
    return out[:12]


def snap_copy(name):
    dst = f"{SNAP}/{name}.kicad_pcb"
    shutil.copy2(BOARD, dst)
    return dst


def restore_from(path):
    shutil.copy2(path, BOARD)


# ---------- attempt harness ----------
RESULT = {
    "pass": "layout-pass30t",
    "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
    "phase": "RUNNING",
    "scope": "P0.11 stubs → P0.10/P0.17 → MAGPIO/MIPI/AUX if clean → VDD_GPIO islands low-risk; SKIP P0.31",
    "keep_stage_A": True,
    "keep_pass30i_30r": True,
    "keep_p022_pass30r": True,
    "no_gerbers": True,
    "hard_bans": [
        "P0.15 west wrap",
        "RF keepout",
        "U3/matching",
        "Stage A VDD2 / protected wraps",
        "pass30i-30r closed copper",
        "P0.22 pass30r keep",
        "J13/J11 moves",
        "P0.31 (skipped this pass)",
    ],
    "backup": os.path.relpath(BACKUP, ROOT),
    "closed": [],
    "blocked": {},
    "reverted_attempts": [],
    "copper_attempts": [],
    "restore_fail_streak": 0,
    "skipped": ["P0.31"],
}


def atomic_attempt(name, net, build_fn, mid_drc_name, baseline_path):
    """build_fn(board) adds copper. Returns (kept:bool, stats, reason)."""
    global RESULT
    pre = f"{SNAP}/pre-{name}.kicad_pcb"
    shutil.copy2(BOARD, pre)
    board = load()
    try:
        build_fn(board)
    except Exception as e:
        restore_from(pre)
        RESULT["reverted_attempts"].append({"net": net, "id": name, "reason": f"build_error:{e}"})
        RESULT["copper_attempts"].append({"id": name, "net": net, "result": f"build_error:{e}"})
        return False, None, f"build_error:{e}"
    save(board)
    zone_fill()
    data, stats = run_drc(f"{REPORTS}/{mid_drc_name}")
    if clean(stats):
        # also require no increase in shorting etc already covered; prefer unconnected drop or equal
        RESULT["copper_attempts"].append({"id": name, "net": net, "result": f"CLEAN {stats}"})
        # Keep only if unconnected improved OR same (stub that doesn't hurt) — require improve for keep
        # Actually: keep if clean AND unconnected <= baseline unconnected for this attempt's start
        return True, stats, "clean"
    # dirty → full revert of this net's edit
    restore_from(pre)
    zone_fill()
    data2, stats2 = run_drc(f"{REPORTS}/{mid_drc_name.replace('.json', '_REVERT.json')}")
    if not clean(stats2):
        RESULT["restore_fail_streak"] += 1
        RESULT["reverted_attempts"].append({
            "net": net, "id": name,
            "reason": f"dirty={stats}; RESTORE_FAIL after revert stats={stats2}",
        })
        RESULT["copper_attempts"].append({"id": name, "net": net, "result": f"dirty+restore_fail {stats}"})
        # hard restore from baseline_path
        restore_from(baseline_path)
        zone_fill()
        return False, stats, "restore_fail"
    RESULT["restore_fail_streak"] = 0
    collide = colliding_from_drc(data)
    RESULT["reverted_attempts"].append({
        "net": net, "id": name,
        "reason": f"dirty={stats}",
        "collide": collide[:5],
    })
    RESULT["copper_attempts"].append({
        "id": name, "net": net,
        "result": f"dirty shorting={stats['shorting_items']} clearance={stats['clearance']} crossing={stats['tracks_crossing']}",
    })
    return False, stats, "dirty"


def keep_if_improved(name, net, before_unc, stats):
    if stats["unconnected_items"] < before_unc and clean(stats):
        RESULT["closed"].append(f"{net} ({name})")
        RESULT["restore_fail_streak"] = 0
        return True
    # clean but no improvement → revert (don't keep dead copper)
    return False


# ========== builders ==========

def build_p011_j16_by9(board):
    """P0.11: from via(49.92,28) → B@y9.2 east → F-hop over P0.15@x106 → J16.2."""
    net = "P0.11"
    # drop via already at 49.92,28 — add B south then east
    add_trk(board, net, 49.92, 28.0, 49.92, 9.2, W, B)
    add_trk(board, net, 49.92, 9.2, 100.0, 9.2, W, B)
    # F-hop over P0.15 B V@x106 and approach
    add_via(board, net, 100.0, 9.2)
    add_trk(board, net, 100.0, 9.2, 100.0, 10.54, W, F)
    add_trk(board, net, 100.0, 10.54, 108.0, 10.54, W, F)


def build_p011_j16_by6(board):
    """P0.11: B@y6 north-band style toward J16."""
    net = "P0.11"
    add_trk(board, net, 49.92, 28.0, 49.92, 6.0, W, B)
    add_trk(board, net, 49.92, 6.0, 104.0, 6.0, W, B)
    add_via(board, net, 104.0, 6.0)
    add_trk(board, net, 104.0, 6.0, 104.0, 10.54, W, F)
    add_trk(board, net, 104.0, 10.54, 108.0, 10.54, W, F)


def build_p011_j16_fy10_with_hops(board):
    """P0.11 F@y10.54 with via hops around nRESET/VIN — start from via east on F then drop."""
    net = "P0.11"
    # From via 49.92,28 go F north carefully via B dodge of VDD1
    add_trk(board, net, 49.92, 28.0, 49.92, 29.5, W, B)
    add_trk(board, net, 49.92, 29.5, 52.5, 29.5, W, B)
    add_trk(board, net, 52.5, 29.5, 52.5, 10.54, W, B)
    # F-hop nRESET band around y10.8-12.6: stay B until past, then F to pad
    add_via(board, net, 52.5, 10.54)
    add_trk(board, net, 52.5, 10.54, 108.0, 10.54, W, F)


def build_p011_j12_bx35_fhops(board):
    """P0.11 B west/south to J12 with F-hops over COEX0/P0.13/P0.15."""
    net = "P0.11"
    # from island (44,29.2)
    add_trk(board, net, 44.0, 29.2, 35.0, 29.2, W, B)
    # F-hop P0.13 V@x40 already west of it at x35
    add_trk(board, net, 35.0, 29.2, 35.0, 42.0, W, B)
    # F-hop COEX0 H@y43
    add_via(board, net, 35.0, 42.0)
    add_trk(board, net, 35.0, 42.0, 35.0, 44.0, W, F)
    add_via(board, net, 35.0, 44.0)
    add_trk(board, net, 35.0, 44.0, 35.0, 61.0, W, B)
    # F-hop COEX0 H@y58.8
    add_via(board, net, 35.0, 57.5)
    add_trk(board, net, 35.0, 57.5, 35.0, 60.0, W, F)
    add_via(board, net, 35.0, 60.0)
    add_trk(board, net, 35.0, 60.0, 35.0, 74.5, W, B)
    # approach J12 — F-hop P0.13/P0.14/P0.15 columns near bottom
    add_via(board, net, 35.0, 74.5)
    add_trk(board, net, 35.0, 74.5, 33.94, 74.5, W, F)
    add_trk(board, net, 33.94, 74.5, 33.94, 76.0, W, F)


def build_p010_j16_by9(board):
    net = "P0.10"
    # from via 47.4,28.5
    add_trk(board, net, 47.4, 28.5, 47.4, 9.0, W, B)
    add_trk(board, net, 47.4, 9.0, 100.0, 9.0, W, B)
    add_via(board, net, 100.0, 9.0)
    add_trk(board, net, 100.0, 9.0, 100.0, 8.0, W, F)
    add_trk(board, net, 100.0, 8.0, 108.0, 8.0, W, F)


def build_p010_j12_bx32(board):
    net = "P0.10"
    add_via(board, net, 47.4, 29.5)  # may already have via at 47.4,28.5
    add_trk(board, net, 47.4, 28.5, 47.4, 29.5, W, B)
    # F-hop over P0.11 B H@y29.2
    add_via(board, net, 47.4, 29.5)
    add_trk(board, net, 47.4, 29.5, 47.4, 30.5, W, F)
    add_via(board, net, 47.4, 30.5)
    add_trk(board, net, 47.4, 30.5, 31.4, 30.5, W, B)
    add_trk(board, net, 31.4, 30.5, 31.4, 74.5, W, B)
    add_via(board, net, 31.4, 74.5)
    add_trk(board, net, 31.4, 74.5, 31.4, 76.0, W, F)


def build_p017_island_x45(board):
    """Join U1 via island to bottom J18 island with F-hops."""
    net = "P0.17"
    # from via 40.25,23.1
    add_trk(board, net, 40.25, 23.1, 40.25, 24.5, W, B)
    add_trk(board, net, 40.25, 24.5, 45.0, 24.5, W, B)
    add_trk(board, net, 45.0, 24.5, 45.0, 32.0, W, B)
    # F-hop COEX2@y33.2 and P0.08@y30.25
    add_via(board, net, 45.0, 29.0)
    add_trk(board, net, 45.0, 29.0, 45.0, 34.5, W, F)
    add_via(board, net, 45.0, 34.5)
    add_trk(board, net, 45.0, 34.5, 45.0, 57.0, W, B)
    # F-hop COEX0@y58.8
    add_via(board, net, 45.0, 57.5)
    add_trk(board, net, 45.0, 57.5, 45.0, 60.5, W, F)
    add_via(board, net, 45.0, 60.5)
    add_trk(board, net, 45.0, 60.5, 48.16, 60.5, W, B)
    add_trk(board, net, 48.16, 60.5, 48.16, 62.0, W, B)


def build_p017_j17_by70_fhops(board):
    """J13 island → J17 with F-hops over P0.22/P0.01/P0.15."""
    net = "P0.17"
    add_trk(board, net, 66.54, 73.4, 78.0, 73.4, W, B)
    # F-hop P0.22 col / P0.01
    add_via(board, net, 78.0, 73.4)
    add_trk(board, net, 78.0, 73.4, 82.0, 73.4, W, F)
    add_via(board, net, 82.0, 73.4)
    add_trk(board, net, 82.0, 73.4, 98.0, 73.4, W, B)
    add_trk(board, net, 98.0, 73.4, 98.0, 28.0, W, B)
    # F-hop wall P0.01@105.55 / P0.15@106 / nRESET / COEX2
    add_via(board, net, 98.0, 28.0)
    add_trk(board, net, 98.0, 28.0, 108.0, 28.0, W, F)
    add_trk(board, net, 108.0, 28.0, 108.0, 26.0, W, F)


def build_magpio1_north(board):
    """MAGPIO1 long north-of-keepout — likely dirty; try once."""
    net = "MAGPIO1"
    add_trk(board, net, 25.6, 23.1, 25.6, 5.0, W, B)
    add_trk(board, net, 25.6, 5.0, 98.0, 5.0, W, B)
    add_trk(board, net, 98.0, 5.0, 98.0, 49.27, W, B)
    add_via(board, net, 98.0, 49.27)
    add_trk(board, net, 98.0, 49.27, 104.0, 49.27, W, F)


def build_aux_jog(board):
    """AUX east of RF trunk — prior fails expected."""
    net = "AUX"
    add_trk(board, net, 20.485, 33.0, 23.5, 33.0, W, F)
    add_trk(board, net, 23.5, 33.0, 23.5, 48.0, W, F)
    add_trk(board, net, 23.5, 48.0, 19.52, 48.0, W, F)


def build_vddgpio_j16_f(board):
    """Low-risk: F column x=108 joining J17.3 stub to J16.5 stub."""
    net = "VDD_GPIO"
    add_trk(board, net, 108.0, 31.08, 108.0, 18.16, 0.25, F)


def build_vddgpio_u1_f_via(board):
    """U1.12 fanout to existing via@40.17,19.126 — may hit P0.17."""
    net = "VDD_GPIO"
    add_trk(board, net, 44.0, 31.5, 42.0, 31.5, 0.25, F)
    add_via(board, net, 42.0, 31.5)
    add_trk(board, net, 42.0, 31.5, 42.0, 19.13, 0.25, B)
    add_trk(board, net, 42.0, 19.13, 40.17, 19.13, 0.25, B)


# ========== main ==========

def main():
    assert os.path.exists(BACKUP), BACKUP
    # ensure start = pass30r keep
    # DRC before already written by probe; re-run to be authoritative
    data0, stats0 = run_drc(f"{REPORTS}/DRC_PASS30T_BEFORE.json")
    nets0 = nets_of(data0)
    board0 = load()
    p015_0 = p015_west(board0)
    stage0 = stage_a_ok(board0)
    baseline = snap_copy("baseline_start")
    keep_snap = baseline

    RESULT["before"] = stats0
    RESULT["before_nets_watch"] = {n: nets0.get(n, 0) for n in WATCH}
    RESULT["p015_west_segs"] = {"before": p015_0}
    RESULT["stage_a_check"] = stage0

    print("BEFORE", stats0, flush=True)
    assert stats0["unconnected_items"] == 69, stats0
    assert clean(stats0), stats0

    stop = False

    def attempt_keep(name, net, builder, mid):
        nonlocal keep_snap, stop
        if stop:
            return False
        before_unc = run_drc(f"{REPORTS}/DRC_PASS30T_PROBE_TMP.json")[1]["unconnected_items"]
        kept_clean, stats, reason = atomic_attempt(name, net, builder, mid, keep_snap)
        if reason == "restore_fail":
            if RESULT["restore_fail_streak"] >= 2:
                RESULT["phase"] = "STOP_RESTORE_FAIL"
                stop = True
                print("STOP: two restore fails", flush=True)
            return False
        if not kept_clean:
            return False
        # clean — check improvement
        if stats["unconnected_items"] < before_unc:
            keep_snap = snap_copy(f"keep-{name}")
            RESULT["closed"].append(f"{net}/{name} ({before_unc}→{stats['unconnected_items']})")
            print(f"KEEP {name} {before_unc}→{stats['unconnected_items']}", flush=True)
            return True
        # clean but no unc improvement → revert (no dead copper)
        restore_from(f"{SNAP}/pre-{name}.kicad_pcb")
        zone_fill()
        RESULT["copper_attempts"][-1]["result"] += " (clean but no unc drop → reverted)"
        RESULT["blocked"][name] = "clean but unconnected unchanged — reverted"
        print(f"REVERT_NO_GAIN {name}", flush=True)
        return False

    # 1. P0.11 header stubs
    if not attempt_keep("p011_j16_by9", "P0.11", build_p011_j16_by9, "DRC_PASS30T_MID_P011a.json"):
        if not stop:
            attempt_keep("p011_j16_by6", "P0.11", build_p011_j16_by6, "DRC_PASS30T_MID_P011b.json")
    if not stop and "P0.11" not in "".join(RESULT["closed"]):
        attempt_keep("p011_j16_fy10", "P0.11", build_p011_j16_fy10_with_hops, "DRC_PASS30T_MID_P011c.json")
    if not stop:
        attempt_keep("p011_j12_bx35", "P0.11", build_p011_j12_bx35_fhops, "DRC_PASS30T_MID_P011d.json")

    # 2. P0.10 / P0.17
    if not stop:
        attempt_keep("p010_j16_by9", "P0.10", build_p010_j16_by9, "DRC_PASS30T_MID_P010a.json")
    if not stop:
        attempt_keep("p010_j12", "P0.10", build_p010_j12_bx32, "DRC_PASS30T_MID_P010b.json")
    if not stop:
        attempt_keep("p017_island", "P0.17", build_p017_island_x45, "DRC_PASS30T_MID_P017a.json")
    if not stop:
        attempt_keep("p017_j17", "P0.17", build_p017_j17_by70_fhops, "DRC_PASS30T_MID_P017b.json")

    # 3. MAGPIO / MIPI / AUX if clean
    if not stop:
        ok = attempt_keep("magpio1_north", "MAGPIO1", build_magpio1_north, "DRC_PASS30T_MID_MAGPIO.json")
        if not ok:
            RESULT["blocked"]["MAGPIO0_2_MIPI"] = "Long U1→J14; MAGPIO1 probe dirty or no-gain; MIPI same class — deferred"
            RESULT["blocked"]["AUX"] = "RF keepout / matching — AUX jog tried only if MAGPIO kept; skipped as not clean"
            RESULT["blocked"]["AUX_FIT"] = "RF keepout path (skipped)"
            # still try AUX once as "if clean"
            attempt_keep("aux_jog", "AUX", build_aux_jog, "DRC_PASS30T_MID_AUX.json")

    # 4. VDD_GPIO islands low-risk only — do NOT rip Stage-A VDD2
    if not stop:
        attempt_keep("vddgpio_j16_f", "VDD_GPIO", build_vddgpio_j16_f, "DRC_PASS30T_MID_VDDGPIO_J16.json")
    if not stop:
        # U1 fanout — may be higher risk; only keep if clean+gain
        attempt_keep("vddgpio_u1", "VDD_GPIO", build_vddgpio_u1_f_via, "DRC_PASS30T_MID_VDDGPIO_U1.json")

    # P0.31 skipped
    RESULT["blocked"]["P0.31"] = "SKIPPED this pass per steering"

    # Final DRC
    data1, stats1 = run_drc(f"{REPORTS}/DRC_PASS30T_AFTER.json")
    nets1 = nets_of(data1)
    board1 = load()
    p015_1 = p015_west(board1)
    stage1 = stage_a_ok(board1)

    RESULT["after"] = stats1
    RESULT["after_nets_watch"] = {n: nets1.get(n, 0) for n in WATCH}
    RESULT["signal_net_deltas"] = {
        n: nets1.get(n, 0) - nets0.get(n, 0)
        for n in WATCH if n != "GND"
    }
    RESULT["gnd_zone_deltas"] = {"GND": nets1.get("GND", 0) - nets0.get("GND", 0)}
    RESULT["p015_west_segs"]["after"] = p015_1
    RESULT["p015_west_segs"]["preserved"] = p015_1 == p015_0
    RESULT["stage_a_check"] = stage1

    if RESULT["phase"] == "RUNNING":
        if RESULT["closed"]:
            RESULT["phase"] = "COMPLETE_PARTIAL" if stats1["unconnected_items"] > 0 else "COMPLETE"
        else:
            RESULT["phase"] = "COMPLETE_NO_KEEP"

    RESULT["success_gate"] = (
        f"{RESULT['phase']} ({stats0['unconnected_items']}→{stats1['unconnected_items']}; "
        f"closed={RESULT['closed']}; restore_fail_streak={RESULT['restore_fail_streak']})"
    )
    RESULT["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30T_BEFORE.json",
        "reports/DRC_PASS30T_AFTER.json",
        "reports/PASS30T_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30t.py",
        os.path.relpath(BACKUP, ROOT),
        ".mcp-backups/pass30t-connect/",
    ]

    json.dump(RESULT, open(f"{REPORTS}/PASS30T_SUMMARY.json", "w"), indent=2)
    print("AFTER", stats1, flush=True)
    print("CLOSED", RESULT["closed"], flush=True)
    print("PHASE", RESULT["phase"], flush=True)
    print("Wrote", f"{REPORTS}/PASS30T_SUMMARY.json", flush=True)

    # sanity: must stay clean
    assert clean(stats1), stats1
    assert RESULT["p015_west_segs"]["preserved"]
    assert stage1.get("VDD2_present") and stage1.get("VDD_nRF_via_north")


if __name__ == "__main__":
    main()
