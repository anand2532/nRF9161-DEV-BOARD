# PCB Layout Review — nRF9161-DEV-BOARD

**Role:** PCB Layout Engineer  
**Working path:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Review date:** 2026-09-23 10:42 IST (Asia/Calcutta) — pass30f executed
**Overall:** **NOT FABRICATION-READY** — connectivity hard gate open  
**Gerbers:** **Do not generate** until `unconnected_items = 0` and DFM checklist is green  

Cross-refs: `docs/FAB_READY_CHECKLIST.md` (DFM gate **RED**), `docs/FAB_STACKUP_NOTES.md`, `docs/PM_STATUS.md`, `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`, `reports/UNCONNECTED_AFTER_FINAL.csv`.

---

## 1. Current connectivity status

| Metric | Count | Source |
| --- | --- | --- |
| **unconnected_items** | **78** | `reports/DRC_PASS30F_AFTER.json` (live `kicad-cli` 9.0.2); VIN_FILT closed in 30f but GND zone islands +1 kept total 78 |
| **shorting_items** | **0** | Same JSON |
| **clearance** | **0** | Pass30 after (was 6 at baseline; zone refill cleared via/zone hits) |
| **hole_clearance** | **0** | Same |
| via_dangling | **78** | `DRC_PASS30F_AFTER.json` |
| drill_out_of_range | **0** | Pass30 before/after — P0.02 & nRESET already ≥0.50/0.30 |
| via_diameter | **0** | Same |
| track_dangling | 13 | Same JSON (includes load-bearing P0.15 west-wrap stubs) |
| silk_overlap / silk_over_copper | 147 / 36 | Cosmetics — after copper freeze |
| Live copper | ~780 segments, ~250 vias | Live after pass30 |

### Count reconciliation (do not mix eras)

| Report | unconnected | Notes |
| --- | --- | --- |
| `reports/DRC_SUMMARY.txt` | 116 | Older summary — **superseded** |
| `reports/DRC_BEFORE_FINAL.json` | 120 | Pre-final pass |
| `reports/DRC_final.json` / `FINAL_DESIGN_REVIEW.md` | 104 | Mid campaign |
| `reports/DRC_AFTER_CONNECT_FULL.json` | 98 | Intermediate |
| **`DRC_PASS30F_AFTER.json`** | **78** | **Authoritative after pass30f** (VIN_FILT closed; GND Class-E +1) |

Live `kicad-cli` 9.0.2 DRC was re-run for pass30c (`reports/DRC_PASS30C_BEFORE.json` / `reports/DRC_PASS30C_AFTER.json`). On-disk `fab/gerbers/` CreationDate **2026-09-16** remains **stale** and must not be used for fab (DFM checklist §5).

**Pass delta (pass30c):** netlist sync + U3.VIN + U3.ON closed. **Before unconnected:** 80 · **After unconnected:** 78 · **Nets closed:** VDD_GPIO (U3.1), COEX0 (U3.3). Class F deferred. shorting/clearance=0. P0.15 wrap preserved.

**Pass delta (pass30e):** Aggressive Class F corridor clear (PM-approved rip list). **Before/After unconnected:** 78/78 · **shorting/clearance:** 0/0 · **Nets closed:** none. ENABLE restore was the failing link. All trial copper reverted. Details: `reports/PASS30E_SUMMARY.json`.

**Pass delta (pass30f):** ONE atomic VIN_FILT co-route. **Before/After unconnected:** 78/78 · **shorting/clearance:** 0/0 · **Nets closed:** `VIN_FILT` (offset by Class-E GND zone islands 9→10). Ripped+restored in same transaction: VDD_GPIO north U@y9, P0.15 F via-bridge (vias@51/60,y16.5 + F@19.5), ENABLE F via-bridge, VDD2_MID south jog@y17.8. P0.08 probe after approved rips still blocked (VDD_nRF via@69.3,30 + via forest) — no live trial copper kept. STOP per still-78 rule; placement-move list for Hardware PM. Details: `reports/PASS30F_SUMMARY.json`.

