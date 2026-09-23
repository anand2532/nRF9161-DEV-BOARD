#!/usr/bin/env python3
"""Pass30k — Class F attack (VIN_F → SWDCLK → nRESET → P0.02).

Applied on live board (see reports/PASS30K_SUMMARY.json):
  VIN_F CLOSED:
    B (49.30,12.60)->(49.30,11.00)->(69.20,11.00)
    via F-hop over VDD_GPIO V@x70: (69.20,11)->(70.80,11)
    B (70.80,11)->(70.80,16.2)->(71.575,16.2)->(71.575,19.062) w=0.30
  Rip+restore same transaction:
    P0.15 east H@y15.35: F-bridge vias@(69.3,15.35)/(72.0,15.35)
  VDD_GPIO left intact (F-hop over it).

  SWDCLK: probed B west column after VDD_GPIO H@19.13 rip — V@x48.05 restore
    blocked by J8.3 GND @(48.05,4.73). Left untouched (no thrash).
  nRESET: H corridors congested (VIN_FILT/VDD2/P0.15/VIN_F/ENABLE); one probe,
    left untouched.
  P0.02 / COEX0: not attempted — STOP after two Class-F restore failures.

Result: unconnected 76→75, shorting=0 clearance=0 crossing=0.
  Closed: VIN_F. Stage A + pass30i/30j kept. P0.15 west wrap 21 segs.
  No placement. No Gerbers.

Do not --apply unless intentionally replaying; prefer session/summary.
"""
from __future__ import annotations
import sys
print(__doc__)
if "--apply" in sys.argv:
    print("Refusing blind --apply; replay from PASS30K_SUMMARY / agent session only.")
    sys.exit(1)
