// ---------------------------------------------------------------------------
// Table Fan — Carrier + PSU board v1
// Replaces the perfboard carrier AND both MP1584 mini buck modules.
// Board: 47 x 92 mm, 2-layer. Local coords: origin at board centre,
// +X = base +X (dial side), +Y = rear (Zero USB-C end).
// Base coords -> board local: X_local = X_base - 42.5, Y_local = Z_base - 50.
// ---------------------------------------------------------------------------

// --- RP2040-Zero ------------------------------------------------------------
// Footprint from Waveshare's official dimension drawing:
// module 18.00 x 23.50 mm, castellated pads at 2.54 mm pitch.
// West column (top->bottom): 5V GND 3V3 GP29 GP28 GP27 GP26 GP15
// East column (top->bottom): GP0 GP1 GP2 GP3 GP4 GP5 GP6 GP7
// South row  (left->right):  GP14 GP13 GP12 GP11 GP10 GP9 GP8
// Side pads: first centre 1.59 mm from the top edge.
// South pads: first centre 1.38 mm from the left edge.
const zeroWest = ["5V", "GND", "3V3", "GP29", "GP28", "GP27", "GP26", "GP15"]
const zeroEast = ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7"]
const zeroSouth = ["GP14", "GP13", "GP12", "GP11", "GP10", "GP9", "GP8"]

const zeroPinLabels: Record<string, string> = {}
zeroWest.forEach((n, i) => (zeroPinLabels[`pin${i + 1}`] = n))
zeroEast.forEach((n, i) => (zeroPinLabels[`pin${i + 9}`] = n))
zeroSouth.forEach((n, i) => (zeroPinLabels[`pin${i + 17}`] = n))

