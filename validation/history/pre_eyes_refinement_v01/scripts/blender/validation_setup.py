"""Shared, deterministic validation studio. Imported by scene setup and renderer."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validation_config import validate_studio


def read_config(root):
    path = Path(root) / "validation/reference_views.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_studio(cfg)
    if errors:
        raise ValueError("Invalid validation studio configuration:\n" + "\n".join(errors))
    return cfg


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def owned_object(name, kind, group):
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != kind:
        raise RuntimeError(f"Validation name collision: {name} is {obj.type}, expected {kind}")
    if obj is None:
        if kind == "CAMERA":
            data = bpy.data.cameras.get(name + "_Data") or bpy.data.cameras.new(name + "_Data")
        else:
            data = bpy.data.lights.get(name + "_Data") or bpy.data.lights.new(name + "_Data", "AREA")
        obj = bpy.data.objects.new(name, data)
    target = collection(group)
    for col in list(obj.users_collection):
        if col != target:
            col.objects.unlink(obj)
    if obj.name not in target.objects:
        target.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj.hide_set(False)
    obj["validation_owned"] = True
    return obj


def aim(obj, location, target):
    obj.parent = None
    obj.animation_data_clear()
    obj.constraints.clear()
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    obj.scale = (1, 1, 1)


def setup(root):
    cfg = read_config(root)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if bpy.app.version >= (5, 0, 0) else "BLENDER_EEVEE_NEXT"
    render = cfg["render"]
    scene.render.resolution_x = scene.render.resolution_y = render["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.film_transparent = render["film_transparent"]
    scene.render.use_border = False
    scene.render.use_crop_to_border = False
    scene.render.use_motion_blur = False
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.image_settings.file_format = render["format"]
    scene.render.image_settings.color_mode = render["color_mode"]
    scene.render.image_settings.color_depth = render["color_depth"]
    scene.eevee.taa_render_samples = render["samples"]
    scene.eevee.use_raytracing = False
    scene.eevee.use_shadows = True
    scene.view_settings.view_transform = render["view_transform"]
    scene.view_settings.look = render["look"]
    scene.view_settings.exposure = render["exposure"]
    scene.view_settings.gamma = render["gamma"]
    scene.view_settings.use_curve_mapping = False
    cameras = []
    for view in cfg["views"]:
        cam = owned_object(view["name"], "CAMERA", "CAMERAS")
        spec = view["camera"]
        aim(cam, spec["location"], spec["target"])
        cam.data.type = spec["projection"]
        cam.data.ortho_scale = spec["ortho_scale"]
        cam.data.lens = spec["lens_mm"]
        cam.data.sensor_width = spec.get("sensor_width_mm", 36.0)
        cam.data.sensor_fit = spec.get("sensor_fit", "AUTO")
        cam.data.shift_x = cam.data.shift_y = 0
        cam.data.clip_start = spec["clip_start_m"]
        cam.data.clip_end = spec["clip_end_m"]
        cam.data.dof.use_dof = False
        cameras.append(cam)
    lighting = cfg["lighting"]
    for spec in lighting["lights"]:
        light = owned_object(spec["name"], "LIGHT", "LIGHTS")
        aim(light, spec["location"], lighting["target"])
        light.data.type = "AREA"
        light.data.shape = "DISK"
        light.data.energy = spec["energy_w"]
        light.data.size = spec["size_m"]
        light.data.color = lighting["color_linear"]
        light.data.use_shadow = True
    world_cfg = cfg["world"]
    world = bpy.data.worlds.get(world_cfg["name"]) or bpy.data.worlds.new(world_cfg["name"])
    world.use_nodes = True
    world.node_tree.nodes.clear()
    background = world.node_tree.nodes.new("ShaderNodeBackground")
    background.inputs["Color"].default_value = (*world_cfg["color_linear"], 1)
    background.inputs["Strength"].default_value = world_cfg["strength"]
    output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    scene.world = world
    scene.camera = cameras[0]
    scene.render.filepath = "//../../validation/renders/VAL_FRONT.png"
    scene["validation_config_sha256"] = hashlib.sha256((Path(root) / "validation/reference_views.json").read_bytes()).hexdigest()
    scene["validation_camera_policy"] = cfg["camera_policy"]
    bpy.context.view_layer.update()
    return cfg, cameras


def geometry_objects(cfg):
    names = set()
    for name in cfg["framing"]["geometry_collections"]:
        col = bpy.data.collections.get(name)
        if col:
            names.update(obj.name for obj in col.all_objects)
    return [bpy.data.objects[n] for n in sorted(names)
            if bpy.data.objects[n].type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}
            and not bpy.data.objects[n].hide_render]


def frame_bounds(cfg, cameras):
    """Conservative evaluated bounding boxes, including perch and rear toe guides."""
    scene = bpy.context.scene
    foreign_lights = [obj.name for obj in scene.objects if obj.type == "LIGHT"
                      and not obj.hide_render and not obj.get("validation_owned")]
    if foreign_lights:
        raise RuntimeError(f"Disable non-studio lights before validation: {foreign_lights}")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = geometry_objects(cfg)
    if not objects:
        raise RuntimeError("No character/perch geometry to validate")
    margin = cfg["framing"]["minimum_margin"]
    result = {}
    errors = []
    for cam in cameras:
        items = {}
        for obj in objects:
            evaluated = obj.evaluated_get(depsgraph)
            points = [world_to_camera_view(scene, cam, evaluated.matrix_world @ Vector(corner))
                      for corner in evaluated.bound_box]
            low = [min(p[i] for p in points) for i in range(3)]
            high = [max(p[i] for p in points) for i in range(3)]
            ok = (low[0] >= margin and low[1] >= margin and high[0] <= 1 - margin
                  and high[1] <= 1 - margin and low[2] >= cam.data.clip_start
                  and high[2] <= cam.data.clip_end)
            items[obj.name] = {"min": low, "max": high, "inside_safe_frame": ok}
            if not ok:
                errors.append(f"{cam.name}: {obj.name} outside fixed safe frame: {low} .. {high}")
        result[cam.name] = {"objects": items, "object_count": len(items),
                            "minimum_image_margin": min(min(v["min"][0], v["min"][1],
                                                           1-v["max"][0], 1-v["max"][1]) for v in items.values()),
                            "inside_safe_frame": all(v["inside_safe_frame"] for v in items.values())}
    if errors:
        raise RuntimeError("Framing failed; correct geometry or document a projection/scale issue.\n" + "\n".join(errors))
    return result


def studio_snapshot():
    scene = bpy.context.scene
    objects = {}
    for obj in sorted(bpy.data.objects, key=lambda o: o.name):
        if not obj.get("validation_owned"):
            continue
        record = {"type": obj.type, "matrix": [list(row) for row in obj.matrix_world]}
        if obj.type == "CAMERA":
            record.update(projection=obj.data.type, lens=obj.data.lens,
                          ortho_scale=obj.data.ortho_scale, sensor_width=obj.data.sensor_width,
                          sensor_fit=obj.data.sensor_fit, clip_start=obj.data.clip_start,
                          clip_end=obj.data.clip_end, shift_x=obj.data.shift_x, shift_y=obj.data.shift_y)
        else:
            record.update(energy=obj.data.energy, size=obj.data.size, color=list(obj.data.color),
                          shape=obj.data.shape)
        objects[obj.name] = record
    background = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
    return {"objects": objects, "camera_datablocks": sorted(d.name for d in bpy.data.cameras),
            "light_datablocks": sorted(d.name for d in bpy.data.lights),
            "world": {"name": scene.world.name, "color": list(background.inputs["Color"].default_value),
                      "strength": background.inputs["Strength"].default_value},
            "render": {"engine": scene.render.engine, "resolution": [scene.render.resolution_x, scene.render.resolution_y],
                       "samples": scene.eevee.taa_render_samples, "view_transform": scene.view_settings.view_transform,
                       "look": scene.view_settings.look, "exposure": scene.view_settings.exposure,
                       "gamma": scene.view_settings.gamma},
            "scene_object_count": len(scene.objects)}
