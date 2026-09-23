#!/usr/bin/env python3
"""Pass30v — layout continue after pass30u KEEP (unconnected=67).

Steering (Hardware PM lock): duals P0.05/07/09/12/18/21/23/24 with NEW corridors,
then careful VDD_GPIO remaining islands if low-risk.
SKIP: P0.31, COEX0, P0.30 (just failed), exact failed P0.11/10/17 geometries from 30t.
Protect: Stage A, west wrap, RF/U3, P0.22 keep, P0.19 keep, all 30i–30u closed copper.
No placement. No Gerbers. Atomic restore; two fails in a row → STOP.
shorting=clearance=crossing=0 or revert.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30v-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
BACKUP = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30v-20260923-125645"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
VIA_D, VIA_DRILL = 0.6, 0.3

os.makedirs(SNAP, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

WATCH = [
    "P0.05", "P0.07", "P0.09", "P0.12", "P0.18", "P0.21", "P0.23", "P0.24",
    "P0.11", "P0.10", "P0.17", "P0.22", "P0.31", "P0.15", "P0.16", "P0.19",
    "P0.30", "P0.26", "P0.28",
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
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30v.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30v.json", out_path)
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
    "pass": "layout-pass30v",
    "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
    "phase": "RUNNING",
    "scope": (
        "NEW corridors duals P0.05/07/09/12/18/21/23/24 then careful VDD_GPIO. "
        "SKIP P0.31/COEX0/P0.30; avoid pass30t P0.11/P0.10/P0.17 exact geometries."
    ),
    "keep_stage_A": True,
    "keep_pass30i_30u": True,
    "keep_p022_pass30r": True,
    "keep_p019_pass30u": True,
    "no_gerbers": True,
    "hard_bans": [
        "P0.15 west wrap",
        "RF keepout",
        "U3/matching",
        "Stage A VDD2 / protected wraps",
        "pass30i-30u closed copper",
        "P0.22 pass30r keep",
        "P0.19 pass30u keep",
        "No placement",
        "P0.31 (skipped)",
        "COEX0 (skipped)",
        "P0.30 (skipped — just failed)",
        "Exact pass30t P0.11/P0.10/P0.17 geometries",
    ],
    "backup": os.path.relpath(BACKUP, ROOT),
    "closed": [],
    "blocked": {},
    "reverted_attempts": [],
    "copper_attempts": [],
    "restore_fail_streak": 0,
    "consecutive_fail_streak": 0,
    "skipped": ["P0.31", "COEX0", "P0.30"],
    "inventory_signal_excl_gnd_p031": {},
    "stop_reason": None,
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


# ========== NEW corridor builders ==========

def build_p005_j12_j9_fy77(board):
    """P0.05: J12.6 (18.7,76) ↔ J9.3 (116,13.08) — NEW F@y77.2 + east col@x114.3/B@x113.0.
    Parallel to P0.04@y78.8 / P0.06@y79.2; does not touch U1 stub (closes header dual)."""
    net = "P0.05"
    add_trk(board, net, 18.7, 76.0, 18.7, 77.2, W, B)
    add_trk(board, net, 18.7, 77.2, 22.5, 77.2, W, B)
    add_via(board, net, 22.5, 77.2)
    add_trk(board, net, 22.5, 77.2, 114.3, 77.2, W, F)
    add_trk(board, net, 114.3, 77.2, 114.3, 36.5, W, F)
    # drop to B before VDD_GPIO F@y31.08 / P0.22 F band
    add_via(board, net, 114.3, 36.5)
    add_trk(board, net, 114.3, 36.5, 113.0, 36.5, W, B)
    add_trk(board, net, 113.0, 36.5, 113.0, 13.2, W, B)
    add_trk(board, net, 113.0, 13.2, 116.0, 13.08, W, B)


def build_p007_j12_j9_fy778(board):
    """P0.07: J12.8 (23.78,76) ↔ J9.2 (116,10.54) — NEW F@y77.8 + east col@x115.2."""
    net = "P0.07"
    add_trk(board, net, 23.78, 76.0, 23.78, 77.8, W, B)
    add_trk(board, net, 23.78, 77.8, 26.0, 77.8, W, B)
    add_via(board, net, 26.0, 77.8)
    add_trk(board, net, 26.0, 77.8, 115.2, 77.8, W, F)
    add_trk(board, net, 115.2, 77.8, 115.2, 36.0, W, F)
    add_via(board, net, 115.2, 36.0)
    add_trk(board, net, 115.2, 36.0, 115.2, 10.7, W, B)
    add_trk(board, net, 115.2, 10.7, 116.0, 10.54, W, B)


def build_p009_j12_j16_fy765(board):
    """P0.09: J12.10 (28.86,76) ↔ J16.4 (108,15.62) — NEW F@y76.5 stub+highway to x108 B drop.
    Avoids pass30t P0.11 geometries."""
    net = "P0.09"
    add_trk(board, net, 28.86, 76.0, 28.86, 76.5, W, B)
    add_trk(board, net, 28.86, 76.5, 32.0, 76.5, W, B)
    add_via(board, net, 32.0, 76.5)
    add_trk(board, net, 32.0, 76.5, 108.0, 76.5, W, F)
    add_via(board, net, 108.0, 76.5)
    add_trk(board, net, 108.0, 76.5, 108.0, 55.0, W, B)
    # F-hop P0.06 B H@y55.5
    add_via(board, net, 108.0, 55.0)
    add_trk(board, net, 108.0, 55.0, 108.0, 53.5, W, F)
    add_via(board, net, 108.0, 53.5)
    add_trk(board, net, 108.0, 53.5, 108.0, 16.0, W, B)
    add_trk(board, net, 108.0, 16.0, 108.0, 15.62, W, B)


def build_p012_j12_j16_fy758(board):
    """P0.12: J12.13 (36.48,76) ↔ J16.3 (108,13.08) — NEW F@y75.8 (under pad row) + B@x109."""
    net = "P0.12"
    add_trk(board, net, 36.48, 76.0, 36.48, 75.8, W, B)
    add_trk(board, net, 36.48, 75.8, 40.0, 75.8, W, B)
    add_via(board, net, 40.0, 75.8)
    add_trk(board, net, 40.0, 75.8, 109.0, 75.8, W, F)
    add_via(board, net, 109.0, 75.8)
    add_trk(board, net, 109.0, 75.8, 109.0, 56.5, W, B)
    add_via(board, net, 109.0, 56.5)
    add_trk(board, net, 109.0, 56.5, 109.0, 54.5, W, F)  # hop P0.06@55.5 / P0.22 vicinity
    add_via(board, net, 109.0, 54.5)
    add_trk(board, net, 109.0, 54.5, 109.0, 13.2, W, B)
    add_trk(board, net, 109.0, 13.2, 108.0, 13.08, W, B)


def build_p018_j13_j17_by728(board):
    """P0.18: extend existing J18↔J13 island @B y72.8 east → J17.2 (108,28.54).
    NEW east extension + F-hops; does not alter existing west copper."""
    net = "P0.18"
    # from existing node (69.08, 72.8)
    add_trk(board, net, 69.08, 72.8, 104.0, 72.8, W, B)
    add_via(board, net, 104.0, 72.8)
    add_trk(board, net, 104.0, 72.8, 107.5, 72.8, W, F)  # hop P0.15@106
    add_via(board, net, 107.5, 72.8)
    add_trk(board, net, 107.5, 72.8, 108.0, 72.8, W, B)
    add_trk(board, net, 108.0, 72.8, 108.0, 56.0, W, B)
    add_via(board, net, 108.0, 56.0)
    add_trk(board, net, 108.0, 56.0, 108.0, 54.0, W, F)  # hop P0.06@55.5
    add_via(board, net, 108.0, 54.0)
    # continue B; F-hop P0.04 B stub ~y52.5/49.2 at x108.45
    add_trk(board, net, 108.0, 54.0, 108.0, 48.0, W, B)
    add_via(board, net, 108.0, 48.0)
    add_trk(board, net, 108.0, 48.0, 106.5, 48.0, W, F)
    add_trk(board, net, 106.5, 48.0, 106.5, 45.0, W, F)
    add_via(board, net, 106.5, 45.0)
    add_trk(board, net, 106.5, 45.0, 108.0, 45.0, W, B)
    add_trk(board, net, 108.0, 45.0, 108.0, 32.0, W, B)
    # F-hop VDD_GPIO B/F around y31.08
    add_via(board, net, 108.0, 32.0)
    add_trk(board, net, 108.0, 32.0, 106.5, 32.0, W, F)
    add_trk(board, net, 106.5, 32.0, 106.5, 28.54, W, F)
    add_trk(board, net, 106.5, 28.54, 108.0, 28.54, W, F)


def build_p021_j13_j10_by732(board):
    """P0.21: J13.6 (76.7,76) ↔ J10.1 (116,28) — NEW B@y73.2 + east col@x114.2
    Parallel to P0.22@y71.5/x109.2; NEW corridor only."""
    net = "P0.21"
    add_trk(board, net, 76.7, 76.0, 76.7, 73.2, W, B)
    add_trk(board, net, 76.7, 73.2, 104.0, 73.2, W, B)
    add_via(board, net, 104.0, 73.2)
    add_trk(board, net, 104.0, 73.2, 107.8, 73.2, W, F)  # hop P0.15@106 / VDD tip
    add_via(board, net, 107.8, 73.2)
    add_trk(board, net, 107.8, 73.2, 114.2, 73.2, W, B)
    add_trk(board, net, 114.2, 73.2, 114.2, 56.5, W, B)
    add_via(board, net, 114.2, 56.5)
    add_trk(board, net, 114.2, 56.5, 114.2, 54.2, W, F)  # hop P0.06 B@y55.5
    add_via(board, net, 114.2, 54.2)
    add_trk(board, net, 114.2, 54.2, 114.2, 37.0, W, B)
    add_via(board, net, 114.2, 37.0)
    # F down past VDD_GPIO F@31.08 / P0.22 attach, stay west of P0.06 F@115.5
    add_trk(board, net, 114.2, 37.0, 114.2, 28.0, W, F)
    add_trk(board, net, 114.2, 28.0, 116.0, 28.0, W, F)


def build_p023_j13_j10_by742(board):
    """P0.23: J13.8 (81.78,76) ↔ J10.3 (116,33.08) — NEW B@y74.2 + col@x115.0."""
    net = "P0.23"
    add_trk(board, net, 81.78, 76.0, 81.78, 74.2, W, B)
    add_trk(board, net, 81.78, 74.2, 104.0, 74.2, W, B)
    add_via(board, net, 104.0, 74.2)
    add_trk(board, net, 104.0, 74.2, 107.8, 74.2, W, F)
    add_via(board, net, 107.8, 74.2)
    add_trk(board, net, 107.8, 74.2, 115.0, 74.2, W, B)
    add_trk(board, net, 115.0, 74.2, 115.0, 56.5, W, B)
    add_via(board, net, 115.0, 56.5)
    add_trk(board, net, 115.0, 56.5, 115.0, 54.2, W, F)
    add_via(board, net, 115.0, 54.2)
    add_trk(board, net, 115.0, 54.2, 115.0, 37.5, W, B)
    add_via(board, net, 115.0, 37.5)
    add_trk(board, net, 115.0, 37.5, 115.0, 33.08, W, F)
    add_trk(board, net, 115.0, 33.08, 116.0, 33.08, W, F)


def build_p024_j13_j10_by690(board):
    """P0.24: J13.9 (84.32,76) ↔ J10.4 (116,35.62) — NEW B@y69.0 (north of P0.01@70.7)
    with F-hops over P0.22@71.5 and P0.01@70.7."""
    net = "P0.24"
    add_trk(board, net, 84.32, 76.0, 84.32, 72.0, W, B)
    add_via(board, net, 84.32, 72.0)
    add_trk(board, net, 84.32, 72.0, 84.32, 69.0, W, F)  # hop P0.22 H@71.5 / P0.01@70.7
    add_via(board, net, 84.32, 69.0)
    add_trk(board, net, 84.32, 69.0, 104.0, 69.0, W, B)
    add_via(board, net, 104.0, 69.0)
    add_trk(board, net, 104.0, 69.0, 107.8, 69.0, W, F)  # hop P0.15 + GND vias
    add_via(board, net, 107.8, 69.0)
    add_trk(board, net, 107.8, 69.0, 112.8, 69.0, W, B)
    add_trk(board, net, 112.8, 69.0, 112.8, 56.5, W, B)
    add_via(board, net, 112.8, 56.5)
    add_trk(board, net, 112.8, 56.5, 112.8, 54.2, W, F)
    add_via(board, net, 112.8, 54.2)
    add_trk(board, net, 112.8, 54.2, 112.8, 38.0, W, B)
    add_via(board, net, 112.8, 38.0)
    add_trk(board, net, 112.8, 38.0, 112.8, 35.62, W, F)
    add_trk(board, net, 112.8, 35.62, 116.0, 35.62, W, F)


def build_vddgpio_mid_bx78_b(board):
    """VDD_GPIO: stitch mid F island via(78,32) on B south-east to via(87.81,26) only
    (short low-risk; no north B to 70,14.8 which was denser)."""
    net = "VDD_GPIO"
    add_trk(board, net, 78.0, 32.0, 78.0, 26.0, 0.25, B)
    add_trk(board, net, 78.0, 26.0, 87.81, 26.0, 0.25, B)


def main():
    assert os.path.exists(BACKUP), BACKUP
    data0, stats0 = run_drc(f"{REPORTS}/DRC_PASS30V_BEFORE.json")
    nets0 = nets_of(data0)
    board0 = load()
    p015_0 = p015_west(board0)
    stage0 = stage_a_ok(board0)
    baseline = snap_copy("baseline_start")
    keep_snap = baseline

    inv = {n: c for n, c in sorted(nets0.items(), key=lambda kv: (-kv[1], kv[0]))
           if n not in ("GND", "P0.31")}
    RESULT["inventory_signal_excl_gnd_p031"] = inv
    RESULT["before"] = stats0
    RESULT["before_nets_watch"] = {n: nets0.get(n, 0) for n in WATCH}
    RESULT["p015_west_segs"] = {"before": p015_0}
    RESULT["stage_a_check"] = stage0

    print("BEFORE", stats0, flush=True)
    print("INVENTORY_SIGNAL", inv, flush=True)
    assert stats0["unconnected_items"] == 67, stats0
    assert clean(stats0), stats0

    stop = False
    fail_streak = 0

    def attempt_keep(name, net, builder, mid):
        nonlocal keep_snap, stop, fail_streak
        if stop:
            return False
        before_unc = run_drc(f"{REPORTS}/DRC_PASS30V_PROBE_TMP.json")[1]["unconnected_items"]
        kept_clean, stats, reason = atomic_attempt(name, net, builder, mid, keep_snap)
        if reason in ("dirty", "restore_fail", "build_error"):
            fail_streak += 1
            RESULT["consecutive_fail_streak"] = fail_streak
            RESULT["blocked"][name] = f"{reason}: {stats}"
            if fail_streak >= 2 or RESULT["restore_fail_streak"] >= 2:
                RESULT["phase"] = "STOP_TWO_FAILS" if fail_streak >= 2 else "STOP_RESTORE_FAIL"
                RESULT["stop_reason"] = (
                    f"two consecutive dirty fails"
                    if fail_streak >= 2
                    else "restore_fail_streak>=2"
                )
                stop = True
                print(f"STOP: fail_streak={fail_streak} restore_fail={RESULT['restore_fail_streak']}", flush=True)
            return False
        if stats["unconnected_items"] < before_unc:
            keep_snap = snap_copy(f"keep-{name}")
            RESULT["closed"].append(f"{net}/{name} ({before_unc}→{stats['unconnected_items']})")
            fail_streak = 0
            RESULT["consecutive_fail_streak"] = 0
            print(f"KEEP {name} {before_unc}→{stats['unconnected_items']}", flush=True)
            return True
        restore_from(f"{SNAP}/pre-{name}.kicad_pcb")
        zone_fill()
        RESULT["copper_attempts"][-1]["result"] += " (clean but no unc drop → reverted)"
        RESULT["blocked"][name] = "clean but unconnected unchanged — reverted"
        print(f"REVERT_NO_GAIN {name}", flush=True)
        return False

    attempts = [
        ("p005_j12_j9_fy77", "P0.05", build_p005_j12_j9_fy77, "DRC_PASS30V_MID_P005.json"),
        ("p007_j12_j9_fy778", "P0.07", build_p007_j12_j9_fy778, "DRC_PASS30V_MID_P007.json"),
        ("p009_j12_j16_fy765", "P0.09", build_p009_j12_j16_fy765, "DRC_PASS30V_MID_P009.json"),
        ("p012_j12_j16_fy758", "P0.12", build_p012_j12_j16_fy758, "DRC_PASS30V_MID_P012.json"),
        ("p018_j13_j17_by728", "P0.18", build_p018_j13_j17_by728, "DRC_PASS30V_MID_P018.json"),
        ("p021_j13_j10_by732", "P0.21", build_p021_j13_j10_by732, "DRC_PASS30V_MID_P021.json"),
        ("p023_j13_j10_by742", "P0.23", build_p023_j13_j10_by742, "DRC_PASS30V_MID_P023.json"),
        ("p024_j13_j10_by690", "P0.24", build_p024_j13_j10_by690, "DRC_PASS30V_MID_P024.json"),
        ("vddgpio_mid_bx78", "VDD_GPIO", build_vddgpio_mid_bx78_b, "DRC_PASS30V_MID_VDDGPIO.json"),
    ]

    for name, net, builder, mid in attempts:
        if stop:
            break
        attempt_keep(name, net, builder, mid)

    RESULT["blocked"]["P0.31"] = "SKIPPED this pass per steering"
    RESULT["blocked"]["COEX0"] = "SKIPPED this pass per steering"
    RESULT["blocked"]["P0.30"] = "SKIPPED this pass per steering (just failed in 30u)"
    RESULT["blocked"]["P0.11_P0.10_P0.17"] = (
        "Avoided exact pass30t failed geometries (by9/by6/fy10/bx35 / island / j17)"
    )

    data1, stats1 = run_drc(f"{REPORTS}/DRC_PASS30V_AFTER.json")
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
    RESULT["inventory_remaining_signal_excl_gnd_p031"] = {
        n: c for n, c in sorted(nets1.items(), key=lambda kv: (-kv[1], kv[0]))
        if n not in ("GND", "P0.31")
    }

    if RESULT["phase"] == "RUNNING":
        if RESULT["closed"]:
            RESULT["phase"] = "COMPLETE_PARTIAL" if stats1["unconnected_items"] > 0 else "COMPLETE"
        else:
            RESULT["phase"] = "COMPLETE_NO_KEEP"

    if RESULT["phase"] == "STOP_TWO_FAILS" and RESULT["closed"]:
        # still a partial keep board
        pass

    RESULT["success_gate"] = (
        f"{RESULT['phase']} ({stats0['unconnected_items']}→{stats1['unconnected_items']}; "
        f"closed={RESULT['closed']}; stop_reason={RESULT.get('stop_reason')}; "
        f"consecutive_fail_streak={RESULT['consecutive_fail_streak']}; "
        f"restore_fail_streak={RESULT['restore_fail_streak']})"
    )
    RESULT["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30V_BEFORE.json",
        "reports/DRC_PASS30V_AFTER.json",
        "reports/PASS30V_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30v.py",
        os.path.relpath(BACKUP, ROOT),
        ".mcp-backups/pass30v-connect/",
    ]

    json.dump(RESULT, open(f"{REPORTS}/PASS30V_SUMMARY.json", "w"), indent=2)
    print("AFTER", stats1, flush=True)
    print("CLOSED", RESULT["closed"], flush=True)
    print("PHASE", RESULT["phase"], flush=True)
    print("Wrote", f"{REPORTS}/PASS30V_SUMMARY.json", flush=True)

    assert clean(stats1), stats1
    assert RESULT["p015_west_segs"]["preserved"]
    assert stage1.get("VDD2_present") and stage1.get("VDD_nRF_via_north")


if __name__ == "__main__":
    main()
