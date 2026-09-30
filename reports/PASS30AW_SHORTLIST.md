# PASS30AW shortlist — U1 pads on non-GND opens

**Timestamp:** 2026-09-30 12:27 IST
**Decision:** **NO-COPPER** (measure only)
**KiCad:** 9.0.2, pcbnew, no save, no refill, no DRC file

Every non-GND net that has a U1 pad on one copper island and at least one other island. GND zone islands are ignored. Connector-to-connector opens with no U1 pad are not ranked. Pad-edge is the copper-edge distance from that U1 pad to the nearest copper on the nearest other island.

## Body

U1 `nRF9161_LGA_16.0x10.5mm`. F.Fab rect is exactly **x 28.0–44.0, y 26.75–37.25**. F.Courtyard is **x 27.75–44.25, y 26.5–37.5** (0.25 mm outside the fab). Pad centers span the fab rect. Exit tests use the fab body, not the courtyard. A pad lip outside the fab rect is not a stub. A stub is an existing track or via of that same island outside the fab rect and not only inside the RF keepout (x≤24.2 and y in 20–64).

Legal exit for a 0.18 mm track at 0.15 mm foreign clearance (need a 0.48 mm copper gap), any one of:

- sideways gap to a neighboring U1 pad ≥ 0.48 mm, or
- via-row gap ≥ 0.48 mm between the flanking fanout vias/tracks within 4.4 mm of the body (F.Cu tracks and vias; a missing flank is an open side if a 0.18 mm track still on the pad clears the remaining flank by ≥ 0.15 mm), or
- a stub of this island already outside the fab body and not only inside the keepout.

Every one of these 37 pads has sideways gaps of **0.200 mm** (0.50 mm pitch, 0.30 mm pad). None exit sideways. West exits that stop in the strip 24.2 < x < 28 are not trapped-by-keepout.

## Census — 37 U1-open pads

