# FAB READY CHECKLIST: v2 (UART modem module, double-sided)

Board: `v2` @ 6645a01. Pass date: 2026-10-13 IST. Full report: `reports/V2_FAB_PASS_6645a01.md`. Rules: `reports/V2_DFM_RULES.md` (branch v2-dfm-rules, fb29971).
v1's checklist stays in `docs/FAB_READY_CHECKLIST.md`.

## Overall gate: **RED** (5 items below; the JLC quote items are open as expected)

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
