# Electronics – Bill of Materials, Wiring & Notes
**Status: Designed for implementation. See `electronics/wiring_diagram.svg` for the visual schematic.**

**MCU: Waveshare RP2040-Zero** (the small board in the photo – RP2040, USB-C,
23.5 × 18 mm, castellated edges, onboard BOOT/RESET buttons and WS2812 RGB LED).
It replaces the earlier Pico 2 W plan. Note: the Zero has **no wireless**
(RP2040, no Wi-Fi/Bluetooth) – none of the responsibilities below need it, so
nothing is lost.

**Mounting (locked in):** the bare Zero solders via its castellated edges to the
**carrier + PSU board** (`electronics/pcb/`: a custom 2-layer PCB, 40.5 × 93 mm, with a notch
round the dial pot). The board also carries both bucks (12 V for the fan, 5 V for the Zero), the
12 V diode-OR, the 100k/22k battery divider (+100 nF), the 10k tach pull-up (+1 nF), the 4-pin fan
header and a connector for every lead. It screws to 8× M2 bosses on the bottom plate. The Zero's
USB-C faces the cutout in the base's rear wall (with a printed strain-relief collar) – it is the
**firmware / programming port**, not the charger. (Friction-fit mounting was rejected:
vibration would walk the Zero loose and stress the USB-C.) The board's own parts list,
assembly and ordering are in `electronics/pcb/README.md`.

