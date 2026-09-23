#!/usr/bin/env python3
"""Probe P0.15 east-hop candidates without committing copper."""
from __future__ import annotations

import sys

import pcbnew

sys.path.insert(0, "/workspace/kicad-projects/nRF9161-DEV-BOARD/scripts")
from complete_route import hypot  # noqa: E402
from final_connect import BOARD, Final  # noqa: E402
from final_pass7 import why  # noqa: E402
from final_pass14 import waypoint_route  # noqa: E402

B = pcbnew.B_Cu
W = 0.18
NAME = "P0.15"


def path_ok(r, pts):
    for a, b in zip(pts, pts[1:]):
        if not r.track_clear(a[0], a[1], b[0], b[1], B, W, NAME):
            return why(r, [a, b], B, W, NAME)
    return None


def main():
    board = pcbnew.LoadBoard(BOARD)
    r = Final(board)
    r.collect()
    cands = []
    # North of ENABLE y=20.3, east of nRESET x=42.75
    cands.append(
        (
            "north jog 19.50",
            [
                (41.75, 20.60),
                (43.30, 20.60),
                (43.30, 19.50),
                (45.10, 19.50),
                (45.10, 18.90),
                (46.30, 18.90),
                (46.30, 19.50),
                (106.00, 19.50),
                (106.00, 20.60),
            ],
        )
    )
    cands.append(
        (
            "north 19.20 via 43.4",
            [
                (41.75, 20.60),
                (43.40, 20.60),
                (43.40, 19.20),
                (106.00, 19.20),
                (106.00, 20.60),
            ],
        )
    )
    cands.append(
        (
            "north 18.60",
            [
                (41.75, 20.60),
                (43.40, 20.60),
                (43.40, 18.60),
                (45.10, 18.60),
                (45.10, 17.80),
                (46.40, 17.80),
                (46.40, 18.60),
                (106.00, 18.60),
                (106.00, 20.60),
            ],
        )
    )
    cands.append(
        (
            "y=19.00 skip nRESET then east",
            [
                (41.75, 20.60),
                (43.50, 20.60),
                (43.50, 19.00),
                (106.00, 19.00),
                (106.00, 20.60),
            ],
        )
    )
    for y in (15.40, 15.80, 16.40, 17.00, 17.60, 18.20, 18.80, 19.10, 19.40, 19.70):
        cands.append(
            (
                f"gate43.5 y={y:.2f}",
                [
                    (41.75, 20.60),
                    (43.50, 20.60),
                    (43.50, y),
                    (106.00, y),
                    (106.00, 20.60),
                ],
            )
        )
    # South-east of via, north of U1 courtyard
    for y in (23.80, 24.20, 24.60, 24.90):
        cands.append(
            (
                f"south-east y={y:.2f} to 106",
                [
                    (41.75, 23.10),
                    (41.75, y),
                    (106.00, y),
                    (106.00, 20.60),
                ],
            )
        )
        cands.append(
            (
                f"SE col49 y={y:.2f}",
                [
                    (41.75, 23.10),
                    (41.75, y),
                    (49.20, y),
                    (49.20, 45.00),
                    (49.20, 58.80),
                    (43.08, 58.80),
                    (43.08, 62.00),
                ],
            )
        )
    # Far north y=6-8
    cands.append(
        (
            "far north y=6.80",
            [
                (41.75, 20.60),
                (43.50, 20.60),
                (43.50, 6.80),
                (106.00, 6.80),
                (106.00, 20.60),
            ],
        )
    )
    cands.append(
        (
            "y=11.40 east of VDD_GPIO",
            [
                (41.75, 20.60),
                (43.50, 20.60),
                (43.50, 11.40),
                (47.40, 11.40),
                (47.40, 16.20),
                (49.20, 16.20),
                (49.20, 11.40),
                (106.00, 11.40),
                (106.00, 20.60),
            ],
        )
    )

    any_ok = False
    for label, pts in cands:
        err = path_ok(r, pts)
        if err is None:
            print(f"CLEAR {label}")
            any_ok = True
        else:
            print(f"BLOCK {label}: {err}")

    print("\n==== dense waypoint (41.75,20.60)->(106,20.60) ====")
    xs = [round(x, 2) for x in [41.75, 43.3, 43.5, 44.5, 45.1, 46.3, 47.4, 48.2, 49.2, 50.2, 51.0, 52.5, 54.0, 56.0, 58.0, 62.0, 70.0, 80.0, 90.0, 100.0, 106.0]]
    ys = [round(y, 2) for y in [6.4, 6.8, 8.0, 9.2, 10.4, 11.4, 12.6, 13.8, 15.0, 16.2, 17.0, 17.8, 18.2, 18.6, 18.9, 19.1, 19.3, 19.5, 19.7, 20.0, 20.3, 20.6, 21.0, 21.5, 22.0, 22.5, 23.1, 23.8, 24.4]]
    pts, L = waypoint_route(r, 41.75, 20.60, 106.00, 20.60, B, W, NAME, xs=xs, ys=ys)
    if pts is None:
        print("waypoint FAIL")
    else:
        print(f"waypoint L={L:.1f} n={len(pts)}")
        err = path_ok(r, pts)
        print("  verify", "CLEAR" if err is None else err)
        for p in pts:
            print(f"    {p[0]:.2f},{p[1]:.2f}")

    print("\n==== waypoint via to 106 ====")
    pts, L = waypoint_route(r, 41.75, 23.10, 106.00, 20.60, B, W, NAME, xs=xs, ys=ys)
    if pts is None:
        print("waypoint via FAIL")
    else:
        print(f"waypoint via L={L:.1f} n={len(pts)} { 'CLEAR' if path_ok(r, pts) is None else path_ok(r, pts)}")
        for p in pts[:30]:
            print(f"    {p[0]:.2f},{p[1]:.2f}")

    print("done any_explicit_clear", any_ok)


if __name__ == "__main__":
    main()
