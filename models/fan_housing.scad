// Portable 120mm Noctua Fan Housing
// Compatible with NF-F12 industrialPPC-3000 PWM (120x120x25 mm)
// Mounting hole spacing: 105 mm center-to-center
// Designed for removable M2 faceplate (screws + nuts) and internal 4-pin connector
// Units: millimeters
// Author: Grok design for nuniesmith/table-fan, reworked Oct 2026
//
// LAYOUT (two level):
//   Bay floor : printed 4x1 18650 sled (models/battery_sled.scad) at X -53..33
//   Mezzanine : 4S BMS (X -60..-15) + 4S charger module (X -12..28)
//               + RP2040-Zero carrier board (X 32..62, USB-C faces rear)
//   Under mezzanine (right of sled): 2x MP1584 mini bucks (12V fan, 5V MCU)
//   Rear cover: screwed plate + OLED pod (0.96" SSD1306)  + Zero USB-C cutout
//               with strain-relief collar
//   +X wall   : 16mm dial pot with on/off click (speed + hard power, one knob)
//   -X wall   : USB-C charge port cutout

/* [Main Dimensions] */
outer_width = 140;          // body width/height
outer_depth = 62;           // front-to-back depth
wall_thickness = 2.5;
fan_size = 120;
fan_thickness = 25;
fan_clearance = 0.4;        // radial clearance around fan
mount_spacing = 105;        // standard 120mm fan hole spacing
mount_hole_d = 3.4;         // M3 clearance

/* [Faceplate Mounting] */
// 4x M2 screw + nut at the cardinal points, in solid plastic outside the fan
// cavity. MUST match faceplate.scad (offset + angles).
faceplate_screw_offset = 66;
m2_clearance_d = 2.4;
m2_nut_pocket_d = 5.0;      // hex across corners (M2 nut ~4.6)
m2_nut_pocket_depth = 2.8;

/* [Electronics Bay] */
electronics_bay_height = 54;   // taller base: sled + mezzanine + modules
bay_depth = 38;
bay_inner_w = outer_width - 2*wall_thickness - 11;  // 129 -> +/-64.5
mezzanine_thickness = 2.5;
mezzanine_y0 = -40;            // bottom face of mezzanine plate

/* [Dial Switch] */
// 16mm pot with rotary on/off switch, side-mounted on the +X base wall.
// Full CCW clicks OFF (hard power cut); CW sweeps slowest -> fastest.
pot_y = -54;
pot_z = 30;
pot_hole_d = 7.5;           // 6-7mm threaded bushing + clearance
knob_recess_d = 20;
knob_recess_depth = 2.5;

/* [Rear Cover + OLED pod] */
cover_t = 3;
// 0.96" SSD1306 OLED (128x64, I2C, ~27x27mm PCB) lives in a small bump-out
// pod on the cover, rear-facing. PCB corner holes ~23mm apart - verify
// against the real module before printing. Modules ship with GND/VCC pin
// order random - check the silkscreen on arrival.
oled_ox0 = -38; oled_ow = 40;   // X -38..2
oled_oy0 = -50; oled_oh = 32;   // Y -50..-18
oled_od = 12;                   // Z 65..77
// Cover screw positions (must match corner blocks below).
// Top-left kept at x=-66 (was moved to clear the old 1602 pod).
cover_screws = [[-66,-20],[60,-20],[-60,-62],[60,-62]];

/* [U-Bail Bracket] */
// Side-pivot U-bail (models/bail.scad): hangs (~100 deg, pin out) or props
// (~30 deg, stop pin in). Folds flat against the side walls; bar nests in a
// groove under the base. Pivot at (Y=0, Z=50) clears the dial (Z=30) and USB-C.
bail_pivot_y = 0; bail_pivot_z = 50;
bail_arm_w = 8;    // arm width (Z)
bail_arm_t = 5;    // arm thickness (X)
bail_arm_l = 71;   // pivot center to bar center
// Raised ribs on ±X walls (X 70..74, Z 43..59, Y -68..+10); 9mm channels
// hold the 8mm arms flush, 7mm pockets hold the pivot discs.
// USB-C charge port (left/+X wall, dial side) - moved from -X
usb_y = -25; usb_z = 30;
// Prop stop pin hole (M3 clearance, removable pin): pin IN = ~30 deg prop,
// pin OUT = free swing past 100 deg for hanging. Position tuned by eye.
stop_y = -12; stop_z = 60;

