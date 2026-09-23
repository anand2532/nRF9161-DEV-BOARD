#!/usr/bin/env python3
"""Deterministic remaining-net closer. Does not restore RF backup. No autorouter."""
from __future__ import annotations

import json
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import (  # noqa: E402
    BOARD,
    RF_NETS,
    Router,
    hypot,
    net_width,
)

DRC_JSON = "/tmp/nrf_hw_drc.json"
BACKUP = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-close-gaps"

# Missing courtyard vias: staggered off the occupied 0.95 mm rings.
FANOUT = {
    "P0.06": (48.55, 36.00),
    "P0.09": (48.55, 29.50),
    "P0.11": (48.55, 28.00),
    "P0.14": (42.25, 21.95),
    "P0.16": (41.25, 21.95),
    "P0.18": (39.75, 21.95),
    "P0.20": (36.75, 21.95),
    "P0.22": (35.25, 21.95),
    "P0.24": (34.25, 21.95),
    "P0.27": (34.25, 42.25),
    "P0.29": (35.75, 42.25),
    "P0.31": (36.75, 42.25),
    "P0.04": (42.25, 42.25),
    "P0.01": (40.25, 42.25),
    "COEX1": (38.25, 42.25),
    "MAGPIO0": (24.65, 21.95),
    "MIPI_VIO": (24.65, 23.10),
    "MIPI_SCLK": (24.65, 24.25),
    "MIPI_SDATA": (24.65, 25.40),
}

NORTH_Y = [8.4, 8.9, 9.4, 9.9, 10.4, 10.9, 11.4, 11.9, 12.4, 12.9, 13.4, 15.4, 15.9, 16.4, 16.9, 17.4]
EAST_X = [88.2, 88.8, 89.4, 90.0, 90.6, 91.2, 91.8, 92.4, 93.0, 93.6, 94.2, 94.8, 95.4, 100.6, 101.2, 101.8, 102.4, 109.0, 109.6, 110.2, 110.8, 111.4, 112.0, 112.6, 113.2, 113.8, 114.4]
SOUTH_Y = [65.2, 65.8, 66.4, 67.0, 67.6, 68.2, 68.8, 72.2, 72.8, 73.4, 74.0, 74.6, 75.2]


def u1_pad(r, name):
    for p in r.pads:
        if p["ref"] == "U1" and p["name"] == name:
            return p
    return None


def nearest_via(r, name, x, y, limit=8.0):
    vias = [v for v in r.vias if v["n"] == name]
    if not vias:
        return None
    v = min(vias, key=lambda q: hypot(q["x"], q["y"], x, y))
    if hypot(v["x"], v["y"], x, y) > limit:
        return None
    return v


def pad_xy(r, ref, num=None, net=None):
    for p in r.pads:
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


