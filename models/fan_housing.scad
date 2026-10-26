// Portable 120 mm Noctua fan: head + battery base
// Compatible with NF-F12 industrialPPC-3000 PWM (120x120x25 mm)
// Mounting hole spacing: 105 mm center-to-center
// Units: millimeters
// Author: Grok design for nuniesmith/table-fan, reworked Oct 2026;
//         head and base redesigned 2026-10-18 after the design review;
//         head deepened to the base's rear face 2026-10-20
//
// LAYOUT
//   Head : a square frame round the fan at the front, and behind it a duct
//          back to the base's rear face, closed by a grille printed with the
//          head. The front grille screws on (models/faceplate.scad). The
//          fan's rear corners rest and bolt on four corner columns that run
//          from the fan to the rear grille, outside the blades, so the intake
//          is clear. Behind the front frame the duct is narrower by the
//          bail's arms on each side, so the folded bail finishes flush.
//   Base : under the head, front to back, open at the bottom (a bottom
//          plate closes it). Holds the 4S pack in models/battery_sled.scad
//          (four cells side by side, axes front to back) with the BMS and
//          the charger on the sled's lid, and beside it the carrier + PSU
//          board (electronics/pcb): the Zero and both 12 V / 5 V bucks.
//   +X base wall   : dial pot (speed + hard power), USB-C charge port,
//                    screen button
//   Rear base wall : Zero USB-C (programming port) cutout + collar, OLED pod
//   Duct sides     : bail pivots, toothed so the bail locks every 15 deg
//                    (models/bail.scad)
//
// Coordinates: X across (+X = left when facing the fan), Y up (fan centre at
// Y 0), Z front to back (front face at Z 0).
//
// part = head | base | plate | pod renders that part in its print
// orientation, ready to export:
//   head  : rear face down         base : upside down (top face down)
//   plate : flat, bosses up        pod  : window face down
// None needs supports. part = all shows them assembled; models/assembly.scad
// adds the bail, faceplates, sled and knob.

include <battery_sled.scad>
sled_part = "none";             // only the sled's dimensions are needed here
include <carrier_pcb.scad>      // the board's outline, holes and parts: written by tools/check_pcb.py
use <faceplate.scad>            // its grille pattern is the head's rear grille

/* [Head] */
outer_width = 140;              // head width and height (X, Y)
fan_size = 120;
fan_thickness = 25;
fan_clearance = 0.6;            // per side: ASA shrinks ~0.6%, which takes 0.4 of a 121 mm cavity
fan_z0 = 3;                     // fan's front face: room for the fan-bolt heads under the faceplate
fan_section = 36;               // the full-width frame round the fan; the duct runs on from here
head_depth = 100;               // to the base's rear face: the fan draws through the whole duct
duct_wall = 2.4;
rear_grille_t = 2.8;            // the faceplate's grille, printed on the bed as the head's first layers
mount_spacing = 105;            // standard 120 mm fan hole spacing
// The fan's M3 x 30 bolts screw into M3 heat-set inserts in the columns' front
// faces. Nuts would sit behind the columns, where the rear grille closes the
// duct and no hand can reach.
column_inner = 47;              // corner columns cover |X|, |Y| from here out to the walls
corner_r = 4;

/* [Faceplate] */
// The front grille (faceplate.scad, print one), on M2 screws into M2
// heat-set inserts at the cardinal points. The rear grille is the same
// pattern, part of the head. (The old hex nut pockets opened on the face
// itself, so a screw pulled its nut out toward the faceplate instead of
// clamping.) MUST match faceplate.scad.
faceplate_screw_offset = 66;
m2_insert_d = 3.2;              // M2 heat-set insert pilot: check your kit
m2_insert_depth = 5;

/* [Bail pivots] */
// The bail's arms pivot on M4 thumb screws into heat-set inserts in the top
// corner columns. Each side of the duct is recessed by an arm and its teeth,
// so folded, the arms finish flush with the front frame and the base. Teeth
// round each pivot, on the recess floor and on the arm, mesh every 15 deg,
// and the thumb screw clamps them, so the angle can't slip in a truck.
pivot_y = 56;                   // high, for hook room over the head
pivot_z = 48;                   // the arm's round end clears the front frame's 45 deg step
side_recess = 7;                // MUST equal bail_arm_t + tooth_h + tooth_gap, for flush arms
bail_arm_t = 6;                 // X (bail.scad)
tooth_n = 24;                   // 15 deg steps
tooth_h = 0.8;
tooth_r = [5.5, 9.5];           // the toothed ring's inner and outer radius
tooth_gap = 0.2;                // between meshed flanks
m4_insert_d = 5.6;              // M4 heat-set insert pilot: check your kit
m4_insert_depth = 8.5;

