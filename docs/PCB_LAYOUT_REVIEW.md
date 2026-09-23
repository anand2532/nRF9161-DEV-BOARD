# PCB Layout Review — nRF9161-DEV-BOARD

**Role:** PCB Layout Engineer  
**Working path:** `/workspace/kicad-projects/nRF9161-DEV-BOARD`  
**Review date:** 2026-09-23 11:52 IST (Asia/Calcutta) — pass30n executed
**Overall:** **NOT FABRICATION-READY** — connectivity hard gate open  
**Gerbers:** **Do not generate** until `unconnected_items = 0` and DFM checklist is green  

Cross-refs: `docs/FAB_READY_CHECKLIST.md` (DFM gate **RED**), `docs/FAB_STACKUP_NOTES.md`, `docs/PM_STATUS.md`, `reports/FINAL_FAB_RELEASE.md`, `reports/DRC_AFTER_CONNECT.json`, `reports/UNCONNECTED_AFTER_FINAL.csv`.

---

## 1. Current connectivity status

| Metric | Count | Source |
| --- | --- | --- |
| **unconnected_items** | **72** | `reports/DRC_PASS30M_AFTER.json` (live `kicad-cli` 9.0.2); nRESET reverted; Stage A+pass30i–30l kept |
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
| **`DRC_PASS30M_AFTER.json`** | **74** | **Authoritative after pass30m** (nRESET probed+reverted; Stage A+pass30i–30l kept) |
| `DRC_PASS30L_AFTER.json` | 74 | Prior — SWDCLK closed; nRESET reverted |
| `DRC_PASS30K_AFTER.json` | 75 | Prior — VIN_F closed; Stage A+pass30i/30j kept |
| `DRC_PASS30J_AFTER.json` | 76 | Prior — P0.08→J12.9 stitch |
| `DRC_PASS30I_AFTER.json` | 77 | Prior — P0.08 U1↔SW3/R14 only |

Live `kicad-cli` 9.0.2 DRC was re-run for pass30c (`reports/DRC_PASS30C_BEFORE.json` / `reports/DRC_PASS30C_AFTER.json`). On-disk `fab/gerbers/` CreationDate **2026-09-16** remains **stale** and must not be used for fab (DFM checklist §5).

**Pass delta (pass30c):** netlist sync + U3.VIN + U3.ON closed. **Before unconnected:** 80 · **After unconnected:** 78 · **Nets closed:** VDD_GPIO (U3.1), COEX0 (U3.3). Class F deferred. shorting/clearance=0. P0.15 wrap preserved.

**Pass delta (pass30e):** Aggressive Class F corridor clear (PM-approved rip list). **Before/After unconnected:** 78/78 · **shorting/clearance:** 0/0 · **Nets closed:** none. ENABLE restore was the failing link. All trial copper reverted. Details: `reports/PASS30E_SUMMARY.json`.

**Pass delta (pass30f):** ONE atomic VIN_FILT co-route. **Before/After unconnected:** 78/78 · **shorting/clearance:** 0/0 · **Nets closed:** `VIN_FILT` (offset by Class-E GND zone islands 9→10). Ripped+restored in same transaction: VDD_GPIO north U@y9, P0.15 F via-bridge (vias@51/60,y16.5 + F@19.5), ENABLE F via-bridge, VDD2_MID south jog@y17.8. P0.08 probe after approved rips still blocked (VDD_nRF via@69.3,30 + via forest) — no live trial copper kept. STOP per still-78 rule; placement-move list for Hardware PM. Details: `reports/PASS30F_SUMMARY.json`.

**Pass delta (pass30i):** ONE atomic P0.08 + ENABLE/COEX2 co-route (Stage A kept; no placement). Ripped ENABLE V@62.5 / V@76.8 / H@y28 + COEX2 V@72; placed P0.08 B@y30.25; restored with F via-bridges (ENABLE@x62.5 ys/yn=29.6/30.9, COEX2@x72 same, ENABLE east F-hop to x=79.2). **Before/After unconnected:** 78/77 · shorting/clearance/crossing 0. Closed P0.08 U1↔SW3/R14; J12.9 still open. P0.15 west preserved. Details: `reports/PASS30I_SUMMARY.json`.

