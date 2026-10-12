# DFM note — VIPPO for U1 trapped pads + `autoroute-gpio` (3e2a15f) review

Author: Fab/DFM agent · 2026-10-12 IST · Opinion only: no design edits. §1.4/C7 updated and committed on `vippo` for 729a1a3.
Inputs: `nRF9161-DEV-BOARD.kicad_pcb` at 3e2a15f (= current HEAD of the shared working copy, branch `autoroute-gpio`) and at `main` (8628f07). Both were extracted with `git show` into /tmp, and DRC was run there with `kicad-cli pcb drc` (zones not refilled). Context: `docs/FAB_STACKUP_NOTES.md` (LOCKED), `docs/FAB_READY_CHECKLIST.md` (gate RED).

## Part 1 — VIPPO for U1 MAGPIO1 / MIPI_SDATA / P0.01 / SIM_1V8

### 1.1 Measured geometry (3e2a15f)
U1 footprint `Board:nRF9161_LGA_16.0x10.5mm`, placed at (36, 32), rotated 180°. Pad sizes in the footprint: 0.8×0.3 (35), 0.3×0.8 (58), 0.8×0.8 (31), 0.3×0.3 (3), 1.6×0.8 (2).

| Pad | Net | Pad size (mm) | Board pos | Via in/at pad today | Current open (DRC) |
|---|---|---|---|---|---|
| 49 | SIM_1V8 | 0.30×0.80 | 29.75, 26.75 | none | pad 49 ↔ track stub @75.6,44.1 |
| 54 | MAGPIO1 | 0.80×0.30 | 28.00, 28.00 | none (2.4 mm F.Cu stub from pad; nearest via 25.6,23.1) | stub ↔ J14.2 |
| 59 | MIPI_SDATA | 0.80×0.30 | 28.00, 30.50 | none, net has 0 tracks | pad 59 ↔ J14.6 |
| 96 | P0.01 | 0.30×0.80 | 40.25, 37.25 | none | pad 96 ↔ track @62,74.5 |

**These 4 pads are exactly the 4 non-GND unconnected items left at 3e2a15f** (the other 15 are GND F.Cu zone islands). **No via-in-pad exists yet.** Layout has to place them, so the via geometry below is a requirement on Layout.
Board via stock today: 0.6/0.3 (262), 0.5/0.3 (81), 0.8/0.4 (59). There is no 0.20 mm drill on the board, so a 0.20 mm VIPPO drill would be a unique tool (see 1.4).

**Fit check:** the limiting dimension is the 0.30 mm pad width. Any via land wider than 0.30 mm overhangs the LGA pad, which breaks the mask/paste definition and narrows the gap to the neighbour pad. The existing 0.5/0.3 and 0.6/0.3 vias **cannot** go in these pads.

### 1.2 Fab availability / minimums (public pages, fetched 2026-10-12)
| Item | JLCPCB | PCBWay |
|---|---|---|
| Epoxy filled & capped (IPC-4761 VII) on 4L 1.6 mm ENIG | Yes. "POFV for 4-layer PCBs still requires charges" (free only on 6L+) [J1][J3] | Yes, "Filled & Capped Via", IPC 4761 Type VII, epoxy resin [P1][P2] |
| VIPPO via sizes | Hole 0.2–0.5 mm; pairs 0.2/0.3, 0.2/0.35, 0.25/0.4, 0.3/0.4, 0.3/0.45; annular ≥0.05 mm (0.075 preferred); place >0.45 mm from regular vias [J1]. Capabilities page: process compatible with 0.15–0.55 mm vias; default on 6L+ [J2] | Min annular ring 0.15 mm, "for pads with vias in the middle" too; CNC finished hole 0.15–6.0 mm; <0.2 mm extra charge [P3] |
| Smallest that fits a 0.30 mm wide pad | **0.20 drill / 0.30 land**: annular 0.05 mm = fab minimum, land = pad width, zero margin | **Does not fit by their published rule.** 0.15 drill + 2×0.15 ring = 0.45 mm > 0.30 mm pad. Needs engineering waiver: unverified |
| Whole board vs per via | Order remark specifies the plugging-hole **diameter** [J4], so selection is effectively by drill size, not by individual via coordinate. Treat it as by-drill-size, not per via | Page says that when the customer requires all through-holes filled, SMD vias are also defined as VIP [P2]. Per-via selection by drill size is not documented: unverified |
| Cost adder (4L) | **Unverified.** JLC says 4L is charged but publishes no figure | **Unverified.** Only "higher production cost" [P2] |
| Lead-time adder | **Unverified** | **Unverified.** Only "longer production time" [P2]. Standard quick-turn lead times exist [P4], but no VIPPO adder is published |

