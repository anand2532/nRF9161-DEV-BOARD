# PASS30AO shortlist — five shortest non-GND island gaps

**Timestamp:** 2026-09-30 10:37 IST
**Decision:** **NO-ROUTE** (no copper edit)
**Gate:** close the remaining VDD_GPIO open only if it is ≤ 25 mm; otherwise close the shortest other non-GND gap only if it is ≤ 20 mm. One 0.18 mm route, ≤ 6 segments, one via only if required. Do not repeat the locked y=7.050 path. Stay east of x=24.2. Do not use the y=44.60 pocket.
**Result:** remaining VDD_GPIO is **27.034 mm** (> 25 mm). Shortest other non-GND gap is `P0.31` **29.078 mm** (> 20 mm). No pair qualifies, so nothing was routed.

GND zone islands ignored. Distance is copper-edge to copper-edge. Island counts match DRC opens (`islands = opens + 1`) on every non-GND open net. Protected keeps were measured: P0.19 is 36.661 mm and P0.22 is 51.605 mm, both outside this five. P0.15, VDD2, SIM_IO_C, and SIM_CLK_C have no open.

## 1. `VDD_GPIO` — 27.034 mm

- **Island A:** F.Cu (74.519, 39.306) — pad U2.5
  - island layers B.Cu, F.Cu; pads pad C11.1, pad J8.1, pad J9.5, pad TP10.1, pad J10.5, pad J13.18, pad R14.2, pad J11.3; anchor (77.799, 28.130); 90 primitives
- **Island B:** B.Cu+F.Cu (58.859, 61.343) — pad J18.9
  - island layers B.Cu, F.Cu; pads pad J18.9, pad J12.17, pad J12.18; anchor (49.941, 73.375); 8 primitives
- **Distance:** 27.034 mm
- **Same-layer gap:** 27.034 mm on F.Cu
- **Blocker:** remaining VDD_GPIO open is 27.034 mm, over the 25 mm cap, so priority 1 does not qualify; copper gap 27.034 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits ENABLE [foreign] worst -0.180 mm, n=2 (F.Cu (72.86,40.95)-(72.86,42.40) @-0.180; pad U2.3 @-0.090); SIM_CLK [foreign] worst -0.180 mm, n=4 (F.Cu (71.68,44.00)-(70.90,44.00) @-0.180; F.Cu (71.68,44.00)-(71.68,42.40) @-0.180); P0.20 [foreign] worst -0.180 mm, n=1 (F.Cu (55.78,60.90)-(74.16,60.90) @-0.180)

## 2. `P0.31` — 29.078 mm

- **Island A:** B.Cu+F.Cu (102.501, 75.250) — pad J13.16
  - island layers B.Cu, F.Cu; pads pad J13.16; anchor (102.100, 76.000); 1 primitives
- **Island B:** B.Cu+F.Cu (115.599, 49.290) — pad J11.2
  - island layers B.Cu, F.Cu; pads pad J11.2; anchor (116.000, 48.540); 1 primitives
- **Distance:** 29.078 mm
- **Same-layer gap:** 29.078 mm on F.Cu
- **Blocker:** 29.078 mm is over the 20 mm cap for any non-VDD_GPIO gap (remaining VDD_GPIO is 27.034 mm, already over 25 mm); copper gap 29.078 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits P0.22 [protected] worst -0.294 mm, n=2 (via@104.5,71.5 @-0.294; F.Cu (104.50,71.50)-(106.50,71.50) @-0.084); GND [foreign] worst -0.216 mm, n=1 (via@110.0,60.0 @-0.216); VDD_GPIO [foreign] worst -0.215 mm, n=2 (F.Cu (104.00,67.08)-(107.18,67.08) @-0.215; F.Cu (105.10,51.08)-(116.00,51.08) @-0.215); P0.04 [protected] worst -0.180 mm, n=1 (F.Cu (114.80,52.50)-(108.45,52.50) @-0.180)

## 3. `P0.30` — 32.207 mm

- **Island A:** B.Cu+F.Cu (99.961, 75.250) — pad J13.15
  - island layers B.Cu, F.Cu; pads pad J13.15; anchor (99.560, 76.000); 1 primitives
