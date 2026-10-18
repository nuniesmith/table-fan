# Electronics – Bill of Materials, Wiring & Notes
**Status: Designed for implementation. See `electronics/wiring_diagram.svg` for the visual schematic.**

**MCU: Waveshare RP2040-Zero** (the small board in the photo – RP2040, USB-C,
23.5 × 18 mm, castellated edges, onboard BOOT/RESET buttons and WS2812 RGB LED).
It replaces the earlier Pico 2 W plan. Note: the Zero has **no wireless**
(RP2040, no Wi-Fi/Bluetooth) – none of the responsibilities below need it, so
nothing is lost.

**Mounting (locked in):** the bare Zero solders via its castellated edges to a
perfboard **carrier (30×70 mm prototype PCB cut to ~30×25 mm)**. The carrier also holds the 100k/24k
battery divider, the 10k tach pull-up, and the 4-pin fan header. The carrier
screws to 4× M2 bosses on the mezzanine plate. The Zero's USB-C faces the rear
cover cutout (with a printed strain-relief collar) – it is the **firmware /
programming port**, not the charger. (Friction-fit mounting was rejected:
vibration would walk the board loose and stress the USB-C.)

## Core Components
| Item | Qty | Notes / Example Part | Purpose |
|------|-----|----------------------|---------|
| Waveshare RP2040-Zero | 1 | RP2040, USB-C, 23.5 × 18 mm | Brain: PWM speed control, battery monitoring, status LED |
| Perfboard carrier | 1 | 30×70 mm prototype PCB, cut to ~30×25 mm | Holds the Zero (castellated solder) + divider + pull-up + fan header |
| Noctua NF-F12 iPPC-3000 PWM | 1 | Amazon link provided | Main 120 mm fan (12 V, max 3.6 W) |
| 4-pin PC Fan Header | 1 | Cut a 4-pin PWM fan extension cable in half | Plug-and-play fan connection on the carrier |
| Dial switch (speed + power) | 1 | **WH138 B10K linear with ON/OFF switch** (confirmed) – 24 mm body, 6 mm × 13.5 mm shaft, aluminum knob 21×17 mm included ×2; printed knob (`models/knob.scad`) is backup only | **The single user control.** Full CCW clicks OFF (hard power cut); CW sweeps slowest → fastest. Pot element is 0.2 W – fine, the wiper only drives the ADC (µA); the switch contacts carry ~0.5 A pack current |
| 18650 cells | 4 (or 8) | Samsung INR18650-35E 3500 mAh flat-top, unprotected | 4S1P pack (~52 Wh). 8 cells = 4 for the pack + 4 spares (4S2P does not fit the current bay – see below) |
| Battery sled (printed) | 1 | `models/battery_sled.scad` – 4×1 inline tray | Holds the 4 cells; series jumpers soldered over the end walls |
| 4S BMS | 1 | **4S 40A *Balance* version** (the one labelled "4S 40A Balance", not the plain "4S 40A") | Balance + over-charge/discharge/current/short protection. The balance function keeps the 4 cells even – take the balance variant. 40 A is overkill for ~1 A load but harmless. **A BMS is NOT a charger (see next row)** |
| 4S charger module | 1 | **4S 2 A Type-C boost charger module** (ordered) – multi 2S/3S/4S selectable, Type-C 5 V in → 16.8 V CC/CV out | **VERIFY the module is set to 4S before first charge.** Feed it from a USB-C PD supply. Output → BMS CHG+/CHG-; works with the dial OFF |
| 0.96" OLED display | 1 | SSD1306 128×64 I2C module, 3.3–5 V, 3.3 V logic compatible | Battery %, charging, fan speed – small rear pod on the bay cover. **No level shifter needed** (unlike the 1602). **Check the silkscreen on arrival: modules ship with GND/VCC pin order random** |
| Buck converter (12 V) | 1 | **MP1584 mini** module set to **12.0 V** | Fan rail from the 4S pack (fan draws only 0.3 A – the mini is plenty) |
| Buck converter (5 V) | 1 | **MP1584 mini** module set to **5.0 V** | **Powers the RP2040-Zero via its 5V pin.** The Zero exposes no VSYS pin, and 14.8–16.8 V straight from the 4S pack would destroy it (5.5 V max on any logic supply) |
| Boost converter (bench) | 1 | **MT3608** module set to 12.0 V | USB-powered bench testing only – does NOT live in the fan |
| Schottky diodes | 2 | **1N5819** (from diode kit) | Diode-OR the two 12 V sources (pack buck + bench boost) |
| USB-C charge port | 1 | USB-C female socket, wired to charger module input | −X side-wall charge input |
| Voltage divider (battery sense) | 2 | 100k + 24k resistors (¼ W) – on the carrier | Scales 16.8 V max → ~3.25 V for the Zero's ADC |
| Pull-up resistor (tach) | 1 | 10k to 3.3 V – on the carrier | Noctua tach is open-collector |
| M2 screws + M2 nuts | 4+4 | M2×6 | Faceplate (nuts sit in hex pockets in the housing) |
| M2 screws | 4 | M2×6 | Zero carrier to mezzanine bosses |
| M3 screws + heat-set inserts | 4+4 | M3×10 | Rear bay cover |
| Wiring, heat-shrink | - | 18 AWG power, 26 AWG signal (on hand) | - |
| 18650 slot charger | 1 | 2-slot standalone charger (bench) | Check/top-up cells before install – not part of the build |

