# PASS30BZ_SUMMARY - P0.23 U1.39 to J13.8/J10.3 island (class A #2)

**Decision:** NO-ROUTE (gate fail, full revert). Tip a458cdd. Blob start e8a108d7d4fe1a374a10789f45217ab39eecb735, end the same (verified). Backup .mcp-backups/pass30bz/pre-edit.kicad_pcb. Not committed.

- **Source:** existing via (34.75, 23.1), net verified live as P0.23, on the U1.39 island. **Target:** P0.23 In2 corner (103.1, 45.3) on the J13.8/J10.3 island, the nearest island copper reachable. Pad-edge 67.098 mm (length waived).
- **Attempted route, In2, 0.18 mm, 9 segments, no new via:** (34.75,23.1)->(34.6,21.5)->(36.4,19.7)->(36.4,18.4)->(54.4,18.4)->(55.025,19.025)->(57.5,19.025)->(67.475,29.0)->(86.9,29.0)->(103.1,45.3). In1 and B.Cu were unreachable in the search.
- **Geometry passed:**
  - Foreign min: P0.23 start vs P0.22 via (35.25, 22.0) 0.21; COEX2 via (72.0, 29.6) 0.21; P0.20 via (36.2, 20.8) 0.246.
  - POWER min: VDD_GPIO via (40.17, 19.13) 0.236; VDD_nRF via (59.3, 22.0) 0.341.
  - Locked runs: only 90° plan crossings (SIM_CLK y=19.2, SIM_RST x=68.0, P0.17/P0.18/P0.21 In1 diagonals), each ≤1.0 mm within 0.50. y=19.025 is centered between SIM_RST y=18.5 and SIM_CLK y=19.55 (0.525 each), so there is no parallel run within 0.50. Same-layer crossings 0.
- **Gate failed:** DRC after showed unconnected 43->43, P0.23 1->0, but **VDD_nRF gained an open**. The In2 run cut the In2 VDD_nRF plane: the fill island holding the F.Cu stubs at (57.21, 18.0) and (58.0, 22.0) was separated around (55-58, 18.4-19.0). short/clearance/crossing/hole 0, h2h 1, GND 12. The script did a full revert automatically.
- **No second path tried.**

**Implication:** any In2 route through the y≈18-22, x≈54-60 VDD_nRF neck will split that plane. A future P0.23 attempt would need In1 (unreachable now), a path avoiding that neck, or a VDD_nRF stitching via (a PM decision).
