# Table Fan Firmware — Waveshare RP2040-Zero (MicroPython)
#
# Copy main.py, fanlogic.py and ssd1306.py to the Zero (via Thonny). It runs
# on boot. Bench-testable today: headered Zero + spare 4-pin PWM fan.
#   - Fan PWM (blue) -> GP15, fan tach (green) -> GP14 (+10k pull-up to 3V3)
#   - Dial wiper -> GP27 (ADC1), dial ends -> 3V3 / GND
#   - Battery divider (100k/22k, on the SWITCHED bus) -> GP26 (ADC0)
#   - OLED SDA/SCL -> GP0/GP1, charger status -> GP13, button -> GP11
#
# Behavior:
#   - Dial sets fan speed (0-100%). Full-CCW clicks the hardware switch and
#     cuts power entirely (firmware never sees it).
#   - OLED shows speed %, RPM, battery % + volts, charging state.
#   - Screen auto-sleeps 15 s after the dial stops (for sleeping in the
#     truck). Wakes on dial move, USB plug/unplug, or the button. The status
#     LED goes dark with it.
#   - Button (GP11) toggles the screen manually.
#   - Battery below 13.2 V for 5 s -> fan off, latched until the pack is
#     charged above 14.0 V or the dial is clicked off.
#   - The OLED is optional: if it is missing or glitches, the fan keeps
#     running and the screen is retried every 30 s.
#   - A watchdog restarts the board if the loop ever hangs. Hold the screen
#     button while switching on to run without it (debugging in Thonny).
#
# The control logic lives in fanlogic.py, which the desktop tests exercise
# (python3 -m unittest discover -s firmware/tests).

from machine import Pin, PWM, ADC, I2C, WDT
from neopixel import NeoPixel
import time

import fanlogic
import ssd1306

# ------------------------------- Config ------------------------------------
PWM_PIN       = 15
TACH_PIN      = 14
DIAL_ADC_CH   = 1          # ADC1 = GP27 (GP12 can't do ADC on RP2040!)
BATT_ADC_CH   = 0          # ADC0 = GP26
CHARGER_PIN   = 13
BUTTON_PIN    = 11
I2C_SDA_PIN   = 0
I2C_SCL_PIN   = 1

PWM_FREQ_HZ   = 25000
TACH_PPR      = 2          # tach pulses per revolution (standard)
MIN_DUTY      = 20         # %: the dial's travel maps onto MIN_DUTY..100%.
                           # The NF-F12 iPPC-3000 runs at its minimum speed
                           # below 20%; use 0 for a fan that slows further.
SCREEN_TIMEOUT_S = 15
OLED_CONTRAST = 0x40       # 0x00-0xFF; dimmer is kinder in a dark cab
LED_LEVEL     = 32         # WS2812 brightness, 0-255
LED_SWAP_RG   = False      # True if the LED shows red while the fan runs
                           # normally (that board's LED takes RGB, not GRB)

BATT_R1 = 100_000.0        # top of divider
BATT_R2 = 22_000.0         # bottom of divider: 16.8 V -> 3.03 V. (24k put
                           # full charge at 3.25 V, 48 mV under the 3.3 V
                           # reference the ADC measures against.)
BATT_CAL = 1.000           # set once: pack voltage on a multimeter divided by
                           # the voltage the screen shows
BATT_FULL_V   = 16.8       # 4S full (100%)
BATT_CUTOFF_V = 13.2       # 3.3 V/cell: fan off below this for BATT_HOLD_MS (0%)
BATT_RESUME_V = 14.0       # cutoff clears only above this (the pack was charged)
BATT_HOLD_MS  = 5000
ADC_SAMPLES   = 16         # readings averaged per battery sample

CHARGER_ACTIVE_LOW = True  # flip to False if yours idles low. MEASURE the
                           # status pin's voltage before wiring it: GP13 only
                           # tolerates 3.3 V (electronics doc, "Charger STAT").

USE_WDT = True

# ------------------------------- Setup -------------------------------------
pwm = PWM(Pin(PWM_PIN))     # step by step: older MicroPython takes no
pwm.freq(PWM_FREQ_HZ)       # keyword arguments in the PWM constructor
pwm.duty_u16(0)

tach_count = 0
def _tach_irq(pin):
    global tach_count
    tach_count += 1
tach_pin = Pin(TACH_PIN, Pin.IN, Pin.PULL_UP)
tach_pin.irq(trigger=Pin.IRQ_FALLING, handler=_tach_irq)

