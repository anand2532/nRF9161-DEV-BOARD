# PASS30BA_SUMMARY — P0.19

**Timestamp:** 2026-09-30 13:23 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** P0.19
**Git HEAD:** `019630abc7962b82bee07d5c52f7057c9bbcceff`
**PCB blob at start:** `e1adfbd7a38989b42abaef3557368955484cd560`
**U1.30 and J18.7 same island:** False
**New via:** no
**New segments:** 0 (limit 8)
**Min foreign clearance:** 0.17 mm vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'}
**Min POWER/VIN clearance:** 0.2736 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}
**Min hole clearance:** 0.3397 mm vs via P0.06 @44.000,39.900
**P0.19 opens:** 1 → 1
**Unconnected:** 58 → 58
**GND islands:** 12 → 12 (waived)

## Endpoints

U1.30 center [39.25, 26.75], copper point [39.378, 27.147]. Existing exit F.Cu (39.25, 26.75)–(39.25, 23.10) and through-via (39.25, 23.10) were not ripped. J18.7 center [53.24, 62.0] (census point [52.993, 61.187] is inside the 1.7 mm pad, not the center). Same island: **False**. Islands: 2.

U1 island: U1.30, F.Cu (39.250,26.750)-(39.250,23.100), via@39.250,23.100.

J18 island: J18.7, J13.4, F.Cu (64.000,64.000)-(66.400,64.000), via@66.400,64.000, via@64.000,64.000, B.Cu (53.240,64.000)-(64.000,64.000), B.Cu (66.400,64.000)-(71.620,64.000), B.Cu (53.240,62.000)-(53.240,64.000), B.Cu (71.620,64.000)-(71.620,76.000).

## Pad-edge

Remeasured F.Cu effective-shape clearance U1.30↔J18.7: **36.658325 mm** (reported 36.658 mm). Census chord length between [39.378, 27.147] and [52.993, 61.187] is 36.662 mm. U1.30 is F.Cu only, so there is no inner-layer pad-edge.

## Straight chord (not used)

0.18 mm F.Cu chord (39.378, 27.147) → (52.993, 61.187), length 36.662 mm. Crosses the SiP fab body (x 28.0–44.0, y 26.75–37.25): **True**. VDD1 F.Cu (50.52, 38.00)–(43.25, 38.00) w=0.40: the chord centerline intersects that track, so the signed edge clearance is **−0.29 mm** (−(0.09+0.20)). Not used.

Foreign items under 0.15 mm on that chord: 12. POWER/VIN under 0.20 mm: 7.

## Layers checked

Existing via (39.25, 23.10) drill 0.3 mm, pad 0.6 mm, F.Cu to B.Cu. On layers: {'F.Cu': True, 'In1.Cu': True, 'In2.Cu': True, 'B.Cu': True}. Through-via, so the route starts on a layer it already hits. No second via.

- F.Cu: {'cells': 254, 'bbox': [37.75, 40.5, 16.0, 26.5], 'ymax': 26.5, 'xmax': 40.5, 'reaches_j18': False}
- B.Cu: {'cells': 652, 'bbox': [32.75, 46.25, 16.0, 26.5], 'ymax': 26.5, 'xmax': 46.25, 'reaches_j18': False}
- In1.Cu: {'cells': 35483, 'bbox': [24.5, 72.0, 16.0, 70.0], 'ymax': 70.0, 'xmax': 72.0, 'reaches_j18': True}
- In2.Cu: {'cells': 35450, 'bbox': [24.5, 72.0, 16.0, 70.0], 'ymax': 70.0, 'xmax': 72.0, 'reaches_j18': True}

F.Cu and B.Cu free space from the via both die at ymax 26.5, short of J18.7, same wall as the P0.16/P0.17 vias. A second via was not added. In1.Cu and In2.Cu both flood-fill to J18.7. Both inner layers already carry a locked skirt at x=44.60 (P0.16 on In1, P0.17 on In2). The P0.06 via (45.150, 36.000) r=0.25 still closes the strip immediately east of x=44.60 (clearance at x=44.93 is -0.12 mm). The west offset x=44.25 clears that via (0.56 mm) and sits 0.35 mm from the skirt. A second P0.06 via at (44.000, 39.900) blocks x=44.25 at y≈39.9, so the route dodges west of it south of the fab body, then returns. In1 was the one attempt (GND plane; extra islands waived). The eastbound was drawn at y=60.00 on the belief the P0.16 vertical ended before it; that vertical runs to y=60.40, so the segment crosses it. In2 was not used (VDD_nRF zone clearance 0.5 mm, and the P0.17 end cap runs to x=48.16). No sealed B.Cu pocket. x>24.2.

P0.06 via check: {'net': 'P0.06', 'at': [45.15, 36.0], 'radius_mm': 0.25, 'need_dx_mm': 0.49, 'skirt_x': 44.6, 'east_of_skirt_x': 44.93, 'clearance_at_x_44_93_mm': -0.12, 'clearance_at_x_44_25_mm': 0.56, 'east_strip_closed': True, 'west_x_44_25_clears_this_via': True}.

## Attempt

One In1.Cu jog, 0.18 mm, no new via. Added, then removed. Corners:

- (39.25, 23.10) → (39.25, 26.50)
- (39.25, 26.50) → (44.25, 26.50)
- (44.25, 26.50) → (44.25, 39.10)
- (44.25, 39.10) → (42.80, 39.90)
- (42.80, 39.90) → (44.25, 40.70)
- (44.25, 40.70) → (44.25, 60.00)
- (44.25, 60.00) → (53.24, 60.00)
- (53.24, 60.00) → (53.24, 61.40)

x=44.25 is 0.35 mm center-to-center from the locked x=44.60 skirts. The two diagonals dodge P0.06 via (44.000, 39.900). The eastbound segment (44.25, 60.00)–(53.24, 60.00) crosses the locked P0.16 In1 skirt (44.60, 27.40)–(44.60, 60.40) at (44.60, 60.00). Endpoint clearance to that skirt was 0.17 mm and missed the interior intersection. DRC `tracks_crossing` = 1 on that pair. P0.19 opens went 1→0 on the mid board. Full restore from `.mcp-backups/pass30ba/pre-edit.kicad_pcb`. No second path.

## Gate

NO-ROUTE. Mid short/clearance/crossing/hole 0/0/1/0. hole_to_hole 1→1. Other non-GND gained: none. Foreign pre-add 0.17 mm vs P0.16 skirt (44.60, 27.40)–(44.60, 60.40) is the endpoint figure; the real fail is the crossing of that skirt. POWER pre-add 0.2736 mm vs VDD2 via (44.722, 25.900). Post-revert DRC matches pre-edit: unconnected 58, P0.19 1, short/clearance/crossing/hole 0/0/0/0, hole_to_hole 1, GND islands 12.

## DRC

| | unconnected | P0.19 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 58 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| mid (reverted) | 57 | 0 | 0 | 0 | 1 | 0 | 1 | 12 |
| after restore | 58 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
Locked copper not ripped. P0.17 not retried. No other net. No Gerbers. No git commit.

