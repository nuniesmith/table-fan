# Portable 120mm Noctua Table / Hanging Fan – Design Documentation

## Project Goals
- 3D-printable enclosure for Noctua NF-F12 industrialPPC-3000 PWM (120×120×25 mm)
- A removable grille in front, on 4× M2 screws into heat-set inserts (the fan comes out the front); the rear grille is part of the head
- Standard 4-pin PC fan header on the carrier + PSU board, so the fan unplugs for replacement
- Waveshare RP2040-Zero (RP2040, USB-C), soldered to the carrier + PSU board (`electronics/pcb/`), controls:
  - Fan speed (25 kHz PWM) from a single dial
  - Battery monitoring / low-voltage cutoff (via ADC + voltage divider)
  - USB-C charging detection & status (onboard WS2812 LED)
- **Single dial switch**: WH138 B10K with rotary on/off click (confirmed – aluminum knob included) – full CCW clicks OFF (hard power cut), CW sweeps slowest → fastest. No separate power button.
- Rechargeable Li-ion battery: **4 × 18650 in 4S1P (14.8 V nominal)** in a printed sled → 12 V MP1584 buck → fan; 5 V MP1584 buck → RP2040-Zero (both bucks on the carrier + PSU board)
- USB-C charging port on the left (+X) side of the base (via the 4S charger module, charges with the dial OFF) + Zero USB-C programming port (rear cutout + strain-relief collar)
- **U-bail** (`models/bail.scad`): carry handle and hook hanger for truck use, with 46 mm of hook room over the top. Its arms pivot on M4 thumb screws in recesses along the duct's sides; teeth round each pivot lock it every 15°, and folded, the arms lie flush.
- **Faceplate grille**: dense radial grille (outer ring + 4 concentric rings + 24 spokes + hub, ~10-12mm gaps) like the reference – finger-safe for the 3000 RPM fan. The rear grille is the same pattern.
- **Screen button**: 6×6mm tactile on the +X wall by the dial (GP11) – manual OLED toggle; OLED also auto-sleeps 15 s after the dial stops and wakes on dial/USB.
- Clean, compact aesthetic similar to commercial portable desk fans

## Mechanical Overview
About 140 × 177 × 100 mm (W × H × D), plus the knob and the rear pod. Coordinates in the models: X across (+X = left when facing the fan), Y up, Z front to back.

### Head (fan_housing.scad, part = "head")
- 100 mm deep, flush with the base's back (2026-10-20; it was a 36 mm frame). At the front, a full-width frame round the fan, with the faceplate on M2 heat-set inserts at its cardinal points. Behind it, a duct back to a rear grille printed with the head, in the faceplate's pattern. The duct stands on the base, whose roof is its floor, and the base's vents open into it.
- The duct is 7 mm narrower each side than the frame, stepping in at 45°: that recess is where the bail's arms sit, flush, when it's folded.
- The fan sits 3 mm behind the front face. Its rear corners rest on four corner columns that run from the fan back to the rear grille, outside the blades. Four M3 × 30 bolts come in from the front through its corner holes into heat-set inserts in the columns' front faces. Nuts would sit behind the columns, out of reach behind the grille.
- **Nothing is behind the fan but the duct and the rear grille**, so the intake is clear. Until 2026-10-18 a 16 mm slab covered 68 % of the blades.
- Printed rear face down: the grille is the first layers, and the columns and walls grow straight up from it. The frame's floor and top widen into the duct at 45°, so nothing bridges.
- The top two columns hold the bail's M4 pivot inserts, through teeth on the recess floor. The bottom two take the two rear head-to-base screws, which come up from inside the base. The frame's floor has the 4 front countersunk M3 screws down into the base, a slot for the fan cable, and a groove across it, so the cable can run from the bottom corner where it leaves the fan to the slot. The fan sits 0.6 mm from the walls, so there's no room beside it.
- The cavity allows 0.6 mm a side, which covers ASA's ~0.6 % shrink across 121 mm; the bolts locate the fan, so play doesn't matter.

### Base (fan_housing.scad, part = "base")
- Under the head, the whole way back. Printed upside down, open at the bottom; the bottom plate (part = "plate") closes it with 4× M3 × 8 into inserts in its corner bosses.
- Inside:
  - The 4S pack in the sled, against the -X wall, with the BMS and the charger side by side on the sled's lid.
  - The carrier + PSU board (the Zero and both bucks) on 8 bosses on the plate, beside the sled, its USB-C at the rear wall.
