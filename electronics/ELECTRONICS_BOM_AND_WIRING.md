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
| Buck Converter (strongly recommended) | 1 | Synchronous buck module set to **12.0 V** | Keeps the Noctua fan inside its official 12 V rating (max 13.2 V). Omit only if you accept running the fan at 14.8–16.8 V |
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

## High-Level Wiring Diagram (text) – 4S version
```
USB-C Port ──► 4S Charger Module ──► 4S BMS ──► 4×18650 Pack (14.8 V nominal)
                                      │
                                      └──► voltage divider → Pico ADC (battery %)

4S Pack (+) ──► Buck Converter (set to 12.0 V) ──► Fan Pin 2 (Yellow / Vcc)
            │
            └──► (optional) Pico VSYS via suitable regulator / diode

4S Pack (-) ──► common GND

Pico GPIO (PWM, e.g. GP0) ──► Fan Pin 4 (Blue / PWM)
Pico GPIO (optional)      ──► Fan Pin 3 (Green / Tach) + 10k pull-up to 3.3 V

Pico ADC or GPIOs ──► Rotary pot / speed switch
Pico 3.3 V / GND  ──► pot, status LEDs / OLED

Optional hard on/off: Pico controls a logic-level MOSFET on the 12 V side.
```

**Note**: If you skip the buck and feed the fan directly from the 4S pack, just connect Pack (+) → Fan Yellow. The fan will run faster/louder and outside official voltage limits.

## Pico Responsibilities (to implement later)
1. Read speed control (pot or switch) → map to PWM duty cycle (0–100%).
2. Generate ~25 kHz PWM on the fan control pin.
3. Monitor battery voltage via divider → estimate % and enforce low-voltage cutoff (disable PWM / MOSFET).
4. Optional: read tach for actual RPM feedback or stall detection.
5. Optional: drive status LED or OLED (battery %, charging if USB detected, current speed).
6. Soft power management / sleep when off.
7. USB-C: if using Pico’s own USB, it can detect VBUS; otherwise monitor charger status pin.

## Power Budget & Runtime (4S 18650)
- Fan at 12 V (via buck): still ~3.6 W max
- Fan fed directly from 4S (14.8–16.8 V): higher power draw and speed (expect 4.5–6 W+)
- Pico + BMS + LEDs + buck losses: ~0.8–1.5 W
- Conservative system total at full speed with buck: **≈ 5–6 W**

**Runtime estimate (4S1P, 3200–3500 mAh cells):**
- Pack energy ≈ 47–52 Wh nominal
- Usable after BMS cut-off & efficiency ≈ 38–43 Wh
- At 5.5 W system load → **7–8 hours** at full speed
- At medium speed easily 12–18+ hours

(Upgrade to 4S2P later if you want even longer runtime.)

## Assembly Notes for Later
- Keep high-current paths short and thick.
- Separate signal GND from high-current paths where practical.
- Mount Pico and modules on a small custom PCB or perfboard that slides into the electronics bay.
- Provide strain relief for the USB-C cable and fan pigtail.
- Label the 4-pin connector clearly (or key it).

## Open Questions / Decisions Needed
- Exact cell capacity / brand (affects runtime)
- Run fan direct from 4S or use the recommended 12 V buck?
- Potentiometer vs multi-position switch
- Include a small LED light bar like the commercial example?
- OLED display or just LEDs?
- Hard power switch in addition to soft control?

Once the mechanical model is solid we can expand this into a full schematic (KiCad) and firmware skeleton.
