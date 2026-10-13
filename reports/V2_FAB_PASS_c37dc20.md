# v2 fab pass: `v2` @ c37dc20 (Layout v2e, 2026-10-13 IST)

Branch `v2-fab-pass-c37dc20` (local) = c37dc20 + merge of `v2-fab-pass-365b7f6` + RF's `reports/V2_RF_REVIEW.md` appendix (authored by RF Power Engineer). The PCB is read-only; the panel is the only generated design file. JLC sources are listed in `reports/V2_DFM_RULES.md` (fb29971). Evidence: `reports/v2fab-c37dc20/`.

## Gate: **GREEN apart from the JLC quote** (Q1–Q16 open)

## Changes 365b7f6 → c37dc20
- v2e-1: C38.2 via changed to a 0.20/0.30 filled via at the pad centre.
- v2e-2: C12 via moved off C12.1, now 0.20/0.30 filled.
- v2e-3: 3 new 0.30/0.60 GND vias for RF F1, and a SIM_IO B.Cu jog.
- No footprint moved, was added or was removed. U1 is identical.

## Layout's claims
| Claim | Verified |
|---|---|
| DRC 0 errors / 0 unconnected | **Yes**, as-is and after zone refill. Only environment lib warnings and the cosmetic J7 net-name parity warning remain (`DRC_asis.json`, `DRC_refilled.json`) |
| C38.2 via 0.20 filled at (33.25, 19.58) | **Yes.** It sits at 0.000 mm from the C38.2 copper pad centre (pad 0.46×0.40), so the 0.30 cap is fully inside the pad with ≥0.05 mm margin; the paste aperture centre is 0.025 mm away. A proper filled via in the pad. Nearest other copper: C38.1 0.26 mm (top), JP2.2 0.25–0.285 mm (bottom, tented) (`drill_fill_classification.txt`) |
| C12 via 0.20 filled at (45.6, 31.4), clear of C12.1 | **Yes.** Not in the pad: the ring is 0.05 mm from C12.1 copper, and the hole edge is 0.10 mm from the pad |
| F1 added 3 standard GND vias, none in a pasted pad | **Yes.** (31.3, 23.9) is 0.215 mm from U4.1/U4.8; (34.45, 23.2) is 0.25 mm from C35.2; (35.85, 24.95) is 0.112 mm from C37.2. All are 0.30/0.60, tented, and outside every pad |
| 22 filled vias per board | **Yes: 22 = 13 × 0.20 + 9 × 0.25** (PTH drill file: 0.20×13, 0.25×9). Every 0.20/0.25 hole is intended for filling: the 16 in U1 pads, C38.2, the C12 via and the 4 RF GND vias at (21.5, 18.95), (21.5, 20.05), (22.78, 22.4), (18.78, 19.45). The scheme is "fill every 0.20 mm hole". **88 per panel** |

## Unfilled-hole edge-overlap re-check (all pads, both sides, copper + paste apertures; `unfilled_hole_pad_overlap.txt`)
All vias are tented. 6 overlaps:
- **C14.2 / C14 paste, FB1.1, FB2.1:** ring-only overlaps of 0.023–0.044 mm, hole ≥0.106 mm outside the pad. **WAIVED** (confirmed by Hardware PM).
- **TP13.1** (via centred) and **TP14.1** (ring 0.15 mm): bottom test pads, no paste, not assembled. Informational, not a solder joint.
- **No unfilled hole overlaps any assembled pasted pad.** PASS

## Other checks
| Check | Result |
|---|---|
| Size / layers / stackup | 50.05×37.55, 4 Cu, 1.6 mm. Board = job = locked note (0.12/1.2/0.12, ENIG). PASS |
| Parts | 51 top / 16 bottom assembled (unchanged). BOM = CPL = 67. No BGA/LGA/QFN/THT/heavy on the bottom. PASS |
| Reflow order | Bottom lighter (16 vs 51; 30.1 vs 167.1 mm² pads). Bottom first, U1 once. PASS |
| Bottom under U1 + 1 mm | Empty. PASS (`geometry_checks.txt`) |
| VIPPO spacing | Min 0.5 mm copper edge to unfilled vias. PASS |
| Bottom pad to via <0.3 mm | **WAIVED** (confirmed by Hardware PM). 20 pairs on assembled parts, by conservative bbox; all are 0.30 tented vias, none overlaps, no filled cap involved (`bottom_pair_waiver.txt`). Note: the filled C38.2 via's bottom cap is 0.25–0.285 mm from JP2.2 (unassembled, hand-bridged); this is called out in ORDER_NOTES B7 |
| Silk | 0 items below 1.0/0.15 mm on either side. Board rule silk clearance 0.15, DRC 0 silk violations. PASS (`U1_JP_silk_checks.txt`) |
| U1 vs Nordic DK | U1 is identical to 365b7f6 (chain back to the DK-verified b9d4e62). PASS |
| Part-to-edge | No footprint moved, so the 365b7f6 table carries over; covered by the panel frame. PASS (`edge_clearance.txt`) |
| JP | JP2 only (bottom, no paste), so a manual bridge is needed. PASS |

## Panel
`panel/nRF9161-v2-panel.kicad_pcb`, rebuilt from `panel/v2_panel.json` on c37dc20.
- **2×2, 118.10×93.10 mm**, 6 mm frame, 2 mm gaps.
- Mouse-bite tabs on N/S only (N at x = 48/57, S at x = 24/44), 3 mm wide, 0.6 mm holes at 1.0 mm pitch.
- 3+3 fiducials (1 mm copper, 2 mm opening, 4.35 mm from the edge) and 4 × 2 mm tooling holes.
- The closest pad to a mouse-bite hole is 2.10 mm.
- **Panel DRC: 0 errors, 0 unconnected** (`DRC_panel.json`, `panel_geometry.txt`).
- JLC rationale and citations: `reports/V2_FAB_PASS_d89dc88.md` §9.

## Package `fab/staging-v2-c37dc20/`
- `single/` and `panel/`: Gerbers (+ VIPPO layer, `.gbrjob`), PTH/NPTH drill + maps, IPC-D-356, BOM, top/bottom CPL, and zips containing ORDER_NOTES.txt (`package_sanity.txt`).
- single: PTH 0.20×13, 0.25×9, 0.30×230, 1.00×10. CPL 51 + 16.
- panel: PTH 0.20×52, 0.25×36, 0.30×920, 1.00×40. NPTH 0.6×128 + 2.0×4. CPL 204 + 64.
- **Order the panel.**

## Open (JLC quote)
Q1–Q16 per `docs/FAB_READY_CHECKLIST_V2.md`. Q14 is now the POFV price for **22 vias per board / 88 per panel**.
