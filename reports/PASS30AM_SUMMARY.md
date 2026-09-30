# PASS30AM_SUMMARY — VDD_GPIO east island (GND islands waived)

**Timestamp:** 2026-09-30 10:28 IST
**KiCad:** 9.0.2
**Decision:** **REVERT**
**Net:** VDD_GPIO
**Via:** no
**Segments:** 4 (limit 6)
**Shortest non-GND gap:** 17.626 mm (≤ 20 mm)
**Unconnected:** 63 → 63
**VDD_GPIO opens:** 2 → 2
**GND zone islands:** 11 → 11 (increase WAIVED)

## Why this gap

Remeasured live copper after pass30al. Headline unconnected 63, GND islands 11.
Shortest remaining non-GND island gap is VDD_GPIO **17.626 mm**:

- Island A (east, J9/J10/U2/R14): closest copper (75.080, 31.808) on F.Cu (75.14, 32.00)–(75.14, 39.05)
- Island B (U1.12 / TP10 / U3): closest copper (70.036, 14.920) on B.Cu (70.00, 8.00)–(70.00, 14.80)
- Same-layer nearest: 18.444 mm on B.Cu, (77.831, 31.637) ↔ (70.053, 14.913)

The straight line is not used. Closest points are on different layers. The B.Cu
straight line hits VIN_F, the P0.08 trunk at y=30.25 (x=46.20–78.50) and COEX2.
COEX2's B.Cu vertical at x=72 closes the northbound corridor, so a same-layer B.Cu
join needs a via to hop it. Both islands already have F.Cu, so the route stays on
F.Cu and does not add a via. It does not repeat the locked U1.12 polyline
(40.170, 19.126)→(44.000, 31.500) and does not rip COEX0.

## Path

South from the existing via (71.300, 8.000) on the U1.12 island, east at y=7.300,
then northeast to the east-island F.Cu junction (86.510, 26.000), the R14.2 /
(86.51, 26)–(87.81, 26) corner. Minimum x is 71.300 (>24.2). Maximum y is 26.000.
The y=44.60 B.Cu pocket is not used. Pre-check used the board 0.10 mm clearance.
VDD_GPIO is netclass POWER, whose clearance is 0.15 mm.

Reason: REVERT. The y=7.300 horizontal clears a 0.10 mm rule but not POWER 0.150 mm
versus pad D3.1 [VIN] at (75.213, 8.000): actual 0.135 mm. Mid DRC VDD_GPIO opens
2→1, gained none, short/cross/hole_clearance 0, hole_to_hole 1→1, GND islands
11→12 (waived, not the revert reason). Clearance 1 fails the gate. Full restore.
One attempt only; the track was not nudged.

### Segments (0.18 mm)

| layer | start | end | width |
| --- | --- | --- | --- |
| F.Cu | (71.300, 8.000) | (71.300, 7.300) | 0.18 mm |
| F.Cu | (71.300, 7.300) | (77.300, 7.300) | 0.18 mm |
| F.Cu | (77.300, 7.300) | (81.500, 13.500) | 0.18 mm |
| F.Cu | (81.500, 13.500) | (86.510, 26.000) | 0.18 mm |

No via added.

## Gate (GND islands waived)

- mid short/clear/cross/hole_clearance: 0/1/0/0 — **not met**
- mid VDD_GPIO opens: 2 → 1 (would have counted)
- no non-GND net gained an open: True
- hole_to_hole did not increase: 1 → 1
- GND islands on the attempt: 11 → 12 (WAIVED, not the revert reason)
- clearance hit: POWER netclass 0.150 mm, actual 0.135 mm, pad D3.1 [VIN] (75.213, 8.000) vs F.Cu (71.300, 7.300)–(77.300, 7.300)
- **met: False** — full revert

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 63 | 0 | 0 | 0 | 0 | 1 | 11 | 2 |
| mid (reverted) | 63 | 0 | 1 | 0 | 0 | 1 | 12 | 1 |
| after (REVERT) | 63 | 0 | 0 | 0 | 0 | 1 | 11 | 2 |

## Protect checklist

- Locked VDD_GPIO F.Cu polyline to U1.12 still present (not the route repeated)
- COEX0 via (37.000, 30.500) and the six locked segments still present
- P0.10 via (47.000, 28.500) and P0.12 via (47.000, 27.500) not moved
- DEC0 B.Cu bridge (46.950, 30.900)–(48.100, 30.900) not ripped
- P0.15 west wrap segment count 42 → 42
- Class C C22/C23/C24, P0.22, P0.19, Stage-A VDD2, SIM_IO_C/SIM_CLK_C walls not ripped
- Footprints moved: none
- y=44.60 B.Cu pocket not used
- RF keepout: this route stays east of x=24.2 (min x=71.300)
- No Gerbers. No git commit.
