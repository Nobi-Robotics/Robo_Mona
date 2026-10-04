"""Verify the actual saved STL files and reserved electronics boxes."""
from pathlib import Path
from itertools import combinations
import json, hashlib
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
design=json.loads((root/'cad/validation.json').read_text())
results={'status':'Geometry checks only; physical assembly and loaded motion unverified','parts':{},'hardware_box_pairs':[]}
for name,spec in design['parts'].items():
 path=root/spec['file'];mesh=trimesh.load(path,force='mesh')
 count=len(mesh.split(only_watertight=False))
 entry={'file':spec['file'],'watertight':bool(mesh.is_watertight),
        'winding_consistent':bool(mesh.is_winding_consistent),'connected_components':count,
        'finite_vertices':bool(np.isfinite(mesh.vertices).all()),'volume_mm3':float(mesh.volume),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 assert entry['watertight'] and entry['winding_consistent'] and count==1 and entry['finite_vertices'] and mesh.volume>0,(name,entry)
 results['parts'][name]=entry
for (a,ra),(b,rb) in combinations(design['reserves'].items(),2):
 ca,cb=np.asarray(ra['center_xyz']),np.asarray(rb['center_xyz'])
 ha,hb=np.asarray(ra['size_xyz'])/2,np.asarray(rb['size_xyz'])/2
 overlap=np.maximum(0,np.minimum(ca+ha,cb+hb)-np.maximum(ca-ha,cb-hb))
 volume=float(np.prod(overlap));assert volume<.01,(a,b,volume)
 results['hardware_box_pairs'].append({'a':a,'b':b,'overlap_mm3':volume})
(root/'cad/export-verification.json').write_text(json.dumps(results,indent=2)+'\n')
print(f"Actual STL files: {len(results['parts'])} passed. Hardware box pairs: {len(results['hardware_box_pairs'])} passed.")
