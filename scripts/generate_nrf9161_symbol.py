#!/usr/bin/env python3
"""Generate nRF9161-LACA-R7 multi-unit KiCad symbol from Nordic PS v1.0 pin table."""
from pathlib import Path

OUT = Path("/home/anand/kicad-projects/nRF9161-DEV-BOARD/libraries/Nordic_nRF9161.kicad_sym")
GRID = 2.54
PLEN = 2.54

# Official nRF9161 Product Specification v1.0 Table 55
GND_PINS = [
    1, 5, 6, 7, 8, 9, 11, 14, 17, 21, 27, 31, 36, 41, 44, 47, 50, 52, 56,
    60, 62, 63, 65, 66, 68, 69, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82,
    85, 90, 94, 98, 103,
]
RES_PINS = [10, 51, 70, 71, 73] + list(range(104, 128))

GPIO = {
    95: "P0.00", 96: "P0.01", 97: "P0.02", 99: "P0.03", 100: "P0.04",
    2: "P0.05", 3: "P0.06", 4: "P0.07", 15: "P0.08", 16: "P0.09",
    18: "P0.10", 19: "P0.11", 20: "P0.12",
    23: "P0.13_AIN0", 24: "P0.14_AIN1", 25: "P0.15_AIN2", 26: "P0.16_AIN3",
    28: "P0.17_AIN4", 29: "P0.18_AIN5", 30: "P0.19_AIN6", 35: "P0.20_AIN7",
    37: "P0.21_TRACECLK", 38: "P0.22_TRACEDATA0", 39: "P0.23_TRACEDATA1",
    40: "P0.24_TRACEDATA2", 42: "P0.25_TRACEDATA3",
    83: "P0.26", 84: "P0.27", 86: "P0.28", 87: "P0.29", 88: "P0.30", 89: "P0.31",
}


def pin(name, number, ptype, x, y, ang, shape="line"):
    return f'''			(pin {ptype} {shape}
				(at {x:.2f} {y:.2f} {ang})
				(length {PLEN})
				(name "{name}" (effects (font (size 1.27 1.27))))
				(number "{number}" (effects (font (size 1.27 1.27))))
			)'''


def rect(x1, y1, x2, y2):
    return f'''			(rectangle
				(start {x1:.2f} {y1:.2f})
				(end {x2:.2f} {y2:.2f})
				(stroke (width 0.254) (type default))
				(fill (type background))
			)'''


def unit_box(unit, title, left_pins, right_pins, extra_pins=""):
    """left_pins/right_pins: list of (name, number, type, shape?)"""
    n = max(len(left_pins), len(right_pins), 4)
    body_h = (n + 1) * GRID
    y_top = body_h / 2
    y_bot = -body_h / 2
    x_left_body, x_right_body = -12.70, 12.70
    pins = []
    for i, item in enumerate(left_pins):
        name, num, ptype = item[0], item[1], item[2]
        shape = item[3] if len(item) > 3 else "line"
        y = y_top - GRID * (i + 1)
        pins.append(pin(name, num, ptype, x_left_body - PLEN, y, 0, shape))
    for i, item in enumerate(right_pins):
        name, num, ptype = item[0], item[1], item[2]
        shape = item[3] if len(item) > 3 else "line"
        y = y_top - GRID * (i + 1)
        pins.append(pin(name, num, ptype, x_right_body + PLEN, y, 180, shape))
    title_text = f'''			(text "{title}"
				(at 0 {y_top - 0.5} 0)
				(effects (font (size 1.27 1.27) (bold yes)))
			)'''
    return f'''		(symbol "NRF9161-LACA-R7_{unit}_1"
{rect(x_left_body, y_top, x_right_body, y_bot)}
{title_text}
{chr(10).join(pins)}
{extra_pins}
		)'''


# Unit 1: Power
left1 = [
    ("VDD1", 102, "power_in"),
    ("VDD2", 22, "power_in"),
    ("VDD_GPIO", 12, "power_in"),
    ("ENABLE", 101, "input"),
    ("DEC0", 13, "passive"),
]
# Stack all GND onto one visual pin (same coordinate)
gnd_y = -((len(left1) + 1) * GRID) / 2  # will be recalculated in unit_box
# We'll add stacked GND as extra pins after unit_box by putting GND as last left pin
# and remaining GND stacked at same position via extra_pins.
left1.append(("GND", GND_PINS[0], "power_in"))
right1 = [("GND", p, "power_in") for p in GND_PINS[1:11]]

# Unit 2: RF / modem control
left2 = [
    ("ANT", 61, "passive"),
    ("AUX", 64, "passive"),
    ("GPS", 67, "passive"),
]
right2 = [
    ("MAGPIO0", 55, "bidirectional"),
    ("MAGPIO1", 54, "bidirectional"),
    ("MAGPIO2", 53, "bidirectional"),
    ("MIPI_SDATA", 59, "bidirectional"),
    ("MIPI_SCLK", 58, "bidirectional"),
    ("MIPI_VIO", 57, "bidirectional"),
    ("COEX0", 93, "bidirectional"),
    ("COEX1", 92, "bidirectional"),
    ("COEX2", 91, "bidirectional"),
]

