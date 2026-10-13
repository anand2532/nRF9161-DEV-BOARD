# RF/Power review — branch `finish` @ 2830243 (pass30cf 61f49a5 + pass30cg In2)

Reviewer: RF Power Engineer. Baseline is fb5f34e (accepted in RF_REVIEW_PASS30CD). This review only read the files: there are no PCB/SCH edits and no commits. Every board was loaded with pcbnew 9.0.2 from `git show` into /tmp, with zones refilled.

## Verdict: **MERGE WITH FIXES**
Nothing in pass30cf/pass30cg breaks the RF or PDN rules. The one fix is to remove the SIM_CLK_C dangling via and its stub (F1). It is small and can go in the next pass. Still **NOT FAB-READY**: 14 non-GND opens.

## 1. Diff summary
**pass30cf (fb5f34e→61f49a5):** 150 items removed and 6 added.
- **DEC0 via (45.4, 30.55)** and its stub: removed ✔.
- **SIM_RST**: the 6.57 mm B.Cu stubs (×2), via (79.3, 36.0) and F.Cu stub: removed ✔. That is 1 via and 6 tracks, 28.8 mm counting duplicates.
- **GNSS_VBIAS orphan loop**: removed ✔. F.Cu (12.05, 50→45.2) and B.Cu (25.1→12.05 @ y 45.2), 17.8 mm. These are the only RF-net items removed, and I approved them in pass30cd.
- **Power/SWD dangling items** (ENABLE, VDD1/2, VDD_GPIO, VIN*, nRESET*, SWD*) and **duplicate segments**: removed. This includes the P0.13/14/15 duplicates. The open count is unchanged at 17.
- **Added**: P0.23 edge reroute (87.5 mm) and P0.02 0.5 mm F.Cu hop.

**pass30cg (61f49a5→2830243):** 47 items added and 0 removed.

| net | mm | In2 mm | vias |
|---|---|---|---|
| COEX1 | 78.9 | 41.8 | 4 |
| P0.24 | 96.3 | 94.8 | 1 |
| P0.27 | 85.7 | 71.2 | 3 |

There is **no new copper on In1**.

## 2. In2 VDD_nRF plane / PDN
| | pass30cf | pass30cg |
|---|---|---|
| pieces | 1 | **1** |
| area (KiCad) | 7431.2 mm² | **6810.5 mm²** (−8.4 %) |
| area (0.05 mm raster) | 7454.9 | 6831.3 |

**Narrowest neck along each current path** is the bottleneck width measured with a distance transform on the In2 fill.

| path | before | after | location of min |
|---|---|---|---|
| JP1 (in) → FB1 (→VDD1, U1 supply) | 4.40 | **3.18 mm** | (47.5, 14.3) |
| JP1 → FB2 (→VDD2_MID) | 3.73 | 3.72 | (53.1, 14.9) |
| JP1 → R2 (I-sense) | 3.73 | 3.72 | (58.6, 22.2) |
| R2 → U2 (TLV73333 in) | 4.70 | 4.70 | (74.8, 38.8) |

- **Neck width:** every neck is ≥3.18 mm, above the 2 mm flag.
- **Loss of width:** the only path that lost width is JP1→FB1, by −1.2 mm. The cause is the P0.24 run at y 20.2 (x 36–49) and its diagonal to (57, 28). That run passes just south of FB1/FB2.
- **Neck keepout:** no signal crosses the x53–60 / y12–22 neck keepout.
- **Load estimate:**
  - The U1 supply is fed through FB1/FB2. U1 pads take VDD1/VDD2, not VDD_nRF directly.
  - In 1 oz copper, 3.18 mm is about 0.05 mΩ/sq. A ~0.5 A LTE TX peak gives under 1 mV of drop.
  - PDN impedance is set by the ferrites and bulk caps, not by the plane neck.
- **Result:** acceptable.
- **In2 under RF:** all new In2 copper is at x ≥ 33.8, outside x0–29 / y20–64. The RF feeds reference In1 in any case.
- **In1 GND:** 2 pieces, 8150.4 mm² (8156.8 before; the −6 mm² is new via antipads). There are **0 track changes on In1**.
- **Note:** there is inherited signal copper on In1 from main/pre-pass30cc (SIM_CLK, SIM_RST, P0.00/05/09/16–19/21/24). It sits outside the RF keepout and is unchanged by this branch. It is a known deviation from the "no signal on In1" intent, so clean it up opportunistically (F4).

## 3. B.Cu GND 18 → 20 pieces
The 590.6 mm² piece (28.9–88.7, 9.4–40.7) split because of the new P0.24/P0.27/COEX1 vias near U1 (33.8, 25.4), (34.7, 38.5) and (38.25, 39.8).

