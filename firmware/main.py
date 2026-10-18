# Table Fan Firmware — Waveshare RP2040-Zero (MicroPython)
#
# Copy main.py and ssd1306.py to the Zero (via Thonny). It runs on boot.
# Bench-testable today: headered Zero + spare 4-pin PWM fan.
#   - Fan PWM (blue) -> GP15, fan tach (green) -> GP14 (+10k pull-up to 3V3)
#   - Dial wiper -> GP27 (ADC1), dial ends -> 3V3 / GND
#   - Battery divider (100k/24k) -> GP26 (ADC0)
#   - OLED SDA/SCL -> GP0/GP1, charger status -> GP13, button -> GP11
#
# Behavior:
#   - Dial sets fan speed (0-100%). Full-CCW clicks the hardware switch and
#     cuts power entirely (firmware never sees it).
#   - OLED shows speed %, RPM, battery %, charging state.
#   - Screen auto-sleeps 15 s after the dial stops (for sleeping in the
#     truck). Wakes on dial move, USB plug/unplug, or the button.
#   - Button (GP11) toggles the screen manually.
#   - Battery < 13.2 V -> fan forced off (cell protection), red LED.
#   - WS2812: green = running, blue = charging, red = low battery,
#     off = screen asleep (fan still runs).

from machine import Pin, PWM, ADC, I2C
from neopixel import NeoPixel
import time
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
MIN_DUTY      = 0          # %  (raise to ~20 if your fan won't start low)
SCREEN_TIMEOUT_S = 15

BATT_R1 = 100_000.0        # top of divider
BATT_R2 = 24_000.0         # bottom of divider
BATT_FULL_V   = 16.8       # 4S full
BATT_EMPTY_V  = 12.0       # 4S empty (3.0 V/cell)
BATT_CUTOFF_V = 13.2       # hard cutoff (3.3 V/cell) - fan forced off below

CHARGER_ACTIVE_LOW = True  # most charger modules pull STAT low when charging;
                           # flip to False if yours idles low. Verify on bench!

DIAL_DEADBAND = 800        # ADC counts (~1.2%) - ignore jitter below this
DIAL_SMOOTH   = 0.3        # exponential smoothing factor (0-1, lower = smoother)

# ------------------------------- Setup -------------------------------------
pwm = PWM(Pin(PWM_PIN), freq=PWM_FREQ_HZ, duty_u16=0)

tach_count = 0
def _tach_irq(pin):
    global tach_count
    tach_count += 1
tach = Pin(TACH_PIN, Pin.IN, Pin.PULL_UP)
tach.irq(trigger=Pin.IRQ_FALLING, handler=_tach_irq)

dial_adc = ADC(DIAL_ADC_CH)
batt_adc = ADC(BATT_ADC_CH)

charger = Pin(CHARGER_PIN, Pin.IN, Pin.PULL_UP)

np = NeoPixel(Pin(16), 1)

i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
screen_on = True
last_interaction = time.ticks_ms()

def wake_screen():
    global screen_on, last_interaction
    last_interaction = time.ticks_ms()
    if not screen_on:
        screen_on = True
        oled.poweron()

def _button_irq(pin):
    # debounce in IRQ: ignore edges <200 ms apart
    global _last_btn
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_btn) > 200:
        _last_btn = now
        if screen_on:
            _toggle_screen()   # turn off
        else:
            wake_screen()      # turn on
def _toggle_screen():
    global screen_on
    screen_on = False
    oled.poweroff()
_last_btn = 0
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=_button_irq)

# ------------------------------ Helpers ------------------------------------
def dial_percent(raw, prev):
    pct = raw / 65535.0 * 100.0
    # deadband against the previous *displayed* value kills jitter
    if abs(raw - prev[0]) < DIAL_DEADBAND:
        return prev[1]
    prev[0] = raw
    # smooth
    sm = prev[1] + DIAL_SMOOTH * (pct - prev[1])
    prev[1] = sm
    return sm

