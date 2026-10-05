"""Quad primary surfaces sampled from the approved coarse envelope, not a remesh."""
import json
import math
import hashlib
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from blockout_geometry import loft, mesh, ellipsoid, swatch, clean, parameters


def smoothstep(a, b, x):
    t = min(1, max(0, (x-a)/(b-a)))
    return t*t*(3-2*t)


def source_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    verts = [obj.matrix_world @ v.co for v in data.vertices]
    tree = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in data.polygons], all_triangles=False)
    low, high = min(v.z for v in verts), max(v.z for v in verts)
    triangles = [[verts[i].copy() for i in tri.vertices] for tri in data.loop_triangles]
    if not triangles:
        data.calc_loop_triangles()
        triangles = [[verts[i].copy() for i in tri.vertices] for tri in data.loop_triangles]
    evaluated.to_mesh_clear()
    return tree, low, high, triangles


def slice_center(sources, z):
    sections = []
    for _,low,high,triangles in sources:
        if not low <= z <= high:
            continue
        points = []
        for triangle in triangles:
            for a,b in zip(triangle, triangle[1:]+triangle[:1]):
                if min(a.z,b.z) <= z <= max(a.z,b.z) and abs(a.z-b.z) > 1e-10:
                    points.append(a.lerp(b, (z-a.z)/(b.z-a.z)))
        if points:
            xmin,xmax = min(p.x for p in points),max(p.x for p in points)
            ymin,ymax = min(p.y for p in points),max(p.y for p in points)
            sections.append((xmax-xmin, ((xmin+xmax)/2,(ymin+ymax)/2)))
    return max(sections, key=lambda p:p[0])[1]


def disk_cap(vertices, faces, ring, top):
    """Concentric square-to-disk map: perimeter reuses the loft ring exactly."""
    count, center = len(ring), sum((Vector(vertices[i]) for i in ring), Vector()) / len(ring)
    n, indices = count//4, {}
    for iy in range(n+1):
        for ix in range(n+1):
            x, y = 2*ix/n-1, 2*iy/n-1
            if x == y == 0:
                radius, angle = 0, 0
            elif abs(x) >= abs(y):
                radius, angle = x, math.pi/4*y/x
            else:
                radius, angle = y, math.pi/2-math.pi/4*x/y
            if radius < 0:
                radius, angle = -radius, angle+math.pi
            j = round(angle/math.tau*count) % count
            if ix in (0, n) or iy in (0, n):
                index = ring[j]
            else:
                f = (angle/math.tau*count) % count
                k = int(f)
                edge = Vector(vertices[ring[k]]).lerp(Vector(vertices[ring[(k+1)%count]]), f-k)
                index = len(vertices)
                vertices.append(tuple(center.lerp(edge, radius)))
            indices[ix, iy] = index
    for iy in range(n):
        for ix in range(n):
            face = (indices[ix,iy], indices[ix+1,iy], indices[ix+1,iy+1], indices[ix,iy+1])
            faces.append(face if top else tuple(reversed(face)))


