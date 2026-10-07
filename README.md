# Table Fan – 120 mm Noctua Portable / Hanging Fan

3D-printable enclosure + electronics for a rechargeable desk/truck fan based on the Noctua NF-F12 industrialPPC-3000 PWM.

## Current Status
- **Mechanical**: Initial OpenSCAD models for main housing and removable faceplate
- **Electronics**: Fully documented BOM, pinout, wiring diagram, and Pico responsibilities (implementation later)
- **Next**: Refine dimensions once battery size is chosen, add kickstand + handle details, generate STLs, then electronics prototype

## Folder Structure
```
table-fan/
├── README.md
├── docs/
│   └── DESIGN_OVERVIEW.md
├── models/
│   ├── fan_housing.scad      ← main body
│   └── faceplate.scad        ← removable front grille (M2×6 mm screws)
└── electronics/
    └── ELECTRONICS_BOM_AND_WIRING.md
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
- Electronics bay sized for Pico 2 W + battery + boost/charger modules
- USB-C port cutout
- Prepared for table stand + hanging handle

## Quick Start – Printing the Current Models
Print both parts, test-fit the Noctua fan, and check M2 screw alignment. The models are parametric – tweak numbers and re-render as we iterate.
