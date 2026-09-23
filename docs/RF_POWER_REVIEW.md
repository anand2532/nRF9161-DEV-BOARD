# RF + Power Integrity Review — nRF9161-DEV-BOARD

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 (Asia/Calcutta) |
| **Reviewer** | RF Power Engineer |
| **Working copy** | `/workspace/kicad-projects/nRF9161-DEV-BOARD` |
| **Scope** | First-cut RF + power integrity vs Nordic nRF9161 PS / nRF91 HDG / nWP033 / DK PCA10153 notes (as cited in README). Schematics B POWER, C LTE, D GNSS, E SIM (`schematic/02`–`05`; live hierarchy — not leftover `schematics/`). Spot-check of `nRF9161-DEV-BOARD.kicad_pcb` + `reports/UNCONNECTED_AFTER_FINAL.csv` / DRC summaries. |
| **Sources of truth** | README Nordic refs; live `.kicad_sch` values; PCB pad nets / placements; connectivity CSV (80 unconnected). |

**Verdict:** Schematic RF/power *topology and values* largely follow Nordic guidance. The board is **not** bring-up-ready: PCB still has open power, VDD_GPIO, SIM, and reset islands that will stop DC/RF/LTE-SIM bring-up. Do not fab until those nets are closed and DRC `unconnected_items = 0`.

---

## DECISION (LOCKED) — GNSS active-antenna bias topology

| Field | Value |
| --- | --- |
| **Choice** | **COEX0-gated bias** (Nordic DK / nWP033 aligned). **Not** always-on from `VDD_GPIO`. |
| **Status** | **LOCKED** 2026-09-23 — Hardware PM: do **not** re-open always-on vs gated. |
| **Owner** | Schematic Engineer (`04_GNSS.kicad_sch`); PCB Layout routes switch + `COEX0`. README already assumes gated — keep README, fix hardware. |

### Why
- nRF9161 DK (PCA10153) uses **COEX0** to enable GNSS LNA / external active-antenna bias; firmware `%XCOEX0` is the documented off-switch for passive antennas and conducted tests on the GNSS SWF.
- This board has **no onboard GNSS LNA/patch** (U.FL-only active antenna). Bias must therefore be switched on the **`GNSS_VBIAS` rail**, not only mirrored to `GNSS_LNA_EN`.
- Current `04_GNSS` ties `FB5` directly `VDD_GPIO` → `GNSS_VBIAS` while `R4` only does `COEX0` → `GNSS_LNA_EN`/TP2. That leaves **DC on J5/J6 whenever `VDD_GPIO` is up**, which contradicts README and is unsafe for passive/conducted use.

### Required schematic topology (`schematic/04_GNSS.kicad_sch`)
```
VDD_GPIO ──► [U_BIAS high-side load switch] ──► FB5 ──► GNSS_VBIAS ──► L4 ──► GNSS_ANT
                         ▲ EN                              │
                      COEX0                         C28/C29/C30 to GND
                                                    C27 DC-block GPS↔GNSS_ANT (unchanged)

COEX0 ── R4 0Ω ── GNSS_LNA_EN ── TP2   (keep as sense / scope point)
```
Keep existing bias-T values: **C27 100 pF**, **L4 100 nH**, **C28 100 pF / C29 10 nF / C30 100 nF**, **FB5 BLM15HG102SN1**.

### Part choices (pick one; prefer A)
| Option | Part | Role | Notes |
| --- | --- | --- | --- |
| **A (preferred)** | **TPS22919DCKR** (SC-70) | Load switch | VIN=`VDD_GPIO` (~3.0 V from U2 `TLV73330PDBV`), ON=`COEX0` (1.8 V–compatible VIH), OUT→FB5. Cap on OUT per TI DS if required. |
| B (alt IC) | TPS22916CYFPR | Load switch | Same net roles; CSP package. |
| C (discrete) | **DMG2305UX** (P-ch) + **2N7002KW** (N-ch) + **100 kΩ** gate pull-up to `VDD_GPIO` | High-side FET switch | COEX0→N-ch gate (optional 1 kΩ series); N-ch drain→P-ch gate; P-ch source=`VDD_GPIO`, drain→FB5. Active-high COEX0 = bias ON. |

