#!/usr/bin/env python3
"""Checks for the carrier + PSU board (electronics/pcb).

Reads the Gerber set in electronics/pcb/gerber/ and the circuit JSON that
`tsci build` writes (electronics/pcb/dist/carrier-psu/circuit.json), and
prints PASS/FAIL for:
  fab    - JLCPCB 2-layer standard rules, with margin: via drill and pad,
           annular rings, copper clearance between nets, copper to the
           board edge and to unplated holes, hole spacing, silkscreen line
           width, text height and placement, solder mask over every via
  nets   - the copper, read from the Gerbers, joins exactly the pins in
           NETLIST below and nothing else (no opens, no shorts). NETLIST is
           written out by hand from the design notes, not taken from the
           .tsx, so a wrong connection in the source shows up here
  bodies - no two parts' courtyards overlap, and no part sits under an M2
           screw head
  fit    - the outline lies on the base's free floor (clear of the sled, the
           corner bosses and the dial pot), and every part is low enough for
           what hangs above it (USB-C socket, button, join bosses)

    python3 tools/check_pcb.py                  # run everything
    python3 tools/check_pcb.py --self-test      # break each check on purpose
    python3 tools/check_pcb.py --write-scad     # regenerate models/carrier_pcb.scad
    python3 tools/check_pcb.py --render out.png # the board, its parts and the base around it
    python3 tools/check_pcb.py --assembly electronics/pcb/assembly.png  # the hand-assembly map

Build first (see electronics/pcb/README.md). Needs shapely (pip install
shapely); --render also needs matplotlib. Exit status 1 if anything fails.

The 3D fit is checked again with OpenSCAD by tools/check_geometry.py, from
models/carrier_pcb.scad, which --write-scad generates from the same build.
"""

import argparse
import copy
import itertools
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "electronics" / "pcb"
GERBERS = PCB / "gerber"
CIRCUIT_JSON = PCB / "dist" / "carrier-psu" / "circuit.json"
SCAD_OUT = ROOT / "models" / "carrier_pcb.scad"

# ---------------------------------------------------------------- rules
# JLCPCB's 2-layer minimums are 0.127 mm trace and space, 0.3 mm via drill
# with a 0.5 mm via pad, and 0.2 mm copper to a routed edge. These are a
# little stricter, so a board that passes here has margin at the fab.
RULES = {
    "min_track": 0.2,           # copper drawn with a round aperture (traces)
    "min_space": 0.15,          # copper of one net to copper of another
    "via_drill": 0.3,
    "via_pad": 0.5,
    "via_ring": 0.15,           # (pad - drill) / 2
    "pth_ring": 0.25,
    "hole_gap": 0.5,            # hole wall to hole wall
    "via_gap_same_net": 0.25,
    "edge": 0.3,                # copper to the board outline
    "npth": 0.3,                # copper to an unplated hole's wall
    "silk_line": 0.15,
    "silk_text_cap": 1.0,       # cap height; tscircuit draws caps 0.7 x font size
    "silk_to_edge": 0.2,
}
TEXT_CAP = 0.7                  # cap height / font size in tscircuit's font
SCREW_HEAD_D = 4.2              # M2 pan head (3.8-4.0) and a little play

# ---------------------------------------------------------------- netlist
# What each pin must connect to. Pins are REF.PIN with PIN the source port
# name (pin1/pin2 on resistors and capacitors). Every pad on the board must
# appear here or in NO_CONNECT.
def _buck(t, vout):
    s = lambda n: f"{n}_{t}"
    return {
        "GND": [f"U_{t}.GND", f"U_{t}.EP", f"CIN1_{t}.pin2", f"CIN2_{t}.pin2",
                f"DC_{t}.A", f"COUT1_{t}.pin2", f"COUT2_{t}.pin2", f"RFB2_{t}.pin2",
                f"RCOMP_{t}.pin2", f"RFREQ_{t}.pin2", f"REN2_{t}.pin2"],
        "VIN": [f"U_{t}.VIN", f"CIN1_{t}.pin1", f"CIN2_{t}.pin1", f"REN1_{t}.pin1"],
        s("SW"): [f"U_{t}.SW", f"CBST_{t}.pin2", f"DC_{t}.K", f"L_{t}.IN"],
        s("BST"): [f"U_{t}.BST", f"CBST_{t}.pin1"],
        s("EN"): [f"U_{t}.EN", f"REN1_{t}.pin2", f"REN2_{t}.pin1"],
        s("COMP"): [f"U_{t}.COMP", f"CCOMP_{t}.pin1"],
        s("COMPX"): [f"CCOMP_{t}.pin2", f"RCOMP_{t}.pin1"],
        s("FB"): [f"U_{t}.FB", f"RFB1_{t}.pin2", f"RFB2_{t}.pin1"],
        s("FREQ"): [f"U_{t}.FREQ", f"RFREQ_{t}.pin1"],
        vout: [f"L_{t}.OUT", f"COUT1_{t}.pin1", f"COUT2_{t}.pin1", f"RFB1_{t}.pin1"],
    }


def build_netlist():
    nets = defaultdict(list)
    for part in (_buck("A", "V12"), _buck("B", "V5RAW")):
        for n, pins in part.items():
            nets[n] += pins
    extra = {
        "GND": ["U1.GND", "C_BULK.neg", "R_DIV2.pin2", "C_DIV.pin2", "C_TACH.pin2",
                "J1_VIN.P2", "J2_FAN.P1", "J3_DIAL.P3", "J4_OLED.P1", "J5_BTN.P2",
                "J6_CHG.P2", "J7_BENCH.P2", "TP_GND.TP"],
        "VIN": ["J1_VIN.P1", "C_BULK.pos", "R_DIV1.pin1", "TP_VIN.TP"],
        "V12": ["D_OR.A"],
        "V5RAW": ["D_5V.A"],
        "V5": ["D_5V.K", "U1.5V", "TP_5V.TP"],
        "FAN12": ["D_OR.K", "D_BENCH.K", "J2_FAN.P2", "TP_12V.TP"],
        "BENCH12": ["D_BENCH.A", "J7_BENCH.P1"],
        "V3": ["U1.3V3", "R_TACH.pin1", "D_CLAMP.K", "J3_DIAL.P1", "J4_OLED.P2", "TP_3V3.TP"],
        "BATT_SENSE": ["U1.GP26", "R_DIV1.pin2", "R_DIV2.pin1", "C_DIV.pin1"],
        "FAN_TACH": ["U1.GP14", "R_TACH.pin2", "C_TACH.pin1", "J2_FAN.P3"],
        "FAN_PWM": ["U1.GP15", "J2_FAN.P4"],
        "DIAL_WIPER": ["U1.GP27", "J3_DIAL.P2"],
        "OLED_SCL": ["U1.GP1", "J4_OLED.P3"],
        "OLED_SDA": ["U1.GP0", "J4_OLED.P4"],
        "CHG_STAT": ["U1.GP13", "R_STAT.pin2", "D_CLAMP.A"],
        "CHG_RAW": ["R_STAT.pin1", "J6_CHG.P1"],
        "SCR_BTN": ["U1.GP11", "J5_BTN.P1"],
    }
    for n, pins in extra.items():
        nets[n] += pins
    return dict(nets)


