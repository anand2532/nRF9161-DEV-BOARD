# RF/Power review — pass30cc autoroute (`autoroute-gpio` 3e2a15f vs main 8628f07)

**Verdict: REJECT as-is.** Do not merge. Re-route with In1.Cu excluded as a signal layer. Most nets can keep their F/B topology. Protected Class C copper is unchanged, but the batch breaks the LOCKED rule that In1 stays solid GND.

Method: pcbnew 9.0.2 Python on `git show` blobs (/tmp/p30). New items = tracks/vias present in 3e2a15f and absent from 8628f07. Removed items: **0**.

## Key numbers
| metric | before | after |
|---|---|---|
| In1.Cu GND filled fragments | 3 | **14** |
| In1.Cu GND filled area (mm²) | 8074 | **6857 (−1217, −15 %)** |
| largest In1 fragment (mm²) | 7762 | 4613 (the main plane is now split into large pieces of 1331, 192, 141, 105, 89… mm²) |
| new signal copper on In1 | 0 | **~1011 mm / 180 segs** (19 of 22 nets) |
| F.Cu GND fragments | 20 | 26 |
| B.Cu GND fragments | 18 | 22 |
| DRC GND-unconnected | 12 | 15 |

## Q1 — per-net length (new copper only)
| net | mm | In1 | F | B | In2 | vias |
|---|---|---|---|---|---|---|
| MAGPIO2 | 132.9 | 116.1 | 16.8 | – | – | 1 |
| MIPI_SCLK | 123.7 | 94.4 | 0 | 29.3 | – | 3 |
| MIPI_VIO | 109.1 | 50.4 | 32.9 | 25.8 | – | 3 |
| MAGPIO0 | 109.0 | 50.8 | 22.4 | 35.8 | – | 7 |
| COEX1 | 81.4 | 25.4 | 1.1 | 54.9 | – | 3 |
| P0.24 | 103.5 | 4.9 | 6.2 | – | 92.5 | 3 |
| P0.21 | 96.8 | 87.5 | 9.4 | – | – | 1 |
| P0.25 | 94.7 | 78.1 | – | 16.6 | – | 4 |
| P0.29 | 87.1 | 40.3 | 46.8 | – | – | 4 |
| P0.27 | 84.0 | 21.9 | 44.4 | 17.7 | – | 3 |
| P0.23 | 81.8 | – | – | – | 81.8 | 0 |
| P0.31 | 81.2 | 26.6 | 3.7 | 50.8 | – | 5 |
| P0.26 | 80.4 | 41.4 | 39.0 | – | – | 1 |
| P0.30 | 79.6 | 16.3 | 42.4 | 20.9 | – | 2 |
| P0.28 | 79.6 | 32.4 | 25.7 | 21.4 | – | 4 |
| P0.12 | 73.1 | 54.9 | 9.3 | 8.9 | – | 2 |
| P0.10 | 72.8 | 50.8 | 6.7 | 15.3 | – | 5 |
| P0.03 | 70.2 | 48.6 | 21.6 | – | – | 1 |
| SIM_IO | 68.8 | 52.0 | 13.7 | 3.1 | – | 4 |
| P0.14 | 64.1 | 46.9 | 1.2 | 16.0 | – | 5 |
| P0.18 | 52.0 | 42.8 | 1.2 | 8.0 | – | 4 |
| VDD_GPIO | 3.4 | – | 3.4 | 0 | – | 0 |

Assessment. Nordic gives no hard mm limit here, so the numbers below are engineering judgment. Nordic's nRF91 guidance keeps MIPI RFFE / MAGPIO / COEX short and near the SiP. They go to the antenna-tuner / front-end, and they must stay off the RF feeds and matching networks.
- **MIPI_SCLK** is up to ~26 MHz with ns edges (RFFE). At 124 mm, 94 mm of it sits in the reference plane and it runs 0.77 mm from the ANT feed. That is **not acceptable**. Target **≤ 50 mm**, on B.Cu (or F.Cu outside the RF area), with an unbroken GND reference and ≤ 2 vias each with a GND return via. MIPI_SDATA (still open) gets the same target, routed alongside SCLK. **MIPI_VIO** is a supply/reference: length matters less. Keep it ≤ ~60 mm, put 100 nF at the tuner end, and keep it off In1.
- **MAGPIO0/2, COEX1** are slow or static control lines, so timing is a non-issue. They still switch during TX and can carry RF/emissions coupling. Target **≤ 80 mm** with no In1 and no route under or next to the 50 Ω feeds. MAGPIO2 at 133 mm (87 % In1) must be re-routed.
- P0.xx GPIO and SIM_IO: length is fine for SI, but the routes are not acceptable on In1 (see Q2).

