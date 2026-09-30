# PASS30AI_SUMMARY — VDD_GPIO via island to U1.12

**Timestamp:** 2026-09-30 09:41 IST
**KiCad:** 9.0.2
**Decision:** **REVERT**
**Net:** VDD_GPIO
**Via used:** False
**Unconnected:** 64 → mid 64 → after 64

## Confirmed live coordinates

- F.Cu via island: net VDD_GPIO @ (40.17, 19.126) dia 0.8 drill 0.4
- U1 @ (36.0, 32.0) unmoved
- U1.12: net VDD_GPIO center (44.0, 31.5) size [0.8, 0.3] bbox [43.6, 31.35, 44.4, 31.65] F.Cu only

## One geometry (not retried)

Straight line forbidden (shorts P0.15 keep and P0.16). Three F.Cu 0.18 mm segments. Segments 1–2 jog east of the P0.16 via@(40.700,20.800) and stay east of the P0.15 vertical keep (x=41.75). Segment 3 is the landing onto U1.12. No via. P0.15 trunk not ripped. No header/U1 move.

| # | start | end | width |
| --- | --- | --- | --- |
| 1 | (40.170, 19.126) | (45.500, 20.150) | 0.18 mm F.Cu |
| 2 | (45.500, 20.150) | (45.500, 26.050) | 0.18 mm F.Cu |
| 3 | (45.500, 26.050) | (44.000, 31.500) | 0.18 mm F.Cu |

## Gate

- short/clear/cross/hole all zero: False
- unconnected drop ≥ 1: False (delta mid 0)
- **met: False**

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance |
| --- | ---: | ---: | ---: | ---: | ---: |
| before | 64 | 0 | 0 | 0 | 0 |
| mid (attempt) | 64 | 0 | 0 | 8 | 0 |
| after (REVERT) | 64 | 0 | 0 | 0 | 0 |

## Revert audit — what the landing hit

Full byte restore from `.mcp-backups/pass30ai/pre-edit.kicad_pcb` (sha256 matches pre-edit). P0.15 trunk not ripped. No second geometry.

Segments 1–2 (the jog east of P0.16 via@(40.700, 20.800), east of the P0.15 vertical keep at x=41.75) produced **no** short, clearance, or crossing. Segment 3, F.Cu (45.500, 26.050)→(44.000, 31.500), length 5.6527 mm, is the dirty landing.

**tracks_crossing = 8** (shorting 0, clearance 0, hole_clearance 0), all on that landing segment:

- VDD_GPIO × P0.11 F.Cu (44.000, 28.000)–(46.500, 28.000)
- VDD_GPIO × DEC0 F.Cu (44.000, 31.000)–(48.720, 31.000) — four coincident DEC0 tracks, four violations
- VDD_GPIO × P0.12 F.Cu (44.000, 27.500)–(47.400, 27.500)
- VDD_GPIO × P0.08 F.Cu (44.000, 30.000)–(46.200, 30.000)
- VDD_GPIO × P0.10 F.Cu (44.000, 28.500)–(47.400, 28.500)

P0.15 keep was not crossed.

**Unconnected count did not drop (64→64).** Per net: VDD_GPIO 3→2 (Pad 12 of U1 was no longer an open ratsnest endpoint — the polyline did reach the pad) and GND zone islands 10→11 after the zone refill that the attempt ran before DRC. Net zero. Gate needs the headline count to fall by ≥ 1 **and** crossing = 0. Both failed.

No via. U1.12 is F.Cu-only. One via cannot cross the north pad-row wall (0.20 mm gaps between 0.30 mm pads; a 0.18 mm track at POWER clearance 0.15 mm needs 0.48 mm). The F.Cu free-space around the via island does not reach U1.12 without crossing that wall or these east escapes.

## Protect checklist

- y=44.60 B.Cu pocket: no track
- SIM_IO_C / SIM_CLK_C walls: not ripped
- U1 and headers: not moved
- Class C, Stage-A VDD2, P0.22, P0.19, P0.15 west wrap / trunk: not ripped
- No Gerbers. No git commit. COEX0 not started.

