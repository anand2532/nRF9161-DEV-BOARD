# PASS30BT_SUMMARY - P0.22 (class D, cap waived)

**Decision:** KEEP. Tip 4b9b615 (not committed). Blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda -> f005a44ac5f9f9816e7b6140d71b9121a23df93b. Backup .mcp-backups/pass30bt/pre-edit.kicad_pcb.

- **Open pair (live):** island A is U1.38 + J8.6 + vias (35.25,18.3/19.9/22.0), (36.5,3.8/5.2), (64.0,3.8/5.2), (53.65,6.0) and B.Cu links. Island B is J10.2 + J13.7 + vias (109.2,32.5/54.8/56.2), (112.5,29.9/32.5), (114.7,29.9), (104.5/106.5,71.5), (79.24/81.3,71.5). Pad-edge 51.605 mm.
- **No new via.** The run goes from the existing via (64.0,5.2) to the existing via (109.2,32.5). Both are through vias on their islands.
- **Route, In2, 0.18 mm, 3 segments:** (64.0,5.2)->(70.3,5.2)->(97.6,32.5)->(109.2,32.5).
- **Closest foreign:** GND pad J17.4 ≈0.18 (circle-approx; DRC clean); ENABLE via (90.375,26.2) 0.264 (ENABLE counted as POWER: ≥0.20 OK); SWDCLK via (63.3,6.0) 0.673. **Closest POWER:** ENABLE 0.264; VDD_GPIO pad J17.3 0.48; VDD_GPIO via (71.3,8.0) 0.783.
- **Locked runs:** min plan distance 0.96 mm (P0.00 In1 corner (80.14,16.4)). Longest stretch within 0.50 mm in plan: **0.00 mm**. Same-layer crossings: 0. No stacking.

| | unconnected | P0.22 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 49 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 48 | 0 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. P0.22 is fully connected. J9, J16 and the do-not-retry items are untouched.
