# v2 fab pass: `v2` @ d89dc88 (final layout candidate, 2026-10-13 IST)

Branch `v2-fab-pass-d89dc88` (local) = d89dc88 + merge of `v2-fab-pass` (the 6645a01 pass, kept for history). PCB, schematic and libraries are read-only; the only design file I generated is the panel. JLC sources [A]–[P] are listed in `reports/V2_DFM_RULES.md` (branch v2-dfm-rules, fb29971). **[General DFM practice]** marks rules that aren't JLC's. Evidence: `reports/v2fab-d89dc88/`.

**Gate: RED** (§10).

## 1. Diff 6645a01 → d89dc88 (`diff_6645a01_d89dc88.txt`)
- Outline, thickness, stackup and every footprint (position, rotation, side, pads) are unchanged.
- **+4 vias, 0.20/0.30 GND:** (21.5, 18.95) and (21.5, 20.05) beside the U4 EP, (22.78, 22.4) near C33.2, and (18.78, 19.45) near C37.2.
- 3 new GND tracks: 2 × 0.3 mm, including the EP link, and 1 × 0.2 mm.
- VDD1 (13 segments) and VDD2 (7 segments) rerouted at 0.5 mm.
- Docs: README, V2_LAYOUT.md, V2_RF_REVIEW.md, PNGs.

## 2. Drill scheme: every 0.20 mm drill (`drill020_classification.txt`)
| # | Location (mm) | Net | Class |
|---|---|---|---|
| 1 | (28.25, 27.0) | GND | U1 pad 52 VIPPO, centred |
| 2 | (28.25, 29.0) | GND | U1 pad 56 VIPPO, centred |
| 3 | (28.25, 31.0) | GND | U1 pad 60 VIPPO, centred |
| 4 | (36.25, 27.0) | GND | U1 pad 36 VIPPO, centred |
| 5 | (40.75, 27.0) | GND | U1 pad 27 VIPPO, centred |
| 6 | (43.75, 27.0) | GND | U1 pad 21 VIPPO, centred |
| 7 | (41.25, 37.0) | GND | U1 pad 98 VIPPO, centred |
| 8 | (21.5, 18.95) | GND | **not in a pad.** Bottom, copper 0.05 mm from U4.9 (EP, GND), 0.25 mm from U4.4/U4.5 |
| 9 | (21.5, 20.05) | GND | **not in a pad.** Bottom, 0.05 mm from U4.9, 0.25 mm from U4.1 (SIM_IO_C) / U4.8 (SIM_IO) |
| 10 | (22.78, 22.4) | GND | **not in a pad.** 0.56 mm from C33.2 |
| 11 | (18.78, 19.45) | GND | **not in a pad.** 0.10 mm from C37.2 (GND), 0.18 mm from C37.1 (SIM_IO) |

The 0.25 mm drills are 9, all in U1 pad 103.