---

## 2. Stackup note

### Present on PCB (copper / planes)

| Layer | Role on disk |
| --- | --- |
| F.Cu | Components, RF microstrip, short digital; GND pour zone present |
| In1.Cu | **GND** plane zone |
| In2.Cu | **VDD_nRF** plane zone |
| B.Cu | GPIO / returns; GND pour zone |
| Board thickness | **1.6 mm** (`(thickness 1.6)` in PCB setup) |
| Outline | 120 × 80 mm |

RF keepout zones (net 0 / empty name, F.Cu+B.Cu) exist in the PCB (west matching / U.FL region). Coordinate keepout changes with **RF Power Engineer via Hardware PM** — do not move LTE/GNSS/AUX 50 Ω trunks or matching without evidence.

### Dielectric / fab stackup — **NOT LOCKED (Hardware PM / Anand)**

Authoritative open questions are in **`docs/FAB_STACKUP_NOTES.md`** (2026-09-23): README assumes ~0.12 mm L1↔L2 prepreg for 0.20 mm `RF_50OHM`, while stale `fab/gerbers/nRF9161-DEV-BOARD-job.gbrjob` lists ~0.48 mm FR4 between Cu pairs and `Finish: None`. Layout must **not** treat either as manufacturer truth.

KiCad board setup has thickness **1.6 mm** and copper roles above, but **no** locked MaterialStackup coupon.

#### Working layout assumption (explicitly pending Anand answers in FAB_STACKUP_NOTES)

Until Anand confirms stack/order, L1–L2 H/Er, finish, and impedance coupon, Layout continues to treat the **README RF assumption** as the working geometry only:

| Layer | Working assumption | Use |
| --- | --- | --- |
| L1 F.Cu | 1 oz | Signals + RF microstrip |
| Prepreg L1–L2 | ~0.12 mm, εr ≈ 4.2 (JLC-like) — **UNCONFIRMED** | RF reference height |
| L2 In1.Cu | 1 oz | Solid **GND** under 50 Ω |
| Core | ~1.2 mm | |
| L3 In2.Cu | 1 oz | **VDD_nRF** pour |
| Prepreg L3–L4 | ~0.12 mm | |
| L4 B.Cu | 1 oz | Digital + GND pour |

**50 Ω working width:** ≈ **0.20 mm** on F.Cu over In1 GND — **recalculate after fab coupon**. Do not regenerate impedance-controlled Gerbers until unconnected=0 **and** stackup answers land.

**Surface finish:** unset (`Finish=None`) — PM/fab decision.

**Status for DFM §1:** remains **FAIL** until Anand closes `docs/FAB_STACKUP_NOTES.md`.

---

## 3. Remaining unconnected classes

Classification from `reports/UNCONNECTED_AFTER_FINAL.csv` (80 rows; matches `FINAL_FAB_RELEASE.md` narrative).

| Class | Count | Meaning |
| --- | --- | --- |
| **A** | **55** | U1 / fanout via / track ↔ header or island (GPIO, MAGPIO/MIPI/COEX, SIM, VDD_GPIO) |
| **E** | **9** | GND F.Cu zone-to-zone islands (dist 0.000 — zone fill / island merge) |
| **G** | **7** | Header duplicate branches (J13 ↔ J10/J11/J18 same-net copies) |
| **F** | **6** | F.Cu / mixed power & debug islands (VIN, nRESET, SWDCLK, P0.08) |
| **C** | **3** | DNP RF shunt stubs (ANT_FIT / AUX / AUX_FIT) — **do not rip 50 Ω trunks** |

### 3.1 Named walls (unchanged — load-bearing)

