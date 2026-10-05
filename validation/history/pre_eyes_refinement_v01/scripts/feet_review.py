"""Produce saved #5 foot geometry and independently reopened four-view evidence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image
from project import find_blender
from beak_review import validate_beak_delivery
from history_bindings import validate_history
from setup_review import sha256,image_metrics,review_boards

ROOT=Path(__file__).resolve().parents[1]
VIEWS=('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')
CRITERIA=('connected_editable_3_plus_1_anatomy','opposed_contact_without_penetration_or_floating','parameterized_secondary_perch_and_four_views')


def validate_feet_delivery(root=ROOT,proof=None,decision=None):
    root=Path(root)
    folder=root/'validation/reviews/feet_v01'
    proof=proof if proof is not None else json.loads((folder/'verification.json').read_text())
    decision=decision if decision is not None else json.loads((folder/'review.json').read_text())
    errors=[]
    def need(condition,message):
        if not condition:errors.append(message)
    def bound(path,digest):need(path.is_file() and sha256(path)==digest,'Stale/missing evidence: '+str(path))
    need(decision.get('status')=='feet_geometry_accepted' and decision.get('blocking_findings')==[],'Four-view foot review not accepted')
    items=decision.get('criteria',[])
    need(tuple(item.get('id') for item in items)==CRITERIA,'Missing goal criterion')
    ranks={'00_original_logo.png':1,'07_turnaround_technical.png':2,'08_parts_lookdev_technical.png':3}
    for item in items:
        need(item.get('result')=='pass' and bool(item.get('reason','').strip()),'Unproved foot criterion')
        need(bool(item.get('references')) and all(ranks.get(ref.get('file'))==ref.get('rank') for ref in item.get('references',[])),'Invalid reference authority')
        need(bool(item.get('evidence')) and all(path in decision.get('evidence_sha256',{}) for path in item.get('evidence',[])),'Unbound visual evidence')
    for path,digest in decision.get('evidence_sha256',{}).items():bound(folder/path,digest)
    bound(root/'blender/scene/owli_feet_v01.blend',proof['scene_sha256'])
    bound(root/'blender/scene/owli_beak_v01.blend',proof['accepted_beak_scene_sha256'])
    required={'design/feet.json','design/proportions.json','scripts/feet_review.py','scripts/blender/40_feet_perch.py','scripts/blender/feet_geometry.py','scripts/blender/verify_feet.py','scripts/blender/feet_probe.py','scripts/blender/feet_evidence.py','validation/reference_views.json'}
    need(required.issubset(proof['source_sha256']),'Incomplete source bindings')
    for path,digest in proof['source_sha256'].items():bound(root/path,digest)
    for path,digest in proof['evidence_sha256'].items():bound(folder/path,digest)
    for path,digest in proof['reference_sha256'].items():bound(root/'references/approved'/path,digest)
    build=proof['build']
    expected={f'GRP_Claw_{side}_{label}' for side in ('L','R') for label in ('Front_1','Front_2','Front_3','Rear_1')}|{'GRP_Foot_L','GRP_Foot_R','GRP_PerchBar','GRP_PerchStem','GRP_PerchBase'}
    need(set(build['surfaces'])==expected,'Wrong foot/perch assembly')
    for mesh in build['surfaces'].values():
        need(mesh['closed_connected'] and mesh['outward_consistent_normals'] and mesh['self_intersections']==0 and mesh['duplicate_vertices']==0 and mesh['euler_characteristic']==2,'Invalid foot surface')
    need(len(build['contacts'])==8 and sum(item['rear'] for item in build['contacts'].values())==2,'Wrong claw anatomy')
    need(set(build.get('pad_support_contact_m',{}))=={'GRP_Foot_L','GRP_Foot_R'} and all(build.get('pad_support_contact_m',{}).values()),'Weight-bearing pad support missing')
    need(len(build['toe_branches'])==2 and all(set(branches)=={'toe_Front_1','toe_Front_2','toe_Front_3','toe_Rear_1'} for branches in build['toe_branches'].values()),'Missing actual anatomical branches')
    tolerance=build['penetration_tolerance_m']
    for contact in build['contacts'].values():
        need(contact['nearest_surface_distance_m']<tolerance and contact['minimum_polygon_halfspace_distance_m']>=-tolerance,'Claw floats or penetrates perch')
    for branches in build['toe_branches'].values():
        for branch in branches.values():need(branch['connected'] and branch['vertices']>100 and branch['nearest_surface_distance_m']<tolerance,'Unproved connected toe contact')
    need(build['independent_surface_collision_pairs']==45,'Missing independent surface collision checks')
    need(len(build['unchanged_part_sha256'])==37 and len(build['empty_transforms'])==3,'Unrelated predecessor preservation missing')
    need(build['repeated_build_identical'] and build['global_scale_factors']==[.5,2],'Missing repeat/scale proof')
    need(len(build['parameter_probes'])==2 and all(p['actual_contact_valid'] for p in build['parameter_probes']),'Permitted parameter limits untested')
    need(set(build['negative_probes'])=={'floating_claw','penetrating_claw','rear_on_front'} and all(build['negative_probes'].values()),'Actual negative grip probes missing')
    need(proof['reload_identical'],'Independent reloads differ')
    for key,value in proof['reloaded'].items():need(build.get(key)==value,'Reopened scene differs: '+key)
    for view in VIEWS:
        need(proof['render_metrics'][view]['reload_pixels_identical'],'Saved-scene pixels differ: '+view)
        for state,scopes in [('baseline',('full','feet')),('candidate',('full','feet','toes'))]:
            for scope in scopes:need(f'evidence/{state}/{scope}/{view}.png' in proof['evidence_sha256'],'Missing fixed-view comparison')
        crop=proof['detail_crops'][view]
        with Image.open(folder/crop['source']) as full,Image.open(folder/(view+'_grip_detail.png')) as detail:
            box=crop['rectangle_px']
            expected_image=full.crop(box).resize(((box[2]-box[0])*crop['display_scale'],(box[3]-box[1])*crop['display_scale']),Image.Resampling.LANCZOS)
            need(expected_image.tobytes()==detail.tobytes(),'Detail view is not the documented unchanged-camera crop')
    return errors


def build_review(blender):
    errors=validate_beak_delivery(ROOT)+validate_history(ROOT)
    if errors:raise RuntimeError('\n'.join(errors))
    scripts=ROOT/'scripts/blender'
    accepted=ROOT/'blender/scene/owli_beak_v01.blend'
    output=ROOT/'validation/reviews/feet_v01'
    target=ROOT/'blender/scene/owli_feet_v01.blend'
    cfg=json.loads((ROOT/'validation/reference_views.json').read_text())
    with tempfile.TemporaryDirectory(prefix='owli-feet-',dir=ROOT/'tmp') as folder:
        scratch=Path(folder)
        shutil.copytree(ROOT/'design',scratch/'design')
        (scratch/'validation').mkdir()
        shutil.copy2(ROOT/'validation/reference_views.json',scratch/'validation/reference_views.json')
        scene=scratch/'tmp/feet/prototype.blend'
        scene.parent.mkdir(parents=True)
        shutil.copy2(accepted,scene)
        env=dict(os.environ)
        env.pop('OWLI_RENDER_SIZE',None)
        env.pop('OWLI_VALIDATION_OUTPUT',None)
        for mode in ('build','reload_a','reload_b'):
            env['OWLI_FEET_MODE']=mode
            subprocess.run([blender,'--background',str(scene),'--python-exit-code','1','--python',str(scripts/'feet_evidence.py')],cwd=scratch,env=env,check=True)
        built=json.loads((scratch/'build_checks.json').read_text())
        a=json.loads((scratch/'reload_a_checks.json').read_text())
        b=json.loads((scratch/'reload_b_checks.json').read_text())
        assert a==b,'Independent reload checks differ'
        assert all(built[key]==value for key,value in a.items()),'Saved geometry differs from build'
        proof={'build':built,'reloaded':a,'reload_identical':True,'design_approval':False,'render_metrics':{},'detail_crops':{}}
        output.mkdir(parents=True,exist_ok=True)
        for view in VIEWS:
            first,second=scratch/'validation/reload_a'/f'{view}.png',scratch/'validation/reload_b'/f'{view}.png'
            with Image.open(first) as im_a,Image.open(second) as im_b:
                assert im_a.tobytes()==im_b.tobytes(),'Fresh reload pixels differ: '+view
            proof['render_metrics'][view]=dict(image_metrics(second),reload_pixels_identical=True)
            shutil.copy2(second,output/second.name)
            with Image.open(scratch/'validation/evidence/candidate/toes'/f'{view}.png') as isolated,Image.open(second) as full:
                box=isolated.getchannel('A').getbbox()
                assert box,'No foot geometry visible: '+view
                box=(max(0,box[0]-16),max(0,box[1]-16),min(1024,box[2]+16),min(1024,box[3]+16))
                # Pixel crop only: production camera and visibility remain unchanged.
                full.crop(box).resize((round((box[2]-box[0])*3),round((box[3]-box[1])*3)),Image.Resampling.LANCZOS).save(output/(view+'_grip_detail.png'))
                proof['detail_crops'][view]={'source':view+'.png','rectangle_px':box,'display_scale':3}
        (output/'render_manifest.json').write_text((scratch/'validation/reload_b/render_manifest.json').read_text(),newline='\n')
        shutil.copytree(scratch/'validation/evidence',output/'evidence',dirs_exist_ok=True)
        shutil.copy2(scene,target)
        proof['scene_sha256']=sha256(target)
        proof['accepted_beak_scene_sha256']=sha256(accepted)
        source_names=['design/feet.json','design/proportions.json','design/character_spec.json','design/materials.json','design/reference_hierarchy.json','design/silhouette_freeze.json','validation/reference_views.json','scripts/feet_review.py','scripts/project.py','scripts/history_bindings.py','scripts/setup_review.py','validation/history/pre_feet_v01/manifest.json']
        source_names+=['scripts/blender/'+name for name in ('40_feet_perch.py','legacy/40_feet_perch.py','feet_geometry.py','verify_feet.py','feet_probe.py','feet_evidence.py','verify_face.py','primary_geometry.py','primary_evidence.py','blockout_geometry.py','validation_setup.py','90_validation.py')]
        proof['source_sha256']={name:sha256(ROOT/name) for name in source_names}
        proof['reference_sha256']={r['file']:sha256(ROOT/'references/approved'/r['file']) for r in json.loads((ROOT/'references/manifest.json').read_text())['references']}
        review_boards(ROOT,output,cfg,'feet_v01 (#5 connected 3+1 grip)')
        proof['evidence_sha256']={p.relative_to(output).as_posix():sha256(p) for p in output.rglob('*.png')}
        (output/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',newline='\n')
    print('FEET REVIEW EVIDENCE BUILT: manual reference decision still required.',output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender')
    args=parser.parse_args()
    build_review(find_blender(args.blender))