| mm | net | U1 pad | center | edge | class | by | nearest other copper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 34.038 | `P0.14` | U1.24 | (42.250, 26.750) | N | trapped | trapped | pad J18.2 F.Cu+B.Cu (40.623, 61.154) |
| 34.259 | `P0.16` | U1.26 | (41.250, 26.750) | N | exit | stub | pad J18.4 F.Cu+B.Cu (45.537, 61.154) |
| 34.863 | `P0.17` | U1.28 | (40.250, 26.750) | N | exit | stub | pad J18.5 F.Cu+B.Cu (47.913, 61.187) |
| 35.644 | `P0.18` | U1.29 | (39.750, 26.750) | N | trapped | trapped | pad J18.6 F.Cu+B.Cu (50.453, 61.187) |
| 36.661 | `P0.19` | U1.30 | (39.250, 26.750) | N | exit | stub | pad J18.7 F.Cu+B.Cu (52.993, 61.187) |
| 38.595 | `P0.20` | U1.35 | (36.750, 26.750) | N | exit | stub | F.Cu (55.78,62.00)-(55.78,60.90) F.Cu (55.736, 60.821) |
| 40.760 | `P0.01` | U1.96 | (40.250, 37.250) | S | trapped | trapped | B.Cu (27.20,78.50)-(62.00,78.50) B.Cu (40.364, 78.410) |
| 40.990 | `SIM_CLK` | U1.46 | (31.250, 26.750) | N | exit | stub | B.Cu (70.90,45.50)-(68.14,45.50) B.Cu (68.060, 45.460) |
| 42.124 | `SIM_RST` | U1.43 | (32.750, 26.750) | N | exit | via-row | B.Cu (71.68,43.80)-(71.68,48.00) B.Cu (71.597, 43.764) |
| 43.298 | `P0.00` | U1.95 | (39.750, 37.250) | S | exit | stub | F.Cu (79.49,18.00)-(79.49,19.13) F.Cu (79.408, 19.163) |
| 44.118 | `P0.07` | U1.4 | (44.000, 35.500) | E | exit | stub | pad J12.8 F.Cu+B.Cu (24.181, 75.250) |
| 45.733 | `P0.05` | U1.2 | (44.000, 36.500) | E | exit | stub | pad J12.6 F.Cu+B.Cu (19.101, 75.250) |
| 46.031 | `SIM_1V8` | U1.49 | (29.750, 26.750) | N | exit | via-row | F.Cu (72.90,44.10)-(72.90,48.60) F.Cu (72.714, 44.027) |
| 47.797 | `P0.09` | U1.16 | (44.000, 29.500) | E | exit | via-row | pad J12.10 F.Cu+B.Cu (29.107, 75.187) |
| 47.976 | `P0.11` | U1.19 | (44.000, 28.000) | E | exit | stub | pad J12.12 F.Cu+B.Cu (34.187, 75.187) |
| 48.028 | `P0.12` | U1.20 | (44.000, 27.500) | E | exit | stub | pad J12.13 F.Cu+B.Cu (36.563, 75.154) |
| 48.055 | `P0.10` | U1.18 | (44.000, 28.500) | E | exit | stub | pad J12.11 F.Cu+B.Cu (31.647, 75.187) |
| 51.402 | `SIM_IO` | U1.48 | (30.250, 26.750) | N | exit | stub | pad C37.1 F.Cu (75.458, 51.862) |
| 58.267 | `P0.03` | U1.99 | (41.750, 37.250) | S | exit | stub | F.Cu (97.49,18.00)-(97.49,19.13) F.Cu (97.404, 19.153) |
| 62.076 | `P0.22` | U1.38 | (35.250, 26.750) | N | exit | stub | via@79.24,71.5 F.Cu+B.Cu (79.029, 71.287) |
| 62.812 | `P0.21` | U1.37 | (35.750, 26.750) | N | exit | stub | pad J13.6 F.Cu+B.Cu (76.161, 75.343) |
| 65.303 | `P0.30` | U1.88 | (36.250, 37.250) | S | exit | stub | F.Cu (101.20,46.40)-(112.40,46.40) F.Cu (101.111, 46.388) |
| 66.628 | `P0.26` | U1.83 | (33.750, 37.250) | S | exit | stub | pad J13.11 F.Cu+B.Cu (88.743, 75.461) |
| 66.737 | `P0.31` | U1.89 | (36.750, 37.250) | S | exit | via-row | F.Cu (103.05,47.10)-(106.70,47.10) F.Cu (102.961, 47.087) |
| 66.873 | `P0.23` | U1.39 | (34.750, 26.750) | N | exit | stub | pad J13.8 F.Cu+B.Cu (81.241, 75.343) |
| 68.318 | `P0.27` | U1.84 | (34.250, 37.250) | S | exit | via-row | pad J13.12 F.Cu+B.Cu (91.202, 75.583) |
| 69.013 | `P0.24` | U1.40 | (34.250, 26.750) | N | exit | via-row | pad J13.9 F.Cu+B.Cu (83.663, 75.461) |
| 69.603 | `P0.28` | U1.86 | (35.250, 37.250) | S | exit | stub | pad J13.13 F.Cu+B.Cu (93.730, 75.599) |
| 69.936 | `COEX1` | U1.92 | (38.250, 37.250) | S | trapped | trapped | pad J15.2 F.Cu+B.Cu (103.538, 63.079) |
| 71.321 | `P0.29` | U1.87 | (35.750, 37.250) | S | trapped | trapped | pad J13.14 F.Cu+B.Cu (96.270, 75.599) |
| 71.584 | `P0.25` | U1.42 | (33.250, 26.750) | N | exit | stub | pad J13.10 F.Cu+B.Cu (86.203, 75.461) |
| 77.438 | `MAGPIO0` | U1.55 | (28.000, 28.500) | W | exit | via-row | pad J14.1 F.Cu+B.Cu (103.500, 47.500) |
| 78.007 | `MAGPIO1` | U1.54 | (28.000, 28.000) | W | exit | stub | pad J14.2 F.Cu+B.Cu (103.538, 49.079) |
| 78.293 | `MIPI_VIO` | U1.57 | (28.000, 29.500) | W | exit | stub | pad J14.4 F.Cu+B.Cu (103.538, 51.619) |
| 78.501 | `MAGPIO2` | U1.53 | (28.000, 27.500) | W | exit | stub | pad J14.3 F.Cu+B.Cu (103.538, 50.349) |
| 78.512 | `MIPI_SCLK` | U1.58 | (28.000, 30.000) | W | exit | stub | pad J14.5 F.Cu+B.Cu (103.538, 52.889) |
| 78.739 | `MIPI_SDATA` | U1.59 | (28.000, 30.500) | W | trapped | trapped | pad J14.6 F.Cu+B.Cu (103.538, 54.159) |

## Ranked exits — 31

