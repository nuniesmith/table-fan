# Table Fan Firmware

MicroPython for the Waveshare RP2040-Zero. Copy `main.py` and `ssd1306.py`
to the Zero via Thonny (it runs on boot).

## What it does

- **Dial → fan speed**: 25 kHz PWM on GP15, 0–100%. Full-CCW clicks the
  hardware switch and cuts power (the Zero just turns off).
- **Tach → RPM**: counts GP14 pulses (2/rev), 1 s window.
- **Battery**: GP26 via 100k/24k divider → voltage, %, low-voltage cutoff
  at 13.2 V (fan forced off, red LED, "LOW BATTERY!" on screen).
- **OLED** (GP0/GP1): speed %, RPM, battery % + volts, CHARGING indicator.
- **Screen sleep** (for truck sleeping): OLED turns off 15 s after the dial
  stops moving. Wakes on dial movement, USB plug/unplug, or the button.
- **Button** (GP11 → GND): toggles the screen manually.
- **WS2812**: green = running, blue = charging, red = low battery,
  off = screen asleep (fan keeps running).

## Pin map

| Pin | Function |
|-----|----------|
| GP15 | Fan PWM (25 kHz) |
| GP14 | Fan tach (IRQ, +10k pull-up to 3V3) |
| GP27 | Dial wiper (ADC1) — **not GP12! GP12 can't do ADC on RP2040** |
| GP26 | Battery divider (ADC0) |
| GP13 | Charger status (active-low = charging; verify on bench) |
| GP11 | Screen button → GND (internal pull-up) |
| GP0/GP1 | OLED I2C (SDA/SCL) |
| GP16 | Onboard WS2812 |

## Bench test (today, with headered Zero + spare PWM fan)

1. Flash MicroPython to the Zero, copy both `.py` files via Thonny.
2. Fan: GND→GND, 12V→bench 12V, PWM(blue)→GP15, tach(green)→GP14.
   Add a 10k resistor from GP14 to 3V3 (or enable the internal pull-up —
   the firmware already does).
3. Pot (any 10k): ends → 3V3/GND, wiper → GP27.
4. Power the Zero via USB. Turn the pot — the fan should follow.
5. If you have the OLED, wire SDA→GP0, SCL→GP1, VCC→3V3, GND→GND.
   **Check the module's silkscreen — GND/VCC pin order is random.**
6. Battery divider: don't connect the 4S pack until the BMS is wired.
   For bench, a variable PSU through the divider works (stay under 17 V).

## Tuning

All tunables are at the top of `main.py`: `MIN_DUTY` (raise if the fan
won't start at low speed), `SCREEN_TIMEOUT_S`, `CHARGER_ACTIVE_LOW`
(flip if your charger module idles low), `DIAL_DEADBAND`, `BATT_CUTOFF_V`.
