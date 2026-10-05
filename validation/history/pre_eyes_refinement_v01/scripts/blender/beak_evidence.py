"""Build/reload #17 in isolation and render closed/open jaws with fixed cameras."""
import json
import os
from pathlib import Path
import runpy
import sys
import bpy
import bmesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
from beak_geometry import build,set_open,config
from verify_beak import inspect,exercise
from verify_face import digest_part,audit
from primary_geometry import source_tree
from primary_evidence import render_set
from validation_setup import setup,studio_snapshot,frame_bounds
from verify_validation_setup import geometry_digest


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def checks(root):
    result=inspect(root)
    result['opening_probes']=exercise(root)
    cfg,cameras=setup(root)
    result.update(geometry_sha256=geometry_digest(cfg),studio=studio_snapshot(),framing=frame_bounds(cfg,cameras))
    return result


def rejection_probes(root):
    result={}
    obj=bpy.data.objects['BAK_Lower']
    original=obj.data
    for label,operation in [('open_jaw_rejected','delete'),('reversed_jaw_face_rejected','reverse')]:
        obj.data=original.copy()
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        if operation=='delete': bmesh.ops.delete(bm,geom=[bm.faces[0]],context='FACES')
        else: bm.faces[0].normal_flip()
        bm.to_mesh(obj.data)
        bm.free()
        try:
            try: audit(obj)
            except AssertionError: result[label]=True
            else: raise AssertionError('Bad jaw topology was accepted')
        finally:
            duplicate=obj.data
            obj.data=original
            bpy.data.meshes.remove(duplicate)
    pivot=bpy.data.objects['BAK_LowerPivot']
    saved=pivot.location.copy()
    _,policy,scale=config(root)
    # Move pivot onto the front of the separation boundary: opening swings rear vertices into the upper jaw.
    try:
        pivot.location=tuple(x*scale for x in policy['split_plane_point_m'])
        # Keep the neutral lower cage in place while moving only the rotation center.
        delta=saved-pivot.location
        for v in obj.data.vertices: v.co+=delta
        bpy.context.view_layer.update()
        try: exercise(root)
        except AssertionError: result['forward_hinge_collision_rejected']=True
        else: raise AssertionError('Forward hinge collision was accepted')
    finally:
        for v in obj.data.vertices: v.co-=delta
        pivot.location=saved
        set_open(root,0)
    path=root/'design/beak.json'
    source=path.read_bytes()
    try:
        policy['maximum_open_degrees']=-18
        write(path,policy)
        try: config(root)
        except ValueError: result['invalid_opening_range_rejected']=True
        else: raise AssertionError('Invalid opening was accepted')
    finally: path.write_bytes(source)
    return result


def run(root,mode):
    cfg,cameras=setup(root)
    if mode=='build':
        parts={o.name:digest_part(o) for o in bpy.data.objects if o.type=='MESH' and o.name!='BLK_Beak'}
        source=source_tree(bpy.data.objects['BLK_Beak'])[0]
        render_set(root,root/'validation/evidence/baseline/full')
        render_set(root,root/'validation/evidence/baseline/beak',{'BLK_Beak'})
        build(root)
        result=checks(root)
        distance=max(source.find_nearest(o.matrix_world@v.co)[3] for o in [bpy.data.objects['BAK_Upper'],bpy.data.objects['BAK_Lower']] for v in o.data.vertices)
        assert distance<5e-7,'Jaw exterior vertices left the frozen evaluated envelope'
        result['maximum_exterior_vertex_deviation_m']=distance
        result['rejection_probes']=rejection_probes(root)
        # Rebuild after negative probes avoids floating-point drift in restored fixture cages.
        build(root)
        original=geometry_digest(cfg)
        counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials))
        build(root)
        assert geometry_digest(cfg)==original,'Beak rebuild changed geometry'
        assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.materials)),'Beak rebuild leaked data'
        assert all(digest_part(bpy.data.objects[n])==h for n,h in parts.items()),'Unrelated geometry changed'
        result['unchanged_part_sha256']=parts
        result['repeated_build_identical']=True
        result['datablock_counts']=counts
        # Rebuilt jaws/pivot must follow the same uniform global scale as the accepted model.
        positions={o.name:[list(o.matrix_world@v.co) for v in o.data.vertices] for o in [bpy.data.objects['BAK_Upper'],bpy.data.objects['BAK_Lower']]}
        path=root/'design/character_spec.json'
        source_bytes=path.read_bytes()
        spec=json.loads(source_bytes)
        try:
            spec['production_scale']['character_height_m']*=.8
            write(path,spec)
            build(root)
            for name,points in positions.items():
                obj=bpy.data.objects[name]
                assert len(points)==len(obj.data.vertices),'Scale changed topology'
                for p,v in zip(points,obj.data.vertices):
                    assert all(abs(a*.8-b)<2e-6 for a,b in zip(p,obj.matrix_world@v.co)),name
        finally:
            path.write_bytes(source_bytes)
            build(root)
        assert geometry_digest(cfg)==original,'Scale probe failed to restore jaw geometry'
        result['beak_global_scale_probe']=True
        write(root/'build_checks.json',result)
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        return
    result=checks(root)
    write(root/f'{mode}_checks.json',result)
    os.environ['OWLI_VALIDATION_OUTPUT']=str(root/'validation'/mode)
    runpy.run_path(str(Path(__file__).with_name('90_validation.py')),run_name='__main__')
    if mode!='reload_a': return
    original=geometry_digest(cfg)
    for label,value in [('closed',0),('half',.5),('open',1)]:
        set_open(root,value)
        render_set(root,root/'validation/evidence'/label/'full')
        render_set(root,root/'validation/evidence'/label/'beak',{'BAK_Upper','BAK_Lower'})
    set_open(root,0)
    assert geometry_digest(cfg)==original,'Evidence changed delivery geometry'


if __name__=='__main__': run(Path.cwd(),os.environ.get('OWLI_BEAK_MODE','build'))
