"""Connected branching foot skins and opposing, separately editable hooked claws."""
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from blockout_geometry import parameters, clean, mesh, swatch
from primary_geometry import disk_cap


def config(root):
    coarse,scale = parameters(root)
    cfg = json.loads((Path(root)/'design/feet.json').read_text())
    for key in ('bar_radius','foot_half_spacing'):
        low,high = cfg[key+'_allowed_m']
        assert low<=cfg[key+'_m']<=high, 'Foot/perch adjustment outside documented range: '+key
    coarse['perch']['bar']['radius'] = cfg['bar_radius_m']
    coarse['feet']['half_spacing'] = cfg['foot_half_spacing_m']
    cfg['pad_center_z_m'] += cfg['bar_radius_m']-cfg['reference_bar_radius_m']
    return coarse,cfg,scale


def join_rings(faces, a, b):
    for j in range(len(a)):
        k = (j+1) % len(a)
        faces.append((a[j], a[k], b[k], b[j]))


def finish(name, vertices, faces, material, scale, collection='FEET'):
    # Compact unused points inside removed pad ports. Preserve deterministic order.
    used = sorted({i for f in faces for i in f})
    remap = {v: i for i, v in enumerate(used)}
    obj = mesh(name, [tuple(Vector(vertices[i])*scale) for i in used],
               [tuple(remap[i] for i in f) for f in faces], collection, material)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj['status'] = 'editable_connected_feet_goal_5'
    return obj, remap


