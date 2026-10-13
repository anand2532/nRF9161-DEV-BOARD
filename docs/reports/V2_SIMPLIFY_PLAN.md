# V2_SIMPLIFY_PLAN: nRF9161 UART modem module — **APPLIED** (branch `v2`, 2026-10-13)

> **STATUS: APPLIED** on local branch `v2` (base 067291f), schematic + BOM + docs only; PCB not updated. The plan text below is the original proposal; where it differs, this box wins.
>
> **Anand's decisions (via Hardware PM, 2026-10-13):**
> 1. Serial Modem add-on `external-mcu.overlay` pins (re-verified against ncs-serial-modem `main`: TX P0.02, RX P0.03, RTS P0.06, CTS P0.07, DTR P0.31, RI P0.30).
> 2. **No PWR_OFF.** ENABLE stays on via R1 10k to VDD1 (+C14, TP17). SW1 DISABLE removed. Q2/R20 not added.
> 3. No 3V3 output pin.
> 4. Current-measurement path removed (R2, JP1, TP19, TP20); VIN_FILT merged into VDD_nRF. J3/J6 SWF removed; J2/J5 U.FL kept.
> 5. AUX L2/TP1 kept (TP1 stays, no BOM).
> 6. **C39 = DNP** in both schematic (`dnp yes`, `in_bom no`) and BOM.csv. RF_POWER_REVIEW.md has no C39 requirement; BOM rationale (nRF91 HDG: nothing extra on nRESET) and the schematic Value "DNP" both say not fitted, so only the KiCad flag was wrong.
> 7. J20 = **1×10** THT 2.54 mm (not 1×12): VIN, GND, VIO, HOST_TX, HOST_RX, HOST_RTS, HOST_CTS, HOST_DTR, HOST_RI, HOST_nRESET.
> 8. Parts (JLCPCB/LCSC, stock via JLC parts API 2026-10-13 ~09:00 IST): U5/U6 SN74LXC2T45DCUR **C5217891** (13,275, extended); U7/U8 SN74LXC1T45DBVR **C4364198** (7,473, extended); Q1 BSS138 onsemi **C52895** (56,329, extended); J20 BOOMELE 2.54-1*10P **C57369** (18,953, extended); R21/R23 100k 0402 **C25741** (basic); C41–C48 100nF 0402 CL05B104KO5NNNC **C1525** (basic).
> 9. Removed J1, J9–J18; test points kept: TP1, TP7–TP9, TP13–TP17.
>
> **Deviations from the plan:** R22 (HOST_nRESET pull-up to VIO) dropped — with VIO absent and R23 pulling VIO low it would hold the modem in reset through Q1; the host drives HOST_nRESET low only. Added R23 100k VIO pull-down so the LXC Ioff-float (VCC < 100 mV → hi-Z) engages when no host is connected. Sheets 08/09/10 deleted; 07 repurposed as "G. HOST INTERFACE (J20)".
>
> **Result:** 104 → 84 symbols; fitted+BOM placements 74 → 67; DNP 8 → 7 (C21–C24, C31, C32, C39); no-BOM pads 22 → 10 (JP2, TP1, TP7–9, TP13–17); BOM.csv 85 → 76 lines (one line per ref, TPs on one line; LCSC column added). ERC 0 errors (170 library-config warnings only, baseline 203).

- Worktree `/workspace/kicad-projects/nRF9161-v2-plan`, branch `v2-simplify-plan`.
- Base `067291fc029273f74bfaba631637886e2b45eabe` (= `main` tip, verified).
- No schematic or PCB edits, nothing committed.
- Part data comes from `BOM.csv` plus a `kicad-cli sch export netlist` of the schematic at 067291f (104 symbols). U1 pad numbers and XY come from `nRF9161-DEV-BOARD.kicad_pcb` at 067291f.

## 0. What this board is (and is not)
- The nRF9161 is an **LTE-M / NB-IoT (3GPP Rel-14) + DECT NR+ + GNSS** SiP. It has **no 2G/GSM (and no 3G/Cat-1/Cat-4)**, so the module must not be marketed as a "GSM modem".
- Host MCUs talk to it with AT commands over UART, using Nordic's Serial LTE Modem (SLM) app or its successor, the Serial Modem add-on.
- Source: https://docs.nordicsemi.com/bundle/ncs-2.6.5/page/nrf/device_guides/working_with_nrf/nrf91/nrf9161.html

