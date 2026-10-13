# PASS30BQ_SUMMARY - P0.12 (covers pass30bp + pass30bq)

## pass30bp: REVERTED (NO-ROUTE)
Two runs nearly stacked on locked runs on the adjacent layer: In2 x=25.4 vs P0.00 In1 x=25.2, and In2 y=17.7 vs SIM_RST In1 y=17.6. The RF-keepout-hugging run was also unwanted. Restored to blob 5a46a4b. DRC: unconnected 49, GND 12, short/clearance/crossing/hole 0, h2h 1.

## pass30bq: NO-ROUTE (no copper)
Tip 45743c9. Blob 5a46a4bef4da85ae0841a8b51077fd8339bb3fda unchanged. Not committed.
- Source: the existing via (47.0, 27.5) on the U1.20 island. Target: J12.13 PTH (36.48, 76.0), pad y 75.15–76.85.
- **Blocking geometry (plan view):** north of the pad are P0.05 In1 y=74.70 (x 22.51–57.05) and P0.11 In2 y=74.80 (x 35.10–45.25, then down to J12.12). South of it is P0.09 In1 y=77.20 (x 30.10–55.30). With the 0.50 mm plan rule, the only band left is y 75.30–76.70, and that band lies inside the J12 pad row. J12.12 (P0.11) and J12.14 (P0.13) close it on the sides. No segment can reach J12.13 at ≥0.50 mm from every locked run.
- Confirmed by grid A* (0.05 mm) on In1, In2 and B.Cu with the 0.50 plan buffer, x≥26, foreign 0.15 / POWER 0.20 and same-layer locked 0.33: unreachable on all three. A min plan distance can't be reported because no candidate route existed.
- DRC (unchanged): unconnected 49, P0.12 opens 2, GND 12, short/clearance/crossing/hole 0, h2h 1.

**Do-not-retry:** J9.2, J9.3, SIM_1V8, P0.09 J16.4, P0.11 J16.2, **P0.12** (both opens).
