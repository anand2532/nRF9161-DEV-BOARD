# PASS30BR_SUMMARY - P0.10 U1.18 to J12.11

**Decision:** NO-ROUTE (rule 3, boxed J12 pad, no grid search). No copper. Tip 45743c9, blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda unchanged. Backup .mcp-backups/pass30br/pre-edit.kicad_pcb. Not committed.

- Live opens: U1.18 (44.0, 28.5; island includes F.Cu stub and existing via 47.0, 28.5) ↔ J12.11 PTH (31.40, 76.00), and island ↔ J16.1 (108.0, 8.0).
- J12.11 pad copper: x 30.55–32.25, y 75.15–76.85.
- North: P0.05 In1 y=74.70 spans x 22.51–57.05 and fully covers the pad width. South: P0.09 In1 y=77.20 spans x 30.10–55.30 and fully covers it too. The 0.50 mm plan band is y 75.20–76.70, inside the pad row. J12.10 (P0.09) and J12.12 (P0.11) close the sides. Same boxed class as J12.13.
- No route was attempted, so there are no segments, no clearances and no parallel stretch to report.
- DRC (unchanged): unconnected 49, P0.10 opens 2, GND 12, short/clearance/crossing/hole 0, h2h 1.

**Do-not-retry:** J9.2, J9.3, SIM_1V8, P0.09 J16.4, P0.11 J16.2, P0.12, **P0.10** (both opens; J16.1 is far beyond the 36 mm cap).
