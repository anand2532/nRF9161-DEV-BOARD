#!/usr/bin/env python3
"""Complete nRF9161-DEV-BOARD routing. Geometric clearance; never force a short."""
from __future__ import annotations

import heapq
import math
import shutil
import sys
from collections import defaultdict

import pcbnew

ROOT = "/workspace/kicad-projects/nRF9161-DEV-BOARD"
BOARD = f"{ROOT}/nRF9161-DEV-BOARD.kicad_pcb"
BACKUP = f"{ROOT}/.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-fullroute"

U1C = (36.0, 32.0)
EDGE = 0.80
VIA_S, VIA_D = 0.60, 0.30
PWR_VIA_S, PWR_VIA_D = 0.80, 0.40
SIG_W, PWR_W, RF_W = 0.18, 0.40, 0.20
RF_PADS = {"61", "64", "67"}
RF_NETS = {"ANT", "ANT_FIT", "AUX", "AUX_FIT", "GPS", "GNSS_ANT"}
RF_OK = RF_NETS | {"GNSS_VBIAS", "GNSS_LNA_EN"}
SKIP = {"", "GND"}
PLANE = {"VDD_nRF"}
J18_BOX = (34.2, 59.5, 63.5, 64.8)
U1_BOX = (27.4, 25.2, 44.6, 39.4)
RF_BOX = (0.0, 20.0, 24.2, 64.0)
UFL = [(5.2, 29.6, 12.4, 34.7), (5.2, 49.6, 12.4, 54.7)]
ADC = {"P0.13", "P0.14", "P0.15", "P0.16", "P0.17", "P0.18", "P0.19", "P0.20", "VDD_GPIO"}
LONG_BCU = None  # filled below

# Open an east via alley between U1 and VDD caps.
MOVES = {
    "C4": (51.0, 35.0),
    "C5": (51.0, 31.0),
    "C6": (51.0, 27.0),
    "C10": (51.0, 39.0),
    "C13": (49.2, 29.6),
    "C39": (46.0, 16.0),
    "TP17": (52.0, 44.0),
    "TP18": (48.0, 20.0),
}


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


def dist_seg_aabb(cx, cy, sx, sy, x1, y1, x2, y2):
    n = max(1, int(hypot(x1, y1, x2, y2) / 0.12))
    best = 1e9
    hx, hy = sx / 2, sy / 2
    for k in range(n + 1):
        t = k / n
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        dx = max(abs(x - cx) - hx, 0.0)
        dy = max(abs(y - cy) - hy, 0.0)
        best = min(best, math.hypot(dx, dy))
    return best


def seg_seg(a1, a2, b1, b2):
    d = min(
        dist_seg(a1[0], a1[1], b1[0], b1[1], b2[0], b2[1]),
        dist_seg(a2[0], a2[1], b1[0], b1[1], b2[0], b2[1]),
        dist_seg(b1[0], b1[1], a1[0], a1[1], a2[0], a2[1]),
        dist_seg(b2[0], b2[1], a1[0], a1[1], a2[0], a2[1]),
    )

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    if cross(a1, a2, b1) * cross(a1, a2, b2) < 0 and cross(b1, b2, a1) * cross(b1, b2, a2) < 0:
        return 0.0
    return d


def in_box(x, y, box):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def net_width(name):
    if name in RF_NETS:
        return RF_W
    if name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC")) or name in PLANE:
        return PWR_W
    return SIG_W


def is_pth(pad):
    return pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH


def use_bcu(name):
    return name.startswith(("P0.", "MAGPIO", "MIPI", "COEX", "SIM")) or name in (
        "SWDCLK",
        "SWDIO",
        "nRESET",
        "ENABLE",
        "VDD_GPIO",
    )


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


