# v2 fab pass: `v2` @ 365b7f6 (pass v2d, 2026-10-13 IST)

Branch `v2-fab-pass-365b7f6` (local) = 365b7f6 + merge of `v2-fab-pass-d89dc88`. The PCB is read-only; the panel is the only generated design file. JLC sources are listed in `reports/V2_DFM_RULES.md` (fb29971). Evidence: `reports/v2fab-365b7f6/`. Drill scheme: **(a) fill every 0.20 mm hole, CONFIRMED** by Hardware PM.

## Gate: **RED (2 items)**
1. **New unfilled 0.30 mm GND via centred in pasted pad C38.2** (top) at (33.366, 19.465). This via was added in v2d-2 when C38 moved to the top. The paste aperture overlaps it fully, so solder wicks into the via (JLC: https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2). Evidence: `via_in_pad_unfilled.txt`, `new_vias_vs_moved_parts.txt`.
2. **C12.1 (top, 0201, VDD_GPIO) overlaps the unfilled via at (45.6, 31.6) by 0.28 mm**, so the hole edge sits inside the pasted pad. This is **pre-existing**: my d89dc88/6645a01 passes only checked top-side vias for centre-in-pad and missed it. Evidence: `via_in_pad_unfilled.txt`.

The fix for both: Layout moves the via off the pad, or makes it 0.20 mm so it gets filled under the confirmed scheme.

Waived (general practice, DRC-legal, tented, not red):
- **FB1.1, FB2.1 and C14** have via copper overlapping the pad edge by 0.02–0.044 mm. The hole stays more than 0.1 mm outside the pad (`via_in_pad_unfilled.txt`). Hardware PM should confirm this waiver.
- **Bottom pad to via <0.3 mm:** my bbox method finds **20 unique pairs on assembled parts**. Layout counts 15; the bbox method is conservative. None overlaps a pad, none involves a filled 0.20/0.25 cap (all are 0.30 tented vias), and DRC is clean. The waiver condition is met (`bottom_pair_waiver.txt`).

## Changes d89dc88 → 365b7f6 (from the commit log and board diff)
- v2d-1 moved unfilled vias off pasted pads.
- v2d-2 moved U4 and C33–C38 to the top beside J7, rerouted the SIM nets on F.Cu, and rerouted SWDIO/P0.22.
- v2d-3 set silk lines to 0.15 mm and the silk clearance rule to 0.15 mm, and trimmed C23's silk.
- Net via change: +26 / −28 (0.30 mm vias). The 0.20 and 0.25 sets are unchanged.

## Checks
| Check | Result |
|---|---|
| Size / layers | 50.05×37.55 mm, 4 Cu, 1.6 mm. PASS |
| Part counts | 59 top / 25 bottom footprints. **Assembled 51 top / 16 bottom**; BOM = CPL = 67. J7, U4 and C33–C38 are on top. PASS |
| Bottom parts | 8 × 0402 C, 2 × 0402 R, Q1 SOT-23, U2 SOT-23-5, U7/U8 SOT-23-6, U5/U6 VSSOP-8. No BGA/LGA/QFN/THT, nothing heavy or tall. **U4 is off the bottom. PASS** |
| Lighter bottom / reflow order | 16 vs 51 parts, pad area 30.1 vs 167.1 mm² (mass not in the repo, not estimated). Bottom first [E], U1 reflowed once. PASS |
| Bottom under U1 outline + 1 mm | Nothing (the moves were to the top, away from U1). PASS (`geometry_checks.txt`) |
| 0.20 mm drills | **11**: 7 in U1 pads (centred) + 4 not in pads. The 4 are now away from U4: nearest pads are J7 top 0.26–2.7 mm, with no pad over a cap. **0.25 mm: 9**, U1 pad 103. **Filled total 20.** PASS (`drill020_classification.txt`) |
| VIPPO spacing | Min 0.5 mm copper edge to an unfilled via (≥0.45). U1 VIPPO bottom caps: no bottom pad nearby. PASS |
| New vias vs moved parts | All 26 new vias are DRC-legal. Closest to the moved parts: C38.1 0.15, C37.1 0.15, C35.1 0.15, U4.8 0.215 mm (tented, outside the pads). **Exception: the C38.2 via-in-pad (red 1)** (`new_vias_vs_moved_parts.txt`) |
| Stackup | Board = job = locked note (0.12/1.2/0.12, ENIG). PASS (`package_sanity.txt`) |
| DRC | 0 errors, 0 unconnected, as-is and refilled. Only environment lib warnings and the cosmetic J7 net-name parity warning remain. The board rule is now silk clearance 0.15, with 0 silk violations. PASS |
| Silk | Texts ≥1.0/0.15 mm and lines ≥0.15 mm on both sides (0 below the minimum). PASS (`silk_widths.txt`) |
| U1 vs Nordic DK | U1 is identical to d89dc88 (159 pads, same position and rotation), and the chain back to b9d4e62 is DK-verified. PASS (`U1_and_JP_checks.txt`) |
| Part-to-edge | Closest: J7 0.7 N, TP13/TP16 0.975 S, R21 1.105 S, J20 1.175 E, U.FL 1.45 W. Covered by the panel frame. PASS (`edge_clearance.txt`) |
| JP | JP2 only, bottom, no paste, so a manual bridge is needed. PASS |

## Panel
`panel/nRF9161-v2-panel.kicad_pcb`, rebuilt from `panel/v2_panel.json` (KiKit 1.8.1) on 365b7f6.
- **2×2, 118.10×93.10 mm**, 6 mm frame, 2 mm gaps.
- **Mouse-bite tabs** on the N/S edges only (N at x = 48/57, S at x = 24/44), 3 mm wide, 0.6 mm holes at 1.0 mm pitch.
- 3 fiducials per side: 1 mm copper, 2 mm opening, 4.35 mm from the edge.
- 4 × 2 mm tooling holes.
- The closest pad to a mouse-bite hole is 2.10 mm (C46).
- **Panel DRC: 0 errors, 0 unconnected** (`DRC_panel.json`, `panel_geometry.txt`).
- The rationale and JLC citations are unchanged from `reports/V2_FAB_PASS_d89dc88.md` §9.

## Package `fab/staging-v2-365b7f6/`
- `single/` and `panel/`: Gerbers (+ VIPPO layer, `.gbrjob`), PTH/NPTH drill + maps, IPC-D-356, BOM, top/bottom CPL, and zips with ORDER_NOTES.txt.
- single: PTH 0.20×11, 0.25×9, 0.30×229, 1.00×10. CPL 51 + 16.
- panel: PTH ×4, NPTH 0.6×128 + 2.0×4. CPL 204 + 64 (each ref ×4; Q12).
- **Order the panel**, once green.
