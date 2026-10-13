# ORDER NOTES: nRF9161 v2 UART modem module @ 6645a01 (prototype)

**Order the PANEL:** `nRF9161-v2-panel-6645a01.zip`, 2×2, 118.10×93.10 mm, mouse-bite tabs, 6 mm frame, 3 fiducials per side, 4 × 2 mm tooling holes. Status: **gate RED. Do not order** until the red items in `docs/FAB_READY_CHECKLIST_V2.md` are fixed and the JLC quote questions are answered.

## A. PCB fabrication
1. 4-layer, 1.6 mm FR4, **ENIG**. Stackup per `docs/FAB_STACKUP_NOTES.md` and the `.gbrjob`: F.Cu 35 µm / 0.12 mm / In1 35 µm / 1.2 mm / In2 35 µm / 0.12 mm / B.Cu 35 µm.
2. **Via-in-pad, epoxy filled and copper capped (POFV / IPC-4761 Type VII), exactly 16 vias per board (64 per panel):** every **0.20 mm** hole (×7 per board) and every **0.25 mm** hole (×9 per board). These are the only 0.20/0.25 tools in the PTH drill file, and they are marked on the `VIPPO` layer Gerber. **No other via is filled**; all other vias are tented. On 4-layer boards POFV is charged: https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv
3. Caps planarized **flush or slightly recessed, never proud**: recess ≤50 µm OK, protrusion ≤+25 µm. JLC's published limit is ±50 µm: https://jlcpcb.com/help/article/pcb-via-covering
4. Hole plating: JLC standard for the prototype.
5. Panel: mouse-bite tabs (0.6 mm holes), deliver as a panel with rails.

## B. Assembly (Standard PCBA, double-sided)
1. **Standard PCBA**. Economic is single-sided only: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
2. **Stencils: Top + Bottom on separate stencils**, a JLC option: https://jlcpcb.com/capabilities/pcb-stencil-manufacturing
   - Top **0.10 mm**, which is the U1 decision.
   - Bottom **0.10 mm** (0201/0402/SOT/VSSOP/USON only). 0.10 mm is a standard thickness at no extra cost (same page).
3. **U1 (nRF9161 LGA) paste at 70–85% of pad area** per Nordic nWP054: https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/footprint.html. The paste Gerber is 1:1 with copper; please apply the reduction.
4. **Reflow order: bottom side first, top side (U1) last**, so U1 is reflowed once and never hangs upside-down. The bottom has 23 parts and the top 44; JLC assembles the side with fewer parts first: https://jlcpcb.com/blog/files-needed-for-pcb-assembly
5. **First-article X-ray of U1** on all pads, including the 16 via-in-pad locations (GND pads 21, 27, 36, 52, 56, 60, 98, and pad 103). Report voiding >25% or any open joint.
6. **JP2 (SIM_VCC, bottom): bridge with solder by hand after reflow.** It has no paste openings (B.Paste checked), so the stencil can't bridge it. Without the bridge the SIM is unpowered. JP1 no longer exists in v2.
7. J20 (1×10 THT header, top): wave/selective solder with the bottom SMT parts protected (fixture): https://jlcpcb.com/help/article/pcb-assembly-fixtures