def pad(cfg, x):
    """Cube-to-ellipsoid quad surface with four toe ports and one ankle port."""
    n, h = cfg['pad_grid_cells'], cfg['port_cells']//2
    vertices, faces, index, ports = [], [], {}, {}
    radii = Vector(cfg['pad_radii_m'])
    center = Vector((x, 0, cfg['pad_center_z_m']))

    def point(key):
        if key not in index:
            q = Vector(tuple(2*v/n-1 for v in key)).normalized()
            index[key] = len(vertices)
            vertices.append(tuple(center+Vector(tuple(q[i]*radii[i] for i in range(3)))))
        return index[key]

    for axis in range(3):
        other = [i for i in range(3) if i != axis]
        for fixed in (0, n):
            holes = []
            if axis == 1:
                holes = [(f'Front_{k}', column, n//2) for k, column in enumerate(cfg['front_port_columns'], 1)] if fixed == n else [('Rear_1', n//2, n//2)]
            if axis == 2 and fixed == n:
                holes = [('Ankle', n//2, n//2)]
            def key(u, v):
                result = [0, 0, 0]
                result[axis], result[other[0]], result[other[1]] = fixed, u, v
                return tuple(result)
            for u in range(n):
                for v in range(n):
                    if any(cu-h <= u < cu+h and cv-h <= v < cv+h for _, cu, cv in holes):
                        continue
                    faces.append(tuple(point(key(a, b)) for a, b in ((u,v),(u+1,v),(u+1,v+1),(u,v+1))))
            for name, cu, cv in holes:
                boundary = [(u,v) for u in range(cu-h,cu+h+1) for v in range(cv-h,cv+h+1)
                            if u in (cu-h,cu+h) or v in (cv-h,cv+h)]
                boundary.sort(key=lambda p: math.atan2(p[1]-cv,p[0]-cu))
                first = boundary.index((cu-h,cv))
                boundary = boundary[first:]+boundary[:first]
                ports[name] = [point(key(u,v)) for u,v in boundary]
    return vertices, faces, ports


def contact_ring(vertices, x, theta, radius, bar, count=16):
    center = Vector((x, bar['center'][1]+(bar['radius']+radius)*math.sin(theta),
                     bar['center'][2]+(bar['radius']+radius)*math.cos(theta)))
    radial = Vector((0,math.sin(theta),math.cos(theta)))
    indices = []
    for j in range(count):
        phi = -math.pi+math.tau*j/count
        indices.append(len(vertices))
        vertices.append(tuple(center+Vector((math.cos(phi)*radius,0,0))+radial*(math.sin(phi)*radius)))
    return indices


def rounded_perch(name, part, cfg, material, scale):
    """Quad cylinder with rounded ends and unchanged frozen outer dimensions."""
    count = cfg['bar_radial_segments']
    radius, half = part['radius'], part['length']/2
    bevel = min(cfg['bar_end_rounding_m'], radius/4, half/4)
    profile = []
    for k in range(5):
        angle = math.pi/2*k/4
        profile.append((-half+bevel-bevel*math.cos(angle),radius-bevel+bevel*math.sin(angle)))
    profile.extend((-a,r) for a,r in reversed(profile))
    vertices, faces, previous = [], [], None
    for axial,r in profile:
        ring = []
        for j in range(count):
            theta = math.tau*j/count
            local = Vector((axial,r*math.sin(theta),r*math.cos(theta))) if part['axis']=='X' else Vector((r*math.cos(theta),r*math.sin(theta),axial))
            ring.append(len(vertices))
            vertices.append(tuple(local+Vector(part['center'])))
        if previous is None: disk_cap(vertices,faces,ring,False)
        else: join_rings(faces,previous,ring)
        previous = ring
    disk_cap(vertices,faces,previous,True)
    obj,_ = finish(name,vertices,faces,material,scale,'PERCH')
    obj['construction'] = 'rounded end profile, distributed quad end caps; frozen outer dimensions'
    return obj


def build(root):
    root = Path(root)
    coarse,cfg,scale = config(root)
    assert cfg['pad_grid_cells'] == 24 and cfg['port_cells'] == 4
    assert len(cfg['front_port_columns']) == 3
    bar = coarse['perch']['bar']
    assert bar['axis'] == 'X'
    clean(('GRP_', 'GUIDE_Foot', 'GUIDE_Leg', 'GUIDE_Toe', 'GUIDE_Claw', 'BLK_Perch'))
    orange, navy = swatch(root,'orange_reference'), swatch(root,'deep_navy')
    perch_material=bpy.data.materials.get('GRP_PerchDiagnostic') or bpy.data.materials.new('GRP_PerchDiagnostic')
    perch_material.use_nodes=True
    perch_material.diffuse_color=cfg['perch_diagnostic_linear_rgba']
    node=perch_material.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=cfg['perch_diagnostic_linear_rgba']
    node.inputs['Roughness'].default_value=.6
    node.inputs['Metallic'].default_value=0
    perch_material['status']='neutral inspection gray; brushed metal and cyan accents follow in #18'
    for kind,part in coarse['perch'].items():
        rounded_perch('GRP_Perch'+kind.title(),part,cfg,perch_material,scale)
    step = math.tau/cfg['bar_radial_segments']
    for side, sign in [('L',-1),('R',1)]:
        x = bar['center'][0]+sign*coarse['feet']['half_spacing']
        vertices, faces, ports = pad(cfg,x)
        branch_indices = {}
        for label in ['Front_1','Front_2','Front_3','Rear_1']:
            direction = 1 if label.startswith('Front') else -1
            offset = coarse['feet']['front_offsets'][int(label[-1])-1] if direction == 1 else 0
            old = ports[label]
            branch = list(old)
            for k in range(cfg['root_extension_steps']):
                ring = []
                for i in old:
                    ring.append(len(vertices))
                    vertices.append(tuple(Vector(vertices[i])+Vector((0,direction*cfg['root_extension_step_m'],0))))
                join_rings(faces,old,ring)
                old = ring
                branch.extend(ring)
            root_points = [Vector(vertices[i]) for i in old]
            start = len(vertices)
            target = contact_ring(vertices,x+offset,direction*step*cfg['contact_start_step'],cfg['toe_radius_root_m'],bar)
            target_points = [Vector(vertices[i]) for i in target]
            del vertices[start:]
            theta = step*cfg['contact_start_step']
            root_tangent = Vector((0,direction*cfg['root_tangent_length_m'],0))
            end_tangent = Vector((0,direction*math.cos(theta),-math.sin(theta)))*cfg['contact_tangent_length_m']
            root_center = sum(root_points,Vector())/len(root_points)
            target_center = sum(target_points,Vector())/len(target_points)
            for k in range(1,cfg['transition_rings']+1):
                t = k/cfg['transition_rings']
                ring = []
                center = root_center*(2*t**3-3*t*t+1)+root_tangent*(t**3-2*t*t+t)+target_center*(-2*t**3+3*t*t)+end_tangent*(t**3-t*t)
                derivative = root_center*(6*t*t-6*t)+root_tangent*(3*t*t-4*t+1)+target_center*(-6*t*t+6*t)+end_tangent*(3*t*t-2*t)
                normal = Vector((0,-direction*derivative.z,direction*derivative.y)).normalized()
                for j,a in enumerate(root_points):
                    ring.append(len(vertices))
                    phi = -math.pi+math.tau*j/len(root_points)
                    residual = a-root_center
                    width = residual.x*(1-t)+cfg['toe_radius_root_m']*math.cos(phi)*t
                    depth = residual.z*(1-t)+cfg['toe_radius_root_m']*math.sin(phi)*t
                    p = center+Vector((width,0,0))+normal*depth
                    vertices.append(tuple(p))
                join_rings(faces,old,ring)
                old = ring
                branch.extend(ring)
            for k in range(cfg['contact_start_step']+1,cfg['skin_end_step']+1):
                t = (k-cfg['contact_start_step'])/(cfg['skin_end_step']-cfg['contact_start_step'])
                radius = cfg['toe_radius_root_m']*(1-t)+cfg['toe_radius_end_m']*t
                splay = offset/coarse['feet']['front_offsets'][-1]*coarse['feet']['splay']*t if direction == 1 else 0
                ring = contact_ring(vertices,x+offset+splay,direction*step*k,radius,bar)
                join_rings(faces,old,ring)
                old = ring
                branch.extend(ring)
            disk_cap(vertices,faces,old,True)
            branch_indices[label] = branch
            claw_vertices, claw_faces, previous = [], [], None
            for k in range(cfg['skin_end_step'],cfg['claw_end_step']+1):
                t = (k-cfg['skin_end_step'])/(cfg['claw_end_step']-cfg['skin_end_step'])
                radius = cfg['toe_radius_end_m']*(1-t)+cfg['claw_tip_radius_m']*t
                ring = contact_ring(claw_vertices,x+offset+(splay if direction == 1 else 0),direction*step*k,radius,bar)
                if previous is None: disk_cap(claw_vertices,claw_faces,ring,False)
                else: join_rings(claw_faces,previous,ring)
                previous = ring
            disk_cap(claw_vertices,claw_faces,previous,True)
            claw,_ = finish(f'GRP_Claw_{side}_{label}',claw_vertices,claw_faces,navy,scale)
            claw['anatomical_branch'] = label
        old = ports['Ankle']
        points = [Vector(vertices[i]) for i in old]
        for k in range(1,9):
            t = k/8
            ring = []
            for j,a in enumerate(points):
                phi = -math.pi+math.tau*j/len(points)
                b = Vector((x+cfg['ankle_radii_m'][0]*math.cos(phi),
                            -.009+cfg['ankle_radii_m'][1]*math.sin(phi),cfg['ankle_top_z_m']))
                ring.append(len(vertices))
                vertices.append(tuple(a.lerp(b,t)))
            join_rings(faces,old,ring)
            old = ring
        disk_cap(vertices,faces,old,True)
        foot,remap = finish('GRP_Foot_'+side,vertices,faces,orange,scale)
        for label,indices in branch_indices.items():
            group = foot.vertex_groups.new(name='toe_'+label)
            group.add([remap[i] for i in indices],1,'REPLACE')
        foot['anatomy'] = '3 forward + 1 rear, connected through pad and ankle'
    bpy.context.view_layer.update()
