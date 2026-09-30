# PASS30BE_SUMMARY — SIM_RST

**Timestamp:** 2026-09-30 17:18 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** SIM_RST
**Git HEAD:** `2201658b04f89bfdfeeced2907dfc9a9eb94ee8d`
**PCB blob at start:** `036e870670d173055c85ca41c994405c95fbb4e8`
**PCB blob at end:** `625ef9d7ba5150f27306905b448cc93eee4f59d9`
**Expected tip/blob matched:** True / True
**Ends already one island:** False
**Far island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far island B.Cu-only:** False
**Far through-vias:** [{'name': 'via@79.376,58.050', 'xy': [79.376, 58.05]}, {'name': 'via@79.300,36.000', 'xy': [79.3, 36.0]}, {'name': 'via@78.000,36.000', 'xy': [78.0, 36.0]}, {'name': 'via@79.376,57.250', 'xy': [79.376, 57.25]}, {'name': 'via@71.030,49.126', 'xy': [71.03, 49.126]}]
**U1 island layers:** ['F.Cu']
**Pad-edge (U1.43 to B.Cu x=71.68 track):** 42.124496 mm (census 42.124)
**P0.25 flank x=32.71 copper clearance:** 0.15 mm (stored x nm 32710000; under 0.15: False)
**P0.25 x decision:** rejected as a through-run. Clearance is exactly 0.150 mm, not under the gate, but the north continuation crosses SIM_CLK In1 at (32.71, 22.665). Kept route does not pass that via.
**New via:** yes (32.75, 25.50) 0.50/0.30 through
**New segments:** 9 (limit 10)
**Crossing test failed:** False
**Min foreign clearance:** 0.16 mm vs {'net': 'COEX0', 'item': 'B.Cu trk (32.25,22.00)-(32.25,30.50)'}
**Min POWER/VIN clearance:** 0.2358 mm vs {'net': 'VDD1', 'item': 'via@49.438,16.874'}
**Min hole clearance:** 0.31 mm vs via MAGPIO2 @26.750,23.100
**SIM_RST opens:** 1 → 0
**Unconnected:** 55 → 54
**GND islands:** 12 → 12 (waived)

## Islands

U1 island: ['U1.43']
Far island: ['TP4.1', 'U4.6', 'C36.1', 'F.Cu (78.000,36.000)-(79.300,36.000)', 'F.Cu (78.250,56.600)-(78.250,57.050)', 'F.Cu (71.030,48.000)-(71.030,49.126)', 'F.Cu (71.680,48.000)-(71.030,48.000)', 'F.Cu (78.250,57.050)-(79.376,57.050)', 'F.Cu (79.376,57.050)-(79.376,58.050)', 'via@79.376,58.050', 'via@79.300,36.000', 'via@78.000,36.000', 'via@79.376,57.250', 'via@71.030,49.126', 'B.Cu (71.680,43.800)-(71.680,48.000)', 'B.Cu (71.680,48.000)-(71.680,43.800)', 'B.Cu (79.376,57.250)-(79.376,58.050)', 'B.Cu (71.680,43.800)-(78.250,43.800)', 'B.Cu (71.680,43.800)-(78.000,43.800)', 'B.Cu (78.250,56.600)-(74.000,56.600)', 'B.Cu (71.680,43.800)-(78.000,43.800)', 'B.Cu (78.000,43.800)-(78.000,36.000)', 'B.Cu (78.250,43.800)-(71.680,43.800)', 'B.Cu (71.680,48.000)-(71.680,43.800)', 'B.Cu (71.030,49.126)-(71.680,48.000)', 'B.Cu (74.000,43.800)-(71.680,43.800)', 'B.Cu (71.680,48.000)-(71.680,43.800)', 'B.Cu (79.376,57.250)-(78.250,56.600)', 'B.Cu (74.000,56.600)-(74.000,43.800)', 'B.Cu (78.000,36.000)-(78.000,43.800)', 'B.Cu (78.000,43.800)-(78.000,36.000)']

## Straight chord

F.Cu 0.18 mm [32.897, 27.128] → [71.597, 43.764], length 42.124179 mm. Crosses SiP body: True. VDD1 {'track': [50.68, 35.0, 50.68, 31.0], 'width_mm': 0.4, 'proper_cross': True, 'edge_clearance_mm': -0.29000000000000004}. Not used.

## P0.25 flank

