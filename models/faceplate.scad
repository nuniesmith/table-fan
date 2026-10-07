// Removable Faceplate for 120mm Noctua Fan Housing
// Secured with 4× M2 × 6 mm screws
// Units: mm
// Matches fan_housing.scad

/* [Parameters – keep in sync with housing] */
outer_width = 135;
faceplate_thickness = 2.8;
fan_size = 120;
grille_margin = 8;              // how much solid border around the grille
faceplate_screw_offset = 58;    // MUST match housing
m2_clearance_d = 2.2;           // clearance hole for M2 screw
use_countersink = true;
countersink_d = 4.2;
countersink_depth = 1.2;

$fn = 64;

module faceplate() {
    difference() {
        // Outer plate – slightly smaller than housing for flush look, or match for flush
        hull() {
            for (x = [-1,1])
                for (y = [-1,1])
                    translate([x*(outer_width/2 - 4), y*(outer_width/2 - 4), 0])
                        cylinder(d=8, h=faceplate_thickness);
        }
        
        // Main airflow opening (slightly smaller than fan for safety)
        translate([0,0,-1])
            cylinder(d=fan_size - 6, h=faceplate_thickness + 2);
        
        // Optional decorative / protective grille bars (simple radial or cross)
        // Simple cross + ring for strength while keeping airflow high
        // (comment out if you prefer fully open)
        /*
        for (a = [0, 45, 90, 135]) {
            rotate([0,0,a])
                translate([0,0,faceplate_thickness/2])
                    cube([fan_size - 10, 2.2, faceplate_thickness + 1], center=true);
        }
        */
        
        // Protective but high-airflow grille: outer ring + 3 concentric rings + 6 spokes
        // Outer safety ring
        difference() {
            cylinder(d=fan_size - 4, h=faceplate_thickness + 1);
            cylinder(d=fan_size - 10, h=faceplate_thickness + 2);
        }
        // Inner rings
        for (r = [22, 38, 52]) {
            difference() {
                cylinder(d=r*2 + 2.5, h=faceplate_thickness + 1);
                cylinder(d=r*2 - 2.5, h=faceplate_thickness + 2);
            }
        }
        // Spokes
        for (a = [0 : 30 : 150]) {
            rotate([0,0,a])
                translate([0, 0, faceplate_thickness/2])
                    cube([fan_size - 12, 1.8, faceplate_thickness + 1], center=true);
        }
        
        // M2 clearance holes
        for (a = [45, 135, 225, 315]) {
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
