# FAB READY CHECKLIST: v2 (UART modem module, double-sided)

Board: `v2` @ **c37dc20** (Layout v2e). Pass date: 2026-10-13 IST. Report: `reports/V2_FAB_PASS_c37dc20.md`. Evidence: `reports/v2fab-c37dc20/`. Package: `fab/staging-v2-c37dc20/`. Drill scheme: fill every 0.20 mm hole, CONFIRMED. **22 filled vias per board, 88 per panel.**

## Overall gate (c37dc20): **GREEN apart from the JLC quote**

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Claims: size, 4L, J7 top; assembled 51 top / 16 bottom | PASS | parts.json |
| 2 | Connectivity as-is / refilled | PASS 0/0 | DRC_asis.json, DRC_refilled.json |
| 3 | DRC errors | PASS 0 | same |
| 4 | Bottom parts (no BGA/LGA/QFN, heavy, tall, THT) | PASS | report |
| 5 | Lighter bottom / reflow order (bottom first) | PASS 16 vs 51 | report |
| 6 | Nothing on the bottom under U1 + 1 mm | PASS | geometry_checks.txt |
| 7 | No unfilled hole overlapping an assembled pasted pad (edge-overlap method, both sides) | PASS | unfilled_hole_pad_overlap.txt |
| 7a | FB1.1, FB2.1, C14: ring overlap 0.02–0.044 mm, hole >0.1 mm outside the pad | **WAIVED** (Hardware PM) | unfilled_hole_pad_overlap.txt |
| 8 | Bottom pads <0.3 mm from via copper (20 pairs, all 0.30 tented, none overlaps, no filled cap) | **WAIVED** (Hardware PM, general practice) | bottom_pair_waiver.txt |
| 9 | Fill scope 22 = 13 × 0.20 + 9 × 0.25, all intended; U1/C38.2 ones centred (0.000 mm); ≥0.45 mm to unfilled | PASS | drill_fill_classification.txt |
| 10 | Layout v2e claims (C38.2, C12 via, 3 F1 vias) | PASS | drill_fill_classification.txt |
| 11 | Stackup board = job = locked note | PASS | package_sanity.txt |
| 12 | Silk ≥1.0/0.15, spacing 0.15, none on pads | PASS | U1_JP_silk_checks.txt, DRC_asis.json |
| 13 | U1 vs Nordic DK | PASS | U1_JP_silk_checks.txt |
| 14 | Part-to-edge (panel frame) | PASS | edge_clearance.txt |
| 15 | Panel 118.10×93.10, 6 mm frame, 3+3 fiducials, 4 × 2 mm tooling, mouse bites, DRC 0/0 | PASS | panel/, DRC_panel.json |
| 16 | Package single + panel, CPL top/bottom | PASS | fab/staging-v2-c37dc20/ |
| 17 | Order notes (22/board, 88/panel; bottom first; JP2 manual bridge + cap caution) | PASS | fab/staging-v2-c37dc20/ORDER_NOTES.md |
| Q | JLC quote Q1–Q16 (Q14 = POFV price for 22/board) | OPEN | below |

---

# Superseded: pass on 365b7f6

## Overall gate (365b7f6): **RED (2 items)**

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Claims: size, 4L, J7 top; assembled 51 top / 16 bottom | PASS | parts.json |
| 2 | Connectivity as-is / refilled | PASS 0/0 | DRC_asis.json, DRC_refilled.json |
| 3 | DRC errors (silk clearance rule now 0.15) | PASS 0 | same |
| 4 | Bottom parts (no BGA/LGA/QFN, heavy, tall, THT) | PASS (U4 moved to top) | report |
| 5 | Lighter bottom / reflow order | PASS 16 vs 51 | report |
| 6 | Nothing on the bottom under U1 + 1 mm | PASS | geometry_checks.txt |
| 7 | No unfilled vias in pasted pads | **FAIL**: C38.2 (new via, centred); C12.1 (0.28 mm overlap, pre-existing). FB1.1/FB2.1/C14 edge overlaps ≤0.044 mm, hole outside the pad: waiver proposed | via_in_pad_unfilled.txt |
| 8 | Bottom pads ≥0.3 mm from via copper | WAIVED (general practice): 20 pairs by bbox (Layout: 15), DRC-legal, no filled cap involved | bottom_pair_waiver.txt |
| 9 | Fill scope: 0.20 ×11 + 0.25 ×9 = 20; U1 ones centred; ≥0.45 mm to unfilled | PASS | drill020_classification.txt |
| 10 | New vias vs moved parts | PASS except C38.2 (item 7) | new_vias_vs_moved_parts.txt |
| 11 | Stackup board = job = locked note | PASS | package_sanity.txt |
| 12 | Silk text/lines ≥1.0/0.15, spacing 0.15, none on pads | PASS | silk_widths.txt, DRC_asis.json |
| 13 | U1 vs Nordic DK | PASS | U1_and_JP_checks.txt |
| 14 | Part-to-edge (panel frame) | PASS | edge_clearance.txt |
| 15 | Panel 118.10×93.10, 6 mm frame, 3+3 fiducials, 4 × 2 mm tooling, mouse bites, DRC 0/0 | PASS | panel/, DRC_panel.json |
| 16 | Package single + panel, CPL top/bottom | PASS (contents); not orderable while RED | fab/staging-v2-365b7f6/ |
| 17 | Order notes (fill scheme confirmed, 51/16, bottom-first) | PASS | fab/staging-v2-365b7f6/ORDER_NOTES.md |
| Q | JLC quote Q1–Q16 (Q14 = POFV price for 20 vias/board) | OPEN | below |

