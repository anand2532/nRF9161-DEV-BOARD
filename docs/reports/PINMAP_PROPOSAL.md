> **STATUS: APPLIED to schematic 2026-10-12 (Tier 1: J9 2-wire, J16 DNF) per Hardware PM ruling. The PCB is not yet updated (needs Update-PCB-from-Schematic). ERC was not run: kicad-cli is unavailable. See docs/SCHEMATIC_REVIEW.md.**

# PINMAP_PROPOSAL — header ↔ U1 GPIO remap (PLAN ONLY)

- HEAD `57c4af7029a5a20c6eb346a9f9c54a4191dd3d4b` (matches expected 57c4af7). Nothing edited, nothing committed.
- PCB sha256 `3d02049d…82ed4`, read-only. Live schematic tree is `schematic/`.
- **kicad-cli is not installed on the box** (`/usr/bin/kicad-cli` is missing and there is no pcbnew python), so no fresh DRC was run. The open list comes from `reports/DRC_PASS30CA_BEFORE.json` (2026-10-12 12:27 IST). PASS30BZ/CA reverted to this same board blob. It shows **43 unconnected: 12 GND zone islands + 31 non-GND**.
- Pad and header XY were parsed straight from `nRF9161-DEV-BOARD.kicad_pcb` (footprint at/rot + pad offset).
- **Locked state:** the PCB has **no `(locked yes)` tracks or vias**. Below, "locked" means the PASS30 process lock: nets with 0 opens, whose routes are kept as-is.

## 0. Key finding (read first)
Every one of the 32 GPIOs is already on J12/J13, and there are **no spare GPIOs**. A permutation of header pins therefore cannot cut the U1-side opens: each GPIO still has to reach *some* header pin, and every function header (J9/J10/J11/J16/J17) sits at x=108–116, ≥60 mm from U1 (U1 body x28–44, y26.75–37.25).

A remap only removes the **header-to-header fan-out opens**. It does that by giving each net one header (de-duplication) and by moving a function onto a GPIO whose leg to that header is already routed. Getting to 0 opens also needs routing unlocks or header moves (section 4).

## 1. Proposed table

U1 pad XY is on F.Cu. "Escapable" means the PASS30AW exit list, refined by the PASS30BS class.

| header pin | old net | new net | U1 pad (num, XY, escapable?) | why |
|---|---|---|---|---|
| J9.4 (116.0,15.62) | P0.04 UART **CTS** | P0.04 UART **RX** (relabel only) | U1.100 (42.25,37.25), routed | P0.04 J9 leg is already routed. Moving RX here avoids the open J9.2 leg. |
| J9.2 (116.0,10.54) | P0.07 UART RX | **NC** (or GND) | U1.4 (44.0,35.5), exit OK | Fixes the D open P0.07↔J9.2 (58.6 mm). P0.07 stays on J12.8, which is routed. |
| J9.3 (116.0,13.08) | P0.05 UART RTS | **NC** | U1.2 (44.0,36.5), exit OK | Fixes the D open P0.05↔J9.3 (63.2 mm, ~125 mm In1). P0.05 stays on J12.6, which is routed. |
| J9.1 (116.0,8.0) | P0.06 TX | unchanged | U1.3 (44.0,36.0), routed | locked |
| J16.1 (108.0,8.0) | P0.10 I2S SCK | **NC / J16 DNP** | U1.18 (44.0,28.5), exit OK (stub only) | Fixes D open (63.2 mm). I2S stays on J12.11. |
| J16.2 (108.0,10.54) | P0.11 LRCK | **NC / DNP** | U1.19 (44.0,28.0), routed to J12.12 | Fixes D open (59.5 mm). |
| J16.3 (108.0,13.08) | P0.12 SDOUT | **NC / DNP** | U1.20 (44.0,27.5), exit OK (stub only) | Fixes D open (61.5 mm). |
| J16.4 (108.0,15.62) | P0.09 SDIN | **NC / DNP** | U1.16 (44.0,29.5), routed to J12.10 | Fixes D open (53.5 mm). |
| J10.1–4 (116, 28–35.62) | P0.21–P0.24 SPI | unchanged | U1.37/38/39/40 (35.75–34.25, 26.75), exit via existing vias | Opens are on the U1 side. De-dup does not help (J10↔J13 legs are already joined). |
| J11.1/.2 | P0.30/P0.31 I2C | unchanged | U1.88/89 (36.25/36.75, 37.25), exit OK | Opens are on the U1 side. Both header legs are routed. |
| J17.1/.2 | P0.17/P0.18 PDM | unchanged | U1.28 routed / U1.29 (39.75,26.75) **trapped** | J17.2 now sits on the J13.3/J18.6 island. Only the U1.29 open is left. |
| J18.1–8 | P0.13–P0.20 | unchanged (silicon-fixed AIN0–7) | — | AIN can't move: AIN0–7 = P0.13–P0.20 only (PS pin table). |
| J12.x / J13.x | P0.00–P0.31 | unchanged | — | Breakout order is kept. Renumbering breakout pins changes no geometry. |

