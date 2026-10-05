"""Explicit isolated #6 worker; only opens/saves a host-owned scratch scene."""
import argparse
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from feathers_geometry import build,set_gesture
from verify_face import digest_part
from face_geometry import set_blink
from beak_geometry import set_open
from validation_setup import setup,studio_snapshot

parser = argparse.ArgumentParser()
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--mode',choices=('preview','build','saved_build','reload_a','reload_b'),required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT = args.work.resolve()
assert Path(bpy.data.filepath).resolve().is_relative_to(ROOT),'Scene must be in work directory'


def write(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')


def hashes():
    return {o.name:digest_part(o) for o in bpy.context.scene.objects if o.type=='MESH'}


def render(label):
    folder = ROOT/'renders'/label
    folder.mkdir(parents=True,exist_ok=True)
    before = studio_snapshot()
    setup(ROOT)
    assert studio_snapshot()==before,'Studio changed'
    for name in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q'):
        bpy.context.scene.camera = bpy.data.objects[name]
        bpy.context.scene.render.filepath = str(folder/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    assert studio_snapshot()==before


if args.mode=='preview':
    build(ROOT)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    render('preview')
    write('preview_inventory.json',{'geometry_sha256':hashes(),'studio':studio_snapshot(),
          'objects':len(bpy.context.scene.objects),'meshes':len(hashes())})
else:
    from feathers_checks import inspect,exercise
    from feathers_geometry import REMOVED
    if args.mode=='build':
        baseline = hashes()
        before = studio_snapshot()
        render('baseline')
        build(ROOT)
        first = hashes()
        counts = (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
        build(ROOT)
        assert first==hashes(),'Repeat build differs'
        assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)),'Build leaked datablocks'
        unchanged = {n:h for n,h in baseline.items() if n not in REMOVED}
        assert len(unchanged)==44 and all(first[n]==h for n,h in unchanged.items())
    checks = inspect(ROOT)
    checks['movement'] = exercise(ROOT)
    assert hashes()==checks['geometry_sha256'],'Neutral restoration drift'
    if args.mode=='build':
        checks['unchanged_part_sha256'] = unchanged
        checks['repeated_build_identical'] = True
        checks['datablock_counts'] = list(counts)
        # The scene inventory grows; camera/light/world/render settings remain exact.
        assert {k:v for k,v in studio_snapshot().items() if k!='scene_object_count'}=={
            k:v for k,v in before.items() if k!='scene_object_count'},'Fixed studio changed during geometry build'
        set_gesture(ROOT,0,0)
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        render('live_neutral')
        set_blink(ROOT,1)
        render('blink')
        set_blink(ROOT,0)
        set_open(ROOT,1)
        render('beak_open')
        set_open(ROOT,0)
        for label,left,right in (('gesture_left',1,0),('gesture_right',0,1),('gesture_both',1,1)):
            set_gesture(ROOT,left,right)
            render(label)
        set_gesture(ROOT,0,0)
        assert hashes()==first
    else:
        render('neutral' if args.mode=='saved_build' else args.mode)
    write(args.mode+'_checks.json',checks)
print('FEATHERS EVIDENCE OK:',args.mode)
