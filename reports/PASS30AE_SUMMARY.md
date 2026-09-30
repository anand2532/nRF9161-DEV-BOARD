# PASS30AE_SUMMARY — Package C_west_longhaul_J14_J15

**Timestamp:** 2026-09-30 03:37 IST
**KiCad:** 9.0.2+dfsg-1 via `/usr/bin/python3`
**Decision:** **REVERT**
**Phase:** COMPLETE_REVERTED
**Landing kept:** None
**Final XY:** J14=[104.0, 48.0] J15=[104.0, 62.0] (frozen) J13=[64.0, 76.0] J10=[116.0, 28.0] J11=[116.0, 46.0] J16=[108.0, 8.0] J9=[116.0, 8.0] J17=[108.0, 26.0] J12=[6.0, 76.0] U1=[36.0, 32.0]
**Class C XY:** C22=[17.5, 31.75] C23=[24.8, 34.0] C24=[15.0, 31.8] L1=[22.0, 32.0] L2=[20.0, 33.0] U3=[26.5, 47.0]

## DRC

| | unconnected | shorting | clearance | crossing |
| --- | ---: | ---: | ---: | ---: |
| Before | 64 | 0 | 0 | 0 |
| After | 64 | 0 | 0 | 0 |

**Delta unconnected:** 0
**Gate:** BLOCKED — full revert; unconnected 64→64; shorting/clearance/crossing=0/0/0

Place+reattach only. No new long-haul MAGPIO/MIPI/COEX1 through RF keepout (x 0–24.2, y 20–64).

## Attempts

### preferred_west_m3
- targets: {'J14': [101.0, 48.0], 'J15': [101.0, 62.0]}
- mid: {'unconnected_items': 64, 'shorting_items': 3, 'clearance': 2, 'tracks_crossing': 0, 'copper_edge_clearance': 0, 'silk_over_copper': 53, 'silk_overlap': 165, 'hole_clearance': 0, 'via_dangling': 72, 'track_dangling': 15}
- clean: False protect: True
- ripped=5 nets=['COEX0', 'COEX2', 'VDD_GPIO'] reattached=5 snapped=0
- reject: dirty_drc
- collide head: [{"type": "clearance", "description": "Clearance violation (netclass 'Default' clearance 0.1000 mm; actual 0.0900 mm)", "items": [{"description": "PTH pad 1 [MAGPIO0] of J14", "pos": {"x": 101.0, "y": 48.0}}, {"description": "Track [nRESET] on B.Cu, length 32.8000 mm", "pos": {"x": 101.68, "y": 58.8}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets MAGPIO1 and GND)", "items": [{"description": "PTH pad 2 [MAGPIO1] of J14", "pos": {"x": 101.0, "y": 49.27}}, {"description": "Pad SH [GND] of J7 on F.Cu", "pos": {"x": 100.595, "y": 49.69}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets MAGPIO2 and GND)", "items": [{"description": "PTH pad 3 [MAGPIO2] of J14", "pos": {"x": 101.0, "y": 50.54}}, {"description": "Pad SH [GND] of J7 on F.Cu", "pos": {"x": 100.595, "y": 49.69}}]}, {"type": "shorting_items", "description": "Items shorting two 

### alt_m2_m2
- targets: {'J14': [102.0, 46.0], 'J15': [102.0, 60.0]}
- mid: {'unconnected_items': 64, 'shorting_items': 11, 'clearance': 2, 'tracks_crossing': 0, 'copper_edge_clearance': 0, 'silk_over_copper': 50, 'silk_overlap': 156, 'hole_clearance': 0, 'via_dangling': 72, 'track_dangling': 15}
- clean: False protect: True
- ripped=5 nets=['COEX0', 'COEX2', 'VDD_GPIO'] reattached=10 snapped=0
- reject: dirty_drc
- collide head: [{"type": "shorting_items", "description": "Items shorting two nets (nets COEX2 and GND)", "items": [{"description": "Track [COEX2] on B.Cu, length 2.0000 mm", "pos": {"x": 102.0, "y": 62.54}}, {"description": "PTH pad 4 [GND] of J15", "pos": {"x": 102.0, "y": 63.81}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets nRESET and MAGPIO0)", "items": [{"description": "Track [nRESET] on B.Cu, length 22.8000 mm", "pos": {"x": 102.4, "y": 36.0}}, {"description": "PTH pad 1 [MAGPIO0] of J14", "pos": {"x": 102.0, "y": 46.0}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets nRESET and MAGPIO0)", "items": [{"description": "Track [nRESET] on B.Cu, length 31.6808 mm", "pos": {"x": 102.33, "y": 27.125833}}, {"description": "PTH pad 1 [MAGPIO0] of J14", "pos": {"x": 102.0, "y": 46.0}}]}, {"type": "shorting_items", "description": "Items shorting two 

## Protect checklist (after)

```
{
  "stage_a": {
    "VDD_nRF_via_north": true,
    "VDD2_vias": 2,
    "VDD2_present": true
  },
  "p015_west": 21,
  "p015_west_before": 21,
  "class_c": {
    "ok": true,
    "gnd_vias": {
      "C22": true,
      "C23": true,
      "C24": true
    },
    "stub_tracks": {
      "C22": 1,
      "C23": 1,
      "C24": 1
    },
    "reasons": []
  },
  "rf_keepout_segs": 0,
  "rf_keepout_before": 0,
  "frozen_xy": {
    "J13": [
      64.0,
      76.0
    ],
    "J10": [
      116.0,
      28.0
    ],
    "J11": [
      116.0,
      46.0
    ],
    "J16": [
      108.0,
      8.0
    ],
    "J9": [
      116.0,
      8.0
    ],
    "J17": [
      108.0,
      26.0
    ],
    "J12": [
      6.0,
      76.0
    ],
    "U1": [
      36.0,
      32.0
    ]
  },
  "locked_extra": {
    "L1": [
      22.0,
      32.0
    ],
    "L2": [
      20.0,
      33.0
    ],
    "U3": [
      26.5,
      47.0
    ]
  },
  "ok": true,
  "reasons": []
}
```

## Policy

- J12 and SE column J13/J10/J11 frozen
- East duals J16/J9/J17 frozen (pass30ac revert)
- No A/B header moves, no Gerbers, no U1 move
- Class C C22/C23/C24 + L1/L2/U3 untouched
- No long-haul route through RF keepout

**Stop:** preferred dirty/reject (dirty_drc); Alt also dirty/reject (dirty_drc) — full revert to pre-edit; STOP placement

