// Test prints: small, quick pieces that check the fits before the long
// prints. Print them in the filament you'll use for the real parts: ASA and
// PETG shrink differently. Each renders in its print orientation.
//   test = "inserts"   : 3 pilot sizes for each heat-set insert (M2, M3, M4).
//                        Set m2/m3/m4_insert_d in fan_housing.scad to the one
//                        that went in straight and won't pull out.
//   test = "fan_fit"   : the head round the fan's rear 6 mm, with the corner
//                        columns' front 8 mm. The fan should drop in and rest
//                        on the columns, and M3 inserts go into their pilots,
//                        so M3 x 30 bolts through the fan's corners reach them.
//   test = "bail_joint": the head's corner round one bail pivot, with its teeth
//                        and M4 insert pilot, and the pivot end of an arm. Put
//                        the M4 insert in and screw the arm on with an M4 x 16
//                        thumb screw: the teeth should mesh every 15 deg, hold
//                        hand-tight, and let the arm swing when it's loosened
//                        about two turns.
//   test = "side_wall" : the base's +X wall round the dial pot, charge port and
//                        button, standing on its top edge as the base prints, so
//                        the openings come out as they will in the base. Check
//                        each part when it arrives.
//   test = "sled_end"  : one end of the battery sled: a cell should slide in
//                        without force or rattle.
// Units: mm

include <bail.scad>
bail_part = "none";             // the housing's and the bail's parts, not their default renders

test = "inserts";               // [inserts, fan_fit, bail_joint, side_wall, sled_end]

module insert_coupon() {
    rows = [["M2", [3.0, 3.2, 3.4], 5], ["M3", [4.0, 4.2, 4.4], 6], ["M4", [5.4, 5.6, 5.8], 8.5]];
    px = 14; py = 16;
    difference() {
        union() {
            translate([-8, -9.5, 0]) cube([10 + 2*px + 15, 2*py + 15.5, 2]);
            for (r = [0 : 2], c = [0 : 2])
                translate([10 + c*px, r*py, 0]) cylinder(d=rows[r][1][c] + 4, h=rows[r][2] + 2);
        }
        for (r = [0 : 2], c = [0 : 2])
            translate([10 + c*px, r*py, 2]) cylinder(d=rows[r][1][c], h=20);
        // labels: the insert size by each row, each hole's diameter under it
        for (r = [0 : 2]) {
            translate([-3, r*py, 1.4]) linear_extrude(1)
                text(rows[r][0], size=3, halign="center", valign="center");
            for (c = [0 : 2])
                translate([10 + c*px, r*py - 6.5, 1.4]) linear_extrude(1)
                    text(str(rows[r][1][c]), size=2.2, halign="center", valign="center");
        }
    }
}

module fan_fit() {                // rear (cut) face on the bed, as the head prints
    translate([0, 0, fan_section]) rotate([180, 0, 0])
        intersection() {
            head();
            translate([-100, -100, fan_section - 14]) cube([200, 200, 14]);
        }
}

module bail_joint() {
    // the +X top corner of the duct round the pivot, its rear (cut) face on the
    // bed as the head prints, so the teeth come out as they will on the head
    z1 = pivot_z + 14;
    translate([0, 0, z1]) rotate([180, 0, 0])
        intersection() {
            head();
            translate([50, pivot_y - 13, pivot_z - 12]) cube([14, outer_width/2 - pivot_y + 14, z1 - pivot_z + 12]);
        }
    // the +X arm's pivot end, flat as the bail prints, beside it
    translate([18, -110, -(pivot_z - bail_w/2)])
        intersection() {
            bail();
            translate([arm_x0 - 2, pivot_y - bail_w/2 - 1, -50]) cube([bail_arm_t + 3, bail_w + 31, 200]);
        }
}

module side_wall() {              // top edge on the bed, as the base prints
    translate([-58, -6, head_y0]) rotate([-90, 0, 0])
        intersection() {
            base();
            translate([58, pot_y - 14, 6]) cube([13, head_y0 + 0.1 - (pot_y - 14), 72]);
        }
}

module sled_end() {               // base on the bed
    rotate([90, 0, 0])
        intersection() {
            sled();
            translate([-1, -1, -1]) cube([sled_w + 2, sled_h + 2, end_t + 16]);
        }
}

if (test == "inserts") insert_coupon();
else if (test == "fan_fit") fan_fit();
else if (test == "bail_joint") bail_joint();
else if (test == "side_wall") side_wall();
else if (test == "sled_end") sled_end();