## Core Components
| Item | Qty | Notes / Example Part | Purpose |
|------|-----|----------------------|---------|
| Waveshare RP2040-Zero | 1 | RP2040, USB-C, 23.5 × 18 mm | Brain: PWM speed control, battery monitoring, status LED |
| Carrier + PSU board | 1 | Custom 2-layer PCB, 40.5 × 93 mm (`electronics/pcb/`); its README has the parts list with LCSC numbers | Holds the Zero (castellated solder), both bucks, the diode-OR, the divider, the tach pull-up, the status-pin parts and the connectors J1–J7 |
| Noctua NF-F12 iPPC-3000 PWM | 1 | Amazon link provided | Main 120 mm fan (12 V, max 3.6 W) |
| 4-pin PC Fan Header | 1 | Molex 47053-1000, on the board (J2) | Plug-and-play fan connection: the fan's own plug goes straight in (a 4-pin extension only if its lead is short) |
| Dial switch (speed + power) | 1 | **WH138 B10K linear with ON/OFF switch** (confirmed) – 24 mm body, 6 mm × 13.5 mm shaft, aluminum knob 21×17 mm included ×2; printed knob (`models/knob.scad`) is backup only | **The single user control.** Full CCW clicks OFF (hard power cut); CW sweeps slowest → fastest. Pot element is 0.2 W – fine, the wiper only drives the ADC (µA); the switch contacts carry ~0.5 A pack current |
| 18650 cells | 4 (or 8) | Samsung INR18650-35E 3500 mAh flat-top, unprotected | 4S1P pack (~52 Wh). 8 cells = 4 for the pack + 4 spares (4S2P does not fit the current bay – see below) |
| Battery sled (printed) | 1 | `models/battery_sled.scad` | Holds the 4 cells. Series straps: **tabbed cells or spot-welded nickel strip, never solder to the cell** (the heat damages its seal and vent) |
| 4S BMS | 1 | **4S 40A *Balance* version** (the one labelled "4S 40A Balance", not the plain "4S 40A") | Balance + over-charge/discharge/current/short protection. The balance function keeps the 4 cells even – take the balance variant. 40 A is overkill for ~1 A load but harmless. **A BMS is NOT a charger (see next row).** Many of these boards are **common-port** (no C− pad): the charger then connects to P+/P− (see "Protection and sensing") |
| 4S charger module | 1 | **4S 2 A Type-C boost charger module** (ordered) – multi 2S/3S/4S selectable, Type-C 5 V in → 16.8 V CC/CV out | **VERIFY the module is set to 4S before first charge.** On 5 V it charges at ~0.8 A at best, about 5 h for a full pack, not 2 A (see "Charging rate"). Output → BMS CHG+/CHG- (P+/P− on a common-port BMS, on the pack side of the fuse); works with the dial OFF. **Measure its status pin before plugging it into J6 (GP13)** |
| 0.96" OLED display | 1 | SSD1306 128×64 I2C module, 3.3–5 V, 3.3 V logic compatible | Battery %, charging, fan speed – small pod on the base's rear wall. **No level shifter needed** (unlike the 1602). Its listing gives the header as **GND, VCC, SCL, SDA** (check the silkscreen anyway: these modules come both ways round), a 27.3 × 27.8 mm board, and −20 to 60 °C |
| Buck converters | 2 | **MP1584EN** chips on the board; outputs fixed by resistors at **12.0 V** and **4.98 V**, nothing to adjust | 12 V: the fan rail from the 4S pack (fan draws only 0.3 A). 5 V: **powers the RP2040-Zero via its 5V pin.** The Zero exposes no VSYS pin, and 14.8–16.8 V straight from the 4S pack would destroy it (5.5 V max on any logic supply). The two MP1584 mini modules are no longer used in the fan: keep them as bench spares |
| Boost converter (bench) | 1 | **MT3608** module set to 12.0 V | USB-powered bench testing only – does NOT live in the fan. Plugs into the board's J7 (BENCH) |
| Schottky diodes (12 V diode-OR) | 2 | **SS34**, on the board | Diode-OR the two 12 V sources (pack buck + bench input on J7) |
| USB-C charge port | 1 | USB-C power socket that brings out **CC1/CC2** (6-pin or more), with **5.1k from each CC pin to GND** (some breakouts have them fitted), wired to charger module input | +X side wall (left, dial side) – moved from -X for truck access. A two-wire socket gets no power from a C-to-C charger |
| Voltage divider (battery sense) | 2 | 100k + 22k (0805) + 100 nF – on the board | **On the board's switched VIN** (J1 +, after the dial switch). Scales 16.8 V max → 3.03 V for the Zero's ADC; calibrate once with `BATT_CAL` |
| Pull-up resistor (tach) | 1 | 10k to 3.3 V + 1 nF to GND – on the board | Noctua tach is open-collector; the 1 nF keeps PWM crosstalk out of the count |
| Fuse | 1 | 2 A fuse in an inline holder, or a 1.5 A PTC | At BMS P+, before the dial switch. The 40 A BMS alone would let a pinched wire burn |
| Schottky (Zero 5 V feed) | 1 | **SS14**, on the board, always fitted | Between the 5 V buck and the Zero's 5V pin, so USB can't back-feed the buck (see "Protection and sensing") |
| Status-pin protection | 1 + 0–1 | 10k in series, on the board; a footprint for a 1N4148WS clamp to 3V3 beside it | Fit the clamp only if the charger's status pin measures above 3.3 V |
| M2 screws + heat-set inserts | 4+4 | M2×6 countersunk | The front faceplate |
| M2 screws | 8 | M2×6 self-tapping | The carrier + PSU board to the bottom-plate bosses |
| M3 screws + heat-set inserts | 10+10 | 4× M3×16 + 4× M3×8 countersunk, 2× M3×8 pan head | Head to base, front and rear; bottom plate |
| M3 screws + heat-set inserts | 4+4 | M3×30 | Fan, through its corner holes into the head's corner columns |
| M4 thumb screws + heat-set inserts | 2+2 | M4×16 knurled (DIN 464) + 2 wave and 2 steel washers | Bail pivots; teeth round them hold the angle |
| Other fixings | – | M2 self-tapping: sled 2× M2×8 + lid 4× M2×6, OLED pod 2× M2×10 + module 4× M2×5; 4 stick-on feet | See `docs/DESIGN_OVERVIEW.md` |
| Wiring, heat-shrink | - | 18 AWG power, 26 AWG signal (on hand); JST XH plugs for the signal leads (crimped, or pre-crimped leads: list in `electronics/pcb/README.md`) | The 18 AWG power leads go into the board's screw terminal J1; the signal leads plug into J3–J6 |
| 18650 slot charger | 1 | 2-slot standalone charger (bench) | Check/top-up cells before install – not part of the build |
| Tactile button 6×6mm | 1 | 6×6 mm tactile switch, **8–9.5 mm tall** (**to order** – not in the current parts order) | Screen on/off toggle: pushed into a pocket in the +X wall from outside, legs through to the inside; wired to GP11 + GND. A shorter switch's stem won't reach out of the pocket |

## Pinout – Waveshare RP2040-Zero (from the board in the photo)
Left edge (top→bottom): **5V, GND, 3V3, GP29, GP28, GP27, GP26, GP15 … GP8**.
Right edge (top→bottom): **GP0 … GP7**. USB-C on top; BOOT/RESET buttons and a
WS2812 RGB LED (on **GP16**) in the middle. No mounting holes – the Zero
solders down via its castellated edges or friction-fits in a printed slot.

