# PASS30CM step 3: C5 exception text → pads 52–60
- **`.kicad_dru`:** already reads "via barrels in U1 pads 52-60 only (signal 53-55, 57-59; GND 52/56/60)" (since e711e6b). No change was needed.
- **`reports/DFM_VIPPO_NOTE.md` (fab note):**
  - Added the C5 exception line (pads 52–60, barrels only, no F.Cu/In1 tracks in x<29 / y 26–40).
  - Refreshed the stale group A table to the DK land pattern: 0.30×0.30 pads, x 28.25.
  - Marked group B 0.25/0.40 as done (74a6605).
- No copper change, so the gate is identical to FX2: all zero, 17 unconnected.
