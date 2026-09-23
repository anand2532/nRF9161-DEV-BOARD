#!/usr/bin/env python3
"""Pass30u — layout continue after pass30t KEEP (unconnected=68).

Steering: inventory signal opens (excl GND zone + skip P0.31); NEW corridors only;
avoid exact failed P0.11/P0.10/P0.17 geometries from pass30t; stop after two fails
in a row; protect Stage A, west wrap, RF/U3, P0.22 keep, 30i–30t copper.
No placement. No Gerbers. shorting=clearance=crossing=0 or revert.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30u-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
BACKUP = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30u-20260923-125307"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
VIA_D, VIA_DRILL = 0.6, 0.3

os.makedirs(SNAP, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

WATCH = [
    "P0.11", "P0.10", "P0.17", "P0.22", "P0.31", "P0.15", "P0.16", "P0.18",
    "P0.19", "P0.30", "P0.24", "P0.23", "P0.21", "P0.26", "P0.28",
    "MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_SCLK", "MIPI_SDATA", "MIPI_VIO",
    "AUX", "AUX_FIT", "VDD_GPIO", "VDD2", "VDD_nRF", "GND", "P0.01", "P0.08",
    "COEX0", "COEX1", "SIM_RST", "SIM_CLK", "SIM_IO", "SIM_1V8",
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
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30u.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30u.json", out_path)
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


RESULT = {
    "pass": "layout-pass30u",
    "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
    "phase": "RUNNING",
    "scope": (
        "NEW corridors: P0.19 J18↔J13 B@y64 F-hop; COEX0 B west-col; "
        "east header stitches if clean; VDD_GPIO mid if clean. "
        "SKIP P0.31; avoid pass30t P0.11/P0.10/P0.17 exact geometries."
    ),
    "keep_stage_A": True,
    "keep_pass30i_30t": True,
    "keep_p022_pass30r": True,
    "no_gerbers": True,
    "hard_bans": [
        "P0.15 west wrap",
        "RF keepout",
        "U3/matching",
        "Stage A VDD2 / protected wraps",
        "pass30i-30t closed copper",
        "P0.22 pass30r keep",
        "No placement",
        "P0.31 (skipped this pass)",
        "Exact pass30t P0.11/P0.10/P0.17 geometries",
    ],
    "backup": os.path.relpath(BACKUP, ROOT),
    "closed": [],
    "blocked": {},
    "reverted_attempts": [],
    "copper_attempts": [],
    "restore_fail_streak": 0,
    "consecutive_fail_streak": 0,
    "skipped": ["P0.31"],
    "inventory_signal_excl_gnd_p031": {},
}


def atomic_attempt(name, net, build_fn, mid_drc_name, baseline_path):
    pre = f"{SNAP}/pre-{name}.kicad_pcb"
    shutil.copy2(BOARD, pre)
    board = load()
    try:
        build_fn(board)
    except Exception as e:
        restore_from(pre)
        RESULT["reverted_attempts"].append({"net": net, "id": name, "reason": f"build_error:{e}"})
        RESULT["copper_attempts"].append({"id": name, "net": net, "result": f"build_error:{e}"})
        return False, None, "build_error"
    save(board)
    zone_fill()
    data, stats = run_drc(f"{REPORTS}/{mid_drc_name}")
    if clean(stats):
        RESULT["copper_attempts"].append({"id": name, "net": net, "result": f"CLEAN {stats}"})
        return True, stats, "clean"
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
        "result": (
            f"dirty shorting={stats['shorting_items']} "
            f"clearance={stats['clearance']} crossing={stats['tracks_crossing']}"
        ),
    })
    return False, stats, "dirty"


# ========== NEW corridor builders (not pass30t P0.11/10/17 geometries) ==========

def build_p019_j18_j13_by64(board):
    """P0.19: J18.7 (53.24,62) ↔ J13.4 (71.62,76) via B@y64 + F-hop over P0.08@x65.2."""
    net = "P0.19"
    # PTH pads → B
    add_trk(board, net, 53.24, 62.0, 53.24, 64.0, W, B)
    add_trk(board, net, 53.24, 64.0, 64.0, 64.0, W, B)
    add_via(board, net, 64.0, 64.0)
    add_trk(board, net, 64.0, 64.0, 66.4, 64.0, W, F)
    add_via(board, net, 66.4, 64.0)
    add_trk(board, net, 66.4, 64.0, 71.62, 64.0, W, B)
    add_trk(board, net, 71.62, 64.0, 71.62, 76.0, W, B)


def build_coex0_b_westcol(board):
    """COEX0: via(31.11,22) → B@x29.8 south with F-hops over GND vias / P0.13 → via(33,43)."""
    net = "COEX0"
    # start at existing via 31.11,22
    add_trk(board, net, 31.11, 22.0, 29.8, 22.0, W, B)
    add_trk(board, net, 29.8, 22.0, 29.8, 27.5, W, B)
    # F-hop GND via forest ~y29-35
    add_via(board, net, 29.8, 27.5)
    add_trk(board, net, 29.8, 27.5, 29.8, 36.5, W, F)
    add_via(board, net, 29.8, 36.5)
    add_trk(board, net, 29.8, 36.5, 29.8, 40.2, W, B)
    # F-hop P0.13 H@y41 / approach existing via 33,43
    add_via(board, net, 29.8, 40.2)
    add_trk(board, net, 29.8, 40.2, 29.8, 42.5, W, F)
    add_trk(board, net, 29.8, 42.5, 33.0, 42.5, W, F)
    add_trk(board, net, 33.0, 42.5, 33.0, 43.0, W, F)
    # via 33,43 already exists on COEX0 — F track lands on it


def build_p030_j13_j11_east(board):
    """P0.30: J13.15 (99.56,76) ↔ J11.1 (116,46) — B south band + F-hops over P0.15/VDD_GPIO/P0.06."""
    net = "P0.30"
    add_trk(board, net, 99.56, 76.0, 99.56, 73.8, W, B)
    add_trk(board, net, 99.56, 73.8, 104.0, 73.8, W, B)
    # F-hop P0.15 V@x106 and VDD_GPIO V@107.18 — jog south of VDD stub tip
    add_via(board, net, 104.0, 73.8)
    add_trk(board, net, 104.0, 73.8, 104.0, 72.5, W, F)
    add_trk(board, net, 104.0, 72.5, 108.5, 72.5, W, F)
    add_via(board, net, 108.5, 72.5)
    add_trk(board, net, 108.5, 72.5, 112.8, 72.5, W, B)
    add_trk(board, net, 112.8, 72.5, 112.8, 56.2, W, B)
    # F-hop P0.06 H@y55.5
    add_via(board, net, 112.8, 56.2)
    add_trk(board, net, 112.8, 56.2, 112.8, 54.0, W, F)
    add_via(board, net, 112.8, 54.0)
    # F-hop VDD_GPIO H@y51.08 — stay F through then to pad
    add_trk(board, net, 112.8, 54.0, 112.8, 49.5, W, F)
    add_trk(board, net, 112.8, 49.5, 112.8, 46.0, W, F)
    add_trk(board, net, 112.8, 46.0, 116.0, 46.0, W, F)


def build_vddgpio_mid_fx84(board):
    """VDD_GPIO: mid F island via(78,32) → east then B drop away from VIN_F/P0.15 — toward via(87.81,26)."""
    net = "VDD_GPIO"
    # via 78,32 already on island; via 87.81,26 also VDD_GPIO — if already same island, try north B stitch
    # Connect B network at (70,14.8) via east column x=84 F-hop then B west under VIN_F gap
    add_trk(board, net, 78.0, 32.0, 78.0, 26.0, 0.25, B)
    add_trk(board, net, 78.0, 26.0, 87.81, 26.0, 0.25, B)
    # 87.81,26 already has via — now from there B north-west carefully
    add_trk(board, net, 87.81, 26.0, 87.81, 14.8, 0.25, B)
    add_trk(board, net, 87.81, 14.8, 70.0, 14.8, 0.25, B)


def main():
    assert os.path.exists(BACKUP), BACKUP
    data0, stats0 = run_drc(f"{REPORTS}/DRC_PASS30U_BEFORE.json")
    nets0 = nets_of(data0)
    board0 = load()
    p015_0 = p015_west(board0)
    stage0 = stage_a_ok(board0)
    baseline = snap_copy("baseline_start")
    keep_snap = baseline

    # inventory signal opens
    inv = {n: c for n, c in sorted(nets0.items(), key=lambda kv: (-kv[1], kv[0]))
           if n not in ("GND", "P0.31")}
    RESULT["inventory_signal_excl_gnd_p031"] = inv
    RESULT["before"] = stats0
    RESULT["before_nets_watch"] = {n: nets0.get(n, 0) for n in WATCH}
    RESULT["p015_west_segs"] = {"before": p015_0}
    RESULT["stage_a_check"] = stage0

    print("BEFORE", stats0, flush=True)
    print("INVENTORY_SIGNAL", inv, flush=True)
    assert stats0["unconnected_items"] == 68, stats0
    assert clean(stats0), stats0

    stop = False
    fail_streak = 0

    def attempt_keep(name, net, builder, mid):
        nonlocal keep_snap, stop, fail_streak
        if stop:
            return False
        before_unc = run_drc(f"{REPORTS}/DRC_PASS30U_PROBE_TMP.json")[1]["unconnected_items"]
        kept_clean, stats, reason = atomic_attempt(name, net, builder, mid, keep_snap)
        if reason in ("dirty", "restore_fail", "build_error"):
            fail_streak += 1
            RESULT["consecutive_fail_streak"] = fail_streak
            RESULT["blocked"][name] = f"{reason}: {stats}"
            if fail_streak >= 2 or RESULT["restore_fail_streak"] >= 2:
                RESULT["phase"] = "STOP_TWO_FAILS" if fail_streak >= 2 else "STOP_RESTORE_FAIL"
                stop = True
                print(f"STOP: fail_streak={fail_streak} restore_fail={RESULT['restore_fail_streak']}", flush=True)
            return False
        # clean
        if stats["unconnected_items"] < before_unc:
            keep_snap = snap_copy(f"keep-{name}")
            RESULT["closed"].append(f"{net}/{name} ({before_unc}→{stats['unconnected_items']})")
            fail_streak = 0
            RESULT["consecutive_fail_streak"] = 0
            print(f"KEEP {name} {before_unc}→{stats['unconnected_items']}", flush=True)
            return True
        # clean but no unc improvement → revert
        restore_from(f"{SNAP}/pre-{name}.kicad_pcb")
        zone_fill()
        RESULT["copper_attempts"][-1]["result"] += " (clean but no unc drop → reverted)"
        RESULT["blocked"][name] = "clean but unconnected unchanged — reverted"
        # no-gain does not count as hard fail streak
        print(f"REVERT_NO_GAIN {name}", flush=True)
        return False

    # 1. P0.19 header stitch (NEW)
    attempt_keep("p019_j18_j13_by64", "P0.19", build_p019_j18_j13_by64, "DRC_PASS30U_MID_P019.json")

    # 2. COEX0 west-col (NEW)
    if not stop:
        attempt_keep("coex0_b_westcol", "COEX0", build_coex0_b_westcol, "DRC_PASS30U_MID_COEX0.json")

    # 3. P0.30 east stitch (NEW) — only if fail streak allows
    if not stop:
        attempt_keep("p030_j13_j11_east", "P0.30", build_p030_j13_j11_east, "DRC_PASS30U_MID_P030.json")

    # 4. VDD_GPIO mid (NEW) — only if still running
    if not stop:
        attempt_keep("vddgpio_mid_bx78", "VDD_GPIO", build_vddgpio_mid_fx84, "DRC_PASS30U_MID_VDDGPIO.json")

    RESULT["blocked"]["P0.31"] = "SKIPPED this pass per steering"
    RESULT["blocked"]["P0.11_P0.10_P0.17"] = (
        "Avoided exact pass30t failed geometries (by9/by6/fy10/bx35 / island / j17)"
    )

    data1, stats1 = run_drc(f"{REPORTS}/DRC_PASS30U_AFTER.json")
    nets1 = nets_of(data1)
    board1 = load()
    p015_1 = p015_west(board1)
    stage1 = stage_a_ok(board1)

    RESULT["after"] = stats1
    RESULT["after_nets_watch"] = {n: nets1.get(n, 0) for n in WATCH}
    RESULT["signal_net_deltas"] = {
        n: nets1.get(n, 0) - nets0.get(n, 0) for n in WATCH if n != "GND"
    }
    RESULT["gnd_zone_deltas"] = {"GND": nets1.get("GND", 0) - nets0.get("GND", 0)}
    RESULT["p015_west_segs"]["after"] = p015_1
    RESULT["p015_west_segs"]["preserved"] = p015_1 == p015_0
    RESULT["stage_a_check"] = stage1
    RESULT["timestamp_ist"] = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    if RESULT["phase"] == "RUNNING":
        if RESULT["closed"]:
            RESULT["phase"] = "COMPLETE_PARTIAL" if stats1["unconnected_items"] > 0 else "COMPLETE"
        else:
            RESULT["phase"] = "COMPLETE_NO_KEEP"

    RESULT["success_gate"] = (
        f"{RESULT['phase']} ({stats0['unconnected_items']}→{stats1['unconnected_items']}; "
        f"closed={RESULT['closed']}; consecutive_fail_streak={RESULT['consecutive_fail_streak']}; "
        f"restore_fail_streak={RESULT['restore_fail_streak']})"
    )
    RESULT["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30U_BEFORE.json",
        "reports/DRC_PASS30U_AFTER.json",
        "reports/PASS30U_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30u.py",
        os.path.relpath(BACKUP, ROOT),
        ".mcp-backups/pass30u-connect/",
    ]

    json.dump(RESULT, open(f"{REPORTS}/PASS30U_SUMMARY.json", "w"), indent=2)
    print("AFTER", stats1, flush=True)
    print("CLOSED", RESULT["closed"], flush=True)
    print("PHASE", RESULT["phase"], flush=True)
    print("Wrote", f"{REPORTS}/PASS30U_SUMMARY.json", flush=True)

    assert clean(stats1), stats1
    assert RESULT["p015_west_segs"]["preserved"]
    assert stage1.get("VDD2_present") and stage1.get("VDD_nRF_via_north")


if __name__ == "__main__":
    main()
