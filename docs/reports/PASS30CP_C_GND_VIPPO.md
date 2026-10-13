# PASS30CP C: GND VIPPO in U1 pads 36/27/21/98 (PM decision)

## Vias added
Four 0.20/0.30 GND vias, copied from the existing group A via (tented, through), centred in the 0.3 mm pads:

| Pad | Via (mm) |
|---|---|
| U1.36 | (36.25, 27.0) |
| U1.27 | (40.75, 27.0) |
| U1.21 | (43.75, 27.0) |
| U1.98 | (41.25, 37.0) |

- Each has a 0.25 mm-radius ring on User.1 (VIPPO).
- RF feeds (ANT, GNSS_ANT, ANT_FIT, GNSS_VBIAS tracks and pads) are more than 9 mm from all four vias, so none was skipped.

## Local reroutes needed for clearance (non-RF, non-SIM nets)
- **VDD2 (B.Cu):** the loop-back via (44.72, 25.9) → (43.25, 26.75) → east was replaced by (44.72, 25.9) → (45.57, 26.75) → (52.22, 26.75). The same 0.25 mm width was kept.
- **P0.01 (B.Cu):** the diagonal from its via (40.25, 38.32) now runs (40.63, 38.32) → (44.60, 34.35) → the existing joint at (44.43, 34.14). This gives hole clearance to the pad-98 via.

## VIPPO count
- Before: 25 (0.20/0.30 ×16, 0.25/0.40 ×9).
- Now: **29** (0.20/0.30 ×20, 0.25/0.40 ×9).
- The fab note (DFM_VIPPO_NOTE.md) and the board VIPPO text are updated.
- Pre-existing gaps, still open:
  - The fab note previously listed 18. The 7 signal VIPPO (pads 20/23/24/29/42/48/89) are now documented as group A2.
  - User.1 rings exist for group A and C only (13). Groups A2/B are identified by drill tool.

## Gate
- All 0.
- Unconnected: 1 (the J5.2 island).
- In1 GND: 2 pieces, 8179.5 mm². VDD_nRF: 1 piece, 6714.2 mm² (the new via antipads).
