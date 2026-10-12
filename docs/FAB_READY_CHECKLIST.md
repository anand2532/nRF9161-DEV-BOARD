# FAB READY CHECKLIST — nRF9161-DEV-BOARD

**Working path:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Checklist date:** 2026-09-23 (IST / Asia/Calcutta)  
**Overall gate:** **RED — NOT FABRICATION-READY** (re-assessed at `vippo` bc6d0fc, 2026-10-12 IST; see "Fab pass bc6d0fc" below)

Do not declare fab-ready until **every** row below is PASS **and** `unconnected_items = 0`.  
Authoritative connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items` (see `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`).

---

## Overall gate

| Field | Value |
| --- | --- |
| Status | **RED / FAIL** (bc6d0fc) |
| unconnected_items | **10**, all GND F.Cu zone-to-zone, **unchanged after zone refill (real, not phantom)**. Evidence: `fab/staging-bc6d0fc/DRC_bc6d0fc_asis.json`, `fab/staging-bc6d0fc/DRC_bc6d0fc_refilled.json` |
| DRC errors (bc6d0fc) | 0 errors. Warnings: track_dangling 4 (VDD_GPIO B.Cu ×3 near (70,8)/(48.05,5.5)/(48.05,3.46); P0.11 B.Cu (44,29.2)); lib_footprint_issues 98 (stock KiCad libs not installed on the box, environment only); lib_footprint_mismatch 1 (TI_TPD3F303) |
| Gerbers regenerated | **Yes**: `fab/staging-bc6d0fc/` from bc6d0fc (zones refilled, /tmp copy). Not releasable while RED |
| Checklist fully green | **No** |

### Fab pass bc6d0fc (2026-10-12 IST)

| # | Item | Status | Evidence / reason |
| --- | --- | --- | --- |
| 1 | Connectivity (hard gate: unconnected = 0) | **FAIL** | 10 GND zone islands remain after refill, so they are real isolated F.Cu copper, not phantom. F.Cu GND fill has 31 pieces; 11 have no stitching via (smallest: U1 slivers 0.38 mm² at (36.1–36.4,25.6–27.2) and (40.6–40.9,25.6–27.2), 1.23 mm² at (41.1,36.8–40.9); largest: 64.5 mm² at (53.6–74.8,24.9–28.3) with C1/C3 GND, 70.6 mm² at (66.5–76.4,7.4–22.0), 50.5 mm² at (56.7–74.7,15.9–24.2)). A stitching via to In1 GND fixes each large piece. The U1 slivers are better removed (zone min-width / island removal) than stitched |
| 2 | DRC | **PASS w/ warnings** | 0 errors; 4 dangling tracks to clean up (see above) |
| 3 | U1 footprint vs Nordic DK | **PASS** | 159/159 pads, sizes, centres ≤0.002 mm, mask +0.05 NSMD, paste 1:1. `reports/DFM_VIPPO_NOTE.md` §1.7 |
| 4 | VIPPO geometry | **PASS w/ note** | Group A 16 × 0.20/0.30 (9 in pads 52–60 + 7 added), all centred. Group B 9 × 0.25/0.40, **6 off-centre by 0.20 mm** (land edge = pad edge). 0.20/0.25 tools are used only by VIPPO; spacing to unfilled vias ≥0.85 mm. Fill scope is 25. Note §1.4 |
| 5 | Gerbers | **PASS (staging)** | 4 Cu + F/B Mask, F/B Paste, F/B Silk, Edge.Cuts, VIPPO (User.1) + `nRF9161-DEV-BOARD-job.gbrjob` (LayerNumber 4, 120.1×80.1, 1.6 mm). Board outline closed (1 outline, 0 holes) |
| 6 | Job-file stackup | **FAIL** | `job.gbrjob` MaterialStackup still has 3 × 0.48 mm dielectrics, which contradicts the LOCKED stackup (L1–L2 ≈0.12 mm, `docs/FAB_STACKUP_NOTES.md`). Fix the board stackup in KiCad or state the stackup explicitly in the order |
| 7 | Drill | **PASS** | `drill/nRF9161-DEV-BOARD-PTH.drl` T1 0.200 ×16, T2 0.250 ×9, T3 0.300 ×329, T4 0.400 ×41, T5 0.650 ×12, T6 1.000 ×78; NPTH file has 0 holes; PDF drill maps generated |
| 8 | IPC-D-356 | **PASS** | `fab/staging-bc6d0fc/nRF9161-DEV-BOARD.d356` |
| 9 | BOM | **FAIL (DNP sync)** | `nRF9161-DEV-BOARD-bom.csv` covers 96 placed refs, matching the board. The schematic excludes 8 as DNP/excluded (C21, C22, C23, C24, C31, C32, D7, J16). The PCB marks only C22/C23/C24/D7 as DNP |
| 10 | CPL | **FAIL (DNP sync)** | `nRF9161-DEV-BOARD-cpl.csv` (78 rows, all top, rotations 0/±90/180, plausible). **It still contains C21, C31, C32, J16**, which are DNP in the schematic, so the assembler would place them. Update PCB from schematic (DNP attributes) or hand-strip before ordering. `-cpl-all.csv` includes DNP parts |
| 11 | Silk legibility (JLC: line ≥0.15 mm, text height ≥1.0 mm, https://jlcpcb.com/capabilities/pcb-capabilities) | **FAIL** | 254 of 260 silk texts are under 1.0 mm (most 0.65–0.8; smallest 0.6 mm: "SWD", "nRF9161-DEV-BOARD", "RF: 0.20mm microstrip…", "GND"). 151 have stroke under 0.15 (0.12). All 260 silk graphics are 0.12/0.10 mm. Not fixed |
| 12 | Silk overlap / over pads | **PASS w/ 1 note** | Default DRC: 0. With JLC 0.15 mm pad-to-silk clearance (temp /tmp project): 1 silk_overlap (U1 reference vs U1 silk at (36.1,38.7)); silk_over_copper 0 |
| 13 | Assembly (stencil 0.10 mm, X-ray first article) | **OPEN** | Per `reports/DFM_VIPPO_NOTE.md` §1.5. Apply to the assembler order |
| C7 | JLC 4L filled & capped quote | **OPEN** (expected) | 8:1 aspect, cost/lead, no-protrusion note. Scope is now 25 vias |

Package: `fab/staging-bc6d0fc/nRF9161-DEV-BOARD-fab-bc6d0fc.zip` (**staging only; do not order while RED**).

---

## 1. Stackup notes / layer stack

| | |
| --- | --- |
| **Status** | **PASS** (design intent locked; fab coupon still pending) |
| **Evidence** | **DECIDED 2026-09-23** (Anand delegated) — see `docs/FAB_STACKUP_NOTES.md`. PCB is **4-layer** F.Cu / In1.Cu / In2.Cu / B.Cu; overall target 1.6 mm. Authoritative RF dielectric: L1↔L2 **H ≈ 0.10–0.15 mm** (~0.12 mm preferred); job.gbrjob **0.48 mm** dielectrics treated as generic export defaults. Finish **ENIG**. Controlled impedance **50 Ω SE** for LTE/GNSS RF (`RF_50OHM`: ANT*/AUX*/GPS/GNSS_ANT). Mid-layer exact mm: fab to propose. History of README vs gbrjob conflict retained in that note. |
| **To go green** | Fab confirms overall thickness + mid construction to hit L1–L2 H and Z0 coupon; align future KiCad/`job.gbrjob` MaterialStackup after `unconnected_items=0` Gerber regen. |

---

## 2. Drill / via rules

| | |
| --- | --- |
| **Status** | **FAIL** |
| **Evidence** | Live PCB: **250 vias** — sizes `(0.6/0.3)×176`, `(0.8/0.4)×58`, `(0.5/0.3)×14`, **`(0.45/0.25)×2`**. Project rules (`nRF9161-DEV-BOARD.kicad_pro`): `min_via_diameter=0.5`, `min_through_hole_diameter=0.3`, Default/RF via 0.6/0.3. Stale drill export `fab/gerbers/nRF9161-DEV-BOARD-PTH.drl` (CreationDate **2026-09-16T14:09:40+05:30**): tools T1=0.300, T2=0.400, T3=0.650, T4=1.000 mm. NPTH file is empty of holes (header + M30 only). `reports/DRC_AFTER_CONNECT.json` violations include **`via_diameter`: 2**, **`drill_out_of_range`: 2** (consistent with 0.25 mm drills under 0.3 mm min). Also **`via_dangling`: 82**. |
| **To go green** | Replace or justify the two 0.25 mm drills (meet fab min, typically ≥0.3 mm). Clear dangling vias / finish nets. Re-run DRC with 0 drill/via diameter errors. Regenerate PTH/NPTH after copper freeze. Confirm fab min drill / annular ring. |

---

## 3. Solder mask / paste

| | |
| --- | --- |
| **Status** | **UNKNOWN** |
| **Evidence** | PCB setup: `pad_to_mask_clearance 0`, `allow_soldermask_bridges_in_footprints no`. Pro rule `solder_mask_to_copper_clearance=0.0`. Stale Gerbers include F/B Mask and F/B Paste (`fab/gerbers/*_Mask.*`, `*_Paste.*`). **B_Paste** is aperture-empty (header only, 500 B) — matches CPL **top-only** (`fab/nRF9161-DEV-BOARD.pos.csv`: 80 parts, Side=top). F_Paste present (~14 KB). LGA paste/stencil guidance in `README.md` Assembly notes (0.10–0.12 mm stainless, Nordic DK practice) — not yet validated against final footprints. No EMS stencil review on file. |
| **To go green** | After copper/silk freeze: regenerate mask/paste Gerbers; review LGA NSMD openings vs Nordic Table 56 / DK; document stencil thickness & reduction; confirm zero-critical mask slivers with fab; keep B_Paste empty only if board stays single-sided SMT. |

---

## 4. Panelization notes

| | |
| --- | --- |
| **Status** | **PASS** (single-board intent; no panel required in-tree) |
| **Evidence** | Outline 120×80 mm (`FINAL_FAB_RELEASE.md`, gbrjob Size X=120.1 Y=80.1). No panelization docs, V-score/mouse-bite language, or panel Gerbers under project (search of working tree excluding `.git`/`.mcp-backups`). Edge.Cuts Gerber present: `fab/gerbers/nRF9161-DEV-BOARD-Edge_Cuts.gm1`. |
| **To go green** | If fab/EMS requires a panel, add explicit panel drawing + notes; otherwise keep as single board and state that in the PO. |

---

## 5. Gerber + drill + IPC-356 + BOM + CPL export readiness

| Artifact | Status | Evidence | To go green |
| --- | --- | --- | --- |
| Gerbers (Cu/Mask/Silk/Paste/Edge) | **FAIL** | Set exists under `fab/gerbers/` (4 Cu + mask/paste/silk + edge + `*-job.gbrjob`), but CreationDate **2026-09-16T14:09:40+05:30**. Later routing/connectivity work documented **2026-09-17** backup and **2026-09-18** DRC (`DRC_AFTER_CONNECT.json`). Live PCB now **777 segments / 250 vias** vs earlier review snapshots. `FINAL_FAB_RELEASE.md`: Gerbers **/fab not generated** for that release. | Drive unconnected→0, then regenerate full Gerber set from frozen PCB; replace `fab/gerbers/`; zip for fab. |
| Drill (PTH/NPTH) | **FAIL** | `*-PTH.drl` / `*-NPTH.drl` present but same **2026-09-16** stamp; stale vs live PCB; NPTH empty. | Regenerate with Gerbers; verify tool list vs fab min drill. |
| IPC-356 / netlist for fab | **FAIL** | No `*ipc*`, `*356*`, or fab netlist found under project maxdepth 3 (excluding backups). `kicad_pro` has `ipc2581` key but no export file. | Export IPC-356 (or fab-required netlist) from frozen PCB; place under `fab/`. |
| BOM | **UNKNOWN** | Root `BOM.csv` present (83 lines + header; MPN/Manufacturer columns; 12 DNP/Optional nonempty). Currency vs final schematic/PCB not proven after last route passes; no `fab/BOM.csv` copy. | Refresh BOM from schematic after freeze; place dated copy in `fab/`; resolve DNP vs assemble list with PM. |
| CPL / pick-and-place | **UNKNOWN** | `fab/nRF9161-DEV-BOARD.pos.csv` present (80 top-side placements). Same checkout stamp as other fab files; not proven regenerated with final XY after later copper. | Regenerate POS/CPL with Gerbers; verify vs centroid of frozen PCB; include bottom if any bottom parts added. |
| Fab package zip | **FAIL** | No `*.zip` under project root or `fab/`. | Create single fab archive: Gerbers+drill+gbrjob+BOM+CPL+IPC-356+README fab notes. |

