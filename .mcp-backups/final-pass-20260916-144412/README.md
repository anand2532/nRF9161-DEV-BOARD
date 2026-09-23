# nRF9161-DEV-BOARD

Development board for **Nordic Semiconductor nRF9161-LACA-R7** (LTE-M, NB-IoT, DECT NR+, GNSS).

Electrical source of truth is official Nordic documentation only:

- nRF9161 Product Specification v1.0 (pinout Table 55, mechanics Table 56, reference circuitry)
- nRF91 Hardware Design Guidelines (nWP-037 family / Table 2) — nRF9161 uses the nRF9160 SiP power/RF pinout with DK extra **FB3 on VDD2**
- nRF91 Series Antenna and RF Interface Guidelines (nWP033)
- nRF9161 DK PCA10153 1.0.0 (FB3, GNSS U.FL + COEX0, TPD3F303, SWF MM8130)
- PCN134: DEC0 = **4.7 µF** (not the older 47 µF)

Do not treat this README as a substitute for those documents when certifying a product.

Project files keep the existing names `nRF9161-DEV-BOARD.kicad_*` (not `nRF9161_Board.*`).

## Board purpose

A 120 mm × 80 mm, 4-layer breakout so firmware and RF bring-up can use every nRF9161 interface: LTE/NR+ and GNSS antenna ports, nano-SIM, SWD, all 32 GPIOs, and labelled UART/SPI/I2C/I2S/PDM/ADC headers.

## nRF9161 capabilities on this board

| Function | Implementation |
| --- | --- |
| LTE-M / NB-IoT / DECT NR+ | ANT pin 61, reserved π-match (0 Ω series, DNP shunts), U.FL J2, SWF J3 |
| AUX | AUX pin 64, reserved π-match, TP1 |
| GNSS | GPS pin 67, nWP033 active-antenna bias-T, U.FL J5, SWF J6 |
| UICC/SIM | SIM_RST/CLK/IO/1V8 via TPD3F303 + JAE SF72S006 nano-SIM. SIM_DET pin 45 **floats** |
| 32 GPIOs | J12 (P0.00–P0.15) and J13 (P0.16–P0.31) |
| SWD | 10-pin Cortex-M J8 |
| MAGPIO / MIPI RFFE | J14 |
| COEX | J15 (COEX0 also enables GNSS bias through R4) |
| ENABLE / nRESET | R1 10 kΩ + C14; SW1 DISABLE; R5 1 kΩ + SW2 RESET |

Onboard GNSS ceramic antenna + BGM1212N7 LNA from the nRF9161 DK is **not fitted**. GNSS is U.FL-only for an external **active** antenna.

## Power requirements

VIN **3.0–5.5 V** on J1 (nRF9161 VDD range).

```
VIN (J1)
  D1 PMEG4030ER reverse Schottky → D2 SMAJ5.0A → F1 2 A → FB4 → C1/C2
  R2 50 mΩ (JP1 bypass) → VDD_nRF
       FB1 → VDD1 (pin 102) + C3 47 µF / C4 4.7 µF / C5 100 nF / C6 15 pF
       FB2 + FB3 → VDD2 (pin 22) + C7–C10 (FB3 per nRF9161 DK)
  R1 10 kΩ → ENABLE (pin 101) + C14 100 nF; SW1 to GND = disable
  TLV73330 3.3 V (EN=ENABLE) → VDD_GPIO (pin 12) + C11/C12
  DEC0 (pin 13) → C13 4.7 µF
```

Peak LTE TX on VDD2 is on the order of **500 mA**. Do not power the board from a weak USB 5 V dongle without checking cable and supply headroom. Use a current-limited bench supply for first power-up (1 A limit is a reasonable start; 2 A fuse is the hard limit).

Open JP1 and measure across R2 / TP19–TP20 for current. Close JP1 for normal operation.

Power LED D3 is on VIN, not a GPIO.

Test points: TP_VIN (TP15), TP_VDD_nRF (TP14), TP_VDD1 (TP11), TP_VDD2 (TP12), TP_VDD_GPIO (TP10/TP13), TP_GND (TP16), TP_ENABLE (TP17).

## RF architecture

Nordic evaluates ANT/AUX/GPS as **50 Ω single-ended**. Matching values are antenna- and PCB-specific (nWP033). This board does **not** invent tuned L/C values:

