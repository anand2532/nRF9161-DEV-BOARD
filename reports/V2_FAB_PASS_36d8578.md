# v2 fab pass: 36d8578 (v2-u4, v2n). **GREEN apart from the JLC quote**

Worked in a /tmp worktree on local branch v2-fab-pass-36d8578, with v2-fab-pass-9c48462 merged in. The PCB was read-only, and the u4wt worktree was not touched. Evidence is in reports/v2fab-36d8578/.

## Closed from 9c48462
- **R1 (U4 silk):** the 3 lines are now 0.15 mm. Silk sweep: 0 lines under 0.15 and 0 texts under 1.0 / 0.15 on either side. The .kicad_pro default silk_line_width is 0.15. Note: the default silk_text_thickness is still 0.1, which only affects new text; every existing text is ≥0.15.
- **W2 (CPL):** jlc/CPL_JLC_v2.csv now has the headers Designator, Comment, Footprint, Mid X, Mid Y, Layer, Rotation. That includes all of JLC's required Designator / Mid X / Mid Y / Layer / Rotation (https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly).
  - 67 rows = 67 BOM refs = 67 fitted on the board: 51 Top, 16 Bottom, no duplicates, no DNP placed.
  - Positions, rotations, layers and footprints match the board. Comments match the board values; D1 SS34, FB4 BLM21PG221SN1 and L1/L2 0R are now correct.
  - J2/J5: BOM Comment is the MPN and CPL Comment is the board value. This is intentional; JLC matches on Designator.
  - Every BOM line has an LCSC number.
- **W1 (U4 land): now OK.**
  - Pins are 0.28 × 0.60 at y ±0.70 (span 0.40–1.00) and x ±0.25 / ±0.75. The EP is 1.70 × 0.40. Board pads equal the library pads (U4 pads were the only footprint change; no tracks or vias changed).
  - Reference: TI SLVSAM5A p.17 (DPV 4211111-2/A), https://www.ti.com/lit/ds/symlink/tpd3f303.pdf. Body 1.50–1.70; terminal length 0.28–0.38 and width 0.20–0.30; pitch 0.50. EP 1.70±0.10 × 0.40±0.10 (p.18, 4211680/A).

  | Item | Value | Verdict |
  |---|---|---|
  | Toe (pad outer 1.00 vs body edge 0.75–0.85) | +0.15 to +0.25 | OK |
  | Heel (pad inner 0.40 vs terminal inner end 0.37–0.57) | +0.07 nominal; −0.03 only at the max-length / min-body extreme | OK. Was −0.03/−0.13 |
  | Width 0.28 vs terminal 0.20–0.30 | Side +0.04 nominal | OK |
  | Pin-to-pin 0.22 / pin-to-EP 0.20 | Mask openings are 1:1 with copper, so the mask webs are 0.22 and 0.20 | OK, ≥ the JLC solder-mask bridge minimum of 0.10 mm (green/red/yellow/blue/purple; 0.13 mm black/white), https://jlcpcb.com/capabilities/pcb-capabilities |
  | Pin paste | 1:1, 0.28 × 0.60. Area ratio at a 0.10 mm stencil ≈ 0.168 / (2 × 0.88 × 0.10) = 0.95 | OK. >0.66 per TI's note G (p.16) and IPC-7525 general practice |
  | EP paste | 2 × 0.75 × 0.30 (about 66%) | OK, unchanged |

  TI still publishes no DPV land, so the land remains derived. The dimensions above are taken from TI's package drawing; nothing was invented.
- **U4 clearances:** the closest different-net copper to a U4 pad is 0.203 mm (pad 4 NC to a SIM_RST_C track). The netclass rule is 0.15, and DRC reports 0 errors.
  - The same-net filled via SIM_1V8 (31.35, 24.75) is 0.06 mm hole-edge to pad 5. Its copper ring does not touch the pad, and it is a 0.20 filled-and-capped, tented via on the same net. Note only, no change from 9c48462.

## Other checks
- **Filled vias:** 30 per board (21 × 0.20 + 9 × 0.25), 120 per panel. The board, the drill files (84/36 on the panel) and the VIPPO Gerber (30/120) agree. In-pad vias are centred, and bottom caps are unchanged (the closest is C38.2's cap to JP2.2, 0.25–0.285 mm, hand-bridged).
- **Unfilled-hole overlap:** C14.2, FB1.1 and FB2.1 ring-only (WAIVED); TP13/TP14 (unassembled). Unchanged.
- **DRC:** 0 errors / 0 unconnected as-is and refilled. Parity 0.
- **Outline, J7, U1, stackup:** unchanged from 9c48462 (no edge, track or via change). R2.0 outline closed, copper ≥0.498 mm from the edge. J7 body is 0.106 and courtyard 0.049 inside the outline. U1 is the DK-verified chain. 4 layers, 1.6 mm, ENIG, 0.12 / 1.2 / 0.12 (= gbrjob).
- **Parts / reflow:** 51 top (171.4 mm² of pads) / 16 bottom (30.1 mm²). The bottom is reflowed first.
- **Bottom pad-to-via <0.3:** 26 pairs, WAIVED.
- **Panel:** rebuilt from v2_panel.json. 118.10 × 93.10 mm, 128 mouse-bites on the straight N/S edges only. 3 fiducials per side, 4 tooling holes. DRC 0/0. Content = 4 × the board (vias, 3300 tracks, all pads including the new U4 land, silk lines).
- **Rotations:** still to be checked in the JLC DFM preview (ORDER_NOTES B2). No offsets are pre-applied.

## Package: fab/staging-v2-36d8578/
- `nRF9161-v2-single-36d8578.zip` and `nRF9161-v2-panel-36d8578.zip`, each with gerbers, the VIPPO Gerber, gbrjob, drill files and maps, IPC-D-356, the BOM (repo jlc/BOM_JLC_v2.csv) and the CPL. The single CPL is repo jlc/CPL_JLC_v2.csv, re-verified against a fresh export. The panel CPL is 268 rows (4 × 67) with the same headers.
- **The DO-NOT-ORDER note is removed.** The order is still gated on quote questions Q1–Q17.

**Waivers kept:** C14, FB1.1, FB2.1, and the bottom pairs under 0.3 mm.