**Pass delta (pass30j):** ONE honest cycle — stitch P0.08 island→J12.9. B column @x=65.2 with F via-hops over COEX2/COEX0/P0.18+P0.17; rip+restore P0.15 bottom H (wide F-bridge 61.5–68.5 @y77.45) + P0.01 (final F-bridge 24.5–27.2 @y78.5 + column U-jog F@y74.5); B H@y79 → via(26.32,78) → F to J12.9. **Before/After unconnected:** 77/76 · shorting/clearance/crossing 0. P0.15 west wrap preserved (21 segs). VIN_F/SWDCLK skipped (not cheap). Details: `reports/PASS30J_SUMMARY.json`.

**Pass delta (pass30o):** P0.02 atomic close (west col x=27.5, B@y4.5, east col x=89). Preflight rip: VDD_GPIO V@48.05 (U-jog west), P0.01 H@15.2 (F-hop 88.2–89.8), P0.15 east H@7.2 (F-hop 88.2–89.8). **Before/After unconnected:** 73/72 · shorting/clearance/crossing 0. P0.15 west wrap preserved. Stage A + pass30i–30n kept. No Gerbers. Details: `reports/PASS30O_SUMMARY.json`.

**Pass delta (pass30n):** ONE atomic nRESET co-route (F@y10.8 under VDD_nRF/JP1). Preflight rip (3): P0.15 (72.0,15.35)→(72.0,7.2), COEX2 (72.0,24.6)→(105.1,24.6), P0.01 (86.14,15.2)→(105.55,15.2). nRESET **KEPT** B@y12.6 + F clearance hop + F-hop 69–71.5; COEX2/P0.01/P0.15 east co-restored. **Before/After unconnected:** 74/73 · shorting/clearance/crossing 0. P0.02 skipped (no free corridor). Stage A + pass30i–30l kept. P0.15 west wrap preserved. No Gerbers. Details: `reports/PASS30N_SUMMARY.json`.

**Pass delta (pass30m):** ONE atomic nRESET co-route. Preflight rip list (1 seg) recorded before copper edit: P0.15 B.Cu (72.0,15.35)→(72.0,7.2). Ripped → routed nRESET B@y12.6 + F-hop 69.0–71.5 over VDD_GPIO/VIN_F → P0.15 F-bridge restore → mid DRC clearance=1 crossing=2 (shorting=0) → **atomic revert**. Colliding copper: nRESET×COEX2, nRESET×P0.01 on B; clearance vs VDD_nRF via@(57.95,12.0). P0.02 not attempted. **Before/After unconnected:** 74/74 · shorting/clearance/crossing 0. Stage A + pass30i–30l kept. P0.15 west wrap preserved. No Gerbers. Details: `reports/PASS30M_SUMMARY.json`.

**Pass delta (pass30l):** ONE honest Class-F cycle (SWDCLK→nRESET→P0.02; option C scan). SWDCLK mixed F/B west column x=34.2 + F-hop over VDD_GPIO H@19.13 + F north band y=1.5 around J8.3 into via@(53.65,4.73) — **closed**. nRESET @y12.6 corridor probed then **reverted** (shorting/clearance/crossing). P0.02 skipped. Option C: no cheap non-RF/U3 stub. **Before/After unconnected:** 75/74 · shorting/clearance/crossing 0. P0.15 west wrap preserved (21 segs). Stage A + pass30i–30k kept. No J8 move. No Gerbers. Details: `reports/PASS30L_SUMMARY.json`.