Shortest pad-edge first. All of them, not a top five. The straight 0.18 mm chord is F.Cu between the two copper points. Clearance is to foreign copper (negative means the chord overlaps it). The chord is not a proposed route.

### 1. `P0.16` — 34.259 mm — stub

- **A:** U1.26 on F.Cu, copper (41.364, 27.150), center (41.250, 26.750)
- **B:** pad J18.4 on F.Cu+B.Cu at (45.537, 61.154)
- **Pad-edge:** 34.259 mm
- **Exit:** F.Cu (41.25, 26.75)–(40.70, 20.80) and via (40.70, 20.80) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** GND -0.349 mm (via@42.0,32.0). 5 foreign nets under 0.15 mm.

### 2. `P0.17` — 34.863 mm — stub

- **A:** U1.28 on F.Cu, copper (40.378, 27.147), center (40.250, 26.750)
- **B:** pad J18.5 on F.Cu+B.Cu at (47.913, 61.187)
- **Pad-edge:** 34.863 mm
- **Exit:** F.Cu to via (40.25, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** GND -0.277 mm (via@42.0,35.0). 4 foreign nets under 0.15 mm.

### 3. `P0.19` — 36.661 mm — stub

- **A:** U1.30 on F.Cu, copper (39.378, 27.147), center (39.250, 26.750)
- **B:** pad J18.7 on F.Cu+B.Cu at (52.993, 61.187)
- **Pad-edge:** 36.661 mm
- **Exit:** F.Cu to via (39.25, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,38.00)-(43.25,38.00)). 5 foreign nets under 0.15 mm.

### 4. `P0.20` — 38.595 mm — stub

- **A:** U1.35 on F.Cu, copper (36.878, 27.147), center (36.750, 26.750)
- **B:** F.Cu (55.78,62.00)-(55.78,60.90) on F.Cu at (55.736, 60.821)
- **Pad-edge:** 38.595 mm
- **Exit:** F.Cu (36.75, 26.75)–(36.20, 20.80) and via (36.20, 20.80) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.06 -0.373 mm (via@44.0,39.9). 8 foreign nets under 0.15 mm.

### 5. `SIM_CLK` — 40.990 mm — stub

- **A:** U1.46 on F.Cu, copper (31.397, 27.128), center (31.250, 26.750)
- **B:** B.Cu (70.90,45.50)-(68.14,45.50) on B.Cu at (68.060, 45.460)
- **Pad-edge:** 40.990 mm
- **Exit:** F.Cu to via (31.25, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD2 -0.419 mm (via@61.3,42.0). 9 foreign nets under 0.15 mm.

### 6. `SIM_RST` — 42.124 mm — via-row

- **A:** U1.43 on F.Cu, copper (32.897, 27.128), center (32.750, 26.750)
- **B:** B.Cu (71.68,43.80)-(71.68,48.00) on B.Cu at (71.597, 43.764)
- **Pad-edge:** 42.124 mm
- **Exit:** West side of the via row is open (no F.Cu flank within 4.4 mm). The only flank is P0.25 via (33.25, 23.10) r=0.30. A 0.18 mm track centered at x=32.71, still on the pad, clears that via by 0.15 mm. Sideways pad gaps are 0.200 mm, so the exit is the open via row, not the pad gap.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.68,35.00)-(50.68,31.00)). 7 foreign nets under 0.15 mm.

### 7. `P0.00` — 43.298 mm — stub

- **A:** U1.95 on F.Cu, copper (39.897, 36.872), center (39.750, 37.250)
- **B:** F.Cu (79.49,18.00)-(79.49,19.13) on F.Cu at (79.408, 19.163)
- **Pad-edge:** 43.298 mm
- **Exit:** F.Cu to via (39.75, 41.10) r=0.30 already south of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.68,35.00)-(50.68,31.00)). 9 foreign nets under 0.15 mm.

### 8. `P0.07` — 44.118 mm — stub

- **A:** U1.4 on F.Cu, copper (43.622, 35.647), center (44.000, 35.500)
- **B:** pad J12.8 on F.Cu+B.Cu at (24.181, 75.250)
- **Pad-edge:** 44.118 mm
- **Exit:** F.Cu to via (47.40, 36.50) r=0.30 already east of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.02 -0.215 mm (via@40.75,41.1). 6 foreign nets under 0.15 mm.

### 9. `P0.05` — 45.733 mm — stub

