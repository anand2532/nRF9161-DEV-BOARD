#!/usr/bin/env python3
"""Complete nRF9161-DEV-BOARD routing: oblong LGA fanout, F.Cu locals, B.Cu channels."""
from __future__ import annotations

import heapq
import math
import sys
from collections import defaultdict

import pcbnew

BOARD = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"

RF_PADS = {"61", "64", "67"}
RF_NETS = {"ANT", "ANT_FIT", "AUX", "AUX_FIT", "GPS", "GNSS_ANT"}
SKIP_NETS = {"", "GND"} | RF_NETS
PLANE_NETS = {"VDD_nRF"}  # stitch to In2 with vias only

GRID = 0.35
VIA_S, VIA_D = 0.55, 0.25
SIG_W, PWR_W, RF_W = 0.18, 0.4, 0.2
EDGE = 0.9
U1C = (36.0, 32.0)


def nm(x):
    return int(pcbnew.FromMM(float(x)))


def mm(v):
    return pcbnew.ToMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


def add_track(board, x1, y1, x2, y2, layer, width, netcode):
    if math.hypot(x2 - x1, y2 - y1) < 0.03:
        return False
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(vec(x1, y1))
    t.SetEnd(vec(x2, y2))
    t.SetWidth(nm(width))
    t.SetLayer(layer)
    t.SetNetCode(netcode)
    board.Add(t)
    return True


def add_via(board, x, y, netcode, size=VIA_S, drill=VIA_D):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(x, y))
    v.SetWidth(nm(size))
    v.SetDrill(nm(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(netcode)
    board.Add(v)
    return v


def is_pth(pad):
    return pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)


def net_width(name):
    if name in RF_NETS:
        return RF_W
    if name.startswith(("VDD", "VIN", "SIM_1V8", "SIM_VCC")):
        return PWR_W
    return SIG_W


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
        rr = (r + 0.001) ** 2
        for i in range(max(0, i0), min(self.nx, i1 + 1)):
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                gx, gy = self.xy(i, j)
                if (gx - x) ** 2 + (gy - y) ** 2 <= rr:
                    cur = self.occ[i][j]
                    if cur == 0 or cur == code:
                        self.occ[i][j] = code
                    else:
                        self.occ[i][j] = -1

    def stamp_seg(self, x1, y1, x2, y2, r, code):
        dist = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(dist / (self.pitch * 0.45)))
        for k in range(n + 1):
            t = k / n
            self.stamp(x1 + t * (x2 - x1), y1 + t * (y2 - y1), r, code)

    def stamp_box(self, x1, y1, x2, y2, code=-1):
        i0, j0 = self.ij(min(x1, x2), min(y1, y2))
        i1, j1 = self.ij(max(x1, x2), max(y1, y2))
        for i in range(max(0, i0), min(self.nx, i1 + 1)):
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                self.occ[i][j] = code

    def blocked(self, i, j, net):
        if not self.inb(i, j):
            return True
        v = self.occ[i][j]
        return v != 0 and v != net

    def astar(self, start, goal, net, limit=80000):
        si, sj = self.ij(*start)
        gi, gj = self.ij(*goal)

        def snap(i, j):
            if self.inb(i, j) and not self.blocked(i, j, net):
                return i, j
            for rad in range(1, 12):
                for di in range(-rad, rad + 1):
                    for dj in (-rad, rad) if abs(di) != rad else range(-rad, rad + 1):
                        ii, jj = i + di, j + dj
                        if self.inb(ii, jj) and not self.blocked(ii, jj, net):
                            return ii, jj
                    if abs(di) == rad:
                        continue
                    for dj in (-rad, rad):
                        ii, jj = i + di, j + dj
                        if self.inb(ii, jj) and not self.blocked(ii, jj, net):
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
        came, gs, seen = {}, {(si, sj): 0}, set()
        steps = 0
        while openh:
            steps += 1
            if steps > limit:
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
                if self.blocked(ni, nj, net):
                    continue
                ng = cost + 1
                if ng < gs.get((ni, nj), 1e18):
                    gs[(ni, nj)] = ng
                    came[(ni, nj)] = (i, j)
                    heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj))
        return None


