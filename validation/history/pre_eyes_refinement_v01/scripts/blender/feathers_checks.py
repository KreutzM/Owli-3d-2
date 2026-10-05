"""#6 actual cage, attachment, symmetric geometry and functional pose probes."""
import hashlib
import json
import math
import bpy
from mathutils import Vector
from feathers_geometry import config,set_gesture,REMOVED
from verify_face import audit,digest_part,exercise as face_exercise
from verify_beak import exercise as beak_exercise
from verify_feet import inspect as feet_inspect
from review_fixes_checks import triangle_audit
from primary_geometry import source_tree
from face_geometry import set_blink
from beak_geometry import set_open
from validation_setup import studio_snapshot,read_config,frame_bounds


def inventory():
    names = {'FTH_WingPrimary_'+s for s in ('L','R')}|{'FTH_TailPrimary'}
    names |= {f'FTH_Wing_{r}_{i}_{s}' for r in ('Upper','Lower') for i in range(3) for s in ('L','R')}
    names |= {f'FTH_{r}_{s}' for r in ('HeadUpper','HeadMiddle','HeadLower','BodyUpper','BodyMiddle','BodyLower','CreamUpper','CreamMiddle','CreamLower','Orange','Flank') for s in ('L','R')}
    names |= {'FTH_TailCenter'}|{f'FTH_Tail{r}_{s}' for r in ('Inner','Outer') for s in ('L','R')}
    names |= {f'FTH_Face{r}_{s}' for r in ('Outer','Cheek','Bridge') for s in ('L','R')}
    names |= {'FTH_HeadCenter','FTH_BodyCenter','FTH_ChestCenter'}
    return names


def hashes():
    return {o.name:digest_part(o) for o in bpy.context.scene.objects if o.type=='MESH'}


def inspect(root):
    _,cfg,scale = config(root)
    names = inventory()
    assert {o.name for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('FTH_')}==names
    assert not any(n in bpy.data.objects for n in REMOVED)
    assert not any(o.type=='ARMATURE' for o in bpy.data.objects) and not bpy.data.actions
    result = {'geometry_sha256':hashes(),'new_meshes':{},'bindings':{},'symmetry':{},'root_contacts':{},'leaf_roots':{},
              'feet':feet_inspect(root),'studio':studio_snapshot()}
    for name in sorted(names):
        obj = bpy.data.objects[name]
        result['new_meshes'][name] = {'cage':audit(obj),'cage_triangles':triangle_audit(obj),
                                     'evaluated_triangles':triangle_audit(obj,True)}
        assert all(len(p.vertices)==4 for p in obj.data.polygons),(name,'quad editable cage required')
        data = {'parent':obj.parent.name if obj.parent else None,
                'collections':sorted(c.name for c in obj.users_collection),
                'vertex_groups':[g.name for g in obj.vertex_groups],
                'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in obj.modifiers],
                'part':obj.get('part','primary')}
        if name.startswith('FTH_Wing'):
            side = name[-1]
            pivot = bpy.data.objects['FTH_WingRoot_'+side]
            expected = Vector(((-1 if side=='L' else 1)*cfg['wing_root_R_m'][0],*cfg['wing_root_R_m'][1:]))*scale
            assert obj.parent==pivot and (pivot.location-expected).length<1e-7
            assert all(abs(x)<1e-9 for x in pivot.rotation_euler)
            assert data['vertex_groups']==['wing_gesture']
            rest = obj.data.attributes['fth_rest']
            assert len(rest.data)==len(obj.data.vertices)
            assert all((p.vector-v.co).length<1e-9 for p,v in zip(rest.data,obj.data.vertices))
            data['rest_sha256'] = hashlib.sha256(json.dumps([list(p.vector) for p in rest.data]).encode()).hexdigest()
            weights = [obj.vertex_groups['wing_gesture'].weight(v.index) for v in obj.data.vertices]
            assert min(weights)>=0 and max(weights)==1
            data['minimum_weight'],data['maximum_weight'] = min(weights),max(weights)
        result['bindings'][name] = data
        if 'part' in obj:
            count = cfg['leaf_cross_segments']+1
            if name.startswith('FTH_Wing'):
                support = 'FTH_WingPrimary_'+name[-1]
            else:
                support = obj['root_support']
            tree = source_tree(bpy.data.objects[support])[0]
            n = len(obj.data.vertices)//2
            front = [obj.matrix_world@v.co for v in list(obj.data.vertices)[:count]]
            back = [obj.matrix_world@v.co for v in list(obj.data.vertices)[n:n+count]]
            distances = [tree.find_nearest(p)[3] for p in front]
            signed = [(p-hit).dot(normal) for p in back for hit,normal,_,_ in [tree.find_nearest(p)]]
            assert max(distances)<.0015*scale,(name,'root floats off support',max(distances))
            assert min(signed)<-.0001*scale,(name,'back root lacks real embedding',min(signed))
            result['leaf_roots'][name] = {'support':support,'samples':count,
                 'embedded_back_samples':sum(d<-.0001*scale for d in signed),
                 'maximum_front_root_distance_m':max(distances),'minimum_back_signed_distance_m':min(signed)}
        if name.endswith('_R'):
            other = bpy.data.objects[name[:-1]+'L']
            points = [obj.matrix_world@v.co for v in obj.data.vertices]
            reflected = [other.matrix_world@v.co for v in other.data.vertices]
            assert len(points)==len(reflected)
            maximum = max((Vector((-a.x,a.y,a.z))-b).length for a,b in zip(points,reflected))
            assert maximum<2e-6*scale,(name,'asymmetric geometry',maximum)
            result['symmetry'][name] = {'vertices':len(points),'maximum_mirror_deviation_m':maximum}
    # Measure intentional shoulder embedding into actual body, rather than only
    # accepting an attachment label. Upper neutral cages penetrate the skin seat.
    body = source_tree(bpy.data.objects['PRI_HeadNeckTorso'])[0]
    for side in ('L','R'):
        wing = bpy.data.objects['FTH_WingPrimary_'+side]
        roots = [wing.matrix_world@v.co for v in wing.data.vertices if wing.vertex_groups['wing_gesture'].weight(v.index)==0]
        distances = [(p-hit).dot(n) for p in roots for hit,n,_,_ in [body.find_nearest(p)]]
        assert len(roots)>32 and min(distances)<-.001*scale,(side,'shoulder lacks real embedding')
        result['root_contacts'][side] = {'fixed_root_vertices':len(roots),'minimum_signed_nearest_distance_m':min(distances),
                                        'maximum_signed_nearest_distance_m':max(distances)}
    cfg_views = read_config(root)
    result['framing'] = frame_bounds(cfg_views,[bpy.data.objects[v['name']] for v in cfg_views['views']])
    result['counts'] = {'objects':len(bpy.context.scene.objects),'meshes':len(hashes()),'new_meshes':len(names),
                        'feather_leaves':sum('part' in bpy.data.objects[n] for n in names),'armatures':0,'actions':0}
    return result


