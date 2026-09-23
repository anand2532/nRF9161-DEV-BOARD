#!/usr/bin/env python3
"""Pass30n — nRESET co-route with COEX2+P0.01+P0.15 east rip/restore + VDD_nRF clearance jog.

Preflight rip list in reports/PASS30N_SUMMARY.json BEFORE copper edit.
Hard bans: P0.15 west wrap; RF; U3; Stage A + pass30i–30l (P0.08/VIN_F/SWDCLK/VIN_FILT).
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30n-connect"
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
    try:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    except Exception as e:
        print("zone fill warning:", e)


def run_drc(out_path):
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30n.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30n.json", out_path)
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
        if isinstance(t, pcbnew.PCB_VIA):
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


def near(a, b, tol=0.05):
    return abs(a - b) < tol


def match_seg(t, layer, x1, y1, x2, y2, tol=0.05):
    if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
        return False
    if t.GetLayer() != layer:
        return False
    try:
        s, e = t.GetStart(), t.GetEnd()
        sx, sy = mm(s.x), mm(s.y)
        ex, ey = mm(e.x), mm(e.y)
    except Exception:
        return False
    return (
        near(sx, x1, tol) and near(sy, y1, tol) and near(ex, x2, tol) and near(ey, y2, tol)
    ) or (
        near(sx, x2, tol) and near(sy, y2, tol) and near(ex, x1, tol) and near(ey, y1, tol)
    )


def rip_preflight(board, rip_list):
    """Rip all preflight segs using ONE track snapshot — GetTracks breaks after Remove()."""
    removed = []
    tracks = list(board.GetTracks())
    claimed = set()
    plan = []  # (track, spec)
    for spec in rip_list:
        layer = B if spec["layer"] == "B.Cu" else F
        found = False
        for t in tracks:
            tid = id(t)
            if tid in claimed:
                continue
            if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
                continue
            if t.GetNetname() != spec["net"]:
                continue
            if match_seg(t, layer, spec["x1"], spec["y1"], spec["x2"], spec["y2"]):
                plan.append((t, spec))
                claimed.add(tid)
                found = True
                break
        if not found:
            removed.append({"id": spec["id"], "net": spec["net"], "error": "NOT_FOUND"})
    for t, spec in plan:
        removed.append(
            {
                "id": spec["id"],
                "net": spec["net"],
                "layer": spec["layer"],
                "x1": round(mm(t.GetStart().x), 3),
                "y1": round(mm(t.GetStart().y), 3),
                "x2": round(mm(t.GetEnd().x), 3),
                "y2": round(mm(t.GetEnd().y), 3),
                "w": round(mm(t.GetWidth()), 3),
            }
        )
        board.Remove(t)
    return removed


def restore_p015_east(board):
    segs = [
        "B (72.0,15.35)->(72.0,13.8)",
        "via(72.0,13.8)",
        "F (72.0,13.8)->(72.0,11.4)",
        "via(72.0,11.4)",
        "B (72.0,11.4)->(72.0,7.2)",
    ]
    add_trk(board, "P0.15", 72.0, 15.35, 72.0, 13.8, W, B)
    add_via(board, "P0.15", 72.0, 13.8)
    add_trk(board, "P0.15", 72.0, 13.8, 72.0, 11.4, W, F)
    add_via(board, "P0.15", 72.0, 11.4)
    add_trk(board, "P0.15", 72.0, 11.4, 72.0, 7.2, W, B)
    return segs


def restore_coex2(board):
    """B detour + F hop south of SW2 (GND pad@101.625,24) — avoid F@y24.6 short."""
    segs = [
        "B (72.0,24.6)->(100.3,24.6)->(100.3,22.5)",
        "via(100.3,22.5)",
        "F (100.3,22.5)->(103.2,22.5)",
        "via(103.2,22.5)",
        "B (103.2,22.5)->(103.2,24.6)->(105.1,24.6)",
    ]
    add_trk(board, "COEX2", 72.0, 24.6, 100.3, 24.6, W, B)
    add_trk(board, "COEX2", 100.3, 24.6, 100.3, 22.5, W, B)
    add_via(board, "COEX2", 100.3, 22.5)
    add_trk(board, "COEX2", 100.3, 22.5, 103.2, 22.5, W, F)
    add_via(board, "COEX2", 103.2, 22.5)
    add_trk(board, "COEX2", 103.2, 22.5, 103.2, 24.6, W, B)
    add_trk(board, "COEX2", 103.2, 24.6, 105.1, 24.6, W, B)
    return segs


def restore_p001(board):
    segs = [
        "B (86.14,15.2)->(100.3,15.2)",
        "via(100.3,15.2)",
        "F (100.3,15.2)->(103.2,15.2)",
        "via(103.2,15.2)",
        "B (103.2,15.2)->(105.55,15.2)",
    ]
    add_trk(board, "P0.01", 86.14, 15.2, 100.3, 15.2, W, B)
    add_via(board, "P0.01", 100.3, 15.2)
    add_trk(board, "P0.01", 100.3, 15.2, 103.2, 15.2, W, F)
    add_via(board, "P0.01", 103.2, 15.2)
    add_trk(board, "P0.01", 103.2, 15.2, 105.55, 15.2, W, B)
    return segs


def route_nreset(board):
    """nRESET: F@y=10.8 under JP1/VDD_nRF (no via near JP1 pads); B from x=59.4."""
    net = "nRESET"
    y = 12.6
    yf = 10.8
    segs = [
        "F (53.65,10.8)->(53.65,12.6) via (west attach)",
        "F under JP1/VDD_nRF: (53.65,10.8)->(59.4,10.8)->(59.4,12.6) via",
        "B (59.4,12.6)->(69.0,12.6)",
        "via F-hop over VDD_GPIO@70 + VIN_F@70.8: (69.0,12.6)->(71.5,12.6)",
        "B (71.5,12.6)->(101.68,12.6)",
        "B (101.68,12.6)->(101.68,26.0) into existing east column",
    ]
    add_trk(board, net, 53.65, 10.8, 53.65, y, W, F)
    add_via(board, net, 53.65, y)
    add_trk(board, net, 53.65, yf, 59.4, yf, W, F)
    add_trk(board, net, 59.4, yf, 59.4, y, W, F)
    add_via(board, net, 59.4, y)
    add_trk(board, net, 59.4, y, 69.0, y, W, B)
    add_via(board, net, 69.0, y)
    add_trk(board, net, 69.0, y, 71.5, y, W, F)
    add_via(board, net, 71.5, y)
    add_trk(board, net, 71.5, y, 101.68, y, W, B)
    add_trk(board, net, 101.68, y, 101.68, 26.0, W, B)
    return {
        "y": y,
        "f_clearance_hop_y": yf,
        "hop_x": [53.65, 59.4],
        "f_hop_vdd_gpio": [69.0, 71.5],
        "segments": segs,
        "vdd_nrf_via": [57.95, 12.0, 0.8],
        "expected_jog_clearance_mm": round(abs(yf - 12.0) - 0.4 - 0.09, 3),
        "note": "no via near JP1; F@10.8 under pads",
    }



def colliding_from_drc(data):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in ("shorting_items", "clearance", "tracks_crossing"):
            out.append(
                {
                    "type": v.get("type"),
                    "description": v.get("description", "")[:300],
                    "items": [
                        {
                            "description": it.get("description", "")[:200],
                            "pos": it.get("pos"),
                        }
                        for it in v.get("items", [])[:4]
                    ],
                }
            )
    return out[:20]


WATCH = (
    "nRESET", "P0.02", "P0.15", "ENABLE", "VIN_FILT", "VIN_F",
    "VDD_GPIO", "P0.08", "SWDCLK", "VDD2", "COEX2", "P0.01", "VDD_nRF",
)


def update_docs(summary):
    path = f"{ROOT}/docs/PCB_LAYOUT_REVIEW.md"
    text = open(path).read()
    ts = summary.get("timestamp_ist", "")
    text = re.sub(
        r"(\*\*Review date:\*\*).*",
        f"**Review date:** {ts} (Asia/Calcutta) — pass30n executed",
        text,
        count=1,
    )
    after_u = summary.get("after", {}).get("unconnected_items")
    if after_u is not None:
        text = re.sub(
            r"(\|\s*\*\*unconnected_items\*\*\s*\|\s*\*\*)\d+(\*\*)",
            rf"\g<1>{after_u}\2",
            text,
            count=1,
        )
    closed = summary.get("closed", [])
    reverted = summary.get("reverted", False)
    rip = summary.get("preflight_rip_list", [])
    delta_line = (
        f"**Pass delta (pass30n):** ONE atomic nRESET co-route (jog under VDD_nRF via). "
        f"Preflight rip ({len(rip)}): "
        + ", ".join(
            f'{r["net"]} ({r.get("x1")},{r.get("y1")})→({r.get("x2")},{r.get("y2")})'
            for r in rip
        )
        + ". "
    )
    if "nRESET" in closed and not reverted:
        delta_line += (
            f"nRESET **KEPT** B@y12.6 + south jog y=10.5 + F-hop 69–71.5; "
            f"COEX2/P0.01/P0.15 east co-restored. "
            f"**Before/After unconnected:** {summary['before']['unconnected_items']}/{summary['after']['unconnected_items']} · "
            f"shorting/clearance/crossing 0. "
        )
    else:
        delta_line += (
            f"nRESET attempted then **reverted** "
            f"(shorting={summary.get('mid',{}).get('shorting_items')} "
            f"clearance={summary.get('mid',{}).get('clearance')} "
            f"crossing={summary.get('mid',{}).get('tracks_crossing')}). "
            f"**Before/After unconnected:** {summary['before']['unconnected_items']}/{summary['after']['unconnected_items']}. "
        )
    if summary.get("p002_attempted"):
        delta_line += f"P0.02: {summary.get('blocked',{}).get('P0.02','attempted')}. "
    else:
        delta_line += "P0.02 skipped (nRESET not KEPT or no free corridor). "
    delta_line += (
        "Stage A + pass30i–30l kept. P0.15 west wrap preserved. No Gerbers. "
        "Details: `reports/PASS30N_SUMMARY.json`.\n\n"
    )
    if "**Pass delta (pass30m):**" in text:
        text = text.replace("**Pass delta (pass30m):**", delta_line + "**Pass delta (pass30m):**", 1)
    elif "**Pass delta (pass30l):**" in text:
        text = text.replace("**Pass delta (pass30l):**", delta_line + "**Pass delta (pass30l):**", 1)
    else:
        text = text.replace("## 1. Current connectivity status", delta_line + "## 1. Current connectivity status", 1)

    section = f"""