/* [Base] */
base_depth = 100;               // front to back; the head stands on its front
base_wall = 2.5;
base_top_t = 2.5;
base_inner_h = 31;              // plate to roof: sled + lid + BMS
plate_t = 3;
boss_s = 8;                     // corner bosses for the bottom-plate screws
m3_insert_d = 4.2;              // M3 heat-set insert pilot: check your kit
m3_insert_depth = 6;
// Head-to-base screws: M3 x 14 countersunk, from the fan cavity floor down
// into inserts in the base. (X, Z); each lands on a boss under the roof.
// Seated (heads 5.5-6.7 mm across), their tips land 4.2-4.9 mm into the
// pilots, 1.1-1.8 mm off the bottom; an M3 x 16 bottoms out before it seats.
join_screw_l = 14;
join_pts = [[-50, 6], [50, 6], [-10, 30], [38, 30]];
join_boss = 8;
join_boss_h = 8;
// ... and two at the back, M3 x 8 pan head from inside the base, up through
// the roof into inserts in the head's bottom corner columns: the duct covers
// the base's whole top, and the bail hangs everything from the head.
rear_join_pts = [[-54, 86], [54, 86]];
// Fan cable: slot through the head's floor and the base's roof (X0, X1, Z0, Z1)
cable_slot = [14, 26, 4, 30];
// ... and a groove across the cavity floor, under the fan's open sides, so
// the cable can run from whichever bottom corner it leaves the fan to the
// slot. (The fan sits 0.6 mm from the walls: there is no room beside it.)
cable_groove = [10, 25];        // Z0, Z1: between the front screws' countersinks and the rear ones
cable_groove_depth = 5;         // full depth from Z0 + depth; the front edge is chamfered 45 deg,
                                // because the head prints rear face down and that edge is its ceiling

/* [Battery] */
sled_x0 = -outer_width/2 + base_wall + 0.5;    // -67: against the -X wall
sled_z0 = 11;

/* [Dial, USB-C, button on the +X base wall] */
// WH138 B10K with switch: 24 mm body, ~18 mm deep + terminals.
pot_y = -88;
pot_z = 24;
pot_hole_d = 7.5;               // M7 bushing + clearance
pot_body_d = 24;
pot_body_depth = 22;            // body + switch + terminals, from the boss below
pot_boss_d = 20;                // thickens the wall round the bushing: the nut clamps 3 mm, not 1.5
pot_boss_t = 1.5;
knob_recess_d = 24;             // cut from the outer face
knob_recess_depth = 1;
usb_y = -88;
usb_z = 46;
usb_open = [13, 10];            // Z, Y: verify against the socket before printing
btn_y = -88;
btn_z = 66;
// 6x6 tactile switch, 8-9.5 mm tall, pushed in from outside into a pocket
// with a floor: a press bears on the floor, not on glue. Its legs pass
// through two slots to the inside.
btn_pocket = 6.3;
btn_pocket_depth = 3.6;         // the switch body's height
btn_floor = 2.4;
btn_leg_pitch = 4.5;            // between the two rows of legs

// Vent slots in the base's top, behind the front frame, over the carrier
// board and the charger. They carry on through the duct's floor, so the fan
// draws air up past them. (X0, X1, Z0, Z1; slots run along Z)
vents = [[20, 42, 42, 62], [-12, 4, 48, 68]];
vent_w = 2;
vent_pitch = 5;

/* [Carrier + PSU board (on the bottom plate)] */
// The board is electronics/pcb/carrier-psu.tsx. Its outline, M2 holes and
// parts are in carrier_pcb.scad, generated from its build, so the plate's
// bosses always sit under the board's holes.
carrier_boss_h = 5;             // the plate's bosses: the board's underside
carrier_boss_d = 5;
zero_usb_x = 37.5;              // the Zero's USB-C, and the rear wall's cutout for it
zero_usb_open = [13.2, 8];      // X, Y: a plug's overmould (up to 12.35 x 6.5) plus print shrinkage
plate_vents = [21, 41, 33, 62]; // X of the first and last slot (5 apart), Z0, Z1: under the board

/* [OLED pod] */
// 0.96" SSD1306 module, from its listing: 27.3 x 27.8 mm PCB, 21.74 x 10.86 mm
// active area, header GND VCC SCL SDA, rated -20..60 C. The listing doesn't give
// the M2 holes; these boards put them 2 mm in from each edge, 23.3 x 23.8 apart.
// Measure yours before printing: only this small part changes if they differ.
oled_pcb = [27.3, 27.8];
oled_hole_dx = 23.3;
oled_hole_dy = 23.8;
oled_glass_t = 1.8;             // PCB front face to glass face
oled_post_d = 3.6;
oled_win = [24, 13];            // the 21.74 x 10.86 active area plus a margin
oled_win_dy = 0;                // move the window up (+) or down (-) to match the glass
pod_wall = 2;
pod_depth = 12;
pod_x = -27;
pod_y = -87;
pod_screw_dx = 24;              // the pod's two M2 screws, either side of pod_x

