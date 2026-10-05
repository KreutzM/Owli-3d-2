"""Integration checks run inside Blender against the actual technical fixture."""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validation_setup import frame_bounds, geometry_objects, read_config, setup, studio_snapshot


def geometry_digest(cfg):
    digest = hashlib.sha256()
    for obj in geometry_objects(cfg):
        digest.update(obj.name.encode())
        for row in obj.matrix_world:
            digest.update(struct.pack("4f", *row))
        if obj.type == "MESH":
            for vertex in obj.data.vertices:
                digest.update(struct.pack("3f", *vertex.co))
            for polygon in obj.data.polygons:
                digest.update(struct.pack(f"{len(polygon.vertices)}I", *polygon.vertices))
    return digest.hexdigest()


def main():
    root = Path.cwd()
    cfg = read_config(root)
    before = studio_snapshot()
    geometry_before = geometry_digest(cfg)
    for _ in range(2):
        _, cams = setup(root)
        assert studio_snapshot() == before, "Repeated setup changed studio or added objects/datablocks"
        assert geometry_digest(cfg) == geometry_before, "Studio setup changed character/perch geometry"
    assert len(bpy.data.cameras) == 4
    assert len(bpy.data.lights) == 5
    assert len(bpy.data.collections["CAMERAS"].objects) == 4
    assert len(bpy.data.collections["LIGHTS"].objects) == 5
    assert bpy.context.scene.render.resolution_x == bpy.context.scene.render.resolution_y == 1024
    assert bpy.context.scene.camera.name == "VAL_FRONT"
    for side in ("L", "R"):
        names = {o.name for o in bpy.data.objects if o.name.startswith(f"GUIDE_Toe_{side}_")}
        assert names == {f"GUIDE_Toe_{side}_Front_{i}" for i in (1, 2, 3)} | {f"GUIDE_Toe_{side}_Rear_1"}
        assert bpy.data.objects[f"GUIDE_Toe_{side}_Rear_1"].location.y < 0
    bounds = frame_bounds(cfg, cams)
    head = bpy.data.objects["BLK_Head"]
    initial_x = head.location.x
    try:
        head.location.x += 1
        bpy.context.view_layer.update()
        try:
            frame_bounds(cfg, cams)
        except RuntimeError as exc:
            assert "BLK_Head" in str(exc)
        else:
            raise AssertionError("Out-of-frame geometry was not rejected")
    finally:
        head.location.x = initial_x
        bpy.context.view_layer.update()
    saved_clip_end = cams[0].data.clip_end
    try:
        cams[0].data.clip_end = 0.1
        try:
            frame_bounds(cfg, cams)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Depth clipping was not rejected")
    finally:
        cams[0].data.clip_end = saved_clip_end
    assert geometry_digest(cfg) == geometry_before
    assert studio_snapshot() == before
    report = {"studio": before, "geometry_sha256": geometry_before, "framing": bounds,
              "checks": {"idempotent_setup": True, "no_geometry_changes": True,
                         "four_cameras_five_lights": True, "canonical_1024_saved": True,
                         "toe_rule_3_plus_1": True, "image_clipping_rejected": True,
                         "depth_clipping_rejected": True}, "design_approval": False}
    path = Path(os.environ["OWLI_VERIFY_OUTPUT"])
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("VALIDATION INTEGRATION OK")


if __name__ == "__main__":
    main()
