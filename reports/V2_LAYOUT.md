# nRF9161 v2 simplified UART module — layout report

Branch `v2` (local only, not pushed). Schematic is unchanged since 0dc7f09 (ERC 0); no layout step required a schematic change.

## Commits
| SHA | Step |
|---|---|
| 6647397 | layout 1: schematic → PCB sync |
| 6a9c2ba | layout 2: 50×34 mm outline, two-sided placement, B1–B5 rule areas, In1 no-track rule area, RF feeds |
| 0db476f | layout 3: bottom re-placed, VDD_nRF In2 vias, RF fence vias |
| ea1c4b0 | layout 4: all nets routed; SIM ESD block (U4, C33, C35–C38) moved below J7; GND islands stitched |
| 8e3a7af | layout 5: silk 1.0 mm / 0.15 mm, J20 pin names |
| 15f3937 | layout 6: VDD_GPIO re-routed out of the RF corner (B5) |
| 18115d6 | layout 7: report + PNGs |
| e48662b | v2b-1: J7 SIM holder moved to TOP (NW corner); board grown 3.5 mm north to 50×37.5; SIM ESD block follows under J7 on the bottom |
| b42e8c1 | v2b-2: VDD_GPIO re-routed at 0.3 mm, POWER clearance 0.15 (141 mm / 16 vias, was 148 mm at 0.25) |
| 2c60fd8 | v2b-3: GNSS fence side− 75.6 → 100 %, J5 3 GND vias |
| 6645a01 | v2b-4: report + PNGs |
| fa510f8 | v2c-1 (F1): U4 ESD return vias |
| 8d983e6 | v2c-2 (F2): VDD1/VDD2 widened to 0.5 mm where there is room |
| 22c85d2 | v2c-3 (F3): README antenna note |
| (this commit) | v2c report + PNGs |

## Board
- 50 × 37.5 mm (grew 3.5 mm in Y only for J7 on top), 4-layer (F / In1 solid GND / In2 VDD_nRF + GND / B). U1 uses the DK footprint with VIPPO; there are no new drill sizes (0.2 and 0.25 VIPPO, 0.3 standard).
- **A panel is needed.** JLC Standard double-sided PCBA needs ≥70×70 mm. Plan a 2×2 panel (100 × 68 + 5 mm rails, so ≥70 mm per side) or 1×2 with rails.
- J20 (1×10 2.54) sits on the east short edge. SWD J8 is on top at the north edge and reachable.

## Part counts
| Side | All | Assembled (no TPs) |
|---|---|---|
| Top | 52 | 44 |
| Bottom | 32 | 23 |

The bottom is lighter (23 vs 44 assembled). J7 SIM holder is now on top. Bottom parts: U4 SIM ESD with C33–C38, level shifters U5–U8 with C41–C48, U2 / Q1 / R21 / R23, JP2 and test points.

## Gate
- **DRC:** 0 violations and unconnected 0 (kicad-cli 9.0.2, zones refilled).
  - The only reported item is `lib_footprint_issues` (84). It is environment-only: the stock KiCad libraries are not installed on the build box. It is not a design issue.
- **Silk:** silk_overlap 0, silk_over_copper 0, silk_edge 0.
  - Refs are 1.0 mm / 0.15 mm.
  - 29 refs on crowded passives/TPs are hidden rather than shrunk: D2, Q1, TP8/13/17, FB4, R10, R21, L2, C2, C5, C6, C9, C10, C12, C13, C22–C24, C27–C32, C35, C36, C39, C43.
  - J20 pin names VIN GND VIO TX RX RTS CTS DTR RI nRST are on silk. Every pin is labelled on at least one side: 1–4 both, 5–7 bottom, 8–10 top.