- **P0.15 west wrap (ROUTED, status OPEN count 0 in GPIO_FINAL):** U1 pad 25 @ (41.75, 26.75) → via **(41.75, 23.10)** → B.Cu courtyard snake x≈31.00–36.50, y≈22.50–59.20 into J18 / J12. **Do not delete.** Blocks naive P0.13–P0.18 U1→existing-B hops. East x=106 copper is fed from J18/J12 south stubs, not an independent U1 hop.
- **ENABLE vias @ (42.75, 41.10) and neighbors** — occupy south courtyard column needed for ADC exits; several ENABLE vias are also in the **via_dangling** set.
- **RF keepout west** ≈ (0, 20)–(24.2, 64) mm — MAGPIO/MIPI must jog **north of keepout**, not through matching.

### 3.2 Class F — power / debug opens (concrete)

| Net | Dist mm | Endpoints (approx) | Notes |
| --- | --- | --- | --- |
| VIN_FILT | — | closed in pass30f | B.Cu (55.35,13.3)→(51.9,13.3)→(51.9,21.9); restores held |
| VIN_F | 24.444 | (48.00, 12.60) ↔ (71.58, 19.06) | North power island |
| nRESET | 68.922 | B (101.68, 58.80) ↔ F (52.22, 10.80) | Long; also owns undersized via @ (45.68, 15.8) |
| SWDCLK | 26.202 | J8 stub (51.95, 4.73) ↔ U1 pad 33 (37.75, 26.75) | Debug critical |
| P0.08 | 32.730 / 49.281 | via/track islands ↔ J12.9 | USER button net |

### 3.3 Class A highlights — VIN / SIM / GPIO / west interfaces

**SIM (U1 → TPD3F303 / J7 side):**

| Net | Dist mm | U1 / island | Far end |
| --- | --- | --- | --- |
| SIM_CLK | 41.382 | U1 pad 46 (31.25, 26.75) | B.Cu track (68.14, 45.50) |
| SIM_IO | 51.975 | U1 pad 48 (30.25, 26.75) | F.Cu track (75.68, 52.00) |
| SIM_RST | 44.352 | U1 pad 43 (32.75, 26.75) | B.Cu track (71.68, 48.00) |
| SIM_1V8 | 46.507 | U1 pad 49 (29.75, 26.75) | F.Cu track (72.90, 44.10) |

**West MAGPIO / MIPI / COEX (U1 west edge ↔ J14/J15 @ x≈104):** MAGPIO0/1/2, MIPI_SCLK/SDATA/VIO, COEX0/1 — all still OPEN (~70–80 mm). Must skirt RF keepout north.

**ADC / south GPIO (blocked by P0.15 wrap + J18 PTH wall y≈60–65):** P0.13, P0.14, P0.16–P0.20 still OPEN U1↔J18/J12/J13. P0.15 itself is **ROUTED** via the wrap.

**East GPIO / SPI / I2C / UART copies:** many P0.05/07/09–12/21–31 U1↔J12/J13 opens; Class G adds J13↔J10/J11/J18 duplicate branches once primaries land.

**VDD_GPIO:** 5 open items (U1 pad 12 islands, header stubs, FB5).

**Near-miss stub:** P0.11 F.Cu track @ (48.62, 28.00) ↔ U1 pad 19 @ (44.00, 28.00) — **4.62 mm** (shortest Class A gap; courtyard congestion).

### 3.4 Class C — DNP RF shunts (coordinate with RF)

| Net | Dist mm | Notes |
| --- | --- | --- |
| ANT_FIT | 4.470 | C22 pad ↔ ANT_FIT track — short stub only |
| AUX | 17.355 | AUX track ↔ C23 |
| AUX_FIT | 23.000 | C24 ↔ AUX_FIT track |

Close with **short same-net stubs** or explicit NC policy — **never** by ripping L1/C21/C22 or GNSS trunks.

### 3.5 Class E — GND zone islands

Nine F.Cu GND zone-to-zone entries at (≈−0.05, −0.05). Likely fill / island merge after copper freeze + zone refill — not discrete signal routes.

### 3.6 DFM via issues to fold into the **same** routing pass (after connectivity P0)

