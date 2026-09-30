# PASS30BF_SUMMARY — P0.00

**Timestamp:** 2026-09-30 17:28 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.00
**Git HEAD:** `b60ffcb6ad9ac026ee3b82eadcfdd6fd9ef8adba`
**PCB blob at start:** `625ef9d7ba5150f27306905b448cc93eee4f59d9`
**PCB blob at end:** `1689715203e755d4422b71fb29202c387b9c7889`
**Expected tip/blob matched:** True / True
**Ends already one island:** False
**Start via (39.75, 41.10) on U1.95 island:** True
**Start via:** {'xy': [39.75, 41.1], 'width_mm': 0.6, 'radius_mm': 0.3, 'drill_mm': 0.3, 'through': True, 'nm': [39750000, 41100000]}
**Far island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far island F.Cu-only:** False
**Far through-vias:** [{'name': 'via@80.140,19.126', 'xy': [80.14, 19.125833], 'width_mm': 0.6, 'drill_mm': 0.3, 'nm': [80140000, 19125833]}]
**U1 island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Pad-edge (U1.95 to F.Cu x=79.49 segment):** 43.297995 mm (census 43.298)
**New via:** no
**Joined:** existing through-via (80.14, 19.125833) on In1.Cu
**New segments:** 9 (limit 10)
**Crossing test failed:** False
**Whole-segment crossing count:** 0
**Min foreign clearance:** 0.16 mm vs {'net': 'MIPI_VIO', 'item': 'via@24.650,24.400'}
**Min POWER/VIN clearance:** 0.2457 mm vs {'net': 'VDD2', 'item': 'via@68.137,16.874'}
**Min hole clearance:** 0.31 mm vs via MIPI_VIO @24.650,24.400
**P0.00 opens:** 1 → 0
**Unconnected:** 54 → 53
**GND islands:** 12 → 12 (waived)

## Islands

U1 island: ['J12.1', 'U1.95', 'F.Cu (39.750,41.100)-(6.000,76.000)', 'F.Cu (39.750,37.250)-(39.750,41.100)', 'via@39.750,41.100']
Far island: ['R10.1', 'F.Cu (79.490,18.000)-(79.490,19.126)', 'F.Cu (79.490,19.126)-(80.140,19.126)', 'via@80.140,19.126']

## Straight chord

F.Cu 0.18 mm [39.897, 36.872] → [79.408, 19.163], length 43.298127 mm. Crosses SiP body: True. VDD1 {'track': [50.68, 35.0, 50.68, 31.0], 'width_mm': 0.4, 'proper_cross': True, 'edge_clearance_mm': -0.29000000000000004}. Not used.

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, P0.19, P0.20, the SIM_CLK In1 run, and the SIM_RST run (F.Cu neck plus In1). Layers are not exempt. A same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds is a fail. Endpoint-only touches are not crossings.
Crossings: **0**. Min centerline to a locked run: **1.0 mm** vs {'net': 'SIM_RST', 'segment': [[32.75, 25.5], [26.2, 25.5]]}.

- (39.75, 41.1) → (39.75, 37.4) crossed=False nearest P0.19 [[44.25, 39.1], [42.8, 39.9]] center 3.05 mm (edge 2.87 mm), 75 samples
- (39.75, 37.4) → (25.2, 37.4) crossed=False nearest P0.19 [[44.25, 39.1], [42.8, 39.9]] center 3.9437 mm (edge 3.7637 mm), 292 samples
- (25.2, 37.4) → (25.2, 23.5) crossed=False nearest SIM_RST [[32.75, 25.5], [26.2, 25.5]] center 1.0 mm (edge 0.82 mm), 278 samples
- (25.2, 23.5) → (25.0, 23.5) crossed=False nearest SIM_RST [[26.2, 25.5], [26.2, 17.6]] center 1.0 mm (edge 0.82 mm), 4 samples
- (25.0, 23.5) → (25.0, 15.2) crossed=False nearest SIM_RST [[26.2, 25.5], [26.2, 17.6]] center 1.2 mm (edge 1.02 mm), 167 samples
- (25.0, 15.2) → (68.7, 15.2) crossed=False nearest SIM_RST [[26.2, 25.5], [26.2, 17.6]] center 2.4 mm (edge 2.22 mm), 875 samples
- (68.7, 15.2) → (68.7, 16.4) crossed=False nearest SIM_RST [[55.3, 18.5], [68.0, 18.5]] center 2.2136 mm (edge 2.0336 mm), 24 samples
- (68.7, 16.4) → (80.14, 16.4) crossed=False nearest SIM_RST [[55.3, 18.5], [68.0, 18.5]] center 2.2136 mm (edge 2.0336 mm), 229 samples
- (80.14, 16.4) → (80.14, 19.125833) crossed=False nearest SIM_RST [[55.3, 18.5], [68.0, 18.5]] center 12.14 mm (edge 11.96 mm), 55 samples

## Attempt