/* [Render] */
part = "all";  // [all, head, base, plate, pod]

$fn = 64;

// ---------- Derived ----------
cavity = fan_size + 2*fan_clearance;            // 120.8
ci = cavity/2;                                  // 60.4
head_y0 = -outer_width/2;                       // -70: head bottom = base top
base_roof = head_y0 - base_top_t;               // -72.5
base_floor = base_roof - base_inner_h;          // -103.5: plate top
base_bottom = base_floor - plate_t;             // -106.5
duct_x = outer_width/2 - side_recess;           // 63: the duct's side faces, where the bail's teeth are
duct_in_x = duct_x - duct_wall;                 // 60.6
duct_in_y = outer_width/2 - duct_wall;          // 67.6
in_x = outer_width/2 - base_wall;               // 67.5
in_z0 = base_wall;
in_z1 = base_depth - base_wall;
zero_usb_y = base_floor + carrier_boss_h + carrier_pcb_t + 1.0 + 1.6;   // boss + board + Zero + half the receptacle
pod_w = oled_pcb[0] + 2 + 2*pod_wall;
pod_h = oled_pcb[1] + 2 + 2*pod_wall;
lid_top = base_floor + sled_h + lid_t;

function corner_boss_xz(sx, fz) =
    [sx*(in_x - boss_s/2), fz == 0 ? in_z0 + boss_s/2 : in_z1 - boss_s/2];

// ---------- Helpers ----------
// box centred on the Z axis, w (X) x h (Y), from z0 to z1, edges along Z rounded
module rounded_box_z(w, h, z0, z1, r) {
    hull() for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*(w/2 - r), sy*(h/2 - r), z0]) cylinder(r=r, h=z1 - z0);
}

// box centred on X, w (X) x d (Z from 0), from y0 to y1, edges along Y rounded
module rounded_box_y(w, d, y0, y1, r) {
    hull() for (sx = [-1, 1], z = [r, d - r])
        translate([sx*(w/2 - r), y0, z]) rotate([-90, 0, 0]) cylinder(r=r, h=y1 - y0);
}

module y_cyl(d, y0, h, d2 = -1) {        // cylinder along +Y from y0
    translate([0, y0, 0]) rotate([-90, 0, 0])
        cylinder(d1=d, d2=(d2 < 0 ? d : d2), h=h);
}

module both_sides() { children(); mirror([1, 0, 0]) children(); }

// A ring of n radial teeth, h tall, standing on the plane z = 0; tooth k is
// centred at phase + k*360/n deg. Each tooth's roots run along radii, so two
// rings mesh face to face half a tooth apart, with the flanks matching at
// every radius.
module serration(n, r0, r1, h, phase = 0) {
    for (k = [0 : n - 1]) rotate([0, 0, phase + k*360/n])
        hull() for (r = [r0, r1])
            translate([r*cos(180/n), 0, 0]) rotate([90, 0, 90]) linear_extrude(0.01)
                polygon([[-r*sin(180/n), 0], [r*sin(180/n), 0], [0, h]]);
}

// ---------- Head ----------
module cardinal_pilots(z_face, into) {   // into = +1: drilled toward +Z
    for (a = [0, 90, 180, 270]) rotate([0, 0, a])
        translate([faceplate_screw_offset, 0, into > 0 ? z_face - 0.1 : z_face - m2_insert_depth])
            cylinder(d=m2_insert_d, h=m2_insert_depth + 0.1);
}

// Corner columns, from the fan's rear face to the rear grille, outside the
// blades. The fan's corners rest on their front faces and bolt into inserts
// there, and the top two carry the bail's pivots. They print straight up
// from the bed (the head prints rear face down): ledges stopping behind the
// fan would be 64 mm in the air.
// The bottom two reach down to the base, which closes the duct: they take the
// rear head-to-base screws.
module columns() {
    z0 = fan_z0 + fan_thickness;
    for (sx = [-1, 1], sy = [-1, 1]) {
        y0 = sy > 0 ? column_inner : head_y0;
        y1 = sy > 0 ? ci + 0.7 : -column_inner;
        translate([sx > 0 ? column_inner : -duct_in_x - 0.5, y0, z0])
            cube([duct_in_x + 0.5 - column_inner, y1 - y0, head_depth - rear_grille_t + 0.1 - z0]);
    }
}

