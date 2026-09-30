# PASS30AQ_SUMMARY — P0.31

**Timestamp:** 2026-09-30 11:01 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.31
**Via added:** no
**Segments:** 6 (limit 8)
**Min foreign clearance (pre-Add, copper edge):** 0.23 mm vs {'net': 'GND', 'item': 'via GND @(110.000,50.000)'} (need ≥ 0.15)
**Min POWER/VIN clearance (pre-Add):** 0.245 mm vs {'net': 'VDD_GPIO', 'item': 'F.Cu VDD_GPIO (105.100,51.080)-(116.000,51.080)'} (need ≥ 0.20)
**Min hole clearance (pre-Add):** 0.38 mm vs viahole GND @(110.000,50.000) (DRC ≥ 0.25)
**Unconnected:** 62 → 61
**P0.31 opens:** 2 → 1
**GND zone islands:** 12 → 12 (waived)
**Short / clearance / crossing / hole_clearance:** 0 / 0 / 0 / 0
**hole_to_hole:** 1 → 1

## Why this path

Straight F.Cu between pad J13.16 and pad J11.2 is not used. Remeasured blockers still sit on that chord (pad-edge gap {'j13_16': [102.1, 76.0], 'j11_2': [116.0, 48.54], 'pad_edge_gap_mm': 29.078, 'start_on_j13_16': True, 'end_on_j11_2': True}): P0.22 via and F.Cu (104.50, 71.50)–(106.50, 71.50), GND via (110, 50), VDD_GPIO F.Cu (104.00, 67.08)–(107.18, 67.08) and (105.10, 51.08)–(116.00, 51.08), P0.04 F.Cu (114.80, 52.50)–(108.45, 52.50). Straight-line hits under 0.15 mm: {
  "GND": {
    "clearance_mm": 0.0,
    "net": "GND",
    "power": false,
    "item": "via GND @(110.000,60.000)"
  },
  "P0.22": {
    "clearance_mm": 0.0,
    "net": "P0.22",
    "power": false,
    "item": "F.Cu P0.22 (104.500,71.500)-(106.500,71.500)"
  },
  "P0.04": {
    "clearance_mm": 0.0,
    "net": "P0.04",
    "power": false,
    "item": "F.Cu P0.04 (114.800,52.500)-(108.450,52.500)"
  },
  "VDD_GPIO": {
    "clearance_mm": 0.0,
    "net": "VDD_GPIO",
    "power": true,
    "item": "F.Cu VDD_GPIO (104.000,67.080)-(107.180,67.080)"
  }
}

The jog leaves J13.16 on the north side of the header, runs west of J14 at x=103.05 down to y=47.10 (north of J14.1), steps east to x=106.70 (east of J14, west of the P0.06 via), drops to y=50.62 (north of the locked VDD_GPIO trunk at y=51.08, south of the P0.04 corner at (113.8, 49.2), clear of the GND via at (110, 50)), runs east to x=114.90, then south and into J11.2. No trunk was ripped. No locked copper was ripped. No via. y=44.60 B.Cu pocket not used. Min x = 102.60 (east of RF keepout x=24.2).

## Segments

| layer | start | end | width |
| --- | --- | --- | --- |
| F.Cu | (102.60, 75.50) | (103.05, 47.10) | 0.18 mm |
| F.Cu | (103.05, 47.10) | (106.70, 47.10) | 0.18 mm |
| F.Cu | (106.70, 47.10) | (106.70, 50.62) | 0.18 mm |
| F.Cu | (106.70, 50.62) | (114.90, 50.62) | 0.18 mm |
| F.Cu | (114.90, 50.62) | (114.90, 48.80) | 0.18 mm |
| F.Cu | (114.90, 48.80) | (115.55, 48.80) | 0.18 mm |

## Gate

KEEP. P0.31 opens 2→1. No other non-GND net gained an open. short/clearance/crossing/hole_clearance 0. hole_to_hole 1→1. Foreign clearance 0.23 mm. POWER clearance 0.245 mm. GND islands 12→12 (waived).

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | P0.31 opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 62 | 0 | 0 | 0 | 0 | 1 | 12 | 2 |
| after | 61 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |

## Protect

{
  "before": {
    "ap_run": true,
    "ap_via": true,
    "y7050": true,
    "u1_12_poly": true,
    "dec0_bridge": true,
    "coex0_via": true,
    "coex0_runs": true,
    "p010": true,
    "p012": true,
    "p015": 42,
    "p004_locked_track": true,
    "p022_locked_track": true
  },
  "after_add": {
    "ap_run": true,
    "ap_via": true,
    "y7050": true,
    "u1_12_poly": true,
    "dec0_bridge": true,
    "coex0_via": true,
    "coex0_runs": true,
    "p010": true,
    "p012": true,
    "p015": 42,
    "p004_locked_track": true,
    "p022_locked_track": true
  },
  "moved": []
}

No header or U1 move. No Gerbers. No git commit. P0.30 not started.
