# Electronics – Bill of Materials, Wiring & Notes
**Status: Designed for implementation. See `electronics/wiring_diagram.svg` for the visual schematic.**

**MCU: Waveshare RP2040-Zero** (the small board in the photo – RP2040, USB-C,
23.5 × 18 mm, castellated edges, onboard BOOT/RESET buttons and WS2812 RGB LED).
It replaces the earlier Pico 2 W plan. Note: the Zero has **no wireless**
(RP2040, no Wi-Fi/Bluetooth) – none of the responsibilities below need it, so
nothing is lost.

**Mounting (locked in):** the bare Zero solders via its castellated edges to a
perfboard **carrier (30×70 mm prototype PCB cut to ~30×25 mm)**. The carrier also holds the 100k/22k
battery divider (+100 nF), the 10k tach pull-up (+1 nF), and the 4-pin fan header. The carrier
screws to 4× M2 bosses on the bottom plate. The Zero's USB-C faces the cutout
in the base's rear wall (with a printed strain-relief collar) – it is the **firmware /
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
| Battery sled (printed) | 1 | `models/battery_sled.scad` | Holds the 4 cells. Series straps: **tabbed cells or spot-welded nickel strip, never solder to the cell** (the heat damages its seal and vent) |
| 4S BMS | 1 | **4S 40A *Balance* version** (the one labelled "4S 40A Balance", not the plain "4S 40A") | Balance + over-charge/discharge/current/short protection. The balance function keeps the 4 cells even – take the balance variant. 40 A is overkill for ~1 A load but harmless. **A BMS is NOT a charger (see next row).** Many of these boards are **common-port** (no C− pad): the charger then connects to P+/P− (see "Protection and sensing") |
| 4S charger module | 1 | **4S 2 A Type-C boost charger module** (ordered) – multi 2S/3S/4S selectable, Type-C 5 V in → 16.8 V CC/CV out | **VERIFY the module is set to 4S before first charge.** On 5 V it charges at ~0.8 A at best, about 5 h for a full pack, not 2 A (see "Charging rate"). Output → BMS CHG+/CHG- (P+/P− on a common-port BMS, on the pack side of the fuse); works with the dial OFF. **Measure its status pin before wiring GP13** |
| 0.96" OLED display | 1 | SSD1306 128×64 I2C module, 3.3–5 V, 3.3 V logic compatible | Battery %, charging, fan speed – small pod on the base's rear wall. **No level shifter needed** (unlike the 1602). **Check the silkscreen on arrival: modules ship with GND/VCC pin order random** |
| Buck converter (12 V) | 1 | **MP1584 mini** module set to **12.0 V** | Fan rail from the 4S pack (fan draws only 0.3 A – the mini is plenty) |
| Buck converter (5 V) | 1 | **MP1584 mini** module set to **5.0 V** | **Powers the RP2040-Zero via its 5V pin.** The Zero exposes no VSYS pin, and 14.8–16.8 V straight from the 4S pack would destroy it (5.5 V max on any logic supply) |
| Boost converter (bench) | 1 | **MT3608** module set to 12.0 V | USB-powered bench testing only – does NOT live in the fan |
| Schottky diodes | 2 | **1N5819** (from diode kit) | Diode-OR the two 12 V sources (pack buck + bench boost) |
| USB-C charge port | 1 | USB-C power socket that brings out **CC1/CC2** (6-pin or more), with **5.1k from each CC pin to GND** (some breakouts have them fitted), wired to charger module input | +X side wall (left, dial side) – moved from -X for truck access. A two-wire socket gets no power from a C-to-C charger |
| Voltage divider (battery sense) | 2 | 100k + 22k resistors (¼ W) + 100 nF – on the carrier | **On the switched VCC bus.** Scales 16.8 V max → 3.03 V for the Zero's ADC; calibrate once with `BATT_CAL` |
| Pull-up resistor (tach) | 1 | 10k to 3.3 V + 1 nF to GND – on the carrier | Noctua tach is open-collector; the 1 nF keeps PWM crosstalk out of the count |
| Fuse | 1 | 2 A fuse in an inline holder, or a 1.5 A PTC | At BMS P+, before the dial switch. The 40 A BMS alone would let a pinched wire burn |
| Schottky (Zero 5 V feed) | 0–1 | SS14 or a spare 1N5819 | Only if the Zero's 5V pin is tied straight to USB VBUS (see "Protection and sensing") |
| Status-pin protection | 0–1 | 10k + 1N4148 clamp to 3V3, or a PC817 optocoupler | Only if the charger's status pin measures above 3.3 V |
| M2 screws + heat-set inserts | 8+8 | M2×6 countersunk | Faceplates, front and rear |
| M2 screws | 4 | M2×6 | Zero carrier to the bottom-plate bosses |
| M3 screws + heat-set inserts | 8+8 | 4× M3×16 + 4× M3×8, countersunk | Head to base; bottom plate |
| M3 screws + nuts | 4+4 | M3×30 | Fan, through its corner holes into the head's rear ledges |
| M4 screws + heat-set inserts | 2+2 | M4×12 + 2 nylon washers | Bail pivots |
| Other fixings | – | M2 self-tapping: sled 2× M2×8 + lid 4× M2×6, OLED pod 2× M2×10 + module 4× M2×5; 4 stick-on feet | See `docs/DESIGN_OVERVIEW.md` |
| Wiring, heat-shrink | - | 18 AWG power, 26 AWG signal (on hand) | - |
| 18650 slot charger | 1 | 2-slot standalone charger (bench) | Check/top-up cells before install – not part of the build |
| Tactile button 6×6mm | 1 | Standard 6×6mm tactile switch (**to order** – not in the current parts order) | Screen on/off toggle on +X wall; wired to GP11 + GND |

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
| GP26 (ADC0) | Battery divider tap | 100k (switched VCC bus) / 22k (GND) + 100 nF → 3.03 V at full charge (on carrier) |
| GP13 | Charger module status pin | Charging detection. **Measure the pin first**: above 3.3 V it needs 10k + a clamp, or an optocoupler |
| GP27 (ADC1) | Dial pot wiper | Speed setting (pot ends: 3V3 / GND) |
| GP0 | OLED SDA | I2C0 SDA direct to the SSD1306 (3.3 V logic, no shifter) |
| GP1 | OLED SCL | I2C0 SCL direct to the SSD1306 |
| GP16 | Onboard WS2812 | Status LED – no extra parts needed |
| GP11 | Screen button (tactile, to GND) | Manual OLED on/off toggle (internal pull-up) |