const ZeroModule = (props: {pcbX: number; pcbY: number}) => (
  <chip
    name="U1"
    pinLabels={zeroPinLabels}
    pcbX={props.pcbX}
    pcbY={props.pcbY}
    footprint={
      <footprint>
        {zeroWest.map((n, k) => (
          <smtpad
            key={n}
            portHints={[`pin${k + 1}`]}
            pcbX={-9.9}
            pcbY={10.16 - k * 2.54}
            shape="rect"
            width={2.8}
            height={1.1}
          />
        ))}
        {zeroEast.map((n, k) => (
          <smtpad
            key={n}
            portHints={[`pin${k + 9}`]}
            pcbX={9.9}
            pcbY={10.16 - k * 2.54}
            shape="rect"
            width={2.8}
            height={1.1}
          />
        ))}
        {zeroSouth.map((n, k) => (
          <smtpad
            key={n}
            portHints={[`pin${k + 17}`]}
            pcbX={-7.62 + k * 2.54}
            pcbY={-12.65}
            shape="rect"
            width={1.1}
            height={2.8}
          />
        ))}
        <silkscreenrect pcbX={0} pcbY={0} width={18.6} height={24.1} />
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

// --- MP1584EN buck (SOIC-8E) -------------------------------------------------
// Datasheet typical application: CIN 10uF, L 10uH @ RT 200k (~500 kHz),
// SS34 catch diode, COUT 22uF, BST 100nF, EN divider 100k/24.9k,
// COMP = 220pF in series with 68.1k to GND, FB ref 0.8 V.
// Pins (top view): 1 SW, 2 EN, 3 COMP, 4 FB (west, top->bottom);
// 8 BST, 7 VIN, 6 FREQ, 5 GND (east, top->bottom); pin9 = exposed pad.
const mp1584PinLabels = {
  pin1: "SW",
  pin2: "EN",
  pin3: "COMP",
  pin4: "FB",
  pin5: "GND",
  pin6: "FREQ",
  pin7: "VIN",
  pin8: "BST",
  pin9: "EP",
}

const SmaDiode = (props: {
  name: string
  pcbX: number
  pcbY: number
  pcbRotation?: number
  kNet?: string
  aNet?: string
}) => {
  const conns: Record<string, string> = {}
  if (props.kNet) conns.K = props.kNet
  if (props.aNet) conns.A = props.aNet
  return (
    <chip
      name={props.name}
      pinLabels={{pin1: "K", pin2: "A"}}
      pcbX={props.pcbX}
      pcbY={props.pcbY}
      pcbRotation={props.pcbRotation ?? 0}
      footprint={
        <footprint>
          <smtpad portHints={["pin1"]} pcbX={-1.65} pcbY={0} shape="rect" width={1.9} height={2.5} />
          <smtpad portHints={["pin2"]} pcbX={1.65} pcbY={0} shape="rect" width={1.9} height={2.5} />
        </footprint>
      }
      connections={conns}
    />
  )
}

const PowerInductor = (props: {
  name: string
  pcbX: number
  pcbY: number
  inNet: string
  outNet: string
}) => (
  <chip
    name={props.name}
    pinLabels={{pin1: "IN", pin2: "OUT"}}
    pcbX={props.pcbX}
    pcbY={props.pcbY}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={-3.05} pcbY={0} shape="rect" width={4.3} height={4.8} />
        <smtpad portHints={["pin2"]} pcbX={3.05} pcbY={0} shape="rect" width={4.3} height={4.8} />
        <silkscreenrect pcbX={0} pcbY={0} width={10.6} height={10.6} />
      </footprint>
    }
    connections={{IN: props.inNet, OUT: props.outNet}}
  />
)

// One complete buck. All small parts placed relative to the chip centre.
// Layout: chip at (x, y); inductor east; CIN north-east; catch diode
// north-west of SW; FB divider south-east; comp/freq/en south.
const Buck = (props: {
  tag: string // "A" (12 V) or "B" (5 V)
  x: number
  y: number
  voutNet: string
  fbTop: string
}) => {
  const {tag, x, y, voutNet} = props
  const sw = `net.SW_${tag}`
  const bst = `net.BST_${tag}`
  const en = `net.EN_${tag}`
  const comp = `net.COMP_${tag}`
  const compx = `net.COMPX_${tag}`
  const fb = `net.FB_${tag}`
  const freq = `net.FREQ_${tag}`
  return (
    <>
      <chip
        name={`U_${tag}`}
        pinLabels={mp1584PinLabels}
        pcbX={x}
        pcbY={y}
        footprint={
          <footprint>
            <smtpad portHints={["pin1"]} pcbX={-2.6} pcbY={1.905} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin2"]} pcbX={-2.6} pcbY={0.635} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin3"]} pcbX={-2.6} pcbY={-0.635} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin4"]} pcbX={-2.6} pcbY={-1.905} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin5"]} pcbX={2.6} pcbY={-1.905} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin6"]} pcbX={2.6} pcbY={-0.635} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin7"]} pcbX={2.6} pcbY={0.635} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin8"]} pcbX={2.6} pcbY={1.905} shape="rect" width={1.5} height={0.65} />
            <smtpad portHints={["pin9"]} pcbX={0} pcbY={0} shape="rect" width={3.4} height={2.4} />
          </footprint>
        }
        connections={{
          SW: sw,
          EN: en,
          COMP: comp,
          FB: fb,
          GND: "net.GND",
          FREQ: freq,
          BST: bst,
          EP: "net.GND",
        }}
      />
      {/* input caps, tight to VIN pin (east side) */}
      <capacitor maxDecouplingTraceLength={100}
        name={`CIN1_${tag}`}
        capacitance="10uF"
        footprint="1210"
        pcbX={x + 6.4}
        pcbY={y + 1.2}
        connections={{pin1: "net.GND"}}
      />
      <capacitor maxDecouplingTraceLength={100}
        name={`CIN2_${tag}`}
        capacitance="100nF"
        footprint="0805"
        pcbX={x + 6.2}
        pcbY={y + 4.6}
        connections={{pin2: "net.GND"}}
      />
      {/* bootstrap cap BST->SW, north of the chip */}
      <capacitor maxDecouplingTraceLength={100}
        name={`CBST_${tag}`}
        capacitance="100nF"
        footprint="0805"
        pcbX={x}
        pcbY={y + 4.8}
        pcbRotation={90}
        connections={{pin1: bst, pin2: sw}}
      />
      {/* catch diode, west of SW pin */}
      <SmaDiode name={`DC_${tag}`} pcbX={x - 6.6} pcbY={y + 1.9} kNet={sw} aNet="net.GND" />
      {/* inductor + output caps, east */}
      <PowerInductor name={`L_${tag}`} pcbX={x + 9.2} pcbY={y - 4.6} inNet={sw} outNet={voutNet} />
      <capacitor maxDecouplingTraceLength={100}
        name={`COUT1_${tag}`}
        capacitance="22uF"
        footprint="1210"
        pcbX={x + 16.2}
        pcbY={y - 4.6}
        pcbRotation={90}
        connections={{pin1: voutNet, pin2: "net.GND"}}
      />
      <capacitor maxDecouplingTraceLength={100}
        name={`COUT2_${tag}`}
        capacitance="100nF"
        footprint="0805"
        pcbX={x + 12.6}
        pcbY={y + 0.6}
        connections={{pin1: voutNet, pin2: "net.GND"}}
      />
      {/* feedback divider, south-west, right under the FB pin */}
      <resistor
        name={`RFB1_${tag}`}
        resistance={props.fbTop}
        footprint="0805"
        pcbX={x - 5.2}
        pcbY={y - 5.2}
        pcbRotation={90}
        connections={{pin1: voutNet, pin2: fb}}
      />
      <resistor
        name={`RFB2_${tag}`}
        resistance="10k"
        footprint="0805"
        pcbX={x - 5.2}
        pcbY={y - 9.2}
        pcbRotation={90}
        connections={{pin1: fb, pin2: "net.GND"}}
      />
      {/* compensation, south-east */}
      <capacitor maxDecouplingTraceLength={100}
        name={`CCOMP_${tag}`}
        capacitance="220pF"
        footprint="0805"
        pcbX={x + 8.6}
        pcbY={y - 8.6}
        connections={{pin1: comp, pin2: compx}}
      />
      <resistor
        name={`RCOMP_${tag}`}
        resistance="68.1k"
        footprint="0805"
        pcbX={x + 8.6}
        pcbY={y - 11.4}
        connections={{pin1: compx, pin2: "net.GND"}}
      />
      {/* freq set + enable divider, south */}
      <resistor
        name={`RFREQ_${tag}`}
        resistance="200k"
        footprint="0805"
        pcbX={x + 2.2}
        pcbY={y - 7.4}
        connections={{pin1: freq, pin2: "net.GND"}}
      />
      <resistor
        name={`REN1_${tag}`}
        resistance="100k"
        footprint="0805"
        pcbX={x - 0.6}
        pcbY={y - 5.4}
        connections={{pin2: en}}
      />
      <resistor
        name={`REN2_${tag}`}
        resistance="24.9k"
        footprint="0805"
        pcbX={x - 1.2}
        pcbY={y - 9.8}
        connections={{pin1: en, pin2: "net.GND"}}
      />
    </>
  )
}

