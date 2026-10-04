#!/usr/bin/env python3
"""RoboMona v5 rounded-cat-ear fit-check CAD. Units mm.

Editable constructive-solid-geometry source using manifold3d. Assembly coordinates
are retained in assembly/ files. Individual STL files are moved/rotated onto Z=0.
This is a packaging prototype; verify actual hardware before printing full shells.

Dependencies: manifold3d, numpy, trimesh. Run from any directory:
    python3 generate_model.py
Optional first argument: alternate parameters JSON path.
"""
from pathlib import Path
import json, sys
import numpy as np
import manifold3d as m
import trimesh
from organic_body import make_body, inner_shell, PATHS, path_samples

ROOT = Path(__file__).resolve().parents[1]
P = json.loads(Path(sys.argv[1]).read_text() if len(sys.argv)>1 else (ROOT/'cad/parameters.json').read_text())
W = P['wall']; N = int(P['quality_segments'])
m.set_circular_segments(N)

def box(size, center=(0,0,0)):
    return m.Manifold.cube(size, center=True).translate(center)

def cyl(r, h, center=(0,0,0), axis='z'):
    s = m.Manifold.cylinder(h, r, circular_segments=N, center=True)
    if axis == 'y': s = s.rotate((90,0,0))
    if axis == 'x': s = s.rotate((0,90,0))
    return s.translate(center)

def ellipsoid(radii, center):
    return m.Manifold.sphere(1, N).scale(radii).translate(center)

def union(*items):
    return m.Manifold.batch_boolean(list(items), m.OpType.Add)

def hull(*items):
    return m.Manifold.compose(list(items)).hull()

def rounded_xy(w,d,h,r,z):
    return hull(*[cyl(r,h,(sx*(w/2-r), sy*(d/2-r),z)) for sx in (-1,1) for sy in (-1,1)])

def roundbox(w,d,h,r,center):
    cx,cy,cz=center
    return hull(*[ellipsoid((r,r,r),(cx+sx*(w/2-r),cy+sy*(d/2-r),cz+sz*(h/2-r)))
        for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)])

def tentacle(points, start_radius=10, end_radius=3):
    """Tapered organic sweep through a Catmull-Rom path, using short hull spans."""
    pts=np.asarray(points,float); padded=np.vstack((pts[0],pts,pts[-1])); spheres=[]
    for i in range(len(pts)-1):
        a,b,c,d=padded[i:i+4]
        for t in np.linspace(0,1,9,endpoint=False):
            p=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
            u=(i+t)/(len(pts)-1); r=end_radius+(start_radius-end_radius)*(1-u)**1.2
            spheres.append(m.Manifold.sphere(r,24).translate(p))
    spheres.append(m.Manifold.sphere(end_radius,24).translate(pts[-1]))
    return union(*[hull(a,b) for a,b in zip(spheres[:-1],spheres[1:])])

def slot(length, diameter, h, center, axis='z', direction='x'):
    c=np.array(center,float); delta=np.zeros(3)
    delta[{'x':0,'y':1,'z':2}[direction]]=(length-diameter)/2
    return hull(cyl(diameter/2,h,c-delta,axis),cyl(diameter/2,h,c+delta,axis))

def mesh(s):
    a=s.to_mesh64()
    return trimesh.Trimesh(vertices=np.asarray(a.vert_properties)[:,:3], faces=np.asarray(a.tri_verts),process=True)

def stl_precision(a):
    """Normalize at STL float32 precision and remove only collapsed/duplicate faces.

    Boolean slivers can collapse during STL serialization. Preserve narrow valid
    triangles; a geometric area threshold can accidentally create holes.
    """
    a=trimesh.Trimesh(vertices=np.asarray(a.vertices,dtype=np.float32),faces=a.faces,process=True)
    a.merge_vertices(digits_vertex=6)
    f=a.faces
    a.update_faces((f[:,0]!=f[:,1]) & (f[:,1]!=f[:,2]) & (f[:,0]!=f[:,2]))
    a.update_faces(a.unique_faces())
    a.remove_unreferenced_vertices()
    assert a.is_watertight and a.is_winding_consistent,'STL precision normalization failed'
    return a

def component_count(a):
    """Count edge-connected faces without an optional scipy/networkx dependency."""
    parents=np.arange(len(a.faces))
    def root(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]]; i=parents[i]
        return i
    for i,j in a.face_adjacency:
        ri,rj=root(i),root(j)
        if ri!=rj: parents[rj]=ri
    return len({root(i) for i in range(len(parents))})

