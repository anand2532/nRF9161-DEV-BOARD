# PASS30BV_SUMMARY - P0.18 island (J13.3/J18.6) to J17.2 (class D, cap waived)

**Decision:** KEEP. Tip 05cfc22 (not committed). Blob 841574e17ab38ff0508510a63863da9ad5e86a4d -> 168d2eb116cb8f2941841d65e53278bf87d2479f. Backup .mcp-backups/pass30bv/pre-edit.kicad_pcb.

- **Pair (live):** island A is J13.3 PTH (69.08, 76.00) + J18.6 PTH (50.70, 62.00) + B.Cu links (69.08,76)-(69.08,72.8)-(50.7,72.8)-(50.7,62). J17.2 PTH (108.00, 28.54) is all layers. Pad-edge 57.998 mm.
- **No vias.** The run goes PTH J13.3 to PTH J17.2 on In1.
- **Route, In1, 0.18 mm, 3 segments:** (68.9,76.0)->(106.7,38.2)->(106.7,29.8)->(108.0,28.54). The start is inside the J13.3 pad, 0.18 off center, to gain clearance from the SIM_CLK_C via.
- **Why In1:** In2 would cross the locked P0.22 In2 run at y=32.5.
- **Closest foreign:** SIM_CLK_C via (99.19, 46.67) 0.286; J17.4 GND pad 0.36; P0.19 pad J13.4 0.983; SIM_RST_C via (97.3, 45.54) 1.067. **Closest POWER:** VDD_GPIO pad J17.3 0.36.
- **Locked runs:**
  - x=106.7 (In1) crosses P0.22 In2 y=32.5 at 90° in plan. The stretch within 0.50 mm is 1.0 mm, the crossing itself, so ≤2 mm.
  - P0.23 In2 diagonal is ≥2.35 mm away in plan.
  - Same-layer crossings 0, no stacking.
  - Pocket (y≈44.6, x≤97.3) not entered: the run passes y=44.6 at x≈100.3.

| | unconnected | P0.18 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 47 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 46 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. The remaining P0.18 open is U1.29 to island (class C). J9, J16 and the do-not-retry items are untouched.
