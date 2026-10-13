# PINOUT: firmware-facing pin map (v2 UART modem module, 2026-10-13)

Branch `v2` (base `067291f`). The schematic (`schematic/`) is the source of truth; the host interface lives on sheet **G. HOST INTERFACE (J20)** (`schematic/07_UART.kicad_sch`).
v2 removes every breakout header (J1, J9–J18): the board is an AT-command LTE-M/NB-IoT (+DECT NR+, GNSS) modem driven by a host MCU over UART. **No 2G/GSM.**

## Host header J20 (1×10, 2.54 mm THT, LCSC C57369). Names are host-view.

| J20 | Host name | Dir (host view) | Path | nRF9161 signal | U1 pad |
|---|---|---|---|---|---|
| 1 | VIN | power in | → D1 → D2/F1/FB4 → VDD_nRF | VDD1/VDD2, U2 LDO | — |
| 2 | GND | — | — | GND | — |
| 3 | VIO | power in (logic ref) | translator A-side VCCA (U5–U8), R21, R23 | — | — |
| 4 | HOST_TX | out | U5 A1→B1 | P0.03 = UART2 **RXD** | 99 |
| 5 | HOST_RX | in | U6 B1→A1 | P0.02 = UART2 **TXD** | 97 |
| 6 | HOST_RTS | out | U5 A2→B2 | P0.07 = UART2 **CTS** (modem input) | 4 |
| 7 | HOST_CTS | in | U6 B2→A2 | P0.06 = UART2 **RTS** (modem output) | 3 |
| 8 | HOST_DTR | out, active-low | U7 A→B, R21 100k pull-up to VIO | P0.31 = DTR | 89 |
| 9 | HOST_RI | in, active-low | U8 B→A | P0.30 = RI | 88 |
| 10 | HOST_nRESET | out, open-drain, active-low | Q1 BSS138 (G=VDD_GPIO, S=nRESET, D=HOST_nRESET) | nRESET | 32 |

- VIN: 3.0–5.5 V (PS VDD range). VIO: 1.1–5.5 V (SN74LXC range), so 1.8 / 3.3 / 5 V hosts work. Modem side (B) is VDD_GPIO = 3.3 V from U2 (unchanged).
- Flow-control naming: the host's RTS output drives the modem's CTS input (P0.07); the modem's RTS output (P0.06) drives the host's CTS input. Cross-over is done on the board; wire J20 straight to host pins of the same name.
- HOST_nRESET: drive low (open-drain or push-pull) to reset. A host driving it high (even 5 V) is blocked by Q1. There is no on-board pull-up on the host side (deliberate: with VIO absent a pull-up to VIO would hold the modem in reset).
- **VIO absent:** R23 (100k) holds VCCA < 100 mV, so the LXC Ioff-float feature puts all translator I/Os in hi-Z. Modem RXD (P0.03), CTS (P0.07) and DTR (P0.31) then sit on their firmware pull-ups (`bias-pull-up` / `GPIO_PULL_UP` in the overlay) = UART idle, flow stopped, DTR deasserted. The modem still runs; no back-powering of the host.
- No PWR_OFF pin: ENABLE (pad 101) stays pulled to its on-state by R1 10k to VDD1 (+C14, TP17). No 3V3 output pin.

## Translator direction ties
| Ref | Part | VCCA | VCCB | DIR | Direction |
|---|---|---|---|---|---|
| U5 | SN74LXC2T45DCUR | VIO | VDD_GPIO | VIO (high) | A→B host→modem (TX, RTS) |
| U6 | SN74LXC2T45DCUR | VIO | VDD_GPIO | GND (low) | B→A modem→host (RX, CTS) |
| U7 | SN74LXC1T45DBVR | VIO | VDD_GPIO | VIO (high) | A→B DTR |
| U8 | SN74LXC1T45DBVR | VIO | VDD_GPIO | GND (low) | B→A RI |
DIR is referenced to VCCA (datasheet), so tying it to VIO/GND is valid at any host voltage. Each VCC pin has a 100 nF (C41–C48).

## Firmware (NCS 3.x Serial Modem add-on)
Build with `-DEXTRA_DTC_OVERLAY_FILE=external-mcu.overlay`. Verified 2026-10-13 against
https://raw.githubusercontent.com/nrfconnect/ncs-serial-modem/main/app/external-mcu.overlay:
```
uart2: TX P0.02, RX P0.03 (bias-pull-up), RTS P0.06, CTS P0.07 (bias-pull-up), hw-flow-control, 115200
dtr-gpios = <&gpio0 31 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
ri-gpios  = <&gpio0 30 GPIO_ACTIVE_LOW>;
```
The hardware matches this overlay with **no pin changes**. Notes:
- nRF9161 DK support was dropped from the add-on; use an nrf9151dk-based or custom board definition (same SiP pin map).
- Remove any DK button/LED aliases on P0.02/P0.03/P0.06/P0.07/P0.30/P0.31 (on the DK, RI drives an LED).
- STATUS LED D4 remains on **P0.00** (optional `led0` alias). LEDs on P0.01–P0.03 and the USER button (P0.08) are gone.
- Legacy SLM (NCS ≤ 3.1, `CONFIG_SLM_POWER_PIN=31`, `CONFIG_SLM_INDICATE_PIN=30`) uses the same DTR/RI pads but its default UART pins differ (P0.10–P0.13); it would need a custom uart2 overlay with the pins above.

## Changes vs v1 (067291f)
| Function | v1 | v2 |
|---|---|---|
| UART | UART0 TX P0.06 / RX P0.04 on J9, 2-wire | uart2 TX P0.02 / RX P0.03 / RTS P0.06 / CTS P0.07 via translators to J20 |
| Wake / indicate | none | DTR P0.31, RI P0.30 |
| Power in | J1 | J20.1 (VIN_IN) |
| LEDs | P0.00–P0.03 | P0.00 STATUS only (D3 power LED on VIN unchanged) |
| Buttons | SW1 DISABLE, SW2 RESET, SW3 USER | SW2 RESET only |
| SPI/I2C/I2S/PDM/ADC/GPIO/MAGPIO/COEX headers | J10–J18 | removed; pins NC (no-connect flags on U1) |
| Trace P0.21–P0.25 | conflicted with SPI0 | no conflict; J8.6 (P0.22 SWO) unchanged |
| Current measurement | R2 + JP1 + TP19/TP20 | removed, VIN_FILT tied directly to VDD_nRF |

Unused GPIOs (P0.01, P0.04, P0.05, P0.08–P0.29 except P0.22 on J8.6), COEX1/2, MAGPIO0–2, MIPI_* are NC. COEX0 still drives U3 (GNSS bias switch).
