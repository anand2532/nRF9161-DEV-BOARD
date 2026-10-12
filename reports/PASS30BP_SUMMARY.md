# PASS30BP_SUMMARY - P0.12 U1.20 to J12.13

**FINAL STATUS: REVERTED (NO-ROUTE)** - Hardware PM ruling, 2026-10-12. Two runs nearly stacked on locked runs on the adjacent layer: In2 x=25.4 vs P0.00 In1 x=25.2, and In2 y=17.7 vs SIM_RST In1 y=17.6. The 42 mm run hugging the RF keepout is also not wanted. Restored blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda. DRC (DRC_PASS30BP_REVERT.json): unconnected 49, GND 12, P0.12 opens 2, short/clearance/crossing/hole 0, h2h 1.

---
## Original attempt record (superseded)

**Decision:** KEEP. Tip 45743c9 (not committed). Blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda -> 89bca9a5014747fb5f8e1f43e8a25bda35a16840. Backup .mcp-backups/pass30bp/pre-edit.kicad_pcb.

## Live census
- U1.20 (44.0, 27.5) F.Cu. Its island is F.Cu (44,27.5)-(47,27.5) plus the existing via (47.0, 27.5). Opens were island↔J12.13 and island↔J16.3.
- J12.13 P0.12 PTH (36.48, 76.0), all layers.
- **No new via.** The run starts on the existing via (47.0, 27.5) and lands directly on the J12.13 PTH.

## Route: In2, 0.18 mm, 10 segments
(47.0,27.5)->(45.95,26.45)->(45.95,21.35)->(42.3,17.7)->(33.3,17.7)->(25.4,25.6)->(25.4,67.7)->(32.75,75.05)->(32.75,77.15)->(35.9,77.15)->(36.48,76.0)
The run goes north around the U1 body, then down the west side at x=25.4 (just east of the RF keepout edge at 24.2), and approaches J12.13 from the south because P0.11 y=74.8 covers it from the north.

- **Closest foreign:** COEX0 via (29.81, 22.0) 0.183; GND via (25.98, 34.0) 0.19; P0.17 In2 skirt corner (45.55, 21.5) 0.209 (c-c 0.389 ≥0.33); P0.22 via (35.25, 18.3) 0.21; J12.12 (P0.11) pad 0.21.
- **Closest POWER:** VDD2 via (44.72, 25.9) 0.738; VDD_GPIO via (40.17, 19.13) 0.936.
- **Crossings:** 0 (whole-segment and DRC).
- **Different-layer near-parallels, flagged:** In2 y=17.7 sits 0.10 from SIM_RST In1 y=17.6, and In2 x=25.4 sits 0.20 from P0.00 In1 x=25.2. Neither shares a centerline.
- P0.11 In2 is not crossed (its pad stub is passed on the west and south). P0.07 In2 is clear (ours ends north of y=79.2 and east of x=25.2).

| | unconnected | P0.12 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 49 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 48 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open.

**Leftover:** J16.3 (108.00, 13.08) PTH, pad-edge ≈61.37 mm, over the 36 mm cap. It goes on the do-not-retry list.
**Do-not-retry:** J9.2, J9.3, SIM_1V8, P0.09 J16.4, P0.11 J16.2, P0.12 J16.3.