// The duct's outside: its top edges rounded like the frame's, its bottom ones
// square, so its sides stand flat on the base.
module duct_outer(z0, z1) {
    hull() {
        for (sx = [-1, 1]) translate([sx*(duct_x - corner_r), outer_width/2 - corner_r, z0]) cylinder(r=corner_r, h=z1 - z0);
        translate([-duct_x, head_y0, z0]) cube([2*duct_x, 1, z1 - z0]);
    }
}

// The faceplate's rings and spokes over the fan's disc, and solid round it.
module rear_grille() {
    translate([0, 0, head_depth - rear_grille_t]) intersection() {
        translate([-duct_in_x - 0.5, head_y0, 0]) cube([2*duct_in_x + 1, duct_in_y + 0.5 - head_y0, rear_grille_t]);
        union() {
            intersection() { faceplate(); cylinder(d=fan_size - 4, h=rear_grille_t); }
            difference() {
                translate([-outer_width/2, -outer_width/2, 0]) cube([outer_width, outer_width, rear_grille_t]);
                translate([0, 0, -1]) cylinder(d=fan_size - 4, h=rear_grille_t + 2);
            }
        }
    }
}

module side_teeth() {           // round each pivot, on the recess floor
    both_sides() translate([duct_x - 0.01, pivot_y, pivot_z]) rotate([0, 90, 0])
        serration(tooth_n, tooth_r[0], tooth_r[1], tooth_h + 0.01);
}

module head() {
    // where the duct's inside reaches full size: the bottom, open onto the
    // base, at 45 deg from the frame's floor; the top a little steeper
    duct_z0 = fan_section - head_y0 + 1 - ci;   // 46.6
    difference() {
        union() {
            // the frame round the fan, its sides stepping in 45 deg at the back
            // to the duct's: square, that step would print as a 7 mm ledge
            difference() {
                hull() {
                    rounded_box_z(outer_width, outer_width, 0, fan_section - side_recess, corner_r);
                    rounded_box_z(2*duct_x, outer_width, 0, fan_section, corner_r);
                }
                translate([-ci, -ci, -1]) cube([cavity, cavity, fan_section + 2]);
            }
            // the duct: sides and a top, standing on the base, whose roof is its
            // floor. Its inside widens from the fan's cavity at 45 deg or less, so
            // the frame's floor and top print without a 90 mm bridge.
            difference() {
                duct_outer(fan_section - 0.5, head_depth);
                translate([-ci, -ci, fan_section - 1]) cube([cavity, cavity, 1.01]);
                hull() {        // from the frame's rear face exactly, or the slope starts outside its wall
                    translate([-ci, -ci, fan_section]) cube([cavity, cavity, 0.01]);
                    translate([-duct_in_x, head_y0 - 1, duct_z0]) cube([2*duct_in_x, duct_in_y - head_y0 + 1, head_depth - duct_z0 + 1]);
                }
            }
            columns();
            rear_grille();
            side_teeth();
        }
        cardinal_pilots(0, 1);
        // the fan's bolts: M3 inserts in the columns' front faces
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx*mount_spacing/2, sy*mount_spacing/2, fan_z0 + fan_thickness - 0.1])
                cylinder(d=m3_insert_d, h=m3_insert_depth + 0.1);
        // bail pivot inserts, from the recess floor into the top columns
        for (sx = [-1, 1])
            translate([sx*(duct_x + tooth_h + 0.1), pivot_y, pivot_z])
                rotate([0, -sx*90, 0]) cylinder(d=m4_insert_d, h=tooth_h + m4_insert_depth + 0.1);
        // head-to-base screws, countersunk into the cavity floor
        for (p = join_pts) translate([p[0], 0, p[1]]) {
            y_cyl(3.4, head_y0 - 1, outer_width/2 - ci + 2);
            y_cyl(3.4, -ci - 1.7, 1.8, 6.6);
        }
        // ... and the two at the back: inserts in the bottom columns, from below
        for (p = rear_join_pts)
            translate([p[0], 0, p[1]]) y_cyl(m3_insert_d, head_y0 - 0.1, m3_insert_depth + 0.1);
        // fan cable down into the base, and the groove that leads it there
        translate([cable_slot[0], head_y0 - 1, cable_slot[2]])
            cube([cable_slot[1] - cable_slot[0], outer_width/2 - ci + 2, cable_slot[3] - cable_slot[2]]);
        translate([-ci - 0.1, 0, 0]) rotate([90, 0, 90]) linear_extrude(cavity + 0.2)
            polygon([[-ci + 0.1, cable_groove[0] - 0.1], [-ci - cable_groove_depth, cable_groove[0] + cable_groove_depth],
                     [-ci - cable_groove_depth, cable_groove[1]], [-ci + 0.1, cable_groove[1]]]);   // (Y, Z)
        // the base's vents open into the duct; carry them through the 45 deg
        // widening where it covers the front of them
        for (v = vents) for (x = [v[0] : vent_pitch : v[1]])
            translate([x - vent_w/2, head_y0 - 1, v[2]]) cube([vent_w, 13, v[3] - v[2]]);
    }
}

