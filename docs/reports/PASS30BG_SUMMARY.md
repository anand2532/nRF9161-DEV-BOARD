# PASS30BG_SUMMARY — P0.07

**Timestamp:** 2026-09-30 17:41 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.07
**Git HEAD:** `e851c3b7098da41ad116489be01451cd2c113723`
**PCB blob at start:** `1689715203e755d4422b71fb29202c387b9c7889`
**PCB blob at end:** `953e98bc52f2b39ffec50928389f4492eff69ce7`
**Expected tip/blob matched:** True / True
**Ends already one island:** False
**Named via (47.40, 36.50) on U1.4 island:** False
**Named via:** {'net': 'P0.05', 'xy': [47.4, 36.5], 'width_mm': 0.6, 'radius_mm': 0.3, 'drill_mm': 0.3, 'through': True, 'nm': [47400000, 36500000], 'on_u1_island': False}
**Start via (47.40, 35.50) on U1.4 island:** True
**Start via:** {'xy': [47.4, 35.5], 'width_mm': 0.6, 'radius_mm': 0.3, 'drill_mm': 0.3, 'through': True, 'nm': [47400000, 35500000], 'net': 'P0.07'}
**J12.8 center:** [23.78, 76.0]
**J12.8 layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far island F.Cu-only:** False
**U1 island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Pad-edge (U1.4 to J12.8):** 44.117219 mm (census 44.118)
**New via:** no
**Joined:** J12.8 pad center on In2.Cu (PTH copper already on In2)
**New segments:** 9 (limit 10)
**Crossing test failed:** False
**Whole-segment crossing count:** 0
**Min foreign clearance:** 0.18 mm vs {'net': 'P0.08', 'item': 'pad J12.9'}
**Min POWER/VIN clearance:** 0.2842 mm vs {'net': 'VDD2', 'item': 'via@59.700,37.126'}
**Min hole clearance:** 0.33 mm vs via P0.06 @48.620,36.000
**P0.07 opens:** 2 → 1
**Unconnected:** 53 → 52
**GND islands:** 12 → 12 (waived)

## Islands

U1 island: ['U1.4', 'F.Cu (44.000,35.500)-(47.400,35.500)', 'via@47.400,35.500']
Far island: ['J12.8']

## Straight chord

F.Cu 0.18 mm [43.622, 35.647] → [24.181, 75.25], length 44.117458 mm. Crosses SiP body: True. P0.02 {'xy': [40.75, 41.1], 'width_mm': 0.6, 'center_distance_mm': 0.17516972579450418, 'edge_clearance_mm': -0.2148302742054958}. Not used.

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, P0.19, P0.20, the SIM_CLK In1 run, the SIM_RST run (F.Cu neck plus In1), and the P0.00 In1 run. Layers are not exempt. A same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds is a fail. Endpoint-only touches are not crossings.
Crossings: **0**. Min centerline to a locked run: **1.9 mm** vs {'net': 'SIM_CLK', 'segment': [[57.2, 19.55], [57.2, 36.0]]}.

- (47.4, 35.5) → (48.05, 35.5) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 2.8 mm (edge 2.62 mm), 13 samples
- (48.05, 35.5) → (48.05, 37.9) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 3.45 mm (edge 3.27 mm), 48 samples
- (48.05, 37.9) → (63.1, 37.9) crossed=False nearest SIM_CLK [[57.2, 19.55], [57.2, 36.0]] center 1.9 mm (edge 1.72 mm), 302 samples
- (63.1, 37.9) → (63.1, 70.0) crossed=False nearest SIM_CLK [[57.2, 36.0], [73.3, 36.0]] center 1.9 mm (edge 1.72 mm), 643 samples
- (63.1, 70.0) → (62.7, 70.0) crossed=False nearest P0.20 [[44.25, 63.2], [55.78, 63.2]] center 9.7019 mm (edge 9.5219 mm), 8 samples
- (62.7, 70.0) → (62.7, 79.2) crossed=False nearest P0.20 [[44.25, 63.2], [55.78, 63.2]] center 9.7019 mm (edge 9.5219 mm), 185 samples
- (62.7, 79.2) → (25.2, 79.2) crossed=False nearest P0.19 [[44.25, 40.7], [44.25, 63.2]] center 16.0 mm (edge 15.82 mm), 751 samples
- (25.2, 79.2) → (25.2, 76.0) crossed=False nearest P0.19 [[44.25, 40.7], [44.25, 63.2]] center 22.9509 mm (edge 22.7709 mm), 65 samples
- (25.2, 76.0) → (23.78, 76.0) crossed=False nearest P0.19 [[44.25, 40.7], [44.25, 63.2]] center 22.9509 mm (edge 22.7709 mm), 29 samples

## Attempt

In2.Cu only, 9 segments, no new via. Named via (47.40, 36.50) is P0.05 and was not used. Starts at existing P0.07 through-via (47.40, 35.50) and lands on J12.8 (PTH, In2 copper). Kept.

