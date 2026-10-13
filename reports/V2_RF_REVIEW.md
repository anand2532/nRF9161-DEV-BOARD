# V2 RF / Power review: G8 sign-off
Reviewer: RF Power Engineer · 2026-10-13 · branch `v2` HEAD 6645a01 · read-only (no PCB/SCH edits, no commits)
Inputs: reports/V2_LAYOUT.md, reports/V2_SIMPLIFY_PLAN.md, nRF9161-DEV-BOARD/reports/V2_RF_RULES.md. The worktree has no copy of the rules file.
Method: pcbnew 9.0.2 Python geometry on the .kicad_pcb. kicad-cli DRC with schematic parity ran on a /tmp copy of the full tree.

## Verdict: **FAB-OK WITH NOTES**
No RF or power blocker. One pre-fab fix is recommended (F1, the SIM ESD return). F2–F4 are cheap improvements or next-spin items.

## 1. GNSS fence via ("0.1 mm edge-to-edge"): PASS, the claim is not reproduced
- Line: GPS and GNSS_ANT run on F.Cu at 0.20 mm wide, over solid In1 GND at H = 0.12 mm (εr 4.2, 35 µm copper). The RF_50OHM clearance is 0.15 mm, so there is an F.Cu GND pour 0.15 mm from each edge, which makes the line a grounded coplanar waveguide.
  - Microstrip on its own (IPC-2141): 47.9 Ω.
  - CPWG with 0.15 mm gap (conformal, t=0): about 54 Ω. Real copper thickness pulls this down a few Ω.
  - Net result is about 50 Ω ±10%. The field is dominated by H (gap/H = 1.25), so the side gap matters only a little.
- Closest GND fence via, edge to edge (via edge to track or pad edge):
  - GPS track: **0.519 mm**, via 0.6 mm at (26.50, 34.00). That is 4.3 H.
  - GNSS_ANT track: 0.60 mm at (20.79, 37.5) and (22.29, 37.5).
  - Pads: J5.1 at 0.333 mm, L4.2 at 0.38 mm, C31.1 at 0.439 mm.
  - No GNSS copper is anywhere near 0.1 mm. That figure is probably via edge to pour edge, not to the feed.
- Rule check: ≥2H (0.24 mm) and ≥0.25–0.3 mm are both met with margin. My V2 rule of ≥0.5 mm from the trace edge is also met (0.519). A via at ≥4H changes Z0 by well under 1 Ω, so there is **no detuning and no move needed**.
- Fab: the via-to-track clearance is at least 0.333 mm, well above the JLC minimum of about 0.1–0.127 mm. The only GND via closer to RF copper is U1 pad-60 VIPPO (0.3 mm via) at (28.25, 31.0), 0.25 mm from the ANT track. This is the already-approved C5 exception.
- Fence vias within 1.5 mm of the feed, with the largest nearest-neighbour gap:
  - GNSS: 9 vias, 2.15 mm
  - ANT: 8 vias, 2.36 mm
  - AUX: 3 vias, 2.0 mm
  - All are ≤3 mm, so PASS.

## 2. Bulk C4/C8 at 3.58 mm: PASS
- C4 is 4.7 µF on **VDD1** (U1 pin 102) and C8 is 4.7 µF on **VDD2** (pin 22). These are the VDD_nRF branches after FB1/FB3. The 47 µF bulk C3/C7 sits at 5.33 mm.
- HF caps are at the pins:
  - VDD1: C6 15 pF at 2.01 mm and C5 100 nF at 2.40 mm.
  - VDD2: C10 15 pF at 2.01 mm and C9 100 nF at 2.40 mm.
  - DEC0: C13 at 1.91 mm.
  - VDD_GPIO: C12 at 1.95 mm.
- Connection: VDD1/VDD2 are 0.25 mm F.Cu (15.3 / 12.5 mm total). About 3.6 mm of 0.25 mm trace is roughly 3 nH, which is fine for a 4.7 µF bulk because the HF caps carry the edge current.
- Note F2: widen VDD1/VDD2 to ≥0.5 mm where there is room. At 0.25 mm the full 15 mm is about 30 mΩ, or about 15 mV at a 0.5 A TX peak. That is acceptable but thin for the PA rail.