**Pass delta (pass30k):** ONE honest Class-F cycle (VIN_F→SWDCLK→nRESET→P0.02). VIN_F B@y11 + F-hop over VDD_GPIO@x70 + B to FB4 island; P0.15 east H@y15.35 F-bridged (69.3–72.0). SWDCLK/nRESET probed then left (restore not DRC-clean in one attempt); P0.02 skipped — STOP. **Before/After unconnected:** 76/75 · shorting/clearance/crossing 0. P0.15 west wrap preserved (21 segs). Stage A + pass30i/30j kept. Details: `reports/PASS30K_SUMMARY.json`.

**Pass delta (pass30h):** ONE honest cycle. Stage A KEPT (VDD2 B walls→via-bridge @x=58; VDD_nRF via (69.3,30)→(69.3,31.5) north). P0.08 probe CLEAR @y=30.25 after ENABLE/COEX2 rip but restore re-crosses / jog hits VDD_GPIO — **reverted**. Stage B placement REVERTED (shorting=5; C6.1@x=48.68 DEC0). **Before/After unconnected:** 78/78 · shorting/clearance/crossing 0. Details: `reports/PASS30H_SUMMARY.json`.

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


---

## Pass30h (2026-09-23 11:07 IST)

**Goal:** ONE honest cycle — Stage A copper-only first (VDD2 via-bridge, optional GND via, VDD_nRF via jog); Stage B placement only if still needed; zone refill; close P0.08 (ENABLE H@y28 rip/restore OK); VIN_F/SWDCLK if cheap. shorting=0 clearance=0. No Gerbers. Protect P0.15 west wrap + RF/U3.

| Metric | Before | After |
| --- | ---: | ---: |
| unconnected_items | **78** | **78** |
| shorting_items | 0 | 0 |
| clearance | 0 | 0 |
| tracks_crossing | 0 | 0 |

**Result: STOP — Stage A kept; P0.08 and Stage B reverted; no signal-net drop.**

### Stage A (applied, DRC clean)
| Edit | Detail | Result |
| --- | --- | --- |
| VDD2 B walls | Rip (52.22,26.75)–(52.22,32) and (54.5,21.2)–(54.5,32) | Done |
| VDD2 via-bridge | Vias@(58,29.55)/(58,30.95) + F hop; south B feeder @y=29.55; north via stitches to y=32 (no north feeder across corridor) | Done |
| VDD_nRF via | (69.3,30)→(**69.3,31.5**) north ≤2 mm — not south onto VIN_FILT F@y28.8 | Done |
| GND via | (80,30)→(80,32.5) | **SKIPPED** — shorts VDD_GPIO F |

### P0.08
Probe after Stage A + ENABLE/COEX2 temp rip: **CLEAR** `B_y30.25` path `(46.2,30)→(46.2,30.25)→(78.5,30.25)→(78.5,26)→(79.67,26)`.  
Live commit with original ENABLE/COEX2 restore → `tracks_crossing=4` (ENABLE x=62.5/76.8, H@y28, COEX2 x=72). Jogged restore → clearance vs VDD_GPIO via. **P0.08 copper REVERTED.**

### Stage B (reverted)
TP20→(56,20), R2→(58,24), TP11→(60,32.5), TP19→(52,20), C6→(49,27). Mid DRC shorting=5 clearance=2 crossing=7. **Root:** C6@(49,27) places pad1 at **x=48.68** (forbidden DEC0/P0.11 column). Bundle reverted; Stage A preserved.

### Signal deltas
None (empty). Class-E GND islands unchanged (total still 78).

### Next proposals
1. **Atomic ENABLE/COEX2 + P0.08 co-route** — rip crossing segments, place P0.08 @y30.25, restore ENABLE/COEX2 with jogs pre-cleared vs VDD_GPIO vias
2. **C6 reattach** — after C6→(49,27), stitch **only** via@(49.2,25.6) with path x≥49.0 (never x≈48.7 vertical)
3. Optional GND via jog needs a clearance-safe target (not 80,32.5)

