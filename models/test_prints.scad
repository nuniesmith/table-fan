// Test prints: small, quick pieces that check the fits before the long
// prints. Print them in the filament you'll use for the real parts: ASA and
// PETG shrink differently. Each renders in its print orientation.
//   test = "inserts"   : 3 pilot sizes for each heat-set insert (M2, M3, M4).
//                        Set m2/m3/m4_insert_d in fan_housing.scad to the one
//                        that went in straight and won't pull out.
//   test = "fan_fit"   : the head's rear 12 mm. The fan should drop in and
//                        rest on the ledges, M3 bolts should pass its corner
//                        holes, the nuts sit in their pockets, and a faceplate
//                        screws on the back.
//   test = "side_wall" : the base's +X wall round the dial pot, charge port and
//                        button: check each part when it arrives.
//   test = "sled_end"  : one end of the battery sled: a cell should slide in
//                        without force or rattle.
// Units: mm

include <fan_housing.scad>
part = "none";                  // the housing's parts, not its default render

test = "inserts";               // [inserts, fan_fit, side_wall, sled_end]

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

module fan_fit() {                // rear face on the bed, as the head prints
    translate([0, 0, head_depth]) rotate([180, 0, 0])
        intersection() {
            head();
            translate([-100, -100, head_depth - 12]) cube([200, 200, 12.1]);
        }
}

module side_wall() {              // outer face on the bed
    translate([-6, 88, outer_width/2]) rotate([0, 90, 0])
        intersection() {
            base();
            translate([58, pot_y - 14, 6]) cube([13, 28, 72]);
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
else if (test == "side_wall") side_wall();
else if (test == "sled_end") sled_end();
