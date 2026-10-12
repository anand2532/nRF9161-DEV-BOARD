# RF / Power review: branch `finish` @ 9d14ed5 (pass30ch/ci/cj) + VIPPO plan

Reviewer: RF Power Engineer. Baseline 2830243 (RF_REVIEW_PASS30CG: MERGE WITH FIXES). Read-only: boards from `git show` into /tmp, zones refilled in pcbnew 9.0.2, kicad-cli DRC run with the matching .kicad_pro. No PCB/SCH edits, no commits.

## Verdict for 9d14ed5: **MERGE**
F1 is applied correctly and the protected RF copper, In1 and the VDD_nRF neck are intact. Three small follow-ups (F2–F4) are **not merge blockers**. Fold them into the next copper pass (the VIPPO pass).

## Checks (2830243 → 9d14ed5)
| # | Check | Result | Status |
|---|---|---|---|
| 1 | F1: SIM_CLK_C via (76.624, 56.05) + 2.55 mm stub | Via removed. B.Cu seg now runs from the tee at (76.62, 53.5) → 46.67. No SIM_CLK_C open in DRC. Only other diff: SIM_1V8 (CI) and P0.10 (CJ) copper. Footprints are unchanged (0 moved). | PASS |
| 2 | SIM_1V8 route | New 77.3 mm: F 32.8 / B 44.6, 6 vias (0.5/0.3). Net total 114.4 mm. Follows the planned north escape: pad 49 (29.75, 26.75) → F.Cu 0.20 → via (29.6, 24.8) → B.Cu x=31.05 down to y 39.8 → F.Cu x≈30 → B/F along y 54.6/56.6 → C38/C33/JP2/U4.5. Length is about 1.1× Manhattan, which is reasonable. No In1/In2 copper. **Width 0.18 mm on most of the run, below the 0.25 mm power rule.** IR: ~0.31 Ω total (1 oz), so ~6 mV at 20 mA and ~16 mV at 50 mA peak (<1% of 1.8 V). Electrically fine. | PASS, see F2 |
| 2b | SIM_1V8 decoupling | C33 (76, 44) and C38 (72, 52) sit at the SIM/JP2 end, 48.9 mm from U1.49. This pin supplies the SIM card, so the card end is the cap that matters. A 100 nF at U1.49 is optional and is a schematic/placement decision, not a blocker. | OK (note) |
| 3 | Via (29.6, 24.8) ↔ SIM_RST In1 (y=25.5) | 0.36 mm copper-to-copper. The rule is Default 0.10 mm (SIM_1V8 and SIM_RST are both Default class), and the SIM exception is 0.15 mm inside the fan-out zone. DC supply next to a slow reset line, with no parallel run. SIM_1V8 F.Cu crosses SIM_RST In1 at 90° only. | PASS, no action |
| 4 | U1 B.Cu GND pieces | 56.6 mm² has GND vias (30, 20/29/32/35/40). 88.1 mm² (x27.8–33.9, y4.8–39.6) has **one** via at (30, 10). DRC (refilled) lists no B.Cu GND island, so both are connected. But the 88.1 piece is a ~35 mm sliver with its only stitch 20+ mm from its RF-corner end (y 30–39.6). | PASS, see F3 |
| 4b | DRC (refilled, with project rules) | unconnected 23 = 12 signal opens + 11 GND F.Cu islands (cg: 26 = 14 + 12). clearance/short/crossing/hole 0. via_dangling 1→0. track_dangling 4 (pre-existing VDD_GPIO ×3 + P0.11). | PASS |
| 5 | P0.10 | U1.18 → J12.11, 66.4 mm (F 15.7 / B 50.7), 5 vias. Min 8.0 mm to RF copper, ≥7.3 mm to SIM, ≥9.8 mm to VDD_nRF copper, >10 mm from the JP1→FB1 neck. Passes 0.21 mm from DEC0 on B.Cu at (45.8, 31.5): GPIO vs modem decoupling node, short, OK at ≥0.2 mm. | PASS |
| 6a | In1 GND | 2 pieces, 8150.4 → 8142.6 mm² (−7.8, via anti-pads only). No new In1 copper. | PASS |
| 6b | In2 VDD_nRF | 1 piece, 6810.5 → 6801.7 mm² (−8.8, via anti-pads). The nearest new via is 10.9 mm from FB1, so the neck is unchanged at **3.18 mm** (>2 mm). | PASS |
| 6c | RF keepout x0–29, y26–40 (F.Cu/In1) | No new copper inside. The SIM_1V8 escape is at x=29.75 and the via at y=24.8. | PASS |
| 6d | Protected RF copper | 53/53 items identical (ANT/ANT_FIT/AUX/AUX_FIT/GPS/GNSS_*). C22/23/24, L1, L2, TP1, U3, C27, L4, FB5 positions identical. | PASS |
| 6e | SIM spacing of new copper | Min 0.36 mm (the via in check 3, inside the fan-out zone). All other new copper is ≥0.69 mm from SIM_IO/CLK/RST(_C). Pre-existing (not new) SIM_1V8 segments near U4/JP2 sit 0.16–0.17 mm from SIM_RST/SIM_RST_C on F.Cu. Those are DC-vs-reset, legacy; note only. | PASS |