def sampled_loft(name, sources, center_at, heights, count, blend, material, symmetric=False):
    vertices, faces = [], []
    for z in heights:
        center = Vector((*center_at(z), z))
        for j in range(count):
            direction = Vector((math.cos(j*math.tau/count), math.sin(j*math.tau/count), 0))
            hits = []
            for tree, low, high, _ in sources:
                if low-1e-7 <= z <= high+1e-7:
                    hit = tree.ray_cast(center+direction, -direction, 2)[0]
                    if hit is not None:
                        hits.append((hit-center).dot(direction))
            if not hits:
                raise RuntimeError(f'No approved envelope at {name} z={z}')
            radius = max(hits)
            if len(hits) == 2 and blend:
                h = max(blend-abs(hits[0]-hits[1]), 0)/blend
                radius += h*h*blend/4
            vertices.append(tuple(center+direction*radius))
    if symmetric:
        for k in range(len(heights)):
            for j in range(count):
                a,b=k*count+j,k*count+(count//2-j)%count
                if a>b: continue
                p,q=Vector(vertices[a]),Vector(vertices[b])
                p=Vector(((p.x-q.x)/2,(p.y+q.y)/2,(p.z+q.z)/2))
                vertices[a],vertices[b]=tuple(p),(-p.x,p.y,p.z)
    for k in range(len(heights)-1):
        for j in range(count):
            a, b = k*count+j, k*count+(j+1)%count
            faces.append((a, b, b+count, a+count))
    disk_cap(vertices, faces, list(range(count)), False)
    disk_cap(vertices, faces, list(range((len(heights)-1)*count, len(heights)*count)), True)
    obj = mesh(name, vertices, faces, 'PRIMARY_FORM', material)
    obj['status'] = 'editable_primary_topology_goal_15'
    obj['construction'] = 'continuous quad loft with distributed quad caps; no internal caps'
    return obj


def heights_for(low, high, step, dense_band=None, dense_step=None):
    # Avoid microscopic sliver quads at rounded extrema; cap inset scales with the model.
    epsilon=step*.025
    result = [low+epsilon]
    z = result[0]
    while z < high-epsilon:
        z += dense_step if dense_band and dense_band[0] <= z <= dense_band[1] else step
        if z < high-epsilon:
            result.append(z)
    result.append(high-epsilon)
    # Support the rounded extrema instead of letting subdivision pull a large first ring inward.
    result.extend(low+step*f for f in (.125,.25,.5,.75) if low+step*f<high-epsilon)
    result.extend(high-step*f for f in (.125,.25,.5,.75) if high-step*f>low+epsilon)
    return sorted(set(result))


def build(root):
    root = Path(root)
    cfg, target_scale = parameters(root)
    # Sampling/tessellation always occurs at reference scale. Scale the completed cage once,
    # so BVH float precision cannot change topology or shape when the character is resized.
    scale=1.0
    policy = json.loads((root/'design/head_body.json').read_text())
    freeze = json.loads((root/'design/silhouette_freeze.json').read_text())
    if freeze['status'] != 'silhouette_frozen' or freeze['blocking_findings']:
        raise RuntimeError('Stage #15 requires the explicit #14 silhouette freeze')
    expected=freeze['evidence_sha256']['design/proportions.json']
    if hashlib.sha256((root/'design/proportions.json').read_bytes()).hexdigest()!=expected:
        raise RuntimeError('Coarse dimensions changed since #14: repeat the documented silhouette review')
    clean(('PRI_', '_PRI_SOURCE_'))
    navy, blue = swatch(root, 'deep_navy'), swatch(root, 'mid_blue')
    sources = []
    for key in ('body', 'head'):
        obj = loft('_PRI_SOURCE_'+key, cfg[key], scale, 'PRIMARY_FORM', navy)
        bpy.context.view_layer.update()
        sources.append(source_tree(obj))
    low, high = sources[0][1], sources[1][2]
    band = [v*scale for v in policy['neck_band_m']]
    shell = sampled_loft('PRI_HeadNeckTorso', sources, lambda z: slice_center(sources,z),
        heights_for(low, high, policy['body_step_m']*scale, band, policy['neck_step_m']*scale),
        policy['angular_segments'], policy['envelope_blend_m']*scale, blue, symmetric=True)
    shell.data.materials.append(navy)
    for poly in shell.data.polygons:
        poly.material_index = int(poly.center.z >= .326*scale)
    groups = {key: shell.vertex_groups.new(name=key) for key in ('body', 'head_neck', 'wing_root_L', 'wing_root_R')}
    a,b = [v*scale for v in policy['head_weight_band_m']]
    for vertex in shell.data.vertices:
        head = smoothstep(a,b,vertex.co.z)
        groups['body'].add([vertex.index], 1-head, 'REPLACE')
        groups['head_neck'].add([vertex.index], head, 'REPLACE')
        for side, point in zip(('L','R'), policy['wing_root_centers_m']):
            distance = (vertex.co-Vector(point)*scale).length
            weight = 1-smoothstep(0, policy['wing_root_radius_m']*scale, distance)
            groups['wing_root_'+side].add([vertex.index], weight, 'REPLACE')
    shell['neck_pivot_m'] = json.dumps([v*target_scale for v in policy['neck_pivot_m']])
    shell['weights_note'] = 'body/head_neck partition; wing_root groups are independent future attachment masks'
    for side, sign in (('L', -1), ('R', 1)):
        rings = cfg['tuft']
        obj = loft('_PRI_SOURCE_tuft', rings, scale, 'PRIMARY_FORM', navy, sign)
        bpy.context.view_layer.update()
        source = source_tree(obj)
        def center_at(z):
            return slice_center([source],z)
        if side=='L':
            sampled_loft('PRI_Tuft_'+side, [source], center_at,
                         heights_for(source[1], source[2], .004*scale), 32, 0, navy)
        else:
            left=bpy.data.objects['PRI_Tuft_L'].data
            out=mesh('PRI_Tuft_R',[(-v.co.x,v.co.y,v.co.z) for v in left.vertices],
                     [tuple(reversed(p.vertices)) for p in left.polygons],'PRIMARY_FORM',navy)
            out['status']='editable_primary_topology_goal_15'
        clean('_PRI_SOURCE_tuft')
        p = cfg['brow']
        brow = ellipsoid('_PRI_SOURCE_brow', [sign*p['center'][0], *p['center'][1:]],
                         p['dimensions'], scale, 'PRIMARY_FORM', navy)
        brow.rotation_euler.y = sign*p['tilt_y']
        bpy.context.view_layer.update()
        verts = [tuple(v.co) for v in brow.data.vertices][1:-1]
        faces = []
        for k in range(14):
            for j in range(32):
                a, b = k*32+j, k*32+(j+1)%32
                faces.append((a,b,b+32,a+32))
        disk_cap(verts, faces, list(range(32)), False)
        disk_cap(verts, faces, list(range(14*32,15*32)), True)
        out = mesh('PRI_Brow_'+side, verts, faces, 'PRIMARY_FORM', navy)
        out.matrix_world = brow.matrix_world.copy()
        for v in out.data.vertices:
            v.co = out.matrix_world @ v.co
        out.matrix_world.identity()
        out['status'] = 'editable_primary_topology_goal_15'
    clean('_PRI_SOURCE_')
    clean(('BLK_Head','BLK_Body','BLK_Tuft_','BLK_Brow_'))
    for obj in bpy.data.collections['PRIMARY_FORM'].objects:
        if obj.name.startswith('PRI_'):
            for v in obj.data.vertices:
                v.co*=target_scale
            obj.data.update()
            sub = obj.modifiers.new('Editable surface smoothing', 'SUBSURF')
            sub.levels = sub.render_levels = policy['subdivision_levels']
            obj['parameter_source'] = 'design/head_body.json + frozen design/proportions.json'
    bpy.context.scene['primary_topology_parameters'] = 'design/head_body.json'
    bpy.context.scene['primary_topology_scope'] = 'head/neck/torso and coarse brow/tufts; #15'
    bpy.context.view_layer.update()
    return shell
