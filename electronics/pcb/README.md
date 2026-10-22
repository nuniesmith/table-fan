# Table Fan — Carrier + PSU PCB v1

Custom 2-layer board (47 × 92 mm, 1.6 mm FR4) that replaces the perfboard
carrier **and** both MP1584 mini buck modules. The BMS and the 4S USB-C
charger stay as modules.

Design source: `carrier-psu.tsx` (tscircuit — build with `npx tscircuit build`,
export with `npx tscircuit export -f gerbers`). Ready-to-order Gerbers are in
`gerber/` (top/bottom copper, mask, silk, paste, edge cuts, plated + NPTH
drills, plus BOM and pick-and-place CSVs). The layout is autorouted and
passes tscircuit's full DRC/connectivity checks; review before ordering —
this is a v1.

## What's on it

- **RP2040-Zero footprint** (Waveshare dims: 18 × 23.5 mm, 23 castellated
  pads, 2.54 mm pitch) at the rear, USB-C to the rear-wall cutout. All fan
  pins land: GP15 PWM, GP14 tach, GP27 dial, GP26 battery sense, GP13
  charger status, GP11 button, GP0/GP1 OLED I2C.
- **Two MP1584EN bucks** (bare SOIC-8E chips, datasheet typical application,
  ~500 kHz, 10 µH, SS34 catch diode):
  - Buck A → **12.0 V** fan rail (FB 140k/10k). Output feeds the fan header
    through an SS34 diode-OR with the bench input (fan sees ≈11.7 V, same
    as the module design).
  - Buck B → **5.0 V** (FB 52.5k/10k), feeding the Zero's 5V pin through an
    SS14 Schottky (prevents USB back-feed; the 0.3 V drop is expected).
- **Battery sense divider** 100k/22k + 100nF → GP26, fed from the switched
  VIN bus.
- **Fan header** (standard 4-pin: GND / 12 V / tach / PWM), tach with
  10k pull-up to 3V3 + 1nF.
- **Charger status** → GP13 via 10k series, plus an optional 1N4148 clamp
  footprint to 3V3 (fit only if the charger module's STAT pin measures
  above 3.3 V at the bench test).
- Connectors: VIN 2-pin screw terminal, bench 12 V JST-XH input (own SS34
  into the diode-OR), dial / OLED / button / charger-status JST-XH,
  test points for VIN / 12 V / 5 V / 3V3 / GND.
- Ground pours on both layers. Nothing smaller than 0805 / SOIC / SMA —
  hand-solderable throughout.

## Ordering

- Boards: bare PCBs from JLCPCB/PCBWay using `gerber/`.
- Parts: LCSC alongside the board order. The two **MP1584EN chips are the
  one part not already on hand** (~$1 each) — the AliExpress order turned
  out to be MP1584 mini *modules*, which stay as bench spares. Everything
  else is standard 0805/1210 passives, SS34/SS14 (SMA), 10 µH shielded
  inductors (~10 × 10 mm), JST-XH and a 5.08 mm screw terminal.

## Assembly notes

- The MP1584 exposed pad is GND with no solder-access hole in v1 —
  pre-tin the pad and chip, then hot-air or a wide iron tip.
- The Zero's back-side GP17–25 test pads face the board; nothing routes
  under the module on the top layer except its own pad fan-out.

## Mechanical — read before printing

The board mounts on the base's +X floor strip with **6× M2 holes**. Two of
print 7's carrier bosses move and two are new, so **print 7 (bottom plate +
sled) must be re-sliced** with boss positions (base coords, mm):

- existing: (27, 68.5), (48, 68.5)
- rear pair moved outboard: (24, 93), (51, 93)
- new front pair: (24, 11), (55, 11)

The 4S charger module relocates to the freed 12 V-buck spot on the battery
sled lid (beside the BMS); only its STAT wire runs to this board's CHG
connector.
