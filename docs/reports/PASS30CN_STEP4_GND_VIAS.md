# PASS30CN step 4: U1 GND-pad vias 0.30/0.60 → 0.25/0.40 (RF approved)
- **Changed:** all 9 GND vias at x 30/36/42, y 29/32/35 (U1 0.8×0.8 GND pads), drill 0.30 → **0.25**, land 0.60 → **0.40** (annular 0.075). All 9 kept, same positions and net.
- **.kicad_dru:** new rule `VIPPO_B_size` (A.Hole == 0.25mm: via_diameter ≥0.4, hole ≥0.25, annular ≥0.075). No other via on the board uses a 0.25 drill.
- **Gate (refilled):** PASS
  - short / clearance / crossing / hole / hole_to_hole / courtyard 0; track_dangling 4 (pre-existing).
  - Unconnected 17 → 17 (same 6 signal + 11 GND).
- **VDD_nRF In2:** 1 piece, 6780.3 → 6784.6 mm² (smaller anti-pads).
- **In1 GND:** 2 pieces, 8142.1 mm².
- **RF and lengths:** RF copper is untouched; lengths are unchanged.
