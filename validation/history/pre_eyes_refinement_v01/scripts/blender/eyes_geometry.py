"""#19 layered eye finish and corrected literal pupil/iris proportions."""
import json
import math
from pathlib import Path
import bpy
from blockout_geometry import clean
from face_geometry import config as face_config, cap
from materials_geometry import linear, EYES

ROLES = ('Eye_Globe', 'Eye_Iris', 'Eye_Pupil', 'Eye_Cornea')
CHANGED = tuple(f'FAC_{part}_{side}' for part in ('Iris', 'Pupil') for side in ('L', 'R'))


def config(root):
    return json.loads((Path(root)/'design/eyes_lookdev.json').read_bytes())


def shader(role, cfg, scale):
    s = cfg['shader']
    mat = bpy.data.materials.get('MAT_'+role) or bpy.data.materials.new('MAT_'+role)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    def node(kind, name):
        item = tree.nodes.new(kind); item.name = name; item.label = name
        return item
    def wire(a, output, b, input):
        tree.links.new(a.outputs[output], b.inputs[input])
    def mathnode(name, operation, a, b=None):
        item = node('ShaderNodeMath', name); item.operation = operation
        for index, value in enumerate((a, b)):
            if value is None: continue
            if isinstance(value, tuple): wire(value[0], value[1], item, index)
            else: item.inputs[index].default_value = value
        return item
    out = node('ShaderNodeOutputMaterial', 'SurfaceOutput')
    if role == 'Eye_Cornea':
        mat.surface_render_method = 'BLENDED'
        clear = node('ShaderNodeBsdfTransparent', 'OpticalTransmission')
        glossy = node('ShaderNodeBsdfGlossy', 'Surface')
        glossy.inputs['Color'].default_value = (1, 1, 1, 1)
        glossy.inputs['Roughness'].default_value = s['cornea_roughness']
        radiance = node('ShaderNodeShaderToRGB', 'RealStudioReflection')
        wire(glossy, 0, radiance, 'Shader')
        optical = node('ShaderNodeEmission', 'StylizedOpticalResponse')
        wire(radiance, 'Color', optical, 'Color')
        optical.inputs['Strength'].default_value = s['cornea_reflection_gain']
        fresnel = node('ShaderNodeFresnel', 'OpticalFresnel')
        fresnel.inputs['IOR'].default_value = s['cornea_ior']
        geometry = node('ShaderNodeNewGeometry', 'ShellFacing')
        front = mathnode('FrontSurfaceOnly', 'SUBTRACT', 1, (geometry, 'Backfacing'))
        weight = mathnode('SingleOpticalCoat', 'MULTIPLY', (front, 0), (fresnel, 'Fac'))
        blend = node('ShaderNodeMixShader', 'OpticalCoating')
        wire(weight, 0, blend, 0); wire(clear, 0, blend, 1); wire(optical, 0, blend, 2)
        wire(blend, 0, out, 'Surface')
        mat.diffuse_color = (1, 1, 1, 0.05)
    else:
        p = node('ShaderNodeBsdfPrincipled', 'Surface')
        p.inputs['Metallic'].default_value = 0
        p.inputs['Roughness'].default_value = s[role.removeprefix('Eye_').lower()+'_roughness']
        p.inputs['IOR'].default_value = s['cornea_ior']
        base = linear(s[role.removeprefix('Eye_').lower()+'_srgb']) if role != 'Eye_Iris' else linear(s['upper_srgb'])
        p.inputs['Base Color'].default_value = base; mat.diffuse_color = base
        wire(p, 'BSDF', out, 'Surface')
        if role == 'Eye_Iris':
            p.inputs['Specular IOR Level'].default_value = s['iris_specular_ior_level']
            tex = node('ShaderNodeTexCoord', 'EyeCoordinates')
            axes = node('ShaderNodeSeparateXYZ', 'EyeAxes'); wire(tex, 'Object', axes, 'Vector')
            # Local X/Z are real meters at the globe-center aim pivot.
            z = mathnode('IrisVerticalNormalized', 'DIVIDE', (axes, 'Z'), .04425*scale)
            lower = mathnode('LowerHemisphere', 'MULTIPLY_ADD', (z, 0), -.5)
            lower.inputs[2].default_value = .5
            ramp = node('ShaderNodeValToRGB', 'BlueCyanDepth')
            ramp.color_ramp.interpolation = 'EASE'
            stops = [(0, 'upper_srgb'), (.38, 'upper_srgb'), (.62, 'middle_srgb'), (.85, 'lower_srgb'), (1, 'lower_light_srgb')]
            ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
            for i, (position, key) in enumerate(stops):
                element = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(position)
                element.position = position; element.color = linear(s[key])
            wire(lower, 0, ramp, 'Fac')
            x2 = mathnode('RadialX2', 'MULTIPLY', (axes, 'X'), (axes, 'X'))
            z2 = mathnode('RadialZ2', 'MULTIPLY', (axes, 'Z'), (axes, 'Z'))
            r2 = mathnode('RadialSquared', 'ADD', (x2, 0), (z2, 0))
            radius = mathnode('RadialDistance', 'SQRT', (r2, 0))
            r = mathnode('IrisRadiusNormalized', 'DIVIDE', (radius, 0), .04425*scale)
            # Lower illumination follows a curved outer iris crescent rather
            # than painting the whole bottom half with a straight horizon.
            radial = node('ShaderNodeValToRGB', 'IrisPeripheralDepth')
            radial.color_ramp.elements[0].position = .30
            radial.color_ramp.elements[0].color = linear(s['upper_srgb'])
            radial.color_ramp.elements[1].position = .96
            radial.color_ramp.elements[1].color = linear(s['middle_srgb'])
            wire(r, 0, radial, 'Fac')
            upper = mathnode('UpperIrisShadeHeight', 'MULTIPLY', (z, 0), 1.4)
            upper.use_clamp = True
            shaded = node('ShaderNodeMixRGB', 'UpperNavyDepth')
            wire(upper, 0, shaded, 0); wire(radial, 'Color', shaded, 1)
            shaded.inputs[2].default_value = linear(s['upper_srgb'])
            crescent = mathnode('LowerCrescentRadius', 'SUBTRACT', (r, 0), .52)
            crescent = mathnode('LowerCrescentGain', 'MULTIPLY', (crescent, 0), 3.5)
            crescent.use_clamp = True
            zone = mathnode('LowerCrescentHeight', 'MULTIPLY', (z, 0), -2.5)
            zone.use_clamp = True
            arc = mathnode('CurvedLowerIris', 'MULTIPLY', (crescent, 0), (zone, 0))
            curved = node('ShaderNodeMixRGB', 'LowerArcDepth')
            wire(arc, 0, curved, 0); wire(shaded, 'Color', curved, 1); wire(ramp, 'Color', curved, 2)
            rim = node('ShaderNodeValToRGB', 'SoftLimbus')
            rim.color_ramp.elements[0].position = .90; rim.color_ramp.elements[0].color = (0, 0, 0, 1)
            rim.color_ramp.elements[1].position = 1; rim.color_ramp.elements[1].color = (1, 1, 1, 1)
            wire(r, 0, rim, 'Fac')
            edge = node('ShaderNodeMixRGB', 'DeepPeripheralRim')
            wire(rim, 'Color', edge, 0); wire(curved, 'Color', edge, 1)
            edge.inputs[2].default_value = linear(s['limbus_srgb'])
            warm_r = mathnode('WarmPeripheralBand', 'SUBTRACT', (r, 0), .91)
            warm_r = mathnode('WarmPeripheralGain', 'MULTIPLY', (warm_r, 0), 15); warm_r.use_clamp = True
            warm_z = mathnode('WarmLowerZone', 'MULTIPLY', (z, 0), -1)
            warm_z = mathnode('WarmLowerRestriction', 'SUBTRACT', (warm_z, 0), .45); warm_z.use_clamp = True
            warm = mathnode('RestrainedWarmArc', 'MULTIPLY', (warm_r, 0), (warm_z, 0))
            color = node('ShaderNodeMixRGB', 'LogoLowerWarmAccent')
            wire(warm, 0, color, 0); wire(edge, 'Color', color, 1)
            color.inputs[2].default_value = linear(s['warm_srgb'])
            # Analytic 2D segment/node distance field in local coordinates.
            position = node('ShaderNodeCombineXYZ', 'IrisPlane')
            wire(axes, 'X', position, 'X'); wire(axes, 'Z', position, 'Z')
            points = cfg['network']['points_xz_m']; distances = []
            for index, (a, b) in enumerate(cfg['network']['links']):
                start = (points[a][0]*scale, 0, points[a][1]*scale)
                delta = ((points[b][0]-points[a][0])*scale, 0, (points[b][1]-points[a][1])*scale)
                rel = node('ShaderNodeVectorMath', f'Link{index}_Relative'); rel.operation = 'SUBTRACT'
                wire(position, 'Vector', rel, 0); rel.inputs[1].default_value = start
                dot = node('ShaderNodeVectorMath', f'Link{index}_Projection'); dot.operation = 'DOT_PRODUCT'
                wire(rel, 'Vector', dot, 0); dot.inputs[1].default_value = delta
                t = mathnode(f'Link{index}_Parameter', 'DIVIDE', (dot, 'Value'), sum(v*v for v in delta)); t.use_clamp = True
                projected = node('ShaderNodeVectorMath', f'Link{index}_Closest'); projected.operation = 'SCALE'
                projected.inputs[0].default_value = delta; wire(t, 0, projected, 'Scale')
                distance = node('ShaderNodeVectorMath', f'Link{index}_Distance'); distance.operation = 'DISTANCE'
                wire(rel, 'Vector', distance, 0); wire(projected, 'Vector', distance, 1)
                band = mathnode(f'Link{index}_Stroke', 'LESS_THAN', (distance, 'Value'), s['network_line_width_m']*scale)
                distances.append(band)
            for index, (x, zpoint) in enumerate(points):
                distance = node('ShaderNodeVectorMath', f'Node{index}_Distance'); distance.operation = 'DISTANCE'
                wire(position, 'Vector', distance, 0); distance.inputs[1].default_value = (x*scale, 0, zpoint*scale)
                dot = mathnode(f'Node{index}_Disk', 'LESS_THAN', (distance, 'Value'), s['network_node_radius_m']*scale)
                distances.append(dot)
            mask = distances[0]
            for index, item in enumerate(distances[1:]): mask = mathnode(f'NetworkUnion{index}', 'MAXIMUM', (mask, 0), (item, 0))
            opacity = mathnode('SubtleNetwork', 'MULTIPLY', (mask, 0), s['network_opacity'])
            final = node('ShaderNodeMixRGB', 'EmbeddedNetwork')
            wire(opacity, 0, final, 0); wire(color, 'Color', final, 1)
            final.inputs[2].default_value = linear(s['network_srgb'])
            wire(final, 'Color', p, 'Base Color'); wire(final, 'Color', p, 'Emission Color')
            glow = mathnode('LowerRetinalLight', 'MULTIPLY_ADD', (arc, 0), s['lower_arc_emission_addition'])
            glow.inputs[2].default_value = s['iris_emission_strength']
            wire(glow, 0, p, 'Emission Strength')
    mat['surface_role'] = role
    mat['parameter_source'] = 'design/eyes_lookdev.json'
    mat['palette_space'] = 'linear from documented sRGB'
    return mat