---

## 6. Manufacturer / fab constraints notes

| | |
| --- | --- |
| **Status** | **UNKNOWN** |
| **Evidence** | Design targets in `README.md` / `FINAL_DESIGN_REVIEW.md`: min trace 0.10 mm (RF 0.20, signal ~0.18, power 0.40); min clearance 0.10 (0.15 RF/power class); assumed JLC-like 4-layer 1.6 mm. gbrjob DesignRules Outer Pad/Track 0.1, MinLineWidth 0.18; Finish **None**. No PO, fab capability sheet, or signed stackup coupon in-tree. |
| **To go green** | Select fab house; confirm min trace/space/drill/annular/mask; lock stackup+impedance coupon; set finish; document constraints in this checklist or `docs/FAB_NOTES.md`. |

---

## 7. Assembly notes

| | |
| --- | --- |
| **Status** | **PASS** (notes exist; assembly not released) |
| **Evidence** | `README.md` §§ Assembly notes, First power-up, Hardware validation — LGA/stencil, DNP RF match, JP1/JP2, ferrite choices, bring-up sequence. BOM marks DNP/Optional. CPL top-only. |
| **VIPPO assembly items** | Stencil **0.10 mm** (supersedes the earlier 0.12 mm), U1 paste ~70–85% of pad area per Nordic nWP054 (https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/footprint.html) and nWP056 (https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html). Rationale (Hardware PM): within RF's 100–120 µm dimple-fill range, at its bottom. **First-article X-ray** of U1 covering pads 52–60 and the 9 GND-pad vias; any open or voiding >25% means a tighter spec next spin. **U1 footprint vs DK: FAIL.** 99 outer pads are 0.8×0.3 and extend 0.40 mm past the package outline, and the mask is not NSMD; see `reports/DFM_VIPPO_NOTE.md` §1.5/§1.7. |
| **To go green** | Keep notes current after freeze; attach to EMS kit with BOM DNP list and RF keepout photo/PDF (`fab/nRF9161-DEV-BOARD-sch.pdf`, PCB PDF under `fab/`). |

