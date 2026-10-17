# Electronics – Bill of Materials, Wiring & Notes
**Status: Documented for later implementation. Mechanical model comes first.**

**MCU: Waveshare RP2040-Zero** (the small board in the photo – RP2040, USB-C,
23.5 × 18 mm, castellated edges, onboard BOOT/RESET buttons and WS2812 RGB LED).
It replaces the earlier Pico 2 W plan. Note: the Zero has **no wireless**
(RP2040, no Wi-Fi/Bluetooth) – none of the responsibilities below need it, so
nothing is lost.

## Core Components
| Item | Qty | Notes / Example Part | Purpose |
|------|-----|----------------------|---------|
| Waveshare RP2040-Zero | 1 | RP2040, USB-C, 23.5 × 18 mm | Brain: PWM speed control, on/off logic, battery monitoring, status LED |
| Noctua NF-F12 iPPC-3000 PWM | 1 | Amazon link provided | Main 120 mm fan (12 V, max 3.6 W) |
| 4-pin PC Fan Header / Connector | 1–2 | Molex KK 2.54 mm 4-pin or standard PC fan socket + plug | Allows easy fan unplug/replacement. One on board, mating plug on fan cable or pigtail |
| Li-ion Battery Pack | 1 | **4 × 18650 in 4S1P** (nominal 14.8 V / full charge 16.8 V). Cells from the linked AliExpress listing or equivalent quality 3000–3500 mAh cells | Power source |
| Battery Management System (BMS) | 1 | **4S BMS** with cell balancing + over-charge / over-discharge / over-current / short protection (10–20 A common boards are fine) | Essential for safe 4S operation |
| USB-C Charging Module | 1 | 4S-capable charger board or USB-C PD trigger + converter that can deliver 16.8 V CC/CV | Charge the pack via USB-C (panel-mount port) |
| Buck Converter (12 V) | 1 | Synchronous buck module set to **12.0 V** (e.g. MP1584 / XL4015 / better synchronous modules) | Required – keeps the Noctua fan inside its official 12 V rating |
| Buck Converter (5 V) | 1 | Small buck module set to **5.0 V** (e.g. MP1584 mini, ~1–3 A) | **Powers the RP2040-Zero via its 5V pin.** The Zero exposes no VSYS pin, and 14.8–16.8 V straight from the 4S pack would destroy it (5.5 V max on any logic supply) |
| Rotary Potentiometer or Switch | 1 | 10k linear pot, or 3–4 position rotary switch | User speed control (read by Zero ADC or GPIO) |
| Power Switch | 1 | Soft control via Zero + optional physical latching/SPDT for hard cut | Zero manages soft power; physical switch recommended for complete isolation |
| USB-C Panel Mount or Breakout | 1 | Panel-mount USB-C or PCB module | External charge port (separate from the Zero's own USB-C, which is the programming port) |
| Status indication | — | **Onboard WS2812 RGB LED (GP16)** covers basic status for free | Battery %, charging, fan speed indication. Small SSD1306 OLED still optional for more detail |
| Level shifter / MOSFET (optional) | 1 | If 3.3 V PWM needs buffering, or for high-side fan switch | Clean 12 V switching / PWM |
| Voltage divider (battery sense) | 2 | 100k + 24k resistors (¼ W fine) | Scales 16.8 V max → ~3.25 V for the Zero's ADC |
| Pull-up resistor (tach) | 1 | 10k to 3.3 V | Noctua tach is open-collector |
| Wiring, heat-shrink, connectors | - | 26–28 AWG for signals, 22–24 AWG for power | - |
| Heat-set inserts (M2 + M3) | 8+ | Brass | Clean screw threads in printed parts |

## Pinout – Waveshare RP2040-Zero (from the board in the photo)
Left edge (top→bottom): **5V, GND, 3V3, GP29, GP28, GP27, GP26, GP15 … GP8**.
Right edge (top→bottom): **GP0 … GP7**. USB-C on top; BOOT/RESET buttons and a
WS2812 RGB LED (on **GP16**) in the middle. No mounting holes – the board
solders down via its castellated edges or friction-fits in a printed slot.

### Assigned pins for the fan
| Zero pin | Connects to | Notes |
|----------|-------------|-------|
| 5V | 5 V buck output | MCU power in (from the 4S pack via the 5 V buck) |
| GND | Common ground | Star-ground the high-current paths here |
| 3V3 (out) | Pot high side, 10k tach pull-up | Onboard regulator output, logic only |
| GP15 | Fan Pin 4 (Blue / PWM) | ~25 kHz PWM for the Noctua |
| GP14 | Fan Pin 3 (Green / Tach) | Input + 10k pull-up to 3V3 |
| GP26 (ADC0) | Battery divider tap | 100k (pack +) / 24k (GND) → ≤3.25 V at full charge |
| GP13 | Charger status pin | Charging detection (from charger module) |
| GP12 | Rotary pot wiper (or speed switch) | ADC or GPIO per chosen control |
| GP11 | Power button (momentary) | Soft-power control |
| GP16 | Onboard WS2812 | Status LED – no extra parts needed |

GP27/GP28 (ADC1/ADC2) and the remaining GPIOs are spare for later (OLED, extra
buttons, second fan, etc.).

## Pinout – Standard 4-pin PC Fan (Noctua)
Looking at the connector (or cable end):
- Pin 1 (Black) : GND
- Pin 2 (Yellow): +12 V (Vcc)
- Pin 3 (Green) : Tach / RPM signal (open-collector, needs pull-up)
- Pin 4 (Blue)  : PWM control (25 kHz recommended, 3.3–5 V logic OK on most Noctua)

**Recommendation**: Solder a short pigtail with a female 4-pin header inside the housing. Fan plugs into it.

## High-Level Wiring Diagram (text) – Final 4S + 12 V Buck + 5 V MCU Rail
```
USB-C Port (charger) ──► 4S Charger Module ──► 4S BMS ──► 4×18650 Pack (14.8 V nominal)
                          │                    │
                          │                    └──► 100k/24k divider → Zero GP26 (ADC0, battery %)
                          │
                          └──► charger status pin → Zero GP13 (charging detection)

4S Pack (+) ──► Buck Converter (fixed 12.0 V) ──► Fan Pin 2 (Yellow / Vcc)
                                          └────► (optional) high-side MOSFET controlled by Zero

4S Pack (+) ──► Buck Converter (fixed 5.0 V) ──► Zero 5V pin (MCU power)

4S Pack (-) ──► common GND ──► Zero GND, fan Pin 1, buck grounds

Zero GP15 (PWM) ──► Fan Pin 4 (Blue / PWM)          (~25 kHz)
Zero GP14       ──► Fan Pin 3 (Green / Tach) + 10k pull-up to 3V3

Zero GP12 / ADC ──► Rotary pot or speed switch
Zero GP11       ──► Power button (momentary)
Zero 3V3 / GND  ──► pot high side, pull-ups, optional OLED
Zero GP16       ──► onboard WS2812 (status, no wiring)
Zero USB-C      ──► programming port (expose via rear cutout for firmware updates)
```

> **Review note (carried over):** an earlier revision of this doc routed the 4S
> pack straight to the Pico's VSYS pin. 4S Li-ion runs 14.8–16.8 V; the Pico
> family's logic supply tops out at 5.5 V. That path would have destroyed the
> MCU on first power-up. The dedicated 5 V buck above is the fix – never feed
> pack voltage directly into the Zero's 5V/3V3 pins.

## RP2040-Zero Responsibilities (locked in)
1. **Fan speed**: Read pot/switch → generate ~25 kHz PWM on GP15 for the Noctua.
2. **Power management**: Soft on/off (and optional hard cut via MOSFET). Respond to physical power switch on GP11.
3. **Battery monitoring**: Read pack voltage via divider on GP26 (ADC0) → estimate %, enforce low-voltage cutoff, show status on the WS2812.
4. **Charging management**: Detect charger status on GP13 → indicate charging on the WS2812, optionally adjust behaviour while charging.
5. **USB-C ports**: the Zero's own USB-C is the programming/data port (VBUS sense if needed); the panel-mount USB-C is charge-only via the charger module. Keep the two ports' roles separate in the housing.
6. Optional: tach feedback on GP14, small OLED on spare GPIOs (battery %, charging, speed).
7. Low-power sleep when the fan is off.

## Power Budget & Runtime (4S + 12 V Buck)
- Fan at regulated 12 V: ~3.6 W max
- Zero + BMS + LEDs + buck losses: ~0.6–1.2 W (no Wi-Fi radio to feed, unlike the Pico 2 W plan)
- Conservative system total at full speed: **≈ 4.5–5.5 W**

**Runtime estimate (4S1P, 3200–3500 mAh cells):**
- Pack energy ≈ 47–52 Wh nominal
- Usable after BMS cut-off & efficiency ≈ 38–43 Wh
- At ~5 W system load → **8–9 hours** at full speed
- At medium/low speed easily 12–20+ hours

(Upgrade to 4S2P later if you want even longer runtime.)

## Assembly Notes for Later
- Keep high-current 12 V paths short and thick.
- Separate signal GND from high-current paths where practical.
- The Zero has no mounting holes: solder it via castellated edges to a small
  carrier/perfboard, or design a friction-fit slot in the electronics bay. The
  carrier board slides into the bay.
- Leave the Zero's BOOT/RESET buttons reachable (or expose them) for firmware updates.
- Route the Zero's USB-C to the rear-panel cutout so firmware can be flashed without opening the case.
- Provide strain relief for the USB-C cable and fan pigtail.
- Label the 4-pin connector clearly (or key it).

## Remaining Decisions
- Exact cell capacity / brand (affects runtime)
- Speed control: continuous potentiometer vs 3–4 position rotary switch
- Status indication: onboard WS2812 is enough, or add the small OLED
- Physical power switch style (latching, momentary for soft-power, or both)
- Whether to include a small LED light bar like the commercial example

Once the mechanical model is solid we can expand this into a full schematic (KiCad) and a firmware skeleton for the RP2040-Zero.
