// ---------------------------------------------------------------------------
// Table Fan — Carrier + PSU board v2.1
// Replaces the perfboard carrier AND both MP1584 mini buck modules.
// 2-layer, 1.6 mm FR4, parts on top. Local coords are the board seen from its
// top, which is the base seen from above with its rear wall up: +x = base -X
// (toward the sled), +y = rear (Zero USB-C end). Base coords -> board local:
// x = 42 - X_base, y = Z_base - 50 (tools/check_pcb.py uses the same map and
// checks that it is a turn, not a mirror). v2 mapped +x to +X, which mirrored
// the board: v2.1 is v2 mirrored back, with every part the right way up.
//
// The outline is the base's free floor (models/fan_housing.scad): clear of the
// battery sled (X 17), the +X corner bosses (X >= 59.5 at the front and back)
// and the dial pot, which comes down to 2.5 mm above the plate at Z 14..34.
// Parts near the pot, and under the USB-C socket and the button, are low;
// tools/check_pcb.py checks every part's height against what hangs above it.
//
// Footprints are each part's datasheet land pattern (named at each one).
// Build, check and export: see README.md.
// ---------------------------------------------------------------------------

// A part's place: board position, then its rotation (CCW degrees).
type At = {x: number; y: number; rot?: number}

// Courtyard + silk helpers for the hand-made footprints.
const Court = (p: {w: number; h: number; x?: number; y?: number}) => (
  <courtyardrect pcbX={p.x ?? 0} pcbY={p.y ?? 0} width={p.w} height={p.h} />
)
const SILK = 0.18 // silkscreen stroke: JLCPCB prints 0.15 and up
const Line = (p: {pts: [number, number][]}) => (
  <silkscreenpath route={p.pts.map(([x, y]) => ({x, y}))} strokeWidth={SILK} />
)
// A filled-looking pin-1 / cathode triangle pointing +X at (x, y).
const Tri = (p: {x: number; y: number; s?: number}) => {
  const s = p.s ?? 0.7
  return <Line pts={[[p.x - s, p.y + s], [p.x, p.y], [p.x - s, p.y - s], [p.x - s, p.y + s]]} />
}
// Board text: a 2.1 mm font prints capitals 1.19-1.22 mm high overall (about
// 1.0 at the stroke's centre), with a 0.19 mm stroke (JLCPCB: >= 1 mm,
// >= 0.15 mm; tools/check_pcb.py measures it in the Gerber).
const Label = (p: {text: string; x: number; y: number; rot?: number}) => (
  <silkscreentext text={p.text} pcbX={p.x} pcbY={p.y} pcbRotation={p.rot ?? 0} fontSize={2.1} />
)
// Reference designators stay off the silk (too small to print legibly at
// this density); assembly.png shows them instead.
const NOREF = {silkscreenTextVisibility: "hidden" as const}

// --- RP2040-Zero ------------------------------------------------------------
// Waveshare's dimension drawing: module 18.00 x 23.50 mm, 23 castellated pads
// at 2.54 mm pitch: 9 down each side, 5 along the bottom (as tscircuit's own
// rp2040-zero part: stampboard_left9_right9_bottom5). West (top->bottom): 5V
// GND 3V3 GP29 GP28 GP27 GP26 GP15 GP14; east (top->bottom): GP0..GP8; south
// (left->right): GP13..GP9. Side pads' centres 1.59 mm from the top and
// bottom edges; the south ones centred. Pads run 0.5 mm under the module and
// 2.3 mm out. (v1 and v2 had 8 + 8 + 7, which left GP14 on no castellation.)
const zeroWest = ["5V", "GND", "3V3", "GP29", "GP28", "GP27", "GP26", "GP15", "GP14"]
const zeroEast = ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8"]
const zeroSouth = ["GP13", "GP12", "GP11", "GP10", "GP9"]
const zeroPinLabels: Record<string, string> = {}
zeroWest.forEach((n, i) => (zeroPinLabels[`pin${i + 1}`] = n))
zeroEast.forEach((n, i) => (zeroPinLabels[`pin${i + 10}`] = n))
zeroSouth.forEach((n, i) => (zeroPinLabels[`pin${i + 19}`] = n))

const ZeroModule = (p: At) => (
  <chip
    name="U1"
    manufacturerPartNumber="RP2040-Zero"
    pinLabels={zeroPinLabels}
    pcbX={p.x}
    pcbY={p.y}
    doNotPlace // hand-soldered: on hand, and not an LCSC part
    pcbStyle={NOREF}
    footprint={
      <footprint>
        {zeroWest.map((n, k) => (
          <smtpad key={n} portHints={[`pin${k + 1}`]} pcbX={-9.9} pcbY={10.16 - k * 2.54} shape="rect" width={2.8} height={1.1} />
        ))}
        {zeroEast.map((n, k) => (
          <smtpad key={n} portHints={[`pin${k + 10}`]} pcbX={9.9} pcbY={10.16 - k * 2.54} shape="rect" width={2.8} height={1.1} />
        ))}
        {zeroSouth.map((n, k) => (
          <smtpad key={n} portHints={[`pin${k + 19}`]} pcbX={-5.08 + k * 2.54} pcbY={-12.65} shape="rect" width={1.1} height={2.8} />
        ))}
        {/* the module's sides, inside the pad rows, and a dot by the 5V pin */}
        <Line pts={[[-8.1, 11.0], [-8.1, -10.6]]} />
        <Line pts={[[8.1, 11.0], [8.1, -10.6]]} />
        <silkscreencircle pcbX={-12.0} pcbY={11.0} radius={0.35} strokeWidth={SILK} />
        <Court w={23.0} h={26.0} y={-1.25} />
      </footprint>
    }
    connections={{
      "5V": "net.V5",
      GND: "net.GND",
      "3V3": "net.V3",
      GP27: "net.DIAL_WIPER",
      GP26: "net.BATT_SENSE",
      GP15: "net.FAN_PWM",
      GP0: "net.OLED_SDA",
      GP1: "net.OLED_SCL",
      GP14: "net.FAN_TACH",
      GP13: "net.CHG_STAT",
      GP11: "net.SCR_BTN",
    }}
  />
)

