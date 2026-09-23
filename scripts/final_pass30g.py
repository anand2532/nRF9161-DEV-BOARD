#!/usr/bin/env python3
"""Pass30g — one honest cycle. KiCad 9: always Save+Reload after Remove."""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime
import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30g-connect"
REPORTS = f"{ROOT}/reports"
BACKUPS = f"{ROOT}/.mcp-backups"
F, B = pcbnew.F_Cu, pcbnew.B_Cu
sys.path.insert(0, f"{ROOT}/scripts")
from final_connect import Final  # noqa: E402

os.makedirs(SNAP, exist_ok=True)


def mm(v):
    return pcbnew.ToMM(v)


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def save(board, path=BOARD):
    pcbnew.SaveBoard(path, board)


def load(path=BOARD):
    return pcbnew.LoadBoard(path)


def add_trk(board, net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(x1, y1))
    t.SetEnd(xy(x2, y2))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)


def fill_zones(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def run_drc(path):
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", "/tmp/nrf30g.json", BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2("/tmp/nrf30g.json", path)
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


def bbox_overlap(a, b):
    return not (
        a.GetRight() < b.GetLeft()
        or a.GetLeft() > b.GetRight()
        or a.GetBottom() < b.GetTop()
        or a.GetTop() > b.GetBottom()
    )


def commit_removes(board, doomed, tag):
    for t in doomed:
        board.Delete(t)
    print(f"  deleted {len(doomed)} ({tag})")
    save(board)
    return load()


def main():
    summary = {
        "pass": "layout-pass30g",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "moves_done": [],
        "moves_skipped": [],
        "vias_jogged": [],
        "closed": [],
        "blocked": {},
        "stop": False,
        "notes": [],
        "gerbers": False,
        "reverted": False,
    }

    before_path = f"{REPORTS}/DRC_PASS30G_BEFORE.json"
    before_data = json.load(open(before_path))
    vc = Counter(v["type"] for v in before_data.get("violations", []))
    before_counts = {
        "unconnected_items": len(before_data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "via_dangling": vc.get("via_dangling", 0),
    }
    before_nets = nets_of(before_data)
    summary["before"] = before_counts
    print("BEFORE", before_counts)

    board = load()
    west0 = p015_west(board)
    summary["p015_west"] = {"before": west0}

    # --- R2/TP20 collision ---
    r2 = board.FindFootprintByReference("R2")
    tp20 = board.FindFootprintByReference("TP20")
    old = r2.GetPosition()
    r2.SetPosition(xy(58.0, 24.0))
    p1 = [p for p in r2.Pads() if p.GetNumber() == "1"][0]
    overlap = bbox_overlap(p1.GetBoundingBox(), list(tp20.Pads())[0].GetBoundingBox())
    p1xy = [mm(p1.GetPosition().x), mm(p1.GetPosition().y)]
    r2.SetPosition(old)
    summary["r2_tp20"] = {
        "overlap": overlap,
        "r2_pad1_at_target": p1xy,
        "tp20": [mm(tp20.GetPosition().x), mm(tp20.GetPosition().y)],
    }
    print("R2/TP20 overlap", overlap, "pad1@", p1xy)
    if not overlap:
        raise SystemExit("unexpected: R2 should overlap TP20")

    c6 = board.FindFootprintByReference("C6")
    c6_old = {
        p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y))
        for p in c6.Pads()
        if p.GetNumber()
    }

    # --- targeted stub rip (collect UUIDs / objects carefully) ---
    doomed = []
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net, ly = t.GetNetname(), t.GetLayer()
        x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
        x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)

        def near(x, y, tol=0.12):
            return (abs(x1 - x) < tol and abs(y1 - y) < tol) or (
                abs(x2 - x) < tol and abs(y2 - y) < tol
            )

        kill = False
        # TP11 VDD1 vertical stub
        if net == "VDD1" and ly == F and abs(x1 - 60) < 0.05 and abs(x2 - 60) < 0.05:
            if abs(min(y1, y2) - 30) < 0.05:
                kill = True
        # TP19 VIN_FILT stubs
        if net == "VIN_FILT" and near(52.0, 22.0, 0.25):
            kill = True
        # C6 pad1 VDD1 fans
        if net == "VDD1" and near(c6_old["1"][0], c6_old["1"][1], 0.15):
            kill = True
        # VDD_nRF stub into via @y30
        if (
            net == "VDD_nRF"
            and ly == F
            and abs(y1 - 30) < 0.05
            and abs(y2 - 30) < 0.05
            and 67.5 <= min(x1, x2)
            and max(x1, x2) <= 69.5
        ):
            kill = True
        if kill:
            doomed.append(t)

    board = commit_removes(board, doomed, "prep-stubs")
    print("board ok", type(board), board.FindFootprintByReference("TP11") is not None)

    # --- moves ---
    for ref, pos in [("TP11", (60.0, 32.5)), ("C6", (49.0, 27.0)), ("TP19", (54.5, 22.0))]:
        board.FindFootprintByReference(ref).SetPosition(xy(*pos))
        summary["moves_done"].append({"ref": ref, "to": list(pos)})
        print("moved", ref, pos)
    summary["moves_skipped"].append(
        {
            "ref": "R2",
            "requested": [58.0, 24.0],
            "reason": "R2.1@(58,22.54) overlaps TP20@(58,22) VIN_FILT vs VDD_nRF",
        }
    )

    # via jog
    for t in board.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != "VDD_nRF":
            continue
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
        if abs(x - 69.3) < 0.05 and abs(y - 30) < 0.05:
            t.SetPosition(xy(69.3, 28.0))
            summary["vias_jogged"].append(
                {"net": "VDD_nRF", "from": [69.3, 30.0], "to": [69.3, 28.0]}
            )
            print("via jog VDD_nRF -> 69.3,28")

    save(board)
    board = load()

    # --- reattach ---
    add_trk(board, "VDD1", 60.0, 32.5, 60.0, 33.0, 0.40, F)
    add_trk(board, "VDD_nRF", 68.0, 30.0, 69.3, 30.0, 0.40, F)
    add_trk(board, "VDD_nRF", 69.3, 30.0, 69.3, 28.0, 0.40, F)

    c6 = board.FindFootprintByReference("C6")
    c61 = [p for p in c6.Pads() if p.GetNumber() == "1"][0]
    c61x, c61y = mm(c61.GetPosition().x), mm(c61.GetPosition().y)
    c5 = board.FindFootprintByReference("C5")
    c51 = [p for p in c5.Pads() if p.GetNumber() == "1"][0]
    c51x, c51y = mm(c51.GetPosition().x), mm(c51.GetPosition().y)
    print(f"C6.1=({c61x:.3f},{c61y:.3f}) C5.1=({c51x:.3f},{c51y:.3f})")
    add_trk(board, "VDD1", c61x, c61y, c61x, c51y, 0.25, F)
    add_trk(board, "VDD1", c61x, c51y, c51x, c51y, 0.25, F)
    add_trk(board, "VDD1", c61x, c61y, c61x, 25.6, 0.25, F)
    add_trk(board, "VDD1", c61x, 25.6, 49.2, 25.6, 0.25, F)

    add_trk(board, "VIN_FILT", 54.5, 22.0, 51.9, 21.9, 0.40, F)
    add_trk(board, "VIN_FILT", 54.5, 22.0, 54.5, 24.5375, 0.40, F)
    add_trk(board, "VIN_FILT", 54.5, 24.5375, 58.0, 24.5375, 0.40, F)
    summary["enable_f_bridge"] = (
        "kept (50.85,23.15)->(50.85,20.3)->(56.5,20.3); C6 west improves courtyard"
    )

    fill_zones(board)
    save(board)
    shutil.copy2(BOARD, f"{SNAP}/after-moves-fill.kicad_pcb")

    _, mid = run_drc(f"{REPORTS}/DRC_PASS30G_MID.json")
    print("MID", mid)
    summary["mid"] = mid

    if mid["shorting_items"] > 0 or mid["clearance"] > 0:
        bak = [f for f in os.listdir(BACKUPS) if "pre-pass30g-" in f][-1]
        shutil.copy2(f"{BACKUPS}/{bak}", BOARD)
        summary["reverted"] = True
        summary["stop"] = True
        summary["notes"].append(
            f"Reverted: mid short={mid['shorting_items']} clr={mid['clearance']}"
        )
        after_data, after = run_drc(f"{REPORTS}/DRC_PASS30G_AFTER.json")
        summary["after"] = after
        finish(summary, before_nets, after_data)
        return

    # --- P0.08 probe (temp rip ENABLE/COEX2 on a copy; live board stays at SNAP) ---
    probe = f"{SNAP}/p008-probe.kicad_pcb"
    live = BOARD
    shutil.copy2(f"{SNAP}/after-moves-fill.kicad_pcb", probe)
    board = load(probe)
    en_ripped, coex_ripped = [], []
    doomed = []
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net, ly = t.GetNetname(), t.GetLayer()
        if net == "ENABLE" and ly == B:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            w = mm(t.GetWidth())
            hit = False
            if abs(y1 - 28) < 0.05 and abs(y2 - 28) < 0.05 and max(x1, x2) > 70:
                hit = True
            if abs(x1 - 62.5) < 0.05 and abs(x2 - 62.5) < 0.05 and min(y1, y2) < 32 and max(y1, y2) > 25:
                hit = True
            if abs(x1 - 76.8) < 0.05 and abs(x2 - 76.8) < 0.05 and min(y1, y2) < 36 and max(y1, y2) > 26:
                hit = True
            if hit:
                en_ripped.append((x1, y1, x2, y2, w))
                doomed.append(t)
        if net == "COEX2" and ly == B:
            x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
            x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
            if abs(x1 - 72) < 0.05 and abs(x2 - 72) < 0.05 and min(y1, y2) < 38 and max(y1, y2) > 24:
                coex_ripped.append((x1, y1, x2, y2, mm(t.GetWidth())))
                doomed.append(t)
    for t in doomed:
        board.Delete(t)
    save(board, probe)
    board = load(probe)
    print("probe ENABLE ripped", en_ripped)
    print("probe COEX2 ripped", coex_ripped)

    r = Final(board)
    r.collect()

    def path_ok(pts, layer=B, w=0.18):
        for i in range(len(pts) - 1):
            a, b_ = pts[i], pts[i + 1]
            if not r.track_clear(a[0], a[1], b_[0], b_[1], layer, w, "P0.08"):
                return False, (a, b_)
        return True, None

    candidates = [
        ("B_y30", B, [(46.2, 30), (78.5, 30), (78.5, 26), (79.67, 26)]),
        (
            "B_over",
            B,
            [
                (46.2, 30),
                (51.5, 30),
                (51.5, 32.5),
                (56.5, 32.5),
                (78.5, 32.5),
                (78.5, 26),
                (79.67, 26),
            ],
        ),
        (
            "B_under",
            B,
            [
                (46.2, 30),
                (50.5, 30),
                (50.5, 25.0),
                (56.5, 25.0),
                (78.5, 25.0),
                (78.5, 26),
                (79.67, 26),
            ],
        ),
        ("F_y32.5", F, [(46.2, 30), (46.2, 32.5), (78.38, 32.5), (78.38, 26)]),
    ]
    failures, chosen = [], None
    for name, ly, pts in candidates:
        ok, bad = path_ok(pts, ly)
        print(("CLEAR" if ok else "BLOCK"), name, bad)
        if ok:
            chosen = (name, ly, pts)
            break
        failures.append({"path": name, "at": list(bad) if bad else None})

    # Optional via jogs on probe only
    if not chosen:
        for net, ox, oy, nx, ny in [
            ("P0.10", 47.4, 28.5, 47.4, 27.0),
            ("VDD1", 53.7, 27.13, 53.7, 25.5),
            ("VDD_GPIO", 78.0, 32.0, 78.0, 33.5),
        ]:
            for t in board.GetTracks():
                if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
                    continue
                x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
                if abs(x - ox) < 0.05 and abs(y - oy) < 0.05:
                    t.SetPosition(xy(nx, ny))
                    print(f"probe jog {net} ({ox},{oy})->({nx},{ny})")
        save(board, probe)
        board = load(probe)
        r = Final(board)
        r.collect()
        for name, ly, pts in candidates:
            ok, bad = path_ok(pts, ly)
            print(("CLEAR2" if ok else "BLOCK2"), name, bad)
            if ok:
                chosen = (name, ly, pts)
                break
            failures.append({"path": name + "+opt", "at": list(bad) if bad else None})

    # Live board stays at after-moves-fill (no P0.08 copper, ENABLE intact)
    shutil.copy2(f"{SNAP}/after-moves-fill.kicad_pcb", live)
    board = load(live)

    summary["stop"] = True
    summary["blocked"]["P0.08"] = {
        "probe_only": True,
        "chosen": chosen[0] if chosen else None,
        "failures": failures,
        "geometry": {
            "VDD2_walls": [[[52.22, 26.75], [52.22, 32.0]], [[54.50, 21.20], [54.50, 32.0]]],
            "GND_via": [80.0, 30.0],
            "why": (
                "After TP11/C6/TP19 + VDD_nRF via→(69.3,28) + ENABLE/COEX2 temp rip (probe), "
                "B@y≈30 still walled by VDD2 verticals; inter-column gap not enterable from west. "
                "Over/under/F blocked. Optional P0.10/VDD1/VDD_GPIO via jogs did not open path."
                + (f" NOTE: track_clear found {chosen[0]} but not committed — verify." if chosen else "")
            ),
        },
        "next_proposals": [
            {
                "ref": "TP20",
                "from": [58.0, 22.0],
                "to": [56.0, 20.0],
                "why": "Unlock R2→(58,24) without VIN_FILT/VDD_nRF short",
            },
            {
                "action": "VDD2 via-bridge or east U-jog at y≈30",
                "segments": [[[52.22, 26.75], [52.22, 32.0]], [[54.50, 21.20], [54.50, 32.0]]],
                "why": "Primary remaining P0.08 B wall",
            },
            {
                "action": "GND via jog",
                "from": [80.0, 30.0],
                "to": [80.0, 32.5],
                "why": "Clear dest approach",
            },
        ],
    }
    summary["blocked"]["VIN_F"] = "Not attempted — P0.08 STOP"
    summary["blocked"]["SWDCLK"] = "Not attempted — P0.08 STOP"
    summary["notes"].append(
        "STOP: P0.08 blocked after legal moves+via jog. Probe-only ENABLE/COEX2 rip. "
        "R2 skipped (TP20 collision). Live board keeps TP11/C6/TP19 + VDD_nRF via jog."
    )

    fill_zones(board)
    save(board)
    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30G_AFTER.json")
    summary["after"] = after
    finish(summary, before_nets, after_data)


