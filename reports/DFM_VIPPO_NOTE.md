# DFM note — VIPPO for U1 trapped pads + `autoroute-gpio` (3e2a15f) review

Author: Fab/DFM agent · 2026-10-12 IST · Opinion only: no design edits, nothing committed.
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
```
VIA-IN-PAD: Vias with FINISHED HOLE 0.20 mm (drill tool T<n>, the only 0.20 mm tool in the
NC drill file; 4 places, located in U1 pads 49/54/59/96, nets SIM_1V8, MAGPIO1, MIPI_SDATA,
P0.01) SHALL be IPC-4761 TYPE VII: filled with NON-CONDUCTIVE epoxy, planarized, and
copper plated over (capped) on both sides, then ENIG finished.
Cap copper thickness >= 12 um (IPC-6012 Class 2 min for capped vias, wrap plating per IPC-6012).
Planarity: dimple/protrusion <= 25 um (0.025 mm) relative to surrounding pad surface.
No voids exposed at surface; no visible hole outline after ENIG.
All other vias: tented both sides (no fill) unless fab requires global fill — in that case
fill+cap ALL vias Type VII; notify before production.
Reference layer: see Fab drawing layer "User.Comments" VIPPO markers (4 places).
Stackup per docs/FAB_STACKUP_NOTES.md (4L 1.6 mm, ENIG, 50 ohm SE coupon).
```
Marking approach: (a) unique 0.20 mm drill size, so the drill file tool table separates these 4 vias. (b) Draw a marker ring and a "VIPPO" label for each one on a User/Fab layer that is exported with the Gerbers. (c) Put the same text in the order remarks. A 0.20 mm drill also raises the JLC drill-size price tier (≤0.25 mm hole with land <0.45 mm costs more [J2]). Note: the 12 µm cap and 25 µm dimple figures are my proposed spec, typical of industry practice. They are not taken from these fabs' pages, so confirm them in the fab EQ.

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
