// Portable 120mm Noctua Fan Housing
// Compatible with NF-F12 industrialPPC-3000 PWM (120x120x25 mm)
// Mounting hole spacing: 105 mm center-to-center
// Designed for removable M2 faceplate and internal 4-pin connector
// Units: millimeters
// Author: Grok design for nuniesmith/table-fan

/* [Main Dimensions] */
outer_width = 135;          // Overall width/height of square body
outer_depth = 58;           // Front-to-back depth (fan 25 + electronics bay + walls)
wall_thickness = 2.5;
fan_size = 120;
fan_thickness = 25;
fan_clearance = 0.4;        // radial clearance around fan
mount_spacing = 105;        // standard 120mm fan hole spacing
mount_hole_d = 3.4;         // for M3 screw (clearance)
m2_hole_d = 1.7;            // for M2 screw into plastic or insert
m2_insert_d = 3.2;          // if using heat-set M2 inserts (adjust to your insert)
use_heatset_m2 = true;

/* [Faceplate Mounting] */
// Positions of the 4 M2 holes relative to center (place them outside the fan frame or on the bezel)
// 58 mm puts them near the corners of a 135 mm body – good for strength and aesthetics
faceplate_screw_offset = 58; // distance from center to each M2 hole (MUST match faceplate.scad)

/* [Electronics Bay] */
electronics_bay_height = 28; // extra height at bottom for battery + Pico + modules
bay_depth = 30;              // how deep the rear bay is

/* [Other] */
handle_height = 18;
stand_slot = true;

$fn = 64;

// ---------- Helper modules ----------
module rounded_cube(size, r=3, center=false) {
    // simple rounded cube
    hull() {
        for (x = [r, size[0]-r])
            for (y = [r, size[1]-r])
                for (z = [r, size[2]-r])
                    translate(center ? [x-size[0]/2, y-size[1]/2, z-size[2]/2] : [x,y,z])
                        sphere(r=r);
    }
}

module fan_mount_holes() {
    for (x = [-1, 1])
        for (y = [-1, 1])
            translate([x*mount_spacing/2, y*mount_spacing/2, 0])
                cylinder(d=mount_hole_d, h=20, center=true);
}

module m2_faceplate_holes(depth=15) {
    for (a = [45, 135, 225, 315]) {
        rotate([0,0,a])
            translate([faceplate_screw_offset, 0, 0])
                if (use_heatset_m2)
                    cylinder(d=m2_insert_d, h=depth);
                else
                    cylinder(d=m2_hole_d, h=depth);
    }
}

// ---------- Main Housing ----------
module housing() {
    difference() {
        // Outer shell
        union() {
            // Main square body
            translate([0,0,outer_depth/2])
                rounded_cube([outer_width, outer_width, outer_depth], r=4, center=true);
            
            // Bottom electronics extension (makes a slightly taller base)
            translate([0, -outer_width/2 + electronics_bay_height/2 - 2, outer_depth/2])
                rounded_cube([outer_width - 4, electronics_bay_height + 4, outer_depth - 2], r=3, center=true);
        }
        
        // Fan cavity (from front)
        translate([0, 0, fan_thickness/2 + 1])
            cube([fan_size + 2*fan_clearance, fan_size + 2*fan_clearance, fan_thickness + 4], center=true);
        
        // Slightly larger rear opening for airflow / cable
        translate([0, 0, outer_depth - 8])
            cube([fan_size - 10, fan_size - 10, 20], center=true);
        
        // Fan mounting holes (M3) – through the rear wall of the fan recess
        translate([0, 0, fan_thickness + 3])
            fan_mount_holes();
        
        // M2 faceplate screw holes / insert pockets (from front face)
        translate([0, 0, -0.1])
            m2_faceplate_holes(depth=8);
        
        // Electronics bay cavity (rear lower section)
        translate([0, -outer_width/2 + electronics_bay_height/2 + 1, outer_depth - bay_depth/2 - 1])
            cube([outer_width - 2*wall_thickness - 2, electronics_bay_height - 2, bay_depth], center=true);
        
        // USB-C cutout (bottom front or side – example on bottom front edge)
        translate([0, -outer_width/2 + 8, 8])
            rotate([90,0,0])
                cube([12, 6, 15], center=true);  // approximate USB-C panel cutout
        
        // Cable path from fan area to electronics bay
        translate([0, -40, fan_thickness + 5])
            cube([12, 30, 10], center=true);
        
        // Optional: hanging handle cutout / lightening
        translate([0, outer_width/2 - 8, outer_depth/2])
            rotate([90,0,0])
                cylinder(d=22, h=20, center=true);
    }
    
    // Internal features: fan seat lip
    difference() {
        translate([0, 0, 1.5])
            cube([fan_size + 6, fan_size + 6, 3], center=true);
        translate([0, 0, 1.5])
            cube([fan_size + 2*fan_clearance, fan_size + 2*fan_clearance, 5], center=true);
        fan_mount_holes();
    }
    
    // Mounting posts or bosses for M3 (optional reinforcement)
    for (x = [-1, 1])
        for (y = [-1, 1])
            translate([x*mount_spacing/2, y*mount_spacing/2, fan_thickness + 1])
                difference() {
                    cylinder(d=8, h=6);
                    cylinder(d=mount_hole_d, h=8);
                }
}

// Render
housing();

// Preview fan (ghost)
%translate([0,0,fan_thickness/2 + 1])
    cube([fan_size, fan_size, fan_thickness], center=true);