**Alternative for I2S** (if Anand wants J16 kept): drop **J12.11/J12.13** (P0.10/P0.12) instead and keep J16.
- Each net still has 1 open, but it moves from the "boxed" J12 approach (class B) to a U1→J16 In2 run of about 4–5 segments. The census says that run is geometrically easy and is held up only by the length cap (DNR).
- P0.09/P0.11 would still need their J16 legs: +2 opens.
- Net effect: −2 instead of −4.

## 2. Nets dropped / merged, fan-outs removed
- No nets are merged or deleted. Header legs are dropped: **J9.2, J9.3, J16.1–J16.4** (6 pads become NC).
- Fan-outs removed:
  - P0.05: J12+J9 → J12
  - P0.07: J12+J9 → J12
  - P0.09–P0.12: J12+J16 → J12
- Multi-header fan-outs kept (their header legs are already routed): P0.04/P0.06 (J12+J9), P0.13–P0.20 (J12/J13+J18; P0.17/18 also J17), P0.21–P0.24 (J13+J10; P0.22 also J8.6), P0.30/31 (J13+J11).

## 3. Firmware-facing changes
- **UART0:** TX P0.06 (unchanged), **RX P0.07 → P0.04**, RTS/CTS removed. DTS: `rx-pin = <4>`, `hw-flow-control` off.
  - P0.05/P0.07 become plain breakout GPIOs on J12.6/J12.8.
  - Check this against the nRF9161 DK / NCS board file defaults (the DK uses other pins anyway, since this is a custom board).
- **I2S:** same GPIOs (SCK P0.10, LRCK P0.11, SDIN P0.09, SDOUT P0.12). The connector changes from J16 to J12.10–J12.13. No DTS change.
- **No change:** SPI, I2C, PDM, ADC, LEDs (P0.00–P0.03), USER button (P0.08).
- **Trace caveat (unchanged, but should be documented):** P0.21 TRACECLK, P0.22–P0.25 TRACEDATA[0..3] (nRF9161 PS pin table; nRF9161 DK UG trace table). SPI0 on J10 and the J8.6 SWO pin can't be used while parallel trace is on. Trace pins need S0S1/H0H1 drive (PS Trace page).
  - Moving SPI off P0.21–P0.24 would not reduce opens, so this plan does not propose it.
- Sources:
  - https://docs.nordicsemi.com/r/bundle/ps_nrf9161/page/pin.html
  - https://docs.nordicsemi.com/r/bundle/ps_nrf9161/page/trace.html
  - https://docs.nordicsemi.com/r/bundle/ug_nrf9161_dk/page/ug/nrf91_dk/hw_description/hw_debug_in_trace.html
  - nWP054 pinout: all GPIOs are at VDD_GPIO level.