From `reports/DRC_AFTER_CONNECT.json` + `docs/FAB_READY_CHECKLIST.md` §2:

| Issue | Count | Concrete |
| --- | --- | --- |
| **via_dangling** | **82** | Fanout vias connected on only one layer — nets include VDD_GPIO(7), VIN_F(6), ENABLE(4), VDD2(4), VIN_FILT(4), SIM_*, nRESET, P0.xx, MAGPIO1, MIPI_VIO, COEX0, … (45 unique nets). Completing B.Cu (or F.Cu) stubs on these vias is part of closing Class A/F, not a separate campaign after Gerbers. |
| **drill_out_of_range** | **2** | Via **P0.02** @ **(40.75, 43.5)** and via **nRESET** @ **(45.68, 15.8)** — hole **0.25 mm** &lt; min **0.30 mm** |
| **via_diameter** | **2** | **Same two vias** — diameter **0.45 mm** &lt; min **0.50 mm**. Upsize to project default **0.60 / 0.30** (or at least 0.50 / 0.30) when touching those nets. |

---

## 4. Prioritized fix plan

### P0 — Connectivity hard gate (`unconnected → 0`)

1. **Preserve P0.15 west wrap** and RF matching / keepouts — no rip-up without RF+PM sign-off.
2. **Close Class F power/debug islands** first where geometry is local: VIN_FILT (~10 mm F.Cu), then VIN_F, SWDCLK, nRESET (with via upsize), P0.08.
3. **SIM cluster** (SIM_CLK/IO/RST/1V8): private B.Cu or F.Cu paths U1 south/east → U4/J7 islands; avoid RF west box.
4. **ADC wall (P0.13–P0.14, P0.16–P0.20):** add staggered fanout vias **beyond** existing ring (1.15–2.1 mm), use **private** B.Cu columns (x≥64.6 east of J18, or west wrap corridor x≈25.1 **south of RF keepout**) — do not add another board-width y≈70 bus.
5. **Remaining GPIO / UART / SPI / I2C / I2S / PDM** U1→J12/J13 primaries, then Class G header duplicates.
6. **MAGPIO / MIPI / COEX:** north-of-keepout jog then east to J14/J15.
7. **VDD_GPIO** islands + FB5; Completing these also clears many dangling vias.
8. **Class C** DNP RF stubs / NC policy with RF Engineer.
9. **Class E** GND: refill F.Cu zones after copper edits; stitch islands if still reported.

### P1 — Fold into the **same** routing pass (DFM — do not defer to a post-Gerber cleanup)

Per Hardware PM / DFM (2026-09-23): after each connectivity move, **also**:

1. **Finish or remove** dangling vias on nets just closed (target: drive `via_dangling` down with unconnected). Prefer finishing B.Cu stubs over deleting load-bearing fanouts (ENABLE @ 42.75,41.10 is structural — connect or deliberately relocate with a plan).
2. **Fix undersized vias immediately when those nets are touched:**
   - P0.02 via (40.75, 43.5): resize ≥ **0.50 / 0.30** (prefer **0.60 / 0.30**)
   - nRESET via (45.68, 15.8): same
3. Re-check `track_dangling` on edited nets (expect some P0.15 stub warnings to remain until wrap topology is intentionally revised — do not “fix” by deleting wrap stubs).

### P2 — After unconnected = 0 (still before Gerbers)

1. Silk cleanup (147 overlap / 36 over copper).
2. Stackup + impedance coupon lock with Hardware PM / fab; update RF width if H/Er change.
3. Zone refill, lib_footprint_mismatch (3), EMS stencil notes.
4. Hand to DFM for green checklist → **only then** regenerate Gerbers / drill / IPC-356 / BOM / CPL / fab zip.

---

## 5. Explicit next routing pass proposal (ordered)

