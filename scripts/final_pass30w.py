#!/usr/bin/env python3
"""Pass30w — layout continue after pass30u KEEP (unconnected=67; pass30v no-keep).

Steering:
1) Careful VDD_GPIO remaining islands only — low-risk stubs/island joins.
   Do NOT rip Stage-A VDD2 or protected wraps.
2) Then SIM_* / COEX1 / MAGPIO (and MIPI/AUX if clean) SHORT stubs only.
Stop on two dirty fails. Keep clean partials.
Protect: west wrap, RF keepout, U3/matching, Stage A, P0.22 keep, P0.19 keep;
no placement; no Gerbers; shorting/clearance/crossing=0 or revert.
Skip P0.31 and saturated SE dual GPIO thrash (P0.05/07 etc).
IF nothing kept: do NOT start another copper pass; produce option E matrix.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30w-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
BACKUP = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30w-20260923-130755"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.18
WPOWER = 0.25
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
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30w.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30w.json", out_path)
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
    "pass": "layout-pass30w",
    "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
    "phase": "RUNNING",
    "scope": (
        "VDD_GPIO remaining islands low-risk stubs/joins only; then "
        "SIM_*/COEX1/MAGPIO (MIPI/AUX if clean) SHORT stubs only. "
        "SKIP P0.31 and saturated SE dual GPIO (P0.05/07 etc)."
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
        "SE dual GPIO thrash P0.05/07/09/12/18/21/23/24 (skipped — saturated)",
        "Exact pass30t P0.11/P0.10/P0.17 and VDD U1@x42 geometries",
    ],
    "backup": os.path.relpath(BACKUP, ROOT),
    "closed": [],
    "blocked": {},
    "reverted_attempts": [],
    "copper_attempts": [],
    "restore_fail_streak": 0,
    "consecutive_fail_streak": 0,
    "skipped": [
        "P0.31",
        "P0.05", "P0.07", "P0.09", "P0.12", "P0.18", "P0.21", "P0.23", "P0.24",
        "P0.30", "COEX0",
    ],
    "inventory_signal_excl_gnd_p031": {},
    "option_e_matrix_produced": False,
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


# ========== builders ==========

def build_vddgpio_u1_nw_fy345(board):
    """VDD_GPIO U1.12 → west island via@40.17,19.13 — NEW vs pass30t x=42 column.
    F north to y=34.5 (above COEX2 B@33.2), west to x=35.5 (west of COEX2 start@37.75),
    via, B south with F-hops over P0.13@y31 / SWDCLK@y24.8 / nRESET band, join via.
    Does NOT touch Stage-A VDD2 @y32 / x58.
    """
    net = "VDD_GPIO"
    add_trk(board, net, 44.0, 31.5, 44.0, 34.5, WPOWER, F)
    add_trk(board, net, 44.0, 34.5, 35.5, 34.5, WPOWER, F)
    add_via(board, net, 35.5, 34.5)
    # B south; F-hop P0.13 H@y31 (x32.2-42.75)
    add_trk(board, net, 35.5, 34.5, 35.5, 32.2, WPOWER, B)
    add_via(board, net, 35.5, 32.2)
    add_trk(board, net, 35.5, 32.2, 35.5, 29.5, WPOWER, F)  # hop P0.13
    add_via(board, net, 35.5, 29.5)
    add_trk(board, net, 35.5, 29.5, 35.5, 25.6, WPOWER, B)
    add_via(board, net, 35.5, 25.6)
    add_trk(board, net, 35.5, 25.6, 35.5, 23.5, WPOWER, F)  # hop SWDCLK@24.8
    add_via(board, net, 35.5, 23.5)
    add_trk(board, net, 35.5, 23.5, 35.5, 19.13, WPOWER, B)
    add_trk(board, net, 35.5, 19.13, 40.17, 19.13, WPOWER, B)


def build_vddgpio_mid_via87_fhops(board):
    """VDD_GPIO east via(87.81,26) → TP10 island (70,14.8).
    B south with F-hop over COEX2 H@y24.6; B west @y16.5 with F-hop over P0.15/VIN_F @x70-72.
    Avoids mid x=78 ENABLE/P0.08 squeeze (pass30v probe).
    """
    net = "VDD_GPIO"
    # existing via at 87.81,26
    add_trk(board, net, 87.81, 26.0, 87.81, 25.2, WPOWER, B)
    add_via(board, net, 87.81, 25.2)
    add_trk(board, net, 87.81, 25.2, 87.81, 23.5, WPOWER, F)  # hop COEX2@24.6
    add_via(board, net, 87.81, 23.5)
    add_trk(board, net, 87.81, 23.5, 87.81, 16.5, WPOWER, B)
    # dodge P0.01 via@86.14,19.13 and @88.2,15.2 — jog west then continue
    # actually column x=87.81 may skim P0.01 via@88.2,15.2 (dist 0.39) — jog to x=85.5
    add_trk(board, net, 87.81, 16.5, 85.5, 16.5, WPOWER, B)
    add_trk(board, net, 85.5, 16.5, 73.5, 16.5, WPOWER, B)
    add_via(board, net, 73.5, 16.5)
    add_trk(board, net, 73.5, 16.5, 73.5, 14.8, WPOWER, F)  # hop P0.15@15.35 / VIN_F
    add_via(board, net, 73.5, 14.8)
    add_trk(board, net, 73.5, 14.8, 70.0, 14.8, WPOWER, B)


def build_sim_clk_stub_extend(board):
    """SIM_CLK: only a SHORT stub from U1 via@31.25,23.1 south ~3mm — will not close
    long haul; used only if prior VDD kept and we probe stub class. Expect no-gain."""
    net = "SIM_CLK"
    add_trk(board, net, 31.25, 23.1, 31.25, 20.0, W, B)


def build_coex1_u1_stub(board):
    """COEX1: SHORT fanout stub from U1.92 only (~4mm) — cannot reach J15; expect no-gain."""
    net = "COEX1"
    add_trk(board, net, 38.25, 37.25, 38.25, 41.1, W, F)
    add_via(board, net, 38.25, 41.1)


def build_magpio0_u1_stub(board):
    """MAGPIO0: SHORT fanout like MAGPIO1/2 pattern west — still far from J14."""
    net = "MAGPIO0"
    add_trk(board, net, 28.0, 28.5, 25.6, 28.5, W, F)
    add_trk(board, net, 25.6, 28.5, 25.6, 24.5, W, F)
    add_via(board, net, 25.6, 24.5)


def unconnected_detail(data):
    """Build pad/refdes detail for option E matrix."""
    rows = []
    for u in data.get("unconnected_items", []):
        nets = set()
        pads = []
        descs = []
        for it in u.get("items", []):
            desc = it.get("description", "")
            descs.append(desc)
            for m in re.findall(r"\[([^\]]+)\]", desc):
                if m not in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                    nets.add(m)
            # Pad N [NET] of REF or PTH pad N [NET] of REF
            m = re.search(r"(?:PTH )?pad (\S+) \[([^\]]+)\] of (\S+)", desc, re.I)
            if m:
                pads.append(f"{m.group(3)}.{m.group(1)}")
            m2 = re.search(r"Pad (\S+) \[([^\]]+)\] of (\S+)", desc)
            if m2:
                pads.append(f"{m2.group(3)}.{m2.group(1)}")
        net = ",".join(sorted(nets)) if nets else "?"
        rows.append({
            "net": net,
            "pads_refdes": sorted(set(pads)),
            "items": descs[:4],
            "pos": [it.get("pos") for it in u.get("items", [])[:4]],
        })
    return rows


def classify_blocker(net, pads, items):
    """Heuristic blocker class + suggested next for option E."""
    n = net.split(",")[0] if net else "?"
    text = " ".join(items).upper()
    pads_s = " ".join(pads)

    if n == "GND":
        return "zone_island", "accept"
    if n == "P0.31":
        return "J13↔J11 SE saturated + under-mod", "place"
    if n in ("P0.05", "P0.07", "P0.09", "P0.12"):
        return "SE dual header / bottom-F highway saturated", "place"
    if n in ("P0.18", "P0.21", "P0.23", "P0.24", "P0.30"):
        return "SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep)", "place"
    if n in ("P0.10", "P0.11", "P0.17"):
        return "pass30t failed geometries; north/east dual still blocked", "place"
    if n == "VDD_GPIO":
        if "U1" in pads_s or "Pad 12" in text:
            return "U1.12 fanout vs GND via forest + P0.13/COEX2/Stage-A VDD2", "place"
        if any(x in text for x in ("78.0", "70.0", "14.8", "TP10", "TP13")):
            return "mid island (78,32)↔TP10 vs P0.08/COEX2/ENABLE/P0.15/VIN_F", "route"
        return "J18/J12 island ↔ east header; COEX0/P0.19/P0.08 bottom band", "route"
    if n.startswith("SIM_"):
        return "U1 SIM fanout ↔ U4 island (~40mm) through COEX2/ENABLE/VDD2", "route"
    if n in ("COEX1", "MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_SCLK", "MIPI_SDATA", "MIPI_VIO"):
        return "U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty", "place"
    if n in ("AUX", "AUX_FIT", "ANT_FIT"):
        return "RF keepout / matching / U3 region", "accept"
    if n == "COEX0":
        return "R4 stub ↔ U3/main; west-col GND via forest (pass30u dirty)", "route"
    if n in ("P0.19", "P0.22"):
        return "partial keep — remaining ratsnest to far header/stub", "accept"
    if n.startswith("P0."):
        return "GPIO corridor saturated / protected copper", "route"
    return "unknown / congested", "route"


def write_option_e_matrix(data, path_md, path_json):
    rows_raw = unconnected_detail(data)
    # collapse by net
    by_net = defaultdict(lambda: {"pads": set(), "count": 0, "items": []})
    for r in rows_raw:
        net = r["net"]
        by_net[net]["count"] += 1
        by_net[net]["pads"].update(r["pads_refdes"])
        by_net[net]["items"].extend(r["items"][:2])

    matrix = []
    for net, info in sorted(by_net.items(), key=lambda kv: (-kv[1]["count"], kv[0])):
        pads = sorted(info["pads"])
        blocker, nxt = classify_blocker(net, pads, info["items"])
        matrix.append({
            "net": net,
            "open_count": info["count"],
            "pads_refdes": pads,
            "likely_blocker_class": blocker,
            "suggested_next": nxt,  # route | place | accept
        })

    json.dump({"pass": "pass30w", "option": "E", "unconnected": len(rows_raw),
               "rows": matrix}, open(path_json, "w"), indent=2)

    lines = [
        "# Remaining Opens Matrix — Option E (pass30w handoff)",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  ",
        f"**Board:** pass30u KEEP (pass30w no copper keep)  ",
        f"**unconnected_items:** {len(rows_raw)}  ",
        f"**Gate:** copper passes exhausted for low-risk VDD_GPIO stubs + short SIM/COEX/MAGPIO class; "
        "do **not** start another copper pass without placement or co-route mandate.",
        "",
        "| Net | Opens | Pads / RefDes | Likely blocker class | Suggested next |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for m in matrix:
        pads = ", ".join(m["pads_refdes"]) if m["pads_refdes"] else "—(track/via island)"
        lines.append(
            f"| `{m['net']}` | {m['open_count']} | {pads} | {m['likely_blocker_class']} | **{m['suggested_next']}** |"
        )
    lines += [
        "",
        "## Suggested-next legend",
        "",
        "- **route** — still plausible with co-route / F-hop mandate (may need rip-restore of non-protected nets)",
        "- **place** — needs footprint nudge (J11/J10/J14/J8 or U1 fanout escape) before copper retry",
        "- **accept** — zone cosmetic, RF keepout, or partial-keep ratsnest; freeze or DFM waive",
        "",
        "## Pass30w attempt notes",
        "",
        "- VDD_GPIO U1 NW + mid via87 F-hop probes: see `PASS30W_SUMMARY.json`",
        "- SIM_*/COEX1/MAGPIO long-haul (~40–80 mm) are **not** short-stub class — deferred to E",
        "- Protected: Stage A VDD2, P0.15 west, P0.22, P0.19, RF/U3 — untouched",
        "",
    ]
    open(path_md, "w").write("\n".join(lines) + "\n")
    return matrix


def main():
    assert os.path.exists(BACKUP), BACKUP
    data0, stats0 = run_drc(f"{REPORTS}/DRC_PASS30W_BEFORE.json")
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
        before_unc = run_drc(f"{REPORTS}/DRC_PASS30W_PROBE_TMP.json")[1]["unconnected_items"]
        kept_clean, stats, reason = atomic_attempt(name, net, builder, mid, keep_snap)
        if reason in ("dirty", "restore_fail", "build_error"):
            fail_streak += 1
            RESULT["consecutive_fail_streak"] = fail_streak
            RESULT["blocked"][name] = f"{reason}: {stats}"
            if fail_streak >= 2 or RESULT["restore_fail_streak"] >= 2:
                RESULT["phase"] = "STOP_TWO_FAILS" if fail_streak >= 2 else "STOP_RESTORE_FAIL"
                RESULT["stop_reason"] = (
                    "two consecutive dirty fails"
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
        # no-gain does not count as dirty fail streak
        return False

    # ----- 1) VDD_GPIO low-risk -----
    attempts = [
        ("vddgpio_u1_nw_fy345", "VDD_GPIO", build_vddgpio_u1_nw_fy345, "DRC_PASS30W_MID_VDDGPIO_U1.json"),
        ("vddgpio_mid_via87_fhops", "VDD_GPIO", build_vddgpio_mid_via87_fhops, "DRC_PASS30W_MID_VDDGPIO_MID.json"),
    ]
    for name, net, builder, mid in attempts:
        if stop:
            break
        attempt_keep(name, net, builder, mid)

    # ----- 2) SHORT stubs only if not stopped -----
    # Only attempt if truly short; long-haul SIM/COEX1/MAGPIO documented as skipped.
    if not stop:
        # Probe one short stub class — expect no-gain; do not burn fail streak on no-gain.
        # If dirty, counts toward stop.
        attempt_keep("sim_clk_stub_extend", "SIM_CLK", build_sim_clk_stub_extend, "DRC_PASS30W_MID_SIMCLK.json")
    if not stop:
        attempt_keep("coex1_u1_stub", "COEX1", build_coex1_u1_stub, "DRC_PASS30W_MID_COEX1.json")
    if not stop:
        attempt_keep("magpio0_u1_stub", "MAGPIO0", build_magpio0_u1_stub, "DRC_PASS30W_MID_MAGPIO0.json")

    RESULT["blocked"]["P0.31"] = "SKIPPED this pass per steering"
    RESULT["blocked"]["SE_dual_GPIO"] = (
        "SKIPPED saturated SE dual thrash (P0.05/07/09/12/18/21/23/24) per steering"
    )
    RESULT["blocked"]["SIM_long_haul"] = (
        "SIM_* U1↔U4 ~40mm — not SHORT stub class; deferred to option E"
    )
    RESULT["blocked"]["COEX1_MAGPIO_MIPI_long"] = (
        "COEX1/MAGPIO/MIPI U1↔J14/J15 ~70–80mm — not SHORT stub class; deferred to option E"
    )
    RESULT["blocked"]["AUX_RF"] = "RF keepout / matching — skipped unless clean short (none)"
    RESULT["blocked"]["Stage_A_VDD2"] = "NOT ripped — protected"

    data1, stats1 = run_drc(f"{REPORTS}/DRC_PASS30W_AFTER.json")
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

    # Option E if nothing kept
    if not RESULT["closed"]:
        matrix = write_option_e_matrix(
            data1,
            f"{REPORTS}/REMAINING_OPENS_MATRIX.md",
            f"{REPORTS}/REMAINING_OPENS_MATRIX.json",
        )
        RESULT["option_e_matrix_produced"] = True
        RESULT["option_e_rows"] = len(matrix)
        RESULT["e_handoff"] = True
        print(f"OPTION_E matrix rows={len(matrix)}", flush=True)

    RESULT["success_gate"] = (
        f"{RESULT['phase']} ({stats0['unconnected_items']}→{stats1['unconnected_items']}; "
        f"closed={RESULT['closed']}; stop_reason={RESULT.get('stop_reason')}; "
        f"consecutive_fail_streak={RESULT['consecutive_fail_streak']}; "
        f"restore_fail_streak={RESULT['restore_fail_streak']}; "
        f"option_e={RESULT['option_e_matrix_produced']})"
    )
    RESULT["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30W_BEFORE.json",
        "reports/DRC_PASS30W_AFTER.json",
        "reports/PASS30W_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30w.py",
        os.path.relpath(BACKUP, ROOT),
        ".mcp-backups/pass30w-connect/",
    ]
    if RESULT["option_e_matrix_produced"]:
        RESULT["files_touched"] += [
            "reports/REMAINING_OPENS_MATRIX.md",
            "reports/REMAINING_OPENS_MATRIX.json",
        ]

    json.dump(RESULT, open(f"{REPORTS}/PASS30W_SUMMARY.json", "w"), indent=2)
    print("AFTER", stats1, flush=True)
    print("CLOSED", RESULT["closed"], flush=True)
    print("PHASE", RESULT["phase"], flush=True)
    print("Wrote", f"{REPORTS}/PASS30W_SUMMARY.json", flush=True)

    assert clean(stats1), stats1
    assert RESULT["p015_west_segs"]["preserved"]
    assert stage1.get("VDD2_present") and stage1.get("VDD_nRF_via_north")


if __name__ == "__main__":
    main()