### Also fix while editing GNSS sheet
1. **FB5 footprint** → `L_0402_1005Metric` (MPN is 0402 `BLM15HG102SN1`; today footprint is 0603).
2. Do **not** feed bias from VDD1/VDD2; stay on `VDD_GPIO` after the switch (active LNA ~5–20 mA; keep TX current off this rail).
3. Default firmware: enable bias only when using an active antenna (`%XCOEX0`); leave off for passive / J6 conducted work.

### What Schematic Engineer must change
1. Insert Option A (or B/C) between `VDD_GPIO` and FB5; net OUT as feed into FB5 (or rename mid-net `GNSS_VBIAS_SRC` if clearer).
2. Tie switch ON/EN to **COEX0** (same net as R4 input).
3. Leave R4/TP2 as COEX0 monitor; do not use R4 as the bias power path.
4. Fix FB5 land to 0402; update BOM.
5. Align README wording once implemented (already describes COEX0 gating — schematic must match).

**Owner:** Schematic Engineer. **PCB:** leave space near GNSS bias-T for SC-70 (or SOT-23 pair if Option C). Promote from ambiguous P1 → **schematic P0 before fab** if active-antenna + passive/conducted flexibility is required (board intent per README).

---

## P0 Critical (would stop board working or fail RF / LTE bring-up)

### P0-1 — Input power path open on PCB (`VIN_FILT` / `VIN_F`)

- **Evidence:** `reports/UNCONNECTED_AFTER_FINAL.csv` class **F**:
  - `VIN_FILT` ~10.1 mm island (tracks at ~(55.35,12.0) ↔ ~(53.2,21.9))
  - `VIN_F` ~24.4 mm island (tracks at ~(48.0,12.6) ↔ ~(71.58,19.06))
- **Schematic (B POWER `02_POWER.kicad_sch`):** Intended chain J1 → D1 `PMEG4030ER` → D2 `SMAJ5.0A` → F1 `2A` → FB4 `BLM18PG221SN1` → C1 `10uF/16V` + C2 `100nF` → R2 `0.05Ω` / JP1 → `VDD_nRF` → FB1/FB2 `BLM18KG221SN1` (matches README power tree; live Values verified).
- **PCB pads:** F1=`VIN`/`VIN_F`, FB4=`VIN_F`/`VIN_FILT`, R2/JP1=`VIN_FILT`/`VDD_nRF` — nets assigned correctly, **copper not finished**.
- **Impact:** `VDD_nRF` / VDD1 / VDD2 / SiP may never see supply. Hard stop for any bring-up.
- **Owner:** PCB Layout Engineer.

### P0-2 — `VDD_GPIO` not reaching U1 (and GNSS bias feed)

- **Evidence:** `UNCONNECTED_AFTER_FINAL.csv` class **A**, multiple islands, including:
  - U1 **pad 12** `[VDD_GPIO]` ↔ nearby F.Cu stub (~13.2 mm)
  - U1 pad 12 ↔ **FB5 pad 1** `[VDD_GPIO]` (~33.7 mm)
  - Additional B.Cu / F.Cu `VDD_GPIO` track islands (~15–34 mm)
- **Schematic:** U2 `TLV73330PDBV` OUT → `VDD_GPIO`; C11 `4.7uF` + C12 `100nF`; GNSS FB5 `BLM15HG102SN1` from `VDD_GPIO` → `GNSS_VBIAS` (must become COEX0-gated per DECISION).
- **PCB:** U2 pad 5 (OUT) = `VDD_GPIO` (correct SOT-23-5 mapping); FB5 pad1=`VDD_GPIO`, pad2=`GNSS_VBIAS`.
- **Impact:** SiP IO domain unpowered → SWD/UART/GPIO dead. Active GNSS bias starved even if RF spine exists. Fail digital + GNSS bring-up.
- **Owner:** PCB Layout Engineer.

### P0-3 — UICC/SIM path open between SiP and SIM filter/socket

- **Evidence:** `UNCONNECTED_AFTER_FINAL.csv` class **A**:
  | Net | Open (approx) | Ends |
  | --- | --- | --- |
  | `SIM_RST` | 44.4 mm | U1 pad **43** ↔ B.Cu track / C36 island |
  | `SIM_CLK` | 41.4 mm | U1 pad **46** ↔ B.Cu track |
  | `SIM_IO` | 52.0 mm | U1 pad **48** ↔ F.Cu track |
  | `SIM_1V8` | 46.5 mm | F.Cu track ↔ U1 pad **49** |