def manhattan_pts(path):
    if not path:
        return []
    pts = [path[0]]
    for x, y in path[1:]:
        px, py = pts[-1]
        if abs(x - px) > 0.02 and abs(y - py) > 0.02:
            pts.append((x, py))
        if abs(x - pts[-1][0]) > 0.02 or abs(y - pts[-1][1]) > 0.02:
            pts.append((x, y))
    return pts


def oblong_u1(fp):
    n = 0
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in RF_PADS or num == "103" or (num.isdigit() and int(num) >= 104):
            continue
        rel = pad.GetFPRelativePosition()
        x, y = mm(rel.x), mm(rel.y)
        west, east = abs(x + 7.75) < 0.06, abs(x - 7.75) < 0.06
        south, north = abs(y + 5.0) < 0.06, abs(y - 5.0) < 0.06
        if not (west or east or south or north):
            continue
        # one-axis oblong only (corners: pick the edge with larger |coord|)
        if (west or east) and (south or north):
            if abs(x) >= abs(y) - 0.01:
                south = north = False
            else:
                west = east = False
        nx, ny, sx, sy = x, y, 0.3, 0.3
        if west:
            nx, sx, sy = x - 0.25, 0.80, 0.30
        elif east:
            nx, sx, sy = x + 0.25, 0.80, 0.30
        elif south:
            ny, sx, sy = y - 0.25, 0.30, 0.80
        elif north:
            ny, sx, sy = y + 0.25, 0.30, 0.80
        pad.SetFPRelativePosition(vec(nx, ny))
        pad.SetSize(pcbnew.VECTOR2I(nm(sx), nm(sy)))
        pad.SetRoundRectRadiusRatio(0.12)
        n += 1
    return n


def rect_ring(cx, cy, hw, hh, step):
    left, right = cx - hw, cx + hw
    top, bot = cy - hh, cy + hh
    pts = []
    x, y = left, top
    segs = ((right - left, 0), (0, bot - top), (left - right, 0), (0, top - bot))
    for dx, dy in segs:
        dist = math.hypot(dx, dy)
        n = max(1, int(round(dist / step)))
        for k in range(n):
            pts.append((x + dx * k / n, y + dy * k / n))
        x += dx
        y += dy
    return pts


def in_rf(x, y):
    return x < 24.0 and 18.0 < y < 66.0


def pad_hits(pads, x, y, net, clearance=0.28):
    for p in pads:
        if p["name"] == net:
            continue
        if (p["x"] - x) ** 2 + (p["y"] - y) ** 2 < (p["r"] + clearance) ** 2:
            return True
    return False


def seg_hits(pads, x1, y1, x2, y2, net, clearance=0.28):
    dist = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(dist / 0.15))
    for k in range(n + 1):
        t = k / n
        if pad_hits(pads, x1 + t * (x2 - x1), y1 + t * (y2 - y1), net, clearance):
            return True
    return False


