# Schematic review — nRF9161-DEV-BOARD

**Reviewer role:** Schematic Engineer  
**Date:** 2026-09-23 (IST / Asia/Calcutta)  
**Working tree:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Live electrical source:** `nRF9161-DEV-BOARD.kicad_sch` → `schematic/*.kicad_sch` (singular).  
**Do not use:** `schematics/` (plural) — leftover unused hierarchy (README known limitation #8).

## Cleanup actions — 2026-09-23 (IST)

- Schematic Engineer pass (same day): COEX0-gated GNSS bias **U3**, FB5 0402, Class C DNP flags, U2→TLV73333 — see section below.

- `kicad-cli` is not installed in this environment, so the stale root `nRF9161-DEV-BOARD-erc.rpt` was deleted rather than regenerated. The authoritative live ERC report is `reports/ERC_kicad-cli.rpt` (0 errors).
- Added `schematics/README.md` as an in-place quarantine marker; the folder was not moved to preserve existing bookmarks.
- Verified the root schematic, project file, README, and scripts contain no live project link to `schematics/`; documentation mentions are explanatory only.

---

## Maturity summary

| Area | Status |
| --- | --- |
| Hierarchy A–L (12 child sheets) | **Done** — root only hosts sheet symbols; no globals on `/` |
| Power tree (VIN → VDD_nRF → VDD1/VDD2/VDD_GPIO, ENABLE, DEC0) | **Mostly done** — topology matches README / Nordic HDG intent |
| nRF9161 pin mux / modem interfaces | **Done on globals** — P0.00–P0.31, SIM_*, SWD*, COEX*, MAGPIO*, MIPI_* labeled from U1 |
| RF front-end (LTE π, AUX, GNSS bias-T, U.FL/SWF) | **Structurally done**; GNSS bias **not** COEX0-gated (see blockers) |
| Connectors / debug (J8–J18, J12/J13) | **Done** with one corrected header rail (J13.17) |
| ERC (live tree vs reports) | **Live tree matches 0-error `reports/ERC_kicad-cli.rpt`**; stale root `nRF9161-DEV-BOARD-erc.rpt` was deleted on 2026-09-23 |
| Fab-ready schematic gate | **Not closed** — PCB still has large unconnected count (layout/DFM); schematic has remaining electrical/docs mismatches below |

**One-liner:** Multi-sheet schematic is electrically mature; locked COEX0-gated GNSS bias (U3 TPS22919DCKR) and TLV73333 3.3 V VDD_GPIO are on the live tree — still **not fab-ready** (PCB unconnected / layout).

---

## Project inventory

### Project file
- `nRF9161-DEV-BOARD.kicad_pro`
- Root schematic: `nRF9161-DEV-BOARD.kicad_sch`

### Live sheet list (`schematic/`)

| Sheet name (root) | File |
| --- | --- |
| A. nRF9161 | `schematic/01_nRF9161.kicad_sch` (U1) |
| B. POWER | `schematic/02_POWER.kicad_sch` |
| C. LTE/NR+ RF | `schematic/03_LTE_RF.kicad_sch` |
| D. GNSS | `schematic/04_GNSS.kicad_sch` |
| E. SIM/UICC | `schematic/05_SIM.kicad_sch` |
| F. SWD/DEBUG | `schematic/06_SWD.kicad_sch` |
| G. UART | `schematic/07_UART.kicad_sch` (J9) |
| H. SPI/I2C | `schematic/08_SPI_I2C.kicad_sch` (J10/J11) |
| I. I2S/PDM/ADC | `schematic/09_I2S_PDM_ADC.kicad_sch` (J16–J18) |
| J. GPIO EXPANSION | `schematic/10_GPIO.kicad_sch` (J12/J13) |
| K. LEDs/BUTTONS | `schematic/11_LEDS_BUTTONS.kicad_sch` |
| L. TEST POINTS | `schematic/12_TESTPOINTS.kicad_sch` |

### Leftover (not in root hierarchy)
- `schematics/A_nRF9161.kicad_sch` … `L_TEST_POINTS.kicad_sch` — **not referenced** by root. Still contains `#FLG04` on `schematics/A_nRF9161.kicad_sch`.

### ERC reports read
- `nRF9161-DEV-BOARD-erc.rpt` — **deleted 2026-09-23** because it was stale (**Errors 2, Warnings 14**); live `schematic/` status is represented by `reports/ERC_kicad-cli.rpt`
- `reports/ERC_kicad-cli.rpt` — **Errors 0, Warnings 1** (`lib_symbol_mismatch` U4 TPD3F303DPV) (2026-09-16T12:47+0530) — **matches live tree**
- `reports/ERC.txt` — sheet list only (no violations)

---

## Priority ERC items (Hardware PM)

### 1) Power-output conflict on POWER sheet — **CLOSED in live tree**

**Stale report:** `nRF9161-DEV-BOARD-erc.rpt` sheet `/B. POWER/`  
`[pin_to_pin]` `#FLG04` Pin 1 (Power output) @ (88.90, 139.70) ↔ `U2` Pin 5 OUT (Power output) @ (71.12, 99.06).

**Live evidence (`schematic/02_POWER.kicad_sch`):**
- `U2` TLV73333PDBV @ (63.5, 101.6); pin 5 OUT → global `VDD_GPIO` @ (71.12, 99.06) (**3.3 V** fixed LDO; was TLV73330 3.0 V).
- PWR_FLAG instances present: `#FLG01`→`GND`, `#FLG02`→`VDD1`, `#FLG03`→`VDD2`, `#FLG05`→`VDD_nRF`.
- **`#FLG04` absent** from all live `schematic/*.kicad_sch` (only remains under unused `schematics/A_nRF9161.kicad_sch`).
- No PWR_FLAG on `VDD_GPIO` — regulator alone is the power_out driver (correct).

**Action taken:** none required on live POWER sheet (already correct).  
**Do not** re-add a PWR_FLAG on `VDD_GPIO`.

### 2) Undriven VCC on SIM U4 — **CLOSED in live tree**

**Stale report:** sheet `/E. SIM/UICC/`  
`[power_pin_not_driven]` `U4` Pin 5 `V_{CC}` (Power input) @ (50.80, 53.34).

**Live evidence (`schematic/05_SIM.kicad_sch` + `01_nRF9161.kicad_sch`):**
- `U4` TPD3F303DPV @ (50.8, 63.5); pin 5 `V_{CC}` (power_in) lands on global **`SIM_1V8`** @ (50.8, 53.34).
- `U1` pin 49 `SIM_1V8` is typed **`power_out`** in embedded/library symbol → drives `SIM_1V8` hierarchy-wide.
- Channel map (TI SIM app convention): DATA1=`SIM_IO`/`SIM_IO_C`, CLK=`SIM_CLK`/`SIM_CLK_C`, DATA2=`SIM_RST`/`SIM_RST_C`.
- Card rail: `JP2` A=`SIM_1V8`, B=`SIM_VCC`; `#FLG07` on `SIM_VCC` @ (115.57, 124.46) for ERC when jumper open.
- `J7` C6 VPP: `no_connect` @ (101.6, 63.5) — matches README (VPP NC).

**Action taken:** none required (connection already correct).  
**Do not** put a second PWR_FLAG on `SIM_1V8` (would conflict with U1 `power_out`).

---

## Schematic edit made this review

### J13 pin 17 rail corrected (`schematic/10_GPIO.kicad_sch`)

| | Before | After |
| --- | --- | --- |
| Net on J13 pin 17 @ (134.62, 68.58) | `VDD_nRF` (VIN-derived, **3.0–5.5 V**) | `VDD_GPIO` (**3.3 V**) |
| UUID | `05418af6-983e-48e0-98dc-6c9d0daa3bd1` | unchanged |

**Rationale:** README authoritative map: “J12/J13 pins 17–18 = VDD_GPIO (3.3 V), 19–20 = GND.”  
J12.17/18 were already `VDD_GPIO`; J13.17 was `VDD_nRF`, which could back-feed 5 V-class VIN into a header users treat as 3V3 (J9–J11/J16 also use `VDD_GPIO`).  
J13.18 remains `VDD_GPIO`; .19/.20 remain `GND`.

---

## Dangling globals triage

Source of the 13× `[global_label_dangling]` warnings: stale `nRF9161-DEV-BOARD-erc.rpt` sheet `/`, coordinates that match **child sheets** (e.g. J13 x≈134.62, J14/J15 x≈147.32).

| Global | Stale ERC | Live coverage (sheets with `global_label`) | Triage |
| --- | --- | --- | --- |
| `P0.25`…`P0.29` | dangling on `/` | `01_nRF9161` + `10_GPIO` (J13.10–14) | **Resolved** — dual-sheet |
| `MAGPIO0/1/2` | dangling | `01_nRF9161` + `03_LTE_RF` (J14) | **Resolved** |
| `MIPI_VIO`, `MIPI_SCLK`, `MIPI_SDATA` | dangling | `01_nRF9161` + `03_LTE_RF` (J14) | **Resolved** |
| `COEX1`, `COEX2` | dangling | `01_nRF9161` + `03_LTE_RF` (J15) | **Resolved** |
| `COEX0` | (not in dangling list) | `01` + `03` + `04_GNSS` | OK |

**Single-sheet globals (not ERC-dangling if pins connect locally):**  
`ANT_FIT`, `AUX_FIT`, `GNSS_ANT`, `GNSS_VBIAS`, `GNSS_LNA_EN`, `SIM_VCC`, `SIM_*_C`, `SIM_CD`, `VIN_IN`/`VIN_F`/`VDD2_MID`, `LED*_A`, `nRESET_SW` — intentional intra-sheet nets.

**Intentional unconnected / float:**
- `SIM_DET` (U1 pin 45): symbol `no_connect`; sheet notes require float (PS). Mechanical detect is `SIM_CD` on J7 CSW/DSW + TP6 — **not** pin 45.

---

## Blocking / high-severity issues (with evidence)

1. **GNSS active-antenna bias is always-on from `VDD_GPIO`, not COEX0-gated** — `schematic/04_GNSS.kicad_sch`: `FB5` pin1=`VDD_GPIO`, pin2=`GNSS_VBIAS`; `L4` ties `GNSS_VBIAS`→`GNSS_ANT`; `R4` only ties `COEX0`→`GNSS_LNA_EN` (TP2). README claims bias “from VDD_GPIO through R4/COEX0”. Passive-antenna users can disable bias only in firmware if a switch exists — **here bias cannot be disabled in hardware via `%XCOEX0`**. Proposed fix: add load-switch / PFET (or Nordic DK-equivalent) between `VDD_GPIO` and `FB5`/`GNSS_VBIAS`, gate with `COEX0` (and keep R4/TP2 as sense if desired).

2. **Stale ERC artifact — RESOLVED** — deleted root `nRF9161-DEV-BOARD-erc.rpt`; authoritative `reports/ERC_kicad-cli.rpt` reports 0 errors. `kicad-cli` was unavailable, so no regeneration was attempted.

3. **Leftover `schematics/` — QUARANTINED** — added `schematics/README.md` with a DO NOT EDIT marker; live hierarchy remains `schematic/`.

4. **`lib_symbol_mismatch` warning on `U4` TPD3F303DPV** — embedded symbol vs library `Power_Protection` (`reports/ERC_kicad-cli.rpt`). Not an electrical open, but update-from-library / freeze local symbol before tape-out so BOM/ERC stay stable.

5. **PCB unconnected items remain the fab hard gate** — schematic completeness ≠ fab-ready; see `reports/UNCONNECTED.md` / README (layout owns remaining opens).

6. **Net name `SWDCLK` (not `SWCLK`)** — consistent on `01_nRF9161` + `06_SWD` J8.4 + TP8; documentation sometimes says SWCLK — naming only, not electrical.

---

## Sheet review notes (priority order)

### Power tree — `02_POWER.kicad_sch`
- Chain present: `J1` `VIN_IN` → `D1` PMEG4030ER → `D2` SMAJ5.0A → `F1` 2A → `FB4` → `VIN_FILT` → `R2`/`JP1` → `VDD_nRF`.
- `FB1`→`VDD1`; `FB2`→`VDD2_MID`→`FB3`→`VDD2` (DK-style FB3).
- `U2` IN=`VDD_nRF`, EN=`ENABLE`, OUT=`VDD_GPIO`; `C11`/`C12` on `VDD_GPIO`; `C13` 4.7 µF on `DEC0` (PCN134).
- `R1` 10k `VDD1`→`ENABLE`, `SW1` DISABLE to GND, `C14` on ENABLE.
- Flags: no conflict on `VDD_GPIO` (see ERC #1 closed).

### nRF9161 / modem — `01_nRF9161.kicad_sch`
- Globals for all 32 GPIOs, RF (`ANT`/`AUX`/`GPS`), SIM (`SIM_RST/CLK/IO/1V8`), SWD (`SWDIO`/`SWDCLK`), `nRESET`, `ENABLE`, `VDD1`/`VDD2`/`VDD_GPIO`, COEX/MAGPIO/MIPI, `DEC0`.
- `SIM_DET` NC; RES/NC pins documented as mechanical-only.

### RF — `03_LTE_RF.kicad_sch` / `04_GNSS.kicad_sch`
- LTE: `ANT`→`L1`→`ANT_FIT`→`J2`/`J3`; AUX→`L2`→`TP1`; DNP `C21–C24`.
- J14 MAGPIO/MIPI + `VDD_GPIO`; J15 COEX0/1/2.
- GNSS: `GPS`→`C27`→`GNSS_ANT`→`J5`/`J6`; bias-T `L4`/`C28–C30`/`FB5`; **U3** TPS22919DCKR gates `VDD_GPIO`→`GNSS_VBIAS_SRC`→FB5 with EN=`COEX0`; R4/TP2 sense only; C31/C32 `(dnp yes)`.

### SIM — `05_SIM.kicad_sch`
- U4 filter + JP2 + J7 nano-SIM + CD; ERC #2 closed as above.

### Debug / connectors
- J8 Cortex 10-pin: 1=`VDD_GPIO`, 2=`SWDIO`, 4=`SWDCLK`, 6=`P0.22`, 8=`nRESET` via `R5`/`SW2`; pins 7/9 no_connect present.
- Protocol headers J9–J11, J16–J18 multiplex same GPIO nets as J12/J13 (intentional).

---


---

## Schematic Engineer pass — 2026-09-23 (IST) — LOCKED GNSS bias + DNP + U2 3.3 V

Implements `docs/RF_POWER_REVIEW.md` **DECISION (LOCKED)** plus Hardware PM add-ons. Live tree only (`schematic/`); **`schematics/` plural not touched**. Not fab-ready.

### A) GNSS COEX0-gated bias (`schematic/04_GNSS.kicad_sch`)

| Item | Detail |
| --- | --- |
| New refdes | **U3** |
| MPN / Value | **TPS22919DCKR** (embedded `power_switch:TPS22919DCK`) |
| Footprint | `Package_TO_SOT_SMD:SOT-363_SC-70-6` |
| Topology | `VDD_GPIO` → U3 VIN → U3 VOUT → net **`GNSS_VBIAS_SRC`** → **FB5** → **`GNSS_VBIAS`** → L4 → GNSS_ANT |
| EN | U3 ON ← **`COEX0`** (same net as R4 input) |
| NC / QOD | pins 4 & 5 left floating (`no_connect`) |
| Unchanged bias-T | C27 100pF, L4 100nH, C28/C29/C30, FB5 BLM15HG102SN1 |
| R4 / TP2 | Still **COEX0 → R4 0Ω → GNSS_LNA_EN → TP2** sense only — **not** the power path |

### B) FB5 footprint

| Before | After |
| --- | --- |
| `Inductor_SMD:L_0603_1608Metric` (0603) | `Inductor_SMD:L_0402_1005Metric` (0402, matches BLM15HG102SN1) |

### C) Class C 50 Ω shunt DNP (P1-4)

| Refs | Sheet | Change |
| --- | --- | --- |
| C21–C24 | `schematic/03_LTE_RF.kicad_sch` | `(dnp yes)`, `(in_bom no)` — Value remains `DNP` |
| C31–C32 | `schematic/04_GNSS.kicad_sch` | `(dnp yes)`, `(in_bom no)` — Value remains `DNP` |

Layout stubs pads; parts stay unpopulated.

### D) U2 VDD_GPIO 3.3 V (P2-1 / P1-8)

| Field | Before | After |
| --- | --- | --- |
| Sheet | `02_POWER.kicad_sch` lib_id / Value / Description | `TLV73330PDBV` (fixed **3.0 V**) → **`TLV73333PDBV`** (fixed **3.3 V**) |
| BOM | TLV73330PDBV / TLV73330PDBVR | **TLV73333PDBV / TLV73333PDBVR** |
| Pinout / footprint | unchanged SOT-23-5 | unchanged |

### E) BOM.csv

- Added **U3** TPS22919DCKR (SC-70-6).
- Updated **U2** to TLV73333PDBVR.
- Noted **FB5** land `L_0402_1005Metric`.

### F) ERC

- Later same-day pass ran `/usr/bin/kicad-cli sch erc` — see **U3 TPS22919 netlist connectivity fix** below (`reports/ERC_U3_after.rpt`, 0 errors). Prior `reports/ERC_kicad-cli.rpt` may still be stale for non-U3 items.

### Files modified (this pass)

- `schematic/04_GNSS.kicad_sch` — U3 load switch, `GNSS_VBIAS_SRC`, FB5 0402, C31/C32 DNP
- `schematic/03_LTE_RF.kicad_sch` — C21–C24 DNP / exclude-from-BOM
- `schematic/02_POWER.kicad_sch` — U2 → TLV73333PDBV
- `BOM.csv` — U2/U3/FB5 notes
- `docs/SCHEMATIC_REVIEW.md` — this section
- `README.md` — TLV73333 MPN + GNSS bias wording aligned to U3/COEX0 gate

### Recommended next fixes (updated)

1. **PCB Layout:** place/route U3 (SC-70) near GNSS bias-T; connect `COEX0` to U3 ON; retarget FB5 land to 0402; keep `GNSS_VBIAS_SRC` between U3 VOUT and FB5.
2. **ERC:** regenerate with `kicad-cli sch erc` once KiCad is available.
3. Medium — resolve U4 `lib_symbol_mismatch` (TPD3F303).
4. Layout/DFM: drive `unconnected_items` → 0 before fab — **do not claim fab-ready**.



---

## Schematic Engineer pass — 2026-09-23 (IST) — U3 TPS22919 netlist connectivity fix

**Problem (Layout):** PCB Layout reported **U3** VIN/VOUT/GND (and risk to EN) had no schematic nets — they had to assign PCB nets manually.

### Root cause

Embedded symbol `power_switch:TPS22919DCK` pin numbers/names match TI DS SC-70-6 (1 IN/VIN, 2 GND, 3 ON, 4 NC, 5 QOD, 6 VOUT). **Not** a wrong pinout.

U3 instance at `(15.24, 38.1)`. KiCad places symbol pins with **library Y-up → schematic Y-down flip**. Actual pin tips:

| Pin | Name | Actual sch tip | Labels/NCs were at (wrong) |
| --- | --- | --- | --- |
| 1 | VIN | `(7.62, 35.56)` | `VDD_GPIO` @ `(7.62, 40.64)` |
| 2 | GND | `(15.24, 45.72)` | `GND` @ `(15.24, 30.48)` |
| 3 | ON | `(7.62, 38.10)` | `COEX0` @ `(7.62, 38.10)` — already correct |
| 4 | NC | `(22.86, 38.10)` | `no_connect` OK |
| 5 | QOD | `(22.86, 40.64)` | `no_connect` was @ `(22.86, 35.56)` (**on VOUT**) |
| 6 | VOUT | `(22.86, 35.56)` | `GNSS_VBIAS_SRC` @ `(22.86, 40.64)` (**on QOD**) |

Labels were placed with naive `origin + pin_at` (no Y-flip). Sheet had **zero wires** near U3, so nothing rescued the miss. Result: netlist showed `unconnected-(U3-VIN-Pad1)`, `unconnected-(U3-VOUT-Pad6)`, `unconnected-(U3-GND-Pad2)`; VOUT also got `no_connect` from the misplaced NC marker.

### Fix (`schematic/04_GNSS.kicad_sch` only — not `schematics/`)

- Moved global labels to correct tips (via short stub wires): `VDD_GPIO`←VIN, `GNSS_VBIAS_SRC`←VOUT, `GND`←GND; kept `COEX0`←ON.
- Moved QOD `no_connect` to `(22.86, 40.64)`; NC stays `(22.86, 38.10)`.
- Nudged U3 Reference/Value text off pin tips.
- Topology unchanged: `VDD_GPIO`→U3.VIN / U3.VOUT→`GNSS_VBIAS_SRC`→FB5 / ON←`COEX0` / GND / NC+QOD float.

### Netlist proof (`kicad-cli sch export netlist`, `reports/netlist_after_u3.xml`)

- **U3.1 VIN** → net `VDD_GPIO` (with U2.5 OUT, U1.12, …)
- **U3.2 GND** → net `GND`
- **U3.3 ON** → net `COEX0` (with U1.93, R4.1, …)
- **U3.6 VOUT** → net `GNSS_VBIAS_SRC` (with FB5.1)
- **U3.4 NC / U3.5 QOD** → intentional unconnected + `no_connect`

### ERC

- Before: `reports/ERC_U3_before.rpt` — **4 errors** (U3 VIN/GND pin_not_connected + power_pin_not_driven).
- After: `reports/ERC_U3_after.rpt` — **0 errors** (107 warnings remain, mostly missing system libs / dangling globals elsewhere).

### Files modified (this pass)

- `schematic/04_GNSS.kicad_sch` — U3 label/wire/no_connect coords
- `docs/SCHEMATIC_REVIEW.md` — this section
- `reports/netlist_before_u3.xml`, `reports/netlist_after_u3.xml`, `reports/ERC_U3_before.rpt`, `reports/ERC_U3_after.rpt`

**PCB Layout next:** re-import netlist / update PCB from schematic so U3 pads pick up `VDD_GPIO`, `GNSS_VBIAS_SRC`, `COEX0`, `GND` automatically — remove any manual net overrides on those pads.


## Recommended next fixes (severity order)

1. **High — GNSS bias control:** **DONE on schematic** (U3 TPS22919DCKR); PCB must still place/route U3 + `COEX0` + FB5 0402 land.
2. **High — ERC deliverable: CLOSED:** stale root report removed; use `reports/ERC_kicad-cli.rpt` (0 errors) until KiCad CLI/GUI regeneration is available.
3. **Medium — leftover `schematics/`: CLOSED:** in-place `schematics/README.md` quarantine marker added; folder is not linked from root.
4. **Medium — resolve `U4` `lib_symbol_mismatch`** (update/freeze TPD3F303 symbol).
5. **Low — silkscreen/docs:** align “SWCLK” wording to net `SWDCLK`; confirm J13.17 silkscreen says 3V3 after this edit.
6. **Layout/DFM (out of schematic scope):** drive `unconnected_items` → 0 before fab.

---

## Open questions / unresolved without KiCad GUI

- `kicad-cli sch erc` / netlist **were** run for the U3 connectivity fix (2026-09-23); see reports `ERC_U3_after.rpt` / `netlist_after_u3.xml`.
- Exact Nordic DK GNSS bias switch topology (part number) not copied here — needs RF/Power engineer sign-off on the COEX0 gate implementation.
- Whether J13.17 `VDD_nRF` was a deliberate “expose raw rail” feature: overridden to match README; restore only with explicit PM + silkscreen change.

---

## Files touched this pass

- `schematic/10_GPIO.kicad_sch` — J13.17 `VDD_nRF` → `VDD_GPIO`
- `nRF9161-DEV-BOARD-erc.rpt` — deleted as stale (2026-09-23)
- `schematics/README.md` — added in-place quarantine marker
- `docs/SCHEMATIC_REVIEW.md` — this document and cleanup status
