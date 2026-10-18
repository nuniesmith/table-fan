// Knob for the 10k dial switch (6mm knurled shaft, e.g. WH138)
// Press-fit on the knurling + M3 set screw. Pointer notch shows the setting.
// Pairs with the knob recess in fan_housing.scad (recess d=20).
// Units: mm

shaft_d = 6.1;      // press fit on a 6mm knurled shaft
knob_d = 22;
knob_h = 16;

$fn = 64;

module knob() {
    difference() {
        // body with a slight taper feel (two stacked cylinders)
        union() {
            cylinder(d=knob_d, h=knob_h - 4);
            translate([0, 0, knob_h - 4]) cylinder(d1=knob_d, d2=knob_d - 4, h=4);
        }
        // shaft bore (blind, from the bottom)
        translate([0, 0, -0.1]) cylinder(d=shaft_d, h=knob_h - 3);
        // M3 set screw (radial)
        translate([0, 0, 5]) rotate([90, 0, 0])
            cylinder(d=2.5, h=knob_d/2 + 1);
        // pointer notch on the top rim
        translate([knob_d/2 - 4, -1, knob_h - 2.1]) cube([4, 2, 2.2]);
    }
    // grip ribs
    for (a = [0 : 15 : 345])
        rotate([0, 0, a])
            translate([knob_d/2 - 0.5, 0, (knob_h - 4)/2])
                cube([1.5, 1.5, knob_h - 4], center=true);
}

knob();
