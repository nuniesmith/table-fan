// Battery sled for the table fan: 4x 18650 side by side, axes front to back
// (4S1P). It sits on the bottom plate in the base, under the fan, and its
// lid carries the 4S BMS.
//   - Two M2 screws up through the bottom plate hold the sled down; four M2
//     screws hold the lid on, so the cells are boxed in (tape alone won't
//     hold 190 g of cells in a truck).
//   - Cells alternate direction. Series straps run across the cell ends at
//     the front and back; leads leave through the notches in the end walls.
//   - Use tabbed cells or spot-welded nickel strip: never solder to a cell.
// Units: mm. Print the sled base down and the lid flat; no supports.
//
// Local coordinates: X across (cell 1 at the X 0 side), Y up from the sled's
// underside, Z front to back. fan_housing.scad places it at
// (sled_x0, base_floor, sled_z0).

/* [Cells] */
cell_d = 18.4;          // max cell diameter (Samsung 35E)
cell_len = 65.3;        // max cell length
cell_gap = 0.4;         // diametral clearance
strap_room = 1.7;       // nickel strips + slack, both ends together
n_cells = 4;

/* [Sled] */
rib_t = 1.6;
side_t = 2;
end_t = 5;              // thick enough for the lid and plate screws
sled_base_t = 1.5;
lid_t = 1.5;
notch_w = 5;            // lead notches in the end walls
notch_h = 6;
m2_pilot_d = 1.7;       // M2 self-tapping
m2_clear_d = 2.4;
strap_relief = 3;       // ribs stop this far short of the cell ends, for the straps

/* [Render] */
sled_part = "sled";     // [sled, lid, print_sled, print_lid]

pocket_d = cell_d + cell_gap;                               // 18.8
pocket_l = cell_len + strap_room;                           // 67
sled_w = n_cells*pocket_d + (n_cells - 1)*rib_t + 2*side_t; // 84
sled_l = pocket_l + 2*end_t;                                // 77
sled_h = sled_base_t + pocket_d;                            // 20.3: walls reach the cells' tops

function cell_x(i) = side_t + pocket_d/2 + i*(pocket_d + rib_t);
function rib_x(i) = cell_x(i) + pocket_d/2 + rib_t/2;
cell_y = sled_base_t + pocket_d/2;

lid_screw_x = [4, sled_w - 4];          // in both end walls, clear of the notches
plate_screw_x = cell_x(1);              // one per end wall, from below
notch_x = [cell_x(0), rib_x(0), rib_x(1), rib_x(2), cell_x(n_cells - 1)];

$fn = 48;

module sled() {
    difference() {
        cube([sled_w, sled_h, sled_l]);
        // cell pockets, open at the top
        for (i = [0 : n_cells - 1])
            translate([cell_x(i) - pocket_d/2, sled_base_t, end_t])
                cube([pocket_d, sled_h, pocket_l]);
        // ribs stop short of the cell ends so the straps can cross them
        for (i = [0 : n_cells - 2])
            for (z = [end_t - 0.1, sled_l - end_t - strap_relief])
                translate([rib_x(i) - rib_t/2 - 0.1, sled_base_t, z])
                    cube([rib_t + 0.2, sled_h, strap_relief + 0.1]);
        // lead notches in both end walls
        for (x = notch_x)
            for (z = [-0.1, sled_l - end_t - 0.1])
                translate([x - notch_w/2, sled_h - notch_h, z])
                    cube([notch_w, notch_h + 0.1, end_t + 0.2]);
        // lid screw pilots (from the top)
        for (x = lid_screw_x)
            for (z = [end_t/2, sled_l - end_t/2])
                translate([x, sled_h - 9, z]) rotate([-90, 0, 0])
                    cylinder(d=m2_pilot_d, h=9.1);
        // plate screw pilots (from below)
        for (z = [end_t/2, sled_l - end_t/2])
            translate([plate_screw_x, -0.1, z]) rotate([-90, 0, 0])
                cylinder(d=m2_pilot_d, h=9);
    }
}

// Lid, in place on top of the sled (Y sled_h .. sled_h + lid_t)
module sled_lid() {
    difference() {
        translate([0, sled_h, 0]) cube([sled_w, lid_t, sled_l]);
        for (x = lid_screw_x)
            for (z = [end_t/2, sled_l - end_t/2])
                translate([x, sled_h - 1, z]) rotate([-90, 0, 0])
                    cylinder(d=m2_clear_d, h=lid_t + 2);
    }
}

module cells() {
    for (i = [0 : n_cells - 1])
        translate([cell_x(i), cell_y, end_t + strap_room/2])
            cylinder(d=cell_d, h=cell_len);
}

// ---------- Render ----------
if (sled_part == "sled") {
    sled();
    %cells();
} else if (sled_part == "lid") {
    sled_lid();
} else if (sled_part == "print_sled") {
    rotate([90, 0, 0]) sled();              // base on the bed
} else if (sled_part == "print_lid") {
    rotate([90, 0, 0]) translate([0, -sled_h, 0]) sled_lid();
}
