"""Inspect foot surfaces and contact against the actual faceted perch, not names."""
import bpy
from mathutils import Vector
from feet_geometry import config
from verify_face import audit
from primary_geometry import source_tree


def triangle_inside_bar(points,planes,tolerance):
    """Clip a triangle against the actual bar's convex straight-section interior."""
    polygon = list(points)
    for normal,bound in planes:
        bound -= tolerance
        distances = [normal.dot(p)-bound for p in polygon]
        if all(d>=0 for d in distances): return False
        clipped = []
        for i,a in enumerate(polygon):
            b = polygon[(i+1)%len(polygon)]
            da,db = distances[i],distances[(i+1)%len(polygon)]
            if da<=0: clipped.append(a)
            if (da<0<db) or (db<0<da): clipped.append(a.lerp(b,da/(da-db)))
        polygon = clipped
        if not polygon: return False
    return bool(polygon)


def inspect(root):
    coarse,cfg,scale = config(root)
    bar = bpy.data.objects['GRP_PerchBar']
    tree = source_tree(bar)[0]
    center = Vector(coarse['perch']['bar']['center'])*scale
    # Polygon half-spaces describe the actual straight bar, including chord faces.
    n = cfg['bar_radial_segments']
    radius=coarse['perch']['bar']['radius']*scale
    planes = []
    bar_points = [bar.matrix_world@v.co for v in bar.data.vertices]
    for face in bar.data.polygons:
        points = [bar_points[i] for i in face.vertices]
        if max(p.x for p in points)-min(p.x for p in points)>.30*scale:
            normal = face.normal.copy()
            assert abs(normal.x)<1e-6
            planes.append((normal,normal.dot(points[0])))
    assert len(planes)==n,'Actual bar straight section must have the documented radial tessellation'
    result = {'surfaces':{}, 'contacts':{}, 'toe_branches':{}, 'penetration_tolerance_m':2e-7*scale}
    for obj in bpy.data.objects:
        if not obj.name.startswith('GRP_'): continue
        result['surfaces'][obj.name] = audit(obj)
        assert all(len(p.vertices)==4 for p in obj.data.polygons),obj.name+': nonquad surface'
        if obj.name.startswith('GRP_Perch'): continue
        obj.data.calc_loop_triangles()
        points = [obj.matrix_world@v.co for v in obj.data.vertices]
        samples = list(points)
        # Interior triangle samples catch crossings missed by vertex-only checks.
        for tri in obj.data.loop_triangles:
            a,b,c = [points[i] for i in tri.vertices]
            samples.extend(((a+b+c)/3,(a+b)/2,(b+c)/2,(c+a)/2))
        outside = [max(normal.dot(p)-bound for normal,bound in planes) for p in samples]
        assert min(outside)>=-2e-7*scale,(obj.name,'perch penetration',min(outside))
        assert all(abs(p.x-center.x)<.17*scale for p in points),'Foot contact outside straight bar section'
        for tri in obj.data.loop_triangles:
            assert not triangle_inside_bar([points[i] for i in tri.vertices],planes,2e-7*scale),(obj.name,'triangle penetrates actual perch',tri.index)
        if obj.name.startswith('GRP_Claw'):
            distance = min(tree.find_nearest(p)[3] for p in points)
            assert distance<2e-7*scale,(obj.name,'floating claw',distance)
            rear = obj['anatomical_branch']=='Rear_1'
            assert all((p.y-center.y)*(-1 if rear else 1)>0 for p in points),(obj.name,'wrong side of perch')
            assert min(p.z for p in points)<center.z-.012*scale,(obj.name,'claw does not wrap below bar')
            result['contacts'][obj.name] = {'nearest_surface_distance_m':distance,'minimum_polygon_halfspace_distance_m':min(outside),'rear':rear}
        if obj.name.startswith('GRP_Foot'):
            support=[p for p in points if abs(p.y-center.y)<1e-7*scale and abs(p.z-center.z-radius)<2e-7*scale]
            assert support,(obj.name,'pad floats above bar crown')
            expected = {'toe_Front_1','toe_Front_2','toe_Front_3','toe_Rear_1'}
            assert {g.name for g in obj.vertex_groups}==expected
            branches = {}
            for group in obj.vertex_groups:
                indices = {v.index for v in obj.data.vertices if any(g.group==group.index and g.weight>.99 for g in v.groups)}
                # Inspect real mesh adjacency within each anatomical branch.
                adjacency = {i:set() for i in indices}
                for edge in obj.data.edges:
                    a,b = edge.vertices
                    if a in indices and b in indices:
                        adjacency[a].add(b); adjacency[b].add(a)
                visited,queue = set(),[next(iter(indices))]
                while queue:
                    i = queue.pop()
                    if i in visited: continue
                    visited.add(i); queue.extend(adjacency[i]-visited)
                assert visited==indices,(obj.name,group.name,'disconnected toe branch')
                rear = group.name=='toe_Rear_1'
                branch_points = [points[i] for i in indices]
                assert all((p.y-center.y)*(-1 if rear else 1)>0 for p in branch_points)
                distance = min(tree.find_nearest(p)[3] for p in branch_points)
                assert distance<2e-7*scale,(obj.name,group.name,'floating toe',distance)
                assert min(p.z for p in branch_points)<center.z-.003*scale
                branches[group.name] = {'vertices':len(indices),'connected':True,'nearest_surface_distance_m':distance}
            result['toe_branches'][obj.name] = branches
            result.setdefault('pad_support_contact_m',{})[obj.name]=[list(p) for p in support]
    assert len(result['contacts'])==8 and len(result['toe_branches'])==2
    feet=[bpy.data.objects['GRP_Foot_'+side] for side in ('L','R')]
    claws=[bpy.data.objects[name] for name in result['contacts']]
    trees={o.name:source_tree(o)[0] for o in feet+claws}
    pairs=0
    for i,a in enumerate(claws):
        for b in claws[i+1:]:
            assert not trees[a.name].overlap(trees[b.name]),(a.name,b.name,'claw collision')
            pairs+=1
        for foot in feet:
            # Only matching terminal caps and their shared boundary may touch.
            def key(p):return tuple(round(v/(1e-7*scale)) for v in p)
            a_points=[key(a.matrix_world@v.co) for v in a.data.vertices]
            b_points=[key(foot.matrix_world@v.co) for v in foot.data.vertices]
            shared=set(a_points)&set(b_points)
            same_side=a.name.split('_')[2]==foot.name.split('_')[2]
            if same_side:assert len(shared)>=25,(a.name,'claw detached from toe cap')
            for ai,bi in trees[a.name].overlap(trees[foot.name]):
                assert same_side and any(a_points[v] in shared for v in a.data.polygons[ai].vertices) and any(b_points[v] in shared for v in foot.data.polygons[bi].vertices),(a.name,foot.name,'collision beyond shared terminal cap')
            pairs+=1
    assert not trees[feet[0].name].overlap(trees[feet[1].name]),'Feet collide'
    result['independent_surface_collision_pairs']=pairs+1
    return result
