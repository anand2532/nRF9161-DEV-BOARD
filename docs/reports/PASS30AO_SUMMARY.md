# PASS30AO_SUMMARY — no qualifying gap

**Timestamp:** 2026-09-30 10:37 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** none
**Distance:** remaining VDD_GPIO 27.034 mm (cap 25 mm); shortest other `P0.31` 29.078 mm (cap 20 mm)
**Path:** none
**POWER clearance measured:** n/a (no copper placed)
**Unconnected:** 63 → 63
**VDD_GPIO opens:** 1 → 1
**GND zone islands:** 12 → 12 (waived, not a factor)
**Short / clearance / crossing / hole_clearance:** 0 / 0 / 0 / 0
**hole_to_hole:** 1 (unchanged; no edit)

## Why no route

Remaining VDD_GPIO open is 27.034 mm (>25 mm) between F.Cu pad U2.5 (74.519, 39.306) and pad J18.9 (58.859, 61.343). Shortest other non-GND gap is P0.31 29.078 mm (>20 mm). Neither priority qualifies, so no track and no via.

Priority 1 is the single remaining VDD_GPIO open (DRC opens = 1, two islands). It is the same pair pass30an left open: the merged east/U1 island (closest copper pad U2.5) and the J18.9 / J12.17 / J12.18 island. 27.034 mm is over 25 mm, so it is not closed. Priority 2 then looks at every other non-GND pair. The shortest is P0.31 at 29.078 mm, over 20 mm. Nothing falls through into a route. A dirty jog was not forced.

## Five shortest non-GND gaps

- `VDD_GPIO` 27.034 mm  F.Cu (74.519, 39.306) ↔ B.Cu+F.Cu (58.859, 61.343)
- `P0.31` 29.078 mm  B.Cu+F.Cu (102.501, 75.250) ↔ B.Cu+F.Cu (115.599, 49.290)
- `P0.30` 32.207 mm  B.Cu+F.Cu (99.961, 75.250) ↔ B.Cu+F.Cu (115.150, 46.850)
- `P0.14` 34.038 mm  B.Cu+F.Cu (40.623, 61.154) ↔ F.Cu (42.136, 27.150)
- `P0.16` 34.259 mm  F.Cu (41.364, 27.150) ↔ B.Cu+F.Cu (45.537, 61.154)

Detail: `reports/PASS30AO_SHORTLIST.md`.

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before (also after; no edit) | 63 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |

Source: `reports/DRC_PASS30AO_BEFORE.json`. No mid or after file — the board file was not written.

## Protect checklist

- Locked pass30an VDD_GPIO F.Cu y=7.050 path not repeated and not ripped
- Locked pass30ak VDD_GPIO polyline to U1.12 not ripped
- COEX0, DEC0 B.Cu bridge, P0.10 via (47.000, 28.500), P0.12 via (47.000, 27.500) not moved
- P0.15 west wrap not touched; east spine at x=45.5 not used
- Class C C22/C23/C24, trunks, L1, L2, TP1, U3, solid In1 GND not touched
- P0.22 keep, P0.19 keep, Stage-A VDD2, SIM_IO_C / SIM_CLK_C walls not ripped
- y=44.60 B.Cu pocket (x≈81.8–97.3) not used
- RF keepout: no new digital copper
- U1 and headers unmoved
- No Gerbers. No git commit.

