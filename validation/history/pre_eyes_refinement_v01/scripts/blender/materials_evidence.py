"""Isolated #18 worker: accepted #6 input, actual fresh material/geometry checks."""
import argparse
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from materials_geometry import build,CHANGED,REMOVED
from materials_checks import shape_hashes,eye_hashes,inspect,exercise,material_snapshot
from feathers_checks import hashes
from feathers_geometry import set_gesture
from face_geometry import set_blink
from beak_geometry import set_open
from validation_setup import setup,studio_snapshot

parser=argparse.ArgumentParser()
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--mode',choices=('preview','baseline_snapshot','build','saved_build','reload_a','reload_b'),required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);ROOT=args.work.resolve()
assert Path(bpy.data.filepath).resolve()==ROOT/'candidate.blend','Only host-owned explicit scratch scene allowed'


def write(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def render(label):
    folder=ROOT/'renders'/label;folder.mkdir(parents=True,exist_ok=True)
    before=studio_snapshot();setup(ROOT)
    assert studio_snapshot()==before,'Studio changed'
    for name in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q'):
        bpy.context.scene.camera=bpy.data.objects[name]
        bpy.context.scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
    assert studio_snapshot()==before


if args.mode=='baseline_snapshot':
    write('baseline_snapshot.json',{'shape_sha256':shape_hashes(),'eye_state_sha256':eye_hashes()})
elif args.mode=='preview':
    build(ROOT)
    write('preview_checks.json',inspect(ROOT))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    render('preview')
else:
    if args.mode=='build':
        baseline=shape_hashes();eyes=eye_hashes();before=studio_snapshot();render('baseline');build(ROOT)
        first=hashes();first_shapes=shape_hashes()
        counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
        build(ROOT)
        assert first==hashes() and first_shapes==shape_hashes(),'Repeat build differs'
        assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)),'Build leaked datablocks'
        unchanged={n:h for n,h in baseline.items() if n not in set(CHANGED)|set(REMOVED)}
        assert len(unchanged)==78 and all(first_shapes[n]==h for n,h in unchanged.items()),'Unauthorised cage change'
        assert eyes==eye_hashes(),'Diagnostic eyes changed before #19'
    checks=inspect(ROOT);checks['movement']=exercise(ROOT)
    assert checks['geometry_sha256']==hashes(),'Neutral restoration drift'
    if args.mode=='build':
        checks['unchanged_shape_sha256']=unchanged;checks['baseline_shape_sha256']=baseline;checks['baseline_eye_state_sha256']=eyes
        checks['repeated_build_identical']=True;checks['datablock_counts']=list(counts)
        assert {k:v for k,v in studio_snapshot().items() if k!='scene_object_count'}=={k:v for k,v in before.items() if k!='scene_object_count'},'Fixed studio changed'
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);render('live_neutral')
        set_blink(ROOT,1);render('blink');set_blink(ROOT,0)
        set_open(ROOT,1);render('beak_open');set_open(ROOT,0)
        for label,left,right in (('gesture_left',1,0),('gesture_right',0,1),('gesture_both',1,1)):
            set_gesture(ROOT,left,right);render(label)
        set_gesture(ROOT,0,0);assert hashes()==first
    else:render('neutral' if args.mode=='saved_build' else args.mode)
    write(args.mode+'_checks.json',checks)
print('MATERIALS EVIDENCE OK:',args.mode)
