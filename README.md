# Table Fan – 120 mm Noctua Portable / Hanging Fan

3D-printable enclosure + electronics for a rechargeable desk/truck fan based on the Noctua NF-F12 industrialPPC-3000 PWM.

## Current Status
- **Mechanical**: Design pass 2 – two-level electronics bay (printed 4×1 18650 sled on bay floor, mezzanine plate for BMS + charger + Zero carrier), rear bay cover with LCD pod + Zero USB-C cutout, dial pot on +X wall, charge port on −X wall, faceplate on M2 screws + nuts
- **Electronics**: Fully documented BOM, pinout, wiring diagram (SVG schematic), and RP2040-Zero responsibilities (implementation later). Parts ordered Oct 17, 2026.
- **Next**: Folding hang/prop bracket design session, then print + bench-test electronics, generate STLs

## Folder Structure
```
table-fan/
├── README.md
├── docs/
│   └── DESIGN_OVERVIEW.md
├── models/
│   ├── fan_housing.scad      ← main body (two-level electronics bay)
│   ├── faceplate.scad        ← removable front grille (M2 screws + nuts)
│   ├── battery_sled.scad     ← printed 4×1 18650 tray
│   └── knob.scad             ← backup dial knob (aluminum knob ships with pot)
└── electronics/
    ├── ELECTRONICS_BOM_AND_WIRING.md
    └── wiring_diagram.svg    ← visual schematic
```

## How to Generate STLs
1. Install [OpenSCAD](https://openscad.org/) (free).
2. Open `models/fan_housing.scad` and `models/faceplate.scad`.
3. Adjust parameters at the top if needed (especially `faceplate_screw_offset` – keep them matched).
4. Render (F6) → Export as STL.
5. Slice in your preferred slicer (PrusaSlicer, Cura, Orca, etc.). PETG recommended.

## Key Design Features
- Fits standard 120 × 120 × 25 mm fan (105 mm mounting pattern)
- Removable faceplate held by 4× M2 × 6 mm screws for easy cleaning
- Internal 4-pin fan connector for tool-free fan replacement
- Electronics bay sized for Waveshare RP2040-Zero + 4×18650 pack + charger/buck modules
- USB-C port cutouts: charger input + RP2040-Zero programming access
- Onboard WS2812 status LED on the Zero (no extra status LEDs needed)
- Prepared for table stand + hanging handle

## Quick Start – Printing the Current Models
Print both parts, test-fit the Noctua fan, and check M2 screw alignment. The models are parametric – tweak numbers and re-render as we iterate.
