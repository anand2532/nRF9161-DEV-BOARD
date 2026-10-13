# ORDER NOTES — nRF9161-DEV-BOARD @ b9d4e62 (prototype)

Package: `nRF9161-DEV-BOARD-fab-b9d4e62.zip` (this folder). Status: PCB data GREEN. **Do not place the order until the JLC quote (C7) confirms the via-in-pad items below.**

## A. PCB fabrication notes
1. 4-layer, 1.6 mm, FR4, **ENIG**. Stackup per `docs/FAB_STACKUP_NOTES.md` (matches `nRF9161-DEV-BOARD-job.gbrjob`): F.Cu 35 µm / prepreg 0.12 mm (εr ~4.2) / In1.Cu 35 µm / core 1.2 mm / In2.Cu 35 µm / prepreg 0.12 mm / B.Cu 35 µm. 50 Ω single-ended microstrip on L1 over the L2 GND reference (impedance coupon / width tuning per stackup note).
2. **Via-in-pad, IPC-4761 Type VII**: epoxy filled (non-conductive), planarized, copper capped, then ENIG. Applies to **exactly 29 vias**: every hole of the **0.20 mm drill (×20)** and the **0.25 mm drill (×9)**. They are the only 0.20/0.25 mm tools in `drill/nRF9161-DEV-BOARD-PTH.drl` and are marked on the `VIPPO` user layer (`gerbers/nRF9161-DEV-BOARD-VIPPO.gbr`). **No other via is filled**; all other vias are tented.
3. Caps planarized **flush or slightly recessed, never proud**: recess (dimple) ≤50 µm OK, protrusion ≤+25 µm.
4. Hole plating: JLC standard is acceptable for this prototype.

## B. Assembly notes
1. Stencil **0.10 mm**.
2. U1 (nRF9161 LGA) paste apertures at **70–85% of pad area** per Nordic nRF9161 Hardware Design Guidelines (nWP054), https://docs.nordicsemi.com/r/bundle/nwp_054/page/wp/nwp_054/footprint.html (see also nWP056). The paste layer in the Gerbers is 1:1 with copper; please apply the reduction.
3. **First-article X-ray of U1**, covering pads 52–60 and all filled-via pads (the 29 via-in-pad locations). Report any voiding >25% or any open joint.
4. **JP1 (I_MEAS) and JP2 (SIM_VCC): bridge each with solder.** These are 2-pad solder jumpers (1.0×1.5 mm half-round pads, about 0.3 mm gap) with **no paste openings**, so the stencil will not bridge them. They need a **manual solder bridge** (iron/rework) after reflow. JP2 must be closed or the SIM card is unpowered. JP1 can be opened again at bring-up to measure current across R2.
