# FAB READY CHECKLIST — nRF9161-DEV-BOARD

**Working path:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Checklist date:** 2026-09-23 (IST / Asia/Calcutta)  
**Overall gate:** **RED — NOT FABRICATION-READY**

Do not declare fab-ready until **every** row below is PASS **and** `unconnected_items = 0`.  
Authoritative connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items` (see `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`).

---

## Overall gate

| Field | Value |
| --- | --- |
| Status | **RED / FAIL** |
| unconnected_items | **80** (need 0) — `reports/DRC_AFTER_CONNECT.json` date `2026-09-18T02:01:29+05:30`; `reports/FINAL_FAB_RELEASE.md`; `reports/UNCONNECTED_AFTER_FINAL.csv` (80 data rows) |
| shorting_items / clearance / hole_clearance (last fab-release narrative) | 0 / 0 / 0 per `FINAL_FAB_RELEASE.md` |
| Gerbers regenerated after last connectivity pass | **No** — `FINAL_FAB_RELEASE.md` states fabrication outputs were **not** generated; on-disk `fab/gerbers` CreationDate is older (2026-09-16) |
| Checklist fully green | **No** |

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
| **To go green** | Keep notes current after freeze; attach to EMS kit with BOM DNP list and RF keepout photo/PDF (`fab/nRF9161-DEV-BOARD-sch.pdf`, PCB PDF under `fab/`). |

---

## 8. Final DRC / ERC / unconnected-items gate

| | |
| --- | --- |
| **Status** | **FAIL** |
| **Evidence** | **Unconnected = 80** — `reports/FINAL_FAB_RELEASE.md` (hard gate failed); `reports/DRC_AFTER_CONNECT.json` (`unconnected_items` length 80, date 2026-09-18 IST); `reports/UNCONNECTED_AFTER_FINAL.csv` (80 rows). Classes summarized in FINAL_FAB_RELEASE (A55/F6/G7/C3/E9). Additional DRC in same JSON: silk_overlap 147, via_dangling 82, silk_over_copper 36, track_dangling 13, lib_footprint_mismatch 3, via_diameter 2, drill_out_of_range 2. Older `reports/DRC_SUMMARY.txt` / README cite 116 unconnected — superseded by AFTER_CONNECT/FINAL_FAB (80). ERC: `reports/ERC_kicad-cli.rpt` (2026-09-16) **0 errors, 1 warning** (lib_symbol_mismatch U4); root `nRF9161-DEV-BOARD-erc.rpt` older with dangling global-label warnings. |
| **To go green** | Route/repair until `unconnected_items=0` and ratsnest=0; clear or waive remaining DRC with documented severity; re-run ERC clean for release; only then regenerate fab outputs. |

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
