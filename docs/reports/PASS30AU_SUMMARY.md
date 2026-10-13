# PASS30AU_SUMMARY — P0.14

**Timestamp:** 2026-09-30 11:45 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** P0.14
**Via added:** no
**Segments:** 0 (limit 8)
**Side of package:** none — east skirt is not reachable from U1.24
**Min foreign clearance:** n/a (no copper)
**Min POWER/VIN clearance:** n/a (no copper)
**Unconnected (ratsnest edges):** 60 → 60
**P0.14 opens:** 1 → 1
**GND zone islands:** unchanged (no copper edit; waived)
**Short / clearance / crossing / hole:** unchanged (no copper edit)

## Remeasured gap

Copper-edge gap **34.038 mm** on F.Cu between ['pad J18.2', 'pad J12.15'] at (40.623, 61.154) and ['pad U1.24'] at (42.136, 27.15). Islands: 2 (opens 1). The 25 mm cap does not apply; this pass is the explicit P0.14 exception. The gap is still not a straight route.

## Straight line (not used)

0.18 mm F.Cu chord [42.136, 27.15] → [40.623, 61.154] (34.038 mm). Crosses the SiP body: **True**. Foreign items under 0.15 mm: 18.

- GND -0.336 mm (via@42.0,29.0)
- P0.04 -0.168 mm (F.Cu (41.25,46.80)-(37.40,46.80))
- P0.03 -0.156 mm (via@41.75,41.1)
- <no-net> -0.09 mm (pad U1.127 (no net))
- P0.15 0.149 mm (pad U1.25)

The chord also runs the south fanout (y≈37–50 under the package). Locked P0.04 segments (41.25, 46.80)–(37.40, 46.80) and (41.25, 42.50)–(41.25, 46.80) were not ripped. P0.15 west wrap was not ripped.

## Why no around-the-package jog

U1.24 is the north-edge pad (42.25, 26.75), size 0.30×0.80, F.Cu only. SiP body is x 28.0–44.0, y 26.75–37.25. The exposed pad lip is only the north 0.40 mm (y 26.35–26.75). South of that lip is under the body, which this pass may not enter.

East pad U1.23 (P0.13) copper gap 0.2 mm and west pad U1.25 (P0.15) copper gap 0.2 mm. A 0.18 mm track at 0.15 mm clearance needs 0.48 mm. The pad row does not pass a track. Both neighbors continue as 0.18 mm F.Cu tracks north to their fanout vias, so the pocket cannot be crossed sideways.

North exit at the via row: P0.15 via (41.75, 23.1) r=0.3 and P0.13 via (42.75, 23.1) r=0.3. Copper-to-copper gap **0.4 mm**, need **0.48 mm**, short by **0.08 mm**. No x clears both vias at once, so the pocket has no north exit on F.Cu. A 0.50/0.30 via centered between the parallel tracks (x=42.25) would clear those tracks by 0.16 mm, but that point is inside the B.Cu GND fill. Moving the via east until it clears the fill (edge x=42.41) puts it through the P0.13 track (west edge x=42.66).

B.Cu inside the pocket is GND fill. At y=25.0 the fill edge is x=42.41 and the P0.13 track west edge is x=42.66 (halo 0.25 mm, the zone's 0.25 mm pullback). A via on the only F.Cu-clear cells drops into that fill or into the halo, which cannot hold a 0.50 mm via at ≥0.15 mm. North of the via row, both F.Cu and B.Cu are GND fill, so there is no layer change that reaches an east skirt.

East of the package (x>44, outside the body) is therefore not reachable in ≤8 segments and one via without crossing P0.13, the body, the south fanout, or the GND pour. No locked trunk was ripped. The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 was not used. No header or U1 move. U1.88 and U1.89 were not retried. P0.24 was not started. No Gerbers. No git commit.

## Gate

NO-ROUTE. P0.14 opens do not drop. No copper was added, so no other net gained an open, short/clearance/crossing/hole stayed as they were, and hole_to_hole was not raised. Nothing to revert.