---

## 8. Final DRC / ERC / unconnected-items gate

| | |
| --- | --- |
| **Status** | **FAIL** |
| **Evidence** | **Unconnected = 80** — `reports/FINAL_FAB_RELEASE.md` (hard gate failed); `reports/DRC_AFTER_CONNECT.json` (`unconnected_items` length 80, date 2026-09-18 IST); `reports/UNCONNECTED_AFTER_FINAL.csv` (80 rows). Classes summarized in FINAL_FAB_RELEASE (A55/F6/G7/C3/E9). Additional DRC in same JSON: silk_overlap 147, via_dangling 82, silk_over_copper 36, track_dangling 13, lib_footprint_mismatch 3, via_diameter 2, drill_out_of_range 2. Older `reports/DRC_SUMMARY.txt` / README cite 116 unconnected — superseded by AFTER_CONNECT/FINAL_FAB (80). ERC: `reports/ERC_kicad-cli.rpt` (2026-09-16) **0 errors, 1 warning** (lib_symbol_mismatch U4); root `nRF9161-DEV-BOARD-erc.rpt` older with dangling global-label warnings. |
| **To go green** | Route/repair until `unconnected_items=0` and ratsnest=0; clear or waive remaining DRC with documented severity; re-run ERC clean for release; only then regenerate fab outputs. |