def batt_voltage():
    # 16-bit ADC, 3.3 V ref, divider ratio (R1+R2)/R2
    v_adc = batt_adc.read_u16() / 65535.0 * 3.3
    return v_adc * (BATT_R1 + BATT_R2) / BATT_R2

def batt_percent(v):
    if v >= BATT_FULL_V: return 100
    if v <= BATT_EMPTY_V: return 0
    return int((v - BATT_EMPTY_V) / (BATT_FULL_V - BATT_EMPTY_V) * 100)

def is_charging():
    lvl = charger.value()
    return (lvl == 0) if CHARGER_ACTIVE_LOW else (lvl == 1)

def set_led(r, g, b):
    np[0] = (r, g, b)
    np.write()

def draw_oled(speed_pct, rpm, bv, bpct, charging, cutoff):
    oled.fill(0)
    oled.text("TABLE FAN", 0, 0, 1)
    oled.text("SPD {:3d}%".format(int(speed_pct)), 0, 16, 1)
    oled.text("RPM {:4d}".format(int(rpm)), 0, 28, 1)
    oled.text("BAT {:2d}% {:.1f}V".format(bpct, bv), 0, 40, 1)
    if cutoff:
        oled.text("LOW BATTERY!", 0, 52, 1)
    elif charging:
        oled.text("CHARGING", 0, 52, 1)
    oled.show()

# ------------------------------- Main loop ---------------------------------
dial_state = [0, 0.0]   # [last_raw, smoothed_pct]
rpm = 0
last_tach_ms = time.ticks_ms()
last_tach_count = 0
last_charger = is_charging()
duty_pct = 0

# settle: take an initial dial reading so we don't ramp from 0
dial_state[0] = dial_adc.read_u16()
dial_state[1] = dial_state[0] / 65535.0 * 100.0

while True:
    loop_ms = time.ticks_ms()

    # --- dial -> target speed ---
    raw = dial_adc.read_u16()
    if abs(raw - dial_state[0]) >= DIAL_DEADBAND:
        wake_screen()  # dial moved (check before dial_percent updates state)
    speed_pct = dial_percent(raw, dial_state)

    # --- battery ---
    bv = batt_voltage()
    bpct = batt_percent(bv)
    cutoff = bv < BATT_CUTOFF_V

    # --- charger edge wakes screen (plug/unplug) ---
    chg = is_charging()
    if chg != last_charger:
        last_charger = chg
        wake_screen()

    # --- tach -> RPM (1 s window) ---
    if time.ticks_diff(loop_ms, last_tach_ms) >= 1000:
        dt = time.ticks_diff(loop_ms, last_tach_ms) / 1000.0
        pulses = tach_count - last_tach_count
        last_tach_count = tach_count
        last_tach_ms = loop_ms
        rpm = (pulses / TACH_PPR) * (60.0 / dt) if dt > 0 else 0

    # --- drive fan ---
    if cutoff:
        duty_pct = 0
    else:
        duty_pct = max(MIN_DUTY, min(100, speed_pct)) if speed_pct > 1 else 0
    pwm.duty_u16(int(duty_pct / 100.0 * 65535))

    # --- screen sleep ---
    if screen_on and time.ticks_diff(loop_ms, last_interaction) > SCREEN_TIMEOUT_S * 1000:
        screen_on = False
        oled.poweroff()

    # --- display + LED ---
    if screen_on:
        draw_oled(speed_pct, rpm, bv, bpct, chg, cutoff)
    if cutoff:
        set_led(32, 0, 0)          # red: low battery
    elif chg:
        set_led(0, 0, 32)          # blue: charging
    elif not screen_on:
        set_led(0, 0, 0)           # dark while you sleep (fan still runs)
    else:
        set_led(0, 32, 0)          # green: running

    time.sleep_ms(100)
