# PASS30CP: final (branch vippo, local, not pushed)

## Commits

| SHA | Content | Unconnected |
|---|---|---|
| 077a757 | Step 1: 5 GND stitch vias; islands 10 → 5 | 5 |
| 6bedbfe | B: 4 dangling B.Cu stubs trimmed; SIM_RST via nudged 0.2 mm | 5 |
| 0f13a32 | Step 2: locked stackup | 5 |
| 2673f8b | A: schematic parity (DNP/BOM sync; FB5/U3 lib names); U4/U1 checked | 5 |
| 7140289 | Step 4: 6 group B vias centred on U1.103 (y 28.8 / 35.2); P0.12 local reroute | 5 |
| 0cf1cb9 | Step 5: silk to JLC limits (0.15 stroke / 1.0 text); U1 ref overlap fixed | 5 |
| 8ed6fdf | C: GND VIPPO in U1 pads 36/27/21/98 (PM); VIPPO total 29 | 1 |
| ce31859 | J5: RF-approved GND via (5.90, 50.75) for the J5.2 island | **0** |

## Final gate (ce31859)
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk (overlap/over-copper/edge), courtyard, mask_bridge, via_dangling and track_dangling: **all 0**.
- **Unconnected: 0.**
- In1 GND: 2 pieces, 8179.5 mm² (main plane 8168.7 + the pre-existing 10.7 piece).
- VDD_nRF (In2): 1 piece, 6712.2 mm².
- Non-gated: lib_footprint_issues 100 (98 before; +2 because the stock KiCad libs are not installed on the build box) and lib_footprint_mismatch 1 (U4, silk only).
- Schematic parity: NC net_conflicts only.

## Step 5 silk
- Refs moved to F.Fab: **none**. All 103 refs fit at 1.0/0.15.
- PNGs:
  - reports/img/PASS30CP_S5_FSilk_before.png and reports/img/PASS30CP_S5_FSilk_after.png
  - reports/img/PASS30CP_S5_BSilk_before.png and reports/img/PASS30CP_S5_BSilk_after.png
- B.Silk is empty.

## U1 GND VIPPO (PM decision)
- Vias (0.20/0.30, tented, centred, ringed on User.1):

  | Pad | Via (mm) |
  |---|---|
  | U1.36 | (36.25, 27.0) |
  | U1.27 | (40.75, 27.0) |
  | U1.21 | (43.75, 27.0) |
  | U1.98 | (41.25, 37.0) |

- All are more than 9 mm from the RF feeds; none was skipped.
- Reroutes for clearance: VDD2 at (44.72, 25.9) and P0.01 at (40.25, 38.32), both on B.Cu.
- New VIPPO total: **29** (0.20/0.30 ×20, 0.25/0.40 ×9).
- The fab note and the board text are updated. The fab note had omitted the 7 signal VIPPO (now documented as group A2).

## J5.2 (RF-approved)
- One 0.30/0.60 tented GND via at (5.90, 50.75), tied to In1, no In1 slot, no F.Cu link.
- Clearances (edge to edge):

  | To | Clearance |
  |---|---|
  | J5.2 pad | 0.325 mm |
  | J5.1 signal pad | 1.30 mm |
  | GNSS_ANT trace | 1.70 mm (outside the ±0.5 band) |
  | GNSS_VBIAS y=50 track | 0.35 mm |
  | GNSS_VBIAS x=5.02 track | 0.48 mm |

- RF to confirm:
  - The via is at the outer-top corner, not the pure outer side.
  - Only one via fits.
  - It is less than 1 mm from GNSS_VBIAS.
- A duplicated, dead GNSS_VBIAS F.Cu loop around J5 (since the initial commit) blocks the outer side. It was left untouched.
- The exception is noted in the DRU and the fab note. Details: PASS30CP_J5_GND.md.

## Open items for PM/RF
1. J5 via position and VBIAS proximity (above).
2. The GNSS_VBIAS duplicate loop around J5.
3. TP1–TP20, JP1 and JP2 now appear in the BOM, per the schematic.
4. The silk was re-placed automatically; a manual cosmetic review of the dense label areas is recommended.
5. The VIPPO ring markers cover groups A and C only; groups A2 and B are identified by drill tool.