## 1. Firmware reference: SLM / Serial Modem default pins (primary sources)

| Source | UART | TX | RX | RTS | CTS | Power/DTR in | Indicate/RI out |
|---|---|---|---|---|---|---|---|
| NCS v2.9.0 SLM `boards/nrf9161dk_nrf9161_ns.{overlay,conf}`, external-MCU block (`uart2_default_alt`, `CONFIG_SLM_POWER_PIN=31`, `CONFIG_SLM_INDICATE_PIN=30`, commented in the file) | uart2 | P0.10 | P0.11 | P0.12 | P0.13 | P0.31 (active-low pulse) | P0.30 (active-low pulse) |
| NCS v2.9.0 SLM same files, active default (PC terminal) | uart0 (DK board pins) | — | — | — | — | P0.08 | P0.00 |
| **Serial Modem add-on (NCS 3.x successor)** `external-mcu.overlay` (nRF9151 DK pin-compatible) | uart2 | **P0.02** | **P0.03** | **P0.06** | **P0.07** | **P0.31 DTR** (level, active-low, pull-up) | **P0.30 RI** (level, active-low) |

Sources:
- https://raw.githubusercontent.com/nrfconnect/sdk-nrf/v2.9.0/applications/serial_lte_modem/boards/nrf9161dk_nrf9161_ns.overlay and the `.conf` next to it. Fetched 2026-10-13. SLM no longer exists on sdk-nrf `main`.
- https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/applications/serial_lte_modem/doc/slm_description.html (NCS 3.1.99 docs)
- https://nrfconnectdocs.nordicsemi.com/addons/addon-serial_modem/latest/main/app/sm_build_and_run.html
- https://nrfconnectdocs.nordicsemi.com/addons/addon-serial_modem/latest/main/releases/migration_notes_ncs_slm_v3.1.x.html: DTR/RI replace the Power/Indicate pins, and `nrf9161dk` support was removed ("use nrf9151dk instead").

**Proposal: adopt the Serial Modem add-on `external-mcu.overlay` pin set** (P0.02/03/06/07 + DTR P0.31 + RI P0.30). That is the maintained path. Those six U1 pads all sit on the south/east edge, next to ENABLE and nRESET:

| Signal | U1 pad | XY at 067291f (mm) | edge |
|---|---|---|---|
| P0.06 | 3 | (43.75, 36.0) | east |
| P0.07 | 4 | (43.75, 35.5) | east |
| P0.02 | 97 | (40.75, 37.0) | south |
| P0.03 | 99 | (41.75, 37.0) | south |
| P0.30 | 88 | (36.25, 37.0) | south |
| P0.31 | 89 | (36.75, 37.0) | south |
| ENABLE | 101 | (42.75, 37.0) | south |
| nRESET | 32 | (38.25, 27.0) | north |

All are outer-ring pads, so they escape on a fresh layout. (The PASS30 escape problems came from the dense breakout fan-out, which v2 removes. This needs to be re-verified in layout.)

Legacy SLM pins (P0.10–P0.13) would also work: they are east-edge pads 18/19/20/23. But they need a different overlay, and P0.13 is AIN0.

Firmware: build the Serial Modem with `-DEXTRA_DTC_OVERLAY_FILE=external-mcu.overlay`, plus a custom board for this module, or nrf9151dk-based, since nRF9161 DK support was dropped. Keep `hw-flow-control` and `dtr-gpios = <&gpio0 31 (GPIO_PULL_UP|GPIO_ACTIVE_LOW)>`, `ri-gpios = <&gpio0 30 GPIO_ACTIVE_LOW>`, exactly as in the cited overlay. Verify against the add-on version actually used.

## 2. Host header J20 (1×12, 2.54 mm), host-view names

