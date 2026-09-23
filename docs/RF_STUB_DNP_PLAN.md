# Class C — RF stub-terminate / DNP shunt fix plan

| Field | Value |
| --- | --- |
| **Date** | 2026-09-23 (Asia/Calcutta) |
| **Author** | RF Power Engineer |
| **Board** | nRF9161-DEV-BOARD (working copy `/workspace/kicad-projects/nRF9161-DEV-BOARD`) |
| **Status** | **APPROVED by Hardware PM (2026-09-23)** — Layout executes as **pass30z** (after pass30y Package B finishes; not interleaved). No Gerbers until unconnected→0. RF re-reviews after copper. |
| **Related** | `docs/RF_POWER_REVIEW.md` §Class C; `docs/SCHEMATIC_REVIEW.md` §C; `docs/FAB_STACKUP_NOTES.md`; `docs/PCB_LAYOUT_REVIEW.md` §3.4; `reports/REMAINING_OPENS_MATRIX.md`; `reports/DRC_PASS30W_AFTER.json` |

---

## 1. Purpose / fab gate

DFM Class **C** opens on **`ANT_FIT` / `AUX` / `AUX_FIT`** are **MUST-FIX**. The west RF keepout (pass30: **x ≈ 0–24.2 mm, y ≈ 20–64 mm**) does **not** waive them.

Policy (locked):

- **Stub-terminate** DNP 50 Ω shunt pads on the RF nets (same-net stub **≤ 2 mm** from RF pad to shunt pad1).
- Leave parts **unpopulated** (`DNP` + exclude-from-BOM).
- **Do not** rip 50 Ω trunks (L1/L2 series path, J2/J3/J5/J6, TP1 feeds) to “clear” DRC.
- Solid **layer L2** (In1 GND) under ANT/AUX/GNSS remains **LOCKED**.

Hardware PM approved this plan (2026-09-23). Sequencing: Layout finishes **pass30y Package B** (J13/J10/J11) first; RF-only copper is **pass30z** (or next idle after 30y), not interleaved with B. Layout then relocates/nudges C22/C23/C24 per §4–§7; RF re-reviews **after** that copper. Still no Gerbers until unconnected→0.

---

## 2. Exact nets / pads table

**Topology (verified schematic `03_LTE_RF` + PCB nets):**

```
U1 ANT ── ANT ── L1 ── ANT_FIT ── J2 (U.FL) / J3 (SWF)
              │              │
             C21            C22     (DNP π shunts → GND)

U1 AUX ── AUX ── L2 ── AUX_FIT ── TP1
              │             │
             C23           C24     (DNP π shunts → GND)
```

**Naming:** refdes **L2** = AUX **series matching inductor** (`Device:L`, `0R / DNP match`). PCB **layer L2** = solid GND plane under RF — different thing; do not confuse.

| Net | Shunt refdes | Footprint pads (PCB) | RF trunk they stub from | Current status (pass30w DRC) |
| --- | --- | --- | --- | --- |
| `ANT` | **C21** | pad1=`ANT`, pad2=`GND`; FP `C_0402_1005Metric` @ ≈(20.0, 28.0) mm | `ANT` copper toward **L1.1** / U1 ANT | Local ~1.5 mm stub near C21; **not** in Class C MUST-FIX trio (sibling π shunt). Confirm join in KiCad if ratsnest remains. |
| `ANT_FIT` | **C22** | pad1=`ANT_FIT`, pad2=`GND`; @ ≈(20.0, 36.0) mm | `ANT_FIT` trunk: **L1.2** → J2.1 / J3.1 (F.Cu 0.20 mm) | **MUST-FIX.** Unconnected: track island ~1.5 mm @ C22 ↔ main ~10.3 mm feed. Gap ≈ **4.5 mm** (layout review) — exceeds ≤2 mm unless footprint nudged toward L1.2. |
| `AUX` | **C23** | pad1=`AUX`, pad2=`GND`; @ ≈(20.0, 48.0) mm | `AUX` trunk: U1 AUX → **L2.1** @ y≈33 mm | **MUST-FIX.** Unconnected: AUX track ~7.8 mm ↔ ~2.0 mm island at C23. C23 sits ~15–17 mm south of main AUX run — relocate or confirm ≤2 mm attach in KiCad. |
| `AUX_FIT` | **C24** | pad1=`AUX_FIT`, pad2=`GND`; @ ≈(20.0, 56.0) mm | `AUX_FIT` trunk: **L2.2** ↔ **TP1.1** @ y≈33 mm | **MUST-FIX.** Unconnected: **C24.1 ↔ L2.2**. Dangling 1.5 mm stub at C24; main trunk at y≈33 — gap ≈ **23 mm**. Footprint must move next to L2.2/TP1; do **not** drag a long RF stub. |
| `GNSS_ANT` / `GPS` | **C31**, **C32** | C31 pad1=`GPS`→GND @≈(18,56); C32 pad1=`GNSS_ANT`→GND @≈(12,40) | GNSS bias-T spine C27/L4/J5/J6 | Same DNP stub policy; **not** in DFM ANT_FIT/AUX/AUX_FIT trio. Do not disturb C27/L4/U3. Confirm pad joins in KiCad. |

