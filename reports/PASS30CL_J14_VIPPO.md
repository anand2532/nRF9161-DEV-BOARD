# PASS30CL: J14 move + VIPPO (branch `vippo`, on top of PASS30CK)

## J14 move (approved)
- Moved from (104, 48), rot 0 to **(26.5, 14.35), rot 180**. Pin 1 (MAGPIO0) is at the bottom (y 14.35) and pin 6 (MIPI_SDATA) at the top (y 8.0); all pins are at x 26.5.
- It sits north-west of U1, about 12 mm north of the U1 NW corner. That is outside the RF keepout (no copper at x<29 in y 20–64; the lowest pad edge is y 14.85) and well away from the SIM area.
- Its THT pads clear the In1 P0.00 (x 25 / y 15.2) and SIM_RST (x 26.2 / y 17.6) tracks.
- Rot 180 was chosen so that all six column escapes reach J14 on B.Cu with zero crossings and no extra vias. VIO/SCLK/SDATA come in from the west side of the pins, MAGPIO0/1/2 from the east side.

## VIPPO
- **Size and marking:** 0.20 drill / 0.30 land, filled and capped (IPC-4761 VII). They are the only 0.20 mm drill tool on the board, so the fab can select them by tool.
- **Rules:** a new `nRF9161-DEV-BOARD.kicad_dru`, keyed on `A.Hole == 0.2mm`:
  - VIPPO_size: via_diameter ≥0.30, hole ≥0.20, annular ≥0.05.
  - VIPPO_In1_C1: In1 clearance and hole_clearance 0.10.
  - The board-level minimums are unchanged for every other via.
- User layer **User.1 renamed "VIPPO"**, with a marker ring on every VIPPO via and the fab-note text. The full fab note is in DFM_VIPPO_NOTE.md §1.4 (update the count to 9 places and pads 52–60).
- **Placed: 9 vias in U1 pads 52–60, all at x 27.95.** Six are signal (53 MAGPIO2, 54 MAGPIO1, 55 MAGPIO0, 57 MIPI_VIO, 58 MIPI_SCLK, 59 MIPI_SDATA); their inner annular rings are removed so In1 gets a 0.40 mm anti-pad. Three are GND (52, 56, 60), connected on all layers (**C3: pad 60 is the fence between pad 59 and ANT pad 61**).
- x 27.95 instead of 28.0 keeps the GND barrels ≥0.25 mm hole-to-copper from VDD_GPIO B.Cu (x 28.5).
- **Not placed:**
  - **P0.14 (pad 24) and P0.18 (pad 29): VIPPO is impossible.** At every in-pad position (±0.25 mm scanned with DRC), the barrel shorts or violates clearance to P0.19 on In1 (y 26.5), P0.20 on In2 (y 26.5) or P0.13 on B.Cu (y 27.0), all of which run under those pads.
  - **SIM_IO (48), P0.12 (20, at x 43.8), P0.25 (42) and P0.31 (89, at y 37.05):** a DRC-clean via position exists, but Freerouting (r12, 30 passes, 8 min) found no B.Cu escape. U1's underside on B.Cu is closed in by VDD_GPIO (x 28.5 / y 19.13), SIM_1V8 (x 31.05), COEX0 (x 32.25), SWDCLK/P0.22 and P0.13. SIM_IO also needs 0.5 mm SIM clearance. These vias were removed so nothing is left dangling.

## Routing
- **The six column nets are routed (hand-routed, all B.Cu, 0.18 mm).** Escape goes west from the in-pad via to a 0.33 mm-pitch channel at x 25.05–26.70, north to y ≈ 20, then into J14. Nothing is west of x 24.5, and there is no escape copper south of y 30.5.

| Net | Length (track) | Target | Met? |
|---|---|---|---|
| MIPI_SCLK | 24.4 mm | ≤50 | yes |
| MIPI_VIO | 22.0 mm | ≤60 | yes |
| MIPI_SDATA | 26.9 mm | (≤50) | yes |
| MAGPIO0 / 1 / 2 | 18.1 / 18.9 / 19.7 mm | ≤80 | yes |

