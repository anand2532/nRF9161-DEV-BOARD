# v2 fab pass: `v2` @ 6645a01 (2026-10-13 IST)

Branch `v2-fab-pass` (local). PCB, schematic and libraries are read-only; the only new design file is the panel (`panel/nRF9161-v2-panel.kicad_pcb`). Rules are from `reports/V2_DFM_RULES.md` (branch `v2-dfm-rules`, fb29971); JLC source letters [A]–[P] refer to that file. Lines marked **[General DFM practice]** are not JLC rules. Evidence lives in `reports/v2fab/`.

**Gate: RED.** See §9.

## 1. Claims
| Claim | Board file | Result |
|---|---|---|
| 50×37.5 mm | Edge.Cuts bbox 50.05×37.55 mm (incl. 0.05 line width) | PASS |
| 4 layers | 4 copper, 1.6 mm | PASS |
| 44 top / 23 bottom | 52 top / 32 bottom footprints. Assembled (in BOM, not DNP): **44 top / 23 bottom** (BOM = CPL = 67 refs). Not assembled: top C21–C24, C31, C32, C39 (DNP) + TP1; bottom TP7–9, TP13–17 + JP2 | PASS |
| J7 on top | J7 nanoSIM (JAE SF72S006) on F.Cu, NW corner | PASS |

## 2. Bottom-side parts (23 assembled)
| Ref | Package | Note |
|---|---|---|
| C35–C38 | 0201 | 22 pF |
| C33, C34, C41–C48 | 0402 | 100/220 nF |
| R21, R23 | 0402 | |
| Q1 | SOT-23 | |
| U2 | SOT-23-5 | LDO |
| U7, U8 | SOT-23-6 | |
| U5, U6 | VSSOP-8 (0.5 mm) | leaded |
| **U4** | **USON-8 1.45×1.45 mm, 0.4 mm pitch (TPD3F303DPV)** | **no-lead (QFN-class) package on the bottom: RED** under V2_DFM_RULES §1/§7 ("never BGA/LGA/QFN on the bottom"). JLC publishes no side restriction [A]; the rule is ours/[General DFM practice]. Tiny and light, so the actual drop risk is low. Either move U4 to the top or get JLC's OK in the quote (Q2) |
- No BGA/LGA, no through-hole parts, nothing heavy or tall on the bottom. The tallest is SOT-23.
- **Mass:** not determined. The repo has no datasheet masses, and I didn't invent any. As a proxy, total copper pad area of assembled parts is top 163.1 mm² vs bottom 34.1 mm² (`reports/v2fab/parts.json`).
- **Lighter bottom:** 23 vs 44 parts, and every heavy part (U1 LGA, J7, J20 THT, U.FLs, SW2, inductors) is on top. JLC assembles the side with fewer parts first [E], so the bottom goes first and U1 is reflowed once. PASS. The reflow-order remark is still in ORDER_NOTES because JLC doesn't promise the order [E].
- **THT:** J20 (1×10 header) is on top. It is wave-soldered [A], and the bottom-side SMT parts need a wave fixture [F]. Ask about the cost in the quote.

## 3. U1 keep-out, via caps, VIPPO
- **Bottom under U1** (F.Fab 27.95–44.05 × 26.7–37.3, +1 mm): no bottom pad or footprint inside. PASS (`geometry_checks.txt`).
- **VIPPO:** 16 = **7 × 0.20/0.30** (U1 GND pads 21, 27, 36, 52, 56, 60, 98) + **9 × 0.25/0.40** (U1 pad 103, GND). All are offset 0.000 from their pad centre. The 0.20 and 0.25 tools are VIPPO-only (PTH drill: 0.20×7, 0.25×9, 0.30×231, 1.00×10). The minimum gap to an unfilled via is 0.868 mm copper edge to copper edge (1.068 mm hole edge to hole edge), above the 0.45 mm minimum. PASS. (v1 had 29; v2 dropped the signal-pad vias.)
- **VIPPO bottom caps vs bottom parts:** all 16 sit under U1, inside the empty keep-out, so no bottom pad is near a cap. PASS.
- **Unfilled vias in pads: RED.** These 0.30 mm vias are tented with mask but sit inside soldered pads with paste. JLC warns that solder flows into vias in pads and weakens the joint [G] (https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2).
  - Via centre inside the pad: **J7 C2/C3/C5/C7 (top)**, **C34.1, R23.1, Q1.1, C42.1 (bottom)**. TP13 and JP2 also have one, but they get no paste.
  - Via overlapping the pad edge: U5.4, C44.1, U2.1, TP14.
  - Evidence: `via_in_pad_unfilled.txt`, `geometry_checks.txt`.
  - Fix: move these vias off the pads, or give them a unique drill and add them to the fill list.