| new piece | mm² | bbox | stitched? |
|---|---|---|---|
| A | 68.3 | x28.9–33.9, y19.6–40.7 (under U1 west/SIM corner) | yes, ~9 GND vias (30/33 × 20–40) |
| B | 11.6 | x34.1–37.4, y33.4–40.8 (under U1 south) | yes, vias (36.0, 35.0), (37.25, 38.15) |

Both pieces are stitched to In1, so neither is a floating island. They are not RF-harmful (stitching was checked at bounding-box level). Piece A sits next to the RF keepout edge. **Keep piece A.** Delete piece B only if DRC flags it as an isolated sliver.

## 4. COEX1 (78.9 mm, 41.8 mm on In2)
- **Length:** within the ≤80 mm target. COEX1 is a slow control signal.
- **Route:** U1 pad 92 (38.25, 37.25) → In2 (38.25, 39.8) → (42.9, 44.9) …(64.5, 46.5)→(91.9, 62.6). It does not pass through the VDD_nRF neck or under RF.
- **Reference:** on In2 the return path is VDD_nRF, which is AC-tied to GND through the decoupling. That is fine for a control line.
- **Result:** acceptable. The same reasoning applies to P0.24 and P0.27, which are plain GPIO.

## 5. Protected copper / SIM spacing
- **Protected footprints:** C22, C23, C24, L1, L2, TP1, U3, C27, L4 and FB5 all have identical position and rotation.
- **RF/GNSS track and via set:** identical except for the 2 approved GNSS_VBIAS orphans, which takes it from 55 to 53 items.
- **In1:** untouched.
- **SIM spacing:** the closest new copper to any SIM net is **0.565 mm**, between the P0.24 via and SIM_RST. That meets ≥0.5 mm, and there are no parallel runs.

## 6. SIM_CLK_C via (76.62, 56.05): **REMOVE (F1)**
- **Real path:** U4 pin 2 (77.75, 55.4) → F.Cu to (77.75, 53.5) → B.Cu (76.62, 53.5) → B.Cu up x 76.62 to (76.62, 46.67) → J7 C3.
- **The stub:** the B.Cu segment (76.62, 56.05→46.67) continues **2.55 mm past the tee at y 53.5** to a via (0.6/0.3 mm) that connects to nothing on F.Cu.
- **Why it goes:** it adds an open stub plus a via barrel on the SIM clock. It brings no layer change and no test access, it reflects, and it sits 0.9 mm from the U4 pins.
- **Fix:** delete the via and shorten the B.Cu segment to start at (76.62, 53.5). The net stays connected.

## 7. Opens: SIM_IO / SIM_1V8 route plan (4-layer, no VIPPO needed)
- **F.Cu north of U1 pads 48 and 49 is free** from y 26.75 to y 22.0. The only items nearby are SIM_CLK at x 31.25 (via at 31.25, 23.1) and COEX0 at y 22.0. There is nothing else in the box x28.5–32 / y20.5–27.
- **Likely reason Freerouting failed:** the SIM class 0.5 mm clearance is impossible at the 0.5 mm pad pitch, since adjacent pad edges are 0.2 mm apart. Pad 49 was also excluded. Fix this with a rule-area exception: default 0.15 mm clearance for SIM nets inside the U1 fan-out zone (y ≥ 24).
- **SIM_IO (pad 48, 30.25, 26.75):**
  - F.Cu 0.15 mm straight north to (30.25, 23.8), then a via at (30.25, 23.8).
  - The via clears SIM_CLK's via by ~0.6 mm edge-to-edge and COEX0 by 1.3 mm.
  - B.Cu east, ≥0.5 mm from SIM_CLK/SIM_RST, to the C37 / U4 pin 8 (77.35, 56.6) SIM_IO copper. Expect ~70 mm, which is fine for SIM at ≤5 MHz.
  - Parallel run with SIM_CLK at <0.5 mm: only the ~3 mm escape at 0.85 mm edge gap, so OK.
- **SIM_1V8 (pad 49, 29.75, 26.75):**
  - F.Cu 0.2 mm north to (29.75, 24.8), then a via at (29.6, 24.8). This is outside the y26–40 F.Cu keepout, and x ≥ 29.
  - B.Cu 0.25 mm east to the C33 (76, 44) / JP2 SIM_1V8 copper.
  - Optional: a 0.3 mm island on In2 instead, east of x 33 only, routed **south of** the y 20.2 P0.24 run and well away from the x53–60 neck. B.Cu is preferred.
  - SIM_1V8 draws only a few mA, so there is no PDN concern. Add 100 nF near U1 only if Layout has room (optional).