class Highway(Router):
    def __init__(self, board):
        super().__init__(board)
        self.nyi = 0
        self.exi = 0
        self.syi = 0

    def take_y(self):
        y = NORTH_Y[self.nyi % len(NORTH_Y)]
        self.nyi += 1
        return y

    def take_x(self):
        x = EAST_X[self.exi % len(EAST_X)]
        self.exi += 1
        return x

    def take_s(self):
        y = SOUTH_Y[self.syi % len(SOUTH_Y)]
        self.syi += 1
        return y

    def fpath(self, pts, name, w, code):
        return self.commit(pts, pcbnew.F_Cu, w, code, name) or False

    def bpath(self, pts, name, w, code):
        return self.commit(pts, pcbnew.B_Cu, w, code, name) or False

    def escape_to_via(self, p, vx, vy, name):
        w = net_width(name)
        code = p["code"]
        # Jog around occupied courtyard vias rather than running through them.
        if not self.via_ok(vx, vy, name):
            site = None
            for dx, dy in (
                (0, 0),
                (1.15, 0),
                (-1.15, 0),
                (0, 1.15),
                (0, -1.15),
                (1.15, 1.15),
                (1.15, -1.15),
                (2.10, 0),
                (0, -2.10),
                (0, 2.10),
            ):
                cx, cy = vx + dx, vy + dy
                if self.via_ok(cx, cy, name):
                    site = (cx, cy)
                    break
            if not site:
                site = self.local_via(p["x"], p["y"], name)
            if not site:
                print(f"NOVIA {name}")
                return None
            vx, vy = site
        candidates = []
        if p["sy"] > p["sx"] + 0.05 and vy < p["y"]:
            # North oblong: stop before the via ring, then jog.
            gate_y = 24.50
            candidates.append([(p["x"], p["y"]), (p["x"], gate_y), (vx, gate_y), (vx, vy)])
            candidates.append([(p["x"], p["y"]), (vx, p["y"]), (vx, vy)])
        elif p["sy"] > p["sx"] + 0.05 and vy > p["y"]:
            gate_y = 39.80
            candidates.append([(p["x"], p["y"]), (p["x"], gate_y), (vx, gate_y), (vx, vy)])
            candidates.append([(p["x"], p["y"]), (vx, p["y"]), (vx, vy)])
        elif p["sx"] > p["sy"] + 0.05 and vx > p["x"]:
            gate_x = 45.80
            candidates.append([(p["x"], p["y"]), (gate_x, p["y"]), (gate_x, vy), (vx, vy)])
            candidates.append([(p["x"], p["y"]), (p["x"] + 1.6, p["y"]), (p["x"] + 1.6, vy), (vx, vy)])
        elif p["sx"] > p["sy"] + 0.05 and vx < p["x"]:
            gate_x = 26.90
            candidates.append([(p["x"], p["y"]), (gate_x, p["y"]), (gate_x, vy), (vx, vy)])
            candidates.append([(p["x"], p["y"]), (p["x"], vy), (vx, vy)])
        else:
            candidates.append([(p["x"], p["y"]), (vx, p["y"]), (vx, vy)])
            candidates.append([(p["x"], p["y"]), (p["x"], vy), (vx, vy)])
        for pts in candidates:
            if self.fpath(pts, name, w, code):
                self.add_via(vx, vy, code, name)
                return vx, vy
        if self.route_f(p["x"], p["y"], vx, vy, name, w, code):
            self.add_via(vx, vy, code, name)
            return vx, vy
        print(f"FANOUT fail {name} -> ({vx:.2f},{vy:.2f})")
        return None

    def to_header(self, name, vx, vy, hx, hy, w, code):
        """Stay south of MAGPIO1 (y=14.8). Use free y≈43 and y≈64–68 buses, x>=65 around J18."""
        lanes = []
        for i in range(16):
            ymid = 42.8 + (i % 8) * 0.40
            ybus = 63.4 + (i % 14) * 0.40
            xcol = 65.2 + (i % 10) * 0.50
            lanes.append((ymid, ybus, xcol))
        tries = []
        for ymid, ybus, xcol in lanes:
            if hy > 70:
                # South GPIO headers. Wrap east of J18, then the free y=64–68 bus.
                tries.append(
                    [(vx, vy), (vx, ymid), (xcol, ymid), (xcol, ybus), (hx, ybus), (hx, hy)]
                )
            elif hx > 100:
                tries.append(
                    [(vx, vy), (vx, ymid), (xcol, ymid), (xcol, hy), (hx, hy)]
                )
            else:
                tries.append(
                    [(vx, vy), (vx, ymid), (xcol, ymid), (xcol, hy), (hx, hy)]
                )
        for pts in tries:
            if self.bpath(pts, name, w, code):
                return True
        print(f"HIGHWAY fail {name} via=({vx:.1f},{vy:.1f}) hdr=({hx:.1f},{hy:.1f})")
        return False