# Unit 3: GPIO 0-15
gpio_order_a = [
    (95, "P0.00"), (96, "P0.01"), (97, "P0.02"), (99, "P0.03"),
    (100, "P0.04"), (2, "P0.05"), (3, "P0.06"), (4, "P0.07"),
    (15, "P0.08"), (16, "P0.09"), (18, "P0.10"), (19, "P0.11"),
    (20, "P0.12"), (23, "P0.13_AIN0"), (24, "P0.14_AIN1"), (25, "P0.15_AIN2"),
]
left3 = [(n, p, "bidirectional") for p, n in gpio_order_a[:8]]
right3 = [(n, p, "bidirectional") for p, n in gpio_order_a[8:]]

# Unit 4: GPIO 16-31
gpio_order_b = [
    (26, "P0.16_AIN3"), (28, "P0.17_AIN4"), (29, "P0.18_AIN5"), (30, "P0.19_AIN6"),
    (35, "P0.20_AIN7"), (37, "P0.21_TRACECLK"), (38, "P0.22_TRACEDATA0"),
    (39, "P0.23_TRACEDATA1"), (40, "P0.24_TRACEDATA2"), (42, "P0.25_TRACEDATA3"),
    (83, "P0.26"), (84, "P0.27"), (86, "P0.28"), (87, "P0.29"),
    (88, "P0.30"), (89, "P0.31"),
]
left4 = [(n, p, "bidirectional") for p, n in gpio_order_b[:8]]
right4 = [(n, p, "bidirectional") for p, n in gpio_order_b[8:]]

# Unit 5: Debug / SIM / reserved
left5 = [
    ("SWDIO", 34, "bidirectional"),
    ("SWDCLK", 33, "input"),
    ("~{RESET}", 32, "input", "inverted"),
    ("SIM_RST", 43, "output"),
    ("SIM_CLK", 46, "output"),
    ("SIM_IO", 48, "bidirectional"),
    ("SIM_1V8", 49, "power_out"),
    ("SIM_DET", 45, "no_connect"),  # PS: Not used. Must be left floating.
]
right5 = [("RES", p, "no_connect") for p in RES_PINS[:16]]

# Remaining GND and RES go on extra stacked pins
extra_gnd = ""
# Remaining GND after first + 10 on right of unit 1
remain_gnd = GND_PINS[11:]
# We'll put remaining GND as additional right pins on unit 1 by extending right1
right1 += [("GND", p, "power_in") for p in remain_gnd]
remain_res = RES_PINS[16:]
right5 += [("RES", p, "no_connect") for p in remain_res]

units = [
    unit_box(1, "POWER", left1, right1),
    unit_box(2, "RF / MODEM CTRL", left2, right2),
    unit_box(3, "GPIO P0.00-P0.15", left3, right3),
    unit_box(4, "GPIO P0.16-P0.31", left4, right4),
    unit_box(5, "DEBUG / SIM / RES", left5, right5),
]

header = '''(kicad_symbol_lib
	(version 20241209)
	(generator "nrf9161_official_ps")
	(generator_version "9.0")
	(symbol "NRF9161-LACA-R7"
		(pin_names (offset 1.016))
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(duplicate_pin_numbers_are_jumpers no)
		(property "Reference" "U"
			(at 0 15.24 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Value" "NRF9161-LACA-R7"
			(at 0 12.70 0)
			(effects (font (size 1.27 1.27)))
		)
		(property "Footprint" "Nordic_nRF9161:nRF9161_LGA_16.0x10.5mm"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Datasheet" "https://docs.nordicsemi.com/bundle/ps_nrf9161"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Description" "Nordic nRF9161 SiP LTE-M/NB-IoT/DECT NR+/GNSS, 16.0x10.5mm LGA. Pinout from nRF9161 Product Specification v1.0 Table 55."
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Manufacturer" "Nordic Semiconductor"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "Manufacturer_Part_Number" "nRF9161-LACA-R7"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "ki_keywords" "nRF9161 Nordic LTE NB-IoT DECT NR+ GNSS SiP"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
		(property "ki_fp_filters" "nRF9161_LGA*"
			(at 0 0 0)
			(effects (font (size 1.27 1.27)) (hide yes))
		)
'''

footer = '''		(embedded_fonts no)
	)
)
'''

OUT.write_text(header + "\n".join(units) + footer)
print(f"Wrote {OUT}")

# Verify all 127 pin numbers present
text = OUT.read_text()
import re
nums = {int(n) for n in re.findall(r'\(number "(\d+)"', text)}
missing = [i for i in range(1, 128) if i not in nums]
extra = sorted(n for n in nums if n < 1 or n > 127)
print(f"pins present: {len(nums)} missing: {missing} extra: {extra}")