NETLIST = build_netlist()
NO_CONNECT = [f"U1.{p}" for p in ("GP29", "GP28", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7",
                                  "GP12", "GP10", "GP9", "GP8")]

# ---------------------------------------------------------------- the base
# Board coordinates -> base coordinates (models/fan_housing.scad: X across,
# +X = the dial side; Z front to back). Must match the header of
# electronics/pcb/carrier-psu.tsx.
BASE_DX, BASE_DZ = 42.0, 50.0
HOUSING = (ROOT / "models" / "fan_housing.scad").read_text()


def housing_value(name):
    """A plain number assigned in fan_housing.scad (`name = 12.5;`)."""
    m = re.search(rf"^{name}\s*=\s*([-\d.]+)\s*;", HOUSING, re.M)
    if not m:
        sys.exit(f"models/fan_housing.scad has no plain `{name} = <number>;`")
    return float(m.group(1))


BOSS_H = housing_value("carrier_boss_h")    # the plate's bosses: the board's underside, above the plate
BOARD_T = 1.6
TOP = BOSS_H + BOARD_T          # the board's top face, above the plate
ROOF = 31.0                     # base_inner_h


# The dial pot (fan_housing.scad pot_keepout): body + switch + terminals from
# X 44 to the +X wall, its axis 15.5 mm above the plate at Z 24, a 26 mm
# keep-out round it. It comes down to 2.5 mm above the plate, so the board
# can't pass under it, and near it parts must stay below its curve.
POT_X0, POT_Z, POT_AXIS, POT_R = 44.0, 24.0, 88.0 - 72.5, 13.0   # pot_y - base_floor = 15.5


def pot_bottom(dz):
    """The pot keep-out's underside, above the plate, at |Z - 24| = dz."""
    return POT_AXIS - math.sqrt(POT_R ** 2 - dz ** 2) if dz < POT_R else math.inf


def _base_floor():
    """Where the board may lie, in base coordinates (X, Z), from
    models/fan_housing.scad, each obstacle grown by 0.5 mm."""
    free = box(17.5, 3.0, 67.0, 97.0)                    # sled's +X side (X 17), inner walls
    free = free.difference(box(59.0, 0, 70, 11.0))       # +X corner bosses, full height
    free = free.difference(box(59.0, 89.0, 70, 100))
    # the pot, where it comes below the board's top face
    dz = math.sqrt(POT_R ** 2 - (POT_AXIS - (BOSS_H + BOARD_T)) ** 2) + 0.5
    free = free.difference(box(POT_X0 - 0.5, POT_Z - dz, 70, POT_Z + dz))
    return free


BASE_FLOOR = _base_floor()
# The bottom plate's own features (fan_housing.scad bottom_plate) that a boss
# under one of the board's holes must not land on: base X/Z.
PLATE_FEATURES = (
    [("vent slot", box(x - 1, 33, x + 1, 62)) for x in range(21, 42, 5)]
    + [("stick-on foot recess", Point(sx * 55, z).buffer(6)) for sx in (-1, 1) for z in (16, 84)]
    + [("corner screw countersink", Point(sx * 63.5, z).buffer(3.3)) for sx in (-1, 1) for z in (6.5, 93.5)]
    + [("zip-tie bridge", box(3, 89, 9, 97))]          # the one left, at (6, 93) along Z
)
BOSS_D = 5.0

# (name, region in base X/Z, the most a part may stand above the board's top)
HEADROOM = [
    ("USB-C charge socket", box(52.5, 39, 67.5, 53), 8.5 - TOP),
    ("button legs and wires", box(59, 62, 64, 70), 10.5 - TOP),
    ("button pocket column", box(64, 60, 67.5, 72), 9.5 - TOP),
    ("join boss + screw tip (50, 6)", box(46, 2, 54, 10), 31 - 8 - 2.5 - TOP),
    ("join boss + screw tip (38, 30)", box(34, 26, 42, 34), 31 - 8 - 2.5 - TOP),
    ("rear screw head (54, 86)", Point(54, 86).buffer(3), 31 - 2.5 - TOP),
    ("roof", box(-70, 0, 70, 100), ROOF - TOP),
]
# Height above the board's top, mated plugs and wire bends included.
PART_HEIGHT = [
    (r"^U1$", 4.5),             # RP2040-Zero: 1.0 PCB + USB-C receptacle
    (r"^U_[AB]$", 1.75),        # SOIC-8
    (r"^L_", 4.5),              # SWPA6045
    (r"^C_BULK$", 6.0),         # 6.3 x 5.8 electrolytic
    (r"^(CIN1|COUT1)_", 2.7),   # 1210
    (r"^(DC_|D_OR|D_BENCH|D_5V)", 2.5),  # SMA
    (r"^D_CLAMP$", 1.1),        # SOD-323
    (r"^J1_", 10.5),            # KF301, wires enter from the side
    (r"^J2_", 17.0),            # fan header with the fan's plug and its cable
    (r"^J[3-7]_", 15.0),        # JST-XH with its plug and wires
    (r"^TP_", 0.2),
    (r".", 1.35),               # 0805
]


def part_height(ref):
    for pat, h in PART_HEIGHT:
        if re.search(pat, ref):
            return h
    raise KeyError(ref)


