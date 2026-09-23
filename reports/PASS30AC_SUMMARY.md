# PASS30AC_SUMMARY — Package A_SE_duals (excl J12)

**Timestamp:** 2026-09-23 13:30 IST
**Decision:** **REVERT**
**Phase:** COMPLETE_REVERTED
**Landing kept:** None
**Final XY:** J16=[108.0, 8.0] J9=[116.0, 8.0] J17=[108.0, 26.0] J12=[6.0, 76.0] (frozen) J13=[64.0, 76.0] J10=[116.0, 28.0] J11=[116.0, 46.0] U1=[36.0, 32.0]
**Class C XY:** C22=[17.5, 31.75] C23=[24.8, 34.0] C24=[15.0, 31.8]

## DRC

| | unconnected | shorting | clearance | crossing |
| --- | ---: | ---: | ---: | ---: |
| Before | 64 | 0 | 0 | 0 |
| After | 64 | 0 | 0 | 0 |

**Delta unconnected:** 0
**Gate:** BLOCKED — reverted to pass30z keep; unconnected 64→64; shorting/clearance/crossing=0/0/0

## Attempts

### preferred_west_m2.54
- targets: {'J16': [105.46, 8.0], 'J9': [113.46, 8.0], 'J17': [105.46, 26.0]}
- mid: {'unconnected_items': 64, 'shorting_items': 7, 'clearance': 1, 'tracks_crossing': 4, 'copper_edge_clearance': 0, 'silk_over_copper': 50, 'silk_overlap': 149, 'hole_clearance': 0, 'via_dangling': 72, 'track_dangling': 16}
- clean: False protect: True
- ripped=9 reattached=11 bus=4 row=0
- reject: dirty_drc
- collide head: [{"type": "clearance", "description": "Clearance violation (netclass 'POWER' clearance 0.1500 mm; actual 0.0700 mm)", "items": [{"description": "Track [COEX2] on B.Cu, length 39.9400 mm", "pos": {"x": 105.1, "y": 24.6}}, {"description": "Track [VDD_GPIO] on B.Cu, length 5.1400 mm", "pos": {"x": 105.46, "y": 31.08}}]}, {"type": "tracks_crossing", "description": "Tracks crossing", "items": [{"description": "Track [P0.01] on B.Cu, length 55.5000 mm", "pos": {"x": 105.55, "y": 15.2}}, {"description": "Track [VDD_GPIO] on B.Cu, length 5.1400 mm", "pos": {"x": 105.46, "y": 31.08}}]}, {"type": "tracks_crossing", "description": "Tracks crossing", "items": [{"description": "Track [VDD_GPIO] on B.Cu, length 8.0000 mm", "pos": {"x": 113.46, "y": 18.16}}, {"description": "Track [P0.04] on B.Cu, length

### alt_south_north_y_deltas
- targets: {'J16': [108.0, 10.54], 'J9': [116.0, 10.54], 'J17': [108.0, 24.0]}
- mid: {'unconnected_items': 68, 'shorting_items': 11, 'clearance': 5, 'tracks_crossing': 7, 'copper_edge_clearance': 0, 'silk_over_copper': 39, 'silk_overlap': 147, 'hole_clearance': 0, 'via_dangling': 73, 'track_dangling': 17}
- clean: False protect: True
- ripped=9 reattached=13 bus=0 row=40
- reject: dirty_drc
- collide head: [{"type": "tracks_crossing", "description": "Tracks crossing", "items": [{"description": "Track [P0.22] on F.Cu, length 2.2000 mm", "pos": {"x": 112.5, "y": 29.9}}, {"description": "Track [VDD_GPIO] on F.Cu, length 9.0800 mm", "pos": {"x": 114.4, "y": 38.16}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets VDD_GPIO and P0.22)", "items": [{"description": "Track [VDD_GPIO] on F.Cu, length 9.0800 mm", "pos": {"x": 114.4, "y": 38.16}}, {"description": "Via [P0.22] on F.Cu - B.Cu", "pos": {"x": 114.7, "y": 29.9}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets VDD_GPIO and GND)", "items": [{"description": "Track [VDD_GPIO] on F.Cu, length 27.9616 mm", "pos": {"x": 114.4, "y": 29.08}}, {"description": "Via [GND] on F.Cu - B.Cu", "pos": {"x"


## Blockers (why both landings failed)

### Preferred west −2.54 → J16/J17@(105.46,*) J9@(113.46,8)
- Mid: shorting=7 clearance=1 crossing=4
- J17.3 VDD_GPIO @x105.46 shorts/crosses **P0.01 B H@y15.2** (and COEX2 B clearance)
- J16.4 P0.09 @ (105.46,15.62) shorts **P0.01 B** stub
- J16.5 VDD_GPIO shorts **P0.06 B** @(106.35,22)
- J9.6 GND @(113.46,20.7) shorts **P0.04 B** column @x113.8
- VDD_GPIO reattach H crossings vs P0.04 B @y19.43
- Protect checklist still OK (Class C / Stage A / frozen SE / J12) — dirty was copper-only

### Alt Y deltas → J16/J9 south +2.54 / J17 north −2.0
- Mid: shorting=11 clearance=5 crossing=7 · **unconnected spike 64→68**
- VDD_GPIO F/B reattach after Y shift shorts **P0.22 via@(114.7,29.9)** and **P0.04 via@(113.8,36.8)**
- VDD_GPIO crossings vs P0.04/P0.06 B; POWER clearance vs GND vias
- Crowds J16↔J17 pad band (south + north toward each other)

## Outcome
Full atomic package revert to **pass30z KEEP** (post pass30ab revert). No footprint moves retained.
J12 unmoved. SE column J13/J10/J11 frozen. Class C C22/C23/C24 preserved. No Gerbers. No B'' execute.

**Next:** Package A west corridor blocked by P0.01 B@y15.2 + P0.04/P0.06 east stubs — needs copper pre-clear or different package. SE column still frozen pending B'' proposals (pass30ad).

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
    "fps_ok": true,
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
    "ok": true,
    "reasons": []
  },
  "frozen_xy": {
    "J12": [
      6.0,
      76.0
    ],
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
    "U1": [
      36.0,
      32.0
    ]
  },
  "ok": true,
  "reasons": []
}
```

## Policy

- J12: DO NOT MOVE (honored)
- SE column J13/J10/J11: FROZEN (honored)
- No B'' execute / No Gerbers / No U1 move
- Class C C22/C23/C24 protected

**Stop:** preferred dirty/reject (dirty_drc); Alt also dirty/reject (dirty_drc) — full revert to pass30z keep; STOP (no further landings)

