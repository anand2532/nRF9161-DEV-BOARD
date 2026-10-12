# pass30cg — In2 routing for the remaining opens (branch `finish`, on pass30cf 61f49a5)

## Set-up (Freerouting 1.9.0, scripts/pass30cg/export3.py)
- **Layers:** signals on F.Cu, In2 and B.Cu. In1 is a power layer (no-route). All existing copper fixed.
- **Keepouts:**
  - RF x0–24.2/y20–64, all layers;
  - x0–29/y26–40 on F.Cu and In1;
  - **x0–29/y20–64 on In2**;
  - **U1 area on In2**, plus a via keepout over U1;
  - VDD_nRF neck x53–60/y12–22: In2 tracks, vias on all layers;
  - sealed B.Cu pocket;
  - a new 0.6 mm strip along every board edge on all layers.
- **Classes:** default 0.18/0.15, via 0.50/0.30. POWER 0.20. SIM (SIM_CLK, SIM_RST, SIM_IO) 0.50. RF feeds + GNSS_VBIAS 1.0 (via ≥1 mm).
- **Nets offered:** the 14 opens, excluding pads 49/54/59 (SIM_1V8, MAGPIO1, MIPI_SDATA). One run with -mp 30, about 8 min.

## Result: per-net new copper
| net | target | mm | F | In2 | B | vias | status |
|---|---|---|---|---|---|---|---|
| COEX1 | ≤80 | 78.9 | 24.7 | 41.8 | 12.4 | 4 | **closed, within target** |
| P0.24 | none | 96.3 | 1.5 | 94.8 | 0 | 1 | closed |
| P0.27 | none | 85.7 | 1.4 | 71.2 | 13.1 | 3 | closed |
| P0.31 | none | 1.3 | 1.3 | – | – | 0 | partial stub only → removed, open |

- **Totals:** vias 303 → 311 (+8). Track 6280.3 → 6541.2 mm (+260.9).
- **Checks on new copper:**
  - 0 on In1;
  - 0 In2 items in the RF/U1/neck keepouts;
  - 0 vias in the U1 area, in pads, or within 1 mm of the RF feeds/GNSS_VBIAS;
  - 0 new copper within 0.5 mm of SIM_CLK/SIM_RST/SIM_IO, so any parallel run at <0.5 mm is 0 mm.

## Gate (zones refilled)
| | before (pass30cf) | after |
|---|---|---|
| non-GND opens | 17 | **14** |
| unconnected / GND islands | 29 / 12 | 26 / 12 |
| short/clr/cross/hole | 0/0/0/0 | 0/0/0/0 |
| hole_to_hole / copper_edge | 0 / 0 | 0 / 0 |
| power nets open | 0 | **0** |
| dangling via / track | 1 / 4 | 1 / 4 |
No closed net reopened.

## Planes
| plane | pieces before | after | area before mm² | after |
|---|---|---|---|---|
| **In2 VDD_nRF** | 1 | **1** | 7431.2 | **6810.5** (−620.7, −8.4 %) |
| In1 GND | 2 | 2 | 8156.8 | 8150.4 |
| F.Cu GND | 23 | 23 | 6910.6 | 6887.3 |
| B.Cu GND | 18 | 20 | 6759.6 | 6731.2 |
VDD_nRF stays one piece and no power net is split. The In2 area loss is the new P0.24/P0.27/COEX1 In2 runs plus clearance (≈208 mm of 0.18 mm track with 0.15–0.20 mm voids). RF/Power should review it.

## Still open (14)
- **Excluded (pads 49/54/59, VIPPO or dog-bone):** SIM_1V8, MAGPIO1, MIPI_SDATA.
- **Not routed by Freerouting under these constraints** (In2 keepouts, SIM 0.5 mm, RF 1.0 mm, In1 closed, U1 via keepout): MIPI_SCLK (≤50), MIPI_VIO (≤60), MAGPIO0, MAGPIO2 (≤80), P0.10, P0.12, P0.14, P0.18, P0.25, SIM_IO. Most of these escape U1 on the west/north side, where the RF and U1 keepouts block In2 and no via fits.
- **P0.31:** Freerouting left only a 1.3 mm partial stub, which was removed.

PNGs: reports/PASS30CG_BEFORE.png / PASS30CG_AFTER.png (F+In2+B), PASS30CG_BEFORE_IN2.png / PASS30CG_AFTER_IN2.png (In2 only).
