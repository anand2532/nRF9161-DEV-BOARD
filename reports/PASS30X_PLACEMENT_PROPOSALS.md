# Pass30x — Placement Proposals ONLY

**Generated:** 2026-09-23 18:43 IST  
**Board:** pass30u KEEP (pass30w no copper) · unconnected=67  
**Mode:** PROPOSALS ONLY — board untouched (no footprint moves, no copper, no Gerbers)  
**Hard gate:** unconnected → 0  

## PM / DFM override (this pass)

| Bucket | Items | Policy |
| --- | --- | --- |
| **Waive** | GND ×10 zone islands | Class-E cosmetic — waive only |
| **Must-fix (RF Class C)** | ANT_FIT, AUX, AUX_FIT | RF owns DNP shunt pads; may **place later under PM OK**; do **not** route through RF keepout |
| **Must-fix (GPIO partials)** | P0.19, P0.22 leftover ratsnests | Real opens (not accept). Finish in **post-placement copper**; see package B help note |
| **Route-later** | SIM_*, COEX0, GPIO singles (P0.00/01/03/14/16/20/25–29) | Co-route / F-hop mandate; not placement packages |

## Live footprint XY (measured from PCB)

| Ref | XY mm | Rot ° | Notes |
| --- | --- | ---: | --- |
| J8 | (50.0, 6.0) | 0.0 | context only (not in place packages) |
| J9 | (116.0, 8.0) | 0.0 |  |
| J10 | (116.0, 28.0) | 0.0 |  |
| J11 | (116.0, 46.0) | 0.0 |  |
| J12 | (6.0, 76.0) | 90.0 |  |
| J13 | (64.0, 76.0) | 90.0 | live (64,76); prior (64,73) failed vs P0.08 vias |
| J14 | (104.0, 48.0) | 0.0 |  |
| J15 | (104.0, 62.0) | 0.0 |  |
| J16 | (108.0, 8.0) | 0.0 |  |
| J17 | (108.0, 26.0) | 0.0 |  |
| U1 | (36.0, 32.0) | 180.0 | pad12 VDD_GPIO abs ≈ (44.0, 31.5) — note only |

Board outline Edge.Cuts ≈ (0,0)–(120,80) mm.

## Package A_SE_duals_J9_J12_J16_J17

**SE duals — J9/J12 (+ J16/J17) for P0.05/07/09/10/11/12/17**  
**Intent:** Open a pin-pitch column between east dual headers (J16/J9, J17) and optionally shift J12 east to shorten saturated bottom-F dual highways that failed in pass30v.  
**Apply as:** single package (J16+J9+J17 together; J12 optional same commit)  
**Nets cluster:** P0.05, P0.07, P0.09, P0.10, P0.11, P0.12, P0.17  

#### J16

- **Current XY:** (108.0, 8.0) rot=0.0
- **Preferred delta:** (-2.54, 0.0) → (105.46, 8.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, 2.54) → (108.0, 10.54) · |Δ|=2.54 mm
- **Nets unlocked:** P0.09, P0.10, P0.11, P0.12
- **Protected-copper risk:** West nudge toward interior may approach VIN_F / P0.15 east stubs @x~105–108 and VDD_GPIO J16↔J17 keep @x111; south alt may crowd J17/P0.17 pad band
- **Full reattach net list:** P0.10, P0.11, P0.12, P0.09, VDD_GPIO, GND
- **Notes:** Open 1-pin-pitch column between J16 and J9 for dual stubs; unlocks P0.09–12 header side

#### J9

- **Current XY:** (116.0, 8.0) rot=0.0
- **Preferred delta:** (-2.54, 0.0) → (113.46, 8.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, 2.54) → (116.0, 10.54) · |Δ|=2.54 mm
- **Nets unlocked:** P0.05, P0.07
- **Protected-copper risk:** West nudge shortens J9↔J16 gap (good) but pads approach J16 PTH; south alt toward J10 may hit P0.06/east VDD_GPIO copies
- **Full reattach net list:** P0.06, P0.07, P0.05, P0.04, VDD_GPIO, GND
- **Notes:** Pair with J16 west as one package — do not move J9 alone

#### J17

- **Current XY:** (108.0, 26.0) rot=0.0
- **Preferred delta:** (-2.54, 0.0) → (105.46, 26.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, -2.0) → (108.0, 24.0) · |Δ|=2.0 mm
- **Nets unlocked:** P0.17, P0.18
- **Protected-copper risk:** West nudge clears x108 corridor vs P0.22@109.2 / VDD wall@110.6; north alt toward J16 may hit VDD_GPIO keep jog @x111
- **Full reattach net list:** P0.17, P0.18, VDD_GPIO, GND
- **Notes:** Helps P0.17 U1↔J17.1 and P0.18 dual; keep VDD_GPIO J16↔J17 F-jog reattach

#### J12

