# PASS30AD — B'' proposals ONLY (no execute)

**Timestamp:** 2026-09-23 13:31 IST  
**Mode:** PROPOSALS ONLY — board untouched (no footprint moves, no copper, no Gerbers)  
**Baseline:** after pass30ac **REVERT** → pass30z KEEP · unconnected=64 · shorting/clearance/crossing=0  
**SE column execute:** **FROZEN** until Hardware PM OK  

## J13 ban list (do not propose)

`(64,73)`, `(64,78.5)`, `(67,76)`, `(64,75)`, `(64,74.5)`

## Hard clears (live)

| Keep | Location / note |
| --- | --- |
| P0.22 vias | **(112.5, 32.5)**, (114.7, 29.9), (112.5, 29.9); also col @x109.2 |
| P0.04 F | V@x113.8 (y36.8–49.2); V@x114.8 (y52.5–78.8); H@y52.5 |
| VDD_GPIO | H@y51.08 to J11; jog x114.4 near J10; wall @x110.6/111 |
| J13 forest | P0.01 F@y74.5 (62→68) + via@(68,74.5); P0.08 vias@(65.2,73.95)/(65.2,72.25) |
| Banned landing | J10/J11 **(113.46,*)** — known fail vs P0.22 via@112.5 |

---

## 1. J10/J11-only (J13 stays (64,76))

West deltas probed (static pad↔via/track), **not** 113.46:

| J10 | J11 | Δx | Static clear? | Hits |
| --- | --- | ---: | --- | --- |
| (115.5, 28) | (115.5, 46) | −0.5 | **NO** | J10.2↔P0.22 via@(114.7,29.9) hole; J11.4↔P0.04 F@x114.8 |
| (115.0, 28) | (115.0, 46) | −1.0 | **NO** | + J10.5/6↔P0.04 F@x113.8 |
| (114.5, 28) | (114.5, 46) | −1.5 | **NO** | denser same class |
| (114.0, 28) | (114.0, 46) | −2.0 | **NO** | J10.5/6 ≈on P0.04@x113.8 |
| (113.46, 28) | (113.46, 46) | −2.54 | **NO (banned)** | J10.3↔P0.22 via@(112.5,32.5) |
| (113.0, 28) | (113.0, 46) | −3.0 | **NO** | J10.3↔via112.5 + P0.04 |

**Safe west deltas:** *none*  
**Conclusion:** No J10/J11-only west package ≤3 mm clears P0.22 via@112.5 **and** P0.04 F / VDD stubs. Even −0.5 mm fails.

---

## 2. Optional J13 west-only (≤2 mm, static probe)

J13 stays at **y=76**; shift toward x=62. Ban list excluded. Probe vs P0.01 F@y74.5 + via@(68,74.5) + P0.08 vias@x65.2:

| XY | Δx | |Δ| mm | Static clear vs forest? |
| --- | ---: | ---: | --- |
| **(63.5, 76)** | −0.5 | 0.5 | YES |
| **(63.0, 76)** | −1.0 | 1.0 | YES |
| **(62.5, 76)** | −1.5 | 1.5 | YES |
| **(62.0, 76)** | −2.0 | 2.0 | YES |

**Notes:**
- Static geometry only — **not** mid-DRC after full 20-pin reattach
- West moves pad1 away from P0.08 @x65.2; y=76 keeps Δy=1.5 from P0.01 F@y74.5
- Does **not** open J10/J11 east squeeze by itself (P0.22/P0.04 still block)
- If ever executed under PM OK: prefer **(62.0, 76)** / alt **(63.0, 76)**; full reattach all J13 nets

---

## 3. Recommendation — leave SE column frozen

### **LEAVE SE COLUMN FROZEN**

Rationale:
1. Static probe finds **no** safe ≤3 mm J10/J11-only west package against hard P0.22 / P0.04 / VDD keeps.
2. Optional J13 west-only ≤2 mm is statically forest-clear but **insufficient alone** to unlock SE duals.
3. Prior executes already dirty-reverted: pass30y (64,78.5)/(67,76)+J10/J11@113.46; pass30ab (64,75)/(64,74.5)+J10/J11@115/115.5.
4. pass30ac Package A also reverted (P0.01/P0.04/P0.06 east congestion).

**Preconditions before any unfreeze / B'' execute:**
- Copper pre-clear or redesign around P0.22 vias @(112.5,32.5) and @(114.7,29.9)
- Jog P0.04 F east trunks @x113.8 / @x114.8 out of J10/J11 west pad sweep
- Preserve VDD_GPIO H@y51.08 and wall @x110.6
- Explicit Hardware PM OK

**No copper execute this pass. No Gerbers. SE column remains frozen.**

---

## Artifacts

- `reports/PASS30AD_B_DOUBLE_PRIME_PROPOSALS.json`
- Probe context from live pass30z-keep board after pass30ac revert
