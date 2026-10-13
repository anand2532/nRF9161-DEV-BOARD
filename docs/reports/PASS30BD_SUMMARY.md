# PASS30BD_SUMMARY — SIM_CLK

**Timestamp:** 2026-09-30 13:58 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** SIM_CLK
**Git HEAD:** `558e22168742b1b3293ff22ca9a987baccc5f8c5`
**PCB blob at start:** `2d07228fba7bf2e61497e4e15cb3c4a9b90e1d57`
**PCB blob at end:** `036e870670d173055c85ca41c994405c95fbb4e8`
**Expected tip/blob matched:** True / True
**Ends already one island:** False
**Far island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**U1 island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Pad-edge (U1.46 to B.Cu 45.50 track):** 40.989923 mm (census 40.990)
**Existing via:** {'pos': [31.25, 23.1], 'drill_mm': 0.3, 'pad_mm': 0.6, 'top': 'F.Cu', 'bottom': 'B.Cu', 'through': True, 'on': {'F.Cu': True, 'In1.Cu': True, 'In2.Cu': True, 'B.Cu': True}}
**New via:** no
**New segments:** 9 (limit 10)
**Crossing test failed:** False
**Min foreign clearance:** 0.169 mm vs {'net': 'ENABLE', 'item': 'via@56.500,20.300'}
**Min POWER/VIN clearance:** 0.2836 mm vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'}
**Min hole clearance:** 0.319 mm vs via ENABLE @56.500,20.300
**SIM_CLK opens:** 1 → 0
**Unconnected:** 56 → 55
**GND islands:** 12 → 12 (waived)

## Islands

U1 island: ['U1.46', 'F.Cu (31.250,26.750)-(31.250,23.100)', 'via@31.250,23.100']
Far island: ['U4.7', 'C35.1', 'TP3.1', 'F.Cu (71.680,42.400)-(70.900,42.400)', 'F.Cu (70.900,44.000)-(70.900,42.400)', 'F.Cu (77.750,57.726)-(78.400,57.726)', 'F.Cu (72.000,36.000)-(73.300,36.000)', 'F.Cu (71.680,44.000)-(70.900,44.000)', 'F.Cu (71.680,44.000)-(71.680,42.400)', 'F.Cu (77.750,56.600)-(77.750,57.726)', 'via@70.900,42.400', 'via@78.400,57.726', 'via@73.300,36.000', 'B.Cu (71.580,57.730)-(75.500,57.730)', 'B.Cu (70.900,45.500)-(68.140,45.500)', 'B.Cu (78.400,59.150)-(78.400,57.730)', 'B.Cu (68.140,54.400)-(71.580,54.400)', 'B.Cu (70.900,42.400)-(70.900,45.500)', 'B.Cu (68.140,45.500)-(68.140,54.400)', 'B.Cu (73.300,36.000)-(73.300,42.400)', 'B.Cu (75.500,57.730)-(75.500,59.150)', 'B.Cu (71.580,54.400)-(71.580,57.730)', 'B.Cu (75.500,59.150)-(78.400,59.150)', 'B.Cu (73.300,42.400)-(70.900,42.400)']

## Straight chord

F.Cu 0.18 mm [31.397, 27.128] → [68.06, 45.46], length 40.990704 mm. Crosses SiP body: True. VDD2 via {'via_xy': [61.3, 42.0], 'via_radius_mm': 0.4, 'centerline_distance_mm': 0.0715, 'edge_clearance_mm': -0.4185}. Not used.

## Lanes checked

The four locked skirts occupy x=44.25 and x=44.60 from about y=26.5 to y=63.2, and a same-centerline stack is forbidden on every layer. East of them, x=44.93 hits P0.06 (45.150, 36.000) at -0.12 mm. West of them, x=43.92 is inside the fab body. That slot is closed, but it is not the only way out: the through-via can leave north on In1.Cu, run at y=19.20/20.05/19.55 (all north of the skirt y=20.80 cap), and drop south at x=57.20, which is east of every locked segment. F.Cu and B.Cu copies of that polyline are blocked by VDD_GPIO, DEC0, P0.15, and VDD2 tracks. In2.Cu clears the same polyline; only In1.Cu was placed.