**Pass name:** `layout-pass30-connect` (proposed)  
**Tooling note:** Existing `scripts/*.py` assume `pcbnew` + `kicad-cli` (paths under `/home/anand/...`). Neither is available on this shared box right now — **do not blind-edit** the `.kicad_pcb` sexp without DRC. Next copper work should run where KiCad CLI works, with backup first.

| Step | Action | Target nets / geometry | Expected effect |
| --- | --- | --- | --- |
| 0 | Backup live PCB to `.mcp-backups/layout-pass30-<timestamp>/` | — | Safety |
| 1 | Baseline DRC JSON | record **before** `unconnected_items`, `via_dangling`, drill/via_diameter | PM ping numbers |
| 2 | F.Cu surgical: VIN_FILT island | (55.35,12.00)→(53.20,21.90), width power class | −1 F if clear |
| 3 | F.Cu surgical: VIN_F | (48.00,12.60)→(71.58,19.06) with jogs around north parts | −1 F |
| 4 | SWDCLK U1 pad 33 ↔ J8 stub | Prefer B.Cu under courtyard exit, avoid RF | −1 F |
| 5 | nRESET: connect islands **and** upsize via (45.68,15.8) to 0.60/0.30 | Long B↔F | −1 F + clear 1 drill/via_diameter |
| 6 | Upsize P0.02 via (40.75,43.5) while routing P0.02 if still open | — | Clear 2nd drill/via_diameter |
| 7 | P0.11 short stub 4.62 mm if clearance OK | (48.62,28.00)→(44.00,28.00) | May only merge fanout island; still need header |
| 8 | SIM_CLK / RST / IO / 1V8 private exits | South/east of U1, no RF box | −4 A |
| 9 | ADC group with new fanout vias + private B columns | P0.13/14/16–20; **keep P0.15 wrap** | Multiple A |
| 10 | Remaining J12/J13 GPIO + Class G duplicates | East headers x≈116 | Multiple A/G |
| 11 | MAGPIO/MIPI/COEX north-then-east | J14/J15 | −8 A |
| 12 | VDD_GPIO island merge + dangling via B stubs | Clears many of 82 dangling | A + dangling |
| 13 | Class C RF DNP stubs with RF Engineer | C22/C23/C24 only | −3 C |
| 14 | Zone refill → Class E GND | — | −9 E |
| 15 | After-DRC JSON | record **after** counts; ping Hardware PM with before/after | Gate check |

**Stop / escalate if:** any step raises `shorting_items` or `unconnected_items`, or requires entering RF keepout / matching copper.

---

## 6. Process gates (Hardware PM)

- Coordinate **RF keepouts** and Class C / matching with **RF Power Engineer via Hardware PM**.
- **No Gerbers** until `unconnected_items = 0` **and** DFM (`docs/FAB_READY_CHECKLIST.md`) signs off. Do not ask DFM for Gerbers while unconnected > 0.
- When a routing pass drops unconnected, capture **exact before/after** counts (and via_dangling / drill/via_diameter) for the PM ping.
- Stale `fab/gerbers/` (2026-09-16) must be replaced only after freeze — not used for fab now.

---

## 7. Session outcome — `layout-pass30-connect` (2026-09-23 09:51 IST)

| Item | Result |
| --- | --- |
| PCB copper edited | **Yes** (pcbnew 9.0.2 + `kicad-cli`) |
| Backup | `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30-connect-20260923-094344` (+ `.mcp-backups/pass30-connect/start.kicad_pcb`) |
| **Before → after unconnected** | **79 → 80** (`reports/DRC_PASS30_BEFORE.json` / `DRC_PASS30_AFTER.json`) |
| Shorting before → after | **0 → 0** |
| Clearance before → after | **6 → 0** (zone refill; no new shorts) |
| via_dangling | **80 → 80** |
| drill_out_of_range / via_diameter | **0 → 0** (already fixed pre-pass) |
| Gerbers | **Not generated** |

### Placed / closed

