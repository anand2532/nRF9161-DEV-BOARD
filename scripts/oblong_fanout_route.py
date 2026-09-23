#!/usr/bin/env python3
"""Oblong outer LGA pads (Nordic b x b1), fanout, B.Cu route, stitch, silk, fill."""
from __future__ import annotations

import heapq
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew

BOARD = "/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
FP_LIB = Path("/workspace/kicad-projects/nRF9161-DEV-BOARD/libraries/Board.pretty/nRF9161_LGA_16.0x10.5mm.kicad_mod")
GRID = 0.30
CLEAR = 0.12
VIA_S, VIA_D = 0.55, 0.25
SIG_W, PWR_W = 0.18, 0.35
EDGE = 0.9
RF_SKIP = {"ANT", "ANT_FIT", "AUX", "AUX_FIT", "GPS", "GNSS_ANT"}
RF_PADS = {"61", "64", "67"}  # keep 0.3 mm; already have 50 ohm traces


def nm(x):
    return int(pcbnew.FromMM(float(x)))


def mm(v):
    return pcbnew.ToMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


def add_track(board, x1, y1, x2, y2, layer, width, netcode):
    if math.hypot(x2 - x1, y2 - y1) < 0.02:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(nm(width))
    t.SetLayer(layer)
    t.SetNetCode(netcode)
    board.Add(t)


def add_via(board, x, y, netcode):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetWidth(nm(VIA_S))
    v.SetDrill(nm(VIA_D))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(netcode)
    board.Add(v)


def add_text(board, text, x, y, size=1.0, angle=0, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(vec(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(nm(size), nm(size)))
    t.SetTextThickness(nm(max(0.12, size * 0.15)))
    if angle:
        t.SetTextAngleDegrees(angle)
    if bold:
        t.SetBold(True)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(t)


class Grid:
    def __init__(self, w, h, pitch):
        self.pitch = pitch
        self.nx = int(math.ceil(w / pitch)) + 1
        self.ny = int(math.ceil(h / pitch)) + 1
        self.occ = [[0] * self.ny for _ in range(self.nx)]

    def ij(self, x, y):
        return int(round(x / self.pitch)), int(round(y / self.pitch))

    def xy(self, i, j):
        return i * self.pitch, j * self.pitch

    def inb(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    def stamp(self, x, y, r, code):
        i0, j0 = self.ij(x - r, y - r)
        i1, j1 = self.ij(x + r, y + r)
        rr = (r + 0.01) ** 2
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if not self.inb(i, j):
                    continue
                gx, gy = self.xy(i, j)
                if (gx - x) ** 2 + (gy - y) ** 2 <= rr:
                    cur = self.occ[i][j]
                    if cur == 0 or cur == code:
                        self.occ[i][j] = code
                    else:
                        self.occ[i][j] = -1

    def stamp_seg(self, x1, y1, x2, y2, r, code):
        dist = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(dist / (self.pitch * 0.5)))
        for k in range(n + 1):
            t = k / n
            self.stamp(x1 + t * (x2 - x1), y1 + t * (y2 - y1), r, code)

    def blocked(self, i, j, net):
        if not self.inb(i, j):
            return True
        v = self.occ[i][j]
        return v != 0 and v != net

    def astar(self, start, goal, net, extra=None):
        si, sj = self.ij(*start)
        gi, gj = self.ij(*goal)

        def snap(i, j):
            for rad in range(0, 10):
                for di in range(-rad, rad + 1):
                    for dj in range(-rad, rad + 1):
                        ii, jj = i + di, j + dj
                        if not self.blocked(ii, jj, net) and (extra is None or not extra(ii, jj)):
                            return ii, jj
            return None

        s, g = snap(si, sj), snap(gi, gj)
        if not s or not g:
            return None
        si, sj = s
        gi, gj = g
        if (si, sj) == (gi, gj):
            return [self.xy(si, sj)]
        h = lambda i, j: abs(i - gi) + abs(j - gj)
        openh = [(h(si, sj), 0, si, sj)]
        came, gscore, seen = {}, {(si, sj): 0}, set()
        steps = 0
        while openh:
            steps += 1
            if steps > 200000:
                return None
            _, cost, i, j = heapq.heappop(openh)
            if (i, j) in seen:
                continue
            seen.add((i, j))
            if (i, j) == (gi, gj):
                path = [(i, j)]
                while (i, j) in came:
                    i, j = came[(i, j)]
                    path.append((i, j))
                path.reverse()
                return [self.xy(a, b) for a, b in path]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if self.blocked(ni, nj, net) or (extra and extra(ni, nj)):
                    continue
                ng = cost + 1
                if ng < gscore.get((ni, nj), 1e18):
                    gscore[(ni, nj)] = ng
                    came[(ni, nj)] = (i, j)
                    heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj))
        return None


