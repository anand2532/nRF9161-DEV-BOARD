# PASS30CP step 2: locked 4-layer stackup in the board
- **Source:** `docs/FAB_STACKUP_NOTES.md` (LOCKED 2026-09-23, RF sign-off) and the fab-pass checklist item 6. L1–L2 H ≈ 0.12 mm (εr 4.2), 1.6 mm overall, ENIG.
- **Added `(stackup)` to `(setup)`:**

| Layer | Thickness (mm) | Material |
|---|---|---|
| Mask | 0.01 | |
| F.Cu | 0.035 | |
| Prepreg | **0.12** | FR4, εr 4.2 |
| In1.Cu | 0.035 | |
| Core | 1.20 | FR4, εr 4.5 |
| In2.Cu | 0.035 | |
| Prepreg | 0.12 | FR4, εr 4.2 (symmetric) |
| B.Cu | 0.035 | |
| Mask | 0.01 | |

  Total 1.60 mm; copper finish ENIG.
- The mid core value is our placeholder for 1.6 mm total. The note says the fab proposes the mid construction, and only L1–L2 is locked.
- **Check:** `kicad-cli` job file exported to /tmp only (no fab outputs committed). MaterialStackup now reads F.Cu/In1.Cu 0.12, In1/In2 1.2, In2/B.Cu 0.12, BoardThickness 1.6, Finish ENIG. It matches.
- **Gate:** DRC unchanged (all zero; unconnected 5 = GND islands). No copper change.
