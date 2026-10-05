"""Isolated Goal 19 production from accepted materials, with preserved eye candidate."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps
from materials_gate import validate_materials, load_json
from project import find_blender
from setup_review import review_boards
from eyes_contracts import (
    BASELINE_COMMIT, BASELINE_SCENE, BASELINE_SHA256, BASELINE_SIZE_BYTES,
    SCENE_PATH, REVIEW_PATH, SOURCES, PROTECTED_SHA256, VIEWS, MODES,
    EVIDENCE_NAMES, REFERENCE_NAMES,
    ARCHIVE_PATH, ARCHIVE_SHA256,
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
            'Only the named new Goal 19 milestone may be published')
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


def eyes_board(work, output, before_framing, after_framing, *, before_folder=None,
               filename='eyes_before_after.png', before_caption='before',
               after_caption='after', title='fixed-camera eye layers before and after'):
    """Actual fixed-camera before/after crops with untouched authority eye panels."""
    names = [f'FAC_{part}_{side}' for part in ('Globe', 'Iris', 'Pupil', 'Cornea')
             for side in ('L', 'R')]
    board = Image.new('RGB', (1740, 1080), '#f3f4f6')
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=22)
    draw.text((24, 16), 'Goal 19 / F-03 | '+title,
              font=font, fill='#17233c')
    for column, view in enumerate(('VAL_FRONT', 'VAL_3Q')):
        bounds = [frames[view]['objects'][name]
                  for frames in (before_framing, after_framing) for name in names]
        left = max(0, int(min(item['min'][0] for item in bounds)*1024)-20)
        right = min(1024, int(max(item['max'][0] for item in bounds)*1024)+20)
        top = max(0, int((1-max(item['max'][1] for item in bounds))*1024)-20)
        bottom = min(1024, int((1-min(item['min'][1] for item in bounds))*1024)+20)
        for row, label in enumerate(('baseline', 'reload_b')):
            draw.text((24+column*570, 70+row*500), view+' / '+(before_caption if row == 0 else after_caption),
                      font=font, fill='#17233c')
            path = before_folder/(view+'.png') if row == 0 and before_folder is not None else work/'renders'/label/(view+'.png')
            with Image.open(path) as source:
                crop = source.convert('RGB').crop((left, top, right, bottom))
                fitted = ImageOps.contain(crop, (540, 440), Image.Resampling.LANCZOS)
                board.paste(fitted, (24+column*570+(540-fitted.width)//2,
                                     112+row*500+(440-fitted.height)//2))
    panels = [('00_original_logo.png', (196, 332, 462, 584), '00 / brand eye color and face'),
              ('08_parts_lookdev_technical.png', (477, 86, 775, 379), '08 / layered eye lookdev')]
    for row, (name, crop, caption) in enumerate(panels):
        draw.text((1164, 70+row*500), caption, font=font, fill='#17233c')
        with Image.open(ROOT/'references/approved'/name) as source:
            fitted = ImageOps.contain(source.convert('RGB').crop(crop), (550, 440),
                                     Image.Resampling.LANCZOS)
            board.paste(fitted, (1164+(550-fitted.width)//2, 112+row*500+(440-fitted.height)//2))
    board.save(output/filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scene-output', type=Path, required=True)
    parser.add_argument('--blender')
    args = parser.parse_args()
    work, output, target = checked_paths(args.work, args.output, args.scene_output)
    errors = validate_materials(ROOT)
    from eyes_gate import validate_candidate_archive
    errors += validate_candidate_archive(ROOT)
    require(not errors, '\n'.join(errors))
    protected = {name: sha(ROOT/name) for name in PROTECTED_SHA256}
    require(protected == PROTECTED_SHA256, 'Historical bytes differ from accepted Git/LFS input')
    archived = {name: sha(ROOT/name) for name in ARCHIVE_SHA256}
    require(archived == ARCHIVE_SHA256, 'Archived unmerged candidate bytes differ')
    accepted = ROOT/BASELINE_SCENE
    require(sha(accepted) == BASELINE_SHA256 and accepted.stat().st_size == BASELINE_SIZE_BYTES,
            'Accepted Goal 18 Blend differs')
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
                str(ROOT/'scripts/blender/eyes_evidence.py'), '--', '--work', str(work), '--mode', mode]
        with (work/(mode+'.log')).open('w', encoding='utf-8', newline='\n') as log:
            result = subprocess.run(argv, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
        commands.append({'mode': mode, 'argv': argv, 'exit_code': result.returncode})
        require(result.returncode == 0, f'Blender {mode} failed; inspect {work/(mode+".log")}')
        print('Blender worker passed:', mode, flush=True)
    checks = {mode: load_json(work/(mode+'_checks.json')) for mode in MODES}
    require(checks['saved_build'] == checks['reload_a'] == checks['reload_b'],
            'Fresh saved-build/two reload datasets differ')
    from eyes_gate import validate_worker_semantics, RELOAD_FIELDS
    cfg = load_json(ROOT/'design/eyes_lookdev.json')
    baseline = load_json(ROOT/'validation/reviews/materials_v01/reload_b_checks.json')
    for mode in MODES:
        errors = validate_worker_semantics(checks[mode], cfg, baseline, mode == 'build')
        require(not errors, '\n'.join(errors))
    require(all(checks['build'][key] == checks['saved_build'][key] for key in RELOAD_FIELDS),
            'Build/reload geometry, shader assignments, or measured probes differ')
    pixels = compare_pixels(work)
    require(protected == {name: sha(ROOT/name) for name in protected}, 'Historical input mutated')
    require(archived == {name: sha(ROOT/name) for name in archived}, 'Archived eye candidate mutated')
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
    review_boards(ROOT, output, views, 'eyes_v01 (#19 eye layers, iris network and F-03)')
    eyes_board(work, output, baseline['framing'], checks['reload_b']['framing'])
    prior_review = ROOT/ARCHIVE_PATH/'review'
    prior = load_json(prior_review/'reload_b_checks.json')
    eyes_board(work, output, prior['framing'], checks['reload_b']['framing'],
               before_folder=prior_review, filename='eyes_refinement_before_after.png',
               before_caption='prior unmerged candidate', after_caption='refinement',
               title='prior candidate and renewed reference refinement')
    (output/'.gitattributes').write_text('*.log text eol=lf\n', encoding='utf-8', newline='\n')
    proof = {
        'gate_version': 2, 'milestone': 'eyes_v01', 'design_approval': False,
        'baseline_commit': BASELINE_COMMIT, 'baseline_scene_sha256': BASELINE_SHA256,
        'scene_path': SCENE_PATH, 'scene_sha256': sha(target), 'scene_size_bytes': target.stat().st_size,
        'build': checks['build'], 'reloaded': checks['reload_a'], 'reload_identical': True,
        'render_comparison': pixels, 'commands': commands,
        'protected_predecessor_sha256': protected,
        'archived_candidate_sha256': archived,
        'source_sha256': {name: sha(ROOT/name) for name in SOURCES},
        'reference_sha256': {name: sha(ROOT/'references/approved'/name) for name in REFERENCE_NAMES},
        'evidence_sha256': {name: sha(output/name) for name in EVIDENCE_NAMES},
    }
    write(output/'verification.json', proof)
    print('NEW GOAL 19 EVIDENCE DELIVERED:', output, 'exact-scene visual decision still required', flush=True)


if __name__ == '__main__':
    main()
