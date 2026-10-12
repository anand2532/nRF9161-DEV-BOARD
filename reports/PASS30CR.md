# PASS30CR (vippo, from 3eab055; local commits, not pushed)

## 1. U4 library footprint (commit e40ca9d, library only)
- `libraries/Board.pretty/TI_TPD3F303_USON-8_1.45x1.45mm_P0.4mm.kicad_mod`: the F.SilkS rectangle (0.12 mm) is replaced by the board copy's two 0.15 mm segments, (-0.85,0.13)→(-0.85,-0.13) and (0.85,-0.13)→(0.85,0.13).
- Pads, library vs board: identical. Checked all 9: number, position, size, shape, layers, mask/paste margins, rr-ratio.
- All non-text graphics are identical.
- DRC lib_footprint_mismatch for U4 went from 1 to **0**.

## 2. Silk spacing ≥0.15 mm (silk only)
**Method.** DRC run on a /tmp copy with `min_silk_clearance` = 0.15.
- 3eab055: **32 pairs** under 0.15 mm. DFM's checklist cites 27, but its full list isn't in fab-pass-3eab055, so every pair found at 0.15 was fixed.
- Worst pairs: J5 "GND" vs J5 outline at 0.036, J2 "GND" vs J2 outline at 0.036, P0.11 vs J12 outline at 0.047, ADC vs P0.13 at 0.054, U1 ref vs U1 outline at 0.088.
- **After: 0 pairs under 0.15 mm**, so the minimum is ≥0.150 (DRC_PASS30CR_SILK015.json).

**Fixes** (1.0 mm text / 0.15 mm stroke kept; labels stay next to their pins):
- **J14 and J15 (1.27 mm pitch):**
  - Stacked 1.0 mm labels can only be 0.12 mm apart.
  - Odd pins are now labelled on the left, even pins on the right: J14 MAGPIO1 / MIPI_VIO / MIPI_SDATA, J15 COEX1 / GND / GND.
- **J8 (2×5, 1.27 mm):**
  - The same 0.12 mm limit applies, and TP8 blocks staggering, so the per-pin labels were replaced by a legend top-left of J8.
  - Legend text: "J8: 1 3V3 2 SWDIO 3 GND / 4 SWDCLK 5 GND 6 P0.22 / 8 nRESET 10 GND 7,9 NC".
  - The pin-1 mark is on the footprint.
- **J3 and J6:** ANT_FIT / GNSS_ANT are now centred above the connector, and GND is left of it.
- **Small nudges (≤0.2 mm):**
  - The J2 and J5 GND labels.
  - The J2 right-hand GND.
  - The J1 VIN_IN and GND labels.
  - The U1, TP18, J10, J12 and J13 refs.
  - ADC moved up 0.25 mm.
- **J12:** P0.11 is back in line with the other row labels (y 74.26, left-justified like its neighbours). "GPIO" merged into the J12 legend as "GPIO P0.00-15".
- **Banner:** "LTE-M / NB-IoT / DECT NR+ / GNSS" moved to open space at (55.0, 54.5) to free the top-left for the J8 legend.

## 3. RF note
- **Committed:** at (30.0, 67.0), F.SilkS, 1.0/0.15. It is in 3eab055 and unchanged here.
- **Bbox:** x 1.30–58.70, y 66.15–67.85, just above the J12 row labels.
- **Copper check:** its bbox meets no ANT, GNSS_ANT, ANT_FIT or GNSS_VBIAS track or pad, and no rule area. It sits far from the RF section: J2/J3/J5/J6 are at x ≤ 12, y 29–62; the GNSS trunk is at x 16, y 35–60.

## Gate (final)
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk overlap / over copper / edge, courtyard, mask_bridge, via_dangling and track_dangling: all **0**.
- **Unconnected: 0.**
- lib_footprint_mismatch: 0. lib_footprint_issues: 100 (informational; the stock libs aren't installed on the build box).
- In1 GND: 2 pieces, 8178.5 mm². VDD_nRF: 1 piece, 6708.2 mm².
- Copper diff vs 3eab055: none (no segment, via or zone changes).

## PNG
reports/PASS30CR_FINAL_TOP.png
