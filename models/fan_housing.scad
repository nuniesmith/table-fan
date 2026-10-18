// Portable 120 mm Noctua fan: head + battery base
// Compatible with NF-F12 industrialPPC-3000 PWM (120x120x25 mm)
// Mounting hole spacing: 105 mm center-to-center
// Units: millimeters
// Author: Grok design for nuniesmith/table-fan, reworked Oct 2026;
//         head and base redesigned 2026-10-18 after the design review
//
// LAYOUT
//   Head : a square frame round the fan, open front and back. A faceplate
//          grille screws onto each face (models/faceplate.scad, print two).
//          The fan's rear corners rest on four corner ledges and are bolted
//          to them; nothing else sits behind the fan, so its intake is clear.
//   Base : under the head and running back behind it, open at the bottom
//          (a bottom plate closes it). Holds the 4S pack in
//          models/battery_sled.scad (four cells side by side, axes front to
//          back) with the BMS on the sled's lid, plus the charger, both
//          MP1584 bucks and the Zero carrier.
//   +X base wall   : dial pot (speed + hard power), USB-C charge port,
//                    screen button
//   Rear base wall : Zero USB-C (programming port) cutout + collar, OLED pod
//   Head sides     : bail pivots (models/bail.scad)
//
// Coordinates: X across (+X = left when facing the fan), Y up (fan centre at
// Y 0), Z front to back (front face at Z 0).
//
// part = head | base | plate | pod renders that part in its print
// orientation, ready to export:
//   head  : front face down        base : upside down (top face down)
//   plate : flat, bosses up        pod  : window face down
// None needs supports. part = all shows them assembled; models/assembly.scad
// adds the bail, faceplates, sled and knob.

include <battery_sled.scad>
sled_part = "none";             // only the sled's dimensions are needed here

/* [Head] */
outer_width = 140;              // head width and height (X, Y)
fan_size = 120;
fan_thickness = 25;
fan_clearance = 0.4;            // per side
fan_z0 = 3;                     // fan's front face: room for the fan-bolt heads under the faceplate
gusset_t = 5;                   // corner ledges behind the fan
head_depth = 36;                // fan_z0 + fan + ledges + 3 for the bolt tails
mount_spacing = 105;            // standard 120 mm fan hole spacing
mount_hole_d = 3.4;             // M3 clearance (fan bolts)
fan_nut_ac = 6.6;               // M3 nut pocket on each ledge's rear face, across corners
fan_nut_depth = 2.6;
gusset_inner = 47;              // ledges cover |X|, |Y| from here out to the cavity wall
corner_r = 4;

/* [Faceplates] */
// The front and rear grilles are the same part (faceplate.scad, print two).
// M2 screws into M2 heat-set inserts at the cardinal points. (The old hex
// nut pockets opened on the face itself, so a screw pulled its nut out
// toward the faceplate instead of clamping.) MUST match faceplate.scad.
faceplate_screw_offset = 66;
m2_insert_d = 3.2;              // M2 heat-set insert pilot: check your kit
m2_insert_depth = 5;

/* [Bail pivots] */
pivot_y = 10;
pivot_z = 28;
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
// Head-to-base screws: M3 x 16 countersunk, from the fan cavity floor down
// into inserts in the base. (X, Z); each lands on a boss under the roof.
join_pts = [[-50, 6], [50, 6], [-10, 30], [40, 30]];
join_boss = 8;
join_boss_h = 8;
// Fan cable: slot through the head's floor and the base's roof (X0, X1, Z0, Z1)
cable_slot = [14, 26, 4, 30];

/* [Battery] */
sled_x0 = -outer_width/2 + base_wall + 0.5;    // -67: against the -X wall
sled_z0 = 11;

/* [Dial, USB-C, button on the +X base wall] */
// WH138 B10K with switch: 24 mm body, ~18 mm deep + terminals.
pot_y = -88;
pot_z = 24;
pot_hole_d = 7.5;               // M7 bushing + clearance
pot_body_d = 24;
pot_body_depth = 22;            // body + switch + terminals, from the wall's inner face
knob_recess_d = 24;             // cut from the outer face
knob_recess_depth = 1;
usb_y = -88;
usb_z = 46;
usb_open = [13, 10];            // Z, Y: verify against the socket before printing
btn_y = -88;
btn_z = 62;
btn_open = 6.4;                 // 6x6 tactile switch, glued in from outside

/* [Zero carrier (on the bottom plate)] */
carrier_size = [25, 30];        // X, Z perfboard; the Zero's USB-C at its rear edge
carrier_x0 = 25;
carrier_z0 = 66.5;
carrier_boss_h = 5;
carrier_hole_dx = 21;           // M2 holes, drilled through the perfboard
carrier_hole_dz = 26;
zero_usb_open = [12.5, 7.5];    // X, Y: room for the plug's overmould