## Pinout – Waveshare RP2040-Zero (from the board in the photo)
Left edge (top→bottom): **5V, GND, 3V3, GP29, GP28, GP27, GP26, GP15 … GP8**.
Right edge (top→bottom): **GP0 … GP7**. USB-C on top; BOOT/RESET buttons and a
WS2812 RGB LED (on **GP16**) in the middle. No mounting holes – the board
solders down via its castellated edges or friction-fits in a printed slot.

### Assigned pins for the fan
| Zero pin | Connects to | Notes |
|----------|-------------|-------|
| 5V | MP1584 #2 (5 V) output | MCU power in (from the 4S pack via the 5 V buck) |
| GND | Common ground | Star-ground the high-current paths at BMS P- |
| 3V3 (out) | Dial pot top, 10k tach pull-up | Onboard regulator output, logic only |
| GP15 | Fan header Pin 4 (Blue / PWM) | ~25 kHz PWM for the Noctua |
| GP14 | Fan header Pin 3 (Green / Tach) | Input + 10k pull-up to 3V3 (on carrier) |
| GP26 (ADC0) | Battery divider tap | 100k (BMS P+) / 24k (GND) → ≤3.25 V at full charge (on carrier) |
| GP13 | Charger module status pin | Charging detection |
| GP12 (ADC) | Dial pot wiper | Speed setting (pot ends: 3V3 / GND) |
| GP0 | OLED SDA | I2C0 SDA direct to the SSD1306 (3.3 V logic, no shifter) |
| GP1 | OLED SCL | I2C0 SCL direct to the SSD1306 |
| GP16 | Onboard WS2812 | Status LED – no extra parts needed |

**No pin for power on/off** – the dial's integrated switch breaks pack+ in
hardware (BMS P+ → switch → VCC bus), so OFF is a true hard cut and the Zero
simply boots at whatever speed the dial is set to. GP11 and the remaining
GPIOs (GP27/GP28 ADC1/ADC2, etc.) are spare for later (OLED, extra buttons,
second fan).

## Pinout – Standard 4-pin PC Fan (Noctua)
Looking at the connector (or cable end):
- Pin 1 (Black) : GND
- Pin 2 (Yellow): +12 V (Vcc)
- Pin 3 (Green) : Tach / RPM signal (open-collector, needs pull-up)
- Pin 4 (Blue)  : PWM control (25 kHz recommended, 3.3–5 V logic OK on most Noctua)

**Recommendation**: Solder a short pigtail with a female 4-pin header inside the housing. Fan plugs into it.

## High-Level Wiring Diagram (text)
Full visual version: **`electronics/wiring_diagram.svg`**. Text summary:
```
USB-C charge port ──► 4S charger module ──► BMS CHG+/CHG- (charge in, dial-OFF safe)
                          └─ status ──► Zero GP13

4×18650 (sled, series jumpers) ──► BMS B-/B1/B2/B3/B+ (balance taps)

BMS P+ ──► DIAL SWITCH (hard cut) ──► VCC bus ──► MP1584 #1 (12 V) ──► 1N5819 ──► fan header pin 2
         │                                        └─► MP1584 #2 (5 V) ──► Zero 5V pin
         └─► 100k/24k divider ──► Zero GP26   (unswitched P+, reads true pack voltage)

USB 5V (bench cable) ──► MT3608 (12 V, bench only) ──► 1N5819 ──┘ (diode-OR with pack buck)

BMS P- ──► GND rail ──► Zero GND, fan header pin 1, buck grounds, pot bottom, divider bottom

Zero GP15 ──► fan header pin 4 (PWM, ~25 kHz)
Zero GP14 ──► fan header pin 3 (tach) + 10k pull-up to 3V3 (on carrier)
Dial pot: ends to 3V3/GND, wiper ──► Zero GP12
Zero 3V3 ──► OLED VCC (check GND/VCC order on the silkscreen!)
Zero GND ──► OLED GND
Zero GP0 ──► OLED SDA, Zero GP1 ──► OLED SCL (direct, 3.3 V – no level shifter)
Zero GP16 ──► onboard WS2812 (status)
Zero USB-C ──► rear-panel cutout + collar (firmware/programming port)
```