**No pin for power on/off** – the dial's integrated switch breaks pack+ in
hardware (BMS P+ → fuse → switch → VCC bus), so OFF is a true hard cut and the Zero
simply boots at whatever speed the dial is set to.

**Screen sleep (for truck sleeping):** the OLED turns off automatically 15 s
after the dial stops moving (no light while you sleep). It wakes on dial
movement, on USB plug-in (charger status pin), or on the screen button.
The button toggles the screen manually. Remaining GPIOs (GP28/ADC2, etc.)
are spare for later (second fan, etc.).

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
USB-C charge port (5.1k on CC1/CC2) ──► 4S charger module ──► BMS CHG+/CHG- (charge in, dial-OFF safe)
                          │                (common-port BMS: P+/P-, on the pack side of the fuse)
                          └─ status ──► (measured; 10k + clamp if above 3.3 V) ──► Zero GP13

4×18650 (sled, series straps) ──► BMS B-/B1/B2/B3/B+ (balance taps)

BMS P+ ──► 2 A fuse ──► DIAL SWITCH (hard cut) ──► VCC bus ──► MP1584 #1 (12 V) ──► 1N5819 ──► fan header pin 2
                                                      ├─► MP1584 #2 (5 V) ──► [Schottky*] ──► Zero 5V pin
                                                      └─► 100k/22k divider (+100 nF) ──► Zero GP26
                                                          (switched: 0 V on GP26 while the Zero is off)

USB 5V (bench cable) ──► MT3608 (12 V, bench only) ──► 1N5819 ──► fan header pin 2 (diode-OR with pack buck)

* only if the Zero's 5V pin is tied straight to USB VBUS

BMS P- ──► GND rail ──► Zero GND, fan header pin 1, buck grounds, pot bottom, divider bottom