// ---------- Base ----------
module corner_boss(sx, fz) {
    x0 = sx > 0 ? in_x - boss_s : -in_x - 0.5;
    z0 = fz == 0 ? in_z0 - 0.5 : in_z1 - boss_s;
    translate([x0, base_floor, z0])
        cube([boss_s + 0.5, base_roof - base_floor + 0.5, boss_s + 0.5]);
}

module pod_column(x) {
    translate([x - 3, pod_y - 6, in_z1 - 6])
        cube([6, base_roof - (pod_y - 6) + 0.5, 6.5]);
}

// Strain-relief collar round the Zero's USB-C plug. Its upper wall is left
// off and the side walls' tops slope 45 deg, so it prints upside down
// without support.
module zero_collar() {
    w = zero_usb_open[0]; h = zero_usb_open[1]; t = 2.75; l = 6;
    translate([zero_usb_x, zero_usb_y, base_depth]) {
        translate([-w/2 - t, -h/2 - t, -0.5]) cube([w + 2*t, t, l + 0.5]);   // floor
        for (sx = [-1, 1])
            translate([sx > 0 ? w/2 : -w/2 - t, 0, 0])
                rotate([90, 0, 90]) linear_extrude(t)
                    polygon([[-h/2 - t, -0.5], [-h/2 - t, l], [h/2 + t - l, l], [h/2 + t + 0.5, -0.5]]);   // (Y, Z)
    }
}

