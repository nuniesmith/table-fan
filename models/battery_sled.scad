// Printed 4x1 18650 sled for the table fan
// Holds 4x 18650 cells inline for a 4S pack. Cells are wired in series with
// short jumpers (alternate cell direction); balance taps go to the 4S BMS.
// Secure cells with a wrap of Kapton tape once wired.
// Units: mm
//
// Placement in fan_housing.scad: bay floor, centered at (0, -66, 37)
// (X centered, Y on the floor, Z centered in the bay).

cell_d = 18.4;          // 18650 + clearance
cell_len = 65.4;
n_cells = 4;
rib_t = 2.5;
end_t = 2.5;
base_t = 3;
wall_h = 14;            // rib/end-wall height above the base
sled_w = 24;            // Z width

inner_len = n_cells*cell_d + (n_cells-1)*rib_t;   // 81.1
total_len = inner_len + 2*end_t;                  // ~86

$fn = 48;

module sled() {
    // base
    translate([-total_len/2, -sled_w/2, 0])
        cube([total_len, sled_w, base_t]);

    // divider ribs between cells
    for (i = [0 : n_cells-2]) {
        x = -inner_len/2 + cell_d + rib_t/2 + i*(cell_d + rib_t);
        translate([x - rib_t/2, -sled_w/2, base_t])
            cube([rib_t, sled_w, wall_h]);
    }

    // end walls (low so series jumper wires pass over the top)
    for (s = [-1, 1])
        translate([s*(total_len/2 - end_t), -sled_w/2, base_t])
            cube([end_t, sled_w, wall_h]);

    // side lips to keep cells from walking out sideways
    for (s = [-1, 1])
        translate([-inner_len/2, s*(sled_w/2 - 1.5), base_t])
            cube([inner_len, 1.5, 6]);

    // mounting ears with 3.2mm holes (optional: tape also works)
    for (s = [-1, 1])
        difference() {
            translate([s*(total_len/2) - (s > 0 ? 0 : 14), -sled_w/2, 0])
                cube([14, sled_w, base_t]);
            translate([s*(total_len/2 + 7), 0, -0.1])
                cylinder(d=3.2, h=base_t + 0.2);
        }
}

sled();

// ghost cells for fit check
%for (i = [0 : n_cells-1]) {
    x = -inner_len/2 + cell_d/2 + i*(cell_d + rib_t);
    translate([x, 0, base_t + cell_d/2])
        rotate([0, 90, 0]) cylinder(d=18, h=65, center=true);
}
