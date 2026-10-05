"""Build/reopen #15 milestone, validate real topology/deformation, publish fixed-view evidence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont
from project import find_blender
from setup_review import sha256, image_metrics, review_boards
from silhouette_review import validate_review

ROOT=Path(__file__).resolve().parents[1]
VIEWS=('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')


def silhouette_metrics(first, second, tolerance, iou_min):
    with Image.open(first) as source: a=source.getchannel('A').point(lambda v:255 if v>=128 else 0)
    with Image.open(second) as source: b=source.getchannel('A').point(lambda v:255 if v>=128 else 0)
    intersection=sum(ImageChops.darker(a,b).histogram()[1:])
    union=sum(ImageChops.lighter(a,b).histogram()[1:])
    iou=intersection/union
    expanded_a=a.filter(ImageFilter.MaxFilter(2*tolerance+1))
    expanded_b=b.filter(ImageFilter.MaxFilter(2*tolerance+1))
    outside_a=ImageChops.subtract(a,expanded_b).getbbox()
    outside_b=ImageChops.subtract(b,expanded_a).getbbox()
    if iou<iou_min or outside_a or outside_b:
        raise RuntimeError(f'Silhouette changed beyond gate: {first.name}: IoU={iou:.6f}, excess={outside_a}/{outside_b}')
    return {'intersection_over_union':iou,'maximum_axis_pixel_distance_limit':tolerance,'within_distance_limit':True}


def build_review(blender):
    freeze=json.loads((ROOT/'design/silhouette_freeze.json').read_text())
    errors=validate_review(ROOT,freeze)
    if errors: raise RuntimeError('\n'.join(errors))
    policy=json.loads((ROOT/'design/head_body.json').read_text())
    cfg=json.loads((ROOT/'validation/reference_views.json').read_text())
    scripts=ROOT/'scripts/blender'
    output=ROOT/'validation/reviews/head_body_v01'
    scene_output=ROOT/'blender/scene/owli_head_body_v01.blend'
    scratch_parent=ROOT/'tmp'
    scratch_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='primary-review-',dir=scratch_parent) as folder:
        scratch=Path(folder)
        shutil.copytree(ROOT/'design',scratch/'design')
        (scratch/'validation').mkdir()
        shutil.copy2(ROOT/'validation/reference_views.json',scratch/'validation/reference_views.json')
        prefix=("import json,runpy,sys,os\nfrom pathlib import Path\nimport bpy\n"
                f"sys.path.insert(0,{str(scripts)!r})\n"
                "from primary_geometry import build,source_tree\nfrom verify_primary import inspect,exercise,envelope_deviation,rejection_probes\n"
                "from verify_validation_setup import geometry_digest\n"
                "from validation_setup import read_config,setup,studio_snapshot,frame_bounds\n"
                "from primary_evidence import render_set,wires\nroot=Path.cwd()\ncfg=read_config(root)\n")
        driver=scratch/'build.py'
        driver.write_text(prefix+
            f"for name in {['00_scene_setup.py','10_blockout.py','40_feet_perch.py']!r}:\n"
            f"    runpy.run_path(str(Path({str(scripts)!r})/name),run_name='__main__')\n"
            "unchanged=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('BLK_Head','BLK_Body','BLK_Tuft_','BLK_Brow_'))]\n"
            "from hashlib import sha256\n"
            "def digest_part(o):\n"
            "    return sha256(repr(([tuple(row) for row in o.matrix_world],[tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()\n"
            "parts={n:digest_part(bpy.data.objects[n]) for n in unchanged}\n"
            "sources={'PRI_HeadNeckTorso':[source_tree(bpy.data.objects[n])[0] for n in ('BLK_Head','BLK_Body')]}\n"
            "for kind in ('Brow','Tuft'):\n"
            "    for side in ('L','R'): sources['PRI_'+kind+'_'+side]=[source_tree(bpy.data.objects['BLK_'+kind+'_'+side])[0]]\n"
            "render_set(root,'validation/evidence/baseline/full')\n"
            "coarse={o.name for o in bpy.data.objects if o.name.startswith(('BLK_Head','BLK_Body','BLK_Tuft_','BLK_Brow_'))}\n"
            "render_set(root,'validation/evidence/baseline/primary',coarse)\n"
            f"runpy.run_path({str(scripts/'20_head_body.py')!r},run_name='__main__')\n"
            "checks=inspect(root)\nchecks['deformation_probes']=exercise(root)\n"
            "checks['frozen_envelope_deviation']=envelope_deviation(root,sources)\n"
            "checks['rejection_probes']=rejection_probes()\n"
            "assert all(digest_part(bpy.data.objects[n])==h for n,h in parts.items())\n"
            "checks['unchanged_part_sha256']=parts\n"
            "before=geometry_digest(cfg)\ncounts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))\n"
            "build(root)\nassert geometry_digest(cfg)==before,'Rebuild changed primary geometry'\n"
            "assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)),'Datablock leak'\n"
            "# Global scale probe rebuilds the entire scene in the isolated fixture.\n"
            "specpath=root/'design/character_spec.json'\nsource=specpath.read_text()\nspec=json.loads(source)\n"
            "positions={o.name:[tuple(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.data.objects if o.type=='MESH'}\n"
            "try:\n"
            "    spec['production_scale']['character_height_m']*=.8\n    specpath.write_text(json.dumps(spec))\n"
            f"    for name in {['10_blockout.py','40_feet_perch.py','20_head_body.py']!r}: runpy.run_path(str(Path({str(scripts)!r})/name),run_name='__main__')\n"
            "    inspect(root)\n"
            "    for name,points in positions.items():\n"
            "        current=bpy.data.objects[name]\n        assert len(points)==len(current.data.vertices)\n"
            "        for p,v in zip(points,current.data.vertices):\n"
            "            assert all(abs(a*.8-b)<1e-6 for a,b in zip(p,current.matrix_world@v.co)),name\n"
            "finally:\n    specpath.write_text(source)\n"
            f"    for name in {['10_blockout.py','40_feet_perch.py','20_head_body.py']!r}: runpy.run_path(str(Path({str(scripts)!r})/name),run_name='__main__')\n"
            "assert geometry_digest(cfg)==before,'Scale probe did not restore geometry'\n"
            "checks['global_scale_probe']=True\nchecks['repeated_build_identical']=True\nchecks['datablock_counts']=counts\n"
            "studio=studio_snapshot()\nsetup(root)\nassert studio_snapshot()==studio\nassert geometry_digest(cfg)==before\n"
            f"runpy.run_path({str(scripts/'90_validation.py')!r},run_name='__main__')\n"
            "checks['geometry_sha256']=geometry_digest(cfg)\nchecks['studio']=studio_snapshot()\n"
            "checks['framing']=frame_bounds(cfg,[bpy.data.objects[n] for n in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')])\n"
            "Path('baseline_checks.json').write_text(json.dumps(checks,indent=2))\n"
            "render_set(root,'validation/evidence/candidate/full')\n"
            "render_set(root,'validation/evidence/candidate/primary',{o.name for o in bpy.data.objects if o.name.startswith('PRI_')})\n"
            "wires(root,'validation/evidence/topology')\n"
            "wires(root,'validation/evidence/head_tilt',probe='head_tilt')\n"
            "wires(root,'validation/evidence/head_turn',probe='head_turn')\n"
            "wires(root,'validation/evidence/wing_root_L',probe='wing_root_L')\n"
            "wires(root,'validation/evidence/wing_root_R',probe='wing_root_R')\n"
            "assert geometry_digest(cfg)==before,'Review visualization changed geometry'\n",encoding='utf-8')
        command=[blender,'--background','--factory-startup','--python-exit-code','1']
        env=dict(os.environ)
        env.pop('OWLI_RENDER_SIZE',None)
        env.pop('OWLI_VALIDATION_OUTPUT',None)
        subprocess.run(command+['--python',str(driver)],cwd=scratch,env=env,check=True)
        baseline=json.loads((scratch/'baseline_checks.json').read_text())
        reload=scratch/'reload.py'
        reload.write_text(prefix+
            "checks=inspect(root)\nchecks['deformation_probes']=exercise(root)\n"
            "checks['geometry_sha256']=geometry_digest(cfg)\nchecks['studio']=studio_snapshot()\n"
            "checks['framing']=frame_bounds(cfg,[bpy.data.objects[n] for n in ('VAL_FRONT','VAL_LEFT','VAL_BACK','VAL_3Q')])\n"
            "Path('reload_checks.json').write_text(json.dumps(checks,indent=2))\n"
            "os.environ['OWLI_VALIDATION_OUTPUT']=str(root/'validation/reloaded')\n"
            f"runpy.run_path({str(scripts/'90_validation.py')!r},run_name='__main__')\n"
            "assert geometry_digest(cfg)==checks['geometry_sha256']\n",encoding='utf-8')
        subprocess.run(command+[str(scratch/'blender/scene/owli.blend'),'--python',str(reload)],cwd=scratch,env=env,check=True)
        reloaded=json.loads((scratch/'reload_checks.json').read_text())
        assert all(reloaded[key]==baseline[key] for key in reloaded),'Fresh reload changed topology/studio/probes'
        # Canonical delivery images come from the saved scene, in fresh Blender processes.
        # Compare two independent reloads rather than EEVEE's in-memory build render cache.
        shutil.move(scratch/'validation/renders',scratch/'validation/build_render')
        shutil.move(scratch/'validation/reloaded',scratch/'validation/renders')
        subprocess.run(command+[str(scratch/'blender/scene/owli.blend'),'--python',str(reload)],cwd=scratch,env=env,check=True)
        twice=json.loads((scratch/'reload_checks.json').read_text())
        assert twice==reloaded,'Second fresh open changed topology/studio/probes'
        checks={'baseline':baseline,'reloaded':reloaded,'reload_identical':True,'render_metrics':{},'silhouette_comparison':{},'design_approval':False}
        for view in VIEWS:
            first=scratch/'validation/renders'/f'{view}.png'
            second=scratch/'validation/reloaded'/f'{view}.png'
            with Image.open(first) as a,Image.open(second) as b:
                assert a.tobytes()==b.tobytes(),f'Reload pixels differ: {view}'
            checks['render_metrics'][view]=dict(image_metrics(first),reload_pixels_identical=True)
            for scope in ('full','primary'):
                folder=scratch/'validation/evidence'
                checks['silhouette_comparison'][scope+'/'+view]=silhouette_metrics(
                    folder/'baseline'/scope/f'{view}.png',folder/'candidate'/scope/f'{view}.png',
                    policy['silhouette_pixel_tolerance'],policy['silhouette_iou_min'])
        # Publish only after complete real-Blender verification. Preserve manually authored report.
        output.mkdir(parents=True,exist_ok=True)
        for p in (scratch/'validation/renders').iterdir(): shutil.copy2(p,output/p.name)
        shutil.copytree(scratch/'validation/evidence',output/'evidence',dirs_exist_ok=True)
        shutil.copy2(scratch/'blender/scene/owli.blend',scene_output)
        checks['scene_sha256']=sha256(scene_output)
        sources=[ROOT/'design/head_body.json',ROOT/'design/proportions.json',ROOT/'design/character_spec.json',ROOT/'design/materials.json',ROOT/'design/silhouette_freeze.json',ROOT/'validation/reference_views.json',ROOT/'scripts/head_body_review.py']
        sources += [scripts/name for name in ('00_scene_setup.py','10_blockout.py','20_head_body.py','40_feet_perch.py','90_validation.py','primary_geometry.py','verify_primary.py','primary_evidence.py','blockout_geometry.py','validation_setup.py')]
        checks['source_sha256']={p.relative_to(ROOT).as_posix():sha256(p) for p in sources}
        checks['frozen_scene_sha256']=sha256(ROOT/'blender/scene/owli_blockout_v01.blend')
        checks['config_sha256']=sha256(ROOT/'validation/reference_views.json')
        review_boards(ROOT,output,cfg,'head_body_v01 (#15 primary topology)')
        checks['evidence_sha256']={p.relative_to(output).as_posix():sha256(p) for p in output.rglob('*.png')}
        (output/'verification.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'PRIMARY REVIEW OK: topology, deformation, scale, fixed silhouettes, fresh reload. {output}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender')
    args=parser.parse_args()
    build_review(find_blender(args.blender))
