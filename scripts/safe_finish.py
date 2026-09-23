#!/usr/bin/env python3
"""Safe finish: oblong outer LGA pads, silkscreen, GND stitch, zone fill. No autoroute."""
import math
import pcbnew

BOARD = "/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
RF_PADS = {"61", "64", "67"}


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


def occupied(board, x, y):
    for pad in board.GetPads():
        p = pad.GetPosition()
        dx, dy = mm(p.x) - x, mm(p.y) - y
        size = pad.GetSize()
        r = max(mm(size.x), mm(size.y)) / 2 + 0.45
        if dx * dx + dy * dy < r * r:
            return True
    for tr in board.GetTracks():
        if isinstance(tr, pcbnew.PCB_VIA):
            p = tr.GetPosition()
            if (mm(p.x) - x) ** 2 + (mm(p.y) - y) ** 2 < 0.55 ** 2:
                return True
        else:
            s, e = tr.GetStart(), tr.GetEnd()
            x1, y1, x2, y2 = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
            vx, vy = x2 - x1, y2 - y1
            l2 = vx * vx + vy * vy
            if l2 < 1e-9:
                continue
            t = max(0.0, min(1.0, ((x - x1) * vx + (y - y1) * vy) / l2))
            px, py = x1 + t * vx, y1 + t * vy
            w = mm(tr.GetWidth()) / 2 + 0.35
            if (px - x) ** 2 + (py - y) ** 2 < w * w:
                return True
    return False


def oblong_u1(fp):
    n = 0
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in RF_PADS or num == "103" or (num.isdigit() and int(num) >= 104):
            continue
        rel = pad.GetFPRelativePosition()
        x, y = mm(rel.x), mm(rel.y)
        west, east = abs(x + 7.75) < 0.05, abs(x - 7.75) < 0.05
        south, north = abs(y + 5.0) < 0.05, abs(y - 5.0) < 0.05
        if not (west or east or south or north):
            continue
        nx, ny, sx, sy = x, y, 0.3, 0.3
        if west:
            nx, sx, sy = x - 0.25, 0.8, 0.3
        elif east:
            nx, sx, sy = x + 0.25, 0.8, 0.3
        if south:
            ny = y - 0.25
            if west or east:
                sx, sy = 0.8, 0.8
            else:
                sx, sy = 0.3, 0.8
        elif north:
            ny = y + 0.25
            if west or east:
                sx, sy = 0.8, 0.8
            else:
                sx, sy = 0.3, 0.8
        pad.SetFPRelativePosition(vec(nx, ny))
        pad.SetSize(pcbnew.VECTOR2I(nm(sx), nm(sy)))
        pad.SetRoundRectRadiusRatio(0.15)
        n += 1
    return n


def main():
    board = pcbnew.LoadBoard(BOARD)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = nm(0.10)
    ds.m_TrackMinWidth = nm(0.10)
    ds.m_ViasMinSize = nm(0.45)
    ds.m_MinThroughDrill = nm(0.25)

    fp = next(f for f in board.GetFootprints() if f.GetReference() == "U1")
    print("U1 present", fp.GetReference(), "skip oblong on board (existing F.Cu fanouts)")

    print("gnd stitch skipped (existing F.Cu routes)")

    for fpp in board.GetFootprints():
        fpp.Value().SetVisible(False)
        ref = fpp.GetReference()
        if not ref.startswith("J"):
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
        ("RF: 0.20mm microstrip over L2 GND. Do not route digital under matching.", 62, 50.5, 0.6, False, 0),
    ]
    for text, x, y, sz, bold, ang in extras:
        add_text(board, text, x, y, size=sz, angle=ang, bold=bold)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    print("saved")


if __name__ == "__main__":
    main()
