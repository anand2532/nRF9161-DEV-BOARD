# RF / Power review: PASS30CO (branch `vippo` @ bc6d0fc), FINAL

Reviewed: commit bc6d0fc itself (`git show` → /tmp, pcbnew 9 zone refill, kicad-cli DRC with project .kicad_pro/.kicad_dru). Compared with 729a1a3 (PASS30CL, MERGE WITH FIXES). Read-only: no PCB/SCH edits, no commit.

## Verdict: **FAB-OK WITH NOTES (RF/power)**
FX1–FX4 are closed and C1–C7 are met. The RF corner is clean. Protected RF copper is bit-identical to 729a1a3. No RF/power blocker remains. The notes below are cleanups or firmware items, not gates.

## Measured checks
| # | Check | Result | Status |
|---|---|---|---|
| 1 | DRC (refilled) | unconnected **10**, all `Zone [GND] on F.Cu` island pairs. short/clearance/crossing/hole/edge/via_dangling = 0. track_dangling 4 (pre-existing, same as 729a1a3): VDD_GPIO B.Cu ×3 at (70,8), (48.05,5.5), (48.05,3.46), plus **P0.11 B.Cu 4.62 mm at (44.0,29.2) under U1**. 102 lib_footprint_issues (library metadata only). | PASS |
| 1a | F.Cu GND islands (no via; pad-only) | U1.98 1.2 mm² (41.1–41.4, 36.8–40.9); U1.1 3.2 mm² (43.7–49.4, 36.7–37.5); U1.21 2.9 mm² (43.6–46.4, 26.2–27.7); U1.36 0.4 mm² (36.1–36.4, 25.6–27.2); U1.27 0.4 mm² (40.6–40.9, 25.6–27.2); C1/C3 64.5 mm² (53.6–74.8, 24.9–28.3); D2 50.5 mm² (56.7–74.7, 15.9–24.2); R3 70.6 mm² (66.5–76.4, 7.4–22.0); C34 11.8 mm² (73.4–80.2, 44.6–48.3); J5 5.8 mm² (5.4–7.3, 50.4–53.6); J15 2.3 mm² (103.1–104.7, 64.8–67.0). These are 11 pad-only pieces; 10 are reported unconnected, and one is pad-tied elsewhere. **None is at x<29 or under the ANT/AUX/GPS feeds.** The 5 U1-attached slivers sit on the north and east sides of U1. | OK (note) |
| 2 | U1 swap | Centre (36,32), rot 180 unchanged. Outer-ring pads 0.8×0.3 → DK 0.30×0.30, **moved 0.25 mm inward to ±7.75 mm (x sides) / ±5.00 mm (y sides) from the U1 centre**. "7.75" is the **pad-centre offset of the west/east columns**, not a via pitch; the pitch stays 0.5 mm. VIPPO vias moved x 27.95 → 28.25 (= pad centres). **RF pads unchanged: ANT 61 (28.25,31.5), AUX 64 (28.25,33.0), GPS 67 (28.25,34.5)**, still 0.30×0.30. | PASS |
| 2a | VIPPO next to the RF pins (edge to nearest RF pad) | MIPI_SDATA (pad 59) 0.70; MIPI_SCLK 1.20; MIPI_VIO 1.70; MAGPIO0/1/2 2.7/3.2/3.7 mm. **GND VIPPO in pad 60 (28.25,31.0), 0.20 mm from ANT**, sits between SDATA and ANT (C3 met). More GND VIPPO at pads (28.25,29.0) and (28.25,27.0). | PASS |
| 2b | 9 U1 GND-pad vias | All 9 are 0.40/0.25 at x 30/36/42 × y 29/32/35 | PASS |
| 2c | ANT/AUX/GPS connection | RF pads did not move, so no feed stub changed. ANT/AUX/GPS/ANT_FIT/AUX_FIT/GNSS_* track set is identical to 729a1a3 (0 added, 0 removed) | PASS |
| 3 | FX1 P0.00 | 0 In1 segments (was 9; F 12 / B 4 now). 108.6 mm, 4 vias | PASS |
| 3a | In1 GND | 2 pieces: 8168.5 mm² main + 10.7 mm² at J12 (49.9–56.8, 75–77, pre-existing). Total 8142.1 → 8179.3 mm² | PASS |
| 3b | In1 under feeds (±0.5 mm of centreline) | ANT 0.000, AUX 0.000 mm² void (was 0.68/0.68: the P0.00 slot is gone). GPS 0.019 mm² at (22.8, 48.8–49.2), a via antipad outside the keepout, same as 729a1a3. ANT_FIT/AUX_FIT 0 | PASS |
| 4 | FX2 COEX0 | 0 COEX0 objects inside the keepout (was 2: (26.2,38–46.35) and y 38). 131.3 mm, 6 vias | PASS |
| 5 | Keepout x0–29 y26–40, F.Cu+In1 | Non-RF objects: the 6 MIPI/MAGPIO VIPPO barrels at x 28.25 (waived, in-pad) and a pre-existing VDD_GPIO F.Cu via/track end at (28.5,40.0) on the keepout edge. **No In1 signal copper.** Pads J3.4 (8.75,39.25) and C27 are unchanged (legacy). | PASS |
| 10a | In2 VDD_nRF | 1 piece, 6780.3 → 6723.6 mm². By erosion, topology is **identical to 729a1a3** at 2.0/2.5/3.0/3.18 mm width. The main body stays one piece at a 2 mm width. One pre-existing 56 mm² east lobe (79.6–91.3, 63.8–74.0) is joined through a <2 mm neck, identical in 729a1a3. | PASS |
| 10b | Protected RF copper | Tracks are identical. C22/C23/C24/L1/L2/TP1/U3/C27/L4/FB5/J1–J3 have the same position, rotation and pads | PASS |
| 10c | MIPI/MAGPIO | SCLK 24.7, SDATA 27.1 (≤50); VIO 22.3 (≤60); MAGPIO0/1/2 18.4/19.2/20.0 (≤80); COEX1 79.1. All B.Cu, 1 via each. Escapes run **north** (y ≤30.6), 0.81–3.8 mm from the feed copper in XY | PASS |
| 10d | B.Cu GND near U1 | Every B.Cu GND piece around U1 has ≥1 GND via. The 2 new unconnectable slivers are suppressed by `pass30co_island_noFill0/1` (B.Cu nopour), which is OK | PASS |

