# v2 fab pass: 9c48462 (branch v2-u4, v2k–v2m). **RED (1 item), plus WARNs**

Worked in a /tmp worktree on local branch v2-fab-pass-9c48462, with v2-fab-pass-bcd1c34 merged in. The PCB was read-only, and the other agent's worktree nRF9161-v2-u4wt was not touched. Evidence is in reports/v2fab-9c48462/.

## RED
| # | Item | Evidence |
|---|---|---|
| R1 | **U4 silkscreen lines are 0.10 mm wide**: 3 F.SilkS segments in the library footprint `Board:TI_TPD3F303_USON-8_DPV_2.1x1.6mm_P0.5mm`, at x=±1.06. JLC's minimum line width is ≥0.15 mm (https://jlcpcb.com/capabilities/pcb-capabilities, Legend). DRC does not flag this because the project has no silk-width rule. Fix: set the 3 lines to 0.15 mm, keeping ≥0.15 mm to the pads. | silk_checks.txt, U4 .kicad_mod |

## WARN (fix proposed, not blocking on its own)
- **W1, U4 land vs TI DPV drawing.** Source: TI TPD3F303 datasheet SLVSAM5A (Rev. A, April 2016), https://www.ti.com/lit/ds/symlink/tpd3f303.pdf.
  - p.17 is the DPV (R-PUSON-N8) mechanical drawing 4211111-2/A: body 2.00–2.20 × 1.50–1.70 mm, pitch 0.50, terminal length 0.28–0.38, terminal width 0.20–0.30.
  - p.18 gives the DPV exposed pad, drawing 4211680/A: 1.70±0.10 × 0.40±0.10.
  - **TI publishes no DPV land pattern.** p.16 is the land/stencil pattern for the *DQD* package only (4211174-2/B: 0.05 mm mask all round, EP paste split in 2, 62% coverage). Any DPV land is therefore derived and **unverified against TI**.
  - The footprint's descr cites "SLVSDF8 pp.17-18". The PDF TI currently serves is SLVSAM5A; the drawing numbers 4211111/4211680 match.

  Footprint compared with the drawing:

  | Feature | Footprint | TI DPV drawing | Verdict |
  |---|---|---|---|
  | Pitch | 0.50 | 0.50 | OK |
  | Pin order (top view) | 1–4 bottom row L→R, 5–8 top row R→L | Same as TI's top view on p.3 | OK |
  | Pad width | 0.25 | Terminal 0.20–0.30 | Narrower than the maximum terminal. WARN, minor |
  | Pad length / position | 0.50, spanning y 0.50–1.00 from centre | Terminal ends at the body edge 0.75–0.85 and is 0.28–0.38 long, so its inner end sits at y 0.37–0.57 | Toe +0.15–0.25 OK. The heel is short: at nominal the pad stops 0.03 mm short of the terminal inner end, and in the worst case 0.13 mm short. **WARN** |
  | Exposed pad | 1.70 × 0.40 copper, 1:1 mask | 1.70±0.10 × 0.40±0.10 | Equal to nominal. OK |
  | EP paste | 2 × 0.75 × 0.30 (0.45 mm² of 0.68 mm², about 66%) | DPV: none published. DQD pattern: 62%, 2 openings | OK, consistent with TI's DQD practice |
  | Pad-to-EP copper gap | 0.30 | n/a | OK |
  | Solder mask | Pad mask margin 0 (board pad_to_mask 0, 1:1) | DQD pattern: 0.05 all round | JLC allows 1:1 (pcb-capabilities, Soldermask). OK |
  | Pin paste | 1:1 on each pin | n/a | OK |

  **Proposed fix for W1 (derived, unverified):** lengthen the 8 pins inward to 0.60 mm, spanning y 0.40–1.00 (centre ±0.70). That leaves a 0.20 mm gap to the EP and covers the worst-case terminal inner end of 0.37 to within 0.03 mm. Optionally widen the pins to 0.28 mm, which leaves a 0.22 mm gap. Do not shrink the EP.
- **W2, jlc/CPL_JLC_v2.csv is stale and uses KiCad headers.**
  - The Val column is from before v2m-5: D1 reads PMEG4030ER (board SS34), FB4 BLM18PG221SN1 (board BLM21PG221SN1), and L1/L2 "0R / DNP match".
  - Its headers Ref/PosX/PosY/Rot/Side are not JLC's required Designator / Mid X / Mid Y / Layer / Rotation (https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly).
  - Positions, rotations and sides match the board for all 67 parts.
  - **Fixed in the package:** `*-cpl-JLC.csv` is regenerated from the board, with JLC headers and current values; the positions were asserted equal to jlc/CPL. The source jlc/ file should get the same fix.