**Connectors / series (do not rip):**

| Ref | Role | Nets |
| --- | --- | --- |
| L1 | LTE series 0R / match | pad1=`ANT`, pad2=`ANT_FIT` |
| L2 | AUX series 0R / match | pad1=`AUX`, pad2=`AUX_FIT` |
| J2 / J3 | U.FL / SWF | `ANT_FIT` |
| TP1 | AUX test pad | `AUX_FIT` |

Evidence: PCB pad nets from live `nRF9161-DEV-BOARD.kicad_pcb`; opens from `reports/DRC_PASS30W_AFTER.json` + `reports/REMAINING_OPENS_MATRIX.md` (matrix “accept” is **superseded** by DFM MUST-FIX for these three nets).

---

## 3. Recommended DNP shunt

| Item | Choice |
| --- | --- |
| **Footprint** | Keep project standard **`Capacitor_SMD:C_0402_1005Metric`** (already on C21–C24, C31–C32). |
| **Value placeholder** | Schematic **Value = `DNP`**. BOM placeholder MPN family already used: **Murata GJM1555C1H100JB01** (High-Q 0402) — treat as **DNP / do not place**; post-VNA populate 0.5–2 pF-class (or tune value) per Nordic π practice. |
| **BOM attributes** | **DNP** + **exclude from BOM** (`in_bom no`) + **do not place**. |
| **KiCad flags** | `(dnp yes)`, `(in_bom no)` — **already set** on C21–C24 and C31–C32 (verified `schematic/03_LTE_RF.kicad_sch`, `04_GNSS.kicad_sch`; see `docs/SCHEMATIC_REVIEW.md` §C). |

---

## 4. Placement region

| Rule | Detail |
| --- | --- |
| **Keepout** | Prefer shunt body **outside** west RF box if a ≤2 mm stub can still reach the 50 Ω pad. If not, **pad-only / footprint inside matching area** is allowed for stub length. |
| **Max stub** | **≤ 2 mm** same-net F.Cu from RF trunk/pad to shunt **pad1**. Width = `RF_50OHM` (0.20 mm nominal). |
| **Orientation** | Pad1 toward RF trunk; pad2 to solid GND with short via or pour (Nordic DK style). Axis along/orthogonal to microstrip per local courtyard — confirm in KiCad. |
| **Antenna voids** | Do not place shunt body over U.FL/SWF keepout voids (live tiny rule-areas ≈ (7.05–8.95, 31.485–33.575) and (7.05–8.95, 51.485–53.575) mm). |
| **AUX_FIT / C24** | **Relocate C24** next to **L2.2 / TP1** (`AUX_FIT` @ y≈33, x≈12–20) so stub ≤2 mm. Current @ y≈56 is not stub-legal. |
| **AUX / C23** | Nudge **C23** toward main `AUX` run at **L2.1** (~20.5, 33) if island gap remains >2 mm. |
| **ANT_FIT / C22** | Nudge **C22** toward **L1.2** (~21.5, 32) or join existing 1.5 mm stub to trunk within ≤2 mm total. |

