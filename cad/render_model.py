import os, sys, json
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/mpl-robomona')
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
from pathlib import Path
root=Path(sys.argv[1])
body_mode='--body' in sys.argv[2:]
paths=[root/'cad/assembly/03_reference_body_six_tentacles_assembled.stl'] if body_mode else [Path(a) for a in sys.argv[2:]]
if not paths:
    spec=json.loads((root/'cad/validation.json').read_text())
    paths=[root/'cad/assembly'/f'{name}_assembled.stl' for name in spec['parts']]
parts=[]
for p in paths:
    mesh=trimesh.load(p,force='mesh',process=False)
    nm=p.stem.lower()
    color='#78838e'
    if any(x in nm for x in ['button','accent','ring']): color='#3689b6'
    elif any(x in nm for x in ['bezel','face']): color='#687581'
    elif any(x in nm for x in ['lid','cover']): color='#8794a0'
    elif any(x in nm for x in ['servo','bracket','clamp','cassette']): color='#838a91'
    parts.append((nm,np.asarray(mesh.triangles),np.asarray(mesh.face_normals),to_rgb(color)))
vertices=np.concatenate([p[1].reshape(-1,3) for p in parts])
blo,bhi=vertices.min(0),vertices.max(0)
fig=plt.figure(figsize=(14,9),dpi=100,facecolor='white')
fig.text(.045,.945,('V5 body sculpt — actual printable STL' if body_mode else 'V5 rounded cat ears — dimensions in mm'),fontsize=23,fontweight='bold',color='#222831')
fig.text(.045,.907,'Head 140 mm wide | Octopus body 127 mm wide | Same 37 x 30 mm screen aperture',fontsize=12,color='#66707b')
light=np.array([-1,-1,2.2]);light/=np.linalg.norm(light)
def view(rect,cam,title,label_dims=False):
    ax=fig.add_axes(rect)
    cam=np.array(cam,float);cam/=np.linalg.norm(cam)
    right=np.cross([0,0,1],cam);right/=np.linalg.norm(right)
    up=np.cross(cam,right)
    tri=np.concatenate([p[1] for p in parts])
    normals=np.concatenate([p[2] for p in parts])
    colors=np.concatenate([np.tile(p[3],(len(p[1]),1)) for p in parts])
    shade=.67+.33*np.maximum(normals@light,0)
    colors=np.clip(colors*shade[:,None],0,1)
    # Cull rear-facing polygons only; inner cavity normals stay visible where appropriate.
    visible=normals@cam > 1e-6
    tri=tri[visible];colors=colors[visible]
    d=tri.mean(1)@cam
    inds=np.argsort(d)
    xy=np.stack((tri@right,tri@up),axis=-1)
    lo=xy.reshape(-1,2).min(0);hi=xy.reshape(-1,2).max(0)
    # Orthographic software z-buffer keeps occlusion exact even across long triangles.
    scale=4.2
    nx=int(np.ceil((hi[0]-lo[0])*scale))+3; ny=int(np.ceil((hi[1]-lo[1])*scale))+3
    zbuf=np.full((ny,nx),-np.inf); bitmap=np.ones((ny,nx,3))
    pix=(xy-lo)*scale+1
    zvals=tri@cam
    dmin,dmax=zvals.min(),zvals.max()
    for p,z,c in zip(pix,zvals,colors):
        x0=max(0,int(np.floor(p[:,0].min())));x1=min(nx-1,int(np.ceil(p[:,0].max())))
        y0=max(0,int(np.floor(p[:,1].min())));y1=min(ny-1,int(np.ceil(p[:,1].max())))
        den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(den)<1e-9: continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
        b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den
        g=1-a-b
        depth=a*z[0]+b*z[1]+g*z[2]
        region=zbuf[y0:y1+1,x0:x1+1]
        take=(a>=-1e-6)&(b>=-1e-6)&(g>=-1e-6)&(depth>region)
        region[take]=depth[take]
        shade_depth=.65+.35*np.clip((depth-dmin)/(dmax-dmin),0,1)
        rgb=bitmap[y0:y1+1,x0:x1+1]
        rgb[take]=c*shade_depth[take,None]
    ax.imshow(bitmap,origin='lower',extent=[lo[0]-1/scale,lo[0]+(nx-1)/scale,lo[1]-1/scale,lo[1]+(ny-1)/scale],interpolation='bilinear')
    pad=16 if label_dims else 7
    ax.set_xlim(lo[0]-pad,hi[0]+pad)
    ax.set_ylim(lo[1]-20,hi[1]+8)
    ax.set_aspect('equal');ax.axis('off')
    ax.set_title(title,fontsize=14,fontweight='bold',color='#303943',pad=17)
    if label_dims:
        col='#4383aa'
        x1,x2=lo[0],hi[0];y=lo[1]-10
        ax.annotate('',(x1,y),(x2,y),arrowprops={'arrowstyle':'<->','color':col,'linewidth':1})
        ax.plot([x1,x1],[lo[1]-1,y-2],color=col,lw=.7)
        ax.plot([x2,x2],[lo[1]-1,y-2],color=col,lw=.7)
        ax.text((x1+x2)/2,y-7,f'{x2-x1:.1f}',ha='center',fontsize=11,color=col)
        x=x1-8
        ax.annotate('',(x,lo[1]),(x,hi[1]),arrowprops={'arrowstyle':'<->','color':col,'linewidth':1})
        ax.text(x-5,(lo[1]+hi[1])/2,f'{hi[1]-lo[1]:.1f}',ha='center',va='center',rotation=90,fontsize=11,color=col)
    return ax
view([.032,.15,.292,.7],[0,-1,0],'FRONT',True)
view([.345,.15,.275,.7],[1,0,0],'SIDE',True)
view([.63,.15,.34,.7],[1,-1.55,.6],'ISOMETRIC')
fig.text(.045,.085,'Actual STL geometry • Electronics omitted; screen opening shown empty',fontsize=12,fontweight='bold',color='#374450')
fig.text(.045,.05,'Hardware envelopes and mounts require verification against the purchased components before a final assembly print.',fontsize=11,color='#69747d')
out=root/'renders'/('body-detail.png' if body_mode else 'model-preview.png');out.parent.mkdir(exist_ok=True)
fig.savefig(out,dpi=100,facecolor='white')
print(json.dumps({'render':str(out),'assembly_bounds':np.round([blo,bhi],3).tolist(),'dimensions':np.round(bhi-blo,3).tolist(),'parts':len(parts)}))
