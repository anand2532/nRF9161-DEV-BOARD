# nRF9161 DEVELOPMENT BOARD — FINAL DESIGN REVIEW

**Status: NOT FABRICATION-READY**

Hard gate failed: `unconnected_items = 104` (must be 0). Fabrication outputs were **not** regenerated.

PCB revision on disk: working 4-layer layout with completed LTE/GNSS/AUX 50 Ω routing, partial digital/power fanout. Backup of this pass: `.mcp-backups/final-pass-20260916-144412/` and `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-close-gaps`.

---

## BOARD

| Item | Value |
|------|--------|
| Dimensions | 120 × 80 mm |
| Layers | 4 |
| Stackup | F.Cu (signals/RF) / In1.Cu **GND** / In2.Cu **VDD_nRF** / B.Cu (GPIO/power returns) |
| PCB revision | REV A (not frozen — connectivity incomplete) |
| Footprints | 102 |
| Tracks | 486 |
| Vias | 125 |
| U1 position | (36.0, 32.0) mm, rotation 180° (RF west) |

Assumed fabrication stackup for 50 Ω (document for the board house; do not keep the current RF width if their dielectric differs):

- 1.6 mm FR-4, 4-layer
- L1 ↔ L2 dielectric ≈ 0.12–0.15 mm (typical JLC 4-layer 1 oz)
- 50 Ω microstrip on F.Cu referenced to In1 GND, trace width ≈ 0.20 mm (as routed)
- Recalculate width to the manufacturer’s actual Er and H before tape-out

---

## nRF9161

| Item | Value |
|------|--------|
| Device | nRF9161-LACA-R7 |
| Package | 16.0 × 10.5 mm LGA, PS Table 55/56 |
| Footprint | `libraries/Board.pretty` nRF9161 LGA (NSMD, oblong edge-pad fanout 0.30 × 0.80 mm) |
| Electrical pins | 127 (PS) |
| KiCad pad objects on U1 | 159 (includes courtyard/extra graphics — verify vs Table 56 before tape-out) |
| RF pads | 61 ANT, 64 AUX, 67 GPS — not oblong’d |
| RES / NC | pads 10, 51, 70, 71, 73, 104–127 left without nets (Nordic reserved/NC) |
| SIM_DET | U1 pad 45 **intentionally floating** (Nordic: do not connect). Mechanical card-detect is `SIM_CD` on J7, a separate net. |

Pin-by-pin PCB vs schematic vs PS is in `reports/PIN_AUDIT.csv` (existing). Remaining **open** U1 signals are listed in `reports/UNCONNECTED.md`.

---

## POWER

| Item | Value |
|------|--------|
| Input | VIN via J1, TVS/protection D1/D2, fuse F1, ferrite FB4 → VIN_FILT |
| nRF core | JP1 / R2 → **VDD_nRF** (In2 plane) |
| VDD1 | FB1 + C3–C6 at U1 east |
| VDD2 | FB2/FB3 + C7–C10 |
| VDD_GPIO | TLV73330 (U2) 3.3 V, 1.7–3.6 V domain, ENABLE sequencing from VDD1 |
| DEC0 | C13 4.7 µF (PCN134) next to U1 |

**Still open:** several VDD1/VDD2/VDD_GPIO capacitor and header islands (see UNCONNECTED). Do not treat In2 as a GPIO layer.

---

## RF

Preserved from the last known-good RF pass. **Do not rip these nets to finish GPIO.**

| Path | Status |
|------|--------|
| LTE/NR ANT (pad 61) → matching → 50 Ω F.Cu → J2 U.FL + J3 SWF tap | Routed |
| AUX (pad 64) | Routed; DNP shunt C23/C24 stubs still listed unconnected |
| GNSS GPS (pad 67) → match/filter → 50 Ω → J5/J6 | Routed |
| GNSS_VBIAS / C30 / L4 | Still open around the GNSS_ANT spine |
| RF keepout | West box ≈ (0, 20)–(24.2, 64) mm — B.Cu GPIO must not enter |

DNP RF shunts (C21–C24, C31) are schematic options; they still need short same-net stubs or explicit no-connects.

---

## INTERFACES

| Interface | Hardware | Connectivity |
|-----------|----------|----------------|
| GPIO | J12 / J13 20-pin, J9–J11 / J16 / J17 | Many P0.xx still open (see below) |
| UART / SPI / I2C / I2S / PDM / ADC | J18 ADC + dedicated headers | Partial; ADC wall at y≈62 is a PTH obstacle |
| SWD | J8 | SWDCLK still unconnected to U1 pad 33 |
| SIM/UICC | J7 + U4 TPD3F303 | SIM_CLK/RST/IO/1V8/VCC islands remain |
| MAGPIO / MIPI / COEX | J14 / J15 | West U1 pads must jog north of RF keepout — not finished |
| Buttons / LEDs | RESET, USER | Present |

