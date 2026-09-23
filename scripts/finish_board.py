#!/usr/bin/env python3
"""Disciplined nRF9161-DEV-BOARD finish: radial LGA fanout + reserved lanes."""
from __future__ import annotations

import math
import sys
from collections import defaultdict

import pcbnew

BOARD = "/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
U1C = (36.0, 32.0)
EDGE = 0.70
VIA_S, VIA_D = 0.60, 0.30
PWR_VIA_S, PWR_VIA_D = 0.80, 0.40
SIG_W, PWR_W, RF_W = 0.18, 0.40, 0.20
RF_PADS = {"61", "64", "67"}
RF_NETS = {"ANT", "ANT_FIT", "AUX", "AUX_FIT", "GPS", "GNSS_ANT"}
RF_OK = RF_NETS | {"GNSS_VBIAS", "GNSS_LNA_EN"}
SKIP = {"", "GND"}
PLANE = {"VDD_nRF"}
J18_BOX = (34.5, 59.8, 63.2, 64.4)  # x0,y0,x1,y1
U1_BOX = (27.6, 25.4, 44.4, 39.2)


class Grid:
    def __init__(self, w, h, pitch):
        from array import array as _array

        self.pitch = pitch
        self.nx = int(math.ceil(w / pitch)) + 1
        self.ny = int(math.ceil(h / pitch)) + 1
        self.occ = _array("i", [0]) * (self.nx * self.ny)

    def _i(self, i, j):
        return i * self.ny + j

    def ij(self, x, y):
        return int(round(x / self.pitch)), int(round(y / self.pitch))

    def inb(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    def blocked(self, i, j, net):
        if not self.inb(i, j):
            return True
        v = self.occ[self._i(i, j)]
        return v != 0 and v != net

    def stamp(self, x, y, r, code):
        i0, j0 = self.ij(x - r, y - r)
        i1, j1 = self.ij(x + r, y + r)
        rr = (r + 0.001) ** 2
        for i in range(max(0, i0), min(self.nx, i1 + 1)):
            gx = i * self.pitch
            dx2 = (gx - x) ** 2
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                gy = j * self.pitch
                if dx2 + (gy - y) ** 2 > rr:
                    continue
                idx = self._i(i, j)
                cur = self.occ[idx]
                if cur == 0 or cur == code:
                    self.occ[idx] = code
                else:
                    self.occ[idx] = -1

    def stamp_seg(self, x1, y1, x2, y2, r, code):
        dist = hypot(x1, y1, x2, y2)
        n = max(1, int(dist / (self.pitch * 0.45)))
        for k in range(n + 1):
            t = k / n
            self.stamp(x1 + t * (x2 - x1), y1 + t * (y2 - y1), r, code)

    def stamp_box(self, x1, y1, x2, y2, code=-1):
        i0, j0 = self.ij(min(x1, x2), min(y1, y2))
        i1, j1 = self.ij(max(x1, x2), max(y1, y2))
        for i in range(max(0, i0), min(self.nx, i1 + 1)):
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                self.occ[self._i(i, j)] = code

    def cells_clear(self, x1, y1, x2, y2, net):
        dist = hypot(x1, y1, x2, y2)
        n = max(1, int(dist / (self.pitch * 0.5)))
        for k in range(n + 1):
            t = k / n
            i, j = self.ij(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
            if self.blocked(i, j, net):
                return False
        return True


def nm(x):
    return int(pcbnew.FromMM(float(x)))


def mm(v):
    return pcbnew.ToMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


def hypot(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def dist_seg(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1
    l2 = vx * vx + vy * vy
    if l2 < 1e-18:
        return hypot(px, py, x1, y1)
    t = max(0.0, min(1.0, ((px - x1) * vx + (py - y1) * vy) / l2))
    return hypot(px, py, x1 + t * vx, y1 + t * vy)


def in_rf(x, y):
    return x < 24.0 and 20.0 < y < 64.0


def in_box(x, y, box):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def net_width(name):
    if name in RF_NETS:
        return RF_W
    if name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC")):
        return PWR_W
    return SIG_W


def net_clear(name):
    if name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC")) or name in PLANE:
        return 0.16
    if name in RF_NETS:
        return 0.15
    return 0.11


def is_pth(pad):
    return pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH


def oblong_u1(fp):
    n = 0
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in RF_PADS or num == "103" or (num.isdigit() and int(num) >= 104):
            continue
        rel = pad.GetFPRelativePosition()
        x, y = mm(rel.x), mm(rel.y)
        west, east = abs(x + 7.75) < 0.08, abs(x - 7.75) < 0.08
        south, north = abs(y + 5.0) < 0.08, abs(y - 5.0) < 0.08
        if not (west or east or south or north):
            continue
        if (west or east) and (south or north):
            if abs(x) >= abs(y) - 0.01:
                south = north = False
            else:
                west = east = False
        nx, ny, sx, sy = x, y, 0.30, 0.30
        if west:
            nx, sx, sy = x - 0.25, 0.80, 0.30
        elif east:
            nx, sx, sy = x + 0.25, 0.80, 0.30
        elif south:
            ny, sx, sy = y - 0.25, 0.30, 0.80
        elif north:
            ny, sx, sy = y + 0.25, 0.30, 0.80
        pad.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        pad.SetFPRelativePosition(vec(nx, ny))
        pad.SetSize(pcbnew.VECTOR2I(nm(sx), nm(sy)))
        pad.SetRoundRectRadiusRatio(0.12)
        n += 1
    return n


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra
            return True
        return False

    def groups(self):
        g = defaultdict(list)
        for i in range(len(self.p)):
            g[self.find(i)].append(i)
        return list(g.values())


class Router:
    def __init__(self, board):
        self.board = board
        ds = board.GetDesignSettings()
        ds.m_MinClearance = nm(0.10)
        ds.m_TrackMinWidth = nm(0.10)
        ds.m_ViasMinSize = nm(0.50)
        ds.m_MinThroughDrill = nm(0.30)
        bbox = board.GetBoardEdgesBoundingBox()
        self.w, self.h = mm(bbox.GetWidth()), mm(bbox.GetHeight())
        self.gF = Grid(self.w, self.h, 0.20)
        self.gB = Grid(self.w, self.h, 0.30)
        self.g2 = Grid(self.w, self.h, 0.30)
        self.layer_grid = {pcbnew.F_Cu: None, pcbnew.B_Cu: None, pcbnew.In2_Cu: None}
        self.pads = []
        self.by_net = defaultdict(list)
        self.tracks = []  # (x1,y1,x2,y2,layer,net,w)
        self.vias = []  # (x,y,net,r)
        self.ok = 0
        self.fail = 0
        self.lane = 0
        self.keepouts = []
        self.u1_via = {}

    def collect(self):
        for pad in self.board.GetPads():
            name = pad.GetNetname()
            pos = pad.GetPosition()
            size = pad.GetSize()
            parent = pad.GetParentFootprint()
            rec = {
                "x": mm(pos.x),
                "y": mm(pos.y),
                "code": pad.GetNetCode(),
                "pth": is_pth(pad),
                "npth": pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
                "ref": parent.GetReference() if parent else "",
                "num": pad.GetNumber(),
                "name": name or "",
                "r": max(mm(size.x), mm(size.y)) / 2,
            }
            self.pads.append(rec)
            if rec["name"]:
                self.by_net[rec["name"]].append(rec)
        for tr in self.board.GetTracks():
            if isinstance(tr, pcbnew.PCB_VIA):
                pt = tr.GetPosition()
                self.vias.append((mm(pt.x), mm(pt.y), tr.GetNetname(), 0.38))
            else:
                s, e = tr.GetStart(), tr.GetEnd()
                self.tracks.append(
                    (
                        mm(s.x),
                        mm(s.y),
                        mm(e.x),
                        mm(e.y),
                        tr.GetLayer(),
                        tr.GetNetname(),
                        mm(tr.GetWidth()),
                    )
                )
        # U.FL footprint keepouts (tracks/vias not allowed)
        self.keepouts = [
            (5.4, 29.8, 12.2, 34.5),  # J2 U.FL body
            (5.4, 49.8, 12.2, 54.5),  # J5 U.FL body
        ]
        self._stamp_base()

    def _stamp_base(self):
        self.layer_grid = {pcbnew.F_Cu: self.gF, pcbnew.B_Cu: self.gB, pcbnew.In2_Cu: self.g2}
        for G in (self.gF, self.gB, self.g2):
            G.stamp_box(0, 0, self.w, EDGE, -1)
            G.stamp_box(0, self.h - EDGE, self.w, self.h, -1)
            G.stamp_box(0, 0, EDGE, self.h, -1)
            G.stamp_box(self.w - EDGE, 0, self.w, self.h, -1)
        for G in (self.gB, self.g2):
            for box in self.keepouts:
                G.stamp_box(*box, -1)
        self.gF.stamp_box(30.4, 29.2, 41.6, 34.8, -1)
        for G in (self.gB, self.g2):
            G.stamp_box(0, 22, 23.5, 46, -1)
            G.stamp_box(0, 46, 20.5, 63.5, -1)
        for p in self.pads:
            if p["npth"]:
                for G in (self.gF, self.gB, self.g2):
                    G.stamp(p["x"], p["y"], p["r"] + 0.15, -1)
                continue
            self.gF.stamp(p["x"], p["y"], 0.16 if p["ref"] == "U1" else p["r"] + 0.08, p["code"] or -1)
            if p["pth"]:
                r = min(0.68, p["r"] + 0.08)
                self.gB.stamp(p["x"], p["y"], r, p["code"] or -1)
                self.g2.stamp(p["x"], p["y"], r, p["code"] or -1)
        for x, y, n, r in self.vias:
            net = self.board.FindNet(n)
            code = net.GetNetCode() if net else -1
            for G in (self.gF, self.gB, self.g2):
                G.stamp(x, y, r, code)
        for x1, y1, x2, y2, ly, n, w in self.tracks:
            G = self.layer_grid.get(ly)
            if not G:
                continue
            net = self.board.FindNet(n)
            code = net.GetNetCode() if net else -1
            G.stamp_seg(x1, y1, x2, y2, w / 2 + 0.11, code)

    def add_track(self, x1, y1, x2, y2, layer, width, netcode, name):
        if hypot(x1, y1, x2, y2) < 0.04:
            return
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(vec(x1, y1))
        t.SetEnd(vec(x2, y2))
        t.SetWidth(nm(width))
        t.SetLayer(layer)
        t.SetNetCode(netcode)
        self.board.Add(t)
        self.tracks.append((x1, y1, x2, y2, layer, name, width))
        G = self.layer_grid.get(layer)
        if G:
            G.stamp_seg(x1, y1, x2, y2, width / 2 + 0.11, netcode)

    def add_via(self, x, y, netcode, name, size=VIA_S, drill=VIA_D):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(vec(x, y))
        v.SetWidth(nm(size))
        v.SetDrill(nm(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(netcode)
        self.board.Add(v)
        self.vias.append((x, y, name, size / 2 + 0.08))
        for G in (self.gF, self.gB, self.g2):
            G.stamp(x, y, size / 2 + 0.20, netcode)
        return v

    ADC = {
        "P0.13",
        "P0.14",
        "P0.15",
        "P0.16",
        "P0.17",
        "P0.18",
        "P0.19",
        "P0.20",
        "VDD_GPIO",
        "GND",
    }

    def path_ok(self, pts, name, layer, width, code):
        G = self.layer_grid.get(layer)
        if not G:
            return False
        for a, b in zip(pts, pts[1:]):
            if hypot(a[0], a[1], b[0], b[1]) < 0.04:
                continue
            if not G.cells_clear(a[0], a[1], b[0], b[1], code):
                return False
            if name not in self.ADC and layer != pcbnew.F_Cu:
                dist = hypot(a[0], a[1], b[0], b[1])
                n = max(1, int(dist / 0.4))
                for k in range(n + 1):
                    t = k / n
                    x = a[0] + t * (b[0] - a[0])
                    y = a[1] + t * (b[1] - a[1])
                    if in_box(x, y, J18_BOX):
                        return False
        return True

    def try_path(self, pts, name, layer, width, code):
        if self.path_ok(pts, name, layer, width, code):
            return self.commit(pts, layer, width, code, name)
        return False

    def commit(self, pts, layer, width, code, name):
        for a, b in zip(pts, pts[1:]):
            self.add_track(a[0], a[1], b[0], b[1], layer, width, code, name)
        self.ok += 1
        return True

    def route_f(self, x1, y1, x2, y2, name, width, code):
        layer = pcbnew.F_Cu
        cands = [
            [(x1, y1), (x2, y1), (x2, y2)],
            [(x1, y1), (x1, y2), (x2, y2)],
        ]
        for d in (-1.2, 1.2, -2.2, 2.2, -3.4, 3.4, -5.0, 5.0):
            cands.append([(x1, y1), (x1, y1 + d), (x2, y1 + d), (x2, y2)])
            cands.append([(x1, y1), (x1 + d, y1), (x1 + d, y2), (x2, y2)])
        for pts in cands:
            if self.try_path(pts, name, layer, width, code):
                return True
        return False

    def channels(self, x1, y1, x2, y2, lane):
        """Leave headers perpendicular; wrap J18 on west x~26–33 or east x~64–74."""
        ybus = 69.15 + (lane % 6) * 0.42
        ymid = 47.4 + (lane % 10) * 0.42
        north = 11.4 + (lane % 8) * 0.42
        west = 25.9 + (lane % 16) * 0.46
        east = 64.3 + (lane % 22) * 0.46
        xf = 99.0 + (lane % 8) * 0.42
        out = []
        # south header (y≈76) → west/east wrap → dest
        out.append([(x1, y1), (x1, ybus), (west, ybus), (west, ymid), (x2, ymid), (x2, y2)])
        out.append([(x1, y1), (x1, ybus), (east, ybus), (east, ymid), (x2, ymid), (x2, y2)])
        out.append([(x2, y2), (x2, ybus), (west, ybus), (west, ymid), (x1, ymid), (x1, y1)])
        out.append([(x2, y2), (x2, ybus), (east, ybus), (east, ymid), (x1, ymid), (x1, y1)])
        # dest also south: stay on ybus
        out.append([(x1, y1), (x1, ybus), (x2, ybus), (x2, y2)])
        # east protocol headers (x≈104–116)
        out.append([(x1, y1), (x1, ymid), (xf, ymid), (xf, y2), (x2, y2)])
        out.append([(x1, y1), (east, y1), (east, y2), (x2, y2)])
        out.append([(x1, y1), (xf, y1), (xf, y2), (x2, y2)])
        # north highway (SWD / LEDs)
        out.append([(x1, y1), (x1, north), (x2, north), (x2, y2)])
        out.append([(x1, y1), (east, y1), (east, north), (x2, north), (x2, y2)])
        # simple L if both in the open
        out.append([(x1, y1), (x2, y1), (x2, y2)])
        out.append([(x1, y1), (x1, y2), (x2, y2)])
        return out

    def wrap_commit(self, x1, y1, x2, y2, name, width, code):
        """Unique wrap. (x1,y1) should be the header; (x2,y2) the via or 2nd header."""
        slot = self.lane
        self.lane += 1
        if slot < 36:
            layer = pcbnew.B_Cu if slot < 18 else pcbnew.In2_Cu
            s = slot % 18
            ybus = 66.5 + s * 0.36
        else:
            layer = pcbnew.B_Cu if slot < 44 else pcbnew.In2_Cu
            s = (slot - 36) % 8
            ybus = 72.70 + s * 0.28
            s = (slot - 36) % 18
        ymid = 47.8 + (slot % 18) * 0.38
        west_set = (26.3, 26.8, 27.3, 27.8, 28.3, 28.8, 31.3, 31.8, 32.3, 32.8, 33.3)
        east_set = (64.4, 64.9, 65.4, 65.9, 66.4, 66.9, 67.4, 67.9, 68.4, 68.9, 69.4)
        col = west_set[s] if s < 11 else east_set[s - 11]
        xf = 110.6 + (s % 8) * 0.40
        # both on south GPIO headers
        if y1 > 70 and y2 > 70:
            pts = [(x1, y1), (x1, ybus), (x2, ybus), (x2, y2)]
        # south GPIO header → east protocol header
        elif y1 > 70 and x2 > 100:
            pts = [(x1, y1), (x1, ybus), (xf, ybus), (xf, y2), (x2, y2)]
        # south GPIO header → ADC J18
        elif y1 > 70 and 58 < y2 < 66:
            pts = [(x1, y1), (x1, ybus), (x2, ybus), (x2, y2)]
        # south GPIO header → courtyard via
        elif y1 > 70:
            pts = [(x1, y1), (x1, ybus), (col, ybus), (col, ymid), (x2, ymid), (x2, y2)]
        # east header → via
        elif x1 > 100:
            pts = [(x1, y1), (xf, y1), (xf, ymid), (x2, ymid), (x2, y2)]
        else:
            pts = [(x1, y1), (x1, ymid), (col, ymid), (x2, ymid), (x2, y2)]
        return self.try_path(pts, name, layer, width, code)

    def route_inner(self, x1, y1, x2, y2, name, width, code):
        return self.wrap_commit(x1, y1, x2, y2, name, width, code)

    def via_ok(self, x, y, name, pwr=False):
        size = PWR_VIA_S if pwr else VIA_S
        # hole clearance 0.25 + drill/2
        drill = PWR_VIA_D if pwr else VIA_D
        need = drill / 2 + 0.27
        if not (EDGE + 1.2 < x < self.w - EDGE - 1.2 and EDGE + 1.2 < y < self.h - EDGE - 1.2):
            return False
        if in_rf(x, y) and name not in RF_OK:
            return False
        if in_box(x, y, U1_BOX):
            return False
        for box in self.keepouts:
            if in_box(x, y, box):
                return False
        for p in self.pads:
            if p["name"] == name:
                continue
            extra = need if p["pth"] else (p["r"] + 0.18 + size / 2)
            if p["pth"]:
                extra = p["r"] + need
            if (p["x"] - x) ** 2 + (p["y"] - y) ** 2 < extra ** 2:
                return False
        for vx, vy, n, r in self.vias:
            if (vx - x) ** 2 + (vy - y) ** 2 < (0.90 if n != name else 0.55) ** 2:
                return False
        return True

    def gen_slots(self):
        slots = []
        for x in (46.6, 47.6, 48.6):
            y = 22.4
            while y <= 43.0:
                slots.append((x, y))
                y += 0.95
        for y in (40.8, 41.8, 42.8):
            x = 25.8
            while x <= 45.8:
                slots.append((x, y))
                x += 0.95
        for y in (23.2, 22.2, 21.2):
            x = 26.0
            while x <= 52.0:
                slots.append((x, y))
                x += 0.95
        for x in (25.7, 26.7):
            for y in (21.4, 22.4, 23.4, 24.4):
                slots.append((x, y))
        self.slots = []
        seen = set()
        for x, y in slots:
            k = (round(x, 2), round(y, 2))
            if k in seen:
                continue
            seen.add(k)
            self.slots.append((x, y))
        self.used = set()

    def take_slot(self, px, py, name, pwr=False):
        best = None
        for i, (sx, sy) in enumerate(self.slots):
            if i in self.used:
                continue
            if not self.via_ok(sx, sy, name, pwr=pwr):
                continue
            d = (sx - px) ** 2 + (sy - py) ** 2
            if best is None or d < best[0]:
                best = (d, i, sx, sy)
        if not best:
            return None
        self.used.add(best[1])
        return best[2], best[3]

    def local_via(self, p, name, pwr=False):
        for dx, dy in (
            (0, 1.35),
            (0, -1.35),
            (1.35, 0),
            (-1.35, 0),
            (1.2, 1.2),
            (-1.2, 1.2),
            (1.2, -1.2),
            (-1.2, -1.2),
            (0, 2.1),
            (0, -2.1),
            (2.1, 0),
            (-2.1, 0),
            (2.4, 1.0),
            (-2.4, 1.0),
        ):
            cand = (p["x"] + dx, p["y"] + dy)
            if self.via_ok(cand[0], cand[1], name, pwr=pwr):
                return cand
        return None

    def radial_end(self, p):
        x, y = p["x"], p["y"]
        if x >= 42.0:
            col = 46.55 if round(y / 0.5) % 2 == 0 else 47.75
            return col, y
        if y <= 28.3:
            row = 23.15 if round(x / 0.5) % 2 == 0 else 22.05
            return x, row
        if y >= 35.4:
            row = 40.85 if round(x / 0.5) % 2 == 0 else 41.95
            return x, row
        if x <= 30.5:
            col = 25.65 if round(y / 0.5) % 2 == 0 else 26.75
            row = min(y, 26.6) - 1.0
            return col, row
        return x + 1.4, y

    def explicit_rf(self):
        # J3 SWF tap: east of C32, south then north to ANT_FIT join at (12,28)
        j3 = next(p for p in self.by_net["ANT_FIT"] if p["ref"] == "J3")
        code = j3["code"]
        paths = [
            [(j3["x"], j3["y"]), (8.0, 43.6), (10.9, 43.6), (10.9, 28.0), (12.0, 28.0)],
            [(j3["x"], j3["y"]), (8.0, 44.0), (10.7, 44.0), (10.7, 27.6), (8.0, 27.6), (8.0, 28.0)],
            [(j3["x"], j3["y"]), (8.0, 43.8), (21.2, 43.8), (21.2, 28.0), (12.0, 28.0)],
        ]
        done = False
        for pts in paths:
            if self.try_path(pts, "ANT_FIT", pcbnew.F_Cu, RF_W, code):
                print("J3 SWF tap routed")
                done = True
                break
        if not done:
            print("J3 tap skipped (occupancy)")

        def pair(net, refa, refb, jogs=None):
            pa = next(p for p in self.by_net[net] if p["ref"] == refa and not p["npth"])
            pb = next(p for p in self.by_net[net] if p["ref"] == refb and not p["npth"])
            w = net_width(net)
            if self.route_f(pa["x"], pa["y"], pb["x"], pb["y"], net, w, pa["code"]):
                return True
            if jogs:
                for pts in jogs:
                    if self.try_path(pts, net, pcbnew.F_Cu, w, pa["code"]):
                        return True
            print(f"RF pair fail {net} {refa}-{refb}")
            self.fail += 1
            return False

        # GNSS_LNA_EN along y=22, north of matching
        pair("GNSS_LNA_EN", "R4", "TP2")
        # GNSS_VBIAS around the GNSS_ANT spine at x=16 / y=51
        vb = self.by_net["GNSS_VBIAS"]
        c28 = next(p for p in vb if p["ref"] == "C28")
        c29 = next(p for p in vb if p["ref"] == "C29")
        c30 = next(p for p in vb if p["ref"] == "C30")
        fb5 = next(p for p in vb if p["ref"] == "FB5")
        l4 = next(p for p in vb if p["ref"] == "L4")
        w = net_width("GNSS_VBIAS")
        code = c28["code"]
        for pts in (
            [(c28["x"], c28["y"]), (12.05, c28["y"]), (12.05, c29["y"]), (c29["x"], c29["y"])],
            [(c28["x"], c28["y"]), (12.05, c28["y"]), (12.05, fb5["y"]), (fb5["x"], fb5["y"])],
            [(c30["x"], c30["y"]), (18.0, 47.2), (12.05, 47.2), (12.05, c28["y"]), (c28["x"], c28["y"])],
            [(l4["x"], l4["y"]), (17.52, 41.2), (12.05, 41.2), (12.05, c28["y"]), (c28["x"], c28["y"])],
        ):
            if not self.try_path(pts, "GNSS_VBIAS", pcbnew.F_Cu, w, code):
                a, b = pts[0], pts[-1]
                if not self.route_f(a[0], a[1], b[0], b[1], "GNSS_VBIAS", w, code):
                    print("GNSS_VBIAS skip", pts[0], pts[-1])

        def stub(net, ref, x_jog):
            pads = [p for p in self.by_net[net] if p["ref"] == ref]
            if not pads:
                return
            p = pads[0]
            others = [q for q in self.by_net[net] if q["ref"] != ref]
            if not others:
                return
            t = min(others, key=lambda q: hypot(p["x"], p["y"], q["x"], q["y"]))
            pts = [(p["x"], p["y"]), (x_jog, p["y"]), (x_jog, t["y"]), (t["x"], t["y"])]
            if not self.try_path(pts, net, pcbnew.F_Cu, RF_W, p["code"]):
                self.route_f(p["x"], p["y"], t["x"], t["y"], net, RF_W, p["code"])

        stub("GNSS_ANT", "C32", 10.9)
        stub("GPS", "C31", 22.4)
        stub("AUX_FIT", "C24", 21.6)

    def fanout_all_u1(self):
        """Radial stub + via for every U1 signal before any other F.Cu crowding."""
        seen = set()
        pads = []
        for p in self.pads:
            if p["ref"] != "U1" or p["npth"]:
                continue
            name = p["name"]
            if not name or name in SKIP or name in RF_NETS:
                continue
            if name in seen:
                continue
            seen.add(name)
            pads.append(p)
        n = 0
        for p in pads:
            name = p["name"]
            code = p["code"]
            width = net_width(name)
            pwr = name.startswith(("VDD", "VIN")) or name in PLANE
            ex, ey = self.radial_end(p)
            # axis-aligned escape only (never along the LGA pad row)
            if abs(ex - p["x"]) < 0.05 or abs(ey - p["y"]) < 0.05:
                self.add_track(p["x"], p["y"], ex, ey, pcbnew.F_Cu, width, code, name)
            else:
                self.add_track(p["x"], p["y"], p["x"], ey, pcbnew.F_Cu, width, code, name)
                self.add_track(p["x"], ey, ex, ey, pcbnew.F_Cu, width, code, name)
            site = (ex, ey)
            if not self.via_ok(ex, ey, name, pwr=pwr):
                site = self.take_slot(ex, ey, name, pwr=pwr) or self.local_via({"x": ex, "y": ey}, name, pwr=pwr)
            if not site:
                print(f"NOVIA U1 {name} {p['num']}")
                self.fail += 1
                continue
            if site != (ex, ey):
                if not self.try_path([(ex, ey), (site[0], ey), (site[0], site[1])], name, pcbnew.F_Cu, width, code):
                    if not self.try_path([(ex, ey), (ex, site[1]), (site[0], site[1])], name, pcbnew.F_Cu, width, code):
                        print(f"FANOUT skip jog {name}")
                        site = None
            if not site:
                self.fail += 1
                continue
            self.add_via(
                site[0],
                site[1],
                code,
                name,
                size=PWR_VIA_S if pwr else VIA_S,
                drill=PWR_VIA_D if pwr else VIA_D,
            )
            self.u1_via[name] = site
            n += 1
        print("U1 fanout vias", n)

    def connect_net(self, name):
        pads = [p for p in self.by_net[name] if not p["npth"] and p["name"]]
        if len(pads) < 2 or name in SKIP:
            return
        code = pads[0]["code"]
        width = net_width(name)
        pwr = name.startswith(("VDD", "VIN")) or name in PLANE
        uniq = []
        seen = set()
        for p in pads:
            k = (round(p["x"], 2), round(p["y"], 2), p["ref"], p["num"])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(dict(p))
        uf = UF(len(uniq))
        # seed from existing tracks
        for i, a in enumerate(uniq):
            for x1, y1, x2, y2, ly, n, w in self.tracks:
                if n != name:
                    continue
                if dist_seg(a["x"], a["y"], x1, y1, x2, y2) < a["r"] + 0.12:
                    a["_trk"] = True
        on = [i for i, p in enumerate(uniq) if p.get("_trk")]
        for a, b in zip(on, on[1:]):
            uf.union(a, b)

        # local F.Cu among non-U1 SMD, short pairs
        pairs = []
        for i, a in enumerate(uniq):
            for j, b in enumerate(uniq):
                if j <= i:
                    continue
                pairs.append((hypot(a["x"], a["y"], b["x"], b["y"]), i, j))
        pairs.sort()
        for d, i, j in pairs:
            if uf.find(i) == uf.find(j):
                continue
            a, b = uniq[i], uniq[j]
            if a["ref"] == "U1" or b["ref"] == "U1":
                continue
            if d > (28.0 if name.startswith("SIM") else 14.0):
                continue
            if a["pth"] and b["pth"] and d > 6.0:
                continue
            if self.route_f(a["x"], a["y"], b["x"], b["y"], name, width, code):
                uf.union(i, j)

        nodes = []  # (x,y)

        def add_node(x, y):
            k = (round(x, 2), round(y, 2))
            if k not in add_node.seen:
                add_node.seen.add(k)
                nodes.append((x, y))

        add_node.seen = set()

        for i, p in enumerate(uniq):
            if p["pth"]:
                add_node(p["x"], p["y"])

        # U1 already fanned out
        if name in self.u1_via:
            add_node(*self.u1_via[name])
        else:
            for i, p in enumerate(uniq):
                if p["ref"] != "U1":
                    continue
                if name in RF_NETS:
                    continue
                cluster = uf.find(i)
                has_pth = any(uniq[k]["pth"] and uf.find(k) == cluster for k in range(len(uniq)))
                if has_pth and len(uf.groups()) == 1:
                    continue
                ex, ey = self.radial_end(p)
                self.add_track(p["x"], p["y"], ex, ey, pcbnew.F_Cu, width, code, name)
                self.ok += 1
                site = self.take_slot(ex, ey, name, pwr=pwr)
                if not site:
                    site = self.local_via({"x": ex, "y": ey}, name, pwr=pwr)
                if not site:
                    print(f"NOVIA U1 {name} {p['num']}")
                    self.fail += 1
                    continue
                if not self.try_path([(ex, ey), (site[0], ey), (site[0], site[1])], name, pcbnew.F_Cu, width, code):
                    self.add_track(ex, ey, site[0], ey, pcbnew.F_Cu, width, code, name)
                    self.add_track(site[0], ey, site[0], site[1], pcbnew.F_Cu, width, code, name)
                self.add_via(site[0], site[1], code, name, size=PWR_VIA_S if pwr else VIA_S, drill=PWR_VIA_D if pwr else VIA_D)
                add_node(site[0], site[1])

        # remaining SMD (not U1) vias
        for i, p in enumerate(uniq):
            if p["ref"] == "U1" or p["pth"]:
                continue
            cluster = uf.find(i)
            has_pth = any(uniq[k]["pth"] and uf.find(k) == cluster for k in range(len(uniq)))
            others = any(uf.find(k) != cluster for k in range(len(uniq)))
            if has_pth and not others:
                continue
            if has_pth and others:
                continue
            if in_rf(p["x"], p["y"]) and name in RF_OK:
                continue
            site = self.local_via(p, name, pwr=pwr)
            if not site:
                if name in PLANE:
                    print(f"NOVIA {name} {p['ref']}")
                    self.fail += 1
                continue
            if not self.route_f(p["x"], p["y"], site[0], site[1], name, width, code):
                continue
            self.add_via(site[0], site[1], code, name, size=PWR_VIA_S if pwr else VIA_S, drill=PWR_VIA_D if pwr else VIA_D)
            add_node(site[0], site[1])

        if name in PLANE:
            return

        WRAP = name.startswith(("P0.", "MAGPIO", "MIPI", "COEX")) or name in (
            "SWDCLK",
            "SWDIO",
            "nRESET",
        )
        if not WRAP:
            return

        via = self.u1_via.get(name)
        pths = [p for p in uniq if p["pth"]]
        if via and pths:
            south = [p for p in pths if p["y"] > 70]
            primary = min(south or pths, key=lambda p: hypot(via[0], via[1], p["x"], p["y"]))
            self.wrap_commit(primary["x"], primary["y"], via[0], via[1], name, width, code)
            for p in pths:
                if p is primary:
                    continue
                if p["y"] > 70 or p["x"] > 100 or 58 < p["y"] < 66:
                    self.wrap_commit(primary["x"], primary["y"], p["x"], p["y"], name, width, code)
            return
        if len(nodes) < 2:
            # leftover SMD clusters: F.Cu then inner from pad coords (SMD only if same layer)
            groups = uf.groups()
            if len(groups) > 1:
                reps = [uniq[g[0]] for g in groups]
                for a, b in zip(reps, reps[1:]):
                    if self.route_f(a["x"], a["y"], b["x"], b["y"], name, width, code):
                        continue
                    self.fail += 1
                    print(f"FAIL leftover {name} {a['ref']}-{b['ref']}")
            return

        connected = [nodes[0]]
        remaining = nodes[1:]
        while remaining:
            best = None
            for c in connected:
                for ri, r in enumerate(remaining):
                    d = abs(c[0] - r[0]) + abs(c[1] - r[1])
                    if best is None or d < best[0]:
                        best = (d, ri, c, r)
            _, ri, src, dst = best
            if self.route_inner(src[0], src[1], dst[0], dst[1], name, width, code):
                connected.append(dst)
                remaining.pop(ri)
                continue
            if self.route_f(src[0], src[1], dst[0], dst[1], name, width, code):
                connected.append(dst)
                remaining.pop(ri)
                continue
            self.fail += 1
            print(f"FAIL {name} {dst[0]:.1f},{dst[1]:.1f}")
            remaining.pop(ri)

    def stitch_gnd(self):
        gnd = self.board.FindNet("GND")
        code = gnd.GetNetCode()
        n = 0
        sites = [(float(x), float(y)) for x in range(6, 115, 6) for y in range(6, 75, 6)]
        sites += [(float(x), float(y)) for x in range(6, 22, 4) for y in (24, 28, 32, 36, 48, 52, 56, 60)]
        for x, y in sites:
            if not self.via_ok(x, y, "GND", pwr=False):
                continue
            if in_box(x, y, U1_BOX):
                continue
            self.add_via(x, y, code, "GND", size=0.60, drill=0.30)
            n += 1
        print("gnd stitch", n)

    def silk(self):
        for fp in self.board.GetFootprints():
            ref = fp.Reference()
            bb = fp.GetBoundingBox(False, False)
            x = mm(bb.GetCenter().x)
            y = mm(bb.GetTop()) - 0.65
            if y < 1.1:
                y = mm(bb.GetBottom()) + 0.65
            ref.SetPosition(vec(x, y))
            if fp.GetReference()[0] in "CRL" and not fp.GetReference().startswith("U"):
                fp.Value().SetVisible(False)
        print("silk updated")


def net_order(name):
    if name in RF_NETS:
        return (0, name)
    if name in ("GNSS_VBIAS", "GNSS_LNA_EN"):
        return (1, name)
    if name.startswith("LED") or name.startswith("VIN"):
        return (2, name)
    if name.startswith("SIM"):
        return (3, name)
    if name.startswith("P0.") or name.startswith("MAGPIO") or name.startswith("MIPI") or name.startswith("COEX") or name in (
        "SWDCLK",
        "SWDIO",
        "nRESET",
        "nRESET_SW",
        "ENABLE",
        "DEC0",
    ):
        return (4, name)
    if name in ("VDD1", "VDD2", "VDD2_MID"):
        return (5, name)
    if name in PLANE:
        return (6, name)
    if name == "VDD_GPIO":
        return (8, name)
    return (7, name)


def main():
    board = pcbnew.LoadBoard(BOARD)
    fp = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    print("oblong", oblong_u1(fp))
    r = Router(board)
    r.collect()
    r.gen_slots()
    r.explicit_rf()
    r.fanout_all_u1()
    for name in sorted(r.by_net.keys(), key=net_order):
        if name in SKIP or name in RF_NETS or name in ("GNSS_VBIAS", "GNSS_LNA_EN"):
            continue
        r.connect_net(name)
    print(f"route ok={r.ok} fail={r.fail}")
    r.silk()
    print("zone fill")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print("saved", BOARD)
    return 0 if r.fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