- **Current XY:** (6.0, 76.0) rot=90.0
- **Preferred delta:** (2.54, 0.0) → (8.54, 76.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, -2.0) → (6.0, 74.0) · |Δ|=2.0 mm
- **Nets unlocked:** P0.05, P0.07, P0.09, P0.10, P0.11, P0.12
- **Protected-copper risk:** East nudge (toward J13) may approach P0.08 bottom stitch / P0.15 bottom H@y77.45 wide F-bridge; north alt toward interior may hit P0.08 via column vicinity and south GPIO copper
- **Full reattach net list:** P0.00, P0.01, P0.02, P0.03, P0.04, P0.05, P0.06, P0.07, P0.08, P0.09, P0.10, P0.11, P0.12, P0.13, P0.14, P0.15, VDD_GPIO, GND
- **Notes:** Optional within package — shortens bottom dual haul toward east dual column; reattach ALL J12 nets incl. closed P0.08

### Post-placement copper hints

- Retry P0.05/P0.07 J12↔J9 on NEW column (not pass30v fy77/fy778 geometries)
- Retry P0.09–12 J12↔J16 stubs in opened x108–116 gap
- Retry P0.17 U1↔J17 with J17 west of P0.22 keep

**Helps finish P0.19 / P0.22?** Indirect only — J17 west slightly eases SE corridor congestion near P0.22@x109.2; does not finish P0.19/P0.22 by itself.

## Package B_SE_column_J10_J11_J13

**SE column — J10/J11/J13 for P0.18–31 squeeze**  
**Intent:** Relieve J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) without repeating failed J13 (64,73).  
**Apply as:** single package (J13 + J10 + J11 together)  
**Nets cluster:** P0.18, P0.21, P0.23, P0.24, P0.30, P0.31  

### J13 anti-collision (do not repeat failed delta)

- **Failed:** [64.0, 76.0] → [64.0, 73.0] — P0.08 vias (65.2,72.25)/(65.2,73.95) vs J13.1@y73
- **Preferred alternate:** → [64.0, 78.5] Δ=[0.0, 2.5] — south away from via stack; open north-of-header reattach band
- **Alt alternate:** → [67.0, 76.0] Δ=[3.0, 0.0] — east shift clears x65.2 via column laterally

#### J13

- **Current XY:** (64.0, 76.0) rot=90.0
- **Preferred delta:** (0.0, 2.5) → (64.0, 78.5) · |Δ|=2.5 mm
- **Alt delta:** (3.0, 0.0) → (67.0, 76.0) · |Δ|=3.0 mm
- **Nets unlocked:** P0.18, P0.21, P0.23, P0.24, P0.30, P0.31, P0.19, P0.22
- **Protected-copper risk:** PREFERRED south (64,78.5): avoids known-fail (64,73) vs P0.08 vias @(65.2,72.25)/(65.2,73.95). Risk: board Edge.Cuts y=80 clearance/silk; south pads closer to edge. ALT east (67,76): shifts pad row away from via x=65.2 column; risk pad shorts into existing B copper near former pass30r y≈72.8 class if any stubs remain north — verify before keep. DO NOT propose (64,73) again.
- **Full reattach net list:** P0.16, P0.17, P0.18, P0.19, P0.20, P0.21, P0.22, P0.23, P0.24, P0.25, P0.26, P0.27, P0.28, P0.29, P0.30, P0.31, VDD_nRF, VDD_GPIO, GND
- **Notes:** Prior (64,73) FAILED pass30s. Preferred Δ=(0,+2.5)→(64,78.5) mag=2.5; alt Δ=(+3,0)→(67,76). Full reattach all 20 pins after move.

#### J10

- **Current XY:** (116.0, 28.0) rot=0.0
- **Preferred delta:** (-2.54, 0.0) → (113.46, 28.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, 2.54) → (116.0, 30.54) · |Δ|=2.54 mm
- **Nets unlocked:** P0.21, P0.23, P0.24, P0.22
- **Protected-copper risk:** West nudge toward interior past VDD_GPIO wall@x110.6 / P0.22 col@x109.2 — may hit J17@x108 / P0.06@107.4 band; south alt crowds J11
- **Full reattach net list:** P0.21, P0.22, P0.23, P0.24, VDD_GPIO, GND
- **Notes:** Opens east-edge squeeze for P0.18–24 duals; MUST reattach pass30r P0.22 B-attach into J10.2

#### J11

- **Current XY:** (116.0, 46.0) rot=0.0
- **Preferred delta:** (-2.54, 0.0) → (113.46, 46.0) · |Δ|=2.54 mm
- **Alt delta:** (0.0, -2.54) → (116.0, 43.46) · |Δ|=2.54 mm
- **Nets unlocked:** P0.30, P0.31
- **Protected-copper risk:** West nudge same class as J10 (VDD H@y51.08 / east wall); north alt toward J10 may PTH-collide
- **Full reattach net list:** P0.30, P0.31, VDD_GPIO, GND
- **Notes:** Unlocks P0.30/P0.31 J13↔J11 after J13 alternate landing

### Post-placement copper hints

- Reattach J13 stubs on NEW y (south) or NEW x (east) — do not reuse pass30s y70 mutual H crossings
- Retry P0.31 U1.89↔J13.16↔J11.2 after column opens
- Retry P0.18/21/23/24/30 SE stitches with NEW geometries (not pass30v)

