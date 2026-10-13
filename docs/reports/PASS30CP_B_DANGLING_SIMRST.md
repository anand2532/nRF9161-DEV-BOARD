# PASS30CP (RF review B): dangling stubs removed; SIM_RST via nudged
**Recheck result:** each "dangling" track was a bridge that overshot. Its far end ran on past the junction, so deleting it outright opened the net (tried: VDD_GPIO ×3 and P0.11 opened). Each one was trimmed to the bridging part only:

| Net | Before (B.Cu) | After |
|---|---|---|
| VDD_GPIO | (70.0, 8.0)–(70.0, 14.8) | (70.0, 8.0)–(70.0, 9.0): TP10/via to the y 9 run |
| VDD_GPIO | (48.05, 5.5)–(48.05, 14.8) | (48.05, 5.5)–(48.05, 9.0) |
| VDD_GPIO | (48.05, 3.46)–(45.0, 3.46) | (46.35, 3.46) via → (45.0, 3.46) |
| P0.11 | (44.0, 29.2)–(48.62, 29.2), the 4.62 mm stub under U1 | (46.5, 29.2)–(48.62, 29.2), now ends at the via (46.5, 28.0) leg; nothing left west of x 46.5 |

**SIM_RST via:** moved from (79.376, 58.05) to (79.376, 57.85), 0.2 mm away from the SIM_IO run at y 58.6. Copper gap is about 0.16 → 0.36 mm. The two SIM_RST tracks that end at it were re-anchored. Approved by RF.

**Gate (refilled):**
- short/clearance/crossing/hole/hole_to_hole/courtyard/edge/silk/mask_bridge are all 0. **via_dangling 0, track_dangling 0** (was 4).
- Unconnected 5 → 5 (the GND islands from step 1).
- In1 GND 2 pieces 8179.5 mm2; VDD_nRF 1 piece 6716.8 mm2
