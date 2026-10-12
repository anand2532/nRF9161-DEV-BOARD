# PASS30BW_SUMMARY - P0.17 J17.1 to skirt island (J13.2) (class D, cap waived)

**Decision:** KEEP. Tip abfe3d6 (not committed). Blob 168d2eb116cb8f2941841d65e53278bf87d2479f -> 8af24cfa9e4121364d59fb744be10079f521fda2. Backup .mcp-backups/pass30bw/pre-edit.kicad_pcb.

- **Pair (live):** J17.1 PTH (108.00, 26.00), all layers, a single-pad island. The other island is U1.28 + the P0.17 skirt (In2) + J18.5 (48.16, 62.0) + J13.2 PTH (66.54, 76.00). Pad-edge 61.526 mm. Landed on J13.2. The locked skirt copper was not touched.
- **No vias.** The run goes PTH to PTH on In1.
- **Route, In1, 0.18 mm, 5 segments:** (108.0,26.0)->(102.6,31.4)->(102.6,41.1)->(69.8,73.9)->(67.3,73.9)->(66.9,76.0, inside the J13.2 pad).
- **Closest foreign:** nRESET via (102.0, 36.0) 0.21; P0.01 via (68.0, 74.5) 0.21; SIM_RST_C via (97.3, 45.54) 0.218; nRESET via (103.3, 36.0) 0.31. **Closest POWER:** none within 1 mm.
- **Locked runs:**
  - P0.18 In1 (same layer) is 0.849 mm away center to center, parallel; that also meets the 0.50 plan rule.
  - x=102.6 crosses P0.22 In2 y=32.5 at 90°. The longest stretch within 0.50 mm in plan is **1.0 mm** (that crossing).
  - P0.23 In2 is clear. Same-layer crossings 0, no stacking. Pocket not entered.

| | unconnected | P0.17 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 46 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 45 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. P0.17 is fully connected. J9, J16 and the remaining do-not-retry items are untouched.
