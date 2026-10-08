# Electronics – Bill of Materials, Wiring & Notes
**Status: Documented for later implementation. Mechanical model comes first.**

## Core Components
| Item | Qty | Notes / Example Part | Purpose |
|------|-----|----------------------|---------|
| Raspberry Pi Pico 2 W | 1 | Official or clone with headers | Brain: PWM speed control, on/off logic, battery monitoring, USB-C status if wired |
| Noctua NF-F12 iPPC-3000 PWM | 1 | Amazon link provided | Main 120 mm fan (12 V, max 3.6 W) |
| 4-pin PC Fan Header / Connector | 1–2 | Molex KK 2.54 mm 4-pin or standard PC fan socket + plug | Allows easy fan unplug/replacement. One on board, mating plug on fan cable or pigtail |
| Li-ion Battery Pack | 1 | **4 × 18650 in 4S1P** (nominal 14.8 V / full charge 16.8 V). Cells from the linked AliExpress listing or equivalent quality 3000–3500 mAh cells | Power source |
| Battery Management System (BMS) | 1 | **4S BMS** with cell balancing + over-charge / over-discharge / over-current / short protection (10–20 A common boards are fine) | Essential for safe 4S operation |
| USB-C Charging Module | 1 | 4S-capable charger board or USB-C PD trigger + converter that can deliver 16.8 V CC/CV | Charge the pack via USB-C |
| Buck Converter | 1 | Synchronous buck module set to **12.0 V** (e.g. MP1584 / XL4015 / better synchronous modules) | Required – keeps the Noctua fan inside its official 12 V rating |
| Rotary Potentiometer or Switch | 1 | 10k linear pot, or 3–4 position rotary switch | User speed control (read by Pico ADC or GPIO) |
| Power Switch | 1 | Soft control via Pico + optional physical latching/SPDT for hard cut | Pico manages soft power; physical switch recommended for complete isolation |
| USB-C Panel Mount or Breakout | 1 | Panel-mount USB-C or PCB module | External charge / data port |
| Status LEDs / Display (optional) | 1–3 | Single LED or small SSD1306 OLED | Battery %, charging, fan speed indication |
| Level shifter / MOSFET (optional) | 1 | If 3.3 V PWM needs buffering, or for high-side fan switch | Clean 12 V switching / PWM |
| Wiring, heat-shrink, connectors | - | 26–28 AWG for signals, 22–24 AWG for power | - |
| Heat-set inserts (M2 + M3) | 8+ | Brass | Clean screw threads in printed parts |

## Pinout – Standard 4-pin PC Fan (Noctua)
Looking at the connector (or cable end):
- Pin 1 (Black) : GND
- Pin 2 (Yellow): +12 V (Vcc)
- Pin 3 (Green) : Tach / RPM signal (open-collector, needs pull-up)
- Pin 4 (Blue)  : PWM control (25 kHz recommended, 3.3–5 V logic OK on most Noctua)

**Recommendation**: Solder a short pigtail with a female 4-pin header inside the housing. Fan plugs into it. This matches the “wire in a 4pin fan connector” request.

## High-Level Wiring Diagram (text) – Final 4S + 12 V Buck
```
USB-C Port ──► 4S Charger Module ──► 4S BMS ──► 4×18650 Pack (14.8 V nominal)
                │                    │
                │                    └──► voltage divider → Pico ADC (battery %)
                │
                └──► charger status pin → Pico GPIO (charging detection)

4S Pack (+) ──► Buck Converter (fixed 12.0 V) ──► Fan Pin 2 (Yellow / Vcc)
            │                                 └──► (optional) high-side MOSFET controlled by Pico
            │
            └──► Pico VSYS (via diode or the Pico’s own regulator path)

4S Pack (-) ──► common GND

Pico GPIO (PWM capable) ──► Fan Pin 4 (Blue / PWM)
Pico GPIO (optional)    ──► Fan Pin 3 (Green / Tach) + 10k pull-up to 3.3 V

Pico ADC / GPIOs ──► Rotary pot or speed switch
Pico GPIOs       ──► Power button / soft-power control
Pico 3.3 V / GND ──► pot, status LEDs / small OLED
```

## Pico Responsibilities (locked in)
1. **Fan speed**: Read pot/switch → generate ~25 kHz PWM for the Noctua.
2. **Power management**: Soft on/off (and optional hard cut via MOSFET). Respond to physical power switch.
3. **Battery monitoring**: Read pack voltage via divider → estimate %, enforce low-voltage cutoff, show status.
4. **Charging management**: Detect USB-C / charger status pin → indicate charging, optionally adjust behaviour while charging.
5. **USB-C port**: Monitor VBUS presence (via Pico’s own USB or external sense).
6. Optional: tach feedback, status LEDs or small OLED (battery %, charging, speed).
7. Low-power sleep when the fan is off.

## Power Budget & Runtime (4S + 12 V Buck)
- Fan at regulated 12 V: ~3.6 W max
- Pico + BMS + LEDs + buck losses: ~0.8–1.5 W
- Conservative system total at full speed: **≈ 5–6 W**

**Runtime estimate (4S1P, 3200–3500 mAh cells):**
- Pack energy ≈ 47–52 Wh nominal
- Usable after BMS cut-off & efficiency ≈ 38–43 Wh
- At 5.5 W system load → **7–8 hours** at full speed
- At medium/low speed easily 12–20+ hours

(Upgrade to 4S2P later if you want even longer runtime.)

## Assembly Notes for Later
- Keep high-current 12 V paths short and thick.
- Separate signal GND from high-current paths where practical.
- Mount Pico and modules on a small custom PCB or perfboard that slides into the electronics bay.
- Provide strain relief for the USB-C cable and fan pigtail.
- Label the 4-pin connector clearly (or key it).

## Remaining Decisions
- Exact cell capacity / brand (affects runtime)
- Speed control: continuous potentiometer vs 3–4 position rotary switch
- Status indication: simple LEDs vs small OLED
- Physical power switch style (latching, momentary for soft-power, or both)
- Whether to include a small LED light bar like the commercial example

Once the mechanical model is solid we can expand this into a full schematic (KiCad) and firmware skeleton.
