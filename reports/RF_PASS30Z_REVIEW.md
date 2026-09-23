# RF pass30z Class C re-review

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 IST |
| **Reviewer** | RF Power Engineer |
| **Board** | nRF9161-DEV-BOARD |
| **Against** | `docs/RF_STUB_DNP_PLAN.md` (approved stub / DNP plan) |
| **Layout claim** | `reports/PASS30Z_SUMMARY.md` KEEP |
| **Verdict** | **PASS** |

## Method

Independent parse of live `nRF9161-DEV-BOARD.kicad_pcb` (footprint XY, pad nets, F.Cu stub segments, GND vias) + `reports/DRC_PASS30Z_BEFORE.json` / `AFTER.json` + pre-edit backup under `.mcp-backups/pass30z-rf-class-c/`. Layout claims were not trusted blindly.

## Stub table (measured)

| Net | Ref | Body XY | Stub (mm) | pad1 | pad2 / GND via |
| --- | --- | ---: | ---: | --- | --- |
| `ANT_FIT` | C22 | (17.5, 31.75) −90° | **0.883** | ANT_FIT | GND via on pad2 |
| `AUX` | C23 | (24.8, 34.0) 0° | **1.000** | AUX | via @ (25.98, 34.0) |
| `AUX_FIT` | C24 | (15.0, 31.8) 0° | **1.200** | AUX_FIT | via @ (16.18, 31.8) |

All stubs join same-net 50 Ω trunks; all ≤2 mm.

## DRC / Class C

- Unconnected **67 → 64**; shorting/clearance/crossing remain 0 in AFTER summary.
- `ANT_FIT` / `AUX` / `AUX_FIT`: **no longer** in `unconnected_items`.

## Protect / must-not-touch

| Item | Result vs pre-edit |
| --- | --- |
| L1, inductor-L2, TP1, J2, J3 | Same XY |
| U3, C27, L4, FB5 | Same XY |
| Solid In1.Cu GND zone | Byte-identical to backup (no RF cut) |
| 50 Ω trunks | Not ripped; Class C stubs only |

## DNP

Schematic `03_LTE_RF`: C22–C24 Value=`DNP`, `(dnp yes)`, `(in_bom no)`. Leave unpopulated.

## Issues (Layout rework)

**None** for Class C.

Minor (non-blocking): C22/C24 bodies sit inside west keepout box (plan allows pad-in-matching); C23 body just east of x≈24.2. PCB footprints lack `(dnp yes)` attribute (schematic DNP is controlling).

## Residual fab gate

Unconnected **64 ≠ 0**. Still no fab. P0 reminder: `VDD_GPIO`, `SIM_*`, `COEX0`/`COEX1`, MAGPIO/MIPI, remaining GPIO, GND islands.

## Package B′

**Protect** C22/C23/C24 stubs, 50 Ω trunks, solid In1/L2 under RF, L1 / inductor-L2 / TP1, U3 / bias-T while Package B′ runs.

## Paste lines

**Hardware PM:** pass30z Class C RF re-review = **PASS**. Stubs 0.883 / 1.000 / 1.200 mm; ANT_FIT/AUX/AUX_FIT DRC closed; trunks/L1/L2/TP1/U3/bias-T/solid In1 intact. No RF rework. **Lock this RF copper for Package B′.** Fab still blocked (unc=64; P0 power/SIM/COEX/GPIO).

**Layout:** Class C accepted — do not touch C22/C23/C24 stubs, 50 Ω trunks, solid In1 under RF, series L1/inductor-L2/TP1, or U3/bias-T during Package B′. Continue P0 opens only outside that protect set.
