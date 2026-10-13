# PASS30CB_SUMMARY - PCB update from remapped schematic (J9.2/J9.3 NC, J9.4 P0.04, J16 DNF)

**Git tip:** 57c4af7 (not committed). **PCB blob before:** e8a108d7d4fe1a374a10789f45217ab39eecb735. **After:** 0e1d4fa0bdb7451c1ad46c4632b1cb834de71c3e. Backup .mcp-backups/pass30cb/pre-edit.kicad_pcb. No routing.
Tooling note: KiCad was missing from the box again. It was reinstalled (Debian kicad 9.0.2) via user-approved apt-get.

## ERC (reports/ERC_PASS30CB.json / .rpt)
0 errors, 201 warnings (107 lib_symbol_issues, 94 footprint_link_issues; all library-link warnings, no electrical errors). Netlist: reports/PASS30CB_netlist.net (103 components).

## Update method
pcbnew Python API (scripts/final_pass30cb.py): set each footprint's value and each pad's net from the netlist. Pins listed as `unconnected-*` become no-net. Zones refilled. No footprint added, removed, moved or swapped.
- Position/rotation/side snapshot before vs after: **0 moved**.
- Tracks+vias: 1423 -> 1423 (none deleted).
- Copper on nets that no longer exist: **none.** J9.2/J9.3 and J16.1-4 had no copper attached. Zones are unaffected.

## Changes
**Values (6):** U2 TLV73330PDBV -> **TLV73333PDBV** (confirmed); D3 Green -> POWER; D4 Green -> STATUS; D5 Green -> LTE; D6 Green -> GNSS; D7 Green -> SPARE_DNP. The LED values came from the uncommitted schematic. PM should confirm they are intended (they look like labels, not part values).
**Pad nets (9):**
- J9.2 P0.07 -> NC; J9.3 P0.05 -> NC
- J16.1 P0.10 -> NC; J16.2 P0.11 -> NC; J16.3 P0.12 -> NC; J16.4 P0.09 -> NC
- **J13.17 VDD_nRF -> VDD_GPIO** (not in the stated remap. It comes from the schematic; please confirm)
- U3.4 / U3.5 unconnected-* placeholder -> no-net (cosmetic)
J9.4 was already P0.04 on the PCB, so there was no change.
**Footprint lib IDs:** FB5 and U3 differ only by library nickname (PCB lacks the prefix). Left unchanged.

## DRC (before = DRC_PASS30BY_AFTER, after = DRC_PASS30CB_AFTER.json)
| | unconnected | non-GND | GND items | short | clearance | crossing | hole | hole_to_hole |
|---|---|---|---|---|---|---|---|---|
| before | 43 | 31 | 12 | 0 | 0 | 0 | 0 | 1 |
| after | 38 | 26 | 12 | 0 | 0 | 0 | 0 | 1 |
-6 for the J9.2, J9.3 and J16.1-4 opens, and +1 for a new VDD_GPIO open at J13.17 (from the J13.17 net change).

### Non-GND opens after (26)
| net | items |
|---|---|
| MAGPIO1 | Track on F.Cu, length 2.4000 mm (28.0,28.0) ↔ PTH pad 2 of J14 (104.0,49.27) |
| MIPI_VIO | Pad 57 of U1 on F.Cu (28.0,29.5) ↔ PTH pad 4 of J14 (104.0,51.81) |
| P0.10 | Pad 18 of U1 on F.Cu (44.0,28.5) ↔ PTH pad 11 of J12 (31.4,76.0) |
| P0.31 | Pad 89 of U1 on F.Cu (36.75,37.25) ↔ Track on F.Cu, length 28.4036 mm (102.6,75.5) |
| P0.26 | Track on F.Cu, length 3.8500 mm (33.75,37.25) ↔ PTH pad 11 of J13 (89.4,76.0) |
| MIPI_SCLK | PTH pad 5 of J14 (104.0,53.08) ↔ Pad 58 of U1 on F.Cu (28.0,30.0) |
| VDD_GPIO | PTH pad 17 of J13 (104.64,76.0) ↔ Track on F.Cu, length 8.9200 mm (107.18,67.08) |
| P0.27 | Pad 84 of U1 on F.Cu (34.25,37.25) ↔ PTH pad 12 of J13 (91.94,76.0) |
| P0.03 | Track on F.Cu, length 37.1500 mm (41.75,74.4) ↔ Track on F.Cu, length 0.6500 mm (97.49,19.125833) |
| P0.01 | Track on B.Cu, length 4.0000 mm (62.0,78.5) ↔ Pad 96 of U1 on F.Cu (40.25,37.25) |
| P0.30 | Track on F.Cu, length 28.3000 mm (101.2,74.7) ↔ Track on F.Cu, length 3.8500 mm (36.25,37.25) |
| MAGPIO2 | Track on F.Cu, length 1.2500 mm (28.0,27.5) ↔ PTH pad 3 of J14 (104.0,50.54) |
| P0.18 | Pad 29 of U1 on F.Cu (39.75,26.75) ↔ Track on B.Cu, length 10.8000 mm (50.7,72.8) |
| P0.25 | Pad 42 of U1 on F.Cu (33.25,26.75) ↔ PTH pad 10 of J13 (86.86,76.0) |
| SIM_1V8 | Track on F.Cu, length 2.7000 mm (75.6,44.1) ↔ Pad 49 of U1 on F.Cu (29.75,26.75) |
| SIM_IO | Pad 48 of U1 on F.Cu (30.25,26.75) ↔ Track on F.Cu, length 4.6000 mm (75.68,52.0) |
| MAGPIO0 | Pad 55 of U1 on F.Cu (28.0,28.5) ↔ PTH pad 1 of J14 (104.0,48.0) |
| COEX1 | Pad 92 of U1 on F.Cu (38.25,37.25) ↔ PTH pad 2 of J15 (104.0,63.27) |
| P0.24 | Pad 40 of U1 on F.Cu (34.25,26.75) ↔ Track on In1.Cu, length 2.9416 mm (84.32,76.0) |
| P0.29 | Pad 87 of U1 on F.Cu (35.75,37.25) ↔ PTH pad 14 of J13 (97.02,76.0) |
| P0.12 | Pad 20 of U1 on F.Cu (44.0,27.5) ↔ PTH pad 13 of J12 (36.48,76.0) |
| P0.28 | Track on F.Cu, length 3.8500 mm (35.25,37.25) ↔ PTH pad 13 of J13 (94.48,76.0) |
| P0.21 | Track on In1.Cu, length 51.9016 mm (77.4,69.9) ↔ Track on F.Cu, length 3.6500 mm (35.75,26.75) |
| MIPI_SDATA | Pad 59 of U1 on F.Cu (28.0,30.5) ↔ PTH pad 6 of J14 (104.0,54.35) |
| P0.14 | Pad 24 of U1 on F.Cu (42.25,26.75) ↔ Track on B.Cu, length 15.4000 mm (40.54,77.4) |
| P0.23 | Track on F.Cu, length 3.6500 mm (34.75,26.75) ↔ Track on In2.Cu, length 30.1510 mm (81.78,76.0) |

New keepout recorded for future passes: VDD_nRF In2 x 53-60, y 12-22.
