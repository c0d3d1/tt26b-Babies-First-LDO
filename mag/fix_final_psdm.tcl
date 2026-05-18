load bg_core_route_all

# These 8 boxes are local bg_core_route_all coordinates from drc_feol(3).xml.
# They bridge tiny psdm gaps that KLayout sees in GDS.

# top row
box 18.08um 8.70um 18.36um 8.82um
paint psdm

box 24.98um 8.70um 25.36um 8.82um
paint psdm

box 31.98um 8.70um 32.36um 8.82um
paint psdm

box 38.98um 8.70um 39.36um 8.82um
paint psdm

# bottom row
box 24.98um -5.00um 25.36um -4.88um
paint psdm

box 31.98um -5.00um 32.36um -4.88um
paint psdm

box 38.98um -5.00um 39.36um -4.88um
paint psdm

# vertical/side gap
box 45.95um 1.72um 46.08um 2.10um
paint psdm

save

load tt_um_c0d3d1_ldo
writeall force
gds write ../gds/tt_um_c0d3d1_ldo.gds
lef write ../lef/tt_um_c0d3d1_ldo.lef -pinonly

quit -noprompt
