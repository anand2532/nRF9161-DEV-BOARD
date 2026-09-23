#!/usr/bin/env python3
"""Pass30z — RF Class C ONLY (C22/C23/C24 relocate + ≤2 mm stubs + GND vias).

Follows docs/RF_STUB_DNP_PLAN.md exactly.
- Relocate C24 next to L2.2/TP1 (AUX_FIT @ y≈33)
- Nudge C23 toward AUX at L2.1
- Nudge C22 toward ANT_FIT at L1.2 / trunk
- Same-net F.Cu stubs ≤2 mm, width 0.20 mm (RF_50OHM)
- Tie pad2 to GND with short via (solid In1 GND untouched / no splits)
- Leave parts DNP; do not rip trunks; no Package A/B/C; no U1; no Gerbers

Gate: shorting/clearance/crossing must be 0, else full RF revert to pre-edit.
"""
from __future__ import annotations

import json
import math
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
SNAP = f"{ROOT}/.mcp-backups/pass30z-rf-class-c"
REPORTS = f"{ROOT}/reports"
PRE = f"{SNAP}/pre-edit.kicad_pcb"
F = pcbnew.F_Cu
RF_W = 0.20
VIA_D, VIA_DRILL = 0.6, 0.3
MAX_STUB = 2.0

# Target placements (center XY mm, rotation degrees)
# C24 REQUIRED near L2.2/TP1 AUX_FIT trunk y=33 x=12–19.5 (north side, clear of GNSS y=35)
# C23 near AUX trunk y=33 east of L2 toward U1 (body ~outside west RF box x>24.2)
# C22 on/near ANT_FIT feed L1.2→(12,28)
TARGETS = {
    # C22 south of ANT_FIT trunk, rot=-90 so pad1 toward trunk / pad2 away (avoids GND-ANT_FIT short)
    "C22": {"xy": (17.50, 31.75), "rot": -90.0, "net": "ANT_FIT"},
    "C23": {"xy": (24.80, 34.00), "rot": 0.0, "net": "AUX"},
    "C24": {"xy": (15.00, 31.80), "rot": 0.0, "net": "AUX_FIT"},
}

# Do not touch
PROTECTED_REFS = {
    "L1", "L2", "L4", "C27", "J2", "J3", "J5", "J6", "TP1", "U1", "U3", "FB5",
    "J10", "J11", "J13", "C21", "C31", "C32",
}

UFL_VOIDS = [
    (7.05, 8.95, 31.485, 33.575),
    (7.05, 8.95, 51.485, 53.575),
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
    try:
        v.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(d))
        v.SetWidth(pcbnew.B_Cu, pcbnew.FromMM(d))
    except TypeError:
        v.SetWidth(pcbnew.FromMM(d))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetNet(board.FindNet(net))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)
    return v


