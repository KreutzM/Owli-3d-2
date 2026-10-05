"""Apply the fixed studio, validate full framing, render four views and persist it."""
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validation_setup import frame_bounds, setup, studio_snapshot

ROOT = Path.cwd()
OUT = Path(os.environ.get("OWLI_VALIDATION_OUTPUT", ROOT / "validation/renders")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
cfg, cameras = setup(ROOT)
scene = bpy.context.scene
bounds = frame_bounds(cfg, cameras)
resolution = int(os.environ.get("OWLI_RENDER_SIZE", cfg["render"]["resolution"]))
if resolution < 1:
    raise ValueError("Render resolution must be positive")
report = {
    "schema_version": 1,
    "blender_version": bpy.app.version_string,
    "config_sha256": scene["validation_config_sha256"],
    "resolution": [resolution, resolution],
    "frame": scene.frame_current,
    "design_approval": False,
    "studio": studio_snapshot(),
    "framing": bounds,
    "references": cfg["views"],
    "render_sha256": {},
}
try:
    scene.render.resolution_x = scene.render.resolution_y = resolution
    for camera in cameras:
        scene.camera = camera
        path = OUT / f"{camera.name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        report["render_sha256"][camera.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print("rendered", camera.name)
finally:
    # Test size/output overrides must never become the saved production defaults.
    scene.render.resolution_x = scene.render.resolution_y = cfg["render"]["resolution"]
    scene.camera = cameras[0]
    scene.render.filepath = "//../../validation/renders/VAL_FRONT.png"

if not bpy.data.filepath:
    raise RuntimeError("Save the scene before running the validation renderer")
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
(OUT / "render_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("Saved fixed cameras/lights and render manifest; no silhouette approval implied.")
