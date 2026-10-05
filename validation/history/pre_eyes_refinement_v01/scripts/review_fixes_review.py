"""Produce #37 in an explicit isolated work directory; publish only new own artifacts.

Example: python scripts/review_fixes_review.py --work tmp/review-fixes-37/run01
 --output validation/reviews/review_fixes_v01
 --scene-output blender/scene/owli_review_fixes_v01.blend
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image
from delivery_gates import validate_all
from evidence_contracts import DELIVERY_INVENTORIES
from review_fixes_contracts import PROTECTED_SHA256
from project import find_blender
from setup_review import review_boards

ROOT = Path(__file__).resolve().parents[1]
BASELINE_HASH = '0fb1512b3a27c4ebe5b7cbdebf520643b7208f2c74f8a847545ffc51dda66797'
VIEWS = ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')
NEW_SOURCES = ('design/review_fixes.json','scripts/review_fixes_review.py','scripts/delivery_gates.py',
    'scripts/delivery_shapes.py','scripts/evidence_contracts.py','scripts/history_gate.py',
    'scripts/blender/review_fixes_geometry.py','scripts/blender/review_fixes_checks.py',
    'scripts/blender/review_fixes_evidence.py','scripts/blender/face_geometry.py',
    'scripts/blender/beak_geometry.py','scripts/blender/verify_beak.py','scripts/blender/verify_validation_setup.py',
    'scripts/review_fixes_contracts.py','scripts/review_fixes_gate.py','scripts/validate_project.py',
    'scripts/audit_review_fixes_history.py')
SOURCES = tuple(sorted(set(NEW_SOURCES).union(*(set(v['source_sha256']) for v in DELIVERY_INVENTORIES.values()))))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_inventory():
    actual = {name:sha(ROOT/name) for name in PROTECTED_SHA256}
    if actual != PROTECTED_SHA256:
        raise ValueError('Historical evidence differs from real predecessor Git/LFS bytes')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender')
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scene-output',type=Path,required=True)
    args = parser.parse_args()
    work,output,target = (p.resolve() for p in (args.work,args.output,args.scene_output))
    # Deliberately restrictive: this producer cannot publish into another milestone.
    if output != ROOT/'validation/reviews/review_fixes_v01' or target != ROOT/'blender/scene/owli_review_fixes_v01.blend':
        raise ValueError('Publish paths must name the new #37 milestone, never accepted predecessors')
    if not work.is_relative_to(ROOT/'tmp') or work == ROOT/'tmp' or work.exists():
        raise ValueError('Choose a fresh explicit work directory below repository tmp/')
    errors = validate_all(ROOT)
    if errors:
        raise RuntimeError('\n'.join(errors))
    accepted = ROOT/'blender/scene/owli_feet_v01.blend'
    assert sha(accepted)==BASELINE_HASH and accepted.stat().st_size==1020254
    protected = protected_inventory()
    # The producer may replace its own prior candidate, never any protected file.
    protected.pop('blender/scene/owli_review_fixes_v01.blend',None)
    work.mkdir(parents=True)
    shutil.copytree(ROOT/'design',work/'design')
    (work/'validation').mkdir()
    shutil.copy2(ROOT/'validation/reference_views.json',work/'validation/reference_views.json')
    scene = work/'candidate.blend'
    shutil.copy2(accepted,scene)
    blender = find_blender(args.blender)
    worker = ROOT/'scripts/blender/review_fixes_evidence.py'
    env = dict(os.environ)
    for key in ('OWLI_RENDER_SIZE','OWLI_VALIDATION_OUTPUT'):
        env.pop(key,None)
    commands = []
    for mode in ('build','saved_build','reload_a','reload_b','foot_corners'):
        argv = [blender,'--background',str(scene),'--python-exit-code','1','--python',str(worker),
                '--','--mode',mode,'--work',str(work)]
        with (work/(mode+'.log')).open('w',encoding='utf-8',newline='\n') as log:
            result = subprocess.run(argv,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
        commands.append(dict(mode=mode,argv=argv,exit_code=result.returncode))
        if result.returncode:
            raise RuntimeError(f'Blender {mode} failed; inspect {work/(mode+".log")}')
        print('Blender worker passed:',mode,flush=True)
    build = json.loads((work/'build_checks.json').read_bytes())
    saved = json.loads((work/'saved_build_checks.json').read_bytes())
    first = json.loads((work/'reload_a_checks.json').read_bytes())
    second = json.loads((work/'reload_b_checks.json').read_bytes())
    assert saved==first==second and all(build[k]==v for k,v in first.items()),'Fresh reopened checks differ'
    render_comparison = {}
    for view in VIEWS:
        images = [work/'renders'/label/(view+'.png') for label in ('neutral','reload_a','reload_b')]
        with Image.open(images[0]) as a,Image.open(images[1]) as b,Image.open(images[2]) as c:
            assert a.tobytes()==b.tobytes()==c.tobytes(),'Build/reload pixels differ: '+view
            render_comparison[view] = dict(size=list(a.size),mode=a.mode,build_and_two_reloads_pixels_identical=True)
    assert all(sha(ROOT/name)==digest for name,digest in protected.items()),'Accepted artifacts changed during isolated run'
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(work/'renders',output/'evidence',dirs_exist_ok=True)
    for name in ('build_checks.json','saved_build_checks.json','reload_a_checks.json','reload_b_checks.json','foot_corners.json',
                 'build.log','saved_build.log','reload_a.log','reload_b.log','foot_corners.log'):
        if name.endswith('.log'):
            # Canonical text bytes survive Git checkout on Windows and Linux.
            lines = (work/name).read_text(encoding='utf-8').splitlines()
            (output/name).write_text('\n'.join(line.rstrip() for line in lines)+'\n',encoding='utf-8',newline='\n')
        else:
            shutil.copy2(work/name,output/name)
    for view in VIEWS:
        shutil.copy2(work/'renders/reload_b'/(view+'.png'),output/(view+'.png'))
    shutil.copy2(scene,target)
    cfg = json.loads((ROOT/'validation/reference_views.json').read_bytes())
    review_boards(ROOT,output,cfg,'review_fixes_v01 (#37 organic face / strict gates)')
    proof = dict(gate_version=2,design_approval=False,baseline_scene_sha256=BASELINE_HASH,
        scene_sha256=sha(target),scene_size_bytes=target.stat().st_size,scene_path=target.relative_to(ROOT).as_posix(),
        build=build,reloaded=first,reload_identical=True,render_comparison=render_comparison,
        foot_corners=json.loads((work/'foot_corners.json').read_bytes()),commands=commands,
        protected_predecessor_sha256=protected,source_sha256={name:sha(ROOT/name) for name in SOURCES},
        reference_sha256={p.name:sha(p) for p in sorted((ROOT/'references/approved').glob('*.png'))})
    checks_files = ('build_checks.json','saved_build_checks.json','reload_a_checks.json','reload_b_checks.json','foot_corners.json')
    proof['evidence_sha256'] = {p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*'))
                               if p.is_file() and (p.suffix in ('.png','.log') or p.name in checks_files)}
    (output/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('NEW #37 EVIDENCE DELIVERED:',output,'manual exact-scene visual review still required',flush=True)


if __name__ == '__main__':
    main()