**Helps finish P0.19 / P0.22?** YES — primary help. J13 south/east requires reattach of P0.19 (J13.4) and P0.22 (J13.7); J10 west shortens remaining P0.22 ratsnest to J10.2 and eases finish of pass30r partial. P0.19 finish still needs copper from U1.30/pass30u island to J13.4 after reattach.

## Package C_west_longhaul_J14_J15

**West long-haul — J14/J15 for MAGPIO/MIPI/COEX1**  
**Intent:** Nudge J14/J15 west (toward U1) as one package to shorten MAGPIO/MIPI/COEX1 long-haul before any copper retry.  
**Apply as:** single package (J14+J15 lockstep — preserve 14 mm vertical spacing)  
**Nets cluster:** MAGPIO0, MAGPIO1, MAGPIO2, MIPI_VIO, MIPI_SCLK, MIPI_SDATA, COEX1  

#### J14

- **Current XY:** (104.0, 48.0) rot=0.0
- **Preferred delta:** (-3.0, 0.0) → (101.0, 48.0) · |Δ|=3.0 mm
- **Alt delta:** (-2.0, -2.0) → (102.0, 46.0) · |Δ|=2.828 mm
- **Nets unlocked:** MAGPIO0, MAGPIO1, MAGPIO2, MIPI_VIO, MIPI_SCLK, MIPI_SDATA
- **Protected-copper risk:** West toward U1 shortens ~70–80mm haul; may approach east GPIO / VDD_GPIO SE wall and under-mod copper. Diagonal alt (-2,-2)→(102,46) mag≈2.83 toward U1 west pad exit — risk RF-adjacent north band if later routed north of keepout incorrectly (routing must stay outside RF keepout)
- **Full reattach net list:** MAGPIO0, MAGPIO1, MAGPIO2, MIPI_VIO, MIPI_SCLK, MIPI_SDATA
- **Notes:** Place-first to make long-haul class tractable; copper still post-placement

#### J15

- **Current XY:** (104.0, 62.0) rot=0.0
- **Preferred delta:** (-3.0, 0.0) → (101.0, 62.0) · |Δ|=3.0 mm
- **Alt delta:** (-2.0, -2.0) → (102.0, 60.0) · |Δ|=2.828 mm
- **Nets unlocked:** COEX1
- **Protected-copper risk:** Same west package as J14; COEX0 is route-later (not unlocked by place alone). Keep COEX2 existing copper clear. Diagonal alt keeps J14/J15 relative pitch.
- **Full reattach net list:** COEX0, COEX1, COEX2, GND, VDD_GPIO
- **Notes:** COEX1 is place-target; COEX0 remains route-later co-route. Reattach COEX2 if stubs break.

### Post-placement copper hints

- After place: route MAGPIO/MIPI/COEX1 outside RF keepout (north-of-keepout jog then east was prior plan — re-validate path length)
- COEX0 stays route-later (pass30u dirty) — do not expect place alone to close it

**Helps finish P0.19 / P0.22?** No direct help.

**RF note:** ANT_FIT/AUX/AUX_FIT remain MUST-FIX via RF Class C DNP placement under separate PM OK — not part of this J14/J15 package; never route through RF keepout.

## Package D_VDD_GPIO_U1_12_NOTE_ONLY

**Optional note only — VDD_GPIO U1.12 escape**  
**Intent:** Document U1.12 blockage; NO U1 move proposal without later explicit PM OK.  
**Apply as:** note only — not a placement package  

- **U1 live XY:** (36.0, 32.0)
- **U1.12 abs:** ≈ (44.0, 31.5)
- **Blocker:** U1.12 fanout vs GND via forest + P0.13/COEX2/Stage-A VDD2; pass30w NW F@y34.5 + B@x35.5 hit P0.22/P0.21 via forest
- **Proposal:** none
- **FLAG:** NO U1 MOVE without later explicit Hardware PM OK
- **Without U1 move:** Header-side VDD_GPIO escapes (J16/J17/J10 already partially tied) + co-route rip list for mid island — not placement this pass
- **P0.19/P0.22:** No — U1 stay. Avoid any VDD_GPIO escape that clips P0.22/P0.19 keep copper.

## Context — route-later (not placement packages)

| Net | Opens | Note |
| --- | ---: | --- |
| SIM_1V8 / SIM_CLK / SIM_IO / SIM_RST | 1 each | U1↔U4 ~40 mm through COEX2/ENABLE/VDD2 — co-route |
| COEX0 | 1 | pass30u B west-col dirty |
| P0.00, P0.01, P0.03, P0.14, P0.16, P0.20 | 1 each | GPIO corridor / protected copper |
| P0.25–P0.29 | 1 each | J13/U1 singles — corridor after Package B |

## Success criteria (this pass)

- [x] Proposal MD + JSON written
- [x] PCB_LAYOUT_REVIEW Pass30x section
- [x] Board untouched
- [ ] Footprint moves / copper — **deferred to PM-approved execute pass**

Artifacts: `reports/PASS30X_PLACEMENT_PROPOSALS.md`, `reports/PASS30X_PLACEMENT_PROPOSALS.json`.

