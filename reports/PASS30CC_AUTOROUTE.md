# pass30cc — Freerouting autoroute batch (branch `autoroute-gpio`)

Base: main 8628f07, board blob 0e1d4fa. After: blob d20a2c4 (see commit). Not pushed; main untouched.

## Tooling
- OpenJDK 21 (`openjdk-21-jre`) + Freerouting **v1.9.0** jar at `/workspace/tools/freerouting-1.9.0.jar` (sha256 9084a488…3102), run under `xvfb-run` with `-de/-do -mp 40|30 -mt 1 -oit 0.5`. v2.5.0 needs Java 25 and was not used.
- KiCad 9.0.2 pcbnew python: `scripts/pass30cc/export.py` (DSN), `imp.py` (SES importer that adds only new wires/vias for the listed nets onto the untouched original board, then refills zones).

## DSN set-up
- Every existing track and via exported as `(type fix)` — **no net was ripped** in the kept result.
- Rules: 0.18 mm track, only via 0.50/0.30, clearance 0.15 mm; POWER class (VDD*, VIN*, ENABLE, DEC0, SIM_VCC, GNSS_VBIAS*) clearance 0.20 mm, width 0.30.
- Keepouts: RF x0–24.2 y20–64 all layers (tracks+vias); VDD_nRF neck x53–60 y12–22 (In2 tracks, vias all layers); sealed B.Cu pocket x81.8–97.3 y44.2–45.0; U1 body/courtyard box x27.6–44.4 y26.35–37.86 via keepout all layers (U1 has no courtyard graphic, so the footprint bbox was used).
- Round A (kept): In2 declared a power layer (no signals) to protect the VDD_nRF plane.
- Round B (kept for P0.23/P0.24 only): In2 allowed; result checked net-by-net for plane splits.

## Experiments
| run | setup | non-GND opens after | note |
|---|---|---|---|
| r1 | all 4 layers | MIPI_SDATA 1, **VDD_nRF 4** | In2 routes split VDD_nRF plane → discarded |
| r2 | In2 = power | 6 | **kept** (20 nets + VDD_GPIO closed) |
| r3 | as r2, ripped P0.00/P0.05/P0.09/P0.11 | 6 (same nets) | ripping gained nothing → discarded |
| r4 | on r2, In2 allowed, 6 nets | 3, VDD_nRF 2 | per-net test: only **P0.23+P0.24** together keep plane whole → kept those two |
| r5 | on r4, In2 allowed, 4 nets | MAGPIO1 closed but VDD_nRF 2 | discarded |

## Gate (before → after)
- non-GND opens **26 → 4** (unconnected 38 → 19)
- short / clearance / crossing / hole: 0/0/0/0 → 0/0/0/0; hole_to_hole 1 → 1; courtyard 0 → 0
- No net closed today became open.
- VDD_nRF 0 opens; every power net 0 opens (VDD_GPIO was open before and is now closed). Zones refilled; no plane split.
- GND islands (GND unconnected items): **12 → 15** (new signal copper on F/In1/B carves 3 more GND pour fragments; reported, not fixed).
- Post-checks on new copper: 0 vias within 0.25 mm of any pad, 0 vias in U1 box, 0 items in RF keepout / neck / pocket.

## Metrics
- Vias 337 → 402 (+65). Track added 1829.2 mm (359 segments: In1 180, F 82, B 63, In2 34). Removed copper: none.
- Nets ripped and rerouted: **none**.
- Nets newly routed: COEX1, MAGPIO0, MAGPIO2, MIPI_SCLK, MIPI_VIO, P0.03, P0.10, P0.12, P0.14, P0.18, P0.21, P0.23, P0.24, P0.25, P0.26, P0.27, P0.28, P0.29, P0.30, P0.31, SIM_IO, VDD_GPIO (0.30 mm, 3.4 mm).
- Many new routes are long (52–133 mm per net); review for SI if any are fast signals.

## Still open
- MAGPIO1, P0.01, SIM_1V8, MIPI_SDATA: no path on F/In1/B with everything else fixed; Freerouting's In2 solutions (r1/r4/r5) all split the VDD_nRF plane. Ripping the J12 approaches (r3) did not help.

## Files
- reports/DRC_PASS30CC_BEFORE.json, reports/DRC_PASS30CC_AFTER.json
- reports/PASS30CC_BEFORE.png, reports/PASS30CC_AFTER.png (copper layers + edge)
- scripts/pass30cc/ (export.py, imp.py, drclib.py, r2/r4 DSN+SES)
