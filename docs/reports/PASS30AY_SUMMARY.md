# PASS30AY_SUMMARY — P0.17

**Timestamp:** 2026-09-30 12:57 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.17
**Git HEAD:** `c801f86437d7f588994839176f6be98a41a85d5b`
**PCB blob at start:** `b17e5794de90387894b0a45376d750cae33bde73`
**Side of package:** east skirt on In2.Cu
**New via:** no
**New segments:** 7 (limit 8)
**Min foreign clearance:** 0.21 mm vs {'net': 'P0.06', 'item': 'via@45.150,36.000'}
**Min POWER/VIN clearance:** 0.3378 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}
**Min hole clearance (pre-add):** 0.31 mm vs via P0.06 @45.150,36.000
**P0.17 opens:** 2 → 1
**Unconnected:** 59 → 58
**GND islands:** 12 → 12 (waived)
**Backup:** `/workspace/kicad-projects/nRF9161-DEV-BOARD/.mcp-backups/pass30ay/pre-edit.kicad_pcb`

## Remeasured gap

Pad-edge **34.860476 mm** (reported 34.86 mm) on F.Cu effective shapes, U1.28 [40.25, 26.75] to J18.5 [48.16, 62.0]. The stated copper points [40.378, 27.147] → [47.913, 61.187] are 34.864 mm apart (J18.5 center is (48.16, 62.0); (47.913, 61.187) is on the pad edge). Other island is J18.5, already on F.Cu and B.Cu. U1 island is the existing stub F.Cu (40.25, 26.75)–(40.25, 23.10) plus through-via (40.25, 23.10). The second via (40.25, 23.95) was not ripped. Stub not ripped.

## Straight line (not used)

0.18 mm F.Cu chord [40.378, 27.147] → [47.913, 61.187] (34.864 mm). Crosses the SiP body. GND via (42.0, 35.0) clearance **-0.276 mm** (via@42.000,35.000, pad radius 0.3 mm). Foreign nets under 0.15 mm: <no-net>, ENABLE, GND, P0.04 (13 items). Not used.

## Layers checked

Existing via (40.25, 23.10) drill 0.3 mm, pad 0.6 mm, F.Cu to B.Cu. On layers: {'F.Cu': True, 'In1.Cu': True, 'In2.Cu': True, 'B.Cu': True}. It is a through via, so the new copper starts on a layer it already hits. No second via.

Free space (0.18 mm centerline, foreign ≥ 0.15, POWER ≥ 0.20, hole ≥ 0.25, off the fab body, x > 24.2, zones ignored because refill pulls them back) from that via:

- F.Cu: {'cells': 250, 'bbox': [37.75, 40.75, 16.0, 26.5], 'ymax': 26.5, 'reaches_j18': False}
- B.Cu: {'cells': 667, 'bbox': [32.75, 46.25, 16.0, 26.5], 'ymax': 26.5, 'reaches_j18': False}
- In1.Cu: {'cells': 30894, 'bbox': [24.5, 72.0, 16.0, 64.0], 'ymax': 64.0, 'reaches_j18': True}
- In2.Cu: {'cells': 31299, 'bbox': [24.5, 72.0, 16.0, 64.0], 'ymax': 64.0, 'reaches_j18': True}

F.Cu and B.Cu both die at ymax 26.5, short of the header, same as the P0.16 via. One extra via cannot join a pocket that ends near y≈27 to J18.5. In1.Cu flood-fill does reach J18.5, but the locked pass30ax skirt (40.70, 20.80)→(45.55, 20.80)→(45.55, 27.40)→(44.60, 27.40)→(44.60, 60.40)→(45.62, 60.40)→(45.62, 61.10) owns that east corridor. Same-layer 0.18 mm centerlines need ≥ 0.33 mm. The P0.06 via (45.150, 36.000) closes the strip beside x=44.60, so this attempt does not run on In1. In2.Cu has no tracks in the corridor and the through-via already hits it. In2 is the VDD_nRF plane (zone local clearance 0.5 mm). The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 was not used. x > 24.2. No west skirt.

## Route

In2.Cu 0.18 mm, east of the body (long run x=44.60). No new via. Corners:

- (40.25, 23.10) → (40.25, 21.50)
- (40.25, 21.50) → (45.55, 21.50)
- (45.55, 21.50) → (45.55, 27.40)
- (45.55, 27.40) → (44.60, 27.40)
- (44.60, 27.40) → (44.60, 60.40)
- (44.60, 60.40) → (48.16, 60.40)
- (48.16, 60.40) → (48.16, 61.30)

North of the fab body at y=21.50, drop at x=45.55 (clears VDD2 via (44.722, 25.900)), then x=44.60 from y=27.40 to y=60.40 (clears P0.06 via (45.150, 36.000) by 0.21 mm; copper edge x=44.51, fab body ends at x=44.0). End cap (48.16, 60.40)–(48.16, 61.30) overlaps J18.5. P0.16's matching XY on In1.Cu is a different layer, so the 0.33 mm same-layer rule does not apply. That In1 copper was not ripped.

## Gate

KEEP. East In2 skirt, 7 new segments, no new via. P0.17 opens 2→1. Unconnected 59→58. Foreign 0.21 mm vs {'net': 'P0.06', 'item': 'via@45.150,36.000'}. POWER 0.3378 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Locked copper not ripped.

## DRC

| | unconnected | P0.17 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 59 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 58 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
Locked copper not ripped. No Gerbers. No git commit.