- LTE/NR+: series L1 is a 0 Ω / LQW15AN placeholder; C21/C22 DNP high-Q 0402 (HDG: Murata LQW15AN + GJM1555C1).
- AUX: same reserved π (L2, C23, C24).
- GNSS: nWP033 active-antenna bias-T — C27 100 pF DC block, L4 100 nH choke, C28–C30 + FB5 on ~3.3 V bias from VDD_GPIO through R4/COEX0. Shunts C31/C32 DNP.

Tune L1/C21/C22 (and GNSS shunts) on the finished mechanics with a VNA.

LTE and GNSS matching sit immediately west of the SiP (U1 rotation 180°, RF edge west). Do not place digital traces under the matching networks.

## Antenna requirements

| Connector | Net | Use |
| --- | --- | --- |
| J2 U.FL | ANT_FIT | External LTE / DECT NR+ antenna |
| J3 SWF MM8130 | ANT_FIT | Conducted LTE RF test |
| J5 U.FL | GNSS_ANT | External **active** GNSS antenna (DC on center) |
| J6 SWF MM8130 | GNSS_ANT | Conducted GNSS RF test |
| TP1 | AUX_FIT | AUX test |

Disable GNSS LNA bias (`%XCOEX0`) if using a passive GNSS antenna.

## SIM requirements

- nRF9161 SIM_RST / SIM_CLK / SIM_IO / SIM_1V8 → TPD3F303DPV → JAE SF72S006 **nano-SIM (4FF)**
- SIM_DET (pin 45) **must float** (PS). Mechanical card-detect is `SIM_CD` on J7 CSW-DSW / TP6 — **not** pin 45
- Close JP2 to feed SIM_1V8 to the card
- SIM VPP (C6) NC

## GPIO map (authoritative)

All 32 GPIOs are on J12/J13. Protocol headers J9–J11 and J16–J18 are the **same nets** (intentional probe multiplexing). Onboard LEDs/USER share P0.00–P0.02 and P0.08 — drive those pins as GPIO or leave the LED/button unused in firmware.

| Pin | GPIO | Default header | Onboard | Alternate |
| --- | --- | --- | --- | --- |
| 95 | P0.00 | J12.1 | STATUS LED D4 | — |
| 96 | P0.01 | J12.2 | LTE LED D5 | — |
| 97 | P0.02 | J12.3 | GNSS LED D6 | — |
| 99 | P0.03 | J12.4 | SPARE LED D7 (optional) | — |
| 100 | P0.04 | J12.5 / UART CTS J9 | — | — |
| 2 | P0.05 | J12.6 / UART RTS J9 | — | — |
| 3 | P0.06 | J12.7 / UART TX J9 | — | — |
| 4 | P0.07 | J12.8 / UART RX J9 | — | — |
| 15 | P0.08 | J12.9 | USER SW3, R14 10 kΩ to VDD_GPIO | — |
| 16 | P0.09 | J12.10 / I2S SDIN J16 | — | — |
| 18 | P0.10 | J12.11 / I2S SCK J16 | — | — |
| 19 | P0.11 | J12.12 / I2S LRCK J16 | — | — |
| 20 | P0.12 | J12.13 / I2S SDOUT J16 | — | — |
| 23 | P0.13 | J12.14 / AIN0 J18 | — | AIN0 |
| 24 | P0.14 | J12.15 / AIN1 J18 | — | AIN1 |
| 25 | P0.15 | J12.16 / AIN2 J18 | — | AIN2 |
| 26 | P0.16 | J13.1 / AIN3 J18 | — | AIN3 |
| 28 | P0.17 | J13.2 / AIN4 J18 / PDM CLK J17 | — | AIN4 |
| 29 | P0.18 | J13.3 / AIN5 J18 / PDM DIN J17 | — | AIN5 |
| 30 | P0.19 | J13.4 / AIN6 J18 | — | AIN6 |
| 35 | P0.20 | J13.5 / AIN7 J18 | — | AIN7 |
| 37 | P0.21 | J13.6 / SPI SCK J10 | — | TRACECLK |
| 38 | P0.22 | J13.7 / SPI MOSI J10 / J8.6 SWO | — | TRACEDATA0 |
| 39 | P0.23 | J13.8 / SPI MISO J10 | — | TRACEDATA1 |
| 40 | P0.24 | J13.9 / SPI CS J10 | — | TRACEDATA2 |
| 42 | P0.25 | J13.10 | — | TRACEDATA3 |
| 83 | P0.26 | J13.11 | — | — |
| 84 | P0.27 | J13.12 | — | — |
| 86 | P0.28 | J13.13 | — | — |
| 87 | P0.29 | J13.14 | — | — |
| 88 | P0.30 | J13.15 / I2C SDA J11 | — | — |
| 89 | P0.31 | J13.16 / I2C SCL J11 | — | — |

