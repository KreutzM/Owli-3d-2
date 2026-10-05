"""Actual #19 layer, shader, full preserved mesh state and motion inspection."""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri
from eyes_geometry import ROLES, LIDS, SOCKETS, config, set_blink
from materials_geometry import EYES
from materials_checks import inspect as materials_inspect, exercise as materials_exercise
from materials_checks import full_material, mesh_geometry, digest, properties, shape_hashes
from review_fixes_checks import triangle_audit
from verify_face import audit
from primary_geometry import source_tree


def layer_data(layer):
    fields = ({p.identifier for p in layer.data[0].bl_rna.properties}-{'rna_type'}) if len(layer.data) else set()
    return {'name':layer.name, 'data_type':getattr(layer, 'data_type', None),
            'domain':getattr(layer, 'domain', None),
            'data':[{name:list(getattr(item, name)) if not isinstance(getattr(item, name), (bool,int,float,str))
                     else getattr(item, name) for name in sorted(fields)} for item in layer.data]}


def mesh_state(obj):
    """Full runtime state, including actual UVs/rest attributes excluded by cage hashes."""
    return {'geometry':mesh_geometry(obj), 'materials':{m.name:full_material(m) for m in obj.data.materials},
            'slots':[m.name for m in obj.data.materials],
            'polygon_indices':[p.material_index for p in obj.data.polygons],
            'uv':{a.name:layer_data(a) for a in obj.data.uv_layers},
            'color':{a.name:layer_data(a) for a in obj.data.color_attributes},
            'attributes':{a.name:layer_data(a) for a in obj.data.attributes},
            'shape_keys':None if not obj.data.shape_keys else
                [[k.name,[list(v.co) for v in k.data]] for k in obj.data.shape_keys.key_blocks]}


def normals_state(obj):
    """Actual ordered corner normals, including authored split normals."""
    mesh = obj.data
    return {'has_custom_normals':mesh.has_custom_normals, 'domain':mesh.normals_domain,
            'loop_vertices':[loop.vertex_index for loop in mesh.loops],
            'vectors':[list(normal.vector) for normal in mesh.corner_normals]}


def normals_audit(obj):
    state = normals_state(obj)
    vectors = state['vectors']
    assert len(vectors) == len(obj.data.loops), (obj.name, 'incomplete corner normal coverage')
    assert all(math.isfinite(value) for vector in vectors for value in vector), (obj.name, 'nonfinite normal')
    error = max(abs(Vector(vector).length-1) for vector in vectors)
    assert error < 1e-5, (obj.name, 'nonunit normal', error)
    return {'has_custom_normals':state['has_custom_normals'], 'domain':state['domain'],
            'loop_count':len(obj.data.loops), 'normal_count':len(vectors),
            'maximum_unit_error':error}


def state_snapshot():
    meshes = {o.name:mesh_state(o) for o in bpy.context.scene.objects if o.type == 'MESH'}
    return {'unchanged_non_eye_sha256':{name:digest(state) for name,state in meshes.items() if name not in EYES},
            'uv_state_sha256':{name:digest(state['uv']) for name,state in meshes.items()},
            'attributes_state_sha256':{name:digest(state['attributes']) for name,state in meshes.items()},
            'normals_state_sha256':{name:digest(normals_state(bpy.data.objects[name])) for name in meshes},
            'eye_local_shape_sha256':{name:digest({key:value for key,value in meshes[name]['geometry'].items()
                                                 if key != 'matrix'}) for name in EYES},
            'pivot_state_sha256':{o.name:digest(properties(o)) for o in bpy.data.objects if o.type=='EMPTY'}}


def inspect(root):
    result = materials_inspect(root)
    result.update(state_snapshot())
    result['eye_materials'] = {role:{'graph':full_material(bpy.data.materials['MAT_'+role]),
                              'shader_sha256':digest(full_material(bpy.data.materials['MAT_'+role]))} for role in ROLES}
    result['eye_geometry'] = {name:{'cage':audit(bpy.data.objects[name]),
                                  'cage_triangles':triangle_audit(bpy.data.objects[name]),
                                  'evaluated_triangles':triangle_audit(bpy.data.objects[name], True)} for name in EYES}
    result['socket_geometry'] = {name:{'cage':audit(bpy.data.objects[name]),
                                     'cage_triangles':triangle_audit(bpy.data.objects[name]),
                                     'evaluated_triangles':triangle_audit(bpy.data.objects[name], True)} for name in SOCKETS}
    result['socket_state_sha256'] = {name:digest(mesh_state(bpy.data.objects[name])) for name in SOCKETS}
    result['normals_audit'] = {obj.name:normals_audit(obj) for obj in bpy.context.scene.objects if obj.type=='MESH'}
    result['eye_layers'] = {}
    for side in ('L', 'R'):
        pivot = bpy.data.objects['FAC_EyeAim_'+side]
        parts = ('Globe', 'Iris', 'Pupil', 'Cornea')
        radii = {part:[min(v.co.length for v in bpy.data.objects[f'FAC_{part}_{side}'].data.vertices),
                       max(v.co.length for v in bpy.data.objects[f'FAC_{part}_{side}'].data.vertices)] for part in parts}
        projected = {part:max(math.hypot(v.co.x, v.co.z) for v in bpy.data.objects[f'FAC_{part}_{side}'].data.vertices)
                     for part in ('Iris', 'Pupil')}
        pairs = {}
        for i, first in enumerate(parts):
            for second in parts[i+1:]:
                hits = source_tree(bpy.data.objects[f'FAC_{first}_{side}'])[0].overlap(source_tree(bpy.data.objects[f'FAC_{second}_{side}'])[0])
                assert not hits, (side, first, second, 'optical layer intersection', hits[:3])
                pairs[first+'/'+second] = 0
        result['eye_layers'][side] = {'center_m':list(pivot.matrix_world.translation), 'radii_m':radii,
             'projected_iris_radius_m':projected['Iris'], 'projected_pupil_radius_m':projected['Pupil'],
             'projected_pupil_iris_ratio':projected['Pupil']/projected['Iris'], 'layer_collision_pairs':pairs}
    result['counts']['eye_materials'] = len(ROLES)
    return result