def manhattan(path):
    if not path:
        return []
    pts = [path[0]]
    for x, y in path[1:]:
        px, py = pts[-1]
        if abs(x - px) > 0.02 and abs(y - py) > 0.02:
            pts.append((x, py))
        pts.append((x, y))
    return pts


def update_library_oblong():
    text = FP_LIB.read_text()
    if text.count("(size 0.8") > 40:
        print("library already oblong")
        return

    def repl(m):
        num, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if num in RF_PADS or num == "103" or int(num) >= 104:
            return m.group(0)
        xmin, xmax, ymin, ymax = -7.75, 7.75, -5.0, 5.0
        nx, ny, sx, sy = x, y, 0.3, 0.3
        west = abs(x - xmin) < 0.02
        east = abs(x - xmax) < 0.02
        south = abs(y - ymin) < 0.02
        north = abs(y - ymax) < 0.02
        if not (west or east or south or north):
            return m.group(0)
        if west:
            nx, sx, sy = x - 0.25, 0.8, 0.3
        elif east:
            nx, sx, sy = x + 0.25, 0.8, 0.3
        if south:
            ny, sx, sy = (y - 0.25 if not (west or east) else ny), (0.8 if west or east else 0.3), 0.8 if not (west or east) else sy
            if west or east:
                ny = y - 0.25
                sx, sy = 0.8, 0.8
        elif north:
            if west or east:
                ny = y + 0.25
                sx, sy = 0.8, 0.8
            else:
                ny, sx, sy = y + 0.25, 0.3, 0.8
        return (
            f'(pad "{num}" smd roundrect\n'
            f'\t\t(at {nx} {ny})\n'
            f'\t\t(size {sx} {sy})\n'
        )

    new, n = re.subn(
        r'\(pad "(\d+)" smd roundrect\n\t\t\(at ([-\d.]+) ([-\d.]+)\)\n\t\t\(size 0\.3 0\.3\)\n',
        repl,
        text,
    )
    FP_LIB.write_text(new)
    print("library pads rewritten", n)


def oblong_u1(fp):
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in RF_PADS or num == "103" or (num.isdigit() and int(num) >= 104):
            continue
        rel = pad.GetFPRelativePosition()
        x, y = mm(rel.x), mm(rel.y)
        west = abs(x + 7.75) < 0.05
        east = abs(x - 7.75) < 0.05
        south = abs(y + 5.0) < 0.05
        north = abs(y - 5.0) < 0.05
        if not (west or east or south or north):
            continue
        nx, ny, sx, sy = x, y, 0.3, 0.3
        if west:
            nx, sx, sy = x - 0.25, 0.8, 0.3
        elif east:
            nx, sx, sy = x + 0.25, 0.8, 0.3
        if south:
            if west or east:
                ny, sx, sy = y - 0.25, 0.8, 0.8
            else:
                ny, sx, sy = y - 0.25, 0.3, 0.8
        elif north:
            if west or east:
                ny, sx, sy = y + 0.25, 0.8, 0.8
            else:
                ny, sx, sy = y + 0.25, 0.3, 0.8
        pad.SetFPRelativePosition(vec(nx, ny))
        pad.SetSize(pcbnew.VECTOR2I(nm(sx), nm(sy)))
        pad.SetRoundRectRadiusRatio(0.15)


def is_pth(pad):
    return pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)


