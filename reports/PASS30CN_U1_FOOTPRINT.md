# PASS30CN (1-3): U1 land pattern → Nordic nRF9161 DK 1.0.0

## Source and verification
- **Downloaded:** `nrf9161-dk---hardware-files-1_0_0.zip` (Nordic blob URL from the order). Used:
  - `PCA10153.../Production files/GERBER/400688.GTL` (top copper)
  - `400688.GTS` (top mask)
  - `PICK_PLACE/400688_Pick_And_Place.csv`: M1 nRF9161-LACAADA, LGA50P1600X1050X104-159N, centre (122.3403, 24.7640) mm, rot 0.
- **Parsed every flash inside the package** (inch, 2.4 format). 159 pads:
  - 126 × R 0.30×0.30 (0.0118 in)
  - 31 × R 0.80×0.80
  - 2 × R 1.60×0.80
  - Mask: 0.40×0.40 / 0.90×0.90 / 1.70×0.90, i.e. **+0.05 mm per side**.
- **Matched our U1** (`Board:nRF9161_LGA_16.0x10.5mm`, footprint-local coordinates) against the DK flashes:
  - The 60 interior pads (0.8 GND, 1.6×0.8, the 0.3×0.3 RF and signal pads) coincide within 0.001 mm.
  - Each of the **99 outer-ring pads** (0.8×0.3 / 0.3×0.8) has exactly one DK 0.30×0.30 flash 0.249–0.250 mm inward, at **±7.75 mm** (x sides) or **±5.00 mm** (y sides).
  - The new centres are snapped to the 0.05 mm grid (max DK deviation 0.001 mm, inch round-off).
  - Copper now ends at ±7.90 / ±5.15, so it sits **fully inside the 16.0×10.5 outline**.
  - Note: the Gerbers carry no pin numbers. Pin mapping is unchanged by construction: each pad keeps its number and net and only moves 0.25 mm inward. The DK pattern is symmetric, so no rotation ambiguity changes any position.
- **Mask:** every U1 pad has a local solder-mask margin of **0.05 mm** (NSMD, matches the GTS). Paste stays 1:1; the assembler applies the 70–85 % reduction (DFM §1.5).
- **U1 position (36, 32), rot 180, and pin mapping are unchanged.**
- **Library:** `libraries/Board.pretty/nRF9161_LGA_16.0x10.5mm.kicad_mod` already had the 7.75 / 0.30×0.30 geometry (the board copy was stale). It is now re-saved from the board footprint, adding the 0.05 mm mask margin.

## Connection repair
- **44 F.Cu track ends** that landed inside an old outer pad were moved to the new pad centre (same net, F.Cu only).
- One redundant **VDD1** F.Cu diagonal, (43.25, 37.0)→(50.52, 37.6) 0.25 mm, now crossed GND pad 1. It was removed; VDD1 stays connected via its 0.4 mm run on y 38. VDD1 track length 80.2 → 73.2 mm.
- **SIM_RST:** its escape ended at (32.71, 26.4) inside the old long pad and now goes to the new centre (32.75, 27.0).
- **VIPPO group A (pads 52–60):** all 9 vias moved from x 27.95 to the new pad centres **x 28.25** (0.30 land = pad). The 6 MIPI/MAGPIO escape tracks were re-anchored to them.
- **VDD_GPIO B.Cu (power):** to fit those vias, the run moved from x 28.50 to x 28.85 (y 19.48–39.65), with 45° joins to the existing via (28.5, 40) and to the y 19.13 run (now starting at x 29.2). Same 0.35 mm width. Clearances: VIPPO land 0.275 mm, GND vias at x 30 0.68 mm, SIM_1V8 via (29.6, 24.8) 0.33 mm.

## RF C1–C7 / lengths
- **C1:** In1 anti-pads unchanged (0.40), slots as accepted.
- **C3:** the pad 60 GND via is now in line with ANT pad 61, 0.20 mm copper gap (same as pad-to-pad).
- **Protected RF copper:** 61/61 identical.
- **Lengths:** MAGPIO0/1/2 18.4/19.2/20.0 mm; MIPI_VIO 22.3; MIPI_SCLK 24.7 (≤50); MIPI_SDATA 27.2. All targets met.

## Gate (zones refilled, kicad-cli DRC + .kicad_dru): PASS
- short 0, clearance 0, crossing 0, hole 0, hole_to_hole 0, copper_edge 0, silk 0, courtyard 0, solder_mask_bridge 0 (one bridge from the VDD1 diagonal was fixed). via_dangling 0. track_dangling 4 (pre-existing).
- **Unconnected: before 17 → after 17** (6 signal + 11 GND). No closed net reopened. No power net opened.
- **VDD_nRF** on In2: 1 piece, 6780.3 → 6780.3 mm².
- **In1 GND:** 2 pieces, 8140.8 → 8142.1 mm².

## Open (6, unchanged)
- SIM_IO, P0.12, P0.25, P0.31: no B.Cu escape (the PASS30CM rip-up was reverted).
- P0.14, P0.18: no legal in-pad via while P0.13 B.Cu runs under the pads.
- These pads now sit at new positions (0.25 mm inward), so any future VIPPO for them must be placed at the new centres.

Images: PASS30CN_BEFORE.png / PASS30CN_AFTER.png (F.Cu+mask+B.Cu+VIPPO). DRC: DRC_PASS30CN_AFTER.json.