dial_adc = ADC(DIAL_ADC_CH)
batt_adc = ADC(BATT_ADC_CH)
charger = Pin(CHARGER_PIN, Pin.IN, Pin.PULL_UP)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
btn_flag = False
def _button_irq(pin):
    # Only a flag. The old handler talked I2C from here, which could land in
    # the middle of a screen update; fanlogic.Button debounces it.
    global btn_flag
    btn_flag = True
button.irq(trigger=Pin.IRQ_FALLING, handler=_button_irq)

np = NeoPixel(Pin(16), 1)
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400_000)

# Held screen button at power-on = no watchdog (it can't be stopped once
# started, and Thonny's Stop would then reset the board after 8 s).
wdt = WDT(timeout=8000) if USE_WDT and button.value() == 1 else None

# ------------------------------ OLED ---------------------------------------
# Any OLED error drops the display, never the fan: the old firmware had no
# try/except, so a missing screen at boot or one loose wire mid-night ended
# the program, and with it the low-voltage cutoff.
oled = None
oled_retry_at = time.ticks_ms()

def oled_start(now):
    global oled, oled_retry_at
    try:
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        oled.contrast(OLED_CONTRAST)
    except OSError:
        oled = None
        oled_retry_at = time.ticks_add(now, 30_000)

def oled_do(fn):
    global oled, oled_retry_at
    if oled is None:
        return
    try:
        fn(oled)
    except OSError:
        oled = None
        oled_retry_at = time.ticks_add(time.ticks_ms(), 30_000)

def draw(o, speed_pct, rpm, volts, bpct, charging, cut):
    o.fill(0)
    o.text("TABLE FAN", 0, 0, 1)
    o.text("SPD {:3d}%".format(int(speed_pct)), 0, 16, 1)
    o.text("RPM {:4d}".format(int(rpm)), 0, 28, 1)
    o.text("BAT {:2d}% {:.1f}V".format(bpct, volts), 0, 40, 1)
    if cut:
        o.text("LOW BATTERY!", 0, 52, 1)
    elif charging:
        o.text("CHARGING", 0, 52, 1)
    o.show()

# ------------------------------ Helpers ------------------------------------
def read_avg(adc, n):
    total = 0
    for _ in range(n):
        total += adc.read_u16()
    return total / n

def pack_volts():
    v_adc = read_avg(batt_adc, ADC_SAMPLES) / 65535 * 3.3
    return v_adc * (BATT_R1 + BATT_R2) / BATT_R2 * BATT_CAL

def is_charging():
    lvl = charger.value()
    return (lvl == 0) if CHARGER_ACTIVE_LOW else (lvl == 1)

# ------------------------------- Main loop ---------------------------------
now = time.ticks_ms()
oled_start(now)
dial = fanlogic.Dial(read_avg(dial_adc, 4))
batt = fanlogic.Battery(BATT_CUTOFF_V, BATT_RESUME_V, BATT_FULL_V, BATT_HOLD_MS,
                        diff=time.ticks_diff)
screen = fanlogic.Screen(now, SCREEN_TIMEOUT_S * 1000, diff=time.ticks_diff)
btn = fanlogic.Button()
tach = fanlogic.Tach(now, TACH_PPR, diff=time.ticks_diff)
last_charging = is_charging()
screen_shown = None        # power state last sent to the OLED

while True:
    now = time.ticks_ms()
    if wdt:
        wdt.feed()

    # --- dial -> speed; a real move wakes the screen ---
    speed_pct, moved = dial.update(read_avg(dial_adc, 4))
    if moved:
        screen.wake(now)

    # --- battery (averaged, latched cutoff) ---
    volts, cut = batt.update(pack_volts(), now)

    # --- charger plug/unplug wakes the screen ---
    charging = is_charging()
    if charging != last_charging:
        last_charging = charging
        screen.wake(now)

    # --- button ---
    flagged = btn_flag
    btn_flag = False
    if btn.update(flagged, button.value() == 0):
        screen.toggle(now)

    # --- tach -> RPM (read the IRQ count once) ---
    count = tach_count
    rpm = tach.update(count, now)

    # --- drive fan ---
    pwm.duty_u16(int(fanlogic.fan_duty(speed_pct, cut, MIN_DUTY) / 100 * 65535))

    # --- screen ---
    on = screen.update(now)
    if oled is None and time.ticks_diff(now, oled_retry_at) >= 0:
        oled_start(now)
        screen_shown = None
    if on != screen_shown:
        oled_do(lambda o: o.poweron() if on else o.poweroff())
        screen_shown = on
    if on:
        oled_do(lambda o: draw(o, speed_pct, rpm, volts, batt.percent(), charging, cut))

    # --- LED: dark whenever the screen is ---
    np[0] = fanlogic.led_colour(on, cut, charging, LED_LEVEL, LED_SWAP_RG)
    np.write()

    time.sleep_ms(100)
