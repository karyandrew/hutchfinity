// Physical-trial accessories for the printed 45.79 mm tub, not a nominal-height rebuild.
use <upstream/casing.scad>;
use <upstream/peg.scad>;
use <upstream/knob.scad>;
$fn=64;
PART="casing";
TUB_X=214.4;
TUB_Y=214.4; // body only; guide projects 0.6 mm out of the open front
TUB_Z=45.79;
SIDE_CLEARANCE=1;
BACK_CLEARANCE=0.5;
TOP_CLEARANCE=1;
SIDE_WALL=18;
BACK_WALL=18;
RIDING_SLAB=1.3;
SLOT_X=TUB_X+2*SIDE_CLEARANCE;
SLOT_Y=TUB_Y+BACK_CLEARANCE;
SLOT_Z=TUB_Z+TOP_CLEARANCE;
OUTER_X=SLOT_X+2*SIDE_WALL;
OUTER_Y=SLOT_Y+BACK_WALL;
MODULE_Z=SLOT_Z+RIDING_SLAB;
PEG_SPACING=190;
PEG_BORE=8.45;
PEG_DEPTH=10;
PEG_CHAMFER=0.5;
PEG_EDGE_LAND=1.2;
PEG_PTP=8.45;
PEG_LENGTH=19.6;
PEG_END_CHAMFER=2.5;
PEG_END_INSET=peg_socket_end_inset(SIDE_WALL,BACK_WALL,8,0.45,PEG_CHAMFER,PEG_EDGE_LAND);
PEG_POSITIONS=peg_reference_positions(OUTER_X,OUTER_Y,SIDE_WALL,BACK_WALL,PEG_SPACING,PEG_END_INSET);
assert(len(PEG_POSITIONS)==7);
assert(2*PEG_DEPTH<MODULE_Z);
assert(PEG_LENGTH<2*PEG_DEPTH);
assert((SIDE_WALL-PEG_BORE-2*PEG_CHAMFER)/2>=4);
module casing() {
    // Existing shell and cutters; bypass no checks. Socket depths are explicitly
    // validated against the wall height, not the unrelated center slab thickness.
    difference() {
        casing_shell(OUTER_X,OUTER_Y,MODULE_Z,SIDE_WALL,BACK_WALL,RIDING_SLAB);
        chamfered_peg_socket_cuts(PEG_POSITIONS,PEG_BORE,PEG_DEPTH,PEG_CHAMFER);
        chamfered_peg_foot_socket_cuts(PEG_POSITIONS,PEG_BORE,PEG_DEPTH,PEG_CHAMFER,MODULE_Z);
    }
}
module pegs() {
    for(i=[0:6]) translate([(i%4)*26,PEG_PTP/2+floor(i/4)*14,0])
        hutchfinity_peg_print_layout(diameter=PEG_PTP,length=PEG_LENGTH,end_chamfer=PEG_END_CHAMFER);
}
if(PART=="casing") casing();
else if(PART=="pegs") pegs();
else if(PART=="handle") hutchfinity_knob(base_depth=34,end_bulge_depth=30);
else assert(false,"Unknown part");
