# PASS30BI_SUMMARY — P0.05 U1.2 to J12.6

**Timestamp:** 2026-09-30 18:00 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.05
**Pair:** U1.2 ↔ J12.6 only
**Git HEAD:** `99ff66c8a933ebb01cc397bcf392732c55d9c9c6`
**PCB blob at start:** `953e98bc52f2b39ffec50928389f4492eff69ce7`
**PCB blob at end:** `7bcfe5791b156e426a2a0affefe938be4d39f8e6`
**sha1sum at start:** `828df5c6726a56fb12bc18312f258fc973d582d6`
**sha1sum at end:** `c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40`
**Expected tip/blob matched:** True / True
**End blob matches start:** False
**Ends already one island:** False
**Via (47.40, 36.50) on U1.2 island:** True
**Start via:** {'xy': [47.4, 36.5], 'width_mm': 0.6, 'radius_mm': 0.3, 'drill_mm': 0.3, 'through': True, 'nm': [47400000, 36500000], 'net': 'P0.05'}
**J12.6 center:** [18.7, 76.0]
**J12.6 size mm:** [1.7, 1.7]
**J12.6 drill mm:** 1.0
**J12.6 layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far island F.Cu-only:** False
**U1 island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Pad-edge (U1.2 copper to J12.6 copper):** 45.730103 mm (census 45.733)
**New via:** no
**Joined:** J12.6 pad center on In1.Cu (PTH copper already on In1)
**New segments:** 7 (limit 10)
**Crossing test failed:** False
**Whole-segment crossing count:** 0
**Min foreign clearance:** 0.33 mm vs {'net': 'P0.20', 'item': 'pad J18.8'}
**Min POWER/VIN clearance:** 0.33 mm vs {'net': 'VDD_GPIO', 'item': 'pad J18.9'}
**Min hole clearance:** 0.68 mm vs hole J18.8 [P0.20]
**Other P0.05 opens left untouched:** [{'name': 'J9.3', 'xy': [116.0, 13.08], 'island': ['J9.3'], 'same_as_u1': False, 'same_as_j12': False}]
**P0.05 opens:** 2 → 1
**U1.2↔J12.6 open:** True → False
**Unconnected:** 52 → 51
**GND islands:** 12 → 12 (waived)
**J9.2 before/after:** {'xy': [116.0, 10.54], 'net': 'P0.07', 'fp_xy': [116.0, 8.0]} / {'xy': [116.0, 10.54], 'net': 'P0.07', 'fp_xy': [116.0, 8.0]}

## Islands

U1 island: ['U1.2', 'F.Cu (44.000,36.500)-(47.400,36.500)', 'via@47.400,36.500']
Far island: ['J12.6']

## Straight chord

F.Cu 0.18 mm [43.622, 36.647] → [19.101, 75.25], length 45.732604 mm. Crosses SiP body: True. P0.02 {'xy': [40.75, 41.1], 'width_mm': 0.6, 'center_distance_mm': 0.03664350727677847, 'edge_clearance_mm': -0.35335649272322156}. Not used.

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, P0.19, P0.20, the SIM_CLK In1 run, the SIM_RST run (F.Cu neck plus In1), the P0.00 In1 run, and the P0.07 In2 run. Layers are not exempt. A same-centerline stack on x=44.25, x=44.60, the y=63.20 eastbounds, or any locked P0.07 centerline is a fail. Endpoint-only touches are not crossings.
Crossings: **0**. Min centerline to a locked run: **0.5 mm** vs {'net': 'P0.07', 'segment': [[48.05, 35.5], [48.05, 37.9]]}.

- (47.4, 36.5) → (47.4, 38.4) crossed=False nearest P0.07 [[48.05, 35.5], [48.05, 37.9]] center 0.65 mm (edge 0.47 mm), 38 samples
- (47.4, 38.4) → (57.05, 38.4) crossed=False nearest P0.07 [[48.05, 35.5], [48.05, 37.9]] center 0.5 mm (edge 0.32 mm), 193 samples
- (57.05, 38.4) → (57.05, 74.7) crossed=False nearest P0.07 [[48.05, 37.9], [63.1, 37.9]] center 0.5 mm (edge 0.32 mm), 727 samples
- (57.05, 74.7) → (22.51, 74.7) crossed=False nearest P0.07 [[25.2, 79.2], [25.2, 76.0]] center 1.3 mm (edge 1.12 mm), 691 samples
- (22.51, 74.7) → (22.51, 79.4) crossed=False nearest P0.07 [[25.2, 76.0], [23.78, 76.0]] center 1.27 mm (edge 1.09 mm), 95 samples
- (22.51, 79.4) → (18.7, 79.4) crossed=False nearest P0.07 [[62.7, 79.2], [25.2, 79.2]] center 2.6974 mm (edge 2.5174 mm), 77 samples
- (18.7, 79.4) → (18.7, 76.0) crossed=False nearest P0.07 [[25.2, 76.0], [23.78, 76.0]] center 5.08 mm (edge 4.9 mm), 69 samples

