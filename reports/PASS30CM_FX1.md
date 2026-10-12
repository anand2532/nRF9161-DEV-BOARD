# PASS30CM step 1 — FX1: P0.00 off In1 (fab blocker)
- **Removed:** every P0.00 In1 track: the RF-corner run x 25.2 / y 23.5–37.4, the y 37.4 and x 39.75 legs, the x 25.0 / y 15.2 / x 68.7 / y 16.4 / x 80.14 run, and the now-useless R10 via (80.14, 19.13). **P0.00 has no In1 copper anywhere now.**
- **New route** (grid router, rule-checked): U1.95 → existing via (39.75, 41.1).
  - B.Cu (39.75, 41.75) → (43.5, 43.3), via.
  - F.Cu → (46.2, 40.6) → (57.75, 40.6) → (63.9, 34.45) → (69.15, 34.45) → (73.05, 29.75), via.
  - B.Cu → (77.7, 25.1), via.
  - F.Cu → (77.7, 21.6) → R10 junction (80.14, 19.13).
  - 0.18 mm, 54.2 mm new copper, 3 new vias 0.6/0.3.
  - Entirely east of x 39.7 and south of / outside U1: nothing in the RF keepout (x<29, y 26–40), nothing under U1.
- **Repair:** the F.Cu run split the GND F.Cu pour piece (x 50–76, y 29–42) into 3. Three GND stitch vias 0.6/0.3 were added at (68.5, 37.5), (55.4, 39.0) and (52.1, 36.8). GND islands stay at 11.

| Gate (refilled) | Before | After |
|---|---|---|
| In1 GND | 2 pieces, 8140.8 mm² | **2 pieces, 8206.5 mm²** (+65.7, the RF-corner void is gone) |
| VDD_nRF In2 | 1 piece, 6784.6 | 1 piece, 6781.0 |
| Unconnected | 17 | 17 (same 6 signal + 11 GND) |

short/clearance/crossing/hole/hole_to_hole/courtyard/copper_edge/silk/mask_bridge are all 0. via_dangling is 0. track_dangling is 4 (pre-existing). P0.00 stays closed.

PNGs:
- `PASS30CM_FX1_BEFORE.png` / `_AFTER.png` (In1)
- `PASS30CM_FX1_ROUTE.png` (F+B)