# ---------------------------------------------------------------- Gerber
ARC_RES = 16


def _flash(ap, x, y):
    kind, p = ap
    if kind == "C":
        return Point(x, y).buffer(p[0] / 2, ARC_RES)
    if kind == "R":
        return box(x - p[0] / 2, y - p[1] / 2, x + p[0] / 2, y + p[1] / 2)
    if kind == "O":
        r = min(p[0], p[1]) / 2
        dx, dy = (p[0] / 2 - r, 0) if p[0] >= p[1] else (0, p[1] / 2 - r)
        return LineString([(x - dx, y - dy), (x + dx, y + dy)]).buffer(r, ARC_RES)
    if kind == "HORZPILL":      # tscircuit macros: total w, total h, circle d, offset
        w, h, d, o = p
        return unary_union([box(x - (w - d) / 2, y - h / 2, x + (w - d) / 2, y + h / 2),
                            Point(x - o, y).buffer(d / 2, ARC_RES), Point(x + o, y).buffer(d / 2, ARC_RES)])
    if kind == "VERTPILL":
        w, h, d, o = p
        return unary_union([box(x - w / 2, y - (h - d) / 2, x + w / 2, y + (h - d) / 2),
                            Point(x, y - o).buffer(d / 2, ARC_RES), Point(x, y + o).buffer(d / 2, ARC_RES)])
    if kind == "ROUNDRECT":     # corner radius, then the four corners
        r, pts = p[0], list(zip(p[1::2], p[2::2]))
        return Polygon([(x + a, y + b) for a, b in pts]).buffer(r, ARC_RES)
    raise ValueError(f"unsupported aperture {kind}")


class Obj:
    def __init__(self, kind, ap, dark, pts, geom):
        self.kind, self.ap, self.dark, self.pts, self.geom = kind, ap, dark, pts, geom


def read_gerber(path):
    """Draws, flashes and regions of one layer, in file order, with polarity."""
    text = path.read_text()
    blocks, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "%":
            j = text.index("%", i + 1)
            blocks.append(("x", text[i + 1:j]))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = text.index("*", i)
            blocks.append(("c", text[i:j]))
            i = j + 1
    dec, aps, objs = 6, {}, []
    ap = None
    dark, region, pts = True, False, []
    x = y = 0.0
    for kind, b in blocks:
        if kind == "x":
            for s in (t.strip() for t in b.split("*")):
                if s.startswith("FS"):
                    dec = int(re.match(r"FSLAX\d(\d)", s).group(1))
                elif s.startswith("MO") and s != "MOMM":
                    raise ValueError(f"{path.name}: units {s}")
                elif s.startswith("AD"):
                    m = re.match(r"ADD(\d+)([A-Za-z_]+),?(.*)", s)
                    vals = [float(v) for v in m.group(3).split("X")] if m.group(3) else []
                    aps[int(m.group(1))] = (m.group(2), vals)
                elif s.startswith("LP"):
                    dark = s == "LPD"
            continue
        if b.startswith("G04") or b in ("G01", "G75", "M02"):
            continue
        if b in ("G02", "G03", "G74") or b.startswith(("G02", "G03")):
            raise ValueError(f"{path.name}: arcs are not supported ({b})")
        if b == "G36":
            region, pts = True, []
            continue
        if b == "G37":
            if len(pts) >= 3:
                objs.append(Obj("region", None, dark, list(pts), Polygon(pts).buffer(0)))
            region, pts = False, []
            continue
        m = re.fullmatch(r"(?:G01)?D(\d+)", b)
        if m and int(m.group(1)) >= 10:
            ap = int(m.group(1))
            continue
        m = re.fullmatch(r"(?:G01)?(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])", b)
        if not m:
            raise ValueError(f"{path.name}: can't read '{b}'")
        nx = int(m.group(1)) / 10 ** dec if m.group(1) else x
        ny = int(m.group(2)) / 10 ** dec if m.group(2) else y
        op = m.group(3)
        if region:
            if op == "2":
                if len(pts) >= 3:
                    objs.append(Obj("region", None, dark, list(pts), Polygon(pts).buffer(0)))
                pts = [(nx, ny)]
            elif op == "1":
                pts = pts or [(x, y)]
                pts.append((nx, ny))
        elif op == "1":
            a = aps[ap]
            if a[0] == "C":
                g = LineString([(x, y), (nx, ny)]).buffer(a[1][0] / 2, ARC_RES) if (x, y) != (nx, ny) \
                    else _flash(a, x, y)
            else:
                g = unary_union([_flash(a, x, y), _flash(a, nx, ny)]).convex_hull
            objs.append(Obj("draw", a, dark, [(x, y), (nx, ny)], g))
        elif op == "3":
            objs.append(Obj("flash", aps[ap], dark, [(nx, ny)], _flash(aps[ap], nx, ny)))
        x, y = nx, ny
    return objs


def layer_image(objs):
    img, run, run_dark = Polygon(), [], None
    for o in objs + [None]:
        if o is None or (run_dark is not None and o.dark != run_dark):
            u = unary_union(run)
            img = img.union(u) if run_dark else img.difference(u)
            run = []
        if o is None:
            break
        run_dark = o.dark
        run.append(o.geom)
    return img


def read_drill(path):
    tools, holes, cur = {}, [], None
    plated = "NonPlated" not in path.read_text()
    for line in path.read_text().splitlines():
        line = line.strip()
        if m := re.fullmatch(r"T(\d+)C([\d.]+)", line):
            tools[int(m.group(1))] = float(m.group(2))
        elif m := re.fullmatch(r"T(\d+)", line):
            cur = int(m.group(1))
        elif m := re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line):
            holes.append({"x": float(m.group(1)), "y": float(m.group(2)), "d": tools[cur], "plated": plated})
    return holes