def feather_function_probes(root):
    """All new meshes included explicitly, including six cream strips omitted by old probes."""
    new = [bpy.data.objects[n] for n in sorted(inventory())]
    targets = {o.name:source_tree(o)[0] for o in new}
    result = {'blink_samples':[i/40 for i in range(41)],'blink_collision_checks':0,
              'gaze_probes':[],'beak_samples':[i/40 for i in range(41)],'beak_collision_checks':0}
    try:
        for value in result['blink_samples']:
            set_blink(root,value)
            for side in ('L','R'):
                for kind in ('Upper','Lower'):
                    obj = bpy.data.objects[f'FAC_Lid_{kind}_{side}']
                    tree = source_tree(obj)[0]
                    for name,target in targets.items():
                        hits = tree.overlap(target)
                        assert not hits,(value,obj.name,name,'lid/feather collision',hits[:3])
                        result['blink_collision_checks'] += 1
        set_blink(root,0)
        for axis in (0,2):
            for degrees in (-12,12):
                for side in ('L','R'):
                    bpy.data.objects['FAC_EyeAim_'+side].rotation_euler[axis] = math.radians(degrees)
                bpy.context.view_layer.update()
                checks = 0
                for side in ('L','R'):
                    for part in ('Globe','Iris','Pupil','Cornea'):
                        obj = bpy.data.objects[f'FAC_{part}_{side}']
                        own = source_tree(obj)[0]
                        for name,target in targets.items():
                            hits = own.overlap(target)
                            assert not hits,(axis,degrees,obj.name,name,'gaze/feather collision',hits[:3])
                            checks += 1
                result['gaze_probes'].append({'axis':'X' if axis==0 else 'Z','degrees':degrees,'collision_checks':checks})
                for side in ('L','R'):
                    bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
                bpy.context.view_layer.update()
        for value in result['beak_samples']:
            set_open(root,value)
            for kind in ('Upper','Lower'):
                obj = bpy.data.objects['BAK_'+kind]
                own = source_tree(obj)[0]
                for name,target in targets.items():
                    hits = own.overlap(target)
                    assert not hits,(value,obj.name,name,'beak/feather collision',hits[:3])
                    result['beak_collision_checks'] += 1
    finally:
        set_blink(root,0)
        set_open(root,0)
        for side in ('L','R'):
            bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
        bpy.context.view_layer.update()
    result['target_meshes'] = sorted(targets)
    return result


def gesture_probes(root):
    before = hashes()
    points = {n:[o.matrix_world@v.co for v in o.data.vertices] for n in inventory()
              for o in [bpy.data.objects[n]] if n.startswith('FTH_Wing')}
    result = {'states':[],'neutral_restored':False}
    try:
        for left,right in ((.5,0),(1,0),(0,.5),(0,1),(.5,.5),(1,1)):
            set_gesture(root,left,right)
            state = {'left':left,'right':right,'parts':{},'foot_collision_checks':0}
            feet = {o.name:source_tree(o)[0] for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('GRP_')}
            for n,original in points.items():
                obj = bpy.data.objects[n]
                actual = [obj.matrix_world@v.co for v in obj.data.vertices]
                motion = [(a-b).length for a,b in zip(actual,original)]
                value = left if n.endswith('_L') else right
                assert (max(motion)>.003) if value else max(motion)<1e-9,(n,'gesture response',value,max(motion))
                fixed = [motion[i] for i,v in enumerate(obj.data.vertices) if obj.vertex_groups['wing_gesture'].weight(v.index)==0]
                assert max(fixed,default=0)<1e-9,(n,'detached shoulder root')
                state['parts'][n] = {'maximum_vertex_displacement_m':max(motion),'fixed_root_drift_m':max(fixed,default=0),
                                      'cage':audit(obj),'triangle_interiors':triangle_audit(obj)}
                own = source_tree(obj)[0]
                for name,tree in feet.items():
                    assert not own.overlap(tree),(n,name,'gesture cuts feet/perch')
                    state['foot_collision_checks'] += 1
            assert all(digest_part(bpy.data.objects[n])==h for n,h in before.items() if not n.startswith('FTH_Wing'))
            result['states'].append(state)
    finally:
        set_gesture(root,0,0)
    assert hashes()==before,'Gesture neutral restoration differs'
    result['neutral_restored'] = True
    return result


def exercise(root):
    return {'blink_and_gaze':face_exercise(root),'beak_opening':beak_exercise(root),
            'feather_function':feather_function_probes(root),'wing_gestures':gesture_probes(root)}
