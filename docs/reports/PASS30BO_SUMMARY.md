# PASS30BO_SUMMARY - P0.11 U1.19 to J12.12

**Decision:** KEEP. Tip b39ed75 (not committed). Blob 1818bbc719d6a4fe6e1a2db3f59ca9fdf9d98baf -> 5a46a4bef4da85ae0841a8b51077fd8339bb3fda. Backup .mcp-backups/pass30bo/pre-edit.kicad_pcb.

## Live census
- U1.19 (44.0, 28.0) F.Cu. Its island already had F.Cu (44,28)-(46.5,28) and (48.62,28)-(49.92,28), vias (46.5,28.0), (48.62,28.0) and (49.92,28.0), and B.Cu y=29.2 links. Opens were U1 island↔J12.12 and U1 island↔J16.2.
- J12.12 P0.11 PTH center (33.94, 76.0), all layers.
- **No new via.** The run starts on the existing P0.11 via (49.92, 28.0) and lands directly on the J12.12 PTH.

## Route: In2, 0.18 mm, 8 segments
(49.92,28.0)->(49.92,32.15)->(46.8,35.27)->(46.8,50.7)->(56.95,60.85)->(56.95,63.1)->(45.25,74.8)->(35.1,74.8)->(33.94,76.0)

- **Closest foreign:** P0.07 via (47.4, 35.5) 0.197; P0.05 via (47.4, 36.5) 0.21; P0.20 pad J18.8 0.23; J12.13/14/15 pads 0.26. P0.07 In2 track edge ≥0.407 (c-c ≥0.587).
- **Closest POWER:** VDD_GPIO pad J18.9 0.43.
- **Crossings:** 0 (whole-segment and DRC). The run passes east of the P0.20 eastbound end (55.78, 63.2) at 0.577 without crossing. P0.09 is on In1, so it isn't on this layer and isn't stacked.

| | unconnected | P0.11 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 50 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 49 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open.

**Leftover:** J16.2 (108.00, 10.54) PTH, pad-edge ≈59.3 mm from the island, over the 36 mm cap. It goes on the do-not-retry list.
**Do-not-retry:** J9.2, J9.3, SIM_1V8, P0.09 J16.4, P0.11 J16.2.
Locked runs, J9, J16.4 and SIM_1V8 untouched. RF keepout, pocket and skirt slot not entered.