| Item | Detail |
| --- | --- |
| **U3** | `TPS22919DCKR` footprint `SOT-363_SC-70-6` @ **(26.5, 47.0)** mm, orient 180° (east of RF keepout) |
| **FB5** | `L_0603_1608Metric` → **`L_0402_1005Metric`** @ **(23.8, 47.65)** orient 180° |
| Nets closed | **`GNSS_VBIAS_SRC`** U3.VOUT→FB5.1; **`GNSS_VBIAS`** FB5.2→bias-T (B.Cu); U3.GND stub |
| Class C | Stub attempts on C21–C24/C31–C32 where clearance allowed (DNP policy; trunks not ripped) |
| P0.15 west wrap | **Preserved** |

### Deferred (honest)

- **U3.VIN (`VDD_GPIO`)** and **U3.ON (`COEX0`)** — courtyard congestion (P0.00/P0.04/P0.13 walls + via forest). Ratsnest remains.
- Class F surgical (`VIN_FILT`, `VIN_F`, `SWDCLK`, `nRESET`, `P0.02`, `P0.08`) — blocked geometry; not forced.
- SIM / ADC / MAGPIO / MIPI / COEX header routes — stopped before risky RF edits.
- Schematic `04_GNSS`: U3 VIN/VOUT/GND global labels do not appear in netlist (ON=`COEX0` does); PCB nets assigned manually to match approved topology.

### Scripts / reports

- `scripts/final_pass30.py`, `scripts/final_pass30b.py`
- `reports/PASS30_SUMMARY.json`, `reports/DRC_PASS30_BEFORE.json`, `reports/DRC_PASS30_AFTER.json`
- Also `/tmp/drc_pass30_before.json`, `/tmp/drc_pass30_after.json`

**Success gate:** clear progress (U3 placed + FB5 0402 + bias path closed) with shorts held at 0; unconnected +1 from new U3 EN/VIN pads still open.

---

## 8. RF layout locks (still in force)

1. West RF keepout x≈**0–24.2**, y≈**20–64** — respected (U3 placed at x=26.5).
2. Class C DNP stub-terminate policy — applied where clear.
3. Do not split In1 GND under 50 Ω; no digital under matching on F.Cu.

---

*End of PCB Layout Review — pass30-connect 2026-09-23 IST*


---

## Pass30c (2026-09-23 10:03 IST)

**Goal:** Sync schematic U3 nets, then close U3.VIN / U3.ON and Class F surgically.

| Metric | Before | After |
| --- | ---: | ---: |
| unconnected_items | **80** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |
| hole_clearance | 0 | 0 |

**Netlist sync:** `reports/netlist_after_u3.xml` + ERC Errors=0 (`reports/ERC_U3_after.rpt`). U3 signal pads already matched schematic (`VDD_GPIO` / `GND` / `COEX0` / `GNSS_VBIAS_SRC`); pads 4/5 assigned `unconnected-(U3-NC-Pad4)` / `unconnected-(U3-QOD-Pad5)`. No manual VIN/VOUT/ON overrides retained beyond netlist.

**Closed:**
- `VDD_GPIO` U3.1 VIN — F stub to via (28.5, 40) then B north to (40.17, 19.13)
- `COEX0` U3.3 ON — F west-north-east around VIN (26.2 → 38 corridor) to via (33, 43) then B to spine (38.8, 43)

**Still open (priority leftovers):**
- Class F: `VIN_FILT`, `VIN_F`, `SWDCLK`, `nRESET`, `P0.02`, `P0.08` (power/debug congestion; no safe path without clearance hits)
- `COEX0` north island still split from south F stub (`F@38.75,37.25` ↔ `via@31.11,22`)
- Other `VDD_GPIO` header/island opens (U3 pad itself is connected)
- SIM / ADC / MAGPIO / MIPI / COEX headers

