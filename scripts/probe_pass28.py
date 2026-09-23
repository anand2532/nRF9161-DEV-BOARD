#!/usr/bin/env python3
"""Read-only dump of COEX2 copper and U1 ADC vias. No SaveBoard."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_pass14 import reload  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu


def main():
    board, r = reload()
    print("==== COEX2 vias ====")
    for v in r.vias:
        if v["n"] == "COEX2":
            print(f"  via ({v['x']:.2f},{v['y']:.2f}) r={v['r']:.2f}")
    print("==== COEX2 tracks ====")
    for t in r.tracks:
        if t["n"] != "COEX2":
            continue
        ly = "F" if t["ly"] == F else ("B" if t["ly"] == B else str(t["ly"]))
        print(f"  {ly} ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f}) w={t['w']:.2f}")
    p = r.u1("COEX2")
    print("U1", p)
    pads = [q for q in r.pads if q["name"] == "COEX2"]
    print("pads", [(q["ref"], q["num"], round(q["x"], 2), round(q["y"], 2)) for q in pads])

    print("\n==== remnant matches ====")
    for t in r.tracks:
        if t["n"] != "COEX2" or t["ly"] != B:
            continue
        xs, ys = sorted([t["x1"], t["x2"]]), sorted([t["y1"], t["y2"]])
        if abs((t["y1"] + t["y2"]) / 2 - 24.60) < 0.20 and abs(t["y1"] - t["y2"]) < 0.25:
            print(f"  H y24.6 ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")
        if abs((t["x1"] + t["x2"]) / 2 - 40.50) < 0.20 and abs(t["x1"] - t["x2"]) < 0.25:
            print(f"  V x40.5 ({t['x1']:.2f},{t['y1']:.2f})-({t['x2']:.2f},{t['y2']:.2f})")


if __name__ == "__main__":
    main()
