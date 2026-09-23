#!/usr/bin/env python3
"""Finish remaining connectivity on the LIVE nRF9161-DEV-BOARD.

Loads the current PCB. Never restores the RF-only pre-fullroute backup.
Never wipes B.Cu. Never calls complete_route.main() or rebuild_bcu.
Skips unnumbered 0402 ghost pads. kicad-cli DRC after each class.
On new shorts/clearance/hole_clearance, restore the last good snapshot.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import (  # noqa: E402
    ADC,
    BOARD,
    J18_BOX,
    RF_BOX,
    RF_NETS,
    RF_OK,
    Router,
    SKIP,
    hypot,
    in_box,
    net_width,
    nm,
    vec,
)

ROOT = "/home/anand/kicad-projects/nRF9161-DEV-BOARD"
BACKUP = f"{ROOT}/.mcp-backups/final-fab-20260917-194911/nRF9161-DEV-BOARD.kicad_pcb"
SNAP_DIR = f"{ROOT}/.mcp-backups/final-fab-20260917-194911"
DRC_JSON = "/tmp/nrf_final_drc.json"
CSV_PATH = f"{ROOT}/reports/UNCONNECTED_BEFORE_FINAL.csv"
PY = ["/usr/bin/python3.10"]  # documentation: pcbnew host

F_NETS = {
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
}
SIM_NETS = {
    "SIM_RST",
    "SIM_CLK",
    "SIM_IO",
    "SIM_1V8",
    "SIM_VCC",
    "SIM_CLK_C",
    "SIM_RST_C",
    "SIM_IO_C",
}
C_NETS = {"ANT_FIT", "AUX", "AUX_FIT", "ANT", "GPS"}
SWD_NETS = {"SWDCLK", "ENABLE", "nRESET", "nRESET_SW", "SWDIO"}
POWER_NETS = {
    "VDD1",
    "VDD2",
    "VDD2_MID",
    "DEC0",
    "VIN_IN",
    "VIN_F",
    "VIN_FILT",
    "VDD_GPIO",
}
FANOUT_NEED = [
    "P0.01",
    "P0.04",
    "P0.06",
    "P0.09",
    "P0.11",
    "P0.14",
    "P0.16",
    "P0.18",
    "P0.20",
    "P0.22",
    "P0.24",
    "P0.27",
    "P0.29",
    "P0.31",
    "MAGPIO0",
    "MIPI_VIO",
    "MIPI_SCLK",
    "MIPI_SDATA",
    "COEX1",
]
WEST_NORTH = {"MAGPIO0", "MAGPIO1", "MAGPIO2", "MIPI_VIO", "MIPI_SCLK", "MIPI_SDATA"}


def net_of(desc: str) -> str:
    m = re.search(r"\[([^\]]+)\]", desc)
    return m.group(1) if m else ""


def is_pth_desc(desc: str) -> bool:
    return "PTH pad" in desc


def is_u1_desc(desc: str) -> bool:
    return " of U1" in desc


def classify_pair(n: str, da: str, db: str) -> str:
    if n == "GND" or da.startswith("Zone") or db.startswith("Zone"):
        return "E"
    if n in C_NETS:
        return "C"
    if n in F_NETS:
        return "F"
    if n in SIM_NETS:
        if is_u1_desc(da) or is_u1_desc(db):
            return "A"
        return "F"
    if n == "VDD_GPIO":
        if is_pth_desc(da) and is_pth_desc(db):
            return "G"
        return "A"
    if n.startswith(("P0.", "MAGPIO", "MIPI", "COEX")):
        if is_pth_desc(da) and is_pth_desc(db):
            return "G"
        return "A"
    return "A"


class Final(Router):
    def collect(self):
        super().collect()
        self.pads = [p for p in self.pads if p["num"] or p["pth"] or p["npth"]]
        bn = defaultdict(list)
        for p in self.pads:
            if p["name"]:
                bn[p["name"]].append(p)
        self.by_net = bn
        self.col_i = 0
        self.east_cols = [64.70 + i * 0.50 for i in range(22)]
        self.west_cols = [25.10, 25.55, 26.00, 26.45, 26.90]
        self.north_ys = [8.20 + i * 0.45 for i in range(18)]
        self.south_ys = [74.00, 73.40, 72.80, 71.60, 70.80, 66.20, 65.60, 64.80]
        self.stub_ys = [77.40, 77.65, 77.90, 78.15]

    def track_clear(self, x1, y1, x2, y2, layer, width, name):
        """Stricter than parent: DRC min clearance is 0.15 mm."""
        saved = self.pads
        self.pads = [p for p in saved if p["num"] or p["pth"] or p["npth"]]
        try:
            if hypot(x1, y1, x2, y2) < 0.03:
                return True
            need = width / 2 + (0.13 if layer == pcbnew.B_Cu else 0.16)
            if layer == pcbnew.B_Cu and name not in RF_OK:
                n = max(1, int(hypot(x1, y1, x2, y2) / 0.35))
                for k in range(n + 1):
                    t = k / n
                    x = x1 + t * (x2 - x1)
                    y = y1 + t * (y2 - y1)
                    if in_box(x, y, RF_BOX):
                        return False
                    if name not in ADC and in_box(x, y, J18_BOX):
                        return False
            from complete_route import dist_seg, dist_seg_aabb, seg_seg

            for p in self.pads:
                if p["npth"]:
                    if dist_seg(p["x"], p["y"], x1, y1, x2, y2) < p["r"] + 0.22:
                        return False
                    continue
                if p["name"] == name:
                    continue
                if not (layer == pcbnew.F_Cu or p["pth"]):
                    continue
                d = dist_seg_aabb(p["x"], p["y"], p["sx"], p["sy"], x1, y1, x2, y2)
                if d < need:
                    return False
            for v in self.vias:
                if v["n"] == name:
                    continue
                d = dist_seg(v["x"], v["y"], x1, y1, x2, y2)
                vneed = need
                if v["n"].startswith(("VDD", "VIN")) or v["n"] in RF_NETS:
                    vneed = width / 2 + 0.18
                if d < v["r"] + vneed:
                    return False
                if d < v["drill"] + 0.28 + width / 2:
                    return False
            for t in self.tracks:
                if t["ly"] != layer or t["n"] == name:
                    continue
                if seg_seg((x1, y1), (x2, y2), (t["x1"], t["y1"]), (t["x2"], t["y2"])) < need + t["w"] / 2:
                    return False
            return True
        finally:
            self.pads = saved

    def pad(self, ref, num=None, net=None):
        for p in self.pads:
            if p["ref"] != ref:
                continue
            if num is not None and p["num"] != str(num):
                continue
            if net is not None and p["name"] != net:
                continue
            if not p["num"] and not p["pth"]:
                continue
            return p
        return None

    def u1(self, name):
        for p in self.pads:
            if p["ref"] == "U1" and p["name"] == name:
                return p
        return None

    def nearest_via(self, name, x, y, limit=8.0):
        vias = [v for v in self.vias if v["n"] == name]
        if not vias:
            return None
        v = min(vias, key=lambda q: hypot(q["x"], q["y"], x, y))
        if limit is not None and hypot(v["x"], v["y"], x, y) > limit:
            return None
        return v

    def code_of(self, name):
        net = self.board.FindNet(name)
        return net.GetNetCode() if net else 0

    def local_w(self, name, w=None):
        if w is not None:
            return w
        if name in RF_NETS or name == "GNSS_VBIAS":
            return 0.20
        if name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC")):
            return 0.25
        return 0.18

    def fcommit(self, pts, name, w=None):
        w = self.local_w(name, w)
        return self.commit(pts, pcbnew.F_Cu, w, self.code_of(name), name)

    def bcommit(self, pts, name, w=None):
        w = self.local_w(name, w)
        return self.commit(pts, pcbnew.B_Cu, w, self.code_of(name), name)

    def jogs(self, x1, y1, x2, y2, extra=()):
        out = [
            [(x1, y1), (x2, y2)],
            [(x1, y1), (x2, y1), (x2, y2)],
            [(x1, y1), (x1, y2), (x2, y2)],
        ]
        ds = list(extra) + [
            -0.35,
            0.35,
            -0.70,
            0.70,
            -1.10,
            1.10,
            -1.60,
            1.60,
            -2.20,
            2.20,
            -3.20,
            3.20,
            -4.40,
            4.40,
            -6.00,
            6.00,
            -8.50,
            8.50,
            -12.0,
            12.0,
        ]
        for d in ds:
            out.append([(x1, y1), (x1, y1 + d), (x2, y1 + d), (x2, y2)])
            out.append([(x1, y1), (x1 + d, y1), (x1 + d, y2), (x2, y2)])
            out.append([(x1, y1), (x1, y2 + d), (x2, y2 + d), (x2, y2)])
        return out

    def route_f_any(self, x1, y1, x2, y2, name, w=None, astar=False):
        w = self.local_w(name, w)
        code = self.code_of(name)
        for pts in self.jogs(x1, y1, x2, y2):
            if self.commit(pts, pcbnew.F_Cu, w, code, name):
                return True
        if astar and hypot(x1, y1, x2, y2) < 28:
            return self.astar_f(x1, y1, x2, y2, name, w, code)
        return False

    def take_east(self):
        x = self.east_cols[self.col_i % len(self.east_cols)]
        self.col_i += 1
        return x

    def private_paths(self, x1, y1, x2, y2, name):
        """Orthogonal private B.Cu corridors. No RF keepout, no reused y=69–72 dump."""
        paths = []
        adc = name in ADC
        # Prefer originating at the south GPIO header.
        if y2 > 70 and y1 <= 70:
            x1, y1, x2, y2 = x2, y2, x1, y1
        stub = self.stub_ys[self.col_i % len(self.stub_ys)]
        if y1 > 70:
            if x1 < 56:
                for col in self.west_cols:
                    for yb in (66.40, 65.80, 67.00, 64.80):
                        paths.append(
                            [(x1, y1), (x1, stub), (col, stub), (col, yb), (col, y2), (x2, y2)]
                            if y2 < 64
                            else [(x1, y1), (x1, stub), (col, stub), (col, y2), (x2, y2)]
                        )
                        paths.append([(x1, y1), (x1, stub), (x2, stub), (x2, y2)])
                        paths.append([(x1, y1), (x1, 74.00), (col, 74.00), (col, y2), (x2, y2)])
            else:
                col = self.take_east()
                for ygate in (74.00, 73.40, 72.80):
                    paths.append([(x1, y1), (x1, stub), (x1, ygate), (col, ygate), (col, y2), (x2, y2)])
                    paths.append([(x1, y1), (x1, stub), (x2, stub), (x2, y2)])
                    paths.append([(x1, y1), (x1, ygate), (x2, ygate), (x2, y2)])
        if x1 > 100 or x2 > 100:
            for xf in (110.6, 111.2, 111.8, 112.4, 105.6, 106.2, 102.4, 101.6):
                for yn in self.north_ys[:10]:
                    paths.append([(x1, y1), (xf, y1), (xf, yn), (x2, yn), (x2, y2)])
                for yb in (58.80, 57.60, 40.40, 38.80, 68.80, 69.40):
                    paths.append([(x1, y1), (xf, y1), (xf, yb), (x2, yb), (x2, y2)])
        if name in WEST_NORTH:
            for yn in self.north_ys:
                for xf in (105.4, 106.0, 110.8, 111.4):
                    paths.append([(x1, y1), (x1, yn), (xf, yn), (xf, y2), (x2, y2)])
        if adc:
            for yb in (58.80, 58.20, 57.40):
                paths.append([(x1, y1), (x1, yb), (x2, yb), (x2, y2)])
        for yb in (45.20, 44.60, 43.80, 42.80, 14.80, 13.60, 12.40, 10.80, 9.40, 8.40):
            paths.append([(x1, y1), (x1, yb), (x2, yb), (x2, y2)])
        for xc in self.east_cols[:12] + self.west_cols:
            paths.append([(x1, y1), (xc, y1), (xc, y2), (x2, y2)])
        paths.append([(x1, y1), (x2, y1), (x2, y2)])
        paths.append([(x1, y1), (x1, y2), (x2, y2)])
        return paths

    def route_b_any(self, x1, y1, x2, y2, name, w=None, astar=True):
        w = self.local_w(name, w)
        code = self.code_of(name)
        if y2 > 70 and y1 <= 70:
            x1, y1, x2, y2 = x2, y2, x1, y1
        for pts in self.private_paths(x1, y1, x2, y2, name):
            if self.commit(pts, pcbnew.B_Cu, w, code, name):
                return True
        if astar:
            return self.astar_b(x1, y1, x2, y2, name, w, code)
        return False

    def join_f(self, a, b, name=None):
        if not a or not b:
            return False
        name = name or a["name"]
        return self.route_f_any(a["x"], a["y"], b["x"], b["y"], name)

    def via_f(self, x, y, name, pwr=None):
        if pwr is None:
            pwr = name.startswith(("VDD", "VIN")) or name in ("SIM_1V8", "SIM_VCC", "DEC0")
        if not self.via_ok(x, y, name, pwr=pwr):
            return None
        self.add_via(x, y, self.code_of(name), name, pwr=pwr)
        return x, y

    def search_via(self, x, y, name, pwr=None):
        if pwr is None:
            pwr = name.startswith(("VDD", "VIN"))
        site = self.local_via(x, y, name, pwr=pwr)
        if site:
            self.add_via(site[0], site[1], self.code_of(name), name, pwr=pwr)
            return site
        return None

    def oblong_escape(self, p, vx, vy, name):
        w = net_width(name)
        code = self.code_of(name)
        px, py = p["x"], p["y"]
        cands = []
        if name in WEST_NORTH:
            gate_y = 19.00
            for gx in (26.90, 26.40, 25.90, 27.40, 25.40):
                cands.append([(px, py), (gx, py), (gx, gate_y), (vx, gate_y), (vx, vy)])
            cands.append([(px, py), (px, gate_y), (vx, gate_y), (vx, vy)])
        elif p["sy"] > p["sx"] + 0.05 and vy < py:
            gy = 24.50
            cands.append([(px, py), (px, gy), (vx, gy), (vx, vy)])
            cands.append([(px, py), (vx, py), (vx, vy)])
        elif p["sy"] > p["sx"] + 0.05 and vy > py:
            gy = 39.80
            cands.append([(px, py), (px, gy), (vx, gy), (vx, vy)])
            cands.append([(px, py), (vx, py), (vx, vy)])
        elif p["sx"] > p["sy"] + 0.05 and vx > px:
            gx = 45.80
            cands.append([(px, py), (gx, py), (gx, vy), (vx, vy)])
            cands.append([(px, py), (px + 1.6, py), (px + 1.6, vy), (vx, vy)])
        elif p["sx"] > p["sy"] + 0.05 and vx < px:
            gx = 26.90
            cands.append([(px, py), (gx, py), (gx, vy), (vx, vy)])
        else:
            cands.append([(px, py), (vx, py), (vx, vy)])
            cands.append([(px, py), (px, vy), (vx, vy)])
        for pts in cands:
            if self.commit(pts, pcbnew.F_Cu, w, code, name):
                return True
        return self.route_f_any(px, py, vx, vy, name, w)

    def via_why(self, x, y, name, pwr=False, size=None, drill=None):
        """Return None if via is legal, else a blocker string. DRC-aligned (0.16 mm)."""
        from complete_route import in_box, dist_seg, U1_BOX, RF_BOX, J18_BOX, UFL, ADC, RF_OK, EDGE

        size = size if size is not None else (0.80 if pwr else 0.60)
        drill = drill if drill is not None else (0.40 if pwr else 0.30)
        if not (EDGE + 1.0 < x < self.w - EDGE - 1.0 and EDGE + 1.0 < y < self.h - EDGE - 1.0):
            return f"edge ({x:.2f},{y:.2f})"
        if in_box(x, y, U1_BOX):
            return f"U1_BOX ({x:.2f},{y:.2f})"
        if in_box(x, y, RF_BOX) and name not in RF_OK:
            return f"RF_BOX ({x:.2f},{y:.2f})"
        if in_box(x, y, J18_BOX) and name not in ADC:
            return f"J18_BOX ({x:.2f},{y:.2f})"
        if any(in_box(x, y, box) for box in UFL):
            return f"U.FL ({x:.2f},{y:.2f})"
        for p in self.pads:
            if p["name"] == name or not p["num"] and not p["pth"]:
                continue
            if p["pth"]:
                need = p["r"] + 0.20 + drill / 2
            else:
                need = max(p["sx"], p["sy"]) / 2 + size / 2 + 0.16
            d = hypot(p["x"], p["y"], x, y)
            if d < need:
                return f"pad {p['ref']}.{p['num']} {p['name']} d={d:.3f} need={need:.3f} @({p['x']:.2f},{p['y']:.2f})"
        for v in self.vias:
            need = 0.90 if v["n"] != name else 0.70
            d = hypot(v["x"], v["y"], x, y)
            if d < need:
                return f"via {v['n']} d={d:.3f} @({v['x']:.2f},{v['y']:.2f})"
        for t in self.tracks:
            if t["n"] == name:
                continue
            d = dist_seg(x, y, t["x1"], t["y1"], t["x2"], t["y2"])
            need = size / 2 + t["w"] / 2 + 0.15
            if d < need:
                ly = "F" if t["ly"] == pcbnew.F_Cu else "B"
                return (
                    f"trk {ly} {t['n']} d={d:.3f} ({t['x1']:.2f},{t['y1']:.2f})-"
                    f"({t['x2']:.2f},{t['y2']:.2f})"
                )
        return None

    def pad_reaches_via(self, p, v, name):
        """True if an F.Cu track of this net touches both the U1 pad and the via."""
        from complete_route import dist_seg

        pad_tracks = []
        via_tracks = []
        for t in self.tracks:
            if t["n"] != name or t["ly"] != pcbnew.F_Cu:
                continue
            if dist_seg(p["x"], p["y"], t["x1"], t["y1"], t["x2"], t["y2"]) < max(p["sx"], p["sy"]) / 2 + 0.12:
                pad_tracks.append(t)
            if dist_seg(v["x"], v["y"], t["x1"], t["y1"], t["x2"], t["y2"]) < 0.35:
                via_tracks.append(t)
        if not pad_tracks or not via_tracks:
            return False
        # same track, or endpoints coincide
        for a in pad_tracks:
            for b in via_tracks:
                if a is b:
                    return True
                for ax, ay in ((a["x1"], a["y1"]), (a["x2"], a["y2"])):
                    for bx, by in ((b["x1"], b["y1"]), (b["x2"], b["y2"])):
                        if hypot(ax, ay, bx, by) < 0.25:
                            return True
        return False

    def f_escape_to(self, p, sx, sy, name):
        px, py = p["x"], p["y"]
        extras = [
            [(px, py), (sx, sy)],
            [(px, py), (px, sy), (sx, sy)],
            [(px, py), (sx, py), (sx, sy)],
        ]
        if p["sy"] > p["sx"] + 0.05:
            gy = 39.70 if sy > py else 25.30
            extras.append([(px, py), (px, gy), (sx, gy), (sx, sy)])
        if p["sx"] > p["sy"] + 0.05:
            gx = 45.20 if sx > px else 26.85
            extras.append([(px, py), (gx, py), (gx, sy), (sx, sy)])
        code = self.code_of(name)
        for pts in extras:
            if self.commit(pts, pcbnew.F_Cu, 0.18, code, name):
                return True
            if self.commit(pts, pcbnew.F_Cu, 0.15, code, name):
                return True
        if self.oblong_escape(p, sx, sy, name):
            return True
        if self.route_f_any(px, py, sx, sy, name, 0.18, astar=False):
            return True
        if hypot(px, py, sx, sy) < 8:
            if self.route_f_any(px, py, sx, sy, name, 0.18, astar=True):
                return True
            if self.route_f_any(px, py, sx, sy, name, 0.15, astar=True):
                return True
        return False

    def extra_fanout_one(self, name, log):
        """Place a new via 1.15–2.1 mm (then farther) outside U1 on the true oblong axis.

        Tries 0.60/0.30 then board-min 0.50/0.30. Does not skip after one failed point.
        Existing courtyard vias <1.1 mm are ignored. Via is added only after F.Cu escape.
        """
        from complete_route import in_box, U1_BOX

        p = self.u1(name)
        if not p:
            log.append((name, None, "no U1 pad"))
            print(f"  no U1 pad {name}")
            return None

        existing = [v for v in self.vias if v["n"] == name]
        for v in sorted(existing, key=lambda q: hypot(q["x"], q["y"], p["x"], p["y"])):
            d = hypot(v["x"], v["y"], p["x"], p["y"])
            if not (1.10 <= d <= 8.00) or in_box(v["x"], v["y"], U1_BOX):
                continue
            if self.pad_reaches_via(p, v, name):
                log.append((name, (v["x"], v["y"], d), "existing-outside"))
                print(f"  KEEP {name} via ({v['x']:.2f},{v['y']:.2f}) d={d:.2f}")
                return (v["x"], v["y"], d, "existing")
            if self.f_escape_to(p, v["x"], v["y"], name):
                log.append((name, (v["x"], v["y"], d), "linked-existing"))
                print(f"  LINK {name} via ({v['x']:.2f},{v['y']:.2f}) d={d:.2f}")
                return (v["x"], v["y"], d, "linked")

        # True oblong outward (not the even-pad 0.95 mm ring target).
        if p["sx"] > p["sy"] + 0.05:
            ux, uy = (-1.0, 0.0) if p["x"] < 36 else (1.0, 0.0)
        elif p["sy"] > p["sx"] + 0.05:
            ux, uy = (0.0, -1.0) if p["y"] < 32 else (0.0, 1.0)
        else:
            ux, uy = (1.0, 0.0)
        px, py = -uy, ux
        cands = []
        if name == "P0.11":
            cands.append((45.20, 28.00, 1.20, "stub"))
        if name in WEST_NORTH:
            for x in (26.85, 26.70, 26.50, 26.30, 25.90, 25.70, 25.40):
                for y in (p["y"], p["y"] + 0.40, p["y"] - 0.40, p["y"] + 1.20, p["y"] + 1.60, 28.90, 19.20, 18.90, 18.40):
                    cands.append((x, y, hypot(x, y, p["x"], p["y"]), "west-north"))
        for rad in (1.15, 1.40, 1.70, 2.10, 2.20, 2.40, 2.55, 2.80, 3.30, 3.70, 4.80, 5.20):
            cands.append((p["x"] + ux * rad, p["y"] + uy * rad, rad, "oblong"))
        for rad in (1.15, 1.40, 1.70, 2.10, 2.20, 2.40, 2.55, 2.80, 3.30, 3.70, 4.80, 5.20):
            for k in range(1, 13):
                ang = math.radians(k * 15)
                cands.append(
                    (
                        p["x"] + rad * (ux * math.cos(ang) + px * math.sin(ang)),
                        p["y"] + rad * (uy * math.cos(ang) + py * math.sin(ang)),
                        rad,
                        f"a{k * 15}",
                    )
                )

        blockers = []
        f_fail = []
        sizes = ((0.60, 0.30, "v06"), (0.50, 0.30, "v05"))
        for sx, sy, rad, tag in cands:
            placed = False
            for size, drill, stag in sizes:
                why = self.via_why(sx, sy, name, pwr=False, size=size, drill=drill)
                if why:
                    if len(blockers) < 20 and stag == "v05":
                        blockers.append(f"{tag} r={rad:.2f} ({sx:.2f},{sy:.2f}): {why}")
                    continue
                if self.f_escape_to(p, sx, sy, name):
                    self.add_via(sx, sy, p["code"], name, pwr=False, size=size, drill=drill)
                    log.append((name, (sx, sy, rad), f"added {tag} {stag}"))
                    print(f"  VIA {name} ({sx:.2f},{sy:.2f}) r={rad:.2f} {tag} {stag} {size:.2f}/{drill:.2f}")
                    return (sx, sy, rad, f"{tag}-{stag}")
                placed = True
            if placed and len(f_fail) < 8:
                f_fail.append(f"{tag} r={rad:.2f} ({sx:.2f},{sy:.2f})")
        log.append((name, None, "NOVIA " + " | ".join(blockers[:4]) + " Ffail=" + ";".join(f_fail[:4])))
        print(f"  NOVIA/Ffail {name}")
        for b in blockers[:6]:
            print(f"    {b}")
        for b in f_fail[:4]:
            print(f"    Ffail {b}")
        return None

    def fanout_one(self, name):
        p = self.u1(name)
        if not p:
            print(f"  no U1 pad {name}")
            return False
        existing = self.nearest_via(name, p["x"], p["y"], limit=6.5)
        if existing:
            if not self.connected_to_track(p, name):
                self.oblong_escape(p, existing["x"], existing["y"], name)
            return True
        pwr = name.startswith(("VDD", "VIN"))
        sites = []
        if name in WEST_NORTH:
            for x in (26.90, 26.40, 25.90, 27.40, 28.00, 25.40):
                for y in (18.80, 18.20, 17.60, 19.20, 16.90):
                    sites.append((x, y))
        else:
            ex, ey = self.radial_end(p)
            dx, dy = ex - p["x"], ey - p["y"]
            for scale in (1.15, 1.45, 1.75, 2.10, 2.50):
                sites.append((p["x"] + dx * scale, p["y"] + dy * scale))
            for s in (-1.15, 1.15, -2.10, 2.10, -0.95, 0.95):
                if abs(dx) > abs(dy):
                    sites.append((ex, ey + s))
                    sites.append((ex + (1.15 if dx > 0 else -1.15), ey + s))
                else:
                    sites.append((ex + s, ey))
                    sites.append((ex + s, ey + (1.15 if dy > 0 else -1.15)))
        site = None
        for sx, sy in sites:
            if self.via_ok(sx, sy, name, pwr=pwr):
                site = (sx, sy)
                break
        if not site:
            site = self.local_via(p["x"], p["y"], name, pwr=pwr)
        if not site:
            print(f"  NOVIA {name}")
            return False
        if self.oblong_escape(p, site[0], site[1], name) or self.connected_to_track(p, name):
            self.add_via(site[0], site[1], p["code"], name, pwr=pwr)
            print(f"  via {name} ({site[0]:.2f},{site[1]:.2f})")
            return True
        print(f"  FANOUT fail {name} site=({site[0]:.2f},{site[1]:.2f})")
        return False

    def primary_header(self, name):
        cands = []
        for p in self.pads:
            if p["name"] != name or not p["pth"]:
                continue
            if p["ref"] in ("J12", "J13") and p["y"] > 70:
                score = 3
            elif p["ref"] in ("J9", "J10", "J11", "J16", "J17", "J14", "J15"):
                score = 2
            elif p["ref"] == "J18":
                score = 1
            else:
                score = 0
            cands.append((-score, hypot(p["x"], p["y"], 36, 32), p))
        if not cands:
            return None
        cands.sort(key=lambda t: (t[0], t[1]))
        return cands[0][2]

    def extras(self, name, skip):
        return [p for p in self.pads if p["name"] == name and p["pth"] and p is not skip]

    # B.Cu free Y bands between the packed highways (P0.01 y=15.2, P0.15 y=20.6,
    # COEX2 y=24.6, COEX0 y=44.4/58.8/62.0, ADC y=72.8–74.0, stubs y=77.45).
    B_BANDS = [
        (8.40, 14.40),
        (16.30, 19.70),
        (21.50, 23.80),
        (25.40, 26.20),
        (28.00, 43.40),
        (45.50, 57.40),
        (65.40, 71.60),
        (75.30, 76.50),
        (77.90, 79.10),
    ]
    B_COLS = [25.10, 25.55, 65.20, 65.80, 70.90, 75.50, 80.40, 96.50, 107.50, 110.90, 112.20]

    def corridor_paths(self, x1, y1, x2, y2, name):
        """Orthogonal B.Cu paths that hop known highways instead of crossing them."""
        paths = []
        stub = 78.15
        east = 107.50  # east of P0.15 x=106 and COEX2 x=105.10
        mid = 70.90  # east of COEX0 H y=44.4 (ends x=64.60)
        west = 25.10  # east of RF keepout x=24.2, west of P0.01 x=27.65
        # Prefer header as the start so stubs stay short.
        if y2 > 70 and y1 <= 70:
            x1, y1, x2, y2 = x2, y2, x1, y1
        if y1 > 70:
            # Primary header at y=76: stub east/west then south-around via east column.
            paths.append([(x1, y1), (x1, stub), (east, stub), (east, 57.20), (mid, 57.20), (mid, y2), (x2, y2)])
            paths.append([(x1, y1), (x1, stub), (east, stub), (east, y2), (x2, y2)])
            paths.append([(x1, y1), (x1, stub), (west, stub), (west, 12.50), (x2, 12.50), (x2, y2)])
            if x1 < 55:
                paths.append([(x1, y1), (x1, stub), (west, stub), (west, 66.20), (mid, 66.20), (mid, y2), (x2, y2)])
            if x1 > 100:
                paths.append([(x1, y1), (east, y1), (east, stub), (east, 57.20), (x2, 57.20), (x2, y2)])
                paths.append([(x1, y1), (east, y1), (east, 12.50), (x2, 12.50), (x2, y2)])
        if name in WEST_NORTH:
            paths.append([(x1, y1), (x1, 12.50), (east, 12.50), (east, y2), (x2, y2)])
            paths.append([(x1, y1), (west, y1), (west, 12.50), (east, 12.50), (east, y2), (x2, y2)])
            paths.append([(x1, y1), (x1, 18.40), (west, 18.40), (west, 12.50), (east, 12.50), (east, y2), (x2, y2)])
        # Generic: mid column (skips COEX0 y=44.4) then east hop around COEX0 y=62.
        paths.append([(x1, y1), (mid, y1), (mid, 57.20), (east, 57.20), (east, y2), (x2, y2)])
        paths.append([(x1, y1), (mid, y1), (mid, 36.50), (east, 36.50), (east, y2), (x2, y2)])
        paths.append([(x1, y1), (x1, 36.50), (mid, 36.50), (mid, 57.20), (east, 57.20), (east, stub), (x2, stub), (x2, y2)])
        paths.append([(x1, y1), (x1, 12.50), (east, 12.50), (east, y2), (x2, y2)])
        paths.append([(x1, y1), (west, y1), (west, 12.50), (east, 12.50), (east, y2), (x2, y2)])
        if name in ADC:
            paths.append([(x1, y1), (x1, 58.40), (x2, 58.40), (x2, y2)])
            paths.append([(x1, y1), (mid, y1), (mid, 58.40), (x2, 58.40), (x2, y2)])
        return paths

    def route_b_corridor(self, x1, y1, x2, y2, name, w=None):
        w = self.local_w(name, w)
        code = self.code_of(name)
        for pts in self.corridor_paths(x1, y1, x2, y2, name):
            if self.commit(pts, pcbnew.B_Cu, w, code, name):
                return True
        return self.astar_b(x1, y1, x2, y2, name, w, code)

    def join_pair(self, p, astar=False):
        name = p["net"]
        if not name or name in SKIP or name == "GND":
            return False
        x1, y1, x2, y2 = p["ax"], p["ay"], p["bx"], p["by"]
        d = hypot(x1, y1, x2, y2)
        if d < 0.05:
            return False
        w = self.local_w(name)
        both_f = p["a_f"] and p["b_f"] and not (p["a_pth"] and p["b_pth"] and d > 10)
        if both_f and d < 28:
            if self.route_f_any(x1, y1, x2, y2, name, w, astar=False):
                return True
        use_b = name.startswith(("P0.", "MAGPIO", "MIPI", "COEX", "SIM", "VDD_GPIO", "SWD", "nRESET", "ENABLE")) or p[
            "a_pth"
        ] or p["b_pth"] or p["a_via"] or p["b_via"] or p["a_b"] or p["b_b"]
        if use_b:
            if self.route_b_corridor(x1, y1, x2, y2, name, w):
                return True
            if self.route_b_any(x1, y1, x2, y2, name, w, astar=astar):
                return True
        if self.route_f_any(x1, y1, x2, y2, name, w, astar=astar):
            return True
        return False


def parse_drc(path):
    data = json.load(open(path))
    vios = data.get("violations", [])
    counts = defaultdict(int)
    for v in vios:
        counts[v.get("type", "")] += 1
    pairs = []
    for u in data.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        n = net_of(a["description"]) or net_of(b["description"])
        pairs.append(
            {
                "net": n,
                "cls": classify_pair(n, a["description"], b["description"]),
                "a": a["description"],
                "b": b["description"],
                "ax": a["pos"]["x"],
                "ay": a["pos"]["y"],
                "bx": b["pos"]["x"],
                "by": b["pos"]["y"],
                "a_pth": is_pth_desc(a["description"]),
                "b_pth": is_pth_desc(b["description"]),
                "a_via": "Via" in a["description"],
                "b_via": "Via" in b["description"],
                "a_f": "F.Cu" in a["description"] or is_pth_desc(a["description"]),
                "b_f": "F.Cu" in b["description"] or is_pth_desc(b["description"]),
                "a_b": "B.Cu" in a["description"] or is_pth_desc(a["description"]) or "Via" in a["description"],
                "b_b": "B.Cu" in b["description"] or is_pth_desc(b["description"]) or "Via" in b["description"],
            }
        )
    return pairs, len(data.get("unconnected_items", [])), counts, data


def run_drc():
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", DRC_JSON, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return parse_drc(DRC_JSON)


def fatal(counts, baseline):
    shorts = counts.get("shorting_items", 0)
    hole = counts.get("hole_clearance", 0)
    clr = counts.get("clearance", 0)
    if shorts > 0:
        return f"shorts={shorts}"
    if hole > baseline.get("hole_clearance", 0):
        return f"hole_clearance {hole}>{baseline.get('hole_clearance', 0)}"
    if clr > max(baseline.get("clearance", 0), 1):
        return f"clearance {clr}>{baseline.get('clearance', 0)}"
    return None


def save_and_check(board, r, label, baseline, last_good):
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(f"  DRC [{label}] unconnected={n} shorts={counts.get('shorting_items', 0)} "
          f"clear={counts.get('clearance', 0)} hole={counts.get('hole_clearance', 0)} "
          f"ok={r.ok} fail={r.fail}", flush=True)
    why = fatal(counts, baseline)
    if why:
        print(f"ABORT {why}; restoring {last_good}")
        shutil.copy2(last_good, BOARD)
        return None, n, counts
    snap = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
    shutil.copy2(BOARD, snap)
    return pairs, n, counts


def fill_zones(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def load():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    return board, r


def phase_power(r: Final):
    print("== power F.Cu ==", flush=True)
    # VDD1 C6–C3 gap around C6 GND
    c3, c6 = r.pad("C3", "1"), r.pad("C6", "1")
    if c3 and c6:
        pts = [(c6["x"], c6["y"]), (c6["x"], 26.00), (c3["x"], 26.00)]
        if not r.fcommit(pts, "VDD1"):
            r.join_f(c6, c3, "VDD1")
    r.join_f(r.u1("VDD1"), r.pad("C4", "1"), "VDD1")
    r.join_f(r.pad("C4", "1"), r.pad("C5", "1"), "VDD1")
    r.join_f(r.pad("C5", "1"), r.pad("C6", "1"), "VDD1")
    r.join_f(r.pad("C6", "1"), r.pad("R1", "1"), "VDD1")
    r.join_f(r.pad("R1", "1"), r.pad("FB1", "2"), "VDD1")

    # VDD2 U1 pad 22 to C8 / via (52.22,32)
    u22, c8 = r.u1("VDD2"), r.pad("C8", "1")
    if u22 and c8:
        pts = [(u22["x"], u22["y"]), (46.60, u22["y"]), (46.60, c8["y"]), (c8["x"], c8["y"])]
        if not r.fcommit(pts, "VDD2"):
            r.join_f(u22, c8, "VDD2")
    via = r.nearest_via("VDD2", 52.22, 32.00, limit=2.0)
    if u22 and via:
        r.route_f_any(u22["x"], u22["y"], via["x"], via["y"], "VDD2")
    r.join_f(r.pad("C8", "1"), r.pad("C9", "1"), "VDD2")
    r.join_f(r.pad("C9", "1"), r.pad("C10", "1"), "VDD2")
    r.join_f(r.pad("C9", "1"), r.pad("C7", "1"), "VDD2")
    r.join_f(r.pad("C7", "1"), r.pad("FB3", "2"), "VDD2")
    # VDD2 leftover islands near (60,42) / FB3
    r.join_f(r.pad("C10", "1"), r.pad("C9", "1"), "VDD2")

    fb2, fb3 = r.pad("FB2", "2"), r.pad("FB3", "1")
    if fb2 and fb3:
        for yj in (18.00, 17.20, 16.50, 19.00, 19.60):
            pts = [(fb2["x"], fb2["y"]), (fb2["x"], yj), (fb3["x"], yj), (fb3["x"], fb3["y"])]
            if r.fcommit(pts, "VDD2_MID"):
                break
        else:
            r.join_f(fb2, fb3, "VDD2_MID")

    c13 = r.pad("C13", "1")
    u13 = r.u1("DEC0")
    if c13 and u13:
        pts = [(u13["x"], u13["y"]), (c13["x"], u13["y"]), (c13["x"], c13["y"])]
        r.fcommit(pts, "DEC0")
    if c13:
        via = r.nearest_via("DEC0", 48.65, 21.13, limit=4)
        if via:
            for xj in (51.20, 51.80, 47.10, 46.40):
                pts = [(c13["x"], c13["y"]), (xj, c13["y"]), (xj, via["y"]), (via["x"], via["y"])]
                if r.fcommit(pts, "DEC0"):
                    break
            else:
                r.route_f_any(c13["x"], c13["y"], via["x"], via["y"], "DEC0")

    # VIN
    d1, j1 = r.pad("D1", "1"), r.pad("J1", "1", "VIN_IN")
    if d1 and j1:
        for yj in (10.00, 8.40, 6.80, 11.40):
            pts = [(d1["x"], d1["y"]), (d1["x"], yj), (j1["x"], yj), (j1["x"], j1["y"])]
            if r.fcommit(pts, "VIN_IN"):
                break
        else:
            if not r.join_f(d1, j1, "VIN_IN"):
                r.route_b_any(d1["x"], d1["y"], j1["x"], j1["y"], "VIN_IN")
    f1, fb4 = r.pad("F1", "2"), r.pad("FB4", "1")
    if f1 and fb4:
        if not r.join_f(f1, fb4, "VIN_F"):
            v1 = r.nearest_via("VIN_F", f1["x"], f1["y"], 4)
            v2 = r.nearest_via("VIN_F", fb4["x"], fb4["y"], 4)
            if v1 and v2:
                r.route_b_any(v1["x"], v1["y"], v2["x"], v2["y"], "VIN_F")
    jp1 = r.pad("JP1", "1")
    if jp1:
        via = r.nearest_via("VIN_FILT", 55.35, 13.30, 3)
        tgt = r.pad("R2", "1")
        if via and tgt:
            for pts in (
                [(via["x"], via["y"]), (52.00, via["y"]), (52.00, tgt["y"]), (tgt["x"], tgt["y"])],
                [(via["x"], via["y"]), (via["x"], 22.00), (52.00, 22.00)],
            ):
                if r.fcommit(pts, "VIN_FILT"):
                    break
            else:
                r.route_f_any(via["x"], via["y"], tgt["x"], tgt["y"], "VIN_FILT")
        r.join_f(r.pad("FB4", "2"), tgt, "VIN_FILT")

    # VDD_GPIO local star
    u12, c12, u2 = r.u1("VDD_GPIO"), r.pad("C12", "1"), r.pad("U2", "5")
    if u12 and c12:
        pts = [(u12["x"], u12["y"]), (46.60, u12["y"]), (46.60, c12["y"]), (c12["x"], c12["y"])]
        if not r.fcommit(pts, "VDD_GPIO"):
            r.join_f(u12, c12, "VDD_GPIO")
    r.join_f(c12, u2, "VDD_GPIO")
    r.join_f(u2, r.pad("TP10", "1"), "VDD_GPIO")
    # FB5 wrap south of RF, never along GNSS_ANT y≈46.8 spine
    fb5 = r.pad("FB5", "1")
    if fb5:
        site = None
        for cand in ((25.60, 66.20), (26.10, 66.80), (25.10, 67.40), (27.20, 66.20)):
            if r.via_ok(cand[0], cand[1], "VDD_GPIO", pwr=True):
                site = cand
                break
        if site:
            pts = [
                (fb5["x"], fb5["y"]),
                (fb5["x"], site[1]),
                (site[0], site[1]),
            ]
            # Stay at x=14 (west of GNSS spine ~16) then east at y>=66
            pts = [
                (fb5["x"], fb5["y"]),
                (14.00, 64.40),
                (site[0], 64.40),
                site,
            ]
            if r.fcommit(pts, "VDD_GPIO", 0.40):
                r.add_via(site[0], site[1], r.code_of("VDD_GPIO"), "VDD_GPIO", pwr=True)
                print("  FB5 VDD_GPIO via", site)
            else:
                print("  FB5 wrap F fail; trying pieces")
                if r.route_f_any(fb5["x"], fb5["y"], site[0], site[1], "VDD_GPIO", 0.40):
                    r.add_via(site[0], site[1], r.code_of("VDD_GPIO"), "VDD_GPIO", pwr=True)


def phase_sim(r: Final):
    print("== SIM ==", flush=True)
    pairs = [
        ("SIM_RST", r.pad("C36", "1"), r.pad("U4", "6")),
        ("SIM_RST", r.pad("C36", "1"), r.pad("TP4", "1")),
        ("SIM_CLK", r.pad("C35", "1"), r.pad("U4", "7")),
        ("SIM_IO", r.pad("C37", "1"), r.pad("U4", "8")),
        ("SIM_1V8", r.pad("C38", "1"), r.pad("U4", "5")),
        ("SIM_1V8", r.pad("C33", "1"), r.pad("C38", "1")),
        ("SIM_1V8", r.pad("C33", "1"), r.pad("JP2", "1")),
        ("SIM_VCC", r.pad("C34", "1"), r.pad("JP2", "2")),
        ("SIM_VCC", r.pad("J7", None, "SIM_VCC"), r.pad("C34", "1")),
        ("SIM_CLK_C", r.pad("U4", "2"), r.pad("J7", None, "SIM_CLK_C")),
        ("SIM_RST_C", r.pad("U4", "3"), r.pad("J7", None, "SIM_RST_C")),
        ("SIM_IO_C", r.pad("U4", "1"), r.pad("J7", None, "SIM_IO_C")),
    ]
    for net, a, b in pairs:
        if a and b:
            if not r.join_f(a, b, net):
                va = r.nearest_via(net, a["x"], a["y"], 6)
                vb = r.nearest_via(net, b["x"], b["y"], 6)
                if va and vb and hypot(va["x"], va["y"], vb["x"], vb["y"]) > 0.8:
                    r.route_b_any(va["x"], va["y"], vb["x"], vb["y"], net)
                elif not r.route_b_any(a["x"], a["y"], b["x"], b["y"], net):
                    print(f"  SIM fail {net} {a['ref']}-{b['ref']}")

    # U1 SIM to island vias (already have courtyard vias for CLK/IO)
    for name in ("SIM_CLK", "SIM_IO", "SIM_RST", "SIM_1V8"):
        p = r.u1(name)
        if not p:
            continue
        v = r.nearest_via(name, p["x"], p["y"], 7)
        if v and not r.connected_to_track(p, name):
            r.oblong_escape(p, v["x"], v["y"], name)
        island = None
        for ref, num in (("C35", "1"), ("C36", "1"), ("C37", "1"), ("C38", "1"), ("U4", None)):
            q = r.pad(ref, num, name) if num else r.pad("U4", net=name)
            if q:
                island = q
                break
        v2 = r.nearest_via(name, 76, 50, 20)
        v1 = v or r.nearest_via(name, p["x"], p["y"], 12)
        if v1 and v2 and hypot(v1["x"], v1["y"], v2["x"], v2["y"]) > 2:
            if not r.route_b_any(v1["x"], v1["y"], v2["x"], v2["y"], name):
                print(f"  SIM B.Cu U1 fail {name}")
        elif p and island:
            r.route_b_any(p["x"], p["y"], island["x"], island["y"], name)


def phase_gnss(r: Final):
    print("== GNSS_VBIAS ==", flush=True)
    c28, c30, l4, fb5 = r.pad("C28", "1"), r.pad("C30", "1"), r.pad("L4", "1"), r.pad("FB5", "2")
    # Stay off GNSS_ANT spine x≈16–18.5 on the 50 Ω trunk; bias at x=17.52 is L4 pad 1.
    if c28 and c30:
        pts = [(c28["x"], c28["y"]), (c28["x"], 49.52), (c30["x"], 49.52), (c30["x"], c30["y"])]
        if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
            pts = [(c28["x"], c28["y"]), (12.05, c28["y"]), (12.05, c30["y"]), (c30["x"], c30["y"])]
            if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
                r.route_f_any(c28["x"], c28["y"], c30["x"], c30["y"], "GNSS_VBIAS", 0.20)
    if c30 and l4:
        pts = [(c30["x"], c30["y"]), (17.52, c30["y"]), (17.52, l4["y"]), (l4["x"], l4["y"])]
        if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
            r.route_f_any(c30["x"], c30["y"], l4["x"], l4["y"], "GNSS_VBIAS", 0.20)
    via = r.nearest_via("GNSS_VBIAS", 17.00, 38.00, 3)
    if l4 and via:
        r.route_f_any(l4["x"], l4["y"], via["x"], via["y"], "GNSS_VBIAS", 0.20)
    if fb5 and l4:
        # West of spine: x≈14 / 12.05 existing copper
        pts = [(l4["x"], l4["y"]), (14.00, l4["y"]), (14.00, fb5["y"]), (fb5["x"], fb5["y"])]
        if not r.fcommit(pts, "GNSS_VBIAS", 0.20):
            r.join_f(l4, fb5, "GNSS_VBIAS")
    r.join_f(r.pad("C28", "1"), r.pad("C29", "1"), "GNSS_VBIAS")


def phase_swd(r: Final):
    print("== SWD / ENABLE / nRESET ==", flush=True)
    c14, r1 = r.pad("C14", "1"), r.pad("R1", "2")
    if c14 and r1:
        pts = [(c14["x"], c14["y"]), (c14["x"], 21.30), (r1["x"], 21.30), (r1["x"], r1["y"])]
        if not r.fcommit(pts, "ENABLE"):
            r.join_f(c14, r1, "ENABLE")
    uen = r.u1("ENABLE")
    if r1 and uen:
        pts = [(r1["x"], r1["y"]), (46.40, r1["y"]), (46.40, uen["y"]), (uen["x"], uen["y"])]
        if not r.fcommit(pts, "ENABLE"):
            v = r.nearest_via("ENABLE", uen["x"], uen["y"], 6)
            if v:
                if r.route_f_any(r1["x"], r1["y"], v["x"], v["y"], "ENABLE"):
                    pass
                else:
                    r.route_b_any(r1["x"], r1["y"], v["x"], v["y"], "ENABLE")
    sw1, u2e = r.pad("SW1", "1"), r.pad("U2", "3")
    if sw1 and u2e:
        if not r.join_f(u2e, sw1, "ENABLE"):
            v = r.nearest_via("ENABLE", sw1["x"], sw1["y"], 4)
            v2 = r.nearest_via("ENABLE", u2e["x"], u2e["y"], 8)
            if v and v2:
                r.route_b_any(v["x"], v["y"], v2["x"], v2["y"], "ENABLE")
            else:
                r.route_b_any(sw1["x"], sw1["y"], u2e["x"], u2e["y"], "ENABLE")

    c39 = r.pad("C39", "1")
    u_nr = r.u1("nRESET")
    v_nr = r.nearest_via("nRESET", 38.25, 23.10, 4)
    if c39 and v_nr:
        pts = [(c39["x"], c39["y"]), (c39["x"], 14.80), (v_nr["x"], 14.80), (v_nr["x"], v_nr["y"])]
        if not r.fcommit(pts, "nRESET"):
            r.route_f_any(c39["x"], c39["y"], v_nr["x"], v_nr["y"], "nRESET")
    r5 = r.pad("R5", "1")
    v_r5 = r.nearest_via("nRESET", 103.30, 36.00, 4)
    if r5 and v_r5:
        r.route_f_any(r5["x"], r5["y"], v_r5["x"], v_r5["y"], "nRESET")
    if v_nr and v_r5:
        r.route_b_any(v_nr["x"], v_nr["y"], v_r5["x"], v_r5["y"], "nRESET")
    r.join_f(r.pad("R5", "2"), r.pad("SW2", "1"), "nRESET_SW")
    vsw = r.nearest_via("nRESET_SW", 99.67, 24.00, 4)
    if vsw and r.pad("R5", "2"):
        r.route_f_any(r.pad("R5", "2")["x"], r.pad("R5", "2")["y"], vsw["x"], vsw["y"], "nRESET_SW")

    # SWDCLK: parallel SWDIO F.Cu, not a 60 mm B.Cu tour
    uclk = r.u1("SWDCLK")
    j8 = r.pad("J8", "4")
    if uclk and j8:
        site = None
        for cand in ((37.75, 21.95), (37.75, 20.80), (38.30, 21.95), (37.20, 21.95)):
            if r.via_ok(cand[0], cand[1], "SWDCLK"):
                site = cand
                break
        pts = [(uclk["x"], uclk["y"]), (uclk["x"], 4.73), (j8["x"], 4.73)]
        if r.fcommit(pts, "SWDCLK"):
            print("  SWDCLK F.Cu direct")
        else:
            if site and r.oblong_escape(uclk, site[0], site[1], "SWDCLK"):
                r.add_via(site[0], site[1], r.code_of("SWDCLK"), "SWDCLK")
                r.route_f_any(site[0], site[1], j8["x"], j8["y"], "SWDCLK")
            else:
                r.route_f_any(uclk["x"], uclk["y"], j8["x"], j8["y"], "SWDCLK")


def phase_fanout(r: Final):
    print("== extra U1 vias ==", flush=True)
    for name in FANOUT_NEED:
        r.fanout_one(name)
    # P0.06 / P0.11 dangling F.Cu stubs: if stub exists without via, add via at stub end
    for name in ("P0.06", "P0.11"):
        p = r.u1(name)
        if not p:
            continue
        if r.nearest_via(name, p["x"], p["y"], 6.5):
            continue
        r.fanout_one(name)


def phase_gpio(r: Final):
    print("== private GPIO + header branches ==", flush=True)
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or p["name"] in ("VDD_GPIO", "P0.08")
        }
    )
    for name in nets:
        hdr = r.primary_header(name)
        p = r.u1(name)
        w = net_width(name)
        via = None
        if p:
            via = r.nearest_via(name, p["x"], p["y"], 7.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias and hdr:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
            elif vias:
                via = vias[0]
        if hdr and via:
            if r.route_b_any(via["x"], via["y"], hdr["x"], hdr["y"], name, w):
                print(f"  B {name} -> {hdr['ref']}.{hdr['num']}")
            else:
                print(f"  HIGHWAY fail {name}")
        elif hdr and p:
            if not r.route_b_any(p["x"], p["y"], hdr["x"], hdr["y"], name, w):
                print(f"  no-via GPIO fail {name}")
        if hdr:
            for extra in r.extras(name, hdr):
                ok = r.route_b_any(hdr["x"], hdr["y"], extra["x"], extra["y"], name, w)
                if not ok:
                    print(f"  extra PTH fail {name} {extra['ref']}.{extra['num']}")

    # VDD_GPIO header copies from nearest live copper
    vg = [p for p in r.pads if p["name"] == "VDD_GPIO" and p["pth"]]
    vias = [v for v in r.vias if v["n"] == "VDD_GPIO"]
    for p in vg:
        src = None
        if vias:
            src = min(vias, key=lambda v: hypot(v["x"], v["y"], p["x"], p["y"]))
        other = [q for q in vg if q is not p]
        if other:
            n = min(other, key=lambda q: hypot(q["x"], q["y"], p["x"], p["y"]))
            r.route_b_any(n["x"], n["y"], p["x"], p["y"], "VDD_GPIO", 0.40)
        if src:
            r.route_b_any(src["x"], src["y"], p["x"], p["y"], "VDD_GPIO", 0.40)


def phase_dnp(r: Final):
    print("== DNP stubs + P0.15 clearance nudge ==", flush=True)
    for net, ref, xj in (
        ("ANT", "C21", 22.4),
        ("ANT_FIT", "C22", 21.6),
        ("AUX", "C23", 21.6),
        ("AUX_FIT", "C24", 21.6),
        ("GPS", "C31", 22.4),
    ):
        p = r.pad(ref, "1")
        if not p:
            continue
        others = [q for q in r.by_net.get(net, []) if q["ref"] != ref and not q["npth"]]
        if not others:
            continue
        t = min(others, key=lambda q: hypot(p["x"], p["y"], q["x"], q["y"]))
        pts = [(p["x"], p["y"]), (xj, p["y"]), (xj, t["y"]), (t["x"], t["y"])]
        if not r.fcommit(pts, net, 0.20):
            r.route_f_any(p["x"], p["y"], t["x"], t["y"], net, 0.20)

    # Nudge P0.15 B.Cu vertical off J13 pad 18 (clearance 0.14 -> >=0.15)
    for tr in list(r.board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            continue
        if tr.GetNetname() != "P0.15" or tr.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = tr.GetStart(), tr.GetEnd()
        x1, y1 = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        x2, y2 = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)

        def fixx(x):
            return 105.45 if abs(x - 106.10) < 0.08 else x

        nx1, nx2 = fixx(x1), fixx(x2)
        if nx1 != x1 or nx2 != x2:
            tr.SetStart(vec(nx1, y1))
            tr.SetEnd(vec(nx2, y2))
            print(f"  nudged P0.15 B.Cu {x1:.2f}/{x2:.2f} -> {nx1:.2f}/{nx2:.2f}")
    r.collect()


def dangling_vias(r: Final):
    """Route a stub or delete vias with no copper on either layer besides themselves."""
    print("== dangling vias ==", flush=True)
    kill = []
    for v in list(r.vias):
        name = v["n"]
        if name in ("GND", "VDD_nRF") or name in RF_NETS:
            continue
        hit = False
        for t in r.tracks:
            if t["n"] != name:
                continue
            if hypot(v["x"], v["y"], t["x1"], t["y1"]) < 0.35 or hypot(v["x"], v["y"], t["x2"], t["y2"]) < 0.35:
                hit = True
                break
            if math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) > 0.01:
                # midpoint proximity
                if min(
                    hypot(v["x"], v["y"], t["x1"], t["y1"]),
                    hypot(v["x"], v["y"], t["x2"], t["y2"]),
                ) < 0.35:
                    hit = True
                    break
        if hit:
            continue
        # try to reach nearest pad
        pads = [p for p in r.by_net.get(name, []) if not p["npth"]]
        if not pads:
            kill.append(v)
            continue
        t = min(pads, key=lambda p: hypot(p["x"], p["y"], v["x"], v["y"]))
        if r.route_f_any(t["x"], t["y"], v["x"], v["y"], name) or r.route_b_any(t["x"], t["y"], v["x"], v["y"], name):
            print(f"  tied dangling via {name} @({v['x']:.2f},{v['y']:.2f})")
        else:
            # keep power/signal courtyard vias even if stubborn
            if hypot(t["x"], t["y"], v["x"], v["y"]) < 8:
                print(f"  keep via {name} @({v['x']:.2f},{v['y']:.2f})")
            else:
                kill.append(v)
    for v in kill:
        try:
            r.board.Remove(v["obj"])
            print(f"  deleted dangling via {v['n']} @({v['x']:.2f},{v['y']:.2f})")
        except Exception:
            pass
    r.collect()


def close_nets(r: Final, pairs, nets, astar=False):
    nset = set(nets)
    work = [p for p in pairs if p["net"] in nset]
    work.sort(key=lambda p: hypot(p["ax"], p["ay"], p["bx"], p["by"]))
    ok = fail = 0
    for p in work:
        if r.join_pair(p, astar=astar):
            ok += 1
        else:
            fail += 1
    print(f"  close nets closed={ok} fail={fail} of {len(work)}")
    return ok


def close_class(r: Final, pairs, cls, extra_nets=(), astar=False):
    if extra_nets:
        work = [p for p in pairs if p["net"] in extra_nets]
    else:
        work = [p for p in pairs if p["cls"] == cls]
    work.sort(key=lambda p: hypot(p["ax"], p["ay"], p["bx"], p["by"]))
    ok = fail = 0
    for p in work:
        if r.join_pair(p, astar=astar):
            ok += 1
        else:
            fail += 1
    print(f"  class {cls} closed={ok} fail={fail} of {len(work)}")
    return ok


def write_csv_if_needed(pairs):
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 50:
        return
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["net", "class", "dist_mm", "ax", "ay", "a", "bx", "by", "b", "note"])
        for p in pairs:
            d = hypot(p["ax"], p["ay"], p["bx"], p["by"])
            w.writerow(
                [
                    p["net"],
                    p["cls"],
                    f"{d:.3f}",
                    f"{p['ax']:.4f}",
                    f"{p['ay']:.4f}",
                    p["a"],
                    f"{p['bx']:.4f}",
                    f"{p['by']:.4f}",
                    p["b"],
                    "",
                ]
            )


def main():
    if not os.path.isfile(BACKUP):
        print("missing backup", BACKUP)
        return 2
    # Refuse to be complete_route.main: never copy RF-only backup onto the live board.
    rf_only = f"{ROOT}/.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-fullroute"
    live_hash = subprocess.check_output(["sha256sum", BOARD], text=True).split()[0]
    bak_hash = subprocess.check_output(["sha256sum", BACKUP], text=True).split()[0]
    print("live", live_hash[:12], "backup", bak_hash[:12], "rf-only-exists", os.path.isfile(rf_only))

    pairs, n0, base_counts, _ = run_drc()
    write_csv_if_needed(pairs)
    print(
        f"start unconnected={n0} shorts={base_counts.get('shorting_items', 0)} "
        f"clear={base_counts.get('clearance', 0)} pairs={len(pairs)}",
        flush=True,
    )
    baseline = {
        "shorting_items": base_counts.get("shorting_items", 0),
        "clearance": base_counts.get("clearance", 0),
        "hole_clearance": base_counts.get("hole_clearance", 0),
    }
    last_good = BACKUP
    board, r = load()
    print("pads", len(r.pads), "tracks", len(r.tracks), "vias", len(r.vias), flush=True)

    phases = [
        ("power", lambda: (phase_power(r), close_nets(r, pairs, POWER_NETS))),
        ("sim", lambda: (phase_sim(r), close_nets(r, pairs, SIM_NETS))),
        ("gnss", lambda: (phase_gnss(r), close_nets(r, pairs, {"GNSS_VBIAS"}))),
        ("swd", lambda: (phase_swd(r), close_nets(r, pairs, SWD_NETS))),
        ("fanout", lambda: phase_fanout(r)),
        (
            "gpio",
            lambda: (
                phase_gpio(r),
                close_class(r, pairs, "A", astar=True),
                close_class(r, pairs, "G", astar=True),
            ),
        ),
        ("dnp", lambda: (phase_dnp(r), close_class(r, pairs, "C"), dangling_vias(r))),
    ]

    for label, fn in phases:
        print(f"\n#### PHASE {label}", flush=True)
        fn()
        r.collect()
        fill_zones(board)
        got = save_and_check(board, r, label, baseline, last_good)
        if got[0] is None:
            return 1
        pairs, n, counts = got
        last_good = os.path.join(SNAP_DIR, f"after-{label}.kicad_pcb")
        board, r = load()
        if n == 0:
            print("unconnected reached 0")
            break
        # tighten baseline clearance if we improved it
        baseline["clearance"] = min(baseline["clearance"], counts.get("clearance", baseline["clearance"]))

    # Loop remaining DRC pairs
    for i in range(6):
        pairs, n, counts, _ = run_drc()
        if n == 0:
            break
        print(f"\n#### LOOP {i+1} remaining={n}", flush=True)
        close_class(r, pairs, "F", astar=False)
        close_class(r, pairs, "A", astar=True)
        close_class(r, pairs, "G", astar=True)
        close_class(r, pairs, "C", astar=False)
        leftover = sorted(
            {
                p["net"]
                for p in pairs
                if p["net"] not in SKIP and p["net"] != "GND" and p["net"] not in RF_NETS
            }
        )
        for name in leftover:
            r.connect_net(name)
        fill_zones(board)
        got = save_and_check(board, r, f"loop{i+1}", baseline, last_good)
        if got[0] is None:
            return 1
        pairs, n, counts = got
        last_good = os.path.join(SNAP_DIR, f"after-loop{i+1}.kicad_pcb")
        board, r = load()
        if n == 0:
            break
        if got[0] is not None and i >= 1:
            # continue even if some remain
            pass

    fill_zones(board)
    pcbnew.SaveBoard(BOARD, board)
    pairs, n, counts, _ = run_drc()
    print(
        f"FINAL unconnected={n} shorts={counts.get('shorting_items', 0)} "
        f"clear={counts.get('clearance', 0)} hole={counts.get('hole_clearance', 0)}",
        flush=True,
    )
    open(f"{ROOT}/reports/DRC_AFTER_CONNECT.json", "w").write(open(DRC_JSON).read())
    return 0 if counts.get("shorting_items", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