**Constraints held:** shorting=0; clearance=0; P0.15 B.Cu west wrap intact (17 segments); no Gerbers; RF keepout x≈0–24.2 respected for new copper (U3 routes x≥26.2).

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30c-20260923-095159`  
**DRC:** `reports/DRC_PASS30C_BEFORE.json`, `reports/DRC_PASS30C_AFTER.json`  
**Summary:** `reports/PASS30C_SUMMARY.json`



---

## Pass30d (2026-09-23 IST)

**Goal:** Drop unconnected below 78 by closing Class F (`VIN_FILT`→`VIN_F`→`SWDCLK`→`nRESET`→`P0.02`/`P0.08`) plus easy `COEX0` north island. Aggressive non-critical blocker jogs allowed; keep shorting=0; do not rip P0.15 west wrap; RF keepout intact.

| Metric | Before | After |
| --- | ---: | ---: |
| unconnected_items | **78** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |

**Closed:** none (all Class F attempts aborted or failed clearance).

**What blocked (honest):**
- `VIN_FILT`: geometric B corridor from via(55.35,13.3) to via(51.9,21.9) requires gap through `VDD_GPIO` H@y=14.8 + `P0.15` north trunk@y=15.35 + `ENABLE` H@y=20.3 + `VDD2` H/V. Simulated deep/north reconnect jogs made the path clear in `track_clear`, but live DRC reported **shorting_items=10 / tracks_crossing=11** — copper discarded.
- `P0.08`: farthest progress — jogged `COEX2` V@x=72, `ENABLE` V@x=62.5, `ENABLE` H@y=28; then blocked by `VDD1` via@53.7 and `P0.10`/`P0.11` via forest near dest via@46.2.
- `VIN_F` / `SWDCLK` / `nRESET` / `P0.02` / `COEX0`: via/track forests; no safe DRC-clean path found.

**Constraints held:** shorting=0 (failed attempts restored); P0.15 west wrap intact; RF keepout respected; no Gerbers.

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30d-20260923-100505`  
**DRC:** `reports/DRC_PASS30D_BEFORE.json`, `reports/DRC_PASS30D_AFTER.json`  
**Summary:** `reports/PASS30D_SUMMARY.json`


---

## Pass30e (2026-09-23 16:04 IST)

**Goal:** Co-route VIN_FILT with ENABLE fully restored; P0.08 if corridors allow.

| Metric | Before | After |
| --- | ---: | ---: |
| unconnected_items | **78** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |

**Closed:** none. VDD_GPIO + P0.15 restores proven in isolation; **ENABLE@y20.3 restore failed** (VDD1 / C5–C6 / VIN_FILT F spine). All trial copper reverted.

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30e-20260923-102320`  
**DRC:** `reports/DRC_PASS30E_BEFORE.json`, `reports/DRC_PASS30E_AFTER.json`  
**Summary:** `reports/PASS30E_SUMMARY.json`

---

## Pass30f (2026-09-23 10:42 IST)

**Goal:** ONE atomic co-route — close VIN_FILT (and VIN_F if cheap) with ENABLE fully restored in the same transaction; P0.08 if corridors allow. Drive unconnected below 78; shorting=0 clearance=0. No footprint moves. No Gerbers.

| Metric | Before | After |
| --- | ---: | ---: |
| unconnected_items | **78** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |
| tracks_crossing | 0 | 0 |

**Closed:** `VIN_FILT` (B.Cu path (55.35,13.3)→(51.9,13.3)→(51.9,21.9) w=0.30). Count stayed 78 because Class-E F.Cu GND zone-island reports went 9→10 (fill artifact @ ≈−0.05,−0.05).

**Ripped + restored (kept on board):**
- `VDD_GPIO` H@y14.8 → north U @y=9.0
- `P0.15` north trunk@y15.35 (west wrap untouched, 21 segs) → F via-bridge vias@(51.0,16.5)/(60.0,16.5) + F@y19.5
- `ENABLE` H@y20.3 → F via-bridge via existing (50.85,23.15)/(56.50,20.30)
- `VDD2_MID` H@y16.87 → south U @y17.8 (needed so P0.15 east via does not short)

**P0.08:** probe after ripping ENABLE H@y28 + V@x62.5 + COEX2@x72 — still blocked (VDD_nRF via@69.3,30 and via/pad forest). Probe only; live board not polluted.

**VIN_F / SWDCLK:** deferred to 30g (not cheap after this cycle).

**STOP:** unconnected still 78 → no further thrash. Placement-move proposals (≤3 mm, do **not** move without Hardware PM):
| Ref | Current xy | Proposed Δ | Why |
| --- | --- | --- | --- |
| TP11 | (60.0, 30.0) | +y 2.5 → (60.0, 32.5) | Free F y≈30 for P0.08 |
| R2 | (58.0, 26.0) | −y 2.0 → (58.0, 24.0) | Clear F y≈28 ENABLE/P0.08 |
| C6 | (51.0, 27.0) | −x 2.0 → (49.0, 27.0) | Open B column near ENABLE/VDD1 |
| TP19 | (52.0, 22.0) | +x 2.5 → (54.5, 22.0) | Off VIN_FILT/ENABLE F spine |

**Constraints held:** shorting=0; clearance=0; P0.15 west wrap intact; RF keepout / matching / U3 GNSS bias untouched; no footprint moves; no Gerbers.

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30f-20260923-103606`  
**DRC:** `reports/DRC_PASS30F_BEFORE.json`, `reports/DRC_PASS30F_AFTER.json`  
**Summary:** `reports/PASS30F_SUMMARY.json`


