# PASS30BX_SUMMARY - P0.21 J13.6 to J10.1 (class D, cap waived)

**Decision:** KEEP. Tip 25cb0bc (not committed). Blob 8af24cfa9e4121364d59fb744be10079f521fda2 -> 0a0c9b42d5e5321aed37b980851592bd2a0318b4. Backup .mcp-backups/pass30bx/pre-edit.kicad_pcb.

- **Pair (live):** J13.6 PTH (76.70, 76.00) and J10.1 PTH (116.00, 28.00), both all layers and single-pad islands. Pad-edge 60.336 mm.
- **No vias.** The run goes PTH to PTH on In1.
- **Route, In1, 0.18 mm, 4 segments:** (77.4,76.0, inside J13.6)->(77.4,69.9)->(114.1,33.2)->(114.1,29.2)->(116.0,28.0).
- **Closest foreign:** P0.22 via (114.7, 29.9) 0.21; SIM_IO_C via (98.54, 50.01) 0.494; SIM_CLK_C via (99.19, 46.67) 0.631; J13.7 pad 0.9. **Closest POWER:** none within 1 mm.
- **Locked runs:**
  - Nearest is P0.23 In2 (diagonal at (103.1,45.3)-(115.2,33.2) and vertical x=103.1), 0.958 mm center to center in plan, other layer.
  - Longest stretch within 0.50 mm in plan: **0.00 mm**.
  - The diagonal runs parallel to P0.17 and P0.18 on In1 at ≥1.7 mm. Crossings 0, no stacking. Pocket and skirt slot not entered.

| | unconnected | P0.21 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 45 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 44 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. The remaining P0.21 open is U1.37 to J13.6 (class A #4). J9, J16 and the do-not-retry items are untouched.
