// U-bail for the table fan: carry handle and hook hanger.
// Two flat arms pivot on M4 thumb screws into heat-set inserts in the head's
// top corner columns, in the recesses along the duct's sides. Teeth on each
// arm's inner face mesh with teeth round its pivot every 15 deg, and the
// thumb screw clamps them, so the angle holds in a truck:
//   - 0 deg, up: carry it, or hang it by the bar, with 46 mm of hook room
//     over the head. Hung, it points about level at 0 deg and further down
//     the further back the bail is set: about 15 deg down at 30, 36 at 90.
//   - 90 deg, folded: the arms lie along the top of the duct's sides, flush
//     with the front frame and the base, and the bar sits 8 mm behind the
//     rear grille.
// Loosen the thumb screws about two turns to move it, and hand-tighten them
// again.
//
// Until 2026-10-18 the arms swung in channels cut into ribs on the side
// walls, but a pivot normal to the wall swings each arm through its own
// rib, so the bail could not move at all. Until 2026-10-20 it hung on
// friction alone and folded onto the base behind a 36 mm head.
//
// Prints flat as modelled: the U on the bed, 20 mm tall, with the teeth on
// the arms' inner faces and teardrop pivot holes; no supports.

include <fan_housing.scad>
part = "none";                  // only the housing's dimensions are needed here

bail_w = 20;                    // the arms' and the bar's width: the bail prints this tall
bail_len = 64;                  // pivot centre to bar centre
bail_bar_h = 8;
bail_fillet = 6;
bail_fold = 90;                 // folded back along the duct's sides
bail_hook_min = 40;             // hook room the checks demand between the head's top and the bar
arm_x0 = duct_x + tooth_h + tooth_gap;          // 64: each arm's inner face, teeth meshed
arm_x1 = arm_x0 + bail_arm_t;                   // 70: its outer face, flush with the front frame

/* [Render] */
bail_part = "bail";             // [bail, print]

// A hole along X, its top pointed (the bail prints Z up), so it doesn't droop.
module x_teardrop(d, len) {
    rotate([0, 90, 0]) linear_extrude(len, center=true)
        hull() { circle(d=d); translate([-d/sqrt(2), 0]) square(0.01, center=true); }
}

// play moves both arms outward (+) or inward (-) from meshed, for the checks:
// loosened for a swing, or pushed into the wall's teeth.
module bail_teeth(play = 0) {   // on each arm's inner face, half a tooth round from the wall's
    both_sides() translate([arm_x0 + play + 0.01, pivot_y, pivot_z]) rotate([0, -90, 0])
        serration(tooth_n, tooth_r[0], tooth_r[1], tooth_h + 0.01, 180/tooth_n);
}

module bail(play = 0) {
    z0 = pivot_z - bail_w/2;
    y_bar = pivot_y + bail_len;
    x0 = arm_x0 + play;
    x1 = arm_x1 + play;
    yi = y_bar - bail_bar_h/2 + 0.1;
    difference() {
        union() {
            both_sides() {
                translate([x0, pivot_y, z0]) cube([bail_arm_t, bail_len, bail_w]);
                translate([x0, pivot_y, pivot_z]) rotate([0, 90, 0]) cylinder(d=bail_w, h=bail_arm_t);
                // fillet inside the arm-to-bar corner
                translate([0, 0, z0]) linear_extrude(bail_w)
                    polygon([[x0 + 0.1, yi], [x0 - bail_fillet, yi], [x0 + 0.1, yi - bail_fillet]]);
            }
            bail_teeth(play);
            translate([-x1, y_bar - bail_bar_h/2, z0]) cube([2*x1, bail_bar_h, bail_w]);
        }
        both_sides() translate([x0 + bail_arm_t/2, pivot_y, pivot_z]) x_teardrop(4.6, bail_arm_t + 2*tooth_h + 2);
    }
}

// The bail swung `a` degrees from up; positive swings the bar rearward.
module bail_at(a, play = 0) {
    translate([0, pivot_y, pivot_z]) rotate([a, 0, 0])
        translate([0, -pivot_y, -pivot_z]) bail(play);
}
module bail_teeth_at(a, play = 0) {
    translate([0, pivot_y, pivot_z]) rotate([a, 0, 0])
        translate([0, -pivot_y, -pivot_z]) bail_teeth(play);
}

// ---------- Render ----------
if (bail_part == "bail") {
    bail();
} else if (bail_part == "print") {
    translate([0, -pivot_y, -(pivot_z - bail_w/2)]) bail();
}
