"""Layered eye meshes, perforated facial mask and nonlinear spherical blink patches."""
import hashlib
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from blockout_geometry import clean, mesh, swatch, parameters


def config(root):
    coarse,scale=parameters(root)
    face=json.loads((Path(root)/'design/face.json').read_text())
    count=face['angular_segments']
    if count<32 or count%4 or face['lid_rows']<4 or face['mask_rows']<4:
        raise ValueError('Face topology requires 4-divisible angular segments >=32 and >=4 rows')
    if not (0<face['aperture_angle_rad']<face['lid_outer_angle_rad']<math.pi/2):
        raise ValueError('Invalid lid aperture/outer arc')
    if face['lid_radius_offset_m']-face['lid_thickness_m']<=face['cornea_radius_offset_m']+face['minimum_surface_clearance_m']:
        raise ValueError('Lids must clear the outer cornea, including their thickness')
    return coarse,face,scale


def finish(name,verts,faces,material,group='EYES',parent=None):
    obj=mesh(name,verts,faces,group,material)
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj['status']='face_geometry_goal_16'
    obj['parameter_source']='design/face.json + frozen eye/mask placement in design/proportions.json'
    if parent:
        obj.parent=parent
        obj.location=(0,0,0)
    return obj


def shell(name,vertices,faces,back,material,group='EYES',parent=None):
    """Thicken an orientable disk/annular quad patch; boundary edges get side walls."""
    n=len(vertices)
    result=list(faces)+[tuple(i+n for i in reversed(face)) for face in faces]
    edges={}
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):
            key=tuple(sorted((a,b)))
            edges.setdefault(key,[]).append((a,b))
    for pairs in edges.values():
        if len(pairs)==1:
            a,b=pairs[0]
            result.append((b,a,a+n,b+n))
    return finish(name,vertices+back,result,material,group,parent)


def cap(name,radius,inner_radius,angle_min,angle_max,count,rows,material,parent):
    """Closed spherical cap/annulus, with constant radius separating eye layers."""
    points=[]
    start=angle_min==0
    if start: points.append((0,radius,0))
    rings=range(1,rows+1) if start else range(rows+1)
    for k in rings:
        theta=angle_min+(angle_max-angle_min)*k/rows
        for j in range(count):
            phi=math.tau*j/count
            points.append((radius*math.sin(theta)*math.cos(phi),radius*math.cos(theta),radius*math.sin(theta)*math.sin(phi)))
    faces=[]
    offset=1 if start else 0
    if start:
        faces.extend((0,1+(j+1)%count,1+j) for j in range(count))
    for k in range(rows-1 if start else rows):
        for j in range(count):
            a=offset+k*count+j
            b=offset+k*count+(j+1)%count
            faces.append((b,a,a+count,b+count))
    return shell(name,points,faces,[tuple(Vector(p)*(inner_radius/radius)) for p in points],material,parent=parent)


def globe(name,radius,count,material,parent):
    """Deterministic latitudinal sphere: no operator/hash-dependent polygon order."""
    rows=48
    points=[(0,0,radius)]
    for k in range(1,rows):
        theta=math.pi*k/rows
        for j in range(count):
            phi=math.tau*j/count
            points.append((radius*math.sin(theta)*math.cos(phi),radius*math.sin(theta)*math.sin(phi),radius*math.cos(theta)))
    south=len(points)
    points.append((0,0,-radius))
    faces=[(0,1+j,1+(j+1)%count) for j in range(count)]
    for k in range(rows-2):
        for j in range(count):
            a=1+k*count+j
            b=1+k*count+(j+1)%count
            faces.append((a,a+count,b+count,b))
    faces.extend((south,1+(rows-2)*count+(j+1)%count,1+(rows-2)*count+j) for j in range(count))
    return finish(name,points,faces,material,parent=parent)


