# Table Fan — Carrier + PSU PCB v2.1

Custom 2-layer board (1.6 mm FR4, 1 oz) that replaces the perfboard carrier
**and** both MP1584 mini buck modules. The BMS and the 4S USB-C charger stay
as modules. The outline is 40.5 × 93 mm, with a 15 × 20 mm notch out of its
+X front side round the dial pot. It lies on the bottom plate beside the
battery sled, on **8 M2 bosses**.

**Order v2.1, not v2.** v2's Gerbers (PR #18) were the mirror image of the
board the 3D model fits: made from them, the notch lands on the sled's side
and the holes miss the bosses. v2.1 is the same board the right way round
(see "Changes in v2.1").

Design source: `carrier-psu.tsx` (tscircuit). Ready-to-order Gerbers are in
`gerber/` (top/bottom copper, mask, silk, paste, edge cuts, plated + NPTH
drills, plus BOM and pick-and-place CSVs). Wiring to the rest of the fan:
[the electronics doc](../ELECTRONICS_BOM_AND_WIRING.md); wire lengths and the
build sequence: [BUILD.md](../../docs/BUILD.md).

## What's on it

- **RP2040-Zero**, soldered by its castellated edges at the rear, USB-C at the
  board's rear edge, centred on the rear wall's cutout (X 37.5, as before).
- **Two MP1584EN bucks** (bare SOIC-8E chips, ~500 kHz, 10 µH shielded
  inductors, SS34 catch diodes). The outputs are set by resistors: nothing
  to adjust. Both start above about 7.5 V (EN divider 100k/24.9k).
  - Buck A → **12.0 V** fan rail (FB 140k/10k), into the fan header through
    an SS34 diode-OR with the bench input. The fan sees about 11.6–11.7 V,
    same as the module design.
  - Buck B → **4.98 V** (FB 52.3k/10k), into the Zero's 5V pin through an
    SS14, so USB can't back-feed the buck. The 5V pin sees about 4.6–4.7 V,
    which the Zero's 3.3 V regulator absorbs.
- **47 µF 35 V electrolytic** across VIN: damps the ringing when the dial's
  switch connects the pack to the bucks' ceramic input caps.
- **Battery divider** 100k/22k + 100 nF → GP26.
- **Tach** pull-up 10k to 3V3 + 1 nF → GP14.
- **Charger status** → GP13 through 10k, plus an optional 1N4148WS clamp to
  3V3 (see Assembly).
- **Test points**: VIN, 12V (the fan rail, after the diode), 5V (the Zero's
  5V), 3V3, GND.
- Ground pours on both layers, with thermal spokes on the through-hole GND
  pads. Nothing smaller than 0805 (apart from the optional SOD-323 clamp):
  hand-solderable throughout.

## Connectors

Pin 1 is at the silkscreen triangle.

