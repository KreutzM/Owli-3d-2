"""Strict Goal 18 assigned shaders, tech/F01 geometry, workers and manual review."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from feathers_gate import (
    load_json, object_shape, table_shape, sequence_shape, validate_shape,
    CAGE_SHAPE, TRIANGLE_SHAPE, FEET_SHAPE, VEC3_SHAPE, FRAME_OBJECT_SHAPE,
    validate_feathers, worker_shape as feather_worker_shape, expected_mesh_names,
)
from delivery_shapes import RELOAD_SHAPES
from materials_contracts import (
    ARCHIVED_STAGE_SHA256, BASELINE_COMMIT, BASELINE_SCENE, BASELINE_SHA256,
    BASELINE_SIZE_BYTES, PROTECTED_SHA256, REFERENCE_AUTHORITY, REFERENCE_NAMES,
    REVIEW_PATH, SCENE_PATH, SOURCES, VIEWS, CRITERIA, EVIDENCE_NAMES,
    MANUAL_EVIDENCE_NAMES, MODES, LABELS,
    BASELINE_ASSIGNMENTS,
    BASELINE_SHAPE_SHA256, BASELINE_EYE_STATE_SHA256, MATERIAL_SHADER_SHA256,
    POLYGON_COUNTS, POLYGON_ASSIGNMENT_SHA256,
)

ROOT = Path(__file__).resolve().parents[1]
EYES = tuple(f'FAC_{part}_{side}' for part in ('Globe', 'Iris', 'Pupil', 'Cornea')
             for side in ('L', 'R'))
CHANGED = tuple(f'FTH_{part}_{side}' for part in ('CreamUpper', 'CreamMiddle', 'CreamLower', 'Orange')
                for side in ('L', 'R'))
REMOVED = tuple(f'BLK_ForeheadNode_{i}' for i in range(5))+tuple(f'BLK_ForeheadLink_{i}' for i in range(4))
ROLES = ('Feather_Navy', 'Feather_Blue', 'Feather_Cyan', 'Feather_Cream', 'Feather_Warm',
         'Keratin_Orange', 'Keratin_Dark', 'Mouth_Interior', 'Perch_Metal', 'Tech_Cyan')
NODE_IDS = ('Hub', 'Top', 'Bottom', 'Inner_L', 'Inner_R', 'Outer_L', 'Outer_R')
LINK_IDS = ('Top', 'Bottom', 'Inner_L', 'Inner_R', 'Outer_L', 'Outer_R')
RING_IDS = ('End_L', 'End_R', 'Stem', 'Base')
PALETTE = {'deep_navy': '#0D1538', 'mid_blue': '#245E8D', 'cyan_reference': '#1EA0C8',
           'cream': '#F4F3E7', 'orange_reference': '#F58C2B'}
RGBA_SHAPE = sequence_shape(4, 'number')
PRINCIPLED_SHAPE = object_shape({
    'base_color': RGBA_SHAPE, 'metallic': 'number', 'roughness': 'number', 'ior': 'number',
    'sheen_weight': 'number', 'anisotropic': 'number', 'emission_color': RGBA_SHAPE,
    'emission_strength': 'number', 'coat_weight': 'number', 'coat_roughness': 'number',
})


def shader_recipe(role):
    nodes = {'SurfaceOutput': 'ShaderNodeOutputMaterial', 'Surface': 'ShaderNodeBsdfPrincipled'}
    links = [['Surface', 'BSDF', 'SurfaceOutput', 'Surface']]
    ramps = {}
    if role != 'Tech_Cyan':
        nodes.update(Coordinates='ShaderNodeTexCoord', GrainDirection='ShaderNodeVectorMath',
                     FineGrain='ShaderNodeTexNoise', SurfaceGrain='ShaderNodeBump')
        links += [['Coordinates', 'Generated', 'GrainDirection', 'Vector'],
                  ['GrainDirection', 'Vector', 'FineGrain', 'Vector'],
                  ['FineGrain', 'Fac', 'SurfaceGrain', 'Height'],
                  ['SurfaceGrain', 'Normal', 'Surface', 'Normal']]
    if role.startswith('Feather'):
        nodes.update(FeatherCoordinates='ShaderNodeUVMap', FeatherAxes='ShaderNodeSeparateXYZ',
                     FeatherGradient='ShaderNodeValToRGB')
        links += [['FeatherCoordinates', 'UV', 'FeatherAxes', 'Vector'],
                  ['FeatherAxes', 'Y', 'FeatherGradient', 'Fac']]
        ramps['FeatherGradient'] = 2
        if role == 'Feather_Warm':
            nodes.update(WarmDiagonal='ShaderNodeValToRGB', WarmTaper='ShaderNodeValToRGB',
                         IntegratedWarmAccent='ShaderNodeMixRGB')
            links += [['FeatherAxes', 'X', 'WarmDiagonal', 'Fac'],
                      ['FeatherAxes', 'Y', 'WarmTaper', 'Fac'],
                      ['WarmTaper', 'Color', 'IntegratedWarmAccent', 'Fac'],
                      ['FeatherGradient', 'Color', 'IntegratedWarmAccent', 'Color1'],
                      ['WarmDiagonal', 'Color', 'IntegratedWarmAccent', 'Color2'],
                      ['IntegratedWarmAccent', 'Color', 'Surface', 'Base Color']]
            ramps.update(WarmDiagonal=7, WarmTaper=6)
        else:
            links.append(['FeatherGradient', 'Color', 'Surface', 'Base Color'])
    return nodes, sorted(links), ramps


def material_shape(role):
    nodes, links, ramps = shader_recipe(role)
    return object_shape({
        'use_nodes': 'bool', 'node_types': table_shape(nodes, 'str'),
        'links': sequence_shape(len(links), sequence_shape(4, 'str')),
        'principled_inputs': PRINCIPLED_SHAPE,
        'ramps': object_shape({name: object_shape({'interpolation': 'str',
            'stops': sequence_shape(count, {'list': 2, 'items': ['number', RGBA_SHAPE]})})
            for name, count in ramps.items()}),
        'shader_sha256': 'sha256',
    })


def expected_material_values(role, cfg):
    palette = {name: linear(value) for name, value in PALETTE.items()}
    s = cfg['shader']
    bases = {'Feather_Navy': palette['deep_navy'], 'Feather_Blue': palette['mid_blue'],
             'Feather_Cyan': palette['cyan_reference'], 'Feather_Cream': palette['cream'],
             'Feather_Warm': palette['orange_reference'], 'Keratin_Orange': palette['orange_reference'],
             'Keratin_Dark': linear(s['claw_srgb']), 'Mouth_Interior': palette['deep_navy'],
             'Perch_Metal': linear(s['perch_srgb']), 'Tech_Cyan': linear(s['emission_srgb'])}
    base = bases[role]
    roughness = s['feather_roughness'] if role.startswith('Feather') else s['keratin_roughness']
    if role == 'Feather_Cream':
        roughness = s['cream_roughness']
    elif role == 'Mouth_Interior':
        roughness = .6
    elif role == 'Perch_Metal':
        roughness = s['perch_roughness']
    inputs = {'base_color': base, 'metallic': s['perch_metallic'] if role == 'Perch_Metal' else 0,
              'roughness': roughness, 'ior': 1.45, 'coat_weight': 0, 'coat_roughness': .03,
              'sheen_weight': s['sheen_weight'] if role.startswith('Feather') else 0,
              'anisotropic': s['perch_anisotropic'] if role == 'Perch_Metal' else 0,
              'emission_color': base if role == 'Tech_Cyan' else [1, 1, 1, 1],
              'emission_strength': s['emission_strength'] if role == 'Tech_Cyan' else 0}
    ramps = {}
    def ramp(interpolation, stops):
        return {'interpolation': interpolation,
                'stops': [[p, c] for p, c in stops]}
    if role.startswith('Feather'):
        tip = base
        if role == 'Feather_Navy':
            tip = mix(base, palette['mid_blue'], .5)
        elif role == 'Feather_Blue':
            tip = mix(base, palette['cyan_reference'], .42)
        elif role == 'Feather_Cyan':
            tip = mix(base, linear('#7BDAEF'), .4)
        elif role == 'Feather_Cream':
            tip = mix(base, linear('#D7E8ED'), .2)
        root = base if role == 'Feather_Cream' else mix(base, palette['deep_navy'], .14)
        if role == 'Feather_Warm':
            root, tip = palette['cream'], mix(palette['mid_blue'], palette['cyan_reference'], .35)
            ramps['WarmDiagonal'] = ramp('EASE', [(0, palette['cream']), (.25, palette['cream']),
                (.35, linear('#FFD068')), (.5, palette['orange_reference']),
                (.7, linear('#FFD068')), (.86, palette['mid_blue']), (1, palette['mid_blue'])])
            ramps['WarmTaper'] = ramp('LINEAR', [(p, [v, v, v, 1]) for p, v in
                ((0, 0), (.18, .5), (.38, 1), (.64, .85), (.88, .2), (1, 0))])
        ramps['FeatherGradient'] = ramp('LINEAR', [(0, root), (1, tip)])
    return inputs, ramps


def validate_material_semantics(material, role, cfg):
    errors = validate_shape(material, material_shape(role), 'material/'+role)
    if errors:
        return errors
    def need(condition, message):
        if not condition:
            errors.append(message+': '+role)
    nodes, links, _ = shader_recipe(role)
    inputs, ramps = expected_material_values(role, cfg)
    need(material['use_nodes'] is True and material['node_types'] == nodes and material['links'] == links,
         'Missing/incorrect actual connected commissioned shader graph')
    for name, value in inputs.items():
        need(near(material['principled_inputs'][name], value),
             'Wrong sRGB-linear/input value '+name)
    for name, expected in ramps.items():
        actual = material['ramps'][name]
        need(actual['interpolation'] == expected['interpolation'], 'Wrong actual gradient interpolation '+name)
        for index, (a, b) in enumerate(zip(actual['stops'], expected['stops'])):
            need(near(a[0], b[0]) and near(a[1], b[1]),
                 'Wrong sRGB-linear gradient stop '+name+'/'+str(index))
    need(material['shader_sha256'] == MATERIAL_SHADER_SHA256[role],
         'Actual full shader fingerprint differs from authored grain/UV/input recipe')
    p = material['principled_inputs']
    if role.startswith('Feather'):
        need(p['metallic'] == 0 and .4 <= p['roughness'] <= .75, 'Metallic/plastic plumage or cream')
    elif role.startswith('Keratin'):
        need(p['metallic'] == 0 and .2 <= p['roughness'] <= .4, 'Wrong keratin gloss')
    elif role == 'Perch_Metal':
        need(near(p['metallic'], .85) and .2 <= p['roughness'] <= .38 and p['anisotropic'] > .2,
             'Missing restrained actual brushed metal')
    elif role == 'Tech_Cyan':
        need(p['metallic'] == 0 and 1.5 <= p['emission_strength'] <= 4,
             'Missing/excessive cyan emission')
    return errors


def expected_tech_names(cfg):
    """Code owns required geometry families; config may parameterize their shape."""
    if set(cfg['forehead']['nodes']) != set(NODE_IDS) or set(cfg['forehead']['links']) != set(LINK_IDS):
        raise ValueError('Missing/unexpected commissioned forehead network node/link inventory')
    rings = cfg['perch_rings']
    if not isinstance(rings, list) or len(rings) != 4 or {entry['id'] for entry in rings} != set(RING_IDS):
        raise ValueError('Missing/unexpected four restrained perch accent rings')
    if {entry['id'] for entry in cfg['chest_overrides']} != {'CreamUpper', 'CreamMiddle', 'CreamLower', 'Orange'}:
        raise ValueError('Missing complete Cream-V and warm diagonal F01 override inventory')
    return ({'TECH_ForeheadNode_'+name for name in NODE_IDS}
            | {'TECH_ForeheadLink_'+name for name in LINK_IDS}
            | {'TECH_PerchRing_'+name for name in RING_IDS})


def expected_assignments(cfg):
    names = (set(BASELINE_ASSIGNMENTS)-set(REMOVED)) | expected_tech_names(cfg)
    swatch = {'deep_navy': 'Feather_Navy', 'mid_blue': 'Feather_Blue',
              'cyan_reference': 'Feather_Cyan', 'cream': 'Feather_Cream',
              'orange_reference': 'Feather_Warm'}
    result = {}
    for name in sorted(names):
        if name in EYES:
            result[name] = BASELINE_ASSIGNMENTS[name]
            continue
        if name.startswith('TECH_'):
            roles = ['Tech_Cyan']
        elif name.startswith('GRP_Perch'):
            roles = ['Perch_Metal']*len(BASELINE_ASSIGNMENTS[name])
        elif name.startswith('GRP_Claw'):
            roles = ['Keratin_Dark']*len(BASELINE_ASSIGNMENTS[name])
        elif name.startswith('GRP_Foot'):
            roles = ['Keratin_Orange']*len(BASELINE_ASSIGNMENTS[name])
        elif name.startswith('BAK_'):
            roles = ['Keratin_Orange', 'Mouth_Interior']
        else:
            roles = [swatch[slot.removeprefix('BLK_Swatch_')] for slot in BASELINE_ASSIGNMENTS[name]]
        result[name] = ['MAT_'+role for role in roles]
    return result


def linear(hex_color):
    rgb = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    return [value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4
            for value in rgb]+[1.0]


def mix(a, b, value):
    return [x*(1-value)+y*value for x, y in zip(a, b)]


def near(a, b, tolerance=2e-6):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(near(x, y, tolerance) for x, y in zip(a, b))
    return type(a) in (int, float) and type(b) in (int, float) and abs(a-b) <= tolerance


def worker_shape(cfg, baseline, build=False):
    """Recursive schema from commissioned families and fixed historical inventories."""
    feathers = load_json(ROOT/'design/wings_feathers.json')
    old = load_json(ROOT/'validation/reviews/review_fixes_v01/reload_b_checks.json')
    fields = copy.deepcopy(feather_worker_shape(feathers, old)['dict'])
    tech = expected_tech_names(cfg)
    names = set(expected_assignments(cfg))
    fields['geometry_sha256'] = table_shape(names, 'sha256')
    fields['shape_sha256'] = table_shape(names, 'sha256')
    fields['eye_state_sha256'] = table_shape(EYES, 'sha256')
    fields['assignments'] = object_shape({name: object_shape({
        'slots': sequence_shape(len(slots), 'str'),
        'polygon_material_indices': sequence_shape(POLYGON_COUNTS[name], 'int'),
        'unassigned_polygons': 'int'}) for name, slots in expected_assignments(cfg).items()})
    fields['materials'] = object_shape({role: material_shape(role) for role in ROLES})
    fields['tech_meshes'] = table_shape(tech, object_shape({
        'cage': CAGE_SHAPE, 'cage_triangles': TRIANGLE_SHAPE,
        'evaluated_triangles': TRIANGLE_SHAPE, 'kind': 'str', 'support': 'str'}))
    fields['tech_seats'] = table_shape(tech, object_shape({
        'support': 'str', 'samples': 'int', 'maximum_surface_distance_m': 'float'}))
    fields['tech_symmetry'] = table_shape(('TECH_ForeheadNode_Inner_R', 'TECH_ForeheadNode_Outer_R',
        'TECH_ForeheadLink_Inner_R', 'TECH_ForeheadLink_Outer_R', 'TECH_PerchRing_End_R'),
        object_shape({'vertices': 'int', 'maximum_mirror_deviation_m': 'float'}))
    fields['framing'] = table_shape(VIEWS, object_shape({
        'objects': table_shape(names, FRAME_OBJECT_SHAPE), 'object_count': 'int',
        'minimum_image_margin': 'float', 'inside_safe_frame': 'bool'}))
    fields['counts']['dict']['tech_meshes'] = 'int'
    fields['movement']['dict']['tech_function'] = object_shape({
        'target_meshes': sequence_shape(len(tech), 'str'),
        'blink_samples': sequence_shape(41, 'float'), 'blink_collision_checks': 'int',
        'gaze_probes': sequence_shape(4, object_shape({'axis': 'str', 'degrees': 'int', 'collision_checks': 'int'})),
        'beak_samples': sequence_shape(41, 'float'), 'beak_collision_checks': 'int',
        'wing_states': sequence_shape(6, object_shape({'left': 'number', 'right': 'number', 'collision_checks': 'int'})),
        'neutral_restored': 'bool',
    })
    if build:
        unchanged = set(BASELINE_SHAPE_SHA256)-set(CHANGED)-set(REMOVED)
        fields.update(unchanged_shape_sha256=table_shape(unchanged, 'sha256'),
                      baseline_shape_sha256=table_shape(BASELINE_SHAPE_SHA256, 'sha256'),
                      baseline_eye_state_sha256=table_shape(EYES, 'sha256'),
                      repeated_build_identical='bool', datablock_counts=sequence_shape(3, 'int'))
    return object_shape(fields)


RELOAD_FIELDS = ('geometry_sha256', 'new_meshes', 'bindings', 'symmetry', 'root_contacts',
                 'leaf_roots', 'feet', 'studio', 'framing', 'counts', 'shape_sha256',
                 'eye_state_sha256', 'assignments', 'materials', 'tech_meshes', 'tech_seats',
                 'tech_symmetry', 'movement')


def validate_worker_structure(data, cfg, baseline, build=False):
    return validate_shape(data, worker_shape(cfg, baseline, build))


def validate_worker_semantics(data, cfg, baseline, build=False):
    """Measured surfaces, assignments, full trajectories and immutable predecessor."""
    errors = validate_worker_structure(data, cfg, baseline, build)
    if errors:
        return errors
    def need(condition, message):
        if not condition:
            errors.append(message)
    def surface(cage, triangles, name, kind='sphere'):
        need(cage['closed_connected'] is True and cage['outward_consistent_normals'] is True
             and cage['self_intersections'] == cage['duplicate_vertices'] == 0
             and cage['vertices'] > 4 and cage['polygons'] > 4
             and cage['euler_characteristic'] == (0 if kind == 'torus' else 2)
             and cage['volume_m3'] > 0 and cage['minimum_polygon_area_m2'] > 0,
             'Invalid closed editable material/F01/tech surface: '+name)
        need(triangles['triangles'] >= cage['polygons']
             and triangles['adjacent_interiors_included'] is True
             and triangles['interior_crossings'] == 0
             and triangles['minimum_polygon_triangle_normal_dot'] > 0
             and 0 <= triangles['maximum_boundary_inset_m'] < .0001
             and triangles['coplanar_candidate_checks'] >= 0
             and triangles['coplanar_overlap_area_tolerance_m2'] == 1e-12
             and triangles['coplanar_plane_tolerance_m'] == 1e-8,
             'Missing/failed adjacent or coplanar material/F01/tech triangles: '+name)
    tech = expected_tech_names(cfg)
    assignments = expected_assignments(cfg)
    names = set(assignments)
    feathers = set(baseline['new_meshes'])
    wings = {name for name in feathers if name.startswith('FTH_Wing')}
    unchanged = {name: digest for name, digest in BASELINE_SHAPE_SHA256.items()
                 if name not in set(CHANGED) | set(REMOVED)}
    need(all(data['shape_sha256'][name] == digest for name, digest in unchanged.items()),
         'Changed unrelated accepted cage/transform/parent/group/modifier')
    need(data['eye_state_sha256'] == BASELINE_EYE_STATE_SHA256
         and all(data['geometry_sha256'][name] == baseline['geometry_sha256'][name] for name in EYES),
         'Changed actual layered eye shape/slots/polygon assignment/shader before Goal 19')
    need(all(data['shape_sha256'][name] != BASELINE_SHAPE_SHA256[name] for name in CHANGED),
         'F01 delivery did not implement prescribed Cream-V and diagonal warm group geometry')
    if build:
        need(data['baseline_shape_sha256'] == BASELINE_SHAPE_SHA256
             and data['baseline_eye_state_sha256'] == BASELINE_EYE_STATE_SHA256
             and data['unchanged_shape_sha256'] == unchanged
             and data['repeated_build_identical'] is True,
             'Missing actual anchored predecessor or repeat-build/exact preservation')
        need(data['datablock_counts'] == [117, 103, 17], 'Leaked/missing material build datablocks')
    for name, slots in assignments.items():
        actual = data['assignments'][name]
        indices = actual['polygon_material_indices']
        need(actual['slots'] == slots and actual['unassigned_polygons'] == 0
             and all(0 <= value < len(slots) for value in indices),
             'Missing/wrong actual material assignment: '+name)
        need(hashlib.sha256(json.dumps(indices).encode()).hexdigest() == POLYGON_ASSIGNMENT_SHA256[name],
             'Changed actual polygon material distribution: '+name)
    for role, material in data['materials'].items():
        errors += validate_material_semantics(material, role, cfg)
    need(data['bindings'] == baseline['bindings'], 'Changed accepted feather gesture/root binding')
    for side, seat in data['root_contacts'].items():
        old = baseline['root_contacts'][side]
        need(seat['fixed_root_vertices'] == old['fixed_root_vertices']
             and seat['minimum_signed_nearest_distance_m'] < -.001
             and seat['maximum_signed_nearest_distance_m'] >= seat['minimum_signed_nearest_distance_m']
             and near(seat['minimum_signed_nearest_distance_m'], old['minimum_signed_nearest_distance_m'], 2e-7)
             and near(seat['maximum_signed_nearest_distance_m'], old['maximum_signed_nearest_distance_m'], 2e-7),
             'Changed measured accepted wing shoulder attachment: '+side)
    for name, mesh in data['new_meshes'].items():
        surface(mesh['cage'], mesh['cage_triangles'], name)
        surface(mesh['cage'], mesh['evaluated_triangles'], name+' evaluated')
        need(mesh['cage']['polygons'] == POLYGON_COUNTS[name]
             and mesh['cage_triangles']['triangles'] == 2*POLYGON_COUNTS[name],
             'Changed bounded editable quad feather topology: '+name)
        if name in data['symmetry']:
            mirror = data['symmetry'][name]
            need(mirror['vertices'] == mesh['cage']['vertices']
                 and 0 <= mirror['maximum_mirror_deviation_m'] < 2e-6,
                 'Actual reflected F01/feather geometry differs: '+name)
    for name, seat in data['leaf_roots'].items():
        need(seat['support'] == baseline['leaf_roots'][name]['support']
             and seat['samples'] == 9 and 0 < seat['embedded_back_samples'] <= 9
             and 0 <= seat['maximum_front_root_distance_m'] < .0015
             and seat['minimum_back_signed_distance_m'] < -.0001,
             'Floating/wrong/incompletely sampled actual F01/feather root: '+name)
    ring_support = {'TECH_PerchRing_'+entry['id']: entry['support'] for entry in cfg['perch_rings']}
    for name, mesh in data['tech_meshes'].items():
        is_ring = name.startswith('TECH_PerchRing_')
        kind = 'torus' if is_ring else 'sphere'
        support = ring_support[name] if is_ring else (
            'FAC_MaskBridge' if name == 'TECH_ForeheadLink_Bottom' else None)
        allowed = {support} if support else {'PRI_HeadNeckTorso', 'FAC_MaskBridge'}
        need(mesh['kind'] == kind and mesh['support'] in allowed,
             'Wrong commissioned tech geometry/support: '+name)
        surface(mesh['cage'], mesh['cage_triangles'], name, kind)
        surface(mesh['cage'], mesh['evaluated_triangles'], name+' evaluated', kind)
        expected_vertices = 1152 if is_ring else 266 if 'Node' in name else 108
        expected_triangles = 2304 if is_ring else 528 if 'Node' in name else 212
        need(mesh['cage']['vertices'] == expected_vertices
             and mesh['cage']['polygons'] == POLYGON_COUNTS[name]
             and mesh['cage_triangles']['triangles'] == mesh['evaluated_triangles']['triangles'] == expected_triangles,
             'Changed bounded actual tech topology inventory: '+name)
        seat = data['tech_seats'][name]
        need(seat['support'] == mesh['support'] and seat['samples'] == expected_vertices
             and 0 <= seat['maximum_surface_distance_m'] < (.0016 if is_ring else .004),
             'Floating/incompletely sampled actual tech seat: '+name)
    for name, mirror in data['tech_symmetry'].items():
        need(mirror['vertices'] == data['tech_meshes'][name]['cage']['vertices']
             and 0 <= mirror['maximum_mirror_deviation_m'] < 2e-6,
             'Actual reflected network/perch geometry differs: '+name)
    for view, frame in data['framing'].items():
        need(frame['object_count'] == len(names) and frame['inside_safe_frame'] is True
             and frame['minimum_image_margin'] > 0
             and all(item['inside_safe_frame'] is True for item in frame['objects'].values()),
             'Actual four-view material/tech silhouette clips fixed studio: '+view)
    current_studio, old_studio = copy.deepcopy(data['studio']), copy.deepcopy(baseline['studio'])
    current_studio.pop('scene_object_count')
    old_studio.pop('scene_object_count')
    need(current_studio == old_studio, 'Fixed accepted studio/camera/light/world/render changed')
    need(data['counts'] == {'objects': 117, 'meshes': 103, 'new_meshes': 51,
             'feather_leaves': 48, 'armatures': 0, 'actions': 0, 'tech_meshes': 17}
         and data['studio']['scene_object_count'] == 117,
         'Wrong bounded material/tech scene inventory')
    feet = data['feet']
    need(feet == baseline['feet'] and feet['independent_surface_collision_pairs'] == 45
         and sum(contact['rear'] for contact in feet['contacts'].values()) == 2
         and all(contact['nearest_surface_distance_m'] < 2e-7
                 and contact['minimum_polygon_halfspace_distance_m'] >= -feet['penetration_tolerance_m']
                 for contact in feet['contacts'].values()), 'Actual 3+1 anatomy/eight claw-bar/support probe changed')
    face = data['movement']['blink_and_gaze']
    beak = data['movement']['beak_opening']
    gaze = [('X', -12), ('X', 12), ('Z', -12), ('Z', 12)]
    samples = [i/40 for i in range(41)]
    states = [(.5, 0), (1, 0), (0, .5), (0, 1), (.5, .5), (1, 1)]
    beak_targets = {name for name in names if name.startswith(('FAC_', 'PRI_Head', 'BLK_Chest', 'BLK_Forehead'))}
    need(face['blink_samples'] == samples and face['minimum_clearance_m'] >= .0003
         and all(value >= .0003 for value in face['minimum_triangle_clearance_m'].values())
         and near(face['minimum_clearance_m'], min(face['minimum_triangle_clearance_m'].values()), 1e-9)
         and face['closed_coverage_rays'] >= 10000 and face['full_close_front_and_back_seam_gap_m'] == 0
         and [(v['axis'], v['degrees']) for v in face['gaze_probes']] == gaze
         and all(v['no_collisions'] is True for v in face['gaze_probes']),
         'Incomplete/unsafe full actual blink/gaze trajectory')
    need(beak['opening_samples'] == samples and beak['upper_fixed'] is True
         and beak['collision_checks'] == 41*(2*len(beak_targets)+1)
         and beak['minimum_sampled_mask_clearance_m'] >= .0003
         and beak['maximum_lower_vertex_displacement_m'] > .005 and beak['front_lower_vertex_drop_m'] > .004,
         'Incomplete/unsafe actual 0–18 degree beak trajectory')
    function = data['movement']['feather_function']
    need(function['target_meshes'] == sorted(feathers)
         and function['blink_samples'] == function['beak_samples'] == samples
         and function['blink_collision_checks'] == 41*4*len(feathers)
         and function['beak_collision_checks'] == 41*2*len(feathers)
         and [(v['axis'], v['degrees']) for v in function['gaze_probes']] == gaze
         and all(v['collision_checks'] == 8*len(feathers) for v in function['gaze_probes']),
         'Missing actual blink/gaze/beak coverage of every current F01/feather mesh')
    gestures = data['movement']['wing_gestures']
    need(gestures['neutral_restored'] is True
         and [(state['left'], state['right']) for state in gestures['states']] == states,
         'Missing isolated/combined actual half/full gestures or neutral return')
    for index, state in enumerate(gestures['states']):
        need(state['foot_collision_checks'] == len(wings)*len(feet['surfaces']),
             'Incomplete actual wing-foot/perch collision pairs: '+str(index))
        for name, motion in state['parts'].items():
            value = state['left'] if name.endswith('_L') else state['right']
            need((motion['maximum_vertex_displacement_m'] > .003 if value
                  else motion['maximum_vertex_displacement_m'] < 1e-9)
                 and 0 <= motion['fixed_root_drift_m'] < 1e-9,
                 'Actual wing/layer motion or fixed-root attachment failed: '+name+'/'+str(index))
            surface(motion['cage'], motion['triangle_interiors'], name+'/'+str(index))
    function = data['movement']['tech_function']
    need(function['target_meshes'] == sorted(tech) and function['neutral_restored'] is True
         and function['blink_samples'] == function['beak_samples'] == samples
         and function['blink_collision_checks'] == 41*4*len(tech)
         and function['beak_collision_checks'] == 41*2*len(tech)
         and [(v['axis'], v['degrees']) for v in function['gaze_probes']] == gaze
         and all(v['collision_checks'] == 8*len(tech) for v in function['gaze_probes'])
         and [(v['left'], v['right']) for v in function['wing_states']] == states
         and all(v['collision_checks'] == len(wings)*len(tech) for v in function['wing_states']),
         'Missing actual full blink/gaze/beak/six-wing-state coverage of every new tech mesh')
    return errors


def proof_shape(cfg, baseline):
    return object_shape({
        'gate_version': 'int', 'milestone': 'str', 'design_approval': 'bool',
        'baseline_commit': 'str', 'baseline_scene_sha256': 'sha256',
        'scene_path': 'str', 'scene_sha256': 'sha256', 'scene_size_bytes': 'int',
        'build': worker_shape(cfg, baseline, True), 'reloaded': worker_shape(cfg, baseline),
        'reload_identical': 'bool',
        'render_comparison': table_shape(VIEWS, object_shape({
            'size': sequence_shape(2, 'int'), 'mode': 'str',
            'build_and_two_reloads_pixels_identical': 'bool'})),
        'commands': sequence_shape(4, object_shape({'mode': 'str',
                                                   'argv': sequence_shape(12, 'str'), 'exit_code': 'int'})),
        'protected_predecessor_sha256': table_shape(PROTECTED_SHA256, 'sha256'),
        'source_sha256': table_shape(SOURCES, 'sha256'),
        'reference_sha256': table_shape(REFERENCE_NAMES, 'sha256'),
        'evidence_sha256': table_shape(EVIDENCE_NAMES, 'sha256'),
    })


DECISION_SHAPE = object_shape({
    'gate_version': 'int', 'milestone': 'str', 'status': 'str',
    'scene_sha256': 'sha256', 'verification_sha256': 'sha256',
    'reference_authority': sequence_shape(3, object_shape({'file': 'str', 'rank': 'int'})),
    'views': table_shape(VIEWS, object_shape({'status': 'str', 'reason': 'str'})),
    'criteria': table_shape(CRITERIA, object_shape({'status': 'str', 'reason': 'str'})),
    'blocking_findings': sequence_shape(0, 'str'),
    'evidence_sha256': table_shape(MANUAL_EVIDENCE_NAMES, 'sha256'),
})


def validate_materials(root=ROOT, proof=None, decision=None):
    """Admit exact current artifacts only after complete machine and manual proof."""
    root = Path(root)
    folder = root/REVIEW_PATH
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    def bound(path, digest):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append('Stale/missing Goal 18 bound evidence: '+str(path))
    try:
        cfg = load_json(root/'design/materials_lookdev.json')
        baseline = load_json(root/'validation/reviews/feathers_v01/reload_b_checks.json')
        if proof is None:
            proof = load_json(folder/'verification.json')
        if decision is None:
            decision = load_json(folder/'review.json')
        errors += validate_shape(proof, proof_shape(cfg, baseline), 'proof')
        errors += validate_shape(decision, DECISION_SHAPE, 'decision')
        if errors:
            return errors
        errors += validate_worker_semantics(proof['build'], cfg, baseline, True)
        errors += validate_worker_semantics(proof['reloaded'], cfg, baseline)
        if errors:
            return errors
        need(proof['gate_version'] == decision['gate_version'] == 2
             and proof['milestone'] == decision['milestone'] == 'materials_v01'
             and proof['design_approval'] is False,
             'Wrong Goal 18 version/scope or conflated automatic approval')
        need(proof['baseline_commit'] == BASELINE_COMMIT
             and proof['baseline_scene_sha256'] == BASELINE_SHA256,
             'Wrong accepted Goal 6 predecessor')
        bound(root/BASELINE_SCENE, BASELINE_SHA256)
        need((root/BASELINE_SCENE).stat().st_size == BASELINE_SIZE_BYTES, 'Accepted predecessor size differs')
        need(proof['protected_predecessor_sha256'] == PROTECTED_SHA256,
             'Untrusted/shrunken historical predecessor inventory')
        for name, digest in PROTECTED_SHA256.items():
            bound(root/name, digest)
        bound(root/'scripts/blender/legacy/50_materials.py', ARCHIVED_STAGE_SHA256)
        for name, digest in proof['source_sha256'].items():
            bound(root/name, digest)
        for name, digest in proof['reference_sha256'].items():
            bound(root/'references/approved'/name, digest)
        need(proof['scene_path'] == SCENE_PATH and proof['scene_size_bytes'] > BASELINE_SIZE_BYTES,
             'Wrong or empty new Goal 18 production scene')
        bound(root/SCENE_PATH, proof['scene_sha256'])
        need((root/SCENE_PATH).stat().st_size == proof['scene_size_bytes'], 'New Goal 18 scene size differs')
        for name, digest in proof['evidence_sha256'].items():
            bound(folder/name, digest)
        for name, digest in decision['evidence_sha256'].items():
            bound(folder/name, digest)
        actual = {mode: load_json(folder/(mode+'_checks.json')) for mode in MODES}
        for mode, data in actual.items():
            errors += validate_worker_semantics(data, cfg, baseline, mode == 'build')
        need(actual['build'] == proof['build'], 'Declared Goal 18 build differs from actual bound worker JSON')
        need(actual['saved_build'] == actual['reload_a'] == actual['reload_b'] == proof['reloaded'],
             'Fresh saved-build/two reload workers differ from declared data')
        need(proof['reload_identical'] is True
             and all(proof['build'][key] == proof['reloaded'][key] for key in RELOAD_FIELDS),
             'Fresh reopening changes required Goal 18 geometry/shader/probe fields')
        pixels = {}
        for label in LABELS:
            pixels[label] = {}
            for view in VIEWS:
                with Image.open(folder/'evidence'/label/(view+'.png')) as im:
                    need(im.format == 'PNG' and im.size == (1024, 1024) and im.mode == 'RGBA',
                         'Missing actual 1024px RGBA Goal 18 view: '+label+'/'+view)
                    need(any(low != high for low, high in im.getextrema()),
                         'Empty/flat Goal 18 image: '+label+'/'+view)
                    pixels[label][view] = im.tobytes()
        for view in VIEWS:
            need(proof['render_comparison'][view] == {
                'size': [1024, 1024], 'mode': 'RGBA', 'build_and_two_reloads_pixels_identical': True},
                'Wrong declared canonical render metadata: '+view)
            need(pixels['neutral'][view] == pixels['reload_a'][view] == pixels['reload_b'][view],
                 'Actual canonical build/two reload PNG pixels differ: '+view)
            with Image.open(folder/(view+'.png')) as published:
                need(published.format == 'PNG' and published.size == (1024, 1024)
                     and published.mode == 'RGBA' and published.tobytes() == pixels['reload_b'][view],
                     'Published manual-review view differs from canonical scene: '+view)
        for pose in ('blink', 'beak_open', 'gesture_left', 'gesture_right', 'gesture_both'):
            need(any(pixels[pose][view] != pixels['live_neutral'][view] for view in VIEWS),
                 'Actual pose render lacks visible response: '+pose)
        need(any(pixels['baseline'][view] != pixels['neutral'][view] for view in VIEWS),
             'New assigned materials/tech scene has no visual change from accepted predecessor')
        need([item['mode'] for item in proof['commands']] == list(MODES),
             'Wrong four fresh Blender command inventory')
        first_argv = proof['commands'][0]['argv']
        for command in proof['commands']:
            mode, argv = command['mode'], command['argv']
            need(command['exit_code'] == 0 and argv[1] == '--background'
                 and argv[3:6] == ['--python-exit-code', '1', '--python']
                 and argv[6].replace('\\', '/').endswith('/scripts/blender/materials_evidence.py')
                 and argv[7:9] == ['--', '--work'] and argv[10:] == ['--mode', mode]
                 and argv[:10] == first_argv[:10], 'Unproven/changed Blender invocation: '+mode)
            log = (folder/(mode+'.log')).read_text(encoding='utf-8')
            need('MATERIALS EVIDENCE OK: '+mode in log and 'Blender ' in log,
                 'Bound worker log lacks successful actual Blender completion: '+mode)
        need(decision['status'] == 'materials_lookdev_accepted' and decision['blocking_findings'] == [],
             'Manual final-scene Goal 18 review not accepted')
        need(decision['scene_sha256'] == proof['scene_sha256'], 'Manual Goal 18 decision names another scene')
        bound(folder/'verification.json', decision['verification_sha256'])
        need(decision['verification_sha256'] == decision['evidence_sha256']['verification.json'],
             'Manual Goal 18 decision verification bindings disagree')
        need(decision['reference_authority'] == list(REFERENCE_AUTHORITY),
             'Wrong Goal 18 visual reference hierarchy')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['views'].values()),
             'Missing written findings in one of four fixed Goal 18 views')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['criteria'].values()),
             'Unresolved or unsupported Goal 18/F01 commissioned acceptance criterion')
        errors += validate_feathers(root)
        return errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return errors+[f'Malformed/missing Goal 18 delivery: {exc}']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate_materials(args.root)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print('MATERIALS DELIVERY VALID: assigned shaders, measured tech/F01, canonical workers/pixels, preserved history')


if __name__ == '__main__':
    main()
