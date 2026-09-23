# PASS30AA — Package B' proposals ONLY (no execute)

**Timestamp:** 2026-09-23 13:24 IST  
**Context:** After **pass30z KEEP** (RF Class C closed; unconnected 67→64).  
**Scope:** Revised Package **B'** candidates for J13/J10/J11. **No copper executed in this pass.** Package **A deferred**.

## Live keep XY (do not move U1)

| Ref | XY (mm) |
| --- | --- |
| J13 | (64.0, 76.0) |
| J10 | (116.0, 28.0) |
| J11 | (116.0, 46.0) |
| U1 | (36.0, 32.0) |

## Banned J13 landings (do not reuse)

`(64, 73)`, `(64, 78.5)`, `(67, 76)`

## Hard clears required

| Obstacle | Rule |
| --- | --- |
| P0.22 via @ **(112.5, 32.5)** | J10 west must clear (113.46 failed — shorted J10.3 P0.23) |
| Bottom highways **y≈78.5–79.2** | J13 must not land on P0.01/P0.04/P0.06/P0.08 tracks |
| P0.01 via @ **(80.51, 76.7)** | J13 pad column must clear |

## Preferred atomic package

| Ref | Target XY | Δ from live |
| --- | --- | --- |
| **J13** | **(64.0, 75.0)** | 1.0 mm north |
| **J10** | **(115.0, 28.0)** | 1.0 mm west |
| **J11** | **(115.0, 46.0)** | 1.0 mm west |
| U1 | (36.0, 32.0) | 0 (locked) |

**Why:** J13 leaves the south highway band and P0.15 @ y=77.45; J10/J11 only −1 mm west so J10.3 stays ~2.57 mm from P0.22 via@(112.5,32.5) (vs ~1.12 mm at failed 113.46). Not a banned landing. Static probe: hard_clear, 0 geom hits (pad vs live copper).

## Alternates (1–2)

### Alt1 — more J13 north, gentler J10 west
- J13 **(64.0, 74.5)** / J10 **(115.5, 28.0)** / J11 **(115.5, 46.0)**
- Δ: 1.5 / 0.5 / 0.5 mm
- Best P0.22 via margin; watch P0.08/P0.01 vias near y≈73.9–74.5

### Alt2 — J13 east+north, J10 west 1.5 mm
- J13 **(65.0, 75.0)** / J10 **(114.5, 28.0)** / J11 **(114.5, 46.0)**
- Δ: ~1.41 / 1.5 / 1.5 mm
- Shifts J13 column vs P0.01 via; do **not** go to 113.46

## Rejected (pass30y evidence)

| Package | Failure |
| --- | --- |
| J13(64,78.5)+J10/J11(113.46,*) | Highways y≈78.5–79.2 + J10 vs P0.22 via short |
| J13(67,76)+J10/J11(113.46,*) | J13 pad6 vs P0.01 via@(80.51,76.7) + same J10 short |
| J13(64,73) | Banned prior landing |

## Execute gate (when PM assigns)

1. Atomic B' only; backup + DRC before/mid/after  
2. shorting/clearance/crossing = 0 else **full revert**  
3. No U1 / no Package A / no Gerbers  
4. Protect Stage A, P0.15 west wrap, P0.22/P0.19, pass30u + **pass30z Class C** copper  

**Note:** Static probe ≠ DRC after reattach. pass30y showed reattach L-jogs can still dirty a geometrically “clear” landing.

## Files

- `reports/PASS30AA_PACKAGE_B_PROPOSALS.json`
- Prior fail detail: `reports/PASS30Y_SUMMARY.md`
