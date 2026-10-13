# PASS30CI: SIM_IO / SIM_1V8 routing (branch `finish`)

## Result
- **SIM_1V8: routed.** F.Cu 0.2 mm escape from U1.49 (29.75, 26.75) to (29.75, 24.8) to via 0.5/0.3 at (29.6, 24.8), then B.Cu east (Freerouting r9). Total 77.3 mm: F 32.8, B 44.6, 6 vias, no In1/In2 copper. Reaches C33, JP2.1, U4.5 and C38.
- **SIM_IO: OPEN.** Freerouting found no path at 0.5 mm SIM clearance from the (30.25, 23.8) via to the SIM side (r9 at 20 passes, and r10 at 30 passes with SIM_1V8 in place). The escape neck and via were removed so nothing is left dangling. Next options: relax SIM_IO clearance outside the fan-out zone (not authorised), or rip up neighbours.
- **The 0.15 mm exception was used only in the fan-out zone.** It covers the SIM_IO/SIM_1V8 escape necks between y 24.8 and 26.75 and the SIM_1V8 via 0.37 mm from SIM_RST on In1 at y ≈ 24.8. No other SIM spacing is under 0.5 mm.
- **Vias:** none in or partly in a pad, none in the RF keepout, and none within 1 mm of RF copper.
- **100 nF on SIM_1V8:** C33 (100nF) pad 1 at (75.52, 44.0) is **48.9 mm** from U1.49. That is NOT within 3 mm. It sits at the SIM card / JP2 end. No footprint was moved, as instructed. A 100 nF cap at U1.49 needs a schematic or placement decision.

## Gate (zone-refilled DRC)
- short 0, clearance 0, crossing 0, hole 0, hole_to_hole 0, copper_edge 0, silk 0. via_dangling 0.
- track_dangling 4: unchanged, the known VDD_GPIO mid-tapped stubs plus P0.11.
- No power net opened. GND islands 11 (unchanged).
- VDD_nRF on In2 is one piece, 6805.1 mm².
- No closed net reopened.
- B.Cu GND under U1: the SIM_1V8 B.Cu run at x = 31.05 split piece A. The new pieces are 56.6 mm² with vias at (30, 20/29/32/35/40) and 88.1 mm² with a via at (30, 10). Both are stitched.

## Open nets (13)
- SIM_IO: no route at 0.5 mm.
- MAGPIO0/1/2 and MIPI_SCLK/VIO/SDATA: west column, routing not allowed.
- P0.10, P0.12, P0.14, P0.18, P0.25 and P0.31: PASS30CJ.

Images: PASS30CI_BEFORE.png, PASS30CI_AFTER.png (F.Cu + B.Cu). DRC: DRC_PASS30CI_AFTER.json.