**Do NOT use a boost module between the 4S pack and the fan.** The pack runs
14.8–16.8 V; a boost converter cannot step *down*, so a "3.7–18 V to 12 V"
boost set to 12 V would pass ~16 V straight to the fan. The MP1584 bucks are
the correct step-down parts. (MT3608 is for USB 5 V → 12 V bench power only.)

> **Review note (carried over):** an earlier revision of this doc routed the 4S
> pack straight to the Pico's VSYS pin. 4S Li-ion runs 14.8–16.8 V; the Pico
> family's logic supply tops out at 5.5 V. That path would have destroyed the
> MCU on first power-up. The dedicated 5 V buck above is the fix – never feed
> pack voltage directly into the Zero's 5V/3V3 pins.

## RP2040-Zero Responsibilities (locked in)
1. **Fan speed**: Read dial (GP12) → generate ~25 kHz PWM on GP15 for the Noctua. Full CCW = hard OFF via the dial switch (Zero unpowered); any CW position boots straight into that speed.
2. **Battery monitoring**: Read pack voltage via divider on GP26 (ADC0) → estimate %, enforce low-voltage cutoff, show status on the WS2812.
3. **Charging management**: Detect charger status on GP13 → indicate charging on the WS2812, optionally pause the fan while charging.
4. **USB-C ports**: the Zero's own USB-C is the programming/data port (rear cutout + collar); the panel-mount USB-C is charge-only via the charger module. Keep the two ports' roles separate.
5. Optional: tach feedback on GP14, small OLED on spare GPIOs (battery %, charging, speed).
6. Low-power sleep when the dial is at minimum (fan effectively off but pack connected).

## Power Budget & Runtime (4S + MP1584 bucks)
- Fan at regulated 12 V: ~3.6 W max
- Zero + BMS + LEDs + buck losses: ~0.6–1.2 W (no Wi-Fi radio to feed)
- Conservative system total at full speed: **≈ 4.5–5.5 W**

**Runtime estimate (4S1P, 3500 mAh cells, ~52 Wh nominal / ~41 Wh usable):**
- Full speed (~4.6 W) → **~9 hours**
- 70 % speed (~2.2 W) → **~18 hours**
- 50 % speed (~1.5 W) → **~28 hours**

Verdict: 4S1P covers the 12-hour target for anything short of full-blast-all-day.
Go 4S2P (8 cells, ~380 g) only if you want 12+ h guaranteed at max speed.
Cell weight: ~48 g each → 4S1P ≈ 190 g.
**Note:** the current bay + sled fit 4S1P. 4S2P would need a wider/taller bay
revision – keep the extra 4 cells as spares for now.

## Mechanical Layout (matches fan_housing.scad)
- **Bay floor**: printed 4×1 18650 sled (`models/battery_sled.scad`) at X -53..33, cells taped in.
- **Mezzanine plate** (on 4× M3 standoffs): 4S BMS (X -60..-15) + charger module (X -12..28) + Zero carrier (X 32..62).
  Carrier USB-C faces the rear cover cutout.
- **Under the mezzanine** (right of the sled): 2× MP1584 mini bucks (12 V + 5 V).
- **Rear**: screwed bay cover (4× M3 into heat-set inserts) with the Zero's USB-C cutout + strain-relief collar,
  plus the **OLED pod** (small bump-out housing the 0.96" SSD1306 screen, glass facing rear).
- **Charge port**: USB-C cutout on the -X base wall, wired to the charger module.
- **Side (+X base wall)**: dial pot through-hole + knob recess; printed knob (`models/knob.scad`).
- Fan wires route through the cable channel and pop up through the mezzanine notch.

### Fan mounting
Primary: 4× M3 screws through the 105 mm mounting holes (the model's top posts +
bottom pillars). Run them through the Noctua's rubber anti-vibration pads – that
is what the rubber is for, and it keeps the fan from walking under vibration.
The faceplate then acts as a light secondary clamp and grille. Sandwich-only
(faceplate pressure alone) is not recommended: 4× M2 in a 2.8 mm printed plate
cannot apply even clamping force and the fan could shift.

## Assembly Notes
- Set both MP1584 outputs **before** connecting anything: 12.0 V (fan) and 5.0 V (Zero).
- Set the MT3608 to 12.0 V on the bench (bench use only – not installed in the fan).
- Keep high-current 12 V paths short; star-ground at BMS P-.
- Solder the Zero to the carrier via castellated edges; keep BOOT/RESET reachable.
- The dial switch carries full pack current on its switch contacts – fine for a
  ~0.5 A load, no relay needed.
- Charging works with the dial OFF (charger feeds the BMS directly).
- Never run the pack buck and the MT3608 into the fan without the 1N5819 diodes.
- Label the 4-pin header; key it if possible.

## Remaining Decisions
- Whether to include a small LED light bar like the commercial example

Firmware skeleton for the RP2040-Zero (PWM + ADC dial + battery sense + I2C OLED)
is the next step once the hardware is in hand.
