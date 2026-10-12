# PASS30CO: north corridor opened; P0.14 and P0.18 routed; P0.25 and SIM_IO rerouted (base 990d175)

## Why this is one commit
The B.Cu corridor north of the U1 pad row was closed by **both** P0.25 (33.25, 27.0) → (42.65, 25.95) **and** the SIM_IO diagonal (33.1, 26.5) → (44.45, 24.85). Two attempts failed:
- Ripping P0.25 alone: only one of P0.14/P0.18 fit through the single exit.
- SIM_IO forced south (no north B.Cu) with P0.25 still in place: no route.

So P0.25 and SIM_IO (step 5/6 copper) were ripped together and the four nets were routed in one pass, in this order: P0.14, P0.18, SIM_IO, P0.25. Splitting this into separate commits would leave an intermediate state that fails the gate.

## What changed
- **In-pad vias:** legal 0.30/0.20 vias at the new pad centres, **P0.14 U1.24 (42.25, 27.0)** and **P0.18 U1.29 (39.75, 27.0)**. P0.25 and SIM_IO keep their in-pad vias (pads 42 and 48). P0.19 and P0.20 were not touched.
- **Clearance nudges:** 8 vertices of P0.18/P0.25 were moved by 0.04 mm to clear POWER (0.15 mm) on VDD2, VDD1 and VIN_FILT.
- **GND repair:**
  - Fill-blocking rule areas on B.Cu over 2 new floating GND slivers under U1 (`pass30co_island_noFill0/1`). These are unconnectable because no via is allowed under the body.
  - 2 GND stitch vias 0.5/0.3 for the C10/C7 GND pad pours, at (52.7, 38.9) and (60.65, 36.5). Each spot was checked against DRC and In1/In2 continuity.
  - Other 0.6/0.3 stitch spots were found by search, but none were added because of a script bug.

## Lengths and vias (track copper; via count includes the in-pad via)
| Net | Before (990d175) | After |
|---|---|---|
| P0.14 | open (20.3 mm header stub, 0 vias) | **closed**, 82.4 mm, 8 vias |
| P0.18 | open (96.0 mm header side, 0 vias) | **closed**, 159.0 mm total net, 6 vias |
| P0.25 | 84.3 mm, 9 vias | 93.8 mm, 9 vias. **Not shorter, and no fewer vias;** the target was not met. The new path frees the corridor. |
| SIM_IO | 142.7 mm, 6 vias | 134.4 mm, 6 vias. Shorter by 8.3 mm; **via count not reduced** |

## SIM spacing and parallel runs (SIM_IO vs others; SIM_IO track copper, same layer)
- **New SIM_IO copper outside the fan-out zone:** 0 points under 0.5 mm.
- **Below 0.5 mm:** only pre-existing copper at the U4 pins (SIM_CLK 0.22 mm, SIM_RST 0.37 mm, at the U4 0.65 mm pitch). Inside the zone, SIM_1V8 is at 0.28 mm (≥0.15 allowed).
- **Parallel run (≤10 mm rule):**

| vs | Min edge gap | Edge ≤0.75 mm: total / longest | Edge ≤1.5 mm: total / longest |
|---|---|---|---|
| SIM_CLK | 0.22 (U4 pins, old) | 3.71 / 1.95 mm | 5.77 / 2.50 mm |
| SIM_RST | 0.37 (U4 pins, old) | 2.25 / 1.50 mm | 5.96 / 3.35 mm |
| SIM_1V8 | 0.28 (fan-out zone) | 12.29 / **8.85** mm | 15.92 / **8.85** mm |

- **Result:** the longest continuous parallel run is **8.85 mm** (SIM_1V8, x 30.55 vs 31.05 under U1). That is **≤10 mm: PASS**.

## Gate (refilled)
- short, clearance, crossing, hole, hole_to_hole, copper_edge, silk, courtyard, mask_bridge and via_dangling are all 0. track_dangling is 4 (pre-existing).
- **Unconnected 12 → 10.** No signal opens remain; the 10 are GND F.Cu islands, the same as before.
- No power open.
- VDD_nRF: 1 piece, 6737.0 → 6723.6 mm².
- In1 GND: 2 pieces, 8185.2 → 8179.3 mm².
- No closed net reopened. RF copper untouched.
- No pin remap is needed.
