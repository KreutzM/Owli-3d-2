"""Assign actual #18 lookdev; use only an isolated working scene."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from materials_geometry import build
from blockout_geometry import save
ROOT=Path.cwd()
parts=build(ROOT)
save(ROOT)
print('MATERIALS ASSIGNED:',len(parts),'actual meshes; non-eye lookdev and seated editable tech.')