## VIPPO plan review (JLC 4L epoxy fill + Cu cap, 0.20/0.30 in-pad, B.Cu escape)
U1 is at (36, 32), rot 180. RF pads (0.3×0.3): **61 ANT (28.25, 31.5), 64 AUX (28.25, 33.0), 67 GPS (28.25, 34.5)**. GND pads 52 (28, 27.0), 56 (28, 29.0) and 60 (28, 31.0) sit inside the west column; pad 60 lies between pad 59 and pad 61.
The In1 GND zone clearance is **0.25 mm**, so a default 0.20 mm barrel cuts a **0.70 mm** anti-pad. That is over the 0.5 mm limit, and at 0.5 mm pitch neighbouring anti-pads merge into slots (pads 53–55 → ~1.7 mm slot, 57–59 → ~1.7 mm slot).

| Pad | Net | XY (mm) | Nearest RF pad (ctr / edge-to-edge) | Nearest feed | Verdict |
|---|---|---|---|---|---|
| 53 | MAGPIO2 | (28.0, 27.5) | 61: 4.01 / 3.46 | ANT 4.0 | OK with C1–C4 (in keepout → C5) |
| 54 | MAGPIO1 | (28.0, 28.0) | 61: 3.51 / 2.96 | ANT 3.5 | OK with C1–C5 |
| 55 | MAGPIO0 | (28.0, 28.5) | 61: 3.01 / 2.46 | ANT 3.0 | OK with C1–C5 |
| 57 | MIPI_VIO | (28.0, 29.5) | 61: 2.02 / 1.47 | ANT 2.0 | OK with C1–C5 |
| 58 | MIPI_SCLK | (28.0, 30.0) | 61: 1.52 / 0.97 | ANT 1.5 | OK with C1–C5. A 0.4 mm anti-pad leaves ~1.1 mm to pad 61. |
| 59 | MIPI_SDATA | (28.0, 30.5) | 61: 1.03 / **0.48** | ANT 1.0 | **FLAGGED**: conditional. Needs C1 (0.4 mm anti-pad → ~0.7 mm to pad 61) **and** C3 (GND VIPPO in pad 60 between it and ANT). Without both: reject. |
| 48 | SIM_IO | (30.25, 26.75) | 61: 5.15 / 4.85 | ANT 5.2 | OK. No RF objection (outside keepout). B.Cu clearance to SIM_1V8 ~0.55 mm. The B.Cu route must still meet SIM ≥0.5 mm / ≤10 mm parallel, which is a Layout feasibility question. |
| 20 | P0.12 | (44.0, 27.5) | 61: 16.3 | 16.3 | OK |
| 24 | P0.14 | (42.25, 26.75) | 61: 14.8 | 14.8 | OK |
| 29 | P0.18 | (39.75, 26.75) | 61: 12.4 | 12.4 | OK |
| 42 | P0.25 | (33.25, 26.75) | 61: 6.9 | 6.9 | OK |
| 89 | P0.31 | (36.75, 37.25) | 67: 8.9 | GPS 8.9 | OK. Escape east/south, not west. |

