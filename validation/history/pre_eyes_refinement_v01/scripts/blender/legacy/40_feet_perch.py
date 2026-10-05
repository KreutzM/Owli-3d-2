"""Exactly 3+1 curved toe guides per foot, wrapping the parameterized perch."""
from pathlib import Path
import sys
import math
import json
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blockout_geometry import parameters, clean, swatch, ellipsoid, mesh, save
ROOT = Path.cwd()
cfg, S = parameters(ROOT)
spec = json.loads((ROOT/'design/character_spec.json').read_text())
assert (spec['anatomy']['feet']['forward_toes'], spec['anatomy']['feet']['rear_toes']) == (3, 1)
p = cfg['feet']
assert len(p['front_offsets']) == 3
clean(('GUIDE_Foot', 'GUIDE_Toe', 'GUIDE_Claw', 'GUIDE_Leg'))
orange = swatch(ROOT, 'orange_reference')
navy = swatch(ROOT, 'deep_navy')
bar = cfg['perch']['bar']
assert bar['axis'] == 'X', 'Toe guide path expects the V1 horizontal perch'
by, bz = bar['center'][1:]
radius = bar['radius'] + p['path_clearance']
for side, sign in (('L', -1), ('R', 1)):
    x = bar['center'][0] + sign*p['half_spacing']
    for part in ('pad', 'leg'):
        y, z = p[part+'_center_yz']
        obj = ellipsoid('GUIDE_'+('Foot' if part=='pad' else 'Leg')+'_'+side,
                        [x, by+y, bz+z-cfg['reference_perch_height_m']], p[part+'_dimensions'], S, 'FEET', orange)
        obj['status'] = 'anatomy_guide'
    paths = [('Front_'+str(i), dx, p['front_angles']) for i, dx in enumerate(p['front_offsets'], 1)]
    paths.append(('Rear_1', 0, p['rear_angles']))
    for label, dx, angles in paths:
        n, m = p['path_segments'], p['radial_segments']
        vertices, faces, centers = [], [], []
        for k in range(n+1):
            t = k/n
            theta = angles[0] + (angles[1]-angles[0])*t
            cx = x+dx+ (dx/p['front_offsets'][-1]*p['splay']*t if label.startswith('Front') else 0)
            cy, cz = by+radius*math.sin(theta), bz+radius*math.cos(theta)
            centers.append([cx*S, cy*S, cz*S])
            thickness = p['toe_radius']*(1-t) + p['tip_radius']*t
            for j in range(m):
                phi = math.tau*j/m
                vertices.append(((cx+thickness*math.cos(phi))*S,
                    (cy+thickness*math.sin(phi)*math.sin(theta))*S,
                    (cz+thickness*math.sin(phi)*math.cos(theta))*S))
        faces.append(tuple(reversed(range(m))))
        for k in range(n):
            for j in range(m):
                a, b = k*m+j, k*m+(j+1)%m
                faces.append((a,b,b+m,a+m))
        faces.append(tuple(range(n*m,(n+1)*m)))
        if angles[1] > angles[0]:
            faces = [tuple(reversed(f)) for f in faces]
        origin = centers[n//2]
        obj = mesh('GUIDE_Toe_'+side+'_'+label,
            [tuple(v[i]-origin[i] for i in range(3)) for v in vertices], faces, 'FEET', orange)
        obj.location = origin
        obj.data.materials.append(navy)
        for poly in obj.data.polygons:
            if poly.index > 1+int(n*.8)*m:
                poly.material_index = 1
        obj['guide_centerline'] = json.dumps(centers)
        obj['locked_toe_rule'] = '3 forward + 1 rear per foot'
        obj['status'] = 'anatomy_guide_not_final_claw'
save(ROOT)
print('Created two gripping feet with exactly three front and one rear guide each.')
