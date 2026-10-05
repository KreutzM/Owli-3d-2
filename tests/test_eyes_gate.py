"""Goal 19 own producer boundaries, anchored history and optical/runtime negatives."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from eyes_contracts import (PROTECTED_SHA256, SOURCES, REFERENCE_NAMES, REVIEW_PATH,
                           SCENE_PATH, MODES, EVIDENCE_NAMES, VIEWS, ARCHIVE_PATH, ARCHIVE_SHA256, CRITERIA)
from eyes_review import checked_paths, compare_pixels

class EyesInventoryTests(unittest.TestCase):
    def test_all_626_git_lfs_predecessor_bytes_remain_immutable(self):
        self.assertEqual(len(PROTECTED_SHA256), 626)
        for name, digest in PROTECTED_SHA256.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest)


    def test_sources_extend_complete_goal_18_inventory_and_require_own_producers(self):
        from materials_contracts import SOURCES as previous
        self.assertTrue(set(previous).issubset(SOURCES))
        self.assertEqual(len(REFERENCE_NAMES), 9)
        self.assertEqual(len(SOURCES), len(set(SOURCES)))
        for name in ('design/eyes_lookdev.json', 'scripts/blender/eyes_geometry.py',
                     'scripts/blender/eyes_checks.py', 'scripts/blender/eyes_evidence.py',
                     'scripts/eyes_gate.py'):
            self.assertIn(name, SOURCES)
        self.assertIn('design/materials.json', PROTECTED_SHA256)
        for mode in MODES:
            self.assertIn(mode+'_checks.json', EVIDENCE_NAMES)

    def test_producer_accepts_only_fresh_explicit_tmp_and_fixed_own_output(self):
        with tempfile.TemporaryDirectory() as parent:
            # Windows runners can expose an 8.3 alias (RUNNER~1) for Temp;
            # checked_paths returns canonical resolved paths on every platform.
            root = Path(parent).resolve()
            (root/'tmp').mkdir()
            work = root/'tmp/fresh'
            self.assertEqual(checked_paths(work, root/REVIEW_PATH, root/SCENE_PATH, root),
                             (work, root/REVIEW_PATH, root/SCENE_PATH))
            for wrong_work in (root/'tmp', root/'outside', root/'tmp/../outside'):
                with self.subTest(work=wrong_work), self.assertRaises(ValueError):
                    checked_paths(wrong_work, root/REVIEW_PATH, root/SCENE_PATH, root)
            for wrong_target in ('blender/scene/owli_feathers_v01.blend',
                                 'blender/scene/owli.blend'):
                with self.subTest(target=wrong_target), self.assertRaises(ValueError):
                    checked_paths(work, root/REVIEW_PATH, root/wrong_target, root)
            with self.assertRaises(ValueError):
                checked_paths(work, root/'validation/reviews/feathers_v01', root/SCENE_PATH, root)
            work.mkdir()
            with self.assertRaises(ValueError):
                checked_paths(work, root/REVIEW_PATH, root/SCENE_PATH, root)

    def test_runner_reads_actual_canonical_pixels_and_rejects_corruption(self):
        from materials_contracts import VIEWS
        with tempfile.TemporaryDirectory() as parent:
            work = Path(parent)
            for label in ('neutral', 'reload_a', 'reload_b'):
                folder = work/'renders'/label
                folder.mkdir(parents=True)
                for view in VIEWS:
                    with Image.new('RGBA', (1024, 1024), (2, 7, 13, 255)) as im:
                        im.putpixel((4, 4), (24, 31, 49, 255))
                        im.save(folder/(view+'.png'))
            self.assertEqual(set(compare_pixels(work)), set(VIEWS))
            changed = work/'renders/reload_b/VAL_FRONT.png'
            with Image.open(changed) as im:
                im.putpixel((5, 5), (3, 7, 13, 255))
                im.save(changed)
            with self.assertRaisesRegex(ValueError, 'Canonical rendered pixels differ'):
                compare_pixels(work)

    def test_runner_rejects_wrong_canonical_mode_even_if_all_three_match(self):
        from materials_contracts import VIEWS
        with tempfile.TemporaryDirectory() as parent:
            work = Path(parent)
            for label in ('neutral', 'reload_a', 'reload_b'):
                folder = work/'renders'/label
                folder.mkdir(parents=True)
                for view in VIEWS:
                    with Image.new('RGB', (1024, 1024), (2, 7, 13)) as im:
                        im.save(folder/(view+'.png'))
            with self.assertRaisesRegex(ValueError, 'Canonical render dimensions/mode differ'):
                compare_pixels(work)

def typed_fixture(schema):
    if isinstance(schema, str):
        return {'str': 'fixture', 'plainstr': '', 'sha256': 'a'*64, 'int': 2, 'float': .2,
                'number': .5, 'bool': True, 'NoneType': None}[schema]
    if 'dict' in schema:
        return {key: typed_fixture(value) for key, value in schema['dict'].items()}
    if 'keys' in schema:
        return {key: typed_fixture(schema['values']) for key in schema['keys']}
    items = schema['items']
    return [typed_fixture(items[0] if len(items) == 1 else items[index])
            for index in range(schema['list'])]


class EyesCandidateArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name).resolve()
        for name in ARCHIVE_SHA256:
            target = cls.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_145_archived_bytes_and_classification_are_independently_fixed(self):
        from eyes_gate import validate_candidate_archive
        self.assertEqual(len(ARCHIVE_SHA256), 145)
        self.assertEqual(validate_candidate_archive(self.root), [])
        self.assertIn(ARCHIVE_PATH+'/scene.blend', ARCHIVE_SHA256)
        self.assertIn(ARCHIVE_PATH+'/review/independent-visual-review.md', ARCHIVE_SHA256)
        self.assertIn(ARCHIVE_PATH+'/scripts/eyes_contracts.py', ARCHIVE_SHA256)

    def test_actual_archived_report_byte_mutation_rejects(self):
        from eyes_gate import validate_candidate_archive
        path = self.root/ARCHIVE_PATH/'review/independent-visual-review.md'
        original = path.read_bytes()
        try:
            path.write_bytes(original+b'\nChanged later acceptance claim\n')
            self.assertTrue(validate_candidate_archive(self.root))
        finally:
            path.write_bytes(original)
        self.assertEqual(validate_candidate_archive(self.root), [])

    def test_shrunken_candidate_inventory_rejects_even_when_remaining_files_exist(self):
        from eyes_gate import validate_candidate_archive
        path = self.root/ARCHIVE_PATH/'inventory.json'
        original = path.read_bytes()
        try:
            candidate = json.loads(original)
            candidate['files_sha256'].pop(next(iter(candidate['files_sha256'])))
            path.write_text(json.dumps(candidate), encoding='utf-8')
            errors = validate_candidate_archive(self.root)
            self.assertTrue(any('fixed inventory' in error for error in errors))
        finally:
            path.write_bytes(original)
        self.assertEqual(validate_candidate_archive(self.root), [])


class EyesStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import eyes_gate as gate
        cls.gate = gate
        cls.cfg = json.loads((ROOT/'design/eyes_lookdev.json').read_bytes())
        cls.baseline = json.loads((ROOT/'validation/reviews/materials_v01/reload_b_checks.json').read_bytes())
        cls.schema = gate.worker_shape(cls.cfg, cls.baseline)
        cls.fixture = typed_fixture(cls.schema)

    def test_all_13_criteria_include_and_require_the_renewed_user_findings(self):
        self.assertEqual(len(CRITERIA), 13)
        decision = typed_fixture(self.gate.DECISION_SHAPE)
        self.assertEqual(self.gate.validate_shape(decision, self.gate.DECISION_SHAPE), [])
        for name in ('F03_reflex_dominance', 'F03_iris_variation', 'F03_network_branching', 'F03_lid_integration'):
            self.assertIn(name, CRITERIA)
            candidate = copy.deepcopy(decision)
            del candidate['criteria'][name]
            with self.subTest(criterion=name):
                self.assertTrue(self.gate.validate_shape(candidate, self.gate.DECISION_SHAPE))
        self.assertIn('eyes_refinement_before_after.png', EVIDENCE_NAMES)

    def test_code_owned_recursive_reload_fields_and_95_preserved_states(self):
        self.assertEqual(set(self.schema['dict']), set(self.gate.RELOAD_FIELDS))
        self.assertEqual(len(self.gate.RELOAD_FIELDS), 30)
        self.assertEqual(self.gate.validate_worker_structure(self.fixture, self.cfg, self.baseline), [])
        self.assertEqual(len(self.schema['dict']['unchanged_non_eye_sha256']['dict']), 95)
        self.assertEqual(len(self.schema['dict']['eye_materials']['dict']), 4)
        self.assertEqual(len(self.schema['dict']['eye_geometry']['dict']), 8)
        self.assertEqual(len(self.gate.PRESERVED_NON_EYES), 90)
        self.assertEqual(len(self.schema['dict']['socket_geometry']['dict']), 5)
        self.assertEqual(len(self.schema['dict']['normals_audit']['dict']), 103)
        self.assertEqual(len(self.schema['dict']['movement']['dict']['eye_function']['dict']['lid_pose_normals_sha256']['dict']), 41)

    def test_missing_or_empty_whole_reload_field_is_rejected(self):
        for field in self.gate.RELOAD_FIELDS:
            for invalid in (None, {}, []):
                candidate = dict(self.fixture)
                candidate[field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assertTrue(self.gate.validate_worker_structure(candidate, self.cfg, self.baseline))
            candidate = dict(self.fixture)
            del candidate[field]
            self.assertTrue(self.gate.validate_worker_structure(candidate, self.cfg, self.baseline))

    def test_recursive_nested_eye_fields_and_lists_require_coverage(self):
        def visit(value, schema, path):
            if isinstance(schema, str):
                return
            if 'dict' in schema or 'keys' in schema:
                required = schema.get('dict')
                if required is None:
                    required = {key: schema['values'] for key in schema['keys']}
                for key, child in required.items():
                    omission = dict(value)
                    del omission[key]
                    self.assertTrue(self.gate.validate_shape(omission, schema, path), path+'/'+key)
                    visit(value[key], child, path+'/'+key)
            else:
                items = schema['items']
                if value:
                    self.assertTrue(self.gate.validate_shape(value[:-1], schema, path), path)
                for index in (range(len(value)) if len(items) != 1 else range(min(len(value), 1))):
                    visit(value[index], items[0] if len(items) == 1 else items[index], path+'/'+str(index))
        for field in ('eye_materials', 'eye_geometry', 'eye_layers', 'unchanged_non_eye_sha256',
                      'uv_state_sha256', 'attributes_state_sha256', 'pivot_state_sha256', 'eye_local_shape_sha256',
                      'normals_state_sha256', 'normals_audit', 'socket_geometry', 'socket_state_sha256'):
            visit(self.fixture[field], self.schema['dict'][field], field)

    def test_type_mismatch_and_extra_eye_roles_are_rejected(self):
        candidate = copy.deepcopy(self.fixture)
        candidate['eye_layers']['L']['projected_pupil_iris_ratio'] = True
        self.assertTrue(self.gate.validate_worker_structure(candidate, self.cfg, self.baseline))
        candidate = copy.deepcopy(self.fixture)
        candidate['eye_materials']['Extra_Coat'] = candidate['eye_materials']['Eye_Cornea']
        self.assertTrue(self.gate.validate_worker_structure(candidate, self.cfg, self.baseline))

    def test_old_validator_projection_preserves_90_and_every_actual_runtime_probe(self):
        projected = self.gate._historical_projection(self.fixture, self.baseline)
        for name in self.gate.PRESERVED_NON_EYES:
            self.assertEqual(projected['shape_sha256'][name], self.fixture['shape_sha256'][name])
            self.assertEqual(projected['geometry_sha256'][name], self.fixture['geometry_sha256'][name])
            self.assertEqual(projected['assignments'][name], self.fixture['assignments'][name])
        self.assertEqual(projected['movement'], {k:v for k,v in self.fixture['movement'].items() if k != 'eye_function'})
        for field in ('feet', 'materials', 'new_meshes', 'tech_meshes', 'studio'):
            self.assertEqual(projected[field], self.fixture[field])

    def test_authored_eye_graphs_and_recomputed_hash_are_valid(self):
        from eyes_contracts import EXPECTED_EYE_GRAPHS
        for role, graph in EXPECTED_EYE_GRAPHS.items():
            material = {'graph': copy.deepcopy(graph), 'shader_sha256': self.gate.digest(graph)}
            self.assertEqual(self.gate.validate_eye_material_semantics(role, material), [])

    def test_self_consistent_unsafe_gloss_ior_network_and_link_changes_reject(self):
        from eyes_contracts import EXPECTED_EYE_GRAPHS
        mutations = [
            ('Eye_Cornea', lambda g: g['nodes']['Surface']['inputs'][1].update(default=.8)),
            ('Eye_Cornea', lambda g: g['nodes']['OpticalFresnel']['inputs'][0].update(default=2.2)),
            ('Eye_Iris', lambda g: g['links'].pop()),
            ('Eye_Iris', lambda g: g['nodes']['SubtleNetwork']['inputs'][1].update(default=1.0)),
            ('Eye_Iris', lambda g: g['nodes']['BlueCyanDepth']['ramp']['stops'][0][1].__setitem__(0, 1.0)),
            ('Eye_Pupil', lambda g: g['nodes']['Surface']['inputs'][1].update(default=1.0)),
        ]
        for role, change in mutations:
            graph = copy.deepcopy(EXPECTED_EYE_GRAPHS[role]); change(graph)
            material = {'graph': graph, 'shader_sha256': self.gate.digest(graph)}
            with self.subTest(role=role):
                self.assertTrue(self.gate.validate_eye_material_semantics(role, material))

    def test_contradictory_shader_digest_rejects(self):
        from eyes_contracts import EXPECTED_EYE_GRAPHS
        graph = copy.deepcopy(EXPECTED_EYE_GRAPHS['Eye_Cornea'])
        self.assertTrue(self.gate.validate_eye_material_semantics('Eye_Cornea',
            {'graph': graph, 'shader_sha256': 'a'*64}))


class EyesDeliveredNegatives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import eyes_gate as gate
        cls.gate = gate
        cls.cfg = json.loads((ROOT/'design/eyes_lookdev.json').read_bytes())
        cls.baseline = json.loads((ROOT/'validation/reviews/materials_v01/reload_b_checks.json').read_bytes())
        cls.actual = json.loads((ROOT/REVIEW_PATH/'reload_b_checks.json').read_bytes())

    def test_delivered_full_worker_has_complete_safe_commissioned_semantics(self):
        self.assertEqual(self.gate.validate_worker_semantics(self.actual, self.cfg, self.baseline), [])

    def test_socket_exceptions_do_not_admit_a_sixth_mesh_or_changed_mask(self):
        for mode in ('sixth', 'mask'):
            value = copy.deepcopy(self.actual)
            if mode == 'sixth':
                value['socket_state_sha256']['FAC_Mask_L'] = 'a'*64
            else:
                value['unchanged_non_eye_sha256']['FAC_Mask_L'] = 'a'*64
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_actual_normals_require_full_corners_units_and_protected_scope(self):
        for mode in ('protected', 'nonunit', 'missing', 'custom'):
            value = copy.deepcopy(self.actual)
            if mode == 'protected':
                value['normals_state_sha256']['FAC_Mask_L'] = 'a'*64
            elif mode == 'nonunit':
                value['normals_audit']['FAC_Lid_Upper_L']['maximum_unit_error'] = .1
            elif mode == 'missing':
                value['normals_audit']['FAC_Lid_Upper_L']['normal_count'] -= 1
            else:
                value['normals_audit']['FAC_Lid_Upper_L']['has_custom_normals'] = False
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_lid_pose_normal_trajectory_and_neutral_restoration_are_required(self):
        for mode in ('sample', 'neutral', 'hash'):
            value = copy.deepcopy(self.actual)
            function = value['movement']['eye_function']
            if mode == 'sample':
                function['lid_pose_normals_sha256'].pop('0.500')
            elif mode == 'neutral':
                function['neutral_normals_restored'] = False
            else:
                function['lid_pose_normals_sha256']['0.500']['FAC_Lid_Upper_L'] = 'a'*64
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_documented_pivot_depth_keeps_local_globe_cornea_and_other_pivots(self):
        for mode in ('local', 'center_x', 'center_y', 'other_pivot'):
            value = copy.deepcopy(self.actual)
            if mode == 'local':
                value['eye_local_shape_sha256']['FAC_Cornea_L'] = 'a'*64
            elif mode == 'center_x':
                value['eye_layers']['L']['center_m'][0] += .001
            elif mode == 'center_y':
                value['eye_layers']['L']['center_m'][1] += .001
            else:
                value['pivot_state_sha256']['BAK_LowerPivot'] = 'a'*64
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_serialized_actual_eye_geometry_hash_contradiction_rejects(self):
        from eyes_contracts import EYES
        for name in EYES:
            value = copy.deepcopy(self.actual)
            value['geometry_sha256'][name] = 'a'*64
            with self.subTest(eye=name):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_any_individual_blink_clearance_and_aggregate_contradiction_reject(self):
        for mode in ('individual', 'aggregate'):
            value = copy.deepcopy(self.actual)
            blink = value['movement']['blink_and_gaze']
            if mode == 'individual':
                key = next(iter(blink['minimum_triangle_clearance_m']))
                blink['minimum_triangle_clearance_m'][key] = -.001
            else:
                blink['minimum_clearance_m'] += .001
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_non_eye_uv_fullstate_and_pivot_mutation_reject(self):
        for field in ('unchanged_non_eye_sha256', 'uv_state_sha256', 'attributes_state_sha256', 'pivot_state_sha256'):
            value = copy.deepcopy(self.actual)
            value[field][next(iter(value[field]))] = 'a'*64
            with self.subTest(field=field):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_layer_overlap_or_ratio_or_removed_audit_reject(self):
        for mode in ('collision', 'ratio', 'triangle'):
            value = copy.deepcopy(self.actual)
            if mode == 'collision':
                pairs = value['eye_layers']['L']['layer_collision_pairs']
                pairs[next(iter(pairs))] = 1
            elif mode == 'ratio':
                value['eye_layers']['L']['projected_pupil_iris_ratio'] = .75
            else:
                value['eye_geometry']['FAC_Pupil_L']['cage_triangles']['interior_crossings'] = 1
            with self.subTest(mode=mode):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))

    def test_missing_partial_runtime_trajectory_reject(self):
        for field, member in (('blink_and_gaze', 'blink_samples'), ('beak_opening', 'opening_samples'),
                              ('tech_function', 'target_meshes'), ('wing_gestures', 'states')):
            value = copy.deepcopy(self.actual)
            value['movement'][field][member].pop()
            with self.subTest(field=field):
                self.assertTrue(self.gate.validate_worker_semantics(value, self.cfg, self.baseline))


if __name__ == '__main__':
    unittest.main()
