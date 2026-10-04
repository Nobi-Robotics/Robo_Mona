"""Smooth reference-led torso and six tentacles; dimensions in millimetres."""
import numpy as np
from pathlib import Path
import hashlib
import manifold3d as m
from scipy.interpolate import PchipInterpolator, CubicSpline
from skimage.measure import marching_cubes

PROFILE=np.array([
 [30,26,29,8],[36,27,31,8],[44,26,32,8],[52,25,33,8],
 [60,22,28,6],[68,17,21,4],[76,13,16,1],[84,12.3,13,0],[89,12.3,13,0]
],float)
PATHS=[
 np.array([[6,-8,49,13],[12,-22,44,11],[15,-31,36,9],[24,-35,36,8],
           [29,-35,42,5.5],[27,-34,48,3.5],[22,-33,46,2.5]],float),
 np.array([[17,13,47,12],[32,7,39,11],[46,-2,38,9],[56,-5,44,7],
           [57,-6,52,5],[53,-7,56,3.7],[49,-8,53,2.7]],float),
 np.array([[16,17,57,12],[28,16,53,12],[39,14,58,11],[48,12,70,10],
           [52,11,80,7.5],[48,10,83,6],[44,9,78,4.8]],float)
]

def path_samples(path,count=55):
 t=np.linspace(0,1,len(path));u=np.linspace(0,1,count)
 return np.column_stack([CubicSpline(t,path[:,i],bc_type='natural')(u) for i in range(3)]+
                        [PchipInterpolator(t,path[:,3])(u)])

def smooth_min(a,b,k):
 h=np.maximum(k-np.abs(a-b),0)/k
 return np.minimum(a,b)-h*h*k*.25

def torso_profile(z,inset=0):
 values=[PchipInterpolator(PROFILE[:,0],PROFILE[:,i],extrapolate=True)(z) for i in range(1,4)]
 return values[0]-inset,values[1]-inset,values[2]

def make_body(step=.65):
 """Vectorized smooth-union field prevents the hard seams of boolean tubes."""
 key=hashlib.sha256(Path(__file__).read_bytes()+str(step).encode()).hexdigest()[:12]
 cache=Path(__file__).parent/'.cache'/f'body-{key}.npz'
 if cache.exists():
  raw=np.load(cache);return m.Manifold(m.Mesh(raw['v'],raw['f']))
 axes=[np.arange(-68,68+step,step,dtype=np.float32),
       np.arange(-54,54+step,step,dtype=np.float32),
       np.arange(25,93+step,step,dtype=np.float32)]
 X,Y,Z=np.meshgrid(*axes,indexing='ij');zc=np.clip(Z,30,89)
 rx,ry,cy=torso_profile(zc)
 field=(np.sqrt((X/rx)**2+((Y-cy)/ry)**2)-1)*np.minimum(rx,ry)
 field=np.maximum(field,np.maximum(30-Z,Z-88))
 # Gentle rear haunches enclose the rear servo-support posts.
 for sign in (-1,1):
  bulge=(np.sqrt(((X-sign*16)/10)**2+((Y-32)/13)**2+((Z-48)/16)**2)-1)*10
  field=smooth_min(field,bulge,4)
  front=(np.sqrt(((X-sign*16)/10)**2+((Y+12)/13)**2+((Z-49)/15)**2)-1)*10
  field=smooth_min(field,front,4)
 for sign in (-1,1):
  for path in PATHS:
   points=path_samples(path);points[:,0]*=sign
   dist=np.full(X.shape,1e5,dtype=np.float32)
   for a,b in zip(points[:-1],points[1:]):
    dx,dy,dz=b[:3]-a[:3];den=dx*dx+dy*dy+dz*dz
    u=np.clip(((X-a[0])*dx+(Y-a[1])*dy+(Z-a[2])*dz)/den,0,1)
    d=np.sqrt((X-a[0]-u*dx)**2+(Y-a[1]-u*dy)**2+(Z-a[2]-u*dz)**2)-(a[3]+u*(b[3]-a[3]))
    np.minimum(dist,d,out=dist)
   field=smooth_min(field,dist,5)
 field=np.maximum(field,32-Z)
 vs,fs,_,_=marching_cubes(field,0,spacing=(step,step,step),allow_degenerate=False)
 vs+=np.array([a[0] for a in axes]);fs=fs[:,::-1].copy()
 solid=m.Manifold(m.Mesh(vs.astype(np.float32),fs.astype(np.uint32)))
 if solid.volume()<0:solid=m.Manifold(m.Mesh(vs.astype(np.float32),fs[:,::-1].copy().astype(np.uint32)))
 assert solid.status()==m.Error.NoError,(solid.status(),solid.volume())
 cache.parent.mkdir(exist_ok=True);raw=solid.to_mesh()
 np.savez_compressed(cache,v=np.asarray(raw.vert_properties),f=np.asarray(raw.tri_verts))
 return solid

def inner_shell():
 """Section loft for the service cavity, open below the pedestal deck."""
 z=np.arange(29,89.01,1.0);rx,ry,cy=torso_profile(np.clip(z,30,89),2.6)
 sections=[]
 for h,a,b,y in zip(z,rx,ry,cy):
  sections.append(m.Manifold.cylinder(.2,1,circular_segments=64,center=True).scale((a,b,1)).translate((0,y,h)))
 return m.Manifold.batch_boolean([m.Manifold.compose([a,b]).hull() for a,b in zip(sections[:-1],sections[1:])],m.OpType.Add)
