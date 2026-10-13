# ORDER NOTES: nRF9161 v2 UART modem module @ c37dc20 (prototype, Layout v2e)

**Order the PANEL:** `nRF9161-v2-panel-c37dc20.zip`, 2×2, 118.10×93.10 mm, mouse-bite tabs, 6 mm frame, 3 fiducials per side, 4 × 2 mm tooling holes. PCB data gate: **GREEN apart from the JLC quote**. Do not order until the quote questions in `docs/FAB_READY_CHECKLIST_V2.md` are answered.

**Drill scheme (CONFIRMED by Hardware PM): fill every 0.20 mm and every 0.25 mm hole.**

## A. PCB fabrication
1. 4-layer, 1.6 mm FR4, **ENIG**. Stackup per `docs/FAB_STACKUP_NOTES.md` and the `.gbrjob`: F.Cu 35 µm / 0.12 mm / In1 35 µm / 1.2 mm / In2 35 µm / 0.12 mm / B.Cu 35 µm.
2. **Via filling: epoxy filled and copper capped (POFV / IPC-4761 Type VII). Filled vias: 22 per board, 88 per panel (2×2).**
   - **0.20 mm ×13 per board (52 per panel):**
     - 7 in U1 GND pads 21, 27, 36, 52, 56, 60 and 98
     - 1 in the C38.2 GND pad at (33.25, 19.58)
     - 1 VDD_GPIO via next to C12.1 at (45.6, 31.4), not in the pad
     - 4 GND vias, not in pads, at (21.5, 18.95), (21.5, 20.05), (22.78, 22.4) and (18.78, 19.45)
   - **0.25 mm ×9 per board (36 per panel):** all in U1 pad 103.
   - These are the only 0.20/0.25 tools in the PTH drill file. **No other via is filled**; all 0.30 mm vias are tented.
   - POFV is charged on 4-layer boards (https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv). JLC doesn't publish the price, so the cost is unverified until quoted.
3. Caps planarized **flush or slightly recessed, never proud**: recess ≤50 µm OK, protrusion ≤+25 µm. JLC's published limit is ±50 µm: https://jlcpcb.com/help/article/pcb-via-covering. This applies to both sides; solder mask stays over the caps (tented).
4. Hole plating: JLC standard for the prototype.
5. Panel: mouse-bite tabs (0.6 mm holes). Deliver as a panel with rails.

## B. Assembly (Standard PCBA, double-sided)
1. **Standard PCBA**. Economic is single-sided only: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
2. **Parts per board:** 51 top, 16 bottom (67 assembled).
   - Bottom: 8 × 0402 C, 2 × 0402 R, Q1 SOT-23, U2 SOT-23-5, U7/U8 SOT-23-6, U5/U6 VSSOP-8.
3. **Stencils: Top + Bottom on separate stencils** (a JLC option: https://jlcpcb.com/capabilities/pcb-stencil-manufacturing). Top **0.10 mm** (U1 LGA, U4 USON 0.4 mm pitch, 0201s). Bottom **0.10 mm**. Both are standard thicknesses at no extra cost (same page).
4. **U1 (nRF9161 LGA) paste at 70–85% of pad area** per Nordic nWP054: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/footprint.html. The paste Gerber is 1:1 with copper; please apply the reduction.
5. **Reflow order: bottom side first, top side (U1) last.** The bottom is lighter: 16 parts and 30.1 mm² of pads against 51 parts and 167.1 mm² on top. JLC assembles the side with fewer parts first: https://jlcpcb.com/blog/files-needed-for-pcb-assembly
6. **First-article X-ray of U1** on all pads, including the 16 U1 via-in-pad locations (GND pads 21, 27, 36, 52, 56, 60, 98 and pad 103). Report voiding >25% or any open joint.
7. **JP2 (SIM_VCC, bottom): bridge with solder by hand after reflow.** It has no paste openings (checked on B.Paste). Without the bridge the SIM is unpowered.
   - **Caution:** the tented bottom cap of the C38.2 GND filled via sits 0.25 mm from JP2.2. Use a small bridge confined to the JP2 gap.
8. J20 (1×10 THT header, top): wave/selective solder with the bottom SMT parts protected by a fixture: https://jlcpcb.com/help/article/pcb-assembly-fixtures
