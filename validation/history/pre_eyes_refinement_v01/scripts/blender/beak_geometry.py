"""Split the accepted hooked beak envelope into closed upper/lower rigid jaw meshes."""
import hashlib
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from blockout_geometry import parameters, clean, swatch, loft, mesh


def config(root):
    coarse,scale=parameters(root)
    cfg=json.loads((Path(root)/'design/beak.json').read_text())
    if not 0<cfg['closed_seam_gap_m']<.002 or not 0<cfg['maximum_open_degrees']<=30:
        raise ValueError('Invalid beak seam or opening range')
    normal=Vector(cfg['split_plane_normal'])
    if abs(normal.x)>1e-8 or normal.z<=0 or normal.length<.1:
        raise ValueError('Beak split must be symmetric with upward normal')
    return coarse,cfg,scale


def stable_mesh(bm):
    """Canonicalize bmesh clipping order so repeated builds have identical indices."""
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    ordered=sorted(bm.verts,key=lambda v:tuple(v.co))
    indices={v:i for i,v in enumerate(ordered)}
    vertices=[tuple(v.co) for v in ordered]
    faces=[]
    for face in bm.faces:
        values=tuple(indices[v] for v in face.verts)
        start=values.index(min(values))
        faces.append(values[start:]+values[:start])
    return vertices,sorted(faces)


def set_open(root,value):
    """Rotate the actual lower jaw about its documented hinge; 0 closed, 1 max open."""
    _,cfg,_=config(root)
    if not 0<=value<=1: raise ValueError('Beak opening must be in [0,1]')
    pivot=bpy.data.objects['BAK_LowerPivot']
    pivot.rotation_euler=(-math.radians(cfg['maximum_open_degrees'])*value,0,0)
    pivot['opening_probe_value']=float(value)
    bpy.context.view_layer.update()


def build(root):
    root=Path(root)
    coarse,cfg,scale=config(root)
    freeze=json.loads((root/'design/silhouette_freeze.json').read_text())
    assert freeze['status']=='silhouette_frozen'
    assert hashlib.sha256((root/'design/proportions.json').read_bytes()).hexdigest()==freeze['evidence_sha256']['design/proportions.json']
    if 'FAC_MaskBridge' not in bpy.data.objects: raise RuntimeError('Beak stage requires accepted #16 face')
    clean(('BAK_','_BAK_SOURCE_'))
    orange=swatch(root,'orange_reference')
    interior=swatch(root,cfg['interior_swatch'])
    # Sample/split once at reference scale, then uniformly scale the final cages.
    # Clipping already-scaled floats can change near-axis vertex ordering/topology.
    source=loft('_BAK_SOURCE_',coarse['beak'],1,'BEAK',orange)
    bpy.context.view_layer.update()
    evaluated=source.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data=evaluated.to_mesh()
    pivot=bpy.data.objects.new('BAK_LowerPivot',None)
    bpy.data.collections['BEAK'].objects.link(pivot)
    pivot.location=Vector(cfg['lower_pivot_m'])*scale
    pivot.empty_display_type='PLAIN_AXES'
    pivot.empty_display_size=.006*scale
    pivot['opening_axis']=cfg['opening_axis']
    pivot['final_control']='beak_open in the later perched-avatar rig'
    point=Vector(cfg['split_plane_point_m'])
    normal=Vector(cfg['split_plane_normal']).normalized()
    try:
        for kind,upper in [('Upper',True),('Lower',False)]:
            bm=bmesh.new()
            bm.from_mesh(data)
            cut=point+normal*cfg['closed_seam_gap_m']/2*(1 if upper else -1)
            result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                dist=1e-8,plane_co=cut,plane_no=normal,clear_inner=upper,clear_outer=not upper)
            edges=[e for e in bm.edges if e.is_boundary]
            filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces']
            if len(filled)!=1:
                bm.free()
                raise RuntimeError(f'Beak {kind} split must produce one planar inner cap; got {len(filled)}, boundary edges {len(edges)}')
            vertices,faces=stable_mesh(bm)
            bm.free()
            vertices=[tuple(Vector(p)*scale) for p in vertices]
            if not upper: vertices=[tuple(Vector(p)-pivot.location) for p in vertices]
            obj=mesh('BAK_'+kind,vertices,faces,'BEAK',orange)
            obj.data.materials.append(interior)
            for poly in obj.data.polygons:
                points=[Vector(vertices[i])+(pivot.location if not upper else Vector()) for i in poly.vertices]
                if all(abs((p-cut*scale).dot(normal))<1e-7*scale for p in points):
                    poly.material_index=1
                    poly.use_smooth=False
            if not upper:
                obj.parent=pivot
                obj.location=(0,0,0)
            obj['status']='beak_geometry_goal_17'
            obj['parameter_source']='design/beak.json + frozen design/proportions.json/beak'
            obj['inner_cap']='planar rigid jaw closure; deformation is rigid hinge rotation'
    finally:
        evaluated.to_mesh_clear()
        clean('_BAK_SOURCE_')
    clean('BLK_Beak')
    bpy.context.scene['beak_parameters']='design/beak.json'
    set_open(root,0)
