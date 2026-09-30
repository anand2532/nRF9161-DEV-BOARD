# PASS30AL_SUMMARY — COEX0 landing (GND islands waived)

**Timestamp:** 2026-09-30 10:20 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** COEX0
**Via:** yes — through via (37.000, 30.500) dia 0.6 drill 0.3
**Segments:** 6 (limit 6)
**Unconnected:** 64 → 63
**COEX0 opens:** 1 → 0
**GND zone islands:** 11 → 11 (increase WAIVED)

## Why not the straight line

Live islands: F.Cu COEX0 (26.200, 38.000)–(33.000, 38.000) and the R4.1 island
via (29.810, 22.000) / (31.110, 22.000). A straight F.Cu drop near x=28.75 hits
no-net pads U1.51 (28.750, 26.750) and U1.73 (28.750, 37.250), both 0.30×0.80.
North/south pad pitch is 0.50 mm, so the gap between pads is 0.20 mm — a 0.18 mm
track at 0.10 mm clearance does not fit. The route does not take that line.

A west F.Cu jog staying x>24.2 cannot land either: it crosses MAGPIO1, MAGPIO2,
MIPI_VIO, MIPI_SCLK and the ANT/AUX/GPS matching tracks. AUX on F.Cu runs to
x=20.485, west of the x=24.2 keepout, so there is no southbound F.Cu east of
x=24.2. A via does not fit in the remaining west corridor beside MAGPIO2
(hole-to-copper). One via is used so the jog can land.

## Confirmed live coordinates

- U1 @ (36.0, 32.0) unmoved
- U1.51 net='' (28.75, 26.75) size [0.3, 0.8]
- U1.73 net='' (28.75, 37.25) size [0.3, 0.8]
- U1.93 net='COEX0' (38.75, 37.25) size [0.3, 0.8]
- R4.1 net='COEX0' (28.51, 22.0)
- P0.15 segments before 42 after 42
- VDD_GPIO polyline present: True
- DEC0 B.Cu bridge present: True

## Path

Not the straight line. Not a west F.Cu wrap (it cannot clear RF matching and stay
x>24.2). Existing north via (31.110, 22.000) is already on the R4 island, so the
route leaves on B.Cu, passes east of U1.51/U1.73 inside the module via field,
and returns to F.Cu beside the thermal pads to land on U1.93, which is the same
island as the y=38 F.Cu run. P0.15 west wrap (x=41.75) is not touched.
Minimum x on this route is 31.110 (>24.2). Maximum y is 37.250 (the y=44.60
B.Cu pocket is not used).

Reason: COEX0 open closed without a new short, clearance, crossing, or hole hit. Straight F.Cu was not used. One via because a west F.Cu jog cannot land.

### Segments (0.18 mm)

| layer | start | end | width |
| --- | --- | --- | --- |
| B.Cu | (31.110, 22.000) | (32.250, 22.000) | 0.18 mm |
| B.Cu | (32.250, 22.000) | (32.250, 30.500) | 0.18 mm |
| B.Cu | (32.250, 30.500) | (37.000, 30.500) | 0.18 mm |
| F.Cu | (37.000, 30.500) | (37.000, 35.900) | 0.18 mm |
| F.Cu | (37.000, 35.900) | (38.750, 35.900) | 0.18 mm |
| F.Cu | (38.750, 35.900) | (38.750, 37.250) | 0.18 mm |

Via: (37.000, 30.500) through, dia 0.60 mm, drill 0.30 mm, net COEX0.

## Gate (GND islands waived)

- short/clear/cross/hole_clearance all zero: True
- COEX0 opens drop: 1 → 0
- no non-GND net gained an open: True 
- hole_to_hole did not increase: 1 → 1
- GND islands: WAIVED (11 → 11)
- **met: True**

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | COEX0 opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 64 | 0 | 0 | 0 | 0 | 1 | 11 | 1 |
| after (KEEP) | 63 | 0 | 0 | 0 | 0 | 1 | 11 | 0 |

## Protect checklist

- VDD_GPIO F.Cu polyline locked and still present
- P0.10 and P0.12 vias at x=47.0 not moved
- DEC0 B.Cu bridge (46.950, 30.900)–(48.100, 30.900) not ripped
- P0.15 west wrap segment count 42 → 42
- Class C C22/C23/C24, P0.22, P0.19, Stage-A VDD2, SIM_IO_C/SIM_CLK_C walls not ripped
- No U1 or header move
- y=44.60 B.Cu pocket not used
- RF keepout: this route stays east of x=24.2 (min x=31.110); no new digital under the matching network
- No Gerbers. No git commit.
