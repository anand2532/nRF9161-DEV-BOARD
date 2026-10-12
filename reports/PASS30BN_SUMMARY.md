# PASS30BN_SUMMARY - P0.09 U1.16 to J12.10 (covers pass30bm + pass30bn)

## pass30bm (prior): NO-ROUTE
P0.09 had no via. Rule 4 forbade a new via (J12.10 is a PTH), and an F.Cu-only route was unreachable. See PASS30BM_SUMMARY.md.

## pass30bn: KEEP
Tip c72e8c5 (not committed). Blob 7bcfe5791b156e426a2a0affefe938be4d39f8e6 -> 1818bbc719d6a4fe6e1a2db3f59ca9fdf9d98baf. Backup: .mcp-backups/pass30bn/pre-edit.kicad_pcb.
Note: the first script run auto-reverted because the gate was miscoded (it demanded P0.09 opens = 0). Its DRC result already passed the real gate. The same route was re-applied with the gate corrected to "P0.09 opens drop". This is not a second path.

- **Via:** (46.90, 29.72), 0.50/0.30 through. It clears all pad copper; the nearest pad is U1.15/16 at x≤44.40, 2.25 mm from via center. U1 courtyard (body x≤44.0, +0.25) ends at x=44.25, so the via is outside it. DRC courtyard 0. Via clearances: P0.08 via (46.2, 30.0) 0.204 (all layers); B.Cu P0.11 track y=29.2 0.18; B.Cu P0.08 track y=30.25 0.19; F.Cu VDD_GPIO x=47.55 0.31 (POWER); P0.10 via 0.674; DEC0 via 0.631. Skirts x=44.25/44.60 are ≥2.05 away.
- **F.Cu neck:** (44.0, 29.5)->(46.6, 29.5)->(46.9, 29.72). It runs between the P0.10 F.Cu track (y=28.5) and the P0.08 F.Cu track (y=30.0); clearance 0.32 to each.
- **In1 run:** (46.9, 29.72)->(48.9, 29.72)->(59.4, 40.22)->(59.4, 60.7)->(59.5, 60.8)->(59.5, 73.0)->(55.3, 77.2)->(30.1, 77.2)->(28.86, 76.0), landing on the J12.10 PTH pad. No via at J12.
- **Segments:** 10 (2 F.Cu + 8 In1).
- **Closest foreign:** P0.05 In1 corners (57.05, 38.4) and (47.4, 38.4) 0.195 edge (0.375 c-c); GND via (60.0, 50.0) 0.21; B.Cu P0.11 0.18 at the via. **Closest POWER:** VDD_GPIO pad J18.9 ≈0.24; J12.17/18 0.26; VDD2 via (52.22, 32.0) 0.245. The P0.05 corner (57.05, 74.7) is 0.35 edge. The run passes the SIM_CLK In1 corner (57.2, 36.0) with no crossing.
- **Crossings:** 0 same-layer, whole-segment test, and DRC crossing 0.

| | unconnected | P0.09 | short | clearance | crossing | hole | hole_to_hole | GND items |
|---|---|---|---|---|---|---|---|---|
| before | 51 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 50 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open.

**Leftover:** J16.4 (108.00, 15.62), pad-edge ≈64.09 mm, over the 36 mm cap. It goes on the do-not-retry list.
**Do-not-retry:** J9.2, J9.3, SIM_1V8, P0.09 J16.4.
Locked runs and J9 untouched; RF keepout and sealed pocket not entered.
