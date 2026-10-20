# Portable 120mm Noctua Table / Hanging Fan – Design Documentation

## Project Goals
- 3D-printable enclosure for Noctua NF-F12 industrialPPC-3000 PWM (120×120×25 mm)
- Removable grilles front and rear, each on 4× M2 screws into heat-set inserts (easy fan swap/cleaning)
- Standard 4-pin PC fan header on the Zero carrier board so the fan unplugs for replacement
- Waveshare RP2040-Zero (RP2040, USB-C) on a small carrier board controls:
  - Fan speed (25 kHz PWM) from a single dial
  - Battery monitoring / low-voltage cutoff (via ADC + voltage divider)
  - USB-C charging detection & status (onboard WS2812 LED)
- **Single dial switch**: WH138 B10K with rotary on/off click (confirmed – aluminum knob included) – full CCW clicks OFF (hard power cut), CW sweeps slowest → fastest. No separate power button.
- Rechargeable Li-ion battery: **4 × 18650 in 4S1P (14.8 V nominal)** in a printed sled → MP1584 mini 12 V buck → fan; MP1584 mini 5 V buck → RP2040-Zero
- USB-C charging port on the left (+X) side of the base (via the 4S charger module, charges with the dial OFF) + Zero USB-C programming port (rear cutout + strain-relief collar)
- **U-bail** (`models/bail.scad`): carry handle and wall-hook hanger for truck use. Its arms pivot on M4 screws outside the head's side walls and the bar passes over the top; swung back, it rests on the base.
- **Faceplate grille**: dense radial grille (outer ring + 4 concentric rings + 24 spokes + hub, ~10-12mm gaps) like the reference – finger-safe for the 3000 RPM fan, on the intake side too.
- **Screen button**: 6×6mm tactile on the +X wall by the dial (GP11) – manual OLED toggle; OLED also auto-sleeps 15 s after the dial stops and wakes on dial/USB.
- Clean, compact aesthetic similar to commercial portable desk fans

## Mechanical Overview
About 140 × 177 × 100 mm (W × H × D), plus the knob and the rear pod. Coordinates in the models: X across (+X = left when facing the fan), Y up, Z front to back.

### Head (fan_housing.scad, part = "head")
- A square frame round the fan, 36 mm deep, open front and back. Printed rear face down, so the corner blocks behind the fan grow straight from the bed.
- The fan sits 3 mm behind the front face, with its rear corners on four corner ledges. Four M3 × 30 bolts come in from the front through the fan's corner holes, and their nuts sit in pockets on the ledges' rear faces, so they clamp.
- **Nothing is behind the fan but the rear grille**, so the intake is clear. Until 2026-10-18 a 16 mm slab covered 68 % of the blades.
- Grilles front and rear: the same faceplate, on M2 heat-set inserts at the cardinal points.
- Side walls: M4 inserts for the bail pivots. Floor: 4 countersunk M3 screws down into the base, a slot for the fan cable, and a groove across it, so the cable can run from the bottom corner where it leaves the fan to the slot. The fan sits 0.6 mm from the walls, so there's no room beside it.
- The cavity allows 0.6 mm a side, which covers ASA's ~0.6 % shrink across 121 mm; the bolts locate the fan, so play doesn't matter.

### Base (fan_housing.scad, part = "base")
- Under the head and running 64 mm back behind it. Printed upside down, open at the bottom; the bottom plate (part = "plate") closes it with 4× M3 × 8 into inserts in its corner bosses.
- Inside:
  - The 4S pack in the sled, against the -X wall, with the BMS on the sled's lid.
  - The 5 V buck on the plate under the head, the charger behind it under the vents; the 12 V buck on the lid, beside the BMS.
  - The Zero carrier on 4 bosses on the plate, its USB-C at the rear wall.
- +X wall:
  - the dial pot: a ring inside makes the wall 3 mm thick under its nut, and the knob recess is cut from the outside;
  - the USB-C charge port;
  - the screen button: an 8–9.5 mm tactile switch pushed into a pocket with a floor, so a press bears on plastic, not glue.
- Top, behind the head: vent slots over the charger and the 12 V buck. The fan's intake draws air past them.
- Rear wall: the Zero's USB-C cutout with a strain-relief collar, and the OLED pod (part = "pod"). The pod is a separate part on 2 screws, so it can be reprinted to fit the real module.

### Removable Faceplate (faceplate.scad)
- Thin (2.8 mm) protective grille (rings + spokes); print two, front and rear
- 4× M2 clearance holes with countersinks at the cardinal points, matching the head
- M2×6 screws into M2 heat-set inserts. (The old captive nuts sat in pockets open to the faceplate side, so a screw pulled its nut out instead of clamping.)

### Battery Sled (models/battery_sled.scad)
- 4× 18650 side by side, axes front to back, alternating direction; series straps across the cell ends, leads out through notches in the end walls
- Lid on 4× M2 boxes the cells in, and carries the BMS; 2× M2 up through the plate hold the sled down. A strip of 1 mm EVA foam under the lid and at each end stops the pack rattling
- Tabbed cells or spot-welded nickel strip – never solder to a cell

### U-bail (models/bail.scad)
- Arms ride outside the head's side walls with a nylon washer each, on M4 × 12 into heat-set inserts. Tighten them until the bail holds its angle.
- Up: carry handle, or hook the bar over a wall hook. Back: swung about 158° until the bar rests on the base.
- The old prop position is gone: the base stands on its own.

### 4-pin Fan Connector
- Header on the Zero carrier board (or a cut fan-extension pigtail) – standard PC pinout
- Fan unplugs without desoldering; its plug passes through the slot in the head's floor

## Bill of Materials (Mechanical)
- M2 heat-set inserts × 8 + M2 × 6 countersunk × 8 (faceplates)
- M3 × 30 × 4 + M3 nuts × 4 (fan)
- M3 heat-set inserts × 8: 4 for the head (M3 × 16 countersunk) and 4 for the bottom plate (M3 × 8 countersunk)
- M4 heat-set inserts × 2 + M4 × 12 × 2 + M4 nylon washers × 2 + M4 steel washers × 2 (bail)
- M2 self-tapping into printed pilots: × 2 M2 × 8 (sled to plate), × 4 M2 × 6 (sled lid), × 2 M2 × 10 (OLED pod), × 4 M2 × 5 (OLED to its posts), × 4 M2 × 6 (Zero carrier)
- 4 stick-on rubber feet, up to 12 mm across; 1 mm EVA foam tape; 2.5–3 mm zip ties (3 bridges on the bottom plate)
- Plastic-safe threadlocker (e.g. Vibra-TITE VC-3) for the fan bolts, faceplate and bail screws: truck vibration backs screws out
- Check the insert kit's hole sizes against the pilots: M2 3.2 mm, M3 4.2 mm, M4 5.6 mm
- Filament: **ASA, or PETG**. A parked summer cab reaches 60–70 °C, which sags PLA, and heat-set inserts creep in PETG near its limit.

## Next Steps
1. Test prints first (`models/test_prints.scad`, see `docs/PRINTING.md`): inserts, fan fit, sled end; the side wall when the pot, socket and button arrive
2. Measure the parts as they arrive (OLED module, BMS, charger, USB-C socket, pot) and adjust the parameters; `python3 tools/check_geometry.py` after every change
3. Print the head, faceplates and bail, then the sled, plate and base; the OLED pod last
4. Full KiCad schematic later if wanted

Files live in `/models/`, `/tools/`, `/docs/` and `/electronics/`.
