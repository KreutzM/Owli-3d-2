"""Editable coarse volumes; dimensions are authored in proportions.json, in meters."""
import json
import math
from pathlib import Path
import bpy


def parameters(root):
    cfg = json.loads((Path(root) / 'design/proportions.json').read_text())
    spec = json.loads((Path(root) / 'design/character_spec.json').read_text())
    return cfg, spec['production_scale']['character_height_m'] / cfg['reference_height_m']


def clean(prefixes):
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)


def swatch(root, color):
    palette = json.loads((Path(root) / 'design/materials.json').read_text())['sampled_logo_colors']
    rgb = [int(palette[color][i:i+2], 16)/255 for i in (1, 3, 5)]
    rgba = tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb) + (1,)
    mat = bpy.data.materials.get('BLK_Swatch_' + color) or bpy.data.materials.new('BLK_Swatch_' + color)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = rgba
    node.inputs['Roughness'].default_value = .8
    node.inputs['Metallic'].default_value = 0
    mat['status'] = 'debug palette swatch, not final lookdev'
    return mat


def finish(obj, name, group, material):
    obj.name = name
    obj.data.name = name + '_Mesh'
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    bpy.data.collections[group].objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj['status'] = 'provisional_blockout'
    return obj


def mesh(name, vertices, faces, group, material):
    data = bpy.data.meshes.new(name + '_Mesh')
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    return finish(obj, name, group, material)


def ellipsoid(name, center, dimensions, scale, group, material):
    vertices = [(0, 0, -dimensions[2]*scale/2)]
    for k in range(1, 16):
        theta = math.pi*k/16
        for j in range(32):
            phi = math.tau*j/32
            vertices.append((dimensions[0]*scale/2*math.sin(theta)*math.cos(phi),
                             dimensions[1]*scale/2*math.sin(theta)*math.sin(phi),
                             -dimensions[2]*scale/2*math.cos(theta)))
    vertices.append((0, 0, dimensions[2]*scale/2))
    faces = [(0, 1+(j+1)%32, 1+j) for j in range(32)]
    for k in range(14):
        for j in range(32):
            a, b = 1+k*32+j, 1+k*32+(j+1)%32
            faces.append((a, b, b+32, a+32))
    faces.extend((len(vertices)-1, 1+14*32+j, 1+14*32+(j+1)%32) for j in range(32))
    obj = mesh(name, vertices, faces, group, material)
    obj.location = [v*scale for v in center]
    return obj


def loft(name, rings, scale, group, material, mirror=1):
    # Each ring: z, center_x, center_y, radius_x, radius_y. Quads remain editable.
    count = 32
    vertices = []
    for z, x, y, rx, ry in rings:
        for j in range(count):
            angle = j*math.tau/count
            vertices.append((mirror*(x+rx*math.cos(angle))*scale,
                             (y+ry*math.sin(angle))*scale, z*scale))
    faces = [tuple(reversed(range(count)))]
    for k in range(len(rings)-1):
        for j in range(count):
            a = k*count+j
            b = k*count+(j+1)%count
            faces.append((a, b, b+count, a+count))
    faces.append(tuple(range((len(rings)-1)*count, len(rings)*count)))
    if mirror < 0:
        faces = [tuple(reversed(f)) for f in faces]
    obj = mesh(name, vertices, faces, group, material)
    sub = obj.modifiers.new('Coarse smoothing', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    return obj


def cap(name, center, radius, angle, scale, material):
    vertices = [(center[0]*scale, (center[1]+radius)*scale, center[2]*scale)]
    for k in range(1, 9):
        theta = angle*k/8
        for j in range(32):
            phi = math.tau*j/32
            vertices.append(((center[0]+radius*math.sin(theta)*math.cos(phi))*scale,
                             (center[1]+radius*math.cos(theta))*scale,
                             (center[2]+radius*math.sin(theta)*math.sin(phi))*scale))
    faces = [(0, 1+(j+1)%32, 1+j) for j in range(32)]
    for k in range(7):
        for j in range(32):
            a, b = 1+k*32+j, 1+k*32+(j+1)%32
            faces.append((a, b, b+32, a+32))
    return mesh(name, vertices, faces, 'EYES', material)


def save(root):
    bpy.context.view_layer.update()
    path = bpy.data.filepath or str(Path(root)/'blender/scene/owli.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path)