// --- Connectors ---------------------------------------------------------------
const HoleConn = (props: {
  name: string
  pcbX: number
  pcbY: number
  pitch: number
  holeDiameter: number
  outerDiameter: number
  nets: string[] // pin1 first (top-most pin)
  horizontal?: boolean
}) => {
  const labels: Record<string, string> = {}
  props.nets.forEach((_, i) => (labels[`pin${i + 1}`] = `P${i + 1}`))
  const conns: Record<string, string> = {}
  props.nets.forEach((n, i) => {
    if (n) conns[`P${i + 1}`] = n
  })
  const mid = ((props.nets.length - 1) * props.pitch) / 2
  return (
    <chip
      name={props.name}
      pinLabels={labels}
      pcbX={props.pcbX}
      pcbY={props.pcbY}
      footprint={
        <footprint>
          {props.nets.map((_, k) => (
            <platedhole
              key={k}
              portHints={[`pin${k + 1}`]}
              pcbX={props.horizontal ? k * props.pitch - mid : 0}
              pcbY={props.horizontal ? 0 : mid - k * props.pitch}
              shape="circle"
              holeDiameter={props.holeDiameter}
              outerDiameter={props.outerDiameter}
            />
          ))}
        </footprint>
      }
      connections={conns}
    />
  )
}

const TestPoint = (props: {name: string; pcbX: number; pcbY: number; net: string}) => (
  <chip
    name={props.name}
    pinLabels={{pin1: "TP"}}
    pcbX={props.pcbX}
    pcbY={props.pcbY}
    footprint={
      <footprint>
        <smtpad portHints={["pin1"]} pcbX={0} pcbY={0} shape="circle" radius={0.9} />
      </footprint>
    }
    connections={{TP: props.net}}
  />
)

