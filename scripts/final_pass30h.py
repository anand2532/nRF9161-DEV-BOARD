#!/usr/bin/env python3
"""Pass30h — one honest cycle (record of applied Stage A geometry).

Applied (live board):
  VDD2: rip B walls (52.22,26.75)-(52.22,32) and (54.5,21.2)-(54.5,32)
  Restore via-bridge @x=58:
    south stubs + feeder @y=29.55 to via@(58,29.55)
    via@(58,30.95) + B stitch (58,30.95)-(58,32) to y=32 highway
    F hop (58,29.55)-(58,30.95)
    north wall stubs (52.22|54.5,30.95)-(52.22|54.5,32)
  VDD_nRF via (69.3,30)->(69.3,31.5) north + F stitch
  GND via jog SKIPPED (shorts VDD_GPIO)

Not kept:
  P0.08 B@y30.25 (ENABLE/COEX2 restore crossings / jog clearance)
  Stage B placement set (shorting=5; C6.1@x=48.68)

See reports/PASS30H_SUMMARY.json. Do not --apply unless intentionally replaying.
"""
from __future__ import annotations
import sys
print(__doc__)
if "--apply" in sys.argv:
    print("Refusing blind --apply; replay from PASS30H_SUMMARY / agent session only.")
    sys.exit(1)
