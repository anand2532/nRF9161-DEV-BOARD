# PASS30Y_SUMMARY — Package B only

**Timestamp:** 2026-09-23 13:17 IST
**Phase:** COMPLETE_REVERTED
**J13 landing kept:** None
**Final XY:** J13=[64.0, 76.0] J10=[116.0, 28.0] J11=[116.0, 46.0] U1=[36.0, 32.0]

## DRC

| | unconnected | shorting | clearance | crossing |
| --- | ---: | ---: | ---: | ---: |
| Before | 67 | 0 | 0 | 0 |
| After | 67 | 0 | 0 | 0 |

**Gate:** BLOCKED — reverted to pass30u keep; unconnected 67→67; shorting/clearance/crossing=0/0/0

## Attempts

### preferred_J13_64_78.5
- targets: {'J13': [64.0, 78.5], 'J10': [113.46, 28.0], 'J11': [113.46, 46.0]}
- mid: {'unconnected_items': 67, 'shorting_items': 11, 'clearance': 3, 'tracks_crossing': 7, 'copper_edge_clearance': 0, 'silk_over_copper': 45, 'silk_overlap': 148, 'hole_clearance': 4, 'via_dangling': 72}
- clean: False edge_class: True
- ripped=18 reattached=21 bus=6
- collide head: [{"type": "tracks_crossing", "description": "Tracks crossing", "items": [{"description": "Track [P0.01] on B.Cu, length 12.5100 mm", "pos": {"x": 68.0, "y": 78.5}}, {"description": "Track [P0.19] on B.Cu, length 14.5000 mm", "pos": {"x": 71.62, "y": 78.5}}]}, {"type": "tracks_crossing", "description": "Tracks crossing", "items": [{"description": "Track [P0.01] on B.Cu, length 12.5100 mm", "pos": {"x": 68.0, "y": 78.5}}, {"description": "Track [P0.18] on B.Cu, length 5.7000 mm", "pos": {"x": 69.0

### alt_J13_67_76
- targets: {'J13': [67.0, 76.0], 'J10': [113.46, 28.0], 'J11': [113.46, 46.0]}
- mid: {'unconnected_items': 67, 'shorting_items': 16, 'clearance': 3, 'tracks_crossing': 4, 'copper_edge_clearance': 0, 'silk_over_copper': 44, 'silk_overlap': 150, 'hole_clearance': 4, 'via_dangling': 72}
- clean: False edge_class: None
- ripped=18 reattached=31 bus=6
- collide head: [{"type": "shorting_items", "description": "Items shorting two nets (nets P0.22 and P0.23)", "items": [{"description": "Via [P0.22] on F.Cu - B.Cu", "pos": {"x": 112.5, "y": 32.5}}, {"description": "PTH pad 3 [P0.23] of J10", "pos": {"x": 113.46, "y": 33.08}}]}, {"type": "shorting_items", "description": "Items shorting two nets (nets P0.01 and P0.21)", "items": [{"description": "Via [P0.01] on F.Cu - B.Cu", "pos": {"x": 80.51, "y": 76.7}}, {"description": "PTH pad 6 [P0.21] of J13", "pos": {"x":

**Stop reason:** alt also dirty or protect/unconnected fail — full revert to pass30u keep
**Backup:** `/workspace/kicad-projects/nRF9161-DEV-BOARD/.mcp-backups/pass30y-connect/pre-edit.kicad_pcb`

## Blockers (why both landings failed)

### Preferred J13 (64, 78.5)
- South pad row lands on existing bottom highways: P0.01 B@y78.5, P0.04 F@y78.8, P0.06 F@y79.2, P0.08 B@y79.0
- hole_clearance=4 (pads vs edge/holes band toward y=80)
- J10 west (113.46): P0.22 via@(112.5,32.5) shorts J10.3 (P0.23)

### Alt J13 (67, 76)
- Same J10 west short vs P0.22 via@(112.5,32.5) — independent of J13
- J13 east: pad6 P0.21 @ (79.7,76) shorts P0.01 via@(80.51,76.7)
- VDD_GPIO reattach L-jogs hit GND via / P0.22 / P0.04

## Outcome
Full atomic package revert to pass30u keep. No footprint moves retained. No Gerbers. Packages A/C/D not touched. U1 unmoved.

**Next hint:** Package B needs either (a) J10 west delta that clears P0.22 via@x112.5, and/or (b) a J13 landing that avoids y≈78.5–79.2 highways and x≈80.5 P0.01 via — not (64,73) again.
