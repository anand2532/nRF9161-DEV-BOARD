# PASS30AG_SUMMARY — one signal in the opened B.Cu corridor

**Timestamp:** 2026-09-30 03:49 IST
**KiCad:** 9.0.2+dfsg-1
**Decision:** **REVERT**
**Net:** SIM_RST
**Unconnected:** 64 → 64 (delta 0)
**Drop ≥ 1:** False
**Short/clearance/crossing after:** 0/0/0
**Corridor:** still free — probe removed, pass30af corridor intact

## Choice

no SIM_* open has two islands on the B slot; probe SIM_RST (next open after continuous SIM_RST_C) inside the corridor only

SIM_RST_C opens before: 0 (continuous if 0).

## Attempt

- edit: {'net': 'SIM_RST', 'layer': 'B.Cu', 'from': [81.8, 44.6], 'to': [97.3, 44.6], 'width_mm': 0.18, 'note': 'single segment strictly inside the opened corridor; no rip'}
- mid: {'unconnected_items': 65, 'shorting_items': 0, 'clearance': 0, 'tracks_crossing': 0, 'hole_clearance': 0, 'track_dangling': 14, 'track_width': 0}
- accept: False reason: unconnected_drop_-1;SIM_RST_open_1->2;probe_does_not_span_an_open
- collide: none. Mid DRC short/clearance/crossing/hole_clearance = 0/0/0/0. The track clears SIM_CLK_C (y=44.05, ~0.37 mm) and SIM_RST_C (y=45.00, ~0.22 mm). It failed because it touches neither SIM_RST island, so KiCad counted a new island: unconnected 64→65, SIM_RST opens 1→2, track_dangling 13→14. Full revert.

## Why the corridor does not close a net

The opened slot is a closed pocket on B.Cu. SIM_CLK_C occupies y=44.05 (x=78.95–97.85) and SIM_RST_C occupies y=45.00 (x=81.80–97.30); a 0.18 mm track at y=44.60 clears them (~0.37 mm and ~0.22 mm) under Default clearance 0.10 mm, but it does not land on two islands of any open net. West exit is blocked by SIM_IO_C B vertical x=78.60 (y=42.50–45.80) and SIM_CLK_C B vertical x=78.95. East exit is blocked by SIM_CLK_C B vertical x=97.85. SIM_RST's nearest B copper ends at x=78.25,y=43.80 (about 3.6 mm from the mouth) and the other island is U1.43 at (32.75, 26.75). SIM_CLK / SIM_IO / SIM_1V8 opens are the U1-to-filter gaps west of x≈78, not this slot. SIM_IO's F spine at x=84 crosses the slot on F.Cu only (east island); a via there would not reach U1.48. No GPIO copper enters the slot (B/F scan x=78–102, y=42.5–47.5 is only SIM_* trunks plus nRESET east of x=101.7).

Nearest island distances (clearance from copper edge to the y=44.60 centerline; touch if ≤ 0.09 mm):

- nearest_SIM_RST: [{"sample": "F (78.00,36.00)-(79.30,36.00)", "dist_B_copper_mm": 3.549, "dist_F_copper_mm": 8.656, "touches_B_track": false, "F_crosses_slot": false}, {"sample": "pad@F (32.75,26.75)", "dist_B_copper_mm": null, "dist_F_copper_mm": 51.797, "touches_B_track": false, "F_crosses_slot": false}]
- nearest_SIM_CLK: [{"sample": "F (71.68,42.40)-(70.90,42.40)", "dist_B_copper_mm": 8.69, "dist_F_copper_mm": 9.908, "touches_B_track": false, "F_crosses_slot": false}, {"sample": "F (31.25,26.75)-(31.25,23.10)", "dist_B_copper_mm": 54.632, "dist_F_copper_mm": 53.209, "touches_B_track": false, "F_crosses_slot": false}]
- nearest_SIM_IO: [{"sample": "F (77.35,56.60)-(77.35,58.60)", "dist_B_copper_mm": 8.3, "dist_F_copper_mm": 0.035, "touches_B_track": false, "F_crosses_slot": true}, {"sample": "F (30.25,26.75)-(30.25,23.10)", "dist_B_copper_mm": 55.554, "dist_F_copper_mm": 54.153, "touches_B_track": false, "F_crosses_slot": false}]
- nearest_SIM_1V8: [{"sample": "F (75.52,44.00)-(75.60,44.10)", "dist_B_copper_mm": 2.802, "dist_F_copper_mm": 2.322, "touches_B_track": false, "F_crosses_slot": false}, {"sample": "pad@F (29.75,26.75)", "dist_B_copper_mm": null, "dist_F_copper_mm": 54.626, "touches_B_track": false, "F_crosses_slot": false}]

P0.22 keep not ripped. No header moves. No Class C move. No Gerbers. One attempt only.

**Stop:** unconnected_drop_-1;SIM_RST_open_1->2;probe_does_not_span_an_open
