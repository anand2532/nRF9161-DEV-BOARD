# PASS30BC_SUMMARY — P0.20

**Timestamp:** 2026-09-30 13:43 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.20
**Git HEAD:** `9ad4b9475455a74a7195575b6d0cec9b6566a38e`
**PCB blob at start:** `9f2d8c0370c9ac60c5283fc3cbb2bc8b015d447a`
**PCB blob at end:** `2d07228fba7bf2e61497e4e15cb3c4a9b90e1d57`
**Expected tip/blob matched:** True / True
**Ends already one island:** False
**Far island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far island F.Cu only:** False
**U1 island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Pad-edge (U1.35 to F.Cu 55.78 stub):** 38.594909 mm (census 38.595)
**Existing via:** {'pos': [36.2, 20.8], 'drill_mm': 0.3, 'pad_mm': 0.6, 'top': 'F.Cu', 'bottom': 'B.Cu', 'through': True, 'on': {'F.Cu': True, 'In1.Cu': True, 'In2.Cu': True, 'B.Cu': True}}
**New via:** no
**Third In1 skirt:** no
**New segments:** 9 (limit 10)
**Crossing test failed:** False
**Min foreign clearance:** 0.17 mm vs {'net': 'P0.17', 'item': 'trk (44.60,27.40)-(44.60,60.40)'}
**Min POWER/VIN clearance:** 0.2736 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}
**Min hole clearance:** 0.3397 mm vs via P0.06 @44.000,39.900
**P0.20 opens:** 1 → 0
**Unconnected:** 57 → 56
**GND islands:** 12 → 12 (waived)

## Islands

U1 island: ['U1.35', 'F.Cu (36.750,26.750)-(36.200,20.800)', 'via@36.200,20.800']
Far island: ['J18.8', 'J13.5', 'F.Cu (55.780,62.000)-(55.780,60.900)', 'F.Cu (74.160,60.900)-(74.160,76.000)', 'F.Cu (55.780,60.900)-(74.160,60.900)']

## Straight chord

F.Cu 0.18 mm (36.878, 27.147) → (55.736, 60.821), length 38.59485 mm. Crosses SiP body: True. P0.06 via {'via_xy': [44.0, 39.9], 'via_radius_mm': 0.3, 'centerline_distance_mm': 0.0174, 'edge_clearance_mm': -0.3726}. Not used.

## Layer exit from (36.20, 20.80)

F.Cu and B.Cu (and In1/In2 on this same x) die at the P0.21 via (35.750, 23.100), before y=26.5. The neighbor vias at x=39.25/40.25 were the ones that died at y=26.5. This via is through-hole to In2, so the route jogs to x=36.45 on In2 and does not punch a new via.

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, and P0.19, layers not exempt. Collinear overlap with P0.19 is the x=44.25 In2 slot, not a crossing. Endpoint-only touches are not crossings. A sample in the interior of a locked segment is a crossing.
Crossings: **0**. Min centerline to P0.16/P0.17: **0.35 mm** vs {'net': 'P0.16', 'segment': [[45.55, 27.4], [44.6, 27.4]]}. Min centerline to P0.19: **0.0 mm** (0 means the same-centerline slot, not a transverse cross). Stacks recorded: 6.

Per new segment, nearest of P0.16/P0.17:

- (36.20, 20.80) → (36.45, 20.80) crossed=False nearest P0.17 [[40.25, 23.1], [40.25, 21.5]] center 3.8639 mm (edge 3.6839 mm), 6 samples
- (36.45, 20.80) → (36.45, 26.50) crossed=False nearest P0.17 [[40.25, 23.1], [40.25, 21.5]] center 3.8 mm (edge 3.62 mm), 114 samples
- (36.45, 26.50) → (44.25, 26.50) crossed=False nearest P0.16 [[45.55, 27.4], [44.6, 27.4]] center 0.9657 mm (edge 0.7857 mm), 156 samples
- (44.25, 26.50) → (44.25, 39.10) crossed=False nearest P0.16 [[45.55, 27.4], [44.6, 27.4]] center 0.35 mm (edge 0.17 mm), 253 samples
- (44.25, 39.10) → (42.80, 39.90) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 34 samples
- (42.80, 39.90) → (44.25, 40.70) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 34 samples
- (44.25, 40.70) → (44.25, 63.20) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 451 samples
- (44.25, 63.20) → (55.78, 63.20) crossed=False nearest P0.17 [[48.16, 60.4], [48.16, 61.3]] center 1.9 mm (edge 1.72 mm), 231 samples
- (55.78, 63.20) → (55.78, 62.00) crossed=False nearest P0.17 [[48.16, 60.4], [48.16, 61.3]] center 7.6521 mm (edge 7.4721 mm), 25 samples

## Why not y=61.63

