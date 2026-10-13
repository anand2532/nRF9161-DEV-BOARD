# RF review — pass30cd/ce (branch `autoroute-gpio` @ fb5f34e)

Reviewer: RF Power Engineer · 2026-10-12 · read-only (pcbnew 9 on `git show` copies in /tmp; zones refilled before every check; DRC via kicad-cli on a refilled copy).
Compared against main 8628f07 (and the rejected 3e2a15f, see RF_REVIEW_PASS30CC.md).

## Verdict: **MERGE** (no blocking RF fixes)
Every item on the pass30cc fix list is met. Protected Class C copper is unchanged. Open MIPI_SCLK/MIPI_VIO are fine to merge as opens, but they remain a fab gate. The follow-ups below are non-blocking and can go in a later RF-only pass.

## PM claims verified
| claim | measured |
|---|---|
| new copper F/B only, 25 vias, 775 mm | **Confirmed.** 774.7 mm (F+B only) and 25 new vias (GND 6). 0 new In1/In2 tracks (112 inner tracks on both commits). 53 items removed (dangling cleanup on rippable nets). |
| In1 GND 2 pieces / 8117.5 mm² | **Confirmed.** Main has 3 pieces / 8074.4 mm². fb5f34e has 2 pieces (8106.8 + 10.7) / 8117.5 mm². In2 VDD_nRF has 1 piece (7350.7 mm²). |
| MIPI_SCLK / MIPI_VIO open | **Confirmed** (DRC unconnected U1 p58 and p57 to J14). |
| P0.21 130.7 mm, P0.23 137.3 mm | **Confirmed.** P0.21: F 107.9 / B 22.8 mm, 1 via. P0.23: F 100.7 / B 36.6 mm, 1 via. |

## Fix-list verification
| item | target | result | status |
|---|---|---|---|
| No new In1 copper | 0 | 0 (In2 also 0) | PASS |
| Extended keepout x0–29, y26–40 | no new copper | 0 new tracks/vias inside | PASS |
| MIPI_SCLK/SDATA ≤50 mm B.Cu, MIPI_VIO ≤60 mm | — | not routed (open) | PASS (open = fab gate) |
| MAGPIO0/1/2, COEX1 ≤80 mm, away from feeds | — | not routed (open; MAGPIO1 is a trapped pad) | PASS (open) |
| P0.14/P0.18 not under U1 or feeds | — | no new copper; both still open | PASS |
| SIM_* ≥0.5 mm, parallel ≤10 mm | — | min 0.504 mm (P0.30↔SIM_IO, F.Cu). Parallel within 1.0 mm: P0.30↔SIM_IO 8.5 mm, P0.29↔SIM_IO 3.6 mm. 0 mm within 0.5 mm. P0.23↔SIM_CLK ≥2.09 mm. P0.24/25 not routed. | PASS |
| RF feeds (ANT/AUX/GPS/ANT_FIT/AUX_FIT/GNSS_*) | ≥1.0 mm | no new copper within 3 mm of any feed. Closest new copper is P0.23 at 10.4 mm from ANT. | PASS |
| VDD_nRF coupling | — | P0.03↔VDD_nRF 0.244 mm on F.Cu, with 0.6 mm run <0.5 mm and 3.7 mm <1 mm. This is a decoupled DC rail and a GPIO at ≥0.2 mm power clearance. | PASS (note) |
| GND slivers / fragments | delete <5 mm² near RF, stitch | 3.8 mm² sliver removed by rule area. 16.3 mm² piece east of U1 stitched with 5 vias. No new slivers in the RF corner. 0 dangling GND vias. | PASS |
| In1 ≥3 pieces-or-better / ≥8070 mm² | — | 2 pieces / 8117.5 mm² (better than main) | PASS |
| New copper in U1 footprint box | — | 9 short segments: B.Cu P0.26/P0.03/P0.01, plus F.Cu P0.01/P0.29 breakouts and the GND pad-90 dog-bone. All are under U1 on B.Cu, with solid In1 between, or are pad fan-out on F.Cu. 0 vias in the U1 area. | Acceptable |

## Protected Class C copper
All 55 track/via items on ANT, ANT_FIT, AUX, AUX_FIT, GPS and GNSS_* are **identical** to main/pass30z. C22, C23, C24, L1, L2, TP1, U3, C27, L4 and FB5 have identical position, rotation, layer and pad nets.

## P0.21 / P0.23 (130.7 / 137.3 mm)
**Acceptable for plain GPIO** (slow edges, no RFFE/clock role). Neither net has segments inside the U1 underside box apart from its pad entry. Minimum distance to the RF feeds is ≥10.4 mm (ANT), ≥11.6 mm (AUX), ≥12.9 mm (GPS) and ≥15.5 mm (fits/stubs). VDD_nRF is ≥8.5 mm away, and SIM_CLK ≥2.1 mm. They run mostly on F.Cu over solid In1, so the return path is intact.

