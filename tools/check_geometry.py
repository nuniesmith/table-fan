#!/usr/bin/env python3
"""Geometry checks for the table fan models.

Renders each check in models/checks.scad with OpenSCAD, measures the
volume of the result, and prints PASS/FAIL:
  clear  - must be empty (an interference, or a blocked opening)
  touch  - must not be empty (a contact that has to exist)
  inside - must be empty (material missing round an insert pilot)
It also renders every printable part and fails any that isn't manifold
(OpenSCAD's "Simple: no").

    python3 tools/check_geometry.py              # run everything
    python3 tools/check_geometry.py --stl stl    # also keep the parts' STLs
    python3 tools/check_geometry.py --self-test  # break each check on purpose

Needs OpenSCAD (2021.01 or later) on PATH, or set OPENSCAD. Takes about a
minute on 16 cores. Exit status 1 if anything fails.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODELS = Path(__file__).resolve().parent.parent / "models"

# (check, kind, what it guards against)
CHECKS = [
    ("airflow", "clear", "nothing but the rear grille behind the fan's blades"),
    ("fan_vs_head", "clear", "the fan fits its cavity"),
    ("fan_on_ledges", "touch", "the fan's rear corners bear on the ledges"),
    ("fan_bolts", "clear", "the fan bolts and nuts have their holes and pockets"),
    ("cells_vs_sled", "clear", "four 18650s fit the sled"),
    ("sled_vs_body", "clear", "the sled fits the base"),
    ("boards_vs_body", "clear", "BMS, charger, bucks, carrier, pot, USB-C and button fit the base"),
    ("boards_vs_each_other", "clear", "those parts, the sled and the fan don't overlap (pot vs fan included)"),
    ("openings", "clear", "USB-C, button, Zero plug and fan cable paths go through"),
    ("bail_sweep", "clear", "the bail swings from up to rest without hitting anything"),
    ("bail_rests", "touch", "swung back, the bail lands on the base"),
    ("parts_mate", "clear", "head, base, plate, pod, faceplates and bail don't overlap"),
    ("oled_fit", "clear", "the OLED module fits its pod"),
    ("oled_on_posts", "touch", "the OLED PCB seats on the posts"),
    ("head_pilots", "inside", "1.2-1.5 mm of wall round the head's insert pilots and fan bolts"),
    ("base_pilots", "inside", "walls round the base's insert pilots; knob recess on the outer face"),
]

# --self-test: one deliberate breakage per check, which must make it fail.
# A check that still passes here can't see what it claims to guard.
MUTATIONS = {
    "airflow": {"gusset_inner": "30"},                  # ledges reach into the blades
    "fan_vs_head": {"fan_clearance": "-0.5"},           # cavity smaller than the fan
    "fan_on_ledges": {"gusset_inner": "60.4"},          # no ledges
    "fan_bolts": {"mount_hole_d": "2.5"},               # bolt holes too small
    "cells_vs_sled": {"cell_gap": "-1"},                # pockets smaller than the cells
    "sled_vs_body": {"sled_z0": "5"},                   # sled into the front bosses
    "boards_vs_body": {"charger_pos": "[50, 4]"},       # charger into the pot and a boss
    "boards_vs_each_other": {"buck1_pos": "[22, 30]"},  # buck onto the charger
    "openings": {"cable_slot": "[14, 26, 4, 4.5]"},     # cable slot nearly closed
    "bail_sweep": {"bail_len": "62"},                   # bar hits the head
    "bail_rests": {"bail_rest_angle": "140"},           # bar never reaches the base
    "parts_mate": {"head_depth": "30"},                 # ledges stick out into the rear grille
    "oled_fit": {"oled_post_d": "6"},                   # posts onto the glass
    "oled_on_posts": {"oled_post_d": "0.01"},           # no posts
    "head_pilots": {"m4_insert_depth": "11"},           # pivot pilot breaks into the cavity
    "base_pilots": {"boss_s": "6"},                     # corner bosses too thin
}

# (label, file, variable, value): the printable parts
PARTS = [
    ("head", "fan_housing.scad", "part", "head"),
    ("base", "fan_housing.scad", "part", "base"),
    ("bottom_plate", "fan_housing.scad", "part", "plate"),
    ("oled_pod", "fan_housing.scad", "part", "pod"),
    ("battery_sled", "battery_sled.scad", "sled_part", "print_sled"),
    ("sled_lid", "battery_sled.scad", "sled_part", "print_lid"),
    ("bail", "bail.scad", "bail_part", "print"),
    ("faceplate", "faceplate.scad", None, None),
    ("knob", "knob.scad", None, None),
]

EMPTY_TOL = 0.05    # mm^3
TOUCH_MIN = 1.0     # mm^3


def stl_volume(path):
    """Volume of a closed STL (ASCII or binary), by signed tetrahedra."""
    data = path.read_bytes()
    tris = []
    if data[:5] == b"solid" and b"facet" in data[:400]:
        verts = []
        for line in data.decode(errors="replace").splitlines():
            parts = line.split()
            if parts and parts[0] == "vertex":
                verts.append(tuple(float(v) for v in parts[1:4]))
        tris = [verts[i:i + 3] for i in range(0, len(verts) - 2, 3)]
    elif len(data) >= 84:
        n = struct.unpack("<I", data[80:84])[0]
        for i in range(n):
            v = struct.unpack("<12f", data[84 + 50*i: 84 + 50*i + 48])
            tris.append([v[3:6], v[6:9], v[9:12]])
    vol = 0.0
    for a, b, c in tris:
        vol += (a[0]*(b[1]*c[2] - b[2]*c[1]) - a[1]*(b[0]*c[2] - b[2]*c[0])
                + a[2]*(b[0]*c[1] - b[1]*c[0]))
    return abs(vol) / 6.0


def render(openscad, scad, defines, out, raw=None):
    cmd = [openscad, "-o", str(out)]
    for k, v in defines.items():
        cmd += ["-D", f'{k}="{v}"']
    for k, v in (raw or {}).items():
        cmd += ["-D", f"{k}={v}"]
    cmd.append(str(MODELS / scad))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = proc.stdout + proc.stderr
    empty = ("top level object is empty" in log or "No top level geometry" in log)
    if out.exists() and out.stat().st_size > 0:
        return stl_volume(out), log, None
    if empty:
        return 0.0, log, None
    return None, log, f"OpenSCAD failed (exit {proc.returncode})"


def passes(kind, vol):
    return vol > TOUCH_MIN if kind == "touch" else vol < EMPTY_TOL


def self_test(openscad, tmp):
    kinds = {name: kind for name, kind, _ in CHECKS}
    missing = set(kinds) - set(MUTATIONS)
    if missing:
        print("no mutation for: " + ", ".join(sorted(missing)))
        return 1
    bad = 0
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        futs = {name: pool.submit(render, openscad, "checks.scad", {"check": name},
                                  tmp / f"mut_{name}.stl", MUTATIONS[name]) for name in kinds}
        print(f"{'check':22} {'broken by':34} {'volume mm3':>11}  result")
        for name, fut in futs.items():
            vol, log, err = fut.result()
            caught = err is None and not passes(kinds[name], vol)
            what = ", ".join(f"{k}={v}" for k, v in MUTATIONS[name].items())
            shown = err or f"{vol:11.2f}"
            print(f"{name:22} {what:34} {shown:>11}  {'caught' if caught else 'MISSED'}")
            bad += not caught
    print(f"\n{bad} check(s) missed their breakage")
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stl", metavar="DIR", help="keep the printable parts' STLs here")
    ap.add_argument("--self-test", action="store_true", help="break each check on purpose; each must fail")
    args = ap.parse_args()

    openscad = os.environ.get("OPENSCAD") or shutil.which("openscad")
    if not openscad:
        sys.exit("OpenSCAD not found: install it or set OPENSCAD")

    tmp = Path(tempfile.mkdtemp(prefix="fan-checks-"))
    if args.self_test:
        sys.exit(self_test(openscad, tmp))
    jobs = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        for name, kind, why in CHECKS:
            fut = pool.submit(render, openscad, "checks.scad", {"check": name}, tmp / f"check_{name}.stl")
            jobs.append(("check", name, kind, why, fut))
        for label, scad, var, val in PARTS:
            fut = pool.submit(render, openscad, scad, {var: val} if var else {}, tmp / f"{label}.stl")
            jobs.append(("part", label, None, None, fut))

        failed = 0
        print(f"{'check':22} {'kind':7} {'volume mm3':>11}  result  what")
        for typ, name, kind, why, fut in jobs:
            vol, log, err = fut.result()
            if typ == "check":
                if err:
                    ok, shown = False, err
                else:
                    ok, shown = passes(kind, vol), f"{vol:11.2f}"
                print(f"{name:22} {kind:7} {shown:>11}  {'PASS' if ok else 'FAIL'}    {why}")
            else:
                simple = "Simple:        yes" in log
                ok = err is None and simple and vol and vol > 0
                detail = err or ("manifold" if simple else "NOT manifold")
                print(f"{'part ' + name:22} {'':7} {vol or 0:11.0f}  {'PASS' if ok else 'FAIL'}    {detail}")
                if ok and args.stl:
                    Path(args.stl).mkdir(parents=True, exist_ok=True)
                    shutil.copy(tmp / f"{name}.stl", Path(args.stl) / f"{name}.stl")
            if not ok:
                failed += 1
                (tmp / f"{name}.log").write_text(log)
    print(f"\n{failed} failed" + (f"; OpenSCAD logs in {tmp}" if failed else ""))
    if not failed:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
