"""Strict Goal 19 eye layers, actual runtime probes and preserved material delivery."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image
from feathers_gate import (load_json, object_shape, table_shape, sequence_shape, validate_shape as inherited_validate_shape,
                           CAGE_SHAPE, TRIANGLE_SHAPE, VEC3_SHAPE)
import materials_gate as previous
import eyes_contracts as authored
from materials_gate import validate_materials, near
from eyes_contracts import (
    BASELINE_COMMIT, BASELINE_SCENE, BASELINE_SHA256, BASELINE_SIZE_BYTES,
    PROTECTED_SHA256, REFERENCE_AUTHORITY, REFERENCE_NAMES, REVIEW_PATH, SCENE_PATH,
    SOURCES, VIEWS, CRITERIA, EVIDENCE_NAMES, MANUAL_EVIDENCE_NAMES, MODES, LABELS, EYES,
    BASELINE_SHAPE_SHA256, BASELINE_GEOMETRY_SHA256, BASELINE_EYE_STATE_SHA256,
    BASELINE_ASSIGNMENTS, BASELINE_POLYGON_COUNTS, BASELINE_POLYGON_ASSIGNMENT_SHA256,
    BASELINE_MATERIAL_SHADER_SHA256, BASELINE_NON_EYE_SHA256, BASELINE_UV_SHA256,
    BASELINE_ATTRIBUTES_SHA256, BASELINE_PIVOT_SHA256, LAYER_PAIRS,
    EXPECTED_RECIPE, EXPECTED_EYE_GRAPHS, EXPECTED_EYE_SHAPE_SHA256, EXPECTED_EYE_STATE_SHA256,
    EXPECTED_EYE_UV_SHA256, EXPECTED_EYE_ATTRIBUTES_SHA256, EXPECTED_EYE_LAYERS, EXPECTED_EYE_GEOMETRY_SHA256,
    EYE_POLYGON_COUNTS, EYE_VERTEX_COUNTS, EYE_TRIANGLE_COUNTS, EXPECTED_BUILD_DATABLOCK_COUNTS,
    ARCHIVE_PATH, ARCHIVE_SHA256, ARCHIVED_CANDIDATE_SHA256,
    LIDS, SOCKETS, CHANGED_PIVOTS, BASELINE_NORMALS_SHA256, BASELINE_NORMALS_AUDIT,
    BASELINE_EYE_LOCAL_SHAPE_SHA256, BASELINE_EYE_CENTERS_M, BASELINE_SOCKET_CAGE_COUNTS,
)
ROOT = Path(__file__).resolve().parents[1]
ROLES = ('Eye_Globe', 'Eye_Iris', 'Eye_Pupil', 'Eye_Cornea')
CHANGED = tuple(f'FAC_{part}_{side}' for part in ('Iris', 'Pupil') for side in ('L', 'R'))
NON_EYES = tuple(sorted(set(BASELINE_SHAPE_SHA256)-set(EYES)))
PRESERVED_NON_EYES = tuple(name for name in NON_EYES if name not in SOCKETS)
PIVOTS = ('BAK_LowerPivot', 'FAC_EyeAim_L', 'FAC_EyeAim_R', 'FTH_WingRoot_L', 'FTH_WingRoot_R')
RELOAD_FIELDS = previous.RELOAD_FIELDS + ('eye_materials', 'eye_geometry', 'eye_layers',
    'unchanged_non_eye_sha256', 'uv_state_sha256', 'attributes_state_sha256', 'pivot_state_sha256', 'eye_local_shape_sha256',
    'normals_state_sha256', 'normals_audit', 'socket_geometry', 'socket_state_sha256')


def _historical_projection(data, baseline):
    """Only inherited diagnostic-eye constraints are replaced for the older validator.

    The actual eight eyes and exactly five revised socket meshes are independently checked by the new commissioned schema,
    geometry, graph and runtime checks. All 90 preserved non-eye and measured functional fields
    pass through without alteration to the complete previous validation.
    """
    projected = {name: copy.deepcopy(data[name]) for name in previous.RELOAD_FIELDS}
    for name in tuple(EYES)+SOCKETS:
        projected['shape_sha256'][name] = BASELINE_SHAPE_SHA256[name]
        projected['geometry_sha256'][name] = BASELINE_GEOMETRY_SHA256[name]
        projected['assignments'][name] = copy.deepcopy(baseline['assignments'][name])
    projected['eye_state_sha256'] = dict(BASELINE_EYE_STATE_SHA256)
    projected['counts'].pop('eye_materials')
    projected['movement'].pop('eye_function')
    return projected


def validate_shape(value, schema, path='worker'):
    """Full RNA graphs legitimately include empty labels/default string inputs."""
    if isinstance(schema, str):
        if schema == 'plainstr':
            return [] if type(value) is str else [path+': invalid graph string']
        return inherited_validate_shape(value, schema, path)
    if 'dict' in schema or 'keys' in schema:
        required = schema.get('dict')
        if required is None:
            required = {key: schema['values'] for key in schema['keys']}
        if not isinstance(value, dict) or set(value) != set(required):
            return [path+': incomplete or unexpected object fields']
        return [error for key, child in required.items()
                for error in validate_shape(value[key], child, path+'/'+key)]
    if not isinstance(value, list) or len(value) != schema['list']:
        return [path+': incomplete or unexpected sequence']
    items = schema['items']
    return [error for index, item in enumerate(value)
            for error in validate_shape(item, items[0] if len(items) == 1 else items[index], path+'/'+str(index))]


def literal_shape(value):
    """Schema comes solely from authored code literals, never supplied evidence."""
    if value is None:
        return 'NoneType'
    if type(value) is bool:
        return 'bool'
    if type(value) is int:
        return 'int'
    if type(value) is float:
        return 'number'
    if isinstance(value, str):
        return 'plainstr'
    if isinstance(value, dict):
        return object_shape({key: literal_shape(item) for key, item in value.items()})
    if isinstance(value, list):
        return {'list': len(value), 'items': [literal_shape(item) for item in value]}
    raise TypeError('Uncommissioned authored recipe type: '+type(value).__name__)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   allow_nan=False).encode()).hexdigest()


def worker_shape(cfg, baseline, build=False):
    material_cfg = load_json(ROOT/'design/materials_lookdev.json')
    feather_baseline = load_json(ROOT/'validation/reviews/feathers_v01/reload_b_checks.json')
    fields = copy.deepcopy(previous.worker_shape(material_cfg, feather_baseline)['dict'])
    fields['assignments'] = object_shape({name: object_shape({
        'slots': sequence_shape(1 if name in EYES else len(BASELINE_ASSIGNMENTS[name]), 'str'),
        'polygon_material_indices': sequence_shape(EYE_POLYGON_COUNTS.get(name, BASELINE_POLYGON_COUNTS[name]), 'int'),
        'unassigned_polygons': 'int'}) for name in BASELINE_ASSIGNMENTS})
    fields['eye_materials'] = object_shape({role: object_shape({
        'graph': literal_shape(EXPECTED_EYE_GRAPHS[role]), 'shader_sha256': 'sha256'}) for role in ROLES})
    fields['eye_geometry'] = table_shape(EYES, object_shape({
        'cage': CAGE_SHAPE, 'cage_triangles': TRIANGLE_SHAPE, 'evaluated_triangles': TRIANGLE_SHAPE}))
    fields['eye_layers'] = table_shape(('L', 'R'), object_shape({
        'projected_pupil_iris_ratio': 'float', 'projected_iris_radius_m': 'float', 'projected_pupil_radius_m': 'float',
        'radii_m': table_shape(('Globe', 'Iris', 'Pupil', 'Cornea'), sequence_shape(2, 'number')),
        'layer_collision_pairs': table_shape(LAYER_PAIRS, 'int'), 'center_m': VEC3_SHAPE}))
    fields['unchanged_non_eye_sha256'] = table_shape(NON_EYES, 'sha256')
    fields['uv_state_sha256'] = table_shape(BASELINE_SHAPE_SHA256, 'sha256')
    fields['attributes_state_sha256'] = table_shape(BASELINE_SHAPE_SHA256, 'sha256')
    fields['counts']['dict']['eye_materials'] = 'int'
    fields['movement']['dict']['eye_function'] = object_shape({
        'target_meshes': sequence_shape(8, 'str'),
        'actual_cornea_max_radius_m': table_shape(('L', 'R'), 'float'),
        'blink_samples': sequence_shape(41, 'float'), 'minimum_clearance_m': 'float',
        'minimum_triangle_clearance_m': table_shape(
            (f'{i/40:.3f}/{kind}/{side}' for i in range(41) for side in ('L','R') for kind in ('Upper','Lower')), 'float'),
        'blink_eye_collision_checks': 'int', 'neutral_restored': 'bool',
        'lid_pose_normals_sha256': table_shape((f'{i/40:.3f}' for i in range(41)), table_shape(LIDS, 'sha256')),
        'neutral_normals_restored': 'bool',
        'gaze_probes': sequence_shape(4, object_shape({'axis': 'str', 'degrees': 'int',
            'target_meshes': sequence_shape(9, 'str'), 'collision_checks': 'int'})),
    })
    fields['pivot_state_sha256'] = table_shape(PIVOTS, 'sha256')
    fields['eye_local_shape_sha256'] = table_shape(EYES, 'sha256')
    fields['normals_state_sha256'] = table_shape(BASELINE_SHAPE_SHA256, 'sha256')
    fields['normals_audit'] = table_shape(BASELINE_SHAPE_SHA256, object_shape({
        'has_custom_normals': 'bool', 'domain': 'str', 'loop_count': 'int', 'normal_count': 'int',
        'maximum_unit_error': 'float'}))
    fields['socket_geometry'] = table_shape(SOCKETS, object_shape({
        'cage': CAGE_SHAPE, 'cage_triangles': TRIANGLE_SHAPE, 'evaluated_triangles': TRIANGLE_SHAPE}))
    fields['socket_state_sha256'] = table_shape(SOCKETS, 'sha256')
    if build:
        fields.update(baseline_shape_sha256=table_shape(BASELINE_SHAPE_SHA256, 'sha256'),
                      baseline_non_eye_sha256=table_shape(NON_EYES, 'sha256'),
                      baseline_normals_state_sha256=table_shape(BASELINE_SHAPE_SHA256, 'sha256'),
                      baseline_eye_local_shape_sha256=table_shape(EYES, 'sha256'),
                      repeated_build_identical='bool', datablock_counts=sequence_shape(3, 'int'))
    return object_shape(fields)


def validate_worker_structure(data, cfg, baseline, build=False):
    return validate_shape(data, worker_shape(cfg, baseline, build))


def validate_eye_material_semantics(role, material):
    shape = object_shape({'graph': literal_shape(EXPECTED_EYE_GRAPHS[role]), 'shader_sha256': 'sha256'})
    errors = validate_shape(material, shape, 'eye_material/'+role)
    if errors:
        return errors
    if material['graph'] != EXPECTED_EYE_GRAPHS[role]:
        errors.append('Actual full eye node/input/link/ramp/property recipe differs: '+role)
    if material['shader_sha256'] != digest(material['graph']):
        errors.append('Actual eye graph and independently recomputed digest differ: '+role)
    return errors


def validate_worker_semantics(data, cfg, baseline, build=False):
    errors = validate_worker_structure(data, cfg, baseline, build)
    if errors:
        return errors
    if authored.LID_OUTPUT_FROZEN is not True:
        return ['Final five-socket/normal recipe has not been bound to a reproduced full worker']
    def need(condition, message):
        if not condition:
            errors.append(message)
    need({name: cfg[name] for name in ('geometry', 'shader', 'network', 'lid_integration')} == EXPECTED_RECIPE,
         'Commissioned eye geometry/shader/motif recipe changed without code-owned review')
    material_cfg = load_json(ROOT/'design/materials_lookdev.json')
    feather_baseline = load_json(ROOT/'validation/reviews/feathers_v01/reload_b_checks.json')
    errors += previous.validate_worker_semantics(_historical_projection(data, baseline), material_cfg, feather_baseline)
    need(all(data['unchanged_non_eye_sha256'][name] == BASELINE_NON_EYE_SHA256[name]
             for name in PRESERVED_NON_EYES),
         'Changed accepted non-eye geometry/slots/graphs/UV/attributes/shape keys')
    need(all(data['attributes_state_sha256'][name] == BASELINE_ATTRIBUTES_SHA256[name] for name in PRESERVED_NON_EYES),
         'Changed actual non-eye rest/mesh attributes')
    need(data['counts']['eye_materials'] == 4, 'Wrong actual eye material count')
    need(data['pivot_state_sha256'] == authored.EXPECTED_PIVOT_SHA256
         and all(data['pivot_state_sha256'][name] == BASELINE_PIVOT_SHA256[name] for name in PIVOTS if name not in CHANGED_PIVOTS),
         'Changed accepted eye/beak/wing pivots')
    need(all(data['shape_sha256'][name] == BASELINE_SHAPE_SHA256[name] for name in PRESERVED_NON_EYES)
         and all(data['geometry_sha256'][name] == BASELINE_GEOMETRY_SHA256[name] for name in PRESERVED_NON_EYES),
         'Changed accepted non-eye cages/material assignment')
    need(all(data['uv_state_sha256'][name] == BASELINE_UV_SHA256[name] for name in PRESERVED_NON_EYES),
         'Changed actual accepted non-eye UV data')
    need(all(data['materials'][role]['shader_sha256'] == expected
             for role, expected in BASELINE_MATERIAL_SHADER_SHA256.items()),
         'Changed actual accepted non-eye full shader graph')
    for name in EYES:
        role = 'Eye_'+name.split('_')[1]
        assignment = data['assignments'][name]
        need(assignment['slots'] == ['MAT_'+role] and assignment['unassigned_polygons'] == 0
             and all(index == 0 for index in assignment['polygon_material_indices']),
             'Missing actual authored layered eye material assignment: '+name)
        need(data['shape_sha256'][name] == EXPECTED_EYE_SHAPE_SHA256[name]
             and data['eye_state_sha256'][name] == EXPECTED_EYE_STATE_SHA256[name]
             and data['geometry_sha256'][name] == EXPECTED_EYE_GEOMETRY_SHA256[name]
             and data['uv_state_sha256'][name] == EXPECTED_EYE_UV_SHA256[name]
             and data['attributes_state_sha256'][name] == EXPECTED_EYE_ATTRIBUTES_SHA256[name],
             'Changed authored actual eye cage/material/UV state: '+name)
        mesh = data['eye_geometry'][name]
        cage = mesh['cage']
        need(cage['closed_connected'] is True and cage['outward_consistent_normals'] is True
             and cage['self_intersections'] == cage['duplicate_vertices'] == 0
             and cage['vertices'] == EYE_VERTEX_COUNTS[name]
             and cage['polygons'] == EYE_POLYGON_COUNTS[name]
             and cage['euler_characteristic'] == (0 if '_Iris_' in name else 2)
             and cage['volume_m3'] > 0 and cage['minimum_polygon_area_m2'] > 0,
             'Invalid actual closed editable eye layer: '+name)
        for label in ('cage_triangles', 'evaluated_triangles'):
            triangles = mesh[label]
            need(triangles['triangles'] == EYE_TRIANGLE_COUNTS[name]
                 and triangles['adjacent_interiors_included'] is True
                 and triangles['interior_crossings'] == 0
                 and triangles['minimum_polygon_triangle_normal_dot'] > 0
                 and 0 <= triangles['maximum_boundary_inset_m'] < .0001
                 and triangles['coplanar_candidate_checks'] >= 0
                 and triangles['coplanar_overlap_area_tolerance_m2'] == 1e-12
                 and triangles['coplanar_plane_tolerance_m'] == 1e-8,
                 'Missing/failed actual eye adjacent/coplanar triangle audit: '+name+'/'+label)
    for role, material in data['eye_materials'].items():
        errors += validate_eye_material_semantics(role, material)
    for side, layers in data['eye_layers'].items():
        need(near(layers['projected_pupil_iris_ratio'], EXPECTED_EYE_LAYERS[side]['projected_pupil_iris_ratio'], 1e-7)
             and .15 < layers['projected_pupil_iris_ratio'] < .4,
             'Wrong actual reference-corrected pupil/iris proportion: '+side)
        need(all(value == 0 for value in layers['layer_collision_pairs'].values())
             and near(layers['center_m'], EXPECTED_EYE_LAYERS[side]['center_m'], 1e-9),
             'Changed eye center or physical optical layers intersect: '+side)
        need(all(near(value, EXPECTED_EYE_LAYERS[side]['radii_m'][part], 1e-7)
                 for part, value in layers['radii_m'].items()),
             'Changed actual optical layer envelopes: '+side)
        need(near(layers['projected_iris_radius_m'], EXPECTED_EYE_LAYERS[side]['projected_iris_radius_m'], 1e-7)
             and near(layers['projected_pupil_radius_m'], EXPECTED_EYE_LAYERS[side]['projected_pupil_radius_m'], 1e-7)
             and layers['projected_iris_radius_m'] > 0
             and near(layers['projected_pupil_iris_ratio'], layers['projected_pupil_radius_m']/layers['projected_iris_radius_m'], 1e-9),
             'Contradictory actual eye projected radii/ratio: '+side)
        radii = layers['radii_m']
        need(radii['Globe'][1] < radii['Iris'][0] < radii['Iris'][1]
             < radii['Pupil'][0] <= radii['Pupil'][1] < radii['Cornea'][0],
             'Actual eye layers lack physical radial separation: '+side)
    need(data['eye_local_shape_sha256'] == authored.EXPECTED_EYE_LOCAL_SHAPE_SHA256
         and all(data['eye_local_shape_sha256'][name] == BASELINE_EYE_LOCAL_SHAPE_SHA256[name]
                 for name in EYES if name.startswith(('FAC_Globe_', 'FAC_Cornea_'))),
         'Changed frozen local globe/cornea envelope or authored relative eye cage')
    for side in ('L', 'R'):
        center = data['eye_layers'][side]['center_m']
        baseline_center = BASELINE_EYE_CENTERS_M[side]
        need(near(center[0], baseline_center[0], 1e-9) and near(center[2], baseline_center[2], 1e-9)
             and near(center[1], baseline_center[1]+cfg['lid_integration']['eye_depth_offset_m'], 2e-8),
             'Undocumented eye arrangement change outside the exact Y-only depth recipe: '+side)
    need(data['socket_state_sha256'] == authored.EXPECTED_SOCKET_STATE_SHA256,
         'Changed authored full-state binding of the exact five revised socket meshes')
    for name in SOCKETS:
        need(data['unchanged_non_eye_sha256'][name] == data['socket_state_sha256'][name]
             and data['shape_sha256'][name] == authored.EXPECTED_SOCKET_SHAPE_SHA256[name]
             and data['geometry_sha256'][name] == authored.EXPECTED_SOCKET_GEOMETRY_SHA256[name]
             and data['uv_state_sha256'][name] == authored.EXPECTED_SOCKET_UV_SHA256[name]
             and data['attributes_state_sha256'][name] == authored.EXPECTED_SOCKET_ATTRIBUTES_SHA256[name]
             and data['assignments'][name] == baseline['assignments'][name],
             'Contradictory actual five-socket cage/material/UV/attribute state: '+name)
        mesh = data['socket_geometry'][name]
        cage = mesh['cage']
        counts = BASELINE_SOCKET_CAGE_COUNTS[name]
        need(cage['vertices'] == counts['vertices'] and cage['polygons'] == counts['polygons']
             and cage['closed_connected'] is True and cage['outward_consistent_normals'] is True
             and cage['self_intersections'] == cage['duplicate_vertices'] == 0
             and cage['euler_characteristic'] == 2 and cage['volume_m3'] > 0
             and cage['minimum_polygon_area_m2'] > 0,
             'Unsafe or unexpectedly retopologized actual socket/bridge cage: '+name)
        for label in ('cage_triangles', 'evaluated_triangles'):
            triangle = mesh[label]
            need(triangle['triangles'] == authored.EXPECTED_SOCKET_TRIANGLE_COUNTS[name]
                 and triangle['adjacent_interiors_included'] is True and triangle['interior_crossings'] == 0
                 and triangle['minimum_polygon_triangle_normal_dot'] > 0
                 and 0 <= triangle['maximum_boundary_inset_m'] < .0001
                 and triangle['coplanar_candidate_checks'] >= 0
                 and triangle['coplanar_overlap_area_tolerance_m2'] == 1e-12
                 and triangle['coplanar_plane_tolerance_m'] == 1e-8,
                 'Failed/missing actual socket adjacent/coplanar triangle audit: '+name+'/'+label)
    need(data['normals_state_sha256'] == authored.EXPECTED_NORMALS_SHA256
         and data['normals_audit'] == authored.EXPECTED_NORMALS_AUDIT,
         'Changed actual final source corner normals or contradictory audit')
    for name, audit in data['normals_audit'].items():
        need(audit['loop_count'] == audit['normal_count'] and audit['normal_count'] > 0
             and 0 <= audit['maximum_unit_error'] < 1e-5 and audit['domain'] in ('POINT','FACE','CORNER')
             and (name not in LIDS or audit['has_custom_normals'] is True),
             'Incomplete/non-unit actual source normals or missing authored lid split normals: '+name)
    normal_preserved = PRESERVED_NON_EYES + tuple(name for name in EYES if name.startswith(('FAC_Globe_','FAC_Cornea_')))
    need(all(data['normals_state_sha256'][name] == BASELINE_NORMALS_SHA256[name] for name in normal_preserved),
         'Changed accepted corner normals outside the exact eye/five-socket revisions')
    function = data['movement']['eye_function']
    need(function['target_meshes'] == list(EYES) and function['blink_samples'] == [i/40 for i in range(41)]
         and function['blink_eye_collision_checks'] == 41*4*8 and function['neutral_restored'] is True
         and all(value >= .0003 for value in function['minimum_triangle_clearance_m'].values())
         and near(function['minimum_clearance_m'], min(function['minimum_triangle_clearance_m'].values()), 1e-9),
         'Incomplete/unsafe actual eight-eye full blink checks or contradictory individual clearances')
    need(all(near(value, data['eye_layers'][side]['radii_m']['Cornea'][1], 1e-9)
             for side, value in function['actual_cornea_max_radius_m'].items()),
         'Blink clearance radius is not the actual current cornea envelope')
    need(function['neutral_normals_restored'] is True
         and function['lid_pose_normals_sha256'] == authored.EXPECTED_LID_POSE_NORMALS
         and function['lid_pose_normals_sha256']['0.000'] == {name:data['normals_state_sha256'][name] for name in LIDS}
         and all(function['lid_pose_normals_sha256']['0.000'][name] != function['lid_pose_normals_sha256']['1.000'][name] for name in LIDS),
         'Missing/stale actual 41-state lid normals or failed complete neutral normal restoration')
    gaze_targets = ['FAC_Mask_L','FAC_Mask_R','FAC_MaskBridge','FAC_Lid_Upper_L','FAC_Lid_Lower_L',
                    'FAC_Lid_Upper_R','FAC_Lid_Lower_R','BAK_Upper','BAK_Lower']
    need([(item['axis'], item['degrees']) for item in function['gaze_probes']] == [('X',-12),('X',12),('Z',-12),('Z',12)]
         and all(item['target_meshes'] == gaze_targets and item['collision_checks'] == 8*9
                 for item in function['gaze_probes']),
         'Missing actual eight-eye gaze/mask/lid/beak collision coverage')
    if build:
        need(data['baseline_shape_sha256'] == BASELINE_SHAPE_SHA256
             and data['baseline_non_eye_sha256'] == BASELINE_NON_EYE_SHA256
             and data['baseline_normals_state_sha256'] == BASELINE_NORMALS_SHA256
             and data['baseline_eye_local_shape_sha256'] == BASELINE_EYE_LOCAL_SHAPE_SHA256
             and data['repeated_build_identical'] is True
             and data['datablock_counts'] == EXPECTED_BUILD_DATABLOCK_COUNTS,
             'Missing true accepted predecessor/repeated build or leaked datablocks')
    return errors


def validate_candidate_archive(root=ROOT):
    """Preserve all original candidate sources/reports; never regenerate their claims."""
    root = Path(root)
    errors = []
    for name, expected in ARCHIVE_SHA256.items():
        path = root/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append('Changed/missing archived unmerged eye candidate: '+name)
    try:
        inventory = load_json(root/ARCHIVE_PATH/'inventory.json')
        metadata = {ARCHIVE_PATH+'/'+name for name in ('inventory.json', 'README.md', '.gitattributes')}
        expected_files = {name: digest for name, digest in ARCHIVE_SHA256.items() if name not in metadata}
        if (set(inventory) != {'status', 'original_scene_sha256', 'files_sha256'}
                or inventory['status'] != 'superseded_unmerged_candidate'
                or inventory['original_scene_sha256'] != ARCHIVED_CANDIDATE_SHA256
                or inventory['files_sha256'] != expected_files):
            errors.append('Wrong/shrunken archived candidate classification or fixed inventory')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append('Malformed/missing archived candidate inventory: '+str(exc))
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
        'archived_candidate_sha256': table_shape(ARCHIVE_SHA256, 'sha256'),
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


def validate_eyes(root=ROOT, proof=None, decision=None):
    """Admit exact current artifacts only after complete machine and manual proof."""
    root = Path(root)
    folder = root/REVIEW_PATH
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    def bound(path, digest):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append('Stale/missing Goal 19 bound evidence: '+str(path))
    try:
        errors += validate_candidate_archive(root)
        if errors:
            return errors
        cfg = load_json(root/'design/eyes_lookdev.json')
        baseline = load_json(root/'validation/reviews/materials_v01/reload_b_checks.json')
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
             and proof['milestone'] == decision['milestone'] == 'eyes_v01'
             and proof['design_approval'] is False,
             'Wrong Goal 19 version/scope or conflated automatic approval')
        need(proof['baseline_commit'] == BASELINE_COMMIT
             and proof['baseline_scene_sha256'] == BASELINE_SHA256,
             'Wrong accepted Goal 18 predecessor')
        bound(root/BASELINE_SCENE, BASELINE_SHA256)
        need((root/BASELINE_SCENE).stat().st_size == BASELINE_SIZE_BYTES, 'Accepted predecessor size differs')
        need(proof['protected_predecessor_sha256'] == PROTECTED_SHA256,
             'Untrusted/shrunken historical predecessor inventory')
        need(proof['archived_candidate_sha256'] == ARCHIVE_SHA256,
             'Untrusted/shrunken unmerged candidate archive inventory')
        for name, digest in PROTECTED_SHA256.items():
            bound(root/name, digest)
        for name, digest in proof['source_sha256'].items():
            bound(root/name, digest)
        for name, digest in proof['reference_sha256'].items():
            bound(root/'references/approved'/name, digest)
        need(proof['scene_path'] == SCENE_PATH and proof['scene_size_bytes'] > BASELINE_SIZE_BYTES,
             'Wrong or empty new Goal 19 production scene')
        bound(root/SCENE_PATH, proof['scene_sha256'])
        need((root/SCENE_PATH).stat().st_size == proof['scene_size_bytes'], 'New Goal 19 scene size differs')
        for name, digest in proof['evidence_sha256'].items():
            bound(folder/name, digest)
        for name, digest in decision['evidence_sha256'].items():
            bound(folder/name, digest)
        actual = {mode: load_json(folder/(mode+'_checks.json')) for mode in MODES}
        for mode, data in actual.items():
            errors += validate_worker_semantics(data, cfg, baseline, mode == 'build')
        need(actual['build'] == proof['build'], 'Declared Goal 19 build differs from actual bound worker JSON')
        need(actual['saved_build'] == actual['reload_a'] == actual['reload_b'] == proof['reloaded'],
             'Fresh saved-build/two reload workers differ from declared data')
        need(proof['reload_identical'] is True
             and all(proof['build'][key] == proof['reloaded'][key] for key in RELOAD_FIELDS),
             'Fresh reopening changes required Goal 19 eye/UV/shader/probe fields')
        pixels = {}
        for label in LABELS:
            pixels[label] = {}
            for view in VIEWS:
                with Image.open(folder/'evidence'/label/(view+'.png')) as im:
                    need(im.format == 'PNG' and im.size == (1024, 1024) and im.mode == 'RGBA',
                         'Missing actual 1024px RGBA Goal 19 view: '+label+'/'+view)
                    need(any(low != high for low, high in im.getextrema()),
                         'Empty/flat Goal 19 image: '+label+'/'+view)
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
             'New optical eye scene has no visual change from accepted predecessor')
        need([item['mode'] for item in proof['commands']] == list(MODES),
             'Wrong four fresh Blender command inventory')
        first_argv = proof['commands'][0]['argv']
        for command in proof['commands']:
            mode, argv = command['mode'], command['argv']
            need(command['exit_code'] == 0 and argv[1] == '--background'
                 and argv[3:6] == ['--python-exit-code', '1', '--python']
                 and argv[6].replace('\\', '/').endswith('/scripts/blender/eyes_evidence.py')
                 and argv[7:9] == ['--', '--work'] and argv[10:] == ['--mode', mode]
                 and argv[:10] == first_argv[:10], 'Unproven/changed Blender invocation: '+mode)
            log = (folder/(mode+'.log')).read_text(encoding='utf-8')
            need('EYES EVIDENCE OK: '+mode in log and 'Blender ' in log,
                 'Bound worker log lacks successful actual Blender completion: '+mode)
        need(decision['status'] == 'eyes_lookdev_accepted' and decision['blocking_findings'] == [],
             'Manual final-scene Goal 19 review not accepted')
        need(decision['scene_sha256'] == proof['scene_sha256'], 'Manual Goal 19 decision names another scene')
        bound(folder/'verification.json', decision['verification_sha256'])
        need(decision['verification_sha256'] == decision['evidence_sha256']['verification.json'],
             'Manual Goal 19 decision verification bindings disagree')
        need(decision['reference_authority'] == list(REFERENCE_AUTHORITY),
             'Wrong Goal 19 visual reference hierarchy')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['views'].values()),
             'Missing written findings in one of four fixed Goal 19 views')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['criteria'].values()),
             'Unresolved or unsupported Goal 19/F03 commissioned acceptance criterion')
        errors += validate_materials(root)
        return errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return errors+[f'Malformed/missing Goal 19 delivery: {exc}']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate_eyes(args.root)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print('EYES DELIVERY VALID: optical layers, iris network/F03, canonical workers/pixels, preserved history')


if __name__ == '__main__':
    main()