// --- The board ------------------------------------------------------------------
export default () => (
  <board width={47} height={92} name="table-fan-carrier-psu">
    <net name="GND" />
    <net name="VIN" />
    <net name="V12" />
    <net name="FAN12" />
    <net name="V5RAW" />
    <net name="V5" />
    <net name="V3" />
    <net name="BATT_SENSE" />
    <net name="FAN_TACH" />
    <net name="FAN_PWM" />
    <net name="DIAL_WIPER" />
    <net name="OLED_SDA" />
    <net name="OLED_SCL" />
    <net name="CHG_STAT" />
    <net name="CHG_RAW" />
    <net name="SCR_BTN" />
    <net name="BENCH12" />

    {/* RP2040-Zero, USB-C at the rear edge */}
    <ZeroModule pcbX={-5} pcbY={33.25} />
    <silkscreentext text="RP2040-ZERO  USB ^" pcbX={-5} pcbY={47.2} fontSize={1.4} />

    {/* Bucks: A = 12 V fan rail (front), B = 5 V Zero rail (behind it) */}
    <Buck tag="A" x={-8} y={-6} voutNet="net.V12" fbTop="140k" />
    <Buck tag="B" x={-8} y={-28} voutNet="net.V5RAW" fbTop="52.5k" />

    {/* 12 V diode-OR: pack buck and bench input join at FAN12 */}
    <SmaDiode name="D_OR" pcbX={-1} pcbY={5} pcbRotation={90} kNet="net.FAN12" aNet="net.V12" />
    <SmaDiode name="D_BENCH" pcbX={-19.3} pcbY={-24.8} pcbRotation={90} kNet="net.FAN12" aNet="net.BENCH12" />
    {/* 5 V feed protection (SS14): buck B -> Zero 5V pin */}
    <SmaDiode name="D_5V" pcbX={7} pcbY={-17} pcbRotation={90} aNet="net.V5RAW" />

    {/* Battery divider 100k/22k + 100nF -> GP26 (on the switched bus) */}
    <resistor
      name="R_DIV1"
      resistance="100k"
      footprint="0805"
      pcbX={-11}
      pcbY={13}
      connections={{pin2: "net.BATT_SENSE"}}
    />
    <resistor
      name="R_DIV2"
      resistance="22k"
      footprint="0805"
      pcbX={-7.4}
      pcbY={13}
      connections={{pin1: "net.BATT_SENSE", pin2: "net.GND"}}
    />
    <capacitor maxDecouplingTraceLength={100}
      name="C_DIV"
      capacitance="100nF"
      footprint="0805"
      pcbX={-7.4}
      pcbY={9.3}
      connections={{pin1: "net.BATT_SENSE", pin2: "net.GND"}}
    />

    {/* Tach pull-up 10k to 3V3 + 1nF -> GP14 */}
    <resistor
      name="R_TACH"
      resistance="10k"
      footprint="0805"
      pcbX={-15.6}
      pcbY={14.5}
      pcbRotation={90}
      connections={{pin1: "net.V3", pin2: "net.FAN_TACH"}}
    />
    <capacitor maxDecouplingTraceLength={100}
      name="C_TACH"
      capacitance="1nF"
      footprint="0805"
      pcbX={-15.6}
      pcbY={10.8}
      pcbRotation={90}
      connections={{pin1: "net.FAN_TACH", pin2: "net.GND"}}
    />

    {/* Charger status: 10k series + optional 1N4148 clamp to 3V3 -> GP13 */}
    <resistor
      name="R_STAT"
      resistance="10k"
      footprint="0805"
      pcbX={-17.6}
      pcbY={-10.5}
      pcbRotation={90}
      connections={{pin1: "net.CHG_RAW", pin2: "net.CHG_STAT"}}
    />
    <chip
      name="D_CLAMP"
      pinLabels={{pin1: "K", pin2: "A"}}
      pcbX={-17.6}
      pcbY={-16.5}
      pcbRotation={90}
      footprint={
        <footprint>
          <smtpad portHints={["pin1"]} pcbX={0} pcbY={1.15} shape="rect" width={1.1} height={1.2} />
          <smtpad portHints={["pin2"]} pcbX={0} pcbY={-1.15} shape="rect" width={1.1} height={1.2} />
        </footprint>
      }
      connections={{K: "net.V3", A: "net.CHG_STAT"}}
    />

    {/* Connectors */}
    <HoleConn
      name="J1_VIN"
      pcbX={17.5}
      pcbY={-36}
      pitch={5.08}
      holeDiameter={1.4}
      outerDiameter={2.6}
      horizontal
      nets={["net.VIN", "net.GND"]}
    />
    <HoleConn
      name="J2_FAN"
      pcbX={-20.6}
      pcbY={6}
      pitch={2.54}
      holeDiameter={1.0}
      outerDiameter={1.75}
      nets={["net.GND", "net.FAN12", "net.FAN_TACH", "net.FAN_PWM"]}
    />
    <HoleConn
      name="J3_DIAL"
      pcbX={-20.6}
      pcbY={-8}
      pitch={2.5}
      holeDiameter={1.0}
      outerDiameter={1.7}
      nets={["net.V3", "net.DIAL_WIPER", "net.GND"]}
    />
    <HoleConn
      name="J4_OLED"
      pcbX={16}
      pcbY={38}
      pitch={2.5}
      holeDiameter={1.0}
      outerDiameter={1.7}
      horizontal
      nets={["net.GND", "net.V3", "net.OLED_SCL", "net.OLED_SDA"]}
    />
    <HoleConn
      name="J5_BTN"
      pcbX={-20.6}
      pcbY={-2}
      pitch={2.5}
      holeDiameter={1.0}
      outerDiameter={1.7}
      nets={["", "net.GND"]}
    />
    <HoleConn
      name="J6_CHG"
      pcbX={-20.6}
      pcbY={-20}
      pitch={2.5}
      holeDiameter={1.0}
      outerDiameter={1.7}
      nets={["net.CHG_RAW", "net.GND"]}
    />
    <HoleConn
      name="J7_BENCH"
      pcbX={-20.6}
      pcbY={-30}
      pitch={2.5}
      holeDiameter={1.0}
      outerDiameter={1.7}
      nets={["net.BENCH12", "net.GND"]}
    />

    {/* Test points */}
    <TestPoint name="TP_VIN" pcbX={10} pcbY={-36} net="net.VIN" />
    <TestPoint name="TP_12V" pcbX={6} pcbY={10} net="net.FAN12" />
    <TestPoint name="TP_5V" pcbX={11} pcbY={-24} net="net.V5" />
    <TestPoint name="TP_3V3" pcbX={11} pcbY={24} net="net.V3" />
    <TestPoint name="TP_GND" pcbX={-21.3} pcbY={30} net="net.GND" />

    {/* Mounting holes (M2): existing bosses, relocated rear pair, new front pair */}
    <hole diameter={2.4} pcbX={-15.5} pcbY={18.5} />
    <hole diameter={2.4} pcbX={5.5} pcbY={18.5} />
    <hole diameter={2.4} pcbX={-18.5} pcbY={43} />
    <hole diameter={2.4} pcbX={8.5} pcbY={43} />
    <hole diameter={2.4} pcbX={-18.5} pcbY={-39} />
    <hole diameter={2.4} pcbX={12.5} pcbY={-39} />

    {/* Ground pours, both layers */}
    <copperpour layer="bottom" connectsTo="net.GND" />
    <copperpour layer="top" connectsTo="net.GND" />

    {/* Guided power routes (autorouter finalises) */}
    <trace maxLength={120}
      name="vin_feed_a"
      from=".J1_VIN > .P1"
      to=".CIN1_A > .pin2"
      thickness={1.0}
      pcbRouteHints={[{x: 6, y: -41}, {x: -6, y: -41}, {x: -6, y: -8}]}
    />
    <trace maxLength={120}
      name="vin_feed_b"
      from=".J1_VIN > .P1"
      to=".CIN1_B > .pin2"
      thickness={1.0}
      pcbRouteHints={[{x: 8, y: -42}, {x: -6, y: -42}, {x: -6, y: -29}]}
    />
    {/* VIN feeds into each buck chip: due-west at the VIN pad's own height */}
    <trace maxLength={120}
      name="vin_chip_a"
      from=".CIN1_A > .pin2"
      to=".U_A > .VIN"
      thickness={0.6}
      pcbRouteHints={[{x: -1.5, y: -2.9}, {x: -4.1, y: -2.9}, {x: -4.1, y: -5.2}]}
    />
    <trace maxLength={120}
      name="vin_chip_b"
      from=".CIN1_B > .pin2"
      to=".U_B > .VIN"
      thickness={0.6}
      pcbRouteHints={[{x: -1.5, y: -24.9}, {x: -4.1, y: -24.9}, {x: -4.1, y: -27.2}]}
    />
    {/* local VIN hops: enable dividers + HF caps tap their buck's input cap */}
    <trace maxLength={120}
      name="vin_hop_a1"
      from=".CIN1_A > .pin2"
      to=".CIN2_A > .pin1"
      thickness={0.4}
      pcbRouteHints={[{x: -1.2, y: -3.2}]}
    />
    <trace maxLength={120}
      name="vin_hop_a2"
      from=".REN1_A > .pin1"
      to=".CIN2_A > .pin1"
      thickness={0.4}
      pcbRouteHints={[
        {x: -10.5, y: -12.5},
        {x: -9, y: -13, via: true, to_layer: "bottom"},
        {x: -4, y: -6},
        {x: -3, y: -2.5, via: true, to_layer: "top"},
      ]}
    />
    <trace maxLength={120}
      name="vin_hop_b1"
      from=".U_B > .VIN"
      to=".REN1_B > .pin1"
      thickness={0.4}
      pcbRouteHints={[{x: -6.8, y: -29.3}, {x: -8.6, y: -31.5}]}
    />
    <trace maxLength={120}
      name="vin_hop_b2"
      from=".REN1_B > .pin1"
      to=".CIN2_B > .pin1"
      thickness={0.4}
    />
    {/* the one long VIN run: up the west lane to the battery divider */}
    <trace maxLength={120}
      name="vin_divider"
      from=".REN1_A > .pin1"
      to=".R_DIV1 > .pin1"
      thickness={0.5}
      pcbRouteHints={[{x: -19, y: -2}, {x: -19, y: 8}, {x: -15, y: 12}]}
    />
    <trace maxLength={120}
      name="scr_btn"
      from=".U1 > .GP11"
      to=".J5_BTN > .P1"
      thickness={0.35}
      pcbRouteHints={[{x: -4.5, y: 10}, {x: -4.5, y: -1}, {x: -14, y: -1}]}
    />
    <trace maxLength={120}
      name="v5_zero"
      from=".D_5V > .K"
      to=".U1 > .5V"
      thickness={0.6}
      pcbRouteHints={[
        {x: -16.9, y: 43.4},
        {x: -16.9, y: 20},
        {x: -16.9, y: 1.5},
        {x: 0, y: 1.5},
        {x: 9.8, y: 0},
        {x: 9.8, y: -13},
        {x: 8.2, y: -15.2},
      ]}
    />

    <silkscreentext text="TABLE FAN CARRIER+PSU v1" pcbX={0} pcbY={-44.6} fontSize={1.5} />
    <silkscreentext text="VIN" pcbX={17.5} pcbY={-32.4} fontSize={1.3} />
    <silkscreentext text="FAN" pcbX={-20.4} pcbY={11.6} fontSize={1.3} />
    <silkscreentext text="DIAL" pcbX={-20.2} pcbY={-12.6} fontSize={1.3} />
    <silkscreentext text="OLED" pcbX={16} pcbY={41.6} fontSize={1.3} />
    <silkscreentext text="BTN" pcbX={-20.2} pcbY={0.8} fontSize={1.3} />
    <silkscreentext text="CHG" pcbX={-20.4} pcbY={-15.6} fontSize={1.3} />
    <silkscreentext text="BENCH12" pcbX={-19.4} pcbY={-25.6} fontSize={1.2} />
    <silkscreentext text="12V" pcbX={6} pcbY={12.2} fontSize={1.2} />
    <silkscreentext text="5V" pcbX={11} pcbY={-21.8} fontSize={1.2} />
    <silkscreentext text="3V3" pcbX={11} pcbY={26.2} fontSize={1.2} />
  </board>
)
