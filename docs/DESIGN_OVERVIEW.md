# Portable 120mm Noctua Table / Hanging Fan – Design Documentation

## Project Goals
- 3D-printable enclosure for Noctua NF-F12 industrialPPC-3000 PWM (120×120×25 mm)
- Removable front faceplate secured with 4× M2 × 6 mm screws (easy cleaning / blade access)
- Standard 4-pin PC fan connector (Molex KK 254 or equivalent) so the fan can be unplugged and replaced
- Raspberry Pi Pico 2 W controls:
  - Power on/off
  - Fan speed (PWM)
  - Battery monitoring / low-voltage cutoff
  - USB-C charging status (if possible)
- Rechargeable Li-ion battery: **4 × 18650 in 4S (14.8 V nominal)**
- USB-C charging port
- Table-top stand + hanging capability (truck cab use)
- Clean, compact aesthetic similar to commercial portable desk fans

## Mechanical Overview
### Main Body (fan_housing.scad)
- Outer dimensions target: ~140 × 140 × 60–70 mm (depth includes rear electronics bay sized for 4×18650 + stand clearance)
- Front cavity accepts the 120 mm fan with ~0.3–0.5 mm clearance
- Fan mounting: 105 × 105 mm hole pattern (standard) using M3 screws + heat-set inserts or nuts on the rear side of the fan recess
- Front face of the housing has 4× M2 threaded holes (or heat-set M2 inserts) at positions that allow the faceplate to clamp or sit flush
- Bottom section: electronics bay for Pico + **4×18650 (4S)** + 4S BMS + charger + optional 12 V buck + USB-C breakout
- Rear: access panel or integrated cover for battery / electronics
- Top: integrated handle / hanging loop
- Bottom rear: fold-out or fixed kickstand for table use

### Removable Faceplate (faceplate.scad)
- Thin (2–3 mm) protective grille or open frame
- 4× M2 clearance holes matching the housing
- Screws: M2 × 6 mm (pan head or button head recommended)
- Designed so the fan can be removed after unscrewing the faceplate (or the faceplate simply protects the front while the fan stays mounted via the 105 mm screws)

### 4-pin Fan Connector
- Internal 4-pin header (standard PC fan pinout) soldered or plugged into a short pigtail
- Allows the Noctua (or any 120 mm 4-pin fan) to be disconnected without desoldering

## Bill of Materials (Mechanical)
- M2 × 6 mm screws × 4 (faceplate)
- M3 × 10–12 mm screws × 4 (fan mounting) + matching nuts or M3 heat-set inserts
- Optional: rubber anti-vibration grommets for the 105 mm mounts
- Heat-set inserts (M2 and M3) if preferred over self-tapping / nuts
- Filament: PETG recommended (strength + temperature resistance). PLA OK for prototypes.

## Next Steps
1. Decide whether to run the fan direct from 4S or use the recommended 12 V buck
2. Add kickstand and hanging handle details
3. Finalize 4S BMS + charger module choice
4. Iterate OpenSCAD models / generate STLs once dimensions locked

Files live in `/models/` and `/docs/` and `/electronics/`.
