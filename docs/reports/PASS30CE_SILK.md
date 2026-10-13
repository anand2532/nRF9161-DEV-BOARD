# pass30ce — silkscreen clean-up (branch `autoroute-gpio`, on top of pass30cd a2c20e1)

Only text was changed: footprint reference fields and board-level F.Silkscreen texts (pin labels and titles). Footprints are unchanged (position, rotation, side). Copper is unchanged: every track and via is identical and zones are untouched. Scripts are in scripts/pass30ce/ (silk.py, then silk2.py). The full change list is in silk_changes.json.

## Method
- All 103 reference designators set to 0.8 mm high, 0.15 mm stroke, 0°. None needed 0.6 mm. Refs that collided were placed beside their footprint's bounding box (N/S/W/E), then searched outward in 0.2 mm steps.
- Board texts (pin labels and similar) kept their size where possible. Three dropped to 0.6 mm where it was dense. They were searched outward from their original spot at the original angle or rotated 90°. Long titles were allowed a wider search.
- Collision model: text bbox + 0.1 mm against footprint silk graphics, other texts, and pads (+0.05 mm mask). Stay ≥0.3 mm inside the board edge.

## Gate (DRC, zones refilled)
| check | before | after |
|---|---|---|
| silk_overlap | 145 | **0** |
| silk_over_copper | 35 | **6** |
| silk_edge_clearance | 0 | 0 |
| electrical (unconnected 29, short/clr/cross/hole 0/0/0/0, hole_to_hole 1, copper_edge_clearance 5, dangling 35/10) | — | identical |

The 6 left on silk_over_copper are **footprint silk graphics**, not text: the U1 outline segments at its 4 corners (5 items) and the U4 outline rectangle (1). Fixing them means editing footprint silk, which is outside the "move/rotate reference text only" rule. **Needs approval** to trim those segments, or a footprint-library fix.

## Hidden refs
None. No reference sits under U1, and every ref found a free spot.

## Changes
- Refs changed: 103 (all are now 0.8 mm / 0°). Big moves: J12 and J13 ≈27 mm (ref now sits beside the long header body), J7 16.5, U1 13.0, J17 12.5.
- Board texts changed: 114. Title "nRF9161 DEVELOPMENT BOARD" moved 27 mm. **Pin labels moved >2.5 mm**: MIPI_SCLK, MIPI_VIO, GND, SIM_RST_C (5.0), MAGPIO0 4.8, MAGPIO2 4.4, SWD 4.2, SWDCLK 4.0, P0.22 3.8, the subtitle 3.8, SWDIO/GND 3.6, 3V3 3.4, SIM_CLK_C 3.2, VIN_IN 3.2, SIM_VCC/GNSS_ANT/P0.10 3.0, and several 2.6–2.8 (J12/J13/J18 row labels staggered). **Check in the PNG that the labels still read next to the right pin.**

PNGs: reports/PASS30CE_BEFORE_FSILK.png, PASS30CE_AFTER_FSILK.png, PASS30CE_BEFORE_BSILK.png, PASS30CE_AFTER_BSILK.png (silk + mask + edge).