---

# Superseded: pass on d89dc88

## Overall gate (d89dc88): **RED** (6 items; the JLC quote items are open as expected)

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Claims: 50×37.5, 4L, 44 top / 23 bottom, J7 top | PASS | parts.json |
| 2 | Connectivity as-is / refilled | PASS 0/0 | DRC_asis.json, DRC_refilled.json |
| 3 | DRC errors | PASS 0 | same |
| 4 | Bottom parts (no BGA/LGA/QFN, heavy, tall, THT) | **FAIL**: U4 USON-8 | report §4 |
| 5 | Lighter bottom / reflow order | PASS: 23 vs 44 parts; mass not determined | report §4 |
| 6 | Nothing on the bottom under U1 + 1 mm | PASS | geometry_checks.txt |
| 7 | No unfilled vias in soldered pads | **FAIL**: J7 ×4, C34, R23, Q1, C42 (+ overlaps) | via_in_pad_unfilled.txt |
| 8 | Bottom pads ≥0.3 mm from via copper [General DFM practice] | **FAIL**: 55 pairs | geometry_checks.txt |
| 9 | U1 VIPPO 16 (7×0.20 + 9×0.25), centred, ≥0.45 mm to unfilled | PASS | report §5 |
| 10 | 0.20/0.25 drills exclusive to the fill scope | **OPEN (decision)**: 4 non-pad 0.20 GND vias near U4/C33/C37. Recommend (a) fill (20 total), pending Hardware PM | drill020_classification.txt |
| 11 | Stackup board = job = locked note | PASS | package_sanity.txt |
| 12 | Silk text ≥1.0/0.15 | PASS | silk_widths.txt |
| 13 | Silk lines ≥0.15 | **FAIL**: 51 lines at 0.12 | silk_widths.txt |
| 14 | Silk spacing ≥0.15 / no silk on pads | **FAIL**: C23 to U1 0.09 mm; on pads 0 | silk_spacing_015.txt |
| 15 | U1 vs Nordic DK | PASS (unchanged since b9d4e62) | report §8 |
| 16 | Part-to-edge | PASS with the panel frame | edge_clearance.txt |
| 17 | Panel (118.10×93.10, 6 mm frame, 3+3 fiducials, 4 × 2 mm tooling, mouse bites, DRC 0/0) | PASS | panel/, DRC_panel.json |
| 18 | Package single + panel, CPL top/bottom | PASS (contents); not orderable while RED | fab/staging-v2-d89dc88/ |
| 19 | Order notes (option (a), pending HW PM) | PASS (written) | fab/staging-v2-d89dc88/ORDER_NOTES.md |
| Q | JLC quote Q1–Q16 | OPEN | below |

Q14 now reads: POFV price on 4-layer boards for **20** vias per board (16 if option (b)).

---

# Superseded: pass on 6645a01 (kept for history)