**Recommendation: (a), fill the 4 vias as well (20 filled vias). Pending Hardware PM confirmation.**
- **Fab risk:** JLC picks which vias to fill by the hole diameter given in the order remark (https://jlcpcb.com/help/article/pcb-via-covering). With (a), the 0.20 tool means "fill every hole", which is the unambiguous rule we already use, and it needs no layout change.
- **Why not (b):** (b) means Layout changes the drill again. The only legal drill smaller than 0.20 is 0.15 mm (JLC minimum via 0.15/0.25 mm for >1 mm boards: https://jlcpcb.com/capabilities/pcb-capabilities). That is about 10.7:1 aspect in 1.6 mm, a worse fab risk than 0.20. A larger, unused drill on a 0.30 pad (e.g. 0.22/0.24) leaves a ring below the board's own 0.05 mm VIPPO annulus, so it isn't viable without a bigger pad, and U4's area is tight.
- **RF / assembly:**
  - Vias 8 and 9 sit 0.05 mm from U4's GND EP and 0.25 mm from the SIM signal pads. A tented, unfilled hole that close to a paste pad depends on a 0.05 mm mask web. If the web fails, solder wicks off the EP or bridges toward SIM_IO, which is the kind of failure JLC's FAQ describes (https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2).
  - A filled, flat cap removes that path. Keeping the drill also keeps Layout's RF GND return near U4 exactly as reviewed in V2_RF_REVIEW.md.
- **Bottom-cap check:** none of the 4 caps sits under a bottom-side pad. Nearest copper gaps are 0.05 (U4 EP, same net), 0.10 (C37.2, same net), 0.18 (C37.1 SIM_IO), 0.25 (U4 signal pads) and 0.56 mm (C33.2). They stay tented; cap planarity (≤+25 µm proud) applies to the bottom too.
- **Cost:** POFV is charged on 4-layer boards (https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv). JLC publishes no price, so the cost of 16 vs 20 vias is unverified and goes in the quote (Q14).

## 3. Claims (`parts.json`)
| Claim | Result |
|---|---|
| 50×37.5 mm | 50.05×37.55 (bbox incl. line width). PASS |
| 4 layers | 4 Cu, 1.6 mm. PASS |
| 44 top / 23 bottom | 52 / 32 footprints. Assembled 44 / 23. BOM = CPL = 67 refs. PASS |
| J7 on top | F.Cu, NW corner. PASS |

## 4. Bottom parts and reflow order
These are unchanged from 6645a01 (footprints identical):
- 23 assembled: 4 × 0201, 12 × 0402, Q1 SOT-23, U2 SOT-23-5, U7/U8 SOT-23-6, U5/U6 VSSOP-8, **U4 USON-8 1.45 mm, 0.4 mm pitch (no-lead): RED** against the V2 rule (JLC publishes no limit). No BGA/LGA, THT, heavy or tall parts.
- Mass is not determined; the repo has no masses, and I didn't invent any. As a proxy, pad area is top 163.1 vs bottom 34.1 mm².
- Bottom-first order: 23 < 44 parts [E]. PASS. The order remark is kept.
- Nothing on the bottom under U1 + 1 mm. PASS.

## 5. VIPPO (U1)
- 16 = 7 × 0.20/0.30 + 9 × 0.25/0.40, all at 0.000 offset in U1 GND pads.
- Spacing to unfilled vias: min 0.868 mm copper edge for the U1 VIPPO set (`geometry_checks.txt`).
- The 0.20/0.25 tools are VIPPO-only **except the 4 above**: see §2. With (a) they become filled too.
- U1's bottom caps are clear of bottom pads. PASS.

## 6. Stackup
Board = job file = locked note: 0.12 / 1.2 / 0.12 FR4, 35 µm Cu × 4, 1.6 mm, ENIG. PASS (`package_sanity.txt`).

## 7. DRC and silk
- DRC: 0 errors, 0 unconnected, both as-is and refilled (`DRC_asis.json`, `DRC_refilled.json`).
  - Warnings: environment lib warnings only, plus 1 cosmetic J7 net-name parity warning as-is.
- Silk text ≥1.0/0.15 mm on both sides. PASS (`silk_widths.txt`).
- **Silk lines 0.12 mm: RED.** 45 bottom (U5–U8, Q1 ×5 each, passives ×2 each) and 6 on J20.
- **Silk spacing 0.15 mm: RED, 1 pair.** C23 (DNP) to U1 is 0.09 mm (`silk_spacing_015.txt`, run on a copy with the silk clearance set to 0.15; the board's own rule is 0). The via/annulus entries in that file come from the copy using default rules, not design errors.
- Silk over pads: 0.
- **Unfilled vias in soldered pads: RED.** These are unchanged from 6645a01: J7 C2/C3/C5/C7 (top), C34.1, R23.1, Q1.1, C42.1 (bottom). TP13 and JP2 have no paste. Edge overlaps: U5.4, C44.1, U2.1 (`via_in_pad_unfilled.txt`, `geometry_checks.txt`).
- **Bottom pads <0.3 mm from via copper [General DFM practice]: RED.** 55 pairs, up from 41 because of the 4 new vias (`geometry_checks.txt`).

## 8. U1 vs Nordic DK
The U1 footprint didn't change between 6645a01 and d89dc88 (§1). 6645a01 is pad-for-pad identical to b9d4e62 (`reports/v2fab/U1_vs_b9d4e62.txt`), and b9d4e62 was verified 159/159 against the DK. PASS.

## 9. Part-to-edge and panel
- Footprints and outline are unchanged, so the edge table carries over (`edge_clearance.txt`). The closest parts are J7 (courtyard 0.075 mm W), J20 (0.23 mm E), U.FL (0.72 mm W) and TP13/TP16 (pads 0.975 mm S).
- JLC doesn't publish a Standard part-to-edge figure. With the rail frame this is PASS for the panel. A single board isn't assemblable anyway (<70×70 mm [A]).

**Panel** `panel/nRF9161-v2-panel.kicad_pcb` (KiKit 1.8.1, `panel/v2_panel.json`), regenerated from d89dc88:
- **2×2, 118.10×93.10 mm** (70×70–250×250 [A]). 6 mm frame on all sides (≥5 mm [C][D]), 2 mm board gap.
- **Separation: mouse-bite tabs, not V-score.**
  - V-cut lines must run the whole panel (https://jlcpcb.com/help/article/pcb-panelization), and JLC recommends 1–2 mm clearance for sensitive parts (https://jlcpcb.com/blog/v-cut-panelization-standards).
  - Every board edge carries J7, U.FL, J20 or TPs.
- **Tabs:** N and S edges only (N at board x = 48/57, S at x = 24/44), 3 mm wide, 4 per board. No tabs on the W edge (J7, RF U.FLs) or the E edge (J20), following https://jlcpcb.com/blog/mouse-bite-panelization-guide.
- **Mouse bites:** 0.6 mm holes at 1.0 mm pitch (0.4 mm web), offset 0.1 mm outward for the pour clearance, so a light deburr is needed.
- The closest pad to a hole is 2.10 mm (C46), meeting ≥2.0 mm (https://jlcpcb.com/blog/smart-pcb-array-design).
- **Fiducials:** 3 per side, top and bottom, 1 mm copper with a 2 mm opening. Centre 4.35 mm from the edge, so the opening edge is at 3.35 mm [C][D][E]. Positions (15.05, 4.40), (103.05, 4.40), (15.05, 88.70) from the top-left.
- **Tooling:** 4 × 2.0 mm NPTH at 3.05 mm from the corners [D].
- **Panel DRC:** 0 errors, 0 unconnected (`DRC_panel.json`, `panel_geometry.txt`).

**Package** `fab/staging-v2-d89dc88/` (`package_sanity.txt`):
- `single/` and `panel/` each contain Gerbers (incl. VIPPO layer) + `.gbrjob`, PTH/NPTH drill + PDF maps, IPC-D-356, BOM, and `*-cpl-top.csv` / `*-cpl-bottom.csv`. Zips: `nRF9161-v2-{single,panel}-d89dc88.zip`, with ORDER_NOTES.txt inside.
- single: PTH 0.20×11, 0.25×9, 0.30×231, 1.00×10, no NPTH. CPL 44 top + 23 bottom. BOM 39 lines / 67 refs = CPL. DNP, TPs and JP2 are excluded.
- panel: 118.10×93.10, PTH ×4, NPTH 0.6×128 + 2.0×4. CPL 176 + 92, each ref ×4; KiKit fiducial/tooling rows removed (Q12).
- **Order the panel**, once the gate is green.

## 10. Red items
1. Unfilled vias in paste pads: J7 C2/C3/C5/C7, C34, R23, Q1, C42 (+ overlaps U5.4, C44.1, U2.1). `reports/v2fab-d89dc88/via_in_pad_unfilled.txt`
2. U4 USON (no-lead) on the bottom, against the V2 rule. `reports/v2fab-d89dc88/parts.json`
3. Silk lines at 0.12 mm: 45 bottom + 6 J20. `reports/v2fab-d89dc88/silk_widths.txt`
4. Silk spacing: C23 to U1 0.09 mm. `reports/v2fab-d89dc88/silk_spacing_015.txt`
5. Bottom pads <0.3 mm from via copper: 55 pairs [General DFM practice]. `reports/v2fab-d89dc88/geometry_checks.txt`
6. Drill-scheme decision open: 4 non-pad 0.20 mm vias need (a) or (b). Recommended (a); pending Hardware PM. `reports/v2fab-d89dc88/drill020_classification.txt`
