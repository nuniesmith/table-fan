// Geometry checks, run by tools/check_geometry.py. Each `check` value
// renders one solid; the script exports it and measures its volume.
//   clear  : must be empty (an interference, or an opening that is blocked)
//   touch  : must NOT be empty (a contact that has to exist)
//   inside : must be empty (material that should surround a hole is missing)
// The script also renders every printable part to confirm it is manifold.

include <bail.scad>
bail_part = "none";
use <faceplate.scad>

check = "";

blade_d = 116;                  // the fan's blade disc

module front_faceplate() { mirror([0, 0, 1]) faceplate(); }

// Everything the bail must clear while it swings.
module bail_obstacles() {
    head();
    rounded_box_z(outer_width, outer_width, -2.8, 0, corner_r);                // the front faceplate
    rounded_box_y(outer_width, base_depth, base_bottom, head_y0, corner_r);    // base + plate
    oled_pod();
    zero_collar();
    translate([outer_width/2, pot_y, pot_z]) rotate([0, 90, 0]) cylinder(d=22, h=18);   // knob
}

module board_keepouts() {
    bms_keepout(); buck2_keepout(); charger_keepout(); buck1_keepout();
    carrier_keepout(); pot_keepout(); usb_socket_keepout(); button_keepout();
    rear_screws_keepout();
}

// Material that must surround each insert pilot (1.2-1.5 mm walls).
module head_pilot_rings() {
    // the bail's pivots, from the recess floor into the top columns
    for (sx = [-1, 1])
        translate([sx*(duct_x - 0.2), pivot_y, pivot_z]) rotate([0, -sx*90, 0])
            difference() { cylinder(d=m4_insert_d + 3, h=m4_insert_depth - 0.2); cylinder(d=m4_insert_d, h=20, center=true); }
    // the front faceplate's
    for (a = [0, 90, 180, 270])
        rotate([0, 0, a]) translate([faceplate_screw_offset, 0, 0.2])
            difference() { cylinder(d=m2_insert_d + 2.4, h=m2_insert_depth - 0.2); cylinder(d=m2_insert_d, h=20, center=true); }
    // the fan's, in the columns' front faces
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx*mount_spacing/2, sy*mount_spacing/2, fan_z0 + fan_thickness + 0.2])
            difference() { cylinder(d=m3_insert_d + 3, h=m3_insert_depth - 0.2); cylinder(d=m3_insert_d, h=20, center=true); }
    // the rear head-to-base screws', up into the bottom columns
    for (p = rear_join_pts)
        translate([p[0], 0, p[1]]) difference() { y_cyl(m3_insert_d + 3, head_y0 + 0.2, m3_insert_depth - 0.2); y_cyl(m3_insert_d, head_y0 - 1, 20); }
}
module base_pilot_rings() {
    for (sx = [-1, 1], fz = [0, 1]) {
        p = corner_boss_xz(sx, fz);
        translate([p[0], 0, p[1]]) difference() { y_cyl(m3_insert_d + 3, base_floor + 0.2, m3_insert_depth); y_cyl(m3_insert_d, base_floor - 1, 20); }
    }
    for (p = join_pts)
        translate([p[0], 0, p[1]]) difference() { y_cyl(m3_insert_d + 3, head_y0 - m3_insert_depth, m3_insert_depth - 0.2); y_cyl(m3_insert_d, head_y0 - 20, 30); }
    // the wall + boss under the pot nut (3 mm), across the M7 nut and washer's 14 mm
    translate([in_x - pot_boss_t + 0.1, pot_y, pot_z]) rotate([0, 90, 0])
        difference() { cylinder(d=14, h=pot_boss_t + base_wall - knob_recess_depth - 0.2); cylinder(d=pot_hole_d, h=20, center=true); }
}

