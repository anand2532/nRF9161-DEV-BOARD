#!/usr/bin/env python3
"""Route remaining nets, stitch GND, add silkscreen, fill zones (KiCad 9 pcbnew)."""
from __future__ import annotations

import heapq
import math
import sys
from collections import defaultdict

import pcbnew

BOARD_PATH = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
GRID = 0.15  # mm
CLEAR = 0.10
VIA_SIZE = 0.6
VIA_DRILL = 0.3
SIG_W = 0.2
PWR_W = 0.4
RF_W = 0.2
EDGE = 0.9
RF_SKIP = {"ANT", "ANT_FIT", "AUX", "AUX_FIT", "GPS", "GNSS_ANT"}
PWR_PREFIX = ("VDD", "VIN", "SIM_1V8", "SIM_VCC", "GNSS_VBIAS", "GNSS_BIAS")


def mm(v) -> float:
    return pcbnew.ToMM(v)


def nm(x: float) -> int:
    return int(pcbnew.FromMM(float(x)))


def vec(x: float, y: float):
    return pcbnew.VECTOR2I(nm(x), nm(y))


class Grid:
    def __init__(self, w, h, pitch):
        self.pitch = pitch
        self.nx = int(math.ceil(w / pitch)) + 1
        self.ny = int(math.ceil(h / pitch)) + 1
        self.occ = [[0] * self.ny for _ in range(self.nx)]  # 0 free, -1 block, else netcode
        self.w = w
        self.h = h

    def ij(self, x, y):
        return int(round(x / self.pitch)), int(round(y / self.pitch))

    def xy(self, i, j):
        return i * self.pitch, j * self.pitch

    def inb(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    def stamp(self, x, y, r, code):
        i0, j0 = self.ij(x - r, y - r)
        i1, j1 = self.ij(x + r, y + r)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if not self.inb(i, j):
                    continue
                gx, gy = self.xy(i, j)
                if (gx - x) ** 2 + (gy - y) ** 2 <= (r + 0.01) ** 2:
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
        return v != 0 and v != net and v != -2

    def astar(self, start, goal, net, extra_block=None):
        si, sj = self.ij(*start)
        gi, gj = self.ij(*goal)
        if not self.inb(si, sj) or not self.inb(gi, gj):
            return None
        # snap to nearest free
        def nearest_free(i, j):
            if not self.blocked(i, j, net) and (extra_block is None or not extra_block(i, j)):
                return i, j
            for rad in range(1, 8):
                for di in range(-rad, rad + 1):
                    for dj in range(-rad, rad + 1):
                        ii, jj = i + di, j + dj
                        if not self.blocked(ii, jj, net) and (
                            extra_block is None or not extra_block(ii, jj)
                        ):
                            return ii, jj
            return None

        s = nearest_free(si, sj)
        g = nearest_free(gi, gj)
        if not s or not g:
            return None
        si, sj = s
        gi, gj = g
        if (si, sj) == (gi, gj):
            return [self.xy(si, sj)]
        h = lambda i, j: abs(i - gi) + abs(j - gj)
        openh = [(h(si, sj), 0, si, sj)]
        came = {}
        gscore = {(si, sj): 0}
        seen = set()
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
        steps = 0
        while openh:
            steps += 1
            if steps > 60000:
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
            for di, dj in dirs:
                ni, nj = i + di, j + dj
                if self.blocked(ni, nj, net):
                    continue
                if extra_block and extra_block(ni, nj):
                    continue
                ng = cost + 1
                if ng < gscore.get((ni, nj), 1e18):
                    gscore[(ni, nj)] = ng
                    came[(ni, nj)] = (i, j)
                    heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj))
        return None


def add_track(board, x1, y1, x2, y2, layer, width, netcode):
    if math.hypot(x2 - x1, y2 - y1) < 0.02:
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(nm(width))
    t.SetLayer(layer)
    t.SetNetCode(netcode)
    board.Add(t)
    return t


def add_via(board, x, y, netcode):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetWidth(nm(VIA_SIZE))
    v.SetDrill(nm(VIA_DRILL))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(netcode)
    board.Add(v)
    return v


def add_text(board, text, x, y, size=1.0, layer=None, angle=0, bold=False):
    if layer is None:
        layer = pcbnew.F_SilkS
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(vec(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(nm(size), nm(size)))
    t.SetTextThickness(nm(max(0.12, size * 0.15)))
    if angle:
        t.SetTextAngleDegrees(angle)
    if bold:
        t.SetBold(True)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(t)
    return t


def is_pth(pad) -> bool:
    attr = pad.GetAttribute()
    return attr in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)


def net_width(name: str) -> float:
    if name in RF_SKIP:
        return RF_W
    if name.startswith(PWR_PREFIX):
        return PWR_W
    return SIG_W


