"""Produce #17 saved jaw geometry and independently reopened four-view evidence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image
from project import find_blender
from face_review import validate_delivery
from head_body_review import silhouette_metrics
from setup_review import sha256,image_metrics,review_boards

ROOT=Path(__file__).resolve().parents[1]
VIEWS=('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')
CRITERIA=('separate_reference_consistent_jaws','plausible_collision_free_opening','documented_pivot_and_four_views')


def validate_beak_delivery(root=ROOT,proof=None,decision=None):
    root=Path(root)
    folder=root/'validation/reviews/beak_v01'
    proof=proof if proof is not None else json.loads((folder/'verification.json').read_text())
    decision=decision if decision is not None else json.loads((folder/'review.json').read_text())
    errors=[]
    def need(condition,message):
        if not condition: errors.append(message)
    def bound(path,digest): need(path.is_file() and sha256(path)==digest,'Stale/missing evidence: '+str(path))
    need(decision.get('status')=='beak_geometry_accepted' and decision.get('blocking_findings')==[],'Visual jaw review is not accepted')
    items=decision.get('criteria',[])
    need(tuple(i.get('id') for i in items)==CRITERIA,'Missing goal criterion')
    for item in items:
        need(item.get('result')=='pass' and bool(item.get('reason','').strip()),'Unproved criterion')
        need(bool(item.get('evidence')) and all(p in decision.get('evidence_sha256',{}) for p in item.get('evidence',[])),'Unbound visual evidence')
    for path,digest in decision.get('evidence_sha256',{}).items(): bound(folder/path,digest)
    bound(root/'blender/scene/owli_beak_v01.blend',proof['scene_sha256'])
    bound(root/'blender/scene/owli_face_v01.blend',proof['accepted_face_scene_sha256'])
    for path,digest in proof['source_sha256'].items(): bound(root/path,digest)
    for path,digest in proof['evidence_sha256'].items(): bound(folder/path,digest)
    for path,digest in proof['reference_sha256'].items(): bound(root/'references/approved'/path,digest)
    build=proof['build']
    need(proof['reload_identical'] and build['repeated_build_identical'] and build['beak_global_scale_probe'],'Build/scale/reload proof missing')
    need(len(build['unchanged_part_sha256'])==50,'Unrelated face/anatomy preservation missing')
    need(len(build['rejection_probes'])==4 and all(build['rejection_probes'].values()),'Negative gates missing')
    need(set(build['meshes'])=={'BAK_Upper','BAK_Lower'},'Separate jaw meshes missing')
    need(build['hooked_tip_stays_upper'] and build['toe_rule_3_plus_1'],'Hook/anatomy invariant failed')
    for mesh in build['meshes'].values(): need(mesh['closed_connected'] and mesh['outward_consistent_normals'] and mesh['self_intersections']==0,'Invalid jaw topology')
    probes=build['opening_probes']
    need(probes['opening_samples']==[i/40 for i in range(41)],'Incomplete opening trajectory')
    need(probes['collision_checks']>=2300 and probes['upper_fixed'],'Actual jaw collision/movement proof missing')
    need(probes['front_lower_vertex_drop_m']>.004 and probes['minimum_sampled_mask_clearance_m']>=.0003,'Invalid visible opening or mask clearance')
    need(build['maximum_exterior_vertex_deviation_m']<5e-7,'Frozen closed envelope changed')
    for key,value in proof['reloaded'].items(): need(build[key]==value,'Reopened scene changed: '+key)
    for view in VIEWS:
        need(proof['render_metrics'][view]['reload_pixels_identical'],'Saved-scene pixels changed: '+view)
        for label in ('baseline','closed','half','open'):
            for scope in ('full','beak'): need(f'evidence/{label}/{scope}/{view}.png' in proof['evidence_sha256'],'Missing four-view probe')
        for scope in ('full','beak'):
            actual=silhouette_metrics(folder/'evidence/baseline'/scope/f'{view}.png',folder/'evidence/closed'/scope/f'{view}.png',3,.98)
            need(actual==proof['silhouette_comparison'][scope+'/'+view],'Silhouette proof changed')
    return errors


def build_review(blender):
    errors=validate_delivery(ROOT)
    if errors: raise RuntimeError('\n'.join(errors))
    scripts=ROOT/'scripts/blender'
    output=ROOT/'validation/reviews/beak_v01'
    scene_output=ROOT/'blender/scene/owli_beak_v01.blend'
    accepted=ROOT/'blender/scene/owli_face_v01.blend'
    cfg=json.loads((ROOT/'validation/reference_views.json').read_text())
    with tempfile.TemporaryDirectory(prefix='owli-beak-',dir=ROOT/'tmp') as folder:
        scratch=Path(folder)
        shutil.copytree(ROOT/'design',scratch/'design')
        (scratch/'validation').mkdir()
        shutil.copy2(ROOT/'validation/reference_views.json',scratch/'validation/reference_views.json')
        target=scratch/'blender/scene/owli.blend'
        target.parent.mkdir(parents=True)
        shutil.copy2(accepted,target)
        env=dict(os.environ)
        env.pop('OWLI_RENDER_SIZE',None)
        env.pop('OWLI_VALIDATION_OUTPUT',None)
        command=[blender,'--background',str(target),'--python-exit-code','1','--python',str(scripts/'beak_evidence.py')]
        for mode in ('build','reload_a','reload_b'):
            env['OWLI_BEAK_MODE']=mode
            subprocess.run(command,cwd=scratch,env=env,check=True)
        built=json.loads((scratch/'build_checks.json').read_text())
        first=json.loads((scratch/'reload_a_checks.json').read_text())
        second=json.loads((scratch/'reload_b_checks.json').read_text())
        assert first==second,'Fresh reloads differ'
        assert all(built[key]==value for key,value in first.items()),'Saved beak differs from build'
        checks={'build':built,'reloaded':first,'reload_identical':True,'render_metrics':{},'silhouette_comparison':{},'design_approval':False}
        for view in VIEWS:
            a=scratch/'validation/reload_a'/f'{view}.png'
            b=scratch/'validation/reload_b'/f'{view}.png'
            with Image.open(a) as im_a,Image.open(b) as im_b:
                assert im_a.tobytes()==im_b.tobytes(),'Saved-scene pixels differ: '+view
            checks['render_metrics'][view]=dict(image_metrics(a),reload_pixels_identical=True)
            for scope in ('full','beak'):
                evidence=scratch/'validation/evidence'
                # One pixel slit is a real separation, not an outer silhouette redesign.
                checks['silhouette_comparison'][scope+'/'+view]=silhouette_metrics(evidence/'baseline'/scope/f'{view}.png',evidence/'closed'/scope/f'{view}.png',3,.98)
        output.mkdir(parents=True,exist_ok=True)
        for path in (scratch/'validation/reload_b').iterdir():
            if path.suffix=='.json': (output/path.name).write_text(path.read_text(),encoding='utf-8',newline='\n')
            else: shutil.copy2(path,output/path.name)
        shutil.copytree(scratch/'validation/evidence',output/'evidence',dirs_exist_ok=True)
        shutil.copy2(target,scene_output)
        checks['scene_sha256']=sha256(scene_output)
        checks['accepted_face_scene_sha256']=sha256(accepted)
        sources=[ROOT/path for path in ('design/beak.json','design/proportions.json','design/character_spec.json','design/materials.json','design/silhouette_freeze.json','validation/reference_views.json','scripts/beak_review.py','scripts/head_body_review.py','scripts/setup_review.py')]
        sources+=[scripts/name for name in ('22_beak.py','beak_geometry.py','verify_beak.py','beak_evidence.py','90_validation.py','blockout_geometry.py','primary_geometry.py','primary_evidence.py','verify_face.py','validation_setup.py','verify_validation_setup.py')]
        checks['source_sha256']={p.relative_to(ROOT).as_posix():sha256(p) for p in sources}
        checks['reference_sha256']={r['file']:sha256(ROOT/'references/approved'/r['file']) for r in json.loads((ROOT/'references/manifest.json').read_text())['references']}
        review_boards(ROOT,output,cfg,'beak_v01 (#17 upper / lower jaw)')
        checks['evidence_sha256']={p.relative_to(output).as_posix():sha256(p) for p in output.rglob('*.png')}
        (output/'verification.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'BEAK REVIEW OK: topology, opening/mask collision probes, fixed silhouette, scale, fresh reload. {output}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender')
    args=parser.parse_args()
    build_review(find_blender(args.blender))