// --- MP1584EN, SOIC-8E (MPS) ----------------------------------------------------
// MPS recommended land: pads 1.60 x 0.61 mm at 1.27 mm pitch, rows 5.40 mm
// apart (3.80 mm between their inner ends); exposed pad 2.62 mm across the
// body x 3.51 mm along it, which leaves 0.59 mm to every pin pad. The exposed
// pad is GND (thermal only at this load); a 1.0 mm via in it, left open on the
// back, lets it be soldered from there with an iron (see Buck).
// Pins: 1 SW, 2 EN, 3 COMP, 4 FB (west, top->bottom); 8 BST, 7 VIN, 6 FREQ,
// 5 GND (east, top->bottom).
const mp1584PinLabels = {
  pin1: "SW", pin2: "EN", pin3: "COMP", pin4: "FB",
  pin5: "GND", pin6: "FREQ", pin7: "VIN", pin8: "BST",
  pin9: "EP", pin10: "GNDB",
}
const Mp1584 = (p: At & {tag: string}) => {
  const ys = [1.905, 0.635, -0.635, -1.905]
  const n = (net: string) => `net.${net}_${p.tag}`
  return (
    <chip
      name={`U_${p.tag}`}
      manufacturerPartNumber="MP1584EN-LF-Z"
      supplierPartNumbers={{jlcpcb: ["C15051"]}}
      pinLabels={mp1584PinLabels}
      pcbX={p.x}
      pcbY={p.y}
      pcbRotation={p.rot ?? 0}
      pcbStyle={NOREF}
      footprint={
        <footprint>
          {ys.map((y, k) => (
            <smtpad key={`w${k}`} portHints={[`pin${k + 1}`]} pcbX={-2.7} pcbY={y} shape="rect" width={1.6} height={0.61} />
          ))}
          {ys.map((y, k) => (
            <smtpad key={`e${k}`} portHints={[`pin${8 - k}`]} pcbX={2.7} pcbY={y} shape="rect" width={1.6} height={0.61} />
          ))}
          <smtpad portHints={["pin9"]} pcbX={0} pcbY={0} shape="rect" width={2.62} height={3.51} noSolderPaste />
          {/* a solid GND plane on the bottom, under mask, beneath the block's
              input loop (chip, CIN1, catch diode): no other net's trace can
              cut it, so the diode's return runs right under its path */}
          <smtpad portHints={["pin10"]} layer="bottom" pcbX={0.35} pcbY={3.75} shape="rect" width={15.7} height={14.5} coveredWithSolderMask noSolderPaste />
          {/* the exposed pad's paste, in two windows clear of its 1.0 mm hole */}
          <solderpaste shape="rect" pcbX={0} pcbY={1.18} width={2.42} height={0.95} />
          <solderpaste shape="rect" pcbX={0} pcbY={-1.18} width={2.42} height={0.95} />
          {/* pin 1 dot, beyond pin 1's outer end */}
          <silkscreencircle pcbX={-3.9} pcbY={2.6} radius={0.3} strokeWidth={SILK} />
          <Court w={7.6} h={5.6} />
        </footprint>
      }
      connections={{
        SW: n("SW"), EN: n("EN"), COMP: n("COMP"), FB: n("FB"),
        GND: "net.GND", FREQ: n("FREQ"), VIN: "net.VIN", BST: n("BST"),
        EP: "net.GND", GNDB: "net.GND",
      }}
    />
  )
}

// --- SMA (DO-214AC) diode: SS34 / SS14 ---------------------------------------
// Pads 2.5 x 1.8 mm, centres 4.0 mm apart (body 4.3 x 2.6, leads to 5.6).
// pin1 = K (cathode, -X, the silk bar), pin2 = A.
const SmaDiode = (p: At & {name: string; kNet: string; aNet: string; mpn: string; lcsc: string}) => (
  <chip
    name={p.name}
    manufacturerPartNumber={p.mpn}
    supplierPartNumbers={{jlcpcb: [p.lcsc]}}
    pinLabels={{pin1: "K", pin2: "A"}}
    pcbX={p.x}
    pcbY={p.y}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={-2.0} pcbY={0} shape="rect" width={2.5} height={1.8} />
        <smtpad portHints={["pin2"]} pcbX={2.0} pcbY={0} shape="rect" width={2.5} height={1.8} />
        <Line pts={[[-3.55, 1.0], [-3.55, -1.0]]} />
        <Line pts={[[-0.6, 1.4], [0.6, 1.4]]} />
        <Line pts={[[-0.6, -1.4], [0.6, -1.4]]} />
        <Court w={7.6} h={3.2} x={-0.15} />
      </footprint>
    }
    connections={{K: p.kNet, A: p.aNet}}
  />
)