if (check == "fan_vs_head") {                   // review: the mezzanine and the dial cut into the fan
    intersection() { fan_keepout(); head(); }
} else if (check == "fan_on_ledges") {          // touch: the fan's rear corners bear on the columns
    intersection() { translate([0, 0, 0.2]) fan_keepout(); head(); }
} else if (check == "airflow") {                // review: a 16 mm slab behind the fan blocked 68% of the blades
    intersection() {
        union() {
            translate([0, 0, fan_z0 + fan_thickness])
                cylinder(d=blade_d, h=head_depth - rear_grille_t - fan_z0 - fan_thickness);
            translate([0, 0, head_depth]) cylinder(d=blade_d, h=6);         // just behind the rear grille
        }
        union() { head(); base(); oled_pod(); bail_at(0); bail_at(bail_fold); }
    }
} else if (check == "cells_vs_sled") {          // review: 65 mm cells in a 24 mm sled
    intersection() { cells_keepout(); sled_placed(); }
} else if (check == "sled_vs_body") {           // review: the sled poked out of the base and into the fan
    intersection() { sled_placed(); union() { base(); bottom_plate(); head(); } }
} else if (check == "boards_vs_body") {
    intersection() { board_keepouts(); union() { base(); bottom_plate(); head(); } }
} else if (check == "boards_vs_each_other") {   // includes the pot against the fan, cells and sled
    ko = ["bms", "buck2", "charger", "buck1", "carrier", "pot", "usb", "button", "sled", "fan", "rear_screws"];
    for (i = [0 : len(ko) - 2], j = [i + 1 : len(ko) - 1])
        intersection() { keepout(ko[i]); keepout(ko[j]); }
} else if (check == "openings") {               // review: the USB-C and button holes were blind
    intersection() { openings_keepout(); union() { head(); base(); bottom_plate(); oled_pod(); } }
} else if (check == "bail_sweep") {             // review: the bail collided at every angle
    // loosened (its teeth lifted clear of the wall's), from up to folded
    for (a = [0 : 3 : bail_fold]) intersection() { bail_at(a, tooth_h + 0.3); bail_obstacles(); }
} else if (check == "bail_detents") {           // at each 15 deg step the teeth mesh without colliding
    for (a = [0 : 360/tooth_n : bail_fold]) intersection() { bail_at(a); head(); }
} else if (check == "bail_teeth_engage") {      // touch: clamped, the arms' teeth bear on the wall's
    intersection() { bail_teeth_at(0, -0.3); side_teeth(); }
} else if (check == "bail_folds_flush") {       // folded, nothing of the bail stands out past the sides
    intersection() {
        bail_at(bail_fold);
        both_sides() translate([outer_width/2 + 0.01, -200, -200]) cube([50, 400, 400]);
    }
} else if (check == "hook_clearance") {         // up, the bar stands at least bail_hook_min over the head
    intersection() {
        bail_at(0);
        translate([-arm_x0 + 1, outer_width/2, pivot_z - bail_w/2 - 1]) cube([2*arm_x0 - 2, bail_hook_min, bail_w + 2]);
    }
} else if (check == "parts_mate") {
    intersection() { head(); base(); }
    intersection() { head(); bottom_plate(); }
    intersection() { base(); bottom_plate(); }
    intersection() { base(); oled_pod(); }
    intersection() { head(); oled_pod(); }
    intersection() { head(); front_faceplate(); }
    intersection() { head(); bail_at(0); }
} else if (check == "fan_bolts") {              // review: the top fan screws could not clamp
    intersection() { fan_bolts_keepout(); head(); }
} else if (check == "oled_fit") {               // review: the pod's posts left no room for the PCB
    intersection() { oled_keepout(); oled_pod(); }
} else if (check == "oled_on_posts") {          // touch: the PCB seats on the posts
    intersection() { translate([0, 0, 0.2]) oled_pcb_keepout(); oled_pod(); }
} else if (check == "button_floor") {          // touch: a press on the button bears on a floor, not glue
    intersection() { translate([-0.2, 0, 0]) button_body_keepout(); base(); }
} else if (check == "head_pilots") {            // inside: walls round the head's insert pilots
    difference() { head_pilot_rings(); head(); }
} else if (check == "base_pilots") {            // inside: walls round the base's pilots; the knob recess is on the outer face
    difference() { base_pilot_rings(); base(); }
}

module keepout(name) {
    if (name == "bms") bms_keepout();
    else if (name == "buck2") buck2_keepout();
    else if (name == "charger") charger_keepout();
    else if (name == "buck1") buck1_keepout();
    else if (name == "carrier") carrier_keepout();
    else if (name == "pot") pot_keepout();
    else if (name == "usb") usb_socket_keepout();
    else if (name == "button") button_keepout();
    else if (name == "sled") { sled_placed(); cells_keepout(); }
    else if (name == "fan") fan_keepout();
    else if (name == "rear_screws") rear_screws_keepout();
}
