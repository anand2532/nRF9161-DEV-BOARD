# PASS30BS_CENSUS - read-only, 37 non-GND opens

Tip 45743c9, blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda (start and end identical). No board writes. Source: DRC_PASS30BP_REVERT.json (49 unconnected, 12 GND).

Method: live union-find islands per net; pad-edge is the min copper-to-copper distance between islands; 0.1 mm grid Dijkstra per layer (In1/In2/B.Cu) with 0.33 same-layer locked spacing, foreign 0.15/POWER 0.20 (+0.03), RF keepout + x>=26, pocket blocked, cross-layer locked-plan cells penalised; exit-via candidates need all-layer clearance and >=0.4 mm from every F.Cu pad. Segment counts are grid estimates (+/-1-2).

| # | net | end A (xy) | end B (xy) | island pads A | island pads B | pad-edge mm | class | note |
|---|---|---|---|---|---|---|---|---|
| 0 | MAGPIO1 | Track [MAGPIO1] on F.Cu, length 2.4000 mm (28.0,28.0) | PTH pad 2 [MAGPIO1] of J14 (104.0,49.27) | U1.54 | J14.2 | 78.27 | C | MAGPIO1 U1.54 west edge: RF keepout/x>=26 + SIM_RST x=26.2/P0.00 x=25.0-25.2 west runs; no inner path |
| 1 | MIPI_VIO | Pad 57 [MIPI_VIO] of U1 on F.Cu (28.0,29.5) | PTH pad 4 [MIPI_VIO] of J14 (104.0,51.81) | U1.57 | J14.4 | 78.557 | C | MIPI_VIO U1.57 west edge: same |
| 2 | P0.10 | Pad 18 [P0.10] of U1 on F.Cu (44.0,28.5) | PTH pad 11 [P0.10] of J12 (31.4,76.0) | U1.18 | J12.11 | 48.143 | B | J12.11 boxed: P0.05 In1 y=74.70 (N), P0.09 In1 y=77.20 (S); J12.10/J12.12 sides |
| 3 | P0.10 | Track [P0.10] on F.Cu, length 3.0000 mm (44.0,28.5) | PTH pad 1 [P0.10] of J16 (108.0,8.0) | U1.18 | J16.1 | 63.203 | D | P0.10 J16.1 63.2 (DNR); geometry In2 ~5 segs |
| 4 | P0.22 | Track [P0.22] on B.Cu, length 1.6000 mm (64.0,5.2) | Track [P0.22] on F.Cu, length 3.3000 mm (109.2,32.5) | J8.6, U1.38 | J10.2, J13.7 | 51.605 | D | P0.22 J8.6/U1.38 island <-> J10.2/J13.7 island 51.6; In1/In2 ~3 segs |
| 5 | P0.17 | PTH pad 1 [P0.17] of J17 (108.0,26.0) | Track [P0.17] on In2.Cu, length 5.9000 mm (45.55,21.5) | J17.1 | J18.5, J13.2, U1.28 | 61.526 | D | P0.17 J17.1 <-> skirt island 61.5; In1/In2 ~4 segs (attaches to locked skirt island) |
| 6 | P0.31 | Pad 89 [P0.31] of U1 on F.Cu (36.75,37.25) | Track [P0.31] on F.Cu, length 28.4036 mm (102.6,75.5) | U1.89 | J13.16, J11.2 | 66.788 | C | P0.31 U1.89 south: ~12 segs + via (>10) |
| 7 | P0.26 | Track [P0.26] on F.Cu, length 3.8500 mm (33.75,37.25) | PTH pad 11 [P0.26] of J13 (89.4,76.0) | U1.83 | J13.11 | 64.538 | A | P0.26 U1.83 (existing island via) -> J13.11; In2 ~10 segs, ~114 mm, south-pad exit |
| 8 | MIPI_SCLK | PTH pad 5 [MIPI_SCLK] of J14 (104.0,53.08) | Pad 58 [MIPI_SCLK] of U1 on F.Cu (28.0,30.0) | J14.5 | U1.58 | 78.777 | C | MIPI_SCLK U1.58 west: In2 ~14 segs (>10) |
| 9 | P0.05 | Track [P0.05] on In1.Cu, length 36.3000 mm (57.05,38.4) | PTH pad 3 [P0.05] of J9 (116.0,13.08) | J12.6, U1.2 | J9.3 | 63.218 | D | P0.05 J9.3 63.2 (DNR); In1 ~9 segs, ~125 mm |
| 10 | P0.09 | Track [P0.09] on In1.Cu, length 20.4800 mm (59.4,40.22) | PTH pad 4 [P0.09] of J16 (108.0,15.62) | J12.10, U1.16 | J16.4 | 53.531 | D | P0.09 J16.4 53.5 (DNR); In1 ~6 segs |
| 11 | P0.27 | Pad 84 [P0.27] of U1 on F.Cu (34.25,37.25) | PTH pad 12 [P0.27] of J13 (91.94,76.0) | U1.84 | J13.12 | 68.496 | C | P0.27 U1.84 south: 10 segs + exit via = 11 (>10) |
| 12 | P0.03 | Track [P0.03] on F.Cu, length 37.1500 mm (41.75,74.4) | Track [P0.03] on F.Cu, length 1.1258 mm (97.49,18.0) | J12.4, U1.99 | R13.1 | 58.373 | C | P0.03 U1.99: ~11 segs (>10) |
| 13 | P0.07 | Track [P0.07] on In2.Cu, length 32.1000 mm (63.1,37.9) | PTH pad 2 [P0.07] of J9 (116.0,10.54) | J12.8, U1.4 | J9.2 | 58.617 | D | P0.07 J9.2 58.6 (DNR); In2 ~5 segs |
| 14 | P0.01 | Track [P0.01] on F.Cu, length 6.0000 mm (62.0,74.5) | Pad 96 [P0.01] of U1 on F.Cu (40.25,37.25) | J12.2, R11.1 | U1.96 | 42.685 | C | P0.01 U1.96 south: no legal exit-via spot (P0.00 In1 y=37.40 loop) |
| 15 | P0.30 | Track [P0.30] on F.Cu, length 11.2000 mm (101.2,46.4) | Track [P0.30] on F.Cu, length 3.8500 mm (36.25,37.25) | J13.15, J11.1 | U1.88 | 64.776 | C | P0.30 U1.88 south: ~11 segs (>10) |
| 16 | MAGPIO2 | Pad 53 [MAGPIO2] of U1 on F.Cu (28.0,27.5) | PTH pad 3 [MAGPIO2] of J14 (104.0,50.54) | U1.53 | J14.3 | 78.766 | C | MAGPIO2 U1.53 west: In2 needs ~13 segs (>10) |
| 17 | P0.18 | Track [P0.18] on B.Cu, length 10.8000 mm (50.7,72.8) | Pad 29 [P0.18] of U1 on F.Cu (39.75,26.75) | J18.6, J13.3 | U1.29 | 35.912 | C | P0.18 U1.29 north: ~15 segs, exit via only inside courtyard |
| 18 | P0.18 | Track [P0.18] on B.Cu, length 18.3800 mm (69.08,72.8) | PTH pad 2 [P0.18] of J17 (108.0,28.54) | J18.6, J13.3 | J17.2 | 57.998 | D | P0.18 J13.3/J18.6 island <-> J17.2 58.0; In1 ~3 segs |
| 19 | P0.25 | Pad 42 [P0.25] of U1 on F.Cu (33.25,26.75) | PTH pad 10 [P0.25] of J13 (86.86,76.0) | U1.42 | J13.10 | 71.798 | A | P0.25 U1.42 (existing via) -> J13.10; In2 ~10 segs, ~95 mm |
| 20 | SIM_1V8 | Track [SIM_1V8] on F.Cu, length 4.5000 mm (72.899999,44.1) | Pad 49 [SIM_1V8] of U1 on F.Cu (29.75,26.75) | C38.1, U4.5, C33.1, JP2.1 | U1.49 | 46.157 | C | SIM_1V8 U1.49: only exit is via-in-pad (pass30bl ruling); DNR |
| 21 | SIM_IO | Pad 48 [SIM_IO] of U1 on F.Cu (30.25,26.75) | Track [SIM_IO] on F.Cu, length 4.6000 mm (75.68,52.0) | U1.48 | U4.8, TP5.1, C37.1 | 51.625 | C | SIM_IO U1.48 north: ~13 segs, SIM_RST/SIM_CLK north band |
| 22 | MAGPIO0 | Pad 55 [MAGPIO0] of U1 on F.Cu (28.0,28.5) | PTH pad 1 [MAGPIO0] of J14 (104.0,48.0) | U1.55 | J14.1 | 77.812 | C | MAGPIO0 U1.55: no legal exit-via spot |
| 23 | COEX1 | Pad 92 [COEX1] of U1 on F.Cu (38.25,37.25) | PTH pad 2 [COEX1] of J15 (104.0,63.27) | U1.92 | J15.2 | 70.061 | C | COEX1 U1.92 south: no legal exit-via spot |
| 24 | P0.24 | PTH pad 9 [P0.24] of J13 (84.32,76.0) | PTH pad 4 [P0.24] of J10 (116.0,35.62) | J13.9 | J10.4 | 49.624 | D | P0.24 J13.9 <-> J10.4 49.6; In1/In2 ~5 segs |
| 25 | P0.24 | Pad 40 [P0.24] of U1 on F.Cu (34.25,26.75) | PTH pad 9 [P0.24] of J13 (84.32,76.0) | U1.40 | J13.9 | 69.232 | A | P0.24 U1.40 -> J13.9; new exit via (29 cands outside courtyard) + In2 ~9 segs (10 total) |
| 26 | P0.29 | Pad 87 [P0.29] of U1 on F.Cu (35.75,37.25) | PTH pad 14 [P0.29] of J13 (97.02,76.0) | U1.87 | J13.14 | 71.495 | C | P0.29 U1.87 south: 11 + via, exit via only inside courtyard |
| 27 | P0.12 | Track [P0.12] on F.Cu, length 3.0000 mm (44.0,27.5) | PTH pad 13 [P0.12] of J12 (36.48,76.0) | U1.20 | J12.13 | 48.08 | B | J12.13 boxed: P0.05 In1 y=74.70 + P0.11 In2 y=74.80 (N), P0.09 In1 y=77.20 (S) |
| 28 | P0.12 | Via [P0.12] on F.Cu - B.Cu (47.0,27.5) | PTH pad 3 [P0.12] of J16 (108.0,13.08) | U1.20 | J16.3 | 61.531 | D | P0.12 J16.3 61.5 (DNR); In2 ~4 segs |
| 29 | P0.28 | Track [P0.28] on F.Cu, length 3.8500 mm (35.25,37.25) | PTH pad 13 [P0.28] of J13 (94.48,76.0) | U1.86 | J13.13 | 67.597 | C | P0.28 U1.86 south: ~11 segs (>10) |
| 30 | P0.21 | PTH pad 6 [P0.21] of J13 (76.7,76.0) | PTH pad 1 [P0.21] of J10 (116.0,28.0) | J13.6 | J10.1 | 60.336 | D | P0.21 J13.6 <-> J10.1 60.3; In1/In2 ~4 segs |
| 31 | P0.21 | Pad 37 [P0.21] of U1 on F.Cu (35.75,26.75) | PTH pad 6 [P0.21] of J13 (76.7,76.0) | U1.37 | J13.6 | 63.05 | A | P0.21 U1.37 (existing via) -> J13.6; In2 ~10 segs, ~90 mm |
| 32 | MIPI_SDATA | Pad 59 [MIPI_SDATA] of U1 on F.Cu (28.0,30.5) | PTH pad 6 [MIPI_SDATA] of J14 (104.0,54.35) | U1.59 | J14.6 | 79.004 | C | MIPI_SDATA U1.59: no legal exit-via spot |
| 33 | P0.11 | Track [P0.11] on In2.Cu, length 4.1500 mm (49.92,28.0) | PTH pad 2 [P0.11] of J16 (108.0,10.54) | J12.12 | J16.2 | 59.498 | D | P0.11 J16.2 59.5 (DNR); In2 ~3 segs |
| 34 | P0.14 | Pad 24 [P0.14] of U1 on F.Cu (42.25,26.75) | Track [P0.14] on B.Cu, length 16.1500 mm (40.54,78.15) | U1.24 | J18.2, J12.15 | 34.291 | A | P0.14 U1.24 -> J12.15/J18.2 island; In2 4 segs + 1 exit via; ONLY courtyard-inside via spots (75 cands, 0 outside) -> needs PM courtyard waiver + DRC clean |
| 35 | P0.23 | PTH pad 8 [P0.23] of J13 (81.78,76.0) | PTH pad 3 [P0.23] of J10 (116.0,33.08) | J13.8 | J10.3 | 53.192 | D | P0.23 J13.8 <-> J10.3 53.2; In1/In2 ~3 segs |
| 36 | P0.23 | Track [P0.23] on F.Cu, length 3.6500 mm (34.75,26.75) | PTH pad 8 [P0.23] of J13 (81.78,76.0) | U1.39 | J13.8 | 67.098 | A | P0.23 U1.39 (existing via 34.75,23.1) -> J13.8; In2 ~9 segs, ~92 mm run, plan-parallel <=0.9 mm |

