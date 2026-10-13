# PASS30CQ silk: labels placed by hand (silk only)
No copper, footprint, via or zone changes; only text and reference-field positions. Text stays at 1.0 mm height / 0.15 mm stroke.

## What changed
### J8 (SWD)
- Odd-pin labels sit left of the header, right-aligned to each pin row: 3V3 / GND / GND (pins 7 and 9 are NC).
- Even-pin labels sit right of the header: SWDIO / SWDCLK / P0.22 / nRESET / GND.
- The J8 ref is now above the header, next to "SWD".

### JP1
- VIN_FILT is left of pad 1. VDD_nRF is below-right of pad 2. The JP1 ref moved left.
- The F1 and TP8 refs were moved to make room.

### J7 / SIM ("short pin numbers + legend")
- Removed 18 labels:
  - 11 "GND" labels on the shield pads
  - the 2 SIM_CD labels inside the holder
  - SIM_IO_C, SIM_VCC, SIM_RST_C and SIM_CLK_C around the holder
  - "PDM"; it became part of "I2S/PDM", see J16
- Added "C1" and "C5" next to the first contact of each row.
- Added the legend "J7: C1 VCC C2 RST C3 CLK / C5 GND C6 NC C7 IO / CD = SIM_CD SH = GND" in the open space below-left of J7.
- "SIM" is centred above the holder.
- The JP2 labels are now vertical: SIM_1V8 by pad 1, SIM_VCC by pad 2.

### J14 (moved here)
- MAGPIO0/1/2, MIPI_VIO, MIPI_SCLK and MIPI_SDATA had been orphaned near J7/J11, at about x 102–107.
- Those nets are only on J14, so the labels now sit next to J14 pins 1–6.

### J16
- Full net labels, horizontal, left of each pin: P0.10 / P0.11 / P0.12 / P0.09 / 3V3 / GND.
- Header label "I2S/PDM", plus "J16" and "DNF" above the header.

### J9, J10, J11 and J17 (no room for full names)
- Labels are short pin numbers (06/07/05/04, 21–24, 30/31, 17/18), plus 3V3/GND.
- A vertical legend "nn = P0.nn" sits beside each block.
- The J9 ref is now vertical at the board edge; the TP9 ref moved below TP9.

### J15
- Horizontal labels COEX0 / COEX1 / COEX2 / GND / 3V3 / GND, one per pin.

### Banner, title and RF note
- Placed in open space:
  - "LTE-M / NB-IoT / DECT NR+ / GNSS" at the top left
  - "nRF9161-DEV-BOARD" at the top centre
  - The RF note at the bottom left, above J12

## Checked by eye
In the renders, every label reads as a separate word, sits beside its own pin, and stays off outlines and pads.

## Gate
- silk_overlap, silk_over_copper and silk_edge: 0.
- All electrical checks 0. Unconnected: 0.
- In1 GND: 2 pieces, 8178.5 mm². VDD_nRF: 1 piece, 6708.2 mm². Electrical results are the same as 1488420.

## PNGs
- reports/PASS30CQ_SILK_AFTER_TOP.png
- reports/PASS30CQ_SILK_AFTER_BOTTOM.png (B.Silk has no items)
- reports/PASS30CQ_SILK_AFTER_SIM.png
- reports/PASS30CQ_SILK_AFTER_J8.png
- reports/PASS30CQ_SILK_AFTER_J15J16.png