parts={}; notes={}; placements={}
def add(name, solid, note, orientation=(0,0,0)):
    clean=solid.simplify(.015)
    clean=union(*[island for island in clean.decompose() if island.volume()>.001])
    parts[name]=clean; notes[name]=note; placements[name]=orientation

# Pedestal and upright low-mounted MG996R, long axis along Y.
bw,bd,bh,br=[P[k] for k in ('base_width','base_depth','base_height','base_corner_radius')]
ct=P['cover_thickness'];seam=.2
base_outer=rounded_xy(bw,bd,bh-ct-seam,br,(bh+ct+seam)/2)
base_inner=rounded_xy(bw-2*W,bd-2*W,bh-ct-W+4,br-W,(ct+bh-W-4)/2)
base=base_outer-base_inner
base_screws=[(sx*56,sy*43) for sx in (-1,1) for sy in (-1,1)]
for x,y in base_screws:
    base=base+(cyl(6,bh-ct,(x,y,(bh+ct)/2))^rounded_xy(bw,bd,bh,br,bh/2))
    base=base-cyl(P['m3_pilot']/2,18,(x,y,ct+8))
torso_screws=[(sx*22,sy*20) for sx in (-1,1) for sy in (-1,1)]
for x,y in torso_screws:base=base-cyl(1.6,10,(x,y,bh))
sv=P['servo_body_reserve'];servo_center=P['servo_body_center_xyz']
servo_box=box(sv,servo_center)
base=base-box((26,48,35),(0,10.35,35))
for x in (-11,11):base=base-cyl(P['button_hole_diameter']/2,18,(x,-bd/2,17),'y')
base=base-box((14,16,8),(-6,bd/2,12))-box((8,16,14),(-29,bd/2,17))
# Uprights rise from the base deck, within the flared lower torso.
supports=[]
for y in (-14,34):
    beam=box((41,9,3),(0,y,49.5))
    for x in (-16,16):
        beam=beam+cyl(4,22,(x,y,40.5))
        beam=beam-cyl(1.25,16,(x,y,47))-cyl(1.25,7,(x,y,53))
    supports.append(beam)
base=base+union(*supports)
base=base-servo_box
add('01_base_tub',base,'Low servo cradle rises to51mm from deck; MG996R long axis Y; two front12.2mm buttons. Support roof and cradle; review slicer orientation.',(0,0,0))
cover=rounded_xy(bw-.6,bd-.6,ct,br-.3,ct/2)
for x,y in base_screws:
    cover=cover-cyl(1.6,8,(x,y,ct/2))-cyl(3.2,1.8,(x,y,.9))
for x,y in [(-57,-20),(-27,-20),(-57,20),(-27,20),(28,-28),(55,-28),(28,0),(55,0),(25,28),(56,28),(-20,43),(8,43)]:
    cover=cover-slot(8,3,8,(x,y,ct/2),'z','y')
add('02_base_bottom_cover',cover,'Generic tie slots; relocated37x66x12 LiPo reserve left of low servo. No pressure ribs against pouch.')

# Organic sculpt: a narrow tapered torso smoothly joins all six thick curls.
print('Sculpting smooth torso and tentacles...',flush=True)
outer=make_body(P['sculpt_grid_mm'])
torso=outer-inner_shell()
# Circular bushing guide around hollow drive extension; loose fit is provisional.
torso=torso+(cyl(12.3,5,(0,0,79.5))-cyl(10,7,(0,0,79.5)))
for x,y in torso_screws:
    torso=torso+cyl(4.3,12,(x,y,38))
    torso=torso-cyl(1.25,14,(x,y,38))
# Integral suction-cup pads on the forward side of the raised limbs.
for sign in (-1,1):
    curve=path_samples(PATHS[2],101)
    for idx in (30,48,65,82):
        x,y,z,rr=curve[idx];x*=sign
        cup=ellipsoid((3.3,2.0,4.0),(x,y-rr-.25,z))
        torso=torso+cup
        torso=torso-ellipsoid((2.5,.85,3.1),(x,y-rr-1.9,z))
    x,y,z,rr=path_samples(PATHS[0],101)[58];x*=sign
    torso=torso+ellipsoid((3.3,2,4.2),(x,y-rr-.25,z))
    torso=torso-ellipsoid((2.5,.8,3.3),(x,y-rr-1.9,z))
# Motor, flange-clamp and drive clearances are cut after the sculpt union.
torso=torso-servo_box
for y in (-14,34):
    torso=torso-box((41.6,9.6,3.6),(0,y,49.5))
    for x in (-16,16):torso=torso-cyl(4.3,23,(x,y,40.5))
    torso=torso-box((39.6,10.6,3.6),(0,y,55))
