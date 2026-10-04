ROBOMONA V5 - SOFTER CAT EARS
==================================
04 October 2026 | Units: millimetres | Nominal overall: 140 x 112 x 187

This revision changes the actual printable geometry to follow your supplied
image more closely. The preview is rendered from the STL geometry, not a
separately generated concept. It is a close interpretation, not an exact
image-to-3D reconstruction; the hidden shape and dimensions are not fully
specified by the reference.

VISIBLE CHANGES FROM V4
- Softer cat ears with broad curved sides and 4.5 mm rounded tip radius.
- Shallow front-facing inner-ear bowls give the ears a natural cupped form.
- Ear tips lowered by 3 mm: overall height approximately 187 mm.
- The 140 mm head shell, shorter neck, TFT opening and octopus body retain V4 dimensions.
- Only the front and rear head shells change; existing V4 other parts can be reused.

START HERE
1. renders/model-preview.png shows the actual complete printed geometry.
2. renders/body-detail.png, when included, shows the revised body close up.
3. reference/target-body.png is your unchanged supplied visual reference.
4. stl/ contains the nine separate print parts. Print one of each.
5. cad/generate_model.py and cad/organic_body.py are the editable CAD source.
6. cad/validation.json records the geometry checks and component envelopes.

IMPORTANT MECHANICAL CHANGE
The MG996R retains the V3 lower location, crossing the base and lower torso. Its long body
axis runs front-to-back, with its output shaft vertical. This frees the narrow
upper torso. A NEW hollow printed drive extension connects the OEM servo horn
to the head. The original V2 servo placement, short horn adapter and some
mounting positions no longer apply. Use both V5 head halves together. The seven other parts are unchanged from V4;
do not use older V3 head, body guide or drive parts.

The new mechanism is a fit-check proposal. Verify the actual servo flange,
shaft height, OEM horn shape, screw access, extension rigidity and neck-guide
clearance before powered operation. There is no validated ball-bearing joint.
The guide clearance is a printed sliding fit that must be tuned to your printer.
The rotating extension has a side entry and central passage for the head wiring;
leave a loose service loop and check it at every intended angle.

PRINT PARTS
01_base_tub.stl                   Base shell and integral low servo cradle
02_base_bottom_cover.stl          Service cover with adjustable tie slots
03_reference_body_six_tentacles.stl  Sculpted torso, six tentacles and suction pads
04_servo_clamp_1.stl              First flange clamp
04_servo_clamp_2.stl              Second flange clamp
05_head_front.stl                Curved face shell, rim, whiskers and ear fronts
06_head_rear.stl                 Rear shell, speaker grille and rear screw access
07_display_retainer.stl          Insulated TFT retention bar
08_hollow_neck_drive.stl          New hollow neck extension and horn interface

The individual STLs are grounded at Z=0 in suggested orientations. Check every
part in your slicer. Curved head shells, raised tentacles, the base roof and
servo supports need support planning. A brim may help small initial contacts.
Use 0.4 mm nozzle / 0.20 mm layers / 4 perimeters as initial FDM settings, then
tune for your machine. The drive extension needs particular strength review;
avoid assuming a watertight mesh implies adequate resistance to servo torque.

Assembled-position meshes and assembly_for_visualization_NOT_FOR_PRINT.stl are
inspection files, not single-piece prints. Print only the files in stl/.

FASTENERS AND ASSEMBLY
M3 holes are nominal 3.2 mm clearance or 2.5 mm pilot. Actual drill sizing and
screw lengths depend on print accuracy and the measured stack. Use the actual
MG996R horn rather than a printed spline. Match-drill the lower extension flange
to that horn. Center the servo before securing it to the mechanism.

The head has a 7 mm mounting pad. Its two screws straddle the shell seam, so use
washers spanning both halves. Measure engagement into the 4 mm top plate of the
drive extension and avoid screw tips projecting into the mechanism. Select the
head-shell screws from actual boss lengths; those are accessed from the rear.

Check servo clamping and all screw access on small trial prints before a complete
print. Retain PCB modules using insulated spacers, straps or ties. Secure the
LiPo pouch gently, with no screw tips or sharp printed edges against it.

PROVISIONAL HARDWARE ENVELOPES (XYZ, assembly coordinates)
Servo body: 22 x 43 x 46; center (0, 10.35, 33). Flange/horn verified separately.
TFT: 60 x 12 x 38; center (0, -27, 129), example PCB 56.5 x 34.
Speaker: 36 x 18 x 36; center (0, 26, 131).
LiPo: 37 x 66 x 12; center (-42, 0, 9), assumed pouch 35 x 60 x 8.
ESP32-C3: 27 x 23 x 12; center (40, -25, 9).
Audio amplifier: 24 x 23 x 12; center (42, 0, 9).
Servo power converter: 40 x 25 x 15; center (34, 24, 10.5).
TP4056: 32 x 20 x 10; center (-6, 43, 8).

These are reservations, not guaranteed dimensions of your products. Inspect
actual connector exits, buttons, USB alignment and wire bend radii. The base
uses generic ties rather than assumed PCB mounting-hole patterns. The TFT's
actual illuminated area remains roughly 35 x 28 mm; the image's face cannot be
copied at its exaggerated apparent size while retaining that 1.8-inch display.

POWER AND MOTION
Use a suitable regulated servo supply; a 1S LiPo cannot directly supply the
MG996R's required 4.8-6.6 V. Keep signal grounds common. The ESP32 board must not
be used as the servo-current source. Select battery, protection and converter
current capabilities for the actual actuator and load.

TP4056 alone is not a complete load-sharing controller. Default: robot load OFF
while charging. Set charging current to match the battery. A running-while-
charging design needs an appropriate power-path circuit.

The intended +/-30 degree head motion is not physically verified. Start at
small angles and test wire slack, binding, head sag, extension flex and heating.
All six tentacles are fixed; moving them would need additional actuators.

REGENERATE
python3 -m pip install -r cad/requirements.txt
python3 cad/generate_model.py
python3 cad/verify_print_kit.py
python3 cad/render_model.py .

The generator overwrites this revision's generated files. Body profiles and
tentacle paths are defined in organic_body.py; shell and mechanism details
are in generate_model.py. parameters.json holds general dimensions. Changing
one parameter does not automatically redesign every fixed mounting coordinate.
Re-run geometry checks after changes. The optional .cache folder can be deleted;
it stores an intermediate sculpt and is rebuilt when the sculpt source changes.

VALIDATION LIMITS
Each part is checked for closed surface, consistent winding, one connected
component and positive volume. Printed-part intersections and reserved hardware
boxes are checked, and head clearance is sampled at 5-degree increments from
-30 to +30. Actual purchased parts, connectors, fasteners, wiring, printer
behavior, load strength, charging and physical assembly are not verified.