- **A:** U1.2 on F.Cu, copper (43.622, 36.647), center (44.000, 36.500)
- **B:** pad J12.6 on F.Cu+B.Cu at (19.101, 75.250)
- **Pad-edge:** 45.733 mm
- **Exit:** F.Cu to via (47.40, 36.50) r=0.30 already east of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.02 -0.353 mm (via@40.75,41.1). 7 foreign nets under 0.15 mm.

### 10. `SIM_1V8` — 46.031 mm — via-row

- **A:** U1.49 on F.Cu, copper (29.897, 27.128), center (29.750, 26.750)
- **B:** F.Cu (72.90,44.10)-(72.90,48.60) on F.Cu at (72.714, 44.027)
- **Pad-edge:** 46.031 mm
- **Exit:** West side of the y=23.10 via row is open. The only flank is SIM_IO via (30.25, 23.10) r=0.30. A 0.18 mm track centered at x=29.71 clears it by 0.15 mm. COEX0 via (29.81, 22.00) is 4.75 mm north of the body, past this row.
- **Straight 0.18 mm F.Cu hits:** GND -0.301 mm (via@42.0,32.0). 9 foreign nets under 0.15 mm.

### 11. `P0.09` — 47.797 mm — via-row

- **A:** U1.16 on F.Cu, copper (43.622, 29.647), center (44.000, 29.500)
- **B:** pad J12.10 on F.Cu+B.Cu at (29.107, 75.187)
- **Pad-edge:** 47.797 mm
- **Exit:** F.Cu via-row gap 0.900 mm between P0.10 via (47.00, 28.50) r=0.30 (inner edge y=28.80) and P0.08 via (46.20, 30.00) r=0.30 (inner edge y=29.70). A 0.18 mm track centered at y=29.45 clears both by at least 0.15 mm. VDD_GPIO at x=47.55 is beyond this row.
- **Straight 0.18 mm F.Cu hits:** GND -0.31 mm (via@42.0,35.0). 8 foreign nets under 0.15 mm.

### 12. `P0.11` — 47.976 mm — stub

- **A:** U1.19 on F.Cu, copper (43.622, 28.147), center (44.000, 28.000)
- **B:** pad J12.12 on F.Cu+B.Cu at (34.187, 75.187)
- **Pad-edge:** 47.976 mm
- **Exit:** F.Cu (44.00, 28.00)–(46.50, 28.00) and via (48.62, 28.00) r=0.30 already east of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.06 -0.251 mm (via@40.2,44.5). 9 foreign nets under 0.15 mm.

### 13. `P0.12` — 48.028 mm — stub

- **A:** U1.20 on F.Cu, copper (43.636, 27.650), center (44.000, 27.500)
- **B:** pad J12.13 on F.Cu+B.Cu at (36.563, 75.154)
- **Pad-edge:** 48.028 mm
- **Exit:** F.Cu to via (47.00, 27.50) r=0.30 already east of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.03 -0.275 mm (via@41.75,41.1). 8 foreign nets under 0.15 mm.

### 14. `P0.10` — 48.055 mm — stub

- **A:** U1.18 on F.Cu, copper (43.622, 28.647), center (44.000, 28.500)
- **B:** pad J12.11 on F.Cu+B.Cu at (31.647, 75.187)
- **Pad-edge:** 48.055 mm
- **Exit:** F.Cu to via (47.00, 28.50) r=0.30 already east of the fab body.
- **Straight 0.18 mm F.Cu hits:** GND -0.378 mm (via@42.0,35.0). 7 foreign nets under 0.15 mm.

### 15. `SIM_IO` — 51.402 mm — stub

- **A:** U1.48 on F.Cu, copper (30.397, 27.128), center (30.250, 26.750)
- **B:** pad C37.1 on F.Cu at (75.458, 51.862)
- **Pad-edge:** 51.402 mm
- **Exit:** F.Cu to via (30.25, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.05 -0.356 mm (via@47.4,36.5). 12 foreign nets under 0.15 mm.

### 16. `P0.03` — 58.267 mm — stub

- **A:** U1.99 on F.Cu, copper (41.897, 36.872), center (41.750, 37.250)
- **B:** F.Cu (97.49,18.00)-(97.49,19.13) on F.Cu at (97.404, 19.153)
- **Pad-edge:** 58.267 mm
- **Exit:** F.Cu (41.75, 37.25)–(41.75, 41.10) already south of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.68,35.00)-(50.68,31.00)). 10 foreign nets under 0.15 mm.