def main():
    update_library_oblong()
    board = pcbnew.LoadBoard(BOARD)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = nm(0.10)
    ds.m_TrackMinWidth = nm(0.10)

    fp = None
    for f in board.GetFootprints():
        if f.GetReference() == "U1":
            fp = f
            break
    if not fp:
        print("U1 missing")
        return 1
    oblong_u1(fp)
    print("U1 outer pads oblong")

    bbox = board.GetBoardEdgesBoundingBox()
    w, h = mm(bbox.GetWidth()), mm(bbox.GetHeight())
    gB = Grid(w, h, GRID)
    for i in range(gB.nx):
        for j in range(gB.ny):
            x, y = gB.xy(i, j)
            if x < EDGE or y < EDGE or x > w - EDGE or y > h - EDGE:
                gB.occ[i][j] = -1

    pads_by_net = defaultdict(list)
    for pad in board.GetPads():
        name = pad.GetNetname()
        if not name:
            continue
        pos = pad.GetPosition()
        x, y = mm(pos.x), mm(pos.y)
        size = pad.GetSize()
        pth = is_pth(pad)
        parent = pad.GetParentFootprint()
        ref = parent.GetReference() if parent else ""
        r = max(mm(size.x), mm(size.y)) / 2 + 0.02
        code = pad.GetNetCode()
        if pth:
            gB.stamp(x, y, r, code)
        pads_by_net[name].append(
            dict(x=x, y=y, code=code, pth=pth, ref=ref, num=pad.GetNumber(), name=name)
        )

    for tr in board.GetTracks():
        code = tr.GetNetCode()
        if isinstance(tr, pcbnew.PCB_VIA):
            p = tr.GetPosition()
            gB.stamp(mm(p.x), mm(p.y), VIA_S / 2 + CLEAR, code)
        else:
            if tr.GetLayer() != pcbnew.B_Cu:
                continue
            s, e = tr.GetStart(), tr.GetEnd()
            gB.stamp_seg(mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(tr.GetWidth()) / 2 + CLEAR, code)

    def ring_slots(cx, cy, hw, hh, margin, step):
        left, right = cx - hw - margin, cx + hw + margin
        top, bot = cy - hh - margin, cy + hh + margin
        pts = []
        x, y = left, top
        path = [
            (right - left, 0),
            (0, bot - top),
            (left - right, 0),
            (0, top - bot),
        ]
        for dx, dy in path:
            dist = math.hypot(dx, dy)
            n = max(1, int(round(dist / step)))
            for k in range(n):
                pts.append((x + dx * k / n, y + dy * k / n))
            x += dx
            y += dy
        return pts

    ux, uy = 36.0, 32.0
    slots = ring_slots(ux, uy, 8.3, 5.6, 1.6, 0.95)
    used_slots = set()

    def take_slot(px, py):
        best = None
        for i, (sx, sy) in enumerate(slots):
            if i in used_slots:
                continue
            d = (sx - px) ** 2 + (sy - py) ** 2
            if best is None or d < best[0]:
                best = (d, i, sx, sy)
        if best is None:
            return None
        used_slots.add(best[1])
        return best[2], best[3]

    routed = failed = 0
    skip_route = {"", "GND", "VDD_nRF"} | RF_SKIP
    for name, pads in sorted(pads_by_net.items()):
        if name in skip_route:
            continue
        code = pads[0]["code"]
        width = PWR_W if name.startswith(("VDD", "VIN", "SIM_1", "SIM_V")) else SIG_W
        nodes = []
        for p in pads:
            if p["pth"]:
                nodes.append((p["x"], p["y"]))
                continue
            if p["ref"] == "U1" and p["num"] in RF_PADS:
                continue
            if p["ref"] == "U1":
                site = take_slot(p["x"], p["y"])
            else:
                site = (p["x"], min(h - 2, p["y"] + 1.2))
            if not site:
                nodes.append((p["x"], p["y"]))
                continue
            vx, vy = site
            add_track(board, p["x"], p["y"], vx, p["y"], pcbnew.F_Cu, width, code)
            add_track(board, vx, p["y"], vx, vy, pcbnew.F_Cu, width, code)
            add_via(board, vx, vy, code)
            gB.stamp(vx, vy, VIA_S / 2 + 0.10, code)
            nodes.append((vx, vy))
        if len(nodes) < 2:
            continue
        connected = [nodes[0]]
        for nxt in nodes[1:]:
            best = min(connected, key=lambda c: abs(c[0] - nxt[0]) + abs(c[1] - nxt[1]))
            path = gB.astar(best, nxt, code)
            if not path:
                failed += 1
                print(f"FAIL {name} {nxt[0]:.1f},{nxt[1]:.1f}")
                continue
            pts = manhattan(path)
            for a, b in zip(pts, pts[1:]):
                add_track(board, a[0], a[1], b[0], b[1], pcbnew.B_Cu, width, code)
                gB.stamp_seg(a[0], a[1], b[0], b[1], width / 2 + CLEAR, code)
            connected.append(nxt)
            routed += 1
    print(f"routed {routed} fail {failed}")

    # GND stitch
    gnd = board.FindNet("GND")
    gnd_code = gnd.GetNetCode() if gnd else 0
    stitch = 0
    sites = [(float(x), float(y)) for x in range(4, 117, 5) for y in range(4, 77, 5)]
    sites += [(float(x), float(y)) for x in range(4, 23, 2) for y in (24, 28, 32, 36, 40, 48, 52, 56, 60)]
    for x, y in sites:
        if 27.5 < x < 44.5 and 24.8 < y < 39.2:
            continue
        i, j = gB.ij(x, y)
        if gB.blocked(i, j, gnd_code):
            continue
        add_via(board, x, y, gnd_code)
        gB.stamp(x, y, VIA_S / 2 + CLEAR, gnd_code)
        stitch += 1
    print("stitch", stitch)

    for fpp in board.GetFootprints():
        fpp.Value().SetVisible(False)
        if not fpp.GetReference().startswith("J"):
            continue
        fpos = fpp.GetPosition()
        fx, fy = mm(fpos.x), mm(fpos.y)
        for pad in fpp.Pads():
            n = pad.GetNetname() or ""
            if not n:
                continue
            label = "3V3" if n == "VDD_GPIO" else n
            p = pad.GetPosition()
            px, py = mm(p.x), mm(p.y)
            ox, oy, ang = 0.0, -1.8, 0
            if fx > 100:
                ox, oy, ang = -2.3, 0.0, 90
            elif fy > 70:
                ox, oy, ang = 0.0, -2.0, 0
            elif fy < 12:
                ox, oy, ang = 0.0, 1.9, 0
            add_text(board, label, px + ox, py + oy, size=0.65, angle=ang)

    extras = [
        ("nRF9161-DEV-BOARD", 60, 2.3, 1.5, True, 0),
        ("LTE/NR+", 8, 26.2, 1.1, False, 0),
        ("GNSS", 8, 46.2, 1.1, False, 0),
        ("nRF9161", 36, 23.5, 1.0, False, 0),
        ("SIM", 96, 38.2, 1.1, False, 0),
        ("SWD", 50, 1.7, 1.0, False, 0),
        ("UART", 116, 3.8, 0.9, False, 90),
        ("SPI", 116, 24.0, 0.9, False, 90),
        ("I2C", 116, 40.0, 0.9, False, 90),
        ("I2S", 108, 3.8, 0.9, False, 90),
        ("PDM", 108, 21.8, 0.9, False, 90),
        ("GPIO", 34, 70.2, 1.0, False, 0),
        ("ADC", 38, 58.2, 0.9, False, 0),
        ("POWER", 76, 5.5, 0.75, False, 0),
        ("STATUS", 80, 11.3, 0.65, False, 0),
        ("LTE", 86, 11.3, 0.65, False, 0),
        ("GNSS", 92, 11.3, 0.65, False, 0),
        ("SPARE", 98, 11.3, 0.65, False, 0),
        ("USER", 80, 21.0, 0.75, False, 0),
        ("RESET", 100, 21.0, 0.75, False, 0),
        ("DISABLE", 92, 21.0, 0.65, False, 0),
        ("VIN 3.0-5.5V", 82, 2.1, 0.75, False, 0),
        ("P0.00-15", 28, 78.5, 0.8, False, 0),
        ("P0.16-31", 88, 78.5, 0.8, False, 0),
        ("1", 4.5, 73.8, 0.7, False, 0),
    ]
    for text, x, y, sz, bold, ang in extras:
        add_text(board, text, x, y, size=sz, angle=ang, bold=bold)

    print("zone fill")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print("saved", BOARD)
    return 0 if failed < 20 else 1


if __name__ == "__main__":
    sys.exit(main())
