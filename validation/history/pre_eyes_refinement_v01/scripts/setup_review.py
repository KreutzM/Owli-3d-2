"""Build, reopen and verify an isolated studio fixture; publish permanent evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def image_metrics(path):
    with Image.open(path) as source:
        image = source.convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    difference = ImageChops.difference(image, background)
    mask = difference.convert("L").point(lambda v: 255 if v > 4 else 0)
    bounds = mask.getbbox()
    if image.size != (1024, 1024) or bounds is None:
        raise RuntimeError(f"Invalid/blank setup render: {path}")
    if min(bounds[:2]) <= 0 or bounds[2] >= 1024 or bounds[3] >= 1024:
        raise RuntimeError(f"Foreground touches image border: {path}: {bounds}")
    histogram = image.convert("L").histogram(mask)
    clipped_fraction = sum(histogram[250:]) / sum(histogram)
    if clipped_fraction > 0.05:
        raise RuntimeError(f"Setup fixture is overexposed: {path}: {clipped_fraction:.1%} near-white foreground")
    return {"size": list(image.size), "foreground_bbox_px": list(bounds),
            "foreground_near_white_fraction": clipped_fraction,
            "background_rgb": list(image.getpixel((0, 0))),
            "foreground_mean_rgb": ImageStat.Stat(image, mask).mean,
            "foreground_stddev_rgb": ImageStat.Stat(image, mask).stddev}


def paste_contained(board, image, box):
    x, y, width, height = box
    contained = ImageOps.contain(image.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
    board.paste(contained, (x + (width-contained.width)//2, y + (height-contained.height)//2))


def reference_image(root, file, crop):
    with Image.open(root / "references/approved" / file) as source:
        image = source.convert("RGB")
    return image.crop(crop) if crop else image


def review_boards(root, output, cfg, milestone="fixed studio setup fixture"):
    title_font = ImageFont.load_default(size=28)
    font = ImageFont.load_default(size=20)
    small = ImageFont.load_default(size=16)
    contact = Image.new("RGB", (2112, 2272), "#f3f4f6")
    contact_draw = ImageDraw.Draw(contact)
    contact_draw.text((32, 16), f"Owli | {milestone} | render evidence; see written review", font=title_font, fill="#17233c")
    for index, view in enumerate(cfg["views"]):
        name = view["name"]
        with Image.open(output / f"{name}.png") as source:
            render = source.convert("RGB")
        col, row = index % 2, index // 2
        contact.paste(render, (32 + col*1056, 100 + row*1080))
        contact_draw.text((32+col*1056, 64+row*1080), name, font=font, fill="#17233c")
        board = Image.new("RGB", (1536, 1240), "#f3f4f6")
        draw = ImageDraw.Draw(board)
        draw.text((20, 15), f"{name} | {milestone}", font=title_font, fill="#17233c")
        draw.text((20, 58), "Fixed camera / provisional surfaces / 1024 px", font=font, fill="#17233c")
        board.paste(render, (20, 100))
        panel = view["reference_panel"]
        ref = reference_image(root, view["reference"], panel["crop_px"])
        draw.text((1064, 58), f"{panel['label']} | rank {view['reference_rank']}", font=font, fill="#17233c")
        if view.get("geometry_reference"):
            paste_contained(board, ref, (1064, 650, 452, 452))
            geom = view["geometry_reference"]
            draw.text((1064, 110), f"Geometry: {geom['label']} | rank 2", font=small, fill="#17233c")
            paste_contained(board, reference_image(root, geom["file"], geom["crop_px"]), (1064, 145, 452, 460))
            draw.text((1064, 615), "Style support (beauty)", font=small, fill="#17233c")
        else:
            paste_contained(board, ref, (1064, 100, 452, 1024))
        draw.text((20, 1140), f"Reference: {view['reference']} | panel: {panel['label']}", font=font, fill="#17233c")
        draw.text((20, 1172), "References preserve aspect ratio; visual decisions are recorded in the written review.", font=font, fill="#17233c")
        draw.text((20, 1204), "Authority: logo (1), technical turnaround (2), parts/lookdev (3), beauty (4).", font=small, fill="#17233c")
        board.save(output / f"{name}_comparison.png")
    contact.save(output / "contact_sheet.png")


def build_review(root, blender, milestone="setup"):
    root = Path(root).resolve()
    subprocess.run([sys.executable, str(root / "scripts/validate_project.py"), "--strict-assets"], cwd=root, check=True)
    cfg_path = root / "validation/reference_views.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    scratch_parent = root / "tmp"
    scratch_parent.mkdir(exist_ok=True)
    output = root / "validation/reviews" / milestone
    scene_output = root / "blender/scene" / ("owli_validation_setup.blend" if milestone == "setup" else "owli_blockout_v01.blend")
    scripts = root / "scripts/blender"
    with tempfile.TemporaryDirectory(prefix="studio-review-", dir=scratch_parent) as scratch:
        scratch = Path(scratch)
        shutil.copytree(root / "design", scratch / "design")
        (scratch / "validation").mkdir()
        shutil.copy2(cfg_path, scratch / "validation/reference_views.json")
        build_driver = scratch / "build.py"
        build_driver.write_text(
            "import json, os, runpy, sys\nfrom pathlib import Path\n"
            f"sys.path.insert(0, {str(scripts)!r})\n"
            "from verify_validation_setup import geometry_digest\n"
            "from validation_setup import read_config\n"
            f"for stage in {[str(scripts / name) for name in ('00_scene_setup.py', '10_blockout.py', '40_feet_perch.py')]!r}:\n"
            "    runpy.run_path(stage, run_name='__main__')\n"
            "import bpy\n"
            "from verify_blockout import inspect, exercise\n"
            "model_checks = dict(inspect(Path.cwd()), **exercise(Path.cwd()))\n"
            "Path('blockout_checks.json').write_text(json.dumps(model_checks))\n"
            "before = geometry_digest(read_config(Path.cwd()))\n"
            "counts = (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.materials))\n"
            f"for stage in {[str(scripts / name) for name in ('10_blockout.py', '40_feet_perch.py')]!r}:\n"
            "    runpy.run_path(stage, run_name='__main__')\n"
            "assert geometry_digest(read_config(Path.cwd())) == before, 'Repeated build changed geometry'\n"
            "assert counts == (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.materials)), 'Repeated build leaked datablocks'\n"
            f"if {milestone!r} == 'setup':\n"
            "    for obj in bpy.data.objects:\n"
            "        if obj.type == 'MESH': obj.data.materials.clear()\n"
            f"runpy.run_path({str(scripts / '90_validation.py')!r}, run_name='__main__')\n"
            "assert geometry_digest(read_config(Path.cwd())) == before, 'Renderer changed model geometry'\n"
            "os.environ['OWLI_VERIFY_OUTPUT'] = str(Path('baseline_checks.json').resolve())\n"
            f"runpy.run_path({str(scripts / 'verify_validation_setup.py')!r}, run_name='__main__')\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env.pop("OWLI_RENDER_SIZE", None)
        env.pop("OWLI_VALIDATION_OUTPUT", None)
        command = [blender, "--background", "--factory-startup", "--python-exit-code", "1"]
        subprocess.run(command + ["--python", str(build_driver)], cwd=scratch, env=env, check=True)
        reload_driver = scratch / "reload.py"
        reload_driver.write_text(
            "import os, runpy, sys, json\nfrom pathlib import Path\n"
            f"sys.path.insert(0, {str(scripts)!r})\n"
            "from verify_blockout import inspect\n"
            "Path('reloaded_blockout_checks.json').write_text(json.dumps(inspect(Path.cwd())))\n"
            "os.environ['OWLI_VERIFY_OUTPUT'] = str(Path('reload_before_checks.json').resolve())\n"
            f"runpy.run_path({str(scripts / 'verify_validation_setup.py')!r}, run_name='__main__')\n"
            "os.environ['OWLI_VALIDATION_OUTPUT'] = str(Path('validation/reloaded').resolve())\n"
            f"runpy.run_path({str(scripts / '90_validation.py')!r}, run_name='__main__')\n"
            "os.environ['OWLI_VERIFY_OUTPUT'] = str(Path('reload_after_checks.json').resolve())\n"
            f"runpy.run_path({str(scripts / 'verify_validation_setup.py')!r}, run_name='__main__')\n",
            encoding="utf-8",
        )
        subprocess.run(command + [str(scratch / "blender/scene/owli.blend"), "--python", str(reload_driver)],
                       cwd=scratch, env=env, check=True)
        baseline = json.loads((scratch / "baseline_checks.json").read_text(encoding="utf-8"))
        checks = {"blockout_checks": json.loads((scratch / "blockout_checks.json").read_text()),
                  "reloaded_blockout_checks": json.loads((scratch / "reloaded_blockout_checks.json").read_text()),
                  "baseline": baseline, "repeated_build_identical": True, "repeated_datablock_counts_identical": True}
        for key in ("reload_before", "reload_after"):
            data = json.loads((scratch / f"{key}_checks.json").read_text(encoding="utf-8"))
            if data != baseline:
                raise RuntimeError(f"Saved/reloaded studio or geometry changed: {key}")
            checks[key + "_identical"] = True
        metrics = {}
        for view in cfg["views"]:
            name = view["name"]
            first = scratch / "validation/renders" / f"{name}.png"
            second = scratch / "validation/reloaded" / f"{name}.png"
            with Image.open(first) as a, Image.open(second) as b:
                identical = a.mode == b.mode and a.size == b.size and a.tobytes() == b.tobytes()
            if not identical:
                raise RuntimeError(f"Save/reload render pixels differ: {name}")
            metrics[name] = dict(image_metrics(first), reload_pixels_identical=identical)
        checks.update(render_metrics=metrics, config_sha256=sha256(cfg_path),
                      reference_sha256={record["file"]: sha256(root / "references/approved" / record["file"])
                                        for record in json.loads((root / "references/manifest.json").read_text(encoding="utf-8"))["references"]},
                      recipe_sources={str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in
                                      (root / "scripts/project.py", root / "scripts/setup_review.py", root / "scripts/validation_config.py")},
                      fixture_sources={name: sha256(scripts / name) for name in
                                       ("00_scene_setup.py", "10_blockout.py", "40_feet_perch.py", "90_validation.py", "validation_setup.py", "verify_validation_setup.py", "blockout_geometry.py", "verify_blockout.py")},
                      design_sources={name: sha256(root / "design" / name) for name in ("proportions.json", "character_spec.json", "materials.json")},
                      design_approval=False)
        # Only replace evidence after both fresh Blender processes pass all checks.
        output.mkdir(parents=True, exist_ok=True)
        scene_output.parent.mkdir(parents=True, exist_ok=True)
        for path in (scratch / "validation/renders").iterdir():
            shutil.copy2(path, output / path.name)
        shutil.copy2(scratch / "blender/scene/owli.blend", scene_output)
        checks["scene_sha256"] = sha256(scene_output)
        (output / "verification.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
        review_boards(root, output, cfg, milestone)
    print(f"SETUP REVIEW OK: 1024px, fixed cameras/lights, identical reload pixels. Evidence: {output}")
