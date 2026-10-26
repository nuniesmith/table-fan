#!/usr/bin/env python3
"""Checks for the carrier + PSU board (electronics/pcb).

Reads the Gerber set in electronics/pcb/gerber/ and the circuit JSON that
`tsci build` writes (electronics/pcb/dist/carrier-psu/circuit.json), and
prints PASS/FAIL for:
  fab    - JLCPCB 2-layer standard rules, with margin: via drill and pad,
           annular rings, copper clearance between nets, no copper slivers,
           copper to the board edge (read from Edge_Cuts, which must match
           the build) and to unplated holes, hole spacing, silkscreen line
           width, text height (measured in the Gerber) and its clearance to
           pads, solder mask over every via, paste only on pads and clear of
           their holes
  nets   - the copper, read from the Gerbers, joins exactly the pins in
           NETLIST below and nothing else (no opens, no shorts). NETLIST is
           written out by hand from the design notes, not taken from the
           .tsx, so a wrong connection in the source shows up here
  bodies - no two parts' courtyards overlap, and no part sits under an M2
           screw head
  fit    - the board maps onto the base turned, not mirrored, with its parts
           on top; the outline lies on the base's free floor (clear of the
           sled, the corner bosses and the dial pot), and every part is low
           enough for what hangs above it (USB-C socket, button, join bosses)

    python3 tools/check_pcb.py                  # run everything
    python3 tools/check_pcb.py --self-test      # break each check on purpose
    python3 tools/check_pcb.py --write-scad     # regenerate models/carrier_pcb.scad
    python3 tools/check_pcb.py --render out.png # the board, its parts and the base around it
    python3 tools/check_pcb.py --assembly electronics/pcb/assembly.png  # the hand-assembly map
    python3 tools/check_pcb.py --clean IN.json OUT.json  # pours and paste, for export (npm run gerbers)

Build first (see electronics/pcb/README.md). Needs shapely 2 (pip install
shapely); --render and --assembly also need matplotlib. Exit status 1 if
anything fails.

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
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "electronics" / "pcb"
GERBERS = PCB / "gerber"
CIRCUIT_JSON = PCB / "dist" / "carrier-psu" / "circuit.json"
SCAD_OUT = ROOT / "models" / "carrier_pcb.scad"

# ---------------------------------------------------------------- rules
# JLCPCB's 2-layer minimums are 0.127 mm trace and space, 0.3 mm via drill
# with a 0.5 mm via pad, 0.2 mm copper to a routed edge, 0.153 mm silk lines,
# 1 mm text and 0.15 mm silk to a pad. The vias here are at those minimums;
# the rest are stricter, so a board that passes has margin at the fab.
RULES = {
    "min_track": 0.2,           # copper drawn with a round aperture (traces)
    "min_copper": 0.15,         # any copper feature's width (pours included)
    "min_space": 0.15,          # copper of one net to copper of another
    "min_slit": 0.15,           # any gap in the copper, one net's own included
    "via_drill": 0.3,
    "via_pad": 0.5,
    "via_ring": 0.15,           # (pad - drill) / 2
    "pth_ring": 0.25,
    "hole_gap": 0.5,            # hole wall to hole wall
    "via_gap_same_net": 0.25,
    "edge": 0.3,                # copper to the board outline
    "npth": 0.3,                # copper to an unplated hole's wall
    "silk_line": 0.15,
    "silk_text": 1.0,           # text height, stroke included, measured in the Gerber
    "silk_to_pad": 0.15,        # silk to an opening in the mask (JLCPCB clips closer silk)
    "silk_to_edge": 0.2,
    "via_to_opening": 0.1,      # a tented via's pad to an opening in the mask
}
POUR_MIN_WIDTH = 0.2            # --clean removes pour copper narrower than this
POUR_CLEARANCE = 0.32           # the pours' clearance to other nets (carrier-psu.tsx)
SCREW_HEAD_D = 4.2              # M2 pan head (3.8-4.0) and a little play

# ---------------------------------------------------------------- netlist
# What each pin must connect to. Pins are REF.PIN with PIN the source port
# name (pin1/pin2 on resistors and capacitors). Every pad on the board must
# appear here or in NO_CONNECT.
def _buck(t, vout):
    s = lambda n: f"{n}_{t}"
    return {
        "GND": [f"U_{t}.GND", f"U_{t}.EP", f"U_{t}.GNDB", f"CIN1_{t}.pin2", f"CIN2_{t}.pin2",
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
                "J6_CHG.P2", "J7_BENCH.P2", "TP_GND.TP", "R_GATE.pin2"],
        "VPACK": ["J1_VIN.P1", "Q_RP.D"],
        "VIN": ["Q_RP.S", "D_GZ.K", "C_BULK.pos", "R_DIV1.pin1", "TP_VIN.TP"],
        "Q_GATE": ["Q_RP.G", "D_GZ.A", "R_GATE.pin1"],
        "V12": ["D_OR.A"],
        "V5RAW": ["D_5V.A"],
        "V5": ["D_5V.K", "U1.5V", "TP_5V.TP"],
        "FAN12": ["D_OR.K", "D_BENCH.K", "J2_FAN.P2", "TP_12V.TP"],
        "BENCH12": ["D_BENCH.A", "J7_BENCH.P1"],
        "V3": ["U1.3V3", "R_TACH.pin1", "D_CLAMP.K", "J3_DIAL.P1", "J4_OLED.P2", "TP_3V3.TP",
               "R_SCL.pin1", "R_SDA.pin1"],
        "BATT_SENSE": ["U1.GP26", "R_DIV1.pin2", "R_DIV2.pin1", "C_DIV.pin1"],
        "FAN_TACH": ["U1.GP14", "R_TACH.pin2", "C_TACH.pin1", "J2_FAN.P3"],
        "FAN_PWM": ["U1.GP15", "J2_FAN.P4"],
        "DIAL_WIPER": ["U1.GP27", "J3_DIAL.P2"],
        "OLED_SCL": ["U1.GP1", "J4_OLED.P3", "R_SCL.pin2"],
        "OLED_SDA": ["U1.GP0", "J4_OLED.P4", "R_SDA.pin2"],
        "CHG_STAT": ["U1.GP13", "R_STAT.pin2", "D_CLAMP.A"],
        "CHG_RAW": ["R_STAT.pin1", "J6_CHG.P1"],
        "SCR_BTN": ["U1.GP11", "J5_BTN.P1"],
    }
    for n, pins in extra.items():
        nets[n] += pins
    nets["BST_A"].append("D_BST_A.K")       # buck A's bootstrap diode, from the 5 V rail
    nets["V5RAW"].append("D_BST_A.A")
    return dict(nets)


NETLIST = build_netlist()
NO_CONNECT = [f"U1.{p}" for p in ("GP29", "GP28", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7",
                                  "GP12", "GP10", "GP9", "GP8")]

# ---------------------------------------------------------------- the base
# Board coordinates -> base coordinates (models/fan_housing.scad: X across,
# +X = the dial side, Y up, Z front to back). The base's frame is right-handed
# with Y up, so seen from above with its rear wall up, +X is on the LEFT. The
# Gerbers are the board seen from its top, +x to the right, and the parts are
# on top: board +x is base -X, board +y is base +Z. Mapping +x to +X would
# mirror the board (v2 did; check_fit tests the handedness). Must match the
# header of electronics/pcb/carrier-psu.tsx.
BASE_X0, BASE_Z0 = 42.0, 50.0
BASE_MAP = (-1.0, BASE_X0, BASE_Z0)          # X = sx * x + X0, Z = y + Z0
HOUSING = (ROOT / "models" / "fan_housing.scad").read_text()


def housing_value(name):
    """A plain number assigned in fan_housing.scad (`name = 12.5;`)."""
    m = re.search(rf"^{name}\s*=\s*([-\d.]+)\s*;", HOUSING, re.M)
    if not m:
        sys.exit(f"models/fan_housing.scad has no plain `{name} = <number>;`")
    return float(m.group(1))


def housing_list(name):
    """A plain list of numbers assigned in fan_housing.scad (`name = [1, 2];`)."""
    m = re.search(rf"^{name}\s*=\s*\[([-\d.,\s]+)\]\s*;", HOUSING, re.M)
    if not m:
        sys.exit(f"models/fan_housing.scad has no plain `{name} = [<numbers>];`")
    return [float(v) for v in m.group(1).split(",")]


def to_base_xy(x, y, m=BASE_MAP):
    return (m[0] * x + m[1], y + m[2])


def to_base(g, m=BASE_MAP):
    return affinity.affine_transform(g, [m[0], 0, 0, 1, m[1], m[2]])


BOSS_H = housing_value("carrier_boss_h")    # the plate's bosses: the board's underside, above the plate
BOSS_D = housing_value("carrier_boss_d")
BOARD_T = 1.6
TOP = BOSS_H + BOARD_T          # the board's top face, above the plate
ROOF = housing_value("base_inner_h")
_BASE_FLOOR_Y = -housing_value("outer_width") / 2 - housing_value("base_top_t") - ROOF


# The dial pot (fan_housing.scad pot_keepout): body + switch + terminals from
# X 44 to the +X wall, its axis 15.5 mm above the plate at Z 24, a 26 mm
# keep-out round it. It comes down to 2.5 mm above the plate, so the board
# can't pass under it, and near it parts must stay below its curve.
POT_X0 = housing_value("outer_width") / 2 - housing_value("base_wall") - housing_value("pot_boss_t") \
    - housing_value("pot_body_depth")
POT_Z = housing_value("pot_z")
POT_AXIS = housing_value("pot_y") - _BASE_FLOOR_Y          # above the plate
POT_R = (housing_value("pot_body_d") + 2) / 2


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
_V = housing_list("plate_vents")              # X of the first and last slot (5 apart), Z0, Z1
PLATE_FEATURES = (
    [("vent slot", box(_V[0] + 5 * i - 1, _V[2], _V[0] + 5 * i + 1, _V[3]))
     for i in range(int(round((_V[1] - _V[0]) / 5)) + 1)]
    + [("stick-on foot recess", Point(sx * 55, z).buffer(6)) for sx in (-1, 1) for z in (16, 84)]
    + [("corner screw countersink", Point(sx * 63.5, z).buffer(3.3)) for sx in (-1, 1) for z in (6.5, 93.5)]
    + [("zip-tie bridge", box(3, 89, 9, 97))]          # the one left, at (6, 93) along Z
)

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
    (r"^D_(CLAMP|BST_|GZ)", 1.1),  # SOD-323
    (r"^Q_", 1.25),             # SOT-23
    (r"^J1_", 10.5),            # KF301, wires enter from the side
    (r"^J2_", 17.0),            # fan header with the fan's plug and its cable
    (r"^J[3-7]_", 15.0),        # JST-XH with its plug and wires
    (r"^TP_", 0.2),
    (r"^[RC]", 1.35),           # 0805 resistors and capacitors
]


def part_height(ref):
    for pat, h in PART_HEIGHT:
        if re.search(pat, ref):
            return h
    raise KeyError(f"{ref}: no height in PART_HEIGHT")


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


def edge_outline(objs):
    """The outline drawn in Edge_Cuts (the centre lines of its draws)."""
    segs = [LineString(o.pts) for o in objs if o.kind == "draw" and o.pts[0] != o.pts[1]]
    found = list(polygonize(unary_union(segs))) if segs else []
    return max(found, key=lambda g: g.area) if found else Polygon()


def slivers(img, width):
    """Copper narrower than `width`: what an opening (shrink, then grow back
    by width / 2) removes, kept where it is long and thin rather than a
    rounded-off corner. (length, mean width, centroid) for each."""
    r = width / 2
    thin = img.difference(img.buffer(-r, ARC_RES).buffer(r, ARC_RES).buffer(1e-4))
    out = []
    for g in polys(thin):
        length = g.length / 2               # half the perimeter: a strip's length, bent or not
        if length > 2 * width and g.area / length < 0.9 * width:
            out.append((length, g.area / length, g.centroid))
    return out


# ---------------------------------------------------------------- the design
class Board:
    def __init__(self, gerbers, circuit_json, placement=False):
        """placement: read the circuit JSON alone (a build with routing off),
        for the bodies and fit checks while parts are being placed."""
        self.layers = {}
        self.map = BASE_MAP
        if not placement:
            for name in ("F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Paste", "B_Paste", "F_SilkScreen",
                         "B_SilkScreen", "Edge_Cuts"):
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
        self.json_outline = Polygon([(p["x"], p["y"]) for p in pts])
        # the outline the fab gets: Edge_Cuts (fab checks it matches the build)
        self.outline = self.json_outline if placement else edge_outline(self.layers["Edge_Cuts"])
        self.thickness = board.get("thickness")
        names = {e["source_component_id"]: e["name"] for e in by["source_component"]}
        sport = {e["source_port_id"]: e for e in by["source_port"]}
        pport = {e["pcb_port_id"]: e for e in by["pcb_port"]}
        # (hand-placed vias appear as pcb_components with no source component)
        self.comp_ref = {e["pcb_component_id"]: names[e["source_component_id"]] for e in by["pcb_component"]
                         if e["source_component_id"] in names}
        self.comp_center = {self.comp_ref[e["pcb_component_id"]]: (e["center"]["x"], e["center"]["y"])
                            for e in by["pcb_component"] if e["pcb_component_id"] in self.comp_ref}
        self.part_layers = {e.get("layer", "top") for e in by["pcb_component"] if e["pcb_component_id"] in self.comp_ref}
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
            elif e.get("shape") == "circular_hole_with_rect_pad":
                g = box(e["x"] - e["rect_pad_width"] / 2, e["y"] - e["rect_pad_height"] / 2,
                        e["x"] + e["rect_pad_width"] / 2, e["y"] + e["rect_pad_height"] / 2)
                layers = ("top", "bottom")
            else:
                g = Point(e["x"], e["y"]).buffer(e["outer_diameter"] / 2, ARC_RES)
                layers = ("top", "bottom")
            masked = bool(e.get("is_covered_with_solder_mask") or e.get("covered_with_solder_mask"))
            self.pads.append({"pin": pin, "x": e["x"], "y": e["y"], "layers": layers, "geom": g, "masked": masked})
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
        self.silk_path_widths = {round(e.get("stroke_width", 0), 4) for e in by["pcb_silkscreen_path"]}
        if placement:
            self.holes = [{"x": e["x"], "y": e["y"], "d": e["hole_diameter"], "plated": False} for e in by["pcb_hole"]]
            self.holes += [{"x": e["x"], "y": e["y"], "d": e["hole_diameter"], "plated": True}
                           for e in by["pcb_plated_hole"] + by["pcb_via"]]
            top = unary_union([p["geom"] for p in self.pads if "top" in p["layers"]])
            bottom = unary_union([p["geom"] for p in self.pads if "bottom" in p["layers"]])
            self.image = {"F_Cu": top, "B_Cu": bottom, "F_Mask": top, "B_Mask": bottom, "F_Paste": Polygon(),
                          "B_Paste": Polygon(), "F_SilkScreen": Polygon(), "B_SilkScreen": Polygon()}
        else:
            self.image = {k: layer_image(v) for k, v in self.layers.items() if k != "Edge_Cuts"}
        self.npth = [h for h in self.holes if not h["plated"]]

    def copy(self):
        return copy.deepcopy(self)


# ---------------------------------------------------------------- checks
def text_strokes(b, t):
    """The silkscreen draws that make up one text: its stroke width (0.09 x
    the font size in tscircuit's font), near its anchor."""
    fs, a = t["font_size"], t["anchor_position"]
    w = round(0.09 * fs, 4)
    if any(abs(w - pw) < 2e-3 for pw in b.silk_path_widths):
        return [], 0                # a silk line's width: its strokes can't be told apart
    along, across = len(t["text"]) * fs * 0.36 + 0.3, 0.65 * fs     # half-sizes: ~0.64 x fs a letter
    rot = round(t.get("ccw_rotation") or 0) % 180
    hx, hy = (across, along) if rot == 90 else (along, across)
    area = box(a["x"] - hx, a["y"] - hy, a["x"] + hx, a["y"] + hy)
    layer = "F_SilkScreen" if t.get("layer", "top") == "top" else "B_SilkScreen"
    return [o for o in b.layers[layer] if o.kind == "draw" and o.ap[0] == "C" and abs(o.ap[1][0] - w) < 2e-3
            and area.contains(Point(o.pts[0])) and area.contains(Point(o.pts[-1]))], rot


def text_height(b, t):
    """A text's printed height, stroke included, from the Gerber (None if its
    strokes aren't there)."""
    objs, rot = text_strokes(b, t)
    if not objs:
        return None
    x0, y0, x1, y1 = unary_union([o.geom for o in objs]).bounds
    return x1 - x0 if rot == 90 else y1 - y0


def check_fab(b):
    bad = []
    if b.outline.is_empty:
        return ["Edge_Cuts holds no closed outline"]
    d = b.outline.symmetric_difference(b.json_outline).area
    if d > 1e-3:
        bad.append(f"Edge_Cuts differs from the build's outline by {d:.2f} mm2: export the Gerbers again")
    edge = b.outline.exterior
    # tracks
    for L in ("F_Cu", "B_Cu"):
        thin = defaultdict(list)
        for o in b.layers[L]:
            if o.kind == "draw" and o.dark and o.ap[0] == "C" and o.ap[1][0] < RULES["min_track"] - 1e-6:
                thin[o.ap[1][0]].append(o.pts[0])
        for w, at in sorted(thin.items()):
            bad.append(f"{L}: {len(at)} track segment(s) {w} mm wide, e.g. at ({at[0][0]:.2f}, {at[0][1]:.2f})")
        sl = slivers(b.image[L], RULES["min_copper"])
        for length, w, c in sorted(sl, key=lambda v: -v[0])[:5]:
            bad.append(f"{L}: a copper sliver {length:.2f} mm long, {w:.3f} mm wide, at ({c.x:.2f}, {c.y:.2f})")
        if len(sl) > 5:
            bad.append(f"{L}: ... {len(sl) - 5} more slivers")
        r = RULES["min_slit"] / 2
        gaps = b.image[L].buffer(r, ARC_RES).buffer(-r, ARC_RES).difference(b.image[L].buffer(1e-4))
        st = [(g.length / 2, g.area / (g.length / 2), g.centroid) for g in polys(gaps)
              if g.length / 2 > 1.0 and 0.01 < g.area / (g.length / 2) < 0.9 * RULES["min_slit"]]
        # (over 1 mm long: the short wedges where two traces leave one pad are normal)
        for length, w, c in sorted(st, key=lambda v: -v[0])[:5]:
            bad.append(f"{L}: a slit in the copper {length:.2f} mm long, {w:.3f} mm wide, at ({c.x:.2f}, {c.y:.2f})")
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
    flashes = {L: [o for o in b.layers[L] if o.kind == "flash" and o.dark and o.ap[0] in ("C", "R")] for L in ("F_Cu", "B_Cu")}
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
        via = h["d"] < 0.6
        for L, p in zip(("F_Cu", "B_Cu"), pads):
            if p is None or math.dist(p.pts[0], (h["x"], h["y"])) > 1e-3:
                bad.append(f"{L}: no pad on the plated hole at ({h['x']}, {h['y']})")
                continue
            ring = (min(p.ap[1][:2]) - h["d"]) / 2
            if via and L == "F_Cu" and (h["d"] < RULES["via_drill"] - 1e-6 or p.ap[1][0] < RULES["via_pad"] - 1e-6):
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
            if side in p["layers"] and not p["masked"] and not mask.buffer(1e-3).covers(p["geom"]):
                bad.append(f"{M}: pad {p['pin']} is covered")
        for h in b.holes:
            if h["plated"] and h["d"] < 0.6 and mask.intersects(Point(h["x"], h["y"]).buffer(h["d"] / 2)):
                bad.append(f"{M}: the via at ({h['x']}, {h['y']}) is not tented")
            elif h["plated"] and h["d"] < 0.6:
                # its pad, against an opening: the fab's mask expansion would bare it
                f = min((o for o in flashes[L]), key=lambda o: math.dist(o.pts[0], (h["x"], h["y"])), default=None)
                r = f.ap[1][0] / 2 if f is not None and math.dist(f.pts[0], (h["x"], h["y"])) < 1e-3 else h["d"] / 2
                d = mask.distance(Point(h["x"], h["y"])) - r
                if d < RULES["via_to_opening"] - 1e-6:
                    bad.append(f"{M}: the via at ({h['x']:.2f}, {h['y']:.2f}) is {max(d, 0):.3f} mm from a mask opening")
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
            side = "top" if S == "F_SilkScreen" else "bottom"
            pad_geoms = [p["geom"] for p in b.pads if side in p["layers"]]
            openings = [g for g in polys(b.image[M]) if any(g.intersects(pg) for pg in pad_geoms)]
            near = silk.intersection(unary_union(openings).buffer(RULES["silk_to_pad"] - 1e-3, ARC_RES))
            for g in polys(near):
                if g.area > 1e-3:
                    bad.append(f"{S}: silk within {RULES['silk_to_pad']} mm of a pad near "
                               f"({g.centroid.x:.2f}, {g.centroid.y:.2f})")
            # no silk over a hole: the drill takes it. Over a via only text counts
            # (a letter drilled away); a part's outline crossing one just loses a dot
            text = unary_union([o.geom for t in b.silk_text for o in text_strokes(b, t)[0]])
            for h in b.holes:
                over = silk if h["d"] >= 0.6 or not h["plated"] else text
                if over.intersects(Point(h["x"], h["y"]).buffer(h["d"] / 2)):
                    bad.append(f"{S}: silk over the hole at ({h['x']}, {h['y']})")
    for t in b.silk_text:
        h = text_height(b, t)
        if h is None and any(abs(round(0.09 * t["font_size"], 4) - pw) < 2e-3 for pw in b.silk_path_widths):
            bad.append(f"silk text '{t['text']}': its stroke is as wide as a silk line's, so it can't be "
                       f"measured: change the font size or SILK")
        elif h is None:
            bad.append(f"silk text '{t['text']}': its strokes aren't in the Gerber where the build put it")
        elif h < RULES["silk_text"] - 1e-6:
            bad.append(f"silk text '{t['text']}' prints {h:.2f} mm tall (>= {RULES['silk_text']})")
    # paste: only on pads, and clear of plated holes (a stencil prints it)
    for P, side in (("F_Paste", "top"), ("B_Paste", "bottom")):
        paste = b.image.get(P, Polygon())
        if paste.is_empty:
            continue
        pads = unary_union([p["geom"] for p in b.pads if side in p["layers"]])
        off = paste.difference(pads.buffer(1e-3))
        for g in polys(off):
            if g.area > 1e-3:
                bad.append(f"{P}: {g.area:.2f} mm2 of paste off its pad near ({g.centroid.x:.2f}, {g.centroid.y:.2f})")
        for h in b.holes:
            if h["plated"] and paste.distance(Point(h["x"], h["y"])) < h["d"] / 2 + 0.1 - 1e-6:
                bad.append(f"{P}: paste within 0.1 mm of the hole at ({h['x']}, {h['y']})")
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


def check_fit(b):
    bad = []
    # Seen from above with its rear wall up, the base's X runs right to left
    # (Y up, right-handed): the board's top view must map onto it with a
    # determinant of -1, or the board as made is the model's mirror image.
    det = b.map[0] * 1.0            # dX/dx * dZ/dy: the map neither turns nor shears
    if det >= 0:
        bad.append("board +x maps to base +X: the board would be the mirror image of the model "
                   "(see BASE_MAP)")
    if b.part_layers - {"top"}:
        bad.append(f"parts on {', '.join(sorted(b.part_layers - {'top'}))}: the map assumes every part on top")
    outline = to_base(b.outline, b.map)
    out = outline.difference(BASE_FLOOR)
    if out.area > 1e-3:
        x0, z0, x1, z1 = out.bounds
        bad.append(f"the board runs {out.area:.1f} mm2 into the base's obstacles "
                   f"(base X {x0:.1f}..{x1:.1f}, Z {z0:.1f}..{z1:.1f})")
    for r, gs in sorted(b.courtyards.items()):
        g = to_base(unary_union(gs), b.map)
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
        boss = Point(to_base_xy(h["x"], h["y"], b.map)).buffer(BOSS_D / 2)
        for name, region in PLATE_FEATURES:
            if boss.intersects(region):
                bad.append(f"the boss under the hole at ({h['x']}, {h['y']}) lands on the plate's {name}")
    # the Zero's USB-C at the rear wall's cutout (fan_housing.scad: zero_usb_x)
    pads = {p["pin"]: p for p in b.pads if p["pin"] in ("U1.5V", "U1.GP0")}
    if len(pads) != 2:
        bad.append("no Zero (U1 with 5V and GP0 pads) on the board to check against the rear cutout")
    else:
        cx = (pads["U1.5V"]["x"] + pads["U1.GP0"]["x"]) / 2
        zero_top = max(p["y"] for p in pads.values()) + 1.59
        X = to_base_xy(cx, 0, b.map)[0]
        if abs(X - zero_usb_x()) > 0.25:
            bad.append(f"the Zero's USB-C is at base X {X:.2f}, the rear cutout at {zero_usb_x()}")
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
    b.json_outline = b.outline


def _sliver(b):
    """A 0.08 mm strip of copper, 2 mm long, in a clear spot."""
    spot = b.outline.buffer(-2).difference(b.image["F_Cu"].buffer(1.5)).representative_point()
    g = box(spot.x - 1, spot.y - 0.04, spot.x + 1, spot.y + 0.04)
    b.image["F_Cu"] = b.image["F_Cu"].union(g)


def _silk_by_pad(b):
    """A silk line 0.01 mm off a pad's opening."""
    p = next(p for p in b.pads if "top" in p["layers"] and p["pin"].startswith("R_DIV1"))
    x0, y0, x1, y1 = p["geom"].bounds
    g = LineString([(x0, y1 + 0.1), (x1, y1 + 0.1)]).buffer(0.09)
    b.image["F_SilkScreen"] = b.image["F_SilkScreen"].union(g)


def _shrink_text(b):
    """One label printed at 0.7 of its size."""
    t = next(t for t in b.silk_text if len(t["text"]) >= 3)
    a = (t["anchor_position"]["x"], t["anchor_position"]["y"])
    for o in text_strokes(b, t)[0]:
        o.geom = affinity.scale(o.geom, 0.7, 0.7, origin=a)
        o.pts = [(a[0] + 0.7 * (x - a[0]), a[1] + 0.7 * (y - a[1])) for x, y in o.pts]


def _edge_mismatch(b):
    """Edge_Cuts' +x side 1 mm further out, read back through the parser."""
    x1 = b.outline.bounds[2]
    for o in b.layers["Edge_Cuts"]:
        o.pts = [(x + 1 if abs(x - x1) < 1e-3 else x, y) for x, y in o.pts]
    b.outline = edge_outline(b.layers["Edge_Cuts"])


def _l_sliver(b):
    """A 0.1 mm L-shaped strip of copper, 1.5 + 1.25 mm, joined to a pad."""
    p = next(p for p in b.pads if "top" in p["layers"] and p["pin"].startswith("R_DIV1"))
    x0, y0, x1, y1 = p["geom"].bounds
    g = LineString([(x1, y1), (x1 + 1.5, y1), (x1 + 1.5, y1 + 1.25)]).buffer(0.05, cap_style=2, join_style=2)
    b.image["F_Cu"] = b.image["F_Cu"].union(g)


def _copper_by_edge(b):
    x0, y0, x1, y1 = b.outline.bounds
    g = box(x1 - 0.25, (y0 + y1) / 2, x1 - 0.1, (y0 + y1) / 2 + 2)
    b.image["B_Cu"] = b.image["B_Cu"].union(g)


def _untented_via(b):
    v = next(h for h in b.holes if h["plated"] and h["d"] < 0.6)
    b.image["F_Mask"] = b.image["F_Mask"].union(Point(v["x"], v["y"]).buffer(0.4))


def _paste_on_hole(b):
    h = next(h for h in b.holes if h["plated"] and h["d"] > 0.6)
    b.image["F_Paste"] = b.image["F_Paste"].union(Point(h["x"], h["y"]).buffer(0.6))


def _slit(b):
    """A 0.1 mm slot cut 2 mm into the top copper."""
    spot = b.image["F_Cu"].buffer(-1.5).representative_point()
    b.image["F_Cu"] = b.image["F_Cu"].difference(box(spot.x - 1, spot.y - 0.05, spot.x + 1, spot.y + 0.05))


def _via_under_text(b):
    """A via drilled through a label's first stroke."""
    v = next(h for h in b.holes if h["plated"] and h["d"] < 0.6)
    o = text_strokes(b, next(t for t in b.silk_text if len(t["text"]) >= 3))[0][0]
    v["x"], v["y"] = o.pts[0]


def _no_zero(b):
    b.pads = [p for p in b.pads if not p["pin"].startswith("U1.")]


def _part_under_head(b):
    h = b.npth[0]
    g = unary_union(b.courtyards["R_DIV1"]).centroid
    b.courtyards["R_DIV1"] = [affinity.translate(c, h["x"] - g.x, h["y"] - g.y) for c in b.courtyards["R_DIV1"]]


def _mirror_map(b):
    b.map = (1.0, BASE_X0, BASE_Z0)                    # v2's map: X = x + 42


def _boss_on_vent(b):
    x, z = 31.0, 45.0                                  # on a vent slot of the plate
    b.npth[0]["x"], b.npth[0]["y"] = (x - b.map[1]) / b.map[0], z - b.map[2]


def _j1_toward_pot(b):
    dx = 2.5 * b.map[0]                                # 2.5 mm toward base +X (dX = sx * dx)
    b.courtyards["J1_VIN"] = [affinity.translate(c, dx, 0) for c in b.courtyards["J1_VIN"]]


# (what breaks, how, a phrase the check must then report)
SELF_TEST = {
    "fab": [("a 0.2 mm via", _thin_via, "via at"),
            ("a 0.1 mm silk line", _thin_silk, "line 0.1"),
            ("a copper sliver", _sliver, "sliver"),
            ("an L-shaped sliver joined to a pad", _l_sliver, "sliver"),
            ("a 0.1 mm slit in the copper", _slit, "slit"),
            ("a via under a label", _via_under_text, "silk over the hole"),
            ("copper 0.1 mm from the edge", _copper_by_edge, "from the board edge"),
            ("a via left untented", _untented_via, "not tented"),
            ("paste over a plated hole", _paste_on_hole, "of the hole"),
            ("silk against a pad", _silk_by_pad, "of a pad"),
            ("a label printed small", _shrink_text, "prints"),
            ("Edge_Cuts not the build's outline", _edge_mismatch, "Edge_Cuts differs")],
    "nets": [("VIN bridged to GND", lambda b: _bridge(b, "J1_VIN.P1", "J1_VIN.P2"), "short"),
             ("FAN_PWM cut at the header", lambda b: _cut(b, "J2_FAN.P4"), "open")],
    "bodies": [("one part moved onto another", _move_courtyard, "overlap"),
               ("a part under an M2 head", _part_under_head, "M2 head")],
    "fit": [("the board 12 mm wider (into the sled)", _grow_outline, "into the base's obstacles"),
            ("the board mapped mirrored, as in v2", _mirror_map, "mirror"),
            ("a boss on a vent slot", _boss_on_vent, "vent slot"),
            ("the Zero missing", _no_zero, "no Zero"),
            ("J1 2.5 mm toward the pot", _j1_toward_pot, "under the dial pot")],
}


# ---------------------------------------------------------------- export
def solid_fill(fill, copper, foreign):
    """A slit fill kept clear of other nets, and only where it leaves the
    copper at least RULES["min_copper"] wide: cut back near another net, a fill
    can leave a finger, and round-off a hairline along a straight edge."""
    g = 1e-5                                    # snapped: near-coincident edges trip GEOS
    area = lambda x: MultiPolygon(polys(x))     # (a snapped overlay can return stray lines)
    fill = area(fill.difference(foreign.buffer(RULES["min_space"] + 0.02, ARC_RES), grid_size=g))
    m = RULES["min_copper"] / 2
    body = area(copper).union(fill, grid_size=g)
    return area(fill.intersection(body.buffer(-m, ARC_RES).buffer(m, ARC_RES), grid_size=g))


def clean_for_export(src, dst, width=POUR_MIN_WIDTH):
    """Write the build's circuit JSON `src` to `dst` ready for the Gerber
    export:
      - each copper pour kept POUR_CLEARANCE off every other net's copper
        (tscircuit's pour runs straight over a drawn trace that changes
        layer), and without copper narrower than `width` (it leaves slivers
        between fine-pitch pads and along traces): an opening of the pour,
        keeping the pieces still joined to its own net's copper;
      - slits under RULES["min_slit"] between one net's own copper filled,
        the pour's and every other net's (acid traps);
      - paste drawn turned by a multiple of 90 deg rewritten as a plain
        rectangle (the exporter drops a rotated rectangle's turn)."""
    cj = json.loads(Path(src).read_text())
    # each copper feature with its net (tscircuit's connectivity key)
    key = {}
    for e in cj:
        if e["type"] in ("source_port", "source_net", "source_trace"):
            key[e[e["type"] + "_id"]] = e.get("subcircuit_connectivity_map_key")
    port_key = {e["pcb_port_id"]: key.get(e["source_port_id"]) for e in cj if e["type"] == "pcb_port"}
    via_d = next((e["outer_diameter"] for e in cj if e["type"] == "pcb_via"), 0.7)
    feats = {"top": [], "bottom": []}
    keyed = {"top": [], "bottom": []}
    def add(L, k, g):
        feats[L].append(g)
        keyed[L].append((k, g))
    for e in cj:
        t = e["type"]
        if t == "pcb_smtpad":
            if e["shape"] == "circle":
                g = Point(e["x"], e["y"]).buffer(e["radius"], ARC_RES)
            else:
                g = box(e["x"] - e["width"] / 2, e["y"] - e["height"] / 2, e["x"] + e["width"] / 2, e["y"] + e["height"] / 2)
                g = affinity.rotate(g, e.get("ccw_rotation") or 0, origin=(e["x"], e["y"]))
            add(e["layer"], port_key.get(e.get("pcb_port_id")), g)
        elif t in ("pcb_plated_hole", "pcb_via"):
            k = port_key.get(e.get("pcb_port_id")) or e.get("subcircuit_connectivity_map_key")
            for L in feats:
                add(L, k, Point(e["x"], e["y"]).buffer(e["outer_diameter"] / 2, ARC_RES))
        elif t == "pcb_trace":
            k = key.get(e.get("source_trace_id"))
            for q in e["route"]:
                if q.get("route_type") == "via":     # a drawn trace's own via
                    for L in feats:
                        add(L, k, Point(q["x"], q["y"]).buffer(via_d / 2, ARC_RES))
            for a, c in zip(e["route"], e["route"][1:]):
                wires = [q for q in (a, c) if q.get("route_type") == "wire"]
                if not wires or len({q["layer"] for q in wires}) > 1:
                    continue                # a segment ending at a via takes its wire end's layer
                add(wires[0]["layer"], k,
                    LineString([(a["x"], a["y"]), (c["x"], c["y"])]).buffer(wires[0]["width"] / 2, ARC_RES))
    out, report = [], []
    for e in cj:
        if e["type"] == "pcb_solder_paste" and e.get("shape") == "rotated_rect":
            turn = round(e.get("ccw_rotation") or 0) % 180
            if turn in (0, 90) and abs((e.get("ccw_rotation") or 0) - round(e.get("ccw_rotation") or 0)) < 1e-6:
                e = dict(e, shape="rect")
                if turn == 90:
                    e["width"], e["height"] = e["height"], e["width"]
                e.pop("ccw_rotation", None)
                report.append(f"paste at ({e['x']:.2f}, {e['y']:.2f}) squared up")
        if e["type"] != "pcb_copper_pour":
            out.append(e)
            continue
        ring = lambda r: [(v["x"], v["y"]) for v in r["vertices"]]
        bs = e["brep_shape"]
        pour = Polygon(ring(bs["outer_ring"]), [ring(r) for r in bs.get("inner_rings", [])]).buffer(0)
        pk = key.get(e.get("source_net_id"))
        foreign = unary_union([g for k, g in keyed[e["layer"]] if k != pk])
        pour = pour.difference(foreign.buffer(POUR_CLEARANCE, ARC_RES))
        opened = pour.buffer(-width / 2, ARC_RES).buffer(width / 2, ARC_RES).intersection(pour)
        own = unary_union([g for k, g in keyed[e["layer"]] if k == pk and g.distance(pour) < 1e-3])
        # and slits under RULES["min_slit"] between it and that copper are filled (a
        # gap that narrow can't hold another net, which keeps >= 0.15 mm each side)
        r = RULES["min_slit"] / 2
        merged = unary_union([opened, own])
        fill = solid_fill(merged.buffer(r, ARC_RES).buffer(-r, ARC_RES).difference(own), merged, foreign)
        opened = unary_union([opened, fill.buffer(0.002, join_style="mitre")])   # overlapping, not touching at a point; mitre adds no arcs
        keep = [g for g in polys(opened) if g.area > 0.01 and g.intersects(own)]
        report.append(f"{e['layer']} pour: {pour.area - sum(g.area for g in keep):.2f} mm2 net change "
                      f"(thin or loose copper removed, same-net slits filled)")
        for g in polys(pour.difference(unary_union(keep).buffer(1e-4) if keep else Polygon())):
            if g.area > 1.0:
                x0, y0, x1, y1 = g.bounds
                report.append(f"  {g.area:.1f} mm2 of it at x {x0:.1f}..{x1:.1f}, y {y0:.1f}..{y1:.1f}")
        for k, g in enumerate(keep):
            g = orient(g, 1.0)
            n = dict(e, pcb_copper_pour_id=f"{e['pcb_copper_pour_id']}_{k}")
            n["brep_shape"] = {
                "outer_ring": {"vertices": [{"x": x, "y": y} for x, y in g.exterior.coords[:-1]]},
                "inner_rings": [{"vertices": [{"x": x, "y": y} for x, y in r.coords[:-1]]} for r in g.interiors],
            }
            out.append(n)
    # Slits between one net's own traces and pads (two traces leaving a pad
    # side by side, say) are filled the same way, as copper under mask. Nets
    # come from the copper itself: each layer's islands, joined through holes.
    isl = [(L, g) for L in feats for g in polys(unary_union(feats[L]))]
    group = list(range(len(isl)))
    def find(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for e in cj:
        if e["type"] in ("pcb_plated_hole", "pcb_via"):
            hit = [i for i, (_, g) in enumerate(isl) if g.intersects(Point(e["x"], e["y"]))]
            for i in hit[1:]:
                group[find(i)] = find(hit[0])
    nets = defaultdict(list)
    for i, (L, g) in enumerate(isl):
        nets[(find(i), L)].append(g)
    layer = {L: unary_union([g for M, g in isl if M == L]) for L in feats}
    r, k = RULES["min_slit"] / 2, 0
    for (n, L), gs in nets.items():
        own = unary_union(gs)
        others = layer[L].difference(own.buffer(1e-4))
        fill = solid_fill(own.buffer(r, ARC_RES).buffer(-r, ARC_RES).difference(own), own, others)
        for g in polys(fill):
            if g.area < 0.01:
                continue                    # the wedges where traces leave a pad: harmless
            g = orient(g.buffer(0.002, join_style="mitre"), 1.0)
            out.append({"type": "pcb_copper_pour", "pcb_copper_pour_id": f"slit_fill_{k}", "shape": "brep",
                        "layer": L, "covered_with_solder_mask": True,
                        "brep_shape": {"outer_ring": {"vertices": [{"x": x, "y": y} for x, y in g.exterior.coords[:-1]]},
                                       "inner_rings": []}})
            c = g.centroid
            report.append(f"{L}: a {g.area:.2f} mm2 slit in one net's copper filled at ({c.x:.2f}, {c.y:.2f})")
            k += 1
    Path(dst).write_text(json.dumps(out))
    return report


# ---------------------------------------------------------------- scad
def write_scad(b, path):
    rnd = lambda v: round(v, 3) + 0.0
    ring = orient(to_base(b.outline, b.map), 1.0)          # counter-clockwise in X/Z
    outline = [(rnd(x), rnd(z)) for x, z in list(ring.exterior.coords)[:-1]]
    holes = [tuple(rnd(v) for v in to_base_xy(h["x"], h["y"], b.map)) for h in sorted(b.npth, key=lambda h: (h["y"], -h["x"]))]
    parts = []
    for r, gs in sorted(b.courtyards.items()):
        x0, z0, x1, z1 = to_base(unary_union(gs), b.map).bounds
        parts.append((rnd(x0), rnd(z0), rnd(x1), rnd(z1), part_height(r), r))
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
    m = b.map
    inv = lambda g: affinity.affine_transform(g, [m[0], 0, 0, 1, m[0] * -m[1], -m[2]])
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
    ax.text(x0 + 0.5, y0 - 0.6, "Carrier + PSU v2.2: top side, parts by reference. Gold: pads. Black: the "
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
    ap.add_argument("--clean", nargs=2, type=Path, metavar=("IN", "OUT"),
                    help="write OUT: the circuit JSON IN ready for the Gerber export (pours, paste)")
    args = ap.parse_args()
    if args.clean:
        for line in clean_for_export(*args.clean):
            print(line)
        print(f"wrote {args.clean[1]}")
        return
    if not args.circuit_json.exists():
        sys.exit(f"{args.circuit_json} is missing: build the board first (electronics/pcb/README.md)")
    b = Board(args.gerbers, args.circuit_json, placement=args.placement)
    if args.write_scad:
        write_scad(b, args.write_scad)
        print(f"wrote {args.write_scad}")
    if args.render:
        render(b, args.render)
        print(f"wrote {args.render}")
    if args.assembly:
        assembly(b, args.assembly)
        print(f"wrote {args.assembly}")
    if args.self_test:
        missed = 0
        for name, fn, _ in CHECKS:
            _conn_cache.clear()
            before = set(fn(b))
            for label, mutate, expect in SELF_TEST[name]:
                m = b.copy()
                _conn_cache.clear()
                mutate(m)
                # caught: the check now reports something new, of the right kind
                caught = any(expect in line for line in set(fn(m)) - before)
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
