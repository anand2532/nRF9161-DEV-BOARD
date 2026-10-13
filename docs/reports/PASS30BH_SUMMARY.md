# PASS30BH_SUMMARY — P0.07 leftover

**Timestamp:** 2026-09-30 17:47 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** P0.07
**Git HEAD:** `bed9dc7e7d4542c71796af436ae8c8e2b224188d`
**PCB blob at start:** `953e98bc52f2b39ffec50928389f4492eff69ce7`
**PCB blob at end:** `953e98bc52f2b39ffec50928389f4492eff69ce7`
**sha1sum at start:** `828df5c6726a56fb12bc18312f258fc973d582d6`
**sha1sum at end:** `828df5c6726a56fb12bc18312f258fc973d582d6`
**Routed:** no
**Copper changed:** no
**New via:** no
**New segments:** 0
**Stopping rule:** length (pad-edge 58.616524 mm > 36 mm).

## Preconditions

Live `kicad-cli` DRC (`run_drc`, same gate as pass30bg): unconnected **52** (required 52), P0.07 opens **1** (required 1). short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12. Counts matched, so the gap was measured. No copper was added. No backup (no edit).

## Leftover pad

**J9.2** center (116.000, 10.540), circular PTH 1.700 mm, drill 1.000 mm. Copper on F.Cu, In1.Cu, In2.Cu, B.Cu. This pad is its own island. U1.4 and J12.8 are already one island and were not ripped.

## Pad-edge

Pad-edge to the nearest copper on the closed U1.4/J12.8 island: **58.616524 mm** on In2.Cu. `GetClearance` from J9.2 to the locked In2 run. The minimum is shared by In2.Cu (48.050,37.900)-(63.100,37.900), In2.Cu (63.100,37.900)-(63.100,70.000) because both end on the round cap at (63.10, 37.90). Track-edge point (63.179941, 37.858654), pad-edge point (115.245003, 10.930486). Center distance to that corner 59.556524 mm. **Over the 36 mm cap.** Same length rule as the P0.17 leftover. No route attempted.

## Why no route

Rule that stopped the pass: **length**. Pad-edge 58.616524 mm is over 36 mm. No segments were laid, so there is no foreign clearance, no POWER clearance, and no new via. Whole-segment crossing count: 0 (no segments). The locked P0.07 In2 run was not ripped and nothing was stacked on its centerline. P0.00, SIM_RST, SIM_CLK, and the four skirts were not ripped or stacked. P0.05 via at (47.40, 36.50) is still net P0.05 and was not routed. Skirt slot, sealed pocket, and RF keepout were not entered. No second path. No other net. No Gerbers. No git commit.

## Locked copper check (read only)

```
{
  "p016": true,
  "p017": true,
  "p019": true,
  "p020": true,
  "sim_clk": true,
  "sim_rst_in1": true,
  "sim_rst_neck": true,
  "sim_rst_via": true,
  "p000": true
}
```

All locked checks true: **True**.

## DRC (unchanged board)

| | unconnected | P0.07 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 52 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 52 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No mid DRC: copper was not edited. AFTER is a copy of BEFORE. End blob matches start blob: **True**.