**Constraints held:** shorting=0; clearance=0; tracks_crossing=0; P0.15 west wrap preserved; RF keepout / U3 untouched; no Gerbers.

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30h-20260923-105755`  
**DRC:** `reports/DRC_PASS30H_BEFORE.json`, `reports/DRC_PASS30H_MID.json`, `reports/DRC_PASS30H_AFTER.json`  
**Summary:** `reports/PASS30H_SUMMARY.json`


---

## Pass30i — atomic P0.08 co-route (2026-09-23 11:12 IST)

**Goal:** Atomic ENABLE/COEX2 + P0.08 co-route on Stage A board. No placement. shorting=0 clearance=0.

**Result: KEEP — unconnected 78→77; P0.08 U1↔SW3/R14 closed.**

### Geometry kept
- **P0.08** B: `(46.2,30)→(46.2,30.25)→(78.5,30.25)→(78.5,26)→(79.67,26)` w=0.18
- **ENABLE @x=62.5** via-bridge: vias@(62.5,29.6)/(62.5,30.9) + F hop (B U-jog impossible across P0.08 H)
- **COEX2 @x=72** via-bridge: vias@(72,30.9)/(72,29.6) + F hop
- **ENABLE east**: via-bridge vias@(76.8,30.9)/(79.2,30.9) + F hop; B reconnect `(79.2,28)→(90.38,28)`

### Remaining
- **P0.08 → J12.9** — closed in pass30j
- Class E GND islands / other Class F (VIN_F, SWDCLK, nRESET) unchanged
- Stage B placement still illegal (C6.1 DEC0) — not attempted

### Next proposals
1. Route P0.08 west/south stub to J12.9 (private column; protect P0.15 wrap)
2. VIN_F / SWDCLK Class F if corridor free after P0.08 east copper
3. Stage B C6 reattach only with pad1 stitch x≥49.0 (never vertical @x=48.68)

---

## Pass30j — P0.08 → J12.9 stitch (2026-09-23 11:24 IST)

**Goal:** Stitch P0.08 from pass30i island (U1↔SW3/R14) to J12.9. Keep Stage A + pass30i ENABLE/COEX2/P0.08 trunk. No placement. shorting=0 clearance=0.

**Result: KEEP — unconnected 77→76; P0.08 fully closed to J12.9.**

### Geometry kept
- **P0.08 trunk** (pass30i) untouched: B `(46.2,30)→…→(79.67,26)`
- **Branch** B@x=65.2 from H@y30.25 south with F via-hops:
  - COEX2 @y38 → vias 37.45/38.55
  - COEX0 @y62 → vias 61.45/62.55
  - P0.18+P0.17 @y72.8/73.4 → vias 72.25/73.95
- **Bottom** B H@y79 `(65.2,79)→(26.32,79)` → B drop → via(26.32,78) → F to J12.9 pad
- **Restores (same transaction):**
  - P0.15 bottom H: wide F-bridge vias@(61.5,77.45)/(68.5,77.45)
  - P0.01: final F-bridge 24.5–27.2 @y78.5 + column U-jog F@y74.5 (62–68)

### Trial note
First restore pair (P0.15@77.45 + P0.01 U-jog@77.8) caused shorting=5/clearance=3 — **reverted**; widened/separated restores then KEPT.

### Remaining / deferred
- VIN_F / SWDCLK: skipped this cycle (Class F still congested; not cheap)
- Class E GND islands / other Class F unchanged
- No Gerbers

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30j-20260923-112326`  
**DRC:** `reports/DRC_PASS30J_BEFORE.json`, `reports/DRC_PASS30J_MID.json`, `reports/DRC_PASS30J_AFTER.json`  
**Summary:** `reports/PASS30J_SUMMARY.json`

---

## Pass30k — Class F VIN_F close (2026-09-23 11:34 IST)

