# Fabrication Stackup Notes — Anand / Hardware PM

## Status

**LOCKED — RF Power Engineer sign-off (2026-09-23).**

**FAB_READY gate: RED (unchanged).**

This note is the project-authoritative stackup **intent** for fab quotes and impedance coupons. Exact mid-layer glass styles and pressed thicknesses remain fab-house proposals (see Remaining fab-house items).

## History — prior conflict (resolved)

- `README.md` §§ PCB stackup / Impedance assumptions described an **assumed 4-layer, 1.6 mm** JLCPCB-like stackup with `prepreg | ~0.12 mm, εr ≈ 4.2` between L1/F.Cu and L2/In1.Cu, and used `H ≈ 0.12 mm` for the 0.20 mm `RF_50OHM` 50 Ω microstrip (confirm with fab coupon).
- `fab/gerbers/nRF9161-DEV-BOARD-job.gbrjob` reported `LayerNumber: 4`, `BoardThickness: 1.6`, `Finish: None`, and `MaterialStackup` dielectrics of **0.48 mm FR4** between each copper pair (F.Cu/In1.Cu, In1.Cu/In2.Cu, In2.Cu/B.Cu) — a symmetric generic export, not a thin outer RF prepreg.
- Conflict: README RF intent (~0.12 mm L1↔L2) vs job.gbrjob (~0.48 mm equal dielectrics) + Finish=None. This note previously asked Anand to choose; he delegated the decision to the design agent on 2026-09-23.

## Evidence (do not invent layer count)

| Source | Fact |
| --- | --- |
| `nRF9161-DEV-BOARD.kicad_pcb` `(layers)` | **4 copper**: F.Cu, In1.Cu, In2.Cu, B.Cu; board `thickness 1.6` |
| `fab/gerbers/nRF9161-DEV-BOARD-job.gbrjob` | `LayerNumber: 4`, `BoardThickness: 1.6`, `Finish: None` (stale export 2026-09-16 IST) |
| `README.md` stackup / RF | L1 signals+RF, L2 GND, L3 VDD_nRF, L4 GPIO/returns; 50 Ω microstrip L1 over L2; net class `RF_50OHM` width 0.20 mm |
| `nRF9161-DEV-BOARD.kicad_pro` | `RF_50OHM` patterns: `ANT*`, `AUX*`, `GPS`, `GNSS_ANT` |
| PCB board setup | No detailed KiCad `stackup` dielectric block locked in the `.kicad_pcb` (job 0.48 mm values are export defaults) |

## Decisions (fab-ready intent)

### 1. Layer count and order (as the board already is)

**4-layer**, overall target **1.6 mm** (README + PCB + gbrjob agree on count and overall thickness target):

| Layer | Name | Role (project intent) |
| --- | --- | --- |
| L1 | F.Cu | Components, RF microstrip, short digital |
| — | dielectric | **RF prepreg — see §2** |
| L2 | In1.Cu | **GND** reference for microstrip (solid under ANT/GPS) |
| — | dielectric | Mid stack — **fab to propose** (§ Remaining) |
| L3 | In2.Cu | **VDD_nRF** pour (+ remaining power/signals as designed) |
| — | dielectric | Outer bottom prepreg — **fab to propose** (§ Remaining); prefer symmetry with L1–L2 RF H when possible |
| L4 | B.Cu | GPIO / returns |

Do **not** change copper layer count; the PCB is already 4-layer.

### 2. Authoritative dielectric map (L1↔L2)

**Authoritative for RF geometry:** thin outer prepreg **H ≈ 0.10–0.15 mm** (README target **~0.12 mm**, εr ≈ 4.2 class FR4) between **L1 (F.Cu) and L2 (In1.Cu / GND)**.

**Rationale:** This is an LTE/GNSS RF board. README and `RF_50OHM` (0.20 mm) are sized for microstrip over a thin L1–L2 dielectric. The gbrjob **0.48 mm** equal dielectrics are treated as **generic KiCad/export defaults** (no locked board stackup block; symmetric filler that would invalidate the 0.20 mm / 50 Ω assumption). Layer count in the job (**4**) is correct and retained; only the dielectric thicknesses in `MaterialStackup` are non-authoritative for RF.