## SIM answers
- **U4** is a TPD3F303 USON-8 at **0.4 mm pitch**, not 0.65: pads 0.25 wide with a 0.15 mm pad-to-pad gap. The gap is set by the package.
- **"SIM_CLK 0.22"** is SIM_CLK (U4.7 escape) to **SIM_IO** (U4.8 escape), F.Cu track-track at (77.44–77.66, 57.73), just south of the pins. The parallel run is ≤1.13 mm. **Accept as a pin-escape exception.**
- **"SIM_RST 0.37"** is SIM_RST to **SIM_IO**, F.Cu at (79.38, 58.1–58.5). The true minimum there is **0.16 mm**, from a SIM_RST *via* to the SIM_IO track at (79.38,58.35). The parallel run is ≤1.5 mm. **Accept as a pin-escape exception** (same-interface, ≤2 mm). Optional: nudge that via about 0.2 mm east.
- **SIM_1V8 0.28** is to **SIM_IO** on B.Cu, x 31.05 vs 31.35 under U1, parallel 8.85 mm (≤10). The worst point in the same area is a **0.18 mm** SIM_IO via to the SIM_1V8 track at (31.2–31.35, 37.8). Both are inside the U1 fan-out zone. Because the U1 centre did not move, the zone is unchanged: x 26.5–45.5, y 24–39. Both are ≥0.15 mm, and SIM_1V8 is DC. **Within the exception: OK.**
- **Other new-copper SIM proximities, all ≥0.15 and inside the U1 zone:** SIM_IO–COEX0 via 0.21 (37.36,30.86); SIM_IO–P0.18 0.22–0.29 over a 4.2 mm run at (39.6,26.5)→(43.35,24.6); SIM_RST–COEX0 via 0.16 (32.5,25.5); SIM_RST pad U1.43 to P0.25 VIPPO 0.20 (adjacent pads). Outside the zone, the new nets keep ≥0.5 mm: SIM_CLK–P0.25 0.56 mm, 8.9 mm parallel on B.Cu at x 68.1 (≤10, OK).
- **Legacy SIM <0.5 mm outside the zone, unchanged** (flag, not block): SIM_CLK–SIM_RST In1 0.42 mm × 6.0 mm (57–73, 36) and a via 0.21 at (73.3,35.6); SIM_1V8–SIM_RST at C36 0.17–0.31 (71.5, 48–49); SIM_1V8–SIM_VCC 0.20–0.31 at C34/JP2; SIM_CLK–VDD_GPIO 0.21 (71.7,42.3); SIM_CLK In1 vs SWDCLK/P0.22/P0.16/ENABLE vias 0.21–0.36 (y 19–24); SIM_1V8–P0.03/P0.10 0.17–0.5 (41.5,56.6)/(30.7,54).

