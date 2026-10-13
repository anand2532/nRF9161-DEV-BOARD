# PASS30CP step 4: centre the group B GND vias on U1 pad 103

Six GND vias (0.40/0.25) were moved onto their pad centres:
- (30/36/42, 29.0) moved to y 28.8.
- (30/36/42, 35.0) moved to y 35.2.

At (42, 28.8) the via then violated clearance to the P0.12 B.Cu track. P0.12 was rerouted locally from its VIPPO at (43.75, 27.5):
- New path: (42.9, 28.35), (42.9, 29.0), (42.45, 29.45), (41.5, 29.45), then the existing joint at (41.5, 28.75), which keeps its existing run.
- This replaces 4 short segments.
- P0.12 is not an RF or SIM net.

## Gate
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk, courtyard, mask_bridge and via_dangling: all 0.
- Unconnected: 5 (GND-pad islands, handled in later commits).
- In1 GND: 2 pieces, 8179.5 mm². VDD_nRF: 1 piece, 6716.8 mm².
