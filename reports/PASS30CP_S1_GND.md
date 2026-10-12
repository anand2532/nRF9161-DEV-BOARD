# PASS30CP step 1: GND island stitching (partial: 10 → 5 unconnected)
**5 GND stitch vias, 0.5/0.3.** Each was checked for:
- ≥1.0 mm from every RF/GNSS net (ANT*, AUX*, GPS, GNSS_ANT, GNSS_VBIAS*, GNSS_LNA_EN);
- not in a pad, not in any rule area or the RF keepout, and outside the U1 body +0.25 mm;
- DRC clean, with In1 GND kept at 2 pieces and VDD_nRF at 1 piece.

| Via | Island fixed |
|---|---|
| (71.05, 26.6) | F.Cu 64.5 mm², C1/C3 area |
| (74.4, 13.1) | F.Cu 70.6 mm², near R3 |
| (69.35, 22.65) | F.Cu 50.5 mm², near D2 |
| (45.6, 37.15) | F.Cu 3.2 mm², east of U1 south row |
| (74.55, 47.2) | F.Cu 11.8 mm² holding C34.2 (GND via; ≥0.15 mm to SIM_VCC, which is not touched) |

**Island removal:** the GND zones are already set to "always remove islands". The 5 remaining pieces are not removed because each holds a GND pad whose only connection is that piece.

**Remaining 5: not fixable within the given rules (decision needed)**

| Island | Pad | Why no fix |
|---|---|---|
| (36.09–36.38, 25.56–27.25), 0.38 mm² | U1.36 (36.25, 27.0) | Sliver between escapes: no via fits. An F.Cu link inward hits U1's NC inner-row pads (y 27.65; short/clearance, tried and reverted). |
| (40.59–40.88, 25.56–27.25), 0.38 mm² | U1.27 (40.75, 27.0) | Same: inner NC pads 106/107. |
| (43.63–46.40, 26.18–27.66), 2.87 mm² | U1.21 (43.75, 27.0) | No legal via spot. The inward link breaks hole clearance to the P0.12 VIPPO (43.75, 27.5). |
| (41.09–41.41, 36.75–40.87), 1.23 mm² | U1.98 (41.25, 37.0) | 0.32 mm sliver. The inward link hits NC pads 126/127 (y 36.35). |
| (5.37–7.29, 50.35–53.65), 5.76 mm² | J5.2 (u.FL GNSS shield pad, left) | Inside the RF copper keepout. A GND link to J5.2 (right) was flagged items_not_allowed; no via allowed (RF ≥1 mm). |

**Options:**
- (a) In-pad GND VIPPO 0.30/0.20 in U1 pads 21/27/36/98, the same pattern as the approved GND pads 52/56/60. This needs a PM/DFM waiver of "no vias in pads"; fill/cap scope would go 25 → 29.
- (b) RF to approve a GND link or via at J5.2 inside the keepout.

**Gate (refilled):**
- short/clearance/crossing/hole/hole_to_hole/courtyard/edge/silk/mask_bridge/via_dangling are all 0.
- **Unconnected 10 → 5** (GND only).
- In1 GND: 2 pieces, 8179.3 mm².
- VDD_nRF: 1 piece, 6723.6 → 6716.5 mm².
- RF copper and SIM nets untouched.
