"""Build/reopen #16 from accepted #15, verify live geometry and publish fixed-view proof."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image
from project import find_blender
from setup_review import sha256, image_metrics, review_boards
from silhouette_review import validate_review

ROOT=Path(__file__).resolve().parents[1]
VIEWS=('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')
CRITERIA=('layered_eyes_and_aim_pivots','readable_collision_free_mask','full_blink_without_penetration_or_gaps','four_view_friendly_face')


def validate_delivery(root=ROOT,decision=None,proof=None):
    """CI checks freshness and completeness; visual acceptance remains manually authored."""
    root=Path(root)
    folder=root/'validation/reviews/face_v01'
    proof=proof if proof is not None else json.loads((folder/'verification.json').read_text())
    decision=decision if decision is not None else json.loads((folder/'review.json').read_text())
    errors=[]
    def need(condition,message):
        if not condition: errors.append(message)
    def bound(path,digest):
        need(path.is_file() and sha256(path)==digest,'Stale/missing evidence: '+str(path))
    need(decision.get('status')=='face_geometry_accepted','Manual face review is not accepted')
    need(decision.get('blocking_findings')==[],'Blocking face findings remain')
    items=decision.get('criteria',[])
    need(tuple(item.get('id') for item in items)==CRITERIA,'Missing/reordered goal criterion')
    for item in items:
        need(item.get('result')=='pass' and bool(item.get('reason','').strip()),'Unproved criterion: '+str(item.get('id')))
        need(bool(item.get('evidence')) and all(p in decision.get('evidence_sha256',{}) for p in item.get('evidence',[])),'Unbound criterion evidence')
    for path,digest in decision.get('evidence_sha256',{}).items(): bound(folder/path,digest)
    bound(root/'blender/scene/owli_face_v01.blend',proof['scene_sha256'])
    bound(root/'blender/scene/owli_head_body_v01.blend',proof['accepted_primary_scene_sha256'])
    for path,digest in proof['source_sha256'].items(): bound(root/path,digest)
    for path,digest in proof['evidence_sha256'].items(): bound(folder/path,digest)
    for path,digest in proof['reference_sha256'].items(): bound(root/'references/approved'/path,digest)
    need(proof.get('reload_identical') is True,'Fresh saved-scene reload not proved')
    build=proof['build']
    need(len(build.get('unchanged_part_sha256',{}))==36,'Unrelated primary/body/anatomy preservation not proved')
    need(build.get('repeated_build_identical') and build.get('face_global_scale_probe'),'Rebuild/scale not proved')
    need(all(build.get('rejection_probes',{}).values()) and len(build.get('rejection_probes',{}))==4,'Negative geometry gates not proved')
    need(len(build.get('meshes',{}))==15,'Missing layered facial meshes')
    for mesh in build.get('meshes',{}).values():
        need(mesh.get('closed_connected') and mesh.get('outward_consistent_normals') and mesh.get('self_intersections')==0,'Invalid delivered surface')
    probes=build['probes']
    need(probes['blink_samples']==[i/40 for i in range(41)],'Incomplete blink trajectory')
    policy=json.loads((root/'design/face.json').read_text())
    need(probes['minimum_clearance_m']>=policy['minimum_surface_clearance_m'],'Lid clearance failed')
    need(probes['closed_coverage_rays']>=10000 and probes['full_close_front_and_back_seam_gap_m']==0,'Full closed-eye coverage not proved')
    need(len(probes['gaze_probes'])==4 and all(p['no_collisions'] for p in probes['gaze_probes']),'Gaze pivot exercise missing')
    for key,value in proof['reloaded'].items(): need(build.get(key)==value,'Reopened scene changed: '+key)
    for view in VIEWS:
        need(proof['render_metrics'][view]['reload_pixels_identical'],'Canonical view changed: '+view)
        for label in ('baseline','neutral','layers','half','closed','wink_L','look_up','look_down','look_left','look_right','cornea_geometry'):
            need(f'evidence/{label}/{view}.png' in proof['evidence_sha256'],'Missing four-view probe: '+label+'/'+view)
    return errors


def build_review(blender):
    freeze=json.loads((ROOT/'design/silhouette_freeze.json').read_text())
    errors=validate_review(ROOT,freeze)
    if errors: raise RuntimeError('\n'.join(errors))
    baseline_folder=ROOT/'validation/reviews/head_body_v01'
    primary=json.loads((baseline_folder/'verification.json').read_text())
    scene=ROOT/'blender/scene/owli_head_body_v01.blend'
    assert sha256(scene)==primary['scene_sha256'],'Accepted #15 scene is stale'
    for name,digest in primary['source_sha256'].items():
        assert sha256(ROOT/name)==digest,'Accepted #15 source is stale: '+name
    for name,digest in primary['evidence_sha256'].items():
        assert sha256(baseline_folder/name)==digest,'Accepted #15 evidence is stale: '+name
    cfg=json.loads((ROOT/'validation/reference_views.json').read_text())
    scripts=ROOT/'scripts/blender'
    output=ROOT/'validation/reviews/face_v01'
    scene_output=ROOT/'blender/scene/owli_face_v01.blend'
    with tempfile.TemporaryDirectory(prefix='owli-face-',dir=ROOT/'tmp') as folder:
        scratch=Path(folder)
        shutil.copytree(ROOT/'design',scratch/'design')
        (scratch/'validation').mkdir()
        shutil.copy2(ROOT/'validation/reference_views.json',scratch/'validation/reference_views.json')
        target=scratch/'blender/scene/owli.blend'
        target.parent.mkdir(parents=True)
        shutil.copy2(scene,target)
        env=dict(os.environ)
        env.pop('OWLI_RENDER_SIZE',None)
        env.pop('OWLI_VALIDATION_OUTPUT',None)
        command=[blender,'--background',str(target),'--python-exit-code','1','--python',str(scripts/'face_evidence.py')]
        for mode in ('build','reload_a','reload_b'):
            env['OWLI_FACE_MODE']=mode
            subprocess.run(command,cwd=scratch,env=env,check=True)
        built=json.loads((scratch/'build_checks.json').read_text())
        first=json.loads((scratch/'reload_a_checks.json').read_text())
        second=json.loads((scratch/'reload_b_checks.json').read_text())
        assert first==second,'Fresh reloads disagree'
        assert all(built[key]==value for key,value in first.items()),'Saved scene differs from build'
        checks={'build':built,'reloaded':first,'reload_identical':True,'render_metrics':{},'design_approval':False}
        for view in VIEWS:
            a=scratch/'validation/reload_a'/f'{view}.png'
            b=scratch/'validation/reload_b'/f'{view}.png'
            with Image.open(a) as im_a,Image.open(b) as im_b:
                assert im_a.tobytes()==im_b.tobytes(),'Saved-scene pixels differ: '+view
            checks['render_metrics'][view]=dict(image_metrics(a),reload_pixels_identical=True)
        output.mkdir(parents=True,exist_ok=True)
        for p in (scratch/'validation/reload_b').iterdir():
            if p.suffix=='.json':
                (output/p.name).write_text(p.read_text(),encoding='utf-8',newline='\n')
            else: shutil.copy2(p,output/p.name)
        shutil.copytree(scratch/'validation/evidence',output/'evidence',dirs_exist_ok=True)
        shutil.copy2(target,scene_output)
        checks['scene_sha256']=sha256(scene_output)
        checks['accepted_primary_scene_sha256']=sha256(scene)
        sources=[ROOT/name for name in ('design/face.json','design/proportions.json','design/character_spec.json','design/materials.json','design/silhouette_freeze.json','validation/reference_views.json','scripts/face_review.py','scripts/setup_review.py')]
        sources+=[scripts/name for name in ('21_eyes_mask.py','face_geometry.py','verify_face.py','face_evidence.py','90_validation.py','blockout_geometry.py','primary_geometry.py','primary_evidence.py','validation_setup.py','verify_validation_setup.py')]
        checks['source_sha256']={p.relative_to(ROOT).as_posix():sha256(p) for p in sources}
        checks['reference_sha256']={r['file']:sha256(ROOT/'references/approved'/r['file']) for r in json.loads((ROOT/'references/manifest.json').read_text())['references']}
        review_boards(ROOT,output,cfg,'face_v01 (#16 eyes / mask / blink)')
        checks['evidence_sha256']={p.relative_to(output).as_posix():sha256(p) for p in output.rglob('*.png')}
        (output/'verification.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'FACE REVIEW OK: closed meshes, layer/mask collisions, 41 blink samples, full-close coverage, gaze, fresh reload pixels. {output}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender')
    args=parser.parse_args()
    build_review(find_blender(args.blender))