torso=torso-cyl(18,4.6,(0,0,62))-cyl(10,29,(0,0,76))-cyl(14.4,12,(0,0,85.7))
torso=torso^box((150,130,56),(0,0,60))
add('03_reference_body_six_tentacles',torso,'Narrow25mm neck, flared54mm lower torso, six blended thick curls and integral suction pads. All fixed. Supports under raised curls.')
for i,y in enumerate((-14,34)):
    bar=box((39,10,3),(0,y,55))
    for x in (-16,16):bar=bar-slot(7,3.2,8,(x,y,55),'z','y')
    bar=bar-servo_box
    add(f'04_servo_clamp_{i+1}',bar,'Low-servo flange clamp; assumed flange thickness2.5mm, verify actual servo.')

# Hollow ellipsoidal cat head, split across Y=0 for direct hardware access.
hw,hd,hh,hz,hr=[P[k] for k in ('head_width','head_depth','head_height','head_bottom','head_radius')]
hc=hz+hh/2
head_outer=ellipsoid((hw/2,hd/2,hh/2),(0,0,hc))
head_inner=ellipsoid((hw/2-W*1.12,hd/2-W*1.12,hh/2-W*1.12),(0,0,hc))
head=head_outer-head_inner
head=head+cyl(14,7,(0,0,hz+3.5))
for sign in (-1,1):
    # Broad curved pinna, a gently outward leaning rounded tip and a shallow
    # front-facing inner-ear bowl. The bowl ends before the rear half/seam.
    tip=P['ear_tip_radius']
    ear=hull(ellipsoid((15,11,11),(sign*43,0,163)),
             ellipsoid((9,8,8),(sign*48,0,176)),
             ellipsoid((tip,5.5,tip),(sign*52,0,P['ear_top']-tip)))
    bowl=hull(ellipsoid((5.8,4.2,7),(sign*47,-9,174)),
              ellipsoid((2.0,2.5,2.5),(sign*51,-6.5,180)))
    ear=ear-bowl
    head=head+ear
# Four shell-closure bosses; clipped to outside shape so they cannot bulge through.
head_screws=[(sx*35,z) for sx in (-1,1) for z in (114,148)]
for x,z in head_screws:
    head=head+(cyl(6,hd+10,(x,0,z),'y')^head_outer)
    head=head-cyl(P['m3_clearance']/2,70,(x,35,z),'y')
    head=head-cyl(3.2,50,(x,39,z),'y')
    head=head-cyl(P['m3_pilot']/2,14,(x,-7,z),'y')
# Recessed37×30 TFT aperture with a flared viewing tunnel through the oval face.
dz=P['display_center_z']; dw,dh=P['display_window']; rw,rh,rd=P['display_reserve']
dy=P['display_center_y']; outer_w,outer_h=P['display_outer_funnel']
def rounded_xz(w,h,r,y,depth):
    return hull(*[cyl(r,depth,(sx*(w/2-r),y,dz+sz*(h/2-r)),'y') for sx in (-1,1) for sz in (-1,1)])
funnel=hull(rounded_xz(outer_w,outer_h,7,-hd/2-1,.3),rounded_xz(dw,dh,3,dy-rd/2,.3))
# Low raised bezel conforms to the dome, with no detached faceplate.
skin=ellipsoid((hw/2+1.1,hd/2+1.1,hh/2+1.1),(0,0,hc))-ellipsoid((hw/2-.3,hd/2-.3,hh/2-.3),(0,0,hc))
head=head+(skin^rounded_xz(62,53,11,-hd/2+10,40))
for sign in (-1,1):
    for zz in (113,120):
        dots=[]
        for xx in (33,38):
            yy=-hd/2*np.sqrt(max(.01,1-(xx/(hw/2))**2-((zz-hc)/(hh/2))**2))-.3
            dots.append(ellipsoid((1.1,1.1,1.3),(sign*xx,yy,zz)))
        head=head+hull(*dots)

# Display frame: outer70×46,60×38 clear pocket,14mm deep with tie/retainer pilots.
frame=box((70,17,46),(0,dy-1.5,dz))-box((rw,20,rh),(0,dy-1.5,dz))
head=head+(frame^head_outer)
for x in (-34,34):
    head=head+(cyl(4,17,(x,dy-1.5,dz),'y')^head_outer)
    head=head-cyl(P['m3_pilot']/2,20,(x,dy-1,dz),'y')
