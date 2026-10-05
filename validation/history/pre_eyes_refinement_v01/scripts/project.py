"""Cross-platform entry point; Blender never needs to be on PATH."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STAGES = {
    "scene": "00_scene_setup.py",
    "blockout": "10_blockout.py",
    "feet": "40_feet_perch.py",
    "materials": "50_materials.py",
    "render": "90_validation.py",
}


def find_blender(explicit=None):
    override = explicit or os.environ.get("BLENDER_EXECUTABLE")
    if override:
        path = shutil.which(override) or (override if Path(override).is_file() else None)
        if not path:
            raise RuntimeError(f"Blender executable not found: {override}")
        return str(path)
    path = shutil.which("blender")
    if path:
        return path
    foundation = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation"
    candidates = list(foundation.glob("Blender */blender.exe"))
    def version(path):
        try:
            return tuple(int(n) for n in path.parent.name.split()[-1].split("."))
        except ValueError:
            return ()
    if candidates:
        return str(max(candidates, key=version))
    raise RuntimeError("Blender not found. Set BLENDER_EXECUTABLE to its absolute executable path.")


def run(command, cwd=ROOT):
    subprocess.run(command, cwd=cwd, check=True)


def doctor(explicit):
    print(f"Python: {sys.version.split()[0]} ({sys.executable})", flush=True)
    from PIL import __version__ as pillow_version
    print(f"Pillow: {pillow_version}", flush=True)
    for command in (["git", "--version"], ["git", "lfs", "version"]):
        run(command)
    blender = find_blender(explicit)
    print(f"Blender executable: {blender}", flush=True)
    run([blender, "--version"])
    run([sys.executable, str(ROOT / "scripts/validate_project.py"), "--strict-assets"])
    print("Optional tools: " + ", ".join(f"{name}={'available' if shutil.which(name) else 'missing'}"
                                        for name in ("ffmpeg", "gh", "make")), flush=True)


def smoke(blender):
    # Existing scaffold scripts write relative to cwd. Isolate all generated artifacts.
    scratch_parent = ROOT / "tmp"
    scratch_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blender-smoke-", dir=scratch_parent) as scratch:
        scratch = Path(scratch)
        shutil.copytree(ROOT / "design", scratch / "design")
        (scratch / "validation").mkdir()
        shutil.copy2(ROOT / "validation/reference_views.json", scratch / "validation/reference_views.json")
        driver = scratch / "smoke.py"
        stage_paths = [str(p) for p in sorted((ROOT / "scripts/blender").glob("[0-9][0-9]_*.py"))]
        driver.write_text(
            "import bpy, runpy\n"
            f"for stage in {stage_paths!r}:\n"
            "    runpy.run_path(stage, run_name='__main__')\n"
            "from verify_feet import inspect\n"
            "from pathlib import Path\n"
            "inspect(Path.cwd())\n"
            "assert bpy.data.objects.get('Owli_Rig') is not None\n"
            "assert len(bpy.data.materials) >= 9\n"
            "from pathlib import Path\n"
            "for view in ('VAL_FRONT', 'VAL_LEFT', 'VAL_BACK', 'VAL_3Q'):\n"
            "    assert (Path('validation/renders') / (view + '.png')).is_file(), view\n"
            "print('SMOKE OK: all scaffold stages, 3+1 toes and four test renders; no design approval implied.')\n",
            encoding="utf-8",
        )
        env = dict(os.environ, OWLI_RENDER_SIZE="64")
        subprocess.run([blender, "--background", "--factory-startup", "--python-exit-code", "1",
                        "--python", str(driver)], cwd=scratch, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "validate", "smoke", "setup-review", "blockout-review", *STAGES])
    parser.add_argument("--blender", help="Absolute Blender executable path; overrides auto detection")
    parser.add_argument("--scene", type=Path, help="Existing .blend for render; defaults to blender/scene/owli.blend")
    parser.add_argument("--output", type=Path, help="Render output directory (render command only)")
    args = parser.parse_args()
    try:
        if args.scene and args.command != "render":
            raise RuntimeError("--scene is only supported for render")
        if args.output and args.command != "render":
            raise RuntimeError("--output is only supported for render")
        if args.command == "doctor":
            doctor(args.blender)
        elif args.command == "validate":
            run([sys.executable, str(ROOT / "scripts/validate_project.py"), "--strict-assets"])
        elif args.command == "smoke":
            smoke(find_blender(args.blender))
        elif args.command in ("setup-review", "blockout-review"):
            from setup_review import build_review
            build_review(ROOT, find_blender(args.blender), "setup" if args.command == "setup-review" else "blockout_v01")
        else:
            scene = args.scene.resolve() if args.scene else ROOT / "blender/scene/owli.blend"
            if args.command == "scene" and scene.exists():
                raise RuntimeError(f"Scene already exists: {scene}. Archive it before rebuilding.")
            if args.command != "scene" and not scene.exists():
                raise RuntimeError("Scene missing; run the scene command first.")
            command = [find_blender(args.blender), "--background", "--factory-startup"]
            if args.command != "scene":
                command.append(str(scene))
            command += ["--python-exit-code", "1", "--python", str(ROOT / "scripts/blender" / STAGES[args.command])]
            if args.command == "render":
                env = dict(os.environ)
                if args.output:
                    env["OWLI_VALIDATION_OUTPUT"] = str(args.output.resolve())
                subprocess.run(command, cwd=ROOT, env=env, check=True)
            else:
                run(command)
    except (RuntimeError, OSError, ImportError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
