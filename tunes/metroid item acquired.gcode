M302 P1; allow cold extrusion
M83; relative extruder moves
G92 E0; reset E axis/axes
G1 F60000000 X0 Y0 Z100; center axis/axes
G4 S1; pause for a second
G1 F227.02265 X0.38766 Y1.16167 Z100.29042 E-0.16632
G1 F87.37021 X0.38847 Y1.16167 Z100.29102 E-0.00035
G1 F293.02674 X0.77613 Y-0.38897 Z100.58144 E-0.16632
G1 F87.37021 X0.77694 Y-0.38897 Z100.58205 E-0.00035
G1 F325.88124 X1.1646 Y1.35156 Z100.87246 E-0.16632
G1 F87.37021 X1.16541 Y1.35156 Z100.87307 E-0.00035
G1 F363.06708 X1.55307 Y-0.60212 Z101.16349 E-0.16632
G1 F30.0 X1.55307 Y-0.60212 Z101.16349 E-0.00035
G1 F404.0581 X1.17015 Y1.69281 Z100.87662 E-0.17406
G1 F82.46649 X1.16935 Y1.69281 Z100.87602 E-0.00036
G1 F324.60091 X0.78643 Y-0.12868 Z100.58915 E-0.17406
G1 F82.46649 X0.78563 Y-0.12868 Z100.58856 E-0.00036
G1 F249.23578 X0.40271 Y1.2359 Z100.30169 E-0.17406
G1 F82.46649 X0.40191 Y1.2359 Z100.30109 E-0.00036
G1 F324.60091 X0.01898 Y-0.58559 Z100.01422 E-0.17406
G1 F30.0 X0.01898 Y-0.58559 Z100.01422 E-0.00036
G1 F425.46522 X0.37677 Y1.96441 Z100.28226 E-0.18255
G1 F73.46929 X0.37752 Y1.96441 Z100.28282 E-0.00038
G1 F359.97485 X0.7353 Y-0.17988 Z100.55086 E-0.18255
G1 F73.46929 X0.73605 Y-0.17988 Z100.55141 E-0.00038
G1 F289.18653 X1.14353 Y1.75843 Z100.85668 E-0.2079
G1 F73.46929 X1.14438 Y1.75843 Z100.85732 E-0.00043
G1 F246.40513 X1.58227 Y0.00688 Z101.18536 E-0.22341
G1 F30.0 X1.58227 Y0.00688 Z101.18536 E-0.00047
G1 F271.25035 X0.16205 Y8.51857 Z99.76514 E-0.96724
G1 F30.0 X0.16205 Y8.51857 Z99.76514 E-0.0
M302 P0; disallow cold extrusion
G4 S1; pause for a second