def polys(g):
    return [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


# ---------------------------------------------------------------- the design
class Board:
    def __init__(self, gerbers, circuit_json, placement=False):
        """placement: read the circuit JSON alone (a build with routing off),
        for the bodies and fit checks while parts are being placed."""
        self.layers = {}
        if not placement:
            for name in ("F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_SilkScreen", "B_SilkScreen", "Edge_Cuts"):
                self.layers[name] = read_gerber(gerbers / f"{name}.gbr")
            self.holes = read_drill(gerbers / "drill-L1-L2.drl") + read_drill(gerbers / "drill_npth.drl")
        cj = json.loads(circuit_json.read_text())
        by = defaultdict(list)
        for e in cj:
            by[e["type"]].append(e)
        self.cj = by
        board = by["pcb_board"][0]
        pts = board.get("outline") or [
            {"x": board["center"]["x"] + sx * board["width"] / 2, "y": board["center"]["y"] + sy * board["height"] / 2}
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        self.outline = Polygon([(p["x"], p["y"]) for p in pts])
        self.thickness = board.get("thickness")
        names = {e["source_component_id"]: e["name"] for e in by["source_component"]}
        sport = {e["source_port_id"]: e for e in by["source_port"]}
        pport = {e["pcb_port_id"]: e for e in by["pcb_port"]}
        # (hand-placed vias appear as pcb_components with no source component)
        self.comp_ref = {e["pcb_component_id"]: names[e["source_component_id"]] for e in by["pcb_component"]
                         if e["source_component_id"] in names}
        self.comp_center = {self.comp_ref[e["pcb_component_id"]]: (e["center"]["x"], e["center"]["y"])
                            for e in by["pcb_component"] if e["pcb_component_id"] in self.comp_ref}
        self.pads = []          # dict(pin, x, y, layers, geom)
        for e in by["pcb_smtpad"] + by["pcb_plated_hole"]:
            sp = sport[pport[e["pcb_port_id"]]["source_port_id"]]
            pin = f"{names[sp['source_component_id']]}.{sp['name']}"
            if e["type"] == "pcb_smtpad":
                if e["shape"] == "circle":
                    g = Point(e["x"], e["y"]).buffer(e["radius"], ARC_RES)
                else:
                    g = box(e["x"] - e["width"] / 2, e["y"] - e["height"] / 2, e["x"] + e["width"] / 2, e["y"] + e["height"] / 2)
                    if e.get("ccw_rotation"):
                        g = affinity.rotate(g, e["ccw_rotation"], origin=(e["x"], e["y"]))
                layers = (e["layer"],)
            else:
                g = Point(e["x"], e["y"]).buffer(e["outer_diameter"] / 2, ARC_RES)
                layers = ("top", "bottom")
            self.pads.append({"pin": pin, "x": e["x"], "y": e["y"], "layers": layers, "geom": g})
        self.courtyards = defaultdict(list)
        for e in by["pcb_courtyard_rect"]:
            c = e["center"]
            g = box(c["x"] - e["width"] / 2, c["y"] - e["height"] / 2, c["x"] + e["width"] / 2, c["y"] + e["height"] / 2)
            if e.get("ccw_rotation"):
                g = affinity.rotate(g, e["ccw_rotation"], origin=(c["x"], c["y"]))
            self.courtyards[self.comp_ref[e["pcb_component_id"]]].append(g)
        for e in by.get("pcb_courtyard_outline", []):
            self.courtyards[self.comp_ref[e["pcb_component_id"]]].append(
                Polygon([(p["x"], p["y"]) for p in e["outline"]]))
        self.silk_text = by["pcb_silkscreen_text"]
        if placement:
            self.holes = [{"x": e["x"], "y": e["y"], "d": e["hole_diameter"], "plated": False} for e in by["pcb_hole"]]
            self.holes += [{"x": e["x"], "y": e["y"], "d": e["hole_diameter"], "plated": True}
                           for e in by["pcb_plated_hole"] + by["pcb_via"]]
            top = unary_union([p["geom"] for p in self.pads if "top" in p["layers"]])
            bottom = unary_union([p["geom"] for p in self.pads if "bottom" in p["layers"]])
            self.image = {"F_Cu": top, "B_Cu": bottom, "F_Mask": top, "B_Mask": bottom,
                          "F_SilkScreen": Polygon(), "B_SilkScreen": Polygon()}
        else:
            self.image = {k: layer_image(v) for k, v in self.layers.items() if k != "Edge_Cuts"}
        self.npth = [h for h in self.holes if not h["plated"]]

    def copy(self):
        return copy.deepcopy(self)


# ---------------------------------------------------------------- checks
def check_fab(b):
    bad = []
    edge = b.outline.exterior
    # tracks
    for L in ("F_Cu", "B_Cu"):
        thin = defaultdict(list)
        for o in b.layers[L]:
            if o.kind == "draw" and o.dark and o.ap[0] == "C" and o.ap[1][0] < RULES["min_track"] - 1e-6:
                thin[o.ap[1][0]].append(o.pts[0])
        for w, at in sorted(thin.items()):
            bad.append(f"{L}: {len(at)} track segment(s) {w} mm wide, e.g. at ({at[0][0]:.2f}, {at[0][1]:.2f})")
    # copper to copper, between nets (islands are nets once joined by holes)
    nets_of = island_nets(b)
    for L in ("F_Cu", "B_Cu"):
        isl = polys(b.image[L])
        tree = STRtree(isl)
        for i, g in enumerate(isl):
            for j in tree.query(g.buffer(RULES["min_space"])):
                if j <= i:
                    continue
                a, c = nets_of.get((L, i), set()), nets_of.get((L, int(j)), set())
                if a and c and a == c:
                    continue
                d = g.distance(isl[j])
                if d < RULES["min_space"] - 1e-6:
                    p = g.exterior.interpolate(g.exterior.project(isl[j].centroid))
                    bad.append(f"{L}: {d:.3f} mm between {'/'.join(sorted(a)) or '?'} and "
                               f"{'/'.join(sorted(c)) or '?'} near ({p.x:.2f}, {p.y:.2f})")
        if not b.image[L].is_empty:
            d = edge.distance(b.image[L])
            if d < RULES["edge"] - 1e-6:
                bad.append(f"{L}: copper {d:.3f} mm from the board edge")
            if not b.image[L].difference(b.outline.buffer(1e-3)).is_empty:
                bad.append(f"{L}: copper outside the board outline")
    # holes
    flashes = {L: [o for o in b.layers[L] if o.kind == "flash" and o.dark and o.ap[0] == "C"] for L in ("F_Cu", "B_Cu")}
    for h in b.holes:
        if not h["plated"]:
            wall = Point(h["x"], h["y"]).buffer(h["d"] / 2, 64)
            for L in ("F_Cu", "B_Cu"):
                d = wall.exterior.distance(b.image[L]) if not wall.intersects(b.image[L]) else 0
                if d < RULES["npth"] - 1e-6:
                    bad.append(f"{L}: copper {d:.3f} mm from the unplated hole at ({h['x']}, {h['y']})")
            continue
        pads = [min(flashes[L], key=lambda o: (o.pts[0][0] - h["x"]) ** 2 + (o.pts[0][1] - h["y"]) ** 2, default=None)
                for L in ("F_Cu", "B_Cu")]
        for L, p in zip(("F_Cu", "B_Cu"), pads):
            if p is None or math.dist(p.pts[0], (h["x"], h["y"])) > 1e-3:
                bad.append(f"{L}: no round pad on the plated hole at ({h['x']}, {h['y']})")
                continue
            ring = (p.ap[1][0] - h["d"]) / 2
            via = h["d"] < 0.6
            if via and (h["d"] < RULES["via_drill"] - 1e-6 or p.ap[1][0] < RULES["via_pad"] - 1e-6):
                bad.append(f"via at ({h['x']}, {h['y']}): drill {h['d']} pad {p.ap[1][0]} "
                           f"(needs >= {RULES['via_drill']} / {RULES['via_pad']})")
            if ring < (RULES["via_ring"] if via else RULES["pth_ring"]) - 1e-6:
                bad.append(f"{L}: annular ring {ring:.3f} mm at ({h['x']}, {h['y']})")
    for a, c in itertools.combinations(b.holes, 2):
        gap = math.dist((a["x"], a["y"]), (c["x"], c["y"])) - a["d"] / 2 - c["d"] / 2
        lim = RULES["hole_gap"]
        if a["d"] < 0.6 and c["d"] < 0.6 and same_net_holes(b, a, c):
            lim = RULES["via_gap_same_net"]
        if gap < lim - 1e-6:
            bad.append(f"holes {gap:.3f} mm apart at ({a['x']}, {a['y']}) and ({c['x']}, {c['y']})")
    # mask: every pad open, every via covered
    for L, M in (("F_Cu", "F_Mask"), ("B_Cu", "B_Mask")):
        mask = b.image[M]
        side = "top" if L == "F_Cu" else "bottom"
        for p in b.pads:
            if side in p["layers"] and not mask.buffer(1e-3).covers(Point(p["x"], p["y"])):
                bad.append(f"{M}: pad {p['pin']} is covered")
        for h in b.holes:
            if h["plated"] and h["d"] < 0.6 and mask.intersects(Point(h["x"], h["y"]).buffer(h["d"] / 2)):
                bad.append(f"{M}: the via at ({h['x']}, {h['y']}) is not tented")
    # silkscreen
    inner = b.outline.buffer(-RULES["silk_to_edge"])
    for S, M in (("F_SilkScreen", "F_Mask"), ("B_SilkScreen", "B_Mask")):
        for o in b.layers[S]:
            if o.kind == "draw" and o.ap[0] == "C" and o.ap[1][0] < RULES["silk_line"] - 1e-6:
                bad.append(f"{S}: line {o.ap[1][0]} mm wide at ({o.pts[0][0]:.2f}, {o.pts[0][1]:.2f})")
                break
        silk = b.image[S]
        if not silk.is_empty:
            out = silk.difference(inner)
            if out.area > 1e-3:
                c = out.centroid
                bad.append(f"{S}: {out.area:.2f} mm2 of silk off the board or within "
                           f"{RULES['silk_to_edge']} mm of its edge, near ({c.x:.1f}, {c.y:.1f})")
            on_pads = silk.intersection(b.image[M])
            for g in polys(on_pads):
                if g.area > 0.01:
                    bad.append(f"{S}: silk over an exposed pad near ({g.centroid.x:.2f}, {g.centroid.y:.2f})")
            for h in b.holes:          # (tented vias may sit under silk)
                if h["d"] < 0.6 and h["plated"]:
                    continue
                if silk.intersects(Point(h["x"], h["y"]).buffer(h["d"] / 2)):
                    bad.append(f"{S}: silk over the hole at ({h['x']}, {h['y']})")
    for t in b.silk_text:
        if t["font_size"] * TEXT_CAP < RULES["silk_text_cap"] - 1e-6:
            bad.append(f"silk text '{t['text']}' is {t['font_size'] * TEXT_CAP:.2f} mm tall")
    if b.thickness is not None and abs(b.thickness - BOARD_T) > 1e-6:
        bad.append(f"board thickness {b.thickness} mm in the design, {BOARD_T} expected")
    return bad


def island_nets(b):
    """(layer, island index) -> the nets of the pins whose pads sit on it."""
    pin_net = {p: n for n, ps in NETLIST.items() for p in ps}
    out = defaultdict(set)
    groups = connectivity(b)
    for p in b.pads:
        k = groups["pad"].get(p["pin"] + f"@{p['x']:.3f},{p['y']:.3f}")
        if k is None:
            continue
        for key in groups["members"][k]:
            if p["pin"] in pin_net:
                out[key].add(pin_net[p["pin"]])
    return out


_conn_cache = {}


def connectivity(b):
    key = id(b)
    if key in _conn_cache:
        return _conn_cache[key]
    isl = {L: polys(b.image[L]) for L in ("F_Cu", "B_Cu")}
    trees = {L: STRtree(isl[L]) for L in isl}
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, c):
        parent[find(a)] = find(c)

    for L in isl:
        for i in range(len(isl[L])):
            find((L, i))
    for h in b.holes:
        if not h["plated"]:
            continue
        ring = Point(h["x"], h["y"]).buffer(h["d"] / 2 + 0.01).exterior
        hits = [(L, int(i)) for L in isl for i in trees[L].query(ring) if isl[L][i].intersects(ring)]
        for k in hits[1:]:
            union(hits[0], k)
    pad_group = {}
    for p in b.pads:
        pt = Point(p["x"], p["y"])
        for side, L in (("top", "F_Cu"), ("bottom", "B_Cu")):
            if side in p["layers"]:
                hits = [int(i) for i in trees[L].query(pt) if isl[L][i].covers(pt)]
                if hits:
                    pad_group[p["pin"] + f"@{p['x']:.3f},{p['y']:.3f}"] = find((L, hits[0]))
                    break
    members = defaultdict(list)
    for k in list(parent):
        members[find(k)].append(k)
    res = {"pad": pad_group, "members": members, "isl": isl}
    _conn_cache[key] = res
    return res


def same_net_holes(b, a, c):
    """Whether the copper round two plated holes is one piece."""
    groups = connectivity(b)
    isl = groups["isl"]["F_Cu"]
    found = []
    for h in (a, c):
        ring = Point(h["x"], h["y"]).buffer(h["d"] / 2 + 0.01).exterior
        hit = next((i for i, g in enumerate(isl) if g.intersects(ring)), None)
        found.append(None if hit is None else
                     next(k for k, ms in groups["members"].items() if ("F_Cu", hit) in ms))
    return found[0] is not None and found[0] == found[1]


def check_nets(b):
    bad = []
    pin_net = {}
    for n, ps in NETLIST.items():
        for p in ps:
            if p in pin_net:
                bad.append(f"NETLIST lists {p} twice")
            pin_net[p] = n
    for p in NO_CONNECT:
        pin_net[p] = None
    groups = connectivity(b)
    seen_pins = set()
    by_group = defaultdict(list)
    for p in b.pads:
        seen_pins.add(p["pin"])
        if p["pin"] not in pin_net:
            bad.append(f"pad {p['pin']} is not in NETLIST or NO_CONNECT")
            continue
        g = groups["pad"].get(p["pin"] + f"@{p['x']:.3f},{p['y']:.3f}")
        if g is None:
            bad.append(f"pad {p['pin']} has no copper under its centre")
            continue
        by_group[g].append(p["pin"])
    for p in pin_net:
        if p not in seen_pins:
            bad.append(f"{p} is in the netlist but has no pad")
    net_groups = defaultdict(set)
    for g, pins in by_group.items():
        nets = {pin_net[p] for p in pins}
        named = {n for n in nets if n}
        if len(named) > 1:
            bad.append(f"short: {', '.join(sorted(named))} share copper ({', '.join(sorted(pins))})")
        if None in nets and len(pins) > 1:
            bad.append(f"a no-connect pin shares copper: {', '.join(sorted(pins))}")
        for n in named:
            net_groups[n].add(g)
    for n, gs in sorted(net_groups.items()):
        if len(gs) > 1:
            parts = [sorted(p for p in by_group[g] if pin_net.get(p) == n) for g in gs]
            bad.append(f"open: {n} is in {len(gs)} pieces: " + " | ".join(", ".join(x) for x in parts))
    return bad


def check_bodies(b):
    bad = []
    refs = sorted({p["pin"].split(".")[0] for p in b.pads})
    for r in refs:
        if not b.courtyards.get(r):
            bad.append(f"{r} has no courtyard")
    cy = {r: unary_union(g) for r, g in b.courtyards.items()}
    for (r1, g1), (r2, g2) in itertools.combinations(sorted(cy.items()), 2):
        o = g1.intersection(g2)
        if o.area > 1e-3:
            x0, y0, x1, y1 = o.bounds
            bad.append(f"{r1} and {r2} overlap by {x1 - x0:.2f} x {y1 - y0:.2f} mm")
    mask = b.image["F_Mask"]
    for h in b.npth:
        head = Point(h["x"], h["y"]).buffer(SCREW_HEAD_D / 2, 64)
        for r, g in cy.items():
            if head.intersection(g).area > 1e-3:
                bad.append(f"the M2 head at ({h['x']}, {h['y']}) sits on {r}")
        if head.intersects(mask.difference(Point(h["x"], h["y"]).buffer(h["d"] / 2 + 0.01))):
            bad.append(f"the M2 head at ({h['x']}, {h['y']}) touches an exposed pad")
        if not b.outline.buffer(-0.2).contains(head):
            bad.append(f"the M2 head at ({h['x']}, {h['y']}) overhangs the board edge")
    for r, g in cy.items():
        if not b.outline.buffer(0.5).contains(g):
            bad.append(f"{r}'s courtyard runs more than 0.5 mm past the board edge")
    return bad


def to_base(g):
    return affinity.translate(g, BASE_DX, BASE_DZ)


def check_fit(b):
    bad = []
    outline = to_base(b.outline)
    out = outline.difference(BASE_FLOOR)
    if out.area > 1e-3:
        x0, z0, x1, z1 = out.bounds
        bad.append(f"the board runs {out.area:.1f} mm2 into the base's obstacles "
                   f"(base X {x0:.1f}..{x1:.1f}, Z {z0:.1f}..{z1:.1f})")
    for r, gs in sorted(b.courtyards.items()):
        g = to_base(unary_union(gs))
        h = part_height(r)
        for name, region, limit in HEADROOM:
            if h > limit + 1e-6 and g.intersects(region) and g.intersection(region).area > 1e-3:
                bad.append(f"{r} ({h} mm tall) under the {name}, which leaves {limit:.1f} mm")
        # under the pot's curve: the part's nearest point to the pot's axis
        x0, z0, x1, z1 = g.bounds
        if x1 > POT_X0 - 0.5:
            dz = 0 if z0 <= POT_Z <= z1 else min(abs(z0 - POT_Z), abs(z1 - POT_Z))
            room = pot_bottom(dz) - TOP
            if h > room + 1e-6:
                bad.append(f"{r} ({h} mm tall) under the dial pot, which leaves {max(room, 0):.1f} mm")
    for h in b.npth:
        boss = Point(h["x"] + BASE_DX, h["y"] + BASE_DZ).buffer(BOSS_D / 2)
        for name, region in PLATE_FEATURES:
            if boss.intersects(region):
                bad.append(f"the boss under the hole at ({h['x']}, {h['y']}) lands on the plate's {name}")
    # the Zero's USB-C at the rear wall's cutout (fan_housing.scad: zero_usb_x)
    if "U1" in b.comp_center:
        x, y = b.comp_center["U1"]
        pads = [p for p in b.pads if p["pin"].startswith("U1.")]
        xs = [p["x"] for p in pads if p["pin"] in ("U1.5V", "U1.GP0")]
        cx = sum(xs) / len(xs) if xs else x
        zero_top = max(p["y"] for p in pads if p["pin"] in ("U1.5V", "U1.GP0")) + 1.59
        if abs(cx + BASE_DX - zero_usb_x()) > 0.25:
            bad.append(f"the Zero's USB-C is at base X {cx + BASE_DX:.2f}, the rear cutout at {zero_usb_x()}")
        rear = b.outline.bounds[3]
        if abs(zero_top - rear) > 0.3:
            bad.append(f"the Zero's top edge is {rear - zero_top:.2f} mm in from the board's rear edge")
    return bad


def zero_usb_x():
    return housing_value("zero_usb_x")      # the rear wall's cutout for the Zero's USB-C

CHECKS = [
    ("fab", check_fab, "JLCPCB 2-layer rules with margin: tracks, clearance, edge, holes, rings, mask, silk"),
    ("nets", check_nets, "the copper joins exactly the pins in NETLIST (no opens, no shorts)"),
    ("bodies", check_bodies, "no two parts overlap; M2 heads clear of parts and pads"),
    ("fit", check_fit, "the board fits the base's free floor; parts clear what hangs above them"),
]


# ---------------------------------------------------------------- self-test
def _bridge(b, p1, p2, layer="F_Cu"):
    """Add copper joining two pads, as a short would."""
    a = next(p for p in b.pads if p["pin"] == p1)
    c = next(p for p in b.pads if p["pin"] == p2)
    g = LineString([(a["x"], a["y"]), (c["x"], c["y"])]).buffer(0.3)
    b.layers[layer].append(Obj("draw", ("C", [0.6]), True, [(a["x"], a["y"])], g))
    b.image[layer] = b.image[layer].union(g)


def _cut(b, pin):
    """Clear the copper round one pad: an open."""
    p = next(p for p in b.pads if p["pin"] == pin)
    ring = p["geom"].buffer(0.6).difference(p["geom"].buffer(0.05))
    for L in ("F_Cu", "B_Cu"):
        b.image[L] = b.image[L].difference(ring)


def _thin_via(b):
    v = next(h for h in b.holes if h["plated"] and h["d"] < 0.6)
    v["d"] = 0.2


def _thin_silk(b):
    b.layers["F_SilkScreen"].append(Obj("draw", ("C", [0.1]), True, [(0, 0), (1, 0)], LineString([(0, 0), (1, 0)]).buffer(0.05)))


def _move_courtyard(b):
    refs = sorted(b.courtyards)
    a, c = refs[0], refs[1]
    ca = unary_union(b.courtyards[a]).centroid
    cc = unary_union(b.courtyards[c]).centroid
    b.courtyards[a] = [affinity.translate(g, cc.x - ca.x, cc.y - ca.y) for g in b.courtyards[a]]


def _grow_outline(b):
    x0, y0, x1, y1 = b.outline.bounds
    b.outline = b.outline.union(box(x1 - 1, y0, x1 + 12, y1))


SELF_TEST = {
    "fab": [("a 0.2 mm via", _thin_via), ("a 0.1 mm silk line", _thin_silk)],
    "nets": [("VIN bridged to GND", lambda b: _bridge(b, "J1_VIN.P1", "J1_VIN.P2")),
             ("FAN_PWM cut at the header", lambda b: _cut(b, "J2_FAN.P4"))],
    "bodies": [("one part moved onto another", _move_courtyard)],
    "fit": [("the board 12 mm wider at +X", _grow_outline)],
}


# ---------------------------------------------------------------- scad
def write_scad(b, path):
    outline = [(round(x + BASE_DX, 3), round(y + BASE_DZ, 3)) for x, y in list(b.outline.exterior.coords)[:-1]]
    holes = [(round(h["x"] + BASE_DX, 3), round(h["y"] + BASE_DZ, 3)) for h in b.npth]
    parts = []
    for r, gs in sorted(b.courtyards.items()):
        x0, y0, x1, y1 = unary_union(gs).bounds
        parts.append((round(x0 + BASE_DX, 3), round(y0 + BASE_DZ, 3), round(x1 + BASE_DX, 3),
                      round(y1 + BASE_DZ, 3), part_height(r), r))
    fmt = lambda v: "[" + ", ".join(fmt(x) if isinstance(x, (list, tuple)) else
                                    (f'"{x}"' if isinstance(x, str) else f"{x:g}") for x in v) + "]"
    text = f"""// Generated by tools/check_pcb.py --write-scad from the PCB build
// (electronics/pcb/carrier-psu.tsx). Do not edit: change the board, rebuild,
// and run the tool again. Base coordinates: X across (+X = dial side), Z
// front to back, as in fan_housing.scad.

carrier_pcb_t = {BOARD_T:g};
carrier_pcb_outline = {fmt(outline)};
carrier_pcb_holes = {fmt(holes)};         // M2, through the board into the plate's bosses
// each part's courtyard (X0, Z0, X1, Z1) and its height above the board
carrier_pcb_parts = {fmt([list(p) for p in parts])};
"""
    path.write_text(text)


# ---------------------------------------------------------------- render
def render(b, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def patch(g, **kw):
        v, c = [], []
        for p in polys(g):
            for ring in [p.exterior, *p.interiors]:
                xy = list(ring.coords)
                v += xy
                c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
        return PathPatch(MPath(v, c), **kw) if v else None

    fig, axs = plt.subplots(1, 2, figsize=(14, 13), dpi=150)
    inv = lambda g: affinity.translate(g, -BASE_DX, -BASE_DZ)
    for ax, (L, col) in zip(axs, (("F_Cu", "#c83737"), ("B_Cu", "#3765c8"))):
        for g, kw in ((inv(box(-70, 0, 70, 100)).difference(inv(BASE_FLOOR)), dict(fc="#ffd9a8", ec="none")),
                      (b.image[L], dict(fc=col, ec="none", alpha=0.8))):
            p = patch(g, **kw)
            if p:
                ax.add_patch(p)
        for name, region, limit in HEADROOM[:-1]:
            p = patch(inv(region), fc="none", ec="#d07000", ls="--", lw=0.7)
            if p:
                ax.add_patch(p)
        if L == "F_Cu":
            p = patch(b.image["F_SilkScreen"], fc="k", ec="none")
            if p:
                ax.add_patch(p)
            for r, gs in b.courtyards.items():
                p = patch(unary_union(gs), fc="none", ec="#444", lw=0.5)
                if p:
                    ax.add_patch(p)
                c = unary_union(gs).centroid
                ax.text(c.x, c.y, r, fontsize=4.5, ha="center", va="center", color="#003")
        for h in b.holes:
            ax.add_patch(plt.Circle((h["x"], h["y"]), h["d"] / 2, fc="w", ec="k" if h["plated"] else "m", lw=0.3))
        x, y = b.outline.exterior.xy
        ax.plot(x, y, "k-", lw=0.8)
        x0, y0, x1, y1 = b.outline.bounds
        ax.set_xlim(x0 - 3, x1 + 9)
        ax.set_ylim(y0 - 3, y1 + 3)
        ax.set_aspect("equal")
        ax.set_title(f"{L} (orange: the base's obstacles; dashed: limited headroom)", fontsize=8)
    fig.tight_layout()
    fig.savefig(path)


# ---------------------------------------------------------------- assembly drawing
def _value(e):
    """A source component's value, as printed on the drawing."""
    def eng(v, unit):
        for s, f in (("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
            if abs(v) >= f * 0.999:
                return f"{v / f:.3g}{s}{unit}"
        return f"{v:g}{unit}"
    if "resistance" in e:
        return eng(e["resistance"], "")
    if "capacitance" in e:
        return eng(e["capacitance"], "F")
    return e.get("manufacturer_part_number") or ""


def assembly(b, path):
    """Top view for hand assembly: pads, the silkscreen's polarity marks, each
    part's outline with its reference and value. The silk carries no
    references, so this is the map."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def patch(g, **kw):
        v, c = [], []
        for p in polys(g):
            for ring in [p.exterior, *p.interiors]:
                xy = list(ring.coords)
                v += xy
                c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
        return PathPatch(MPath(v, c), **kw) if v else None

    src = {e["name"]: e for e in b.cj["source_component"]}
    x0, y0, x1, y1 = b.outline.bounds
    scale = 0.25                                       # inches of figure per mm of board: 6.35 x
    fig = plt.figure(figsize=((x1 - x0 + 2) * scale, (y1 - y0 + 2) * scale), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    for g, kw in ((b.outline, dict(fc="#f4f4ee", ec="k", lw=1.2)),
                  (b.image["F_Mask"], dict(fc="#d9b44a", ec="none")),
                  (b.image["F_SilkScreen"], dict(fc="#222", ec="none"))):
        p = patch(g, **kw)
        if p:
            ax.add_patch(p)
    for h in b.holes:
        ax.add_patch(plt.Circle((h["x"], h["y"]), h["d"] / 2, fc="w", ec="#555", lw=0.6))
    for r, gs in sorted(b.courtyards.items()):
        g = unary_union(gs)
        p = patch(g, fc="none", ec="#3060c0", lw=0.8, ls="--")
        if p:
            ax.add_patch(p)
        gx0, gy0, gx1, gy1 = g.bounds
        w, h = gx1 - gx0, gy1 - gy0
        tall = h > w * 1.3
        size = max(5.0, min(14.0, (min(w, h) if not tall else min(w, h)) * 3.2))
        val = _value(src.get(r, {}))
        text = r if not val or r.startswith(("U1", "J", "TP_")) else f"{r}\n{val}"
        ax.text((gx0 + gx1) / 2, (gy0 + gy1) / 2, text, fontsize=size, ha="center", va="center",
                rotation=90 if tall else 0, color="#002a7a", fontweight="bold", linespacing=0.95,
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    ax.text(x0 + 0.5, y0 - 0.6, "Carrier + PSU v2: top side, parts by reference. Gold: pads. Black: the "
            "silkscreen (cathode bars, pin-1 triangles, +).", fontsize=9, va="top")
    ax.set_xlim(x0 - 1, x1 + 1)
    ax.set_ylim(y0 - 1, y1 + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path)


# ---------------------------------------------------------------- main
def run(b, quiet=False, only=None):
    failed = 0
    for name, fn, what in CHECKS:
        if only and name not in only:
            continue
        bad = fn(b)
        if not quiet:
            print(f"{name:7s} {'PASS' if not bad else 'FAIL':5s} {what}")
            for line in bad[:40]:
                print(f"          - {line}")
            if len(bad) > 40:
                print(f"          ... and {len(bad) - 40} more")
        failed += bool(bad)
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gerbers", type=Path, default=GERBERS)
    ap.add_argument("--circuit-json", type=Path, default=CIRCUIT_JSON)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write-scad", nargs="?", const=SCAD_OUT, type=Path)
    ap.add_argument("--render", type=Path)
    ap.add_argument("--assembly", type=Path)
    ap.add_argument("--placement", action="store_true",
                    help="bodies and fit only, from the circuit JSON of a build with routing off")
    args = ap.parse_args()
    if not args.circuit_json.exists():
        sys.exit(f"{args.circuit_json} is missing: build the board first (electronics/pcb/README.md)")
    b = Board(args.gerbers, args.circuit_json, placement=args.placement)
    if args.write_scad:
        write_scad(b, args.write_scad)
        print(f"wrote {args.write_scad.relative_to(ROOT) if args.write_scad.is_absolute() else args.write_scad}")
    if args.render:
        render(b, args.render)
        print(f"wrote {args.render}")
    if args.assembly:
        assembly(b, args.assembly)
        print(f"wrote {args.assembly}")
    if args.self_test:
        missed = 0
        for name, fn, _ in CHECKS:
            for label, mutate in SELF_TEST[name]:
                m = b.copy()
                _conn_cache.clear()
                mutate(m)
                caught = bool(fn(m))
                print(f"{name:7s} {'caught' if caught else 'MISSED':7s} {label}")
                missed += not caught
        _conn_cache.clear()
        print(f"\n{missed} breakage(s) missed")
        sys.exit(1 if missed else 0)
    failed = run(b, only=("bodies", "fit") if args.placement else None)
    print(f"\n{failed} check(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
