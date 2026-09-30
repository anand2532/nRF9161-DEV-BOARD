# PASS30AT shortlist — five shortest connector-to-connector opens

**Timestamp:** 2026-09-30 11:27 IST
**Decision:** **NO-ROUTE** (no copper edit)
**Why:** the remaining P0.30 open, pad U1.88 (via at (36.250, 41.100)) to the locked pass30as track, is **64.776 mm**, over the 25 mm cap. That leftover is listed after the five. It is not a connector-to-connector candidate (one end is U1).

A pair is included only when both islands have pads and every pad is a connector (reference `J*`). U1 and any non-connector pad (R/C/U/D/L/TP/SW) drop the pair. 11 pairs match. Five shortest by pad-edge are listed. The next is `P0.12` at 93.559 mm (J12.13 ↔ J16.3). GND zone islands (12) are not ranked.

Pad-edge is copper-edge between the connector pads on one shared layer. A straight-line blocker is foreign copper a 0.18 mm capsule on that F.Cu chord would clear by less than 0.15 mm. Negative clearance is an overlap. Island counts match DRC opens (`islands = opens + 1`) on every non-GND open net (`reports/DRC_PASS30AS_AFTER.json`, live unconnected 60).

## 1. `P0.24` — 49.625 mm

- **A:** pad J10.4 on B.Cu+F.Cu at (116.000, 35.620)
- **B:** pad J13.9 on B.Cu+F.Cu at (84.320, 76.000)
- **Pad-edge:** 49.625 mm
- **Island copper-edge:** 49.625 mm (same pair; closest copper is the pads)
- **Same-layer chord:** F.Cu (115.461, 36.277) → (84.859, 75.343)
- **Straight-line blockers (< 0.15 mm):** VDD_GPIO -0.215 mm (F.Cu (114.40,38.16)-(114.40,31.08), n=2); P0.04 -0.180 mm (F.Cu (113.80,49.20)-(113.80,36.80), n=1); P0.31 -0.180 mm (F.Cu (102.60,75.50)-(103.05,47.10), n=3); P0.30 -0.180 mm (F.Cu (101.20,46.40)-(112.40,46.40), n=2); P0.06 -0.180 mm (F.Cu (113.20,47.20)-(113.20,36.00), n=2); MAGPIO2 -0.090 mm (pad J14.3, n=1); MIPI_VIO -0.034 mm (pad J14.4, n=1); GND 0.128 mm (pad J7.SH, n=1)
- **Nearest:** VDD_GPIO -0.215 mm (F.Cu (114.40,38.16)-(114.40,31.08))
- **B.Cu chord nearest:** VDD_GPIO -0.290 mm (B.Cu (111.20,38.80)-(116.00,38.80)); 10 nets under 0.15 mm

## 2. `P0.23` — 53.192 mm

- **A:** pad J10.3 on B.Cu+F.Cu at (116.000, 33.080)
- **B:** pad J13.8 on B.Cu+F.Cu at (81.780, 76.000)
- **Pad-edge:** 53.192 mm
- **Island copper-edge:** 53.192 mm (same pair; closest copper is the pads)
- **Same-layer chord:** F.Cu (115.461, 33.737) → (82.319, 75.343)
- **Straight-line blockers (< 0.15 mm):** VDD_GPIO -0.215 mm (F.Cu (114.40,38.16)-(114.40,31.08), n=1); P0.31 -0.180 mm (F.Cu (103.05,47.10)-(106.70,47.10), n=2); P0.30 -0.180 mm (F.Cu (101.20,46.40)-(112.40,46.40), n=2); P0.06 -0.180 mm (F.Cu (113.20,47.20)-(113.20,36.00), n=2); SIM_CD -0.090 mm (pad J7.CSW, n=1); GND -0.021 mm (via@110.0,40.0, n=3); MAGPIO0 -0.001 mm (pad J14.1, n=1); MAGPIO1 0.123 mm (pad J14.2, n=1)
- **Nearest:** VDD_GPIO -0.215 mm (F.Cu (114.40,38.16)-(114.40,31.08))
- **B.Cu chord nearest:** VDD_GPIO -0.290 mm (B.Cu (111.20,38.80)-(116.00,38.80)); 12 nets under 0.15 mm

## 3. `P0.18` — 59.678 mm

- **A:** pad J13.3 on B.Cu+F.Cu at (69.080, 76.000)
- **B:** pad J17.2 on B.Cu+F.Cu at (108.000, 28.540)
- **Pad-edge:** 59.678 mm
- **Island copper-edge:** 57.999 mm. Island copper is 57.999 mm on B.Cu: track (69.08,72.80)-(50.70,72.80) on the J13 island to pad J17.2. Pad-edge is the longer of the two because that track sticks south of J13.3.
- **Same-layer chord:** F.Cu (69.619, 75.343) → (107.461, 29.197)
- **Straight-line blockers (< 0.15 mm):** nRESET -0.299 mm (via@102.0,36.0, n=3); SIM_VCC -0.290 mm (F.Cu (93.46,45.54)-(94.76,45.54), n=2); VDD_GPIO -0.290 mm (F.Cu (86.51,31.08)-(108.00,31.08), n=2); SIM_CD -0.180 mm (F.Cu (90.00,52.04)-(90.00,36.00), n=1); SIM_IO -0.180 mm (F.Cu (77.35,58.60)-(84.00,58.60), n=2); P0.20 -0.180 mm (F.Cu (74.16,60.90)-(74.16,76.00), n=1); GND 0.070 mm (pad J7.SH, n=1)
- **Nearest:** nRESET -0.299 mm (via@102.0,36.0)
- **B.Cu chord nearest:** nRESET -0.299 mm (via@102.0,36.0); 9 nets under 0.15 mm