## GPIO answers
- **P0.18:** 159.0 mm, 6 vias (F 15 / B 21 / In1 3 legacy segments at x 68.9–108, y 28–76).
  - Clearances: ≥12.0 mm to ANT; 0.5 mm under the U1 body (B.Cu only); not on In2; 3.2 mm from the board edge.
  - Closest SIM is SIM_IO, 0.22 mm in the fan-out zone.
  - **OK for plain GPIO.**
- **P0.25:** 93.8 mm, 9 vias (F/B only).
  - Clearances: ≥6.3 mm to ANT; 0.8 mm under U1; not on In2; 3.2 mm from the edge.
  - SIM_CLK 0.56 mm over 8.9 mm (passes).
  - **OK for plain GPIO.**
- **Recommendation (not a blocker):** set both to standard drive (S0S1) in firmware, with slow edges. If either is ever used above about 1 MHz, add a 0603 33 Ω series R footprint at U1.
- **New nets:**

| Net | Length | Vias | Min to RF feed | Min to SIM |
|---|---|---|---|---|
| P0.12 | 54.7 mm | 3 | 5.2 mm | SIM_IO 0.84 |
| P0.13 | 72.8 mm | 4 | 2.3 mm | SIM_IO 0.49 (U1 zone) |
| P0.14 | 82.4 mm | 8 | 14.4 mm | SIM_1V8 0.57; 1.8 mm from the edge |
| P0.31 | 144.5 mm | 6 | 6.5 mm (to GNSS_VBIAS_SRC) | 1.7 mm |
| SIM_IO | 134.4 mm | 6 | 2.06 mm (B.Cu under In1 vs the ANT pad) | – |

  P0.13 crosses the DC GNSS_VBIAS_SRC at (24.96,47.75), B.Cu under F.Cu with In1 between, which is OK. P0.31 and SIM_IO are long, but they are low-speed (SIM ≤5 MHz); OK.
- **Legacy In1 signal tracks** (none in the RF corner; flag only):
  - P0.16: x 44.6–45.55, y 20.8–61.1. It runs along the U1 east edge.
  - P0.19: x 44.25, y 23–63, plus (39.25–44.25, 26.5). This is under the U1 NE corner.
  - SIM_RST: (26.2–32.75, 25.5), (26.2, 17.6–25.5) and y 17.6–18.5 → x 78. The first segment is 0.5 mm north of the keepout.
  - SIM_CLK: (31.25,23.1)→(33.6,19.2)→(57.2,19.55)→(57.2,36)→(73.3,36).
  - P0.05: (47.4,36.5)→(57.05,38.4)→(57.05,74.7)→(18.7,79.4).
  - P0.09: (46.9,29.7)→(59.4,40.2)→(59.5,73)→(28.9,76).
  - P0.17, P0.18, P0.21, P0.24: x 67–116, east half.

## Fix list (none blocks fab from RF/power)
1. **N1 (cleanup):** remove the dangling P0.11 B.Cu stub, 4.62 mm, at (44.0,29.2) under U1. It is an unterminated stub under the modem; small risk, easy fix. If not done before fab, it is acceptable.
2. **N2 (optional):** move the SIM_RST via at (79.38,58.35) about 0.2 mm off the SIM_IO track (0.16 → ≥0.3 mm).
3. **N3 (firmware):** P0.18/P0.25/P0.31/P0.14 at standard drive. Optional 33 Ω series footprints next spin.
4. **N4 (next spin):** move the legacy In1 signal tracks (P0.16/P0.19 at the U1 east edge, SIM_CLK/SIM_RST north of U1, P0.05/P0.09) off In1. Widen the <2 mm VDD_nRF neck to the east lobe (79.6–91.3, 63.8–74.0). Both are unchanged since 729a1a3.
5. **N5:** the 10 F.Cu GND islands are not RF-relevant; DFM decides whether to delete them (pad-only slivers) or leave them.

## Fab gates still open (non-RF)
- DFM sign-off on VIPPO (JLC epoxy fill + cap, flush/recessed ≤25 µm proud), the 0.25/0.40 GND vias, and the C5 exception.
- The 10 GND-island unconnected items: DFM/PM decision to waive or delete.
- Gerbers, drill, pick-and-place and BOM not yet generated; final DRC on the exported fab set; X-ray of U1 on first articles.
- Schematic/ERC parity after the U1 land-pattern swap was not checked here.
