// Removable Faceplate for 120mm Noctua Fan Housing
// Secured with 4x M2 screws + M2 nuts (nuts sit in hex pockets in the housing)
// Units: mm
// Matches fan_housing.scad

/* [Parameters – keep in sync with housing] */
outer_width = 140;          // MUST match fan_housing.scad
faceplate_thickness = 2.8;
fan_size = 120;
grille_margin = 8;              // how much solid border around the grille
faceplate_screw_offset = 66;    // MUST match housing (cardinal points now)
m2_clearance_d = 2.2;           // clearance hole for M2 screw
use_countersink = true;
countersink_d = 4.2;
countersink_depth = 1.2;

$fn = 64;

module faceplate() {
    difference() {
        union() {
            // Frame: rounded-square plate with circular opening
            difference() {
                hull() {
                    for (x = [-1,1])
                        for (y = [-1,1])
                            translate([x*(outer_width/2 - 4), y*(outer_width/2 - 4), 0])
                                cylinder(d=8, h=faceplate_thickness);
                }
                translate([0,0,-1])
                    cylinder(d=fan_size - 6, h=faceplate_thickness + 2);
            }
            // Grille: outer ring + 4 concentric rings + 24 spokes + hub
            // (reference-style dense radial grille; gaps ~10-12mm)
            difference() {
                cylinder(d=fan_size - 4, h=faceplate_thickness);
                cylinder(d=fan_size - 10, h=faceplate_thickness + 1);
            }
            for (r = [18, 30, 42, 52]) {
                difference() {
                    cylinder(d=r*2 + 2, h=faceplate_thickness);
                    cylinder(d=r*2 - 2, h=faceplate_thickness + 1);
                }
            }
            cylinder(d=30, h=faceplate_thickness);  // center hub
            for (a = [0 : 15 : 345]) {
                rotate([0,0,a])
                    translate([36, 0, faceplate_thickness/2])
                        cube([44, 2, faceplate_thickness], center=true);
            }
        }

        // M2 clearance holes (cardinal points - must match housing)
        for (a = [0, 90, 180, 270]) {
            rotate([0,0,a])
                translate([faceplate_screw_offset, 0, -0.1]) {
                    cylinder(d=m2_clearance_d, h=faceplate_thickness + 1);
                    if (use_countersink)
                        translate([0,0,faceplate_thickness - countersink_depth])
                            cylinder(d1=m2_clearance_d, d2=countersink_d, h=countersink_depth + 0.1);
                }
        }
    }
}

faceplate();