## 4. `P0.21` — 59.990 mm

- **A:** pad J10.1 on B.Cu+F.Cu at (116.000, 28.000)
- **B:** pad J13.6 on B.Cu+F.Cu at (76.700, 76.000)
- **Pad-edge:** 59.990 mm
- **Island copper-edge:** 59.990 mm (same pair; closest copper is the pads)
- **Same-layer chord:** F.Cu (115.150, 28.850) → (77.239, 75.343)
- **Straight-line blockers (< 0.15 mm):** VDD_GPIO -0.215 mm (F.Cu (114.40,31.08)-(86.51,31.08), n=1); P0.22 -0.180 mm (F.Cu (112.50,29.90)-(114.70,29.90), n=5); SIM_IO_C -0.180 mm (F.Cu (98.54,48.71)-(98.54,50.01), n=3); SIM_CD -0.180 mm (F.Cu (100.27,52.04)-(90.00,52.04), n=3); GND -0.005 mm (pad J7.SH, n=1); P0.30 0.099 mm (F.Cu (101.20,46.40)-(112.40,46.40), n=2)
- **Nearest:** VDD_GPIO -0.215 mm (F.Cu (114.40,31.08)-(86.51,31.08))
- **B.Cu chord nearest:** VDD_GPIO -0.290 mm (B.Cu (110.60,31.08)-(110.60,38.80)); 10 nets under 0.15 mm

## 5. `P0.17` — 62.907 mm

- **A:** pad J13.2 on B.Cu+F.Cu at (66.540, 76.000)
- **B:** pad J17.1 on B.Cu+F.Cu at (108.000, 26.000)
- **Pad-edge:** 62.907 mm
- **Island copper-edge:** 61.684 mm. Island copper is 61.684 mm on B.Cu: track (66.54,73.40)-(48.16,73.40) on the J13 island to pad J17.1. Pad-edge is 62.907 mm.
- **Same-layer chord:** F.Cu (67.079, 75.343) → (107.150, 26.850)
- **Straight-line blockers (< 0.15 mm):** VDD_GPIO -0.290 mm (F.Cu (86.51,31.08)-(108.00,31.08), n=2); P0.01 -0.217 mm (via@68.0,74.5, n=2); SIM_VCC -0.215 mm (F.Cu (93.46,45.54)-(93.46,33.54), n=1); SIM_CD -0.180 mm (F.Cu (90.00,52.04)-(90.00,36.00), n=1); SIM_IO -0.180 mm (F.Cu (77.35,58.60)-(84.00,58.60), n=2); P0.20 -0.180 mm (F.Cu (74.16,60.90)-(74.16,76.00), n=1); GND 0.032 mm (pad J7.SH, n=1)
- **Nearest:** VDD_GPIO -0.290 mm (F.Cu (86.51,31.08)-(108.00,31.08))
- **B.Cu chord nearest:** P0.01 -0.217 mm (via@68.0,74.5); 10 nets under 0.15 mm

## Also measured — `P0.30` U1.88 leftover — 64.776 mm

Not a connector-to-connector candidate (one end is U1.88). Included because this pass was required to name it. It is not in the five.

- **A:** pad U1.88 on F.Cu at (36.250, 37.250), via (36.250, 41.100) od 0.60 / drill 0.30. Closest copper is the via edge at (36.549, 41.124).
- **B:** locked pass30as island, pads J13.15 (99.560, 76.000) and J11.1 (116.000, 46.000). Closest copper is F.Cu (101.20, 46.40)–(112.40, 46.40) at (101.110, 46.393).
- **Same-layer chord:** F.Cu (36.549, 41.124) → (101.110, 46.393)
- **Copper-edge:** 64.776 mm. U1.88 pad-edge to that track is 65.303 mm.
- **Straight-line blockers (< 0.15 mm):** SIM_1V8 -0.290 mm (F.Cu (75.52,44.00)-(75.52,46.00), n=10); COEX2 -0.268 mm (via@37.75,41.1, n=2); SIM_VCC -0.215 mm (F.Cu (80.65,33.54)-(80.65,46.00), n=5); VDD2 -0.215 mm (F.Cu (61.80,42.00)-(61.80,45.10), n=1); COEX0 -0.187 mm (via@38.75,41.1, n=2); ENABLE -0.180 mm (F.Cu (52.00,44.00)-(52.00,40.95), n=3); SIM_CLK_C -0.180 mm (F.Cu (99.19,45.54)-(99.19,46.67), n=2); VDD_GPIO -0.180 mm (F.Cu (70.44,41.55)-(54.44,61.05), n=1); P0.03 -0.180 mm (F.Cu (41.75,74.40)-(41.75,37.25), n=2); SIM_CD -0.180 mm (F.Cu (90.00,52.04)-(90.00,36.00), n=1); P0.02 -0.180 mm (F.Cu (40.75,41.10)-(40.75,43.50), n=2); SIM_IO -0.180 mm (F.Cu (84.00,58.60)-(84.00,36.00), n=1); SIM_CLK -0.180 mm (F.Cu (70.90,44.00)-(70.90,42.40), n=4); P0.00 -0.180 mm (F.Cu (39.75,41.10)-(6.00,76.00), n=3); GND -0.048 mm (pad J7.SH, n=4); SIM_RST_C -0.041 mm (pad J7.C2, n=2)
- **Nearest:** SIM_1V8 -0.290 mm (F.Cu (75.52,44.00)-(75.52,46.00)). 16 nets, 45 items.

## Not attempted

No backup, no track, no via. The locked pass30as P0.30 run was not ripped. The P0.31 U1.89 leftover was not retried. P0.14 was not started. The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved. No Gerbers. No git commit.

