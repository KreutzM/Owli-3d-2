"""Inspect actual #16 meshes and exercise nonlinear lids, coverage and gaze pivots."""
import hashlib
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from mathutils.kdtree import KDTree
from face_geometry import config, set_blink
from primary_geometry import source_tree


def digest_part(obj):
    payload={'matrix':[list(row) for row in obj.matrix_world],
             'vertices':[list(v.co) for v in obj.data.vertices],
             'faces':[list(p.vertices) for p in obj.data.polygons],
             'materials':[m.name for m in obj.data.materials],
             'groups':[[[g.group,g.weight] for g in v.groups] for v in obj.data.vertices],
             'modifiers':[(m.name,m.type,getattr(m,'levels',None),getattr(m,'render_levels',None)) for m in obj.modifiers]}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def audit(obj):
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    try:
        assert all(e.is_manifold and e.is_contiguous for e in bm.edges),obj.name+': open/inconsistent surface'
        assert all(f.calc_area()>1e-12 for f in bm.faces),obj.name+': degenerate face'
        assert bm.calc_volume(signed=True)>0,obj.name+': inward surface'
        visited=set()
        pending=[bm.verts[0]]
        while pending:
            v=pending.pop()
            if v.index in visited: continue
            visited.add(v.index)
            pending.extend(e.other_vert(v) for e in v.link_edges)
        assert len(visited)==len(bm.verts),obj.name+': disconnected mesh'
        kd=KDTree(len(bm.verts))
        for v in bm.verts: kd.insert(v.co,v.index)
        kd.balance()
        assert all(len(kd.find_range(v.co,1e-7))==1 for v in bm.verts),obj.name+': duplicate vertex'
        tree=BVHTree.FromBMesh(bm)
        hits=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)]
        assert not hits,(obj.name,'self intersections',hits[:5])
        euler=len(bm.verts)-len(bm.edges)+len(bm.faces)
        expected=0 if obj.name.startswith(('FAC_Iris_','FAC_Mask_')) else 2
        assert euler==expected,(obj.name,euler,expected)
        if obj.name.startswith('FAC_Lid_'):
            assert all(len(f.verts)==4 for f in bm.faces),'Lid cage must stay all quad'
        return {'vertices':len(bm.verts),'polygons':len(bm.faces),'closed_connected':True,
                'outward_consistent_normals':True,'self_intersections':0,'duplicate_vertices':0,
                'euler_characteristic':euler,'volume_m3':bm.calc_volume(signed=True),
                'minimum_polygon_area_m2':min(f.calc_area() for f in bm.faces)}
    finally: bm.free()


def inspect(root):
    coarse,face,scale=config(root)
    expected={f'FAC_{part}_{side}' for part in ('Globe','Iris','Pupil','Cornea','Mask','Lid_Upper','Lid_Lower','EyeAim') for side in ('L','R')}|{'FAC_MaskBridge'}
    assert {o.name for o in bpy.data.objects if o.name.startswith('FAC_')}==expected
    assert not any(o.name.startswith(('BLK_Eye_','BLK_IrisGuide_','BLK_PupilGuide_','BLK_Mask_','BLK_MaskBridge')) for o in bpy.data.objects)
    assert not any(o.type=='ARMATURE' for o in bpy.data.objects),'Final rig is outside #16'
    result={'meshes':{},'eye_centers_m':{},'collision_pairs':{}}
    for name in sorted(expected):
        obj=bpy.data.objects[name]
        if obj.type=='MESH': result['meshes'][name]=audit(obj)
    eye=coarse['eyes']
    for side,sign in (('L',-1),('R',1)):
        pivot=bpy.data.objects['FAC_EyeAim_'+side]
        center=Vector((sign*eye['half_spacing'],eye['depth'],eye['height']))*scale
        assert (pivot.location-center).length<1e-7
        assert all(abs(x)<1e-8 for x in pivot.rotation_euler)
        result['eye_centers_m'][side]=list(center)
        radii={'Globe':(eye['radius'],eye['radius']),
               'Iris':(eye['radius']+face['iris_radius_offset_m']-face['iris_thickness_m'],eye['radius']+face['iris_radius_offset_m']),
               'Pupil':(eye['radius']+face['pupil_radius_offset_m']-.00015,eye['radius']+face['pupil_radius_offset_m']),
               'Cornea':(eye['radius']+face['cornea_radius_offset_m']-face['cornea_thickness_m'],eye['radius']+face['cornea_radius_offset_m'])}
        layers=[]
        for part,(low,high) in radii.items():
            obj=bpy.data.objects[f'FAC_{part}_{side}']
            assert obj.parent==pivot and obj.location.length<1e-8
            assert all(abs(x-1)<1e-8 for x in obj.scale)
            assert all(low*scale-2e-7*scale<=v.co.length<=high*scale+2e-7*scale for v in obj.data.vertices),(part,'radius changed',low,high,scale,min(v.co.length for v in obj.data.vertices),max(v.co.length for v in obj.data.vertices))
            layers.append(obj)
        assert len({o.data.as_pointer() for o in layers})==4
        for a_index,a in enumerate(layers):
            for b in layers[a_index+1:]:
                overlaps=source_tree(a)[0].overlap(source_tree(b)[0])
                assert not overlaps,(a.name,b.name,'layer collision',overlaps[:3])
                result['collision_pairs'][a.name+'/'+b.name]=0
    masks=[bpy.data.objects['FAC_Mask_'+s] for s in ('L','R')]+[bpy.data.objects['FAC_MaskBridge']]
    for mask in masks:
        for target in [bpy.data.objects['BLK_Beak']]+[bpy.data.objects[f'FAC_{p}_{s}'] for p in ('Globe','Iris','Pupil','Cornea') for s in ('L','R')]:
            hits=source_tree(mask)[0].overlap(source_tree(target)[0])
            assert not hits,(mask.name,target.name,'mask collision',hits[:3])
            result['collision_pairs'][mask.name+'/'+target.name]=0
    for side in ('L','R'):
        toes={o.name for o in bpy.data.objects if o.name.startswith('GUIDE_Toe_'+side+'_')}
        assert toes=={f'GUIDE_Toe_{side}_Front_{i}' for i in (1,2,3)}|{f'GUIDE_Toe_{side}_Rear_1'}
    result['toe_rule']='3 forward + 1 rear per foot, preserved'
    return result


