#!/usr/bin/env python3
"""Find short same-layer CLEAR island gaps on remaining open nets."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from rescue_final import pok  # noqa: E402
from rescue_islands2 import net_graph, summarize  # noqa: E402

F, B = pcbnew.F_Cu, pcbnew.B_Cu
OPEN = [
    "COEX0", "COEX1", "MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_SCLK", "MIPI_SDATA", "MIPI_VIO",
    "P0.00", "P0.01", "P0.02", "P0.03", "P0.05", "P0.07", "P0.08", "P0.09", "P0.10", "P0.11",
    "P0.12", "P0.14", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "P0.21", "P0.22", "P0.23",
    "P0.24", "P0.25", "P0.26", "P0.27", "P0.28", "P0.29", "P0.30", "P0.31",
    "SIM_1V8", "SIM_CLK", "SIM_IO", "SIM_RST", "SWDCLK", "VDD_GPIO", "VIN_F", "VIN_FILT", "nRESET",
]


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    hits = []
    for name in OPEN:
        g = summarize(net_graph(r, name))
        if len(g) < 2:
            print(f"{name}: islands={len(g)} (skip)")
            continue
        print(f"{name}: islands={len(g)}")
        for i, a in enumerate(g):
            for j, b in enumerate(g):
                if j <= i:
                    continue
                best = None
                for p in a["pts"]:
                    for q in b["pts"]:
                        if p[2] != q[2]:
                            continue
                        d = hypot(p[0], p[1], q[0], q[1])
                        if best is None or d < best[0]:
                            best = (d, p, q)
                if not best:
                    continue
                d, p, q = best
                ly = p[2]
                err = pok(r, [(p[0], p[1]), (q[0], q[1])], ly, name)
                layer = "F" if ly == F else "B"
                mark = "CLEAR" if err is None else f"BLOCK {err}"
                print(f"  [{i}-{j}] {d:.3f}mm {layer} ({p[0]:.2f},{p[1]:.2f})->({q[0]:.2f},{q[1]:.2f}) {mark}")
                print(f"      pads {a['pads']} <-> {b['pads']} vias {a['vias'][:3]} <-> {b['vias'][:3]}")
                if err is None and d < 25:
                    hits.append((d, name, layer, p, q, a["pads"], b["pads"]))
    print("\n=== CLEAR stitches d<25 ===")
    for h in sorted(hits):
        print(f"  {h[1]:12s} {h[0]:6.3f} {h[2]} ({h[3][0]:.2f},{h[3][1]:.2f})->({h[4][0]:.2f},{h[4][1]:.2f}) {h[5]}->{h[6]}")


if __name__ == "__main__":
    main()
