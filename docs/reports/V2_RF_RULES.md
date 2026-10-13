# V2 RF / Power Rules — double-sided UART modem module (nRF9161)
Author: RF Power Engineer · 2026-10-13 · read-only review, no PCB/SCH edits.
Input status: `reports/V2_SIMPLIFY_PLAN.md` did **not exist** when this was written. Re-check these rules against it once it lands.

Source tags: **[N]** Nordic nRF9161 HDG (nWP054) / product spec · **[V]** antenna/connector vendor typical · **[J]** engineering judgment / v1 lessons.
- HDG GND: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/gnd.html
- HDG DEC0: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/dec0.html
- HDG placement: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/component_placement.html
- PS antenna port: https://docs.nordicsemi.com/bundle/ps_nrf9161/page/regulatory_information.html

## 1. TOP side only
| Item | Rule | Src |
|---|---|---|
| U1 nRF9161 SiP | Top. Reflow first. Nordic DK pads + VIPPO carried over from v1 | N/J |
| LTE match L1, C21/C22 (π) | Top, inline on the 50 Ω feed. Keep π footprints even if DNP | N (reserve π space) |
| AUX L2, C23/C24, TP1 | Top | J |
| GNSS C27, C31/C32, bias-T L4, C28–C30, FB5, U3 TPS22919 | Top, next to the GNSS feed | J |
| RF connectors J2 U.FL, J3 SWF, J5/J6 GNSS (or chip antenna) | Top, within ≤10 mm of U1 RF pads | N (short line) / J |
| DEC caps at U1 pins (DEC0 C9 etc.) and VDD_nRF HF caps (≤1 µF) | Top, at the pin, GND straight into In1 | N ("close to pin, same GND plane") |
| VDD_nRF bulk (≥10 µF) | Top preferred. Bottom allowed only outside B1–B5, per Section 3 | J |

## 2. BOTTOM keep-clear zones (no parts; no copper except GND pour)
| Zone | Extent | Src |
|---|---|---|
| B1 under U1 | U1 courtyard + 1.0 mm on all sides. Solid B.Cu GND pour tied to the 9 filled U1 GND vias (thermal spread). No parts, no signals | N (solid GND, filled vias) / J |
| B2 under RF feeds | Each 50 Ω feed (ANT/AUX/GPS) from U1 pad to connector: ≥1.0 mm lateral from the trace edge (≥8H, H = 0.12 mm). Bottom = GND pour only | J |
| B3 under matching networks | Full footprint area of L1/L2/C21–C24/C27–C32/L4/FB5/U3 + 1.0 mm. No bottom parts, GND pour only | J |
| B4 under connectors | J2/J3/J5/J6 courtyard + 1.0 mm. No bottom parts (U.FL mating force, rework, RF). GND pour only | J |
| B5 RF corner | v1 RF keepout equivalent (west edge of U1 to board edge, spanning all feeds) + 2 mm from U1 RF corner. No bottom parts | J |
| B6 on-board antenna (if used) | Clearance area: **no copper on ANY layer, no parts either side**. Typical chip antenna: 10–15 mm × board width at the board edge (Ignion/Taoglas class). Use the chosen datasheet as the authority | V |

GND stitching along feeds: via fence both sides, pitch **≤3 mm**. Derivation: at 2.7 GHz λ0 = 111 mm; εeff ≈ 3.3 (FR4 microstrip) → λg ≈ 61 mm; λg/20 ≈ 3.1 mm. Fence via ≥0.5 mm from the trace edge [J].

## 3. Where bottom parts ARE allowed [J]
- Anywhere outside B1–B6, and ≥5 mm from the U1 RF corner (pads 61/64/67) and ≥3 mm from any RF feed.
- OK on bottom: UART level shifters/ESD, header/castellations, VDD_GPIO LDO (TLV73333), ENABLE/reset parts, SIM holder + its ESD (if kept), test pads, LEDs (keep LEDs and any buck converter away from antennas and connectors) [N: noisy parts away from antennas].
- VDD_nRF source (regulator/bulk) on bottom: short, wide path. ≥1.0 mm trace or pour, and **≥4 vias of 0.30 mm** per layer transition for 0.5 A peaks (≈1 A/via thermal, 4 for low L / IR drop) [J].