- (47.4, 35.5) → (48.05, 35.5) In2.Cu 0.18 mm
- (48.05, 35.5) → (48.05, 37.9) In2.Cu 0.18 mm
- (48.05, 37.9) → (63.1, 37.9) In2.Cu 0.18 mm
- (63.1, 37.9) → (63.1, 70.0) In2.Cu 0.18 mm
- (63.1, 70.0) → (62.7, 70.0) In2.Cu 0.18 mm
- (62.7, 70.0) → (62.7, 79.2) In2.Cu 0.18 mm
- (62.7, 79.2) → (25.2, 79.2) In2.Cu 0.18 mm
- (25.2, 79.2) → (25.2, 76.0) In2.Cu 0.18 mm
- (25.2, 76.0) → (23.78, 76.0) In2.Cu 0.18 mm

East of the SiP at x=48.05 (clear of the P0.06 via at 48.62, 36.00), east to x=63.10 (east of the P0.20 y=63.20 end at x=55.78 and of the skirt verticals), south to y=70, jog to x=62.70 to clear J13.1, south to y=79.20 (south of the header row and of the RF keepout), west to x=25.20, north into the gap east of J12.8, then west onto the pad center. x=44.25 and x=44.60 not used. Sealed y=44.60 pocket not entered. RF keepout box x<=24.2 and y in [20, 64] not entered. P0.00, SIM_RST, and SIM_CLK centerlines not stacked. No header or U1 move. No other net.

## Clearance by segment

- In2.Cu (47.4, 35.5)–(48.05, 35.5) ok=True foreign=0.3682 vs {'net': 'P0.06', 'item': 'via@48.620,36.000'} power=None vs None hole=0.5182 vs via P0.06 @48.620,36.000 why=None
- In2.Cu (48.05, 35.5)–(48.05, 37.9) ok=True foreign=0.18 vs {'net': 'P0.06', 'item': 'via@48.620,36.000'} power=None vs None hole=0.33 vs via P0.06 @48.620,36.000 why=None
- In2.Cu (48.05, 37.9)–(63.1, 37.9) ok=True foreign=0.2842 vs {'net': 'VDD2', 'item': 'via@59.700,37.126'} power=0.2842 vs {'net': 'VDD2', 'item': 'via@59.700,37.126'} hole=0.4842 vs via VDD2 @59.700,37.126 why=None
- In2.Cu (63.1, 37.9)–(63.1, 70.0) ok=True foreign=0.21 vs {'net': 'ENABLE', 'item': 'via@62.500,40.950'} power=0.81 vs {'net': 'VDD2', 'item': 'via@61.800,45.100'} hole=0.36 vs via ENABLE @62.500,40.950 why=None
- In2.Cu (63.1, 70.0)–(62.7, 70.0) ok=True foreign=2.6877 vs {'net': 'P0.08', 'item': 'via@65.200,72.250'} power=None vs None hole=2.8377 vs via P0.08 @65.200,72.250 why=None
- In2.Cu (62.7, 70.0)–(62.7, 79.2) ok=True foreign=0.31 vs {'net': 'P0.01', 'item': 'via@62.000,74.500'} power=None vs None hole=0.46 vs via P0.01 @62.000,74.500 why=None
- In2.Cu (62.7, 79.2)–(25.2, 79.2) ok=True foreign=0.31 vs {'net': 'P0.01', 'item': 'via@27.200,78.500'} power=2.26 vs {'net': 'VDD_GPIO', 'item': 'pad J12.17'} hole=0.46 vs via P0.01 @27.200,78.500 why=None
- In2.Cu (25.2, 79.2)–(25.2, 76.0) ok=True foreign=0.18 vs {'net': 'P0.08', 'item': 'pad J12.9'} power=None vs None hole=0.46 vs via P0.01 @24.500,78.500 why=None
- In2.Cu (25.2, 76.0)–(23.78, 76.0) ok=True foreign=0.18 vs {'net': 'P0.08', 'item': 'pad J12.9'} power=None vs None hole=0.53 vs hole J12.9 [P0.08] why=None

## Gate

KEEP. In2 south bypass, 9 new segments, no new via, from existing P0.07 through-via (47.40, 35.50) onto J12.8. Named via (47.40, 36.50) is P0.05 and was not used. Straight F.Cu chord not used (P0.02). Skirt slot, sealed pocket, and RF keepout not used. Whole-segment crossings: 0. P0.07 opens 2→1. Unconnected 53→52. Foreign 0.18 mm vs {'net': 'P0.08', 'item': 'pad J12.9'}. POWER 0.2842 mm vs {'net': 'VDD2', 'item': 'via@59.700,37.126'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Four skirts, SIM_CLK, SIM_RST, and P0.00 not ripped or stacked. No other net.

## DRC

| | unconnected | P0.07 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 53 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 52 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. SIM_CLK, SIM_RST, and P0.00 not ripped and not stacked. Skirt slot, sealed pocket, and RF keepout not used. No other net. No Gerbers. No git commit.

