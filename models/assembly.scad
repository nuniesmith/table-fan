// The whole fan assembled: head, base, bottom plate, OLED pod, the front
// faceplate, bail, battery sled, knob, with the fan, cells, boards and the
// bail's thumb screws as ghosts. For looking at, not for printing: export each part from its own
// file (see README).

include <bail.scad>
bail_part = "none";
use <faceplate.scad>
use <knob.scad>

/* [View] */
bail_angle = 0;                 // 0 = up (carry / hang); 90 = folded back along the duct; 15 deg steps
show_faceplates = true;
view = "full";                  // [full, cutaway, base_layout]: cutaway slices off the -X half;
                                // base_layout shows the base below its roof, from above
upright = true;                 // stand it up for OpenSCAD's Z-up view (the models are Y-up)

module assembled() {
    color("SteelBlue") head();
    color("LightSteelBlue") base();
    color("SlateGray") bottom_plate();
    color("SteelBlue") oled_pod();
    color("Orange") bail_at(bail_angle);
    if (show_faceplates) color("DimGray") mirror([0, 0, 1]) faceplate();
    color("Peru") sled_placed();
    color("Black") translate([outer_width/2 + 1.5, pot_y, pot_z]) rotate([0, 90, 0]) knob();
    // bought parts
    color("Gainsboro", 0.5) fan_keepout();
    color("Teal") cells_keepout();
    color("Green") bms_keepout();
    color("RoyalBlue") charger_keepout();
    color("DarkGreen") carrier_pcb_board();
    color("MediumPurple") carrier_pcb_parts();
    color("Gold") { pot_keepout(); usb_socket_keepout(); button_keepout(); }
    color("Silver") both_sides()       // M4 x 16 knurled thumb screws, on a washer
        translate([arm_x1, pivot_y, pivot_z]) rotate([0, 90, 0]) { cylinder(d=9, h=1); translate([0, 0, 1]) cylinder(d=12, h=6); }
    color("Black") oled_keepout();
}

rotate(upright ? [90, 0, 180] : [0, 0, 0])
    if (view == "cutaway")
        difference() {
            assembled();
            translate([-200, -200, -50]) cube([200, 400, 300]);
        }
    else if (view == "base_layout")
        intersection() {
            assembled();
            translate([-100, base_bottom - 1, -20]) cube([200, base_roof - base_bottom + 0.5, 160]);
        }
    else
        assembled();
