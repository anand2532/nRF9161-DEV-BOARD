# PASS30CM: status (stopped by the PM plan change, U1 footprint replacement)

## Committed (this commit): docs only, no copper change
- `.kicad_dru`: added the RF C5 exception text ("via barrels in U1 pads 52-60 only").
- `reports/DFM_VIPPO_NOTE.md` §1.4: 9 vias in U1 pads 52-60, marker layer "VIPPO" (User.1).
- Board unchanged from 729a1a3, so the gate is identical to PASS30CL: short, clearance, crossing, hole, hole_to_hole, copper_edge, silk and courtyard all 0. 17 unconnected (6 signal + 11 GND). VDD_nRF is one piece, 6780.3 mm². In1 GND is 2 pieces, 8142.1 mm².

## Worked on but NOT committed (reverted; it would be undone by the U1 land-pattern change)
- **Rip-up under U1:** P0.13 (U1.23 to (32.2,38)), COEX0 (R4 to U1.93 link incl. the F.Cu y 22 run), SWDCLK (U1.33 to via (34.2,19.8)).
- **SIM_1V8 escape rework:** B.Cu via (29.6,24.8) → x 29.2 → y 37.5 → (31.05,39.85), 0.25 mm. SIM_1V8 stayed closed and C40 was kept.
- **New VIPPO vias:** SIM_IO (30.25,26.75), P0.12 (43.8,27.5), P0.25 (33.25,26.75), P0.31 (36.75,37.05), P0.14 (42.25,26.95), P0.18 (39.75,26.95).
- **Result of that placement:** DRC was clean (0 short/clearance/hole) after the rip-up. So **P0.14 and P0.18 do get a legal in-pad via once P0.13 B.Cu (y 27.0) is ripped.** The locked P0.19 In1 / P0.20 In2 runs stay clear at a +0.20 mm offset (y 26.95). This only holds for the old pad geometry; re-check it after the footprint change.
- The Freerouting run (r13) did not finish before the plan change, so the three ripped nets were never closed again. The whole rip-up was reverted under "revert any part that fails".
- **FX1 (P0.00 off In1) and FX2 (COEX0 y 38 run): not done.** Both connect to U1 pads (P0.00 at U1.~(39.75,37.4), COEX0 U1.93) and the footprint change will affect them, so they move to after PASS30CN.
- FX3/FX4 (optional GND vias): not done, deferred with FX1.

## Open (unchanged, 6)
- SIM_IO, P0.12, P0.25, P0.31: no B.Cu escape without the rip-up above.
- P0.14, P0.18: a via spot exists only after the P0.13 rip-up.
