// U-Bail Bracket for the table fan - side-pivot hanging/prop stand.
// Prints flat on the bed (X-Y plane), no supports. Drill the 4.5mm pivot
// holes after printing if they don't come out clean.
//
// Assembly: M4 screw through each arm into the heat-set insert in the
// housing's pivot pad. Friction pivot - tighten to taste (truck vibration).
//   - Folded: arms point down, bar nests in the groove under the base.
//   - Prop: insert an M3 screw (from your kit) in each stop-pin hole, swing
//     the bail back until the arms rest on the pins (~30 deg).
//   - Hang: pull the stop pins, swing the bail up ~100 deg, hook the bar
//     over a wall hook. The fan dangles below on the two M4 pivots.
//
// Arm centers at X=±75.5 (ride on the 3mm pivot pads); pivot holes at local
// Y=0 align with the housing pivots at (Y=0, Z=50).

bail_arm_x = 75.5;   // arm centerline |X|
bail_arm_t = 5;      // arm thickness (X)
bail_arm_w = 8;      // arm width (Z)
bail_arm_l = 71;     // pivot center to bar center
bail_bar_y = -73.5;  // bar bottom edge (nests in base groove)
bail_z0 = 46;        // arm/bar front face (Z)

module bail() {
    difference() {
        union() {
            // arms (pivot hole 6mm below the top end)
            for (sx = [1, -1])
                translate([sx*bail_arm_x - bail_arm_t/2, -bail_arm_l, bail_z0])
                    cube([bail_arm_t, bail_arm_l + 6, bail_arm_w]);
            // bottom bar joining the arms
            translate([-bail_arm_x - bail_arm_t/2, bail_bar_y, bail_z0])
                cube([2*bail_arm_x + bail_arm_t, 5, bail_arm_w]);
        }
        // pivot holes (M4 clearance)
        for (sx = [1, -1])
            translate([sx*bail_arm_x - 3, 0, 50])
                rotate([0,90,0]) cylinder(d=4.5, h=6);
    }
}

// ---------- Render ----------
bail();
