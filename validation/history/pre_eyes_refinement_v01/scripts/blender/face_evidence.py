"""Isolated #16 build/reload checks and fixed-camera geometric probe renders."""
import json
import math
import os
from pathlib import Path
import runpy
import sys
import bpy
import bmesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
from face_geometry import build, config, set_blink
from verify_face import inspect, exercise, digest_part, audit
from validation_setup import setup, studio_snapshot, frame_bounds
from verify_validation_setup import geometry_digest
from primary_evidence import render_set


def checks(root):
    result=inspect(root)
    result['probes']=exercise(root)
    cfg,cameras=setup(root)
    result.update(geometry_sha256=geometry_digest(cfg),studio=studio_snapshot(),framing=frame_bounds(cfg,cameras))
    return result


def rejection_probes(root):
    """Prove the gates fail for real corrupted cages and the rejected blink construction."""
    result={}
    obj=bpy.data.objects['FAC_Lid_Upper_L']
    original=obj.data
    for label,operation in [('open_lid_rejected','remove'),('reversed_face_rejected','reverse')]:
        obj.data=original.copy()
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        if operation=='remove': bmesh.ops.delete(bm,geom=[bm.faces[0]],context='FACES')
        else: bm.faces[0].normal_flip()
        bm.to_mesh(obj.data)
        bm.free()
        try:
            try: audit(obj)
            except AssertionError: result[label]=True
            else: raise AssertionError('Corrupted lid was accepted: '+label)
        finally:
            duplicate=obj.data
            obj.data=original
            bpy.data.meshes.remove(duplicate)
    path=root/'design/face.json'
    source=path.read_bytes()
    face=json.loads(source)
    try:
        face['lid_thickness_m']=face['lid_radius_offset_m']
        write(path,face)
        try: config(root)
        except ValueError: result['unsafe_lid_clearance_rejected']=True
        else: raise AssertionError('Unsafe lid thickness accepted')
        face=json.loads(source)
        face['blink_meeting_curve']=-.08
        write(path,face)
        set_blink(root,.95)
        try: audit(obj)
        except AssertionError: result['folded_canthus_rejected']=True
        else: raise AssertionError('Folded canthus accepted')
    finally:
        path.write_bytes(source)
        set_blink(root,0)
    return result


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def run(root,mode):
    cfg,cameras=setup(root)
    if mode=='build':
        replaced=('BLK_Eye_','BLK_IrisGuide_','BLK_PupilGuide_','BLK_Mask_','BLK_MaskBridge')
        parts={o.name:digest_part(o) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(replaced)}
        render_set(root,root/'validation/evidence/baseline')
        build(root)
        result=checks(root)
        result['rejection_probes']=rejection_probes(root)
        assert all(digest_part(bpy.data.objects[n])==h for n,h in parts.items()),'Unrelated geometry changed'
        result['unchanged_part_sha256']=parts
        original=geometry_digest(cfg)
        counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
        build(root)
        assert geometry_digest(cfg)==original,'Rebuild changed geometry'
        assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)),'Rebuild leaked datablocks'
        result['repeated_build_identical']=True
        result['datablock_counts']=counts
        # Exercise global scaling of the generated face without changing the accepted source scene.
        positions={o.name:[list(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('FAC_')}
        path=root/'design/character_spec.json'
        source=path.read_bytes()
        spec=json.loads(source)
        try:
            spec['production_scale']['character_height_m']*=.8
            write(path,spec)
            build(root)
            for name,points in positions.items():
                obj=bpy.data.objects[name]
                assert len(obj.data.vertices)==len(points)
                for point,v in zip(points,obj.data.vertices):
                    assert all(abs(a*.8-b)<2e-6 for a,b in zip(point,obj.matrix_world@v.co)),name
        finally:
            path.write_bytes(source)
            build(root)
        assert geometry_digest(cfg)==original,'Scale probe failed to restore face'
        assert all(digest_part(bpy.data.objects[n])==h for n,h in parts.items())
        result['face_global_scale_probe']=True
        write(root/'build_checks.json',result)
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        return
    result=checks(root)
    write(root/f'{mode}_checks.json',result)
    os.environ['OWLI_VALIDATION_OUTPUT']=str(root/'validation'/mode)
    runpy.run_path(str(Path(__file__).with_name('90_validation.py')),run_name='__main__')
    if mode!='reload_a': return
    before=geometry_digest(cfg)
    render_set(root,root/'validation/evidence/neutral')
    names={o.name for o in bpy.data.objects if o.name.startswith('FAC_') and o.type=='MESH'}
    render_set(root,root/'validation/evidence/layers',names)
    for label,values in [('half',.5),('closed',1),('wink_L',{'L':1,'R':0})]:
        set_blink(root,values)
        render_set(root,root/'validation/evidence'/label)
    set_blink(root,0)
    _,face,_=config(root)
    for label,axis,sign in [('look_up',0,1),('look_down',0,-1),('look_left',2,1),('look_right',2,-1)]:
        for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler[axis]=sign*math.radians(face['aim_probe_degrees'])
        bpy.context.view_layer.update()
        render_set(root,root/'validation/evidence'/label)
        for side in ('L','R'): bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
        bpy.context.view_layer.update()
    # Reveal the separate clear cornea geometry using a temporary inspection swatch.
    saved={}
    cream=bpy.data.materials['BLK_Swatch_cream']
    for side in ('L','R'):
        obj=bpy.data.objects['FAC_Cornea_'+side]
        saved[obj.name]=obj.data.materials[0]
        obj.data.materials[0]=cream
    try:
        render_set(root,root/'validation/evidence/cornea_geometry',set(saved))
    finally:
        for name,material in saved.items(): bpy.data.objects[name].data.materials[0]=material
    assert geometry_digest(cfg)==before,'Probe visualization changed canonical geometry'
    # Never save these temporary probe states/materials into the delivery.


if __name__=='__main__':
    run(Path.cwd(),os.environ.get('OWLI_FACE_MODE','build'))