## 3. VDD_GPIO at 0.3 mm × 141 mm: PASS
- Routing: 141.4 mm total (F.Cu 81.2 + B.Cu 60.2), 16 vias of 0.3/0.6, no In1 copper.
- Resistance: 1 oz (35 µm per the stackup) gives R = 1.72e-8 × 0.1414 / (0.3e-3 × 35e-6) = **0.23 Ω**. With the vias (about 16 × 0.5 mΩ) and a warm board, call it ≤0.26 Ω.
- Load: nRF GPIO bank, 4 LXC translators, LED, pull-ups, ≤20 mA expected. That gives an IR drop of ≤5 mV, and still only 26 mV at a pessimistic 100 mA. That is 0.8% of 3.3 V, so acceptable.
- Clearance from RF:
  - The closest approach to any RF feed track is **4.94 mm**.
  - The westernmost point is F.Cu x 27.3–27.95 at y 41.0–41.4, near U3 (GNSS bias switch). That is south of B5 (y ≤ 39.5) and outside the RF feeds.
  - There is no B.Cu VDD_GPIO in B1–B5 (rule areas are DRC-clean).
  - On In1, 0 tracks.
- Next spin (F4): re-place the south translator strip so a direct 0.4 mm route of about 91 mm fits. It is optional.

## 4. U4 SIM ESD on bottom under J7: PLACEMENT PASS, RETURN PATH WEAK (F1)
- Placement:
  - U4 is at (21.5, 19.5) on B.Cu. J7 is top, SIM (not RF), bbox x 16.05–31.25, y 11.95–24.0.
  - The nearest RF zone (B4_J2 / B5) starts at y 25.98, and U4 is 10.0 mm from the nearest RF pad. It is outside B1–B6, so OK.
- Return path:
  - The U4 EP (pad 9, GND) reaches In1 through **one** via at (21.5, 18.0), 1.5 mm away, over a 0.2 mm track. That is about 1.5 nH plus via.
  - C33.2 at (21.98, 21.6) has no GND via within 1.5 mm (nearest 3.43 mm, reached through a chain of 0.15 mm tracks to the EP).
  - C37.2 has none within 1.5 mm (1.58 mm).
  - C35/C36/C38 each have a via at 0.7 mm.
  - For an IEC 61000-4-2 return, the TPD3F303 needs a short, multi-via EP-to-plane path.
  - It works electrically (unconnected 0), but it is weak, so **F1** below.

## 5. Small ground with external antennas: PASS, with antenna-type note
- The board GND is 50 × 37.5 mm, which is about 0.11 λ at 700 MHz. With the antenna external on U.FL (J2 LTE, J5 GNSS), the board is **not the radiator**. Efficiency is set by the external antenna and its own ground.
- Antenna types:
  - **Ground-independent** types (half-wave dipole, sleeve dipole, or a "ground-plane independent" flex/PCB antenna on a cable) are unaffected by the board size.
  - **Monopole/whip "stick" antennas** need a ground plane of about λ/4 (≈100 mm at 700–800 MHz). On this board they would use the module plus coax shield as the counterpoise. That brings detuning, efficiency loss in the low bands (several dB is typical at B12/B13/B20/B28) and cable-dependent behaviour.
- **Recommend** for LTE: a ground-independent sleeve dipole or flex dipole (LTE-M/NB-IoT 698–2200 MHz). For GNSS: an active patch with its own ground plate (the bias-T path is in place). Document this in the module integration notes.
- Ground continuity:
  - In1 GND is **one piece, 1705.5 mm²** (no split).
  - In2 VDD_nRF is one piece, 1575 mm².
  - F.Cu and B.Cu GND have 16 and 15 pour fragments respectively (main pours 1153 and 1268 mm²). They are retained only when via-tied (orphans removed), so the reference is not split.