| Ref | Part | Pins (1 first) | Goes to |
|---|---|---|---|
| J1 VIN | KF301-5.0-2P screw terminal, 5.0 mm pitch | 1 + (VIN), 2 − (GND) | + from the dial switch (after the fuse); − from BMS P− (ground star). 18 AWG |
| J2 FAN | Molex 47053-1000, 4-pin PC fan header | 1 GND, 2 +12 V, 3 tach, 4 PWM | the Noctua's own plug, directly |
| J3 DIAL | JST XH 3-pin (B3B-XH-A) | 1 3V3, 2 wiper (GP27), 3 GND | the pot's three lugs: ends to 3V3 and GND, wiper (middle) to pin 2 |
| J4 OLED | JST XH 4-pin (B4B-XH-A) | 1 GND, 2 3V3, 3 SCL (GP1), 4 SDA (GP0) | the OLED module (its listing: GND VCC SCL SDA; check its silkscreen) |
| J5 BTN | JST XH 2-pin (B2B-XH-A) | 1 GP11, 2 GND | the screen button |
| J6 CHG | JST XH 2-pin | 1 charger STAT (through the board's 10k to GP13), 2 GND | the charger module's status pin |
| J7 BENCH | JST XH 2-pin | 1 bench +12 V, 2 GND | the MT3608 (bench only, for tests without a pack) |

Where they sit (base X, Z, roughly):
- J1 (39, 22), at the front by the notch;
- J2 (22, 22), front-left, right under the roof's fan-cable slot;
- J7 (29, 7.5), at the front edge;
- on the −X edge (X ~21.6): J6 at Z 62, J3 at Z 72, J4 at Z 84;
- J5 (55, 66.5), by the button.

JST XH takes 22–28 AWG: the 26 AWG signal leads get XH plugs (crimped, or
pre-crimped leads). The 18 AWG power leads go into the screw terminal J1.

## Build, check and export

Needs Node.js with npm, [Bun](https://bun.sh) (tscircuit's `tsci` runs
under it), `unzip`, and Python 3 with shapely 2 (`pip install shapely`;
matplotlib too, for the pictures).

```
cd electronics/pcb
npm ci             # exactly the versions in package-lock.json
npm run gerbers    # build (writes dist/), clean the pours, export into gerber/
cd ../..
python3 tools/check_pcb.py               # fab, nets, bodies, fit: PASS/FAIL
python3 tools/check_pcb.py --self-test   # breaks each check on purpose
```

If the board moved, regenerate the plate's bosses and recheck the 3D fit:

```
python3 tools/check_pcb.py --write-scad  # rewrites models/carrier_pcb.scad
python3 tools/check_geometry.py
```

After any change to the parts, redraw the assembly map:
`npm run assembly` (it runs
`python3 tools/check_pcb.py --assembly electronics/pcb/assembly.png`).

- `check_pcb.py` reads the Gerbers and the build's circuit JSON. Its
  checks: **fab** (JLCPCB 2-layer rules, with margin: no copper slivers,
  the outline read from Edge_Cuts, text height measured in the Gerber,
  silk 0.15 mm off pads); **nets** (the copper joins exactly the pins in a
  netlist written out by hand in the tool: no opens, no shorts); **bodies**
  (no courtyard overlaps, M2 heads clear of parts and pads); **fit** (the
  board maps onto the base turned, not mirrored; the outline on the base's
  free floor, each part under what hangs above it). `--self-test` breaks
  each rule 14 ways and checks each one is caught.
- The board's coordinates are its top view, which is the base seen from
  above with its rear wall up: board x = 42 − base X, y = base Z − 50.
  Seen that way the base's +X (the pot's side) is on the left.
- tscircuit 0.0.3003 and everything under it are pinned by
  `package-lock.json`: `npm ci` then `npm run gerbers` gives the Gerbers in
  `gerber/` again, apart from their date stamps. The scripts run with the
  parts engine off: the LCSC numbers are written in the source.
- `npm run gerbers` cleans the copper pours before exporting
  (`check_pcb.py --clean-pours`): tscircuit's pour leaves slivers between
  fine-pitch pads and along traces, which a fab can't make. It removes pour
  copper narrower than 0.2 mm and any piece left loose.
- The router is `autorouterVersion="beta_pipeline7"` (the default one
  shorted two nets here). Each buck's own wiring (SW, BST, VIN/GND to CIN1,
  FB, COMP, EN, FREQ, VOUT) is drawn in the source, to the datasheet
  layout. The router lays every other net, then GND last: the pours carry
  GND, and it adds GND traces and vias only where a pad's patch of pour
  needs joining.
- Design rules in the source: track 0.25 mm min (0.3 default, 0.4–0.6
  power), 0.16 mm trace to pad (the router leaves at least 0.15 mm between
  nets), vias 0.3 / 0.7 mm tented, copper 0.5 mm off the edge.

## Ordering

- Boards: zip `gerber/` (Gerber X2 + Excellon) and order from JLCPCB or
  PCBWay: 2 layers, 1.6 mm, 1 oz, any finish and colour. The notch is
  normal routing.
- Parts: LCSC, from the BOM below. `gerber/bom.csv` is tscircuit's BOM with
  the same numbers (all but U1 and RFB1_B).
- The MP1584 mini modules, the 1N5819 diodes and the perfboard are no
  longer used in the fan. Keep the minis as bench spares.

## BOM