- Older `DRC_kicad-cli.rpt` also shows card-side islands (`SIM_*_C`, `SIM_VCC` to J7).
- **Schematic (E SIM `05_SIM.kicad_sch`):** U1 → TPD3F303 `U4` → JAE SF72S006 `J7`; JP2 `SIM_VCC` open jumper; C33 `100nF`, C34 `220nF`, C35–C38 `22pF`. Topology matches HDG/DK intent.
- **Good:** U1 pad **45** `SIM_DET` has **no net** (must float per PS) — confirmed on PCB.
- **Impact:** No SIM ↔ modem → LTE attach / UICC bring-up fails.
- **Owner:** PCB Layout Engineer.

### P0-4 — `nRESET` path open on PCB

- **Evidence:** `UNCONNECTED_AFTER_FINAL.csv` class **F**: `nRESET` ~68.9 mm (B.Cu track ~(101.7,58.8) ↔ F.Cu ~(52.2,10.8)).
- **Impact:** Debugger reset / reliable programming and recovery unreliable → blocks SWD bring-up that gates RF firmware tests.
- **Owner:** PCB Layout Engineer.

### P0-5 — Fab gate: 80+ unconnected items (project hard stop)

- README / `reports/UNCONNECTED.md` / `FINAL_FAB_RELEASE.md`: **do not fab** until `unconnected_items = 0`.
- Live summary variants cite **80–116** unconnected depending on report vintage; shorts/clearance/hole_clearance reported **0**.
- **Impact:** Any board spun from current Gerbers will not match the schematic electrically on critical nets above.

---

## P1 High (likely RF/power risk before fab)

### P1-1 — GNSS bias still always-on in schematic (**decision locked: must gate with COEX0**)

- **Decision:** See **DECISION — GNSS active-antenna bias (LOCKED)** above. Nordic-aligned = **COEX0-gated**, not always-on. Do not re-open.
- **As-built evidence (`04_GNSS.kicad_sch` / PCB):**
  - FB5: `VDD_GPIO` → `GNSS_VBIAS` (hard-wired)
  - L4 `100nH`: `GNSS_VBIAS` → `GNSS_ANT`; C27 `100pF` DC block on `GPS`↔`GNSS_ANT`
  - C28 `100pF`, C29 `10nF`, C30 `100nF` on `GNSS_VBIAS`
  - R4 `0R`: `COEX0` → `GNSS_LNA_EN` (TP2) only — **not** a power switch
- **Gap:** Hardware does not implement the locked decision; README already assumes gated bias.
- **Action:** Implement DECISION parts (primary **TPS22917DBVR** / **TPS22916BYFPR**, or discrete alternate); keep nWP033 L/C values; fix FB5 0402 land.
- **Owner:** Schematic Engineer (impl) + PCB Layout (route `COEX0` + switch).

### P1-2 — `COEX0` still open on PCB

- **Evidence:** `UNCONNECTED_AFTER_FINAL.csv` class **A**: `COEX0` track ↔ via (~17.1 mm). `COEX1` U1 pad 92 ↔ J15 (~70.7 mm).
- **Impact:** `%XCOEX0` / J15 COEX bring-up broken; even the LNA_EN TP is dead. Secondary to P1-1 for bias power, but blocks coex validation.
- **Owner:** PCB Layout Engineer.

### P1-3 — LTE/AUX series match BOM vs assembly intent

- **Schematic C LTE:** L1 / L2 Value = `0R / DNP match`, `(dnp no)` — series path must be **0 Ω** for first RF bring-up.
- **BOM:** MPN `LQW15AN10NG00` (**10 nH**), note “Fit 0R until VNA; then LQW15AN”.
- **Risk:** EMS stuffs 10 nH (or leaves DNP from the note) → ANT/AUX open or mistuned → conducted/OTA fail before VNA.
- **Action:** BOM primary MPN = 0R 0402 jumper; alternate line for LQW15ANxxx after tune. Clear DNP=no on L1/L2.
- **Owner:** Schematic / BOM owner.

### P1-4 — Pi-match shunt caps Value=`DNP` but KiCad `(dnp no)`