Emission risk is low as long as firmware doesn't use them for fast PWM or clocks. If either becomes a >1 MHz signal, set a slow drive mode or add a series R at U1. Optional: a series 33–100 Ω footprint near U1 in a later schematic pass. Not required for merge.

## Dangling items (DRC on refilled fb5f34e): 35 vias + 10 tracks = 45
This is the 44 locked-net items plus 1 kept P0.11 stub. **There are no GND dangling items**, so all GND stitching vias tie to the zones.

### RF / Class C nets
| net | item | layer | XY (mm) | class | action |
|---|---|---|---|---|---|
| GNSS_VBIAS | track 4.79 mm (12.05,50.0)→(12.05,45.21) | F.Cu | 12.05, 50.0 | REMOVABLE (orphan loop leftover; open end at 12.05,45.21 with no via) | remove in RF-only pass |
| GNSS_VBIAS | track 13.05 mm (25.1,45.21)→(12.05,45.21) | B.Cu | 25.1, 45.21 | REMOVABLE (other half of the same broken loop; net is already connected via 13.35,50 / 25.1,38 path) | remove in RF-only pass |

Also on GNSS_VBIAS: duplicate overlapping F.Cu segments (5.02,50)–(13.52,50), (5.02,50)–(5.02,54) and (5.02,54)–(13.52,54) appear twice each. They are harmless but should be cleaned up in the same pass.

INTENTIONAL: the C22/C23/C24 Class C stubs (0.88/1.0/1.2 mm). They connect to pads, so DRC does not flag them; keep them. ANT/ANT_FIT/AUX/AUX_FIT/GPS/GNSS_ANT have 0 dangling items.
**RF counts: 0 intentional-flagged, 2 removable (both GNSS_VBIAS; DC bias stubs, decoupled, not on the 50 Ω path, so non-blocking).**

### Power / SWD / other (defer to Layout/Schematic; likely leftovers from reverted passes)
- ENABLE: vias (91.67,24.0) (42.75,41.1) (56.5,20.3) (42.75,45.6) (43.4,45.13); B.Cu tracks 0.32 mm @ (47.68,21.68) and 2.85 mm @ (50.85,23.15)
- VDD_GPIO: vias (79.3,32) (71.3,8) (87.81,26) (49.75,3.46) (76.44,39.05) (78,32); B.Cu tracks 9.3 mm @ (48.05,5.5) and 3.05 mm @ (48.05,3.46)
- VDD2: vias (61.8,45.1) (54.5,21.2) (68.14,16.87) (69.44,18.0); B.Cu tracks 1.05 mm @ (52.22,30.95) and (54.5,30.95)
- VDD1 (49.44,16.87) · VIN_IN (63.3,10.0) · VIN_FILT (52.55,23.03) (53.7,22.4) · VIN_F (71.2,19.8) (72.88,19.06) (49.05,13.33)
- DEC0: vias (48.65,21.13) and **(45.4,30.55)**
- SIM_CLK_C (76.62,56.05) · SIM_VCC (94.76,45.54) · SIM_RST via (79.3,36.0) + B.Cu track 6.57 mm @ (78.25,43.8)
- SWDIO **(37.25,23.1)** · SWDCLK (53.65,4.73) (63.3,6.0) · nRESET (53.65,12.6) (103.3,36.0) (53.65,7.27) **(38.25,23.1)** · nRESET_SW (99.67,24.0)
- P0.11 B.Cu 4.62 mm @ (44.0,29.2): kept on purpose (removing it reopens P0.11)

RF-relevant flags:
- **DEC0 via (45.4,30.55)** sits next to U1. DEC0 is a modem decoupling node, so an orphan via there is a small antenna stub on a sensitive node. Recommend removing it if Schematic/Layout confirm it is unused.
- SWDIO/nRESET vias at (37.25/38.25, 23.1), just north of U1, are low risk; remove them when convenient.
- The SIM_RST 6.57 mm dangling B.Cu stub is a stub on a SIM line; recommend removing it.
- No VDD_nRF dangling items.

## Residual fab gates (unchanged by this merge)
- DRC unconnected = 29 (17 non-GND opens + 12 GND zone islands): MIPI_SCLK, MIPI_VIO, MAGPIO0, MAGPIO2, COEX1, P0.10, P0.12, P0.14, P0.18, P0.24, P0.25, P0.27, P0.31, SIM_IO, plus trapped U1 pads MAGPIO1 (p54), MIPI_SDATA (p59), SIM_1V8 (p49).
- VIPPO on U1 trapped pads: RF/power side OK (see PASS30CC review); **pending DFM cost/capability**.
- hole_to_hole 1, copper_edge_clearance 5: Layout/DFM to clear.
- No Gerbers until unconnected = 0.
