"""Desktop tests for firmware/fanlogic.py (plain CPython, no board needed).

Run: python3 -m unittest discover -s firmware/tests
"""

import os
import py_compile
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIRMWARE = os.path.dirname(HERE)
sys.path.insert(0, FIRMWARE)

import fanlogic  # noqa: E402


def raw(pct):
    return int(pct / 100 * 65535)


class DialTests(unittest.TestCase):
    """The four dial movements from the 2026-10-18 review, where the old
    smoothing stalled at 30.0 / 66.4 / 54.6 / 13.6%."""

    def settle(self, start_pct, path, hold=20):
        dial = fanlogic.Dial(raw(start_pct))
        pct = None
        for p in path + [path[-1]] * hold:     # hold = 2 s of 100 ms loops
            pct, _ = dial.update(raw(p))
        return pct

    def test_a_quick_full_turn_reaches_full_speed(self):
        self.assertAlmostEqual(self.settle(0, [100]), 100, delta=0.5)

    def test_a_turn_over_a_second_settles_on_the_dial(self):
        self.assertAlmostEqual(self.settle(20, [20 + 6 * i for i in range(1, 11)]), 80, delta=0.5)

    def test_a_slow_turn_settles_on_the_dial(self):
        self.assertAlmostEqual(self.settle(30, [30 + 0.9 * i for i in range(1, 34)]), 60, delta=0.5)

    def test_turning_down_reaches_zero(self):
        self.assertAlmostEqual(self.settle(60, [60 - 6 * i for i in range(1, 11)]), 0, delta=0.5)

    def test_noise_settles_near_the_dial_without_drifting(self):
        random.seed(2)
        dial = fanlogic.Dial(raw(50))
        for _ in range(300):
            pct, _ = dial.update(raw(50) + random.randint(-120, 120))
        self.assertAlmostEqual(pct, 50, delta=0.6)

    def test_one_noise_spike_does_not_wake_the_screen(self):
        dial = fanlogic.Dial(raw(40))
        readings = [raw(40)] * 5 + [raw(40) + 2500] + [raw(40)] * 5
        self.assertFalse(any(dial.update(r)[1] for r in readings))

    def test_a_real_turn_wakes_the_screen_within_two_readings(self):
        dial = fanlogic.Dial(raw(40))
        moved = [dial.update(raw(45))[1] for _ in range(2)]
        self.assertEqual(moved, [False, True])

    def test_a_still_dial_never_wakes_the_screen(self):
        dial = fanlogic.Dial(raw(70))
        self.assertFalse(any(dial.update(raw(70))[1] for _ in range(200)))


