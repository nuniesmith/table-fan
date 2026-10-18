# Portable 120mm Noctua Table / Hanging Fan – Design Documentation

## Project Goals
- 3D-printable enclosure for Noctua NF-F12 industrialPPC-3000 PWM (120×120×25 mm)
- Removable front faceplate secured with 4× M2 screws + M2 nuts (nuts in hex pockets in the housing – easy fan swap/cleaning)
- Standard 4-pin PC fan header on the Zero carrier board so the fan unplugs for replacement
- Waveshare RP2040-Zero (RP2040, USB-C) on a small carrier board controls:
  - Fan speed (25 kHz PWM) from a single dial
  - Battery monitoring / low-voltage cutoff (via ADC + voltage divider)
  - USB-C charging detection & status (onboard WS2812 LED)
- **Single dial switch**: WH138 B10K with rotary on/off click (confirmed – aluminum knob included) – full CCW clicks OFF (hard power cut), CW sweeps slowest → fastest. No separate power button.
- Rechargeable Li-ion battery: **4 × 18650 in 4S1P (14.8 V nominal)** in a printed sled → MP1584 mini 12 V buck → fan; MP1584 mini 5 V buck → RP2040-Zero
- USB-C charging port (rear cover, via 4S charger module – charges with dial OFF) + Zero USB-C programming port (rear cutout + strain-relief collar)
- **U-bail bracket** (`models/bail.scad`): side-pivot U-bracket for truck use – hangs from a wall hook (~100°, stop pins out) or props on a table (~30°, M3 stop pins in). Arms nest into channels in raised side ribs so the folded bail sits **flush** with the body (reference-style); pivot discs rotate in pockets, M4 screws into heat-set inserts (friction pivots). Bar nests in a groove under the base.
- **Faceplate grille**: dense radial grille (outer ring + 4 concentric rings + 24 spokes + hub, ~10-12mm gaps) like the reference – finger-safe for the 3000 RPM fan.
- **Screen button**: 6×6mm tactile on the +X wall by the dial (GP11) – manual OLED toggle; OLED also auto-sleeps 15 s after the dial stops and wakes on dial/USB.
- Clean, compact aesthetic similar to commercial portable desk fans

## Mechanical Overview
### Main Body (fan_housing.scad)
- ~140 × 144 × 62 mm. Two-level electronics bay in the taller base:
  - **Bay floor**: printed 4×1 18650 sled (`models/battery_sled.scad`)
  - **Mezzanine plate** (4× M3 standoffs): 4S BMS + 4S charger module + RP2040-Zero carrier (30×25 perfboard, 4× M2 bosses, USB-C facing rear)
  - **Under the mezzanine** (beside the sled): 2× MP1584 mini bucks (12 V fan rail, 5 V MCU rail)
- Front cavity accepts the 120 mm fan with ~0.4 mm clearance; 105 × 105 mm M3 mounting (top posts + bottom pillars rebuilt as solid ribs inside the bay)
- Faceplate: 4× M2×6 screws into M2 nuts captive in front-face hex pockets (cardinal points, in solid plastic)
- Rear: screwed bay cover (4× M3 into heat-set inserts) with USB-C cutouts (Zero programming port + charge port) and a printed collar guiding/strain-relieving the Zero's USB-C plug
- **Rear OLED pod**: small bump-out on the bay cover housing a 0.96" SSD1306 OLED (128×64, I2C, ~27×27 PCB), glass facing rear – battery %, charging, fan speed. 4× M2 posts; verify the PCB hole spacing (~23 mm) against the real module before printing.
- Side (+X base wall): dial pot through-hole + knob recess; aluminum knob ships with the WH138, printed knob (`models/knob.scad`) is backup
- Top: integrated handle / hanging loop cutout

### Removable Faceplate (faceplate.scad)
- Thin (2.8 mm) protective grille (rings + spokes)
- 4× M2 clearance holes with countersinks at cardinal points, matching the housing
- M2×6 screws from the front into captive M2 nuts – no heat-set inserts needed

### Battery Sled (models/battery_sled.scad)
- Separate printed part: 4×1 inline 18650 tray with divider ribs, end walls, side lips and mounting ears
- Cells alternate direction; series jumpers solder over the low end walls; balance taps to the BMS
- Secure with Kapton tape once wired

### 4-pin Fan Connector
- Header on the Zero carrier board (or a cut fan-extension pigtail) – standard PC pinout
- Fan unplugs without desoldering

## Bill of Materials (Mechanical)
- M2 × 6 mm screws × 4 + M2 nuts × 4 (faceplate, nuts in housing pockets)
- M2 × 6 mm screws × 4 (Zero carrier to mezzanine bosses)
- M3 × 10 mm screws × 4 + M3 heat-set inserts × 4 (rear bay cover)
- M3 × 12 mm screws × 4 (fan mounting) + M3 standoffs × 4 (mezzanine)
- Optional: rubber anti-vibration grommets for the 105 mm mounts
- Filament: PETG recommended (strength + temperature resistance). PLA OK for prototypes.

## Next Steps
1. Generate first printable STLs and test-fit the Noctua fan + sled + carrier + bail
2. Firmware skeleton for the RP2040-Zero (PWM + ADC dial + battery sense + WS2812)
3. Full KiCad schematic later if wanted

Files live in `/models/` and `/docs/` and `/electronics/`.
