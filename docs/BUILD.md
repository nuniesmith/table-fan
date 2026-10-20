# Build guide

From printed parts to a running fan, in order. The details live elsewhere; this guide is the sequence:
- printing: [PRINTING.md](PRINTING.md);
- wiring and safety: [the electronics doc](../electronics/ELECTRONICS_BOM_AND_WIRING.md);
- firmware: [firmware/README.md](../firmware/README.md).

Two parts are still waiting on what arrives:
- **the OLED pod** is sized from the module's listing (27.3 × 27.8 mm board). The listing doesn't give the hole spacing: check the module's holes are **23.3 × 23.8 mm apart** (centre to centre) before printing it;
- **a clamp for the charge socket**, if it needs one.

## 0. Have ready
- **Printed:** head, faceplate, bail, base, bottom plate, battery sled and lid (PLA), and later the OLED pod.
- **Hardware:** the fixings list in PRINTING.md ("Order now").
- **Tools:**
  - soldering iron with a heat-set insert tip;
  - multimeter;
  - bench power supply (for setting the bucks);
  - wire strippers, side cutters, heat-shrink, isopropyl;
  - a spot welder if your cells have no tabs.
- **Wire:** 18 AWG red/black for power; 26 AWG in several colours for signals.

## 1. Prepare the prints
- [ ] Remove brims and skirts. Check that each test print passed: the fan fit, the bail joint, the inserts, the cell fit.
- [ ] Heat-set inserts, with the iron at **about 180–200 °C for PLA**, pressed straight and flush:
  - head: M2 ×4 (front face); M3 ×4 (the corner columns' front faces, 28 mm into the cavity, for the fan); M3 ×2 (underneath, at the back); M4 ×2 (the side recesses, through the teeth);
  - base: M3 ×4 (top surface), M3 ×4 (corner bosses underneath).
- [ ] Clear any stringing out of the holes: the pot hole, the charge socket opening, the button pocket and its leg slots.

## 2. Head and fan
- [ ] Head onto the base: 4× M3 × 16 countersunk, from inside the fan cavity down into the base's inserts. Then 2× M3 × 8 pan head from inside the empty base, up through the holes in its roof into the head's rear inserts.
- [ ] Turn the fan so its cable leaves at a **bottom corner**, with the airflow arrow pointing out of the front. Feed the plug down through the slot, lay the cable in the floor groove, and seat the fan.
- [ ] 4× M3 × 30 from the front through the fan's corner holes into the columns' inserts. A drop of threadlocker on each.
- [ ] Faceplate on the front: M2 × 6 into the inserts. (The rear grille is part of the head.)

## 3. Electronics on the bench
### 3a. Set the bucks first
- [ ] On the bench supply at about 15 V, with nothing on their outputs, set one MP1584 to **12.0 V** and one to **5.0 V**. Mark them "12" and "5".

### 3b. The Zero carrier (perfboard, about 25 × 30 mm)
- [ ] Solder the Zero onto the perfboard by its castellated edges, with its USB-C at one short edge: that edge goes to the base's rear cutout.
- [ ] Fit the parts:
  - the battery divider: 100k from the VCC pad to GP26, 22k from GP26 to GND, 100 nF from GP26 to GND;
  - the tach pull-up: 10k from GP14 to 3V3, 1 nF from GP14 to GND;
  - the fan header, from the cut extension cable: GND, +12 V, tach → GP14, PWM → GP15;
  - if the charger's status pin measured over 3.3 V: 10k + a 1N4148 clamp on GP13.
- [ ] Leave solder pads for the incoming wires (the cut list below).
- [ ] Drill the 4 corner holes to 2.2 mm, 21 × 26 mm apart, to match the bosses on the bottom plate.

### 3c. The battery pack
- [ ] Check each cell reads 3.0–4.2 V, all four within 0.02 V of each other.
- [ ] Lay them in the sled **alternating direction**, and join them in series:
  - **rear straps**: 1–2 and 3–4;
  - **front strap**: 2–3;
  - use spot-welded nickel strip or the cells' tabs, never solder on a bare cell.
- [ ] Pack leads out through the front end-wall notches: B− from cell 1, B+ from cell 4. Balance leads B1 (rear 1–2), B2 (front 2–3), B3 (rear 3–4) out through the notches nearest them.
- [ ] A strip of 1 mm EVA foam under the lid and at each end; lid on with 4× M2 × 6.
- [ ] BMS on the lid (foam tape). Connect **B− first, then B1, B2, B3, B+**, and check the BMS output reads the pack voltage.

### 3d. The harness
Cut every wire below to length, label both ends, and heat-shrink every joint. Lengths come from the 3D layout, with 20 % extra and 30 mm for the ends. Wires from the plate to a wall part include a **100 mm service loop**, so the plate can be lowered beside the base with everything still connected.

| Wire | From → to | Gauge / colour | Cut |
|------|-----------|----------------|-----|
| Pack − | cell 1 → BMS B− | 18 black | 80 mm |
| Pack + | cell 4 → BMS B+ | 18 red | 120 mm |
| Switched supply in | BMS P+ → **2 A fuse holder** → dial switch | 18 red | 250 mm (fuse inline) |
| Switched supply out | dial switch → VCC splice by the 5 V buck | 18 red | 180 mm |
| VCC | splice → 12 V buck in | 18 red | 150 mm |
| VCC sense | splice → carrier (divider top) | 26 red | 130 mm |
| Ground star | BMS P− → ground splice | 18 black | 90 mm |
| Ground | splice → 5 V buck / 12 V buck / carrier | 18 black | 140 / 80 / 170 mm |
| Charge in | charge socket → charger in (2 wires) | 18 red + black | 160 mm |
| Charge out | charger out → BMS (P+/P− if common-port) (2) | 18 red + black | 160 mm |
| Charger status | charger STAT → carrier GP13 | 26 | 90 mm |
| 12 V | 12 V buck out → 1N5819 → fan header + | 26 yellow | 120 mm |
| 5 V | 5 V buck out → (Schottky) → Zero 5V | 26 orange | 130 mm |
| Dial | pot ends + wiper → 3V3 / GND / GP27 (3) | 26 | 220 mm |
| Button | button → GP11 / GND (2) | 26 | 190 mm |
| OLED | header GND, VCC, SCL, SDA → GND, 3V3, GP1, GP0 (4) | 26 | 240 mm |
| Fan | the fan's own cable → carrier header | (fan cable) | about 260 mm needed; if short, use the cut extension's other half |

Optional: JST-XH plugs on the dial, button and OLED leads, which are 26 AWG, would let the plate come right out. Keep the 18 AWG power leads soldered: JST-XH only takes 22 AWG and thinner, and soldered joints survive vibration best.

## 4. Into the base
Turn the base upside down on a soft cloth.
- [ ] Wall parts:
  - **dial pot**: snap off its locating tab, then the nut tight against the inside ring;
  - **charge socket**: glue it into its opening;
  - **button**: push it into its pocket from outside, legs through the slots, a drop of glue to keep it in;
  - **OLED pod**: screw the module to its posts first, then the pod onto the rear wall with 2× M2 × 10.
- [ ] Bottom-plate parts:
  - the sled: 2× M2 × 8 up through the plate;
  - the charger and the 5 V buck: foam tape, at the places in the layout;
  - the carrier: 4× M2 × 6, its USB-C at the rear wall;
  - the 12 V buck: on the lid beside the BMS.
- [ ] Connect the wall parts' leads to the plate side. Zip-tie each bundle to the three tie bridges, with a dab of glue at the Zero's castellated pads.

## 5. First power-up
Plate still beside the base, the dial OFF. Follow **"First power-up, in this order"** in the electronics doc: bucks first, then pack, fuse, switch, Zero, and the fan last.

## 6. Firmware and calibration
- [ ] Flash MicroPython to the Zero (hold BOOT, plug in USB, copy the UF2), then copy `main.py`, `fanlogic.py`, `ssd1306.py` with Thonny.
- [ ] Thonny's console prints a status line every second; use it for the checks below.
- [ ] Set **`BATT_CAL`**: the pack's voltage on a multimeter ÷ the voltage the screen or console shows.
- [ ] Set **`CHARGER_ACTIVE_LOW`** from the status pin's readings: charging, full, unplugged. With USB unplugged, the screen must not say CHARGING.
- [ ] LED green while running? If it's red, set `LED_SWAP_RG = True`. Fan won't start at the bottom of the dial? Raise `MIN_DUTY`.

## 7. Close up and finish
- [ ] Tuck the service loops in, then the bottom plate: 4× M3 × 8 countersunk. Stick on the 4 feet.
- [ ] Bail: an M4 × 16 thumb screw each side, with a wave washer and a steel washer under its head, through the arm into the pivot insert, the arm's teeth against the wall's. No threadlocker: you turn these by hand. Hand-tight locks the bail; loosen about two turns to move it a 15° step.
- [ ] Final check:
  - the dial runs smoothly over its whole travel, and clicks off;
  - it charges with the dial off (CHARGING shows);
  - the screen sleeps after 15 s and the button wakes it;
  - the bail steps from up to folded, holds each step hand-tight, and folded, its arms sit flush with the sides.

## Looking after it (PLA)
- PLA softens at about 55–60 °C. **Don't leave the fan in a closed, parked cab in summer**: take it inside, or keep it in the shade low in the cab. A light filament colour soaks up less sun.
- The OLED module is rated to 60 °C too.
- PLA creeps a little under constant load. Check the bail's thumb screws are hand-tight before a drive, and re-tighten the faceplate screws after the first few weeks.
- If it ever warps, the same files print in PETG or ASA: `tools/slice.py --material petg`.