In1.Cu only, 9 segments, no new via. Starts at existing through-via (39.75, 41.10) and lands on existing through-via (80.14, 19.125833). Kept.

- (39.75, 41.1) → (39.75, 37.4) In1.Cu 0.18 mm
- (39.75, 37.4) → (25.2, 37.4) In1.Cu 0.18 mm
- (25.2, 37.4) → (25.2, 23.5) In1.Cu 0.18 mm
- (25.2, 23.5) → (25.0, 23.5) In1.Cu 0.18 mm
- (25.0, 23.5) → (25.0, 15.2) In1.Cu 0.18 mm
- (25.0, 15.2) → (68.7, 15.2) In1.Cu 0.18 mm
- (68.7, 15.2) → (68.7, 16.4) In1.Cu 0.18 mm
- (68.7, 16.4) → (80.14, 16.4) In1.Cu 0.18 mm
- (80.14, 16.4) → (80.14, 19.125833) In1.Cu 0.18 mm

West of the SiP on In1 at x=25.20 then x=25.00 (east of the RF keepout x=24.2), north at y=15.20 (north of SIM_RST y=17.60 and of SIM_CLK), east to x=80.14, south onto the existing far through-via. x=44.25 and x=44.60 not used. Sealed y=44.60 pocket not entered. SIM_RST and SIM_CLK centerlines not stacked. No header or U1 move. No other net.

## Clearance by segment

- In1.Cu (39.75, 41.1)–(39.75, 37.4) ok=True foreign=0.61 vs {'net': 'COEX0', 'item': 'via@38.750,41.100'} power=None vs None hole=0.76 vs via COEX0 @38.750,41.100 why=None
- In1.Cu (39.75, 37.4)–(25.2, 37.4) ok=True foreign=2.01 vs {'net': 'GND', 'item': 'via@39.000,35.000'} power=2.11 vs {'net': 'VDD_GPIO', 'item': 'via@28.500,40.000'} hole=2.16 vs via GND @39.000,35.000 why=None
- In1.Cu (25.2, 37.4)–(25.2, 23.5) ok=True foreign=0.16 vs {'net': 'MIPI_VIO', 'item': 'via@24.650,24.400'} power=3.7112 vs {'net': 'VDD_GPIO', 'item': 'via@28.500,40.000'} hole=0.31 vs via MIPI_VIO @24.650,24.400 why=None
- In1.Cu (25.2, 23.5)–(25.0, 23.5) ok=True foreign=0.1757 vs {'net': 'MAGPIO1', 'item': 'via@25.600,23.100'} power=None vs None hole=0.3257 vs via MAGPIO1 @25.600,23.100 why=None
- In1.Cu (25.0, 23.5)–(25.0, 15.2) ok=True foreign=0.21 vs {'net': 'MAGPIO1', 'item': 'via@25.600,23.100'} power=None vs None hole=0.36 vs via MAGPIO1 @25.600,23.100 why=None
- In1.Cu (25.0, 15.2)–(68.7, 15.2) ok=True foreign=0.21 vs {'net': 'nRESET', 'item': 'via@45.680,15.800'} power=0.61 vs {'net': 'VDD2_MID', 'item': 'via@67.213,16.300'} hole=0.36 vs via nRESET @45.680,15.800 why=None
- In1.Cu (68.7, 15.2)–(68.7, 16.4) ok=True foreign=0.21 vs {'net': 'P0.15', 'item': 'via@69.300,15.350'} power=0.2457 vs {'net': 'VDD2', 'item': 'via@68.137,16.874'} hole=0.36 vs via P0.15 @69.300,15.350 why=None
- In1.Cu (68.7, 16.4)–(80.14, 16.4) ok=True foreign=0.2457 vs {'net': 'VDD2', 'item': 'via@68.137,16.874'} power=0.2457 vs {'net': 'VDD2', 'item': 'via@68.137,16.874'} hole=0.4457 vs via VDD2 @68.137,16.874 why=None
- In1.Cu (80.14, 16.4)–(80.14, 19.125833) ok=True foreign=None vs None power=None vs None hole=None vs None why=None

## Gate

KEEP. In1 west/north bypass, 9 new segments, no new via, from existing through-via (39.75, 41.10) onto existing through-via (80.14, 19.125833). Straight F.Cu chord not used (VDD1). Skirt slot and sealed pocket not used. Whole-segment crossings: 0. P0.00 opens 1→0. Unconnected 54→53. Foreign 0.16 mm vs {'net': 'MIPI_VIO', 'item': 'via@24.650,24.400'}. POWER 0.2457 mm vs {'net': 'VDD2', 'item': 'via@68.137,16.874'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Four skirts, SIM_CLK, and SIM_RST not ripped or stacked. No other net.

## DRC

| | unconnected | P0.00 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 54 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 53 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. SIM_CLK and SIM_RST not ripped and not stacked. Skirt slot and sealed pocket not used. No other net. No Gerbers. No git commit.

