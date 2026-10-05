"""Editable broad feather groups, exact reflection, shared soft wing root field."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from blockout_geometry import clean, parameters, swatch, mesh, loft
from primary_geometry import source_tree, sampled_loft, heights_for, slice_center, smoothstep
from face_geometry import shell

REMOVED = ('BLK_Wing_L','BLK_Wing_R','BLK_Tail','BLK_Chest','BLK_ChestAccent_L','BLK_ChestAccent_R')


def config(root):
    coarse, scale = parameters(root)
    cfg = json.loads((Path(root)/'design/wings_feathers.json').read_text(encoding='utf-8'))
    if not 8 <= cfg['leaf_rows'] <= 32 or not 4 <= cfg['leaf_cross_segments'] <= 16:
        raise ValueError('Broad leaves require bounded nontrivial lattice')
    if not 0 < cfg['shell_thickness_m'] < cfg['surface_relief_m'] < .006:
        raise ValueError('Invalid feather thickness/relief')
    if not 0 < cfg['gesture_limit_degrees'] <= 15:
        raise ValueError('V1 gestures are restrained, not flight')
    return coarse,cfg,scale


def finish_leaf(name,points,faces,normals,cfg,scale,color,part,side=None):
    back = [tuple(Vector(p)-n*cfg['shell_thickness_m']*scale) for p,n in zip(points,normals)]
    obj = shell(name,points,faces,back,color,group='FEATHERS')
    obj['status'] = 'editable_broad_feather_group_goal_6'
    obj['part'] = part
    obj['parameter_source'] = 'design/wings_feathers.json'
    obj['overlap_policy'] = 'root embedded in supporting primary; neighbors intentionally shingle'
    return obj


def lattice(cfg,scale,surface):
    points,normals,faces = [],[],[]
    rows,cross = cfg['leaf_rows'],cfg['leaf_cross_segments']
    for k in range(rows+1):
        t = k/rows
        width = .025+.975*math.sin(math.pi*t)**.75
        for j in range(cross+1):
            u = 2*j/cross-1
            p,n = surface(t,u*width)
            relief = cfg['root_offset_m']+cfg['surface_relief_m']*math.sin(math.pi*t/2)*(1-.65*u*u)
            points.append(tuple((p+n*relief)*scale))
            normals.append(n)
    for k in range(rows):
        for j in range(cross):
            a = k*(cross+1)+j
            faces.append((a,a+1,a+cross+2,a+cross+1))
    return points,faces,normals


def project_leaf(name,entry,tree,cfg,scale,front,material,part):
    a,b = Vector(entry['root']),Vector(entry['tip'])
    axis = (b-a).normalized()
    transverse = Vector((-axis.y,axis.x))
    anchor = tree.ray_cast(Vector((a.x*scale,(.35 if front else -.35)*scale,a.y*scale)),
                           Vector((0,-1 if front else 1,0)),.8*scale)[0]
    assert anchor is not None,(name,'root must lie on actual supporting surface')
    def surface(t,u):
        x,z = a.lerp(b,t)+transverse*(entry['half_width']*u)
        x += entry.get('curve_x_m',0)*math.sin(math.pi*t)
        z += entry.get('curve_z_m',0)*math.sin(math.pi*t)
        if part=='face':
            # Smooth authored depth spine sampled from the accepted mask. A
            # combined mask/head BVH has discontinuous normals at their overlap;
            # projecting the thick shell through that seam folded its side walls.
            from review_fixes_geometry import sample_open
            values = entry['depth_profile_m']
            p = sample_open([(y,0,0) for y in values],t*(len(values)-1))
            y = p.x+(anchor.y/scale-values[0])*(1-t)**2
            return Vector((x,y+entry.get('cross_depth_slope_m',0)*u,z)),Vector((0,1,0))
        if part=='tail':
            # A compact designed fan extends beside the coarse tail envelope.
            # Preserve X/Z lattice rather than clamp several tips to one ray hit.
            knots = cfg['tail_back_profile_z_y_m']
            k = next((i for i in range(len(knots)-1) if z<=knots[i+1][0]),len(knots)-2)
            q = min(1,max(0,(z-knots[k][0])/(knots[k+1][0]-knots[k][0])))
            y = knots[k][1]*(1-q)+knots[k+1][1]*q+entry.get('depth_offset_m',0)
            root_z = a.y
            k0 = next((i for i in range(len(knots)-1) if root_z<=knots[i+1][0]),len(knots)-2)
            q0 = min(1,max(0,(root_z-knots[k0][0])/(knots[k0+1][0]-knots[k0][0])))
            root_y = knots[k0][1]*(1-q0)+knots[k0+1][1]*q0+entry.get('depth_offset_m',0)
            y += (anchor.y/scale-root_y)*(1-t)**2
            return Vector((x,y,z)),Vector((0,-1,0))
        p = Vector((x*scale,(.35 if front else -.35)*scale,z*scale))
        hit,n,_,_ = tree.ray_cast(p,Vector((0,-1 if front else 1,0)),.8*scale)
        if hit is None:
            hit,n,_,distance = tree.find_nearest(Vector((x*scale,0,z*scale)))
            if distance > .014*scale:
                raise AssertionError((name,'outside support',x,z,distance))
        if n.y*(1 if front else -1) < 0:
            n = -n
        return hit/scale+n*entry.get('depth_offset_m',0)*math.sin(math.pi*t),n.normalized()
    obj = finish_leaf(name,*lattice(cfg,scale,surface),cfg,scale,material,part)
    if part=='tail':
        obj['root_support'] = 'FTH_TailPrimary'
    elif part!='face':
        obj['root_support'] = 'PRI_HeadNeckTorso'
    else:
        # Resolve the concrete accepted surface providing the combined ray seat.
        candidates = ('FAC_Mask_R','FAC_MaskBridge','PRI_HeadNeckTorso')
        obj['root_support'] = min(candidates,key=lambda n:source_tree(bpy.data.objects[n])[0].find_nearest(anchor)[3])
    return obj


def reflect_leaf(obj,new_name):
    bpy.context.view_layer.update()
    points = [obj.matrix_world@v.co for v in obj.data.vertices]
    other = mesh(new_name,[(-v.x,v.y,v.z) for v in points],
                 [tuple(reversed(p.vertices)) for p in obj.data.polygons],
                 'FEATHERS',obj.data.materials[0])
    for key in obj.keys():
        other[key] = obj[key]
    if other.get('root_support')=='FAC_Mask_R':
        other['root_support'] = 'FAC_Mask_L'
    other['symmetric_pair'] = obj.name
    obj['symmetric_pair'] = other.name
    return other


def primary(root,key,name,group,material,scale,sign=1):
    if sign==-1:
        out = reflect_leaf(bpy.data.objects[name[:-1]+'R'],name)
        for col in list(out.users_collection):
            col.objects.unlink(out)
        bpy.data.collections[group].objects.link(out)
        return out
    coarse,_ = parameters(root)
    guide = loft('_FTH_SOURCE_'+name,coarse[key],scale,group,material,sign)
    bpy.context.view_layer.update()
    source = source_tree(guide)
    out = sampled_loft(name,[source],lambda z:slice_center([source],z),
                       heights_for(source[1],source[2],.004*scale),32,0,material)
    for col in list(out.users_collection):
        col.objects.unlink(out)
    bpy.data.collections[group].objects.link(out)
    out['status'] = 'editable_quad_primary_goal_6'
    clean('_FTH_SOURCE_')
    return out


def set_gesture(root,left=0,right=0):
    _,cfg,scale = config(root)
    if not all(0 <= value <= 1 for value in (left,right)):
        raise ValueError('Gesture values must be in [0,1]')
    for side,sign,value in (('L',-1,left),('R',1,right)):
        pivot = bpy.data.objects['FTH_WingRoot_'+side]
        angle = -sign*math.radians(cfg['gesture_limit_degrees'])*value
        for obj in pivot.children:
            rest = obj.data.attributes['fth_rest']
            weights = obj.vertex_groups['wing_gesture']
            for v,p in zip(obj.data.vertices,rest.data):
                v.co = p.vector if value==0 else Matrix.Rotation(angle*weights.weight(v.index),3,'Y')@p.vector
            obj.data.update()
        pivot['gesture_probe_value'] = float(value)
    bpy.context.view_layer.update()


def bind_wing(obj,pivot,center,scale):
    obj.parent = pivot
    obj.matrix_parent_inverse.identity()
    obj.location = (0,0,0)
    weights = obj.vertex_groups.new(name='wing_gesture')
    for v in obj.data.vertices:
        weight = 1-smoothstep(.290*scale,.335*scale,v.co.z)
        weights.add([v.index],weight,'REPLACE')
        v.co -= center
    rest = obj.data.attributes.new('fth_rest',type='FLOAT_VECTOR',domain='POINT')
    for item,v in zip(rest.data,obj.data.vertices):
        item.vector = v.co
    obj['binding'] = 'wing root parent + shared nonlinear deformation from fth_rest/wing_gesture'


def build(root):
    coarse,cfg,scale = config(root)
    if 'PRI_HeadNeckTorso' not in bpy.data.objects or 'BAK_Upper' not in bpy.data.objects:
        raise RuntimeError('Feathers require primary, face and beak geometry')
    clean(('FTH_','_FTH_SOURCE_'))
    colors = {c:swatch(root,c) for c in ('deep_navy','mid_blue','cyan_reference','cream','orange_reference')}
    body_tree = source_tree(bpy.data.objects['PRI_HeadNeckTorso'])[0]
    tail = primary(root,'tail','FTH_TailPrimary','FEATHERS',colors['deep_navy'],scale)
    tail_tree = source_tree(tail)[0]
    for side,sign in (('R',1),('L',-1)):
        wing = primary(root,'wing','FTH_WingPrimary_'+side,'WINGS',colors['deep_navy'],scale,sign)
        wing_source = source_tree(wing)
        tree = wing_source[0]
        section_centers = {}
        leaves,index = [],0
        for layer in cfg['wing_layers']:
            for column,phi in enumerate(layer['centers']):
                if side=='L':
                    obj = reflect_leaf(bpy.data.objects[f'FTH_Wing_{layer["id"]}_{column}_R'],
                                       f'FTH_Wing_{layer["id"]}_{column}_L')
                    leaves.append(obj)
                    index += 1
                    continue
                def surface(t,u,phi=phi,layer=layer):
                    z = layer['root_z']*(1-t)+layer['tip_z']*t
                    angle = phi+layer['sweep_radians']*t+u*layer['angular_width']
                    if z not in section_centers:
                        section_centers[z] = slice_center([wing_source],z*scale)
                    center = Vector((*section_centers[z],z*scale))
                    d = Vector((sign*math.cos(angle),math.sin(angle),0))
                    hit,n,_,_ = tree.ray_cast(center+d*.25*scale,-d,.5*scale)
                    if hit is None:
                        raise AssertionError(('wing has no support',side,z,angle))
                    # Constant-Z radial thickness follows the smooth authored
                    # angular field. Per-triangle cone normals kinked inward
                    # walls at narrow distal tips and produced real crossings.
                    return hit/scale,d.normalized()
                color = 'cyan_reference' if index in cfg['wing_accent_indices'] else layer['color']
                obj = finish_leaf(f'FTH_Wing_{layer["id"]}_{column}_{side}',*lattice(cfg,scale,surface),
                                  cfg,scale,colors[color],'wing')
                leaves.append(obj)
                index += 1
        center = Vector((sign*cfg['wing_root_R_m'][0],*cfg['wing_root_R_m'][1:]))*scale
        pivot = bpy.data.objects.new('FTH_WingRoot_'+side,None)
        bpy.data.collections['WINGS'].objects.link(pivot)
        pivot.location = center
        pivot['status'] = 'geometry probe attachment; final controls #23'
        for obj in [wing]+leaves:
            bind_wing(obj,pivot,center,scale)
    for key,front,part in (('back_layers',False,'body_back'),('chest_layers',True,'body_chest')):
        for entry in cfg[key]:
            name = 'FTH_'+entry['id']+'_R'
            obj = project_leaf(name,entry,body_tree,cfg,scale,front,colors[entry['color']],part)
            reflect_leaf(obj,name[:-1]+'L')
    for entry in cfg['central_layers']:
        project_leaf('FTH_'+entry['id'],entry,body_tree,cfg,scale,entry['front'],
                     colors[entry['color']],'body_chest' if entry['front'] else 'body_back')
    for entry in cfg['tail_layers']:
        suffix = '' if entry['id']=='Center' else '_R'
        obj = project_leaf('FTH_Tail'+entry['id']+suffix,entry,tail_tree,cfg,scale,False,
                           colors[entry['color']],'tail')
        if suffix:
            reflect_leaf(obj,obj.name[:-1]+'L')
    from mathutils.bvhtree import BVHTree
    vertices,polygons = [],[]
    for name in ('FAC_Mask_R','FAC_MaskBridge','PRI_HeadNeckTorso'):
        owner = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        data = owner.to_mesh()
        start = len(vertices)
        vertices.extend(owner.matrix_world@v.co for v in data.vertices)
        polygons.extend(tuple(i+start for i in p.vertices) for p in data.polygons)
        owner.to_mesh_clear()
    face_tree = BVHTree.FromPolygons(vertices,polygons)
    for entry in cfg['face_layers']:
        obj = project_leaf('FTH_Face'+entry['id']+'_R',entry,face_tree,cfg,scale,True,colors['cream'],'face')
        reflect_leaf(obj,obj.name[:-1]+'L')
    clean(REMOVED)
    bpy.context.scene['feathers_parameters'] = 'design/wings_feathers.json'
    bpy.context.scene['feathers_scope'] = '#6 wing/body/tail/face; diagnostic colors; final rig deferred'
    set_gesture(root,0,0)
    return {o.name for o in bpy.data.objects if o.name.startswith('FTH_')}