- **Bottom pads ≥0.3 mm from via caps [General DFM practice]: RED.** 41 bottom pad/via pairs are under 0.3 mm, including the overlaps above. The board's own 0.1 mm clearance rule passes in DRC. List: `geometry_checks.txt`.

## 4. Stackup
Board stackup: F.Cu 35 µm / FR4 0.12 / In1 35 µm / FR4 1.2 / In2 35 µm / FR4 0.12 / B.Cu 35 µm, mask 10 µm, 1.6 mm, ENIG. The regenerated job file has the same values, plus `Finish: ENIG` and 4 layers. This matches `docs/FAB_STACKUP_NOTES.md` (4L, 1.6 mm, L1–L2 ~0.12 mm, ENIG). PASS.

## 5. DRC and silk
- DRC as-is and after a KiCad Python zone refill: **0 errors, 0 unconnected** (`DRC_asis.json`, `DRC_refilled.json`).
  - The remaining warnings are 82 `lib_footprint_issues`, because the stock KiCad libraries aren't installed on the box. That is an environment issue.
  - There is also 1 parity warning: the J7 `VPP/SWP` net-name slash-escape on an unconnected pad. It is cosmetic.
  - The refilled copy has no schematic next to it, so its parity results are an artefact.
- Silk text: top 37 and bottom 32 texts, all ≥1.0 mm / 0.15 mm. PASS.
- **Silk line width: RED.** 45 bottom footprint lines and 6 on J20 (top) are 0.12 mm, under the 0.15 mm minimum. The bottom lines are on U7, C41–C48 and others.
- **Silk spacing 0.15 mm: RED, 1 pair.** C23 (DNP) silk to U1 silk is 0.09 mm (`silk_spacing_015.txt`). The board's own silk-clearance rule is set to 0, so I re-ran DRC on a copy with 0.15 mm.
- Silk over pads: 0 (DRC silk_over_copper). PASS.

## 6. U1 vs Nordic DK
The U1 footprint `Board:nRF9161_LGA_16.0x10.5mm` at 6645a01 is pad-for-pad identical to b9d4e62: 159 pads, same positions relative to the origin, sizes, shapes, mask and paste margins, rotation 180, on top (`U1_vs_b9d4e62.txt`). b9d4e62 was verified against the DK at 159/159 (docs/FAB_READY_CHECKLIST.md, fab pass b9d4e62), so v2 inherits that match. PASS.

## 7. Part-to-edge and panel
Closest parts to the board edge (pads / body / courtyard, `edge_clearance.txt`):
- J7 is 0.70 mm (N) / 0.45 mm (W) / 0.075 mm (W).
- J20 is 1.175 / 0.705 / 0.23 mm (E).
- The U.FL connectors J2 and J5 are 1.45 / 1.2 / 0.72 mm (W).
- TP13 and TP16 pads are 0.975 mm (S); their F.Fab ring overhangs the edge.

JLC doesn't publish a Standard-PCBA part-to-edge number (V2_DFM_RULES §2, Q4). Because the panel puts rails around every board, this is PASS for the panel and not suitable for single-board assembly.