## Q2 — In1
In1.Cu carries a single zone, **GND, full board**. The stackup doc locks it as the L1 microstrip reference (H ≈ 0.12 mm) and as solid GND under ANT/AUX/GNSS. It is also the GND reference under U1. Findings:
- 0 new In1 items inside the declared keepout (x0–24.2). However, the **50 Ω feeds continue on F.Cu from x 22.3 to 28.25** to the U1 pads ANT(28.25,31.5), AUX(28.25,33.0) and GPS(28.25,34.5). That stretch is outside the keepout and was never protected:
  - **MIPI_VIO In1 (24.65,24.4)→(24.65,39.88)** slots In1 straight across under the ANT, AUX and GPS feeds and next to the C24/AUX_FIT region.
  - **P0.14 In1 (37.43,23.8)→(26.16,35.07)→(26.16,35.64)** runs diagonally under the U1 body and crosses under the AUX/GPS feeds (lateral offset ≈0.01 mm to AUX, 0.39 mm to GPS).
  - MAGPIO0 In1 (25.66→29.34, y 38.1–39.8) and MIPI_SCLK In1 (26.7, 39.9–40.5) cut the plane just south of the feeds and the U1 RF corner.
- Inside the U1 footprint box (27.6–44.4 × 26.35–37.86): P0.18 (3 segs, 13.2 mm) and P0.14 (1 seg, 15.9 mm).
- Board-wide, In1 is cut from 3 into 14 fragments. Return currents for the modem, SIM and every L1 trace now detour.
- **Must move off In1: all 19 nets that use it.** Priority order: MIPI_VIO, P0.14, MAGPIO0, MIPI_SCLK, P0.18, then MAGPIO2, P0.21, P0.25, P0.12, SIM_IO and the rest.

## Q3 — coupling (new track vs victim; adjacent-layer value is centre-line offset; flagged if < 0.36 mm (3H) or < 0.5 mm)
| aggressor | victim | layers | min mm | ∥ <0.5 mm |
|---|---|---|---|---|
| P0.14 | **AUX feed** | In1/F | 0.01 (under) | 7.8 mm |
| MIPI_VIO | **AUX feed** | In1/F | 0.33 | 1.0 |
| P0.14 | **GPS feed** | In1/F | 0.39 | 6.5 |
| MIPI_SCLK | **ANT feed** | F/F | 0.77 | – |
| P0.14 / MAGPIO0 | GNSS_VBIAS(_SRC) | In1/F, B/B | 0.11–0.37 | 0.7–1.5 |
| P0.24 | SIM_CLK | In2/In1 | 0.02 | 23.7 |
| P0.25 | SIM_CLK | In1/In1 | 0.17 | 27.2 |
| P0.23 | SIM_RST / SIM_IO_C / SIM_RST_C | In2/B | 0.06–0.23 | 10–34 |
| MIPI_VIO | SIM_IO | F/F | 0.16 | 22.3 |
| MIPI_VIO | SIM_CD | In1/F | 0.23 | 21.8 |
| P0.12 / MIPI_SCLK / MIPI_VIO | VDD_GPIO | In1/F | 0.12–0.46 | 14–19 |
| SIM_IO | SIM_1V8 | In1/F | 0.50 | 6.8 |
VDD_nRF had no new track within 1 mm. The report's claim that the VDD_nRF plane is intact holds: P0.23/P0.24 sit on In2 without splitting the plane. Those two nets still couple to SIM over long runs (24–34 mm) with no GND between the layers, because In2 is a power plane.