## RF gates (V2_RF_RULES.md)
| Gate | Result | Numbers |
|---|---|---|
| G1 placement | PASS | All RF section on top. Bottom parts in RF zones: 0. Nearest bottom part to an RF pad/feed is 8.66 mm. Rule areas B1–B5 present. |
| G2 In1 | PASS | 0 non-GND tracks/zones. 1 piece, 1706 mm². 100% under the feeds. |
| G3 feeds | PASS | 0.20 mm on F.Cu with 0 RF vias. ANT 9.03 mm, GNSS 9.03 mm, AUX 6.35 mm. L4 stub 1.0 mm. All π footprints present. Fence (% of feed within 1.5 mm of a fence via): ANT 100/100, AUX 100/100, GNSS 98.7 / 100 (≤3 mm pitch; 0.6/0.3 vias, not in pads, ≥0.85 mm from feed centre). The only non-RF net in the RF corner is GNSS_VBIAS (the bias-T, intended). |
| G4 under U1 | PASS | 0 bottom parts and 0 non-GND bottom tracks in B1. B.Cu GND 100% under U1. U1 vias 0.2/GND ×7, 0.25/GND ×9. |
| G5 power | PASS | In2 VDD_nRF is 1 piece (1574 mm²). 14 VDD_nRF vias, 4 within 3 mm of FB4. Decoupling caps 1.9–2.5 mm from pins (C4 and C8 bulk at 3.58 mm). |
| G6 GNSS | PASS | Bias path C28/C29/C30/FB5/L4 present. J2 and J5 each have 3 GND vias within 1.5 mm of their GND pads. |
| G7 DRC | PASS | See Gate above. |
| G8 RF review sign-off | OPEN | Needs human RF review. |

**B6 is n/a.** B6 covers the on-board antenna keepout. v2 has no on-board antenna: LTE and GNSS use external antennas via the J2 / J5 U.FL connectors, so there is no antenna clearance region to keep out.

## Notes and conflicts
- **SIM holder on top (DFM conflict resolved).** J7 moved to the top NW corner (rot 270); the board grew 3.5 mm in Y only. RF keepouts unchanged. All vias are tented board-wide (`tenting front back`), including those under J7.
- **SIM ESD block.** U4 with C33–C38 sits on the bottom under the west part of J7, outside the keepouts. The ESD caps were reordered and rotated so their GND pads share a strip, and 1V8 reaches U4.5 via a short F.Cu jumper.
- **VDD_GPIO.** Re-routed at 0.3 mm with POWER clearance (141 mm, 16 vias; was 148 mm at 0.25). A direct 0.4 mm route (≈91 mm) was achieved, but the dense south HOST/level-shifter strip could then not be re-routed (P0.31, HOST_CTS/RTS/TX stayed open). Getting to 0.4 mm and a direct route needs that strip re-placed. The north↔south link (C11 → U7) is still about 46 mm.
- **Narrow ground pour gaps.** Zone clearance is 0.15 mm and minimum width 0.15 mm, and orphan islands are removed.

## RF review (V2_RF_REVIEW.md: FAB-OK WITH NOTES) — v2c actions
- **F1 (done).**
  - The U4 EP (21.5, 19.5) now has 2 extra GND vias at (21.5, 18.95) and (21.5, 20.05). They use the existing 0.3/0.2 via size, are tented and are not in pads. Each via centre is 0.55 mm from the EP centre and 0.2 mm from the EP edge (the via ring clears the pad edge by 0.05 mm). A via centre within 0.5 mm of the EP centre would have to sit inside the pad.
  - The EP is tied to these vias and to the existing (21.5, 18.0) via with a 0.3 mm B.Cu track.
  - C37.2 has a new 0.3/0.2 GND via at (18.78, 19.45), 0.25 mm from the pad edge.
  - C33.2 has a new 0.3/0.2 GND via at (22.78, 22.40), 0.71 mm from the pad edge. That is the closest legal spot given the SIM_1V8 POWER clearance and the 0.25 mm hole clearance.
- **F2 (done where there is room).** VDD1/VDD2 widened from 0.25 to 0.5 mm:

  | Net | Widened to 0.5 mm | Left at 0.25 mm |
  |---|---|---|
  | VDD1 | 11.8 mm | 3.4 mm |
  | VDD2 | 4.3 mm | 8.3 mm |
  | Total | 16.1 mm | 11.7 mm |

  The narrow VDD2 runs are on F.Cu: (43.25, 27.0)→(45.74, 25.48), plus (46.25, 22.6)→(50.08, 21.59) near FB3. Neighbouring copper blocks 0.5 mm there.
- **F3 (done).** README has the antenna note: LTE uses a sleeve or flex dipole (ground-independent, not a monopole stick); GNSS uses an active patch with its own ground plate.
- **N1.** gates.py reports the minimum fence-via-to-trace figure as 0.1 mm; that is a script artefact. RF measured 0.519 mm.
- VDD_GPIO at 0.3 mm / 141 mm is accepted as is. The direct 0.4 mm route is F4, for the next spin.

## Images
- Top: `reports/v2_layout_top.png`
- Bottom (mirrored view): `reports/v2_layout_bottom.png`
