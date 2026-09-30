# PASS30BJ_SUMMARY — P0.05 leftover

**Timestamp:** 2026-09-30 18:05 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** P0.05
**Git HEAD:** `d9a24687f90a94df2bd3796832823588efd1e078`
**PCB blob at start:** `7bcfe5791b156e426a2a0affefe938be4d39f8e6`
**PCB blob at end:** `7bcfe5791b156e426a2a0affefe938be4d39f8e6`
**sha1sum at start:** `c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40`
**sha1sum at end:** `c6dc3ba60aa52dbe533823c2a6a2af7aa5fb0e40`
**Routed:** no
**Copper changed:** no
**New via:** no
**New segments:** 0
**Stopping rule:** length (pad-edge 63.217656 mm > 36 mm).

## Preconditions

Live `kicad-cli` DRC (`run_drc`, same gate as pass30bh / pass30bi): unconnected **51** (required 51), P0.05 opens **1** (required 1). short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12. Counts matched, so the gap was measured. No copper was added. No backup (no edit).

## Leftover pad

**J9.3** center (116.000, 13.080), circle PTH 1.700 x 1.700 mm, drill 1.000 mm. Copper on F.Cu, In1.Cu, In2.Cu, B.Cu. This pad is its own island. U1.2 and J12.6 are already one island and were not ripped. Prior report named J9.3 at (116.00, 13.08): **True**.

## Pad-edge

Pad-edge to the nearest copper on the closed U1.2/J12.6 island: **63.217656 mm** on In1.Cu. `GetClearance` from J9.3 to the locked In1 run. The minimum is shared by In1.Cu (47.400,38.400)-(57.050,38.400), In1.Cu (57.050,38.400)-(57.050,74.700) because both end on the round cap at (57.05, 38.40). Track-edge point (57.132695, 38.364481), pad-edge point (115.218994, 13.415455). Center distance to that corner 64.157657 mm. **Over the 36 mm cap.** Same length rule as pass30bh (J9.2 was 58.617 mm and was not routed). No route attempted.

## Why no route

Rule that stopped the pass: **length**. Pad-edge 63.217656 mm is over 36 mm. No segments were laid, so there is no foreign clearance, no POWER clearance, and no new via. Whole-segment crossing count: 0 (no segments). The locked P0.05 In1 run was not ripped and nothing was stacked on its centerline. P0.07, P0.00, SIM_RST, SIM_CLK, and the four skirts were not ripped or stacked. J9.2 (P0.07) was not touched and stays open. Skirt slot, sealed pocket, and RF keepout were not entered. No second path. No other net. No Gerbers. No git commit.

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
  "p000": true,
  "p007": true,
  "p007_via": true,
  "p005": true,
  "p005_via": true,
  "j9_2": true
}
```

J9.2: `{"xy": [116.0, 10.54], "net": "P0.07", "fp_xy": [116.0, 8.0]}`.

All locked checks true: **True**.

## DRC (unchanged board)

| | unconnected | P0.05 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 51 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No mid DRC: copper was not edited. AFTER is a copy of BEFORE. End blob matches start blob: **True**.

