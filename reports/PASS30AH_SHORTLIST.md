# PASS30AH shortlist — five shortest real island gaps

**Timestamp:** 2026-09-30 09:28 IST
**Decision:** **NO ROUTE** (no copper edit)
**Gate:** shortest non-protected island gap must be ≤ 12 mm AND joinable by one 0.18 mm track or one via without crossing protected copper.
**Result:** 0 gaps ≤ 12 mm. Shortest real gap is **12.305 mm** on `VDD_GPIO`.

GND zone islands ignored. Protected keeps excluded from this list (P0.22, P0.19, P0.15 west wrap, Stage-A VDD2, Class C RF, sealed SIM_IO_C / SIM_CLK_C). Island counts match DRC opens (`islands = opens + 1`) on every non-GND open net.

Distance is copper-edge to copper-edge between the two islands, not pad-center to pad-center.

## 1. `VDD_GPIO` — 12.305 mm

- **Island A:** (40.279, 19.511) — via@40.17,19.126
  - layers B.Cu, F.Cu; pads pad C11.1, pad J8.1, pad TP10.1, pad U3.1, pad C12.1; anchor (47.057, 15.286); 30 primitives
- **Island B:** (43.622, 31.353) — pad U1.12
  - layers F.Cu; pads pad U1.12; anchor (44.000, 31.500); 1 primitives
- **Distance:** 12.305 mm
- **Same-layer gap:** 12.305 mm on F.Cu
- **One via (0.60 mm) can join:** False
- **What blocks the straight line:** copper gap 12.305 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits P0.16 [foreign] worst -0.335 mm, n=2 (via@40.7,20.8 @-0.335; F.Cu (41.25,26.75)-(40.70,20.80) @-0.180); P0.15 [protected] worst -0.180 mm, n=2 (F.Cu (41.75,26.75)-(41.75,23.10) @-0.180; via@41.75,23.1 @0.051); DEC0 [foreign] worst -0.048 mm, n=1 (pad U1.13 @-0.048); P0.14 [foreign] worst -0.001 mm, n=1 (pad U1.24 @-0.001); P0.13 [foreign] worst 0.077 mm, n=1 (pad U1.23 @0.077); GND [foreign] worst 0.088 mm, n=1 (pad U1.14 @0.088)

## 2. `COEX0` — 15.590 mm

- **Island A:** (28.645, 37.910) — F.Cu (26.20,38.00)-(33.00,38.00)
  - layers F.Cu; pads pad U3.3, pad U1.93, pad J15.1; anchor (48.974, 50.200); 24 primitives
- **Island B:** (28.645, 22.320) — pad R4.1
  - layers F.Cu; pads pad R4.1; anchor (29.810, 22.000); 5 primitives
- **Distance:** 15.590 mm
- **Same-layer gap:** 15.590 mm on F.Cu
- **One via (0.60 mm) can join:** False
- **What blocks the straight line:** copper gap 15.590 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits <no-net> [no-net copper] worst -0.090 mm, n=2 (pad U1.51 (no net) @-0.090; pad U1.73 (no net) @-0.090)

## 3. `VDD_GPIO` — 17.626 mm

- **Island A:** (75.080, 31.808) — F.Cu (75.14,32.00)-(75.14,39.05)
  - layers F.Cu; pads pad J9.5, pad J10.5, pad J13.18, pad R14.2, pad J11.3, pad TP13.1, pad U2.5, pad J17.3; anchor (101.388, 37.734); 49 primitives
- **Island B:** (70.036, 14.920) — B.Cu (70.00,8.00)-(70.00,14.80)
  - layers B.Cu; pads pad C11.1, pad J8.1, pad TP10.1, pad U3.1, pad C12.1; anchor (47.057, 15.286); 30 primitives
- **Distance:** 17.626 mm
- **Same-layer gap:** 18.444 mm on B.Cu
- **One via (0.60 mm) can join:** False
- **What blocks the straight line:** copper gap 17.626 mm is greater than 12 mm; closest copper is on different layers (F.Cu vs B.Cu); one track cannot join them and one 0.60 mm via cannot span the gap; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on B.Cu hits VIN_F [foreign] worst -0.269 mm, n=5 (via@71.575,17.663 @-0.269; B.Cu (71.58,16.20)-(71.58,19.06) @-0.240); P0.08 [foreign] worst -0.180 mm, n=1 (B.Cu (46.20,30.25)-(78.50,30.25) @-0.180); COEX2 [foreign] worst -0.180 mm, n=1 (B.Cu (72.00,24.60)-(100.30,24.60) @-0.180)

## 4. `VDD_GPIO` — 27.034 mm

- **Island A:** (74.519, 39.306) — pad U2.5
  - layers F.Cu; pads pad J9.5, pad J10.5, pad J13.18, pad R14.2, pad J11.3, pad TP13.1, pad U2.5, pad J17.3; anchor (101.388, 37.734); 49 primitives
- **Island B:** (58.859, 61.343) — pad J18.9
  - layers B.Cu, F.Cu; pads pad J18.9, pad J12.17, pad J12.18; anchor (49.941, 73.375); 8 primitives
- **Distance:** 27.034 mm
- **Same-layer gap:** 27.034 mm on F.Cu
- **One via (0.60 mm) can join:** False
- **What blocks the straight line:** copper gap 27.034 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits ENABLE [foreign] worst -0.180 mm, n=2 (F.Cu (72.86,40.95)-(72.86,42.40) @-0.180; pad U2.3 @-0.090); SIM_CLK [foreign] worst -0.180 mm, n=4 (F.Cu (71.68,44.00)-(70.90,44.00) @-0.180; F.Cu (71.68,44.00)-(71.68,42.40) @-0.180); P0.20 [foreign] worst -0.180 mm, n=1 (F.Cu (55.78,60.90)-(74.16,60.90) @-0.180)

## 5. `P0.31` — 29.078 mm

- **Island A:** (102.501, 75.250) — pad J13.16
  - layers B.Cu, F.Cu; pads pad J13.16; anchor (102.100, 76.000); 1 primitives
- **Island B:** (115.599, 49.290) — pad J11.2
  - layers B.Cu, F.Cu; pads pad J11.2; anchor (116.000, 48.540); 1 primitives
- **Distance:** 29.078 mm
- **Same-layer gap:** 29.078 mm on F.Cu
- **One via (0.60 mm) can join:** False
- **What blocks the straight line:** copper gap 29.078 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits P0.22 [protected] worst -0.294 mm, n=2 (via@104.5,71.5 @-0.294; F.Cu (104.50,71.50)-(106.50,71.50) @-0.084); GND [foreign] worst -0.216 mm, n=1 (via@110.0,60.0 @-0.216); VDD_GPIO [foreign] worst -0.215 mm, n=2 (F.Cu (104.00,67.08)-(107.18,67.08) @-0.215; F.Cu (105.10,51.08)-(116.00,51.08) @-0.215); P0.04 [protected] worst -0.180 mm, n=1 (F.Cu (114.80,52.50)-(108.45,52.50) @-0.180)

## Not attempted

No backup, no rip, no track, no via. The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved.