def run_drc(out_path):
    tmp = "/tmp/nrf30z_drc.json"
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", tmp, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(tmp, out_path)
    data = json.load(open(out_path))
    vc = Counter(v["type"] for v in data.get("violations", []))
    return data, {
        "unconnected_items": len(data.get("unconnected_items", [])),
        "shorting_items": vc.get("shorting_items", 0),
        "clearance": vc.get("clearance", 0),
        "tracks_crossing": vc.get("tracks_crossing", 0),
        "copper_edge_clearance": vc.get("copper_edge_clearance", 0),
        "silk_over_copper": vc.get("silk_over_copper", 0),
        "silk_overlap": vc.get("silk_overlap", 0),
        "hole_clearance": vc.get("hole_clearance", 0),
        "via_dangling": vc.get("via_dangling", 0),
        "track_dangling": vc.get("track_dangling", 0),
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


def class_c_opens(data):
    """Return which of ANT_FIT/AUX/AUX_FIT still have unconnected items."""
    wanted = {"ANT_FIT", "AUX", "AUX_FIT"}
    present = set()
    details = {n: [] for n in wanted}
    for u in data.get("unconnected_items", []):
        desc = " | ".join(it.get("description", "") for it in u.get("items", []))
        nets_hit = set()
        for it in u.get("items", []):
            for m in re.findall(r"\[([^\]]+)\]", it.get("description", "")):
                if m in wanted:
                    nets_hit.add(m)
        # also catch by pad refs
        if "C22" in desc:
            nets_hit.add("ANT_FIT")
        if "C23" in desc and "AUX_FIT" not in desc:
            nets_hit.add("AUX")
        if "C24" in desc:
            nets_hit.add("AUX_FIT")
        for n in nets_hit & wanted:
            present.add(n)
            details[n].append(desc[:220])
    return present, details


def clean(s):
    return s["shorting_items"] == 0 and s["clearance"] == 0 and s["tracks_crossing"] == 0


def colliding(data, limit=25):
    out = []
    for v in data.get("violations", []):
        if v.get("type") in (
            "shorting_items",
            "clearance",
            "tracks_crossing",
            "copper_edge_clearance",
            "hole_clearance",
        ):
            out.append(
                {
                    "type": v["type"],
                    "description": v.get("description", "")[:220],
                    "items": [
                        {
                            "description": it.get("description", "")[:160],
                            "pos": it.get("pos"),
                        }
                        for it in v.get("items", [])[:3]
                    ],
                }
            )
        if len(out) >= limit:
            break
    return out


def zone_fill():
    script = f"{SNAP}/zone_fill_once.py"
    open(script, "w").write(
        "import pcbnew\n"
        f"b=pcbnew.LoadBoard({BOARD!r})\n"
        "pcbnew.ZONE_FILLER(b).Fill(b.Zones())\n"
        f"pcbnew.SaveBoard({BOARD!r}, b)\n"
        "print('zone-fill saved', flush=True)\n"
    )
    subprocess.check_call([sys.executable, script])


def p015_west(board):
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != "P0.15" or t.GetLayer() != pcbnew.B_Cu:
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


def fp_xy(board, ref):
    fp = board.FindFootprintByReference(ref)
    if not fp:
        return None
    return (round(mm(fp.GetPosition().x), 3), round(mm(fp.GetPosition().y), 3))


def pad_xy(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == str(num):
            return (mm(p.GetPosition().x), mm(p.GetPosition().y))
    return None


def inventory(board):
    refs = ["C21", "C22", "C23", "C24", "L1", "L2", "L4", "C27", "TP1", "J2", "J3", "J5", "J6",
            "U1", "U3", "FB5", "J10", "J11", "J13"]
    out = {"footprints": {}, "rf_tracks": []}
    for ref in refs:
        fp = board.FindFootprintByReference(ref)
        if not fp:
            continue
        pads = {}
        for p in fp.Pads():
            n = p.GetNumber()
            if not n:
                continue
            pads[n] = {
                "xy": [round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3)],
                "net": p.GetNetname(),
            }
        out["footprints"][ref] = {
            "xy": [round(mm(fp.GetPosition().x), 3), round(mm(fp.GetPosition().y), 3)],
            "rot": fp.GetOrientation().AsDegrees(),
            "dnp": bool(fp.IsDNP()),
            "pads": pads,
        }
    nets = {"ANT", "ANT_FIT", "AUX", "AUX_FIT"}
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() not in nets:
            continue
        x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
        x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
        out["rf_tracks"].append(
            {
                "net": t.GetNetname(),
                "layer": board.GetLayerName(t.GetLayer()),
                "w": round(mm(t.GetWidth()), 3),
                "len": round(math.hypot(x2 - x1, y2 - y1), 3),
                "a": [round(x1, 3), round(y1, 3)],
                "b": [round(x2, 3), round(y2, 3)],
            }
        )
    return out


def in_void(x, y):
    for x0, x1, y0, y1 in UFL_VOIDS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def dist_pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-12 and abs(dy) < 1e-12:
        return math.hypot(px - x1, py - y1), (x1, y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    qx, qy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - qx, py - qy), (qx, qy)


def nearest_trunk_point(board, net, px, py, prefer_segs=None):
    """Nearest point on same-net F.Cu trunk (prefer long segments / listed segs)."""
    best_d = 1e9
    best_q = None
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != net or t.GetLayer() != F:
            continue
        x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
        x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
        length = math.hypot(x2 - x1, y2 - y1)
        # skip our own tiny island stubs (<2.1mm) unless nothing else
        d, q = dist_pt_seg(px, py, x1, y1, x2, y2)
        # Prefer longer trunk segments
        score = d - (0.01 if length > 3.0 else 0.0)
        if score < best_d:
            best_d = score
            best_q = q
    # second pass: if best is on a short stub, prefer long trunks explicitly
    long_best_d, long_best_q = 1e9, None
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != net or t.GetLayer() != F:
            continue
        x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
        x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 3.0:
            continue
        d, q = dist_pt_seg(px, py, x1, y1, x2, y2)
        if d < long_best_d:
            long_best_d = d
            long_best_q = q
    if long_best_q is not None and long_best_d <= MAX_STUB + 0.05:
        return long_best_d, long_best_q
    return (best_d if best_q else 1e9), best_q


def remove_old_shunt_islands(board):
    """Remove short dangling stubs that belonged to old C22/C23/C24 islands.

    Do NOT touch main trunks (L1/L2/J2/J3/TP1 feeds).
    """
    # Exact known island stubs from inventory (pre-move)
    victims = []
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA) or t.Type() == pcbnew.PCB_VIA_T:
            continue
        net = t.GetNetname()
        if net not in ("ANT_FIT", "AUX", "AUX_FIT"):
            continue
        if t.GetLayer() != F:
            continue
        x1, y1 = mm(t.GetStart().x), mm(t.GetStart().y)
        x2, y2 = mm(t.GetEnd().x), mm(t.GetEnd().y)
        length = math.hypot(x2 - x1, y2 - y1)
        if length > 2.1:
            continue
        # Old C22 island: ~y=36 x=18–19.5
        if net == "ANT_FIT" and abs(y1 - 36.0) < 0.2 and abs(y2 - 36.0) < 0.2:
            victims.append(t)
            continue
        # Old C23 island: near (19.5,48) → (19.6,46)
        if net == "AUX" and min(y1, y2) > 45.0 and max(y1, y2) < 49.0:
            victims.append(t)
            continue
        # Old C24 island: ~x=19.52 y=56–57.5
        if net == "AUX_FIT" and min(y1, y2) > 55.0 and max(y1, y2) < 58.5:
            victims.append(t)
            continue
    for t in victims:
        board.Delete(t)
    return len(victims)