def rf_block(i, j, grid: Grid):
    x, y = grid.xy(i, j)
    return x < 23.5 and 18.0 < y < 66.0


def simplify(path):
    if len(path) < 3:
        return path
    out = [path[0]]
    for p in path[1:]:
        ax, ay = out[-1]
        # merge colinear later
        out.append(p)
    # collapse colinear
    col = [out[0]]
    for i in range(1, len(out) - 1):
        x0, y0 = col[-1]
        x1, y1 = out[i]
        x2, y2 = out[i + 1]
        if abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) < 1e-6:
            continue
        col.append(out[i])
    col.append(out[-1])
    return col


def path_to_manhattan(path):
    """Ensure only H/V segments."""
    if not path:
        return []
    pts = [path[0]]
    for x, y in path[1:]:
        px, py = pts[-1]
        if abs(x - px) > 0.01 and abs(y - py) > 0.01:
            pts.append((x, py))
        pts.append((x, y))
    return pts


def main():
    board = pcbnew.LoadBoard(BOARD_PATH)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = nm(0.10)
    ds.m_TrackMinWidth = nm(0.10)
    ds.m_ViasMinSize = nm(0.45)
    ds.m_MinThroughDrill = nm(0.25)
    try:
        ds.SetCustomTrackWidth(nm(0.20))
        ds.SetCustomViaSize(nm(0.60))
        ds.SetCustomViaDrill(nm(0.30))
    except Exception:
        pass

    bbox = board.GetBoardEdgesBoundingBox()
    w, h = mm(bbox.GetWidth()), mm(bbox.GetHeight())
    print(f"board {w:.2f}x{h:.2f} mm")

    gF = Grid(w, h, GRID)
    gB = Grid(w, h, GRID)

    # board edge
    for i in range(gF.nx):
        for j in range(gF.ny):
            x, y = gF.xy(i, j)
            if x < EDGE or y < EDGE or x > w - EDGE or y > h - EDGE:
                gF.occ[i][j] = -1
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
        r = max(mm(size.x), mm(size.y)) / 2 + (0.04 if pth else 0.03)
        code = pad.GetNetCode()
        gF.stamp(x, y, r, code)
        if pth:
            gB.stamp(x, y, r, code)
        fp = pad.GetParentFootprint() if hasattr(pad, "GetParentFootprint") else None
        ref = fp.GetReference() if fp else ""
        pads_by_net[name].append(
            {
                "x": x,
                "y": y,
                "code": code,
                "pth": pth,
                "ref": ref,
                "pad": pad,
            }
        )

    for tr in board.GetTracks():
        code = tr.GetNetCode()
        if isinstance(tr, pcbnew.PCB_VIA):
            pos = tr.GetPosition()
            x, y = mm(pos.x), mm(pos.y)
            try:
                vw = mm(tr.GetWidth(pcbnew.F_Cu))
            except Exception:
                vw = VIA_SIZE
            r = vw / 2 + CLEAR
            gF.stamp(x, y, r, code)
            gB.stamp(x, y, r, code)
        else:
            s, e = tr.GetStart(), tr.GetEnd()
            x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
            r = mm(tr.GetWidth()) / 2 + CLEAR
            layer = tr.GetLayer()
            if layer == pcbnew.F_Cu:
                gF.stamp_seg(x1, y1, x2, y2, r, code)
            elif layer == pcbnew.B_Cu:
                gB.stamp_seg(x1, y1, x2, y2, r, code)
            else:
                gF.stamp_seg(x1, y1, x2, y2, r, code)
                gB.stamp_seg(x1, y1, x2, y2, r, code)

    routed = failed = 0
    skip_names = {"", "GND"}

    def try_via(x, y, code, name, ref=""):
        """Search nearby free via site, preferring away from U1 center."""
        ux, uy = 36.0, 32.0
        candidates = []
        dists = (0.9, 1.2, 1.6, 2.2, 2.8, 3.4)
        angs = list(range(0, 360, 15))
        # bias away from SiP center for U1 pads
        if ref == "U1":
            base = math.degrees(math.atan2(y - uy, x - ux))
            angs = [int(base + d) % 360 for d in range(-60, 61, 15)] + angs
        for dist in dists:
            for ang in angs:
                rad = math.radians(ang)
                vx = x + dist * math.cos(rad)
                vy = y + dist * math.sin(rad)
                if vx < 24 and 18 < vy < 66 and name not in RF_SKIP:
                    continue
                if vx < EDGE + 0.8 or vy < EDGE + 0.8 or vx > w - EDGE - 0.8 or vy > h - EDGE - 0.8:
                    continue
                i, j = gB.ij(vx, vy)
                if gB.blocked(i, j, code) or gF.blocked(i, j, code):
                    continue
                if 28.5 < vx < 43.5 and 25.8 < vy < 38.2:
                    continue
                score = (vx - ux) ** 2 + (vy - uy) ** 2
                candidates.append((score if ref == "U1" else dist, vx, vy))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1], candidates[0][2]

    for name, pads in sorted(pads_by_net.items()):
        if name in skip_names:
            continue
        code = pads[0]["code"]
        width = net_width(name)
        # unique positions
        uniq = []
        seen = set()
        for p in pads:
            key = (round(p["x"], 2), round(p["y"], 2))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(p)
        if len(uniq) < 2:
            continue

        anchors = []  # (x,y) already on this net in copper we own
        # existing vias/tracks already stamped as this net — pick pad sites as seeds
        seed = uniq[0]
        if name in RF_SKIP:
            # F.Cu only, allow RF region
            connected = [seed]
            for p in uniq[1:]:
                path = gF.astar((connected[-1]["x"], connected[-1]["y"]), (p["x"], p["y"]), code)
                if not path:
                    # try from any connected
                    path = None
                    for c in connected:
                        path = gF.astar((c["x"], c["y"]), (p["x"], p["y"]), code)
                        if path:
                            break
                if not path:
                    failed += 1
                    print(f"FAIL RF {name} {p['x']:.1f},{p['y']:.1f}")
                    continue
                pts = path_to_manhattan(simplify(path))
                for a, b in zip(pts, pts[1:]):
                    add_track(board, a[0], a[1], b[0], b[1], pcbnew.F_Cu, width, code)
                    gF.stamp_seg(a[0], a[1], b[0], b[1], width / 2 + CLEAR, code)
                connected.append(p)
                routed += 1
            continue

        # digital/power: fanout SMD to via, route B.Cu
        uniq.sort(key=lambda p: (0 if p["pth"] else 1, p["x"], p["y"]))
        nodes = []
        for p in uniq:
            if p["pth"]:
                nodes.append((p["x"], p["y"]))
                continue
            site = try_via(p["x"], p["y"], code, name, p.get("ref", ""))
            if site is None:
                nodes.append((p["x"], p["y"]))
                continue
            vx, vy = site
            fpath = gF.astar((p["x"], p["y"]), (vx, vy), code)
            if not fpath:
                # orthogonal stub fallback
                fpath = [(p["x"], p["y"]), (vx, p["y"]), (vx, vy)]
            pts = path_to_manhattan(simplify(fpath))
            ok = True
            for a, b in zip(pts, pts[1:]):
                add_track(board, a[0], a[1], b[0], b[1], pcbnew.F_Cu, width, code)
                gF.stamp_seg(a[0], a[1], b[0], b[1], width / 2 + 0.08, code)
            add_via(board, vx, vy, code)
            gF.stamp(vx, vy, VIA_SIZE / 2 + CLEAR, code)
            gB.stamp(vx, vy, VIA_SIZE / 2 + CLEAR, code)
            nodes.append((vx, vy))

        if len(nodes) < 2:
            continue
        connected = [nodes[0]]
        extra = lambda i, j: rf_block(i, j, gB)
        for nxt in nodes[1:]:
            path = None
            best_c = connected[0]
            # nearest connected
            best_c = min(connected, key=lambda c: abs(c[0] - nxt[0]) + abs(c[1] - nxt[1]))
            path = gB.astar(best_c, nxt, code, extra_block=extra)
            if not path:
                for c in connected:
                    path = gB.astar(c, nxt, code, extra_block=extra)
                    if path:
                        break
            if not path:
                path = gB.astar(best_c, nxt, code, extra_block=None)
            if not path:
                failed += 1
                print(f"FAIL {name} -> {nxt[0]:.1f},{nxt[1]:.1f}")
                continue
            pts = path_to_manhattan(simplify(path))
            for a, b in zip(pts, pts[1:]):
                add_track(board, a[0], a[1], b[0], b[1], pcbnew.B_Cu, width, code)
                gB.stamp_seg(a[0], a[1], b[0], b[1], width / 2 + CLEAR, code)
            connected.append(nxt)
            routed += 1

    print(f"route connections ok={routed} fail={failed}")

    # GND stitching
    gnd = board.FindNet("GND")
    gnd_code = gnd.GetNetCode() if gnd else 0
    stitch = 0
    if gnd_code:
        # grid + ring around U1 and RF
        sites = []
        for x in range(3, int(w) - 2, 5):
            for y in range(3, int(h) - 2, 5):
                sites.append((float(x), float(y)))
        # denser around U1
        for x in [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46]:
            for y in [23, 25, 27, 39, 41]:
                sites.append((float(x), float(y)))
        # RF stitching
        for x in [4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
            for y in [24, 28, 32, 36, 40, 44, 48, 52, 56, 60]:
                sites.append((float(x), float(y)))
        for x, y in sites:
            i, j = gB.ij(x, y)
            if gB.blocked(i, j, gnd_code) or gF.blocked(i, j, gnd_code):
                continue
            if 28.5 < x < 43.5 and 26 < y < 38:
                continue  # under LGA body
            add_via(board, x, y, gnd_code)
            gF.stamp(x, y, VIA_SIZE / 2 + CLEAR, gnd_code)
            gB.stamp(x, y, VIA_SIZE / 2 + CLEAR, gnd_code)
            stitch += 1
    print(f"GND stitch vias {stitch}")

    # Silkscreen: connector pin names from pad nets
    silk_nets_short = {
        "VDD_GPIO": "3V3",
        "VDD_nRF": "VDD",
        "GNSS_LNA_EN": "LNA_EN",
        "GNSS_VBIAS": "BIAS",
        "GNSS_ANT": "GNSS",
        "ANT_FIT": "LTE",
        "nRESET": "RST",
        "SWCLK": "CLK",
        "SWDIO": "DIO",
    }
    done_labels = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        pos = fp.GetPosition()
        fx, fy = mm(pos.x), mm(pos.y)
        # shrink overlapping values
        val = fp.Value()
        val.SetVisible(False)
        # connector pin silk
        if ref.startswith("J") or ref.startswith("SW") or ref.startswith("TP"):
            pads = list(fp.Pads())
            if ref.startswith("J") and len(pads) >= 2:
                for pad in pads:
                    n = pad.GetNetname()
                    if not n or n == "GND" and pad.GetNumber() not in ("1", "2", "3"):
                        label = silk_nets_short.get(n, n)
                    else:
                        label = silk_nets_short.get(n, n)
                    if n == "GND":
                        label = "GND"
                    if n.startswith("P0."):
                        label = n
                    p = pad.GetPosition()
                    px, py = mm(p.x), mm(p.y)
                    # offset toward board interior
                    ox = 0
                    oy = -1.6 if fy > 70 else (1.6 if fy < 12 else 0)
                    if fx > 100:
                        ox, oy = -2.6, 0
                    elif fy > 70:
                        ox, oy = 0, -2.2
                    elif fy < 12:
                        ox, oy = 0, 2.0
                    key = (round(px + ox, 1), round(py + oy, 1), label)
                    if key in done_labels:
                        continue
                    done_labels.add(key)
                    ang = 90 if fx > 100 else 0
                    add_text(board, label, px + ox, py + oy, size=0.7, angle=ang)
        # LED / button names
    extras = [
        ("nRF9161-DEV-BOARD", 60, 2.4, 1.6, True),
        ("LTE/NR+", 8, 26.5, 1.1, False),
        ("GNSS", 8, 46.5, 1.1, False),
        ("nRF9161", 36, 23.6, 1.0, False),
        ("SIM", 96, 38.5, 1.1, False),
        ("SWD", 50, 1.8, 1.0, False),
        ("UART", 116, 4.2, 0.9, False),
        ("SPI", 116, 24.2, 0.9, False),
        ("I2C", 116, 40.2, 0.9, False),
        ("I2S", 108, 4.2, 0.9, False),
        ("PDM", 108, 22.2, 0.9, False),
        ("GPIO", 30, 70.5, 1.0, False),
        ("ADC", 38, 58.5, 0.9, False),
        ("POWER", 76, 5.6, 0.8, False),
        ("STATUS", 80, 11.4, 0.7, False),
        ("LTE", 86, 11.4, 0.7, False),
        ("GNSS", 92, 11.4, 0.7, False),
        ("SPARE", 98, 11.4, 0.7, False),
        ("USER", 80, 21.2, 0.8, False),
        ("RESET", 100, 21.2, 0.8, False),
        ("DISABLE", 92, 21.2, 0.7, False),
        ("VIN 3.0-5.5V", 82, 2.2, 0.8, False),
        ("J_GPIO P0.00-15", 28, 78.6, 0.8, False),
        ("J_GPIO P0.16-31", 88, 78.6, 0.8, False),
        ("PIN1", 4.2, 73.5, 0.6, False),
        ("RF KEEPOUT: matching + U.FL. Solid L2 GND under 50R microstrip.", 40, 48.5, 0.6, False),
    ]
    for text, x, y, sz, bold in extras:
        add_text(board, text, x, y, size=sz, bold=bold)

    # Fill zones
    print("filling zones...")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    pcbnew.SaveBoard(BOARD_PATH, board)
    print("saved", BOARD_PATH)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
