# PASS30CM step 5: P0.13 rip-up under U1; P0.12, P0.25 and P0.31 routed; P0.13 reclosed
- **Ripped:** P0.13 entirely, except the J18.1 / J12.14 header stubs (51 items). That includes its B.Cu runs under U1 at y 27, x 40, y 30/31 and x 32.2, and its north F.Cu/via escape. Neither SWDCLK nor COEX0 needed to be ripped; both are unchanged.
- **Routing:** grid router (0.05 mm grid, rule-checked: 0.1 / POWER 0.15 / SIM 0.5, hole 0.25, edge 0.5). The RF keepout (x<29, y 26–40, F.Cu/In1) and U1 interior F.Cu were forbidden, and no non-VIPPO via was allowed under the U1 body.
- **VIPPO 0.30/0.20** (In1/In2 remove-unconnected, same as group A) placed at the **new pad centres**:

| Net | VIPPO pad | Pad position (mm) | Escape |
|---|---|---|---|
| P0.12 | U1.20 | 43.75, 27.5 | B.Cu under U1 → J12.13 |
| P0.25 | U1.42 | 33.25, 27.0 | B.Cu y≈26 → east → J13.10 |
| P0.31 | U1.89 | 36.75, 37.0 | B.Cu south → J13.16 / J11 chain |
| P0.13 | U1.23 | 42.75, 27.0 | B.Cu under U1 → J18.1 (reclosed) |

| Net | Before | After |
|---|---|---|
| P0.12 | open | **closed**, 54.7 mm, 3 vias |
| P0.25 | open | **closed**, 84.3 mm, 9 vias |
| P0.31 | open (U1 side) | **closed**, 144.5 mm total net (the J13–J11 leg is unchanged), 6 vias |
| P0.13 | closed, 88.4 mm | **closed**, 72.8 mm, 4 vias |
| COEX0 / SWDCLK | 131.3 / 63.0 | unchanged |

- **GND repair:** the new copper split some F/B GND pour pieces. Legal GND stitch vias 0.6/0.3 were added to every changed piece (18 vias, picked by a deepest-legal-point search). One pre-existing F.Cu island was also tied in.
- **Gate (refilled):** short/clearance/crossing/hole/hole_to_hole/courtyard/edge/silk/mask_bridge are all 0. via_dangling is 0. track_dangling is 4 (pre-existing).
  - **Unconnected 17 → 13:** signal 6 → 3 (P0.14, P0.18, SIM_IO), GND islands 11 → 10.
  - No power net open; no closed net reopened.
  - In1 GND: 2 pieces, 8204.6 → 8190.1 mm² (VIPPO barrels).
  - VDD_nRF: 1 piece, 6774.1 → 6747.6 mm².
  - RF copper untouched.
- Open: P0.14 and P0.18 → step 7; SIM_IO → step 6.
