# PASS30AT_SUMMARY — P0.30 leftover

**Timestamp:** 2026-09-30 11:27 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net measured:** P0.30 (the one remaining open after pass30as KEEP)
**Routed:** no

## Leftover

The remaining P0.30 open is **pad U1.88** (with its via) to the locked pass30as island (**pad J13.15** and **pad J11.1**).

| island | pads | layer | xy | other copper |
| --- | --- | --- | --- | --- |
| leftover | U1.88 | F.Cu | (36.250, 37.250) | F.Cu 0.18 mm (36.25, 37.25)→(36.25, 41.10); via 0.60/0.30 at (36.250, 41.100) |
| locked pass30as | J13.15 | B.Cu+F.Cu | (99.560, 76.000) | eight 0.18 mm segments and via 0.60/0.30 at (112.400, 46.400) |
| locked pass30as | J11.1 | B.Cu+F.Cu | (116.000, 46.000) | same island |

DRC names this open as via [P0.30] at (36.25, 41.10) against the F.Cu track at (101.20, 46.40). Live islands: 2, matching 1 DRC open.

## Gap

Copper-edge gap **64.776 mm** (cap 25 mm), F.Cu, from the leftover island to the locked pass30as track. Over the cap, so no jog was placed. No backup. Board bytes unchanged.

| endpoint | ref | layer | xy |
| --- | --- | --- | --- |
| A | via@36.25,41.1 (island of pad U1.88) | F.Cu | (36.549, 41.124) |
| B | F.Cu (101.20, 46.40)–(112.40, 46.40) | F.Cu | (101.110, 46.393) |

The closest copper on the leftover island is the via annular ring, not the pad. Pad-edge from U1.88 itself to that same locked track is **65.303 mm** (pad outline point (36.400, 37.614) to (101.111, 46.388)). Either number is over 25 mm.

## Straight 0.18 mm line

F.Cu (36.549, 41.124) → (101.110, 46.393). It is not clear. 45 foreign items on 16 nets sit inside 0.15 mm. Negative clearance means the 0.18 mm capsule overlaps that copper. Nearest: SIM_1V8 F.Cu (75.52, 44.00)–(75.52, 46.00) at **-0.290 mm**.

| net | clearance mm | worst item | items |
| --- | ---: | --- | ---: |
| SIM_1V8 | -0.290 | F.Cu (75.52,44.00)-(75.52,46.00) | 10 |
| COEX2 | -0.268 | via@37.75,41.1 | 2 |
| SIM_VCC | -0.215 | F.Cu (80.65,33.54)-(80.65,46.00) | 5 |
| VDD2 | -0.215 | F.Cu (61.80,42.00)-(61.80,45.10) | 1 |
| COEX0 | -0.187 | via@38.75,41.1 | 2 |
| ENABLE | -0.180 | F.Cu (52.00,44.00)-(52.00,40.95) | 3 |
| SIM_CLK_C | -0.180 | F.Cu (99.19,45.54)-(99.19,46.67) | 2 |
| VDD_GPIO | -0.180 | F.Cu (70.44,41.55)-(54.44,61.05) | 1 |
| P0.03 | -0.180 | F.Cu (41.75,74.40)-(41.75,37.25) | 2 |
| SIM_CD | -0.180 | F.Cu (90.00,52.04)-(90.00,36.00) | 1 |
| P0.02 | -0.180 | F.Cu (40.75,41.10)-(40.75,43.50) | 2 |
| SIM_IO | -0.180 | F.Cu (84.00,58.60)-(84.00,36.00) | 1 |
| SIM_CLK | -0.180 | F.Cu (70.90,44.00)-(70.90,42.40) | 4 |
| P0.00 | -0.180 | F.Cu (39.75,41.10)-(6.00,76.00) | 3 |
| GND | -0.048 | pad J7.SH | 4 |
| SIM_RST_C | -0.041 | pad J7.C2 | 2 |

POWER/VIN on that chord: VDD2 -0.215 mm and VDD_GPIO -0.180 mm, both under 0.20 mm. Locked copper on the chord includes VDD2, SIM_CLK_C, VDD_GPIO, and COEX0. The line was not used. The locked eight-segment P0.30 run was not ripped.

## Decision

NO-ROUTE. Gap 64.776 mm > 25 mm. One jog was not attempted. P0.31 leftover (U1.89) was not retried. P0.14 was not started. No header or U1 move. Sealed B.Cu pocket y≈44.60 not used. No Gerbers. No git commit.

Live unconnected is still **60** (`CONNECTIVITY_DATA.GetUnconnectedCount`, same as `reports/DRC_PASS30AS_AFTER.json`). P0.30 opens still 1. P0.31 opens still 1. short/clearance/crossing/hole_clearance 0. hole_to_hole 1. GND islands 12 (waived). No new DRC file, because no copper changed.

Five shortest connector-to-connector non-GND opens (both islands are connector pads only, no U1): P0.24 49.625 mm, P0.23 53.192 mm, P0.18 59.678 mm, P0.21 59.990 mm, P0.17 62.907 mm. All over 25 mm. The U1.88 leftover is recorded with them and is not one of the five. Detail: `reports/PASS30AT_SHORTLIST.md`.