| # | Host name | nRF9161 signal | U1 pad | Dir (host view) | Level | Notes |
|---|---|---|---|---|---|---|
| 1 | VIN | VIN (D1 → F1 → FB4 → VIN_FILT → R2/JP1 → VDD_nRF) | — | power in | 3.0–5.5 V | PS VDD range 3.0–5.5 V. Replaces J1. |
| 2 | GND | GND | — | — | — | |
| 3 | VIO | translator VCCA (U5–U8), R21/R22 pull-ups | — | power in (ref) | 1.1–5.5 V (LXC range: verify) | Host's logic rail. Not a supply output. |
| 4 | HOST_TX | P0.03 = modem UART RX | 99 | out | VIO | via U5 |
| 5 | HOST_RX | P0.02 = modem UART TX | 97 | in | VIO | via U6 |
| 6 | HOST_RTS | P0.07 = modem CTS | 4 | out | VIO | via U5 |
| 7 | HOST_CTS | P0.06 = modem RTS | 3 | in | VIO | via U6 |
| 8 | HOST_DTR (wake) | P0.31 DTR | 89 | out, active-low | VIO | via U7. R21 100k to VIO, so the default is deasserted. |
| 9 | HOST_RI | P0.30 RI | 88 | in, active-low | VIO | via U8 |
| 10 | HOST_nRESET | nRESET | 32 | out, open-drain, active-low | host pulls low only | Through Q1 (gate = VDD_GPIO), R22 10k to VIO. 5 V-safe. |
| 11 | HOST_PWR_OFF | ENABLE (pin 101) | 101 | out, active-high | ≥ Q2 Vgs(th) | Q2 pulls ENABLE low (= SiP off; U2 off too, since U2.EN = ENABLE). R20 pulls down, so the default is ON. |
| 12 | GND | GND | — | — | — | |

Optional (see Q3): a 3V3 output (VDD_GPIO) pin is deliberately not included. U2 TLV73333 also powers the SiP GPIO rail, so its spare capacity is unverified.

## 3. Level translation: recommendation

VDD_GPIO range per the PS is **1.7–3.6 V**, and VDD_GPIO must come up after VDD/ENABLE and be low whenever ENABLE is low. Source: https://docs.nordicsemi.com/r/bundle/ps_nrf9161/page/recommended_op_conditions.html.

| Option | Pros | Cons |
|---|---|---|
| A. Feed VDD_GPIO from host VIO, no translator | Zero parts | Can't take 5 V hosts. Violates the PS sequencing rules whenever the host rail is up while VIN/ENABLE is not, which is likely on a module. Rejected. |
| B. TXB0104 (auto-direction) | One IC, 4 ch | Weak drive. Misbehaves with pull-ups/RC loads. Can't do the open-drain RESET. |
| C. TXS0104E | Built-in pull-ups, open-drain capable | Slow edges and pull-up loading on push-pull UART. 5 V side must be the higher-rail side (fixed orientation). |
| D. LSF0204 | Bidirectional, open-drain capable | Needs VREF_A < VREF_B. The host VIO can be above or below 3.3 V, so the orientation is not fixed. Rejected. |
| **E. SN74LXC2T45 ×2 + SN74LXC1T45 ×2 (fixed direction), Q1 OD isolator, Q2 for ENABLE** | Each side 1.1–5.5 V independently (verify datasheet), so 1.8/3.3/5 V hosts all work. Push-pull and clean for UART + RTS/CTS. DIR is fixed per signal, and UART signals are unidirectional. | 4 ICs + decoupling. |

**Recommended: E.**
- VDD_GPIO stays at 3.3 V from U2 (TLV73333), which already meets the sequencing rules because U2.EN = ENABLE.
- nRESET is not driven push-pull, because SW2 and the SWD probe also drive it. It uses BSS138-style FET isolation (gate at VDD_GPIO), so the host only ever pulls low and 5 V never reaches the SiP.
- ENABLE sits in the VDD1/VIN domain (R1 10k to VDD1, up to 5.5 V), so it is driven by Q2 (an NFET to GND). That makes HOST_PWR_OFF active-high. If Anand wants it active-low, it needs a second FET (Q4).

## 4. Part list: before → after

Before (067291f schematic):
- **104 symbols**: 74 fitted + in BOM, 8 DNP (C21–C24, C31, C32, D7, J16), 22 excluded from BOM (JP1, JP2, TP1–TP20).
- **BOM.csv: 85 rows** (TP1–TP20 share 1 row).

After:
- **91 symbols** (104 − 31 removed + 18 new).
- Fitted + in BOM: 55 kept + 18 new = **73 placements**.
- 6 DNP kept (C21–C24, C31, C32).
- 12 no-BOM pads/jumpers kept (JP1, JP2, TP7, TP8, TP9, TP13, TP14, TP15, TP16, TP17, TP19, TP20).
- **BOM.csv: ~75 rows** (85 − 21 removed rows + 11 new rows; C41–C48 share one row).

