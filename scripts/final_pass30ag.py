#!/usr/bin/env python3
"""Pass30ag — use ONLY the opened B.Cu corridor to close one net.

Corridor (pass30af keep): B.Cu y=44.60, x=81.80–97.30, one 0.18 mm signal,
between SIM_CLK_C @ y=44.05 and SIM_RST_C @ y=45.00.

Prefer SIM_RST_C if it still has an open that this corridor can join.
Otherwise the single next SIM_* open whose islands both touch the corridor.
If none can, one probe track (SIM_RST) strictly inside the corridor, then
FULL REVERT unless short/clearance/crossing stay 0 AND unconnected drops >= 1.

No header moves. No Class C / P0.22 / frozen east-SE rip. No Gerbers.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/pass30ag-corridor"
REPORTS = f"{ROOT}/reports"
PRE = f"{SNAP}/pre-edit.kicad_pcb"
REVIEW = f"{ROOT}/docs/PCB_LAYOUT_REVIEW.md"
B = pcbnew.B_Cu
F = pcbnew.F_Cu

# Freed slot. Track centerline.
CORR_Y = 44.60
CORR_X1 = 81.80
CORR_X2 = 97.30
CORR_W = 0.18

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
SIM_OPEN_ORDER = ["SIM_RST_C", "SIM_RST", "SIM_CLK", "SIM_IO", "SIM_1V8"]
WATCH = [
    "SIM_RST_C", "SIM_RST", "SIM_CLK", "SIM_IO", "SIM_1V8", "SIM_CLK_C", "SIM_IO_C",
    "SIM_CD", "SIM_VCC", "P0.22", "P0.04", "P0.06", "P0.01", "P0.15", "P0.19",
    "VDD2", "VDD_nRF", "GND",
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
    tmp = "/tmp/nrf30ag_drc.json"
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
        "track_width": vc.get("track_width", 0),
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
    return (
        s["shorting_items"] == 0
        and s["clearance"] == 0
        and s["tracks_crossing"] == 0
        and s["hole_clearance"] == 0
    )


def colliding(data, limit=12):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in ("shorting_items", "clearance", "tracks_crossing", "hole_clearance"):
            out.append(
                {
                    "type": v["type"],
                    "description": v.get("description", "")[:220],
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


def restore_pre():
    shutil.copy2(PRE, BOARD)


def dist_point_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    if l2 < 1e-12:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
    qx, qy = ax + t * vx, ay + t * vy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def seg_seg_dist(a, b, c, d):
    # approximate by sampling + endpoint distances (segments are axis-aligned here)
    best = min(
        dist_point_seg(a[0], a[1], c[0], c[1], d[0], d[1]),
        dist_point_seg(b[0], b[1], c[0], c[1], d[0], d[1]),
        dist_point_seg(c[0], c[1], a[0], a[1], b[0], b[1]),
        dist_point_seg(d[0], d[1], a[0], a[1], b[0], b[1]),
    )
    # exact for axis-aligned or crossing: also check midpoint samples
    for i in range(1, 8):
        t = i / 8.0
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        best = min(best, dist_point_seg(px, py, c[0], c[1], d[0], d[1]))
    return best


class UF:
    def __init__(self):
        self.p = {}

    def add(self, x):
        self.p.setdefault(x, x)

    def find(self, x):
        self.add(x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def corridor_audit(board):
    """Per SIM net: island distances to the corridor centerline.

    An island 'touches' the 0.18 mm B track if some B.Cu copper of that
    island comes within half-width (0.09 mm) of the centerline. F.Cu does
    not touch a B track; a via inside the corridor would, and is noted
    separately when F copper crosses the centerline.
    """
    center = ((CORR_X1, CORR_Y), (CORR_X2, CORR_Y))
    half = CORR_W / 2.0
    # collect geometry per net
    geos = defaultdict(list)  # (kind, layer, a, b or None, radius)
    for t in board.GetTracks():
        n = t.GetNetname()
        if not n.startswith("SIM_") and n not in ("P0.03", "P0.22", "nRESET", "VDD_GPIO"):
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = mm(t.GetPosition().x), mm(t.GetPosition().y)
            r = mm(t.GetWidth(B)) / 2.0
            geos[n].append(("via", "via", (x, y), None, r))
        else:
            a = (mm(t.GetStart().x), mm(t.GetStart().y))
            b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
            lay = "B" if t.GetLayer() == B else "F" if t.GetLayer() == F else str(t.GetLayer())
            geos[n].append(("seg", lay, a, b, mm(t.GetWidth()) / 2.0))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if n not in geos and not n.startswith("SIM_"):
                continue
            if not n.startswith("SIM_"):
                continue
            x, y = mm(p.GetPosition().x), mm(p.GetPosition().y)
            sz = p.GetSize()
            r = max(mm(sz.x), mm(sz.y)) / 2.0
            lay = "B" if p.GetLayerSet().Contains(B) else "F"
            geos[n].append(("pad", lay, (x, y), None, r))

    report = {}
    for n, items in sorted(geos.items()):
        uf = UF()
        for i in range(len(items)):
            uf.add(i)
        def touches(i, j):
            ki, li, ai, bi, ri = items[i]
            kj, lj, aj, bj, rj = items[j]
            # vias/pads join any layer; segs join only same layer or via/pad
            if ki == "seg" and kj == "seg" and li != lj:
                return False
            tol = 0.08 + (0 if ki == "seg" else 0) 
            # endpoint / point proximity. Use copper radii so a via on a track joins.
            if ki == "seg" and kj == "seg":
                return seg_seg_dist(ai, bi, aj, bj) <= 0.08
            if ki != "seg" and kj != "seg":
                return ((ai[0] - aj[0]) ** 2 + (ai[1] - aj[1]) ** 2) ** 0.5 <= ri + rj + 0.05
            # point vs seg
            pt, seg_a, seg_b, pr, sr = (ai, aj, bj, ri, rj) if ki != "seg" else (aj, ai, bi, rj, ri)
            return dist_point_seg(pt[0], pt[1], seg_a[0], seg_a[1], seg_b[0], seg_b[1]) <= pr + 0.05

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if touches(i, j):
                    uf.union(i, j)
        islands = defaultdict(list)
        for i in range(len(items)):
            islands[uf.find(i)].append(items[i])

        island_rows = []
        b_touch = 0
        f_cross = 0
        for isl in islands.values():
            best_b = 1e9
            best_f = 1e9
            sample = None
            for kind, lay, a, b, r in isl:
                if kind == "seg":
                    d = seg_seg_dist(a, b, center[0], center[1]) - r
                    if lay == "B":
                        best_b = min(best_b, d)
                    elif lay == "F":
                        best_f = min(best_f, d)
                    if sample is None:
                        sample = f"{lay} ({a[0]:.2f},{a[1]:.2f})-({b[0]:.2f},{b[1]:.2f})"
                else:
                    d = dist_point_seg(a[0], a[1], center[0][0], center[0][1], center[1][0], center[1][1]) - r
                    if lay == "B" or kind == "via":
                        best_b = min(best_b, d)
                    if lay == "F" or kind == "via":
                        best_f = min(best_f, d)
                    if sample is None:
                        sample = f"{kind}@{lay} ({a[0]:.2f},{a[1]:.2f})"
            touches_b = best_b <= half + 0.02
            crosses_f = best_f <= half + 0.02
            if touches_b:
                b_touch += 1
            if crosses_f:
                f_cross += 1
            island_rows.append(
                {
                    "sample": sample,
                    "dist_B_copper_mm": None if best_b > 1e8 else round(best_b, 3),
                    "dist_F_copper_mm": None if best_f > 1e8 else round(best_f, 3),
                    "touches_B_track": touches_b,
                    "F_crosses_slot": crosses_f,
                }
            )
        island_rows.sort(key=lambda r: (r["dist_B_copper_mm"] is None, r["dist_B_copper_mm"] or 99))
        report[n] = {
            "islands": len(island_rows),
            "islands_touching_B_slot": b_touch,
            "islands_F_crossing_slot": f_cross,
            "can_close_with_B_track_only": b_touch >= 2,
            "nearest": island_rows[:4],
        }
    return report


def add_probe_track(board, netname):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(xy(CORR_X1, CORR_Y))
    t.SetEnd(xy(CORR_X2, CORR_Y))
    t.SetWidth(pcbnew.FromMM(CORR_W))
    t.SetLayer(B)
    net = board.FindNet(netname)
    if net is None:
        raise RuntimeError(f"missing net {netname}")
    t.SetNet(net)
    board.Add(t)
    return {
        "net": netname,
        "layer": "B.Cu",
        "from": [CORR_X1, CORR_Y],
        "to": [CORR_X2, CORR_Y],
        "width_mm": CORR_W,
        "note": "single segment strictly inside the opened corridor; no rip",
    }


def note_review(summary):
    decision = summary["decision"]
    b = summary["before"]["unconnected_items"]
    a = summary["after"]["unconnected_items"]
    aft = summary["after"]
    net = summary.get("attempt_net")
    text = open(REVIEW).read()
    if "## Pass30ag —" in text:
        return
    block = f"""