/* [Render] */
part = "housing";  // [housing, cover]

$fn = 64;

// ---------- Helper modules ----------
module rounded_cube(size, r=3, center=false) {
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

// M2 nut pockets (front face) + clearance holes, cardinal points
module faceplate_holes() {
    for (a = [0, 90, 180, 270])
        rotate([0,0,a])
            translate([faceplate_screw_offset, 0, 0]) {
                translate([0,0,-0.1])
                    cylinder(d=m2_nut_pocket_d, h=m2_nut_pocket_depth+0.1, $fn=6);
                translate([0,0,-0.1])
                    cylinder(d=m2_clearance_d, h=14);
            }
}

// ---------- Main Housing ----------
module housing() {
    difference() {
        union() {
            // Main square body
            translate([0,0,outer_depth/2])
                rounded_cube([outer_width, outer_width, outer_depth], r=4, center=true);

            // Bottom electronics base (taller: sled + mezzanine)
            translate([0, -outer_width/2 + electronics_bay_height/2 - 2, outer_depth/2])
                rounded_cube([outer_width - 4, electronics_bay_height + 4, outer_depth - 2], r=3, center=true);

            // Bail ribs (both side walls) - raised rails; arms nest into the
            // channels so the folded bail sits flush with the rib tops.
            // (0.2mm embedded into the wall for a clean union.)
            for (sx = [1, -1])
                translate([sx > 0 ? sx*outer_width/2 - 0.2 : sx*outer_width/2 - 4, -68, 43])
                    cube([4.2, 78, 16]);
        }

        // Fan cavity (from front)
        translate([0, 0, fan_thickness/2 + 1])
            cube([fan_size + 2*fan_clearance, fan_size + 2*fan_clearance, fan_thickness + 4], center=true);

        // Slightly larger rear opening for airflow
        translate([0, 0, outer_depth - 8])
            cube([fan_size - 10, fan_size - 10, 20], center=true);

        // Fan mounting holes (M3) - through the rear wall of the fan recess
        translate([0, 0, fan_thickness + 3])
            fan_mount_holes();

        // Faceplate M2 nut pockets + clearance (front face)
        faceplate_holes();

        // Electronics bay cavity - OPEN at the rear (serviced via bay cover)
        translate([0, -outer_width/2 + electronics_bay_height/2 + 1, outer_depth - bay_depth/2 - 0.5])
            cube([bay_inner_w, electronics_bay_height, bay_depth + 2], center=true);

        // Dial pot: hole through +X base wall + knob recess on the outer face
        translate([outer_width/2 - 7, pot_y, pot_z])
            rotate([0,90,0]) cylinder(d=pot_hole_d, h=10);
        translate([outer_width/2 - 4.5, pot_y, pot_z])
            rotate([0,90,0]) cylinder(d=knob_recess_d, h=knob_recess_depth);

        // USB-C charge port cutout on the +X wall (left side, dial side)
        // Socket glues in from outside; pigtail wires reach the bay interior.
        // Verify the opening against the real socket before printing.
        translate([outer_width/2 - 4, usb_y - 6.5, usb_z - 5])
            cube([8, 13, 10]);

        // Screen button hole (+X wall, near dial) - 6x6mm tactile switch,
        // glues in from outside. Wired to GP11 + GND (firmware: toggles OLED).
        translate([outer_width/2 - 4, -41.5, 8.5])
            cube([8, 7, 7]);

        // Bail arm channels (both walls) - 9mm wide for 8mm arms (0.5/side play)
        translate([outer_width/2 - 2, -68, 45.5]) cube([6, 74, 9]);
        translate([-outer_width/2 - 4, -68, 45.5]) cube([6, 74, 9]);
        // Pivot pockets (arm disc ends rotate here)
        translate([outer_width/2 - 2, bail_pivot_y, bail_pivot_z])
            rotate([0,90,0]) cylinder(r=7, h=6);
        translate([-outer_width/2 - 4, bail_pivot_y, bail_pivot_z])
            rotate([0,90,0]) cylinder(r=7, h=6);
        // M4 heat-set insert pilots (8mm deep from channel floor)
        translate([outer_width/2 - 10, bail_pivot_y, bail_pivot_z])
            rotate([0,90,0]) cylinder(d=6, h=8.2);
        translate([-outer_width/2 + 2, bail_pivot_y, bail_pivot_z])
            rotate([0,90,0]) cylinder(d=6, h=8.2);

        // Prop stop pin holes (M3 clearance, both walls) - removable pin
        for (sx = [1, -1])
            translate([sx*(outer_width/2 - 10), stop_y, stop_z])
                rotate([0, sx*90, 0])
                    cylinder(d=3.2, h=10);

        // Bail bar groove under the base (bar nests here when folded)
        translate([-80, -outer_width/2 - 4, bail_pivot_z - 4])
            cube([160, 6, 8]);

        // Cable path from fan area up over the mezzanine into the bay
        translate([0, -40, fan_thickness + 5])
            cube([12, 30, 10], center=true);

        // Hanging handle cutout
        translate([0, outer_width/2 - 8, outer_depth/2])
            rotate([90,0,0])
                cylinder(d=22, h=20, center=true);
    }

