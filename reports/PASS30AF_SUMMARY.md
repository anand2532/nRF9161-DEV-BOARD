# PASS30AF_SUMMARY — SIM preclear

**Timestamp:** 2026-09-30 03:42 IST
**KiCad:** 9.0.2+dfsg-1
**Decision:** **KEEP**
**Net:** SIM_RST_C
**Unconnected:** 64 → 64 (delta 0)
**Short/clearance/crossing after:** 0/0/0
**Corridor:** B.Cu y≈44.60 x≈81.8–97.3 freed for one 0.18 mm signal (SIM_RST_C trunk now y=45.00; dangling duplicates removed)

## Attempts

### SIM_RST_C_dangling_rip_and_y45_jog
- net: SIM_RST_C
- edit: {'deleted_dangling': 2, 'jogged_trunk': 1, 'extended_riser': 1, 'trimmed_via_risers': 2, 'new_trunk_y': 45.0}
- mid: {'unconnected_items': 64, 'shorting_items': 0, 'clearance': 0, 'tracks_crossing': 0, 'hole_clearance': 0, 'track_dangling': 13}
- accept: True reason: ok

P0.22 keep not ripped. No header moves. No Gerbers.