Assembled placements barely drop (74 → 73), because the translator adds about as many parts as the LEDs and buttons removed. The big savings are the **11 through-hole headers (J1, J9–J18; 70 pins)**, board area, and routing (the remaining PCB opens were all GPIO breakout fan-out).

| Ref | Value | MPN | Status | Reason |
|---|---|---|---|---|
| C1 | 10uF/16V | GRM21BR61C106ME15 | KEEP | decoupling/filter |
| C2 | 100nF | GRM155R61A104KA01 | KEEP | decoupling/filter |
| C3 | 47uF/10V | GRM21BR61A476ME15 | KEEP | decoupling/filter |
| C4 | 4.7uF | GRM155R61A475MEAA | KEEP | decoupling/filter |
| C5 | 100nF | GRM033R61A104KE15 | KEEP | decoupling/filter |
| C6 | 15pF | GJM0335C1E150JB01 | KEEP | decoupling/filter |
| C7 | 47uF/10V | GRM21BR61A476ME15 | KEEP | decoupling/filter |
| C8 | 4.7uF | GRM155R61A475MEAA | KEEP | decoupling/filter |
| C9 | 100nF | GRM033R61A104KE15 | KEEP | decoupling/filter |
| C10 | 15pF | GJM0335C1E150JB01 | KEEP | decoupling/filter |
| C11 | 4.7uF | GRM155R61A475MEAA | KEEP | decoupling/filter |
| C12 | 100nF | GRM033R61A104KE15 | KEEP | decoupling/filter |
| C13 | 4.7uF | GRM155R61A475MEAA | KEEP | decoupling/filter |
| C14 | 100nF | GRM033R61A104KE15 | KEEP | ENABLE decoupling |
| C21 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C22 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C23 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C24 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C27 | 100pF | GJM0335C1E101JB01 | KEEP | decoupling/filter |
| C28 | 100pF | GRM155R71H101KA01 | KEEP | decoupling/filter |
| C29 | 10nF | GRM155R71H103KA01 | KEEP | decoupling/filter |
| C30 | 100nF | GRM155R61A104KA01 | KEEP | decoupling/filter |
| C31 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C32 | DNP | GJM1555C1H100JB01 | KEEP (DNP) | DNP noBOM decoupling/filter |
| C33 | 100nF | GRM155R61A104KA01 | KEEP | decoupling/filter |
| C34 | 220nF | GRM155R61A224KE01 | KEEP | decoupling/filter |
| C35 | 22pF | GRM0335C1E220JA01 | KEEP | decoupling/filter |
| C36 | 22pF | GRM0335C1E220JA01 | KEEP | decoupling/filter |
| C37 | 22pF | GRM0335C1E220JA01 | KEEP | decoupling/filter |
| C38 | 22pF | GRM0335C1E220JA01 | KEEP | decoupling/filter |
| C39 | DNP | GRM033R61A104KE15 | KEEP | nRESET cap (BOM says DNP; the schematic has no DNP flag, see open questions) |
| C40 | 100nF | GRM155R71A104KA01D | KEEP | decoupling/filter |
| D1 | PMEG4030ER | PMEG4030ER | KEEP | reverse-polarity |
| D2 | SMAJ5.0A | SMAJ5.0A | KEEP | VIN TVS |
| D3 | Green LED | KP-2012SGC | KEEP | power LED |
| D4 | Green LED | KP-2012SGC | KEEP | STATUS LED (P0.00) |
| D5 | Green LED | KP-2012SGC | REMOVE | LTE LED (P0.01): not needed in the modem role |
| D6 | Green LED | KP-2012SGC | REMOVE | GNSS LED (P0.02): not needed; P0.02 becomes modem UART TX |
| D7 | Green LED | KP-2012SGC | REMOVE | DNP noBOM Spare LED (P0.03): P0.03 becomes modem UART RX |
| F1 | 2A | 0468002.NR | KEEP | VIN fuse |
| FB1 | BLM18KG221SN1 | BLM18KG221SN1D | KEEP | decoupling/filter |
| FB2 | BLM18KG221SN1 | BLM18KG221SN1D | KEEP | decoupling/filter |
| FB3 | BLM18KG221SN1 | BLM18KG221SN1D | KEEP | decoupling/filter |
| FB4 | BLM18PG221SN1 | BLM18PG221SN1D | KEEP | decoupling/filter |
| FB5 | BLM15HG102SN1 | BLM15HG102SN1D | KEEP | GNSS bias filter |
| J1 | VIN_3V0-5V5 | 61300211121 | REMOVE | VIN header: VIN moves onto the host header |
| J2 | U.FL_LTE_NR+ | U.FL-R-SMT-1(10) | KEEP | LTE U.FL |
| J3 | SWF_LTE | MM8130-2600 | KEEP | LTE SWF (Optional) |
| J5 | U.FL_GNSS | U.FL-R-SMT-1(10) | KEEP | GNSS U.FL |
| J6 | SWF_GNSS | MM8130-2600 | KEEP | GNSS SWF (Optional) |
| J7 | nanoSIM_4FF | SF72S006V4BR | KEEP | nano-SIM |
| J8 | SWD_10pin | FTSH-105-01-L-DV | KEEP | SWD flashing |
| J9 | UART0 | 61300611121 | REMOVE | UART0 breakout |
| J10 | SPI0 | 61300611121 | REMOVE | SPI0 breakout |
| J11 | I2C0 | 61300411121 | REMOVE | I2C0 breakout |
| J12 | GPIO_P0.00-15 | 61302011121 | REMOVE | GPIO breakout |
| J13 | GPIO_P0.16-31 | 61302011121 | REMOVE | GPIO breakout |
| J14 | RFFE_MAGPIO | 61300611121 | REMOVE | MAGPIO/MIPI RFFE breakout (no external FEM) |
| J15 | COEX | 61300611121 | REMOVE | COEX breakout (COEX0 still drives U3) |
| J16 | I2S | 61300611121 | REMOVE | DNP noBOM I2S (already DNF) |
| J17 | PDM | 61300411121 | REMOVE | PDM breakout |
| J18 | ADC_AIN0-7 | 61301011121 | REMOVE | ADC breakout |
| JP1 | I_MEAS | solder jumper | KEEP | noBOM I_MEAS jumper |
| JP2 | SIM_VCC | solder jumper | KEEP | noBOM SIM_VCC jumper |
| L1 | 0R / DNP match | LQW15AN10NG00 | KEEP | LTE match |
| L2 | 0R / DNP match | LQW15AN10NG00 | KEEP | AUX match |
| L4 | 100nH | LQW15ANR10J00 | KEEP | GNSS bias-T |
| R1 | 10k | RC0201FR-0710KL | KEEP | ENABLE pull-up |
| R2 | 0.05 | PE1206FRF070R05L | KEEP | current shunt |
| R3 | 1k | RC0402FR-071KL | KEEP | power LED resistor |
| R4 | 0R | RC0402JR-070RL | REMOVE | COEX0 -> GNSS_LNA_EN sense, only feeds TP2 |
| R5 | 1k | RC0201FR-071KL | KEEP | RESET button series |
| R10 | 1k | RC0402FR-071KL | KEEP | D4 series resistor |
| R11 | 1k | RC0402FR-071KL | REMOVE | D5 series resistor |
| R12 | 1k | RC0402FR-071KL | REMOVE | D6 series resistor |
| R13 | 1k | RC0402FR-071KL | REMOVE | D7 series resistor |
| R14 | 10k | RC0402FR-0710KL | REMOVE | USER button pull-up |
| SW1 | DISABLE | KXT311LHS | REMOVE | DISABLE button: replaced by host HOST_PWR_OFF (ENABLE) + TP17 |
| SW2 | RESET | KXT311LHS | KEEP | RESET |
| SW3 | USER | KXT311LHS | REMOVE | USER button on P0.08 (only used as the PC-terminal power pin in SLM) |
| TP1 | AUX | 5015 | REMOVE | noBOM AUX_FIT pad (see open questions) |
| TP2 | LNA_EN | 5015 | REMOVE | noBOM LNA_EN sense pad |
| TP3 | SIM_CLK | 5015 | REMOVE | noBOM SIM_CLK pad |
| TP4 | SIM_RST | 5015 | REMOVE | noBOM SIM_RST pad |
| TP5 | SIM_IO | 5015 | REMOVE | noBOM SIM_IO pad |
| TP6 | SIM_CD | 5015 | REMOVE | noBOM SIM_CD pad |
| TP7 | SWDIO | 5015 | KEEP | noBOM bring-up test pad |
| TP8 | SWCLK | 5015 | KEEP | noBOM bring-up test pad |
| TP9 | nRESET | 5015 | KEEP | noBOM bring-up test pad |
| TP10 | VDD_GPIO | 5015 | REMOVE | noBOM duplicate of TP13 VDD_GPIO |
| TP11 | VDD1 | 5015 | REMOVE | noBOM VDD1 pad (VDD1 = VDD_nRF through FB1) |
| TP12 | VDD2 | 5015 | REMOVE | noBOM VDD2 pad |
| TP13 | VDD_GPIO | 5015 | KEEP | noBOM bring-up test pad |
| TP14 | VDD_nRF | 5015 | KEEP | noBOM bring-up test pad |
| TP15 | VIN | 5015 | KEEP | noBOM bring-up test pad |
| TP16 | GND | 5015 | KEEP | noBOM bring-up test pad |
| TP17 | ENABLE | 5015 | KEEP | noBOM bring-up test pad |
| TP18 | DEC0 | 5015 | REMOVE | noBOM DEC0 pad |
| TP19 | I_MEAS+ | 5015 | KEEP | noBOM bring-up test pad |
| TP20 | I_MEAS- | 5015 | KEEP | noBOM bring-up test pad |
| U1 | NRF9161-LACA-R7 | nRF9161-LACA-R7 | KEEP | modem SiP |
| U2 | TLV73333PDBV | TLV73333PDBVR | KEEP | VDD_GPIO 3.3 V LDO (EN=ENABLE keeps PS sequencing) |
| U3 | TPS22919DCKR | TPS22919DCKR | KEEP | GNSS active-antenna bias switch (COEX0) |
| U4 | TPD3F303DPV | TPD3F303DPVR | KEEP | SIM ESD |