// --- SOD-323 diode: 1N4148WS ---------------------------------------------------
// Body 1.7 x 1.25, leads to 2.5-2.7 mm. Pads 1.0 x 0.8 mm at +-1.2 mm (a
// little long, for an iron). pin1 = K (-X, the silk bar).
const Sod323 = (p: At & {name: string; kNet: string; aNet: string; dnp?: boolean}) => (
  <chip
    name={p.name}
    manufacturerPartNumber="1N4148WS"
    supplierPartNumbers={{jlcpcb: ["C2128"]}}
    pinLabels={{pin1: "K", pin2: "A"}}
    pcbX={p.x}
    pcbY={p.y}
    doNotPlace={p.dnp}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={-1.2} pcbY={0} shape="rect" width={1.0} height={0.8} />
        <smtpad portHints={["pin2"]} pcbX={1.2} pcbY={0} shape="rect" width={1.0} height={0.8} />
        <Line pts={[[-1.95, 0.6], [-1.95, -0.6]]} />
        <Court w={4.4} h={1.8} x={-0.1} />
      </footprint>
    }
    connections={{K: p.kNet, A: p.aNet}}
  />
)

// --- Sunlord SWPA6045S220MT, 22 uH, 6.0 x 6.0 x 4.5 mm -------------------------
// Datasheet land: pads b 1.7 x c 5.7 mm, a = 2.8 mm between them.
// Isat 2.2 A, rated 1.8 A. 22 uH: MPS's Table 3 range for 12 V (22-33 uH)
// and for 5 V (15-22 uH) out; under 0.5 A peak here.
const Inductor = (p: At & {name: string; inNet: string; outNet: string}) => (
  <chip
    name={p.name}
    manufacturerPartNumber="SWPA6045S220MT"
    supplierPartNumbers={{jlcpcb: ["C83454"]}}
    pinLabels={{pin1: "IN", pin2: "OUT"}}
    pcbX={p.x}
    pcbY={p.y}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={-2.25} pcbY={0} shape="rect" width={1.7} height={5.7} />
        <smtpad portHints={["pin2"]} pcbX={2.25} pcbY={0} shape="rect" width={1.7} height={5.7} />
        <Line pts={[[-1.2, 3.25], [1.2, 3.25]]} />
        <Line pts={[[-1.2, -3.25], [1.2, -3.25]]} />
        <Court w={6.6} h={6.6} />
      </footprint>
    }
    connections={{IN: p.inNet, OUT: p.outNet}}
  />
)

// --- Nichicon UWT1V470MCL1GS, 47 uF 35 V, 6.3 x 5.8 mm ---------------------------
// Base plate 6.6 x 6.6, terminals 2.2 mm apart. Pads 3.0 x 1.6 mm, centres
// 5.2 mm apart. pin1 = + (VIN, -X).
const Electrolytic = (p: At & {name: string; posNet: string; negNet: string}) => (
  <chip
    name={p.name}
    manufacturerPartNumber="UWT1V470MCL1GS"
    supplierPartNumbers={{jlcpcb: ["C87068"]}}
    pinLabels={{pin1: "pos", pin2: "neg"}}
    pcbX={p.x}
    pcbY={p.y}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={-2.6} pcbY={0} shape="rect" width={3.0} height={1.6} />
        <smtpad portHints={["pin2"]} pcbX={2.6} pcbY={0} shape="rect" width={3.0} height={1.6} />
        {/* base plate, chamfered on the + side, and a + */}
        <Line pts={[[-2.0, 3.2], [3.2, 3.2], [3.2, 1.1]]} />
        <Line pts={[[-2.0, -3.2], [3.2, -3.2], [3.2, -1.1]]} />
        <Line pts={[[-2.0, 3.2], [-3.2, 2.0], [-3.2, 1.1]]} />
        <Line pts={[[-2.0, -3.2], [-3.2, -2.0], [-3.2, -1.1]]} />
        <Line pts={[[-5.0, 2.3], [-3.8, 2.3]]} />
        <Line pts={[[-4.4, 2.9], [-4.4, 1.7]]} />
        <Court w={8.8} h={7.2} />
      </footprint>
    }
    connections={{pos: p.posNet, neg: p.negNet}}
  />
)

