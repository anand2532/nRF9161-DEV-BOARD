# BOM vs Footprint Audit — nRF9161 v2

- Audited HEAD: 13dce7119f8f2cdaa978353099656e27ce0ae3fc (branch v2, matches origin/v2). Read-only: BOM.csv, schematic/ and .kicad_pcb are unchanged.
- Sources: footprints from the live schematic/*.kicad_sch (they match the PCB footprints for the flagged parts); MPNs from BOM.csv; stock and Basic/Extended from the JLCPCB SMT parts API on 2026-10-13 (IST). LCSC model and brand were cross-checked on the LCSC detail API. Stock numbers can change.
- DNP parts (C21–C24, C31, C32, C39), JP2 (solder jumper) and the test points are not assembled, so they have no LCSC number.

## Mismatches and proposals
1. **D1** PMEG4030ER (SOD-123W) on a D_SMA land. Proposal: change the MPN to **SS34, C8678 (Basic, about 4.08M in stock)**, rated 40 V / 3 A in SMA with Vf about 0.5 V, which covers the PMEG4030ER rating. No Layout change. Also fix the BOM.csv Package text "SOD-123W" to SMA.
2. **FB4** BLM18PG221SN1D (0603) on an L_0805 land. Proposal: **BLM21PG221SN1D, C85840**, 0805, 220 Ω at 100 MHz, 2 A, 0.05 Ω. Its current rating is higher than the 1.4 A of the 0603 part. No Layout change.
3. **D3/D4** KP-2012SGC (0805) on an LED_0603 land. Proposal: **LTST-C191KGKT, C125098**, 0603 green, 571 nm, Vf about 2.0 V. The 1 k resistors give about 1 mA from 3.3 V. No Layout change. (The Kingbright 0603 equivalent, KP-1608SGC C598263, has only 1502 in stock.)
4. **F1** Confirmed as a real part: Littelfuse 0468002.NR (468 series, 2 A fast-acting, 1206). LCSC lists it as 0468002.NRHF **C187611**, about 16k in stock. No change. The Robu PTC substitute (BSMD1206-260) is a different fuse type.
5. **U4 TPD3F303 — new, needs Layout.** TI's DPV package is USON-8, 2.1 × 1.6 mm, 0.5 mm pitch. The footprint is "1.45x1.45mm_P0.4mm", and its pad x-positions (−0.65/−0.25/0.25/0.65) mix 0.4 and 0.5 mm pitch and include an EP. It does not match DPV, and it was not verified against DQD (WSON 1.7 × 1.35 mm). Proposal: keep TPD3F303DPVR (C2865991, 4078 in stock) and have Layout replace the land with TI's DPV land pattern. The other option is TPD3F303DQDR (C2869050) with a DQD land. Either way this needs Layout.
6. **L1/L2** The BOM MPN is a 10 nH LQW15AN10NG00, but the parts are fitted as 0R. Proposal: 0402WGF0000TCE **C17168 (Basic)** until VNA tuning. No Layout change.
7. Murata capacitor MPNs not stocked at JLC were swapped for same-size, same-or-better parts: C1, C2/C30/C33, C27, C28 (moved to C0G), C29 and C34. J7 SF72S006V4BR → SF72S006VBDR2500 (check the pinout). SW2 KXT311LHS (322 in stock) → KXT331LHS.

## Needs Layout
- U4 only (footprint change). Every other item is an MPN-only change.
- Check: J8 FTSH-105-01-L-DV-K has keying pegs. Confirm the current SMD footprint has peg holes, or keep the non-K part (low JLC stock).

## Stock concerns
- **U1 nRF9161-LACA-R7: only 6 at JLC (C21547412).** Consign the parts or buy from Mouser or DigiKey.
- L4 LQW15ANR10J00D: 850. U4: 4078. J8: 2574.

## Table
| Ref | Value | Current footprint | Current MPN | Issue | Proposed MPN | LCSC | JLC stock | Basic/Ext | Needs Layout |
|---|---|---|---|---|---|---|---|---|---|
| U1 | NRF9161-LACA-R7 | Board:nRF9161_LGA_16.0x10.5mm | nRF9161-LACA-R7 | OK; JLC stock very low | NRF9161-LACA-R7 | C21547412 | 6 | Extended | n |
| U2 | TLV73333PDBV | SOT-23-5 | TLV73333PDBVR | OK | TLV73333PDBVR | C134139 | 42996 | Extended | n |
| U3 | TPS22919DCKR | SOT-363_SC-70-6 | TPS22919DCKR | OK | TPS22919DCKR | C2149796 | 61479 | Extended | n |
| U4 | TPD3F303DPV | Board:TI_TPD3F303_USON-8_1.45x1.45mm_P0.4mm | TPD3F303DPVR | MISMATCH: DPV pkg is USON-8 2.1x1.6mm 0.5mm pitch (TI); footprint is 1.45x1.45 P0.4 with mixed 0.4/0.5 pad pitch + EP. Neither DPV nor DQD (WSON 1.7x1.35) verified | TPD3F303DPVR (keep) + replace footprint with TI DPV land pattern; alt TPD3F303DQDR C2869050 if footprint redrawn to DQD | C2865991 | 4078 | Extended | y |
| C1 | 10uF/16V | C_0805 | GRM21BR61C106ME15 | JLC stock 2 | CL21A106KOQNNNE | C1713 | 307836 | Extended | n |
| C2,C30,C33 | 100nF | C_0402 | GRM155R61A104KA01 | JLC stock 27 | CL05B104KO5NNNC | C1525 | 23509498 | Basic | n |
| C3,C7 | 47uF/10V | C_0805 | GRM21BR61A476ME15 | OK | GRM21BR61A476ME15L | C124129 | 44604 | Extended | n |
| C4,C8,C11,C13 | 4.7uF | C_0402 | GRM155R61A475MEAA | OK | GRM155R61A475MEAAD | C335105 | 165860 | Extended | n |
| C5,C9,C12,C14 | 100nF | C_0201 | GRM033R61A104KE15 | OK | GRM033R61A104KE15D | C76934 | 492693 | Extended | n |
| C6,C10 | 15pF C0G | C_0201 | GJM0335C1E150JB01 | OK | GJM0335C1E150JB01D | C710722 | 11944 | Extended | n |
| C27 | 100pF C0G | C_0201 | GJM0335C1E101JB01 | not stocked at JLC | GRM0335C1H101JA01D | C76922 | 446739 | Extended | n |
| C28 | 100pF | C_0402 | GRM155R71H101KA01 | not stocked; C0G is better | GRM1555C1H101JA01D | C77177 | 1043903 | Extended | n |
| C29 | 10nF | C_0402 | GRM155R71H103KA01 | not stocked | CL05B103KB5NNNC | C15195 | 3952526 | Basic | n |
| C34 | 220nF | C_0402 | GRM155R61A224KE01 | not stocked | CL05B224KO5NNNC | C16772 | 1583653 | Basic | n |
| C35,C36,C37,C38 | 22pF C0G | C_0201 | GRM0335C1E220JA01 | OK | GRM0335C1H220JA01D | C76924 | 70339 | Extended | n |
| C40 | 100nF X7R | C_0402 | GRM155R71A104KA01D | OK | GRM155R71A104KA01D | C71687 | 19583 | Extended | n |
| C41-C48 | 100nF | C_0402 | CL05B104KO5NNNC | OK | CL05B104KO5NNNC | C1525 | 23509498 | Basic | n |
| D1 | PMEG4030ER | Diode_SMD:D_SMA | PMEG4030ER | MISMATCH: SOD-123W part on SMA land | SS34 (40V 3A SMA, Vf~0.5V@3A; MDD) | C8678 | 4077984 | Basic | n |
| D2 | SMAJ5.0A | D_SMA | SMAJ5.0A | OK (JLC stock is RUILON brand) | SMAJ5.0A | C10758 | 14778 | Extended | n |
| D3,D4 | Green LED | LED_0603 | KP-2012SGC | MISMATCH: KP-2012SGC is 0805 | LTST-C191KGKT (0603 green 571nm, Vf 2.0V; Robu has LTST-C190KGKT) | C125098 | 196322 | Extended | n |
| F1 | 2A fuse | Fuse_1206 | 0468002.NR | Confirmed real: Littelfuse 468 series 2A fast 1206 | 0468002.NRHF | C187611 | 16232 | Extended | n |
| FB1,FB2,FB3 | BLM18KG221SN1 | L_0603 | BLM18KG221SN1D | OK | BLM18KG221SN1D | C88980 | 68075 | Extended | n |
| FB4 | BLM18PG221SN1 | L_0805 | BLM18PG221SN1D | MISMATCH: 0603 part on 0805 land | BLM21PG221SN1D (0805 220R@100MHz, 2A, 0.05R; >= PG18 1.4A) | C85840 | 204288 | Extended | n |
| FB5 | BLM15HG102SN1 | L_0402 | BLM15HG102SN1D | OK | BLM15HG102SN1D | C76889 | 13091 | Extended | n |
| L1,L2 | 0R (fit) | L_0402 | LQW15AN10NG00 | MPN is a 10nH inductor but fit is 0R | 0402WGF0000TCE (0R until VNA tune) | C17168 | 9283694 | Basic | n |
| L4 | 100nH | L_0402 | LQW15ANR10J00 | OK; JLC stock low (850) | LQW15ANR10J00D | C86130 | 850 | Extended | n |
| R1 | 10k | R_0201 | RC0201FR-0710KL | OK | RC0201FR-0710KL | C106225 | 1907628 | Extended | n |
| R3,R10 | 1k | R_0402 | RC0402FR-071KL | OK | 0402WGF1001TCE | C11702 | 7849057 | Basic | n |
| R5 | 1k | R_0201 | RC0201FR-071KL | OK | RC0201FR-071KL | C138165 | 1942104 | Extended | n |
| R21,R23 | 100k | R_0402 | 0402WGF1003TCE | OK | 0402WGF1003TCE | C25741 | 10210621 | Basic | n |
| J2,J5 | U.FL | U.FL_Hirose_U.FL-R-SMT-1_Vertical | U.FL-R-SMT-1(10) | OK | U.FL-R-SMT-1(10) | C88373 | 26515 | Extended | n |
| J7 | nanoSIM 4FF | JAE_SIM_Card_SF72S006 | SF72S006V4BR | V4BR variant not at JLC | SF72S006VBDR2500 (same SF72S006 family; verify pin-out vs footprint) | C2977286 | 13083 | Extended | n |
| J8 | SWD 2x5 1.27 | PinHeader_2x05_P1.27mm_Vertical_SMD | FTSH-105-01-L-DV | OK; -K adds keying pegs - check holes | FTSH-105-01-L-DV-K | C5155080 | 2574 | Extended | n |
| J20 | 1x10 2.54 | PinHeader_1x10_P2.54mm_Vertical | 2.54-1*10PPin | OK | BOOMELE 2.54-1*10P | C57369 | 16904 | Extended | n |
| SW2 | RESET | SW_SPST_CK_KXT3 | KXT311LHS | OK; low stock | KXT331LHS (same KXT3 body) | C778127 | 9970 | Extended | n |
| U5,U6 | SN74LXC2T45 | VSSOP-8 | SN74LXC2T45DCUR | OK | SN74LXC2T45DCUR | C5217891 | 13275 | Extended | n |
| U7,U8 | SN74LXC1T45 | SOT-23-6 | SN74LXC1T45DBVR | OK | SN74LXC1T45DBVR | C4364198 | 7473 | Extended | n |
| Q1 | BSS138 | SOT-23 | BSS138 | OK | BSS138 | C52895 | 54256 | Extended | n |