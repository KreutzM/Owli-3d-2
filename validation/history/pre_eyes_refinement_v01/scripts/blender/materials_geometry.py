"""Assigned #18 lookdev, seated tech geometry and the authored F01 chest finish."""
import hashlib
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Matrix
from blockout_geometry import mesh,clean,parameters
from primary_geometry import source_tree
from feathers_geometry import config as feather_config,project_leaf,reflect_leaf

EYES = tuple(f'FAC_{p}_{s}' for p in ('Globe','Iris','Pupil','Cornea') for s in ('L','R'))
CHANGED = tuple(f'FTH_{p}_{s}' for p in ('CreamUpper','CreamMiddle','CreamLower','Orange') for s in ('L','R'))
REMOVED = tuple(f'BLK_ForeheadNode_{i}' for i in range(5))+tuple(f'BLK_ForeheadLink_{i}' for i in range(4))
ROLES = ('Feather_Navy','Feather_Blue','Feather_Cyan','Feather_Cream','Feather_Warm',
         'Keratin_Orange','Keratin_Dark','Mouth_Interior','Perch_Metal','Tech_Cyan')


def config(root):
    cfg=json.loads((Path(root)/'design/materials_lookdev.json').read_bytes())
    palette=json.loads((Path(root)/'design/materials.json').read_bytes())['sampled_logo_colors']
    _,scale=parameters(root)
    return cfg,palette,scale