- **Refs:** C21–C24 (LTE/AUX), C31–C32 (GNSS). Footprints on ANT/AUX/GNSS nets.
- **PCB:** Class **C** opens on C22 / C23 / C24 stubs (expected if DNP and not stubbed to the 50 Ω line).
- **Risk:** Fabricator using schematic DNP flag (not BOM “DNP” column) may **stuff** placeholders; or leave floating pads that DRC flags forever.
- **Action:** Set `(dnp yes)` / exclude-from-bom appropriately; stub or NC-mark same-net pads without moving 50 Ω trunks.
- **Owner:** Schematic + PCB Layout.

### P1-5 — FB5 footprint vs MPN size mismatch

- **BOM/schematic value:** `BLM15HG102SN1` (**0402**).
- **Schematic footprint + PCB:** `Inductor_SMD:L_0603_1608Metric` (**0603**).
- **Risk:** Wrong land pattern for intended bead → assembly defect on GNSS bias.
- **Owner:** Schematic Engineer.

### P1-6 — Stale / conflicting connectivity reports

- `DRC_kicad-cli.rpt` still lists opens on **ENABLE** (C14/R1), **DEC0** (C13), **VDD1**, **VDD2**, **GNSS_VBIAS**; these **do not** appear in `UNCONNECTED_AFTER_FINAL.csv`.
- **Action:** Re-run `kicad-cli pcb drc` on the live PCB and treat the fresh JSON as truth before fab. Do not assume ENABLE/DEC0/VDD2 are closed until re-verified.
- **Owner:** PCB Layout / DFM.


### P1-8 — `VDD_GPIO` LDO is 3.0 V MPN while README/BOM text say 3.3 V

- **Schematic** `U2` = `TLV73330PDBV` (TI fixed **3.0 V**; symbol description confirms).
- **README** power tree / bring-up / header notes: **3.3 V** `VDD_GPIO`.
- **BOM.csv** MPN `TLV73330PDBVR` but note text “3.3 V VDD_GPIO LDO” — inconsistent.
- **Impact:** 3.0 V is within nRF9161 `VDD_GPIO` abs-max range and usually OK for active GNSS bias, but SWD VTREF, labelled 3.3 V headers, and README bring-up checks will read ~3.0 V. Prefer aligning to README.
- **Action:** Change U2 to **`TLV73333PDBV` / `TLV73333PDBVR`** (3.3 V) **or** revise README+BOM to 3.0 V everywhere. Do not leave MPN vs docs split.
- **Owner:** Schematic Engineer.

### P1-7 — DEC0 placement distance (verify after re-route)

- C13 `4.7uF` (PCN134 — correct value) at ~(49.2, 29.6); U1 center ~(36, 32), rot 180°.
- ~13 mm to SiP center / ~5 mm class to east edge — acceptable if pad 13 fanout is short; confirm after closing any remaining DEC0 island (stale DRC). Nordic wants DEC0 **close** to pin 13.
- **Owner:** PCB Layout Engineer.

### P1-8 — Root sheet stale RF note

- Root `nRF9161-DEV-BOARD.kicad_sch` text still says “Do not populate **C18–C21**”; live design uses **C21–C24** / C31–C32.
- Confusion risk at assembly.
- **Owner:** Schematic Engineer.

---

## P2 Medium / notes

