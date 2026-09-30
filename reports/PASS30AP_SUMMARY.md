# PASS30AP_SUMMARY — last VDD_GPIO open

**Timestamp:** 2026-09-30 10:47 IST
**KiCad:** 9.0.2
**Decision:** **KEEP**
**Net:** VDD_GPIO
**Via added:** no (starts on the existing via at (76.4375, 39.050))
**Segments:** 8 (limit 8)
**Min POWER/VIN clearance (pre-Add, copper edge):** 2.2373 mm (need ≥ 0.20)
**Min foreign clearance (pre-Add):** 0.2073 mm vs {'net': 'SIM_CLK', 'item': 'F.Cu SIM_CLK (71.680,42.400)-(70.900,42.400)'}
**Unconnected:** 63 → 62
**VDD_GPIO opens:** 1 → 0
**GND zone islands:** 12 → 12 (waived)
**Short / clearance / crossing / hole_clearance:** 0 / 0 / 0 / 0
**hole_to_hole:** 1 → 1

## Why this path

Straight F.Cu from pad U2.5 to pad J18.9 is not used. Remeasured blockers still sit on that line: ENABLE F.Cu (72.860, 40.950)–(72.860, 42.400) and (72.860, 42.400)–(74.200, 42.400) plus pad U2.3; SIM_CLK F.Cu (71.680, 44.000)–(70.900, 44.000) and (71.680, 44.000)–(71.680, 42.400); P0.20 F.Cu (55.780, 60.900)–(74.160, 60.900) then south at x=74.160. Pad-edge gap U2.5↔J18.9 is {'u2_5': [75.138, 39.05], 'j18_9': [58.32, 62.0], 'pad_edge_gap_mm': 27.03, 'end_on_j18_9': True}.

The jog leaves the existing F.Cu via just east of U2.5, steps south and west around the ENABLE via at (74.200, 42.400) and the SIM_CLK stub at x≈70.9–71.7, then runs southwest to x=54.438 (west of J18.8 / the P0.20 trunk), drops south of that trunk, and enters J18.9 from the southwest. No trunk was ripped. No locked copper was ripped. No new via. y=44.60 B.Cu pocket not used. Min x = 54.438 (east of RF keepout x=24.2).

## Segments

| layer | start | end | width |
| --- | --- | --- | --- |
| F.Cu | (76.4375, 39.050) | (76.4375, 41.550) | 0.18 mm |
| F.Cu | (76.4375, 41.550) | (74.438, 43.050) | 0.18 mm |
| F.Cu | (74.438, 43.050) | (72.438, 43.050) | 0.18 mm |
| F.Cu | (72.438, 43.050) | (71.938, 42.050) | 0.18 mm |
| F.Cu | (71.938, 42.050) | (70.438, 41.550) | 0.18 mm |
| F.Cu | (70.438, 41.550) | (54.438, 61.050) | 0.18 mm |
| F.Cu | (54.438, 61.050) | (54.438, 63.550) | 0.18 mm |
| F.Cu | (54.438, 63.550) | (58.200, 62.700) | 0.18 mm |

## Gate

KEEP. VDD_GPIO opens 1→0. No other non-GND net gained an open. short/clearance/crossing/hole_clearance 0. hole_to_hole 1→1. POWER clearance 2.2373 mm. GND islands 12→12 (waived).

## DRC

| | unconnected | shorting | clearance | tracks_crossing | hole_clearance | hole_to_hole | GND islands | VDD_GPIO opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| before | 63 | 0 | 0 | 0 | 0 | 1 | 12 | 1 |
| after | 62 | 0 | 0 | 0 | 0 | 1 | 12 | 0 |

## Protect

{
  "before": {
    "y7050": true,
    "u1_12_poly": true,
    "dec0_bridge": true,
    "coex0_via": true,
    "coex0_runs": true,
    "p010": true,
    "p012": true,
    "p015": 42
  },
  "after_add": {
    "y7050": true,
    "u1_12_poly": true,
    "dec0_bridge": true,
    "coex0_via": true,
    "coex0_runs": true,
    "p010": true,
    "p012": true,
    "p015": 42
  },
  "moved": []
}

No header or U1 move. No Gerbers. No git commit.