## 4. Expected open count
Baseline: 31 non-GND (+12 GND islands, not affected by a pinmap).

**Resolved by remap (−6):** P0.05↔J9.3, P0.07↔J9.2, P0.09↔J16.4, P0.10↔J16.1, P0.11↔J16.2, P0.12↔J16.3.

**Expected after remap: 25 non-GND (+12 GND = 37 unconnected).** Unproven until DRC runs after the schematic and PCB update.

Still needs routing work (25 = 9 + 4 + 2 + 8 + 2):
- **Fixed-function (9), out of remap scope:**
  - MAGPIO0/1/2, MIPI_VIO/SCLK/SDATA: west edge, RF keepout + x≥26 + SIM_RST/P0.00 west runs.
  - COEX1 U1.92: trapped south.
  - SIM_1V8 U1.49: via-in-pad only.
  - SIM_IO U1.48: north band.
- **North-edge GPIO via the existing vias (4):** P0.21 U1.37, P0.23 U1.39, P0.24 U1.40, P0.25 U1.42 to J13. P0.23 is already DNR because In2 east-west runs split the VDD_nRF In2 neck (x53–60, y12–22; PASS30BZ/CA). Expect the same for the others.
- **Trapped north (2):** P0.14 U1.24 (courtyard-inside via spots only), P0.18 U1.29. Both are AIN, so they can't be remapped.
- **South pads inside the P0.00 In1 loop y=37.40 (8):** P0.01 U1.96 (trapped), P0.03 U1.99, P0.26 U1.83, P0.27 U1.84, P0.28 U1.86, P0.29 U1.87 (trapped), P0.30 U1.88, P0.31 U1.89.
- **J12 boxed (2):** P0.10 J12.11, P0.12 J12.13. Unlock: move the P0.09 In1 y=77.20 / P0.05 In1 y=74.70 approach.

**Getting to 0 needs more than a pinmap.** Options, for Anand/PM:
- (a) Reroute the P0.00 south loop (unlocks up to 8).
- (b) A VDD_nRF stitching-via policy, or moving the In2 neck (unlocks the 4 north).
- (c) A courtyard / via-in-pad waiver (P0.14, P0.18, SIM_1V8).
- (d) Fix the RF keepout / P0.00 west bypass (6 west fixed-function).
- (e) Last resort: depopulate breakout pins for trapped GPIOs, i.e. leave the GPIO unbroken-out. Candidates: P0.27, P0.29, P0.26, P0.28 (J13.11–14, no on-board load). This contradicts README "all 32 GPIOs".

## 5. Risks / open questions
1. **Dropping UART RTS/CTS** loses HW flow control on J9. Is a 2-wire console OK? If not, keep J9.2/J9.3 and grant a length-cap waiver (D class, In1/In2 5–9 segments).
2. **J16 DNP vs J12-only I2S:** the README promises a labelled I2S header. The silkscreen and README header map need updating either way.
3. README says "In2.Cu is the VDD_nRF plane — do not pour GPIO on it". Several remaining GPIO plans and existing routes use In2 (e.g. P0.07, P0.11, P0.20, P0.23 islands). That conflicts with PASS30BZ/CA VDD_nRF splits. **PM should rule** on whether In2 GPIO routing is allowed.
4. **The PCB is stale against the schematic:** U2's value on the PCB is still `TLV73330PDBV`, but the schematic has TLV73333. Run Update-PCB-from-Schematic before or with this remap.
5. With no kicad-cli, the "25" is arithmetic from the DRC JSON, not a run. Re-verify with DRC after implementation.
6. The PASS30AW escapable census is dated 2026-09-30 (older board, sha 3f20…). PASS30BS (tip 45743c9) is newer, and its classes take precedence here.
7. J8.6 (P0.22) used as "SWO": the nRF9161 PS pin table lists P0.22 only as TRACEDATA[0]. Confirm the debugger mode, but keep it as dedicated debug.
