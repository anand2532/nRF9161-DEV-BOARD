# PASS30AK_SUMMARY — replay pass30aj VDD_GPIO shove (GND islands waived)

**Timestamp:** 2026-09-30 10:05 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Path:** shove (replay of pass30aj; west attempted: False)
**Net:** VDD_GPIO
**Unconnected:** 64 → mid 64 → after 64
**VDD_GPIO opens:** 3 → mid 2 → after 2
**GND zone islands:** 10 → mid 11 → after 11 (increase WAIVED)
**Geometry matches pass30aj:** True

## Confirmed live coordinates

- F.Cu via island: net VDD_GPIO @ (40.17, 19.126) dia 0.8 drill 0.4
- U1 @ (36.0, 32.0) unmoved
- U1.12: net VDD_GPIO center (44.0, 31.5) size [0.8, 0.3] bbox [43.6, 31.35, 44.4, 31.65] F.Cu only

## Path

Exact replay of `scripts/final_pass30aj.py` (`apply_shove` + `add_poly`). Not a new corridor. Shove, not west. The shove stays east of the P0.15 vertical keep (x=41.75, y=23.10–26.75) and does not rip or shove P0.15. The pass30ai east spine at x=45.5 was not repeated. Straight line was not used. No new via on VDD_GPIO. P0.08 and P0.11 were not shoved.

shove geometry does not enter the P0.15 keep (x=41.75, y=23.10-26.75); west approach not used.

### VDD_GPIO polyline (0.18 mm F.Cu)

| # | start | end | width |
| --- | --- | --- | --- |
| 1 | (40.170, 19.126) | (40.170, 20.200) | 0.18 mm F.Cu |
| 2 | (40.170, 20.200) | (45.900, 20.200) | 0.18 mm F.Cu |
| 3 | (45.900, 20.200) | (45.900, 25.400) | 0.18 mm F.Cu |
| 4 | (45.900, 25.400) | (47.550, 25.400) | 0.18 mm F.Cu |
| 5 | (47.550, 25.400) | (47.550, 31.500) | 0.18 mm F.Cu |
| 6 | (47.550, 31.500) | (44.000, 31.500) | 0.18 mm F.Cu |

### Nets shoved

- **P0.12**: F stub + dangling via (47.400, 27.500) → (47.000, 27.500). Pad connection kept.
- **P0.10**: F stub + dangling via (47.400, 28.500) → (47.000, 28.500). Pad connection kept.
- **DEC0**: removed 4 coincident F horizontals (44.000, 31.000)–(48.720, 31.000). Left F stub ends at via (46.950, 30.900); B.Cu bridge to via (48.100, 30.900); right F stub returns to (48.720, 31.000) so the DEC0 trunk is continuous. Dangling via (47.800, 31.200) moved to (45.400, 30.550) with F riser (45.400, 31.000)–(45.400, 30.550).
- Not shoved: P0.08, P0.11, P0.15.

## Gate (GND islands waived)

- short/clear/cross/hole all zero: True
- VDD_GPIO opens drop (3→2 or better): True (3 → 2)
- no non-GND net gained an open: True
- GND islands: WAIVED (do not revert for 10→11)
- P0.15 segment count still 42: True (42 → 42)
- **met: True**

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 64 | 0 | 0 | 0 | 0 | 10 | 3 |
| mid (shove) | 64 | 0 | 0 | 0 | 0 | 11 | 2 |
| after (KEEP) | 64 | 0 | 0 | 0 | 0 | 11 | 2 |

Headline unconnected can stay flat when the VDD_GPIO open closes and one F.Cu GND zone island appears. That island is waived on this pass. Pre-existing hole_to_hole (P0.02×P0.02) is unchanged and is not part of this gate.

## Keep audit

Edit kept. Geometry is the pass30aj shove plus the same six-segment F.Cu polyline. Board sha256 ecb3cc4eb4034efb… differs from the pre-edit backup cb0addfddd13cba3… as expected. GND island increase was waived and was not a revert reason.

F.Cu GND filled outlines 15 → 16.

Outline delta (area mm², bbox):

- new: area 19.682 bbox [41.08, 20.54, 47.21, 27.16]
- new: area 131.562 bbox [39.97, 3.74, 53.31, 25.06]
- new: area 6921.852 bbox [0.5, 0.5, 119.5, 79.5]
- replaced: area 185.979 bbox [37.59, 3.74, 53.31, 27.16]
- replaced: area 6925.47 bbox [0.5, 0.5, 119.5, 79.5]

## Protect checklist

- y=44.60 B.Cu pocket: no track
- SIM_IO_C / SIM_CLK_C walls: not ripped
- U1 and headers: not moved
- Class C, Stage-A VDD2, P0.22, P0.19, P0.15 west wrap / trunk: not ripped
- P0.08 and P0.11 copper: not shoved (not on this polyline)
- No Gerbers. No git commit. COEX0 not started.