### 8.1 DFM waive candidates (Option E accept class — 2026-09-23 IST)

Reviewed against `reports/REMAINING_OPENS_MATRIX.md` + live `reports/DRC_PASS30W_AFTER.json` (unconnected=**67**). **Hard gate stays `unconnected_items → 0`.** Overall gate remains **RED**. No Gerbers regenerated.

| Bucket | DFM verdict | Note |
| --- | --- | --- |
| GND×10 zone islands | **WAIVE candidate** (cosmetic) | Zone↔zone @ ≈(−0.05,−0.05); Class E fill/island artifact — refill/stitch after copper freeze; not a discrete signal break |
| ANT_FIT / AUX / AUX_FIT | **MUST-FIX** (RF) | Not a keepout waive: RF policy requires **stub-terminate** DNP shunt pads (`docs/RF_POWER_REVIEW.md` Class C); do not leave open |
| P0.19 / P0.22 leftover ratsnests | **MUST-FIX** (electrical) | Partial-keep copper left real GPIO island gaps (U1.30↔B stub; B↔F P0.22 islands) — finish or place before fab |

Only GND Class-E could be jointly redefined as non-gate after zone refill proves phantom; do **not** redefine RF or GPIO partial-keeps.

---

## Inventory snapshot (evidence tree)