def build(root):
    coarse, face, scale = face_config(root)
    cfg = config(root); g = cfg['geometry']; eye = coarse['eyes']
    if 'TECH_ForeheadNode_Hub' not in bpy.data.objects:
        raise RuntimeError('Eyes require accepted #18 material scene')
    previous_materials = {m.name for name in EYES for m in bpy.data.objects[name].data.materials}
    mats = {role: shader(role, cfg, scale) for role in ROLES}
    for side in ('L', 'R'):
        pivot = bpy.data.objects['FAC_EyeAim_'+side]
        for part in ('Iris', 'Pupil'): clean('FAC_'+part+'_'+side)
        iris_radius = (eye['radius']+face['iris_radius_offset_m'])*scale
        cap('FAC_Iris_'+side, iris_radius, iris_radius-face['iris_thickness_m']*scale,
            math.asin(g['iris_inner_projected_radius_m']*scale/iris_radius), eye['iris_angle'],
            g['angular_segments'], g['radial_segments'], mats['Eye_Iris'], pivot)
        pupil_radius = (eye['radius']+face['pupil_radius_offset_m'])*scale
        cap('FAC_Pupil_'+side, pupil_radius, pupil_radius-.00015*scale, 0, g['pupil_angle_rad'],
            g['pupil_angular_segments'], g['pupil_radial_segments'], mats['Eye_Pupil'], pivot)
        for part in ('Globe', 'Iris', 'Pupil', 'Cornea'):
            obj = bpy.data.objects[f'FAC_{part}_{side}']
            obj.data.materials.clear(); obj.data.materials.append(mats['Eye_'+part])
            for polygon in obj.data.polygons: polygon.material_index = 0
            obj['lookdev_source'] = 'design/eyes_lookdev.json'
    for name in previous_materials:
        material = bpy.data.materials.get(name)
        if material and material.users == 0 and name not in {'MAT_'+role for role in ROLES}:
            bpy.data.materials.remove(material)
    bpy.context.view_layer.update()
    bpy.context.scene['eyes_scope'] = '#19 optical eye layers, corrected pupil ratio and embedded procedural iris network'
    return list(EYES)
