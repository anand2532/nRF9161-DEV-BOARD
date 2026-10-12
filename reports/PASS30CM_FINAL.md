# PASS30CM final summary (branch `vippo`, base 9fb2733, not pushed)

| Step | SHA | What | Unconnected | Gate |
|---|---|---|---|---|
| FX1 | 66e2a0b | P0.00 removed from In1 entirely; F/B reroute east of U1; 3 GND stitches | 17 → 17 | PASS. In1 GND 2 pcs, 8140.8 → 8206.5 mm² |
| FX2 | aababdf | COEX0 U3 branch rerouted out of the RF keepout (y ≥ 42.5) | 17 → 17 | PASS |
| C5 text | 232a29d | Fab-note C5 exception "pads 52–60" (DRU already had it); DFM note refreshed | – | docs only |
| FX3/FX4 | 7fab1ce | GND vias 0.5/0.3 at (27.6, 23.0) and (26.8, 35.6) | 17 → 17 | PASS |
| 5 | 1cd6bcb | P0.13 ripped and reclosed; P0.12, P0.25 and P0.31 routed with VIPPO at new pad centres; GND stitches | 17 → 13 | PASS |
| 6 | 9415424 | SIM_IO closed: VIPPO pad 48 + B.Cu; SIM_1V8 untouched (closed, POWER, C40 kept) | 13 → 12 | PASS. SIM gap ≥0.55 outside / ≥0.20 in fan-out zone |
| 7 | – | P0.14/P0.18: no legal route; nothing committed | 12 | – |

## Final gate on HEAD (refilled)
- **Zero-checks:** short, clearance, crossing, hole, hole_to_hole, copper_edge, silk, courtyard, solder_mask_bridge and via_dangling are all 0. track_dangling is 4 (pre-existing).
- **Unconnected: 17 (9fb2733) → 12.** That is 2 signal (P0.14, P0.18) + 10 GND islands (was 11).
- **No power net open.** VDD_nRF In2: 1 piece, 6784.6 → 6737.0 mm².
- **In1 GND:** 2 pieces, 8140.8 → 8185.2 mm². The P0.00 RF-corner void is gone; the drop from 8206.5 comes from the new VIPPO barrels.

## Lengths (mm, track copper) 9fb2733 → HEAD
| Net | Before | After |
|---|---|---|
| P0.00 | 154.1 | 108.6 |
| COEX0 | 142.7 | 131.3 |
| P0.12 | open | 54.7 |
| P0.25 | open | 84.3 |
| P0.31 | 46.2 (open) | 144.5 |
| P0.13 | 88.4 | 72.8 |
| SIM_IO | 37.5 (open) | 142.7 |

- **COEX0:** U1.93 → U3.3 is about 21.8 mm (≤80 met). The whole net exceeds 80 only because of the pre-existing J15 header leg.

## Step 7: why P0.14 and P0.18 stay open (for the Schematic remap)
P0.19 (In1) and P0.20 (In2) were not moved. **A VIPPO spot is legal on both pads:** P0.14 has a 0.20 mm land gap to the P0.13 VIPPO and P0.18 has 0.48 mm to P0.25. The escape from each spot is blocked:

- **P0.14 (U1.24, 42.25, 27.0):**
  - **B.Cu** is enclosed. To the east and south is P0.13 (VIPPO at 42.75, 27.0 and its SW run to 40.85, 28.9). To the north is the P0.25 run (33.25, 27.0) → (42.65, 25.95) with its via. Further south is P0.12 (43.75, 27.5) → (41.5, 28.75).
  - **F.Cu:** a north escape out of the pad is blocked by the adjacent pad escapes and vias north of the row. No exit was found.
  - The router search exhausted after 7262 nodes (B) and 115 nodes (F).
- **P0.18 (U1.29, 39.75, 27.0):**
  - **B.Cu** pocket is bounded to the north by the P0.25 diagonal at y ≈ 26.4. To the south and west it is bounded by the P0.13 / P0.12 / SIM_IO runs under U1. The search exhausted after 9776 nodes.
  - **F.Cu:** the north exit is blocked (505 nodes).
- **Fix options:**
  - (a) Schematic remaps P0.14/P0.18 to free GPIOs.
  - (b) A later pass rips P0.25 and reroutes it under its own pad column, which would open the north B.Cu corridor for both.

## Notes
- **P0.25 and SIM_IO:** long, multi-via routes (9 and 5 vias). They pass the gate, but an SI/cleanup review is recommended.
- **SIM ≤10 mm parallel rule:** not checked by tool.
- **Images:** `PASS30CM_FINAL_BEFORE.png` (9fb2733) and `PASS30CM_FINAL_AFTER.png` (HEAD), layers F/B/In1/VIPPO. DRC: `DRC_PASS30CM_FINAL.json`.
