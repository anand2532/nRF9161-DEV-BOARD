# PASS30AW_SUMMARY — U1 open census

**Timestamp:** 2026-09-30 12:27 IST
**KiCad:** 9.0.2
**Decision:** **NO-COPPER**

| | count |
| --- | --- |
| U1 pads on a non-GND open | **37** |
| Can exit the fab body | **31** |
| Trapped | **6** |
| Trapped-by-keepout | **0** |

**Shortest exitable:** `P0.16` **34.259 mm**, U1.26 F.Cu copper (41.364, 27.150) to pad J18.4 (45.537, 61.154). Exit is an existing stub (via 40.70, 20.80), not a new route.

Trapped: U1.24 P0.14 (via-row 0.400 / sideways 0.200), U1.29 P0.18 (0.400 / 0.200), U1.96 P0.01 (0.400 / 0.200), U1.87 P0.29 (0.400 / 0.200), U1.92 COEX1 (0.400 / 0.200), U1.59 MIPI_SDATA (via-row 0, straddle / sideways 0.200).

U1.88 P0.30 and U1.89 P0.31 are on the exit list (stub, and 0.900 mm via-row). They were classified only and not routed.

SiP fab body confirmed x 28.0–44.0, y 26.75–37.25. Courtyard is 0.25 mm outside that. Details: `reports/PASS30AW_SHORTLIST.md`.

## Board file

Unchanged: **yes**. `nRF9161-DEV-BOARD.kicad_pcb` sha256 before and after `3f209b087c54966030c17b3ca9f91dc0758a511bfacc0aacd44ef7a1850ff005`. Size 2357924. mtime still 2026-09-30 11:23 IST (05:53:28Z). This pass only wrote reports. No save, no refill.

