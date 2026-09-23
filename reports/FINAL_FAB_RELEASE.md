# nRF9161 DEVELOPMENT BOARD — FINAL FAB RELEASE

**Status: NOT FABRICATION-READY**

Hard gate failed: `unconnected_items = 80` (must be 0) and ratsnest is not zero. Fabrication outputs were **not** generated.

Connectivity truth: `kicad-cli pcb drc` JSON `unconnected_items`.

| Gate | Result |
|------|--------|
| unconnected_items | **80** (need 0) |
| shorting_items | 0 |
| clearance | 0 |
| hole_clearance | 0 |
| Gerbers /fab | **not generated** |

## Board

| Item | Value |
|------|--------|
| Size | 120 × 80 mm |
| Layers | F.Cu / In1.Cu GND / In2.Cu / B.Cu |
| In2 plane net | `VDD_nRF` |
| Tracks | 733 |
| Vias | 250 (start 250) |
| U1 | (36.0, 32.0) mm, rot 180° |
| SIM_DET U1 pad 45 net | `''` (must stay empty) |
| Backup | `.mcp-backups/final-fab-20260917-194911/` |
| Live snapshot after this pass | `after-pass29.kicad_pcb` |
| Pre-this-pass snapshot | `after-pass28.kicad_pcb` |

## This pass (P0.15 west-wrap bounding test)

Start **80** unconnected / **0** shorts. End **80** / **0**. Absolute cap 80. No copper added. No wrap ripped. P0.13–P0.18 U1-to-B hops **not retried** (step 1 did not delete). New vias this pass: 0. Dangling new vias: 0.

**P0.15 west wrap is load-bearing — not removed.** U1 pad 25 (41.75, 26.75) reaches J18.3 / J12.16 only through the courtyard snake from via (41.75, 23.10) west/south (x≈31.00–36.50, y≈22.50–59.20) into J18 at (43.08, 59.20). East copper V x=106 y=20.60–77.45 is fed from J18/J12 south stubs (y=77.45 H), not from an independent via-to-x=106 hop. Stubs (41.75, 23.10)–(41.75, 20.60) and (41.75, 22.50)–(46.50, 22.50)–(46.50, 21.20) do **not** reach x=106. Deleting the wrap would disconnect the U1 pad. A third P0.15 path was **not** added.

**Nets closed this pass:** none

**Closed this live session (earlier passes):** P0.04 J9 (82→81), P0.06 J9 (81→80). COEX2 west remnants removed at unconnected=80 (net stayed ROUTED). This bounding pass closed zero nets.

### Per-net

| net | result |
|-----|--------|
| P0.15 west wrap | **kept** — load-bearing U1-to-J18/J12; east x=106 is downstream of J18 south stubs |
| P0.13–P0.18 U1-to-B | **not attempted** — wrap still occupies x≈31–41.75 y≈22.5–45; ENABLE via (42.75, 41.10) remains |

## Remaining unconnected (by class)

| Class | Count | Meaning |
|-------|-------|--------|
| A | 55 | U1/via to header or island |
| F | 6 | F.Cu power/SIM/SWD islands |
| G | 7 | Header duplicate branches |
| C | 3 | DNP RF shunts (50 Ω) |
| E | 9 | GND F.Cu zone-to-zone |

## Named walls (unchanged)

- **P0.15 west wrap** — via (41.75, 23.10), B courtyard snake x≈31.00–36.50 y≈22.50–59.20 into J18 (43.08, 59.20). Blocks P0.13–P0.18 U1-to-existing-B hops.
- **ENABLE via (42.75, 41.10)** — occupies the south courtyard column that ADC hops need after the wrap.
- **VIN** — VIN_FILT / VIN_F F-class islands; no 80 mm VIN bus this pass.
- **DNP 50 Ω** — class C RF shunt stubs; not closed (F-nets still open).
- **GND E** — F.Cu zone-to-zone GND islands.

### Still-open F targets

- VIN_FILT OPEN 10.131 mm (55.35,12.00)–(53.20,21.90)
- SIM_IO OPEN 51.975 mm (30.25,26.75)–(75.68,52.00)
- SIM_CLK OPEN 41.382 mm (31.25,26.75)–(68.14,45.50)
- nRESET OPEN 68.922 mm (101.68,58.80)–(52.22,10.80)
- P0.08 OPEN 49.281 mm (44.00,30.00)–(26.32,76.00)
- P0.08 OPEN 32.730 mm (78.38,24.00)–(46.20,30.00)
- VIN_F OPEN 24.444 mm (48.00,12.60)–(71.58,19.06)

## Reports

- `reports/UNCONNECTED_AFTER_FINAL.csv`
- `reports/GPIO_FINAL.csv`
- `reports/FINAL_FAB_RELEASE.md`
- `reports/DRC_AFTER_CONNECT.json`