### 17. `P0.22` — 62.076 mm — stub

- **A:** U1.38 on F.Cu, copper (35.389, 27.140), center (35.250, 26.750)
- **B:** via@79.24,71.5 on F.Cu+B.Cu at (79.029, 71.287)
- **Pad-edge:** 62.076 mm
- **Exit:** F.Cu (35.25, 26.75)–(35.25, 22.00) already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.06 -0.324 mm (via@48.8,40.8). 10 foreign nets under 0.15 mm.

### 18. `P0.21` — 62.812 mm — stub

- **A:** U1.37 on F.Cu, copper (35.889, 27.140), center (35.750, 26.750)
- **B:** pad J13.6 on F.Cu+B.Cu at (76.161, 75.343)
- **Pad-edge:** 62.812 mm
- **Exit:** F.Cu to via (35.75, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,38.00)-(43.25,38.00)). 10 foreign nets under 0.15 mm.

### 19. `P0.30` — 65.303 mm — stub

- **A:** U1.88 on F.Cu, copper (36.400, 37.614), center (36.250, 37.250)
- **B:** F.Cu (101.20,46.40)-(112.40,46.40) on F.Cu at (101.111, 46.388)
- **Pad-edge:** 65.303 mm
- **Exit:** F.Cu to via (36.25, 41.10) r=0.30 already south of the fab body. Classified only; not a route to retry.
- **Straight 0.18 mm F.Cu hits:** SIM_VCC -0.377 mm (via@94.76,45.54). 18 foreign nets under 0.15 mm.

### 20. `P0.26` — 66.628 mm — stub

- **A:** U1.83 on F.Cu, copper (33.889, 37.639), center (33.750, 37.250)
- **B:** pad J13.11 on F.Cu+B.Cu at (88.743, 75.461)
- **Pad-edge:** 66.628 mm
- **Exit:** F.Cu to via (33.75, 41.10) r=0.30 already south of the fab body.
- **Straight 0.18 mm F.Cu hits:** COEX0 -0.3 mm (via@38.75,41.1). 12 foreign nets under 0.15 mm.

### 21. `P0.31` — 66.737 mm — via-row

- **A:** U1.89 on F.Cu, copper (36.900, 37.614), center (36.750, 37.250)
- **B:** F.Cu (103.05,47.10)-(106.70,47.10) on F.Cu at (102.961, 47.087)
- **Pad-edge:** 66.737 mm
- **Exit:** F.Cu via-row gap 0.900 mm between P0.30 via (36.25, 41.10) r=0.30 (edge x=36.55) and COEX2 via (37.75, 41.10) r=0.30 (edge x=37.45). A 0.18 mm track centered at x=36.80 clears both by at least 0.15 mm. Right neighbor U1.90 is GND and has no local via, so this is not the 0.40 mm adjacent-via pinch. Classified only; not a route to retry.
- **Straight 0.18 mm F.Cu hits:** SIM_CLK -0.301 mm (via@70.9,42.4). 18 foreign nets under 0.15 mm.

### 22. `P0.23` — 66.873 mm — stub

- **A:** U1.39 on F.Cu, copper (34.889, 27.140), center (34.750, 26.750)
- **B:** pad J13.8 on F.Cu+B.Cu at (81.241, 75.343)
- **Pad-edge:** 66.873 mm
- **Exit:** F.Cu to via (34.75, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,38.00)-(43.25,38.00)). 8 foreign nets under 0.15 mm.

### 23. `P0.27` — 68.318 mm — via-row

- **A:** U1.84 on F.Cu, copper (34.389, 37.639), center (34.250, 37.250)
- **B:** pad J13.12 on F.Cu+B.Cu at (91.202, 75.583)
- **Pad-edge:** 68.318 mm
- **Exit:** F.Cu via-row gap 0.900 mm between P0.26 via (33.75, 41.10) r=0.30 and P0.28 via (35.25, 41.10) r=0.30. A 0.18 mm track centered at x=34.30 clears both by at least 0.15 mm. Right neighbor U1.85 is GND and has no local via.
- **Straight 0.18 mm F.Cu hits:** P0.00 -0.291 mm (via@39.75,41.1). 12 foreign nets under 0.15 mm.

### 24. `P0.24` — 69.013 mm — via-row