    // Fan seat lip
    difference() {
        translate([0, 0, 1.5])
            cube([fan_size + 6, fan_size + 6, 3], center=true);
        translate([0, 0, 1.5])
            cube([fan_size + 2*fan_clearance, fan_size + 2*fan_clearance, 5], center=true);
    }

    // Top fan mount posts (solid plastic here)
    for (x = [-1, 1])
        translate([x*mount_spacing/2, mount_spacing/2, fan_thickness + 1])
            difference() {
                cylinder(d=8, h=6);
                cylinder(d=mount_hole_d, h=8);
            }

    // Bottom fan mount pillars: solid ribs in the bay carrying the lower
    // fan screws (the bay void removed the original posts here)
    for (x = [-1, 1])
        difference() {
            translate([x*mount_spacing/2 - 5.5, -69, 26]) cube([11, 22, 10]);
            translate([x*mount_spacing/2, -52.5, 25]) cylinder(d=mount_hole_d, h=12);
        }

    // Mezzanine plate (BMS + charger + Zero carrier live on top)
    difference() {
        translate([-62, mezzanine_y0, 25]) cube([124, mezzanine_thickness, 34]);
        // cable notch: fan wires come up through here
        translate([-7, mezzanine_y0 - 0.1, 24]) cube([14, mezzanine_thickness + 0.2, 12]);
    }

    // Mezzanine standoffs (M3) from the bay floor.
    // Positions dodge the sled (X -53..33, Z 25..49), pillars and dial pot.
    for (p = [[38,44],[38,56],[-58,44],[-20,56]])
        difference() {
            translate([p[0] - 3.5, -68, p[1] - 3.5]) cube([7, 28, 7]);
            translate([p[0], -69, p[1]]) rotate([90,0,0]) cylinder(d=3.2, h=30);
        }

    // Zero carrier bosses (4x M2) on the mezzanine.
    // Carrier: 30x25 perfboard at X 32..62, Z 34..59; Zero USB-C faces the rear.
    for (cx = [34, 60]) for (cz = [36, 57])
        difference() {
            translate([cx - 2.25, mezzanine_y0 + mezzanine_thickness, cz - 2.25])
                cube([4.5, 6, 4.5]);
            translate([cx, mezzanine_y0 + mezzanine_thickness - 0.5, cz])
                cylinder(d=1.8, h=8);
        }