**Goal:** Class F order VIN_F → SWDCLK → nRESET → P0.02 (one net at a time; DRC-clean before next). Keep Stage A + pass30i/30j. Co-restore ripped nets. shorting=0 clearance=0. No placement. No Gerbers. Stop after two Class-F restore failures.

**Result: KEEP — unconnected 76→75; VIN_F closed.**

### Geometry kept
- **VIN_F** B: `(49.30,12.60)→(49.30,11.00)→(69.20,11.00)` w=0.30
- **VIN_F** F-hop over VDD_GPIO V@x70: vias@(69.20,11.00)/(70.80,11.00) + F H
- **VIN_F** B: `(70.80,11.00)→(70.80,16.20)→(71.575,16.20)→(71.575,19.062)` into FB4 island
- **P0.15 restore:** east H@y15.35 F-bridge vias@(69.30,15.35)/(72.00,15.35); B keep 60→69.3
- **VDD_GPIO** intact (no rip — hopped on F)

### Blocked / deferred (one honest cycle each)
- **SWDCLK:** B west column after VDD_GPIO H@19.13 rip is geometrically clear, but V@x48.05 restore hits J8.3 GND @(48.05,4.73). No live copper left.
- **nRESET:** H corridors congested (VIN_FILT / VDD2 / P0.15 / VIN_F / ENABLE vias). Left untouched.
- **P0.02 / COEX0:** not attempted — STOP after two Class-F restore failures.

### Preserved
- Stage A VDD2 via-bridge + VDD_nRF via north
- pass30i ENABLE/COEX2 + P0.08 trunk H@y30.25 + pass30j J12.9 stitch
- P0.15 west wrap (21 segs)
- RF keepout / U3/GNSS bias

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30k-20260923-112757`  
**DRC:** `reports/DRC_PASS30K_BEFORE.json`, `reports/DRC_PASS30K_MID_VINF.json`, `reports/DRC_PASS30K_AFTER.json`  
**Summary:** `reports/PASS30K_SUMMARY.json`

---

## Pass30l — SWDCLK F/mixed detour around J8.3 (2026-09-23 11:40 IST)

**Goal:** Class F order SWDCLK → nRESET → P0.02; if Class F stalls, option C cheap signal islands. Keep Stage A + pass30i–30k. F.Cu/mixed detour around J8.3 GND without moving J8. Co-restore VDD_GPIO if ripped. shorting=0 clearance=0. No Gerbers.

**Result: KEEP — unconnected 75→74; SWDCLK U1.33↔J8.4 closed.**

### Geometry kept (SWDCLK)
- F stub `(37.75,26.75)→(37.75,24.8)` + via
- B west column `@x=34.2`: `(37.75,24.8)→(34.2,24.8)→(34.2,19.8)`
- F-hop over intact VDD_GPIO H@y19.13: vias@(34.2,19.8)/(34.2,18.4)
- B `(34.2,18.4)→(34.2,1.5)` + via
- F north band around J8.3: `(34.2,1.5)→(53.65,1.5)→(53.65,4.73)` into existing SWDCLK via
- **No VDD_GPIO rip. No J8 move.**

### Blocked / deferred
- **nRESET:** one probe B@y12.6 with F-hops @ENABLE/VIN_F → shorting=1 clearance=1 crossing=3 — **reverted atomically**
- **P0.02:** not attempted (nRESET not closed; avoid thrash)
- **Option C:** candidates MAGPIO1/MIPI_VIO/AUX_FIT/P0.16/… scanned; AUX_FIT @x19.52 hits RF (GPS/ANT_FIT/GNSS_VBIAS); COEX0 touches U3 — skipped

### Preserved
- Stage A VDD2 via-bridge + VDD_nRF via north @(69.3,31.5)
- pass30i–30k ENABLE/COEX2/P0.08/VIN_F/P0.15 restores
- P0.15 west wrap (21 segs)
- RF keepout / U3

### Signal deltas
| Net | Δ unconnected |
| --- | --- |
| SWDCLK | −1 |
| nRESET | 0 |
| P0.02 | 0 |
| others watched | 0 |

### J8 proposal (NOT applied — needs new OK)
None required this cycle (SWDCLK closed without placement). If future B@x48.05 restore still desired: J8 `(50.0,6.0)→(50.0,3.5)` Δ=2.5 mm north — opens pad clearance vs VDD_GPIO V@x48.05 (only if a later pass re-needs that column).

**Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30l-20260923-114002`  
**DRC:** `reports/DRC_PASS30L_BEFORE.json`, `reports/DRC_PASS30L_MID.json`, `reports/DRC_PASS30L_MID_NRESET.json`, `reports/DRC_PASS30L_AFTER.json`  
**Summary:** `reports/PASS30L_SUMMARY.json`



