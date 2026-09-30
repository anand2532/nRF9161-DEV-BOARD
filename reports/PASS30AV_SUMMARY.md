# PASS30AV_SUMMARY — P0.14

**Timestamp:** 2026-09-30 12:06 IST
**KiCad:** 9.0.2
**Decision:** **REVERT**
**Net:** P0.14
**Via:** (42.25, 25.50), 0.50 mm pad, 0.30 mm drill. Placed, refilled, then removed on revert.
**Refill cleared the via:** True (B.Cu pad-edge to GND fill 0.2505 mm, center inside fill False)
**F.Cu stub:** (42.25, 26.40) → (42.25, 25.50), 0.18 mm, one segment, not in the B.Cu budget. Reverted with the via.
**B.Cu segments:** 0 (limit 8). No second via.
**Min foreign clearance (via + stub, after refill, including the pulled-back zone):** 0.16 mm vs {'net': 'P0.15', 'item': 'F P0.15 (41.75,26.75)-(41.75,23.10)'}
**Min POWER clearance:** 0.702 mm vs {'net': 'VDD2', 'item': 'F VDD2 (43.25,25.90)-(44.72,25.90)'}
**New via hole-to-hole:** 1.3286 mm vs viahole P0.13 @(42.750,23.950)
**P0.14 opens:** 1 → 1 (mid 1)
**Unconnected:** 60 → 60 (mid 60)
**GND islands:** 12 → 12 (waived; mid 12)

## Why no B.Cu route

The via sits between the parallel F.Cu tracks (P0.15 at x=41.75, P0.13 at x=42.75). A 0.50 mm pad at x=42.25 clears each track by 0.16 mm. y=25.50 keeps the pad north of the SiP body (pad south edge y=25.75, body starts y=26.75) and south of the P0.13/P0.15 vias at y=23.1 / 23.95.

B.Cu GND there is zone fill. Refill was run so the pour could pull back. That does not open a path to J18.2. A 0.2 mm flood of B.Cu track centers that clear foreign copper by 0.15 mm, POWER by 0.20 mm, and holes by 0.25 mm, stay at copper x>24.2, and stay outside the SiP body, has bbox x 29.0–46.2, y 16.0–26.6 (1645 cells). It does not reach J18.2. The south side is the body plus the VDD2 trunk at y=26.75; the west side stops at the VDD_GPIO / COEX0 wall near x=29; the east side stops at x=46.2. Leaving that component crosses foreign copper or the body. No 8-segment polyline exists, and no longer polyline exists either. Zero B.Cu segments were added. The sealed pocket y≈44.60, x≈81.8–97.3 was not used. Locked trunks were not ripped. P0.13 and P0.15 vias were not moved. The F.Cu pinch between those vias was not retried. U1.88 and U1.89 were not retried. P0.24 was not started.

## Gate

REVERT. P0.14 opens 1→1 (need a drop of at least 1). B.Cu segments added: 0. Free-space component reaches J18: False. Refill cleared via: True. Foreign 0.16 mm, POWER 0.702 mm. Mid short/clearance/crossing/hole 0/0/0/0, hole_to_hole 1→1. Other nets gained: none. Full restore. No second path. No F.Cu pinch retry.

## DRC

| | unconnected | P0.14 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 60 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| mid (via+stub, before revert) | 60 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after restore | 60 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