def local_power(r: Highway):
    def join(net, a, b, via_y=None):
        pa, pb = a, b
        if not pa or not pb:
            return
        w = net_width(net)
        # Jog around the 0402 GND pad that sits 0.64 mm from pin 1.
        yj = pa["y"] - 0.70
        pts = [(pa["x"], pa["y"]), (pa["x"], yj), (pb["x"], yj), (pb["x"], pb["y"])]
        if r.fpath(pts, net, w, pa["code"]):
            print(f"F {net} {pa['ref']}-{pb['ref']}")
            return
        if r.route_f(pa["x"], pa["y"], pb["x"], pb["y"], net, w, pa["code"]):
            print(f"F {net} {pa['ref']}-{pb['ref']}")
        else:
            print(f"F fail {net} {pa['ref']}-{pb['ref']}")

    # VDD1 chain
    join("VDD1", pad_xy(r, "U1", "102"), pad_xy(r, "C4", "1"))
    join("VDD1", pad_xy(r, "C4", "1"), pad_xy(r, "C5", "1"))
    join("VDD1", pad_xy(r, "C5", "1"), pad_xy(r, "C6", "1"))
    join("VDD1", pad_xy(r, "C6", "1"), pad_xy(r, "C3", "1"))
    join("VDD1", pad_xy(r, "C6", "1"), pad_xy(r, "R1", "1"))
    join("VDD1", pad_xy(r, "R1", "1"), pad_xy(r, "FB1", "2"))
    # VDD2
    join("VDD2", pad_xy(r, "U1", "22"), pad_xy(r, "C8", "1"))
    join("VDD2", pad_xy(r, "C8", "1"), pad_xy(r, "C9", "1"))
    join("VDD2", pad_xy(r, "C9", "1"), pad_xy(r, "C10", "1"))
    join("VDD2", pad_xy(r, "C9", "1"), pad_xy(r, "C7", "1"))
    join("VDD2", pad_xy(r, "C7", "1"), pad_xy(r, "FB3", "2"))
    join("VDD2_MID", pad_xy(r, "FB2", "2"), pad_xy(r, "FB3", "1"))
    # VDD_GPIO local
    join("VDD_GPIO", pad_xy(r, "U1", "12"), pad_xy(r, "C12", "1"))
    u1g = pad_xy(r, "U1", "12")
    c12 = pad_xy(r, "C12", "1")
    if u1g and c12:
        pts = [(u1g["x"], u1g["y"]), (46.60, u1g["y"]), (46.60, c12["y"]), (c12["x"], c12["y"])]
        if r.fpath(pts, "VDD_GPIO", 0.40, u1g["code"]):
            print("F VDD_GPIO U1-C12 jog")
    join("VDD_GPIO", pad_xy(r, "C12", "1"), pad_xy(r, "U2", "5"))
    fb5v = pad_xy(r, "FB5", "1")
    if fb5v:
        site = (25.60, 66.00)
        pts = [(fb5v["x"], fb5v["y"]), (13.20, fb5v["y"]), (13.20, 66.00), site]
        if r.via_ok(site[0], site[1], "VDD_GPIO", pwr=True) and r.fpath(pts, "VDD_GPIO", 0.40, fb5v["code"]):
            r.add_via(site[0], site[1], fb5v["code"], "VDD_GPIO", pwr=True)
            print("FB5 VDD_GPIO via", site)
        else:
            print("FB5 VDD_GPIO wrap fail")
    join("ENABLE", pad_xy(r, "C14", "1"), pad_xy(r, "R1", "2"))
    join("DEC0", pad_xy(r, "U1", "13"), pad_xy(r, "C13", "1"))
    # VIN shorts
    join("VIN_FILT", pad_xy(r, "JP1", "1"), pad_xy(r, "R2", "1") if pad_xy(r, "R2", "1") else pad_xy(r, "JP1", "1"))
    # SIM local F.Cu around U4 / caps
    join("SIM_RST", pad_xy(r, "C36", "1"), pad_xy(r, "U4", "6"))
    join("SIM_RST", pad_xy(r, "C36", "1"), pad_xy(r, "TP4", "1"))
    join("SIM_CLK", pad_xy(r, "C35", "1"), pad_xy(r, "U4", "7"))
    join("SIM_1V8", pad_xy(r, "C38", "1"), pad_xy(r, "U4", "5"))
    join("SIM_1V8", pad_xy(r, "C33", "1"), pad_xy(r, "C38", "1"))
    join("SIM_IO", pad_xy(r, "C37", "1"), pad_xy(r, "U4", "8"))
    join("SIM_VCC", pad_xy(r, "C34", "1"), pad_xy(r, "JP2", "2"))
    join("SIM_CLK_C", pad_xy(r, "U4", "2"), pad_xy(r, "J7", None, "SIM_CLK_C"))
    join("SIM_RST_C", pad_xy(r, "U4", "3"), pad_xy(r, "J7", None, "SIM_RST_C"))
    join("SIM_IO_C", pad_xy(r, "U4", "1"), pad_xy(r, "J7", None, "SIM_IO_C"))
    join("SIM_VCC", pad_xy(r, "J7", None, "SIM_VCC"), pad_xy(r, "C34", "1"))
    # GNSS_VBIAS along east of GNSS spine
    c30 = pad_xy(r, "C30", "1")
    l4 = pad_xy(r, "L4", "1")
    fb5b = pad_xy(r, "FB5", "2")
    if c30 and l4:
        pts = [(c30["x"], c30["y"]), (17.52, c30["y"]), (17.52, l4["y"]), (l4["x"], l4["y"])]
        if not r.fpath(pts, "GNSS_VBIAS", 0.20, c30["code"]):
            join("GNSS_VBIAS", c30, l4)
    if l4 and fb5b:
        pts = [(l4["x"], l4["y"]), (14.00, l4["y"]), (14.00, fb5b["y"]), (fb5b["x"], fb5b["y"])]
        if not r.fpath(pts, "GNSS_VBIAS", 0.20, l4["code"]):
            join("GNSS_VBIAS", l4, fb5b)
    # DNP RF shunts: stub to existing same-net copper, do not rewrite 50 ohm trunks
    for net, ref, xj in (
        ("ANT", "C21", 22.4),
        ("ANT_FIT", "C22", 21.6),
        ("AUX", "C23", 21.6),
        ("AUX_FIT", "C24", 21.6),
        ("GPS", "C31", 22.4),
    ):
        p = pad_xy(r, ref, "1")
        if not p:
            continue
        others = [q for q in r.by_net.get(net, []) if q["ref"] != ref]
        if not others:
            continue
        t = min(others, key=lambda q: hypot(p["x"], p["y"], q["x"], q["y"]))
        pts = [(p["x"], p["y"]), (xj, p["y"]), (xj, t["y"]), (t["x"], t["y"])]
        if not r.fpath(pts, net, 0.20, p["code"]):
            r.route_f(p["x"], p["y"], t["x"], t["y"], net, 0.20, p["code"])