    // Rear cover corner blocks with M3 heat-set insert holes (cover screws)
    for (p = cover_screws)
        difference() {
            translate([p[0] > 0 ? 53 : -67, p[1] > -40 ? -26 : -68, 52])
                cube([14, 12, 10]);
            translate([p[0], p[1], 51.9])
                cylinder(d=4.2, h=10.2);
        }
}

// Strain-relief collar for the Zero's USB-C (on the bay cover, outer face)
module usb_collar() {
    difference() {
        translate([38, -37, outer_depth + cover_t]) cube([18, 14, 8]);
        translate([41, -34, outer_depth + cover_t - 0.1]) cube([12, 8, 8.2]);
    }
}

// OLED pod: small bump-out on the bay cover housing a 0.96" SSD1306 OLED
// (128x64, I2C, ~27x27mm PCB). The module drops in from the bay side before
// the cover is screwed on; its screen shows through the rear window.
// Screws go in from outside: rear-wall clearance holes -> PCB holes ->
// standoff post pilots.
module oled_pod() {
    difference() {
        // outer shell
        translate([oled_ox0, oled_oy0, outer_depth + cover_t])
            cube([oled_ow, oled_oh, oled_od]);
        // hollow interior (breaks through the cover plate for the wires)
        translate([oled_ox0 + 2, oled_oy0 + 2, outer_depth + cover_t - 1])
            cube([oled_ow - 4, oled_oh - 4, oled_od - 3]);
        // screen window in the rear wall (wall: Z 73..77)
        translate([oled_ox0 + 7, oled_oy0 + 9.5, outer_depth + cover_t + oled_od - 4.1])
            cube([oled_ow - 14, 13, 4.2]);
        // 4x M2 clearance holes through the rear wall (PCB corner holes, ~23mm apart)
        for (hx = [oled_ox0 + 8.5, oled_ox0 + oled_ow - 8.5])
            for (hy = [oled_oy0 + 4.5, oled_oy0 + oled_oh - 4.5])
                translate([hx, hy, outer_depth + cover_t + oled_od - 4.1])
                    cylinder(d=2.4, h=4.2);
    }
    // standoff posts the OLED PCB screws to (M2 self-tap pilots)
    for (hx = [oled_ox0 + 8.5, oled_ox0 + oled_ow - 8.5])
        for (hy = [oled_oy0 + 4.5, oled_oy0 + oled_oh - 4.5])
            difference() {
                translate([hx - 2.5, hy - 2.5, outer_depth + cover_t])
                    cube([5, 5, 8]);
                translate([hx, hy, outer_depth + cover_t - 0.1])
                    cylinder(d=1.8, h=8.2);
            }
}

// ---------- Rear Bay Cover (separate printed part) ----------
module bay_cover() {
    difference() {
        // plate overlaps the opening onto the housing face
        translate([-68.5, -70, outer_depth]) cube([137, 58, cover_t]);
        // 4x M3 clearance for the corner-block screws
        // (top-left kept at x=-66, clears the OLED pod)
        for (p = cover_screws)
            translate([p[0], p[1], outer_depth - 0.1])
                cylinder(d=3.4, h=cover_t + 0.2);
        // Zero USB-C (programming port) cutout - aligns with carrier at X~47
        translate([41, -34, outer_depth - 0.1]) cube([12, 8, cover_t + 0.2]);
        // OLED pass-through (the pod sits over this opening)
        translate([oled_ox0 + 2, oled_oy0 + 2, outer_depth - 0.1])
            cube([oled_ow - 4, oled_oh - 4, cover_t + 0.2]);
    }
    usb_collar();
    oled_pod();
}

// ---------- Render ----------
if (part == "housing") {
    housing();
    // ghost previews
    %translate([0,0,fan_thickness/2 + 1])
        cube([fan_size, fan_size, fan_thickness], center=true);
    %translate([-10, -66, 37])  // battery sled envelope (see models/battery_sled.scad)
        cube([86, 22, 24], center=true);
} else if (part == "cover") {
    bay_cover();
} else {
    housing();
    translate([0, 0, 90]) bay_cover();
}
