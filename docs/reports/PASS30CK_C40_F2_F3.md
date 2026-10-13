# PASS30CK: C40, LED fields, F2, F3 (branch `vippo` from 55f07b7)

## Update PCB from Schematic (pcbnew Python; netlist taken from `kicad-cli sch export netlist`)
- **C40 added** (100nF 0402, Murata GRM155R71A104KA01D). Pad 1 is on SIM_1V8 and pad 2 on GND. It uses the board's own 0402 footprint (cloned from C33; the KiCad libraries are not installed on the box), with fresh UUIDs (0 duplicate UUIDs).
- **D3–D7:** Value changed to "Green LED". Hidden fields added: Function (POWER/STATUS/LTE/GNSS/SPARE_DNP), Manufacturer Kingbright, MPN KP-2012SGC. **D7 has the DNP attribute set**, plus DNP=yes and a Note field. No footprints were moved.

## C40 placement
- Placed at (30.00, 25.55), rot 0, on the SIM_1V8 F.Cu escape directly north of U1. Pad 1 is at (29.52, 25.55), **1.22 mm centre-to-centre from U1 pad 49**, tied to the 0.25 mm escape by a 0.23 mm stub.
- The GND pad (30.48, 25.55) runs a 0.9 mm, 0.25 mm-wide track to a GND via (0.5/0.3) at **(30.48, 24.65)**. That via is outside the U1 pads and the U1 area, and outside the RF keepout (x ≥ 29).
- Clearances (all inside the y ≥ 24 fan-out zone): via to SIM_CLK F.Cu 0.43 mm, via to SIM_RST In1 0.51 mm, pad 2 to SIM_IO pad 48 0.48 mm.
- C40's two silk body lines overlapped the U1 outline, so they and its reference text were moved to F.Fab. Silk stays 0.

## F2: SIM_1V8
- `SIM_1V8` was added to the POWER netclass pattern in the .kicad_pro (clearance 0.15).
- **97.2 of 114.7 mm is now ≥0.25 mm.** Width was raised to 0.25 wherever 0.15 general / 0.5 SIM / 0.25 hole clearance allowed (0.15 SIM only inside the y ≥ 24 fan-out zone).
- Three legacy segments are still 0.18–0.20 mm because widening would break clearance:
  - F.Cu (80.85, 48.6)–(71.7, 48.6), 9.15 mm;
  - F.Cu (78.65, 56.6)–(80.85, 56.6), 2.2 mm;
  - B.Cu (30.57, 48.24)–(30.57, 54.34), 6.1 mm.
  Waiver per the RF review: IR ≤16 mV at 50 mA.

## F3: 88.1 mm² B.Cu GND sliver
- South of y 19 the sliver is a **0.23 mm-wide strip** at x 27.84–28.07, between P0.02 B.Cu (x 27.5) and VDD_GPIO B.Cu (x 28.5), and it lies inside the RF keepout. A via cannot fit there, so the y 25/32/38 stitches are impossible.
- I used the reviewer's alternative instead: a B.Cu no-pour rule area `pass30ck_sliver_noFill` (x 27.7–28.25, y 19.0–39.75) removes the strip.
- The remaining block (x 27.84–33.86, y 4.84–19.0, 83.3 mm²) is stitched at ≤5 mm spacing. New GND vias (0.5/0.3) at (30.5, 5.6), (33.5, 10.0), (28.5, 10.0), (30.5, 14.3) and (30.5, 16.7), plus the existing (30, 10).

## Gate (zones refilled, kicad-cli DRC with project rules) — PASS
- short 0, clearance 0, crossing 0, hole 0, hole_to_hole 0, copper_edge 0, silk 0, courtyard 0. via_dangling 0.
- track_dangling 4: pre-existing.
- unconnected 23 = 12 signal + 11 GND islands (unchanged). **SIM_1V8 still closed.** No power net opened.
- VDD_nRF on In2 is one piece, 6791.5 mm² (was 6801.7; the −10.2 mm² is the anti-pads of the 6 new GND vias).
- In1 GND: 2 pieces, 8142.6 mm² (unchanged).
- RF protected copper untouched.

Open (12): MAGPIO0/1/2, MIPI_SCLK/VIO/SDATA, SIM_IO, P0.12/14/18/25/31, all for PASS30CL.

Images: PASS30CK_BEFORE.png, PASS30CK_AFTER.png. DRC: DRC_PASS30CK_AFTER.json.
