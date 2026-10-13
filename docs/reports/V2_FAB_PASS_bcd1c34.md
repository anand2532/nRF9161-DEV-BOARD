# v2 fab pass: bcd1c34 (v2-cosmetic, v2j). **GREEN apart from the JLC quote**

Worked in a /tmp worktree on local branch v2-fab-pass-bcd1c34, with v2-fab-pass-5ad8bde merged in. The PCB was read-only. Evidence is in reports/v2fab-bcd1c34/.

| Check | Result |
|---|---|
| Copper changes vs 5ad8bde | **None.** In the git diff of the .kicad_pcb, only text `at` / `size` / `justify` lines changed (21 + 21 + 2/1), in J20/LTE/nRST/CT gr_texts and the D2 reference. Tracks, vias, zones, pads, Edge.Cuts and stackup are unchanged. See diff_5ad8bde_bcd1c34.txt. |
| Silk height / stroke | 0 texts under 1.0 mm or 0.15 mm, 0 lines under 0.15 mm, on both sides. The labels are 1.0 h × 0.6 w × 0.15 stroke. CTS is now CT (8 in the panel, no CTS). JLC: text ≥1.0 mm, line ≥0.15 mm (https://jlcpcb.com/capabilities/pcb-capabilities). R1 is closed. |
| Silk spacing / pads / edge | No silk-to-silk gaps under 0.15 mm between different items. The closest silk to a mask opening is 0.175 mm (F RTS to R3.2), then 0.185 mm (B RI to U2.5). The D2 reference is 0.587 mm from D1.1. All labels are ≥3.2 mm from the edge (the bottom board name 1.19 mm). DRC silk rules: 0 violations. The only sub-0.15 notch is U1's own pin-1 circle (unchanged, DK footprint). |
| Logo | A–M 0.215 mm, M–P 0.254 mm, no slit, strokes ≥0.15 mm. |
| Filled vias | **22 per board** (13 × 0.20 + 9 × 0.25), **88 per panel**. The drill files and the VIPPO Gerber agree (22 / 88 flashes). |
| Unfilled-hole edge overlap | Ring-only at C14.2, FB1.1, FB2.1 (WAIVED). Hole overlaps only with unassembled TP13/TP14. Unchanged. |
| DRC | 0 errors / 0 unconnected as-is and refilled. Only environment library warnings and the cosmetic J7 parity warning. |
| Outline / J7 | Closed R2.0 outline, 1 outline, 0 holes. Copper ≥0.498 mm from the edge (JLC ≥0.2). J7's body is 0.106 mm and its courtyard 0.052 mm inside the arc (unchanged geometry). |
| U1 | Unchanged; identical back to the DK-verified b9d4e62. |
| Stackup | 4 layers, 1.6 mm, ENIG, 0.12 / 1.2 / 0.12. Board and both .gbrjob files agree. |
| Parts / reflow | 51 top / 16 bottom = 67. The BOM is identical to the c37dc20 package. The bottom is reflowed first (30.1 vs 170.1 mm² of pads). |
| Bottom pad-to-via <0.3 | 26 pairs, WAIVED (JP2.2 filled cap 0.285 mm, ORDER_NOTES B7). |
| Panel | Rebuilt from panel/v2_panel.json (KiKit 1.8.1, tabs N 48/57, S 24/44). 118.10 × 93.10 mm, 2×2, 128 mouse-bites, on the straight N/S edges only (board-local x 6–43, against the straight span 2.0–48.05). Fiducials 1 mm with a 2 mm opening, 3 per side; 4 × 2 mm tooling holes. Panel DRC 0 errors / 0 unconnected. Content = 4 × the board (980 vias, 3212 tracks, every silk text). |

**Package:** fab/staging-v2-bcd1c34/, with nRF9161-v2-single-bcd1c34.zip and nRF9161-v2-panel-bcd1c34.zip (22 files each). The DO-NOT-ORDER note is removed. ORDER_NOTES now reads "GREEN apart from the JLC quote", and the order is still gated on the quote questions, including Q17 (mouse-bite 5 mm).

**Waivers kept:** C14, FB1.1, FB2.1, and the bottom pairs under 0.3 mm.