- **P0.02 (closed net, rerouted to free the channel):** its north B.Cu branch moved from x 27.5 (y 4.5–40.5) to via (27.5, 40.5) → (27.5, 36.5) → (24.6, 36.5) → x 24.6 north → (25.5, 4.5) → (27.5, 4.5). It stays closed.
  - **RF to check:** it is new B.Cu at x 24.6 (inside x 23.5–29) and at y 36.5 in the west column. Like the old x 27.5 run, it crosses under the ANT/AUX/GPS F.Cu feeds, with In1 GND in between. GNSS_VBIAS is ≥1.3 mm away and the GND via at (25.98, 34) 1.0 mm away.

## RF C1–C7 status
- **C1: partly met.** The anti-pad is 0.40 mm, but the In1 webs **do not survive.**
  - The In1 GND zone min thickness is 0.20 mm, so 0.10 mm webs are dropped.
  - The stagger fallback (27.8 / 28.2) is impossible because VDD_GPIO B.Cu at x 28.5 shorts any land at x>28.03.
  - Result: two In1 slots about 0.4 × 1.4 mm (pads 53–55 and 57–59, narrowing to ~0.15 mm between barrels). They are separated and bounded by the connected GND barrels in 52/56/60. See PASS30CL_IN1.png. **RF must accept this or waive.**
- **C2:** met for the escapes (west to x ≥25, north, nothing west of 23.5, nothing south of 30.5). See the P0.02 note above.
- **C3:** GND VIPPO in 52, 56 and 60 (60 mandatory: done). No extra GND via was added near the bundle at y ≈ 26, because that area is inside the RF keepout. The GND barrels are within 0.5 mm of every signal barrel.
- **C4:** no new In1 copper. In1 is still 2 pieces: **8142.6 → 8142.1 mm²** (−0.5).
- **C5:** the only copper inside the x<29 keepout is the via barrels in pads 52–60 plus B.Cu escapes. There are no F.Cu or In1 tracks.
- **C6:** the 61 protected RF items and C22/23/24/L1/L2/TP1/U3/C27/L4/FB5 are identical. The In2 neck is untouched (no copper changed in x 53–60). No new copper near SIM.
- **C7:** DFM/JLC confirmation is still pending (4L POFV, 0.05 mm ring, 8:1 aspect).

## Gate (zones refilled, kicad-cli DRC with project rules + .kicad_dru) — PASS with listed opens
- short 0, clearance 0, crossing 0, hole 0, hole_to_hole 0, copper_edge 0, silk 0, courtyard 0. via_dangling 0.
- track_dangling 4: pre-existing.
- unconnected **23 → 17** = 6 signal + 11 GND islands. No power net opened.
- VDD_nRF on In2 is one piece, **6791.5 → 6780.3 mm²** (via and THT anti-pads).
- GND B.Cu 21 → 22 pieces; the new piece is in the freed channel, and the GND island count is unchanged at 11.
- Footprints: only J14 moved (approved); C40 was added in CK.

## Remaining opens (6)
- **P0.14, P0.18:** no legal in-pad via (In1/In2/B.Cu tracks of P0.19, P0.20 and P0.13 under the pads). These need a reroute of those closed nets or a pin remap.
- **SIM_IO:** in-pad via possible, but there is no B.Cu path at 0.5 mm SIM clearance (blocked by VDD_GPIO, SIM_1V8, C40's GND via and COEX0). A SIM_1V8 escape rework or a SIM clearance waiver is needed.
- **P0.12, P0.25, P0.31:** in-pad via possible, but the router found no B.Cu escape under U1. A rip-up of P0.13 / COEX0 / SWDCLK under U1 is needed.

Images: PASS30CL_BEFORE.png, PASS30CL_AFTER.png (F/B/VIPPO), PASS30CL_IN1.png. DRC: DRC_PASS30CL_AFTER.json.
