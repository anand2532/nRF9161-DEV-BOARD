#!/usr/bin/env python3
"""Close remaining unconnected islands on the CURRENT board. Do not restore RF backup."""
from __future__ import annotations

import json
import subprocess
import sys

import pcbnew

sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import (  # noqa: E402
    BOARD,
    RF_NETS,
    SKIP,
    Router,
    hypot,
    net_width,
    use_bcu,
)

DRC_JSON = "/tmp/nrf_close_drc.json"


def skip_pad(p):
    if p["npth"]:
        return False
    if not p["num"] and not p["pth"]:
        return True
    return False


class Closer(Router):
    def collect(self):
        super().collect()
        self.pads = [p for p in self.pads if not skip_pad(p)]
        self.by_net = {}
        from collections import defaultdict

        bn = defaultdict(list)
        for p in self.pads:
            if p["name"]:
                bn[p["name"]].append(p)
        self.by_net = bn

    def track_clear(self, x1, y1, x2, y2, layer, width, name):
        # ignore unnumbered ghost pads
        saved = self.pads
        self.pads = [p for p in saved if p["num"] or p["pth"] or p["npth"]]
        try:
            return super().track_clear(x1, y1, x2, y2, layer, width, name)
        finally:
            self.pads = saved


def parse_unconnected(path):
    data = json.load(open(path))
    shorts = sum(1 for v in data.get("violations", []) if v.get("type") == "shorting_items")
    pairs = []
    for u in data.get("unconnected_items", []):
        a, b = u["items"][0], u["items"][1]
        def net(desc):
            if "[" in desc and "]" in desc:
                return desc.split("[")[1].split("]")[0]
            return ""
        n = net(a["description"]) or net(b["description"])
        if n == "GND" or n in SKIP:
            continue
        pairs.append(
            {
                "net": n,
                "a": a["description"],
                "b": b["description"],
                "ax": a["pos"]["x"],
                "ay": a["pos"]["y"],
                "bx": b["pos"]["x"],
                "by": b["pos"]["y"],
                "a_pth": "PTH" in a["description"],
                "b_pth": "PTH" in b["description"],
                "a_via": "Via" in a["description"],
                "b_via": "Via" in b["description"],
                "a_f": "F.Cu" in a["description"] or "PTH" in a["description"],
                "b_f": "F.Cu" in b["description"] or "PTH" in b["description"],
                "a_b": "B.Cu" in a["description"] or "PTH" in a["description"] or "Via" in a["description"],
                "b_b": "B.Cu" in b["description"] or "PTH" in b["description"] or "Via" in b["description"],
            }
        )
    pairs.sort(key=lambda p: hypot(p["ax"], p["ay"], p["bx"], p["by"]))
    return pairs, len(data.get("unconnected_items", [])), shorts