---

## Pass30g (2026-09-23 IST)

**Goal:** ONE honest cycle — apply Hardware-PM-approved four placement moves, zone refill, close P0.08 (then VIN_F/SWDCLK if cheap). shorting=0 clearance=0. No Gerbers. Protect P0.15 west wrap + RF/U3.

| Metric | Before | After (restored) |
| --- | ---: | ---: |
| unconnected_items | **78** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |

**Result: STOP — placement set not DRC-legal; board reverted.**

### What was attempted
| Ref | Requested | Outcome |
| --- | --- | --- |
| TP11 | (60,30)→(60,32.5) | Applied in bundle; **reverted** (bundle shorting) |
| R2 | (58,26)→(58,24) | **SKIPPED** — R2.1 VIN_FILT @(58,22.54) overlaps TP20 VDD_nRF @(58,22) |
| C6 | (51,27)→(49,27) | Applied; VDD1 reattach along x≈48.7 shorts **DEC0/P0.11**; **reverted** |
| TP19 | (52,22)→(54.5,22) | Applied; pad shorts **VDD2 via@(54.50,21.20)**; **reverted** |
| VDD_nRF via | (69.3,30)→(69.3,28) | Attempted with bundle; **reverted** |

Mid-attempt DRC (not kept): shorting=11, tracks_crossing=7.

### P0.08
Not closable this cycle. Even prior /tmp probes with TP11/C6/TP19 + via jog + ENABLE/COEX2 rip remain walled by **VDD2 verticals** @x=52.22 and @x=54.50 on B@y≈30.

### Next proposals (need Hardware PM)
1. **TP20** (58,22)→(56,20) — unlock R2→(58,24)
2. **Revise TP19** target — (54.5,22) illegal; try (56.5,22) or (52,20)
3. **VDD2 via-bridge / east U-jog** at y≈30 (primary B corridor wall)
4. **C6 VDD1 reattach** via existing via@(49.2,25.6) — avoid DEC0 column
5. Optional **GND via** (80,30)→(80,32.5) for dest approach

**Constraints held on live board:** shorting=0; clearance=0; P0.15 west wrap 21 segs; RF keepout / U3 untouched; no Gerbers; no footprint moves left on board.

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30g-20260923-104551`  
**DRC:** `reports/DRC_PASS30G_BEFORE.json`, `reports/DRC_PASS30G_MID.json`, `reports/DRC_PASS30G_AFTER.json`  
**Summary:** `reports/PASS30G_SUMMARY.json`
