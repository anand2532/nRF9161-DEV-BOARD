# PASS30AX_SUMMARY — P0.16

**Timestamp:** 2026-09-30 12:43 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.16
**Side of package:** east skirt on In1.Cu
**New via:** no
**New segments:** 6 (limit 8)
**Min foreign clearance:** 0.21 mm vs {'net': 'P0.06', 'item': 'via@45.150,36.000'}
**Min POWER/VIN clearance:** 0.3378 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}
**Min hole clearance (pre-add):** 0.31 mm vs via P0.06 @45.150,36.000
**P0.16 opens:** 1 → 0
**Unconnected:** 60 → 59
**GND islands:** 12 → 12 (waived)

## Remeasured gap

Pad-edge **34.259 mm** on F.Cu, U1.26 [41.25, 26.75] to J18.4 [45.62, 62.0]. Other island is J18.4 already tied on B.Cu to J13.1. The U1 island is the existing stub F.Cu (41.25, 26.75)–(40.70, 20.80) plus via (40.70, 20.80). Stub not ripped.

## Straight line (not used)

0.18 mm F.Cu chord [41.364, 27.15] → [45.537, 61.154] (34.259 mm). Crosses the SiP body. Worst hit GND -0.349 mm (via@42.000,32.000). Foreign nets under 0.15 mm: <no-net>, ENABLE, GND, P0.04, P0.15 (19 items).

## Why not F.Cu or B.Cu

Free space (0.18 mm centerline, foreign ≥ 0.15, POWER ≥ 0.20, hole ≥ 0.25, off the fab body, x > 24.2, GND pour ignored) from the existing via:

- F.Cu: {'cells': 545, 'bbox': [37.75, 47.0, 16.0, 27.0], 'reaches_j18': False}
- B.Cu: {'cells': 652, 'bbox': [32.75, 46.25, 16.0, 26.5], 'reaches_j18': False}

Neither component reaches J18.4. The start pocket ends near y≈27 and the J18 component starts south of the fanout (y≈41). One via is a point, so it cannot join two components that do not overlap. The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 was not used. No west skirt.

## Route

In1.Cu 0.18 mm, east of the body (long run x=44.60 > 44). No new via. Corners:

- (40.70, 20.80) → (45.55, 20.80)
- (45.55, 20.80) → (45.55, 27.40)
- (45.55, 27.40) → (44.60, 27.40)
- (44.60, 27.40) → (44.60, 60.40)
- (44.60, 60.40) → (45.62, 60.40)
- (45.62, 60.40) → (45.62, 61.10)

The north run is y=20.80, above the fab body. The drop at x=45.55 clears VDD2 via (44.722, 25.900). The south run at x=44.60 clears P0.06 via (45.150, 36.000) by 0.21 mm and stays east of the body (copper edge x=44.51). End cap overlaps J18.4.

## Gate

KEEP. East In1 skirt, 6 new segments, no new via. P0.16 opens 1→0. Unconnected 60→59. Foreign 0.21 mm, POWER 0.3378 mm. short/clearance/crossing/hole 0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none.

## DRC

| | unconnected | P0.16 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 60 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 59 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

