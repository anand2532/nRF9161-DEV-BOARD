# PINOUT: firmware-facing pin map (after PINMAP_PROPOSAL, 2026-10-12)

The schematic (`schematic/`) is the source of truth. The full GPIO table is in README "GPIO map".

## Changes vs previous revision
| Function | Old | New | Firmware action |
|---|---|---|---|
| UART0 TX | P0.06 → J9.1 | P0.06 → J9.1 (unchanged) | — |
| UART0 RX | P0.07 → J9.2 | **P0.04 → J9.4** | `rx-pin` / pinctrl `UART_RX` = P0.04 |
| UART0 RTS | P0.05 → J9.3 | **removed** (J9.3 NC) | `hw-flow-control` off; no RTS pin |
| UART0 CTS | P0.04 → J9.4 | **removed** (P0.04 is now RX) | no CTS pin |
| I2S | J16 + J12.10–13 | **J12.10–13 only**; J16 DNF, pins 1–4 NC | GPIOs unchanged: SDIN P0.09, SCK P0.10, LRCK P0.11, SDOUT P0.12 |

P0.05 (J12.6) and P0.07 (J12.8) are now plain breakout GPIOs.

## Unchanged
- SPI0 J10: SCK P0.21, MOSI P0.22, MISO P0.23, CS P0.24.
- I2C0 J11: SDA P0.30, SCL P0.31.
- PDM J17: CLK P0.17, DIN P0.18.
- ADC J18: AIN0–7 = P0.13–P0.20. These are silicon-fixed (nRF9161 PS pin table).
- LEDs: P0.00–P0.03. USER button: P0.08.
- Fixed-function signals: SIM_*, COEX0–2, MAGPIO0–2, MIPI_*, nRESET, ENABLE, SWD.

## Trace vs SPI0 / J10 / J8.6 conflict
P0.21 = TRACECLK, P0.22–P0.25 = TRACEDATA[0..3]. Sources:
- nRF9161 PS pin assignments: https://docs.nordicsemi.com/r/bundle/ps_nrf9161/page/pin.html
- nRF9161 DK trace table: https://docs.nordicsemi.com/r/bundle/ug_nrf9161_dk/page/ug/nrf91_dk/hw_description/hw_debug_in_trace.html

When parallel trace (TPIU) is enabled:
- SPI0 on J10, J8.6 (P0.22) and J13.6–J13.10 can't be used by the application.
- Trace pins need S0S1 or H0H1 drive; use H0H1 if trace is too slow (PS Trace page: https://docs.nordicsemi.com/r/bundle/ps_nrf9161/page/trace.html).

Firmware that uses SPI0 must leave trace disabled.
