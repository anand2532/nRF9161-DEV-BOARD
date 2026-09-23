#!/usr/bin/env python3
"""Pass30i — atomic P0.08 + ENABLE/COEX2 co-route (Stage A kept; no placement).

Applied on live board (see reports/PASS30I_SUMMARY.json):
  Rip (B.Cu):
    ENABLE V (62.5,25.2)-(62.5,40.95)
    ENABLE V (76.8,36)-(76.8,28)
    ENABLE H (76.8,28)-(90.38,28)
    COEX2  V (72,38)-(72,24.6)
  P0.08 B@y30.25:
    (46.2,30)-(46.2,30.25)-(78.5,30.25)-(78.5,26)-(79.67,26) w=0.18
  Restores (via-bridges — B U-jogs cannot cross P0.08 H):
    ENABLE @x=62.5: B→via(62.5,29.6)→F→via(62.5,30.9)→B to (62.5,40.95)
    COEX2  @x=72:   B→via(72,30.9)→F→via(72,29.6)→B to (72,24.6)
    ENABLE east:    B (76.8,36)-(76.8,30.9)→via→F→via(79.2,30.9)→B (79.2,28)-(90.38,28)

Result: unconnected 78→77, shorting=0 clearance=0 crossing=0.
  Closed: P0.08 U1↔SW3/R14 island. Remaining: P0.08 ↔ J12.9.
  P0.15 west wrap preserved (21 segs). Stage A VDD2/VDD_nRF untouched.

Do not --apply unless intentionally replaying; prefer session/summary.
"""
from __future__ import annotations
import sys
print(__doc__)
if "--apply" in sys.argv:
    print("Refusing blind --apply; replay from PASS30I_SUMMARY / agent session only.")
    sys.exit(1)
