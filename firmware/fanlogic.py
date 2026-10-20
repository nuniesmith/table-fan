# Table fan control logic, free of MicroPython hardware imports so the same
# code runs on the RP2040-Zero and under desktop CPython for the tests
# (firmware/tests/test_fanlogic.py: `python3 -m unittest discover -s firmware/tests`).
#
# Everything that measures time takes `now` as an argument and subtracts
# with the `diff` function it was given: MicroPython's time.ticks_ms()
# wraps, so main.py passes time.ticks_diff; the tests use plain subtraction.


def _sub(a, b):
    return a - b


class Dial:
    """Dial reading (0-65535) -> fan speed in percent, plus "did it move".

    The speed is smoothed toward the latest reading on EVERY update, so it
    always settles where the dial points. Until 2026-10-18 the smoothing only
    stepped when the reading moved 800 counts, so the output froze partway:
    a quick 0 -> 100% turn left the fan at 30%.

    Movement (for waking the screen) is judged separately, with its own
    threshold, and needs two readings in a row past it: one noise spike must
    not light up a dark cab.
    """

    def __init__(self, raw, smooth=0.3, wake_counts=1500, snap_pct=0.25):
        self.smooth = smooth
        self.wake_counts = wake_counts
        self.snap_pct = snap_pct
        self.pct = raw / 65535 * 100
        self._ref = raw          # the reading the last wake was judged from
        self._pending = False    # one reading past the threshold already seen

    def update(self, raw):
        """Feed one reading. Returns (speed_pct, moved)."""
        target = raw / 65535 * 100
        self.pct += self.smooth * (target - self.pct)
        if abs(target - self.pct) < self.snap_pct:
            self.pct = target
        moved = False
        if abs(raw - self._ref) >= self.wake_counts:
            if self._pending:
                moved = True
                self._ref = raw
                self._pending = False
            else:
                self._pending = True
        else:
            self._pending = False
        return self.pct, moved


class Battery:
    """Pack voltage, percent, and the low-voltage cutoff.

    The cutoff needs the smoothed voltage below `cutoff_v` for `hold_ms` in a
    row, then LATCHES: the fan stays off until the pack reads above `resume_v`
    (it has been charged) or the dial is clicked off, which restarts the
    board. Without the latch the fan's own load toggled it every 100 ms near
    the threshold: the pack sags ~0.1 V while the fan runs and recovers when
    it stops.

    Below `no_pack_v` there is no pack on the divider: the Zero is running
    from USB, on the bench. (On the pack, the 5 V buck can't run the Zero
    below ~5.5 V, and the BMS disconnects at ~10 V.) Then there's nothing to
    protect, so no cutoff; until 2026-10-20 the fan stopped 5 s into every
    bench test.
    """

    def __init__(self, cutoff_v=13.2, resume_v=14.0, full_v=16.8, hold_ms=5000,
                 smooth=0.2, diff=_sub, no_pack_v=5.0):
        self.cutoff_v = cutoff_v
        self.resume_v = resume_v
        self.full_v = full_v
        self.hold_ms = hold_ms
        self.smooth = smooth
        self.diff = diff
        self.no_pack_v = no_pack_v
        self.v = None
        self.cut = False
        self._below_since = None

    def update(self, volts, now):
        """Feed one (already averaged) reading. Returns (smoothed_volts, cut)."""
        if self.v is None:
            self.v = volts
        else:
            self.v += self.smooth * (volts - self.v)
        if not self.present():
            self.cut = False
            self._below_since = None
            return self.v, self.cut
        if self.cut:
            if self.v > self.resume_v:
                self.cut = False
                self._below_since = None
        elif self.v < self.cutoff_v:
            if self._below_since is None:
                self._below_since = now
            elif self.diff(now, self._below_since) >= self.hold_ms:
                self.cut = True
        else:
            self._below_since = None
        return self.v, self.cut

    def present(self):
        """A pack is on the divider (not USB power on the bench)."""
        return self.v is not None and self.v >= self.no_pack_v

    def percent(self):
        """0% at the cutoff voltage, 100% at full charge, linear between.

        (0% used to be 12.0 V, so the screen read 25% at the moment the fan
        was cut off.)
        """
        if not self.present():
            return 0
        pct = (self.v - self.cutoff_v) / (self.full_v - self.cutoff_v) * 100
        return int(max(0, min(100, pct)))


class Button:
    """The screen button: one toggle per press, however the contacts bounce.

    The pin IRQ only raises a flag; I2C happens in the main loop. A press is
    acted on once, and the button then has to read released on two updates in
    a row before another press counts. Flags raised meanwhile, by release
    bounce, are dropped. (The old IRQ toggled on any falling edge 200 ms after
    the last, so a press held longer than that toggled again on release.)
    """

    def __init__(self):
        self._held = False
        self._released_reads = 0

    def update(self, flagged, pressed):
        """`flagged`: the IRQ fired since the last update. `pressed`: the pin
        reads pressed now. Returns True when the screen should toggle."""
        if self._held:
            if pressed:
                self._released_reads = 0
            else:
                self._released_reads += 1
                if self._released_reads >= 2:
                    self._held = False
            return False
        if flagged or pressed:
            self._held = True
            self._released_reads = 0
            return True
        return False


class Screen:
    """Whether the OLED should be on: it sleeps `timeout_ms` after the last
    interaction, so the cab goes dark, and the button toggles it either way."""

    def __init__(self, now, timeout_ms=15000, diff=_sub):
        self.timeout_ms = timeout_ms
        self.diff = diff
        self.on = True
        self._last = now

    def wake(self, now):
        self._last = now
        self.on = True

    def toggle(self, now):
        if self.on:
            self.on = False
        else:
            self.wake(now)

    def update(self, now):
        if self.on and self.diff(now, self._last) > self.timeout_ms:
            self.on = False
        return self.on


class Tach:
    """Fan RPM from the tach IRQ's running pulse count, over `window_ms`."""

    def __init__(self, now, ppr=2, window_ms=1000, diff=_sub):
        self.ppr = ppr
        self.window_ms = window_ms
        self.diff = diff
        self.rpm = 0
        self._count = 0
        self._t = now

    def update(self, count, now):
        """`count`: the IRQ's total, read ONCE by the caller (reading the
        global twice let a pulse fall between the two reads)."""
        dt = self.diff(now, self._t)
        if dt >= self.window_ms:
            self.rpm = (count - self._count) / self.ppr * 60000 / dt
            self._count = count
            self._t = now
        return self.rpm


def fan_duty(speed_pct, cut, min_duty=0):
    """PWM duty in percent: off below 1% or while cut off. Above that, the
    dial's travel maps linearly onto `min_duty`..100%, so all of it changes
    the speed. (It used to clamp at `min_duty`; a fan that runs at its
    minimum speed below 20% duty, like the NF-F12 iPPC-3000, then ignored
    the bottom fifth of the dial.)"""
    if cut or speed_pct < 1:
        return 0
    return min_duty + (100.0 - min_duty) * min(100.0, speed_pct) / 100.0


def led_colour(screen_on, cut, charging, level=32, swap_rg=False):
    """The status LED follows the screen: dark whenever the screen sleeps, so
    nothing lights the cab at night (it used to stay blue all night while
    charging, and red after a cutoff). Wake the screen to see the state."""
    if not screen_on:
        return (0, 0, 0)
    if cut:
        c = (level, 0, 0)
    elif charging:
        c = (0, 0, level)
    else:
        c = (0, level, 0)
    # some RP2040-Zero LEDs take RGB rather than WS2812's usual GRB
    return (c[1], c[0], c[2]) if swap_rg else c
