# PASS30AS_SUMMARY — P0.30

**Timestamp:** 2026-09-30 11:23 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** P0.30
**Via added:** yes, through via (112.40, 46.40) od 0.60 mm drill 0.30 mm
**Segments:** 8 (limit 8)
**Min foreign clearance (pre-Add, copper edge, tracks and via):** 0.29 mm vs {'net': 'GND', 'item': 'pad J7.SH [GND]'} (need ≥ 0.15)
**Min POWER/VIN clearance (pre-Add):** 0.7 mm vs {'net': 'VDD_GPIO', 'item': 'B.Cu VDD_GPIO (111.200,51.080)-(111.200,38.800)'} (need ≥ 0.20)
**Min hole clearance (pre-Add, foreign holes):** 0.56 mm vs viahole P0.06 @(107.400,47.200) (DRC ≥ 0.25)
**New via hole-to-hole (pre-Add):** 3.538 mm vs hole J11.2 [P0.31]
**Unconnected:** 61 → 60
**P0.30 opens:** 2 → 1
**GND zone islands:** 12 → 12 (waived)
**Short / clearance / crossing / hole_clearance:** 0 / 0 / 0 / 0
**hole_to_hole:** 1 → 1

## Why this path

Straight F.Cu between pad J13.15 and pad J11.1 is not used. Remeasured blockers still sit on that chord (pad-edge gap {'j13_15': [99.56, 76.0], 'j11_1': [116.0, 46.0], 'pad_edge_gap_mm': 32.207, 'start_on_j13_15': True, 'end_on_j11_1': True}). Straight-line hits under 0.15 mm: {
  "P0.04": {
    "clearance_mm": 0.0,
    "net": "P0.04",
    "power": false,
    "item": "F.Cu P0.04 (113.800,49.200)-(113.800,36.800)"
  },
  "P0.31": {
    "clearance_mm": 0.0,
    "net": "P0.31",
    "power": false,
    "item": "F.Cu P0.31 (102.600,75.500)-(103.050,47.100)"
  },
  "VDD_GPIO": {
    "clearance_mm": 0.0,
    "net": "VDD_GPIO",
    "power": true,
    "item": "F.Cu VDD_GPIO (105.100,67.080)-(105.100,51.080)"
  },
  "GND": {
    "clearance_mm": 0.0,
    "net": "GND",
    "power": false,
    "item": "pad J15.6 [GND]"
  }
}

The jog leaves J13.15 on the north side of the annular ring, runs north to y=74.70 (clear of J13.16), east to x=101.20 (east of GND via (100, 70) and the J7 shield, west of the locked P0.31 run), north to y=46.40 (north of the P0.31 y=47.10 segment, west of the P0.06/P0.04 fence), and east to a single via at (112.40, 46.40). B.Cu then drops to y=45.00 and runs the east gutter at x=117.60 into J11.1, staying off the P0.31 landing on J11.2 and ≥0.20 mm from the B.Cu VDD_GPIO trunk. The sealed B.Cu pocket y≈44.60, x≈81.8–97.3 is not used. Min x = 99.56 (east of RF keepout x=24.2). No trunk was ripped.

## Segments

| layer | start | end | width |
| --- | --- | --- | --- |
| F.Cu | (99.56, 75.28) | (99.56, 74.70) | 0.18 mm |
| F.Cu | (99.56, 74.70) | (101.20, 74.70) | 0.18 mm |
| F.Cu | (101.20, 74.70) | (101.20, 46.40) | 0.18 mm |
| F.Cu | (101.20, 46.40) | (112.40, 46.40) | 0.18 mm |
| B.Cu | (112.40, 46.40) | (112.40, 45.00) | 0.18 mm |
| B.Cu | (112.40, 45.00) | (117.60, 45.00) | 0.18 mm |
| B.Cu | (117.60, 45.00) | (117.60, 46.00) | 0.18 mm |
| B.Cu | (117.60, 46.00) | (116.70, 46.00) | 0.18 mm |

## Gate

KEEP. P0.30 opens 2→1. No other non-GND net gained an open. short/clearance/crossing/hole_clearance 0. hole_to_hole 1→1. Foreign clearance 0.29 mm. POWER clearance 0.7 mm. GND islands 12→12 (waived).

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | P0.30 opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 61 | 0 | 0 | 0 | 0 | 1 | 12 | 2 |
| after | 60 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |

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
    "p022_locked_track": true,
    "p031_locked_run": true
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
    "p022_locked_track": true,
    "p031_locked_run": true
  },
  "moved": []
}

No header or U1 move. No Gerbers. No git commit. P0.14 not started. P0.31 leftover (U1.89) not touched.
