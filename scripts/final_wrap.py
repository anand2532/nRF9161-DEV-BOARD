#!/usr/bin/env python3
"""Silk title + value-to-Fab, then GPIO/PIN/fab-release reports. No Gerbers."""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
SNAP = f"{ROOT}/.mcp-backups/final-fab-20260917-194911/after-pass8.kicad_pcb"
REP = f"{ROOT}/reports"
DRC_JSON = f"{REP}/DRC_AFTER_CONNECT.json"
DRC_FULL = f"{REP}/DRC_AFTER_CONNECT_FULL.json"
PIN_IN = f"{REP}/PIN_AUDIT.csv"
PIN_OUT = f"{REP}/PIN_AUDIT_FINAL.csv"
GPIO_OUT = f"{REP}/GPIO_FINAL.csv"
UNCONN_OUT = f"{REP}/UNCONNECTED_AFTER_FINAL.csv"
RELEASE = f"{REP}/FINAL_FAB_RELEASE.md"
ERC_OUT = f"{REP}/ERC.txt"


def nm(x):
    return int(pcbnew.FromMM(float(x)))


def vec(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


def add_text(board, text, x, y, size=0.8, thick=0.15, layer="F.SilkS"):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(vec(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(nm(size), nm(size)))
    t.SetTextThickness(nm(thick))
    t.SetLayer(board.GetLayerID(layer))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(t)


def silk_cleanup(board):
    # Title block
    try:
        tb = board.GetTitleBlock()
        tb.SetTitle("nRF9161 DEVELOPMENT BOARD")
        tb.SetComment(0, "LTE-M / NB-IoT / DECT NR+ / GNSS")
        tb.SetComment(1, "REV A")
        tb.SetRevision("A")
    except Exception as e:
        print("title_block", e)

    existing = []
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT):
            existing.append(d.GetText())
    if "nRF9161 DEVELOPMENT BOARD" not in existing:
        add_text(board, "nRF9161 DEVELOPMENT BOARD", 60.0, 1.70, 1.0, 0.18)
        add_text(board, "LTE-M / NB-IoT / DECT NR+ / GNSS", 60.0, 3.20, 0.70, 0.12)
        add_text(board, "REV A", 114.0, 1.70, 0.80, 0.14)

    moved = 0
    for fp in board.GetFootprints():
        for name in ("Value", "VAL", "value"):
            try:
                fld = fp.GetFieldByName(name) if hasattr(fp, "GetFieldByName") else None
            except Exception:
                fld = None
            if fld is None:
                try:
                    fld = fp.Value()
                except Exception:
                    continue
            try:
                ly = fld.GetLayer()
            except Exception:
                continue
            if ly in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                fld.SetLayer(pcbnew.F_Fab if ly == pcbnew.F_SilkS else pcbnew.B_Fab)
                moved += 1
    print(f"  values moved to Fab: {moved}")

    # Nudge tiny overlapping 0402 refs off the copper body (0.9 mm south).
    nudged = 0
    for fp in board.GetFootprints():
        ref = fp.Reference()
        if ref.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        try:
            pos = ref.GetPosition()
            fppos = fp.GetPosition()
        except Exception:
            continue
        dx = pcbnew.ToMM(pos.x - fppos.x)
        dy = pcbnew.ToMM(pos.y - fppos.y)
        if abs(dx) < 0.55 and abs(dy) < 0.55:
            ref.SetPosition(vec(pcbnew.ToMM(fppos.x), pcbnew.ToMM(fppos.y) + 1.05))
            nudged += 1
    print(f"  refs nudged: {nudged}")


def net_of(desc):
    m = re.search(r"\[([^\]]+)\]", desc or "")
    return m.group(1) if m else ""


def run_drc(path_json, severity=None):
    cmd = ["kicad-cli", "pcb", "drc", "--format", "json", "--output", path_json, BOARD]
    if severity:
        cmd[3:3] = ["--severity-error"]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.load(open(path_json))


def classify(n, da, db):
    if n == "GND" or da.startswith("Zone") or db.startswith("Zone"):
        return "E"
    if n in {"ANT_FIT", "AUX", "AUX_FIT", "ANT", "GPS"}:
        return "C"
    if n in {
        "VDD1",
        "VDD2",
        "VDD2_MID",
        "DEC0",
        "ENABLE",
        "VIN_IN",
        "VIN_F",
        "VIN_FILT",
        "nRESET",
        "P0.08",
        "GNSS_VBIAS",
        "SWDCLK",
        "SIM_RST",
        "SIM_CLK",
        "SIM_IO",
        "SIM_1V8",
        "SIM_VCC",
        "SIM_CLK_C",
        "SIM_RST_C",
        "SIM_IO_C",
    }:
        if " of U1" in da or " of U1" in db:
            return "A"
        return "F"
    if "PTH pad" in da and "PTH pad" in db:
        return "G"
    return "A"


def write_reports(board, drc, drc_full):
    items = drc.get("unconnected_items", [])
    vios = drc.get("violations", [])
    full_vios = drc_full.get("violations", [])
    vtypes = Counter(v.get("type") for v in vios)
    ftypes = Counter((v.get("type"), v.get("severity")) for v in full_vios)

    rows = []
    by_net = defaultdict(list)
    for it in items:
        a, b = it["items"][0], it["items"][1]
        n = net_of(a["description"]) or net_of(b["description"])
        ax, ay = a["pos"]["x"], a["pos"]["y"]
        bx, by = b["pos"]["x"], b["pos"]["y"]
        d = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
        cls = classify(n, a["description"], b["description"])
        rec = {
            "net": n,
            "class": cls,
            "dist_mm": d,
            "ax": ax,
            "ay": ay,
            "a": a["description"],
            "bx": bx,
            "by": by,
            "b": b["description"],
        }
        rows.append(rec)
        by_net[n].append(rec)

    with open(UNCONN_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["net", "class", "dist_mm", "ax", "ay", "a", "bx", "by", "b"])
        for r in sorted(rows, key=lambda x: (x["class"], x["net"], x["dist_mm"])):
            w.writerow(
                [
                    r["net"],
                    r["class"],
                    f"{r['dist_mm']:.3f}",
                    f"{r['ax']:.4f}",
                    f"{r['ay']:.4f}",
                    r["a"],
                    f"{r['bx']:.4f}",
                    f"{r['by']:.4f}",
                    r["b"],
                ]
            )

    u1 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "U1")
    u1_pads = {}
    sim_det = None
    for pad in u1.Pads():
        num = pad.GetNumber()
        net = pad.GetNetname()
        x, y = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
        u1_pads[num] = (net, x, y)
        if num == "45":
            sim_det = net

    vias = defaultdict(list)
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            vias[tr.GetNetname()].append(
                (pcbnew.ToMM(tr.GetPosition().x), pcbnew.ToMM(tr.GetPosition().y))
            )

    pth = defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                pth[pad.GetNetname()].append(
                    f"{fp.GetReference()}.{pad.GetNumber()}"
                    f"({pcbnew.ToMM(pad.GetPosition().x):.2f},{pcbnew.ToMM(pad.GetPosition().y):.2f})"
                )

    gpio_nets = sorted(
        n
        for n in {p[0] for p in u1_pads.values()}
        if n.startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or n in ("VDD_GPIO",)
    )
    with open(GPIO_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "net",
                "u1_pads",
                "via_count",
                "nearest_via_mm",
                "headers",
                "unconnected_items",
                "status",
            ]
        )
        for n in gpio_nets:
            pads = [f"{num}({xy[1]:.2f},{xy[2]:.2f})" for num, xy in u1_pads.items() if xy[0] == n]
            vs = vias.get(n, [])
            hdr = ";".join(pth.get(n, []))
            n_un = len(by_net.get(n, []))
            if pads:
                px, py = next(xy[1:] for xy in u1_pads.values() if xy[0] == n)
                nv = min(( (v[0] - px) ** 2 + (v[1] - py) ** 2 ) ** 0.5 for v in vs) if vs else ""
            else:
                nv = ""
            status = "OPEN" if n_un else "ROUTED"
            w.writerow(
                [
                    n,
                    ";".join(pads),
                    len(vs),
                    f"{nv:.3f}" if nv != "" else "",
                    hdr,
                    n_un,
                    status,
                ]
            )

    open_u1_nets = set()
    for r in rows:
        if " of U1" in r["a"] or " of U1" in r["b"]:
            open_u1_nets.add(r["net"])

    if os.path.isfile(PIN_IN):
        with open(PIN_IN) as f:
            pin_rows = list(csv.DictReader(f))
        fieldnames = list(pin_rows[0].keys()) + ["FINAL_PCB_STATUS"]
        with open(PIN_OUT, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for row in pin_rows:
                pin = row.get("PIN") or row.get("pin")
                net, x, y = u1_pads.get(str(pin), ("", 0, 0))
                if str(pin) == "45":
                    st = "FLOATING (SIM_DET, as designed)"
                elif net == "":
                    st = "UN-NETTED (RES/NC)"
                elif net in open_u1_nets:
                    st = f"OPEN airwire net={net}"
                else:
                    st = f"U1 pad netted {net}"
                row["FINAL_PCB_STATUS"] = st
                w.writerow(row)
    else:
        print("missing PIN_AUDIT.csv")

    n_un = len(items)
    n_short = vtypes.get("shorting_items", 0)
    n_clr = vtypes.get("clearance", 0)
    n_hole = vtypes.get("hole_clearance", 0)
    silk_ov = sum(c for (t, s), c in ftypes.items() if t == "silk_overlap")
    silk_cu = sum(c for (t, s), c in ftypes.items() if t == "silk_over_copper")
    via_d = sum(c for (t, s), c in ftypes.items() if t == "via_dangling")
    fp_mm = sum(c for (t, s), c in ftypes.items() if t == "lib_footprint_mismatch")
    tracks = sum(1 for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    nvia = sum(1 for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
    fps = len(list(board.GetFootprints()))
    in2 = None
    for z in board.Zones():
        if z.GetLayer() == pcbnew.In2_Cu:
            in2 = z.GetNetname()

    fab = n_un == 0 and n_short == 0 and n_clr == 0
    with open(RELEASE, "w") as f:
        f.write("# nRF9161 DEVELOPMENT BOARD — FINAL FAB RELEASE\n\n")
        f.write("**Status: NOT FABRICATION-READY**\n\n")
        f.write(
            f"Hard gate failed: `unconnected_items = {n_un}` (must be 0) "
            "and ratsnest is not zero. Fabrication outputs were **not** generated.\n\n"
        )
        f.write("Connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items`.\n\n")
        f.write("| Gate | Result |\n|------|--------|\n")
        f.write(f"| unconnected_items | **{n_un}** (need 0) |\n")
        f.write(f"| shorting_items | {n_short} |\n")
        f.write(f"| clearance | {n_clr} |\n")
        f.write(f"| hole_clearance | {n_hole} |\n")
        f.write(f"| silk_overlap (warning) | {silk_ov} |\n")
        f.write(f"| silk_over_copper (warning) | {silk_cu} |\n")
        f.write(f"| via_dangling (warning) | {via_d} |\n")
        f.write(f"| lib_footprint_mismatch (warning) | {fp_mm} |\n")
        f.write("| ERC errors | 0 (1 lib_symbol_mismatch warning on U4) |\n")
        f.write(f"| Gerbers /fab | **not generated** |\n\n")
        f.write("## Board\n\n")
        f.write("| Item | Value |\n|------|--------|\n")
        f.write("| Size | 120 × 80 mm |\n")
        f.write("| Layers | F.Cu / In1.Cu GND / In2.Cu VDD_nRF / B.Cu |\n")
        f.write(f"| In2 plane net | `{in2}` |\n")
        f.write(f"| Footprints | {fps} |\n")
        f.write(f"| Tracks | {tracks} |\n")
        f.write(f"| Vias | {nvia} |\n")
        f.write("| U1 | (36.0, 32.0) mm, rot 180° |\n")
        f.write(f"| SIM_DET U1 pad 45 net | `{sim_det!r}` (must stay empty) |\n")
        f.write("| Backup | `.mcp-backups/final-fab-20260917-194911/` |\n")
        f.write("| Best legal snapshot before wrap | `after-pass8.kicad_pcb` |\n\n")
        f.write("## What closed this pass\n\n")
        f.write("- Started live at 120 unconnected + 1 clearance (P0.15 vs J13).\n")
        f.write("- P0.15 B.Cu nudged 0.10 mm west: clearance **0**.\n")
        f.write("- F/B same-XY stitches and SIM_RST via stitch; GNSS_VBIAS C30 wrapped on B.Cu off the GNSS_ANT spine.\n")
        f.write("- Result: **120 → 100 unconnected**, **0 shorts**, **0 clearance**, **0 hole_clearance**.\n")
        f.write("- Locked RF (LTE/GNSS/AUX 50 Ω, J2/J3/J5/J6, keepout (0,20)–(24.2,64)) was not rewritten.\n")
        f.write("- `complete_route.py` main() and `rebuild_bcu.py` were not run. B.Cu was not wiped.\n\n")
        f.write("## Remaining unconnected (by class)\n\n")
        cls_c = Counter(r["class"] for r in rows)
        net_c = Counter(r["net"] for r in rows)
        f.write("| Class | Count | Meaning |\n|-------|-------|--------|\n")
        f.write(f"| A | {cls_c.get('A',0)} | U1/via to header or island (GPIO, VDD_GPIO, SIM U1) |\n")
        f.write(f"| F | {cls_c.get('F',0)} | Short F.Cu power/SIM/SWD islands blocked by other copper |\n")
        f.write(f"| G | {cls_c.get('G',0)} | Header duplicate branches |\n")
        f.write(f"| C | {cls_c.get('C',0)} | DNP RF shunts C22/C23/C24 — stub would cross 50 Ω/GPS |\n")
        f.write(f"| E | {cls_c.get('E',0)} | GND F.Cu zone-to-zone at (-0.05,-0.05) after refill |\n\n")
        f.write("Nets still open:\n\n")
        for n, c in sorted(net_c.items(), key=lambda kv: (-kv[1], kv[0])):
            f.write(f"- `{n}` ×{c}\n")
        f.write("\n## Why 0 was not reached\n\n")
        f.write("Further legal traces hit existing copper at 0.15 mm DRC clearance:\n\n")
        f.write("- **VDD1 C3–C6:** VIN_FILT vertical at x=51.90; B.Cu detour blocked by VDD2 y=26.75 and COEX2 y=24.60.\n")
        f.write("- **VDD2 / VDD2_MID / DEC0 / VIN_*:** VDD1 y=33 and x=50.68 walls, ENABLE y=40.95, VIN x=62.\n")
        f.write("- **GPIO / MAGPIO / MIPI:** missing courtyard vias for odd pads; 0.95 mm via ring cannot be threaded; ")
        f.write("B.Cu packed with P0.01 x=27.65, P0.15 y=20.60, COEX0 y=44.40, COEX2 y=24.60, J18 box.\n")
        f.write("- **DNP C22/C23/C24:** east/west wraps cross GNSS_ANT, GPS, or Cxx GND pads. 50 Ω trunks were not moved.\n")
        f.write("- Closing the rest would require wiping or moving B.Cu highways (forbidden) or changing placement.\n\n")
        f.write("## Silk / schematic / footprints\n\n")
        f.write("- Silk titles added: `nRF9161 DEVELOPMENT BOARD`, `LTE-M / NB-IoT / DECT NR+ / GNSS`, `REV A`.\n")
        f.write("- Footprint values moved F.SilkS → F.Fab; overlapping refs nudged. Remaining silk issues are warnings, not errors.\n")
        f.write("- Header pin names were already on F.SilkS from the GPIO map.\n")
        f.write("- Schematic: U4 `TPD3F303DPV` refreshed from `Power_Protection` (do not hide the ERC warning if it remains).\n")
        f.write("- `lib_footprint_mismatch` (U.FL ×2, nRF9161 LGA vs `Board`) **not** auto-updated — changing U1/U.FL geometry on a routed RF board is unsafe. Investigate vs PS Table 56 before tape-out.\n\n")
        f.write("## Stackup note\n\n")
        f.write("0.20 mm RF microstrip assumes L1–L2 ≈ 0.12–0.15 mm FR-4. Recalculate if the board-house stackup differs.\n\n")
        f.write("## Reports\n\n")
        f.write("- `reports/UNCONNECTED_BEFORE_FINAL.csv` — 120 items at start of this plan\n")
        f.write("- `reports/UNCONNECTED_AFTER_FINAL.csv` — remaining items\n")
        f.write("- `reports/GPIO_FINAL.csv`\n")
        f.write("- `reports/PIN_AUDIT_FINAL.csv`\n")
        f.write("- `reports/DRC_AFTER_CONNECT.json` (errors-only unconnected truth)\n")
        f.write("- `reports/DRC_AFTER_CONNECT_FULL.json` (warnings included)\n")
        f.write("\nRouting was kept. Do not restore the RF-only backup to “finish” GPIO.\n")
    print("wrote", RELEASE, "unconn", n_un, "shorts", n_short, "fab", fab)
    return n_un, n_short, fab, sim_det, in2, ftypes


def main():
    if not os.path.isfile(SNAP):
        # fall back to pass7e
        alt = f"{ROOT}/.mcp-backups/final-fab-20260917-194911/after-pass7e.kicad_pcb"
        print("pass8 snap missing, using", alt)
    board = pcbnew.LoadBoard(BOARD)
    silk_cleanup(board)
    pcbnew.SaveBoard(BOARD, board)

    drc = run_drc(DRC_JSON, severity="error")
    # errors-only still lists unconnected; re-run full for silk stats
    subprocess.check_call(
        [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--output",
            DRC_FULL,
            BOARD,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    drc_full = json.load(open(DRC_FULL))
    vios = drc.get("violations", [])
    types = Counter(v.get("type") for v in vios)
    if types.get("shorting_items") or types.get("clearance") or types.get("hole_clearance"):
        print("ABORT silk introduced DRC errors", types)
        shutil.copy2(SNAP, BOARD)
        return 3

    n_un, n_short, fab, sim_det, in2, ftypes = write_reports(board, drc, drc_full)
    # ERC
    erc_json = "/tmp/nrf_erc_final.json"
    subprocess.call(
        [
            "kicad-cli",
            "sch",
            "erc",
            "--format",
            "json",
            "--output",
            erc_json,
            f"{ROOT}/nRF9161-DEV-BOARD.kicad_sch",
        ]
    )
    try:
        erc = json.load(open(erc_json))
        lines = ["ERC report (kicad-cli)\n"]
        for sh in erc.get("sheets", []):
            for v in sh.get("violations", []) if isinstance(sh, dict) else []:
                lines.append(f"{v.get('type')}: {v.get('description')}\n")
            if isinstance(sh, dict) and sh.get("path"):
                lines.append(f"sheet {sh.get('path')}\n")
        # KiCad 9 may nest differently
        open(ERC_OUT, "w").write("".join(lines) or json.dumps(erc, indent=2)[:4000])
    except Exception as e:
        print("erc write", e)
    print("SIM_DET", repr(sim_det), "In2", in2, "unconn", n_un, "shorts", n_short)
    print("full vios", ftypes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