## 6645a01 gate: **RED** (5 items below; the JLC quote items are open as expected)

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Claims: 50×37.5, 4L, 44 top / 23 bottom, J7 top | PASS | report §1, `reports/v2fab/parts.json` |
| 2 | Connectivity as-is / refilled | PASS (0 / 0) | `reports/v2fab/DRC_asis.json`, `DRC_refilled.json` |
| 3 | DRC errors | PASS (0) | same. Only environment lib warnings and 1 cosmetic J7 net-name parity warning remain |
| 4 | Bottom parts: no BGA/LGA/QFN, heavy, tall or THT | **FAIL**: U4 USON-8 (no-lead) on the bottom | report §2 |
| 5 | Lighter bottom (JLC does the side with fewer parts first) | PASS: 23 vs 44 parts, pad area 34 vs 163 mm². Mass not determined | report §2 |
| 6 | Nothing on the bottom under U1 (+1 mm) | PASS | `reports/v2fab/geometry_checks.txt` |
| 7 | No unfilled vias in soldered pads (JLC FAQ: https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2) | **FAIL**: J7 C2/C3/C5/C7, C34, R23, Q1, C42 (+ edge overlaps U5.4, C44.1, U2.1) | `reports/v2fab/via_in_pad_unfilled.txt` |
| 8 | Bottom pads ≥0.3 mm from via caps [General DFM practice] | **FAIL**: 41 pairs | `reports/v2fab/geometry_checks.txt` |
| 9 | VIPPO: 16 = 7×0.20/0.30 + 9×0.25/0.40, centred, drills exclusive, ≥0.45 mm to unfilled vias (min 0.868), no bottom-cap conflict | PASS | report §3 |
| 10 | Stackup: board = job = FAB_STACKUP_NOTES (4L, 1.6, 0.12/1.2/0.12, ENIG) | PASS | report §4, `single/gerbers/*.gbrjob` |
| 11 | Silk text ≥1.0/0.15 mm, both sides | PASS | report §5 |
| 12 | Silk lines ≥0.15 mm | **FAIL**: 45 bottom + 6 J20 at 0.12 mm | `reports/v2fab/geometry_checks.txt` |
| 13 | Silk spacing ≥0.15 mm / no silk on pads | **FAIL**: C23 to U1 0.09 mm (1 pair). Silk on pads: 0 | `reports/v2fab/silk_spacing_015.txt` |
| 14 | U1 vs Nordic DK | PASS (identical to b9d4e62, which was DK-verified) | `reports/v2fab/U1_vs_b9d4e62.txt` |
| 15 | Part-to-edge | PASS for the panel (rails all round, no tabs on the J7/U.FL/J20 edges). Not suitable for single-board assembly | `reports/v2fab/edge_clearance.txt` |
| 16 | Panel ≥70×70, ≤250×250, rails ≥5, fiducials, tooling, DRC | PASS: 118.10×93.10, 6 mm frame, 3+3 fiducials, 4×2 mm tooling, DRC 0/0 | `panel/`, `reports/v2fab/DRC_panel.json`, `panel_geometry.txt` |
| 17 | Staging package (single + panel; Gerbers, job, drill + maps, D356, BOM, CPL top/bottom) | PASS (contents). Not orderable while RED | `fab/staging-v2-6645a01/` |
| 18 | Order notes | PASS (written) | `fab/staging-v2-6645a01/ORDER_NOTES.md/.txt` |
| Q | JLC quote | OPEN | below |

## Open quote questions
Q1–Q11 are from V2_DFM_RULES §7:
- Q1. Bottom-side size and mass limits.
- Q2. QFN/LGA/BGA on the first-reflow side. Applies to U4.
- Q3. Carrier/fixture charge for double-sided boards.
- Q4. Part-to-edge distance.
- Q5. Double-sided panel rules.
- Q6. Lead time.
- Q7. Two framed stencils for $16.42, and a different thickness per side.
- Q8. Second reflow vs POFV/LGA.
- Q9. Will JLC honour a "bottom first" remark?
- Q10. AOI and SPI on both sides.
- Q11. Mask over bottom caps.

New in this pass:
- Q12. Duplicate designators in the panel CPL.
- Q13. Wave fixture for J20 with bottom-side SMT, and its cost.
- Q14. POFV price on 4-layer boards (16 vias per board).
- Q15. 0.20 mm drill through 1.6 mm (8:1 aspect ratio).
- Q16. Manual JP2 bridge on the bottom side.

## Fix list for Layout
1. Move the unfilled vias out of the J7, C34, R23, Q1 and C42 pads, and clear the U5.4, C44.1 and U2.1 overlaps. Alternatively, give those vias a unique drill and add them to the fill list.
2. Move U4 to the top, or keep it on the bottom only if JLC confirms Q2.
3. Set the 0.12 mm silk lines to ≥0.15 mm (bottom-side footprints, J20).
4. Fix the C23/U1 silk spacing. C23 is DNP, so its silk can be trimmed.
5. Get bottom pads ≥0.3 mm from via copper where practical [General DFM practice].
