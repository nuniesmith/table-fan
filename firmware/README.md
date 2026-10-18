# Table Fan Firmware

MicroPython for the Waveshare RP2040-Zero. Copy `main.py`, `fanlogic.py`
and `ssd1306.py` to the Zero via Thonny (it runs on boot).

## What it does

- **Dial → fan speed**: 25 kHz PWM on GP15, 0–100%. The speed settles
  exactly where the dial points. Full-CCW clicks the hardware switch and
  cuts power (the Zero just turns off).
- **Tach → RPM**: counts GP14 pulses (2/rev), 1 s window.
- **Battery**: GP26 via a 100k/22k divider on the **switched** bus →
  voltage, % (0% = the cutoff voltage), and the low-voltage cutoff: below
  13.2 V for 5 s the fan stops, "LOW BATTERY!" shows, and it stays off
  until the pack is charged above 14.0 V or the dial is clicked off.
- **OLED** (GP0/GP1): speed %, RPM, battery % + volts, CHARGING indicator.
  Optional: if it is missing or glitches, the fan keeps running and the
  screen is retried every 30 s.
- **Screen sleep** (for truck sleeping): the OLED turns off 15 s after the
  dial stops moving. A real dial movement (two readings in a row), USB
  plug/unplug, or the button wakes it.
- **Button** (GP11 → GND): toggles the screen, once per press.
- **WS2812**: green = running, blue = charging, red = low battery, shown only
  while the screen is on. Dark while the screen sleeps, so nothing lights
  the cab; wake the screen to see the state.
- **Watchdog**: restarts the board if the loop hangs. Hold the screen button
  while switching on to run without it (it can't be stopped once started,
  so Thonny's Stop would otherwise reset the board after 8 s).

## Files

| File | What |
|------|------|
| `main.py` | Pins, hardware setup and the loop |
| `fanlogic.py` | The control logic (dial, battery cutoff, button, screen, LED), no hardware imports |
| `ssd1306.py` | Minimal OLED driver |
| `tests/test_fanlogic.py` | Desktop tests: `python3 -m unittest discover -s firmware/tests` |

## Pin map

| Pin | Function |
|-----|----------|
| GP15 | Fan PWM (25 kHz) |
| GP14 | Fan tach (IRQ, +10k pull-up to 3V3) |
| GP27 | Dial wiper (ADC1) — **not GP12! GP12 can't do ADC on RP2040** |
| GP26 | Battery divider (ADC0), 100k/22k from the switched bus |
| GP13 | Charger status (active-low = charging; **measure its voltage first**) |
| GP11 | Screen button → GND (internal pull-up) |
| GP0/GP1 | OLED I2C (SDA/SCL) |
| GP16 | Onboard WS2812 |

## Bench test (today, with headered Zero + spare PWM fan)

1. Flash MicroPython to the Zero, copy the three `.py` files via Thonny.
2. Fan: GND→GND, 12V→bench 12V, PWM(blue)→GP15, tach(green)→GP14.
   Add a 10k resistor from GP14 to 3V3 (or rely on the internal pull-up —
   the firmware enables it).
3. Pot (any 10k): ends → 3V3/GND, wiper → GP27.
4. Power the Zero via USB. Turn the pot — the fan should follow and settle
   on the dial.
5. If you have the OLED, wire SDA→GP0, SCL→GP1, VCC→3V3, GND→GND.
   **Check the module's silkscreen — GND/VCC pin order is random.**
6. Battery divider: don't connect the 4S pack until the BMS is wired.
   For bench, a variable PSU through the divider works (stay under 17 V).
7. Calibrate once: compare the screen's voltage with a multimeter on the
   pack, and set `BATT_CAL` = multimeter / screen.
8. Charger status: before wiring GP13, measure the module's status pin to
   ground while charging and when full. If it ever exceeds 3.3 V, wire it
   through 10k plus a clamp diode to 3V3, or an optocoupler. Then set
   `CHARGER_ACTIVE_LOW` from what you measured.

## Tuning

All tunables are at the top of `main.py`: `MIN_DUTY` (raise if the fan
won't start at low speed), `SCREEN_TIMEOUT_S`, `OLED_CONTRAST`, `LED_LEVEL`,
`BATT_CAL`, `BATT_CUTOFF_V` / `BATT_RESUME_V` / `BATT_HOLD_MS`,
`CHARGER_ACTIVE_LOW`. Dial smoothing and the wake threshold are arguments
of `fanlogic.Dial` (`smooth`, `wake_counts`).
