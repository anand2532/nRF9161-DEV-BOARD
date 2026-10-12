# RF review: pass30ck/pass30cl (branch `vippo`, 1f84f25 + 729a1a3, base `finish` 9d14ed5)

**Verdict: MERGE WITH FIXES.** The branch adds no RF regression. The fixes listed below are for the next pass (FX1 blocks fab, not this merge).

Method: read-only. I extracted both commits with `git show` to /tmp, refilled all zones in pcbnew 9.0.2 and ran kicad-cli DRC with the .kicad_pro plus the new .kicad_dru. Geometry was measured from the filled polygons. Nothing in the repo was edited apart from this file.

## 1. J14 and length gate (G3): MET
J14 moved from (104, 48) r0 to **(26.5, 14.35) r180**, on F.Cu, north-west of U1 and outside the keepout.

| Net | Length | Layer | Vias | Target | Result |
|---|---|---|---|---|---|
| MIPI_SCLK | 24.4 mm | B.Cu | 1 (VIPPO) | ≤50 | PASS |
| MIPI_SDATA | 26.9 mm | B.Cu | 1 | ≤50 | PASS |
| MIPI_VIO | 22.0 mm | B.Cu | 1 | ≤60 | PASS |
| MAGPIO0 | 18.1 mm | B.Cu | 1 | ≤80 | PASS |
| MAGPIO1 | 18.9 mm | B.Cu | 1 | ≤80 | PASS |
| MAGPIO2 | 19.7 mm | B.Cu | 1 | ≤80 | PASS |

The series-R option is no longer needed.

DRC (refilled):

| Check | 9d14ed5 | 729a1a3 |
|---|---|---|
| Errors (short, clearance, hole, edge) | 0 | 0 |
| track_dangling | 4 | 4 (pre-existing: 3 × VDD_GPIO, 1 × P0.11) |
| lib_footprint_issues | 101 | 102 (library not installed; not a real issue) |
| Unconnected | 23 | **17** |

The 17 are 6 signal opens (P0.12, P0.14, P0.18, P0.25, P0.31, SIM_IO) plus 11 GND zone islands.

## 2. (a) C1 In1 slots: ACCEPT (waiver W1)
Measured In1 voids after refill. The rest of the box x 27–29.6 / y 26.8–35.2 has none.

| Void | x | y | Size | Orientation |
|---|---|---|---|---|
| Pads 53–55 | 27.75–28.15 | 27.30–28.70 | 0.40 × 1.40 mm, 0.42 mm² | N–S |
| Pads 57–59 | 27.75–28.15 | 29.30–30.70 | 0.40 × 1.40 mm, 0.42 mm² | N–S |

- **Distances, 57–59 slot:** 0.65 mm to the pad 61 projection (edge y 31.35). 0.70 mm to the ANT feed edge, so 0.34 mm outside its 3H return window. 2.2 mm to AUX/pad 64 and 3.7 mm to GPS/pad 67. 5.3 mm to the ANT vertical at x 22.485.
- **Distances, 53–55 slot:** ≥2.7 mm to ANT.
- **Feeds are not interrupted.** Neither slot crosses or lies between a feed and its return. The In1 coverage scan under ANT/AUX/GPS (±0.36 mm) is identical before and after the change, so the slots add zero uncovered samples.
- **No resonance.** 1.4 mm is about λ/70 at 1.6 GHz. GND barrels 52/56/60 sit at both ends and in the middle of each pair, so each slot is closed at both ends.
- **MIPI/MAGPIO return path:** fine. RFFE/GPIO edges are slow (tens of MHz). Each signal barrel has a GND barrel ≤0.5 mm away to carry the return between layers. The B.Cu escapes reference In2 and never cross the slots.
- **Fixes considered:**
  - Stagger: not possible (VDD_GPIO B.Cu at x 28.5).
  - Drop the In1 GND zone min_thickness 0.20 → 0.10 so the webs survive: works geometrically, but it is board-wide and gives 0.10 mm inner webs at the JLC limit.
  - 0.15 mm drill: not on the JLC POFV table.
- **Recommendation:** accept as is (W1). Do not change the zone min width.

## 3. (b) C3 GND vias: MET for RF
- **In-pad GND VIPPO** (0.20/0.30, connected on all layers) at (27.95, 27.0) pad 52, (27.95, 29.0) pad 56 and **(27.95, 31.0) pad 60 (mandatory): present.** Pad 60 fences pad 59 from ANT pad 61.
- **Extra via near the cluster is missing.** The nearest GND vias outside the pads are (30.0, 29.0), (30.0, 32.0) and (25.98, 34.0).
- The in-pad GND VIPPO alone is sufficient: every signal barrel has a GND barrel within 0.5 mm.
- The extra via does not need to sit in the keepout. The bundle leaves the keepout at y < 26, so a GND via there is outside it. That is optional fix FX3.

## 4. (c) P0.02 north branch: ACCEPT
- **Route:** B.Cu only, 0.18 mm. Via at (27.5, 40.5) → (27.5, 36.5) → jog west at y 36.5 → x 24.6 north to y 5.4 → (25.5, 4.5). The F.Cu portion (x 27.5, y 40.5–45) and the U3-side copper are unchanged from base. Total length 192.8 → 198.0 mm.
- **Keepout:** none of it is on F.Cu or In1 inside x ≤ 29 / y 26–40. The B.Cu portion is outside the keepout layer set.
- **Crossings:** it crosses ANT (y ≈ 31.7), AUX (y 33) and GPS (y ≈ 34.7) at right angles, with solid In1 GND between. Overlap within 0.5 mm in plan view: 1.4 / 2.3 / 1.4 mm. That is the crossing width, plus a 1.0 mm run beside the AUX→C23 stub at x 24.32 (0.09 mm in plan view, through In1).
- **Distances:**