Get real cost and lead numbers from an online quote: JLC with "Epoxy Filled & Capped" selected, PCBWay Advanced PCB with "Via in pad" selected. Do not put estimates in the package.

**Consequence if the fab applies it to the whole board:** all 402 vias get filled and capped. Expect a higher cost, an extra cap-plating cycle (more surface copper, so check fine features against the 0.18 mm tracks), and no exposed via test points. Fully filled vias are electrically harmless here and help with paste/voiding under the RF can and ground pad. **Recommendation:** make the 4 VIPPO vias a unique drill (0.20 mm), so the fab can apply the process to that one tool and leave the rest tented. Accept whole-board fill as the fallback and price it.

### 1.3 Feasibility verdict
- **JLCPCB:** feasible but at the edge of their rules: 0.20/0.30 POFV, annular exactly 0.05 mm minimum, 0.20 mm hole in 1.6 mm board (8:1 aspect). Each via must also be >0.45 mm from regular vias (per [J1]). Layout must check that against nearby escape vias. **Conditionally OK, pending Layout confirmation of clearance + JLC EQ acceptance.**
- **PCBWay:** **not OK by published rules** (0.15 mm ring minimum). Only with written engineering approval.
- The neighbour-pad gap stays the footprint gap, because the land sits inside the pad. LGA solder joint: a capped via under a 0.3×0.8 pad is the standard VIPPO use case. A dimple will reduce solder volume, so a planarity spec is needed (below).

### 1.4 Fab-note text (paste into fab drawing / order remarks)

**Updated 2026-10-12 for `vippo` @ 729a1a3 (PASS30CL). Scope per Hardware PM decision: 18 filled-and-capped vias = 9 × 0.20/0.30 in pads 52–60 (table A) + 9 GND thermal vias in U1 GND pads (table B), decided target **0.25/0.40** (option (b), Hardware PM + RF approved 2026-10-12). **Group B 0.25/0.40 is pending a Layout change after pass30cm; the current PCB at 729a1a3 still has 0.30/0.60.** Table A: Verified from the `.kicad_pcb` at 729a1a3 (pcbnew API, file extracted with `git show` into /tmp):

| U1 pad | Net | Pad (mm) | Via centre (mm) | Drill / land (mm) |
|---|---|---|---|---|
| 52 | GND | 0.80×0.30 | 27.95, 27.00 | 0.20 / 0.30 |
| 53 | MAGPIO2 | 0.80×0.30 | 27.95, 27.50 | 0.20 / 0.30 |
| 54 | MAGPIO1 | 0.80×0.30 | 27.95, 28.00 | 0.20 / 0.30 |
| 55 | MAGPIO0 | 0.80×0.30 | 27.95, 28.50 | 0.20 / 0.30 |
| 56 | GND | 0.80×0.30 | 27.95, 29.00 | 0.20 / 0.30 |
| 57 | MIPI_VIO | 0.80×0.30 | 27.95, 29.50 | 0.20 / 0.30 |
| 58 | MIPI_SCLK | 0.80×0.30 | 27.95, 30.00 | 0.20 / 0.30 |
| 59 | MIPI_SDATA | 0.80×0.30 | 27.95, 30.50 | 0.20 / 0.30 |
| 60 | GND | 0.80×0.30 | 27.95, 31.00 | 0.20 / 0.30 |

