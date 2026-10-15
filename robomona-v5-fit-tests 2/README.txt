ROBOMONA V5 - COMPONENT FIT-TEST KIT
15 October 2026 | All dimensions in millimetres

PURPOSE
Nine small printable gauges use the component envelopes already reserved in
RoboMona V5. No purchased component measurements have been assumed verified.
These rings check an outline in one plane. They are NOT actual mounting
brackets, complete cavities, or proof that a component can be installed.
The current robot model has not been changed.

PRINT AND TEST
1. Print the relevant STL flat, at 100% scale, in millimetres. Each gauge is
   3 mm tall. Use the same material, nozzle and dimensional compensation you
   intend for the robot. No supports are required. Keep any brim out of the hole.
2. Remove stringing and brim. Measure the printed opening with calipers before
   testing. Record its actual dimensions: print shrinkage or first-layer flare
   can make it smaller than the nominal CAD size. Do not resize the whole robot
   to correct a component fit problem.
3. Label each ring using its filename. Compare the appropriate component outline
   with the opening, gently and without force. Check protruding pins/connectors
   separately. A reserved envelope may be deliberately larger than the component;
   passing the gauge does not mean the part will be held securely.
4. Measure the remaining dimension separately, including solder joints, insulation
   and connectors. Use fit-results.csv to record measurements and observations.
5. Check mounting-hole positions, retaining hardware and cable bend space before
   printing the corresponding full shell. Those details are not tested by rings.

GAUGES                          OPENING         OTHER RESERVED DIMENSION
01 MG996R main body              22 x 43         46 height
02 TFT board envelope           60 x 38         12 depth
03 Speaker envelope             36 x 36         18 depth
04 LiPo envelope                37 x 66         12 thickness
05 ESP32-C3 Super Mini envelope  27 x 23         12 height
06 TP4056 envelope              32 x 20         10 height
07 Audio amplifier envelope     24 x 23         12 height
08 Servo power converter        40 x 25         15 height
09 Panel button                 diameter 12.2   panel coupon thickness 3

The amplifier and servo power converter are included because V5 reserves space
for them. Their specific products have not been selected or verified.
No additional fit allowance was added: the openings match V5 reserved spaces.
For the TFT/speaker the ring is viewed from the front of the component; the
remaining dimension is depth. Other rectangular gauges check the plan view.
The button coupon checks shaft fit, not nut access or the curved robot wall.

COMPONENT-SPECIFIC CHECKS
SERVO: Compare only its main housing with gauge 01. Mounting ears/flanges are
expected to project outside that outline. Separately measure the flange spacing,
flange thickness, screw slots, shaft height and actual OEM horn. The existing
clamps were drawn around an assumed 2.5 mm flange thickness. Horn matching and
clamp fit are not established by this body-outline test.

DISPLAY: The 60 x 38 mm reservation is for the board, not the illuminated image.
Check the actual display against V5's 37 x 30 mm aperture using the dimensions;
this kit does not reproduce that rounded aperture or its recessed viewing tunnel.
Check PCB thickness, connector exits and whether the retaining bar would press
on components. Spacer/pad thickness must be determined from the real board.

SPEAKER: Check its frame, magnet and terminals within 36 x 36 x 18, plus access
for the retaining straps. A separate amplifier is tested with gauge 07.

BATTERY: Do not push a LiPo pouch into a rigid ring or clamp it. Compare a paper
outline of its measured dimensions with gauge 04. Include the lead exit and
strain relief. The reservation is not permission to compress a thicker pouch.

BOARDS: Include soldered headers, USB plug insertion space, wire exits and any
insulated mounting supports. The current base uses generic tie slots; board-
specific screw standoffs are not provided. A bare PCB fitting is only a first step.

BUTTONS: Test the shaft gently in gauge 09. Separately check body depth, terminal
space and nut access. V5 has two holes for panel buttons, not a tactile-switch
carrier. Do not enlarge the final holes until the actual buttons are identified.

PASS / FAIL RECORD
- Fits with usable clearance: record measured gaps and remaining depth.
- Tight or won't fit: record the component and measured opening dimensions.
- PCB fits but connector or mounting hardware conflicts: record separately.
- Not yet measured: leave as unverified, not a pass.
A passing gauge is a preliminary envelope check only.

NEXT ASSEMBLY TEST - CURRENT BLOCKER
Do not print a complete robot based solely on these gauges. V5's one-piece neck
drive has 28 and 35 mm flanges around an 18 mm shaft, while the body's guide is
20 mm. Neither flange passes through the guide. The adapter needs a removable
flange or another assembly-access correction, followed by insertion-path and
fastener-access checks. This kit does not correct that mechanism.
After that correction, test the servo cradle, clamps, actual horn and neck joint
as a small assembly before adding the head. Hardware and wire clearance during
motion are not established by static envelope tests.

FILES
stl/: nine planar gauges, one of each as needed.
fit-results.csv: measurement worksheet.
cad/generate_gauges.py: dependency-free Python 3 source.
cad/design-validation-reference.json: copied V5 reservation data, not new tests.
cad/gauge-validation.json: closure, winding, connected-component and volume checks
for these gauge meshes. Serialized STL edge closure was also checked.

REGENERATE
python3 cad/generate_gauges.py
