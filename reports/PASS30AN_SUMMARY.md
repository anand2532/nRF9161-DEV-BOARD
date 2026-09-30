# PASS30AN_SUMMARY — VDD_GPIO east island, y nudge (GND islands waived)

**Timestamp:** 2026-09-30 10:33 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** VDD_GPIO
**Via:** no
**y used:** 7.05
**Measured clearance to D3.1 [VIN] (75.213, 8.000), horizontal copper edge:** 0.385 mm
**Requirement:** >= 0.20 mm to D3.1 and every other POWER/VIN copper
**Segments:** 4 (limit 6)
**Unconnected:** 63 → 63
**VDD_GPIO opens:** 2 → 1
**GND zone islands:** 11 → 12 (increase WAIVED)

## Why this attempt

Replay of the reverted pass30am VDD_GPIO route. That path failed because the
y=7.300 horizontal was 0.135 mm from pad D3.1 [VIN] at (75.213, 8.000); POWER
netclass wants 0.150 mm. This pass moves only that horizontal north, to clear
0.20 mm, and reties the x=71.300 vertical. Other corners stay
(71.300, 8.000), (81.500, 13.500), (86.510, 26.000). No via. No second path.
The locked U1.12 polyline is not repeated. North limit is y=6.800.

## Pre-commit clearance (pad geometry + 0.18 mm track)

Measured with `SHAPE.GetClearance` on the solid 0.18 mm track against pad D3.1
and every other F.Cu POWER/VIN track, via annular, and pad, before `board.Add`.

- Candidate y=7.050: D3.1 horizontal 0.385 mm, route min POWER/VIN 0.385 mm, meets 0.20: True
- Candidate y=6.800: not measured (y=7.050 already met 0.20 mm)
- Chosen y: 7.05

Reason: KEEP. Horizontal at y=7.050 clears D3.1 by 0.385 mm (>= 0.20 mm) and other POWER/VIN copper by 0.385 mm. VDD_GPIO opens 2→1. No new short, clearance, crossing, or hole hit. No via. Locked COEX0 and the U1.12 polyline were not ripped.

### Segments (0.18 mm)

| layer | start | end | width |
| --- | --- | --- | --- |
| F.Cu | (71.300, 8.000) | (71.300, 7.050) | 0.18 mm |
| F.Cu | (71.300, 7.050) | (77.300, 7.050) | 0.18 mm |
| F.Cu | (77.300, 7.050) | (81.500, 13.500) | 0.18 mm |
| F.Cu | (81.500, 13.500) | (86.510, 26.000) | 0.18 mm |

No via added.

## Gate (GND islands waived)

- mid short/clear/cross/hole_clearance: 0/0/0/0
- mid VDD_GPIO opens: 2 → 1
- no non-GND net gained an open: True 
- hole_to_hole: 1 → 1
- GND islands on the attempt: 11 → 12 (WAIVED)
- **met: True**

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 63 | 0 | 0 | 0 | 0 | 1 | 11 | 2 |
| mid | 63 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |
| after (KEEP) | 63 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |

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
