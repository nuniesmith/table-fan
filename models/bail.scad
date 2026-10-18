// U-bail for the table fan: carry handle and wall-hook hanger.
// Two flat arms pivot on M4 screws into heat-set inserts in the head's side
// walls. The arms ride OUTSIDE the walls (a nylon washer between), so
// nothing is in their way, and the bar passes over the top of the head.
//   - Up: carry it, or hook the bar over a wall hook. The fan hangs below
//     the pivots; tighten the M4 screws to hold the angle you want.
//   - Back: swing it rearward until the bar rests on the base behind the
//     head (about 158 deg).
// The old prop position is gone: the base stands on its own.
//
// Until 2026-10-18 the arms swung in channels cut into ribs on the side
// walls, but a pivot normal to the wall swings each arm through its own
// rib, so the bail could not move at all.
//
// Prints flat as modelled (Z is the 12 mm thickness), no supports. Drill
// the 4.5 mm pivot holes after printing if they droop.

include <fan_housing.scad>
part = "none";                  // only the housing's dimensions are needed here

bail_washer = 1;                // nylon washer between each arm and the head
bail_arm_t = 5;                 // X
bail_arm_w = 12;                // Z
bail_len = 80;                  // pivot centre to bar centre
bail_bar_h = 8;                 // Y
bail_boss_d = bail_arm_w;       // round arm ends; no wider, so it prints flat
bail_fillet = 6;
bail_arm_x = outer_width/2 + bail_washer + bail_arm_t/2;    // 73.5
bail_rest_angle = 157;          // swung back, the bar lands on the base at ~157.7 deg

/* [Render] */
bail_part = "bail";             // [bail, print]

module bail() {
    z0 = pivot_z - bail_arm_w/2;
    y_bar = pivot_y + bail_len;
    difference() {
        union() {
            for (sx = [-1, 1]) {
                translate([sx*bail_arm_x - bail_arm_t/2, pivot_y, z0])
                    cube([bail_arm_t, bail_len, bail_arm_w]);
                translate([sx*bail_arm_x, pivot_y, pivot_z])
                    rotate([0, 90, 0]) cylinder(d=bail_boss_d, h=bail_arm_t, center=true);
                // fillet inside each arm-to-bar corner
                xi = sx*(bail_arm_x - bail_arm_t/2 + 0.1);
                yi = y_bar - bail_bar_h/2 + 0.1;
                translate([0, 0, z0]) linear_extrude(bail_arm_w)
                    polygon([[xi, yi], [xi - sx*bail_fillet, yi], [xi, yi - bail_fillet]]);
            }
            translate([-bail_arm_x - bail_arm_t/2, y_bar - bail_bar_h/2, z0])
                cube([2*bail_arm_x + bail_arm_t, bail_bar_h, bail_arm_w]);
        }
        for (sx = [-1, 1])
            translate([sx*bail_arm_x, pivot_y, pivot_z])
                rotate([0, 90, 0]) cylinder(d=4.5, h=bail_arm_t + 2, center=true);
    }
}

// The bail swung `a` degrees from up; positive swings the bar rearward.
module bail_at(a) {
    translate([0, pivot_y, pivot_z]) rotate([a, 0, 0])
        translate([0, -pivot_y, -pivot_z]) bail();
}

// ---------- Render ----------
if (bail_part == "bail") {
    bail();
} else if (bail_part == "print") {
    translate([0, -pivot_y, -(pivot_z - bail_arm_w/2)]) bail();
}
