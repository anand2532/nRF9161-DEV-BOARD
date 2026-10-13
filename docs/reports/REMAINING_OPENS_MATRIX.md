# Remaining Opens Matrix — Option E (pass30w handoff)

**Generated:** 2026-09-23 13:09 IST  
**Board:** pass30u KEEP (pass30w no copper keep)  
**unconnected_items:** 67  
**Gate:** copper passes exhausted for low-risk VDD_GPIO stubs + short SIM/COEX/MAGPIO class; do **not** start another copper pass without placement or co-route mandate.

| Net | Opens | Pads / RefDes | Likely blocker class | Suggested next |
| --- | ---: | --- | --- | --- |
| `GND` | 10 | —(track/via island) | zone_island | **accept** |
| `VDD_GPIO` | 3 | U1.12 | U1.12 fanout vs GND via forest + P0.13/COEX2/Stage-A VDD2 | **place** |
| `P0.05` | 2 | J12.6, J9.3 | SE dual header / bottom-F highway saturated | **place** |
| `P0.07` | 2 | J12.8, J9.2 | SE dual header / bottom-F highway saturated | **place** |
| `P0.09` | 2 | J12.10, J16.4, U1.16 | SE dual header / bottom-F highway saturated | **place** |
| `P0.10` | 2 | J12.11, J16.1, U1.18 | pass30t failed geometries; north/east dual still blocked | **place** |
| `P0.11` | 2 | J12.12, J16.2 | pass30t failed geometries; north/east dual still blocked | **place** |
| `P0.12` | 2 | J12.13, J16.3 | SE dual header / bottom-F highway saturated | **place** |
| `P0.17` | 2 | J17.1, U1.28 | pass30t failed geometries; north/east dual still blocked | **place** |
| `P0.18` | 2 | J17.2, U1.29 | SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) | **place** |
| `P0.21` | 2 | J10.1, J13.6, U1.37 | SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) | **place** |
| `P0.23` | 2 | J10.3, J13.8, U1.39 | SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) | **place** |
| `P0.24` | 2 | J10.4, J13.9, U1.40 | SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) | **place** |
| `P0.30` | 2 | J11.1, J13.15 | SE J13↔J10/J11 column squeeze (VDD_GPIO wall + P0.22 keep) | **place** |
| `P0.31` | 2 | J11.2, J13.16, U1.89 | J13↔J11 SE saturated + under-mod | **place** |
| `ANT_FIT` | 1 | —(track/via island) | RF keepout / matching / U3 region | **accept** |
| `AUX` | 1 | —(track/via island) | RF keepout / matching / U3 region | **accept** |
| `AUX_FIT` | 1 | C24.1, L2.2 | RF keepout / matching / U3 region | **accept** |
| `COEX0` | 1 | —(track/via island) | R4 stub ↔ U3/main; west-col GND via forest (pass30u dirty) | **route** |
| `COEX1` | 1 | J15.2, U1.92 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MAGPIO0` | 1 | J14.1, U1.55 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MAGPIO1` | 1 | J14.2 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MAGPIO2` | 1 | J14.3 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MIPI_SCLK` | 1 | J14.5, U1.58 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MIPI_SDATA` | 1 | J14.6, U1.59 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `MIPI_VIO` | 1 | J14.4, U1.57 | U1 west pad ↔ J14/J15 (~70–80mm); RF-adjacent north band dirty | **place** |
| `P0.00` | 1 | U1.95 | GPIO corridor saturated / protected copper | **route** |
| `P0.01` | 1 | U1.96 | GPIO corridor saturated / protected copper | **route** |
| `P0.03` | 1 | —(track/via island) | GPIO corridor saturated / protected copper | **route** |
| `P0.14` | 1 | U1.24 | GPIO corridor saturated / protected copper | **route** |
| `P0.16` | 1 | U1.26 | GPIO corridor saturated / protected copper | **route** |
| `P0.19` | 1 | U1.30 | partial keep — remaining ratsnest to far header/stub | **accept** |
| `P0.20` | 1 | —(track/via island) | GPIO corridor saturated / protected copper | **route** |
| `P0.22` | 1 | —(track/via island) | partial keep — remaining ratsnest to far header/stub | **accept** |
| `P0.25` | 1 | J13.10 | GPIO corridor saturated / protected copper | **route** |
| `P0.26` | 1 | J13.11 | GPIO corridor saturated / protected copper | **route** |
| `P0.27` | 1 | J13.12, U1.84 | GPIO corridor saturated / protected copper | **route** |
| `P0.28` | 1 | J13.13 | GPIO corridor saturated / protected copper | **route** |
| `P0.29` | 1 | J13.14, U1.87 | GPIO corridor saturated / protected copper | **route** |
| `SIM_1V8` | 1 | U1.49 | U1 SIM fanout ↔ U4 island (~40mm) through COEX2/ENABLE/VDD2 | **route** |
| `SIM_CLK` | 1 | U1.46 | U1 SIM fanout ↔ U4 island (~40mm) through COEX2/ENABLE/VDD2 | **route** |
| `SIM_IO` | 1 | —(track/via island) | U1 SIM fanout ↔ U4 island (~40mm) through COEX2/ENABLE/VDD2 | **route** |
| `SIM_RST` | 1 | U1.43 | U1 SIM fanout ↔ U4 island (~40mm) through COEX2/ENABLE/VDD2 | **route** |

## Suggested-next legend

- **route** — still plausible with co-route / F-hop mandate (may need rip-restore of non-protected nets)
- **place** — needs footprint nudge (J11/J10/J14/J8 or U1 fanout escape) before copper retry
- **accept** — zone cosmetic, RF keepout, or partial-keep ratsnest; freeze or DFM waive

## Pass30w attempt notes

- VDD_GPIO U1 NW + mid via87 F-hop probes: see `PASS30W_SUMMARY.json`
- SIM_*/COEX1/MAGPIO long-haul (~40–80 mm) are **not** short-stub class — deferred to E
- Protected: Stage A VDD2, P0.15 west, P0.22, P0.19, RF/U3 — untouched