def eye_function(root):
    """Actual outer radius and all eight eye surfaces remain safe under blink/aim."""
    before = shape_hashes()
    before_normals = {name:digest(normals_state(bpy.data.objects[name])) for name in LIDS}
    actual_radii = {side:max(v.co.length for v in bpy.data.objects['FAC_Cornea_'+side].data.vertices) for side in ('L','R')}
    eyes = {name:source_tree(bpy.data.objects[name])[0] for name in EYES}
    result = {'target_meshes':list(EYES), 'actual_cornea_max_radius_m':actual_radii,
              'blink_samples':[i/40 for i in range(41)], 'minimum_triangle_clearance_m':{},
              'blink_eye_collision_checks':0, 'gaze_probes':[], 'neutral_restored':False,
              'lid_pose_normals_sha256':{}, 'neutral_normals_restored':False}
    try:
        for value in result['blink_samples']:
            set_blink(root, value)
            result['lid_pose_normals_sha256'][f'{value:.3f}'] = {
                name:digest(normals_state(bpy.data.objects[name])) for name in LIDS}
            for side in ('L', 'R'):
                center = bpy.data.objects['FAC_EyeAim_'+side].matrix_world.translation
                for kind in ('Upper', 'Lower'):
                    lid = bpy.data.objects[f'FAC_Lid_{kind}_{side}']
                    tree, _, _, triangles = source_tree(lid)
                    clearance = min((closest_point_on_tri(center,*triangle)-center).length-actual_radii[side] for triangle in triangles)
                    assert clearance >= .0003, (value, lid.name, 'actual cornea clearance', clearance)
                    result['minimum_triangle_clearance_m'][f'{value:.3f}/{kind}/{side}'] = clearance
                    for name, target in eyes.items():
                        assert not tree.overlap(target), (value, lid.name, name, 'blink/eye collision')
                        result['blink_eye_collision_checks'] += 1
        set_blink(root, 0)
        for axis in (0, 2):
            for degrees in (-12, 12):
                for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler[axis] = math.radians(degrees)
                bpy.context.view_layer.update()
                targets = {name:source_tree(bpy.data.objects[name])[0] for name in
                           ('FAC_Mask_L','FAC_Mask_R','FAC_MaskBridge','FAC_Lid_Upper_L','FAC_Lid_Lower_L',
                            'FAC_Lid_Upper_R','FAC_Lid_Lower_R','BAK_Upper','BAK_Lower')}
                checks = 0
                for name in EYES:
                    tree = source_tree(bpy.data.objects[name])[0]
                    for target, other in targets.items():
                        assert not tree.overlap(other), (axis, degrees, name, target, 'eye aim collision')
                        checks += 1
                result['gaze_probes'].append({'axis':'X' if axis==0 else 'Z', 'degrees':degrees,
                                             'target_meshes':list(targets), 'collision_checks':checks})
                for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler = (0,0,0)
                bpy.context.view_layer.update()
    finally:
        set_blink(root, 0)
        for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler = (0,0,0)
        bpy.context.view_layer.update()
    assert before == shape_hashes(), 'Eye motion neutral restoration drift'
    after_normals = {name:digest(normals_state(bpy.data.objects[name])) for name in LIDS}
    assert before_normals == after_normals, 'Eye motion neutral corner-normal restoration drift'
    assert result['lid_pose_normals_sha256']['0.000'] != result['lid_pose_normals_sha256']['1.000'], 'Lid normals failed to follow the actual blink'
    result['neutral_normals_restored'] = True
    result['minimum_clearance_m'] = min(result['minimum_triangle_clearance_m'].values())
    result['neutral_restored'] = True
    return result


def exercise(root):
    result = materials_exercise(root)
    result['eye_function'] = eye_function(root)
    return result