/* [OLED pod] */
// 0.96" SSD1306 module (~27.5 x 28 mm PCB, M2 holes ~23 x 23 mm apart). Only
// this small part needs reprinting if the real module differs.
oled_pcb = [27.5, 28];
oled_hole_dx = 23;
oled_hole_dy = 23;
oled_glass_t = 1.8;             // PCB front face to glass face
oled_post_d = 3.6;
oled_win = [26, 13];
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
in_x = outer_width/2 - base_wall;               // 67.5
in_z0 = base_wall;
in_z1 = base_depth - base_wall;
zero_usb_x = carrier_x0 + carrier_size[0]/2;
zero_usb_y = base_floor + carrier_boss_h + 1.6 + 1.0 + 1.6;   // boss + perfboard + Zero + half the receptacle
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

// ---------- Head ----------
module cardinal_pilots(z_face, into) {   // into = +1: drilled toward +Z
    for (a = [0, 90, 180, 270]) rotate([0, 0, a])
        translate([faceplate_screw_offset, 0, into > 0 ? z_face - 0.1 : z_face - m2_insert_depth])
            cylinder(d=m2_insert_d, h=m2_insert_depth + 0.1);
}

// Corner ledges the fan's rear face rests on. M3 bolts come in from the front
// through the fan's corner holes; their nuts sit in pockets on the ledges'
// rear faces, so they clamp.
module gussets() {
    z0 = fan_z0 + fan_thickness;
    for (sx = [-1, 1], sy = [-1, 1])
        difference() {
            translate([sx > 0 ? gusset_inner : -ci - 0.5, sy > 0 ? gusset_inner : -ci - 0.5, z0])
                cube([ci + 0.5 - gusset_inner, ci + 0.5 - gusset_inner, gusset_t]);
            translate([sx*mount_spacing/2, sy*mount_spacing/2, z0 - 1])
                cylinder(d=mount_hole_d, h=gusset_t + 2);
            translate([sx*mount_spacing/2, sy*mount_spacing/2, z0 + gusset_t - fan_nut_depth])
                cylinder(d=fan_nut_ac, h=fan_nut_depth + 1, $fn=6);
        }
}

module head() {
    difference() {
        union() {
            difference() {
                rounded_box_z(outer_width, outer_width, 0, head_depth, corner_r);
                translate([-ci, -ci, -1]) cube([cavity, cavity, head_depth + 2]);
            }
            gussets();
        }
        cardinal_pilots(0, 1);
        cardinal_pilots(head_depth, -1);
        // bail pivot inserts
        for (sx = [-1, 1])
            translate([sx*(outer_width/2 + 0.1), pivot_y, pivot_z])
                rotate([0, -sx*90, 0]) cylinder(d=m4_insert_d, h=m4_insert_depth + 0.1);
        // head-to-base screws, countersunk into the cavity floor
        for (p = join_pts) translate([p[0], 0, p[1]]) {
            y_cyl(3.4, head_y0 - 1, outer_width/2 - ci + 2);
            y_cyl(3.4, -ci - 1.7, 1.8, 6.6);
        }
        // fan cable down into the base
        translate([cable_slot[0], head_y0 - 1, cable_slot[2]])
            cube([cable_slot[1] - cable_slot[0], outer_width/2 - ci + 2, cable_slot[3] - cable_slot[2]]);
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
        }
        // bottom-plate screw inserts (from below)
        for (sx = [-1, 1], fz = [0, 1]) {
            p = corner_boss_xz(sx, fz);
            translate([p[0], 0, p[1]]) y_cyl(m3_insert_d, base_floor - 0.1, m3_insert_depth + 0.1);
        }
        // head-to-base inserts (from the top surface)
        for (p = join_pts)
            translate([p[0], 0, p[1]]) y_cyl(m3_insert_d, head_y0 - m3_insert_depth, m3_insert_depth + 0.1);
        // fan cable slot
        translate([cable_slot[0], base_roof - 1, cable_slot[2]])
            cube([cable_slot[1] - cable_slot[0], base_top_t + 2, cable_slot[3] - cable_slot[2]]);
        // +X wall: dial pot hole + knob recess (from the outer face)
        translate([in_x - 1, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=pot_hole_d, h=base_wall + 2);
        translate([outer_width/2 - knob_recess_depth, pot_y, pot_z])
            rotate([0, 90, 0]) cylinder(d=knob_recess_d, h=knob_recess_depth + 1);
        // +X wall: USB-C charge port and screen button, through to the bay
        translate([in_x - 1, usb_y - usb_open[1]/2, usb_z - usb_open[0]/2])
            cube([base_wall + 2, usb_open[1], usb_open[0]]);
        translate([in_x - 1, btn_y - btn_open/2, btn_z - btn_open/2])
            cube([base_wall + 2, btn_open, btn_open]);
        // rear wall: Zero USB-C
        translate([zero_usb_x - zero_usb_open[0]/2, zero_usb_y - zero_usb_open[1]/2, in_z1 - 1])
            cube([zero_usb_open[0], zero_usb_open[1], base_wall + 8]);
        // rear wall: OLED pod opening (wires) + its two screws
        translate([pod_x - 11, pod_y - 8, in_z1 - 1]) cube([22, 16, base_wall + 2]);
        for (s = [-1, 1])
            translate([pod_x + s*pod_screw_dx, pod_y, in_z1 - 6])
                cylinder(d=1.7, h=base_wall + 6.1);
    }
    zero_collar();
}