---

## Pass30m — deeper nRESET co-route (2026-09-23 11:44 IST)

### Goal
Atomic nRESET B@y12.6 co-route with preflight-recorded rip list. Restore ripped nets in same transaction. shorting=0 clearance=0. No Gerbers.

### Preflight rip list (recorded before copper edit)
- `P015_EAST_B_V_72`: P0.15 B.Cu (72.0,15.35)→(72.0,7.2) w=0.18 — B vertical crosses corridor @y=12.6
- ENABLE / VIN_FILT H / VDD2: **not ripped** (no overlap at y=12.6)
- VIN_F / P0.08 / SWDCLK: **not ripped** (hard ban)

### Attempt
- Rip P0.15 east stub → nRESET B@y12.6 with F-hop (69.0–71.5) → restore P0.15 F-bridge vias@(72,13.8)/(72,11.4)

### Result
- **nRESET closed:** no
- **Reverted:** yes (full transaction from `pre-nreset-tx.kicad_pcb`)
- **Before unconnected:** 74
- **Mid unconnected:** 73 (shorting=0 clearance=1 crossing=2)
- **After unconnected:** 74
- **P0.15 west segs:** preserved (21)
- **P0.02:** not attempted

### Colliding copper (mid DRC — reason for revert)
- tracks_crossing: nRESET B@y12.6 × COEX2 B
- tracks_crossing: nRESET B@y12.6 × P0.01 B
- clearance: nRESET B vs VDD_nRF via@(57.95, 12.0) (actual 0.11 < 0.15 POWER)

### Artifacts
- Backup: `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30m-20260923-114330`
- DRC: `reports/DRC_PASS30M_BEFORE.json`, `reports/DRC_PASS30M_MID.json`, `reports/DRC_PASS30M_AFTER.json`
- Summary: `reports/PASS30M_SUMMARY.json`


---

## Pass30n — nRESET co-route + COEX2/P0.01 rip-restore (2026-09-23 11:52 IST)

### Goal
Atomic nRESET with ≥0.15 mm clearance to VDD_nRF via@(57.95,12) d=0.8. Rip P0.15 east + COEX2 + P0.01 crossed segs; co-restore before DRC. shorting=0 clearance=0 crossing=0. No Gerbers.

### Preflight rip list (recorded before copper edit)
- `P015_EAST_B_V_72`: P0.15 B.Cu (72.0,15.35)→(72.0,7.2) w=0.18 — B vertical crosses nRESET corridor @y=12.6; local east stub rip allowed (as pass30m)
- `COEX2_B_H_246`: COEX2 B.Cu (72.0,24.6)→(105.1,24.6) w=0.18 — B H crossed by nRESET east attach V@x=101.68 y=12.6→26.0 (pass30m mid crossing)
- `P001_B_H_152`: P0.01 B.Cu (86.14,15.2)→(105.55,15.2) w=0.18 — B H crossed by nRESET east attach V@x=101.68 y=12.6→26.0 (pass30m mid crossing)

