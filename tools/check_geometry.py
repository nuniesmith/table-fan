#!/usr/bin/env python3
"""Geometry checks for the table fan models.

Renders each check in models/checks.scad with OpenSCAD, measures the
volume of the result, and prints PASS/FAIL:
  clear  - must be empty (an interference, or a blocked opening)
  touch  - must not be empty (a contact that has to exist)
  inside - must be empty (material missing round an insert pilot)
It also renders every printable part and fails any that isn't manifold:
every edge of its mesh must be shared by exactly two triangles, once each
way. That is read from the exported STL itself, so it works the same with
OpenSCAD 2021.01 (CGAL) and the newer Manifold backend, whose logs differ.

    python3 tools/check_geometry.py              # run everything
    python3 tools/check_geometry.py --stl stl    # also keep the parts' STLs
    python3 tools/check_geometry.py --self-test  # break each check on purpose
    python3 tools/check_geometry.py --overhangs  # where each part bridges or overhangs, and its filament

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
    ("fan_on_ledges", "touch", "the fan's rear corners bear on the corner columns"),
    ("fan_bolts", "clear", "the fan bolts reach their inserts in the columns"),
    ("join_screws", "clear", "the head-to-base screws seat without bottoming out in their inserts"),
    ("cells_vs_sled", "clear", "four 18650s fit the sled"),
    ("sled_vs_body", "clear", "the sled fits the base"),
    ("boards_vs_body", "clear", "BMS, charger, carrier board (each part to its height), pot, USB-C, button and the rear screws fit the base"),
    ("boards_vs_each_other", "clear", "those parts, the sled and the fan don't overlap (pot vs fan and board included)"),
    ("pcb_on_bosses", "touch", "the carrier board bears on the plate's bosses"),
    ("pcb_bosses_whole", "clear", "each of the board's 8 bosses is whole: no vent or recess cuts into one"),
    ("openings", "clear", "USB-C, button, Zero plug, fan cable (slot + floor groove) and vents are open"),
    ("bail_sweep", "clear", "loosened, the bail swings from up to folded without hitting anything"),
    ("bail_detents", "clear", "at every 15 deg step the bail's teeth mesh with the wall's"),
    ("bail_teeth_engage", "touch", "clamped, the bail's teeth bear on the wall's"),
    ("bail_folds_flush", "clear", "folded, the bail stays within the head's sides"),
    ("hook_clearance", "clear", "up, the bar clears the head's top by at least 40 mm for a hook"),
    ("parts_mate", "clear", "head, base, plate, pod, faceplate and bail don't overlap"),
    ("oled_fit", "clear", "the OLED module fits its pod"),
    ("oled_on_posts", "touch", "the OLED PCB seats on the posts"),
    ("button_floor", "touch", "a press on the screen button bears on a floor, not on glue"),
    ("head_pilots", "inside", "1.2-1.5 mm of wall round the head's insert pilots"),
    ("base_pilots", "inside", "walls round the base's insert pilots; knob recess on the outer face"),
]

# --self-test: one deliberate breakage per check, which must make it fail.
# A check that still passes here can't see what it claims to guard.
MUTATIONS = {
    "airflow": {"column_inner": "30"},                  # columns reach into the blades
    "fan_vs_head": {"fan_clearance": "-0.5"},           # cavity smaller than the fan
    "fan_on_ledges": {"column_inner": "61"},            # no columns under the fan
    "fan_bolts": {"m3_insert_depth": "3"},              # bolt tails into the columns past the pilots
    "join_screws": {"join_screw_l": "16"},              # the old M3 x 16: bottoms out in the pilot
    "cells_vs_sled": {"cell_gap": "-1"},                # pockets smaller than the cells
    "sled_vs_body": {"sled_z0": "5"},                   # sled into the front bosses
    "boards_vs_body": {"charger_pos": "[50, 4]"},       # charger out through the +X wall
    "boards_vs_each_other": {"charger_pos": "[-40, 30]"},  # charger onto the BMS
    "pcb_on_bosses": {"carrier_boss_d": "0.01"},        # no bosses under the board
    "pcb_bosses_whole": {"plate_vents": "[21, 41, 26, 62]"},   # a vent slot under the (40.5, 30.2) boss
    "openings": {"cable_groove_depth": "1"},            # cable groove too shallow for the cable
    "bail_sweep": {"bail_len": "50"},                   # bar hits the head's top rear edge
    "bail_detents": {"tooth_n": "23"},                  # teeth out of step with 15 deg
    "bail_teeth_engage": {"tooth_h": "0.01"},           # no teeth
    "bail_folds_flush": {"bail_arm_t": "8"},            # arms thicker than the recess
    "hook_clearance": {"pivot_y": "40"},                # bar 16 mm lower
    "parts_mate": {"tooth_gap": "-0.4"},                # arms' teeth into the wall's
    "oled_fit": {"oled_post_d": "6"},                   # posts onto the glass
    "oled_on_posts": {"oled_post_d": "0.01"},           # no posts
    "button_floor": {"btn_floor": "0"},                 # pocket goes straight through
    "head_pilots": {"pivot_y": "66"},                   # pivot insert breaks out of the head's top
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
    ("test_inserts", "test_prints.scad", "test", "inserts"),
    ("test_fan_fit", "test_prints.scad", "test", "fan_fit"),
    ("test_bail_joint", "test_prints.scad", "test", "bail_joint"),
    ("test_side_wall", "test_prints.scad", "test", "side_wall"),
    ("test_sled_end", "test_prints.scad", "test", "sled_end"),
]

EMPTY_TOL = 0.05    # mm^3
TOUCH_MIN = 1.0     # mm^3


def stl_triangles(path):
    """Triangles of an STL (ASCII or binary) as vertex-tuple triples."""
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
    return tris


def stl_volume(path):
    """Volume of a closed STL, by signed tetrahedra."""
    vol = 0.0
    tris = stl_triangles(path)
    for a, b, c in tris:
        vol += (a[0]*(b[1]*c[2] - b[2]*c[1]) - a[1]*(b[0]*c[2] - b[2]*c[0])
                + a[2]*(b[0]*c[1] - b[1]*c[0]))
    return abs(vol) / 6.0


def stl_manifold(path):
    """(closed, bad_edges): closed means every directed edge appears exactly
    once and its reverse exactly once, i.e. watertight and consistently
    oriented, with no edge shared by four faces."""
    key = lambda v: tuple(round(c, 4) for c in v)   # noqa: E731
    edges = {}
    for tri in stl_triangles(path):
        a, b, c = (key(v) for v in tri)
        if a == b or b == c or c == a:
            continue                                  # degenerate sliver
        for e in ((a, b), (b, c), (c, a)):
            edges[e] = edges.get(e, 0) + 1
    bad = sum(1 for (u, v), n in edges.items() if n != 1 or edges.get((v, u), 0) != 1)
    return bad == 0 and bool(edges), bad


def render(openscad, scad, defines, out, raw=None):
    cmd = [openscad, "-o", str(out)]
    for k, v in defines.items():
        cmd += ["-D", f'{k}="{v}"']
    for k, v in (raw or {}).items():
        cmd += ["-D", f"{k}={v}"]
    cmd.append(str(MODELS / scad))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = proc.stdout + proc.stderr
    if "ERROR:" in log:                 # an assert or a syntax error: never "empty"
        return None, log, f"OpenSCAD error (exit {proc.returncode})"
    empty = any(m in log for m in ("top level object is empty", "No top level geometry",
                                   "Nothing to export", "Current top level object is not a 3D object"))
    if out.exists() and out.stat().st_size > 0:
        return stl_volume(out), log, None
    if empty:
        return 0.0, log, None
    return None, log, f"OpenSCAD failed (exit {proc.returncode})"


def overhang_report(path):
    """Downward faces steeper than 45 deg that aren't on the bed, grouped into
    connected regions: (area mm2, X span, Y span, height). Each should be a
    bridge, supported at both ends, or under ~3 mm."""
    tris = stl_triangles(path)
    zmin = min(v[2] for t in tris for v in t)
    over, total_area = [], 0.0
    for a, b, c in tris:
        u = [b[i] - a[i] for i in range(3)]
        w = [c[i] - a[i] for i in range(3)]
        n = [u[1]*w[2] - u[2]*w[1], u[2]*w[0] - u[0]*w[2], u[0]*w[1] - u[1]*w[0]]
        ln = sum(x*x for x in n) ** 0.5
        if ln == 0:
            continue
        total_area += ln / 2
        if n[2] / ln < -0.71 and min(a[2], b[2], c[2]) > zmin + 0.05:
            over.append(((a, b, c), ln / 2))
    parent = list(range(len(over)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, (t, _) in enumerate(over):
        for v in t:
            k = tuple(round(x, 3) for x in v)
            if k in seen:
                parent[find(i)] = find(seen[k])
            else:
                seen[k] = i
    groups = {}
    for i, item in enumerate(over):
        groups.setdefault(find(i), []).append(item)
    regions = []
    for items in groups.values():
        pts = [v for t, _ in items for v in t]
        span = [max(p[k] for p in pts) - min(p[k] for p in pts) for k in range(3)]
        regions.append((sum(a for _, a in items), span[0], span[1], min(p[2] for p in pts) - zmin))
    return sorted(regions, reverse=True), total_area


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
    ap.add_argument("--overhangs", action="store_true",
                    help="list each part's bridges and overhangs, and estimate its filament")
    args = ap.parse_args()

    openscad = os.environ.get("OPENSCAD") or shutil.which("openscad")
    if not openscad:
        sys.exit("OpenSCAD not found: install it or set OPENSCAD")

    ver = subprocess.run([openscad, "--version"], capture_output=True, text=True)
    print((ver.stdout + ver.stderr).strip().splitlines()[0])
    tmp = Path(tempfile.mkdtemp(prefix="fan-checks-"))
    if args.self_test:
        sys.exit(self_test(openscad, tmp))
    if args.overhangs:
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
            futs = [(label, pool.submit(render, openscad, scad, {var: val} if var else {}, tmp / f"{label}.stl"))
                    for label, scad, var, val in PARTS]
            print("Downward faces above the bed, as printed: each should be a bridge (supported at both")
            print("ends) or under ~3 mm. Filament assumes 4 perimeters, 25% infill, ASA at 1.07 g/cm3.\n")
            for label, fut in futs:
                vol, log, err = fut.result()
                if err:
                    print(f"{label}: {err}")
                    continue
                regions, area = overhang_report(tmp / f"{label}.stl")
                skin = min(vol, area * 1.8)
                grams = (skin + 0.25 * max(0.0, vol - skin)) / 1000 * 1.07
                big = [r for r in regions if r[0] > 3]
                print(f"{label}: ~{grams:.0f} g, {len(big)} region(s) over 3 mm2")
                for a, sx, sy, h in big:
                    print(f"    {a:7.0f} mm2  {sx:5.1f} x {sy:5.1f} mm  at {h:5.1f} mm")
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(0)
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
                closed, bad = stl_manifold(tmp / f"{name}.stl") if err is None and vol else (False, 0)
                ok = err is None and closed and vol > 0
                detail = err or ("manifold" if closed else f"NOT manifold ({bad} bad edges)")
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