- +X wall:
  - the dial pot: a ring inside makes the wall 3 mm thick under its nut, and the knob recess is cut from the outside;
  - the USB-C charge port;
  - the screen button: an 8–9.5 mm tactile switch pushed into a pocket with a floor, so a press bears on plastic, not glue.
- Top, behind the fan: vent slots over the board's 12 V buck and over the charger, open into the duct. The fan draws air past them.
- Rear wall: the Zero's USB-C cutout with a strain-relief collar, and the OLED pod (part = "pod"). The pod is a separate part on 2 screws, so it can be reprinted to fit the real module.

### Removable Faceplate (faceplate.scad)
- Thin (2.8 mm) protective grille (rings + spokes); print one, for the front
- 4× M2 clearance holes with countersinks at the cardinal points, matching the head
- M2×6 screws into M2 heat-set inserts. (The old captive nuts sat in pockets open to the faceplate side, so a screw pulled its nut out instead of clamping.)

### Battery Sled (models/battery_sled.scad)
- 4× 18650 side by side, axes front to back, alternating direction; series straps across the cell ends, leads out through notches in the end walls
- Lid on 4× M2 boxes the cells in, and carries the BMS and the charger; 2× M2 up through the plate hold the sled down. A strip of 1 mm EVA foam under the lid and at each end stops the pack rattling
- Tabbed cells or spot-welded nickel strip – never solder to a cell

### U-bail (models/bail.scad)
- Arms ride in the recesses along the duct's sides, on M4 × 16 knurled thumb screws into heat-set inserts in the top corner columns. 24 teeth round each pivot, on the recess floor and on the arm, mesh every 15°; hand-tight, the screw clamps them, so the angle can't slip in a truck. Loosen it about two turns to move a step.
- Up (0°): carry handle, or hang it by the bar, with 46 mm of hook room over the head. Hung up, it points about level at 0° and further down the further back the bail is set: about 15° down at 30°, 36° at 90°.
- Folded (90°): the arms lie along the top of the sides, flush with the front frame and the base, and the bar sits 8 mm behind the rear grille. The base stands on its own.
- The arms and bar are 20 mm wide; the bail prints flat on its U, teeth on the arms' inner faces, with teardrop pivot holes.

### 4-pin Fan Connector
- Header (J2, Molex 47053) on the carrier + PSU board – standard PC pinout; the fan's own plug goes straight in
- Fan unplugs without desoldering; its plug passes through the slot in the head's floor

## Bill of Materials (Mechanical)
- M2 heat-set inserts × 4 + M2 × 6 countersunk × 4 (faceplate)
- M3 × 30 × 4 (fan), into 4 M3 heat-set inserts in the head's corner columns
- M3 heat-set inserts × 10 more: 4 in the base's top (M3 × 14 countersunk, head to base), 2 under the head's back (M3 × 8 pan head, head to base) and 4 for the bottom plate (M3 × 8 countersunk)
- M4 heat-set inserts × 2 + M4 × 16 knurled thumb screws (DIN 464) × 2 + M4 wave washers × 2 + M4 steel washers × 2 (bail)
- M2 self-tapping into printed pilots: × 2 M2 × 8 (sled to plate), × 4 M2 × 6 (sled lid), × 2 M2 × 10 (OLED pod), × 4 M2 × 5 (OLED to its posts), × 8 M2 × 6 (carrier + PSU board)
- 4 stick-on rubber feet, up to 12 mm across; 1 mm EVA foam tape; 2.5–3 mm zip ties (1 bridge on the bottom plate)
- Plastic-safe threadlocker (e.g. Vibra-TITE VC-3) for the fan bolts and faceplate screws: truck vibration backs screws out. Not on the bail's thumb screws, which you turn by hand
- Check the insert kit's hole sizes against the pilots: M2 3.2 mm, M3 4.2 mm, M4 5.6 mm
- Filament: **PLA** for this build. It softens at about 55–60 °C, so the fan stays out of a hot parked cab. PETG or ASA would take more heat with the same files.

## Next Steps
1. Test prints first (`models/test_prints.scad`, see `docs/PRINTING.md`): inserts, fan fit, sled end; the side wall when the pot, socket and button arrive
2. Measure the parts as they arrive (OLED module, BMS, charger, USB-C socket, pot) and adjust the parameters; `python3 tools/check_geometry.py` after every change
3. Print the bail joint test, then the head, faceplate and bail, then the sled, plate and base; the OLED pod last
4. Order the carrier + PSU board and its parts, then build and test it (`electronics/pcb/README.md`, `docs/BUILD.md`)
5. Full KiCad schematic later if wanted

Files live in `/models/`, `/tools/`, `/docs/` and `/electronics/`.
