"""Inspect real jaw cages/pivot and exercise opening against the accepted face."""
import math
import bpy
from mathutils import Vector
from beak_geometry import config,set_open
from verify_face import audit,digest_part
from primary_geometry import source_tree


def inspect(root):
    _,cfg,scale=config(root)
    names={o.name for o in bpy.data.objects if o.name.startswith('BAK_')}
    assert names=={'BAK_Upper','BAK_Lower','BAK_LowerPivot'},names
    assert 'BLK_Beak' not in bpy.data.objects
    assert not any(o.name.startswith('_BAK_SOURCE_') for o in bpy.data.objects)
    assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
    upper,lower=[bpy.data.objects['BAK_'+kind] for kind in ('Upper','Lower')]
    pivot=bpy.data.objects['BAK_LowerPivot']
    assert upper.data!=lower.data and upper.parent is None and lower.parent==pivot
    assert (pivot.location-Vector(cfg['lower_pivot_m'])*scale).length<1e-7
    assert all(abs(x)<1e-8 for x in pivot.rotation_euler),'Delivery must be closed'
    assert upper.location.length==0 and lower.location.length==0
    result={'meshes':{o.name:audit(o) for o in (upper,lower)},'lower_pivot_m':list(pivot.location),'opening_axis':'-X','maximum_open_degrees':cfg['maximum_open_degrees']}
    p=Vector(cfg['split_plane_point_m'])*scale
    n=Vector(cfg['split_plane_normal']).normalized()
    assert abs((pivot.location-p).dot(n))<1e-7,'Hinge must lie on the jaw separation plane'
    min_y=float('inf')
    for kind,obj in [('Upper',upper),('Lower',lower)]:
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        signed=[(v-p).dot(n) for v in points]
        if kind=='Upper': assert min(signed)>=cfg['closed_seam_gap_m']*scale/2-1e-7
        else: assert max(signed)<=-cfg['closed_seam_gap_m']*scale/2+1e-7
        cap=[v for v,d in zip(points,signed) if abs(abs(d)-cfg['closed_seam_gap_m']*scale/2)<1e-7]
        assert len(cap)>=6,'Missing closed planar interior cap'
        min_y=min(min_y,min(v.y for v in cap))
        result[kind.lower()+'_cap_boundary_vertices']=len(cap)
    assert pivot.location.y<min_y-1e-5*scale,'Hinge behind every cut boundary vertex avoids opening into upper jaw'
    upper_min=min((upper.matrix_world@v.co).z for v in upper.data.vertices)
    lower_min=min((lower.matrix_world@v.co).z for v in lower.data.vertices)
    assert upper_min+.003*scale<lower_min,'Hooked distal tip must belong to fixed upper beak'
    assert result['meshes']['BAK_Lower']['volume_m3']/result['meshes']['BAK_Upper']['volume_m3']>.07,'Lower jaw must be volumetric, not a thin sliver'
    result['hooked_tip_stays_upper']=True
    for side in ('L','R'):
        toes={o.name for o in bpy.data.objects if o.name.startswith('GUIDE_Toe_'+side+'_')}
        assert toes=={f'GUIDE_Toe_{side}_Front_{i}' for i in (1,2,3)}|{f'GUIDE_Toe_{side}_Rear_1'}
    result['toe_rule_3_plus_1']=True
    return result


def exercise(root):
    _,cfg,scale=config(root)
    upper,lower=[bpy.data.objects['BAK_'+kind] for kind in ('Upper','Lower')]
    upper_digest=digest_part(upper)
    targets=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('FAC_','PRI_Head','BLK_Chest','BLK_Forehead'))]
    trees={o.name:source_tree(o)[0] for o in targets+[upper]}
    closed=[lower.matrix_world@v.co for v in lower.data.vertices]
    result={'opening_samples':[i/40 for i in range(41)],'collision_checks':0,'minimum_sampled_mask_clearance_m':float('inf'),'upper_fixed':True}
    try:
        for value in result['opening_samples']:
            set_open(root,value)
            assert abs(bpy.data.objects['BAK_LowerPivot'].rotation_euler.x+math.radians(cfg['maximum_open_degrees'])*value)<1e-7
            assert digest_part(upper)==upper_digest,'Upper jaw moved during lower opening'
            for obj in (upper,lower):
                own=source_tree(obj)[0]
                for target in targets+([upper] if obj==lower else []):
                    hits=own.overlap(trees[target.name])
                    assert not hits,(value,obj.name,target.name,'beak collision',hits[:3])
                    result['collision_checks']+=1
                    if target.name.startswith('FAC_Mask'):
                        # Two-direction cage-vertex sampling complements definitive BVH intersection checks.
                        points=[obj.matrix_world@v.co for v in obj.data.vertices]
                        distances=[trees[target.name].find_nearest(p)[3] for p in points]
                        distances += [own.find_nearest(target.matrix_world@v.co)[3] for v in target.data.vertices]
                        distance=min(distances)
                        assert distance>=cfg['minimum_mask_clearance_m']*scale,(value,obj.name,target.name,'mask clearance',distance)
                        result['minimum_sampled_mask_clearance_m']=min(result['minimum_sampled_mask_clearance_m'],distance)
        opened=[lower.matrix_world@v.co for v in lower.data.vertices]
        displacements=[(a-b).length for a,b in zip(closed,opened)]
        result['maximum_lower_vertex_displacement_m']=max(displacements)
        assert max(displacements)>.005*scale,'Opening must be an actual visible geometric movement'
        front=max(range(len(closed)),key=lambda i:closed[i].y)
        result['front_lower_vertex_drop_m']=closed[front].z-opened[front].z
        assert result['front_lower_vertex_drop_m']>.004*scale,'Lower tip must open downward'
    finally: set_open(root,0)
    return result