Zero GP15 ──► fan header pin 4 (PWM, ~25 kHz)
Zero GP14 ──► fan header pin 3 (tach) + 10k pull-up to 3V3 (on carrier)
Dial pot: ends to 3V3/GND, wiper ──► Zero GP27
Zero 3V3 ──► OLED VCC (check GND/VCC order on the silkscreen!)
Zero GND ──► OLED GND
Zero GP0 ──► OLED SDA, Zero GP1 ──► OLED SCL (direct, 3.3 V – no level shifter)
Zero GP16 ──► onboard WS2812 (status)
Zero GP11 ──► tactile button ──► GND (screen toggle, internal pull-up)
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

## Protection and sensing
Added after the 2026-10-18 review. None of it changes the architecture; each
item stops a part from being damaged or the pack from being drained.

**Fuse.** A 2 A fuse (or a 1.5 A PTC) right at BMS P+, before the dial switch.
The load is under 0.5 A; without the fuse, a pinched 18 AWG wire in a vibrating
cab carries current until the 40 A BMS trips, far beyond what the wire, the
dial switch or an MP1584 survives. Land the charger's + on the pack side of the
fuse, so charge current never runs through it.

**Battery sense (GP26).** The divider hangs on the **switched** VCC bus. On
unswitched P+ it fed up to 3.25 V into GP26 while the Zero was off, through the
pin's protection diode into the dead 3V3 rail: outside the RP2040's ratings, and
it half-powers the board. The switch drops millivolts, so the reading is still
the pack voltage. 100k/22k puts a full 16.8 V pack at 3.03 V, which leaves room
under the 3.3 V reference. The ADC measures against the Zero's 3V3 rail, and
±2 % on that rail is ±0.34 V at the pack, so calibrate once: compare the screen
with a multimeter on the pack and set `BATT_CAL` in `firmware/main.py` to
multimeter ÷ screen. 100 nF from GP26 to GND filters the noise.

**Charger STAT (GP13).** Many 4S Type-C boost modules have no logic-level status
pin; the "status" is their LED, and an LED node can sit at 5 V or more. GP13
tolerates 3.3 V. Before connecting it:
1. With GP13 unconnected, charge a real pack from USB and measure the status
   pin to GND while charging, then again when full.
2. If it ever exceeds 3.3 V, connect it through 10k with a clamp diode
   (1N4148, cathode to 3V3), or use an optocoupler across the LED.
3. Set `CHARGER_ACTIVE_LOW` in `firmware/main.py` from what you measured.

**The Zero's 5V pin and USB.** If that pin is tied straight to USB VBUS (check
Waveshare's schematic), plugging into the programming port with the dial on
connects the MP1584's 5 V to the laptop's. Put a Schottky (SS14) between the
buck and the 5V pin, or only program with the dial off. The Schottky costs
~0.3 V, which the Zero's 3.3 V regulator absorbs.

**Charging rate.** 2 A into a 16.8 V pack is about 34 W; a 5 V USB source
gives at most 15 W (3 A). On 5 V the module charges at roughly 0.8 A, so a full
charge of 3.5 Ah cells takes about 5 hours (longer from a 2 A source). Only a
module that negotiates USB PD at a higher voltage can do better, and this one
is listed as 5 V in. The 5.1k CC pull-downs matter twice: without them a C-to-C
charger supplies nothing, and with them a PD charger stays at 5 V.

**Charging while the fan runs.** The charger and the fan share P+. The fan's
load keeps the CC/CV charger from reaching its termination current, so the
cells sit at 4.2 V and STAT reads "charging" all night. Harmless now and then;
for a routine overnight top-up, click the dial off. Don't charge in a hot cab:
the 35E charges at 0–45 °C and the module has no temperature sensing.

**BMS.** Many 40 A "balance" boards are common-port (no C− pad): the charger
connects to P+ and P−. Their over-discharge cutoff (about 2.5–2.7 V per cell)
sits below the firmware's 3.3 V per cell, so the firmware cuts first. Balancing
is tens of mA and only near 4.2 V per cell: it keeps matched cells matched but
won't rescue a mismatched pack, so check all four cells read within 0.02 V of
each other before building it.

**Fan PWM drive (optional).** GP15 drives the Noctua's PWM pin push-pull at
3.3 V, while the 4-wire fan spec expects an open-drain output against the fan's
own pull-up (up to 5.25 V). It works with most fans. To stay in spec, drive a
small N-MOSFET (2N7002: source to GND, drain to the PWM pin, gate to GP15
with a 100k pull-down). It inverts the signal, so the firmware's duty must be
inverted too (`65535 -` in the `pwm.duty_u16` line of `main.py`).

