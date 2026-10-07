# Electronics – Bill of Materials, Wiring & Notes
**Status: Documented for later implementation. Mechanical model comes first.**

## Core Components
| Item | Qty | Notes / Example Part | Purpose |
|------|-----|----------------------|---------|
| Raspberry Pi Pico 2 W | 1 | Official or clone with headers | Brain: PWM speed control, on/off logic, battery monitoring, USB-C status if wired |
| Noctua NF-F12 iPPC-3000 PWM | 1 | Amazon link provided | Main 120 mm fan (12 V, max 3.6 W) |
| 4-pin PC Fan Header / Connector | 1–2 | Molex KK 2.54 mm 4-pin or standard PC fan socket + plug | Allows easy fan unplug/replacement. One on board, mating plug on fan cable or pigtail |
| Li-ion / LiPo Battery Pack | 1 | TBD size (recommend start with 2S or 3S 18650 or 5000–10000 mAh pouch) | Power source |
| Battery Management System (BMS) | 1 | Matching series count (e.g. 2S/3S protection board) | Over-charge, over-discharge, over-current, short protection |
| USB-C Charging Module | 1 | TP4056 (1S) or better multi-cell charger / IP2326 / dedicated PD module | Charge the pack via USB-C |
| Boost Converter (if needed) | 1 | MT3608 or better synchronous boost (set to 12.0 V) | Step battery voltage up to clean 12 V for the fan. Not needed if using 3S (11.1 V nominal) and fan tolerates it |
| Rotary Potentiometer or Switch | 1 | 10k linear pot, or 3–4 position rotary switch | User speed control (read by Pico ADC or GPIO) |
| Power Switch (optional) | 1 | Small SPDT or latching | Hard power cut if desired (Pico can also soft-switch) |
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

## High-Level Wiring Diagram (text)
```
USB-C Port ──► Charger Module ──► BMS ──► Battery Pack
                              │
                              └──► (optional fuel gauge / voltage sense to Pico ADC)

Battery Pack (+) ──► Boost Converter (to 12 V) ──► Fan Pin 2 (Yellow / Vcc)
                 │
                 └──► Pico VSYS / VBUS (via diode or direct depending on design)

Battery Pack (-) ──► common GND

Pico GPIO (PWM capable, e.g. GP0) ──► Fan Pin 4 (Blue / PWM)
Pico GPIO (optional) ──► Fan Pin 3 (Green / Tach) with 10k pull-up to 3.3 V

Pico ADC ──► Voltage divider from Battery Pack (+)
Pico ADC or GPIOs ──► Rotary pot / switch
Pico 3.3 V / GND ──► pot, LEDs, display

Optional: Pico controls a MOSFET on the 12 V line for hard on/off.
```

## Pico Responsibilities (to implement later)
1. Read speed control (pot or switch) → map to PWM duty cycle (0–100%).
2. Generate ~25 kHz PWM on the fan control pin.
3. Monitor battery voltage via divider → estimate % and enforce low-voltage cutoff (disable PWM / MOSFET).
4. Optional: read tach for actual RPM feedback or stall detection.
5. Optional: drive status LED or OLED (battery %, charging if USB detected, current speed).
6. Soft power management / sleep when off.
7. USB-C: if using Pico’s own USB, it can detect VBUS; otherwise monitor charger status pin.

## Power Budget Reminder (at 100% fan)
- Fan: 3.6 W max
- Boost losses + Pico + LEDs: ~0.8–1.5 W
- Total system ≈ 4.5–5.5 W → size battery accordingly (see previous runtime table)

## Assembly Notes for Later
- Keep high-current 12 V paths short and thick.
- Separate signal GND from high-current paths where practical.
- Mount Pico and modules on a small custom PCB or perfboard that slides into the electronics bay.
- Provide strain relief for the USB-C cable and fan pigtail.
- Label the 4-pin connector clearly (or key it).

## Open Questions / Decisions Needed
- Exact battery chemistry & capacity (affects bay size and whether boost is required)
- Potentiometer vs multi-position switch vs capacitive buttons
- Include a small LED light bar like the commercial example?
- OLED display or just LEDs?
- Hard power switch in addition to soft control?

Once the mechanical model is solid and battery size is chosen, we can expand this into a full schematic (KiCad) and firmware skeleton.