JLC capability (quick check, jlcpcb.com capabilities + POFV page): epoxy-filled, plated-over via-in-pad is offered on 4-layer, **charged** (free only on 6–20L). The POFV table lists **0.20 hole / 0.30 dia** (annular ring 0.05 mm, the minimum; 0.075 preferred). 1.6 mm / 0.2 mm = 8:1 aspect, at the limit. DFM must confirm the order option, cost and the 0.05 mm ring.

### Length targets after VIPPO: **not achievable with J14 where it is**
J14 (MAGPIO/MIPI header) is at (104, 48). The west column is at x=28, so the straight line is ~78 mm and a realistic north-then-east B.Cu route is ~100 mm. That exceeds MIPI_SCLK/SDATA ≤50, MIPI_VIO ≤60 and MAGPIO ≤80. COEX1 is closed (78.9 mm, J15). This is a placement gate, see G3.

## Conditions for the VIPPO pass
- **C1** Local In1 clearance override (rule area or custom .kicad_dru rule) for the signal VIPPO barrels: **0.10 mm → 0.40 mm anti-pad**, leaving ~0.10 mm In1 webs at 0.5 pitch. If DFM rejects 0.10 mm webs, stagger the vias in the 0.8 mm pads: alternate x=27.8 / 28.2, which gives ~0.64 mm diagonal pitch.
- **C2** No anti-pad under any 50 Ω feed. The ANT feed runs pad61 → (22.49, 32.0) → north x=22.49 → y=27.3 → west. The B.Cu escape of 53–59 goes **north (x 23.5–29) to y<26, then east** toward J14. No B.Cu west of x 23.5 or south of y 30.5 in the west column. P0.31 escapes east/south.
- **C3** GND stitching: put GND VIPPO (same 0.20/0.30) in GND pads **52, 56, 60**. Pad 60 is mandatory, as the fence between pad 59 and ANT pad 61. Also add ≥1 GND via within 1 mm of each B.Cu signal-via cluster north of the column (y≈26).
- **C4** No new In1 copper. Barrels only. In1 must stay 2 pieces and continuous between the column and pads 61/64/67. Re-measure In1 area/pieces after refill.
- **C5** Pads 53–59 are inside the extended RF keepout (x0–29). An explicit, documented exception for **via barrels only, pads 53–59** is required, with the keepout otherwise unchanged. No F.Cu/In1 tracks in the keepout.
- **C6** Protected RF copper 53/53 + C22/23/24/L1/L2/TP1/U3/C27/L4/FB5 must remain identical. In2 neck ≥2 mm (currently 3.18 mm). SIM ≥0.5 mm outside the y≥24 fan-out exception.
- **C7** JLC confirmation by DFM (4L POFV option, 0.05 mm ring, 8:1 aspect).

## Fix list
- **F2** (next pass, non-blocking) Widen SIM_1V8 to ≥0.25 mm where clearance allows, or record a waiver (IR ≤16 mV at 50 mA). Add `SIM_1V8` to the POWER netclass pattern so the rule is enforced.
- **F3** (next pass) Stitch the 88.1 mm² B.Cu GND sliver (x27.8–33.9, y4.8–39.6): add GND vias every ≤5 mm, at minimum near y≈25, 32 and 38. Today its only stitch is at (30, 10), 20–30 mm from its RF-corner end. Alternatively delete the sliver portion south of y 26.
- **F4** (optional) 100 nF at U1.49 on SIM_1V8, if Schematic agrees.

## Fab gates (still NOT fab-ready)
- **G1** 12 signal opens: MAGPIO0/1/2, MIPI_SCLK/VIO/SDATA, SIM_IO, P0.12/14/18/25/31. Plus 11 GND F.Cu islands to stitch or remove.
- **G2** VIPPO pass done under C1–C7, then RF re-review.
- **G3** MIPI/MAGPIO length targets: decide **before** the VIPPO pass. Either (a, preferred) move J14 near U1's west/north side so routes are ≤50/60/80 mm, or (b) the user/Hardware PM accepts ~100 mm runs with series 22–33 Ω at U1 (schematic change) and a continuous GND reference.
- **G4** DFM sign-off on POFV and cost. No Gerbers until unconnected = 0.
