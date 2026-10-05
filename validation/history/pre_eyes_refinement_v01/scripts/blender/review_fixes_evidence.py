"""#37 evidence worker. Loaded file and explicit outputs must be in host-owned scratch."""
import argparse
import json
from pathlib import Path
import sys

import bpy

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from review_fixes_geometry import build, CHANGED
from review_fixes_checks import inspect, exercise, triangle_audit
from verify_face import digest_part
from face_geometry import set_blink
from beak_geometry import set_open
from validation_setup import read_config, setup, studio_snapshot, frame_bounds

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('build','saved_build','reload_a','reload_b','foot_corners'), required=True)
parser.add_argument('--work', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT = args.work.resolve()
assert Path(bpy.data.filepath).resolve().is_relative_to(ROOT), 'Loaded scene must be a work copy'


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')


def hashes():
    return {o.name: digest_part(o) for o in bpy.context.scene.objects if o.type=='MESH'}


def snapshot():
    result = inspect(ROOT)
    result['studio'] = studio_snapshot()
    result['pivots'] = {o.name: [list(row) for row in o.matrix_world] for o in bpy.context.scene.objects if o.type=='EMPTY'}
    cfg = read_config(ROOT)
    result['framing'] = frame_bounds(cfg, [bpy.data.objects[v['name']] for v in cfg['views']])
    result['movement'] = exercise(ROOT)
    assert result['geometry_sha256'] == hashes(), 'Probe restoration changed geometry'
    return result


def render(label):
    folder = ROOT/'renders'/label
    folder.mkdir(parents=True,exist_ok=True)
    scene = bpy.context.scene
    before = studio_snapshot()
    setup(ROOT)
    assert studio_snapshot() == before, 'Canonical setup changed saved cameras or lights'
    assert scene.render.resolution_x == scene.render.resolution_y == 1024
    assert scene.render.resolution_percentage == 100
    studio = studio_snapshot()
    for name in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q'):
        scene.camera = bpy.data.objects[name]
        scene.render.filepath = str(folder/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    assert studio_snapshot() == studio, 'Rendering changed fixed studio'


def negative_surfaces():
    fixtures = {
        'adjacent_shared_vertex_overlap': ([(0,0,0),(.02,0,0),(0,.02,0),(.018,.002,0),(.002,.018,0)], [(0,1,2),(0,3,4)]),
        'adjacent_shared_edge_overlap': ([(0,0,0),(.02,0,0),(0,.02,0),(.007,.006,0)], [(0,1,2),(1,0,3)]),
        'degenerate_triangle': ([(0,0,0),(.02,0,0),(.01,0,0)], [(0,1,2)]),
        'folded_quad': ([(0,0,0),(.02,.02,0),(0,.02,0),(.02,0,0)], [(0,1,2,3)]),
    }
    results = {}
    for name,(vertices,faces) in fixtures.items():
        data = bpy.data.meshes.new('_RFX_NEGATIVE_MESH')
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new('_RFX_NEGATIVE_'+name,data)
        bpy.context.scene.collection.objects.link(obj)
        try:
            try:
                triangle_audit(obj)
            except AssertionError as exc:
                results[name] = dict(rejected=True, reason=str(exc))
            else:
                raise AssertionError('Negative surface accepted: '+name)
        finally:
            bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.meshes.remove(data)
    return results


if args.mode == 'build':
    baseline = hashes()
    pivots = {o.name:[list(row) for row in o.matrix_world] for o in bpy.context.scene.objects if o.type=='EMPTY'}
    studio = studio_snapshot()
    render('baseline')
    build(ROOT)
    first = hashes()
    build(ROOT)
    assert hashes() == first, 'Repeated face correction differs'
    checks = snapshot()
    assert checks['studio'] == studio and checks['pivots'] == pivots
    unchanged = {name:digest for name,digest in baseline.items() if name not in CHANGED}
    assert len(unchanged)==45 and all(first[name]==digest for name,digest in unchanged.items())
    checks['unchanged_part_sha256'] = unchanged
    checks['repeated_build_identical'] = True
    checks['negative_surface_probes'] = negative_surfaces()
    for label, blink, beak in (('live_neutral',0,0),('blink',1,0),('beak_open',0,1)):
        set_blink(ROOT,blink)
        set_open(ROOT,beak)
        render(label)
    set_blink(ROOT,0)
    set_open(ROOT,0)
    assert hashes() == first
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    write('build_checks.json',checks)
elif args.mode in ('saved_build','reload_a','reload_b'):
    checks = snapshot()
    # Eevee's in-process build renders have small RGB cache differences despite
    # identical cages. Canonical saved-build views use their own fresh process.
    render('neutral' if args.mode=='saved_build' else args.mode)
    write(args.mode+'_checks.json',checks)
else:
    from feet_geometry import build as feet_build, config as feet_config
    from verify_feet import inspect as feet_inspect
    config_path = ROOT/'design/feet.json'
    original = config_path.read_bytes()
    policy = json.loads(original)
    result = {'allowed': [],'rejected': []}
    try:
        for radius,spacing in ((.016,.050),(.016,.062),(.022,.050),(.022,.062),(.019,.056)):
            config_path.write_text(json.dumps(dict(policy,bar_radius_m=radius,foot_half_spacing_m=spacing)),encoding='utf-8')
            feet_build(ROOT)
            proof = feet_inspect(ROOT)
            result['allowed'].append(dict(bar_radius_m=radius,foot_half_spacing_m=spacing,
                contacts=len(proof['contacts']),collision_pairs=proof['independent_surface_collision_pairs'],actual_contact_valid=True))
        for key,value in (('bar_radius_m',.0159),('bar_radius_m',.0221),('foot_half_spacing_m',.0499),('foot_half_spacing_m',.0621)):
            config_path.write_text(json.dumps(dict(policy,**{key:value})),encoding='utf-8')
            try:
                feet_config(ROOT)
            except AssertionError as exc:
                result['rejected'].append(dict(parameter=key,value=value,reason=str(exc)))
            else:
                raise AssertionError('Out-of-range foot configuration accepted')
    finally:
        config_path.write_bytes(original)
    write('foot_corners.json',result)
print('REVIEW FIXES EVIDENCE OK:',args.mode)