class BatteryTests(unittest.TestCase):
    def feed(self, batt, volts, start_ms, seconds):
        t = start_ms
        for _ in range(int(seconds * 10)):
            batt.update(volts, t)
            t += 100
        return t

    def test_cutoff_waits_five_seconds_below_the_threshold(self):
        batt = fanlogic.Battery()
        t = self.feed(batt, 13.0, 0, 4.0)
        self.assertFalse(batt.cut)
        self.feed(batt, 13.0, t, 2.0)
        self.assertTrue(batt.cut)

    def test_a_brief_dip_does_not_cut(self):
        batt = fanlogic.Battery()
        t = self.feed(batt, 14.5, 0, 2)
        t = self.feed(batt, 13.0, t, 3)
        self.feed(batt, 14.5, t, 10)
        self.assertFalse(batt.cut)

    def test_once_cut_it_stays_cut_until_charged(self):
        batt = fanlogic.Battery()
        t = self.feed(batt, 13.0, 0, 6)
        self.assertTrue(batt.cut)
        t = self.feed(batt, 13.6, t, 60)       # load removed: the pack recovers a little
        self.assertTrue(batt.cut)
        self.feed(batt, 14.2, t, 5)            # charging
        self.assertFalse(batt.cut)

    def test_no_chatter_at_the_threshold_under_load(self):
        """A pack at 13.25 V that sags 0.12 V while the fan runs, with ADC
        noise: the fan may stop once, and must not restart."""
        random.seed(3)
        batt = fanlogic.Battery()
        running, changes, t = True, 0, 0
        for _ in range(6000):                  # 10 minutes
            volts = 13.25 - (0.12 if running else 0.0) + random.uniform(-0.04, 0.04)
            _, cut = batt.update(volts, t)
            now_running = fanlogic.fan_duty(50, cut) > 0
            changes += now_running != running
            running = now_running
            t += 100
        self.assertLessEqual(changes, 1)

    def test_no_pack_on_the_bench_never_cuts(self):
        """USB power with nothing on the divider: the fan must keep running."""
        batt = fanlogic.Battery()
        self.feed(batt, 0.02, 0, 60)
        self.assertFalse(batt.cut)
        self.assertFalse(batt.present())
        self.assertEqual(batt.percent(), 0)

    def test_a_pack_connected_after_usb_power_does_not_cut(self):
        batt = fanlogic.Battery()
        t = self.feed(batt, 0.0, 0, 3)
        self.feed(batt, 15.2, t, 10)          # the smoothed reading climbs through 5..13.2 V
        self.assertFalse(batt.cut)
        self.assertTrue(batt.present())

    def test_a_flat_pack_still_cuts(self):
        batt = fanlogic.Battery()
        self.feed(batt, 12.0, 0, 6)
        self.assertTrue(batt.cut)

    def test_percent_is_zero_at_cutoff_and_full_at_16_8(self):
        batt = fanlogic.Battery()
        batt.update(13.2, 0)
        self.assertEqual(batt.percent(), 0)
        batt = fanlogic.Battery()
        batt.update(16.8, 0)
        self.assertEqual(batt.percent(), 100)

    def test_ticks_wrap_is_handled_by_the_given_diff(self):
        period = 1 << 30
        diff = lambda a, b: ((a - b + period // 2) % period) - period // 2  # noqa: E731
        batt = fanlogic.Battery(diff=diff)
        t = period - 2000
        for _ in range(60):
            batt.update(13.0, t % period)
            t += 100
        self.assertTrue(batt.cut)


class ButtonTests(unittest.TestCase):
    def test_one_press_toggles_once_however_long_it_is_held(self):
        btn = fanlogic.Button()
        toggles = [btn.update(i == 0, True) for i in range(15)]
        self.assertEqual(toggles.count(True), 1)

    def test_release_bounce_does_not_toggle_again(self):
        btn = fanlogic.Button()
        self.assertTrue(btn.update(True, True))
        for _ in range(5):
            btn.update(False, True)            # held 0.5 s
        # release with bounce: flags raised while the pin reads released
        self.assertFalse(btn.update(True, False))
        self.assertFalse(btn.update(True, False))
        self.assertFalse(btn.update(False, False))

    def test_a_second_press_after_release_toggles(self):
        btn = fanlogic.Button()
        btn.update(True, True)
        btn.update(False, False)
        btn.update(False, False)
        self.assertTrue(btn.update(True, True))

    def test_a_press_shorter_than_one_loop_is_caught_by_the_flag(self):
        btn = fanlogic.Button()
        self.assertTrue(btn.update(True, False))


class ScreenAndLedTests(unittest.TestCase):
    def test_screen_sleeps_after_the_timeout_and_wakes(self):
        screen = fanlogic.Screen(0, 15000)
        self.assertTrue(screen.update(14000))
        self.assertFalse(screen.update(15100))
        screen.wake(16000)
        self.assertTrue(screen.update(20000))

    def test_toggle_turns_it_off_and_back_on(self):
        screen = fanlogic.Screen(0, 15000)
        screen.toggle(100)
        self.assertFalse(screen.update(200))
        screen.toggle(300)
        self.assertTrue(screen.update(400))

    def test_the_led_is_dark_whenever_the_screen_sleeps(self):
        for cut in (False, True):
            for charging in (False, True):
                self.assertEqual(fanlogic.led_colour(False, cut, charging), (0, 0, 0))
        self.assertEqual(fanlogic.led_colour(True, True, True), (32, 0, 0))
        self.assertEqual(fanlogic.led_colour(True, False, True), (0, 0, 32))
        self.assertEqual(fanlogic.led_colour(True, False, False), (0, 32, 0))

    def test_swapped_led_still_shows_the_right_colours(self):
        self.assertEqual(fanlogic.led_colour(True, False, False, 32, swap_rg=True), (32, 0, 0))
        self.assertEqual(fanlogic.led_colour(True, True, False, 32, swap_rg=True), (0, 32, 0))
        self.assertEqual(fanlogic.led_colour(True, False, True, 32, swap_rg=True), (0, 0, 32))
        self.assertEqual(fanlogic.led_colour(False, True, True, 32, swap_rg=True), (0, 0, 0))


class FanAndTachTests(unittest.TestCase):
    def test_duty(self):
        self.assertEqual(fanlogic.fan_duty(0.5, False), 0)
        self.assertEqual(fanlogic.fan_duty(60, True), 0)
        self.assertEqual(fanlogic.fan_duty(150, False), 100)
        self.assertEqual(fanlogic.fan_duty(50, False), 50)

    def test_the_whole_dial_changes_the_speed_above_min_duty(self):
        duties = [fanlogic.fan_duty(p, False, min_duty=20) for p in range(1, 101)]
        self.assertAlmostEqual(duties[0], 20.8)
        self.assertAlmostEqual(duties[9], 28.0)         # 10% of the dial
        self.assertEqual(duties[-1], 100)
        self.assertTrue(all(b > a for a, b in zip(duties, duties[1:])))   # no dead zone
        self.assertEqual(fanlogic.fan_duty(0.5, False, min_duty=20), 0)   # still off at the bottom

    def test_rpm_from_pulse_counts(self):
        tach = fanlogic.Tach(0, ppr=2)
        self.assertEqual(tach.update(50, 500), 0)          # window not over yet
        self.assertAlmostEqual(tach.update(100, 1000), 3000)
        self.assertAlmostEqual(tach.update(150, 2000), 1500)


class SourceTests(unittest.TestCase):
    def test_main_and_driver_compile(self):
        for name in ("main.py", "ssd1306.py", "fanlogic.py"):
            py_compile.compile(os.path.join(FIRMWARE, name), doraise=True)


if __name__ == "__main__":
    unittest.main()
