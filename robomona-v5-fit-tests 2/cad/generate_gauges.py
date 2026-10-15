"""Dependency-free planar envelope gauges; dimensions from RoboMona V5.
These are outline gauges, not replicas of actual component mounts.
"""
from pathlib import Path
import math, struct, json, csv
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT.parent/'robomona-v5-rounded-ears/cad/validation.json'
# Stored copy keeps the kit reproducible outside the original workspace.
if not DESIGN.exists(): DESIGN=ROOT/'cad/design-validation-reference.json'
spec=json.loads(DESIGN.read_text())
(ROOT/'stl').mkdir(exist_ok=True)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def ring(outer,inner,h=3):
 n=len(outer);v=[(x,y,z) for z in (0,h) for loop in (outer,inner) for x,y in loop];f=[]
 def quad(a,b,c,d):f.extend([(a,b,c),(a,c,d)])
 for i in range(n):
  j=(i+1)%n
  quad(i,j,2*n+j,2*n+i) # outside
  quad(n+j,n+i,3*n+i,3*n+j) # inside
  quad(2*n+i,2*n+j,3*n+j,3*n+i) # top
  quad(j,i,n+i,n+j) # bottom
 return v,f

def rectangle(w,d):return [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]
def export(name,v,f):
 edges=Counter();direct=Counter();vol=0
 for face in f:
  a,b,c=[v[i] for i in face];normal=cross(sub(b,a),sub(c,a));assert dot(normal,normal)>1e-12
  vol+=dot(a,cross(b,c))/6
  for i,j in zip(face,face[1:]+face[:1]):edges[tuple(sorted((i,j)))]+=1;direct[(i,j)]+=1
 assert all(c==2 for c in edges.values())
 assert all(direct[(b,a)]==c for (a,b),c in direct.items())
 assert vol>0
 # Edge-connected triangle traversal.
 edgefaces=defaultdict(list)
 for idx,face in enumerate(f):
  for i,j in zip(face,face[1:]+face[:1]):edgefaces[tuple(sorted((i,j)))].append(idx)
 adj=defaultdict(set)
 for a,b in edgefaces.values():adj[a].add(b);adj[b].add(a)
 todo=[0];seen=set()
 while todo:
  a=todo.pop()
  if a not in seen:seen.add(a);todo.extend(adj[a]-seen)
 assert len(seen)==len(f)
 path=ROOT/'stl'/f'{name}.stl'
 with path.open('wb') as out:
  out.write(b'RoboMona V5 planar envelope gauge'.ljust(80,b'\0'));out.write(struct.pack('<I',len(f)))
  for face in f:
   a,b,c=[v[i] for i in face];no=cross(sub(b,a),sub(c,a));l=math.sqrt(dot(no,no));no=tuple(x/l for x in no)
   out.write(struct.pack('<12fH',*no,*a,*b,*c,0))
 # Re-read binary output and repeat edge closure on actual serialized coordinates.
 data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0];check=Counter()
 assert len(data)==84+count*50
 for i in range(count):
  vals=struct.unpack_from('<12fH',data,84+50*i);verts=[tuple(vals[j:j+3]) for j in (3,6,9)]
  for a,b in zip(verts,verts[1:]+verts[:1]):check[tuple(sorted((a,b)))]+=1
 assert all(n==2 for n in check.values())
 return {'file':str(path.relative_to(ROOT)),'closed_edges':True,'consistent_winding':True,'connected_components':1,'volume_mm3':round(vol,3),'triangles':len(f)}

order=[('servo_body',(0,1)),('display',(0,2)),('speaker',(0,2)),('lipo',(0,1)),('esp32_c3',(0,1)),('tp4056',(0,1)),('audio_amplifier',(0,1)),('servo_power_converter',(0,1))]
rows=[];reports=[]
for num,(key,axes) in enumerate(order,1):
 sizes=spec['reserves'][key]['size_xyz'];w,d=[sizes[a] for a in axes];third=next(i for i in range(3) if i not in axes)
 name=f'{num:02d}_{key}_{w:g}x{d:g}mm';v,f=ring(rectangle(w+6,d+6),rectangle(w,d))
 reports.append(export(name,v,f));rows.append([name,w,d,sizes[third],'','','','',''])
# 12.2 mm nominal panel-button hole. 128-sided polygon stays within 0.002 mm of circle.
n=128;inner=[(6.1*math.cos(2*math.pi*i/n),6.1*math.sin(2*math.pi*i/n)) for i in range(n)]
outer=[(10.1*math.cos(2*math.pi*i/n),10.1*math.sin(2*math.pi*i/n)) for i in range(n)]
v,f=ring(outer,inner);reports.append(export('09_button_hole_D12p2mm',v,f))
with (ROOT/'fit-results.csv').open('w') as f:
 wr=csv.writer(f);wr.writerow(['gauge','opening_width_mm','opening_height_mm','remaining_reserved_dimension_mm','measured_component_width','measured_component_height','measured_component_depth','connector_clearance','result_notes']);wr.writerows(rows)
(ROOT/'cad/gauge-validation.json').write_text(json.dumps({'scope':'Planar envelope gauges only, not mount or insertion-path validation','parts':reports},indent=2)+'\n')
print(f'{len(reports)} STL gauges generated and checked, including serialized edge closure.')