## 6. Rules re-check (V2_RF_RULES.md vs applied plan and layout)
| Rule | Result |
|---|---|
| §1 top-only: U1, L1, L2, C21–C24, C27–C32, L4, FB5, U3, J2, J5, DEC/HF caps, bulk C3/C4/C7/C8 | PASS, all F.Cu |
| §2 B1–B5 bottom keep-clear | PASS. 0 bottom parts or tracks in B1 (U1), B2 (ANT/AUX/GPS), B3, B4 (J2/J5) or B5. The nearest bottom part to an RF pad is C33 at 7.92 mm (≥5 / ≥3 mm rules met). Bottom parts: U2 (59.5, 40.8), U4, U5–U8, C33–C38, C41–C48, Q1, R21, R23, JP2, TPs. No violations |
| B6 on-board antenna | n/a (external antennas only) |
| In1 solid GND, no signals | PASS. 0 In1 tracks, rule area `In1_GND_only_no_tracks` board-wide, 1 island |
| 50 Ω width 0.20 mm | PASS. All RF nets 0.20 mm F.Cu, 0 RF vias |
| Feed ≤10 mm | PASS. Copper: ANT 5.15 + ANT_FIT 2.91, GNSS 5.15 + 4.24, AUX 2.57 + 2.81. Pad-to-connector per Layout: ANT 9.03, GNSS 9.03, AUX 6.35 |
| Fence pitch ≤3 mm, ≥0.5 mm from edge | PASS. Max gap 2.36 mm. Min edge clearance 0.519 mm (excluding the approved U1 pad-60 VIPPO) |
| VDD_nRF ≥1 mm or pour, ≥4 vias | PASS. In2 pour of 1575 mm² plus 14 VDD_nRF vias. The F.Cu stubs are 0.3 mm (10.5 mm) |
| DRC / unconnected | PASS. kicad-cli 9.0.2: 0 errors, **0 unconnected**, 82 `lib_footprint_issues` (environment only). Parity: 1 cosmetic `net_conflict` on J7 C6, a no-connect net name with "/" vs "{slash}" |

Rules made obsolete or changed by the simplify plan (the rules file itself is not edited):
- R1. **J3/J6 SWF are absent** in the layout, though the plan listed them as "KEEP (Optional)". Drop them from the §1 top-only list and from B4. Production RF test is then via the U.FL only. Confirm with Anand (plan Q4).
- R2. **TP1 (AUX_FIT)** is still placed, though the plan marks it "REMOVE pending Q5". It is harmless (top, inside the RF area). Keep it until Q5 is answered.
- R3. **B6** is not applicable (no on-board antenna). §4's ground-length guidance is replaced by the §5 antenna-type recommendation above.
- R4. The §3 example list said "SIM holder on bottom". The holder is now on **top** (J7), with its ESD block on the bottom. That is allowed, outside B1–B5.
- R5. The fence rule stays at "≥0.5 mm from trace edge". The tighter 2H minimum (0.24 mm) is adequate, but 0.5 mm stays the target.

## Fix list
1. **F1 (recommended before fab), U4 ESD return.**
   - Add ≥2 GND vias (0.3/0.6 tented) within 0.5 mm of the U4 EP (21.5, 19.5) on B.Cu, for example 1 east and 1 west of the pad column in the free space toward (21.5, 20.9) and (22.6, 18.6).
   - Alternatively, use a 0.2/0.3 VIPPO in the EP.
   - Add 1 GND via ≤0.7 mm from C33.2 (21.98, 21.6) and 1 from C37.2 (18.58, 19.9).
   - Widen the EP-to-via link to ≥0.3 mm.
   - Layout to place and DRC. Exact spots depend on the ESD pad strip.
2. **F2 (recommended), VDD1/VDD2 width.** Widen FB1→C3/C4→U1.102 (VDD1) and FB3→C7/C8→U1.22 (VDD2) from 0.25 mm to ≥0.5 mm where clearance allows.
3. **F3 (doc), integration note.** Specify a ground-independent LTE antenna (sleeve or flex dipole, 698–2200 MHz) and an active GNSS patch with its own ground. Avoid monopole stick antennas.
4. **F4 (next spin).** VDD_GPIO direct 0.4 mm route of about 91 mm after the south translator strip is re-placed.
5. **N1 (info).** The "0.1 mm GNSS fence via" figure in V2_LAYOUT / the PM brief is not reproduced. The measured minimum is 0.519 mm to the trace and 0.333 mm to the J5.1 pad. No action.

---
## Re-check @ 365b7f6 (v2d: U4 + C33–C38 to top, SWDIO/P0.22 reroute): **PASS (FAB-OK WITH NOTES)**
Read-only. Analysis ran on a /tmp copy using pcbnew 9.0.2 and kicad-cli DRC with parity.

- **Moved parts:** all are now F.Cu. U4 is at (32.4, 23.9) and C33–C38 sit at x 32.3–35.3, y 17.3–25.5.
  - Min pad to RF copper (feeds and RF pads): **7.30 mm** (C36); U4 is 7.42 mm.
  - Min to the top RF keepout (x<29, y 26–40): **2.64 mm** (U4).
  - Min to the U1 body bbox: C36 0.11 mm, U4 1.03 mm. DRC shows no courtyard overlap, and U1's non-RF north side is OK.
  - B1–B5 are bottom-only zones, so they don't apply to these top parts. Bottom parts in B1–B5: 0 (rule areas DRC-clean).
