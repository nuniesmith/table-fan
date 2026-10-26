# Build guide

From printed parts to a running fan, in order. The details live elsewhere; this guide is the sequence:
- printing: [PRINTING.md](PRINTING.md);
- wiring and safety: [the electronics doc](../electronics/ELECTRONICS_BOM_AND_WIRING.md);
- the carrier + PSU board: [its README](../electronics/pcb/README.md);
- firmware: [firmware/README.md](../firmware/README.md).

Two parts are still waiting on what arrives:
- **the OLED pod** is sized from the module's listing (27.3 × 27.8 mm board). The listing doesn't give the hole spacing: check the module's holes are **23.3 × 23.8 mm apart** (centre to centre) before printing it;
- **a clamp for the charge socket**, if it needs one.

## 0. Have ready
- **Printed:** head, faceplate, bail, base, bottom plate, battery sled and lid (PLA), and later the OLED pod.
- **Hardware:** the list in PRINTING.md ("Order now"): the fixings, the board and its parts, the JST XH plugs.
- **Tools:**
  - soldering iron with a heat-set insert tip;
  - a fine tip and flux, or hot air, for the board's MP1584 chips;
  - multimeter;
  - a current-limited bench power supply, for the board test;
  - wire strippers, side cutters, heat-shrink, isopropyl;
  - a JST XH crimper, unless you use pre-crimped leads;
  - a spot welder if your cells have no tabs.
- **Wire:** 18 AWG red/black for power; 26 AWG in several colours for signals.