## Q4 — GND islands (+3 DRC; new fill fragments)
- F.Cu: new pieces 959 mm² (54.8–114, 31.5–63), 706 mm² (28–80, 41–78), 213 mm² (22.7–50.2, 22.9–47.3: **touches the RF feed/U1 corner**), 16.6 mm² (31.6–35.9, 14.1–27.2, U1 north), and slivers of 0.7 mm² (33.7, 23.4–26.4) and 0.3 mm² (37.2, 36.8–38).
- B.Cu: new 4.8 mm² (25.7–27.2, 29–35.2), **directly under the ANT/AUX/GPS feed stubs**. The other new pieces are 17–80 mm², in the east/digital area.
- The sub-5 mm² slivers near U1/RF (F 0.3, F 0.7, B 4.8 mm²) are the likely DRC islands. They are harmful because floating or barely-stitched copper next to the 50 Ω feeds detunes the match. Fix: **remove them** (zone min-area 5 mm² or keepout). If the 213 / 16.6 mm² F.Cu pieces stay, stitch them with GND vias at ≤ 2 mm pitch (≈ λ/20 at 2.2 GHz in FR4 would allow more, but they sit next to RF). Most of the islands disappear once In1 is cleared.

## Q5 — protected Class C copper
Unchanged. Footprint position, rotation and pads match for C22, C23, C24, L1, L2, TP1, U3, C27, L4 and FB5. All 64 track/via items on ANT, ANT_FIT, AUX, AUX_FIT, GNSS_*, GPS are identical. **pass30z PASS stands.**

## VIPPO (MAGPIO1 p54, MIPI_SDATA p59, SIM_1V8 p49, P0.01 p96; pads 0.8×0.3 mm, 0.5 mm pitch)
**Acceptable from the RF/power side, with conditions:**
1. IPC-4761 Type VII: non-conductive epoxy fill, planarized, copper cap plated over (cap ≥ 12 µm), dimple/bump ≤ ±15 µm for the LGA joint.
2. Via ≤ 0.2 mm laser or 0.25/0.15 mm mechanical, fully inside the 0.3 mm pad width. This needs DFM Fab Engineer confirmation of capability and cost (VIPPO adds a fab step to the whole panel).
3. The via must not land in In1 under the RF pads p61/64/67. p54/p59 are 1.0–2.5 mm from ANT p61, so keep anti-pads minimal (≤ 0.15 mm annulus clearance) and then **escape on B.Cu**, not In1.
4. SIM_1V8 draws only a few tens of mA (SIM supply). One VIPPO via is fine. Put its 100 nF (and 1 µF if planned) on the B.Cu escape within 3 mm.
5. MIPI_SDATA should route with MIPI_SCLK (≤ 50 mm, B.Cu).
Alternative: escape on F.Cu between pads if 0.5 mm pitch allows 0.1 mm track/0.1 mm space (fab dependent), or dog-bone to a via just outside the pad row where free space exists (p49/p96 are on the outer rows). Prefer this wherever it closes the net without VIPPO.

## Fix list
1. **Remove all new In1.Cu copper (≈1011 mm, 19 nets).** Re-run Freerouting with In1 declared a plane/no-route layer, as was already done for In2.
2. MIPI_VIO: no copper on x 24.2–29 / y 24–40. Route north-then-east on B.Cu, ≤ 60 mm.
3. P0.14 and P0.18: no route under the U1 body or the AUX/GPS feeds. B.Cu escape, ≤ 60 mm.
4. MIPI_SCLK (+ SDATA): B.Cu, **≤ 50 mm**, ≥ 1.5 mm (≥ 3× width+H) from the ANT/AUX/GPS feeds, ≤ 2 vias, each with a GND stitch via within 1 mm.
5. MAGPIO0/1/2, COEX1: B.Cu, ≤ 80 mm, no F.Cu within 1 mm of the feeds or matching.
6. **Extend the RF keepout** to x 0–29.0 × y 26–40 for In1/F.Cu (route and via), covering the feed run to the U1 RF pads.
7. SIM: give SIM_CLK ≥ 0.5 mm (or GND guard) from P0.24/P0.25/P0.23. Cap parallel runs ≤ 10 mm, or move P0.23/P0.24 to keep In2 runs off the SIM area.
8. Remove the GND slivers by the RF corner (zone min island area ≥ 5 mm²). Stitch the remaining F/B fragments at ≤ 2 mm pitch near U1/RF.
9. Re-check after the re-route: In1 GND fragment count = before (3), and area ≥ 8070 mm².

## Residual fab gate
No Gerbers until unconnected = 0, In1 is solid again (fix 1/9), the VIPPO decision is confirmed with DFM, and the earlier P0 power/SIM/COEX/GPIO items are closed. The U2 TLV73330 (3.0 V) vs 3.3 V VDD_GPIO doc mismatch is still open.
