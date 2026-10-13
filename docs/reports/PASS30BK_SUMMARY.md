# PASS30BK_SUMMARY — SIM_1V8 U1.49 to far F.Cu track

**Timestamp:** 2026-09-30 18:16 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** SIM_1V8
**Pair:** U1.49 ↔ F.Cu (72.90, 44.10)–(72.90, 48.60) only
**Git HEAD:** `b91e9d5acd79f3dedac131b4c7b87d38c51f7bac`
**PCB blob at start:** `7bcfe5791b156e426a2a0affefe938be4d39f8e6`
**PCB blob at end:** `7bcfe5791b156e426a2a0affefe938be4d39f8e6`
**sha1sum at start:** `c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40`
**sha1sum at end:** `c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40`
**End blob matches start:** True
**Ends already one island:** False
**Pad-edge:** 46.030849 mm (census 46.031)
**U1.49 island layers:** ['F.Cu']
**Far track:** F.Cu (72.900,44.100)-(72.900,48.600) w=0.400
**Far island layers:** ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
**Far through-vias:** [{'name': 'via@80.000,47.126', 'xy': [80.0, 47.126], 'width_mm': 0.6, 'drill_mm': 0.3}, {'name': 'via@76.170,45.126', 'xy': [76.17, 45.126], 'width_mm': 0.6, 'drill_mm': 0.3}]
**Far island F.Cu-only:** False
**Joined:** nothing
**SIM_IO flank candidates:** [{'x': 29.71, 'y0': 26.4, 'y1': 22.6, 'stored_x_nm': 29710000, 'copper_clearance_mm': 0.15, 'center_distance_mm': 0.5399999999999991, 'under_0_15': False, 'on_gate_0_150': True, 'meets_gate': False}, {'x': 29.7, 'y0': 26.4, 'y1': 22.6, 'stored_x_nm': 29700000, 'copper_clearance_mm': 0.16, 'center_distance_mm': 0.5500000000000007, 'under_0_15': False, 'on_gate_0_150': False, 'meets_gate': True}, {'x': 29.69, 'y0': 26.4, 'y1': 22.6, 'stored_x_nm': 29690000, 'copper_clearance_mm': 0.17, 'center_distance_mm': 0.5599999999999987, 'under_0_15': False, 'on_gate_0_150': False, 'meets_gate': True}]
**COEX0 candidates:** [{'x': 29.71, 'y0': 26.4, 'y1': 21.4, 'stored_x_nm': 29710000, 'copper_clearance_mm': 0.0, 'center_distance_mm': 0.09999999999999787, 'under_0_15': True, 'on_gate_0_150': False, 'meets_gate': False}, {'x': 29.7, 'y0': 26.4, 'y1': 21.4, 'stored_x_nm': 29700000, 'copper_clearance_mm': 0.0, 'center_distance_mm': 0.10999999999999943, 'under_0_15': True, 'on_gate_0_150': False, 'meets_gate': False}, {'x': 29.2, 'y0': 26.4, 'y1': 21.4, 'stored_x_nm': 29200000, 'copper_clearance_mm': 0.22, 'center_distance_mm': 0.6099999999999994, 'under_0_15': False, 'on_gate_0_150': False, 'meets_gate': True}]
**x used:** none. x=29.71 rejected (exactly 0.150 mm, on the gate). x=29.70 rejected as a through-run (clears SIM_IO at 0.160 mm, crosses SIM_RST, hits COEX0).
**West-slot best In1 vertical:** {'x': 26.01, 'foreign_exact': 0.01, 'foreign_mm': 0.01, 'foreign_item': {'net': 'SIM_RST', 'item': 'trk (26.20,25.50)-(26.20,17.60)'}, 'power': None, 'body': False}
**Rejected north-run crossings:** 1 ([{'segment': [[29.7, 26.4], [29.7, 22.6]], 'locked_net': 'SIM_RST', 'locked_layer': 'In1.Cu', 'locked': [[32.75, 25.5], [26.2, 25.5]], 'proper_interior': True, 'collinear_stack': False, 'interior_sample_hits': [], 'min_center_distance_mm': 0.012}])
**Straight chord GND edge:** {'xy': [42.0, 32.0], 'width_mm': 0.6, 'center_distance_mm': 0.08854487164217303, 'edge_clearance_mm': -0.30145512835782695}
**New via:** no
**Segments kept:** none
**Other SIM_1V8 pads:** [{'name': 'C38.1', 'xy': [71.68, 52.0], 'same_as_u1': False, 'same_as_far': True, 'layers': ['F.Cu']}, {'name': 'U4.5', 'xy': [78.65, 56.6], 'same_as_u1': False, 'same_as_far': True, 'layers': ['F.Cu']}, {'name': 'C33.1', 'xy': [75.52, 44.0], 'same_as_u1': False, 'same_as_far': True, 'layers': ['F.Cu']}, {'name': 'JP2.1', 'xy': [79.35, 46.0], 'same_as_u1': False, 'same_as_far': True, 'layers': ['F.Cu']}]
**Other SIM_1V8 opens left:** []

## Gate

NO-ROUTE. No copper. The y=23.10 via-row exit is blocked. Pad-edge 46.030849 mm (census 46.031). SIM_IO via (30.25, 23.10) radius 0.3 mm. x=29.71 copper clearance 0.150000 mm, exactly on the 0.15 gate (same failure class as pass30be x=32.71). Rejected. x=29.70 clears SIM_IO at 0.160 mm but a north through-run crosses locked SIM_RST In1 (32.75, 25.50)–(26.20, 25.50) and COEX0 via (29.81, 22.00) clearance is 0.000 mm. West slot x=24.80–27.20 best foreign 0.01 mm at x=26.01 vs {'net': 'SIM_RST', 'item': 'trk (26.20,25.50)-(26.20,17.60)'}. That slot is the only geometric opening that does not cross SIM_RST, and it fails the 0.15 mm gate (MAGPIO1 via sits in it; P0.00 x=25.20 and SIM_RST x=26.20 close the sides). Straight F.Cu chord hits GND via (42.0, 32.0) at -0.301 mm. Not used. Far island is not F.Cu-only (through-vias at 80.000,47.126 and 76.170,45.126) but no legal segment reaches the named track or those vias. Skirt slot, sealed pocket, and RF keepout not used. No second path. Blob matches start: True.

## DRC

| | unconnected | SIM_1V8 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No copper added. Locked runs not ripped. J9.2 and J9.3 not touched. Skirt slot, sealed pocket, and RF keepout not used. No other net. No Gerbers. No commit.