def linear(hex_color):
    rgb=[int(hex_color[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1.0,)


def mix(a,b,value):
    return tuple(x*(1-value)+y*value for x,y in zip(a,b))


def shader(role,cfg,palette):
    mat=bpy.data.materials.get('MAT_'+role) or bpy.data.materials.new('MAT_'+role)
    mat.use_nodes=True
    tree=mat.node_tree;tree.nodes.clear()
    def node(kind,name):
        n=tree.nodes.new(kind);n.name=name;n.label=name;return n
    def wire(a,out,b,inp):tree.links.new(a.outputs[out],b.inputs[inp])
    out=node('ShaderNodeOutputMaterial','SurfaceOutput')
    p=node('ShaderNodeBsdfPrincipled','Surface')
    wire(p,'BSDF',out,'Surface')
    s=cfg['shader'];col={k:linear(v) for k,v in palette.items()}
    bases={'Feather_Navy':col['deep_navy'],'Feather_Blue':col['mid_blue'],
      'Feather_Cyan':col['cyan_reference'],'Feather_Cream':col['cream'],
      'Feather_Warm':col['orange_reference'],'Keratin_Orange':col['orange_reference'],
      'Keratin_Dark':linear(s['claw_srgb']),'Mouth_Interior':col['deep_navy'],
      'Perch_Metal':linear(s['perch_srgb']),'Tech_Cyan':linear(s['emission_srgb'])}
    base=bases[role];p.inputs['Base Color'].default_value=base;mat.diffuse_color=base
    rough=s['feather_roughness'] if role.startswith('Feather') else s['keratin_roughness']
    if role=='Feather_Cream':rough=s['cream_roughness']
    if role=='Mouth_Interior':rough=.6
    if role=='Perch_Metal':rough=s['perch_roughness']
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=s['perch_metallic'] if role=='Perch_Metal' else 0
    p.inputs['Sheen Weight'].default_value=s['sheen_weight'] if role.startswith('Feather') else 0
    p.inputs['Anisotropic'].default_value=s['perch_anisotropic'] if role=='Perch_Metal' else 0
    p.inputs['IOR'].default_value=1.45
    if role=='Tech_Cyan':
        p.inputs['Emission Color'].default_value=base
        p.inputs['Emission Strength'].default_value=s['emission_strength']
    else:
        tex=node('ShaderNodeTexCoord','Coordinates')
        mapping=node('ShaderNodeVectorMath','GrainDirection');mapping.operation='MULTIPLY'
        mapping.inputs[1].default_value=(180,2,1) if role!='Perch_Metal' else (2,200,200)
        wire(tex,'Generated',mapping,0)
        noise=node('ShaderNodeTexNoise','FineGrain');noise.inputs['Scale'].default_value=5
        noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.65
        wire(mapping,'Vector',noise,'Vector')
        bump=node('ShaderNodeBump','SurfaceGrain')
        bump.inputs['Strength'].default_value=s['grain_strength']
        bump.inputs['Distance'].default_value=s['grain_distance_m']
        wire(noise,'Fac',bump,'Height');wire(bump,'Normal',p,'Normal')
        if role.startswith('Feather'):
            uv=node('ShaderNodeUVMap','FeatherCoordinates');uv.uv_map='ldv_feather'
            sep=node('ShaderNodeSeparateXYZ','FeatherAxes');wire(uv,'UV',sep,'Vector')
            ramp=node('ShaderNodeValToRGB','FeatherGradient')
            tip=base
            if role=='Feather_Navy':tip=mix(base,col['mid_blue'],.5)
            if role=='Feather_Blue':tip=mix(base,col['cyan_reference'],.42)
            if role=='Feather_Cyan':tip=mix(base,linear('#7BDAEF'),.4)
            if role=='Feather_Cream':tip=mix(base,linear('#D7E8ED'),.2)
            ramp.color_ramp.elements[0].color=mix(base,col['deep_navy'],.14) if role!='Feather_Cream' else base
            ramp.color_ramp.elements[1].color=tip
            wire(sep,'Y',ramp,'Fac');wire(ramp,'Color',p,'Base Color')
            if role=='Feather_Warm':
                # U runs from the cream center toward the cool outer flank.
                ramp.color_ramp.elements[0].color=col['cream']
                ramp.color_ramp.elements[1].color=mix(col['mid_blue'],col['cyan_reference'],.35)
                band=node('ShaderNodeValToRGB','WarmDiagonal')
                cr=band.color_ramp;cr.interpolation='EASE'
                cr.elements[0].color=col['cream'];cr.elements[1].color=col['mid_blue']
                for pos,color in ((.25,col['cream']),(.35,linear('#FFD068')),(.5,col['orange_reference']),(.7,linear('#FFD068')),(.86,col['mid_blue'])):
                    cr.elements.new(pos).color=color
                wire(sep,'X',band,'Fac')
                fade=node('ShaderNodeValToRGB','WarmTaper')
                cr=fade.color_ramp;cr.elements[0].color=(0,0,0,1);cr.elements[1].color=(0,0,0,1)
                for pos,val in ((.18,.5),(.38,1),(.64,.85),(.88,.2)):
                    cr.elements.new(pos).color=(val,val,val,1)
                wire(sep,'Y',fade,'Fac')
                blend=node('ShaderNodeMixRGB','IntegratedWarmAccent');blend.blend_type='MIX'
                wire(fade,'Color',blend,0);wire(ramp,'Color',blend,1);wire(band,'Color',blend,2)
                wire(blend,'Color',p,'Base Color')
    mat['surface_role']=role;mat['palette_space']='linear from documented sRGB';mat['parameter_source']='design/materials_lookdev.json + materials.json'
    return mat


def uv_leaf(obj,cfg):
    uv=obj.data.uv_layers.get('ldv_feather') or obj.data.uv_layers.new(name='ldv_feather')
    if 'part' in obj and len(obj.data.vertices)==2*(cfg['leaf_rows']+1)*(cfg['leaf_cross_segments']+1):
        count=(cfg['leaf_rows']+1)*(cfg['leaf_cross_segments']+1)
        def coord(v):
            i=v%count;return ((i%(cfg['leaf_cross_segments']+1))/cfg['leaf_cross_segments'],(i//(cfg['leaf_cross_segments']+1))/cfg['leaf_rows'])
    else:
        vs=[v.co for v in obj.data.vertices];low=[min(v[i] for v in vs) for i in range(3)];high=[max(v[i] for v in vs) for i in range(3)]
        def coord(i):
            v=vs[i];return ((v.x-low[0])/max(1e-9,high[0]-low[0]),(high[2]-v.z)/max(1e-9,high[2]-low[2]))
    for loop in obj.data.loops:uv.data[loop.index].uv=coord(loop.vertex_index)


def tech_mesh(name,verts,faces,material,kind,support):
    obj=mesh(name,verts,faces,'TECH',material)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    obj['geometry_kind']=kind;obj['root_support']=support;obj['parameter_source']='design/materials_lookdev.json'
    return obj


def forehead(cfg,scale,material):
    from mathutils.bvhtree import BVHTree
    verts=[];faces=[]
    for n in ('PRI_HeadNeckTorso','FAC_MaskBridge'):
        obj=bpy.data.objects[n];dg=bpy.context.evaluated_depsgraph_get();data=obj.evaluated_get(dg).to_mesh();off=len(verts)
        verts.extend(obj.matrix_world@v.co for v in data.vertices);faces.extend(tuple(off+i for i in p.vertices) for p in data.polygons);obj.evaluated_get(dg).to_mesh_clear()
    tree=BVHTree.FromPolygons(verts,faces)
    f=cfg['forehead']
    def seat(x,z):
        hit,n,_,_=tree.ray_cast(Vector((x*scale,.35*scale,z*scale)),Vector((0,-1,0)),.8*scale)
        assert hit is not None,('forehead projection outside head',x,z)
        if n.y<0:n=-n
        return hit+n*f['seat_offset_m']*scale,n.normalized()
    for name,(x,z) in f['nodes'].items():
        center,n=seat(x,z);rad=f['hub_radius_m'] if name=='Hub' else f['terminal_radius_m']
        depth=f['hub_depth_m'] if name=='Hub' else f['node_depth_m']
        a=n.cross(Vector((1,0,0))).normalized();b=n.cross(a).normalized();v=[];faces=[]
        rows,columns=12,24
        v.append(tuple(center+n*depth*scale))
        for k in range(1,rows):
            th=math.pi*k/rows
            for j in range(columns):
                ph=math.tau*j/columns;v.append(tuple(center+n*(depth*math.cos(th)*scale)+(a*math.cos(ph)+b*math.sin(ph))*(rad*math.sin(th)*scale)))
        last=len(v);v.append(tuple(center-n*depth*scale))
        faces.extend((0,1+j,1+(j+1)%columns) for j in range(columns))
        for k in range(rows-2):
            for j in range(columns):
                i=1+k*columns+j;q=1+k*columns+(j+1)%columns;faces.append((i,i+columns,q+columns,q))
        faces.extend((last,1+(rows-2)*columns+(j+1)%columns,1+(rows-2)*columns+j) for j in range(columns))
        obj=tech_mesh('TECH_ForeheadNode_'+name,v,faces,material,'sphere','PRI_HeadNeckTorso')
        # Bottom seating is actually on the accepted bridge, not a policy label.
        obj['root_support']=min(('PRI_HeadNeckTorso','FAC_MaskBridge'),key=lambda q:source_tree(bpy.data.objects[q])[0].find_nearest(center)[3])
    for name,(start,end) in f['links'].items():
        a=Vector(f['nodes'][start]);b=Vector(f['nodes'][end]);v=[];faces=[];steps=f['link_samples'];columns=12
        for k in range(steps):
            x,z=a.lerp(b,k/(steps-1));c,n=seat(x,z)
            tangent=Vector((b.x-a.x,0,b.y-a.y)).normalized();u=tangent.cross(n).normalized();w=tangent.cross(u).normalized()
            for j in range(columns):
                phi=math.tau*j/columns;v.append(tuple(c+(u*math.cos(phi)+w*math.sin(phi))*f['link_radius_m']*scale))
        for k in range(steps-1):
            for j in range(columns):
                i=k*columns+j;q=k*columns+(j+1)%columns;faces.append((i,q,q+columns,i+columns))
        faces.append(tuple(reversed(range(columns))));faces.append(tuple((steps-1)*columns+j for j in range(columns)))
        obj=tech_mesh('TECH_ForeheadLink_'+name,v,faces,material,'sphere','PRI_HeadNeckTorso')
        obj['root_support']='FAC_MaskBridge' if name=='Bottom' else 'PRI_HeadNeckTorso'


def rings(cfg,scale,material):
    for e in cfg['perch_rings']:
        c=Vector(e['center'])*scale;v=[];faces=[];n,m=96,12
        for i in range(n):
            theta=math.tau*i/n
            for j in range(m):
                phi=math.tau*j/m;r=e['radius_m']+e['tube_m']*math.cos(phi)
                p=Vector((r*math.cos(theta),r*math.sin(theta),e['tube_m']*math.sin(phi)))*scale
                if e['axis']=='X':p=Vector((p.z,p.x,p.y))
                v.append(tuple(c+p))
        for i in range(n):
            for j in range(m):faces.append((i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m))
        tech_mesh('TECH_PerchRing_'+e['id'],v,faces,material,'torus',e['support'])


def build(root):
    root=Path(root);cfg,palette,scale=config(root)
    if 'FTH_WingPrimary_L' not in bpy.data.objects:raise RuntimeError('Materials require delivered feather geometry')
    if 'TECH' not in bpy.data.collections:bpy.context.scene.collection.children.link(bpy.data.collections.new('TECH'))
    mats={role:shader(role,cfg,palette) for role in ROLES}
    _,f,scale=feather_config(root)
    for e in cfg['chest_overrides']:
        clean(('FTH_'+e['id']+'_L','FTH_'+e['id']+'_R'))
        o=project_leaf('FTH_'+e['id']+'_R',e,source_tree(bpy.data.objects['PRI_HeadNeckTorso'])[0],f,scale,True,mats['Feather_Warm' if e['id']=='Orange' else 'Feather_Cream'],'body_chest')
        o['parameter_source']='design/materials_lookdev.json/chest_overrides';reflect_leaf(o,o.name[:-1]+'L')
    clean(('TECH_Forehead','TECH_PerchRing','BLK_Forehead'))
    forehead(cfg,scale,mats['Tech_Cyan']);rings(cfg,scale,mats['Tech_Cyan'])
    # Reflect authored right surfaces exactly: independent surface normals differ
    # at triangle boundaries and otherwise introduce measurable 11um link drift.
    for name in ('TECH_ForeheadNode_Inner_R','TECH_ForeheadNode_Outer_R','TECH_ForeheadLink_Inner_R','TECH_ForeheadLink_Outer_R','TECH_PerchRing_End_R'):
        right=bpy.data.objects[name];left_name=name[:-1]+'L';clean(left_name)
        points=[right.matrix_world@v.co for v in right.data.vertices]
        left=tech_mesh(left_name,[(-p.x,p.y,p.z) for p in points],
            [tuple(reversed(p.vertices)) for p in right.data.polygons],mats['Tech_Cyan'],right['geometry_kind'],right['root_support'])
        left['symmetric_pair']=name;right['symmetric_pair']=left_name
    mapping={'deep_navy':'Feather_Navy','mid_blue':'Feather_Blue','cyan_reference':'Feather_Cyan','cream':'Feather_Cream','orange_reference':'Feather_Warm'}
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name in EYES:continue
        if o.name.startswith('TECH_'):continue
        roles=[]
        if o.name.startswith('GRP_Perch'):roles=['Perch_Metal']*len(o.data.materials)
        elif o.name.startswith('GRP_Claw'):roles=['Keratin_Dark']*len(o.data.materials)
        elif o.name.startswith('GRP_Foot'):roles=['Keratin_Orange']*len(o.data.materials)
        elif o.name.startswith('BAK_'):roles=['Keratin_Orange','Mouth_Interior']
        elif o.name.startswith('FTH_Orange'):roles=['Feather_Warm']
        elif o.name in CHANGED:roles=['Feather_Cream']
        else:
            for mat in o.data.materials:
                key=mat.name.removeprefix('BLK_Swatch_')
                roles.append(mapping[key] if key in mapping else mat['surface_role'])
        assert roles,(o.name,'missing actual assignment')
        o.data.materials.clear()
        for role in roles:o.data.materials.append(mats[role])
        if any(role.startswith('Feather') for role in roles):uv_leaf(o,f)
    bpy.context.view_layer.update()
    bpy.context.scene['materials_scope']='#18 assigned non-eye shaders; F01 chest; eyes19 and nostrils40 remain open'
    return sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH')