- **A:** U1.40 on F.Cu, copper (34.389, 27.140), center (34.250, 26.750)
- **B:** pad J13.9 on F.Cu+B.Cu at (83.663, 75.461)
- **Pad-edge:** 69.013 mm
- **Exit:** F.Cu via-row gap 0.900 mm between P0.25 via (33.25, 23.10) r=0.30 and P0.23 via (34.75, 23.10) r=0.30. A 0.18 mm track centered at x=34.21 clears the P0.23 via by 0.15 mm. Left neighbor U1.41 is GND and has no local via. SWDCLK at x=34.20 is B.Cu only.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,38.00)-(43.25,38.00)). 9 foreign nets under 0.15 mm.

### 25. `P0.28` — 69.603 mm — stub

- **A:** U1.86 on F.Cu, copper (35.397, 37.628), center (35.250, 37.250)
- **B:** pad J13.13 on F.Cu+B.Cu at (93.730, 75.599)
- **Pad-edge:** 69.603 mm
- **Exit:** F.Cu to via (35.25, 41.10) r=0.30 already south of the fab body.
- **Straight 0.18 mm F.Cu hits:** P0.02 -0.38 mm (via@40.75,41.1). 10 foreign nets under 0.15 mm.

### 26. `P0.25` — 71.584 mm — stub

- **A:** U1.42 on F.Cu, copper (33.389, 27.140), center (33.250, 26.750)
- **B:** pad J13.10 on F.Cu+B.Cu at (86.203, 75.461)
- **Pad-edge:** 71.584 mm
- **Exit:** F.Cu to via (33.25, 23.10) r=0.30 already north of the fab body.
- **Straight 0.18 mm F.Cu hits:** GND -0.377 mm (via@42.0,35.0). 9 foreign nets under 0.15 mm.

### 27. `MAGPIO0` — 77.438 mm — via-row

- **A:** U1.55 on F.Cu, copper (28.397, 28.628), center (28.000, 28.500)
- **B:** pad J14.1 on F.Cu+B.Cu at (103.500, 47.500)
- **Pad-edge:** 77.438 mm
- **Exit:** F.Cu gap 1.320 mm between MAGPIO1 track y=28.00 w=0.18 (edge y=28.09) and MIPI_VIO track y=29.50 w=0.18 (edge y=29.41). Outward is west, into the strip 24.2 < x < 28, which is outside the RF keepout. Not trapped-by-keepout.
- **Straight 0.18 mm F.Cu hits:** GND -0.36 mm (via@30.0,29.0). 15 foreign nets under 0.15 mm.

### 28. `MAGPIO1` — 78.007 mm — stub

- **A:** U1.54 on F.Cu, copper (28.397, 28.128), center (28.000, 28.000)
- **B:** pad J14.2 on F.Cu+B.Cu at (103.538, 49.079)
- **Pad-edge:** 78.007 mm
- **Exit:** F.Cu to via (25.60, 23.10) r=0.30. Via copper stays at x≥25.30, outside the keepout x≤24.2.
- **Straight 0.18 mm F.Cu hits:** COEX0 -0.365 mm (via@37.0,30.5). 14 foreign nets under 0.15 mm.

### 29. `MIPI_VIO` — 78.293 mm — stub

- **A:** U1.57 on F.Cu, copper (28.397, 29.628), center (28.000, 29.500)
- **B:** pad J14.4 on F.Cu+B.Cu at (103.538, 51.619)
- **Pad-edge:** 78.293 mm
- **Exit:** F.Cu to via (24.65, 24.40) r=0.30. Via copper west edge is x=24.35, still outside the keepout x≤24.2.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,37.95)-(50.52,35.00)). 18 foreign nets under 0.15 mm.

### 30. `MAGPIO2` — 78.501 mm — stub

- **A:** U1.53 on F.Cu, copper (28.397, 27.628), center (28.000, 27.500)
- **B:** pad J14.3 on F.Cu+B.Cu at (103.538, 50.349)
- **Pad-edge:** 78.501 mm
- **Exit:** F.Cu to via (26.75, 23.10) r=0.30, outside the keepout.
- **Straight 0.18 mm F.Cu hits:** VDD2 -0.459 mm (via@59.7,37.126). 15 foreign nets under 0.15 mm.

### 31. `MIPI_SCLK` — 78.512 mm — stub