x=44.93 remeasure: {'via_xy': [45.15, 36.0], 'radius_mm': 0.25, 'width_mm': 0.5, 'centerline_x': 44.93, 'edge_clearance_mm': -0.12}
x=43.92 inside body: True

Per-layer probe of x=44.93 from y=27.40 to y=50.00 (stops before the y=60.40 east caps so the via hit is visible):

- In1.Cu: ok=False foreign=-0.18 vs {'net': 'P0.16', 'item': 'trk (45.55,27.40)-(44.60,27.40)'} hole=-0.02 vs via P0.06 @45.150,36.000
- In2.Cu: ok=False foreign=-0.18 vs {'net': 'P0.17', 'item': 'trk (45.55,27.40)-(44.60,27.40)'} hole=-0.02 vs via P0.06 @45.150,36.000
- F.Cu: ok=False foreign=-0.12 vs {'net': 'P0.06', 'item': 'via@45.150,36.000'} hole=-0.02 vs via P0.06 @45.150,36.000
- B.Cu: ok=False foreign=-0.12 vs {'net': 'P0.06', 'item': 'via@45.150,36.000'} hole=-0.02 vs via P0.06 @45.150,36.000

## Free space from via (31.25, 23.10)

The via sits at x=31.25, inside the fab body's x-range (28–44), so a straight south run enters the body at y=26.75. Straight north dies on the COEX0 via (31.110, 22.000). East along y=23.10 dies on the P0.25 via (33.250, 23.100) before the skirt. West dies on the SIM_IO via (30.250, 23.100). F.Cu and B.Cu therefore do not reach the far island in a straight shot. The kept route leaves northeast, then runs north of the skirts.

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, P0.19, and P0.20, layers not exempt. A same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds is a fail even on another layer. Endpoint-only touches are not crossings. A sample in the interior of a locked segment is a crossing.
Crossings: **0**. Min centerline to a locked skirt: **0.75 mm** vs {'net': 'P0.16', 'segment': [[40.7, 20.8], [45.55, 20.8]]}.

Per new segment, nearest locked skirt:

- (31.25, 23.1) → (33.6, 22.4) crossed=False nearest P0.20 [[36.45, 20.8], [36.45, 26.5]] center 2.85 mm (edge 2.67 mm), 50 samples
- (33.6, 22.4) → (33.6, 19.2) crossed=False nearest P0.20 [[36.2, 20.8], [36.45, 20.8]] center 2.6 mm (edge 2.42 mm), 64 samples
- (33.6, 19.2) → (39.4, 19.2) crossed=False nearest P0.20 [[36.2, 20.8], [36.45, 20.8]] center 1.6 mm (edge 1.42 mm), 116 samples
- (39.4, 19.2) → (39.4, 20.05) crossed=False nearest P0.16 [[40.7, 20.8], [45.55, 20.8]] center 1.5008 mm (edge 1.3208 mm), 18 samples
- (39.4, 20.05) → (56.0, 20.05) crossed=False nearest P0.16 [[40.7, 20.8], [45.55, 20.8]] center 0.75 mm (edge 0.57 mm), 333 samples
- (56.0, 20.05) → (56.0, 19.55) crossed=False nearest P0.16 [[40.7, 20.8], [45.55, 20.8]] center 10.4769 mm (edge 10.2969 mm), 11 samples
- (56.0, 19.55) → (57.2, 19.55) crossed=False nearest P0.16 [[40.7, 20.8], [45.55, 20.8]] center 10.5245 mm (edge 10.3445 mm), 25 samples
- (57.2, 19.55) → (57.2, 36.0) crossed=False nearest P0.16 [[40.7, 20.8], [45.55, 20.8]] center 11.65 mm (edge 11.47 mm), 329 samples
- (57.2, 36.0) → (73.3, 36.0) crossed=False nearest P0.16 [[44.6, 27.4], [44.6, 60.4]] center 12.6 mm (edge 12.42 mm), 322 samples

## Attempt

In1.Cu 0.18 mm, no new via. Kept.