| ID | Item | Evidence / note |
| --- | --- | --- |
| P2-1 | U2 is **TLV73330** = **fixed 3.0 V**, README says 3.3 V GPIO | Within nRF9161 VDD_GPIO range; fix README or change to TLV73333 if 3.3 V required for peripherals. 300 mA LDO is **not** in LTE TX path (TX is on VDD2 from VIN) — OK for peak TX current. |
| P2-2 | VDD1/VDD2 ferrites `BLM18KG221SN1` | Matches HDG Table 2 family. README notes DK preference for lower-DCR `BLM18PG121SN1D` — optional swap to reduce IR drop at ~500 mA VDD2 peaks; KG221 current rating is adequate if routing is solid. |
| P2-3 | JP1 open by default | Current still flows through R2 `50 mΩ` (~25 mV @ 500 mA). Close JP1 for normal RF TX tests (README). |
| P2-4 | JP2 open by default | SIM VCC isolated until closed — correct for bring-up; must close for UICC. |
| P2-5 | AUX is TP1 only (no U.FL) | Fine for reserved AUX; not needed for first LTE attach. |
| P2-6 | No onboard GNSS LNA/patch | Documented; **active** antenna on J5 required. |
| P2-7 | RF keepout zones on PCB | Keepouts exist at west edge (~x 7–9 / board edge). Matching/U.FL sit east of that; ensure digital/B.Cu stays out of west RF box per README (~0–24 mm x). |
| P2-8 | 50 Ω width | Netclass `RF_50OHM` in project; README assumes ~0.20 mm over ~0.12 mm H, εr≈4.2. **Confirm with fab stackup coupon** before tape-out. |
| P2-9 | In1.Cu solid GND under RF | Zone pour GND on In1 — correct microstrip reference; do not split under ANT/GPS. |
| P2-10 | C27 0201 vs other RF 0402 | OK if assembly capable; watch tombstoning. |
| P2-11 | Input TVS `SMAJ5.0A` | Continuous VIN must stay 3.0–5.5 V (README). |
| P2-12 | Peak TX headroom | F1 2 A; supply must deliver ~500 mA VDD2 pulses. Weak USB 5 V dongles are a bring-up footgun (README). Not a schematic brick if VIN path is routed (P0-1). |

---

## What matches Nordic / OK (brief)

| Area | Finding |
| --- | --- |
| LTE ANT/AUX match | Reserved π: series L1/L2 `0R` placeholders, shunt C21–C24 DNP — Nordic “don’t invent tune values” approach (nWP033). J2 U.FL + J3 SWF MM8130. |
| GNSS RF | C27 `100pF` DC block + L4 `100nH` choke + bias filter C28–C30 + FB5; shunts C31/C32 DNP — nWP033 active-antenna bias-T topology. J5 U.FL + J6 SWF. |
| DEC0 | C13 **`4.7uF`** — PCN134 (not legacy 47 µF). |
| VDD1 bank | FB1 `BLM18KG221SN1` + C3 `47uF/10V` + C4 `4.7uF` + C5 `100nF` + C6 `15pF`. |
| VDD2 bank | FB2 + **FB3** (DK extra) + C7 `47uF` + C8 `4.7uF` + C9 `100nF` + C10 `15pF`. |
| ENABLE | R1 `10k` from VDD1, C14 `100nF`, SW1 to GND; U2 EN tied to ENABLE — sensible sequencing. |
| SIM_DET | Pad 45 intentionally unconnected. |
| SIM ESD/filter | TPD3F303 + nano-SIM SF72S006 + ISO caps — HDG/DK-like. |
| SiP orientation | U1 ~(36, 32) mm, **rot 180°**, RF edge west; L1 ~(22,32), J2 ~(8,32) — matching west of SiP as README requires. |
| Stackup intent | F.Cu RF / In1 GND / In2 `VDD_nRF` / B.Cu — correct roles for RF + power plane. |
| TX current path | LTE PA current on VDD2 from VIN through ferrites — **not** through TLV733 300 mA LDO. |

---


## Power tree skim vs README

README tree vs live `02_POWER.kicad_sch` (verified values):

| Node | README | Schematic (live) | Match? |
| --- | --- | --- | --- |
| Input | VIN 3.0–5.5 V on J1 | J1 `VIN_3V0-5V5` | Yes |
| Reverse / TVS / fuse / bead | D1 PMEG4030ER → D2 SMAJ5.0A → F1 2 A → FB4 | D1 `PMEG4030ER`, D2 `SMAJ5.0A`, F1 `2A`, FB4 `BLM18PG221SN1` | Yes |
| Bulk on VIN_FILT | C1/C2 | C1 `10uF/16V`, C2 `100nF` | Yes |
| Sense / bypass | R2 50 mΩ, JP1 | R2 `0.05`, JP1 `I_MEAS` | Yes |
| VDD1 | FB1 + 47 µF / 4.7 µF / 100 nF / 15 pF | FB1 `BLM18KG221SN1`, C3 `47uF/10V`, C4 `4.7uF`, C5 `100nF`, C6 `15pF` | Yes |
| VDD2 | FB2+**FB3** + same bank | FB2+FB3 `BLM18KG221SN1`, C7–C10 same pattern | Yes (DK FB3 present) |
| ENABLE | R1 10 kΩ, C14 100 nF, SW1 | R1 `10k`, C14 `100nF`, SW1 `DISABLE` | Yes |
| VDD_GPIO LDO | **TLV73330 3.3 V**, EN=ENABLE | **`TLV73330PDBV` = fixed 3.0 V**, EN=ENABLE | **No — 3.0 V vs README 3.3 V** (P2-1; still in SiP range) |
| DEC0 | C13 4.7 µF (PCN134) | C13 `4.7uF` | Yes |
| LTE TX path | ~500 mA on VDD2 from VIN, not through GPIO LDO | Same architecture | Yes |