## Attempt

In1.Cu only, 7 segments, no new via. Via (47.40, 36.50) is P0.05 and is on the U1.2 island. Starts there and lands on J12.6 (PTH, In1 copper) from the south. Kept.

- (47.4, 36.5) → (47.4, 38.4) In1.Cu 0.18 mm
- (47.4, 38.4) → (57.05, 38.4) In1.Cu 0.18 mm
- (57.05, 38.4) → (57.05, 74.7) In1.Cu 0.18 mm
- (57.05, 74.7) → (22.51, 74.7) In1.Cu 0.18 mm
- (22.51, 74.7) → (22.51, 79.4) In1.Cu 0.18 mm
- (22.51, 79.4) → (18.7, 79.4) In1.Cu 0.18 mm
- (18.7, 79.4) → (18.7, 76.0) In1.Cu 0.18 mm

South of the P0.07 y=37.90 run at y=38.40 (0.50 mm off that centerline), east to x=57.05 (the J18.8/J18.9 gap, east of the P0.20 y=63.20 end at x=55.78), south to y=74.70 (north of the J12 row and of the P0.07 x=25.20 wall), west to x=22.51 (the J12.7/J12.8 gap), south to y=79.40 (south of the P0.07 y=79.20 run and of the header, west of x=25.20 so the locked horizontal is not crossed), west to x=18.70, then north onto the J12.6 pad center. x=44.25 and x=44.60 not used. P0.07 centerline not used. Sealed y=44.60 pocket not entered. RF keepout box x<=24.2 and y in [20, 64] not entered. P0.00, SIM_RST, SIM_CLK, and P0.07 centerlines not stacked. J9.2 not touched. No header or U1 move. No other net. J9.3 left open.

## Clearance by segment

- In1.Cu (47.4, 36.5)–(47.4, 38.4) ok=True foreign=0.61 vs {'net': 'P0.07', 'item': 'via@47.400,35.500'} power=None vs None hole=0.76 vs via P0.07 @47.400,35.500 why=None
- In1.Cu (47.4, 38.4)–(57.05, 38.4) ok=True foreign=2.01 vs {'net': 'P0.06', 'item': 'via@48.620,36.000'} power=2.4504 vs {'net': 'VDD2', 'item': 'via@59.700,37.126'} hole=2.16 vs via P0.06 @48.620,36.000 why=None
- In1.Cu (57.05, 38.4)–(57.05, 74.7) ok=True foreign=0.33 vs {'net': 'P0.20', 'item': 'pad J18.8'} power=0.33 vs {'net': 'VDD_GPIO', 'item': 'pad J18.9'} hole=0.68 vs hole J18.8 [P0.20] why=None
- In1.Cu (57.05, 74.7)–(22.51, 74.7) ok=True foreign=0.36 vs {'net': 'P0.07', 'item': 'pad J12.8'} power=0.36 vs {'net': 'VDD_GPIO', 'item': 'pad J12.17'} hole=0.71 vs hole J12.8 [P0.07] why=None
- In1.Cu (22.51, 74.7)–(22.51, 79.4) ok=True foreign=0.33 vs {'net': 'P0.06', 'item': 'pad J12.7'} power=None vs None hole=0.68 vs hole J12.8 [P0.07] why=None
- In1.Cu (22.51, 79.4)–(18.7, 79.4) ok=True foreign=1.7941 vs {'net': 'P0.01', 'item': 'via@24.500,78.500'} power=None vs None hole=1.9441 vs via P0.01 @24.500,78.500 why=None
- In1.Cu (18.7, 79.4)–(18.7, 76.0) ok=True foreign=1.6 vs {'net': 'P0.04', 'item': 'pad J12.5'} power=None vs None hole=1.95 vs hole J12.5 [P0.04] why=None

## Gate

KEEP. In1 south approach, 7 new segments, no new via, from existing P0.05 through-via (47.40, 36.50) onto J12.6. Via is on the U1.2 island. Straight F.Cu chord not used (P0.02). P0.07 centerline not used. Skirt slot, sealed pocket, and RF keepout not used. Whole-segment crossings: 0. P0.05 opens 2→1. U1.2↔J12.6 open closed. Unconnected 52→51. Foreign 0.33 mm vs {'net': 'P0.20', 'item': 'pad J18.8'}. POWER 0.33 mm vs {'net': 'VDD_GPIO', 'item': 'pad J18.9'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. J9.3 left open. J9.2 not touched. Four skirts, SIM_CLK, SIM_RST, P0.00, and P0.07 not ripped or stacked. No other net.

## DRC

| | unconnected | P0.05 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 52 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. SIM_CLK, SIM_RST, P0.00, and the P0.07 In2 run not ripped and not stacked. J9.2 not touched. Skirt slot, sealed pocket, and RF keepout not used. No other net. No Gerbers. No git commit.

