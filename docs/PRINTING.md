# Printing and prep

Everything except the OLED pod can be printed before the parts arrive. The pod
waits for the module, so its hole spacing can be measured first. Run
`python3 tools/check_geometry.py` after changing any dimension. This build is
**PLA**; once the parts are printed, [BUILD.md](BUILD.md) takes it from there.

## Print order
1. **Test prints** (`models/test_prints.scad`, set `test`). Print them in the same PLA as the real parts.

   | Test | Checks | Then |
   |------|--------|------|
   | `inserts` | 3 pilot sizes each for the M2, M3 and M4 heat-set inserts | Set `m2_insert_d`, `m3_insert_d`, `m4_insert_d` in `fan_housing.scad` to the size that went in straight and won't pull out |
   | `fan_fit` | The head round the fan's rear 6 mm, with the corner columns' front 8 mm: the fan drops in and rests on the columns, and M3 inserts go into their pilots so the M3 × 30 bolts reach them | Tight fan: raise `fan_clearance`. Up to ~1 mm of play is fine: the bolts locate the fan |
   | `bail_joint` | One bail pivot: the head's corner with its teeth and M4 insert pilot, and an arm's pivot end. With the M4 insert in and an M4 × 16 screw, the teeth mesh every 15°, hold hand-tight, and swing when it's loosened about two turns | Teeth that skip under load: raise `tooth_h` to 1.0. Arm won't sit flush: check the insert went in flush |
   | `sled_end` | A cell slides in without force or rattle | Tight: raise `cell_gap` in `battery_sled.scad` |
   | `side_wall` | The dial pot's bushing, the knob recess, the charge socket and the button | Print it when those parts arrive (below) |
2. **Head**, the **faceplate** and the **bail**, once `fan_fit` and `bail_joint` have passed: these depend only on the fan's standard size.
3. **Sled + lid** and the **bottom plate**.
4. **Base**. It depends on the pot, charge socket and button, so print `side_wall` with the real parts first. To print it sooner, check the WH138 against the listing (M7 bushing, 24 mm body) and plan to file the 13 × 10 socket opening if your socket differs.
5. **OLED pod**: sized from the module's listing. Check that its mounting holes are 23.3 × 23.8 mm apart before printing; otherwise set `oled_hole_dx` / `oled_hole_dy` and re-slice.

The knob is a backup only: the aluminium knob ships with the pot.

**Filament**: about 535 g of PLA for the whole fan plus about 80 g of test prints, as sliced in the plate table below. One 1 kg spool covers it, with room to reprint anything but the head.

## Ender-3 Neo, in PLA
Nine plates, sliced from Creality's own Ender-3 Neo + Generic PLA profiles
(`slicing/ender3-neo-pla.ini`, below). Every one fits the 220 × 220 bed, needs
no supports, and starts by homing and probing the bed (`G28`, `G29`). Print
them in number order:

| # | Plate | Time | PLA |
|---|-------|------|-----|
| 01 | Test prints: inserts, sled end, side wall (with a brim: the wall piece stands up) | 4 h 09 | 33 g |
| 02 | Test: fan fit, at draft settings (0.28 mm, 2 walls); it only checks fit | 2 h 43 | 34 g |
| 02b | Test: bail joint, at normal settings (the teeth are what it tests), with a brim | 1 h 25 | 12 g |
| 03 | Head: the frame, duct, corner columns and rear grille in one | 28 h 09 | 267 g |
| 04 | Faceplate, for the front | 5 h 28 | 43 g |
| 05 | Bail + sled lid | 4 h 23 | 45 g |
| 06 | Bottom plate + battery sled | 8 h 24 | 82 g |
| 07 | Base | 9 h 22 | 90 g |
| 08 | OLED pod (check the module's holes first) | 1 h 05 | 7 g |

About 65 hours and 610 g of PLA in all. Print 01, 02 and 02b first, and
check them before going on (see "Print order" above): the head alone is more
than a day. If a test shows a fit is off,
change the dimension and re-slice:

    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer   # writes gcode/

Before the first plate:
- **Set the Z offset** on the printer, so the first layer of plate 01 is right. Every print re-probes the bed, which adds about 2 minutes.
- PLA: 205 °C for the first layer, 200 °C after (what your PLA prints at); bed 60 °C; part fan at 100 % from layer 2. Overhanging edges print with bridge settings ("detect bridging perimeters").
- **PLA softens at about 55–60 °C**, and a parked summer cab gets hotter: don't leave the finished fan in a closed cab in the sun ([BUILD.md](BUILD.md), "Looking after it").

To slice by hand instead, import `slicing/ender3-neo-pla.ini` in PrusaSlicer (File › Import › Import Config) and load the STLs from `python3 tools/check_geometry.py --stl stl`.

### If you ever reprint in PETG
PLA is the build. If the fan ever needs to take more heat, the same files print in PETG: the same seven plates and about the same times, using about 490 g:

    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer --material petg   # writes gcode/petg/

- **235 °C**, not Creality's 240: the Neo's hotend is PTFE-lined to the nozzle, and PTFE starts to break down above about 240 °C.
- Bed 70 °C. Part fan 20–50 %, off for the first 3 layers, full for bridges.
- PETG can bond to a PEI or glass bed hard enough to tear the surface: wipe on a thin layer of glue stick as a release.
- PETG picks up moisture: if it pops or strings badly, dry the spool (about 65 °C for 4 h).
- Reprint `01_test_prints` in PETG first: inserts sit differently in it.

## Settings
- **Material: PLA.** It's what's on hand, and it prints these parts easily. It softens at about 55–60 °C, so the finished fan stays out of a hot parked cab. PETG or ASA would take more heat with the same files, and the fan cavity already allows for ASA's shrink.
- 0.2 mm layers; **4 perimeters** (the insert bosses and pivot walls need solid plastic round them); 5 top and bottom layers; 25 % gyroid infill.
- **No supports on any part.** What remains are short bridges (the base's openings, 13–22 mm; the head's cable slot, 12 mm) and horizontal holes: default bridge settings. `python3 tools/check_geometry.py --overhangs` lists every one, part by part.
- No brims needed in PLA, apart from the test plate's standing wall piece, which already has one.
- Orientations are in the README table: each part renders already in its print orientation.

## Heat-set inserts
Press them in straight with a soldering iron (about 180–200 °C for PLA) until flush, and let them cool before loading them.

| Where | Inserts |
|-------|---------|
| Head, front face (faceplate) | M2 × 4 |
| Head, the corner columns' front faces, 28 mm into the cavity (fan) | M3 × 4 |
| Head, underneath at the back (the rear head-to-base screws) | M3 × 2 |
| Head, the side recesses (bail pivots) | M4 × 2 |
| Base, top surface (head screws) | M3 × 4 |
| Base, corner bosses underneath (bottom plate) | M3 × 4 |

## Order now
Not in the Oct 17 order, or decided since. Skip what's already in your kits.
- **Fixings** (as of 2026-10-20's deeper head):
  - heat-set inserts M2 ×4 / M3 ×14 / M4 ×2;
  - M2 × 6 countersunk ×4 (faceplate);
  - M3 × 30 ×4 (fan, into inserts: no nuts);
  - M3 × 16 countersunk ×4 (head to base, front);
  - M3 × 8 pan or button head ×2 (head to base, rear);
  - M3 × 8 countersunk ×4 (bottom plate);
  - **M4 × 16 knurled thumb screws ×2** (DIN 464), 2 steel washers and 2 M4 wave washers (bail);
  - M2 self-tapping screws, 5–10 mm, about 16.
- No longer needed: the fan's M3 nuts, the bail's M4 × 12 and nylon washers, and four of the M2 inserts and screws (there's one faceplate now).
- **Optional**: JST-XH 2.54 mm plugs (2-, 3- and 4-pin) for the dial, button and OLED leads, so the bottom plate can come right out (BUILD.md, the harness).
- **Screen button**: 6 × 6 mm tactile switch, **8–9.5 mm tall**. It sits in a pocket in the wall, so a short one's stem won't reach out of it.
- **Electronics**, from the electronics doc:
  - 2 A fuse + inline holder (or a 1.5 A PTC);
  - a **22k** resistor (in most E12 kits);
  - 100 nF and 1 nF ceramic capacitors;
  - 5.1k × 2, if the USB-C socket has no CC pull-downs;
  - an SS14 Schottky, if the Zero's 5V pin is VBUS;
  - 10k + 1N4148, or a PC817, if the charger's status pin measures over 3.3 V.
- **Cells**: tabbed cells, or nickel strip and a spot welder (a handheld one is fine). Never solder to a cell.
- **Misc**:
  - plastic-safe threadlocker (e.g. Vibra-TITE VC-3);
  - 4 stick-on rubber feet, up to 12 mm across;
  - 1 mm EVA foam tape (so the cells don't rattle);
  - double-sided foam tape (for the boards);
  - 2.5–3 mm zip ties;
  - stranded wire.

## While you wait
- Flash MicroPython to the Zero and run the bench test in `firmware/README.md` with a spare fan: the dial, the LED's colour order and the OLED.
- When the charger arrives, measure its status pin (charging, full, **and unplugged**) before it goes near GP13.
- When the BMS arrives, check its outline: up to about 50 × 75 fits the sled lid.