// --- Through-hole connectors ---------------------------------------------------------
// Pins in a row along X (rot 0) from pin 1, centred; the housing reaches
// `back` to +Y and `front` to -Y (at rot 270, pin 1 is on top and +Y turns
// to +X). Courtyard = the housing, from its drawing, plus 0.2 mm all round.
const HoleConn = (p: At & {
  name: string
  mpn: string
  lcsc: string
  pitch: number
  hole: number
  pad: number
  nets: string[] // pin 1 first
  body: {w: number; front: number; back: number} // along the row; either side of it
  plug?: "from_above" | "from_y_pos" // how the plug or wire goes in, at rot 0
}) => {
  const labels: Record<string, string> = {}
  const conns: Record<string, string> = {}
  p.nets.forEach((n, i) => {
    labels[`pin${i + 1}`] = `P${i + 1}`
    if (n) conns[`P${i + 1}`] = n
  })
  const mid = ((p.nets.length - 1) * p.pitch) / 2
  const halfW = p.body.w / 2
  return (
    <chip
      name={p.name}
      manufacturerPartNumber={p.mpn}
      supplierPartNumbers={{jlcpcb: [p.lcsc]}}
      pinLabels={labels}
      pcbX={p.x}
      pcbY={p.y}
      pcbRotation={p.rot ?? 0}
      pcbStyle={NOREF}
      footprint={
        <footprint insertionDirection={p.plug ?? "from_above"}>
          {p.nets.map((_, k) => (
            <platedhole
              key={k}
              portHints={[`pin${k + 1}`]}
              pcbX={k * p.pitch - mid}
              pcbY={0}
              shape="circle"
              holeDiameter={p.hole}
              outerDiameter={p.pad}
            />
          ))}
          {/* housing outline (its sides drawn 0.4 in, off the board's edge; its
              ends 0.15 in, off the end pins), and pin 1's end marked */}
          <Line pts={[[-halfW + 0.15, p.body.back - 0.4], [halfW - 0.15, p.body.back - 0.4], [halfW - 0.15, -p.body.front + 0.4], [-halfW + 0.15, -p.body.front + 0.4], [-halfW + 0.15, p.body.back - 0.4]]} />
          <Tri x={-halfW - 0.25} y={0} s={0.6} />
          <Court w={p.body.w + 0.4} h={p.body.front + p.body.back + 0.4} y={(p.body.back - p.body.front) / 2} />
        </footprint>
      }
      connections={conns}
    />
  )
}
// JST XH vertical (B2B/B3B/B4B-XH-A): 2.50 mm pitch, housing (n-1) x 2.5 +
// 4.9 long x 5.75 deep, the pins 2.35 mm from one face and 3.4 from the
// other; the courtyard takes 3.4 on both sides. Holes 1.0 mm.
const xh = (n: number) => ({w: (n - 1) * 2.5 + 4.9, front: 3.4, back: 3.4})
const XH_PN: Record<number, [string, string]> = {
  2: ["B2B-XH-A(LF)(SN)", "C158012"],
  3: ["B3B-XH-A(LF)(SN)", "C144394"],
  4: ["B4B-XH-A(LF)(SN)", "C144395"],
}
const Xh = (p: At & {name: string; nets: string[]}) => (
  <HoleConn
    {...p}
    mpn={XH_PN[p.nets.length][0]}
    lcsc={XH_PN[p.nets.length][1]}
    pitch={2.5}
    hole={1.0}
    pad={1.7}
    body={xh(p.nets.length)}
  />
)

const TestPoint = (p: At & {name: string; net: string}) => (
  <chip
    name={p.name}
    pinLabels={{pin1: "TP"}}
    pcbX={p.x}
    pcbY={p.y}
    doNotPlace
    pcbStyle={NOREF}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={0} pcbY={0} shape="circle" radius={0.8} noSolderPaste />
        <Court w={2.0} h={2.0} />
      </footprint>
    }
    connections={{TP: p.net}}
  />
)

// 0805 / 1210 passives. The JLCPCB numbers for the standard values are the
// ones tscircuit's parts engine chose for v1.
const LCSC: Record<string, string> = {
  "10k": "C17414", "22k": "C17560", "24.9k": "C17571", "68.1k": "C17795",
  "100k": "C149504", "140k": "C17460", "200k": "C17539",
  "52.3k": "C273887", // YAGEO RC0805FR-0752K3L, 1 %
  "100nF": "C28233", "220pF": "C107145", "1nF": "C46653",
  "10uF": "C138687", // Samsung CL32B106KBJNNNE, 50 V X7R 1210 (VIN: 16.8 V, up to ~26 V at switch-on)
  "22uF": "C52306", // Samsung CL32A226KAJNNNE, 25 V X5R 1210
}
const R = (p: At & {name: string; value: string; n1: string; n2: string; mpn?: string}) => (
  <resistor
    name={p.name}
    resistance={p.value}
    footprint="0805_nosilkscreen"
    pcbX={p.x}
    pcbY={p.y}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    manufacturerPartNumber={p.mpn}
    supplierPartNumbers={LCSC[p.value] ? {jlcpcb: [LCSC[p.value]]} : undefined}
    connections={{pin1: p.n1, pin2: p.n2}}
  />
)
const C = (p: At & {name: string; value: string; n1: string; n2: string; size?: "0805" | "1210"}) => (
  <capacitor
    name={p.name}
    capacitance={p.value}
    maxDecouplingTraceLength={100} // tscircuit's 1 mm default would stop the autorouter
    footprint={`${p.size ?? "0805"}_nosilkscreen`}
    pcbX={p.x}
    pcbY={p.y}
    pcbRotation={p.rot ?? 0}
    pcbStyle={NOREF}
    supplierPartNumbers={LCSC[p.value] ? {jlcpcb: [LCSC[p.value]]} : undefined}
    connections={{pin1: p.n1, pin2: p.n2}}
  />
)