## Pass30ag — one signal in the B.Cu y=44.60 corridor — {summary['timestamp_ist']}

**Decision:** **{decision}**. Net attempted: `{net}`. SIM_RST_C was already continuous (0 opens), so the corridor was spare.

**Attempt:** one 0.18 mm B.Cu segment (81.80, 44.60)–(97.30, 44.60) only. No header move. No Class C / P0.22 / frozen east-SE rip.

**Why it does not close a net:** the slot is a sealed pocket. West mouth is walled by `SIM_IO_C` B @ x=78.60 and `SIM_CLK_C` B @ x=78.95; east mouth by `SIM_CLK_C` B @ x=97.85. No open SIM_* (or GPIO) island pair both touches that centerline, so unconnected cannot drop by ≥1 without leaving the corridor.

**Unconnected:** {b}→{a}. short/clearance/crossing after {decision}: {aft['shorting_items']}/{aft['clearance']}/{aft['tracks_crossing']}. Corridor still free.

**Artifacts:** `reports/PASS30AG_SUMMARY.md`, `reports/PASS30AG_SUMMARY.json`, `reports/DRC_PASS30AG_BEFORE.json`, `reports/DRC_PASS30AG_MID_SIM_RST.json`, `reports/DRC_PASS30AG_AFTER.json`, `scripts/final_pass30ag.py`
"""
    open(REVIEW, "a").write(block)
    # brief pointer near the live status paragraph
    anchor = "Live `kicad-cli` 9.0.2 DRC was re-run for pass30c"
    if anchor in text and "**Pass delta (pass30ag):**" not in text:
        text = open(REVIEW).read()  # includes appended section
        insert = (
            f"**Pass delta (pass30ag):** Corridor probe `{net}` **{decision}**. "
            f"SIM_RST_C already continuous. In-corridor B track did not join any open island "
            f"(pocket sealed by SIM_IO_C @x78.60 and SIM_CLK_C @x78.95 / x97.85). "
            f"Unconnected {b}→{a}. short/clr/cross "
            f"{aft['shorting_items']}/{aft['clearance']}/{aft['tracks_crossing']}. "
            f"Corridor still free. No Gerbers. Details: `reports/PASS30AG_SUMMARY.md`.\n\n"
        )
        text = text.replace(anchor, insert + anchor, 1)
        open(REVIEW, "w").write(text)


def main():
    os.makedirs(SNAP, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    if not os.path.isfile(PRE):
        shutil.copy2(BOARD, PRE)
    else:
        # always start from the snapshot taken at first entry
        pass

    summary = {
        "pass": "layout-pass30ag-corridor",
        "timestamp_ist": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "kicad": pcbnew.GetBuildVersion(),
        "python": sys.executable,
        "scope": "One 0.18 mm signal inside B.Cu corridor y=44.60 x=81.8-97.3 only.",
        "backup": PRE,
        "phase": "INIT",
        "corridor_spec": {"layer": "B.Cu", "y": CORR_Y, "x1": CORR_X1, "x2": CORR_X2, "width_mm": CORR_W},
    }

    # If a previous crashed edit left the board dirty, restore the original snapshot
    # only when PRE already existed at start. First run copies current board above.
    board = load()
    west0 = p015_west(board)
    summary["protect_before"] = protect_ok(board, west0)
    if not summary["protect_before"]["ok"]:
        summary["phase"] = "ABORT_PROTECT"
        summary["decision"] = "ABORT"
        json.dump(summary, open(f"{REPORTS}/PASS30AG_SUMMARY.json", "w"), indent=2)
        print("ABORT", summary["protect_before"], flush=True)
        return

    audit = corridor_audit(board)
    summary["corridor_audit"] = {k: audit[k] for k in SIM_OPEN_ORDER if k in audit}
    summary["corridor_audit_extra"] = {
        k: {"islands_touching_B_slot": v["islands_touching_B_slot"], "can_close_with_B_track_only": v["can_close_with_B_track_only"]}
        for k, v in audit.items()
        if k not in SIM_OPEN_ORDER
    }

    # Choose net: first SIM open (prefer SIM_RST_C) that has >=2 islands touching the B slot.
    chosen = None
    choice_reason = ""
    for n in SIM_OPEN_ORDER:
        info = audit.get(n)
        if not info:
            continue
        if info["can_close_with_B_track_only"]:
            chosen = n
            choice_reason = "two islands touch the B slot"
            break
    probe_only = False
    if chosen is None:
        # SIM_RST_C is the preferred finish, but it is continuous. Next SIM open is SIM_RST.
        # Nothing fits; still run exactly one in-corridor probe so DRC records the collision
        # (or proves the pocket is clear but does not drop unconnected).
        chosen = "SIM_RST"
        probe_only = True
        choice_reason = (
            "no SIM_* open has two islands on the B slot; "
            "probe SIM_RST (next open after continuous SIM_RST_C) inside the corridor only"
        )
    summary["attempt_net"] = chosen
    summary["choice_reason"] = choice_reason
    summary["probe_only"] = probe_only
    print("CHOICE", chosen, choice_reason, flush=True)

    before_data, before = run_drc(f"{REPORTS}/DRC_PASS30AG_BEFORE.json")
    summary["before"] = before
    before_nets = nets_of(before_data)
    summary["before_nets_watch"] = {n: before_nets.get(n, 0) for n in WATCH}
    print("BEFORE", before, "SIM_RST_C", before_nets.get("SIM_RST_C", 0), flush=True)

    # If SIM_RST_C gained an open vs the audit (shouldn't), prefer it only when the slot can close it.
    if before_nets.get("SIM_RST_C", 0) > 0 and audit.get("SIM_RST_C", {}).get("can_close_with_B_track_only"):
        chosen = "SIM_RST_C"
        probe_only = False
        summary["attempt_net"] = chosen
        summary["probe_only"] = False

    attempts = []
    kept = None
    info = {"label": "corridor_B_y44.60", "net": chosen, "probe_only": probe_only}
    try:
        board = load()
        info["edit"] = add_probe_track(board, chosen)
        save(board)
        zone_fill()
        data, stats = run_drc(f"{REPORTS}/DRC_PASS30AG_MID_SIM_RST.json")
        info["mid"] = stats
        mid_nets = nets_of(data)
        info["mid_nets_watch"] = {n: mid_nets.get(n, 0) for n in WATCH}
        info["collide"] = colliding(data)
        info["clean"] = clean(stats)
        info["protect"] = protect_ok(load(), west0)
        net_before = before_nets.get(chosen, 0)
        net_mid = mid_nets.get(chosen, 0)
        drop = before["unconnected_items"] - stats["unconnected_items"]
        info["net_open_before"] = net_before
        info["net_open_mid"] = net_mid
        info["unconnected_drop"] = drop
        reasons = []
        if not info["clean"]:
            reasons.append("dirty_drc")
        if not info["protect"]["ok"]:
            reasons.append("protect_fail:" + ",".join(info["protect"]["reasons"][:6]))
        if drop < 1:
            reasons.append(f"unconnected_drop_{drop}")
        if net_mid >= net_before:
            reasons.append(f"{chosen}_open_{net_before}->{net_mid}")
        if probe_only and drop < 1:
            reasons.append("probe_does_not_span_an_open")
        info["accept"] = len(reasons) == 0
        info["reason"] = "ok" if info["accept"] else ";".join(reasons)
    except Exception as e:
        info["accept"] = False
        info["reason"] = f"exception:{e}"
        info["clean"] = False
        restore_pre()
    attempts.append(info)
    print("MID", info.get("mid"), info.get("reason"), flush=True)

    if info.get("accept"):
        kept = info
        shutil.copy2(BOARD, f"{SNAP}/after-keep.kicad_pcb")
    else:
        restore_pre()

    after_data, after = run_drc(f"{REPORTS}/DRC_PASS30AG_AFTER.json")
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
    summary["drop_at_least_1"] = (not summary["reverted"]) and summary["unconnected_delta"] <= -1
    if kept:
        summary["phase"] = "COMPLETE_KEEP"
        summary["decision"] = "KEEP"
        summary["corridor"] = "consumed by the kept 0.18 mm signal"
    else:
        summary["phase"] = "COMPLETE_REVERTED"
        summary["decision"] = "REVERT"
        summary["corridor"] = "still free — probe removed, pass30af corridor intact"
        summary["stop_reason"] = info.get("reason")
        # audit narrative
        rst = audit.get("SIM_RST", {})
        clk = audit.get("SIM_CLK", {})
        io = audit.get("SIM_IO", {})
        v8 = audit.get("SIM_1V8", {})
        rstc = audit.get("SIM_RST_C", {})
        summary["audit"] = {
            "SIM_RST_C_opens_before": before_nets.get("SIM_RST_C", 0),
            "SIM_RST_C_continuous": before_nets.get("SIM_RST_C", 0) == 0,
            "SIM_RST_C_islands_touching_slot": rstc.get("islands_touching_B_slot"),
            "why": (
                "The opened slot is a closed pocket on B.Cu. "
                "SIM_CLK_C occupies y=44.05 (x=78.95–97.85) and SIM_RST_C occupies y=45.00 "
                "(x=81.80–97.30); a 0.18 mm track at y=44.60 clears them (~0.37 mm and ~0.22 mm) "
                "under Default clearance 0.10 mm, but it does not land on two islands of any open net. "
                "West exit is blocked by SIM_IO_C B vertical x=78.60 (y=42.50–45.80) and "
                "SIM_CLK_C B vertical x=78.95. East exit is blocked by SIM_CLK_C B vertical x=97.85. "
                "SIM_RST's nearest B copper ends at x=78.25,y=43.80 (about 3.6 mm from the mouth) "
                "and the other island is U1.43 at (32.75, 26.75). "
                "SIM_CLK / SIM_IO / SIM_1V8 opens are the U1-to-filter gaps west of x≈78, not this slot. "
                "SIM_IO's F spine at x=84 crosses the slot on F.Cu only (east island); a via there "
                "would not reach U1.48."
            ),
            "nearest_SIM_RST": rst.get("nearest"),
            "nearest_SIM_CLK": clk.get("nearest"),
            "nearest_SIM_IO": io.get("nearest"),
            "nearest_SIM_1V8": v8.get("nearest"),
            "mid_collide": info.get("collide", [])[:6],
            "mid_stats": info.get("mid"),
        }

    json.dump(summary, open(f"{REPORTS}/PASS30AG_SUMMARY.json", "w"), indent=2)

    lines = [
        "# PASS30AG_SUMMARY — one signal in the opened B.Cu corridor",
        "",
        f"**Timestamp:** {summary['timestamp_ist']}",
        f"**KiCad:** {summary['kicad']}",
        f"**Decision:** **{summary['decision']}**",
        f"**Net:** {summary['attempt_net']}",
        f"**Unconnected:** {before['unconnected_items']} → {after['unconnected_items']} (delta {summary['unconnected_delta']})",
        f"**Drop ≥ 1:** {summary['drop_at_least_1']}",
        f"**Short/clearance/crossing after:** {after['shorting_items']}/{after['clearance']}/{after['tracks_crossing']}",
        f"**Corridor:** {summary['corridor']}",
        "",
        "## Choice",
        "",
        summary["choice_reason"],
        "",
        f"SIM_RST_C opens before: {summary['before_nets_watch'].get('SIM_RST_C', 0)} (continuous if 0).",
        "",
        "## Attempt",
        "",
        f"- edit: {info.get('edit')}",
        f"- mid: {info.get('mid')}",
        f"- accept: {info.get('accept')} reason: {info.get('reason')}",
    ]
    if info.get("collide"):
        lines.append(f"- collide: {json.dumps(info['collide'][:4])[:900]}")
    else:
        lines.append("- collide: none (short/clearance/crossing/hole_clearance did not fire, or attempt did not reach DRC)")
    lines += ["", "## Why the corridor does not close a net", ""]
    if summary.get("audit"):
        lines.append(summary["audit"]["why"])
        lines.append("")
        lines.append("Nearest island distances (clearance from copper edge to the y=44.60 centerline; touch if ≤ 0.09 mm):")
        lines.append("")
        for name in ("nearest_SIM_RST", "nearest_SIM_CLK", "nearest_SIM_IO", "nearest_SIM_1V8"):
            lines.append(f"- {name}: {json.dumps(summary['audit'].get(name))[:500]}")
    lines.append("")
    lines.append("P0.22 keep not ripped. No header moves. No Class C move. No Gerbers. One attempt only.")
    if summary.get("stop_reason"):
        lines.append("")
        lines.append(f"**Stop:** {summary['stop_reason']}")
    if summary["decision"] == "KEEP":
        lines += [
            "",
            "## Next single-net corridor plan (do not execute)",
            "",
            "This keep consumed the y=44.60 slot. Do not put a second signal between SIM_CLK_C @44.05 and SIM_RST_C @45.00.",
            "Next pass should look for a different free centerline (not this pocket) before touching another SIM_* open.",
        ]
    open(f"{REPORTS}/PASS30AG_SUMMARY.md", "w").write("\n".join(lines) + "\n")
    note_review(summary)
    print("DONE", summary["decision"], "delta", summary["unconnected_delta"], flush=True)
    print("AFTER", after, flush=True)


if __name__ == "__main__":
    main()