- (31.25, 23.1) → (33.6, 22.4) In1.Cu
- (33.6, 22.4) → (33.6, 19.2) In1.Cu
- (33.6, 19.2) → (39.4, 19.2) In1.Cu
- (39.4, 19.2) → (39.4, 20.05) In1.Cu
- (39.4, 20.05) → (56.0, 20.05) In1.Cu
- (56.0, 20.05) → (56.0, 19.55) In1.Cu
- (56.0, 19.55) → (57.2, 19.55) In1.Cu
- (57.2, 19.55) → (57.2, 36.0) In1.Cu
- (57.2, 36.0) → (73.3, 36.0) In1.Cu

North bypass: leave the through-via northeast to clear P0.25, run north at x=33.60 (west of SWDCLK/P0.22), east at y=19.20 under VDD_GPIO (40.170, 19.126), south to y=20.05 (still 0.75 mm north of the P0.16/P0.20 y=20.80 cap), east to x=56.00, north to y=19.55 to clear ENABLE (56.500, 20.300), east to x=57.20, south to y=36.00, east onto SIM_CLK via (73.30, 36.00). x>24.2. No header or U1 move. Fanout vias not moved. Skirts not ripped and not stacked. No other net.

## Clearance by segment

- (31.25, 23.1)–(33.6, 22.4) ok=True foreign=0.181 vs {'net': 'P0.25', 'item': 'via@33.250,23.100'} power=None vs None hole=0.331 vs via P0.25 @33.250,23.100 why=None
- (33.6, 22.4)–(33.6, 19.2) ok=True foreign=0.21 vs {'net': 'SWDCLK', 'item': 'via@34.200,19.800'} power=None vs None hole=0.36 vs via SWDCLK @34.200,19.800 why=None
- (33.6, 19.2)–(39.4, 19.2) ok=True foreign=0.21 vs {'net': 'SWDCLK', 'item': 'via@34.200,19.800'} power=0.2836 vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'} hole=0.36 vs via SWDCLK @34.200,19.800 why=None
- (39.4, 19.2)–(39.4, 20.05) ok=True foreign=0.2836 vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'} power=0.2836 vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'} hole=0.4836 vs via VDD_GPIO @40.170,19.126 why=None
- (39.4, 20.05)–(56.0, 20.05) ok=True foreign=0.169 vs {'net': 'ENABLE', 'item': 'via@56.500,20.300'} power=0.4342 vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'} hole=0.319 vs via ENABLE @56.500,20.300 why=None
- (56.0, 20.05)–(56.0, 19.55) ok=True foreign=0.169 vs {'net': 'ENABLE', 'item': 'via@56.500,20.300'} power=1.4001 vs {'net': 'VDD2', 'item': 'via@54.500,21.200'} hole=0.319 vs via ENABLE @56.500,20.300 why=None
- (56.0, 19.55)–(57.2, 19.55) ok=True foreign=0.36 vs {'net': 'ENABLE', 'item': 'via@56.500,20.300'} power=1.71 vs {'net': 'VDD_nRF', 'item': 'via@56.087,17.350'} hole=0.51 vs via ENABLE @56.500,20.300 why=None
- (57.2, 19.55)–(57.2, 36.0) ok=True foreign=0.31 vs {'net': 'ENABLE', 'item': 'via@56.500,23.800'} power=0.41 vs {'net': 'VDD2', 'item': 'via@58.000,30.950'} hole=0.46 vs via ENABLE @56.500,23.800 why=None
- (57.2, 36.0)–(73.3, 36.0) ok=True foreign=0.6358 vs {'net': 'VDD2', 'item': 'via@59.700,37.126'} power=0.6358 vs {'net': 'VDD2', 'item': 'via@59.700,37.126'} hole=0.8358 vs via VDD2 @59.700,37.126 why=None

## Gate

KEEP. In1.Cu north bypass, 9 new segments, no new via. Skirt slot (x=44.25 / x=44.60) was not the only way and was not used. Whole-segment crossing test: 0 crossings (min center to a locked skirt 0.75 mm). SIM_CLK opens 1→0. Unconnected 56→55. Foreign 0.169 mm vs {'net': 'ENABLE', 'item': 'via@56.500,20.300'}. POWER 0.2836 mm vs {'net': 'VDD_GPIO', 'item': 'via@40.170,19.126'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Four skirts not ripped or stacked. No other net.

## DRC

| | unconnected | SIM_CLK | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 56 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 55 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. No new via. No other net. No Gerbers. No git commit.