**After a low-battery cutoff, click the dial off.** The fan stops, but the Zero
keeps drawing about 15 mA, and a fan that doesn't stop at 0 % PWM keeps
turning slowly, until the BMS disconnects at about 10–11 V.

## RP2040-Zero Responsibilities (locked in)
1. **Fan speed**: Read dial (GP27) → generate ~25 kHz PWM on GP15 for the Noctua. Full CCW = hard OFF via the dial switch (Zero unpowered); any CW position boots straight into that speed.
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
**Note:** the base and sled fit 4S1P. 4S2P would need a taller base (a second
layer of cells where the BMS now sits) – keep the extra 4 cells as spares for now.

## Mechanical Layout (matches fan_housing.scad)
Since 2026-10-18 everything lives in the **base** under the fan, which runs 64 mm
back behind the head; nothing sits behind the fan. Positions are X across
(+X = left when facing the fan) and Z front to back, in mm; `models/assembly.scad`
with `view = "base_layout"` shows them from above.
- **Sled** (`models/battery_sled.scad`) on the bottom plate against the -X wall
  (X -67..17, Z 11..88): 4 cells side by side, axes front to back, lid screwed on.
- **On the sled's lid**: the 4S BMS (46 × 60 footprint at X -64..-18) and the 12 V buck.
  Measure the BMS on arrival: up to about 50 × 75 fits the lid beside the buck.
- **On the plate, +X side**: the charger module (X 19..44, Z 4..39) and the 5 V buck
  (Z 42..64), on foam tape; the Zero carrier on 4 M2 bosses (X 25..50, Z 67..97),
  its USB-C at the rear wall.
- **+X wall**: dial pot (Z 24; knob recess cut from the outside), USB-C charge port
  (Z 46), screen button (Z 62), all cut through to the inside.
- **Rear wall**: the Zero's USB-C cutout + strain-relief collar, and the **OLED pod**:
  a separate part on 2 screws, glass facing rear, which can be reprinted to fit the
  real module (`oled_*` parameters).
- **Fan cable**: down through the slot in the head's floor and the base's roof
  (X 14..26), to the header on the carrier.
- Bottom plate: 4× M3 countersunk into inserts; vent slots under the charger.

### Fan mounting
4× M3 × 30 from the front, through the fan's corner holes (105 mm pattern), into M3
nuts sitting in pockets on the rear faces of the head's four corner ledges. The nuts
are behind the ledges, so the bolts clamp the fan against them. Run the bolts through
the Noctua's rubber anti-vibration pads if yours has them. The grilles front and
rear are separate parts and don't hold the fan.

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
- Fuse at BMS P+ before anything else is connected; charger + on the pack side of it.
- Measure the charger's status pin before it goes anywhere near GP13 (above).
- Use stranded wire, tie it down near every joint, and put a dab of glue on each
  joint at the Zero's castellated pads: 26 AWG joints fatigue first in a truck.
- Solder the OLED's wires; a pushed-on header works loose.

## Verify on arrival (electrical)
- **Charger module**: set to 4S; its input spec (5 V only, or USB PD); its
  status pin's voltage while charging and when full.
- **USB-C socket**: it brings out CC1/CC2, and has 5.1k pull-downs (fit them if not).
- **BMS**: the balance version; common-port or a separate C− charge pad.
- **Cells**: all four within 0.02 V of each other; whether they came with tabs.
- **RP2040-Zero**: whether its 5V pin is tied straight to USB VBUS (decides the Schottky).
- **MP1584 bucks**: set to 12.0 V and 5.0 V before anything is connected.
- **Fan**: whether it starts at low duty (`MIN_DUTY`), whether it stops at 0 %,
  and its PWM pin's voltage when powered with the pin unconnected.
- **WH138**: the switch's current rating (the load is under 0.5 A).

## Remaining Decisions
- Whether to include a small LED light bar like the commercial example

Firmware for the RP2040-Zero (PWM + ADC dial + battery sense + I2C OLED) is in
`firmware/`; see its README for the bench test and calibration.