- Geometry: these are the only 0.20 mm drills on the board (all other vias 0.3/0.4 drill), so selection by tool works. Annular ring is 0.05 mm (JLC POFV minimum [J1]). The land equals the 0.30 mm pad width (zero margin, does not overhang). It is offset 0.05 mm along the 0.80 mm pad length, so it stays inside the pad.
- Spacing: the VIPPO pitch is 0.50 mm (0.20 mm land-to-land, 0.30 mm hole-to-hole edge). The nearest regular via is 2.35 mm edge-to-edge (SIM_1V8 0.5/0.3 via from pad 52), so it meets JLC's >0.45 mm rule [J1].
- Earlier trapped pads: 54 MAGPIO1 and 59 MIPI_SDATA are now VIPPO. **49 SIM_1V8 and 96 P0.01 have no via-in-pad and are no longer reported as unconnected** in `reports/DRC_PASS30CL_AFTER.json` (C40/SIM_1V8 rework in PASS30CK). That file has 17 unconnected: 11 GND islands plus P0.12, P0.14, P0.18, P0.25, P0.31 and SIM_IO.


Table B: GND thermal vias in U1 0.80×0.80 GND pads (footprint pad "103"). **Hardware PM decision: fill + cap, do not move** (they carry U1's thermal path and ground return). **Decided target drill/land: 0.25/0.40 (option (b)). PENDING Layout change after pass30cm; the "current" column below is the PCB at 729a1a3.**

| # | Pad | Net | Via centre (mm) | Current drill/land @729a1a3 → target (mm) | Nearest non-filled via (Cu edge) |
|---|---|---|---|---|---|
| 1 | 103 | GND | 30.00, 29.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 2 | 103 | GND | 30.00, 32.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 3 | 103 | GND | 30.00, 35.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 4 | 103 | GND | 36.00, 29.00 | 0.30/0.60 → **0.25/0.40** | 1.20 mm (COEX0) |
| 5 | 103 | GND | 36.00, 32.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 6 | 103 | GND | 36.00, 35.00 | 0.30/0.60 → **0.25/0.40** | 1.20 mm (COEX0) |
| 7 | 103 | GND | 42.00, 29.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 8 | 103 | GND | 42.00, 32.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |
| 9 | 103 | GND | 42.00, 35.00 | 0.30/0.60 → **0.25/0.40** | 2.40 mm |

- The hole is 0.30 mm, inside JLC's POFV range of 0.2–0.5 mm, and the ring is 0.15 mm (≥0.05 min) [J1]. The 0.30/0.60 pair isn't in JLC's POFV size table, though (0.2/0.3, 0.2/0.35, 0.25/0.4, 0.3/0.4, 0.3/0.45) [J1]. Confirm in EQ. The pitch is 3.0 mm, and every via is ≥1.20 mm Cu-edge (≥1.50 mm hole-edge) from any non-filled via, which meets JLC's >0.45 mm rule [J1].

**DFM consequence: drill-size selection.** Board via inventory at 729a1a3 is 336 vias: 0.6/0.3 ×220, 0.5/0.3 ×66, 0.8/0.4 ×41, 0.3/0.2 ×9. **286 vias are 0.30 mm drill**, and that includes these 9. Footprint pads don't use 0.30 mm holes. So the 9 GND-pad vias **cannot be singled out by drill size**.
- (a) **"Fill all 0.30 mm vias":** 286 vias get filled and capped, which is 277 more than needed. The cost and lead-time impact is **UNVERIFIED**, because JLC publishes no 4L POFV price. Side effects: extra cap plating over 0.18 mm track areas, and no open via test points.
- (b) **Unique drill for the 9:** Layout changes them to a size not used anywhere else, within JLC's POFV table. **0.25/0.40** is the only unused pair in that table. It keeps a 0.075 mm ring (JLC preferred) and fits easily in a 0.80 mm pad, but it gives less thermal barrel than 0.30. Alternatively, put them on the existing 0.20 mm filled tool (0.20/0.35). That needs no new tool but gives even less thermal barrel. Spacing to non-filled vias stays ≥1.2 mm, so it passes the 0.45 mm rule either way.
- (c) **Select per via by note/image:** JLC's via-covering page allows "leave a note or upload an image... to explain which vias need to be filled" as an alternative to filling all of one diameter [J4]. This keeps 0.30/0.60 with no PCB change, but it relies on manual CAM selection, so the risk of a fab error is higher.
- **DECISION (2026-10-12): option (b) chosen.** Group B → 0.25/0.40 on its own 0.25 mm drill tool. Layout makes the change after pass30cm.
- **RF approval conditions (from RF, via Hardware PM):** (1) keep all 9 GND vias (no reduction in count); (2) hole-wall plating, (3) cap planarity (U1 is an LGA). **Revised 2026-10-12: RF accepts JLC standard for the prototype (no advanced / IPC Class 3 order).** Prototype values: plating = JLC standard (~18 µm average [J2]); caps: recess (dimple) ≤50 µm acceptable, protrusion ≤+25 µm. **Production target** (revisit for production): plating ≥20 µm average (IPC-6012 Class 2), 25 µm preferred. The earlier ±15 µm cap requirement is superseded.
- After the change, spacing still holds: the via centres don't move and the land shrinks 0.60 → 0.40, so the Cu-edge gap to non-filled vias grows to ≥1.30 mm (>0.45 mm [J1]).
- Original recommendation (kept for record): (b) with **0.25/0.40** on its own drill tool, plus a VIPPO-layer marker and order note. This gives deterministic selection by tool, uses a pair from JLC's published table, and fills only 18 vias. Fallback is (c) with an image and an EQ confirmation. Avoid (a) unless the quote shows a negligible adder. **No PCB change was made; this is a Layout decision.** If (b) is adopted, re-check that thermal performance is acceptable (RF/Power).

```
VIA-IN-PAD / FILLED & CAPPED: 18 places, all IPC-4761 TYPE VII (NON-CONDUCTIVE epoxy fill,
planarized, copper capped both sides, then ENIG):
 Group A: 9 vias, FINISHED HOLE 0.20 mm / land 0.30 mm (the only 0.20 mm drill tool), U1 pads
   52-60: GND (52,56,60), MAGPIO2 (53), MAGPIO1 (54), MAGPIO0 (55), MIPI_VIO (57),
   MIPI_SCLK (58), MIPI_SDATA (59).
 Group B: 9 GND thermal vias in U1 0.8x0.8 GND pads at (30/36/42, 29/32/35) mm,
   FINISHED HOLE 0.25 mm / land 0.40 mm. The 0.25 mm drill tool is the only 0.25 mm tool
   and identifies group B.
Fill + cap ALL vias of the 0.20 mm and 0.25 mm drill tools; no other vias are filled.
Hole-wall copper plating: fab standard (prototype).
Caps: planarize FLUSH or SLIGHTLY RECESSED, NEVER PROUD. Recess (dimple) up to 50 um
acceptable; protrusion above surrounding pad surface not to exceed +25 um.
Cap copper: per fab POFV process, minimum 5 um (JLC published), continuous over fill.
No voids exposed at surface; no visible hole outline after ENIG.
All other vias: tented both sides (no fill). If fab requires global fill, notify before
production.
Reference layer: Fab drawing layer "VIPPO" (User.1) markers (18 places).
Stackup per docs/FAB_STACKUP_NOTES.md (4L 1.6 mm, ENIG, 50 ohm SE coupon).
NOTE: protrusion limit (+25 um) is tighter than fab standard (+/-50 um); confirm in EQ.
```
Marking approach: (a) a unique 0.20 mm drill size, so the drill file tool table separates group A (and group B if option (b) is adopted). (b) PASS30CL has a marker ring for each group A via on user layer "VIPPO" (User.1); export it with the Gerbers. (c) Put the same text in the order remarks. A 0.20 mm hole with a 0.30 mm land also adds JLC's small-via charge ("hole <0.3 mm and diameter ≤0.4 mm" [J5]). **Spec values: sources and history.** Current values are the prototype values above.
- History: my earlier 12 µm cap / 25 µm dimple proposal was withdrawn. RF's first conditions (plating ≥20–25 µm, cap ±15 µm) were superseded 2026-10-12, when RF accepted JLC standard for the prototype. The cap copper minimum of 5 µm is JLC's published filled-via figure [J4].

| Item | JLC published | Prototype requirement (RF-accepted) | Production target | Order note needed? |
|---|---|---|---|---|
| Hole-wall plating | "Average Hole Plating Thickness 18μm" [J2] | JLC standard (~18 µm avg) | ≥20 µm avg (25 µm preferred), revisit at production | No (proto) |
| Filled-via cap copper | "Hole surface copper thickness ≥ 5um" [J4] | JLC standard | — | No |
| Cap planarity | "depression and protrusion within 50um" [J4], i.e. ±50 µm | Recess ≤50 µm OK; **protrusion ≤+25 µm** | — | **Yes.** +25 µm is tighter than JLC's ±50 µm on the proud side, so the order note asks for flush or slightly recessed caps, never proud |

**Order-remark text (JLC):** "Epoxy filled & capped vias (0.20 mm and 0.25 mm drill tools only): please planarize caps flush or slightly recessed, never proud. Max protrusion +25 um; recess up to 50 um acceptable. Standard hole plating OK."

### 1.6 Assembly (U1 LGA)
- Stencil: **0.12 mm**, with U1 apertures per Nordic's recommended footprint / solder paste mask in the **nRF9161 Hardware Design Guidelines (nWP054), "Footprint and solder paste mask"**: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/footprint.html. That page gives the land pattern and mask openings only as figures (NSMD pads). **I didn't take aperture numbers from it; take apertures from that document.** Use the footprint from the nRF9161 DK PcbDoc, not pca10153.IntLib (Nordic DevZone: https://devzone.nordicsemi.com/f/nordic-q-a/114096/footprint-and-soldering-issues-with-nrf9161).
- **Flag for Hardware PM/RF:** Nordic's sibling nRF9151 guide (nWP056) recommends an **80–100 µm** stencil and paste reduction to ~70–85% of pad area (https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html). That is thinner than the chosen 0.12 mm. I didn't find a stencil-thickness value in the nRF9161 text. Confirm 0.12 mm with the assembler or the nWP054 PDF.
- **First-article X-ray of U1** covering pads 52–60 (group A) and the 9 GND-pad vias (group B). If any open is found or voiding exceeds 25%, the next spin gets a tighter spec (plating/planarity per production target, and/or tighter cap spec).

### C7 — JLC 4L POFV at 0.20/0.30 + cost: **OPEN / UNVERIFIED (cost)**
- Capability: **evidenced.** The JLC POFV page lists the 0.20 hole / 0.30 diameter pair, annular ≥0.05 mm, >0.45 mm from other holes, and states "POFV for 4-layer PCBs still requires charges", i.e. it is offered on 4L [J1]. The via-covering help page (updated Sep 09, 2026) offers "Epoxy-filled & Capped", selected by note or by drill diameter [J4]. Not published: 8:1 aspect acceptance specifically at 1.6 mm 4L. Confirm in EQ.
- Cost: **UNVERIFIED.** No public 4L POFV price was found ([J1], [J4], [J6], quote page [J5]). The 0.2/0.3 small-via surcharge exists, but its amount is not published [J5]. **A live JLC online quote is needed** (4L, 1.6 mm, ENIG, Epoxy Filled & Capped, min via 0.2/0.3). No numbers estimated.
- Scope is now 18 vias. Drill-selection issue for group B: see table B above.
- Also pending the quote: JLC accepts the no-protrusion order note (+25 µm max proud; recess ≤50 µm). Plating is JLC standard for the prototype (RF-accepted).
- Group B drill change (0.30/0.60 → 0.25/0.40) is pending Layout after pass30cm.
- C7 cannot be PASS until there is a quote.

### 1.5 Alternatives if VIPPO is rejected
1. **Re-escape on F.Cu between pads / via outside the courtyard:** best option if any channel exists. MAGPIO1 already has a 2.4 mm F.Cu stub out of pad 54, so its blocker is the route onward, not the pad. Check whether a 0.1 mm-clearance neck (min_clearance 0.1) can reach an outside via.
2. **Pin remap** to an unblocked U1 GPIO for P0.01 / MAGPIO1 / MIPI_SDATA, where the schematic allows it. SIM_1V8 is a fixed function, so no remap there. Pass30cb already did remaps, so this is an established path.
3. **Untented / plugged-only (IPC-4761 Type III/IV) via in pad:** **reject for LGA.** Solder wicks into the hole, giving open or starved joints and large voids. Plugged-only also leaves a dimple and outgassing. Not acceptable for a fine-pitch LGA.
4. **Microvia L1→L2 (HDI):** this would break the locked L1–L2 0.12 mm prepreg/RF stackup and push the board into HDI pricing. Not recommended.
5. **6-layer board:** POFV is free at JLC on 6L+ [J1][J3], but that throws away the LOCKED 4L stackup. Only consider it if 4L VIPPO is refused and options 1–2 fail.

**Recommendation:** first try alternatives 1 and 2 (no special process). Any pad still trapped after that gets JLC 4L epoxy filled & capped, 0.20/0.30, on a unique drill tool, with the note above. Get a real quote before committing. Do not use PCBWay for this feature without written approval.

### Sources
- [J1] https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv
- [J2] https://jlcpcb.com/capabilities/pcb-capabilities
- [J3] https://jlcpcb.com/resources/pcb-design
- [J4] https://jlcpcb.com/help/article/pcb-via-covering
- [J5] https://cart.jlcpcb.com/quote
- [J6] https://jlcpcb.com/blog/via-filling-guide
- [J7] https://jlcpcb.com/blog/mastering-pcb-plating
- [P1] https://www.pcbway.com/pcb_prototype/PCB_Via_Covering.html
- [P2] https://www.pcbway.com/pcb_prototype/PCB_Via_in_Pad.html (also helpcenter Via_in_Pad.html)
- [P3] https://www.pcbway.com/capabilities.html
- [P4] https://www.pcbway.com/quickturn-pcb-fabrication.html

## Part 2 — `autoroute-gpio` @ 3e2a15f vs `main` @ 8628f07

kicad-cli DRC (no zone refill), results in /tmp only:

| Metric | main 8628f07 | 3e2a15f |
|---|---|---|
| unconnected_items | 38 | **19** (4 = the U1 pads above, 15 = GND F.Cu islands) |
| vias | 337 | 402 (**+65, all 0.5/0.3**) |
| via_dangling | 61 | 50 |
| track_dangling | 13 | 13 |
| hole_to_hole | 1 (via P0.02) | 1 (same, pre-existing) |
| silk_overlap / silk_over_copper | 145 / 35 | 145 / 35 (unchanged) |
| new tracks | — | 359 segments: 355 × 0.18 mm, 4 × 0.3 mm; layers In1 180, F 82, B 63, In2 34 |

Fab minimums: new vias are 0.5/0.3 with a 0.10 mm annular ring. That meets JLC multilayer (hole 0.15/0.25 dia min, dia ≥ hole+0.1 [J2]) and the project rule (min_via_annular 0.1). It is **below PCBWay's published 0.15 mm ring minimum [P3]**, so a PCBWay order would need 0.6/0.3. Track 0.18 mm is fine at both. Via count: +65 adds no new drill size and has negligible cost impact.

**Top issues, needs changes:**
1. **Solid L2 GND broken under RF (stackup lock violation).** 180 new signal segments are on **In1.Cu, the L2 GND reference plane** (main had 72 In1 signal segments in total). Several run within 0.6 mm in XY of F.Cu RF microstrips: MIPI_VIO under AUX (2) / ANT (1) / GPS (1), P0.14 under GPS (2) / AUX (1). This directly violates FAB_STACKUP_NOTES RF caveat 2 (solid L2 under ANT/AUX/GNSS). Those segments must come off In1, or at least out of the RF corridor. Ideally keep In1 signal-free entirely, and add a keepout on In1 over the RF region so the autorouter can't do this again.
2. **New vias next to the GNSS/RF section:** MAGPIO0 via @25.66,38.14 is 0.55 mm from GNSS_VBIAS, P0.14 vias @25.66,42.43 (0.56 mm) and @26.16,35.64 (0.96 mm from GPS), MIPI_SCLK @26.70,39.85 (1.6 mm). Each via anti-pad cuts L2 next to the RF feed, so move them out of the GNSS corridor.
3. **4 U1 opens remain** (Part 1). The gate stays RED until they're resolved, and the 15 GND islands are a separate waive/refill issue.
4. **Leftover hygiene:** 50 dangling vias, 13 dangling tracks, 1 hole_to_hole (pre-existing). Clean up before Gerbers.
5. Silk counts are unchanged and remain a checklist item. Acid traps/slivers: no DRC hits (KiCad has no acid-angle check). Freerouting output is orthogonal/45° at 0.18 mm, so I see no obvious acute-angle risk, but I haven't inspected it visually. Re-check in the fab DFM viewer after Gerbers.

**Verdict: `autoroute-gpio` NEEDS CHANGES before fab.** It is a real connectivity improvement (38→19), but issue 1 breaks the locked RF reference plane. Fab gate remains RED.