def move_shunt(board, ref, tx, ty, rot_deg):
    fp = board.FindFootprintByReference(ref)
    assert fp, f"missing {ref}"
    fp.SetPosition(xy(tx, ty))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot_deg, pcbnew.DEGREES_T))
    if hasattr(fp, "SetDNP"):
        fp.SetDNP(True)
    if hasattr(fp, "SetExcludedFromBOM"):
        fp.SetExcludedFromBOM(True)
    return fp


def apply_copper(board):
    """Move C22/C23/C24, add stubs + GND vias. Returns detail dict."""
    removed = remove_old_shunt_islands(board)
    save(board)
    board = load()  # refresh after Delete — SWIG proxies go stale otherwise
    details = {"removed_old_stubs": removed, "moves": {}, "stubs": [], "vias": []}

    for ref, spec in TARGETS.items():
        tx, ty = spec["xy"]
        assert not in_void(tx, ty), f"{ref} lands in U.FL void"
        move_shunt(board, ref, tx, ty, spec["rot"])
        p1 = pad_xy(board, ref, 1)
        p2 = pad_xy(board, ref, 2)
        details["moves"][ref] = {
            "xy": [tx, ty],
            "rot": spec["rot"],
            "pad1": [round(p1[0], 3), round(p1[1], 3)],
            "pad2": [round(p2[0], 3), round(p2[1], 3)],
            "net": spec["net"],
        }

    # Save intermediate so nearest_trunk sees pads at new locations without old islands
    # (tracks already removed)

    for ref, spec in TARGETS.items():
        net = spec["net"]
        p1x, p1y = pad_xy(board, ref, 1)
        p2x, p2y = pad_xy(board, ref, 2)
        d, q = nearest_trunk_point(board, net, p1x, p1y)
        stub_len = None
        if q is None:
            details["stubs"].append({"ref": ref, "net": net, "error": "no trunk"})
        elif d < 0.12:
            # pad already on/overlapping trunk
            stub_len = 0.0
            details["stubs"].append(
                {
                    "ref": ref,
                    "net": net,
                    "len": 0.0,
                    "from": [round(p1x, 3), round(p1y, 3)],
                    "to": [round(q[0], 3), round(q[1], 3)],
                    "note": "pad_overlaps_trunk",
                }
            )
        elif d <= MAX_STUB + 1e-6:
            add_trk(board, net, p1x, p1y, q[0], q[1], RF_W, F)
            stub_len = round(d, 3)
            details["stubs"].append(
                {
                    "ref": ref,
                    "net": net,
                    "len": stub_len,
                    "from": [round(p1x, 3), round(p1y, 3)],
                    "to": [round(q[0], 3), round(q[1], 3)],
                }
            )
        else:
            details["stubs"].append(
                {
                    "ref": ref,
                    "net": net,
                    "error": f"stub_too_long_{d:.3f}",
                    "to": [round(q[0], 3), round(q[1], 3)] if q else None,
                }
            )

        # GND via just outside pad2 (east for rot=0), short pour tie
        # Prefer via ~0.7 mm east of pad2 center, nudge if needed
        vx, vy = p2x + 0.75, p2y
        # Keep via out of U.FL voids and away from known RF pads
        if in_void(vx, vy):
            vx, vy = p2x, p2y + 0.75
        if ref == "C22":
            # Via at pad2 (same net) — avoid east stub that ate AUX_FIT clearance
            vx, vy = p2x, p2y
        elif ref == "C23":
            vx, vy = p2x + 0.70, p2y
        elif ref == "C24":
            vx, vy = p2x + 0.70, p2y
        add_via(board, "GND", vx, vy)
        gap = math.hypot(vx - p2x, vy - p2y)
        if gap > 0.25:
            add_trk(board, "GND", p2x, p2y, vx, vy, 0.25, F)
        details["vias"].append(
            {"ref": ref, "xy": [round(vx, 3), round(vy, 3)], "pad2_gap": round(gap, 3)}
        )

    return board, details


