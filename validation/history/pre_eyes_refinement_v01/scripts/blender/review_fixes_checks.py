"""Targeted #37 surface/attachment QA, including adjacent triangle interiors."""
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from verify_face import audit, digest_part, exercise as face_exercise
from verify_beak import exercise as beak_exercise
from verify_feet import inspect as feet_inspect
from primary_geometry import source_tree
from review_fixes_geometry import CHANGED


def coplanar_overlap_area(first, second, normal):
    """Clip projected triangles; positive area is overlap, boundary contact is zero."""
    axis = max(range(3), key=lambda i:abs(normal[i]))
    axes = [i for i in range(3) if i != axis]
    first = [(p[axes[0]],p[axes[1]]) for p in first]
    second = [(p[axes[0]],p[axes[1]]) for p in second]
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if cross(*second) < 0:
        second.reverse()
    result = first
    for a,b in zip(second,second[1:]+second[:1]):
        previous = result
        result = []
        if not previous:
            return 0
        for start,end in zip(previous,previous[1:]+previous[:1]):
            ds,de = cross(a,b,start),cross(a,b,end)
            inside_start,inside_end = ds >= 0,de >= 0
            if inside_start != inside_end:
                t = ds/(ds-de)
                result.append((start[0]+(end[0]-start[0])*t,start[1]+(end[1]-start[1])*t))
            if inside_end:
                result.append(end)
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(result,result[1:]+result[:1])))*.5


def coplanar_interior_hits(points, triangles):
    """Spatial hash supplies coplanar candidates omitted by Blender's BVH."""
    grid, normals, hits = {}, [], []
    if not triangles:
        return hits,0
    extent = max(max(p[i] for p in points)-min(p[i] for p in points) for i in range(3))
    cell = max(extent/25, .0002)
    for index,ids in enumerate(triangles):
        coords = [points[i] for i in ids]
        normals.append((coords[1]-coords[0]).cross(coords[2]-coords[0]).normalized())
        low = [math.floor(min(p[i] for p in coords)/cell) for i in range(3)]
        high = [math.floor(max(p[i] for p in coords)/cell) for i in range(3)]
        for x in range(low[0],high[0]+1):
            for y in range(low[1],high[1]+1):
                for z in range(low[2],high[2]+1):
                    grid.setdefault((x,y,z),[]).append(index)
    seen,checks = set(),0
    for group in grid.values():
        for i,a in enumerate(group):
            for b in group[i+1:]:
                pair = (a,b) if a < b else (b,a)
                if pair in seen:
                    continue
                seen.add(pair)
                normal = normals[a]
                if abs(normal.dot(normals[b])) < 1-1e-6:
                    continue
                first,second = [[points[k] for k in triangles[index]] for index in (a,b)]
                if max(abs((p-first[0]).dot(normal)) for p in second) > 1e-8:
                    continue
                checks += 1
                if coplanar_overlap_area(first,second,normal) > 1e-12:
                    hits.append(pair)
    return hits,checks


def triangle_audit(obj, evaluated=False):
    """Inset triangle interiors by 1e-3 of their median to discard contact boundaries.

Unlike the v1 shared-vertex filter, this checks adjacent faces as well. It detects
positive-area folds/crossings, including coplanar overlaps. Features narrower than
the inset are a documented blind spot. Cage and evaluated surfaces are separate.
"""
    owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else obj
    data = owner.to_mesh() if evaluated else obj.data
    try:
        data.calc_loop_triangles()
        points, polys = [], []
        maximum_inset = 0
        triangles = list(data.loop_triangles)
        normals_by_face = {}
        for tri in triangles:
            coords = [obj.matrix_world @ data.vertices[i].co for i in tri.vertices]
            normal = (coords[1]-coords[0]).cross(coords[2]-coords[0])
            assert normal.length > 2e-12, (obj.name, tri.polygon_index, 'degenerate triangle')
            normals_by_face.setdefault(tri.polygon_index, []).append(normal.normalized())
            center = sum(coords, Vector()) / 3
            start = len(points)
            for p in coords:
                inset = p.lerp(center, 1e-3)
                maximum_inset = max(maximum_inset, (p-inset).length)
                points.append(inset)
            polys.append((start, start+1, start+2))
        min_dot = min((a.dot(b) for ns in normals_by_face.values() for i,a in enumerate(ns) for b in ns[i+1:]), default=1)
        assert min_dot > 0, (obj.name, 'folded polygon triangulation', min_dot)
        tree = BVHTree.FromPolygons(points, polys, all_triangles=True, epsilon=0)
        hits = [(a,b) for a,b in tree.overlap(tree) if a < b]
        assert not hits, (obj.name, 'triangle interior crossing (adjacency included)', hits[:8])
        coplanar,checks = coplanar_interior_hits(points,polys)
        assert not coplanar, (obj.name, 'coplanar triangle interior overlap', coplanar[:8])
        return dict(triangles=len(polys), adjacent_interiors_included=True,
                    interior_crossings=0, minimum_polygon_triangle_normal_dot=min_dot,
                    maximum_boundary_inset_m=maximum_inset,coplanar_candidate_checks=checks,
                    coplanar_overlap_area_tolerance_m2=1e-12,coplanar_plane_tolerance_m=1e-8)
    finally:
        if evaluated:
            owner.to_mesh_clear()


def inspect(root):
    result = {'changed_meshes': {}, 'geometry_sha256': {}, 'feet': feet_inspect(root), 'attachment_contacts': {}}
    for obj in sorted((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o:o.name):
        result['geometry_sha256'][obj.name] = digest_part(obj)
        if obj.name in CHANGED:
            result['changed_meshes'][obj.name] = dict(cage=audit(obj),
                cage_triangles=triangle_audit(obj), evaluated_triangles=triangle_audit(obj, True))
    head = source_tree(bpy.data.objects['PRI_HeadNeckTorso'])[0]
    for side in ('L','R'):
        obj = bpy.data.objects['FAC_Mask_'+side]
        count = 96
        # Outer front/back rows lie astride the unchanged head: deliberate rooted socket.
        n = len(obj.data.vertices)//2
        row = [obj.data.vertices[i].co for i in range(n-count,n)]
        distances = [head.find_nearest(p)[3] for p in row]
        assert max(distances) < .0012, (side, 'unattached mask border', max(distances))
        result['attachment_contacts']['mask_'+side] = dict(samples=count, max_root_distance_m=max(distances),
                policy='front skin offset 1mm, medial beak seat recessed; maximum root distance 1.2mm')
    return result


def exercise(root):
    return {'blink_and_gaze': face_exercise(root), 'beak_opening': beak_exercise(root)}