## Counts
A 6, B 2, C 17, D 12 (total 37).

## Class A ranked (easiest first)
1. P0.14 U1.24 -> J12.15/J18.2 island; In2 4 segs + 1 exit via; ONLY courtyard-inside via spots (75 cands, 0 outside) -> needs PM courtyard waiver + DRC clean
2. P0.23 U1.39 (existing via 34.75,23.1) -> J13.8; In2 ~9 segs, ~92 mm run, plan-parallel <=0.9 mm
3. P0.24 U1.40 -> J13.9; new exit via (29 cands outside courtyard) + In2 ~9 segs (10 total)
4. P0.21 U1.37 (existing via) -> J13.6; In2 ~10 segs, ~90 mm
5. P0.25 U1.42 (existing via) -> J13.10; In2 ~10 segs, ~95 mm
6. P0.26 U1.83 (existing island via) -> J13.11; In2 ~10 segs, ~114 mm, south-pad exit

Note: A2-A6 all target J13 (y=76, x 76.7-89.4) from the U1 via row along In2; they share one corridor, so routing one narrows the next. Re-search after each KEEP.

## Unlocks
- **B (J12.11, J12.13):** reroute the P0.09 In1 J12 approach (y=77.20, x 30.1-55.3) to land J12.10 from the west/south-west, or move the P0.05 In1 y=74.70 run north of y~73.5 for x<40. Either opens a 0.50 band on that side. Alternative: swap P0.10/P0.12 to free J12 pins outside x 30.1-55.3 (schematic change).
- **D (header leftovers, all >36 mm):** geometrically easy (3-9 segs). The unlock is a per-pair cap waiver from PM, or moving J16/J9/J10/J17 (x 108-116) closer to J12/J13, or a schematic pin reassignment so each net needs only one header. The cheapest by segments: P0.22 (3), P0.23 J10.3 (3), P0.18 J17.2 (3), P0.11 J16.2 (3), P0.17 J17.1 (4), P0.21 J10.1 (4), P0.12 J16.3 (4).
- **C (trapped U1 pads):** west-edge MAGPIO*/MIPI_* are hemmed by the RF keepout + x>=26 and the SIM_RST x=26.20 / P0.00 x=25.0-25.2 west runs. Unlock: reroute the P0.00 west bypass, or relax x>=26, or move U1/J14 away from the keepout. South pads (P0.01, P0.26-31, COEX1) sit inside the P0.00 In1 loop (y=37.40, x=25.2..39.75); rerouting P0.00 south of U1 out of y=37.40 would free them, or allow 12-14 segments. SIM_1V8/SIM_IO/P0.18 need a via-in-pad / courtyard via waiver or a SIM_RST/SIM_CLK north-band reroute.
