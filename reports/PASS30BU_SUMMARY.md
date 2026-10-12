# PASS30BU_SUMMARY - P0.23 J13.8 to J10.3 (class D, cap waived)

**Decision:** KEEP. Tip f642613 (not committed). Blob f005a44ac5f9f9816e7b6140d71b9121a23df93b -> 841574e17ab38ff0508510a63863da9ad5e86a4d. Backup .mcp-backups/pass30bu/pre-edit.kicad_pcb.

- **Pair (live):** J13.8 PTH (81.78, 76.00), all layers, a single-pad island. J10.3 PTH (116.00, 33.08), all layers, also single-pad. Pad-edge 53.192 mm.
- **No vias.** The run goes PTH to PTH on In2.
- **Route, In2, 0.18 mm, 4 segments:** (81.78,76.0)->(103.1,54.68)->(103.1,45.3)->(115.2,33.2)->(116.0,33.08).
- **Closest foreign:** P0.06 via (113.2,36.0) 0.226; J14.1/2/3 pads (MAGPIO0/1/2) 0.31; MIPI_SDATA pad J14.6 0.369; GND via (110,40) 0.741. **Closest POWER:** none within 1 mm.
- **Locked runs (incl. P0.22 In2):** min plan distance 5.2 mm (P0.22 In2 y=32.5). Longest stretch within 0.50 mm in plan: **0.00 mm**. Crossings 0. Stacking none. The route stays clear of the pocket (x=103.1 > 97.3).

| | unconnected | P0.23 | short | clearance | crossing | hole | h2h | GND |
|---|---|---|---|---|---|---|---|---|
| before | 48 | 2 | 0 | 0 | 0 | 0 | 1 | 12 |
| after | 47 | 1 | 0 | 0 | 0 | 0 | 1 | 12 |
No other non-GND net gained an open. The remaining P0.23 open is U1.39 to J13.8 (class A #2 in PASS30BS). J9, J16 and the do-not-retry items are untouched.