J12/J13 pins 17–18 = VDD_GPIO (3.3 V), 19–20 = GND.

Full 127-pin audit: `reports/PIN_AUDIT.csv`.

## Peripheral map

| Header | Signals |
| --- | --- |
| J9 UART | TX P0.06, RX P0.07, RTS P0.05, CTS P0.04, 3V3, GND |
| J10 SPI | SCK P0.21, MOSI P0.22, MISO P0.23, CS P0.24, 3V3, GND |
| J11 I2C | SDA P0.30, SCL P0.31, 3V3, GND |
| J16 I2S | SCK P0.10, LRCK P0.11, SDIN P0.09, SDOUT P0.12, 3V3, GND |
| J17 PDM | CLK P0.17, DATA P0.18, 3V3, GND |
| J18 ADC | AIN0–AIN7 (P0.13–P0.20), GND |
| J8 SWD | 10-pin 1.27 mm ARM Cortex (J-Link) |

PWM can be assigned to any GPIO in software; there is no dedicated PWM header.

## SWD / programming

J8 (Samtec FTSH-105 style 1.27 mm 2×5):

| Pin | Signal |
| --- | --- |
| 1 | VDD_GPIO (VTREF) |
| 2 | SWDIO (pin 34) + TP7 |
| 3 | GND |
| 4 | SWCLK (pin 33) + TP8 |
| 5 | GND |
| 6 | P0.22 SWO (optional) |
| 7 | NC |
| 8 | nRESET via R5 1 kΩ + TP9 |
| 9 | NC |
| 10 | GND |

Use nRF Command Line Tools / J-Link. SWD is referenced to the SiP debug domain; VDD_GPIO on pin 1 is target-voltage sense at 3.3 V.

```
nrfjprog -f NRF91 --program firmware.hex --chiperase --verify --reset
```

## PCB stackup

Assumed **4-layer, 1.6 mm**, JLCPCB-like 7628 / JLC04161H-7628 (confirm with the fabricator impedance coupon):

| Layer | Name | Copper | Use |
| --- | --- | --- | --- |
| L1 | F.Cu | 1 oz | Components, RF microstrip, short digital |
| prepreg | ~0.12 mm, εr ≈ 4.2 | | |
| L2 | In1.Cu | 1 oz | **Solid GND** |
| core | ~1.2 mm | | |
| L3 | In2.Cu | 1 oz | VDD_nRF pour + remaining signals |
| prepreg | ~0.12 mm | | |
| L4 | B.Cu | 1 oz | GND pour + digital |

Outline 120 mm × 80 mm, R2 mm corners.

## Impedance assumptions

50 Ω microstrip on L1 over L2 GND:

- H ≈ 0.12 mm, εr ≈ 4.2, 1 oz copper
- Trace width **0.20 mm** (net class `RF_50OHM`)
- Confirm with the fabricator’s 4-layer impedance coupon before tape-out (typical 0.16–0.22 mm)

RF keepout: no digital components or buses in the west matching/U.FL region. L2 under the 50 Ω line is solid GND (required for microstrip). Do not split L2 under ANT/GPS.

## Assembly notes

1. LGA 16.0×10.5 mm, 0.30 mm round-rect pads from PS Table 56 (b=0.30). Nordic also documents oblong b×b1 0.30×0.80 for perimeter fanout; this revision uses 0.30 mm pads. Verify against the DK PcbDoc before SMT.
2. Stencil: follow Nordic DK practice; typical 0.10–0.12 mm stainless with reduction on LGA pads. Characterise with the EMS.
3. Populate DNP match parts only after VNA tune.
4. Close JP1 and JP2 for bring-up unless measuring current / isolating SIM VCC.
5. Ferrites: BOM uses BLM18KG221SN1 on VDD1/VDD2 (HDG Table 2 family). Some later DK notes prefer BLM18PG121SN1D (DCR < 0.1 Ω) — either is a Nordic-documented option; do not substitute arbitrary beads.

