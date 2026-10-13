# PASS30CJ: P0.10/12/14/18/25/31 fan-out (branch `finish`)

Freerouting r11: 30 passes. In1 and In2 were exported as power/no-route, and existing copper was locked. Only the target nets were imported.

## Result
- **P0.10: routed.** U1.18 to J12.11, 66.4 mm (F 15.7, B 50.7, In1/In2 0). 5 vias at (31.17, 53.87), (45.51, 28.58), (49.60, 35.67), (48.43, 31.94) and (40.38, 52.15). All are outside the U1, RF and neck keepouts, none is in a pad, and none is within 1 mm of RF copper.
- **P0.31: OPEN.** The router produced only a 1.3 mm partial stub, which was removed.
- **P0.12, P0.14, P0.18, P0.25: OPEN.** The router produced no wiring. The U1 fan-out and the B.Cu channels are congested under the fixed power/RF/SIM keepouts and In1 is no-route.

## Gate (zone-refilled DRC)
- short 0, clearance 0, crossing 0, hole 0, hole_to_hole 0, copper_edge 0, silk 0. via_dangling 0.
- track_dangling 4: unchanged, pre-existing.
- No power net opened. GND islands 11 (unchanged).
- VDD_nRF on In2 is one piece, 6801.7 mm².
- No closed net reopened.
- No SIM copper within 0.5 mm.

## Open nets (12)
- SIM_IO: no 0.5 mm path (PASS30CI).
- P0.12, P0.14, P0.18, P0.25, P0.31: no route found.
- MAGPIO0/1/2 and MIPI_SCLK/VIO/SDATA: west column, routing not allowed.

Images: PASS30CJ_BEFORE.png, PASS30CJ_AFTER.png. DRC: DRC_PASS30CJ_AFTER.json.
