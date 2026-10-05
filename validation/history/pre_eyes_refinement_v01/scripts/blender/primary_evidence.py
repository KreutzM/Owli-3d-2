"""Additional fixed-camera silhouette, wire and deformation evidence; never saved into delivery."""
from pathlib import Path
import bpy
from validation_setup import setup
from verify_primary import deform


def render_set(root, output, names=None):
    _,cams=setup(root)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    saved={o.name:o.hide_render for o in bpy.data.objects if o.type=='MESH'}
    transparent=scene.render.film_transparent
    scene.render.film_transparent=True
    try:
        if names is not None:
            for name in saved: bpy.data.objects[name].hide_render=name not in names
        for cam in cams:
            scene.camera=cam
            scene.render.filepath=str((output/(cam.name+'.png')).resolve())
            bpy.ops.render.render(write_still=True)
    finally:
        for name,value in saved.items(): bpy.data.objects[name].hide_render=value
        scene.render.film_transparent=transparent
        setup(root)


def wires(root, output, probe=None):
    names={o.name for o in bpy.data.objects if o.name.startswith('PRI_')}
    gray=bpy.data.materials.new('_PRIMARY_REVIEW_CLAY')
    gray.diffuse_color=(.3,.38,.48,1)
    black=bpy.data.materials.new('_PRIMARY_REVIEW_WIRE')
    black.diffuse_color=(.015,.025,.035,1)
    for material in (gray,black):
        material.use_nodes=True
        node=material.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value=material.diffuse_color
        node.inputs['Roughness'].default_value=.8
    saved={}
    original=None
    try:
        if probe: original=deform(root,probe)
        for name in names:
            obj=bpy.data.objects[name]
            saved[name]=(obj.data,obj.modifiers[0].show_render)
            obj.data=obj.data.copy()
            obj.data.materials.clear()
            obj.data.materials.append(gray)
            obj.data.materials.append(black)
            for p in obj.data.polygons: p.material_index=0
            obj.modifiers[0].show_render=False
            modifier=obj.modifiers.new('_Review wires','WIREFRAME')
            modifier.thickness=.00035
            modifier.use_replace=False
            modifier.use_even_offset=True
            modifier.material_offset=1
        render_set(root,output,names)
    finally:
        for name,(data,show) in saved.items():
            obj=bpy.data.objects[name]
            duplicate=obj.data
            obj.data=data
            bpy.data.meshes.remove(duplicate)
            obj.modifiers.remove(obj.modifiers['_Review wires'])
            obj.modifiers[0].show_render=show
        if original is not None:
            obj=bpy.data.objects['PRI_HeadNeckTorso']
            for v,p in zip(obj.data.vertices,original): v.co=p
            obj.data.update()
        bpy.data.materials.remove(gray)
        bpy.data.materials.remove(black)
        bpy.context.view_layer.update()
