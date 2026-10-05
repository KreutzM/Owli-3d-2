"""Development gate: build, repeat, scale and deliberately corrupt actual foot geometry."""
import json
import shutil
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from feet_geometry import build
from verify_feet import inspect
from verify_face import digest_part

root = Path.cwd()
out = root/'tmp/feet'
out.mkdir(parents=True,exist_ok=True)
unchanged = {o.name:digest_part(o) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('GRP_','GUIDE_Foot','GUIDE_Leg','GUIDE_Toe','GUIDE_Claw','BLK_Perch'))}
assert len(unchanged)==37,('Unexpected accepted predecessor',len(unchanged))
build(root)
proof = inspect(root)
snapshot = {o.name:digest_part(o) for o in bpy.data.objects if o.name.startswith('GRP_')}
coordinates = {o.name:[tuple(v.co) for v in o.data.vertices] for o in bpy.data.objects if o.name.startswith('GRP_')}
build(root)
assert snapshot=={o.name:digest_part(o) for o in bpy.data.objects if o.name.startswith('GRP_')}
proof['repeated_build_identical'] = True
proof['unchanged_part_sha256'] = unchanged
assert all(digest_part(bpy.data.objects[name])==digest for name,digest in unchanged.items())

scratch = out/'scale_probe'
shutil.copytree(root/'design',scratch/'design',dirs_exist_ok=True)
spec_path = scratch/'design/character_spec.json'
original_spec = json.loads(spec_path.read_text())
for factor in (.5,2):
    spec = json.loads(json.dumps(original_spec))
    spec['production_scale']['character_height_m'] *= factor
    spec_path.write_text(json.dumps(spec)+'\n',newline='\n')
    build(scratch)
    inspect(scratch)
    for name,points in coordinates.items():
        actual = bpy.data.objects[name].data.vertices
        assert len(points)==len(actual)
        assert all(max(abs(a/factor-b) for a,b in zip(v.co,p))<3e-8 for v,p in zip(actual,points)),(name,'scale drift')
build(root)
proof['global_scale_factors'] = [.5,2]
feet_path = scratch/'design/feet.json'
original_feet = json.loads(feet_path.read_text())
spec_path.write_text(json.dumps(original_spec)+'\n',newline='\n')
proof['parameter_probes'] = []
for radius,spacing in [(.016,.05),(.022,.062)]:
    cfg = json.loads(json.dumps(original_feet))
    cfg['bar_radius_m'],cfg['foot_half_spacing_m'] = radius,spacing
    feet_path.write_text(json.dumps(cfg)+'\n',newline='\n')
    build(scratch)
    inspect(scratch)
    proof['parameter_probes'].append({'bar_radius_m':radius,'foot_half_spacing_m':spacing,'actual_contact_valid':True})
build(root)
proof['negative_probes'] = {}
obj = bpy.data.objects['GRP_Claw_L_Rear_1']
for name,offset in [('floating_claw',(0,-.01,0)),('penetrating_claw',(0,.003,0)),('rear_on_front',(0,.05,0))]:
    obj.location = offset
    bpy.context.view_layer.update()
    try:
        inspect(root)
    except AssertionError as error:
        proof['negative_probes'][name] = str(error)
    else:
        raise AssertionError('Invalid grip passed: '+name)
    finally:
        obj.location = (0,0,0)
        bpy.context.view_layer.update()
assert all(digest_part(bpy.data.objects[name])==digest for name,digest in unchanged.items())
assert snapshot=={o.name:digest_part(o) for o in bpy.data.objects if o.name.startswith('GRP_')}
proof['geometry_sha256'] = snapshot
bpy.ops.wm.save_as_mainfile(filepath=str(out/'prototype.blend'))
(out/'build_checks.json').write_text(json.dumps(proof,indent=2)+'\n',newline='\n')
print('FEET DEVELOPMENT GATES PASSED: closed quad topology, actual triangle contact, repeat, scale, unchanged predecessor and negative probes.')
