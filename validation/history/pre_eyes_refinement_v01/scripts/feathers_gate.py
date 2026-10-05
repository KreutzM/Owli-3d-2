"""Strict #6 delivery admission: actual workers, preserved history, and real pixels.

This verifies a geometric feather milestone. Final materials, complete rig controls,
and combined animation QA retain their assigned later goals.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from delivery_gates import validate_all
from delivery_shapes import RELOAD_SHAPES
from review_fixes_gate import validate_review_fixes
from feathers_contracts import (
    ARCHIVED_STAGE_SHA256, BASELINE_COMMIT, BASELINE_SCENE, BASELINE_SHA256,
    BASELINE_SIZE_BYTES, PROTECTED_SHA256, REFERENCE_AUTHORITY, REFERENCE_NAMES,
    RELOAD_FIELDS, REMOVED_MESHES, REVIEW_PATH, SCENE_PATH, SOURCES, VIEWS,
    CRITERIA, EVIDENCE_NAMES, MANUAL_EVIDENCE_NAMES, MODES, LABELS,
    CENTRAL_LAYER_IDS,
)

ROOT = Path(__file__).resolve().parents[1]


def object_shape(fields):
    return {'dict': fields}


def table_shape(keys, value):
    return {'dict': {key: value for key in sorted(keys)}}


def sequence_shape(length, item):
    return {'list': length, 'items': [item]}


def validate_shape(value, schema, path='worker'):
    """Exact recursive coverage, including legitimate typed empty lists/null parents."""
    if isinstance(schema, str):
        if schema == 'number':
            valid = type(value) in (int, float) and math.isfinite(value)
        elif schema == 'sha256':
            valid = (isinstance(value, str) and len(value) == 64
                     and all(c in '0123456789abcdef' for c in value))
        else:
            valid = type(value).__name__ == schema
            if valid and schema == 'str':
                valid = bool(value.strip())
            if valid and schema == 'float':
                valid = math.isfinite(value)
        return [] if valid else [f'{path}: invalid or missing {schema}']
    if 'dict' in schema or 'keys' in schema:
        required = schema.get('dict')
        if required is None:
            required = {key: schema['values'] for key in schema['keys']}
        if not isinstance(value, dict) or set(value) != set(required):
            return [f'{path}: incomplete or unexpected object fields']
        return [error for key, child in required.items()
                for error in validate_shape(value[key], child, path+'/'+key)]
    if not isinstance(value, list) or len(value) != schema['list']:
        return [f'{path}: incomplete or unexpected sequence']
    items = schema['items']
    return [error for index, item in enumerate(value)
            for error in validate_shape(item, items[0] if len(items) == 1 else items[index],
                                        path+'/'+str(index))]


def expected_mesh_names(cfg):
    """Derive the executable parameter inventory, requiring every commissioned region."""
    names = {'FTH_WingPrimary_L', 'FTH_WingPrimary_R', 'FTH_TailPrimary'}
    for key in ('wing_layers', 'back_layers', 'chest_layers', 'tail_layers', 'face_layers'):
        entries = cfg[key]
        if not isinstance(entries, list) or not 2 <= len(entries) <= 12:
            raise ValueError('Missing/non-broad commissioned region: '+key)
        if len({entry['id'] for entry in entries}) != len(entries):
            raise ValueError('Duplicate feather group IDs: '+key)
        for entry in entries:
            identifier = entry['id']
            if not isinstance(identifier, str) or not identifier or not identifier.isalnum():
                raise ValueError('Invalid feather group ID: '+key)
            if key == 'wing_layers':
                centers = entry['centers']
                if not isinstance(centers, list) or not 2 <= len(centers) <= 8:
                    raise ValueError('Missing/bloated broad wing layer columns')
                names.update(f'FTH_Wing_{identifier}_{i}_{side}'
                             for i in range(len(centers)) for side in ('L', 'R'))
            elif key == 'tail_layers' and identifier == 'Center':
                names.add('FTH_TailCenter')
            else:
                prefix = ('FTH_Tail' if key == 'tail_layers' else
                          'FTH_Face' if key == 'face_layers' else 'FTH_')
                names.update(prefix+identifier+'_'+side for side in ('L', 'R'))
    central = cfg['central_layers']
    if (not isinstance(central, list) or len(central) != 3
            or {entry['id'] for entry in central} != set(CENTRAL_LAYER_IDS)):
        raise ValueError('Missing exact continuous head/body/chest central groups')
    names.update('FTH_'+identifier for identifier in CENTRAL_LAYER_IDS)
    if 'FTH_TailCenter' not in names or not 12 <= len(names) <= 80:
        raise ValueError('Compact centered tail or bounded broad groups missing')
    return names


CAGE_SHAPE = RELOAD_SHAPES['face_v01']['meshes']['values']
TRIANGLE_SHAPE = object_shape({
    'triangles': 'int', 'adjacent_interiors_included': 'bool', 'interior_crossings': 'int',
    'minimum_polygon_triangle_normal_dot': 'float', 'maximum_boundary_inset_m': 'float',
    'coplanar_candidate_checks': 'int', 'coplanar_overlap_area_tolerance_m2': 'float',
    'coplanar_plane_tolerance_m': 'float',
})
NEW_MESH_SHAPE = object_shape({'cage': CAGE_SHAPE, 'cage_triangles': TRIANGLE_SHAPE,
                               'evaluated_triangles': TRIANGLE_SHAPE})
FOOT_FIELDS = ('surfaces', 'contacts', 'toe_branches', 'penetration_tolerance_m',
               'pad_support_contact_m', 'independent_surface_collision_pairs')
FEET_SHAPE = object_shape({key: RELOAD_SHAPES['feet_v01'][key] for key in FOOT_FIELDS})
VEC3_SHAPE = sequence_shape(3, 'float')
FRAME_OBJECT_SHAPE = object_shape({'min': VEC3_SHAPE, 'max': VEC3_SHAPE,
                                  'inside_safe_frame': 'bool'})


def worker_shape(cfg, baseline, build=False):
    names = expected_mesh_names(cfg)
    unchanged = set(baseline['geometry_sha256'])-set(REMOVED_MESHES)
    all_names = names | unchanged
    wings = {name for name in names if name.startswith('FTH_Wing')}
    bindings = {}
    for name in sorted(names):
        fields = {'parent': 'str' if name in wings else 'NoneType',
                  'collections': sequence_shape(1, 'str'),
                  'vertex_groups': sequence_shape(1 if name in wings else 0, 'str'),
                  'modifiers': sequence_shape(0, 'str'), 'part': 'str'}
        if name in wings:
            fields.update(rest_sha256='sha256', minimum_weight='float', maximum_weight='float')
        bindings[name] = object_shape(fields)
    frame = object_shape({'objects': table_shape(all_names, FRAME_OBJECT_SHAPE),
                          'object_count': 'int', 'minimum_image_margin': 'float',
                          'inside_safe_frame': 'bool'})
    part_motion = object_shape({'maximum_vertex_displacement_m': 'float', 'fixed_root_drift_m': 'number',
                                'cage': CAGE_SHAPE, 'triangle_interiors': TRIANGLE_SHAPE})
    gesture = object_shape({'left': 'number', 'right': 'number', 'parts': table_shape(wings, part_motion),
                            'foot_collision_checks': 'int'})
    function = object_shape({
        'blink_samples': sequence_shape(41, 'float'), 'blink_collision_checks': 'int',
        'gaze_probes': sequence_shape(4, object_shape({'axis': 'str', 'degrees': 'int', 'collision_checks': 'int'})),
        'beak_samples': sequence_shape(41, 'float'), 'beak_collision_checks': 'int',
        'target_meshes': sequence_shape(len(names), 'str'),
    })
    fields = {
        'geometry_sha256': table_shape(all_names, 'sha256'),
        'new_meshes': table_shape(names, NEW_MESH_SHAPE),
        'bindings': object_shape(bindings),
        'symmetry': table_shape({name for name in names if name.endswith('_R')},
                               object_shape({'vertices': 'int', 'maximum_mirror_deviation_m': 'float'})),
        'root_contacts': table_shape(('L', 'R'), object_shape({
            'fixed_root_vertices': 'int', 'minimum_signed_nearest_distance_m': 'float',
            'maximum_signed_nearest_distance_m': 'float'})),
        'leaf_roots': table_shape(names-{'FTH_WingPrimary_L', 'FTH_WingPrimary_R', 'FTH_TailPrimary'},
                                 object_shape({'support': 'str', 'samples': 'int',
                                               'embedded_back_samples': 'int',
                                               'maximum_front_root_distance_m': 'float',
                                               'minimum_back_signed_distance_m': 'float'})),
        'feet': FEET_SHAPE,
        'studio': RELOAD_SHAPES['face_v01']['studio'],
        'framing': table_shape(VIEWS, frame),
        'counts': object_shape({name: 'int' for name in
                              ('objects', 'meshes', 'new_meshes', 'feather_leaves', 'armatures', 'actions')}),
        'movement': object_shape({
            'blink_and_gaze': RELOAD_SHAPES['face_v01']['probes'],
            'beak_opening': RELOAD_SHAPES['beak_v01']['opening_probes'],
            'feather_function': function,
            'wing_gestures': object_shape({'states': sequence_shape(6, gesture), 'neutral_restored': 'bool'}),
        }),
    }
    if build:
        fields.update(unchanged_part_sha256=table_shape(unchanged, 'sha256'),
                      repeated_build_identical='bool', datablock_counts=sequence_shape(3, 'int'))
    return object_shape(fields)


def validate_worker_structure(data, cfg, baseline, build=False):
    return validate_shape(data, worker_shape(cfg, baseline, build))


def validate_worker_semantics(data, cfg, baseline, build=False):
    """Require measured geometry and full commissioned functional coverage."""
    errors = validate_worker_structure(data, cfg, baseline, build)
    if errors:
        return errors
    def need(condition, message):
        if not condition:
            errors.append(message)
    def surface(cage, triangles, name):
        need(cage['closed_connected'] is True and cage['outward_consistent_normals'] is True
             and cage['self_intersections'] == 0 and cage['duplicate_vertices'] == 0
             and cage['vertices'] > 4 and cage['polygons'] > 4
             and cage['euler_characteristic'] == 2 and cage['volume_m3'] > 0
             and cage['minimum_polygon_area_m2'] > 0, 'Invalid closed editable #6 surface: '+name)
        need(triangles['triangles'] == 2*cage['polygons']
             and triangles['adjacent_interiors_included'] is True
             and triangles['interior_crossings'] == 0
             and triangles['minimum_polygon_triangle_normal_dot'] > 0
             and 0 <= triangles['maximum_boundary_inset_m'] < .0001
             and triangles['coplanar_candidate_checks'] >= 0
             and triangles['coplanar_overlap_area_tolerance_m2'] == 1e-12
             and triangles['coplanar_plane_tolerance_m'] == 1e-8,
             'Missing/failed adjacent or coplanar #6 triangle check: '+name)
    names = expected_mesh_names(cfg)
    unchanged = {name: digest for name, digest in baseline['geometry_sha256'].items()
                 if name not in REMOVED_MESHES}
    wings = {name for name in names if name.startswith('FTH_Wing')}
    need(all(data['geometry_sha256'][name] == digest for name, digest in unchanged.items()),
         'Changed unrelated accepted #37 mesh')
    if build:
        need(data['unchanged_part_sha256'] == unchanged and data['repeated_build_identical'] is True,
             'Missing repeated build or exact preservation')
        need(data['datablock_counts'][:2] == [data['counts']['objects'], data['counts']['meshes']]
             and data['datablock_counts'][2] == 7, 'Leaked or missing #6 build datablocks')
    for name, mesh in data['new_meshes'].items():
        surface(mesh['cage'], mesh['cage_triangles'], name)
        surface(mesh['cage'], mesh['evaluated_triangles'], name+' evaluated')
        binding = data['bindings'][name]
        need(binding['modifiers'] == [], 'Unreviewed #6 modifier: '+name)
        if name in ('FTH_WingPrimary_L', 'FTH_WingPrimary_R', 'FTH_TailPrimary'):
            part = 'primary'
        elif name.startswith('FTH_Wing_'):
            part = 'wing'
        elif name.startswith('FTH_Tail'):
            part = 'tail'
        elif name.startswith('FTH_Face'):
            part = 'face'
        elif name in ('FTH_HeadCenter', 'FTH_BodyCenter') or any(name == 'FTH_'+entry['id']+'_'+side
                 for entry in cfg['back_layers'] for side in ('L', 'R')):
            part = 'body_back'
        else:
            part = 'body_chest'
        need(binding['part'] == part, 'Wrong commissioned feather region: '+name)
        if name in wings:
            side = name[-1]
            need(binding['parent'] == 'FTH_WingRoot_'+side and binding['vertex_groups'] == ['wing_gesture']
                 and 0 <= binding['minimum_weight'] < 1 and binding['maximum_weight'] == 1,
                 'Missing shared wing root/rest field: '+name)
            need(binding['collections'] == ['WINGS' if 'Primary' in name else 'FEATHERS'],
                 'Wrong wing grouping: '+name)
        else:
            need(binding['parent'] is None and binding['vertex_groups'] == []
                 and binding['collections'] == ['FEATHERS'], 'Wrong editable feather grouping: '+name)
        if name in data['symmetry']:
            mirror = data['symmetry'][name]
            need(mirror['vertices'] == mesh['cage']['vertices']
                 and 0 <= mirror['maximum_mirror_deviation_m'] < 2e-6,
                 'Actual reflected geometry differs: '+name)
    for side, contact in data['root_contacts'].items():
        need(contact['fixed_root_vertices'] > 32 and contact['minimum_signed_nearest_distance_m'] < -.001
             and contact['maximum_signed_nearest_distance_m'] >= contact['minimum_signed_nearest_distance_m'],
             'Shoulder lacks measured attachment: '+side)
    for name, contact in data['leaf_roots'].items():
        if name.startswith('FTH_Wing_'):
            supports = {'FTH_WingPrimary_'+name[-1]}
        elif name.startswith('FTH_Tail'):
            supports = {'FTH_TailPrimary'}
        elif name.startswith('FTH_Face'):
            supports = {'FAC_Mask_'+name[-1], 'FAC_MaskBridge', 'PRI_HeadNeckTorso'}
        else:
            supports = {'PRI_HeadNeckTorso'}
        need(contact['support'] in supports, 'Wrong actual supporting primary for feather root: '+name)
        need(contact['samples'] == cfg['leaf_cross_segments']+1 == 9
             and 0 < contact['embedded_back_samples'] <= contact['samples']
             and 0 <= contact['maximum_front_root_distance_m'] < .0015
             and contact['minimum_back_signed_distance_m'] < -.0001,
             'Floating or incompletely sampled actual feather root: '+name)
    for view, frame in data['framing'].items():
        need(frame['object_count'] == len(names)+len(unchanged) and frame['inside_safe_frame'] is True
             and frame['minimum_image_margin'] > 0
             and all(item['inside_safe_frame'] is True for item in frame['objects'].values()),
             'Actual four-view silhouette clips fixed studio: '+view)
    current_studio, old_studio = copy.deepcopy(data['studio']), copy.deepcopy(baseline['studio'])
    current_studio.pop('scene_object_count')
    old_studio.pop('scene_object_count')
    need(current_studio == old_studio, 'Fixed accepted studio changed')
    counts = data['counts']
    need(counts['new_meshes'] == len(names) and counts['meshes'] == len(names)+len(unchanged)
         and counts['feather_leaves'] == len(names)-3 and counts['armatures'] == counts['actions'] == 0
         and counts['objects'] == counts['meshes']+14
         and data['studio']['scene_object_count'] == counts['objects'], 'Wrong bounded #6 scene inventory')
    feet = data['feet']
    need(feet == baseline['feet'], 'Actual 3+1 anatomy/contact probe differs from accepted #37')
    need(feet['independent_surface_collision_pairs'] == 45
         and sum(contact['rear'] for contact in feet['contacts'].values()) == 2
         and all(contact['nearest_surface_distance_m'] < 2e-7
                 and contact['minimum_polygon_halfspace_distance_m'] >= -feet['penetration_tolerance_m']
                 for contact in feet['contacts'].values()), 'Eight claw/bar grip contacts failed')
    face, beak = data['movement']['blink_and_gaze'], data['movement']['beak_opening']
    beak_targets = {name for name in unchanged
                   if name.startswith(('FAC_', 'PRI_Head', 'BLK_Chest', 'BLK_Forehead'))}
    need(face['blink_samples'] == [i/40 for i in range(41)] and face['minimum_clearance_m'] >= .0003
         and face['closed_coverage_rays'] >= 10000 and face['full_close_front_and_back_seam_gap_m'] == 0
         and [(v['axis'], v['degrees']) for v in face['gaze_probes']] == [('X', -12), ('X', 12), ('Z', -12), ('Z', 12)]
         and all(v['no_collisions'] is True for v in face['gaze_probes']),
         'Incomplete or unsafe full blink/gaze trajectory')
    need(beak['opening_samples'] == [i/40 for i in range(41)] and beak['upper_fixed'] is True
         and beak['collision_checks'] == 41*(2*len(beak_targets)+1)
         and beak['minimum_sampled_mask_clearance_m'] >= .0003
         and beak['front_lower_vertex_drop_m'] > .004, 'Incomplete or unsafe 0–18 degree beak trajectory')
    function = data['movement']['feather_function']
    need(function['target_meshes'] == sorted(names)
         and function['blink_samples'] == function['beak_samples'] == [i/40 for i in range(41)]
         and function['blink_collision_checks'] == 41*4*len(names)
         and function['beak_collision_checks'] == 41*2*len(names)
         and [(v['axis'], v['degrees']) for v in function['gaze_probes']] == [('X', -12), ('X', 12), ('Z', -12), ('Z', 12)]
         and all(v['collision_checks'] == 8*len(names) for v in function['gaze_probes']),
         'Missing actual lid/eye/beak checks against every new feather, including face groups')
    gestures = data['movement']['wing_gestures']
    need(gestures['neutral_restored'] is True
         and [(state['left'], state['right']) for state in gestures['states']]
         == [(.5, 0), (1, 0), (0, .5), (0, 1), (.5, .5), (1, 1)],
         'Missing isolated/combined half/full gestures or neutral return')
    for index, state in enumerate(gestures['states']):
        need(state['foot_collision_checks'] == len(wings)*len(feet['surfaces']),
             'Incomplete wing/foot/perch collision pair inventory: '+str(index))
        for name, motion in state['parts'].items():
            value = state['left'] if name.endswith('_L') else state['right']
            need((motion['maximum_vertex_displacement_m'] > .003 if value
                  else motion['maximum_vertex_displacement_m'] < 1e-9)
                 and 0 <= motion['fixed_root_drift_m'] < 1e-9,
                 'Wing/layer motion or fixed root failed: '+name+'/'+str(index))
            surface(motion['cage'], motion['triangle_interiors'], name+'/'+str(index))
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


def load_json(path):
    def pairs(items):
        value = {}
        for key, child in items:
            if key in value:
                raise ValueError('Duplicate JSON object key: '+key)
            value[key] = child
        return value
    def nonfinite(token):
        raise ValueError('Nonfinite JSON number: '+token)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs, parse_constant=nonfinite)


def validate_feathers(root=ROOT, proof=None, decision=None):
    """Require the complete, exact, final #6 delivery and all predecessor gates."""
    root = Path(root)
    folder = root/REVIEW_PATH
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    def bound(path, digest):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append('Stale/missing #6 bound evidence: '+str(path))
    try:
        cfg = load_json(root/'design/wings_feathers.json')
        baseline = load_json(root/'validation/reviews/review_fixes_v01/reload_b_checks.json')
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
             and proof['milestone'] == decision['milestone'] == 'feathers_v01'
             and proof['design_approval'] is False, 'Wrong #6 version/scope or conflated automatic approval')
        need(proof['baseline_commit'] == BASELINE_COMMIT and proof['baseline_scene_sha256'] == BASELINE_SHA256,
             'Wrong accepted #37 predecessor')
        bound(root/BASELINE_SCENE, BASELINE_SHA256)
        need((root/BASELINE_SCENE).stat().st_size == BASELINE_SIZE_BYTES, 'Accepted predecessor size differs')
        need(proof['protected_predecessor_sha256'] == PROTECTED_SHA256, 'Untrusted/shrunken historical predecessor inventory')
        for name, digest in PROTECTED_SHA256.items():
            bound(root/name, digest)
        bound(root/'scripts/blender/legacy/30_wings_feathers.py', ARCHIVED_STAGE_SHA256)
        for name, digest in proof['source_sha256'].items():
            bound(root/name, digest)
        for name, digest in proof['reference_sha256'].items():
            bound(root/'references/approved'/name, digest)
        need(proof['scene_path'] == SCENE_PATH and proof['scene_size_bytes'] > BASELINE_SIZE_BYTES,
             'Wrong or empty new #6 production scene')
        bound(root/SCENE_PATH, proof['scene_sha256'])
        need((root/SCENE_PATH).stat().st_size == proof['scene_size_bytes'], 'New #6 scene size differs')
        for name, digest in proof['evidence_sha256'].items():
            bound(folder/name, digest)
        for name, digest in decision['evidence_sha256'].items():
            bound(folder/name, digest)
        actual = {mode: load_json(folder/(mode+'_checks.json')) for mode in MODES}
        for mode, data in actual.items():
            errors += validate_worker_semantics(data, cfg, baseline, mode == 'build')
        need(actual['build'] == proof['build'], 'Declared #6 build differs from actual bound worker JSON')
        need(actual['saved_build'] == actual['reload_a'] == actual['reload_b'] == proof['reloaded'],
             'Fresh canonical build/two reload workers differ from declared data')
        need(proof['reload_identical'] is True
             and all(proof['build'][key] == proof['reloaded'][key] for key in RELOAD_FIELDS),
             'Fresh reopening changes required #6 fields')
        pixels = {}
        for label in LABELS:
            pixels[label] = {}
            for view in VIEWS:
                with Image.open(folder/'evidence'/label/(view+'.png')) as im:
                    need(im.format == 'PNG' and im.size == (1024, 1024) and im.mode == 'RGBA',
                         'Missing actual 1024px RGBA #6 view: '+label+'/'+view)
                    need(any(low != high for low, high in im.getextrema()), 'Empty/flat #6 image: '+label+'/'+view)
                    pixels[label][view] = im.tobytes()
        for view in VIEWS:
            comparison = proof['render_comparison'][view]
            need(comparison == {'size': [1024, 1024], 'mode': 'RGBA',
                                'build_and_two_reloads_pixels_identical': True},
                 'Wrong declared canonical render metadata: '+view)
            need(pixels['neutral'][view] == pixels['reload_a'][view] == pixels['reload_b'][view],
                 'Actual canonical build/two reload PNG pixels differ: '+view)
            with Image.open(folder/(view+'.png')) as published:
                need(published.size == (1024, 1024) and published.mode == 'RGBA'
                     and published.tobytes() == pixels['reload_b'][view],
                     'Published manual-review view differs from canonical scene: '+view)
        for pose in ('blink', 'beak_open', 'gesture_left', 'gesture_right', 'gesture_both'):
            need(any(pixels[pose][view] != pixels['live_neutral'][view] for view in VIEWS),
                 'Actual pose render lacks visible response: '+pose)
        need(any(pixels['baseline'][view] != pixels['neutral'][view] for view in VIEWS),
             'New feather scene has no visual change from accepted predecessor')
        need([item['mode'] for item in proof['commands']] == list(MODES), 'Wrong four fresh Blender command inventory')
        first_argv = proof['commands'][0]['argv']
        for command in proof['commands']:
            mode, argv = command['mode'], command['argv']
            need(command['exit_code'] == 0 and argv[1] == '--background'
                 and argv[3:6] == ['--python-exit-code', '1', '--python']
                 and argv[6].replace('\\', '/').endswith('/scripts/blender/feathers_evidence.py')
                 and argv[7:9] == ['--', '--work'] and argv[10:] == ['--mode', mode]
                 and argv[:10] == first_argv[:10], 'Unproven/changed Blender invocation: '+mode)
            log = (folder/(mode+'.log')).read_text(encoding='utf-8')
            need('FEATHERS EVIDENCE OK: '+mode in log and 'Blender ' in log,
                 'Bound worker log lacks successful actual Blender completion: '+mode)
        need(decision['status'] == 'feathers_geometry_accepted' and decision['blocking_findings'] == [],
             'Manual final-scene #6 review not accepted')
        need(decision['scene_sha256'] == proof['scene_sha256'], 'Manual #6 decision names another scene')
        bound(folder/'verification.json', decision['verification_sha256'])
        need(decision['verification_sha256'] == decision['evidence_sha256']['verification.json'],
             'Manual #6 decision verification bindings disagree')
        need(decision['reference_authority'] == list(REFERENCE_AUTHORITY), 'Wrong #6 visual reference hierarchy')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['views'].values()),
             'Missing written findings in one of four fixed #6 views')
        need(all(item['status'] == 'pass' and item['reason'].strip() for item in decision['criteria'].values()),
             'Unresolved or unsupported #6 commissioned acceptance criterion')
        errors += validate_all(root)
        errors += validate_review_fixes(root)
        return errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return errors+[f'Malformed/missing #6 delivery: {exc}']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate_feathers(args.root)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print('FEATHERS DELIVERY VALID: complete #6 proof, canonical workers/pixels, preserved predecessors')


if __name__ == '__main__':
    main()