Mid dielectrics (L2↔L3 core/prepreg, L3↔L4): **not specified as exact mm in project docs** — fab shall propose FR4 core/prepreg construction to meet **overall ~1.6 mm** while holding **L1–L2 H in the 0.10–0.15 mm** band for controlled impedance.

### 3. Surface finish

**ENIG** (Electroless Nickel Immersion Gold).

**Rationale:** Fine-pitch nRF9161 LGA + RF/U.FL/SWF pads; project docs did not require HASL/OSP/other. gbrjob `Finish: None` is unset export, not a design requirement. Specify ENIG on the PO / fab notes when Gerbers are regenerated.

### 4. Controlled impedance

**Yes** — **50 Ω single-ended** microstrip on L1 over L2 GND.

**Net class / path class (from project, not invented):** KiCad net class `RF_50OHM` (track 0.20 mm) via patterns `ANT*`, `AUX*`, `GPS`, `GNSS_ANT` — i.e. **LTE/GNSS RF paths / antenna feed**. Nordic evaluates ANT/AUX/GPS as 50 Ω single-ended (`README.md` RF architecture).

Fab shall provide a **4-layer impedance coupon** matched to the agreed L1–L2 H/εr; recalculate or confirm 0.20 mm width against fab stackup before tape-out (README typical window 0.16–0.22 mm).

## RF Power Engineer sign-off — 2026-09-23 (LOCKED)

**AGREE:** L1–L2 H ≈ **0.10–0.15 mm** (prefer **~0.12 mm**), εr ≈ **4.2-class FR4**; **Z0 = 50 Ω single-ended** on `ANT*`/`AUX*`/`GPS`/`GNSS_ANT` per Nordic **nWP033**; **ENIG** is OK; and the 4-layer order is **L1 RF / L2 GND / L3 VDD_nRF / L4 GPIO**. Do not change the H band or 50 Ω target.

RF caveats (not blockers):

1. The impedance coupon **MUST lock width before tape-out**. If fab Dk/H is outside ~0.12 mm / εr 4.2, retune width within the README window **0.16–0.22 mm**; do not invent a new Z0.
2. L2 under the ANT/AUX/GNSS matching networks and feeds must remain **solid GND**: no splits and no DIG pours.
3. The controlled-impedance callout is **single-ended microstrip only**; there is no differential RF on this board.
4. Regenerate Gerbers only after `unconnected_items = 0`.

## Remaining fab-house items

1. Confirm **overall board thickness** (target 1.6 mm) after pressing with the chosen glass styles.
2. Propose **exact mid-layer construction** (L2–L3 and L3–L4 core/prepreg, Cu weights) that hits **L1–L2 H ≈ 0.10–0.15 mm (~0.12 mm preferred)** and **Z0 = 50 Ω** on the RF coupon.
3. Provide **εr / Dk** for the outer prepreg used under L1 and the impedance coupon stack reference.
4. Confirm **ENIG** availability and any mask-over-ENIG notes for RF pads.
5. After coupon sign-off, align KiCad board stackup / future `job.gbrjob` MaterialStackup with fab values (replace 0.48 mm defaults).

## Gerber regeneration gate

**Gerbers will not be regenerated until `unconnected_items = 0`.**  
On-disk `fab/gerbers` (including this job.gbrjob) remain stale relative to live connectivity work; do not treat current MaterialStackup thicknesses as fab PO truth.

## Quick reference (decided)

| Item | Decision |
| --- | --- |
| Copper layers | **4** (F / In1 / In2 / B) |
| L1–L2 dielectric H | **~0.10–0.15 mm** (prefer **~0.12 mm** RF prepreg) |
| Mid dielectrics | Fab propose to meet ~1.6 mm overall |
| Finish | **ENIG** |
| Impedance | **50 Ω SE** — LTE/GNSS RF / `RF_50OHM` (`ANT*`, `AUX*`, `GPS`, `GNSS_ANT`) |
