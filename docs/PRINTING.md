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