New parts (refs proposed):

| Ref | Value | MPN | Status | Reason |
|---|---|---|---|---|
| J20 | HOST 1x12 2.54 mm | TBD (Würth WR-PHD 1x12, e.g. 61301211121: verify) | NEW | host header |
| U5 | SN74LXC2T45 | SN74LXC2T45DCUR (verify pkg) | NEW | HOST_TX + HOST_RTS, host->modem (DIR fixed) |
| U6 | SN74LXC2T45 | SN74LXC2T45DCUR (verify pkg) | NEW | HOST_RX + HOST_CTS, modem->host (DIR fixed) |
| U7 | SN74LXC1T45 | SN74LXC1T45DBVR (verify) | NEW | HOST_DTR host->modem P0.31 |
| U8 | SN74LXC1T45 | SN74LXC1T45DBVR (verify) | NEW | HOST_RI modem P0.30->host |
| Q1 | BSS138-class NFET (Vgs(th)<=1.5 V) | TBD | NEW | HOST_nRESET open-drain isolator, gate=VDD_GPIO |
| Q2 | logic-level NFET (Vgs(th)<=1.0 V) | TBD | NEW | HOST_PWR_OFF: gate high pulls ENABLE low |
| R20 | 100k | RC0402FR-07100KL (verify) | NEW | Q2 gate pull-down (default: modem ON) |
| R21 | 100k | RC0402FR-07100KL (verify) | NEW | HOST_DTR pull-up to VIO (default deasserted = UART idle) |
| R22 | 10k | RC0402FR-0710KL (in BOM as R14) | NEW | HOST_nRESET pull-up to VIO (host side of Q1) |
| C41-C48 | 100nF | GRM155R61A104KA01 (in BOM as C2) | NEW | VCCA/VCCB decoupling for U5-U8 (8 placements) |