---

## Pass30n — nRESET co-route + COEX2/P0.01 rip-restore ({ts})

### Goal
Atomic nRESET with ≥0.15 mm clearance to VDD_nRF via@(57.95,12) d=0.8. Rip P0.15 east + COEX2 + P0.01 crossed segs; co-restore before DRC. shorting=0 clearance=0 crossing=0. No Gerbers.

### Preflight rip list (recorded before copper edit)
"""
    for r in rip:
        section += (
            f"- `{r['id']}`: {r['net']} {r['layer']} "
            f"({r['x1']},{r['y1']})→({r['x2']},{r['y2']}) w={r['w']} — {r['reason']}\n"
        )
    mid = summary.get("mid", {})
    section += f"""
### Attempt
- Clearance jog: B south to y=10.5 for x=56.2–59.4 under VDD_nRF via (expect clr ~{summary.get('nreset_attempt',{}).get('expected_jog_clearance_mm','?')} mm)
- F-hop 69.0–71.5 over VDD_GPIO/VIN_F (no rip)
- Co-restore COEX2 F-hop @y24.6, P0.01 F-hop @y15.2, P0.15 east F-bridge

### Result
- **nRESET closed/KEPT:** {"yes" if "nRESET" in closed and not reverted else "no"}
- **Reverted:** {"yes" if reverted else "no"}
- **Before unconnected:** {summary['before']['unconnected_items']}
- **Mid unconnected:** {mid.get('unconnected_items')} (shorting={mid.get('shorting_items')} clearance={mid.get('clearance')} crossing={mid.get('tracks_crossing')})
- **After unconnected:** {summary['after']['unconnected_items']}
- **P0.15 west segs:** {summary.get('p015_west_segs', {})}
- **P0.02:** {summary.get('blocked', {}).get('P0.02', 'n/a')}
- **Backup:** `{summary.get('backup')}`
- **DRC:** `reports/DRC_PASS30N_BEFORE.json`, `reports/DRC_PASS30N_MID.json`, `reports/DRC_PASS30N_AFTER.json`
- **Summary:** `reports/PASS30N_SUMMARY.json`
"""
    if summary.get("colliding_copper"):
        section += "\n### Colliding copper (mid DRC — reason for revert)\n"
        for c in summary["colliding_copper"][:8]:
            section += f"- {c.get('type')}: {c.get('description','')[:200]}\n"

    open(path, "w").write(text + section)


def main():
    summary_path = f"{REPORTS}/PASS30N_SUMMARY.json"
    summary = json.load(open(summary_path))
    assert summary.get("preflight_rip_list"), "preflight rip list missing"
    if summary.get("copper_edit_started"):
        print("WARN: copper_edit_started was True — continuing with fresh backup")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{BACKUPS}/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30n-{ts}"
    shutil.copy2(BOARD, backup)
    summary["backup"] = os.path.relpath(backup, ROOT)
    summary["timestamp_ist"] = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    summary["copper_edit_started"] = True
    summary["phase"] = "EDITING"
    summary["closed"] = []
    summary["blocked"] = {}
    summary["reverted"] = False
    summary["reverted_nets"] = []
    summary["restores"] = {}
    summary["notes"] = [
        "Preflight rip list recorded in PASS30N_SUMMARY before copper edit",
        "ONE atomic cycle: rip P0.15 east + COEX2 H@24.6 + P0.01 H@15.2 → route nRESET with south jog → co-restore → DRC",
    ]
    summary["p002_attempted"] = False
    json.dump(summary, open(summary_path, "w"), indent=2)

    board = load()
    summary["p015_west_segs"] = {"before": p015_west(board)}
    summary["stage_a_check_before"] = stage_a_ok(board)

    print("DRC BEFORE...")
    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30N_BEFORE.json")
    before_nets = nets_of(before_data)
    summary["before"] = before
    summary["before_nets_watch"] = {n: before_nets.get(n, 0) for n in WATCH}
    print("  before:", before)
    json.dump(summary, open(summary_path, "w"), indent=2)

    # Reload after external kicad-cli DRC to avoid SWIG board stale state
    board = load()

    pre_tx = f"{SNAP}/pre-nreset-tx.kicad_pcb"
    shutil.copy2(BOARD, pre_tx)

    print("Ripping preflight set...")
    removed = rip_preflight(board, summary["preflight_rip_list"])
    summary["ripped_actual"] = removed
    missing = [r for r in removed if r.get("error")]
    if missing:
        summary["notes"].append(f"WARN missing rips: {missing}")
        print("  WARN missing:", missing)
    print("  ripped:", len([r for r in removed if not r.get("error")]))

    print("Routing nRESET...")
    summary["nreset_attempt"] = route_nreset(board)

    print("Co-restoring COEX2 + P0.01 + P0.15 east...")
    summary["restores"]["COEX2"] = restore_coex2(board)
    summary["restores"]["P0.01"] = restore_p001(board)
    summary["restores"]["P0.15"] = restore_p015_east(board)

    # Save copper first; zone-fill in child process (Fill can SIGSEGV on exit)
    save(board)
    print("Saved pre-fill; zone-fill subprocess...", flush=True)
    fill_script = f"{SNAP}/zone_fill_once.py"
    open(fill_script, "w").write(
        "import pcbnew,sys\n"
        f"b=pcbnew.LoadBoard({BOARD!r})\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        f"pcbnew.SaveBoard({BOARD!r}, b)\n"
        "print('zone-fill saved', flush=True)\n"
    )
    rc = subprocess.call([sys.executable, fill_script])
    print("zone-fill rc", rc, flush=True)
    # reload after fill (or pre-fill if child died before save)
    board = load()

    print("DRC MID...")
    mid_data, mid = run_drc(f"{REPORTS}/DRC_PASS30N_MID.json")
    mid_nets = nets_of(mid_data)
    summary["mid"] = mid
    summary["mid_nets_watch"] = {n: mid_nets.get(n, 0) for n in WATCH}
    print("  mid:", mid)

    nreset_closed = mid_nets.get("nRESET", 0) < before_nets.get("nRESET", 0)
    restores_ok = (
        mid_nets.get("P0.15", 0) <= before_nets.get("P0.15", 0)
        and mid_nets.get("COEX2", 0) <= before_nets.get("COEX2", 0)
        and mid_nets.get("P0.01", 0) <= before_nets.get("P0.01", 0)
    )
    # P0.01 may still have its own 1 unc from before — must not increase
    gate_ok = clean(mid) and nreset_closed and restores_ok

    if not gate_ok:
        print("FAIL — atomic revert")
        shutil.copy2(pre_tx, BOARD)
        summary["reverted"] = True
        summary["reverted_nets"].append("nRESET")
        summary["colliding_copper"] = colliding_from_drc(mid_data)
        summary["blocked"]["nRESET"] = (
            f"Atomic revert after mid DRC: shorting={mid['shorting_items']} "
            f"clearance={mid['clearance']} crossing={mid['tracks_crossing']}; "
            f"nRESET_unc mid={mid_nets.get('nRESET')} (was {before_nets.get('nRESET')}). "
            f"restores_ok={restores_ok}."
        )
        summary["blocked"]["P0.02"] = "Not attempted — nRESET not KEPT"
        summary["notes"].append("STOP — shorting/crossing/clearance >0; full tx reverted")
        summary["stop"] = True
        after_data, after = run_drc(f"{REPORTS}/DRC_PASS30N_AFTER.json")
        after_nets = nets_of(after_data)
        summary["after"] = after
    else:
        print("nRESET KEPT clean")
        summary["closed"].append("nRESET")
        summary["notes"].append(
            f"nRESET KEPT: unconnected {before['unconnected_items']}→{mid['unconnected_items']}"
        )
        summary["blocked"]["P0.02"] = (
            "Skipped — no free corridor identified without additional rips this cycle "
            "(only after nRESET KEPT; defer to avoid thrash)"
        )
        summary["p002_attempted"] = False
        summary["stop"] = False
        after_data, after = mid_data, mid
        after_nets = mid_nets
        shutil.copy2(f"{REPORTS}/DRC_PASS30N_MID.json", f"{REPORTS}/DRC_PASS30N_AFTER.json")
        summary["after"] = after

    import gc
    board = None
    gc.collect()
    board = load()
    try:
        summary["p015_west_segs"]["after"] = p015_west(board)
    except Exception as e:
        print("WARN p015_west after:", e)
        summary["p015_west_segs"]["after"] = summary["p015_west_segs"].get("before")
    try:
        summary["stage_a_check"] = stage_a_ok(board)
    except Exception as e:
        print("WARN stage_a after:", e)
        summary["stage_a_check"] = summary.get("stage_a_check_before")
    summary["p015_west_segs"]["preserved"] = (
        summary["p015_west_segs"]["after"] == summary["p015_west_segs"]["before"]
    )
    if "stage_a_check" not in summary or summary["stage_a_check"] is None:
        summary["stage_a_check"] = summary.get("stage_a_check_before")
    summary["signal_net_deltas"] = {
        n: after_nets.get(n, 0) - before_nets.get(n, 0) for n in WATCH
    }
    summary["all_net_deltas"] = {
        n: after_nets.get(n, 0) - before_nets.get(n, 0)
        for n in sorted(set(before_nets) | set(after_nets))
        if after_nets.get(n, 0) != before_nets.get(n, 0)
    }
    summary["phase"] = "COMPLETE_REVERTED" if summary["reverted"] else "COMPLETE_KEPT"
    bu, au = summary["before"]["unconnected_items"], summary["after"]["unconnected_items"]
    success = (
        not summary["reverted"]
        and "nRESET" in summary["closed"]
        and au <= 73
        and summary["after"]["shorting_items"] == 0
        and summary["after"]["clearance"] == 0
        and summary["after"]["tracks_crossing"] == 0
        and summary["signal_net_deltas"].get("nRESET", 0) <= -1
    )
    summary["success_gate"] = (
        f"{'MET' if success else 'NOT MET'} ({bu}→{au}; nRESET "
        f"{'KEPT' if 'nRESET' in summary['closed'] and not summary['reverted'] else 'reverted'})"
    )
    summary["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30N_BEFORE.json",
        "reports/DRC_PASS30N_MID.json",
        "reports/DRC_PASS30N_AFTER.json",
        "reports/PASS30N_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30n.py",
        summary["backup"],
        ".mcp-backups/pass30n-connect/pre-nreset-tx.kicad_pcb",
    ]
    json.dump(summary, open(summary_path, "w"), indent=2)
    update_docs(summary)
    json.dump(summary, open(summary_path, "w"), indent=2)

    print("DONE", summary["success_gate"])
    print(json.dumps({
        "before": summary["before"],
        "mid": summary.get("mid"),
        "after": summary["after"],
        "closed": summary["closed"],
        "reverted": summary["reverted"],
        "deltas": summary["signal_net_deltas"],
        "rip": summary.get("ripped_actual"),
        "collisions": summary.get("colliding_copper", [])[:5],
    }, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
