"""Isolated Goal 18 production: exact accepted feather input, explicit own output."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps
from feathers_gate import validate_feathers, load_json
from project import find_blender
from setup_review import review_boards
from materials_contracts import (
    BASELINE_COMMIT, BASELINE_SCENE, BASELINE_SHA256, BASELINE_SIZE_BYTES,
    SCENE_PATH, REVIEW_PATH, SOURCES, PROTECTED_SHA256, VIEWS, MODES,
    EVIDENCE_NAMES, REFERENCE_NAMES, ARCHIVED_STAGE_SHA256,
)

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    import json
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_paths(work, output, target, root=ROOT):
    """A producer cannot route writes to any predecessor or reusable scratch tree."""
    root = Path(root).resolve()
    work, output, target = (Path(p).resolve() for p in (work, output, target))
    require(output == root/REVIEW_PATH and target == root/SCENE_PATH,
            'Only the named new Goal 18 milestone may be published')
    require(work.is_relative_to(root/'tmp') and work != root/'tmp' and not work.exists(),
            'Choose a fresh explicit work directory below repository tmp/')
    return work, output, target


def compare_pixels(work):
    result = {}
    for view in VIEWS:
        paths = [work/'renders'/label/(view+'.png')
                 for label in ('neutral', 'reload_a', 'reload_b')]
        with Image.open(paths[0]) as a, Image.open(paths[1]) as b, Image.open(paths[2]) as c:
            require(a.format == b.format == c.format == 'PNG'
                    and a.size == b.size == c.size == (1024, 1024)
                    and a.mode == b.mode == c.mode == 'RGBA',
                    'Canonical render dimensions/mode differ: '+view)
            require(a.tobytes() == b.tobytes() == c.tobytes(),
                    'Canonical rendered pixels differ: '+view)
            result[view] = {'size': list(a.size), 'mode': a.mode,
                           'build_and_two_reloads_pixels_identical': True}
    return result


def chest_board(work, output, before_framing, after_framing):
    """Same fixed-view image crop before/after; authority panels retain aspect."""
    names = [f'FTH_{part}_{side}' for part in ('CreamUpper', 'CreamMiddle', 'CreamLower', 'Orange')
             for side in ('L', 'R')]+['FTH_ChestCenter']
    board = Image.new('RGB', (1740, 1080), '#f3f4f6')
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=22)
    draw.text((24, 16), 'Goal 18 / F-01 | fixed-camera chest distribution before and after',
              font=font, fill='#17233c')
    for column, view in enumerate(('VAL_FRONT', 'VAL_3Q')):
        bounds = [frames[view]['objects'][name]
                  for frames in (before_framing, after_framing) for name in names]
        left = max(0, int(min(item['min'][0] for item in bounds)*1024)-28)
        right = min(1024, int(max(item['max'][0] for item in bounds)*1024)+28)
        top = max(0, int((1-max(item['max'][1] for item in bounds))*1024)-28)
        bottom = min(1024, int((1-min(item['min'][1] for item in bounds))*1024)+28)
        for row, label in enumerate(('baseline', 'reload_b')):
            draw.text((24+column*570, 70+row*500), view+' / '+('before' if row == 0 else 'after'),
                      font=font, fill='#17233c')
            with Image.open(work/'renders'/label/(view+'.png')) as source:
                crop = source.convert('RGB').crop((left, top, right, bottom))
                fitted = ImageOps.contain(crop, (540, 440), Image.Resampling.LANCZOS)
                board.paste(fitted, (24+column*570+(540-fitted.width)//2,
                                     112+row*500+(440-fitted.height)//2))
    panels = [('00_original_logo.png', (150, 630, 870, 970), '00 / brand chest palette'),
              ('08_parts_lookdev_technical.png', (930, 485, 1195, 737), '08 / chest construction')]
    for row, (name, crop, caption) in enumerate(panels):
        draw.text((1164, 70+row*500), caption, font=font, fill='#17233c')
        with Image.open(ROOT/'references/approved'/name) as source:
            fitted = ImageOps.contain(source.convert('RGB').crop(crop), (550, 440),
                                     Image.Resampling.LANCZOS)
            board.paste(fitted, (1164+(550-fitted.width)//2, 112+row*500+(440-fitted.height)//2))
    board.save(output/'chest_before_after.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scene-output', type=Path, required=True)
    parser.add_argument('--blender')
    args = parser.parse_args()
    work, output, target = checked_paths(args.work, args.output, args.scene_output)
    errors = validate_feathers(ROOT)
    require(not errors, '\n'.join(errors))
    protected = {name: sha(ROOT/name) for name in PROTECTED_SHA256}
    require(protected == PROTECTED_SHA256, 'Historical bytes differ from accepted Git/LFS input')
    require(sha(ROOT/'scripts/blender/legacy/50_materials.py') == ARCHIVED_STAGE_SHA256,
            'Archived material stage differs from exact predecessor Git blob')
    accepted = ROOT/BASELINE_SCENE
    require(sha(accepted) == BASELINE_SHA256 and accepted.stat().st_size == BASELINE_SIZE_BYTES,
            'Accepted Goal 6 Blend differs')
    work.mkdir(parents=True)
    shutil.copytree(ROOT/'design', work/'design')
    (work/'validation').mkdir()
    shutil.copy2(ROOT/'validation/reference_views.json', work/'validation/reference_views.json')
    scene = work/'candidate.blend'
    shutil.copy2(accepted, scene)
    env = dict(os.environ)
    for key in ('OWLI_RENDER_SIZE', 'OWLI_VALIDATION_OUTPUT'):
        env.pop(key, None)
    blender = find_blender(args.blender)
    commands = []
    for mode in MODES:
        argv = [blender, '--background', str(scene), '--python-exit-code', '1', '--python',
                str(ROOT/'scripts/blender/materials_evidence.py'), '--', '--work', str(work), '--mode', mode]
        with (work/(mode+'.log')).open('w', encoding='utf-8', newline='\n') as log:
            result = subprocess.run(argv, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
        commands.append({'mode': mode, 'argv': argv, 'exit_code': result.returncode})
        require(result.returncode == 0, f'Blender {mode} failed; inspect {work/(mode+".log")}')
        print('Blender worker passed:', mode, flush=True)
    checks = {mode: load_json(work/(mode+'_checks.json')) for mode in MODES}
    require(checks['saved_build'] == checks['reload_a'] == checks['reload_b'],
            'Fresh saved-build/two reload datasets differ')
    from materials_gate import validate_worker_semantics, RELOAD_FIELDS
    cfg = load_json(ROOT/'design/materials_lookdev.json')
    baseline = load_json(ROOT/'validation/reviews/feathers_v01/reload_b_checks.json')
    for mode in MODES:
        errors = validate_worker_semantics(checks[mode], cfg, baseline, mode == 'build')
        require(not errors, '\n'.join(errors))
    require(all(checks['build'][key] == checks['saved_build'][key] for key in RELOAD_FIELDS),
            'Build/reload geometry, shader assignments, or measured probes differ')
    pixels = compare_pixels(work)
    require(protected == {name: sha(ROOT/name) for name in protected}, 'Historical input mutated')
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(work/'renders', output/'evidence', dirs_exist_ok=True)
    for mode in MODES:
        shutil.copy2(work/(mode+'_checks.json'), output/(mode+'_checks.json'))
        lines = (work/(mode+'.log')).read_text(encoding='utf-8').splitlines()
        (output/(mode+'.log')).write_text('\n'.join(line.rstrip() for line in lines)+'\n',
                                        encoding='utf-8', newline='\n')
    for view in VIEWS:
        shutil.copy2(work/'renders/reload_b'/(view+'.png'), output/(view+'.png'))
    shutil.copy2(scene, target)
    views = load_json(ROOT/'validation/reference_views.json')
    review_boards(ROOT, output, views, 'materials_v01 (#18 plumage/keratin/perch, motif and F-01)')
    chest_board(work, output, baseline['framing'], checks['reload_b']['framing'])
    (output/'.gitattributes').write_text('*.log text eol=lf\n', encoding='utf-8', newline='\n')
    proof = {
        'gate_version': 2, 'milestone': 'materials_v01', 'design_approval': False,
        'baseline_commit': BASELINE_COMMIT, 'baseline_scene_sha256': BASELINE_SHA256,
        'scene_path': SCENE_PATH, 'scene_sha256': sha(target), 'scene_size_bytes': target.stat().st_size,
        'build': checks['build'], 'reloaded': checks['reload_a'], 'reload_identical': True,
        'render_comparison': pixels, 'commands': commands,
        'protected_predecessor_sha256': protected,
        'source_sha256': {name: sha(ROOT/name) for name in SOURCES},
        'reference_sha256': {name: sha(ROOT/'references/approved'/name) for name in REFERENCE_NAMES},
        'evidence_sha256': {name: sha(output/name) for name in EVIDENCE_NAMES},
    }
    write(output/'verification.json', proof)
    print('NEW GOAL 18 EVIDENCE DELIVERED:', output, 'exact-scene visual decision still required', flush=True)


if __name__ == '__main__':
    main()