## 1. Prepare the prints
- [ ] Remove brims and skirts. Check that each test print passed: the fan fit, the bail joint, the inserts, the cell fit.
- [ ] Heat-set inserts, with the iron at **about 180–200 °C for PLA**, pressed straight and flush:
  - head: M2 ×4 (front face); M3 ×4 (the corner columns' front faces, 28 mm into the cavity, for the fan); M3 ×2 (underneath, at the back); M4 ×2 (the side recesses, through the teeth);
  - base: M3 ×4 (top surface), M3 ×4 (corner bosses underneath).
- [ ] Clear any stringing out of the holes: the pot hole, the charge socket opening, the button pocket and its leg slots.

## 2. Head and fan
- [ ] Head onto the base: 4× M3 × 14 countersunk (an M3 × 16 bottoms out in the insert before its head seats), from inside the fan cavity down into the base's inserts. Then 2× M3 × 8 pan head from inside the empty base, up through the holes in its roof into the head's rear inserts.
- [ ] Turn the fan so its cable leaves at a **bottom corner**, the +X one (the dial's side) if you can, as it's nearest the slot, and with the airflow arrow pointing out of the front. Feed the plug down through the slot, lay the cable in the floor groove, and seat the fan.
- [ ] 4× M3 × 30 from the front through the fan's corner holes into the columns' inserts. A drop of threadlocker on each.
- [ ] Faceplate on the front: M2 × 6 into the inserts. (The rear grille is part of the head.)

## 3. Electronics on the bench
### 3a. The board
- [ ] Solder it up as [its README](../electronics/pcb/README.md) says ("Assembly"): the MP1584s first, the through-hole connectors last, each header the way its silk outline draws it (the fan header's peg fits its hole only one way; each JST header's slotted wall goes where the silk draws the slots), then its mated plug's pin-1 wire checked at the triangle before soldering. Solder the Zero with its USB-C end flush with the board's rear edge, not set back: a plug's body reaches below the board's top face. The designators aren't on the board: [`assembly.png`](../electronics/pcb/assembly.png) is the map.
- [ ] D_CLAMP, the 1N4148WS: fit it only if the charger's status pin measured over 3.3 V.
- [ ] Test it before anything is plugged in (J2–J7 empty): the bench supply on J1 at 12–16.8 V, limited to 100 mA. Against TP_GND, TP_12V should read 11.8–12.0 V, TP_5V about 4.6–4.8 V and TP_3V3 3.3 V. Idle current is tens of mA. The outputs are set by resistors: there is nothing to adjust. Then swap the supply's leads on J1 for a moment: it should draw nothing (the reverse-polarity FET blocks).

### 3b. The board on the plate
- [ ] It needs no drilling: lay it on the bottom plate, and its 8 holes sit on the plate's 8 bosses, with the Zero's USB-C at the rear edge. A plate printed for the old perfboard (4 bosses) or for the v2 board (one boss at (56.2, 47), now (55.7, 42.6)) won't fit: reprint it (PRINTING.md, plate 06).

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
Cut every wire below to length, label both ends, and heat-shrink every soldered joint. Nothing is spliced: at the board, each lead ends in a plug or in J1's screw terminal (below). Lengths come from the 3D layout, with 20 % extra and 30 mm for the ends. Wires from the plate to a wall part include a **100 mm service loop**, so the plate can be lowered beside the base with everything still connected.

| Wire | From → to | Gauge / colour | Cut |
|------|-----------|----------------|-----|
| Pack − | cell 1 → BMS B− | 18 black | 80 mm |
| Pack + | cell 4 → BMS B+ | 18 red | 120 mm |
| Switched supply in | BMS P+ → **2 A fuse holder** → dial switch | 18 red | 250 mm (fuse inline) |
| Switched supply out | dial switch → J1 + | 18 red | 170 mm (J1's wire entry faces away from the dial: lead it round the terminal). At the switch, bend both switch leads toward the roof or the front wall, not straight back: J1 stands right behind the pot |
| Ground | BMS P− → J1 − | 18 black | 140 mm |
| Charge in | charge socket → charger in (2 wires) | 18 red + black | 210 mm |
| Charge out | charger out → BMS (P+/P− if common-port) (2) | 18 red + black | 80 mm |
| Charger status | charger STAT + GND → J6 (XH-2) | 26 | 90 mm |
| Dial | pot lugs → J3 (XH-3): seen from the knob end with the lugs down, the right lug to pin 1 (3V3), the middle (wiper) to 2, the left to 3 (GND), so clockwise is faster. If the fan runs fastest just above off, swap the outer two | 26 | 210 mm |
| Button | button → J5 (XH-2) | 26 | 150 mm |
| OLED | module GND, VCC, SCL, SDA → J4 (XH-4) pins 1–4 | 26 | 210 mm |
| Fan | the fan's own cable → J2 | (fan cable) | about 170 mm needed from the fan's +X corner (about 200 mm from the −X one); if short, a 4-pin fan extension |
| Bench (bench only) | MT3608 out → J7 (XH-2) | 26 | as convenient |

The 26 AWG signal leads plug into the board's JST XH headers: crimp XH plugs onto them (XHP housings, SXH crimps), or use pre-crimped XH leads. Check each plug's pin-1 wire against the triangle on the board. XH only takes 22–28 AWG, so the 18 AWG power leads go into J1's screw terminal instead: with a crimped ferrule (0.75–1 mm²), or failing that twisted strands; never a tinned end, which loosens under the screw. Re-tighten J1 after the first few trips.

## 4. Into the base
Turn the base upside down on a soft cloth.
- [ ] Wall parts:
  - **dial pot**: snap off its locating tab and turn it so its lugs point to the front wall (toward the roof, the plate or the charge socket there's no room for them), then the nut tight against the inside ring;
  - **charge socket**: glue it into its opening;
  - **button**: push it into its pocket from outside, legs through the slots, a drop of glue to keep it in;
  - **OLED pod**: screw the module to its posts first, then the pod onto the rear wall with 2× M2 × 10.
- [ ] Bottom-plate parts:
  - the sled: 2× M2 × 8 up through the plate;
  - the charger: on the sled's lid beside the BMS, foam tape;
  - the board: 8× M2 × 6 into the plate's bosses, its USB-C at the rear wall.
- [ ] Lead the wiring to the board, the dial OFF, but don't connect it yet: the first power-up (below) connects J1, then the plugs, in order. Zip-tie the wiring to the tie bridge behind the sled: the plugs latch, so it needs only the one.

## 5. First power-up
Plate still beside the base, the dial OFF. Follow **"First power-up, in this order"** in the electronics doc: the board test (done in 3a), then pack, fuse and switch with J2–J7 unplugged, the Zero, and the fan last.

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
