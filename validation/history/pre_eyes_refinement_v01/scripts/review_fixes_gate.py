"""Admission gate for the exact new #37 delivery, not a generic rig/beauty approval."""
import hashlib
import json
from pathlib import Path
from PIL import Image

from delivery_gates import validate_inventory
from evidence_contracts import DELIVERY_INVENTORIES
from review_fixes_contracts import PROTECTED_SHA256

ROOT = Path(__file__).resolve().parents[1]
RELOAD_FIELDS = ('changed_meshes','geometry_sha256','feet','attachment_contacts','studio','pivots','framing','movement')
CHANGED = {'FAC_Mask_L','FAC_Mask_R','FAC_MaskBridge','PRI_Brow_L','PRI_Brow_R'}


def validate_review_fixes(root=ROOT,proof=None,decision=None):
    from review_fixes_review import SOURCES, VIEWS, BASELINE_HASH
    root = Path(root)
    folder = root/'validation/reviews/review_fixes_v01'
    errors = []
    def need(condition,message):
        if not condition:
            errors.append(message)
    def bound(path,digest):
        need(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,'Stale/missing #37 evidence: '+str(path))
    try:
        if proof is None:
            proof = json.loads((folder/'verification.json').read_bytes())
        if decision is None:
            decision = json.loads((folder/'review.json').read_bytes())
        errors += validate_inventory(proof,{'source_sha256':SOURCES,
            'reference_sha256':DELIVERY_INVENTORIES['face_v01']['reference_sha256'],'reloaded':RELOAD_FIELDS,
            'protected_predecessor_sha256':tuple(PROTECTED_SHA256)})
        if errors:
            return errors
        need(proof['protected_predecessor_sha256']==PROTECTED_SHA256,'Untrusted predecessor inventory/digests')
        for name,digest in PROTECTED_SHA256.items():
            bound(root/name,digest)
        for name,digest in proof['source_sha256'].items():
            bound(root/name,digest)
        for name,digest in proof['reference_sha256'].items():
            bound(root/'references/approved'/name,digest)
        expected_scene = 'blender/scene/owli_review_fixes_v01.blend'
        need(proof['scene_path']==expected_scene,'Unexpected #37 scene path')
        bound(root/expected_scene,proof['scene_sha256'])
        need((root/expected_scene).stat().st_size==proof['scene_size_bytes'],'Scene size mismatch')
        need(proof['baseline_scene_sha256']==BASELINE_HASH and proof['reload_identical'] is True,'Wrong predecessor or reload assertion')
        build,reloaded = proof['build'],proof['reloaded']
        for field in RELOAD_FIELDS:
            need(isinstance(reloaded[field],dict) and bool(reloaded[field]),'Empty/malformed #37 reload field: '+field)
            need(build.get(field)==reloaded[field],'Reopened #37 state differs: '+field)
        first = json.loads((folder/'reload_a_checks.json').read_bytes())
        second = json.loads((folder/'reload_b_checks.json').read_bytes())
        saved = json.loads((folder/'saved_build_checks.json').read_bytes())
        need(saved==first==second==reloaded,'Fresh worker data differs from declared #37 reload')
        need(json.loads((folder/'build_checks.json').read_bytes())==build,'Worker build differs from declared #37 build')
        need(set(build['changed_meshes'])==CHANGED,'Missing corrected primary face meshes')
        need(build['repeated_build_identical'] is True and len(build['unchanged_part_sha256'])==45,'Repeat/preservation missing')
        baseline = json.loads((root/'validation/reviews/independent_interim_after_feet/scene-inspection.json').read_bytes())
        expected_unchanged = {name:v['digest'] for name,v in baseline['objects'].items() if v['type']=='MESH' and name not in CHANGED}
        expected_pivots = {name:v['matrix_world'] for name,v in baseline['objects'].items() if v['type']=='EMPTY'}
        need(build['unchanged_part_sha256']==expected_unchanged,'Unrelated geometry differs from independently inspected accepted #5')
        need(set(build['geometry_sha256'])==set(expected_unchanged)|CHANGED
             and all(build['geometry_sha256'][name]==digest for name,digest in expected_unchanged.items()),'Wrong mesh inventory or changed unrelated mesh')
        need(build['pivots']==expected_pivots and build['studio']==baseline['studio_before'],'Accepted pivots/fixed studio changed')
        for data in build['changed_meshes'].values():
            need(data['cage']['closed_connected'] and data['cage']['outward_consistent_normals'],'Invalid primary face surface')
            for field in ('cage_triangles','evaluated_triangles'):
                need(data[field]['interior_crossings']==0 and data[field]['adjacent_interiors_included'] is True and data[field]['minimum_polygon_triangle_normal_dot']>0,'Adjacent/coplanar face check failed')
        need(set(build['negative_surface_probes'])=={'adjacent_shared_vertex_overlap','adjacent_shared_edge_overlap','degenerate_triangle','folded_quad'}
             and all(v['rejected'] is True for v in build['negative_surface_probes'].values()),'Actual surface negatives missing')
        face = build['movement']['blink_and_gaze']
        beak = build['movement']['beak_opening']
        need(face['blink_samples']==[i/40 for i in range(41)] and face['minimum_clearance_m']>=.0003 and face['closed_coverage_rays']>=10000
             and face['full_close_front_and_back_seam_gap_m']==0,'Blink trajectory/clearance/closure failed')
        need([(v['axis'],v['degrees']) for v in face['gaze_probes']]==[('X',-12),('X',12),('Z',-12),('Z',12)]
             and all(v['no_collisions'] for v in face['gaze_probes']),'Actual gaze probes missing')
        need(beak['opening_samples']==[i/40 for i in range(41)] and beak['upper_fixed'] and beak['collision_checks']>=2300
             and beak['minimum_sampled_mask_clearance_m']>=.0003 and beak['front_lower_vertex_drop_m']>.004,'Actual beak motion/clearance failed')
        feet = build['feet']
        need(len(feet['contacts'])==8 and sum(v['rear'] for v in feet['contacts'].values())==2 and feet['independent_surface_collision_pairs']==45,'3+1 grip missing')
        corners = proof['foot_corners']
        need(corners==json.loads((folder/'foot_corners.json').read_bytes()),'Declared Foot-corner results differ from bound worker data')
        need([(v.get('bar_radius_m'),v.get('foot_half_spacing_m')) for v in corners['allowed']]
             ==[(.016,.050),(.016,.062),(.022,.050),(.022,.062),(.019,.056)],'Wrong Foot-corner sample inventory')
        need([(v.get('parameter'),v.get('value')) for v in corners['rejected']]
             ==[('bar_radius_m',.0159),('bar_radius_m',.0221),('foot_half_spacing_m',.0499),('foot_half_spacing_m',.0621)]
             and all(isinstance(v.get('reason'),str) and v['reason'].strip() for v in corners['rejected']),
             'Wrong out-of-range Foot sample inventory or rejection reason')
        need(len(corners['allowed'])==5 and all(v['actual_contact_valid'] and v['contacts']==8 and v['collision_pairs']==45 for v in corners['allowed'])
             and len(corners['rejected'])==4,'Permitted/out-of-range parameter regressions missing')
        need(set(proof['render_comparison'])==set(VIEWS),'Missing canonical view comparison')
        required = {f'evidence/{label}/{view}.png' for label in ('baseline','neutral','blink','beak_open','reload_a','reload_b') for view in VIEWS}
        required.update(('build_checks.json','saved_build_checks.json','reload_a_checks.json','reload_b_checks.json','foot_corners.json',
                         'build.log','saved_build.log','reload_a.log','reload_b.log','foot_corners.log'))
        need(required.issubset(proof['evidence_sha256']),'Incomplete #37 evidence bindings')
        for path,digest in proof['evidence_sha256'].items():
            bound(folder/path,digest)
        need(all(v['build_and_two_reloads_pixels_identical'] is True for v in proof['render_comparison'].values()),'Fresh view pixel comparison missing')
        for view in VIEWS:
            paths = [folder/'evidence'/label/(view+'.png') for label in ('neutral','reload_a','reload_b')]
            with Image.open(paths[0]) as a,Image.open(paths[1]) as b,Image.open(paths[2]) as c:
                need(a.size==b.size==c.size==(1024,1024) and a.mode==b.mode==c.mode
                     and a.tobytes()==b.tobytes()==c.tobytes(),'Actual canonical build/reload pixels differ: '+view)
                need(proof['render_comparison'][view].get('size')==list(a.size)
                     and proof['render_comparison'][view].get('mode')==a.mode,'Declared view metadata differs: '+view)
        need([v['mode'] for v in proof['commands']]==['build','saved_build','reload_a','reload_b','foot_corners'] and all(v['exit_code']==0 for v in proof['commands']),'Worker exit evidence missing')
        need(decision['status']=='review_fixes_geometry_accepted' and decision['blocking_findings']==[],'#37 visual review not accepted')
        need(decision.get('scene_sha256')==proof['scene_sha256'],'Visual decision names a different #37 scene')
        need(decision.get('reference_authority')==[{'file':'00_original_logo.png','rank':1},
             {'file':'07_turnaround_technical.png','rank':2},{'file':'08_parts_lookdev_technical.png','rank':3}],
             'Wrong #37 visual reference authority')
        need(set(decision['views'])==set(VIEWS) and all(v.get('result')=='pass' and v.get('reason','').strip() for v in decision['views'].values()),'Unproved four-view decision')
        need(set(decision['findings'])=={'IR-01','IR-02','IR-03','IR-04','IR-05'} and all(v.get('status') in ('resolved','resolved_current_deferred_rig')
             and isinstance(v.get('reason'),str) and v['reason'].strip() for v in decision['findings'].values()),'Findings matrix incomplete')
        need(bool(decision['evidence_sha256']) and 'verification.json' in decision['evidence_sha256'],'Unbound #37 review')
        for path,digest in decision['evidence_sha256'].items():
            bound(folder/path,digest)
        return errors
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        return errors+[f'Malformed/missing #37 evidence: {exc}']