J18 pads are 1.700 mm circles on y=62.000. y=61.63 is inside the pad copper. Not placed.
Probe (44.25, 61.63)–(55.78, 61.63) foreign 0.0 mm vs {'net': 'P0.16', 'item': 'pad J18.4'}.

## No-dodge check

{'ok': False, 'foreign_mm': -0.14, 'foreign_item': {'net': 'P0.06', 'item': 'via@44.000,39.900'}, 'hole_mm': 0.01, 'hole_item': 'via P0.06 @44.000,39.900', 'why': 'x=44.25 passes 0.25 mm from P0.06 via (44.000, 39.900). Edge clearance is negative. Dodge required. P0.19 dodge not ripped.'}

## Attempt

In2.Cu 0.18 mm, no new via. Kept.

- (36.20, 20.80) → (36.45, 20.80) In2.Cu
- (36.45, 20.80) → (36.45, 26.50) In2.Cu
- (36.45, 26.50) → (44.25, 26.50) In2.Cu
- (44.25, 26.50) → (44.25, 39.10) In2.Cu
- (44.25, 39.10) → (42.80, 39.90) In2.Cu
- (42.80, 39.90) → (44.25, 40.70) In2.Cu
- (44.25, 40.70) → (44.25, 63.20) In2.Cu
- (44.25, 63.20) → (55.78, 63.20) In2.Cu
- (55.78, 63.20) → (55.78, 62.00) In2.Cu

x=36.45 clears the P0.21 via (35.750, 23.100) that blocks a straight south exit. y=26.50 then x=44.25 is the In2 slot beside the P0.17 skirt (x=44.60) and on the P0.19 centerline. West dodge (44.25, 39.10)→(42.80, 39.90)→(44.25, 40.70) around P0.06 via (44.000, 39.900). Eastbound y=63.20, then north onto J18.8 (55.78, 62.00). No third In1 skirt. No via punched into the F.Cu stub. Skirts and the P0.19 run not ripped. x>24.2. No other net.

## Clearance by segment

- (36.20, 20.80)–(36.45, 20.80) ok=True foreign=0.9186 vs {'net': 'P0.22', 'item': 'via@35.250,19.900'} power=None vs None hole=1.0686 vs via P0.22 @35.250,19.900 why=None
- (36.45, 20.80)–(36.45, 26.50) ok=True foreign=0.31 vs {'net': 'P0.21', 'item': 'via@35.750,23.100'} power=None vs None hole=0.46 vs via P0.21 @35.750,23.100 why=None
- (36.45, 26.50)–(44.25, 26.50) ok=True foreign=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} power=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} hole=0.4736 vs via VDD2 @44.722,25.900 why=None
- (44.25, 26.50)–(44.25, 39.10) ok=True foreign=0.17 vs {'net': 'P0.17', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} hole=0.4736 vs via VDD2 @44.722,25.900 why=None
- (44.25, 39.10)–(42.80, 39.90) ok=True foreign=0.17 vs {'net': 'P0.17', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=None vs None hole=0.3397 vs via P0.06 @44.000,39.900 why=None
- (42.80, 39.90)–(44.25, 40.70) ok=True foreign=0.17 vs {'net': 'P0.17', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=None vs None hole=0.3397 vs via P0.06 @44.000,39.900 why=None
- (44.25, 40.70)–(44.25, 63.20) ok=True foreign=0.17 vs {'net': 'P0.17', 'item': 'trk (44.60,60.40)-(48.16,60.40)'} power=None vs None hole=0.56 vs via ENABLE @43.400,45.126 why=None
- (44.25, 63.20)–(55.78, 63.20) ok=True foreign=0.26 vs {'net': 'P0.16', 'item': 'pad J18.4'} power=1.8692 vs {'net': 'VDD_GPIO', 'item': 'pad J18.9'} hole=0.61 vs hole J18.4 [P0.16] why=None
- (55.78, 63.20)–(55.78, 62.00) ok=True foreign=1.6 vs {'net': 'P0.19', 'item': 'pad J18.7'} power=1.6 vs {'net': 'VDD_GPIO', 'item': 'pad J18.9'} hole=1.95 vs hole J18.7 [P0.19] why=None

## Gate

KEEP. In2.Cu x=44.25 slot, 9 new segments, no new via. Whole-segment crossing test: 0 crossings (min center to P0.16/P0.17 0.35 mm; P0.19 same-centerline stacks 6, not crossings). P0.20 opens 1→0. Unconnected 57→56. Foreign 0.17 mm vs {'net': 'P0.17', 'item': 'trk (44.60,27.40)-(44.60,60.40)'}. POWER 0.2736 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. No third In1 skirt. Skirts and P0.19 not ripped.

## DRC

| | unconnected | P0.20 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 57 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| mid | 56 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 56 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 skirts and the P0.19 run not ripped. No third In1 skirt. No new via. No other net. No Gerbers. No git commit.

