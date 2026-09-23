#!/usr/bin/env python3
"""Rebuild ALL B.Cu signal routing on a clean layer. Preserve F.Cu and vias. No autorouter."""
from __future__ import annotations

import json
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import BOARD, Router, hypot, net_width  # noqa: E402

DRC_JSON = "/tmp/nrf_bcu_drc.json"


class Rebuild(Router):
    def __init__(self, board):
        super().__init__(board)
        self.xcols_e = [
            x
            for x in [round(64.6 + i * 0.50, 2) for i in range(110)]
            if 64.6 <= x <= 115.2 and all(abs(x - g) >= 1.05 for g in (70, 80, 90, 100, 110))
        ]
        self.xcols_w = [round(25.40 + i * 0.45, 2) for i in range(16)]
        self.yjogs = [round(y, 2) for y in (
            [15.20 + i * 0.40 for i in range(7)]
            + [19.00 + i * 0.40 for i in range(9)]
            + [24.60 + i * 0.40 for i in range(10)]
            + [44.40 + i * 0.40 for i in range(12)]
        )]
        self.ei = 0
        self.wi = 0
        self.yi = 0

    def next_east(self):
        x = self.xcols_e[self.ei % len(self.xcols_e)]
        self.ei += 1
        return x

    def next_west(self):
        x = self.xcols_w[self.wi % len(self.xcols_w)]
        self.wi += 1
        return x

    def next_y(self):
        y = self.yjogs[self.yi % len(self.yjogs)]
        self.yi += 1
        return y
    def wipe_bcu(self):
        kill = [
            t
            for t in self.board.GetTracks()
            if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu
        ]
        for t in kill:
            self.board.Remove(t)
        print("removed B.Cu tracks", len(kill), flush=True)

    def courtyard_via(self, name, p):
        vias = [v for v in self.vias if v["n"] == name]
        if not vias:
            return None
        if p:
            return min(vias, key=lambda v: hypot(v["x"], v["y"], p["x"], p["y"]))
        return vias[0]

    def path_to(self, name, vx, vy, hx, hy, lane):
        w = net_width(name)
        code = self.board.FindNet(name).GetNetCode()
        if self.astar_b(vx, vy, hx, hy, name, w, code):
            return True
        # Gate south of J18 then retry
        for gate in ((65.2, 57.0), (25.8, 57.0), (114.2, 57.0), (65.2, 68.0), (25.8, 68.0)):
            if self.astar_b(vx, vy, gate[0], gate[1], name, w, code):
                if self.astar_b(gate[0], gate[1], hx, hy, name, w, code):
                    return True
        print(f"FAIL {name} ({vx:.1f},{vy:.1f})->({hx:.1f},{hy:.1f})", flush=True)
        return False


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


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Rebuild(board)
    r.wipe_bcu()
    r.collect()
    print("after wipe tracks", len(r.tracks), "vias", len(r.vias), flush=True)

    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["pth"]
            and p["name"]
            and p["name"]
            not in (
                "GND",
                "VDD_nRF",
                "VIN_IN",
                "VIN_FILT",
                "VIN_F",
                "ANT",
                "ANT_FIT",
                "AUX",
                "AUX_FIT",
                "GPS",
                "GNSS_ANT",
            )
        }
    )
    lane = 0
    ok = fail = 0
    for name in nets:
        hdr = primary_hdr(r, name)
        if not hdr:
            continue
        u1 = next((p for p in r.pads if p["ref"] == "U1" and p["name"] == name), None)
        via = r.courtyard_via(name, u1 or hdr)
        if not via:
            print("no via", name)
            fail += 1
            continue
        if r.path_to(name, via["x"], via["y"], hdr["x"], hdr["y"], lane):
            ok += 1
            extras = [p for p in r.pads if p["name"] == name and p["pth"] and p is not hdr]
            for extra in extras:
                lane += 1
                r.path_to(name, hdr["x"], hdr["y"], extra["x"], extra["y"], lane)
        else:
            fail += 1
        lane += 1

    print(f"routed {ok} fail {fail}", flush=True)
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
