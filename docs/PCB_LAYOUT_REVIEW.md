# PCB Layout Review — nRF9161-DEV-BOARD

**Role:** PCB Layout Engineer  
**Working path:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Review date:** 2026-09-23 09:27 IST (Asia/Calcutta)  
**Overall:** **NOT FABRICATION-READY** — connectivity hard gate open  
**Gerbers:** **Do not generate** until `unconnected_items = 0` and DFM checklist is green  

Cross-refs: `docs/FAB_READY_CHECKLIST.md` (DFM gate **RED**), `docs/FAB_STACKUP_NOTES.md`, `docs/PM_STATUS.md`, `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`, `reports/UNCONNECTED_AFTER_FINAL.csv`.

---

## 1. Current connectivity status

| Metric | Count | Source |
| --- | --- | --- |
| **unconnected_items** | **80** | `reports/DRC_AFTER_CONNECT.json` (`unconnected_items` length; date `2026-09-18T02:01:29+05:30`); `reports/UNCONNECTED_AFTER_FINAL.csv` (80 data rows); `reports/FINAL_FAB_RELEASE.md` |
| **shorting_items** | **0** | Same JSON + FINAL_FAB_RELEASE |
| **clearance** | **0** | Same |
| **hole_clearance** | **0** | Same |
| via_dangling | **82** | `DRC_AFTER_CONNECT.json` violations (fold into next routing pass after / with connectivity) |
| drill_out_of_range | **2** | Same — vias with **0.25 mm** hole (board min **0.30 mm**) |
| via_diameter | **2** | Same — vias with **0.45 mm** diameter (board min **0.50 mm**); same two vias as drill violations |
| track_dangling | 13 | Same JSON (includes load-bearing P0.15 west-wrap stubs) |
| silk_overlap / silk_over_copper | 147 / 36 | Cosmetics — after copper freeze |
| Live copper | 777 segments, 250 vias | Parsed from live `nRF9161-DEV-BOARD.kicad_pcb` |

### Count reconciliation (do not mix eras)

| Report | unconnected | Notes |
| --- | --- | --- |
| `reports/DRC_SUMMARY.txt` | 116 | Older summary — **superseded** |
| `reports/DRC_BEFORE_FINAL.json` | 120 | Pre-final pass |
| `reports/DRC_final.json` / `FINAL_DESIGN_REVIEW.md` | 104 | Mid campaign |
| `reports/DRC_AFTER_CONNECT_FULL.json` | 98 | Intermediate |
| **`DRC_AFTER_CONNECT.json` / FINAL_FAB / CSV** | **80** | **Authoritative for this review** |

`kicad-cli` / `pcbnew` are **not available** in this box session, so a fresh DRC could not be re-run. Authoritative numbers remain the AFTER_CONNECT / FINAL_FAB set above. On-disk `fab/gerbers/` CreationDate **2026-09-16** is **stale** and must not be used for fab (DFM checklist §5).

**Pass delta (this Layout Engineer session):** review / documentation only — **no copper edit**.  
**Before unconnected:** 80 · **After unconnected:** 80 · **Nets closed:** none.

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
| VIN_FILT | 10.131 | (55.35, 12.00) ↔ (53.20, 21.90) | Shortest F power island — candidate for careful F.Cu jog |
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

## 7. Session outcome (Layout Engineer)

| Item | Result |
| --- | --- |
| PCB copper edited | **No** (review-only) |
| Backup taken | N/A (no edit); prior backups exist under `.mcp-backups/` |
| Nets closed | **None** |
| Unconnected before → after | **80 → 80** |
| Shorting | **0** (unchanged) |
| Why no auto-route | `pcbnew` / `kicad-cli` missing on box; remaining opens sit on P0.15 wrap, RF keepout, and courtyard congestion — blind sexp edits are reckless |
| DFM fold-in acknowledged | Next connect pass must also attack `via_dangling`×82 and resize the two 0.45/0.25 vias (`P0.02` @ 40.75,43.5; `nRESET` @ 45.68,15.8) |
| This document | `docs/PCB_LAYOUT_REVIEW.md` |

---

## 8. RF layout locks for pass30 (Hardware PM + RF Power — 2026-09-23)

**Status:** Locked for when copper tooling returns. **No copper until** pcbnew+kicad-cli on shared box **or** vyomos local exec. Source: Hardware PM handoff; details in `docs/RF_POWER_REVIEW.md` §Layout pass30 coordination.

1. **West RF keepout (mandatory):** x ≈ **0–24.2 mm**, y ≈ **20–64 mm**.
   - No digital under matching on **F.Cu**.
   - MAGPIO / MIPI / COEX: **north-then-east on B.Cu**.
   - Do **not** split **In1 GND** under 50 Ω trunks.
   - Stay ≥ **0.5 mm** outside matching courtyards.

2. **Class C DNP 50 Ω shunts C21–C24, C31–C32:** STUB-TERMINATE ≤ **2 mm** same-net stub to the RF-side pad; GND pad to solid GND. Do **not** leave open, populate, or rip trunks.

3. **GNSS bias** remains **Schematic Engineer** scope (not layout).

Pass30 sequence otherwise unchanged (VIN_FILT → … → Class C only after RF confirms — now locked as stub-terminate above).

---


### Pass30 add-ons (Schematic complete — Hardware PM 2026-09-23)

When tooling unlocks copper (still **idle** until pcbnew/local exec), **after backup** add to sequence:

1. **Place/route U3** `TPS22919DCKR` (SC-70-6) near GNSS bias-T:
   - VIN = `VDD_GPIO`
   - VOUT → **FB5** (0402) → `GNSS_VBIAS`
   - EN = `COEX0`
2. **FB5 footprint:** update to **0402** land if PCB still has an older size.
3. **Stub-terminate** DNP **C21–C24 / C31–C32** per RF locks (§8): ≤2 mm same-net stub to RF-side pad; GND pad to solid GND.

Note: unconnected remains **80** today; placing U3 will add nets until those nets are routed. No Gerbers until unconnected = 0.


*End of PCB Layout Review — 2026-09-23 IST*
