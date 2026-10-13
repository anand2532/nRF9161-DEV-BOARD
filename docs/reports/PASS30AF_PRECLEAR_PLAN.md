# PASS30AF preclear plan

**Trigger:** pass30ae Package C full revert. Board is the pass30ac tip (`d2d1c21`), unconnected 64.

**Goal:** Identify non-protected copper that blocks P0.22 / P0.04 / SE-dual corridors, then execute only the safest preclear that opens a corridor for **one** signal. Do not rip the P0.22 keep.

## Do not rip

- Stage A — VDD_nRF via @(69.3, 31.5); VDD2 vias @(58, 29.55) and @(58, 30.95)
- P0.15 west wrap (B.Cu with x < 45)
- RF keepout x 0–24.2, y 20–64; U3 / matching / L1 / L2 / In1
- Class C C22 (17.5, 31.75), C23 (24.8, 34), C24 (15, 31.8), stubs and GND vias
- pass30r **P0.22 keep** (vias @(112.5, 32.5), @(114.7, 29.9), @(112.5, 29.9), @(109.2, 32.5) and their trunks)
- pass30u closures that are still valid (including P0.19)
- Frozen footprints J13, J10, J11, J16, J9, J17, J12, U1

## What actually blocks the named corridors

| Corridor | Blocker | Rip? |
| --- | --- | --- |
| P0.22 last open (B @(64, 5.2) vs keep @(109.2, 54.8)) | distance + keep copper | **No** — keep is banned; not a local preclear |
| P0.04 / J10–J11 west sweep | P0.04 F V@x113.8 (y36.8–49.2), V@x114.8 (y52.5–78.8), H@y52.5 | **No** — P0.04 is closed (0 opens). A rip regresses it |
| SE duals J16/J9/J17 | P0.06 F@x113.2 y36–47.2 (closed), P0.01 B wall @x105.55 (1 open spine), VDD_GPIO, P0.22 vias | **No** this pass |
| SIM east approach y≈44.6, x≈80–97 | duplicate dangling `SIM_RST_C` on top of the live B trunk, pinched against `SIM_CLK_C` @y44.05 (edge gap ~0.37 mm, too tight for a 0.18 mm track) | **Yes — chosen** |

`SIM_CLK` / `SIM_IO` / `SIM_RST` / `SIM_1V8` each still have one open, but their copper is not what fills the SE column. `SIM_CD`’s extra F segment on y=52.04 is redundant and does **not** open a new centerline.

## Execute (one net)

**Net:** `SIM_RST_C` only.

1. Delete the two dangling duplicate B tracks `(79.38, 44.60)–(97.30, 44.60)`.
2. Jog the live B trunk `(81.80, 44.60)–(97.30, 44.60)` to **y=45.00**, and extend the x=81.80 riser end from 44.60 to 45.00.
3. Trim the duplicate B via-risers `(97.30, 44.60)–(97.30, 45.54)` up to y=45.00 so the old tail does not dangle into the freed line. Via @(97.30, 45.54) and the F stub stay.

**Corridor freed (not routed this pass):** B.Cu along y≈44.60, x≈81.8–97.3, between `SIM_CLK_C` @y44.05 and the jogged trunk @y45.00. Room for one 0.18 mm signal. Does not enter x>108, the P0.22 keep, RF keepout, or Class C.

**Fallback if that jog is dirty:** delete only the redundant `SIM_CD` F segment `(100.27, 52.04)–(96.55, 52.04)` (covered by the longer y=52.04 track). Stop after one clean keep or two dirty fails.

No header moves. No Gerbers. No second net.
