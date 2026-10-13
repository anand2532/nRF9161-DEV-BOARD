# PASS30BL_SUMMARY - SIM_1V8 U1.49 via south corridor

**FINAL STATUS: REVERTED (NO-ROUTE)** - Hardware PM ruling, 2026-10-12.
**Reason:** the new via (29.75,26.05) 0.50/0.30 partly overlapped the F.Cu-only nRF9161 LGA pad U1.49 (via-in-pad). That risks solder wicking, and plugging will not be made a fab requirement.
**Other layers:** In1 is blocked by P0.19 at x=39.25. B.Cu is blocked by COEX0 at x=32.25. In2 was reachable only through that via.
**Restored blob:** 7bcfe5791b156e426a2a0affefe938be4d39f8e6 (sha1sum c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40). Tip be23037. Not committed.
**Revert DRC** (reports/DRC_PASS30BL_REVERT.json): unconnected 51, GND items 12, SIM_1V8 opens 1, short/clearance/crossing/hole 0, hole_to_hole 1. This matches pass30bk AFTER.
**Do-not-retry:** J9.2, J9.3, SIM_1V8.

---
## Original attempt record (superseded)

**Decision:** KEEP. **KiCad:** 9.0.2. **Git tip:** be23037 (not committed).
**Start blob:** 7bcfe5791b156e426a2a0affefe938be4d39f8e6 (sha1sum c6dc3ba6...). **End blob:** a273ae94425319d313eade673c7880426fc1682d.
Backup: .mcp-backups/pass30bl/pre-edit.kicad_pcb. Script: scripts/final_pass30bl.py. JSON: reports/PASS30BL_RESULT.json, DRC_PASS30BL_BEFORE/AFTER.json.

## Measurements
- SIM_RST In1 track edge y=25.59; U1.49 pad copper top y=26.35. Gap is 0.76 mm, so a 0.50 via cannot sit fully between them. The via overlaps its own U1.49 pad (same net), and that is legal.
- New via (29.75, 26.05), 0.50/0.30 through. Clearances: In1 SIM_RST track 0.21; F.Cu SIM_IO stub x=30.25 0.16; U1.48 SIM_IO pad corner 0.21; U1.50 GND pad corner 0.21; SIM_RST via (32.75,25.50) 1.75 ctr (≫); SIM_IO via (30.25,23.10) 2.44; COEX0 via (29.81,22.00) and COEX0 B.Cu x=32.25 ≥2.2; MAGPIO1 F.Cu y=28.0 ≥1.6; B.Cu VDD_GPIO x=28.5 0.83 (POWER). 0.60 via not used.
- Courtyard: the via spans y 25.80–26.30, north of the courtyard edge (26.50), so it sits outside the U1 body/courtyard. DRC courtyard 0/0.
- In1 eastbound fails: P0.19 In1 (39.25,23.1)-(39.25,26.5)-(44.25,26.5) walls y≈26; north gap SIM_CLK y=20.05 vs P0.16 via (40.7,20.8) is 0.36 mm, below the 0.48 mm needed. B.Cu fails: COEX0 x=32.25. In2 eastbound at y≈26 is walled by P0.20 x=36.45, so the In2 run turns north before it.

## Route (0.18 mm, 10 segments, 1 new via)
1. F.Cu (29.75,26.75)->(29.75,26.05)
2-10. In2: (29.75,26.05)->(34.00,26.05)->(34.00,21.00)->(35.25,20.95)->(35.75,20.20)->(55.50,20.20)->(55.50,34.00)->(75.00,34.00)->(75.00,44.00)->(76.17,45.126) (existing SIM_1V8 through-via, far island)

Min foreign In2: 0.192 P0.22 via (35.25,19.90); 0.21 P0.16 via (40.7,20.8) and P0.20 via (36.2,20.8); 0.21 SIM_RST via. Min POWER: 0.51 VDD2 via (54.5,21.2); VDD_GPIO via (76.44,39.05) 0.95. Same-layer crossings with locked runs: 0. No locked centerline stacked (closest: In2 y=20.20 sits 0.15 off SIM_CLK In1 y=20.05, on a different layer). The In2 segments cross locked In1/F.Cu runs in plan view only (SIM_RST neck, SIM_CLK x=57.2/y=36), on other layers. P0.07 In2 untouched (y=34 run ends north of 37.9). No skirt, sealed pocket, RF keepout, or J9 use.

## DRC
| | unconnected | SIM_1V8 | short | clearance | crossing | hole | hole_to_hole | GND unconnected items |
|---|---|---|---|---|---|---|---|---|
| before | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 51 | 0 | 0 | 0 | 0 | 0 | 1 | 13 |
No other non-GND net gained an open. The total stays at 51 because the via split one In1 GND fill island (+1 GND item, waived).