---

## 5. Schematic / BOM

**Schematic Engineer changes required: none** (verified 2026-09-23).

| Refs | Sheet | Flags |
| --- | --- | --- |
| C21–C24 | `schematic/03_LTE_RF.kicad_sch` | `(dnp yes)`, `(in_bom no)`, Value=`DNP` |
| C31–C32 | `schematic/04_GNSS.kicad_sch` | `(dnp yes)`, `(in_bom no)`, Value=`DNP` |

No missing shunt symbols for `ANT_FIT` / `AUX` / `AUX_FIT`. BOM.csv already lists C21–C24 / C31–C32 as DNP High-Q 0402.

Optional cleanup (not blocking Class C copper): root-sheet text still mentions “C18–C21” in places — cosmetic only (`RF_POWER_REVIEW` P2 note).

---

## 6. Layout must NOT touch

- Solid **layer L2** GND under ANT / AUX / GNSS matching and feeds (no splits, no DIG pours).
- Existing matching **series** parts and π **trunks**: L1, L2 (inductor), J2, J3, J5, J6, TP1, C27, L4 bias-T spine.
- Stackup **H / Z0** lock (`docs/FAB_STACKUP_NOTES.md`: L1–L2 H ≈ 0.10–0.15 mm, ~0.12 preferred; Z0 = 50 Ω SE; ENIG).
- GNSS bias switch **U3** / `GNSS_VBIAS` / FB5 / COEX0 gating.
- Do **not** rip 50 Ω trunks to fix unconnected; do **not** delete DNP footprints; do **not** stuff shunt MPNs for this fab spin.

---

## 7. Layout MAY do (when PM unlocks tiny RF-only edit)

1. **Relocate** C24 (required) and nudge C22/C23 as needed so each RF-side pad is within **≤ 2 mm** of its trunk.
2. Add **same-net stub** ≤2 mm, 0.20 mm F.Cu, from RF pad/trunk → shunt **pad1**.
3. Tie shunt **pad2** to solid GND (short via to layer L2 or local GND pour) — DK style.
4. Recommended attach points:
   - **`ANT_FIT` / C22:** pad1 ← stub from copper near **L1.2** (or existing C22 island joined into L1.2→J2/J3 feed).
   - **`AUX` / C23:** pad1 ← stub from copper near **L2.1** / U1-AUX run.
   - **`AUX_FIT` / C24:** pad1 ← stub from copper at **L2.2** or **TP1.1** (after moving C24 there).
5. Leave parts unpopulated. No MAGPIO/MIPI/COEX digital under matching on F.Cu; do not split In1 GND under 50 Ω.

---

## 8. Acceptance

| Check | Pass criteria |
| --- | --- |
| Class C nets | Live DRC **clear** of `ANT_FIT` / `AUX` / `AUX_FIT` `unconnected_items` (and related C22/C23/C24 pad opens). |
| Process | Re-run DRC after the tiny RF-only edit; attach before/after JSON under `reports/`. |
| Fab gate | Still **no fab** until P0 power / SIM / reset (and other Class A) nets closed — board target **unconnected → 0**. Class C alone does not unlock Gerbers. |
| RF sign-off | RF Power Engineer re-reviews **after** copper lands; this plan is not a post-copper waiver. |

---

## 9. Decision needed from Hardware PM

1. **Approve** this stub-terminate / DNP shunt plan (MUST-FIX; keepout does not waive).
2. **Assign** Layout a **tiny RF-only** edit (C24 relocate + C22/C23 nudge + ≤2 mm stubs + GND vias). Schematic: **no further change** for Class C flags.
3. After copper: assign **RF** to re-review; then continue P0 opens toward unconnected = 0 before any Gerber release.

**RF recommendation:** Approve. Preferred fix is footprint relocation + short stubs — not trunk rips, not “accept/waive,” not populating shunts pre-VNA.