### Assigned pins for the fan
| Zero pin | Connects to | Notes |
|----------|-------------|-------|
| 5V | The board's 5 V buck, through the SS14 | MCU power in (from the 4S pack via the 5 V buck) |
| GND | Common ground (the board's pours) | Ground star at J1 −, where BMS P− lands |
| 3V3 (out) | Dial pot top, 10k tach pull-up | Onboard regulator output, logic only |
| GP15 | Fan header Pin 4 (Blue / PWM) | ~25 kHz PWM for the Noctua |
| GP14 | Fan header Pin 3 (Green / Tach) | Input + 10k pull-up to 3V3 (on the board) |
| GP26 (ADC0) | Battery divider tap | 100k (the board's switched VIN) / 22k (GND) + 100 nF → 3.03 V at full charge (on the board) |
| GP13 | Charger module status pin, via J6 | Charging detection, through the board's 10k. **Measure the pin first**: above 3.3 V fit the board's clamp diode, or use an optocoupler |
| GP27 (ADC1) | Dial pot wiper | Speed setting (pot ends: 3V3 / GND) |
| GP0 | OLED SDA | I2C0 SDA direct to the SSD1306 (3.3 V logic, no shifter) |
| GP1 | OLED SCL | I2C0 SCL direct to the SSD1306 |
| GP16 | Onboard WS2812 | Status LED – no extra parts needed |
| GP11 | Screen button (tactile, to GND) | Manual OLED on/off toggle (internal pull-up) |

**No pin for power on/off** – the dial's integrated switch breaks pack+ in
hardware (BMS P+ → fuse → switch → the board's J1), so OFF is a true hard cut and the Zero
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

The fan's own plug goes straight into J2 on the board; pin 1 is at the silkscreen triangle.

## High-Level Wiring Diagram (text)
Full visual version: **`electronics/wiring_diagram.svg`**. Text summary:
```
USB-C charge port (5.1k on CC1/CC2) ──► 4S charger module ──► BMS CHG+/CHG- (charge in, dial-OFF safe)
                          │                (common-port BMS: P+/P-, on the pack side of the fuse)
                          └─ status + GND (measured first) ──► board J6

4×18650 (sled, series straps) ──► BMS B-/B1/B2/B3/B+ (balance taps)

BMS P+ ──► 2 A fuse ──► DIAL SWITCH (hard cut) ──► board J1 + (switched VIN)
BMS P- ──► board J1 - (ground star)

USB 5V (bench cable) ──► MT3608 (12 V, bench only) ──► board J7

Fan's own plug ──► J2    Dial pot ──► J3    OLED ──► J4    Screen button ──► J5

┌─ CARRIER + PSU BOARD (electronics/pcb/) ──────────────────────────────────────────
│ J1 + ─┬─► MP1584 (12.0 V) ──► SS34 ──► J2 pin 2 (fan +12 V)
│       ├─► MP1584 (4.98 V) ──► SS14 ──► Zero 5V pin
│       └─► 100k/22k divider (+100 nF) ──► Zero GP26
│           (switched: 0 V on GP26 while the Zero is off)
│ J7 + (bench 12 V) ──► SS34 ──► J2 pin 2 (diode-OR with the 12 V buck)
│ J1 - ──► GND pours ──► Zero GND, J2 pin 1, buck grounds, pot end, divider bottom
│ Zero GP15 ──► J2 pin 4 (PWM, ~25 kHz)
│ Zero GP14 ──► J2 pin 3 (tach) + 10k pull-up to 3V3 + 1 nF
│ J6 status ──► 10k (+ clamp to 3V3, only if fitted) ──► Zero GP13
│ J3: pot ends to 3V3/GND (pins 1, 3), wiper (pin 2) ──► Zero GP27
│ J4: GND, 3V3, SCL (GP1), SDA (GP0) (direct, 3.3 V – no level shifter;
│     check the OLED's GND/VCC order on its silkscreen!)
│ J5: Zero GP11 ──► tactile button ──► GND (screen toggle, internal pull-up)
│ Zero GP16 ──► onboard WS2812 (status)
│ Zero USB-C ──► rear-panel cutout + collar (firmware/programming port)
└───────────────────────────────────────────────────────────────────────────────────
```

**Do NOT use a boost module between the 4S pack and the fan.** The pack runs
14.8–16.8 V; a boost converter cannot step *down*, so a "3.7–18 V to 12 V"
boost set to 12 V would pass ~16 V straight to the fan. The board's MP1584 bucks are
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

**Battery sense (GP26).** The divider, on the board, hangs on the **switched**
VIN, after the dial switch. On
unswitched P+ it fed up to 3.25 V into GP26 while the Zero was off, through the
pin's protection diode into the dead 3V3 rail: outside the RP2040's ratings, and
it half-powers the Zero. The switch drops millivolts, so the reading is still
the pack voltage. 100k/22k puts a full 16.8 V pack at 3.03 V, which leaves room
under the 3.3 V reference. The ADC measures against the Zero's 3V3 rail, and
±2 % on that rail is ±0.34 V at the pack, so calibrate once: compare the screen
with a multimeter on the pack and set `BATT_CAL` in `firmware/main.py` to
multimeter ÷ screen. 100 nF from GP26 to GND filters the noise.

**Charger STAT (GP13).** Many 4S Type-C boost modules have no logic-level status
pin; the "status" is their LED, and an LED node can sit at 5 V or more. GP13
tolerates 3.3 V. The board always has 10k in series between J6 and GP13.
Before plugging the status lead into J6:
1. With J6 empty, charge a real pack from USB and measure the status
   pin to GND while charging, again when full, **and with the USB unplugged**.
   The unplugged reading matters most: it is the normal running state, and an
   unpowered module can pull its pin low, which would read as "charging".
2. If it ever exceeds 3.3 V, fit the clamp diode in its footprint on the board
   (1N4148WS, cathode to 3V3), or use an optocoupler across the LED.
3. Set `CHARGER_ACTIVE_LOW` in `firmware/main.py` from what you measured.

**The Zero's 5V pin and USB.** The board feeds that pin from the 5 V buck
through an SS14 Schottky, always fitted, so a cable in the programming port
with the dial on can't back-feed the buck. The Schottky costs ~0.3 V: the pin
sees about 4.6–4.7 V, which the Zero's 3.3 V regulator absorbs.

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
inverted too (`65535 -` in the `pwm.duty_u16` line of `main.py`). The board
has no footprint for it: GP15 runs straight to J2 pin 4.

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
Since 2026-10-18 everything lives in the **base** under the fan; nothing sits
behind the fan but the head's duct, which since 2026-10-20 runs back over the
whole base. Positions are X across
(+X = left when facing the fan) and Z front to back, in mm; `models/assembly.scad`
with `view = "base_layout"` shows them from above.
- **Sled** (`models/battery_sled.scad`) on the bottom plate against the -X wall
  (X -67..17, Z 11..88): 4 cells side by side, axes front to back, lid screwed on.
- **On the sled's lid**, on foam tape: the 4S BMS (46 × 60 footprint at X -64..-18) and,
  beside it, the charger (X -12..13, Z 40..75), under the left vent slots in the base's top,
  which open into the head's duct, so the fan draws air past it.
  Measure the BMS on arrival: up to about 50 × 75 fits the lid beside the charger.
- **On the plate, +X of the sled**: the carrier + PSU board on 8 M2 bosses (X 18..58.5,
  Z 3.5..96.5), with a 15 × 20 mm notch out of its +X side round the dial pot
  (X 43.5..58.5, Z 14..34). Its 12 V buck, the one that warms, sits under the other vent slots in the base's top.
  Its connectors, roughly (X, Z):
  - J1 VIN (39, 22), at the front by the notch, its wire entry facing +X;
  - J2 FAN (22, 22), right under the fan-cable slot;
  - J7 BENCH (29, 7.5), at the front edge;
  - J6 CHG, J3 DIAL and J4 OLED along the -X edge (X about 21.6), at Z 62, 72 and 84;
  - J5 BTN (55, 66.5), by the button;
  - the Zero at the rear, its USB-C on the rear wall's cutout (X 37.5).
- **+X wall**:
  - the dial pot (Z 24): a ring inside makes the wall 3 mm under the nut, and the knob recess is cut from the outside;
  - the USB-C charge port (Z 46);
  - the screen button (Z 66), in a pocket with a floor, so a press bears on plastic, not glue.
- **Rear wall**: the Zero's USB-C cutout + strain-relief collar, and the **OLED pod**:
  a separate part on 2 screws, glass facing rear, which can be reprinted to fit the
  real module (`oled_*` parameters).
- **Fan cable**:
  - from whichever bottom corner it leaves the fan, along the groove across the cavity floor (there is no room beside the fan);
  - down through the slot in the head's floor and the base's roof (X 14..26);
  - to J2 on the board.
- Bottom plate: 4× M3 countersunk into inserts, the board's 8 bosses, vent slots under its 12 V buck (X 20..42, Z 33..62), and 1 zip-tie bridge behind the sled (X 6, Z 93): the board's leads plug into latching connectors.

### Fan mounting
4× M3 × 30 from the front, through the fan's corner holes (105 mm pattern), into M3
heat-set inserts in the front faces of the head's four corner columns, which run
from the fan back to the rear grille, outside the blades. Run the bolts through the
Noctua's rubber anti-vibration pads if yours has them. The front grille is a
separate part and doesn't hold the fan.

## Assembly Notes
- No bucks to set: the board's outputs are fixed (12.0 V fan rail, 4.98 V for the Zero).
  Test the board on J1 **before** connecting anything (step 1 below).
- Set the MT3608 to 12.0 V on the bench (bench use only – not installed in the fan).
- Keep the 18 AWG power leads short. The ground star is J1 − and the board's pours:
  BMS P− goes straight to J1 −.
- Build the board as in `electronics/pcb/README.md` ("Assembly"): the soldering order,
  the polarity marks, and the pin-1 check on each header before soldering it.
- Solder the Zero to the board via its castellated edges; keep BOOT/RESET reachable.
- The dial switch carries full pack current on its switch contacts – fine for a
  ~0.5 A load, no relay needed.
- Charging works with the dial OFF (charger feeds the BMS directly).
- The MT3608 only ever goes into J7, never straight to the fan: the board's SS34
  diode-OR keeps it and the pack buck apart.
- Fuse at BMS P+ before anything else is connected; charger + on the pack side of it.
- Measure the charger's status pin before it goes anywhere near J6 (above).
- Use stranded wire and tie it down near every joint: 26 AWG joints fatigue first in a truck.
- Solder the OLED's wires at the module; a pushed-on header works loose.
- A strip of 1 mm EVA foam under the sled's lid and at each end of the pack stops it rattling.
- Dial pot: snap off its small locating tab (or drill a hole for it), so its face sits flat on the wall's ring, and tighten the nut firmly.

### First power-up, in this order
1. The board on its own, with J2–J7 empty: a current-limited bench supply
   (12–16.8 V, 100 mA limit) on J1. Measure TP_12V (11.8–12.0 V with no fan on
   it), TP_5V (about 4.6–4.8 V) and TP_3V3 (3.3 V, from the Zero) against TP_GND.
   Idle current is tens of mA.
2. Pack:
   - check that every cell reads 3.0–4.2 V, all within 0.02 V of each other;
   - connect the BMS's **B− first, then B1, B2, B3, B+ in order**, and disconnect in reverse: a wrong order can kill its balance chip;
   - the BMS output should read the pack voltage.
3. Fuse in. Dial OFF: connect the switch to J1 +, and BMS P− to J1 −. Switch on with J2–J7 still empty, and measure TP_12V and TP_5V again.
4. Zero: flash and test it over USB (`firmware/README.md`); the SS14 keeps USB off the 5 V buck, so the dial can be on. Then plug in J3–J5 (dial, OLED, button), and J6 once the charger's status pin is measured.
5. Fan last, into J2: TP_12V drops to about 11.6–11.7 V once it runs (after the SS34). Then calibrate `BATT_CAL` against a multimeter.

## Verify on arrival (electrical)
- **Charger module**: set to 4S; its input spec (5 V only, or USB PD); its
  status pin's voltage while charging, when full and unplugged.
- **USB-C socket**: it brings out CC1/CC2, and has 5.1k pull-downs (fit them if not).
- **BMS**: the balance version; common-port or a separate C− charge pad.
- **Cells**: all four within 0.02 V of each other; whether they came with tabs.
- **Carrier + PSU board**: once built, its test points (TP_VIN, TP_12V, TP_5V, TP_3V3,
  TP_GND) on the bench supply, before anything is plugged in ("First power-up", step 1).
- **Fan**: whether it starts at low duty (`MIN_DUTY`), whether it stops at 0 %,
  and its PWM pin's voltage when powered with the pin unconnected.
- **WH138**: the switch's current rating (the load is under 0.5 A).

## Remaining Decisions
- Whether to include a small LED light bar like the commercial example

Firmware for the RP2040-Zero (PWM + ADC dial + battery sense + I2C OLED) is in
`firmware/`; see its README for the bench test and calibration.