| Qty | Part | LCSC | Refs |
|---|---|---|---|
| 2 | MP1584EN-LF-Z (MPS), SOIC-8E | C15051 | U_A, U_B |
| 2 | SWPA6045S100MT (Sunlord) 10 µH, 6 × 6 × 4.5 mm, Isat 3.2 A | C79272 | L_A, L_B |
| 4 | SS34 (SMA, 40 V 3 A) | C115205 | DC_A, DC_B, D_OR, D_BENCH |
| 1 | SS14 (SMA, 40 V 1 A, MDD) | C2480 | D_5V |
| 1 | 1N4148WS (SOD-323), optional | C2128 | D_CLAMP |
| 2 | 10 µF 25 V X5R 1210 (Samsung CL32A106KATLNNE) | C730494 | CIN1_A, CIN1_B |
| 2 | 22 µF 25 V X5R 1210 (Samsung CL32A226KAJNNNE) | C52306 | COUT1_A, COUT1_B |
| 1 | 47 µF 35 V electrolytic 6.3 × 5.8 (Nichicon UWT1V470MCL1GS) | C87068 | C_BULK |
| 7 | 100 nF 0805 | C28233 | CIN2_x, CBST_x, COUT2_x, C_DIV |
| 2 | 220 pF 0805 | C107145 | CCOMP_x |
| 1 | 1 nF 0805 | C46653 | C_TACH |
| 4 | 10k 0805 | C17414 | RFB2_x, R_TACH, R_STAT |
| 1 | 140k 0805 | C17460 | RFB1_A |
| 1 | 52.3k 0805 1 % (UNI-ROYAL 0805W8F5232T5E) | search LCSC by value (see Caveats) | RFB1_B |
| 2 | 68.1k 0805 | C17795 | RCOMP_x |
| 2 | 200k 0805 | C17539 | RFREQ_x |
| 3 | 100k 0805 | C149504 | REN1_x, R_DIV1 |
| 2 | 24.9k 0805 | C17571 | REN2_x |
| 1 | 22k 0805 | C17560 | R_DIV2 |
| 1 | KF301-5.0-2P terminal | C474881 | J1 |
| 1 | Molex 47053-1000 fan header | C240840 | J2 |
| 1 | JST B3B-XH-A(LF)(SN) | C144394 | J3 |
| 1 | JST B4B-XH-A(LF)(SN) | C144395 | J4 |
| 3 | JST B2B-XH-A(LF)(SN) | C158012 | J5, J6, J7 |
| 1 | RP2040-Zero (Waveshare), on hand | — | U1 |

Mating plugs: JST XHP-2 ×3, XHP-3, XHP-4 housings + SXH crimps (or
pre-crimped XH leads). The fan plugs into J2 directly.

## Assembly

[`assembly.png`](assembly.png) is the map: every part's reference and value.
**The designators are not on the board.** The silkscreen has the connector
names, a triangle at each connector's pin 1, + and − beside J1's pins, a
bar at each diode's cathode, a + and a chamfered outline at the
electrolytic's +, a dot at each MP1584's pin 1 and at the Zero's 5V pin,
and the test point names.

- Order: the MP1584s first (smallest pitch), then the 0805/1210 passives,
  diodes, inductors, the electrolytic, the Zero, and the through-hole
  connectors last.
- Each MP1584's exposed pad: tin the pad lightly, place the chip, tack and
  solder the pins, then from the back feed solder into the 1.0 mm hole in
  the pad with the iron until it wets through. At this load (0.3 A) the pad
  is for heat only, so a pad that didn't fully wet is not a fault.
- Diodes: the cathode is the end with the silkscreen bar (the band on the
  part). The electrolytic's + (its unmarked side; the stripe on the can
  marks −) goes to the + by the chamfer.
- D_CLAMP: fit it only if the charger's STAT pin measures above 3.3 V.
- The Zero: solder only its castellated edges. Under it the board is all
  solder mask (its vias are tented), so the pads on its underside can't
  short to anything; don't tin them.
- Headers: the fan header and the JST headers have symmetric pin patterns,
  so they can go in backwards. **Before soldering each one, mate its plug
  and check the plug's pin-1 wire is at the triangle.**
- First power test, before anything is plugged in (J2–J7 empty): a
  current-limited bench supply (12–16.8 V, 100 mA limit) on J1. Measure
  TP_12V (11.8–12.0 V with no fan on it; 11.6–11.7 V once the fan runs,
  after the SS34), TP_5V (about 4.6–4.8 V) and TP_3V3 (3.3 V, from the
  Zero). Idle current is tens of mA.

## Mechanical — read before printing

- The board lies on the bottom plate, +X of the battery sled, on 8 M2
  bosses (5 mm tall, 5 mm across), fixed with **8× M2 × 6 self-tapping**
  screws (the perfboard used 4). Holes, base (X, Z): (21, 6.5),
  (55.5, 6.5), (40.5, 30.2), (56.2, 42.6), (47.5, 59.5), (55.5, 74),
  (21, 93.5), (55, 93.5).
