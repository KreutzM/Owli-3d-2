"""Actual isolated #19 build, saved-open and two fresh-open Blender workers."""
import argparse
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from eyes_geometry import build, CHANGED, SOCKETS, configure_lids, set_blink
from eyes_checks import inspect, exercise, state_snapshot
from materials_checks import shape_hashes, eye_hashes
from feathers_checks import hashes
from beak_geometry import set_open
from feathers_geometry import set_gesture
from validation_setup import setup, studio_snapshot

parser = argparse.ArgumentParser()
parser.add_argument('--work', type=Path, required=True)
parser.add_argument('--mode', choices=('preview','baseline_snapshot','build','saved_build','reload_a','reload_b'), required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT = args.work.resolve()
assert Path(bpy.data.filepath).resolve() == ROOT/'candidate.blend', 'Only explicit scratch candidate allowed'


def write(name, data):
    (ROOT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def render(label):
    folder = ROOT/'renders'/label
    folder.mkdir(parents=True,exist_ok=True)
    before = studio_snapshot(); setup(ROOT)
    assert studio_snapshot() == before, 'Studio changed'
    for name in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q'):
        bpy.context.scene.camera = bpy.data.objects[name]
        bpy.context.scene.render.filepath = str(folder/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    assert studio_snapshot() == before


if args.mode == 'baseline_snapshot':
    write('baseline_snapshot.json', dict(shape_sha256=shape_hashes(), **state_snapshot()))
elif args.mode == 'preview':
    build(ROOT); write('preview_checks.json',inspect(ROOT))
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath); render('preview')
else:
    if args.mode == 'build':
        baseline = shape_hashes(); baseline_state = state_snapshot(); before = studio_snapshot()
        render('baseline'); build(ROOT)
        first = hashes(); first_shapes = shape_hashes(); first_state = state_snapshot(); first_eye_state = eye_hashes()
        counts = (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
        build(ROOT)
        assert first == hashes() and first_shapes == shape_hashes() and first_state == state_snapshot(), 'Repeated eye build drift'
        assert first_eye_state == eye_hashes(), 'Repeated build changed actual eye slots or complete shader graphs'
        assert counts == (len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)), 'Repeated build leaks'
        assert all(first_state['unchanged_non_eye_sha256'][name] == value
                   for name,value in baseline_state['unchanged_non_eye_sha256'].items()
                   if name not in SOCKETS), 'Protected non-eye state changed'
        assert all(first_state['pivot_state_sha256'][name] == value
                   for name,value in baseline_state['pivot_state_sha256'].items()
                   if not name.startswith('FAC_EyeAim_')), 'Protected pivots changed'
        assert all(first_state['eye_local_shape_sha256'][name] == value
                   for name,value in baseline_state['eye_local_shape_sha256'].items()
                   if name.startswith(('FAC_Globe_', 'FAC_Cornea_'))), 'Local globe/cornea envelope changed'
        assert all(first_state['normals_state_sha256'][name] == value
                   for name,value in baseline_state['normals_state_sha256'].items()
                   if name not in SOCKETS and not name.startswith(('FAC_Iris_', 'FAC_Pupil_'))), 'Protected actual corner normals changed'
        assert all(first_shapes[name] == value for name,value in baseline.items() if name not in CHANGED), 'Unexpected cage change'
        assert studio_snapshot() == before, 'Fixed studio changed'
    configure_lids(ROOT)
    neutral_state = state_snapshot()
    checks = inspect(ROOT); checks['movement'] = exercise(ROOT)
    assert checks['geometry_sha256'] == hashes(), 'Neutral restoration drift'
    assert neutral_state == state_snapshot(), 'Full neutral state or corner-normal restoration drift'
    if args.mode == 'build':
        checks['baseline_shape_sha256'] = baseline
        checks['baseline_non_eye_sha256'] = baseline_state['unchanged_non_eye_sha256']
        checks['baseline_normals_state_sha256'] = baseline_state['normals_state_sha256']
        checks['baseline_eye_local_shape_sha256'] = baseline_state['eye_local_shape_sha256']
        checks['repeated_build_identical'] = True
        checks['datablock_counts'] = list(counts)
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath); render('live_neutral')
        set_blink(ROOT,1); render('blink'); set_blink(ROOT,0)
        set_open(ROOT,1); render('beak_open'); set_open(ROOT,0)
        for label,left,right in (('gesture_left',1,0),('gesture_right',0,1),('gesture_both',1,1)):
            set_gesture(ROOT,left,right); render(label)
        set_gesture(ROOT,0,0)
        assert first == hashes(), 'Endpoint neutral restoration drift'
        assert first_state == state_snapshot(), 'Endpoint full-state or corner-normal restoration drift'
    else:
        render('neutral' if args.mode == 'saved_build' else args.mode)
    write(args.mode+'_checks.json',checks)
print('EYES EVIDENCE OK:',args.mode)