- **A:** U1.58 on F.Cu, copper (28.397, 30.128), center (28.000, 30.000)
- **B:** pad J14.5 on F.Cu+B.Cu at (103.538, 52.889)
- **Pad-edge:** 78.512 mm
- **Exit:** F.Cu to via (26.874, 30.65) r=0.30, outside the keepout.
- **Straight 0.18 mm F.Cu hits:** VDD1 -0.29 mm (F.Cu (50.52,37.95)-(50.52,35.00)). 16 foreign nets under 0.15 mm.

## Trapped — 6

Included: U1.24. None are trapped-by-keepout. Blocking gaps are sideways and via-row. Need 0.48 mm.

### `P0.14` U1.24 F.Cu (42.250, 26.750) (N)

- **Sideways:** 0.200 mm
- **Via-row:** 0.400 mm
- **Why:** Sideways 0.200 mm to U1.25 (P0.15) and to U1.23 (P0.13). North via-row 0.400 mm between P0.15 via (41.75, 23.10) r=0.30 and P0.13 via (42.75, 23.10 and 23.95) r=0.30. Need 0.48 mm. No stub. Same pinch measured in pass30au; the reverted via (42.25, 25.50) was not placed again.
- **Other island (not ranked):** pad J18.2 F.Cu+B.Cu (40.623, 61.154), pad-edge 34.038 mm

### `P0.18` U1.29 F.Cu (39.750, 26.750) (N)

- **Sideways:** 0.200 mm
- **Via-row:** 0.400 mm
- **Why:** Sideways 0.200 mm to U1.30 (P0.19) and to U1.28 (P0.17). Via-row 0.400 mm between P0.19 via (39.25, 23.10) r=0.30 and P0.17 via (40.25, 23.10) r=0.30. No stub.
- **Other island (not ranked):** pad J18.6 F.Cu+B.Cu (50.453, 61.187), pad-edge 35.644 mm

### `P0.01` U1.96 F.Cu (40.250, 37.250) (S)

- **Sideways:** 0.200 mm
- **Via-row:** 0.400 mm
- **Why:** Sideways 0.200 mm to U1.95 (P0.00) and to U1.97 (P0.02). South via-row 0.400 mm between P0.00 via (39.75, 41.10) r=0.30 and P0.02 via (40.75, 41.10) r=0.30. No stub.
- **Other island (not ranked):** B.Cu (27.20,78.50)-(62.00,78.50) B.Cu (40.364, 78.410), pad-edge 40.760 mm

### `COEX1` U1.92 F.Cu (38.250, 37.250) (S)

- **Sideways:** 0.200 mm
- **Via-row:** 0.400 mm
- **Why:** Sideways 0.200 mm to U1.91 (COEX2) and to U1.93 (COEX0). South via-row 0.400 mm between COEX2 via (37.75, 41.10) r=0.30 and COEX0 via (38.75, 41.10) r=0.30. No stub.
- **Other island (not ranked):** pad J15.2 F.Cu+B.Cu (103.538, 63.079), pad-edge 69.936 mm

### `P0.29` U1.87 F.Cu (35.750, 37.250) (S)

- **Sideways:** 0.200 mm
- **Via-row:** 0.400 mm
- **Why:** Sideways 0.200 mm to U1.86 (P0.28) and to U1.88 (P0.30). South via-row 0.400 mm between vias (35.25, 41.10) and (36.25, 41.10), both r=0.30. No stub.
- **Other island (not ranked):** pad J13.14 F.Cu+B.Cu (96.270, 75.599), pad-edge 71.321 mm

### `MIPI_SDATA` U1.59 F.Cu (28.000, 30.500) (W)

- **Sideways:** 0.200 mm
- **Via-row:** 0.000 mm
- **Why:** Sideways 0.200 mm to U1.58 (MIPI_SCLK) and to U1.60 (GND). MIPI_SCLK via (26.874, 30.650) r=0.30 covers y 30.35–30.95 and straddles the pad axis y=30.50, so the via-row gap on the axis is 0. The pad's track-center window (±0.06 mm) cannot clear that via by 0.15 mm. The via is at x=26.87, outside the RF keepout, so this is a via block, not trapped-by-keepout. No stub.
- **Other island (not ranked):** pad J14.6 F.Cu+B.Cu (103.538, 54.159), pad-edge 78.739 mm

## Not done

No track, via, zone, or footprint move. No refill. The reverted P0.14 via at (42.25, 25.50) was not placed. P0.13 and P0.15 vias were not moved. U1.88 and U1.89 were classified and not routed. The y=44.60 pocket was not used. No header or U1 move. No Gerbers. No git commit. No one was pinged.