- The bosses come from the board: `models/carrier_pcb.scad` is written by
  `check_pcb.py --write-scad` from the build, and `fan_housing.scad`
  includes it. Don't edit it by hand.
- **The bottom plate (plate 06, with the sled) must be reprinted**, or
  printed for the first time, from the new model. See
  [PRINTING.md](../../docs/PRINTING.md). A plate printed for v2 has one
  boss 4.4 mm off (at Z 47, now 42.6): reprint that too.
- The charger moves from the plate onto the sled's lid, beside the BMS,
  under the roof's left vent slots (foam tape). Its STAT lead runs to J6.
- J1's wire entry faces −X, toward the sled, away from the pot.

## Changes in v2.1

v2 (PR #18) fixed v1, but its review after merging found:
- **Its Gerbers were mirrored.** Its local frame put board +x at base +X,
  which seen from above is a mirror image, so the board as made would not
  have matched the model: the notch on the sled's side, the holes off the
  bosses. v2.1 maps board +x to base −X (`check_pcb.py` now tests the
  handedness) and is v2 mirrored back, with every part placed the right way
  up rather than mirrored; each buck block is turned 180°. One hole moved
  (Z 47 to 42.6) to clear a part of the turned 5 V buck.
- Copper slivers down to 0.02 mm in the top pour, between the MP1584 pins
  and along traces: the pours are now cleaned before export.
- Text 0.96–0.99 mm tall, under JLCPCB's 1 mm: now 1.2 mm. J1's + and −
  were text too small to print: now drawn. The OLED label sat 0.01 mm off
  a pad: silk now keeps 0.15 mm off every pad.
- J1's wires entered toward the pot with 1.2 mm to spare: they now enter
  from the other side.
- Vias 0.3 / 0.7 mm (were 0.6): the router keeps those 0.15 mm off other
  nets, where 0.6 mm vias ended up 0.115 mm off. GND is routed last, over
  the pours.
- The exposed pads' paste kept clear of their solder holes; no paste on
  the test points.
- The checker read the outline from the build, not Edge_Cuts, and its
  self-test only counted any failure as a catch: both fixed. The build is
  pinned by `package-lock.json`.

## Changes from v1

v1 (PR #17) had these; v2 fixes all of them:
- The outline (47 × 92 mm) ran into the base's +X corner bosses and the dial pot.
- 0.2/0.3 mm vias (0.05 mm ring) and 0.10 mm copper gaps, below JLCPCB's 2-layer minimums.
- Parts that couldn't be fitted: JST housings overlapping, D_BENCH under two headers, the VIN terminal over a screw hole, parts inside the inductor outline.
- The MP1584 exposed-pad land turned 90°, 0.15 mm from every pin, VIN included.
- A buck layout against the datasheet: SW through vias under the chip, the catch diode through two vias, COMP 13 mm long.
- Silkscreen too thin to print, designators illegible, text off the board, no polarity marks.
- No part numbers for half the BOM, a 52.5k that doesn't exist, cap voltage ratings unknown.
- Models and docs still describing the perfboard.
- No bulk input cap, no thermal reliefs.

## Caveats

- The 52.3k has no confirmed LCSC listing. Any 0805 1 % 52.3k works
  (4.98 V); 52.5k doesn't exist.
- MP1584 exposed-pad land: from MPS's recommended land pattern (2.62 ×
  3.51 mm, rows 5.40 mm apart). The package drawing itself (MPS
  MF-PO-D-0018) is worth a glance before ordering.
- The JST XH and fan header courtyards are drawn with margin because their
  exact pin offset wasn't confirmed. The electrolytic's land is from its
  terminal spacing (2.2 mm), not a published land.
- The passives' LCSC numbers came from tscircuit's parts engine at v1:
  check value and package when ordering.
- The board is laid out for hand soldering. The paste layer is tscircuit's
  default (each pad's paste 70 % of it each way, the exposed pads' in two
  windows): check it before ordering a stencil. For a JLCPCB assembly
  order, leave out U1 (the Zero, on hand) and D_CLAMP (fitted only if
  needed); the test points are marked do-not-place.
- tscircuit warns "4 chip overlaps in final layout": that's its
  auto-generated schematic, not the PCB.
