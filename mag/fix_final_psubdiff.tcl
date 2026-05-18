load bg_core_route_all

# KLayout calls this layer psdm.
# Magic calls the corresponding p+ diffusion/tap layer psubdiff/psd/ppd.
# Use psubdiff here.

# top row
box 18.08um 8.70um 18.36um 8.82um
paint psubdiff

box 24.98um 8.70um 25.36um 8.82um
paint psubdiff

box 31.98um 8.70um 32.36um 8.82um
paint psubdiff

box 38.98um 8.70um 39.36um 8.82um
paint psubdiff

# bottom row
box 24.98um -5.00um 25.36um -4.88um
paint psubdiff

box 31.98um -5.00um 32.36um -4.88um
paint psubdiff

box 38.98um -5.00um 39.36um -4.88um
paint psubdiff

# vertical/side gap
box 45.95um 1.72um 46.08um 2.10um
paint psubdiff

save bg_core_route_all

load tt_um_c0d3d1_ldo
save tt_um_c0d3d1_ldo

gds write ../gds/tt_um_c0d3d1_ldo.gds
lef write ../lef/tt_um_c0d3d1_ldo.lef -pinonly

quit -noprompt