- **Rerouted tracks:**
  - Min to RF copper: SWDIO 9.77 mm, P0.22 8.07 mm. The SIM nets bottom out at 4.48 mm (SIM_1V8).
  - 0 points in the top RF keepout.
  - The B.Cu segments (SIM_IO, SIM_CLK, SIM_1V8 jumpers) stay outside B1, closest **0.18 mm**, which DRC accepts.
- **In1:** 0 tracks, 1 GND island of 1707.1 mm².
- **Fence vias are unchanged:**
  - ANT: 8 vias, max gap 2.36 mm.
  - AUX: 3 vias, max gap 2.0 mm.
  - GNSS: 9 vias, max gap 2.15 mm.
  - The min centre distance (0.919 mm on GNSS) is unchanged, so the 0.519 mm edge figure still holds.
- **U4 ESD return (F1):** improved, but the target isn't fully met, so F1 stays open as recommended rather than blocking.
  - The EP connects over **0.3 mm** F.Cu to 2 GND vias at **1.65 mm** (30.75, 23.9) and **1.72 mm** (30.9, 23.05), and on to C40.2.
  - The U4 EP and the C33/C35/C36/C37 GND pads all touch the F.Cu GND pour.
  - Nearest via per ESD cap GND pad: C38 0.16 mm, C36 1.85 mm, C33 2.54 mm, C37 2.58 mm, C35 3.34 mm.
  - The ≤0.5 mm EP-via target is not met.
  - Remaining fix: add 1–2 GND vias ≤0.7 mm from the U4 EP (32.4, 23.9) and from C35.2 (34.45, 23.98) and C37.2 (35.25, 24.62), DRC permitting.
- **G7 recomputed:**
  - kicad-cli 9.0.2: **0 errors, 0 unconnected**.
  - 82 `lib_footprint_issues` warnings (environment only).
  - Parity: 1 cosmetic `net_conflict` on J7 C6 (no-connect net name with "/" vs "{slash}").
- G1–G6 and G8 hold. F2–F4 from above are unchanged.

---
## Re-check @ c37dc20 (v2e: F1 vias, SIM_IO jog, filled vias C38.2 and near C12): **PASS, F1 CLOSED**
- **U4 ground return:** the U4 ground pad (32.4, 23.9) now has 3 GND vias at 1.10 mm (new, 31.3/23.9), 1.65 mm and 1.72 mm (centre-to-pad-centre), all on 0.3 mm F.Cu and tied to the top GND pour. The new via is about 0.45 mm edge to edge from the pad.
  - C35.2 has a via at 0.78 mm (centre, (34.45, 23.2)) and C37.2 one at 0.68 mm ((35.85, 24.95)). C38.2 has a 0.2/0.3 filled via in the pad.
  - C33.2 is at 1.64 mm and C36.2 at 1.85 mm. Both are on the pour, which is acceptable.
  - **F1 closed.**
- **SIM_IO on the bottom:** the closest point to B1 is 0.30 mm edge to edge, on the via-stub segment (31.3, 25.1→24.75). The jog at y 24.15 is 1.25 mm from B1. It stays outside B1, and SIM_IO is ≥4.68 mm from RF copper.
- **New vias:**
  - Distance to RF copper is ≥7.72 mm; none is in B1.
  - Distance to U1 pads: (35.85, 24.95) is 1.60 mm and (45.6, 31.4) VDD_GPIO is 1.55 mm. Both are outside B1 (0.23 and 0.18 mm from its edge).
  - The nearest U1 VIPPO via is ≥2.09 mm away, and no via sits in a DEC pad.
- **In1:** 0 tracks, 1 piece, 1707.5 mm².
- **Fence vias:** unchanged (max gap ANT 2.36, AUX 2.0, GNSS 2.15 mm).
- **DRC (kicad-cli 9.0.2):** 0 errors, 0 unconnected. 82 `lib_footprint_issues` warnings (environment only) and 1 cosmetic parity `net_conflict` on J7 C6.
- G1–G8 PASS. FAB-OK WITH NOTES; F2–F4 unchanged.
