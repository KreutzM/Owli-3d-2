"""Isolated #6 production runner: accepted #37 in, new own milestone out."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from PIL import Image
from delivery_gates import validate_all
from review_fixes_gate import validate_review_fixes
from project import find_blender
from setup_review import review_boards
from feathers_contracts import (BASELINE_COMMIT,BASELINE_SCENE,BASELINE_SHA256,BASELINE_SIZE_BYTES,
    SCENE_PATH,REVIEW_PATH,SOURCES,PROTECTED_SHA256,VIEWS)

ROOT = Path(__file__).resolve().parents[1]
MODES = ('build','saved_build','reload_a','reload_b')
LABELS = ('baseline','live_neutral','blink','beak_open','gesture_left','gesture_right','gesture_both',
          'neutral','reload_a','reload_b')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scene-output',type=Path,required=True)
    p.add_argument('--blender')
    args = p.parse_args()
    work,output,target = (v.resolve() for v in (args.work,args.output,args.scene_output))
    if output!=ROOT/REVIEW_PATH or target!=ROOT/SCENE_PATH:
        raise ValueError('Only the named new #6 milestone may be published')
    if not work.is_relative_to(ROOT/'tmp') or work==ROOT/'tmp' or work.exists():
        raise ValueError('Choose a fresh explicit work directory below repository tmp/')
    errors = validate_all(ROOT)+validate_review_fixes(ROOT)
    if errors:
        raise RuntimeError('\n'.join(errors))
    protected = {name:sha(ROOT/name) for name in PROTECTED_SHA256}
    if protected!=PROTECTED_SHA256:
        raise ValueError('Accepted historical evidence differs from Git/LFS predecessor')
    accepted = ROOT/BASELINE_SCENE
    assert sha(accepted)==BASELINE_SHA256 and accepted.stat().st_size==BASELINE_SIZE_BYTES
    work.mkdir(parents=True)
    shutil.copytree(ROOT/'design',work/'design')
    (work/'validation').mkdir()
    shutil.copy2(ROOT/'validation/reference_views.json',work/'validation/reference_views.json')
    scene = work/'candidate.blend'
    shutil.copy2(accepted,scene)
    env = dict(os.environ)
    for key in ('OWLI_RENDER_SIZE','OWLI_VALIDATION_OUTPUT'):
        env.pop(key,None)
    blender = find_blender(args.blender)
    commands = []
    for mode in MODES:
        argv = [blender,'--background',str(scene),'--python-exit-code','1','--python',
                str(ROOT/'scripts/blender/feathers_evidence.py'),'--','--work',str(work),'--mode',mode]
        with (work/(mode+'.log')).open('w',encoding='utf-8',newline='\n') as log:
            result = subprocess.run(argv,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
        commands.append({'mode':mode,'argv':argv,'exit_code':result.returncode})
        if result.returncode:
            raise RuntimeError(f'Blender {mode} failed; inspect {work/(mode+".log")}')
        print('Blender worker passed:',mode,flush=True)
    checks = {m:json.loads((work/(m+'_checks.json')).read_bytes()) for m in MODES}
    assert checks['saved_build']==checks['reload_a']==checks['reload_b'],'Fresh reload data differs'
    assert all(checks['build'][k]==v for k,v in checks['saved_build'].items()),'Build/reload geometry or probes differ'
    pixels = {}
    for view in VIEWS:
        paths = [work/'renders'/label/(view+'.png') for label in ('neutral','reload_a','reload_b')]
        with Image.open(paths[0]) as a,Image.open(paths[1]) as b,Image.open(paths[2]) as c:
            assert a.size==b.size==c.size==(1024,1024) and a.mode==b.mode==c.mode=='RGBA'
            assert a.tobytes()==b.tobytes()==c.tobytes(),'Canonical rendered pixels differ: '+view
            pixels[view] = {'size':list(a.size),'mode':a.mode,'build_and_two_reloads_pixels_identical':True}
    assert protected=={n:sha(ROOT/n) for n in protected},'Historical input mutated'
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(work/'renders',output/'evidence',dirs_exist_ok=True)
    for mode in MODES:
        shutil.copy2(work/(mode+'_checks.json'),output/(mode+'_checks.json'))
        lines = (work/(mode+'.log')).read_text(encoding='utf-8').splitlines()
        (output/(mode+'.log')).write_text('\n'.join(line.rstrip() for line in lines)+'\n',encoding='utf-8',newline='\n')
    for view in VIEWS:
        shutil.copy2(work/'renders/reload_b'/(view+'.png'),output/(view+'.png'))
    shutil.copy2(scene,target)
    cfg = json.loads((ROOT/'validation/reference_views.json').read_bytes())
    review_boards(ROOT,output,cfg,'feathers_v01 (#6 broad wing/body/tail/cream groups)')
    (output/'.gitattributes').write_text('*.log text eol=lf\n',encoding='utf-8',newline='\n')
    proof = {'gate_version':2,'milestone':'feathers_v01','design_approval':False,
        'baseline_commit':BASELINE_COMMIT,'baseline_scene_sha256':BASELINE_SHA256,
        'scene_path':SCENE_PATH,'scene_sha256':sha(target),'scene_size_bytes':target.stat().st_size,
        'build':checks['build'],'reloaded':checks['reload_a'],'reload_identical':True,
        'render_comparison':pixels,'commands':commands,
        'protected_predecessor_sha256':protected,'source_sha256':{n:sha(ROOT/n) for n in SOURCES},
        'reference_sha256':{p.name:sha(p) for p in sorted((ROOT/'references/approved').glob('*.png'))}}
    proof['evidence_sha256'] = {p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*'))
        if p.is_file() and (p.suffix in ('.png','.log') or p.name in {m+'_checks.json' for m in MODES})}
    write(output/'verification.json',proof)
    print('NEW #6 EVIDENCE DELIVERED:',output,'exact-scene visual decision still required',flush=True)


if __name__=='__main__':
    main()