head=head-funnel-box((rw,rd,rh),(0,dy,dz))
retainer=box((76,3,8),(0,dy+9.5,dz))
for x in (-34,34): retainer=retainer-cyl(P['m3_clearance']/2,9,(x,dy+9.5,dz),'y')
add('07_display_retainer',retainer,'Rear retention bar spans PCB pocket; use soft insulating pads, avoid components. 2×M3 screws, PCB56.5×34 assumed.',(90,0,0))
# Speaker support frame and rear grille (36×36×18 envelope).
speaker_x=0; speaker_z=dz+2; speaker_y=26
sframe=box((43,17,43),(speaker_x,speaker_y+15.5,speaker_z))-box((37,21,37),(speaker_x,speaker_y+15.5,speaker_z))
head=head+(sframe^head_outer)
for gx in range(-2,3):
    for gz in range(-2,3):
        if gx*gx+gz*gz<=5:
            head=head-cyl(1.6,30,(speaker_x+gx*5,speaker_y+19,speaker_z+gz*5),'y')
for x in (speaker_x-20,speaker_x+20):
    for z in (speaker_z-10,speaker_z+10):
        head=head-box((2.8,30,5.5),(x,speaker_y+19,z))
head=head-box((36,18,36),(0,speaker_y,speaker_z))
# Bottom wiring arc and horn-platen attachment; adapter is a separate printed part.
# Cables pass through the hollow extension, avoiding the former side notch.
head=head-cyl(5,30,(0,0,hz+5))
for x in (-9,9): head=head-cyl(P['m3_clearance']/2,30,(x,0,hz+5))
gap=P['head_joint_gap']
front=head^box((160,100-gap/2,220),(0,-50-gap/4,110))
rear=head^box((160,100-gap/2,220),(0,50+gap/4,110))
# Internal screw stops bridge the cosmetic seam; shells cannot be pulled inward.
for x,z in head_screws:
    stop=cyl(6,gap+.4,(x,-.2,z),'y')-cyl(P['m3_pilot']/2,2,(x,0,z),'y')
    front=front+stop
add('05_head_front',front,'True ellipsoidal cat dome, rounded ears with shallow inner bowls, flared52×44-to37×30 viewing recess; TFTreserve60×38×12 centeredY−27. Integrated7mm neck pad. Rear-access M3 closure; curved bezel and cheek whiskers.',(-90,0,0))
add('06_head_rear',rear,'Rear speaker grille and integral strap frame; fourM3 pilot bosses with positive closure stops. Hollow shell; rear half of ears.',(90,0,0))
# Drive platen spans both shell halves, holds the original horn and ties the split
# bottom together. Pilot slots intentionally do not reproduce unknown horn holes.
# Hollow torque extension from the lowered OEM horn to the head.
adapter=cyl(17.5,4,(0,0,62))+cyl(9,18,(0,0,72))+cyl(14,4,(0,0,82))
adapter=adapter-cyl(5,40,(0,0,77))
# Side entry allows the harness to enter above the horn's center screw.
adapter=adapter-box((7,16,7),(0,-8,70))
for y in (-10,10):adapter=adapter-slot(12,2.2,8,(0,y,62),'z','x')
for x in (-9,9):adapter=adapter-cyl(1.25,8,(x,0,82))
add('08_hollow_neck_drive',adapter,'Provisional hollow extension: lower17.5-radius OEM-horn flange z60..64, shaftOD18/ID10, upper28mm headplate. Match-drill horn; assess stiffness and bushing fit.')

# Exports with verification and reproducible assembly transforms.
(ROOT/'stl').mkdir(exist_ok=True); (ROOT/'cad'/'assembly').mkdir(exist_ok=True)
report={'units':'mm','status':'FIT-CHECK PROTOTYPE — physical fit, load, motion, thermal and charging validation NOT performed',
        'coordinate_system':'X right, Y rear, Z up; front is -Y',
        'parts':{},'reserves':{},'warnings':[
        'Real screen PCB, LiPo pouch, speaker module, USB board and button dimensions must be measured before full printing.',
        'V3 changes servo layout: upright long-axis along Y, low cradle across base and lower body, with a new hollow drive extension. Horn, bearing, fasteners and load behavior need physical engineering checks.',
        'Mesh checks establish watertight geometry only, not mechanical strength, fit or electrical safety.',
        'Head yaw ±30 degrees is an intended initial limit, not tested travel; establish safe travel after wiring and fitting.',
        '3.2mm clearance and2.5mm pilot holes may need drilling; choose screw lengths after measuring actual stack.',
        'Assembly STL is for visualization, not a one-piece print.']}