Via: {'xy': [33.25, 23.1], 'width_mm': 0.6, 'radius_mm': 0.3, 'drill_mm': 0.3, 'pos_nm': [33250000, 23100000]}

- x=32.71 stored_nm=32710000 copper=0.150000 mm hole=0.300000 mm under_0.15=False
- x=32.70 stored_nm=32700000 copper=0.160000 mm hole=0.310000 mm under_0.15=False
- x=32.69 stored_nm=32689999 copper=0.170001 mm hole=0.320000 mm under_0.15=False

## Whole-segment crossing test

segment-vs-segment interior intersection plus 0.05 mm samples, against P0.16, P0.17, P0.19, P0.20, and the SIM_CLK In1 run. Layers are not exempt. A same-centerline stack on x=44.25, x=44.60, or the y=63.20 eastbounds is a fail. Endpoint-only touches are not crossings.
Crossings: **0**. Min centerline to a locked run: **0.6 mm** vs {'net': 'SIM_CLK', 'segment': [[57.2, 36.0], [73.3, 36.0]]}.

- (32.71, 26.4) → (32.75, 25.5) crossed=False nearest SIM_CLK [[31.25, 23.1], [33.6, 22.4]] center 2.7283 mm (edge 2.5483 mm), 19 samples
- (32.75, 25.5) → (26.2, 25.5) crossed=False nearest SIM_CLK [[31.25, 23.1], [33.6, 22.4]] center 2.4 mm (edge 2.22 mm), 132 samples
- (26.2, 25.5) → (26.2, 17.6) crossed=False nearest SIM_CLK [[31.25, 23.1], [33.6, 22.4]] center 5.05 mm (edge 4.87 mm), 158 samples
- (26.2, 17.6) → (55.3, 17.6) crossed=False nearest SIM_CLK [[33.6, 22.4], [33.6, 19.2]] center 1.6 mm (edge 1.42 mm), 582 samples
- (55.3, 17.6) → (55.3, 18.5) crossed=False nearest SIM_CLK [[56.0, 20.05], [56.0, 19.55]] center 1.2619 mm (edge 1.0819 mm), 18 samples
- (55.3, 18.5) → (68.0, 18.5) crossed=False nearest SIM_CLK [[56.0, 20.05], [56.0, 19.55]] center 1.05 mm (edge 0.87 mm), 255 samples
- (68.0, 18.5) → (68.0, 35.4) crossed=False nearest SIM_CLK [[57.2, 36.0], [73.3, 36.0]] center 0.6 mm (edge 0.42 mm), 338 samples
- (68.0, 35.4) → (78.0, 35.4) crossed=False nearest SIM_CLK [[57.2, 36.0], [73.3, 36.0]] center 0.6 mm (edge 0.42 mm), 201 samples
- (78.0, 35.4) → (78.0, 36.0) crossed=False nearest SIM_CLK [[57.2, 36.0], [73.3, 36.0]] center 4.7 mm (edge 4.52 mm), 13 samples

## Attempt

F.Cu neck plus In1.Cu, one 0.50/0.30 through-via. Kept.

- via (32.75, 25.50) drill 0.30 diameter 0.50 through
- (32.71, 26.4) → (32.75, 25.5) F.Cu 0.18 mm
- (32.75, 25.5) → (26.2, 25.5) In1.Cu 0.18 mm
- (26.2, 25.5) → (26.2, 17.6) In1.Cu 0.18 mm
- (26.2, 17.6) → (55.3, 17.6) In1.Cu 0.18 mm
- (55.3, 17.6) → (55.3, 18.5) In1.Cu 0.18 mm
- (55.3, 18.5) → (68.0, 18.5) In1.Cu 0.18 mm
- (68.0, 18.5) → (68.0, 35.4) In1.Cu 0.18 mm
- (68.0, 35.4) → (78.0, 35.4) In1.Cu 0.18 mm
- (78.0, 35.4) → (78.0, 36.0) In1.Cu 0.18 mm

West of the SiP on In1 at x=26.20 (east of the RF keepout x=24.2), north at y=17.60 (north of the skirt cap y=20.80 and of the SIM_CLK run), east to x=68.00, south to y=35.40 (0.60 mm centerline off the SIM_CLK y=36.00 run), east onto through-via (78.00, 36.00). x=44.25 and x=44.60 not used. Sealed y=44.60 pocket not entered. No header or U1 move. Skirts not ripped and not stacked. SIM_CLK run not ripped and not stacked. No other net.

