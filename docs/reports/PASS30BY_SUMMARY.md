# PASS30BY_SUMMARY - P0.24 J13.9 to J10.4 (class D, cap waived)

**Decision:** KEEP. Tip 191301e (not committed). Blob 0a0c9b42d5e5321aed37b980851592bd2a0318b4 -> e8a108d7d4fe1a374a10789f45217ab39eecb735. Backup .mcp-backups/pass30by/pre-edit.kicad_pcb.

- **Pair (live):** J13.9 PTH (84.32, 76.00) and J10.4 PTH (116.00, 35.62), both all layers and single-pad islands. Pad-edge 49.624 mm.
- **No vias.** The run goes PTH to PTH on In1.
- **Route, In1, 0.18 mm, 5 segments:** (84.32,76.0)->(86.4,73.92)->(87.1,73.92)->(106.8,54.22)->(106.8,44.82)->(116.0,35.62).
- **Closest foreign:** GND via (90.0, 70.0) 0.231; P0.06 via (107.4, 47.2) 0.26; P0.04 via (113.8, 36.8) 0.381; J13.10 (P0.25) pad 0.856. **Closest POWER:** none within 1 mm.
- **Locked runs:** nearest is P0.23 In2 (parallel diagonal) at 1.976 mm center to center, other layer. Longest stretch within 0.50 mm in plan: **0.00 mm**. P0.21/P0.17/P0.18 on In1 are ≥2 mm away. Crossings 0, no stacking. Pocket (x≤97.3) not entered.

| | unconnected | P0.24 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 44 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 43 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. The remaining P0.24 open is U1.40 to J13.9 (class A #3). J9, J16 and the do-not-retry items are untouched. This was the last class D pair not on the do-not-retry list.