def lid_points(coarse,face,scale,side,kind,value):
    p=coarse['eyes']
    radius=(p['radius']+face['lid_radius_offset_m'])*scale
    center=Vector(((-1 if side=='L' else 1)*p['half_spacing'],p['depth'],p['height']))*scale
    count=face['angular_segments']//2
    rows=face['lid_rows']
    aperture=face['aperture_angle_rad']
    outer=face['lid_outer_angle_rad']
    sign=1 if kind=='Upper' else -1
    points=[]
    # Fixed canthi retain a nonzero strip width between inner/outer arcs, avoiding poles.
    for k in range(rows+1):
        t=k/rows
        for j in range(count+1):
            phi=math.pi*j/count
            x_inner=radius*math.sin(aperture)*math.cos(phi)
            h=radius*math.sin(aperture)*math.sin(phi)
            z_inner=(sign*(1-value)+face['blink_meeting_curve']*value)*h
            x_outer=radius*math.sin(outer)*math.cos(phi)
            z_outer=sign*radius*math.sin(outer)*math.sin(phi)
            x=x_inner*(1-t)+x_outer*t
            z=z_inner*(1-t)+z_outer*t
            y=math.sqrt(max(0,radius*radius-x*x-z*z))
            points.append(tuple(center+Vector((x,y,z))))
    back=[tuple(center+(Vector(p)-center)*((radius-face['lid_thickness_m']*scale)/radius)) for p in points]
    faces=[]
    for k in range(rows):
        for j in range(count):
            a=k*(count+1)+j
            face=(a,a+1,a+count+2,a+count+1)
            faces.append(face if sign==1 else tuple(reversed(face)))
    return points,faces,back


def set_blink(root,values):
    """Recompute actual lid cages on their clearance sphere. 0 open, 1 fully closed."""
    coarse,face,scale=config(root)
    for side in ('L','R'):
        value=values[side] if isinstance(values,dict) else values
        if not 0<=value<=1: raise ValueError('Blink must be in [0,1]')
        for kind in ('Upper','Lower'):
            obj=bpy.data.objects[f'FAC_Lid_{kind}_{side}']
            front,_,back=lid_points(coarse,face,scale,side,kind,value)
            for vertex,point in zip(obj.data.vertices,front+back): vertex.co=point
            obj.data.update()
            obj['blink_probe_value']=float(value)
    bpy.context.view_layer.update()


def mask(root,coarse,face,scale,side,material):
    p=coarse['mask']
    eye=coarse['eyes']
    sign=-1 if side=='L' else 1
    count,rows=face['angular_segments'],face['mask_rows']
    points=[]
    for k in range(rows+1):
        t=k/rows
        for j in range(count):
            phi=math.tau*j/count
            # Rings blend the eye-centric socket into the frozen cream lobe envelope.
            x_inner=sign*eye['half_spacing']+face['mask_inner_radius_m']*math.cos(phi)
            z_inner=eye['height']+face['mask_inner_radius_m']*math.sin(phi)
            x_outer=sign*p['center'][0]+p['dimensions'][0]/2*math.cos(phi)
            z_outer=p['center'][2]+p['dimensions'][2]/2*math.sin(phi)
            x=x_inner*(1-t)+x_outer*t
            z=z_inner*(1-t)+z_outer*t
            y=(eye['depth']+.006)*(1-t)+p['center'][1]*t+face['mask_ridge_depth_m']*math.sin(math.pi*t)
            # The beak's medial attachment gets a recessed cheek/nose seat, never a cream shield through orange geometry.
            if z<.397 and abs(x)<.037:
                w=(1-min(1,abs(x)/.037))*(1-min(1,max(0,(z-.387)/.01)))
                y=min(y,face['mask_medial_back_y_m']+.008*(1-w))
            points.append((x*scale,y*scale,z*scale))
    faces=[]
    for k in range(rows):
        for j in range(count):
            a=k*count+j
            b=k*count+(j+1)%count
            faces.append((a,b,b+count,a+count))
    back=[(x,y-face['mask_thickness_m']*scale,z) for x,y,z in points]
    return shell('FAC_Mask_'+side,points,faces,back,material,group='PRIMARY_FORM')


