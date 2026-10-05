"""Apply #17 after the accepted #16 face; final avatar rig follows separately."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from beak_geometry import build
from blockout_geometry import save
build(Path.cwd())
save(Path.cwd())
print('BEAK GEOMETRY BUILT: separate closed upper/lower meshes and lower-jaw hinge.')
