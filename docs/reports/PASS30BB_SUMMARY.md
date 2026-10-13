# PASS30BB_SUMMARY — P0.19

**Timestamp:** 2026-09-30 13:32 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.19
**Git HEAD:** `816310c76593afe19c905ba35450d05129ac5a6f`
**PCB blob at start:** `e1adfbd7a38989b42abaef3557368955484cd560`
**PCB blob at end:** `9f2d8c0370c9ac60c5283fc3cbb2bc8b015d447a`
**U1.30 and J18.7 same island:** False
**Pad-edge:** 36.658325 mm
**New via:** no
**New segments:** 8 (limit 10)
**Skirts crossed:** False
**Skirts ripped:** no
**Min foreign clearance:** 0.17 mm vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'}
**Min POWER/VIN clearance:** 0.2736 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}
**Min hole clearance:** 0.3397 mm vs via P0.06 @44.000,39.900
**P0.19 opens:** 1 → 0
**Unconnected:** 58 → 57
**GND islands:** 12 → 12 (waived)

## Whole-segment skirt test

segment-vs-segment intersection plus 0.05 mm samples along each new segment, both skirts, layers not exempt.
Crossings: **0**. Min centerline distance to either skirt: **0.35 mm** vs {'net': 'P0.16', 'segment': [[45.55, 27.4], [44.6, 27.4]]}.
Both P0.16 (In1.Cu) and P0.17 (In2.Cu) were tested. Different layers were not treated as allowed to cross.

Per new segment, nearest skirt:

- (39.25, 23.10) → (39.25, 26.50) crossed=False nearest P0.17 [[40.25, 23.1], [40.25, 21.5]] center 1.0 mm (edge 0.82 mm), 68 samples
- (39.25, 26.50) → (44.25, 26.50) crossed=False nearest P0.16 [[45.55, 27.4], [44.6, 27.4]] center 0.9657 mm (edge 0.7857 mm), 101 samples
- (44.25, 26.50) → (44.25, 39.10) crossed=False nearest P0.16 [[45.55, 27.4], [44.6, 27.4]] center 0.35 mm (edge 0.17 mm), 253 samples
- (44.25, 39.10) → (42.80, 39.90) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 34 samples
- (42.80, 39.90) → (44.25, 40.70) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 34 samples
- (44.25, 40.70) → (44.25, 63.20) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 0.35 mm (edge 0.17 mm), 451 samples
- (44.25, 63.20) → (53.24, 63.20) crossed=False nearest P0.17 [[48.16, 60.4], [48.16, 61.3]] center 1.9 mm (edge 1.72 mm), 180 samples
- (53.24, 63.20) → (53.24, 62.00) crossed=False nearest P0.17 [[48.16, 60.4], [48.16, 61.3]] center 5.128 mm (edge 4.948 mm), 25 samples

## Why not y=61.63

J18 pads are 1.700 mm circles on y=62.000. y=61.63 is inside J18.4 (P0.16), J18.5 (P0.17) and J18.6 (P0.18). Blocked. Not placed.
Clearance of (44.25, 61.63)–(53.24, 61.63): foreign 0.0 mm vs {'net': 'P0.16', 'item': 'pad J18.4'}; hole -0.22 mm vs hole J18.4 [P0.16].
J18.7 is a 1.700 mm circle at (53.240, 62.000), drill 1.000 mm, on In1.Cu. Pad copper runs y=61.15–62.85. The P0.17 end cap stops at y=61.30 on x=48.16, which is J18.5's center, so there is no corridor between the end cap and the pad. The open eastbound is south of the pads.

## Attempt

In1.Cu 0.18 mm, no new via. Kept. Corners:

- (39.25, 23.10) → (39.25, 26.50) In1.Cu
- (39.25, 26.50) → (44.25, 26.50) In1.Cu
- (44.25, 26.50) → (44.25, 39.10) In1.Cu
- (44.25, 39.10) → (42.80, 39.90) In1.Cu
- (42.80, 39.90) → (44.25, 40.70) In1.Cu
- (44.25, 40.70) → (44.25, 63.20) In1.Cu
- (44.25, 63.20) → (53.24, 63.20) In1.Cu
- (53.24, 63.20) → (53.24, 62.00) In1.Cu

West dodge (44.25, 39.10)→(42.80, 39.90)→(44.25, 40.70) is around P0.06 via (44.000, 39.900). Vertical x=44.25 is 0.35 mm center-to-center from the locked x=44.60 skirts (edge 0.17 mm) and passes between J18.3 (43.08, 62.00) and J18.4 (45.62, 62.00). Eastbound y=63.20 is 1.90 mm south of the P0.17 end cap (y=61.30) and 0.26 mm off the J18 pad copper. North stub ends at the J18.7 center, not past the pad. x>24.2. No new via. P0.17 not retried. No other net.

## Clearance by segment

- (39.25, 23.10)–(39.25, 26.50) ok=True foreign=0.61 vs {'net': 'P0.17', 'item': 'via@40.250,23.100'} power=None vs None hole=0.76 vs via P0.17 @40.250,23.100 why=None
- (39.25, 26.50)–(44.25, 26.50) ok=True foreign=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} power=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} hole=0.4736 vs via VDD2 @44.722,25.900 why=None
- (44.25, 26.50)–(44.25, 39.10) ok=True foreign=0.17 vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=0.2736 vs {'net': 'VDD2', 'item': 'via@44.722,25.900'} hole=0.4736 vs via VDD2 @44.722,25.900 why=None
- (44.25, 39.10)–(42.80, 39.90) ok=True foreign=0.17 vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=None vs None hole=0.3397 vs via P0.06 @44.000,39.900 why=None
- (42.80, 39.90)–(44.25, 40.70) ok=True foreign=0.17 vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'} power=None vs None hole=0.3397 vs via P0.06 @44.000,39.900 why=None
- (44.25, 40.70)–(44.25, 63.20) ok=True foreign=0.17 vs {'net': 'P0.16', 'item': 'trk (44.60,60.40)-(45.62,60.40)'} power=None vs None hole=0.56 vs via ENABLE @43.400,45.126 why=None
- (44.25, 63.20)–(53.24, 63.20) ok=True foreign=0.26 vs {'net': 'P0.16', 'item': 'pad J18.4'} power=None vs None hole=0.61 vs hole J18.4 [P0.16] why=None
- (53.24, 63.20)–(53.24, 62.00) ok=True foreign=1.6 vs {'net': 'P0.18', 'item': 'pad J18.6'} power=None vs None hole=1.95 vs hole J18.6 [P0.18] why=None

## Gate

KEEP. In1.Cu south of both end caps, 8 new segments, no new via. Whole-segment skirt test: 0 crossings (min center distance 0.35 mm). P0.19 opens 1→0. Unconnected 58→57. Foreign 0.17 mm vs {'net': 'P0.16', 'item': 'trk (44.60,27.40)-(44.60,60.40)'}. POWER 0.2736 mm vs {'net': 'VDD2', 'item': 'via@44.722,25.900'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Skirts not crossed or ripped. P0.17 not retried.

## DRC

| | unconnected | P0.19 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 58 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| mid | 57 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 57 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
Locked copper not ripped. P0.16 and P0.17 skirts not crossed and not ripped. P0.17 not retried. No other net. No Gerbers. No git commit.