def move_parts(board):
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in MOVES:
            x, y = MOVES[ref]
            fp.SetPosition(vec(x, y))
            print(f"move {ref} -> {x},{y}")


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
        self.pads = []
        self.by_net = defaultdict(list)
        self.tracks = []
        self.vias = []
        self.ok = 0
        self.fail = 0
        self.u1_via = {}
        self.chan = 0

    def collect(self):
        self.pads = []
        self.by_net = defaultdict(list)
        for pad in self.board.GetPads():
            name = pad.GetNetname() or ""
            pos = pad.GetPosition()
            size = pad.GetSize()
            parent = pad.GetParentFootprint()
            num = pad.GetNumber()
            pth = is_pth(pad)
            npth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            # 0402 libraries often ship extra unnumbered, netless pads that
            # sit on top of the real pad and falsely block every escape.
            if not num and not pth and not npth:
                continue
            rec = {
                "x": mm(pos.x),
                "y": mm(pos.y),
                "sx": mm(size.x),
                "sy": mm(size.y),
                "code": pad.GetNetCode(),
                "pth": pth,
                "npth": npth,
                "ref": parent.GetReference() if parent else "",
                "num": num,
                "name": name,
                "r": min(mm(size.x), mm(size.y)) / 2,
            }
            self.pads.append(rec)
            if name:
                self.by_net[name].append(rec)
        self.vias = []
        self.tracks = []
        for tr in self.board.GetTracks():
            if isinstance(tr, pcbnew.PCB_VIA):
                pt = tr.GetPosition()
                try:
                    w = mm(tr.GetFrontWidth())
                except Exception:
                    w = VIA_S
                if w < 0.3:
                    w = VIA_S
                self.vias.append(
                    {
                        "x": mm(pt.x),
                        "y": mm(pt.y),
                        "n": tr.GetNetname(),
                        "r": w / 2,
                        "drill": mm(tr.GetDrill()) / 2 if tr.GetDrill() else VIA_D / 2,
                        "obj": tr,
                    }
                )
            else:
                s, e = tr.GetStart(), tr.GetEnd()
                self.tracks.append(
                    {
                        "x1": mm(s.x),
                        "y1": mm(s.y),
                        "x2": mm(e.x),
                        "y2": mm(e.y),
                        "ly": tr.GetLayer(),
                        "n": tr.GetNetname(),
                        "w": mm(tr.GetWidth()),
                    }
                )

    def cleanup_vias(self):
        kill = []
        u1 = [p for p in self.pads if p["ref"] == "U1" and p["name"] != "GND"]
        rings = [
            (44.8, 19.0, 49.2, 44.8),
            (25.5, 39.0, 46.8, 44.8),
            (25.5, 18.8, 50.5, 24.8),
            (23.8, 20.0, 27.4, 31.0),
            (9.6, 26.5, 12.6, 45.0),
        ]
        for v in self.vias:
            if v["n"] != "GND":
                continue
            x, y = v["x"], v["y"]
            hit = any(hypot(x, y, p["x"], p["y"]) < 1.25 for p in u1)
            if not hit:
                hit = any(in_box(x, y, box) for box in rings)
            # LGA edge via rows collide with oblong pads
            if 25.0 <= x <= 46.0 and (25.4 <= y <= 27.4 or 36.6 <= y <= 38.6):
                hit = True
            if hit:
                kill.append(v)
        for v in kill:
            self.board.Remove(v["obj"])
        self.vias = [v for v in self.vias if v not in kill]
        print("removed blocking GND vias", len(kill))

    def track_clear(self, x1, y1, x2, y2, layer, width, name):
        if hypot(x1, y1, x2, y2) < 0.03:
            return True
        need = width / 2 + 0.13
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
        for p in self.pads:
            if p["npth"]:
                if dist_seg(p["x"], p["y"], x1, y1, x2, y2) < p["r"] + 0.20:
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
            if v["n"].startswith(("VDD", "VIN")) or v["n"] in PLANE or v["n"] in RF_NETS:
                vneed = width / 2 + 0.16
            if d < v["r"] + vneed:
                return False
            if d < v["drill"] + 0.25 + width / 2:
                return False
        for t in self.tracks:
            if t["ly"] != layer or t["n"] == name:
                continue
            if seg_seg((x1, y1), (x2, y2), (t["x1"], t["y1"]), (t["x2"], t["y2"])) < need + t["w"] / 2:
                return False
        return True

    def path_clear(self, pts, layer, width, name):
        for a, b in zip(pts, pts[1:]):
            if not self.track_clear(a[0], a[1], b[0], b[1], layer, width, name):
                return False
        return True

    def via_ok(self, x, y, name, pwr=False):
        size = PWR_VIA_S if pwr else VIA_S
        drill = PWR_VIA_D if pwr else VIA_D
        if not (EDGE + 1.0 < x < self.w - EDGE - 1.0 and EDGE + 1.0 < y < self.h - EDGE - 1.0):
            return False
        if in_box(x, y, U1_BOX) or (in_box(x, y, RF_BOX) and name not in RF_OK):
            return False
        if in_box(x, y, J18_BOX) and name not in ADC:
            return False
        if any(in_box(x, y, box) for box in UFL):
            return False
        for p in self.pads:
            if p["name"] == name:
                continue
            if p["pth"]:
                need = p["r"] + 0.25 + drill / 2
            else:
                need = max(p["sx"], p["sy"]) / 2 + size / 2 + 0.40
            if hypot(p["x"], p["y"], x, y) < need:
                return False
        for v in self.vias:
            if hypot(v["x"], v["y"], x, y) < (1.00 if v["n"] != name else 0.75):
                return False
        for t in self.tracks:
            if t["n"] == name:
                continue
            if dist_seg(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) < size / 2 + t["w"] / 2 + 0.15:
                return False
        return True

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
        self.tracks.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "ly": layer, "n": name, "w": width})

    def add_via(self, x, y, netcode, name, pwr=False, size=None, drill=None):
        size = size if size is not None else (PWR_VIA_S if pwr else VIA_S)
        drill = drill if drill is not None else (PWR_VIA_D if pwr else VIA_D)
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(vec(x, y))
        v.SetFrontWidth(nm(size))
        try:
            v.SetWidth(pcbnew.F_Cu, nm(size))
            v.SetWidth(pcbnew.B_Cu, nm(size))
        except TypeError:
            pass
        v.SetDrill(nm(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(netcode)
        self.board.Add(v)
        self.vias.append({"x": x, "y": y, "n": name, "r": size / 2, "drill": drill / 2, "obj": v})
        return v

    def commit(self, pts, layer, width, code, name):
        if not self.path_clear(pts, layer, width, name):
            return False
        for a, b in zip(pts, pts[1:]):
            self.add_track(a[0], a[1], b[0], b[1], layer, width, code, name)
        self.ok += 1
        return True

    def jogs_f(self, x1, y1, x2, y2):
        out = [[(x1, y1), (x2, y1), (x2, y2)], [(x1, y1), (x1, y2), (x2, y2)]]
        for d in (-0.7, 0.7, -1.3, 1.3, -2.0, 2.0, -3.0, 3.0, -4.4, 4.4, -6.0, 6.0, -8.5, 8.5):
            out.append([(x1, y1), (x1, y1 + d), (x2, y1 + d), (x2, y2)])
            out.append([(x1, y1), (x1 + d, y1), (x1 + d, y2), (x2, y2)])
        return out

    def astar_f(self, x1, y1, x2, y2, name, width, code):
        pitch = 0.30
        s = (int(round(x1 / pitch)), int(round(y1 / pitch)))
        g = (int(round(x2 / pitch)), int(round(y2 / pitch)))
        net = code
        blocked = set()
        # light occupancy: vias + foreign F.Cu pads
        for v in self.vias:
            if v["n"] == name:
                continue
            i0 = int((v["x"] - 0.55) / pitch)
            i1 = int((v["x"] + 0.55) / pitch)
            j0 = int((v["y"] - 0.55) / pitch)
            j1 = int((v["y"] + 0.55) / pitch)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if hypot(i * pitch, j * pitch, v["x"], v["y"]) <= 0.55:
                        blocked.add((i, j))
        for p in self.pads:
            if p["name"] == name or p["npth"]:
                continue
            rad = max(p["sx"], p["sy"]) / 2 + 0.20
            i0 = int((p["x"] - rad) / pitch)
            i1 = int((p["x"] + rad) / pitch)
            j0 = int((p["y"] - rad) / pitch)
            j1 = int((p["y"] + rad) / pitch)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if hypot(i * pitch, j * pitch, p["x"], p["y"]) <= rad:
                        blocked.add((i, j))
        blocked.discard(s)
        blocked.discard(g)
        h = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
        pq = [(h(s, g), 0, s, None)]
        came = {}
        cost = {s: 0}
        steps = 0
        found = None
        while pq and steps < 8000:
            _, gcost, cur, _ = heapq.heappop(pq)
            steps += 1
            if cur == g:
                found = cur
                break
            if gcost != cost.get(cur):
                continue
            i, j = cur
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (i + di, j + dj)
                if nxt in blocked:
                    continue
                nx, ny = nxt[0] * pitch, nxt[1] * pitch
                if not (1 < nx < self.w - 1 and 1 < ny < self.h - 1):
                    continue
                ng = gcost + 1
                if ng < cost.get(nxt, 1e9):
                    cost[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(pq, (ng + h(nxt, g), ng, nxt, cur))
        if not found:
            return False
        cells = [g]
        while cells[-1] != s:
            cells.append(came[cells[-1]])
        cells.reverse()
        pts = [(x1, y1)]
        for i, j in cells:
            pts.append((i * pitch, j * pitch))
        pts.append((x2, y2))
        # compress collinear
        comp = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - comp[-1][0]) < 0.02 or abs(p[1] - comp[-1][1]) < 0.02:
                if len(comp) >= 2 and (
                    (abs(comp[-1][0] - comp[-2][0]) < 0.02 and abs(p[0] - comp[-1][0]) < 0.02)
                    or (abs(comp[-1][1] - comp[-2][1]) < 0.02 and abs(p[1] - comp[-1][1]) < 0.02)
                ):
                    comp[-1] = p
                    continue
            comp.append(p)
        return self.commit(comp, pcbnew.F_Cu, width, code, name)

    def route_f(self, x1, y1, x2, y2, name, width, code):
        for pts in self.jogs_f(x1, y1, x2, y2):
            if self.commit(pts, pcbnew.F_Cu, width, code, name):
                return True
        if hypot(x1, y1, x2, y2) < 28:
            return self.astar_f(x1, y1, x2, y2, name, width, code)
        return False

    def bcu_candidates(self, x1, y1, x2, y2):
        cands = [
            [(x1, y1), (x2, y1), (x2, y2)],
            [(x1, y1), (x1, y2), (x2, y2)],
        ]
        if y1 > 70 and x1 < 25.0:
            # Stay south of the RF keepout; wrap east before going north.
            for yb in (68.2, 68.8, 69.4, 67.6):
                for col in (25.5, 26.1, 26.7, 27.3, 31.9, 32.5):
                    cands.insert(0, [(x1, y1), (x1, yb), (col, yb), (col, y2), (x2, y2)])
        elif y1 > 70 and x1 < 33.4:
            cands.insert(0, [(x1, y1), (x1, y2), (x2, y2)])
        if y1 > 70 and 64.2 < x1 < 101.5:
            cands.insert(0, [(x1, y1), (x1, y2), (x2, y2)])
        if y1 > 70 and 33.4 <= x1 <= 64.2:
            for col in (32.6, 31.6, 65.2, 66.2):
                for yb in (66.2, 66.8, 67.4, 68.0):
                    cands.append([(x1, y1), (x1, yb), (col, yb), (col, y2), (x2, y2)])
        if x1 > 101:
            for xf in (102.4, 101.8, 103.0, 90.4, 89.8, 91.0):
                cands.insert(0, [(x1, y1), (xf, y1), (xf, y2), (x2, y2)])
            # J14/J15: walk around nano-SIM J7 (x~96, y~48)
            if 44.0 < y1 < 70.0:
                for yb in (14.8, 13.6, 12.4, 11.2, 40.4, 39.6, 38.8, 68.4, 69.0, 69.6):
                    cands.insert(0, [(x1, y1), (106.6, y1), (106.6, yb), (x2, yb), (x2, y2)])
            for xf in (99.2, 99.8, 100.4, 98.6):
                cands.append([(x1, y1), (xf, y1), (xf, y2), (x2, y2)])
        ys = [45.6 + i * 0.55 for i in range(22)] + [65.8 + i * 0.50 for i in range(14)]
        ys += [8.4 + i * 0.55 for i in range(12)]
        xs = [24.9, 25.5, 26.1, 26.7, 27.3, 27.9, 28.5, 31.3, 31.9, 32.5, 33.1]
        xs += [64.7 + i * 0.55 for i in range(16)]
        xs += [98.6, 99.2, 99.8, 100.4, 101.0, 110.0, 110.6, 111.2]
        for yb in ys:
            cands.append([(x1, y1), (x1, yb), (x2, yb), (x2, y2)])
        for xc in xs:
            cands.append([(x1, y1), (xc, y1), (xc, y2), (x2, y2)])
        for yb in ys[:8]:
            for xc in xs[:8]:
                cands.append([(x1, y1), (x1, yb), (xc, yb), (xc, y2), (x2, y2)])
        return cands

    def route_b(self, x1, y1, x2, y2, name, width, code):
        for _ in range(12):
            pts = self.unique_path(x1, y1, x2, y2)
            if self.commit(pts, pcbnew.B_Cu, width, code, name):
                return True
        return self.astar_b(x1, y1, x2, y2, name, width, code)

    def unique_path(self, x1, y1, x2, y2):
        i = self.chan
        self.chan += 1
        if i < 18:
            yb = 46.4 + i * 0.50
        else:
            yb = 66.0 + ((i - 18) % 14) * 0.42
        west = 25.5 + (i % 6) * 0.48
        east = 64.8 + (i % 12) * 0.48
        col = west if min(x1, x2) < 50 else east
        xf = 106.6
        if y1 > 70 and x1 < 25.0:
            ybus = 68.2 + (i % 4) * 0.45
            return [(x1, y1), (x1, ybus), (col, ybus), (col, yb), (x2, yb), (x2, y2)]
        if y1 > 70 and 58 < y2 < 66:
            return [(x1, y1), (x1, y2), (x2, y2)]
        if y1 > 70 and 33.4 <= x1 <= 64.2:
            return [(x1, y1), (x1, yb if yb > 64 else 67.2), (col, yb if yb > 64 else 67.2), (col, yb), (x2, yb), (x2, y2)]
        if y1 > 70:
            return [(x1, y1), (x1, yb), (x2, yb), (x2, y2)]
        if x1 > 101:
            ynorth = 14.8 + (i % 6) * 0.50
            return [(x1, y1), (xf, y1), (xf, ynorth), (x2, ynorth), (x2, y2)]
        return [(x1, y1), (x1, yb), (x2, yb), (x2, y2)]

    def astar_b(self, x1, y1, x2, y2, name, width, code):
        pitch = 0.40
        s = (int(round(x1 / pitch)), int(round(y1 / pitch)))
        g = (int(round(x2 / pitch)), int(round(y2 / pitch)))
        blocked = set()
        rad = 0.42
        for v in self.vias:
            if v["n"] == name:
                continue
            if hypot(v["x"], v["y"], x1, y1) < 0.90 or hypot(v["x"], v["y"], x2, y2) < 0.90:
                continue
            i0, i1 = int((v["x"] - rad) / pitch), int((v["x"] + rad) / pitch)
            j0, j1 = int((v["y"] - rad) / pitch), int((v["y"] + rad) / pitch)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if hypot(i * pitch, j * pitch, v["x"], v["y"]) <= rad:
                        blocked.add((i, j))
        for p in self.pads:
            if p["name"] == name or not p["pth"]:
                continue
            radp = p["r"] + 0.22
            i0, i1 = int((p["x"] - radp) / pitch), int((p["x"] + radp) / pitch)
            j0, j1 = int((p["y"] - radp) / pitch), int((p["y"] + radp) / pitch)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if hypot(i * pitch, j * pitch, p["x"], p["y"]) <= radp:
                        blocked.add((i, j))
        # RF keepout + J18
        i0, i1 = 0, int(24.2 / pitch)
        j0, j1 = int(20.0 / pitch), int(64.0 / pitch)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                blocked.add((i, j))
        if name not in ADC:
            i0, i1 = int(34.2 / pitch), int(63.5 / pitch)
            j0, j1 = int(59.5 / pitch), int(64.8 / pitch)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    blocked.add((i, j))
        for t in self.tracks:
            if t["ly"] != pcbnew.B_Cu or t["n"] == name:
                continue
            radt = t["w"] / 2 + 0.22
            dist = hypot(t["x1"], t["y1"], t["x2"], t["y2"])
            nseg = max(1, int(dist / (pitch * 0.45)))
            for k in range(nseg + 1):
                tt = k / nseg
                x = t["x1"] + tt * (t["x2"] - t["x1"])
                y = t["y1"] + tt * (t["y2"] - t["y1"])
                i0, i1 = int((x - radt) / pitch), int((x + radt) / pitch)
                j0, j1 = int((y - radt) / pitch), int((y + radt) / pitch)
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        if hypot(i * pitch, j * pitch, x, y) <= radt:
                            blocked.add((i, j))
        blocked.discard(s)
        blocked.discard(g)
        h = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
        pq = [(h(s, g), 0, s)]
        came = {}
        cost = {s: 0}
        steps = 0
        found = None
        while pq and steps < 80000:
            _, gcost, cur = heapq.heappop(pq)
            steps += 1
            if cur == g:
                found = cur
                break
            if gcost != cost.get(cur):
                continue
            i, j = cur
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (i + di, j + dj)
                if nxt in blocked:
                    continue
                nx, ny = nxt[0] * pitch, nxt[1] * pitch
                if not (1.2 < nx < self.w - 1.2 and 1.2 < ny < self.h - 1.2):
                    continue
                ng = gcost + 1
                if ng < cost.get(nxt, 1e9):
                    cost[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(pq, (ng + h(nxt, g), ng, nxt))
        if not found:
            return False
        cells = [g]
        while cells[-1] != s:
            cells.append(came[cells[-1]])
        cells.reverse()
        pts = [(x1, y1)]
        for i, j in cells:
            pts.append((i * pitch, j * pitch))
        pts.append((x2, y2))
        comp = [pts[0]]
        for p in pts[1:]:
            if len(comp) >= 2 and (
                (abs(comp[-1][0] - comp[-2][0]) < 0.05 and abs(p[0] - comp[-1][0]) < 0.05)
                or (abs(comp[-1][1] - comp[-2][1]) < 0.05 and abs(p[1] - comp[-1][1]) < 0.05)
            ):
                comp[-1] = p
                continue
            comp.append(p)
        return self.commit(comp, pcbnew.B_Cu, width, code, name)

    def route_to_via(self, x1, y1, vx, vy, name, width, code):
        """Reach a courtyard via from the outside so we do not thread the via row."""
        if vy >= 39.5:
            gate = (vx, 45.6)
        elif vy <= 24.8:
            gate = (vx, 14.8)
        elif vx >= 45.0:
            gate = (49.4, vy)
        else:
            gate = (vx, 45.6)
        if not self.route_b(x1, y1, gate[0], gate[1], name, width, code):
            return False
        return self.commit([(gate[0], gate[1]), (vx, vy)], pcbnew.B_Cu, width, code, name)

    def local_via(self, x, y, name, pwr=False):
        for r in (1.3, 1.7, 2.2, 2.8, 3.5, 4.2):
            for ang in range(0, 360, 30):
                a = math.radians(ang)
                cx, cy = x + r * math.cos(a), y + r * math.sin(a)
                if self.via_ok(cx, cy, name, pwr=pwr):
                    return cx, cy
        return None

    def radial_end(self, p):
        x, y = p["x"], p["y"]
        # Escape along the oblong long axis (never along the pad row).
        if p["sx"] > p["sy"] + 0.05:
            if x < U1C[0]:
                # West RF edge: take the north via ring, not a west via alley.
                col = 25.60 if round(y / 0.5) % 2 == 0 else 26.75
                row = 23.10 if round(x / 0.5) % 2 == 0 else 21.95
                return col, row
            col = 46.20 if round(y / 0.5) % 2 == 0 else 47.40
            return col, y
        if p["sy"] > p["sx"] + 0.05:
            if y < U1C[1]:
                row = 23.10 if round(x / 0.5) % 2 == 0 else 21.95
                return x, row
            row = 41.10 if round(x / 0.5) % 2 == 0 else 42.25
            return x, row
        if x >= 42.0:
            return (46.20 if round(y / 0.5) % 2 == 0 else 47.40), y
        if y <= 28.4:
            return x, (23.10 if round(x / 0.5) % 2 == 0 else 21.95)
        if y >= 35.3:
            return x, (41.10 if round(x / 0.5) % 2 == 0 else 42.25)
        return (25.60 if round(y / 0.5) % 2 == 0 else 26.75), y

    def explicit_rf(self):
        j3 = next(p for p in self.by_net["ANT_FIT"] if p["ref"] == "J3")
        code = j3["code"]
        paths = [
            [(j3["x"], j3["y"]), (8.0, 43.6), (10.9, 43.6), (10.9, 28.0), (12.0, 28.0)],
            [(j3["x"], j3["y"]), (8.0, 44.2), (10.6, 44.2), (10.6, 27.5), (8.0, 27.5), (8.0, 28.0)],
        ]
        for pts in paths:
            if self.commit(pts, pcbnew.F_Cu, RF_W, code, "ANT_FIT"):
                print("J3 SWF tap routed")
                break
        else:
            print("J3 tap FAILED")
            self.fail += 1

        def pair(net, ra, rb):
            pa = next(p for p in self.by_net[net] if p["ref"] == ra and not p["npth"])
            pb = next(p for p in self.by_net[net] if p["ref"] == rb and not p["npth"])
            if not self.route_f(pa["x"], pa["y"], pb["x"], pb["y"], net, net_width(net), pa["code"]):
                print(f"RF pair fail {net} {ra}-{rb}")
                self.fail += 1

        pair("GNSS_LNA_EN", "R4", "TP2")
        vb = self.by_net["GNSS_VBIAS"]
        c28 = next(p for p in vb if p["ref"] == "C28")
        code = c28["code"]
        w = net_width("GNSS_VBIAS")
        for ref in ("C29", "FB5", "C30", "L4"):
            q = next(p for p in vb if p["ref"] == ref)
            ok = False
            for xj in (12.05, 10.45, 12.80):
                pts = [(c28["x"], c28["y"]), (xj, c28["y"]), (xj, q["y"]), (q["x"], q["y"])]
                if self.commit(pts, pcbnew.F_Cu, w, code, "GNSS_VBIAS"):
                    ok = True
                    break
            if not ok:
                if not self.route_f(c28["x"], c28["y"], q["x"], q["y"], "GNSS_VBIAS", w, code):
                    print("GNSS_VBIAS fail", ref)
                    self.fail += 1

        def stub(net, ref, xj):
            pads = [p for p in self.by_net[net] if p["ref"] == ref]
            if not pads:
                return
            p = pads[0]
            others = [q for q in self.by_net[net] if q["ref"] != ref]
            t = min(others, key=lambda q: hypot(p["x"], p["y"], q["x"], q["y"]))
            pts = [(p["x"], p["y"]), (xj, p["y"]), (xj, t["y"]), (t["x"], t["y"])]
            if not self.commit(pts, pcbnew.F_Cu, RF_W, p["code"], net):
                self.route_f(p["x"], p["y"], t["x"], t["y"], net, RF_W, p["code"])

        stub("GNSS_ANT", "C32", 10.6)
        stub("GPS", "C31", 22.4)
        stub("AUX_FIT", "C24", 21.6)

    def fanout_u1(self):
        pads = []
        seen = set()
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
        skip_via = {"DEC0", "VDD1", "VDD2", "VDD_GPIO"}
        n = 0
        for p in pads:
            if p["name"] in skip_via:
                # Local F.Cu to nearby decoupling; no courtyard via.
                continue
            name = p["name"]
            code = p["code"]
            width = net_width(name)
            pwr = name.startswith(("VDD", "VIN")) or name in PLANE
            ex, ey = self.radial_end(p)
            if abs(ex - p["x"]) < 0.05 or abs(ey - p["y"]) < 0.05:
                esc = [(p["x"], p["y"]), (ex, ey)]
            elif p["sx"] > p["sy"]:
                esc = [(p["x"], p["y"]), (ex, p["y"]), (ex, ey)]
            else:
                esc = [(p["x"], p["y"]), (p["x"], ey), (ex, ey)]
            if not self.commit(esc, pcbnew.F_Cu, width, code, name):
                print(f"FANOUT track fail {name} pad{p['num']}")
                self.fail += 1
                continue
            site = None
            dx, dy = ex - p["x"], ey - p["y"]
            for scale in (1.0, 1.2, 1.45, 1.75, 2.1, 2.5):
                sx = p["x"] + dx * scale
                sy = p["y"] + dy * scale
                if self.via_ok(sx, sy, name, pwr=pwr):
                    site = (sx, sy)
                    break
            if not site:
                # small perpendicular stagger only (0.95 mm) so we do not cross neighbors
                for s in (-0.95, 0.95, -1.9, 1.9):
                    if abs(dx) > abs(dy):
                        cand = (ex, ey + s)
                    else:
                        cand = (ex + s, ey)
                    if self.via_ok(cand[0], cand[1], name, pwr=pwr):
                        site = cand
                        break
            if not site:
                print(f"NOVIA U1 {name} pad{p['num']}")
                self.fail += 1
                continue
            if abs(site[0] - ex) > 0.05 or abs(site[1] - ey) > 0.05:
                if abs(dx) > abs(dy):
                    jog = [(ex, ey), (site[0], ey), (site[0], site[1])]
                else:
                    jog = [(ex, ey), (ex, site[1]), (site[0], site[1])]
                if not self.commit(jog, pcbnew.F_Cu, width, code, name):
                    print(f"FANOUT jog fail {name}")
                    self.fail += 1
                    continue
            self.add_via(site[0], site[1], code, name, pwr=pwr)
            self.u1_via[name] = site
            n += 1
        print("U1 fanout vias", n)

    def connected_to_track(self, p, name):
        for t in self.tracks:
            if t["n"] != name:
                continue
            if dist_seg(p["x"], p["y"], t["x1"], t["y1"], t["x2"], t["y2"]) < max(p["sx"], p["sy"]) / 2 + 0.12:
                return True
        for v in self.vias:
            if v["n"] == name and hypot(v["x"], v["y"], p["x"], p["y"]) < 0.55:
                return True
        return False

    def connect_net(self, name):
        pads = [p for p in self.by_net[name] if not p["npth"]]
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
            uniq.append(p)
        uf = UF(len(uniq))
        on = [i for i, p in enumerate(uniq) if self.connected_to_track(p, name)]
        for a, b in zip(on, on[1:]):
            uf.union(a, b)
        if name in self.u1_via:
            u1i = [i for i, p in enumerate(uniq) if p["ref"] == "U1"]
            for i in u1i[1:]:
                uf.union(u1i[0], i)
            on += u1i
            for a, b in zip(on, on[1:]):
                uf.union(a, b)

        if name in PLANE:
            for p in uniq:
                if p["pth"]:
                    continue
                site = self.local_via(p["x"], p["y"], name, pwr=True)
                if not site:
                    print(f"NOVIA plane {name} {p['ref']}")
                    self.fail += 1
                    continue
                if self.route_f(p["x"], p["y"], site[0], site[1], name, width, code):
                    self.add_via(site[0], site[1], code, name, pwr=True)
            return

        pairs = []
        for i, a in enumerate(uniq):
            for j in range(i + 1, len(uniq)):
                b = uniq[j]
                pairs.append((hypot(a["x"], a["y"], b["x"], b["y"]), i, j))
        pairs.sort()
        allow_u1_f = name in {"DEC0", "VDD1", "VDD2", "VDD_GPIO", "ENABLE", "nRESET", "SWDCLK", "SWDIO"}
        for d, i, j in pairs:
            if uf.find(i) == uf.find(j):
                continue
            a, b = uniq[i], uniq[j]
            if (a["ref"] == "U1" or b["ref"] == "U1") and not allow_u1_f:
                continue
            if (a["ref"] == "U1" or b["ref"] == "U1") and d > 12.0:
                continue
            lim = 36.0 if name.startswith(("SIM", "VIN", "VDD", "LED", "ENABLE", "nRESET")) else 14.0
            if d > lim:
                continue
            if a["pth"] and b["pth"] and d > 8.0:
                continue
            if self.route_f(a["x"], a["y"], b["x"], b["y"], name, width, code):
                uf.union(i, j)

        via = self.u1_via.get(name)
        pths = [p for p in uniq if p["pth"]]
        smd_vias = [(v["x"], v["y"]) for v in self.vias if v["n"] == name]
        target = via or (smd_vias[0] if smd_vias else None)

        if target and use_bcu(name):
            primary = None
            if pths:
                south = [p for p in pths if p["y"] > 70]
                primary = min(south or pths, key=lambda p: hypot(target[0], target[1], p["x"], p["y"]))
                if not self.route_to_via(primary["x"], primary["y"], target[0], target[1], name, width, code):
                    print(f"FAIL PTH-U1 {name} {primary['ref']}")
                    self.fail += 1
            for p in pths:
                if p is primary:
                    continue
                src = (primary["x"], primary["y"]) if primary is not None else target
                a, b = (p["x"], p["y"]), src
                # Prefer originating at the south GPIO header.
                if b[1] > 70 and a[1] <= 70:
                    a, b = b, a
                if not self.route_b(a[0], a[1], b[0], b[1], name, width, code):
                    if not self.route_to_via(p["x"], p["y"], target[0], target[1], name, width, code):
                        print(f"FAIL extra PTH {name} {p['ref']}")
                        self.fail += 1

        # leftover SMD to target
        for i, p in enumerate(uniq):
            if p["ref"] == "U1" or p["pth"]:
                continue
            if self.connected_to_track(p, name) and all(uf.find(i) == uf.find(k) or not (uniq[k]["pth"] or uniq[k]["ref"] == "U1") for k in range(len(uniq))):
                continue
            if self.connected_to_track(p, name) and via and name in self.u1_via:
                # may still need via to U1 if not on same copper
                pass
            if all(self.connected_to_track(uniq[k], name) for k in range(len(uniq)) if uniq[k]["ref"] != "U1"):
                if via or not any(q["ref"] == "U1" for q in uniq):
                    continue
            dest = target
            if dest and self.route_f(p["x"], p["y"], dest[0], dest[1], name, width, code):
                uf.union(i, 0)
                continue
            site = self.local_via(p["x"], p["y"], name, pwr=pwr)
            if site and self.route_f(p["x"], p["y"], site[0], site[1], name, width, code):
                self.add_via(site[0], site[1], code, name, pwr=pwr)
                if dest and use_bcu(name):
                    if not self.route_b(site[0], site[1], dest[0], dest[1], name, width, code):
                        print(f"FAIL leftover B {name} {p['ref']}")
                        self.fail += 1
            elif dest:
                print(f"FAIL leftover {name} {p['ref']}")
                self.fail += 1

    def stitch_gnd(self):
        gnd = self.board.FindNet("GND")
        code = gnd.GetNetCode()
        n = 0
        for x in range(10, 112, 10):
            for y in range(10, 72, 10):
                fx, fy = float(x), float(y)
                if not self.via_ok(fx, fy, "GND"):
                    continue
                if in_box(fx, fy, U1_BOX) or in_box(fx, fy, RF_BOX) or in_box(fx, fy, J18_BOX):
                    continue
                self.add_via(fx, fy, code, "GND")
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
    if name.startswith(("P0.", "MAGPIO", "MIPI", "COEX")):
        return (2, name)
    if name in ("DEC0", "ENABLE", "nRESET", "nRESET_SW", "SWDCLK", "SWDIO"):
        return (3, name)
    if name.startswith("SIM"):
        return (4, name)
    if name.startswith("LED") or name.startswith("VIN"):
        return (5, name)
    if name in ("VDD1", "VDD2", "VDD2_MID"):
        return (6, name)
    if name in PLANE:
        return (7, name)
    if name == "VDD_GPIO":
        return (8, name)
    return (9, name)


def main():
    shutil.copy2(BACKUP, BOARD)
    board = pcbnew.LoadBoard(BOARD)
    fp = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    print("oblong", oblong_u1(fp))
    move_parts(board)
    r = Router(board)
    r.collect()
    r.cleanup_vias()
    r.explicit_rf()
    r.fanout_u1()
    for name in sorted(r.by_net.keys(), key=net_order):
        if name in SKIP or name in RF_NETS or name in ("GNSS_VBIAS", "GNSS_LNA_EN"):
            continue
        r.connect_net(name)
    print(f"route ok={r.ok} fail={r.fail}")
    r.stitch_gnd()
    r.silk()
    print("zone fill")
    for z in board.Zones():
        if z.GetNetname() == "GND":
            z.SetLocalClearance(nm(0.25))
            z.SetThermalReliefGap(nm(0.25))
            z.SetThermalReliefSpokeWidth(nm(0.20))
            try:
                z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            except Exception:
                pass
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print("saved", BOARD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
