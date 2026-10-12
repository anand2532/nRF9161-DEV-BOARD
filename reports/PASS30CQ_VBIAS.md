# PASS30CQ: GNSS_VBIAS duplicate loop removed, C29 reconnected, 2nd J5.2 GND via (RF-approved)
Base: 62a37bf.

## Removed (F.Cu, GNSS_VBIAS)
The duplicate loop, both 0.18 and 0.20 mm copies (6 tracks):

| Track | Copies |
|---|---|
| (13.52,50) → (5.02,50) | ×2 |
| (5.02,50) → (5.02,54) | ×2 |
| (5.02,54) → (13.52,54) | ×2 |

Also removed:
- (13.52,50) → (12.05,50), 0.18 mm: the duplicate.
- (12.05,50) → (13.35,50), 0.20 mm: this became a dangling stub once the loop was gone. The VBIAS via at (13.35,50) sits in C28.1 and still connects it.

## C29.1 reconnection
- The planned F.Cu track (13.52,50) → (13.52,54) **crosses the GNSS_ANT feed** at y≈51 (DRC tracks_crossing), so the fallback was used:
  - F.Cu stub from (13.52,54.00) (C29.1) to (13.35,54.90), 0.20 mm.
  - Via 0.30/0.60 at **(13.35,54.90)** onto the existing B.Cu VBIAS track at x 13.35 (55.4 → 50).
- The via is fully outside the pad: 0.29 mm edge gap to C29.1 (pad bottom y 54.31).
- To C29.2 GND: 0.62 mm from the via, ≥0.58 mm from the stub. C28.2 is not affected.
- Result: GNSS_VBIAS is one net. C28, C29, C30, L4 and FB5 are all connected (DRC unconnected 0).

## Second J5.2 GND via
- 0.30/0.60, tented both sides, GND to In1, at **(5.40, 52.475)** on the outer (left) side of J5.2.

| Check | Required | Actual (edge to edge) |
|---|---|---|
| J5.2 pad edge (x 6.0) | ≥0.15 | 0.30 |
| J5.1 signal pad | ≥0.5 | ≈1.9 |
| GNSS_ANT trace | outside ±0.5 band | >2.0 |

- It is 1.20 mm from the first via at (5.90,50.75).

## Gate
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk, courtyard, mask_bridge, via_dangling and track_dangling: all 0.
- **Unconnected: 0.**
- In1 GND: 2 pieces, 8178.5 mm². VDD_nRF: 1 piece, 6708.2 mm².

## PNGs
reports/img/PASS30CQ_J5_before.png and reports/img/PASS30CQ_J5_after.png.
