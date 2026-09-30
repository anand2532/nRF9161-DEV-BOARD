# PASS30AH_SUMMARY — shortest-gap gate

**Timestamp:** 2026-09-30 09:28 IST
**KiCad:** 9.0.2+dfsg-1
**Decision:** **NO ROUTE**
**Net:** none
**Unconnected:** 64 → 64 (delta 0)
**Short/clearance/crossing/hole_clearance:** 0/0/0/0 (baseline DRC, board not edited)
**Drop ≥ 1:** False (no attempt)

## Choice

No non-protected island gap is <= 12 mm. Shortest real gap is VDD_GPIO 12.305 mm (F.Cu via@(40.17,19.13) to pad U1.12) and that straight line also shorts the P0.15 keep.

Measured live copper islands (tracks, vias, pads on F.Cu/B.Cu). GND zone islands skipped. A pair is a protected keep and was excluded when the net is P0.22, P0.19, P0.15, VDD2, an RF/Class-C net, or a sealed SIM wall net (SIM_IO_C, SIM_CLK_C). None of those excluded nets had a sub-12 mm gap anyway (P0.15 and VDD2 and the SIM walls and Class C have no DRC open; P0.19's remaining gap is 36.7 mm).

## Five shortest real gaps

- `VDD_GPIO` 12.305 mm  (40.279, 19.511) ↔ (43.622, 31.353)
- `COEX0` 15.590 mm  (28.645, 37.910) ↔ (28.645, 22.320)
- `VDD_GPIO` 17.626 mm  (75.080, 31.808) ↔ (70.036, 14.920)
- `VDD_GPIO` 27.034 mm  (74.519, 39.306) ↔ (58.859, 61.343)
- `P0.31` 29.078 mm  (102.501, 75.250) ↔ (115.599, 49.290)

Detail: `reports/PASS30AH_SHORTLIST.md`.

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance |
| --- | ---: | ---: | ---: | ---: | ---: |
| before (no edit, also after) | 64 | 0 | 0 | 0 | 0 |

Source: `reports/DRC_PASS30AH_BEFORE.json`. No after file — the board file was not written.

## Protect checklist

- y=44.60 B.Cu pocket (x≈81.8–97.3): no new track
- SIM_IO_C and SIM_CLK_C walls: not ripped
- Placement frozen: J14(104,48) J15(104,62); J13(64,76) J10(116,28) J11(116,46); J16(108,8) J9(116,8) J17(108,26); J12(6,76); U1(36,32)
- Class C C22/C23/C24, RF trunks, L1, L2, U3, west RF keepout: untouched
- P0.22 keep, P0.19 keep, P0.15 west wrap, Stage-A VDD2, P0.04/P0.06/P0.01 keeps: untouched
- No Gerbers. No git commit.

**Stop:** no gap ≤ 12 mm. One attempt not used. Idle.