## Clearance by segment

- via (32.75, 25.50) 0.50 mm ok=True foreign=0.16 vs {'net': 'COEX0', 'item': 'B.Cu trk (32.25,22.00)-(32.25,30.50)'} power=9.1319 hole=2.1515 vs via P0.25 @33.250,23.100
- F.Cu (32.71, 26.4)–(32.75, 25.5) ok=True foreign=0.22 vs {'net': 'GND', 'item': 'pad U1.44'} power=None vs None hole=2.2115 vs via P0.25 @33.250,23.100 why=None
- In1.Cu (32.75, 25.5)–(26.2, 25.5) ok=True foreign=1.5107 vs {'net': 'MIPI_VIO', 'item': 'via@24.650,24.400'} power=None vs None hole=1.6607 vs via MIPI_VIO @24.650,24.400 why=None
- In1.Cu (26.2, 25.5)–(26.2, 17.6) ok=True foreign=0.16 vs {'net': 'MAGPIO2', 'item': 'via@26.750,23.100'} power=None vs None hole=0.31 vs via MAGPIO2 @26.750,23.100 why=None
- In1.Cu (26.2, 17.6)–(55.3, 17.6) ok=True foreign=0.2358 vs {'net': 'VDD1', 'item': 'via@49.438,16.874'} power=0.2358 vs {'net': 'VDD1', 'item': 'via@49.438,16.874'} hole=0.4358 vs via VDD1 @49.438,16.874 why=None
- In1.Cu (55.3, 17.6)–(55.3, 18.5) ok=True foreign=0.3354 vs {'net': 'VDD_nRF', 'item': 'via@56.087,17.350'} power=0.3354 vs {'net': 'VDD_nRF', 'item': 'via@56.087,17.350'} hole=0.5354 vs via VDD_nRF @56.087,17.350 why=None
- In1.Cu (55.3, 18.5)–(68.0, 18.5) ok=True foreign=0.5179 vs {'net': 'VDD2', 'item': 'via@68.790,19.126'} power=0.5179 vs {'net': 'VDD2', 'item': 'via@68.790,19.126'} hole=0.7179 vs via VDD2 @68.790,19.126 why=None
- In1.Cu (68.0, 18.5)–(68.0, 35.4) ok=True foreign=0.3 vs {'net': 'VDD2', 'item': 'via@68.790,19.126'} power=0.3 vs {'net': 'VDD2', 'item': 'via@68.790,19.126'} hole=0.5 vs via VDD2 @68.790,19.126 why=None
- In1.Cu (68.0, 35.4)–(78.0, 35.4) ok=True foreign=0.21 vs {'net': 'SIM_CLK', 'item': 'via@73.300,36.000'} power=2.91 vs {'net': 'VDD_GPIO', 'item': 'via@78.000,32.000'} hole=0.36 vs via SIM_CLK @73.300,36.000 why=None
- In1.Cu (78.0, 35.4)–(78.0, 36.0) ok=True foreign=2.91 vs {'net': 'VDD_GPIO', 'item': 'via@78.000,32.000'} power=2.91 vs {'net': 'VDD_GPIO', 'item': 'via@78.000,32.000'} hole=3.11 vs via VDD_GPIO @78.000,32.000 why=None

## Gate

KEEP. F.Cu neck plus In1 west/north bypass, 9 new segments, one 0.50/0.30 through-via at (32.75, 25.50), landing on existing through-via (78.00, 36.00). x=32.71 through-run was not used (P0.25 clearance exactly 0.150 mm, but it crosses SIM_CLK). Skirt slot and sealed pocket not used. Whole-segment crossings: 0. SIM_RST opens 1→0. Unconnected 55→54. Foreign 0.16 mm vs {'net': 'COEX0', 'item': 'B.Cu trk (32.25,22.00)-(32.25,30.50)'}. POWER 0.2358 mm vs {'net': 'VDD1', 'item': 'via@49.438,16.874'}. short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12→12 (waived). Other non-GND gained: none. Four skirts and the SIM_CLK run not ripped or stacked. No other net.

## DRC

| | unconnected | SIM_RST | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 55 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 54 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |

No other non-GND net gained an open.
P0.16 / P0.17 / P0.19 / P0.20 skirts not ripped and not stacked. SIM_CLK In1 run not ripped and not stacked. No other net. No Gerbers. No git commit.