Minimal bring-up test-point set kept:
- TP7 SWDIO, TP8 SWCLK, TP9 nRESET
- TP13 VDD_GPIO, TP14 VDD_nRF, TP15 VIN, TP16 GND
- TP17 ENABLE
- TP19/TP20 I_MEAS±

## 5. Firmware-facing changes vs README / docs/PINOUT.md

| Function | Current (067291f docs) | v2 |
|---|---|---|
| UART | UART0 TX P0.06 / RX P0.04 on J9, 2-wire | **uart2: TX P0.02, RX P0.03, RTS P0.06, CTS P0.07, hw-flow-control** |
| Power/wake | none (SW1 DISABLE on ENABLE) | **DTR P0.31** (Serial Modem). Legacy SLM `CONFIG_SLM_POWER_PIN=31` is the same pin. |
| Indicate | none | **RI P0.30**. Legacy `CONFIG_SLM_INDICATE_PIN=30` is the same pin. |
| LEDs | P0.00 STATUS, P0.01 LTE, P0.02 GNSS, P0.03 spare | **P0.00 STATUS only**. P0.02/P0.03 are reused for UART, so LED D6/D7 must be removed (firmware must not drive them as LEDs). |
| USER button | P0.08 | removed |
| Trace (P0.21–P0.25) | conflicts with SPI0/J10 | no conflict (J10 removed). J8.6 (P0.22) stays on SWD. |
| I2S / PDM / ADC / I2C / SPI headers | J9–J18 | removed. GPIOs become unbroken-out. |

