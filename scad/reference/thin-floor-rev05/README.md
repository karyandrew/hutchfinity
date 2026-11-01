---
sensitivity: public
version: 1.0.0
---

# Thin-floor revision 05 reference

Preserved source for the design ported to `scad/tub.scad` and `scad/hutchfinity.scad`. These files are not used by the build.

- `model.py`: the CadQuery model, at Regular size with the old 2.01 mm stack clearance and a 3.74 mm stack term. The current contract replaces those two values with a 0.50 mm air gap and the measured 4.30 mm overlap.
- `accessories.scad`: the casing, peg, and pull caller for the printed 45.79 mm tub. It expects a newer `casing.scad` than the one in this repository.

With those two values applied, the port matches this model within 0.05% of volume at 10 x 10 x 10h and 12 x 16 x 20h, and for the plain tub and grid insert at 10 x 10.
