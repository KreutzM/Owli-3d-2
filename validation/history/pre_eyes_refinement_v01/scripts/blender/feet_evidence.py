"""Build the #5 stage and independently reopen its geometry in the fixed studio."""
import json
import os
from pathlib import Path
import runpy
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from primary_evidence import render_set
from verify_feet import inspect
from verify_face import digest_part
from validation_setup import setup,studio_snapshot,frame_bounds

ROOT=Path.cwd()
MODE=os.environ['OWLI_FEET_MODE']
SCRIPTS=Path(__file__).resolve().parent


def snapshot():
    cfg,cameras=setup(ROOT)
    result=inspect(ROOT)
    result['geometry_sha256']={o.name:digest_part(o) for o in bpy.data.objects if o.name.startswith('GRP_')}
    result['unchanged_part_sha256']={o.name:digest_part(o) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('GRP_')}
    result['empty_transforms']={o.name:[list(row) for row in o.matrix_world] for o in bpy.data.objects if o.type=='EMPTY'}
    result['studio']=studio_snapshot()
    result['framing']=frame_bounds(cfg,cameras)
    return result


if MODE=='build':
    setup(ROOT)
    predecessor_pivots={o.name:[list(row) for row in o.matrix_world] for o in bpy.data.objects if o.type=='EMPTY'}
    render_set(ROOT,ROOT/'validation/evidence/baseline/full')
    render_set(ROOT,ROOT/'validation/evidence/baseline/feet',{o.name for o in bpy.data.objects if o.name.startswith(('GUIDE_Foot','GUIDE_Toe','GUIDE_Leg','BLK_Perch'))})
    runpy.run_path(str(SCRIPTS/'40_feet_perch.py'),run_name='__main__')
    stage={o.name:digest_part(o) for o in bpy.data.objects if o.name.startswith('GRP_')}
    runpy.run_path(str(SCRIPTS/'feet_probe.py'),run_name='__main__')
    proof=json.loads((ROOT/'tmp/feet/build_checks.json').read_text())
    checks=snapshot()
    assert stage==checks['geometry_sha256'],'Production entry point differs from probe build'
    assert predecessor_pivots==checks['empty_transforms'],'Face or beak pivot changed'
    proof.update(checks)
    render_set(ROOT,ROOT/'validation/evidence/candidate/full')
    render_set(ROOT,ROOT/'validation/evidence/candidate/feet',{o.name for o in bpy.data.objects if o.name.startswith('GRP_')})
    render_set(ROOT,ROOT/'validation/evidence/candidate/toes',{o.name for o in bpy.data.objects if o.name.startswith(('GRP_Foot','GRP_Claw'))})
    setup(ROOT)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    (ROOT/'build_checks.json').write_text(json.dumps(proof,indent=2)+'\n',newline='\n')
else:
    checks=snapshot()
    os.environ['OWLI_VALIDATION_OUTPUT']=str(ROOT/'validation'/MODE)
    runpy.run_path(str(SCRIPTS/'90_validation.py'),run_name='__main__')
    (ROOT/(MODE+'_checks.json')).write_text(json.dumps(checks,indent=2)+'\n',newline='\n')