| Path | Role |
| --- | --- |
| `nRF9161-DEV-BOARD.kicad_pro` / `.kicad_pcb` / `.kicad_sch` | Project + PCB + root schematic |
| `schematic/*.kicad_sch`, `schematics/*.kicad_sch` | Multi-sheet schematics (12 sheets) |
| `BOM.csv` | Root BOM |
| `fab/gerbers/*` | Gerber + PTH/NPTH + gbrjob (stale 2026-09-16 IST) |
| `fab/nRF9161-DEV-BOARD.pos.csv` | CPL |
| `fab/*.pdf`, `fab/pdf/` | Sch/PCB PDF exports |
| `reports/FINAL_FAB_RELEASE.md` | Latest fab-release verdict: **NOT READY**, unconnected=80 |
| `reports/DRC_AFTER_CONNECT.json` | Authoritative unconnected=80 |
| `reports/UNCONNECTED_AFTER_FINAL.csv` | Per-net open list |
| `docs/PM_STATUS.md` | PM snapshot; owns this checklist path |
| IPC-356 | **Missing** |
| Fab zip | **Missing** |

---

## Ranked fab blockers (for Hardware PM)

1. **Connectivity hard gate** — `unconnected_items=80` (`reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`, `reports/UNCONNECTED_AFTER_FINAL.csv`).
2. **Fab outputs not current** — Gerbers/drill CreationDate 2026-09-16 IST; FINAL_FAB_RELEASE says not regenerated; live PCB progressed (250 vias / 777 segments).
3. **No IPC-356 / no fab zip** — exports absent under `fab/`.
4. **Drill/via rule breaks** — two 0.25 mm drills; DRC `drill_out_of_range`×2, `via_diameter`×2; 82 dangling vias (`DRC_AFTER_CONNECT.json`).
5. **Stackup / impedance** — **Decision locked** in `docs/FAB_STACKUP_NOTES.md` (4L; L1–L2 H~0.12 mm; ENIG; 50 Ω RF). Remaining: fab coupon / mid-stack proposal (not a design conflict).
6. **Silk / production cosmetics** — 147 silk_overlap + 36 silk_over_copper in AFTER_CONNECT DRC (acceptable only after copper freeze, still not release-clean).

**Gate remains RED.**


## C7 — JLC 4-layer filled-and-capped via-in-pad (VIPPO)

| | |
| --- | --- |
| **Status** | **OPEN** (overall gate stays **RED**) |
| **Evidence** | Scope: 18 filled+capped vias at `vippo` 729a1a3: 9 × 0.20/0.30 in U1 pads 52–60, plus 9 × 0.30/0.60 GND thermal vias in U1 GND pads. Details in `reports/DFM_VIPPO_NOTE.md` §1.4/C7. Capability evidenced: JLC POFV page lists 0.2/0.3, ring ≥0.05 mm, >0.45 mm from other holes, and "POFV for 4-layer PCBs still requires charges" (https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv). Epoxy-filled & capped is selectable by note/image or by drill diameter (https://jlcpcb.com/help/article/pcb-via-covering). **PENDING a live JLC quote:** (a) 8:1 aspect ratio for the 0.20 mm hole through 1.6 mm; (b) 4L POFV cost and lead time; (c) JLC accepts the no-protrusion order note (caps flush or recessed, ≤+25 µm proud). Plating is JLC standard (~18 µm) for the prototype, RF-accepted; production target is ≥20 µm. **Drill selection:** 286 of 336 vias are 0.30 mm drill, so option (b) was chosen. Group B moves to **0.25/0.40** (unique tool), **pending Layout change after pass30cm**. The PCB at 729a1a3 is still 0.30/0.60. |
| **To go green** | Layout changes group B to 0.25/0.40 after pass30cm (keep all 9). Get a live JLC quote (4L, 1.6 mm, ENIG, Epoxy Filled & Capped) with cost/lead recorded, and get EQ acceptance of 0.2/0.3 at 8:1 and of the no-protrusion order note. |
