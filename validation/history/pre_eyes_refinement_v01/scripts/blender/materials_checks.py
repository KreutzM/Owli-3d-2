"""Actual assigned shaders, preserved cages/eyes, seated tech and pose probes for #18."""
import hashlib
import json
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from materials_geometry import EYES,ROLES,config
from feathers_checks import inspect as feather_inspect,exercise as feather_exercise,inventory
from feathers_geometry import set_gesture
from face_geometry import set_blink
from beak_geometry import set_open
from primary_geometry import source_tree
from review_fixes_checks import triangle_audit


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def simple(value):
    if value is None or isinstance(value,(bool,int,float,str)):return value
    if isinstance(value,bpy.types.ID):return {'id_type':value.bl_rna.identifier,'name':value.name}
    try:return [simple(item) for item in value]
    except TypeError:return repr(value)


def properties(value):
    result={}
    for prop in value.bl_rna.properties:
        if prop.identifier in ('rna_type','node_tree','internal_links','inputs','outputs','users','session_uid','is_updated','is_updated_data','original','tag','is_runtime_data','is_embedded_data','is_evaluated'):continue
        if prop.type not in ('BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER'):continue
        try:result[prop.identifier]=simple(getattr(value,prop.identifier))
        except (AttributeError,TypeError,RuntimeError):pass
    return result


def mesh_geometry(obj):
    mesh=obj.data
    return {'matrix':[list(row) for row in obj.matrix_world],'parent':obj.parent.name if obj.parent else None,
        'parent_inverse':[list(row) for row in obj.matrix_parent_inverse],
        'vertices':[list(v.co) for v in mesh.vertices],'edges':[list(e.vertices) for e in mesh.edges],
        'faces':[list(p.vertices) for p in mesh.polygons],'smooth':[p.use_smooth for p in mesh.polygons],
        'groups':[[g.name,g.lock_weight] for g in obj.vertex_groups],
        'weights':[[[g.group,g.weight] for g in v.groups] for v in mesh.vertices],
        'modifiers':[properties(m) for m in obj.modifiers],'collections':sorted(c.name for c in obj.users_collection)}


def shape_hashes():
    return {o.name:digest(mesh_geometry(o)) for o in bpy.context.scene.objects if o.type=='MESH'}


def full_material(mat):
    result={'properties':properties(mat)}
    if mat.node_tree:
        nodes={}
        for node in mat.node_tree.nodes:
            nodes[node.name]={'properties':properties(node),'inputs':[],'outputs':[]}
            for kind in ('inputs','outputs'):
                for socket in getattr(node,kind):
                    nodes[node.name][kind].append({'name':socket.name,'identifier':socket.identifier,'type':socket.type,
                        'default':simple(getattr(socket,'default_value',None)),'hide':socket.hide,'enabled':socket.enabled})
            if node.type=='VALTORGB':
                nodes[node.name]['ramp']={'interpolation':node.color_ramp.interpolation,
                    'stops':[[e.position,list(e.color)] for e in node.color_ramp.elements]}
        result['nodes']=nodes
        result['links']=sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in mat.node_tree.links])
    return result


def eye_hashes():
    return {n:digest({'geometry':mesh_geometry(bpy.data.objects[n]),
        'material_slots':[m.name for m in bpy.data.objects[n].data.materials],
        'polygon_material_indices':[p.material_index for p in bpy.data.objects[n].data.polygons],
        'materials':{m.name:full_material(m) for m in bpy.data.objects[n].data.materials}}) for n in EYES}