- **W3, rotations for the JLC DFM preview** (no offsets invented): U1 180, U4 180, U2/U5–U8 0 (bottom), U3 0, Q1 0 (bottom), D1 180, D2 0, D3 0, D4 180, F1 90, J2/J5 180 (U.FL), J7 −90, J8 0, J20 0, SW2 0. These are KiCad-convention values; check each against the JLC preview.

## BOM / CPL readiness
- BOM headers are Comment, Designator, Footprint, LCSC. That covers JLC's required Comment, Designator and Footprint (https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly). The column name JLC auto-detects for LCSC part numbers is unverified; map it manually if the uploader asks.
- 67 fitted parts on the board = 67 in the BOM = 67 in the CPL (51 top, 16 bottom). No duplicates, no DNP part placed (DNP: C21–C24, C31, C32, C39, JP2, TP*), and every BOM line has an LCSC number.
- Side, position and footprint agree for all parts.
- Comment vs value: J2/J5 use the MPN U.FL-R-SMT-1(10) against board values U.FL_LTE_NR+ / U.FL_GNSS. That is intentional and fine.
- LCSC spot-check:
  - C2865991 = TI TPD3F303DPVR, USON-8-EP (1.6×2.1). Matches.
  - C8678 = SS34, SMA (DO-214AC). Matches D_SMA.
  - C85840 = Murata BLM21PG221SN1D, 0805. Matches FB4 L_0805.
- The panel CPL has 4 placements per designator (Q12, open).

## GREEN checks
- **Diff vs bcd1c34:**
  - U4: new footprint, rotated 180, same position.
  - Value-only changes on D1, FB4, L1, L2.
  - J7: pad net renamed only.
  - Vias: 5 removed, all 0.30 (3 GND, SIM_IO, SIM_CLK). 8 added, all 0.20/0.30.
  - Tracks: 28 removed / 50 added, on GND and the SIM nets.
  - U1 is unchanged (DK-verified chain back to b9d4e62). Stackup unchanged.
- **Filled vias: 30 per board** (21 × 0.20 + 9 × 0.25), **120 per panel**. The board, the drill files (single 21/9; panel 84/36) and the VIPPO Gerber agree.
  - Every 0.20/0.25 drill is in the fill set.
  - In-pad ones are centred: U1 pads 21/27/36/52/56/60/98 and C38.2 at offset 0.000, and 9 in U1.103 on the pad grid.
  - None of the 8 new vias is in a pad.
  - Bottom caps: the closest to a bottom pad is C38.2's cap, 0.25–0.285 mm from JP2.2 (unassembled, hand-bridged; same as before). All 8 new caps are ≥2.3 mm from any bottom pad.
- **Unfilled-hole edge overlap:** ring-only at C14.2, FB1.1, FB2.1 (WAIVED). Hole overlaps only with unassembled TP13/TP14. Unchanged.
- **Silk:** text all ≥1.0 mm with ≥0.15 mm stroke, including the 13 restored references (1.0 × 0.7 × 0.15). No silk-to-silk gap under 0.15 mm. DRC silk rules: 0 violations. Other than R1, the only sub-0.15 items are those same U4 lines and U1's own pin-1 circle (unchanged). The logo is removed.
- **DRC:** 0 errors / 0 unconnected as-is, the same after refilling, and schematic parity 0. Only environment library warnings remain.
- **Outline:** closed R2.0 shape. Copper ≥0.498 mm from the edge, with nothing outside. J7 body is 0.106 mm and courtyard 0.049–0.052 mm inside the arc.
- **Stackup:** 4 layers, 1.6 mm, ENIG, 0.12 / 1.2 / 0.12 (board = .gbrjob).
- **Parts / reflow:** 51 top (171.1 mm² of pads) / 16 bottom (30.1 mm²). The bottom is reflowed first.
- **Bottom pad-to-via <0.3:** 26 pairs, WAIVED.
- **Panel:** rebuilt from v2_panel.json. 118.10 × 93.10 mm, 128 mouse-bites on the straight N/S edges only (board-local x 6–43, straight span 2.0–48.05). 3 fiducials per side (1 mm, 2 mm opening), 4 × 2 mm tooling holes. Panel DRC 0/0. Content = 4 × the board (vias 872/84/36, 3300 tracks, all silk texts and footprints).

## Package: fab/staging-v2-9c48462/ (DO NOT ORDER while R1 is open)
- `nRF9161-v2-single-9c48462.zip` and `nRF9161-v2-panel-9c48462.zip` contain gerbers, the VIPPO Gerber (30 / 120 flashes), .gbrjob, PTH/NPTH drill files and maps, IPC-D-356, the JLC BOM (copied from jlc/BOM_JLC_v2.csv) and the JLC-header CPL (single: 67; panel: 268, i.e. 4 × 67).
- ORDER_NOTES updated to 30 per board / 120 per panel.

**Waivers kept:** C14, FB1.1, FB2.1, and the bottom pairs under 0.3 mm.
