# pass30cf — clean-up (branch `finish` from main 726831b, blob c404cef)

## (a) Silk
- **J12 / J13 / J18 pin labels:** all old labels deleted. 50 new ones, one per pin, centred on the pin x, in a single row above each header. 0° text does not fit the 2.54 mm pitch, so they are rotated 90°, 0.7 mm high, 0.12 mm stroke. Text comes from the pin net (VDD_GPIO shows as "3V3"). Note: J13.18 now reads 3V3 where the old label said VDD_nRF, because the pin's net is VDD_GPIO.
- **Pin 1:** stray '1' at (4.5, 73.8) removed. A filled silk dot (Ø0.6) sits beside pin 1 of J12, J13 and J18, next to the footprint's own pin-1 bracket.
- **Titles:** kept "nRF9161-DEV-BOARD" (60, 2.3) and the subtitle "LTE-M / NB-IoT / DECT NR+ / GNSS". Removed the duplicate title at (36, 3.0), "nRF9161 DEVELOPMENT BOARD", and the 0.8 mm duplicate 'LTE/NR+' and 'GNSS' near J2 and J5 (the 1.1 mm versions stay). 'ADC' moved to (38, 56.0) to clear the J18 labels.
- **J16:** new 'DNF' text (1.0 mm, 90°) beside the header.
- **U1/U4 silk (approved):**
  - U1's outline ran along its pad rows, so trimming left nothing. I replaced it with a rectangle 0.35 mm outside the pad field (27.25, 26.0 – 44.75, 38.0). The pin-1 dot was kept.
  - The U4 rectangle was cut to 2 segments clear of its pads.
  - This adds 1 `lib_footprint_mismatch` (U1 now differs from the library); that is expected.
- **Gate:** silk_overlap 0 (was 0), silk_over_copper 6 → **0**, silk_edge_clearance **0**.

## (b) Dangling copper
Each item was removed one at a time and kept out only if no net's open count changed (scripts/pass30cf/dangle_cf.py).
- **Removed: 66 items (34 vias, 32 tracks).** These are the approved power/SWD items (ENABLE, VDD1, VDD2, VDD_GPIO, VIN_IN, VIN_FILT, VIN_F, SIM_VCC, DEC0, SWDIO, SWDCLK, nRESET, nRESET_SW). They include:
  - DEC0 via (45.4, 30.55), unused, plus its 0.45 mm stub;
  - both SIM_RST B.Cu 6.57 mm stubs (two overlapping copies), the SIM_RST via (79.3, 36.0) and the 1.3 mm F.Cu stub it left behind;
  - the GNSS_VBIAS orphan tracks F.Cu 4.79 mm and B.Cu 13.05 mm;
  - the F.Cu stubs left dangling once their vias were gone.
- **Duplicates removed: 154 segments** (101 exact copies, 53 fully inside a same-net, same-layer, same-or-wider segment). RF nets (ANT, GPS, GNSS_ANT, GNSS_VBIAS) were held, with 13 duplicate groups left untouched.
- **Kept:**
  - P0.11 B.Cu 4.62 mm stub: removing it reopens P0.11.
  - VDD_GPIO B.Cu 9.3, 3.05 and 6.8 mm tracks: removing any of them opens VDD_GPIO. They are tapped mid-segment, so DRC flags them dangling even though they carry the connection.
  - SIM_CLK_C via (76.62, 56.05): not on the approved list; held for RF/Power.
  - C22/23/24 stubs untouched.
- **Dangling:** vias 35 → **1**, tracks 10 → **4** (all explained above).

## (c) Edge and hole
- 5 × copper_edge_clearance: all were the pass30cd P0.23 run hugging the top edge at y = 0.43. Rerouted locally with the same topology: F.Cu at y = 0.60 (0.51 mm to the edge, 0.157 mm to the P0.21 run below), via moved to (112.30, 0.76), then the B.Cu diagonal to the original end point (117.55, 6.34). → **0**.
- hole_to_hole: P0.02 had two vias 0.5 mm apart at (27.5, 43.5/44.0) joined by a 0.5 mm B.Cu hop. The F.Cu path is clear, so both vias and the hop were replaced by a 0.5 mm F.Cu segment. → **0**.
- No footprint moved.

## Gate (zones refilled)
| | before | after |
|---|---|---|
| non-GND opens | 17 | **17** (same nets) |
| unconnected / GND | 29 / 12 | 29 / 12 |
| short/clr/cross/hole | 0/0/0/0 | 0/0/0/0 |
| hole_to_hole | 1 | **0** |
| copper_edge_clearance | 5 | **0** |
| silk overlap / over copper / edge | 0 / 6 / 0 | **0 / 0 / 0** |
| dangling via / track | 35 / 10 | **1 / 4** |

PNGs: reports/PASS30CF_BEFORE_FSILK.png, PASS30CF_AFTER_FSILK.png, PASS30CF_BEFORE_CU.png, PASS30CF_AFTER_CU.png.