def material_snapshot(mat):
    p=mat.node_tree.nodes['Surface']
    fields={'base_color':'Base Color','metallic':'Metallic','roughness':'Roughness','ior':'IOR',
        'coat_weight':'Coat Weight','coat_roughness':'Coat Roughness','anisotropic':'Anisotropic',
        'sheen_weight':'Sheen Weight','emission_color':'Emission Color','emission_strength':'Emission Strength'}
    return {'use_nodes':mat.use_nodes,'node_types':{n.name:n.bl_idname for n in mat.node_tree.nodes},
        'links':sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in mat.node_tree.links]),
        'principled_inputs':{k:simple(p.inputs[v].default_value) for k,v in fields.items()},
        'ramps':{n.name:{'interpolation':n.color_ramp.interpolation,'stops':[[e.position,list(e.color)] for e in n.color_ramp.elements]}
            for n in mat.node_tree.nodes if n.type=='VALTORGB'},'shader_sha256':digest(full_material(mat))}


def tech_audit(obj):
    bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    try:
        assert all(e.is_manifold and e.is_contiguous for e in bm.edges),(obj.name,'open/inconsistent')
        assert all(f.calc_area()>1e-12 for f in bm.faces),(obj.name,'degenerate')
        assert bm.calc_volume(signed=True)>0,(obj.name,'inward normals')
        seen=set();pending=[bm.verts[0]]
        while pending:
            v=pending.pop()
            if v.index in seen:continue
            seen.add(v.index);pending.extend(e.other_vert(v) for e in v.link_edges)
        assert len(seen)==len(bm.verts),(obj.name,'disconnected')
        kd=KDTree(len(bm.verts))
        for v in bm.verts:kd.insert(v.co,v.index)
        kd.balance()
        assert all(len(kd.find_range(v.co,1e-7))==1 for v in bm.verts),(obj.name,'duplicate')
        tree=BVHTree.FromBMesh(bm)
        hits=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)]
        assert not hits,(obj.name,'self intersections',hits[:3])
        euler=len(bm.verts)-len(bm.edges)+len(bm.faces)
        expected=0 if obj['geometry_kind']=='torus' else 2
        assert euler==expected,(obj.name,'topology',euler)
        return {'vertices':len(bm.verts),'polygons':len(bm.faces),'closed_connected':True,'outward_consistent_normals':True,
            'self_intersections':0,'duplicate_vertices':0,'euler_characteristic':euler,'volume_m3':bm.calc_volume(signed=True),
            'minimum_polygon_area_m2':min(f.calc_area() for f in bm.faces)}
    finally:bm.free()


def inspect(root):
    result=feather_inspect(root)
    cfg,_,scale=config(root)
    tech=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('TECH_'))
    expected={f'TECH_ForeheadNode_{n}' for n in cfg['forehead']['nodes']}|{f'TECH_ForeheadLink_{n}' for n in cfg['forehead']['links']}|{f'TECH_PerchRing_{e["id"]}' for e in cfg['perch_rings']}
    assert set(tech)==expected
    result['shape_sha256']=shape_hashes();result['eye_state_sha256']=eye_hashes()
    result['assignments']={}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':continue
        slots=[m.name if m else None for m in obj.data.materials]
        indices=[p.material_index for p in obj.data.polygons]
        bad=sum(i>=len(slots) or not slots[i] for i in indices)
        assert slots and not bad,(obj.name,'unassigned visible polygons')
        result['assignments'][obj.name]={'slots':slots,'polygon_material_indices':indices,'unassigned_polygons':bad}
    result['materials']={role:material_snapshot(bpy.data.materials['MAT_'+role]) for role in ROLES}
    result['tech_meshes']={};result['tech_seats']={}
    for name in tech:
        obj=bpy.data.objects[name]
        result['tech_meshes'][name]={'cage':tech_audit(obj),'cage_triangles':triangle_audit(obj),
            'evaluated_triangles':triangle_audit(obj,True),'kind':obj['geometry_kind'],'support':obj['root_support']}
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        if name.startswith('TECH_Forehead'):
            supports=[source_tree(bpy.data.objects[n])[0] for n in ('PRI_HeadNeckTorso','FAC_MaskBridge')]
            distances=[min(t.find_nearest(p)[3] for t in supports) for p in points]
            assert max(distances)<.004*scale,(name,'unseated motif',max(distances))
        else:
            t=source_tree(bpy.data.objects[obj['root_support']])[0]
            distances=[t.find_nearest(p)[3] for p in points]
            assert max(distances)<.0016*scale,(name,'perch accent unseated',max(distances))
        result['tech_seats'][name]={'support':obj['root_support'],'samples':len(points),'maximum_surface_distance_m':max(distances)}
    result['tech_symmetry']={}
    for name in ('TECH_ForeheadNode_Inner_R','TECH_ForeheadNode_Outer_R','TECH_ForeheadLink_Inner_R','TECH_ForeheadLink_Outer_R','TECH_PerchRing_End_R'):
        right=bpy.data.objects[name];left=bpy.data.objects[name[:-1]+'L']
        assert len(right.data.vertices)==len(left.data.vertices)
        kd=KDTree(len(left.data.vertices))
        for i,v in enumerate(left.data.vertices):kd.insert(left.matrix_world@v.co,i)
        kd.balance()
        distances=[]
        for v in right.data.vertices:
            p=right.matrix_world@v.co;distances.append(kd.find(Vector((-p.x,p.y,p.z)))[2])
        maximum=max(distances)
        assert maximum<2e-6*scale,(name,'asymmetric tech',maximum)
        result['tech_symmetry'][name]={'vertices':len(right.data.vertices),'maximum_mirror_deviation_m':maximum}
    result['counts']['tech_meshes']=len(tech)
    return result


