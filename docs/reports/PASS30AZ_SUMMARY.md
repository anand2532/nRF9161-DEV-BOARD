# PASS30AZ_SUMMARY — P0.17

**Timestamp:** 2026-09-30 13:09 IST
**KiCad:** 9.0.2
**Decision:** **NO-ROUTE**
**Net:** P0.17
**Git HEAD:** `8942891b2a70c7fe722dc95417f2936f390dfc6d`
**PCB blob:** `e1adfbd7a38989b42abaef3557368955484cd560`
**Routed:** no
**Copper changed:** no
**New via:** no
**New segments:** 0
**Stopping rule:** length (pad-edge 61.510 mm > 36 mm). South U1 pad: no. East fence J10/J11: no.

## Preconditions

Live `kicad-cli` DRC: unconnected **58** (required 58), P0.17 opens **1** (required 1). short/clearance/crossing/hole 0/0/0/0. hole_to_hole 1. GND islands 12. Counts matched, so the gap was measured. No copper was added.

## Endpoints

1. **J17.1** net P0.17, center (108.000, 26.000), rectangle 1.7×1.7 mm PTH. Copper on F.Cu, In1.Cu, In2.Cu, B.Cu. This pad is its own island.
2. **In2.Cu track** net P0.17, (45.550, 21.500)–(45.550, 27.400), width 0.18 mm. DRC anchors the open on this track (length 5.900 mm). It is the pass30ay skirt, not a pad. Pads on the same island:

   - J18.5 center (48.160, 62.000), copper on F.Cu, In1.Cu, In2.Cu, B.Cu
   - J13.2 center (66.540, 76.000), copper on F.Cu, In1.Cu, In2.Cu, B.Cu
   - U1.28 center (40.250, 26.750), copper on F.Cu

Neither endpoint is a south U1 pad (U1 south means center y ≥ 37.0; U1.88 and U1.89 are the south pins). U1.28 is on the skirt island at y=26.750, north of that line, and it is not the open end. Neither endpoint is J10 or J11.

## Pad-edge

Pad-edge length of a 0.18 mm join: **61.510 mm** (exact 61.510000 mm) on In2.Cu. `GetClearance` between J17.1 and the In2 track (45.550, 21.500)–(45.550, 27.400). The west face of J17.1 (y 25.150–26.850) is equally far from the east edge of that track, so every nearest pair has this length. Over the 36 mm cap.

## Straight chord (not used)

0.18 mm In2.Cu chord (45.640, 26.000) → (107.150, 26.000), length 61.510 mm. Nearest copper: east edge of the In2 track at y=26.000, and the west edge of J17.1. Crosses the SiP fab body (x 28.0–44.0, y 26.75–37.25): **False**. The chord is east of x=44 and north of y=26.75.

Foreign items closer than 0.15 mm (5):

- VDD_nRF -0.988 mm (In2.Cu zone fill VDD_nRF (local clearance 0.5 mm); worst at x=92.070, centerline signed depth -0.898 mm)
- VDD_GPIO -0.490 mm (via@87.810,26.000 r=0.400 on In2.Cu)
- P0.08 -0.390 mm (via@79.675,26.000 r=0.300 on In2.Cu)
- ENABLE -0.190 mm (via@90.375,26.200 r=0.300 on In2.Cu)
- VDD1 -0.090 mm (via@49.200,25.600 r=0.400 on In2.Cu)

POWER/VIN items closer than 0.20 mm (3):

- VDD_nRF -0.988 mm (In2.Cu zone fill VDD_nRF (local clearance 0.5 mm); worst at x=92.070, centerline signed depth -0.898 mm)
- VDD_GPIO -0.490 mm (via@87.810,26.000 r=0.400 on In2.Cu)
- VDD1 -0.090 mm (via@49.200,25.600 r=0.400 on In2.Cu)

POWER/VIN nets checked: VDD1, VDD2, VDD2_MID, VDD_GPIO, VDD_nRF, VIN, VIN_F, VIN_FILT, VIN_IN. Negative clearance is overlap. The VDD_nRF entry is the In2 pour the chord runs through, not a track. The chord was not used. No route was attempted.

## Why no route

Rule that stopped the pass: **length**. Pad-edge 61.510 mm is over 36 mm. South-pad and east-fence rules were checked and do not apply. No copper added. The pass30ay In2 skirt was not ripped. P0.19 and P0.20 were not started. No other net was touched. No backup (no edit). No Gerbers. No git commit.

## DRC (unchanged board)

| | unconnected | P0.17 | short | clearance | crossing | hole | hole_to_hole | GND islands |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| measured | 58 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |

No before/after pair: copper was not edited.