**PCB gap (not a README/schematic disagreement):** `VIN_FILT` / `VIN_F` / `VDD_GPIO` islands still open (P0-1, P0-2) — tree is correct on paper, unfinished in copper.



## DECISION (locked) — Layout pass30 coordination

### 1) West MAGPIO / MIPI / COEX vs RF keepout

**Route north of the west RF matching keepout, then east to J14/J15. Do not cross under LTE/GNSS/AUX matching on F.Cu.**

| Item | Value |
| --- | --- |
| **Working keepout (respect this)** | Board coords **x ≈ 0–24.2 mm, y ≈ 20–64 mm** — west matching + U.FL/SWF corridor (LTE J2/J3, GNSS J5/J6, π-match L1/L2/C21–C24, GNSS bias-T). Cited from `docs/PCB_LAYOUT_REVIEW.md` §west RF keepout + README “RF keepout / no digital under matching”. |
| **Layers** | Keepout intent is **F.Cu RF microstrip + no digital under match**. Prefer **B.Cu** (or east escape then south) for MAGPIO/MIPI/COEX. **Do not split In1.Cu GND** under 50 Ω trunks. |
| **Live KiCad rule-areas today** | Only two tiny keepouts on **F.Cu+B.Cu** (tracks/vias/pads/pours disallowed, footprints allowed): ≈ **(7.05–8.95, 31.485–33.575)** and **(7.05–8.95, 51.485–53.575)** mm — connector-local, **not** the full west RF box. |
| **Action for Layout** | Treat the **0–24.2 × 20–64** box as mandatory clearance for pass30. Optionally add a named KiCad Rule Area matching that polygon on F.Cu (coordinate with RF before shrinking). U1 @ (36, 32) rot 180°; J14/J15 @ x≈104 — **north-then-east** jog around keepout. |

**Clearance rule:** no MAGPIO/MIPI/COEX tracks, vias, or pours inside the working keepout on F.Cu; stay ≥ **0.5 mm** outside matching component courtyards when skirting the north edge.

### 2) Class C — DNP 50 Ω RF shunts (C21–C24, C31–C32)

**Disposition: stub-terminate (short same-net stub to RF pad). Do not leave open. Do not populate. Do not rip 50 Ω trunks.**

Nordic nWP033 reserved-π practice: series = 0 Ω for first bring-up; **shunts unpopulated until VNA**. Footprints must remain.

| Ref | Net | Layout action |
| --- | --- | --- |
| C21, C22 | `ANT_FIT` (LTE π shunts) | Connect RF-side pad to `ANT_FIT` with **shortest stub** (target ≤ 2 mm). GND pad to solid GND. Leave part **DNP**. |
| C23, C24 | `AUX` / `AUX_FIT` | Same stub-terminate policy. |
| C31, C32 | `GNSS_ANT` | Same; do not disturb C27/L4 bias-T spine. |

**Forbidden:** deleting shunt footprints; ripping L1/L2/J2/J3/J5/J6 trunks to “clear” DRC; stuffing shunt MPNs for fab spin.

**Schematic follow-up (not Layout):** set KiCad `(dnp yes)` / exclude-from-BOM on C21–C24, C31–C32 so EMS does not populate.

### 3) GNSS bias topology (reconfirmed)

**COEX0-gated** high-side switch (preferred **TPS22919DCKR**) between `VDD_GPIO` and FB5 — see DECISION section above. Schematic owns the change; Layout leave space near GNSS bias-T for SC-70 (or SOT-23 pair if discrete).

---

## Stackup / impedance (RF concurrence with DFM)