def protect_ok(board, before_inv):
    chk = {
        "stage_a": stage_a_ok(board),
        "p015_west_tracks": p015_west(board),
        "U1": fp_xy(board, "U1"),
        "J13": fp_xy(board, "J13"),
        "J10": fp_xy(board, "J10"),
        "J11": fp_xy(board, "J11"),
        "L1": fp_xy(board, "L1"),
        "L2": fp_xy(board, "L2"),
        "TP1": fp_xy(board, "TP1"),
        "J2": fp_xy(board, "J2"),
        "J3": fp_xy(board, "J3"),
        "U3": fp_xy(board, "U3"),
        "FB5": fp_xy(board, "FB5"),
        "C27": fp_xy(board, "C27"),
        "L4": fp_xy(board, "L4"),
    }
    ok = True
    reasons = []
    if not chk["stage_a"]["VDD_nRF_via_north"] or not chk["stage_a"]["VDD2_present"]:
        ok = False
        reasons.append("Stage A vias missing")
    if chk["p015_west_tracks"] < 1:
        ok = False
        reasons.append("P0.15 west wrap missing")
    for ref in ["U1", "J13", "J10", "J11", "L1", "L2", "TP1", "J2", "J3", "U3", "FB5", "C27", "L4"]:
        if before_inv["footprints"].get(ref) and chk[ref] != tuple(before_inv["footprints"][ref]["xy"]):
            # before_inv xy is list
            prev = before_inv["footprints"][ref]["xy"]
            if chk[ref] != (prev[0], prev[1]):
                ok = False
                reasons.append(f"{ref} moved {prev} -> {chk[ref]}")
    chk["ok"] = ok
    chk["reasons"] = reasons
    return chk


def revert():
    shutil.copy2(PRE, BOARD)
    print("REVERTED to pre-edit backup", flush=True)


def write_reports(summary):
    md = f"""# PASS30Z_SUMMARY — RF Class C only

**Timestamp:** {summary['timestamp']}
**Decision:** **{summary['decision']}**
**Phase:** {summary['phase']}

## DRC

| | unconnected | shorting | clearance | crossing |
| --- | ---: | ---: | ---: | ---: |
| Before | {summary['before']['unconnected_items']} | {summary['before']['shorting_items']} | {summary['before']['clearance']} | {summary['before']['tracks_crossing']} |
| After | {summary['after']['unconnected_items']} | {summary['after']['shorting_items']} | {summary['after']['clearance']} | {summary['after']['tracks_crossing']} |

**Gate:** {summary['gate_note']}

## Class C (ANT_FIT / AUX / AUX_FIT)

| Net | Before open? | After open? | Closed? |
| --- | --- | --- | --- |
| ANT_FIT | {summary['class_c_before'].get('ANT_FIT')} | {summary['class_c_after'].get('ANT_FIT')} | {summary['closed'].get('ANT_FIT')} |
| AUX | {summary['class_c_before'].get('AUX')} | {summary['class_c_after'].get('AUX')} | {summary['closed'].get('AUX')} |
| AUX_FIT | {summary['class_c_before'].get('AUX_FIT')} | {summary['class_c_after'].get('AUX_FIT')} | {summary['closed'].get('AUX_FIT')} |

## Final XY (C22/C23/C24)

| Ref | Final XY | Stub len (mm) | GND via |
| --- | --- | --- | --- |
| C22 | {summary['final_xy'].get('C22')} | {summary['stub_lens'].get('C22')} | {summary['via_xy'].get('C22')} |
| C23 | {summary['final_xy'].get('C23')} | {summary['stub_lens'].get('C23')} | {summary['via_xy'].get('C23')} |
| C24 | {summary['final_xy'].get('C24')} | {summary['stub_lens'].get('C24')} | {summary['via_xy'].get('C24')} |

## Protect checklist

```
{json.dumps(summary.get('protect', {}), indent=2)}
```

## Notes

{summary.get('notes', '')}

**Backup:** `{PRE}`
**Script:** `scripts/final_pass30z.py`
**DRC:** `reports/DRC_PASS30Z_BEFORE.json`, `reports/DRC_PASS30Z_AFTER.json`
"""
    open(f"{REPORTS}/PASS30Z_SUMMARY.md", "w").write(md)
    open(f"{REPORTS}/PASS30Z_SUMMARY.json", "w").write(json.dumps(summary, indent=2))


