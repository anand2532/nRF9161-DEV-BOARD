# PASS30AR shortlist — five shortest non-GND opens

**Timestamp:** 2026-09-30 11:07 IST
**Decision:** **NO-ROUTE** (no copper edit)
**Why:** the remaining P0.31 open, pad U1.89 to the locked pass30aq track, is **66.737 mm**, over the 25 mm cap. That leftover is listed after the five. It is not one of the five shortest.

Distance is copper-edge to copper-edge on the live board. Each row is a real DRC open (`reports/DRC_PASS30AQ_AFTER.json`, live unconnected count 61). GND zone islands (12) are not ranked. A straight-line blocker is foreign copper a 0.18 mm capsule on the chord would clear by less than 0.15 mm. Negative clearance is an overlap.

## 1. `P0.30` — 32.207 mm

- **A:** pad J13.15 on B.Cu+F.Cu at (99.961, 75.250)
- **B:** pad J11.1 on B.Cu+F.Cu at (115.150, 46.850)
- **Same-layer chord:** F.Cu (99.961, 75.250) → (115.150, 46.850)
- **Straight-line blockers (< 0.15 mm):** VDD_GPIO -0.215 mm (F.Cu (105.10,67.08)-(105.10,51.08), n=5); P0.04 -0.180 mm (F.Cu (114.80,52.50)-(108.45,52.50), n=3); P0.31 -0.180 mm (F.Cu (102.60,75.50)-(103.05,47.10), n=2); GND -0.090 mm (pad J15.6, n=1)
- **Nearest:** VDD_GPIO -0.215 mm (F.Cu (105.10,67.08)-(105.10,51.08))

## 2. `P0.14` — 34.038 mm

- **A:** pad U1.24 on F.Cu at (42.136, 27.150)
- **B:** pad J18.2 on B.Cu+F.Cu at (40.623, 61.154)
- **Same-layer chord:** F.Cu (42.136, 27.150) → (40.623, 61.154)
- **Straight-line blockers (< 0.15 mm):** GND -0.336 mm (via@42.0,29.0, n=8); P0.04 -0.168 mm (F.Cu (41.25,46.80)-(37.40,46.80), n=3); P0.03 -0.156 mm (via@41.75,41.1, n=4); P0.15 0.149 mm (pad U1.25, n=1)
- **Nearest:** GND -0.336 mm (via@42.0,29.0)

## 3. `P0.16` — 34.259 mm

- **A:** pad J18.4 on B.Cu+F.Cu at (45.537, 61.154)
- **B:** pad U1.26 on F.Cu at (41.364, 27.150)
- **Same-layer chord:** F.Cu (45.537, 61.154) → (41.364, 27.150)
- **Straight-line blockers (< 0.15 mm):** GND -0.349 mm (via@42.0,32.0, n=8); ENABLE -0.321 mm (via@43.4,45.126, n=7); P0.04 0.068 mm (pad U1.100, n=1); P0.15 0.149 mm (pad U1.25, n=1)
- **Nearest:** GND -0.349 mm (via@42.0,32.0)

## 4. `P0.17` — 34.863 mm

- **A:** pad U1.28 on F.Cu at (40.378, 27.147)
- **B:** pad J18.5 on B.Cu+F.Cu at (47.913, 61.187)
- **Same-layer chord:** F.Cu (40.378, 27.147) → (47.913, 61.187)
- **Straight-line blockers (< 0.15 mm):** GND -0.277 mm (via@42.0,35.0, n=6); ENABLE -0.180 mm (F.Cu (52.00,44.00)-(42.75,44.00), n=4); P0.04 0.040 mm (pad U1.100, n=1)
- **Nearest:** GND -0.277 mm (via@42.0,35.0)

## 5. `P0.18` — 35.644 mm

- **A:** pad J18.6 on B.Cu+F.Cu at (50.453, 61.187)
- **B:** pad U1.29 on F.Cu at (39.878, 27.147)
- **Same-layer chord:** F.Cu (50.453, 61.187) → (39.878, 27.147)
- **Straight-line blockers (< 0.15 mm):** VDD1 -0.290 mm (F.Cu (50.52,38.00)-(43.25,38.00), n=9); P0.06 -0.237 mm (via@44.0,39.9, n=1); ENABLE -0.180 mm (F.Cu (52.00,44.00)-(42.75,44.00), n=4); GND -0.090 mm (pad U1.103, n=5); P0.17 0.131 mm (pad U1.28, n=1)
- **Nearest:** VDD1 -0.290 mm (F.Cu (50.52,38.00)-(43.25,38.00))

## Also measured — `P0.31` U1.89 leftover — 66.737 mm

Not in the five (rank is well below P0.18 at 35.644 mm). Included because this pass was required to measure it.

- **A:** pad U1.89 on F.Cu at (36.900, 37.614)
- **B:** F.Cu (103.05,47.10)-(106.70,47.10) on F.Cu at (102.961, 47.087)
- **Same-layer chord:** F.Cu (36.900, 37.614) → (102.961, 47.087)
- **Straight-line blockers (< 0.15 mm):** SIM_CLK -0.301 mm (via@70.9,42.4, n=4); VDD2 -0.290 mm (F.Cu (50.68,40.00)-(50.68,39.00), n=12); SIM_CLK_C -0.272 mm (via@99.19,46.666, n=2); SIM_VCC -0.215 mm (F.Cu (80.65,33.54)-(80.65,46.00), n=5); ENABLE -0.180 mm (F.Cu (42.75,37.25)-(42.75,41.10), n=4); P0.04 -0.180 mm (F.Cu (42.25,37.25)-(42.25,40.30), n=1); VDD_GPIO -0.180 mm (F.Cu (72.44,43.05)-(71.94,42.05), n=4); P0.03 -0.180 mm (F.Cu (41.75,37.25)-(41.75,41.10), n=2); +9 nets
- **Nearest:** SIM_CLK -0.301 mm (via@70.9,42.4). 17 nets, 47 items.

## Not attempted

No backup, no track, no via. The locked pass30aq P0.31 run was not ripped. P0.30 was not started even though it is the shortest remaining open. The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved. No Gerbers. No git commit.