// --- MP1584 buck --------------------------------------------------------------------
// MPS datasheet: CIN 10 uF (50 V X7R), L 22 uH (Table 3), RFREQ 200k
// (~485 kHz), catch diode, COUT 22 uF, BST 100 nF, EN 100k/24.9k (on above
// ~7.5 V), FB = 0.8 V. COMP 220 pF + 68.1k to GND is the front-page circuit's
// network, not Table 3's: checked here at 56-61 deg phase margin, 20-56 kHz
// crossover. The 12 V buck runs at VOUT/VIN 72-91 %, so it gets the external
// bootstrap diode the datasheet asks for above 65 % (from the 5 V rail).
//
// Layout, chip turned 90 deg so its pins face +Y and -Y:
//   top row    BST VIN FREQ GND  -> CIN1 across VIN..GND right above the
//              pins (FREQ runs up between its pads to RFREQ), CIN2 beside it
//   bottom row SW  EN  COMP FB   -> EN, COMP, FB fan straight down to their
//              parts, so nothing crosses and FB's node is short
//   SW (bottom-left) -> catch diode right below it, CBST up the chip's left
//   side to BST, the inductor beyond, the output caps on its far end.
// The input loop (CIN1 -> VIN -> SW -> diode -> GND) closes through the
// chip's bottom GND plane: vias at the diode's anode and by CIN1, and the
// exposed pad's hole, join it to the top.
// `flip` turns the whole block 180 deg, so its layout (and the drawn paths,
// which are in the chip's own frame) stays the same.
const Buck = (p: {tag: string; x: number; y: number; flip?: boolean; vout: string; fbTop: string; fbTopMpn?: string; bstDiode?: boolean}) => {
  const {tag, vout} = p
  const n = (s: string) => `net.${s}_${tag}`
  const k = p.flip ? -1 : 1
  // a part at block offset (dx, dy), turned r degrees
  const at = (dx: number, dy: number, r = 0): At => ({x: p.x + k * dx, y: p.y + k * dy, rot: (r + (p.flip ? 180 : 0)) % 360})
  return (
    <>
      <Mp1584 tag={tag} {...at(0, 0, 90)} />
      {/* solder-access hole through the exposed pad, open on the back */}
      <via pcbX={p.x} pcbY={p.y} holeDiameter={1.0} outerDiameter={1.8} connectsTo="net.GND" tented="exposed" />
      {/* the input loop's return: diode anode, CIN1 and CIN2 down to the bottom plane */}
      {([[-9.6, -7.1], [-8.4, -7.1], [3.2, 4.9], [-3.0, 7.75]] as [number, number][]).map(([dx, dy], i) => {
        const v = at(dx, dy)
        return <via key={`gv${i}`} pcbX={v.x} pcbY={v.y} holeDiameter={0.3} outerDiameter={0.7} connectsTo="net.GND" />
      })}
      {p.bstDiode && (
        <Sod323 name={`D_BST_${tag}`} kNet={n("BST")} aNet="net.V5RAW" {...at(-5.0, 5.8, 90)} />
      )}
      <C name={`CIN1_${tag}`} value="10uF" size="1210" n1="net.VIN" n2="net.GND" {...at(0.635, 5.6, 0)} />
      <C name={`CIN2_${tag}`} value="100nF" n1="net.VIN" n2="net.GND" {...at(-3.0, 5.6, 90)} />
      <R name={`RFREQ_${tag}`} value="200k" n1={n("FREQ")} n2="net.GND" {...at(4.4, 7.0, 270)} />
      <C name={`CBST_${tag}`} value="100nF" n1={n("BST")} n2={n("SW")} {...at(-4.0, 0, 270)} />
      <Inductor name={`L_${tag}`} inNet={n("SW")} outNet={vout} {...at(-8.6, 0, 180)} />
      <C name={`COUT1_${tag}`} value="22uF" size="1210" n1={vout} n2="net.GND" {...at(-9.5, 5.0, 0)} />
      <C name={`COUT2_${tag}`} value="100nF" n1={vout} n2="net.GND" {...at(-9.5, 7.85, 0)} />
      <SmaDiode name={`DC_${tag}`} mpn="SS34" lcsc="C115205" kNet={n("SW")} aNet="net.GND" {...at(-7.0, -5.4, 180)} />
      <R name={`RFB2_${tag}`} value="10k" n1={n("FB")} n2="net.GND" {...at(3.8, -5.2, 270)} />
      <R name={`RFB1_${tag}`} value={p.fbTop} mpn={p.fbTopMpn} n1={vout} n2={n("FB")} {...at(5.8, -5.2, 90)} />
      <C name={`CCOMP_${tag}`} value="220pF" n1={n("COMP")} n2={n("COMPX")} {...at(0.635, -5.6, 270)} />
      <R name={`RCOMP_${tag}`} value="68.1k" n1={n("COMPX")} n2="net.GND" {...at(0.635, -9.1, 270)} />
      <R name={`REN2_${tag}`} value="24.9k" n1={n("EN")} n2="net.GND" {...at(-1.6, -9.1, 270)} />
      <R name={`REN1_${tag}`} value="100k" n1="net.VIN" n2={n("EN")} {...at(-3.6, -9.1, 90)} />

      {/* The block's own wiring, drawn rather than autorouted, so SW, the input
          loop and FB stay as short as the datasheet asks. Paths are block
          offsets from the chip's centre (Wire turns them into the chip's frame). */}
      <Wire tag={tag} name="sw_d" from={`.U_${tag} > .SW`} to={`.DC_${tag} > .K`} w={0.6} />
      <Wire tag={tag} name="sw_cbst" from={`.U_${tag} > .SW`} to={`.CBST_${tag} > .pin2`} w={0.6} />
      <Wire tag={tag} name="sw_l" from={`.CBST_${tag} > .pin2`} to={`.L_${tag} > .IN`} w={0.6} />
      <Wire tag={tag} name="bst" from={`.U_${tag} > .BST`} to={`.CBST_${tag} > .pin1`} w={0.3} path={[[-4.0, 2.7]]} />
      {p.bstDiode && <Wire tag={tag} name="bst_d" from={`.D_BST_${tag} > .K`} to={`.CBST_${tag} > .pin1`} w={0.3} />}
      <Wire tag={tag} name="vin" from={`.U_${tag} > .VIN`} to={`.CIN1_${tag} > .pin1`} w={0.6} />
      <Wire tag={tag} name="vin2" from={`.CIN1_${tag} > .pin1`} to={`.CIN2_${tag} > .pin1`} w={0.6} />
      <Wire tag={tag} name="gnd" from={`.U_${tag} > .GND`} to={`.CIN1_${tag} > .pin2`} w={0.6} />
      <Wire tag={tag} name="freq" from={`.U_${tag} > .FREQ`} to={`.RFREQ_${tag} > .pin1`} w={0.3} path={[[0.635, 7.912]]} />
      <Wire tag={tag} name="fb" from={`.U_${tag} > .FB`} to={`.RFB2_${tag} > .pin1`} w={0.3} />
      <Wire tag={tag} name="fb2" from={`.RFB2_${tag} > .pin1`} to={`.RFB1_${tag} > .pin2`} w={0.3} />
      <Wire tag={tag} name="comp" from={`.U_${tag} > .COMP`} to={`.CCOMP_${tag} > .pin1`} w={0.3} />
      <Wire tag={tag} name="compx" from={`.CCOMP_${tag} > .pin2`} to={`.RCOMP_${tag} > .pin1`} w={0.3} />
      <Wire tag={tag} name="en" from={`.U_${tag} > .EN`} to={`.REN2_${tag} > .pin1`} w={0.3} path={[[-1.0, -3.6], [-1.0, -7.6]]} />
      <Wire tag={tag} name="en2" from={`.REN2_${tag} > .pin1`} to={`.REN1_${tag} > .pin2`} w={0.3} />
      <Wire tag={tag} name="vout" from={`.L_${tag} > .OUT`} to={`.COUT1_${tag} > .pin1`} w={0.6} />
      <Wire tag={tag} name="vout2" from={`.COUT1_${tag} > .pin1`} to={`.COUT2_${tag} > .pin1`} w={0.6} />
    </>
  )
}