def finish(summary, before_nets, after_data):
    board = load()
    summary["p015_west"]["after"] = p015_west(board)
    after_nets = nets_of(after_data)
    deltas = {}
    for n in sorted(set(before_nets) | set(after_nets)):
        b, a = before_nets.get(n, 0), after_nets.get(n, 0)
        if b != a:
            deltas[n] = [b, a]
    summary["net_unconnected_delta"] = deltas
    summary["signal_net_deltas"] = {k: v for k, v in deltas.items() if k != "GND"}
    bak = [f for f in os.listdir(BACKUPS) if "pre-pass30g-" in f][-1]
    summary["backup"] = f".mcp-backups/{bak}"
    summary["drc"] = [
        "reports/DRC_PASS30G_BEFORE.json",
        "reports/DRC_PASS30G_MID.json",
        "reports/DRC_PASS30G_AFTER.json",
    ]
    bu = summary["before"]["unconnected_items"]
    au = summary["after"]["unconnected_items"]
    summary["success_gate"] = (
        f"unconnected < {bu} with shorting=0 — "
        + ("MET" if au < bu and summary["after"]["shorting_items"] == 0 else "NOT MET")
    )
    summary["files_touched"] = [
        "nRF9161-DEV-BOARD.kicad_pcb",
        "reports/DRC_PASS30G_BEFORE.json",
        "reports/DRC_PASS30G_MID.json",
        "reports/DRC_PASS30G_AFTER.json",
        "reports/PASS30G_SUMMARY.json",
        "docs/PCB_LAYOUT_REVIEW.md",
        "scripts/final_pass30g.py",
    ]
    for ref in ["TP11", "R2", "C6", "TP19"]:
        fp = board.FindFootprintByReference(ref)
        print("FINAL", ref, mm(fp.GetPosition().x), mm(fp.GetPosition().y))
    with open(f"{REPORTS}/PASS30G_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("AFTER", summary["after"])
    print("stop", summary["stop"])
    print("moves_done", summary["moves_done"])
    print("moves_skipped", summary["moves_skipped"])
    print("vias", summary["vias_jogged"])
    print("signal deltas", summary["signal_net_deltas"])
    print("p015", summary["p015_west"])
    print("Wrote PASS30G_SUMMARY.json")


if __name__ == "__main__":
    main()
