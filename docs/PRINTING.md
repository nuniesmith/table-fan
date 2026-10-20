# Printing and prep

Everything except the OLED pod can be printed before the parts arrive. The pod
waits for the module, so its hole spacing can be measured first. Run
`python3 tools/check_geometry.py` after changing any dimension.

## Print order
1. **Test prints** (`models/test_prints.scad`, set `test`). Use the filament you'll print the real parts in; ASA and PETG shrink differently.

   | Test | Checks | Then |
   |------|--------|------|
   | `inserts` | 3 pilot sizes each for the M2, M3 and M4 heat-set inserts | Set `m2_insert_d`, `m3_insert_d`, `m4_insert_d` in `fan_housing.scad` to the size that went in straight and won't pull out |
   | `fan_fit` | The head's rear 12 mm: the fan drops in and rests on the ledges, M3 bolts pass its corner holes, the nuts sit in their pockets, a faceplate screws on | Tight fan: raise `fan_clearance`. Up to ~1 mm of play is fine: the bolts locate the fan |
   | `sled_end` | A cell slides in without force or rattle | Tight: raise `cell_gap` in `battery_sled.scad` |
   | `side_wall` | The dial pot's bushing, the knob recess, the charge socket and the button | Print it when those parts arrive (below) |
2. **Head**, **two faceplates** and the **bail**: these depend only on the fan's standard size.
3. **Sled + lid** and the **bottom plate**.
4. **Base**. It depends on the pot, charge socket and button, so print `side_wall` with the real parts first. To print it sooner, check the WH138 against the listing (M7 bushing, 24 mm body) and plan to file the 13 × 10 socket opening if your socket differs.
5. **OLED pod**, once the module is measured: set the `oled_*` parameters.

The knob is a backup only: the aluminium knob ships with the pot.

**Filament**: about 410 g of ASA for the whole fan, plus about 80 g of test prints. One 1 kg spool covers it with room for a reprint. Estimated from the parts' volumes at 4 perimeters and 25 % infill, so expect your slicer to differ by up to ~20 %.

| Part | ~g | Part | ~g |
|------|----|------|----|
| Head | 120 | Faceplate (each) | 42 |
| Base | 85 | Sled + lid | 47 |
| Bottom plate | 44 | Bail | 24 |
| OLED pod | 6 | Test prints (all four) | 80 |

## Ender-3 Neo, in PLA
Seven plates, sliced from Creality's own Ender-3 Neo + Generic PLA profiles
(`slicing/ender3-neo-pla.ini`, below). Every one fits the 220 × 220 bed, needs
no supports, and starts by homing and probing the bed (`G28`, `G29`). Print
them in number order:

| # | Plate | Time | PLA |
|---|-------|------|-----|
| 01 | Test prints: inserts, sled end, side wall (with a brim: the wall piece stands up) | 4 h 09 | 33 g |
| 02 | Test: fan fit, at draft settings (0.28 mm, 2 walls); it only checks fit | 2 h 44 | 32 g |
| 03 | Head | 12 h 26 | 122 g |
| 04 | Faceplate: **print twice**, front and rear | 5 h 27 each | 43 g each |
| 05 | Bail + sled lid | 3 h 17 | 34 g |
| 06 | Bottom plate + battery sled | 8 h 24 | 82 g |
| 07 | Base | 9 h 20 | 90 g |

About 51 hours and 480 g of PLA in all. Print 01 and 02 first, and check
them before going on (see "Print order" above). If a test shows a fit is off,
change the dimension and re-slice:

    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer   # writes gcode/

Before the first plate:
- **Set the Z offset** on the printer, so the first layer of plate 01 is right. Every print re-probes the bed, which adds about 2 minutes.
- PLA: 205 °C for the first layer, 200 °C after (what your PLA prints at); bed 60 °C; part fan at 100 % from layer 2. Overhanging edges print with bridge settings ("detect bridging perimeters").
- **PLA softens at about 55–60 °C**, and a parked summer cab gets hotter. PLA is fine for fitting everything and a first build; before trusting it in a hot truck, reprint at least the head, base and bail in PETG (the Neo prints it at 230–240 °C on a 70–80 °C bed).
- Heat-set inserts go into PLA at a lower iron temperature: about 180–200 °C.

To slice by hand instead, import `slicing/ender3-neo-pla.ini` in PrusaSlicer (File › Import › Import Config) and load the STLs from `python3 tools/check_geometry.py --stl stl`.

### The final build, in PETG
Once the PLA build has proved the fits, reprint for the truck in PETG. It's the same seven plates and about the same times, using about 490 g:

    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer --material petg   # writes gcode/petg/

- **235 °C**, not Creality's 240: the Neo's hotend is PTFE-lined to the nozzle, and PTFE starts to break down above about 240 °C.
- Bed 70 °C. Part fan 20–50 %, off for the first 3 layers, full for bridges.
- PETG can bond to a PEI or glass bed hard enough to tear the surface: wipe on a thin layer of glue stick as a release.
- PETG picks up moisture: if it pops or strings badly, dry the spool (about 65 °C for 4 h).
- Reprint `01_test_prints` in PETG first: inserts sit differently in it.

## Settings
- **Material: ASA, or PETG.** A parked summer cab reaches 60–70 °C, which sags PLA. ASA needs an enclosure and shrinks about 0.6 %; turn on your slicer's shrinkage compensation if it has one. The fan cavity already allows for the shrink.
- 0.2 mm layers; **4 perimeters** (the insert bosses and pivot walls need solid plastic round them); 5 top and bottom layers; 25 % gyroid infill.
- **No supports on any part.** What remains are short bridges (the base's openings, 13–22 mm; the head's cable slot, 12 mm) and horizontal holes: default bridge settings. `python3 tools/check_geometry.py --overhangs` lists every one, part by part.
- Brim of about 5 mm on the base and the bottom plate in ASA, whose corners lift.
- Orientations are in the README table: each part renders already in its print orientation.

## Heat-set inserts
Press them in straight with a soldering iron (about 230 °C for PETG, 250 °C for ASA) until flush, and let them cool before loading them.

| Where | Inserts |
|-------|---------|
| Head, front and rear faces (faceplates) | M2 × 8 |
| Head, side walls (bail pivots) | M4 × 2 |
| Base, top surface (head screws) | M3 × 4 |
| Base, corner bosses underneath (bottom plate) | M3 × 4 |

## Order now
Not in the Oct 17 order, or decided since. Skip what's already in your kits.
- **Fixings**:
  - heat-set inserts M2 ×8 / M3 ×8 / M4 ×2;
  - M2 × 6 countersunk ×8 (faceplates);
  - M3 × 30 ×4 with nuts and washers (fan);
  - M3 × 16 countersunk ×4 (head to base);
  - M3 × 8 countersunk ×4 (bottom plate);
  - M4 × 12 ×2, plus 2 nylon and 2 steel washers (bail);
  - M2 self-tapping screws, 5–10 mm, about 16.
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