- **Fallbacks if DRC refuses the via spots:**
  - (a) VIPPO on pads 48/49 escaping on B.Cu. This is RF-OK under IPC-4761 Type VII and is pending DFM.
  - (b) A dog-bone does not fit on the 0.5 mm-pitch north row.
  - (d) A fine-line escape is what is described above.
- **Other 12 opens:**
  - **West column (x 28.0): MAGPIO0/1/2, MIPI_SCLK/VIO/SDATA.** Every west/north exit runs straight into the x0–29 / y26–40 F.Cu+In1 keepout and the U1 In2 keepout. The realistic 4-layer path is VIPPO on pads 53–59 → B.Cu. B.Cu under the RF area is shielded by solid In1 and In2. Keep these runs ≥1 mm from GNSS_VBIAS vias and within the length targets.
  - **North row: P0.14 (42.25), P0.18 (39.75), P0.25 (33.25).** These are congested by existing In1/In2 escapes, but the F.Cu north fan-out with a via above y 25 (like SIM_IO) is feasible.
  - **East column: P0.10/P0.12 (x 44).** East exits are not RF-constrained. F.Cu east with a via at x ≥ 45.5 should route.
  - **P0.31:** south row (36.75, 37.25), F.Cu south. The south side is free of the RF keepout.

## 8. 6-layer assessment
- **Microstrip widths:** I used Hammerstad/Wheeler with t = 35 µm for 50 Ω on F.Cu.

| εr \ H | 0.10 mm | 0.12 mm | 0.15 mm |
|---|---|---|---|
| 4.2 | 0.174 | 0.212 | 0.270 |
| 4.5 | 0.164 | 0.201 | 0.255 |

  The current RF_50OHM is 0.20 mm, which is consistent with H 0.12 / εr ~4.5. If the 6-layer build keeps L1–L2 at ~0.12 mm, **the width does not change**. Only the coupon, the impedance-control note and the stackup doc change. Matching π/C24 values are tuned on the VNA post-fab anyway, because they are DNP placeholders. Keepouts stay the same, and there are still no via stubs on RF.
- **Option A, SIG/GND/SIG/SIG/PWR/SIG:**
  - L3 and L4 give 2 inner signal layers for the west/north U1 exits.
  - L3 is next to GND, but L4 references the PWR plane.
  - This option gives the most routing.
- **Option B, SIG/GND/SIG/PWR/GND/SIG (recommended if going 6L):**
  - L2 stays solid GND under RF and U1, L3 is a stripline between GND and PWR, and B.Cu sits over a GND plane.
  - It gives 1 extra signal layer, which is enough for the west column fan-out with blind or through vias. Through vias would still need VIPPO in the U1 0.5 mm field.
  - It is cleaner for return paths and EMI.
- **Does 6-layer fix the exits cleanly?** Only partially. The U1 west/north pads are still trapped by pad pitch, so via-in-pad (VIPPO) or HDI microvias are needed regardless of layer count. 6-layer adds room after the via, not the escape itself.
- **Cost (estimate only):** the bare-board cost is about +30–60 % for a 6L prototype, plus about 2–5 days of lead time. Adding VIPPO to either option costs extra; DFM must quote it.
- **Recommendation: stay on 4-layer.** Close SIM_IO, SIM_1V8 and the north/east/south opens with fan-out vias. Use VIPPO only for the west column (pads 53–59, plus 49 if needed). Go 6L (option B) only if DFM rejects VIPPO or the west-column MIPI/MAGPIO cannot meet the length targets on B.Cu.

## Fix list
- **F1 (must, small):** remove the SIM_CLK_C via (76.62, 56.05) and trim the B.Cu stub to the (76.62, 53.5) tee.
- **F2:** add a SIM-net clearance exception in the U1 fan-out zone, then route SIM_IO and SIM_1V8 per §7.
- **F3:** decide VIPPO for the west column with DFM, then route MAGPIO/MIPI on B.Cu within the targets (MIPI_SCLK/SDATA ≤50, VIO ≤60, MAGPIO ≤80).
- **F4 (opportunistic):** move the inherited In1 signal tracks to F.Cu/B.Cu/In2.
- **Protect set unchanged:** C22/C23/C24 stubs, RF trunks, In1, the VDD_nRF neck x53–60/y12–22, and the extended RF keepout.

## Fab gates (unchanged)
- non-GND opens = 0 (now 14)
- DRC short/clearance = 0
- In1 2 pieces, ≥8100 mm²
- In2 VDD_nRF 1 piece, neck ≥2 mm
- protected RF copper identical to pass30z (minus approved orphans)
- VIPPO spec (IPC-4761 VII) on the fab note if used
- impedance coupon for 0.20 mm / H 0.12
- no Gerbers until all of the above pass
