# PASS30CP J5: GND via for the J5.2 (left pad) island, RF-approved

## Via
One 0.30/0.60 GND via, tented both sides, at **(5.90, 50.75)**. It goes straight to In1 (no In1 slot; In1 stays 2 pieces). No F.Cu link was added.

| Check | Required | Actual (edge to edge) |
|---|---|---|
| J5.2 pad edge (pad top y 51.375) | ≥0.15 | 0.325 |
| J5.1 signal pad (x 7.5–8.5) | ≥0.5 | 1.30 |
| GNSS_ANT trace (leaves pad 1 at (8, 50.95) toward +x) | outside ±0.5 band | 1.70 from the trace edge, so ≥1.2 outside the band |
| GNSS_VBIAS track y=50 (0.2 w) | board clearance | 0.35 |
| GNSS_VBIAS track x=5.02 (0.2 w) | board clearance | 0.48 |

## Deviations: RF please confirm
1. **Position.** There is no room on the pure outer (left) side of J5.2: the gap from the pad edge (x 6.0) to the GNSS_VBIAS track at x 5.02 is too small for a 0.6 mm land. Below the pad, the y=54 VBIAS track blocks it. The via therefore sits at the outer-top corner. It is still on the far side from the signal pin.
2. **Only one via.** A second one does not fit.
3. **Distance to GNSS_VBIAS.** The via is 0.35 mm from the GNSS_VBIAS copper. The step-1 stitch rule asks for ≥1 mm from GNSS_VBIAS; the J5 brief did not restate it.
4. **Finding, no change made.** GNSS_VBIAS has a rectangular F.Cu loop around J5: (13.52,50) → (5.02,50) → (5.02,54) → (13.52,54).
   - The loop is drawn twice (0.18 and 0.20 mm sets), dates from the initial commit, and does not touch J5.1.
   - It looks like a leftover. It was not touched (RF copper).

The J5 signal pad, the GNSS trunk, C27, L4, FB5, U3, C31 and C32 are unchanged.

## Gate
- All 0.
- **Unconnected: 0.**
- In1 GND: 2 pieces. VDD_nRF: 1 piece.