## First power-up procedure

1. Visual inspect solder, LGA, RF matching, SIM cage, polarity of D1/D2/LEDs.
2. With power off, measure resistance VIN–GND and VDD_nRF–GND. Expect high kΩ after capacitors charge; a dead short is a stop.
3. Leave J2/J5 antennas disconnected until DC rails are good.
4. Apply **current-limited** 3.3–5.0 V at J1 (start ~200 mA limit, raise to 1 A).
5. Check TP15 VIN, TP14 VDD_nRF, TP11 VDD1, TP12 VDD2, TP10 VDD_GPIO (~3.3 V), TP17 ENABLE high, TP16 GND.
6. Confirm SW1 not held (DISABLE). nRESET should sit high (internal pull-up).
7. Connect J-Link to J8. `nrfjprog -f NRF91 --ids` must see the SiP.
8. Program a blink/UART sample.
9. Toggle P0.00–P0.02 and watch STATUS/LTE/GNSS LEDs; press USER (P0.08).
10. Insert nano-SIM, close JP2, check SIM_1V8, CLK, RST, IO with a scope (keep probes short).
11. Fit LTE antenna on J2, run `%COPS` / Nordic asset_tracker LTE attach.
12. Fit **active** GNSS antenna on J5, enable COEX0 / LNA bias, check `$GNGGA` or `%XMONITOR`.
13. DECT NR+ only with matching firmware and a suitable 1.9 GHz antenna on J2.

## Hardware validation

Follow Nordic nRF9161 Hardware Verification Guidelines: current vs TX, VDD2 droop during LTE pulses, conducted RF via J3/J6 SWF, UICC ISO-7816, SWD, GPIO loopback on J12/J13.

## Known limitations — not production-ready until these are closed

kicad-cli DRC (`--severity-error`): **0 shorts, 0 clearance, 0 hole_clearance**. ERC: **0 errors**. The board is **not fab-ready** because **116 pads are still unconnected**.

1. **Routing is incomplete.** Outer LGA pads are Nordic oblong 0.30×0.80 mm; 27 U1 nets have courtyard vias; J3 SWF tap is on F.Cu. Remaining unconnected copper is mainly VDD1/VDD2/VDD_GPIO, SIM (RST/CLK/IO/1V8), ENABLE/nRESET, MAGPIO/MIPI/COEX, and several GPIOs plus their protocol-header duplicates (J9/J10/J16/J18). Finish those in Pcbnew.
2. GNSS_VBIAS still needs C30 and L4 joined around the GNSS_ANT spine without crossing the 50 Ω line.
3. 0.50 mm-pitch LGA escape cannot run traces *along* pad rows; remaining U1 pads that failed fanout must leave along the oblong long axis into the north/south/east via rings (west MAGPIO/MIPI should jog to the north ring).
4. In2.Cu is the VDD_nRF plane — do not pour GPIO on it. Long GPIO remainder belongs on B.Cu with unique channels south of J18 (y≈46–55) and west wrap x≈25–33 for J12 pins in the RF x-range.
5. Silkscreen is dense on 0402 clusters. Connector names and pin-1 markers are present.
6. No onboard GNSS LNA/patch. Active antenna required.
7. Input TVS is 5.0 V; continuous VIN must stay within 3.0–5.5 V.
8. `schematics/` (plural) is leftover unused hierarchy; the live design is `schematic/` (singular).

**Do not send this PCB to a fab until unconnected nets are routed and DRC unconnected_items is zero.**

## Reports and manufacturing

- BOM: `BOM.csv`
- ERC: `reports/ERC.txt`, `reports/ERC_kicad-cli.rpt`
- DRC: `reports/DRC_kicad-cli.rpt`, `reports/DRC_SUMMARY.txt`
- Pin audit: `reports/PIN_AUDIT.csv`
- Gerbers/drill/pos: `fab/` (generated from the last saved PCB; reflects the routing state above)

## Project files

- `nRF9161-DEV-BOARD.kicad_pro`
- `nRF9161-DEV-BOARD.kicad_sch` — sheets A–L
- `schematic/01_nRF9161.kicad_sch` … `12_TESTPOINTS.kicad_sch`
- `nRF9161-DEV-BOARD.kicad_pcb`
- `libraries/Nordic_nRF9161.kicad_sym`
- `libraries/Board.pretty` — LGA, SWF, TPD3F303 USON
