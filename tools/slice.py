#!/usr/bin/env python3
"""Slice the table fan's print plates for a Creality Ender-3 Neo, in PLA or PETG.

Exports every part's STL with OpenSCAD (as tools/check_geometry.py does),
then slices each plate with PrusaSlicer and slicing/ender3-neo-<material>.ini,
and prints each plate's time, filament and any slicer warnings.

    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer                  # PLA -> gcode/pla/
    python3 tools/slice.py --prusaslicer /path/to/prusa-slicer --material petg  # PETG -> gcode/petg/

Needs OpenSCAD and PrusaSlicer 2.7 or later (its AppImage works: pass the
extracted squashfs-root/AppRun). Copy the .gcode files to the printer's SD
card and print them in number order; docs/PRINTING.md says what each tests.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_geometry as cg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = {"pla": ROOT / "slicing" / "ender3-neo-pla.ini", "petg": ROOT / "slicing" / "ender3-neo-petg.ini"}

# The fan-fit test only checks fits, so it prints faster at draft settings.
DRAFT = ["--layer-height", "0.28", "--perimeters", "2", "--top-solid-layers", "3",
         "--bottom-solid-layers", "3", "--fill-density", "15%"]

# (G-code name, parts on the plate, extra PrusaSlicer options). The knob is a
# backup only, so it has no plate.
PLATES = [
    ("01_test_prints", ["test_inserts", "test_sled_end", "test_side_wall"], ["--brim-width", "5"]),   # the wall piece stands tall
    ("02_test_fan_fit", ["test_fan_fit"], DRAFT),
    ("02b_test_bail_joint", ["test_bail_joint"], ["--brim-width", "5"]),   # normal settings: the teeth are what it tests
    ("03_head", ["head"], []),
    ("04_faceplate", ["faceplate"], []),          # the front one; the rear grille is part of the head
    ("05_bail_and_sled_lid", ["bail", "sled_lid"], []),
    ("06_bottom_plate_and_battery_sled", ["bottom_plate", "battery_sled"], []),
    ("07_base", ["base"], []),
    ("08_oled_pod", ["oled_pod"], []),     # check the module's hole spacing first
]


def warnings(log):
    """PrusaSlicer's warnings, one line each: a warning runs from "warning:"
    to its next progress line ("89 => ...")."""
    found = []
    for m in re.finditer(r"warning: (.*?)(?=\n\d+ =>|\Z)", log, re.S):
        text = " ".join(m.group(1).replace("Consider enabling supports.", "").split())
        found.append(text.replace(".stl", ""))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prusaslicer", default=os.environ.get("PRUSASLICER") or shutil.which("prusa-slicer"),
                    help="PrusaSlicer executable (default: $PRUSASLICER or prusa-slicer on PATH)")
    ap.add_argument("--material", choices=sorted(CONFIGS), default="pla")
    ap.add_argument("--out", help="where the G-code goes (default gcode/<material>/)")
    args = ap.parse_args()
    config = CONFIGS[args.material]
    material = args.material.upper()
    openscad = os.environ.get("OPENSCAD") or shutil.which("openscad")
    if not openscad or not args.prusaslicer:
        sys.exit("needs OpenSCAD (or $OPENSCAD) and PrusaSlicer (--prusaslicer or $PRUSASLICER)")

    tmp = Path(tempfile.mkdtemp(prefix="fan-slice-"))
    out = Path(args.out or ROOT / "gcode" / args.material)
    out.mkdir(parents=True, exist_ok=True)
    parts = {label: (scad, var, val) for label, scad, var, val in cg.PARTS}
    needed = sorted({p for _, ps, _ in PLATES for p in ps})
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        stl = {}
        for label in needed:
            scad, var, val = parts[label]
            stl[label] = pool.submit(cg.render, openscad, scad, {var: val} if var else {}, tmp / f"{label}.stl")
        for label, fut in stl.items():
            vol, log, err = fut.result()
            if err or not vol:
                sys.exit(f"{label}: OpenSCAD export failed ({err})")

        def slice_plate(name, labels, extra):
            cmd = [args.prusaslicer, "--export-gcode", "--load", str(config), *extra]
            if len(labels) > 1:
                cmd.append("--merge")
            cmd += ["-o", str(out / f"{name}.gcode")] + [str(tmp / f"{lab}.stl") for lab in labels]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            return proc.returncode, proc.stdout + proc.stderr

        jobs = [(name, pool.submit(slice_plate, name, labels, extra)) for name, labels, extra in PLATES]
        failed = 0
        total_g = 0.0
        print(f"{'plate':36} {'time':>12} {material + ' g':>7}  warnings")
        for name, fut in jobs:
            code, log = fut.result()
            gcode = out / f"{name}.gcode"
            if code or not gcode.exists():
                print(f"{name:36} FAILED\n{log[-600:]}")
                failed += 1
                continue
            text = gcode.read_text()
            t = re.search(r"; estimated printing time \(normal mode\) = (.+)", text)
            g = re.search(r"; filament used \[g\] = ([\d.]+)", text)
            grams = float(g.group(1)) if g else 0.0
            total_g += grams
            print(f"{name:36} {t.group(1) if t else '?':>12} {grams:7.1f}  {'; '.join(warnings(log)) or 'none'}")
    print(f"\n{total_g:.0f} g of {material} in all. G-code in {out}")
    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