**Panel** (`panel/nRF9161-v2-panel.kicad_pcb`, KiKit 1.8.1, preset `panel/v2_panel.json`):
- **2×2, 118.10 × 93.10 mm.** That is inside the 70×70–250×250 mm range for a Standard panel [A].
- 6 mm frame on all four sides (≥5 mm rails [C][D]) and a 2 mm gap between boards. JLC's mouse-bite guide gives 1.6–2 mm, min 1.2: https://jlcpcb.com/blog/mouse-bite-panelization-guide
- **Separation: tabs with mouse bites, not V-score.**
  - Every board edge has a part close to it: J7 (W/N), U.FL (W), J20 (E), TPs (S).
  - V-score lines must cross the whole panel (https://jlcpcb.com/help/article/pcb-panelization). JLC asks for ≥0.4 mm, and recommends 1–2 mm, from the V-cut centreline for copper and tall or sensitive parts (https://jlcpcb.com/blog/v-cut-panelization-standards).
  - V-cut would stress the J7 SIM holder, the U.FL RF connectors and J20.
- **Tab placement:** tabs are on the N and S edges only, 2 per edge (N at board x=48 and 57, S at x=24 and 44, each 3 mm wide), so 4 per board.
  - The W edge (J7 and the U.FL RF connectors) and the E edge (J20) have no tabs. JLC says to avoid mouse bites near protruding components: https://jlcpcb.com/blog/mouse-bite-panelization-guide
  - The closest pad to any mouse-bite hole is 2.10 mm (C46, bottom). J7 is at 2.28 mm. That meets JLC's ≥2.0 mm from routed tab edges: https://jlcpcb.com/blog/smart-pcb-array-design
- Mouse bites are 0.6 mm drills at 1.0 mm pitch, which is 0.4 mm hole edge to hole edge (the mouse-bite guide gives 0.6 mm and 0.35–0.4 mm).
  - Offset is −0.1 mm, outward into the tab. That keeps the 0.25 mm hole clearance to the board's GND pour.
  - JLC says to centre holes on the frame line or up to 1/3 inside the board. Outward placement leaves a small nub, so a light deburr is needed.
- **Fiducials:** 3 per side, top and bottom (≥3 per side [E]; 3–4 [C]). 1 mm copper with a 2 mm mask opening [C]. The centre is 4.35 mm from the panel edge, so the opening edge is at 3.35 mm, meeting both ≥3.35 mm including keep-out [C] and 3.85 mm [D]. Positions from the panel's top-left: (15.05, 4.40), (103.05, 4.40), (15.05, 88.70).
- **Tooling holes:** 4 × 2.0 mm NPTH [D], centres 3.05 mm from both edges at the four corners.
- **Panel DRC: 0 errors, 0 unconnected** (`DRC_panel.json`). The only warnings are the 199 environment `lib_footprint_issues`. Design rules were inherited from the project.

## 8. Staging package `fab/staging-v2-6645a01/`
- `single/` and `panel/` each contain: Gerbers (F/In1/In2/B Cu, mask, paste, silk, Edge.Cuts, VIPPO user layer) plus the `.gbrjob`, `drill/` PTH and NPTH with PDF maps, IPC-D-356, BOM, and separate `*-cpl-top.csv` / `*-cpl-bottom.csv`. Each has a zip next to it: `nRF9161-v2-single-6645a01.zip`, `nRF9161-v2-panel-6645a01.zip`.
- **Order the PANEL.** A 50×37.5 mm board is under the 70×70 mm minimum for Standard PCBA [A].
- Sanity checks:
  - single: 4 layers, 50.05×37.55, closed outline, PTH 0.20×7, 0.25×9, 0.30×231, 1.00×10, NPTH none. CPL 44 top + 23 bottom, rotations 0/±90/180. BOM = 39 lines, 67 refs, which equals the CPL refs. DNP and TP/JP are excluded.
  - panel: 118.10×93.10. PTH ×4 of the single board. NPTH 0.6×128 mouse bites + 2.0×4 tooling. CPL 176 top + 92 bottom (= 4×). KiKit fiducial/tooling rows removed. Refs repeat per board (`{orig}`), so check in the quote whether JLC needs unique designators (Q12).
- Not ready to order: the gate is RED.

## 9. Red items
1. Unfilled vias inside paste pads: J7 C2/C3/C5/C7, C34, R23, Q1, C42 (plus edge overlaps U5.4, C44.1, U2.1). `reports/v2fab/via_in_pad_unfilled.txt`
2. U4 USON-8 (no-lead) on the bottom, against the V2 rule. `reports/v2fab/parts.json`
3. Silk lines 0.12 mm (<0.15): 45 bottom, 6 J20. `reports/v2fab/geometry_checks.txt`
4. Silk spacing: C23 to U1 is 0.09 mm (<0.15). `reports/v2fab/silk_spacing_015.txt`
5. Bottom pads <0.3 mm from via copper: 41 pairs [General DFM practice]. `reports/v2fab/geometry_checks.txt`

Open, expected (JLC quote): Q1–Q11 from V2_DFM_RULES, plus Q12 (duplicate designators in the panel CPL), Q13 (wave fixture for J20 with bottom SMT, and its cost), Q14 (POFV charge on 4-layer boards, 16 vias), Q15 (8:1 aspect ratio for the 0.20 mm drill in 1.6 mm), Q16 (manual JP2 bridge on the bottom).