assembly_mesh=[]
for name,s in parts.items():
    a=stl_precision(mesh(s)); assembly_mesh.append(a)
    a.export(ROOT/'cad'/'assembly'/f'{name}_assembled.stl')
    oriented=s.rotate(placements[name]); printable=mesh(oriented)
    translation=np.array([0.,0.,-printable.bounds[0,2]])
    printable.apply_translation(translation)
    printable=stl_precision(printable)
    printable.export(ROOT/'stl'/f'{name}.stl')
    comps=component_count(printable)
    report['parts'][name]={'file':f'stl/{name}.stl','assembled_bounds':np.round(a.bounds,3).tolist(),
        'print_bounds':np.round(printable.bounds,3).tolist(),'dimensions':np.round(printable.extents,3).tolist(),
        'print_rotation_xyz_deg':list(placements[name]),'print_translation':translation.tolist(),
        'watertight':bool(printable.is_watertight),'winding_consistent':bool(printable.is_winding_consistent),
        'connected_components':comps,'volume_mm3':round(float(printable.volume),2),
        'faces':len(printable.faces),'notes':notes[name]}
    assert printable.is_watertight and printable.is_winding_consistent and printable.volume>0,(name,'invalid mesh')
    assert comps==1,(name,'disconnected solids',comps)
assembly=trimesh.util.concatenate(assembly_mesh)
assembly.export(ROOT/'cad'/'assembly_for_visualization_NOT_FOR_PRINT.stl')
report['assembled_bounds']=np.round(assembly.bounds,3).tolist()
report['assembled_dimensions']=np.round(assembly.extents,3).tolist()
report['printed_part_interference_checks']=[]
part_names=list(parts)
for i,name in enumerate(part_names):
    for other in part_names[i+1:]:
        overlap=parts[name]^parts[other]
        volume=float(overlap.volume())
        report['printed_part_interference_checks'].append({'part_a':name,'part_b':other,'intersection_mm3':round(volume,6)})
        assert volume<.01,(name,other,'printed part interference',volume)
report['reserves']={
  'servo_body':{'size_xyz':sv,'center_xyz':servo_center,'flange_and_horn':'separate provisional interface; not included in body rectangle'},
  'display':{'size_xyz':[60,12,38],'center_xyz':[0,dy,dz],'assumed_PCB':[56.5,34],'visible_window_xz':[37,30],'outer_funnel_xz':[52,44]},
  'speaker':{'size_xyz':[36,18,36],'center_xyz':[0,speaker_y,speaker_z]},
  'lipo':{'size_xyz':[37,66,12],'center_xyz':[-42,0,9],'assumed_cell':[35,60,8]},
  'esp32_c3':{'size_xyz':[27,23,12],'center_xyz':[40,-25,9]},
  'audio_amplifier':{'size_xyz':[24,23,12],'center_xyz':[42,0,9]},
  'servo_power_converter':{'size_xyz':[40,25,15],'center_xyz':[34,24,10.5]},
  'tp4056':{'size_xyz':[32,20,10],'center_xyz':[-6,43,8]}}
report['hardware_envelope_checks']=[]
for label,reserve in report['reserves'].items():
    region=box(reserve['size_xyz'],reserve['center_xyz'])
    for name,s in parts.items():
        volume=float((region^s).volume())
        report['hardware_envelope_checks'].append({'reserve':label,'part':name,'intersection_mm3':round(volume,6)})
        assert volume<.01,(label,name,'reserved hardware envelope interference',volume)
moving_names=['05_head_front','06_head_rear','07_display_retainer','08_hollow_neck_drive']
moving=union(*[parts[name] for name in moving_names])
fixed=union(*[solid for name,solid in parts.items() if name not in moving_names])
report['sampled_printed_yaw_checks']=[]
for angle in range(-30,31,5):
    pose=moving.rotate((0,0,angle))
    volume=float((pose^fixed).volume())
    report['sampled_printed_yaw_checks'].append({'yaw_degrees':angle,'fixed_part_intersection_mm3':round(volume,6)})
    assert volume<.01,('printed yaw collision',angle,volume)
report['yaw_check_limit']='13 static mesh poses at5-degree increments; excludes installed hardware, wires, screw heads and actual servo alignment. Physical motion is unverified.'
(ROOT/'cad'/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','assembled_dimensions')},indent=2))
for name,r in report['parts'].items():
    print(f"{name}: watertight={r['watertight']} components={r['connected_components']} dims={r['dimensions']} volume={r['volume_mm3']}")
