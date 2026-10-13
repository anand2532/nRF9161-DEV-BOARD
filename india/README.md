# Building the nRF9161 v2 board in India

This guide covers Indian options for making the board and for buying parts. The reference build is still **JLCPCB fab + PCBA with LCSC parts**; see the main [README](../README.md#fabrication-and-ordering-jlcpcb). Use the options here for local fab, hand assembly, rework or spares.

Everything below was taken from each vendor's own page on 2026-10-13 IST. Where a vendor's site doesn't state something, it is marked **unverified**. Ask the vendor to confirm it before you order.

## What the board needs from a fab

From [`fab/staging-v2-36d8578/ORDER_NOTES.md`](../fab/staging-v2-36d8578/ORDER_NOTES.md) and the PCB file:

- 4 layers, 1.6 mm, ENIG, controlled-impedance stackup (0.12 / 1.2 / 0.12 mm)
- Vias: 218 × 0.30 mm drill / 0.60 mm pad, **21 × 0.20 mm drill / 0.30 mm pad**, 9 × 0.25 mm drill / 0.40 mm pad
- **30 epoxy-filled, copper-capped vias** per board (POFV, IPC-4761 Type VII), which are the 0.20 and 0.25 mm ones
- Double-sided SMT assembly with 0201 passives, an LGA SiP (U1, X-ray recommended), USON-8 0.5 mm pitch (U4), plus one THT header (J20)

The **0.20 mm drill on a 0.30 mm pad with filling and capping** is what rules out most low-cost fabs.

## (a) PCB fabrication and assembly in India

| Vendor | Layers | Min drill / via | ENIG | Filled / capped vias | Assembly | Lead time (published) | Can likely build 0.20 mm filled vias? |
|---|---|---|---|---|---|---|---|
| [PCB Power](https://www.pcbpower.com/) (Gujarat) | Up to 24 ([fab page](https://www.pcbpower.com/pcbmanufacturing)) | Min via tool 0.20 mm, min finished via 0.10 mm, **min via pad 0.40 mm outer** ([capabilities](https://www.pcbpower.com/technology/technical-capabilities-rigid-pcb)) | Yes | "Via Fill" in their [design guideline](https://www.pcbpower.com/page/design-guideline) is a **second solder-mask layer** (closes ≤0.25 mm holes). Epoxy fill + copper cap is not listed: **unverified**. Via-on-pad offered for non-BGA ([PCBA caps](https://www.pcbpower.com/technology/technical-capabilities-pcba)) | Yes: SMT/THT, single or double-sided, 0201 and smaller, QFN, BGA | "Starting from 3 working days" (fab page) | **Partly.** 0.20 mm drill is OK, but our 0.30 mm pad is under their 0.40 mm minimum, and POFV is unverified. |
| [LionCircuits](https://www.lioncircuits.com/pcb-fabrication) (Bengaluru) | 2/4/6 standard; up to 12 via sales ([capabilities](https://www.lioncircuits.com/pcb-manufacturing-capabilities/rigid-pcb)) | Standard **0.3 mm** min drill; 0.15 mm listed for the advanced tier ([fab page](https://www.lioncircuits.com/pcb-fabrication)) | Yes (instant-quote option) | Not stated: **unverified** | Yes: SMT + THT, one or both sides; machine assembly needs ≥50 × 100 mm or a panel ([capabilities](https://www.lioncircuits.com/pcb-manufacturing-capabilities)) | Fab: standard 6 working days, 48 h rush, 24 h super rush. Assembly: 4 working days after parts arrive ([FAQ](https://www.lioncircuits.com/faq/pcb-assembly/how-long-do-you-take-for-assembly)) | **Not on the standard instant-quote tier.** Ask sales about the advanced tier + filling. |
| [Robu PCB service](https://robu.in/product/online-pcb-manufacturing-service/) | 1, 2, 4, 6 ([capabilities](https://robu.in/pcb-manufacturing-capabilities/)) | Multilayer: min via hole 0.20 mm, **min via diameter 0.45 mm (limit 0.40 mm)**. 1-2 layer: 0.3 mm hole / 0.5 mm via | Not stated on the capabilities page: **unverified** | Not listed; no blind/buried vias: **unverified / likely no** | Not stated on the capabilities page: **unverified** | Earlier quote: 15-20 business days (see note) | **No.** The 0.30 mm pads on our 0.20 mm vias are under Robu's 0.40 mm via-diameter limit, and via filling isn't offered on the page. |
| [Fine-Line Circuits Ltd](https://www.finelineindia.com/capabilities/) | Multilayer, HDI, rigid-flex, PTFE (company profile) | Hole size 8 mil / 0.20 mm ([LinkedIn profile](https://linkedin.com/company/fine-line-circuits-limited)) | Lead-free finishes listed; ENIG specifically: **unverified** | "Via filling and capping" stated in the profile | Fab house; assembly **unverified** | Not published | **Likely yes**: it states both 0.20 mm holes and via filling/capping. Export-oriented, so expect a production-style quote. |
| [Hi-Q Electronics](https://www.hiqelectronics.com/standard-multilayer-pcbs/) | Up to 38 (per search summary of the page) | 0.15 mm min hole, 0.45 mm min pad (per search summary) | Yes (per search summary) | **Unverified** | **Unverified** | Not published | **Possibly** on drill; the 0.45 mm pad minimum is larger than our 0.30 mm. The page didn't load directly, so recheck it. |
| [Sienna ECAD](https://www.siennaecad.com/prototype.html) (Bengaluru/Chennai) | Up to 24 (assembly page) | Not published: **unverified** | **Unverified** | **Unverified** (HDI listed on its [PCB Directory profile](https://www.pcbdirectory.com/manufacturer/profile/sienna-ecad-technologies)) | Yes: complex double-sided, 01005, 0.4 mm BGA/POP, AOI, flying probe | Not published ("quick turn prototype") | **Unverified.** A strong option for **assembly** of the LGA + 0201 parts on boards made elsewhere. |
| [Circuitwala](https://www.circuitwala.com/technical-capabilities/) (Ahmedabad) | **2** on its own capabilities page | 0.5 mm min via | Not stated | No | Turnkey assembly per [PCB Directory](https://www.pcbdirectory.com/manufacturer/profile/circuitwala) | Not published | **No.** 2-layer, 0.5 mm via. |
| [Rhydo Technologies](https://www.rhydo.com/electronic-manufacturing-services/) | Site lists assembly/EMS services; no fab specs found | **Unverified** | **Unverified** | **Unverified** | EMS / assembly | Not published | **Unverified** (assembly only, as far as the site shows). |

**Quote links:** PCB Power instant quote on its [home page](https://www.pcbpower.com/), LionCircuits instant quote from its [fab page](https://www.lioncircuits.com/pcb-fabrication) (upload Gerber, plus BOM and CPL for assembly), Robu via its [PCB service page](https://robu.in/product/online-pcb-manufacturing-service/). For the others, email the sales address on the site with the Gerber and the via table above.

**Robu quote seen earlier:** ₹11,957 for 5 panels, 15-20 business days. The specs behind that number (ENIG, filled vias, impedance) were **not confirmed**, so don't treat it as a price for this board. Robu's current capability page lists a **0.20 mm** minimum via hole for multilayer boards (0.3 mm applies to 1-2 layers). The blocker for this board is the **0.40 mm minimum via diameter** (our 0.20 mm vias have 0.30 mm pads) and the lack of via filling.

**Practical path in India:**
1. Ask Fine-Line, or PCB Power, to quote with the 0.20 mm / 0.30 mm filled vias exactly as designed.
2. If no local fab will do it, keep JLC for the bare PCB and assemble in India (LionCircuits, Sienna ECAD, PCB Power), or hand-assemble with the parts below.
3. Don't enlarge the 0.20 mm vias to suit a fab without a layout + RF re-review. They sit in the U1/U4 fan-out and near the RF keepouts.

Gerbers: see [`gerbers/`](gerbers/README.md).

## (b) Buying components in India

Per-line sourcing with exact URLs, INR prices and stock is in **[`BOM_INDIA.csv`](BOM_INDIA.csv)** ([`.xlsx`](BOM_INDIA.xlsx)).

| Vendor | Notes |
|---|---|
| [Robu.in](https://robu.in/) | Best for passives, LEDs, the LDO and the TI translators. Prices include GST. Most 0201/0402 MLCCs are ₹0.1-₹2 each. Several exact Murata parts are out of stock (BLM18KG, BLM21PG, GRM21BR61A476ME15L). |
| [LionCircuits parts](https://www.lioncircuits.com/) | Best India source for the hard parts: **nRF9161-LACA-R7, TPD3F303DPVR, TPS22919DCKR, SF72S006 SIM socket, FTSH-105 SWD header, 0468002 fuse, U.FL**. Ships in 7-10 days. Many lines price from 10 pcs. |
| [Amazon.in](https://www.amazon.in/) | Not searched line by line for this BOM (Robu and LionCircuits covered every line first). Useful for tools, solder paste, flux and generic headers. |
| [Evelta](https://evelta.com/) | Indian distributor; worth checking for the TI parts and connectors. Not used in the BOM. |
| [element14 India](https://in.element14.com/) | Large catalogue in INR. Good backup for Murata/TI exact MPNs. Not checked line by line. |
| [mouser.in](https://www.mouser.in/), [digikey.in](https://www.digikey.in/) | Every exact MPN. Prices in INR. Customs duty may apply; free shipping above their thresholds. Use them for anything out of stock locally (C3/C7, L1/L2). |

**Totals** (cheapest in-stock exact MPN, unit price × qty, excluding shipping and MOQ): see the bottom rows of `BOM_INDIA.csv`. U1 (nRF9161, ₹3,745) is about two thirds of the cost.