def primary_header(r, name):
    """Prefer south GPIO headers, then east, then J18 for ADC."""
    cands = []
    for p in r.pads:
        if p["name"] != name or not p["pth"]:
            continue
        score = 0
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


def extra_pth(r, name, skip):
    out = []
    for p in r.pads:
        if p["name"] == name and p["pth"] and p is not skip:
            out.append(p)
    return out


def run_drc():
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--output", DRC_JSON, BOARD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    data = json.load(open(DRC_JSON))
    shorts = sum(1 for v in data.get("violations", []) if v.get("type") in ("shorting_items", "clearance", "hole_clearance"))
    n = len(data.get("unconnected_items", []))
    return n, shorts, data


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Highway(board)
    r.collect()
    print("pads", len(r.pads), "tracks", len(r.tracks), "vias", len(r.vias), flush=True)

    local_power(r)

    # Fanout missing U1 vias
    for name, site in FANOUT.items():
        p = u1_pad(r, name)
        if not p:
            print("no U1 pad", name)
            continue
        if nearest_via(r, name, p["x"], p["y"], limit=6.5):
            continue
        print("fanout", name, site, flush=True)
        r.escape_to_via(p, site[0], site[1], name)

    r.collect()

    # Highway remaining signal nets that still have a PTH destination
    nets = sorted(
        {
            p["name"]
            for p in r.pads
            if p["name"].startswith(("P0.", "MAGPIO", "MIPI", "COEX", "SIM_", "SWD", "nRESET", "ENABLE", "VDD_GPIO"))
        }
    )
    for name in nets:
        # Skip nets that already have a long B.Cu run (already fanned to headers).
        blen = sum(
            hypot(t["x1"], t["y1"], t["x2"], t["y2"])
            for t in r.tracks
            if t["n"] == name and t["ly"] == pcbnew.B_Cu
        )
        if blen > 20:
            continue
        hdr = primary_header(r, name)
        p = u1_pad(r, name)
        if not hdr:
            continue
        w = net_width(name)
        code = hdr["code"]
        via = None
        if p:
            via = nearest_via(r, name, p["x"], p["y"], limit=7.0)
        if via is None:
            vias = [v for v in r.vias if v["n"] == name]
            if vias:
                via = min(vias, key=lambda v: hypot(v["x"], v["y"], hdr["x"], hdr["y"]))
        if via is None:
            print("no via for", name)
            continue
        if r.to_header(name, via["x"], via["y"], hdr["x"], hdr["y"], w, code):
            print(f"B {name} -> {hdr['ref']}", flush=True)
        for extra in extra_pth(r, name, hdr):
            ybus = 64.0 + (r.syi % 10) * 0.40
            r.syi += 1
            xcol = 65.2 + (r.exi % 8) * 0.50
            r.exi += 1
            pts = [(hdr["x"], hdr["y"]), (hdr["x"], ybus), (extra["x"], ybus), (extra["x"], extra["y"])]
            if extra["x"] > 100 and abs(hdr["y"] - extra["y"]) < 40:
                pts = [(hdr["x"], hdr["y"]), (hdr["x"], extra["y"]), (extra["x"], extra["y"])]
            if extra["ref"] == "J18":
                pts = [(hdr["x"], hdr["y"]), (hdr["x"], 58.8), (extra["x"], 58.8), (extra["x"], extra["y"])]
            if not r.bpath(pts, name, w, code):
                print(f"extra PTH fail {name} {extra['ref']}")

    # VDD_GPIO south/east power bus
    vg = [p for p in r.pads if p["name"] == "VDD_GPIO" and p["pth"]]
    vg.sort(key=lambda p: (round(p["y"], 1), p["x"]))
    code = vg[0]["code"] if vg else 0
    for a, b in zip(vg, vg[1:]):
        if abs(a["y"] - b["y"]) < 1.0:
            r.bpath([(a["x"], a["y"]), (b["x"], b["y"])], "VDD_GPIO", 0.40, code)
        elif abs(a["x"] - b["x"]) < 1.0:
            r.bpath([(a["x"], a["y"]), (b["x"], b["y"])], "VDD_GPIO", 0.40, code)
        else:
            r.bpath([(a["x"], a["y"]), (a["x"], 74.0), (b["x"], 74.0), (b["x"], b["y"])], "VDD_GPIO", 0.40, code)

    print("zone fill", flush=True)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    n, shorts, _ = run_drc()
    print(f"DRC unconnected={n} shorts/clear/hole={shorts} ok={r.ok} fail={r.fail}", flush=True)
    if shorts:
        print("ABORT restoring backup")
        import shutil

        shutil.copy2(BACKUP, BOARD)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