## 4. Smaller board vs antenna/GND clearance
- **External antenna via U.FL/SWF (recommended for v2):** board size does **not** affect antenna performance. Keep the 50 Ω feed short (≤10 mm) and the connector near U1 [N/J].
- **On-board chip/PCB antenna:** LTE low bands (700–960 MHz) need a long ground plane. Typically ≥80–100 mm of GND length for good LB efficiency [V]. A small module will lose LB efficiency, so it needs the vendor's evaluation/EM sim [N recommends EM simulation for small form factors]. LTE and GNSS antennas must not be adjacent [N].
- GNSS: an active antenna needs the bias-T path (L4/FB5/C28–C30, U3 COEX0 gate) carried over intact, with J5 GND stitched (≥2 vias, v1 lesson).

## 5. Stackup / impedance
- Stay **4L**: L1 sig/RF · In1 solid GND (no signals, ever) · In2 VDD_nRF · B.Cu. H = 0.12 mm → keep **0.20 mm** 50 Ω microstrip (JLC impedance calc to confirm) [J/v1].
- Different stackup: recompute. Microstrip (IPC-2141) Z0 = 87/√(εr+1.41)·ln(5.98H/(0.8W+T)).
  Example: 2L 1.6 mm (H≈1.5, εr 4.5) → W ≈ 2.9 mm. Too wide for U1 pads and needs a large taper, and there is no solid reference under U1. **Recommend 4L** [J].
- Double-sided parts do not change this: bottom-side parts reference In2/B.Cu, so the L1/In1 RF pair is unaffected [J].

## 6. Double-sided assembly
1. Bottom (light, small parts) reflowed first, then top with U1, connectors and RF parts. Or top first if all bottom parts pass the JLC second-side weight rule. U1 is never on the bottom [J].
2. No heavy or tall parts on the bottom (shields, inductors >0.1 g/mm² pad area) [J].
3. U.FL/SWF on top, nothing under them on the bottom (B4) [J].
4. RF test access: J3 SWF on top. GND and VDD_nRF test pads may go on the bottom outside B1–B5 [J].
5. VIPPO caps flush or recessed (≤25 µm proud), X-ray U1 on first articles (v1 decision) [J].

## 7. Power rules
1. DEC0 cap at pin 13, other DEC/VDD caps at their pins on top. GND straight to In1 with dedicated via(s) [N].
2. VDD_nRF: In2 plane, neck ≥2 mm (v1). Bulk within 10 mm of U1 VDD pins [J].
3. ENABLE: pull to the defined state, sequenced after VDD_GPIO per the PS [N/J].
4. VDD_GPIO 3.3 V from TLV73333. UART at VDD_GPIO level. Level shifter only if the host differs [J].
5. SIM (if kept): SIM lines ≥0.5 mm from other signals, ESD at the holder [J/v1].
6. ESD on UART/power entry at the connector. Optional RF ESD must be low-C and negligible at RF [N].

## 8. Layout checklist / RF gates
- [ ] G1 placement: Section 1 parts on top. Bottom keep-outs B1–B6 drawn as KiCad rule areas (bottom footprints + B.Cu tracks) before routing.
- [ ] G2 In1: zero non-GND copper. ≤2 pieces, nothing under the feeds.
- [ ] G3 feeds: 0.20 mm 50 Ω, ≤10 mm, fence ≤3 mm pitch, π footprints present.
- [ ] G4 U1: 9 filled GND vias, solid B.Cu GND under U1, no bottom parts in B1.
- [ ] G5 power: VDD_nRF neck ≥2 mm, ≥4 vias per transition, DEC caps at pins.
- [ ] G6 GNSS: bias-T one net, J5 GND ≥2 vias.
- [ ] G7 antenna (if on-board): clearance copper-free on all layers, vendor review done.
- [ ] G8 RF review sign-off before Gerbers.