def bridge(face,scale,material):
    count=12
    points=[]
    # A narrow central feather/skin seat remains behind the beak, widening above the eye line.
    for z,width,y in face['bridge_rings']:
        for j in range(count+1):
            u=2*j/count-1
            points.append((width*u*scale,(y+.002*(1-u*u))*scale,z*scale))
    faces=[]
    for k in range(len(face['bridge_rings'])-1):
        for j in range(count):
            a=k*(count+1)+j
            faces.append((a+1,a,a+count+1,a+count+2))
    return shell('FAC_MaskBridge',points,faces,[(x,y-face['mask_thickness_m']*scale,z) for x,y,z in points],material,group='PRIMARY_FORM')


def clear_cornea():
    name='FAC_CorneaInspection'
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes=True
    nodes=material.node_tree.nodes
    nodes.clear()
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    out=nodes.new('ShaderNodeOutputMaterial')
    material.node_tree.links.new(transparent.outputs[0],out.inputs[0])
    material['status']='transparent geometric inspection overlay; final cornea shader deferred'
    return material


def build(root):
    root=Path(root)
    coarse,face,scale=config(root)
    freeze=json.loads((root/'design/silhouette_freeze.json').read_text())
    if freeze['status']!='silhouette_frozen' or hashlib.sha256((root/'design/proportions.json').read_bytes()).hexdigest()!=freeze['evidence_sha256']['design/proportions.json']:
        raise RuntimeError('Face stage requires unchanged frozen coarse dimensions')
    if 'PRI_HeadNeckTorso' not in bpy.data.objects: raise RuntimeError('Build the accepted #15 primary shell first')
    clean('FAC_')
    navy,blue,cyan,cream=[swatch(root,key) for key in ('deep_navy','mid_blue','cyan_reference','cream')]
    cornea_material=clear_cornea()
    eye=coarse['eyes']
    n=face['angular_segments']
    rows=face['radial_segments']
    for side,sign in (('L',-1),('R',1)):
        center=Vector((sign*eye['half_spacing'],eye['depth'],eye['height']))*scale
        pivot=bpy.data.objects.new('FAC_EyeAim_'+side,None)
        bpy.data.collections['EYES'].objects.link(pivot)
        pivot.location=center
        pivot.empty_display_type='PLAIN_AXES'
        pivot.empty_display_size=.012*scale
        pivot['aim_axis']='+Y; local X horizontal and Z up; globe-center pivot'
        pivot['final_controls']='eye_'+side+'_aim in the future avatar rig'
        globe('FAC_Globe_'+side,eye['radius']*scale,n,navy,pivot)
        iris=cap('FAC_Iris_'+side,(eye['radius']+face['iris_radius_offset_m'])*scale,
                 (eye['radius']+face['iris_radius_offset_m']-face['iris_thickness_m'])*scale,
                 eye['pupil_angle'],eye['iris_angle'],n,rows,cyan,pivot)
        iris.data.materials.append(blue)
        for p in iris.data.polygons:
            p.material_index=int((p.center.x*p.center.x+p.center.z*p.center.z)**.5<.038*scale)
        cap('FAC_Pupil_'+side,(eye['radius']+face['pupil_radius_offset_m'])*scale,
            (eye['radius']+face['pupil_radius_offset_m']-.00015)*scale,0,eye['pupil_angle']+.005,n,rows,navy,pivot)
        cap('FAC_Cornea_'+side,(eye['radius']+face['cornea_radius_offset_m'])*scale,
            (eye['radius']+face['cornea_radius_offset_m']-face['cornea_thickness_m'])*scale,
            0,face['cornea_angle_rad'],n,rows,cornea_material,pivot)
        mask(root,coarse,face,scale,side,cream)
        for kind in ('Upper','Lower'):
            front,faces,back=lid_points(coarse,face,scale,side,kind,0)
            obj=shell(f'FAC_Lid_{kind}_{side}',front,faces,back,cream,group='PRIMARY_FORM')
            obj['blink_probe_value']=0.0
            obj['blink_method']='face_geometry.set_blink: spherical nonlinear reconstruction'
    bridge(face,scale,cream)
    clean(('BLK_Eye_','BLK_IrisGuide_','BLK_PupilGuide_','BLK_Mask_','BLK_MaskBridge'))
    bpy.context.scene['face_parameters']='design/face.json'
    bpy.context.scene['face_scope']='#16 eye/iris/cornea aim pivots, perforated mask and spherical blink topology'
    bpy.context.view_layer.update()
