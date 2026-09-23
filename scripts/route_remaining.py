#!/usr/bin/env python3
"""Remove blocking GND stitch vias, then A* only still-open signal nets. Keep existing B.Cu/RF."""
from __future__ import annotations

import json
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import (  # noqa: E402
    BOARD,
    RF_BOX,
    U1_BOX,
    Router,
    hypot,
    in_box,
    net_width,
)

DRC_JSON = "/tmp/nrf_remain_drc.json"


def primary_hdr(r, name):
    cands = []
    for p in r.pads:
        if p["name"] != name or not p["pth"]:
            continue
        score = 3 if p["ref"] in ("J12", "J13") else 2 if p["ref"].startswith("J") else 0
        cands.append((-score, p["x"], p))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands[0][2]


class Remain(Router):
    def drop_gnd_grid(self):
        kill = []
        for v in self.vias:
            if v["n"] != "GND":
                continue
            x, y = v["x"], v["y"]
            if in_box(x, y, RF_BOX) or in_box(x, y, U1_BOX):
                continue
            on = abs(x / 10.0 - round(x / 10.0)) < 0.15 and abs(y / 10.0 - round(y / 10.0)) < 0.15
            if on and 10 <= x <= 110 and 10 <= y <= 70:
                kill.append(v)
        for v in kill:
            self.board.Remove(v["obj"])
        print("removed GND grid vias", len(kill), flush=True)
        self.vias = [v for v in self.vias if v not in kill]


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Remain(board)
    r.collect()
    r.drop_gnd_grid()
    r.collect()

    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["pth"]
            and p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX", "SIM_", "SWD", "nRESET", "ENABLE", "VDD_GPIO"))
        }
    )
    ok = fail = skip = 0
    for name in nets:
        blen = sum(
            hypot(t["x1"], t["y1"], t["x2"], t["y2"])
            for t in r.tracks
            if t["n"] == name and t["ly"] == pcbnew.B_Cu
        )
        if blen > 25:
            skip += 1
            continue
        hdr = primary_hdr(r, name)
        if not hdr:
            continue
        u1 = next((p for p in r.pads if p["ref"] == "U1" and p["name"] == name), None)
        vias = [v for v in r.vias if v["n"] == name]
        if not vias:
            print("no via", name)
            fail += 1
            continue
        via = min(vias, key=lambda v: hypot(v["x"], v["y"], (u1 or hdr)["x"], (u1 or hdr)["y"]))
        w = net_width(name)
        code = hdr["code"]
        if r.astar_b(via["x"], via["y"], hdr["x"], hdr["y"], name, w, code):
            print("A*", name, "->", hdr["ref"], flush=True)
            ok += 1
            for extra in r.pads:
                if extra["name"] == name and extra["pth"] and extra is not hdr:
                    r.astar_b(hdr["x"], hdr["y"], extra["x"], extra["y"], name, w, code)
        else:
            print("FAIL", name, flush=True)
            fail += 1
    print(f"ok={ok} fail={fail} skip={skip}", flush=True)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", DRC_JSON, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    data = json.load(open(DRC_JSON))
    shorts = sum(
        1
        for v in data.get("violations", [])
        if v.get("type") in ("shorting_items", "clearance", "hole_clearance")
    )
    n = len(data.get("unconnected_items", []))
    print(f"DRC unconnected={n} shorts/clear/hole={shorts}", flush=True)
    return 0 if shorts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
