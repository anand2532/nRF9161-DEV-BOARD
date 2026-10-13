# v2 fab pass: 5ad8bde (v2-cosmetic, v2h + v2i)

Worked in a /tmp worktree on local branch v2-fab-pass-5ad8bde, with v2-fab-pass-42876bb merged in. The PCB was read-only. Evidence is in reports/v2fab-5ad8bde/. The package is at fab/staging-v2-5ad8bde/.

## Gate: RED (1 item). Everything else GREEN apart from the quote.
| # | Item | Result | Evidence |
|---|---|---|---|
| R1 | Silk text height | **RED: 21 labels are 0.8 mm high (stroke 0.15).** F.Silkscreen: J20 TX, RX, RTS, CTS, DTR, RI, GND, VIN, VIO, nRST, plus LTE (11). B.Silkscreen: the same 10 J20 labels. JLC requires text height ≥1.0 mm ("Characters height less than 40 mil (1.0mm) will be unidentifiable"): https://jlcpcb.com/capabilities/pcb-capabilities. The v2i-2/v2i-3 commit messages state 0.8 mm, so this is by design, not a measurement artefact. | silk_checks.txt |

Fix options for PM: raise these labels to ≥1.0 mm, move them to F.Fab/B.Fab, or explicitly accept the risk of illegible labels (a PM decision; not waived here).

## Fixed since 42876bb
- AMP logo, measured directly from the polygons: 5 filled pieces join into 3 letters, 5.5 × 1.735 mm. The A–M gap is **0.215 mm** and the M–P gap is **0.254 mm**, both ≥0.15. **The P notch is gone**: a closing test finds no slit under 0.15 mm. No stroke is under 0.15 mm (mitre-opening test).
- J7: the F.Fab body clears the R2.0 arc by 0.106 mm. The courtyard chamfer runs from (16.075, 13.2) to (16.8, 11.975), with its ends 0.052 and 0.059 mm inside the arc and a minimum line distance of 0.049 mm (the 0.003 mm difference is from polygonisation). All J7 copper is ≥0.647 mm from the edge.

## Checks
- **Diff against 42876bb:** no footprint moved or changed. U1 is identical (and is unchanged from the DK-verified b9d4e62). Two vias were added, (23.0, 26.5) and (18.5, 41.5), both 0.30/0.60 GND. No tracks changed. Stackup unchanged. The changes are silk and outline only.
- **Silk:** stroke widths are all ≥0.15. There are no silk-to-silk gaps under 0.15 mm between different items on either side; this includes the new LTE label and the vertical J20 labels. Heights: see R1. The only sub-0.15 notch is inside U1's own pin-1 circle against its body line (0.012 mm²). That geometry is unchanged from the DK-verified footprint, so it is a note only. DRC (silk_over_copper, silk_edge_clearance, min_silk_clearance 0.15): 0 violations.
- **Filled vias: 22 per board** (13 × 0.20/0.30 + 9 × 0.25/0.40), **88 per panel**. The 2 restored vias are 0.30 mm, so they are not filled. The count is confirmed from the board and from both drill files (single: 0.20×13, 0.25×9, 0.30×223; panel: 52/36/892).
- **Unfilled-hole edge overlap**, covering all 0.30 holes against every pad bbox (copper and paste, both sides). Ring-only overlaps at C14.2 (plus its paste), FB1.1 and FB2.1, all WAIVED. Hole overlaps only with unassembled TP13 and TP14. Nothing new, and the 2 restored vias are clear.
- **DRC:** 0 errors / 0 unconnected as-is, and the same after refilling the pours. Warnings are only the cosmetic J7 parity warning and environment library warnings.
- **R2.0 outline:** 4 arcs of R2.0 plus lines of 46.0 and 33.5, forming one closed outline with no holes. Closest copper to the edge is zone fill at 0.498 mm (the 0.5 mm rule, minus polygonisation), then the J7.SH pad at 0.647 mm. Nothing is outside the outline. JLC needs ≥0.2 mm (same page).
- **Stackup:** 4 layers, 1.6 mm, ENIG, F.Cu 35 µm / 0.12 / 1.2 / 0.12. The board and both .gbrjob files agree, and the stackup is unchanged.
- **Parts:** 51 top / 16 bottom assembled, 67 in total. The BOM is identical to the c37dc20 package, and the CPL matches by reference. Bottom pad area is 30.1 mm² against 170.1 mm² on top, so **the bottom is reflowed first** and U1 goes through reflow once.
- **Bottom pad-to-via <0.3 mm:** 26 pairs, the WAIVED category. The filled C38.2 cap is 0.285 mm from JP2.2 (hand-bridged, called out in ORDER_NOTES B7).

## Panel
- The committed panel (built in 0c124fa) has the right geometry, but **its content is stale**: it lacks the v2i-2 LTE label and the v2i-3 J20 labels (40 silk texts missing compared with 4 × the board).
- **Rebuilt** from panel/v2_panel.json (KiKit 1.8.1, same annotation tabs: N 48/57, S 24/44) on 5ad8bde. This is the panel used for the package.
- The rebuilt panel's geometry is identical to the committed one: 118.10 × 93.10 mm, 2×2, 128 mouse-bite holes. Tabs sit only on the straight N/S edges, at board-local x 6–43 against a straight span of 2.0–48.05.
- Fiducials are 1 mm with a 2 mm opening, 3 per side. There are 4 tooling holes of 2 mm.
- Content matches 4 × the board: 980 vias, 3212 tracks, and every silk text.
- Panel DRC: 0 errors / 0 unconnected.
- Note: the JLC page says "Minimum width of breakaway tab ... with mouse-bites, the minimum width is 5mm". Our tabs are 3 mm; the rails are 6 mm. It is unclear whether this refers to the tab or the rail, so it is **unverified** and should be asked with the quote.

## Package (built despite R1; marked DO NOT ORDER in ORDER_NOTES)
- fab/staging-v2-5ad8bde/nRF9161-v2-single-5ad8bde.zip and nRF9161-v2-panel-5ad8bde.zip. Each holds gerbers, the VIPPO gerber, .gbrjob, drill files and maps, IPC-D-356, BOM, CPL top/bottom and ORDER_NOTES.
- The VIPPO gerber now carries the 22 / 88 flashes. The c37dc20 VIPPO.gbr was empty.

## Waivers kept
C14, FB1.1, FB2.1, and the bottom pairs under 0.3 mm: WAIVED.

## Quote
Pending; no figures.