module base() {
    difference() {
        union() {
            difference() {
                rounded_box_y(outer_width, base_depth, base_floor, head_y0, corner_r);
                translate([-in_x, base_floor - 1, in_z0])
                    cube([2*in_x, base_roof - base_floor + 1, in_z1 - in_z0]);
            }
            for (sx = [-1, 1], fz = [0, 1]) corner_boss(sx, fz);
            for (p = join_pts)
                translate([p[0] - join_boss/2, base_roof - join_boss_h, p[1] - join_boss/2])
                    cube([join_boss, join_boss_h + 0.5, join_boss]);
            for (s = [-1, 1]) pod_column(pod_x + s*pod_screw_dx);
            // ring round the pot bushing on the wall's inside, its edge chamfered
            // 45 deg: the base prints upside down, so a square edge starts as a ledge
            translate([in_x - pot_boss_t, pot_y, pot_z]) rotate([0, 90, 0])
                cylinder(d1=pot_boss_d - 2*pot_boss_t, d2=pot_boss_d, h=pot_boss_t + 0.01);
            translate([in_x - 0.01, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=pot_boss_d, h=0.5);
            // column that gives the button pocket its floor (hangs from the roof, so it prints)
            translate([outer_width/2 - btn_pocket_depth - btn_floor, btn_y - 6, btn_z - 6])
                cube([btn_pocket_depth + btn_floor - base_wall + 0.5, base_roof - btn_y + 6.5, 12]);
        }
        // bottom-plate screw inserts (from below)
        for (sx = [-1, 1], fz = [0, 1]) {
            p = corner_boss_xz(sx, fz);
            translate([p[0], 0, p[1]]) y_cyl(m3_insert_d, base_floor - 0.1, m3_insert_depth + 0.1);
        }
        // head-to-base inserts (from the top surface)
        for (p = join_pts)
            translate([p[0], 0, p[1]]) y_cyl(m3_insert_d, head_y0 - m3_insert_depth, m3_insert_depth + 0.1);
        // the head's two rear screws come up through the roof from inside
        for (p = rear_join_pts)
            translate([p[0], 0, p[1]]) y_cyl(3.4, base_roof - 1, base_top_t + 2);
        // fan cable slot
        translate([cable_slot[0], base_roof - 1, cable_slot[2]])
            cube([cable_slot[1] - cable_slot[0], base_top_t + 2, cable_slot[3] - cable_slot[2]]);
        // +X wall: dial pot hole + knob recess (from the outer face)
        translate([in_x - pot_boss_t - 1, pot_y, pot_z]) rotate([0, 90, 0])
            cylinder(d=pot_hole_d, h=pot_boss_t + base_wall + 2);
        translate([outer_width/2 - knob_recess_depth, pot_y, pot_z])
            rotate([0, 90, 0]) cylinder(d1=knob_recess_d - 2*knob_recess_depth, d2=knob_recess_d, h=knob_recess_depth + 0.01);
        translate([outer_width/2, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=knob_recess_d, h=1);
        // +X wall: USB-C charge port, through to the bay
        translate([in_x - 1, usb_y - usb_open[1]/2, usb_z - usb_open[0]/2])
            cube([base_wall + 2, usb_open[1], usb_open[0]]);
        // +X wall: screen button pocket from outside, and slots for its legs
        translate([outer_width/2 - btn_pocket_depth, btn_y - btn_pocket/2, btn_z - btn_pocket/2])
            cube([btn_pocket_depth + 1, btn_pocket, btn_pocket]);
        for (s = [-1, 1])
            translate([outer_width/2 - btn_pocket_depth - btn_floor - 0.1, btn_y - 4, btn_z + s*btn_leg_pitch/2 - 0.6])
                cube([btn_floor + 0.2, 8, 1.2]);
        // vents in the top, behind the head
        for (v = vents) for (x = [v[0] : vent_pitch : v[1]])
            translate([x - vent_w/2, base_roof - 1, v[2]]) cube([vent_w, base_top_t + 2, v[3] - v[2]]);
        // rear wall: Zero USB-C
        translate([zero_usb_x - zero_usb_open[0]/2, zero_usb_y - zero_usb_open[1]/2, in_z1 - 1])
            cube([zero_usb_open[0], zero_usb_open[1], base_wall + 8]);
        // rear wall: OLED pod opening (wires) + its two screws. Its lower edge
        // comes to a 45 deg point: the base prints upside down, and a flat
        // edge would be a 22 mm bridge in a 2.5 mm wall (the slicer flagged it).
        translate([0, 0, in_z1 - 1]) linear_extrude(base_wall + 2)
            polygon([[pod_x - 7, pod_y + 6], [pod_x + 7, pod_y + 6], [pod_x + 7, pod_y - 2],
                     [pod_x, pod_y - 9], [pod_x - 7, pod_y - 2]]);
        for (s = [-1, 1])
            translate([pod_x + s*pod_screw_dx, pod_y, in_z1 - 6])
                cylinder(d=1.7, h=base_wall + 6.1);
    }
    zero_collar();
}

// ---------- Bottom plate ----------
// Zip-tie bridges: wiring tied down near the joints survives a truck.
// (X, Z, 1 = the tie runs along Z.) The carrier board covers the plate from
// X 18 to 58.5; its wires plug into latching connectors on it.
tie_pts = [[6, 93, 1]];

module tie_bridge(x, z, along_z) {
    translate([x, 0, z]) rotate([0, along_z ? 90 : 0, 0])
        difference() {
            translate([-4, base_floor - 0.5, -3]) cube([8, 5.5, 6]);
            // tunnel for a 2.5-3 mm tie, its roof peaked at 45 deg so it needs no bridge
            translate([-5, 0, 0]) rotate([90, 0, 90]) linear_extrude(10)
                polygon([[base_floor + 0.6, -1.75], [base_floor + 0.6, 1.75], [base_floor + 2.0, 1.75],
                         [base_floor + 3.75, 0], [base_floor + 2.0, -1.75]]);   // (Y, Z)
        }
}

module bottom_plate() {
    sled_screw_z = [sled_z0 + end_t/2, sled_z0 + sled_l - end_t/2];
    difference() {
        union() {
            rounded_box_y(outer_width, base_depth, base_bottom, base_floor, corner_r);
            // the carrier board's bosses
            for (h = carrier_pcb_holes)
                translate([h[0], 0, h[1]]) y_cyl(carrier_boss_d, base_floor - 0.5, carrier_boss_h + 0.5);
            for (t = tie_pts) tie_bridge(t[0], t[1], t[2]);
        }
        // M3 countersunk screws into the base's corner bosses
        for (sx = [-1, 1], fz = [0, 1]) {
            p = corner_boss_xz(sx, fz);
            translate([p[0], 0, p[1]]) {
                y_cyl(3.4, base_bottom - 1, plate_t + 2);
                y_cyl(6.6, base_bottom - 0.1, 1.7, 3.2);
            }
        }
        // M2 countersunk screws up into the sled's end walls
        for (z = sled_screw_z)
            translate([sled_x0 + plate_screw_x, 0, z]) {
                y_cyl(2.4, base_bottom - 1, plate_t + 2);
                y_cyl(4.6, base_bottom - 0.1, 1.2, 2.2);
            }
        // board boss pilots (M2 self-tapping)
        for (h = carrier_pcb_holes)
            translate([h[0], 0, h[1]]) y_cyl(1.7, base_floor - 1.5, carrier_boss_h + 2);
        // vent slots under the board's 12 V buck
        for (x = [plate_vents[0] : 5 : plate_vents[1]])
            translate([x - 1, base_bottom - 1, plate_vents[2]]) cube([2, plate_t + 2, plate_vents[3] - plate_vents[2]]);
        // recesses for stick-on feet
        for (sx = [-1, 1], z = [16, 84])
            translate([sx*55, 0, z]) y_cyl(12, base_bottom - 0.1, 1.1);
    }
}

// ---------- OLED pod (screws onto the base's rear wall) ----------
// The module drops in glass first and screws to the posts from behind; the
// pod then screws to the rear wall over the wire opening.
module oled_pod() {
    z0 = base_depth;
    z1 = base_depth + pod_depth;
    difference() {
        union() {
            translate([pod_x - pod_w/2, pod_y - pod_h/2, z0]) cube([pod_w, pod_h, pod_depth]);
            // screw ears, full depth so they print from the bed
            translate([pod_x - pod_screw_dx - 4, pod_y - 4, z0]) cube([2*pod_screw_dx + 8, 8, pod_depth]);
        }
        translate([pod_x - pod_w/2 + pod_wall, pod_y - pod_h/2 + pod_wall, z0 - 1])
            cube([pod_w - 2*pod_wall, pod_h - 2*pod_wall, pod_depth - pod_wall + 1]);
        translate([pod_x - oled_win[0]/2, pod_y + oled_win_dy - oled_win[1]/2, z1 - pod_wall - 1])
            cube([oled_win[0], oled_win[1], pod_wall + 2]);
        // M2 x 10 through each ear into the base: clearance, counterbored from the window side
        for (s = [-1, 1]) translate([pod_x + s*pod_screw_dx, pod_y, 0]) {
            translate([0, 0, z0 - 1]) cylinder(d=2.4, h=pod_depth + 2);
            translate([0, 0, z0 + 2.5]) cylinder(d=4.5, h=pod_depth);
        }
    }
    // posts the PCB screws to; their height sets the glass against the window
    for (sx = [-1, 1], sy = [-1, 1])
        translate([pod_x + sx*oled_hole_dx/2, pod_y + sy*oled_hole_dy/2, z1 - pod_wall - oled_glass_t])
            difference() {
                cylinder(d=oled_post_d, h=oled_glass_t + 0.5);
                translate([0, 0, -0.1]) cylinder(d=1.6, h=oled_glass_t + pod_wall - 0.6);
            }
}

// ---------- Layout keep-outs ----------
// Where the bought parts go, for models/assembly.scad and the checks in
// models/checks.scad. Board sizes are typical listings: measure yours.
bms_size = [46, 8, 60];         // X, Y (incl. balance header), Z; on the sled lid
charger_size = [25, 8, 35];     // 4S Type-C boost charger
bms_pos = [sled_x0 + 3, sled_z0 + 8];          // X0, Z0 on the lid
charger_pos = [sled_x0 + 55, sled_z0 + 29];    // on the lid beside the BMS, under the roof's vents

module fan_keepout() {
    translate([-fan_size/2, -fan_size/2, fan_z0]) cube([fan_size, fan_size, fan_thickness]);
}
module cells_keepout() { translate([sled_x0, base_floor, sled_z0]) cells(); }
module sled_placed() { translate([sled_x0, base_floor, sled_z0]) { sled(); sled_lid(); } }
module bms_keepout() { translate([bms_pos[0], lid_top, bms_pos[1]]) cube(bms_size); }
module charger_keepout() { translate([charger_pos[0], lid_top, charger_pos[1]]) cube(charger_size); }
// the carrier board on its bosses, and every part on it to its height
// (mated plugs and wire bends included); the Zero's USB-C sticks out 0.5 at the back
module carrier_pcb_board() {
    translate([0, base_floor + carrier_boss_h + carrier_pcb_t, 0]) rotate([90, 0, 0])
        linear_extrude(carrier_pcb_t) polygon(carrier_pcb_outline);
}
module carrier_pcb_parts() {
    for (q = carrier_pcb_parts)
        translate([q[0], base_floor + carrier_boss_h + carrier_pcb_t, q[1]])
            cube([q[2] - q[0], q[4], q[3] - q[1] + (q[5] == "U1" ? 0.5 : 0)]);
}
module carrier_pcb_keepout() { carrier_pcb_board(); carrier_pcb_parts(); }
module pot_keepout() {          // body + switch + terminals, and the bushing through the wall
    translate([in_x - pot_boss_t - pot_body_depth, pot_y, pot_z]) rotate([0, 90, 0])
        cylinder(d=pot_body_d + 2, h=pot_body_depth);
    translate([in_x - pot_boss_t - 0.1, pot_y, pot_z]) rotate([0, 90, 0])
        cylinder(d=7, h=pot_boss_t + base_wall + 1.2);
}
module usb_socket_keepout() {
    translate([in_x - 15, usb_y - 7, usb_z - 7]) cube([15, 14, 14]);
}
module button_keepout() {       // its legs, solder and wires inside the floor
    translate([outer_width/2 - btn_pocket_depth - btn_floor - 5, btn_y - 5, btn_z - 4]) cube([5, 10, 8]);
}
module button_body_keepout() {  // the 6x6 switch body, seated in its pocket
    translate([outer_width/2 - btn_pocket_depth, btn_y - 3, btn_z - 3]) cube([btn_pocket_depth, 6, 6]);
}
// What has to pass through each opening, at fixed sizes: the charge socket's
// body (12 x 9), the 6x6 button, the Zero's USB-C plug (12 x 7 overmould),
// and the fan's 4-pin plug (10 x 7) down through the cable slot.
module openings_keepout() {
    translate([in_x - 1, usb_y - 4.5, usb_z - 6]) cube([base_wall + 6, 9, 12]);
    translate([outer_width/2 - btn_pocket_depth + 0.1, btn_y - 3, btn_z - 3]) cube([btn_pocket_depth + 5, 6, 6]);
    // the fan cable (4 x 6 mm, kept 0.5 below the floor so the fan can't pinch
    // it) along the floor groove, corner to corner
    translate([-ci + 1, -ci - 4.5, (cable_groove[0] + cable_groove_depth + cable_groove[1])/2 - 3])
        cube([2*ci - 2, 4, 6]);
    // each vent slot is open
    for (v = vents) for (x = [v[0] : vent_pitch : v[1]])
        translate([x - vent_w/2 + 0.3, base_roof - 0.5, v[2] + 0.5]) cube([vent_w - 0.6, base_top_t + 1, v[3] - v[2] - 1]);
    translate([zero_usb_x - 6, zero_usb_y - 3.5, in_z1 - 0.5]) cube([12, 7, 18]);
    translate([(cable_slot[0] + cable_slot[1])/2 - 5, base_roof - 3, (cable_slot[2] + cable_slot[3])/2 - 3.5])
        cube([10, -ci - base_roof + 4, 7]);
}
oled_pcb_front = base_depth + pod_depth - pod_wall - oled_glass_t;
module oled_pcb_keepout() {
    translate([pod_x - oled_pcb[0]/2, pod_y - oled_pcb[1]/2, oled_pcb_front - 1.6])
        cube([oled_pcb[0], oled_pcb[1], 1.6]);
}
module oled_keepout() {         // PCB + glass, seated on the posts
    oled_pcb_keepout();
    translate([pod_x - 26.7/2, pod_y - 19.3/2, oled_pcb_front]) cube([26.7, 19.3, oled_glass_t]);
}
module fan_bolts_keepout() {    // M3 x 30 bolts from the fan's front flange into the column inserts
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx*mount_spacing/2, sy*mount_spacing/2, 0]) {
        translate([0, 0, fan_z0 - 2]) cylinder(d=5.5, h=2);                 // pan head
        translate([0, 0, fan_z0]) cylinder(d=3, h=30);
    }
}
// The head-to-base screws' shanks, seated: the countersink is 5.5 across
// where the smallest head stops, the deepest the tip can go.
join_seat_y = -ci - 1.7 + (5.5 - 3.4) * 1.8 / 3.2;
assert(-ci - 1.7 + (6.72 - 3.4) * 1.8 / 3.2 - join_screw_l <= head_y0 - 4,
       "join_screw_l: a large head leaves under 4 mm in the insert");
