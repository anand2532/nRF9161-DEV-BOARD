# Hardware PM status — nRF9161-DEV-BOARD

- **Working copy (shared computer):** `/workspace/kicad-projects/nRF9161-DEV-BOARD`
- **Git remote:** `https://github.com/anand2532/nRF9161-DEV-BOARD.git` (clone of user `git@github.com:anand2532/nRF9161-DEV-BOARD.git`)
- **User machine path (local exec still offline):** `/home/anand/kicad-projects/nRF9161-DEV-BOARD`
- **Goal:** fabrication-ready board that will work (schematic + PCB + RF/power + DFM gate)

## Snapshot (2026-09-23)

- Mature multi-sheet design (12 sheets), README is Nordic-doc driven
- Existing ERC: 2 errors, 14 warnings (power pin conflicts / dangling globals)
- Existing DRC JSON: 59 violations (clearance 29, silk issues, starved thermal, etc.)
- `fab/` and `reports/` already present — DFM must re-validate before green

## Specialist owners

| Role | Doc to maintain |
| --- | --- |
| Schematic Engineer | `docs/SCHEMATIC_REVIEW.md` |
| PCB Layout Engineer | `docs/PCB_LAYOUT_REVIEW.md` |
| RF Power Engineer | `docs/RF_POWER_REVIEW.md` |
| DFM Fab Engineer | `docs/FAB_READY_CHECKLIST.md` |

Do not declare fab-ready until DFM checklist is green and critical ERC/DRC/RF items are closed.
