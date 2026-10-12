# PASS30BM_SUMMARY - P0.09 U1.16 to J12.10

**Decision:** NO-ROUTE. No copper was added. **Tip:** c72e8c5. **Blob start/end:** 7bcfe5791b156e426a2a0affefe938be4d39f8e6 (unchanged). Backup: .mcp-backups/pass30bm/pre-edit.kicad_pcb. Not committed.

## Facts measured live
- U1.16 P0.09 center (44.000, 29.500), copper x 43.60–44.40, y 29.35–29.65. It is F.Cu only.
- J12.10 P0.09 center (28.860, 76.000), a 1.70 mm square PTH with copper on all layers. The census point (29.107, 75.187) is a pad-edge point. Pad-edge distance measured here is ≈47.10 mm (census 47.797).
- **P0.09 has no tracks and no vias at all.** No via in the via row belongs to P0.09. The nearby vias belong to other nets: P0.08 (46.2, 30.0), DEC0 (45.4, 30.55), P0.11 (46.5, 28.0) and P0.10 (47.0, 28.5).
- Leftover: J16.4 (108.00, 15.62), PTH. Its pad-edge distance to U1.16 is ≈64.09 mm, over the 36 mm cap.

## Why NO-ROUTE
1. The ordered class ("from the east via, run south") needs an existing P0.09 exit via, and there is none.
2. Rule 4 allows a new via only if the far copper has none on that layer. J12.10 is a PTH with copper on every layer, so a new via is not allowed.
3. An F.Cu-only route is not available either. A 0.05 mm grid A* search on F.Cu (foreign 0.15 / POWER 0.20 + 0.03 margin, RF keepout blocked) found no path from U1.16 to J12.10.
No second path was tried.

## DRC (no change)
unconnected 51, P0.09 opens 2, short/clearance/crossing/hole 0, hole_to_hole 1, GND items 12. Files: DRC_PASS30BM_BEFORE.json, and DRC_PASS30BM_AFTER.json (a copy, since the board was not changed).

## Needs a PM ruling
Allow one new P0.09 exit via east of U1.16 that fully clears all pad copper, then In1/In2 south to J12.10. Or keep P0.09 on the do-not-retry list.