- **Island B:** B.Cu+F.Cu (115.150, 46.850) — pad J11.1
  - island layers B.Cu, F.Cu; pads pad J11.1; anchor (116.000, 46.000); 1 primitives
- **Distance:** 32.207 mm
- **Same-layer gap:** 32.207 mm on F.Cu
- **Blocker:** 32.207 mm is over the 20 mm cap for any non-VDD_GPIO gap (remaining VDD_GPIO is 27.034 mm, already over 25 mm); copper gap 32.207 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits VDD_GPIO [foreign] worst -0.215 mm, n=5 (F.Cu (105.10,67.08)-(105.10,51.08) @-0.215; F.Cu (104.00,67.08)-(107.18,67.08) @-0.215); P0.04 [protected] worst -0.180 mm, n=3 (F.Cu (114.80,52.50)-(108.45,52.50) @-0.180; F.Cu (113.80,49.20)-(113.80,36.80) @-0.098); GND [foreign] worst -0.090 mm, n=1 (pad J15.6 @-0.090)

## 4. `P0.14` — 34.038 mm

- **Island A:** B.Cu+F.Cu (40.623, 61.154) — pad J18.2
  - island layers B.Cu, F.Cu; pads pad J18.2, pad J12.15; anchor (41.050, 74.121); 14 primitives
- **Island B:** F.Cu (42.136, 27.150) — pad U1.24
  - island layers F.Cu; pads pad U1.24; anchor (42.250, 26.750); 1 primitives
- **Distance:** 34.038 mm
- **Same-layer gap:** 34.038 mm on F.Cu
- **Blocker:** 34.038 mm is over the 20 mm cap for any non-VDD_GPIO gap (remaining VDD_GPIO is 27.034 mm, already over 25 mm); copper gap 34.038 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits GND [foreign] worst -0.336 mm, n=8 (via@42.0,29.0 @-0.336; via@42.0,32.0 @-0.310); P0.04 [protected] worst -0.168 mm, n=3 (F.Cu (41.25,46.80)-(37.40,46.80) @-0.168; F.Cu (41.25,42.50)-(41.25,46.80) @-0.168); P0.03 [foreign] worst -0.156 mm, n=4 (via@41.75,41.1 @-0.156; F.Cu (41.75,37.25)-(41.75,41.10) @-0.117); <no-net> [no-net copper] worst -0.090 mm, n=1 (pad U1.127 (no net) @-0.090)

## 5. `P0.16` — 34.259 mm

- **Island A:** F.Cu (41.364, 27.150) — pad U1.26
  - island layers B.Cu, F.Cu; pads pad U1.26; anchor (40.975, 23.775); 3 primitives
- **Island B:** B.Cu+F.Cu (45.537, 61.154) — pad J18.4
  - island layers B.Cu, F.Cu; pads pad J18.4, pad J13.1; anchor (54.810, 71.500); 8 primitives
- **Distance:** 34.259 mm
- **Same-layer gap:** 34.259 mm on F.Cu
- **Blocker:** 34.259 mm is over the 20 mm cap for any non-VDD_GPIO gap (remaining VDD_GPIO is 27.034 mm, already over 25 mm); copper gap 34.259 mm is greater than 12 mm; one via (0.60 mm OD) cannot bridge this XY gap; straight 0.18 mm track on F.Cu hits GND [foreign] worst -0.349 mm, n=8 (via@42.0,32.0 @-0.349; pad U1.103 @-0.090); ENABLE [foreign] worst -0.321 mm, n=7 (via@43.4,45.126 @-0.321; F.Cu (52.00,44.00)-(42.75,44.00) @-0.180); <no-net> [no-net copper] worst -0.074 mm, n=2 (pad U1.105 (no net) @-0.074; pad U1.104 (no net) @0.074); P0.04 [protected] worst 0.068 mm, n=1 (pad U1.100 @0.068)

## Not attempted

No backup, no rip, no track, no via. The locked y=7.050 VDD_GPIO path was not repeated. The y=44.60 B.Cu pocket was not used. Headers and U1 were not moved. No Gerbers. No git commit.