// A drawn trace: straight from pad to pad, or through `path`. tscircuit takes
// path points in the `from` part's own frame; every path here starts at the
// buck chip, turned 90 deg, so a block offset (x, y) is (y, -x) in its frame.
const Wire = (p: {tag: string; name: string; from: string; to: string; w: number; path?: [number, number][]}) =>
  p.path ? (
    <trace name={`${p.name}_${p.tag}`} from={p.from} to={p.to} thickness={p.w} pcbPath={p.path.map(([x, y]) => ({x: y, y: -x}))} />
  ) : (
    <trace name={`${p.name}_${p.tag}`} from={p.from} to={p.to} thickness={p.w} pcbStraightLine />
  )

// --- The board ---------------------------------------------------------------------------
// Base X/Z -> local: (42 - X, Z - 50).
// X 58.5 on the +X side clears the corner bosses (59.5) and leaves the strip
// along the +X wall, under the USB-C socket and the button, to their wires.
const OUTLINE: [number, number][] = [
  [24, -46.5], // X 18 (sled + 1), Z 3.5
  [24, 46.5], // Z 96.5: the Zero's USB-C at the rear wall
  [-16.5, 46.5], // X 58.5
  [-16.5, -16], // Z 34: the pot comes below the board's top from here...
  [-1.5, -16], // X 43.5 (the pot from X 44)
  [-1.5, -36], // ... to Z 14
  [-16.5, -36],
  [-16.5, -46.5],
]
// M2 holes onto the plate's bosses (base X, Z in models/carrier_pcb.scad).
// The plate's vent slots (X 20..42, Z 33..62) and its feet's recesses
// (X 55, Z 16 / 84) keep the bosses off those spots.
const HOLES: [number, number][] = [
  [21, -43.5],
  [-13.5, -43.5],
  [1.5, -19.8],
  [-13.7, -7.4],
  [-5.5, 9.5],
  [-13.5, 24],
  [21, 43.5],
  [-13, 43.5],
]

