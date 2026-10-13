# v2 fab pass: 42876bb (v2-cosmetic, "cosmetic pass v2f/g"), CHECK-ONLY

Per the Hardware PM steering: v2h will restore 2 standard GND vias at (23.0, 26.5) and (18.5, 41.5). **No final package was generated for this SHA** (fab/staging-v2-42876bb/ intentionally absent). The package will be built on the v2h SHA. The PCB was read-only. Evidence is in reports/v2fab-42876bb/.

## Gate: RED (2 silk-logo items), everything else GREEN apart from the quote
| # | Item | Result | Evidence |
|---|---|---|---|
| R1 | AMP logo: spacing from polygon 0 (A) to polygon 2 (M) | **RED: 0.143 mm, below the 0.15 mm silk-to-silk minimum** (DRC does not check graphic-to-graphic) | silk_checks.txt |
| R2 | AMP logo: notch inside the P (polygon 1) at x 45.457–45.564, y 47.137–47.381 | **RED: gap about 0.107 mm, below 0.15 mm. Likely an artefact of the font conversion; it will not resolve on silk** | silk_checks.txt |
| | Logo strokes (mitre-erosion sweep) | no feature under 0.15 mm, OK | silk_checks.txt |

Suggested fix for v2h: re-export the logo with ≥0.15 mm letter spacing and fill or close the P notch. Silk limits are line ≥0.15 mm and text ≥1.0 mm (https://jlcpcb.com/capabilities/pcb-capabilities).

## Checks
- **Silk:** 0 texts under 1.0 mm or 0.15 mm stroke, 0 lines under 0.15 mm (F: 43 texts / 112 lines; B: 30 texts / 63 lines). DRC (silk_over_copper, silk_edge_clearance, min_silk_clearance 0.15) reports 0 silk violations, so there is no silk on pads, mask openings or the edge.
- **Filled vias: 22/board** (13 × 0.20/0.30 + 9 × 0.25/0.40), **unchanged from c37dc20**. The 9 removed vias were all 0.30 GND, so every 0.20/0.25 drill is still intended for filling (scheme (a)). The list is in drill_fill_classification.txt; that is 88 per panel.
- **Removed vias:** the diff counts 9, all 0.30 GND: (17.0,41.5) (17.0,47.5) (18.5,25.0) (18.5,41.5) (18.5,43.0) (20.0,41.5) (21.5,26.5) (23.0,26.5) (24.5,26.5). The v2f-2 commit message says 8.
- **DRC:** as-is 0 errors / 0 unconnected; after refilling the pours 0 errors / 0 unconnected. The only warnings are the cosmetic J7 parity warning and environment library warnings.
- **Unfilled-hole edge overlap** (0.30 holes against every pad bbox, copper and paste, both sides): ring-only overlaps at C14.2 (plus its paste), FB1.1 and FB2.1, all WAIVED, unchanged. Hole overlaps are only with unassembled bottom TP13/TP14, as before. No new items. See unfilled_hole_pad_overlap.txt.
- **C44:** moved (41.0,46.2)→(41.0,46.4), bottom, rot 0. Nearest pads: C43 at 1.03 mm, U6.1 at 1.365 mm. Nearest via is 0.13 mm away on VDD_GPIO, the same net as C44.1; it is not in the pad-overlap list. Nothing on the bottom is under U1 (+1 mm).
- **R2.5 outline:** 4 arcs + 4 lines, one closed outline with no holes. Copper to edge: closest pad J7.SH at 0.515 mm, tracks at 0.65 mm, zone fill at 0.498 mm (polygonisation of the 0.5 mm rule). All are ≥0.2 mm (JLC, same page). DRC copper-edge reports 0. Note: the earlier -0.3 / 0.0 figures came from a script flaw and were re-measured with shapely.
- **Note (not red):** at the NW R2.5 corner, J7's F.Fab body rectangle extends about 0.13 mm past the arc (0.02 mm² of area), and so does its courtyard. Its pads are 0.515 mm inside. The holder corner will overhang the rounded corner slightly. This is mechanical/cosmetic only, and the F.Fab rectangle may overstate the real part corner (unverified).
- **Bottom pad-to-via <0.3 mm:** 26 pairs, the WAIVED category (including the filled cap 0.285 mm from JP2.2).

## Panel (de49f6e)
Panel used: **panel/nRF9161-v2-panel.kicad_pcb from de49f6e, kept as is.**
- 118.10 × 93.10 mm, 2×2.
- 128 mouse-bite holes: N tabs at board-local x 30–43 and S tabs at x 6–30, all on the straight segments (2.5–47.55). None are on the R2.5 corners, and the nearest is ≥3.5 mm from where a corner arc begins.
- Fiducials 1 mm with a 2 mm opening, T and B, 3 per side. Tooling holes 2 mm, 4×.
- Panel DRC 0 errors / 0 unconnected (only library warnings).
- Content matches 42876bb: 972 vias = 4 × 243, C44 at its new position, same silk count.
- A check rebuild from v2_panel.json on 42876bb gave identical geometry (panel_review_rebuilt_check.txt). The rebuild was not committed.

## Waivers kept (docs/FAB_READY_CHECKLIST_V2.md)
C14, FB1.1, FB2.1, and the bottom pairs under 0.3 mm stay WAIVED.

## Quote
Not requested; still pending, with no figures.