Remaining GPIO (from DRC, not the original guess list): P0.01, P0.04, P0.06, P0.09, P0.11, P0.13–P0.26, P0.27–P0.31 (subset with open pairs), plus duplicate header copies on J9/J10/J16/J17/J18.

---

## VALIDATION (this pass)

| Check | Result |
|-------|--------|
| ERC errors | **0** |
| ERC warnings | **1** — `U4` TPD3F303DPV library symbol mismatch (`Power_Protection`) |
| DRC shorting / clearance / hole_clearance | **0 / 0 / 0** |
| DRC unconnected_items | **104** ← hard fail |
| Ratsnest | Non-zero (same islands as DRC) |
| silk_overlap | 141 |
| silk_over_copper | 35 |
| via_dangling | 55 (fanout vias waiting for B.Cu) |
| track_dangling | 2 (P0.11 / P0.06 F.Cu stubs) |
| lib_footprint_mismatch | 3 |
| Fab files | **Not generated** (gate) |

Source reports: `reports/DRC_kicad-cli.rpt`, `reports/DRC_final.json`, `reports/ERC.txt`, `reports/UNCONNECTED.md`.

---

## WHY 116 → 104, NOT 0

Work in this pass (no autorouter, RF backup not restored):

1. Backed up the live board (`final-pass-20260916-144412`, `pre-close-gaps`).
2. Full unconnected list taken from `kicad-cli pcb drc` JSON, not MCP airwires.
3. Ghost unnumbered 0402 pads were falsely blocking legal F.Cu — skipped in the geometric router.
4. Closed a few local F.Cu islands (VDD1 C4–C6–R1–FB1, DEC0, some SIM/power, nRESET_SW, one VDD_GPIO hop).
5. **Did not** accept a B.Cu wipe that raised unconnected to 118+; restored the 106-island board, then 104 after F.Cu jogs.

What still blocks 100% connectivity:

- **Courtyard via pitch vs 0.6 mm vias:** odd-row U1 pads (P0.06/09/11/14/16/18/20/22/24/27/29/31, MAGPIO0, MIPI, COEX1, P0.01, P0.04) have no legal via site 0.5 mm from the existing 0.95 mm ring.
- **B.Cu congestion:** already-routed GPIOs occupy y≈69–72 board-width buses and x≈50.8 / 105–107 columns. Remaining nets cannot cross those without ripping the working GPIO (not done).
- **J18 PTH wall** (x≈34–63, y≈60–65) and **10 mm GND stitch grid** (partially removed this pass) pinch south/east exits.
- **North MAGPIO1 highway at y=14.8** blocks a north-bus detour around the SiP.
- **0402 GND pads** sit 0.64 mm from pin 1 and block naive VDD/ENABLE/SIM stubs; only some jogs succeeded.
- West MAGPIO/MIPI cannot sit in a via alley against the RF keepout; north-ring jog is still incomplete.

Blind autoroute and “mark as NC” were rejected. Remaining connections must be placed **net-by-net** (unique B.Cu columns east of J18 at x≥64.6 or west wrap x≈25.1 south of RF, plus extra fanout vias beyond the 0.95 mm ring).

---

## MANUFACTURING (when connectivity is 0)

| Item | Current design |
|------|----------------|
| Min trace | 0.10 mm (RF 0.20, signal 0.18, power 0.40) |
| Min clearance | 0.10 mm default; 0.15 power/RF class |
| Smallest drill | 0.25 mm through (signal via 0.60/0.30; power 0.80/0.40) |
| LGA | NSMD oblong fanout; confirm paste/mask vs Nordic land pattern |
| Assembly | SiP + 0402 + nano-SIM + U.FL; keep RF keepout clear of vias |

---

## SILKSCREEN

Not cleaned. 141 overlaps, 35 over copper. Connector/GPIO labels are not production-ready.

---

## NEXT ACTIONS (required before `/fab`)

1. Add staggered fanout vias **beyond** the existing ring for every U1 pad still without a via (1.15–2.1 mm, not 0.50 mm from neighbors).
2. Give each remaining GPIO a **private** B.Cu vertical (x≥64.6 or x≈25.1) and a **short** y≈77.5 stub to its header pin — do not run another board-width y≈70 bus.
3. Finish VDD1/VDD2/VDD_GPIO/ENABLE/SIM/GNSS_VBIAS with F.Cu jogs around 0402 GND pads.
4. Stub or NC-mark DNP RF shunts without moving 50 Ω trunks.
5. Silk pass after copper is finished.
6. Re-run ERC + DRC; **only then** write `/fab` and freeze REV A.

Until `unconnected_items = 0` and ratsnest = 0, this project stays a development layout, not a Gerber release.
