# PASS30AR_SUMMARY — P0.31 leftover

**Timestamp:** 2026-09-30 11:07 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net measured:** P0.31 (the one remaining open after pass30aq KEEP)
**Routed:** no

## Gap

Pad-edge gap **66.737 mm** (cap 25 mm). Over the cap, so no jog was placed. No backup. Board bytes unchanged.

Copper-edge to copper-edge on F.Cu. `pcbnew` clearance from the U1.89 effective pad shape to the nearest pass30aq track segment is 66.736 mm, which matches.

| endpoint | ref | layer | xy |
| --- | --- | --- | --- |
| A | pad U1.89 | F.Cu | (36.900, 37.614) |
| B | F.Cu (103.05, 47.10)–(106.70, 47.10) | F.Cu | (102.961, 47.087) |

U1.89 is its own island (the pad only). The other island is the locked pass30aq run: J13.16, six F.Cu 0.18 mm segments, J11.2. The nearest copper on that island is the west edge of the horizontal segment at y=47.10, not the DRC anchor at (102.60, 75.50).

## Straight 0.18 mm line

F.Cu (36.900, 37.614) → (102.961, 47.087). It is not clear. 47 foreign items on 17 nets sit inside 0.15 mm. Negative clearance means the 0.18 mm capsule overlaps that copper. Nearest: SIM_CLK via@(70.900, 42.400) at **-0.301 mm**.

| net | clearance mm | worst item | items |
| --- | ---: | --- | ---: |
| SIM_CLK | -0.301 | via@70.9,42.4 | 4 |
| VDD2 | -0.290 | F.Cu (50.68,40.00)-(50.68,39.00) | 12 |
| SIM_CLK_C | -0.272 | via@99.19,46.666 | 2 |
| SIM_VCC | -0.215 | F.Cu (80.65,33.54)-(80.65,46.00) | 5 |
| ENABLE | -0.180 | F.Cu (42.75,37.25)-(42.75,41.10) | 4 |
| P0.04 | -0.180 | F.Cu (42.25,37.25)-(42.25,40.30) | 1 |
| VDD_GPIO | -0.180 | F.Cu (72.44,43.05)-(71.94,42.05) | 4 |
| P0.03 | -0.180 | F.Cu (41.75,37.25)-(41.75,41.10) | 2 |
| COEX0 | -0.180 | F.Cu (38.75,37.25)-(38.75,41.10) | 2 |
| SIM_CD | -0.180 | F.Cu (90.00,52.04)-(90.00,36.00) | 1 |
| P0.02 | -0.180 | F.Cu (40.75,37.25)-(40.75,41.10) | 1 |
| SIM_IO | -0.180 | F.Cu (84.00,58.60)-(84.00,36.00) | 1 |
| P0.00 | -0.180 | F.Cu (39.75,37.25)-(39.75,41.10) | 1 |
| COEX2 | -0.180 | F.Cu (37.75,37.25)-(37.75,41.10) | 2 |
| GND | -0.090 | pad U1.90 | 3 |
| SIM_RST_C | 0.043 | pad J7.C2 | 1 |
| COEX1 | 0.050 | pad U1.92 | 1 |

Filled zones are not in this table. A pour retreats around a track, so it is not a discrete blocker. Locked copper on this chord includes VDD2, SIM_CLK_C, P0.04, VDD_GPIO (pass30ap), and COEX0. The line was not used.

## Decision

NO-ROUTE. Gap 66.737 mm > 25 mm. One jog was not attempted. Locked P0.31 run was not ripped. P0.30 was not started. No header or U1 move. No Gerbers. No git commit.

Live unconnected is still **61** (`GetUnconnectedCount`, same as `reports/DRC_PASS30AQ_AFTER.json`). P0.31 opens still 1. No new DRC file, because no copper changed.

Five shortest other non-GND opens are all over 25 mm as well (P0.30 32.207 mm is the shortest). Detail: `reports/PASS30AR_SHORTLIST.md`.
