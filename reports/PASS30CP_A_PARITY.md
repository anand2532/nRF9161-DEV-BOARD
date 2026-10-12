# PASS30CP A: schematic parity

## Attribute sync, from the schematic netlist
- C21, C31, C32, J16: DNP on, excluded from BOM. Before this change both were off.
- D7: excluded from BOM. DNP was already on.
- JP1, JP2, TP1–TP20: no longer excluded from BOM, matching the schematic. They stay excluded from position files.
  - **PM flag:** test points and jumpers will now show up in the BOM.

## Footprint names (name only)
- FB5 is now Inductor_SMD:L_0402_1005Metric.
- U3 is now Package_TO_SOT_SMD:SOT-363_SC-70-6.
- Pads were compared with the KiCad 9.0.2 library (number, position, size, shape, drill). They are identical, so the geometry is unchanged and only the FPID changed.
- The stock libraries are not installed on the build box, so DRC raises 2 extra informational lib_footprint_issues (98 → 100). They are not part of the gate.

## U4: not updated
- Board:TI_TPD3F303_USON-8_1.45x1.45mm_P0.4mm.
- All pads (copper, mask, paste) are identical. The only difference is F.Silkscreen: the board copy uses 0.12 mm line segments, the library copy a 0.12 mm rectangle.
- This is silk only and has no electrical or assembly impact.

## U1
- The board copy of Board:nRF9161_LGA_16.0x10.5mm matches the library exactly: all pads and graphics.
- The library has solder_mask_margin 0.05 on all 159 pads, with the DK pattern from e6d1fe0. No fix was needed.

## Parity rerun
- Only net_conflict entries remain, all on NC/RES pads ("unconnected-…"): U1 RES pads, U2/U3/U4 NC, J7/J8/J9/J16. This was expected.

## Gate
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk, courtyard, mask_bridge, via_dangling and track_dangling: all 0.
- Unconnected: 5 (the GND islands from S1, waiver pending).
- In1 GND: 2 pieces, 8179.5 mm². VDD_nRF In2: 1 piece, 6716.8 mm².