def tech_function(root):
    targets={o.name:source_tree(o)[0] for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('TECH_')}
    result={'target_meshes':sorted(targets),'blink_samples':[i/40 for i in range(41)],'blink_collision_checks':0,
        'gaze_probes':[],'beak_samples':[i/40 for i in range(41)],'beak_collision_checks':0,'wing_states':[],'neutral_restored':False}
    before=shape_hashes()
    def against(obj):
        own=source_tree(obj)[0]
        for name,t in targets.items():assert not own.overlap(t),(obj.name,name,'function/tech collision')
        return len(targets)
    try:
        for value in result['blink_samples']:
            set_blink(root,value)
            for side in ('L','R'):
                for kind in ('Upper','Lower'):result['blink_collision_checks']+=against(bpy.data.objects[f'FAC_Lid_{kind}_{side}'])
        set_blink(root,0)
        for axis in (0,2):
            for degrees in (-12,12):
                for side in ('L','R'):bpy.data.objects['FAC_EyeAim_'+side].rotation_euler[axis]=math.radians(degrees)
                bpy.context.view_layer.update()
                checks=sum(against(bpy.data.objects[n]) for n in EYES)
                result['gaze_probes'].append({'axis':'X' if axis==0 else 'Z','degrees':degrees,'collision_checks':checks})
                for side in ('L','R'):bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
                bpy.context.view_layer.update()
        for value in result['beak_samples']:
            set_open(root,value)
            for kind in ('Upper','Lower'):result['beak_collision_checks']+=against(bpy.data.objects['BAK_'+kind])
        set_open(root,0)
        for left,right in ((.5,0),(1,0),(0,.5),(0,1),(.5,.5),(1,1)):
            set_gesture(root,left,right)
            checks=sum(against(bpy.data.objects[n]) for n in sorted(inventory()) if n.startswith('FTH_Wing'))
            result['wing_states'].append({'left':left,'right':right,'collision_checks':checks})
    finally:
        set_blink(root,0);set_open(root,0);set_gesture(root,0,0)
        for side in ('L','R'):bpy.data.objects['FAC_EyeAim_'+side].rotation_euler=(0,0,0)
        bpy.context.view_layer.update()
    assert before==shape_hashes(),'Tech probe neutral restoration drift'
    result['neutral_restored']=True
    return result


def exercise(root):
    result=feather_exercise(root);result['tech_function']=tech_function(root)
    return result