### Attempt
- Clearance: F@y=10.8 from x=53.65→59.4 under JP1/VDD_nRF (no via near JP1 pads; expect clr ~0.71 mm to via d=0.8)
- F-hop 69.0–71.5 over VDD_GPIO/VIN_F (no rip)
- Co-restore: COEX2 F-hop @y22.5 south of SW2; P0.01 F-hop @y15.2; P0.15 east F-bridge

### Result
- **nRESET closed/KEPT:** yes
- **Reverted:** no
- **Before unconnected:** 74
- **Mid/After unconnected:** 73 (shorting=0 clearance=0 crossing=0)
- **P0.15 west segs:** {'before': 21, 'after': 21, 'preserved': True}
- **P0.02:** Skipped — no free corridor identified without additional rips this cycle (only after nRESET KEPT; defer)
- **Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30n-20260923-115144`
- **DRC:** `reports/DRC_PASS30N_BEFORE.json`, `reports/DRC_PASS30N_MID.json`, `reports/DRC_PASS30N_AFTER.json`
- **Summary:** `reports/PASS30N_SUMMARY.json`

### Signal deltas
| Net | Δ unconnected |
| --- | --- |
| nRESET | -1 |
| P0.02 | 0 |
| COEX2 | 0 |
| P0.01 | 0 |
| P0.15 | 0 |


---

## Pass30o — P0.02 close (2026-09-23 12:03 IST)

### Goal
P0.02 first with atomic rip/restore of non-banned blockers; then cheap true signal islands/header stubs. shorting=0 clearance=0 crossing=0. No Gerbers. Protect Stage A + pass30i–30n kept copper + P0.15 west wrap + RF/U3.

### Preflight rip list
- `VDD_GPIO_B_V_4805`: VDD_GPIO B.Cu (48.05,3.46)→(48.05,14.80) — crosses P0.02 H@y4.5; U-jog west restore
- `P001_B_H_152`: P0.01 B.Cu (86.14,15.2)→(100.3,15.2) — crossed by P0.02 east col @x89
- `P015_EAST_B_H_72`: P0.15 B.Cu (72.0,7.2)→(106.0,7.2) — east H only (not west wrap)

### Geometry kept (P0.02)
- West: from existing B@y45.8 via col **x=27.5** with F-hops over P0.06@44.5 / P0.13@43–41
- Corridor: B **H@y=4.5** with F-hops over SWDCLK@x34.2 + VDD_GPIO U@x45; **north jog** around SWDCLK via@(53.65,4.73)
- East: col **x=89** F-hop over nRESET@y12.6 → attach (89,19.13)→(92.14,19.13) into existing via
- Restores: VDD_GPIO U-jog west; P0.01/P0.15 F-hops 88.2–89.8

### Result
- **Closed/KEPT:** P0.02
- **Reverted:** no
- **Before unconnected:** 73
- **After unconnected:** 72 (shorting=0 clearance=0 crossing=0)
- **P0.15 west segs:** before=21 after=21 preserved=True
- **Stage A:** {'VDD_nRF_via_north': True, 'VDD2_vias': 2, 'VDD2_present': True}
- **Cheap islands:** scanned ['MAGPIO0', 'MAGPIO1', 'MAGPIO2', 'MIPI_SCLK', 'MIPI_SDATA', 'MIPI_VIO', 'P0.00', 'P0.01', 'P0.03', 'P0.14', 'P0.16', 'P0.20'] — none committed (no pre-cleared stub this cycle)
- **Backup:** `.mcp-backups/nRF9161-DEV-BOARD.kicad_pcb.pre-pass30o-20260923-120037`
- **DRC:** `reports/DRC_PASS30O_BEFORE.json`, `reports/DRC_PASS30O_MID.json`, `reports/DRC_PASS30O_AFTER.json`
- **Summary:** `reports/PASS30O_SUMMARY.json`

### Signal deltas
| Net | Δ unconnected |
| --- | --- |
| P0.02 | -1 |
| VDD_GPIO | 0 |
| P0.01 | 0 |
| P0.15 | 0 |
| nRESET | 0 |