def run_drc():
    subprocess.check_call(
        [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--output",
            DRC_JSON,
            BOARD,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return parse_unconnected(DRC_JSON)


def nearest_via(r: Closer, name, x, y):
    vias = [v for v in r.vias if v["n"] == name]
    if not vias:
        return None
    return min(vias, key=lambda v: hypot(v["x"], v["y"], x, y))


def ensure_u1_via(r: Closer, name):
    pads = [p for p in r.pads if p["ref"] == "U1" and p["name"] == name]
    if not pads:
        return None
    p = pads[0]
    near = [v for v in r.vias if v["n"] == name and hypot(v["x"], v["y"], p["x"], p["y"]) < 6.5]
    if near:
        return min(near, key=lambda v: hypot(v["x"], v["y"], p["x"], p["y"]))
    if name in {"DEC0", "VDD1", "VDD2", "VDD_GPIO"} or name in RF_NETS:
        return None
    code = p["code"]
    width = net_width(name)
    pwr = name.startswith(("VDD", "VIN"))
    ex, ey = r.radial_end(p)
    if abs(ex - p["x"]) < 0.05 or abs(ey - p["y"]) < 0.05:
        esc = [(p["x"], p["y"]), (ex, ey)]
    elif p["sx"] > p["sy"]:
        esc = [(p["x"], p["y"]), (ex, p["y"]), (ex, ey)]
    else:
        esc = [(p["x"], p["y"]), (p["x"], ey), (ex, ey)]
    if not r.connected_to_track(p, name):
        if not r.commit(esc, pcbnew.F_Cu, width, code, name):
            if not r.route_f(p["x"], p["y"], ex, ey, name, width, code):
                return None
    site = None
    dx, dy = ex - p["x"], ey - p["y"]
    for scale in (1.0, 1.2, 1.45, 1.75, 2.1, 2.5):
        sx, sy = p["x"] + dx * scale, p["y"] + dy * scale
        if r.via_ok(sx, sy, name, pwr=pwr):
            site = (sx, sy)
            break
    if not site:
        for s in (-0.95, 0.95, -1.9, 1.9):
            cand = (ex, ey + s) if abs(dx) > abs(dy) else (ex + s, ey)
            if r.via_ok(cand[0], cand[1], name, pwr=pwr):
                site = cand
                break
    if not site:
        return None
    if abs(site[0] - ex) > 0.05 or abs(site[1] - ey) > 0.05:
        if abs(dx) > abs(dy):
            jog = [(ex, ey), (site[0], ey), (site[0], site[1])]
        else:
            jog = [(ex, ey), (ex, site[1]), (site[0], site[1])]
        r.commit(jog, pcbnew.F_Cu, width, code, name)
    r.add_via(site[0], site[1], code, name, pwr=pwr)
    r.u1_via[name] = site
    return {"x": site[0], "y": site[1], "n": name}


def close_pair(r: Closer, p):
    name = p["net"]
    if not name or name in SKIP:
        return False
    net = r.board.FindNet(name)
    if not net:
        return False
    code = net.GetNetCode()
    w = net_width(name)
    x1, y1, x2, y2 = p["ax"], p["ay"], p["bx"], p["by"]
    d = hypot(x1, y1, x2, y2)
    if d < 0.08:
        return False
    both_f = p["a_f"] and p["b_f"] and not (p["a_pth"] and p["b_pth"] and d > 8)
    if both_f and d < 22:
        if r.route_f(x1, y1, x2, y2, name, w, code):
            return True
        if name in RF_NETS:
            for pts in (
                [(x1, y1), (x2, y1), (x2, y2)],
                [(x1, y1), (x1, y2), (x2, y2)],
            ):
                if r.commit(pts, pcbnew.F_Cu, 0.20, code, name):
                    return True
    if use_bcu(name) or p["a_pth"] or p["b_pth"] or p["a_via"] or p["b_via"] or p["a_b"] or p["b_b"]:
        if y2 > 70 and y1 <= 70:
            x1, y1, x2, y2 = x2, y2, x1, y1
        via = nearest_via(r, name, x1, y1)
        if "U1" in p["a"] or "U1" in p["b"]:
            via = ensure_u1_via(r, name) or via
        if via and (p["a_pth"] or p["b_pth"]):
            hx, hy = (x1, y1) if y1 > 70 or p["a_pth"] else (x2, y2)
            if r.route_to_via(hx, hy, via["x"], via["y"], name, w, code):
                return True
        if r.route_b(x1, y1, x2, y2, name, w, code):
            return True
        if r.route_to_via(x1, y1, x2, y2, name, w, code):
            return True
        site = r.local_via(x1, y1, name)
        if site and r.route_f(x1, y1, site[0], site[1], name, w, code):
            r.add_via(site[0], site[1], code, name)
            if r.route_b(site[0], site[1], x2, y2, name, w, code):
                return True
    if r.route_f(x1, y1, x2, y2, name, w, code):
        return True
    return False


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Closer(board)
    r.collect()
    print("pads", len(r.pads), "tracks", len(r.tracks), "vias", len(r.vias))

    pairs, n0, shorts0 = run_drc()
    print("start unconnected", n0, "shorts", shorts0, "actionable", len(pairs))

    for round_i in range(8):
        ok = 0
        fail = 0
        for p in pairs:
            if close_pair(r, p):
                ok += 1
            else:
                fail += 1
        leftover = sorted({p["net"] for p in pairs})
        for name in leftover:
            r.connect_net(name)
        print(f"round {round_i+1} closed={ok} fail={fail} connect leftover={len(leftover)}")
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(BOARD, board)
        pairs, n, shorts = run_drc()
        print(f"  DRC unconnected={n} shorts={shorts}")
        if shorts:
            print("ABORT shorts created; restore pre-close-gaps backup")
            import shutil
            shutil.copy2(
                "/home/anand/kicad-projects/nRF9161-DEV-BOARD/.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-close-gaps",
                BOARD,
            )
            return 1
        if n == 0:
            break
        r = Closer(board)
        r.collect()
        if ok == 0 and round_i >= 1:
            print("no pair progress")
            break

    print(f"final ok={r.ok} fail={r.fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
