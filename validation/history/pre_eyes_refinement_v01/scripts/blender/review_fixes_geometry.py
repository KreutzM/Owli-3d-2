"""Parametric #37 broad facial discs and raised organic brow volumes.

Work on an explicit copy of #5. No alteration of historical eye/lid/beak recipes.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from blockout_geometry import clean, parameters, swatch
from face_geometry import shell, finish
from primary_geometry import source_tree

CHANGED = ('FAC_Mask_L', 'FAC_Mask_R', 'FAC_MaskBridge', 'PRI_Brow_L', 'PRI_Brow_R')


def sample_loop(points, value):
    """Periodic cubic interpolation, same angular correspondence as socket rings."""
    position = value * len(points)
    k, t = math.floor(position), position % 1
    p0, p1, p2, p3 = [Vector(points[i % len(points)]) for i in (k-1, k, k+1, k+2)]
    return (p1*2 + (p2-p0)*t + (p0*2-p1*5+p2*4-p3)*t*t + (-p0+p1*3-p2*3+p3)*t*t*t)*.5


def sample_open(points, position):
    k = min(len(points)-2, math.floor(position))
    t = position-k
    p0,p1,p2,p3 = [Vector(points[min(len(points)-1,max(0,i))]) for i in (k-1,k,k+1,k+2)]
    return (p1*2 + (p2-p0)*t + (p0*2-p1*5+p2*4-p3)*t*t + (-p0+p1*3-p2*3+p3)*t*t*t)*.5


def build(root):
    root = Path(root)
    coarse, scale = parameters(root)
    cfg = json.loads((root / 'design/review_fixes.json').read_text(encoding='utf-8'))
    head_tree = source_tree(bpy.data.objects['PRI_HeadNeckTorso'])[0]
    clean(CHANGED)
    cream, navy = swatch(root, 'cream'), swatch(root, 'deep_navy')
    count, rows = cfg['angular_segments'], cfg['mask_rows']
    eye = coarse['eyes']
    for side, sign in (('L', -1), ('R', 1)):
        points = []
        for k in range(rows+1):
            t = k/rows
            for j in range(count):
                phi = j*math.tau/count
                # Reflect the complete right disc rather than reversing angular attachment.
                inner = Vector((eye['half_spacing']+cfg['mask_inner_radius_m']*math.cos(phi),
                                eye['height']+cfg['mask_inner_radius_m']*math.sin(phi)))
                outer = sample_loop(cfg['mask_outer_contour_R_xz_m'], j/count)
                hit = head_tree.ray_cast(Vector((sign*outer.x*scale, .3*scale, outer.y*scale)), Vector((0, -1, 0)), .6*scale)[0]
                if hit is None:
                    # Project lateral requested contour onto the actual side of the head;
                    # keep the existing skull, never suspend a socket outside its skin.
                    hit = head_tree.find_nearest(Vector((sign*outer.x*scale, .025*scale, outer.y*scale)))[0]
                    outer = Vector((abs(hit.x)/scale, hit.z/scale))
                x, z = inner.lerp(outer, t)
                root_y = hit.y/scale + cfg['mask_root_front_offset_m']
                y = cfg['mask_inner_y_m']*(1-t) + root_y*t + cfg['mask_ridge_depth_m']*math.sin(math.pi*t)
                # Recess the beak/nose seat behind the fixed hooked upper jaw.
                if z < .399 and abs(x) < .039:
                    y = min(y, .088 + .006*min(1, abs(x)/.039))
                points.append((sign*x*scale, y*scale, z*scale))
        faces = []
        for k in range(rows):
            for j in range(count):
                a, b = k*count+j, k*count+(j+1)%count
                face = (a, b, b+count, a+count)
                faces.append(face if sign == 1 else tuple(reversed(face)))
        back = [(x, y-cfg['mask_thickness_m']*scale, z) for x,y,z in points]
        obj = shell('FAC_Mask_'+side, points, faces, back, cream, group='PRIMARY_FORM')
        obj['parameter_source'] = 'design/review_fixes.json'
    points, faces = [], []
    cross = 20
    knots = cfg['bridge_rows_z_width_y_m']
    bridge_rows = [sample_open(knots,i/cfg['bridge_substeps'])
                   for i in range((len(knots)-1)*cfg['bridge_substeps']+1)]
    for z, width, y in bridge_rows:
        for j in range(cross+1):
            u = 2*j/cross-1
            points.append((width*u*scale, (y+.001*(1-u*u))*scale, z*scale))
    for k in range(len(bridge_rows)-1):
        for j in range(cross):
            a = k*(cross+1)+j
            faces.append((a+1, a, a+cross+1, a+cross+2))
    obj = shell('FAC_MaskBridge', points, faces,
                [(x,y-cfg['mask_thickness_m']*scale,z) for x,y,z in points], cream, group='PRIMARY_FORM')
    obj['parameter_source'] = 'design/review_fixes.json'
    path = cfg['brow_path_R_xyz_radius_m']
    segments, cross = cfg['brow_path_samples'], cfg['brow_cross_segments']
    # Piecewise smooth interpolation of an explicit tapered curved axis; quad rings + caps.
    for side, sign in (('L', -1), ('R', 1)):
        points, faces = [], []
        for k in range(segments):
            pos = k/(segments-1)*(len(path)-1)
            i = min(len(path)-2, int(pos))
            t = pos-i
            t = t*t*(3-2*t)
            x,y,z,r = [path[i][axis]*(1-t)+path[i+1][axis]*t for axis in range(4)]
            for j in range(cross):
                phi = j*math.tau/cross
                points.append((sign*x*scale, (y+math.cos(phi)*r*1.4)*scale,
                               (z+math.sin(phi)*r*.6)*scale))
        for k in range(segments-1):
            for j in range(cross):
                a,b = k*cross+j,k*cross+(j+1)%cross
                faces.append((a,b,b+cross,a+cross))
        faces.extend((tuple(reversed(range(cross))),tuple(range((segments-1)*cross,segments*cross))))
        obj = finish('PRI_Brow_'+side, points, faces, navy, group='PRIMARY_FORM')
        obj['parameter_source'] = 'design/review_fixes.json'
    bpy.context.scene['review_fixes_scope'] = '#37 organic broad mask/bridge and raised tapered brows; eye/lid/beak/feet unchanged'
    for name in CHANGED:
        bpy.data.objects[name]['status'] = 'review_fixes_geometry_goal_37'
    bpy.context.view_layer.update()