module join_screws_keepout() {
    for (p = join_pts) translate([p[0], 0, p[1]])
        y_cyl(2.9, join_seat_y - join_screw_l, join_screw_l - 2);
}
module rear_screws_keepout() {  // the head's two rear M3 x 8 pan heads, inside the base, and their shanks
    for (p = rear_join_pts) translate([p[0], 0, p[1]]) {
        y_cyl(6, base_roof - 2.5, 2.5);
        y_cyl(3, base_roof - 0.1, 8.1);
    }
}

// ---------- Render ----------
if (part == "head") {
    translate([0, 0, head_depth]) rotate([180, 0, 0]) head();    // rear face down
} else if (part == "base") {
    translate([0, 0, head_y0]) rotate([-90, 0, 0]) base();
} else if (part == "plate") {
    translate([0, 0, -base_bottom]) rotate([90, 0, 0]) bottom_plate();
} else if (part == "pod") {
    translate([-pod_x, pod_y, base_depth + pod_depth]) rotate([180, 0, 0]) oled_pod();
} else if (part == "all") {
    color("SteelBlue") head();
    color("LightSteelBlue") base();
    color("SlateGray") bottom_plate();
    color("SteelBlue") oled_pod();
    // ghosts: fan, sled with cells and lid
    %translate([-fan_size/2, -fan_size/2, fan_z0]) cube([fan_size, fan_size, fan_thickness]);
    %translate([sled_x0, base_floor, sled_z0]) { sled(); sled_lid(); cells(); }
}
