# PASS30CA_SUMMARY - P0.23 U1.39 island to J13.8/J10.3 island on In2 (covers bz + ca)

## pass30bz: NO-ROUTE (reverted)
The In2 9-segment route closed P0.23 but split the In2 VDD_nRF plane near x 55-58, y 18.4-19.0, cutting off the F.Cu stubs at (57.21, 18.0) and (58.0, 22.0). VDD_nRF went 0->1. Full revert to e8a108d.

## pass30ca: NO-ROUTE (reverted)
Tip a458cdd. Blob start e8a108d7d4fe1a374a10789f45217ab39eecb735, end the same (verified). Backup .mcp-backups/pass30ca/pre-edit.kicad_pcb. Not committed.

- **Source:** existing P0.23 via (34.75, 23.1). **Target:** P0.23 In2 corner (103.1, 45.3).
- **Attempted route, In2, 0.18 mm, 12 segments (max), no new via, fully outside the neck box x54-60/y18-22:** (34.75,23.1)->(34.6,21.5)->(36.4,19.7)->(36.4,18.8)->(37.1,18.1)->(53.6,18.1)->(53.6,16.6)->(56.6,16.6)->(57.6,17.6)->(68.8,17.6)->(69.48,16.92)->(74.8,16.92)->(103.1,45.22).
- **Pre-checks passed:**
  - Foreign min: P0.22 via (35.25, 22.0) 0.21.
  - POWER min: VDD2/VDD2_MID vias 0.236; VIN_F via (71.58, 17.66) 0.252; VDD_nRF via (56.09, 17.35) 0.26.
  - Locked plan: only ≤1.0 mm crossings. y=16.92 is 0.52 from P0.00 In1 y=16.4, so nothing is within 0.50. Same-layer crossings 0.
- **Full DRC per-net open diff:** P0.23 1->0, **VDD_nRF 0->1**; every other net unchanged. Unconnected 43->43, short/clearance/crossing/hole 0, h2h 1, GND 12.
- **Failure:** the run's y=16.6 / 17.6 dog-leg around (56.6-57.6, 16.6-17.6) wrapped the VDD_nRF via (56.09, 17.35). That cut its In2 plane connection from the F.Cu stub at (56.65, 12.0). The north detour splits the same plane, just north of the neck box. Full revert done automatically. No second path.

**Do-not-retry:** P0.23 U1 side (U1.39 island) added. Full list: J9.2, J9.3, SIM_1V8, P0.09 J16.4, P0.11 J16.2, P0.12, P0.10, P0.23 U1.39.
**Implication:** the In2 VDD_nRF plane around x 53-60, y 12-22 is a choke for any east-west In2 run north of U1. The class A U1->J13 routes that need In2 will hit the same problem unless PM allows a VDD_nRF stitching via or reroutes that power feed.
