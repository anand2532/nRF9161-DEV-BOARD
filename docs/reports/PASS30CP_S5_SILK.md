# PASS30CP step 5: silk to JLC limits

## Changes
- **Footprint silk:** all 257 graphics went from 0.12 to 0.15 mm stroke.
- **Board-level silk:** the 3 graphics went from 0.10 to 0.15 mm.
- **Refs:** all 103 visible refs went from 0.8/0.15 to 1.0/0.15 (height/stroke).
- **Board labels:** all 157 went to ≥1.0 mm height and ≥0.15 mm stroke (previously 0.6–0.9 / 0.12). The 3 labels already at 1.1/0.165 were unchanged.
- **B.Silk:** has no items.
- **U1 ref overlap at (36.1, 38.7):** fixed by moving the ref +0.1 mm in y.
- **Refs moved to F.Fab:** NONE. All refs fit at 1.0 mm.
- **Visibility:** all connector, LED, switch and TP labels stay on silk.

## Re-placement after the size increase
- 65 labels overlapped after resizing. They were re-placed automatically (search radius ≤2.5 mm, 90° rotation allowed) with a few manual fixes. Positions are in /tmp/rt/s5b_res*.json.
- The two banner texts moved:
  - "LTE-M / NB-IoT / DECT NR+ / GNSS" moved from (63.8, 3.2) to (31.4, 3.0) (top left).
  - "nRF9161-DEV-BOARD" moved to (61.9, 3.5).
- GPIO was moved to y 69.15.
- **Recommendation:** a manual cosmetic review of the dense pin-label areas (SIM/J7, J8 SWD, J15/J16 headers).

## PNGs
- reports/img/PASS30CP_S5_FSilk_before.png and reports/img/PASS30CP_S5_FSilk_after.png.
- reports/img/PASS30CP_S5_BSilk_before.png and reports/img/PASS30CP_S5_BSilk_after.png.

## Gate
- silk_overlap, silk_over_copper and silk_edge: 0.
- short, clearance, crossing, hole, hole_to_hole, copper_edge, courtyard, mask_bridge and via_dangling: 0.
- Unconnected: 5.
- In1 GND: 2 pieces, 8179.5 mm². VDD_nRF: 1 piece, 6716.8 mm².
