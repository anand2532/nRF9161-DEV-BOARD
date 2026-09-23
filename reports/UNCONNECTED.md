# Unconnected items (DRC truth)

Count at start of this plan: **120** (`UNCONNECTED_BEFORE_FINAL.csv`; plan text said 104).

Count now: **99** (`UNCONNECTED_AFTER_FINAL.csv`).

`kicad-cli pcb drc` JSON `unconnected_items` is authoritative. Shorts/clearance/hole_clearance: **0**.

This board is **not fabrication-ready** until unconnected is 0. See `FINAL_FAB_RELEASE.md`.
