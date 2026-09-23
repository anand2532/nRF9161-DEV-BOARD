#!/usr/bin/env python3
"""After SES import: GND stitch, silkscreen, zone fill."""
import math
import sys
import pcbnew

BOARD_PATH = "/home/anand/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"


def nm(x):
    return int(pcbnew.FromMM(float(x)))


def mm(v):
    return pcbnew.ToMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


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


def occupied(board, x, y, r=0.45):
    pt = vec(x, y)
    for pad in board.GetPads():
        p = pad.GetPosition()
        dx = mm(p.x) - x
        dy = mm(p.y) - y
        size = pad.GetSize()
        pr = max(mm(size.x), mm(size.y)) / 2 + r
        if dx * dx + dy * dy < pr * pr:
            return True
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            p = tr.GetPosition()
            dx = mm(p.x) - x
            dy = mm(p.y) - y
            if dx * dx + dy * dy < (0.6) ** 2:
                return True
        else:
            s, e = tr.GetStart(), tr.GetEnd()
            x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
            # point-segment distance
            vx, vy = x2 - x1, y2 - y1
            l2 = vx * vx + vy * vy
            if l2 < 1e-9:
                continue
            t = max(0.0, min(1.0, ((x - x1) * vx + (y - y1) * vy) / l2))
            px, py = x1 + t * vx, y1 + t * vy
            w = mm(tr.GetWidth()) / 2 + 0.25
            if (px - x) ** 2 + (py - y) ** 2 < w * w:
                return True
    return False


def main():
    board = pcbnew.LoadBoard(BOARD_PATH)
    gnd = board.FindNet("GND")
    gnd_code = gnd.GetNetCode() if gnd else 0
    stitch = 0
    sites = []
    for x in range(3, 118, 5):
        for y in range(3, 78, 5):
            sites.append((float(x), float(y)))
    for x in [4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
        for y in [24, 28, 32, 36, 40, 44, 48, 52, 56, 60]:
            sites.append((float(x), float(y)))
    for x in [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46]:
        for y in [23, 25, 40, 42]:
            sites.append((float(x), float(y)))
    seen = set()
    for x, y in sites:
        key = (round(x, 1), round(y, 1))
        if key in seen:
            continue
        seen.add(key)
        if 28.2 < x < 43.8 and 25.5 < y < 38.5:
            continue
        if occupied(board, x, y):
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(vec(x, y))
        v.SetWidth(nm(0.6))
        v.SetDrill(nm(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(gnd_code)
        board.Add(v)
        stitch += 1
    print("GND stitch", stitch)

    for fp in board.GetFootprints():
        fp.Value().SetVisible(False)
        ref = fp.GetReference()
        if not ref.startswith("J"):
            continue
        for pad in fp.Pads():
            n = pad.GetNetname() or ""
            if not n:
                continue
            label = n
            if n == "VDD_GPIO":
                label = "3V3"
            p = pad.GetPosition()
            px, py = mm(p.x), mm(p.y)
            fppos = fp.GetPosition()
            fx, fy = mm(fppos.x), mm(fppos.y)
            ox, oy, ang = 0.0, -1.8, 0
            if fx > 100:
                ox, oy, ang = -2.4, 0.0, 90
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

    print("filling zones")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(BOARD_PATH, board)
    print("saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