Overlay delta from the add-on `external-mcu.overlay`:
- None for the UART/DTR/RI pins.
- Add a board LED alias on P0.00 if the status LED is wanted. The add-on's board overlays drive RI to an LED on the DKs.
- Remove the button DTR mapping.

## 6. Placement notes (two-sided)
- **Top:**
  - U1 and the entire RF chain (L1, L2, C21–C32, J2, J3, J5, J6, L4, FB5, U3)
  - SIM J7 + U4 + C33–C38/C40
  - Bulk caps C3/C7, D1/D2/F1/FB4
  - U1 decoupling (C4–C14), which must stay at the pins per the HDG
  - LEDs and SW2 for visibility
  - J20 and J8 (or J20 through-hole from the top)
- **Bottom candidates:**
  - Translators U5–U8 + C41–C48, Q1/Q2, R20–R22 (all small SMD, not RF)
  - U2 + C11/C12 if the area under U1 is free of RF
  - R1, R3, R5, R10, C39
  - Keep the bottom under U1's RF pads and the antenna feed clear, and keep the GND reference intact.
- **JLCPCB:**
  - Two-sided SMT is billed as two assembly passes. The second side adds its own setup fee and stencil.
  - Putting only passives + SOT/SC-70 parts on the bottom avoids a second side with fine-pitch parts. U5/U6 DCU packages are 0.5 mm pitch: verify JLC capability/stock.
  - A through-hole J20 adds a hand/wave-solder step. An SMD or castellated host edge is the alternative (Q5).
  - Exact JLC fees are not cited here: check the current price list.

## 7. Open questions for Anand
1. **Serial Modem add-on pins (P0.02/03/06/07, DTR/RI) vs legacy SLM P0.10–P0.13 + POWER/INDICATE?** This plan assumes the add-on (NCS ≥3.2). If you are pinned to NCS ≤3.1, the same hardware works with a custom overlay.
2. **HOST_PWR_OFF polarity:** active-high via 1 FET (proposed), or active-low (needs 2 FETs)? Or drop it and rely on DTR + `AT#XSLEEP`?
3. **3V3 output on the header?** U2's spare current is not established from the files.
4. **Keep the current-measurement path** (R2 0.05 Ω + JP1 + TP19/TP20) on a production module? Keep J3/J6 SWF test connectors (BOM: Optional)?
5. **AUX port:** L2 + TP1 (AUX_FIT). Is AUX used? The PS role was not re-checked in this plan. TP1 is marked REMOVE pending your answer.
6. **C39 (nRESET cap):** BOM.csv says DNP, but the schematic symbol has no DNP flag. Which is right?
7. **Host connector:** 1×12 through-hole vs castellated/SMD edge for a drop-in module? Board outline/size target?
8. **Part choices to confirm against the datasheet/stock:**
   - SN74LXC1T45/2T45 rail range and packages
   - Q1/Q2 exact MPNs (Vgs(th) at 1.8 V hosts)
   - J20 MPN
9. **Data mismatches noticed (no action taken):**
   - BOM C39 = DNP vs schematic fitted
   - BOM J14/J15 list 2.54 mm-series MPN 61300611121 for 1.27 mm headers (both removed in v2 anyway)