**2026-09-23:** Concur with `docs/FAB_STACKUP_NOTES.md` — L1–L2 **H ≈ 0.10–0.15 mm (~0.12 mm preferred)**, **Z0 = 50 Ω SE** on `RF_50OHM` (0.20 mm nominal; coupon may retune 0.16–0.22 mm), **ENIG**, solid L2 GND under ANT/AUX/GNSS. No RF objection to DFM’s lock.

## Power tree vs README (skim)

Schematic `02_POWER` **matches** README topology and key values:

| Node | README | Schematic | Status |
| --- | --- | --- | --- |
| Input path | D1 PMEG4030ER → D2 SMAJ5.0A → F1 2 A → FB4 → C1/C2 | Same MPNs/values (`C1` 10 µF/16 V, `C2` 100 nF) | OK |
| Sense | R2 50 mΩ + JP1 → `VDD_nRF` | `R2` 0.05 Ω, `JP1` | OK |
| VDD1 | FB1 + C3 47 µF / C4 4.7 µF / C5 100 nF / C6 15 pF | FB1 `BLM18KG221SN1` + same C values | OK |
| VDD2 | FB2+FB3 (DK FB3) + C7–C10 | FB2+FB3 + C7–C10 | OK |
| ENABLE | R1 10 kΩ + C14; SW1 disable | Same | OK |
| `VDD_GPIO` | README: TLV73330 **3.3 V** | `U2` **TLV73330PDBV = 3.0 V** + C11/C12 | **MPN/docs mismatch — see P1-8** |
| DEC0 | C13 4.7 µF (PCN134) | C13 4.7 µF | OK |
| LTE TX current | ~500 mA on VDD2 from VIN path | TX not through TLV73330 | OK — do not move GNSS switch or GPIO LDO onto VDD2 |

**No new schematic P0 on the power tree itself.** Remaining power risk is **PCB open islands** (`VIN_FILT`/`VIN_F`, `VDD_GPIO`, etc. in P0 list), not regulator selection.

## Open questions / handoffs

### PCB Layout Engineer

1. Close **P0-1…P0-4** nets (`VIN_FILT`/`VIN_F`, `VDD_GPIO` to U1+FB5, all `SIM_*`, `nRESET`) without ripping LTE/GNSS 50 Ω trunks.
2. Finish `COEX0`/`COEX1` and DNP RF shunt stubs (or explicit NC).
3. Re-run DRC; reconcile with stale ENABLE/DEC0/VDD2/GNSS_VBIAS hits in `DRC_kicad-cli.rpt`.
4. Confirm L2 under ANT/GPS is unbroken GND; keep digital out of west RF keepout.
5. Check FB5 land pattern after schematic footprint fix (0402 vs 0603).

### Schematic Engineer

1. **Implement locked DECISION:** COEX0-gated GNSS bias (TPS22917/TPS22916 or discrete alternate) on `04_GNSS` — do not rewrite README to always-on (P1-1).
2. Fix L1/L2 BOM MPN vs 0R intent; set DNP flags on C21–C24, C31–C32.
3. FB5 footprint 0402 to match `BLM15HG102SN1`.
4. Update root sheet C18–C21 text; clarify VDD_GPIO 3.0 vs 3.3 V (TLV73330PDBV).
5. Optional: note BLM18PG121 as preferred VDD2 bead for IR drop.

### Bring-up (after copper closed)

1. Current-limited VIN; verify TP rails before antennas.
2. Close JP1 for TX; close JP2 for SIM.
3. Populate L1 as **0R**; leave shunt DNPs empty until VNA.
4. After DECISION impl: active GNSS needs `%XCOEX0` asserted; passive/conducted with COEX0 low (no DC on J5). Until implemented, treat bias as always-on hazard.
5. Measure VDD2 droop during LTE TX pulses per Nordic HW verification guidance.

---

## Report artifacts used

- `README.md`, `docs/PM_STATUS.md`
- `schematic/02_POWER.kicad_sch`, `03_LTE_RF.kicad_sch`, `04_GNSS.kicad_sch`, `05_SIM.kicad_sch` (+ root hierarchy)
- `nRF9161-DEV-BOARD.kicad_pcb` (pad nets, placements, zones)
- `BOM.csv`, `reports/UNCONNECTED_AFTER_FINAL.csv`, `reports/DRC_SUMMARY.txt`, `reports/FINAL_DESIGN_REVIEW.md`, `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_kicad-cli.rpt` (stale cross-check)

**No git commit made** (per task).