def update_layout_review(summary):
    path = f"{ROOT}/docs/PCB_LAYOUT_REVIEW.md"
    try:
        text = open(path).read()
    except OSError:
        return
    block = (
        f"\n\n## Pass30z — RF Class C (C22/C23/C24) — {summary['timestamp']}\n\n"
        f"- **Decision:** {summary['decision']}\n"
        f"- Unconnected {summary['before']['unconnected_items']} → {summary['after']['unconnected_items']}; "
        f"shorting/clearance/crossing after = "
        f"{summary['after']['shorting_items']}/{summary['after']['clearance']}/{summary['after']['tracks_crossing']}\n"
        f"- Class C closed: {summary['closed']}\n"
        f"- Final XY: C22={summary['final_xy'].get('C22')} C23={summary['final_xy'].get('C23')} "
        f"C24={summary['final_xy'].get('C24')}\n"
        f"- Details: `reports/PASS30Z_SUMMARY.md`\n"
    )
    if "Pass30z — RF Class C" in text:
        # replace last pass30z section roughly by appending anew only if missing
        pass
    open(path, "a").write(block)


def main():
    os.makedirs(SNAP, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)

    # 1. Backup
    if not os.path.exists(PRE):
        shutil.copy2(BOARD, PRE)
    else:
        # refresh pre-edit from current live (pass30y reverted to pass30u keep)
        shutil.copy2(BOARD, PRE)
    shutil.copy2(BOARD, f"{SNAP}/pre-edit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.kicad_pcb")

    board = load()
    before_inv = inventory(board)
    open(f"{SNAP}/inventory_before.json", "w").write(json.dumps(before_inv, indent=2))

    print("=== DRC BEFORE ===", flush=True)
    data_b, stats_b = run_drc(f"{REPORTS}/DRC_PASS30Z_BEFORE.json")
    print(stats_b, flush=True)
    cc_b_set, cc_b_det = class_c_opens(data_b)
    print("Class C open nets:", cc_b_set, flush=True)

    print("=== APPLY RF Class C copper ===", flush=True)
    board = load()
    board, copper = apply_copper(board)
    save(board)
    open(f"{SNAP}/copper_detail.json", "w").write(json.dumps(copper, indent=2))
    print(json.dumps(copper, indent=2), flush=True)

    print("=== ZONE FILL ===", flush=True)
    zone_fill()

    print("=== DRC AFTER ===", flush=True)
    data_a, stats_a = run_drc(f"{REPORTS}/DRC_PASS30Z_AFTER.json")
    print(stats_a, flush=True)
    cc_a_set, cc_a_det = class_c_opens(data_a)
    print("Class C open nets after:", cc_a_set, flush=True)

    board = load()
    after_inv = inventory(board)
    protect = protect_ok(board, before_inv)

    closed = {
        "ANT_FIT": ("ANT_FIT" in cc_b_set) and ("ANT_FIT" not in cc_a_set),
        "AUX": ("AUX" in cc_b_set) and ("AUX" not in cc_a_set),
        "AUX_FIT": ("AUX_FIT" in cc_b_set) and ("AUX_FIT" not in cc_a_set),
    }
    stub_lens = {}
    via_xy = {}
    final_xy = {}
    for s in copper.get("stubs", []):
        stub_lens[s["ref"]] = s.get("len", s.get("error"))
    for v in copper.get("vias", []):
        via_xy[v["ref"]] = v["xy"]
    for ref in TARGETS:
        final_xy[ref] = list(TARGETS[ref]["xy"])

    # Live XY from board (post-edit or will refresh after revert)
    for ref in TARGETS:
        final_xy[ref] = list(fp_xy(board, ref))

    is_clean = clean(stats_a)
    protect_pass = protect["ok"]
    any_closed = any(closed.values())
    # Success = clean AND (class C progress or already clear) AND protect
    # Gate per task: shorting/clearance/crossing must be 0; else full revert
    decision = "KEEP"
    phase = "COMPLETE_KEEP"
    gate_note = (
        f"clean={is_clean}; unconnected {stats_b['unconnected_items']}→{stats_a['unconnected_items']}; "
        f"closed={closed}; protect={protect_pass}"
    )
    notes = (
        f"Removed {copper['removed_old_stubs']} old island stubs. "
        f"Targets per RF_STUB_DNP_PLAN. Collisions: {colliding(data_a, 8)}"
    )

    if not is_clean:
        decision = "REVERT"
        phase = "COMPLETE_REVERTED"
        gate_note = (
            f"BLOCKED — dirty DRC shorting/clearance/crossing="
            f"{stats_a['shorting_items']}/{stats_a['clearance']}/{stats_a['tracks_crossing']}; "
            f"full RF revert to pre-edit"
        )
        notes = f"Collide head: {json.dumps(colliding(data_a, 12))[:1500]}"
        shutil.copy2(f"{REPORTS}/DRC_PASS30Z_AFTER.json", f"{REPORTS}/DRC_PASS30Z_MID_DIRTY.json")
        revert()
        # re-drc after revert for after stats that match live board
        data_a, stats_a = run_drc(f"{REPORTS}/DRC_PASS30Z_AFTER.json")
        cc_a_set, cc_a_det = class_c_opens(data_a)
        board = load()
        for ref in ["C22", "C23", "C24"]:
            final_xy[ref] = list(fp_xy(board, ref))
        closed = {
            "ANT_FIT": False,
            "AUX": False,
            "AUX_FIT": False,
        }
        stub_lens = {r: None for r in TARGETS}
        via_xy = {r: None for r in TARGETS}
        protect = protect_ok(board, before_inv)
    elif not protect_pass:
        decision = "REVERT"
        phase = "COMPLETE_REVERTED"
        gate_note = f"BLOCKED — protect fail {protect['reasons']}; full RF revert"
        revert()
        data_a, stats_a = run_drc(f"{REPORTS}/DRC_PASS30Z_AFTER.json")
        cc_a_set, cc_a_det = class_c_opens(data_a)
        board = load()
        for ref in ["C22", "C23", "C24"]:
            final_xy[ref] = list(fp_xy(board, ref))
        closed = {"ANT_FIT": False, "AUX": False, "AUX_FIT": False}
        stub_lens = {r: None for r in TARGETS}
        via_xy = {r: None for r in TARGETS}
        protect = protect_ok(board, before_inv)

    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "decision": decision,
        "phase": phase,
        "gate_note": gate_note,
        "before": stats_b,
        "after": stats_a,
        "before_nets": nets_of(data_b),
        "after_nets": nets_of(data_a),
        "class_c_before": {n: (n in cc_b_set) for n in ("ANT_FIT", "AUX", "AUX_FIT")},
        "class_c_after": {n: (n in cc_a_set) for n in ("ANT_FIT", "AUX", "AUX_FIT")},
        "class_c_before_details": cc_b_det,
        "class_c_after_details": cc_a_det,
        "closed": closed,
        "final_xy": final_xy,
        "stub_lens": stub_lens,
        "via_xy": via_xy,
        "copper": copper if decision == "KEEP" else {"reverted": True, "attempted": copper},
        "protect": protect,
        "notes": notes,
        "backup": PRE,
    }
    write_reports(summary)
    update_layout_review(summary)
    print("=== SUMMARY ===", flush=True)
    print(json.dumps({k: summary[k] for k in (
        "decision", "before", "after", "closed", "final_xy", "stub_lens", "gate_note"
    )}, indent=2), flush=True)
    return 0 if decision == "KEEP" else 2


if __name__ == "__main__":
    sys.exit(main())