// ---------- Bottom plate ----------
module bottom_plate() {
    sled_screw_z = [sled_z0 + end_t/2, sled_z0 + sled_l - end_t/2];
    difference() {
        union() {
            rounded_box_y(outer_width, base_depth, base_bottom, base_floor, corner_r);
            // Zero carrier bosses
            for (dx = [-1, 1], dz = [-1, 1])
                translate([zero_usb_x + dx*carrier_hole_dx/2, 0, carrier_z0 + carrier_size[1]/2 + dz*carrier_hole_dz/2])
                    y_cyl(5, base_floor - 0.5, carrier_boss_h + 0.5);
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
        // carrier boss pilots (M2 self-tapping)
        for (dx = [-1, 1], dz = [-1, 1])
            translate([zero_usb_x + dx*carrier_hole_dx/2, 0, carrier_z0 + carrier_size[1]/2 + dz*carrier_hole_dz/2])
                y_cyl(1.7, base_floor - 1.5, carrier_boss_h + 2);
        // vent slots under the charger and buck
        for (x = [22 : 5 : 42])
            translate([x - 1, base_bottom - 1, 10]) cube([2, plate_t + 2, 50]);
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
buck_size = [17, 5, 22];        // MP1584 mini
bms_pos = [sled_x0 + 3, sled_z0 + 8];          // X0, Z0 on the lid
buck2_pos = [sled_x0 + 55, sled_z0 + 40];      // 12 V buck, on the lid beside the BMS
charger_pos = [19, 4];                          // on the plate
buck1_pos = [22, 42];                           // 5 V buck, on the plate

module fan_keepout() {
    translate([-fan_size/2, -fan_size/2, fan_z0]) cube([fan_size, fan_size, fan_thickness]);
}
module cells_keepout() { translate([sled_x0, base_floor, sled_z0]) cells(); }
module sled_placed() { translate([sled_x0, base_floor, sled_z0]) { sled(); sled_lid(); } }
module bms_keepout() { translate([bms_pos[0], lid_top, bms_pos[1]]) cube(bms_size); }
module buck2_keepout() { translate([buck2_pos[0], lid_top, buck2_pos[1]]) cube(buck_size); }
module charger_keepout() { translate([charger_pos[0], base_floor, charger_pos[1]]) cube(charger_size); }
module buck1_keepout() { translate([buck1_pos[0], base_floor, buck1_pos[1]]) cube(buck_size); }
// perfboard + Zero + fan header, on the plate bosses; the USB-C sticks out 0.5 at the back
module carrier_keepout() {
    translate([carrier_x0, base_floor + carrier_boss_h, carrier_z0])
        cube([carrier_size[0], 12.5, carrier_size[1] + 0.5]);
}
module pot_keepout() {          // body + switch + terminals, and the bushing through the wall
    translate([in_x - pot_body_depth, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=pot_body_d + 2, h=pot_body_depth);
    translate([in_x - 0.1, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=7, h=base_wall + 1.2);
}
module usb_socket_keepout() {
    translate([in_x - 15, usb_y - 7, usb_z - 7]) cube([15, 14, 14]);
}
module button_keepout() {
    translate([in_x - 6.5, btn_y - 4, btn_z - 4]) cube([6.5, 8, 8]);
}
// What has to pass through each opening, at fixed sizes: the charge socket's
// body (12 x 9), the 6x6 button, the Zero's USB-C plug (12 x 7 overmould),
// and the fan's 4-pin plug (10 x 7) down through the cable slot.
module openings_keepout() {
    translate([in_x - 1, usb_y - 4.5, usb_z - 6]) cube([base_wall + 6, 9, 12]);
    translate([in_x - 1, btn_y - 3, btn_z - 3]) cube([base_wall + 6, 6, 6]);
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
module fan_bolts_keepout() {    // M3 bolt shanks and their nuts
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx*mount_spacing/2, sy*mount_spacing/2, 0]) {
        translate([0, 0, 1]) cylinder(d=3, h=fan_z0 + fan_thickness + gusset_t + 1.6);
        translate([0, 0, fan_z0 + fan_thickness + gusset_t - 2.4]) cylinder(d=6.35, h=2.4, $fn=6);
    }
}

// ---------- Render ----------
if (part == "head") {
    head();
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