export default () => (
  <board
    name="table-fan-carrier-psu"
    outline={OUTLINE.map(([x, y]) => ({x, y}))}
    thickness={1.6}
    fabricatorPreset="jlcpcb_standard"
    isViaInPadAllowed // only the bucks' solder-access holes, in their exposed pads
    // 0.3 / 0.7 mm vias (0.2 mm ring): the router keeps a via's 0.7 clear of
    // other traces, where at 0.6 it left 0.115 mm
    pcbStyle={{viaHoleDiameter: 0.3, viaPadDiameter: 0.7}}
    minViaHoleDiameter={0.3}
    minViaPadDiameter={0.7}
    minTraceWidth={0.25}
    minTraceToPadEdgeClearance={0.17}
    minPadEdgeToPadEdgeClearance={0.2}
    minViaEdgeToPadEdgeClearance={0.3} // also keeps GND vias off GND pads' mask openings
    minViaHoleEdgeToViaHoleEdgeClearance={0.5}
    minTraceToHoleEdgeClearance={0.3}
    minBoardEdgeClearance={0.5}
    autorouter={{traceClearance: 0.2, allowViaInPad: false}}
    // this router version gives a clean route here (the default one shorted
    // FAN_TACH into VIN near buck A); tools/check_pcb.py verifies the result
    autorouterVersion="beta_pipeline7"
    defaultTraceWidth={0.3}
    // Two phases: every other net first, then GND, which the pours carry;
    // the router adds GND traces and vias only where a pad's patch of pour
    // needs joining to the rest
    routeRemaining={false}
    // tscircuit's routing DRC counts only traces, not copper joined through
    // the bottom planes and their vias; tools/check_pcb.py checks the copper
    // itself, stricter, and `npm run gerbers` ends with it
    routingDrcChecksDisabled
  >
    <net name="GND" isGroundNet routingPhaseIndex={1} />
    <net name="VIN" isPowerNet nominalTraceWidth={0.5} routingPhaseIndex={0} />
    <net name="V12" isPowerNet nominalTraceWidth={0.5} routingPhaseIndex={0} />
    <net name="FAN12" isPowerNet nominalTraceWidth={0.5} routingPhaseIndex={0} />
    <net name="BENCH12" isPowerNet nominalTraceWidth={0.5} routingPhaseIndex={0} />
    <net name="V5RAW" isPowerNet nominalTraceWidth={0.4} routingPhaseIndex={0} />
    <net name="V5" isPowerNet nominalTraceWidth={0.4} routingPhaseIndex={0} />
    <net name="V3" isPowerNet routingPhaseIndex={0} />
    <net name="BATT_SENSE" routingPhaseIndex={0} />
    <net name="FAN_TACH" routingPhaseIndex={0} />
    <net name="FAN_PWM" routingPhaseIndex={0} />
    <net name="DIAL_WIPER" routingPhaseIndex={0} />
    <net name="OLED_SDA" routingPhaseIndex={0} />
    <net name="OLED_SCL" routingPhaseIndex={0} />
    <net name="CHG_STAT" routingPhaseIndex={0} />
    <net name="CHG_RAW" routingPhaseIndex={0} />
    <net name="SCR_BTN" routingPhaseIndex={0} />

    {/* RP2040-Zero: its top edge on the board's rear edge, USB-C at the cutout (X 37.5) */}
    <ZeroModule x={4.5} y={34.75} />

    {/* Bucks: A = 12 V fan rail, B = 5 V for the Zero; each block turned
        180 deg, its inductor toward the board's +x side */}
    <Buck tag="A" x={11.8} y={-6.18} flip bstDiode vout="net.V12" fbTop="140k" />
    <Buck tag="B" x={-7.1} y={-6.18} flip vout="net.V5RAW" fbTop="52.3k" fbTopMpn="RC0805FR-0752K3L" />

    {/* VIN in, and its bulk capacitor: damps the ringing when the dial's switch
        connects the pack through its leads to the bucks' ceramic inputs */}
    <HoleConn
      name="J1_VIN"
      mpn="KF301-5.0-2P"
      lcsc="C474881"
      x={3.3}
      y={-27.5}
      rot={270}
      pitch={5.0}
      hole={1.3}
      pad={2.4}
      nets={["net.VIN", "net.GND"]}
      body={{w: 10.67, front: 4.0, back: 3.6}} // 7.6 deep, 3.6 on the wire side: +x, base -X, away from the pot
      plug="from_y_pos"
    />
    {/* + and - at J1's wire entry, drawn: text this small prints as a dot */}
    <silkscreenpath route={[{x: 7.6, y: -25}, {x: 9.2, y: -25}]} strokeWidth={SILK} />
    <silkscreenpath route={[{x: 8.4, y: -25.8}, {x: 8.4, y: -24.2}]} strokeWidth={SILK} />
    <silkscreenpath route={[{x: 7.6, y: -30}, {x: 9.2, y: -30}]} strokeWidth={SILK} />
    <Electrolytic name="C_BULK" posNet="net.VIN" negNet="net.GND" x={-6.5} y={-42.9} rot={180} />

    {/* 12 V diode-OR: pack buck and bench input join at FAN12 */}
    <SmaDiode name="D_OR" mpn="SS34" lcsc="C115205" kNet="net.FAN12" aNet="net.V12" x={14} y={-28} rot={90} />
    <SmaDiode name="D_BENCH" mpn="SS34" lcsc="C115205" kNet="net.FAN12" aNet="net.BENCH12" x={10.5} y={-34} rot={270} />
    {/* 5 V feed protection (SS14): buck B -> Zero 5V pin, so USB can't back-feed the buck;
        beside the Zero's 5V pad, at its top-left corner */}
    <SmaDiode name="D_5V" mpn="SS14" lcsc="C2480" kNet="net.V5" aNet="net.V5RAW" x={-9.5} y={37.5} rot={90} />

    {/* Battery divider 100k/22k + 100nF -> GP26 (on the switched VIN) */}
    <R name="R_DIV1" value="100k" n1="net.VIN" n2="net.BATT_SENSE" x={8.5} y={7.0} rot={180} />
    <R name="R_DIV2" value="22k" n1="net.BATT_SENSE" n2="net.GND" x={5} y={7.0} rot={180} />
    <C name="C_DIV" value="100nF" n1="net.BATT_SENSE" n2="net.GND" x={5} y={10} rot={180} />

    {/* Tach pull-up 10k to 3V3 + 1nF -> GP14 */}
    <R name="R_TACH" value="10k" n1="net.V3" n2="net.FAN_TACH" x={12.2} y={16} rot={270} />
    <C name="C_TACH" value="1nF" n1="net.FAN_TACH" n2="net.GND" x={12.2} y={12.4} rot={270} />

    {/* Charger status: 10k series + optional 1N4148 clamp to 3V3 -> GP13 */}
    <R name="R_STAT" value="10k" n1="net.CHG_RAW" n2="net.CHG_STAT" x={15} y={12} rot={90} />
    {/* fitted by hand, and only if the charger's STAT pin measures above 3.3 V */}
    <Sod323 name="D_CLAMP" kNet="net.V3" aNet="net.CHG_STAT" x={15} y={16} rot={270} dnp />

    {/* Connectors */}
    <HoleConn
      name="J2_FAN"
      mpn="47053-1000"
      lcsc="C240840"
      x={20.2}
      y={-28}
      rot={270}
      pitch={2.54}
      hole={1.0}
      pad={1.75}
      nets={["net.GND", "net.FAN12", "net.FAN_TACH", "net.FAN_PWM"]}
      body={{w: 10.2, front: 3.5, back: 3.5}} // 10.2 x 5.84, keyed; 3.5 both sides to be safe
    />
    <Xh name="J3_DIAL" x={20.4} y={21.8} rot={270} nets={["net.V3", "net.DIAL_WIPER", "net.GND"]} />
    <Xh name="J4_OLED" x={20.4} y={33.75} rot={270} nets={["net.GND", "net.V3", "net.OLED_SCL", "net.OLED_SDA"]} />
    <Xh name="J5_BTN" x={-12.8} y={16.5} rot={270} nets={["net.SCR_BTN", "net.GND"]} />
    <Xh name="J6_CHG" x={20.4} y={12} rot={270} nets={["net.CHG_RAW", "net.GND"]} />
    <Xh name="J7_BENCH" x={13} y={-42.5} rot={180} nets={["net.BENCH12", "net.GND"]} />

    {/* Test points */}
    <TestPoint name="TP_VIN" net="net.VIN" x={5.5} y={-20.3} />
    <TestPoint name="TP_12V" net="net.FAN12" x={14} y={-36} />
    <TestPoint name="TP_5V" net="net.V5" x={-8.6} y={44.6} />
    <TestPoint name="TP_3V3" net="net.V3" x={-9.8} y={27.5} />
    <TestPoint name="TP_GND" net="net.GND" x={-9.8} y={31} />

    {/* The notch round the pot is off the board: keep the router out of it,
        and 0.5 mm off its edges */}
    <keepout shape="rect" pcbX={-9.25} pcbY={-26} width={16.5} height={21} layers={["top", "bottom"]} />

    {/* Mounting holes (M2) onto the plate's bosses */}
    {HOLES.map(([x, y], i) => (
      <hole key={i} diameter={2.4} pcbX={x} pcbY={y} />
    ))}

    {/* Ground pours, both layers; thermal spokes on every GND pad */}
    <copperpour layer="top" connectsTo="net.GND" clearance={0.32} boardEdgeMargin={0.5} useThermalReliefs />
    <copperpour layer="bottom" connectsTo="net.GND" clearance={0.32} boardEdgeMargin={0.5} useThermalReliefs />

    {/* Silkscreen: what each connector is, which way round, test points */}
    <Label text="CARRIER+PSU V2.1" x={11.3} y={-16.2} />
    <Label text="FAN" x={20.5} y={-20.5} />
    <Label text="DIAL" x={15.4} y={21.5} rot={90} />
    <Label text="BENCH" x={13} y={-38.3} />
    <Label text="CHG" x={20.5} y={7.0} />
    <Label text="BTN" x={-7.6} y={16.5} rot={90} />
    <Label text="OLED" x={19.4} y={41.3} />
    <Label text="12V" x={17.5} y={-36} />
    <Label text="VIN" x={9} y={-20.3} />
    <Label text="5V" x={-8.6} y={42.5} />
    <Label text="3V3" x={-12.6} y={27.5} />
    <Label text="GND" x={-12.6} y={31} />
  </board>
)