def main():
    board = pcbnew.LoadBoard(BOARD)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = nm(0.10)
    ds.m_TrackMinWidth = nm(0.10)
    ds.m_ViasMinSize = nm(0.45)
    ds.m_MinThroughDrill = nm(0.25)

    fp = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    print("oblong", oblong_u1(fp))

    bbox = board.GetBoardEdgesBoundingBox()
    w, h = mm(bbox.GetWidth()), mm(bbox.GetHeight())

    padinfo = []
    by_net = defaultdict(list)
    for pad in board.GetPads():
        name = pad.GetNetname()
        if not name:
            continue
        pos = pad.GetPosition()
        x, y = mm(pos.x), mm(pos.y)
        size = pad.GetSize()
        parent = pad.GetParentFootprint()
        rec = {
            "x": x,
            "y": y,
            "code": pad.GetNetCode(),
            "pth": is_pth(pad),
            "ref": parent.GetReference() if parent else "",
            "num": pad.GetNumber(),
            "name": name,
            "r": max(mm(size.x), mm(size.y)) / 2,
            "pad": pad,
        }
        padinfo.append(rec)
        by_net[name].append(rec)

    gF = Grid(w, h, 0.20)
    gB = Grid(w, h, GRID)
    for G in (gF, gB):
        G.stamp_box(0, 0, w, EDGE, -1)
        G.stamp_box(0, h - EDGE, w, h, -1)
        G.stamp_box(0, 0, EDGE, h, -1)
        G.stamp_box(w - EDGE, 0, w, h, -1)
    # RF keepout on B.Cu for digital (F.Cu RF already routed)
    gB.stamp_box(0, 18, 23.5, 66, -1)

    for p in padinfo:
        gF.stamp(p["x"], p["y"], p["r"] + 0.05, p["code"])
        if p["pth"]:
            gB.stamp(p["x"], p["y"], min(0.85, p["r"] + 0.05), p["code"])

    for tr in board.GetTracks():
        code = tr.GetNetCode()
        if isinstance(tr, pcbnew.PCB_VIA):
            pt = tr.GetPosition()
            gF.stamp(mm(pt.x), mm(pt.y), 0.40, code)
            gB.stamp(mm(pt.x), mm(pt.y), 0.40, code)
        else:
            s, e = tr.GetStart(), tr.GetEnd()
            r = mm(tr.GetWidth()) / 2 + 0.10
            if tr.GetLayer() == pcbnew.F_Cu:
                gF.stamp_seg(mm(s.x), mm(s.y), mm(e.x), mm(e.y), r, code)
            elif tr.GetLayer() == pcbnew.B_Cu:
                gB.stamp_seg(mm(s.x), mm(s.y), mm(e.x), mm(e.y), r, code)

    # J3 LTE SWF tap around J2, 50 ohm on F.Cu
    j3 = next(p for p in by_net["ANT_FIT"] if p["ref"] == "J3")
    # join existing ANT_FIT at (12, 28)
    tap = [(j3["x"], j3["y"]), (11.6, j3["y"]), (11.6, 28.0), (12.0, 28.0)]
    code_ant = j3["code"]
    ok_tap = True
    for a, b in zip(tap, tap[1:]):
        if seg_hits(padinfo, a[0], a[1], b[0], b[1], "ANT_FIT", 0.22):
            ok_tap = False
    if ok_tap:
        for a, b in zip(tap, tap[1:]):
            add_track(board, a[0], a[1], b[0], b[1], pcbnew.F_Cu, RF_W, code_ant)
            gF.stamp_seg(a[0], a[1], b[0], b[1], RF_W / 2 + 0.10, code_ant)
        print("J3 SWF tap routed")
    else:
        print("J3 tap blocked; left for manual")

    # Via slots: two rings, skip RF west
    slots = []
    for hw, hh, step in ((10.4, 7.6, 0.95), (12.0, 9.0, 1.05)):
        for x, y in rect_ring(U1C[0], U1C[1], hw, hh, step):
            if in_rf(x, y) or x < 25.2:
                continue
            if EDGE + 1 < x < w - EDGE - 1 and EDGE + 1 < y < h - EDGE - 1:
                slots.append((x, y))
    used = set()

    def take_slot(px, py, code):
        best = None
        for i, (sx, sy) in enumerate(slots):
            if i in used:
                continue
            ii, jj = gB.ij(sx, sy)
            if gB.blocked(ii, jj, code) or gF.blocked(*gF.ij(sx, sy), code):
                continue
            d = (sx - px) ** 2 + (sy - py) ** 2
            if best is None or d < best[0]:
                best = (d, i, sx, sy)
        if not best:
            return None
        used.add(best[1])
        return best[2], best[3]

    def fcu_manhattan(x1, y1, x2, y2, net, width, code):
        via_h = (x2, y1)
        via_v = (x1, y2)
        for mid in (via_h, via_v):
            if not seg_hits(padinfo, x1, y1, mid[0], mid[1], net) and not seg_hits(
                padinfo, mid[0], mid[1], x2, y2, net
            ):
                add_track(board, x1, y1, mid[0], mid[1], pcbnew.F_Cu, width, code)
                add_track(board, mid[0], mid[1], x2, y2, pcbnew.F_Cu, width, code)
                gF.stamp_seg(x1, y1, mid[0], mid[1], width / 2 + 0.08, code)
                gF.stamp_seg(mid[0], mid[1], x2, y2, width / 2 + 0.08, code)
                return True
        return False

    routed = failed = 0
    plane_vias = 0

    # VDD_nRF: via to In2 plane
    for p in by_net.get("VDD_nRF", []):
        if p["pth"]:
            continue
        site = take_slot(p["x"], p["y"], p["code"]) if p["ref"] == "U1" else (p["x"] + 0.0, p["y"] + 1.15)
        if p["ref"] != "U1":
            # try south then north of pad
            for cand in ((p["x"], p["y"] + 1.2), (p["x"], p["y"] - 1.2), (p["x"] + 1.2, p["y"]), (p["x"] - 1.2, p["y"])):
                if in_rf(*cand):
                    continue
                ii, jj = gB.ij(*cand)
                if not gB.blocked(ii, jj, p["code"]) and not pad_hits(padinfo, cand[0], cand[1], "VDD_nRF", 0.35):
                    site = cand
                    break
        if not site:
            continue
        if fcu_manhattan(p["x"], p["y"], site[0], site[1], "VDD_nRF", PWR_W, p["code"]):
            add_via(board, site[0], site[1], p["code"], size=0.7, drill=0.35)
            gF.stamp(site[0], site[1], 0.45, p["code"])
            gB.stamp(site[0], site[1], 0.45, p["code"])
            plane_vias += 1
    print("VDD_nRF plane vias", plane_vias)

    for name, pads in sorted(by_net.items()):
        if name in SKIP_NETS or name in PLANE_NETS:
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

        # 1) short F.Cu links for nearby pads
        parent = {id(p): p for p in uniq}
        # union-find
        parent_uf = {i: i for i in range(len(uniq))}

        def find(i):
            while parent_uf[i] != i:
                parent_uf[i] = parent_uf[parent_uf[i]]
                i = parent_uf[i]
            return i

        def union(i, j):
            ri, rj = find(i), find(j)
            if ri != rj:
                parent_uf[rj] = ri

        for i, a in enumerate(uniq):
            for j, b in enumerate(uniq):
                if j <= i:
                    continue
                if find(i) == find(j):
                    continue
                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if d < 5.5 and d > 0.2:
                    if fcu_manhattan(a["x"], a["y"], b["x"], b["y"], name, width, code):
                        union(i, j)
                        routed += 1

        # 2) fanout remaining SMD to vias
        nodes = []  # (x,y) copper nodes on B.Cu or PTH
        for i, p in enumerate(uniq):
            if p["pth"]:
                nodes.append((p["x"], p["y"], find(i)))
                continue
            # already F.Cu-connected cluster may still need a via to reach PTH
            need_via = True
            # if this SMD cluster already includes a PTH, skip extra via for this pad
            cluster = find(i)
            has_pth = any(uniq[k]["pth"] and find(k) == cluster for k in range(len(uniq)))
            if has_pth:
                continue
            site = None
            if p["ref"] == "U1":
                site = take_slot(p["x"], p["y"], code)
            else:
                for cand in (
                    (p["x"], p["y"] + 1.25),
                    (p["x"], p["y"] - 1.25),
                    (p["x"] + 1.25, p["y"]),
                    (p["x"] - 1.25, p["y"]),
                    (p["x"] + 1.25, p["y"] + 1.25),
                ):
                    if not (EDGE + 1 < cand[0] < w - EDGE - 1 and EDGE + 1 < cand[1] < h - EDGE - 1):
                        continue
                    if in_rf(*cand) and name not in RF_NETS:
                        continue
                    ii, jj = gB.ij(*cand)
                    if gB.blocked(ii, jj, code):
                        continue
                    if pad_hits(padinfo, cand[0], cand[1], name, 0.38):
                        continue
                    site = cand
                    break
            if not site:
                failed += 1
                print(f"NOVIA {name} {p['ref']}.{p['num']} @{p['x']:.1f},{p['y']:.1f}")
                continue
            if not fcu_manhattan(p["x"], p["y"], site[0], site[1], name, width, code):
                # force two-segment anyway if the via is close
                add_track(board, p["x"], p["y"], site[0], p["y"], pcbnew.F_Cu, width, code)
                add_track(board, site[0], p["y"], site[0], site[1], pcbnew.F_Cu, width, code)
                gF.stamp_seg(p["x"], p["y"], site[0], p["y"], width / 2 + 0.08, code)
                gF.stamp_seg(site[0], p["y"], site[0], site[1], width / 2 + 0.08, code)
            add_via(board, site[0], site[1], code)
            gF.stamp(site[0], site[1], 0.38, code)
            gB.stamp(site[0], site[1], 0.38, code)
            nodes.append((site[0], site[1], cluster))

        # add PTH nodes
        for i, p in enumerate(uniq):
            if p["pth"]:
                nodes.append((p["x"], p["y"], find(i)))

        # unique node positions
        n2 = []
        seen_n = set()
        for x, y, c in nodes:
            k = (round(x, 2), round(y, 2))
            if k in seen_n:
                continue
            seen_n.add(k)
            n2.append((x, y, c))
        nodes = n2
        if len(nodes) < 2:
            continue

        # 3) B.Cu A* connect clusters
        connected = [nodes[0]]
        remaining = nodes[1:]
        while remaining:
            best = None
            for ci, c in enumerate(connected):
                for ri, r in enumerate(remaining):
                    d = abs(c[0] - r[0]) + abs(c[1] - r[1])
                    if best is None or d < best[0]:
                        best = (d, ci, ri, c, r)
            _, _, ri, src, dst = best
            path = gB.astar((src[0], src[1]), (dst[0], dst[1]), code)
            if not path:
                failed += 1
                print(f"FAIL {name} {dst[0]:.1f},{dst[1]:.1f}")
                remaining.pop(ri)
                continue
            pts = manhattan_pts(path)
            for a, b in zip(pts, pts[1:]):
                add_track(board, a[0], a[1], b[0], b[1], pcbnew.B_Cu, width, code)
                gB.stamp_seg(a[0], a[1], b[0], b[1], width / 2 + 0.10, code)
            connected.append(dst)
            remaining.pop(ri)
            routed += 1

    print(f"route ok={routed} fail={failed}")

    # GND stitch, occupancy-aware
    gnd = board.FindNet("GND")
    gnd_code = gnd.GetNetCode()
    stitch = 0
    sites = [(float(x), float(y)) for x in range(5, 116, 5) for y in range(5, 76, 5)]
    sites += [(float(x), float(y)) for x in range(4, 23, 2) for y in (22, 26, 30, 34, 38, 46, 50, 54, 58, 62)]
    for x, y in sites:
        if 27.5 < x < 44.5 and 25.0 < y < 39.0:
            continue
        i, j = gB.ij(x, y)
        fi, fj = gF.ij(x, y)
        if gB.blocked(i, j, gnd_code) or gF.blocked(fi, fj, gnd_code):
            continue
        if pad_hits(padinfo, x, y, "GND", 0.45):
            continue
        add_via(board, x, y, gnd_code, size=0.6, drill=0.3)
        gB.stamp(x, y, 0.40, gnd_code)
        gF.stamp(x, y, 0.40, gnd_code)
        stitch += 1
    print("gnd stitch", stitch)

    print("zone fill")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print("saved", BOARD)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