| To | Distance |
|---|---|
| Pad 61 / 64 / 67 | 3.65 / 3.58 / 2.14 mm |
| C21 / L1 / L2 / C27 / C22 / C24 | 3.7 / 1.7 / 3.7 / 2.0 / 6.7 / 8.7 mm |
| C23 (DNP shunt) | overlaps in plan view through In1 |

- **Compared with base:** the old run at x 27.5 sat 0.75 mm from pad 61, so this is an improvement.
- **Watch item:** In1 directly above x 24.6 is covered, but the inherited P0.00 In1 void (see FX1) starts only about 0.16 mm east of it.

## 5. F3: DONE
- **No-pour area:** `pass30ck_sliver_noFill` is a B.Cu-only rule area, copperpour not allowed, at x 27.7–28.25 / y 19.0–39.75 (about 11.4 mm²).
  - It removed the 0.23 mm unstitchable B.Cu sliver.
  - It does not touch In1, which carries the RF reference, or F.Cu, so no ground was removed under the feeds or the matching network. No In1 slot was created.
- **North block:** now x 24.94–33.86 / y 4.84–18.71, 90.0 mm², stitched at (30, 10), (28.5, 10), (33.5, 10), (30.5, 5.6), (30.5, 14.3) and (30.5, 16.7). OK.
- **New small B.Cu GND piece:** x 24.94–27.70 / y 30.84–36.17, 14.7 mm², formed in the freed channel. It has a single stitch via at (25.98, 34.0). It is not floating, and it is 5.3 mm long, far below resonance. A second via is optional (FX4).
- B.Cu GND pieces: 21 → 22. The GND island count is unchanged at 11.

## 6. Standard gates
| Gate | Result |
|---|---|
| In1 GND | 2 pieces, 8142.6 → 8142.1 mm² |
| In1 track count | 72 → 72 (no new In1 copper) |
| C4 | PASS |
| In2 VDD_nRF | 1 piece, 6801.7 → 6780.3 mm². 0.00 mm² removed in x 50–62, so the neck is unchanged at 3.18 mm (≥2) |
| Protected RF | ANT/ANT_FIT/AUX/AUX_FIT/GPS/GNSS_* tracks and vias identical (hash). C21–C24, L1, L2, TP1, U3, C27, L4, FB5 identical. **PASS** |
| SIM spacing | Closest new copper to SIM is the C40 GND via (CK) to SIM_1V8 on B.Cu, 0.35 mm. That is GND, inside the y ≥ 24 fan-out zone. No new signal near SIM. PASS |
| C2 | Escapes at x 25.05–27.96, y 8.0–30.5. Nothing west of 23.5 or south of 30.5. PASS |
| C5 | New copper in the keepout (F.Cu/In1) is only the VIPPO barrels in pads 52–60, with GND 52/56/60 added to the documented 53–59 exception. PASS |
| C7 | DFM/JLC POFV confirmation still open |

**Correction to the CG/CJ reviews (inherited, present since main 8628f07):**
- **P0.00 on In1:** runs x 25.2, y 23.5–37.4 and then east along y 37.4. That puts it inside the keepout. It cuts an In1 void about 0.7 mm wide straight across the return path of all three feeds, at ANT (25.4, 31.7), AUX (25.4, 33.0) and GPS (25.4, 34.7). The CG review said this copper was outside the keepout, which was wrong.
- **COEX0 on F.Cu:** (26.2, 38) → (33, 38) is also inside the keepout. It is ≥3 mm from the feeds, so its impact is low.

## 7. Fix list
- **FX1 (fab-blocking, inherited):** move P0.00 off In1 in the RF corner. Re-route it on B.Cu east of x 29, or north of y 26, so In1 is solid under ANT/AUX/GPS. Re-run the In1 feed-coverage check; it should show 0 uncovered samples.
- **FX2 (non-blocking):** COEX0 F.Cu at y 38, x 26.2–29: move it to x ≥ 29 or y ≥ 40 when convenient.
- **FX3 (optional):** add one 0.5/0.3 GND via near the escape bundle outside the keepout, for example around (27.6, 23) between MAGPIO2 (x 26.7) and VDD_GPIO (x 28.5). Check it with DRC on all layers.
- **FX4 (optional):** add a second GND via in the 14.7 mm² B.Cu piece, for example around (26.8, 35.6), with DRC.
- **W1:** waive the C1 web loss (two 0.4 × 1.4 mm In1 slots). Do not change the zone min width.
- **Docs:** update the C5 exception text to "via barrels in pads 52–60" and DFM_VIPPO_NOTE §1.4 to 9 vias.

## Fab gates (NOT fab-ready)
- **G1:** 17 unconnected: P0.12, P0.14, P0.18, P0.25, P0.31, SIM_IO, plus 11 GND F.Cu islands.
- **G2:** FX1 done and re-reviewed.
- **G3:** length gate met (closed).
- **G4:** DFM POFV sign-off (C7) and cost.
- No Gerbers until unconnected = 0.
