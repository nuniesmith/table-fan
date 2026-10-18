// U-Bail Bracket for the table fan - side-pivot hanging/prop stand.
// Prints flat on the bed (X-Y plane), no supports. Drill the 4.5mm pivot
// holes after printing if they don't come out clean.
//
// The arms nest into channels in the housing's side ribs so the folded bail
// sits flush with the body (like the reference). Pivot discs rotate in
// pockets; M4 screws through the arms into heat-set inserts (friction pivot
// - tighten to taste for truck vibration).
//   - Folded: arms point down in the channels, bar nests in the groove
//     under the base.
//   - Prop: insert an M3 screw (from your kit) in each stop-pin hole, swing
//     the bail back until the arms rest on the pins (~30 deg).
//   - Hang: pull the stop pins, swing the bail up ~100 deg, hook the bar
//     over a wall hook. The fan dangles below on the two M4 pivots.
//
// Arm centers at X=±70.5 (in the 9mm channels); pivot holes at local Y=0
// align with the housing pivots at (Y=0, Z=50).

bail_arm_x = 70.5;   // arm centerline |X| (channel X 68..74)
bail_arm_t = 5;      // arm thickness (X)
bail_arm_w = 8;      // arm width (Z)
bail_arm_l = 71;     // pivot center to bar center
bail_disc_r = 6;     // pivot disc radius
bail_bar_y = -73.5;  // bar bottom edge (nests in base groove)
bail_z0 = 46;        // arm/bar front face (Z)

module bail() {
    difference() {
        union() {
            // arms
            for (sx = [1, -1])
                translate([sx*bail_arm_x - bail_arm_t/2, -bail_arm_l, bail_z0])
                    cube([bail_arm_t, bail_arm_l + 6, bail_arm_w]);
            // pivot discs (rotate in the housing pockets; 5.4 thick for a solid
            // overlap with the arms - avoids coplanar faces)
            for (sx = [1, -1])
                translate([sx*bail_arm_x, 0, 50])
                    rotate([0,90,0]) cylinder(r=bail_disc_r, h=bail_arm_t + 0.4, center=true);
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
