"""Build production feet after #4; preserve the historical coarse blockout recipe."""
from pathlib import Path
import runpy
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
ROOT=Path.cwd()
if 'FAC_MaskBridge' in bpy.data.objects:
    if 'BAK_Upper' not in bpy.data.objects:
        raise RuntimeError('Production feet require the completed #4 face and beak milestone')
    from feet_geometry import build
    from blockout_geometry import save
    build(ROOT)
    save(ROOT)
    print('FEET BUILT: connected 3+1 toe skins, separate hooked claws and rounded perch.')
else:
    runpy.run_path(str(Path(__file__).resolve().parent/'legacy/40_feet_perch.py'),run_name='__main__')