def exercise(root):
    coarse,face,scale=config(root)
    radius=coarse['eyes']['radius']*scale
    cornea_radius=(coarse['eyes']['radius']+face['cornea_radius_offset_m'])*scale
    minimum=float('inf')
    samples=sorted(set(face['blink_samples']+[i/40 for i in range(41)]))
    result={'blink_samples':samples,'minimum_triangle_clearance_m':{},'closed_coverage_rays':0}
    try:
        for value in samples:
            set_blink(root,value)
            for side in ('L','R'):
                center=bpy.data.objects['FAC_EyeAim_'+side].location
                for kind in ('Upper','Lower'):
                    obj=bpy.data.objects[f'FAC_Lid_{kind}_{side}']
                    try: audit(obj)
                    except AssertionError as error: raise AssertionError((value,str(error))) from error
                    triangles=source_tree(obj)[3]
                    # Exact closest point on every rendered triangle, not just cage vertices.
                    clearance=min((closest_point_on_tri(center,*tri)-center).length-cornea_radius for tri in triangles)
                    minimum=min(minimum,clearance)
                    assert clearance>=face['minimum_surface_clearance_m']*scale,(value,obj.name,'lid/cornea clearance',clearance)
                    assert not source_tree(obj)[0].overlap(source_tree(bpy.data.objects['FAC_Cornea_'+side])[0]),(value,obj.name,'cornea intersection')
                    result['minimum_triangle_clearance_m'][f'{value:.3f}/{kind}/{side}']=clearance
        set_blink(root,1)
        count=face['angular_segments']//2+1
        for side in ('L','R'):
            upper,lower=[bpy.data.objects[f'FAC_Lid_{k}_{side}'] for k in ('Upper','Lower')]
            n=len(upper.data.vertices)//2
            for offset in (0,n):
                assert all((upper.data.vertices[offset+i].co-lower.data.vertices[offset+i].co).length<1e-7 for i in range(count)),side+': full blink seam gap'
            center=bpy.data.objects['FAC_EyeAim_'+side].location
            trees=[source_tree(o)[0] for o in (upper,lower)]
            # Dense front rays cover the whole cornea cap, including the meeting seam.
            r=cornea_radius*math.sin(face['cornea_angle_rad'])
            for iz in range(-40,41):
                for ix in range(-40,41):
                    x,z=ix*r/40,iz*r/40
                    if x*x+z*z>r*r: continue
                    origin=center+Vector((x,.2*scale,z))
                    hits=[t.ray_cast(origin,Vector((0,-1,0)),.4*scale) for t in trees]
                    assert any(h[0] is not None and (h[0]-center).length>radius for h in hits),(side,ix,iz,'closed blink exposes eye')
                    result['closed_coverage_rays']+=1
        result['full_close_front_and_back_seam_gap_m']=0
        result['minimum_clearance_m']=minimum
        # Probe each actual aim pivot through +/- yaw and pitch. Rigid child layers follow.
        set_blink(root,0)
        result['gaze_probes']=[]
        for axis in ('X','Z'):
            for sign in (-1,1):
                angle=math.radians(face['aim_probe_degrees'])*sign
                for side in ('L','R'):
                    pivot=bpy.data.objects['FAC_EyeAim_'+side]
                    pivot.rotation_euler[0 if axis=='X' else 2]=angle
                bpy.context.view_layer.update()
                for side in ('L','R'):
                    cornea=bpy.data.objects['FAC_Cornea_'+side]
                    for target in [bpy.data.objects[f'FAC_Lid_{k}_{side}'] for k in ('Upper','Lower')]+[bpy.data.objects['FAC_Mask_'+s] for s in ('L','R')]+[bpy.data.objects['FAC_MaskBridge']]:
                        assert not source_tree(cornea)[0].overlap(source_tree(target)[0]),(axis,sign,cornea.name,target.name,'gaze collision')
                    for part in ('Globe','Iris','Pupil','Cornea'):
                        obj=bpy.data.objects[f'FAC_{part}_{side}']
                        assert (obj.matrix_world.translation-bpy.data.objects['FAC_EyeAim_'+side].location).length<1e-7
                result['gaze_probes'].append({'axis':axis,'degrees':face['aim_probe_degrees']*sign,'no_collisions':True})
                for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
                bpy.context.view_layer.update()
    finally:
        for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
        set_blink(root,0)
    return result


if __name__=='__main__':
    root=Path.cwd()
    result=inspect(root)
    result['probes']=exercise(root)
    print(json.dumps(result,indent=2))
