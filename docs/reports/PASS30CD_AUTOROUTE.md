# pass30cd — Freerouting re-run after the RF reject of pass30cc (branch `autoroute-gpio`)

Restore commit 1f817b3 sets the board back to main 8628f07 (blob 0e1d4fa). 3e2a15f is kept in history. Not pushed; main untouched.

## Set-up (Freerouting 1.9.0, `scripts/pass30cd/export2.py`)
- Signal layers: **F.Cu and B.Cu only**. In1 (GND reference) and In2 (VDD_nRF) are declared power layers, so 0 new copper on In1/In2.
- All existing copper is `fix`. RF keepout x0–24.2/y20–64 on all layers, plus x0–29/y26–40 on F.Cu+In1. VDD_nRF In2 neck x53–60/y12–22. Sealed B.Cu pocket. Via keepout over the U1 area x27.6–44.4/y26.35–37.86.
- Classes: default 0.18/0.15. Via 0.50/0.30 only. POWER clearance 0.20. **SIM** (SIM_CLK, SIM_RST, SIM_IO) clearance 0.50. RF_50OHM plus GNSS_VBIAS/GNSS_VBIAS_SRC clearance 1.0 (DFM a).
- Two runs: r6 (26 nets) and r7 (the 16 left). r7 only produced MIPI_VIO at 143 mm, over its 60 mm limit, so it was discarded.
- Imported only nets that were open. Every DRC was run on a zone-refilled copy (DFM c).

## Length targets
| net | target | result |
|---|---|---|
| MIPI_SCLK | ≤50 | r6 gave 161.1 mm → copper removed, left open |
| MIPI_VIO | ≤60 | r7 gave 143.0 mm → copper removed, left open |
| MAGPIO0, MAGPIO2, COEX1 | ≤80 | no route found on F/B |

## Per-net new copper (kept)
| net | mm | F | B | vias |
|---|---|---|---|---|
| P0.23 | 137.3 | 100.7 | 36.6 | 1 |
| P0.21 | 130.7 | 107.9 | 22.8 | 1 |
| P0.28 | 102.7 | 69.9 | 32.8 | 2 |
| P0.30 | 94.4 | 53.2 | 41.2 | 2 |
| P0.29 | 92.2 | 51.1 | 41.1 | 4 |
| P0.26 | 86.7 | 34.4 | 52.4 | 4 |
| P0.03 | 71.1 | 21.2 | 49.9 | 2 |
| P0.01 | 55.3 | 17.8 | 37.6 | 3 |
| VDD_GPIO | 3.4 | 3.4 | 0 | 0 |
| GND (pad-90 dog-bone + stitch) | 0.9 | 0.9 | 0 | 6 |
| **total** | **774.7** | | | **25** |
No target was set for P0.xx. P0.21 and P0.23 are long (131/137 mm), mostly on F.Cu.

## Post-import checks (scripts/pass30cd/newcheck.py)
- 0 new In1/In2 copper. 0 vias in the U1 area (0.25 mm margin), in keepouts, or in pads. 0 vias within 1.0 mm of ANT/AUX/GPS/GNSS feed or GNSS_VBIAS copper.
- No new copper within 0.5 mm edge-to-edge of SIM_CLK/SIM_RST/SIM_IO, so any parallel run at <0.5 mm is 0 mm (limit 10).

## DFM addendum
- (a) Done in the DSN class and verified after import.
- (b) Dangling cleanup was greedy and one item at a time. An item was only removed if no net's open count changed and no rule count rose. Removed: **23 vias + 30 tracks** on rippable nets (P0.xx, MAGPIO, MIPI, COEX, SIM_1V8/SIM_IO stubs; list in scripts/pass30cd/dangling_result.json). Kept: 1 (a P0.11 B.Cu stub whose removal reopens P0.11). **Not removed: 44 items on locked nets** (ENABLE, VDD*, VIN*, DEC0, SIM_VCC, SIM_RST, SIM_CLK_C, GNSS_VBIAS, SWD, nRESET). The spec keeps that copper fixed, and GNSS_VBIAS is RF-protected. A blind first attempt that also removed them broke VDD_GPIO, and was reverted. Dangling after: 35 vias, 10 tracks (from 61/13).
- (c) Zones refilled before every DRC.
- (d) Pad 96 (P0.01): **FIT.** A dog-bone to a via at y ≥38.15 (fully outside the U1 area) clears foreign copper by ≥0.15 mm, power by ≥0.20, SIM by ≥0.5, RF by ≥1.0, and hole-to-hole by 0.25. Freerouting closed P0.01 from pad 96 with no rule breach. Pad 49 (SIM_1V8): **NO-FIT.** Every via spot outside U1 breaks the 0.5 mm SIM clearance (SIM_RST In2/F, SIM_IO) or clearance to VDD_GPIO/P0.02/COEX0. Pads 54/59 left for VIPPO.

## GND
- The new 3.8 mm² F.Cu sliver south of U1 (x36.6–37.4, y36.8–42.9) was removed with a no-fill rule area, `pass30cd_sliver_noFill`. U1 pad 90 (GND) was cut off by the new routes, so it got a 0.9 mm F.Cu dog-bone to a GND via at (37.25, 38.15).
- The new 16.3 mm² F.Cu GND piece east of U1 (x45.9–50.2, y28.3–36.6) got 5 GND stitch vias at ≥2 mm spacing: (49.24,28.54) (49.34,30.94) (46.24,32.04) (48.24,32.64) (48.54,35.44). All are outside the keepouts and the U1 area.
- The pass30cc slivers (In1, B.Cu 4.8 mm²) do not exist here, because no In1 routing was done.

| layer | pieces before | after | area before mm² | after |
|---|---|---|---|---|
| In1 GND | 3 | **2** | 8074.4 | **8117.5** |
| F.Cu GND | 20 | 24 | 7218.7 | 6882.9 |
| B.Cu GND | 18 | 19 | 6920.9 | 6339.5 |
| In2 VDD_nRF | 1 | 1 | 7341.6 | 7350.7 |
In1 has 2 pieces instead of 3 because removing dangling vias merged the 302 mm² piece into the main plane (8106.8 + 10.7 mm²). DRC GND-unconnected: 12 → 12.

## Gate
- non-GND opens 26 → **17**. Unconnected 38 → 29.
- short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1.
- All power nets 0 opens (VDD_GPIO newly closed). VDD_nRF has 1 piece. No closed net reopened.
- Vias 337 → 339 (+25 new, −23 dangling). Track +774.7 mm new, total 6360.4 → 7056.2 mm.

## Still open (17)
- Over length target, removed: MIPI_SCLK (161 mm), MIPI_VIO (143 mm).
- Trapped U1 pads, waiting for VIPPO: MAGPIO1 (p54), MIPI_SDATA (p59), SIM_1V8 (p49, dog-bone no-fit).
- No F/B path with In1/In2 closed, the extended RF keepout, SIM 0.5 mm and RF 1.0 mm: MAGPIO0, MAGPIO2, COEX1, P0.10, P0.12, P0.14, P0.18, P0.24, P0.25, P0.27, P0.31, SIM_IO.

PNGs: reports/PASS30CD_BEFORE.png, reports/PASS30CD_AFTER.png.
