# PASS30AB_SUMMARY — Package B' only

**Timestamp:** 2026-09-23 13:27 IST
**Decision:** **REVERT**
**Phase:** COMPLETE_REVERTED
**Landing kept:** None
**Final XY:** J13=[64.0, 76.0] J10=[116.0, 28.0] J11=[116.0, 46.0] U1=[36.0, 32.0]
**Class C XY:** C22=[17.5, 31.75] C23=[24.8, 34.0] C24=[15.0, 31.8]

## DRC

| | unconnected | shorting | clearance | crossing |
| --- | ---: | ---: | ---: | ---: |
| Before | 64 | 0 | 0 | 0 |
| After | 64 | 0 | 0 | 0 |

**Delta unconnected:** 0
**Gate:** BLOCKED — reverted to pass30z keep; unconnected 64→64; shorting/clearance/crossing=0/0/0

## Attempts

### preferred_J13_64_75
- targets: {'J13': [64.0, 75.0], 'J10': [115.0, 28.0], 'J11': [115.0, 46.0]}
- mid: {'unconnected_items': 64, 'shorting_items': 4, 'clearance': 1, 'tracks_crossing': 0, 'copper_edge_clearance': 0, 'silk_over_copper': 55, 'silk_overlap': 185, 'hole_clearance': 1, 'via_dangling': 72, 'track_dangling': 15}
- clean: False protect: True
- ripped=18 reattached=21 bus=6
- reject: dirty_drc
- collide head: [{"type": "shorting_items", "description": "Items shorting two nets (nets P0.17 and P0.01)", "items": [{"description": "PTH pad 2 [P0.17] of J13", "pos": {"x": 66.54, "y": 75.0}}, {"description": "Track [P0.01] on F.Cu, length 6.0000 mm", "pos": {"x": 62.0, "y": 74.5}}]}, {"type": "clearance", "description": "Clearance violation (netclass 'Default' clearance 0.1000 mm; actual 0.0401 mm)", "items": [{"description": "PTH pad 3 [P0.18] of J13", "pos": {"x": 69.08, "y": 75.0}}, {"description": "Via [P0.01] on F.Cu - B.Cu", "pos": {"x": 68.0, "y": 74.5}}]}, {"type": "shorting_items", "description":

### alt1_J13_64_74.5
- targets: {'J13': [64.0, 74.5], 'J10': [115.5, 28.0], 'J11': [115.5, 46.0]}
- mid: {'unconnected_items': 64, 'shorting_items': 3, 'clearance': 2, 'tracks_crossing': 0, 'copper_edge_clearance': 0, 'silk_over_copper': 55, 'silk_overlap': 145, 'hole_clearance': 2, 'via_dangling': 72, 'track_dangling': 15}
- clean: False protect: True
- ripped=18 reattached=21 bus=6
- reject: dirty_drc
- collide head: [{"type": "shorting_items", "description": "Items shorting two nets (nets P0.17 and P0.01)", "items": [{"description": "PTH pad 2 [P0.17] of J13", "pos": {"x": 66.54, "y": 74.5}}, {"description": "Track [P0.01] on F.Cu, length 6.0000 mm", "pos": {"x": 62.0, "y": 74.5}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets P0.18 and P0.01)", "items": [{"description": "PTH pad 3 [P0.18] of J13", "pos": {"x": 69.08, "y": 74.5}}, {"description": "Via [P0.01] on F.Cu - B.Cu", "pos": {"x": 68.0, "y": 74.5}}]}, {"type": "shorting_items", "description": "Items shorting two nets (


## Blockers (why both landings failed)

### Preferred J13(64,75) + J10/J11(115,*)
- J13.2 P0.17 @ y=75 shorts P0.01 F track @ y=74.5
- J13.3 P0.18 clearance to P0.01 via@(68.0, 74.5)
- J11 west: P0.04 F@x≈114.8 shorts J11.4 GND
- J10 west: VDD_GPIO F reattach stubs short J10.2 P0.22 and J10.3 P0.23
- Mid: short=4 clr=1 cross=0 hole=1

### Alt1 J13(64,74.5) + J10/J11(115.5,*)
- J13.2 P0.17 @ y=74.5 shorts same P0.01 F@y=74.5
- J13.3 P0.18 shorts P0.01 via@(68.0, 74.5)
- J13.1 P0.16 clearance to P0.08 via@(65.2, 73.95)
- J11 still shorts P0.04 F@x≈114.8
- J10.3 vs VDD_GPIO clearance (POWER 0.15)
- Mid: short=3 clr=2 cross=0 hole=2

## Outcome
Full atomic package revert to **pass30z KEEP**. No footprint moves retained. Class C C22/C23/C24 copper preserved. No Gerbers. No Package A / Alt2. U1 unmoved.

**Next hint:** J13 north band y=74.5–75 hits P0.01 highway/via; J10/J11 −1.0/−0.5 mm west still collide with P0.04 east trunk and VDD_GPIO column stubs — need PM-approved Alt2 or copper move of P0.01/P0.04/VDD_GPIO first.

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
  "U1": [
    36.0,
    32.0
  ],
  "ok": true,
  "reasons": []
}
```

**Stop reason:** preferred dirty/reject (dirty_drc); Alt1 also dirty/reject (dirty_drc) — full revert to pass30z keep; STOP (no Alt2)
**Backup:** `/workspace/kicad-projects/nRF9161-DEV-BOARD/.mcp-backups/pass30ab-package-b/pre-edit.kicad_pcb`
**Script:** `scripts/final_pass30ab.py`
**DRC:** `reports/DRC_PASS30AB_BEFORE.json`, `MID_PREF`/`MID_ALT` as needed, `DRC_PASS30AB_AFTER.json`
